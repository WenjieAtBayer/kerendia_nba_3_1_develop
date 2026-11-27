# QC 02: Lab claims features, NBA 3.1

**QC status:** DONE, 2026-11-27 (claim type Lab; plan: `02_lab_claims_features_qc_plan.md`)  
**Verdict:** PASS with actions. Counting logic, windows, cohorts and grain are proven (independent recount 0 mismatches, 6-HCP trace 24,024 cells 0 mismatches). Open: the 24 eligible-patient columns use the stale `pj_pat_sglt2_filter_m` (77% eligible, pre-C1), 8,641 duplicate pull rows, K / HbA1c volume drift in holdout, and doc text.  
**QC run:** 2026-11-27, serverless, on the output written 2026-11-17 (`PULL_DT` 2026-11-17, Delta v0 03:22, job 1010893614518587). Notebook re-run during QC: no.

Rule source for this QC = `../Feature_Evaluation/05_Feature_Views/NBA_3_1_LAAD_Feature_Views_Readiness_Plan.md` ("readiness"), section 6 plus the Lab rows of sections 4, 5.3, 5.4 and 6.2; developer rules = `NBA_3_1_Lab_Claims_Features_Plan.md`, `NBA_3_1_Lab_Claims_Features_Client_Summary.md`, decisions X13-X24. Section 7 (work plan) out of scope. All evidence from read-only queries; no notebook or table changed. Catalog prefix `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_nba_3_1.` omitted below.

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `hcp_level_features/02 Lab Claims Files/02_claim_lab_monthly_cohort` (37 cells) |
| Rule file | Readiness sections 4, 5.3, 5.4, 6, 6.2 (replaces `60_ftp_copay...`) |
| Source table | `full_2026_11_16_pull_lab_step4` (PJ01 `03_patient_journey_labs` Step 4): 307,461,581 rows, 2023-01-01 .. 2026-09-30; GFR 174,588,290 / UACR 32,918,919 / POTASSIUM 61,583,584 / HBA1C 38,370,788 rows. Eligibility: `full_2026_11_16_pj_pat_sglt2_filter_m` (PJ06 `06_patient_journey_combine_3_1`), 4,123,720,085 patient-months, used only by the 24 `ELIGIBLE_PATIENTS` columns (cell 25) |
| Universe | `input_hcp_universe`: 294,727 `PROVIDER_ID` |
| Cohorts | `input_claims_cohorts`: family `claims`, offset 0, c1 to c28 (Training c1-c24, Testing c25-c26, Holdout c27-c28) |
| Mapping | `HCP_NPI_MAPPING_TABLE` (3.0 query_output, NPI -> `PROVIDER_ID`, cell 31) |
| Output | `full_2026_11_16_hcp_claim_lab_monthly_cohort`: 5,165,946 rows x 152 columns (143 features + 9 metadata), 199,122 NPIs; provider version `full_2026_11_16_hcp_provider_claim_lab_monthly_cohort`: 5,166,454 rows, 199,149 `PROVIDER_ID` |
| Expected grain | One row per `NPI_NUMBER` x `COHORT_ID` from the first cohort whose cutoff is on or after the NPI's first GFR / UACR test (not universe x 28) |
| NBA 3.0 counterpart | `02_claim_lab_monthly`; output `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/claim_lab_monthly_ZS` (119 columns, 116 features) |
| NBA 3.0 final model | 752 features: `/Users/sehar.aejaz.ext@bayer.com/Extra Notebooks/Final NBA 3.0 Modeling Features.xlsx` |

## 2. QC checklist

