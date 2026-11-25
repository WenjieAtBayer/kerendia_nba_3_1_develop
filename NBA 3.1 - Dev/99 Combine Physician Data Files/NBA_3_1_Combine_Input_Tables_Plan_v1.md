# NBA 3.1 – Combine physician data: input tables to join (Dev - v1)

**Status (2026-11-24):** inventory of every feature table the 3.1 combine notebook must join, built from the notebooks in `kerendia_nba_3_1_develop/NBA 3.1 - Dev - v1` (Git folder on `combine`, commit `5071439`). The write path of each feature notebook was read from its code and every output was opened in the 3.1 volume. Companion of `NBA_3_1_Combine_Input_Tables_Plan.md` (same exercise on `kerendia_nba_3_1_develop_pg/NBA 3.1 - Dev`). No combine code written yet.

**Roots**
* `VOL` = `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/`
* `NO` = `VOL/notebook_output/`
* `DEV` = `VOL/hcp_level_model/dev_pipeline/notebook_output/`

---

## 1. What is in Dev - v1

Unlike the `_pg` folder, **v1 holds every feature notebook in one place**, including the ones that were only on dev branches:

| Area | Notebooks in v1 |
| --- | --- |
| Claims NB01-NB07 | `03_Feature_Engineering/03_HCP_level_features/hcp_level_features/0{1..7} .../` + `00_cohort_config`, `00_load_uc_inputs` |
| HCP level | `03_HCP_Level_Features/`: `09_claim_comorbidity`, `10_kerendia_prior_writing`, `11_adoption_features`, `26/27/28_Features_*_nba31`, `31_Competitor_drugs_NBRX_share`, `31_Competitor_drugs_NBRx_share_nba31`, `32_EDA_HCP_Features_nba31`, `36_market_event_features`, `hcp_features_config.py` |
| Static | `06_Physician_Static_Features/07_...`, `07_Census_Sdoh_Features/08_...`, `09_Colocation_Features/33_...` |
| Patient | `03_patient_features/Final Notebooks/`: RX, DX, PX, LAB, `01_Additional_Patient_Features` |
| Promotional personal | `04_Promotional_Features/personal_promotional_features/`: F2F, Speaker Programs, Irep emails, Message, MSL, Samples |
| Promotional non-personal | `non_personal_promotional_features/`: HQ Emails, Digital_Engagement, High_Intent_Signal_Features, DTC, OE (`35_OE_Promotional_Features_NBA31`) |
| Not 3.1-ready | `05_NBRx_NRx_TRx/26-28` and root `04_Promotional_Features/14-34` (3.0 code in the `_pg` review; v1 copies not re-read), `FTP_and_Copay/19, 22`, digital `13/14/50/51/53` |

At least 18 notebooks have different code from the `_pg` copy (NB01, NB03-NB05, NB07, 00_cohort_config, 00_Write_HCP_Inputs_31, 10, 11, DTC, paid media, HQ email, high intent, and the F2F, iRep, message, samples and speaker field notebooks); some notebooks could not be compared because the `_pg` files are stored in another format. The write paths read from the v1 code point to the tables already in the volume (section 3); whether those outputs were written by the v1 version of the code was not checked.

## 2. Join key

One row per HCP x claims cohort, `HCP_COHORT_ID = <PROVIDER_ID>_c<n>`, cohorts `c1`-`c28`. Checked today: all 46 tables of section 3 hold exactly `c1`-`c28`.

Skeleton: HCP universe `VOL/HCP_Universe_without_call_hcps` (294,727 HCPs, from the 2026-11-19 check) x 28 = 8,252,356 rows.

| Cohort column | Families |
| --- | --- |
| `COHORT_ID` | claims NB01-NB06, field events / iRep / message / MSL / sample |
| `cohort_id` | static, comorbidity, competitor NBRx share, market events, prior writing, adoption, NBRx / NRx / TRx, competitor share |
| `COHORT` | patient, field core / account call / core account, HQ email, paid media, high intent, DTC, OE |

