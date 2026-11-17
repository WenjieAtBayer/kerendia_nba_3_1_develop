# Recommendations: 07_phy_static_features (NBA 3.1)

## Data Refresh Status (read first)

| Input | Type | Refresh needed? | Notes |
| --- | --- | --- | --- |
| `PHCDW.PHCDW_STG.MDM_STG_HCP_PRFL` | Snowflake table (MDM) | No - refreshed at source | Latest row per NPI by CREATED_DATE |
| `PHCDW.PHCDW_STG.MDM_STG_HCP_ACCT_AFFL` | Snowflake table (MDM) | No - refreshed at source | START_DATE is the load date (2026-11-06 for all 744,201 universe rows) and END_DATE is 100% null, so the table is a current snapshot with no history |
| `PHCDW.PHCDW_STG_CAR.STG_IQVIA_LAAD_DIM_PROVIDER` | Snowflake table | No | Only ORG_NM is used |
| HCP universe, `SOURCE_PROVIDER_BHID_NPI_MAPPING` | Pipeline outputs | No | Rebuilt each run |

This notebook reads **no static CSV or Excel files**. One logic item behaves like a stale input: `currentYear = datetime.now().year` is hard-wired into HCP_AGE, HCP_EXPERIENCE and GRAD_TRG_START_YEARS. The values move by 1 each calendar year, independent of the prediction window (see Section 2).

## Validation Method
All fill rates and counts below come from queries run on 2026-11-12 against the current Snowflake tables, restricted to the current HCP universe: 234,405 PROVIDER_IDs, 234,226 matched to a PRFL record by NPI and 225,847 with at least one affiliation. Constraint applied: **only columns that already exist in the three source tables are used**, and nothing assumes new columns or new data feeds.

## 1. Column Availability in the Existing Sources (HCP universe)

| Column (PRFL) | Used today? | Fill % | Observed values | Usable? |
| --- | --- | --- | --- | --- |
| GRAD_YEAR | Yes (HCP_EXPERIENCE) | 80.5% | 1954-2033 (includes future years) | Yes, after capping |
| BIRTH_YEAR | Yes (HCP_AGE) | **15.1%** | Date string | Weak: 85% null |
| GENDER | Pulled, not encoded | 100% | F 122,255 / M 93,361 / U 18,579 | Yes |
| MEDICAL_DEGREE_1 | Pulled, then dropped | 100% | MD 124,140 / NP 62,916 / DO 23,560 / PA 22,113 | Yes |
| SPECIALTY_2 | Pulled, then dropped | 44.6% | IM, FM, GP, HOS 3,218, CD 2,979, IC 1,995 | Yes |
| PRIMARY_SPECIALTY_GROUP | Pulled, then dropped | 100% | G-FM 128,610 / G-IM 69,480 / G-CD 23,282 | Yes, but duplicates nb 20 specialty |
| TYPE_OF_PRACTICE / MPA / PLACE_OF_EMPLOYMENT | Pulled, then dropped | ~59% | Numeric AMA-style codes (e.g. MPA 4 = 116,244) | Yes, one-hot top codes plus a missing flag |
| EDUCATION_LEVEL | Pulled, not encoded | 53.4% | RESIDENCY / MEDSCH / FELLOW | Weak |
| HCP_TYPE | Pulled, then dropped | 100% | **99.5% = 'P'** | No - no variance |
| BOARD_CERTIFICATION | Pulled, then dropped | **0.0%** | - | No - empty |
| GRAD_TRG_START_DATE / END_DATE | START used | 57% / 59% | Median duration 0.2 years | No - dates unreliable |
| FELLOW / KAISER | Yes | 89% / 54% | Y = 1,395 / Y = 615 | Very sparse |

| Column (ACCT_AFFL) | Used today? | Fill % | Observed values |
| --- | --- | --- | --- |
| ACCT_NAME, MAJOR_CLASS_OF_TRADE, DESCRIPTION | Yes | 99.5-100% | Medical Group Outpatient 402,344 rows, Hospitals 194,345, Dialysis 10,656, Home Health 19,737, Hospice 5,460, PHS 340B 4,350 |
| SPECIALTY (account specialty) | No (same table) | 99.5% | PRCP 226,799, CD 52,966, NEP 34,951, END 12,053 |
| BHO_ID (account ID) | No (same table) | - | Unique account key |
| IS_PRIMARY_RELATIONSHIP__V | No (same table) | 100% | Y 133,177 / N 610,507 |
| HCO_TYPE | No (same table) | 99.5% | Coded duplicate of DESCRIPTION |
| START_DATE / END_DATE | No | 100% / 0% | Load date only, so no tenure is possible |

