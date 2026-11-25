# NBA 3.0 Colocation Analysis

## Notebook Overview
This notebook creates colocation flags at the premise (sub-building) and building level to identify influenced HCPs who are in close proximity to influencer HCPs. Influencer HCPs are those who have prescribed Kerendia in the past 3 months from the anchor date. The colocation concept captures peer influence effects on Kerendia prescribing behavior.

## Data Sources Used

| Source | Table/File | Purpose |
| --- | --- | --- |
| Databricks Catalog | `kerendia_laad_based_lrx.KERENDIA_LAAD_BASED_LRX_V6` | Historic Kerendia NBRx claims (2 years of data) |
| PHCDW (Snowflake) | `PHCDW_STG.MDM_STG_HCP_ADDR` | HCP address & geocoding: latitude, longitude, premise (building), sub_building |
| Databricks Volume | HCP Universe (`kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`) | HCP universe (228,690 HCPs in the run this note was based on; 234,405 in the current output, see the profile below) |
| Databricks Volume | `kerendia_nba_3_0_npi_bhid_mapping` | PROVIDER_ID to BH_ID mapping |

## Data Source Column Usage

**Method.** Total column counts and fill rates for UC tables are from direct queries. The MDM_STG_HCP_ADDR snapshot is a pre-selected subset (8 columns) from the Snowflake source; the full table has additional columns (ADMINISTRATIVE_AREA, SUB_ADMINISTRATIVE_AREA, POSTAL_CODE, etc.) not available in UC.

### Summary

| Source | Table/File | Total Columns | Columns Used | Usage Rate |
| --- | --- | --- | --- | --- |
| Databricks (UC) | `KERENDIA_LAAD_BASED_LRX_V6` | 30 | 5 | 16.7% |
| PHCDW (Snowflake) | `MDM_STG_HCP_ADDR` (snapshot) | 8 | 8 | 100% |
| Databricks (Volume) | `kerendia_nba_3_0_npi_bhid_mapping` | 3 | 2 | 66.7% |
| Databricks (Volume) | HCP universe | 1 | 1 | 100% |

### KERENDIA_LAAD_BASED_LRX_V6 (30 columns, 5 used)

Filtered to PRODUCT_GROUP = 'KERENDIA' (2,762,409 rows).

| Column | Fill Rate (Kerendia rows) | Used For |
| --- | --- | --- |
| PRODUCT_GROUP | 100% | WHERE filter |
| PROVIDER_ID | 100% | Join key |
| NPI | 99.9% | Pulled but not used downstream |
| PERIOD_ID | 100% | Monthly anchor (SVC_DT_M) |
| NBRX | 100% | Pulled as PROJECTED_NBRX (count of writers, not sum) |

25 of 30 columns are not used, including PERIOD_TYPE (W vs X not filtered), SPECIALTY_GROUP, INDICATION_GROUP, PRODUCT_CLASS (available in V7), GENDER, AGE_GROUP, PAY_TYPE, SOURCE_OF_BUSINESS, RX_CHANNEL, and HYPERTENSION_FLAG (see the 33 recommendation file for new features from these).

### MDM_STG_HCP_ADDR (Snowflake; 8-column snapshot, 8 used)

The notebook reads a saved snapshot (`query_output/kerendia_nba_3_0_hcp_model_hcp_profile_geocoding_addreess_information`) with 8 pre-selected columns. The full Snowflake table has additional columns not in the snapshot.

| Column | Fill Rate | Used For |
| --- | --- | --- |
| BH_ID | — | Join key |
| LATITUDE | — | Colocation grouping (−999.99 = missing) |
| LONGITUDE | — | Colocation grouping (−999.99 = missing) |
| PREMISE | — | Building-level grouping (as BUILDING) |
| SUB_BUILDING | — | Sub-premise-level grouping (as SUB_PREMISE) |
| ADDRESS_ORDINAL | — | Selects lowest address per HCP |
| CREATED_DATE | — | Not used in logic |
| FORMATTED_ADDRESS | — | Not used in logic |

Fill rates: 3.7% of universe HCPs (8,558) have no address row and get null for all colocation features. LATITUDE/LONGITUDE use −999.99 as an imputed missing value, which the notebook treats as flag = 0.

### kerendia_nba_3_0_npi_bhid_mapping (3 columns, 2 used)

| Column | Used For |
| --- | --- |
| PROVIDER_ID | Join to HCP universe |
| BH_ID | Join to MDM_STG_HCP_ADDR |

