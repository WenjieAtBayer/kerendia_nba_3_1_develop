# QC 05: Samples features, NBA 3.1

**QC status:** DONE, 20 Nov 2026 (channel 5 of 6), redone from the start  
**Verdict:** PASS with actions. 11 / 13 pass; Q12 OPEN (notebook 17 still reads the market access table), Q13 FAIL (stale docs). Output is correct for the notebook's rules on the data at run time; 29 features, not the 9 this plan expected.  
**QC run:** 20 Nov 2026, serverless, read-only on the output then in place. Q1 to Q13 below describe that output.

**Re-run, 20 Nov 2026 (after QC, to pick up source changes).** Notebook cells 2 to 17 and 20 run; all succeeded. `field_sample_line` 278,525 lines (278,527 raw, 2 exact duplicates, 11 without BHID); latest order date 2026-11-13. Year 2 received 442,923 units / 20,225 doctors vs `22_` 449,246 / 20,270 (-1.41% / -0.22%), equal to the Snowflake figure in Q11. Output 8,252,328 rows, 36 columns (29 features), 0 duplicate keys, 0 nulls; cell 13 29 / 29 rules pass; QC's 36 checks 0 violations; cell 15 recompute 8 / 8 (c24). Only c23 to c28 changed: received units 12M c23 264,909 (was 273,773), c24 271,557 (283,525), c25 291,348 (303,316), c26 311,228 (323,196), c27 347,411 (359,379), c28 380,699 (392,667); HCPs with 40 mg 12M c28 2,160 (2,221); total received units 12M over all cohorts 12,267,481 (12,336,185). Appendix B shows the pre-re-run values.

**Re-run with the 21-day settling rule, 20 Nov 2026 (user request; supersedes the re-run above).** Cell 4 `SETTLE_DAYS = 0` changed to `21` (readiness X1 / `22_` R7); the optional settling-period request feature stays off (`INCLUDE_REQUEST_FEATURE = False`). Cells 2 to 17 and 20 run; all succeeded. `SAMPLE_CUTOFF_DATE` = `LOOKBACK_END_DATE` - 21 on every row (c1 2024-05-27, c28 2026-08-27); all windows (received, pending, failed, 40 mg, 10 / 20 mg) now end at the cutoff. Output 8,252,328 rows, 36 columns (29 features), 0 duplicate `HCP_COHORT_ID`, 0 nulls; cell 13 29 / 29 rules pass; cell 15 recompute 8 / 8 (c24). Year 2 line totals (cell 8, by order date) unchanged: 442,923 received units. Received units 12M: c1 458,657 / 21,489 HCPs, c16 489,846, c24 264,325 / 12,834, c25 278,879, c26 296,498, c27 313,801, c28 355,089 / 17,226 (was 380,699 without settling). 40 mg 12M starts at c16 (cutoff 2025-08-27; 344 HCPs) and reaches 2,121 HCPs at c28. Q12 market access comparison (cell 16, same cutoffs): market access / NBA 3.1 units ratio 0.35 (c1) rising to 0.998 (c12, c13), then falling to 0.424 (c24), 0.261 (c25), 0.124 (c26), 0.048 (c27), 0.055 (c28); HCPs 1,537 vs 17,226 at c28. The market access table misses legacy lines in early cohorts and `aoc_received__c` lines from Aug 2025, so notebook 17 (market access only) and this block measure different things; Q12 stays OPEN until notebook 17 either reads `field_sample_line` or drops sample features.

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `personal_promotional_features/Samples/samples_feature` (20 cells) |
| Client summary | `Samples/samples_feature_nba_3_1_client_summary.md` |
| Readiness file | `40_field_activity_nba_3_1_readiness_plan.md`: Phase 0 V5, Phase 4 X1; `22_samples_reconciliation_call_vs_shipped_dropped_2024_2026.md` |
| Output | `kerendia_nba_3_1_volume/notebook_output/field_activity_nba_3_1/kerendia_nba_3_1_hcp_model_field_sample_features.parquet` |
| Universe / cohorts | `HCP_Universe_without_call_hcps/` x `cohorts/promotional/cohorts.parquet` |
| Expected shape | 9 features + keys, rows = universe x 28 (plan). **Actual: 29 features + 7 keys (36 columns)**, see Q3 |
| NBA 3.0 counterpart | `17_promotional_features_samples` (54 features, 9 x 1 to 6M), market access table `ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER` |
| NBA 3.0 final model | MLflow run `f583bcbc9d56477fae983d44c16f8c70`, 752 features, `Shap_Importances.csv` |

