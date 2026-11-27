# QC 01: Rx claims features (NB01 `01_claim_rx_monthly_cohort`), NBA 3.1

**QC status:** DONE, 2026-11-27 (claim type Rx; next: Dx claims NB02)  
**Verdict:** PASS with actions. Cohorts, windows, sources, invariants and the 6-case HCP trace match exactly (0 mismatches). The provider output covers the universe x 28 spine apart from HCPs before their first Rx (by design). Open: NPI to PROVIDER_ID mapping gaps, the 3.0 vs 3.1 level difference is not yet explained, Kerendia drift needs NBA-team sign-off, and the doc feature counts are out of date.  
**QC run:** 2026-11-27, serverless, on the output written 2026-11-17 (`PULL_DT` = 2026-11-17, run `full_2026_11_16`). Notebook re-run during QC: no (read-only queries only; no notebook or table changed).

Rule source = `Feature_Evaluation/05_Feature_Views/NBA_3_1_LAAD_Feature_Views_Readiness_Plan.md` ("readiness"), section 6 (contender views V1, V2, V3, F10) and section 4 (Rx pull row). Developer rules = `NBA_3_1_Rx_Claims_Features_Plan.md` ("plan") and `00_cohort_config`. UC schema `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_nba_3_1` = `<S>`.

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `hcp_level_features/01 Rx Claims Files/01_claim_rx_monthly_cohort` (39 cells) |
| Rule file | readiness sections 4 and 6 (V1 Kerendia writing, V2 claim type, V3 SGLT2 add-on pool, F10 trends); plan sections 0, 0b, 4, 5 |
| Source table | `<S>.full_2026_11_16_pull_rx_hcp`: 3,275,477,893 rows, `SVC_DT` 2023-01-01..2026-09-30. Written 2026-11-17 by job 1010893614518587 (PJ03 `03_patient_journey_rx` cell 46, Step 4d: `RUN_QUERY_DIR/rx_hcp_pull`, mapped to the UC table name by `path_to_table`) |
| Patient input | `pat_new_and_total_treatments` (PJ06 combine), group 2.8 only |
| Universe | `<S>.input_hcp_universe`: 294,727 `PROVIDER_ID` (0 null) |
| Cohorts | `<S>.input_claims_cohorts`: family claims, offset 0, c1 to c28 (24 Training, 2 Testing, 2 Holdout (Backtesting)); prediction month = lookback end + 2 months |
| Mapping | `kerendia_nba_3_0_npi_bhid_mapping` (NPI_NUMBER -> PROVIDER_ID, NB01 cell 34) |
| Output | `<S>.full_2026_11_16_hcp_claim_rx_monthly_cohort`: 8,088,310 rows x 4,681 columns (9 key / metadata + 4,672 features; 2,586 bigint, 2,086 double). Provider version `<S>.full_2026_11_16_hcp_provider_claim_rx_monthly_cohort`: 8,089,535 rows |
| Expected grain | Template: one row per `PROVIDER_ID` x `COHORT` = universe x 28, checked on the provider output (the only NB01 table with `PROVIDER_ID`). NB01 design (cell 21): one row per HCP with Rx history up to the cutoff x cohort; the main output is keyed by `NPI_NUMBER` only |
| NBA 3.0 counterpart | 3.0 `notebook_output/claim_rx_monthly` (3.0 volume, calendar months 2022-01..2026-10, last written 2026-11-26) |
| NBA 3.0 final model | 752 features: `/Users/sehar.aejaz.ext@bayer.com/Extra Notebooks/Final NBA 3.0 Modeling Features.xlsx` |

## 2. QC checklist