NPI_NUMBER is present but not used by this notebook.

### HCP universe (1 column, 1 used)

| Column | Used For |
| --- | --- |
| PROVIDER_ID | Primary key |

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

## Flag Distribution (from an earlier run's execution results)
- **SUBPREMISE_COLOCATION_FLAG**: 1 = 227,269 records (8.6%); 0 = 2,425,727 records (91.4%)
- **BUILDING_COLOCATION_FLAG**: 1 = 821,035 records (30.9%); 0 = 1,831,961 records (69.1%)

The section below replaces these with the current NBA 3.0 output.

## NBA 3.0 Feature Profile (HCP counts, nulls, distribution)

**Method.** Profiled on 2026-11-17 from the NBA 3.0 ops output `kerendia_nba_3_hcp_model_hcp_subpremise_building_colocation_flag_for_inference` (PULL_DT 2026_10_27). It is left-joined to the NBA 3.0 HCP universe (**234,405 HCPs**), as in the other static files. This is the only static-folder output that varies by month (`99_Combine_Physician_Data` joins it on `['PROVIDER_ID', 'SVC_DT_M']`), so the HCP-level profile uses the latest month (SVC_DT_M = 2026-09-01), with one row per HCP.

### Output shape
* 2,710,164 rows = 12 months (SVC_DT_M 2025-10-01 to 2026-09-01) x 225,847 HCPs. There are exactly 225,847 HCPs in every month and no duplicate PROVIDER_ID x month rows.
* Universe HCPs with no colocation row: **8,558 (3.7%)**. They get null for all four columns in every cohort.
* Over the 12 months, 94,951 universe HCPs (40.5%) have BUILDING_COLOCATION_FLAG = 1 in at least one month, and 28,818 (12.3%) have SUBPREMISE_COLOCATION_FLAG = 1. In an average month, 32.4% of the 225,847 HCPs with a row have the building flag and 9.2% the sub-premise flag.

### Per-feature profile (HCP level, latest month, n = 234,405)

| Feature | In 752? | HCPs with value | % | Null HCPs | Null % | Distinct | HCPs = 0 | HCPs = 1 / non-zero | Min | P25 | Median | Mean | P75 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NUM_HCPS_IN_BUILDING | Yes | 99,849 | 42.6% | 134,556 | 57.4% | 23 | 0 | 99,849 (42.6%) | 1 | 1 | 2 | 2.56 | 3 | 33 |
| BUILDING_COLOCATION_FLAG | Yes | 225,847 | 96.3% | 8,558 | 3.7% | 2 | 145,628 (62.1%) | 80,219 (34.2%) | 0 | 0 | 0 | 0.36 | 1 | 1 |
| NUM_HCPS_IN_SUBPREMISE | No | 36,664 | 15.6% | 197,741 | 84.4% | 12 | 0 | 36,664 (15.6%) | 1 | 1 | 1 | 1.68 | 2 | 15 |
| SUBPREMISE_COLOCATION_FLAG | No | 225,847 | 96.3% | 8,558 | 3.7% | 2 | 202,282 (86.3%) | 23,565 (10.1%) | 0 | 0 | 0 | 0.10 | 0 | 1 |
| PEER_HCPS_IN_BUILDING (derived, nulls kept) | No | 99,849 | 42.6% | 134,556 | 57.4% | 26 | 19,629 (8.4%) | 80,220 (34.2%) | 0 | 1 | 1 | 2.16 | 3 | 33 |
| PEER_HCPS_IN_BUILDING (derived, null filled with 0) | No | 225,847 | 96.3% | 8,558 | 3.7% | 26 | 145,627 (62.1%) | 80,220 (34.2%) | 0 | 0 | 0 | 0.95 | 1 | 33 |

Percentiles are approximate (Spark `percentile_approx`).

