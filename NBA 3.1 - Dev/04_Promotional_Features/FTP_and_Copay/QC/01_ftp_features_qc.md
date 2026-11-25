# QC 01: FTP features, NBA 3.1

**QC status:** DONE, 24 Nov 2026 (claim type 1 of 2; next: 02 Copay)  
**Verdict:** PASS with actions. The features are correct: the HCP trace matched 133 of 133 values (7 cases x 19 features), and 13 independent invariants found 0 violations once one invariant of mine was corrected (Q11). 1 fix, 4 documentation items and 4 notes are open (section 10).  
**QC run:** 24 Nov 2026, serverless, on the output written 2026-11-24 (`PULL_DT`) by the claims-cohort run of `ftp_feature`. The notebook was not re-run during QC.  
**QC update (25 Nov 2026):** Phase 2 X4 (8 patient-mix shares) and X5 (2 payer-mix shares) added to the output after the first QC; checked on the 25 Nov output (`PULL_DT` 2026-11-25, 8,252,328 rows x 29 features): fill rate (section 7), invariants (Q11) and an independent HCP trace (Q10: 70 / 70 values). V7 closed (section 6a).

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
| Output | `<V31>/hcp_level_model/dev_pipeline/notebook_output/market_access_nba_3_1/kerendia_nba_3_1_hcp_model_ftp_features`: 8,252,328 rows after the F1 rerun (8,252,356 when QC ran) x 29 features since 25 Nov 2026 (19 at first QC + 8 X4 + 2 X5; + 6 keys, `PULL_DT`) |
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
| Q14 | Snapshot retention (O2), program groups (O5) and data drift, owned by the NBA team | O2: every monthly snapshot partition kept (none dropped, latest month present); O5: groups = config (0 new, 0 missing); drift: every change > 20% vs training explained and signed off by the NBA team | PASS (25 Nov 2026) |

## 3. Evidence log

