# QC 06: Eligible HCP claims features (HCP monthly, NB06), NBA 3.1

**QC status:** DONE, 2026-11-27 (plan: `06_eligible_hcp_claims_features_qc_plan.md`)  
**Verdict:** PASS with actions. The notebook computes what it says: all 217 features were recomputed independently from the Rx pull + patient tables with 0 differences (331.5M stage / window / `RUNNING_` / dialysis cells and 76 DM / HF count columns over every NPI x cohort; `PCT_` checked by formula). Grain, cohorts, windows, invariants and fill rate are clean. Open: the eligibility input `pj_pat_sglt2_filter_m` is the stale version flagged by readiness section 4 (77% eligible patient-months), so every eligible-based feature must be rebuilt after the PJ06 re-run (F1); rejected-only Rx claims are counted (F2); provider mapping gaps (F3); run not flagged as run of record (F4); stale doc text (F5); NBA-team drift sign-off.  
**QC run:** 2026-11-27, serverless (Genie Code scratch session), on the output written 2026-11-17 06:18 (`PULL_DT` 2026-11-17, job 1010893614518587, run `full_2026_11_16`). Notebook re-run during QC: **no**. Evidence = read-only queries only; no notebook or table changed.

Rule source = `Feature_Evaluation/05_Feature_Views/NBA_3_1_LAAD_Feature_Views_Readiness_Plan.md` ("readiness"), section 6 (contender views, 6.1 bridge, 6.2 CKD stage) plus sections 4, 5.3 and 5.4. Section 7 (work plan) is out of scope. Developer rules: `NBA_3_1_Eligible_HCP_Features_Plan.md` ("plan"), `NBA_3_1_Eligible_HCP_Features_Client_Summary.md` ("summary"). `<S>` = `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_nba_3_1`.

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `hcp_level_features/06 Eligible HCP Claims Files/06_claim_eligible_hcp` (35 cells) |
| Upstream notebooks | `Patient_Journey_Validation/Px Files/05_patient_journey_px` (`pj_px`, first dialysis date); `Combine Files/06_patient_journey_combine_3_1` (`pj_pat_sglt2_filter_m` eligibility + stage, `pj_dm_hf_flags` DM / HF type) |
| Rule file | Readiness sections 4, 5.3, 5.4, 6, 6.1, 6.2 |
| Source table (Rx) | `<S>.full_2026_11_16_pull_rx_hcp`: 3,275,477,893 rows, `SVC_DT` 2023-01-01 .. 2026-09-30, 0 null NPI, 307,579,439 rows with `REJECTION_FLAG = 1`. NB06 uses only NPI, patient, day |
| Patient tables | `<S>.full_2026_11_16_pj_pat_sglt2_filter_m` 4,123,720,085 patient-months (150,897,177 patients); `<S>.full_2026_11_16_pj_px` 1,543,698 patients; `<S>.full_2026_11_16_pj_dm_hf_flags` 89,168,946 patients |
| Universe | `<S>.input_hcp_universe`: 294,727 `PROVIDER_ID` |
| Cohorts | `<S>.input_claims_cohorts`: 28 cohorts c1 .. c28, offset 0; Training c1-c24, Testing c25-c26, Holdout (Backtesting) c27-c28 |
| Mapping | 3.0 volume `query_output/kerendia_nba_3_0_npi_bhid_mapping` (`HCP_NPI_MAPPING_TABLE`) |
| Output (NPI) | `<S>.full_2026_11_16_hcp_claim_eligible_patient_cohort`: 8,085,306 rows x 226 columns (217 features + `NPI_NUMBER`, `COHORT_ID` + 7 metadata), 294,535 NPIs |
| Output (provider) | `<S>.full_2026_11_16_hcp_provider_claim_eligible_patient_cohort`: 8,086,528 rows, 3,001 with null `PROVIDER_ID` |
| Expected grain | One row per `NPI_NUMBER` x `COHORT_ID` **for NPIs with at least one eligible Rx patient-month from 2023-01 to the cohort month** (sparse, not universe x 28) |
| NBA 3.0 counterpart | `06_claim_eligible_hcp` -> `ops_pipeline_bkp/notebook_output/kerendia_nba_3_0_claim_eligible_patient` (13,601,116 rows, months 2022-01 .. 2026-10, 84 features) |
| NBA 3.0 final model | 752 features: `/Users/sehar.aejaz.ext@bayer.com/Extra Notebooks/Final NBA 3.0 Modeling Features.xlsx` |

## 2. QC checklist