Claims have no `HCP_COHORT_ID`: build `concat(PROVIDER_ID, '_', COHORT_ID)`.

## 3. Tables to join (46)

Rows, total columns (incl. key / metadata), cohorts and last write checked in the volume on 2026-11-24. "Writes to" is the path in the v1 code.

### 3.1 Claims (6) – Delta

v1 code: `OUTPUT_PATH = hcp_output_path(<table>)` = `DEV/<RUN_NAME>/hcp_claims/<table>` (`00_cohort_config`; `RUN_NAME` comes from the job parameter `RUN_OUTPUT_DIR`). Latest full run in the volume: `full_2026_11_13`.

| # | Table | Notebook | Rows | Cols | Last write |
| --- | --- | --- | --- | --- | --- |
| 1 | `provider_claim_rx_monthly_cohort` | NB01 | 8,089,535 | 4,681 | 2026-11-14 |
| 2 | `provider_claim_lab_monthly_cohort` | NB02 | 5,166,454 | 152 | 2026-11-14 |
| 3 | `provider_claim_diagnosis_monthly_cohort` | NB03 | 7,588,997 | 122 | 2026-11-14 |
| 4 | `final_claims_monthly_cohort` | NB04 | 8,089,535 | 3,164 | 2026-11-14 |
| 5 | `claim_rx_nps_monthly_cohort` | NB05 | 8,088,324 | 172 | 2026-11-14 |
| 6 | `provider_claim_eligible_patient_cohort` | NB06 | 8,086,528 | 226 | 2026-11-14 |

Key `PROVIDER_ID` + `COHORT_ID`. One row per key and the null `PROVIDER_ID` rows (D13) are from the 2026-11-19 check, not re-run. `DEV/hcp_claims_features/` (top level) uses the old `..._offset7` cohort ids: not used.

### 3.2 Patient events (15) – Delta

v1 code writes to `NO/patient_features/<family>/` (checked for RX and add-on; the DX / PX / LAB path strings were not fully resolved). Both copies exist with the same rows, columns and cohorts:

| # | Table | Rows | Cols | Last write `NO` | Last write `DEV` |
| --- | --- | --- | --- | --- | --- |
| 7 | `rx/rx_first_occurrence_features` | 8,056,166 | 402 | 2026-11-03 | 2026-11-09 |
| 8 | `rx/rx_frequency_features` | 8,245,160 | 1,294 | 2026-11-03 | 2026-11-09 |
| 9 | `rx/rx_recency_features` | 8,046,833 | 281 | 2026-11-03 | 2026-11-09 |
| 10 | `dx/dx_first_occurrence_features` | 7,992,786 | 339 | 2026-11-03 | 2026-11-07 |
| 11 | `dx/dx_frequency_features` | 8,163,428 | 1,204 | 2026-11-03 | 2026-11-08 |
| 12 | `dx/dx_recency_features` | 7,851,283 | 263 | 2026-11-03 | 2026-11-08 |
| 13 | `dx/dx_hospitalization_features` | 8,163,428 | 13 | 2026-11-03 | 2026-11-08 |
| 14 | `px/px_first_occurrence_features` | 7,846,216 | 164 | 2026-11-03 | 2026-11-08 |
| 15 | `px/px_frequency_features` | 8,126,328 | 534 | 2026-11-03 | 2026-11-08 |
| 16 | `px/px_recency_features` | 7,622,534 | 129 | 2026-11-03 | 2026-11-09 |
| 17 | `px/px_hospitalization_features` | 8,126,328 | 13 | 2026-11-03 | 2026-11-08 |
| 18 | `lab/lab_first_occurrence_features` | 5,373,514 | 12 | 2026-11-03 | 2026-11-08 |
| 19 | `lab/lab_frequency_features` | 5,714,576 | 24 | 2026-11-03 | 2026-11-08 |
| 20 | `lab/lab_recency_features` | 4,776,999 | 27 | 2026-11-03 | 2026-11-08 |
| 21 | `addon/claims_addon_patient_features` | 8,095,859 | 44 | 2026-11-03 | 2026-11-07 |

