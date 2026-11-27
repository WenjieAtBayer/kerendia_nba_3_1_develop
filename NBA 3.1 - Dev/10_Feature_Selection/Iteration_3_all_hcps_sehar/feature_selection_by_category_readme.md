# Feature selection by category (Kerendia NBA 3.1)

This folder selects the strongest HCP-level features for predicting Kerendia NBRx, **separately for each feature category and for existing writers vs non-writers**. Each category notebook reads only its own source tables (the same ones NBA 3.1 Combine uses), applies the same fill rules, and runs the same two-part method. All shared logic lives in one core notebook; the category notebooks only set a small config.

**Status (2026-11-27):** all six categories have run on the **full HCP universe (294,726 HCPs) for cohorts c12-c24** (3,831,438 HCP-month rows). Every run passed its built-in checks.

## Notebooks in this folder

| Notebook | Category | Source tables | Features |
| --- | --- | --- | --- |
| 00_category_feature_selection_core | (shared logic, run via %run) | - | - |
| 01_claims_feature_selection | Claims (Rx, Dx, lab, monthly, NPS, eligible patients) | 6 | 8,458 |
| 02_patient_events_feature_selection | Patient events (Rx / Dx / Px / lab first occurrence, frequency, recency, hospitalization + add-on) | 15 | 4,687 |
| 03_sales_feature_selection | Sales (NBRx, NRx, TRX, competitor share, competitor NBRx share) | 5 | 3,311 |
| 04_promotional_feature_selection | Promotional (personal field activity + non-personal HQ email, digital, high intent, DTC, OE) | 11 | 648 |
| 05_static_feature_selection | Static HCP (physician attributes, census/SDoH, colocation/IDN, market events + calendar) | 4 | 81 |
| 06_comorb_claims_feature_selection | Comorbidity claims (09 claim comorbidity, 10 Kerendia prior writing, 11 adoption) | 3 | 53 |

Each category notebook = pip install LightGBM + category config (CATEGORY, LABEL, SOURCE_TABLES, paths) + `%run ./00_category_feature_selection_core`.

## Methodology

### Data
* **HCPs:** full universe without call HCPs (294,726; the placeholder HCP "0" is excluded). Weight 1 per row. (`SAMPLE_LIST` can instead point to the 10k option-A sample with its group weights.)
* **Cohorts:** c12-c24 (13 cohorts; lookback end fully included, 2-month gap before the prediction month). The `COHORTS` widget defaults to c1-c28.
* **Rows:** 294,726 x 13 = 3,831,438 HCP-months: 314,535 writer rows (36,654 HCPs; 89,861 weighted NBRx) and 3,516,903 non-writer rows (283,797 HCPs; 22,881 NBRx).
* **Target:** Kerendia NBRx in the prediction month (from the target_variable table).
* **Writer definition:** TOTAL_HCP_NBRX_CLAIMS_KERENDIA_IN_LAST_12_MONTH > 0 (empty = 0), joined on HCP_COHORT_ID.
* **Fill rules:** exactly as in NBA 3.1 Combine (0 for counts, -9999 for first-occurrence, 9999 for time-since, c1-c24 median for census features and HCP_EXPERIENCE). Verified feature-by-feature against the Combine feature dictionary (0 mismatches).
* **Cohort guard:** the run stops if any source table is missing one of the chosen cohorts.

### Part 1 - writers vs non-writers
* Mean / median analysis of every feature in the two groups, weighted by row weight.
* **DISCRIMINATION = |2 x AUC - 1|** (weighted AUC: chance that a writer row has a higher value than a non-writer row; ties share half the credit). 1.0 = perfect separation, 0 = no difference. Plus medians, means and Cohen's d.