| # | Check | How | Pass when | Status |
| --- | --- | --- | --- | --- |
| Q1 | HCP universe | Distinct keys, rows per cohort, duplicate keys, anti joins of the output against the universe (via mapping), placeholder IDs | Output = universe x 28, 0 duplicates, 0 outside | PASS on the provider output: every missing key explained by design (F1); mapping exceptions (null / outside-universe IDs) tracked in F2 |
| Q2 | Right cohorts | Output `COHORT_ID` / `COHORT_MONTH` / `DATASET` / `OFFSET_DAYS` vs `input_claims_cohorts` | 0 mismatches | PASS |
| Q3 | Windows and point-in-time | E = `CUTOFF_DATE` = last day of lookback end month (offset 0); claim counted if `start < SVC_DT <= E` (`filter_to_window`); recount from the pull incl. a window shifted by one day | No claim after E contributes | PASS (load-date test N/A: no load timestamp in the pull) |
| Q4 | Data sources vs readiness | Readiness section 4 Rx row: rows, dates, null NPI, `REJECTION_FLAG`, `CLAIM_TYPE` | Same sources, differences explained | PASS |
| Q5 | All features made | Plan families + section 6 views vs output columns and types | 0 missing without a reason | PASS (count doc mismatch, F6) |
| Q6 | Business rules | Section 4 table below | Each rule matches or documented | PASS (V2 reversed claims blocked upstream, documented in readiness) |
| Q7 | Fill rate | 18 key features: % null / zero / non-zero, min / max, non-zero by dataset and c28 | No unexpected nulls; flags raised | PASS (flags F5) |
| Q8 | NBA 3.0 752 coverage | Every Rx-named 3.0 feature in the 752 matched by exact name | 0 skipped without a reason | PASS (87 out of NB01 scope, F4) |
| Q9 | Preserved vs new | Section 8 | All labelled | PASS |
| Q10 | HCP trace | 6 NPI x cohort cases recomputed from the pull with separate SQL | Output = recompute | PASS |
| Q11 | Invariants | Full-table recount on 8,088,310 rows | 0 violations | PASS |
| Q12 | NBA 3.0 output comparison | 3.0 `claim_rx_monthly` 2026-08 vs 3.1 c28 on common NPIs | Differences explained | OPEN (F3) |
| Q13 | Reproducibility and docs | `PULL_DT`, row count, history; plan / readiness counts vs output | No stale text that changes meaning | FAIL (doc only, F6) |
| Q14 | Product / category values and drift (owner: NBA team) | Treatment categories and brands in the pull vs `00_cohort_config`; active HCPs and 12M claims per `DATASET` vs Training | Values = config; drift > 20% explained and signed off | OPEN (F5, sign-off) |

Adaptation for Rx: Q3 uses `SVC_DT` vs `CUTOFF_DATE` (no `RX_FILL_DATE` / `INSERT_TS`); Q14 checks treatment categories and brands instead of program groups (`GRP_NUM` does not exist for Rx).

## 3. Evidence log