Key `PROVIDER_ID` + `HCP_COHORT_ID`, column `COHORT`. The 2026-11-19 row hash found `NO` and `DEV` identical. Proposed: read from `NO`, where the v1 code writes (Q1). Not joined: `*_censor_report`, `_test_sample_*`.

### 3.3 Rx market (6) – Delta

Key `PROVIDER_ID` + `HCP_COHORT_ID`, column `cohort_id`, 8,252,356 rows = keys.

| # | Table | Notebook (v1) | Writes to | Cols | Last write |
| --- | --- | --- | --- | --- | --- |
| 22 | `nbrx_features` | `26_Features_NBRx_nba31` | `DEV/hcp_features_v7_cohort_aligned/` | 1,033 | 2026-11-17 |
| 23 | `nrx_features` | `27_Features_NRx_nba31` | same | 1,033 | 2026-11-17 |
| 24 | `trx_features` | `28_Features_TRx_nba31` | same | 1,033 | 2026-11-17 |
| 25 | `competitor_share_features` | `31_Competitor_drugs_NBRx_share_nba31` | same | 190 | 2026-11-17 |
| 26 | `kerendia_prior_writing` | `10_kerendia_prior_writing` | `HCP_FEATURES_OUT_31` (`hcp_features_config.py`: `{DEV_PIPELINE}/notebook_output/hcp_features`; output found in `DEV/hcp_features/`) | 29 | 2026-11-19 |
| 27 | `adoption_features` | `11_adoption_features` | `DEV/hcp_features/` | 20 | 2026-11-18 |

The v1 code settles which NBRx version is final: `hcp_features_v7_cohort_aligned` ("V7 + aligned SWITCH_FROM/ADD_ON_TO + V7 pruning"). `hcp_features_v7_cohort/` and the old monthly `hcp_features/{nbrx,nrx,trx,competitor_share}_features` (no cohort) are not used. The `05_NBRx_NRx_TRx/26-28` notebooks are not used (3.0 code in the `_pg` copy; the v1 copies were not re-read).

### 3.4 Static HCP (6) – Delta, `DEV/hcp_features/`

Key `PROVIDER_ID` + `HCP_COHORT_ID`, column `cohort_id`, 8,252,356 rows = keys.

| # | Table | Notebook (v1) | Cols | Last write |
| --- | --- | --- | --- | --- |
| 28 | `physician_attributes_features` | `06_Physician_Static_Features/07_physician_attributes_features` | 27 | 2026-11-19 |
| 29 | `census_features` | `07_Census_Sdoh_Features/08_census_features` | 41 | 2026-11-19 |
| 30 | `colocation_idn_features` | `09_Colocation_Features/33_colocation_idn_features` | 22 | 2026-11-19 |
| 31 | `claim_comorbidity` | `03_HCP_Level_Features/09_claim_comorbidity` | 19 | 2026-11-17 |
| 32 | `competitor_nbrx_share` | `03_HCP_Level_Features/31_Competitor_drugs_NBRX_share` | 55 | 2026-11-17 |
| 33 | `market_event_features` | `03_HCP_Level_Features/36_market_event_features` (`NB_OUT_31/hcp_features/`) | 8 | 2026-11-17 |

`DEV/static_features/{07_phy_static_features, ...}` (key `PROVIDER_ID` only, 314,920 rows) are not used: in `07_physician_attributes_features` that path is `DRAFT_OUTPUT_PATH`, "read only, for comparison".

### 3.5 Field activity (8) – Parquet, `NO/field_activity_nba_3_1/`

v1 code: `INTERMEDIATE_DIR = V31/notebook_output/field_activity_nba_3_1`. Key `PROVIDER_ID` + `HCP_COHORT_ID`, 8,252,328 rows = keys (placeholder HCP `'0'` missing).

