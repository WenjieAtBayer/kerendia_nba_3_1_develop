# NBA 3.0 final 752 features: what they are called in NBA 3.1

Written 2026-11-27. Purpose: before we change the statistical clean-up (Iteration 3), we need to know which of the 752 features of the final NBA 3.0 model exist in the NBA 3.1 feature table, so the clean-up can be told never to remove them.

This check was done **by feature name only**. Values were not compared yet (see open points).

## Where to find things

| What | Where |
| --- | --- |
| NBA 3.0 final feature list (input of the 3.0 ops pipeline) | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/input_files/Kerendia_NBA_3_feature_list_752_features.csv` |
| NBA 3.0 feature scorecard (rank, family, SHAP for the same 752 features) | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/dev_folder/notebook_output/feature_evaluation/NBA_3_0_Model_752_Feature_Scorecard.csv` |
| NBA 3.0 feature table built from that list | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_selected_features_data` |
| NBA 3.1 feature dictionary (17,384 features, with category) | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/combined_2026_11_26_full/hcp_combined/kerendia_nba_3_1_hcp_feature_dictionary` |
| Statistical clean-up notebook that will use this match | `NBA 3.1 - Dev/10_Feature_Selection/Iteration_3_all_HCPs/02_nba_3_1_statistical_cleanup` |

## 1. The NBA 3.0 list: 753 rows = 752 features

The 3.0 list file has one column (`Features`) and **753 rows**: the HCP key `HCP_COHORT_ID` plus **752 features**. Source: `Kerendia_NBA_3_feature_list_752_features.csv`.

We checked that this is really the final 3.0 list in two other places:

| Check | Result | Source |
| --- | --- | --- |
| Same features as the 3.0 scorecard? | Yes, all 752 are in the scorecard (752 rows) | `NBA_3_0_Model_752_Feature_Scorecard.csv` |
| Same features as the 3.0 feature table? | Yes, the table has these 752 features as columns, plus `HCP_COHORT_ID`, `PULL_DT` and `COHORT` (755 columns) | `kerendia_nba_3_hcp_selected_features_data` |

The scorecard also gives each feature its 3.0 rank (1 = most important) and family. The ranks below come from there.

## 2. Overall result

We compared the 752 names with the 17,384 feature names in the 3.1 feature dictionary.

| Result | Features | What it means |
| --- | --- | --- |
| Same name in 3.1 | 350 | Nothing to do |
| Same feature, renamed | 71 | A clear naming rule links the 3.0 and 3.1 name (section 4) |
| Close substitute | 24 | 3.1 has a very similar feature, but the definition is a bit different (section 5) |
| Drug or diagnosis is in 3.1, but not this time window or measure | 61 | 3.1 redesigned these features (section 6) |
| Drug is not in 3.1 at all | 9 | The drug was dropped from the 3.1 event lists (section 7) |
| No clear 3.1 match | 237 | Mostly promotion, payer and HCP profile features that 3.1 rebuilt with new names (section 8) |
| **Total** | **752** | |

Sources: 3.0 list file and 3.1 feature dictionary above.

**Why so many names changed:** in 3.1 the claims, patient-event, promotion and payer features were rebuilt by new or reworked notebooks. Some only got a new naming style (for example the `_RX` / `_DX` / `_PX` ending was dropped), others got new time windows or new definitions.

## 3. The 350 with the same name

| 3.1 category | Features | Examples |
| --- | --- | --- |
| Claims | 270 | `TOTAL_RX_CLAIMS_IN_LAST_1_MONTH`, `TOTAL_RX_CLAIMS_FARXIGA_30_DAYS_SUPPLY_IN_LAST_1_MONTH` |
| Rx market | 50 | `KERENDIA_NBRX_IN_LAST_6_MONTH`, `TOTAL_HCP_NBRX_CLAIMS_SOB_ADD_ON_IN_LAST_3_MONTH` |
| Static HCP | 24 | `DIALYSIS_CENTER_FLAG`, `LONG_TERM_CARE_FACIL_FLAG` |
| Patient events | 3 | `TOTAL_EVENTS_TIME_180_DAYS_RX`, `TOTAL_EVENTS_TIME_360_DAYS_RX` |
| Derived in combine | 3 | `CALENDAR_MONTH`, `CALENDAR_YEAR` |

323 of the 350 are in the three categories that go through the statistical clean-up (Claims, Patient events, Rx market). The other 27 go straight to the model step anyway.

## 4. The 71 renamed features

Each rule was checked: the new name exists in the 3.1 dictionary.