| # | Check | How | Pass when | Status |
| --- | --- | --- | --- | --- |
| Q1 | HCP universe | Keys, duplicates, rows per cohort vs NPIs with eligible Rx history, provider IDs vs universe, null IDs | 0 duplicates; rows per cohort explained; 0 outside universe | PASS (NPI table); provider copy has open mapping items (F3) |
| Q2 | Right cohorts | Output `COHORT_ID`, `COHORT_MONTH`, `OFFSET_DAYS`, `CUTOFF_DATE`, `SVC_DT_M`, `DATASET` vs `input_claims_cohorts` | 0 mismatches | PASS |
| Q3 | Windows and point-in-time | E = `CUTOFF_DATE`; N-month window = N calendar months ending with the cohort month (sum, D1); `RUNNING_` = 2023-01 .. cohort month | No claim after E counted | PASS (load-date check N/A: no `INSERT_TS`) |
| Q4 | Data sources vs readiness | Section 4 rows: rows, dates, types, eligible share; Delta history | Same sources, unchanged since the run | PASS (sources = readiness); content of `sglt2_filter_m` stale (F1) |
| Q5 | All features made | 217 expected names (plan + X20) vs output | 0 missing, 0 unexpected | PASS |
| Q6 | Business rules | Readiness section 6 views (V1/V2, V6-V9, 6.1, F9, F10) and plan rules vs notebook | Match or documented and agreed | OPEN (F1, F2 need decisions; others documented, section 4) |
| Q7 | Fill rate | All 217 features, all / train / test / holdout / c28 | No unexpected nulls; flags explained | PASS |
| Q8 | NBA 3.0 752 coverage | NB06 features in the 752 | 0 skipped | PASS |
| Q9 | Preserved vs new | 84 3.0 features vs 217 3.1 | All labelled | PASS |
| Q10 | HCP trace | Full independent recompute of every count column (all NPI x cohort) + 4 step-by-step cases | Output = recompute | PASS |
| Q11 | Invariants | 55 checks: nesting, stage / DM / HF sums, eligible <= Rx patients, `PCT_` formula, flags, `RUNNING_` monotonic | 0 violations | PASS |
| Q12 | NBA 3.0 output comparison | 3.0 month 2026-08 vs 3.1 c28 on common providers | Differences explained | PASS |
| Q13 | Reproducibility and docs | Delta history, run registry, doc headers | No stale text that changes meaning | OPEN (F4, F5) |
| Q14 | Data completeness and drift (owner: NBA team) | DM / HF values vs notebook lists; monthly Rx patient-months (F9 95% rule); active HCPs / 12M counts per `DATASET` | Values = lists; drift <= 20% or explained | Data PASS; NBA-team sign-off OPEN |

## 3. Evidence log

