# NBA 3.1 – HCP Claims Features: Analysis of the NBA 3.0 Implementation

**Scope:** the six HCP-level claim notebooks (`01_claim_rx_monthly` … `06_claim_eligible_hcp`) and the six patient-journey notebooks they depend on, all under
`/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`.

**Companion files:**
* `NBA_3_1_HCP_Claims_Features_Recommendations.md` (what to change, add, or remove for 3.1).
* `NBA_3_1_HCP_Claims_Selected_Features_277.csv` (the 277 selected claim features, with source HCP notebook, feature family, window and patient-journey dependency).

**Structure reference:** `NBA_3_1_Patient_Features_Analysis.md` (patient-level features, Sehar). The patient-level features are a separate pipeline and are not covered here.

**Evidence used**
* Code read of all 12 notebooks plus `00_step23_function` and `99_Combine_Physician_Data`.
* Final model feature list with SHAP (752 features) and the combined feature list `kerendia_nba_3_hcp_complete_features_list_2026_09_25.csv` (25,048 features).
* EDA on the backup outputs in `.../hcp_level_model/ops_pipeline_bkp/` (`notebook_output/` and `query_output/`). Snapshot month for fill-rate and distribution checks: **SVC_DT_M = 2026-08-01**, joined to the inference HCP universe `kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` (**231,412 PROVIDER_IDs**). Correlation checks use a 20% random HCP sample (~46k HCPs).

---

## 0. Shared foundations

### 0.1 Pipeline position

```
Snowflake (IQVIA LAAD Rx/Dx/Px, Quest Lab)
   └─ 00_Write_Input_Files ─► query_output/ (Rx_01_new, Rx_05, Lab_03, Lab_04, Dx_03, pat_journey_dx, lab_query_output …)
         ├─ Patient_Journey_For_Claim_Eligible_HCP/01–06 ─► patient × month tables (Section 1)
         └─ 01–06 HCP claim notebooks ─► HCP × month feature tables (Sections 2–7)
                 └─ 99_Combine_Physician_Data ─► HCP × cohort modelling table (25,048 features)
                         └─ feature selection (Boruta + SHAP) ─► final 752 features
```

### 0.2 Common mechanics (all six notebooks)

| Item | Behaviour in 3.0 |
| --- | --- |
| Output grain | `PROVIDER_ID` × `SVC_DT_M` (NB01/NB04 aggregate on `NPI_NUMBER` and map to `PROVIDER_ID` in 99_Combine; NB03/NB05/NB06 are provider-level throughout) |
| Time unit | Calendar month (`date_trunc('MM', SVC_DT)`) |
| Fill missing months | `step2_fill_missing` (from `00_step23_function`) creates a dense HCP × month spine |
| Windows | `step3_lag_*` creates `_IN_LAST_{1,3,6,12}_MONTH` plus `RUNNING_` (cumulative from first month in data) |
| Ratios | `PCT_` = feature / matching denominator in the same window |
| Output window | 2022-01 to 2026-08 |
| Join into model | `99_Combine_Physician_Data` joins on `PROVIDER_ID` × `SVC_DT_M`, where `SVC_DT_M = trunc(LOOKBACK_END_DATE,'MM')` from the anchor-date CSV (example scoring row: anchor 2025-10-01, lookback end 2025-09-30) |

### 0.3 Feature funnel (claims notebooks only)

| Notebook | Produced cols | Final 752 | Modeling Selection (%) | SHAP share of model |
| --- | --- | --- | --- | --- |
| NB01 claim_rx_monthly | 5,411 | 172 | 3.2% | 17.5% |
| NB02 claim_lab_monthly | 116 | 0 | 0% | 0.0% |
| NB03 claim_diagnosis_monthly | 127 | 3 | 2.4% | 0.13% |
| NB04 claims_monthly | 3,691 | 89 | 2.4% | 5.1% |
| NB05 claim_rx_nps_monthly | 188 | 14 | 7.4% | 2.3% |
| NB06 claim_eligible_hcp | 84 | 1 | 1.2% | 0.04% |
| **Total (unique)** | **9,617** | **277** | **2.9%** | **25.1%** |

Notes:
* Modeling Selection (%) = features in the final 752 / columns produced by the notebook.
* The full list of the 277 selected features, with the HCP notebook (NB01–NB06) each comes from and the patient-journey notebooks (PJ01–PJ06) it depends on, is in `NBA_3_1_HCP_Claims_Selected_Features_277.csv` (same folder).
* 2 features (`TOTAL_RX_CLAIMS_IN_LAST_1_MONTH`, `TOTAL_RX_CLAIMS_IN_LAST_12_MONTH`) are produced identically by NB01 and NB04 (100% value match), so the per-notebook counts sum to 279 but the unique count is 277.
* The claims notebooks produce ~38% of the 25,048 combined columns but ~37% of final features and 25% of SHAP. The other 475 final features come from prior writing, F2F/promotion, HCP demographics, recency, Kerendia claims, NBRx/NRx/TRx, competitor shares, etc.
* Rank position: 3 of the top 25, 7 of the top 50 and 21 of the top 100 features come from these notebooks. Highest: `RUNNING_TOTAL_RX_CLAIMS_ACE_OR_ARB_COMMERCIAL` (rank 14), `TOTAL_RX_CLAIMS_PATIENT_WITH_1_ACTIVE_TREATMENT_IN_LAST_1_MONTH` (18), `TOTAL_PATIENTS_START_SGLT2_IN_LAST_6_MONTH` (19).

### 0.4 Window usage across all six notebooks

| Window | NB01 used | NB04 used | NB05 used | NB03/NB06 used | Observation |
| --- | --- | --- | --- | --- | --- |
| BASE (current month) | 0 / 492 | 0 / 336 | 0 / 18 | 0 | **Never selected.** In NB01–NB05 the base column is value-identical to `_IN_LAST_1_MONTH` (checked on 941 NB01 pairs, 671 NB04 pairs, 34 NB05 pairs, 21 NB02, 23 NB03: 100% equal) |
| PCT_BASE | 0 / 487 | 0 / 335 | 0 / 16 | 0 | Same duplication |
| IN_LAST_1 | 9 + 12 PCT | 9 + 4 PCT | 2 | 0 | |
| IN_LAST_3 | 11 + 9 PCT | 20 + 1 PCT | 4 + 2 PCT | 1 | |
| IN_LAST_6 | 16 + 18 PCT | 16 + 2 PCT | 1 | 1 | |
| IN_LAST_12 | 27 + 17 PCT | 19 + 1 PCT | 2 + 2 PCT | 1 | |
| RUNNING_ | 52 (6.1% SHAP) | 17 | 1 | 1 | Most valuable single window for NB01 |
| DIFF / RATIO | 0 / 12 and 1 / 12 | – | – | – | |

