# QC 01: FTP features, NBA 3.1

**QC status:** DONE, 24 Nov 2026 (claim type 1 of 2; next: 02 Copay)  
**Verdict:** PASS with actions. The features are correct: the HCP trace matched 133 of 133 values (7 cases x 19 features), and 13 independent invariants found 0 violations once one invariant of mine was corrected (Q11). 1 fix, 4 documentation items and 4 notes are open (section 10).  
**QC run:** 24 Nov 2026, serverless, on the output written 2026-11-24 (`PULL_DT`) by the claims-cohort run of `ftp_feature`. The notebook was not re-run during QC.

How to use: see `00_qc_template.md`. Rule source = `60_ftp_copay_nba_3_1_readiness_plan.md` ("readiness"). `<V31>` = `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume`.

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `04_Promotional_Features/FTP_and_Copay/ftp_feature` (19 cells) |
| Rule file | `60_ftp_copay_nba_3_1_readiness_plan.md` |
| Source table | `market_access.kerendia_ftp_claims` (7 `WF` program groups) |
| Universe | `<V31>/HCP_Universe_without_call_hcps`: 294,727 HCPs |
| Cohorts | `<V31>/cohorts/claims/cohorts.parquet`: family `claims`, offset 0, c1 to c28 (c1-c24 train, c25-c26 test, c27-c28 holdout) |
| Mapping | 3.0 volume `ops_pipeline/query_output/kerendia_nba_3_0_npi_bhid_mapping` (read only) |
| Output | `<V31>/hcp_level_model/dev_pipeline/notebook_output/market_access_nba_3_1/kerendia_nba_3_1_hcp_model_ftp_features`: 8,252,328 rows after the F1 rerun (8,252,356 when QC ran) x 19 features (+ 6 keys, `PULL_DT`) |
| Expected grain | One row per `PROVIDER_ID` x `COHORT` = 294,727 x 28 |
| NBA 3.0 counterpart | 3.0 ops output `kerendia_nba_3_hcp_model_ftp_features_v2_for_inference` (cohort `I01`, `MONTH_ID` 2026-10-17) |
| NBA 3.0 final model | `Final NBA 3.0 Modeling Features.xlsx` (752 features) |

## 2. QC checklist

| # | Check | Pass when | Status |
| --- | --- | --- | --- |
| Q1 | HCP universe | Output = universe x 28, 0 duplicates, 0 outside | PASS (1 fix: `PROVIDER_ID = '0'`) |
| Q2 | Right cohorts (claims, 3.1 volume) | 0 mismatches, no promotional dates | PASS |
| Q3 | Windows and point-in-time | No claim after E or loaded late contributes | PASS |
| Q4 | Data sources vs readiness | Same sources, differences explained | PASS (2 notes) |
| Q5 | All features made | 0 missing without a reason | PASS |
| Q6 | Business rules | Match or documented difference | PASS (4 documented differences) |
| Q7 | Fill rate | No unexpected nulls; flags listed | PASS (6 features > 99.5% zero) |
| Q8 | NBA 3.0 752 coverage | 0 skipped | PASS (4 / 4 mapped) |
| Q9 | Preserved vs new | All labelled | PASS |
| Q10 | HCP trace | Output = recompute | PASS (133 / 133) |
| Q11 | Invariants | 0 violations | PASS |
| Q12 | NBA 3.0 output comparison | Differences explained | PASS (not comparable value by value) |
| Q13 | Reproducibility and docs | No stale text that changes meaning | PASS (readiness doc items in section 10) |

## 3. Evidence log

