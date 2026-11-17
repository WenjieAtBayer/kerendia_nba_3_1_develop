# Recommendations: 33_HCP_Colocation_flag_new (NBA 3.1)

## Data Refresh Status (read first)

| Input | Type | Refresh needed? | Notes |
| --- | --- | --- | --- |
| `query_output/kerendia_nba_3_0_hcp_model_hcp_profile_geocoding_addreess_information` | Delta snapshot of MDM_STG_HCP_ADDR | **Re-run upstream query each cycle** | The notebook reads this saved snapshot; the live Snowflake query is commented out. Last written 2026-10-26. If the upstream query step is skipped, addresses go stale |
| `kerendia_laad_based_lrx.KERENDIA_LAAD_BASED_LRX_V7` | UC table | No (refreshed at source) | V7 adds PRODUCT_CLASS (sMRA, SGLT2, GLP1, INSULIN, CGM), SPECIALTY_GROUP_ALIGNED and other columns. SPECIALTY_GROUP values changed (CARDIOLOGY → CARD, NEPHROLOGY → NEPH, ENDOCRINOLOGY → ENDO, PCP/IM → PCP). Weekly data (W) 2021-12-10 to 2026-10-16, 321,767 Kerendia NBRx |
| HCP universe, NPI-BHID mapping | Pipeline outputs | No | Rebuilt each run |

This notebook reads **no static CSV or Excel files**.

## Validation Method
Notebook code, LRx V7 schema and values, and MDM_STG_HCP_ADDR for the current universe were inspected on 2026-11-12. V7 PRODUCT_CLASS enables MRA/SGLT2/GLP1/INSULIN/CGM grouping without hardcoded product lists. Constraint: **only columns already in these sources are used**.

## 1. What the Data and Code Show
* NUM_HCPS_IN_BUILDING = count of distinct PROVIDER_IDs with any Kerendia LRx row in the 3-month window, grouped by LATITUDE, LONGITUDE, BUILDING and MONTH. **It includes the HCP themself.**
* The claims query filters only PRODUCT_GROUP = 'KERENDIA'. It does **not** filter PERIOD_TYPE. LRx V7 has two types: W (weekly, 321,767 Kerendia NBRx) and X (74,019 NBRx). Writer counts use countDistinct, so they are less exposed. Any NBRx-sum feature, however, would mix both period types unless PERIOD_TYPE is filtered.
* Rows with NBRX = 0 are not excluded, so 'writer' means any Kerendia LRx activity, not strictly a new-to-brand Rx.
* Only one address per HCP is used (minimum ADDRESS_ORDINAL in the original query), although universe HCPs have on average 5.9 addresses in MDM_STG_HCP_ADDR.
* LRx V7 adds PRODUCT_CLASS (sMRA, SGLT2, GLP1, INSULIN, CGM) which makes MRA/SGLT2/GLP1/INSULIN/CGM features straightforward without hardcoded product lists. SPECIALTY_GROUP values in V7 are abbreviated: CARD, NEPH, ENDO, PCP, NP/PA, HOS, HOSPITALIST, OTHERS. INDICATION_GROUP values include HF combinations (HF, CVD + HF, T2D + CKD + CVD + HF, etc.) plus T2D, CKD, CVD and ALL_OTHERS. **There is no T1D indication group.**
* In the final 752: NUM_HCPS_IN_BUILDING (SHAP 0.086928) and BUILDING_COLOCATION_FLAG (0.023756).

## 2. Improvements to Existing Features (same data)
| Feature | Improvement |
| --- | --- |
| NUM_HCPS_IN_BUILDING | Add NUM_OTHER_KERENDIA_WRITERS_IN_BUILDING = count excluding the HCP themself, so it measures peers only. Keep the original for continuity |
| NBRx filter | Add NBRX > 0 to the Kerendia LRx pull so a 'writer' is an HCP with at least one new-to-brand Kerendia Rx in the window, not any Kerendia LRx activity (rows with NBRX = 0 are currently counted) |
| Lookback window | Add 6M and 12M versions of the count and flag. LRx history goes back to 2023, so this needs no new data |
| Address coverage | Compute colocation over all 'Professional' addresses of the HCP and take the max, instead of only the primary address |

## 3. New Features From Existing Data
| New Feature | Columns | Logic | Rationale |
| --- | --- | --- | --- |
| BUILDING_KERENDIA_NBRX_3M | LRx NBRX (already pulled as PROJECTED_NBRX) | Sum of NBRx by building in window (PERIOD_TYPE filtered) | Volume, not just writer count |
| NUM_NEPH / CARD / ENDO / PCP_WRITERS_IN_BUILDING | LRx SPECIALTY_GROUP | Writer count by specialty group | Cross-specialty peer influence |
| NUM_HF_KERENDIA_WRITERS_IN_BUILDING | LRx INDICATION_GROUP | Writers with any Kerendia row where INDICATION_GROUP contains HF | HF-specific peer signal for 3.1 |
| NUM_CKD_KERENDIA_WRITERS_IN_BUILDING | Same | INDICATION_GROUP contains CKD | CKD-specific peer signal |
| BUILDING_HCP_COUNT | Address snapshot + universe | All universe HCPs at the building, writing or not | Building size |
| NUM_MRA_WRITERS_IN_BUILDING | LRx V7 PRODUCT_CLASS = 'sMRA' (includes ALDACTONE, SPIRONOLACTONE, EPLERENONE, INSPRA, CAROSPIR, ALDACTAZIDE) | Same logic as the Kerendia count | Steroidal MRA prescribing nearby — competitor-class signal |
| NUM_SGLT2_GLP1_WRITERS_IN_BUILDING | LRx V7 PRODUCT_CLASS IN ('SGLT2', 'GLP1') | Same logic | Cardiorenal-metabolic practice intensity |
| NUM_INSULIN_CGM_WRITERS_IN_BUILDING | LRx V7 PRODUCT_CLASS IN ('INSULIN', 'CGM') | Same logic | Diabetes-heavy practice proxy |

## 4. Priority Summary
| Priority | Action | Features |
| --- | --- | --- |
| HIGH | Fix definitions | Peer-only count (exclude self), NBRX > 0 filter, re-run address snapshot each cycle |
| HIGH | HF and specialty-aware colocation | NUM_HF_KERENDIA_WRITERS_IN_BUILDING, NUM_CARD/NEPH/ENDO_WRITERS_IN_BUILDING |
| HIGH | Longer windows | 6M / 12M counts and flags |
| MEDIUM | Intensity and building size | BUILDING_KERENDIA_NBRX_3M, BUILDING_HCP_COUNT |
| MEDIUM | Market-basket colocation | NUM_MRA_WRITERS_IN_BUILDING, NUM_SGLT2_GLP1_WRITERS_IN_BUILDING, NUM_INSULIN_CGM_WRITERS_IN_BUILDING |