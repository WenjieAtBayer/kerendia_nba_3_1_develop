# NBA 3.1 — HCP Claims Feature Review (NB01–NB06)

**Purpose:** Review each HCP-level claims feature family against the source findings and the NBA 3.0 model evaluation, and give a keep / fix / drop call per family.
**Date:** 2026-11-23
**Inputs:** `../01_Source_Review/` (Rx, Dx, Px, overview), `../02_NBA_3_0_Model_Evaluation/NBA_3_0_Model_Feature_Evaluation.md`, a text scan of the NB01–NB06 code (pattern counts only, not a full code read)

---

## 1. Summary

| Notebook | Source | 3.0 family SHAP share (validation sample) | Source finding | Call |
| --- | --- | --- | --- | --- |
| NB01 Rx claims | PJ03 output (`FCT_RX`) | Rx claims 34.56% + Kerendia writing 22.87% | RX-A | **Fix** |
| NB02 Lab claims | PJ01 output (`QUEST_TO_LAAD_HIST`) | 6.46% | S3, L-A, L-C | **Fix** |
| NB03 Dx claims | PJ02 output (`FACT_DX`) | 3.10% | DX-A, DX-C, DX-D | **Keep, check counting** |
| NB04 Monthly cohort | NB01–NB03 outputs | n/a (combination step) | inherits all | **Keep** |
| NB05 Rx NPS | PJ03 output | part of Kerendia writing 22.87% | RX-A | **Fix** |
| NB06 Eligible HCP | patient journey eligibility | not a 3.0 family | RX-A, PX-D | **Keep, re-run after C1 fix** |

Px-based features (3.0 share 3.04%) feed eligibility (dialysis) rather than a separate NB.

## 2. Code scan (text pattern counts)

| Notebook | `countDistinct` | `CLAIM_TYPE` | `distinct(` |
| --- | --- | --- | --- |
| NB01 `01_claim_rx_monthly_cohort` | 5 | 0 | 11 |
| NB02 `02_claim_lab_monthly_cohort` (.py) | 0 | 0 | 10 |
| NB03 `03_claim_diagnosis_monthly_cohort` | 0 | 0 | 12 |
| NB04 `04_claims_monthly_cohort` | 2 | 0 | 13 |
| NB05 `05_claim_rx_nps_monthly_cohort` | 7 | 0 | 16 |
| NB06 `06_claim_eligible_hcp` (.py) | 3 | 0 | 20 |

No notebook references `CLAIM_TYPE`. NB02 and NB03 never call `countDistinct`; whether their counts are rows or distinct claims/patients **has not been confirmed** (they may de-duplicate with `distinct()` first).

## 3. Per family

### NB01 — Rx claims (`01 Rx Claims Files/`)
* **Finding:** ~21% of Rx rows are reversed (11.4%) or rejected (9.7%) (Sep 2026); no claim-type filter in PJ03 or NB01.
* **3.0 signal:** the largest families. `RUNNING_TOTAL_HCP_RX_REJECTED_KERENDIA_CLAIMS` is rank 7, so rejected claims carry signal of their own.
* **Call: fix.** Count paid claims for TRx/NRx/NBRx; keep rejected (and reversed) as separate features. This also aligns with the target, which uses `CLAIM_TYPE = 'PD'`.
* **Redundancy:** a 22-feature cluster of Kerendia patient/NRx windows and a 12-feature SGLT2 / `SGLT2_WO_INVOKANA_300MG` cluster (supports O9: drop the WO_INVOKANA variants).

### NB02 — Lab claims (`02 Lab Claims Files/`)
* **Finding:** HIST stacks reloads (Jun 2024: Quest 69%, LabCorp 59% duplicate rows); LabCorp pre-2025 rows often lack patient ID; LabCorp is the only potassium and HbA1c source.
* **3.0 signal:** 6.46%, 97 features; 23 to dedupe, 2 drop / drop candidate.
* **Call: fix.** Apply the S3 dedup rule before counting; flag the 2025 LabCorp patient-ID change as a regime shift.

### NB03 — Dx claims (`03 Diagnosis Claims Files/`)
* **Finding:** ~27% of Dx rows repeat claim + code; ~20% have no referring/rendering provider; Jan 2023 coverage step.
* **3.0 signal:** 3.10%, 48 features; 7 to dedupe, 8 drop / drop candidate.
* **Call: keep, check counting.** Confirm NB03 counts distinct claims or patients (PJ02 3.1 already de-duplicates). Avoid growth features that span Jan 2023.

### NB04 — Monthly cohort (`04 Monthly Cohort Claims Files/`)
* Combination step; inherits all source issues. **Call: keep.** Re-run after the NB01/NB02 fixes.

### NB05 — Rx NPS (`05 Rx NPS Claims Files/`)
* **Finding:** same RX-A issue; a reversed claim could be counted as a new patient start.
* **Call: fix.** Use paid claims only for NBRx/NPS flags (same rule as the 3.0 target). Open item O10 (null vs 0) still applies.

### NB06 — Eligible HCP (`06 Eligible HCP Claims Files/`)
* Depends on patient eligibility (C1/C3/C9/C10 rules, dialysis flag from Px).
* **Call: keep, re-run** after the PJ06 C1 fix (O12). The thin latest Px month (PX-D) can miss a recent dialysis start.

## 4. Not checked

* Whether NB02/NB03 count rows or distinct entities (needs a code read).
* Impact of the claim-type fix on feature values (needs a re-run).
* Feature-by-feature mapping from 3.1 NB columns to 3.0 model features; 3.0 shares above are by family name keywords.