## 2. QC checklist

| # | Check | How | Pass when | Status |
| --- | --- | --- | --- | --- |
| Q1 | HCP universe | Distinct PROVIDER_ID vs universe; rows; duplicates; extra HCPs; placeholder `0` (no exclude setting in this notebook, other blocks remove it) | Same HCP set; `0` handled the same as other blocks | PASS |
| Q2 | Cohorts and windows | Lookback ends; window days; `SAMPLE_CUTOFF_DATE` = lookback end; no order after it | All match | PASS |
| Q3 | All features made | Columns vs config vs readiness X1 | 9 features; `SMPL_REQ_CALLS_LAST_21D` absent | PASS (29 features; extras to agree) |
| Q4 | Business rules | Fill section 4 | All match or difference agreed | PASS (4 differences to agree) |
| Q5 | Data sources | Notebook: `FACT_CALL_SAMPLE`, `MAP_CUSTOMER_XREF`; readiness: one source, `FACT_CALL_SAMPLE` with explicit status map | Same; market access table not used | PASS |
| Q6 | Fill rate | % null, % zero, % non-zero per feature, per cohort | 40 mg features 0 before c15 / c16 (40 mg since Aug 2025); dip around 28 Jul to 4 Aug 2025 explained | PASS (Q-S7 cause open) |
| Q7 | NBA 3.0 model coverage | Sample features in the 752 with SHAP rank | Mapped or dropped with reason | PASS |
| Q8 | Preserved vs new | Fill section 5 | Every feature labelled | PASS |
| Q9 | HCP trace | Section 6, at least 5 HCPs | Final value = output | PASS (141 / 145 vs today; 4 explained) |
| Q10 | Invariants | Nested windows; received units >= sample calls when calls > 0; 40 mg <= total | 0 violations | PASS |
| Q11 | Reconciliation | Received units by year vs `22_` | Year 2 received far above market access table (which holds about 13%) | PASS |
| Q12 | Cross-block | Samples counted only here (S3); market access block uses the same logic or this output | Agreed with block owner | OPEN |
| Q13 | Reproducibility and docs | Same schema on re-run; summary current | No stale text | FAIL |

## 3. Evidence log

