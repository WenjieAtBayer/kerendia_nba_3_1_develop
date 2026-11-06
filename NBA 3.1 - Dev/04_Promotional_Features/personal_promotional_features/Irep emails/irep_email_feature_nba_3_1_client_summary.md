# Phase 3 iRep Emails: Output Analysis (NBA 3.1)

**Notebook:** `44_field_activity_phase3_irep` (id 3065782460311590)
**Plan:** `40_field_activity_nba_3_1_readiness_plan.md` (Phase 3 iRep, V7)
**Original notebook:** `43_field_activity_phase3_events_irep_msl` (id 3794969181677813) -- split into events, iRep, and MSL (notebook 45)
**Run analysed:** 6 Nov 2026, serverless
**Date:** 6 Nov 2026

**Cohorts.** 28 promotional cohorts: c1-c24 training, c25-c26 testing, c27-c28 back-testing; lookback ends 2024-06-17 to 2026-09-17. **Universe.** 294,726 PROVIDER_IDs (placeholder 0 removed); 294,577 with a BHID; 38 BHIDs on more than one PROVIDER_ID. **Keys.** PROVIDER_ID x COHORT_ID (universe x cohort skeleton, 8,252,328 rows). Previous notebook 43 used BHID keys, 26 cohorts (C01-C26), no universe skeleton (1,332,364 rows).

---

## 1. Summary

| Item | Result |
| --- | --- |
| field_irep_email | 576,106 delivered Kerendia iRep emails since 2022-01-01 |
| Output | 8,252,328 rows = 294,726 x 28, 20 features (26 columns) |
| G1 checks | 9/9 invariants pass; 0 duplicates, 0 nulls |
| Snowflake recompute | 10/10 HCPs match on c24 (end 2026-05-17) |
| HCPs with emails 12M | 27,106 (c14) to 35,290 (c22), 9-12% of universe |
| Y1 delivered | 83,090 emails (36,479 doctors, 55 templates) |
| Y2 delivered | 75,590 emails (32,377 doctors, 33 templates) |
| Open rate | 38.1% Y1, 26.7% Y2 |
| Click rate | 2.6% Y1, 2.1% Y2 |

**Bottom line.** The iRep block is built from FACT_SENT_EMAIL (Kerendia rule: Kerendia alone or co-promoted, medical excluded) and DIM_APPROVED_DOCUMENT, mapped to PROVIDER_ID from the HCP universe. The universe x cohort skeleton ensures one row per HCP per cohort with defaults. All G1 checks pass. About 9-12% of the 295K universe received Kerendia iRep emails in 12 months.

---

## 2. Reconciliation with Phase 0 V7

| Item | Phase 0 Y1 | Notebook Y1 | Phase 0 Y2 | Notebook Y2 |
| --- | --- | --- | --- | --- |
| Delivered (NBA 3.1 rule) | ~83,200 | 83,090 | ~74,600 | 75,590 |
| Delivered (NBA 3.0 name rule) | 40,250 | 40,209 | 32,632 | 32,922 |
| Doctors | -- | 36,479 | -- | 32,377 |
| Templates | -- | 55 | -- | 33 |
| Kerendia + Lynkuet co-promo | 0 | 0 | 0 | 0 |

NBA 3.1 rule captures about 2x more emails than NBA 3.0 name rule (includes PP-KER templates, CKD/HF/T1D speaker program templates).

---

## 3. Template groups (proposed, Q-C2)

| Group | Y1 | Y2 | Pre-Y1 2022 | Pre-Y1 2023 | Pre-Y1 2024 |
| --- | --- | --- | --- | --- | --- |
| EHR | 1,211 | 1,853 | 179 | 610 | 108 |
| ACCESS_PA | 8,736 | 9,844 | 72,033 | 21,570 | 12,403 |
| EVENT_INVITE | 34,584 | 9,345 | 4,314 | 1,221 | 21,238 |
| T1D | 0 | 10,536 | 0 | 0 | 0 |
| HF_CONTENT | 8,787 | 22,818 | 0 | 0 | 0 |
| CKD_CONTENT | 27,178 | 16,645 | 161,707 | 46,989 | 51,716 |
| INTRO_THANKYOU | 2,594 | 4,549 | 14,818 | 3,730 | 3,074 |
| OTHER | 0 | 0 | 818 | 846 | 52 |

