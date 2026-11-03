# Kerendia NBA 3.1 | Patient Features | AI Readiness Plan

**Scope:** Patient-level claims features (RX, DX, PX, Lab) for the Kerendia Next Best Action (NBA) HCP model.
**Purpose:** Explains, phase by phase, how the NBA 3.0 patient feature notebooks were rebuilt into the NBA 3.1 notebooks: what changed, why, and what we learned.
**Audience:** Client analytics, data science and platform teams.

---

## 1. Executive Summary

In NBA 3.0, patient features were spread over 10 notebooks. Each notebook joined every raw claim to every cohort before it aggregated anything. Cohort dates, event lists and paths were set inside each notebook.

NBA 3.1 changes this in four phases:

| Phase | Theme | Outcome |
| --- | --- | --- |
| 0 | NBA 3.0 baseline | 10 notebooks, claim x cohort cross-join, hard-coded settings |
| 1 | Better First Occurrence logic | Pre-aggregate first, then cross-join the cohorts. 4 notebooks, one per source |
| 2 | Offset cohorts with dynamic months | Cohorts can start on any day of the month. Shared helper functions. Pivot before cross-join (about 6x faster) |
| 3 | Helper notebooks | One cohort generator for all feature families. One event list (product basket) config, no hard-coded events |
| 4 | Final notebooks on the full HCP universe | Final RX / DX / PX / LAB notebooks that use the helpers, run on 314,920 HCPs x 28 cohorts, with built-in checks |

The final logic and lessons learned are written down in one machine-readable skill (`databricks-skills/patient_features_skills/SKILL.md`). People and AI assistants use it to build, change and check notebooks the same way. This is what makes the pipeline **AI ready**.

---

## 2. End-to-End View

```
NBA 3.0 (10 notebooks, per feature type)
   |  Phase 1: pre-aggregate First Occurrence, one notebook per source
   v
*_Patient_Features (RX, DX, PX, LAB)
   |  Phase 2: offset / dynamic-month cohorts, shared helper functions
   v
*_Patient_Features_offset + 00_Patient_Feature_Helpers_offset
   |  Phase 3: shared helpers
   |     00_cohort_generation   -> CohortGenerator(family).load()
   |     00_event_list_config   -> event_groups(), apply_event_list(), validate_event_input()
   v
Final Notebooks/*_Patient_Features + 00_Patient_Feature_Helpers_31
   |  Phase 4: full HCP universe, 28 cohorts, checks, NBA 3.1 feature rules
   v
notebook_output/patient_features/{rx,dx,px,lab}/  (on kerendia_nba_3_1_volume)
```

---

## 3. Phase 0 | NBA 3.0 Baseline

**Location:** `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/01_Patient_Features`

| Source | Notebooks |
| --- | --- |
| RX | `01_rx_features_rec_&_first_occ`, `01_rx_frequency_features` |
| DX | `02_dx_features_rec_&_first_occ`, `02_dx_frequency_features`, `02_dx_hospitalization_features` |
| PX | `03_px_features_rec_&_first_occ`, `03_px_frequency_features`, `03_px_hospitalization_features` |
| Lab | `04_lab_features_rec_&_first_occ`, `04_lab_frequency_features` |

**How it worked**

* Settings came from `00_config` (`cohort_start_date`, `cohort_end_date`, `months_increment`, `lookback_duration`, `event_prevalence`).
* `DataFrameMerger` (`00_load_processed_data`) joined **every raw claim to every cohort**. It then computed `EVENT_TIME = datediff(LOOKBACK_END_DATE, EVENT_DATE)` on every claim x cohort row.
* `DataFrameBatchProcessor` split that large table into cohort batches. The `first_occurrence_of_event` and `recency` helper classes then pivoted each batch, and the batches were unioned again.
* Event columns came from the data, filtered by `event_prevalence`. The output schema could change between runs.
* Outputs were written to the 3.0 volume with hard-coded paths. Memory was managed by hand (`gc.collect()`, `del`).

**Limitations found**