| # | Result (numbers) | Where (cell / query) | Notes |
| --- | --- | --- | --- |
| Q1 | 8,252,328 rows = 294,726 HCPs x 28; every cohort 294,726 rows; 0 duplicate (`PROVIDER_ID`, `COHORT_ID`) and 0 duplicate `HCP_COHORT_ID`; `HCP_COHORT_ID` = `PROVIDER_ID_COHORT_ID` on all rows; 0 HCPs outside the universe; universe has 294,727 IDs, only `0` missing from output (cell 5 filter, same result as other blocks) | QC session; cell 5 | |
| Q2 | 28 cohorts; `DATASET`, `PREDICTION_MONTH`, `LOOKBACK_END_DATE` match cohorts.parquet (0 mismatches); `SAMPLE_CUTOFF_DATE` = `LOOKBACK_END_DATE` on all 28 (`SETTLE_DAYS = 0`). Windows 3 / 6 / 12M = 91 / 182 / 365 days, order date in (cutoff - days, cutoff]; cell 10 asserts no line after the cutoff | QC session; cells 4, 10 | |
| Q3 | 29 features in config order, all int, 0 nulls in any column; `SMPL_REQ_CALLS_LAST_21D` absent (`INCLUDE_REQUEST_FEATURE = False`). Beyond the 9 planned: 6 strength features `SMPL_{10,20}MG_RCVD_UNITS_{3,6,12}M` and 14 pending / failed features `SMPL_{PENDING,FAILED}_{UNITS,CALLS}_{3,6,12}M`, `SMPL_DAYS_SINCE_LAST_{PENDING,FAILED}` (added 11 Nov, cell 18) | QC session; cell 4 | Plan said 9 |
| Q4 | Section 4 | Cells 4, 7; readiness lines 109, 177, 229 | |
| Q5 | `FACT_CALL_SAMPLE` (`SYS_DELETE_FLAG = '0'`, BRC 10 / 20 / 40 mg and legacy `Kerendia 10mg / 20mg`, from 2023-01-01) left join `MAP_CUSTOMER_XREF`; exact duplicates dropped; one row per `CALL_SMPL_ID` asserted; unmapped status stops the run. Market access table not read; `MARKET_ACCESS_STATUSES` used only in the comparison cell 16 | Cells 6, 7, 16 | |
| Q6 | 0 nulls; fill in appendix A. Received 12M: 7.29% of HCPs at c1, 4.47% at c23 (low), 6.23% at c28. 40 mg: 0 HCPs c1 to c14, 64 at c15, 485 at c16, 1,649 at c24, 2,221 at c28. Dip: received units 6,363 to 11,415 a week in July 2025, 75 (week of 28 Jul) and 105 (4 Aug), then 3,194 (11 Aug) and 9,674 (18 Aug). Received 3M units: 114,287 to 153,476 in c1 to c14, 39,517 to 73,212 in c16 to c23, 131,033 to 163,721 in c25 to c28. Pending features non-zero on <= 0.02% of rows; failed 0.07 to 0.27% | QC session | Appendix A, B |
| Q7 | 10 sample features in the 752, 0.386% of total SHAP; best `TOTAL_OVERALL_SAMPLE_IN_LAST_6_MONTH` (rank 179, 0.145%) and `TOTAL_SAMPLE_DROPPED_IN_LAST_6_MONTH` (218, 0.120%); others ranks 450 to 749 | `Shap_Importances.csv`; name search `SAMPL` / `SMPL` | |
| Q8 | Section 5: all 10 replaced, 0 dropped without reason | | |
| Q9 | 5 HCPs x 29 = 145 values recomputed from raw `FACT_CALL_SAMPLE` today: 141 match. The 4 mismatches (case 5 failed units / calls 6M and 12M, output +10 units / +1 call) are line `V68000000052094` (`rejected__c`, 10 units): present in the line file, no longer in `FACT_CALL_SAMPLE`. It is the only removed line across the 5 traced BHIDs, so all 145 agree with the data the notebook read | QC session | Section 6 |
| Q10 | 0 violations on 36 checks: nested 3 <= 6 <= 12M for received, pending, failed (units and calls) and 10 / 20 mg units; units > 0 iff calls > 0 (3 categories x 3 windows); recency 999 iff no 12M calls and in [0, 364] otherwise (3 categories); received units >= calls; 10 + 20 mg <= total (3 windows) and = total at 12M when no 40 mg; 40 mg 6M <= 12M, only 0 / 1, implies a 12M received call, 0 when cutoff < 2025-08-01; recency < 91 iff 3M calls > 0; no negatives. Cell 13 runs its own invariant set at run time | QC session; cell 13 | |
| Q11 | Line file, Year 2 (Nov 2025 to Oct 2026) received BRC with BHID: 454,073 units / 20,534 doctors vs `22_` 449,246 / 20,270 (+1.07% / +1.30%, within 3%). By status: `aoc_received__c` 395,214, `Delivered_vod` 58,859. Market access status rule gives 59,884 units (13.2% of received). Snowflake today: 442,923 / 20,225. Line-by-line (68,877 line-file vs 67,065 Snowflake lines): 1,826 lines (12,478 units, 12,176 received) no longer in `FACT_CALL_SAMPLE` (0 flagged deleted, so removed from the table), 14 new lines (99 units), 1,425 status changes (mainly 1,207 `Delivered_vod` to `aoc_received__c`, both received), 0 quantity changes | QC session | Source changes after run |
| Q12 | Notebook `17_promotional_features_samples` reads only `ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER`; 0 references to `field_sample_line`, `FACT_CALL_SAMPLE` or `aoc_received`. Samples would be counted twice, and wrong in 17, if both blocks enter the model (S3, Q-S2, client summary P9) | `17_promotional_features_samples.ipynb` | OPEN |
| Q13 | Stale: (1) client summary (6 Nov) says 9 features / 16 columns, `X1-e` "no 10 / 20 mg split", c24 14,110 HCPs / 291,915 units, c28 18,584 / 401,027, 40 mg c24 1,698; output has 29 features, c24 13,840 / 283,525, c28 18,369 / 392,667, 40 mg c24 1,649; pending, failed, strength features not described. (2) Cell 18, 6 Nov bullets: 9 features, Year 2 452,210 / 20,448, 40 mg "0 for c1 to c15, 344 in c16" (output 64 at c15, 485 at c16). Its 11 Nov updates match the output (c1 10 / 20 mg 12M 320,255 / 146,164; c28 240,268 / 146,535; total 392,667). (3) Readiness X1: 21-day settling rule and no 10 / 20 mg split. (4) This plan: 9 features. Schema fixed by `expected_feature_columns()` | Cells 4, 18; client summary; readiness line 177 | FAIL |