### Part 2 - per group (writers, non-writers separately)
1. **NBA 3.1 statistical clean-up:** stage 1 constant; stage 2 near-constant (>= 99.5% one value); stage 3 low fill (< 1% non-default); stage 4 near-copy (Spearman >= 0.95 with a stronger kept feature); flag 5 no signal (linear rho and non-linear eta both below the 99th percentile of noise-shuffled NBRx); flag 6 unstable (link not repeated in both halves of the doctors).
2. **Model:** one over-fitted LightGBM Poisson model per group on all chosen cohorts (500 trees, lr 0.05, 63 leaves, min 20 rows/leaf, no hold-out). Over-fitted on purpose - it ranks features, it is not a performance estimate.
3. **SHAP:** exact tree SHAP via pred_contrib on every row; features ranked by weighted mean |SHAP|, with the sign of the link (Spearman of value vs SHAP) and gain/splits.
4. **Best features:** SHAP rank with mean / median, discrimination and clean-up results side by side.

### Performance
The per-feature statistics (steps 6-7) are compiled numba kernels: one sort per feature, run in parallel on all driver cores. In test runs the notebook also runs the old numpy code and asserts the results match (max difference 1e-13). At 3.83M rows this cut the statistics from hours to minutes (claims step 6: 22 min; step 7: 17 min).

### Outputs
Per category, in `dev_pipeline/notebook_output/feature_selection_by_category/<RUN_NAME>/<category>/`: keys (HCP x cohort rows), category_data (filled features), mean_median_writers_vs_non_writers.csv, cleanup_funnel.csv, cleanup_stats_{group}.csv, model_fit_in_sample.csv, shap_ranking_{group}.csv, shap_by_sub_category.csv, shap_coverage.csv, group_summary.csv, feature_dictionary.csv, model_{group}.txt, model_{group}_feature_order.csv, run_info.json.

## Runs and jobs

| Run | Scope | Result |
| --- | --- | --- |
| dev_test (job 762617886630299, earlier) | 10k sample x 28 cohorts, 400 HCPs x 300 features x 50 trees | 6/6 SUCCESS; validated the design |
| 500-HCP test (run 50222855418455) | full universe, c12-c24, 500 HCPs (6,500 rows), all features, 500 trees | 6/6 SUCCESS; numba = numpy (max diff 1e-13); all checks passed |
| Full run (runs 945311089393562, 94743834955567, 678075036280586) | full universe, c12-c24, 3,831,438 rows, all features, 500 trees | 6/6 SUCCESS; all checks passed |

Jobs: "Kerendia NBA 3.1 - Feature selection by category (claims)" (945010120582940), "(patient events)" (876237751115631), "(sales, promotional, static, comorb)" (106572619213657). Note: the workspace subnet (subnet-0a61978844dd2385e) ran out of free IP addresses when several clusters started at once - patient events needed retries and its own job.

## Full-run results (full universe, c12-c24, RUN_NAME full_universe_c12_c24)

### Clean-up funnel (features removed per stage)

| Category | Start | 1 constant | 2 near-const | 3 low fill | 4 near-copy | In model (W / NW) | No flag (W / NW) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Claims | 8,458 | 128 / 84 | 814 / 1,263 | 276 / 314 | 3,324 / 2,986 | 3,916 / 3,811 | 1,109 / 47 |
| Patient events | 4,687 | 23 / 14 | 444 / 828 | 323 / 457 | 782 / 630 | 3,115 / 2,758 | 620 / 110 |
| Sales | 3,311 | 138 / 119 | 460 / 647 | 137 / 144 | 774 / 691 | 1,802 / 1,710 | 380 / 83 |
| Promotional | 648 | 49 / 42 | 130 / 244 | 39 / 40 | 100 / 92 | 330 / 230 | 55 / 0 |
| Static | 81 | 1 / 1 | 0 / 0 | 1 / 1 | 4 / 5 | 75 / 74 | 26 / 0 |
| Comorb-claims | 53 | 0 / 0 | 0 / 5 | 0 / 5 | 6 / 2 | 47 / 41 | 23 / 0 |

(W / NW = writers / non-writers. "No flag" = kept after stage 4 AND neither signal flag set - these are the clean candidates.)

### Model fit (in-sample, by design)