| # | Result (numbers) | Notes |
| --- | --- | --- |
| Q1 | Universe 294,727 rows = 294,727 distinct. Output 8,252,356 rows, 294,727 distinct HCPs, exactly 294,727 per cohort, 0 duplicate (`PROVIDER_ID`, `COHORT`), 0 HCPs outside the universe | `PROVIDER_ID = '0'` (placeholder) is in the universe: 28 rows, 0 fills. `00_cohort_config.load_hcp_universe` drops it; `ftp_feature` does not (F1) |
| Q2 | `metadata.json`: family `claims`, offset 0, 28 cohorts, c1 2024-07-01 to c28 2026-10-01. Output vs file on `COHORT` / `DATASET` / `PREDICTION_MONTH` / `SVC_DT`: 28 cohorts, 0 mismatches; `SVC_DT` always the 1st of a month (0 promotional day-17 dates) | |
| Q3 | E = last day of lookback end month (c28: 2026-08-31); 12M window (2025-08-31, 2026-08-31]. Trace: fill on 2026-08-31 counted (case 3a, recency 0); fill on 2026-09-01 not counted (case 3b); fill 2026-05-01 loaded 2026-11-15 not counted (case 4, the only late-loaded claim in the c28 window). Notebook S1 SQL recount c28 = output (9,279 fills / 3,951 HCPs); O4: 0 of 364 fills in the last 14 days loaded late | |
| Q4 | Section 5 | Universe path name differs from readiness (same 294,727); universe HCPs with an NPI 294,553 vs readiness 294,578 |
| Q5 | Section 6: 12 core + 7 extended = 19 columns = config; C5 / C6 are built in `copay_feature` (DEC-F07); X4 / X5 not built (privacy, V7 open) | |
| Q6 | Section 4 | |
| Q7 | Section 7: 0 nulls in all 19; 0 constant; train-vs-holdout non-zero share differs by < 1 point for every feature | `FTP_DAYS_SINCE_LAST_FILL` sentinel 9999 in 95.59% of rows |
| Q8 | 4 FTP features in the 752: ranks 467, 632, 662, 664; together 0.0986% of mean abs SHAP. 0 copay features | Readiness says ranks 500-661 (F3) |
| Q9 | Section 8: 4 replaced, 0 dropped, 15 new | |
| Q10 | Section 9: 7 HCP x cohort cases, 19 features each, recomputed in pandas from the source table: 0 mismatches | |
| Q11 | 0 violations: nested 1 <= 3 <= 6 <= 12M (fills, new-Rx); new-Rx <= fills; flag = (12M fills > 0); cap = min(12M, 21); band edges 0/1/2/4/10/25; 1M fill => recency <= 30; extended = 0 when no 12M fill; shares in [0, 1]; pharmacies <= fills; fills per Rx >= 1 when active; trend within [-prior 3M, 3M]; flag = (recency < window days) | My first check "recency <= 365 iff flag" gave 118 rows (recency 365, flag 0). Cause: the window is 12 calendar months (365 or 366 days), recency is days; 127 rows have flag 1 at 365 (window with 29 Feb). Corrected check: 0 (F6) |
| Q12 | 3.0 `I01` (3,893 HCPs, written date, record grain, anchor 2026-10-17) vs 3.1 c28 (fill date, E 2026-08-31): HCPs > 0 1M 414 vs 547, 3M 1,188 vs 1,358, 6M 2,104 vs 2,318; Spearman (rows with either > 0) -0.628 / -0.091 / 0.322 | Windows end ~7 weeks apart and use a different date, so value-level agreement is not expected. 3.1 counts are higher on fewer days |
| Q13 | Output = full universe run (8,252,356 rows), `PULL_DT` 2026-11-24, QC log `qc/ftp_feature_checks` written; notebook header and decision log describe the claims-cohort run | `23_ftp_copay_features` and `00_ftp_copay_config` (promotional-cohort build) are still in the folder (F5) |

## 4. Business rules (readiness vs notebook)

