# Kerendia NBA 3.1 – HCP Eligible Patient Features: Summary of Changes

**Scope:** HCP-level eligible patient features (`06_claim_eligible_hcp`): how many of the patients an HCP prescribed for were eligible for Kerendia, by CKD and UACR stage, plus a dialysis flag, per cohort  
**Baseline:** NBA 3.0 notebook `06_claim_eligible_hcp` (calendar months)  
**Data used:** IQVIA LAAD claims of the 10 validation HCPs (9 have Rx claims)  
**Status:** validated on the 10 HCPs (2026-11-03); ready for the full run

---

## 1. Summary

* **Eligibility comes from the 3.1 patient journey** (latest run): eligible = CKD stage 2–4 and not on dialysis, or stage unknown with SGLT2 use. Any change to these rules (open patient-journey decisions on SGLT2 and diabetes) only needs a re-run.
* **The Rx claims now come from the 3.1 Rx journey**, like the other HCP features. For the validation HCPs this changes almost nothing (one more patient-month since 2023).
* **The main change is the patient's CKD stage**, as in the other HCP features: for the validation HCPs, last 12 months, 980 eligible patient-months are at stage 3 instead of 23 (previous copy of the patient table), and fewer are "stage unknown" (6,259 instead of 7,207). The total is 1% lower (7,479 instead of 7,544).
* **Same columns as NBA 3.0**; the one selected model feature from this notebook (eligible patients at stage 4, since 2023) is one of them.
* **One deliberate difference with NBA 3.0 (decided 2026-11-03):** in NBA 3.0 the "last N months" columns of this notebook are an *average* over N+1 months, while all other HCP features (and this refactor) use the *total* over the last N months. We keep the total, so all HCP features follow one rule. The monthly counts themselves are the same as NBA 3.0.

---

## 2. Results (validation HCPs, last cohort, last 12 months)

| Eligible patient-months | Previous patient table | 3.1 patient journey |
| --- | --- | --- |
| Total | 7,544 | 7,479 |
| CKD stage 2 | 144 | 126 |
| CKD stage 3 | 23 | 980 |
| CKD stage 4 | 170 | 114 |
| Stage unknown | 7,207 | 6,259 |
| UACR stage 2 / 3 | 25 / 13 | 25 / 11 |

| Check | Result |
| --- | --- |
| Recount of HCP 1386651560 from the raw tables, every cohort | **PASS:** 820 checks, 0 differences |
| Fast engine = step-by-step engine | **PASS** |
| Own recount of the last cohort (total and per stage, per HCP) | **PASS:** 7,479 eligible patient-months, 0 differences |
| Output complete | 20 cohorts, 180 rows, 76 columns, no duplicates, no empty values; provider table complete |
| Same as NBA 3.0 at offset 0 | Monthly counts the same; the "last N months" columns differ because NBA 3.0 averages them (see above) |

---

## 3. Open points

| Topic | Proposal |
| --- | --- |
| "Last N months" columns: total or NBA 3.0 average | **Decided:** total (as the other HCP features); the selected model feature is not affected |
| Patient-journey eligibility decisions (SGLT2, diabetes) | Re-run only |
| Heart failure / diabetes type of eligible patients (new in 3.1) | Not used yet (possible new features later) |
| HCP universe | Same decision as for the other HCP features |

Details: `06 Eligible HCP Claims Files/NBA_3_1_Eligible_HCP_Features_Plan.md`.
