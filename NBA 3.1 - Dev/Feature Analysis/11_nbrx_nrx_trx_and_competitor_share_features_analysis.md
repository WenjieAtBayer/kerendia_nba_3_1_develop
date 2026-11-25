# NBA 3.0 Kerendia NBRx / NRx / TRx and Competitor Drug NBRx Share Features: How They Are Built

Notebooks reviewed (NBA 3.0 Ops pipeline, `03_HCP_Level_Features` folder):

* `26_Features_NBRx` — NBRx (new-to-brand) features pivoted across 11 dimensions
* `27_Features_NRx` — NRx (new prescription) features, same pipeline with NRx metric
* `28_Features_TRx` — TRx (total prescription) features, same pipeline with TRx metric
* `31_Competitor_drugs_NBRX_share` — NBRx share percentages for 4 SGLT2i competitor drugs

NBA 3.1 changes are not part of this file.

---

## 1. How NBA 3.0 builds the NBRx, NRx and TRx features

### 1.0 What is this section about?

The NBA (Next Best Action) model scores every HCP who could prescribe Kerendia and recommends the next promotional action. The target is the HCP's Kerendia NBRx in a 30-day prediction window. **NBRx / NRx / TRx features** describe the HCP's recent prescription volume across every product, demographic and clinical segment available in the LAAD-based LRx data — not just Kerendia.

This section covers the **three near-identical notebooks** (26, 27, 28) that share an 8-step pipeline and differ only in which metric column they aggregate. Section 1.1 covers the shared foundations. Section 1.2 covers the pipeline steps: (a) data sources, (b) preprocessing, (c) features created. 1.3 covers the parameterization table (what changes between the three notebooks). 1.4 and 1.5 cover the output tables and caveats. 1.6 covers data sources and terms.

**In short**: each notebook reads weekly LAAD-based LRx data for every product, rolls it up to calendar months, pivots it across 11 dimensions (product group, specialty, switch-from, add-on-to, age, gender, payer, source of business, channel, indication, hypertension), fills in missing months with the `step2_fill_missing` helper, computes 1/3/6/12-month rolling sums and running totals with the `step3_lag` helper, and saves ~1,337 columns per HCP-month to a Delta table.

| Notebook | Feature type | Business question | Section |
| --- | --- | --- | --- |
| 26 | NBRx across 11 dimensions | How many new-to-brand prescriptions did the HCP write, by product and segment? | 1.2 |
| 27 | NRx across 11 dimensions | How many new prescriptions (incl. restarts, switches) did the HCP write? | 1.2 |
| 28 | TRx across 11 dimensions | What is the HCP's total prescription volume (incl. refills)? | 1.2 |

### 1.1 Shared foundations

**Who is scored and on which date**

| Item | What it means | Last run (26) | Last run (27/28) |
| --- | --- | --- | --- |
| HCP universe | `ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`. Inner-joined in this notebook, not applied later | 222,125 HCPs | 223,454 HCPs |
| Cohort | One scoring date per run, labelled `I01` | `I01` | `I01` |
| Join key | `PROVIDER_ID` + `SVC_DT_M` | — | — |

The HCP universe size differs between runs because the three notebooks were last executed on different dates (26 on 2025-11-27, 27 and 28 on 2025-10-24). The code is identical; the universe Delta table was refreshed between runs.

**Cohort dates** (from `hcp_model_inference_anchor_dates.csv`, filtered to `COHORT = 'I01'`)

| Date | Rule | Last run (26) | Last run (27/28) |
| --- | --- | --- | --- |
| Lookback start (`LOOKBACK_START_DATE`) | Lookback end - 365 days | 2024-10-31 | 2024-06-30 |
| Lookback end | Last day of the month two months before the anchor month | 2025-10-31 | 2025-06-30 |
| Scoring month | First day of the lookback-end month | 2025-12-01 | 2025-08-01 |

