# Calls Data Migration Analysis: `FACT_CALL` → `ker_lynkuet_calls_data`

**Source workbook:** `Data_Drift_NBA_3_1.xlsx` (tab: `Call Table`)
**Project:** Kerendia

> **Brand scope.** This project concerns **Kerendia** only. Both call tables hold more than one brand, so every figure must be read as the Kerendia slice:
>
> - **Old `FACT_CALL`** is a multi-brand table. The workbook's figures come from the Kerendia slice (`DETL_PROD = 'KERENDIA'`), not from the whole table.
> - **New `ker_lynkuet_calls_data`** holds calls for two brands, **Kerendia and Lynkuet**, as its name says, which is why it carries `PROD_BRAND_NM`. It must be restricted with `PROD_BRAND_NM = 'KERENDIA'` before any comparison.
>
> Where the workbook doesn't state whether a figure is Kerendia-filtered, this document says so.

**Convention used below:** statements marked *(inference)* are my reading of the evidence and have not been confirmed by a query. Everything else is taken from the workbook or computed directly from numbers in it.

---

## 1. Executive summary

**The new table is not a like-for-like replacement for `FACT_CALL`, and the existing SQL cannot be reused directly.**

| | Old `FACT_CALL` (Kerendia slice) | New `ker_lynkuet_calls_data` (Kerendia slice) |
|---|---|---|
| Columns | 7 | 6 |
| Output columns that carry over | 2 of 7 (both renames), plus the product filter | n/a |
| Old columns with no equivalent | 5, plus the `STAT` filter | n/a |
| Rows | 2,794,152 | 1,849,788 (−944,364, or 66% of old) |
| History | From 2021-06-23 | From 2024-06-03 |

Top findings:

1. **Five descriptive fields are gone** (channel, call type, duration, purpose, record type) **and so is the `STAT = 'SUBMITTED_VOD'` filter.** Any promotional feature that splits calls by those attributes, such as meal vs. no-meal or sample vs. no-sample, cannot be rebuilt from the new table.
2. **The 944K-row gap is not yet explained.** The new table covers about 3 fewer years of history. Until both tables are compared on the same date window, the gap can't be attributed to missing history versus missing content.
3. **The new table holds two brands, and `FACT_CALL` holds several.** Brand filtering must be applied on both sides. Some workbook figures (HCP counts, the `CALL_NM` prefix profile) don't state whether they are Kerendia-filtered.
4. **`CALL_NM` repeats across rows**, so row counts may not mean the same thing in the two tables.
5. **History is truncated to June 2024**, which matters for any model needing earlier data.

---

## 2. Sample data snapshot (values in each column)

Taken from a screenshot of 10 rows from each table (dates shown as M/D/YYYY). Ten rows are indicative only; a full `SELECT DISTINCT` per column is still needed (see the reconciliation checks).

**Old data: `CPH_DB_PROD.MODEL_V2.FACT_CALL`**

| BHID | MONTH_ID | CHNNL_NM | CALL_TYP_CD | CALL_DURTN | CALL_PRPSE | CALL_REC_TYP_NM |
|---|---|---|---|---|---|---|
| BH22681685 | 11/20/2025 | F2F | Group Detail | 30 | Promotional Activity with meal | Face2Face Signed |
| BH22681685 | 10/17/2025 | F2F | Group Detail | 30 | Promotional Activity | Face2Face Signed |
| BH22681685 | 12/17/2025 | F2F | Group Detail | 30 | Promotional Activity with meal | Face2Face Signed |
| BH11021470 | 8/17/2022 | REMOTE_CALL | Group Detail | 30 | Promotional Activity | BPH_Remote_Meeting |
| BH11021470 | 6/17/2024 | F2F | Detail Only | *(blank)* | Promotional Activity | BPH_Face2Face_SIG |
| BH11021470 | 8/22/2024 | F2F | Detail Only | *(blank)* | Promotional Activity | BPH_Face2Face_SIG |
| BH11021470 | 7/21/2022 | REMOTE_CALL | Group Detail | 30 | Promotional Activity | BPH_Remote_Meeting |
| BH11021470 | 10/18/2022 | REMOTE_CALL | Detail Only | 30 | Promotional Activity | BPH_Remote_Meeting |
| BH11021470 | 9/30/2022 | REMOTE_CALL | Group Detail | 30 | Promotional Activity | BPH_Remote_Meeting |
| BH11021470 | 6/10/2022 | F2F | Group Detail | *(blank)* | Promotional Activity | BPH_Face2Face_SIG |