| Rule | Readiness says | Notebook does | Match |
| --- | --- | --- | --- |
| Source | UC `kerendia_ftp_claims`, not sales-aligned (D1) | Same; sales-aligned not read | Yes |
| Programs | 7 `WF` groups; BRIDGE excluded (D8) | V1: 0 rows outside 7 groups | Yes |
| Claim grain | One count per `ORGN_CLM_AUTH_NUM` (S2) | 106,211 rows = 106,211 claims; 0 duplicates | Yes |
| Feature date | `RX_FILL_DATE`; written date only for X6 (D2) | Same; written date used only in X6 and experiment E6 | Yes |
| Point-in-time | `INSERT_TS <= cutoff`, trim 14 days (principle 3, D4) | E = last day of lookback month, `INSERT_TS < PREDICTION_MONTH`, trim 0 (DEC-F02 / F03; one-month gap; E7 best at 0d) | Difference, documented (F2) |
| Windows | 1 / 3 / 6 / 12M ending at lookback end (D3) | Same, calendar months | Yes |
| Join | `PROVIDER_ID -> NPI -> PRSC_NPI`; `BH_ID` monitored; null NPI excluded (principle 7, V4) | Same; 47 null-NPI claims excluded; link 99.63% | Yes |
| Full universe / zero means zero | Every HCP x cohort; has-any flag; 0 = no fill (S3) | Same; 0 nulls | Yes (except `'0'`, F1) |
| Skew | Cap at p99 (example 23) + band (D5) | Cap 21 (training p99 on active rows) + 6 bands | Value differs, documented (F4) |
| Recency | Sentinel for never (principle 6) | 9999 | Yes |
| Leakage | Clawback flags, `MDM_SPECIALTY` excluded (V5) | Not used | Yes |
| Money | `NET_*` only (principle 5) | No money feature for FTP | N/A |
| Naming | `FTP_` prefix; do not reuse `TOTAL_RX_FTP_IN_LAST_*` (D6) | Same | Yes |
| Dropped from 3.0 | `PCT_*`, all-time running total | Not built | Yes |
| Layout | One combined `23_ftp_copay_features` (D6) | Separate `ftp_feature` / `copay_feature` (user decision) | Difference, documented (F5) |
| Keep / drop | Decided by experiments (S6, G2) | Proxy E1 +0.0012 / +0.0018 AUC < +0.002: DROP; all columns written | Yes (F7) |

## 5. Data sources (readiness vs notebook)

| Source | Readiness says | Notebook uses | Rows / dates found | Match |
| --- | --- | --- | --- | --- |
| FTP claims | `market_access.kerendia_ftp_claims`, ~106K, 7 WF | Same | 106,211 rows; fill 2021-10-11 to 2026-11-13; `REFRESH_TS` 2026-11-23; max `INSERT_TS` 2026-11-15; 47 null NPI | Yes |
| Universe | `kerendia_nba_3_1.input_hcp_universe` (294,727) | `<V31>/HCP_Universe_without_call_hcps` | 294,727 | Same count, other path name |
| Cohorts | `input_claims_cohorts` (c1-c28) | `<V31>/cohorts/claims/cohorts.parquet` | 28, family claims, offset 0 | Yes |
| Mapping | `00_cohort_config` default `NPI_BHID_MAPPING_PATH` | Same path (3.0 volume, read only) | 1,659,041 rows; 294,553 universe HCPs with NPI | Yes |
| Snapshot | O2 only | O2 only | 1 partition (2026-11-01) | Yes |
| Experiment inputs | E0 = 3.1 model without FTP | Proxy: `kerendia_prior_writing` (E0) + `kerendia_claims_monthly_from_raw_fct_rx` (NBRx target) | not re-profiled | Proxy, documented (DEC-F12) |
| Writes | 3.1 volume only | Output, staging, QC log in `<V31>/.../market_access_nba_3_1` | - | Yes |

## 6. Features made (plan vs output)

