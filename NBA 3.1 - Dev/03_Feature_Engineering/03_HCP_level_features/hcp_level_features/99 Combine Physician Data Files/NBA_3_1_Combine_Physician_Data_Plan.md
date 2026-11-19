# NBA 3.1 – Combine physician data (99): move to the 3.1 pipeline, analysis and plan

**Status (2026-11-19):** plan refreshed from everything on the `combine` branch and the outputs in the 3.1 volume. **No code changed and nothing run in the notebook.** The notebook is updated only after this plan and the decisions in section 7 are approved.  
**Structure:** section 1 explains how the 3.0 notebook works; sections 2-8 are the 3.1 plan. The 2026-11-11 analysis is kept in a separate file.

**Roots used below**
* `NO` = `kerendia_nba_3_1_volume/notebook_output/`
* `DEV` = `kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/`
* `V30` = `kerendia_nba_3_volume/` (the 3.0 volume)

---

## 1. How the 3.0 notebook works

**Notebook:** `(Clone) NBA_3_0_Combine_Physician_Data` in this folder, a clone of the 3.0 `99_Combine_Physician_Data` (188 cells).  
**What it does:** builds one row per HCP x cohort (`HCP_COHORT_ID`) by joining every HCP feature family (claims monthly, HCP-level, promotional, feature accelerator). It then one-hot encodes specialty, adds calendar / launch features, keeps the 752 selected features, imputes nulls, casts to float and writes the model input table.

| Step | Cells | What it does |
| --- | --- | --- |
| Setup | 2 | `%run` 3.0 `00_Helper_Notebooks/00_connection` |
| Load | 3, 6, 111 | 12 accelerator tables + 2 hospitalization tables, 34 HCP / promo / claims tables, all from the 3.0 `ops_pipeline/notebook_output/` (most `*_for_inference`) |
| Skeleton | 13-28 | 3.0 HCP universe (`kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`) x cohort anchor file (`query_output/hcp_model_inference_anchor_dates.csv`); `SVC_DT_M = trunc(LOOKBACK_END_DATE)`; BHID added from `kerendia_nba_3_0_npi_bhid_mapping`, rows without BHID dropped |
| NPI to PROVIDER_ID | 29-36 | `claim_rx_monthly`, `hcp_paid_search`, `nbrx_shares_4_features` mapped NPI to `PROVIDER_ID`; NPI dropped |
| Part 1: claims + HCP-level | 37-74 | 23 tables left-joined on `PROVIDER_ID` + `SVC_DT_M` (2 static tables on `PROVIDER_ID` only), `dropDuplicates(PROVIDER_ID, SVC_DT_M)`; `HCP_COHORT_ID = PROVIDER_ID_COHORT` |
| Part 2: promotional | 75-101 | 11 promotional tables: 8 joined on `HCP_COHORT_ID = BHID_COHORT` (calls x2, speaker, HQ email, iRep, clickstream, FTP, samples); geo on BHID; census on ZIP; DTC through a DMA to ZIP file on `ZIP_CODE_GEO` + `SVC_DT_M`; key then rebuilt as `PROVIDER_ID_COHORT` |
| Part 3: feature accelerator | 102-126 | rx / dx / px / lab recency, first occurrence, frequency + hospitalization on `HCP_COHORT_ID`; columns filtered by name (`_rx`, `_dx`, `_px`, `_lab`) |
| Combine | 127-152 | accelerator, promotional and part 1 left-joined on `HCP_COHORT_ID`; names upper-cased; specialty one-hot (`HCP_SPECIALTY_*`); 2 Kerendia / SGLT2 ratio features; `AGE` renamed `HCP_AGE` |
| Calendar | 153-157 | cohort join gives `CALENDAR_MONTH`, `CALENDAR_YEAR`, `MONTHS_SINCE_KER_LAUNCH` (launch 2021-07-01) |
| Feature list | 158-171 | full column list saved as CSV snapshot; keep the 752 features of `input_files/Kerendia_NBA_3_feature_list_752_features.csv`; **missing features added as constant 0**; string and date columns dropped; names cleaned |
| Impute + write | 172-187 | HCP age / experience and SDoH: median; recency (`TIME_MIN`): 9999; first occurrence: -9999; `TIME_TO_ADOPT_FARXIGA`: 9999; rest 0; cast to float; 8 hard-coded renames; write Parquet snapshot + **overwrite** Delta `ops_pipeline/notebook_output/kerendia_nba_3_hcp_selected_features_data` |