The lookback dates are read from the anchor CSV but are **not used as SQL filters** in these notebooks. The queries split at a fixed `WEEK_ENDING_DATE = '20230101'` boundary (see 1.2a). The lookback dates are used downstream by the combine step (`99_Combine_Physician_Data`).

**Source tables** (Unity Catalog, queried directly with Spark SQL, no Snowflake pull)

| Source | Table | Date filter | Rows (last run) |
| --- | --- | --- | --- |
| Historical LAAD LRx (pre-2023) | `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_laad_based_lrx.KERENDIA_LAAD_BASED_LRX_FULL_DATA_STARTING_2021` | `WEEK_ENDING_DATE < '20230101'` | 856,066,347 |
| Current LAAD LRx (2023+) | `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_laad_based_lrx.KERENDIA_LAAD_BASED_LRX_V6` | `WEEK_ENDING_DATE >= '20230101'` | 2,405,461,871 (26) / 2,321,470,810 (27/28) |

Both tables share the same 21-column schema. The notebooks union them after loading.

**Columns used** (identical across all three notebooks)

| Column | What it means | Example |
| --- | --- | --- |
| `PROVIDER_ID` | LAAD ID of the prescriber (key column) | 11735757 |
| `PERIOD_ID` | End date of the period. `PERIOD_TYPE = 'W'` rows are full weeks ending on a Friday. `PERIOD_TYPE = 'X'` rows are the two halves of a week that crosses a month end, dated on the month end and on the Friday | September 2026: 2026-09-04 (X), 09-11, 09-18, 09-25 (W), 09-30 (X) |
| `PRODUCT_GROUP` | Product group (74 groups + null). Covers Kerendia, SGLT2i, GLP-1, RAAS, MRA, diuretics, insulin, etc. | KERENDIA |
| `SPECIALTY_GROUP` | Prescriber specialty group (6 + null) | NEPHROLOGY |
| `SWITCH_FROM` | Product the patient switched from (~74 + null) | OZEMPIC |
| `ADD_ON_TO` | Product added on to (~74 + null) | FARXIGA BRAND |
| `AGE_GROUP` | Patient age group (8 values) | 65+ |
| `GENDER` | Patient gender (3 values) | M |
| `PAY_TYPE` | Payer type (5 values) | MEDICARE PART D |
| `SOURCE_OF_BUSINESS` | Source of business classification (6 values) | Immediate Continue |
| `RX_CHANNEL` | Rx channel (4 + null) | R |
| `INDICATION_GROUP` | Indication group (16 values). `'ALL OTHERS'` is relabelled to `'ALL_OTHERS'` | T2D + CKD + CVD |
| `HYPERTENSION_FLAG` | Hypertension flag (1 + null) | HTN |
| `NBRX` | New-to-brand prescriptions. Integer count | 3 |
| `NRX` | New prescriptions (incl. restarts, switches). Integer count | 1 |
| `TRX` | Total prescriptions (incl. refills). Integer count | 5 |
| `NPI` | National Provider Identifier | 1972662260 |
| `PRI_SPCL_DESC` | Primary specialty description | NEPHROLOGY |

**Helper notebooks** (run via `%run` at the top of each notebook)

| Helper | Provides |
| --- | --- |
| `00_connection` | Spark session, imports (`F`, `col`, `when`, `date_format`, `trunc`, `concat`, `substring`, `dt`, `gc`), table path constants |
| `00_config` | Cohort anchor date loading. **Only 26 runs this; 27 and 28 load anchor dates inline instead** |
| `00_step23_function` | `step2_fill_missing` (continuous monthly calendar) and `step3_lag` (rolling-window sums and running totals) |

---

### 1.2 The shared 8-step pipeline

**a. Data sources**

The notebooks read from two LAAD-based LRx tables split by a fixed date boundary:

