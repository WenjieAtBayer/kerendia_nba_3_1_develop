# QC 02: Copay features, NBA 3.1

**QC status:** DONE, 24 Nov 2026 (claim type 2 of 2)  
**Verdict:** PASS with actions. The features are correct: the HCP trace matched 184 of 184 values (8 cases x 23 features, C6 rebuilt from the FTP claims table), and 19 independent invariants found 0 violations. 1 fix, 3 documentation items and 5 notes are open (section 10).  
**QC run:** 24 Nov 2026, serverless, on the output written 2026-11-24 (`PULL_DT`) by the claims-cohort run of `copay_feature`. The notebook was not re-run during QC. Numbers marked (nb) come from the notebook's own run log, not re-run here.

How to use: see `00_qc_template.md`. Rule source = `60_ftp_copay_nba_3_1_readiness_plan.md` ("readiness"). `<V31>` = `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume`.

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `04_Promotional_Features/FTP_and_Copay/copay_feature` (15 cells) |
| Rule file | `60_ftp_copay_nba_3_1_readiness_plan.md` |
| Source table | `market_access.kerendia_copay_claims` (3 `DF` program groups) |
| Second input | FTP output `FTP_HAS_ANY_12M` (C6 only) |
| Universe | `<V31>/HCP_Universe_without_call_hcps`: 294,727 HCPs |
| Cohorts | `<V31>/cohorts/claims/cohorts.parquet`: family `claims`, offset 0, c1 to c28 |
| Mapping | 3.0 volume `ops_pipeline/query_output/kerendia_nba_3_0_npi_bhid_mapping` (read only) |
| Output | `<V31>/hcp_level_model/dev_pipeline/notebook_output/market_access_nba_3_1/kerendia_nba_3_1_hcp_model_copay_features`: 8,252,328 rows after the F1 rerun (8,252,356 when QC ran) x 23 features (+ 6 keys, `PULL_DT`) |
| Expected grain | One row per `PROVIDER_ID` x `COHORT` = 294,727 x 28, same keys as the FTP output |
| NBA 3.0 counterpart | 3.0 ops output `kerendia_nba_3_hcp_model_copay_features_for_inference` (58 months, latest `SVC_DT_M` 2026-10-01) |
| NBA 3.0 final model | `Final NBA 3.0 Modeling Features.xlsx` (752 features) |

## 2. QC checklist

| # | Check | Pass when | Status |
| --- | --- | --- | --- |
| Q1 | HCP universe | Output = universe x 28, 0 duplicates, 0 outside | PASS (1 fix: `PROVIDER_ID = '0'`) |
| Q2 | Right cohorts (claims, 3.1 volume) | 0 mismatches | PASS |
| Q3 | Windows and point-in-time | No claim after E or loaded late contributes | PASS |
| Q4 | Data sources vs readiness | Same sources, differences explained | PASS (2 notes) |
| Q5 | All features made | 0 missing without a reason | PASS |
| Q6 | Business rules | Match or documented difference | PASS (3 documented differences) |
| Q7 | Fill rate | No unexpected nulls; flags listed | PASS (4 features > 99.5% zero) |
| Q8 | NBA 3.0 752 coverage | 0 skipped | PASS (0 copay features in the 752) |
| Q9 | Preserved vs new | All labelled | PASS (all 23 new) |
| Q10 | HCP trace | Output = recompute | PASS (184 / 184) |
| Q11 | Invariants | 0 violations | PASS (19 / 19) |
| Q12 | NBA 3.0 output comparison | Differences explained | PASS (not comparable value by value) |
| Q13 | Reproducibility and docs | No stale text that changes meaning | PASS (readiness items in section 10) |

## 3. Evidence log

