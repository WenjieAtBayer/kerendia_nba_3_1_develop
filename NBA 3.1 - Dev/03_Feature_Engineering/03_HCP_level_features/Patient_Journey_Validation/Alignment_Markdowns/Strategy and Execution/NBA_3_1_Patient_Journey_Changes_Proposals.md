# NBA 3.1 – Patient journey changes: proposals for team review

**Date:** 2026-10-27  
**Scope:** patient journey notebooks in `03_Feature_Engineering/03_HCP_level_features/Patient_Journey_Validation/`  
**Source of truth:** `Final Product Basket/Kerendia_Dx_Final.csv`, `Kerendia_Lab_Final.csv`, `Kerendia_Rx_Final.csv` (the codes and products to be used in NBA 3.1)  
**Status:** **Proposals only. No notebook has been changed and nothing has been written to any table.**

This document collects the proposed changes, step by step, for the team to review before anything is changed. Each decision lists the alternative, so the team can choose differently. All checks behind the proposals are reported here; there are no separate QC notebooks or files.

### Progress by agenda item
| # | Item | Status | Section |
| --- | --- | --- | --- |
| 1 | Product basket: Dx codes | Proposed, waiting for review | 1.1 |
| 1 | Product basket: Lab codes | Reviewed, open questions | 1.2 |
| 2 | Treatment categories (Rx basket) | Proposed, waiting for review | 2 |
| 3 | Stage calculation | Skipped for now | – |
| 4 | PACE table | Skipped for now (which table is meant still to be confirmed) | – |
| 5 | Lab data source (LabCorp) | 3.0 usage reviewed, open questions | 5 |
| 6 | New features | Proposed, waiting for review | 6 |

---

## General flow: how the patient journey is built

Six notebooks build one monthly row per patient (`PATIENT_ID`, `DATE`) for the patients of the HCPs in scope. PJ01–PJ05 each read one claims source and write one table; PJ06 combines them; the HCP notebooks aggregate the result to HCP level.

| Step | Notebook | Source | What it produces | Output table | Agenda item |
| --- | --- | --- | --- | --- | --- |
| PJ01 | `01_patient_journey_labs` | Quest lab results (`STG_CAR_IQV_QUEST_TO_LAAD_HIST`), PCP specialties | eGFR and UACR values → GFR stage, UACR stage per patient-month | `kerendia_nba_3_1_lab_journey_validation` | 1 (Lab basket), 5 (LabCorp) |
| PJ02 | `02_patient_journey_dx` | LAAD Dx claims | CKD stage from diagnosis codes, forward-filled by month | `kerendia_nba_3_1_dx_journey_validation` | 1 (Dx basket) |
| PJ03 | `03_patient_journey_rx` | LAAD Rx claims + `CKD_PRODUCT_MAPPING_VW` | Active treatment classes and brands per patient-month (days supply + 7-day gap) | `kerendia_nba_3_1_rx_journey_validation` | 2 (Treatment categories) |
| PJ04 | `04_patient_journey_t2d_flag` | LAAD Dx (T2D text) + diabetes Rx tables | T2D flag per patient | `kerendia_nba_3_1_t2d_validation` | 1 (Dx basket, T2D codes) |
| PJ05 | `05_patient_journey_px` | LAAD Px claims | Dialysis flag | `kerendia_nba_3_1_px_validation` | 1 (Px basket, later) |
| PJ06 | `06_patient_journey_combine` | PJ01–PJ05 outputs | Final stage (`GFR_DX_STAGE` = Dx, else lab GFR; `GFR_UACR_DX_STAGE` adds UACR), eligibility, new/total treatments, SGLT2 filter | `pat_new_and_total_treatments`, `pat_new_ckd_stage`, `pat_gfr_dx_stage`, `pat_uacr_stage`, `pat_sglt2_filter_m` | 3 (Stage calculation) |
| HCP | NB01–NB06 (`hcp_level_features`) | PJ06 outputs + `Rx_01_new`, `Rx_05`, `Dx_03` | HCP-level patient counts by stage, treatment, brand | HCP feature tables | 6 (New features) |

A change in PJ01–PJ05 only reaches the model after PJ06 and the HCP notebooks are re-run. The HCP notebooks also read their own inputs (`Rx_01_new`, `Rx_05`, `Dx_03`), which use the 3.0 code lists, so each basket change has to be applied there too.

---

## 1. Product basket (Dx and Lab codes)

### 1.1 Dx codes: proposed change to `02_patient_journey_dx`

#### Proposed change (not applied)
All changes are in the "Load dx data" cell (cell 6):
* Replace the 163-entry `DIAGNOSIS_CODE IN (...)` list with a 28-code dictionary `DX_STAGE_BY_CODE` (code → stage) defined at the top of the cell.
* Set the CKD stage from **DIAGNOSIS_CODE** (`CASE DIAGNOSIS_CODE WHEN 'N18.1' THEN 1 ... ELSE 0 END`, built from the dictionary) instead of `CASE CATEGORY = '<description text>'`. The text rule never matches N18.30/31/32 (stage 3a/3b/unspecified) and the list has no stage 5 codes, so 3.0 has no stage 3 or stage 5 Dx patients.
* Add `DX.DIAGNOSIS_CODE` to the inner and outer SELECT so `df_dx` keeps the code for QC. The output table schema (`PATIENT_ID, DATE, DX_STAGE, DX_STAGE_UPDATED, cohort_label`) does not change.