1. **Old table** (`KERENDIA_LAAD_BASED_LRX_FULL_DATA_STARTING_2021`): all data with `WEEK_ENDING_DATE < '20230101'`. The `PERIOD_ID` column is already a string in `yyyyMMdd` format in this table.
2. **New table** (`KERENDIA_LAAD_BASED_LRX_V6`): all data with `WEEK_ENDING_DATE >= '20230101'`. The `PERIOD_ID` column is a date type and is converted to `yyyyMMdd` string format with `date_format("PERIOD_ID", "yyyyMMdd")`.
3. **Union**: the two DataFrames are concatenated. Notebook 26 uses `unionByName`; notebooks 27 and 28 use `union`. Both work because the column order is identical (same `SELECT DISTINCT` statement).

No lookback date filter is applied at the SQL level. The full historical range is read.

**b. Preprocessing steps**

1. **Filter to HCP universe.** *What:* inner-join the unioned LRx data to `kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` on `PROVIDER_ID`. *Result:* ~2.55 billion rows (26) / ~2.50 billion rows (27/28), ~222K / ~223K distinct providers.

2. **Normalise INDICATION_GROUP.** *What:* replace `'ALL OTHERS'` with `'ALL_OTHERS'` (underscored) for consistent pivot column names.

3. **Monthly truncation.** *What:* convert `PERIOD_ID` (string `yyyyMMdd`) to a date (`YEAR_MONTH_DAY`), then truncate to month (`SVC_DT_M`). Since every `PERIOD_ID` falls in one calendar month, weekly periods do not double-count when summed to monthly.

4. **Pivot and aggregate across 11 dimensions.** *What:* for each of 11 columns (see table below), replace null/`'NULL'` with a placeholder, group by `[PROVIDER_ID, SVC_DT_M]`, pivot on the dimension column, and `SUM` the metric column (`NBRX`, `NRX` or `TRX`). Clean each pivoted column name by replacing special characters (`+` → `and`, `/` → ` or `, `-` → `_`, spaces → `_`, removing `()` and `&`) and uppercasing.

5. **Join into spine.** *What:* left-join all 11 dimension DataFrames on `[PROVIDER_ID, SVC_DT_M]`. Product Group is the left anchor; all other dimensions are left-joined to it.

6. **Fill missing months** (`step2_fill_missing`). *What:* generate a continuous monthly calendar from the global min to global max `SVC_DT_M`, cross-join with every distinct `PROVIDER_ID`, and left-join the spine back. Missing provider-months get null feature values (not 0). *Detail to know:* the calendar uses global min/max, not per-provider min/max, so every provider gets the same full date range.

7. **Create lag features** (`step3_lag`). *What:* for every feature column, compute `SUM` over `rowsBetween(-i+1, 0)` for i = 1, 3, 6, 12 (named `..._IN_LAST_{N}_MONTH`) and a cumulative running total `RUNNING_...` over `rowsBetween(unboundedPreceding, currentRow)`. The window is partitioned by `PROVIDER_ID` and ordered by `SVC_DT_M`. *Detail to know:* the window includes the current month, so `_IN_LAST_1_MONTH` equals the base monthly value.

8. **Drop base columns, filter, add metadata and save.** *What:* drop all original (non-lagged) columns, keeping only `PROVIDER_ID`, `SVC_DT_M`, the lag columns and running totals. Filter `PROVIDER_ID` not null and `SVC_DT_M >= '2023-01-01'`. Rename `NPI` to `NPI_NUMBER`. Add `PULL_DT` (current date as `YYYY_MM_DD` string). Write to Delta with `overwrite` mode and `overwriteSchema=true`.

**The 11 pivot dimensions**

