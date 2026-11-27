# QC 05: Rx new patient starts (NPS) features (HCP monthly, NB05), NBA 3.1

**QC status:** DONE, 2026-11-27 (claim type Rx NPS; plan: `05_rx_nps_claims_features_qc_plan.md`)  
**Verdict:** PASS with actions. The calculation is correct. All 95 count features were recomputed independently from the NB05 Rx pull over all 8,088,324 provider x cohort rows, and all 68 `PCT_` features were checked against their formula. A separate pandas trace of 5 cases also matched. Grain, cohorts, windows, invariants and fill rate are clean. Open items: rejected claims count as starts (11.2% of class starts, 34.0% of Kerendia starts, readiness V1 paid-only rule); the first-start history covers only claims written by universe HCPs; the output is keyed by `PROVIDER_ID`, not `NPI_NUMBER` (readiness 5.1); stale doc text; the run is not flagged as run of record; NBA-team drift sign-off.  
**QC run:** 2026-11-27, serverless (Genie Code scratch session), on the output written 2026-11-17 06:35 (`PULL_DT` 2026-11-17, job 1010893614518587, run `full_2026_11_16`). Notebook re-run during QC: **no**. Evidence = read-only queries only; no notebook or table changed.

Rule source = `Feature_Evaluation/05_Feature_Views/NBA_3_1_LAAD_Feature_Views_Readiness_Plan.md` ("readiness"): section 6 (contender views), plus sections 4, 5.1, 5.3 and 5.4. Section 7 (work plan) is out of scope. Developer rules: `NBA_3_1_Rx_NPS_Features_Plan.md` ("plan") and `NBA_3_1_Rx_NPS_Features_Client_Summary.md` ("summary"). `<S>` = `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_nba_3_1`.

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `hcp_level_features/05 Rx NPS Claims Files/05_claim_rx_nps_monthly_cohort` (31 cells) |
| Upstream notebooks | `Patient_Journey_Validation/Rx Files/03_patient_journey_rx`, Step 4e (cell 46) writes the NB05 pull. `Combine Files/06_patient_journey_combine_3_1` (PJ06) is **not** read by NB05: 0 references either way (see F6) |
| Rule file | Readiness sections 4, 5.1, 5.3, 5.4, 6 |
| Source table | `<S>.full_2026_11_16_pull_rx_nps` (`HCP_NPS_TABLE`, `HCP_NPS_SOURCE = "3.1"`): 4,649,582,001 rows, `SVC_DT` 2021-01-02 .. 2026-09-30, 294,674 `PROVIDER_ID`, 294,670 NPIs, 12 raw `TREATMENT_CATEGORY`, 17 `CATEGORY` |
| Universe | `<S>.input_hcp_universe`: 294,727 `PROVIDER_ID` |
| Cohorts | `<S>.input_claims_cohorts`: 28 cohorts c1 .. c28, offset 0, lookback end 2024-05 .. 2026-08. Training c1-c24, Testing c25-c26, Holdout (Backtesting) c27-c28 |
| Mapping | None in NB05: the pull already carries `PROVIDER_ID` and `NPI_NUMBER` (1 NPI per provider; 4 NPIs have 2 providers) |
| Output | `<S>.full_2026_11_16_hcp_claim_rx_nps_monthly_cohort`: 8,088,324 rows x 172 columns (163 features + 9 metadata: `PROVIDER_ID`, `COHORT_ID`, `COHORT_MONTH`, `OFFSET_DAYS`, `CUTOFF_DATE`, `SVC_DT_M`, `PULL_DT`, `DATASET`, `COHORT_SET`), 294,579 providers |
| Expected grain | One row per `PROVIDER_ID` x `COHORT_ID` **for providers with at least one counted claim from 2023-01-01 to the cohort cutoff** (sparse, not universe x 28) |
| NBA 3.0 counterpart | `05_claim_rx_nps_monthly` -> `ops_pipeline_bkp/notebook_output/kerendia_nba_3_0_claim_rx_nps_monthly` (13,357,266 rows, months 2022-01 .. 2026-09, 234,338 providers, 188 features) |
| NBA 3.0 final model | 752 features: `/Users/sehar.aejaz.ext@bayer.com/Extra Notebooks/Final NBA 3.0 Modeling Features.xlsx` |

