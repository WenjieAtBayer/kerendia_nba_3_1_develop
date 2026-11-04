# Kerendia NBA 3.1 – HCP Diagnosis Claims Features: Summary of Changes

**Scope:** HCP-level diagnosis (Dx) claims features (`03_claim_diagnosis_monthly_cohort`): how many CKD-related diagnosis claims each HCP has, by CKD stage of the claim and by the stage the patient has just moved into, per cohort, in the last 1, 3, 6 and 12 months  
**Baseline:** NBA 3.0 notebook `03_claim_diagnosis_monthly` (calendar months)  
**Data used for validation:** IQVIA diagnosis claims of the 10 validation HCPs, 20 cohorts 2025-01 .. 2026-08 at offset 7; all-US Dx tables for the size checks  
**Status:** validated on the 10 HCPs (2026-11-03). The Dx features now use the NBA 3.1 Dx data; open points in section 5

---

## 1. Summary

* **New input: the 3.1 Dx data.** The features now count the diagnosis claims of the 3.1 Dx patient journey (one row per HCP, patient, day and diagnosis code), instead of the separate NBA 3.0 HCP Dx table (`Dx_03`).
* **Why:** the NBA 3.0 HCP Dx table uses the NBA 3.0 code list, takes the CKD stage from the diagnosis text, and misses the newer stage-3 codes (3a, 3b, unspecified 3) and every stage-5 / end-stage code. Since 2023 it has 12.6K stage-3 claims and no stage-5 claims (all US). The 3.1 Dx journey, which uses the final Dx product basket and reads the stage from the code, has 65.3M stage-3 and 115.8M stage-5 claims.
* **Same claims otherwise:** without those missing codes the 3.1 data has 290.6M claims since 2023, against 284.9M in the NBA 3.0 table. The change is the missing codes, not a different claim definition.
* **Patient stage from the latest run:** the "patient new to stage" features now read the patient-journey run of 2026-11-02, not an older copy from before the stage fix. With the older copy, no claim of the validation HCPs had a patient new to stage 3 or 5.
* **New columns:** stage-5 claim counts (`TOTAL_DX_CLAIMS_STAGE_5_...`, its share and running total) are added: 9 new columns, 120 in total. No column is removed or renamed.
* **All checks pass:** recount of every value from the raw claims (16,020 checks, 0 differences), fast engine = step-by-step version, same result as NBA 3.0 at offset 0 when run on the NBA 3.0 data (the counting logic is unchanged).

---

## 2. What the Dx claims features use

| Input | Used for | Changed in 3.1? |
| --- | --- | --- |
| Dx claims of the 3.1 Dx patient journey: one row per HCP, patient, day and code, with the CKD stage of the code (1–5, or unspecified) | Total Dx claims, claims by stage, shares, `RUNNING_` | **Yes:** was the NBA 3.0 HCP Dx table `Dx_03` |
| Patient CKD stage per month (3.1 patient journey) | Claims where the patient moved to a new stage that month | **Yes:** now the latest run (was an older copy) |

---

## 3. NBA 3.0 vs NBA 3.1 Dx data

| Rule | NBA 3.0 HCP Dx table | NBA 3.1 (now used) |
| --- | --- | --- |
| Codes | NBA 3.0 kidney code list | 31 CKD codes of the final Dx product basket |
| Stage | From the description text | From the code |
| Stage 3 (N18.30, N18.31, N18.32) | Missing (only the old N18.3) | Stage 3, with sub-stage 3a / 3b |
| Stage 5 and ESRD (N18.5, N18.6, I12.0, I13.11, I13.2) | Missing | Stage 5 (N18.6 also marked ESRD) |
| Type 1 diabetes with kidney disease (E10.21/22/29) | Missing | Included, stage unspecified (open point) |
| Several claims, same HCP, patient, day and code | Counted each | Counted once |
| HCP universe | NBA 3.0 | NBA 3.1 |

