# Analysis: 07_phy_static_features

## Notebook Overview
This notebook creates physician static (demographic and professional) features for the Kerendia NBA 3.0 HCP-level NBRx prediction model. It pulls HCP profile, specialty, and affiliation data from multiple PHCDW source tables, cleans and transforms them, and saves the output for inference.

## Data Sources Used

| Source | Table | Purpose |
| --- | --- | --- |
| PHCDW (Snowflake) | `PHCDW_STG_CAR.STG_IQVIA_LAAD_DIM_PROVIDER` | Provider specialty code, organization name |
| PHCDW (Snowflake) | `PHCDW_STG.MDM_STG_HCP_PRFL` | HCP profile: medical degree, birth year, grad year, gender, education, opt-out flags |
| PHCDW (Snowflake) | `PHCDW_STG.MDM_STG_HCP_ACCT_AFFL` | Account affiliations: teaching hospital, dialysis center, long-term care, etc. |
| Databricks Volume | `kerendia_nba_3_volume` → `kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` | HCP universe (225,265 HCPs) |
| Databricks Catalog | `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING` | PROVIDER_ID to NPI/BH_ID mapping |

## Features Created

### 1. Provider Dimension Features (from STG_IQVIA_LAAD_DIM_PROVIDER)
- **PRIMARY_SPECIALTY_CODE** - HCP's primary specialty code
- **ORG_NM** - Organization name

### 2. HCP Profile Features (from MDM_STG_HCP_PRFL)
Uses ROW_NUMBER() OVER (PARTITION BY NPI_NUM ORDER BY CREATED_DATE desc) to get the latest record per NPI.
- **MEDICAL_DEGREE_1** - Medical degree
- **RECORD_STATE** - Record state
- **HCP_STATUS** - HCP status
- **BIRTH_YEAR** - Birth year (used to calculate AGE)
- **EDUCATION_LEVEL** - Education level
- **GRAD_YEAR** - Graduation year (used to calculate EXPERIENCE)
- **GRAD_TRG_START_DATE** - Graduate training start date
- **GENDER** - Gender
- **KAISER** - Kaiser flag (binary: Y/true = 1)
- **PDRP_OPTOUT** - PDRP opt-out flag (binary: Y/true = 1)
- **AMA_DO_NOT_CONTACT** - AMA do not contact flag (binary: Y/true = 1)
- **CANDIDATE_RECORD** - Candidate record flag (binary: Y/true = 1)
- **FELLOW** - Fellow flag (binary: Y/true = 1)
- **GRAD_TRAINING** - Graduate training flag (binary: Y/true = 1)
- **IS_EXTERNALLY_MASTERED** - Externally mastered flag (binary: Y/true = 1)
- **IS_VEEVA_MASTER** - Veeva master flag (binary: Y/true = 1)

### 3. Affiliation Features (from MDM_STG_HCP_ACCT_AFFL)
Business rules applied to create binary flags:
- **TEACHING_HOSP_FLAG** = 1 if DESCRIPTION = 'Organization, CMS Teaching Hospital', else 0
- **DIALYSIS_CENTER_FLAG** = 1 if MAJOR_CLASS_OF_TRADE = 'Dialysis & Infusion Centers', else 0
- **LONG_TERM_CARE_FACIL_FLAG** = 1 if DESCRIPTION = 'Organization, Nursing Home or Long Term Care', else 0

#### Affiliation Description Pivot
The DESCRIPTION array column is exploded and pivoted into ~70 binary columns (HCP_AFFL_DESCRIPTION_*). A filtering step keeps only columns where the sum exceeds 1% of total HCP count (threshold = 212,074 * 0.01 = ~2,121), reducing to 14 columns. Examples include:
- HCP_AFFL_DESCRIPTION_ORGANIZATION_CMS_TEACHING_HOSPITAL
- HCP_AFFL_DESCRIPTION_ORGANIZATION_GROUP_PRACTICE
- HCP_AFFL_DESCRIPTION_ORGANIZATION_HOSPITAL
- HCP_AFFL_DESCRIPTION_ORGANIZATION_HEALTH_SYSTEM
- HCP_AFFL_DESCRIPTION_PHARMACY_RETAIL_CHAIN
- HCP_AFFL_DESCRIPTION_ORGANIZATION_CLINIC
- (and ~8 others)

- **AFFL_COUNT** - Total count of affiliations per HCP (computed before the pivot)

### 4. Derived Numeric Features
Formulas used (currentYear = datetime.now().year, set to 2025 at runtime; originally 2022 per notebook comments):
- **AGE** = currentYear - YEAR(BIRTH_YEAR), set to NULL if BIRTH_YEAR = '1900-01-01' or is NULL
- **GRAD_TRG_START_YEARS** = currentYear - YEAR(GRAD_TRG_START_DATE)
- **HCP_EXPERIENCE** = currentYear - GRAD_YEAR

### 5. Output
Saved to: `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_phy_static_features_for_inference`
- 225,265 distinct PROVIDER_IDs
- 27 columns total

## Features in the 752 Final NBA 3.0 Modeling Features
Cross-referenced with the Final NBA 3.0 Modeling Features Excel (752 features, with SHAP importance values).

The following features from this notebook appeared in the final 752 model features (Category: HCP Demo):

| Feature | Mean_Abs_SHAP | Importance Rank in HCP Demo |
| --- | --- | --- |
| **AFFL_COUNT** | 0.121468 | 1st (highest in HCP Demo) |
| **HCP_EXPERIENCE** | 0.026390 | 3rd |
| **HCP_AGE** | 0.007158 | 6th |
| **DIALYSIS_CENTER_FLAG** | 0.003081 | 8th |
| **TEACHING_HOSP_FLAG** | 0.000956 | 9th |
| **LONG_TERM_CARE_FACIL_FLAG** | 0.000311 | 10th (lowest in HCP Demo) |

**6 out of 10 HCP Demo features** in the final model came from this notebook.

### Features NOT in the final 752:
The following features were created but did NOT make it to the final 752 model features:
- PRIMARY_SPECIALTY_CODE, ORG_NM (raw categorical, likely encoded downstream)
- MEDICAL_DEGREE_1, RECORD_STATE, HCP_STATUS, EDUCATION_LEVEL, GENDER (raw)
- GRAD_TRG_START_YEARS (derived but not selected)
- KAISER, PDRP_OPTOUT, AMA_DO_NOT_CONTACT, CANDIDATE_RECORD, FELLOW, GRAD_TRAINING, IS_EXTERNALLY_MASTERED, IS_VEEVA_MASTER (binary flags)
- All 14 HCP_AFFL_DESCRIPTION_* pivoted columns (none made the final cut)

## Key Observations
- AFFL_COUNT is the single most important HCP Demo feature (SHAP = 0.121), suggesting HCPs with more affiliations are stronger NBRx predictors
- HCP_EXPERIENCE (years since graduation) is the 3rd most important, indicating experienced HCPs prescribe more
- DIALYSIS_CENTER_FLAG and TEACHING_HOSP_FLAG have very low SHAP values, suggesting marginal contribution
- LONG_TERM_CARE_FACIL_FLAG has the lowest SHAP in the entire HCP Demo category (0.000311)
- The 14 pivoted HCP_AFFL_DESCRIPTION_* columns were all filtered out during feature selection, suggesting the raw count (AFFL_COUNT) was more informative than individual affiliation types