| # | Result (numbers) | Where (query / cell) | Notes |
| --- | --- | --- | --- |
| Q1 | NPI output: 8,088,310 rows = 8,088,310 distinct (NPI, COHORT_ID); 0 null / '' / '0' NPI; 0 rows with 12M = 0 and RUNNING = 0. Rows per cohort c1 278,220 .. c28 294,575 (grows with history). Main output has no `PROVIDER_ID` column. Provider output: 8,089,535 rows; 0 duplicate non-null (PROVIDER_ID, COHORT_ID); spine universe x 28 = 8,252,356, of which 8,085,481 have a row and 166,875 do not: 159,231 are cohorts before the provider's first cohort with Rx history, 7,644 = 273 providers x 28 with no Rx at all, 0 gaps after the first cohort. Mapping exceptions: 3,094 rows with null `PROVIDER_ID`; 42 `PROVIDER_ID` (960 rows) not in the universe | QC queries on provider output, universe and cohort file (cross join spine, anti / semi joins) | Missing keys follow the cell 21 design (HCPs appear once they have Rx history). A first universe check used NOT IN with null keys (always 0) and was replaced by anti joins |
| Q2 | 28 / 28 cohorts matched; 0 mismatches on month (`COHORT_MONTH` = month of `lookback_end_date`), `DATASET`, `OFFSET_DAYS` (0). `CUTOFF_DATE` = month end for all 28; `COHORT_SET` C1-C5 .. C27-C28 | Group-by on output keys joined to cohort file | |
| Q3 | Recount from the pull (NPI not null, start excl / end incl): c28 1M 76,788,269, 12M 925,756,743, RUNNING 3,200,351,516; c1 1M 71,420,307: all equal to the output sums. Window shifted by one day (08-02..09-01) = 78,264,316 (different, so the edge is tested). Fills on 2026-08-31: 3,461,740 (in); on 2026-09-01: 3,059,526 (out of c28) | Aggregate SQL on the pull vs sums of output columns | Readiness 5.4 (load date vs service date) cannot be tested: the pull has no load timestamp |
| Q4 | Pull: 3,275,477,893 rows (= readiness section 4), 2023-01-01..2026-09-30, 0 null NPI; `REJECTION_FLAG` decimal(1,0): 0 = 2,967,898,454, 1 = 307,579,439, null 0; 16 columns, no `CLAIM_TYPE` (extra `RX_SOURCE`, not used by NB01) | Profile query on the pull | Matches readiness: "No `CLAIM_TYPE` column: only `REJECTION_FLAG`" |
| Q5 | 4,672 feature columns. Exact counts: Kerendia 234 (= plan X16 +234), `RATIO_..._IN_PRIOR_3_LAST_3_MONTH` 12, `PCT_` 2,052, `RUNNING_` 520, NBRx / NRx / TRx 0. Windows 1 / 3 / 6 / 12 only | Output schema | Other family counts by name prefix are approximate (gender `_F` / `_M` / `_U` suffixes not separated) and not reported |
| Q6 | See section 4 | Notebook cells 10-34, `00_cohort_config` | |
| Q7 | Section 7: 0% null on all 18; `RUNNING_TOTAL_RX_CLAIMS` min 1; no feature > 99.5% zero; train vs holdout non-zero change > 5 pts on Kerendia 12M (+5.22) and RUNNING Kerendia (+8.53) | One aggregate pass over the full output | |
| Q8 | 752 file: 259 Rx-named 3.0 features (22.59% SHAP). 172 in the 3.1 output by exact name (17.53% SHAP, best rank 14), incl. all 137 of sub-category "Rx Claim-based". 87 not in NB01 (5.06% SHAP, best rank 35): all Rx x CKD stage (`..._PATIENT_WITH_DX_GFR/UACR_STAGE_...`, `..._PATIENT_WITH_GFR_STAGE_...`, sub-category "Dx CKD stage") | xlsx parsed (sheet 1, 752 rows) vs output schema | The notebook that owns the 87 was not verified (F4) |
| Q9 | Section 8 | | |
| Q10 | 6 cases, 5 distinct NPIs, all values equal (section 9) | Separate SQL on the pull, window E from the cohort file | |
| Q11 | 0 violations of: total and Kerendia nesting 1M <= 3M <= 6M <= 12M <= RUNNING; rejected <= total (SGLT2, Kerendia 12M); Jardiance + Farxiga + Invokana 100 + 300 <= SGLT2 (12M); `SGLT2_WO_INVOKANA_300MG` = SGLT2 - Invokana 300 (12M); Kerendia <= total (12M); `PCT_` Kerendia 12M in [0, 1], = Kerendia / total, 0 when total = 0; no negatives (5 columns) | One SQL pass, 8,088,310 rows | |
| Q12 | 3.0 2026-08 (235,825 NPIs) vs 3.1 c28 (294,575 NPIs), 221,438 common. On common NPIs: total 12M +10.83% (Spearman 0.9915); SGLT2 12M +19.49% (0.9872); rejected SGLT2 12M +44.45% (0.9631); total 1M +14.30% (0.9891); HCPs > 0 almost equal (220,375 vs 220,448 for total 12M) | 3.0 Delta table vs 3.1 output, Spearman on a sample of 200,000 common NPIs | Rankings agree; levels differ. Cause not tested (Rx basket, Step 4d claim key, universe, data vintage) |
| Q13 | `PULL_DT` = 2026-11-17 on all 28 cohorts; history: CTAS 2026-11-17 06:13 (job 1010893614518587), table properties 2026-11-19. Plan: 4,668 features; readiness 1 / 7: "NB01 = 4,677 columns"; output: 4,672 features / 4,681 columns | Output, `DESCRIBE HISTORY`, docs | |
| Q14 | 12 treatment categories in the pull; GLP-1 (375.8M) and DPP-IV (43.3M) become "Other- glucose mgmt" via `HCP_RX_CATEGORY_MAP`; `KERENDIA` 3,933,727 claims, 82,207 NPIs. Brands: 7 of 8 `HCP_BRANDS` present; "Diuretic + MRA" 0 rows and no column. Drift (mean per cohort vs Training): active HCPs +2.1% (test and holdout), 12M claims +4.1%, Kerendia 12M +33.7% test / +39.2% holdout | Pull group-by; output group-by on `DATASET` | Kerendia drift > 20%: needs NBA-team sign-off |

