---
name: laad-rx-features
description: >
  Consolidated reference for the three LAAD-based prescription feature notebooks (26_Features_NBRx,
  27_Features_NRx, 28_Features_TRx) in the Kerendia NBA 3.x HCP-level feature engineering pipeline.
  Covers NBRx/NRx/TRx metric definitions and business rules, the shared 8-step pipeline, the 11
  pivot dimensions with cardinalities, lag window configuration, output column naming conventions,
  data source choice (HCP-patient level vs patient-level), upstream LAAD V6 provenance, and
  cross-notebook parameterization. Read this skill when generating, modifying, debugging, or
  understanding any of the three Rx feature notebooks, or when deciding which LAAD prescription
  table to use for a new notebook.
---

# LAAD-Based Prescription Feature Engineering (NBRx / NRx / TRx)

Single consolidated reference for the three HCP-level prescription feature notebooks in the
Kerendia NBA 3.x pipeline. These notebooks share an identical 8-step pipeline and differ only
in which metric column they aggregate. This skill abstracts those differences into a
parameterization table and documents everything else as shared logic.

---

## 1. Metric Definitions and Business Rules

### 1.1 What Each Metric Measures

| Metric | Full Name | Definition | IQVIA Lookback Rule |
| --- | --- | --- | --- |
| **NBRx** | New-to-Brand Rx | A prescription where the patient had **no claim for the same product in the prior 12 months**. Captures genuine new patient starts on a brand. | 12-month product-specific lookback. The lookback is against the same product, not all products or all prescriptions. |
| **NRx** | New Rx | Any **new prescription dispensing event** — includes new starts, restarts (after a gap), and switches from other products. Broader than NBRx because a "restart" after 6 months counts as NRx but NOT NBRx (the 12-month lookback still sees the old claim). | N/A — NRx is defined by source-of-business classification, not a lookback window. |
| **TRx** | Total Rx | **All prescriptions** — new, refills, continuations, everything. The broadest volume measure. | N/A — all claims are TRx. |

### 1.2 Subset Hierarchy

```
NBRx  ⊆  NRx  ⊆  TRx
```

Every NBRx is an NRx, and every NRx is a TRx, but not vice versa. A refill is a TRx but
not an NRx. A restart after 6 months is an NRx but not an NBRx.

### 1.3 When to Use Each Metric Downstream

| Use Case | Metric | Why |
| --- | --- | --- |
| New patient acquisition / brand adoption | NBRx | Captures only genuinely new-to-brand starts |
| Prescribing initiation behavior (including restarts) | NRx | Captures all new dispensing events regardless of prior history |
| Total prescribing volume / market share | TRx | Captures full prescription volume including refills |
| Source-of-business analysis (switch-from, add-on) | NBRx or NRx | SOB is most meaningful for new prescriptions |
| Adherence / persistence signals | TRx | Refill patterns require total volume |

### 1.4 Population Scope

For Kerendia analyses, the population is scoped to `HF +/- CKD` and `CKD Only` indication
groups. The IQVIA LAAD source data covers Kerendia, SGLT2, and sMRA product groups. Do not
use a Kerendia-only NBRx/TRx definition for an all-products population.

---

## 2. Data Source Choice: HCP-Patient Level vs Patient-Level

The LAAD ecosystem has two distinct table families for prescription data. Choosing the wrong
one will produce incorrect features or fail at the wrong grain.

### 2.1 Two-Table Comparison

| Aspect | HCP-Patient Level (used by these notebooks) | Patient-Level |
| --- | --- | --- |
| **Table** | `kerendia_laad_based_lrx.KERENDIA_LAAD_BASED_LRX_V6` | `pace_ker_in_house_schema.pt_lvl_nbrx` / `pt_lvl_trx` |
| **Grain** | Provider × Week × Product × Indication × Demographics | Patient × Claim (one row per claim) |
| **Has PATIENT_ID?** | No — patients are aggregated away | Yes — tracks individual patients |
| **NBRX/NRX/TRX columns** | Pre-computed **counts** at the combined dimensional grain | `pt_lvl_nbrx`: one row per NBRx claim; `pt_lvl_trx`: one row per TRx claim |
| **Key ID column** | `PROVIDER_ID` (IQVIA prescriber ID) | `PATIENT_ID`, `PROVIDER_ID`, `CLAIM_ID` |
| **Date column** | `WEEK_ENDING_DATE` (week-ending Friday) | `NBRX_DT` (NBRx) / `SVC_DT` (TRx) |
| **Dimensional richness** | 11 demographic/clinical dimensions (product, specialty, switch-from, add-on-to, age, gender, payer, SOB, channel, indication, hypertension) | Patient demographics (age, gender), payer, indication flags, 180-day lookback month |
| **Row count** | Large (billions of rows in V6) | Varies by product scope |
| **Catalog** | `ph-com-ai-us-prod-catalog-2553213839599380` | `ph-com-ai-us-prod-catalog-2553213839599380` |

### 2.2 Decision Tree for New Notebooks

```
Does the notebook need individual PATIENT_ID?
  ├─ YES → Use patient-level tables (pt_lvl_nbrx / pt_lvl_trx)
  │        Examples: patient journey analysis, SOB lookbacks, therapy persistence
  └─ NO → Is the output grain PROVIDER_ID × time?
           ├─ YES → Use HCP-patient level (V6)
           │        Examples: HCP-level features, market share by provider
           └─ NO → Evaluate case-by-case
```

### 2.3 Why These Notebooks Use HCP-Patient Level

1. **Output grain is PROVIDER_ID × month** — individual patient identity is not needed
2. **Folder context**: `03_HCP_Level_Features` — the model predicts per-HCP, not per-patient
3. **Dimensional richness**: V6 provides 11 pre-computed dimensions (switch-from, add-on-to,
   channel, payer, indication, hypertension) that enable pivot-based feature engineering
4. **Pre-computed metrics**: NBRx, NRx, TRx are already computed upstream — the notebooks
   simply `SUM()` the pre-computed columns

> **Warning:** Do not join the HCP-patient level table to patient-level claim rows on
> `PROVIDER_ID` alone. The HCP-patient level data is pre-aggregated at Provider × Week ×
> Product × Indication × Demographics — joining to claim-level rows will fan out and
> inflate counts.

---

## 3. Upstream Data Provenance

### 3.1 Source Tables