| Category | Writers: deviance explained / Spearman | Non-writers: deviance explained / Spearman |
| --- | --- | --- |
| Claims | 0.54 / 0.49 | 0.47 / 0.12 |
| Patient events | 0.52 / 0.47 | 0.44 / 0.11 |
| Sales | 0.52 / 0.47 | 0.43 / 0.11 |
| Promotional | 0.39 / 0.39 | 0.29 / 0.09 |
| Static | 0.36 / 0.37 | 0.25 / 0.09 |
| Comorb-claims | 0.48 / 0.45 | 0.30 / 0.09 |

Spearman is capped by the ~99% of zero-NBRx rows among non-writers, not by a bug.

### Top features by discrimination (writers vs non-writers, \|2 x AUC - 1\|)

DISCRIMINATION is computed once per feature, from both groups together. AUC = chance that a random writer row has a higher value than a random non-writer row, so DISCRIMINATION = \|2 x AUC - 1\| measures how well the feature separates the groups (0 = no difference, 1 = perfect) without saying which side is higher. HIGHER_IN gives the direction (AUC > 0.5: higher in writers; AUC < 0.5: higher in non-writers). The two tables below split the ranking by that direction.

#### Higher in writers (AUC > 0.5)

| Category | Top features (DISCRIMINATION; median writers vs non-writers) |
| --- | --- |
| Claims | TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_12_MONTH (0.96; 15 vs 0), PCT_TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_12_MONTH (0.95; 0.005 vs 0), RUNNING_TOTAL_RX_CLAIMS_KERENDIA (0.94; 26 vs 0) |
| Patient events | NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_360_DAYS (0.97; 3 vs 0), NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_180_DAYS (0.91; 2 vs 0), MAX_EVENT_TIME_KERENDIA_FIRST_OCCURRENCE (0.88; 658 vs -9999 = never) |
| Sales | PERC_KERENDIA_MRA_SHARE_12M, PERC_KERENDIA_HF_DRUG_SHARE_12M, KERENDIA_IN_LAST_12_MONTH (all 1.00 - built from the same Kerendia NBRx that defines the writer flag) |
| Promotional | KERENDIA_WRITER_EVER_FLAG (0.86; 1 vs 0), OE_EXPOSURE_TOUCHPOINT_P9 (0.75; 42 vs 0), OE_EXPOSURE_TOUCHPOINT_P6 (0.75; 29 vs 0) |
| Static | COLOC_HQ_PEER_SHARE_3M (0.25), COLOC_PRAC_PEER_SHARE_3M (0.20), AFFL_NEPH_ACCT_COUNT (0.20) |
| Comorb-claims | KERENDIA_TRX_APPROVED_IN_LAST_12_MONTH (0.96; 13 vs 0), KERENDIA_TRX_IN_LAST_12_MONTH (0.96; 15 vs 0), KERENDIA_NBRX_IN_LAST_12_MONTH (0.95; 2 vs 0) |

#### Higher in non-writers (AUC < 0.5)