## 4. Business rules (readiness vs notebook)

| Rule | Readiness says (section) | Notebook does (cell / decision) | Match |
| --- | --- | --- | --- |
| Entity key | `NPI_NUMBER` STRING for all views (5.1) | Output keyed by `NPI_NUMBER` (STRING), provider table by `PROVIDER_ID` (cell 34) | Yes |
| Windows | Calendar months; 3 and 12 months plus running total and 3 vs previous 3 (5.2, 5.3) | 1 / 3 / 6 / 12 months ending at `CUTOFF_DATE` (offset 0 = month end), start exclusive / end inclusive (`filter_to_window`); `RUNNING_` = all history to the cutoff | Yes (Q3 recount exact) |
| V1 Kerendia writing | NBRx, TRx, running totals, time since first Kerendia Rx; register NB01 / NB05 output (Track R); NBRx stays in notebooks; paid-only needs `CLAIM_TYPE` (6) | Kerendia claim counts (234 columns: windows, `RUNNING_`, `PCT_`, rejected, refill, payer, age, gender, ratio); no NBRx / time-since-first columns in NB01 (NB05); all claim types counted (no paid filter possible) | Yes for NB01 scope; paid-only open upstream |
| V2 Claim type | PD / RV / RJ counts and rejection rate; RJ can start via `REJECTION_FLAG`; RV blocked until PJ03 adds `CLAIM_TYPE` (6) | Group 2.3 `TOTAL_REJECTED_RX_CLAIMS_*` and `RUNNING_TOTAL_REJECTED_*` from `REJECTION_FLAG = 1` (cell 14); no reversed or paid split | Yes (RJ); RV not possible, as readiness states |
| V3 SGLT2 add-on pool | Patient-level state per month (on SGLT2, no Kerendia) (6) | Not built in NB01 (needs the HCP-patient bridge, readiness 6.1) | N/A |
| F10 Trends | 3 months vs previous 3 (6) | `RATIO_RX_CLAIMS_<category>_IN_PRIOR_3_LAST_3_MONTH`, 12 columns (cell 24), treatment categories only | Partly: no brand / rejected trends |
| Rates and shares | Computed after the join; null when denominator is 0 (5.3) | `PCT_` = feature / total of the same window, 0 (not null) when the total is 0 (Q11) | Difference: 0 instead of null (documented here, note) |
| Rx categories | 3.0 meaning kept (plan D3, config option C) | GLP-1 / DPP-IV category -> "Other- glucose mgmt"; GLP-1 and DPP-IV stay as brands (`HCP_BRANDS`) | Yes |
| Data start / end | 2023-01-01; one-month lag (5.3, 5.4) | Pull 2023-01-01..2026-09-30; last cohort c28 = Aug 2026 (lag Sep, prediction Oct) | Yes |

