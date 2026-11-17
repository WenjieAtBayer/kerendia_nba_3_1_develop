# Recommendations: 08_census_features (NBA 3.1)

## Data Refresh Status (read first)

| Input | Type | Last modified | Refresh needed? |
| --- | --- | --- | --- |
| `/Volumes/.../kerendia_nba_3_volume/hcp_level_model/ops_pipeline/input_files/SDoH Walgreens v2.csv` | **Static CSV** | 2025-09-24 | **YES. This is the only input to the notebook, and it is static.** |

* The file has no year or vintage column, so the ACS vintage cannot be determined from the data. The column naming (ACS_*_ZC, ZIPCODE + ZCTA) matches a ZIP/ZCTA-level ACS extract. Confirm the vintage with whoever supplied the "Walgreens v2" file.
* It has 41,011 ZIPs mapped to 32,441 ZCTAs, so the ZIP-to-ZCTA crosswalk is baked in. 13,919 ZIPs share a ZCTA with another ZIP and therefore get identical values. ZIPs created after the crosswalk will be missing.
* Refresh request: same 24 columns, same names, same ZIP + ZCTA layout, newer ACS 5-year vintage. Record the vintage year in the file name.

## Validation Method
The CSV was profiled directly on 2026-11-12: nulls, ranges, correlations and identities between columns. Coverage was checked against the primary-address ZIPs of the current HCP universe from MDM_STG_HCP_ADDR (234,163 HCPs). That set may differ slightly from the ZIP the pipeline actually joins on. Constraint: **only the 22 existing ACS columns are used**, with no new columns or sources.

## 1. What the Data Shows
* Coverage: 99.99% of HCP primary-address ZIPs are found in the file.
* Nulls across all ZIPs: race-specific poverty is often null (POV_ASIAN 35.3%, POV_BLACK 28.3%, POV_HISPANIC 16.5%). At HCP ZIPs the nulls are much lower (4.4%, 2.6%, 1.2%), so these features remain usable for the model population. All other columns are null at 0.9-1.7% of all ZIPs.
* Exact identities (verified):
  * ACS_PCT_LT_HS_ZC + ACS_PCT_HS_GRADUATE_ZC + ACS_PCT_POSTHS_ED_ZC = 100 (min 99.99, max 100.01).
  * ACS_PCT_COLLEGE_ASSOCIATE_DGR_ZC + ACS_PCT_BACHELOR_DGR_ZC + ACS_PCT_GRADUATE_DGR_ZC = ACS_PCT_POSTHS_ED_ZC (mean difference 0.00, std 0.01).
* High correlations (only pairs with |r| > 0.8): UNINSURED vs UNINSURED_BELOW64 (r = 0.969) and HS_GRADUATE vs POSTHS_ED (r = 0.842). TRANSPORT vs PUBL_TRANSIT did not exceed 0.8.
* ACS_PCT_EDUC_ZC is **not** equal to BACHELOR + GRADUATE (mean difference 4.26, std 19.21). It carries separate information, so do not drop it on redundancy grounds.
* The race shares (WHITE + BLACK + ASIAN + OTHER) average 94.3, not 100. HISPANIC is an ethnicity and overlaps with the race categories.

## 2. Improvements to Existing Features (same data)
| Improvement | Logic |
| --- | --- |
| Explicit missing handling | Leave NaN for tree models, but add SDOH_MISSING_FLAG for HCP ZIPs not in the file (0.01% today, rising as the file ages) |
| ZIP formatting | Keep the 5-digit zero-padding; also truncate ZIP+4 on the HCP side before the join |
| Per capita income scale | Add LOG_PER_CAPITA_INC alongside the raw value (range 137 to 320,536) to tame the long tail for any non-tree model |

## 3. New Features From the Existing 22 Columns
| New Feature | Logic | Rationale |
| --- | --- | --- |
| SDOH_DEPRIVATION_INDEX | Mean of z-scores of LT_HS, UNEMPLOY, UNINSURED_BELOW64, TRANSPORT and (-) PER_CAPITA_INC, computed across ZIPs in the file | One stable socioeconomic disadvantage signal; robust to single-column noise |
| ACS_PCT_BACHELOR_PLUS_ZC | BACHELOR + GRADUATE | Standard attainment cut, cleaner than three overlapping columns |
| ACS_PCT_NON_WHITE_ZC | 100 - WHITE | Single diversity measure; complements HISPANIC (top SHAP) |
| SDOH_POVERTY_DISPARITY | max(POV_BLACK, POV_HISPANIC, POV_ASIAN) - POV_WHITE (ignoring nulls) | Summarises the four sparse race-poverty columns into one |
| SDOH_INCOME_DECILE_US | Decile of PER_CAPITA_INC across all ZIPs | Rank-based, stable between ACS refreshes |
| TERR_SDOH_* (e.g. TERR_DEPRIVATION_MEAN) | Average of a ZIP measure over all ZIPs in the HCP's territory, using the zip_terr file already used in notebook 20 | Territory context |
| SDOH_DEPRIVATION_VS_TERR | HCP ZIP index - territory mean | Shows whether the HCP practises in a poorer or richer pocket than the territory average |
| COUNTY_SDOH_* | Average over ZIPs in the same county (COUNTY_NAME + STATE from zip_terr) | Smooths noisy small-ZIP values. Unweighted, because the file has no population column |