The notebooks read from two tables in
`ph-com-ai-us-prod-catalog-2553213839599380.kerendia_laad_based_lrx`:

| Table | Date Range | Purpose |
| --- | --- | --- |
| `KERENDIA_LAAD_BASED_LRX_FULL_DATA_STARTING_2021` | `WEEK_ENDING_DATE < '20230101'` | Historical data (pre-2023) |
| `KERENDIA_LAAD_BASED_LRX_V6` | `WEEK_ENDING_DATE >= '20230101'` | Current data (2023+) |

Both tables share the same schema. The notebooks union them after loading.

### 3.2 What V6 Is

`KERENDIA_LAAD_BASED_LRX_V6` is the output of an upstream Snowflake-to-Unity-Catalog
migration pipeline. That pipeline:

1. Reads from **11 Snowflake source tables** (LAAD prescription facts, patient demographics,
   provider dimensions, product dimensions, plan dimensions, etc.)
2. Applies **indication grouping** (T2D, CKD, HF, CVD combinations)
3. Applies **hypertension flagging** (HTN flag)
4. Labels **switch-from / add-on-to** therapy patterns
5. **Pre-computes NBRx, NRx, and TRx** at the provider × week × product × indication ×
   demographic grain
6. Enriches with patient demographics, HCP attributes, and payer information
7. Outputs to `KERENDIA_LAAD_BASED_LRX_V6`

**The three feature notebooks do NOT compute NBRx/NRx/TRx from scratch.** They consume the
pre-computed columns from V6 and aggregate them into HCP-level monthly features.