| Plan family | Expected | Output columns | Status |
| --- | --- | --- | --- |
| C1 has any | 1 | `FTP_HAS_ANY_12M` | Made |
| C2 fills | 8-12 incl. cap / band | `FTP_FILLS_1M/3M/6M/12M`, `FTP_FILLS_12M_CAP`, `FTP_FILLS_12M_BAND` | Made (6) |
| C3 new-Rx fills | 4 | `FTP_NEWRX_FILLS_1M/3M/6M/12M` | Made |
| C4 recency | 1 | `FTP_DAYS_SINCE_LAST_FILL` | Made |
| C5 affordability | copay only | - | N/A for FTP |
| C6 overlap | 1 | `FTP_CPY_BOTH_12M` in `copay_feature` | Built there |
| X1 persistence | refill share, fills per Rx | `FTP_REFILL_SHARE_12M`, `FTP_FILLS_PER_RX_12M` | Made |
| X2 dose mix | 20 / 40 mg share | `FTP_HIGH_DOSE_SHARE_12M` | Made |
| X3 patient-days | days supply | `FTP_DAYS_SUPPLY_12M` | Made |
| X4 patient mix | after privacy check | - | Not built (open) |
| X5 payer mix | after V7 | - | Not built (V7 open) |
| X6 written-to-fill lag | 1 | `FTP_AVG_WRITTEN_TO_FILL_DAYS_12M` | Made |
| X7 pharmacy breadth | 1 | `FTP_DISTINCT_PHARMACIES_12M` | Made |
| X8 trend | 1 | `FTP_FILLS_3M_VS_PRIOR_3M` | Made |

Types: counts long / int, shares and averages double; 0 unexpected columns.

## 7. Fill rate

% over 8,252,356 rows. 0 nulls in every feature.

| Feature | % zero | % non-zero | min / max | % non-zero train / test / holdout / c28 | Flag |
| --- | --- | --- | --- | --- | --- |
| `FTP_HAS_ANY_12M` | 98.735 | 1.265 | 0 / 1 | 1.259 / 1.276 / 1.330 / 1.341 | |
| `FTP_FILLS_1M` | 99.832 | 0.168 | 0 / 37 | 0.166 / 0.179 / 0.185 / 0.186 | > 99.5% zero |
| `FTP_FILLS_3M` | 99.591 | 0.409 | 0 / 98 | 0.402 / 0.443 / 0.455 / 0.461 | > 99.5% zero |
| `FTP_FILLS_6M` | 99.290 | 0.710 | 0 / 145 | 0.697 / 0.793 / 0.789 / 0.786 | |
| `FTP_FILLS_12M` | 98.735 | 1.265 | 0 / 198 | 1.259 / 1.276 / 1.330 / 1.341 | |
| `FTP_FILLS_12M_CAP` | 98.735 | 1.265 | 0 / 21 | same as 12M | |
| `FTP_FILLS_12M_BAND` | 98.735 | 1.265 | 0 / 5 | same as 12M | |
| `FTP_NEWRX_FILLS_1M` | 99.847 | 0.153 | 0 / 37 | 0.151 / 0.167 / 0.168 / 0.169 | > 99.5% zero |
| `FTP_NEWRX_FILLS_3M` | 99.625 | 0.375 | 0 / 98 | 0.369 / 0.408 / 0.419 / 0.423 | > 99.5% zero |
| `FTP_NEWRX_FILLS_6M` | 99.346 | 0.654 | 0 / 145 | 0.643 / 0.723 / 0.724 / 0.724 | |
| `FTP_NEWRX_FILLS_12M` | 98.831 | 1.169 | 0 / 198 | 1.162 / 1.192 / 1.236 / 1.246 | |
| `FTP_DAYS_SINCE_LAST_FILL` | 0.007 | 4.406 (+ 95.587 sentinel) | 0 / 9999 | 4.295 / 5.010 / 5.133 / 5.166 | sentinel |
| `FTP_REFILL_SHARE_12M` | 99.795 | 0.205 | 0 / 1 | 0.210 / 0.168 / 0.184 / 0.188 | > 99.5% zero |
| `FTP_FILLS_PER_RX_12M` | 98.735 | 1.265 | 0 / 9 | same as 12M | |
| `FTP_HIGH_DOSE_SHARE_12M` | 99.628 | 0.372 | 0 / 1 | 0.362 / 0.417 / 0.448 / 0.458 | > 99.5% zero |
| `FTP_DAYS_SUPPLY_12M` | 98.735 | 1.265 | 0 / 5,940 | same as 12M | |
| `FTP_AVG_WRITTEN_TO_FILL_DAYS_12M` | 99.012 | 0.988 | 0 / 771 | 0.988 / 0.971 / 1.013 / 1.023 | |
| `FTP_DISTINCT_PHARMACIES_12M` | 98.735 | 1.265 | 0 / 47 | same as 12M | |
| `FTP_FILLS_3M_VS_PRIOR_3M` | 99.331 | 0.669 | -63 / 58 | 0.656 / 0.752 / 0.745 / 0.741 | |

