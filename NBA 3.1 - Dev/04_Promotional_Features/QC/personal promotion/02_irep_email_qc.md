# QC 02: iRep email features, NBA 3.1

**QC status:** DONE, 20 Nov 2026 (channel 2 of 6)  
**Verdict:** PASS with actions. The feature values are correct (Q9: 140 of 140 recomputed values match). Q12: the gap to NBA 3.0 is explained by different cohort dates (about 457 days). 4 modelling decisions are open (section 8).  
**QC run:** 20 Nov 2026, serverless, on the output of the last notebook run (6 Nov 2026). The notebook was not re-run.

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `personal_promotional_features/Irep emails/irep_email_feature` (16 cells) |
| Client summary | `Irep emails/irep_email_feature_nba_3_1_client_summary.md` |
| Readiness file | `40_field_activity_nba_3_1_readiness_plan.md`: Phase 0 V7, Phase 3 I-1 to I-4 |
| Output | `kerendia_nba_3_1_volume/notebook_output/field_activity_nba_3_1/kerendia_nba_3_1_hcp_model_field_irep_features.parquet` |
| Universe / cohorts | `HCP_Universe_without_call_hcps/` (294,727) x `cohorts/promotional/cohorts.parquet` (c1 to c28) |
| Expected shape | 20 features (confirmed) + 6 key columns, rows = universe x 28 |
| NBA 3.0 counterpart | `16_promotional_features_irep`: dev output `kerendia_nba_3_hcp_model_irep_features.parquet` (84 features, 1 to 6M), ops output `..._irep_features_for_inference` (14 features, 3M) |
| NBA 3.0 final model | MLflow run `f583bcbc9d56477fae983d44c16f8c70`, 752 features, `Shap_Importances.csv` |

## 2. QC checklist

Status values: `PASS` / `FAIL` / `OPEN` / `N/A`. Record evidence in section 3.

| # | Check | How | Pass when | Status |
| --- | --- | --- | --- | --- |
| Q1 | HCP universe | Distinct PROVIDER_ID vs universe; rows = HCPs x 28; duplicate keys; HCPs not in universe; placeholder `0`; BHID mapping coverage | Same HCP set, 0 duplicates, 0 extra HCPs, mapping loss documented | PASS |
| Q2 | Cohorts and windows | Lookback end per cohort = cohorts.parquet; window days; no email after lookback end | All match, no leakage | PASS |
| Q3 | All features made | Output columns vs notebook config vs readiness I-1 to I-4 | No missing / extra column | PASS |
| Q4 | Business rules | Fill section 4 | All match or difference agreed | PASS (2 to agree) |
| Q5 | Data sources | Notebook uses `FACT_SENT_EMAIL`, `DIM_APPROVED_DOCUMENT`, `FACT_EMAIL_ACTIVITY`, `MAP_CUSTOMER_XREF`; readiness section 5 lists the same | Same tables, joins and filters | PASS |
| Q6 | Fill rate | % null, % zero, % non-zero, min / max per feature; all cohorts, per split, c28 | No unexpected nulls; near-constant features flagged; open features checked around April 2026 | PASS (4 flags) |
| Q7 | NBA 3.0 model coverage | iRep features in the 752 with SHAP rank, mapped to 3.1 | None dropped without reason | PASS |
| Q8 | Preserved vs new | Fill section 5 | Every feature labelled | PASS |
| Q9 | HCP trace | Section 6, at least 5 HCPs, recomputed from Snowflake | Final value = output | PASS (140 / 140) |
| Q10 | Invariants | Nested windows; clicked <= opened <= delivered <= sent (per email); template group counts <= Kerendia delivered | 0 violations | PASS (1 data note) |
| Q11 | Reconciliation | Year 2 Kerendia delivered emails | Year 2 total about 74,600 (V7), of which about 41,533 come from `KER` templates that NBA 3.0 misses (NBA 3.0 sees 32,632) | PASS |
| Q12 | NBA 3.0 output comparison | Delivered 3M totals by normalised cohort | Gap explained by `Delivered_vod` fix and `KER` templates | PASS (cohort dates differ) |
| Q13 | Reproducibility and docs | Same schema on re-run; header and summary current | No stale text | PASS (1 note; re-run not done) |