| # | Dimension | Pivot column | Null replacement | Column prefix |
| --- | --- | --- | --- | --- |
| 1 | Product Group | `PRODUCT_GROUP` | `UNKNOWN_PG` | `TOTAL_HCP_{METRIC}_CLAIMS_PRODUCT_GROUP_` |
| 2 | Specialty Group | `SPECIALTY_GROUP` | `UNKNOWN` | `TOTAL_HCP_{METRIC}_CLAIMS_SPEC_` |
| 3 | Switch From | `SWITCH_FROM` | `UNKNOWN` | `TOTAL_HCP_{METRIC}_CLAIMS_SWITCH_FROM_` |
| 4 | Add On To | `ADD_ON_TO` | `UNKNOWN` | `TOTAL_HCP_{METRIC}_CLAIMS_ADD_ON_TO_` |
| 5 | Age Group | `AGE_GROUP` | *(no replacement)* | `TOTAL_HCP_{METRIC}_CLAIMS_AGE_GROUP_` (26) / `TOTAL_HCP_{METRIC}_CLAIMS_AGE_` (27/28) |
| 6 | Pay Type | `PAY_TYPE` | *(no replacement)* | `TOTAL_HCP_{METRIC}_CLAIMS_PAY_TYPE_` |
| 7 | Source of Business | `SOURCE_OF_BUSINESS` | *(no replacement)* | `TOTAL_HCP_{METRIC}_CLAIMS_SOB_` |
| 8 | Rx Channel | `RX_CHANNEL` | *(no replacement)* | `TOTAL_HCP_{METRIC}_CLAIMS_CHANNEL_` |
| 9 | Indication Group | `INDICATION_GROUP` | *(no replacement)* | `TOTAL_HCP_{METRIC}_CLAIMS_INDICATION_GROUP_` |
| 10 | Hypertension Flag | `HYPERTENSION_FLAG` | `UNKNOWN_HF` (26) / `UNKNOWN_HP` (27/28) | `TOTAL_HCP_{METRIC}_CLAIMS_HYPERTENSION_` |
| 11 | Gender | `GENDER` | `UNKNOWN` | `TOTAL_HCP_{METRIC}_CLAIMS_GENDER_` |

`{METRIC}` is `NBRX`, `NRX` or `TRX` depending on the notebook.

**c. Features created**

Each notebook produces a wide table with one row per `PROVIDER_ID` x `SVC_DT_M`. The number of feature columns depends on the cardinality of each pivot dimension. With 11 dimensions and 4 lag windows (1, 3, 6, 12 months) plus running totals, the output has ~1,337 columns.

Feature naming pattern: `TOTAL_HCP_{METRIC}_CLAIMS_{DIMENSION}_{VALUE}_IN_LAST_{N}_MONTH` and `RUNNING_TOTAL_HCP_{METRIC}_CLAIMS_{DIMENSION}_{VALUE}`.

*Example:* `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_3_MONTH` = Kerendia new-to-brand prescriptions by the HCP in the last 3 calendar months.

---

### 1.3 What changes between NBRx, NRx and TRx

| Parameter | NBRx (Notebook 26) | NRx (Notebook 27) | TRx (Notebook 28) |
| --- | --- | --- | --- |
| Metric column aggregated | `NBRX` | `NRX` | `TRX` |
| Aggregation alias | `SUM_NBRX` | `SUM_NRX` | `SUM_TRX` |
| Column prefix | `TOTAL_HCP_NBRX_CLAIMS_` | `TOTAL_HCP_NRX_CLAIMS_` | `TOTAL_HCP_TRX_CLAIMS_` |
| Age group prefix | `..._AGE_GROUP_` | `..._AGE_` | `..._AGE_` |
| Hypertension null replacement | `UNKNOWN_HF` | `UNKNOWN_HP` | `UNKNOWN_HP` |
| `.na.fill(0)` after pivot | **Commented out** (nulls preserved) | **Commented out** (nulls preserved) | **Active** (nulls → 0) |
| Union method | `unionByName` | `union` | `union` |
| Runs `00_config` helper | Yes | No (inline) | No (inline) |
| Output variable | `df_nbrx_feats` | `df_nrx_feats` | `df_trx_feats` |
| Output Delta path suffix | `nbrx_features_w_provider_id_for_inference` | `nrx_features_w_provider_id_for_inference` | `trx_features_w_provider_id_for_inference` |