| Area | Limitation |
| --- | --- |
| Scale | The claim x cohort cross-join happens before aggregation. Billions of claims x N cohorts does not scale. |
| Maintenance | 10 notebooks repeat the same loading, batching and union code. |
| Consistency | Cohort dates and event lists are set in each notebook. They can drift between sources. |
| Flexibility | Cohorts follow calendar months only. No offset for feature families with other data lags. |
| Reproducibility | The pivot columns depend on the data, so the schema can differ between batches and runs. |

---

## 4. Phase 1 | Better First Occurrence Logic

**Location:** `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_1_develop_sm/NBA 3.1 - Dev/03_patient_features/`
**Notebooks:** `DX_Patient_Features`, `PX_Patient_Features`, `RX_Patient_Features`, `LAB_Patient_Features`

**What changed**

1. **Pre-aggregate before the cross-join.** We first find the First Occurrence date per HCP and product/event: `groupBy(PROVIDER_ID, EVENT_NAME).agg(min(EVENT_DATE))`. The result is saved as an intermediate. Only this small table is cross-joined with the broadcast cohort table (28 cohorts in the 3.1 schedule).
2. **Future leakage guard.** `EVENT_TIME = datediff(LOOKBACK_END_DATE, FIRST_OCCURRENCE_DATE)`. Only rows with `EVENT_TIME >= 0` are kept.
3. **Same pattern for Recency, Sub-feature 1 (most recent event).** We take `max(EVENT_DATE)` per HCP and event before the cross-join.
4. **One notebook per source.** First Occurrence, Recency (6 sub-features), Frequency (sub-types A-D) and Hospitalization (DX/PX) are now in one notebook per source. 10 notebooks became 4.
5. **Canonical input schema.** `standardize()` renames source columns to `PROVIDER_ID`, `PATIENT_ID`, `EVENT_NAME`, `EVENT_DATE`, `EVENT_TYPE`, `CLAIM_ID`, `DATA_SOURCE`. `sanitize_column_name()` makes the pivoted column names safe for Delta.
6. **Test runs.** The notebooks can run on a random sample of 10K HCPs before a full run.

**Why it matters**

| Before (3.0) | After (Phase 1) |
| --- | --- |
| Billions of claims x N cohorts, then aggregate | Millions of (HCP, event) rows x N cohorts |
| 10 notebooks with repeated code | 4 notebooks with the same structure |
| Source-specific column names inside the logic | One canonical schema; only the input mapping differs |

**Learnings**

* Any feature of the form `agg(f(EVENT_DATE))` per `(PROVIDER_ID, EVENT_NAME)` can be pre-aggregated before the cohort cross-join.
* **Serverless / Spark Connect:** chained `.withColumn()` loops in Frequency Sub-B and Sub-C built logical plans more than 1,373 levels deep. This caused a `RecursionError` in the 10K-HCP job. We replaced them with a single `.withColumns(dict)` call in all four notebooks. The output did not change (see `CHANGELOG_withColumns_fix.md`).
* `.cache()` / `.persist()` and `F.count("*")` inside a pivot do not work on serverless. We use `F.count(F.lit(1))` and Delta/Parquet checkpoints instead.

---

## 5. Phase 2 | Offset Logic for Cohorts with Dynamic Months

**Location:** `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_1_develop_sm/NBA 3.1 - Dev/03_patient_features/`
**Notebooks:** `DX_Patient_Features_offset`, `PX_Patient_Features_offset`, `RX_Patient_Features_offset`, `LAB_Patient_Features_offset`, plus the shared `00_Patient_Feature_Helpers_offset`

**What changed**

1. **Offset (custom-month) cohorts.** A cohort month can start on any day D from 1 to 28. For example, with offset 7 a month runs from the 7th to the 6th of the next month. Lookback end dates and the monthly bucket (`SVC_DT_M`) follow this offset. Cohorts follow real calendar dates, not fixed 30-day windows.
2. **Dynamic cohort list.** `build_cohort_table(max_data_date)` builds cohorts from the latest claim date. Cohorts whose window ends after the data ends are skipped.
3. **Shared helper functions.** The notebooks became short. Each one sets its parameters and calls shared builders such as `load_hcp_universe`, `load_claims`, `add_event_keys` and `first_occurrence_features`, from `00_Patient_Feature_Helpers_offset`.
4. **Pivot before cross-join for First Occurrence.** We pivot once per HCP, then broadcast cross-join the cohorts and compute `EVENT_TIME` per column. On serverless (RX, 231K HCPs, 243 events, 19 cohorts at offset 7) this took **0.21 min instead of 1.31 min (about 6x faster)**. The output was identical (4,366,572 rows, 0 differences), and no cohort batching was needed.
5. **Deterministic HCP sample.** The `TEST_HCP_SAMPLE` widget samples with `xxhash64(PROVIDER_ID)`, so test runs can be repeated. Test outputs go to a separate `_test` folder.
6. **Delta-safe event keys.** Event names are cleaned once into an `EVENT_KEY` column before the pivot. Every pivot then gives clean column names (`MAX_EVENT_TIME_{EVENT_KEY}_FIRST_OCCURRENCE`).