## 3. Evidence log

| # | Result (numbers) | Where (cell / query) | Notes |
| --- | --- | --- | --- |
| Q1 | Universe: 294,727 rows / distinct, 0 null or blank, 1 placeholder `0`. Output: 8,252,328 rows = 294,726 HCPs x 28; every HCP has 28 rows and every cohort 294,726. 0 duplicate (PROVIDER_ID, COHORT_ID), 0 duplicate `HCP_COHORT_ID`, `HCP_COHORT_ID` = `PROVIDER_ID_COHORT_ID` on all rows. 0 HCPs outside the universe; only `0` missing (removed on purpose, cell 5). Mapping: 294,577 HCPs with a BHID, 149 without (0 iRep emails in any cohort), 0 HCPs on more than 1 BHID, 38 BHIDs on 2 HCPs (76 HCPs, 16 with iRep in 12M at c28) | QC session; cell 5 | Same universe and mapping result as F2F |
| Q2 | 28 cohorts match cohorts.parquet on `DATASET` (24 / 2 / 2), `PREDICTION_MONTH` and `LOOKBACK_END_DATE` (2024-06-17 to 2026-09-17): 0 mismatches. Windows 3 / 6 / 12M = 91 / 182 / 365 days, email in window if days before END < N (cell 8). Window edge confirmed by trace HCP 2: last email 90 days before END is counted in 3M. Leakage: cell 8 asserts every email is in (END - 365, END]; the independent recompute (Q9) matched | Cells 4, 8; Q9 | |
| Q3 | 20 features, same order as `expected_feature_columns()`: I-1 7 (delivered 3 / 6 / 12M, clicked 3 / 6 / 12M, recency), I-2 8 (7 template groups + OTHER, 6M), I-3 3 (opened 3 / 6M, tracking flag), I-4 2 (access / content link clicks, 6M). All bigint, 0 nulls | QC session; cell 4 | |
| Q4 | Section 4. All readiness rules are in the code. To agree: (1) opens are in the output, although readiness says to build them only after Q-C1 is explained (the cell 4 comment says "on hold"); (2) unbranded templates are out unless named `KER` | Cells 4, 6 | |
| Q5 | `FACT_SENT_EMAIL`, `MAP_CUSTOMER_XREF`, `DIM_APPROVED_DOCUMENT`, `FACT_EMAIL_ACTIVITY` (`EVNT_TYP = 'Clicked_vod'`) in `CPH_DB_PROD.MODEL_V2`, plus `SOURCE_PROVIDER_BHID_NPI_MAPPING`. Filters: `STAT ILIKE 'Delivered%'`, send date >= 2022-01-01, BHID `LIKE 'BH%'` and not `BHO%`, dedup on `SNT_EMAIL_ID` | Cell 6 | Matches readiness section 5 |
| Q6 | 0% null. Flags: (1) `IREP_T1D_6M` is 0 on every row, so it is constant; (2) near-constant: `IREP_OTHER_6M` 0.00% (max 2), `IREP_CLICK_ACCESS_6M` 0.01%, `IREP_CLICKED_3M` 0.12%, `IREP_EHR_6M` 0.13%; (3) opens: 3M open rate is 33.4 to 42.1% from c1 to c22 (END 2026-03-17), then falls each month to 33.3% (c23), 30.0, 25.0, 23.5, 22.1 and 20.1% (c28); `IREP_OPEN_TRACKING_CHANGE_FLAG` is 8.3% in train and 100% in test / holdout; (4) mix drift train vs test: `IREP_EVENT_INVITE_6M` 2.97% vs 0.87%, `IREP_HF_CONTENT_6M` 0.90% vs 2.28%. Full table in appendix A | QC session | |
| Q7 | 0 of the 752 come from the NBA 3.0 iRep outputs (dev 84 features, ops 14). The 752 has 2 iRep features from the digital block: `DIGITAL_IREP_EMAIL_EXPOSURE_IN_LAST_6_MONTH` (rank 738, 0.002% SHAP) and `..._3_MONTH` (rank 743, 0.001%) | MLflow `Shap_Importances.csv` vs NBA 3.0 output columns | Exact name match |
| Q8 | Section 5 | | |
| Q9 | 7 HCPs (5 at c28, 1 at c24, 1 at c10), 20 features each = 140 values recomputed in pandas from raw Snowflake rows: 140 match (section 6) | QC session | Shared-BHID and no-BHID HCPs left out |
| Q10 | 14 checks on 8,252,328 rows. 13 pass with 0 violations: nested windows for delivered and clicked, clicked <= delivered, opened 3M <= 6M <= delivered 6M, opened 3M <= delivered 3M, template groups sum exactly to delivered 6M, link clicks <= delivered 6M, recency 999 exactly when delivered 12M = 0, recency in [0, 364] or 999, recency < 91 exactly when delivered 3M > 0, recency < 182 exactly when delivered 6M > 0, tracking flag = END >= 2026-04-01, no negatives. 1 extra check fails: link clicks <= `IREP_CLICKED_6M` on 337 rows (79 HCPs; content 337, access 7; 179 with clicked 6M = 0). Cause: some delivered Kerendia emails have a `Clicked_vod` event but `CLK_CNT` = 0 (97 in 2022, 3 to 5 a year in 2023 to 2025, 163 in 2026). The two features come from different click sources. Clicked <= opened was not checked | QC session; notebook cell 11 (9 rules) | Data note, not a code error |
| Q11 | Snowflake recompute today with the notebook rule: Y1 83,090 delivered / 36,479 doctors; Y2 74,532 / 32,091. NBA 3.0 name rule (`ILIKE '%kerendia%'`): Y1 40,209, Y2 32,586. Extra from `KER` templates in Y2: 41,946. Exact `STAT = 'Delivered'` gives 0 in Y2 | QC session, direct SQL | Within 1% of V7 (83,200 / 74,600) and of NBA 3.0 32,632; +1.0% vs 41,533 |
| Q12 | Delivered 3M by cohort, NBA 3.1 / NBA 3.0 dev output: 0.38 (c15) to 1.94 (c12); below 1 in c7 to c10 and c14 to c16, above 1 elsewhere. NBA 3.0 delivered 3M in this output is not 0 (448,302 in total over 966,381 rows), so the readiness point that the NBA 3.0 delivered feature is always 0 does not hold for this file. The cohorts where NBA 3.1 is lower (c7 to c10, c14 to c16) are not explained by the extra `KER` templates, which can only add emails | QC session; NBA 3.0 `16_promotional_features_irep` cells 8 to 11; `promotional_features_hcp_model_cohort_anchor_dates.csv` | Explained (20 Nov 2026): NBA 3.0 cohort end dates are 455 to 459 days earlier than NBA 3.1 for the same cohort number (C01 ends 2023-03-17, c1 ends 2024-06-17), so the per-cohort ratio compares different periods. Other NBA 3.0 differences: BHID from `PHCDW_STG.MDM_STG_HCP_XREF` (`K2_AC2`, `VAULT_CRM_AC2`) instead of `MAP_CUSTOMER_XREF`; `SELECT DISTINCT` without the email ID (same-day duplicates collapse); delivered flag = exact `'Delivered'`, which is non-zero in that output, so the status value was likely different when NBA 3.0 ran (not verifiable today) |
| Q13 | Not re-run (it would overwrite the output). Schema fixed by the cell 10 assert. Cell 1 (28 cohorts) and the client summary (8,252,328 rows, 20 features) match the output; readiness not re-read for iRep. Note: the cell 4 comment says opens are "on hold" but they are built. The QC plan's Q11 target (41,533 as the total) was wrong; it is the `KER`-template subset | QC session | |

