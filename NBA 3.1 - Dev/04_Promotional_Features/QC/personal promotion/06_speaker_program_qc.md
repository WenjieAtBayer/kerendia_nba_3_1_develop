# QC 06: Speaker program (events) features, NBA 3.1

**QC status:** DONE, 20 Nov 2026 (channel 6 of 6)  
**Verdict:** PASS with actions. 10 / 13 pass; Q5 OPEN (`FACT_EVENT_ATTENDEE` not used, reason not documented), Q12 OPEN (no NBA 3.0 HCP-level speaker output found), Q13 FAIL (stale docs). Output correct for the notebook rules (85 / 85 traced values match); `SPKR_ATTENDED_T1D_12M` is constant 0.  
**QC run:** 20 Nov 2026, serverless, read-only on the output of the 6 Nov run (notebook not re-run). Event table rebuilt from Snowflake today with the notebook's cells 3 to 6 (no write).

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `personal_promotional_features/Speaker Programs/speaker_program_feature` (16 cells) |
| Client summary | `Speaker Programs/speaker_program_feature_nba_3_1_client_summary.md` |
| Readiness file | `40_field_activity_nba_3_1_readiness_plan.md`: Phase 0 V6, Phase 3 E-1 to E-4 |
| Output | `kerendia_nba_3_1_volume/notebook_output/field_activity_nba_3_1/kerendia_nba_3_1_hcp_model_field_events_features.parquet` |
| Universe / cohorts | `HCP_Universe_without_call_hcps/` x `cohorts/promotional/cohorts.parquet` |
| Expected shape | 17 features + 6 keys (23 columns), rows = universe x 28. Confirmed |
| NBA 3.0 counterpart | `14_promotional_features_speaker_program` (66 features, 11 x 1 to 6M) |
| NBA 3.0 final model | MLflow run `f583bcbc9d56477fae983d44c16f8c70`, 752 features, `Shap_Importances.csv` |

## 2. QC checklist

| # | Check | How | Pass when | Status |
| --- | --- | --- | --- | --- |
| Q1 | HCP universe | Distinct PROVIDER_ID vs universe; rows; duplicates; extra HCPs; placeholder `0` | Same HCP set, 0 duplicates | PASS |
| Q2 | Cohorts and windows | Lookback ends; window days; no event after lookback end | All match | PASS |
| Q3 | All features made | Columns vs config vs readiness E-1 to E-4 | No missing / extra column | PASS (8 additions to agree) |
| Q4 | Business rules | Fill section 4 | All match | PASS (Q-D1 to Q-D3 open) |
| Q5 | Data sources | Notebook: `ANLT_BASE_FACT_EVNT_PRSNL_PROM`, `FACT_EVENT_SPEAKER`, `MAP_CUSTOMER_XREF`; readiness also lists `FACT_EVENT_ATTENDEE` | Missing `FACT_EVENT_ATTENDEE` explained or added | OPEN |
| Q6 | Fill rate | % null, % zero, % non-zero per feature, per cohort; `DAYS_SINCE` sentinel share | No unexpected nulls; near-constant features flagged | PASS (2 flags) |
| Q7 | NBA 3.0 model coverage | Speaker features in the 752 with SHAP rank | Mapped or dropped with reason | PASS |
| Q8 | Preserved vs new | Fill section 5 | Every feature labelled | PASS |
| Q9 | HCP trace | Section 6, at least 5 HCPs | Final value = output | PASS (85 / 85) |
| Q10 | Invariants | Nested windows; attended by topic / type <= attended total; registered-not-attended and attended do not overlap per event | 0 violations | PASS |
| Q11 | Reconciliation | Events and attendees per year vs `20_` review (about 8,000 `Signed_vod` a year without attendance) | Within expected range | PASS |
| Q12 | NBA 3.0 output comparison | Attended counts by normalised cohort | Differences explained (state split, event type split) | OPEN |
| Q13 | Reproducibility and docs | Same schema on re-run; summary current | No stale text | FAIL |

## 3. Evidence log

