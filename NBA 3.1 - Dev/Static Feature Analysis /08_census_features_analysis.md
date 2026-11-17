# Analysis: 08_census_features

## Notebook Overview
This notebook creates Social Determinants of Health (SDoH) features from US Census American Community Survey (ACS) data at the ZIP code level. These features capture local demographics, education, poverty, transportation, employment, income, and insurance characteristics of the areas where HCPs practice.

## Data Sources Used

| Source | File/Path | Purpose |
| --- | --- | --- |
| Databricks Volume | `SDoH Walgreens v2.csv` in `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/input_files/` | US Census ACS data by ZIP code/ZCTA |

## Features Created

The input CSV contains 24 columns (including ZIPCODE and ZCTA). After dropping ZCTA, 22 feature columns are created:

### Race / Ethnicity (5 features)
| Feature | Description |
| --- | --- |
| ACS_PCT_ASIAN_ZC | % Asian population in ZIP code |
| ACS_PCT_BLACK_ZC | % Black population in ZIP code |
| ACS_PCT_HISPANIC_ZC | % Hispanic population in ZIP code |
| ACS_PCT_OTHER_RACE_ZC | % Other race population in ZIP code |
| ACS_PCT_WHITE_ZC | % White population in ZIP code |

### Education (7 features)
| Feature | Description |
| --- | --- |
| ACS_PCT_EDUC_ZC | % with education attainment |
| ACS_PCT_COLLEGE_ASSOCIATE_DGR_ZC | % with college associate degree |
| ACS_PCT_BACHELOR_DGR_ZC | % with bachelor's degree |
| ACS_PCT_GRADUATE_DGR_ZC | % with graduate degree |
| ACS_PCT_HS_GRADUATE_ZC | % with high school graduate |
| ACS_PCT_LT_HS_ZC | % with less than high school |
| ACS_PCT_POSTHS_ED_ZC | % with post-high school education |

### Poverty (4 features)
| Feature | Description |
| --- | --- |
| ACS_PCT_POV_ASIAN_ZC | % Asian population in poverty |
| ACS_PCT_POV_BLACK_ZC | % Black population in poverty |
| ACS_PCT_POV_HISPANIC_ZC | % Hispanic population in poverty |
| ACS_PCT_POV_WHITE_ZC | % White population in poverty |

### Transportation (2 features)
| Feature | Description |
| --- | --- |
| ACS_PCT_TRANSPORT_ZC | % using transportation (general) |
| ACS_PCT_PUBL_TRANSIT_ZC | % using public transit |

### Employment & Income (2 features)
| Feature | Description |
| --- | --- |
| ACS_PCT_UNEMPLOY_ZC | % unemployed |
| ACS_PER_CAPITA_INC_ZC | Per capita income |

### Insurance (2 features)
| Feature | Description |
| --- | --- |
| ACS_PCT_UNINSURED_ZC | % uninsured population |
| ACS_PCT_UNINSURED_BELOW64_ZC | % uninsured population below age 64 |

## Business Rules Applied
1. ZIPCODE is zero-padded to 5 digits (`str.zfill(5)`)
2. ZCTA column is dropped (redundant with ZIPCODE)
3. Data is converted from pandas to Spark DataFrame
4. PULL_DT (current date) is added as a metadata column
5. Output is written as Delta table (overwrite mode)

## Output
Saved to: `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_sdoh_features_for_inference`

## Features in the 752 Final NBA 3.0 Modeling Features

**ALL 22 features** from this notebook appeared in the final 752 model features (Category: Geographic Features, Sub Category: SDoH). This is a 100% retention rate — every SDoH feature survived feature selection.

Ranked by SHAP importance:

| Feature | Mean_Abs_SHAP | Rank in SDoH |
| --- | --- | --- |
| **ACS_PCT_HISPANIC_ZC** | 0.041448 | 1st (highest) |
| ACS_PCT_LT_HS_ZC | 0.021943 | 2nd |
| ACS_PCT_UNEMPLOY_ZC | 0.015822 | 3rd |
| ACS_PCT_WHITE_ZC | 0.015638 | 4th |
| ACS_PCT_OTHER_RACE_ZC | 0.011785 | 5th |
| ACS_PCT_ASIAN_ZC | 0.011211 | 6th |
| ACS_PCT_GRADUATE_DGR_ZC | 0.008663 | 7th |
| ACS_PCT_POV_BLACK_ZC | 0.008922 | 8th |
| ACS_PCT_TRANSPORT_ZC | 0.008173 | 9th |
| ACS_PCT_BACHELOR_DGR_ZC | 0.007580 | 10th |
| ACS_PCT_HS_GRADUATE_ZC | 0.007461 | 11th |
| ACS_PCT_COLLEGE_ASSOCIATE_DGR_ZC | 0.007385 | 12th |
| ACS_PCT_POSTHS_ED_ZC | 0.007166 | 13th |
| ACS_PCT_PUBL_TRANSIT_ZC | 0.006979 | 14th |
| ACS_PCT_POV_ASIAN_ZC | 0.006846 | 15th |
| ACS_PCT_UNINSURED_BELOW64_ZC | 0.007733 | 16th |
| ACS_PCT_EDUC_ZC | 0.005680 | 17th |
| ACS_PCT_UNINSURED_ZC | 0.005441 | 18th |
| ACS_PER_CAPITA_INC_ZC | 0.006072 | 19th |
| ACS_PCT_POV_HISPANIC_ZC | 0.004768 | 20th |
| ACS_PCT_POV_WHITE_ZC | 0.003886 | 21st |
| ACS_PCT_BLACK_ZC | 0.006485 | 22nd |

## Key Observations
- ACS_PCT_HISPANIC_ZC has the highest SHAP value (0.041448) among all SDoH features, suggesting HCPs in areas with higher Hispanic populations have distinct NBRx patterns
- Education features (ACS_PCT_LT_HS_ZC, ACS_PCT_GRADUATE_DGR_ZC) are among the top SDoH predictors, indicating that patient education levels in an HCP's area influence Kerendia prescribing
- Poverty and unemployment features have moderate importance, reflecting socioeconomic barriers to Kerendia access
- The SDoH features collectively make up 22 of the 752 final features (2.9%), all under the Geographic Features category
- These features are static at the ZIP level and do not change over time — they capture the practice environment rather than HCP behavior