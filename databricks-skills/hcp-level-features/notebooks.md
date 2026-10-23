# HCP-Level Feature Notebooks: Catalog

Reference for [SKILL.md](SKILL.md). Status is as of 2026-10-23. Check the notebook before you rely on a number.

## Common locations

* **Volume base:** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/`
  * `query_output/`: inputs written by `00_Write_Input_Files` (3.0, notebook 198916793191530, reads Snowflake PHCDW) and by the patient journey notebooks
  * `notebook_output/`: feature outputs (3.0 originals and the 3.1 `*_cohort` tables) and staging tables (`*_stage_*`, `*_feature_rows_*`)
* **3.0 originals:** `/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`
* **Connection notebook:** `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection`
* **3.1 clone folder:** `/Users/patricio.guledjian.ext@bayer.com/kerendia_nba_3_1_develop_clone/` (`00_cohort_config`, `hcp_level_features/`, `Patient_Journey_Validation/`)
* **Git folder:** `/Users/patricio.guledjian.ext@bayer.com/kerendia_nba_3_1_develop` (branch `dev/hcp-claims-features`). Push only when the user asks.
* **NPI -> provider mapping:** `query_output/kerendia_nba_3_0_npi_bhid_mapping` (`NPI_NUMBER`, `PROVIDER_ID`)
* **Test NPIs (validation mode):** 1396374062, 1508230566, 1801062104, 1386651560, 1528629052, 1659887388, 1215675616, 1467950774, 1235697863, 1841364841

## Patient-journey tables used by HCP features

The patient journey notebooks are in `Patient_Journey_Validation/` (01 labs, 02 dx, 03 rx, 04 t2d flag, 05 px, 06 combine). They are offset-aware via `assign_cohort_month`.

| Used by | 3.0 table (query_output) | 3.1 validation table | Grain |
| --- | --- | --- | --- |
| NB01 | `pat_new_and_total_treatments` | `kerendia_nba_3_1_pat_new_and_total_treatments_validation` | patient x month (`SVC_DT_M`), `TOTAL_TREATMENTS`, `TOTAL_NEW_TREATMENTS` |
| NB03 | `pat_new_ckd_stage` | `kerendia_nba_3_1_pat_new_ckd_stage_validation` | patient x month, `NEW_CKD_STAGE` |
| NB04 A | `pat_gfr_dx_stage_and_treatment_category` | `kerendia_nba_3_1_pat_gfr_dx_stage_validation` | patient x month, `GFR_DX_STAGE`, `UACR_STAGE` |
| NB04 C | `pat_uacr_stage..._new` | `kerendia_nba_3_1_pat_uacr_stage_validation` | patient x month x CATEGORY x BRAND |
| NB06 (todo) | `pat_sglt2_filter_m` | `kerendia_nba_3_1_pat_sglt2_filter_m_validation` | patient x month eligibility |

Warning: the 3.1 validation patient tables were last written on 2026-10-19 by an offset-0 run. Offset-7 HCP outputs that join them are month-misaligned until the patient journey is re-run at offset 7 and those cohorts are rewritten. The user rejected mixing the two.

## NB01: `01_claim_rx_monthly_cohort` (ID 1489390052618043)

* **Source:** `query_output/Rx_01_new` (31 GB, about 4.03B rows, 2021-01-02..2026-08-28, about 17.9M null NPIs). Cleaning: strip trailing spaces from `TREATMENT_CATEGORY`. Derived columns are added once in `add_rx_derived_cols`: `DAYS_SUPPLY_BIN` (30/60/90/Not/Unknown), `METHOD_OF_PAYMENT` null -> `METHOD_OF_PAYMENT_Unknown`, `AGE` / `AGE_BIN` (10-year bins, `AGE_GROUP_ABOVE_80`, `AGE_GROUP_IGNORE`), `PATIENT_GENDER` null -> `PATIENT_GENDER_Unknown`.
* **Brand filter:** `Category IN ('INVOKANA 100MG','INVOKANA 300MG','FARXIGA','JARDIANCE','SPIRONOLACTONE-MRA','Diuretic + MRA','DPP-IV','GLP-1')`
* **Feature groups (17 `CLAIM_GROUPS` + 2 patient-treatment groups):** category, brand, rejected category/brand (`TOTAL_REJECTED_RX_CLAIMS_`, `REJECTION_FLAG = 1`), duration (Tx/brand x DAYS_SUPPLY_BIN), refill (alone, brand x REFILL_FLAG; no Tx x refill), payer (alone, Tx, brand x METHOD_OF_PAYMENT), age (alone, Tx, brand), gender (alone, Tx, brand), patient treatment buckets (`TOTAL_RX_CLAIMS_PATIENT_WITH_{NO|1|2_OR_3|3_MORE}_{ACTIVE|NEW}_TREATMENT(S)`).
* **Extras:** AVG family (`AVG_PATIENT_AGE`, `TOTAL_PATIENT_COUNT`, `AVG_TREATMENT_PER_PATIENT`, `TOTAL_TREATMENT_COUNT` + `RUNNING_`), `SGLT2_WO_INVOKANA_300MG` (counts, duration, rejection, age, gender; windowed and RUNNING_), PCT, DIFF/RATIO for 12 features.
* **Lookbacks:** `[1,3,6,12]` (config; the 9m window was dropped 2026-10-23, 3.0 never had it). **Engine:** pattern A (`build_feature_long`, `build_monthly_avg`, `build_all_cohorts_fast`).
* **Output:** `notebook_output/claim_rx_monthly_cohort` (NPI level, about 4,506 columns) + `provider_claim_rx_monthly_cohort` (provider level, cell "Provider ID mapping and provider-level output", added 2026-10-23, not run yet). Written in one write for all cohorts (`replaceWhere COHORT_ID IN (...)`). Production still reads the 3.0 `pat_new_and_total_treatments`.
* **Cells to know:** "Check: all-cohorts query = per-cohort engine (2 cohorts)" (first and last cohort, 45,040 cells each, 0 mismatches; about 1 min), "HCP trace across all cohorts" (NPI 1386651560, 19 cohorts, 2,489 checks, 0 mismatches). The older "Single HCP Journey - Full Feature Trace (preview cohort)" only checks one cohort. The last markdown cell "Part 4: Status and Flags for Wenjie" lists open points (provider mapping, `99_Combine` key, `AVG_EXTRA_MONTH`).
* **AVG:** `AVG_EXTRA_MONTH = True` (default, as 3.0) divides by N+1 months, False by N.
* **Validation:** offset-0 parity vs `notebook_output/claim_rx_monthly`: 19 months x 3,685 columns, 0 mismatches, 19 known-quirk cells (3.0 `RUNNING_REJECTED_..._SGLT2_WO_INVOKANA_300MG` off by 1). The write takes 1.3 min for 19 cohorts.
* **Quirks:** the 3.0 `SGLT2_WO` subtraction became null when the brand column was null (3.1 is algebraically correct). The model uses 52 `RUNNING_` features (from `kerendia_nba_3_hcp_selected_features_data`).

## NB02: `02_claim_lab_monthly_cohort` (ID 3779149833381333)

* **Source:** `query_output/Lab_03` (`SVC_DT` date, no null NPIs, from 2021-07). `PATIENT_ID` cast to string.
* **Features:** `TOTAL_LAB_CLAIMS`, by `TEST_TYPE` (GFR, UACR), by `STAGE` (8 values; GFR stages contain parentheses, so `clean_col_name` strips `()`), RUNNING_, PCT.
* **Lookbacks:** config `[1,3,6,12]` (9m dropped 2026-10-23). **Engine:** pattern A (`build_lab_long`). `FAST_SOURCES = {"run": df_lab, "orig": df_lab_all}`.
* **Output:** `claim_lab_monthly_cohort` + `provider_claim_lab_monthly_cohort`. **3.0 table:** `claim_lab_monthly_ZS` / `provider_claim_lab_monthly_ZS`.
* **Validation:** parity 20 months x 116 columns, 0 mismatches. Trace 0 mismatches.

## NB03: `03_claim_diagnosis_monthly_cohort` (ID 3779149833381626)

* **Source:** `query_output/Dx_03` (409M rows). `add_dx_stage_label`: `DX_STAGE` 1..5 -> `STAGE_1..5`, anything else (0, null) -> `STAGE_UNSPECIFIED`; the values present are `STAGE_1..4` + `STAGE_UNSPECIFIED`, read once from the full table as fixed pivot values. Patient CKD stage table: `NEW_CKD_STAGE` 1..5 -> `NEW_TO_STAGE_1..5`, else `NO_NEW_STAGE` (fixed list). Validation reads `kerendia_nba_3_1_pat_new_ckd_stage_validation`, production still reads the 3.0 `pat_new_ckd_stage`.
* **Patient join (`add_patient_stage(df, offset_days, pat_df=None)`):** left join on `PATIENT_ID` + `assign_cohort_month(SVC_DT, offset)` = `SVC_DT_M`. `FAST_SOURCES["run"]` is a function of the offset: `lambda off: (df_dx, add_patient_stage(df_dx, off))`; the parity cell adds `"orig"` with the 3.0 table.
* **Engine details:** `build_dx_long` -> `(NPI, _CM, KEY, N)`; `_DX_GROUPS = [("DX_STAGE", "TOTAL_DX_CLAIMS_", ...), ("NEW_CKD_STAGE", "TOTAL_DX_CLAIMS_WITH_PATIENT_", ...)]`; 60 count columns, 111 output columns per cohort before PCT.
* **Features:** `TOTAL_DX_CLAIMS`, `TOTAL_DX_CLAIMS_STAGE_*`, `TOTAL_DX_CLAIMS_WITH_PATIENT_*` (stage the patient is new to in the claim's cohort month), RUNNING_, PCT.
* **Lookbacks:** `DX_LOOKBACK_WINDOWS = HCP_LOOKBACK_WINDOWS["dx"]` = `[1,3,6,12]`. **Engine:** pattern A.
* **Output:** `claim_diagnosis_monthly_cohort` + `provider_claim_diagnosis_monthly_cohort`. **3.0 table:** `provider_claim_diagnosis_monthly` (provider level only, 130 columns).
* **Validation:** parity 19 months x 127 columns, 0 mismatches (with the 3.0 patient table). The 3.0 table is provider level only, so the parity maps NPI -> PROVIDER_ID first, and 3.0 base-month columns (no suffix) are compared with `_IN_LAST_1_MONTH`. Trace 1,140 checks, 0 mismatches.

## NB04: `04_claims_monthly_cohort` (ID 3779149833381874)

* **Sources:** `Rx_01_new` (base; `df_rx` keeps the full history for the walkthrough and parity; since 2026-10-23 `DATA_START_DATE` is applied to the feature rows: `df_feat_all` (full) -> `FEATURE_VALUES`, `df_feat` = rows from `DATA_START_DATE`; trace filters the same way), `Lab_04` (same-day lab; `PATIENT_ID` cast to string, lab NPI dropped because the lab can come from any HCP), patient GFR table (family A), patient UACR table (family C). Validation reads `kerendia_nba_3_1_pat_gfr_dx_stage_validation` / `kerendia_nba_3_1_pat_uacr_stage_validation`; production the 3.0 `pat_gfr_dx_stage_and_treatment_category` / `pat_uacr_stage_and_treatment_category_new`. `Dx_03` is loaded (as in 3.0) but not used, and `recency_window=90` is also unused.
* **Labels (cell "Label helpers"):** patient tables: `gfr_label` 1..5 -> `GFR_STAGE_1..5` else `GFR_STAGE_UNKNOWN`; `uacr_label` 1..3 -> `UACR_STAGE_1..3` else `UACR_STAGE_UNKNOWN`. Lab tests: `CHRONIC KIDNEY DISEASE, STAGE 1` .. `STAGE 5` (with `(MILD)`, `(MODERATE)`, `(SEVERE)` for 2-4) -> `GFR_STAGE_1..5` else `GFR_STAGE_UNSPECIFIED`; UACR `A1..A3` -> `UACR_STAGE_1..3` else `UACR_STAGE_UNSPECIFIED`.
* **Brand list:** `BRANDS` = the NB01 brand filter. 175 feature columns per window (A 28, B 46, C 100, total 1); preview cohort has 1,578 columns (700 window, 175 RUNNING_, 696 PCT_ + keys).
* **Families:** A `TOTAL_RX_CLAIMS_PATIENT_WITH_<GFR>[_AND_<UACR>]` (left join on patient + month). B `..._WITH_TEST_<stage>_WITH_<class|brand>` (same-day join on `SVC_DT` + patient; unmatched claims only contribute column names, N=0). C `..._WITH_DX_<stage>_WITH_<class|brand>` (inner join on patient + month to the UACR table, which is a CATEGORY x BRAND cross product, so each claim counts n times; this also happens in 3.0).
* **Cleaning:** `clean_name_04` = 3.0 order without parenthesis removal (don't use `clean_col_name`).
* **Lookbacks:** `[1,3,6,12]`. **Engine:** pattern B feature rows (`build_feature_rows` -> `(NPI, SVC_DT, FEATURE, N)`) + all-cohorts engine (`build_all_cohorts_fast`, cell "Fast cohort engine (all cohorts in one query)", uses the config's `feature_rows_to_months` / `build_all_cohorts_from_months` / `add_cohort_meta`). `build_cohort` stays as the reference; cell "Check: fast engine = build_cohort (2 cohorts)".
* **Output:** `claims_monthly_cohort` (NPI) + `final_claims_monthly_cohort` (provider). Written in **one write** for all cohorts (`replaceWhere COHORT_ID IN (...)`, since 2026-10-23; before: one write per cohort). **3.0 table:** `final_claims_monthly` (12.96M rows, 3,694 columns). The parity cell rebuilds feature rows at offset 0 with the 3.0 patient tables and its own `FEATURE_VALUES0`, then counts 3.0 columns not built (combinations the test HCPs never had) and checks they are all 0.
* **Validation:** parity 2,217 columns x 10 providers x 19 months, 0 mismatches (3.0 patient tables; rerun 2026-10-23 with the fast engine: PASS, about 24 min, mostly the pandas comparison loop). Fast engine = `build_cohort` for all 19 cohorts, 0 mismatching cells (12 s vs 141 s). Trace NPI 1386651560: 16,625 checks, 0 mismatches.

## NB05: `05_claim_rx_nps_monthly_cohort` (ID 977892282441458)

* **Source:** `query_output/kerendia_nba_3_0_Rx_05` (27 GB, 4.03B rows, has `PROVIDER_ID`, `NPI_NUMBER`, `PRIMARY_SPECIALTY_CODE`). Cleaning: strip trailing spaces from `TREATMENT_CATEGORY`, keep the original `SVC_DT >= 2019-11-01` filter. Since 2026-10-23 the counted claims are `df_rx_run` = `df_rx` from `DATA_START_DATE`; `df_rx_pat` keeps the full history for first-start dates (else pre-2023 starters would look new); parity uses the full `df_rx`. The HCP filter is on `NPI_NUMBER` (`apply_npi_filter`). Key = `PROVIDER_ID` throughout. `df_rx` = the run's HCP claims. `df_rx_pat` = all claims of their patients, by any HCP (needed for first-start dates; in production this is the full table).
* **Features:** `TOTAL_PATIENTS_VISIT` (distinct patients per cohort month, summed over windows: a patient seen in 3 months counts 3 times, same as 3.0), `TOTAL_PATIENTS_START_<class|brand>` (16 columns: 9 classes + 7 brands, `Diuretic + MRA` never appears), `TOTAL_NEW_PATIENT_START` (distinct patients with at least one class start in the month), RUNNING_, PCT (denominator `TOTAL_PATIENTS_VISIT`).
* **Start rule:** a start is a claim on the patient's first-ever date for that class/brand across ALL HCPs, and only the HCP who wrote it gets the credit. Same-day duplicates count once. Two HCPs on the same first day both get +1 (34 cases). Specialty is part of the distinct key.
* **Cleaning:** `clean_name_05` (`/` -> `_OR_`, `+` -> `_AND_`). The fixed feature list is read from the 3.0 output columns.
* **Lookbacks:** `[1,3,6,12]`. **Engine:** pattern B feature rows + all-cohorts engine (`build_all_cohorts_fast`, key `PROVIDER_ID`), one write with `replaceWhere COHORT_ID IN (...)` (since 2026-10-23). Visits / new patients are one row per patient per cohort month in the feature rows, so summing by cohort month keeps the distinct counts. Checked 2026-10-23: fast = `build_cohort` for 19 cohorts (0 mismatching cells), offset-0 parity 35,720 cells, 0 mismatches.
* **Output:** `claim_rx_nps_monthly_cohort` (provider level directly, no mapping). **3.0 table:** `kerendia_nba_3_0_claim_rx_nps_monthly` (190 columns). In 3.0, base-month columns compare with 3.1 `_IN_LAST_1_MONTH`.
* **Validation (2026-10-22):** completeness 19 cohorts, 190 rows (10 providers), 161 columns as expected (18 features x 4 windows + 18 RUNNING_ + 16 x 4 PCT_ + 7 metadata), 0 duplicates, 0 nulls. Offset-0 parity vs 3.0: 19 months x 188 columns, 35,720 cells, 0 mismatches. Trace NPI 1386651560 / provider 7608159: 19 cohorts, 2,926 checks, 0 mismatches.
* **Findings:** left-censoring in 2021-01 (no impact from 2025 cohorts), null instead of 0 in filled months (1,014,149 rows), `TOTAL_NEW_PATIENT_START` null for providers with no starts.

## Open items across notebooks (ask the user / Wenjie)

1. Re-run the patient journey at offset 7, then rewrite the NB01/NB03/NB04 cohorts that join patient tables.
2. NB01: provider-level output cell added 2026-10-23; run it and check null PROVIDER_ID / duplicates.
3. `99_Combine_Physician_Data` joins on `SVC_DT_M`; the cohort tables key on `COHORT_ID` (`SVC_DT_M` is kept as the cohort month start). Decide the bridge.
4. Future data leak: at offset > 0 a monthly patient-table row can include days after the cutoff. This is a design decision for Wenjie.
5. Null vs 0 for HCPs with no activity: confirm 0 is acceptable downstream.
6. NB06 `06_claim_eligible_hcp` (3.0 ID 198916793189151) is not refactored yet. It needs the offset-7 `pat_sglt2_filter_m`.
7. `00_step23_function` (`step2_fill_missing`, `step3_lag*`) is still used by other 3.0 notebooks. Don't delete it.
8. `DATA_START_DATE` now applied in all five notebooks (NB04/NB05 changed 2026-10-23, not rerun yet). All five use `get_hcp_cohort_months()` (common end date of all HCP inputs, `00_cohort_config`). Rerun NB01-NB05 and their checks; NB04/NB05 `RUNNING_` values will drop.
9. Production mode (`VALIDATION_MODE = False`) has never been run for any of the five notebooks. Production runtimes and staging-table sizes are unknown.