**Upstream documentation:**
[LAAD_LRx_Migration_Analysis.md](https://github.com/WenjieAtBayer/kerendia_nba_3_1_develop/blob/c871010d75fa2888066491772e0bc536f08e5a42/NBA%203.1%20-%20Dev/02_Input_Data_Creation/00_Data_Migration/LAAD_LRx_Migration_Analysis.md)
— full pipeline flow, source systems, helper/master notebook steps, and output schema.
The upstream pipeline is a separate skill-sized topic; this skill covers the downstream
feature engineering only.

### 3.3 Columns Selected from V6

All three notebooks select the same 21 columns via `SELECT DISTINCT`:

```sql
SELECT DISTINCT
  WEEK_ENDING_DATE, PROVIDER_ID, PERIOD_ID, PERIOD_TYPE,
  SPECIALTY_GROUP, PRODUCT_GROUP, SWITCH_FROM, ADD_ON_TO,
  AGE_GROUP, GENDER, PAY_TYPE, SOURCE_OF_BUSINESS, RX_CHANNEL,
  INDICATION_GROUP, HYPERTENSION_FLAG, PAYER_PLAN_ID,
  NBRX, TRX, NRX, NPI, PRI_SPCL_DESC
FROM `ph-com-ai-us-prod-catalog-2553213839599380`.`kerendia_laad_based_lrx`.
  KERENDIA_LAAD_BASED_LRX_V6
WHERE WEEK_ENDING_DATE >= '20230101'
```

---

## 4. Parameterization: What Varies vs What Stays the Same

### 4.1 What Changes Between the Three Notebooks

| Parameter | NBRx (Notebook 26) | NRx (Notebook 27) | TRx (Notebook 28) |
| --- | --- | --- | --- |
| Metric column aggregated | `NBRX` | `NRX` | `TRX` |
| Aggregation expression | `F.sum("NBRX").alias("SUM_NBRX")` | `F.sum("NRX").alias("SUM_NRX")` | `F.sum("TRX").alias("SUM_TRX")` |
| Column prefix (general pattern) | `TOTAL_HCP_NBRX_CLAIMS_{DIM}_` | `TOTAL_HCP_NRX_CLAIMS_{DIM}_` | `TOTAL_HCP_TRX_CLAIMS_{DIM}_` |
| Age group prefix (**inconsistency**) | `TOTAL_HCP_NBRX_CLAIMS_AGE_GROUP_` | `TOTAL_HCP_NRX_CLAIMS_AGE_` | `TOTAL_HCP_TRX_CLAIMS_AGE_` |
| Hypertension null replacement (**inconsistency**) | `UNKNOWN_HF` | `UNKNOWN_HP` | `UNKNOWN_HP` |
| `.na.fill(value=0)` after pivot | **Commented out** (nulls preserved) | **Commented out** (nulls preserved) | **Active** (nulls → 0) |
| Output variable name | `df_nbrx_feats` | `df_nrx_feats` | `df_trx_feats` |
| Output Delta path suffix | `nbrx_features_w_provider_id_for_inference` | `nrx_features_w_provider_id_for_inference` | `trx_features_w_provider_id_for_inference` |

### 4.2 Known Cross-Notebook Inconsistencies

**Age group prefix:** NBRx uses `AGE_GROUP_` (e.g., `TOTAL_HCP_NBRX_CLAIMS_AGE_GROUP_65above`)
while NRx and TRx use `AGE_` (e.g., `TOTAL_HCP_NRX_CLAIMS_AGE_65above`). This is a naming
drift between notebook 26 and notebooks 27/28. If this is unified in a future refactor,
downstream column references will need updating.

**Hypertension null replacement:** NBRx replaces null/`'NULL'` hypertension values with
`UNKNOWN_HF`, while NRx and TRx use `UNKNOWN_HP`. The resulting pivoted column names differ
(e.g., `..._HYPERTENSION_UNKNOWN_HF` vs `..._HYPERTENSION_UNKNOWN_HP`). This is naming
drift, but with a semantic wrinkle: in this codebase, `HF` is the standard abbreviation for
**Heart Failure** (an indication group — see `CKD + HF`, `T2D + HF` in the INDICATION_GROUP
values), NOT for Hypertension Flag. The `UNKNOWN_HP` variant in NRx/TRx is the more
accurate abbreviation (HP = Hypertension). The `UNKNOWN_HF` in NBRx is a likely copy-paste
error that borrowed the Heart Failure abbreviation instead of the Hypertension one. The
null-replacement logic itself is identical across all three notebooks — only the string
literal differs. If this is unified in a future refactor, downstream column references will
need updating.

**`.na.fill(0)` behavioral difference:** TRx fills pivot nulls with 0 after each pivot
(interpretation: "no claims = 0 claims"). NBRx and NRx leave pivot nulls as null
(interpretation: "no claims = unknown/absent"). This is likely intentional but reason
unverified. The difference is semantically meaningful: in `step3_lag`, the
`SUM().over(Window.rowsBetween(...))` window function treats null as "skip" (does not
contribute to the sum) but treats 0 as "zero" (contributes zero to the sum). This means
TRx running totals and lag features will never be null for a provider-month where the
provider exists in the spine, while NBRx/NRx lag features CAN be null if all months in
the window had null base values.

### 4.3 What Stays the Same

| Shared Element | Value |
| --- | --- |
| Source tables | `KERENDIA_LAAD_BASED_LRX_FULL_DATA_STARTING_2021` (old) + `KERENDIA_LAAD_BASED_LRX_V6` (new) |
| Split date | `WEEK_ENDING_DATE` < / >= `'20230101'` |
| Columns selected | Same 21 columns (see Section 3.3) |
| HCP universe path | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` |
| HCP universe size | See HCP universe Delta path (changes per inference cycle) |
| Index columns | `[PROVIDER_ID, SVC_DT_M]` |
| 11 pivot dimensions | Product Group, Specialty Group, Switch From, Add On To, Age Group, Pay Type, SOB, Rx Channel, Indication Group, Hypertension Flag, Gender |
| `INDICATION_GROUP` cleanup | `'ALL OTHERS'` → `'ALL_OTHERS'` |
| Date truncation | `PERIOD_ID` → `SVC_DT` → `YEAR_MONTH_DAY` → `SVC_DT_M` (trunc to month) |
| Fill missing function | `step2_fill_missing(df, key_col="PROVIDER_ID", date_col="SVC_DT_M")` |
| Lag function | `step3_lag(df, key_col="PROVIDER_ID", date_col="SVC_DT_M", last_i_month_list=[1,3,6,12])` |
| Post-lag date filter | `SVC_DT_M >= '2023-01-01'` |
| Metadata column | `PULL_DT` (current date as `YYYY_MM_DD` string literal) |
| Write mode | `overwrite` with `overwriteSchema=true` |
| Output format | Delta |
| Helper notebooks | `00_connection`, `00_config`, `00_step23_function` |

---

## 5. Shared Pipeline (8 Steps)

All three notebooks follow the same 8-step flow. The primary variation is the metric
column being aggregated (see Section 4.1). Three additional cross-notebook inconsistencies
(age group prefix, hypertension null replacement, `.na.fill(0)` behavior) are documented
in Section 4.2 and called out inline below where they affect specific steps.

### Step 1: Load V6 Data (Split Load)

**What:** Load LAAD-based LRx data from two tables, split by date.

**Logic:**
```python
# Old data (pre-2023)
query_old = """
  SELECT DISTINCT <21 columns>
  FROM `ph-com-ai-us-prod-catalog-2553213839599380`.`kerendia_laad_based_lrx`
    .KERENDIA_LAAD_BASED_LRX_FULL_DATA_STARTING_2021
  WHERE WEEK_ENDING_DATE < '20230101'
"""
hcp_lrx_claims_old = spark.sql(query_old)

# New data (2023+)
query_new = """
  SELECT DISTINCT <21 columns>
  FROM `ph-com-ai-us-prod-catalog-2553213839599380`.`kerendia_laad_based_lrx`
    .KERENDIA_LAAD_BASED_LRX_V6
  WHERE WEEK_ENDING_DATE >= '20230101'
"""
hcp_lrx_claims_new = spark.sql(query_new)

# Format PERIOD_ID to yyyyMMdd string
hcp_lrx_claims_new = hcp_lrx_claims_new.withColumn("PERIOD_ID", date_format("PERIOD_ID", "yyyyMMdd"))

# Union
hcp_lrx_claims = hcp_lrx_claims_old.unionByName(hcp_lrx_claims_new)
```

**Grain at this point:** Provider × Week × Product × Indication × Demographics (unchanged
from source).


> **Note on `unionByName` vs `union`:** NBRx uses `unionByName`, while NRx and TRx use
> `union`. Both work here because the column order is identical (same SELECT statement),
> but `unionByName` is the safer choice if column order ever drifts.

### Step 2: Filter to HCP Universe

**What:** Inner join to the HCP universe to keep only providers of interest.

**Logic:**
```python
hcp_universe = spark.read.format("delta").load(hcp_universe_path)
hcp_universe = hcp_universe.select("PROVIDER_ID")
hcp_lrx_claims = hcp_universe.join(hcp_lrx_claims, on="PROVIDER_ID", how="inner")
```

**Grain:** Same as Step 1, but filtered to the HCP universe.


### Step 3: Monthly Truncation

**What:** Convert weekly `PERIOD_ID` to monthly `SVC_DT_M`.

**Logic:**
```python
hcp_lrx_claims = hcp_lrx_claims.withColumn(
    "SVC_DT",
    concat(substring('PERIOD_ID',1,4), substring('PERIOD_ID',5,2), substring('PERIOD_ID',7,2))
)
hcp_lrx_claims = hcp_lrx_claims.withColumn(
    "YEAR_MONTH_DAY",
    F.to_date(F.unix_timestamp(hcp_lrx_claims.SVC_DT, 'yyyyMMdd').cast('timestamp'))
)
hcp_lrx_claims = hcp_lrx_claims.withColumn("SVC_DT_M", trunc("YEAR_MONTH_DAY", 'month'))
hcp_lrx_claims = hcp_lrx_claims.drop('SVC_DT').drop('YEAR_MONTH_DAY')
```

**Also applies:** `INDICATION_GROUP` cleanup: `'ALL OTHERS'` → `'ALL_OTHERS'`.

**Grain after this step:** Provider × Month × Product × Indication × Demographics
(multiple rows per provider-month because the original weekly/dimensional grain is preserved;
aggregation happens in Step 4).

### Step 4: Pivot and Aggregate Across 11 Dimensions

**What:** For each of the 11 dimensions, group by `[PROVIDER_ID, SVC_DT_M]`, pivot on the
dimension values, and compute `SUM(<metric>)`.

This produces 11 separate DataFrames, each at the `(PROVIDER_ID, SVC_DT_M)` grain, with
one column per distinct value of that dimension.

**Pattern (example: Product Group for NBRx):**
```python
df_category_claims = hcp_lrx_claims.withColumn(
    "PRODUCT_GROUP",
    F.when(((col("PRODUCT_GROUP").isNull()) | (col('PRODUCT_GROUP') == 'NULL')),
           'UNKNOWN_PG').otherwise(col('PRODUCT_GROUP'))
)

df_category = (
    df_category_claims
    .groupBy(["PROVIDER_ID", "SVC_DT_M"]).pivot("PRODUCT_GROUP")
    .agg(F.sum("NBRX").alias("SUM_NBRX"))   # ← metric column changes per notebook
)

# Clean column names
df_category = df_category.select([
    F.col(c).alias('TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_' +  # ← prefix changes per notebook
        c.replace(", ", " ").replace("+", "and")
         .replace("/", " or ").replace("-", "_")
         .replace(" ", "_").replace("__", "_")
         .replace("(", "").replace(")", "")
         .replace("&", "").upper())
    if c not in ["PROVIDER_ID", "SVC_DT_M"] else col(c)
    for c in df_category.columns
])
```

See Section 6 for all 11 dimensions and their specific prefixes.

> **Step 4 inconsistencies (see Section 4.2 for full details):**
> - **`.na.fill(0)` after pivot:** TRx calls `.na.fill(value=0)` after each pivot
>   (replacing null with 0). NBRx and NRx have this line commented out (nulls preserved).
>   The code example above shows the NBRx/NRx variant. For TRx, add `.na.fill(value=0)`
>   after the `.agg()` call in each pivot.
> - **Age group prefix:** NBRx uses `AGE_GROUP_`, NRx/TRx use `AGE_`.
> - **Hypertension null replacement:** NBRx uses `UNKNOWN_HF`, NRx/TRx use `UNKNOWN_HP`.

**Grain after this step:** `(PROVIDER_ID, SVC_DT_M)` — one row per provider per month,
with pivoted columns for each dimension.

### Step 5: Join Into Spine

**What:** Left-join all 11 dimension DataFrames into a single spine.

**Logic:**
```python
df_spine = (
    df_category
    .join(df_specialty, how='left', on=["PROVIDER_ID", "SVC_DT_M"])
    .join(df_switch, how='left', on=["PROVIDER_ID", "SVC_DT_M"])
    .join(df_add_on_to, how='left', on=["PROVIDER_ID", "SVC_DT_M"])
    .join(df_patient_age, how='left', on=["PROVIDER_ID", "SVC_DT_M"])
    .join(df_payer, how='left', on=["PROVIDER_ID", "SVC_DT_M"])
    .join(df_sob, how='left', on=["PROVIDER_ID", "SVC_DT_M"])
    .join(df_channels, how='left', on=["PROVIDER_ID", "SVC_DT_M"])
    .join(df_indication_grp, how='left', on=["PROVIDER_ID", "SVC_DT_M"])
    .join(df_hypertension_flag, how='left', on=["PROVIDER_ID", "SVC_DT_M"])
    .join(df_gender, how='left', on=["PROVIDER_ID", "SVC_DT_M"])
)
```

**Grain:** `(PROVIDER_ID, SVC_DT_M)` — same as Step 4, but now wide (all dimension columns
in one DataFrame).

**Note:** `df_category` (Product Group) is the left spine anchor. All other dimensions
are left-joined to it. If a provider-month has product group claims but no claims in
another dimension, those columns will be null.

### Step 6: Fill Missing Months (`step2_fill_missing`)

**What:** Ensure every provider has a continuous monthly time series from their earliest
to their latest month.

**Function (from `00_step23_function`):**
```python
def step2_fill_missing(df, key_col, date_col):
    # Generate all months from global min to global max
    date_list_df = (
        df.select(date_col)
        .agg(F.min(date_col).alias('min_date'), F.max(date_col).alias('max_date'))
        .withColumn(date_col,
            F.explode(F.expr('sequence(min_date, max_date, interval 1 month)')))
        .drop("min_date", "max_date")
    )
    # Cross-join with distinct providers
    patient_id_list_df = df.select(key_col).distinct()
    patient_date_full_list = patient_id_list_df.crossJoin(date_list_df)
    # Left-join back original data
    return patient_date_full_list.join(df, on=[key_col, date_col], how="left")
```

**Business rule:** The cross-join uses the **global** min/max dates across ALL providers,
not per-provider min/max. This means every provider gets the same full date range,
regardless of when their first/last claim occurred.

**Cost:** The cross-join of all providers × all months produces a large intermediate
result. This is manageable but is the most expensive step after the initial data load.

**Grain after this step:** `(PROVIDER_ID, SVC_DT_M)` — one row per provider per month
(guaranteed continuous). Feature columns are null for months where the provider had no
claims.

### Step 7: Create Lag Features (`step3_lag`)

**What:** Compute rolling-window sums and cumulative running totals for every feature column.

**Function (from `00_step23_function`):**
```python
def step3_lag(df, key_col, date_col, last_i_month_list):
    window_base = Window.partitionBy(key_col).orderBy(date_col)
    features = [col for col in df.columns if col not in [key_col, date_col]]

    # Rolling window sums: SUM over last i months (inclusive of current month)
    last_i_month = [
        F.sum(col).over(window_base.rowsBetween(-i+1, 0))
         .alias(col + "_IN_LAST_" + str(i) + "_MONTH")
        for i in last_i_month_list for col in features
    ]

    # Cumulative running total (inclusive of current month)
    running_total = [
        F.sum(col).over(window_base.rowsBetween(Window.unboundedPreceding, Window.currentRow))
         .alias("RUNNING_" + col)
        for col in features
    ]

    return df.select("*", *last_i_month, *running_total)
```

**Lag windows:** `[1, 3, 6, 12]` months.

**Window frame semantics:**
- `_IN_LAST_1_MONTH` = `rowsBetween(0, 0)` = current month only
- `_IN_LAST_3_MONTH` = `rowsBetween(-2, 0)` = current + 2 prior months
- `_IN_LAST_6_MONTH` = `rowsBetween(-5, 0)` = current + 5 prior months
- `_IN_LAST_12_MONTH` = `rowsBetween(-11, 0)` = current + 11 prior months
- `RUNNING_` = `rowsBetween(unboundedPreceding, currentRow)` = all history up to and
  including current month

**Important:** The window includes the current row (`0`). This means `_IN_LAST_1_MONTH`
is the same as the base feature value for that month. The lag features are NOT shifted
by one month — they include the current month.

**Column explosion:** For N base feature columns and 4 lag windows, `step3_lag` produces
`N × 4` lag columns + `N` running-total columns = `N × 5` new columns. With 11 dimensions
each having multiple pivot values, the total column count grows significantly.

**Post-lag cleanup:** After `step3_lag`, the base feature columns (from Step 4) are dropped:
```python
keep_cols = ["PROVIDER_ID", "SVC_DT_M"]
cols_to_drop = [c for c in df_spine_step2.columns if c not in keep_cols]
df_feats = df_feats.drop(*cols_to_drop)
```

This keeps only PROVIDER_ID, SVC_DT_M, the lag columns, and the running-total columns.

### Step 8: Filter, Add Metadata, and Save

**What:** Filter to recent data, add pull-date metadata, write to Delta.

**Logic:**
```python
# Filter to recent dates
df_feats = df_feats.filter(F.to_date('SVC_DT_M') >= '2023-01-01')

# Remove null PROVIDER_IDs
df_feats = df_feats.filter(df_feats.PROVIDER_ID.isNotNull())

# Rename NPI column
df_feats = df_feats.withColumnRenamed("NPI", "NPI_NUMBER")

# Add pull-date metadata
curr_date = str(dt.today().strftime('%Y_%m_%d'))
df_feats = df_feats.withColumn("PULL_DT", F.lit(curr_date))

# Write
df_feats.write.mode("overwrite").format("delta") \
    .option("overwriteSchema", "true") \
    .save(output_path)
```

**Output paths:**

| Metric | Output Path |
| --- | --- |
| NBRx | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_nbrx_features_w_provider_id_for_inference` |
| NRx | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_nrx_features_w_provider_id_for_inference` |
| TRx | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_trx_features_w_provider_id_for_inference` |

**Grain:** `(PROVIDER_ID, SVC_DT_M)` — one row per provider per month, from 2023-01-01
onward, with lag and running-total feature columns.

---

## 6. The 11 Pivot Dimensions

Each dimension follows the same pattern: null/`'NULL'` replacement → groupBy → pivot → agg
→ column rename. The table below documents each dimension with its actual cardinality and
distinct values as queried from V6.

### 6.1 Dimension Reference Table

| # | Dimension | Pivot Column | Null Replacement | Cardinality | Column Prefix (NBRx) |
| --- | --- | --- | --- | --- | --- |
| 1 | Product Group | `PRODUCT_GROUP` | `UNKNOWN_PG` | 74 + null | `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_` |
| 2 | Specialty Group | `SPECIALTY_GROUP` | `UNKNOWN` | 6 + null | `TOTAL_HCP_NBRX_CLAIMS_SPEC_` |
| 3 | Switch From | `SWITCH_FROM` | `UNKNOWN` | ~74 + null | `TOTAL_HCP_NBRX_CLAIMS_SWITCH_FROM_` |
| 4 | Add On To | `ADD_ON_TO` | `UNKNOWN` | ~74 + null | `TOTAL_HCP_NBRX_CLAIMS_ADD_ON_TO_` |
| 5 | Age Group | `AGE_GROUP` | *(no replacement)* | 8 | `TOTAL_HCP_NBRX_CLAIMS_AGE_GROUP_` (see note) |
| 6 | Pay Type | `PAY_TYPE` | *(no replacement)* | 5 | `TOTAL_HCP_NBRX_CLAIMS_PAY_TYPE_` |
| 7 | Source of Business | `SOURCE_OF_BUSINESS` | *(no replacement)* | 6 | `TOTAL_HCP_NBRX_CLAIMS_SOB_` |
| 8 | Rx Channel | `RX_CHANNEL` | *(no replacement)* | 4 + null | `TOTAL_HCP_NBRX_CLAIMS_CHANNEL_` |
| 9 | Indication Group | `INDICATION_GROUP` | *(no replacement)* | 16 | `TOTAL_HCP_NBRX_CLAIMS_INDICATION_GROUP_` |
| 10 | Hypertension Flag | `HYPERTENSION_FLAG` | `UNKNOWN_HF` (NBRx) / `UNKNOWN_HP` (NRx/TRx) | 1 + null | `TOTAL_HCP_NBRX_CLAIMS_HYPERTENSION_` |
| 11 | Gender | `GENDER` | `UNKNOWN` | 3 | `TOTAL_HCP_NBRX_CLAIMS_GENDER_` |

> **Note on prefix for NRx/TRx:** Replace `NBRX` in the prefix with `NRX` or `TRX`
> respectively. All other components stay the same EXCEPT the age group and hypertension
> inconsistencies documented in Section 4.2.

### 6.2 Distinct Values Per Dimension

**Specialty Group (6 + null):**
`ALL OTHERS`, `CARDIOLOGY`, `ENDOCRINOLOGY`, `NEPHROLOGY`, `NP/PA`, `PCP/IM`, *null*

**Age Group (8):**
`<18`, `18-24`, `25-34`, `35-44`, `45-54`, `55-64`, `65+`, `UNKNOWN`

**Pay Type (5):**
`CASH`, `MEDICAID`, `MEDICARE`, `MEDICARE PART D`, `THIRD PARTY`

**Source of Business (6):**
`Add On`, `Immediate Continue`, `Immediate Switch`, `New to Market`, `Restart Different`,
`Restart Same`

**Rx Channel (4 + null):**
`A` (adjusted), `L` (long-term care), `M` (mail order), `R` (retail), *null*

**Indication Group (16):**
`ALL_OTHERS`, `CKD`, `CKD + CVD`, `CKD + CVD + HF`, `CKD + HF`, `CVD`, `CVD + HF`, `HF`,
`T2D`, `T2D + CKD`, `T2D + CKD + CVD`, `T2D + CKD + CVD + HF`, `T2D + CKD + HF`,
`T2D + CVD`, `T2D + CVD + HF`, `T2D + HF`

**Hypertension Flag (1 + null):**
`HTN`, *null* → after null replacement: `HTN`, `UNKNOWN_HF` (NBRx) or `UNKNOWN_HP` (NRx/TRx)

**Gender (3):**
`F`, `M`, `U`

**Product Group (74 + null):** Based on v4 mapping (`Kerendia_Market_Basket_Product_Group_Mapping_and_Priority_v4.csv`).
The following 74 groups produce pivot features (plus `UNKNOWN_PG` for null):

*P1 (SGLT2i):* `CANAGLIFLOZIN_INVOKANA COMBOS`, `DAPAGLIFLOZIN_FARXIGA COMBOS`,
`EMPAGLIFLOZIN_JARDIANCE COMBOS`, `ERTUGLIFLOZIN_STEGLATRO COMBOS`, `FARXIGA BRAND`,
`FARXIGA GENERICS`, `INPEFA`, `INVOKANA`, `JARDIANCE`, `KERENDIA`, `STEGLATRO`

*P2 (GLP-1 / specialty):* `BYDUREON`, `BYETTA`, `JANUVIA`, `MOUNJARO`, `OZEMPIC`,
`REZVOGLAR KWIKPEN`, `RYBELSUS`, `SAXENDA`, `SOLIQUA`, `T1D DISEASE-MODIFYING`,
`TRULICITY`, `VICTOZA`, `WEGOVY`, `XULTOPHY`

*P3 (RAAS / HF / CKD supportive):* `ACE INHIBITORS AND COMBOS`,
`ANGIOTENSIN II RECEPTOR ANTAGONISTS AND COMBOS`, `CARDIAC GLYCOSIDES`,
`CARDIAC MYOSIN ACTIVATORS`, `ENTRESTO`, `HF RATE CONTROL`, `HF VASODILATORS`,
`IRON DEFICIENCY DRUG`, `VITAMIN D ANALOG DRUG`

*P4 (MRA / diuretics / CKD renal / DPP-4 / meglitinide):* `ACARBOSE`,
`ALISKIREN HEMIFUM`, `BRENZAVVY`, `CALCIMIMETICS`, `CKD SYMPTOM MGMT`,
`ERYTHROPOIESIS STIMULATING AGENTS`, `GLUCAGON RESCUE`, `K-SPARING DIURETICS`,
`LOOP DIURETICS`, `MINERALOCORTICOID RECEPTOR ANTAGONISTS`, `NESINA`, `ONGLYZA`,
`PHOSPHATE BINDERS`, `PRANDIN`, `SAXAGLIPTIN HYDROCHLORIDE`,
`SAXAGLIPTIN_ONGLYZA COMBOS`, `STARLIX`, `THIAZIDE DIURETICS`, `TRADJENTA`,
`ZITUVIMET`, `ZITUVIO`

*P5 (beta blockers / SUs / TZDs / older agents):* `ALOGLIPTIN_NESINA COMBOS`,
`BETA BLOCKERS AND COMBOS`, `GLIMEPIRIDE`, `GLIPIZIDE`, `GLIPIZIDE COMBOS`,
`GLYBURIDE`, `GLYBURIDE COMBOS`, `PRANDIN_METFORMIN COMBOS`, `VERQUVO`

*P6 (insulin / CGM / metformin / devices):* `BASAL (LONG-ACTING) INSULIN`,
`CGM AND SUPPLIES`, `CKD SUPPORTIVE`, `INSULIN DELIVERY DEVICES`, `METFORMIN`,
`PRE-MIXED INSULIN`, `RAPID-ACTING INSULIN`, `SHORT-ACTING HUMAN INSULIN`,
`SYMLINPEN`, `ZEPBOUND`

**Groups removed from v3 (11 groups dropped in v4):**
`ACTOS`, `ADLYXIN`, `BEXAGLIFLOZIN`, `CALCIUM CHANNEL BLOCKERS AND COMBOS`,
`CYCLOSET`, `DIURETICS AND COMBOS` (split into LOOP/THIAZIDE/K-SPARING),
`INSULIN GLAR M SOL`, `MIGLITOL`, `OTHERS` (decomposed into dedicated groups),
`PIOGLITAZONE_ACTOS COMBOS`, `SULFONYLUREAS`, `TEKTURNA`

**Groups added in v4 (13 new groups):** `CALCIMIMETICS`, `CARDIAC GLYCOSIDES`,
`CARDIAC MYOSIN ACTIVATORS`, `CKD SUPPORTIVE`, `CKD SYMPTOM MGMT`,
`GLUCAGON RESCUE`, `HF RATE CONTROL`, `HF VASODILATORS`,
`INSULIN DELIVERY DEVICES`, `K-SPARING DIURETICS`, `LOOP DIURETICS`,
`T1D DISEASE-MODIFYING`, `THIAZIDE DIURETICS`

**Mapping file:** `/Users/sehar.aejaz.ext@bayer.com/kerendia_nba_3_1_develop/NBA 3.1 - Dev/Product_Group_Mapping/Kerendia_Market_Basket_Product_Group_Mapping_and_Priority_v4.csv`

**Switch From (~74 + null) / Add On To (~74 + null):** Cardinality tracks Product Group
but may differ slightly because not all products appear in switch-from or add-on-to contexts.
These represent the drug the patient switched from or added Kerendia on top of, respectively.

### 6.3 Cardinality Drift Detection

The cardinalities above reflect the v4 mapping (NBA 3.1, T1D + HF expansion). If the pivot
produces significantly more or fewer columns than expected, check for:
- Upstream V6 pipeline not yet updated with v4 mapping — the LAAD pipeline at
  `/Users/wenjie.chen@bayer.com/kerendia_data_needs/LAAD based LRx Pipeline/` must be
  re-run with the updated mapping file before these cardinalities take effect
- New products entering the IQVIA market basket (Product Group, Switch From, Add On To)
- Changes in IQVIA's indication grouping logic (Indication Group)
- New specialty categories being added by IQVIA (Specialty Group)

**Important:** The v4 mapping eliminates the `OTHERS` catch-all group and the
`DIURETICS AND COMBOS` aggregate group. If V6 still contains these values (pipeline not
yet updated), the notebooks will produce pivot columns for the old group names. Ensure
the upstream pipeline has been re-run with the v4 mapping before generating features.

---

## 7. Lag Windows

### 7.1 Active Windows

```python
last_i_month_list = [1, 3, 6, 12]
```

These produce two types of output columns per base feature:

| Output Type | Naming Pattern | Window Frame |
| --- | --- | --- |
| Rolling sum | `{base_feature}_IN_LAST_{i}_MONTH` | `rowsBetween(-(i-1), 0)` — inclusive of current month |
| Cumulative total | `RUNNING_{base_feature}` | `rowsBetween(unboundedPreceding, currentRow)` |

### 7.2 Eliminated Windows (NBA 2.3)

18-month and 24-month lag windows were eliminated in the NBA 2.3 enhancement due to
data unavailability. The original list was `[1, 3, 6, 12, 18, 24]`. The code comments
preserve this history:

```python
# UPDATE - 2024-05-20 NBA 2.3 ENHANCEMENT
# FEATURES BEING CREATED WITH 12 MONTH LAG ONLY, 18, 24 MONTH LAG FEATURES
# HAVE BEEN ELIMINATED DUE TO DATA UNAVAILABILITY
# last_i_month_list = [1, 3, 6, 12, 18, 24]
last_i_month_list = [1, 3, 6, 12]
```

Do NOT re-add 18/24-month windows without confirming sufficient historical data coverage.

---

## 8. Output Column Naming Convention

### 8.1 Base Feature Naming

Before lag computation, each pivoted column follows:
```
TOTAL_HCP_{METRIC}_CLAIMS_{DIMENSION_PREFIX}_{SANITIZED_VALUE}
```

Where:
- `{METRIC}` = `NBRX`, `NRX`, or `TRX`
- `{DIMENSION_PREFIX}` = dimension-specific prefix (see Section 6.1)
- `{SANITIZED_VALUE}` = dimension value after the sanitization chain

### 8.2 Sanitization Chain

Applied to every pivot value before it becomes a column name suffix:

```python
c.replace(", ", " ")
 .replace("+", "and")      # or "above" for AGE_GROUP 65+
 .replace("/", " or ")
 .replace("-", "_")
 .replace(" ", "_")
 .replace("__", "_")
 .replace("(", "")
 .replace(")", "")
 .replace("&", "")
 .upper()
```

**Special cases for Age Group:**
- `65+`  → `.replace("+", "above")` → `65ABOVE`
- `<18`  → `.replace("<", "LESS_THAN_")` → `LESS_THAN_18`

Both required. Without the `<` rule, the `<18` bucket makes an invalid column name.

The originals also contain a dead `.replace("<", "GREATER_THAN_")` call immediately
after the `LESS_THAN_` replacement (a copy-paste bug — should have been `>` not `<`).
It has no effect because all `<` chars are already consumed by the first replacement.
Reproduce it for byte-level fidelity with the originals.

### 8.3 Lag Feature Naming

After `step3_lag`, the base feature columns are dropped and replaced by:

| Type | Pattern | Example (NBRx, Product Group, Kerendia, 3-month) |
| --- | --- | --- |
| Rolling sum | `{base}_IN_LAST_{i}_MONTH` | `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_3_MONTH` |
| Running total | `RUNNING_{base}` | `RUNNING_TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA` |

### 8.4 Examples Across All Three Metrics

| Metric | Dimension | Value | 6-Month Lag Column |
| --- | --- | --- | --- |
| NBRx | Product Group | KERENDIA | `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_6_MONTH` |
| NRx | Specialty | NEPHROLOGY | `TOTAL_HCP_NRX_CLAIMS_SPEC_NEPHROLOGY_IN_LAST_6_MONTH` |
| TRx | Pay Type | MEDICARE PART D | `TOTAL_HCP_TRX_CLAIMS_PAY_TYPE_MEDICARE_PART_D_IN_LAST_6_MONTH` |
| NBRx | Indication | T2D + CKD | `TOTAL_HCP_NBRX_CLAIMS_INDICATION_GROUP_T2D_and_CKD_IN_LAST_6_MONTH` |
| TRx | SOB | Immediate Switch | `TOTAL_HCP_TRX_CLAIMS_SOB_IMMEDIATE_SWITCH_IN_LAST_6_MONTH` |
| NBRx | Age Group | 65+ | `TOTAL_HCP_NBRX_CLAIMS_AGE_GROUP_65ABOVE_IN_LAST_6_MONTH` |
| NRx | Age Group | 65+ | `TOTAL_HCP_NRX_CLAIMS_AGE_65ABOVE_IN_LAST_6_MONTH` |

Note the AGE_GROUP_ vs AGE_ inconsistency in the last two rows (see Section 4.2).

---

## 9. Performance Guidance

These notebooks process billions of rows through 11 pivot operations, a large provider cross-join,
and a window-function column explosion. The patterns below are drawn from the companion
skills and adapted for this pipeline's specific bottlenecks.

### 9.1 Pre-Aggregation Before Pivot (from generic-patient-features)

The V6 data is already pre-aggregated at the Provider × Week × Product × Demographics grain.
The notebooks further aggregate to Provider × Month × Dimension in each pivot step. This
two-stage aggregation (V6 upstream → monthly pivot in notebooks) is what makes the pipeline
feasible. Do NOT attempt to pivot on the raw LAAD claim-level data — it would produce a
cross-join orders of magnitude larger.

### 9.2 Cross-Join Cost in `step2_fill_missing`

The fill-missing step creates a cross-join of:
- Many distinct `PROVIDER_ID` values (HCP universe size)
- ~48 months (global min to max date range)
- = large intermediate result

This is then left-joined back to the spine. The cost is bounded by the provider count ×
month count, not by the original claim row count. Monitor this if the HCP universe grows
significantly.

### 9.3 Column Explosion in `step3_lag`

With high-cardinality dimensions (Product Group: 74, Switch From: ~74, Add On To: ~74),
the pivot step produces hundreds of base columns. `step3_lag` then multiplies each by 5
(4 lag windows + 1 running total). The total output column count can reach 1,000+.

**Mitigation:** The base columns are dropped after lag computation (see Step 7 of the
pipeline). Only lag and running-total columns are written to Delta.

### 9.4 Serverless Constraints

These notebooks run on serverless compute. Known constraints:

| Constraint | Impact | Workaround |
| --- | --- | --- |
| No `.cache()` / `.persist()` | Cannot materialize intermediate DataFrames | Use `.write.parquet()` for expensive intermediates if needed |
| `F.count("*")` fails in some contexts | Use `F.count(F.lit(1))` instead | Already not used in these notebooks (they use `F.sum()`) |
| RecursionError on deep plans | Chained `.withColumn()` in loops can exceed plan depth | Use batched `.withColumns({...})` (Python 3.10+ / Spark 3.4+) |
| Delta column name restrictions | ` ,;{}()\n\t=` are forbidden | The sanitization chain (Section 8.2) handles this |

### 9.5 Broadcast Joins for Small Dimensions

The HCP universe (single column, manageable size) is small enough to broadcast:
```python
hcp_universe = F.broadcast(hcp_universe)
hcp_lrx_claims = hcp_universe.join(hcp_lrx_claims, on="PROVIDER_ID", how="inner")
```

The current notebooks do NOT explicitly broadcast the HCP universe. Adding `F.broadcast()`
would improve performance by avoiding a shuffle join on the large claims table.

### 9.6 Column Sanitization for Delta Writes

The sanitization chain (Section 8.2) handles most special characters. However, if new
product names or dimension values contain characters outside the current replacement set,
Delta writes will fail with:
```
AnalysisException: Found invalid character(s) among ' ,;{}()\n\t=' in the column names
```

The generic-patient-features skill uses a regex-based `sanitize_column_name()` function
that is more robust:
```python
def sanitize_column_name(name):
    import re as _re
    name = _re.sub(r'[^A-Za-z0-9_]', '_', name.replace("+", "AND").replace("/", "_OR_"))
    name = _re.sub(r'_+', '_', name).strip('_')
    return name.upper()
```

Consider adopting this for future iterations of the LAAD Rx feature notebooks.

---

## 10. Common Pitfalls

### 10.1 Null vs Empty String in Dimension Columns

Some dimension columns contain both `null` and the string `'NULL'`. The notebooks handle
both:
```python
F.when(((col("COL").isNull()) | (col('COL') == 'NULL')), 'REPLACEMENT')
```

If the upstream V6 pipeline changes its null representation (e.g., to empty string `''`),
this filter will miss it. Check for empty strings if null counts look unexpectedly low.

### 10.2 Case Sensitivity in Filter Values

The `INDICATION_GROUP` cleanup explicitly matches `'ALL OTHERS'` (with space):
```python
F.when(col("INDICATION_GROUP") == "ALL OTHERS", "ALL_OTHERS")
```

This is case-sensitive. If the upstream source changes to `'All Others'` or `'all others'`,
the replacement will silently stop working and both `ALL_OTHERS` and `ALL OTHERS` will
appear as separate pivot values.

### 10.3 Column-Name Drift Between Skill and Production

The column names documented in this skill are based on the current V6 dimension values.
If IQVIA adds new products, indications, or specialty groups, the pivot will produce new
columns not listed here. This is expected behavior — the pivot is dynamic. The skill
documents the cardinalities for drift detection, not as a fixed schema.

### 10.4 `DISTINCT` in the Source Query

The source queries use `SELECT DISTINCT`. This deduplicates rows that are identical across
all 21 selected columns. If V6 contains true duplicates (same provider, same week, same
product, same demographics, same metric values), they will be collapsed. This is generally
safe because V6 is already pre-aggregated, but it means the notebooks cannot detect if
V6 has accidental duplicate rows.

### 10.5 `union` vs `unionByName`

NBRx uses `unionByName`, while NRx and TRx use `union`. Both work because the same SELECT
statement produces identical column order. If the old-data and new-data queries are ever
modified independently (e.g., adding a column to one but not the other), `union` will
silently misalign columns while `unionByName` will throw an error. Prefer `unionByName`.

### 10.6 The `SVC_DT_M >= '2023-01-01'` Filter

The post-lag filter discards all months before 2023-01-01. This is applied AFTER lag
computation, so the 12-month lag for January 2023 correctly includes data from
January–December 2022 (which is present in the old-data table). If the filter were
applied BEFORE lag computation, the first 11 months of lag features would be incomplete.

### 10.7 `step3_lag` Window Frame Includes Current Month

The window frame `rowsBetween(-i+1, 0)` includes the current row. This means
`_IN_LAST_1_MONTH` = current month's value (not the prior month's value). If the
business requirement changes to exclude the current month (true "lag"), the frame
would need to shift to `rowsBetween(-i, -1)`.