| All US, Dx claims since 2023 | NBA 3.0 HCP Dx table | NBA 3.1 (now used) |
| --- | --- | --- |
| Claims | 284.9M | 473.1M |
| HCPs | 226.9K | 283.3K |
| Stage 1 | 1.24M | 1.26M |
| Stage 2 | 9.24M | 9.42M |
| Stage 3 | 12.6K | 65.3M |
| Stage 4 | 16.3M | 16.7M |
| Stage 5 | 0 | 115.8M |
| Stage unspecified | 258.1M | 264.6M |

---

## 4. Effect on the validation HCPs (20 cohorts)

| | Before (NBA 3.0 HCP Dx table) | After (NBA 3.1) |
| --- | --- | --- |
| Dx claims since 2023 | 6,815 | 8,991 |
| HCPs with Dx features | 9 | 9 (1 out, 1 in) |
| Columns | 111 | 120 (+9 stage-5 columns) |
| Dx claims in the last 12 months, last cohort (2026-08) | 1,753 | 3,210 |
| ... stage 3 / stage 5 | 0 / not available | 501 / 1,034 |
| All claims up to the last cohort | 6,692 | 8,760 |
| All claims with a patient new to stage 3 / stage 5 | 0 / 0 | 623 / 171 |

* On the same HCP, patient and day, the highest stage stays the same or goes up (mostly from "unspecified" to stage 3 or 5); it never goes down.
* HCP 1528629052 gets Dx features for the first time. HCP 1508230566 is not in the NBA 3.1 HCP universe, so it has no NBA 3.1 Dx data, the same as for the lab features.
* For the 8 HCPs in both, 41% of the count values change, most of them upwards.
* 3 of the 277 selected model features come from this notebook. `TOTAL_DX_CLAIMS_STAGE_UNSPECIFIED_IN_LAST_3_MONTH` goes down slightly (stage 3 / 5 claims move out of "unspecified"). The two `..._WITH_PATIENT_NO_NEW_STAGE_IN_LAST_6 / 12_MONTH` features rise by about 85%, because the added stage-3 and stage-5 claims are counted too.

---

## 5. Open points for the full run

| Topic | Today | Proposal |
| --- | --- | --- |
| Where the 3.1 Dx data is stored | Intermediate table of the patient-journey run of 2026-11-02 | Save it as a named output of every patient-journey run (same as for lab) |
| HCP universe | NBA 3.1 universe (HCP 1508230566 is not in it) | Same decision for all HCP inputs; confirm the NBA 3.1 universe for the HCP features |
| New stage-5 columns | Added | Confirm for the model feature list |
| Type 1 diabetes kidney codes | Counted as Dx claims (stage unspecified) | Keep, or exclude for HCP features |

---

## 6. Results (10 validation HCPs, 20 cohorts)

| Check | Result |
| --- | --- |
| Recount of every value from the raw 3.1 claims and patient stages (windows, stages, patient stages, shares, running totals) | **PASS:** 16,020 checks, 0 differences |
| Recount of HCP 1841364841 in the notebook, every cohort | **PASS:** 1,300 checks, 0 differences |
| Fast engine = step-by-step engine (first and last cohort) | **PASS:** 2,124 values, 0 differences |
| Same as NBA 3.0 at offset 0, on the NBA 3.0 data (19 months) | **PASS:** 0 differences |
| Output complete | 20 cohorts, 180 rows, no duplicates, no empty values |
| Provider table | 180 rows, every HCP mapped to a `PROVIDER_ID`, no duplicates |

---

## 7. Next steps

1. Same review for the combined claims notebook (NB04), which still reads NBA 3.0 Dx and lab tables (`Dx_03`, `Lab_04`).
2. Before the full run: the open points in section 5.

Details: `03 Diagnosis Claims Files/NBA_3_1_Dx_Claims_Features_Plan.md`.