Window correlation (log1p, NB01 volume features): 3M vs 6M r = 0.92–0.99, 6M vs 12M r = 0.93–0.98, 1M vs 12M r = 0.64–0.92. `RUNNING_` vs `_IN_LAST_12_MONTH` has median r = 0.85 (range 0.52–0.92), so RUNNING carries information beyond 12M, but its value depends on how far back the data starts (2021) and grows monotonically with time.

### 0.5 Redundancy among the 277 selected claim features

Pairwise log1p correlation on the final selected feature table (20% HCP sample):
* 71 of 277 features have at least one partner at |r| ≥ 0.95; 125 at ≥ 0.90; 184 at ≥ 0.80.
* Representative exact or near-exact duplicates that both survived selection:
  * `..._SGLT2_...` vs `..._SGLT2_WO_INVOKANA_300MG_...` (r = 1.00; 6 such pairs in the 752).
  * `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_GFR_STAGE_4` vs `..._GFR_STAGE_4_AND_UACR_STAGE_UNKNOWN` (r = 0.999).
  * NB04 family C `..._DX_GFR_STAGE_UNKNOWN_WITH_<X>` vs `..._DX_UACR_STAGE_UNKNOWN_WITH_<X>` (r = 0.98–0.99).
  * `TOTAL_RX_CLAIMS_IN_LAST_12_MONTH` vs `TOTAL_RX_CLAIMS_PATIENT_WITH_NO_NEW_TREATMENT_IN_LAST_12_MONTH` (r = 0.998).
  * NB06 `RUNNING_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_4` vs NB04 `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_GFR_STAGE_4` (r = 0.978).

The dominant latent signal in these features is HCP prescribing volume, sliced many ways.

### 0.6 Product mapping (Rx_01_new, last 12 months to 2026-08)

| TREATMENT_CATEGORY | CATEGORY (brand) | Claims (12M) | Note |
| --- | --- | --- | --- |
| Calcium channel / Beta blocker | same | 210.7M | |
| ACE/ ARB | same | 124.7M | |
| Combo drug | same | 97.5M | |
| Diuretic_NON_MRA | same | 77.4M | |
| metformin | same | 71.8M | |
| Other- glucose mgmt | GLP-1 | 48.6M | GLP-1 sits under "Other glucose mgmt" at the class level |
| Insulin | same / GLP-1 | 44.4M / 53K | Insulin–GLP-1 combos coded as GLP-1 brand |
| Other- glucose mgmt | same | 29.3M | Sulfonylureas, TZDs, etc. |
| SGLT2 | JARDIANCE / FARXIGA / SGLT2 / INVOKANA 300 / INVOKANA 100 | 27.7M / 10.1M / 3.3M / 163K / 113K | "SGLT2" brand = combos (Synjardy, Xigduo, Glyxambi) + Steglatro |
| MRA | SPIRONOLACTONE-MRA / MRA | 17.3M / 0.86M | "MRA" brand ≈ eplerenone |
| Diuretic_NON_MRA | SPIRONOLACTONE-MRA | 377K | Spironolactone/HCTZ: class and brand disagree |
| Other- glucose mgmt | DPP-IV | 8.9M | |

Observations:
* **`Diuretic + MRA` never appears in the data** although it is hard-coded in the brand filter lists of NB01 and NB04, so all `..._DIURETIC_AND_MRA_...` columns are empty.
* **No finerenone/Kerendia, tirzepatide (Mounjaro) or sotagliflozin (Inpefa) claims are in Rx_01_new.** Kerendia is handled by `21_kerendia_claims` / prior-writing notebooks; tirzepatide is missing from the CKD product mapping altogether.
* INVOKANA 300MG is ~0.4% of SGLT2 claims, which is why every `SGLT2_WO_INVOKANA_300MG` feature correlates at r ≈ 1.0 with its `SGLT2` counterpart.

---

## 1. Patient journey (foundation for NB01, NB03, NB04, NB06)

Folder `Patient_Journey_For_Claim_Eligible_HCP/`. Builds patient × month state tables that HCP notebooks join to Rx/Dx claims on `PATIENT_ID` × `SVC_DT_M`.

### 1.1 Notebook summary

| # | Notebook | Input | Logic | Output (grain) |
| --- | --- | --- | --- | --- |
| 01 | patient_journey_labs | `kerendia_nba_3_0_lab_query_output` (Quest lab results from `STG_CAR_IQV_QUEST_TO_LAAD_HIST`, written by `00_Write_Input_Files` cell 61; GFR_STAGE, UACR_STAGE) | Forward-fill each test result to the month before the next test | `kerendia_nba_3_0_lab_journey_output` (patient × month: GFR_STAGE, UACR_STAGE) |
| 02 | patient_journey_dx | `pat_journey_dx` (LAAD Dx + DIM_DIAGNOSIS; DX_STAGE from description) | Patient × month CKD stage, forward filled; `DX_STAGE_UPDATED` | `df_dx_combine` (patient × month) |
| 03 | patient_journey_rx | LAAD Rx + product mapping, restricted to HCP universe | 7-day gap buffer, explode SVC_DT→END_DT daily, collapse to patient × month with arrays of TREATMENT_CATEGORY and CATEGORY | `df_rx_clean` (~3.3–3.5B rows) |
| 04 | patient_journey_t2d_flag | LAAD Dx (`%TYPE 2 DIABETES%`) ∪ LAAD Rx × diabetes product mapping | Patient-level union | `df_t2d_patient` (PATIENT_ID, DIABETIC_FLAG = 1) |
| 05 | patient_journey_px | LAAD Px × DIM_PROCEDURE (`%DIALYSIS%`) | First dialysis date | `df_px` (PATIENT_ID, FIRST_DIALYSIS_DATE, DIALYSIS_FLAG) |
| 06 | patient_journey_combine | Outputs of 01–05 | Full-outer join lab + dx + rx on patient × month; add T2D and dialysis flags; derive five tables | See 1.2 |

### GFR and UACR definitions

Two lab measures define a patient's CKD status. Both come from Quest lab results and are staged in `00_Write_Input_Files`.