| Naming rule (3.0 → 3.1) | Features | Example |
| --- | --- | --- |
| `_RX` / `_DX` / `_PX` ending dropped, double underscores made single | 27 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_90_DAYS_RX` → `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_90_DAYS` |
| `PRODUCT_GROUP_` dropped | 21 | `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_12_MONTH` → `TOTAL_HCP_NBRX_CLAIMS_KERENDIA_IN_LAST_12_MONTH` |
| `X_RX_TIME_MIN` → `MIN_EVENT_TIME_X_TIME_MIN` | 6 | `KERENDIA_RX_TIME_MIN` → `MIN_EVENT_TIME_KERENDIA_TIME_MIN` |
| `X_RX_FIRST_OCCURRENCE` → `MAX_EVENT_TIME_X_FIRST_OCCURRENCE` | 6 | `SYNJARDY_XR_RX_FIRST_OCCURRENCE` → `MAX_EVENT_TIME_SYNJARDY_XR_FIRST_OCCURRENCE` |
| `PATIENT_WITH_DX_GFR/UACR` → `PATIENT_WITH_TEST_GFR/UACR` | 5 | `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_4_WITH_OTHER_GLUCOSE_MGMT` → `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_TEST_GFR_STAGE_4_WITH_OTHER_GLUCOSE_MGMT` |
| Doubled `DAYS` removed | 3 | `SKEWNESS_TIME_180_DAYS_DAYS_RX` → `SKEWNESS_TIME_180_DAYS_RX` |
| `ALL_OTHERS` → `OTHERS` | 2 | `TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_ALL_OTHERS_IN_LAST_12_MONTH` → `TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_OTHERS_IN_LAST_12_MONTH` |
| `HCP_` added | 1 | `TIME_TO_ADOPT_FARXIGA` → `HCP_TIME_TO_ADOPT_FARXIGA` |

In 3.1 these 71 are in Patient events (42), Rx market (24) and Claims (5), so all of them go through the clean-up.

Full list, by 3.0 rank:

| 3.0 rank | 3.0 name | 3.1 name | 3.1 category | Rule |
| --- | --- | --- | --- | --- |
| 2 | `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_12_MONTH` | `TOTAL_HCP_NBRX_CLAIMS_KERENDIA_IN_LAST_12_MONTH` | Rx market | PRODUCT_GROUP_ dropped |
| 3 | `KERENDIA_RX_TIME_MIN` | `MIN_EVENT_TIME_KERENDIA_TIME_MIN` | Patient events | TIME_MIN → MIN_EVENT_TIME_ |
| 4 | `RUNNING_TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA` | `RUNNING_TOTAL_HCP_NBRX_CLAIMS_KERENDIA` | Rx market | PRODUCT_GROUP_ dropped |
| 15 | `TIME_TO_ADOPT_FARXIGA` | `HCP_TIME_TO_ADOPT_FARXIGA` | Rx market | HCP_ added |
| 27 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_90_DAYS_RX` | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_90_DAYS` | Patient events | ending / underscores |
| 29 | `RUNNING_TOTAL_HCP_TRX_CLAIMS_PRODUCT_GROUP_RYBELSUS` | `RUNNING_TOTAL_HCP_TRX_CLAIMS_RYBELSUS` | Rx market | PRODUCT_GROUP_ dropped |
| 34 | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DID_PROCEDURE_IN_LAST_360_DAYS_PX` | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DID_PROCEDURE_IN_LAST_360_DAYS` | Patient events | ending / underscores |
| 40 | `SYNJARDY_XR_RX_FIRST_OCCURRENCE` | `MAX_EVENT_TIME_SYNJARDY_XR_FIRST_OCCURRENCE` | Patient events | FIRST_OCCURRENCE → MAX_EVENT_TIME_ |
| 41 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_HYDROCHLOROTHIAZIDE_IN_LAST_360_DAYS_RX` | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_HYDROCHLOROTHIAZIDE_IN_LAST_360_DAYS` | Patient events | ending / underscores |
| 47 | `RUNNING_TOTAL_HCP_TRX_CLAIMS_PRODUCT_GROUP_TRULICITY` | `RUNNING_TOTAL_HCP_TRX_CLAIMS_TRULICITY` | Rx market | PRODUCT_GROUP_ dropped |
| 51 | `TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_ALL_OTHERS_IN_LAST_12_MONTH` | `TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_OTHERS_IN_LAST_12_MONTH` | Rx market | ALL_OTHERS → OTHERS |
| 56 | `ECHO_TESTS_PX_FIRST_OCCURRENCE` | `MAX_EVENT_TIME_ECHO_TESTS_FIRST_OCCURRENCE` | Patient events | FIRST_OCCURRENCE → MAX_EVENT_TIME_ |
| 67 | `CREATININE_OTHER_SOURCE_PX_TIME_MIN` | `MIN_EVENT_TIME_CREATININE_OTHER_SOURCE_TIME_MIN` | Patient events | TIME_MIN → MIN_EVENT_TIME_ |
| 73 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_ENTRESTO_IN_LAST_360_DAYS_RX` | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_ENTRESTO_IN_LAST_360_DAYS` | Patient events | ending / underscores |
| 85 | `NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_HEMOGLOBIN__GLYCOSYLATED__A1C__IN_LAST_90_DAYS_PX` | `NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_HEMOGLOBIN_GLYCOSYLATED_A1C_IN_LAST_90_DAYS` | Patient events | ending / underscores |
| 88 | `TOTAL_HCP_TRX_CLAIMS_PRODUCT_GROUP_METFORMIN_IN_LAST_12_MONTH` | `TOTAL_HCP_TRX_CLAIMS_METFORMIN_IN_LAST_12_MONTH` | Rx market | PRODUCT_GROUP_ dropped |
| 94 | `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_PROCEDURES_IN_LAST_12_MONTH_PX` | `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_PROCEDURES_IN_LAST_12_MONTH` | Patient events | ending / underscores |
| 101 | `SKEWNESS_TIME_180_DAYS_DAYS_RX` | `SKEWNESS_TIME_180_DAYS_RX` | Patient events | doubled DAYS removed |
| 120 | `RUNNING_TOTAL_HCP_TRX_CLAIMS_PRODUCT_GROUP_KERENDIA` | `RUNNING_TOTAL_HCP_TRX_CLAIMS_KERENDIA` | Rx market | PRODUCT_GROUP_ dropped |
| 124 | `TOTAL_HCP_NRX_CLAIMS_PRODUCT_GROUP_FARXIGA_BRAND_IN_LAST_12_MONTH` | `TOTAL_HCP_NRX_CLAIMS_FARXIGA_BRAND_IN_LAST_12_MONTH` | Rx market | PRODUCT_GROUP_ dropped |
| 126 | `RUNNING_TOTAL_HCP_NRX_CLAIMS_PRODUCT_GROUP_TRULICITY` | `RUNNING_TOTAL_HCP_NRX_CLAIMS_TRULICITY` | Rx market | PRODUCT_GROUP_ dropped |
| 138 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_180_DAYS_RX` | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_180_DAYS` | Patient events | ending / underscores |
| 143 | `AMILORIDE_HCL_RX_FIRST_OCCURRENCE` | `MAX_EVENT_TIME_AMILORIDE_HCL_FIRST_OCCURRENCE` | Patient events | FIRST_OCCURRENCE → MAX_EVENT_TIME_ |
| 184 | `TOTAL_HCP_NRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_3_MONTH` | `TOTAL_HCP_NRX_CLAIMS_KERENDIA_IN_LAST_3_MONTH` | Rx market | PRODUCT_GROUP_ dropped |
| 189 | `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_6_MONTH` | `TOTAL_HCP_NBRX_CLAIMS_KERENDIA_IN_LAST_6_MONTH` | Rx market | PRODUCT_GROUP_ dropped |
| 195 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_360_DAYS_RX` | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_360_DAYS` | Patient events | ending / underscores |
| 221 | `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_OZEMPIC_IN_LAST_3_MONTH` | `TOTAL_HCP_NBRX_CLAIMS_OZEMPIC_IN_LAST_3_MONTH` | Rx market | PRODUCT_GROUP_ dropped |
| 224 | `TOTAL_HOSPITALIZED_CLAIMS_ALL_PROCEDURES_IN_LAST_12_MONTH_PX` | `TOTAL_HOSPITALIZED_CLAIMS_ALL_PROCEDURES_IN_LAST_12_MONTH` | Patient events | ending / underscores |
| 234 | `PROTEINURIA_UNSPECIFIED_DX_TIME_MIN` | `MIN_EVENT_TIME_PROTEINURIA_UNSPECIFIED_TIME_MIN` | Patient events | TIME_MIN → MIN_EVENT_TIME_ |
| 238 | `SKEWNESS_TIME_360_DAYS_DAYS_RX` | `SKEWNESS_TIME_360_DAYS_RX` | Patient events | doubled DAYS removed |
| 295 | `RUNNING_TOTAL_HCP_NRX_CLAIMS_PRODUCT_GROUP_FARXIGA_BRAND` | `RUNNING_TOTAL_HCP_NRX_CLAIMS_FARXIGA_BRAND` | Rx market | PRODUCT_GROUP_ dropped |
| 296 | `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_3_MONTH` | `TOTAL_HCP_NBRX_CLAIMS_KERENDIA_IN_LAST_3_MONTH` | Rx market | PRODUCT_GROUP_ dropped |
| 304 | `RUNNING_TOTAL_HCP_NRX_CLAIMS_PRODUCT_GROUP_KERENDIA` | `RUNNING_TOTAL_HCP_NRX_CLAIMS_KERENDIA` | Rx market | PRODUCT_GROUP_ dropped |
| 313 | `SKEWNESS_TIME_180_DAYS_DAYS_PX` | `SKEWNESS_TIME_180_DAYS_PX` | Patient events | doubled DAYS removed |
| 321 | `TOTAL_HCP_NBRX_CLAIMS_INDICATION_GROUP_ALL_OTHERS_IN_LAST_6_MONTH` | `TOTAL_HCP_NBRX_CLAIMS_INDICATION_GROUP_OTHERS_IN_LAST_6_MONTH` | Rx market | ALL_OTHERS → OTHERS |
| 324 | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DID_PROCEDURE_IN_LAST_180_DAYS_PX` | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DID_PROCEDURE_IN_LAST_180_DAYS` | Patient events | ending / underscores |
| 365 | `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_4_WITH_OTHER_GLUCOSE_MGMT` | `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_TEST_GFR_STAGE_4_WITH_OTHER_GLUCOSE_MGMT` | Claims | DX_GFR/UACR → TEST_ |
| 370 | `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_PROCEDURES_IN_LAST_6_MONTH_PX` | `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_PROCEDURES_IN_LAST_6_MONTH` | Patient events | ending / underscores |
| 384 | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DIAGNOSED_IN_LAST_360_DAYS_DX` | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DIAGNOSED_IN_LAST_360_DAYS` | Patient events | ending / underscores |
| 396 | `NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_CREATININE__OTHER_SOURCE_IN_LAST_180_DAYS_PX` | `NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_CREATININE_OTHER_SOURCE_IN_LAST_180_DAYS` | Patient events | ending / underscores |
| 413 | `HEMOGLOBIN_GLYCOSYLATED_A1C_PX_TIME_MIN` | `MIN_EVENT_TIME_HEMOGLOBIN_GLYCOSYLATED_A1C_TIME_MIN` | Patient events | TIME_MIN → MIN_EVENT_TIME_ |
| 415 | `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_JARDIANCE_IN_LAST_1_MONTH` | `TOTAL_HCP_NBRX_CLAIMS_JARDIANCE_IN_LAST_1_MONTH` | Rx market | PRODUCT_GROUP_ dropped |
| 433 | `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_4_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_12_MONTH` | `TOTAL_RX_CLAIMS_PATIENT_WITH_TEST_GFR_STAGE_4_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_12_MONTH` | Claims | DX_GFR/UACR → TEST_ |
| 458 | `TOTAL_HCP_NRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_12_MONTH` | `TOTAL_HCP_NRX_CLAIMS_KERENDIA_IN_LAST_12_MONTH` | Rx market | PRODUCT_GROUP_ dropped |
| 465 | `NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_ECHO_TESTS_IN_LAST_180_DAYS_PX` | `NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_ECHO_TESTS_IN_LAST_180_DAYS` | Patient events | ending / underscores |
| 494 | `TOTAL_HOSPITALIZED_CLAIMS_ALL_PROCEDURES_IN_LAST_6_MONTH_PX` | `TOTAL_HOSPITALIZED_CLAIMS_ALL_PROCEDURES_IN_LAST_6_MONTH` | Patient events | ending / underscores |
| 516 | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DIAGNOSED_IN_LAST_180_DAYS_DX` | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DIAGNOSED_IN_LAST_180_DAYS` | Patient events | ending / underscores |
| 534 | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_HYPERTENSIVE_HEART_AND_CHRONIC_KIDNEY_DISEASE_WITH_HEART_FAILURE_AND_STAGE_1_THROUGH_STAGE_4_CHRONIC_IN_LAST_360_DAYS_DX` | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_HYPERTENSIVE_HEART_AND_CHRONIC_KIDNEY_DISEASE_WITH_HEART_FAILURE_AND_STAGE_1_THROUGH_STAGE_4_CHRONIC_IN_LAST_360_DAYS` | Patient events | ending / underscores |
| 542 | `ECHO_TESTS_PX_TIME_MIN` | `MIN_EVENT_TIME_ECHO_TESTS_TIME_MIN` | Patient events | TIME_MIN → MIN_EVENT_TIME_ |
| 545 | `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_1_MONTH` | `TOTAL_HCP_NBRX_CLAIMS_KERENDIA_IN_LAST_1_MONTH` | Rx market | PRODUCT_GROUP_ dropped |
| 562 | `ATHEROSCLEROSIS_OF_RENAL_ARTERY_DX_FIRST_OCCURRENCE` | `MAX_EVENT_TIME_ATHEROSCLEROSIS_OF_RENAL_ARTERY_FIRST_OCCURRENCE` | Patient events | FIRST_OCCURRENCE → MAX_EVENT_TIME_ |
| 563 | `TOTAL_HCP_NRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_1_MONTH` | `TOTAL_HCP_NRX_CLAIMS_KERENDIA_IN_LAST_1_MONTH` | Rx market | PRODUCT_GROUP_ dropped |
| 564 | `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_DIAGNOSIS_IN_LAST_6_MONTH_DX` | `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_DIAGNOSIS_IN_LAST_6_MONTH` | Patient events | ending / underscores |
| 567 | `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_DIAGNOSIS_IN_LAST_1_MONTH_DX` | `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_DIAGNOSIS_IN_LAST_1_MONTH` | Patient events | ending / underscores |
| 574 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_DILTIAZEM_HCL_IN_LAST_90_DAYS_RX` | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_DILTIAZEM_HCL_IN_LAST_90_DAYS` | Patient events | ending / underscores |
| 585 | `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_JARDIANCE_IN_LAST_12_MONTH` | `TOTAL_HCP_NBRX_CLAIMS_JARDIANCE_IN_LAST_12_MONTH` | Rx market | PRODUCT_GROUP_ dropped |
| 596 | `NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_ECHO_TESTS_IN_LAST_360_DAYS_PX` | `NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_ECHO_TESTS_IN_LAST_360_DAYS` | Patient events | ending / underscores |
| 613 | `TOTAL_HCP_TRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_6_MONTH` | `TOTAL_HCP_TRX_CLAIMS_KERENDIA_IN_LAST_6_MONTH` | Rx market | PRODUCT_GROUP_ dropped |
| 616 | `TOTAL_HCP_TRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_12_MONTH` | `TOTAL_HCP_TRX_CLAIMS_KERENDIA_IN_LAST_12_MONTH` | Rx market | PRODUCT_GROUP_ dropped |
| 625 | `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_4_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_6_MONTH` | `TOTAL_RX_CLAIMS_PATIENT_WITH_TEST_GFR_STAGE_4_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_6_MONTH` | Claims | DX_GFR/UACR → TEST_ |
| 657 | `TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_1_MONTH_DX` | `TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_1_MONTH` | Patient events | ending / underscores |
| 659 | `DIABETES_MELLITUS_DUE_TO_UNDERLYING_CONDITION_WITH_DIABETIC_NEPHROPATHY_DX_TIME_MIN` | `MIN_EVENT_TIME_DIABETES_MELLITUS_DUE_TO_UNDERLYING_CONDITION_WITH_DIABETIC_NEPHROPATHY_TIME_MIN` | Patient events | TIME_MIN → MIN_EVENT_TIME_ |
| 665 | `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_UACR_STAGE_3_WITH_OTHER_GLUCOSE_MGMT` | `RUNNING_TOTAL_RX_CLAIMS_PATIENT_WITH_TEST_UACR_STAGE_3_WITH_OTHER_GLUCOSE_MGMT` | Claims | DX_GFR/UACR → TEST_ |
| 677 | `SECONDARY_SIDEROBLASTIC_ANEMIA_DUE_TO_DISEASE_DX_FIRST_OCCURRENCE` | `MAX_EVENT_TIME_SECONDARY_SIDEROBLASTIC_ANEMIA_DUE_TO_DISEASE_FIRST_OCCURRENCE` | Patient events | FIRST_OCCURRENCE → MAX_EVENT_TIME_ |
| 692 | `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_UACR_STAGE_3_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_6_MONTH` | `TOTAL_RX_CLAIMS_PATIENT_WITH_TEST_UACR_STAGE_3_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_6_MONTH` | Claims | DX_GFR/UACR → TEST_ |
| 693 | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_PROTEINURIA__UNSPECIFIED_IN_LAST_180_DAYS_DX` | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_PROTEINURIA_UNSPECIFIED_IN_LAST_180_DAYS` | Patient events | ending / underscores |
| 708 | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_ATHEROSCLEROSIS_OF_RENAL_ARTERY_IN_LAST_90_DAYS_DX` | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_ATHEROSCLEROSIS_OF_RENAL_ARTERY_IN_LAST_90_DAYS` | Patient events | ending / underscores |
| 709 | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_PROTEINURIA__UNSPECIFIED_IN_LAST_360_DAYS_DX` | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_PROTEINURIA_UNSPECIFIED_IN_LAST_360_DAYS` | Patient events | ending / underscores |
| 715 | `REVISION_OPEN_ARTERIOVENOUS_FISTULA_WITHOUT_THROMBECTOMY_AUTOGENOUS_OR_NONAUTOGENOUS_DIALYSIS_GR_PX_FIRST_OCCURRENCE` | `MAX_EVENT_TIME_REVISION_OPEN_ARTERIOVENOUS_FISTULA_WITHOUT_THROMBECTOMY_AUTOGENOUS_OR_NONAUTOGENOUS_DIALYSIS_GR_FIRST_OCCURRENCE` | Patient events | FIRST_OCCURRENCE → MAX_EVENT_TIME_ |
| 722 | `TOTAL_HOSPITALIZED_CLAIMS_ALL_PROCEDURES_IN_LAST_1_MONTH_PX` | `TOTAL_HOSPITALIZED_CLAIMS_ALL_PROCEDURES_IN_LAST_1_MONTH` | Patient events | ending / underscores |
| 733 | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_HYPERTENSIVE_CHRONIC_KIDNEY_DISEASE_WITH_STAGE_5_CHRONIC_KIDNEY_DISEASE_OR_END_STAGE_RENAL_DISEASE_IN_LAST_180_DAYS_DX` | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_HYPERTENSIVE_CHRONIC_KIDNEY_DISEASE_WITH_STAGE_5_CHRONIC_KIDNEY_DISEASE_OR_END_STAGE_RENAL_DISEASE_IN_LAST_180_DAYS` | Patient events | ending / underscores |

## 5. The 24 close substitutes

3.1 has a feature on the same topic, but its definition is a bit different. All 24 are in the three clean-up categories (Rx market 14, Patient events 10).

| Change | Features | Why it is not the same |
| --- | --- | --- |
| Indication group "T2D + CKD + CVD" → "T2D + CKD + HF" | 14 | 3.1 has no CVD indication group; HF is the nearest group, but it covers other patients |
| `CHANGE_IN_FREQ_...` → `LOGRATIO_FREQ_...` | 10 | Both measure a change in how often something happens, but 3.1 uses a log ratio; the 3.0 formula was not compared |

| 3.0 rank | 3.0 name | 3.1 name | 3.1 category | Change |
| --- | --- | --- | --- | --- |
| 11 | `TOTAL_HCP_NBRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_CVD_IN_LAST_12_MONTH` | `TOTAL_HCP_NBRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_HF_IN_LAST_12_MONTH` | Rx market | CVD group → HF group |
| 52 | `TOTAL_HCP_NRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_CVD_IN_LAST_6_MONTH` | `TOTAL_HCP_NRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_HF_IN_LAST_6_MONTH` | Rx market | CVD group → HF group |
| 125 | `RUNNING_TOTAL_HCP_NBRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_CVD` | `RUNNING_TOTAL_HCP_NBRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_HF` | Rx market | CVD group → HF group |
| 177 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_FUROSEMIDE_IN_LAST_3_MONTH_RX` | `LOGRATIO_FREQ_FUROSEMIDE_IN_LAST_3_MONTH` | Patient events | CHANGE_IN_FREQ → LOGRATIO_FREQ |
| 179 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_ECHO_TESTS_IN_LAST_3_MONTH_PX` | `LOGRATIO_FREQ_ECHO_TESTS_IN_LAST_3_MONTH` | Patient events | CHANGE_IN_FREQ → LOGRATIO_FREQ |
| 259 | `TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_CVD_IN_LAST_12_MONTH` | `TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_HF_IN_LAST_12_MONTH` | Rx market | CVD group → HF group |
| 275 | `RUNNING_TOTAL_HCP_NRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_CVD` | `RUNNING_TOTAL_HCP_NRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_HF` | Rx market | CVD group → HF group |
| 278 | `TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_CVD_IN_LAST_3_MONTH` | `TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_HF_IN_LAST_3_MONTH` | Rx market | CVD group → HF group |
| 291 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_ECHO_TESTS_IN_LAST_6_MONTH_PX` | `LOGRATIO_FREQ_ECHO_TESTS_IN_LAST_6_MONTH` | Patient events | CHANGE_IN_FREQ → LOGRATIO_FREQ |
| 292 | `TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_CVD_IN_LAST_6_MONTH` | `TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_HF_IN_LAST_6_MONTH` | Rx market | CVD group → HF group |
| 311 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_CHRONIC_KIDNEY_DISEASE_STAGE_3_UNSPECIFIED_IN_LAST_6_MONTH_DX` | `LOGRATIO_FREQ_CHRONIC_KIDNEY_DISEASE_STAGE_3_UNSPECIFIED_IN_LAST_6_MONTH` | Patient events | CHANGE_IN_FREQ → LOGRATIO_FREQ |
| 316 | `RUNNING_TOTAL_HCP_NRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_CVD_AND_HF` | `RUNNING_TOTAL_HCP_NRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_HF` | Rx market | CVD group → HF group |
| 331 | `TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_CVD_AND_HF_IN_LAST_12_MONTH` | `TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_HF_IN_LAST_12_MONTH` | Rx market | CVD group → HF group |
| 397 | `TOTAL_HCP_NRX_CLAIMS_INDICATION_GROUP_CKD_AND_CVD_IN_LAST_12_MONTH` | `TOTAL_HCP_NRX_CLAIMS_INDICATION_GROUP_CKD_AND_HF_IN_LAST_12_MONTH` | Rx market | CVD group → HF group |
| 425 | `RUNNING_TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_CVD` | `RUNNING_TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_HF` | Rx market | CVD group → HF group |
| 448 | `RUNNING_TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_CVD_AND_HF` | `RUNNING_TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_HF` | Rx market | CVD group → HF group |
| 460 | `TOTAL_HCP_NBRX_CLAIMS_INDICATION_GROUP_CKD_AND_CVD_IN_LAST_6_MONTH` | `TOTAL_HCP_NBRX_CLAIMS_INDICATION_GROUP_CKD_AND_HF_IN_LAST_6_MONTH` | Rx market | CVD group → HF group |
| 490 | `TOTAL_HCP_NRX_CLAIMS_INDICATION_GROUP_T2D_AND_CVD_IN_LAST_12_MONTH` | `TOTAL_HCP_NRX_CLAIMS_INDICATION_GROUP_T2D_AND_HF_IN_LAST_12_MONTH` | Rx market | CVD group → HF group |
| 518 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_NIFEDIPINE_ER_IN_LAST_6_MONTH_RX` | `LOGRATIO_FREQ_NIFEDIPINE_ER_IN_LAST_6_MONTH` | Patient events | CHANGE_IN_FREQ → LOGRATIO_FREQ |
| 572 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_MIXED_HYPERLIPIDEMIA_IN_LAST_6_MONTH_DX` | `LOGRATIO_FREQ_MIXED_HYPERLIPIDEMIA_IN_LAST_6_MONTH` | Patient events | CHANGE_IN_FREQ → LOGRATIO_FREQ |
| 598 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_LABETALOL_HCL_IN_LAST_3_MONTH_RX` | `LOGRATIO_FREQ_LABETALOL_HCL_IN_LAST_3_MONTH` | Patient events | CHANGE_IN_FREQ → LOGRATIO_FREQ |
| 623 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_END_STAGE_RENAL_DISEASE_IN_LAST_3_MONTH_DX` | `LOGRATIO_FREQ_END_STAGE_RENAL_DISEASE_IN_LAST_3_MONTH` | Patient events | CHANGE_IN_FREQ → LOGRATIO_FREQ |
| 658 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_PROTEINURIA_UNSPECIFIED_IN_LAST_3_MONTH_DX` | `LOGRATIO_FREQ_PROTEINURIA_UNSPECIFIED_IN_LAST_3_MONTH` | Patient events | CHANGE_IN_FREQ → LOGRATIO_FREQ |
| 731 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_PROTEINURIA_UNSPECIFIED_IN_LAST_6_MONTH_DX` | `LOGRATIO_FREQ_PROTEINURIA_UNSPECIFIED_IN_LAST_6_MONTH` | Patient events | CHANGE_IN_FREQ → LOGRATIO_FREQ |

## 6. The 61 where 3.1 has the drug or diagnosis, but not this window or measure

**Why:** 3.1 redesigned the patient-event features. For each drug, diagnosis, procedure and lab test, 3.1 now has:

* patient counts for the last 90, 180 and 360 days (`NUM_OF_PATIENTS_THE_HCP_..._IN_LAST_90/180/360_DAYS`)
* change in frequency for 3 and 6 months (`LOGRATIO_FREQ_..._IN_LAST_3/6_MONTH`)
* recency and first occurrence (`MIN_EVENT_TIME_...`, `MAX_EVENT_TIME_...`)

The 3.0 monthly counts (`FREQ_..._IN_LAST_1/2/3/6/12_MONTH`), the 30- and 60-day patient counts, and the 1- and 2-month change features no longer exist. Checked in the 3.1 dictionary: no feature starts with `FREQ_`, every `LOGRATIO_FREQ_` feature is 3 or 6 months (608 each), and every `NUM_OF_PATIENTS_THE_HCP_` day-window feature is 90, 180 or 360 days (608 each). Example: `ECHO_TESTS` has 8 features in 3.1 (3 patient counts, 2 change features, recency, first occurrence and "first claim before window"), but no `FREQ_ECHO_TESTS_IN_LAST_12_MONTH_PX`.

By 3.0 family: Rx claims 26, Dx claims 12, Lab claims 8, Kerendia prior writing 8, Px claims 7.

Highest-ranked examples:

| 3.0 rank | 3.0 name | 3.0 family |
| --- | --- | --- |
| 22 | `FREQ_ALBUMIN__URINE_EG_MICROALBUMIN_QUANTITATIVE_IN_LAST_12_MONTH_PX` | Lab claims |
| 49 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_RYBELSUS_IN_LAST_30_DAYS_RX` | Rx claims (other products) |
| 62 | `FREQ_ENTRESTO_IN_LAST_12_MONTH_RX` | Rx claims (other products) |
| 63 | `GFR_LAB_DATA_FIRST_OCCURRENCE` | Lab claims |
| 90 | `NUM_OF_PATIENTS_THE_HCP_DID_LAB_TEST_GFR_IN_LAST_360_DAYS_LAB_DATA` | Lab claims |
| 109 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_PROPRANOLOL_HCL_IN_LAST_2_MONTH_RX` | Rx claims (other products) |
| 142 | `FREQ_ACUTE_ON_CHRONIC_SYSTOLIC_CONGESTIVE_HEART_FAILURE_IN_LAST_12_MONTH_DX` | Dx / comorbidity claims |
| 153 | `FREQ_METOPROLOL_TART_IN_LAST_12_MONTH_RX` | Rx claims (other products) |
| 164 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_METOPROLOL_TART_IN_LAST_2_MONTH_RX` | Rx claims (other products) |
| 167 | `FREQ_UNSPECIFIED_SYSTOLIC_CONGESTIVE_HEART_FAILURE_IN_LAST_6_MONTH_DX` | Dx / comorbidity claims |
| 180 | `FREQ_ACUTE_ON_CHRONIC_COMBINED_SYSTOLIC_CONGESTIVE_AND_DIASTOLIC_CONGESTIVE_HEART_FAILURE_IN_LAST_12_MONTH_DX` | Dx / comorbidity claims |
| 185 | `FREQ_ECHO_TESTS_IN_LAST_12_MONTH_PX` | Px claims |