Last stored outputs in the clone: 222,125 rows; 25,323 columns after the combine (cell 128); accelerator part 9,735 columns (cell 125).

---

## 2. How this plan was built (2026-11-19)

1. Listed every folder of `NBA 3.1 - Dev` on the `combine` branch.
2. Parsed the write path of 43 notebooks (feature notebooks, config and helpers) from their code.
3. Opened every output found in the 3.1 volume and read format, column count, key columns and cohort ids.

Not checked: row counts, one row per key, and whether two copies of the same table hold the same values.

## 3. Goal of the 3.1 combine

* One row per HCP x cohort for the 28 claims cohorts c1-c28, key `HCP_COHORT_ID = PROVIDER_ID_c<n>`.
* Every feature family of section 4 joined on that key.
* A **feature catalog** next to the table: one row per feature with its `CATEGORY` (section 6), so we know where each feature came from.

## 4. What the branch and the volume hold

### 4.1 Claims, HCP monthly (NB01-NB07)

Notebooks in `03_Feature_Engineering/03_HCP_level_features/hcp_level_features/`. Output of the run `full_2026_11_13` in `DEV/full_2026_11_13/hcp_claims/`, Delta, key `PROVIDER_ID` + `COHORT_ID` (28 cohorts).

| Notebook | Table used by the combine | Columns |
| --- | --- | --- |
| 01_claim_rx_monthly_cohort | `provider_claim_rx_monthly_cohort` | 4,681 |
| 02_claim_lab_monthly_cohort | `provider_claim_lab_monthly_cohort` | 152 |
| 03_claim_diagnosis_monthly_cohort | `provider_claim_diagnosis_monthly_cohort` | 122 |
| 04_claims_monthly_cohort | `final_claims_monthly_cohort` | 3,164 |
| 05_claim_rx_nps_monthly_cohort | `claim_rx_nps_monthly_cohort` | 172 |
| 06_claim_eligible_hcp | `provider_claim_eligible_patient_cohort` (the non-provider table is keyed by `NPI_NUMBER`) | 226 |
| 07_split_cohort_sets | no table written (helper) | - |

The run folder also holds the non-provider versions (`claim_rx_monthly_cohort`, `claims_monthly_cohort`, ...). The combine uses the `provider_` tables.

### 4.2 Patient events (rx, dx, px, lab, add-on)

Notebooks in `03_patient_features/Final Notebooks/`. The code writes to `NO/patient_features/<family>/`. A copy with the same column counts is in `DEV/patient_features/`. Delta, key `PROVIDER_ID` + `HCP_COHORT_ID`, cohort column `COHORT` (28 cohorts).

| Notebook | Tables (columns) |
| --- | --- |
| RX_Patient_Features | `rx_first_occurrence_features` (402), `rx_frequency_features` (1,294), `rx_recency_features` (281) |
| DX_Patient_Features | `dx_first_occurrence_features` (339), `dx_frequency_features` (1,204), `dx_recency_features` (263), `dx_hospitalization_features` (13) |
| PX_Patient_Features | `px_first_occurrence_features` (164), `px_frequency_features` (534), `px_recency_features` (129), `px_hospitalization_features` (13) |
| LAB_Patient_Features | `lab_first_occurrence_features` (12), `lab_frequency_features` (24), `lab_recency_features` (27) |
| 01_Additional_Patient_Features | `addon/claims_addon_patient_features` (44) |

The `*_censor_report` tables (5 columns) are checks, not features.

### 4.3 Rx market (HCP level)

| Notebook | Where the code writes | Output found | Columns | Key |
| --- | --- | --- | --- | --- |
| `03_HCP_Level_Features/10_kerendia_prior_writing` | `NO/hcp_features/kerendia_prior_writing` | only `DEV/hcp_features/kerendia_prior_writing` | 29 | `PROVIDER_ID` + `HCP_COHORT_ID`, `cohort_id` (28) |
| `03_HCP_Level_Features/11_adoption_features` | `NO/hcp_features/adoption_features` | `NO` (19 columns) and `DEV` (20 columns) | 19 / 20 | same |
| `05_NBRx_NRx_TRx/26_Features_NBRx`, `27_Features_NRx`, `28_Features_TRx` | **the 3.0 volume** (`V30/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_{nbrx,nrx,trx}_...`) | `NO` and `DEV` `hcp_features/{nbrx,nrx,trx}_features` | 1,266 each | `PROVIDER_ID` + `SVC_DT_M` (46 months), **no cohort id** |
| not found in the scanned notebooks | - | `NO` and `DEV` `hcp_features/competitor_share_features` | 76 | `PROVIDER_ID` + `SVC_DT_M` (46 months) |