### Worked Example: TERR_SDOH_* (TERR_DEPRIVATION_MEAN) and SDOH_DEPRIVATION_VS_TERR
Illustrative numbers only.

**Step 1: ZIP-level SDOH_DEPRIVATION_INDEX.** Standardise each column across all ZIPs in the file, z = (ZIP value - mean across all ZIPs) / std across all ZIPs. Flip the sign for PER_CAPITA_INC (higher income = less deprived), then average the five z-scores. Example for ZIP 30301:

| Column | ZIP value | Mean (all ZIPs) | Std (all ZIPs) | z |
| --- | --- | --- | --- | --- |
| LT_HS | 18 | 12 | 6 | +1.0 |
| UNEMPLOY | 9 | 5 | 2 | +2.0 |
| UNINSURED_BELOW64 | 14 | 10 | 4 | +1.0 |
| TRANSPORT | 10 | 6 | 4 | +1.0 |
| PER_CAPITA_INC | 22,000 | 32,000 | 10,000 | -1.0, flipped to +1.0 |

Index = (1.0 + 2.0 + 1.0 + 1.0 + 1.0) / 5 = **1.2**. Positive means more deprived than the average US ZIP.

**Step 2: Territory average (TERR_DEPRIVATION_MEAN).** Take all ZIPs mapped to the territory in zip_terr and average their index. Example for territory T-101:

| ZIP | SDOH_DEPRIVATION_INDEX |
| --- | --- |
| 30301 | 1.2 |
| 30302 | 0.4 |
| 30303 | -0.6 |
| 30304 | -0.2 |
| 30305 | Not in SDOH file, skipped |

TERR_DEPRIVATION_MEAN (T-101) = (1.2 + 0.4 - 0.6 - 0.2) / 4 = **0.2**. Each ZIP counts once, whether or not it has HCPs (unweighted, since the file has no population column).

**Step 3: Attach to HCPs and compare (SDOH_DEPRIVATION_VS_TERR).** Every HCP in T-101 gets TERR_DEPRIVATION_MEAN = 0.2. The relative feature is the HCP's own ZIP index minus the territory mean:

| HCP | ZIP | ZIP index | TERR_DEPRIVATION_MEAN | SDOH_DEPRIVATION_VS_TERR |
| --- | --- | --- | --- | --- |
| HCP A | 30301 | 1.2 | 0.2 | +1.0 (poorer pocket than the territory) |
| HCP B | 30303 | -0.6 | 0.2 | -0.8 (better-off pocket) |

The `*` in TERR_SDOH_* means Step 2 can be applied to any single column instead of the index (e.g. TERR_ACS_PCT_HISPANIC_MEAN = average ACS_PCT_HISPANIC_ZC over the territory's ZIPs).

**Implementation notes**
* Shared ZCTAs: 13,919 ZIPs share a ZCTA and carry identical values. Consider de-duplicating by ZCTA within a territory so one area is not counted several times.
* HCPs whose ZIP has no territory in zip_terr get null.
* Static check: the census values only change when the CSV is refreshed, but the territory mean also changes when territories are realigned. Freeze the zip_terr mapping at a fixed date if this is to stay a static feature.

## 4. Priority Summary
| Priority | Action | Features |
| --- | --- | --- |
| HIGH | Refresh the static CSV with the same schema and record the vintage | All 22 ACS_* |
| HIGH | Remove the exact duplicate | ACS_PCT_POSTHS_ED_ZC |
| MEDIUM | Composite and derived features | SDOH_DEPRIVATION_INDEX, ACS_PCT_BACHELOR_PLUS_ZC, SDOH_POVERTY_DISPARITY |
| MEDIUM | Territory / county context | TERR_SDOH_*, SDOH_DEPRIVATION_VS_TERR |
