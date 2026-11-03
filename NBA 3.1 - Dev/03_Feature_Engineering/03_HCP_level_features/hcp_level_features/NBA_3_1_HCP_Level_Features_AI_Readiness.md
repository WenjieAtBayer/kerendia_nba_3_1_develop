# NBA 3.1 HCP-Level Claims Features: AI Readiness Status

**Scope:** `03_Feature_Engineering/03_HCP_level_features/hcp_level_features` (NB01 to NB05) and the shared config `../00_cohort_config`
**Status as of:** 2026-11-03
**Purpose:** Record the work done so far on moving the NBA 3.0 HCP-level claims features to the NBA 3.1 cohort design (configurable cohort month and day offset). Also lists what is validated, what is still open, and what is needed before the full HCP universe (production) run.

---

## 1. Summary

| Item | Status |
| --- | --- |
| Notebooks refactored (3.0 to 3.1 cohort-based) | 5 of 5 in this folder (Rx, Lab, Dx, Combined Claims, NPS) |
| Shared config (`00_cohort_config`) | Done. One place for parameters, cohort logic, paths, brands, windows, patient tables and the fast-engine helpers |
| Feature logic vs 3.0 | Unchanged. Only the time grain changes (calendar month rows become date-range windows ending at each cohort cutoff) |
| Performance | Fast cohort engine in every notebook: claims are read once per run and all cohorts are built in one query and one write |
| Validation (10 test HCPs) | Built into every notebook: fast vs step-by-step engine, offset-0 parity vs the 3.0 output, single-HCP raw-claim trace, completeness checks |
| Production run (full HCP universe) | Not done yet. Blocked on 3.1 production patient-journey tables and downstream wiring (see section 8) |

---

## 2. What changed from 3.0 to 3.1

| Aspect | NBA 3.0 (original) | NBA 3.1 (cohort-based) |
| --- | --- | --- |
| Time grain | Calendar month (`date_trunc('MM', SVC_DT)` to `SVC_DT_M`) | Daily `SVC_DT` kept; date-range windows ending at each cohort cutoff |
| Output grain | 1 row per (NPI, SVC_DT_M) | 1 row per (NPI, COHORT_ID), partitioned by `COHORT_ID` |
| Lookback windows | `Window.rowsBetween(-i+1, 0)` over monthly rows | `SVC_DT > start AND SVC_DT <= cutoff`, windows 1, 3, 6, 12 months |
| Fill missing months | `step2_fill_missing` (cross join NPI x months) | Not needed. NPI universe = NPIs in the widest window plus NPIs with older history (keeps `RUNNING_` values) |
| AVG features | `step3_lag_avg` (window one month wider) | Two-stage: monthly aggregate, zero-fill, fixed denominator. `AVG_EXTRA_MONTH = True` reproduces 3.0 |
| `RUNNING_` features | Unbounded preceding sum | Kept. All claims from `DATA_START_DATE` up to the cohort cutoff |
| Start-date filter | Hardcoded `SVC_DT_M >= '2022-01-01'` | Cohort config (`COHORT_ORIGIN` .. `COHORT_LAST`, complete data only) plus team rule `DATA_START_DATE = 2023-01-01` |
| Pivot columns | Values found in the run's data | Fixed pivot values from the full history, so every cohort has the same columns (0 when no claims) |
| Parameters | Hardcoded | `OFFSET_DAY`, `COHORT_ORIGIN`, `COHORT_LAST`, `COHORT_MONTHS`, `LOOKBACK_WINDOWS`, `VALIDATION_MODE` |
| Helpers | `00_step23_function` | `00_cohort_config` (`00_step23_function` no longer used by these notebooks) |

### How the offset works

* `assign_cohort_month(SVC_DT, offset)`: offset 0 = calendar month. Offset 7 = cohort boundaries on the 7th; the 7th starts the new cohort (`trunc(date_sub(SVC_DT, offset - 1), 'month')`).
* Cutoff of a cohort = month end (offset 0) or month end + (offset - 1) days. Example: Feb cohort at offset 7 runs up to Mar 6.
* Window start: at offset 0 it snaps to calendar months, so 3.0 values are reproduced exactly. At offset > 0 it is cutoff minus N months.
* `COHORT_ID` = `YYYY-MM_offset{N}` (for example `2025-02_offset7`).

---

## 3. Shared configuration (`00_cohort_config`)

All HCP notebooks run `%run "../00_cohort_config"` after `00_connection` (`00_connection` may restart Python, so it must run first).

