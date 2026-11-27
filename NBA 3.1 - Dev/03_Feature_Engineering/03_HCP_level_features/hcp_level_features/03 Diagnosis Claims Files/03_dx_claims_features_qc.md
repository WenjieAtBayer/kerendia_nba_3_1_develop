# QC 03: Dx claims features (HCP monthly, NB03), NBA 3.1

**QC status:** DONE, 2026-11-27 (claim type Dx; plan: `03_dx_claims_features_qc_plan.md`)  
**Verdict:** PASS with actions. All 113 features were recomputed independently from the Dx pull with 0 differences: 265.6M window, stage and running cells over every NPI x cohort, plus the patient-stage columns for 6 HCPs. Grain, cohorts, windows, invariants and fill rate are clean. Open: 949 provider rows with null `PROVIDER_ID` and 33 provider IDs outside the universe (provider copy only), run not flagged as run of record, stale doc text, NBA-team drift sign-off.  
**QC run:** 2026-11-27, serverless (Genie Code scratch session), on the output written 2026-11-17 06:14 (`PULL_DT` 2026-11-17, job 1010893614518587, run `full_2026_11_16`). Notebook re-run during QC: **no**. Evidence = read-only queries only; no notebook or table changed.

Rule source = `Feature_Evaluation/05_Feature_Views/NBA_3_1_LAAD_Feature_Views_Readiness_Plan.md` ("readiness"), section 6 (contender views) plus sections 4, 5.4 and 6.2 for Dx. Section 7 (work plan) is out of scope. Developer rules: `NBA_3_1_Dx_Claims_Features_Plan.md` ("plan"), `NBA_3_1_Dx_Claims_Features_Client_Summary.md` ("summary"). `<S>` = `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_nba_3_1`.

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `hcp_level_features/03 Diagnosis Claims Files/03_claim_diagnosis_monthly_cohort` (37 cells). The task brief called it `01_claim_dx_monthly_cohort` |
| Upstream notebooks | `Patient_Journey_Validation/Dx Files/02_patient_journey_dx` (Dx pull, Step 4; brief: `03_patient_journey_dx`); `Combine Files/06_patient_journey_combine_3_1` (patient CKD stage table) |
| Rule file | Readiness sections 4, 5.4, 6, 6.2 |
| Source table | `<S>.full_2026_11_16_pull_dx_step4`: 475,010,310 rows, 283,382 NPIs, 31 Dx codes, `SVC_DT` 2023-01-01 .. 2026-09-30 |
| Patient table | `<S>.full_2026_11_16_pj_pat_new_ckd_stage`: 4,123,720,085 patient-months (`PATIENT_ID`, `SVC_DT_M`, `NEW_CKD_STAGE`) |
| Universe | `<S>.input_hcp_universe`: 294,727 `PROVIDER_ID` |
| Cohorts | `<S>.input_claims_cohorts`: 28 cohorts c1 .. c28, offset 0, lookback end 2024-05 .. 2026-08; Training c1-c24, Testing c25-c26, Holdout c27-c28 |
| Mapping | `query_output/kerendia_nba_3_0_npi_bhid_mapping` (NPI -> `PROVIDER_ID`, `HCP_NPI_MAPPING_TABLE` in `00_cohort_config`) |
| Output (NPI) | `<S>.full_2026_11_16_hcp_claim_diagnosis_monthly_cohort`: 7,588,208 rows x 122 columns (113 features + `NPI_NUMBER` + 8 metadata), 282,971 NPIs |
| Output (provider) | `<S>.full_2026_11_16_hcp_provider_claim_diagnosis_monthly_cohort`: 7,588,997 rows, 282,975 non-null `PROVIDER_ID` |
| Expected grain | One row per `NPI_NUMBER` x `COHORT_ID` **for NPIs with at least one Dx claim from 2023-01-01 to the cohort cutoff** (sparse, not universe x 28) |
| NBA 3.0 counterpart | `03_claim_diagnosis_monthly` -> `ops_pipeline_bkp/notebook_output/provider_claim_diagnosis_monthly` (13,007,970 rows, months 2022-01 .. 2026-09, 127 features) |
| NBA 3.0 final model | 752 features: `/Users/sehar.aejaz.ext@bayer.com/Extra Notebooks/Final NBA 3.0 Modeling Features.xlsx` |

## 2. QC checklist