* **GFR (estimated glomerular filtration rate, eGFR)** measures how well the kidneys filter blood, in mL/min/1.73m². It is calculated from serum creatinine. Lower values mean worse kidney function, and the G stage (CKD stage 1–5) is based on it.
* **UACR (urine albumin-to-creatinine ratio)** measures albumin leaking into the urine, in mg/g. It is a marker of kidney damage (albuminuria). Higher values mean more damage, and the A stage (A1–A3) is based on it.
* Kerendia's CKD-with-T2D population is described on both axes (reduced eGFR and/or raised albuminuria), so both measures are carried through the patient journey.

**GFR staging** (standard KDIGO GFR categories)

| GFR range (mL/min/1.73m²) | Stage Description | Stage | KDIGO meaning |
| --- | --- | --- | --- |
| 90 – 150 | CHRONIC KIDNEY DISEASE, STAGE 1 | 1 | G1: normal or high |
| 60 – 89 | CHRONIC KIDNEY DISEASE, STAGE 2 (MILD) | 2 | G2: mildly decreased |
| 30 – 59 | CHRONIC KIDNEY DISEASE, STAGE 3 (MODERATE) | 3 | G3a (45–59) and G3b (30–44), not split in the code |
| 15 – 29 | CHRONIC KIDNEY DISEASE, STAGE 4 (SEVERE) | 4 | G4: severely decreased |
| < 15 | CHRONIC KIDNEY DISEASE, STAGE 5 | 5 | G5: kidney failure |
| > 150 | Dropped (`IGNORE`) | 0 | Implausible value |

**UACR staging** (standard KDIGO albuminuria categories)

| UACR range (mg/g) | Stage Description | Stage | KDIGO meaning |
| --- | --- | --- | --- |
| < 30 | A1 | 1 | Normal to mildly increased |
| 30 – 299 | A2 | 2 | Moderately increased |
| ≥ 300 | A3 | 3 | Severely increased |

The same thresholds appear in two places:
* **Cell 17 (`Lab_03`)** writes the text labels shown above (NB02 turns them into column names such as `STAGE_2_MILD`). It is the input to NB02 and is marked `%skip`, so the current run reuses the previously written `Lab_03` table.
* **Cell 61 (`kerendia_nba_3_0_lab_query_output`)** writes numeric `GFR_STAGE` (1–5) and `UACR_STAGE` (1–3). It is the active input to `01_patient_journey_labs`. A GFR row has `UACR_STAGE` = null and a UACR row has `GFR_STAGE` = null.

**How a lab result becomes a stage (both cells)**
1. Source: `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_QUEST_TO_LAAD_HIST` (Quest results linked to LAAD patient IDs).
2. Test type from the test name: `GFR` if it contains GFR or GLOMERULAR; `UACR` if it contains ALB or RATIO; all other tests are dropped.
3. Units kept: `ML/MIN/1.73M2` for GFR; `MCG/MGCREAT`, `MG/GCREAT`, `MG/GCR`, `MG/G{CREAT}` for UACR.
4. Only plain numeric results are kept. Values containing `<`, `>` or `-` are excluded, so results reported as text such as ">60" or "<15" are dropped. This may under-count the highest and lowest GFR bands.
5. Ordering HCP primary specialty must be one of FM, FPG, GP, GPM, IFP, IM, IMG, IPM, NRP, PHA, and the NPI must not be null.
6. Several results for the same patient, HCP, date and test are reduced to their median, and the median is mapped to a stage with the thresholds above.
7. Cell 61 also keeps only results from 2021-11-30 onward, which is why lab history starts later than Rx/Dx (see 1.3).

**Dx-based CKD stage (input to `02_patient_journey_dx`)**

`pat_journey_dx` (cell 71) assigns `DX_STAGE` from the diagnosis description: "STAGE 1" = 1, "STAGE 2 (MILD)" = 2, "STAGE 3 (MODERATE)" = 3, "STAGE 4 (SEVERE)" = 4, any "STAGE 5" = 5, everything else = 0 (CKD, stage not specified). The ICD code list in that query includes N18.1, N18.2, N18.3, N18.4 and N18.9 but not N18.30, N18.31, N18.32, N18.5 or N18.6. This is the cause of the near-empty Dx stage 3 and missing stage 5 described in 1.3.

**Dx codes per Dx CKD stage**

The cell 71 code list has 163 codes. Applying the description rule above to their standard ICD-9 / ICD-10 descriptions gives:

| Stage Description | Stage | Dx codes | Codes |
| --- | --- | --- | --- |
| CHRONIC KIDNEY DISEASE, STAGE 1 | 1 | 1 | N18.1 |
| CHRONIC KIDNEY DISEASE, STAGE 2 (MILD) | 2 | 1 | N18.2 |
| CHRONIC KIDNEY DISEASE, STAGE 3 (MODERATE) | 3 | 1 | N18.3 (retired Oct-2020; replaced by N18.30 / N18.31 / N18.32, which are not in the list) |
| CHRONIC KIDNEY DISEASE, STAGE 4 (SEVERE) | 4 | 1 | N18.4 |
| Any "STAGE 5" | 5 | 0 | None (N18.5, N18.6, I12.0, I13.11, I13.2 are not in the list) |
| Everything else (stage not specified) | 0 | 159 | See breakdown below |
| **Total** | | **163** | |

Breakdown of the 159 stage-0 codes:

| Group | Dx codes | Codes |
| --- | --- | --- |
| CKD, stage unspecified | 4 | N18, N18.9, 585, 585.9 |
| ICD-9 CKD stage I–IV (Roman numerals, so the "STAGE 1" text rule does not match) | 4 | 585.1, 585.2, 585.3, 585.4 |
| Diabetes with kidney complications | 22 | 249.4x, 250.4x, E08.2x, E09.2x, E11.2x, E13.2x |
| Hypertensive CKD / heart and CKD | 23 | 403.x, 404.x, I12, I12.9, I13, I13.0, I13.1, I13.10 |
| Anemia in CKD | 2 | D63.1, 285.21 |
| Other renal | 2 | 588.81, N25.81 |
| Transplant / dialysis status | 3 | Z94.0, V42.0, Z99.2 |
| Not valid diagnosis codes (procedure-style or unrelated values, e.g. 0TY0.0Z0, 5A1.D00Z, 909.xx, G03.xx, 800–889) | 99 | Most of these are probably dropped by the join to `STG_IQVIA_LAAD_DIM_DIAGNOSIS` |

Only 4 of the 163 codes can produce a known Dx stage, and none can produce stage 5. These counts come from the code list and standard ICD descriptions, not from the data. They should be checked against the descriptions in `STG_IQVIA_LAAD_DIM_DIAGNOSIS` (for example, whether IQVIA spells ICD-9 stages as "STAGE I" or "STAGE 1").

