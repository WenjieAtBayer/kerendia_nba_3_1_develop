# HCP-level claims features in NBA 3.1: Readiness Plan

**For:** Wenjie. **Reviewed by:** Raman. **Version:** 2026-11-16.  
**Run assessed:** `full_2026_11_13` (job 1010893614518587, run 338478597334222). Earlier run: `full_2026_11_11` (run 441950237921).

The plan tells the story in order: where to find things (section 1), a summary (2), what NBA 3.0 built (3), what changed on the way to 3.1 and why (4), including the changes of 2026-11-13 (4.6), what 3.1 delivers notebook by notebook (5), what is no longer built (6), what this means for the model (7), the run (8), the open points (9), and the storage in Unity Catalog tables (10; built and validated 2026-11-16).

Every number has a source in brackets, for example [S3]. The sources are listed in section 1. Numbers marked "my check" were counted on those tables for this plan (2026-11-12, updated 2026-11-14). Sections 3 and 4.1–4.5 compare 3.0 with the run `full_2026_11_11`; section 4.6 shows what the changes of 2026-11-13 moved; sections 5–9 describe the run `full_2026_11_13`.

---

## 1. Where to find things

Volume root: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/`. Workspace root: `/Workspace/Users/wenjie.chen@bayer.com/`.

| Ref | What | Path |
| --- | --- | --- |
| S1 | 3.0 HCP feature tables (NB01–NB06) | `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/`: `claim_rx_monthly`, `claim_lab_monthly_ZS`, `provider_claim_diagnosis_monthly`, `final_claims_monthly`, `kerendia_nba_3_0_claim_rx_nps_monthly`, `kerendia_nba_3_0_claim_eligible_patient` |
| S2 | 3.1 HCP feature tables (NB01–NB06) | `kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/full_2026_11_13/hcp_claims/` (sections 5–8; the same folder under `full_2026_11_11` for section 4): `claim_rx_monthly_cohort`, `claim_lab_monthly_cohort`, `provider_claim_diagnosis_monthly_cohort`, `claims_monthly_cohort`, `claim_rx_nps_monthly_cohort`, `claim_eligible_patient_cohort` |
| S3 | 3.0 inputs and patient tables | `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/`: `Rx_01_new` (Rx), `Lab_03` (NB02 lab), `Lab_04` (NB04 lab), `Dx_03`, `kerendia_nba_3_0_Rx_05`, `pat_new_and_total_treatments`, `pat_new_ckd_stage`, `pat_gfr_dx_stage_and_treatment_category`, `pat_uacr_stage_and_treatment_category_new`, `df_px` (dialysis), `df_t2d_patient` (diabetes); eligibility: `.../notebook_output/kerendia_nba_3_0_pat_sglt2_filter_m` |
| S4 | 3.1 inputs | `kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/query_output/full_2026_11_11/` and `.../full_2026_11_13/`: `rx_hcp_pull`, `lab_step4_pull`, `dx_step4_pull`; new in `full_2026_11_13`: `rx_nps_pull` (NB05 input) |
| S5 | 3.1 patient tables | `kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/full_2026_11_11/patient_journey/` (and the same folder under `full_2026_11_13`): `kerendia_nba_3_1_<table>_validation` (for example `..._pat_gfr_dx_stage_validation`, `..._pat_sglt2_filter_m_validation`) |
| S6 | 3.1 product baskets (used by the run) | `kerendia_nba_3_1_volume/final_product_mapping/Kerendia_{Rx,Dx,Lab,Px}_Final_Product_Mapping_2026_11_06.csv`, `Kerendia_Dx_Flag_Additions_2026_11_06.csv`; Rx from `full_2026_11_13` on: `Kerendia_Rx_Final_Product_Mapping_2026_11_13.csv` (written by `Final Product Basket/00_product_mapping_update_2026_11_13`) |
| S7 | The 752 model features of 3.0 | `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/input_files/Kerendia_NBA_3_feature_list_752_features.csv` |
| S8 | The 277 claims features among the 752, with notebook, family and window | `kerendia_nba_3_1_develop_pg/NBA 3.1 - Dev/Feature Analysis/NBA_3_1_HCP_Claims_Selected_Features_277.csv` |
| S9 | 3.0 code | `kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/00_Write_Input_Files.py` (input queries) and `.../00_Helper_Notebooks/00_step23_function.py` (look-back and running totals) |
| S10 | Patient-journey plan and combine notebook | `.../03_HCP_level_features/Patient_Journey_Validation/Alignment_Markdowns/Strategy and Execution/AI_Readiness_Plan.md`; `.../Patient_Journey_Validation/Combine Files/06_patient_journey_combine_3_1` |
| S11 | Per-notebook plans | `hcp_level_features/02 Lab Claims Files/NBA_3_1_Lab_Claims_Features_Plan.md`, `03 Diagnosis Claims Files/NBA_3_1_Dx_Claims_Features_Client_Summary.md`, `04 Monthly Cohort Claims Files/NBA_3_1_Claims_Features_Plan.md` |
| S12 | Decision log (X1–X20) | `hcp_level_features/Alignment_Markdowns/Strategy_and_Execution/NBA_3_1_HCP_Features_Decisions.md` |
| S13 | HCP universe | `NBA 3.1 - Dev/01_HCP_Universe/NBA_3.1_HCP_Universe_Presentation_V6_ZS_Recommended.md` |
| S14 | Runs | Job 1010893614518587 "NBA 3.1 Patient Journey + HCP Features": run 338478597334222 (`full_2026_11_13`), run 441950237921 (`full_2026_11_11`), validation run 128972234721576 (`validation_2026_11_13`) |
| S15 | Settings (brand list, start date, GLP-1 rule) | `03_HCP_level_features/00_cohort_config` |
| S16 | Unity Catalog schema for 3.1 (planned storage, section 10) | `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_nba_3_1` |

---

## 2. Summary

| Topic | 3.0 | 3.1 | Source |
| --- | --- | --- | --- |
| Time design | One row per HCP and calendar month | One row per HCP and cohort (28 monthly cohorts, May 2024 to August 2026) | S1, S2 |
| HCPs with Rx claims since 2023 | 234,170 | 294,612 (220,892 in both) | S3, S4, my check |
| Products | No Kerendia; no Mounjaro, Zepbound, Wegovy or generic dapagliflozin | All of them counted | S6 |
| Lab and diagnosis inputs | Separate 3.0 queries that missed many tests and the stage 3 and 5 codes | The 3.1 patient journey | S9, S11 |
| New signals | – | Potassium, HbA1c, diabetes type, heart-failure type, CKD stage 5, Kerendia | S2 |
| Features in NB01–NB06 | 9,617 | 8,463 | S1, S2 |

Of the 9,617 3.0 features, 7,788 are kept and 1,829 are not built any more: 1,704 were exact repeats of another column, 15 NB06 columns hold the same values as the 3.1 "last 1 month" columns (decisions X8, X9), and 110 "other glucose mgmt" stage columns are still not built (decision X5, section 6). The 4 NB01 columns for the month alone that were not exact repeats (`AVG_PATIENT_AGE`, `AVG_TREATMENT_PER_PATIENT`, `TOTAL_PATIENT_COUNT`, `TOTAL_TREATMENT_COUNT`) are built and are among the 7,788 kept. 675 features are new.

The 3.0 model uses 277 of these features [S8]; 270 exist in 3.1. Their values per HCP change: 141 stay within ±20%, 93 are lower and 36 are higher (section 7). The main causes are the 73,720 added HCPs, who write fewer prescriptions each, the later start of the running totals, and the new CKD stage rules. The model is retrained, and feature selection runs again on all 3.1 features [S12, X5].

**Changes of 2026-11-13 (section 4.6):** DPP-IV is back in the patient journey, GLP-1 claims are no longer counted twice in NB04, NB05 reads a 3.1 input that includes Kerendia and the new GLP-1 drugs, and NB01 again has the 4 averages and counts for the month alone.

**Decision X5 (final 2026-11-16, section 6):** NB04 builds the DPP-IV stage columns (90 columns, 2 model features; their 20 plain monthly copies are exact repeats and not built), not the "other glucose mgmt" stage columns (110 columns, 7 model features). The 7 have little weight in the 3.0 model, most of their signal is in the GLP-1 stage features, and building them would need the other glucose drugs in the shared patient journey. Feature selection runs again on 3.1. The run of record is `full_2026_11_13`.

**Status:** the full run `full_2026_11_13` succeeded for all 13 tasks and all 28 cohorts in 5 h 31 min [S14]. Section 9 lists 16 open points; 1, 5 and 12 are resolved. One correction to earlier versions of this plan: the SGLT2 rule of the Kerendia eligibility is **not** applied in 3.1 either (open point 6). The eligible share drops for other reasons (section 4.5).

---

## 3. Where we started: NBA 3.0

### 3.1 How 3.0 built the features

| Aspect | 3.0 | Source |
| --- | --- | --- |
| Row | One row per HCP and calendar month; the output starts in 2022-01 | S1, S9 (`SVC_DT_M >= '2022-01-01'` at the end of NB01–NB06) |
| Look-back windows | Last 1, 3, 6 and 12 months | S9 (`00_step23_function`) |
| Running totals | All claims since the first row of the input: 2021-01 for Rx and diagnosis, 2021-07 for lab | S9; input start dates: S3, my check |
| HCPs with Rx claims (2023-01 to 2026-09) | 234,170 | S3 `Rx_01_new`, my check |
| Treatment categories | From the Snowflake view `PHCDW.PHCDW_DSAA.CKD_PRODUCT_MAPPING_VW` | S9 |
| Brands with own features | Invokana 100 mg, Invokana 300 mg, Farxiga, Jardiance, Spironolactone-MRA, Diuretic + MRA, DPP-IV, GLP-1 | S9, S15 |
| Lab and diagnosis claims | Own 3.0 queries (`Lab_03`, `Lab_04`, `Dx_03`), separate from the 3.0 patient journey | S9 |

### 3.2 The six notebooks and their features

| Notebook | What it measured per HCP | 3.0 features | Example features | Source |
| --- | --- | ---: | --- | --- |
| NB01 Rx claims | Prescriptions by treatment category and brand, rejected claims, days supply, refill, payer, patient age and gender, patient treatments | 5,411 | `TOTAL_RX_CLAIMS_SGLT2_IN_LAST_3_MONTH`, `PCT_TOTAL_RX_CLAIMS_ACE_OR_ARB_AGE_GROUP_20_30_IN_LAST_6_MONTH`, `RATIO_RX_CLAIMS_ACE_OR_ARB_IN_PRIOR_3_LAST_3_MONTH` | S1 |
| NB02 Lab claims | eGFR and UACR tests by stage | 116 | `TOTAL_LAB_CLAIMS_GFR_IN_LAST_3_MONTH`, `TOTAL_LAB_CLAIMS_A2_IN_LAST_3_MONTH`, `TOTAL_LAB_CLAIMS_CHRONIC_KIDNEY_DISEASE_STAGE_1_IN_LAST_3_MONTH` | S1 |
| NB03 Diagnosis claims | CKD diagnosis claims by stage, and claims of patients who moved to a new stage | 127 | `TOTAL_DX_CLAIMS_STAGE_UNSPECIFIED_IN_LAST_3_MONTH`, `TOTAL_DX_CLAIMS_WITH_PATIENT_NO_NEW_STAGE_IN_LAST_6_MONTH` | S1 |
| NB04 Combined claims | Prescriptions split by the patient's kidney stage that month, a same-day lab test, and stage × treatment | 3,691 | `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_GFR_STAGE_4_AND_UACR_STAGE_UNKNOWN`, `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_1_WITH_GLP_1_IN_LAST_6_MONTH` | S1 |
| NB05 New patient starts | Patients who started a drug class or brand with the HCP | 188 | `TOTAL_PATIENTS_START_SGLT2_IN_LAST_6_MONTH`, `RUNNING_TOTAL_PATIENTS_START_SGLT2` | S1 |
| NB06 Eligible patients | Kerendia-eligible patients by stage; dialysis | 84 | `TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_3_IN_LAST_3_MONTH`, `RUNNING_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_4`, `DIALYSIS_FLAG` | S1 |
| **Total** | | **9,617** | | |

Counts are feature columns without ID and date columns.

### 3.3 What the 3.0 model uses

The model uses 752 features [S7]. 277 come from these six notebooks [S8]; the other 475 come from other sources (promotion, HCP profile, Kerendia sales and others).

| Notebook | Model features | Example model features [S8] |
| --- | ---: | --- |
| NB01 Rx claims | 172 | `PCT_TOTAL_RX_CLAIMS_ACE_OR_ARB_AGE_GROUP_10_20_IN_LAST_12_MONTH`, `RUNNING_TOTAL_RX_CLAIMS_ACE_OR_ARB_MGD_MEDICAID`, `PCT_TOTAL_RX_CLAIMS_MEDICARE_IN_LAST_12_MONTH` |
| NB02 Lab claims | 0 | – |
| NB03 Diagnosis claims | 3 | `TOTAL_DX_CLAIMS_STAGE_UNSPECIFIED_IN_LAST_3_MONTH`, `TOTAL_DX_CLAIMS_WITH_PATIENT_NO_NEW_STAGE_IN_LAST_12_MONTH` |
| NB04 Combined claims | 89 | `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_1_WITH_GLP_1_IN_LAST_12_MONTH`, `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_4_WITH_OTHER_GLUCOSE_MGMT` |
| NB05 New patient starts | 14 | `RUNNING_TOTAL_PATIENTS_START_SGLT2`, `TOTAL_PATIENTS_START_DIURETIC_NON_MRA_IN_LAST_3_MONTH` |
| NB06 Eligible patients | 1 | `RUNNING_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_4` |

2 features are in both NB01 and NB04 (total Rx claims), so the rows add up to 279 for 277 features. By window: running totals 71, 12 months 68, 6 months 54, 3 months 48, 1 month 35, ratio 1 [S8].

### 3.4 What 3.0 was missing

| Gap | Size | Why it happened | Source |
| --- | --- | --- | --- |
| Kerendia not counted | 0 claims in the 3.0 Rx input; 3.9M in 3.1 (2023-01 to 2026-09) | Kerendia was not in the 3.0 product rules | S3, S4, my check |
| Newer GLP-1 drugs and generic dapagliflozin not counted | Mounjaro 124.1M, Zepbound 29.0M, Wegovy 25.8M, generic dapagliflozin 16.2M claims in 3.1 | Not in the Snowflake view (basket notes) | S4, S6 |
| Few UACR tests in NB04 | `Lab_04`: 12,247 UACR tests from 9.8K patients since 2023; the 3.1 pull: 32.9M tests from 16.1M patients | The `Lab_04` query removes the spaces from the unit and then compares it with a list that writes the UACR unit with a space (`'MG/G {CREAT}'`), so those tests never match. `Lab_03` reads the raw unit column and finds 16.6M UACR tests | S9 ("File Lab_04"), S3, S4, my check |
| About half of the lab tests missing in NB02 | `Lab_03`: 108.8M tests from 122.9K HCPs since 2023; 3.1: 207.5M from 199.9K | `Lab_03` is an older, separate query: older provider table for the specialty filter, raw test names and units. 3.1 finds tests by LOINC code from the lab basket (201.1M of the 207.5M) | S11 (NB02 plan, F1), S4, my check |
| Stage 3 sub-codes and stage 5 missed in NB03 | Stage 3: 12.6K claims in 3.0 vs 65.4M in 3.1; stage 5: 0 vs 115.9M (2023-01 to 2026-09) | 3.0 read the stage from the diagnosis text, which does not match codes such as N18.30–N18.32 or N18.5 / N18.6 | S3 `Dx_03`, S4 `dx_step4_pull`, my check; S11 (NB03 summary) |
| Only a type 2 diabetes flag; no heart failure | – | Not built in 3.0. Kerendia's indications are CKD with type 2 diabetes, and heart failure with LVEF of 40% or more | S10 |
| No potassium or HbA1c signal | – | Not built in 3.0. The Kerendia label advises against starting above 5.0 mmol/L potassium | S10 |

---

## 4. What changed from 3.0 to 3.1, and why

### 4.1 Time design

| Aspect | 3.0 | 3.1 | Why | Source |
| --- | --- | --- | --- | --- |
| Row | HCP × calendar month | HCP × cohort: 28 cohorts c1–c28 (May 2024 to August 2026), each ending on the last day of its month | The 3.1 model is trained, validated and back-tested on these cohorts | S2, cohort file `cohorts/claims/cohorts.parquet` |
| Look-back windows | 1, 3, 6, 12 months | Same | – | S2 |
| Running totals | From 2021-01 (Rx, diagnosis) or 2021-07 (lab) | From 2023-01-01 | 3.1 data start in the settings; open point 10 | S15 |
| Plain monthly columns | Built next to "last 1 month" with the same value | Not built, except the 4 NB01 averages and counts for the month alone (added 2026-11-13) | Exact repeats (section 6) | S1, S2 |

### 4.2 HCP universe

| | 3.0 | 3.1 | Source |
| --- | ---: | ---: | --- |
| HCPs with Rx claims, 2023-01 to 2026-09 | 234,170 | 294,612 | S3 `Rx_01_new`, S4 `rx_hcp_pull`, my check |
| HCPs in both | 220,892 | 220,892 | same |
| HCPs only in this version | 13,278 | 73,720 | same |
| Rx claims per HCP, 2023-01 to 2026-09 | HCPs in both: 13,434 (3.1) / HCPs only in 3.0: 4,523 | HCPs only in 3.1: 4,135 | same |

Why the universe changed: 3.1 uses a new HCP universe that is 26% larger and keeps 94.4% of the 3.0 universe (220,017 of 232,965) [S13]. The added HCPs write about a third of the prescriptions of an HCP in both versions, so per-HCP averages go down (section 7).

### 4.3 Products

**Where the product rules come from**

| Area | 3.0 | 3.1 | Source |
| --- | --- | --- | --- |
| Rx | Snowflake view for the category, brand rules in the 3.0 query | Rx basket: 367 products, 245 active in the patient journey; from 2026-11-13: 372 products, 266 active | S9, S6, my check |
| Diagnosis, lab, procedures | Code lists in the 3.0 queries | Dx, lab and Px baskets, plus a list of 38 type 2 diabetes, 68 type 1 diabetes and 10 heart-failure codes | S9, S6 |

**What is different in the 3.1 baskets [S6]**

| Change | Products | Why |
| --- | --- | --- |
| GLP-1 drugs counted | Already in 3.0: Ozempic, Trulicity, Rybelsus, Victoza, Bydureon BCise, Byetta. New: Mounjaro, Zepbound, Wegovy, Wegovy HD, liraglutide, Saxenda, exenatide | The new ones are not in the Snowflake view; 3.1 adds them (basket update of 2026-11-05) |
| Generic dapagliflozin counted as SGLT2 | Dapagliflozin, dapagliflozin / metformin | Not in the view; a generic of Farxiga |
| Kerendia its own category and brand | Kerendia | The target drug; kept out of MRA so the competitor MRA counts are not inflated |
| New dialysis code | J0606 (etelcalcetide, given only to hemodialysis patients) | Finds more dialysis patients |
| DPP-IV and other glucose drugs **off** in the patient journey | For example Januvia, Tradjenta, glipizide, pioglitazone (`ACTIVE_JOURNEY = N`, note "Not in the 3.0 journey") | The basket was built on the product list of the 3.0 patient journey. This causes decision X5 (section 6) |
| DPP-IV switched **on** (basket of 2026-11-13) | 21 DPP-IV products: 16 switched to `ACTIVE_JOURNEY = Y` (for example Januvia, Tradjenta, Janumet), 5 added (Onglyza, Kombiglyze XR, Nesina, Kazano, Oseni); category and brand DPP-IV. The other glucose drugs (for example glipizide, pioglitazone) stay off | Brings back the DPP-IV patient tracking of 3.0 (section 4.6) |

**New products in the 3.1 Rx input** (claims since 2023-01-01) [S4, S6]

| Product | Claims (3.1) | Counted under |
| --- | ---: | --- |
| Mounjaro | 124.1M | Brand GLP-1, category "Other glucose mgmt" |
| Zepbound | 29.0M | Same |
| Wegovy, Wegovy HD | 25.8M | Same |
| Liraglutide, Saxenda, exenatide | 2.6M | Same |
| Generic dapagliflozin, dapagliflozin / metformin | 16.2M | Category SGLT2, no brand (Farxiga stays the brand) |
| Kerendia | 3.9M | Own category and brand: new columns |

**Why most new drugs add no columns.** NB01 builds one set of columns per treatment category and per brand on the brand list (the same 8 brands as 3.0 [S15]). A new drug that joins an existing category or brand fills the existing columns: their values rise, no columns are added. Only Kerendia is a new category and brand, so only Kerendia adds columns (234 in NB01, 180 in NB04 [S2]).

**Is the GLP-1 setup the same as in 3.0?** Yes. In 3.0 the Snowflake view put the GLP-1 drugs in the category "Other glucose mgmt", and GLP-1 was a brand. The 3.1 basket gives the GLP-1 drugs the category "GLP-1". Because GLP-1 is also on the brand list, NB01 would have created the same column names twice (for example `TOTAL_RX_CLAIMS_GLP_1_IN_LAST_3_MONTH` as category and as brand). Decision "option C" (2026-11-05) maps the GLP-1 category back to "Other glucose mgmt" in NB01 and NB04, so the structure is the same as in 3.0 [S15, S12]. The patient journey keeps "GLP-1" as a category. Since 2026-11-13 the same rule covers DPP-IV (`HCP_RX_CATEGORY_MAP` in S15), and NB04 counts GLP-1 and DPP-IV only through the brand, as 3.0 did (section 4.6).

**Treatment categories, 3.0 vs 3.1** (Rx claims 2023-01 to 2026-09; "Same HCPs" = the 220,892 HCPs in both versions) [S3, S4, my check]

| Category | 3.0 | 3.1 | Change | Same HCPs: 3.0 → 3.1 | Added HCPs (3.1 only) | Why it changed |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| ACE/ARB | 472.1M | 510.6M | +8% | 462.0M → 462.1M | 48.5M | Added HCPs only |
| Calcium channel / beta blocker | 765.7M | 854.3M | +12% | 748.8M → 748.9M | 105.3M | Added HCPs only |
| Combo drug | 338.5M | 364.8M | +8% | 331.0M → 331.1M | 33.8M | Added HCPs only |
| Diuretic (non-MRA) | 293.8M | 320.0M | +9% | 286.7M → 286.8M | 33.2M | Added HCPs only |
| Insulin | 167.3M | 173.5M | +4% | 164.2M → 164.2M | 9.2M | Added HCPs only |
| Metformin | 267.4M | 281.3M | +5% | 261.4M → 261.5M | 19.8M | Added HCPs only |
| MRA | 59.5M | 67.1M | +13% | 58.3M → 58.3M | 8.8M | Added HCPs only |
| SGLT2 | 143.3M | 165.2M | +15% | 141.3M → 156.7M | 8.5M | Generic dapagliflozin (+15.4M for the same HCPs) and added HCPs |
| Other glucose mgmt (incl. GLP-1, as NB01 counts it) | 337.4M | 531.7M | +58% | 331.3M → 494.0M | 37.7M | New GLP-1 drugs, and added HCPs |
| Kerendia | 0 | 3.9M | new | 0 → 3.9M | 0.0M | New product |

For the same HCPs, every unchanged category has the same claims in both versions. The growth there comes only from the added HCPs. The 3.0 totals also hold the claims of the 13,278 HCPs that are not in 3.1 (for example 8.8M ACE/ARB claims) and claims without an NPI (for example 1.3M ACE/ARB claims); 3.1 has no claims without an NPI.

**Brands, 3.0 vs 3.1** (same period and sources; columns = all NB01 columns named after the brand: look-back, running total, ratio and 3–6-month difference [S1, S2, my check])

| Brand | 3.0 | 3.1 | Change | Same HCPs: 3.0 → 3.1 | Why it changed | NB01 columns 3.0 → 3.1 |
| --- | ---: | ---: | ---: | --- | --- | --- |
| Jardiance | 87.9M | 91.7M | +4% | 86.6M → 86.6M | Added HCPs | 263 → 263 |
| Farxiga | 40.6M | 42.2M | +4% | 40.1M → 40.1M | Added HCPs | 254 → 254 |
| Invokana 100 mg | 0.81M | 0.85M | +5% | 0.79M → 0.79M | Added HCPs | 261 → 261 |
| Invokana 300 mg | 1.09M | 1.13M | +4% | 1.07M → 1.07M | Added HCPs | 252 → 252, plus 153 → 155 "SGLT2 without Invokana 300 mg" columns |
| SGLT2 without brand | 12.9M | 29.4M | +128% | 12.8M → 28.1M | Generic dapagliflozin | – |
| GLP-1 | 186.4M | 376.0M | +102% | 183.6M → 346.4M | Mounjaro, Zepbound, Wegovy and others | 261 → 261 |
| DPP-IV | 39.4M | 40.6M | +3% | 38.5M → 38.5M | Added HCPs | 252 → 252 |
| Other glucose mgmt without brand | 111.8M | 115.4M | +3% | 109.4M → 109.4M | Added HCPs | – |
| Spironolactone-MRA | 58.4M | 65.8M | +13% | 57.2M → 57.2M | Added HCPs | 254 → 254 |
| Kerendia | 0 | 3.9M | new | 0 → 3.9M | New product | 0 → 234 |

In the run `full_2026_11_13` the DPP-IV brand has 43.3M claims (same HCPs: 38.5M → 41.1M, +7% against 3.0), because the 2026-11-13 basket also counts 2.7M claims of generic gliptins (for example sitagliptin phosphate 1.1M, saxagliptin 0.8M); "Other glucose mgmt" as NB01 counts it is 534.6M (same HCPs 496.8M). The other categories and brands differ from the table by at most 0.14M claims (GLP-1: 375.67M → 375.80M), from late claims for August and September 2026 [S4, my check].

The changes above 100% (GLP-1, SGLT2 without brand) are real: they are the new drugs, not errors. The "SGLT2 without Invokana 300 mg" family has 2 more columns because two of its running totals now have claims. "Diuretic + MRA" is on the brand list but has no claims since 2023, so it has no columns in either version.

### 4.4 Lab and diagnosis inputs

| Input | 3.0 | 3.1 | Why it changed | Source |
| --- | --- | --- | --- | --- |
| NB02 lab tests (eGFR, UACR) | `Lab_03`: 108.8M tests (GFR 92.2M, UACR 16.6M), 122.9K HCPs | 207.5M tests (GFR 174.6M, UACR 32.9M), 199.9K HCPs | 3.1 uses the patient-journey lab data, found by LOINC code; `Lab_03` was an older query. Tests in both get the same stage (June 2025: 100% of UACR, 99.98% of eGFR) | S3, S4, S11 (NB02 plan), my check |
| NB04 lab tests | `Lab_04`: GFR 90.2M, UACR 12,247 | Same pull as NB02 | The unit mismatch in `Lab_04` (section 3.4) | S3, S9, my check |
| NB03 diagnosis claims | Stage from the description text | Stage from the code; stage 3: 12.6K → 65.4M, stage 5: 0 → 115.9M | The code lists catch the sub-codes and stage 5 | S3, S4, my check |
| Potassium (new) | – | 61.6M tests, 23.7M patients, 163.0K HCPs; 4.5M tests above 5.0 mmol/L (2.8M patients) | New signal; only the 10 primary-care specialties of the lab pull | S4, my check |
| HbA1c (new) | – | 38.4M tests, 16.6M patients, 144.8K HCPs; 1.7M tests of 9% or higher (0.94M patients) | New signal | S4, my check |

All counts are from 2023-01-01 to 2026-09-30; patient and HCP counts are exact distinct counts.

### 4.5 The patient journey

The HCP notebooks read patient tables to know each patient's CKD stage, treatments, diabetes, heart failure, dialysis and Kerendia eligibility. The patient-journey notebooks PJ01–PJ06 build them [S10].

**What changed in each patient-journey notebook [S10]**

| Notebook | What it builds | What changed in 3.1 | Why |
| --- | --- | --- | --- |
| PJ01 Labs | Each patient's eGFR / UACR tests and stage | Tests found by LOINC code from the lab basket; results such as ">90" kept; new table with potassium and HbA1c values and flags (potassium above 5.0, HbA1c 9% or higher) | Catch tests the 3.0 name and unit rules missed; new signals |
| PJ02 Diagnosis | Each patient's CKD stage from diagnosis codes | Stage from the code (stage 3 sub-codes, stage 5); one stage per month instead of a list; a missing stage stays empty instead of 0; months start at the patient's first CKD diagnosis | In 3.0 a stage of 0 hid the lab stage of the same month; stage 5 patients were not recognised |
| PJ03 Rx | Each patient's treatments per month; the HCP Rx inputs | New Rx basket (section 4.3): GLP-1 its own category, Kerendia added, generic dapagliflozin as SGLT2; DPP-IV on since 2026-11-13, other glucose drugs off. Since 2026-11-13 it also writes the NB05 input `rx_nps_pull` (history from 2021) | Count the new drugs; NB05 on the 3.1 basket |
| PJ04 Diabetes / heart failure | Diabetes and heart-failure flags per patient | 3.0: one type 2 diabetes flag. 3.1: diabetes type (type 2, type 1, other, none) and heart-failure type (preserved-EF proxy, reduced-EF proxy, mixed, unknown); the 3.0 flag is kept as `T2D_FLAG_30` | Kerendia's two indications |
| PJ05 Procedures | Dialysis patients and first dialysis date | New codes incl. J0606; a column that was always 1 is dropped | Find more dialysis patients |
| PJ06 Combine | Eligibility per patient and month; the tables the HCP notebooks read | Heart-failure flag and diabetes type added. Eligibility rule unchanged: stage 2–4 or unknown, not on dialysis. The SGLT2 rule is still not applied (it compares the stage with -1, copied from 3.0) | Open decisions C1 and C9 (open point 6) |

**What the patient tables look like now, and the effect on the HCP features** (rows 3.0 → 3.1) [S3, S5, my check]

| Patient table | Read by | Rows 3.0 → 3.1 | Why the rows changed | Effect on the HCP features |
| --- | --- | --- | --- | --- |
| New and total treatments | NB01 | 4.50B → 4.12B | 3.0 covers 70 months (2021-01 to 2026-10), 3.1 45 months (2023-01 to 2026-09). For the same months (2023-01 to 2026-08), 3.1 has more rows: 4.01B vs 3.01B | Patient-treatment features, for example `TOTAL_RX_CLAIMS_PATIENT_WITH_NO_NEW_TREATMENT_IN_LAST_3_MONTH`, `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_2_OR_3_ACTIVE_TREATMENTS` [S8]; model features in this family change by 0.94 per HCP (median, section 7) |
| New CKD stage | NB03 | 4.50B → 4.12B | Same months as above | "Patients new to a stage" features rise 1.32× per HCP, because stage 3 and 5 are now recognised |
| Stage × treatment (GFR / diagnosis) | NB04 | 4.50B → 4.12B | Same months as above | Claims move between stages (table below): stage 4 down, stage 1–3 up. The other glucose columns are gone (X5); the DPP-IV columns are back since 2026-11-13 |
| Stage × treatment (UACR) | NB04 | 18.76B → 14.45B | Same months; one row per patient, month, treatment and brand | Same as above for the UACR stage |
| Eligibility | NB06, NB02 | 4.50B → 4.12B; eligible 4.38B (97%) → 3.17B (77%) | Same months. The eligible share falls because many more patient-months are stage 1 or 5, which are not eligible (table below) | Eligible-patient features are lower; the model's NB06 feature falls to 0.43 per HCP. Source of the 148 new diabetes and heart-failure features |
| Dialysis | NB06 | 1.49M → 1.54M patients | New dialysis codes incl. J0606 | `DIALYSIS_FLAG`; fewer eligible patients |
| Diabetes / heart failure | NB06 | 77.2M → 89.1M patients | 3.1 also lists patients with heart failure (23.8M) or type 1 diabetes, not only type 2 | New `..._DM_TYPE_...` and `..._HF_TYPE_...` features |
| Lab flags | NB02 | new | New | New potassium and HbA1c features |

The number of patient rows per month is higher in 3.1 (August 2026: 113.2M vs 72.2M). We have not yet split this by source (more lab patients, new drugs, months from the first diagnosis on); open point 14.

**CKD stage of the patient-months in August 2026** (`GFR_UACR_DX_STAGE`) [S3 `pat_gfr_dx_stage_and_treatment_category`, S5 `..._pat_gfr_dx_stage_validation`, my check]

| Stage | 3.0 | 3.1 | Eligible? | Why it changed |
| --- | ---: | ---: | --- | --- |
| 0 | 9.84M | 0 | Yes (as unknown) | 3.1 leaves a missing stage empty instead of 0 [S10, N1] |
| 1 | 2.45M | 32.48M | No | In 3.0 the Dx value 0 hid the lab stage (only about 18% of 3.0 lab months carried a lab stage into the combine [S10, B1]); 3.1 shows it |
| 2 | 4.93M | 24.24M | Yes | Same reason |
| 3 | 0.68M | 11.78M | Yes | Same reason, plus the stage 3 sub-codes |
| 4 | 2.38M | 1.24M | Yes | Patients now at a more precise stage (3 or 5) |
| 5 | 0.02M | 1.42M | No | Stage 5 codes now read |
| Unknown | 51.87M | 42.08M | Yes, unless on dialysis | The rest |

This is why the eligible share falls from 97% to 77%: the stage 1 and stage 5 months (33.9M in August 2026) are not eligible. The SGLT2 rule plays no part.

### 4.6 Changes of 2026-11-13 and what they moved

Run `full_2026_11_13` compared with `full_2026_11_11` [S2, S4, S5, my check]. Before the full run, all changes were tested on the test HCPs (validation run, all 13 tasks passed [S14]).

| Change | Where | What it does | Effect in the run |
| --- | --- | --- | --- |
| DPP-IV on in the patient journey | Rx basket 2026-11-13 [S6] | 21 DPP-IV products tracked per patient (section 4.3) | 1,289,659 patients with DPP-IV in the August 2026 patient table (3.0: 0.98M patient-months); 90 NB04 DPP-IV stage columns are back, with 2 of the 9 missing model features |
| DPP-IV in `HCP_RX_CATEGORY_MAP` | Settings [S15] | DPP-IV counts under "Other glucose mgmt" as category and under DPP-IV as brand, like GLP-1 | No column name is created twice |
| GLP-1 counted once in NB04 | NB04 | The stage × treatment features counted a GLP-1 claim through the category and through the brand, both into `..._WITH_GLP_1`; now only through the brand, as 3.0 | GLP-1 stage claims (cohort c28, last month): 321.7M → 162.7M (×0.51) |
| NB05 on the 3.1 basket | PJ03, NB05, settings | New input `rx_nps_pull`: the 3.1 Rx pull with history from 2021 (4.65B claims, 294,670 HCPs, 2021-01-02 to 2026-09-30) instead of the 3.0 `kerendia_nba_3_0_Rx_05` | NB05 has 8.09M rows (was 6.45M; now the 3.1 HCP universe) and 9 Kerendia start columns; starts on Mounjaro, Zepbound and Wegovy now count under GLP-1 |
| 4 NB01 columns for the month alone | NB01 | `AVG_PATIENT_AGE`, `TOTAL_PATIENT_COUNT`, `AVG_TREATMENT_PER_PATIENT`, `TOTAL_TREATMENT_COUNT`, with the 3.0 names | Equal to 3.0 on the test HCPs (27 cohorts, 1,000,890 values compared, 0 differences) |

**Other drug classes in NB04 are 1–3% higher.** For the same cohort and window (c28, last month), NB04 stage claims grow for every class: SGLT2 +3.3%, ACE/ARB +2.3%, metformin +2.8%, insulin +2.9%, MRA +1.3%, Kerendia +3.1%. The SGLT2 ratio is 1.023–1.033 in every cohort c1–c28. The Rx claims themselves are unchanged (SGLT2: same count in every month up to July 2026). The cause is the counting rule NB04 took over from 3.0: the patient table has one row for every pair of drug class and brand a patient has in a month, and NB04 counts each Rx claim once per row. A patient on Jardiance had 1 row (SGLT2 × Jardiance); with DPP-IV the same patient has 4 ({SGLT2, DPP-IV} × {Jardiance, DPP-IV}), so the SGLT2 claims count twice. In August 2026, the 473,171 SGLT2 patients who also have DPP-IV went from 1,540,030 to 2,013,218 SGLT2 rows; the other 6,342,652 SGLT2 patients are almost unchanged (21,972,810 → 21,973,216 rows). 3.0 counted the same way, so 3.1 is now closer to 3.0 than before; the rule itself is open point 16.

---

## 5. What we have in 3.1: notebook by notebook

All counts and names from S1 and S2 (feature columns, without ID and date columns).

| Notebook | 3.0 | 3.1 | Kept | New | Not built |
| --- | ---: | ---: | ---: | ---: | ---: |
| NB01 Rx claims | 5,411 | 4,672 | 4,436 | 236 | 975 |
| NB02 Lab claims | 116 | 143 | 95 | 48 | 21 |
| NB03 Diagnosis claims | 127 | 113 | 104 | 9 | 23 |
| NB04 Combined claims | 3,691 | 3,155 | 2,930 | 225 | 761 |
| NB05 New patient starts | 188 | 163 | 154 | 9 | 34 |
| NB06 Eligible patients | 84 | 217 | 69 | 148 | 15 |
| **Total** | **9,617** | **8,463** | **7,788** | **675** | **1,829** |

Compared with `full_2026_11_11`: NB01 +4 (the averages and counts for the month alone), NB04 +90 (DPP-IV by the patient's stage), NB05 +9 (Kerendia starts) [S2, my check].

**The 675 new features**

| Notebook | New features | Count | Example names | Why new |
| --- | --- | ---: | --- | --- |
| NB01 | Kerendia prescriptions by window, payer, days supply, refill, age, gender, rejections, running totals | 234 | `TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_3_MONTH`, `TOTAL_RX_CLAIMS_KERENDIA_COMMERCIAL_IN_LAST_1_MONTH`, `PCT_TOTAL_REJECTED_RX_CLAIMS_KERENDIA_IN_LAST_3_MONTH`, `RUNNING_TOTAL_RX_CLAIMS_KERENDIA` | Kerendia is a new category and brand |
| NB01 | SGLT2 without Invokana 300 mg, running totals | 2 | `RUNNING_TOTAL_RX_CLAIMS_SGLT2_WO_INVOKANA_300MG_DAYS_SUPPLY_UNKNOWN` | These values have claims in the 3.1 data; NB01 builds a column for each value it finds |
| NB02 | Potassium: patients tested, above 5.0 mmol/L, % flagged; all and eligible patients; 4 windows | 24 | `TOTAL_PATIENTS_POTASSIUM_TESTED_IN_LAST_1_MONTH`, `TOTAL_PATIENTS_POTASSIUM_GT_5_IN_LAST_3_MONTH`, `PCT_ELIGIBLE_PATIENTS_POTASSIUM_GT_5_IN_LAST_12_MONTH` | New signal: the label advises against starting Kerendia above 5.0 |
| NB02 | HbA1c: same, at 9% or higher | 24 | `TOTAL_ELIGIBLE_PATIENTS_HBA1C_GE_9_IN_LAST_6_MONTH`, `PCT_ELIGIBLE_PATIENTS_HBA1C_GE_9_IN_LAST_12_MONTH` | New signal: uncontrolled diabetes |
| NB03 | CKD stage 5 diagnosis claims: 4 windows, % and running total | 9 | `TOTAL_DX_CLAIMS_STAGE_5_IN_LAST_3_MONTH`, `PCT_TOTAL_DX_CLAIMS_STAGE_5_IN_LAST_12_MONTH`, `RUNNING_TOTAL_DX_CLAIMS_STAGE_5` | Stage 5 codes now read |
| NB04 | Kerendia by the patient's CKD stage | 180 | `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_3_WITH_KERENDIA_IN_LAST_6_MONTH`, `PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_5_WITH_KERENDIA_IN_LAST_12_MONTH` | Kerendia is a new treatment |
| NB05 | Kerendia starts: 4 windows, % and running total | 9 | `TOTAL_PATIENTS_START_KERENDIA_IN_LAST_3_MONTH`, `PCT_TOTAL_PATIENTS_START_KERENDIA_IN_LAST_12_MONTH`, `RUNNING_TOTAL_PATIENTS_START_KERENDIA` | NB05 reads the 3.1 input since 2026-11-13 (section 4.6) |
| NB04 | UACR test stage × Invokana 100 / 300 mg | 45 | `TOTAL_RX_CLAIMS_PATIENT_WITH_TEST_UACR_STAGE_1_WITH_INVOKANA_300MG_IN_LAST_3_MONTH` | The 3.1 lab data has UACR tests (section 4.4), so these combinations now have claims |
| NB06 | Patients by diabetes type (type 2, type 1, other, none); all and eligible; % shares | 64 | `TOTAL_RX_PATIENTS_DM_TYPE_T2D_IN_LAST_3_MONTH`, `PCT_ELIGIBLE_PATIENTS_DM_TYPE_T2D_IN_LAST_12_MONTH` | Kerendia's CKD indication requires type 2 diabetes |
| NB06 | Patients by heart-failure type (preserved-EF proxy, reduced-EF proxy, mixed, unknown) | 64 | `TOTAL_ELIGIBLE_PATIENTS_HF_TYPE_HFREF_PROXY_IN_LAST_6_MONTH`, `PCT_ELIGIBLE_PATIENTS_HF_TYPE_HFPEF_PROXY_IN_LAST_12_MONTH` | Kerendia's heart-failure indication (LVEF 40% or more) |
| NB06 | Patients with any heart failure | 16 | `TOTAL_RX_PATIENTS_HF_IN_LAST_12_MONTH`, `PCT_ELIGIBLE_PATIENTS_HF_IN_LAST_12_MONTH` | Same |
| NB06 | Treated patients (denominator) | 4 | `TOTAL_RX_PATIENTS_IN_LAST_1_MONTH` | Base for the % shares |
| **Total** | | **675** | | |

**How the kept features change, per notebook**

| Notebook | Kept | What changes in the values | Why |
| --- | ---: | --- | --- |
| NB01 | 4,436 | GLP-1 brand about 2×; SGLT2 +15%; DPP-IV +7% for the same HCPs; per-HCP values of the other categories lower | New drugs and generic gliptins; added HCPs with fewer claims (section 4.2) |
| NB02 | 95 | About twice as many tests | 3.1 lab data (section 4.4) |
| NB03 | 104 | Stage 3 claims counted; missing stage stays unknown | Stage from the code |
| NB04 | 2,930 | Stage 4 down, stages 1–3 up, GLP-1 by stage up to 10× in the model features; the other classes 1–3% above `full_2026_11_11` | New stage rules (section 4.5) and new GLP-1 drugs; DPP-IV rows in the patient table (section 4.6) |
| NB05 | 154 | Lower per HCP (median of the 14 model features: 0.89) | Reads the 3.1 input since 2026-11-13: larger HCP universe, new drugs (section 4.6) |
| NB06 | 69 | Eligible patients lower | Stage 1 and 5 months not eligible (section 4.5) |

---

## 6. What is no longer built, and why

1,829 3.0 columns are not built in `full_2026_11_13`: 1,704 exact repeats, 15 NB06 columns covered by the 3.1 "last 1 month" columns, and 110 "other glucose mgmt" stage columns (X5) [S1, S2, my check]. The 4 NB01 plain monthly columns that are not exact repeats are built (added 2026-11-13, below).

**Repeated monthly columns (1,703 in 3.0).** 3.0 stored each monthly value twice: as a plain monthly column (for example `PCT_TOTAL_RX_CLAIMS_DPP_IV`) and as "last 1 month" (`PCT_TOTAL_RX_CLAIMS_DPP_IV_IN_LAST_1_MONTH`). We compared both on all rows of each 3.0 table (7.4M rows for NB02, 13.0M–13.6M for the others) [S1, my check]:

| Notebook | Plain monthly columns | Same values as "last 1 month" | Different | Example dropped columns |
| --- | ---: | ---: | ---: | --- |
| NB01 Rx claims | 979 | 975 | 4 | `PCT_TOTAL_REJECTED_RX_CLAIMS_ACE_OR_ARB`, `PCT_TOTAL_RX_CLAIMS_DPP_IV`, `TOTAL_RX_CLAIMS_SGLT2` |
| NB02 Lab claims | 21 | 21 | 0 | `PCT_TOTAL_LAB_CLAIMS_A1`, `PCT_TOTAL_LAB_CLAIMS_A2` |
| NB03 Diagnosis claims | 23 | 23 | 0 | `PCT_TOTAL_DX_CLAIMS_STAGE_1`, `PCT_TOTAL_DX_CLAIMS_STAGE_3` |
| NB04 Combined claims | 631 | 631 | 0 | `PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_1_WITH_ACE_OR_ARB` |
| NB05 New patient starts | 34 | 34 | 0 | `PCT_TOTAL_PATIENTS_START_ACE_OR_ARB`, `TOTAL_PATIENTS_START_DPP_IV` |
| NB06 Eligible patients | 15 | 0 | 15 | `PCT_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_3` |
| **Total** | **1,703** | **1,684** | **19** | |

The six categories without brands (ACE/ARB, calcium channel / beta blocker, combo drug, diuretic non-MRA, insulin, metformin) are still fully built; only their plain monthly copies (322 of the 979 in NB01) are gone. The 40 plain monthly copies among the X5 columns (20 DPP-IV, 20 other glucose mgmt) are also exact repeats in 3.0 (13.6M rows, 0 differences [S1, my check]); with the DPP-IV columns back, the 20 DPP-IV copies are repeats like the others, so 1,684 + 20 = 1,704 repeats are not built.

The 19 plain monthly columns that differ from "last 1 month" are treated separately: 4 are built, 15 are not (below).

**The 19 columns that were not exact repeats: 4 built, 15 not built** (open point 1, resolved 2026-11-13)

| Notebook | Columns | Why they are not exact repeats | Resolution |
| --- | --- | --- | --- |
| NB01 | 4: `AVG_PATIENT_AGE`, `AVG_TREATMENT_PER_PATIENT`, `TOTAL_PATIENT_COUNT`, `TOTAL_TREATMENT_COUNT` | In 3.0 the averages cover one extra month, and 3.1 keeps that rule for the look-backs, so the value for the month alone was missing | **Built** in 3.1 under the 3.0 names (added 2026-11-13, present in `full_2026_11_13`); equal to 3.0 on the test HCPs (section 4.6) |
| NB06 | 15: eligible patients in total, by GFR / diagnosis stage and by UACR stage, and their % shares, for example `PCT_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_3` | 3.0 NB06 look-backs were averages over one extra month; 3.1 counts the month itself (decision X8 [S12]) | **Not built**: the 3.1 "last 1 month" column holds the month alone and matches these 3.0 columns (decision X9 [S12]) |

**Decision X5 (NB04): the DPP-IV stage columns are built, the "other glucose mgmt" stage columns are not** (final 2026-11-16 [S12])

| What | Detail | Source |
| --- | --- | --- |
| Columns concerned | Claims by the patient's CKD stage for DPP-IV and other glucose drugs: 66 GFR / Dx stage × DPP-IV, 66 GFR / Dx stage × other glucose mgmt, 44 UACR stage × DPP-IV, 44 UACR stage × other glucose mgmt (220, including 40 plain monthly copies). Claims by the stage of a same-day lab test for these drugs are built in any case (180 columns, for example `TOTAL_RX_CLAIMS_PATIENT_WITH_TEST_GFR_STAGE_1_WITH_DPP_IV_IN_LAST_6_MONTH`), because they come from the Rx claims, not the patient table | S1, S2 |
| Why they depend on the patient journey | NB04 takes the patient's treatments from the patient table. The table has a drug only if the Rx basket switches it on for the journey (`ACTIVE_JOURNEY = Y`). 3.0 had "DPP-IV" and "Other- glucose mgmt" in it (August 2026: 0.98M and 8.47M patient-months). In 3.1 the GLP-1 drugs, part of "Other glucose mgmt" in 3.0, have their own category "GLP-1" | S3, S5, S6, my check |
| Added: DPP-IV by stage | 90 columns built and 2 model features. Their 20 plain monthly copies are exact repeats and not built (counted in the 1,704 repeats). The Rx basket of 2026-11-13 switches DPP-IV (for example Januvia, Tradjenta) on for the journey: 1,289,659 DPP-IV patients in August 2026 (section 4.6) | S2, S6 |
| Not added: "other glucose mgmt" by stage | 110 columns (90 plus 20 plain copies) and 7 model features. The other glucose drugs (for example glipizide, pioglitazone, acarbose) stay off for the journey, and NB04 counts GLP-1 and DPP-IV only through their brand, so no patient-month has the class "other glucose mgmt" | S2, S6, my check |

The 9 model features: `PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_UNKNOWN_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_1_MONTH`, `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_4_WITH_OTHER_GLUCOSE_MGMT`, `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_UACR_STAGE_3_WITH_OTHER_GLUCOSE_MGMT`, `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_4_WITH_DPP_IV_IN_LAST_12_MONTH`, `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_4_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_12_MONTH`, `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_4_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_6_MONTH`, `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_UACR_STAGE_3_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_6_MONTH`, `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_UACR_STAGE_UNKNOWN_WITH_DPP_IV_IN_LAST_3_MONTH`, `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_UACR_STAGE_UNKNOWN_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_1_MONTH` [S8, S2]. The 2 DPP-IV features are built in `full_2026_11_13`; the 7 "other glucose mgmt" features are not.

**Why DPP-IV is added.** DPP-IV is one of the brands with features of their own in 3.0 and 3.1 (`HCP_BRANDS` [S15]), with its own NB01 and NB04 columns, and 3.0 tracked DPP-IV patients in the journey (0.98M patient-months in August 2026 [S3]). With DPP-IV on for the journey, NB04 builds its stage columns as 3.0 did.

**Why "other glucose mgmt" is not added** [S12, my check]:

| Reason | Evidence |
| --- | --- |
| The 3.0 feature list is a reference only: the 3.1 model is retrained and feature selection runs again on all 3.1 features | S12 (X5); section 7.1 |
| The 7 features matter little in the 3.0 model | 0.49% of the total mean absolute SHAP of the 3.0 production model (the 2 DPP-IV features: 0.06%); ranks 64 to 705 of 752 (MLflow run `f583bcbc9d56477fae983d44c16f8c70`, `Shap_Importances.csv`) |
| Most of their signal is in the GLP-1 stage features, which 3.1 builds | Correlation with the GLP-1 version of the same column 0.77–0.89 (3.0 `final_claims_monthly`, August 2026, all 234,348 HCPs); 3 of the GLP-1 / DPP-IV versions are themselves model features |
| The class needs drugs that the shared patient journey does not track | The other glucose drugs (115.4M claims, 10,127,453 patients and 252,921 HCPs in 2023-01 to 2026-09 [S4]) would have to be on for the journey. That changes the treatment counts per patient (NB01) and the eligibility tables (PJ06) for every user of the journey, for 7 features of low importance |
| The class built from GLP-1 and DPP-IV alone would have a different meaning | The columns would carry the 3.0 names with a narrower content. NB04 counts GLP-1 and DPP-IV through their brand only, which also keeps a claim from being counted twice in the same column (section 4.6) |

What 3.1 still has for these drugs: NB01 counts the other glucose drugs in its "other glucose mgmt" category features, and NB04 builds the same-day lab test × drug columns (above).

---

## 7. What this means for the model

### 7.1 Will 3.1 use the same features as 3.0?

No. The 752 features were chosen for the 3.0 model. For 3.1 the model is retrained and feature selection runs again on all 3.1 features: the 8,463 claims features, including the 675 new ones, plus the other sources [S12, X5]. The selection decides which new features are used. It can only run once the step that joins all HCP features is switched to cohorts (open point 9); no date is set yet.

The number 270 is therefore only a check: of the 277 claims features in the 3.0 model, 270 exist in `full_2026_11_13` under the same name (268 in `full_2026_11_11`; the 2 DPP-IV features are back). It does not mean 3.1 will use them.

### 7.2 How much do the 270 features change?

For each feature we took the average per HCP in August 2026 (3.0: month 2026-08; 3.1: cohort c28) and divided 3.1 by 3.0. 1.00 = no change; 0.80 = 20% lower [S1, S2, S8, my check].

| Notebook | Model features in 3.1 | Similar (±20%) | Lower | Higher | Median change | Main reason |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| NB01 Rx claims | 172 | 116 | 52 | 4 | 0.86 | Added HCPs with fewer claims (section 4.2); running totals start later |
| NB03 Diagnosis claims | 3 | 1 | 0 | 2 | 1.32 | Stage 3 and 5 now recognised |
| NB04 Combined claims | 80 (7 not built, X5) | 11 | 39 | 30 | 0.81 | New stage mix (section 4.5); new GLP-1 drugs |
| NB05 New patient starts | 14 | 13 | 1 | 0 | 0.89 | 3.1 input since 2026-11-13 (section 4.6) |
| NB06 Eligible patients | 1 | 0 | 1 | 0 | 0.43 | Fewer eligible stage 4 patient-months (1.98M → 1.20M, August 2026) |
| **Total** | **270** | **141** | **93** | **36** | | |

The same method on `full_2026_11_11` gives the earlier result exactly (268 features: 135 similar, 94 lower, 39 higher), so the two runs are comparable. The GLP-1 stage features roughly halved between the runs (for example 19.9× → 10.0×, section 4.6).

NB01 includes the 2 features shared with NB04.

**By window** [S8, my check]

| Window | Features | Similar | Lower | Higher | Median | Why |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Running total | 69 | 2 | 59 | 8 | 0.64 | 3.1 counts from 2023-01, 3.0 from 2021-01: 44 vs 68 months in August 2026 (44 / 68 = 0.65) |
| 12 months | 67 | 48 | 8 | 11 | 0.89 | Added HCPs |
| 6 months | 52 | 36 | 8 | 8 | 0.94 | Same |
| 3 months | 48 | 31 | 11 | 6 | 0.88 | Same |
| 1 month | 33 | 23 | 7 | 3 | 0.87 | Same |
| Ratio | 1 | 1 | 0 | 0 | 0.95 | Same |

**Examples of the largest changes** [S8, my check]

| Feature | Change | Why |
| --- | ---: | --- |
| `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_1_WITH_GLP_1_IN_LAST_6_MONTH` | 10.0× | 13× more stage 1 patient-months and twice the GLP-1 claims (19.9× in `full_2026_11_11`, before the double count was removed) |
| `TOTAL_DX_CLAIMS_WITH_PATIENT_NO_NEW_STAGE_IN_LAST_6_MONTH` | 1.34× | Stage 3 and 5 claims now counted |
| `PCT_TOTAL_RX_CLAIMS_MEDICARE_IN_LAST_12_MONTH` | 1.73× | Not checked yet |
| `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_GFR_STAGE_4_AND_UACR_STAGE_UNKNOWN` | 0.33 | Fewer stage 4 patients; running total starts later |
| `RUNNING_TOTAL_RX_CLAIMS_METFORMIN_MGD_MEDICAID` | 0.49 | Running total starts later; added HCPs |
| `RUNNING_TOTAL_PATIENTS_START_SGLT2` | 0.55 | Running total starts later; 3.1 input with the larger HCP universe (0.63 in `full_2026_11_11`) |
| `RUNNING_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_4` | 0.43 | Fewer eligible stage 4 patient-months |

---

## 8. Run status

Run 338478597334222 (`full_2026_11_13`) finished with SUCCESS: all 13 tasks, all 28 cohorts, NB07 passed (2.2 min) [S14]. From the first patient-journey task to the end of NB04: 5 h 29 min; 5 h 31 min in total. Before it, the validation run 128972234721576 passed all 13 tasks on the test HCPs.

| Task | Runtime (min) | 11-11 | Task | Runtime (min) | 11-11 |
| --- | ---: | ---: | --- | ---: | ---: |
| PJ01 Labs | 18.0 | 14.6 | NB01 Rx claims | 170.4 | 151.9 |
| PJ02 Diagnosis | 18.6 | 13.5 | NB02 Lab claims | 41.0 | 31.6 |
| PJ03 Rx (incl. the new NB05 input) | 61.4 | 37.1 | NB03 Diagnosis claims | 165.3 | 146.2 |
| PJ04 Diabetes / heart failure | 5.3 | 5.9 | NB04 Combined claims | 246.0 | 221.2 |
| PJ05 Procedures | 1.4 | 1.3 | NB05 New patient starts | 166.1 | 148.6 |
| PJ06 Combine | 16.5 | 15.5 | NB06 Eligible patients | 165.0 | 146.5 |
| | | | NB07 Cohort-set check | 2.2 | 3.0 (attempt 5) |

| Output [S2] | Rows | Columns (incl. 9 ID and date columns) | 11-11 |
| --- | ---: | ---: | ---: |
| NB01 Rx claims | 8.09M | 4,681 | 4,677 |
| NB02 Lab claims | 5.17M | 152 | 152 |
| NB03 Diagnosis claims | 7.59M | 122 | 122 |
| NB04 Combined claims | 8.09M | 3,164 | 3,074 |
| NB05 New patient starts | 8.09M | 172 | 163 |
| NB06 Eligible patients | 8.09M | 226 | 226 |

No table has duplicate column names, and no column of `full_2026_11_11` is missing [S2, my check]. NB07 checks that every output has the 28 cohorts in the right training, validation and back-testing groups, without duplicate rows. In `full_2026_11_11`, attempts 1–4 stopped on rows without a provider ID (open point 8); attempt 5 passed (231 GB of outputs).

---

## 9. Open points

| # | Point | Who decides | Rerun needed |
| --- | --- | --- | --- |
| 1 | ~~19 monthly columns not in 3.1~~ Resolved 2026-11-13 | Wenjie | Done |
| 2 | GLP-1 has no category feature of its own | Wenjie | NB01, NB04 if added |
| 3 | New drugs have no features of their own | Wenjie | NB01, NB04 if added |
| 4 | Two copies of the product basket | Team | No |
| 5 | ~~DPP-IV and other glucose drugs in the patient journey (X5)~~ Resolved 2026-11-16: DPP-IV stage columns built, "other glucose mgmt" stage columns not | Wenjie, Raman | Done |
| 6 | Eligibility rules C1 (SGLT2) and C9 (diabetes) | NBA team | PJ06, NB01–NB06 |
| 7 | Retraining and feature selection | Raman | Model only |
| 8 | Rows without a provider ID | Team | NB01–NB06 provider tables |
| 9 | Combine step not switched to cohorts | Team | Combine step |
| 10 | Running totals start in 2023 | Wenjie | All if changed |
| 11 | Near-duplicate SGLT2 features | Wenjie, Raman | No (selection) |
| 12 | ~~NB05 still reads the 3.0 input~~ Resolved 2026-11-13 | Team | Done |
| 13 | Type 1 diabetes kidney codes in NB03 | Wenjie | NB03 if removed |
| 14 | More patient rows per month in 3.1, not yet explained | Team (check) | No |
| 15 | Clean-up and defaults | Team | No |
| 16 | NB04 counts a claim once per class × brand row of the patient-month | Wenjie | NB04 if changed |
| 17 | Storage in Unity Catalog tables instead of files in the volume (team decision 2026-11-16) | Team | Validation run on tables (done); first full run on tables `full_2026_11_16` |

**1. 19 monthly columns are not in 3.1.** What is going on: 4 NB01 averages and counts and 15 NB06 eligibility columns held values for the month alone that 3.1 does not store (section 6). Options: (a) accept, because 3.1 keeps the look-back versions, for example `TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_3_IN_LAST_1_MONTH`; (b) restore them as extra columns. None of them is in the 752 [S7, my check]. **Resolved 2026-11-13:** the 4 NB01 columns are built again (equal to 3.0 on the test HCPs); the 15 NB06 columns stay out, because the 3.1 "last 1 month" columns hold the same values (X8, X9) (section 6).

**2. GLP-1 has no category feature of its own.** What is going on: by option C, GLP-1 drugs count under "Other glucose mgmt" and under the GLP-1 brand, as in 3.0 (section 4.3). GLP-1 claims doubled (186.4M → 376.0M), so "Other glucose mgmt" is now 70% GLP-1 (375.8M of 534.6M in `full_2026_11_13`, which also includes DPP-IV) [S4, my check]. Options: (a) keep; (b) a separate GLP-1 category, which needs a new name to avoid the clash with the brand columns. Effect of (b): a new set of category columns in NB01 and NB04; other categories have 236–245 NB01 columns each [S2].

**3. The new drugs have no features of their own.** What is going on: Mounjaro (124.1M claims), Zepbound (29.0M), Wegovy (25.8M) sit inside the GLP-1 brand, generic dapagliflozin (16.2M) inside SGLT2 [S4]. The model cannot tell them apart. Options: (a) keep; (b) add some of them to the brand list; today's brands have 252–263 NB01 columns each (brand table in section 4.3).

**4. Two copies of the product basket.** What is going on: the run reads the volume folder [S6]. The workspace folder `Final Product Basket` holds the version before the 2026-11-05 update (16 Rx products and J0606 switched off). If someone uses the workspace copy, Kerendia and the new GLP-1 drugs drop out. Action: update or clearly label the workspace copy.

**5. DPP-IV and other glucose drugs in the patient journey (X5) (resolved 2026-11-16).** What was going on: NB04 builds its patient stage × drug columns from the patient table, which in `full_2026_11_11` had neither DPP-IV nor the other glucose drugs (3.0, August 2026: 0.98M DPP-IV and 8.47M "other glucose mgmt" patient-months [S3]). Decision X5: DPP-IV is on for the journey since 2026-11-13 (1,289,659 DPP-IV patients in August 2026), so its 90 NB04 stage columns and 2 of the 9 model features are built (the 20 plain monthly copies are repeats) (section 4.6). The other glucose drugs (for example glipizide, pioglitazone; 115.4M claims since 2023 that NB01 counts) stay off for the journey, so the 110 "other glucose mgmt" stage columns and their 7 model features are not built. Why: section 6, decision X5. 3.1 feature selection runs again on all 3.1 features.

**6. Eligibility rules C1 and C9 (patient journey).** What is going on: the SGLT2 rule (C1) is meant to exclude patients with unknown stage who never had an SGLT2, but it compares the stage with -1 and never applies, in 3.0 and in 3.1 [S10, PJ06 combine]. Fixing it makes 56% of the eligible months not eligible. C9: 58% of eligible months have no type 1 or type 2 diabetes diagnosis [S10]. Effect of a change: eligibility and all patient-based features in NB01, NB03, NB04 and NB06 change; rerun PJ06 and the HCP job (no code change in the HCP notebooks).

**7. Retraining and feature selection.** What is going on: 129 of the 270 model features move by more than 20% per HCP (section 7), and 675 new features are available. The 3.0 model cannot be applied to 3.1 as it is. Action: run feature selection and training on 3.1 after point 9.

**8. Rows without a provider ID.** What is going on: the provider tables have 3,094 rows without a provider ID (NB01, NB04), 949 (NB03) and 3,001 (NB06), because the NPI-to-provider mapping misses 105 HCPs and gives 2 IDs to 52 [S2, mapping `query_output/kerendia_nba_3_0_npi_bhid_mapping`]. The NPI tables are complete. Proposal: keep the mapping, fill or de-duplicate these 157 HCPs from the provider ID in the 3.1 Rx input, before the combine step.

**9. Combine step not switched to cohorts.** What is going on: the step that joins all HCP features for the model (`99_Combine_Physician_Data`) joins by calendar month; 3.1 delivers the claims features by cohort. Other HCP feature notebooks (promotion and others) still use the 3.0 logic. Action: join on provider and cohort; plan in `99 Combine Physician Data Files/NBA_3_1_Combine_Physician_Data_Plan.md`.

**10. Running totals start in 2023.** What is going on: 3.1 counts from 2023-01-01, 3.0 from 2021 (section 3.1), so running totals are about a third lower (median 0.65, section 7). 69 of the 270 model features in 3.1 are running totals [S8]. Options: (a) keep 2023; (b) pull data from 2021, which makes every pull larger.

**11. Near-duplicate SGLT2 features.** What is going on: 155 "SGLT2 without Invokana 300 mg" columns in 3.1 (187 in 3.0) [S1, S2], for example `RUNNING_TOTAL_RX_CLAIMS_SGLT2_WO_INVOKANA_300MG`, are almost equal to the SGLT2 columns (correlation about 1.0), because Invokana 300 mg has 1.13M of the 165.2M SGLT2 claims [S4]. Options: drop them before selection, or let selection handle them.

**12. NB05 still read the 3.0 input (resolved 2026-11-13).** Resolution: PJ03 now writes `rx_nps_pull`, the 3.1 Rx pull with history from 2021 (same basket and HCP universe as the NB01 input), and NB05 reads it; Kerendia, Mounjaro, Zepbound and Wegovy starts are counted (section 4.6). Open from this point: confirm 0 for months without claims. What was going on: a "new start" needs each patient's claims since 2021, which the 3.1 Rx pull (from 2023) does not have, so NB05 reads `kerendia_nba_3_0_Rx_05` [S3]. Starts on Kerendia, Mounjaro, Zepbound or Wegovy are not counted. Also, months without claims are 0 in 3.1 and empty in 3.0. Options: a 3.1 input with history from 2021 for these drugs; confirm 0 for empty months.

**13. Type 1 diabetes kidney codes in NB03.** What is going on: 1.39M rows with type 1 diabetes kidney codes count as CKD diagnosis claims with unspecified stage [`hcp_level_features/03 Diagnosis Claims Files/NBA_3_1_Dx_Claims_Features_Plan.md`]. Options: keep (CKD with type 1 diabetes is still CKD) or remove (if the features should follow the type 2 indication).

**14. More patient rows per month in 3.1.** What is going on: August 2026 has 113.2M patient rows in 3.1 against 72.2M in 3.0 [S3, S5]. We have not split the difference by source yet (more lab patients, new drugs, months counted from the first diagnosis). Action: check, because it drives the patient-based features.

**15. Clean-up and defaults.** What is going on: the settings fall back to the 3.0 HCP universe when none is given; older run outputs take a lot of space [S15]. Action: default to the 3.1 universe, remove old run outputs. Done 2026-11-16: the "latest run" setting (`HCP_LATEST_FULL_RUN`) points to `full_2026_11_13`. Also: in validation runs PJ01 does not save its lab pull and runs the lab query several times (whole notebook about 60 min instead of 15).

**16. NB04 counts a claim once per class × brand row.** What is going on: the patient table has one row for every pair of drug class and brand a patient has in a month, and NB04 counts each Rx claim once per row, as 3.0 did. So a claim counts once for every brand value of the patient-month, for example twice in the SGLT2 column for a patient on Jardiance and DPP-IV. Since DPP-IV is back, the class counts rose 1–3% (section 4.6). Options: (a) keep, as 3.0; (b) count each claim once per class and once per brand. Effect of (b): all stage × treatment features in NB04 change; rerun NB04.

**17. Storage in Unity Catalog tables.** What is going on: the team decided on 2026-11-16 that nothing is saved as Parquet and every 3.1 input and output is a Unity Catalog table. Today the HCP universe and the cohort list are Parquet, the baskets are CSV, and the pulls, patient-journey and HCP outputs are Delta files in the volume, none of them a table [S2, S4, S5, S6]. Plan: section 10. Status 2026-11-16: built and validated. A validation run on tables gives the same features as a validation run on files with the same code (section 10.5). The job saves to tables by default since 2026-11-16 (`STORAGE_MODE = uc`); the first full run on tables, `full_2026_11_16`, is running.

---

## 10. Storage in Unity Catalog tables

### 10.1 Summary

* **What:** every 3.1 input and output of the HCP pipeline (job 1010893614518587, PJ01–PJ06 and NB01–NB07) is saved as a managed Unity Catalog table in `kerendia_nba_3_1`, instead of Parquet, CSV or Delta folders in the volume (team decision 2026-11-16).
* **Why:** tables can be found and read by name in Unity Catalog, each with a description and tags; access is managed in Unity Catalog; later steps (the combine step, the model) read fixed names; the HCP tables can later get keys and become time-series feature tables (step 7).
* **The features do not change:** the pipeline logic is the same, only where data is read and saved. A validation run on tables gave the same 24 tables as a validation run on files (section 10.5).
* **One switch:** the job parameter `STORAGE_MODE`: `uc` = tables (default since 2026-11-16), `volume` = files, as before. Switching back needs no code change; the volume folders of earlier runs are unchanged.
* **Status 2026-11-16:** steps 0–5 done (section 10.4). The first full run on tables, `full_2026_11_16` (run 814119312914044), is running; after a comparison with `full_2026_11_13` it becomes the run of record. Until `HCP_LATEST_FULL_RUN` points to it, a validation run on tables fails (it reads the lab and Dx pulls of that full run as tables).
* **Code:** branch `dev/hcp-claims-features` (commit 697f8d3, 2026-11-16).

### 10.2 Today: files in the volume

Up to `full_2026_11_13`, all 3.1 data are files in `kerendia_nba_3_1_volume` [S2, S4, S5, S6]:

| Data | Where | Format |
| --- | --- | --- |
| HCP universe | `HCP_Universe_without_call_hcps/` | Parquet |
| Claims cohorts c1–c28 | `cohorts/claims/cohorts.parquet` and `metadata.json` | Parquet, JSON |
| Product baskets (Rx, Dx, Dx flag additions, Lab, Px) | Product mapping folder, one CSV per version with the date in the file name | CSV |
| Raw pulls (PJ01–PJ03) | `hcp_level_model/dev_pipeline/query_output/<run>/` | Delta folders |
| Patient journey (PJ01–PJ06) | `hcp_level_model/dev_pipeline/notebook_output/<run>/patient_journey/` | Delta folders |
| HCP features (NB01–NB06) | `hcp_level_model/dev_pipeline/notebook_output/<run>/hcp_claims/`, partitioned by `COHORT_SET` | Delta folders |
| Intermediate results | `.../hcp_claims/_stage/` and the Rx scratch pull `rx_fills_tagged` | Delta folders, kept after the run |

How it works: `00_cohort_config` builds the paths from the run name (`RUN_OUTPUT_DIR`), and each notebook reads and writes by path; the newest basket is the file with the latest date in its name. What this means:

* No description or tags: one has to know the path, and the folder names say little (for example the suffix `_validation` on every patient-journey folder, also in full runs).
* Access is granted for the volume as a whole, not per dataset.
* The run of record is a convention (a folder name in the settings and in this plan): anyone reading the outputs must change paths for every new run.
* Intermediate folders stay after each run.

### 10.3 With Unity Catalog tables: what changes

The notebooks still name a path, but read and save through shared functions in `00_cohort_config` (cell "Storage helpers": `read_delta`, `write_delta`, `path_exists`, `read_mapping_csv`, `save_product_mapping`, `drop_temp_tables`, `register_run`, `set_run_of_record`). In table mode these turn the path into a table name (section 10.3.4), so the notebooks changed only a few lines each.

| Topic | Files (`volume`) | Tables (`uc`) |
| --- | --- | --- |
| Inputs | Parquet and CSV in the volume | Tables `input_*` and `ref_*`, loaded once (section 10.3.3) |
| New basket version | New CSV file | New rows in the `ref_` table with a new `BASKET_DATE` (`save_product_mapping`) |
| Run outputs | Delta folders per run | Tables `<run>_<layer>_<dataset>` (section 10.3.4) |
| Intermediate results | Folders, kept | Temporary tables `tmp_<run>_...`, deleted at the end of each notebook |
| Description | None | Comment and tags on every table |
| Runs | Folder names | Run list `run_registry` (NB07 adds a run when its checks pass) |
| Run of record | A folder name by convention | Views with fixed names `hcp_*` (`set_run_of_record`) |
| Safety | – | In table mode no file is written; a target without a table name stops the run |

Not changed: the feature logic and values; the `COHORT_SET` partitions; the 3.0 tables read from the 3.0 volume (section 10.3.3); the DX, PX and RX event lists in the workspace (checks only).

For anyone reading the outputs: runs from `full_2026_11_16` on exist only as tables. Read `kerendia_nba_3_1.hcp_<table>` (the run of record, once set) or `kerendia_nba_3_1.<run>_hcp_<table>` for a given run. Earlier runs stay in the volume folders. The combine step (step 8) and any code that reads the volume paths of the HCP outputs must move to these names.

#### 10.3.1 Setup

| Topic | Decision | Source |
| --- | --- | --- |
| Schema | `kerendia_nba_3_1` (owner Wenjie, created 2026-10-28). Tables since 2026-11-16 (sections 10.3.3, 10.3.4). The group `US_DSAA_PROD_GROUP` has all privileges on it through the catalog | S16, my check |
| Table type | Managed tables only; nothing new is saved as files | Team decision |
| Job account | Job 1010893614518587 runs as a user account (patricio.guledjian.ext@bayer.com), so the tables will be owned by that account. Later: move the job to a service principal or hand the tables to the group | S14, my check |
| Layout | The HCP tables keep the `COHORT_SET` partitions (training, validation and back-testing groups), as today | S15 |
| Keys | HCP (`NPI_NUMBER` or `PROVIDER_ID`), `COHORT_ID` and the cutoff date, never empty, so the HCP tables can later become time-series feature tables | – |
| Run of record | The first full run on tables (`full_2026_11_16`) becomes the run of record after a comparison with `full_2026_11_13` (volume folders). A validation run on tables proved the new code first (section 10.5) | – |
| Old runs in the volume | Kept until the tables are checked | – |

#### 10.3.2 How the tables are organised

A Unity Catalog schema has no folders, so all tables sit side by side in `kerendia_nba_3_1`. They are organised by:

* **Names that sort into groups:** `<run>_<layer>_<dataset>` for each run, with the layers `pull` (raw pulls), `pj` (patient journey) and `hcp` (HCP features); `input_<dataset>` and `ref_<dataset>` for data not tied to a run. The prefix `kerendia_nba_3_1_` and the suffix `_validation` of today's patient-journey names are dropped.
* **A comment on each table:** run tables: layer, run, the notebook that wrote it, the date and the old volume path (set by `write_delta`); input and reference tables: what one row means, the source file and the load date.
* **Tags on each table:** run tables `project`, `run`, `layer` (plus the notebook's own tags, e.g. `dataset`); input and reference tables `project`, `layer`, `dataset`, `load_date`.
* **A run list (`run_registry`):** one row per run: `RUN_NAME`, `RUN_TYPE` (full or validation), `STATUS`, `JOB_ID`, `JOB_RUN_ID`, `IS_RUN_OF_RECORD`, `NOTE`, `UPDATED_AT`. NB07 adds the run when all its checks pass (table mode only).
* **Views with fixed names for the run of record:** for example `hcp_claims_monthly_cohort` reads `<run of record>_hcp_claims_monthly_cohort`. Later steps (the combine step, the model) always read the same names; a new run of record only changes the views.

#### 10.3.3 Inputs and reference tables (no run)

| Table | Today [S6, my check] | Note |
| --- | --- | --- |
| `input_hcp_universe` | `kerendia_nba_3_1_volume/HCP_Universe_without_call_hcps/` (Parquet) | 294,727 rows. Load date in the comment and tag, not as a column, so the table equals the file |
| `input_claims_cohorts` | `kerendia_nba_3_1_volume/cohorts/claims/cohorts.parquet` and `metadata.json` | Cohorts c1–c28 with cutoffs (28 rows). `metadata.json` (read by no code) is in the table comment |
| `ref_product_mapping_rx` | `Kerendia_Rx_Final_Product_Mapping_2026_11_06.csv`, `..._2026_11_13.csv` | Column `BASKET_DATE`, both versions |
| `ref_product_mapping_dx` | `Kerendia_Dx_Final_Product_Mapping_2026_11_06.csv` | Same |
| `ref_dx_flag_additions` | `Kerendia_Dx_Flag_Additions_2026_11_06.csv` | Same |
| `ref_product_mapping_lab` | `Kerendia_Lab_Final_Product_Mapping_2026_11_06.csv` | Same |
| `ref_product_mapping_px` | `Kerendia_Px_Final_Product_Mapping_2026_11_06.csv` | Same |
| `run_registry` | – | New; created by the first table-mode run (2026-11-16) |

Loaded on 2026-11-16 by the notebook `03_HCP_level_features/00_load_uc_inputs` (rerun = same tables). Basket tables hold the exact CSV text of every field (all strings), plus `ROW_NO` (file row order) and `BASKET_DATE`: Rx 739 rows (367 for 2026_11_06 + 372 for 2026_11_13), Dx 240, Dx flag additions 116, Lab 28, Px 145. Check (13 of 13 OK): the Parquet tables have the same types and rows as the files (no row only on one side); each basket version has the same field text row by row, and pandas reads the same table from the file and from the table for the three read options used in PJ01–PJ05; the latest version per kind is the same as from the files. New basket versions: `save_product_mapping` (00_cohort_config), not a new CSV.

The 3.0 reference tables in the 3.0 volume (S1, S3, the NPI-to-provider mapping) stay as they are: they are not ours and are only read. Three of them change what a run writes and are refreshed by the 3.0 pipeline: the NPI-to-provider mapping (provider IDs of the six provider tables and the NPI join of the patient journey), `Rx_01_new` (column list of NB01, rows before 2023 in NB04 and NB06, never counted) and `Lab_04` (rows before 2023 in NB04). Between the backup of 2026-10-23 and the live tables of 2026-10-26, the mapping gained 8,112 and lost 54 NPI-provider pairs [my check]. Rerunning an old run can therefore give other provider IDs. Not tracked yet (option: record their Delta versions in `run_registry`). All other 3.0 reads only feed checks (`RUN_CHECKS` or validation runs).

#### 10.3.4 Tables per run (26 tables per full run; example `full_2026_11_13`)

Each name below starts with the run name, for example `full_2026_11_13_pull_rx_hcp`.

| Layer | Table (after the run name) | Today in the run folders [S2, S4, S5] | Written by |
| --- | --- | --- | --- |
| pull | `pull_lab_step4` | `lab_step4_pull` | PJ01 |
| pull | `pull_dx_step4` | `dx_step4_pull` | PJ02 |
| pull | `pull_rx_hcp`, `pull_rx_nps` | `rx_hcp_pull`, `rx_nps_pull` | PJ03 |
| pj | `pj_lab_journey`, `pj_lab_flags` | `kerendia_nba_3_1_lab_journey_validation`, `..._lab_flags_validation` | PJ01 |
| pj | `pj_dx_journey` | `..._dx_journey_validation` | PJ02 |
| pj | `pj_rx_journey` | `..._rx_journey_validation` | PJ03 |
| pj | `pj_dm_hf_flags` | `..._dm_hf_flags_validation` | PJ04 |
| pj | `pj_px` | `..._px_validation` | PJ05 |
| pj | `pj_pat_new_and_total_treatments`, `pj_pat_new_ckd_stage`, `pj_pat_gfr_dx_stage`, `pj_pat_uacr_stage`, `pj_pat_sglt2_filter_m` | `..._pat_*_validation` | PJ06 |
| hcp | `hcp_claim_rx_monthly_cohort`, `hcp_provider_claim_rx_monthly_cohort` | `claim_rx_monthly_cohort`, `provider_claim_rx_monthly_cohort` | NB01 |
| hcp | `hcp_claim_lab_monthly_cohort`, `hcp_provider_claim_lab_monthly_cohort` | same pattern | NB02 |
| hcp | `hcp_claim_diagnosis_monthly_cohort`, `hcp_provider_claim_diagnosis_monthly_cohort` | same pattern | NB03 |
| hcp | `hcp_claims_monthly_cohort`, `hcp_final_claims_monthly_cohort` | same pattern | NB04 |
| hcp | `hcp_claim_rx_nps_monthly_cohort` | same pattern | NB05 |
| hcp | `hcp_claim_eligible_patient_cohort`, `hcp_provider_claim_eligible_patient_cohort` | same pattern | NB06 |

NB07 only checks the `hcp_` tables. `rx_fills_tagged` (scratch pull of PJ03, no reader) and the `_stage/` folder become temporary tables `tmp_<run>_...`, deleted at the end of PJ03 and of each HCP notebook; after a failed run they stay until the next run of the same name. A validation run writes 24 tables (it reads the lab and Dx pulls of the run in `HCP_LATEST_FULL_RUN`, now `full_2026_11_13`). In table mode the save function never writes a file: a target without a table name stops the run.

#### 10.3.5 Still to confirm

1. The original DX, PX and RX event lists (CSV in the workspace folder `Final Product Basket`, used only for checks) stay in Git as source documents.
2. `HCP_Universe/` (with call HCPs) is also in the volume; only the universe in the settings is loaded.
3. The provider-level tables keep their current base names, so the 3.0 names stay recognisable.

### 10.4 Steps

| Step | What | Check | Status |
| --- | --- | --- | --- |
| 0 | Job account and rights; table list (this section) | – | Done 2026-11-16 |
| 1 | Shared save and read functions in the settings notebook (`00_cohort_config`, cell "Storage helpers") | Test on a test table | Done: write, read back, comment and tags on a test table (deleted); file writes refused in table mode |
| 2 | PJ01–PJ06 and NB01–NB07 use them | No Parquet writes or volume output paths left in the job notebooks | Done: scan of the 13 notebooks; only 3.0 reads, event lists and the switched-off Rx basket draft (workspace) remain |
| 3 | One-time load of inputs and baskets | Same rows and contents as the files | Done: 7 tables, 13 of 13 checks OK (section 10.3.3) |
| 4 | Validation run on tables | Same features as a validation run on files with the same code | Done: section 10.5 |
| 5 | Update this plan; one commit | – | Done: commit 697f8d3 (2026-11-16) |
| 6 | Job default `STORAGE_MODE = uc`; first full run on tables (`full_2026_11_16`); compare with `full_2026_11_13`; make it the run of record (views `hcp_*`) and point `HCP_LATEST_FULL_RUN` to it | Same features as `full_2026_11_13`, apart from changes in the source data | Running (started 2026-11-16) |
| 7 | Primary keys on the HCP tables (time-series feature tables) | Same values in a point-in-time lookup as in a plain join | To do |
| 8 | Combine step on cohorts, reading the views (open point 9) | – | To do |

The validation was first planned against `validation_2026_11_13`. That run started before `full_2026_11_13` existed, so its lab and Dx features used the pulls of an older full run; it is not a fair comparison. Instead, two validation runs of the same code were run on 2026-11-16, one on files and one on tables (section 10.5).

### 10.5 Validation: tables vs files (2026-11-16)

| Run | Mode | Output | Result |
| --- | --- | --- | --- |
| 781010009126241 | `STORAGE_MODE = volume` | `validation_2026_11_16_vol` (volume folders) | Success, 13 of 13 tasks, about 63 min |
| 1054941833537319 | `STORAGE_MODE = uc` | `validation_2026_11_16_uc` (24 tables) | Success, 13 of 13 tasks, about 123 min |

Comparison of all 24 tables (2 Rx pulls, 11 patient-journey, 11 HCP) [my check]:

* Columns, column order, types and row counts: identical in all 24.
* Values: 20 tables identical (same sum of a hash of every row).
* `pj_rx_journey` (55,463 rows) and `pj_pat_gfr_dx_stage` (13,401 rows): the same items in lists (treatment categories, brands) in a different order; after sorting the lists, no row differs.
* `hcp_claim_rx_monthly_cohort` and `hcp_provider_claim_rx_monthly_cohort`: 8 of 3,904 feature columns differ, all averages (`AVG_PATIENT_AGE_*`, `AVG_TREATMENT_PER_PATIENT_*` and their `RUNNING_` versions); the largest difference is 9.1e-13. No count, flag or text value differs.
* Both kinds of difference come from how Spark builds lists and adds up decimal numbers (order of the rows), not from the storage. Not yet shown by two runs on files.
* The table run wrote no folders in the volume and left no temporary tables; NB07 added it to `run_registry` (SUCCESS, not the run of record).

The table-mode run took longer: PJ01–PJ03 took about 66 min each in the table run against 3–10 min in the file run; the later tasks took about the same time. Both runs started at the same moment (the job allows one run at a time with a queue, but the second did not wait), so the likely cause is the two runs competing for Snowflake, not the tables. Not checked yet.


