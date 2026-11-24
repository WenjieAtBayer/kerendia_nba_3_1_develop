# NBA 3.0 Production Model — Feature Evaluation (752 features)

**Purpose:** Find which feature families carry the NBA 3.0 HCP model signal, which features are dead, sparse or redundant, and how the source-review findings touch them.
**Date:** 2026-11-23
**Model:** MLflow run `f583bcbc9d56477fae983d44c16f8c70` (LightGBM `LGBMRegressor`, Tweedie, 659 trees). Every `runs:/` reference in `NBA 3.0 Ops - Pipeline` (11 hits) is this run.
**Data:** validation set `kerendia_nba_3_hcp_model_validation_data_v4.parquet` (443,446 HCP-cohort rows, cohorts C23 and C24), random 50,000-row sample (seed 42).
**Scorecard (752 rows):** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/dev_folder/notebook_output/feature_evaluation/NBA_3_0_Model_752_Feature_Scorecard.csv` (stored in the volume, not in this folder, because of its size)
**Related docs:** `../01_Source_Review/NBA_3_1_LAAD_Source_Review_Overview.md`, `../../../../../Feature Analysis/00_README.md`

---

## 1. Model and target checks

| Check | Result |
| --- | --- |
| Feature count | 752 in the model signature, all unique, same order as the booster |
| SHAP artifact in the run (`Shap_Importances.csv`) | same 752 features, no duplicates |
| Features absent from validation data | 1: `DIGITAL_BANNER_EXPOSURE_IN_LAST_1_MONTH` (set to missing for scoring) |
| Zero-gain / zero-SHAP features | 1 / 1 |
| Metrics logged in the run | none |
| Target (`HCP_Target_Variable`) | sum of Kerendia NBRx flags per `PROVIDER_ID` × cohort in the prediction window; built from `FCT_RX` with `CLAIM_TYPE = 'PD'` only; data 2023-04-07 to 2025-06-06 |

**Note:** the target uses paid claims only, but the 3.1 feature pipeline (PJ03/NB01) has no claim-type filter (see Rx review RX-A). Features and target count claims differently.

## 2. Importance by family

Families are assigned by keywords in the feature name (heuristic; 51 features unmapped). SHAP shares sum to 100%.

| Family | Features | SHAP share (run artifact) | SHAP share (validation sample) | Gain share |
| --- | --- | --- | --- | --- |
| Rx claims (other products) | 294 | 34.73% | 34.56% | 8.36% |
| Kerendia prior writing (NBRx/NPS) | 110 | 21.33% | 22.87% | 73.75% |
| Other / unmapped (time, ACS zip, DTC, patient starts) | 51 | 10.06% | 10.59% | 3.26% |
| Promotion — F2F/calls | 32 | 9.26% | 8.13% | 8.27% |
| Market access / payer | 70 | 6.51% | 6.55% | 1.93% |
| Lab claims | 97 | 6.48% | 6.46% | 1.77% |
| Dx / comorbidity claims | 48 | 3.27% | 3.10% | 0.85% |
| Px claims | 27 | 3.28% | 3.04% | 0.68% |
| HCP profile / affiliation | 9 | 2.89% | 2.71% | 0.51% |
| Promotion — digital/email | 13 | 1.05% | 1.02% | 0.34% |
| Adoption speed | 1 | 1.13% | 0.96% | 0.28% |

* Validation-sample SHAP ranks match the run artifact closely (Spearman 0.99).
* Signal is concentrated: top 50 features = 40.5% of SHAP, top 100 = 54.9%; the bottom 400 together = 13.59%.
* Gain is dominated by Kerendia prior writing (73.75%), so gain alone overstates that family.
* Cross-check with `Feature Analysis/00_README.md`: adoption speed 1.13% here vs 1.10% there. The README comorbidity figure (0.54%) covers 3 specific features, so it is not comparable with the broader Dx family above.

## 3. Top 20 features (validation sample)

Ranks in cohorts C23 and C24 are within 5 places of each other for all 20.

| Rank | Feature | Family |
| --- | --- | --- |
| 1 | TOTAL_F2F_IN_LAST_6_MONTH | Promotion — F2F |
| 2 | TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_12_MONTH | Kerendia writing |
| 3 | KERENDIA_RX_TIME_MIN | Kerendia writing |
| 4 | RUNNING_TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA | Kerendia writing |
| 5 | MONTHS_SINCE_KER_LAUNCH | Time |
| 6 | AFFL_COUNT | HCP profile |
| 7 | RUNNING_TOTAL_HCP_RX_REJECTED_KERENDIA_CLAIMS | Kerendia writing (rejected claims) |
| 8 | NUM_HCPS_IN_BUILDING | HCP profile |
| 9 | TOTAL_F2F_IN_LAST_5_MONTH | Promotion — F2F |
| 10 | TOTAL_HCP_RX_MAIL_ORDER_CHANNEL_CLAIMS_IN_LAST_12_MONTH | Rx claims |
| 11 | TOTAL_HCP_NBRX_CLAIMS_INDICATION_GROUP_T2D_AND_CKD_AND_CVD_IN_LAST_12_MONTH | Kerendia writing |
| 12 | RUNNING_TOTAL_RX_CLAIMS_ACE_OR_ARB_COMMERCIAL | Market access |
| 13 | TOTAL_F2F_IN_LAST_3_MONTH | Promotion — F2F |
| 14 | TOTAL_F2F_IN_LAST_4_MONTH | Promotion — F2F |
| 15 | TIME_TO_ADOPT_FARXIGA | Adoption speed |
| 16 | CALENDAR_MONTH | Time |
| 17 | RUNNING_TOTAL_HCP_TRX_CLAIMS_ADD_ON_TO_KERENDIA | Kerendia writing |
| 18 | TOTAL_F2F_IN_LAST_2_MONTH | Promotion — F2F |
| 19 | TOTAL_PATIENTS_START_SGLT2_IN_LAST_6_MONTH | Patient starts |
| 20 | NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_LISINOPRIL_HCTZ_IN_LAST_360_DAYS_RX | Rx claims |

* Five overlapping F2F windows (2–6 months) in the top 20: one window plus a recency feature would probably carry the same signal.
* Rejected Kerendia claims (rank 7) are a strong signal (likely access friction). So the 3.1 claim-type fix (RX-A) should **split** paid and rejected claims, not just drop rejected ones.
* Time features (`MONTHS_SINCE_KER_LAUNCH`, `CALENDAR_MONTH`) rank high; they track launch maturity and may not generalise to new indications.

## 4. Dead, sparse and redundant features

| Check | Count | SHAP share |
| --- | --- | --- |
| Near-duplicate clusters (abs r > 0.95, sample) | 86 clusters, 274 features | |
| Redundant (in a cluster, not its top-SHAP member) | 188 | 15.06% |
| Low value (< 0.01% SHAP share) | 57 | |
| Sparse (≥ 99% zero or missing) | 14 | |

Largest clusters:

| Size | SHAP share | Example members |
| --- | --- | --- |
| 22 | 1.31% | Kerendia patients in last 90/180/360 days, Kerendia NRx last 3 months |
| 15 | 0.86% | Retail-channel and continue-source-of-business claim counts |
| 12 | 1.01% | SGLT2 class and `SGLT2_WO_INVOKANA_300MG` counts (confirms O9) |
| 11 | 0.74% | Nephrology-specialty TRx/NRx/NBRx counts |
| 6 | 1.40% | Add-on source-of-business NBRx/TRx/NRx |
| 6 | 0.32% | Medicare Part D and age 65+ claim counts |
| 5 | 0.35% | SGLT2 30-day-supply counts |
| 4 | 0.21% | GFR/UACR stage-unknown + metformin counts |

## 5. Scorecard recommendations

Rule: drop = low value and redundant; drop candidate = low value or sparse; dedupe = redundant, keep the best member of its cluster; fix = absent from the data.

| Family | Keep | Dedupe | Drop candidate | Drop | Fix |
| --- | --- | --- | --- | --- | --- |
| Rx claims (other products) | 205 | 72 | 13 | 4 | 0 |
| Kerendia prior writing | 67 | 31 | 2 | 10 | 0 |
| Lab claims | 72 | 23 | 1 | 1 | 0 |
| Market access / payer | 56 | 14 | 0 | 0 | 0 |
| Other / unmapped | 44 | 4 | 3 | 0 | 0 |
| Dx / comorbidity | 33 | 7 | 6 | 2 | 0 |
| Px claims | 19 | 5 | 3 | 0 | 0 |
| Promotion — F2F/calls | 10 | 7 | 12 | 3 | 0 |
| Promotion — digital/email | 8 | 2 | 1 | 1 | 1 |
| HCP profile / affiliation | 7 | 2 | 0 | 0 | 0 |
| Adoption speed | 1 | 0 | 0 | 0 | 0 |
| **Total** | **522** | **167** | **41** | **21** | **1** |

188 features (dedupe + drop), or 229 including drop candidates, could be removed for 3.1 with little expected loss, to be confirmed by a retrain. These are statistical recommendations only, not business decisions.

## 6. Source findings that touch the model

| Source finding | Families affected | SHAP share at stake |
| --- | --- | --- |
| RX-A reversed/rejected Rx claims counted | Rx claims, Kerendia writing | ~57% |
| S3 lab HIST reloads | Lab claims | ~6.5% |
| DX-A / PX-B Jan 2023 coverage step | Dx, Px | ~6% |

## 7. Not checked

* Leakage: feature windows vs the prediction window were not checked feature by feature. The target is future NBRx, so trailing-window features are expected to be safe; `RUNNING_TOTAL_*` features should be checked to confirm they stop before the prediction start.
* Tuning and back-test metrics (not logged in the production run).
* Cohorts other than C23/C24 (the validation file has only these two).
* How these numbers line up with the 3.1 feature selection notebooks in `kerendia_nba_3_1_develop_sm/Feature Selection`.