**Learnings (written into the skill, Sections 10 and 12)**

* **Month labels must match across tables.** NBA 3.1 labels a cohort month by the 1st of its reference month. A bucket labeled by its start date (for example `2025-02-07`) will not join to 3.1 patient tables.
* **Offset tables must not be mixed with calendar-month tables.** At offset 7, claims from days 1-6 fall into the previous month.
* **Input history must cover the earliest lookback.** Some inputs held less history than their names suggested. We now check the date range of each input against the first cohort.
* **Validation IDs.** The test NPIs did not match the IQVIA `PROVIDER_ID`. Test runs now sample the HCP universe instead.
* Each cohort offset was still set inside the cohort config of each notebook. This led to Phase 3.

---

## 6. Phase 3 | Helper Notebooks (Single Sources of Truth)

### Helper 1: Cohort Generation Utility

**Location:** `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_1_develop_sm/NBA 3.1 - Dev/00_Helper_Notebooks/00_cohort_generation`

This notebook builds the 28 NBA 3.1 cohorts once for each feature family and saves them. Feature notebooks only read them, using the family name they belong to.

| Item | Value |
| --- | --- |
| Schedule source of truth | `NBA_3.1_Model_Architecture_and_Cohorts.xlsx` |
| Cohorts | c1-c28: Training c1-c24, Testing c25-c26, Holdout (Backtesting) c27-c28 |
| c1 prediction month | 2024-07-01 (each next cohort is +1 month) |
| Lookback | 12 months. Claims c1: 2023-06-01 to 2024-05-01 (whole months, both included) |
| Data lag | 1 month for claims (`lookback_end_date` = prediction month - 2 months) |
| Family offsets | `claims` = 0 (month boundaries), `promotional` = 17 (day 17), `mmit` and `laad_lrx` = not set yet |
| Storage | `<COHORT_VOLUME_ROOT>/<family>/cohorts.parquet` + `metadata.json` |

**API used by every feature notebook**

* `CohortGenerator("claims").load()` returns a 28-row table with `cohort_id`, `prediction_month`, `dataset`, `offset_days`, `lookback_start_date`, `lookback_end_date`.
* `load()` never rebuilds the cohorts. It fails if the file is missing or was built with a different offset.
* Cohorts are only rebuilt when `00_cohort_generation` itself is run. They are not rebuilt when another notebook loads it with `%run`.
* `validate()` compares c1 with the known dates from the Excel file. A family with no offset set raises a clear `ValueError`.

### Helper 2: Dynamic Product Basket (Event List Config)

**Location:** `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_1_develop_sm/NBA 3.1 - Dev/02_Input_Data_Creation/00_event_list_config`

This notebook loads the curated NBA 3.1 event lists (market baskets) from CSV files and gives them to the input and feature notebooks. Events are no longer hard-coded.

| Claim type | Event list CSV | Join key | EVENT_GROUPs |
| --- | --- | --- | --- |
| RX | `Kerendia NBA 3.1 - Rx Event List.csv` | `EVENT_NAME` (product name, through an NDC crosswalk from `pt_lvl_nbrx`) | 258 |
| DX | `Kerendia NBA 3.1 - Dx Event List.csv` | `EVENT_CODE` (ICD-10) | 240 |
| PX | `Kerendia NBA 3.1 - Px Event List.csv` | `EVENT_CODE` (CPT/HCPCS) | 106 |
| Lab | `Kerendia NBA 3.1 - Lab Event List.csv` | `EVENT_CODE` (LOINC, with a GFR/UACR fallback when the code is missing) | 4 |

