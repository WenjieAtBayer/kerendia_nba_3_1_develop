# NBA 3.1 – Combine physician data (99): move to the 3.1 pipeline, analysis and plan

**Status (2026-11-11):** analysis only. **No code changed and nothing run in the notebook.** Changes C1–C14 wait for approval and the decisions in section 4.  
**Notebook:** `hcp_level_features/(Clone) 99_Combine_Physician_Data` (clone of the 3.0 `99_Combine_Physician_Data`, 189 cells)  
**What it does (3.0):** builds one row per HCP x cohort (`HCP_COHORT_ID`) by joining every HCP feature family (claims monthly, HCP-level, promotional, feature accelerator). It then one-hot encodes specialty, adds calendar / launch features, keeps the 752 selected features, imputes nulls, casts to float and writes the model input table.  
**Open points this closes:** O7 (combine joins on `SVC_DT_M`, but 3.1 outputs are keyed by `COHORT_ID`) and O14 (combine still on 3.0 logic) in `NBA_3_1_HCP_Level_Features_AI_Readiness.md`; go-live phase 4 / next action 7.

---

## 1. How the 3.0 notebook works

| Step | Cells | What it does |
| --- | --- | --- |
| Setup | 2 | `%run` 3.0 `00_Helper_Notebooks/00_connection` |
| Load | 3, 6, 111 | 12 accelerator tables + 2 hospitalization tables, 34 HCP / promo / claims tables, all from the 3.0 `ops_pipeline/notebook_output/` (most `*_for_inference`) |
| Skeleton | 13–28 | 3.0 HCP universe (`kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`) x cohort anchor file (`query_output/hcp_model_inference_anchor_dates.csv`); `SVC_DT_M = trunc(LOOKBACK_END_DATE)`; BHID added from `kerendia_nba_3_0_npi_bhid_mapping`, rows without BHID dropped |
| NPI → PROVIDER_ID | 29–36 | `claim_rx_monthly`, `hcp_paid_search`, `nbrx_shares_4_features` mapped NPI → `PROVIDER_ID`; NPI dropped |
| Part 1: claims + HCP-level | 37–74 | 23 tables left-joined on `PROVIDER_ID` + `SVC_DT_M` (2 static tables on `PROVIDER_ID` only), `dropDuplicates(PROVIDER_ID, SVC_DT_M)`; `HCP_COHORT_ID = PROVIDER_ID_COHORT` |
| Part 2: promotional | 75–101 | 11 promotional tables: 8 joined on `HCP_COHORT_ID = BHID_COHORT` (calls x2, speaker, HQ email, iRep, clickstream, FTP, samples); geo on BHID; census on ZIP; DTC through a DMA → ZIP file on `ZIP_CODE_GEO` + `SVC_DT_M`; key then rebuilt as `PROVIDER_ID_COHORT` |
| Part 3: feature accelerator | 102–126 | rx / dx / px / lab recency, first occurrence, frequency + hospitalization on `HCP_COHORT_ID`; columns filtered by name (`_rx`, `_dx`, `_px`, `_lab`) |
| Combine | 127–152 | accelerator ⟕ promotional ⟕ part 1 on `HCP_COHORT_ID`; names upper-cased; specialty one-hot (`HCP_SPECIALTY_*`); 2 Kerendia / SGLT2 ratio features; `AGE` → `HCP_AGE` |
| Calendar | 153–157 | cohort join → `CALENDAR_MONTH`, `CALENDAR_YEAR`, `MONTHS_SINCE_KER_LAUNCH` (launch 2021-07-01) |
| Feature list | 158–171 | full column list saved as CSV snapshot; keep the 752 features of `input_files/Kerendia_NBA_3_feature_list_752_features.csv`; **missing features added as constant 0**; string and date columns dropped; names cleaned |
| Impute + write | 172–187 | HCP age / experience and SDoH: median; recency (`TIME_MIN`): 9999; first occurrence: −9999; `TIME_TO_ADOPT_FARXIGA`: 9999; rest 0; cast to float; 8 hard-coded renames; write Parquet snapshot + **overwrite** Delta `ops_pipeline/notebook_output/kerendia_nba_3_hcp_selected_features_data` |