**Treatment categories (`TREATMENT_CATEGORY` and `CATEGORY`)**

Rx claims are kept only if the product is in `PHCDW.PHCDW_DSAA.CKD_PRODUCT_MAPPING_VW`, and the mapping's `Treatment_Category` must not be "other" (`00_Write_Input_Files`, Rx_01 cell 6). Each claim then gets two labels:
* `TREATMENT_CATEGORY`: the drug class.
* `CATEGORY`: a brand or sub-class label. It is set by product-name rules for SGLT2 brands, spironolactone, DPP-IV and GLP-1, and otherwise equals `TREATMENT_CATEGORY`.

`03_patient_journey_rx` carries both as monthly arrays per patient, and they drive the class/brand features in NB01, NB04 and NB05.

`TREATMENT_CATEGORY` values (9 in the data):

| TREATMENT_CATEGORY | Meaning | Examples | Claims (12M to 2026-08) |
| --- | --- | --- | --- |
| ACE/ ARB | Renin-angiotensin system blockers: ACE inhibitors and angiotensin receptor blockers. Standard CKD / hypertension backbone on top of which Kerendia is added | Lisinopril, ramipril, losartan, valsartan | 124.7M |
| Calcium channel / Beta blocker | Blood-pressure and heart-rate drugs: calcium channel blockers and beta blockers | Amlodipine, diltiazem, metoprolol, carvedilol | 210.7M |
| Combo drug | Fixed-dose blood-pressure combinations (ARB + diuretic, ACE + diuretic, ACE + CCB, ARB + CCB, BB + diuretic, ARB + BB + diuretic) | Losartan/HCTZ, amlodipine/benazepril | 97.5M |
| Diuretic_NON_MRA | Diuretics other than MRAs (thiazide and loop diuretics) | HCTZ, chlorthalidone, furosemide | 77.8M |
| MRA | Steroidal mineralocorticoid receptor antagonists, the class closest to Kerendia (a non-steroidal MRA, which is not in this table) | Spironolactone, eplerenone | 18.2M |
| SGLT2 | SGLT2 inhibitors, kidney-protective glucose-lowering drugs, recommended alongside RAS blockers in CKD with T2D | Empagliflozin, dapagliflozin, canagliflozin, ertugliflozin | 41.4M |
| metformin | First-line T2D therapy | Metformin | 71.8M |
| Insulin | Insulins | Insulin glargine, lispro | 44.5M |
| Other- glucose mgmt | All other glucose-lowering drugs, including GLP-1 and DPP-IV | Sulfonylureas, TZDs, semaglutide, sitagliptin | 86.8M |

`CATEGORY` values (brand or sub-class):

| CATEGORY | Parent TREATMENT_CATEGORY | Meaning / assignment rule | Claims (12M to 2026-08) |
| --- | --- | --- | --- |
| JARDIANCE | SGLT2 | Empagliflozin; product name contains JARDIANCE | 27.7M |
| FARXIGA | SGLT2 | Dapagliflozin; product name contains FARXIGA | 10.1M |
| INVOKANA 300MG | SGLT2 | Canagliflozin 300 mg; name contains INVOKANA and strength = 300 MG | 163K |
| INVOKANA 100MG | SGLT2 | Canagliflozin 100 mg; name contains INVOKANA and strength = 100 MG | 113K |
| SGLT2 | SGLT2 | All other SGLT2 products: combinations (e.g. Synjardy, Xigduo, Glyxambi) and Steglatro | 3.3M |
| SPIRONOLACTONE-MRA | MRA (377K under Diuretic_NON_MRA) | Any product whose name contains SPIRONOLACTONE. Spironolactone/HCTZ combinations keep class Diuretic_NON_MRA, so brand and class disagree | 17.3M + 377K |
| MRA | MRA | Other MRAs, mainly eplerenone | 0.86M |
| GLP-1 | Other- glucose mgmt (53K under Insulin) | Named GLP-1 RA list: semaglutide (Ozempic, Rybelsus), dulaglutide (Trulicity), liraglutide (Victoza), exenatide (Byetta, Bydureon), lixisenatide (Adlyxin), albiglutide (Tanzeum), and insulin degludec/liraglutide (Xultophy, class Insulin). Tirzepatide (Mounjaro) is not in the list | 48.6M + 53K |
| DPP-IV | Other- glucose mgmt | Named DPP-4 inhibitor list: sitagliptin (Januvia, Janumet), linagliptin (Tradjenta, Jentadueto), saxagliptin (Onglyza, Kombiglyze), alogliptin (Nesina, Kazano, Oseni) | 8.9M |
| Same as TREATMENT_CATEGORY | ACE/ ARB, Calcium channel / Beta blocker, Combo drug, Diuretic_NON_MRA, metformin, Insulin, Other- glucose mgmt | No brand rule applies; the class label is reused | See class table |
| Diuretic + MRA | n/a | Hard-coded in the NB01 / NB04 brand lists but never present in the data | 0 |

Notes:
* "Other- glucose mgmt" at class level mixes GLP-1, DPP-IV and older agents. The GLP-1 and DPP-IV signal is only visible at `CATEGORY` level.
* Claim volumes are taken from the Rx_01_new EDA in section 0.6. Class totals are the sums of all brand rows under each class (for example, Diuretic_NON_MRA includes the 377K spironolactone/HCTZ claims and Insulin includes the 53K GLP-1 combination claims).
* No finerenone (Kerendia), tirzepatide or sotagliflozin claims appear in Rx_01_new (see 0.6).

### 1.2 Tables produced by 06_patient_journey_combine

| Table | Columns | Consumer |
| --- | --- | --- |
| `pat_new_and_total_treatments` | TOTAL_TREATMENTS (size of category array), TOTAL_NEW_TREATMENTS (vs prior month) | NB01 patient-treatment buckets |
| `pat_new_ckd_stage` | NEW_CKD_STAGE (only when stage changed vs prior month) | NB03 new-to-stage features |
| `pat_gfr_dx_stage_and_treatment_category` | GFR_DX_STAGE, GFR_UACR_DX_STAGE, UACR_STAGE, CATEGORY (array), BRAND (array) | NB04 family A |
| `pat_uacr_stage_and_treatment_category_new` | Same, **exploded** to one row per CATEGORY × BRAND | NB04 family C |
| `kerendia_nba_3_0_pat_sglt2_filter_m` | ELIGIBLE_PATIENT_FLAG, GFR_UACR_DX_STAGE, GFR_DX_STAGE, UACR_STAGE | NB06 |

### 1.3 EDA findings

**Coverage and dates (current backup)**