| # | Result (numbers) | Where (query) | Notes |
| --- | --- | --- | --- |
| Q1 | NPI table: 8,085,306 rows = 8,085,306 distinct (`NPI_NUMBER`, `COHORT_ID`); 0 null / blank / '0' NPI; 294,535 NPIs. Rows per cohort rise from 278,033 (c1) to 294,535 (c28). Expected rows per cohort (NPIs whose first eligible Rx patient-month from 2023-01 is <= the cohort month) = output for **all 28 cohorts, 0 difference**. Pull NPIs since 2023: 294,612; 36 never have an eligible patient-month; NPIs with any Rx (not only eligible) would give 40 (c28) to 187 (c1) more rows per cohort, so the grain is "eligible history", not "Rx history". Provider table: 8,086,528 rows, 3,001 null `PROVIDER_ID`, 8,083,527 non-null rows all distinct on (`PROVIDER_ID`, `COHORT_ID`); 42 output `PROVIDER_ID`s not in the universe; 310 universe `PROVIDER_ID`s have no row | `count` / `count distinct`; per-cohort recount from `pull_rx_hcp` x `sglt2_filter_m` joined to `input_claims_cohorts`; `left_anti` vs `input_hcp_universe` | Sparse grain is by design (rows come from eligible feature rows). Downstream must zero-fill missing HCP x cohort rows. Causes of the 3,001 null IDs and the +1,222 provider rows were **not re-measured** in this QC; the summary (2026-11-04 run) attributes them to NPIs missing from / double-mapped in the 3.0 mapping (F3) |
| Q2 | 28 distinct cohort rows in the output, 28 in the file, full join: **0 mismatches** on `DATASET`, `OFFSET_DAYS` (0), `CUTOFF_DATE` = `last_day(lookback_end_date)`, `SVC_DT_M` = `lookback_end_date`, `COHORT_MONTH`; `PULL_DT` 2026-11-17 on all; 7 `COHORT_SET` groups (C1-C5_training .. C27-C28_backtesting) | `select distinct` metadata full join `input_claims_cohorts` | No promotional dates |
| Q3 | Independent recompute from the raw tables (distinct NPI x patient x calendar month of `pull_rx_hcp` from 2023-01-01, inner join `sglt2_filter_m` flag = 1 on patient + month; window = `months_between(lookback_end, month)` 0 .. N-1; running = month <= lookback end; dialysis = any Rx patient of the cohort month with first dialysis < 2017-01-01 or <= claim day): 8,085,306 rows, 0 rows on one side only, **0 mismatches in 331,497,546 cells** (40 total / stage window / `RUNNING_` columns + `DIALYSIS_FLAG`) | Spark job on `pull_rx_hcp`, `pj_pat_sglt2_filter_m`, `pj_px` and the output | Month buckets: a claim on E (last day of the lookback month) is in, E+1 is in the next month and out. No load timestamp in the pull, so late loads cannot be tested (readiness 5.4) |
| Q4 | Rx pull 3,275,477,893 rows (= readiness section 4), 2023-01-01 .. 2026-09-30, 0 null NPI. `sglt2_filter_m` 4,123,720,085 rows (= readiness), 150,897,177 patients, months 2023-01 .. 2026-09, **mean `ELIGIBLE_PATIENT_FLAG` 0.7697** (readiness: 77%, written by an earlier code version; current PJ06 code gives 18.5% on a 5% sample). Eligible rows: `GFR_DX_STAGE` only STAGE_2 / 3 / 4 / UNKNOWN, `UACR_STAGE` only STAGE_2 / 3 / UNKNOWN (0 null stage among eligible rows). `pj_px` 1,543,698 patients, `FIRST_DIALYSIS_DATE` STRING, every value casts to a date (0 null), 2021-01-02 .. 2026-09-30. `pj_dm_hf_flags` 89,168,946 patients, one row each. Delta history: all inputs v0 CTAS 2026-11-17 01:59 .. 03:01 by job 1010893614518587; in the first 4 non-OPTIMIZE / VACUUM versions inspected per table, later versions are only CLUSTER BY / SET TBLPROPERTIES; outputs v0 at 06:18 / 06:19. Inputs look unchanged since the output was written (later versions beyond those inspected not checked) | `count`, `min / max`, `avg`, `describe history` | Outputs only in `kerendia_nba_3_1`; nothing written to the 3.0 volume (notebook asserts) |
| Q5 | 217 features: 32 stage window counts (8 x 4 windows), 8 `RUNNING_`, 28 stage `PCT_`, 148 DM / HF (4 windows x (1 Rx total + 9 Rx groups + 9 eligible groups + 18 `PCT_`)), 1 `DIALYSIS_FLAG`; generated name list vs output: **0 missing, 0 unexpected**. Types: 116 BIGINT, 100 DOUBLE, 1 INT. 226 columns in total = summary. No trend / DIFF / RATIO columns | `dtypes` vs generated list | The planning note "about 277 columns" was a mis-count; the real count is 226 |
| Q6 | See section 4 | NB06 cells 7, 15, 21, 25, 27, 29, 31 | F1 and F2 need decisions |
| Q7 | 0 null cells in all 217 features; 0 negative values; no constant column; no column > 99.5% zero (max 90.93%: `TOTAL_ELIGIBLE_PATIENTS_DM_TYPE_OTHER_IN_LAST_1_MONTH`); every `PCT_` max <= 1. Holdout-vs-training change > 5 points on 19 columns: UACR stage 2 / 3 window counts and their `PCT_` (16, +6.2 to +8.7), `RUNNING_` GFR stage 4 (+6.5), `RUNNING_` UACR stage 2 (+11.8), `RUNNING_` UACR stage 3 (+12.8) | Single-pass Spark aggregate on the output | `RUNNING_` grows with history from 2023-01 (c1 17 months, c28 44); UACR stage coverage rises over time. Expected, noted for modelling (F6) |
| Q8 | 752 xlsx (752 rows) has 1 NB06 feature: `RUNNING_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_4` (rank 491 by `Mean_Abs_SHAP`, 0.041% of total SHAP). Present in 3.1 under the same name | `pd.read_excel` (openpyxl installed in the scratch session only) | Same as plan F6 (selected-277) |
| Q9 | 3.0 output 84 features vs 3.1 217: 69 same name (preserved; window columns now sum of N months, not 3.0 mean of N+1, F7 / D1), 15 not carried (8 base-month counts without suffix, e.g. `TOTAL_ELIGIBLE_PATIENTS`, and 7 base-month `PCT_`), 148 new (DM / HF, X20) | Set comparison of column names | Base-month columns = `_IN_LAST_1_MONTH` in the cohort design |
| Q10 | (a) Full recompute of the 76 DM / HF count columns (DM type from `pj_dm_hf_flags`, null -> NONE; HF month = month >= month of `HF_FIRST_DATE`; HF type null -> UNKNOWN; eligible = flag 1) over all 8,085,306 rows: **0 mismatches**. (b) The 40 stage columns + `DIALYSIS_FLAG` are covered by the Q3 full recompute. (c) 72 DM / HF `PCT_` and 28 stage `PCT_` are checked by the Q11 formula. (d) 4 step-by-step cases in section 9: all = output | Spark job on the raw tables | |
| Q11 | **0 violations** in 55 checks on 8,085,306 rows: 1M <= 3M <= 6M <= 12M <= `RUNNING_` (8 stage columns); 1M <= 3M <= 6M <= 12M for the 9 Rx DM / HF groups; GFR stage sum = total and UACR stage sum = total (4 windows); Rx DM sum = `TOTAL_RX_PATIENTS`, eligible DM sum = `TOTAL_ELIGIBLE_PATIENTS`, HF type sum = HF (Rx and eligible, 4 windows); eligible <= Rx patients (total and every group); `PCT_` = count / denominator, 0.0 when the denominator is 0 (100 columns, tol 1e-9); `DIALYSIS_FLAG` in {0, 1}; `RUNNING_TOTAL_ELIGIBLE_PATIENTS` >= 1. `RUNNING_` never drops from one cohort to the next for an NPI (8 columns, 0 cases). `DIALYSIS_FLAG` = 1 on 41.7% of rows | Spark aggregate + window `lag` | |
| Q12 | 3.0 month 2026-08 (234,502 providers) vs 3.1 c28 (294,459 non-null): 220,895 common. Base-month total (3.0 `TOTAL_ELIGIBLE_PATIENTS` vs 3.1 `..._IN_LAST_1_MONTH`): HCPs > 0 216,619 -> 216,452, sum 35.68M -> 34.28M (-3.9%), Pearson 0.969. `RUNNING_TOTAL_ELIGIBLE_PATIENTS`: 2,269.5M -> 1,476.0M, Pearson 0.968. Selected feature `RUNNING_..._GFR_DX_STAGE_4`: HCPs > 0 215,176 -> 211,160, sum 33.6M -> 17.0M, Pearson 0.96. Base-month stage 3: HCPs > 0 95,967 -> 207,755, sum 0.34M -> 4.47M, Pearson 0.609 | Join on `PROVIDER_ID` | `RUNNING_` lower: 3.0 counts from 2022-01, 3.1 from `DATA_START_DATE` 2023-01-01. Stage 3 jump: code-based CKD stage of the 3.1 patient journey (plan F1: 23 -> 980 on the test HCPs). Window columns not compared (3.0 means vs 3.1 sums, F7). Pearson used; Spearman not computed |
| Q13 | Outputs v0 CTAS 2026-11-17 06:18 (NPI) and 06:19 (provider); 8,085,306 / 8,086,528 rows = Delta `numOutputRows`; job 1010893614518587. `run_registry`: `full_2026_11_16` STATUS SUCCESS, job run 814119312914044, note "NB07: all 11 HCP tables OK", **`IS_RUN_OF_RECORD` = False**. Stale text: F5 | `describe history`, `run_registry` | |
| Q14 | `DM_TYPE` values in `pj_dm_hf_flags`: T2D, T1D, OTHER, null; `HF_TYPE`: HFPEF_PROXY, HFREF_PROXY, MIXED, UNKNOWN, null = notebook lists (null mapped to NONE / UNKNOWN). Monthly distinct Rx NPI x patient: Aug 2026 43,960,996 = 100.3% of the median of May-Jul (43,839,568); Sep 2026 (lag month) 43,379,234 = 98.7% of the median of Jun-Aug (43,960,996): both meet the 95% rule (readiness 5.4). Drift per `DATASET` (mean per cohort): active HCPs (12M eligible > 0) Training 286,539, Testing 292,451 (+2.1%), Holdout 292,439 (+2.1%); 12M eligible patient-months 454.9M, 461.9M (+1.5%), 459.9M (+1.1%); 12M Rx patient-months 510.5M, 529.8M (+3.8%), 529.0M (+3.6%) | `group by` on pull, dm_hf_flags and output | All below 20%. F9 is checked on the Rx pull only (eligibility and DM / HF are patient tables of the same run). Needs NBA-team sign-off |