## 2. QC checklist

| # | Check | How | Pass when | Status |
| --- | --- | --- | --- | --- |
| Q1 | HCP universe | Keys, duplicates, rows per cohort vs providers with a counted claim, providers vs universe, null / placeholder IDs | 0 duplicates; rows per cohort = recount; 0 outside universe | PASS |
| Q2 | Right cohorts | Output cohort metadata vs `input_claims_cohorts` | 0 mismatches | PASS |
| Q3 | Windows and point-in-time | E = `CUTOFF_DATE`; N-month window = calendar months (E-N months, E]; `RUNNING_` = 2023-01-01 .. E; first-start dates from the full pull history; edge-day case | No claim after E counted | PASS (load-date part N/A: no `INSERT_TS` in the pull) |
| Q4 | Data sources vs readiness | Rows, dates, nulls, rejected share, `RX_SOURCE`, Delta history | Same sources, unchanged since the run | PASS |
| Q5 | All features made | 163 expected names (19 values x 4 windows, 19 `RUNNING_`, 17 starts x 4 `PCT_`) vs output | 0 missing, 0 unexpected | PASS |
| Q6 | Business rules | Readiness section 6 (V1, V2, V3, F9, F10) and plan rules vs notebook | Match or documented and agreed | OPEN (F1, F2, F3) |
| Q7 | Fill rate | All 163 features, all / train / test / holdout / c28 | No unexpected nulls; flags explained | PASS |
| Q8 | NBA 3.0 752 coverage | 14 NPS features in the 752 | 0 skipped | PASS |
| Q9 | Preserved vs new | 188 3.0 features vs 163 3.1 features | All labelled | PASS |
| Q10 | HCP trace | Full SQL recompute of all count cells + pandas trace of 5 provider x cohort cases | Output = recompute | PASS |
| Q11 | Invariants | Nesting, start <= visits, total-new bounds, `PCT_` formula, `RUNNING_` monotonic, no negatives | 0 violations | PASS |
| Q12 | NBA 3.0 output comparison | 3.0 month 2026-08 vs 3.1 c28 on common providers | Differences explained | PASS |
| Q13 | Reproducibility and docs | Delta history, run registry, doc headers | No stale text that changes meaning | OPEN (F4, F5) |
| Q14 | Basket and data drift (owner: NBA team) | Class / brand basket vs config; monthly volumes (F9, 95% rule); active providers and 12M starts per `DATASET` | Basket = config; drift <= 20% or explained | Data PASS; NBA-team sign-off OPEN |

## 3. Evidence log

