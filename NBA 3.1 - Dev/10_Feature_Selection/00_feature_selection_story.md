# NBA 3.1 Feature Selection: the Story So Far

How we went from the NBA 3.0 way of choosing features (a 1,000-HCP sample and one model) to the NBA 3.1 way: two groups of HCPs, a weighted sample of 10,000 HCPs, and a statistical clean-up that hands a shorter list to model-based selection.

Status on 2026-11-25: the clean-up is done for both groups. The lists for model-based selection are ready.

---

## Where to find things

All paths below start at the volume root `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/`.

| What | Where |
| --- | --- |
| HCP list | `HCP_Universe_without_call_hcps` |
| Target table (Kerendia NBRx per HCP and month) | `notebook_output/target_variable/target_variable` |
| Writer rule source (NBRx features) | `hcp_level_model/dev_pipeline/notebook_output/hcp_features_v7_cohort_aligned/nbrx_features` |
| Sample list (10,000 HCPs, rows and weights) | `hcp_level_model/dev_pipeline/sample_lists/option_a_10k_hcps_10_months` |
| Combine notebook | `NBA 3.1 - Dev/99 Combine Physician Data Files/NBA_3_1_Combine_Physician_Data` |
| Combined table for the sample | `hcp_level_model/dev_pipeline/notebook_output/combined_2026_11_25/hcp_combined/_sample_option_a_10k_hcps_10_months/kerendia_nba_3_1_hcp_selected_features_data` |
| Clean-up notebook | `NBA 3.1 - Dev/10_Feature_Selection/02_nba_3_1_statistical_cleanup` |
| Clean-up outputs | `hcp_level_model/dev_pipeline/notebook_output/combined_2026_11_25/feature_selection/_sample_option_a_10k_hcps_10_months/statistical/` |
| **Lists for model-based selection** | clean-up outputs, `selected_features_writers.csv` and `selected_features_non_writers.csv` |
| First (1,000-HCP) run and its readiness file | `.../combined_2026_11_24/feature_selection/_test_sample_1000/poisson/` and `NBA 3.1 - Dev/10_Feature_Selection/01_nba_3_0_method_shap_1000_hcps_readiness.md` (notebook: `01_nba_3_0_method_shap_1000_hcps`) |

Files in the clean-up output folder:

| File | Content |
| --- | --- |
| `selected_features_writers.csv`, `selected_features_non_writers.csv` | Every feature kept after step 4, with its two flags and its link to NBRx |
| `feature_stats_writers.csv`, `feature_stats_non_writers.csv` | All 17,238 features with every number used, and the step that removed it |
| `near_copies_writers.csv`, `near_copies_non_writers.csv` | Each removed near-copy and the stronger feature it copies |
| `funnel.csv` | Features removed or flagged at each step |
| `category_summary.csv` | The same by feature category |
| `group_summary.csv` | Rows, HCPs and NBRx per group |
| `run_summary.json` | Thresholds, noise bars and counts of the run |

---

## Chapter 1. Where we started: the NBA 3.0 method

In NBA 3.0 we chose features the way the OE reference notebook did: take a sample of **1,000 HCPs**, train **one model** on all of them, and keep the features the model finds most useful (ranked by SHAP, which measures how much each feature moves the predictions).

For 3.1 we first ran exactly that method on the new feature tables, as a baseline (full details in `01_nba_3_0_method_shap_1000_hcps_readiness.md`):

* 1,000 HCPs, picked by a fixed hash of the HCP id, x 28 months.
* Training months c1-c24: 24,000 rows with **504 NBRx in 328 rows**. Test months c25-c26: 2,000 rows with 68 NBRx (source: `run_summary.json`, readiness file).
* 17,238 candidate features, 786 constant, 16,452 given to the model, 1,000 kept (source: `run_summary.json`).
* The model fit the training months almost perfectly (R2 0.979) but held up only partly on the test months (R2 0.377; it predicted 31.2 of 68 actual NBRx) (source: `train_test_metrics.csv`).