## 4. Business rules (readiness vs notebook)

| Rule | Readiness / plan says (section) | Notebook does (cell / decision) | Match |
| --- | --- | --- | --- |
| V6 Eligible panel | Section 6: **Blocked**; section 4: `sglt2_filter_m` built before the C1 SGLT2 fix, only `ELIGIBLE_PATIENT_FLAG` (77% of patient-months), no per-indication flags; re-run PJ06 with C1 | Cell 7 reads `get_patient_table_path("sglt2_filter_m")` = `full_2026_11_16_pj_pat_sglt2_filter_m`; cell 15 keeps flag = 1. QC: mean flag 0.7697 in this table | **No (F1).** Logic is right (Q3 0 mismatches) but the input is the stale table; all `TOTAL_ELIGIBLE_*`, `RUNNING_*`, stage `PCT_*` and `*_ELIGIBLE_PATIENTS_*` DM / HF columns change after the PJ06 re-run. Per-indication counts (CKD+T2D / CKD+T1D / HF) are section 7 work |
| V7 CKD stage mix | 6.2: current stage = lab eGFR first, 3a / 3b from the eGFR value, stage 1-2 only with damage evidence, Dx coded stage as fallback | NB06 counts the patient-month label `GFR_DX_STAGE` of `sglt2_filter_m` (PJ06: Dx first, then lab; stage 3 not split), and `UACR_STAGE` | Documented difference: the 6.2 rule is for the new V7 view (section 7, out of scope); NB06 keeps the 3.0 definition (F7) |
| V8 HF | Section 6: HFpEF-proxy patients from `pj_dm_hf_flags` + bridge; proxy adequacy open | Cell 27: HF month = month >= month of `HF_FIRST_DATE` (same as PJ06 `HF_FLAG`); `HF_TYPE` HFPEF_PROXY / HFREF_PROXY / MIXED / UNKNOWN (null -> UNKNOWN) | Yes (Q10 0 mismatches); proxy adequacy stays open (readiness) |
| V9 T1D + CKD | Section 6: E10 + N18 patients, little history since Sep 2026 | `TOTAL_*_DM_TYPE_T1D_*` from `pj_dm_hf_flags` `DM_TYPE` (patient level, not monthly) | Yes for the existing columns; 12M eligible T1D non-zero on 73.9% of rows. A T1D+CKD view itself is section 7 work |
| V1 / V2 claim type | 5.3 / R1: paid, reversed and rejected as separate features; target-aligned features paid only | Cell 7 reads NPI, patient, day only; no `REJECTION_FLAG` filter. 56,861,932 of 1,687,754,809 eligible patient-months since 2023 (3.37%) come from patients whose only claims with the HCP that month are rejected | **Open (F2):** not a target-aligned feature, so the R1 rule does not force paid-only, but "patients seen" includes rejected-only fills; needs a decision |
| 6.1 HCP-patient bridge | One row per NPI x patient x month from Rx, Dx or Lab claims | NB06 builds the same grain from **Rx only** (cell 15 `eligible_patient_months`, cell 27) | Note: reusable for the bridge, but Dx / Lab-only patients are missing (F8) |
| F9 completeness | 5.4: last month >= 95% of the median of the 3 months before | No flag in NB06 (Track C). Aug 2026 = 100.3%, Sep 2026 = 98.7% | Yes for this run; flag not built (out of scope) |
| F10 trends | 3 months vs previous 3 | No trend columns (Q5) | N/A, not in NB06 |
| V3, V4, V5, V10 | SGLT2 add-on pool, calls, practice, lab monitoring | Not in NB06 | N/A |
| Windows (D1) | Plan D1 (2026-11-03): window = **sum** of N monthly counts, not the 3.0 mean of N+1 | Cells 21, 25 (shared engine), 27 | Yes (Q3) |
| `DATA_START_DATE` | Team rule: counted claims from 2023-01-01, `RUNNING_` included | Cell 21: `_rx_counted = SVC_DT >= DATA_START_DATE` | Yes (Q3) |
| Dialysis (D2) | Plan D2: any Rx patient of the HCP (not only eligible), first dialysis on / before the claim day or before 2017, cohort month only (not windowed) | Cell 15 `build_dialysis_claims`, cell 25 join on cohort month | Yes (Q3: 0 mismatches) |
| Fixed stage columns | Walkthrough 8: fixed list (3.0 columns + any other value) | Cell 21 `BASE_STAGE_FEATURES`; data has no other stage value | Yes |
| `PCT_` | Plan: count / window total, 0.0 when total is 0 (readiness 5.3 says null for new Track C features) | Cells 25, 27: `otherwise(0.0)` | Yes for NB06 (3.0 definition kept); null rule applies to new Track C views only |
| Provider mapping | Summary open point: keep the 3.0 mapping; fix for unmapped / double-mapped NPIs not applied | Cell 31: left join to the 3.0 mapping, NPI dropped | Yes; open item still open (F3) |