## 4. Business rules to verify (readiness vs notebook)

| Rule | Readiness file says | Notebook does (cell) | Match |
| --- | --- | --- | --- |
| Received | `Delivered` + `AOC Received`; `Shipped` excluded | Status `DLVR_STAT` in `DELIVERED`, `Delivered_vod`, `aoc_received__c`; `Shipped_vod` is PENDING (cell 4) | Yes |
| Legacy products | Not covered | `Kerendia 10mg/20mg` with NULL status counted as received (`COUNT_LEGACY_DIRECT_SAMPLES=True`, Q-S6 open) | Difference |
| Settling rule | 21-day settling rule (R7) | Removed 6 Nov 2026 (`SETTLE_DAYS = 0`) at user request | Difference: update readiness |
| Strength | 40 mg flag (6 / 12M, data-available flag); no 10 vs 20 mg split | 40 mg flags 6 / 12M from `FORTY_MG_START = 2025-08-01`; `SMPL_40MG_AVAILABLE` in diagnostics only. **10 and 20 mg unit features built** (`STRENGTH_UNIT_FEATURES = [10, 20]`) | Difference: agree or drop |
| Pending / failed | Not in X1 | 14 features; PENDING = `Shipped_vod`, `In_Progress_vod`, `on_hold__c`, `IN PROCESS`; FAILED = `rejected__c`, `Returned`, `Cancelled_vod`, `lost_in_transit__c`; current status only | Addition: agree |
| Mapping | BHID to PROVIDER_ID via `SOURCE_PROVIDER_BHID_NPI_MAPPING` | Cell 5, restricted to the universe; a BHID on several PROVIDER_IDs gives its samples to each | Yes |
| Legacy volume | | Legacy lines 78,320 to 92,711 units a quarter from Q1 2023 to Q1 2024, all NULL status; 66 units in Q2 2024 | (see legacy row) |