| # | Result (numbers) | Where (cell / query) | Notes |
| --- | --- | --- | --- |
| Q1 | 8,252,328 rows = 294,726 HCPs x 28; every cohort 294,726 rows; 0 duplicate `HCP_COHORT_ID`; `HCP_COHORT_ID` = `PROVIDER_ID_COHORT_ID`; 0 HCPs outside the universe; only `0` missing (cell 5 filter) | QC session; cell 5 | |
| Q2 | 28 cohorts; `DATASET`, `PREDICTION_MONTH`, `LOOKBACK_END_DATE` match cohorts.parquet (0 mismatches). Windows 3 / 6 / 12M = 91 / 182 / 365 days, event date in (END - 365, END]; cell 8 asserts no record outside | QC session; cells 4, 8 | Cell 5 print sorts cohorts as text (shows "c1 to c9"); output not affected |
| Q3 | 17 features in config order, all bigint, 0 nulls. Readiness E-1 to E-4 list 8 (`SPKR_ATTENDED_6M/12M`, `SPKR_DAYS_SINCE_ATTENDED`, `SPKR_REGISTERED_NOT_ATTENDED_12M`, `SPKR_INVITED_12M`, `SPKR_ATTENDED_HF_12M`, `SPKR_ATTENDED_CKD_CV_12M`, `SCI_EVENT_ATTENDED_12M`, `SPKR_IS_KERENDIA_SPEAKER`); all built (speaker flag named `_12M`). Additions: `SPKR_ATTENDED_3M`, `EVT_ATTENDED_ANY_12M`, `SPKR_SIGNED_NO_ATND_12M`, `SPKR_ATTENDED_T1D/CASE/OTHER_TOPIC_12M`, `SPKR_ATTENDED_REMOTE_12M`, `SPKR_N_TALKS_12M` | Cell 4; readiness lines 163 to 166 | |
| Q4 | Section 4 | Cells 4, 6 | |
| Q5 | Events from `ANLT_BASE_FACT_EVNT_PRSNL_PROM` (`PROD_BRAND_NM = 'KERENDIA'`, BHIDs `BH%` not `BHO%`, from 2022-01-01); speakers from `FACT_EVENT_SPEAKER` + `MAP_CUSTOMER_XREF` (status `Attended_vod`, `Signed_vod`). Readiness line 92 lists `FACT_EVENT_ATTENDEE` as a source of `field_event_state`; the notebook does not read it and gives no reason (attendance comes from the `ATND` column) | Cell 6; readiness line 92 | OPEN |
| Q6 | 0 nulls. All features non-zero on <= 1.32% of rows (appendix A). `SPKR_ATTENDED_T1D_12M` 0 on every row: the T1D talk's first attendance is 2026-10-27, after c28 ends (2026-09-17). `SPKR_ATTENDED_OTHER_TOPIC_12M` max 1, at most 1 HCP per cohort. HF 0 until c15, 1,073 attendances at c28; CKD / CV 1,568 (c1) to 577 (c28). `SPKR_N_TALKS_12M`: top HCPs 109, 102, 95, 85, 55 talks (all with 0 attendances, i.e. speakers only); 237 HCP x cohort rows >= 20; c28 speakers p50 / p90 / p99 = 5 / 14 / 37 | QC session | Appendix A, B |
| Q7 | 7 name matches in the 752 (`SPEAK`, `SPKR`, `EVENT`, `EVT`, `PROGRAM`), 0.162% of SHAP: `TOTAL_EVENTS_TIME_180_DAYS_PX` (226, 0.118%), `TOTAL_EVENTS_TIME_360_DAYS_RX` (678), `TOTAL_SPKR_EVNT_FMT_F2F_IN_LAST_6_MONTH` (679), `TOTAL_EVENTS_TIME_180_DAYS_RX` (704), `TOTAL_SPEAKER_PROGRAMS_ATTENDED_IN_LAST_3_MONTH` (709), `TOTAL_SPKR_EVNT_FMT_F2F_IN_LAST_2_MONTH` (736), `_3_MONTH` (751) | `Shap_Importances.csv` | |
| Q8 | Section 5 | | |
| Q9 | 5 c28 HCPs x 17 = 85 values recomputed in pandas from raw event and speaker rows (today's data): 85 / 85 match | QC session | Section 6 |
| Q10 | 0 violations on 11 checks: 3M <= 6M <= 12M; topic groups sum to `SPKR_ATTENDED_12M`; speaker attended + scientific <= any attended; remote <= attended; recency 999 iff no attendance, in [0, 364] otherwise, < 91 iff 3M > 0, < 182 iff 6M > 0; speaker flag 0 / 1 and = 1 iff talks > 0; no negatives. Per-event state overlap impossible by build (one strongest state per HCP x event; cell 6 asserts uniqueness) | QC session; cells 6, 11 | |
| Q11 | HCP x event states by year, rebuilt today (V6 / client summary in brackets): attended Y1 4,523 (4,515) / Y2 5,176 (5,085); signed Y1 5,832 (5,851) / Y2 8,246 (8,098); speaker-program attended Y1 3,383 (3,375) / Y2 3,791 (3,736); scientific attended Y1 1,081 (1,081) / Y2 1,299 (1,263). Signed without attendance about 8,200 in Y2, as `20_` expects. `field_event_state` 173,642 rows today (172,698 on 6 Nov); speakers 6,492 (6,383) | QC session; cell 7 | Source grew after the run |
| Q12 | NBA 3.0 `hcp_level_model/speaker_program_dev/` holds speaker-program optimisation and NBRx outputs (counterfactuals, top 5K, integration results), no HCP x cohort speaker feature file; other NBA 3.0 folders not searched | `dbutils.fs.ls` | OPEN: locate notebook 14 output |
| Q13 | Stale: (1) cell 14 says "9/9 invariants"; cell 11 has 7 rules. (2) Client summary names the notebook `43_field_activity_phase3_events`; says T1D "appears from 2026" (true in raw data, but the feature is 0 in every cohort); ranges cover only some cohorts: HCPs attended 1,504 (c15) to 1,897 (c5) vs 2,041 / 2,063 at c27 / c28; Kerendia speakers 119 to 200 vs 208 at c26. (3) Readiness E-1 to E-4 list 8 features, output has 17. Consistent: 17 features / 23 columns, 7 / 7 invariants, 8,252,328 rows | Cells 11, 14; client summary | FAIL |

## 4. Business rules to verify (readiness vs notebook)

| Rule | Readiness file says | Notebook does (cell) | Match |
| --- | --- | --- | --- |
| States | Invited, registered and attended kept apart; attended is the primary signal | One row per HCP x event, strongest state wins: ATTENDED > SIGNED > REGISTERED > INVITED > OTHER (cell 6) | Yes (SIGNED added as own state) |
| Attended | Confirmed attendance only; `Signed_vod` without `ATND` is not attendance (Q-D1) | ATTENDED = `UPPER(ATND) = 'ATTENDED'`; `Signed_vod` = SIGNED, own feature | Yes; Q-D1 open |
| RSVP map | | Registered = `Accepted_vod`, `Confirmed`, `Registered`, `Wait-Listed`; invited = `Invited_vod`, `Nominated`. Not mapped (OTHER): `Registration_Pending_vod` (4 non-attended rows), `Registration_Approved_vod` (2) | Small gap: add both to REGISTERED |
| Event type | Speaker programs split from scientific presentations, round tables and medical events (Q-D2) | SPEAKER_PROGRAM = `EVNT_CAT = 'SPEAKER PROGRAMS'`; SCIENTIFIC = `EVNT_TYP` in Scientific Presentation, Scientific Round Tables, `medical_event__c`, Symposium; rest OTHER_EVENT | Yes; Q-D2 open |
| Topic groups | HF, CKD / CV (after Q-D3) | Regex groups T1D, HF, CASE, CKD_CV, else OTHER_TOPIC (first match, in that order) | Yes, plus T1D / CASE / OTHER; Q-D3 open |
| Kerendia speaker | `SPKR_IS_KERENDIA_SPEAKER` from `FACT_EVENT_SPEAKER` | Speaker status `Attended_vod` / `Signed_vod` on a Kerendia event; flag + distinct talks in 12M | Yes |
| Kerendia event | Event belongs to Kerendia (rule as in notebook) | `PROD_BRAND_NM = 'KERENDIA'`; `BHO%` IDs excluded | Yes |
| Mapping | | BHID to PROVIDER_ID via `SOURCE_PROVIDER_BHID_NPI_MAPPING`, universe only (38 BHIDs on > 1 PROVIDER_ID, cell 5) | Yes |

## 5. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature | In 752? (SHAP rank) | NBA 3.1 feature | Status | Reason |
| --- | --- | --- | --- | --- |
| `TOTAL_SPEAKER_PROGRAMS_ATTENDED_IN_LAST_3_MONTH` | Yes (709) | `SPKR_ATTENDED_3M` | Replaced | Confirmed attendance, speaker programs only |
| `TOTAL_SPKR_EVNT_FMT_F2F_IN_LAST_6/2/3_MONTH` | Yes (679, 736, 751) | `SPKR_ATTENDED_*M` with `SPKR_ATTENDED_REMOTE_12M` | Replaced | Format kept as a remote share; F2F = attended - remote |
| `TOTAL_EVENTS_TIME_180_DAYS_PX`, `_360_DAYS_RX`, `_180_DAYS_RX` | Yes (226, 678, 704) | None in this block | Not mapped | Name match only; source of these features not confirmed (PX / RX suggests claims, not speaker programs) |
| (none) | | `SPKR_DAYS_SINCE_ATTENDED`, `EVT_ATTENDED_ANY_12M`, signed / registered / invited, topic groups, `SCI_EVENT_ATTENDED_12M`, speaker flag and talks | New | States and event types split (V6) |

Summary: 7 name matches in the 752 (0.162% SHAP); 4 replaced, 3 to confirm.

## 6. HCP trace (step-by-step recompute)

HCPs: attended several programs, registered but not attended, invited only, Kerendia speaker, no events.

| Step | What | Value |
| --- | --- | --- |
| 1 | PROVIDER_ID to BHID(s) | |
| 2 | Raw event rows in 12M | |
| 3 | After Kerendia event and event type rules | |
| 4 | After state mapping (invited / registered / attended) | |
| 5 | Per window and topic | |
| 6 | Final feature value | |
| 7 | Match | |

**Results.** c28 (end 2026-09-17); HCPs with one BHID and one PROVIDER_ID; raw rows pulled today with the notebook's query, state, topic and window rules re-implemented in pandas.

| Case | PROVIDER_ID / BHID | Events 12M | Speaker attended | Any attended | Signed | Registered | Invited | Days since | Scientific | HF | Talks | Match |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 Attended several | 22433333 / BH28133083 | 3 | 3 | 3 | 0 | 0 | 0 | 112 | 0 | 3 | 0 | 17 / 17 |
| 2 Signed, no attendance | 25431864 / BH37049272 | 1 | 0 | 0 | 1 | 0 | 0 | 999 | 0 | 0 | 0 | 17 / 17 |
| 3 Invited only | 12348949 / BH13013828 | 1 | 0 | 0 | 0 | 0 | 1 | 999 | 0 | 0 | 0 | 17 / 17 |
| 4 Kerendia speaker | 8103114 / BH11814344 | 1 | 1 | 1 | 0 | 0 | 0 | 232 | 0 | 1 | 5 | 17 / 17 |
| 5 Scientific event | 11867101 / BH10750645 | 1 | 0 | 1 | 0 | 0 | 0 | 999 | 1 | 0 | 0 | 17 / 17 |

## 7. Points found during QC

* Q-D1 (meaning of `Signed_vod`), Q-D2 (event type split) and Q-D3 (topic groups) still open; the notebook implements the proposals.
* `FACT_EVENT_ATTENDEE` listed in readiness, not used, no reason given.
* `SPKR_ATTENDED_T1D_12M` constant 0 in all 28 cohorts (T1D talk starts 2026-10-27); exclude from training, keep in config for scoring.
* `SPKR_ATTENDED_OTHER_TOPIC_12M` near-constant (max 1); attended topics falling in OTHER are `Kerendia Speaker Training` (7, Y1), empty topic names (18, before Y1) and one HFpEF talk (3, after Nov 2026, outside all windows).
* Topic mix shifts: HF from c16, CKD / CV falling; level shift between training and scoring.
* Very active speakers (up to 109 talks in 12M); consider capping or a log transform.
* Source grew since the 6 Nov run (173,642 vs 172,698 HCP x event rows); re-run before modelling.

## 8. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 10 / 13 (Q5, Q12 OPEN; Q13 FAIL) |
| Open issues | `FACT_EVENT_ATTENDEE` reason; NBA 3.0 speaker output not located; stale cell 14 and client summary; 2 unmapped RSVP statuses |
| Decisions (to agree) | (a) Drop or keep `SPKR_ATTENDED_T1D_12M` (constant 0) and `SPKR_ATTENDED_OTHER_TOPIC_12M`. (b) Map `Registration_Pending_vod` / `Registration_Approved_vod`. (c) Cap `SPKR_N_TALKS_12M`. (d) Re-run before modelling |
| Fixes made to the notebook | None (QC read-only) |
| Ready for modelling | Yes as a candidate block (E4), after (a) and a re-run |
| Next channel | None (last personal promotion channel) |

## Appendix A. Fill rate (17 features)

0% null. % of rows not at default (0; 999 for days since). Train c1 to c24, test c25 to c26, holdout c27 to c28.

| Feature | All | Train | Test | Holdout | c28 | Max |
| --- | --- | --- | --- | --- | --- | --- |
| `SPKR_ATTENDED_3M` | 0.134 | 0.137 | 0.111 | 0.121 | 0.124 | 4 |
| `SPKR_ATTENDED_6M` | 0.263 | 0.267 | 0.227 | 0.252 | 0.242 | 4 |
| `SPKR_ATTENDED_12M` | 0.509 | 0.506 | 0.511 | 0.545 | 0.543 | 8 |
| `SPKR_DAYS_SINCE_ATTENDED` (999) | 0.509 | 0.506 | 0.511 | 0.545 | 0.543 | 999 |
| `EVT_ATTENDED_ANY_12M` | 0.596 | 0.584 | 0.646 | 0.696 | 0.700 | 8 |
| `SPKR_SIGNED_NO_ATND_12M` | 0.871 | 0.803 | 1.244 | 1.318 | 1.319 | 5 |
| `SPKR_REGISTERED_NOT_ATTENDED_12M` | 0.067 | 0.061 | 0.100 | 0.114 | 0.116 | 2 |
| `SPKR_INVITED_12M` | 0.138 | 0.128 | 0.182 | 0.212 | 0.217 | 2 |
| `SPKR_ATTENDED_T1D_12M` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 |
| `SPKR_ATTENDED_HF_12M` | 0.112 | 0.074 | 0.321 | 0.354 | 0.348 | 3 |
| `SPKR_ATTENDED_CASE_12M` | 0.011 | 0.009 | 0.022 | 0.025 | 0.026 | 1 |
| `SPKR_ATTENDED_CKD_CV_12M` | 0.396 | 0.431 | 0.187 | 0.187 | 0.191 | 6 |
| `SPKR_ATTENDED_OTHER_TOPIC_12M` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1 |
| `SCI_EVENT_ATTENDED_12M` | 0.079 | 0.068 | 0.132 | 0.152 | 0.161 | 3 |
| `SPKR_ATTENDED_REMOTE_12M` | 0.093 | 0.100 | 0.054 | 0.056 | 0.039 | 2 |
| `SPKR_IS_KERENDIA_SPEAKER_12M` | 0.056 | 0.053 | 0.070 | 0.067 | 0.068 | 1 |
| `SPKR_N_TALKS_12M` | 0.056 | 0.053 | 0.070 | 0.067 | 0.068 | 109 |

## Appendix B. Profile by cohort (sums over HCPs, 12M)

| Cohort | HCPs spkr attended | Spkr attended | HCPs any attended | Scientific | Signed | Registered | Invited | Speakers | Talks | HF | CASE | CKD_CV |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| c1 | 1,476 | 1,577 | 1,565 | 85 | 1,759 | 137 | 138 | 144 | 705 | 0 | 9 | 1,568 |
| c5 | 1,821 | 1,920 | 1,897 | 37 | 2,038 | 201 | 343 | 126 | 808 | 0 | 0 | 1,920 |
| c10 | 1,585 | 1,678 | 1,750 | 121 | 2,186 | 149 | 556 | 127 | 1,056 | 0 | 5 | 1,673 |
| c15 | 1,217 | 1,298 | 1,504 | 259 | 2,260 | 131 | 524 | 186 | 1,394 | 0 | 41 | 1,256 |
| c16 | 1,185 | 1,266 | 1,509 | 300 | 2,355 | 164 | 495 | 190 | 1,596 | 118 | 41 | 1,106 |
| c20 | 1,432 | 1,550 | 1,849 | 422 | 3,421 | 221 | 312 | 200 | 1,867 | 641 | 43 | 865 |
| c24 | 1,489 | 1,610 | 1,872 | 390 | 3,830 | 291 | 499 | 205 | 1,781 | 904 | 64 | 641 |
| c26 | 1,502 | 1,622 | 1,909 | 420 | 4,073 | 301 | 561 | 208 | 1,821 | 1,013 | 64 | 544 |
| c27 | 1,610 | 1,740 | 2,041 | 443 | 4,274 | 339 | 608 | 198 | 1,531 | 1,118 | 69 | 553 |
| c28 | 1,600 | 1,727 | 2,063 | 498 | 4,270 | 347 | 641 | 199 | 1,390 | 1,073 | 77 | 577 |