| Table | Rows | Date range |
| --- | --- | --- |
| `pat_journey_dx` | 401.3M (15.7M patients) | 2021-01-02 to 2026-08-28 |
| `df_dx_combine` | 1.07B | 2021-01 to 2026-08 |
| `kerendia_nba_3_0_lab_query_output` | 225.2M | **2021-11-30** to 2026-08-31 |
| `df_rx_clean` | ~3.3B+ | 2021-01 to 2026-08 |
| `df_t2d_patient` | 76.7M | patient-level |
| `df_px` | 1.47M | patient-level |

* Lab history starts 10 months after Rx/Dx (Nov-2021), so lab-derived stage is left-censored for early 2022 cohorts.

**Stage availability at 2026-08 (patient × month)**

| Field | Distribution |
| --- | --- |
| `GFR_DX_STAGE` (pat_gfr table, 71.6M rows) | null 72.1%, 0 = 13.5%, 1 = 3.3%, 2 = 6.8%, **3 = 0.9%**, 4 = 3.3%, 5 = 0.02% |
| `UACR_STAGE` | null 98.5%, A1 = 1.2%, A2 = 0.27%, A3 = 0.07% |
| `NEW_CKD_STAGE` | null 94.5%; transitions: 1 = 1.37M, 2 = 1.63M, 3 = 0.55M, 4 = 58K, 5 = 14K, 0 = 310K |
| `TOTAL_TREATMENTS` | 0 = 15.5%, 1 = 41.6%, 2–3 = 36.0%, >3 = 6.8%; any new treatment = 6.7% |
| `pat_sglt2_filter_m` | ELIGIBLE_PATIENT_FLAG = 1 for 68.7M patient-months, of which **89% have GFR_UACR_DX_STAGE = STAGE_UNKNOWN** |

**Dx CKD stage mapping gap (affects NB03, NB04, NB06).** `DX_STAGE` is parsed from the diagnosis description. In `pat_journey_dx` since 2025-01:
* `CHRONIC KIDNEY DISEASE, STAGE 4 (SEVERE)`: 7.26M rows → stage 4
* `CHRONIC KIDNEY DISEASE, STAGE 2 (MILD)`: 4.28M → stage 2
* `CHRONIC KIDNEY DISEASE, STAGE 1`: 0.56M → stage 1
* `CHRONIC KIDNEY DISEASE, STAGE 3 (MODERATE)`: **only 4,632** → stage 3
* No stage 5 / ESRD descriptions at all.
* The top Dx categories (dialysis dependence 31.7M, anemia in CKD 22.9M, T2D with diabetic CKD 18.3M, hypertensive CKD 16.3M, CKD unspecified 6.1M) all map to stage 0.

Stage 3 is clinically the most common CKD stage, so this is a mapping defect, not a population fact. The cause is confirmed in the `pat_journey_dx` query (see 1.1.1): ICD-10 N18.3 was split into N18.30/N18.31/N18.32 (stage 3 unspecified / 3a / 3b), and these codes are not in the Dx code list (only legacy N18.3 is). N18.5/N18.6 (stage 5 / ESRD) are also not in the list. Result: Dx-based stage 3 and stage 5 are almost empty and most CKD patients are "unknown" stage.

**Other quirks**
* 01_labs: `na.fill({"LAST_TEST_DATE": end_date_limit})` silently does nothing on a date column, so the last test of each patient is not forward-filled to the end date (fixed in the 3.1 validation version).
* 03_rx: daily explode of every claim (3.3–3.5B rows) is the most expensive step in the journey; output only needs patient × month.
* `pat_uacr_stage_and_treatment_category_new` averages **3.98 rows per patient-month** (Aug-2026) because it explodes CATEGORY × BRAND; this drives the double counting in NB04 family C.
* All tables are calendar-month aligned. 3.1 cohorts with offset anchor dates (e.g. day-7 anchors) will not line up with these tables without re-bucketing.
* **Eligibility rule bug (06_combine).** `STAGE_ELIGIBLE` is set to -1 for unknown stage, but the final rule tests `GFR_UACR_DX_STAGE == -1` (the raw stage, which is null or 0, never -1) instead of `STAGE_ELIGIBLE == -1`. The "unknown stage and no SGLT2 → not eligible" branch therefore never fires, and every non-dialysis patient with unknown stage is eligible. This explains why 89% of eligible patient-months are STAGE_UNKNOWN.
* `SGLT2_FLAG` is a lifetime patient flag (any SGLT2 month anywhere in the spine), joined to every month, so it would introduce look-ahead once the bug above is fixed. `DIABETIC_FLAG` is joined but not used in the eligibility rule.
* Dialysis flag uses "first dialysis before 2017-01-01 or ≤ DATE"; a patient never recovers from the flag (reasonable, but transplant patients are not handled).

---

## 2. NB01 – `01_claim_rx_monthly`

**Sources:** `Rx_01_new` (31 GB, ~4.03B rows, 2021-01-02..2026-08-28; NPI, patient, product, days supply, rejection, payer, birth year, gender, refill flag); `pat_new_and_total_treatments`.

**Features built (5,411 columns)**

| Family | Definition | Produced | Final 752 | SHAP |
| --- | --- | --- | --- | --- |
| Category/brand volume | Claims by the 9 treatment classes and 8 brands listed below | 194 | 14 | 1.27% |
| Age | Class/brand × 10-year patient age bin | 1,991 | 39 | 3.15% |
| Payer | Class/brand × METHOD_OF_PAYMENT (the 7 payer types listed below) | 1,122 | 35 | 4.28% |
| Duration | Class/brand × DAYS_SUPPLY bin (30/60/90/other/unknown) | 880 | 27 | 3.26% |
| Gender | Class/brand × F/M/U | 561 | 18 | 1.80% |
| Refill | Brand × new Rx / refill | 176 | 11 | 1.07% |
| Rejected | Rejected claims by class/brand | 176 | 4 | 0.40% |
| Patient treatment | Claims for patients with 0/1/2–3/>3 active and 0/1+ new treatments | 88 | 6 | 0.96% |
| SGLT2_WO_INVOKANA_300MG | SGLT2 minus Invokana 300 across volume/age/gender/duration/rejected | 187 | 17 | 1.28% |
| AVG / patient count | AVG_PATIENT_AGE, TOTAL_PATIENT_COUNT, AVG_TREATMENT_PER_PATIENT, TOTAL_TREATMENT_COUNT | 24 | 0 | 0% |
| DIFF / RATIO | 3-vs-prior-3 month change and ratio (total-level; brand-level DIFF/RATIO columns are counted in their brand family) | 12 | 1 | 0.05% |