| # | Result (numbers) | Where (query) | Notes |
| --- | --- | --- | --- |
| Q1 | 8,088,324 rows = 8,088,324 distinct (`PROVIDER_ID`, `COHORT_ID`); 0 null, 0 `'0'` / blank IDs; 294,579 providers, **0 outside** the 294,727 universe. Rows per cohort rise from 278,220 (c1) to 294,579 (c28). Expected rows per cohort (providers whose first pull claim from 2023-01-01 is <= cutoff) = output for **all 28 cohorts, 0 difference** | `count / count distinct`; `left anti join input_hcp_universe`; per-cohort recount from `pull_rx_nps` `min(SVC_DT)` per provider joined to `input_claims_cohorts` | Sparse grain is by design. 148 universe providers never appear (no counted claim by the c28 cutoff). Downstream must zero-fill missing provider x cohort rows |
| Q2 | 28 distinct cohort rows in the output, all 28 in the file: **0 mismatches** on `DATASET`, `OFFSET_DAYS` (0), `CUTOFF_DATE` = `last_day(lookback_end_date)`, `SVC_DT_M` = `lookback_end_date`, `COHORT_MONTH`. `PULL_DT` 2026-11-17 on all rows; 7 `COHORT_SET` groups | `select distinct` metadata from output, joined to `input_claims_cohorts` | - |
| Q3 | Independent SQL recompute (own category cleaning; first dates per patient x class and patient x brand over the whole pull; counted claims >= 2023-01-01; calendar-month buckets `months_between(lookback_end, month) < N`; running = month <= lookback end) vs output: 8,088,324 rows joined, 0 rows on one side only. 95 count columns: all start, total-new and `RUNNING_` start cells match. 1,671 `TOTAL_PATIENTS_VISIT*` cells (16 providers) differed only because the QC query used `count(distinct spec, patient)`, which drops rows with a null `PRIMARY_SPECIALTY_CODE` (17 providers, 11,232 rows in the pull). A null-safe recount for those 16 providers x 28 cohorts (444 rows) gives **0 mismatches**. Edge case provider 10000012, c28: 12 claims on E (2026-08-31) counted, 3 on E+1 (2026-09-01) not; 1M visits 155 = output | Temp views `r`, `mon`, `lng`, `exp` on `pull_rx_nps` vs the output | No load timestamp in the pull, so late loads can't be tested (readiness 5.4 notes the same) |
| Q4 | Pull: 4,649,582,001 rows, 2021-01-02 .. 2026-09-30, 0 null `PROVIDER_ID` / `PATIENT_ID`. Rows from 2023-01-01 = 3,275,477,893 = readiness section 4 row count of `pull_rx_hcp` (same query and basket, as PJ03 Step 4e says). `RX_SOURCE` values: JOURNEY, HCP_ONLY. `REJECTION_FLAG = 1`: 416,068,393 (8.9%; JOURNEY 402,353,494, HCP_ONLY 13,714,899). Delta history: pull v0 CTAS 2026-11-17 02:22, output v0 CTAS 06:35 (both job 1010893614518587); after that only OPTIMIZE / VACUUM on the pull and SET TBLPROPERTIES on the output, so the input is unchanged since the output was written. Output in `kerendia_nba_3_1`, nothing written to the 3.0 volume | `count`, `min/max`, `group by RX_SOURCE, REJECTION_FLAG`, `describe history` | Rejected claims are marked only by `REJECTION_FLAG` |
| Q5 | 163 features (95 counts, 68 `PCT_`): 76 window counts, 19 `RUNNING_`, 68 `PCT_`. The expected-name list was generated from the data's 10 classes (after GLP-1 / DPP-IV -> `Other- glucose mgmt`) + 7 brands: **0 missing, 0 unexpected**. Classes include `KERENDIA` (new in 3.1). `Diuretic + MRA` brand absent (no such `CATEGORY` in the pull; not in the 3.0 output either). No trend / DIFF columns | Generated list vs `spark.table(...).columns` | Plan and summary still say 154 features (F4) |
| Q6 | See section 4: 11 rules; 8 match, 3 open (F1 rejected claims, F2 first-start history scope, F3 entity key) | NB05 code; PJ03 Step 4e (cell 46); `00_cohort_config` | V1 is Track R (register): the logic is not changed in this QC |
| Q7 | 0 null cells in all 163 features; min >= 0 everywhere; `PCT_` max <= 1; no constant column. > 99.5% zero: `..._INVOKANA_100MG_IN_LAST_1_MONTH` 99.56%, `..._INVOKANA_300MG_IN_LAST_1_MONTH` 99.72% (and their `PCT_`). Train vs holdout change > 5 points on 31 columns (section 7), largest Farxiga starts 3M 34.97% -> 14.70% | One aggregate query per `DATASET` + c28 | Flags explained in section 7 |
| Q8 | 14 NB05 features in the 752 (best: `TOTAL_PATIENTS_START_SGLT2_IN_LAST_6_MONTH`, rank 19, 0.69% SHAP); all 14 present in the 3.1 output under the same name | xlsx parsed with `zipfile` (no openpyxl on serverless) | Not checked against the plan's list of NB05 features in the selected 277 |
| Q9 | 3.0: 188 features = 154 window / running / `PCT_` + 34 base-month columns. 154 preserved under the same name; the 34 base-month columns duplicate `_IN_LAST_1_MONTH` (the notebook parity maps them there); 9 new `KERENDIA` features. 154 + 9 = 163 | Column lists of both outputs | Section 8 |
| Q10 | Pandas trace (separate code from the SQL recompute) of 5 provider x cohort cases, 95 count checks each, **0 mismatches** (section 9). Together with Q3, all 95 count columns are proven on every row | `/tmp/nps_trace.pkl` (scratch) | Config trace HCP 1386651560 (= provider 7608159) is case 1 |
| Q11 | Over 8,088,324 rows: 1M <= 3M <= 6M <= 12M <= `RUNNING_` for all 19 values: 0 violations. Any start or total-new > visits in the same window: 0. Total-new > sum of class starts: 0. Total-new < largest class start: 0. `PCT_` = start / visits (0 when visits = 0): 0 differences > 1e-9 on 68 columns. `RUNNING_` visits, total-new and Kerendia never decrease from cohort to cohort: 0. 34,639 rows have 0 visits in 12M but `RUNNING_` > 0 (provider inactive in the last year, by design) | One aggregate SQL on the output; `lag()` over cohorts | - |
| Q12 | 3.0 month 2026-08 (234,338 providers) vs 3.1 c28 (294,579): 220,895 common, 13,443 only 3.0, 73,684 only 3.1. Spearman on common: visits 12M 0.991 (+7.9% total), new patients 12M 0.968 (+2.2%), SGLT2 6M 0.901 (+32.9%), ACE/ARB 3M 0.969 (-8.6%), Jardiance 12M 0.987 (-4.9%), GLP-1 12M 0.818 (+143.3%), `RUNNING_` SGLT2 0.914 (-36.3%) | pandas on the two outputs | High rank agreement. Total shifts are consistent with the 3.1 input (different basket and pull) and universe, and with `RUNNING_` counted from `DATA_START_DATE` 2023-01-01 in 3.1 vs a longer history in 3.0 (months from 2022-01). Product-level causes (e.g. GLP-1 +143%) were not traced |
| Q13 | Output written once (v0 CTAS 2026-11-17 06:35; registry job run 814119312914044). `run_registry`: `full_2026_11_16` SUCCESS, NB07 "all 11 HCP tables OK", **`IS_RUN_OF_RECORD` = False**. Stale text: plan and summary say input stays 3.0 `Rx_05`, "154 features / 163 columns", "20 cohorts, offset 7" (plan update header); the NB05 code and config read the 3.1 pull | `describe history`; `run_registry`; doc read | F4, F5 |
| Q14 | Basket: 12 raw classes (incl. GLP-1, DPP-IV, KERENDIA) -> 10 after the config mapping (GLP-1, DPP-IV -> `Other- glucose mgmt`); 7 of the 8 `HCP_BRANDS` present (no `Diuretic + MRA`). Monthly pull rows Jul 2025 .. Sep 2026 / median of the 3 months before: 0.921 .. 1.063; Sep 2026 (lag month) 0.977, Aug 2026 0.998; below 0.95 only Feb 2026 (0.921, short month) and Nov 2025 (0.945). Per `DATASET`, average per cohort vs training: active providers +2.1% (test and holdout), visits 12M +3.8% / +3.6%, new patients 12M -12.1% / -13.1%, **Kerendia starts 12M +19.2% / +25.1%**, **Farxiga starts 12M -27.9% / -39.3%** | `group by trunc(SVC_DT,'MM')`; aggregate per `DATASET` | Two changes > 20%: Kerendia starts rising and Farxiga brand starts falling. Likely market causes (Kerendia uptake, generic dapagliflozin) were not verified at product level. Needs NBA-team sign-off |