| Category | Top features (DISCRIMINATION; median writers vs non-writers) |
| --- | --- |
| Claims | PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_1_ACTIVE_TREATMENT_IN_LAST_12_MONTH (0.39; 0.19 vs 0.25), PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_1_ACTIVE_TREATMENT_IN_LAST_6_MONTH (0.37), PCT_TOTAL_RX_CLAIMS_PATIENT_WITH_1_ACTIVE_TREATMENT_IN_LAST_3_MONTH (0.36) |
| Patient events | MIN_EVENT_TIME_JARDIANCE_TIME_MIN (0.16; 2 vs 4), MIN_EVENT_TIME_FARXIGA_TIME_MIN (0.13; 3 vs 7), MIN_EVENT_TIME_FUROSEMIDE_TIME_MIN (0.09; 3 vs 4) |
| Sales | PERC_GLP1_NBRX_SHARE_T2D_IN_LAST_12_MONTH (0.11; 0.54 vs 0.63), PERC_JARDIANCE_NBRX_SHARE_12M (0.08; 0.52 vs 0.62), PERC_GLP1_NBRX_SHARE_T2D_IN_LAST_3_MONTH (0.07) |
| Promotional | MONTHS_SINCE_FIRST_KERENDIA_RX (0.85; 23 vs 999), DIGITAL_DAYS_SINCE_LAST_EXPOSURE (0.67; 0 vs 999), FLD_DAYS_SINCE_LAST_INT (0.62; 45 vs 999) |
| Static | ACS_PCT_WHITE_NONHISP_ZC (0.17; 59.5 vs 67.2), TERR_SDOH_WHITE (0.15), COUNTY_SDOH_WHITE (0.14) |
| Comorb-claims | MIN_DAYS_TO_PRESCRIBE_FARXIGA_POST_FIRST_CKD_DIAGNOSIS_ANY_HCP (0.49; 23 vs 440), MIN_DAYS_TO_PRESCRIBE_FARXIGA_POST_CKD_DIAGNOSIS (0.44; 24 vs 9999), MIN_DAYS_TO_PRESCRIBE_JARDIANCE_POST_FIRST_CKD_DIAGNOSIS_ANY_HCP (0.37; 18 vs 162) |

Read the non-writer table with care: most of these are "time since" / "days to" features, where a higher value means *longer ago or never* (999 / 9999 fill). So "higher in non-writers" here means writers had *more recent* Kerendia use, digital exposure, field calls and faster Farxiga/Jardiance uptake after CKD diagnosis. The genuinely higher-in-non-writers signals are weak (claims: share of Rx claims from single-treatment patients; sales: GLP-1 and Jardiance NBRx share; static: zip/territory % white).

#### Count of features by direction (full run)

| Category | DISCRIMINATION >= 0.5 (writers / non-writers higher) | >= 0.2 (writers / non-writers higher) | All features (writers / non-writers / same) |
| --- | --- | --- | --- |
| Claims | 202 / 0 | 2,249 / 31 | 7,952 / 435 / 71 |
| Patient events | 11 / 0 | 211 / 0 | 3,614 / 1,059 / 14 |
| Sales | 54 / 0 | 837 / 0 | 3,079 / 129 / 103 |
| Promotional | 78 / 4 | 172 / 11 | 576 / 30 / 42 |
| Static | 0 / 0 | 2 / 0 | 51 / 29 / 1 |
| Comorb-claims | 14 / 0 | 35 / 7 | 39 / 14 / 0 |

### Top features by SHAP - writers

| Category | Top features (weighted mean \|SHAP\| share, sign, flags) |
| --- | --- |
| Claims | TOTAL_PATIENTS_START_KERENDIA_IN_LAST_12_MONTH (11.6%, +, clean), TOTAL_PATIENTS_START_KERENDIA_IN_LAST_6_MONTH (7.4%, +, clean), RUNNING_TOTAL_PATIENTS_START_KERENDIA (6.4%, +, clean), TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_3_MONTH (4.2%, +, clean), TOTAL_PATIENTS_START_KERENDIA_IN_LAST_3_MONTH (2.6%, +, clean) |
| Patient events | NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_90_DAYS (19.5%, +, clean), NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_360_DAYS (14.2%, +, clean), NUM_OF_PATIENTS_THE_HCP_STARTED_ON_SGLT2_IN_LAST_90_DAYS_RX (5.0%, +, clean), MIN_EVENT_TIME_KERENDIA_TIME_MIN (3.8%, -, clean), LOGRATIO_FREQ_KERENDIA_IN_LAST_3_MONTH (3.5%, +, clean) |
| Sales | TOTAL_HCP_NBRX_CLAIMS_KERENDIA_IN_LAST_12_MONTH (15.2%, +, clean), RUNNING_TOTAL_HCP_NBRX_CLAIMS_KERENDIA (5.3%, +, clean), KERENDIA_IN_LAST_6_MONTH (3.8%, +, clean), TOTAL_HCP_NRX_CLAIMS_KERENDIA_IN_LAST_6_MONTH (3.5%, +, clean), TOTAL_NBRX_CLAIMS_HF_DRUG_IN_LAST_3_MONTH (2.8%, +, clean) |
| Promotional | SMPL_RCVD_UNITS_12M (7.6%, +, clean), FLD_DAYS_SINCE_LAST_INT (5.9%, -, clean), FLD_INT_KER_ONLY_3M (5.6%, +, clean), MONTHS_SINCE_FIRST_KERENDIA_RX (4.3%, +, clean), NEW_WRITER_LAST_12M_FLAG (3.4%, -, clean) |
| Static | AFFL_NEPH_ACCT_COUNT (17.3%, +, clean), HCP_EXPERIENCE (5.4%, +, clean), HCP_GENDER_F (5.4%, -, clean), AFFL_CARD_ACCT_COUNT (5.0%, +, unstable), COLOC_HQ_PEER_SHARE_3M (3.6%, +, clean) |
| Comorb-claims | KERENDIA_NBRX_IN_LAST_12_MONTH (25.1%, +, clean), KERENDIA_NBRX_IN_LAST_6_MONTH (14.3%, +, clean), KERENDIA_TRX_IN_LAST_3_MONTH (11.8%, +, clean), KERENDIA_NBRX_IN_LAST_3_MONTH (7.5%, +, clean), MIN_DAYS_TO_PRESCRIBE_FARXIGA_POST_FIRST_CKD_DIAGNOSIS_ANY_HCP (4.8%, -, clean) |