---

## 11. Helper Notebooks

### 11.0 Helper notebook paths (`%run`)

```
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config"
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_step23_function"
```

Wrong paths = notebooks won't run (`step2_fill_missing` / `step3_lag` come from
`00_step23_function`). As of NBA 3.1 these helpers have **not been migrated** — they
still live under the NBA 3.0 Ops Pipeline path shown above. If they are copied to a 3.1
location, update these paths.

**Note:** NBRx runs all three helpers. NRx and TRx run only `00_connection` and
`00_step23_function` (they skip `00_config`).

### 11.1 `00_connection`

Stable shared utility that sets up Snowflake connections and common imports. Referenced
by `%run` at the top of each notebook. Not detailed here — treat as a black-box
infrastructure dependency.

### 11.2 `00_config`

Sets up cohort parameters, file paths, and lookback/prediction dates. The LAAD Rx feature
notebooks read the anchor dates CSV from this config:
```python
cohort_anchor_date = spark.read.csv(
    ".../hcp_model_inference_anchor_dates.csv",
    header=True, inferSchema=True
)
LOOKBACK_START_DATE = cohort_anchor_date.filter(
    F.col("COHORT") == "I01"
).first()["LOOKBACK_START_DATE"]
```

Note: The LAAD Rx feature notebooks use the anchor dates CSV for date configuration but
do NOT use the cohort-based feature generation pattern from the patient-features skill.
They produce a flat `(PROVIDER_ID, SVC_DT_M)` output without cohort IDs.