## 2. Issues Found in the Current Logic
1. **Description pivot never reaches the output.** `df_affl_desc_pivot` (14 HCP_AFFL_DESCRIPTION_* columns) is built, but `df_spine` joins `df_affl`, not the pivot. That is why none of these columns are in the final 752: they were never offered to feature selection.
2. **HCP_AGE is 85% null.** Only 15.1% of the universe has BIRTH_YEAR, which explains its low SHAP (0.007158).
3. **Year drift.** AGE, HCP_EXPERIENCE and GRAD_TRG_START_YEARS use the wall-clock year (2025 at the last 3.0 run), not the prediction anchor date, so runs in different calendar years give different values for the same HCP, and training and inference can disagree.
4. **GRAD_YEAR has future values** (max 2033). These create negative HCP_EXPERIENCE values.
5. **AFFL_COUNT counts rows, not accounts.** It is `count(*)` over distinct (BH_ID, ACCT_NAME, MAJOR_CLASS_OF_TRADE, DESCRIPTION): 735,712 such rows versus 744,201 raw rows. Mean 3.3, median 3, max 41 per HCP.
6. GENDER and EDUCATION_LEVEL are written as raw strings. Neither appears in the 752, which is consistent with them never being encoded.

## 3. Improvements to Existing Features (feasible with current columns)

| Feature | In 752? (SHAP) | Improvement | Columns |
| --- | --- | --- | --- |
| AFFL_COUNT | Yes (0.121468) | Count distinct BHO_ID (accounts) instead of rows. Optionally keep the row count as is for continuity and add the distinct count alongside. | BHO_ID (same table) |
| HCP_EXPERIENCE | Yes (0.026390) | Anchor to `prediction_start` year instead of `datetime.now()`. Set GRAD_YEAR > anchor year to null. | GRAD_YEAR |
| HCP_AGE | Yes (0.007158) | Either drop it (redundant with HCP_EXPERIENCE, 85% null), or impute AGE = anchor - GRAD_YEAR + median(birth-to-grad gap among the 15% with both fields). Anchor to prediction_start. | BIRTH_YEAR, GRAD_YEAR |
| TEACHING_HOSP_FLAG | Yes (0.000956) | Keep (cheap). | DESCRIPTION |
| HCP_AFFL_DESCRIPTION_* | No (not in 3.0 output) | This pivot was not part of the NBA 3.0 feature set (it was built in the notebook but never joined to the output). It will be added in NBA 3.1 by joining the pivot to the spine. | DESCRIPTION |

## 4. Features to Drop (not useful)
- **GRAD_TRG_START_YEARS**: the training dates are unreliable (median duration 0.2 years) and redundant with HCP_EXPERIENCE.
- **KAISER, PDRP_OPTOUT, AMA_DO_NOT_CONTACT, CANDIDATE_RECORD, IS_EXTERNALLY_MASTERED, IS_VEEVA_MASTER, GRAD_TRAINING, FELLOW**: these are governance and contact flags, and none is in the 752. KAISER (615 Y) and FELLOW (1,395 Y) are too sparse to matter. Apply PDRP and AMA opt-outs as targeting filters downstream.
- **ORG_NM, raw ACCT_NAME / MAJOR_CLASS_OF_TRADE / DESCRIPTION arrays**: high-cardinality text. Use them only as inputs to engineered flags.
- **EDUCATION_LEVEL**: 53% fill and largely implied by MEDICAL_DEGREE_1.

## 5. New Features From the Existing Sources
All of these use tables this notebook already queries. Columns marked "same table" exist in the table but need adding to the SELECT.