| Parameter / helper | Current value / role |
| --- | --- |
| `OFFSET_DAY` (`OFFSET_DAYS` alias) | 7 |
| `DATA_START_DATE` | 2023-01-01 (team rule: no data before this date, `RUNNING_` included) |
| `COHORT_ORIGIN` / `COHORT_LAST` | 2025-01-01 (C1) / 2026-10-01 (C22) |
| `COHORT_MONTH` | 2025-02 (preview cohort only) |
| `COHORT_MONTHS` | None = every cohort from origin to last with complete data |
| `LOOKBACK_WINDOWS` | [1, 3, 6, 12] (3.1 decision 2026-10-23: same windows as 3.0 in every notebook; the 9-month window was dropped) |
| `AVG_EXTRA_MONTH` | True (replicates 3.0 `step3_lag_avg`) |
| `VALIDATION_MODE` | Job parameter, default `true` = 10 test HCPs; `false` = full HCP universe |
| `get_hcp_cohort_months()` | Cohorts whose cutoff is on or before the earliest last `SVC_DT` across `Rx_01_new`, `Lab_03`, `Lab_04`, `Dx_03`, `kerendia_nba_3_0_Rx_05`, so every HCP table has the same `COHORT_ID`s |
| `get_cohort_bounds(month)` | `cohort_id`, `cutoff`, `window_bounds`, `avg_window_bounds` |
| `apply_npi_filter()` / `get_test_npis()` | Restricts to the 10 test NPIs in validation mode, no-op in production |
| `build_feature_group`, `build_total_col`, `filter_to_window`, `clean_col_name` | Pivot and count helpers shared by the notebooks |
| `materialize(df, name)` | Serverless has no `.cache()`: in memory in validation, staging Delta table in production |
| All-cohorts engine for feature-row tables | Shared engine used by NB04 and NB05 |
| HCP shared constants | `HCP_QUERY_OUTPUT`, `HCP_NOTEBOOK_OUTPUT`, `HCP_BRANDS` (8 brands), `HCP_BRAND_FILTER`, `HCP_RX_HISTORY_START` (2019-11-01, NB05 first-start lookup only), `HCP_LOOKBACK_WINDOWS`, `HCP_PATIENT_TABLES`, `HCP_NPI_MAPPING_TABLE` |
| 3.0 reference snapshot | `ops_pipeline_bkp/` (`HCP_REF_*`). Used only for offset-0 parity. The 2026-10 refresh of `ops_pipeline/` restated history (about -3% Rx and -21% lab claims for the test HCPs), so parity must read both the 3.0 inputs and the 3.0 outputs from the snapshot |
| Self-test | `assign_cohort_month` checked against known dates |