### 11.3 `00_step23_function`

Contains `step2_fill_missing`, `step3_lag`, `step3_lag_avg`, and `step3_lag_distinct`.
The LAAD Rx feature notebooks use only `step2_fill_missing` and `step3_lag` (not the
avg or distinct variants). See Sections 5.6 and 5.7 for the full function code.

---

## 12. Verification Checklist

After running any of the three notebooks, verify:

| Check | Expected | How to Verify |
| --- | --- | --- |
| Output row count | HCP universe size × months since 2023-01 (post-2023 filter) | `df_feats.count()` |
| No null PROVIDER_ID | 0 | `df_feats.filter(col("PROVIDER_ID").isNull()).count()` |
| Column count is plausible | 500–1500+ (depends on pivot cardinality × 5 lag variants) | `len(df_feats.columns)` |
| PULL_DT is today's date | `YYYY_MM_DD` format | `df_feats.select("PULL_DT").distinct().show()` |
| SVC_DT_M range starts at 2023-01-01 | Min = 2023-01-01 | `df_feats.agg(F.min("SVC_DT_M")).show()` |
| KERENDIA product column exists | Non-null for providers who wrote Kerendia | Check `RUNNING_TOTAL_HCP_{METRIC}_CLAIMS_PRODUCT_GROUP_KERENDIA` |
| No forbidden characters in column names | All columns match `[A-Z0-9_]+` | `[c for c in df_feats.columns if not re.match(r'^[A-Z0-9_]+$', c)]` |