Proposed dictionary:
```python
DX_STAGE_BY_CODE = {
    "N18.1": 1, "N18.2": 2,
    "N18.3": 3, "N18.30": 3, "N18.31": 3, "N18.32": 3,
    "N18.4": 4,
    "N18.5": 5, "N18.6": 5, "I12.0": 5, "I13.11": 5, "I13.2": 5,   # stage 5 / ESRD
    "N18.9": 0, "I12.9": 0, "I13.0": 0, "I13.10": 0,                # CKD, stage unknown
    "E11.21": 0, "E11.22": 0, "E11.29": 0,
    "E08.21": 0, "E08.22": 0, "E08.29": 0,
    "E13.21": 0, "E13.22": 0, "E13.29": 0,
    "E09.22": 0, "D63.1": 0, "Z99.2": 0,
}
```

#### Code → stage mapping

| Stage | Codes |
| --- | --- |
| 1 | N18.1 |
| 2 | N18.2 |
| 3 | N18.3, N18.30, N18.31, N18.32 |
| 4 | N18.4 |
| 5 | N18.5, N18.6, I12.0, I13.11, I13.2 |
| 0 (CKD, stage unknown) | N18.9, I12.9, I13.0, I13.10, E11.21, E11.22, E11.29, E08.21, E08.22, E08.29, E13.21, E13.22, E13.29, E09.22, D63.1, Z99.2 |

Stage 0 becomes null before forward fill, as in 3.0. These codes add patients to the Dx spine but do not set a stage.

#### Added (in the basket, missing from 3.0)
Patients are approximate distinct counts in LAAD Dx, 2025-01 to 2026-09, all HCPs.

| Code | Description | Stage | Patients |
| --- | --- | --- | --- |
| N18.31 | CKD stage 3a | 3 | 8.24M |
| N18.30 | CKD stage 3 unspecified | 3 | 6.73M |
| N18.32 | CKD stage 3b | 3 | 4.97M |
| N18.6 | End stage renal disease | 5 | 1.85M |
| I12.0 | Hypertensive CKD with stage 5 / ESRD | 5 | 1.20M |
| N18.5 | CKD stage 5 | 5 | 0.76M |
| I13.2 | Hypertensive heart + CKD with HF and stage 5 / ESRD | 5 | 0.74M |
| I13.11 | Hypertensive heart + CKD without HF, stage 5 / ESRD | 5 | 0.15M |

For comparison, the legacy N18.3 code, the only stage-3 code 3.0 could stage, has 13.8K patients in the same window.

#### Removed from the 3.0 list
| Group | Codes | Why | Volume lost |
| --- | --- | --- | --- |
| ICD-9 | 249.4x, 250.4x, 285.21, 403.x, 404.x, 585.x, 588.81, V42.0 (32 codes) | ICD-9 retired in 2015; data starts 2019 | 0 |
| Procedure / revenue codes typed as Dx | 909.18–909.99 (CPT 90918–90999), 5A1.D00Z…, 0TY0.0Z0…, 3E1.M39Z, G02.57, G03.xx, G90.1x, S93.3x, 503.6x, S20.65, 399.5, 549.8, 556.9, 995.xx, 800–889 (~99 codes) | Not diagnosis codes (decimal inserted); cannot match the Dx table | 0 |
| Non-billable header codes | N18, I12, I13, I13.1, E08.2, E09.2, E11.2, E13.2 | Not in basket; parent categories | ~1.4K patients |
| Not in basket | E09.21, E09.29, N25.81, Z94.0 | Not in basket | ~2.6K patients (N25.81 and Z94.0 = 0) |

#### Decisions to confirm with the team
| # | Proposed decision | Alternative | How to change |
| --- | --- | --- | --- |
| D1 | PJ02 uses only the **CKD subset** of the Dx basket. T2D, HF, PVD, anemia, cardiomyopathy and other codes are not used for staging | Use the full basket in PJ02 | Add codes to `DX_STAGE_BY_CODE` with stage 0. Not recommended: it would put every T2D/HF patient into the Dx spine and inflate NB03 Dx counts. These codes belong in the T2D flag (PJ04), a new HF flag and new features |
| D2 | **T1D kidney codes excluded** (E10.21, E10.22, E10.29; ~0.17M patients) | Include them as stage 0 | Add the 3 codes with value 0. Excluded because the Kerendia label is T2D + CKD and 3.0 never had E10 codes |
| D3 | **ESRD merged into stage 5** (N18.6, I12.0, I13.11, I13.2 → 5) | Separate ESRD value (e.g. 6) or flag | Change the values in `DX_STAGE_BY_CODE`. Kept as 5 so downstream stage pivots (1–5) still work; dialysis is already flagged by `05_patient_journey_px` |
| D4 | **Z99.2 (dialysis dependence) kept as stage 0**, same as 3.0 | Map to 5 | Change Z99.2 to 5 in `DX_STAGE_BY_CODE` |
| D5 | **Not in PJ02, for later:** R80.9 proteinuria, I15.1, I70.1, Z49.01/02/31/32 (dialysis encounters), Z48.22 (transplant aftercare) | Add to PJ02 | Better suited to a dialysis/transplant flag or new features (agenda item 6) |

#### Expected impact (10 test HCPs, offset 7)
| Stage | Patients today (3.0 code list) | Patients with proposed basket |
| --- | --- | --- |
| 0 / unknown | 810 | 1,076 |
| 1 | 12 | 9 |
| 2 | 60 | 61 |
| 3 | **0** | **690** |
| 4 | 257 | 288 |
| 5 | **0** | **326** |

Patients in the Dx spine went from 817 to 1,162, and patient-month rows from 37,582 to 53,452. A patient can appear in more than one stage over time. Stage 1 dropped slightly because the monthly maximum now catches higher stages.

