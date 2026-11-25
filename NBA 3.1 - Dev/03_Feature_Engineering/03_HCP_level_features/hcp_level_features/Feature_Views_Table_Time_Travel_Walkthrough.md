# NBA 3.1 — Storing Monthly Features as a Feature Table, with Time Travel

**Client walkthrough** · Date: 2026-11-20
**Demo notebook:** `/Users/saurabh.modi.ext@bayer.com/NBA_3_1_Feature_Table_Time_Travel_Demo`
**Related investigation:** `NBA_3_1_Feature_Views_Investigation` (same folder as this document)

---

## 1. The questions we were asked

Our HCP-level feature pipeline produces a large DataFrame that is refreshed **every month**. We were asked:

1. Should we save it as a **Parquet file**, a **Unity Catalog (UC) table**, or register it with **Feature Views / Feature Store**?
2. What are the **pros and cons** of the Feature Store route?
3. Can we **go back to previous versions** (time travel)? If yes, can we keep **no more than 3 past versions** to save storage?

## 2. Short answers

| Question | Answer |
| --- | --- |
| Best storage option | A **UC feature table**: a normal Delta table in Unity Catalog with a primary key on `NPI_NUMBER` + `CUTOFF_DATE_TS` (time column). Our notebooks keep computing the features exactly as today; we only *register* the output. |
| Should Feature Views *compute* the features? | **No.** Feature Views counts in rolling days (e.g. "last 30 days"), our features count in calendar months. In the earlier investigation, values matched only 38–46% of the time. |
| Is time travel available? | **Yes.** It comes from Delta Lake, which every UC table (and therefore every feature table) is built on. |
| Can we cap it at 3 versions? | Not by count — Delta keeps history **by age (days)**. Setting retention to **95 days** keeps roughly the last 3 monthly refreshes. If *exactly* 3 is required, a simple snapshot table does it (shown in the demo). |

## 3. Comparing the three storage options

| Capability | Parquet file | Plain UC table | UC feature table |
| --- | --- | --- | --- |
| Access control, lineage and discovery in Unity Catalog | Limited | Yes | Yes |
| Go back to a previous version (time travel) | No | Yes | Yes |
| Listed in the **Features UI** (searchable feature catalogue) | No | No | Yes |
| **Point-in-time** joins for training (no future data leakage) | No | No | Yes |
| Model → feature → source lineage | No | No | Yes |
| Ready for online serving later | No | No | Yes |
| Extra effort | — | — | Primary key + one registration call |

### Pros of the feature table
* Feature values are **unchanged** — the earlier investigation confirmed a 100% match with our existing output.
* **Point-in-time correctness** is automatic: training data never picks up information from after the cohort date.
* One searchable place where data scientists can find and understand HCP features.
* Built-in **time travel**, rollback and audit trail of every monthly run.
* Minimal change: our feature-engineering notebooks stay as they are.

### Cons / things to plan for
* The job needs the `databricks-feature-engineering` Python library.
* Primary-key columns must be **non-null and unique**; duplicate rows would fail the write.
* Only the table owner can add the primary key.
* **Storage:** each monthly refresh rewrites the table, so keeping 3 past refreshes costs roughly **4× the table size** (current + 3).
* Not yet tested at full production scale (~8M rows, ~3,900 columns per table).

---

## 4. Demo walkthrough

The demo uses a small **synthetic** dataset (5 HCPs, monthly cohorts Jan–Oct 2026) in a sandbox schema (`nba_fv_test`). No production data was touched. Every step below was run and the results shown are the actual outputs.

### Step 1 — Build a monthly feature DataFrame
One row per HCP per cohort month, with three example features (`TOTAL_RX_CLAIMS_IN_LAST_1_MONTH`, `TOTAL_RX_CLAIMS_IN_LAST_3_MONTH`, `TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_1_MONTH`). Each refresh adds a new cohort month and re-computes older values (as happens with late-arriving claims).

### Step 2 — Register it as a feature table and set retention
* Registered with primary key `(NPI_NUMBER, CUTOFF_DATE_TS)`, with `CUTOFF_DATE_TS` as the time column.
* Retention set to **95 days** (≈ 3 monthly refreshes) using two table settings:
  * `delta.logRetentionDuration` — how long version history is kept (default 30 days)
  * `delta.deletedFileRetentionDuration` — how long old data files are kept (default **7 days**, which would leave almost no monthly history)

**Result:** feature table created; both retention settings confirmed at 95 days.

### Step 3 — Simulate 5 monthly refreshes
Refreshes dated 5 Jul, 5 Aug, 5 Sep, 5 Oct and 5 Nov 2026. Each run overwrites the table and is tagged with its refresh date.

| Refresh | Rows in table |
| --- | --- |
| 2026-07-05 | 30 |
| 2026-08-05 | 35 |
| 2026-09-05 | 40 |
| 2026-10-05 | 45 |
| 2026-11-05 | 50 |

**Check:** after all overwrites, the primary key, the time column and the 95-day retention were all still in place.