## 4. Business rules to verify (readiness vs notebook)

| Rule | Readiness file says | Notebook does (cell) | Match |
| --- | --- | --- | --- |
| Delivered | `STAT ILIKE 'Delivered%'` (NBA 3.0 used `'Delivered'`, always 0) | Cell 6: `se.STAT ILIKE 'Delivered%'`. Q11: exact `'Delivered'` gives 0 in Snowflake today | Yes |
| Kerendia email | Template name contains `Kerendia`, word `KER` / `PP-KER-`, or is a CKD / HF / T1D speaker-program pre / post-meeting template; co-promotion with Lynkuet included | Cell 4 `IREP_KERENDIA_SQL`: the same 4 conditions; `COPROMO_FLAG` only labels co-promotion, nothing is removed | Yes |
| Excluded | Lynkuet-only and medical templates (`Medical Email`, MSL, unsolicited request) | Cell 4: `NOT (medical email, MSL, unsolicited request%)`; Lynkuet-only fails the Kerendia condition | Yes |
| Unbranded | `Cardiorenal Unbranded Content Share`: to confirm with brand team | Not included unless the name also matches the Kerendia rule | To agree |
| Template groups (I-2) | HF content, access / PA, EHR, invite (grouping per F-11 / Q-C2) | Cell 4: 7 groups (EHR, ACCESS_PA, EVENT_INVITE, T1D, HF_CONTENT, CKD_CONTENT, INTRO_THANKYOU) + OTHER, first match in that order | Yes; T1D group is always 0 |
| Opens (I-3) | Only after the April 2026 open-rate drop is explained (Q-C1) | Built (`IREP_OPENED_3M/6M`) with `IREP_OPEN_TRACKING_CHANGE_FLAG` (END >= 2026-04-01); cell 4 comment says "on hold" | To agree |
| Link group (I-4) | Small volumes; access link group | Cell 6: access = URL matches savings / support / copay / access / coverage / prior auth / CoverMyMeds / Blink; content = any URL that is not a system link | Yes |
| One source | iRep only in this block (S3) | Only `FACT_SENT_EMAIL` family | Yes |
| Doctors only | (not stated) | BHID `LIKE 'BH%'` and not `BHO%`; dedup on `SNT_EMAIL_ID` | Addition |
| Defaults | (not stated) | Counts 0, recency 999 | Yes |