#### Downstream impact (if approved)
* `06_patient_journey_combine` → `pat_new_ckd_stage`, `pat_gfr_dx_stage`, `pat_uacr_stage`, and eligibility. Stage 3 and 5 Dx patients now exist, and Dx still overrides lab in `GFR_DX_STAGE` (to be reviewed under agenda item 3, stage calculation).
* HCP NB03 (`WITH_PATIENT_*` stage columns) and NB04 families A/C change after PJ06 is re-run.
* NB03's own source `Dx_03` uses the 3.0 code list and the same text mapping. It needs the same refresh to match.

#### Next steps
* Team review of D1–D5.
* After approval: apply the change to PJ02, write `kerendia_nba_3_1_dx_journey_validation`, then re-run PJ06 and the HCP notebooks.
* Apply the same Dx mapping to `Dx_03` (HCP NB03 source).

### 1.2 Lab codes: review of `Kerendia_Lab_Final.csv` against `01_patient_journey_labs`

The basket defines tests by **LOINC**. `01_patient_journey_labs` currently identifies tests by name pattern (`%GFR%`, `%GLOMERULAR%`, `%ALB%`, `%RATIO%`) plus a unit filter (`ML/MIN/1.73M2`, `MG/GCREAT`, …).

Points to check before switching to LOINC (from a reading of the codes; to be confirmed against the data):
* **eGFR group (12 entries):** 88294-4 is listed twice and 3 entries are `nan`. 48643-1 (MDRD, Black) appears to be missing.
* **UACR group (14 entries):** the core ratio code 14959-1 (microalbumin/creatinine, mass ratio, urine) appears to be missing. Several listed codes look like components or collection codes, not the ratio result: 2160-0 (serum creatinine), 61151-7 (serum albumin), 2161-8 and 14683-7 (urine creatinine), 13362-9 and 19153-6 (urine collection/volume). Applying the UACR cut-offs (30 / 300 mg/g) to these would give wrong stages, so they should not feed staging.
* **Potassium 2823-3 and HbA1c 4548-4** are new. They should not feed GFR/UACR staging and will be added as separate test types for new features (agenda item 6).
* Prerequisite: confirm that the Quest source `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_QUEST_TO_LAAD_HIST` has a LOINC column (agenda item 5 also covers LabCorp).

#### Next steps
* Check the LOINC column in the Quest source.
* Then propose the PJ01 change (LOINC lists for eGFR and UACR) for team review.

---

## 2. Treatment categories: proposed change to `03_patient_journey_rx`

### How categories are built today
* Step 2 inner-joins Rx claims to `PHCDW.PHCDW_DSAA.CKD_PRODUCT_MAPPING_VW` on `PRODUCT_NAME` and **drops every product whose `Treatment_Category` contains "other"**. Products not in the view are dropped by the inner join.
* Step 4 overrides only the brand column `CATEGORY` (Invokana 100/300 MG, Jardiance, Farxiga, a DPP-IV list, a GLP-1 list). `TREATMENT_CATEGORY` is never overridden.
* Resulting classes: ACE/ ARB, Calcium channel / Beta blocker, Combo drug, Diuretic_NON_MRA, Insulin, metformin, MRA, SGLT2.

Current mapping as seen in the 3.0 Rx input (`Rx_01_new`, same view, claims since 2025-01): 9 categories, one of which (`Other- glucose mgmt`, 45 products) is filtered out. Product counts per category: Calcium channel / Beta blocker 53, Insulin 46, Other- glucose mgmt 45, Combo drug 39, ACE/ ARB 32, Diuretic_NON_MRA 27, SGLT2 13, metformin 6, MRA 5.

### Main findings
| # | Finding | Evidence |
| --- | --- | --- |
| F1 | **GLP-1 is effectively missing.** Ozempic, Rybelsus, Trulicity, Victoza, Bydureon and Byetta are mapped to `Other- glucose mgmt` and dropped. The GLP-1 override list never fires for them. Only Xultophy (mapped to Insulin) gets the GLP-1 brand | 14 GLP-1 patient-months vs 17,734 SGLT2 in the 3.1 validation Rx journey (10 test HCPs) |
| F2 | **Tirzepatide and new semaglutide brands are not in the view**: Mounjaro (4.91M basket patients), Zepbound (2.15M), Wegovy (1.46M), Wegovy HD, generic liraglutide, Saxenda, exenatide | Not found in the mapping |
| F3 | **DPP-IV is never a category.** All DPP-IV products sit in `Other- glucose mgmt` and are dropped; generic sitagliptin, Zituvio, Zituvimet and saxagliptin are not in the view | No DPP-IV value in `TREATMENT_CATEGORY` |
| F4 | **Kerendia is not in the view** (0.19M basket patients) | Not found in the mapping |
| F5 | **SGLT2 gaps**: generic dapagliflozin (1.07M), dapagliflozin/metformin, Trijardy XR, Brenzavvy, Inpefa not in the view | Not found in the mapping |
| F6 | **Single-ingredient ACE/ARB mapped to `Combo drug`**: losartan (8.60M), enalapril, fosinopril, quinapril, Micardis | Basket group ARB/ACE vs view `Combo drug` |
| F7 | **Class conflicts**: Lotrel (amlodipine/benazepril) in CCB/BB; spironolactone/HCTZ in Diuretic_NON_MRA; Entresto in ACE/ ARB, generic sacubitril/valsartan (0.60M) not in the view | Basket groups ACE, SPIRONOLACTONE, ENTRESTO |
| F8 | **Missing variants in existing classes**: nebivolol (0.34M), diltiazem forms (Dilt-XR, Tiadylt, diltiazem HCl / ER), carvedilol phosphate ER, verapamil SR, Hemangeol, Katerzia, Norliqva, nimodipine; diuretics Hemiclor, Inzirqo, Soaanz, Furoscix; ACE moexipril; insulin generics and pens (insulin glargine / -yfgn, degludec, Lyumjev, Merilog, Rezvoglar, Relion pens) | Not found in the mapping |
| F9 | **Basket products that are not treatments for these classes**: CGMs, insulin pumps, glucagon rescue; CKD-complication drugs (iron, ESAs, phosphate binders, calcitriol, paricalcitol, cinacalcet); HF drugs (Verquvo, ivabradine, BiDil); renin inhibitors (aliskiren, Tekturna); Baxfendy | In basket, not in the view |
| F10 | **In the view but not in the basket**: ~73 older brand names (Coreg, Lopressor, Hyzaar, Vasotec, Glucophage, indapamide, Onglyza, Amaryl, …), ~0.24M patients in total | Same molecules as basket products, low volume |