### 4.4 Static HCP features

All in `DEV/hcp_features/`, Delta, key `PROVIDER_ID` + `HCP_COHORT_ID`, `cohort_id` (28 cohorts). **None of these notebooks is on the `combine` branch.**

| Table | Columns | Notebook and branch |
| --- | --- | --- |
| `physician_attributes_features` | 27 | 07_physician_attributes_features, on `dev/claims-comorbidity-competitor-features` |
| `census_features` | 41 | 08_census_features, same branch |
| `colocation_idn_features` | 22 | 33_colocation_idn_features, same folder as 07 / 08 (`NBA 3.1 Static Feature Notebooks/`); branch not checked |
| `claim_comorbidity` | 19 | not identified |
| `competitor_nbrx_share` | 55 | not identified |
| `market_event_features` | 8 | not identified |

### 4.5 Promotional, personal (field activity)

Notebooks in `04_Promotional_Features/personal_promotional_features/<channel>/`. Output in `NO/field_activity_nba_3_1/`, Parquet, key `HCP_COHORT_ID` (`PROVIDER_ID_c<n>`, 28 cohorts) + `PROVIDER_ID`, no separate cohort column. The cohorts come from `cohorts/promotional/cohorts.parquet` (offset 17 days).

| Notebook | Table | Columns |
| --- | --- | --- |
| F2F/f2f_feature | `kerendia_nba_3_1_hcp_model_field_core_features.parquet` | 59 |
| Speaker Programs/speaker_program_feature | `..._field_events_features.parquet` | 23 |
| Irep emails/irep_email_feature | `..._field_irep_features.parquet` | 26 |
| Message features/message_feature | `..._field_message_features.parquet` | 9 |
| MSL/msl_feature | `..._field_msl_features.parquet` | 8 |
| Samples/samples_feature | `..._field_sample_features.parquet` | 36 |
| not identified | `..._field_account_call_features.parquet` | 10 |
| not identified | `..._field_core_account_features.parquet` | 63 |

The other files in the folder (`field_interaction_*`, `*_record`, `*_line`, `*_diagnostics`) are intermediate, not features.

### 4.6 Promotional, non-personal

Notebooks in `04_Promotional_Features/non_personal_promotional_features/`. Output in `NO/`, Parquet, promotional cohorts.

| Notebook | Table | Columns | Key |
| --- | --- | --- | --- |
| HQ Emails/15_promotional_features_HQ_Emails_new | `hq_email_nba_3_1/kerendia_nba_3_1_hcp_model_hq_email_features.parquet` | 23 | `HCP_COHORT_ID` (28) |
| Digital_Engagement/24_Features_Digital_NBA31 | `digital_engagement_nba_3_1/kerendia_nba_3_1_hcp_model_digital_paid_media_features.parquet` | 152 | `HCP_COHORT_ID` (28) |
| High_Intent_Signal_Features/25_Features_High_Intent_Signals_NBA31 | `high_intent_signals_nba_3_1/kerendia_nba_3_1_hcp_model_high_intent_features.parquet` | 37 | `HCP_COHORT_ID` (28) |
| DTC/34_promotional_features_DTC | `dtc_nba_3_1/kerendia_nba_3_1_dtc_zip_features.parquet` | 17 | `ZIP5` + `COHORT` (28) |
| same | `dtc_nba_3_1/kerendia_nba_3_1_dtc_social_dma_features.parquet` | 7 | `COHORT` (28); geo key column not checked |
| same | `dtc_nba_3_1/kerendia_nba_3_1_dtc_search_state_features.parquet` | 7 | `COHORT` (**20 cohorts only**); geo key column not checked |
| no notebook in the branch (folder `OE/` has only the client summary) | `oe_nba_3_1/kerendia_nba_3_1_oe_promotional_features.parquet` | 320 | `PROVIDER_ID` + `HCP_COHORT_ID`, `COHORT` (28) |
| same | `oe_nba_3_1/..._TEST.parquet` | 164 | 1 cohort (c28): a test, not used |
| 51_digital_nba_phase1_features, 53_digital_nba_phase2_high_intent_features | write to `V30/hcp_level_model/dev_folder/notebook_output/nba_3_1_digital_phase{1,2}/` | not checked | `COHORT_ID` (from the code) |
| 14_hcp_digital_phase1_feature_block | table `kerendia_nba_3.digital_features_phase1`, `SAVE_OUTPUT = False` | not checked | - |