| # | Table (`kerendia_nba_3_1_hcp_model_..._features.parquet`) | Notebook (v1) | Cohort col | Cols | Last write |
| --- | --- | --- | --- | --- | --- |
| 34 | `field_core` | `F2F/f2f_feature` | `COHORT` | 59 | 2026-11-06 |
| 35 | `field_account_call` | `F2F/f2f_feature` (`ACCT_OUTPUT_PATH`) | `COHORT` | 10 | 2026-11-11 |
| 36 | `field_core_account` | `F2F/f2f_feature` (`COMBINED_OUTPUT_PATH`) | `COHORT` | 63 | 2026-11-11 |
| 37 | `field_events` | `Speaker Programs/speaker_program_feature` | `COHORT_ID` | 23 | 2026-11-06 |
| 38 | `field_irep` | `Irep emails/irep_email_feature` | `COHORT_ID` | 26 | 2026-11-06 |
| 39 | `field_message` | `Message features/message_feature` | `COHORT_ID` | 9 | 2026-11-06 |
| 40 | `field_msl` | `MSL/msl_feature` | `COHORT_ID` | 8 | 2026-11-06 |
| 41 | `field_sample` | `Samples/samples_feature` | `COHORT_ID` | 36 | 2026-11-20 |

The v1 code shows that the two account tables come from `f2f_feature`, which they do not in the `_pg` plan. `field_core_account` likely overlaps `field_core` ("COMBINED"), so check for duplicate columns before joining both. Intermediate files (`field_interaction_*`, `*_record`, `*_line`, `*_diagnostics`) are not joined.

### 3.6 Non-personal promotional (5) – Parquet, `NO/`

Key `PROVIDER_ID` + `HCP_COHORT_ID`, column `COHORT`, rows = keys.

| # | Table | Notebook (v1) | Rows | Cols | Last write |
| --- | --- | --- | --- | --- | --- |
| 42 | `hq_email_nba_3_1/kerendia_nba_3_1_hcp_model_hq_email_features.parquet` | `HQ Emails/15_promotional_features_HQ_Emails_new` | 3,648,042 | 23 | 2026-11-20 |
| 43 | `digital_engagement_nba_3_1/kerendia_nba_3_1_hcp_model_digital_paid_media_features.parquet` | `Digital_Engagement/24_Features_Digital_NBA31` | 8,252,328 | 152 | 2026-11-20 |
| 44 | `high_intent_signals_nba_3_1/kerendia_nba_3_1_hcp_model_high_intent_features.parquet` | `High_Intent_Signal_Features/25_Features_High_Intent_Signals_NBA31` | 8,252,328 | 37 | 2026-11-23 |
| 45 | `dtc_nba_3_1/kerendia_nba_3_1_hcp_model_dtc_features.parquet` | **no writer found** (see below) | 8,252,328 | 20 | 2026-11-23 |
| 46 | `oe_nba_3_1/kerendia_nba_3_1_oe_promotional_features.parquet` | `OE/35_OE_Promotional_Features_NBA31` | 8,252,328 | 324 | 2026-11-23 |

**DTC:** the v1 notebook `DTC/34_promotional_features_DTC` writes only the geography tables (`ZIP_OUT` `..._dtc_zip_features`, `SOCIAL_OUT` `..._dtc_social_dma_features`, `SEARCH_OUT` `..._dtc_search_state_features`). The string `hcp_model_dtc` is in neither the v1 nor the `_pg` copy of `DTC/34_promotional_features_DTC` (the 3.0 `04_Promotional_Features/34_promotional_features_DTC` was not checked). The HCP-level table #45 (ZIP already matched to HCP, `DTC_ZIP_MATCHED`, 8 social / search features) exists in the volume, so its notebook is somewhere else (Q2). Fallback if it cannot be found: join `..._dtc_zip_features` (`ZIP5` + `COHORT`) through the HCP ZIP, as in D6.

Not joined: `oe_nba_3_1/..._TEST.parquet`, `_intermediate*/`, `feature_manifest.parquet` (used only for the data dictionary).

### 3.7 Size

| Family | Tables | Cols (incl. keys / metadata) |
| --- | --- | --- |
| Claims | 6 | 8,517 |
| Patient | 15 | 4,743 |
| Rx market | 6 | 3,338 |
| Static HCP | 6 | 172 |
| Field activity | 8 | 234 |
| Non-personal | 5 | 556 |
| **Total** | **46** | **17,560** |

