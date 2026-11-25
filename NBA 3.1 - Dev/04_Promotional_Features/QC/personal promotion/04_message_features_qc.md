# QC 04: Key message features, NBA 3.1

**QC status:** DONE, 20 Nov 2026 (channel 4 of 6)  
**Verdict:** PASS with actions. The feature values are correct (Q9: 15 of 15 recomputed values match) and the denominator equals the F2F block exactly (Q12). V4 is still not passed (T2 89.9%, T3 open), so the features stay gated candidates.  
**QC run:** 20 Nov 2026, serverless, on the output of the last notebook run (6 Nov 2026). The notebook was not re-run.

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `personal_promotional_features/Message features/message_feature` (21 cells) |
| Client summary | `Message features/message_feature_nba_3_1_client_summary.md` |
| Readiness file | `40_field_activity_nba_3_1_readiness_plan.md`: Phase 0 V4, Phase 2 M1 to M3 |
| Output | `kerendia_nba_3_1_volume/notebook_output/field_activity_nba_3_1/kerendia_nba_3_1_hcp_model_field_message_features.parquet` |
| Universe / cohorts | `HCP_Universe_without_call_hcps/` x `cohorts/promotional/cohorts.parquet`; `EXCLUDE_PROVIDER_IDS = ["0"]` |
| Expected shape | 3 features (`FLD_CKD_FIRST_SHARE_6M`, `FLD_HF_FIRST_SHARE_6M`, `FLD_KEYMSG_AVAILABLE`) + keys, 294,726 x 28 rows |
| NBA 3.0 counterpart | None (no message features in NBA 3.0); all 3 are new |

## 2. QC checklist

| # | Check | How | Pass when | Status |
| --- | --- | --- | --- | --- |
| Q1 | HCP universe | Distinct PROVIDER_ID vs universe minus `0`; rows; duplicates; extra HCPs | Same HCP set, 0 duplicates | PASS |
| Q2 | Cohorts and windows | Lookback ends; 6M = 182 days; no call after lookback end | All match | PASS |
| Q3 | All features made | Columns vs config vs readiness M1 to M3 (M2 and dual share dropped on purpose) | 3 features; drops documented | PASS |
| Q4 | Business rules | Fill section 4 | All match | PASS (1 to agree) |
| Q5 | Data sources | Notebook: `FACT_CALL`, `FACT_CALL_DETAIL`, `FACT_CALL_KEY_MESSAGE`, `MAP_CUSTOMER_XREF`; readiness: `field_interaction_message` from `FACT_CALL_KEY_MESSAGE` | Same; same Kerendia and record-class rules as F2F | PASS |
| Q6 | Fill rate | % null, % zero, % non-zero per feature, per cohort | Codes appear only from c14; full 6M window from c21; share null vs 0 when no interaction is a documented choice | PASS (2 notes) |
| Q7 | NBA 3.0 model coverage | Confirm no message feature in the 752 | 0 found | PASS |
| Q8 | Preserved vs new | All new; record in section 5 | Done | PASS |
| Q9 | HCP trace | Section 6, at least 5 HCPs | Final value = output | PASS (15 / 15) |
| Q10 | Invariants | Shares in [0, 1]; CKD + HF share can exceed 1 only by the dual-code calls (29,808); `FLD_KEYMSG_AVAILABLE` 0 / 1 | 0 unexplained violations | PASS |
| Q11 | V4 gate | Share of Kerendia interactions with a position code per month / territory (about 90% borderline) | V4 result written down | PASS (V4 itself not passed) |
| Q12 | Cross-block | Denominator = Kerendia `HCP_INTERACTION` from F2F block | Same counts as F2F 6M | PASS |
| Q13 | Reproducibility and docs | Same schema on re-run; summary current | No stale text | PASS (1 note; re-run not done) |

## 3. Evidence log