| # | Result (numbers) | Notes |
| --- | --- | --- |
| Q1 | Output 8,252,356 rows, 294,727 distinct HCPs, 294,727 per cohort (min = max), 0 duplicate keys, 0 HCPs outside the universe; 0 `HCP_COHORT_ID` not in the FTP output | `PROVIDER_ID = '0'`: 28 rows, 0 fills (F1, same as FTP) |
| Q2 | 28 cohorts; output vs cohort file on `COHORT` / `DATASET` / `PREDICTION_MONTH` / `SVC_DT`: 0 mismatches; `SVC_DT` not on the 1st: 0 | Config `COHORT_PATH` = claims file |
| Q3 | E = last day of lookback end month; `INSERT_TS < PREDICTION_MONTH`; trim 0. Trace: fill on 2026-08-31 counted (case 3a, recency 0); fills on 2026-09-01 not counted (case 3b: 49 raw -> 44 <= E); a claim loaded after 2026-10-01 dropped (case 4: 20 -> 19). Invariant flag = (recency < window days): 0 | (nb) O4: 4 of 1,324 c28 fills in the last 14 days loaded late (0.3%) |
| Q4 | Section 5 | Same universe / mapping notes as FTP |
| Q5 | Section 6: 15 core (C1-C6) + 8 extended = 23 = config `core_columns()` + `C6_COLS` + `EXT_COLS`; types int / bigint / double | X4 / X5 not built (privacy, V7) |
| Q6 | Section 4 | |
| Q7 | Section 7: 0 nulls in all 23; 0 constant; train-vs-holdout non-zero share differs by < 0.4 points | Copay coverage grows over time: HCPs with a 12M fill 1.30% train -> 1.67% holdout |
| Q8 | Search of the 752 for `COPAY`, `CPY`, `PTNT`, `OOP`, `AFFORD`: 0 matches | The 3.0 copay features were not in the final model |
| Q9 | Section 8: 0 preserved, 23 new; 3.0 copay columns dropped or replaced | |
| Q10 | Section 9: 8 HCP x cohort cases, 23 features each, recomputed in pandas from the copay and FTP source tables: 0 mismatches | |
| Q11 | 0 violations each: nested windows (fills, new-Rx); new-Rx <= fills; flag = (12M > 0); cap = min(12M, 53); band edges; flag = (recency < window days); 1M fill => recency <= 30; C5 zero when no fill; C5 avg in [0, 2000]; C5 share in [0, 1]; share > 0 => avg > 0; share = 1 => avg > 300; C6 <= copay flag; extended zero when no fill; shares in [0, 1]; pharmacies <= fills; fills per Rx >= 1; trend within [-prior 3M, 3M]. C6 = `FTP_HAS_ANY_12M` x `CPY_HAS_ANY_12M` for all 8,252,356 rows: 0 mismatches. Training p99 of active 12M fills = 53 = cap | |
| Q12 | 3.0 latest month (`SVC_DT_M` 2026-10-01, 9,313 HCPs) vs 3.1 c28 (E 2026-08-31): HCPs > 0 1M 237 vs 1,964, 3M 1,265 vs 3,099, 6M 2,529 vs 3,885; Spearman (rows with either > 0) -0.299 / -0.097 / 0.213 | Window anchors differ by about 1 month and the 3.0 counting rule was not traced, so values are not expected to agree. 3.1 is also checked against the S4 assessment instead (next row) |
| Q12b | (nb) S4: c28 output 4,988 HCPs / 32,045 fills / 1,053 both vs assessment 4,992 / 32,057 / 1,054 (max -0.095%, tolerance 0.5%) | Gap = 12 claims loaded after 2026-10-01 |
| Q13 | Full universe run, `PULL_DT` 2026-11-24, QC log `qc/copay_feature_checks` written; (nb) second build identical (0 differing rows) | Same stale-folder note as FTP F5 |

## 4. Business rules (readiness vs notebook)