| # | Check | How | Pass when | Status |
| --- | --- | --- | --- | --- |
| Q1 | HCP universe | Keys, rows per cohort, duplicates, placeholder IDs; expected rows rebuilt from the pull; provider IDs vs universe | 0 duplicates, gap fully explained | PASS |
| Q2 | Right cohorts | Output cohort fields vs `input_claims_cohorts` | 0 mismatches | PASS |
| Q3 | Windows and point-in-time | E = `CUTOFF_DATE`; test counted if `SVC_DT` in [1st of (E month - N + 1), E]; `RUNNING_` from 2023-01-01; independent recount per cohort x window; edge day | 0 mismatches; E in, E + 1 out | PASS (load-date PIT not testable: no `INSERT_TS`) |
| Q4 | Data sources vs readiness | Section 4 Lab row: rows, dates, nulls, dedup (S3); eligibility table | Same sources, differences explained | PASS (findings F1, F2) |
| Q5 | All features made | Output columns vs families (plan + X18 / X19); section 6 views | 0 missing, 0 unexpected | PASS |
| Q6 | Business rules | Stage mapping, `PCT_` rule, flag thresholds, eligibility rule, section 6 (V10, V6, V7) | Each rule matches or difference documented | FAIL (eligible columns use pre-C1 eligibility, F1) |
| Q7 | Fill rate | All 143 features, all / train / test / holdout / c28 | No unexpected nulls; flags explained | PASS |
| Q8 | NBA 3.0 752 coverage | 752 xlsx vs NB02 columns | 0 skipped without reason | PASS |
| Q9 | Preserved vs new | 3.0 ZS columns vs 3.1 columns | All labelled | PASS |
| Q10 | HCP trace | 6 NPIs x 28 cohorts, all 143 features, recomputed in pandas from pull + eligibility | Output = recompute | PASS |
| Q11 | Invariants | Full table: nesting, sums, `RUNNING_` >= 12M, eligible <= all, flagged <= tested, `PCT_` in [0, 1] | 0 violations | PASS |
| Q12 | NBA 3.0 output comparison | 3.0 ZS 2026-08 vs 3.1 c28, common NPIs | Differences explained | PASS |
| Q13 | Reproducibility and docs | Delta history, `PULL_DT`, input versions, stale text | No stale text that changes meaning | OPEN (F5, F6) |
| Q14 | Test basket and data drift (owner: NBA team) | Test types vs `LAB_STAGED_TESTS` + `LAB_FLAG_RULES`; per `DATASET` volumes; F9 monthly completeness (5.4) | Basket = config; drift > 20% explained and signed off | OPEN (F4: K tested holdout +27%) |

## 3. Evidence log