## 5. Data sources (readiness vs notebook)

| Source | Readiness says | Notebook uses | Rows / dates found | Match |
| --- | --- | --- | --- | --- |
| Rx pull | `full_2026_11_16_pull_rx_hcp`, 3,275,477,893 rows, 2023-01-01 .. 2026-09-30, no `CLAIM_TYPE` (only `REJECTION_FLAG`) | `HCP_RX_TABLE` (3.1 pull), NPI / patient / day | 3,275,477,893; 2023-01-01 .. 2026-09-30; 0 null NPI; 307,579,439 rejected | Yes (F2 on rejected claims) |
| Eligibility | `full_2026_11_16_pj_pat_sglt2_filter_m`, 4,123,720,085, stale (77%) | `get_patient_table_path("sglt2_filter_m")` | 4,123,720,085; mean flag 0.7697 | Same table; **stale (F1)** |
| Dialysis | `full_2026_11_16_pj_px`, `FIRST_DIALYSIS_DATE` STRING | `get_patient_table_path("px")`, `to_date` in cell 15 | 1,543,698 patients; all dates cast; 2021-01-02 .. 2026-09-30 | Yes |
| DM / HF | `full_2026_11_16_pj_dm_hf_flags`, one row per patient | `get_patient_table_path("dm_hf_flags")` | 89,168,946 patients; values = lists | Yes |
| Cohorts | `input_claims_cohorts`, 28 | `get_hcp_cohort_months()` | 28; 0 mismatches (Q2) | Yes |
| Universe | `input_hcp_universe` (O2: confirm mapping) | Not applied in NB06 (Rx pull already limited upstream) | 294,727; 42 output IDs outside, 310 universe IDs without a row | Open (F3) |
| NPI mapping | O2 | 3.0 `kerendia_nba_3_0_npi_bhid_mapping` | 3,001 null-ID provider rows | Open (F3) |