**Key differences explained:**

* **Metric semantics**: NBRx (new-to-brand, strict 12-month product-specific lookback) ⊆ NRx (new prescription, includes restarts and switches) ⊆ TRx (total, includes refills). Every NBRx is an NRx and every NRx is a TRx, but not vice versa.
* **Age group prefix inconsistency**: notebook 26 uses `AGE_GROUP_` while 27 and 28 use `AGE_`. This is naming drift; if unified, downstream column references will need updating.
* **Hypertension null replacement**: notebook 26 uses `UNKNOWN_HF` (likely a copy-paste error borrowing the Heart Failure abbreviation), while 27/28 use `UNKNOWN_HP` (Hypertension — more accurate). The null-replacement logic is identical; only the string literal differs.
* **`.na.fill(0)` behavior**: TRx fills pivot nulls with 0 after each pivot ("no claims = 0"), while NBRx and NRx leave nulls ("no claims = unknown/absent"). In `step3_lag`, `SUM().over(Window)` treats null as skip (does not contribute) and 0 as zero. So TRx lag features can never be null for a provider-month in the spine, while NBRx/NRx lag features can be null if all months in the window had null base values.

---

### 1.4 What the final tables look like

| Notebook | Output Delta path | Rows | Columns | Contains |
| --- | --- | --- | --- | --- |
| 26 | `.../ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_nbrx_features_w_provider_id_for_inference` | 7,373,883 | 1,337 | Lag + running-total NBRx features across 11 dimensions |
| 27 | `.../ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_nrx_features_w_provider_id_for_inference` | 7,373,883 | 1,337 | Lag + running-total NRx features across 11 dimensions |
| 28 | `.../ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_trx_features_w_provider_id_for_inference` | 7,373,883 | 1,337 | Lag + running-total TRx features across 11 dimensions |

All output paths are under `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/`.

Each table is one row per `PROVIDER_ID` x `SVC_DT_M` from 2023-01-01 onward. The `PULL_DT` column records the run date.

### 1.5 Things to watch out for

1. **No lookback date filter in SQL.** The queries read the full historical range (pre-2023 from the old table, 2023+ from V6). The post-lag filter (`SVC_DT_M >= '2023-01-01'`) keeps only 2023+ months in the output. Pre-2023 data only matters for the 12-month rolling window that reaches back into 2022.
2. **Not limited to Kerendia.** The pivots cover all 74+ product groups. Kerendia is one of them. The model gets the HCP's prescribing volume across the full market basket, not just Kerendia.
3. **Column count is large (~1,337).** The 11-dimension pivot with 4 lag windows plus running totals produces a very wide table. Most columns are sparse (many product groups are rarely prescribed by a given HCP).
4. **Cross-notebook inconsistencies** (see 1.3): age group prefix, hypertension null replacement and `.na.fill(0)` behavior differ between notebook 26 and notebooks 27/28. If these are unified in a future refactor, downstream column references will need updating.
5. **`step2_fill_missing` uses global date range.** Every provider gets the same monthly calendar (global min to global max). Providers with claims only in 2025 still get rows for 2023 and 2024 (with null feature values). This inflates the row count but is needed for rolling-window calculations.
6. **`step3_lag` includes the current month.** `_IN_LAST_1_MONTH` is the same as the base monthly value. The lag is not shifted by one month.
7. **`00_config` not run by 27/28.** Notebook 26 runs `00_config` as a helper; 27 and 28 do not. All three load anchor dates from the same CSV inline. The only practical difference is that `00_config` may set additional global variables not used by these notebooks.
8. **HCP universe varies between runs.** The universe Delta table is refreshed between inference cycles. The three notebooks were last run on different dates, so they have slightly different universe sizes (222K vs 223K). In production they should be run in the same cycle.
9. **Missing vs 0.** For NBRx and NRx, months where the HCP had no claims in a dimension produce null after the fill-missing step, and nulls propagate through the rolling-window `SUM` (skipped, not treated as 0). For TRx, `.na.fill(0)` ensures these are 0.