## 5. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature | In 752? (SHAP rank) | NBA 3.1 feature | Status | Reason |
| --- | --- | --- | --- | --- |
| `TOTAL_OVERALL_SAMPLE_IN_LAST_6_MONTH` / `_5_` / `_2_MONTH` | Yes (179, 482, 450) | `SMPL_RCVD_UNITS_3M/6M/12M` | Replaced | Received rule incl. `aoc_received__c`; 3 / 6 / 12M windows |
| `TOTAL_SAMPLE_DROPPED_IN_LAST_6_MONTH` / `_1_MONTH` | Yes (218, 652) | `SMPL_RCVD_UNITS_*`, `SMPL_RCVD_CALLS_*` | Replaced | One received definition |
| `TOTAL_SAMPLE_SHIPPED_IN_LAST_6_MONTH` | Yes (740) | `SMPL_PENDING_*` | Replaced | Shipped is not received (V5) |
| `TOTAL_F2F_AND_DETAIL_WITH_SAMPLE_IN_LAST_4/3/2_MONTH`, `TOTAL_F2F_AND_GROUP_DETAIL_WITH_SAMPLE_IN_LAST_6_MONTH` | Yes (725, 741, 742, 749) | `SMPL_RCVD_CALLS_*` | Replaced | Sample calls from `FACT_CALL_SAMPLE`, not call type |
| (none) | | `SMPL_DAYS_SINCE_LAST_RCVD`, `SMPL_40MG_RCVD_6M/12M`, 10 / 20 mg units, pending / failed | New | Recency, 40 mg (Aug 2025), strength, status |

Summary: 10 NBA 3.0 sample features in the 752 (0.386% SHAP), all replaced.

## 6. HCP trace (step-by-step recompute)

HCPs: many received units, `aoc_received__c` only (missed by 3.0), `Shipped_vod` only (should be 0), legacy NULL-status sample, 40 mg sample.

| Step | What | Value |
| --- | --- | --- |
| 1 | PROVIDER_ID to BHID(s) | |
| 2 | Raw `FACT_CALL_SAMPLE` rows in 12M | |
| 3 | After status map (received only) | |
| 4 | After cutoff date | |
| 5 | Units / calls / 40 mg per window | |
| 6 | Final feature value | |
| 7 | Match | |

**Results.** HCPs with one BHID and one PROVIDER_ID. No HCP had only `Shipped_vod` lines in the c28 window, so case 3 is pending / failed only.

| Case | PROVIDER_ID / BHID | Cohort | Lines 12M | Units by status 12M | Received units 12M / calls 12M / units 3M | Days since | 40 mg 12M | 10 / 20 mg units 12M | Pending / failed units 12M | Match |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 Many units | 7671278 / BH10804723 | c28 | 59 | aoc 453, rejected 108 | 453 / 19 / 217 | 0 | 1 | 257 / 178 | 0 / 108 | 29 / 29 |
| 2 `aoc_received__c` only | 11645886 / BH12741525 | c28 | 1 | aoc 10 | 10 / 1 / 0 | 106 | 0 | 10 / 0 | 0 / 0 | 29 / 29 |
| 3 Pending / failed only | 10088356 / BH15022631 | c28 | 2 | Returned 25 | 0 / 0 / 0 | 999 | 0 | 0 / 0 | 0 / 25 | 29 / 29 |
| 4 Legacy NULL status | 9231801 / BH14762078 | c1 | 1 | NULL 6 | 6 / 1 / 0 | 284 | 0 | 6 / 0 | 0 / 0 | 29 / 29 |
| 5 40 mg + failed | 7676534 / BH10666435 | c28 | 14 | aoc 59, rejected 40 | 59 / 8 / 39 | 14 | 1 | 57 / 0 | 0 / 40 | 25 / 29 |

Case 5: output failed units 6M / 12M 30 / 50 and calls 4 / 6 vs 20 / 40 and 3 / 5 today. Difference = line `V68000000052094` (`rejected__c`, 10 units), in `field_sample_line` but removed from `FACT_CALL_SAMPLE` since the run.

## 7. Points found during QC

* Q-S6: legacy NULL-status lines are counted as received; they drive early training cohorts (client summary: 56.2% of c1 received units).
* Q-S7 confirmed in data: 75 and 105 received units in the weeks of 28 Jul and 4 Aug 2025.
* Source instability: since the run, 1,826 Year 2 lines (12,478 units) left `FACT_CALL_SAMPLE` and 1,425 changed status. A re-run will give slightly different features (Year 2 received today 442,923 units, -1.41% vs `22_` 449,246, still within the 3% tolerance).
* Received volume low in c16 to c23, recovering in testing and holdout (level shift between training and scoring).
* Pending features are near-constant (<= 0.02% non-zero).
* Notebook 17 not aligned (Q-S2).