| # | Result (numbers) | Notes |
| --- | --- | --- |
| Q1 | Universe 294,727 rows = 294,727 distinct. Output 8,252,356 rows, 294,727 distinct HCPs, exactly 294,727 per cohort, 0 duplicate (`PROVIDER_ID`, `COHORT`), 0 HCPs outside the universe | `PROVIDER_ID = '0'` (placeholder) is in the universe: 28 rows, 0 fills. `00_cohort_config.load_hcp_universe` drops it; `ftp_feature` does not (F1) |
| Q2 | `metadata.json`: family `claims`, offset 0, 28 cohorts, c1 2024-07-01 to c28 2026-10-01. Output vs file on `COHORT` / `DATASET` / `PREDICTION_MONTH` / `SVC_DT`: 28 cohorts, 0 mismatches; `SVC_DT` always the 1st of a month (0 promotional day-17 dates) | |
| Q3 | E = last day of lookback end month (c28: 2026-08-31); 12M window (2025-08-31, 2026-08-31]. Trace: fill on 2026-08-31 counted (case 3a, recency 0); fill on 2026-09-01 not counted (case 3b); fill 2026-05-01 loaded 2026-11-15 not counted (case 4, the only late-loaded claim in the c28 window). Notebook S1 SQL recount c28 = output (9,279 fills / 3,951 HCPs); O4: 0 of 364 fills in the last 14 days loaded late | |
| Q4 | Section 5 | Universe path name differs from readiness (same 294,727); universe HCPs with an NPI 294,553 vs readiness 294,578 |
| Q5 | Section 6: 12 core + 17 extended = 29 columns = config (25 Nov 2026; first QC: 12 + 7 = 19); C5 / C6 are built in `copay_feature` (DEC-F07); X4 built after compliance sign-off (DEC-F09), X5 built after V7 profiling (DEC-F16) | Notebook S5: 29 columns from config, rebuild identical |
| Q6 | Section 4 | |
| Q7 | Section 7: 0 nulls in all 19; 0 constant; train-vs-holdout non-zero share differs by < 1 point for every feature. X4 / X5 (25 Nov output): 0 nulls in all 10; all 10 > 99.5% zero; `FTP_PAT_GENDER_U_SHARE_12M` constant 0; `FTP_OTHER_CVRG_REJECTED_SHARE_12M` non-zero in training only (0.018%; 0 in test / holdout) | `FTP_DAYS_SINCE_LAST_FILL` sentinel 9999 in 95.59% of rows; X4 / X5 flags in F10 |
| Q8 | 4 FTP features in the 752: ranks 467, 632, 662, 664; together 0.0986% of mean abs SHAP. 0 copay features | Readiness says ranks 500-661 (F3) |
| Q9 | Section 8: 4 replaced, 0 dropped, 25 new (15 at first QC + 8 X4 + 2 X5) | |
| Q10 | Section 9: 7 HCP x cohort cases, 19 features each, recomputed in pandas from the source table: 0 mismatches. X4 / X5 (25 Nov): same 7 cases, 10 features each, recomputed in pandas from the raw `kerendia_ftp_claims` rows (own date parsing, 3.0 mapping file, cohort file): 70 / 70 match, 12M fills match in every case | The 7 cases have no code `01` / `03` fill, so X5 is 0 in all of them; X5 non-zero values are covered by the notebook c28 recount (297 code `01` fills / 0 code `03`, output = SQL) |
| Q11 | 0 violations: nested 1 <= 3 <= 6 <= 12M (fills, new-Rx); new-Rx <= fills; flag = (12M fills > 0); cap = min(12M, 21); band edges 0/1/2/4/10/25; 1M fill => recency <= 30; extended = 0 when no 12M fill; shares in [0, 1]; pharmacies <= fills; fills per Rx >= 1 when active; trend within [-prior 3M, 3M]; flag = (recency < window days). X4 / X5 (25 Nov, 104,419 active rows): 5 age shares sum to 1: 0 violations; 3 gender shares sum to 1: 0; X5 `01` + `03` shares <= 1: 0; any of the 10 non-zero when no 12M fill: 0; all 10 within [0, 1] | My first check "recency <= 365 iff flag" gave 118 rows (recency 365, flag 0). Cause: the window is 12 calendar months (365 or 366 days), recency is days; 127 rows have flag 1 at 365 (window with 29 Feb). Corrected check: 0 (F6) |
| Q12 | 3.0 `I01` (3,893 HCPs, written date, record grain, anchor 2026-10-17) vs 3.1 c28 (fill date, E 2026-08-31): HCPs > 0 1M 414 vs 547, 3M 1,188 vs 1,358, 6M 2,104 vs 2,318; Spearman (rows with either > 0) -0.628 / -0.091 / 0.322 | Windows end ~7 weeks apart and use a different date, so value-level agreement is not expected. 3.1 counts are higher on fewer days |
| Q13 | Output = full universe run (8,252,356 rows), `PULL_DT` 2026-11-24, QC log `qc/ftp_feature_checks` written; notebook header and decision log describe the claims-cohort run | `23_ftp_copay_features` and `00_ftp_copay_config` (promotional-cohort build) are still in the folder (F5) |
| Q14 | 25 Nov 2026 check on the source table and the current output (29 features). **O2:** `kerendia_ftp_claims_snapshot` has 1 partition (2026-11-01, 136,306 raw rows); nothing dropped; from now on one partition per month must be added and kept. **O5:** `GRP_NUM` in `kerendia_ftp_claims` = the 7 WF groups in config (0 new, 0 missing). **Drift** (per cohort, vs training): active HCPs training 3,711 / test 3,760 (+1%) / holdout 3,918 (+6%); 12M fills 9,002 / 8,926 (-1%) / 9,242 (+3%); new-Rx share 0.891 / 0.910 / 0.905 (notebook O3). All within 20% | Independent query on the source table and the output; notebook O3 / O5 rows in `qc/ftp_feature_checks` | Owner of O2, O5 and drift review: **NBA team** (user, 25 Nov 2026). Re-check on every refresh: the partition list only grows; a new or missing group fails O5 until the NBA team updates `PROGRAM_GROUPS` and notes it in the decision log |

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
| X4 patient mix | after privacy check | `FTP_PAT_AGE_18_44/45_64/65_74/75P/UNKNOWN_SHARE_12M`, `FTP_PAT_GENDER_MALE/FEMALE/U_SHARE_12M` | Made (8), 25 Nov 2026: compliance sign-off for age / gender share features; bands agreed with the user; claim-weighted shares of 12M fills, no patient IDs (DEC-F09) |
| X5 payer mix | after V7 | `FTP_NO_OTHER_CVRG_SHARE_12M` (code `01`), `FTP_OTHER_CVRG_REJECTED_SHARE_12M` (code `03`) | Made (2), 25 Nov 2026: V7 closed (section 6a); `00` is the remainder, no column; no BIN feature (DEC-F16) |
| X6 written-to-fill lag | 1 | `FTP_AVG_WRITTEN_TO_FILL_DAYS_12M` | Made |
| X7 pharmacy breadth | 1 | `FTP_DISTINCT_PHARMACIES_12M` | Made |
| X8 trend | 1 | `FTP_FILLS_3M_VS_PRIOR_3M` | Made |