### 4.7 Market access

| Area | What the branch has | 3.1 output |
| --- | --- | --- |
| MMIT | only EDA notebooks (`04_MMIT_Features/MMIT_EDA_Checks/`) | none found in `NO` or `DEV` |
| FTP | `FTP_and_Copay/19_ftp_features` writes `V30/.../ops_pipeline/notebook_output/kerendia_nba_3_1_hcp_model_ftp_features_for_inference` (inference cohort) | none found in `NO` or `DEV` |
| Copay | `FTP_and_Copay/22_copay_features` writes `V30/.../dev_folder/notebook_output/kerendia_nba_3_hcp_model_copay_features.parquet` with the 3.0 anchor CSV | none found in `NO` or `DEV` |

### 4.8 Not used: 3.0 promotional notebooks

The notebooks at the root of `04_Promotional_Features/` (14, 15, 16, 17, 18, 19, 24, 25, 34) read the 3.0 anchor CSV and write to the 3.0 volume. They are replaced by sections 4.5 and 4.6. No 3.1 clickstream notebook or output was found.

## 5. What we found

**N1. Five key styles.** The combine has to bring all of them to `HCP_COHORT_ID`:

| Style | Families |
| --- | --- |
| `PROVIDER_ID` + `COHORT_ID` | claims NB01-NB06 |
| `PROVIDER_ID` + `HCP_COHORT_ID` + cohort column | patient (`COHORT`), static and Rx market (`cohort_id`), OE (`COHORT`) |
| `HCP_COHORT_ID` only | field activity, HQ email, digital paid media, high intent |
| `PROVIDER_ID` + `SVC_DT_M` (monthly, no cohort) | NBRx / NRx / TRx, competitor share |
| geography + cohort | DTC (ZIP5 for the ZIP table; the DMA and state key columns were not checked) |

The cohort column has three names (`COHORT_ID`, `cohort_id`, `COHORT`).

**N2. Two copies of several families.** Patient features, adoption, NBRx / NRx / TRx and competitor share exist in both `NO` and `DEV`. Adoption differs (19 vs 20 columns). We need one source per family.

**N3. The code on the branch does not always match the outputs.**
* `10_kerendia_prior_writing` writes to `NO`, but the output exists only in `DEV`.
* `26`-`28` write to the 3.0 volume, but 3.1 copies exist.

So some outputs come from a different version of the code than the one on `combine`.

**N4. Missing from the branch.** The static notebooks (07, 08, 33, folder `NBA 3.1 Static Feature Notebooks/`) are not on `combine`. No writer was found in the scanned notebooks for `claim_comorbidity`, `competitor_nbrx_share`, `market_event_features`, `competitor_share_features`, OE and the two field account tables.

**N5. Not 3.1-ready.** MMIT, FTP, copay and clickstream have no 3.1 cohort output. Digital phase 1 / 2 write to the 3.0 volume.

**N6. DTC search by state covers 20 of 28 cohorts.** 8 cohorts will be empty for those columns.

**N7. Size.** About 18,000 columns over all tables of section 4 (key and metadata columns included):
* claims 8,517
* patient 4,743
* Rx market about 3,920
* promotional about 800
* static 172

3.0 already had 25,323 columns for a single cohort (section 1), so a full-width join over 28 cohorts is not realistic: select features per table first and process one `COHORT_SET` at a time.