### Top features by SHAP - non-writers

| Category | Top features |
| --- | --- |
| Claims | RUNNING_TOTAL_RX_CLAIMS_KERENDIA (2.8%, +, clean), TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_12_MONTH (2.2%, +, clean), PCT_TOTAL_RX_CLAIMS_SGLT2_WO_INVOKANA_300MG_IN_LAST_6_MONTH (1.4%, +), TOTAL_RX_CLAIMS_PATIENT_WITH_DX_UACR_STAGE_UNKNOWN_WITH_KERENDIA_IN_LAST_12_MONTH (1.4%, +), TOTAL_RX_CLAIMS_GLP_1_NEW_PRESCRIPTION_IN_LAST_12_MONTH (1.3%, -) |
| Patient events | MAX_EVENT_TIME_KERENDIA_FIRST_OCCURRENCE (5.4%, +, clean), NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_FARXIGA_IN_LAST_180_DAYS (5.1%, +, clean), PCT_OF_PATIENTS_THE_HCP_STARTED_ON_SGLT2_IN_LAST_90_DAYS_RX (3.3%, +, clean), NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_METFORMIN_HYDROCHLORIDE_E_IN_LAST_360_DAYS (2.9%, -), NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_OZEMPIC_IN_LAST_360_DAYS (2.5%, +) |
| Sales | RUNNING_TOTAL_HCP_NRX_CLAIMS_KERENDIA (3.0%, +, clean), TOTAL_NBRX_SGLT2_CKD_IN_LAST_12_MONTH (2.5%, +, clean), RUNNING_TOTAL_HCP_NRX_CLAIMS_INDICATION_GROUP_OTHERS (1.9%, -), TOTAL_NBRX_GLP1_T2D_IN_LAST_12_MONTH (1.5%, -), RUNNING_TOTAL_HCP_TRX_CLAIMS_ADD_ON_TO_KERENDIA (1.4%, +, clean) |
| Promotional | FLD_DAYS_SINCE_LAST_INT (18.4%, -, no signal), KERENDIA_WRITER_EVER_FLAG (13.5%, +, no signal), DTC_SEARCH_IMPRESSIONS_PER_1K_ADULTS_3M (9.8%, +), HQ_EMAIL_DAYS_SINCE_LAST_SENT (4.3%, +), FLD_CODETAIL_PERIOD_FLAG (3.4%, +) |
| Static | DAYS_SINCE_FARXIGA_LOE (7.1%, +), HCP_GENDER_F (6.0%, -), TERR_SDOH_LT_HS (5.7%, +), AFFL_CARD_ACCT_COUNT (5.6%, +), COLOC_BLDG_PEER_WRITERS_3M (5.6%, +) |
| Comorb-claims | MIN_DAYS_TO_PRESCRIBE_FARXIGA_POST_FIRST_CKD_DIAGNOSIS_ANY_HCP (14.0%, -), KERENDIA_TRX_IN_LAST_12_MONTH (13.0%, +), MIN_DAYS_TO_PRESCRIBE_JARDIANCE_POST_FIRST_CKD_DIAGNOSIS_ANY_HCP (8.1%, -), MIN_DAYS_TO_PRESCRIBE_ENTRESTO_POST_FIRST_CKD_DIAGNOSIS_ANY_HCP (7.9%, -), HCP_TIME_TO_ADOPT_JARDIANCE (6.8%, +) |