| # | Result (numbers) | Where (query / cell) | Notes |
| --- | --- | --- | --- |
| Q1 | 5,165,946 rows = 5,165,946 distinct NPI x cohort; 0 null / `'0'` / empty NPI. Rows per cohort c1 164,347 rising to c28 199,122. Rebuilt expected rows (NPI with first GFR / UACR test <= cutoff) = 5,165,946: 0 missing, 0 extra. Provider: 0 null `PROVIDER_ID`, 0 duplicates on `PROVIDER_ID` x cohort, 199,149 IDs (+27 vs NPIs, +508 rows = NPI fan-out); 21 `PROVIDER_ID` not in `input_hcp_universe`. 672 NPIs (2,201 pull rows) have only potassium / HbA1c tests and get no row | QC query Q1 on output, provider output, pull, universe | Grid gap 199,122 x 28 = 5,575,416 vs 5,165,946 fully explained by first-test rule (cell 17). F3, F7 |
| Q2 | 28 cohorts; `COHORT_MONTH` = lookback end month, `OFFSET_DAYS` 0, `CUTOFF_DATE` = last day of lookback end, `SVC_DT_M` = lookback end, `DATASET` = file: 0 mismatches; 28 distinct metadata rows; 7 `COHORT_SET` groups | Full join output metadata vs `input_claims_cohorts` | Cutoffs 2024-05-31 .. 2026-08-31 |
| Q3 | Independent recount of `TOTAL_LAB_CLAIMS_IN_LAST_{1,3,6,12}_MONTH` and `RUNNING_TOTAL_LAB_CLAIMS` summed per cohort: 140 cells, 0 mismatches (6,508,165,620 tests). Edge NPI 1205840931: test on 2026-08-31 counted, test on 2026-09-01 not (c28 1M = 78 = Aug count) | QC recount from pull; trace | Sep 2026 (lag month) never counted. First QC attempt used `add_months` on month-ends and gave 32 false mismatches (QC query bug, fixed) |
| Q4 | Pull rows 307,461,581 = readiness section 4; 0 null NPI / patient / date; 0 GFR or UACR without stage; 0 K / HbA1c without value. 8,641 duplicate rows on NPI x patient x day x test (GFR 7,117, UACR 754, K 422, HbA1c 348): every one has 2 `PROVIDER_ID`s, same value and stage. `sglt2_filter_m`: 3,174,179,271 of 4,123,720,085 patient-months eligible (77.0%) | Pull profile; group-by on key; eligibility profile | Inputs written in the same run before NB02 (pull v0 01:39, eligibility v0 03:01, output 03:22) and only OPTIMIZE / VACUUM since. F1, F2 |
| Q5 | 143 features: TEST_TYPE 8, STAGE 32, TOTAL 4, `RUNNING_` 11, `PCT_` 40 (= 95 base), flag features 48 (K / HbA1c x all / eligible x tested / flag / `PCT_` x 4 windows). No 9M, trend, DIFF, 3a / 3b columns | Column scan of output | Matches X18 (+48) and the 95 base names |
| Q6 | 0 violations (12M): total = GFR + UACR; GFR = sum of 5 stages; UACR = A1 + A2 + A3; `PCT_` = count / total and 0.0 when total 0; K `PCT_` = flagged / tested. Pull stage ranges: eGFR 1 = 90-200, 2 = 60-<90, 3 = 30-<60, 4 = 15-<30, 5 = 1-<15; UACR A1 <30, A2 30-<300, A3 300-10,000. Flags: K > 5.0 on 7.32% of K tests, HbA1c >= 9 on 4.54%. Eligible share of tested patient-months in output: K 68.6%, HbA1c 66.1% | Rule queries on output and pull; cells 8, 19, 25; config `LAB_FLAG_RULES` | Eligible share follows the stale 77% table (F1) |
| Q7 | 0 null, 0 constant, 0 > 99.5% zero, 0 negative; all `PCT_` in [0, 1]. 7 train-vs-holdout > 5 points: `RUNNING_` A3 / stage 4 / stage 5 (cumulative, grow with time) and K > 5 1M (all and eligible, count and `PCT_`) | Fill-rate scan, all 143 features | See section 7, F4 |
| Q8 | 752 xlsx (752 rows): 0 NB02 columns. Lab SHAP only from 7 accelerator features (e.g. rank 67 GFR patients 360d 0.31%, rank 142 GFR first occurrence 0.18%), not NB02 | xlsx read | No NB02 feature in the 3.0 model |
| Q9 | 3.0 ZS: 116 features = 95 with the same 3.1 name + 21 base-month columns without suffix, identical to `_IN_LAST_1_MONTH` (dropped as duplicates); 48 new; 0 unlabelled | Column map ZS vs 3.1 | 3.0 ZS has windows 1 / 3 / 6 / 12 only; no 9M columns (F6) |
| Q10 | 168 rows (6 NPIs x 28), same keys; 24,024 cells, 0 mismatches | pandas recompute from pull + eligibility | Section 9 |
| Q11 | Nesting 1 <= 3 <= 6 <= 12 (19 count bases): 0; `RUNNING_` < 12M: 0; eligible > all: 0; flagged > tested: 0; sum rules (4 windows): 0; `RUNNING_` total = GFR + UACR: 0 | Full-table invariant query | - |
| Q12 | 3.0 2026-08: 130,445 NPIs; 3.1 c28: 199,122; common 62,035. Spearman: 1M 0.705, 12M 0.801, GFR 12M 0.803, UACR 12M 0.838, `RUNNING_` 0.834. 12M sum on common: 29,460,945 (3.0) vs 39,116,444 (3.1, +33%) | ZS vs c28 | 3.1 pull holds more tests (lab plan F1); 3.0 `RUNNING_` starts 2021, 3.1 2023 |
| Q13 | Output v0 2026-11-17 03:22 (`CREATE OR REPLACE`, 5,165,946 rows, job 1010893614518587), `PULL_DT` 2026-11-17; provider v0 03:25. Stale text: cell 2 (3.0 view, 2018 / Apr-2021 steps), cell 1 (`notebook_output/...` paths), cell 15 ("Lab_03 history"); client summary body (102 columns, 10 HCPs) and "X19: -21 9M" | Delta history; notebook / doc read | F5, F6 |
| Q14 | Pull test types = GFR, UACR (`LAB_STAGED_TESTS`) + POTASSIUM, HBA1C (`LAB_FLAG_RULES`): 0 new, 0 missing. Per cohort Training / Testing / Holdout: NPIs 182,265 / 197,060 / 198,736; active 12M 168,663 / 175,717 / 177,237; tests 12M 53.26M / 57.58M (+8.1%) / 62.37M (+17.1%); K tested 12M 14.04M / 14.57M (+3.8%) / 17.83M (+27.0%). F9: Sep 2026 at 0.96-0.99 of prior-3-month median (passes 95%); below 95% in Jul 2025 and Sep 2025 (K / HbA1c 0.87-0.91) and May 2026 (0.90-0.97) | Per-`DATASET` query; monthly pull counts | Jun-Jul 2026 step: K / HbA1c x1.8-2.1, GFR / UACR x1.25-1.35 (F4) |