## 5. Data sources (readiness vs notebook)

| Source | Readiness says | Notebook uses | Rows / dates found | Match |
| --- | --- | --- | --- | --- |
| Rx pull | `full_2026_11_16_pull_rx_hcp`, 3,275,477,893 rows, 2023-01-01..2026-09-30, `NPI_NUMBER` 0 null, `SVC_DT` DATE, no `CLAIM_TYPE` | Same table via `HCP_RX_TABLE` / `read_delta` (15 of 16 columns) | 3,275,477,893; 2023-01-01..2026-09-30; 0 null NPI; no `CLAIM_TYPE` | Yes |
| Cohorts | `input_claims_cohorts`, 28 cohorts, lookback end 2024-05-01..2026-08-01 | Same (`CLAIMS_COHORT_PATH`, UC mode) | 28; offset 0; 24 / 2 / 2 split | Yes |
| Universe | `input_hcp_universe` keyed by `PROVIDER_ID`; confirm NPI mapping (O2) | Universe applied in the pull (PJ03); NB01 maps NPI -> `PROVIDER_ID` with `kerendia_nba_3_0_npi_bhid_mapping` | 294,727 providers; 3,094 output rows unmapped; 42 mapped IDs outside the universe | Open (O2, F2) |
| Patient table | Not in readiness section 4 | `pat_new_and_total_treatments` via `get_patient_table_path` (group 2.8) | Not profiled in this QC | Not checked |
| 3.0 volume | No write to the 3.0 volume | UC mode: `write_delta` stops on paths without a table name; outputs are UC tables | Output and provider tables in `<S>` | Yes |

## 6. Features made (plan vs output)

| Plan family | Expected (readiness / plan) | Output columns | Status |
| --- | --- | --- | --- |
| Totals, 2.1 treatment category, 2.2 brand | 11 categories (12 in the pull, GLP-1 / DPP-IV mapped) + 7 brands present, 4 windows | Present (e.g. `TOTAL_RX_CLAIMS_<cat>_IN_LAST_<N>_MONTH`) | PASS |
| Kerendia (X16) | +234 features | 234 columns containing `KERENDIA` | PASS |
| 2.3 rejection (V2 RJ) | Category + brand, `REJECTION_FLAG = 1` | `TOTAL_REJECTED_RX_CLAIMS_*`, `RUNNING_TOTAL_REJECTED_*` | PASS |
| 2.4 duration, 2.5 refill, 2.6 payer, 2.7 patient attributes | 3.0 groups | Present (days-supply bins, refill / new prescription, payer, age and gender) | PASS |
| 2.8 patient treatment | Active / new treatment buckets | `TOTAL_RX_CLAIMS_PATIENT_WITH_*` | PASS |
| `RUNNING_`, `PCT_`, AVG, `SGLT2_WO_INVOKANA_300MG` | Plan sections 1, 0 | `RUNNING_` 520, `PCT_` 2,052, `AVG_PATIENT_AGE*` / `AVG_TREATMENT_PER_PATIENT*`, SGLT2_WO family | PASS |
| F10 trend | 3 vs previous 3 | 12 `RATIO_..._IN_PRIOR_3_LAST_3_MONTH` | PASS (categories only) |
| V1 NBRx / time since first | NB05 | Not in NB01 | N/A (other notebook) |
| V2 reversed / paid | Needs `CLAIM_TYPE` | None | Blocked upstream (F7) |
| Total feature count | Plan 4,668; readiness 4,677 columns | 4,672 features / 4,681 columns | Doc mismatch (F6) |

## 7. Fill rate

% over all 8,088,310 output rows unless stated. No sentinel values are used by NB01 (missing = 0).