## 4. Not joined (not 3.1-ready)

| Area | v1 notebook | Why not |
| --- | --- | --- |
| FTP | `FTP_and_Copay/19_ftp_features` | Writes `..._ftp_features_for_inference` (inference cohort); no `c1`-`c28` output |
| Copay | `FTP_and_Copay/22_copay_features` | Writes `kerendia_nba_3_hcp_model_copay_features.parquet`; no cohort column |
| Digital phase 1 / 2 | `51_digital_nba_phase1_features`, `53_..._phase2_high_intent_features` | Phase 1 on `..._offset7` cohorts, phase 2 has no output; replaced by #43 and #44 |
| Digital block | `14_hcp_digital_phase1_feature_block` | `SAVE_OUTPUT = False` |
| Clickstream | `04_Promotional_Features/18_promotional_ClickStream_features` (3.0) | Dropped (D7) |
| 3.0 promotional | root `04_Promotional_Features/14-34` | 3.0 code in the `_pg` review, replaced by 3.5 / 3.6 |
| MMIT | only `04_MMIT_Features/` docs and EDA | No output |
| Veeva Link to People | `Veeva Link To People Analysis/` | Outputs in `DEV/veeva_link_to_people/` use anchor dates / `..._offset7` cohorts, not `c1`-`c28` |

## 5. Combine steps

1. **Config cell**: one entry per table of section 3 (path, format, family, sub-family, cohort column, writer notebook). It drives the loading, the data dictionary and the checks.
2. **Skeleton**: universe x 28 cohorts from `VOL/cohorts/claims`; columns `HCP_COHORT_ID`, `PROVIDER_ID`, `COHORT_ID`, `COHORT_SET`; placeholder `'0'` out (D13).
3. **Normalize**: rename the cohort column to `COHORT_ID`; build `HCP_COHORT_ID` for claims; drop metadata (`SVC_DT_M`, `SVC_DT`, `PULL_DT`, `DATASET`, `COHORT_MONTH`, `PREDICTION_MONTH`, `OFFSET_DAYS`, `CUTOFF_DATE`, `LOOKBACK_END_DATE`, `ZIP5`, `DMA_CODE`, `STATE_NAME`, ...).
4. **Side file**: claims rows with null `PROVIDER_ID`, kept with `NPI_NUMBER` (D13).
5. **Left joins** on `HCP_COHORT_ID`, one `COHORT_SET` at a time.
6. **Derived**: specialty one-hot (fixed list), calendar / months since launch, Kerendia / SGLT2 ratios.
7. **Impute**: 0 for counts / flags; 9999 / -9999 for recency / first occurrence; medians from training cohorts only (D10, D14).
8. **Write** `<run>/hcp_combined/kerendia_nba_3_1_hcp_selected_features_data` (Delta, partitioned by `COHORT_SET`) plus the data dictionary (D11).
9. **Final feature list** filter at the end (D9).

## 6. Checks

* Every table: rows = distinct `HCP_COHORT_ID`; only `c1`-`c28`.
* Skeleton row count unchanged after each join; match rate per table and cohort.
* No feature name in two tables (watch NB01 vs NB04, and `field_core` vs `field_core_account`).
* 0 nulls after imputation; one HCP traced by hand across families.

## 7. Open questions

| ID | Question | Owner |
| --- | --- | --- |
| Q1 | Patient features: read `NO` (v1 code writes there, last write 2026-11-03) or `DEV` (D4, later write 2026-11-07 to 11-09, same rows)? | Patient owner |
| Q2 | Which notebook writes `kerendia_nba_3_1_hcp_model_dtc_features.parquet`? Sync it into v1 | DTC owner |
| Q3 | Claims: confirm `full_2026_11_13` is the run to combine, or rerun with the v1 code | Claims owner |
| Q4 | Join both `field_core` and `field_core_account`, or only one? | Field owner |
| Q5 | Commit `NBA 3.1 - Dev - v1` to `combine`; it is now the single source for the combine notebook | Team |
