# EDA Check 2 — TherapeuticClass Duplication in Step 2

**Question:** `bronze_statuses` repeats each drug under several `TherapeuticClass` values. Does Step 2 of the pipeline handle this correctly, and can class-level rows ever disagree?

**Status:** Complete (all periods, `bronze_statuses`, `bronze_restrictions`).

---

## 1. Rows per key

Key = `FormularyId x MedId x Period x feed_date`, all 15 periods.

| MedId | Drug | Classes | Rows per key | Keys with conflicting status |
|---|---|---|---|---|
| 607231 | Kerendia | CKD, CHF, Cardiovascular Agents | 3 | 0 |
| 582254 | Jardiance | CKD, CHF | 2 | 0 |
| 582255 | Jardiance | Blood Glucose Regulators | 1 | 0 |
| 580683 | Farxiga | CKD, CHF, Blood Glucose Regulators | 3 | 0 |
| 577710 | Invokana | CKD, CHF, Cardiovascular Agents | 3 | 0 |
| 595221 | Steglatro | CKD, CHF, Blood Glucose Regulators, Cardiovascular Agents | 4 | 0 |

* Status is **identical across classes** for every key (0 conflicts out of about 98K keys per drug).
* No true duplicates within a class.
* `bronze_restrictions` (PA / QL / ST detail) for Kerendia is also identical across classes (0 of 3,279 formulary x code keys differ).

## 2. Effect on the current pipeline

* Step 2a does not select `TherapeuticClass`. Step 2b uses `row_number()` over `(FormularyId, MedId, Period)` ordered by `feed_date DESC`, which keeps one row from the 2-4 tied class rows.
* Because the tied rows are identical, the result is **deterministic in value** even though the row picked is arbitrary. **No fix required**, but adding `TherapeuticClass = 'Nephrology - Chronic Kidney Disease'` to the filter reduces scanned rows about 3x and makes the intent explicit.

## 3. Related finding — Jardiance dual MedId (Q4)

* 582254 is listed under CKD / CHF, while 582255 is under Blood Glucose Regulators (the T2D listing).
* On the latest monthly snapshot, the two codes disagree on **0.06%** of formulary-periods (15 of 25,224), all `Preferred` (582254) vs `Preferred (PA/ST)` (582255).
* The "most favorable" rule therefore has negligible impact. Q4 can be closed. A simpler option is to use 582254 only, since it is the CKD listing.

## 4. Guidance for new features

* Statuses and restrictions: filter to one class (CKD) to avoid row multiplication. Exception: Jardiance 582255 exists only under Blood Glucose Regulators, so a CKD filter drops it (acceptable if 582254 is used for Jardiance).
* `bronze_pa_v2`, `bronze_st`, `bronze_pa_udf` are keyed by **IndicationName** rather than class, and **do differ** between CKD and Heart Failure. Always filter `IndicationName = 'Chronic Kidney Disease'` (or build CKD and HF features separately).
