# Analysis: 33_HCP_Colocation_flag_new

## Notebook Overview
This notebook creates colocation flags at the premise (sub-building) and building level to identify influenced HCPs who are in close proximity to influencer HCPs. Influencer HCPs are those who have prescribed Kerendia in the past 3 months from the anchor date. The colocation concept captures peer influence effects on Kerendia prescribing behavior.

## Data Sources Used

| Source | Table/File | Purpose |
| --- | --- | --- |
| Databricks Catalog | `kerendia_laad_based_lrx.KERENDIA_LAAD_BASED_LRX_V6` | Historic Kerendia NBRx claims (2 years of data) |
| PHCDW (Snowflake) | `PHCDW_STG.MDM_STG_HCP_ADDR` | HCP address & geocoding: latitude, longitude, premise (building), sub_building |
| Databricks Volume | HCP Universe (`kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`) | HCP universe (228,690 HCPs) |
| Databricks Volume | `kerendia_nba_3_0_npi_bhid_mapping` | PROVIDER_ID to BH_ID mapping |

## Features Created

### 1. Building-Level Colocation Features
| Feature | Type | Description |
| --- | --- | --- |
| **BUILDING_COLOCATION_FLAG** | Binary (0/1) | 1 if another HCP in the same building prescribed Kerendia in the past 3 months |
| **NUM_HCPS_IN_BUILDING** | Integer | Count of distinct HCPs in the same building who prescribed Kerendia in the past 3 months |

### 2. Sub-Premise-Level Colocation Features
| Feature | Type | Description |
| --- | --- | --- |
| **SUBPREMISE_COLOCATION_FLAG** | Binary (0/1) | 1 if another HCP in the same sub-premise prescribed Kerendia in the past 3 months |
| **NUM_HCPS_IN_SUBPREMISE** | Integer | Count of distinct HCPs in the same sub-premise who prescribed Kerendia in the past 3 months |

## Business Rules Applied

### Colocation Flag Logic (applied identically for both building and sub-premise levels):

1. **Missing geocoding**: If LATITUDE or LONGITUDE = -999.99 (imputed missing value), colocation flag = 0
2. **Missing premise/building**: If BUILDING or SUB_PREMISE = 'NOT_AVAILABLE', colocation flag = 0
3. **Null handling**: If colocation flag is NULL (no match found), set to 0
4. **Single HCP in location**:
   - If the only HCP who prescribed Kerendia is the current HCP itself → flag = 0 (self-presence, no peer influence)
   - If the only HCP is a different HCP → flag = 1 (peer influence detected)
5. **Multiple HCPs in location**: If more than 1 HCP prescribed Kerendia → flag = 1 (strong peer influence)

### Time Window
- **3-month lookback**: For each anchor date (MONTH), the notebook looks back 3 months to identify HCPs who prescribed Kerendia. Only HCPs with at least 1 Kerendia NBRx claim in the 3-month window are considered "influencers."

### Data Processing Steps
1. Load HCP universe and join with NPI-BHID mapping (228,619 HCPs after join)
2. Load HCP address & geocoding data from MDM_STG_HCP_ADDR (selecting lowest address ordinal per HCP)
3. Load historic Kerendia NBRx claims from LAAD-based LRx V6
4. Create monthly anchor date spine (12 months from date_start to date_end)
5. Cross-join HCP universe with monthly dates
6. For each HCP-month, identify the 3-month lookback window
7. Filter Kerendia claims that fall within the 3-month window
8. Aggregate at premise/sub-premise level: count distinct HCPs, collect HCP IDs
9. Join aggregated data back to HCP universe
10. Apply colocation flag rules
11. Select final columns and save

### Output
Saved to: `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_hcp_subpremise_building_colocation_flag_for_inference`
Columns: PROVIDER_ID, SVC_DT_M, NUM_HCPS_IN_SUBPREMISE, SUBPREMISE_COLOCATION_FLAG, BUILDING_COLOCATION_FLAG, NUM_HCPS_IN_BUILDING, PULL_DT

## Features in the 752 Final NBA 3.0 Modeling Features

Cross-referenced with the Final NBA 3.0 Modeling Features Excel (Category: HCP Demo):

| Feature | Mean_Abs_SHAP | Rank in HCP Demo |
| --- | --- | --- |
| **NUM_HCPS_IN_BUILDING** | 0.086928 | 2nd (very high) |
| **BUILDING_COLOCATION_FLAG** | 0.023756 | 4th |

**2 out of 10 HCP Demo features** in the final model came from this notebook.

### Features NOT in the final 752:
- **SUBPREMISE_COLOCATION_FLAG** — did NOT make the final 752 features. The sub-premise level was too granular and did not add incremental predictive value over the building level.
- **NUM_HCPS_IN_SUBPREMISE** — did NOT make the final 752 features.

## Flag Distribution (from execution results)
- **SUBPREMISE_COLOCATION_FLAG**: 1 = 227,269 records (8.6%); 0 = 2,425,727 records (91.4%)
- **BUILDING_COLOCATION_FLAG**: 1 = 821,035 records (30.9%); 0 = 1,831,961 records (69.1%)

## Key Observations
- NUM_HCPS_IN_BUILDING is the 2nd most important HCP Demo feature (SHAP = 0.086928), second only to AFFL_COUNT (0.121468). This confirms that peer influence at the building level is a strong predictor of Kerendia NBRx.
- BUILDING_COLOCATION_FLAG (SHAP = 0.023756) is also significant, ranking 4th in HCP Demo.
- The sub-premise level features were entirely dropped, suggesting that building-level granularity is sufficient — sub-premise is too fine-grained to capture meaningful peer influence patterns.
- The 3-month lookback window is a key parameter — it captures recent peer influence rather than historical patterns.
- The flag logic correctly handles self-exclusion (an HCP who prescribed Kerendia alone in a building does not get a colocation flag).