**New data: `ker_lynkuet_calls_data`**

| HCP_ID | CALL_DATE | WEEKLY | MONTHLY | CALL_NM | PROD_BRAND_NM |
|---|---|---|---|---|---|
| BH11720769 | 5/14/2026 | 5/15/2026 | 5/31/2026 | VC015609847 | KERENDIA |
| BH14377177 | 1/6/2025 | 1/10/2025 | 1/31/2025 | C008643724 | KERENDIA |
| BH12531661 | 7/22/2024 | 7/26/2024 | 7/31/2024 | C007983382 | KERENDIA |
| BH11303922 | 9/24/2026 | 9/25/2026 | 9/30/2026 | VC016494291 | KERENDIA |
| BH38118104 | 6/23/2026 | 6/26/2026 | 6/30/2026 | VC015860567 | KERENDIA |
| BH10682571 | 12/3/2024 | 12/6/2024 | 12/31/2024 | C008569371 | KERENDIA |
| BH11183823 | 8/11/2026 | 8/14/2026 | 8/31/2026 | VC016178189 | KERENDIA |
| BH22931934 | 6/10/2026 | 6/12/2026 | 6/30/2026 | VC015709741 | KERENDIA |
| BH11811727 | 5/9/2025 | 5/9/2025 | 5/31/2025 | C009197475 | KERENDIA |
| BH11454043 | 9/2/2025 | 9/5/2025 | 9/30/2025 | VC010638823 | KERENDIA |

**Column dictionary from the snapshot**

| Table | Column | Values seen in the sample | Notes |
|---|---|---|---|
| Old | `BHID` | `BH` + 8 digits (e.g. `BH22681685`) | Same format as new `HCP_ID`. Only 2 distinct IDs in the sample. |
| Old | `MONTH_ID` | Daily dates, 6/10/2022 to 12/17/2025 | Holds the call date, not a month. |
| Old | `CHNNL_NM` | `F2F`, `REMOTE_CALL` | Pairs with the record type: `F2F` ↔ `Face2Face Signed` / `BPH_Face2Face_SIG`; `REMOTE_CALL` ↔ `BPH_Remote_Meeting`. |
| Old | `CALL_TYP_CD` | `Group Detail`, `Detail Only` | `Sample` and `Event` variants not seen in these rows. |
| Old | `CALL_DURTN` | `30` or blank | Blank in 3 of 10 rows, including `F2F` rows. |
| Old | `CALL_PRPSE` | `Promotional Activity`, `Promotional Activity with meal` | Meal flag appears in 2 of 10 rows. |
| Old | `CALL_REC_TYP_NM` | `Face2Face Signed`, `BPH_Face2Face_SIG`, `BPH_Remote_Meeting` | Mixed naming styles for the same F2F channel. |
| New | `HCP_ID` | `BH` + 8 digits | Same ID format as old `BHID`, which supports joining the two *(not yet tested on overlap)*. |
| New | `CALL_DATE` | Daily dates, 7/22/2024 to 9/24/2026 | Equivalent of old `MONTH_ID`. |
| New | `WEEKLY` | Friday of the call week (e.g. 1/6/2025, a Monday, → 1/10/2025); equals `CALL_DATE` when the call is on a Friday (5/9/2025) | Verified on all 10 rows. |
| New | `MONTHLY` | Last day of the call month | Verified on all 10 rows. |
| New | `CALL_NM` | `C` + 9 digits (`C007983382` to `C009197475`) or `VC` + 9 digits (`VC010638823` to `VC016494291`) | In this sample, `C` IDs fall in Jul 2024 to May 2025 and `VC` IDs from Sep 2025 onward, which fits the two-era reading in 3.5 *(inference)*. |
| New | `PROD_BRAND_NM` | `KERENDIA` in all 10 rows | The sample is already Kerendia-filtered, so it shows nothing about Lynkuet rows. |

**What the snapshot shows**