| Feature | % null | % zero | % non-zero | % sentinel | min / max | % non-zero train / test / holdout / c28 | Flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TOTAL_RX_CLAIMS_IN_LAST_1_MONTH | 0.00 | 2.83 | 97.17 | 0 | 0 / 13,827 | 97.24 / 96.92 / 96.65 / 96.59 | |
| TOTAL_RX_CLAIMS_IN_LAST_12_MONTH | 0.00 | 0.43 | 99.57 | 0 | 0 / 157,032 | 99.60 / 99.45 / 99.37 / 99.35 | |
| TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_3_MONTH | 0.00 | 88.52 | 11.48 | 0 | 0 / 2,112 | 10.99 / 13.96 / 14.72 / 14.95 | |
| TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_12_MONTH | 0.00 | 84.44 | 15.56 | 0 | 0 / 7,672 | 14.86 / 19.16 / 20.08 / 20.34 | Train vs holdout +5.22 pts |
| TOTAL_RX_CLAIMS_SGLT2_IN_LAST_12_MONTH | 0.00 | 7.13 | 92.87 | 0 | 0 / 24,967 | 92.71 / 93.88 / 93.82 / 93.81 | |
| TOTAL_RX_CLAIMS_JARDIANCE_IN_LAST_12_MONTH | 0.00 | 9.63 | 90.37 | 0 | 0 / 20,381 | 90.10 / 92.02 / 91.93 / 91.90 | |
| TOTAL_RX_CLAIMS_FARXIGA_IN_LAST_12_MONTH | 0.00 | 19.02 | 80.98 | 0 | 0 / 6,153 | 80.78 / 82.57 / 81.66 / 81.42 | |
| TOTAL_RX_CLAIMS_INVOKANA_300MG_IN_LAST_12_MONTH | 0.00 | 88.00 | 12.00 | 0 | 0 / 592 | 12.59 / 8.76 / 8.30 / 8.20 | -4.29 pts |
| TOTAL_REJECTED_RX_CLAIMS_SGLT2_IN_LAST_12_MONTH | 0.00 | 14.82 | 85.18 | 0 | 0 / 5,420 | 84.79 / 87.52 / 87.40 / 87.36 | |
| TOTAL_REJECTED_RX_CLAIMS_KERENDIA_IN_LAST_12_MONTH | 0.00 | 90.66 | 9.34 | 0 | 0 / 1,063 | 9.00 / 11.10 / 11.61 / 11.75 | |
| RUNNING_TOTAL_RX_CLAIMS | 0.00 | 0.00 | 100.00 | 0 | 1 / 395,504 | 100 / 100 / 100 / 100 | |
| RUNNING_TOTAL_RX_CLAIMS_KERENDIA | 0.00 | 80.59 | 19.41 | 0 | 0 / 14,210 | 18.27 / 25.41 / 26.80 / 27.16 | Train vs holdout +8.53 pts |
| PCT_TOTAL_RX_CLAIMS_SGLT2_IN_LAST_12_MONTH | 0.00 | 7.13 | 92.87 | 0 | 0 / 1 | 92.71 / 93.88 / 93.82 / 93.81 | |
| PCT_TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_12_MONTH | 0.00 | 84.44 | 15.56 | 0 | 0 / 1 | 14.86 / 19.16 / 20.08 / 20.34 | +5.22 pts |
| RATIO_RX_CLAIMS_SGLT2_IN_PRIOR_3_LAST_3_MONTH | 0.00 | 13.48 | 86.52 | 0 | 0 / 897 | 86.17 / 88.67 / 88.47 / 88.41 | Long tail (small denominators) |
| AVG_PATIENT_AGE_IN_LAST_12_MONTH | 0.00 | 0.46 | 99.54 | 0 | 0 / 83.6 | 99.56 / 99.45 / 99.36 / 99.34 | |
| TOTAL_RX_CLAIMS_PATIENT_WITH_1_ACTIVE_TREATMENT_IN_LAST_12_MONTH | 0.00 | 1.11 | 98.89 | 0 | 0 / 27,175 | 98.92 / 98.82 / 98.72 / 98.70 | |
| TOTAL_RX_CLAIMS_PATIENT_WITH_2_OR_3_ACTIVE_TREATMENTS_IN_LAST_12_MONTH | 0.00 | 1.61 | 98.39 | 0 | 0 / 40,822 | 98.39 / 98.43 / 98.34 / 98.32 | |