| # | Check | How | Pass when | Status |
| --- | --- | --- | --- | --- |
| Q1 | HCP universe | Keys, duplicates, rows per cohort vs NPIs with Dx history, provider IDs vs universe, null IDs | 0 duplicates; rows per cohort explained; 0 outside universe | PASS (NPI table); provider copy has open mapping items (F1, F2) |
| Q2 | Right cohorts | Output `COHORT_ID`, `COHORT_MONTH`, `OFFSET_DAYS`, `CUTOFF_DATE`, `SVC_DT_M`, `DATASET` vs `input_claims_cohorts` | 0 mismatches | PASS |
| Q3 | Windows and point-in-time | E = `CUTOFF_DATE` = last day of the lookback end month; N-month window = calendar months (E-N months, E]; `RUNNING_` = 2023-01-01 .. E; edge-day HCP | No claim after E counted | PASS (load-date check N/A: no `INSERT_TS` in the pull) |
| Q4 | Data sources vs readiness | Section 4 Dx row: rows, dates, null NPI, null stage; table history | Same sources, unchanged since the run | PASS |
| Q5 | All features made | 113 expected names (4 windows x {total, 6 Dx stages, 6 patient stages}, 48 `PCT_`, 13 `RUNNING_`) vs output | 0 missing, 0 unexpected | PASS |
| Q6 | Business rules | Readiness section 6 views (V7, V9, F9, F10) and plan rules vs notebook | Match or documented | PASS (differences documented, section 4) |
| Q7 | Fill rate | All 113 features, all / train / test / holdout / c28 | No unexpected nulls; flags explained | PASS |
| Q8 | NBA 3.0 752 coverage | 3 Dx features in the 752 | 0 skipped | PASS |
| Q9 | Preserved vs new | 127 3.0 features vs 113 3.1 | All labelled | PASS |
| Q10 | HCP trace | 6 HCPs x 28 cohorts recomputed from pull + patient table; plus full recompute of all non-patient features | Output = recompute | PASS |
| Q11 | Invariants | Nesting, stage sums, `PCT_`, `RUNNING_` monotonic, no negatives | 0 violations | PASS |
| Q12 | NBA 3.0 output comparison | 3.0 month 2026-08 vs 3.1 c28 on common providers | Differences explained | PASS |
| Q13 | Reproducibility and docs | Delta history, run registry, doc headers | No stale text that changes meaning | OPEN (F3, F4) |
| Q14 | Code basket and data drift (owner: NBA team) | 31 pull codes vs `ref_product_mapping_dx`; monthly volumes (F9 95% rule); active HCPs / 12M claims per `DATASET` | Basket = config; drift <= 20% or explained | Data PASS; NBA-team sign-off OPEN |

## 3. Evidence log

