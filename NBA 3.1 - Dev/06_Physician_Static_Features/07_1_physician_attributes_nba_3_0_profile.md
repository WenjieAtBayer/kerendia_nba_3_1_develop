# Analysis: HCP Physician Attributes (nb 07_phy_static_features)

NBA 3.0 profile of the physician static feature family. For NBA 3.1 readiness, see `07_2_physician_attributes_data_assessment.md` in this folder. Section 8 lists the points in this profile that the 3.1 checks have since settled or corrected.

## 1. Notebook Overview
This notebook creates physician static (demographic and professional) features for the Kerendia NBA 3.0 HCP-level NBRx model. It pulls HCP profile, specialty and affiliation data from PHCDW source tables, cleans and transforms them, and saves one row per HCP for inference.

## 2. Data Sources Used

| Source | Table | Purpose |
| --- | --- | --- |
| PHCDW (Snowflake) | `PHCDW_STG_CAR.STG_IQVIA_LAAD_DIM_PROVIDER` | Provider specialty code, organization name |
| PHCDW (Snowflake) | `PHCDW_STG.MDM_STG_HCP_PRFL` | HCP profile: degree, birth / grad year, gender, education, opt-out flags |
| PHCDW (Snowflake) | `PHCDW_STG.MDM_STG_HCP_ACCT_AFFL` | Account affiliations: teaching hospital, dialysis center, long-term care, etc. |
| Databricks Volume | `kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` | HCP universe (234,405 HCPs) |
| Databricks Catalog | `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING` | PROVIDER_ID to NPI / BH_ID mapping |

## 3. Data Source Column Usage

**Method.** Total column counts come from UC copies of the Snowflake tables (`kerendia_nba_3.stg_car_iqv_laad_dim_prvdr`; `pace_ker_in_house_schema.mdm_stg_hcp_prfl`). Fill rates are on the full source table, not restricted to the universe. MDM_STG_HCP_ACCT_AFFL has no UC copy (confirmed, Section 8), so its fill rates come from the 2026-11-12 Snowflake check on the NBA 3.0 universe.

### 3.1 Summary

| Source | Table | Total Columns | Columns Used | Usage Rate |
| --- | --- | --- | --- | --- |
| PHCDW (Snowflake) | `STG_IQVIA_LAAD_DIM_PROVIDER` | 30 | 4 | 13.3% |
| PHCDW (Snowflake) | `MDM_STG_HCP_PRFL` | 83 | 27 | 32.5% |
| PHCDW (Snowflake) | `MDM_STG_HCP_ACCT_AFFL` | 10+ (no UC copy to count) | 4 | - |
| Databricks (UC) | `SOURCE_PROVIDER_BHID_NPI_MAPPING` | 3 | 3 | 100% |
| Databricks (Volume) | HCP universe | 1 | 1 | 100% |

### 3.2 STG_IQVIA_LAAD_DIM_PROVIDER (30 columns, 4 used)

| Column | Fill Rate | Used For |
| --- | --- | --- |
| PROVIDER_ID | 100% | Join key |
| NPI_NUMBER | 96.2% | Join to PRFL |
| PRIMARY_SPECIALTY_CODE | 91.9% | Feature (raw categorical, not in 752) |
| ORG_NM | 8.1% | Feature (filled for 19 universe HCPs in the output) |

### 3.3 MDM_STG_HCP_PRFL (83 columns, 27 used)

Latest row per NPI: `ROW_NUMBER() OVER (PARTITION BY NPI_NUM ORDER BY CREATED_DATE desc)`.