### 1.6 Data used and terms

**Data used**

| Source | Path | Notes |
| --- | --- | --- |
| Historical LAAD LRx | `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_laad_based_lrx.KERENDIA_LAAD_BASED_LRX_FULL_DATA_STARTING_2021` | Pre-2023 data |
| Current LAAD LRx | `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_laad_based_lrx.KERENDIA_LAAD_BASED_LRX_V6` | 2023+ data |
| HCP universe | `.../ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` | Inner-joined in this notebook |
| Anchor dates | `.../ops_pipeline/query_output/hcp_model_inference_anchor_dates.csv` | Cohort `I01` lookback dates |
| Helper functions | `00_Helper_Notebooks/00_step23_function` | `step2_fill_missing`, `step3_lag` |

**Terms used in this document**

| Term | Meaning |
| --- | --- |
| NBRx | New-to-brand prescription: a patient's first Rx for the product (new or switched). IQVIA applies a 12-month product-specific lookback |
| NRx | New prescription: any new dispensing event, including new starts, restarts (after a gap) and switches from other products. Broader than NBRx |
| TRx | Total prescriptions: all prescriptions including refills and continuations. The broadest volume measure |
| LRx | IQVIA longitudinal prescription data, here derived from LAAD and grouped by prescriber, period and product group |
| LAAD | IQVIA's Linked Administrative Claims Data, the upstream source for the LRx tables |
| `PERIOD_TYPE` W / X | W = full week ending Friday. X = part of a week split at a month end |
| Pivot dimension | One of 11 demographic/clinical columns used to create one feature column per distinct value |
| Running total | Cumulative sum from the HCP's earliest month to the current month |

---

## 2. How NBA 3.0 builds the Competitor Drug NBRx Share features

### 2.0 What is this section about?

While notebooks 26/27/28 cover the HCP's own prescribing volume across all products and segments, notebook 31 answers a different question: **among the 4 SGLT2i competitor drugs (Farxiga, Invokana, Jardiance, Steglatro), what is each drug's share of the HCP's total SGLT2i NBRx?** This gives the model a sense of which competitor is most prevalent in each HCP's practice.

**In short**: the notebook reads LAAD-based LRx V6, pivots on `PRODUCT_GROUP` to get NBRx per SGLT2i competitor per NPI per month, computes each competitor's 12-month NBRx as a percentage of the 4-competitor total, and saves 4 percentage-share features to a Delta table.

This notebook differs from 26/27/28 in several ways: it uses `NPI` (not `PROVIDER_ID`) as the key, reads from V6 only (no split load), does not filter to the HCP universe, uses only a 12-month lag window, and produces only 4 percentage features.

### 2.1 Shared foundations

| Item | What it means | Last run |
| --- | --- | --- |
| Key column | `NPI_NUMBER` (renamed from `NPI` in the SQL query). **Not `PROVIDER_ID`** | — |
| HCP universe | **Not applied.** All NPIs in V6 are included | 2,288,153,597 rows from V6 |
| Cohort / lookback | **Not applied.** No lookback date filter in the SQL query | — |
| Join key | `NPI_NUMBER` + `SVC_DT_M` | — |

**Source table**

| Source | Table | Date filter | Rows (last run) |
| --- | --- | --- | --- |
| LAAD-based LRx (V6 only) | `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_laad_based_lrx.KERENDIA_LAAD_BASED_LRX_V6` | None (reads all data) | 2,288,153,597 |

**Helper notebooks**

| Helper | Provides |
| --- | --- |
| `00_connection` | Spark session, imports |
| `00_step23_function` | `step2_fill_missing`, `step3_lag` |

Note: this notebook does **not** run `00_config`.

---

### 2.2 Data sources and preprocessing

**a. Data sources**