The top of the list made business sense, but the readiness file already noted that ranks 500-1,000 were close to chance: with so few NBRx, a feature at rank 800 could just as well be at 1,200.

## Chapter 2. What we learned from the 3.0 method

Before changing anything, we compared the SHAP list with simple statistics on the same 24,000 training rows (source: `model_data_parquet/` of the first run, recomputed 2026-11-25):

| Finding | Number | What it means |
| --- | --- | --- |
| SHAP top 1,000 vs the 1,000 features most correlated with NBRx (rank correlation) | 86 in common | The two methods pick almost entirely different features |
| SHAP-selected features whose correlation with NBRx is below the noise level for 1,000 HCPs (0.063) | 761 of 1,000 | Most selected features show no link on their own |
| Example: `PCT_TOTAL_RX_CLAIMS_METFORMIN_COMMERCIAL_IN_LAST_6_MONTH` | SHAP rank 6, correlation 0.049 | Important to the model, invisible to a simple test |

Two lessons came out of this:

1. **The sample was too small.** About 500 NBRx is not enough signal to rank 17,000 features reliably.
2. **Neither method is enough alone.** SHAP finds features that help in combination with others; simple statistics find features that help on their own. A good process uses both.

And from a call with the team, a third: **writers and non-writers behave differently**, so they should get separate models.

## Chapter 3. What changed in 3.1

| | NBA 3.0 method | NBA 3.1 method |
| --- | --- | --- |
| Models | One model for all HCPs | Two: existing writers and non-writers |
| Sample | 1,000 random HCPs, all 28 months | 10,000 HCPs chosen by group, 10 training months + 2 test months each, with weights |
| NBRx in the training rows | 504 | 12,468 (10,006 writers + 2,462 non-writers) |
| First filter | Constant features only | Six statistical steps, run per group |
| Final ranking | SHAP on one model | Model-based selection per group, on the cleaned list (next step) |

The chapters below tell how we got there.

## Chapter 4. Who is a writer?

**Rule:** an HCP is an **existing writer** in a month if they wrote at least one Kerendia NBRx in the 12 months of feature data before it (`TOTAL_HCP_NBRX_CLAIMS_KERENDIA_IN_LAST_12_MONTH` > 0, empty treated as 0; source: NBRx features table). Everyone else is a **non-writer**. A non-writer who writes in the prediction month is a new or returning writer, the most valuable case for NBA.

**Check:** we rebuilt the rule from the target table for c14-c28 on all HCPs: 4,420,890 rows, each with its full 12 months. The rule agrees on all but 2 rows, and the NBRx count on all but 8 (source: target table + NBRx features table, exact counts).

## Chapter 5. How big are the two groups?

All 294,726 HCPs x 28 months = 8,252,328 rows (source: HCP list x target table x NBRx features table, exact counts):

| Months | Group | Rows | NBRx | Rows with an NBRx |
| --- | --- | --- | --- | --- |
| Training c1-c24 | Writers | 540,355 | 152,580 | 92,395 |
| Training c1-c24 | Non-writers | 6,533,069 | 36,791 | 32,537 |
| Test c25-c26 | Writers | 56,817 | 15,375 | 9,482 |
| Test c25-c26 | Non-writers | 532,635 | 4,309 | 3,809 |
| Backtesting c27-c28 | Writers | 59,823 | 17,230 | 10,493 |
| Backtesting c27-c28 | Non-writers | 529,629 | 4,523 | 3,951 |

What this tells us, for the training months:

* **Writers are few but write most NBRx:** 7.6% of rows, 80.6% of NBRx.
* **Non-writers rarely start:** 0.5% of their rows have an NBRx, against 17.1% for writers.
* **The writer group is growing:** 19,051 writers in c1, 27,411 in c24, 30,352 in c28.
* **HCPs move between groups:** from one month to the next, a non-writer became a writer 34,904 times, and a writer dropped back 23,603 times.