| Column | Fill Rate (source) | Used For |
| --- | --- | --- |
| NPI_NUM | 82.2% | Join key + partition |
| CREATED_DATE | 100% | Ordering (latest row per NPI) |
| MEDICAL_DEGREE_1 | 90.8% | Feature (raw) |
| RECORD_STATE | 100% | Feature (raw) |
| HCP_STATUS | 100% | Feature (raw) |
| HCP_TYPE | 100% | Pulled, then dropped (99.5% = 'P') |
| SPECIALTY_1 | 95.8% | Pulled, then dropped |
| SPECIALTY_2 | 21.7% | Pulled, then dropped |
| KAISER | 83.4% | Feature (binary flag) |
| PDRP_OPTOUT | 52.4% | Feature (binary flag) |
| AMA_DO_NOT_CONTACT | 53.5% | Feature (binary flag) |
| BIRTH_YEAR | 11.1% | Feature, becomes AGE (85% null at HCP level) |
| BOARD_CERTIFICATION | 0.0% | Pulled, then dropped (empty) |
| CANDIDATE_RECORD | 100% | Feature (binary flag, constant 0 in output) |
| EDUCATION_LEVEL | 20.8% | Feature (raw) |
| FELLOW | 53.3% | Feature (binary flag) |
| GENDER | 89.4% | Feature (raw) |
| GRAD_TRAINING | 53.3% | Feature (binary flag) |
| GRAD_TRG_END_DATE | 23.3% | Pulled, then dropped |
| GRAD_TRG_START_DATE | 22.4% | Feature, becomes GRAD_TRG_START_YEARS |
| GRAD_YEAR | 24.5% | Feature, becomes HCP_EXPERIENCE |
| IS_EXTERNALLY_MASTERED | 100% | Feature (binary flag, constant 0 in output) |
| IS_VEEVA_MASTER | 100% | Feature (binary flag, 99.6% = 1) |
| MPA | 100% | Pulled, then dropped |
| PLACE_OF_EMPLOYMENT | 24.2% | Pulled, then dropped |
| TYPE_OF_PRACTICE | 24.2% | Pulled, then dropped |
| YEARS_IN_PROGRESS | 21.9% | Pulled, then dropped |
| PRIMARY_SPECIALTY_GROUP | 90.7% | Pulled, then dropped (duplicates nb 20 specialty) |

56 of 83 columns (67.5%) are not used. Ten pulled columns (HCP_TYPE, SPECIALTY_1, SPECIALTY_2, BOARD_CERTIFICATION, MPA, PLACE_OF_EMPLOYMENT, TYPE_OF_PRACTICE, YEARS_IN_PROGRESS, PRIMARY_SPECIALTY_GROUP, GRAD_TRG_END_DATE) are dropped before the output.

### 3.4 MDM_STG_HCP_ACCT_AFFL (Snowflake only)

Known columns: BH_ID, ACCT_NAME, MAJOR_CLASS_OF_TRADE, DESCRIPTION, SPECIALTY, BHO_ID, IS_PRIMARY_RELATIONSHIP__V, HCO_TYPE, START_DATE, END_DATE. Fill rates from the 2026-11-12 Snowflake check on the 3.0 universe.

| Column | Fill Rate | Used For |
| --- | --- | --- |
| BH_ID | - | Join key |
| ACCT_NAME | 99.5% | Input to AFFL_COUNT (not saved as a feature) |
| MAJOR_CLASS_OF_TRADE | 100% | Input to DIALYSIS_CENTER_FLAG |
| DESCRIPTION | 100% | Input to TEACHING_HOSP_FLAG, LONG_TERM_CARE_FACIL_FLAG |

### 3.5 SOURCE_PROVIDER_BHID_NPI_MAPPING (3 columns, 3 used)

| Column | Fill Rate | Used For |
| --- | --- | --- |
| PROVIDER_ID | 100% | Join key |
| NPI_NUMBER | 94.9% | Join to PRFL |
| BH_ID | 100% | Join to ACCT_AFFL |

## 4. Features Created

### 4.1 Provider dimension (STG_IQVIA_LAAD_DIM_PROVIDER)
* **PRIMARY_SPECIALTY_CODE**: primary specialty code
* **ORG_NM**: organization name

### 4.2 HCP profile (MDM_STG_HCP_PRFL, latest row per NPI)
* **MEDICAL_DEGREE_1, RECORD_STATE, HCP_STATUS, EDUCATION_LEVEL, GENDER**: raw strings
* **BIRTH_YEAR** (becomes AGE), **GRAD_YEAR** (becomes HCP_EXPERIENCE), **GRAD_TRG_START_DATE** (becomes GRAD_TRG_START_YEARS)
* Binary flags (Y / true = 1): **KAISER, PDRP_OPTOUT, AMA_DO_NOT_CONTACT, CANDIDATE_RECORD, FELLOW, GRAD_TRAINING, IS_EXTERNALLY_MASTERED, IS_VEEVA_MASTER**