Types: counts long / int, shares and averages double; 0 unexpected columns. The 10 X4 / X5 columns are double.

E8 (proxy model, 25 Nov): X4 +0.0000 / +0.0001 and X5 +0.0000 / +0.0000 test / holdout AUC vs E1, below the +0.002 keep rule: both DROP from the model, columns still written (DEC-F14).

## 6a. V7 closure (payer codes, `OTHR_CVRG_CD`)

| Item | Detail |
| --- | --- |
| Readiness V7 | Profile `OTHR_CVRG_CD` and agree the meaning of each code before X5 is built |
| What was done (25 Nov 2026) | Every value profiled in both UC claims tables; counts add up to the row counts (FTP 106,211, copay 106,721); 0 nulls, 0 blanks |
| FTP codes | `00` 101,332 claims (95.41%, 15,668 prescribers); `03` 2,483 (2.34%, 1,272); `01` 2,396 (2.26%, 853) |
| Copay codes | `08` 87,788 (82.26%, 8,475); `03` 18,933 (17.74%, 2,495) |
| Meanings used | NCPDP Telecommunication Standard, Other Coverage Code (308-C8): `00` not specified, `01` no other coverage, `03` other coverage billed, claim rejected, `08` billing for patient's share only |
| Disclaimer | The meanings are an outside reference only: **not** derived from the data and **not** confirmed by the market access / data team (Q2 stays open for that confirmation). Codes and counts are from the data |
| Primary-payer BIN | FTP: filled only on code `03` claims (2,482 of 2,483; 85 BINs), so no BIN feature for FTP. Copay: on every claim (268 BINs). Full list in `qc/v7_payer_bin_mapping_worksheet.csv` (354 rows, `PAYER_CATEGORY` empty for the market access team) |
| Time pattern | FTP code `03` fills by year: 2021 170, 2022 1,648, 2023 604, 2024 61, 2025 0, 2026 0. Code `01` present through 2026. Cause of the change unknown (F10) |
| Result | X5 built on codes `01` / `03` (DEC-F16); independent c28 recount 297 / 0 = output |
| Status | **CLOSED** (25 Nov 2026, user decision) in the notebook header and decision log. Note: the V7 check in the notebook code still prints `OPEN`, so the QC log `qc/ftp_feature_checks` keeps P0 OPEN = 2 (V7, V10) until that check is changed |

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

X4 / X5 (added 25 Nov 2026): % over 8,252,328 rows of the 25 Nov output; 0 nulls in all 10; min / max 0 / 1 for all except U (0 / 0).