## 8. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 11 / 13 (Q12 OPEN, Q13 FAIL) |
| Open issues | Q-S2 notebook 17 (double counting); stale client summary, cell 18 6 Nov bullets, readiness X1, this plan's expected shape; source line removals since the run |
| Decisions (to agree) | (a) Q-S6 legacy NULL = received. (b) Keep 10 / 20 mg units (readiness: no split). (c) Keep pending (near-constant) and failed features. (d) Re-run before modelling to pick up current source data |
| Fixes made to the notebook | None (QC read-only) |
| Ready for modelling | Yes for E5 as a candidate block, once (a) is decided and notebook 17 is excluded or aligned |
| Next channel | 06 Speaker programs |

## Appendix A. Fill rate (29 features)

0% null. % of rows not at the default (0; 999 for recency). Train c1 to c24, test c25 to c26, holdout c27 to c28.

| Feature | All | Train | Test | Holdout | c28 | Max |
| --- | --- | --- | --- | --- | --- | --- |
| `SMPL_RCVD_UNITS_3M` | 2.32 | 2.14 | 3.20 | 3.53 | 3.53 | 280 |
| `SMPL_RCVD_CALLS_3M` | 2.32 | 2.14 | 3.20 | 3.53 | 3.53 | 15 |
| `SMPL_RCVD_UNITS_6M` | 3.78 | 3.65 | 4.04 | 5.06 | 5.27 | 453 |
| `SMPL_RCVD_CALLS_6M` | 3.78 | 3.65 | 4.04 | 5.06 | 5.27 | 27 |
| `SMPL_RCVD_UNITS_12M` | 6.09 | 6.16 | 5.24 | 6.06 | 6.23 | 844 |
| `SMPL_RCVD_CALLS_12M` | 6.09 | 6.16 | 5.24 | 6.06 | 6.23 | 50 |
| `SMPL_DAYS_SINCE_LAST_RCVD` (999) | 6.09 | 6.16 | 5.24 | 6.06 | 6.23 | 999 |
| `SMPL_40MG_RCVD_6M` | 0.16 | 0.10 | 0.43 | 0.52 | 0.55 | 1 |
| `SMPL_40MG_RCVD_12M` | 0.21 | 0.13 | 0.69 | 0.77 | 0.75 | 1 |
| `SMPL_10MG_RCVD_UNITS_3M` | 2.19 | 2.02 | 3.01 | 3.33 | 3.34 | 180 |
| `SMPL_10MG_RCVD_UNITS_6M` | 3.60 | 3.48 | 3.81 | 4.81 | 5.02 | 299 |
| `SMPL_10MG_RCVD_UNITS_12M` | 5.87 | 5.96 | 4.95 | 5.76 | 5.94 | 498 |
| `SMPL_20MG_RCVD_UNITS_3M` | 1.67 | 1.53 | 2.38 | 2.61 | 2.60 | 133 |
| `SMPL_20MG_RCVD_UNITS_6M` | 2.77 | 2.66 | 3.04 | 3.86 | 4.03 | 198 |
| `SMPL_20MG_RCVD_UNITS_12M` | 4.56 | 4.58 | 4.08 | 4.72 | 4.85 | 346 |
| `SMPL_PENDING_UNITS_3M` | 0.00 | 0.00 | 0.00 | 0.01 | 0.01 | 27 |
| `SMPL_PENDING_CALLS_3M` | 0.00 | 0.00 | 0.00 | 0.01 | 0.01 | 2 |
| `SMPL_PENDING_UNITS_6M` | 0.00 | 0.00 | 0.01 | 0.01 | 0.01 | 27 |
| `SMPL_PENDING_CALLS_6M` | 0.00 | 0.00 | 0.01 | 0.01 | 0.01 | 2 |
| `SMPL_PENDING_UNITS_12M` | 0.02 | 0.02 | 0.01 | 0.02 | 0.02 | 145 |
| `SMPL_PENDING_CALLS_12M` | 0.02 | 0.02 | 0.01 | 0.02 | 0.02 | 7 |
| `SMPL_DAYS_SINCE_LAST_PENDING` (999) | 0.02 | 0.02 | 0.01 | 0.02 | 0.02 | 999 |
| `SMPL_FAILED_UNITS_3M` | 0.07 | 0.06 | 0.10 | 0.11 | 0.11 | 135 |
| `SMPL_FAILED_CALLS_3M` | 0.07 | 0.06 | 0.10 | 0.11 | 0.11 | 8 |
| `SMPL_FAILED_UNITS_6M` | 0.11 | 0.11 | 0.15 | 0.17 | 0.17 | 185 |
| `SMPL_FAILED_CALLS_6M` | 0.11 | 0.11 | 0.15 | 0.17 | 0.17 | 12 |
| `SMPL_FAILED_UNITS_12M` | 0.19 | 0.17 | 0.26 | 0.27 | 0.26 | 260 |
| `SMPL_FAILED_CALLS_12M` | 0.19 | 0.17 | 0.26 | 0.27 | 0.26 | 20 |
| `SMPL_DAYS_SINCE_LAST_FAILED` (999) | 0.19 | 0.17 | 0.26 | 0.27 | 0.26 | 999 |