### 4.3 Affiliation (MDM_STG_HCP_ACCT_AFFL)
* **TEACHING_HOSP_FLAG** = 1 if any DESCRIPTION = 'Organization, CMS Teaching Hospital'
* **DIALYSIS_CENTER_FLAG** = 1 if any MAJOR_CLASS_OF_TRADE = 'Dialysis & Infusion Centers'
* **LONG_TERM_CARE_FACIL_FLAG** = 1 if any DESCRIPTION = 'Organization, Nursing Home or Long Term Care'
* **AFFL_COUNT** = `count(*)` over distinct (BH_ID, ACCT_NAME, MAJOR_CLASS_OF_TRADE, DESCRIPTION)

### 4.4 Derived numeric
`currentYear = datetime.now().year`, which was **2026** at the last 3.0 run (Section 8):
* **AGE** = currentYear - YEAR(BIRTH_YEAR); NULL if BIRTH_YEAR = '1900-01-01' or NULL
* **GRAD_TRG_START_YEARS** = currentYear - YEAR(GRAD_TRG_START_DATE)
* **HCP_EXPERIENCE** = currentYear - GRAD_YEAR

## 5. Business Rules and Output
1. Latest PRFL row per NPI by CREATED_DATE.
2. Y / true flags mapped to 1, everything else to 0.
3. Affiliation arrays (ACCT_NAME, MAJOR_CLASS_OF_TRADE, DESCRIPTION) are collected per BH_ID and kept in the output.
4. All blocks left-joined to the universe on PROVIDER_ID.

Output: `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_phy_static_features_for_inference`. Checked 2026-11-18: **234,405 rows, one per PROVIDER_ID, 25 columns**, PULL_DT 2026_10_26.

## 6. NBA 3.0 Feature Profile (HCP counts, nulls, distribution)

**Method.** Profiled on 2026-11-17 from the 3.0 ops output above, left-joined to the NBA 3.0 universe (**234,405 HCPs**), as `99_Combine_Physician_Data` does. The features are static, so the percentages are the same in every cohort.

* Every universe HCP has a row.
* 225,786 HCPs have a non-empty DESCRIPTION array. The 8,495 HCPs (3.6%) with no MDM affiliation get NULL for every affiliation feature.
* "HCPs with value" = non-null. % = share of 234,405. For 0/1 flags, "= 1" counts HCPs flagged 1.

### 6.1 Numeric and flag features