**Helpers**

* `apply_event_list()` keeps only basket events and replaces each event with its clubbed `EVENT_GROUP`. It removes duplicate events per claim, and it fails if more than 10% of the list has no claims.
* `event_groups(claim_type)` gives the fixed pivot list, so the output schema is the same in every batch, cohort and run.
* `validate_event_input()` stops the run if the input files are stale or not clubbed.
* `INPUT_PATHS_31` holds all input paths (`dx_full_history`, `dx_12m`, `dx_hosp`, `rx_all`, ...), so notebooks do not hard-code paths.

**Why it matters:** To change products, codes or clubbing, the business edits only the CSV files and re-runs `01_Input_data_creation`. No feature code changes. The basket also replaces `event_prevalence` as the way to control the number of columns.

---

## 7. Phase 4 | Final Notebooks on the Full HCP Universe

**Location:** `.../NBA 3.1 - Dev/03_patient_features/Final Notebooks/`
**Notebooks:** `RX_Patient_Features`, `DX_Patient_Features`, `PX_Patient_Features`, `LAB_Patient_Features`, `00_Patient_Feature_Helpers_31` (optimized builders), `01_Additional_Patient_Features` (add-on features), `00_Patient_Features_EDA`

**Standard notebook layout**

1. `%run` in order: `00_connection`, then `00_event_list_config`, then `00_cohort_generation`, then `00_Patient_Feature_Helpers_31`.
2. Parameters: `FEATURE_FAMILY = "claims"`, input paths from `INPUT_PATHS_31`, windows, and the `TEST_HCP_SAMPLE` widget (0 = full universe).
3. Load the cohorts and check them: claims family, offset 0, ids c1..c28, c1 lookback 2023-06-01 to 2024-05-01.
4. Load the HCP universe (314,920 HCPs). Apply a `left_semi` join right after loading every claims input.
5. Standardize and validate the inputs, then build First Occurrence, Recency, Frequency and Hospitalization.
6. Write the outputs to `kerendia_nba_3_1_volume/notebook_output/patient_features/<source>/`. Sample runs go to `_test_sample_<N>`, so full outputs are never overwritten.

**Example scale (DX):** First Occurrence reads 1.93B rows (2021-01-02 to 2026-08-31). Recency and Frequency read 1.22B rows. Hospitalization reads 567M pre-filtered rows.

**NBA 3.1 feature rules applied**

| Feature | 3.1 rule | Reason |
| --- | --- | --- |
| First Occurrence | Drop the 34 left-censored events (for example lisinopril, amlodipine, metformin). Cap other events at 365 days and add a `_FIRST_CLAIM_BEFORE_WINDOW` flag. Keep recent launches (Kerendia, Mounjaro, Inpefa). | The data starts on 2021-01-02. For long-established drugs, the value shows the data start date, not when the HCP started using the drug. |
| Recency | Totals without a suffix are no longer written | They repeat the typed totals |
| Frequency | Change windows 3 and 6 only (`LOGRATIO_FREQ_*`). Unique patients for 90/180/360 days only. Drop `FREQ_*_IN_LAST_*` when a `NUM_OF_PATIENTS_*` column exists | Fewer redundant features |
| Frequency / Hosp output | One row per HCP x cohort at `SVC_DT_M = LOOKBACK_END_DATE` | Same grain as the HCP model |
| Add-on features | Untreated eligible pool, 90-day trigger events, HF with LVEF >= 40%, potassium barrier, MRA switch candidates (`01_Additional_Patient_Features`) | New business signals for NBA 3.1 |

**Checks built into the notebooks (skill Section 10.8.6)**

1. The cohorts are the claims family on the expected schedule.
2. Month-boundary filter: the last day of the end month is included, and the 1st of the next month is not.
3. Claims from days 1-6 stay in their own calendar month.
4. The output cohorts are exactly the loaded cohort ids.
5. Every output HCP is in the HCP universe: `out.join(hcp_universe, "PROVIDER_ID", "left_anti").count() == 0`.