Last stored outputs in the clone: 222,125 rows; 25,323 columns after the combine (cell 128); accelerator part 9,735 columns (cell 125).

## 2. Inputs before and after

### 2.1 Skeleton, cohorts, mapping

| Input | 3.0 | 3.1 / proposal |
| --- | --- | --- |
| HCP universe | `kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` (3.0 volume) | `kerendia_nba_3_1_volume/HCP_Universe_without_call_hcps/` (X1). Note: the config default `HCP_UNIVERSE_PATH` still points to the 3.0 table; only the job parameter switches it |
| Cohorts | `hcp_model_inference_anchor_dates.csv`: **today 1 row, cohort `I01`** (lookback end 2026-09-30, inference). Comments in the notebook (C21, C22, C26) come from earlier training runs | Claims cohort file `cohorts/claims/cohorts.parquet`: c1–c28, offset 0, 24 Training / 2 Testing / 2 Holdout (Backtesting); via `CLAIMS_COHORTS` / `COHORT_SETS` of `00_cohort_config` (X13) |
| NPI → PROVIDER_ID / BHID | `query_output/kerendia_nba_3_0_npi_bhid_mapping` | Same table (user confirmed 2026-11-04); `HCP_NPI_MAPPING_TABLE` / `NPI_BHID_MAPPING_PATH` in the config. Gaps O2 (105 unmapped, 52 with 2 IDs) still open |

### 2.2 Claims monthly features (NB01–NB06)

| 3.0 table (cell 6) | 3.1 table (`<run>/hcp_claims/`, `read_hcp_output`) | Key |
| --- | --- | --- |
| `claim_rx_monthly` (NPI, mapped in cell 33) | `provider_claim_rx_monthly_cohort` (already mapped) | `PROVIDER_ID` x `COHORT_ID` |
| `provider_claim_lab_monthly_ZS` | `provider_claim_lab_monthly_cohort` | same |
| `provider_claim_diagnosis_monthly` | `provider_claim_diagnosis_monthly_cohort` | same |
| `final_claims_monthly` | `final_claims_monthly_cohort` | same |
| `kerendia_nba_3_0_claim_rx_nps_monthly` | `claim_rx_nps_monthly_cohort` (provider level) | same |
| `kerendia_nba_3_0_claim_eligible_patient` | `provider_claim_eligible_patient_cohort` | same |

Checked 2026-11-11 in `full_2026_11_07/hcp_claims/`: 9 of the 11 tables are there; **`provider_claim_rx_monthly_cohort` and `final_claims_monthly_cohort` are missing** (NB01 / NB04 did not finish in that run). `full_2026_11_11/` has only `patient_journey/` so far. `provider_claim_eligible_patient_cohort`: 226 columns, 28 `COHORT_ID`s, folders `COHORT_SET=<group>`; non-feature columns `PROVIDER_ID, COHORT_ID, COHORT_MONTH, OFFSET_DAYS, CUTOFF_DATE, SVC_DT_M, PULL_DT, DATASET, COHORT_SET` (+ `DIALYSIS_FLAG` as a feature).

### 2.3 HCP-level, promotional and accelerator features