## Chapter 6. Choosing the sample

A random sample would again be mostly HCPs who never write. So we split the HCPs into three groups by what they did in c1-c24 and picked more from the useful ones (source: HCP list x target table x NBRx features table; sample list):

| Group | Who | HCPs in total | Picked | Weight per HCP |
| --- | --- | --- | --- | --- |
| S1 | Wrote at least one NBRx in c1-c24 | 37,931 | 6,000 | 6.32 |
| S2 | Writer in some month, but no NBRx in c1-c24 | 6,666 | 1,000 | 6.67 |
| S3 | Never wrote and never a writer | 250,129 | 3,000 | 83.38 |
| **Total** | | **294,726** | **10,000** | |

**How can an HCP be a writer without any NBRx in c1-c24 (group S2)?** Each month (cohort) looks at two different time windows:

* The **writer flag looks back**: an NBRx in the 12-month lookback window before the month.
* **"NBRx in c1-c24" looks forward**: NBRx in the prediction months only, which run from July 2024 (c1) to June 2026 (c24).

The first lookback windows start before July 2024:

| Month | Lookback window (writer flag) | Prediction month (NBRx count) |
| --- | --- | --- |
| c1 | Jun 2023 - May 2024 | Jul 2024 |
| c2 | Jul 2023 - Jun 2024 | Aug 2024 |
| c13 | Jun 2024 - May 2025 | Jul 2025 |

(source: `cohorts/claims/cohorts.parquet`)

Example: an HCP writes one NBRx in March 2024 and never again. In c1 the lookback includes March 2024, so the HCP is a writer. The HCP stays a writer until March 2024 leaves the lookback (c1 to c10), but has 0 NBRx in every prediction month. So S2 are **lapsed writers**: they wrote before our first prediction month and then stopped.

The data agrees (source: target table x NBRx features table, all 6,666 S2 HCPs):

* All are writers already in c1 (6,079) or c2 (587): their NBRx fell between June 2023 and June 2024.
* None is a writer after c13, the last month whose lookback can still hold June 2024.
* The middle S2 HCP is a writer for 8 months; the longest is 13.

We keep S2 as its own group because it shows the "writer who stops writing" pattern, which the writer model needs. A random sample would hold only a few of them.

**Why 10 months per HCP instead of all 24.** Two months next to each other share 11 of their 12 months of feature data, so extra months of the same HCP add little. For the same number of rows, 10,000 HCPs x 10 months teaches more than about 4,200 HCPs x 24 months. The 10 months are picked at random with a fixed seed, and each HCP keeps both test months c25-c26.

**Weights.** Each sampled row stands for the rows we did not pick: the group weight times 2.4 for the 14 skipped training months. With weights, the sample adds up to the whole universe:

| Training rows | Sample rows | Sample NBRx | Weighted rows | Universe rows | Weighted NBRx | Universe NBRx |
| --- | --- | --- | --- | --- | --- | --- |
| Writers | 35,286 | 10,006 | 537,998 | 540,355 | 151,815 | 152,580 |
| Non-writers | 64,714 | 2,462 | 6,535,426 | 6,533,069 | 37,354 | 36,791 |

(source: sample list x target table, exact counts)

The sample has 120,000 rows: 100,000 training and 20,000 test. The same list comes back on every run, and it contains all 1,000 HCPs of the first run.

## Chapter 7. Combine on the sample

Combine joins the 44 feature tables into one row per HCP and month. It now accepts a sample list: it builds only the listed rows, carries the group and weight columns along, and skips the backtesting months c27-c28, which are not in the list. To save time, each feature table is cut down to the sampled HCPs before it is joined.