T1D templates appear from 2026 (Y2). HF content grows from 8,787 (Y1) to 22,818 (Y2). Event invites decline from 34,584 (Y1) to 9,345 (Y2).

---

## 4. G1 checks

9 invariants, all pass with 0 violations:
* IREP_DELIVERED 3M <= 6M <= 12M
* IREP_CLICKED_xM <= IREP_DELIVERED_xM (all 3 windows)
* Template groups sum to IREP_DELIVERED_6M
* IREP_OPENED_3M <= OPENED_6M <= DELIVERED_6M
* IREP_CLICK_ACCESS / CONTENT <= DELIVERED_6M
* DAYS_SINCE_DELIVERED = 999 iff no email
* DAYS_SINCE_DELIVERED in [0, 364] or 999
* Open-tracking flag matches LOOKBACK_END_DATE
* CLICKED <= DELIVERED per window

0 duplicate HCP_COHORT_ID, 0 nulls, 8,252,328 rows = 294,726 x 28.

---

## 5. Zero rate and sparse features

Features above 95% zero in every cohort (training):
* IREP_DELIVERED_3M (93.3-97.3%), IREP_DELIVERED_6M (90.8-95.1%)
* IREP_CLICKED_3M/6M/12M (all >99.5%)
* IREP_EHR_6M (99.6-100%), IREP_T1D_6M (100%), IREP_OTHER_6M (~100%)
* IREP_ACCESS_PA_6M (98.1-99.4%), IREP_EVENT_INVITE_6M (93.8-99.4%)
* IREP_OPEN_TRACKING_CHANGE_FLAG (0% for c1-c14 = all default; 100% for c15+ = all non-default)
* IREP_CLICK_ACCESS_6M (~100%), IREP_CLICK_CONTENT_6M (99.8-99.9%)

Not above 95%: IREP_DELIVERED_12M (88-91%), IREP_DAYS_SINCE_DELIVERED (88-91%), IREP_HF_CONTENT_6M (97.2-100%), IREP_CKD_CONTENT_6M (93.9-98.1%), IREP_OPENED_3M (97.4-98.9%), IREP_OPENED_6M (96.1-97.8%), IREP_INTRO_THANKYOU_6M (99.3-99.9%).

---

## 6. Output

**Path:** `kerendia_nba_3_1_volume/notebook_output/field_activity_nba_3_1/kerendia_nba_3_1_hcp_model_field_irep_features.parquet`
**Schema:** HCP_COHORT_ID, PROVIDER_ID, COHORT_ID, DATASET, PREDICTION_MONTH, LOOKBACK_END_DATE + 20 features (all long).

---

## 7. Open points

* Q-C1: Opens on hold (tracking change at 2026-04-01, not comparable before/after).
* Q-C2: Template groups are proposals (EHR, ACCESS_PA, EVENT_INVITE, T1D, HF_CONTENT, CKD_CONTENT, INTRO_THANKYOU, OTHER).
* iRep open rate declining (38.1% Y1 to 26.7% Y2); click rate stable at ~2%.
* T1D templates new in 2026; HF content growing.
* E3/E4 model experiments not yet run.

---

## 8. Changes from original notebook 43

* Split iRep from the combined events + iRep + MSL notebook into a standalone notebook.
* Switched from 26-cohort CSV (C01-C26) to 28-cohort promotional parquet (c1-c28).
* Switched from BHID keys to PROVIDER_ID from HCP universe (placeholder 0 removed).
* Universe x cohort skeleton (8,252,328 rows = 294,726 x 28) with defaults for HCPs with no emails.
* Output to NBA 3.1 volume.
* MSL features removed (already in separate notebook 45).