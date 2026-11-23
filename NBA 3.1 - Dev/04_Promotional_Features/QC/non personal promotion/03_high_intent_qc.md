# QC 03: High-intent signal (family 3) features, NBA 3.1

**QC status:** DONE, 12 / 13 PASS (channel 3 of 5, non-personal promotion); Q13 PARTIAL: client summary is stale (P7, docs only)  
**Verdict:** READY for modelling. The final output matches an independent recompute in all 28 features and all 8,252,328 rows (0 differences)  
**Final output:** written 23 Nov 2026 (`PULL_DT` 2026_11_23). RAR staged in `_stage_rar_requests.parquet` (1,406 requests, pulled 2026-11-23 08:00, data to 17 Nov 2026); claims Delta version 3 (`PULL_DT` 2026-11-19, months to Oct 2026) recorded in `run_info.json`; notebook QC cell 19 / 19 PASS. All results below are on this output

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `non_personal_promotional_features/High_Intent_Signal_Features/25_Features_High_Intent_Signals_NBA31` (15 cells) |
| Client summary | `High_Intent_Signal_Features/High_Intent_Signal_Features_Client_Summary.md` |
| Design / readiness | `52_digital_feature_families_nba30_vs_nba31.md` section 3.3 |
| Sources | Request-a-Rep: Snowflake `PHCDW.PHCDW_CDM.RPT_DIGITAL_RAR_TAB` (`BRAND_NAME` like Kerendia); New Writer: `kerendia_claims_monthly_from_raw_fct_rx`; Impiricus SMS: MMX (`SRC_SYS_CD = IMPIRICUS`, tactic `SMS`) |
| Output | `{OUT_DIR}/kerendia_nba_3_1_hcp_model_high_intent_features.parquet` |
| Universe / cohorts | `HCP_Universe_without_call_hcps/` x `cohorts/promotional/cohorts.parquet` (c1 to c28) |
| Doctor key | `BH_ID` / NPI -> `PROVIDER_ID` via `SOURCE_PROVIDER_BHID_NPI_MAPPING` |
| Expected shape | 28 fixed features + 9 keys = 37 columns; rows = universe x 28 = 8,252,328 |
| NBA 3.0 counterpart | None (new family) |
| NBA 3.0 final model | MLflow run `f583bcbc9d56477fae983d44c16f8c70`, 752 features |

## 2. QC checklist

| # | Check | Pass when | Final result | Status |
| --- | --- | --- | --- | --- |
| Q1 | HCP universe | Same HCP set, 0 duplicates | 294,726 doctors; 8,252,328 rows = 294,726 x 28; `HCP_COHORT_ID` unique; every universe doctor present, none outside. RAR: 623 of 1,406 requests reach a universe doctor (BH_ID 547, NPI 76); the rest come from doctors outside the universe (P2) | PASS |
| Q2 | Cohorts and windows | All match | `DATASET`, `PREDICTION_MONTH`, `SVC_DT` = cohort file for all 28 cohorts; RAR windows `(END - w, END]`; New Writer uses the last complete month (END on the 17th -> previous month). `RAR_HISTORY_MONTHS` / `MMX_HISTORY_MONTHS` 0 for c1 to c8 (data from 1 Jan 2025), 12 from c20 | PASS |
| Q3 | All features made | No missing / extra column | 37 columns = `expected_schema.json` (9 keys + 28 features = manifest): RAR_ALL 8, RAR_CALL 3, RAR_SAMPLE 3, RAR_IREP 2, RAR_HQ 2, NEW_WRITER 5, SMS 5 | PASS |
| Q4 | Business rules | All match | All 9 rules in section 4 match (shares after P1) | PASS |
| Q5 | Data sources | Matches design | RAR reads only hashed `TRANSACTION_ID`, BH_ID, NPI, dates, request type and follow-up columns (no PII); claims `kerendia_claims_monthly_from_raw_fct_rx` (Jul 2021 to Oct 2026, raw FCT_RX, not LAAD v6); SMS from MMX `IMPIRICUS` + tactic SMS | PASS |
| Q6 | Fill rate | Nulls only where designed; near-constant flagged | NULLs only in the 4 follow-up shares, and only when there is no 12M request; near-constant features flagged (P4); fill table in section 3 | PASS |
| Q7 | NBA 3.0 model coverage | Mapped or none | 0 of the 752 match RAR / SMS / writer; closest are the NBRx claim features | PASS |
| Q8 | Preserved vs new | Every feature labelled | 28 / 28 new | PASS |
| Q9 | HCP trace | Final value = output | Full-grid recompute (all 8,252,328 rows, 28 features) from the staged RAR, claims Delta v3 and MMX: 0 differences | PASS |
| Q10 | Invariants | 0 violations | 0 violations: window nesting, follow-ups <= requests, flag consistency, share NULL only without a request, 999 sentinels, ever-writer never 1 -> 0 from c27 to c28. 1 boundary row explained (P6) | PASS |
| Q11 | Reconciliation | Within expected range | 1,406 requests (2025: 570, 2026: 836) vs 1,385 in the design (4 more weeks of data); follow-ups call 433, samples 295, iRep 10, HQ email 0. New writers: 64 months with no gap, 85,653 in total; cohort flag totals = monthly counts in all 28 cohorts | PASS |
| Q12 | Comparison with the Rx block | Consistent | All 8,252,328 rows match `kerendia_prior_writing` on `HCP_COHORT_ID`; 0 contradictions between new-writer flags and TRx | PASS |
| Q13 | Reproducibility and docs | No stale text | RAR staged, `run_info.json` written, notebook header updated; client summary stale (P7) | PARTIAL |

