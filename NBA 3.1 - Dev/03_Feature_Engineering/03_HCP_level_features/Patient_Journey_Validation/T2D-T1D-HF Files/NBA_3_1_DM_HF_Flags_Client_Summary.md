# NBA 3.1 – Diabetes type and heart failure flags: summary

**Date:** 2026-10-30  
**Notebook:** `Patient_Journey_Validation/T2D-T1D-HF Files/04_patient_journey_dm_hf_flags`  
**Details and all numbers:** `NBA_3_1_DM_HF_Flags_Plan.md` (same folder)

## Why this was needed

NBA 3.1 targets three patient groups instead of one: T2D + CKD (as in 3.0), T1D + CKD and heart failure. The 3.0 patient journey could only say *"this patient is diabetic"*. It could not tell T1D from T2D, and it had no heart failure at all. The new notebook keeps the 3.0 answer and adds the two missing ones.

## What we have now

| Question | 3.0 | 3.1 |
| --- | --- | --- |
| Is the patient diabetic? | Yes / no (`DIABETIC_FLAG`) | Kept as `T2D_FLAG_30`, so nothing breaks downstream |
| Which diabetes type? | Not answered: T1D patients were counted as T2D | `DM_TYPE` = T2D, T1D or OTHER, plus `DM_MIXED` for patients coded both ways |
| Heart failure? | Not answered | `HF_FLAG`, the HF type (`HF_TYPE`) and the first HF date |
| Which codes? | Word search on the description | The agreed product basket, plus a small additions file for codes the basket is missing |

## What it means in numbers

* **T2D: 77.2M → 73.5M patients (−4.7%).** Mainly two groups leave:
  * 2.5M patients whose only sign of diabetes is an SGLT2 prescription on its own (no diabetes diagnosis, no other diabetes drug). SGLT2s are also prescribed for HF and CKD, and 1.1M of these patients have HF, so many are likely not diabetic (D1).
  * 1.2M patients who are mostly coded as T1D.
* **T1D: 1.9M patients (new).** 1.2M of them were T2D in 3.0; 0.8M had no diabetes flag before.
* **Coding is often mixed:** 3.6M patients have both T1D and T2D codes. The type with more claim days wins (D2), and `DM_MIXED` keeps them visible so they can be excluded later if needed.
* **HF: 23.8M patients (new).** About half also have T2D; 11.7M have no diabetes, which is the group the HF indication adds. By type: 6.2M diastolic (closest to HFpEF), 4.4M systolic (closest to HFrEF), 5.4M both, 7.8M unspecified. Claims have no ejection fraction, so the type is an estimate from the code.
* **Validation HCPs (4,238 patients):** T2D 2,490 → 2,339, T1D 39, HF 1,309.

## How we know it is right

* The 3.0 rule, rerun in the new notebook, gives exactly the same 77,186,262 patients as the table the old notebook wrote.
* With the additions file, the T2D codes are exactly the 3.0 codes, and no T1D or HF code found by a description search is missing.
* For the validation patients, every flag was recomputed a second, independent way from the raw claims: 0 differences.

## Decisions taken (please review)

We took the option we think is best on each open question so the work can move on. Each one is easy to change.

| # | Decision | Why |
| --- | --- | --- |
| D1 | An SGLT2 on its own, with no diabetes diagnosis, no longer makes a patient T2D | SGLT2s are standard HF and CKD drugs; counting them would put many HF and CKD patients without diabetes in the T2D group |
| D2 | Patients coded both T1D and T2D get the type with more claim days (tie: T2D) | Uses the most frequent coding; ties go to the larger, 3.0 group |
| D3 | Insulins keep counting as in 3.0 when a patient has no diabetes diagnosis | Keeps parity with 3.0; they only matter for patients without any diabetes diagnosis (effect not measured separately) |
| D4 | CKD eligibility rule for T1D is set in the combine step (PJ06), not here. Proposal: same rule as T2D | Eligibility is decided per indication in PJ06 |
| D5 | Old ICD-9 codes (2013–2015) stay out, as in 3.0 | Claims are over 10 years old; recent patients are covered by ICD-10 |
| D6 | The additions file stays separate for now and is merged into the Dx basket with Saurabh once the Dx journey goes live | The Dx journey checks its basket against the original list; merging now would break that check |

## What happens next

1. Team review of the decisions above.
2. The new table is written when the 3.1 Dx table goes live, together with the Rx and Px tables.
3. The combine step (PJ06) then switches to the new flags and sets eligibility per indication: T2D + CKD, T1D + CKD and HF.
4. New HCP features become possible, for example the number of HF patients per HCP by HF type, or the number of T1D + CKD patients per HCP.