**Derived peer-only count.** The saved output applies the self-only rule to BUILDING_COLOCATION_FLAG but not to NUM_HCPS_IN_BUILDING. PEER_HCPS_IN_BUILDING = NUM_HCPS_IN_BUILDING − 1 if the HCP is a Kerendia writer themself (at least one KERENDIA claim in `KERENDIA_LAAD_BASED_LRX_V6` with PERIOD_ID from 2026-06-01 to before 2026-09-01, the notebook's 3-month window), otherwise unchanged. The filled version sets 0 for HCPs that have a colocation row but no nearby writer; the 8,558 HCPs with no row stay null. Among HCPs with peers > 0 (80,220), mean = 2.68, median = 2. This feature is not in the notebook output or the 752; it was profiled on 2026-11-18.

**NUM_HCPS_IN_BUILDING vs flag vs writer status (latest month, HCPs with a row):**

| NUM_HCPS_IN_BUILDING | Flag | HCP is writer | HCPs | Peer count | Meaning |
| --- | --- | --- | --- | --- | --- |
| 1 | 0 | Yes | 19,629 | 0 | The HCP is the only writer in the building (self-only, flag set to 0) |
| 1 | 0 | No | 1 | 1 | Exception (PROVIDER_ID 20974663), probably a claim near the window edge |
| 1 | 1 | No | 30,245 | 1 | The only writer is a different HCP |
| >1 | 1 | No | 29,012 | 2–33 | Several writers, all peers |
| >1 | 1 | Yes | 20,962 | 1–32 | Several writers, including the HCP |
| null | 0 | No | 125,771 | null / 0 | No writer in the building |
| null | 0 | Yes | 227 | null / 0 | Writer whose building is NOT_AVAILABLE |

Peer count > 0 matches BUILDING_COLOCATION_FLAG = 1 for 225,846 of 225,847 HCPs with a row (the exception is the one HCP above).

### Data-quality findings from the profile
* **The counts are null, not 0, when no writer is nearby.** NUM_HCPS_IN_BUILDING is never 0 (min 1). It is null for 134,556 HCPs (57.4%), while the flag is filled 0/1 for every HCP with a row (null only for the 8,558 with no row). A model sees "no Kerendia writer in the building" as missing, not as 0.
* **The count includes the HCP themself.** The minimum is 1 wherever it is non-null. The profile is on the final output, where the self-only rule sets the flag to 0 but leaves the count at 1. The gap between the 99,849 HCPs with a count and the 80,219 with flag = 1 is exactly 19,630 HCPs with count 1 and flag 0: 19,629 self-only writers plus 1 exception. Another 20,962 writers have counts above 1 that include themselves. The derived PEER_HCPS_IN_BUILDING removes the HCP from the count.
* Building-level colocation is 3.4x more common than sub-premise (34.2% vs 10.1% of HCPs), which fits sub-premise being dropped from the 752.
* The share of HCPs flagged is fairly stable but rising slightly: 30.9% of records in the earlier run, 32.4% in an average month of the current output, and 34.2% in the latest month.

## Features in the 752 Final NBA 3.0 Modeling Features

Cross-referenced with the Final NBA 3.0 Modeling Features Excel (Category: HCP Demo):

| Feature | Mean_Abs_SHAP | Share of total SHAP | Overall rank (of 752) | Rank in HCP Demo (of 10) |
| --- | --- | --- | --- | --- |
| **NUM_HCPS_IN_BUILDING** | 0.086928 | 1.22% | 8 | 2nd (very high) |
| **BUILDING_COLOCATION_FLAG** | 0.023756 | 0.33% | 64 | 5th |

Rank correction: BUILDING_COLOCATION_FLAG is 5th in HCP Demo, not 4th. HCP_SPECIALTY_NEPH (3rd) and HCP_EXPERIENCE (4th) both rank above it.

**2 out of 10 HCP Demo features** in the final model came from this notebook.

### Features NOT in the final 752:
- **SUBPREMISE_COLOCATION_FLAG** — did NOT make the final 752 features. The sub-premise level was too granular and did not add incremental predictive value over the building level.
- **NUM_HCPS_IN_SUBPREMISE** — did NOT make the final 752 features.

## Key Observations
- NUM_HCPS_IN_BUILDING is the 2nd most important HCP Demo feature (SHAP = 0.086928), second only to AFFL_COUNT (0.121468). This confirms that peer influence at the building level is a strong predictor of Kerendia NBRx.
- BUILDING_COLOCATION_FLAG (SHAP = 0.023756) is also significant, ranking 5th in HCP Demo.
- The sub-premise level features were entirely dropped, suggesting that building-level granularity is sufficient — sub-premise is too fine-grained to capture meaningful peer influence patterns.
- The 3-month lookback window is a key parameter — it captures recent peer influence rather than historical patterns.
- The flag logic correctly handles self-exclusion (an HCP who prescribed Kerendia alone in a building does not get a colocation flag).