A single SQL query reads all rows from `KERENDIA_LAAD_BASED_LRX_V6` with no date filter. The query renames `NBRX` to `PROJECTED_NBRX`, `TRX` to `PROJECTED_TRX`, `NRX` to `PROJECTED_NRX`, and `NPI` to `NPI_NUMBER`. A `PULL_DT` column is added with `current_date()`.

**b. Preprocessing steps**

1. **Monthly truncation.** *What:* convert `PERIOD_ID` (string `yyyyMMdd`) to a date (`YEAR_MONTH_DAY`), then truncate to month (`SVC_DT_M`). Same approach as 26/27/28.

2. **Pivot on PRODUCT_GROUP.** *What:* replace null/`'NULL'` `PRODUCT_GROUP` values with `'UNKNOWN'`, then normalise any product group containing `'FARXIGA'` to `'FARXIGA'` (this consolidates brand and generic Farxiga variants, per a March 2024 IQVIA data update). Group by `[NPI_NUMBER, SVC_DT_M]`, pivot on `PRODUCT_GROUP`, and `SUM(PROJECTED_NBRX)`. Clean column names with the same character-replacement logic as 26/27/28.

3. **Select 4 competitor drugs.** *What:* from the full pivot, select only `TOTAL_NBRX_CLAIMS_FARXIGA`, `TOTAL_NBRX_CLAIMS_INVOKANA`, `TOTAL_NBRX_CLAIMS_JARDIANCE`, `TOTAL_NBRX_CLAIMS_STEGLATRO`. Compute `TOTAL_NBRX_CLAIMS` as the sum of these 4 competitors. *Detail to know:* Kerendia is NOT included in the total. The share is among the 4 SGLT2i competitors only.

4. **Fill missing months** (`step2_fill_missing`). *What:* generate a continuous monthly calendar from global min to global max `SVC_DT_M`, cross-join with every distinct `NPI_NUMBER`, and left-join. Same logic as 26/27/28 but keyed on `NPI_NUMBER`.

5. **Create 12-month lag features** (`step3_lag`). *What:* compute `SUM` over `rowsBetween(-11, 0)` for each column (the 4 competitors + the total). Only a 12-month window is used (`last_i_month_list = [12]`), unlike 26/27/28 which use `[1, 3, 6, 12]`. Running totals are also computed but are dropped later.

6. **Drop base columns and running totals.** *What:* drop all original (non-lagged) columns, keeping only `NPI_NUMBER`, `SVC_DT_M`, and the 12-month lag columns.

7. **Compute percentage shares.** *What:* for each of the 4 competitors, compute `competitor_12_month_nbrx / total_12_month_nbrx`, with division-by-zero handled by `when().otherwise(0)`.

8. **Filter and save.** *What:* filter `NPI_NUMBER` not null, fill remaining nulls with 0, filter `SVC_DT_M >= '2022-11-01'`, add `PULL_DT`, and write to Delta.

**c. Features created**

| Feature | Business meaning | Formula |
| --- | --- | --- |
| `PERC_FARXIGA_NBRX_SHARE` | Farxiga's share of the HCP's 4-competitor SGLT2i NBRx in the last 12 months | `TOTAL_NBRX_CLAIMS_FARXIGA_IN_LAST_12_MONTH / TOTAL_NBRX_CLAIMS_IN_LAST_12_MONTH` |
| `PERC_JARDIANCE_NBRX_SHARE` | Jardiance's share | `TOTAL_NBRX_CLAIMS_JARDIANCE_IN_LAST_12_MONTH / TOTAL_NBRX_CLAIMS_IN_LAST_12_MONTH` |
| `PERC_INVOKANA_NBRX_SHARE` | Invokana's share | `TOTAL_NBRX_CLAIMS_INVOKANA_IN_LAST_12_MONTH / TOTAL_NBRX_CLAIMS_IN_LAST_12_MONTH` |
| `PERC_STEGLATRO_NBRX_SHARE` | Steglatro's share | `TOTAL_NBRX_CLAIMS_STEGLATRO_IN_LAST_12_MONTH / TOTAL_NBRX_CLAIMS_IN_LAST_12_MONTH` |

