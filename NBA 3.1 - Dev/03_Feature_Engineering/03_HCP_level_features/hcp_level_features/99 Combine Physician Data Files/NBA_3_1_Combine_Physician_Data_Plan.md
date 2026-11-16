# Combine Physician Data (99) in NBA 3.1: Plan

**For:** Wenjie. **Version:** 2026-11-16.  
**Notebook:** `hcp_level_features/99 Combine Physician Data Files/(Clone) 99_Combine_Physician_Data`. It still holds the 3.0 code (189 cells). The **first 3.1 iteration** is designed in section 6 and **not written into the notebook yet**.  
**Inputs assessed:** HCP claims run `full_2026_11_13` [S8]; HCP-level, patient and promotional tables in the 3.1 volume as of 2026-11-12/13 [S9–S11].  
**Closes:** readiness plan open point 9 (combine step not switched to cohorts) [S12].

The plan tells the story in order: where to find things (1), a summary (2), what the 3.0 notebook did (3), what changes for 3.1 and why (4), the inputs family by family (5), what the first 3.1 iteration does (6), what we still do not have (7), the checks (8) and the decisions (9).

Every number has a source in brackets, for example [S8]. "My check" means counted on those tables for this plan (2026-11-13, updated 2026-11-16 on `full_2026_11_13`).

---

## 1. Where to find things