Note: the basket `PRODUCT_GROUP` mixes classes (ACE, ARB, BB, DIURETICS), brands (JARDIANCE, OZEMPIC) and a large `OTHERS` bucket (CCBs, metformin, sulfonylureas, DPP-IV, iron, …), so it cannot be used directly as `TREATMENT_CATEGORY`. A product → class mapping has to be built from it.

### Proposed change (not applied)
Replace the `CKD_PRODUCT_MAPPING_VW` join and the Step 4 overrides with a 3.1 mapping built from `Kerendia_Rx_Final.csv` (clubbed rows expanded to their members): `PRODUCT_NAME → TREATMENT_CATEGORY, BRAND`, stored as a small table or CSV and joined on `PRODUCT_NAME`. Step 3 (days supply + 7-day gap) and Step 5–6 (monthly aggregation) stay as they are.

Proposed classes:

| TREATMENT_CATEGORY | Products | BRAND values | vs 3.0 |
| --- | --- | --- | --- |
| ACE/ ARB | All ACE and ARB products, single and fixed-dose combos (incl. losartan, Lotrel, Edarbi/Edarbyclor, Micardis) | ACE/ ARB | Absorbs `Combo drug` (F6, F7) |
| ARNI | Entresto, sacubitril/valsartan | ENTRESTO | New (HF) |
| SGLT2 | Jardiance, Farxiga, dapagliflozin, Invokana, Steglatro, Brenzavvy, Inpefa and combos (Synjardy, Xigduo, Glyxambi, Trijardy, Qtern, Steglujan, Segluromet, Invokamet) | JARDIANCE, FARXIGA, INVOKANA 100MG / 300MG, SGLT2 | Adds F5 |
| GLP-1 | Ozempic, Wegovy, Rybelsus, Trulicity, Victoza, liraglutide, Saxenda, Bydureon, Byetta, exenatide, Mounjaro, Zepbound | SEMAGLUTIDE, TIRZEPATIDE, OTHER GLP-1 | New as a class (F1, F2) |
| DPP-IV | Januvia, Janumet, Tradjenta, Jentadueto, sitagliptin, Zituvio, saxagliptin, alogliptin and combos | DPP-IV | New as a class (F3) |
| MRA | Spironolactone (incl. /HCTZ), Aldactone, Carospir, eplerenone, Inspra | MRA | Fixes F7 |
| Kerendia | Kerendia | KERENDIA | New (F4), see D9 |
| Diuretic_NON_MRA | Loop, thiazide, potassium-sparing (non-MRA) diuretics | Diuretic_NON_MRA | Adds F8 |
| Calcium channel / Beta blocker | CCBs and beta blockers | Calcium channel / Beta blocker | Adds F8 |
| Insulin | All insulins incl. Soliqua and Xultophy | Insulin | Adds F8 |
| metformin | Metformin IR/ER | metformin | Same |
| Other glucose mgmt | Sulfonylureas, pioglitazone, meglitinides, acarbose/miglitol, Symlin, Cycloset | – | Excluded, same as 3.0 (D8) |

### Decisions to confirm with the team
| # | Proposed decision | Alternative | How to change |
| --- | --- | --- | --- |
| D6 | **Merge `Combo drug` into ACE/ ARB.** In the current view most of `Combo drug` is plain losartan / enalapril, so the class is not meaningful | Keep `Combo drug` for fixed-dose combinations only | Map combo product names to `Combo drug` in the new mapping. Changes `TOTAL_TREATMENTS` (a combo counts as 1 instead of 2 classes) |
| D7 | **Add GLP-1 and DPP-IV as treatment classes**, with GLP-1 brands split into semaglutide / tirzepatide / other | Keep them out, as in 3.0 | Drop the two classes from the mapping. Recommended to add: GLP-1 is a direct competitor in T2D + CKD (A2 in the recommendations) |
| D8 | **Keep other glucose-lowering drugs (sulfonylureas, TZD, …) excluded**, as in 3.0 | Add them as an `Other glucose mgmt` class | Remove the "other" filter for that class |
| D9 | **Kerendia as its own class (nsMRA), not merged with steroidal MRA.** Before it feeds `TOTAL_TREATMENTS` or the NB04 brand pivots, check for target leakage, since the model predicts Kerendia prescribing | Leave Kerendia out, as in 3.0 | Remove the row from the mapping |
| D10 | **ARNI as its own class** | Keep Entresto in ACE/ ARB | Map ARNI products to ACE/ ARB |
| D11 | **Not treatment classes:** CGMs, pumps, glucagon, CKD-complication drugs, other HF drugs, renin inhibitors, Baxfendy (class to be confirmed). Proposed for new features (agenda item 6) | Add them to the mapping | Add rows with a new class |
| D12 | **Keep the ~73 older brand names that are in the view but not in the basket** (same molecules, ~0.24M patients) | Use only basket products | Drop them from the mapping |