## Appendix B. Profile by cohort

| Cohort | HCPs rcvd 12M | % | Units 12M | Units 3M | 10 mg 12M | 20 mg 12M | HCPs 40 mg 12M / 6M | HCPs failed / units | HCPs pending |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| c1 | 21,490 | 7.29 | 466,419 | 148,610 | 320,255 | 146,164 | 0 / 0 | 223 / 4,547 | 327 |
| c4 | 21,037 | 7.14 | 498,762 | 128,213 | 338,332 | 160,430 | 0 / 0 | 339 / 7,102 | 156 |
| c8 | 20,261 | 6.87 | 532,548 | 114,287 | 349,022 | 183,526 | 0 / 0 | 479 / 10,121 | 12 |
| c12 | 18,723 | 6.35 | 529,195 | 142,054 | 338,760 | 190,435 | 0 / 0 | 545 / 10,643 | 10 |
| c14 | 18,385 | 6.24 | 519,833 | 114,298 | 332,719 | 187,114 | 0 / 0 | 556 / 11,310 | 10 |
| c15 | 17,760 | 6.03 | 489,296 | 88,627 | 312,770 | 176,141 | 64 / 64 | 535 / 10,772 | 11 |
| c16 | 17,525 | 5.95 | 470,979 | 73,212 | 298,912 | 170,470 | 485 / 485 | 615 / 12,062 | 19 |
| c19 | 15,280 | 5.18 | 368,059 | 39,517 | 230,979 | 134,650 | 870 / 870 | 624 / 11,664 | 16 |
| c23 | 13,161 | 4.47 | 273,773 | 66,019 | 168,436 | 101,655 | 1,377 / 830 | 642 / 11,568 | 37 |
| c24 | 13,840 | 4.70 | 283,525 | 97,098 | 173,313 | 105,769 | 1,649 / 1,040 | 682 / 12,409 | 40 |
| c25 | 14,970 | 5.08 | 303,316 | 131,033 | 184,099 | 114,005 | 1,903 / 1,187 | 745 / 13,624 | 41 |
| c26 | 15,910 | 5.40 | 323,196 | 163,721 | 195,910 | 121,309 | 2,140 / 1,366 | 763 / 13,740 | 41 |
| c27 | 17,348 | 5.89 | 359,379 | 161,930 | 218,417 | 134,667 | 2,300 / 1,469 | 816 / 15,040 | 40 |
| c28 | 18,369 | 6.23 | 392,667 | 161,385 | 240,268 | 146,535 | 2,221 / 1,609 | 777 / 14,725 | 64 |