Volume root: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/`. Workspace root: `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_1_develop_pg/NBA 3.1 - Dev/`.

| Ref | What | Path |
| --- | --- | --- |
| S1 | 3.0 combine notebook: the code in the clone before 2026-11-13 (189 cells, last run 2025-11-28) | Clone of the 3.0 notebook `99_Combine_Physician_Data`; this work does not touch the original |
| S2 | 3.0 inputs | `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/` (for example `claim_rx_monthly`, `final_claims_monthly`, `rx_recency_features`, `kerendia_nba_3_hcp_model_hq_email_features_for_inference`); cohort anchor `.../query_output/hcp_model_inference_anchor_dates.csv` |
| S3 | 3.0 output | `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_selected_features_data` |
| S4 | The 752 model features of 3.0 | `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/input_files/Kerendia_NBA_3_feature_list_752_features.csv` |
| S5 | The 277 claims features among the 752 | `Feature Analysis/NBA_3_1_HCP_Claims_Selected_Features_277.csv` |
| S6 | Cohort files | `kerendia_nba_3_1_volume/cohorts/claims/cohorts.parquet` (offset 0), `kerendia_nba_3_1_volume/cohorts/promotional/cohorts.parquet` (offset 17) |
| S7 | 3.1 HCP universe | `kerendia_nba_3_1_volume/HCP_Universe_without_call_hcps/` |
| S8 | 3.1 claims features NB01–NB06 | `kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/full_2026_11_13/hcp_claims/` |
| S9 | 3.1 HCP-level features | `kerendia_nba_3_1_volume/notebook_output/hcp_features/` |
| S10 | 3.1 patient features (3.0 "feature accelerator") | `kerendia_nba_3_1_volume/notebook_output/patient_features/{rx, dx, px, lab, addon}/` |
| S11 | 3.1 promotional features | `kerendia_nba_3_1_volume/notebook_output/{hq_email_nba_3_1, digital_engagement_nba_3_1, high_intent_signals_nba_3_1, field_activity_nba_3_1, dtc_nba_3_1}/` |
| S12 | HCP claims readiness plan | `03_Feature_Engineering/03_HCP_level_features/hcp_level_features/Alignment_Markdowns/Strategy_and_Execution/NBA_3_1_HCP_Level_Features_AI_Readiness.md` |
| S13 | Settings and helpers | `03_Feature_Engineering/03_HCP_level_features/00_cohort_config` |
| S14 | Git branches searched (after `git fetch`, 2026-11-12) | `combine`, `dev/hcp-claims-features`, `dev/promotional-features`, `dev/patient-features`, `dev/claims-comorbidity-competitor-features`, `dev/nbrx-nrx-trx-features`, `dev/mmit-features`, `analysis/hcp-universe-revamp`, `dev/stage-branch`, `main` |
| S15 | Output of the 3.1 notebook | `kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/<run>/hcp_combined/` |

---

## 2. Summary

| Topic | 3.0 | 3.1 | Source |
| --- | --- | --- | --- |
| Purpose | Inference table: one cohort `I01` (lookback end 2026-09-30) | Training table: 28 cohorts c1–c28 (24 Training, 2 Testing, 2 Holdout) | S2, S6 |
| HCPs and rows | 3.0 universe; stored output 222,125 rows | 294,726 HCPs (my check: distinct valid `PROVIDER_ID`) x 28 cohorts = 8,252,328 rows | S1, S7 |
| Join key | `PROVIDER_ID` + calendar month (`SVC_DT_M`); promotional tables on `BHID_<cohort>` | `PROVIDER_ID` + cohort id (`COHORT_ID`), one key `HCP_COHORT_ID = PROVIDER_ID_c<n>` | S1 |
| Inputs | 48 tables (12 accelerator, 2 hospitalization, 34 HCP / promotional / claims), all 3.0 | 36 HCP tables to join (6 claims, 6 HCP-level, 15 patient, 9 promotional); 3 DTC tables not joined yet | S1, S8–S11 |
| 3.0 families with no 3.1 table | – | HCP profile (static), SDoH (census), comorbidity, Kerendia claims, channel, colocation, additional indication, DRG, geo, clickstream; FTP and copay only for inference | S14 |
| Model features | 752 | 370 of the 752 exist by name in the 3.1 inputs: 270 claims, 100 HCP-level and patient. 382 not found | S4, S5, my check |
| Missing features | Added as constant 0 | Not added; listed in a report | S1 |
| Output | Overwrites the 3.0 production table | Delta table by `COHORT_SET` in the 3.1 run folder | S3, S15 |

**Status:** first 3.1 iteration designed (section 6), not yet written into the notebook and not run. It will join every 3.1 table that exists today and report what is missing. The open points in section 7 decide how complete the table becomes.

---

## 3. Where we started: the 3.0 notebook

| Step | 3.0 cells | What it did | Source |
| --- | --- | --- | --- |
| Setup | 2 | `%run` of the 3.0 `00_connection` | S1 |
| Load | 3, 6, 111 | 48 tables from the 3.0 `ops_pipeline/notebook_output/`, most `*_for_inference` | S1, S2 |
| Skeleton | 13–28 | 3.0 universe x cohort anchor file; `SVC_DT_M` = month of `LOOKBACK_END_DATE`; BHID added | S1 |
| NPI to provider | 29–36 | `claim_rx_monthly`, `hcp_paid_search`, `nbrx_shares_4_features` mapped from NPI to `PROVIDER_ID` | S1 |
| Part 1: claims and HCP-level | 37–74 | 23 tables joined on `PROVIDER_ID` + `SVC_DT_M`; the 5 Rx totals repeated in `final_claims_monthly` dropped (cell 45) | S1 |
| Part 2: promotional | 75–101 | 8 tables on `BHID_<cohort>`; geo on BHID; DTC through a DMA-to-ZIP file; key then rebuilt as `PROVIDER_ID_<cohort>` | S1 |
| Part 3: accelerator | 102–126 | rx / dx / px / lab recency, first occurrence, frequency, hospitalization on `HCP_COHORT_ID`; columns kept only if their name contains `_rx`, `_dx`, `_px` or `_lab` | S1 |
| Combine | 127–152 | Three parts joined; names upper-cased; specialty one-hot (`HCP_SPECIALTY_*`); 2 Kerendia / SGLT2 ratios; `AGE` renamed `HCP_AGE` | S1 |
| Calendar | 153–157 | `CALENDAR_MONTH`, `CALENDAR_YEAR`, `MONTHS_SINCE_KER_LAUNCH` (launch 2021-07-01) | S1 |
| Feature list | 158–171 | Keep the 752 [S4]; **missing ones added as constant 0**; string and date columns dropped; names cleaned | S1 |
| Impute and write | 172–187 | Median for HCP age, experience and 22 SDoH columns; 9999 for recency (`TIME_MIN`) and `TIME_TO_ADOPT_FARXIGA`; −9999 for first occurrence; 0 for the rest; cast to float; 8 renames back to the model names; **overwrite** of the 3.0 table [S3] | S1 |

Result of the last 3.0 run: 222,125 rows, 25,323 columns after the combine [S1, cell 128].

---

## 4. What changes for 3.1 and why

| Topic | 3.0 | 3.1 (first iteration) | Why | Source |
| --- | --- | --- | --- | --- |
| Settings | 3.0 `00_connection`; Spark `min`, `max` and `sum = 0` hide the Python built-ins | 3.1 `00_cohort_config`; Python built-ins kept | One config for the 3.1 pipeline; it also stops any write outside the 3.1 volume | S13 |
| HCP universe | 3.0 inference universe | `HCP_Universe_without_call_hcps`, 294,726 HCPs (my check) | 3.1 universe decision (X1) | S7 |
| Cohorts | 1 inference cohort | c1–c28 from the claims cohort file; c1: `lookback_end_date` 2024-05-01, prediction month 2024-07-01; c28: 2026-08-01, prediction month 2026-10-01 | The 3.1 model is trained on 28 monthly cohorts | S6 |
| Join key | Calendar month | Cohort id | The promotional cohort file has other dates for the same id (c1: lookback end 2024-06-17, offset 17) but the same prediction month (2024-07-01). A date join would mix them | S6 |
| Cohort column name | – | Read as `COHORT_ID`, lower case `c1`–`c28` | The 3.1 tables use 3 names: `COHORT_ID` (claims, field events, iRep, samples, message, MSL), `COHORT` (HQ email, field core, digital, high intent, DTC, patient features), `cohort_id` (prior writing, adoption) | S8–S11 |
| NPI mapping | NPI to provider for 3 tables | Not needed | Every 3.1 HCP table already has `PROVIDER_ID` | S8–S11 |
| Calendar-month tables | Joined on the month | NBRx / NRx / TRx and competitor shares joined on `PROVIDER_ID` + the cohort month of the claims cohort file | These 4 tables have no cohort id (`PROVIDER_ID`, `SVC_DT_M`; 46 months in NBRx, my check) | S9 |
| ID and date columns | Kept from several tables (3.0 output had `PULL_DT` and `BHID` twice) | Dropped from every input, kept once from the skeleton | Every 3.1 table carries its own copies (`COHORT_MONTH`, `OFFSET_DAYS`, `CUTOFF_DATE`, `SVC_DT_M`, `PULL_DT`, `DATASET`, `COHORT_SET`, ...) | S8 |
| Repeated claims columns | 5 Rx totals of `final_claims_monthly` dropped | Same 5 dropped from NB04 (`TOTAL_RX_CLAIMS_IN_LAST_{1,3,6,12}_MONTH`, `RUNNING_TOTAL_RX_CLAIMS`) | They are also in NB01; my check found no other name in two tables | S8, my check |
| Patient feature columns | Kept only if the name contains `_rx`, `_dx`, `_px`, `_lab` | All feature columns kept | 3.1 names do not carry the suffix on every column: for example `MIN_EVENT_TIME_ACARBOSE_TIME_MIN` in `rx_recency_features`. The 3.0 filter would drop them | S10 |
| Kerendia / SGLT2 ratio | From `TOTAL_HCP_RX_CLAIMS_OF_DRUG_CLASS_{KERENDIA,SGLT2}_*` | From NB01 `TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_{1,12}_MONTH` / `TOTAL_RX_CLAIMS_SGLT2_IN_LAST_{1,12}_MONTH` | The 3.0 source columns are in no 3.1 table; the NB01 columns exist (my check). Same meaning to confirm (open point 7.7) | S8 |
| Specialty one-hot | From the values found in the data | Not built | No 3.1 HCP profile table (open point 7.1). When it comes: a fixed value list, so every cohort set gets the same columns | S1 |
| Calendar features | From `SVC_DT_M` | From the cohort month (same meaning: month of the lookback end) | No calendar month in the skeleton any more | S6 |
| Feature list | 752, missing ones = 0 | Mode `752`: keep what exists, list what is missing, no 0-fill. Mode `all`: every feature | Retraining and feature selection run again on 3.1 (readiness open point 7); a 0-filled column looks like data | S4, S12 |
| Imputation | Medians on all rows | Same rules; medians from the training cohorts only (exact median) | Medians from validation and backtest rows would leak into training. Today none of the median columns exists in 3.1 (no HCP profile, no SDoH) | S1 |
| Name rules | `TIME_TO_ADOPT_FARXIGA` | Same rule; the 3.1 adoption table calls it `HCP_TIME_TO_ADOPT_FARXIGA` | Not renamed yet (open point 7.8) | S9 |
| Output | Overwrite of the 3.0 table; snapshots in `ops_pipeline_snapshots/` | `<run>/hcp_combined/`, Delta partitioned by `COHORT_SET`, written one set at a time; an existing set is not overwritten without the overwrite parameter | Protects 3.0 production; NB01 alone is 8.09M rows x 4,681 columns [S12], so all sets at once are too large | S3, S15 |
| Check cells | Many `display` / `count` / `printSchema` cells (for example cells 8–12, 41–52) | One input check before the join and one QC section at the end | Each check reads the full tables | S1 |

---

## 5. Inputs, family by family

Key columns read from the tables; writers from the Git search [S14].

| Family | 3.0 table | 3.1 table | Key in the 3.1 table | Writer (branch) | Planned in the first iteration |
| --- | --- | --- | --- | --- | --- |
| Claims NB01–NB06 | `claim_rx_monthly`, `provider_claim_lab_monthly_ZS`, `provider_claim_diagnosis_monthly`, `final_claims_monthly`, `kerendia_nba_3_0_claim_rx_nps_monthly`, `kerendia_nba_3_0_claim_eligible_patient` | `provider_claim_rx_monthly_cohort`, `provider_claim_lab_monthly_cohort`, `provider_claim_diagnosis_monthly_cohort`, `final_claims_monthly_cohort`, `claim_rx_nps_monthly_cohort`, `provider_claim_eligible_patient_cohort` [S8] | `PROVIDER_ID`, `COHORT_ID` | NB01–NB06 (dev/hcp-claims-features) | Joined |
| Prior writing | `kerendia_prior_writing` | `hcp_features/kerendia_prior_writing` (53 columns) | `PROVIDER_ID`, `cohort_id` | `03_HCP_Level_Features/10_kerendia_prior_writing` (dev/claims-comorbidity-competitor-features), claims cohorts | Joined |
| Adoption | `adoption_features_inv_far` | `hcp_features/adoption_features` (19 columns, 28 cohorts) | `PROVIDER_ID`, `cohort_id` | `03_HCP_Level_Features/11_adoption_features` (same branch), claims cohorts | Joined |
| NBRx / NRx / TRx | `nbrx / nrx / trx_features_w_provider_id` | `hcp_features/{nbrx, nrx, trx}_features` (1,266 columns each) | `PROVIDER_ID`, `SVC_DT_M` (calendar month) | Not found: the notebooks `05_NBRx_NRx_TRx/26–28` on every branch write to the 3.0 volume | Joined by cohort month; writer open (7.2) |
| Competitor shares | `perc_competitor_nbrx_shares` | `hcp_features/competitor_share_features` (76 columns) | `PROVIDER_ID`, `SVC_DT_M` | Not found in any branch | Joined by cohort month; writer open (7.2) |
| Patient features | 12 accelerator + 2 hospitalization tables | `rx_{recency, first_occurrence, frequency}`, `dx_` and `px_{recency, first_occurrence, frequency, hospitalization}`, `lab_{recency, first_occurrence, frequency}`, `addon/claims_addon_patient_features` [S10] | `PROVIDER_ID`, `COHORT` (c1–c28 checked on `rx_recency_features`) | `03_patient_features/Final Notebooks/` (dev/patient-features) | Joined (15 tables); cohort file open (7.4) |
| HQ email | `hq_email_features_for_inference` | `hq_email_nba_3_1/..._hq_email_features.parquet` (23 columns) | `PROVIDER_ID`, `COHORT` | `HQ Emails/15_promotional_features_HQ_Emails_new` (dev/promotional-features) | Joined |
| Digital paid media | `hcp_paid_search` | `digital_engagement_nba_3_1/..._digital_paid_media_features.parquet` (152 columns) | `PROVIDER_ID`, `COHORT` | `Digital_Engagement/24_Features_Digital_NBA31` | Joined |
| High-intent signals | – (new) | `high_intent_signals_nba_3_1/..._high_intent_features.parquet` (37 columns) | `PROVIDER_ID`, `COHORT` | `High_Intent_Signal_Features/25_Features_High_Intent_Signals_NBA31` | Joined |
| Field: calls / F2F | `call_features_bhoid`, `call_features` | `field_activity_nba_3_1/..._field_core_features.parquet` (59 columns) | `PROVIDER_ID`, `COHORT` | `F2F/f2f_feature` | Joined |
| Field: speaker, iRep, samples | `speaker_program`, `irep_features`, `samples_features` | `..._field_events_` (23), `..._field_irep_` (26), `..._field_sample_features.parquet` (36) | `PROVIDER_ID`, `COHORT_ID` | `Speaker Programs/`, `Irep emails/`, `Samples/` | Joined |
| Field: message, MSL | – (new) | `..._field_message_` (9), `..._field_msl_features.parquet` (8) | `PROVIDER_ID`, `COHORT_ID` | `Message features/`, `MSL/` | Joined |
| DTC | `DTC_PROMOTION_for_inference` + DMA-to-ZIP file | `dtc_nba_3_1/kerendia_nba_3_1_dtc_{zip, social_dma, search_state}_features.parquet` | Market x cohort (`DMA_CODE`, `COHORT`); no HCP key | `DTC/34_promotional_features_DTC` | **Not joined** (7.3) |
| Clickstream (CLM) | `clickstream_features` | None | – | Only the 3.0 notebook `18_promotional_ClickStream_features` | Missing (7.5) |
| FTP, copay | `ftp_features_v2`, `copay_features` | None in the 3.1 volume | – | `FTP_and_Copay/19_ftp_features` writes an inference table (one cohort, BHID key); `22_copay_features` keeps the 3.0 output name | Missing (7.5) |
| HCP profile and others | `phy_static_features`, `sdoh` (census), `claim_comorbidity`, `kerendia_claims`, `channel`, `colocation_flag`, `additional_hcp_level_features`, `drg_kerendia / farxiga / jardiance`, `geo_features` | None | – | No 3.1 notebook in any branch (comorbidity and channel: analysis documents only; MMIT: EDA only) | Missing (7.1) |
| Digital phase 1 / 2 | – | Not written (`notebook_output/nba_3_1_digital_phase1/`, `_phase2/` missing in both volumes) | – | `51_digital_nba_phase1_features`, `53_digital_nba_phase2_high_intent_features` | Not needed if replaced by digital paid media and high intent (7.6) |

### 5.1 The 752 model features in the 3.1 inputs

My check: the 752 names [S4] (the file has 753 rows; one is `HCP_COHORT_ID`) compared with the column names of the 3.1 inputs, written the 3.0 way (upper case, `__` as `_`). Claims tables from `full_2026_11_13` [S8]; other tables from the 3.1 volume [S9–S11].

| Where the feature is found | Model features | Example features |
| --- | ---: | --- |
| NB01 Rx claims | 172 | `PCT_TOTAL_REJECTED_RX_CLAIMS_JARDIANCE_IN_LAST_6_MONTH`, `PCT_TOTAL_RX_CLAIMS_ACE_OR_ARB_90_DAYS_SUPPLY_IN_LAST_3_MONTH` |
| NB03 diagnosis claims | 3 | `TOTAL_DX_CLAIMS_STAGE_UNSPECIFIED_IN_LAST_3_MONTH`, `TOTAL_DX_CLAIMS_WITH_PATIENT_NO_NEW_STAGE_IN_LAST_6_MONTH` |
| NB04 combined claims | 82 | `PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_3_WITH_COMBO_DRUG_IN_LAST_1_MONTH`, `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_4_WITH_DPP_IV_IN_LAST_12_MONTH` |
| NB05 new patient starts | 14 | `PCT_TOTAL_PATIENTS_START_ACE_OR_ARB_IN_LAST_3_MONTH` |
| NB06 eligible patients | 1 | `RUNNING_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_4` |
| Prior writing | 5 | `KERENDIA_NBRX_IN_LAST_1_MONTH`, `KERENDIA_NBRX_IN_LAST_6_MONTH` |
| NBRx / NRx / TRx | 24 / 30 / 38 | `RUNNING_TOTAL_HCP_NBRX_CLAIMS_GENDER_F`, `RUNNING_TOTAL_HCP_NBRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_CVD` |
| Patient features | 3 | `TOTAL_EVENTS_TIME_180_DAYS_RX`, `TOTAL_EVENTS_TIME_360_DAYS_RX`, `TOTAL_EVENTS_TIME_180_DAYS_PX` |
| **Found** | **370** | 270 claims features (the NB rows add up to 272 because 2 found names are in both NB01 and NB04), 100 others |
| Not found | 382 | Among them: the 22 SDoH (`ACS_PCT_*`, `ACS_PER_CAPITA_INC_ZC`), `HCP_AGE`, `HCP_EXPERIENCE`, the 2 `HCP_SPECIALTY_*`, `TIME_TO_ADOPT_FARXIGA`, and the 7 claims features still removed by X5 [S12] (the 2 DPP-IV features are back in `full_2026_11_13`) |

Why so many are not found: whole families have no 3.1 table (section 5), and the 3.1 patient and promotional notebooks were rewritten with new column names (for example HQ email, field activity, and recency names such as `MIN_EVENT_TIME_ACARBOSE_TIME_MIN`). Created by the notebook itself and also in the 752: `CALENDAR_MONTH`, `CALENDAR_YEAR`, `MONTHS_SINCE_KER_LAUNCH`, `RATIO_KERENDIA_TO_SGLT2_CLAIMS_IN_LAST_12_MONTHS`.

---

## 6. What the first 3.1 iteration does

| Section in the notebook | What it does |
| --- | --- |
| 1. Settings (planned) | `%run` of `00_cohort_config`; run parameters (source run `full_2026_11_13`, output run, cohort sets, feature mode `752` or `all`, overwrite); paths |
| 2. Inputs | One list of the 39 3.1 tables: path, format, cohort column, cohort calendar, columns to drop; the 3.0 families without a 3.1 table; the rename rules |
| 3. Helpers | Read an input for one cohort set as `PROVIDER_ID`, `COHORT_ID` and its features; cohort-month join for the calendar-month tables |
| 4. Skeleton | 3.1 universe x 28 claims cohorts, with `HCP_COHORT_ID`, `COHORT_MONTH`, `PREDICTION_MONTH`, `DATASET`, `COHORT_SET`; stops if rows ≠ HCPs x 28 |
| 5. Input check | Per input: found or not, columns, cohorts present, duplicate keys, rows without a provider ID. Stops if a claims table is missing, a key is duplicated or a feature name is in two tables |
| 6. Feature list | Mode `752`: present / missing report per feature (saved in `hcp_combined/_reports/`); missing ones are not added |
| 7. Medians | Exact medians from the training cohorts (c1–c24) for HCP age, experience and SDoH, if the columns exist |
| 8. Combine | Per `COHORT_SET`: left joins on `PROVIDER_ID` + `COHORT_ID`, ratio and calendar features, 3.0 imputation rules, string and date columns dropped, float cast, 3.0 name cleaning (and the 8 model renames in mode `752`), write |
| 9. QC | Rows and distinct `HCP_COHORT_ID` per set against the skeleton; match rate per input; input rows of HCPs outside the universe; nulls after imputation |
| 10. Open points | What the notebook does not cover yet (section 7) |

---

## 7. What we still do not have

| # | Open point | Background | Options | Effect | Who |
| --- | --- | --- | --- | --- | --- |
| 7.1 | 3.0 families with no 3.1 table: HCP profile (age, experience, specialty), SDoH, comorbidity, Kerendia claims, channel, colocation, additional indication, DRG, geo | No 3.1 notebook in any branch [S14] | Rebuild for c1–c28; drop; the 3.0 tables cannot be used (one inference cohort) | Most of the 384 missing model features; no medians, no specialty one-hot | HCP / promotional owners (Sehar, Saurabh) |
| 7.2 | Writer of NBRx / NRx / TRx and competitor shares | The 3.1 tables exist [S9] but the notebooks in Git write to the 3.0 volume and read the 3.0 universe | Find the writer, or switch `26–28` to the 3.1 volume and universe | Cannot confirm their universe and LRx source; joined by cohort month for now | Owners of dev/nbrx-nrx-trx-features, dev/claims-comorbidity-competitor-features |
| 7.3 | DTC link to the HCP | DTC tables are DMA / state x cohort; 3.0 used the HCP ZIP from `geo_features` | HCP ZIP / DMA / state from the 3.1 universe or a 3.1 geo table | DTC features not in the table | Promotional owners |
| 7.4 | Cohort file of the patient features | Claims (month end) or promotional (17th) changes which months a cohort covers | Confirm with the writer | If promotional, c1 ends 2024-06-17 instead of the claims lookback month May 2024 (`lookback_end_date` 2024-05-01) | Owner of dev/patient-features |
| 7.5 | Clickstream, FTP and copay for c1–c28 | Only 3.0 or inference versions exist [S14] | Finish the FTP / copay revamp; rebuild clickstream | Features missing | Promotional owners |
| 7.6 | Digital phase 1 / 2 | Notebooks exist, tables do not | Confirm that digital paid media and high intent replace them | None if replaced | Promotional owners |
| 7.7 | Kerendia / SGLT2 ratio source | 3.0 source columns not in 3.1; NB01 has `TOTAL_RX_CLAIMS_KERENDIA_*` and `TOTAL_RX_CLAIMS_SGLT2_*` | Accept the NB01 columns; or find the 3.0 source | Ratio values may differ from 3.0 | 3.0 owner |
| 7.8 | Renamed features | 3.1 notebooks renamed columns (for example `HCP_TIME_TO_ADOPT_FARXIGA` for `TIME_TO_ADOPT_FARXIGA`) | Rename map 3.1 → 3.0 names per family (the notebook has an empty one); or select on the 3.1 names | Without it, renamed features show as missing in mode `752` | Family owners |
| 7.9 | Rows without a provider ID | 3,094 rows (NB01, NB04), 949 (NB03), 3,001 (NB06) [S12, open point 8] | Fill from the provider ID of the 3.1 Rx input (readiness proposal) | Those rows are lost in the join; the input check counts them | HCP claims (us) |
| 7.10 | NB05 input | ~~NB05 still reads the 3.0 input `Rx_05`~~ Resolved 2026-11-13: PJ03 now writes `rx_nps_pull` (3.1 Rx pull with history from 2021), NB05 reads it; Kerendia, Mounjaro, Zepbound and Wegovy starts are counted. `full_2026_11_13` has the fix | Done | HCP claims (us) |
| 7.11 | 3.1 feature list | The 752 are the 3.0 model features [S4] | Feature selection on mode `all` (readiness open point 7) | Until then mode `752` is a report, not the model input | Raman |
| 7.12 | Two calendars in one row | Claims c1 uses the lookback month May 2024 (`lookback_end_date` 2024-05-01); promotional c1 ends 2024-06-17; both predict 2024-07-01 and are joined on the same cohort id | Accept (same prediction month); or move one family to the other calendar | Promotional windows end later than claims windows | Team decision |
| 7.13 | Config defaults | `HCP_UNIVERSE_PATH` is still the 3.0 universe and `HCP_LATEST_FULL_RUN` is `full_2026_11_05` [S13] | Update the config (readiness open point 15) | None for this notebook: it sets its own universe and run | HCP claims (us) |

---

## 8. Checks

| Check | Expected | Where |
| --- | --- | --- |
| Skeleton | rows = 294,726 x 28; one row per `HCP_COHORT_ID` | Section 4 |
| Inputs | every claims table found; no duplicate key; no feature name in two tables | Section 5 |
| Joins | rows per set = skeleton rows per set | Section 9 |
| Match rate | share of skeleton rows found in each input, per run | Section 9 |
| Claims values | equal to the NB01–NB06 values for the trace HCPs (all cohorts) | To add after the first run |
| Promotional values | promotional c<n> lands on claims c<n> (one HCP by hand) | To add after the first run |
| Feature list | present / missing report saved | Section 6 |
| Imputation | medians from training only; 0 nulls after imputation | Sections 7, 9 |
| Output | 7 `COHORT_SET` groups | Section 9 |

---

## 9. Decisions

| ID | Question | Proposal | Planned for the first iteration |
| --- | --- | --- | --- |
| D1 | Training (c1–c28), inference or both | Training first; inference later with the same code and one cohort | Training |
| D2 | Join key | `PROVIDER_ID` + `COHORT_ID`; `HCP_COHORT_ID = PROVIDER_ID_c<n>` | Planned |
| D3 | Families without a 3.1 table | Per family: rebuild or drop (7.1, 7.5, 7.6) | Open; reported as missing |
| D4 | Feature list | 3.1 selection; until then the 752 only as a report, no 0-fill | Planned (mode `752` default, mode `all` available) |
| D5 | Imputation statistics | Medians from training cohorts only | Planned |
| D6 | Output | `<run>/hcp_combined/`, Delta by `COHORT_SET`, plus a column list | Planned |
| D7 | Rows without a provider ID | Fix in NB01–NB06 (7.9) | Open; counted |
| D8 | Where the notebook lives | This folder, in this Git folder (not the `combine` branch) | Agreed (user, 2026-11-13) |
| D9 | DTC link to the HCP | 7.3 | Open; DTC not joined |
| D10 | Calendar-month tables | Join on the cohort month of the claims cohort file | Planned |

---