By window type in the 172 used: 63 plain windows, 56 PCT, 52 RUNNING, 1 RATIO.

**Classes, brands and payer types used in the NB01 features**

The column token is the value as it appears in feature names (for example `RUNNING_TOTAL_RX_CLAIMS_ACE_OR_ARB_COMMERCIAL`). NB01 builds it from the raw value by replacing `/` with `OR`, `+` with `AND`, and `-` and spaces with `_`, then upper-casing. Claim figures are the last 12 months to 2026-08 from Rx_01_new (see 0.6 and 1.1).

| Group | Raw value | Column token | Definition | Claims (12M) / share |
| --- | --- | --- | --- | --- |
| Treatment class (`TREATMENT_CATEGORY`) | ACE/ ARB | `ACE_OR_ARB` | ACE inhibitors and angiotensin receptor blockers (RAS blockers), the CKD / hypertension backbone | 124.7M |
| Treatment class | Calcium channel / Beta blocker | `CALCIUM_CHANNEL_OR_BETA_BLOCKER` | Calcium channel blockers and beta blockers | 210.7M |
| Treatment class | Combo drug | `COMBO_DRUG` | Fixed-dose blood-pressure combinations (ARB / ACE / BB with a diuretic or CCB) | 97.5M |
| Treatment class | Diuretic_NON_MRA | `DIURETIC_NON_MRA` | Thiazide and loop diuretics (not MRAs) | 77.8M |
| Treatment class | MRA | `MRA` | Steroidal mineralocorticoid receptor antagonists (spironolactone, eplerenone) | 18.2M |
| Treatment class | SGLT2 | `SGLT2` | SGLT2 inhibitors (empagliflozin, dapagliflozin, canagliflozin, ertugliflozin and combinations) | 41.4M |
| Treatment class | metformin | `METFORMIN` | Metformin, first-line T2D therapy | 71.8M |
| Treatment class | Insulin | `INSULIN` | Insulins | 44.5M |
| Treatment class | Other- glucose mgmt | `OTHER_GLUCOSE_MGMT` | All other glucose-lowering drugs (sulfonylureas, TZDs, GLP-1, DPP-IV) | 86.8M |
| Brand (`CATEGORY`) | JARDIANCE | `JARDIANCE` | Empagliflozin (product name contains JARDIANCE) | 27.7M |
| Brand | FARXIGA | `FARXIGA` | Dapagliflozin (product name contains FARXIGA) | 10.1M |
| Brand | INVOKANA 100MG | `INVOKANA_100MG` | Canagliflozin 100 mg | 113K |
| Brand | INVOKANA 300MG | `INVOKANA_300MG` | Canagliflozin 300 mg | 163K |
| Brand | SPIRONOLACTONE-MRA | `SPIRONOLACTONE_MRA` | Any product containing spironolactone, including spironolactone/HCTZ | 17.7M |
| Brand | GLP-1 | `GLP_1` | GLP-1 receptor agonists from a fixed product list (semaglutide, dulaglutide, liraglutide, exenatide, lixisenatide, albiglutide, Xultophy); tirzepatide not included | 48.7M |
| Brand | DPP-IV | `DPP_IV` | DPP-4 inhibitors from a fixed product list (sitagliptin, linagliptin, saxagliptin, alogliptin) | 8.9M |
| Brand | Diuretic + MRA | `DIURETIC_AND_MRA` | Hard-coded in the brand filter but never present in the data, so all its columns are empty | 0 |
| Payer (`METHOD_OF_PAYMENT`) | Commercial | `COMMERCIAL` | Private insurance (employer or individual plans) | 41.9% |
| Payer | Medicare Part D | `MEDICARE_PART_D` | Medicare prescription drug coverage (standalone Part D or Medicare Advantage drug plans) | 46.3% |
| Payer | Medicare | `MEDICARE` | Medicare paid outside Part D | 0.15% |
| Payer | Managed Medicaid | `MGD_MEDICAID` | Medicaid delivered through managed-care organisations | 5.5% |
| Payer | FFS Medicaid | `FFS_MEDICAID` | State fee-for-service Medicaid | 4.4% |
| Payer | Cash | `CASH` | Patient paid out of pocket; no insurer billed | 1.8% |
| Payer | Unknown | `METHOD_OF_PAYMENT_UNKNOWN` | Null METHOD_OF_PAYMENT, relabelled in NB01 | ≈ 0% |

Notes:
* Brand features only use the 8 brands above (`Category IN (...)` filter in NB01). The generic `SGLT2` and `MRA` CATEGORY values are not part of the brand set; they are covered only at class level.
* Brand claims cross classes: SPIRONOLACTONE-MRA includes 377K claims whose class is Diuretic_NON_MRA, and GLP-1 includes 53K claims whose class is Insulin.
* Payer figures are shares of all NB01 claims, not claim counts.

**Top NB01 features:** `RUNNING_TOTAL_RX_CLAIMS_ACE_OR_ARB_COMMERCIAL` (14), `TOTAL_RX_CLAIMS_PATIENT_WITH_1_ACTIVE_TREATMENT_IN_LAST_1_MONTH` (18), `RUNNING_TOTAL_RX_CLAIMS_METFORMIN_COMMERCIAL` (31), `RUNNING_TOTAL_RX_CLAIMS_GLP_1_30_DAYS_SUPPLY` (41), `TOTAL_RX_CLAIMS_CALCIUM_CHANNEL_OR_BETA_BLOCKER_90_DAYS_SUPPLY_IN_LAST_12_MONTH` (44), `PCT_TOTAL_RX_CLAIMS_NEW_PRESCRIPTION_IN_LAST_6_MONTH` (61).

**EDA findings**
* Coverage: 99.9% of the HCP universe has an NB01 row at 2026-08; 63 rows have null PROVIDER_ID.
* Sparse tails: 458 age columns, 222 duration, 161 gender, 110 payer columns are non-zero for < 1% of HCPs. Median non-zero rate: payer 33%, duration 36%, age 37%, gender 70%, volume 89%.
* Age distribution of claims (12M): 60–70 28.1%, 70–80 24.1%, 50–60 18.8%, 40–50 9.7%, > 80 6.8%, `IGNORE` (missing birth year) 7.0%, < 20 0.4%. The `AGE_GROUP_10_0` bin is an invalid label (0 claims) and `0_10` / `10_20` bins are clinically irrelevant for CKD/T2D.
* Gender: F 51.4%, M 48.6%, U 0.01%. `PCT_..._F` + `PCT_..._M` = 1.000 for every HCP, so the two PCT columns are perfect complements.
* Payer: Medicare Part D 46.3%, Commercial 41.9%, Managed Medicaid 5.5%, FFS Medicaid 4.4%, Cash 1.8%, Medicare (non-Part D) 0.15%. Payer × class features are the single highest-SHAP NB01 family; commercial share is the top claims-based signal.
* New Rx 47.2% vs refill 52.8%.
* DAYS_SUPPLY is effectively always populated (null share ≈ 0.0003%), so the `UNKNOWN_DAYS_SUPPLY` columns are empty.
* AVG / patient count family has high fill (median non-zero 98%) but 0 selections, because it duplicates volume.