| # | Result (numbers) | Where (cell / query) | Notes |
| --- | --- | --- | --- |
| Q1 | 8,252,328 rows = 294,726 HCPs x 28; every cohort 294,726 rows; 0 duplicate keys; `HCP_COHORT_ID` = `PROVIDER_ID_COHORT_ID`; 0 HCPs outside the universe; only `0` missing | QC session; cell 15 asserts | Same mapping as other blocks |
| Q2 | 28 cohorts match cohorts.parquet (0 mismatches). Window (END - 182, END], asserted in cell 12. `DATA_START` 2023-12-01 before the c1 window start (2023-12-19) | Cells 4, 5, 12 | |
| Q3 | 3 features in config order: `FLD_CKD_FIRST_SHARE_6M`, `FLD_HF_FIRST_SHARE_6M` (double), `FLD_KEYMSG_AVAILABLE` (int); 0 nulls / NaN. M2 (materials) and the dual share are dropped, with reasons in cell 2 | QC session; cell 2 | |
| Q4 | Section 4 | Cells 4, 6, 12, 13 | |
| Q5 | `FACT_CALL`, `FACT_CALL_DETAIL` (`SOURCE_PROD_NM = 'Kerendia'`), `FACT_CALL_KEY_MESSAGE`, `MAP_CUSTOMER_XREF`; HCP_INTERACTION = submitted, not BHO, not medical (record type or Finerenone), no account / office key message (5 names). `message_feature` cell 4 writes this output path (`46_` not opened) | Cell 6 | Same rules as F2F; Q12 confirms |
| Q6 | 0 nulls. % rows > 0 (all / train / test / holdout / c28): CKD share 6.36 / 4.85 / 14.76 / 16.00 / 16.18; HF share 3.35 / 2.70 / 6.93 / 7.51 / 7.62; M3 8.66 / 6.56 / 20.52 / 21.98 / 22.20. Codes: c1 to c12 all 0; c13 4 HCPs (June 2025 `P1 KER` codes); c14 2,842; c15 21,358; c28 63,081. M3 = 1 from c15 (14,789) to c28 (65,419). Mean HF share among M3 = 1 is 0.370 at c15 and 0.288 to 0.290 at c25 to c28 | QC session | Note 1: share 0 means either no interaction or interactions without a position-1 code (no null). Note 2: train / test drift is large because codes exist only from c13 / c14 |
| Q7 | No feature in the 752 with `KEYMSG`, `KEY_MSG`, `MESSAGE`, `CKD_FIRST`, `HF_FIRST` or `POSITION` in its name | `Shap_Importances.csv` | Name search |
| Q8 | Section 5: 3 new | | |
| Q9 | 5 HCPs at c28 x 3 features = 15 values, recomputed from raw Snowflake (calls + key messages): 15 match (section 6) | QC session | Low-entry territory list from the notebook's `field_interaction_message.parquet` (not independent) |
| Q10 | Shares outside [0, 1]: 0. M3 only 0 / 1. CKD + HF share > 1: 55,544 rows (= cell 2; calls with both codes). Share > 0 with M3 = 0: 27,808 rows, all explained by the M3 rule: (A) 2,846 rows / 2,842 HCPs in c13 to c14 (cohort ends before 2025-08-01, so M3 is always 0); (B) 16,001 rows / 8,002 HCPs in c15 to c20 whose coded calls in the window are all from June to July 2025, before `FULL_CODE_START` (c15 8,002, c16 2,819, c17 1,754, c18 1,344, c19 1,179, c20 903); (C) 8,961 rows / 2,472 HCPs in c15 to c28 where every call from Aug 2025 is in a low-entry territory (19 at c15, 320 to 894 a cohort from c16). 0 rows in any other group. M3 recomputed from the message base with the cell 12 / 13 rule matches the output on all 1,534,508 HCP x cohort rows with an interaction | QC session | |
| Q11 | V4 on the message base. Monthly position-code share: 0.3% (Jun 2025), 52.2% (Jul 2025), 88.3 to 89.4% (Aug to Dec 2025), 88.8 to 90.7% (2026). `HAS_IND` (incl. the material) reads 92.7 to 97.2% in 2026. T1 (lowest 2026 month >= 80%): 88.8%, pass. T2 (>= 90% of territories at >= 70%): 89.9% of 746 territories, fail by 0.1 point; 69 territories below 50% (51,745 interactions). T3 / K2 and the process review not checked here | QC session | Same as cell 2 |
| Q12 | Base: Y1 472,236 calls / 77,308 doctors (= 4 Nov reference), Y2 606,357 / 96,719. At c28 the 6M Kerendia interaction count per HCP equals F2F `FLD_INT_TOTAL_6M` for all 294,726 HCPs (325,956 calls in both) | QC session | |
| Q13 | Cell 2 and cell 18 figures match the QC (T1 88.8%, T2 89.9%, 69 territories, 55,544 rows, Y1 / Y2 bases). Note: cell 2 says 11 of 24 training cohorts (c14 to c24) have codes; c13 also has 4 HCPs. Client summary not read. Not re-run | Cells 2, 18 | |

## 4. Business rules to verify (readiness vs notebook)