## 4. Business rules (readiness vs notebook)

| Rule | Readiness says (section) | Notebook does (cell / decision) | Match |
| --- | --- | --- | --- |
| Entity / time | `NPI_NUMBER`, `SVC_DT` DATE (5.1, 4) | `NPI_NUMBER` x `COHORT_ID`, `SVC_DT` windows (cells 8, 23) | Yes |
| Calendar-month windows | Exact calendar months (5.2) | Month-aligned windows checked in engine (cell 23); QC recount 0 mismatches | Yes |
| Window set | 3, 12, running, trend; 1 / 6 only if SHAP justifies (5.3) | 1 / 3 / 6 / 12 + `RUNNING_` (3.0 set kept, X19) | Documented difference (Track R keeps 3.0 parity) |
| Data start | 2023-01-01 (5.3) | `DATA_START_DATE` 2023-01-01 for all features incl. `RUNNING_` (cell 8) | Yes |
| Lab dedup (S3) | Dedup before counting (5.3, 4) | No dedup in NB02; 8,641 duplicate rows from 2 `PROVIDER_ID`s per NPI counted twice | No (F2) |
| Shares | Null when denominator 0 (5.3, Track C) | 0.0 when denominator 0 (cells 19, 25, 3.0 rule) | Documented difference (Track R keeps 3.0) |
| V10 lab monitoring | UACR / eGFR testing, K tested and high, HbA1c (6) | Test counts + K > 5.0 / HbA1c >= 9 patient-month flags (X18) | Yes; K / HbA1c LabCorp only (L-A) |
| V6 eligible panel | Blocked until PJ06 re-run with C1 (6, 6.3) | 24 eligible columns read the current `sglt2_filter_m` (77% eligible, pre-C1) | No (F1) |
| V7 CKD stage | Lab first, 3a / 3b from eGFR value, stage 1-2 only with damage evidence (6.2) | Tests counted by eGFR stage 1-5 and UACR A1-A3 on the test; no 3a / 3b, no damage rule | Documented (V7 not built, section 7) |
| F9 / lag | Data end per source at 95% of median (5.4) | Not applied; last cohort uses Aug 2026, which passes | Documented |
| F10 trends | 3 vs previous 3 months (6) | No trend columns | N/A |
| V1-V3, V8, V9 | Rx, Dx, bridge views | Not in NB02 | N/A |

## 5. Data sources (readiness vs notebook)

| Source | Readiness says | Notebook uses | Rows / dates found | Match |
| --- | --- | --- | --- | --- |
| Lab pull | `full_2026_11_16_pull_lab_step4`, 307,461,581, 2023-01-01..2026-09-30, 0 null NPI, ready after dedup check | `HCP_LAB_TABLE` (3.1 pull, cell 8) | 307,461,581; same dates; 0 null NPI; 8,641 duplicates | Yes (dedup open, F2) |
| Eligibility | `pj_pat_sglt2_filter_m` 4,123,720,085, 77% eligible, earlier code version | `get_patient_table_path("sglt2_filter_m")` (cell 25) | 4,123,720,085; 77.0% | Yes, but stale (F1) |
| Cohorts | `input_claims_cohorts`, 28 | Claims cohort file via config | 28, 0 mismatches | Yes |
| Universe | `input_hcp_universe` (O2 mapping open) | Via the full-run pull (3.1 universe) | 294,727 IDs; 21 output IDs outside | Mostly (F7) |
| 3.0 volume | No write | Writes only to the 3.1 run (`assert_31_write_path`) | Output in `kerendia_nba_3_1` | Yes |