- **Nothing in the new table carries the old descriptive fields.** The new sample has no channel, call type, duration, purpose or record type, which confirms the loss described in 3.3.
- **Duration is null even on face-to-face calls** in the old sample (3 of 10 rows), consistent with the 55% null rate.
- **`CHNNL_NM` is derived from the record type.** Every sample row's channel agrees with its record-type value, which is why losing the record type also removes the only source for channel.
- **Identifier and date formats line up.** Both tables use `BH########` HCP IDs and daily call dates, so the join keys are compatible.

---

## 3. Analysis

### 3.1 What each table contains

| Attribute | Old: `FACT_CALL` (multi-brand table; slice shown is non-BHO, Kerendia, submitted) | New: `ker_lynkuet_calls_data` (Kerendia + Lynkuet brands) |
|---|---|---|
| Columns | `BHID`, `MONTH_ID`, `CHNNL_NM`, `CALL_TYP_CD`, `CALL_DURTN`, `CALL_PRPSE`, `CALL_REC_TYP_NM` | `HCP_ID`, `CALL_DATE`, `WEEKLY`, `MONTHLY`, `CALL_NM`, `PROD_BRAND_NM` |
| Rows (comparable filter) | **2,794,152** | **1,849,788** (non-BHO, **Kerendia only**, no STAT filter possible) |
| Distinct HCPs | 177,010 | 133,726 *(workbook doesn't say whether this is Kerendia-filtered; see 3.4)* |
| Date range | 2021-06-23 → 2026-09-25 | 2024-06-03 → 2026-09-25 |
| Distinct call dates | 1,750 | 773 |
| Rows per HCP (avg) | ~15.8 | ~13.8 |

Two details:

- `MONTH_ID` in the old table is **not a month**. It holds a daily call date, with 1,750 distinct values over ~5 years. The workbook's `CALL_DATE → MONTH_ID` mapping is therefore a like-for-like rename.
- The new table adds `WEEKLY` and `MONTHLY`. From the sample rows these appear to be the week-ending Friday and the month-end of `CALL_DATE` *(inference, consistent in all 10 sample rows)*. They are new capability, and the workbook doesn't mention them.

### 3.2 Column mapping

| Old field / logic | New equivalent | Status | Consequence |
|---|---|---|---|
| `BHID` (via `BAYER_CUST_ID` + XREF join) | `HCP_ID` | ✅ Rename | XREF join can be dropped |
| `MONTH_ID = TO_DATE(CALL_DATE)` | `CALL_DATE` | ✅ Rename | None |
| `DETL_PROD = 'KERENDIA'` | `PROD_BRAND_NM = 'KERENDIA'` | ✅ Rename | None |
| `BAYER_CUST_ID NOT LIKE '%BHO%'` | `HCP_ID NOT LIKE '%BHO%'` | ✅ Translatable | None |
| `BAYER_CUST_ID IS NOT NULL` | `HCP_ID IS NOT NULL` | ✅ Translatable | None |
| `CHNNL_NM` (derived from `REC_TYP_NM`) | none | ❌ Missing | Channel mix lost |
| `CALL_TYP_CD` | none | ❌ Missing | Detail / group / sample split lost |
| `CALL_DURTN` | none | ❌ Missing | Duration lost |
| `CALL_PRPSE` | none | ❌ Missing | Meal flag and non-promotional exclusion lost |
| `CALL_REC_TYP_NM` | none | ❌ Missing | Record-type detail lost |
| `STAT = 'SUBMITTED_VOD'` | none | ❌ Cannot apply | Can't confirm only submitted calls are present |
| n/a | `WEEKLY`, `MONTHLY`, `CALL_NM` | 🆕 New | Pre-built roll-ups and a call identifier |

**Minimum viable query on the new table** (a direct translation of the mappings above; add schema and database qualifiers as needed):

```sql
SELECT
    HCP_ID    AS BHID,
    CALL_DATE AS MONTH_ID,
    WEEKLY,
    MONTHLY,
    CALL_NM
FROM ker_lynkuet_calls_data
WHERE PROD_BRAND_NM = 'KERENDIA'
  AND HCP_ID IS NOT NULL
  AND HCP_ID NOT LIKE '%BHO%';
```

This returns 5 columns against the old query's 7. The five lost fields cannot be added by any change to the SQL.

### 3.3 What the lost fields actually carried

Profiles come from the old table (2.79M rows). They show how much information disappears with each field.

| Lost field | Old-table profile | Practical loss |
|---|---|---|
| **`CHNNL_NM`** | F2F 96.04%; Group 2.08%; Remote 1.68%; Phone 0.20%; 2 negligible values | **Moderate.** ~4% of calls are non-F2F. Channel-mix features collapse to "all calls". |
| **`CALL_TYP_CD`** | Group Detail 64.02%; Detail Only 27.53%; Group Detail w/ Sample 5.54%; Detail w/ Sample 2.90%; Event Detail ~0% | **High.** Cannot separate group from individual detailing (64% vs 28%), nor identify the ~8.4% of calls that involved samples. |
| **`CALL_DURTN`** | **55.26% null.** When populated: min 1, max 12,000, mean 31.84, Q1 = median = Q3 = 30 | **Low.** More than half the data is null and the populated values barely vary. The 12,000 max is an outlier that needed capping anyway. |
| **`CALL_PRPSE`** | Promotional 87.33%; Promotional with meal **12.37%**; ~0.3% spread across 13 non-promotional or other purposes | **High.** The meal flag is a genuine signal on ~12% of calls. Without purpose, the ~0.3% of non-promotional calls (e.g. Regulatory Compliance, Market Access) can't be excluded from "promotional" counts. |
| **`CALL_REC_TYP_NM`** | 12 distinct values. F2F-signed variants 96.0%; Remote/Group/KAM/etc. the rest | **Low-moderate.** Largely overlaps `CHNNL_NM` (it feeds it). |
| **`STAT` filter** | Old query keeps only `SUBMITTED_VOD` | **Unknown.** If the new table contains unsubmitted calls, counts could be inflated. If it's already filtered upstream, no impact. Needs owner confirmation. |

**Net effect:** the new table can still produce *"number of Kerendia calls per HCP per date/week/month"*. It cannot produce *"number of meal calls, sample calls, group calls, remote calls, or average duration"*. Any promotional feature depending on those is not reproducible.

### 3.4 Coverage comparison

| Metric | Value | Reading |
|---|---|---|
| HCPs in both tables | **125,561** | 94% of the new table's HCPs; 71% of FACT_CALL's HCPs |
| HCPs only in `FACT_CALL` | 51,449 | 29% of the old universe has no calls in the new table |
| HCPs only in new table | 8,165 | 6% of the new universe is unseen in the old table. **If the 133,726 count includes Lynkuet-brand-only HCPs, this figure is overstated for Kerendia.** |
| Row difference | −944,364 | New table has 34% fewer rows |
| History | Old starts 2021-06-23; new starts 2024-06-03 | New table is missing ~3 years |

**The most important caveat on these numbers:** the two tables cover different date windows. `FACT_CALL` has ~3 years of history that the new table cannot have, so a large part of both the row gap and the 51,449 "old-only" HCPs may simply be pre-June-2024 activity. The workbook compares full-table totals. A like-for-like comparison would restrict `FACT_CALL` to `MONTH_ID >= 2024-06-03` before counting rows and HCPs, and apply `PROD_BRAND_NM = 'KERENDIA'` to the new side's HCP and date counts as well as its row count. Until that's done, the real content gap in the shared window is unknown. This is the single most valuable next check.

### 3.5 Data-quality observations on the new table

| Observation | Detail |
|---|---|
| `CALL_NM` is not unique per row | The prefix profile shows **2,389,846** rows but only **1,417,080** distinct IDs (814,243 `VC…` + 602,837 `C…`). The same call ID appears on multiple rows. A likely reason is one row per brand detailed in a call, so a call covering both Kerendia and Lynkuet would appear twice *(inference)*. `FACT_CALL` is also multi-brand and may follow the same one-row-per-brand pattern; this is untested. Whether `CALL_NM` also repeats **within Kerendia alone** is untested. |
| Prefix profile covers a wider population than the comparison | 2.39M rows (prefix profile) vs 1.85M (Kerendia, non-BHO). The gap is plausibly the Lynkuet-brand rows, and possibly BHO IDs *(inference)*. The population behind each profile should be stated. |
| Two ID formats | `VC` prefix = 72.37%, `C` prefix = 27.63%. Observed ranges: `C006330036`–`C009536697` and `VC010464564`–`VC016503491`. This looks like two source systems or eras *(inference)*. |

### 3.6 Risk summary

| Risk | Severity | Why |
|---|---|---|
| Promotional features dependent on type / purpose / channel can't be rebuilt | 🔴 High | Fields absent, no proxy in new table |
| History truncated to Jun 2024 | 🔴 High | Any model or trend needing pre-2024 data loses ~3 years |
| `SUBMITTED_VOD` filter can't be verified | 🟠 Medium | Silent over- or under-counting possible |
| 944K-row gap unexplained | 🟠 Medium | Confounded by date window; needs same-window test |
| Row grain differs (`CALL_NM` repeats; two brands in one table) | 🟠 Medium | Counts may not be comparable without brand filtering and dedup rules |
| Duration lost | 🟢 Low | 55% null and near-constant when present |

---

## 4. Inconsistencies found inside the workbook (Call Table tab)

| # | Location | Issue |
|---|---|---|
| 1 | Call tab | Column is `CALL_DURTN` in the null profile but `CALL_DURN` in the stats block. |
| 2 | Call tab | Prefix profile total (2.39M) and distinct IDs (1.42M) don't match the 1.85M comparison row count. The population isn't stated; the extra rows are plausibly Lynkuet-brand calls. |
| 3 | Call tab | `CALL_REC_TYP_NM` contains case-variant duplicates: `BPH_Remote_Meeting` (43,331) vs `BPH_REMOTE_MEETING` (2,639), and `BPH_Remote_Group_Meeting` (1,030) vs `BPH_REMOTE_GROUP_MEETING` (16). Any grouping on this field needs case-normalization. |
| 4 | Call tab | The `HCP_ID` / `CALL_DATE` population counts (133,726 HCPs; 2024-06-03 → 2026-09-25) don't say whether they are Kerendia-filtered, while the row count explicitly is. |

---

## 5. Recommended next steps

### 5.1 Questions for the owner of `ker_lynkuet_calls_data`

1. Does an upstream source hold channel, call type, duration, purpose, record type and status for these calls? Can they be added to `ker_lynkuet_calls_data`?
2. Is the table already filtered to submitted calls only, for both brands?
3. Is there any history before 2024-06-03, and can it be backfilled?
4. What is the row grain, given that `CALL_NM` repeats? Is it one row per call, per HCP-attendee, or per brand detailed? Is it the same as in `FACT_CALL`?

### 5.2 Reconciliation checks to run (in priority order)

| # | Check | Purpose |
|---|---|---|
| 1 | Restrict `FACT_CALL` to `MONTH_ID >= 2024-06-03`, then recount rows, HCPs and HCP-date pairs vs the new table (Kerendia only) | Separates the date-window effect from real content gaps (3.4) |
| 2 | Row-grain test on the new table, filtered to Kerendia: rows vs distinct `CALL_NM` vs distinct `HCP_ID`+`CALL_DATE`+`CALL_NM`. Repeat on `FACT_CALL` | Establishes whether row counts are comparable |
| 3 | Count rows and distinct HCPs by `PROD_BRAND_NM` in the new table | Confirms what the 133,726 HCPs and the 2.39M-row prefix profile actually include |

### 5.3 Decisions needed from the project owner

| Decision | Options |
|---|---|
| Call features that need the lost fields | (a) Drop them; (b) request the fields be added upstream; (c) keep `FACT_CALL` as the source for those features for as long as it is maintained |
| Pre-2024 call history | Hybrid source (`FACT_CALL` before the cutover, the new table after) with an explicit bridge, **or** truncate model training to Jun 2024 onward |

### 5.4 Housekeeping

- Add a population statement (for example "non-BHO, Kerendia, submitted") above every profile table in the workbook.
- Normalize casing in `CALL_REC_TYP_NM` in any downstream logic.

---

## 6. Appendix: counts at a glance

| Item | Value |
|---|---|
| Old call rows (non-BHO, Kerendia, submitted) | 2,794,152 |
| New call rows (non-BHO, Kerendia) | 1,849,788 |
| Difference | −944,364 (−33.8%) |
| Distinct HCPs: old / new | 177,010 / 133,726 |
| HCPs: both / old-only / new-only | 125,561 / 51,449 / 8,165 |
| Date range: old | 2021-06-23 → 2026-09-25 (1,750 distinct dates) |
| Date range: new | 2024-06-03 → 2026-09-25 (773 distinct dates) |
| Prefix profile on new table (population not stated) | 2,389,846 rows; 1,417,080 distinct `CALL_NM` |