| Family | 3.0 tables | 3.1 output found in `kerendia_nba_3_1_volume/notebook_output/` | Status |
| --- | --- | --- | --- |
| HCP-level (Rx market) | `nbrx / nrx / trx_features_w_provider_id`, `perc_competitor_nbrx_shares`, `kerendia_prior_writing`, `adoption_features_inv_far` | `hcp_features/{nbrx_features, nrx_features, trx_features, competitor_share_features, kerendia_prior_writing, adoption_features}` | Exists; schema and cohort key to check |
| HCP-level (other) | `phy_static_features`, `sdoh` (census), `claim_comorbidity`, `kerendia_claims`, `copay`, `channel`, `paid_search`, `colocation_flag`, `additional_hcp_level_features`, `drg_kerendia / farxiga / jardiance`, `geo_features` | None found | Owner to confirm: 3.1 version, keep 3.0, or drop |
| HQ email | `hq_email_features_for_inference` | `hq_email_nba_3_1/kerendia_nba_3_1_hcp_model_hq_email_features.parquet` (`HCP_COHORT_ID = PROVIDER_ID_COHORT`, promotional cohorts) | Exists |
| DTC | `DTC_PROMOTION_for_inference` + DMA → ZIP file | `dtc_nba_3_1/kerendia_nba_3_1_dtc_{zip, social_dma, search_state}_features.parquet` | Exists; 3 tables at different geo levels instead of 1 |
| Field (calls, iRep, samples, speaker) | `call_features_bhoid`, `call_features`, `irep_features`, `samples_features`, `speaker_program` | `field_activity_nba_3_1/kerendia_nba_3_1_hcp_model_field_{core, events, irep, message, msl, sample}_features.parquet` | Exists; 3.0 → 3.1 mapping of tables to confirm |
| Digital | `clickstream_features` | `digital_engagement_nba_3_1/` holds only `placement_dictionary` and `unmapped_report` | No feature table yet |
| FTP / copay | `ftp_features_v2`, `copay_features` | None found | FTP / copay revamp in progress |
| Accelerator (patient-level events per HCP) | `rx/dx/px/lab_{recency, first_occurrence, accelerator}_features`, `dx/px_combined_hospitalization` | `patient_features/{rx, dx, px, lab, addon}` | Exists; mapping of the 14 tables to confirm |
| Feature list | `input_files/Kerendia_NBA_3_feature_list_752_features.csv` | `feature_selection/` holds only the 4 event lists | No 3.1 selected list yet |

**Cohort calendars differ:** claims cohorts end on the last day of the month (offset 0); the promotional cohort file (`cohorts/promotional/cohorts.parquet`) has `offset_days = 17` (c1 lookback ends 2024-06-17). Both use the same ids c1–c28 and prediction months. A join on `SVC_DT_M` would mix them; the join must be on the cohort id.

## 3. Findings

**F1. Inference, not training.** Every input is a `*_for_inference` table and the anchor file now holds one inference cohort (`I01`). The 3.1 HCP notebooks produce 28 training / validation / backtesting cohorts. The 3.1 combine has to work on c1–c28 (scope question D1).

**F2. Join key = `SVC_DT_M` (O7).** Part 1 joins on `PROVIDER_ID` + `SVC_DT_M` and the calendar features come from `SVC_DT_M`. In 3.1 the cohort is `COHORT_ID`; the promotional cohorts have different dates for the same id. All joins should use `PROVIDER_ID` + `COHORT_ID` (or `HCP_COHORT_ID`).

**F3. Two different `HCP_COHORT_ID`s.** Promotional tables use `BHID_COHORT` (cell 25), all others `PROVIDER_ID_COHORT` (cells 69, 96, 104); the key is dropped and rebuilt in between. 3.1 HQ email already uses `PROVIDER_ID_COHORT`. Cohort ids change from `C26` / `I01` to `c1`–`c28` (lower case); cell 133 / 181 split the key on `_` to get the cohort.

**F4. Writes to production.** Cell 185 overwrites the 3.0 Delta `ops_pipeline/notebook_output/kerendia_nba_3_hcp_selected_features_data`; cells 158 / 184 write to `ops_pipeline_snapshots/`. These must move to the 3.1 run folder with `assert_31_write_path`.