## 6. Features made (plan vs output)

| Plan family | Expected (plan / summary) | Output columns | Status |
| --- | --- | --- | --- |
| Eligible patient-months per window | Total + 4 GFR / Dx stages + 3 UACR stages = 8 x 4 windows = 32 | 32 | PASS |
| `RUNNING_` | 8 | 8 | PASS |
| Stage `PCT_` | 7 x 4 = 28 | 28 | PASS |
| DM / HF type (X20) | 148 (summary: 128 DM / HF type + 20 HF eligibility) | 148 | PASS |
| `DIALYSIS_FLAG` | 1 | 1 | PASS |
| **Total** | **217** (3.0 84 -> 3.1 217, 226 columns) | **217**, 0 missing, 0 unexpected | PASS |
| Readiness section 6 contenders (V6 per indication, V7 6.2 stage, V9 view, F9, F10) | Track C views | None in NB06 (section 7 work) | N/A by scope |

## 7. Fill rate

% over all 8,085,306 output rows (only HCP x cohorts with eligible history, see Q1). No sentinel values. 0% null on all 217 features. A `PCT_` column is non-zero exactly when its count is (Q11 formula check), so selected count columns are shown; family ranges below.

| Family | Columns | % zero (min .. max) | % null |
| --- | --- | --- | --- |
| Stage window counts | 32 | 0.48 .. 66.86 | 0 |
| `RUNNING_` | 8 | 0.00 .. 43.28 | 0 |
| Stage `PCT_` | 28 | 0.49 .. 66.86 | 0 |
| DM / HF counts | 76 | 0.42 .. 90.93 | 0 |
| DM / HF `PCT_` | 72 | 1.03 .. 90.93 | 0 |
| `DIALYSIS_FLAG` | 1 | 58.32 | 0 |