The Kerendia shift fits growing Kerendia use over time; it is a real trend, not a defect, but it changes the feature distribution between training and holdout (F5).

## 8. NBA 3.0 vs NBA 3.1 feature map

Feature-level match by exact name; the 3.1 output keeps the 3.0 names.

| NBA 3.0 feature | In 752? (SHAP rank, % SHAP) | NBA 3.1 feature | Status (preserved / replaced / dropped / new) | Reason |
| --- | --- | --- | --- | --- |
| 137 "Rx Claim-based" features (e.g. totals, brand, rejected, `PCT_`, `RUNNING_`) | Yes | Same names in NB01 output | Preserved (137 / 137) | |
| 35 "Plan Type & combination with Claims" Rx features | Yes | Same names | Preserved (35 / 35) | |
| All 172 above | Yes, best rank 14, 17.53% SHAP in total | Same names | Preserved | |
| 87 Rx x CKD stage features (`..._PATIENT_WITH_DX_GFR_STAGE_*`, `..._DX_UACR_STAGE_*`, `..._PATIENT_WITH_GFR_STAGE_*`) | Yes, best rank 35, 5.06% SHAP | Not in NB01 | Out of NB01 scope | All 87 are 3.0 sub-category "Dx CKD stage" (87 / 87); not built by NB01 (no CKD-stage input). Owner notebook to confirm (F4) |
| Kerendia family | n/a (Kerendia not in 3.0 Rx data) | 234 `*KERENDIA*` columns | New (X16) | Kerendia added to the basket |
| 6 removed treatment categories | n/a | Removed | Dropped (X17, plan update 2026-11-11) | Decided in `NBA_3_1_HCP_Features_Decisions.md` (not re-read in this QC) |
| `SGLT2_WO_INVOKANA_300MG` family | Not counted in this QC | Kept, `= SGLT2 - Invokana 300` (Q11, 12M) | Preserved | The HCP claims analysis doc recommends dropping it (R5); not verified in this QC |

## 9. HCP trace (step-by-step recompute)

Recomputed with separate SQL on `pull_rx_hcp`: E = last day of the cohort's `lookback_end_date` month; window N = `last_day(add_months(E, -N)) < SVC_DT <= E`; category = `TREATMENT_CATEGORY` with trailing spaces removed; brand = `CATEGORY`.

| Step | What |
| --- | --- |
| 1 | NPI chosen from the output (cases below); per the plan, the pull is limited to the 3.1 universe by PJ03 (not re-checked; see F2) |
| 2 | Raw rows in the pull for the NPI, `SVC_DT <= E` (= RUNNING) |
| 3 | Source filters: NPI not null (0 nulls), `SVC_DT >= 2023-01-01` (pull start) |
| 4 | `SVC_DT <= E` |
| 5 | Loaded before `PREDICTION_MONTH`: N/A (no load date) |
| 6 | Inside each window (1 / 3 / 12M) |
| 7 | Derived: Kerendia 12M, rejected SGLT2 12M, Jardiance 12M, `PCT_` Kerendia 12M |
| 8 | Output value; step 7 = step 8 |