Volume base: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/` (`query_output/` = inputs, `notebook_output/` = feature outputs and staging tables).

---

## 4. Notebook inventory

| # | Notebook | 3.0 source | Inputs | Outputs (`notebook_output/`, partitioned by `COHORT_ID`) |
| --- | --- | --- | --- | --- |
| 01 | `01_claim_rx_monthly_cohort` | `01_claim_rx_monthly` | `Rx_01_new`, patient `new_and_total_treatments` | `claim_rx_monthly_cohort`, `provider_claim_rx_monthly_cohort` |
| 02 | `02_claim_lab_monthly_cohort` | `02_claim_lab_monthly` | `Lab_03` | `claim_lab_monthly_cohort`, `provider_claim_lab_monthly_cohort` |
| 03 | `03_claim_diagnosis_monthly_cohort` | `03_claim_diagnosis_monthly` | `Dx_03`, patient `new_ckd_stage` | `claim_diagnosis_monthly_cohort`, `provider_claim_diagnosis_monthly_cohort` |
| 04 | `04_claims_monthly_cohort` | `04_claims_monthly` | `Rx_01_new`, `Lab_04`, patient `gfr_dx_stage`, patient `uacr_stage` | `claims_monthly_cohort`, `final_claims_monthly_cohort` |
| 05 | `05_claim_rx_nps_monthly_cohort` | `05_claim_rx_nps_monthly` | `kerendia_nba_3_0_Rx_05` | `claim_rx_nps_monthly_cohort` (already at `PROVIDER_ID` level) |

3.0 sources live in `kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`. Wenjie's 3.0 tables are not written to by any 3.1 notebook.

---

## 5. Notebook details

### NB01: Claim Rx features (`01_claim_rx_monthly_cohort`)

The widest notebook. The 3.0 notebook was reverse engineered first (pipeline overview, feature groups, places where monthly logic was hardcoded), then refactored.

| Group | Pivot | Prefix |
| --- | --- | --- |
| Total | none (denominator for `PCT_`) | `TOTAL_RX_CLAIMS` |
| 2.1 Treatment category | `TREATMENT_CATEGORY` | `TOTAL_RX_CLAIMS_` |
| 2.2 Brand | `Category` in the 8 `HCP_BRANDS` | `TOTAL_RX_CLAIMS_` |
| 2.3 Rejection | category and brand, `REJECTION_FLAG = 1` | `TOTAL_REJECTED_RX_CLAIMS_` |
| 2.4 Duration | category / brand x `DAYS_SUPPLY_BIN` (30/60/90/Not/Unknown) | `TOTAL_RX_CLAIMS_` |
| 2.5 Refill | brand x `REFILL_FLAG`, `REFILL_FLAG` alone (treatment x refill removed: not in 3.0) | `TOTAL_RX_CLAIMS_` |
| 2.6 Payer | category / brand / alone x `METHOD_OF_PAYMENT` (null to Unknown) | `TOTAL_RX_CLAIMS_` |
| 2.7 Patient attributes | category / brand / alone x `AGE_BIN` (10-year bins) and `PATIENT_GENDER` | `TOTAL_RX_CLAIMS_` |
| 2.8 Patient treatment | active / new treatment buckets (joined to the patient table on the cohort month) | `TOTAL_RX_CLAIMS_PATIENT_WITH_` |
| Derived | `SGLT2_WO_INVOKANA_300MG`, `PCT_`, `_IN_LAST_3_6_MONTH` (last 6 - last 3), `RATIO_..._IN_PRIOR_3_LAST_3_MONTH`, `RUNNING_` | |
| AVG family | `AVG_PATIENT_AGE`, `TOTAL_PATIENT_COUNT`, `AVG_TREATMENT_PER_PATIENT`, `TOTAL_TREATMENT_COUNT` (windows + `RUNNING_`); no `PCT_` for these, as in 3.0 | |

Key fixes and decisions recorded in the notebook:
* `add_rx_derived_cols()` builds the duration, payer, age and gender columns once, so windowed, `RUNNING_` and AVG features use the same definitions. Age now uses the year of `SVC_DT`.
* Null-NPI claims are excluded (about 16.7M in the source).
* The NPI universe is widened with NPIs from the full history (otherwise about 1,200 doctors per cohort would get `RUNNING_` = 0).
* 2026-10-22 fixes: patient-treatment join and AVG months use the cohort's own offset (previously always the global offset). `TOTAL_PATIENT_COUNT` counts distinct patients on non-"other" claims only, as in 3.0. `TOTAL_TREATMENT_COUNT` windows and the 4 AVG `RUNNING_` columns were added back.
* Fast engine: the step-by-step version read `Rx_01_new` (31 GB, not clustered) about 140 times per cohort (over 10 minutes per cohort even for 10 HCPs). The fast engine explodes each claim into feature keys once, counts by NPI x cohort month x key, then builds all cohorts in one pivot. `build_cohort_slow` is kept for reference.
* 2026-10-26: one-time reset of the 3.1 output tables (to remove the dropped 9-month columns that `mergeSchema` would keep). Rewritten with 20 cohorts and 3,693 columns. The reset cell is now disabled.

### NB02: Claim Lab features (`02_claim_lab_monthly_cohort`)

* Source `Lab_03` (Quest / LabCorp view). GFR and UACR tests with the CKD stage from the median result (GFR stages 1 to 5, UACR stages 1 to 3, as in 3.0).
* Features: `TOTAL_LAB_CLAIMS_{TEST_TYPE | STAGE}_IN_LAST_{N}_MONTH`, `TOTAL_LAB_CLAIMS`, `RUNNING_`, `PCT_`.
* `clean_col_name` removes parentheses (for example `STAGE 2 (MILD)`).
* Same fast engine as NB01. Offset-0 parity is checked against Wenjie's `claim_lab_monthly_ZS`.

### NB03: Claim Diagnosis features (`03_claim_diagnosis_monthly_cohort`)

* Source `Dx_03`. Features: CKD stage of each Dx claim (`TOTAL_DX_CLAIMS_STAGE_*`, number to `STAGE_n` label as in 3.0), stage the patient is new to in that month (`TOTAL_DX_CLAIMS_WITH_PATIENT_*`, joined to patient `new_ckd_stage` on the offset-aligned cohort month), total, `RUNNING_`, `PCT_`.
* Contains display cells for each step (raw claims, stage mapping, patient-stage join, combined spine, PCT columns, NPI to `PROVIDER_ID` mapping).
* Offset-0 parity against `provider_claim_diagnosis_monthly`.

### NB04: Combined Claims features (`04_claims_monthly_cohort`)

Starts from each Rx claim and adds what was known about the patient's kidneys at that time:

| Family | Question | Joined table | Prefix |
| --- | --- | --- | --- |
| A | GFR / UACR stage of the patient that month | patient `gfr_dx_stage` (patient x month) | `TOTAL_RX_CLAIMS_PATIENT_WITH_GFR_...` |
| B | Same-day GFR / UACR lab test and its stage, by drug class | `Lab_04` | `TOTAL_RX_CLAIMS_PATIENT_WITH_TEST_...` |
| C | Treatment categories / brands of the patient that month, by stage | patient `uacr_stage` (patient x month x treatment) | `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_...` |

* About 3,700 columns (every stage crossed with every category / brand).
* Walkthrough sections 1 to 3 show every input, the claim-level joins and the 3.0 output before the refactor.
* Findings: `Dx_03` is loaded but never used in 3.0 (can be dropped). The UACR x treatment table expands category and brand lists independently (a patient on 3 treatments has 3 x 3 = 9 rows per month); 3.0 has the same structure, so it is kept.
* Built as a long feature-row table (key, SVC_DT, FEATURE, N), then the shared all-cohorts engine from `00_cohort_config`.

### NB05: New Patient Starts (`05_claim_rx_nps_monthly_cohort`)

* Source `kerendia_nba_3_0_Rx_05` (4.03B rows, 2021-01-02 to 2026-08-28, 231,346 providers). Already at `PROVIDER_ID` level, so no NPI mapping step.
* A start = the patient's first-ever Rx claim for a drug class or brand, by any HCP. The writing HCP gets credit.
* Features: `TOTAL_PATIENTS_VISIT` (`PCT_` denominator), `TOTAL_PATIENTS_START_<CLASS>`, `TOTAL_PATIENTS_START_<BRAND>`, `TOTAL_NEW_PATIENT_START`, with windows, `RUNNING_`, `PCT_`.
* First-start dates use the full history from 2019-11-01; counted claims start at `DATA_START_DATE`, so a patient who started in 2021 is not counted as a new start in 2023.
* Walkthrough findings (to confirm with Wenjie):
  1. Starts are left-censored at the start of the data (2,630 starts in 2021-01 vs about 200 per month from 2022). Cohorts from 2025-01 have a 4-year burn-in, so they are not affected.
  2. Starts are looked up across all HCPs (0.2% of starts credited to 2 HCPs on the same first day).
  3. `Diuretic + MRA` never appears, so there are 16 start columns (9 classes + 7 brands), kept fixed.
  4. and 5. Months with no claims are null in 3.0 (not 0); the 3.1 output uses 0, and parity treats null = 0.
  6. `PCT_` denominator is a sum of monthly distinct patients (kept as in 3.0).
  7. Specialty is in the distinct key (no impact for the test HCPs).
  8. Header text of the 3.0 notebook is stale (mentions 2016/2017 data).

---

## 6. Common notebook structure

Every notebook follows the same layout:

1. `%run 00_connection`, then `%run ../00_cohort_config`, then config confirmation
2. Load inputs; apply `apply_npi_filter` and `DATA_START_DATE`; keep a full-history copy for fixed pivot values and parity only
3. Cohort list from `get_hcp_cohort_months()` and `COHORT_BOUNDS`
4. Step-by-step feature functions for one cohort with a preview (`cb_preview`)
5. Fast all-cohorts engine and a check that it equals the step-by-step version
6. One write of all cohorts: Delta, `partitionBy("COHORT_ID")`, `replaceWhere` on this run's `COHORT_ID`s, `mergeSchema` (other offsets / cohorts are kept)
7. Completeness checks: expected vs written cohorts, duplicate (NPI, COHORT_ID), null cells
8. NPI to `PROVIDER_ID` mapping (`kerendia_nba_3_0_npi_bhid_mapping`) and provider-level table
9. Validation: offset-0 parity and HCP trace

Output metadata columns: `COHORT_ID`, `COHORT_MONTH`, `OFFSET_DAYS`, `CUTOFF_DATE`, `SVC_DT_M` (first day of the cohort month), `PULL_DT`.

---

## 7. Validation approach

| Check | What it does | Where |
| --- | --- | --- |
| Fast engine = step-by-step | Compare every cell for the first and last cohort (rtol 1e-9), plus column order and types | NB01 to NB05 |
| Offset-0 parity | Rebuild every month at offset 0 for the test NPIs and compare every shared column with the 3.0 output from the reference snapshot (null = 0). Skipped (not failed) if the snapshot is missing; skipped in production | NB01 to NB05 |
| HCP trace | For a fixed trace HCP (`HCP_TRACE_NPIS`), recount raw claims per cohort and window in pandas and compare with the written features (totals, category, brand, rejection, `RUNNING_`) | NB01 to NB05 |
| Completeness | Cohorts expected vs in table, duplicates, null cells, rows per cohort | NB01 to NB05 |
| Provider output | Null `PROVIDER_ID` and duplicate (PROVIDER_ID, COHORT_ID) counts | NB01 to NB04 |

Recorded results (from notebook comments): NB01 fast engine matched the step-by-step code on 4 cohorts with 0 mismatches (2026-10-22). Saved outputs of the validation cells were not available when this file was written, so the latest PASS / FAIL results should be confirmed by rerunning the validation sections.

Test NPIs (validation mode): 1396374062, 1508230566, 1801062104, 1386651560, 1528629052, 1659887388, 1215675616, 1467950774, 1235697863, 1841364841.

---

## 8. Open items and risks

| # | Item | Impact | Next step |
| --- | --- | --- | --- |
| 1 | Production patient tables: in production `get_patient_table()` still returns the 3.0 tables (calendar months). At offset 7 the patient-treatment / CKD-stage joins in NB01, NB03 and NB04 are then not aligned | Production values at offset > 0 not final | Build the 3.1 patient journey production outputs at the current offset and point `HCP_PATIENT_TABLES` to them |
| 2 | Patient-table location: HCP notebooks read the validation patient tables from `query_output/`, while the patient journey config now writes to `RUN_OUTPUT_DIR` (default `query_output/validation_2026_10_30/`) | Possible stale patient inputs | Confirm the HCP notebooks read the latest patient-journey run |
| 3 | `99_Combine_Physician_Data` joins on `SVC_DT_M`; 3.1 outputs are keyed by `COHORT_ID` (`SVC_DT_M` is kept as the cohort month) | Downstream combine not wired | Decide: join on `SVC_DT_M` from metadata, or switch the key to `COHORT_ID` |
| 4 | `RUNNING_` meaning in the cohort model (running from `DATA_START_DATE`) | Interpretation differs from 3.0 for history before 2023 | Confirm with Wenjie; possible fixed horizon (e.g. 24 months) |
| 5 | `SGLT2_WO_INVOKANA_300MG` family (187 columns, r about 1.0 with SGLT2) | Redundant columns | Analysis recommendation R5 = drop; awaiting decision |
| 6 | NB05 null vs 0 for months without claims, left-censored starts | Small value differences vs 3.0 | Confirm 0 is acceptable |
| 7 | Cohort count: at the current common data end (2026-08-28) and offset 7 the expected list is 2025-01 .. 2026-07 (19 cohorts); the 2026-10-26 rewrite recorded 20 cohorts | Number of cohorts per table | Confirm on the next run (completeness cell prints it) |
| 8 | Column count: NB01 recorded 3,693 columns after the reset; comments elsewhere mention about 4,500 for the query | Documentation consistency | Confirm from the next write |
| 9 | NB01 "Part 4" status cell is partly out of date (NPI to provider mapping and multi-cohort generation are already done) | Documentation | Update the cell |
| 10 | Other HCP notebooks outside this folder (06 onward, combine) still use `00_step23_function` | Mixed logic in the pipeline | Refactor or confirm they stay on 3.0 logic |

---

## 9. Before the production (full HCP universe) run

1. Rebuild the 3.1 patient journey (production) at `OFFSET_DAY = 7` and point `HCP_PATIENT_TABLES` (production entries) to it.
2. Set `VALIDATION_MODE = false` as a job parameter (staging tables are written by `materialize()` in production).
3. Run NB01 to NB05 in order; check the completeness cell of each (same `COHORT_ID`s in every table, 0 duplicates).
4. Run the HCP trace cells on a sample of production HCPs (parity runs only in validation mode).
5. Wire the cohort outputs into the combine step (item 3 above).
6. Option: schedule as a Lakeflow Job with one task per notebook.

---

## 10. References

* Config: `03_HCP_level_features/00_cohort_config`
* Related folders: `03_HCP_level_features/Patient_Journey_Validation`, `03_HCP_level_features/Final Product Basket`
* 3.0 pipeline: `kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`
* Feature analysis docs: `kerendia_nba_3_1_develop/NBA 3.1 - Dev/Feature Analysis/NBA_3_1_HCP_Claims_Features_Analysis.md` and `..._Recommendations.md`
* Patient features readiness plan: `03_patient_features/NBA_3_1_Patient_Features_AI_Readiness_Plan.md`
