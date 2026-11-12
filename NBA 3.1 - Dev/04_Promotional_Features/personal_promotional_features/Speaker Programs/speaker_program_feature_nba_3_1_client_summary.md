# Phase 3 Events (Speaker Programs): Output Analysis (NBA 3.1)

**Notebook:** `43_field_activity_phase3_events` (id 3065782460311589)
**Plan:** `40_field_activity_nba_3_1_readiness_plan.md` (Phase 3 events, V6)
**Original notebook:** `43_field_activity_phase3_events_irep_msl` (id 3794969181677813) -- split into events, iRep, and MSL (notebook 45)
**Run analysed:** 6 Nov 2026, serverless
**Date:** 6 Nov 2026

**Cohorts.** 28 promotional cohorts: c1-c24 training, c25-c26 testing, c27-c28 back-testing; lookback ends 2024-06-17 to 2026-09-17. **Universe.** 294,726 PROVIDER_IDs (placeholder 0 removed); 294,577 with a BHID; 38 BHIDs on more than one PROVIDER_ID. **Keys.** PROVIDER_ID x COHORT_ID (universe x cohort skeleton, 8,252,328 rows). Previous notebook 43 used BHID keys, 26 cohorts (C01-C26), no universe skeleton (1,332,364 rows).

---

## 1. Summary

| Item | Result |
| --- | --- |
| field_event_state | 172,698 HCP x event rows; 6,383 speaker x event rows |
| Output | 8,252,328 rows = 294,726 x 28, 17 features (23 columns) |
| G1 checks | 7/7 invariants pass; 0 duplicates, 0 nulls |
| Snowflake recompute | 10/10 HCPs match on c24 (end 2026-05-17) |
| HCPs with attendance 12M | 1,504 (c15) to 1,897 (c5), 0.5-0.6% of universe |
| Kerendia speakers 12M | 119 (c8) to 200 (c20) |
| Zero rate | All 17 features >95% zero in every cohort |

**Bottom line.** The events block is built from ANLT_BASE_FACT_EVNT_PRSNL_PROM (Kerendia, speaker programs) and FACT_EVENT_SPEAKER, mapped to PROVIDER_ID from the HCP universe. The universe x cohort skeleton ensures one row per HCP per cohort with defaults. All G1 checks pass. Events are very sparse: only 0.5-0.6% of the 295K universe attended any event in 12 months.

---

## 2. Reconciliation with Phase 0 V6

| Item | Phase 0 Y1 | Notebook Y1 | Phase 0 Y2 | Notebook Y2 |
| --- | --- | --- | --- | --- |
| Attended (any event) | 4,515 | 4,512 | 5,085 | 5,054 |
| Speaker programs | 3,375 | 3,375 | 3,736 | 3,724 |
| Scientific events | 1,081 | 1,078 | 1,263 | 1,244 |
| Signed_vod (no attendance) | 5,851 | 5,846 | 8,098 | 8,027 |
| Registered | 345 | 343 | 926 | 881 |
| Invited | 669 | 669 | 1,427 | 1,379 |

Small gaps (Y1 -3, Y2 -31 attended) from Snowflake source changes and BHO/non-BH ID filtering.

---

## 3. Feature profile

| Feature family | Features | Range across 28 cohorts |
| --- | --- | --- |
| E-1 Attendance | SPKR_ATTENDED_3M/6M/12M, SPKR_DAYS_SINCE_ATTENDED, EVT_ATTENDED_ANY_12M | 1,504-1,897 HCPs attended; avg 1.1 attended if any |
| E-2 Other states | SPKR_SIGNED_NO_ATND_12M, SPKR_REGISTERED_NOT_ATTENDED_12M, SPKR_INVITED_12M | 131-3,135 signed; 135-239 registered; 119-559 invited |
| E-3 Topics/scientific/remote | SPKR_ATTENDED_{T1D,HF,CASE,CKD_CV,OTHER_TOPIC}_12M, SCI_EVENT_ATTENDED_12M, SPKR_ATTENDED_REMOTE_12M | CKD_CV dominant in training; HF growing (868 Y1, 2,132 Y2); T1D 0 until Y2 |
| E-4 Kerendia speaker | SPKR_IS_KERENDIA_SPEAKER_12M, SPKR_N_TALKS_12M | 119-200 Kerendia speakers per cohort |

---

## 4. G1 checks

7 invariants, all pass with 0 violations:
* SPKR_ATTENDED 3M <= 6M <= 12M
* Topic groups sum to SPKR_ATTENDED_12M
* SPKR_ATTENDED_12M + SCI_EVENT <= EVT_ATTENDED_ANY_12M
* REMOTE <= SPKR_ATTENDED_12M
* DAYS_SINCE_ATTENDED = 999 iff no attendance
* DAYS_SINCE_ATTENDED in [0, 364] or 999
* Speaker flag iff talks > 0

0 duplicate HCP_COHORT_ID, 0 nulls, 8,252,328 rows = 294,726 x 28.

---

## 5. Zero rate

All 17 features are above 95% zero in every cohort. Key rates:

| Feature | Training zero range |
| --- | --- |
| SPKR_ATTENDED_12M | 99.38-99.60% |
| SPKR_SIGNED_NO_ATND_12M | 98.81-99.43% |
| SPKR_ATTENDED_CKD_CV_12M | 99.38-99.79% |
| SPKR_ATTENDED_HF_12M | 99.70-100.0% |
| SPKR_ATTENDED_T1D_12M | 100.0% |
| SPKR_IS_KERENDIA_SPEAKER_12M | 99.93-99.96% |

---

## 6. Output

**Path:** `kerendia_nba_3_1_volume/notebook_output/field_activity_nba_3_1/kerendia_nba_3_1_hcp_model_field_events_features.parquet`
**Schema:** HCP_COHORT_ID, PROVIDER_ID, COHORT_ID, DATASET, PREDICTION_MONTH, LOOKBACK_END_DATE + 17 features (all long).

---

## 7. Open points

* Q-D1: Signed_vod (8,027 Y2 pairs) exceeds attendances -- confirm interpretation.
* Q-D3: Topic groups are proposals (CKD_CV, HF, T1D, CASE, OTHER_TOPIC).
* Attendees include non-prescribers and business professionals -- only matter if in the HCP universe.
* HF topic growing in Y2 (2,132 vs 868 in Y1); T1D appears from 2026.
* E3/E4 model experiments not yet run.

---

## 8. Changes from original notebook 43

* Split events from the combined events + iRep + MSL notebook into a standalone notebook.
* Switched from 26-cohort CSV (C01-C26) to 28-cohort promotional parquet (c1-c28).
* Switched from BHID keys to PROVIDER_ID from HCP universe (placeholder 0 removed).
* Universe x cohort skeleton (8,252,328 rows = 294,726 x 28) with defaults for HCPs with no events.
* Output to NBA 3.1 volume.
* MSL features removed (already in separate notebook 45).