Recency is non-zero for 4.4% of rows but only 1.3% have a 12M fill: recency looks back to 2021, the 12M features do not.

## 8. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature | In 752? (SHAP rank, % SHAP) | NBA 3.1 feature | Status | Reason |
| --- | --- | --- | --- | --- |
| `TOTAL_RX_FTP_IN_LAST_1_MONTH` | 467, 0.0445% | `FTP_FILLS_1M` | replaced | fill date, claim grain, new name (D6) |
| `TOTAL_RX_FTP_IN_LAST_4_MONTH` | 632, 0.0218% | `FTP_FILLS_3M` / `FTP_FILLS_6M` | replaced | 4M window not in D3 (1 / 3 / 6 / 12M) |
| `TOTAL_RX_FTP_IN_LAST_6_MONTH` | 662, 0.0163% | `FTP_FILLS_6M` | replaced | as 1M |
| `TOTAL_RX_FTP_IN_LAST_3_MONTH` | 664, 0.0159% | `FTP_FILLS_3M` | replaced | as 1M |
| 3.0 `TOTAL_RX_FTP_IN_LAST_2/5_MONTH`, `PCT_*`, running total | not in 752 | - | dropped | not in D3 windows / readiness drop list |

Summary: 4 FTP features in the 752 (0.0986% of SHAP): 4 replaced, 0 skipped. New in 3.1 (15): `FTP_HAS_ANY_12M`, `FTP_FILLS_12M` (+ cap, band), 4 new-Rx windows, recency, 7 extended (X1-X3, X6-X8). None is on the model-recommended list after G2 (F7).

## 9. HCP trace (step-by-step recompute)

E = last day of the lookback end month; steps follow the template. All 19 features compared for each case.

| Case | PROVIDER_ID | Cohort | NPIs | 2 raw rows | 3 after filters | 4 fill <= E | 5 loaded < pred. month | 6 in 12M | Values / mismatches |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 high volume | 8094582 | c28 | 1 | 323 | 323 | 302 | 302 | 156 | 19 / 0 |
| 2 refill + high dose | 6854429 | c28 | 1 | 10 | 10 | 9 | 9 | 3 | 19 / 0 |
| 3a fill on last day (in) | 23309802 | c28 | 1 | 1 | 1 | 1 | 1 | 1 | 19 / 0 |
| 3b fill on 1st of next month (out) | 10324312 | c28 | 1 | 3 | 3 | 2 | 2 | 1 | 19 / 0 |
| 4 loaded after prediction month | 7261360 | c28 | 1 | 2 | 2 | 2 | 1 | 1 | 19 / 0 |
| 5 no FTP fill | 7961830 | c28 | 1 | 0 | 0 | 0 | 0 | 0 | 19 / 0 |
| 6 training cohort | 8094582 | c5 | 1 | 323 | 323 | 93 | 93 | 43 | 19 / 0 |

Derived values (recompute = output in every cell):