## 4. Business rules (readiness vs notebook)

| Rule | Readiness / plan says (section) | Notebook does (cell / decision) | Match |
| --- | --- | --- | --- |
| Input table | Plan / summary: "input stays 3.0 `Rx_05`" | NB05 + config: `HCP_NPS_SOURCE = "3.1"` -> `full_2026_11_16_pull_rx_nps` (PJ03 Step 4e, 3.1 basket, from 2019-11-01) | Code correct, docs stale (F4) |
| Start definition | Plan: first claim of the class / brand of the patient, by **any** HCP, credited to the HCP who wrote it | `min(SVC_DT)` per patient x class / brand over all pull claims of the patients (proven by Q3 recompute) | Logic matches; scope of "any HCP" open (F2) |
| First-start history | Plan: needs history before 2023 | Pull from 2021-01-02 (`HCP_RX_HISTORY_START` 2019-11-01 filter); counted claims from `DATA_START_DATE` 2023-01-01 only | Match |
| Specialty in distinct key | 3.0 behaviour: kept | Visits and starts distinct on (provider, specialty, patient, ...); null specialty is kept as its own value (17 providers) | Match (proven Q3) |
| `PCT_` denominator | 3.0 behaviour: sum of monthly distinct visits | start / `TOTAL_PATIENTS_VISIT_IN_LAST_N_MONTH`, 0 when denominator 0 | Match (Q11) |
| GLP-1 / DPP-IV | Config: class mapped to `Other- glucose mgmt`, brand kept | `hcp_rx_categories()`; no duplicate columns (Q5) | Match |
| Kerendia | 3.1 basket includes Kerendia | `TOTAL_PATIENTS_START_KERENDIA_*` (9 features) | Match (new) |
| Windows | `HCP_LOOKBACK_WINDOWS["nps"]` = 1 / 3 / 6 / 12 | 1 / 3 / 6 / 12 + `RUNNING_`, same as 3.0 | Match |
| V1 paid-only (target-aligned) | Readiness 6, V1: paid-only filter | No filter on `REJECTION_FLAG`: rejected claims count as visits and starts. 15,824,899 of 141,511,286 class starts from 2023 (11.18%) have only rejected claims on the start day; Kerendia 134,454 of 395,486 (34.0%) | **Open (F1)** |
| V1 entity / timestamp | Readiness 5.1: entity `NPI_NUMBER`; label timestamp = 1st of the month after the lookback end | Output keyed by `PROVIDER_ID` only; time = `SVC_DT_M` (= lookback end month) and `CUTOFF_DATE` (= last day of it) | **Open (F3)**: register with an `NPI_NUMBER` column (1:1 in the pull, 4 NPIs with 2 providers) and a derived timestamp = `CUTOFF_DATE` + 1 day |
| V1 stateful | Readiness 6: first claim per patient is stateful, keep in notebooks | NB05 computes it in the notebook | Match |