Each percentage is between 0 and 1. When the total is 0 (the HCP wrote no SGLT2i NBRx in the last 12 months), the share is set to 0.

---

### 2.3 What the final table looks like

| Output | Key columns | Feature columns | Metadata | Contains |
| --- | --- | --- | --- | --- |
| `.../ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_perc_competitor_nbrx_shares_for_inference` | `NPI_NUMBER`, `SVC_DT_M` | 4 percentage shares | `PULL_DT` | 2.2 |

Full output path: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_perc_competitor_nbrx_shares_for_inference`.

Filtered to `SVC_DT_M >= '2022-11-01`. Last run `PULL_DT = 2025_10_08`.

### 2.4 Things to watch out for

1. **NPI-based, not PROVIDER_ID-based.** This notebook keys on `NPI_NUMBER`, unlike 26/27/28 which key on `PROVIDER_ID`. The combine step (`99_Combine_Physician_Data`) must join on a different key or map NPI to PROVIDER_ID.
2. **No HCP universe filter.** All NPIs in V6 are included. The combine step later handles the universe restriction.
3. **Only V6, no split load.** Unlike 26/27/28 which read from two tables (pre-2023 + 2023+), this notebook reads only from V6. Pre-2023 data is not included, so the 12-month rolling window for months in late 2022 may be incomplete.
4. **Only 12-month lag window.** Unlike 26/27/28 which use 1, 3, 6, 12-month windows, this notebook only computes 12-month rolling sums. No shorter windows are available.
5. **Farxiga consolidation.** Any `PRODUCT_GROUP` containing `'FARXIGA'` is relabelled to `'FARXIGA'`. This consolidates brand and generic variants per a March 2024 IQVIA update. If new Farxiga variants appear, they will be captured automatically.
6. **4 competitors only.** The share is among Farxiga, Invokana, Jardiance and Steglatro — all SGLT2i inhibitors. Kerendia (an MRA) is not a competitor in this share calculation. Other SGLT2i drugs (e.g. Inpefa) are not included because they do not appear in the V6 data or are not in the select list.
7. **No `.na.fill(0)` on pivot.** Null product groups are replaced with `'UNKNOWN'` before the pivot, but the pivot output is not filled with 0. The `fillna(0)` at the end (cell 22) fills all remaining nulls after the percentage computation.
8. **Date filter starts 2022-11-01.** The output is filtered to `SVC_DT_M >= '2022-11-01'`, one month earlier than the 2023-01-01 filter in 26/27/28. This allows the 12-month window for January 2023 to reach back to November 2022.

### 2.5 Data used and terms

**Data used**

| Source | Path | Notes |
| --- | --- | --- |
| Input | `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_laad_based_lrx.KERENDIA_LAAD_BASED_LRX_V6` | Read at last run (2025-10-08) |
| Output | `.../ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_perc_competitor_nbrx_shares_for_inference` | `PULL_DT = 2025_10_08` |
| Helper functions | `00_Helper_Notebooks/00_step23_function` | `step2_fill_missing`, `step3_lag` |

**Terms used in this section**

| Term | Meaning |
| --- | --- |
| SGLT2i | Sodium-glucose cotransporter-2 inhibitor class. Includes Farxiga, Jardiance, Invokana and Steglatro |
| MRA | Mineralocorticoid receptor antagonist. Kerendia (finerenone) is an MRA, not an SGLT2i |
| NBRx share | A competitor drug's NBRx as a percentage of the total NBRx across the 4 SGLT2i competitors |
| Farxiga consolidation | IQVIA updated Farxiga to include combined brand and generic from March 2024. The code normalises any product group containing 'FARXIGA' to 'FARXIGA' |