| Feature | In 752? | HCPs with value | % | Null HCPs | Null % | Distinct | HCPs = 0 | HCPs = 1 / non-zero | Min | P25 | Median | Mean | P75 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AFFL_COUNT | Yes | 225,910 | 96.4% | 8,495 | 3.6% | 31 | 0 | 225,910 (96.4%) | 1 | 2 | 3 | 3.74 | 5 | 43 |
| TEACHING_HOSP_FLAG | Yes | 225,910 | 96.4% | 8,495 | 3.6% | 2 | 119,349 (50.9%) | 106,561 (45.5%) | 0 | 0 | 0 | 0.47 | 1 | 1 |
| DIALYSIS_CENTER_FLAG | Yes | 225,910 | 96.4% | 8,495 | 3.6% | 2 | 217,391 (92.7%) | 8,519 (3.6%) | 0 | 0 | 0 | 0.04 | 0 | 1 |
| LONG_TERM_CARE_FACIL_FLAG | Yes | 225,910 | 96.4% | 8,495 | 3.6% | 2 | 215,263 (91.8%) | 10,647 (4.5%) | 0 | 0 | 0 | 0.05 | 0 | 1 |
| HCP_EXPERIENCE | Yes | 188,006 | 80.2% | 46,399 | 19.8% | 73 | 6 | 188,000 (80.2%) | **-7** | 10 | 19 | 21.29 | 31 | 72 |
| AGE (HCP_AGE) | Yes | 35,211 | **15.0%** | 199,194 | **85.0%** | 73 | 0 | 35,211 (15.0%) | 20 | 41 | 49 | 50.36 | 58 | 97 |
| GRAD_TRG_START_YEARS | No | 127,857 | 54.5% | 106,548 | 45.5% | 16 | 156 | 127,701 (54.5%) | 0 | 56 | 56 | 55.85 | 56 | 56 |
| GRAD_TRAINING | No | 234,405 | 100% | 0 | 0% | 2 | 114,902 (49.0%) | 119,503 (51.0%) | 0 | 0 | 1 | 0.51 | 1 | 1 |
| PDRP_OPTOUT | No | 234,405 | 100% | 0 | 0% | 2 | 229,122 (97.7%) | 5,283 (2.3%) | 0 | 0 | 0 | 0.02 | 0 | 1 |
| AMA_DO_NOT_CONTACT | No | 234,405 | 100% | 0 | 0% | 2 | 230,705 (98.4%) | 3,700 (1.6%) | 0 | 0 | 0 | 0.02 | 0 | 1 |
| KAISER | No | 234,405 | 100% | 0 | 0% | 2 | 233,827 (99.8%) | 578 (0.2%) | 0 | 0 | 0 | 0.00 | 0 | 1 |
| FELLOW | No | 234,405 | 100% | 0 | 0% | 2 | 233,910 (99.8%) | 495 (0.2%) | 0 | 0 | 0 | 0.00 | 0 | 1 |
| IS_VEEVA_MASTER | No | 234,405 | 100% | 0 | 0% | 2 | 903 (0.4%) | 233,502 (99.6%) | 0 | 1 | 1 | 1.00 | 1 | 1 |
| CANDIDATE_RECORD | No | 234,405 | 100% | 0 | 0% | **1** | 234,405 (100%) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| IS_EXTERNALLY_MASTERED | No | 234,405 | 100% | 0 | 0% | **1** | 234,405 (100%) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Percentiles are approximate (Spark `percentile_approx`). The 8,495 nulls of the three affiliation flags are the HCPs with no affiliation record (the same HCPs as AFFL_COUNT).

### 6.2 Categorical / text columns

| Column | In 752? | HCPs with value | % | Null HCPs | Null % | Distinct | Value counts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GENDER | No | 233,476 | 99.6% | 929 | 0.4% | 3 | F 122,702 (52.3%), M 95,292 (40.7%), U 15,482 (6.6%) |
| EDUCATION_LEVEL | No | 125,027 | 53.3% | 109,378 | 46.7% | 3 | RESIDENCY 109,780, MEDSCH 10,096, FELLOW 5,151 |
| ORG_NM | No | 19 | 0.0% | 234,386 | 100.0% | 19 | Effectively empty |
| MAJOR_CLASS_OF_TRADE, ACCT_NAME, DESCRIPTION | No (arrays) | 225,786 non-empty | 96.3% | - | - | - | Inputs to the flags |

### 6.3 Data-quality findings
* **AGE is 85% null.** Only 35,211 HCPs have a usable BIRTH_YEAR, which fits its low SHAP (rank 263).
* **HCP_EXPERIENCE has negative values** (min -7) because GRAD_YEAR contains future years. 19.8% of HCPs are null.
* **GRAD_TRG_START_YEARS is a placeholder.** 127,506 of its 127,857 non-null values are 56 = 2026 - 1970. The most common GRAD_TRG_START_DATE in PRFL is 1970-01-01 (1,179,664 source rows), followed by 1970-03-23 (128,992). The feature carries almost no information.
* **Two flags are constant** (CANDIDATE_RECORD, IS_EXTERNALLY_MASTERED), and IS_VEEVA_MASTER is 1 for 99.6% of HCPs.
* **ORG_NM is filled for 19 HCPs**, so it is unusable.
* The 3.6% of HCPs with no affiliation get NULL (not 0) for AFFL_COUNT and the three flags. LightGBM routes them as missing, which is a different branch from HCPs with zero teaching or dialysis affiliations.

## 7. Features in the 752 Final NBA 3.0 Modeling Features

Cross-referenced with the Final NBA 3.0 Modeling Features Excel (752 features, Mean_Abs_SHAP). Category: HCP Demo.

