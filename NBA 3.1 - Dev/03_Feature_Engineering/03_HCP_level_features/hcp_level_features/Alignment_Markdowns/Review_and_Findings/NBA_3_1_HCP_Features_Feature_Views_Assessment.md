# Feature Views for the NBA 3.1 HCP claims features: assessment

**For:** Wenjie. **Date:** 2026-11-16. **Reference run:** `full_2026_11_13` (job 1010893614518587, run 338478597334222).  
**Scope:** read-only review. Nothing was created, registered, changed or run for it; the only change is this file.

Each statement is labelled:

* **[W]** read in the workspace or in our code (notebooks, outputs, readiness plan, API answers)
* **[D]** documented Databricks behavior (Feature Views and Feature Store documentation)
* **[I]** my inference; not tested

Where I am not sure how something works, I say so.

---

## Summary

1. **Can we use Feature Views?** Probably yes, but two checks are open. The Feature Views service answers in our workspace and has no features in `kerendia_nba_3` [W]. It needs serverless or Databricks Runtime 17.0 ML and the client library 0.16.0 or later [D]; we use serverless [W]. Not checked: whether our job environment can install that library version, and whether we have the right to register features in the schema (CREATE FEATURE) [W: not checkable read-only]. Feature Views are in Public Preview [D].
2. **What they would replace or add.** Unity Catalog tables store the features. Feature Views define how features are computed: one object per feature, plus point-in-time training sets, materialization, backfill and online serving [D]. A third option lies in between: our planned Unity Catalog tables become **time-series feature tables** once they get a primary key with a time column. That adds point-in-time lookups and model lineage without rewriting any feature [D].
3. **Do they fit how we build features?** Only partly. Cohorts and cutoff dates fit well with point-in-time training sets [D, I]. The rest does not fit:
   * Calendar-month windows are not defined in the documentation: windows are a duration (for example 30 days) [D]. That changes the values [I].
   * Most of our features need joins with the patient tables first, which Feature Views do not do [W, D].
   * Exact distinct-patient counts have no matching function: the documentation lists an approximate distinct count [D].
   * Shares (`PCT_`) and ratios need one derived feature each, and these cannot be materialized [D].
   * 8,463 columns would mean 8,463 Feature objects [W, I].
4. **Plan.**
   * **Now:** finish the move to Unity Catalog tables, with key columns that are ready to become feature tables.
   * **Then two small tests on the 9 test HCPs:**
     * (A) a time-series feature table on one notebook output;
     * (B) a few Feature Views computed without registering anything (Rx claim counts by window, one share, one patient count, one stage feature), compared with our values.
   * **Then decide.** My expectation is feature tables for all HCP outputs, and Feature Views at most for a small set of selected features later, if online serving or more frequent updates become a need [I].

---

## 1. Can we use Feature Views in our workspace?

| Check | Result | Label |
| --- | --- | --- |
| Feature Views service | The API for listing features answers in our workspace; for `kerendia_nba_3` it returns an empty list (no features registered) | [W] |
| Product status | Public Preview | [D] |
| Compute | Serverless, or a classic cluster on Databricks Runtime 17.0 ML or later | [D] |
| Our compute | The checks for this review ran on serverless; the job tasks for the 3.1 features run on the compute set in job 1010893614518587, not re-checked here | [W] |
| Client library | `databricks-feature-engineering` 0.16.0 or later, installed in the notebook (0.17.0 for some functions) | [D] |
| Library in our environment | Not checked: that would mean installing it | [W: open] |
| Right to create tables in `kerendia_nba_3` | Yes | [W] (permission check) |
| Right to register features (CREATE FEATURE) and read them (READ FEATURE) | Not checked: the permission check I can run does not cover this right | [W: open] |
| Online store | Needed only for online serving; it runs on Lakebase | [D] |

**Conclusion:** technically available [W, D]. Before any test, the library installation and CREATE FEATURE on a test schema need to be confirmed [I].

---

## 2. What would Feature Views replace or add compared with Unity Catalog tables?

### 2.1 Three levels

| Level | What it is | What it gives us | What it costs | Label |
| --- | --- | --- | --- | --- |
| Unity Catalog tables (decided by the team) | NB01–NB06 write Delta tables in Unity Catalog instead of folders in the volume | Access rights, lineage between tables, one name per table | The planned change of the save and read functions | [W] (team decision), [D] |
| Time-series feature tables | The same tables with a primary key (HCP + time column, the time column marked as time series) | Shown in the Features UI; point-in-time lookups when building training sets and scoring; the model records which features it used | Key columns must be NOT NULL; only the table owner can add the key | [D] |
| Feature Views | Each feature defined as an object: source table, filter, aggregation, time window, HCP column, date column | Databricks computes the values; point-in-time training sets; incremental materialization on a schedule; backfill; online serving; feature lineage to the model | Rewriting the feature logic as definitions; limits in section 3 | [D] |