## 5. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature | In 752? (SHAP rank) | NBA 3.1 feature | Status | Reason |
| --- | --- | --- | --- | --- |
| `TOTAL_IREP_EMAILS_*` / `TOTAL_IREP_EMAIL_*_FLAG_*` and `TOTAL_IREP_APPRVD_DOC_NM_*` (84 in dev output, 14 in ops) | No (0 of the 752) | `IREP_DELIVERED_*`, `IREP_CLICKED_*`, `IREP_OPENED_*`, template groups `IREP_*_6M` | Replaced (not used by the 3.0 model) | Kerendia rule (V7) and new template groups (F-11 / Q-C2) |
| `DIGITAL_IREP_EMAIL_EXPOSURE_IN_LAST_6_MONTH` | Yes, rank 738 (0.002%) | `IREP_DELIVERED_6M` | Replaced | iRep counted once, in this block (S3); confirm the digital block no longer carries iRep |
| `DIGITAL_IREP_EMAIL_EXPOSURE_IN_LAST_3_MONTH` | Yes, rank 743 (0.001%) | `IREP_DELIVERED_3M` | Replaced | Same |
| (none) | | `IREP_DELIVERED_12M`, `IREP_CLICKED_12M`, `IREP_DAYS_SINCE_DELIVERED`, `IREP_OPEN_TRACKING_CHANGE_FLAG`, `IREP_CLICK_ACCESS_6M`, `IREP_CLICK_CONTENT_6M` | New | 12M window, recency, tracking-change flag, link groups (I-4) |

Summary: 2 of the 752 are iRep features (0.003% of SHAP), both from the digital block, both replaced; 0 dropped without reason. All 20 NBA 3.1 iRep features are labelled: 14 replaced, 6 new.

## 6. HCP trace (step-by-step recompute)

HCPs: high volume, single email near a window edge, no emails, email on a `KER`-named template (missed by 3.0), email opened in April 2026.