### Downstream impact (if approved)
* `06_patient_journey_combine`: `TOTAL_TREATMENTS` / `NEW_TREATMENTS` in `pat_new_and_total_treatments` rise for patients on GLP-1 / DPP-IV / ARNI / newly mapped products, and fall where `Combo drug` merges into ACE/ ARB. The SGLT2 eligibility flag (`pat_sglt2_filter_m`) picks up generic dapagliflozin and the new SGLT2 brands.
* HCP NB01 (`WITH_n_ACTIVE_TREATMENT` columns), NB04 family C (category × brand pivots) and NB06 change after PJ06 is re-run. NB04 gets new pivot values (GLP-1, DPP-IV, ARNI, Kerendia).
* NB01 / NB04 / NB05 also read `Rx_01_new` / `Rx_05`, which use the same view. They need the same mapping to stay consistent.

### How this was checked
The current mapping was taken from the product names and categories in `Rx_01_new` (claims since 2025-01), which is built from the same view. A product with no claims in that period would not show up, so a direct check against the view is still to be done; its result will be added to this section.

### Next steps
* Team review of D6–D12.
* Confirm Baxfendy's class.
* Check the mapping directly against `CKD_PRODUCT_MAPPING_VW`.
* After approval: build the 3.1 product → class mapping from `Kerendia_Rx_Final.csv`, then apply it in PJ03 and in the `Rx_01_new` / `Rx_05` inputs.

---

## 5. Lab data source: is LabCorp used in NBA 3.0?

### How this was checked
Code search of all notebooks, files and queries under `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop` for `LabCorp` (any casing, with or without space or underscore) and for the view `KERENDIA_LAB_QUEST_LABCORP_VIEW`. Every match was then read cell by cell.

### Result: LabCorp is not used in any active 3.0 code
8 notebooks mention LabCorp. They are copies of two notebooks, `00_Write_Input_Files` and `02_claim_lab_monthly`, in four folders. In all of them the mention is a comment, a commented-out query or a markdown header.

| Folder | Notebook | Where LabCorp appears | Active lab source |
| --- | --- | --- | --- |
| `NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features` (production) | `00_Write_Input_Files` | Comment `# Concatenated LABCORP, PROGOSE date` above the Lab_02 query; that section is titled "Not used" and is skipped | Lab_03: `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_QUEST_TO_LAAD_HIST` (Quest only) |
| same | `02_claim_lab_monthly` | Markdown header lists `PHCDW.PHCDW_DSAA.KERENDIA_LAB_QUEST_LABCORP_VIEW` as data source | Reads `Lab_03` from the volume (Quest only). The header is out of date |
| `NBA 3.0 Dev/08_HCP_Level_Model/03_Feature_Engineering/03_HCP_Level_Features` | `00_Write_Input_Files` | "Komodo Lab 24" section: query on `KERENDIA_LAB_QUEST_LABCORP_VIEW` commented out with the note "Old query changed on 3rd may 24", replaced by "Updated lab data with 100% Quest data" (`PHCDW_SANDBOX.VIEW_RB_QUEST_PROGNOSE_20230924`) | Lab_02, Lab_03, Lab_04 and the patient journey lab query: Quest only |
| same | `02_claim_lab_monthly` | Same markdown header | Reads `Lab_03` (Quest only) |
| `NBA 3.0 Dev/99_Patient_Level_Model/04_HCP_Level_Features` | `00_Write_Input_Files` | Commented-out Lab_02 query that unions **LabCorp** (`KERENDIA_LAB_QUEST_LABCORP_VIEW`, 2020-01-01 to 2021-06-30) with **Quest Prognos** (`VIEW_RB_QUEST_PROGNOSE_20230924`, from 2021-07-01) | Quest only |
| same | `02_claim_lab_monthly` | Same markdown header | Quest only |
| `NBA 3.0 Dev/99_Patient_Level_Model/07_Model_Evaluation/Model - Backtesting/04_HCP_Level_Features_backtesting` | `00_Write_Input_Files`, `02_claim_lab_monthly` | Backtesting copies of the two notebooks above, same pattern | Quest only |

How the 3.0 lab source changed over time, from the comments in the code:
* Up to May 2024: LabCorp (`KERENDIA_LAB_QUEST_LABCORP_VIEW`) for 2020-01 to 2021-06, joined with Quest Prognos from 2021-07.
* 2024-05-03: switched to "100% Quest data" (`VIEW_RB_QUEST_PROGNOSE_20230924`).
* Current Ops pipeline and 3.1 `01_patient_journey_labs`: `STG_CAR_IQV_QUEST_TO_LAAD_HIST` (Quest only).

So NBA 3.0 has no LabCorp lab results. Adding LabCorp in 3.1 would be a new source, not a restore of existing 3.0 logic.

### Open questions before adding LabCorp in 3.1
| # | Question | Why it matters |
| --- | --- | --- |
| Q1 | Does `PHCDW.PHCDW_DSAA.KERENDIA_LAB_QUEST_LABCORP_VIEW` still exist and is it refreshed? Last used in code in May 2024, for dates up to 2021-06 | It is the only LabCorp source referenced in 3.0 |
| Q2 | Is there another LabCorp feed (e.g. the one behind `kerendia_nba_3_pace.new_writers_lab_data`, which counts Quest/LabCorp patients per NPI since 2024-01)? | PJ01 needs patient-level results, not NPI-level counts |
| Q3 | Do LabCorp patient IDs match LAAD / Quest `PATIENT_ID`? | PJ06 joins lab, Dx and Rx on `PATIENT_ID` |
| Q4 | Does the LabCorp source have LOINC, result value and unit columns? | Needed to apply the basket LOINC lists (section 1.2) and the eGFR / UACR cut-offs |
| Q5 | How much do Quest and LabCorp overlap (same patient, same date)? | Avoid double counting tests and medians |
| Q6 | Why was LabCorp dropped in May 2024? | Could be a known data quality or coverage issue |