| Case | 12M window | Last fill | 1M / 3M / 12M fills | New-Rx 12M | Recency | Cap | Refill share | High-dose share | 3M vs prior 3M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | (2025-08-31, 2026-08-31] | 2026-08-27 | 11 / 44 / 156 | 156 | 4 | 21 | 0 | 0 | -8 |
| 2 | same | 2026-08-20 | 1 / 2 / 3 | 1 | 11 | 3 | 0.6667 | 0.3333 | 2 |
| 3a | same | 2026-08-31 | 1 / 1 / 1 | 1 | 0 | 1 | 0 | 1 | 1 |
| 3b | same | 2026-02-09 | 0 / 0 / 1 | 1 | 203 | 1 | 0 | 0 | 0 |
| 4 | same | 2026-05-01 | 0 / 0 / 1 | 1 | 122 | 1 | 0 | 1 | -1 |
| 5 | same | none | 0 / 0 / 0 | 0 | 9999 | 0 | 0 | 0 | 0 |
| 6 | (2023-09-30, 2024-09-30] | 2024-09-17 | 8 / 20 / 43 | 43 | 13 | 21 | 0 | 0 | 11 |

No universe HCP sharing an NPI has an FTP fill in the c28 window, so the shared-NPI rule (DEC-F06) could not be traced.

## 10. Findings and actions

| # | Finding | Severity | Action / owner | Status |
| --- | --- | --- | --- | --- |
| F1 | `PROVIDER_ID = '0'` (placeholder) is in the universe and has 28 output rows (all 0). `00_cohort_config.load_hcp_universe` and the patient notebooks drop it | fix | Fixed in code 24 Nov 2026: config cell universe read now drops null / empty / `'0'` (same rule as `load_hcp_universe`); checked on the universe file: 294,727 -> 294,726 (only `'0'` dropped), expected output 8,252,328 rows. Rerun 24 Nov 2026: output 8,252,328 rows, 294,726 HCPs, 0 `'0'` rows, 0 duplicate keys; G1 12 / 12 PASS; S4 c28 3,951 HCPs / 9,279 fills (unchanged); gates unchanged (G3 FAIL) | FIXED |
| F2 | Readiness principle 3 / D4 (14-day trim, `INSERT_TS <= cutoff`) describes the promotional anchor; the claims-cohort run uses `INSERT_TS < PREDICTION_MONTH` and trim 0 | doc | Update readiness D4 | OPEN |
| F3 | Readiness section 3: FTP SHAP ranks 500-661, 0.09%; actual 467, 632, 662, 664 and 0.0986% | doc | Update readiness | OPEN |
| F4 | Readiness D5 cap example 23; measured 21. V6 expects 1.9-2.7% coverage (FTP or copay); FTP alone is 1.10-1.62% | doc | Update readiness | OPEN |
| F5 | Readiness D6 recommends one combined notebook; the folder now has `ftp_feature` / `copay_feature` plus the older `23_ftp_copay_features` / `00_ftp_copay_config` (promotional build) | doc | Record the layout decision; archive or rerun the `23_` output so nothing downstream reads it | OPEN |
| F6 | 12M flag uses calendar months, recency uses days: a fill exactly 365 days back is in the window only when it contains 29 Feb (118 rows flag 0, 127 rows flag 1) | note | Keep; mention in feature docs | Accepted |
| F7 | G2 = DROP on the proxy model (+0.0012 / +0.0018 AUC); 3.0 had 4 FTP features in the 752 | note | Modelling to confirm with the full 3.1 model; brand team on Q9 | OPEN |
| F8 | 6 features > 99.5% zero (1M / 3M fills, 1M / 3M new-Rx, refill share, high-dose share) | note | Feature selection to filter | OPEN |
| F9 | G3 fails: O2 retention and O5 group owner open; no scheduled job | note | Market access team (Q7, Q8) | OPEN |

## 11. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 13 / 13 (with the actions above) |
| QC by / date | Genie Code for Wenjie Chen, 24 Nov 2026 |
| Reviewed by / date | |
| Next | 02 Copay (`copay_feature`) |