**Quirks**
* BASE and `_IN_LAST_1_MONTH` duplicates (492 + 487 redundant columns).
* SGLT2 vs SGLT2_WO_INVOKANA_300MG is r ≈ 1.0 everywhere; 6 redundant pairs are both in the 752.
* `Diuretic + MRA` brand columns are always empty.
* Spironolactone/HCTZ counts as brand SPIRONOLACTONE-MRA but class Diuretic_NON_MRA, so brand and class totals do not reconcile.

---

## 3. NB02 – `02_claim_lab_monthly`

**Source:** `Lab_03` (Quest lab claims from 2021-07, filtered to ordering HCPs with specified lab specialties; no null NPIs).

**Features built (116 columns):** `TOTAL_LAB_CLAIMS`, by TEST_TYPE (GFR, UACR), by stage (GFR CKD 1–5 with text labels such as `STAGE_2_MILD`, UACR A1–A3), with 1/3/6/12/RUNNING windows and PCT.

**Final 752: 0 features.**

**EDA findings**
* Coverage: only 55.8% of the universe has a row; 43.5% of HCPs have any lab claim in the last 12 months.
* Mix: GFR 83.2% / UACR 16.8% of lab claims. UACR stages A1 12.7%, A2 3.2%, A3 0.9%. GFR stages: 1 = 41.6%, 2 = 30.9%, 3 = 9.5%, 4 = 1.0%, 5 = 0.3%.
* Median non-zero rate per column 16–37%.
* UACR testing is a guideline-relevant behaviour for Kerendia (albuminuria is part of the label) but is captured only for HCPs whose labs go through Quest and who are coded as the orderer.

**Quirks**
* Stage labels carry parentheses and severity words (`(MILD)`, `(MODERATE)`, `(SEVERE)`) that are stripped into column names.
* No patient-level de-duplication: repeat tests on the same patient count multiple times.

---

## 4. NB03 – `03_claim_diagnosis_monthly`

**Sources:** `Dx_03` (409M rows; DX_STAGE derived from description); `pat_new_ckd_stage`.

**Features built (127 columns):** `TOTAL_DX_CLAIMS`, by DX_STAGE (1–4 and UNSPECIFIED), by patient new-to-stage (1–5, NO_NEW_STAGE), windows and PCT. Provider-level only.

**Final 752: 3 features, 0.13% SHAP**
* `TOTAL_DX_CLAIMS_WITH_PATIENT_NO_NEW_STAGE_IN_LAST_12_MONTH` (rank 314)
* `TOTAL_DX_CLAIMS_WITH_PATIENT_NO_NEW_STAGE_IN_LAST_6_MONTH` (537)
* `TOTAL_DX_CLAIMS_STAGE_UNSPECIFIED_IN_LAST_3_MONTH` (661)

All three are effectively Dx-volume proxies.

**EDA findings**
* Coverage: 97.4% of universe.
* Stage mix of Dx claims (12M): unspecified 90.1%, stage 4 5.9%, stage 2 3.5%, stage 1 0.5%, **stage 3 0.0%** (see 1.3 mapping gap). No stage 5 column exists.
* Patient new-to-stage mix: no new stage 93.2%; new to 1/2/3/4/5 = 0.4/2.1/1.5/2.1/0.7%.
* The new-to-stage signal (a CKD progression event) is conceptually valuable but sparse and is computed on the defective stage mapping.

---

## 5. NB04 – `04_claims_monthly`

**Sources:** `Rx_01_new` (base claim spine); `Lab_04` (same-day lab); `pat_gfr_dx_stage_and_treatment_category` (family A); `pat_uacr_stage_and_treatment_category_new` (family C); `Dx_03` loaded but unused.

**Features built (3,691 columns)**

| Family | Definition | Produced | Final 752 | SHAP |
| --- | --- | --- | --- | --- |
| Total | `TOTAL_RX_CLAIMS` (identical to NB01) | 6 | 2 | 0.07% |
| A – patient stage | Rx claims split by the patient's GFR/Dx stage and GFR × UACR stage that month | 330 | 6 | 0.25% |
| B – same-day test | Rx claims × same-day lab GFR/UACR stage × class/brand | 1,705 | 0 | 0% |
| C – patient stage × patient therapy | Rx claims × patient GFR or UACR stage × patient's active class/brand that month | 1,650 | 81 | 4.80% |

**What family C actually measures.** The Rx side contributes only `NPI_NUMBER, PATIENT_ID, SVC_DT_M`; CATEGORY and BRAND come from the patient journey table. So `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_4_WITH_SGLT2` = all claims (any drug) the HCP wrote that month for patients who were in GFR stage 4 **and on an SGLT2 that month (from any prescriber)**, multiplied by fan-out. It is a "patient-panel therapy mix × stage" signal, not "SGLT2 claims by stage".

**EDA findings**
* Coverage: 99.9% of universe.
* **Family C double counting is large.** Summing family C class-level columns across GFR stages gives a median **8.1×** the HCP's total Rx claims (p10 5.9×, p90 11.2×). Versus the NB01 claim count of the same class: SGLT2 14.8×, ACE/ARB 6.9×, GLP-1 8.4×, Farxiga 16.3×. Cause: each claim joins to every CATEGORY × BRAND row of the patient-month (avg 3.98 rows).
* Stage composition (family A, 12M): GFR stage unknown 90.8% of claims, stage 1 1.8%, 2 4.4%, 3 0.8%, 4 2.2%, 5 0.02%. In family C, UNKNOWN-stage columns carry 84–90% of the volume.
* The 81 selected family C features: 52 on the GFR axis, 29 on UACR; 31 are `STAGE_UNKNOWN` columns (≈ 2.95% SHAP of the 4.8%). The UNKNOWN columns behave as "claims for patients on drug X" (r = 0.85–0.92 with NB01 class volume).
* The known-stage C columns that survived are mostly GFR stage 4 and stage 2 (e.g. `RUNNING_..._DX_GFR_STAGE_4_WITH_SGLT2` rank 166) — the stages that the Dx mapping populates.
* Family B: median non-zero rate 0.04%; 1,199 of 1,705 columns are non-zero for < 1% of HCPs. Same-day Rx–lab match is rare because pharmacy fill date rarely equals lab draw date.