| # | Result (numbers) | Where (query) | Notes |
| --- | --- | --- | --- |
| Q1 | NPI table: 7,588,208 rows = 7,588,208 distinct (`NPI_NUMBER`, `COHORT_ID`), 0 null / blank / '0' NPI, 282,971 NPIs. Rows per cohort rise from 253,390 (c1) to 282,971 (c28). Expected rows per cohort (NPIs whose first pull claim from 2023-01-01 is <= cutoff) = output for **all 28 cohorts, 0 difference**. 411 pull NPIs are absent because their first claim is in Sep 2026 (lag month, after the c28 cutoff). Provider table: 7,588,997 rows, 949 with null `PROVIDER_ID`, 0 duplicate (`PROVIDER_ID`, `COHORT_ID`) among non-null; +789 rows vs the NPI table = NPIs with 2 `PROVIDER_ID`s in the 3.0 mapping. Universe 294,727: 11,785 have no Dx row at all; 33 output `PROVIDER_ID`s are not in the universe. Pull `PROVIDER_ID`: 283,386, all in the universe, 0 null | `count / count distinct` on both outputs; per-cohort recount from `pull_dx_step4` `min(SVC_DT)` per NPI joined to `input_claims_cohorts`; `not exists` vs `input_hcp_universe` | Sparse grain is by design (`combine_features`: NPIs with claims in the 12M window or any history). Downstream must zero-fill missing HCP x cohort rows. The 33 + 949 come from the 3.0 NPI-BHID mapping, not from the pull (summary section 6 open item) |
| Q2 | 28 distinct cohort rows in the output, 28 in the file, full join: **0 mismatches** on `DATASET`, `OFFSET_DAYS` (0), `CUTOFF_DATE` = `last_day(lookback_end_date)`, `SVC_DT_M` = `lookback_end_date`, `COHORT_MONTH`; `PULL_DT` 2026-11-17 on all; `COHORT_SET` 7 groups (C1-C5_training .. C27-C28_backtesting) | `select distinct` metadata from output full join `input_claims_cohorts` | No promotional dates |
| Q3 | Independent recompute (calendar month buckets: `months_between(lookback_end_date, month) between 0 and N-1`; running = month <= lookback end, from 2023-01-01) vs output, every NPI x cohort: 7,588,208 rows joined, 0 rows only on one side, **0 mismatches in 265,587,280 cells** (4 totals, 24 Dx-stage window counts, `RUNNING_TOTAL_DX_CLAIMS` and 6 `RUNNING_` stage columns). Edge case NPI 1003000902: 4 claims on 2026-08-31 (E) counted, 5 on 2026-09-01 (E+1) not; c28 3M = 276 = output | SQL temp views `m` / `rc` on `pull_dx_step4` and the output | The pull has no load timestamp, so late loads can't be tested (readiness 5.4 notes the same) |
| Q4 | Pull: 475,010,310 rows, 2023-01-01 .. 2026-09-30, 0 null `NPI_NUMBER`, 0 null `DX_STAGE`, 0 null `PATIENT_ID`, 0 duplicate NPI x patient x day x code, 31 codes = readiness section 4 (475,010,310). Patient table 4,123,720,085 rows = readiness. Delta history: pull v0 CTAS 2026-11-17 01:31 and patient table v0 2026-11-17 02:47 (both job 1010893614518587); after that only OPTIMIZE / CLUSTER BY / VACUUM, so the inputs are unchanged since the output was written (06:14). Outputs written once (v0 CTAS) in `kerendia_nba_3_1`, nothing in the 3.0 volume | `count`, `min/max`, `describe history` | `CKD_SUBSTAGE` holds only 3a / 3b / ESRD (N18.31, N18.32, N18.6), as readiness section 4 says |
| Q5 | 113 features (65 BIGINT counts, 48 DOUBLE `PCT_`): 52 window, 13 `RUNNING_`, 48 `PCT_`; expected-name list generated from the plan: **0 missing, 0 unexpected**. Includes the 9 `STAGE_5` columns (plan C3). No trend / DIFF / RATIO columns | `spark.table(...).dtypes` vs generated list | Matches summary: 113 features, 122 columns |
| Q6 | See section 4: 8 rules, all match or documented | Notebook cells 7, 16-18, 21, 23, 28, 30 | V7 6.2 rule not applied by design (section 7 work) |
| Q7 | 0 null cells in all 113 features; min >= 0; `PCT_` max = 1. No constant column, no column > 99.5% zero (max 97.60% zero: `..._WITH_PATIENT_NEW_TO_STAGE_1_IN_LAST_1_MONTH`). Train-vs-holdout change > 5 points only on 8 `RUNNING_` columns (stage 1, 2, 4, 5 and patient new-to-stage 1, 2, 4, 5: +5.2 to +8.0 points) | Single-pass Spark aggregate on the output | `RUNNING_` grows with history length from 2023-01-01 (c1 has 17 months, c28 has 44), so later cohorts are more often non-zero. Expected, not a defect; noted for modelling (F6) |
| Q8 | 752 xlsx (Sheet1, 752 rows) has 3 Dx features: `TOTAL_DX_CLAIMS_WITH_PATIENT_NO_NEW_STAGE_IN_LAST_12_MONTH` (rank 314, 0.083% SHAP), `..._NO_NEW_STAGE_IN_LAST_6_MONTH` (rank 537, 0.035%), `TOTAL_DX_CLAIMS_STAGE_UNSPECIFIED_IN_LAST_3_MONTH` (rank 661, 0.016%). All 3 are in the 3.1 output under the same name | `pd.read_excel` (openpyxl installed in the scratch session only); rank by `Mean_Abs_SHAP` | Same 3 as plan D4 / selected-277 |
| Q9 | 3.0 output 127 features vs 3.1 113: 104 same name (preserved), 9 new (`STAGE_5` x 4 windows, 4 `PCT_`, 1 `RUNNING_`), 23 not carried: 12 base-month columns without suffix (e.g. `TOTAL_DX_CLAIMS`, `TOTAL_DX_CLAIMS_STAGE_1`) and 11 base-month `PCT_` columns; 0 other names | Set comparison of column names | Base-month columns = `_IN_LAST_1_MONTH` in the cohort design (NB03 cell 32: parity compares them) |
| Q10 | 6 HCPs x 28 cohorts = 168 rows: patient-stage window and `RUNNING_` columns (30 per row) recomputed by joining the pull to `pj_pat_new_ckd_stage` on patient + claim month: **0 mismatches in 5,040 cells**, 0 unmatched rows. Step values in section 9 | Temp views `tp` / `r` | Non-patient columns of these HCPs are covered by the full Q3 recompute |
| Q11 | 0 violations on 7,588,208 rows: 1M <= 3M <= 6M <= 12M <= `RUNNING_` (total and 12 stage columns); sum of 6 Dx stages = total (4 windows); sum of 6 patient stages = total (4 windows); `PCT_` = count / total, 0 when total = 0 (48 columns, tol 1e-9); `RUNNING_` stage sums = running total; no negatives; `RUNNING_TOTAL_DX_CLAIMS` >= 1 on every row; `RUNNING_TOTAL_DX_CLAIMS` never drops from one cohort to the next for an NPI (0 cases) | Spark aggregate + window `lag` | |
| Q12 | 3.0 month 2026-08 (228,181 providers) vs 3.1 c28 (282,975): 215,683 common. 12M total: HCPs > 0 213,296 -> 263,464; sum on common 77.6M -> 124.9M (+61%), Pearson 0.993. 12M stage 3: 662 -> 236,416 HCPs > 0, sum 2,666 -> 18.2M, Pearson 0.02. 3M stage unspecified: sum 17.5M -> 17.9M (+2%), Pearson 0.999. 12M patient no-new-stage: 72.3M -> 114.6M, Pearson 0.993. Running total: 404.2M -> 440.6M, Pearson 0.981 | Join on `PROVIDER_ID` | Explained by plan F1: 3.0 `Dx_03` lacks N18.30-32, all stage-5 / ESRD codes and T1D codes. Pearson used; Spearman not computed |
| Q13 | Output v0 CTAS 2026-11-17 06:14 (NPI) and 06:18 (provider), 7,588,208 / 7,588,997 rows = Delta `numOutputRows`. `run_registry`: `full_2026_11_16` STATUS SUCCESS, job run 814119312914044, note "NB07: all 11 HCP tables OK", but `IS_RUN_OF_RECORD` = **False**. Stale text: see F4 | `describe history`, `run_registry` | |
| Q14 | 31 pull codes are all in `ref_product_mapping_dx` (basket 2026_11_06); stage / substage / DM type of the pull = config for all 31 (0 mismatches). T1D codes E10.21/22/29: 1,393,020 rows, all `DX_STAGE` 0. Monthly pull rows: Aug 2026 10,920,704 = 97.1% of the median of May-Jul (11,242,322); Sep 2026 (lag month) 10,763,192 = 95.7% of the median of Jun-Aug (11,242,322) -> both meet the 95% rule (readiness 5.4). Drift per `DATASET` (mean per cohort): active HCPs (12M > 0) Training 257,166, Testing 263,176 (+2.3%), Holdout 263,370 (+2.4%); 12M Dx claims 122.7M, 129.8M (+5.8%), 131.1M (+6.9%) | `group by` on pull and output | All below 20%. Needs NBA-team sign-off |

## 4. Business rules (readiness vs notebook)