"clean" = kept after stage 4 with no signal/unstable flag. In claims, patient events and sales the very top non-writer SHAP features are clean; in promotional, static and comorb-claims none of the non-writer features is clean (0 kept with no flag) (they beat the noise bar in-sample but their link is weak - 22,881 NBRx spread over 3.5M rows).

### Sub-category SHAP shares (non-writers)

| Category | Where the SHAP importance sits |
| --- | --- |
| Claims | Rx claims 62.9%, monthly claims 21.0%, Rx NPS 10.0% |
| Patient events | RX frequency 47.0%, RX first occurrence 15.2%, add-on 14.0% |
| Sales | NRX 33.2%, TRX 32.1%, NBRX 20.7% |
| Promotional | personal field activity ~55% (FLD features), DTC ~13%, HQ email ~8% |
| Static | census/SDoH dominant, colocation/IDN second, physician attributes third |
| Comorb-claims | comorbidity ~40%, adoption ~35%, prior writing ~25% |

### How many features cover 90% of SHAP

| Category | Writers | Non-writers |
| --- | --- | --- |
| Claims | 1,043 | 979 |
| Patient events | 485 | 306 |
| Sales | 462 | 459 |
| Promotional | 100 | 56 |
| Static | 42 | 39 |
| Comorb-claims | 18 | 19 |

### Runtimes (full universe, c12-c24)

| Category | Total (min) | Slowest steps |
| --- | --- | --- |
| Claims | 167 | load into memory 40, SHAP 39, model 29, build 19 |
| Patient events | 177 | SHAP 74, build 49, load 19 |
| Sales | 145 | load 29, build 17, model 10, SHAP 10 |
| Promotional | 80 | SHAP ~60 |
| Static | 70 | SHAP ~55 |
| Comorb-claims | 58 | SHAP ~45 |

Clusters (Job Compute policy, 16.4 LTS ML): claims r5d.16xlarge driver + 4-12 r5d.4xlarge; patient events r5d.8xlarge + 2-4 r5d.4xlarge; sales r5d.8xlarge + r5d.2xlarge; promotional/static/comorb m5d.8xlarge drivers.

## Where to find the full feature lists

The tables above show only the top 3-5 features. The complete lists for every model are CSV files in the UC volume, one folder per category:

`/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/feature_selection_by_category/full_universe_c12_c24/<category>/`

where `<category>` is `claims`, `patient_events`, `sales`, `promotional`, `static` or `comorb_claims`. (The `_test_500_hcps_0_features/` sub-folder holds the 500-HCP test run - do not use it for selection.)

### Full SHAP ranking per model (main list to use)

| Category | Writers model | Non-writers model |
| --- | --- | --- |
| Claims | `claims/shap_ranking_writers.csv` (3,916 features) | `claims/shap_ranking_non_writers.csv` (3,811) |
| Patient events | `patient_events/shap_ranking_writers.csv` (3,115) | `patient_events/shap_ranking_non_writers.csv` (2,758) |
| Sales | `sales/shap_ranking_writers.csv` (1,802) | `sales/shap_ranking_non_writers.csv` (1,710) |
| Promotional | `promotional/shap_ranking_writers.csv` (330) | `promotional/shap_ranking_non_writers.csv` (230) |
| Static | `static/shap_ranking_writers.csv` (75) | `static/shap_ranking_non_writers.csv` (74) |
| Comorb-claims | `comorb_claims/shap_ranking_writers.csv` (47) | `comorb_claims/shap_ranking_non_writers.csv` (41) |