Other section 6 views: **V2** (claim type) is not an NB05 feature; the rejected share is reported under F1, and RV can't be split (no `CLAIM_TYPE`). **V3** (SGLT2 add-on pool): NB05 has SGLT2 and Kerendia starts, but no "on SGLT2, not on Kerendia" state, so N/A. **F9** (completeness) is reported in Q14. **F10** (trends): NB05 has no trend columns, so N/A. **V4-V10**: not Rx NPS, N/A.

## 5. Data sources (readiness vs notebook)

| Source | Readiness says | Notebook uses | Rows / dates found | Match |
| --- | --- | --- | --- | --- |
| Rx claims | Section 4: `full_2026_11_16_pull_rx_hcp`, 3,275,477,893 rows, 2023-01-01 .. 2026-09-30, no `CLAIM_TYPE` | `full_2026_11_16_pull_rx_nps` (same query, from 2019-11-01) | 4,649,582,001 rows, 2021-01-02 .. 2026-09-30; 3,275,477,893 from 2023 | Yes (from 2023 identical in count) |
| Cohorts | Section 4: `input_claims_cohorts`, 28 cohorts, lookback end 2024-05 .. 2026-08 | `get_hcp_cohort_months()` | 28 cohorts, 0 mismatches | Yes |
| Universe | Section 4: `input_hcp_universe` keyed by `PROVIDER_ID` | Pull filtered to the universe in PJ03 Step 4e | 294,727; 0 output IDs outside | Yes |
| Patient tables (PJ06) | Not used by V1 | None | - | Yes (brief said NB05 joins a PJ06 table: not the case, F6) |
| Data end | Section 4 / 5.4: pulls end 2026-09-30 = lag month of c28 | Common end date over HCP inputs | Max `SVC_DT` 2026-09-30; c28 cutoff 2026-08-31 | Yes |

## 6. Features made (plan vs output)