| Rule | Readiness / plan says (section) | Notebook does (cell / decision) | Match |
| --- | --- | --- | --- |
| Dx input | Section 4: `pull_dx_step4` is ready (0 null NPI, `SVC_DT` DATE); plan C1 | Load cell 7: `load_dx_input()` with `HCP_DX_SOURCE = "3.1"`; null-stage assert. Full recompute from `full_2026_11_16_pull_dx_step4` matches (Q3) | Yes |
| V7 CKD stage mix: claim stage | 6.2: Dx `DX_STAGE_UPDATED` is carried forward as worst-ever; V7 should use the stage **coded** in the period | NB03 counts each claim by the `DX_STAGE` coded on that claim (cell 7 `add_dx_stage_label`, cell 16 pivot), not a carried stage. `CKD_SUBSTAGE` is loaded but not used (no 3a / 3b columns) | Yes (claim-level coded stage); 3a / 3b split not in NB03 |
| V7: patient stage | 6.2 recommends lab eGFR first, Dx fallback, for the new V7 view | `TOTAL_DX_CLAIMS_WITH_PATIENT_*` read `NEW_CKD_STAGE` from `pj_pat_new_ckd_stage`, built by PJ06 with the current Dx-first rule (`coalesce(DX_STAGE_UPDATED, GFR_STAGE, UACR_STAGE)`), same as 3.0 | Documented difference: the 6.2 rule is for the new V7 view (section 7, out of scope). These existing features keep the 3.0 definition (F5) |
| V9 T1D + CKD | Section 6: uses `DM_TYPE`, `DX_STAGE` of the pull; plan D5 keep or drop T1D codes | T1D codes kept and counted as stage unspecified (summary update: "T1D codes kept"); 1,393,020 pull rows, all stage 0 | Yes (decision applied). No T1D-specific feature in NB03; V9 itself is Track C work |
| F9 completeness | 5.4: data end = last month with >= 95% of the median of the 3 months before | No completeness flag in NB03 (Track C). Last feature month Aug 2026 = 97.1%, so no window shift is needed for this run | Yes for this run; flag not built (out of scope) |
| F10 trends | Section 6: 3 months vs previous 3 | No trend columns in NB03 (Q5) | N/A, not in NB03 |
| V2, V10 | Rx claim type; lab | Not Dx | N/A |
| V1, V3, V6, V8 | Rx output / patient state + HCP-patient bridge | Not in NB03 | N/A |
| Windows | Plan: 1, 3, 6, 12 months; `RUNNING_` from `DATA_START_DATE` | Cells 5, 16, 17: `DX_LOOKBACK_WINDOWS = (1, 3, 6, 12)`; option B `SVC_DT >= DATA_START_DATE` (2023-01-01) | Yes (Q3) |
| Fixed pivot / `STAGE_5` | Plan C3 / decision X4 | Cell 7: fixed `DX_STAGE_VALUES` with `STAGE_5`; 9 new columns present | Yes |
| `PCT_` | Plan: count / window total, 0.0 when total is 0 (readiness 5.3 says null for new Track C features) | Cell 21: `otherwise(0.0)` | Yes for NB03 (3.0 definition kept); the null rule applies to new Track C views only |
| Provider mapping | Summary section 6: keep the 3.0 mapping; fix for unmapped / double-mapped HCPs open | Cell 30: left join to the 3.0 mapping, NPI dropped | Yes; open item still open (F1, F2) |

## 5. Data sources (readiness vs notebook)

| Source | Readiness says | Notebook uses | Rows / dates found | Match |
| --- | --- | --- | --- | --- |
| Dx pull | `full_2026_11_16_pull_dx_step4`, 475,010,310 rows, 2023-01-01 .. 2026-09-30 | `HCP_DX_TABLE` (3.1 pull) | 475,010,310; 2023-01-01 .. 2026-09-30; 283,382 NPIs; 31 codes; 0 null NPI / stage / patient | Yes |
| Patient CKD stage | `full_2026_11_16_pj_pat_new_ckd_stage`, 4,123,720,085, months 2023-01 .. 2026-09 | `get_patient_table_path("new_ckd_stage")` | 4,123,720,085; trace on 6 HCPs with this table = output (0 mismatches) | Yes |
| Cohorts | `input_claims_cohorts`, 28 | `get_hcp_cohort_months()` | 28; 0 mismatches (Q2) | Yes |
| Universe | `input_hcp_universe`, keyed by `PROVIDER_ID` | Pull already limited to the universe (PJ02) | 294,727; all 283,386 pull `PROVIDER_ID` in it | Yes |
| NPI mapping | O2: confirm the mapping | 3.0 `kerendia_nba_3_0_npi_bhid_mapping` | 949 null-ID rows, 33 IDs outside universe in the provider copy | Open (F1, F2) |
| Code basket | Final Dx basket | `ref_product_mapping_dx` (2026_11_06) | 31 / 31 codes and stage mappings match | Yes |

## 6. Features made (plan vs output)

| Plan family | Expected (plan / summary) | Output columns | Status |
| --- | --- | --- | --- |
| Total Dx claims per window | 4 (1, 3, 6, 12M) | 4 | PASS |
| Dx stage per window | 6 stages (1-5, unspecified) x 4 = 24 | 24 | PASS |
| Patient new-to-stage per window | 6 (new to 1-5, no new stage) x 4 = 24 | 24 | PASS |
| `RUNNING_` | 1 total + 6 stages + 6 patient stages = 13 | 13 | PASS |
| `PCT_` | 12 per window x 4 = 48 | 48 | PASS |
| **Total** | **113** (summary: 3.0 104 -> 3.1 113) | **113**, 0 missing, 0 unexpected | PASS |
| Readiness section 6 (V7, V9, F9, F10) | Track C views | None in NB03 (section 7 work) | N/A by scope |

