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
| Record type (`CALL_REC_TYP_NM`) | Kind of visit | `Face2Face Signed`, `BPH_Face2Face_SIG`, `Group Call Signed` | `Face2Face Interaction Med`, `Non Face2Face Interaction Med`, `Remote Interaction Med`, `Group Interaction Med`, `Remote Group Interaction Med`, `BPH_MED_*` (5 variants), `Event Call Report` (11 types in total, section 2.2) |
| Product text (`DETL_PROD`) | What was discussed | `Kerendia`, `Kerendia;Lynkuet` | `Finerenone [Kerendia/Firialta] ...` plus an indication (CKD, DKD, HF, HFpEF, CVD, T1D); 1,082 different full texts in Year 1 + 2 (section 2.1). Also other medical products (Asundexian, Elinzanetant) |

**Rule (`MEDICAL` class):**

* the record type contains `Interaction Med` or `_Med`, starts with `BPH_MED_`, or is `Event Call Report` → **medical record**;
* and the product text contains `Finerenone` → **Kerendia-related medical record** (MD-1 scope).

MSL records use the scientific name **Finerenone**, not the brand name Kerendia. That is why NBA 3.0 never counted them: it only kept `DETL_PROD = 'KERENDIA'`. That happened by luck, not by design.

> **Issue: Kerendia (Finerenone) has many product names in medical records.** There is no single product value for Kerendia in MSL visits. The same medicine appears under **9 different names plus 3 cut-off fragments**, and a single call often lists several of them in one text. Any rule that tests for one exact value (as NBA 3.0 did with `'KERENDIA'`) will miss most visits. NBA 3.1 must test "product text **contains** `Finerenone`" (case-insensitive), and the list below should be confirmed with the CRM team (C3).

**Source of the numbers below:** `CPH_DB_PROD.MODEL_V2.FACT_CALL`, submitted calls Nov 2024 – Oct 2026, the 11 medical record types, product text containing `finerenone`; counts are calls, with no doctor filter (they include organisation / BHO IDs and calls without a customer match, so they are higher than the Phase 3 doctor counts). Queried 5 Nov 2026.

### 2.1 Kerendia (Finerenone) product names

**How the product text is built.**

* 36,816 medical calls mention Finerenone, with **1,082 different full product texts**.
* These texts are combinations of only **27 single products**; **19,669 calls (53%)** list more than one product in the same text, separated by several spaces (not by `;`).
* Every Finerenone value has the form `Finerenone [Kerendia/Firialta]` + optional indication + optional `(US)`.

**All Finerenone values (after splitting multi-product texts).** A call that lists two Finerenone values is counted under both.

| # | Product text value | Indication | Calls | Year 1 | Year 2 | First seen | Last seen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `Finerenone [Kerendia/Firialta] (US)` | None (general) | 15,762 | 7,452 | 8,310 | 2024-11-01 | 2026-10-30 |
| 2 | `Finerenone [Kerendia/Firialta] - HFpEF` | Heart failure (preserved EF) | 13,267 | 12,054 | 1,213 | 2024-11-01 | 2026-01-22 |
| 3 | `Finerenone [Kerendia/Firialta] - DKD (US)` | Diabetic kidney disease | 10,082 | 6,027 | 4,055 | 2024-11-01 | 2026-10-29 |
| 4 | `Finerenone [Kerendia/Firialta] - HFpEF (US)` | Heart failure (preserved EF) | 8,563 | 0 | 8,563 | 2025-11-07 | 2026-10-30 |
| 5 | `Finerenone [Kerendia/Firialta] - HF (US)` | Heart failure | 6,658 | 2,153 | 4,505 | 2025-06-20 | 2026-10-30 |
| 6 | `Finerenone [Kerendia/Firialta] - CKD` | Chronic kidney disease | 4,188 | 3,796 | 392 | 2024-11-01 | 2026-01-08 |
| 7 | `Finerenone [Kerendia/Firialta] - T1D (US)` | Type 1 diabetes | 3,218 | 409 | 2,809 | 2024-11-02 | 2026-10-30 |
| 8 | `Finerenone [Kerendia/Firialta] - CVD` | Cardiovascular disease | 2,408 | 2,170 | 238 | 2024-11-01 | 2026-01-28 |
| 9 | `Finerenone [Kerendia/Firialta] - CKD (US)` | Chronic kidney disease | 2,376 | 0 | 2,376 | 2025-12-01 | 2026-10-30 |
| 10 | `Finerenone` (cut off) | — | 31 | 6 | 25 | 2025-09-09 | 2025-12-17 |
| 11 | `Finerenone [Kere` (cut off) | — | 4 | 2 | 2 | 2024-11-19 | 2025-11-09 |
| 12 | `Finerenone [Keren` (cut off) | — | 2 | 0 | 2 | 2025-12-18 | 2025-12-18 |

**What to notice.**

* **Renaming around Dec 2025.** `- HFpEF` and `- CKD` were replaced by `- HFpEF (US)` and `- CKD (US)` (new values from Nov / Dec 2025, old ones last seen Jan 2026). `- CVD` stops in Jan 2026 and has no `(US)` version. A rule on exact names would break silently at each renaming.
* **New indications appear over time.** `- HF (US)` starts in June 2025 (HF approval July 2025); `- T1D (US)` is mostly Year 2.
* **Cut-off fragments** (37 calls) look like text truncated partway; they are still caught by "contains `Finerenone`".
* **No value says "Kerendia" alone.** The brand name only appears inside the brackets.

**Other products listed in the same text as Finerenone** (top values): `Cardiovascular Portfolio {Med} (US)` 1,653 calls; `Asundexian {Med} (US)` 47 and `Asundexian {Med} - FXIa Inhibitor (US)` 19; `Women's Healthcare Portfolio {Med} (US)` 20; `Others Portfolio {Med} (US)` 18; `Darolutamide [Nubeqa] (US)` 16; `Elinzanetant [Lynkuet] (US)` 10; `Elinzanetant {Med} (US)` 10; `Oncology Portfolio {Med} (US)` 5.

### 2.2 Medical record types (all 11)

`BPH_MED_*` is not one type but 5 separate types. Calls with Finerenone in the product text, Year 1 + 2:

| Record type (`CALL_REC_TYP_NM`) | Calls |
| --- | --- |
| `Face2Face Interaction Med` | 15,290 |
| `BPH_MED_Face2Face_Interaction_Med` | 8,074 |
| `Non Face2Face Interaction Med` | 3,895 |
| `BPH_MED_Non_Face2Face_Interaction_Med` | 2,942 |
| `Group Interaction Med` | 2,280 |
| `Remote Interaction Med` | 1,774 |
| `BPH_MED_Remote_Interaction_Med` | 926 |
| `Remote Group Interaction Med` | 605 |
| `Event Call Report` | 484 |
| `BPH_MED_Group_Interaction_Med` | 462 |
| `BPH_MED_Remote_Group_Interaction_Med` | 84 |

**Implications.**

* The MD-1 rule ("contains `Finerenone`") catches all 12 Finerenone values; no exact-name list is used.
* The record-type rule is pattern-based for the same reason: the old fixed list missed `Non Face2Face Interaction Med` and `Group Interaction Med` (5,045 Year 2 records leaked into rep visits before the 3 Nov fix).
* Indications are available in the text, but compliance approved only a yes / no flag; indication-level MSL features would need a separate approval (X3).
* Ask the CRM team (C3) to confirm the full list of Finerenone product names and medical record types, and to announce future renamings.

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