### Step 4 — Time travel to earlier refreshes
The table history listed **9 versions for 5 refreshes** — table creation and settings changes also create versions. This is why "keep 3 versions" has to be expressed as "keep about 3 refreshes' worth of days".

| Version | What happened |
| --- | --- |
| 0–3 | Table created, key columns set, retention configured |
| 4 | Refresh 2026-07-05 |
| 5 | Refresh 2026-08-05 |
| 6 | Refresh 2026-09-05 |
| 7 | Refresh 2026-10-05 |
| 8 | Refresh 2026-11-05 (current) |

Reading old versions worked both **by version number** (first refresh → 30 rows, previous refresh → 45 rows) and **by timestamp** (45 rows).

The same feature value for one HCP and cohort (NPI_001, March 2026) across refreshes shows how each version preserves what the table looked like at that time:

| Refresh | Version | TOTAL_RX_CLAIMS_IN_LAST_1_MONTH |
| --- | --- | --- |
| 2026-07-05 | 4 | 32 |
| 2026-08-05 | 5 | 8 |
| 2026-09-05 | 6 | 8 |
| 2026-10-05 | 7 | 49 |
| 2026-11-05 | 8 | 37 |

*(Values are synthetic and change randomly between runs; in production the changes would come from restated claims.)*

**Rollback:** if a monthly run is wrong, the table can be restored to the previous refresh's version with a single `RESTORE TABLE` command. The restore is itself recorded as a new version, so no history is lost.

### Step 5 — Point-in-time lookup (main feature-table benefit)
We asked for features at arbitrary dates. The feature table returned the latest cohort **on or before** each date — never a later one.

| HCP | Requested date | Cohort used | Explanation |
| --- | --- | --- | --- |
| NPI_001 | 2026-01-15 | none (empty) | Before the first cohort (31 Jan) |
| NPI_001 | 2026-03-15 | 2026-02-28 | Latest cohort before 15 Mar |
| NPI_002 | 2026-06-30 | 2026-06-30 | Exact match |
| NPI_003 | 2026-12-01 | 2026-10-31 | Latest available cohort |

### Step 6 — Keeping about 3 past refreshes (time-based)
Delta has **no "keep N versions" setting**. History is removed by age:
1. Version history older than the retention period is cleaned up automatically.
2. Old data files older than the retention period are deleted when **`VACUUM`** runs (via predictive optimization, or as the last step of the monthly job). Without `VACUUM`, old files are never deleted.

In the demo all versions were only minutes old, so `VACUUM` had nothing to delete yet. Applying the 95-day rule to the real refresh dates:

| Refresh | Age at the 5 Nov run | Still recoverable? |
| --- | --- | --- |
| 2026-07-05 | 123 days | No |
| 2026-08-05 | 92 days | Yes |
| 2026-09-05 | 61 days | Yes |
| 2026-10-05 | 31 days | Yes |
| 2026-11-05 | 0 days (current) | Yes |

**Result:** current refresh + 3 previous refreshes kept; the oldest one expires. If run dates slip by more than a few days, this can occasionally be 2 or 4 previous refreshes.

### Step 7 — Exactly 3 refreshes (count-based alternative)
When exactly 3 is required regardless of run timing, keep snapshots as **rows** instead of versions:
* Each refresh is appended with a `REFRESH_DATE` column (re-running the same month replaces it, so no duplicates).
* Anything outside the latest 3 refresh dates is deleted; `VACUUM` later frees the storage.

**Result after 5 refreshes:**

| REFRESH_DATE | Rows |
| --- | --- |
| 2026-09-05 | 40 |
| 2026-10-05 | 45 |
| 2026-11-05 | 50 |

Exactly 3 refreshes retained — confirmed by an automated check in the notebook.

---

## 5. Recommendation

1. **Keep** the existing feature-engineering notebooks unchanged.
2. **Store** the monthly output as a **UC feature table** (primary key `NPI_NUMBER` + `CUTOFF_DATE_TS` as the time column). Do not use Parquet.
3. **Set retention to 95 days** on both retention settings and make sure **`VACUUM`** runs after each monthly write. This gives roughly the current + 3 previous refreshes.
4. **Only if exactly 3 is a hard requirement**, add the snapshot table from Step 7.
5. **Tag each monthly write** with its refresh date so any version can be traced to a pipeline run.

### Monthly job outline
1. Compute the feature DataFrame (as today).
2. Overwrite the feature table, tagged with the refresh date.
3. *(Optional)* Append to the snapshot table and keep the last 3 refreshes.
4. Run `VACUUM`.

## 6. What is still to be verified
* Write performance and storage at full scale (~8M rows, ~3,900 columns per table).
* That the production job's service principal can create feature tables and owns the tables (needed to add primary keys).
* Whether predictive optimization is enabled on the target schema (otherwise `VACUUM` must be scheduled explicitly).
* Online serving and model-to-feature lineage (`log_model`) were not part of this demo.

## 7. Cleanup
The demo tables (`demo_hcp_features_ft`, `demo_hcp_features_snapshots`) live in the sandbox schema `nba_fv_test` and can be dropped at any time using the cleanup cell at the end of the demo notebook.