Note on GFR: the 3.0 lab features use `GFR`, while the 3.1 patient-event lab features use `EGFR_TEST_ALL_LOINC_VARIANTS` (for example `NUM_OF_PATIENTS_THE_HCP_DID_LAB_TEST_EGFR_TEST_ALL_LOINC_VARIANTS_IN_LAST_360_DAYS`). This may be the same test with a wider code list, but it was not checked.

## 7. The 9 where the drug is not in 3.1

No 3.1 feature mentions these drugs. All are from the 3.0 family "Rx claims (other products)".

| 3.0 rank | 3.0 name |
| --- | --- |
| 20 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_LISINOPRIL_HCTZ_IN_LAST_360_DAYS_RX` |
| 60 | `TELMISARTAN_HCTZ_RX_FIRST_OCCURRENCE` |
| 226 | `VICTOZA_3_PAK_RX_TIME_MIN` |
| 520 | `FREQ_AMLODIP_BES_OROLMESAR_IN_LAST_3_MONTH_RX` |
| 641 | `FREQ_AMLODIP_BES_ORVALSAR_IN_LAST_2_MONTH_RX` |
| 681 | `FREQ_DILTIAZEM_SR_IN_LAST_6_MONTH_RX` |
| 701 | `EDARBYCLOR_RX_TIME_MIN` |
| 750 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_EDARBYCLOR_IN_LAST_60_DAYS_RX` |
| 752 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_EDARBYCLOR_IN_LAST_1_MONTH_RX` |

## 8. The 237 with no clear 3.1 match

| 3.0 family | Features | What it is, and what 3.1 has instead |
| --- | --- | --- |
| Rx claims (other products) | 84 | Mail-order channel, rejected/reversed claims, `ADD_ON_TO_..._AND_COMBOS` and old `PRODUCT_GROUP_` drug groups that do not exist in 3.1 (for example `TOTAL_HCP_TRX_CLAIMS_ADD_ON_TO_ACE_INHIBITORS_AND_COMBOS_IN_LAST_12_MONTH`; 3.1 has `..._ADD_ON_TO_ARB_...`, `..._ADD_ON_TO_CCB_...`) |
| Kerendia prior writing (NBRx/NPS) | 61 | Rejected/reversed Kerendia claims, Kerendia formulary (`PCT_PLANS_KERENDIA_...`), Farxiga share without a window (3.1 only has it with a window: `PERC_FARXIGA_NBRX_SHARE_1M`, `_3M`, `_6M`, `_12M`, plus `..._ALL_...` and `..._CKD_...` versions) |
| Promotion - F2F/calls | 32 | `TOTAL_F2F_IN_LAST_n_MONTH`, `BHO_TOTAL_F2F_...`; 3.1 rebuilt field activity (for example `FLD_INT_F2F_1M`, `_3M`, `_6M`) |
| Market access / payer | 30 | Medicare Part D pay type and Farxiga formulary (`PCT_PLANS_FARXIGA_...`); 3.1 has new FTP and Copay features |
| Other / unmapped | 11 | DTC publisher features (Health Union, Healthline, Sharecare, Facebook/Instagram), `HCP_AGE` |
| Promotion - digital/email | 10 | WebMD DTC, banner and HQ email exposure, speaker programs |
| HCP profile / affiliation | 4 | `AFFL_COUNT`, `BUILDING_COLOCATION_FLAG`, `HCP_SPECIALTY_NEPH`, `HCP_SPECIALTY_PCP` |
| Dx / comorbidity claims | 3 | For example `PCT_TOTAL_DX_PATIENTS_CV_KD_IN_LAST_12_MONTH` |
| Lab claims | 2 | For example `PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_UNKNOWN_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_1_MONTH` (3.1 has this feature for numbered GFR stages, but not for "stage unknown"; "stage unknown" appears in other 3.1 features, for example `PCT_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_UNKNOWN_IN_LAST_12_MONTH`) |
| **Total** | **237** | |

**45 of these 237 were in the 3.0 top 100:**

| 3.0 rank | 3.0 name |
| --- | --- |
| 1 | `TOTAL_F2F_IN_LAST_6_MONTH` |
| 6 | `AFFL_COUNT` |
| 7 | `RUNNING_TOTAL_HCP_RX_REJECTED_KERENDIA_CLAIMS` |
| 8 | `NUM_HCPS_IN_BUILDING` |
| 9 | `TOTAL_F2F_IN_LAST_5_MONTH` |
| 10 | `TOTAL_HCP_RX_MAIL_ORDER_CHANNEL_CLAIMS_IN_LAST_12_MONTH` |
| 13 | `TOTAL_F2F_IN_LAST_3_MONTH` |
| 14 | `TOTAL_F2F_IN_LAST_4_MONTH` |
| 18 | `TOTAL_F2F_IN_LAST_2_MONTH` |
| 23 | `PERC_FARXIGA_NBRX_SHARE` |
| 24 | `PCT_PLANS_KERENDIA_COVERED_LOOKBACK` |
| 28 | `PCT_PLANS_KERENDIA_UNRESTRICTED` |
| 32 | `DTC_PROMOTION_HEALTH_UNION_TOTAL_IMPRESSIONS` |
| 35 | `RUNNING_TOTAL_HCP_TRX_CLAIMS_INDICATION_GROUP_CVD` |
| 36 | `TOTAL_HCP_TRX_CLAIMS_ADD_ON_TO_ACE_INHIBITORS_AND_COMBOS_IN_LAST_12_MONTH` |
| 38 | `TOTAL_HCP_RX_REVERSED_KERENDIA_CLAIMS_IN_LAST_6_MONTH` |
| 39 | `TOTAL_HCP_TRX_CLAIMS_ADD_ON_TO_DIURETICS_AND_COMBOS_IN_LAST_12_MONTH` |
| 42 | `TOTAL_HCP_NRX_CLAIMS_ADD_ON_TO_GLIPIZIDE_IN_LAST_6_MONTH` |
| 43 | `TOTAL_F2F_IN_LAST_1_MONTH` |
| 46 | `BUILDING_COLOCATION_FLAG` |
| 48 | `RUNNING_TOTAL_HCP_TRX_CLAIMS_ADD_ON_TO_ACE_INHIBITORS_AND_COMBOS` |
| 50 | `HCP_SPECIALTY_NEPH` |
| 53 | `TOTAL_HCP_RX_REJECTED_KERENDIA_CLAIMS_IN_LAST_12_MONTH` |
| 54 | `TOTAL_HCP_RX_BETA_BLOCKERS_MAIL_ORDER_CHANNEL_CLAIMS_IN_LAST_6_MONTH` |
| 58 | `RUNNING_TOTAL_HCP_TRX_CLAIMS_SPEC_NEPHROLOGY` |
| 61 | `RUNNING_TOTAL_HCP_NRX_CLAIMS_ADD_ON_TO_ACE_INHIBITORS_AND_COMBOS` |
| 64 | `TOTAL_HCP_TRX_CLAIMS_PRODUCT_GROUP_EMPAGLIFLOZIN_JARDIANCE_COMBOS_IN_LAST_12_MONTH` |
| 65 | `RUNNING_TOTAL_HCP_TRX_CLAIMS_PRODUCT_GROUP_METFORMIN` |
| 69 | `PCT_PLANS_KERENDIA_COVERED_ST_OR_PA_ST` |
| 70 | `RUNNING_TOTAL_HCP_TRX_CLAIMS_ADD_ON_TO_DIURETICS_AND_COMBOS` |
| 71 | `PCT_TOTAL_DX_PATIENTS_CV_KD_IN_LAST_12_MONTH` |
| 72 | `RUNNING_TOTAL_HCP_TRX_CLAIMS_PRODUCT_GROUP_ACE_INHIBITORS_AND_COMBOS` |
| 74 | `TOTAL_HCP_RX_CLAIMS_WITH_IMMEDIATE_CONTINUE_SOURCE_OF_BUSINESS_IN_LAST_12_MONTH` |
| 75 | `RUNNING_TOTAL_HCP_RX_CLAIMS_OF_DRUG_CLASS_KERENDIA` |
| 76 | `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_VITAMIN_D_ANALOG_DRUG_IN_LAST_12_MONTH` |
| 81 | `PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_UNKNOWN_WITH_OTHER_GLUCOSE_MGMT_IN_LAST_1_MONTH` |
| 82 | `TOTAL_HCP_RX_ACE_ARBS_ATYPICAL_CHANNEL_CLAIMS_IN_LAST_3_MONTH` |
| 83 | `TOTAL_HCP_RX_REVERSED_CALCIUM_CHANNEL_BLOCKERS_CLAIMS_IN_LAST_12_MONTH` |
| 84 | `DIGITAL_BANNER_TACTIC_EXPOSURE_IN_LAST_3_MONTH` |
| 86 | `TOTAL_HCP_NBRX_CLAIMS_HYPERTENSION_HTN_IN_LAST_12_MONTH` |
| 87 | `RUNNING_TOTAL_HCP_NRX_CLAIMS_PAY_TYPE_THIRD_PARTY` |
| 89 | `PCT_PLANS_KERENDIA_SPECIALTY_LOOKBACK` |
| 92 | `TOTAL_HCP_RX_REJECTED_KERENDIA_CLAIMS_IN_LAST_6_MONTH` |
| 95 | `TOTAL_HCP_TRX_CLAIMS_ADD_ON_TO_MINERALOCORTICOID_RECEPTOR_ANTAGONISTS_IN_LAST_6_MONTH` |
| 100 | `PCT_PLANS_KERENDIA_COVERED_ST_OR_PA_ST_LOOKBACK` |

## 9. What this means for the statistical clean-up

The new rule is: the clean-up only looks at Claims, Patient events and Rx market, and it never removes a 3.0 feature.

| Group | Features | Effect in the clean-up |
| --- | --- | --- |
| Same name, in the 3 categories | 323 | Protected |
| Same name, other categories | 27 | Not checked by the clean-up anyway (go straight to the model) |
| Renamed (all in the 3 categories) | 71 | Protected, under the 3.1 name |
| Close substitutes (all in the 3 categories) | 24 | Protected only if the team agrees (open point 1) |
| No exact 3.1 version | 307 (61 + 9 + 237) | Cannot be protected; the 3.0 feature does not exist in 3.1 |

So **394 features can be protected for sure** (323 + 71), or **418** if the close substitutes are included.

## 10. Open points

**1. Close substitutes (24 features)**

* Background: 14 use the HF indication group instead of the CVD group, and 10 use the 3.1 change formula instead of the 3.0 one.
* Options: (a) protect them as the nearest equivalent; (b) treat them as new 3.1 features that must pass the clean-up like any other.
* Effect: (a) keeps up to 24 more features out of the clean-up; (b) is stricter but may drop features close to important 3.0 ones (the best one was rank 11 in 3.0).

**2. Values not compared yet**

* Background: the match was done only on names. A renamed feature could still be built in a different way.
* Options: compare 3.0 and 3.1 values for the 71 renamed features on the same doctors and month, or accept the name match.
* Effect: comparing takes a short extra check but confirms that "same, renamed" really means the same values.

**3. Important 3.0 features with no 3.1 version**

* Background: 45 of the 3.0 top 100 have no clear 3.1 match (section 8). Most are promotion, payer and HCP profile features, which go straight to the model in their new 3.1 form. The rest are claims features such as rejected/reversed Kerendia claims (rank 7) and mail-order claims (rank 10).
* Options: (a) accept that 3.1 has a different feature set; (b) rebuild the most important missing ones in feature engineering.
* Effect: (b) needs feature-engineering work and a new Combine run before feature selection.
