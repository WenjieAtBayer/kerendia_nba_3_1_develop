# Kerendia NBA 3.1 – HCP Combined Claims Features: Summary of Changes

**Scope:** HCP-level combined features (`04_claims_monthly_cohort`): each HCP's Rx claims, split by what was known about the patient's kidneys when the prescription was written  
**Baseline:** NBA 3.0 notebook `04_claims_monthly` (calendar months)  
**Data used for validation:** IQVIA LAAD claims of the 10 validation HCPs (9 have Rx claims), 20 cohorts 2025-01 .. 2026-08 at offset 7  
**Status:** validated on the 10 HCPs (2026-11-03); full run after all six HCP notebooks

---

## 1. Summary

* **All inputs now come from the 3.1 patient journey**, like the other HCP features: the Rx claims (same as the Rx features), the lab tests (same as the lab features) and the patient kidney stage and treatments per month (latest patient-journey run).
* **The largest change is the patient's CKD stage.** The notebook was reading an old copy of the patient table, from before the 3.1 diagnosis journey recognised stage-3 and stage-5 codes. Now, for the validation HCPs, 2,502 Rx claims of the last 12 months are matched to a known patient stage instead of 770 (stage 3: 1,765 instead of 37).
* **Many more lab tests are available.** The NBA 3.0 lab table had almost no UACR tests (12.9 thousand patients in the US, against 16.1 million in the 3.1 lab data). Same-day tests stay rare at HCP level (24 Rx claims with a same-day test since 2023 for the validation HCPs, 2 before).
* **The Rx claims are the same as before** (one newer claim in the last 12 months).
* **All checks pass:** same result as NBA 3.0 at offset 0 (19 months, 0 differences), the fast engine = the step-by-step version, one HCP recounted from the raw tables (19,800 checks, 0 differences), and an own recount of the totals, patient stages and same-day tests (0 differences).
* **One open point for the model:** 9 of the 89 selected model features from this notebook combine the patient's stage with a DPP-IV or other glucose-lowering treatment. The 3.1 patient journey does not keep these treatments, so these features no longer exist (section 5).

---

## 2. What the features use

| Feature family | Question | Input | Changed in 3.1? |
| --- | --- | --- | --- |
| Total | How many Rx claims? | Rx claims | Source: 3.1 Rx journey (same claims) |
| A. Patient stage | What GFR / UACR stage was the patient in that month? | Patient stage per month (patient journey) | **Yes:** latest 3.1 run, stage 3 and 5 from codes |
| B. Same-day test | Did the patient have a GFR / UACR test on the day of the prescription? | Lab tests | **Yes:** 3.1 lab data (many more UACR tests) |
| C. Stage x treatment | Which treatments is the patient on that month, by stage? | Patient stage x treatment per month (patient journey) | **Yes:** latest 3.1 run |

---

## 3. What changed

| | Before | Now |
| --- | --- | --- |
| Rx claims | NBA 3.0 table | 3.1 Rx journey (same as the Rx features) |
| Lab tests | NBA 3.0 lab table | 3.1 lab data (same as the lab features) |
| Patient tables | Copy written 2026-10-26 | Latest patient-journey run (2026-11-02); the full run uses the full patient-journey run |
| Diagnosis table | Read, not used | Not read |
| Columns | 1,560 | 1,785: new stage x drug combinations (mainly stage 3 / 5 and UACR tests); the columns of the previous output are all kept |

History before 2023 (the start of the 3.1 data) is still read from the NBA 3.0 tables, but only to keep the same list of columns; it is never counted.

---

## 4. Results (9 validation HCPs with Rx claims)

| Measure | Before | Now |
| --- | --- | --- |
| Rx claims, last cohort, last 12 months | 12,836 | 12,837 |
| ... of patients with a known GFR stage | 770 | 2,502 |
| ... stage 3 / stage 5 | 37 / 7 | 1,765 / 216 |
| ... stage 4 | 291 | 162 |
| Rx claims with a same-day GFR / UACR test, since 2023 | 2 / 0 | 13 / 11 |
| Stage x treatment rows counted, since 2023 | 337,113 | 341,098 (+1.2%) |

The shifts between stages (stage 4 and stage 2 down, stage 3 and 5 up) come from the 3.1 patient-journey stage rules (diagnosis codes for stage 3 and 5); they are the same patient tables the patient journey summaries describe.

| Check | Result |
| --- | --- |
| Same as NBA 3.0 at offset 0 (19 months, NBA 3.0 inputs) | **PASS:** 0 differences |
| Fast engine = step-by-step engine (first and last cohort) | **PASS:** 32,094 values, 0 differences |
| Recount of HCP 1386651560 from the raw tables, every cohort | **PASS:** 19,800 checks, 0 differences |
| Own recount (totals, patient stage, same-day tests; last cohort) | **PASS:** 0 differences |
| Output complete | 20 cohorts, 180 rows, 1,785 columns, no duplicates, no empty values; provider table complete |

---

## 5. Open points

| Topic | Today | Proposal |
| --- | --- | --- |
| DPP-IV / other glucose treatments in the stage x treatment features | Not in the 3.1 patient journey, so 9 selected model features are missing | **Decided:** follow the patient journey; the 9 features leave the model list and the feature selection is rerun when the model is retrained on 3.1 |
| GLP-1 stage x treatment features (7 selected) | Present in the 3.1 data, but not for the 10 validation HCPs | Check in the full run |
| HCP universe | NBA 3.1 universe (HCP 1508230566 is not in it) | Same decision for all HCP features |

Details: `04 Monthly Cohort Claims Files/NBA_3_1_Claims_Features_Plan.md`.