### Next steps
* Ask the 3.0 owners about Q6 and whether a current LabCorp feed exists (Q1, Q2).
* If a source exists: check Q3–Q5 against the data and report the results in this section.
* Then propose the PJ01 change (Quest + LabCorp union) for team review.

---

## 6. New features

### Scope and starting point
This section expands the "add" candidates in `Feature Analysis/NBA_3_1_HCP_Claims_Features_Recommendations.md` (IDs such as PJ7, C7, N3 refer to that file) and adds new candidates that come from the Final Product Basket work in sections 1, 2 and 5. Fixes and removals from that file (P0 items, column slimming) are not repeated here.

Features are built in two layers:
* **Patient layer (6.1):** one flag or value per patient-month, built in the patient journey notebooks (PJ01–PJ06). These are the building blocks.
* **HCP layer (6.2):** counts and shares of an HCP's patients, built in the HCP notebooks from the patient layer.

Priority legend as in the recommendations file: **P1** high value, **P2** optional. "NEW" marks candidates that are not in the recommendations file.

### 6.1 Patient layer: building blocks

| # | Flag / value | Definition | Source | Depends on | Origin | Priority |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | `T2D_FLAG` (time-aware) | 1 from the first T2D event onward: Dx E11.x (basket "defining" T2D codes) or a T2D-specific Rx (SGLT2, GLP-1, DPP-IV, metformin, insulin with E11 Dx). T1D-only patients (E10.x without E11.x) = 0 | PJ02 Dx, PJ03 Rx (replaces the text match `%TYPE 2 DIABETES%` in PJ04) | 1.1, 2 | PJ7, E2 | P1 |
| P2 | `CKD_FLAG` (time-aware) | 1 from the first of: CKD Dx in the 1.1 dictionary, **or** two eGFR < 60 or two UACR ≥ 30 at least 90 days apart (KDIGO definition) | PJ01 lab, PJ02 Dx | 1.1, 1.2 | NEW (lab-based CKD) | P1 |
| P3 | `T2D_CKD_LABEL_FLAG` | `T2D_FLAG` AND `CKD_FLAG` AND NOT `ESRD_DIALYSIS_FLAG` | P1, P2, P5 | 1.1, 1.2, 2 | PJ7 | P1 |
| P4 | `HF_FLAG` and `HF_TYPE` | `HF_FLAG` = any HF Dx: I50.x, I11.0, I13.0, I13.2, I09.81 (all in the Dx basket). `HF_TYPE`: **PRESERVED_PROXY** = I50.3x (diastolic), **REDUCED_PROXY** = I50.2x (systolic), **MIXED** = I50.4x, **UNSPECIFIED** = other | PJ02 Dx | 1.1 | PJ7, extended | P1 |
| P5 | `ESRD_DIALYSIS_FLAG` | Dx N18.6, Z99.2, Z49.01/02/31/32, or a dialysis CPT from the Px basket (90935, 90937, 90945, 90960–90966, 90999). Replaces `%DIALYSIS%` text match in PJ05 | PJ02 Dx, PJ05 Px | 1.1 (D4, D5) | PJ10 | P1 |
| P6 | `KIDNEY_TRANSPLANT_FLAG` | Dx Z48.22 (aftercare following kidney transplant). Z94.0 is not in the basket | PJ02 Dx | 1.1 | PJ10 | P2 |
| P7 | `STAGE_SOURCE`, `STAGE_KNOWN` | Where the stage came from (lab / Dx / both) and whether it is known | PJ06 | 1.1, 1.2 | PJ8 | P2 |
| P8 | Therapy booleans | `ON_SGLT2`, `ON_GLP1_SEMAGLUTIDE`, `ON_GLP1_TIRZEPATIDE`, `ON_GLP1_OTHER`, `ON_DPP4`, `ON_ACE_ARB`, `ON_ARNI`, `ON_STEROIDAL_MRA`, `ON_KERENDIA`, `ON_INSULIN`, `ON_METFORMIN` (active supply in the month) | PJ03 | 2 (classes D6–D10) | PJ5, A2 | P1 |
| P9 | `UACR_TESTED`, `EGFR_TESTED` | Any UACR / eGFR test in the month, from Quest (basket LOINCs) **or** LAAD Px CPT 82043 (urine albumin), 82570 (urine creatinine), 82565 (serum creatinine), 80047/80048/80053 (panels with creatinine) | PJ01 lab, PJ05 Px | 1.2, 5 | L1 | P1 |
| P10 | `LAST_EGFR`, `EGFR_DECLINE_30PCT_24M` | Last eGFR value; flag when eGFR fell ≥ 30% vs the highest value in the prior 24 months | PJ01 lab | 1.2 | NEW | P2 |
| P11 | `LAST_POTASSIUM`, `POTASSIUM_GT_5` | Last serum potassium (LOINC 2823-3); flag if > 5.0 mmol/L | PJ01 lab | 1.2 | NEW | P1 |
| P12 | `LAST_HBA1C`, `HBA1C_GE_9` | Last HbA1c (LOINC 4548-4); flag uncontrolled diabetes (≥ 9%). HbA1c testing also from Px CPT 83036/83037 | PJ01 lab, PJ05 Px | 1.2 | NEW | P2 |
| P13 | `DIABETES_SEVERITY` markers | Insulin use (Rx or Z79.4), CGM / insulin pump (Rx basket devices, Z96.41, Z46.81), hypoglycaemia (E11.649, E11.641), microvascular complications (E11.3x retinopathy, E11.4x neuropathy) | PJ02 Dx, PJ03 Rx | 1.1, 2 (D11) | NEW | P2 |
| P14 | `CKD_COMPLICATION` markers | Anaemia in CKD (D63.1) or ESA / IV iron Rx; mineral-bone treatment (phosphate binders, calcitriol, paricalcitol, cinacalcet) | PJ02 Dx, PJ03 Rx | 1.1, 2 (D11) | NEW | P2 |
| P15 | `CV_COMORBIDITY` markers | PAD / atherosclerosis (I70.x, I73.9), resistant hypertension (I1A.0), cardiomyopathy (I42.x) | PJ02 Dx | 1.1 | NEW | P2 |

