# Kerendia NBA 3.1 – HCP New Patient Starts Features: Summary of Changes

**Scope:** HCP-level new patient starts (`05_claim_rx_nps_monthly_cohort`): how many patients started a drug class or brand with each HCP, and how many patients the HCP saw, per cohort  
**Baseline:** NBA 3.0 notebook `05_claim_rx_nps_monthly` (calendar months)  
**Data used for validation:** IQVIA LAAD Rx claims of the 10 validation HCPs (9 have Rx claims), 20 cohorts 2025-01 .. 2026-08 at offset 7  
**Status:** validated on the 10 HCPs (2026-11-03); no change to the data or the features

---

## 1. Summary

* **Nothing from the 3.1 patient journey reaches these features.** They use only Rx claims, not the patient tables.
* **The input stays the NBA 3.0 Rx table.** A "start" is the patient's first prescription of a drug class with any HCP. This needs the claims of every HCP and the history since 2021; the new 3.1 Rx data used by the other HCP features starts in 2023 and covers only the HCPs of the model, so it cannot tell a real start from a continuing treatment.
* **For the validation HCPs the claims are the same** in both sources (49,140 of 49,140 since 2023, plus 2 newer claims in the 3.1 data).
* **The output is identical** to the previous one (0 values changed), and all 14 model features from this notebook are there.
* **All checks pass:** same result as NBA 3.0 at offset 0 (35,720 values, 0 differences), the fast engine = the step-by-step version, one HCP recounted from the raw claims (3,080 checks), and an own recount of four start features (0 differences).

---

## 2. Checks

| Check | Result |
| --- | --- |
| Same as NBA 3.0 at offset 0 (19 months) | **PASS:** 35,720 values, 0 differences |
| Fast engine = step-by-step engine | **PASS:** 0 differences |
| Recount of HCP 1386651560 from the raw claims, every cohort | **PASS:** 3,080 checks, 0 differences |
| Own recount, last cohort, last 12 months (SGLT2 / ACE-ARB / Jardiance / GLP-1 starts) | **PASS:** 84 / 72 / 82 / 22, 0 differences per HCP |
| Output complete | 20 cohorts, 180 rows, 161 columns, no duplicates, no empty values |

---

## 3. Open points

| Topic | Proposal |
| --- | --- |
| New drugs (Kerendia, Mounjaro, Wegovy, Zepbound, generic dapagliflozin) | When they are added to the product basket (next phase), these features need an Rx input from the basket with all HCPs since 2021 |
| HCP universe | Same decision as for the other HCP features |

Details: `05 Rx NPS Claims Files/NBA_3_1_Rx_NPS_Features_Plan.md`.