## 6. Features made (plan vs output)

| Plan family | Expected (readiness / plan) | Output columns | Status |
| --- | --- | --- | --- |
| Tests by type | GFR, UACR x 4 windows | 8 | Made |
| Tests by stage | eGFR 1-5 + A1-A3 x 4 windows | 32 | Made |
| Total | 4 windows | 4 | Made |
| `RUNNING_` | total + 2 types + 8 stages | 11 | Made |
| `PCT_` | 10 per window | 40 | Made |
| K / HbA1c flags (X18, V10) | 2 tests x 2 groups x 3 x 4 windows | 48 | Made (eligible half on stale input, F1) |
| 9-month window (X19) | Removed | 0 | As planned |
| V7 3a / 3b, F10 trend, F9 completeness | Section 7 work | 0 | Not in scope |

## 7. Fill rate

All 143 features over 5,165,946 rows: 0% null, no constant column, none > 99.5% zero, no negative value, all `PCT_` in [0, 1]. Selected features:

| Feature | % null | % zero | % non-zero | % sentinel | min / max | % non-zero train / test / holdout / c28 | Flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TOTAL_LAB_CLAIMS_IN_LAST_1_MONTH` | 0 | 32.00 | 68.00 | - | 0 / 21,198 | 68.1 / 67.0 / 67.9 / 67.6 | |
| `TOTAL_LAB_CLAIMS_IN_LAST_3_MONTH` | 0 | 21.38 | 78.62 | - | 0 / 46,034 | 78.9 / 76.7 / 77.8 / 78.0 | |
| `TOTAL_LAB_CLAIMS_IN_LAST_12_MONTH` | 0 | 7.98 | 92.02 | - | 0 / 101,598 | 92.5 / 89.2 / 89.2 / 89.2 | |
| `RUNNING_TOTAL_LAB_CLAIMS` | 0 | 0.00 | 100.00 | - | 1 / 184,642 | 100 / 100 / 100 / 100 | by construction |
| `TOTAL_LAB_CLAIMS_GFR_IN_LAST_12_MONTH` | 0 | 8.62 | 91.38 | - | 0 / 101,018 | 91.9 / 88.6 / 88.7 / 88.7 | |
| `TOTAL_LAB_CLAIMS_UACR_IN_LAST_12_MONTH` | 0 | 36.38 | 63.62 | - | 0 / 28,735 | 63.7 / 63.0 / 63.3 / 63.4 | |
| `..._STAGE_3_MODERATE_IN_LAST_12_MONTH` | 0 | 29.56 | 70.44 | - | 0 / 7,572 | 70.6 / 69.1 / 69.5 / 69.6 | |
| `..._STAGE_4_SEVERE_IN_LAST_12_MONTH` | 0 | 57.42 | 42.58 | - | 0 / 1,046 | 42.5 / 42.3 / 43.8 / 44.0 | |
| `..._STAGE_5_IN_LAST_1_MONTH` | 0 | 94.94 | 5.06 | - | 0 / 53 | 4.8 / 5.7 / 6.8 / 6.7 | |
| `TOTAL_LAB_CLAIMS_A2_IN_LAST_12_MONTH` | 0 | 49.94 | 50.06 | - | 0 / 6,107 | 50.0 / 50.1 / 50.6 / 50.6 | |
| `TOTAL_LAB_CLAIMS_A3_IN_LAST_1_MONTH` | 0 | 87.72 | 12.28 | - | 0 / 239 | 11.9 / 13.9 / 15.0 / 14.6 | |
| `RUNNING_TOTAL_LAB_CLAIMS_A3` | 0 | 53.63 | 46.37 | - | - / 2,828 | 45.5 / 50.6 / 51.6 / 51.8 | train-hold > 5 (cumulative) |
| `RUNNING_..._STAGE_4_SEVERE` | 0 | 46.27 | 53.73 | - | - / 3,333 | 52.9 / 57.9 / 59.2 / 59.5 | train-hold > 5 (cumulative) |
| `RUNNING_..._STAGE_5` | 0 | 65.51 | 34.49 | - | - / 1,128 | 33.6 / 38.6 / 40.0 / 40.3 | train-hold > 5 (cumulative) |
| `TOTAL_PATIENTS_POTASSIUM_TESTED_IN_LAST_12_MONTH` | 0 | 32.33 | 67.67 | - | 0 / 15,530 | 67.8 / 65.9 / 67.5 / 67.9 | |
| `TOTAL_PATIENTS_POTASSIUM_GT_5_IN_LAST_1_MONTH` (and its `PCT_`) | 0 | 80.53 | 19.47 | - | 0 / 112 | 18.8 / 21.6 / 24.9 / 24.6 | train-hold > 5 (F4) |
| `TOTAL_ELIGIBLE_PATIENTS_POTASSIUM_GT_5_IN_LAST_1_MONTH` (and its `PCT_`) | 0 | 82.81 | 17.19 | - | 0 / 92 | 16.5 / 19.5 / 22.7 / 22.4 | train-hold > 5 (F4) |
| `TOTAL_ELIGIBLE_PATIENTS_POTASSIUM_GT_5_IN_LAST_12_MONTH` | 0 | 60.85 | 39.15 | - | 0 / 908 | 39.2 / 38.2 / 39.7 / 40.0 | |
| `TOTAL_PATIENTS_HBA1C_GE_9_IN_LAST_1_MONTH` | 0 | 88.83 | 11.17 | - | 0 / 91 | 10.7 / 12.1 / 15.2 / 14.9 | |
| `PCT_ELIGIBLE_PATIENTS_HBA1C_GE_9_IN_LAST_12_MONTH` | 0 | 73.97 | 26.03 | - | 0 / 1 | 26.2 / 24.4 / 26.0 / 26.3 | |

The 7 flagged columns are the only ones with a train-vs-holdout change > 5 points.

## 8. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature | In 752? (SHAP rank, % SHAP) | NBA 3.1 feature | Status | Reason |
| --- | --- | --- | --- | --- |
| 95 columns with window suffix or `RUNNING_` (types, stages, total, `PCT_`) | No (0 NB02 columns in 752) | Same 95 names | Preserved | Same logic (offset-0 parity, lab plan section 0); input now the 3.1 pull |
| 21 base-month columns without suffix (e.g. `TOTAL_LAB_CLAIMS`, `TOTAL_LAB_CLAIMS_GFR`, `PCT_TOTAL_LAB_CLAIMS_GFR`) | No | `..._IN_LAST_1_MONTH` | Replaced (duplicate) | Equal to the 1-month window column at offset 0 |
| - | - | 48 K / HbA1c flag columns | New | X18, readiness V10 |
| Accelerator lab features (rank 67, 142, 331, 598, 602, 674, 701; 0.67% SHAP together) | Yes | Not NB02 | N/A | Built by the accelerator, outside this notebook |

## 9. HCP trace (step-by-step recompute)

All 143 features for 6 NPIs x 28 cohorts recomputed in pandas from `pull_lab_step4` and `sglt2_filter_m` (steps 1-7 below), compared with the output (step 8): 168 rows, 24,024 cells, 0 mismatches.

| Step | What |
| --- | --- |
| 1 | NPIs: 1598705535 (high volume), 1962737981 (stage 5), 1376571174 (K > 5), 1821106592 (no tests in 12M), 1003047473 (training c5, HbA1c >= 9), 1205840931 (window edge) |
| 2 | Raw pull rows for those NPIs (all dates, all 4 tests) |
| 3 | `SVC_DT` >= 2023-01-01; GFR / UACR -> stage text; K / HbA1c -> flag per row (K > 5.0, HbA1c >= 9.0) |
| 4 | `SVC_DT` <= `CUTOFF_DATE` |
| 5 | Load date: not available (no `INSERT_TS`) |
| 6 | Windows [1st of (cutoff month - N + 1), cutoff]; flags per (NPI, patient, month, test) = max flag; eligible if (patient, month) has `ELIGIBLE_PATIENT_FLAG` = 1 |
| 7 | Counts, `PCT_` (0.0 when denominator 0), `RUNNING_` |
| 8 | Examples (recompute = output): 1598705535 c28 `RUNNING_TOTAL` 184,642, 12M 51,349; 1962737981 c20 stage 5 12M 122; 1376571174 c26 3M K tested 59, K > 5 28, eligible K > 5 24; 1821106592 c28 12M 0, `RUNNING_` 7,252; 1003047473 c5 12M 48, HbA1c >= 9 1; 1205840931 c28 1M 78 (2026-08-31 in, 2026-09-01 out) |

## 10. Findings and actions

| # | Finding | Severity | Action / owner | Status |
| --- | --- | --- | --- | --- |
| F1 | The 24 `ELIGIBLE_PATIENTS` columns use `pj_pat_sglt2_filter_m` written by the pre-C1 code: 77.0% of patient-months eligible (current code 18.5% on a 5% sample, readiness 6.3). Output eligible share of tested patient-months is 68.6% (K) / 66.1% (HbA1c). Values follow the table correctly (trace 0 mismatches) but the eligibility is wrong | blocker (for the 24 columns) | Re-run PJ06 with C1 / C11, then NB02; until then do not use the eligible columns in selection. Owner: NBA team | Open |
| F2 | 8,641 duplicate pull rows on NPI x patient x day x test, each from 2 `PROVIDER_ID`s per NPI; 7,871 GFR / UACR duplicates counted twice (0.004% of 207.5M); K / HbA1c duplicates collapse at patient-month level | fix | Dedup the pull on NPI x patient x day x test (readiness S3) in PJ01 Step 4 or NB02 load. Owner: lab journey | Open |
| F3 | 672 NPIs with only K / HbA1c tests (2,201 rows) get no output row: flag features are added only to rows that have GFR / UACR tests (cell 25 left join) | doc | Confirm intended; else build the NPI spine from all 4 tests | Open |
| F4 | K / HbA1c volume steps up in Jun-Jul 2026 (x1.8-2.1 month on month); holdout K tested 12M per cohort +27.0% vs training; K > 5 1M non-zero 18.8% -> 24.9%. Likely LabCorp coverage growth (readiness L-C / L-D) | note (drift) | NBA team to review and sign off; consider source split | Open |
| F5 | Stale text: NB02 cell 2 lists the 3.0 view and 2018 / Apr-2021 steps; cell 1 lists `notebook_output/` paths (output is UC); cell 15 says "Lab_03 history"; client summary body still says 102 columns / 10 HCPs | doc | Update header cells and summary | Open |
| F6 | Client summary / plan say X19 removed 21 `IN_LAST_9_MONTH` features; the 3.0 reference `claim_lab_monthly_ZS` has no 9M columns. Its 21 extra columns are base-month duplicates of the 1-month window | doc | Correct the X19 wording or point to the 3.0 table that had 9M | Open |
| F7 | 21 `PROVIDER_ID` in the provider output are not in `input_hcp_universe` (NPI mapping fan-out, open point O2) | note | Filter to the universe at model assembly or fix the mapping | Open |
| F8 | Point-in-time on load date not testable (no `INSERT_TS` in the pull); only service-date windows proven | note | Readiness 5.4 lag rule | Open |
| F9 | V7 rules (3a / 3b, damage evidence) and F10 trends not in NB02 | note | Section 7 work, out of scope | N/A |

## 11. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 11 / 14 (Q6 FAIL on F1; Q13, Q14 OPEN) |
| QC by / date | Genie Code for Saurabh Modi, 2026-11-27 |
| O5 and drift review (NBA team) / date | |
| Reviewed by / date | |
| Next | F1 (PJ06 re-run + NB02 re-run), F2 dedup; then re-check Q6 and Q14 |