| Rule | Readiness says | Notebook does | Match |
| --- | --- | --- | --- |
| Source | UC `kerendia_copay_claims` (D1) | Same | Yes |
| Programs | 3 `DF` groups | Config `PROGRAM_GROUPS`; source has 3 groups | Yes |
| Claim grain | One count per `ORGN_CLM_AUTH_NUM` | 106,721 rows = 106,721 claims | Yes |
| Feature date | `RX_FILL_DATE`; written date for X6 only (D2) | Same | Yes |
| Point-in-time | `INSERT_TS <= cutoff`, trim 14 days (D4) | `INSERT_TS < PREDICTION_MONTH`, trim 0 (DEC-C02, same as FTP DEC-F02 / F03) | Difference, documented (F2) |
| Windows | 1 / 3 / 6 / 12M (D3) | Same | Yes |
| Join | `PROVIDER_ID -> NPI -> PRSC_NPI` | Same; 43 null-NPI claims excluded | Yes |
| Full universe / zero = zero | Every HCP x cohort; 0 = no fill | Same; 0 nulls | Yes (except `'0'`, F1) |
| Skew | Cap at p99 (example 45) + band (D5) | Cap 53 (training p99, DEC-C01) | Value differs, documented (F3) |
| Recency | Sentinel | 9999 | Yes |
| Money (C5) | `NET_PTNT_COPAY` only; share > 300 USD (principle 5) | `NET_PTNT_COPAY` in [0, 2000] only (DEC-C03); 0 when no 12M fill | Yes + range rule (F6) |
| Overlap (C6) | HCP with FTP and copay fills in 12M | FTP flag from FTP output x copay flag (DEC-C04) | Yes |
| Leakage | Clawback flags, `MDM_SPECIALTY` excluded | In `EXCLUDED`, not used | Yes |
| Naming | `CPY_` prefix; no `TOTAL_RX_COPAY_*` reuse | Same (`FTP_CPY_BOTH_12M` for C6) | Yes |
| Dropped from 3.0 | `PCT_*`, running total | Not built | Yes |
| Keep / drop | Experiments (S6, G2) | (nb) E1 +0.0002 / +0.0004 AUC, E5 C5 -0.0001 / +0.0000: DROP; all columns written (DEC-C06) | Yes (F7) |

## 5. Data sources (readiness vs notebook)

| Source | Readiness says | Notebook uses | Rows / dates found | Match |
| --- | --- | --- | --- | --- |
| Copay claims | `market_access.kerendia_copay_claims`, 3 DF | Same | 106,721 rows; fill 2021-08-04 to 2026-11-13; `REFRESH_TS` 2026-11-23; max `INSERT_TS` 2026-11-15; 43 null NPI; 0 null copay; 265 copay values outside [0, 2000] | Yes |
| FTP claims / output | C6 | FTP output flag (QC recomputed it from `kerendia_ftp_claims`) | as QC 01 | Yes |
| Universe | `kerendia_nba_3_1.input_hcp_universe` | `<V31>/HCP_Universe_without_call_hcps` | 294,727 | Same count, other path name |
| Cohorts | claims cohorts | `<V31>/cohorts/claims/cohorts.parquet` | 28, claims, offset 0 | Yes |
| Mapping | `00_cohort_config` default | Same path | as QC 01 | Yes |
| Snapshot | O2 only | O2 only | 1 partition (2026-11-01) | Yes |
| Experiment inputs | E0 = 3.1 model without copay | Proxy prior writing + monthly Rx (same as FTP) | not re-profiled | Proxy, documented |
| Writes | 3.1 volume only | `<V31>/.../market_access_nba_3_1` | - | Yes |

## 6. Features made (plan vs output)

