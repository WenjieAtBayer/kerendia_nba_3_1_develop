# Phase 0 MSL Explained (V10)

**For:** readers new to the Kerendia field activity data  
**Validation step:** V10 of `40_field_activity_nba_3_1_readiness_plan.md`  
**Sources:** `40_field_activity_phase0_output_analysis.md` (V10, re-run 3 Nov 2026), `20_field_activity_data_review_2024_2026.md` (section 6.6), Phase 3 notebook `43_field_activity_phase3_events_irep_msl` (run 4 Nov 2026)  
**Years:** Year 1 = Nov 2024 – Oct 2025, Year 2 = Nov 2025 – Oct 2026

**V10 in one sentence.** V10 checks that MSL (medical) visits are found correctly in the call data: counted at the right volume, never counted as rep visits, and ready to feed one feature, the MSL flag (MD-1).

**Status.** Passed in Phase 0 after the fix of 3 Nov 2026. MD-1 built in Phase 3. Open: should the flag count Finerenone visits only, or any medical visit (A9 / C11)?

---

## 1. What is an MSL visit?

* A **rep** (sales consultant) visits a doctor to promote Kerendia. That is commercial activity.
* An **MSL** (Medical Science Liaison) is a scientist on Bayer's medical team. MSLs discuss scientific questions with doctors (study data, mechanism, new indications), and they are **not allowed to sell**.
* Both log their visits in the **same Veeva CRM**, so MSL visits land in the **same table as rep calls**: `CPH_DB_PROD.MODEL_V2.FACT_CALL`. Nothing in that table says "this is an MSL" directly; we recognise MSL visits from two fields.

---

## 2. How an MSL record is recognised

| Field | What it holds | Rep call example | MSL visit example |
| --- | --- | --- | --- |
| Record type (`CALL_REC_TYP_NM`) | Kind of visit | `Face2Face Signed`, `BPH_Face2Face_SIG`, `Group Call Signed` | `Face2Face Interaction Med`, `Non Face2Face Interaction Med`, `Remote Interaction Med`, `Group Interaction Med`, `Remote Group Interaction Med`, `BPH_MED_*`, `Event Call Report` |
| Product text (`DETL_PROD`) | What was discussed | `Kerendia`, `Kerendia;Lynkuet` | `Finerenone [Kerendia/Firialta] ...` plus an indication (CKD, DKD, HF, HFpEF, CVD, T1D); 1,073 different texts. Also other medical products (Asundexian, Elinzanetant) |

**Rule (`MEDICAL` class):**

* the record type contains `Interaction Med` or `_Med`, starts with `BPH_MED_`, or is `Event Call Report` → **medical record**;
* and the product text contains `Finerenone` → **Kerendia-related medical record** (MD-1 scope).

MSL records use the scientific name **Finerenone**, not the brand name Kerendia. That is why NBA 3.0 never counted them: it only kept `DETL_PROD = 'KERENDIA'`. That happened by luck, not by design.

---

## 3. Why V10 is needed

1. **MSL visits must never count as rep visits.** If they did, a doctor seeing an MSL would look "called by a rep", the model would learn from medical activity, and reps might be told to visit because of an MSL visit. That would be a compliance problem.
2. **Compliance allowed one thing** (30 Oct 2026): a **flag** "this doctor had a medical interaction in the last 6 / 12 months" (MD-1). Counts, topics or notes need a separate approval (X3).
3. So V10 checks **volume** (do we find the expected number of MSL visits?) and **classification** (does none leak into the HCP interaction class?).

---

## 4. What Phase 0 found

| Check | Result |
| --- | --- |
| Volume, Finerenone MSL visits | Year 1: 10,496 visits / 6,409 doctors; Year 2: 11,401 / 6,947. The review expected about 10,500 – 10,900 / 6,400 – 6,800; Year 2 is about 5% above, consistent with growing MSL activity |
| Volume, all medical products | Y1 22,773, Y2 30,673, about 2.8 times the Finerenone volume in Year 2, because the Asundexian and Elinzanetant MSL teams started |
| Classification, before the fix | **5,045 Year 2 MSL records were classed as doctor visits.** The old rule had a fixed list of record types and missed spellings such as `Non Face2Face Interaction Med` and `Group Interaction Med`. None had Kerendia in the product text, so the Kerendia counts were not affected. The notebook's own check reused the same list, so it could not see them |
| Classification, after the fix (3 Nov) | Record types matched by pattern instead of a list. An independent check finds **0** medical records among HCP interactions |

---

## 5. What Phase 3 found (MD-1 built)

| Year | All medical records | Finerenone (MD-1) | Doctors with Finerenone |
| --- | --- | --- | --- |
| Year 1 | 22,715 | 10,462 | 6,409 |
| Year 2 | 30,143 | 11,180 | 6,964 |

* Year 2 Finerenone visits by type: `Face2Face Interaction Med` 6,583, `Non Face2Face Interaction Med` 1,737, `Group Interaction Med` 1,440, `Remote Interaction Med` 786, `Event Call Report` 347, `Remote Group Interaction Med` 287.
* MSL activity is rising: 1,704 visits in Nov – Dec 2025, 3,207 in Q3 2026.
* In the training cohorts, 3,838 – 5,636 doctors per cohort have the 12-month flag; it is 0 for 87 – 93% of rows.
* Phase 3 counts are about 2% lower than Phase 0 (11,180 vs 11,401): the Phase 0 pattern also counted medical records on organisation (BHO) IDs; Phase 3 counts doctors only.

---

## 6. Example

Dr. C in Q3 2026:

| Date | Record type | Product text | Class | Counts as |
| --- | --- | --- | --- | --- |
| 5 Jul | `Face2Face Signed` | `Kerendia` | HCP interaction | Rep visit (Phase 1 features) |
| 12 Aug | `Face2Face Interaction Med` | `Finerenone [Kerendia/Firialta] HF` | Medical | MSL flag = 1 |
| 3 Sep | `Remote Interaction Med` | `Asundexian ...` | Medical | Not in MD-1 if the scope is Finerenone only |

Result: Dr. C has 1 rep visit and `FLD_MSL_INTERACTION_6M = 1`. Before the fix, the 3 Sep record could have been classed as a doctor visit (though not a Kerendia visit).

---

## 7. Open points

| # | Question | Why it matters | Who |
| --- | --- | --- | --- |
| A9 / C11 | Should the MSL flag count only Finerenone visits, or any medical visit? | The approval was for a Kerendia-related flag; non-Finerenone visits doubled in Year 2. Default: Finerenone only | Medical affairs, compliance |
| C3 | About 34K medical-type records sit on organisation (BHO) IDs (Y1 14,967, Y2 18,783). Drop them from organisation context? | They are MSL copies, not rep activity, but would feed the organisation features | CRM team, medical affairs |
| C3 | Is the record-type list complete? | A new MSL record type would leak into rep visits again | CRM team |
| — | Keep the MSL flag out of rep-facing driver text | Compliance: reps must not be steered by medical activity | NBA team |

**Safeguard.** The independent check (any `MED` record type, `Event Call Report` or `Finerenone` text among HCP interactions must be 0) runs in every pipeline run, to catch new spellings.