Why some of these matter for Kerendia specifically (to be confirmed with Medical):
* **HF type (P4):** the HF indication covers LVEF ≥ 40%. Claims cannot see LVEF, so diastolic HF (I50.3x) is the closest proxy for the labelled HF population; systolic HF (I50.2x) is mostly LVEF < 40%.
* **Potassium (P11):** per the US label, Kerendia should not be started when serum potassium is > 5.0 mmol/L, so a high K+ is a direct barrier to initiation.
* **eGFR (P10):** per the US label, initiation is not recommended below eGFR 25; a fast decliner is a patient where the HCP may act sooner.
* **Testing (P9):** guidelines recommend at least annual UACR and eGFR in T2D. An HCP who rarely tests UACR cannot identify most Kerendia patients, which is an education signal on its own.

### 6.2 HCP layer: candidate features

All counts are **distinct patients** of the HCP in the trailing window (recommendation X8), with 0 instead of null when the HCP has no such patients (X5). Default windows: 6 and 12 months.

#### Panel and stage
| # | Feature | Definition | Built from | Origin | Priority |
| --- | --- | --- | --- | --- | --- |
| H1 | `TOTAL_PATIENTS_T2D_CKD` | Patients with `T2D_CKD_LABEL_FLAG` = 1 | P3 | PJ7 | P1 |
| H2 | `TOTAL_PATIENTS_CKD_STAGE_{1_2, 3A, 3B, 4, 5_ESRD, UNKNOWN}` | By corrected stage; 3a/3b from N18.31/N18.32 or eGFR 45–59 / 30–44 | Section 1.1 stage, P7 | D2 | P1 |
| H3 | `TOTAL_PATIENTS_PROGRESSED_TO_STAGE_{3,4}` | Stage increase only, ignoring flicker and unknown ↔ known | Stage history | D3 | P1 |
| H4 | `TOTAL_PATIENTS_EGFR_FAST_DECLINE` | Patients with `EGFR_DECLINE_30PCT_24M` | P10 | NEW | P2 |
| H5 | `TOTAL_PATIENTS_HF`, `TOTAL_PATIENTS_HF_PRESERVED_PROXY`, `TOTAL_PATIENTS_T2D_CKD_AND_HF` | HF panel for the second indication; overlap with the CKD-T2D panel | P3, P4 | PJ7, extended | P1 |

#### Guideline pillars and white space
| # | Feature | Definition | Built from | Origin | Priority |
| --- | --- | --- | --- | --- | --- |
| H6 | `TOTAL_PATIENTS_STAGE_<s>_ON_<therapy>` | Stage {2, 3, 4, unknown} × therapy {SGLT2, GLP-1, steroidal MRA, ACE/ARB, Kerendia} | H2, P8 | C2 | P1 |
| H7 | `PCT_T2D_CKD_PATIENTS_ON_{SGLT2, GLP1, ACE_ARB}` | Pillar adoption rate per HCP | H1, P8 | C8 | P1 |
| H8 | `TOTAL_PATIENTS_T2D_CKD_ON_ACE_ARB_AND_SGLT2_NO_MRA` | Two pillars, no MRA: the most direct add-on candidates | H1, P8 | C7 | P1 |
| H9 | `TOTAL_PATIENTS_T2D_CKD_KERENDIA_READY` | `T2D_CKD_LABEL_FLAG` AND last eGFR ≥ 25 (or unknown) AND last K+ ≤ 5.0 (or unknown) AND on ACE/ARB AND NOT on Kerendia | P3, P8, P10, P11 | NEW (extends E4) | P1 |
| H10 | `TOTAL_PATIENTS_T2D_CKD_ON_STEROIDAL_MRA` | Spironolactone / eplerenone users in the label population: switch candidates | P3, P8 | C9 | P2 |
| H11 | `TOTAL_PATIENTS_HF_PRESERVED_PROXY_NOT_ON_KERENDIA` | HF white space for the second indication; split by `ON_SGLT2` | P4, P8 | NEW | P1 |
| H12 | `TOTAL_NEW_ELIGIBLE_PATIENTS` | Patients who first meet H1 criteria in the window | P3 | E4 | P1 |

#### Testing behaviour
| # | Feature | Definition | Built from | Origin | Priority |
| --- | --- | --- | --- | --- | --- |
| H13 | `PCT_T2D_PATIENTS_UACR_TESTED_12M`, `PCT_T2D_PATIENTS_EGFR_TESTED_12M` | Share of the HCP's T2D patients with a UACR / eGFR test in 12 months (Quest or Px) | P1, P9 | L1, extended | P1 |
| H14 | `TOTAL_PATIENTS_UACR_A2_A3` | Patients with last UACR ≥ 30 | PJ01 UACR stage | NEW | P2 |