| Plan family | Expected | Output columns | Status |
| --- | --- | --- | --- |
| Patients visiting | 4 windows + `RUNNING_` | 5 (`TOTAL_PATIENTS_VISIT_*`) | PASS |
| Class starts | 10 classes x (4 windows + `RUNNING_`) | 50 (ACE/ARB, CCB/BB, combo, diuretic non-MRA, insulin, **Kerendia**, MRA, other glucose, SGLT2, metformin) | PASS |
| Brand starts | 7 brands x (4 windows + `RUNNING_`) | 35 (DPP-IV, Farxiga, GLP-1, Invokana 100 / 300, Jardiance, spironolactone-MRA) | PASS |
| Total new patients | 4 windows + `RUNNING_` | 5 (`TOTAL_NEW_PATIENT_START_*`) | PASS |
| `PCT_` | 17 starts x 4 windows | 68 | PASS |
| Trend (F10) | Not in NB05 | 0 | N/A |
| **Total** | 163 | 163 | 0 missing, 0 unexpected |

## 7. Fill rate

% over all 8,088,324 output rows. No sentinel values exist (0 is the empty value; 0 null cells in all 163 features).

| Feature (group) | % null | % zero | % non-zero | % sentinel | min / max | % non-zero train / test / holdout / c28 | Flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Visits 1M / 3M / 6M / 12M / `RUNNING_` | 0 | 2.83 / 1.56 / 0.96 / 0.43 / 0 | 97.17 / 98.44 / 99.04 / 99.57 / 100 | 0 | 0 / 63,321 (12M) | 12M: 99.60 / 99.45 / 99.37 / 99.35 | - |
| Total new patients 1M / 3M / 6M / 12M / `RUNNING_` | 0 | 10.22 / 5.17 / 3.24 / 1.75 / 0.49 | 89.78 / 94.83 / 96.76 / 98.25 / 99.51 | 0 | 0 / 8,411 (12M) | 12M: 98.32 / 97.93 / 97.74 / 97.70 | - |
| Class / brand starts, 1M (17) | 0 | 31.50 .. 99.72 | 0.28 .. 68.50 | 0 | >= 0 | c28 0.10 .. 62.05 | Invokana 100MG / 300MG > 99.5% zero |
| Class / brand starts, 3M / 6M / 12M (51) | 0 | up to 99.21 / 98.46 / 96.95 | from 0.79 / 1.54 / 3.05 up to 85.67 / 91.14 / 94.56 | 0 | >= 0 | - | - |
| Starts `RUNNING_` (17) | 0 | 2.51 .. 91.73 | 8.27 .. 97.49 | 0 | >= 0 | c28 9.23 .. 98.42 | - |
| `PCT_` (68) | 0 | same as the start column | same as the start column | 0 | 0 / <= 1 | - | as the start column |
| SGLT2 starts 6M | 0 | 21.99 | 78.01 | 0 | 0 / 990 | 78.10 / 77.70 / 77.27 / 77.12 | - |
| Kerendia starts 12M | 0 | 91.02 | 8.98 | 0 | 0 / 555 | 8.68 / 10.49 / 11.11 / 11.28 | Rising |
| `RUNNING_` Kerendia starts | 0 | 86.41 | 13.59 | 0 | 0 / 955 | 12.84 / 17.50 / 18.48 / 18.74 | +5.6 points (running total grows) |
| Farxiga starts 3M | 0 | 67.35 | 32.65 | 0 | 0 / 357 | 34.97 / 23.41 / 14.70 / 13.59 | **-20.3 points** |
| Invokana 300MG starts 1M | 0 | 99.72 | 0.28 | 0 | 0 / 24 | 0.31 / 0.12 / 0.10 / 0.10 | > 99.5% zero |

Train vs holdout change > 5 points (31 columns: 14 window counts, the same 14 `PCT_`, 3 `RUNNING_`): Farxiga 1M -12.77, 3M -20.27, 6M -15.23, 12M -7.62; ACE/ARB 1M -10.09, 3M -6.92; metformin 1M -8.59, 3M -5.53; Jardiance 1M -6.76, 3M -5.62; CCB/BB 1M -6.64; diuretic non-MRA 1M -6.59; combo 1M -5.61; insulin 3M -5.07; `RUNNING_` Kerendia +5.64, DPP-IV +5.78, Farxiga +7.04. Reading: short-window starts drop in later cohorts as patients accumulate history (fewer "first ever" claims), plus a Farxiga brand decline (cause not traced); `RUNNING_` totals grow with time by construction.