### 2.2 What Feature Views would replace

* The computation in NB01–NB06 (windows, counts, sums), but only for features that come from **one table with row filters** and a supported aggregation [D]. For joins across tables and multi-step aggregations, the documentation points to a Lakeflow pipeline in front, with Feature Views on its output table [D].
* Our own point-in-time logic per cohort (cohort list, cutoff, look-back) would be replaced by a training-set call that only uses data before each row's timestamp [D]. The documentation doesn't say whether this is faster than our cohort engine; I don't know [I].

### 2.3 What Feature Views would not replace

* **Storage:** materialized values still land in Unity Catalog tables (offline store) [D]. The team's decision stays valid either way [I].
* **The patient journey (PJ01–PJ06):** stage, treatment and eligibility per patient-month are multi-step logic across lab, Dx and Rx data [W]. This stays a pipeline [D, I].
* **The joins of NB04 and NB06:** claims × patient stage × treatment [W]. Feature Views would need these as a pre-joined table [D].

### 2.4 Does an NBA 3.1 need speak for Feature Views?

* **Online serving:** I found no use of it in our HCP notebooks or plans. The features are built per monthly cohort [W]. Online serving looks like no need today [I].
* **Point-in-time correctness:** we already reach it with cohorts and cutoffs [W]. A feature table can give it for the join of all HCP features (open point 9 in the readiness plan) without changing the features [D, I].

---

## 3. Do Feature Views fit how we build the features?

### 3.1 How we build them today

| Aspect | NBA 3.1 | Label |
| --- | --- | --- |
| Row | HCP × cohort: 28 cohorts c1–c28 (May 2024 to August 2026), each ending on the last day of its month; cohort list in `cohorts/claims/cohorts.parquet` | [W] |
| Windows | Last 1, 3, 6 and 12 calendar months before the cutoff, plus running totals from 2023-01-01 | [W] |
| Feature types | Counts (`TOTAL_`), shares (`PCT_`), ratios (`RATIO_..._PRIOR_3_LAST_3`), running totals (`RUNNING_TOTAL_`), averages, distinct patients (`TOTAL_PATIENTS_START_`, `TOTAL_ELIGIBLE_PATIENTS_`) | [W] |
| Joins | NB04: Rx claims × the patient's CKD stage and treatments that month (patient-month tables from PJ06); NB05 and NB06: patient tables; NB01: patient treatment counts | [W] |
| Counting rule | NB04 counts each Rx claim once per drug-class × brand row of the patient-month (open point 16) | [W] |
| Columns | 8,463 in NB01–NB06 (NB01 4,672; NB04 3,155); NB01 builds a column for each value it finds in the data | [W] |
| Size | About 8.09M rows per output table (NB01, NB04, NB05, NB06) | [W] (readiness plan) |
| Runtime | Full run 5 h 31 min; NB04 246 min, NB01 170 min | [W] |

### 3.2 Fit, feature type by feature type

| Our need | What Feature Views offer | Fit | Label |
| --- | --- | --- | --- |
| Cohorts with a cutoff | A training set from a table with HCP + timestamp per row; features use only data before that timestamp | Good: one row per HCP × cohort with the cutoff as timestamp | [D], fit [I] |
| Windows of 1/3/6/12 calendar months | Windows as a duration: rolling (back from the timestamp), tumbling (fixed blocks from the Unix epoch, with an offset), sliding | Weak: I found no calendar-month window. A 30-day or 91-day window gives other values than our month windows. **Not sure** whether a newer version has month windows | [D], fit [I] |
| Running totals from 2023-01-01 | Windows have an optional start time; backfill mentions "lifetime" windows | **Not sure** how a total from a fixed date works with a training set | [D], [I] |
| Counts with conditions (payer, brand, days supply, refill) | Count or sum with a row filter on the source table | Good: one feature per condition and window | [D], fit [I] |
| Stage × treatment (NB04) | No joins; use a pre-joined table | Only on a claim-level table already joined with the patient stage. NB04 already builds such claim-level tables in memory (families A, B, C) | [D], [W], fit [I] |
| Exact distinct patients (NB05, NB06) | Approximate distinct count only; the documented list has no exact distinct count | Weak: we report exact counts. Possible workaround: one row per HCP × patient × month before the feature; then a count over a window counts a patient once per month, not once overall | [D], [I] |
| Shares and ratios | A derived feature (registered Python function on other features); cannot be materialized or served online | Possible, but one derived feature per share: thousands | [D], [I] |
| Averages | Average aggregation | Good if the average is over claims; our "per patient" averages first need patient-level steps | [D], [I] |
| 8,463 columns | One Feature object per column | Large: I found no documented limit, and **don't know** how training sets perform with thousands of features | [I] |
| Columns for each value found | Each value needs its own feature definition | New values (like Kerendia in 3.1) need new definitions; today NB01 adds them by itself | [W], [I] |
| NB04 counting rule | Not a Feature Views topic | Would have to be reproduced in the pre-joined table | [I] |