| Plan family | Output columns | Status |
| --- | --- | --- |
| C1 has any | `CPY_HAS_ANY_12M` | Made |
| C2 fills | `CPY_FILLS_1M/3M/6M/12M`, `CPY_FILLS_12M_CAP`, `CPY_FILLS_12M_BAND` | Made (6) |
| C3 new-Rx | `CPY_NEWRX_FILLS_1M/3M/6M/12M` | Made |
| C4 recency | `CPY_DAYS_SINCE_LAST_FILL` | Made |
| C5 affordability | `CPY_AVG_COPAY_BEFORE_CARD_12M`, `CPY_COPAY_GT300_SHARE_12M` | Made |
| C6 overlap | `FTP_CPY_BOTH_12M` | Made |
| X1 persistence | `CPY_REFILL_SHARE_12M`, `CPY_FILLS_PER_RX_12M` | Made |
| X2 dose mix | `CPY_HIGH_DOSE_SHARE_12M` | Made |
| X3 patient-days | `CPY_DAYS_SUPPLY_12M`, `CPY_90DAY_SHARE_12M` | Made (DEC-C05) |
| X4 / X5 | - | Not built (privacy / V7 open) |
| X6 / X7 / X8 | `CPY_AVG_WRITTEN_TO_FILL_DAYS_12M`, `CPY_DISTINCT_PHARMACIES_12M`, `CPY_FILLS_3M_VS_PRIOR_3M` | Made |

## 7. Fill rate

% over 8,252,356 rows. 0 nulls in every feature.

| Feature | % zero | % non-zero | min / max | % non-zero train / test / holdout / c28 | Flag |
| --- | --- | --- | --- | --- | --- |
| `CPY_HAS_ANY_12M` | 98.650 | 1.350 | 0 / 1 | 1.301 / 1.611 / 1.674 / 1.692 | |
| `CPY_FILLS_1M` | 99.457 | 0.543 | 0 / 55 | 0.523 / 0.654 / 0.672 / 0.666 | |
| `CPY_FILLS_3M` | 99.185 | 0.815 | 0 / 160 | 0.779 / 1.007 / 1.046 / 1.051 | |
| `CPY_FILLS_6M` | 98.968 | 1.032 | 0 / 299 | 0.992 / 1.251 / 1.296 / 1.318 | |
| `CPY_FILLS_12M` | 98.650 | 1.350 | 0 / 517 | as has-any | |
| `CPY_FILLS_12M_CAP` | 98.650 | 1.350 | 0 / 53 | as has-any | |
| `CPY_FILLS_12M_BAND` | 98.650 | 1.350 | 0 / 5 | as has-any | |
| `CPY_NEWRX_FILLS_1M` | 99.800 | 0.200 | 0 / 18 | 0.195 / 0.231 / 0.233 / 0.225 | > 99.5% zero |
| `CPY_NEWRX_FILLS_3M` | 99.534 | 0.466 | 0 / 38 | 0.448 / 0.582 / 0.567 / 0.568 | > 99.5% zero |
| `CPY_NEWRX_FILLS_6M` | 99.271 | 0.729 | 0 / 59 | 0.697 / 0.915 / 0.928 / 0.933 | |
| `CPY_NEWRX_FILLS_12M` | 98.933 | 1.067 | 0 / 86 | 1.024 / 1.297 / 1.351 / 1.363 | |
| `CPY_DAYS_SINCE_LAST_FILL` | 0.026 | 2.145 (+ 97.829 sentinel) | 0 / 9999 | 2.029 / 2.783 / 2.894 / 2.917 | sentinel |
| `CPY_AVG_COPAY_BEFORE_CARD_12M` | 98.670 | 1.330 | 0 / 1,998.82 | 1.284 / 1.579 / 1.638 / 1.656 | 0 also for active HCPs with only invalid / zero copays (F6) |
| `CPY_COPAY_GT300_SHARE_12M` | 99.166 | 0.834 | 0 / 1 | 0.808 / 0.971 / 1.009 / 1.017 | |
| `FTP_CPY_BOTH_12M` | 99.633 | 0.367 | 0 / 1 | 0.370 / 0.342 / 0.356 / 0.357 | > 99.5% zero |
| `CPY_REFILL_SHARE_12M` | 98.931 | 1.069 | 0 / 1 | 1.030 / 1.277 / 1.334 / 1.345 | |
| `CPY_FILLS_PER_RX_12M` | 98.650 | 1.350 | 0 / 24 | as has-any | |
| `CPY_HIGH_DOSE_SHARE_12M` | 99.395 | 0.605 | 0 / 1 | 0.578 / 0.758 / 0.787 / 0.796 | |
| `CPY_90DAY_SHARE_12M` | 99.553 | 0.447 | 0 / 1 | 0.415 / 0.621 / 0.665 / 0.676 | > 99.5% zero |
| `CPY_DAYS_SUPPLY_12M` | 98.650 | 1.350 | 0 / 15,510 | as has-any | |
| `CPY_AVG_WRITTEN_TO_FILL_DAYS_12M` | 98.725 | 1.275 | 0 / 449 | 1.229 / 1.522 / 1.581 / 1.597 | |
| `CPY_DISTINCT_PHARMACIES_12M` | 98.650 | 1.350 | 0 / 15 | as has-any | |
| `CPY_FILLS_3M_VS_PRIOR_3M` | 99.149 | 0.851 | -43 / 117 | 0.824 / 0.993 / 1.031 / 1.058 | |