#### Treatment dynamics
| # | Feature | Definition | Built from | Origin | Priority |
| --- | --- | --- | --- | --- | --- |
| H15 | Add-on starts among T2D+CKD | `TOTAL_PATIENTS_START_SGLT2_ON_ACE_ARB`, `TOTAL_PATIENTS_START_GLP1_ON_SGLT2`, `TOTAL_PATIENTS_START_STEROIDAL_MRA` (12-month washout) | P3, P8 | N3 | P1 |
| H16 | GLP-1 brand starts | `TOTAL_PATIENTS_START_SEMAGLUTIDE`, `_TIRZEPATIDE` | P8 | N4, A2 | P1 |
| H17 | SGLT2 rejection rate | Rejected / submitted SGLT2 claims (and Farxiga / Jardiance) in 6 / 12 months | Rx claims | A4 | P2 |
| H18 | 90-day supply share | Share of SGLT2 and ACE/ARB claims with 90-day supply | Rx claims | A5 | P2 |

#### Barriers and patient mix
| # | Feature | Definition | Built from | Origin | Priority |
| --- | --- | --- | --- | --- | --- |
| H19 | `TOTAL_PATIENTS_T2D_CKD_POTASSIUM_GT_5` | Label patients with last K+ > 5.0: initiation barrier | P3, P11 | NEW | P1 |
| H20 | `PCT_T2D_CKD_PATIENTS_ON_INSULIN`, `_WITH_CGM` | Diabetes severity mix of the label panel | P3, P13 | NEW | P2 |
| H21 | `PCT_T2D_CKD_PATIENTS_WITH_CKD_COMPLICATION` | Anaemia / mineral-bone treatment: sicker, often nephrology-managed panel | P3, P14 | NEW | P2 |
| H22 | `PCT_T2D_CKD_PATIENTS_CO_MANAGED_NEPHROLOGY` | Share of the HCP's label patients who also have a claim from a nephrologist in 12 months | P3 + provider specialty on Dx / Rx claims | NEW | P2 |
| H23 | `PCT_T2D_CKD_PATIENTS_AGE_65_PLUS` | Medicare-age share of the label panel (access and copay context) | P3 + demographics | NEW | P2 |

### 6.3 Design rules for all new features
* **No look-ahead:** every flag is evaluated as of the lookback end of the cohort month (E2). Lifetime flags joined to every month are not allowed.
* **Kerendia-derived features** (`ON_KERENDIA`, H6 with Kerendia, H9 "NOT on Kerendia", H11) must be checked against the target definition before use. If the target is Kerendia NBRx in the forecast window, current Kerendia use in the lookback is allowed; anything overlapping the target window is not.
* **Distinct patients over claim counts** for panel features (X8); claim counts only where the claim itself is the behaviour (rejection, days supply).
* **Coverage:** Quest covers about 43.5% of HCPs (recommendations L1). Lab-based features (P2, P10–P12, H4, H9, H14, H19) will be null-heavy until LabCorp (section 5) or Px fallbacks are added; keep "unknown" as its own category rather than treating it as normal.
* **Overlap:** check existing HCP notebooks (`09_claim_comorbidity`, `21_kerendia_claims`, `26/27/28_Features_NBRx/NRx/TRx`, `31_Competitor_drugs_NBRX_share`) before adding panel counts, to avoid re-creating duplicates.

### 6.4 Dependencies on earlier sections
| Feature group | Needs |
| --- | --- |
| Stage features (H2, H3, H6) | Section 1.1 approved (Dx stage by code) |
| Lab-value features (P2, P10–P12, H4, H9, H14, H19) | Section 1.2 (LOINC lists, K+ and HbA1c as separate tests) and, for coverage, section 5 |
| Therapy features (P8, H6–H11, H15, H16) | Section 2 approved (GLP-1, DPP-IV, ARNI, Kerendia classes) |
| HF features (P4, H5, H11) | HF codes from the Dx basket (not part of the CKD subset in 1.1, D1) |
| Dialysis / transplant (P5, P6) | Section 1.1 D4/D5 and the Px basket dialysis CPTs |

### 6.5 Decisions to confirm with the team
| # | Proposed decision | Alternative | How to change |
| --- | --- | --- | --- |
| D13 | **HF features use all HF codes, plus a separate diastolic (I50.3x) proxy** for the LVEF ≥ 40% indication | Only all-HF, or only diastolic | Drop `HF_TYPE` or restrict `HF_FLAG` |
| D14 | **Lab-based CKD definition (P2) uses two abnormal values ≥ 90 days apart** | Single abnormal value | Change the persistence rule in P2. A single value adds patients but also acute kidney injury noise |
| D15 | **"Kerendia-ready" (H9) uses eGFR ≥ 25 and K+ ≤ 5.0, with unknown values allowed** | Require known values | Change the unknown handling. Requiring known values would drop most patients today (lab coverage) |
| D16 | **Add hyperkalaemia Dx (E87.5) and potassium binders (Lokelma, Veltassa) to the basket.** They are not in the current Dx or Rx basket | Use lab K+ only | Add rows to `Kerendia_Dx_Final.csv` / `Kerendia_Rx_Final.csv`. Gives a K+ signal for HCPs without Quest coverage |
| D17 | **Kerendia-derived features kept, subject to the leakage check in 6.3** | Exclude all Kerendia-derived features | Remove `ON_KERENDIA` and the "NOT on Kerendia" filters |
| D18 | **Windows limited to 6 and 12 months** for new features | Also 1, 3 months and bounded RUNNING | Add windows in the HCP notebooks. Fewer windows keep the column count low (recommendations section 0.1) |

### Next steps
* Team review of 6.1–6.2 and D13–D18; pick the P1 set for the first 3.1 build.
* Confirm the Kerendia label points (HF LVEF ≥ 40%, K+ > 5.0, eGFR 25) with Medical.
* Confirm the target definition to settle the Kerendia leakage rule (D17).
* After sections 1.1, 1.2 and 2 are approved: estimate coverage for each P1 feature (share of HCPs with a non-zero value) and report it in this section before building.