## 7. Fill rate

% over all 7,588,208 output rows (only HCP x cohorts with Dx history, see Q1). No sentinel values in this notebook. 0% null on all 113 features. A `PCT_` column is non-zero exactly when its count column is (Q11: `PCT_` = count / total, 0 violations), so they are not repeated.

| Feature | % null | % zero | % non-zero | min / max | % non-zero train / test / holdout / c28 | Flag |
| --- | --- | --- | --- | --- | --- | --- |
| `TOTAL_DX_CLAIMS_IN_LAST_1_MONTH` | 0 | 28.54 | 71.46 | 0 / 15,663 | 71.65 / 70.84 / 69.93 / 69.40 | |
| `TOTAL_DX_CLAIMS_IN_LAST_3_MONTH` | 0 | 16.22 | 83.78 | 0 / 44,492 | 84.00 / 82.76 / 82.26 / 82.10 | |
| `TOTAL_DX_CLAIMS_IN_LAST_6_MONTH` | 0 | 9.94 | 90.06 | 0 / 88,159 | 90.36 / 88.37 / 88.27 / 88.23 | |
| `TOTAL_DX_CLAIMS_IN_LAST_12_MONTH` | 0 | 4.79 | 95.21 | 0 / 169,770 | 95.55 / 93.41 / 93.15 / 93.10 | |
| `TOTAL_DX_CLAIMS_STAGE_1_IN_LAST_1_MONTH` | 0 | 95.75 | 4.25 | 0 / 437 | 4.24 / 4.37 / 4.28 / 4.21 | |
| `TOTAL_DX_CLAIMS_STAGE_2_IN_LAST_1_MONTH` | 0 | 82.23 | 17.77 | 0 / 1,959 | 17.66 / 18.58 / 18.27 / 18.10 | |
| `TOTAL_DX_CLAIMS_STAGE_3_IN_LAST_1_MONTH` | 0 | 47.52 | 52.48 | 0 / 1,720 | 52.43 / 53.04 / 52.53 / 52.09 | |
| `TOTAL_DX_CLAIMS_STAGE_4_IN_LAST_1_MONTH` | 0 | 73.58 | 26.42 | 0 / 475 | 26.43 / 26.47 / 26.27 / 25.91 | |
| `TOTAL_DX_CLAIMS_STAGE_5_IN_LAST_1_MONTH` | 0 | 71.74 | 28.26 | 0 / 5,381 | 28.34 / 28.02 / 27.58 / 27.23 | |
| `TOTAL_DX_CLAIMS_STAGE_UNSPECIFIED_IN_LAST_1_MONTH` | 0 | 35.64 | 64.36 | 0 / 9,915 | 64.56 / 63.73 / 62.73 / 62.19 | |
| `TOTAL_DX_CLAIMS_STAGE_1_IN_LAST_3_MONTH` | 0 | 91.59 | 8.41 | 0 / 1,049 | 8.37 / 8.74 / 8.57 / 8.54 | |
| `TOTAL_DX_CLAIMS_STAGE_2_IN_LAST_3_MONTH` | 0 | 70.30 | 29.70 | 0 / 4,780 | 29.47 / 31.24 / 30.82 / 30.75 | |
| `TOTAL_DX_CLAIMS_STAGE_3_IN_LAST_3_MONTH` | 0 | 32.11 | 67.89 | 0 / 5,019 | 67.84 / 68.32 / 67.94 / 67.81 | |
| `TOTAL_DX_CLAIMS_STAGE_4_IN_LAST_3_MONTH` | 0 | 58.73 | 41.27 | 0 / 1,272 | 41.23 / 41.63 / 41.34 / 41.29 | |
| `TOTAL_DX_CLAIMS_STAGE_5_IN_LAST_3_MONTH` | 0 | 59.05 | 40.95 | 0 / 15,483 | 41.01 / 40.82 / 40.37 / 40.16 | |
| `TOTAL_DX_CLAIMS_STAGE_UNSPECIFIED_IN_LAST_3_MONTH` (752: rank 661) | 0 | 21.82 | 78.18 | 0 / 28,057 | 78.41 / 77.18 / 76.56 / 76.37 | |
| `TOTAL_DX_CLAIMS_STAGE_1_IN_LAST_6_MONTH` | 0 | 87.61 | 12.39 | 0 / 1,854 | 12.34 / 12.61 / 12.75 / 12.76 | |
| `TOTAL_DX_CLAIMS_STAGE_2_IN_LAST_6_MONTH` | 0 | 61.09 | 38.91 | 0 / 8,768 | 38.66 / 40.13 / 40.57 / 40.63 | |
| `TOTAL_DX_CLAIMS_STAGE_3_IN_LAST_6_MONTH` | 0 | 23.35 | 76.65 | 0 / 9,141 | 76.70 / 76.33 / 76.42 / 76.40 | |
| `TOTAL_DX_CLAIMS_STAGE_4_IN_LAST_6_MONTH` | 0 | 48.72 | 51.28 | 0 / 2,443 | 51.28 / 51.23 / 51.41 / 51.44 | |
| `TOTAL_DX_CLAIMS_STAGE_5_IN_LAST_6_MONTH` | 0 | 49.66 | 50.34 | 0 / 29,682 | 50.45 / 49.71 / 49.74 / 49.71 | |
| `TOTAL_DX_CLAIMS_STAGE_UNSPECIFIED_IN_LAST_6_MONTH` | 0 | 14.38 | 85.62 | 0 / 55,435 | 85.93 / 83.90 / 83.79 / 83.75 | |
| `TOTAL_DX_CLAIMS_STAGE_1_IN_LAST_12_MONTH` | 0 | 82.31 | 17.69 | 0 / 2,854 | 17.64 / 17.97 / 17.99 / 17.97 | |
| `TOTAL_DX_CLAIMS_STAGE_2_IN_LAST_12_MONTH` | 0 | 50.96 | 49.04 | 0 / 15,368 | 48.82 / 50.16 / 50.38 / 50.43 | |
| `TOTAL_DX_CLAIMS_STAGE_3_IN_LAST_12_MONTH` | 0 | 15.61 | 84.39 | 0 / 14,784 | 84.53 / 83.61 / 83.55 / 83.54 | |
| `TOTAL_DX_CLAIMS_STAGE_4_IN_LAST_12_MONTH` | 0 | 38.24 | 61.76 | 0 / 4,092 | 61.83 / 61.35 / 61.38 / 61.41 | |
| `TOTAL_DX_CLAIMS_STAGE_5_IN_LAST_12_MONTH` | 0 | 39.17 | 60.83 | 0 / 58,070 | 61.05 / 59.62 / 59.57 / 59.55 | |
| `TOTAL_DX_CLAIMS_STAGE_UNSPECIFIED_IN_LAST_12_MONTH` | 0 | 8.07 | 91.93 | 0 / 107,152 | 92.27 / 90.10 / 89.86 / 89.81 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_1_IN_LAST_1_MONTH` | 0 | 97.60 | 2.40 | 0 / 275 | 2.38 / 2.44 / 2.54 / 2.46 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_2_IN_LAST_1_MONTH` | 0 | 89.73 | 10.27 | 0 / 556 | 10.22 / 10.50 / 10.50 / 10.35 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_3_IN_LAST_1_MONTH` | 0 | 71.52 | 28.48 | 0 / 880 | 28.71 / 27.38 / 27.02 / 26.61 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_4_IN_LAST_1_MONTH` | 0 | 86.62 | 13.38 | 0 / 383 | 13.42 / 13.14 / 13.18 / 12.96 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_5_IN_LAST_1_MONTH` | 0 | 91.17 | 8.83 | 0 / 1,478 | 8.91 / 8.48 / 8.27 / 7.98 | |
| `..._WITH_PATIENT_NO_NEW_STAGE_IN_LAST_1_MONTH` | 0 | 31.59 | 68.41 | 0 / 15,033 | 68.55 / 68.06 / 67.16 / 66.70 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_1_IN_LAST_3_MONTH` | 0 | 94.28 | 5.72 | 0 / 653 | 5.69 / 5.75 / 6.02 / 6.08 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_2_IN_LAST_3_MONTH` | 0 | 79.21 | 20.79 | 0 / 1,215 | 20.68 / 21.37 / 21.37 / 21.39 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_3_IN_LAST_3_MONTH` | 0 | 51.74 | 48.26 | 0 / 2,103 | 48.50 / 47.27 / 46.59 / 46.40 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_4_IN_LAST_3_MONTH` | 0 | 72.82 | 27.18 | 0 / 994 | 27.22 / 27.11 / 26.82 / 26.84 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_5_IN_LAST_3_MONTH` | 0 | 82.01 | 17.99 | 0 / 2,000 | 18.09 / 17.60 / 17.24 / 17.14 | |
| `..._WITH_PATIENT_NO_NEW_STAGE_IN_LAST_3_MONTH` | 0 | 18.70 | 81.30 | 0 / 42,862 | 81.48 / 80.54 / 80.04 / 79.90 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_1_IN_LAST_6_MONTH` | 0 | 90.50 | 9.50 | 0 / 886 | 9.50 / 9.25 / 9.69 / 9.75 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_2_IN_LAST_6_MONTH` | 0 | 69.54 | 30.46 | 0 / 2,345 | 30.38 / 30.62 / 31.19 / 31.27 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_3_IN_LAST_6_MONTH` | 0 | 38.46 | 61.54 | 0 / 3,491 | 61.84 / 59.74 / 59.81 / 59.73 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_4_IN_LAST_6_MONTH` | 0 | 61.07 | 38.93 | 0 / 1,720 | 39.01 / 38.35 / 38.57 / 38.57 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_5_IN_LAST_6_MONTH` | 0 | 73.24 | 26.76 | 0 / 3,254 | 26.89 / 26.07 / 25.95 / 25.84 | |
| `..._WITH_PATIENT_NO_NEW_STAGE_IN_LAST_6_MONTH` (752: rank 537) | 0 | 12.01 | 87.99 | 0 / 85,204 | 88.25 / 86.52 / 86.47 / 86.44 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_1_IN_LAST_12_MONTH` | 0 | 84.56 | 15.44 | 0 / 1,435 | 15.56 / 14.62 / 14.88 / 14.93 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_2_IN_LAST_12_MONTH` | 0 | 57.51 | 42.49 | 0 / 3,067 | 42.53 / 42.09 / 42.38 / 42.43 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_3_IN_LAST_12_MONTH` | 0 | 25.93 | 74.07 | 0 / 6,434 | 74.50 / 71.71 / 71.54 / 71.50 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_4_IN_LAST_12_MONTH` | 0 | 47.91 | 52.09 | 0 / 2,972 | 52.29 / 50.96 / 50.93 / 50.92 | |
| `..._WITH_PATIENT_NEW_TO_STAGE_5_IN_LAST_12_MONTH` | 0 | 61.82 | 38.18 | 0 / 3,586 | 38.46 / 36.60 / 36.51 / 36.46 | |
| `..._WITH_PATIENT_NO_NEW_STAGE_IN_LAST_12_MONTH` (752: rank 314) | 0 | 6.43 | 93.57 | 0 / 164,826 | 93.88 / 91.96 / 91.73 / 91.69 | |
| `RUNNING_TOTAL_DX_CLAIMS` | 0 | 0.00 | 100.00 | 1 / 481,004 | 100 / 100 / 100 / 100 | |
| `RUNNING_TOTAL_DX_CLAIMS_STAGE_1` | 0 | 72.06 | 27.94 | 0 / 8,480 | 27.08 / 32.48 / 33.28 / 33.47 | train-holdout > 5 pts |
| `RUNNING_TOTAL_DX_CLAIMS_STAGE_2` | 0 | 36.26 | 63.74 | 0 / 42,923 | 62.63 / 69.62 / 70.59 / 70.82 | train-holdout > 5 pts |
| `RUNNING_TOTAL_DX_CLAIMS_STAGE_3` | 0 | 7.52 | 92.48 | 0 / 51,969 | 92.12 / 94.37 / 94.63 / 94.69 | |
| `RUNNING_TOTAL_DX_CLAIMS_STAGE_4` | 0 | 24.14 | 75.86 | 0 / 13,076 | 75.04 / 80.18 / 80.87 / 81.04 | train-holdout > 5 pts |
| `RUNNING_TOTAL_DX_CLAIMS_STAGE_5` | 0 | 24.32 | 75.68 | 0 / 187,199 | 74.92 / 79.67 / 80.33 / 80.48 | train-holdout > 5 pts |
| `RUNNING_TOTAL_DX_CLAIMS_STAGE_UNSPECIFIED` | 0 | 2.04 | 97.96 | 0 / 306,261 | 97.86 / 98.49 / 98.55 / 98.56 | |
| `RUNNING_..._WITH_PATIENT_NEW_TO_STAGE_1` | 0 | 69.80 | 30.20 | 0 / 3,183 | 29.43 / 34.21 / 35.05 / 35.24 | train-holdout > 5 pts |
| `RUNNING_..._WITH_PATIENT_NEW_TO_STAGE_2` | 0 | 37.46 | 62.54 | 0 / 9,429 | 61.57 / 67.65 / 68.59 / 68.82 | train-holdout > 5 pts |
| `RUNNING_..._WITH_PATIENT_NEW_TO_STAGE_3` | 0 | 11.23 | 88.77 | 0 / 16,557 | 88.42 / 90.63 / 90.98 / 91.07 | |
| `RUNNING_..._WITH_PATIENT_NEW_TO_STAGE_4` | 0 | 28.19 | 71.81 | 0 / 7,373 | 71.02 / 75.95 / 76.67 / 76.85 | train-holdout > 5 pts |
| `RUNNING_..._WITH_PATIENT_NEW_TO_STAGE_5` | 0 | 37.98 | 62.02 | 0 / 12,264 | 61.30 / 65.76 / 66.47 / 66.63 | train-holdout > 5 pts |
| `RUNNING_..._WITH_PATIENT_NO_NEW_STAGE` | 0 | 1.32 | 98.68 | 0 / 464,733 | 98.60 / 99.12 / 99.17 / 99.18 | |
| 48 `PCT_` columns | 0 | = count column | = count column | 0 / 1 | = count column | |

## 8. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature | In 752? (SHAP rank, % SHAP) | NBA 3.1 feature | Status | Reason |
| --- | --- | --- | --- | --- |
| `TOTAL_DX_CLAIMS_WITH_PATIENT_NO_NEW_STAGE_IN_LAST_12_MONTH` | Yes (314, 0.083%) | same name | Preserved | Same logic; values about +58% on common HCPs (Q12) because stage 3 / 5 codes are now counted |
| `TOTAL_DX_CLAIMS_WITH_PATIENT_NO_NEW_STAGE_IN_LAST_6_MONTH` | Yes (537, 0.035%) | same name | Preserved | As above |
| `TOTAL_DX_CLAIMS_STAGE_UNSPECIFIED_IN_LAST_3_MONTH` | Yes (661, 0.016%) | same name | Preserved | Sum +2% on common HCPs; some claims move to stage 3 / 5, T1D codes added |
| Other 101 window / `RUNNING_` / `PCT_` features | No | same names | Preserved | Same definition, 3.1 input |
| 12 base-month columns without suffix (e.g. `TOTAL_DX_CLAIMS`, `TOTAL_DX_CLAIMS_STAGE_1`, `TOTAL_DX_CLAIMS_WITH_PATIENT_NO_NEW_STAGE`) | No | `..._IN_LAST_1_MONTH` | Replaced (duplicate dropped) | In the cohort design the base month = the 1-month window (NB03 cell 32) |
| 11 base-month `PCT_` columns | No | `PCT_..._IN_LAST_1_MONTH` | Replaced (duplicate dropped) | As above |
| - | - | `TOTAL_DX_CLAIMS_STAGE_5_IN_LAST_{1,3,6,12}_MONTH`, 4 `PCT_`, `RUNNING_TOTAL_DX_CLAIMS_STAGE_5` | New (9) | Plan C3 / decision X4: 3.0 `Dx_03` had no stage-5 / ESRD codes |

## 9. HCP trace (step-by-step recompute)

Cases chosen by query: high volume (top `RUNNING_` at c28), stage-5 heavy, the config trace HCP, T1D codes in Jun-Aug 2026, no claims in the 12M window at c28, and window edge (claims on 2026-08-31 and 2026-09-01). c1 is the training cohort case. Counts are rows of `pull_dx_step4`.

| Step | What | 1477623635 high volume | 1013186808 stage 5 | 1841364841 trace HCP | 1013413517 T1D | 1295711950 no 12M claims | 1003000902 window edge |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | In universe / pull (`PROVIDER_ID` in universe) | yes | yes | yes | yes | yes | yes |
| 2 | Raw pull rows (all dates) | 492,070 | 2,321 | 2,670 | 3,261 | 49,495 | 6,772 |
| 3 | After source filter (`SVC_DT` >= 2023-01-01) | 492,070 | 2,321 | 2,670 | 3,261 | 49,495 | 6,772 |
| 4 | `SVC_DT` <= E (c28, 2026-08-31) = expected `RUNNING_TOTAL_DX_CLAIMS` | 481,004 | 2,321 | 2,610 | 3,132 | 49,495 | 6,681 |
| 5 | On E (in) / on E+1 2026-09-01 (out) | 693 / 454 | 0 / 0 | 3 / 2 | 0 / 31 | 0 / 0 | 4 / 5 |
| 6 | c28 3M window (Jun-Aug 2026) / 12M window (Sep 2025-Aug 2026) | 34,529 / 139,620 | 0 / 110 | 119 / 560 | 582 / 1,753 | 0 / 0 | 276 / 1,761 |
| 7 | Derived: 12M stage 5 / 12M T1D rows / c1 12M (Jun 2023-May 2024) | 48,135 / 39 / 118,000 | 110 / 0 / 1,130 | 203 / 0 / 764 | 247 / 87 / 323 | 0 / 0 / 22,900 | 0 / 27 / 1,445 |
| 8 | Output c28: running / 3M / 12M / 12M stage 5 / `PCT_` stage 5 12M; c1 12M | 481,004 / 34,529 / 139,620 / 48,135 / 0.3448 / 118,000 | 2,321 / 0 / 110 / 110 / 1.0 / 1,130 | 2,610 / 119 / 560 / 203 / 0.3625 / 764 | 3,132 / 582 / 1,753 / 247 / 0.1409 / 323 | 49,495 / 0 / 0 / 0 / 0.0 / 22,900 | 6,681 / 276 / 1,761 / 0 / 0.0 / 1,445 |
| | Step 7 = step 8 | yes | yes | yes | yes | yes | yes |

Patient-stage columns of these 6 HCPs (24 window + 6 `RUNNING_` per row, 28 cohorts): 5,040 cells, 0 mismatches (Q10). For 1013413517 the T1D rows (87 in 12M) are part of `TOTAL_DX_CLAIMS_STAGE_UNSPECIFIED_IN_LAST_12_MONTH` = 1,105.

## 10. Findings and actions

| # | Finding | Severity | Action / owner | Status |
| --- | --- | --- | --- | --- |
| F1 | Provider copy: 949 rows with null `PROVIDER_ID` (NPIs missing from the 3.0 NPI-BHID mapping); 698 on the 2026-11-04 run per summary | fix | Apply the agreed rule (take the `PROVIDER_ID` of the 3.1 input for these HCPs) in all six HCP notebooks / NBA team | Open |
| F2 | Provider copy: 33 `PROVIDER_ID`s not in `input_hcp_universe`, and +789 rows from NPIs with 2 IDs in the 3.0 mapping. The pull itself has all IDs in the universe | fix | Same fix as F1 (O2) / NBA team | Open |
| F3 | `run_registry`: `full_2026_11_16` SUCCESS but `IS_RUN_OF_RECORD` = False | doc | Flag the run of record before the outputs are used for modelling / registered (Track R) / NBA team | Open |
| F4 | Stale text: plan header "Validation set: 10 test HCPs, 20 cohorts ... offset 7" and outputs as `notebook_output/...` (now UC tables, 28 cohorts, offset 0); summary body "120 in total" and "T1D: open point" (update banner says 122 columns, T1D kept); notebook title cell "Open: where the pull is stored, specialty filter / HCP universe, T1D codes" | doc | Update the plan header, summary body and title cell / developer | Open |
| F5 | Patient-stage features use the current Dx-first `NEW_CKD_STAGE`; readiness 6.2 recommends lab-first for V7. Not a defect for NB03 (3.0 definition kept) | note | Keep in mind when V7 is built (section 7) | Noted |
| F6 | Sparse grain: HCP x cohorts without Dx history have no row (e.g. 11,785 universe HCPs never appear). 8 `RUNNING_` columns are non-zero more often in later cohorts (+5 to +8 points) because history grows from 2023-01-01 | note | Downstream combine must zero-fill; consider this drift in feature selection / NBA team | Noted |
| F7 | Point-in-time on load date can't be tested (no `INSERT_TS`); Aug 2026 volume 97.1% and Sep 2026 95.7% of the 3-month median, so no thin month in this run | note | F9 flag is Track C work | Noted |

## 11. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 12 / 14 (Q13 open: F3, F4; Q14 data pass, waiting for NBA-team sign-off) |
| QC by / date | Genie Code for Saurabh Modi, 2026-11-27 |
| O5 and drift review (NBA team) / date | |
| Reviewed by / date | |
| Next | Close F1-F4; NBA-team sign-off on Q14 drift |