## 8. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature (3.0 copay output) | In 752? | NBA 3.1 feature | Status | Reason |
| --- | --- | --- | --- | --- |
| `TOTAL_RX_COPAY_IN_LAST_1/3/6_MONTH` | No | `CPY_FILLS_1M/3M/6M` | replaced (not in 752) | fill date, claim grain, new name (D6) |
| `TOTAL_RX_COPAY_IN_LAST_2/4/5_MONTH` | No | - | dropped | not in D3 windows |
| `TOTAL_RX_COPAY`, `RUNNING_TOTAL_RX_COPAY`, `PCT_*` (7) | No | - | dropped | readiness drop list |

Summary: 0 copay features in the 752, so none is preserved; all 23 3.1 features are new to the model (incl. the first affordability features C5 and the overlap flag C6). None is on the model-recommended list after G2 (F7).

## 9. HCP trace (step-by-step recompute)

C6 recomputed from `kerendia_ftp_claims` with the same rules (not read from the FTP output).

| Case | PROVIDER_ID | Cohort | NPIs | 2 raw | 3 after filters | 4 fill <= E | 5 loaded < pred. month | 6 in 12M | valid copay 12M | FTP 12M | Values / mismatches |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 high volume | 24976916 | c28 | 1 | 1,049 | 1,049 | 998 | 998 | 308 | 308 | 1 | 23 / 0 |
| 2 copay > 2000 in window | 8053013 | c28 | 1 | 2 | 2 | 2 | 2 | 1 | 0 | 0 | 23 / 0 |
| 3a fill on last day (in) | 7003639 | c28 | 1 | 22 | 22 | 16 | 16 | 13 | 13 | 0 | 23 / 0 |
| 3b fill on 1st of next month (out) | 7177717 | c28 | 1 | 49 | 49 | 44 | 44 | 24 | 24 | 0 | 23 / 0 |
| 4 loaded after prediction month | 11385738 | c28 | 1 | 22 | 22 | 20 | 19 | 15 | 15 | 0 | 23 / 0 |
| 5 no copay fill | 8181357 | c28 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 23 / 0 |
| 6 90-day + refill + FTP overlap | 10197782 | c28 | 1 | 19 | 19 | 19 | 19 | 9 | 9 | 1 | 23 / 0 |
| 7 training cohort | 24976916 | c5 | 1 | 1,049 | 1,049 | 308 | 308 | 299 | 299 | 1 | 23 / 0 |

Derived values (recompute = output in every cell):

