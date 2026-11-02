# NBA 3.0 Kerendia Prior Writing Features: How They Are Built

Notebook reviewed: `/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/10_kerendia_prior_writing`. NBA 3.1 changes are not part of this file.

## 1. How NBA 3.0 builds the Kerendia prior writing features

### 1.0 What is this section about?

The NBA (Next Best Action) model scores every HCP who could prescribe Kerendia and recommends the next promotional action. The target is the HCP's Kerendia NBRx in a 30-day prediction window. **Kerendia prior writing features** describe the HCP's recent Kerendia new-to-brand writing: how many NBRx the HCP wrote in each of the last 1 to 6 calendar months.

This section explains how the **NBA 3.0 Ops pipeline** builds these features, so a reader can follow the logic without reading the code. Section 1.1 covers the shared foundations. Section 1.2 covers the single feature type in three parts: (a) data sources and what each column means, (b) preprocessing steps, (c) features created. 1.3 and 1.4 cover the output table and caveats. 1.5 to 1.7 cover the data used, the model importance and the column volume. 1.8 lists every prior writing feature in the final 752-feature NBA 3.0 model. Numbers come from the latest ops run (pull date 2026-10-26, lookback 2025-09-30 to 2026-09-30, cohort `I01`, scoring month `SVC_DT_M = 2026-09-01`).

**In short**: the notebook reads weekly LAAD-based Kerendia NBRx by prescriber, rolls it up to calendar months, fills in missing months with 0, and sums the last 1 to 6 months. **Important finding (1.4, item 1): these Kerendia NBRx features are redundant with the Kerendia NBRx features that `26_Features_NBRx` already builds from the same LRx table.** For the 1, 3 and 6-month windows the values are identical for every universe HCP.

| Feature type | Business question | Section |
| --- | --- | --- |
| Kerendia NBRx in the last N months | How many new Kerendia patients did the HCP start recently? | 1.2 |

### 1.1 Shared foundations

**Who is scored and on which date**

| Item | What it means | Last run |
| --- | --- | --- |
| HCP universe | `ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`. **Not applied in this notebook.** The universe is only applied later by the left join in `99_Combine_Physician_Data` | 234,405 HCPs |
| Cohort | One scoring date per run, labelled `I01` | `I01` |
| Join key | `PROVIDER_ID` + `SVC_DT_M`. The combine step joins on `SVC_DT_M = trunc(LOOKBACK_END_DATE, 'MM')` | `SVC_DT_M = 2026-09-01` |

**Cohort dates** (from `00_config`)

| Date | Rule | Last run |
| --- | --- | --- |
| Lookback start (`lookback_start_date`) | Lookback end - 365 days. Used as the lower date filter of the query | 2025-09-30 |
| Lookback end | Last day of the month two months before the anchor month | 2026-09-30 |
| Scoring month | First day of the lookback-end month | 2026-09-01 |
| Prediction window | 7th of the anchor month + 30 days | 2026-11-07 to 2026-12-07 |

**Source table** (Unity Catalog, queried directly with Spark SQL, no Snowflake pull)

| Source | Table | One row is | Used columns |
| --- | --- | --- | --- |
| LAAD-based LRx | `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_laad_based_lrx.KERENDIA_LAAD_BASED_LRX_V6` | One prescriber x period x product group x segment (specialty, payer, channel, indication, ...) | `PROVIDER_ID`, `PERIOD_ID`, `NBRX` |

**Columns used**

| Column | What it means | Example |
| --- | --- | --- |
| `PROVIDER_ID` | LAAD ID of the prescriber | 11735757 |
| `PERIOD_ID` | End date of the period. `PERIOD_TYPE = 'W'` rows are full weeks ending on a Friday. `PERIOD_TYPE = 'X'` rows are the two halves of a week that crosses a month end, dated on the month end and on the Friday. So every period falls in one calendar month and monthly sums do not double count | September 2026: 2026-09-04 (X), 09-11, 09-18, 09-25 (W), 09-30 (X) |
| `NBRX` | New-to-brand prescriptions. Integer (no projection factor in V6) | 3 |
| `PRODUCT_GROUP` | Product group. The features cover `KERENDIA` | KERENDIA |

Table coverage at review: `PERIOD_ID` 2023-01-06 to 2026-10-02 (234 periods).

---

### 1.2 NBRx in the last N months

**a. Data sources**

`KERENDIA_LAAD_BASED_LRX_V6`, rows with `PERIOD_ID >= lookback_start_date` (2025-09-30) and `PROVIDER_ID` not null. No upper date filter, so the October 2026 periods (up to 2026-10-02) are also read.

**b. Preprocessing steps**

1. **Aggregate.** *What:* `SUM(NBRX)` of Kerendia per `PROVIDER_ID` and `PERIOD_ID`, across every segment (specialty, payer, channel, indication, ...). The result is named `KERENDIA_NBRX`.
2. **Month bucket.** *What:* `SVC_DT_M` = first day of the `PERIOD_ID` month, then sum per HCP and month.
3. **Full calendar.** *What:* build every month from 2021-01-01 to the latest month in the data (2026-10) and cross-join it with every HCP in the data. Left-join the monthly sums and **fill empty months with 0**. *Detail to know:* months before the lookback start are always 0 because the query does not read them, so the 2021-2025 part of the calendar only adds rows.
4. **Rolling sums** (`step3_lag` in `00_step23_function`). *What:* `SUM` over `rowsBetween(-i+1, 0)` for i = 1 to 6. *Detail to know:* unlike `step3_lag_avg` used by the comorbidity notebook, this window covers exactly **i months**, ending with the current month.
5. **Drop helpers.** The monthly value `KERENDIA_NBRX` and the running total `RUNNING_KERENDIA_NBRX` are dropped. Remaining nulls are filled with 0.