## 8. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature | In 752? (SHAP rank, % SHAP) | NBA 3.1 feature | Status | Reason |
| --- | --- | --- | --- | --- |
| `TOTAL_PATIENTS_START_SGLT2_IN_LAST_6_MONTH` | Yes (19, 0.691%) | same | preserved | Totals +32.9% vs 3.0 (Q12) |
| `TOTAL_NEW_PATIENT_START_IN_LAST_1_MONTH` | Yes (62, 0.339%) | same | preserved | - |
| `PCT_TOTAL_PATIENTS_START_ACE_OR_ARB_IN_LAST_3_MONTH` | Yes (76, 0.290%) | same | preserved | - |
| `PCT_TOTAL_PATIENTS_START_COMBO_DRUG_IN_LAST_12_MONTH` | Yes (138, 0.178%) | same | preserved | - |
| `RUNNING_TOTAL_PATIENTS_START_SGLT2` | Yes (145, 0.171%) | same | preserved | Counted from 2023-01-01 in 3.1: values lower (Q12, -36.3%) |
| `TOTAL_PATIENTS_START_DIURETIC_NON_MRA_IN_LAST_3_MONTH` | Yes (161, 0.157%) | same | preserved | - |
| `PCT_TOTAL_PATIENTS_START_METFORMIN_IN_LAST_12_MONTH` | Yes (191, 0.130%) | same | preserved | - |
| `PCT_TOTAL_PATIENTS_START_DIURETIC_NON_MRA_IN_LAST_3_MONTH` | Yes (277, 0.096%) | same | preserved | - |
| `TOTAL_PATIENTS_START_SPIRONOLACTONE_MRA_IN_LAST_12_MONTH` | Yes (340, 0.072%) | same | preserved | - |
| `TOTAL_PATIENTS_START_JARDIANCE_IN_LAST_1_MONTH` | Yes (359, 0.067%) | same | preserved | - |
| `TOTAL_NEW_PATIENT_START_IN_LAST_3_MONTH` | Yes (377, 0.063%) | same | preserved | - |
| `TOTAL_PATIENTS_START_SPIRONOLACTONE_MRA_IN_LAST_3_MONTH` | Yes (499, 0.040%) | same | preserved | - |
| `TOTAL_PATIENTS_START_COMBO_DRUG_IN_LAST_3_MONTH` | Yes (595, 0.028%) | same | preserved | - |
| `TOTAL_PATIENTS_START_JARDIANCE_IN_LAST_12_MONTH` | Yes (615, 0.024%) | same | preserved | - |
| Other 140 window / `RUNNING_` / `PCT_` features | No | same names | preserved | - |
| 34 base-month columns (e.g. `TOTAL_PATIENTS_VISIT`, `PCT_TOTAL_PATIENTS_START_SGLT2`) | No | `..._IN_LAST_1_MONTH` | replaced | Same value as the 1M window at offset 0; the cohort grain has no separate base month |
| - | - | 9 `..._KERENDIA` (4 windows, `RUNNING_`, 4 `PCT_`) | new | 3.1 basket adds Kerendia as a class |

0 3.0 features dropped without a reason.

## 9. HCP trace (step-by-step recompute)

Pandas code, separate from the SQL recompute of Q3: claims of the provider, all claims of its patients in the pull (for first-start dates), own category cleaning and month buckets.