| Case | NPI / cohort (E) | RUNNING | 1M | 3M | 12M | Kerendia 12M | Rej. SGLT2 12M | Jardiance 12M | Fills on E | Match |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| High volume; also highest rejected SGLT2 | 1619082625 / c28 (2026-08-31) | 395,504 | 4,961 | 15,054 | 107,533 | 205 | 3,606 | 13,434 | 199 | Yes |
| Kerendia top writer | 1588633135 / c28 | 113,797 | 932 | 2,873 | 32,499 | 5,082 (`PCT_` 0.156374 = 5,082 / 32,499) | 1,829 | 3,245 | 35 | Yes |
| No fills in 12M | 1003019647 / c28 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Yes |
| Window edge (fills on 08-31 and 09-01) | 1003000126 / c28 | 745 | 56 | 106 | 360 | 0 | 3 | 19 | 6 (in); 09-01 fills out | Yes |
| Training cohort | 1003003609 / c1 (2024-05-31) | 1,820 | 133 | 345 | 1,282 | 16 | 28 | 11 | 11 | Yes |

## 10. Findings and actions

| # | Finding | Severity (blocker / fix / doc / note) | Action / owner | Status |
| --- | --- | --- | --- | --- |
| F1 | Universe coverage is checked on the provider output `..._hcp_provider_claim_rx_monthly_cohort` (cell 34), because the main output has only `NPI_NUMBER`. 8,085,481 of 8,252,356 universe x 28 keys have a row, 0 duplicates. All 166,875 missing keys are by design (cell 21): 159,231 are cohorts before the provider's first Rx history, 7,644 are the 273 universe providers with no Rx in the pull (x 28); 0 gaps after a provider first appears | note | Training set: left-join features to the universe x cohort spine and fill 0 for missing keys (no Rx history = 0 claims) / NBA team | Closed (by design) |
| F2 | Provider output: 3,094 rows with null `PROVIDER_ID` (NPI not in `kerendia_nba_3_0_npi_bhid_mapping`); 42 mapped `PROVIDER_ID` (960 rows) not in the universe | fix | Close readiness open point O2: drop or remap null-ID rows, check the 42 IDs against the 3.1 universe / data engineering | Open |
| F3 | 3.0 vs 3.1 (Aug 2026, 221,438 common NPIs): totals +10.8% (12M), +14.3% (1M), SGLT2 +19.5%, rejected SGLT2 +44.5%; Spearman 0.96-0.99 | fix (explain) | Break down the difference by source (Rx basket vs `Rx_01_new`, claim key H4, universe) for the common NPIs / NB01 developer | Open |
| F4 | 87 Rx x CKD-stage 3.0 features (5.06% SHAP) are not produced by NB01 | note | Confirm which 3.1 notebook builds them, or record them as dropped / feature-engineering owner | Open |
| F5 | Drift vs Training: Kerendia 12M claims +33.7% (test) / +39.2% (holdout); Kerendia non-zero share +5.2 pts (12M) and +8.5 pts (RUNNING) | note | NBA team sign-off (expected uptake trend); consider share / trend features over raw counts in selection | Open |
| F6 | Feature count in the docs does not match the output: plan 4,668, readiness 4,677 columns; output 4,672 features / 4,681 columns | doc | Update plan header and readiness section 1 / Phase 5 with 4,672 / 4,681 / NB01 developer | Open |
| F7 | No `CLAIM_TYPE` in the pull: reversed and paid-only claims cannot be split (V1 paid-only, V2 RV) | fix (upstream) | PJ03 Step 4d to add `CLAIM_TYPE` / `CLAIM_STATUS` (readiness R1) / PJ03 owner | Open (known, readiness) |
| F8 | `PCT_` is 0 when the window total is 0; readiness 5.3 asks for null | note | Decide for Track C only; NB01 keeps 3.0 behaviour | Open |
| F9 | No load timestamp in the pull, so the late-load (point-in-time on load date) check cannot be run | note | Covered by the readiness data-lag rule (5.4) | Open |

## 11. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 11 / 14 (Q1-Q11 PASS; Q13 FAIL, doc only; Q12 and Q14 OPEN) |
| QC by / date | Genie Code for Saurabh Modi / 2026-11-27 |
| O5 and drift review (NBA team) / date | |
| Reviewed by / date | |
| Next | Close F2, F3, F6; NBA-team sign-off on F5; then QC of NB02 (Dx claims) |