| Rule | Readiness file says | Notebook does (cell) | Match |
| --- | --- | --- | --- |
| CKD-first / HF-first | Indication of the main (position 1) message (PN-1) | Cell 6: `CKD_FIRST` / `HF_FIRST` per call; cell 13: share = position-1 CKD (or HF) calls / calls with any position-1 code, 0 if none | Yes (shares, not the plan's any-CKD / any-HF flags; documented in cell 2) |
| Code names | Position-1 codes in Jun to Jul 2025 named `P1 KER CKD/HF` | Cell 6: `%Position 1 KER CKD%` or `P1 KER CKD%` (same for HF) | Yes |
| Exclusions | `%KER CKD%` must not match material `KER CKD/HF Digital MVA Refresh Dual Indication`; `%Dual Indication%` is a visual aid, not a message | Features use position codes only; `HAS_IND` (with materials) is used only in the gate diagnostics; dual not built | Yes |
| M3 available flag | HCP had a Kerendia interaction from 2025-08-01 in a territory that is not low-entry | Cell 13: any call on or after 2025-08-01 in a territory that is not low-entry. Low-entry = >= 50 calls from Aug 2025 in that cohort's window and position-code share < 50% (cell 12, no look-ahead) | Yes |
| M2 materials | Dropped (V4) | Not built | Yes |
| Share default | (not stated) | 0.0 when no position-1 code, also when no interaction | To agree (0 vs null) |

## 5. NBA 3.1 feature list (all new)

| NBA 3.1 feature | Definition | Status |
| --- | --- | --- |
| `FLD_CKD_FIRST_SHARE_6M` | Share of Kerendia HCP interactions with a position-1 code in (END - 182, END] whose position-1 code is CKD; 0 if none | New |
| `FLD_HF_FIRST_SHARE_6M` | Same for HF; can sum with CKD to > 1 when a call has both codes | New |
| `FLD_KEYMSG_AVAILABLE` | 1 if a Kerendia HCP interaction on or after 2025-08-01 in the window was in a territory that is not low-entry, else 0 | New |

No message feature in NBA 3.0 or the 752 (Q7).

## 6. HCP trace (step-by-step recompute)

HCPs: mostly CKD-first, mostly HF-first, both codes on one call, Kerendia interactions with no code, low-entry territory (flag 0).

| Step | What | Value |
| --- | --- | --- |
| 1 | PROVIDER_ID to BHID(s) | |
| 2 | Kerendia `HCP_INTERACTION` calls in 6M (denominator) | |
| 3 | Key message rows on those calls | |
| 4 | After code / exclusion rules (CKD-first, HF-first) | |
| 5 | Shares | |
| 6 | Final feature value | |
| 7 | Match | |

**Results (20 Nov 2026), c28, window 2026-03-20 to 2026-09-17.** Raw `FACT_CALL` + `FACT_CALL_DETAIL` + `FACT_CALL_KEY_MESSAGE` per BHID; HCP_INTERACTION and code rules applied in pandas.

| Case | PROVIDER_ID / BHID | Raw calls | Kerendia HCP interactions | With position-1 code | CKD-1 / HF-1 / both | Calls in low-entry territory | CKD share | HF share | M3 | Match |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 Mostly CKD-first | 7614515 / BH11333446 | 6 | 6 | 6 | 5 / 1 / 0 | 0 | 0.8333 | 0.1667 | 1 | 3 / 3 |
| 2 Mostly HF-first | 11916008 / BH12841306 | 12 | 9 | 9 | 1 / 8 / 0 | 0 | 0.1111 | 0.8889 | 1 | 3 / 3 |
| 3 Both codes on one call | 10139434 / BH11943639 | 7 | 7 | 7 | 7 / 3 / 3 | 0 | 1.0000 | 0.4286 | 1 | 3 / 3 |
| 4 Interactions, no code | 10100573 / BH11863138 | 10 | 5 | 0 | 0 / 0 / 0 | 2 | 0 | 0 | 1 | 3 / 3 |
| 5 Low-entry territory | 16757321 / BH27509779 | 10 | 2 | 2 | 2 / 0 / 0 | 2 | 1.0000 | 0 | 0 | 3 / 3 |

Case 4: 2 of 5 calls are in low-entry territories, the others are not, so M3 = 1. 67 low-entry territories at c28.

## 7. Points found during QC

* V4: T1 passes (88.8%), T2 fails by 0.1 point (89.9%); K2 (always-CKD teams), K3 and the process review are still open (not checked here).
* Output path is set in `message_feature` cell 4; `46_` was not checked further.
* Codes appear in c13 (4 HCPs, June 2025 `P1 KER` codes), not only from c14.
* Shares are 0 (not null) when there is no position-1 code.
* 24,962 rows in c15 to c28 have a share but M3 = 0: 16,001 because the only coded calls are from June to July 2025 (c15 to c20), 8,961 because all calls from Aug 2025 are in low-entry territories. So M3 = 0 does not always mean "no codes"; the model sees CKD / HF shares on rows it is told have no reliable code data.
* Training has codes in only c13 to c24; c1 to c12 are all 0, so train vs test fill differs a lot (M3 6.56% vs 20.52%).

## 8. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 13 / 13 |
| Open (outside this QC) | V4 thresholds (K1), K2 / K3, process review with Maria Kontorinakis |
| Decisions (to agree) | (a) Share default 0 vs null when no code. (b) Use only with `FLD_KEYMSG_AVAILABLE` and test in E3 / E6. (c) Set the shares to 0 (or null) when M3 = 0 (27,808 rows), or keep them |
| Doc fix | Cell 2: codes start in c13 (4 HCPs), not c14 |
| Fixes made to the notebook | None (QC was read-only) |
| Ready for modelling | Yes, as gated candidates (V4 not passed) |
| Next channel | 05 Samples |