| | First run (1,000 HCPs) | Sample run (10,000 HCPs) |
| --- | --- | --- |
| Rows | 28,000 | 120,000 |
| Features | 17,238 | 17,238 |
| Feature tables cut down to the sampled HCPs before joining | No | Yes |
| Month groups built | 7 (c1-c28) | 6 (c1-c26) |
| Run time | 137 minutes (job run `196650153984570`) | 73 minutes (job run `233237647200069`) |

**Why is the 10,000-HCP run faster than the 1,000-HCP run?** Not because of the number of HCPs, but because the two runs worked differently:

1. **Cut down first, then join.** Every feature table holds all 295,000 HCPs. The first run joined the full tables and kept the 1,000 sampled HCPs only at the end, so it did the work for all HCPs. The sample run first cuts each table down to the sampled HCPs and only then joins, so it only does the work for the rows it keeps. This saved most of the time, around 8 minutes per month group.
2. **One month group less.** The backtesting months c27-c28 are not in the sample list, so the sample run skipped them (about 16 minutes).

The cut-down now also applies to the 1,000-HCP test option, so a new 1,000-HCP run would be faster too. It does not help a run on all HCPs, because there is nothing to cut; making that run faster is a separate next step.

Checks on the result (source: combined table for the sample):

* Exactly the 120,000 rows of the sample list, each once, with the same groups and weights.
* No empty values left in any feature.
* The writer flag agrees with `TOTAL_HCP_NBRX_CLAIMS_KERENDIA_IN_LAST_12_MONTH` on every row.
* For the 1,000 HCPs of the first run (12,000 shared rows), 300 randomly chosen features have identical values in both runs.

## Chapter 8. The statistical clean-up

The clean-up runs separately for writers and non-writers, on the training rows only, using the weights. It does not use any model.

### What it calculates