| Step | Provider 7608159 / c28 (config trace HCP 1386651560) | 21698047 / c10 (no claims in 12M) | 10084143 / c28 (Kerendia starter) | 10000012 / c28 (window edge) | 10000290 / c5 (high volume, training) |
| --- | --- | --- | --- | --- | --- |
| 1 Provider in universe | yes | yes | yes | yes | yes |
| 2 Raw rows of the provider (all dates) | 29,424 | 3,012 | 1,115 | 9,956 | 26,363 |
| 2b Patients / all their claims by any universe HCP | 1,172 / 55,669 | 488 / 23,321 | 347 / 26,477 | 1,288 / 75,298 | 2,399 / 123,328 |
| 3-4 Counted: 2023-01-01 <= `SVC_DT` <= E | 19,969 (E 2026-08-31) | 2 (E 2025-02-28) | 898 | 8,469 | 10,249 (E 2024-09-30) |
| 5 Loaded before `PREDICTION_MONTH` | N/A (no load date) | N/A | N/A | N/A | N/A |
| 6 Claims on E / on E+1 | 26 / 18 | 0 / 0 | 5 / 7 | 12 / 3 | 28 / 18 |
| 7 Visits 1M / 12M / `RUNNING_` | 268 / 3,081 / 11,317 | 0 / 0 / 1 | 71 / 481 / 715 | 155 / 1,682 / 6,080 | 307 / 4,113 / 6,918 |
| 7 New patients 12M; SGLT2 starts 12M; Kerendia starts 12M | 123; 7; 1 | 0; 0; 0 | 83; 19; 5 | 58; 2; 0 | 164; 4; 0 |
| 8 Output = step 7 (95 count columns) | 95 / 95 match | 95 / 95 | 95 / 95 | 95 / 95 | 95 / 95 |

## 10. Findings and actions

| # | Finding | Severity | Action / owner | Status |
| --- | --- | --- | --- | --- |
| F1 | Rejected claims (`REJECTION_FLAG = 1`, 8.9% of pull rows) count as visits and as starts. 11.18% of class starts from 2023 (15,824,899 of 141,511,286) and 34.0% of Kerendia starts (134,454 of 395,486) have only rejected claims on the start day. Readiness V1: paid only. Whether 3.0 filtered rejected claims was not checked in this QC | fix (decision) | NBA team: decide whether a start needs a paid claim (filter `REJECTION_FLAG = 0` for the start date, or keep 3.0 parity and document). Owner: Wenjie (to confirm) | OPEN |
| F2 | First-start dates use only claims written by universe HCPs: PJ03 Step 4e filters the pull to the HCP universe (`left_semi` on `PROVIDER_ID`). The plan / summary say a start is the first claim "by any HCP". A patient who started with a non-universe HCP looks like a new start at a universe HCP | fix (confirm) | Confirm whether 3.0 `Rx_05` had the same universe filter. If not, write the history part of the pull without the universe filter. Owner: Wenjie | OPEN |
| F3 | Output keyed by `PROVIDER_ID` with `SVC_DT_M` / `CUTOFF_DATE`; readiness 5.1 needs `NPI_NUMBER` + label timestamp (1st of month after lookback end) for Track R registration | doc / prep | Add `NPI_NUMBER` (1:1 from the pull; 4 NPIs with 2 providers to resolve) and the timestamp when registering (out of scope here) | OPEN |
| F4 | Stale docs: plan / summary say input = 3.0 `Rx_05`, "154 features / 163 columns", "20 cohorts, offset 7"; Actual: 3.1 pull, 163 features + 9 metadata = 172 columns, 28 cohorts offset 0 | doc | Update plan, summary and NB05 markdown | OPEN |
| F5 | `run_registry`: `full_2026_11_16` `IS_RUN_OF_RECORD` = False | doc | Flag the run of record before feature selection | OPEN |
| F6 | Task brief says NB05 joins a PJ06 combine patient-month table; NB05 reads only the Rx pull (0 references between NB05 and PJ06) | note | None; QC tested the code as written | CLOSED |
| F7 | Drift > 20% vs training: Kerendia starts 12M +25.1% (holdout), Farxiga starts 12M -39.3% (holdout) / -27.9% (test). Pull months Nov 2025 (0.945) and Feb 2026 (0.921) are below the 95% rule; the lag month Sep 2026 is complete (0.977) | note (owner NBA team) | NBA-team review and sign-off | OPEN |
| F8 | 17 providers have rows with null `PRIMARY_SPECIALTY_CODE` (11,232 rows); NB05 keeps null as its own specialty value in visit counts | note | None | CLOSED |

## 11. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 11 / 14 (Q6 and Q13 open; Q14 data PASS, sign-off open) |
| QC by / date | Genie Code for Saurabh Modi, 2026-11-27 |
| O5 and drift review (NBA team) / date | |
| Reviewed by / date | |
| Next | NBA-team decisions on F1 / F2; doc fixes F4 / F5; NPI key and timestamp at Track R registration (F3) |
