# HCP-level claims features in NBA 3.1: Readiness Plan

**For:** Wenjie. **Reviewed by:** Raman. **Version:** 2026-11-12.  
**Run assessed:** `full_2026_11_11` (job 1010893614518587, run 441950237921).

The plan tells the story in order: where to find things (section 1), a summary (2), what NBA 3.0 built (3), what changed on the way to 3.1 and why (4), what 3.1 delivers notebook by notebook (5), what is no longer built (6), what this means for the model (7), the run (8), and the open points (9).

Every number has a source in brackets, for example [S3]. The sources are listed in section 1. Numbers marked "my check, 2026-11-12" were counted on those tables for this plan.

---

## 1. Where to find things

Volume root: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/`. Workspace root: `/Workspace/Users/wenjie.chen@bayer.com/`.

| Ref | What | Path |
| --- | --- | --- |
| S1 | 3.0 HCP feature tables (NB01–NB06) | `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/`: `claim_rx_monthly`, `claim_lab_monthly_ZS`, `provider_claim_diagnosis_monthly`, `final_claims_monthly`, `kerendia_nba_3_0_claim_rx_nps_monthly`, `kerendia_nba_3_0_claim_eligible_patient` |
| S2 | 3.1 HCP feature tables (NB01–NB06) | `kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/full_2026_11_11/hcp_claims/`: `claim_rx_monthly_cohort`, `claim_lab_monthly_cohort`, `provider_claim_diagnosis_monthly_cohort`, `final_claims_monthly_cohort`, `claim_rx_nps_monthly_cohort`, `claim_eligible_patient_cohort` |
| S3 | 3.0 inputs and patient tables | `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/`: `Rx_01_new` (Rx), `Lab_03` (NB02 lab), `Lab_04` (NB04 lab), `Dx_03`, `kerendia_nba_3_0_Rx_05`, `pat_new_and_total_treatments`, `pat_new_ckd_stage`, `pat_gfr_dx_stage_and_treatment_category`, `pat_uacr_stage_and_treatment_category_new`, `df_px` (dialysis), `df_t2d_patient` (diabetes); eligibility: `.../notebook_output/kerendia_nba_3_0_pat_sglt2_filter_m` |
| S4 | 3.1 inputs | `kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/query_output/full_2026_11_11/`: `rx_hcp_pull`, `lab_step4_pull`, `dx_step4_pull` |
| S5 | 3.1 patient tables | `kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/full_2026_11_11/patient_journey/`: `kerendia_nba_3_1_<table>_validation` (for example `..._pat_gfr_dx_stage_validation`, `..._pat_sglt2_filter_m_validation`) |
| S6 | 3.1 product baskets (used by the run) | `kerendia_nba_3_1_volume/final_product_mapping/Kerendia_{Rx,Dx,Lab,Px}_Final_Product_Mapping_2026_11_06.csv`, `Kerendia_Dx_Flag_Additions_2026_11_06.csv` |
| S7 | The 752 model features of 3.0 | `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/input_files/Kerendia_NBA_3_feature_list_752_features.csv` |
| S8 | The 277 claims features among the 752, with notebook, family and window | `kerendia_nba_3_1_develop_pg/NBA 3.1 - Dev/Feature Analysis/NBA_3_1_HCP_Claims_Selected_Features_277.csv` |
| S9 | 3.0 code | `kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/00_Write_Input_Files.py` (input queries) and `.../00_Helper_Notebooks/00_step23_function.py` (look-back and running totals) |
| S10 | Patient-journey plan and combine notebook | `.../03_HCP_level_features/Patient_Journey_Validation/Alignment_Markdowns/Strategy and Execution/AI_Readiness_Plan.md`; `.../Patient_Journey_Validation/Combine Files/06_patient_journey_combine_3_1` |
| S11 | Per-notebook plans | `hcp_level_features/02 Lab Claims Files/NBA_3_1_Lab_Claims_Features_Plan.md`, `03 Diagnosis Claims Files/NBA_3_1_Dx_Claims_Features_Client_Summary.md`, `04 Monthly Cohort Claims Files/NBA_3_1_Claims_Features_Plan.md` |
| S12 | Decision log (X1–X20) | `hcp_level_features/Alignment_Markdowns/Strategy_and_Execution/NBA_3_1_HCP_Features_Decisions.md` |
| S13 | HCP universe | `NBA 3.1 - Dev/01_HCP_Universe/NBA_3.1_HCP_Universe_Presentation_V6_ZS_Recommended.md` |
| S14 | Run | Job 1010893614518587 "NBA 3.1 Patient Journey + HCP Features", run 441950237921 |
| S15 | Settings (brand list, start date, GLP-1 rule) | `03_HCP_level_features/00_cohort_config` |

---

## 2. Summary

| Topic | 3.0 | 3.1 | Source |
| --- | --- | --- | --- |
| Time design | One row per HCP and calendar month | One row per HCP and cohort (28 monthly cohorts, May 2024 to August 2026) | S1, S2 |
| HCPs with Rx claims since 2023 | 234,170 | 294,612 (220,892 in both) | S3, S4, my check |
| Products | No Kerendia; no Mounjaro, Zepbound, Wegovy or generic dapagliflozin | All of them counted | S6 |
| Lab and diagnosis inputs | Separate 3.0 queries that missed many tests and the stage 3 and 5 codes | The 3.1 patient journey | S9, S11 |
| New signals | – | Potassium, HbA1c, diabetes type, heart-failure type, CKD stage 5, Kerendia | S2 |
| Features in NB01–NB06 | 9,617 | 8,360 | S1, S2 |

Of the 9,617 3.0 features, 7,694 are kept and 1,923 are not built any more: 1,684 were exact repeats of another column, 220 were dropped by decision X5 (the patient journey no longer tracks DPP-IV and other glucose drugs, section 6), and 19 need a decision. 666 features are new.

The 3.0 model uses 277 of these features [S8]; 268 exist in 3.1. Their values per HCP change: 135 stay within ±20%, 94 are lower and 39 are higher (section 7). The main causes are the 73,720 added HCPs, who write fewer prescriptions each, the later start of the running totals, and the new CKD stage rules. The model is retrained, and feature selection runs again on all 3.1 features [S12, X5].

**Status:** the full run succeeded for all 13 tasks and all 28 cohorts [S14]. Section 9 lists 15 open points. One correction to earlier versions of this plan: the SGLT2 rule of the Kerendia eligibility is **not** applied in 3.1 either (open point 6). The eligible share drops for other reasons (section 4.5).

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
| Plain monthly columns | Built next to "last 1 month" with the same value | Not built | Exact repeats (section 6) | S1, S2 |

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
| Rx | Snowflake view for the category, brand rules in the 3.0 query | Rx basket: 367 products, 245 active | S9, S6 |
| Diagnosis, lab, procedures | Code lists in the 3.0 queries | Dx, lab and Px baskets, plus a list of 38 type 2 diabetes, 68 type 1 diabetes and 10 heart-failure codes | S9, S6 |

**What is different in the 3.1 baskets [S6]**

| Change | Products | Why |
| --- | --- | --- |
| GLP-1 drugs counted | Already in 3.0: Ozempic, Trulicity, Rybelsus, Victoza, Bydureon BCise, Byetta. New: Mounjaro, Zepbound, Wegovy, Wegovy HD, liraglutide, Saxenda, exenatide | The new ones are not in the Snowflake view; 3.1 adds them (basket update of 2026-11-05) |
| Generic dapagliflozin counted as SGLT2 | Dapagliflozin, dapagliflozin / metformin | Not in the view; a generic of Farxiga |
| Kerendia its own category and brand | Kerendia | The target drug; kept out of MRA so the competitor MRA counts are not inflated |
| New dialysis code | J0606 (etelcalcetide, given only to hemodialysis patients) | Finds more dialysis patients |
| DPP-IV and other glucose drugs **off** in the patient journey | For example Januvia, Tradjenta, glipizide, pioglitazone (`ACTIVE_JOURNEY = N`, note "Not in the 3.0 journey") | The basket was built on the product list of the 3.0 patient journey. This causes decision X5 (section 6) |

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

**Is the GLP-1 setup the same as in 3.0?** Yes. In 3.0 the Snowflake view put the GLP-1 drugs in the category "Other glucose mgmt", and GLP-1 was a brand. The 3.1 basket gives the GLP-1 drugs the category "GLP-1". Because GLP-1 is also on the brand list, NB01 would have created the same column names twice (for example `TOTAL_RX_CLAIMS_GLP_1_IN_LAST_3_MONTH` as category and as brand). Decision "option C" (2026-11-05) maps the GLP-1 category back to "Other glucose mgmt" in NB01 and NB04, so the structure is the same as in 3.0 [S15, S12]. The patient journey keeps "GLP-1" as a category.

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
| PJ03 Rx | Each patient's treatments per month | New Rx basket (section 4.3): GLP-1 its own category, Kerendia added, generic dapagliflozin as SGLT2; DPP-IV and other glucose drugs off | Count the new drugs |
| PJ04 Diabetes / heart failure | Diabetes and heart-failure flags per patient | 3.0: one type 2 diabetes flag. 3.1: diabetes type (type 2, type 1, other, none) and heart-failure type (preserved-EF proxy, reduced-EF proxy, mixed, unknown); the 3.0 flag is kept as `T2D_FLAG_30` | Kerendia's two indications |
| PJ05 Procedures | Dialysis patients and first dialysis date | New codes incl. J0606; a column that was always 1 is dropped | Find more dialysis patients |
| PJ06 Combine | Eligibility per patient and month; the tables the HCP notebooks read | Heart-failure flag and diabetes type added. Eligibility rule unchanged: stage 2–4 or unknown, not on dialysis. The SGLT2 rule is still not applied (it compares the stage with -1, copied from 3.0) | Open decisions C1 and C9 (open point 6) |

**What the patient tables look like now, and the effect on the HCP features** (rows 3.0 → 3.1) [S3, S5, my check]

| Patient table | Read by | Rows 3.0 → 3.1 | Why the rows changed | Effect on the HCP features |
| --- | --- | --- | --- | --- |
| New and total treatments | NB01 | 4.50B → 4.12B | 3.0 covers 70 months (2021-01 to 2026-10), 3.1 45 months (2023-01 to 2026-09). For the same months (2023-01 to 2026-08), 3.1 has more rows: 4.01B vs 3.01B | Patient-treatment features, for example `TOTAL_RX_CLAIMS_PATIENT_WITH_NO_NEW_TREATMENT_IN_LAST_3_MONTH`, `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_2_OR_3_ACTIVE_TREATMENTS` [S8]; model features in this family change by 0.94 per HCP (median, section 7) |
| New CKD stage | NB03 | 4.50B → 4.12B | Same months as above | "Patients new to a stage" features rise 1.32× per HCP, because stage 3 and 5 are now recognised |
| Stage × treatment (GFR / diagnosis) | NB04 | 4.50B → 4.12B | Same months as above | Claims move between stages (table below): stage 4 down, stage 1–3 up. The DPP-IV and other glucose columns are gone (X5) |
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

---

## 5. What we have in 3.1: notebook by notebook

All counts and names from S1 and S2 (feature columns, without ID and date columns).

| Notebook | 3.0 | 3.1 | Kept | New | Not built |
| --- | ---: | ---: | ---: | ---: | ---: |
| NB01 Rx claims | 5,411 | 4,668 | 4,432 | 236 | 979 |
| NB02 Lab claims | 116 | 143 | 95 | 48 | 21 |
| NB03 Diagnosis claims | 127 | 113 | 104 | 9 | 23 |
| NB04 Combined claims | 3,691 | 3,065 | 2,840 | 225 | 851 |
| NB05 New patient starts | 188 | 154 | 154 | 0 | 34 |
| NB06 Eligible patients | 84 | 217 | 69 | 148 | 15 |
| **Total** | **9,617** | **8,360** | **7,694** | **666** | **1,923** |

**The 666 new features**

| Notebook | New features | Count | Example names | Why new |
| --- | --- | ---: | --- | --- |
| NB01 | Kerendia prescriptions by window, payer, days supply, refill, age, gender, rejections, running totals | 234 | `TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_3_MONTH`, `TOTAL_RX_CLAIMS_KERENDIA_COMMERCIAL_IN_LAST_1_MONTH`, `PCT_TOTAL_REJECTED_RX_CLAIMS_KERENDIA_IN_LAST_3_MONTH`, `RUNNING_TOTAL_RX_CLAIMS_KERENDIA` | Kerendia is a new category and brand |
| NB01 | SGLT2 without Invokana 300 mg, running totals | 2 | `RUNNING_TOTAL_RX_CLAIMS_SGLT2_WO_INVOKANA_300MG_DAYS_SUPPLY_UNKNOWN` | These values have claims in the 3.1 data; NB01 builds a column for each value it finds |
| NB02 | Potassium: patients tested, above 5.0 mmol/L, % flagged; all and eligible patients; 4 windows | 24 | `TOTAL_PATIENTS_POTASSIUM_TESTED_IN_LAST_1_MONTH`, `TOTAL_PATIENTS_POTASSIUM_GT_5_IN_LAST_3_MONTH`, `PCT_ELIGIBLE_PATIENTS_POTASSIUM_GT_5_IN_LAST_12_MONTH` | New signal: the label advises against starting Kerendia above 5.0 |
| NB02 | HbA1c: same, at 9% or higher | 24 | `TOTAL_ELIGIBLE_PATIENTS_HBA1C_GE_9_IN_LAST_6_MONTH`, `PCT_ELIGIBLE_PATIENTS_HBA1C_GE_9_IN_LAST_12_MONTH` | New signal: uncontrolled diabetes |
| NB03 | CKD stage 5 diagnosis claims: 4 windows, % and running total | 9 | `TOTAL_DX_CLAIMS_STAGE_5_IN_LAST_3_MONTH`, `PCT_TOTAL_DX_CLAIMS_STAGE_5_IN_LAST_12_MONTH`, `RUNNING_TOTAL_DX_CLAIMS_STAGE_5` | Stage 5 codes now read |
| NB04 | Kerendia by the patient's CKD stage | 180 | `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_3_WITH_KERENDIA_IN_LAST_6_MONTH`, `PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_5_WITH_KERENDIA_IN_LAST_12_MONTH` | Kerendia is a new treatment |
| NB04 | UACR test stage × Invokana 100 / 300 mg | 45 | `TOTAL_RX_CLAIMS_PATIENT_WITH_TEST_UACR_STAGE_1_WITH_INVOKANA_300MG_IN_LAST_3_MONTH` | The 3.1 lab data has UACR tests (section 4.4), so these combinations now have claims |
| NB06 | Patients by diabetes type (type 2, type 1, other, none); all and eligible; % shares | 64 | `TOTAL_RX_PATIENTS_DM_TYPE_T2D_IN_LAST_3_MONTH`, `PCT_ELIGIBLE_PATIENTS_DM_TYPE_T2D_IN_LAST_12_MONTH` | Kerendia's CKD indication requires type 2 diabetes |
| NB06 | Patients by heart-failure type (preserved-EF proxy, reduced-EF proxy, mixed, unknown) | 64 | `TOTAL_ELIGIBLE_PATIENTS_HF_TYPE_HFREF_PROXY_IN_LAST_6_MONTH`, `PCT_ELIGIBLE_PATIENTS_HF_TYPE_HFPEF_PROXY_IN_LAST_12_MONTH` | Kerendia's heart-failure indication (LVEF 40% or more) |
| NB06 | Patients with any heart failure | 16 | `TOTAL_RX_PATIENTS_HF_IN_LAST_12_MONTH`, `PCT_ELIGIBLE_PATIENTS_HF_IN_LAST_12_MONTH` | Same |
| NB06 | Treated patients (denominator) | 4 | `TOTAL_RX_PATIENTS_IN_LAST_1_MONTH` | Base for the % shares |
| **Total** | | **666** | | |

**How the kept features change, per notebook**

| Notebook | Kept | What changes in the values | Why |
| --- | ---: | --- | --- |
| NB01 | 4,432 | GLP-1 brand about 2×; SGLT2 +15%; per-HCP values of the other categories lower | New drugs; added HCPs with fewer claims (section 4.2) |
| NB02 | 95 | About twice as many tests | 3.1 lab data (section 4.4) |
| NB03 | 104 | Stage 3 claims counted; missing stage stays unknown | Stage from the code |
| NB04 | 2,840 | Stage 4 down, stages 1–3 up, GLP-1 by stage up to 20× | New stage rules (section 4.5) and new GLP-1 drugs |
| NB05 | 154 | Unchanged | Still reads the 3.0 input `kerendia_nba_3_0_Rx_05` [S3] (open point 12) |
| NB06 | 69 | Eligible patients lower | Stage 1 and 5 months not eligible (section 4.5) |

---

## 6. What is no longer built, and why

**Repeated monthly columns (1,703).** 3.0 stored each monthly value twice: as a plain monthly column (for example `PCT_TOTAL_RX_CLAIMS_DPP_IV`) and as "last 1 month" (`PCT_TOTAL_RX_CLAIMS_DPP_IV_IN_LAST_1_MONTH`). We compared both on all rows of each 3.0 table (7.4M rows for NB02, 13.0M–13.6M for the others) [S1, my check]:

| Notebook | Plain monthly columns | Same values as "last 1 month" | Different | Example dropped columns |
| --- | ---: | ---: | ---: | --- |
| NB01 Rx claims | 979 | 975 | 4 | `PCT_TOTAL_REJECTED_RX_CLAIMS_ACE_OR_ARB`, `PCT_TOTAL_RX_CLAIMS_DPP_IV`, `AVG_PATIENT_AGE` |
| NB02 Lab claims | 21 | 21 | 0 | `PCT_TOTAL_LAB_CLAIMS_A1`, `PCT_TOTAL_LAB_CLAIMS_A2` |
| NB03 Diagnosis claims | 23 | 23 | 0 | `PCT_TOTAL_DX_CLAIMS_STAGE_1`, `PCT_TOTAL_DX_CLAIMS_STAGE_3` |
| NB04 Combined claims | 631 | 631 | 0 | `PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_1_WITH_ACE_OR_ARB` |
| NB05 New patient starts | 34 | 34 | 0 | `PCT_TOTAL_PATIENTS_START_ACE_OR_ARB`, `TOTAL_PATIENTS_START_DPP_IV` |
| NB06 Eligible patients | 15 | 0 | 15 | `PCT_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_3` |
| **Total** | **1,703** | **1,684** | **19** | |

The six categories without brands (ACE/ARB, calcium channel / beta blocker, combo drug, diuretic non-MRA, insulin, metformin) are still fully built; only their plain monthly copies (322 of the 979 in NB01) are gone.

**The 19 columns that need a decision** (open point 1)

| Notebook | Columns | Why they are not exact repeats |
| --- | --- | --- |
| NB01 | 4: `AVG_PATIENT_AGE`, `AVG_TREATMENT_PER_PATIENT`, patient count, treatment count | In 3.0 the averages cover one extra month, and 3.1 keeps that rule, so the value for the month alone is not in 3.1 |
| NB06 | 15: eligible patients in total, by GFR / diagnosis stage and by UACR stage, and their % shares, for example `PCT_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_3` | 3.0 NB06 look-backs were averages over one extra month; 3.1 counts the month itself (decision X8 [S12]). The 3.1 "last 1 month" column holds the month alone; it has not been checked against these 15 |

**Decision X5 (NB04, 220 columns)**

| What | Detail | Source |
| --- | --- | --- |
| Columns | Claims by the patient's CKD stage for DPP-IV and other glucose drugs: 66 GFR / Dx stage × DPP-IV, 66 GFR / Dx stage × other glucose mgmt, 44 UACR stage × DPP-IV, 44 UACR stage × other glucose mgmt. The 220 include 40 plain monthly copies. Claims by the stage of a same-day lab test for these drugs are still built (180 columns, for example `TOTAL_RX_CLAIMS_PATIENT_WITH_TEST_GFR_STAGE_1_WITH_DPP_IV_IN_LAST_6_MONTH`), because they come from the Rx claims, not the patient table | S1, S2 |
| Why they cannot be built | NB04 takes the patient's treatments from the patient table. In 3.1 that table has no "Other- glucose mgmt" or "DPP-IV" (August 2026, 3.0: 8.47M and 0.98M patient-months). The Rx basket keeps these drugs off for the patient journey (Januvia, Tradjenta, glipizide, pioglitazone: `ACTIVE_JOURNEY = N`), and the GLP-1 drugs, which were part of "Other glucose mgmt" in 3.0, now have their own category "GLP-1" | S3, S5, S6, my check |
| Why we accepted it | Switching these drugs on only for the HCP features would make the HCP patient tables differ from the patient journey used everywhere else | S12 (X5) |
| Effect on the model | 9 of the 277 model features are among them (list below) | S8 |
| How to reverse | Switch the drugs on in the Rx basket and rerun PJ03, PJ06 and NB04 (open point 5) | S12 |

The 9 model features: `PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_UNKNOWN_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_1_MONTH`, `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_4_WITH_OTHER_GLUCOSE_MGMT`, `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_UACR_STAGE_3_WITH_OTHER_GLUCOSE_MGMT`, `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_4_WITH_DPP_IV_IN_LAST_12_MONTH`, `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_4_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_12_MONTH`, `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_4_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_6_MONTH`, `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_UACR_STAGE_3_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_6_MONTH`, `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_UACR_STAGE_UNKNOWN_WITH_DPP_IV_IN_LAST_3_MONTH`, `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_UACR_STAGE_UNKNOWN_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_1_MONTH` [S8, S2].

---

## 7. What this means for the model

### 7.1 Will 3.1 use the same features as 3.0?

No. The 752 features were chosen for the 3.0 model. For 3.1 the model is retrained and feature selection runs again on all 3.1 features: the 8,360 claims features, including the 666 new ones, plus the other sources [S12, X5]. The selection decides which new features are used. It can only run once the step that joins all HCP features is switched to cohorts (open point 9); no date is set yet.

The number 268 is therefore only a check: of the 277 claims features in the 3.0 model, 268 still exist in 3.1 under the same name. It does not mean 3.1 will use them.

### 7.2 How much do the 268 features change?

For each feature we took the average per HCP in August 2026 (3.0: month 2026-08; 3.1: cohort c28) and divided 3.1 by 3.0. 1.00 = no change; 0.80 = 20% lower [S1, S2, S8, my check].

| Notebook | Model features in 3.1 | Similar (±20%) | Lower | Higher | Typical change | Main reason |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| NB01 Rx claims | 172 | 114 | 54 | 4 | 0.82–0.95 by family (SGLT2 without Invokana 300 mg: 1.04) | Added HCPs with fewer claims (section 4.2); running totals start later |
| NB03 Diagnosis claims | 3 | 1 | 0 | 2 | 0.83 and 1.32 | Stage 3 and 5 now recognised |
| NB04 Combined claims | 78 (9 missing, X5) | 7 | 38 | 33 | 0.46 (stage) to 0.80 (stage × treatment) | New stage mix (section 4.5); new GLP-1 drugs |
| NB05 New patient starts | 14 | 13 | 1 | 0 | 1.00 | Same 3.0 input |
| NB06 Eligible patients | 1 | 0 | 1 | 0 | 0.43 | Fewer eligible stage 4 patient-months (1.98M → 1.20M, August 2026) |
| **Total** | **268** | **135** | **94** | **39** | | |

NB01 includes the 2 features shared with NB04.

**By window** [S8, my check]

| Window | Features | Similar | Lower | Higher | Median | Why |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Running total | 69 | 2 | 58 | 9 | 0.65 | 3.1 counts from 2023-01, 3.0 from 2021-01: 44 vs 68 months in August 2026 (44 / 68 = 0.65) |
| 12 months | 66 | 47 | 7 | 12 | 0.91 | Added HCPs |
| 6 months | 52 | 33 | 11 | 8 | 0.90 | Same |
| 3 months | 47 | 29 | 11 | 7 | 0.90 | Same |
| 1 month | 33 | 23 | 7 | 3 | 0.88 | Same |
| Ratio | 1 | 1 | 0 | 0 | 0.95 | Same |

**Examples of the largest changes** [S8, my check]

| Feature | Change | Why |
| --- | ---: | --- |
| `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_1_WITH_GLP_1_IN_LAST_6_MONTH` | 19.9× | 13× more stage 1 patient-months and twice the GLP-1 claims |
| `TOTAL_DX_CLAIMS_WITH_PATIENT_NO_NEW_STAGE_IN_LAST_6_MONTH` | 1.32× | Stage 3 and 5 claims now counted |
| `PCT_TOTAL_RX_CLAIMS_MEDICARE_IN_LAST_12_MONTH` | 1.72× | Not checked yet |
| `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_GFR_STAGE_4_AND_UACR_STAGE_UNKNOWN` | 0.33 | Fewer stage 4 patients; running total starts later |
| `RUNNING_TOTAL_RX_CLAIMS_METFORMIN_MGD_MEDICAID` | 0.49 | Running total starts later; added HCPs |
| `RUNNING_TOTAL_PATIENTS_START_SGLT2` | 0.63 | Running total starts later |
| `RUNNING_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_4` | 0.43 | Fewer eligible stage 4 patient-months |

---

## 8. Run status

Run 441950237921 finished with SUCCESS: all 13 tasks, all 28 cohorts [S14]. From the first patient-journey task to the end of NB04: 4 h 40 min; 17 h 40 min in total, including the NB07 retries.

| Task | Runtime (min) | Task | Runtime (min) |
| --- | ---: | --- | ---: |
| PJ01 Labs | 14.6 | NB01 Rx claims | 151.9 |
| PJ02 Diagnosis | 13.5 | NB02 Lab claims | 31.6 |
| PJ03 Rx | 37.1 | NB03 Diagnosis claims | 146.2 |
| PJ04 Diabetes / heart failure | 5.9 | NB04 Combined claims | 221.2 |
| PJ05 Procedures | 1.3 | NB05 New patient starts | 148.6 |
| PJ06 Combine | 15.5 | NB06 Eligible patients | 146.5 |
| | | NB07 Cohort-set check | 3.0 (attempt 5) |

| Output [S2] | Rows | Columns (incl. 9 ID and date columns) |
| --- | ---: | ---: |
| NB01 Rx claims | 8.09M | 4,677 |
| NB02 Lab claims | 5.17M | 152 |
| NB03 Diagnosis claims | 7.59M | 122 |
| NB04 Combined claims | 8.09M | 3,074 |
| NB05 New patient starts | 6.45M | 163 |
| NB06 Eligible patients | 8.09M | 226 |

All outputs together: 231 GB. NB07 checks that every output has the 28 cohorts in the right training, validation and back-testing groups, without duplicate rows. Attempts 1–4 stopped on rows without a provider ID (open point 8); attempt 5 passed.

---

## 9. Open points

| # | Point | Who decides | Rerun needed |
| --- | --- | --- | --- |
| 1 | 19 monthly columns not in 3.1 | Wenjie | NB01, NB06 if restored |
| 2 | GLP-1 has no category feature of its own | Wenjie | NB01, NB04 if added |
| 3 | New drugs have no features of their own | Wenjie | NB01, NB04 if added |
| 4 | Two copies of the product basket | Team | No |
| 5 | DPP-IV and other glucose drugs off in the patient journey (X5) | Wenjie, product mapping | PJ03, PJ06, NB04 if switched on |
| 6 | Eligibility rules C1 (SGLT2) and C9 (diabetes) | NBA team | PJ06, NB01–NB06 |
| 7 | Retraining and feature selection | Raman | Model only |
| 8 | Rows without a provider ID | Team | NB01–NB06 provider tables |
| 9 | Combine step not switched to cohorts | Team | Combine step |
| 10 | Running totals start in 2023 | Wenjie | All if changed |
| 11 | Near-duplicate SGLT2 features | Wenjie, Raman | No (selection) |
| 12 | NB05 still reads the 3.0 input | Team | NB05 |
| 13 | Type 1 diabetes kidney codes in NB03 | Wenjie | NB03 if removed |
| 14 | More patient rows per month in 3.1, not yet explained | Team (check) | No |
| 15 | Clean-up and defaults | Team | No |

**1. 19 monthly columns are not in 3.1.** What is going on: 4 NB01 averages and counts and 15 NB06 eligibility columns held values for the month alone that 3.1 does not store (section 6). Options: (a) accept, because 3.1 keeps the look-back versions, for example `TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_3_IN_LAST_1_MONTH`; (b) restore them as extra columns. None of them is in the 752 [S7, my check]. Recommendation: (a).

**2. GLP-1 has no category feature of its own.** What is going on: by option C, GLP-1 drugs count under "Other glucose mgmt" and under the GLP-1 brand, as in 3.0 (section 4.3). GLP-1 claims doubled (186.4M → 376.0M), so "Other glucose mgmt" is now 71% GLP-1 (375.7M of 531.7M) [S4]. Options: (a) keep; (b) a separate GLP-1 category, which needs a new name to avoid the clash with the brand columns. Effect of (b): a new set of category columns in NB01 and NB04; other categories have 236–245 NB01 columns each [S2].

**3. The new drugs have no features of their own.** What is going on: Mounjaro (124.1M claims), Zepbound (29.0M), Wegovy (25.8M) sit inside the GLP-1 brand, generic dapagliflozin (16.2M) inside SGLT2 [S4]. The model cannot tell them apart. Options: (a) keep; (b) add some of them to the brand list; today's brands have 252–263 NB01 columns each (brand table in section 4.3).

**4. Two copies of the product basket.** What is going on: the run reads the volume folder [S6]. The workspace folder `Final Product Basket` holds the version before the 2026-11-05 update (16 Rx products and J0606 switched off). If someone uses the workspace copy, Kerendia and the new GLP-1 drugs drop out. Action: update or clearly label the workspace copy.

**5. DPP-IV and other glucose drugs are off in the patient journey (X5).** What is going on: section 6. 3.0 tracked them per patient (0.98M DPP-IV patient-months in August 2026 [S3]); 3.1 does not, so 220 NB04 columns and 9 model features are gone. Options: (a) accept; (b) switch them on in the Rx basket for the journey. Effect of (b): rerun PJ03, PJ06 and NB04; the patient journey also changes (treatment counts per patient).

**6. Eligibility rules C1 and C9 (patient journey).** What is going on: the SGLT2 rule (C1) is meant to exclude patients with unknown stage who never had an SGLT2, but it compares the stage with -1 and never applies, in 3.0 and in 3.1 [S10, PJ06 combine]. Fixing it makes 56% of the eligible months not eligible. C9: 58% of eligible months have no type 1 or type 2 diabetes diagnosis [S10]. Effect of a change: eligibility and all patient-based features in NB01, NB03, NB04 and NB06 change; rerun PJ06 and the HCP job (no code change in the HCP notebooks).

**7. Retraining and feature selection.** What is going on: 133 of the 268 model features move by more than 20% per HCP (section 7), and 666 new features are available. The 3.0 model cannot be applied to 3.1 as it is. Action: run feature selection and training on 3.1 after point 9.

**8. Rows without a provider ID.** What is going on: the provider tables have 3,094 rows without a provider ID (NB01, NB04), 949 (NB03) and 3,001 (NB06), because the NPI-to-provider mapping misses 105 HCPs and gives 2 IDs to 52 [S2, mapping `query_output/kerendia_nba_3_0_npi_bhid_mapping`]. The NPI tables are complete. Proposal: keep the mapping, fill or de-duplicate these 157 HCPs from the provider ID in the 3.1 Rx input, before the combine step.

**9. Combine step not switched to cohorts.** What is going on: the step that joins all HCP features for the model (`99_Combine_Physician_Data`) joins by calendar month; 3.1 delivers the claims features by cohort. Other HCP feature notebooks (promotion and others) still use the 3.0 logic. Action: join on provider and cohort; plan in `99 Combine Physician Data Files/NBA_3_1_Combine_Physician_Data_Plan.md`.

**10. Running totals start in 2023.** What is going on: 3.1 counts from 2023-01-01, 3.0 from 2021 (section 3.1), so running totals are about a third lower (median 0.65, section 7). 69 of the 268 model features are running totals [S8]. Options: (a) keep 2023; (b) pull data from 2021, which makes every pull larger.

**11. Near-duplicate SGLT2 features.** What is going on: 155 "SGLT2 without Invokana 300 mg" columns in 3.1 (187 in 3.0) [S1, S2], for example `RUNNING_TOTAL_RX_CLAIMS_SGLT2_WO_INVOKANA_300MG`, are almost equal to the SGLT2 columns (correlation about 1.0), because Invokana 300 mg has 1.13M of the 165.2M SGLT2 claims [S4]. Options: drop them before selection, or let selection handle them.

**12. NB05 still reads the 3.0 input.** What is going on: a "new start" needs each patient's claims since 2021, which the 3.1 Rx pull (from 2023) does not have, so NB05 reads `kerendia_nba_3_0_Rx_05` [S3]. Starts on Kerendia, Mounjaro, Zepbound or Wegovy are not counted. Also, months without claims are 0 in 3.1 and empty in 3.0. Options: a 3.1 input with history from 2021 for these drugs; confirm 0 for empty months.

**13. Type 1 diabetes kidney codes in NB03.** What is going on: 1.39M rows with type 1 diabetes kidney codes count as CKD diagnosis claims with unspecified stage [`hcp_level_features/03 Diagnosis Claims Files/NBA_3_1_Dx_Claims_Features_Plan.md`]. Options: keep (CKD with type 1 diabetes is still CKD) or remove (if the features should follow the type 2 indication).

**14. More patient rows per month in 3.1.** What is going on: August 2026 has 113.2M patient rows in 3.1 against 72.2M in 3.0 [S3, S5]. We have not split the difference by source yet (more lab patients, new drugs, months counted from the first diagnosis). Action: check, because it drives the patient-based features.

**15. Clean-up and defaults.** What is going on: the settings still point the "latest run" to an older run and fall back to the 3.0 HCP universe when none is given; older run outputs take a lot of space [S15]. Action: point to `full_2026_11_11`, default to the 3.1 universe, remove old run outputs.