Each file has one row per feature in that model, sorted by `SHAP_RANK` (1 = most important). Key columns: `MEAN_ABS_SHAP`, `SHAP_SHARE`, `SHAP_CUM_SHARE` (cumulative - the features covering 90% of SHAP are the rows up to and including the first one with `SHAP_CUM_SHARE >= 0.9`, i.e. `SHAP_RANK <= features_for_90pct_shap` from `shap_coverage.csv`), `SHAP_DIRECTION_RHO` (+ = higher value raises predicted NBRx), `GAIN`, `SUB_CATEGORY`, the writers-vs-non-writers stats (`DISCRIMINATION`, `DISCRIMINATION_RANK`, `HIGHER_IN`, `MEAN_/MEDIAN_WRITERS`, `MEAN_/MEDIAN_NON_WRITERS`), the clean-up stats (`SIGNAL_SCORE`, `RHO`, `ETA`, `FILL_SHARE`) and the flags `FLAG_5_NO_SIGNAL`, `FLAG_6_UNSTABLE`. For a clean shortlist, filter both flags = False and sort by `SHAP_RANK`.

### Other per-category files

| File | What it holds |
| --- | --- |
| `mean_median_writers_vs_non_writers.csv` | All features of the category (before clean-up), ranked by `DISCRIMINATION_RANK`; means, medians, SDs, fill shares, AUC, Cohen's d, `HIGHER_IN` |
| `cleanup_stats_writers.csv` / `cleanup_stats_non_writers.csv` | All features with every clean-up result per group: stage removed (`REMOVED_AT`, `REASON`), near-copy partner (`COPY_OF`, `RHO_WITH_COPY`), signal and noise bars, half-sample stability, `SELECTED`, `PASSES_ALL_SIX` |
| `cleanup_funnel.csv` | Features removed / flagged at each stage, per group |
| `shap_by_sub_category.csv` | SHAP share per sub-category, per group |
| `shap_coverage.csv` | Features in model / used by trees / needed for 80%, 90%, 95% of SHAP |
| `model_fit_in_sample.csv`, `group_summary.csv` | Model fit and row / HCP / NBRx counts per group |
| `model_writers.txt` / `model_non_writers.txt` | Saved LightGBM models (load with `lgb.Booster(model_file=...)`); input column order in `model_<group>_feature_order.csv` |
| `feature_dictionary.csv` | Every feature with its source table, sub-category and fill rule |
| `run_info.json` | Run parameters (cohorts, sample list, model settings), row counts and run time |
| `category_data/`, `keys/` | The filled feature data set and HCP x cohort keys (Delta tables; read with `spark.read.format("delta").load(...)`) used by the models |

Each category notebook's job-run output (step 11 "Best features per group") shows only the top 50 (`TOP_N` widget) per group; use the CSVs above for the full lists.

## Caveats

* **Circularity in sales and comorb:** the writer flag is built from TOTAL_HCP_NBRX_CLAIMS_KERENDIA_IN_LAST_12_MONTH, which is itself a sales feature, so sales' discrimination for it is 1.0 by construction (its AUC rounding is clipped to [0,1]). Kerendia past-use features also dominate comorb's writer ranking.
* **Non-writer signal is thin:** 22,881 NBRx over 3.5M rows; many non-writer features carry the no-signal flag. Treat non-writer rankings as a first pass, not a final list.
* **In-sample everything:** the models are deliberately over-fitted to rank features; do not read the deviance explained or Spearman as performance.
* **Weights:** in this full-universe run every row has weight 1; the 10k sample-list runs use WEIGHT_GROUP.