| Feature | % zero | % non-zero | min / max | % non-zero train / test / holdout / c28 | Flag |
| --- | --- | --- | --- | --- | --- |
| `FTP_PAT_AGE_18_44_SHARE_12M` | 99.898 | 0.102 | 0 / 1 | 0.102 / 0.096 / 0.102 / 0.104 | > 99.5% zero |
| `FTP_PAT_AGE_45_64_SHARE_12M` | 99.511 | 0.489 | 0 / 1 | 0.490 / 0.477 / 0.491 / 0.495 | > 99.5% zero |
| `FTP_PAT_AGE_65_74_SHARE_12M` | 99.393 | 0.607 | 0 / 1 | 0.614 / 0.555 / 0.574 / 0.576 | |
| `FTP_PAT_AGE_75P_SHARE_12M` | 99.683 | 0.317 | 0 / 1 | 0.315 / 0.324 / 0.333 / 0.337 | > 99.5% zero |
| `FTP_PAT_AGE_UNKNOWN_SHARE_12M` | 99.712 | 0.288 | 0 / 1 | 0.280 / 0.324 / 0.353 / 0.358 | > 99.5% zero |
| `FTP_PAT_GENDER_MALE_SHARE_12M` | 99.157 | 0.843 | 0 / 1 | 0.843 / 0.826 / 0.862 / 0.867 | |
| `FTP_PAT_GENDER_FEMALE_SHARE_12M` | 99.304 | 0.696 | 0 / 1 | 0.691 / 0.707 / 0.735 / 0.743 | |
| `FTP_PAT_GENDER_U_SHARE_12M` | 100.000 | 0.000 | 0 / 0 | 0 / 0 / 0 / 0 | constant (no U in FTP data) |
| `FTP_NO_OTHER_CVRG_SHARE_12M` | 99.947 | 0.053 | 0 / 1 | 0.052 / 0.063 / 0.066 / 0.068 | > 99.5% zero |
| `FTP_OTHER_CVRG_REJECTED_SHARE_12M` | 99.985 | 0.015 | 0 / 1 | 0.018 / 0.000 / 0.000 / 0.000 | > 99.5% zero; training only |

65-74, male and female are 99.2 - 99.4% zero, just under the 99.5% flag line, so they are not flagged.

## 8. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature | In 752? (SHAP rank, % SHAP) | NBA 3.1 feature | Status | Reason |
| --- | --- | --- | --- | --- |
| `TOTAL_RX_FTP_IN_LAST_1_MONTH` | 467, 0.0445% | `FTP_FILLS_1M` | replaced | fill date, claim grain, new name (D6) |
| `TOTAL_RX_FTP_IN_LAST_4_MONTH` | 632, 0.0218% | `FTP_FILLS_3M` / `FTP_FILLS_6M` | replaced | 4M window not in D3 (1 / 3 / 6 / 12M) |
| `TOTAL_RX_FTP_IN_LAST_6_MONTH` | 662, 0.0163% | `FTP_FILLS_6M` | replaced | as 1M |
| `TOTAL_RX_FTP_IN_LAST_3_MONTH` | 664, 0.0159% | `FTP_FILLS_3M` | replaced | as 1M |
| 3.0 `TOTAL_RX_FTP_IN_LAST_2/5_MONTH`, `PCT_*`, running total | not in 752 | - | dropped | not in D3 windows / readiness drop list |

Summary: 4 FTP features in the 752 (0.0986% of SHAP): 4 replaced, 0 skipped. New in 3.1 (25): `FTP_HAS_ANY_12M`, `FTP_FILLS_12M` (+ cap, band), 4 new-Rx windows, recency, 7 extended (X1-X3, X6-X8), 8 X4 patient-mix shares and 2 X5 payer-mix shares (no 3.0 counterpart). None is on the model-recommended list after G2 (F7).

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
| F9 | G3 failed on O2 / O5 owners and no scheduled job. Now: O2 and O5 owned by the NBA team, which also checks data drift (Q14); the scheduled job is deferred to the ops phase of the project (user, 25 Nov 2026), so G3 closes on O1 - O5 | note | NBA team (O2, O5, drift); ops phase (job) | CLOSED |
| F10 | X4 / X5 (25 Nov): 7 of the 10 columns > 99.5% zero (all except 65-74, male, female); `FTP_PAT_GENDER_U_SHARE_12M` is constant 0 (kept so FTP and copay share one schema); `FTP_OTHER_CVRG_REJECTED_SHARE_12M` is 0 in every test / holdout row because code `03` stops after 2024 (cause unknown); the unknown-age band likely holds most 80+ patients (ages stop at 79, not confirmed). E8: both DROP | note | Feature selection to drop the constant / training-only columns; ask the data team about code `03` and age 80+ with Q2 | OPEN |

## 11. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 14 / 14 (with the actions above) |
| O2, O5 and drift review (NBA team) / date | Owner: NBA team. First check run by Genie Code 25 Nov 2026 (Q14, PASS); NBA team review: pending |
| Scheduled job | Deferred to the ops phase of the project (G3 closed without it) |
| QC by / date | Genie Code for Wenjie Chen, 24 Nov 2026 |
| Reviewed by / date | |
| Next | 02 Copay (`copay_feature`) |