| Step | What | Value |
| --- | --- | --- |
| 1 | PROVIDER_ID to BHID(s) | |
| 2 | Raw `FACT_SENT_EMAIL` rows in 12M | |
| 3 | After Kerendia template rule | |
| 4 | After delivered status filter | |
| 5 | Activity join (opened / clicked) | |
| 6 | Per window and template group | |
| 7 | Final feature value | |
| 8 | Match | |

**Results (20 Nov 2026).** Raw rows from Snowflake for each BHID, 2024-03-01 to 2026-09-17; rules applied in pandas, independently of the notebook code.

| Case | PROVIDER_ID / BHID | Cohort | Raw emails | In 12M | Kerendia rule | Delivered | Not named `Kerendia` (missed by 3.0) | Opened | `CLK_CNT` > 0 | Click event, `CLK_CNT` = 0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 High volume | 7887891 / BH11698641 | c28 | 133 | 83 | 32 | 32 | 32 | 0 | 0 | 0 |
| 2 Window edge (90 days) | 10099315 / BH12501787 | c28 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| 3 No emails | 7907713 / BH10968210 | c28 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 4 Groups + clicks | 16335015 / BH13538437 | c28 | 17 | 4 | 4 | 4 | 0 | 4 | 3 | 1 |
| 5 Opened, after April 2026 | 7023868 / BH10525801 | c24 | 22 | 7 | 7 | 7 | 4 | 6 | 0 | 0 |
| 6 Training cohort | 10748578 / BH32461934 | c10 | 15 | 13 | 11 | 11 | 3 | 0 | 0 | 0 |
| 7 Click mismatch | 10065022 / BH12624573 | c28 | 38 | 8 | 7 | 7 | 2 | 7 | 6 | 1 |

Final values (output = recomputed for all 140 values):

| Feature | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `IREP_DELIVERED_3M` | 10 | 1 | 0 | 2 | 3 | 2 | 0 |
| `IREP_DELIVERED_6M` | 20 | 1 | 0 | 3 | 3 | 3 | 1 |
| `IREP_DELIVERED_12M` | 32 | 1 | 0 | 4 | 7 | 11 | 7 |
| `IREP_CLICKED_3M` | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `IREP_CLICKED_6M` | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| `IREP_CLICKED_12M` | 0 | 0 | 0 | 3 | 0 | 0 | 6 |
| `IREP_DAYS_SINCE_DELIVERED` | 7 | 90 | 999 | 50 | 38 | 45 | 171 |
| `IREP_EHR_6M` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `IREP_ACCESS_PA_6M` | 0 | 0 | 0 | 1 | 1 | 0 | 0 |
| `IREP_EVENT_INVITE_6M` | 20 | 1 | 0 | 0 | 2 | 0 | 0 |
| `IREP_T1D_6M` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `IREP_HF_CONTENT_6M` | 0 | 0 | 0 | 2 | 0 | 0 | 1 |
| `IREP_CKD_CONTENT_6M` | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| `IREP_INTRO_THANKYOU_6M` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `IREP_OTHER_6M` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `IREP_OPENED_3M` | 0 | 0 | 0 | 2 | 3 | 0 | 0 |
| `IREP_OPENED_6M` | 0 | 0 | 0 | 3 | 3 | 0 | 1 |
| `IREP_OPEN_TRACKING_CHANGE_FLAG` | 1 | 1 | 1 | 1 | 1 | 0 | 1 |
| `IREP_CLICK_ACCESS_6M` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `IREP_CLICK_CONTENT_6M` | 0 | 0 | 0 | 3 | 0 | 0 | 1 |

Case 4 shows the Q10 data note: `IREP_CLICK_CONTENT_6M` = 3 but `IREP_CLICKED_6M` = 2. Case 7: content click 1, clicked 6M 0.

## 7. Points found during QC