| Calculation | What it is | Used in |
| --- | --- | --- |
| Weighted share of the most common value | For each feature, the share of rows that hold its most frequent value | Steps 1-2 |
| Weighted fill share | Share of rows where the feature is not at its default fill value (0, -9999, 9999 or the median from Combine) | Step 3 |
| Rank correlation between features (Spearman) | How closely two features move together, on 20,000 training rows | Step 4 |
| Weighted rank correlation with NBRx (Spearman) | Whether NBRx goes up or down as the feature goes up. Computed from the weighted covariance of the ranks | Steps 5-6 |
| Correlation ratio with NBRx | The feature is cut into 10 groups by size and the average NBRx of each group is compared. Catches links that are not a straight line (for example, NBRx highest in the middle) | Steps 5-6 |
| Noise bar | NBRx is shuffled between HCPs (each HCP's months kept together) and both links are recomputed. The value that only 1% of features beat by chance is the bar a real link must clear | Step 5 |

No median is calculated in the clean-up. Medians appear only in Combine, as the fill value for 37 census and HCP-experience features. The clean-up only checks whether a feature sits at that fill value.

### The six steps

| Step | Rule | Why | Example features (writers) |
| --- | --- | --- | --- |
| 1. Constant | Same value in every row | Cannot tell HCPs apart | `ALDACTAZIDE_IN_LAST_1_MONTH` (same value in every row) |
| 2. Near-constant | One value in at least 99.5% of rows | Too rare to learn from | `ALDACTONE_IN_LAST_12_MONTH` (one value in 99.8% of rows) |
| 3. Low fill | Not at its default value in under 1% of rows | Almost always empty | `BRENZAVVY_IN_LAST_3_MONTH` (filled in 0.64%), `DIGITAL_PLC_EPOCRATES_DOCALERT_ENGAGEMENT_6M` (0.57%) |
| 4. Near-copy | Rank correlation of at least 0.95 with a stronger feature | Adds nothing new; the stronger copy stays | `ACS_PCT_UNINSURED_BELOW64_ZC` copies `ACS_PCT_UNINSURED_ZC` (0.99) |
| 5. No signal | Both links to NBRx below the noise bar | No link on its own | flag only |
| 6. Unstable | The link to NBRx is not repeated in both halves of the HCPs | Link may be chance | flag only |

**Decision: steps 5 and 6 only flag, they do not remove.** Chapter 2 showed that features can matter in combination while showing no link alone. If steps 5 and 6 removed features, 611 of the first run's SHAP top 1,000 would be lost for writers, among them `MIN_EVENT_TIME_EGFR_TEST_ALL_LOINC_VARIANTS_TIME_MIN` (SHAP rank 8). So the cut is made after step 4, and the flags go with the list as information for the next step.

Noise bars (source: `run_summary.json`): writers 0.136 (rank correlation) and 0.119 (correlation ratio); non-writers 0.051 and 0.045. The non-writer bar is lower because the group has more rows.

### What came out

(source: `funnel.csv`)

| Step | Writers | Non-writers |
| --- | --- | --- |
| Start | 17,238 | 17,238 |
| 1. Constant | -475 | -512 |
| 2. Near-constant | -1,618 | -2,704 |
| 3. Low fill | -765 | -986 |
| 4. Near-copy | -5,168 | -4,633 |
| **Kept: the list for model-based selection** | **9,212** | **8,403** |
| of which flagged 5, no signal | 7,683 | 8,129 |
| of which flagged 6, unstable | 108 | 55 |
| of which no flag | 1,421 | 219 |

10,824 features are kept in at least one group, and 6,791 in both.

**By category** (source: `category_summary.csv`):

| Category | Features | Kept, writers | No flag, writers | Kept, non-writers | No flag, non-writers |
| --- | --- | --- | --- | --- | --- |
| Claims | 8,458 | 3,929 | 933 | 3,740 | 132 |
| Patient events | 4,687 | 3,135 | 135 | 2,743 | 7 |
| Rx market | 3,300 | 1,738 | 299 | 1,609 | 28 |
| Promotional, non-personal | 520 | 232 | 1 | 163 | 27 |
| Promotional, personal | 128 | 59 | 18 | 35 | 17 |
| Static HCP | 142 | 116 | 35 | 110 | 8 |
| Added by Combine (calendar) | 3 | 3 | 0 | 3 | 0 |
| **Total** | **17,238** | **9,212** | **1,421** | **8,403** | **219** |

**Strongest features without a flag** (source: `selected_features_*.csv`):

| Writers | Link | Non-writers | Link |
| --- | --- | --- | --- |
| `TOTAL_PATIENTS_START_KERENDIA_IN_LAST_6_MONTH` | 0.376 | `FLD_INT_KER_PRIMARY_3M` | 0.091 |
| `KERENDIA_NBRX_IN_LAST_12_MONTH` | 0.402 | `FLD_INT_TOTAL_6M` | 0.091 |
| `KERENDIA_NBRX_IN_LAST_3_MONTH` | 0.359 | `TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_6_MONTH` | 0.097 |
| `TOTAL_HCP_NBRX_CLAIMS_KERENDIA_IN_LAST_12_MONTH` | 0.401 | `FLD_INT_TOTAL_12M` | 0.087 |
| `TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_1_MONTH` | 0.381 | `RUNNING_TOTAL_PATIENTS_START_KERENDIA` | 0.090 |

(Link = weighted rank correlation with NBRx on the training months.)

The two groups tell different stories. For writers, their own Kerendia history leads. For non-writers, field interactions with reps (`FLD_INT_...`) come first, and all links are weaker: the group has 2,156 training rows with an NBRx, against 6,097 for writers.

**Do the links hold on later months?** Among features without a flag, the link points the same way on the test months c25-c26 for 1,418 of 1,421 writer features and 217 of 219 non-writer features.

**What happened to the first run's SHAP top 1,000** (source: `feature_stats_*.csv` and `final_selected_top_1000_features_by_shap.csv`):

| | Writers | Non-writers |
| --- | --- | --- |
| Kept, no flag | 123 | 31 |
| Kept, flagged no signal | 611 | 700 |
| Kept, flagged unstable | 8 | 5 |
| Removed as near-copy | 258 | 252 |
| Removed in steps 1-3 | 0 | 12 |

A removed near-copy is not a loss: its stronger twin stays. For example, `RUNNING_TOTAL_RX_CLAIMS_KERENDIA` (SHAP rank 1) is represented by `TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_12_MONTH` (correlation 0.96), and `KERENDIA_TRX_APPROVED_IN_LAST_3_MONTH` (rank 7) by `TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_3_MONTH` (0.98).

**Checks** (built into the notebook, all passed in job run `702321318330434`, 19 minutes):

* The counts of every step add up to the total.
* Every kept feature follows steps 1-4, and no two kept features are near-copies (largest correlation between two kept features: 0.950, just under the cut).
* The fill share of sample features matches a separate calculation in Spark.
* `TOTAL_HCP_NBRX_CLAIMS_KERENDIA_IN_LAST_12_MONTH` is constant among non-writers, as the writer rule requires.

---

## Next step: model-based selection (India team)

The clean-up removed what is certainly useless or duplicated. What is left (9,212 writer and 8,403 non-writer features) is small enough for methods that train models, which can see features that only help in combination. These methods fit, for each group:

| Method | How it works | What we gain |
| --- | --- | --- |
| **Boruta** | Each feature gets a shuffled copy (a "shadow"). A model is trained many times; a feature is kept only if it beats the best shadow more often than chance | A clear keep / drop answer per feature, with no need to pick a cut-off like "top 1,000" |
| **Repeated SHAP (stability selection)** | Train the model many times on different halves of the HCPs and different seeds, and count how often each feature lands in the top N | Solves the 3.0 problem of ranks 500-1,000 being close to chance: we keep features that are important again and again |
| **Permutation importance on the test months** | Shuffle one feature at a time in c25-c26 and measure how much the prediction gets worse | Measures usefulness on months the model has not seen, so features that only help memorise the training months drop out |
| **Step-down elimination** | Train, drop the weakest 10-20% of features, retrain, and repeat while test accuracy holds | Finds the smallest list that predicts as well as the full one, which makes the final model simpler and faster |
| **Group importance** | Measure importance for families of features (for example, all SGLT2 claim features or all field features) instead of one by one | Easier business review, and it shows which data sources really matter, which helps decide which feature tables to keep building |

Whatever method is chosen, some rules keep it consistent with this work:

* Run each group separately, using the lists in `selected_features_writers.csv` and `selected_features_non_writers.csv`.
* Use the `WEIGHT` column, so results represent all HCPs and not just the sample.
* Train on c1-c24, check on c25-c26, and never put the same HCP on both sides when splitting the training months.
* Keep the flags visible: a flagged feature that the model keeps is worth a business check before it goes into the final list.

## Open points

**1. Owner and method for model-based selection**

* *Background:* the India team will run the next step. The method is not chosen yet.
* *Options:* Boruta, repeated SHAP, or both (they answer different questions: "is it better than noise" and "is it reliably important").
* *Effect:* repeated SHAP is closest to the 3.0 method and easiest to compare; Boruta gives a cut-off without guessing a list size.

**2. Few NBRx for non-writers in the test months**

* *Background:* the non-writer test months have 184 rows with an NBRx (source: sample list x target table). That is enough to check the direction of links, but thin for judging a model on its own.
* *Options:* (a) keep the sample; (b) add more non-writer HCPs (S3) to the sample, which needs a new Combine run (73 minutes for the current sample).
* *Effect:* (b) makes non-writer test results more stable, at the cost of more rows.

**3. New notebooks not yet saved to GitHub**

* *Background:* the clean-up notebook and this file are in the `_pg` working folder only.
* *Effect:* until they are committed, the team cannot see them on the `combine` branch.