| Feature | % null | % zero | % non-zero | min / max | % non-zero train / test / holdout / c28 | Flag |
| --- | --- | --- | --- | --- | --- | --- |
| `TOTAL_ELIGIBLE_PATIENTS_IN_LAST_1_MONTH` | 0 | 3.04 | 96.96 | 0 / 4,599 | 97.04 / 96.67 / 96.39 / 96.32 | F1 |
| `TOTAL_ELIGIBLE_PATIENTS_IN_LAST_12_MONTH` | 0 | 0.48 | 99.52 | 0 / 51,148 | 99.55 / 99.38 / 99.30 / 99.28 | F1 |
| `TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_3_IN_LAST_12_MONTH` | 0 | 4.96 | 95.04 | 0 / 8,754 | 94.86 / 96.11 / 96.07 / 96.06 | |
| `TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_4_IN_LAST_12_MONTH` | 0 | 19.82 | 80.18 | 0 / 1,931 | 79.74 / 82.64 / 82.82 / 82.83 | |
| `TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_UNKNOWN_IN_LAST_12_MONTH` | 0 | 0.68 | 99.32 | 0 / 34,973 | 99.36 / 99.16 / 99.07 / 99.04 | |
| `TOTAL_ELIGIBLE_PATIENTS_UACR_STAGE_3_IN_LAST_12_MONTH` | 0 | 48.44 | 51.56 | 0 / 736 | 50.42 / 57.65 / 58.81 / 59.08 | drift +8.4 (F6) |
| `RUNNING_TOTAL_ELIGIBLE_PATIENTS` | 0 | 0.00 | 100.00 | 1 / 157,801 | 100 / 100 / 100 / 100 | |
| `RUNNING_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_4` (3.0 SHAP 491) | 0 | 13.82 | 86.18 | 0 / 5,880 | 85.28 / 91.13 / 91.77 / 91.91 | drift +6.5 (F6) |
| `TOTAL_RX_PATIENTS_IN_LAST_12_MONTH` | 0 | 0.42 | 99.58 | 0 / 63,321 | 99.61 / 99.46 / 99.38 / 99.36 | |
| `TOTAL_ELIGIBLE_PATIENTS_DM_TYPE_T2D_IN_LAST_12_MONTH` | 0 | 1.36 | 98.64 | 0 / 40,574 | 98.68 / 98.50 / 98.40 / 98.37 | |
| `TOTAL_ELIGIBLE_PATIENTS_DM_TYPE_T1D_IN_LAST_12_MONTH` | 0 | 26.09 | 73.91 | 0 / 6,178 | 73.88 / 74.21 / 73.95 / 73.89 | V9 |
| `TOTAL_ELIGIBLE_PATIENTS_DM_TYPE_T1D_IN_LAST_1_MONTH` | 0 | 54.91 | 45.09 | 0 / 533 | 45.34 / 43.76 / 43.53 / 43.25 | |
| `TOTAL_ELIGIBLE_PATIENTS_HF_IN_LAST_12_MONTH` | 0 | 3.49 | 96.51 | 0 / 11,076 | 96.43 / 97.03 / 96.95 / 96.92 | V8 |
| `TOTAL_ELIGIBLE_PATIENTS_HF_TYPE_HFPEF_PROXY_IN_LAST_12_MONTH` | 0 | 8.95 | 91.05 | 0 / 6,289 | 90.78 / 92.66 / 92.66 / 92.65 | V8 |
| `TOTAL_ELIGIBLE_PATIENTS_DM_TYPE_OTHER_IN_LAST_1_MONTH` | 0 | 90.93 | 9.07 | - | - | highest % zero |
| `DIALYSIS_FLAG` | 0 | 58.32 | 41.68 | 0 / 1 | 41.61 / 41.89 / 42.29 / 42.11 | |

The high non-zero shares (eligible patient-months on > 96% of HCP x cohorts) reflect the stale 77% eligibility table (F1) and are expected to fall after the PJ06 re-run.

## 8. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature | In 752? (SHAP rank, % SHAP) | NBA 3.1 feature | Status | Reason |
| --- | --- | --- | --- | --- |
| `RUNNING_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_4` | Yes (491, 0.041%) | Same name | Preserved | Selected model feature; history now from 2023-01 |
| Other 7 `RUNNING_*` | No | Same names | Preserved | |
| 32 `*_IN_LAST_{1,3,6,12}_MONTH` stage counts | No | Same names | Preserved (redefined: sum of N months, not mean of N+1, D1 / F7) | |
| 28 `PCT_*_IN_LAST_N_MONTH` | No | Same names | Preserved (redefined via the window counts) | |
| `DIALYSIS_FLAG` | No | Same name | Preserved | D2 |
| 8 base-month counts (`TOTAL_ELIGIBLE_PATIENTS`, `..._GFR_DX_STAGE_*`, `..._UACR_STAGE_*`) | No | `..._IN_LAST_1_MONTH` | Replaced | Cohort design: base month = 1-month window |
| 7 base-month `PCT_` | No | `PCT_..._IN_LAST_1_MONTH` | Replaced | Same |
| - | - | 148 `TOTAL_RX_PATIENTS_*`, `TOTAL_ELIGIBLE_PATIENTS_{DM_TYPE,HF}*`, `PCT_RX_*`, `PCT_ELIGIBLE_*` | New | X20 (DM / HF type, 2026-11-06) |

## 9. HCP trace (step-by-step recompute)

All values recomputed from `pull_rx_hcp`, `sglt2_filter_m`, `pj_dm_hf_flags` and `pj_px`, independently of the notebook code. Window = 12 months ending with the cohort month.

