# Kerendia NBA 3.1 – HCP Lab Claims Features: Summary of Changes

> **Update 2026-11-11.** The sections below describe the Phase A sync (2026-11-03). Since then:
> * **Cohorts:** 28 cohorts c1–c28, offset 0, from the claims cohort file. Replaces 20 cohorts at offset 7.
> * **Output:** Delta partitioned by COHORT_SET (7 groups), few large files per group. Replaces Delta partitioned by COHORT_ID (decision X14).
> * **HbA1c / Potassium features added (X18):** 48 new features for HbA1c ≥ 9 and Potassium > 5 (total tested, total/eligible above threshold, PCT, each × 4 windows).
> * **9-month lookback removed (X19):** 21 features with `IN_LAST_9_MONTH` removed. Windows standardized to [1, 3, 6, 12].
> * **Feature count:** 3.0 = 116 features → 3.1 = 143 features (+48 new, −21 removed, net +27). Total columns = 152 (143 features + 9 metadata).
> * **Open points in section 5 resolved:** specialty filter and lab pull location are set.
> * See decisions X13–X24 in `NBA_3_1_HCP_Features_Decisions.md`.

**Scope:** HCP-level lab claims features (`02_claim_lab_monthly_cohort`): how many eGFR and UACR tests each HCP ordered, by CKD stage, per cohort, in the last 1, 3, 6 and 12 months  
**Baseline:** NBA 3.0 notebook `02_claim_lab_monthly` (calendar months)  
**Data used for validation:** IQVIA Quest lab data of the 10 validation HCPs, 20 cohorts 2025-01 .. 2026-08 at offset 7; all-US lab tables for the size checks  
**Status:** validated on the 10 HCPs (2026-11-03). The lab features now use the NBA 3.1 lab data; two points are open for the full run (section 5)

---

## 1. Summary

The lab claims features were already rebuilt for NBA 3.1 (cohorts with an offset, one run for all cohorts, checked against NBA 3.0). This step connects them to the NBA 3.1 lab data.

* **New input: the 3.1 lab data.** The lab features now count the tests from the 3.1 lab patient journey (one row per HCP, patient, day and test), instead of a separate NBA 3.0 HCP lab table (`Lab_03`). HCP features and patient journey now count the same tests with the same rules.
* **Why:** the NBA 3.0 HCP lab table held only about half of the lab tests: 108.8M tests since 2023 from 122.9K HCPs, against 190.1M in the NBA 3.0 lab journey and 207.5M from 199.9K HCPs in NBA 3.1. It came from an older, separate query.
* **Same stages:** a test counted in both tables has the same CKD stage (all US, June 2025: 100% of UACR and 99.98% of eGFR tests). The change is which tests are counted, not how they are staged.
* **Same columns:** all 102 feature names are unchanged.
* **Effect on the validation HCPs:** 498 lab tests instead of 240; 9 HCPs have lab features instead of 7 (3 new, 1 drops out). Over the last 12 months, the 9 HCPs ordered 151 tests (was 92).
* **All checks pass:** recount of every value from the raw tests (3,060 checks, 0 differences), fast engine = step-by-step version, same result as NBA 3.0 at offset 0 when run on the NBA 3.0 data (the counting logic is unchanged).

---

## 2. What the lab claims features use

| Input | Used for | Changed in 3.1? |
| --- | --- | --- |
| Lab tests of the 3.1 lab patient journey: one row per HCP, patient, day and test (eGFR or UACR), with the CKD stage | All 102 columns: tests by type (eGFR, UACR), by stage (eGFR stages 1–5, UACR A1–A3), total, shares, `RUNNING_` | **Yes:** was the NBA 3.0 HCP lab table `Lab_03` |

The lab patient journey's final table has one stage per patient and month, without the HCP. The features use its earlier step, which still has the HCP who ordered each test.

---

## 3. NBA 3.0 vs NBA 3.1 lab data

| Rule | NBA 3.0 HCP lab table | NBA 3.1 (now used) |
| --- | --- | --- |
| Which tests | Test names and units written in the SQL, older provider table | Lab basket (LOINC codes + test-name backup), current provider table |
| eGFR 150–200 | Dropped | Stage 1 |
| Results such as `>90` and `75^` | Dropped (plain numbers only) | Kept |
| Several eGFR equations on the same day | Median of all | The preferred one (race-free CKD-EPI 2021) |
| Valid range | None | eGFR 1–200, UACR 0–10,000 |
| Stage cut-offs | eGFR 5 stages, UACR A1–A3 | Same |
| Specialty filter | 10 primary-care codes | Same 10 codes (open decision L1 of the lab journey) |
| HCP universe | NBA 3.0 | NBA 3.1 |

| All US, tests since 2023 | NBA 3.0 HCP lab table | NBA 3.0 lab journey | NBA 3.1 (now used) |
| --- | --- | --- | --- |
| Tests | 108.8M | 190.1M | 207.5M |
| HCPs | 122.9K | 167.1K | 199.9K |

---

## 4. Effect on the validation HCPs (20 cohorts)

| | Before (NBA 3.0 HCP lab table) | After (NBA 3.1) |
| --- | --- | --- |
| Lab tests since 2023 | 240 | 498 (208 in both, all with the same stage) |
| HCPs with lab features | 7 | 9 |
| Rows (HCP x cohort) | 140 | 180 |
| Columns | 102 | 102, same names |
| All tests up to the last cohort (2026-08), 9 HCPs together | 238 | 480 |
| Tests in the last 12 months, last cohort | 92 | 151 |

* 3 HCPs get lab features for the first time (1215675616, 1396374062, 1528629052): their tests were missing in the NBA 3.0 HCP lab table.
* 1 HCP (1508230566) loses its 26 tests: it is not in the NBA 3.1 HCP universe (checked 2026-11-03: in the 3.0 universe, not in the 3.1 one), so the 3.1 lab data has no row for it. The same HCP drops out of all HCP features in the full run.
* For the 6 HCPs in both, about a quarter of the count values change (1,706 of 6,600), mostly upwards.

---

## 5. Open points for the full run

| Topic | Today | Proposal |
| --- | --- | --- |
| Where the 3.1 lab data is stored | Intermediate table of the patient-journey run of 2026-11-02 | Save it as a named output of every patient-journey run and point the lab features to it |
| Specialty filter and HCP universe | 10 primary-care codes; NBA 3.1 universe (HCP 1508230566 is not in it) | Same decision for both levels (lab journey L1); confirm the NBA 3.1 universe for the HCP features |

---

## 6. Results (10 validation HCPs, 20 cohorts)

| Check | Result |
| --- | --- |
| Recount of every value from the raw 3.1 tests (totals, eGFR, stage 3, A2, all windows, all-time total) | **PASS:** 3,060 checks, 0 differences |
| Recount of HCP 1528629052 in the notebook, every cohort | **PASS:** 900 checks, 0 differences |
| Fast engine = step-by-step engine (first and last cohort) | **PASS:** 1,800 values, 0 differences |
| Same as NBA 3.0 at offset 0, on the NBA 3.0 data (19 months) | **PASS:** 0 differences |
| Output complete | 20 cohorts, 180 rows, no duplicates, no empty values |
| Provider table | 180 rows, every HCP mapped to a `PROVIDER_ID`, no duplicates |

---

## 7. Next steps

1. Same review for the other HCP notebooks (Dx, combined claims, new patient starts, eligible patients); the combined claims notebook also uses an NBA 3.0 lab table.
2. Before the full run: the open points in section 5.

Details: `02 Lab Claims Files/NBA_3_1_Lab_Claims_Features_Plan.md`.