The optimized builders in `00_Patient_Feature_Helpers_31` were checked against the reference logic on a 300-HCP DX sample, with 0 mismatches.

---

## 8. How This Makes the Pipeline AI Ready

| AI readiness area | What we put in place |
| --- | --- |
| Written specification | `SKILL.md` covers the input contract, business rules (marked Hard or Tunable), column names, performance patterns, serverless limits, known gaps and checks. People and AI assistants build notebooks from the same rules. |
| Single sources of truth | Cohorts come from `00_cohort_generation`, products and codes from `00_event_list_config`, and HCPs from the `HCP_Universe` folder. No cohort, event or HCP list is set inside a feature notebook. |
| Repeatable outputs | Fixed pivot lists, fixed cohort ids, deterministic sampling and partition-level overwrites. A re-run gives the same schema and values. |
| Built-in checks | Event input checks, cohort checks against known dates, HCP universe checks and leakage guards run in every notebook. |
| Scale | Pre-aggregation, pivot before cross-join, broadcast joins and Delta checkpoints. The pipeline runs on billions of claims on serverless. |
| Easy to extend | New feature families get their own offset in `CohortGenerator`. New products only need a CSV change. New claim types follow the same canonical schema. |
| Traceability | Every 3.1 change in the skill records the reason and the evidence (for example run times, row counts and censoring shares). |

---

## 9. Key Learnings

1. **Aggregate first, expand later.** Most of the speed gain came from collapsing claims before joining them to cohorts, and from pivoting before the cross-join.
2. **Put shared settings in one place.** Cohort dates and product lists set in each notebook caused differences between sources. Shared helpers removed them.
3. **Month labels and offsets matter.** One month grain and one labeling convention must be used across patient tables and HCP outputs, or joins fail without any error.
4. **Fixed schemas need fixed lists.** Pivot on the basket, not on the values found in the data.
5. **Check that the data covers the time window.** Always compare each input's date range with the earliest cohort lookback before you use it.
6. **Plan for serverless.** Use `.withColumns()` instead of chained `.withColumn()`, no caching, `F.count(F.lit(1))` in pivots, and Delta-safe column names.
7. **Write lessons into the skill.** Each gap found in a test run went into `SKILL.md`, so the next build (by a person or an AI assistant) does not repeat it.

---

## 10. Open Items and Next Steps

| Item | Status / action |
| --- | --- |
| `CohortGenerator` helpers for the month grain, N-month windows and AVG windows | TODO. These are worked out in each notebook for now (skill Section 10.8.2). |
| `mmit` and `laad_lrx` cohort offsets | Not set yet. They must be set before those families use `CohortGenerator`. |
| Helper `%run` paths | The final notebooks and the skill point to helper copies in other user folders (`sehar.aejaz.ext`, `kerendia_nba_3_1_develop_sa`). Move them to one shared location before production. |
| Production scheduling | Run the four final notebooks plus `01_Additional_Patient_Features` as a job after the input data creation and patient journey steps (skill Section 10.8.5). |

---

## Appendix | Asset Reference

| Asset | Path |
| --- | --- |
| NBA 3.0 notebooks | `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/01_Patient_Features` |
| Phase 1 notebooks | `.../kerendia_nba_3_1_develop_sm/NBA 3.1 - Dev/03_patient_features/{DX,PX,RX,LAB}_Patient_Features` |
| Phase 2 notebooks | `.../kerendia_nba_3_1_develop_sm/NBA 3.1 - Dev/03_patient_features/{DX,PX,RX,LAB}_Patient_Features_offset` |
| Cohort generation helper | `.../kerendia_nba_3_1_develop_sm/NBA 3.1 - Dev/00_Helper_Notebooks/00_cohort_generation` |
| Event list config helper | `.../kerendia_nba_3_1_develop_sm/NBA 3.1 - Dev/02_Input_Data_Creation/00_event_list_config` |
| Final notebooks | `.../kerendia_nba_3_1_develop_sm/NBA 3.1 - Dev/03_patient_features/Final Notebooks/` |
| Logic and learnings (skill) | `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_1_develop_sm/databricks-skills/patient_features_skills/SKILL.md` |
| Serverless fix log | `.../03_patient_features/CHANGELOG_withColumns_fix.md` |