**F5. 3.0 helper + shadowed built-ins.** `%run` of the 3.0 `00_connection` (star import of `pyspark.sql.functions`); cell 46 imports `min, max` from Spark; cell 52 assigns `sum = 0`. Same issue as X22: config code needs `builtins.*`.

**F6. NPI mapping no longer needed for Rx claims.** 3.1 NB01 writes `provider_claim_rx_monthly_cohort`; cell 33 (map NPI → PROVIDER_ID) goes. `paid_search` and `competitor shares` still need it if they stay NPI-keyed.

**F7. New metadata columns in every 3.1 HCP table** (`COHORT_MONTH, OFFSET_DAYS, CUTOFF_DATE, SVC_DT_M, PULL_DT, DATASET, COHORT_SET`). 3.0 dropped only `PULL_DT`; 3.0 already ended with duplicate `PULL_DT` and `BHID` columns (cell 132). Keep them once (from the skeleton) and drop them from each feature table before the join.

**F8. Size.** 3.0: 222,125 rows x 25,323 columns for one cohort. 3.1: universe x 28 cohorts, and NB01 alone has about 4,675 columns, NB04 about 3,070 (E2E 2026-11-05). A full-width join of all families over 28 cohorts is not realistic; select the model features per table first and process one `COHORT_SET` at a time.

**F9. Missing features become 0 without a warning** (cell 164). In 3.1 some of the 752 features are gone on purpose: 979 NB01 features of 6 removed categories (X17), 9 NB04 features (X5), 15 old NB06 stage columns (X20), NB02 9-month windows (X19). They would be filled with constant 0. The step should report and stop, or the list should be replaced (D4).

**F10. Kerendia / SGLT2 ratio** (cell 150) reads `TOTAL_HCP_RX_CLAIMS_OF_DRUG_CLASS_KERENDIA/SGLT2_IN_LAST_{1,12}_MONTH`; the source table is not clear from the notebook (not an NB01 name). 3.1 NB01 now has `TOTAL_RX_CLAIMS_KERENDIA_*` (X16). To confirm.

**F11. Imputation uses all rows.** Medians (HCP age, experience, SDoH) are computed on the whole table. With 28 cohorts this includes validation and backtesting rows (leakage). 9999 / −9999 rules depend on column names (`TIME_MIN`, `FIRST_OCCURRENCE`); check they still match the 3.1 names.

**F12. Data-driven one-hot.** Specialty columns come from the distinct values in the data (cell 145). Per-set processing would give different columns per set; fix the value list (as `PIVOT_VALUES` in NB01).

**F13. Hard-coded renames** (cell 182: 8 double-underscore names) and column cleaning exist only to match the 3.0 model; revisit with the 3.1 list.

**F14. NB05 still has the removed categories** (`TOTAL_PATIENTS_START_ACE_OR_ARB_*`, `INSULIN`, `METFORMIN`, ...) in `claim_rx_nps_monthly_cohort` (X7 kept `Rx_05`), while NB01 dropped them (X17). Not a combine issue, but the combined table will show it.

**F15. Many check cells** (`display`, `count`, `printSchema`, column counts) run full actions; on 28 cohorts they cost a lot. Keep a few at the end.

## 4. Decisions needed