| Feature | Mean_Abs_SHAP | Share of total SHAP | Overall rank (of 752) | Rank in HCP Demo (of 10) |
| --- | --- | --- | --- | --- |
| **AFFL_COUNT** | 0.121468 | 1.70% | 4 | 1st |
| **HCP_EXPERIENCE** | 0.026390 | 0.37% | 55 | 4th |
| **HCP_AGE** (output column `AGE`) | 0.007158 | 0.10% | 263 | 7th |
| **DIALYSIS_CENTER_FLAG** | 0.003081 | 0.04% | 478 | 8th |
| **TEACHING_HOSP_FLAG** | 0.000956 | 0.01% | 684 | 9th |
| **LONG_TERM_CARE_FACIL_FLAG** | 0.000311 | 0.004% | 726 | 10th |

The other HCP Demo features are NUM_HCPS_IN_BUILDING (2nd) and BUILDING_COLOCATION_FLAG (5th) from nb 33, and HCP_SPECIALTY_NEPH (3rd) and HCP_SPECIALTY_PCP (6th) from nb 20. **6 of the 10 HCP Demo features** come from this notebook.

In the 3.0 output but **not** in the 752: ORG_NM, EDUCATION_LEVEL and GENDER (raw strings, never encoded), GRAD_TRG_START_YEARS, and the eight governance / contact flags (KAISER, PDRP_OPTOUT, AMA_DO_NOT_CONTACT, CANDIDATE_RECORD, FELLOW, GRAD_TRAINING, IS_EXTERNALLY_MASTERED, IS_VEEVA_MASTER).

PRIMARY_SPECIALTY_CODE, MEDICAL_DEGREE_1, RECORD_STATE and HCP_STATUS are pulled by the notebook but are not among the 25 columns of the 3.0 output (checked 2026-11-18), so they never reached the model.

## 8. Points Settled by the 3.1 Checks (2026-11-18)

| Point | Finding |
| --- | --- |
| Universe and output size | The 3.0 output has 234,405 rows and 25 columns (an earlier note said 225,265 HCPs and 27 columns). |
| currentYear at the 3.0 run | 2026. HCP_EXPERIENCE + GRAD_YEAR = 2026 for 187,996 HCPs (3 others give 2024 or 2039; not investigated). |
| GRAD_TRG_START_YEARS placeholder | Confirmed: 1970-01-01 placeholder dates (see 6.3). |
| UC copy of MDM_STG_HCP_ACCT_AFFL | None. I searched `information_schema.tables` for `acct_affl`, `hcp_affl` and `hco_affl` (22 tables). The closest candidates (`whc_data.acct_affl_master`, `whc_data.whc_hcp_affl_master`, `whc_tsd.acct_affl`, `pc_data.hcp_hco_affl`) have no IS_PRIMARY_RELATIONSHIP__V or START_DATE, so they are not copies. |
| AFFL_COUNT "double counting" | **Reversed.** On the 3.1 nb 07 output (built from the real ACCT_AFFL), the distinct-account count is never below AFFL_COUNT and is higher for 12,204 HCPs (Spearman 0.994). AFFL_COUNT slightly **under**counts accounts, because accounts that share name, class and description collapse into one row. |

## 9. Key Observations
* AFFL_COUNT is the most important HCP Demo feature (SHAP 0.121, overall rank 4). On 3.1 its univariate writer-rate gradient is moderate (Q1 8.0% vs Q5 13.3%, rho 0.060). SHAP and a univariate gradient measure different things; this file does not explain the gap.
* HCP_EXPERIENCE (rank 55) is the second-strongest feature here, despite 19.8% nulls and negative values.
* AGE (rank 263) is 85% null and, where filled, tracks HCP_EXPERIENCE (Spearman 0.97 on the 3.1 output, where AGE is partly imputed from GRAD_YEAR).
* The three affiliation flags have low SHAP. DIALYSIS_CENTER_FLAG has a strong univariate gradient on 3.1 (43.3% vs 9.0%), but inside nephrology it narrows to 47.7% vs 38.6%. That fits overlap with HCP_SPECIALTY_NEPH as the reason for its low SHAP.
* Several output columns carry no usable information: GENDER and EDUCATION_LEVEL (never encoded), CANDIDATE_RECORD and IS_EXTERNALLY_MASTERED (constant), ORG_NM (19 HCPs) and GRAD_TRG_START_YEARS (placeholder).