| Case | 12M window | Last fill | 1M / 3M / 12M | New-Rx 12M | Recency | Cap | Avg copay | > 300 share | Both | Refill share | 90-day share | 3M vs prior |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | (2025-08-31, 2026-08-31] | 2026-08-31 | 20 / 74 / 308 | 40 | 0 | 53 | 610.47 | 0.8734 | 1 | 0.8701 | 0 | -6 |
| 2 | same | 2026-01-26 | 0 / 0 / 1 | 1 | 217 | 1 | 0.00 | 0 | 0 | 0 | 1 | 0 |
| 3a | same | 2026-08-31 | 2 / 7 / 13 | 6 | 0 | 13 | 198.08 | 0.0769 | 0 | 0.5385 | 0 | 3 |
| 3b | same | 2026-08-20 | 3 / 8 / 24 | 9 | 11 | 24 | 152.71 | 0.0417 | 0 | 0.6250 | 0.25 | 4 |
| 4 | same | 2026-07-20 | 0 / 2 / 15 | 2 | 42 | 15 | 87.33 | 0 | 0 | 0.8667 | 0 | -4 |
| 5 | same | none | 0 / 0 / 0 | 0 | 9999 | 0 | 0.00 | 0 | 0 | 0 | 0 | 0 |
| 6 | same | 2026-06-06 | 0 / 1 / 9 | 1 | 86 | 9 | 524.13 | 0.4444 | 1 | 0.8889 | 0.2222 | -2 |
| 7 | (2023-09-30, 2024-09-30] | 2024-09-30 | 55 / 160 / 299 | 77 | 0 | 53 | 579.41 | 0.8930 | 1 | 0.7425 | 0 | 65 |

Case 2 shows the C5 range rule: one 12M fill with copay 2,235.01 USD counts as a fill but gives avg copay 0. No universe HCP sharing an NPI has a copay fill in the c28 window, so DEC-F06 could not be traced.

## 10. Findings and actions

| # | Finding | Severity | Action / owner | Status |
| --- | --- | --- | --- | --- |
| F1 | `PROVIDER_ID = '0'` in the universe: 28 output rows, all 0 (same as QC 01 F1) | fix | Fixed in code 24 Nov 2026 (config cell, same filter as `ftp_feature`); expected 294,726 HCPs / 8,252,328 rows. Rerun 24 Nov 2026 after `ftp_feature`: output 8,252,328 rows, 294,726 HCPs, 0 `'0'` rows, keys identical to the FTP output; G1 15 / 15 PASS; S4 c28 4,988 / 32,045 / 1,053 (unchanged); gates unchanged (G3 FAIL) | FIXED |
| F2 | Readiness D4 (14-day trim, `INSERT_TS <= cutoff`) differs from the claims-cohort rule (trim 0, `INSERT_TS < PREDICTION_MONTH`) | doc | Update readiness D4 (shared with QC 01 F2) | OPEN |
| F3 | Readiness D5 copay cap example 45; measured 53 | doc | Update readiness | OPEN |
| F4 | Readiness D6 combined notebook vs separate notebooks; old `23_` output in the folder | doc | As QC 01 F5 | OPEN |
| F5 | C6 depends on the FTP output: `copay_feature` must run after `ftp_feature` | note | Order the tasks in the job | OPEN |
| F6 | C5 = 0 for both "no fill" and "fills but no valid copay" (and true 0 USD copays): avg copay non-zero 1.330% vs has-any 1.350% | note | Keep (has-any separates no fill); document; consider a valid-copay count if C5 is kept | OPEN |
| F7 | G2 = DROP on the proxy model (E1 +0.0002 / +0.0004); no copay feature was in the 3.0 752 | note | Modelling to confirm on the full 3.1 model; Q9 | OPEN |
| F8 | 4 features > 99.5% zero (1M / 3M new-Rx, C6, 90-day share); coverage grows 1.30% -> 1.67% from train to holdout | note | Feature selection; watch for drift | OPEN |
| F9 | G3 fails: O2 / O5 open, no job; copay meaning of `OTHR_CVRG_CD` 08 / 03 unknown (V7, X5) | note | Market access team (Q2, Q7, Q8) | OPEN |

## 11. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 13 / 13 (with the actions above) |
| QC by / date | Genie Code for Wenjie Chen, 24 Nov 2026 |
| Reviewed by / date | |
| Next | Fix F1 in both notebooks; readiness doc updates (F2-F4) |