**Quirks**
* `Dx_03` loaded but unused; `recency_window = 90` defined but unused.
* Family B uses a left join: claims without a same-day lab land in `GFR_STAGE_UNSPECIFIED` and `UACR_STAGE_UNSPECIFIED`; multiple labs on one day duplicate the claim.
* `TOTAL_RX_CLAIMS` duplicates NB01.
* Family A GFR_STAGE_X vs GFR_STAGE_X_AND_UACR_STAGE_UNKNOWN are r ≈ 0.999 because UACR is null for 98.5% of patient-months.

---

## 6. NB05 – `05_claim_rx_nps_monthly`

**Source:** `kerendia_nba_3_0_Rx_05` (27 GB, 4.03B rows, from 2019-11-01; PROVIDER_ID level).

**Definition:** New Patient Start (NPS) = a claim on the patient's first-ever date for that class/brand across all HCPs; credited to the writing HCP.

**Features built (188 columns):** `TOTAL_PATIENTS_VISIT`, `TOTAL_PATIENTS_START_<class|brand>` (9 classes + 7 brands), `TOTAL_NEW_PATIENT_START`, windows, PCT over `TOTAL_PATIENTS_VISIT`.

**Final 752: 14 features, 2.3% SHAP**

| Group | Used | SHAP |
| --- | --- | --- |
| Class starts | 8 | 1.74% |
| Any new start | 2 | 0.40% |
| Brand starts | 4 | 0.20% |
| Visits | 0 | 0% |

Top: `TOTAL_PATIENTS_START_SGLT2_IN_LAST_6_MONTH` (rank 19, 0.69% SHAP — third-highest-ranked feature across the six claims notebooks), `TOTAL_NEW_PATIENT_START_IN_LAST_1_MONTH` (62), `PCT_TOTAL_PATIENTS_START_ACE_OR_ARB_IN_LAST_3_MONTH` (76).

**EDA findings**
* Highest Modeling Selection (%) of the six notebooks (7.4%) — "initiation" behaviour is less collinear with raw volume than the NB01 slices.
* Left censoring: starts spike in the first months of LAAD history because patients with existing therapy look "new".
* 1,014,149 filled months have null instead of 0 for visit/start counts; `TOTAL_NEW_PATIENT_START` is null (not 0) for HCPs without starts.
* `Diuretic + MRA` never appears as a start.
* 34 of 16,195 checked starts were shared by two HCPs on the same first date (both credited).

---

## 7. NB06 – `06_claim_eligible_hcp`

**Sources:** `Rx_01_new` (NPI × patient × month); `pat_sglt2_filter_m`; `df_px`.

**Logic:** join Rx claims to `pat_sglt2_filter_m` where `ELIGIBLE_PATIENT_FLAG = 1`; count distinct eligible patients per HCP-month, pivoted by GFR/Dx stage (2, 3, 4, UNKNOWN) and UACR stage (2, 3, UNKNOWN); add `DIALYSIS_FLAG`; windows via `step3_lag_avg` (average, not sum).

**Features built (84 columns). Final 752: 1 feature** — `RUNNING_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_4` (rank 491, 0.04% SHAP). 15 features were in the Boruta set.

**EDA findings**
* Root cause of the weak definition: the eligibility rule bug described in 1.3 (unknown-stage patients are always eligible).
* Eligible-patient composition (12M): GFR stage UNKNOWN 93.3%, stage 2 4.1%, stage 4 1.8%, stage 3 0.7%; UACR UNKNOWN 99.7%.
* `TOTAL_ELIGIBLE_PATIENTS_IN_LAST_12_MONTH` correlates r = 0.976 with total Rx claims — "eligible" is effectively "all active patients".
* `DIALYSIS_FLAG` = 1 for 43% of HCPs (any dialysis patient ever), so it carries little discrimination.
* Unlike NB01–NB05, NB06 `_IN_LAST_1_MONTH` is not equal to the base month (5–100% agreement by column), consistent with `step3_lag_avg` producing averages over a lagged window — the window semantics differ from the other notebooks.
* The one selected feature is a near-duplicate (r = 0.978) of NB04 `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_GFR_STAGE_4`.

---

## 8. Summary table

| Notebook | Core concept | Final 752 | SHAP | Primary issue | Signal assessment |
| --- | --- | --- | --- | --- | --- |
| Patient journey | Patient × month stage / therapy state | (indirect) | – | Dx stage 3/5 mapping gap; 72% null stage; CATEGORY × BRAND explode | Foundation is valuable but stage is mostly unknown |
| NB01 | Rx volume by class/brand × age/payer/duration/gender/refill | 172 | 17.5% | 5,411 cols, 97% unused; heavy redundancy | Strong; payer and duration slices carry most value |
| NB02 | HCP lab ordering | 0 | 0% | 44% HCP coverage; Quest-only | Weak in current form |
| NB03 | Dx volume by CKD stage | 3 | 0.13% | Stage mapping; volume proxy | Weak |
| NB04 | Rx × patient stage × patient therapy | 89 | 5.1% | Family C 8× double count; family B empty | Moderate; mostly "patients on drug X" proxy |
| NB05 | New patient starts | 14 | 2.3% | Left censoring; null vs 0 | Strong per column (highest Modeling Selection %) |
| NB06 | Eligible (CKD 2–4, non-dialysis) patients | 1 | 0.04% | Eligibility rule bug → ≈ everyone eligible; avg-lag | Weak in current form |

---

## 9. Caveats

* Fill-rate and distribution checks are a single snapshot month (2026-08). Training cohorts span 2022–2025; rates may differ for earlier months (especially lab, which starts Nov-2021).
* Correlation checks use a 20% random HCP sample and log1p transform.
* SHAP shares come from the final 752-feature model; features dropped earlier (Boruta / correlation filter) may still carry signal that was absorbed by a correlated survivor. Low SHAP share therefore means "not uniquely informative given the other features", not "no signal".
* The Dx stage 3/5 root cause (N18.30/N18.31/N18.32, N18.5 and N18.6 missing from the code list) was checked against the `pat_journey_dx` query in `00_Write_Input_Files` (cell 71).
* EDA was run on the backup (`ops_pipeline_bkp`) outputs, not on the 3.1 validation tables.