### From MDM_STG_HCP_PRFL
| New Feature | Columns | Logic | Evidence / coverage |
| --- | --- | --- | --- |
| HCP_DEGREE_NP_PA | MEDICAL_DEGREE_1 | 1 if NP, PA or APRN | 85,237 of 234,226 (36%). NP/PA are a distinct LRx specialty group with 28,361 Kerendia NBRx in LRx V6 since Sep 2025 |
| HCP_GENDER_F | GENDER | 1 if F, 0 if M, null if U | 100% fill |
| HCP_SECONDARY_SPEC_CARDIORENAL | SPECIALTY_2 | 1 if SPECIALTY_2 is in CD, IC, AHF, HFT, NEP, END or DIA | 7,237 HCPs. Picks up internists with a cardiology or nephrology secondary specialty (HF and CKD relevant) |
| HCP_PRACTICE_TYPE_* / HCP_MPA_* | TYPE_OF_PRACTICE, MPA | One-hot of codes with at least 1% prevalence, plus a missing flag (41% missing) | Already pulled; decode the codes with the MDM data dictionary before naming them |
| HCP_EMPLOYMENT_* | PLACE_OF_EMPLOYMENT | Same approach | Codes 6 (67,255), 99 (36,605), 2 (17,272) |

### From MDM_STG_HCP_ACCT_AFFL
| New Feature | Columns | Logic | Evidence / coverage |
| --- | --- | --- | --- |
| AFFL_DISTINCT_ACCT_COUNT | BHO_ID (same table) | countDistinct(BHO_ID) | Fixes AFFL_COUNT double counting |
| AFFL_CARD_ACCT_COUNT | SPECIALTY (same table) | Number of affiliated accounts with SPECIALTY = CD | 52,966 affiliation rows. Most direct static HF signal available |
| AFFL_NEPH_ACCT_COUNT | SPECIALTY | Same, NEP | 34,951 rows |
| AFFL_ENDO_ACCT_COUNT | SPECIALTY | Same, END | 12,053 rows; diabetes-focused practices |
| AFFL_HOSPITAL_COUNT | MAJOR_CLASS_OF_TRADE | Count of 'Hospitals' affiliations | 194,345 rows |
| AFFL_IDN_ACO_FLAG | DESCRIPTION | 1 if ACO or Health System | ACO 36,183 rows; Health System 23,275 rows |
| AFFL_POST_ACUTE_FLAG | MAJOR_CLASS_OF_TRADE | 1 if Home Health, Hospice or Residential/Long-Term Care | 19,737 + 5,460 + 14,254 rows; advanced HF care settings |
| PRIMARY_AFFL_CLASS_* | IS_PRIMARY_RELATIONSHIP__V (same table), MAJOR_CLASS_OF_TRADE | Class of trade of the primary account (Y = 133,177 rows), one-hot | Separates hospital-based from office-based primary practice |
| PRIMARY_ACCT_HCP_COUNT | BHO_ID, IS_PRIMARY_RELATIONSHIP__V | Number of universe HCPs sharing the HCP's primary account | Practice size proxy. Uses data already in the table |

## 6. Priority Summary
| Priority | Action | Features |
| --- | --- | --- |
| HIGH | Fix existing definitions | AFFL_COUNT to distinct BHO_ID; HCP_EXPERIENCE and AGE anchored to prediction_start; cap future GRAD_YEAR |
| HIGH | HF-relevant affiliation features | AFFL_CARD_ACCT_COUNT, AFFL_NEPH_ACCT_COUNT, AFFL_ENDO_ACCT_COUNT, AFFL_POST_ACUTE_FLAG |
| HIGH | Encode unused but complete PRFL columns | HCP_DEGREE_NP_PA, HCP_GENDER_F, HCP_SECONDARY_SPEC_CARDIORENAL |
| MEDIUM | Practice setting | PRIMARY_AFFL_CLASS_*, PRIMARY_ACCT_HCP_COUNT, AFFL_IDN_ACO_FLAG, AFFL_HOSPITAL_COUNT, HCP_PRACTICE_TYPE_* |
| MEDIUM | Add affiliation description pivot (new in 3.1) | HCP_AFFL_DESCRIPTION_* |
| MEDIUM | Drop | GRAD_TRG_START_YEARS, governance flags |

Note: HCP_SPECIALTY_CARD / ENDO are not added here. Notebook 20 already outputs SPECIALTY_GROUP with CARD (24,590 HCPs) and ENDO (9,711), so see the 20 and 35 recommendation files.