### 3.3 Conclusion

Feature Views fit the simple Rx, lab and Dx counts by window and the cohort / cutoff design [D, I]. They don't fit the core of NB04–NB06 without a pre-joined table, and the windows probably differ from ours [D, I]. Rewriting all 8,463 features would change values that we have just aligned with 3.0, with no visible gain for monthly batch scoring [I].

---

## 4. A sensible plan

### Step 0: Unity Catalog tables (already planned)

Design the tables so they can become feature tables later [I]:

* **Key columns:** HCP (`NPI_NUMBER` or `PROVIDER_ID`), `COHORT_ID` and the cutoff date, NOT NULL and unique per row [W] (keys today), [D] (NOT NULL needed).
* **Owner:** the account that writes the tables, so that it can add the primary key [D].

### Step 1: Test A, time-series feature table (small)

* **Data:** a copy of one validation output, for example NB05 (252 rows, 172 columns in the validation run) [W], in a test schema.
* **Steps:** add the primary key HCP + cutoff date (marked as time series); build a training set for the 9 test HCPs × 28 cohorts with a feature lookup; compare it with a plain join.
* **Success:** identical values; the table appears in the Features UI.
* **Needs:** CREATE TABLE in a test schema (we have it in `kerendia_nba_3` [W]); table owner.

### Step 2: Test B, Feature Views without registering (small)

The documentation says features can be computed and used in a training set without registering them [D], so this test needs no CREATE FEATURE. It still needs the library installation.

* **Data:** the Rx pull of a validation run (9 test HCPs; 51,639 claims in `validation_2026_11_13`) [W]. The label table is the 9 HCPs × 28 cohorts with the cutoff as timestamp.
* **Features to test:**

| Test | Our column | Feature View | What we learn |
| --- | --- | --- | --- |
| B1 | `TOTAL_RX_CLAIMS_IN_LAST_{1,3,6,12}_MONTH` (NB01) | Count of claims per HCP; rolling windows of 30/91/182/365 days, and tumbling windows | How far duration windows are from our month windows |
| B2 | One payer or brand count, for example `TOTAL_RX_CLAIMS_SGLT2_IN_LAST_3_MONTH` | Count with a row filter | Whether filters reproduce our categories |
| B3 | One share, for example `PCT_TOTAL_RX_CLAIMS_MEDICARE_IN_LAST_12_MONTH` | Derived feature from two counts | How much work one share is |
| B4 | `TOTAL_PATIENTS_START_SGLT2_IN_LAST_6_MONTH` (NB05) | Approximate distinct patients | Gap to our exact count |
| B5 | One NB04 stage feature on a claim-level table joined with the patient stage | Count with a row filter on the joined table | Whether the NB04 logic can be expressed |

* **Measure:** share of identical values per feature, largest differences, run time, lines of definition per feature.

### Step 3: Decide

| Question | If yes | If no |
| --- | --- | --- |
| B1 matches with some window type | Feature Views possible for counts | They would change the feature definitions; the model retraining has to accept that |
| B4 is close enough, or exact counts are not needed | Patient counts possible | Keep NB05 and NB06 as they are |
| Is online serving or more frequent updates a need? | Feature Views for the selected features (after the new feature selection) | Feature tables are enough |

**My expectation:** time-series feature tables for all HCP outputs (low effort, no change in values); Feature Views not as a replacement of NB01–NB06; perhaps later for a small set of selected, simple features [I].

### Open questions for the team

1. What did the team want from Feature Views: governance, reuse across models, online serving, or less code?
2. Is there a test schema where we may register features?
3. Is the library installation allowed in our job environment?

---

## Sources

* **[W]**
  * Notebooks NB01–NB07 and `00_cohort_config` in `03_HCP_level_features`.
  * Readiness plan `Strategy_and_Execution/NBA_3_1_HCP_Level_Features_AI_Readiness.md` (feature counts, windows, cohorts, runtimes).
  * Validation outputs `validation_2026_11_13`.
  * Feature Views API (list of features in `kerendia_nba_3`).
  * Unity Catalog permission check (CREATE TABLE).
* **[D]** Databricks documentation:
  * Feature Views (requirements, batch features, streaming).
  * Feature Views API reference (time windows, derived features).
  * Train models with Feature Views.
  * Backfill Feature Views (limitations).
  * Feature tables in Unity Catalog (primary key, time series).