**N8. 3.0 notebook logic that must change** (steps of section 1; from the 2026-11-11 review of the notebook, not re-checked today):
* Setup: `%run` of the 3.0 `00_connection` star-imports Spark functions and shadows `sum`, `min`, `max`; use the 3.1 `00_cohort_config` and `builtins`.
* Joins: on `SVC_DT_M` and two different `HCP_COHORT_ID` rules (`BHID_COHORT` for promotional, `PROVIDER_ID_COHORT` for the rest); 3.1 must join on the cohort id.
* Metadata: every 3.1 table carries `COHORT_MONTH, OFFSET_DAYS, CUTOFF_DATE, SVC_DT_M, PULL_DT, DATASET, COHORT_SET`; keep them once.
* Feature list: missing features are filled with 0 without a warning.
* Imputation: medians are taken over all rows; with 28 cohorts that includes validation and backtesting rows (leakage).
* One-hot: specialty columns come from the data; fix the value list.
* Renames: 8 hard-coded renames exist only to match the 3.0 model.
* Write: the last cell overwrites the 3.0 production Delta table; 3.1 must write to a 3.1 path only.

## 6. Category column (proposal)

The model table has one column per feature, so the category goes in a **feature catalog** saved next to it.

| Column | Content |
| --- | --- |
| `FEATURE_NAME` | name in the combined table |
| `CATEGORY` | one of the values below |
| `SUB_CATEGORY` | family inside the category (e.g. `Rx frequency`, `F2F`, `Census`) |
| `SOURCE_NOTEBOOK` | notebook that builds it |
| `SOURCE_TABLE` | path of the table it was read from |

| `CATEGORY` | Tables |
| --- | --- |
| Claims | NB01-NB06 (4.1) |
| Patient events | rx, dx, px, lab, add-on (4.2) |
| Rx market | NBRx, NRx, TRx, competitor share, prior writing, adoption (4.3) |
| Static HCP | physician, census, colocation / IDN, comorbidity, competitor NBRx share, market events (4.4) |
| Promotional - personal | field activity (4.5) |
| Promotional - non-personal | HQ email, digital paid media, high intent, DTC, OE (4.6) |
| Market access | MMIT, FTP, copay (4.7, once available) |
| Derived in combine | specialty one-hot, calendar, ratio features |

The catalog is built from the list of source tables in one config cell, so every column gets exactly one category. Checks:
* no feature without a category
* no feature name in two tables

## 7. Decisions needed

| ID | Question | Proposal |
| --- | --- | --- |
| D1 | Scope | Training c1-c28 first; inference later with the same code |
| D2 | Category format | Feature catalog as in section 6 |
| D3 | Static notebooks are on `dev/claims-comorbidity-competitor-features` | Merge that branch into `combine`, or read only the saved outputs |
| D4 | Source of truth when a table is in both `NO` and `DEV` (N2, N3) | One root per family, agreed with each owner |
| D5 | Monthly tables without a cohort (NBRx / NRx / TRx, competitor share) | Take the row whose `SVC_DT_M` is the lookback-end month of each cohort, or ask the owner to add the cohort id |
| D6 | DTC geography | ZIP5 from the HCP ZIP of the census spine; DMA and state through a ZIP mapping; search-by-state empty for the 8 missing cohorts |
| D7 | Families not 3.1-ready (MMIT, FTP, copay, clickstream, digital phase 1 / 2) | Leave out of the first version and list them in the catalog as pending |
| D8 | Tables with no writer found (N4), field account tables, OE `_TEST` | Owner confirms each; `_TEST` left out |
| D9 | Feature list | All 3.1 features; report against the 752 list only, no 0-fill |
| D10 | Imputation statistics | Medians from the training cohorts only, applied to all sets |
| D11 | Output | `<run>/hcp_combined/kerendia_nba_3_1_hcp_selected_features_data`, Delta partitioned by `COHORT_SET`, plus the feature catalog; never the 3.0 path |
| D12 | Notebook location | New 3.1 notebook in this folder, next to this plan; the clone stays as the 3.0 reference |
| D13 | `PROVIDER_ID` gaps in the NPI / BHID mapping (open point O2) | Decide before the combine |

## 8. Next steps

1. Decide D1-D13.
2. Owners confirm the tables in N4 and D8.
3. Write the list of notebook changes from sections 5 and 7, then rewrite the notebook.
4. Validation:
   * one row per `HCP_COHORT_ID` (universe x 28)
   * no row gain after each join; match rate per table and cohort reported
   * no duplicate column names; metadata columns once
   * promotional cohort c<n> lands on claims cohort c<n> (one HCP checked by hand)
   * 0 nulls after imputation
   * the catalog checks of section 6