| ID | Question | Proposal |
| --- | --- | --- |
| D1 | Scope: training (c1–c28) or inference (`I01`) or both | **Training first** (c1–c28 from the claims cohort file); inference later with the same code and one cohort |
| D2 | Join key | **`PROVIDER_ID` + `COHORT_ID`**, `HCP_COHORT_ID = PROVIDER_ID_c<n>`; promotional tables joined on the cohort id, not on dates |
| D3 | Families with no 3.1 output (static, SDoH, comorbidity, Kerendia claims, copay, channel, paid search, colocation, additional, DRG, geo, clickstream, FTP) | Per family: 3.1 owner, keep the 3.0 table (only if it has the same cohorts), or drop. Needs the promo / HCP owners (Sehar, Saurabh) |
| D4 | Feature list | 3.1 list from the 3.1 feature selection (model retrained, X5). Until then: use the 752 list only for a report of present / missing, no 0-fill |
| D5 | Imputation statistics | Medians from the training cohorts only, applied to all sets |
| D6 | Output | `<run>/hcp_combined/kerendia_nba_3_1_hcp_selected_features_data`, Delta partitioned by `COHORT_SET` (same as `write_hcp_output`), plus the column list snapshot |
| D7 | `PROVIDER_ID` gaps (O2) | Decide before the combine (E2E 2026-11-04 asks for this); proposal: fill from the 3.1 Rx input |
| D8 | Where the notebook lives | Move it to this folder as `99_combine_physician_data_cohort`, next to this plan |

## 5. Changes (after approval)

| ID | Change | Where |
| --- | --- | --- |
| C1 | `%run "../../00_cohort_config"` instead of the 3.0 `00_connection`; `builtins` for sum / min / max | Setup, cells 46, 52 |
| C2 | Skeleton = 3.1 universe x `CLAIMS_COHORTS` (28 rows, `COHORT_ID`, `COHORT_MONTH`, `DATASET`, `COHORT_SET`) | Cells 13–28 |
| C3 | Claims tables via `read_hcp_output(HCP_NOTEBOOK_OUTPUT + table)`; drop the metadata columns (F7); stop if a table is missing | Cell 6 |
| C4 | Remove the NPI mapping of Rx claims (F6) | Cells 29–36 |
| C5 | All joins on `PROVIDER_ID` + `COHORT_ID`; one `HCP_COHORT_ID` rule | Cells 53, 81–98, 104–123, 128 |
| C6 | Inputs of section 2.3 from the 3.1 paths agreed in D3, read through one dictionary in a config cell | Cells 3, 6, 111 |
| C7 | Promotional join: HQ email, DTC (3 tables), field activity on the cohort id; drop the DMA → ZIP file if the DTC ZIP table covers it | Cells 76–101 |
| C8 | Select the model features per table before the join; loop over `COHORT_SETS` (F8) | New cell before the joins |
| C9 | Calendar features from `COHORT_MONTH` of the cohort file | Cells 153–157 |
| C10 | Fixed specialty value list (F12) | Cells 144–148 |
| C11 | Feature list: report present / missing, stop if a selected feature is missing (unless listed as dropped by X5 / X17 / X19 / X20) | Cells 160–164 |
| C12 | Imputation statistics from training cohorts (D5) | Cells 173–179 |
| C13 | Write to the 3.1 run folder only (`assert_31_write_path`), Delta by `COHORT_SET` (D6); remove the 3.0 overwrite | Cells 158, 184–185 |
| C14 | Remove or group the check cells; keep a final QC section | Throughout |

Not changed: feature logic of the source notebooks, the 9999 / −9999 / median rules (unless D5), the float cast.

## 6. Validation plan

| Check | Expected |
| --- | --- |
| Skeleton | rows = universe HCPs x 28, one row per `HCP_COHORT_ID` |
| Joins | no row gain after each join; match rate per table and cohort reported |
| Columns | no duplicate names; metadata columns once |
| Claims columns | equal to the source table values for the trace HCPs (all cohorts) |
| Promotional columns | promo cohort c<n> lands on claims cohort c<n> (check one HCP by hand) |
| Feature list | present / missing report; 0 unexpected missing |
| Imputation | medians from training only; 0 nulls after imputation |
| Output | 7 `COHORT_SET` groups, rows per set = source |
| Structure parity vs 3.0 | for one cohort with 3.0 inputs: same columns and key logic (values differ by design) |

## 7. Before starting

* NB01 and NB04 provider tables for a complete run (missing in `full_2026_11_07`; `full_2026_11_11` in progress).
* D1–D8 answered, D3 with the family owners.