| Step | High volume: NPI 1619082625, c28 | Dialysis, small: NPI 1003129388, c28 | Same HCP, training: 1003129388, c1 | No eligible in window: NPI 1003019647, c28 |
| --- | --- | --- | --- | --- |
| 1 `PROVIDER_ID` (3.0 mapping) | 7840288 | 10982774 | 10982774 | 8152481 |
| 2 Raw rows in pull (all dates) / rejected | 400,315 / 76,371 | 161 / 9 | 161 / 9 | 12 / 0 |
| 3-4 Claims in the 12M window (<= E) | 107,533 | 21 | 34 | 0 |
| 5 Load date | N/A (no `INSERT_TS`) | N/A | N/A | N/A |
| 6 Distinct patient-months / eligible | 39,150 / 32,066 | 19 / 16 | 24 / 24 | 0 / 0 |
| 7 T2D patient-months / HF patient-months / dialysis patients in cohort month | 36,935 / 5,094 / 24 | 9 / 0 / 1 | 10 / 8 / 0 | 0 / 0 / 0 |
| 8 Output 12M Rx / eligible / Rx T2D / Rx HF / `DIALYSIS_FLAG` | 39,150 / 32,066 / 36,935 / 5,094 / 1 | 19 / 16 / 9 / 0 / 1 | 24 / 24 / 10 / 8 / 0 | 0 / 0 / 0 / 0 / 0 |
| Match step 7 = step 8 | Yes | Yes | Yes | Yes (row exists: eligible history before the window, Q1) |

Edge days: covered by the full recompute (Q3, calendar month buckets; 0 mismatches on every NPI x cohort).

## 10. Findings and actions

| # | Finding | Severity | Action / owner | Status |
| --- | --- | --- | --- | --- |
| F1 | Eligibility input `full_2026_11_16_pj_pat_sglt2_filter_m` is the stale version (mean flag 0.7697 vs 18.5% with the current PJ06 code, readiness 4 / 6.3). All eligible-based features (all except `TOTAL_RX_PATIENTS*`, `TOTAL_RX_PATIENTS_*`, `PCT_RX_PATIENTS_*`, `DIALYSIS_FLAG`) will change | Blocker for V6 and for using the eligible features in feature selection | Re-run PJ06 with the C1 fix, then NB06 into a new run; re-run this QC (Q3 / Q10 queries can be reused) / pipeline owner | Open |
| F2 | Rejected claims counted: 3.37% of eligible patient-months come only from rejected Rx claims (readiness 5.3 / R1, V2) | Fix or doc | Decide: keep ("patients seen") or count paid + reversed only; document in the plan / NBA team | Open |
| F3 | Provider copy: 3,001 rows with null `PROVIDER_ID`, +1,222 rows vs NPI table, 42 IDs outside the universe, 310 universe IDs without a row. Causes not re-measured here; summary attributes them to the 3.0 mapping | Fix | Apply the agreed mapping fix (same rule in all six HCP notebooks) / pipeline owner | Open (known) |
| F4 | `run_registry`: `full_2026_11_16` `IS_RUN_OF_RECORD` = False | Doc | Set the run of record once F1 is resolved / NBA team | Open |
| F5 | Stale text: summary lists HF types `HFPEF` / `HFREF` / `HF_UNSPECIFIED` (output: `HFPEF_PROXY` / `HFREF_PROXY` / `MIXED` / `UNKNOWN`); summary status "validated on the 10 HCPs, ready for the full run" and plan header (outputs "180 rows", `notebook_output/...`) predate the full UC run; title cell walkthrough still names `Rx_01_new` | Doc | Update summary and plan headers / notebook owner | Open |
| F6 | Holdout vs training non-zero share moves > 5 points on 19 UACR stage and `RUNNING_` columns (max +12.8) | Note | Expected (history length, UACR coverage); consider for modelling | Noted |
| F7 | V7: NB06 stage = PJ06 Dx-first label, stage 3 not split; readiness 6.2 recommends lab first with 3a / 3b | Note | Section 7 work (new V7 view), not a defect of NB06 | Noted |
| F8 | 6.1 bridge: NB06 grain is Rx-only HCP-patient-month; Dx / Lab-only patients absent | Note | Input for the bridge design (section 7) | Noted |
| F9 | Sparse grain: rows only for NPIs with eligible history up to the cohort | Note | Zero-fill missing HCP x cohort rows downstream | Noted |

## 11. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 11 / 14 (Q6, Q13 open; Q14 data pass, sign-off open) |
| QC by / date | Genie Code for Saurabh Modi, 2026-11-27 |
| O5 and drift review (NBA team) / date | |
| Reviewed by / date | |
| Next | Resolve F1 (PJ06 re-run, then NB06) and re-run Q3 / Q10 / Q7; decide F2 |