## 3. Final results

| Item | Result |
| --- | --- |
| RAR requests | 1,406 (2025: 570, 2026: 836; to 17 Nov 2026); 623 reach a universe doctor. Request types: samples 597, contact by rep 524, empty 188, news 54, other 43 |
| RAR follow-ups | Call 433, samples 295, iRep 10, HQ email 0 (columns empty in the source) |
| Follow-up shares | NULL only when there is no 12M request; with a request and no follow-up the share is 0 (call 1,236, sample 1,976, iRep 3,503, HQ 3,577 rows) |
| Open requests | 48 doctors at the c28 end (`rar_open_requests_latest_cohort.parquet`) |
| New writers | 64 months Jul 2021 to Oct 2026, no missing month, 85,653 writers. 2024: 1,162 to 1,523 a month; 2025: 1,340 to 1,906; 2026 Jan to Sep: 1,811 to 2,184. Oct 2026 (1,406) is partial and used by no cohort; c28 uses up to Aug 2026 |
| Impiricus SMS | 5 months only (Mar, Apr, Jun, Nov, Dec 2025); none after Dec 2025, so `SMS_*_3M` is 0 from c22 |
| Overlap with the Rx block | Not duplicates: 379,104 rows are ever-writers with no TRx in 12 months (lapsed writers); 287,511 of 488,575 new-writer-12M rows (58.8%) have NBRx 12M > 0 (NBRx is a patient-level new-to-brand measure, not the doctor's first Rx) |

### Fill rates (final output, all 28 cohorts, 8,252,328 rows)

| Feature | Null % | Zero % | Value % | 999 rows | Max | Note |
| --- | --- | --- | --- | --- | --- | --- |
| `RAR_COUNT_3M` / `6M` / `12M` | 0 | 99.983 / 99.971 / 99.957 | 0.017 / 0.029 / 0.043 | | 12 | Very sparse |
| `RAR_LAST_6M_FLAG` | 0 | 99.971 | 0.029 | | 1 | |
| `DAYS_SINCE_LAST_RAR` | 0 | 0 | 0.043 | 8,248,751 | 999 | |
| `RAR_OPEN_REQUEST_FLAG` | 0 | 99.992 | 0.008 | | 1 | |
| `RAR_TYPE_SAMPLES_FLAG` / `CONTACT_BY_REP` | 0 | 99.965 / 99.995 | 0.035 / 0.005 | | 1 | |
| `RAR_CALL_COUNT_12M` / share | 0 / 99.957 | 99.972 / 0.015 | 0.028 / 0.028 | | 4 / 1 | Share NULL only with no 12M request (P1) |
| `RAR_SAMPLE_COUNT_12M` / share | 0 / 99.957 | 99.981 / 0.024 | 0.019 / 0.019 | | 4 / 1 | P1 fixed |
| `RAR_IREP_COUNT_12M` / share | 0 / 99.957 | 99.999 / 0.042 | 0.001 / 0.001 | | 1 / 1 | Near-constant (P4) |
| `RAR_HQ_COUNT_12M` / share | 0 / 99.957 | 100 / 0.043 | 0 / 0 | | 0 / 0 | Constant (source empty, P4) |
| `RAR_OPEN_NO_CALL_FLAG` / `NO_SAMPLE` | 0 | 99.992 / 99.988 | 0.008 / 0.012 | | 1 | |
| `NEW_WRITER_LAST_3M` / `6M` / `12M_FLAG` | 0 | 98.401 / 96.887 / 94.080 | 1.599 / 3.113 / 5.920 | | 1 | |
| `KERENDIA_WRITER_EVER_FLAG` | 0 | 80.157 | 19.843 | | 1 | |
| `MONTHS_SINCE_FIRST_KERENDIA_RX` | 0 | 0.543 | 19.300 | 6,614,786 | 999 | |
| `SMS_SENT_3M` / `12M` | 0 | 99.574 / 98.619 | 0.426 / 1.381 | | 7 / 8 | 3M is 0 from c22 on (expected: no SMS after Dec 2025); 12M non-zero to c28 |
| `SMS_ENGAGED_3M` / `12M_FLAG` | 0 | 99.995 / 99.980 | 0.005 / 0.020 | | 1 | Near-constant |
| `DAYS_SINCE_LAST_SMS` | 0 | 0.001 | 1.380 | 8,138,361 | 999 | |

## 4. Business rules (design vs notebook)

| Rule | Design | Notebook | Match |
| --- | --- | --- | --- |
| RAR leakage | Follow-up counts only if its date is >= request date and <= cohort end | `fu()` in cell 9: date not NULL, >= request, <= END; follow-ups before the request dropped in cell 4; self-test covers a call after END | Yes |
| Open request | At most 90 days (`RAR_OPEN_DAYS`): request in last 90 days without that follow-up by END | `datediff(END, request) < 90` and no follow-up by END; open flag uses any type, `OPEN_NO_CALL` / `NO_SAMPLE` per type | Yes (90 days can exceed the 3M window, P6) |
| Request type | Separate features (`RAR_TYPE_SAMPLES_FLAG`, `RAR_TYPE_CONTACT_BY_REP_FLAG`) | `contains('SAMPL')`, `contains('CONTACT BY REP')` on 12M requests | Yes |
| Shares | `RAR_t_COUNT_12M / RAR_COUNT_12M`, NULL only if no request | `when(RAR_COUNT_12M > 0, coalesce(count, 0) / RAR_COUNT_12M)`; self-test and QC check added | Yes (after P1 fix) |
| PII | Only IDs, dates, types, follow-up columns; `TRANSACTION_ID` SHA-256 hashed in Snowflake | Query in cell 4 | Yes |
| Doctor key | BH_ID / NPI -> `PROVIDER_ID` | BH_ID map, then OE BH_ID -> NPI fallback, then NPI; cell 5 prints the customer-master reason for unmapped requests | Yes; 44% coverage is the population, not a mapping gap (P2) |
| New Writer | First month with `TRX_KERENDIA_OVERALL > 0`; complete months only | `LAST_M = trunc(END) - 1 month`; flags on `FIRST_RX_M`; months since = `months_between(LAST_M, FIRST_RX_M)`; 999 if never | Yes |
| Impiricus SMS | Fixed schema; no rows after Dec 2025 | Sum of exposure, engagement flag, days since; 12M window | Yes (3M = 0 from c22; data gaps, P5) |
| Formulary wins | Not built (source missing) | Not built | Yes |

## 5. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature | In the 752 (rank) | NBA 3.1 feature | Status | Reason |
| --- | --- | --- | --- | --- |
| (none) | 0 of 752 match RAR / SMS / writer | All 28 features | New | Family 3 is new. NBA 3.0 NBRx claim features (rank 2, 5, ...) are related to the new-writer flags; check overlap in the combine step |

## 6. Independent recompute (final output)

Independent SQL recompute of all 28 features on the full grid (all 8,252,328 rows instead of 5 doctors), from `_stage_rar_requests.parquet`, claims Delta v3 and MMX, with its own mapping, windows, follow-up date gate, 90-day open rule, new-writer rule and SMS sums.

| Scope | Result |
| --- | --- |
| Rows | 0 rows only in the output, 0 only in the recompute |
| Features | 0 differences in all 28 features |
| Boundary case | 1 row (doctor 7165019, c24): open flag 1 with 3M count 0, because the request was 89 days before END and the 3M window is 89 days (P6) |

## 7. Fixes applied and notes

| # | Problem found | Fix | Final result | Status |
| --- | --- | --- | --- | --- |
| P1 | Follow-up shares were NULL in many rows with requests and no follow-up, so "asked, not followed up" looked like "never asked" | Cell 9: share = `coalesce(count, 0) / RAR_COUNT_12M` when requests > 0; self-test and cell 12 QC check (share NULL only when `RAR_COUNT_12M` = 0) | 0 NULL shares in rows with requests | FIXED |
| P3 | RAR was read live from Snowflake and not staged; Snowflake changed after 13 Nov and the claims table was rewritten on 19 Nov, so the output could not be reproduced | Cell 4 stages RAR in `_stage_rar_requests.parquet` (hashed IDs, dates, types only; `REFRESH_RAR = False` rebuilds without Snowflake); cell 6 records the claims Delta version; cell 11 writes `run_info.json` | Recompute from the stage: 0 differences | FIXED |
| P2 | 783 of 1,406 requests (55.7%) do not reach a universe doctor | Searched every mapping source in Databricks and Snowflake (`DIM_CUSTOMER`, `DIMHCPPROF`, `MAP_CUSTOMER_XREF`, OE map and others); none links them to universe doctors. Cell 5 prints the split every run | The requesters are outside the universe (694 in the customer master with no NPI, 83 with an NPI outside the universe, 6 not in the master); mapping kept | EXPLAINED |
| P4 | Near-constant: `RAR_HQ_COUNT_12M` and share always 0 / NULL; iRep 0.001%; all RAR features <= 0.043% non-zero | Keep the schema; drop HQ (and probably iRep) RAR features in feature selection | | NOTE |
| P5 | SMS has 5 months of data and 122 duplicate doctor x date rows (summed) | Ask the MMX owner (same question as channel 1 P5) | Gaps read as "no SMS" | NOTE |
| P6 | 90-day open window can be longer than the 3M window (89 days) | None | 1 row | NOTE |
| P7 | Client summary `High_Intent_Signal_Features_Client_Summary.md` (6 Nov 2026) is stale: old counts (1,385 requests, 411 calls, 84,389 writers, 49 open), says write / QC not yet run, suggests a mapping refresh that P2 shows is not needed, and does not mention the P1 share rule or the staged RAR | Update the summary to the 23 Nov run | | OPEN (docs) |

## 8. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 12 / 13 (Q13 PARTIAL: client summary stale, P7) |
| Fixes made | P1 (cell 9, share rule), P3 (cells 4, 6, 11: staged RAR, `run_info.json`), P2 diagnostic (cell 5), notebook header (cell 1); final output written 23 Nov 2026 |
| Open issues | P7 (client summary, docs only). Notes for modelling: P4 (near-constant RAR HQ / iRep), P5 (SMS gaps), P6 (90-day boundary) |
| Ready for modelling | Yes |
| Next channel | 04 DTC |