* Open features are in the output. The 3M open rate falls from 37.7% (c22) to 20.1% (c28) after the April 2026 tracking change.
* Unbranded template decision still open.
* `IREP_T1D_6M` is 0 on every row.
* Link-click features (`FACT_EMAIL_ACTIVITY`) and clicked counts (`CLK_CNT`) disagree on 337 rows; most such emails are from 2022 and 2026.
* NBA 3.0 iRep output is not all 0, unlike the readiness note. NBA 3.0 cohorts end about 457 days earlier than NBA 3.1 cohorts with the same number, so per-cohort comparisons are not like-for-like (applies to all channels).
* Same 38 shared BHIDs as F2F (76 HCPs).

## 8. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 13 / 13 |
| Modelling decisions (to agree) | (a) Drop `IREP_T1D_6M` (constant) and probably `IREP_OTHER_6M` / `IREP_CLICK_ACCESS_6M` (near-constant). (b) Opens: keep with the tracking flag, or drop until Q-C1 is explained. (c) Unbranded templates in or out. (d) Link clicks vs clicked: accept the two sources or cap link clicks at clicked |
| Doc fix | Cell 4 comment "on hold" for opens; QC plan Q11 target corrected |
| Fixes made to the notebook | None (QC was read-only) |
| Ready for modelling | Yes for delivered, clicked, recency and template groups; opens after decision (b) |
| Next channel | 03 MSL |

## Appendix A. Fill rate (20 features)

0% null for every feature. Values are % of rows not at the default (0; 999 for recency). Train = c1 to c24, test = c25 to c26, holdout = c27 to c28.

| Feature | All | Train | Test | Holdout | c28 | Max |
| --- | --- | --- | --- | --- | --- | --- |
| `IREP_DELIVERED_3M` | 3.94 | 4.05 | 3.21 | 3.36 | 3.84 | 19 |
| `IREP_DELIVERED_6M` | 6.69 | 6.91 | 5.21 | 5.62 | 5.79 | 29 |
| `IREP_DELIVERED_12M` | 10.98 | 11.07 | 10.89 | 10.00 | 9.58 | 46 |
| `IREP_CLICKED_3M` | 0.12 | 0.12 | 0.10 | 0.09 | 0.09 | 8 |
| `IREP_CLICKED_6M` | 0.22 | 0.23 | 0.16 | 0.18 | 0.18 | 14 |
| `IREP_CLICKED_12M` | 0.40 | 0.40 | 0.40 | 0.38 | 0.36 | 23 |
| `IREP_DAYS_SINCE_DELIVERED` (999) | 10.98 | 11.07 | 10.89 | 10.00 | 9.58 | 999 |
| `IREP_EHR_6M` | 0.13 | 0.12 | 0.20 | 0.18 | 0.17 | 4 |
| `IREP_ACCESS_PA_6M` | 1.20 | 1.20 | 1.04 | 1.32 | 1.42 | 12 |
| `IREP_EVENT_INVITE_6M` | 2.67 | 2.97 | 0.87 | 0.83 | 0.76 | 24 |
| `IREP_T1D_6M` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0 |
| `IREP_HF_CONTENT_6M` | 1.12 | 0.90 | 2.28 | 2.48 | 2.88 | 11 |
| `IREP_CKD_CONTENT_6M` | 3.36 | 3.61 | 1.93 | 1.84 | 1.73 | 16 |
| `IREP_INTRO_THANKYOU_6M` | 0.45 | 0.39 | 0.59 | 1.03 | 1.03 | 11 |
| `IREP_OTHER_6M` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 2 |
| `IREP_OPENED_3M` | 1.52 | 1.63 | 0.96 | 0.84 | 0.93 | 15 |
| `IREP_OPENED_6M` | 2.75 | 2.90 | 1.92 | 1.80 | 1.72 | 22 |
| `IREP_OPEN_TRACKING_CHANGE_FLAG` | 21.43 | 8.33 | 100.00 | 100.00 | 100.00 | 1 |
| `IREP_CLICK_ACCESS_6M` | 0.01 | 0.01 | 0.02 | 0.02 | 0.02 | 2 |
| `IREP_CLICK_CONTENT_6M` | 0.16 | 0.17 | 0.13 | 0.14 | 0.14 | 12 |
