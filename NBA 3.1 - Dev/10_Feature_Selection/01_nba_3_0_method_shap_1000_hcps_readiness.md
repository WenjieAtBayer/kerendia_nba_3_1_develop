# NBA 3.1 Feature Selection: Readiness

How we got from the 3.1 feature tables to a ranked list of the 1,000 most useful features, using a 1,000-HCP test sample.

Status on 2026-11-24: Combine and feature selection both ran end to end on the 1,000-HCP sample, and every check passed. The selected list is ready for the team to review.

---

## Where to find things

| What | Where |
| --- | --- |
| Combine notebook | `NBA 3.1 - Dev/99 Combine Physician Data Files/NBA_3_1_Combine_Physician_Data` |
| Feature selection notebook | `NBA 3.1 - Dev/10_Feature_Selection/01_nba_3_0_method_shap_1000_hcps` |
| Volume root (all paths below start here) | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/` |
| HCP list used by Combine | `HCP_Universe_without_call_hcps` |
| Cohort file (dates for c1-c28) | `cohorts/claims/cohorts.parquet` |
| Target table | `notebook_output/target_variable/target_variable` |
| Combined feature table (1,000-HCP sample) | `hcp_level_model/dev_pipeline/notebook_output/combined_2026_11_24/hcp_combined/_test_sample_1000/kerendia_nba_3_1_hcp_selected_features_data` |
| Feature dictionary (one row per feature) | same folder, `kerendia_nba_3_1_hcp_feature_dictionary` |
| Feature selection outputs | `hcp_level_model/dev_pipeline/notebook_output/combined_2026_11_24/feature_selection/_test_sample_1000/poisson/` |
| **Final list of 1,000 features** | feature selection outputs, `final_selected_top_1000_features_by_shap.csv` |

Files in the feature selection output folder:

| File | Content |
| --- | --- |
| `final_selected_top_1000_features_by_shap.csv` | The 1,000 selected features, in rank order |
| `top_100_features_by_shap.csv` | The top 100 only |
| `shap_ranking_all_features.csv` | Every feature used, ranked by SHAP, with its share of total impact |
| `all_feature_importance_gain.csv` | Gain and split counts from the model, for every feature |
| `constant_features_dropped.csv` | Features with one value on all training rows, and that value |
| `excluded_source_features.csv` | Features left out on purpose by source table (empty: every Combine feature was a candidate) |
| `train_test_metrics.csv` | R2, RMSE, MAE and predicted vs actual NBRx, for train and test |
| `top_30_shap_impact.png`, `top_30_shap_beeswarm.png` | Charts of the top 30 features |
| `lightgbm_model.txt` | The trained model |
| `feature_alias_mapping.csv` | Short model names (f0, f1, ...) to real feature names |
| `model_data_parquet/` | Model rows: combined features + target + train/test label |
| `run_summary.json` | All counts and metrics of the run in one file |

---

## The journey

### Step 1. Combine: one row per HCP and cohort

Every 3.1 feature notebook writes its own table. Before we can rank features, they have to sit side by side, one row per HCP and cohort. The Combine notebook does this.

**What goes in**

* **44 source tables**, the feature tables listed in the Combine input plan (source: feature dictionary, distinct source tables).
* **The HCP list** `HCP_Universe_without_call_hcps`: 294,726 HCPs, after removing the placeholder HCP `0` (294,727 rows with it) (source: `HCP_Universe_without_call_hcps`, exact distinct count).
* **28 monthly cohorts**, c1 to c28 (source: `cohorts/claims/cohorts.parquet`). Each cohort has a lookback end date (the last month of feature data) and a prediction month two months later:

| Cohort | Lookback end | Prediction month |
| --- | --- | --- |
| c1 | 2024-05-01 | 2024-07-01 |
| c24 | 2026-04-01 | 2026-06-01 |
| c26 | 2026-06-01 | 2026-08-01 |
| c28 | 2026-08-01 | 2026-10-01 |

**The 1,000-HCP sample.** The full table is too big to iterate on quickly, so Combine was run on a test sample of 1,000 HCPs. The sample is the first 1,000 HCPs of the list after sorting them by a fixed hash of the HCP id, so **the same 1,000 HCPs come back every run** (source: Combine notebook, skeleton step).

**What Combine does, in order**

1. **Builds the skeleton**: every sampled HCP times all 28 cohorts, with the key `HCP_COHORT_ID` = HCP id + cohort (for example `7935084_c27`).
2. **Checks each input table**: keys, cohorts present, rows without an HCP id, and how many rows match the skeleton.
3. **Joins the features one cohort set at a time** (7 sets, below), so a large run never has to hold all 28 cohorts at once.
4. **Fills missing values** with one rule per feature type:

| Rule | Used for | Fill value | Features (source: feature dictionary) |
| --- | --- | --- | --- |
| Zero | Counts, shares and flags, e.g. `TOTAL_HCP_NBRX_CLAIMS_KERENDIA_IN_LAST_12_MONTH` | 0 | 16,584 |
| First occurrence | First time an event was seen, e.g. `MAX_EVENT_TIME_..._FIRST_OCCURRENCE` | -9999 | 578 |
| Median | Census / SDoH features and HCP experience | Median of the training cohorts c1-c24 | 37 |
| Time since | Days or months since an event, time to adopt | 9999 | 36 |
| None | The 3 calendar features Combine adds itself | (never missing) | 3 |
| **Total** | | | **17,238** |

5. **Adds 3 calendar features**: `CALENDAR_MONTH`, `CALENDAR_YEAR` and `MONTHS_SINCE_KER_LAUNCH`.
6. **Writes** the combined table and a feature dictionary with one row per feature (name, category, definition, source notebook and table, fill rule).

**What came out** (source: combined table, `_test_sample_1000`)

* 28,000 rows = 1,000 HCPs x 28 cohorts, each `HCP_COHORT_ID` exactly once.
* 17,245 columns: 17,238 features + 7 id columns.
* All 7 cohort sets present:

| Cohort set | Use | Cohorts | Rows |
| --- | --- | --- | --- |
| C1-C5_training | Training | 5 | 5,000 |
| C6-C10_training | Training | 5 | 5,000 |
| C11-C15_training | Training | 5 | 5,000 |
| C16-C20_training | Training | 5 | 5,000 |
| C21-C24_training | Training | 4 | 4,000 |
| C25-C26_validation | Testing | 2 | 2,000 |
| C27-C28_backtesting | Holdout (backtesting) | 2 | 2,000 |
| **Total** | | **28** | **28,000** |

The run took 137 minutes (Combine job run `196650153984570`, 2026-11-24).

**The 17,238 features by category** (source: feature dictionary):

| Category | Features | Example features |
| --- | --- | --- |
| Claims | 8,458 | `RUNNING_TOTAL_RX_CLAIMS_KERENDIA`, `PCT_TOTAL_RX_CLAIMS_SGLT2_MEDICARE_PART_D_IN_LAST_3_MONTH` |
| Patient events | 4,687 | `MIN_EVENT_TIME_EGFR_TEST_ALL_LOINC_VARIANTS_TIME_MIN`, `LOGRATIO_FREQ_ACUTE_ON_CHRONIC_DIASTOLIC_CONGESTIVE_HEART_FAILURE_IN_LAST_6_MONTH` |
| Rx market (NBRx / NRx / TRx, competitor share) | 3,300 | `KERENDIA_TRX_APPROVED_IN_LAST_3_MONTH`, `TOTAL_HCP_NBRX_CLAIMS_KERENDIA_IN_LAST_12_MONTH` |
| Promotional, non-personal (digital, HQ emails, OE, high intent, DTC) | 520 | `DIGITAL_EXPOSURE_3M_VS_PRIOR_3M`, `DTC_SOCIAL_CLICKS_PER_1K_ADULTS_3M` |
| Static HCP (physician attributes, census, colocation) | 142 | `PCT_OF_PATIENTS_IN_HCP_DX_PANEL_WITH_CKD_STAGE_4_IN_LAST_365_DAYS_DX` |
| Promotional, personal (F2F, iRep emails, MSL, messages, samples, speaker programs) | 128 | `FLD_KER_PRIMARY_SHARE_12M`, `FLD_DAYS_SINCE_LAST_INT` |
| Added by Combine (calendar) | 3 | `CALENDAR_MONTH` |
| **Total** | **17,238** | |

### Step 2. Adding the target

The feature selection notebook starts by attaching the outcome we want to predict: **Kerendia NBRx in the cohort's prediction month** (`KERENDIA_NBRX` in the target table), joined on `HCP_COHORT_ID`.

* The target table covers 314,920 HCPs x 28 cohorts = 8,817,760 rows (source: target table, exact count).
* All 28,000 sample rows found a target; no rows were gained or lost in the join, and the NBRx total matches the target table for the same keys (source: feature selection run, built-in checks).
* The sample holds **622 NBRx in 413 rows**, from 129 HCPs (source: combined sample joined to the target table). Most rows are zero, which is normal for NBRx and why the model uses a Poisson objective (Step 4).

### Step 3. Splitting by time, not at random

Rows are split by cohort, so the model is always tested on months later than the ones it learned from:

| Part | Cohorts | Rows | NBRx | Rows with NBRx > 0 | Used for |
| --- | --- | --- | --- | --- | --- |
| Train | c1-c24 | 24,000 | 504 | 328 | Training the model and computing SHAP |
| Test | c25-c26 | 2,000 | 68 | 46 | Checking how well the model holds up on later months |
| Backtesting holdout | c27-c28 | 2,000 | 50 | 39 | Not used here; kept for backtesting |

(source: combined sample joined to the target table, exact counts)

The OE reference notebook split rows at random. A time split is stricter: the same HCP can appear in train and test, but never in the same month, which is closer to how the model will be used.

### Step 4. Feature selection

**Clean-up.** 786 features have one single value on all 24,000 training rows (for example, a feature that is 0 for every sampled HCP). They cannot help the model and are dropped, leaving **16,452 features** (source: `constant_features_dropped.csv`, `run_summary.json`).

**Model.** One LightGBM model learns to predict Kerendia NBRx from all 16,452 features. The settings follow the OE reference notebook, with one change: a Poisson objective instead of plain squared error, because the target is a count that is mostly zero.

| Setting | Value |
| --- | --- |
| Objective | Poisson (count target) |
| Trees | 250 |
| Learning rate | 0.05 |
| Leaves per tree | 31 |
| Minimum rows per leaf | 100 |
| Feature and row sampling | None: every tree sees all features and all rows |
| Random seed | 42 (the run gives identical results every time) |

(source: `run_summary.json`)

**Ranking.** For each feature we compute SHAP: how much the feature moves each prediction, averaged over all 24,000 training rows. Features are ranked by that average impact, and the top 1,000 are kept. SHAP is preferred over the model's own gain score because it measures the effect on predictions directly; both are saved.

### Step 5. What came out

Run: feature selection job run `1011506234707993`, 2026-11-24, 12 minutes, SUCCESS (source: `run_summary.json`).

| Step | Features |
| --- | --- |
| Candidates from Combine | 17,238 |
| Dropped as constant | 786 |
| Used by the model | 16,452 |
| With any SHAP impact | 2,648 |
| **Selected** | **1,000** |

(source: `run_summary.json`)

**How the model did** (source: `train_test_metrics.csv`)

| Part | Rows | R2 | RMSE | MAE | Actual NBRx | Predicted NBRx |
| --- | --- | --- | --- | --- | --- | --- |
| Train (c1-c24) | 24,000 | 0.979 | 0.031 | 0.005 | 504 | 504.5 |
| Test (c25-c26) | 2,000 | 0.377 | 0.220 | 0.032 | 68 | 31.2 |

The gap between train and test is expected with only 1,000 HCPs: the model learns the sample very closely and holds up only partly on later months. On test, it predicts 46% of the actual NBRx. For feature selection this is acceptable, because we use the model to rank features, not to forecast.

**Top 15 features** (source: `shap_ranking_all_features.csv`)

| Rank | Feature | Share of total SHAP |
| --- | --- | --- |
| 1 | `RUNNING_TOTAL_RX_CLAIMS_KERENDIA` | 4.18% |
| 2 | `PCT_TOTAL_RX_CLAIMS_SGLT2_MEDICARE_PART_D_IN_LAST_3_MONTH` | 3.11% |
| 3 | `PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_UACR_STAGE_UNKNOWN_WITH_CALCIUM_CHANNEL_OR_BETA_BLOCKER_IN_LAST_3_MONTH` | 2.04% |
| 4 | `PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_UACR_STAGE_UNKNOWN_WITH_INSULIN_IN_LAST_12_MONTH` | 1.89% |
| 5 | `FLD_KER_PRIMARY_SHARE_12M` | 1.83% |
| 6 | `PCT_TOTAL_RX_CLAIMS_METFORMIN_COMMERCIAL_IN_LAST_6_MONTH` | 1.75% |
| 7 | `KERENDIA_TRX_APPROVED_IN_LAST_3_MONTH` | 1.45% |
| 8 | `MIN_EVENT_TIME_EGFR_TEST_ALL_LOINC_VARIANTS_TIME_MIN` | 1.44% |
| 9 | `PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_GFR_STAGE_3_AND_UACR_STAGE_UNKNOWN_IN_LAST_3_MONTH` | 1.28% |
| 10 | `PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_UACR_STAGE_UNKNOWN_WITH_CALCIUM_CHANNEL_OR_BETA_BLOCKER_IN_LAST_6_MONTH` | 1.20% |
| 11 | `PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_DX_UACR_STAGE_UNKNOWN_WITH_KERENDIA_IN_LAST_6_MONTH` | 1.16% |
| 12 | `PCT_TOTAL_RX_CLAIMS_SGLT2_AGE_GROUP_70_80_IN_LAST_12_MONTH` | 0.83% |
| 13 | `PCT_TOTAL_RX_CLAIMS_METFORMIN_NOT_30_60_90_DAYS_SUPPLY_IN_LAST_6_MONTH` | 0.76% |
| 14 | `FLD_DAYS_SINCE_LAST_INT` | 0.73% |
| 15 | `PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_TEST_GFR_STAGE_2_WITH_METFORMIN_IN_LAST_12_MONTH` | 0.71% |

The list makes business sense: an HCP's Kerendia history comes first, followed by the mix of their CKD / T2D patients (UACR and GFR stage, SGLT2, metformin) and field promotion.

**Where the selected features come from** (source: feature dictionary + `shap_ranking_all_features.csv`)

| Category | Features | Constant (dropped) | With SHAP impact | Selected | Share of total SHAP | Best rank |
| --- | --- | --- | --- | --- | --- | --- |
| Claims | 8,458 | 346 | 1,573 | 547 | 59.9% | 1 |
| Patient events | 4,687 | 75 | 653 | 305 | 24.7% | 8 |
| Rx market | 3,300 | 251 | 316 | 103 | 9.4% | 7 |
| Promotional, personal | 128 | 15 | 21 | 11 | 4.1% | 5 |
| Promotional, non-personal | 520 | 98 | 48 | 15 | 1.0% | 72 |
| Static HCP | 142 | 1 | 36 | 18 | 0.8% | 171 |
| Added by Combine (calendar) | 3 | 0 | 1 | 1 | 0.1% | 344 |
| **Total** | **17,238** | **786** | **2,648** | **1,000** | **100%** | |

Every category is represented. Personal promotion is small in count (11 features) but carries 4.1% of the impact, with `FLD_KER_PRIMARY_SHARE_12M` at rank 5. Two DTC features are selected: `DTC_SOCIAL_CLICKS_PER_1K_ADULTS_3M` (rank 161) and `DTC_SEARCH_CLICKS_PER_1K_ADULTS_1M` (rank 249).

### Step 6. How much to trust the list

Impact is concentrated at the top (source: `shap_ranking_all_features.csv`):

| Top features | Share of total SHAP |
| --- | --- |
| Top 10 | 20.2% |
| Top 100 | 48.4% |
| Top 300 | 67.9% |
| Top 1,000 | 89.9% |

Half of all impact sits in the first 111 features; 90% is reached at rank 1,006.

How often the model actually uses a feature tells us how stable its rank is (median number of tree splits that use the feature, out of 250 trees; source: `all_feature_importance_gain.csv`):

| Ranks | Median splits |
| --- | --- |
| 1-100 | 14 |
| 101-300 | 5 |
| 501-1,000 | 2 |

So, with 1,000 HCPs:

* **The top 100-300 are solid.** They are used often by the model and carry most of the impact.
* **Ranks 500-1,000 are borderline.** They are used about twice each, so whether a feature lands at rank 800 or 1,200 is close to chance. The cause is the amount of signal in the sample: 504 NBRx in the training rows.

---

## How to run it again

1. **Combine** with a sample: run the Combine notebook with the test sample set to 1,000 HCPs (0 = all HCPs). It writes to `_test_sample_1000/` under the chosen run folder. The 1,000-HCP run took 137 minutes.
2. **Feature selection**: run `01_nba_3_0_method_shap_1000_hcps` from the first cell (it installs LightGBM and SHAP), with the same run name and sample size. The 1,000-HCP run took 12 minutes.

The notebook stops on its own if an input is missing, if any HCP does not have all 28 cohorts, or if the target join gains or loses rows.

---

## Open points

**1. Sample size for the final feature list**

* *Background:* the ranking above comes from 1,000 of 294,726 HCPs (0.3%). The top 100-300 are stable; ranks 500-1,000 are not (Step 6). The notebook loads all features into memory. The 1,000-HCP run fits on the standard serverless notebook (16 GB); memory use grows with the number of HCPs, so a much larger sample needs more memory.
* *Options:* (a) keep the 1,000-HCP list and treat ranks 500-1,000 as provisional; (b) re-run Combine and feature selection on a larger sample, using the notebook's High memory setting (32 GB) or a larger cluster for the feature selection step.
* *Effect:* (b) gives a more reliable tail of the list; the top features are not expected to change much. It needs a new Combine run with the larger sample before feature selection.

**2. HCP list: Combine and the target use different lists**

* *Background:* Combine uses `HCP_Universe_without_call_hcps` (294,726 HCPs). The target table covers `HCP_Universe` (314,920 HCPs). 294,688 HCPs are in both; 20,232 target HCPs are not in Combine's list, and 38 Combine HCPs have no target (source: exact comparison of the two lists).
* *Decision:* keep Combine's list. Only HCPs in both lists are used, so the 20,232 HCPs are not part of feature selection, and the 38 HCPs without a target are set aside by the notebook.
* *Effect:* none on the 1,000-HCP run (all 1,000 sampled HCPs have a target). For a full run, up to 38 HCPs would be set aside.