**c. Features created**

| Feature | Business meaning | Example (scoring month, universe HCPs) |
| --- | --- | --- |
| `KERENDIA_NBRX_IN_LAST_{N}_MONTH`, N = 1 to 6 | Kerendia NBRx written by the HCP in the last N calendar months, ending with the lookback-end month | `KERENDIA_NBRX_IN_LAST_1_MONTH` > 0 for 7,113 HCPs, median 1 (among writers), max 24. `KERENDIA_NBRX_IN_LAST_6_MONTH` > 0 for 22,088 HCPs, median 1, max 139 |

*Example:* HCP 11735757 wrote 24 Kerendia NBRx in September 2026, the largest 1-month value in the universe. Across all HCPs in the LRx table, September 2026 has 10,523 Kerendia NBRx from 7,113 HCPs.

* `LAST_1_MONTH` = 1 to 30 September 2026 (calendar month, not the last 30 days).
* The scoring month does not include October data, so there is no leakage from the October periods into the features used at inference.

---

### 1.3 What the final table looks like

| Output | Rows | Columns | Contains |
| --- | --- | --- | --- |
| `ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_kerendia_prior_writing_for_inference` | One row per HCP x month, 2021-01 to 2026-10 | 9 (6 features + `PROVIDER_ID`, `SVC_DT_M`, `PULL_DT`) | 1.2 |

Universe HCPs without a row in this table get empty values, not 0, after the left join in the combine step.

### 1.4 Things to watch out for

1. **Redundant with `26_Features_NBRx` (critical).** `26_Features_NBRx` reads the same LRx table, pivots `PRODUCT_GROUP` and builds `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_{1,3,6,12}_MONTH` and `RUNNING_TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA`. For the scoring month (September 2026), the Kerendia NBRx over the last 1, 3 and 6 months matches the `26_Features_NBRx` columns for all 234,403 universe HCPs in that table (0 differences, correlation 1.00). The 2, 4 and 5-month windows only add adjacent windows of the same count. So this notebook adds no new Kerendia information.
2. **Not limited to the HCP universe.** Every HCP in the LRx table is written for all 70 months, when only one month for the 234K universe HCPs is used.
3. **Calendar starts in 2021, data starts in the lookback.** Months before 2025-09 are always 0. For training cohorts built the same way, any window that reaches back before that cohort's own lookback start would be 0. With a 6-month maximum window this is not a problem today.
4. **No upper date filter.** The query reads periods after the lookback end (to 2026-10-02). They only affect the October row, which is not used at inference, but the notebook relies on the combine step to pick the right month.
5. **Other prior writing features.** Besides `26_Features_NBRx` (item 1), the "Prior Writing" sub-category in the Excel (145 features, 25.0% of SHAP) comes from other notebooks. The strongest Kerendia writing signals in the model are from those notebooks, not from this one.
6. **Missing vs 0.** Inside this table empty months are 0. HCPs not in the table become empty after the combine join.

### 1.5 Data used and terms

**Data used**

| Source | Path | Notes |
| --- | --- | --- |
| Input | `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_laad_based_lrx.KERENDIA_LAAD_BASED_LRX_V6` | Read at review (2026-10-29) |
| Output | `.../hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_kerendia_prior_writing_for_inference` | `PULL_DT = 2026_10_26` |
| HCP universe | `.../ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` | 234,405 HCPs |
| Final 752 feature list | `/Users/sehar.aejaz.ext@bayer.com/Extra Notebooks/Final NBA 3.0 Modeling Features.xlsx` | Used for 1.6 and 1.8 |
| Helper functions | `00_Helper_Notebooks/00_step23_function` | `step3_lag` |

**Terms used in this document**

| Term | Meaning |
| --- | --- |
| NBRx | New-to-brand prescription: a patient's first Rx for the product (new or switched) |
| LRx | IQVIA longitudinal prescription data, here derived from LAAD and grouped by prescriber, period and product group |
| `PERIOD_TYPE` W / X | W = full week ending Friday. X = part of a week split at a month end |
| SHAP share | A feature's mean absolute SHAP value divided by the sum over all 752 features |

### 1.6 Importance in the NBA 3.0 model (share of total mean absolute SHAP)

5 of the 6 features are among the final 752 (only `KERENDIA_NBRX_IN_LAST_3_MONTH` was dropped). Together they hold **0.43%** of total SHAP. The Excel files them under "Claim-based features / Rx Claim-based".

| Family | Features created | Features kept | SHAP share |
| --- | --- | --- | --- |
| NBRx in the last N months (1.2) | 6 | 5 | 0.43% |

### 1.7 Column volume

| Family | Windows | Total |
| --- | --- | --- |
| NBRx in the last N months | 1, 2, 3, 4, 5, 6 months | 6 |

---

### 1.8 Prior writing features used in the final NBA 3.0 model

Source: `Final NBA 3.0 Modeling Features.xlsx`. SHAP rank is 1-752 by mean absolute SHAP.

| SHAP rank | Feature | Window | SHAP share |
| --- | --- | --- | --- |
| 173 | `KERENDIA_NBRX_IN_LAST_2_MONTH` | Aug to Sep 2026 | 0.15% |
| 225 | `KERENDIA_NBRX_IN_LAST_1_MONTH` | Sep 2026 | 0.12% |
| 248 | `KERENDIA_NBRX_IN_LAST_4_MONTH` | Jun to Sep 2026 | 0.10% |
| 492 | `KERENDIA_NBRX_IN_LAST_6_MONTH` | Apr to Sep 2026 | 0.04% |
| 652 | `KERENDIA_NBRX_IN_LAST_5_MONTH` | May to Sep 2026 | 0.02% |
