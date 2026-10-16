# Frequency Features — Query & Exploration Template

All frequency features are **pre-materialized** under the notebook_output volume.
All are Delta format except Lab lag frequency (Parquet).

## Reading Pre-Materialized Outputs

```python
BASE = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output"

# Sub-type A: Claim Counts (Delta)
rx_freq  = spark.read.format("delta").load(f"{BASE}/rx_frequency_features")
dx_freq  = spark.read.format("delta").load(f"{BASE}/dx_frequency_features")
px_freq  = spark.read.format("delta").load(f"{BASE}/px_frequency_features")
lab_freq = spark.read.format("delta").load(f"{BASE}/lab_data_frequency_features")

# Sub-type B: Lag Frequency
rx_lag  = spark.read.format("delta").load(f"{BASE}/rx_lag_frequency_features")
dx_lag  = spark.read.format("delta").load(f"{BASE}/dx_lag_frequency_features")
px_lag  = spark.read.format("delta").load(f"{BASE}/px_lag_frequency_features")
lab_lag = spark.read.parquet(f"{BASE}/lab_data_lag_frequency_features")  # NOTE: Parquet!

# Sub-type C: Change in Frequency (after dropping raw FREQ_* cols)
rx_change  = spark.read.format("delta").load(f"{BASE}/rx_change_frequency")
dx_change  = spark.read.format("delta").load(f"{BASE}/dx_change_frequency")
px_change  = spark.read.format("delta").load(f"{BASE}/px_change_frequency")
lab_change = spark.read.format("delta").load(f"{BASE}/lab_data_change_frequency")

# Sub-type C alt: Change + Lag combined (before drop)
rx_freq_change  = spark.read.format("delta").load(f"{BASE}/rx_freq_and_change_frequency")
dx_freq_change  = spark.read.format("delta").load(f"{BASE}/dx_freq_and_change_frequency")
px_freq_change  = spark.read.format("delta").load(f"{BASE}/px_freq_and_change_frequency")
lab_freq_change = spark.read.format("delta").load(f"{BASE}/lab_data_freq_and_change_frequency")

# Sub-type D: Unique Patient Counts
rx_pts  = spark.read.format("delta").load(f"{BASE}/rx_num_patients_features")
dx_pts  = spark.read.format("delta").load(f"{BASE}/dx_num_patients_features")
px_pts  = spark.read.format("delta").load(f"{BASE}/px_num_patients_features")
lab_pts = spark.read.format("delta").load(f"{BASE}/lab_data_num_patients_features")
```

```python
# Print shapes for all outputs
for name, df in [
    ("RX freq", rx_freq), ("DX freq", dx_freq), ("PX freq", px_freq), ("Lab freq", lab_freq),
    ("RX lag", rx_lag), ("DX lag", dx_lag), ("PX lag", px_lag), ("Lab lag", lab_lag),
    ("RX change", rx_change), ("DX change", dx_change), ("PX change", px_change), ("Lab change", lab_change),
    ("RX pts", rx_pts), ("DX pts", dx_pts), ("PX pts", px_pts), ("Lab pts", lab_pts),
]:
    print(f"{name}: {df.count():,} rows, {len(df.columns)} cols")
```

## Understanding the Schema

### Sub-type A & B: Monthly Grain
**Key columns:** `PROVIDER_ID`, `SVC_DT_M` (first of month)

```python
# List all event names from claim count features
event_cols = sorted([c for c in rx_freq.columns if c.startswith("FREQ_") and c not in ("PROVIDER_ID", "SVC_DT_M")])
print(f"RX has {len(event_cols)} event frequency columns:")
for c in event_cols:
    print(f"  {c}")
```

### Sub-type B: Lag Column Pattern
```python
# Lag columns follow: FREQ_{EVENT}_IN_LAST_{N}_MONTH where N in [1,2,3,6,12]
import re
lag_cols = [c for c in rx_lag.columns if re.match(r'FREQ_.*_IN_LAST_\d+_MONTH', c)]
print(f"RX has {len(lag_cols)} lag frequency columns")

# Extract unique event names from lag columns
pattern = r"FREQ_(.*)_IN_LAST_\d+_MONTH"
from collections import OrderedDict
event_names = list(OrderedDict.fromkeys(
    re.match(pattern, c).group(1) for c in lag_cols if re.match(pattern, c)
))
print(f"Covering {len(event_names)} events")
```

### Sub-type C: Change Frequency Column Pattern
```python
# Change columns: CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_{EVENT}_IN_LAST_{N}_MONTH (N in [1,2,3,6])
change_cols = [c for c in rx_change.columns if c.startswith("CHANGE_IN_FREQ_")]
print(f"RX has {len(change_cols)} change frequency columns")
```

### Sub-type D: Patient Count Grain
**Key columns:** `PROVIDER_ID`, `COHORT` (NOT SVC_DT_M)

```python
# Patient count columns: NUM_OF_PATIENTS_THE_HCP_{VERB}_{EVENT}_IN_LAST_{N}_DAYS
pt_cols = [c for c in rx_pts.columns if c.startswith("NUM_OF_PATIENTS_")]
print(f"RX has {len(pt_cols)} patient count columns")
```

## Regenerating Frequency Features (Sub-type A + B)

```python
# Cell 1–2: Setup
%run ".../00_connection"
%run ".../00_config"
```

```python
# Cell 3: Read claims (RX example)
rx_claims = spark.read.format("delta").load(rx1_file_path)
rx_claims = rx_claims.withColumn("SVC_DT_M", F.date_trunc('MM', col("SVC_DT")))
index_cols = ['PROVIDER_ID', 'SVC_DT_M']
```

```python
# Cell 4: Pivot for claim counts
freq_rx_claims = rx_claims.groupBy(index_cols).pivot("PRODUCT_GROUP").agg(F.count(F.lit(1)))

# Sanitize column names
freq_rx_claims = freq_rx_claims.select([
    expr(f"`{c}`").alias(
        'FREQ_' + c.replace(", ", " ").replace("+", "and").replace("/", " or ")
                   .replace("-", "_").replace(" ", "_").upper()
    ) if c not in index_cols else col(c)
    for c in freq_rx_claims.columns
])
```

```python
# Cell 5: Helper functions (defined inline — NOT from a shared module)
def step2_fill_missing(df, key_col, date_col):
    date_list_df = (
        df.select(date_col)
        .agg(F.min(date_col).alias('min_date'), F.max(date_col).alias('max_date'))
        .withColumn(date_col, F.explode(F.expr('sequence(min_date, max_date, interval 1 month)')))
        .drop("min_date", "max_date")
    )
    patient_id_list_df = df.select(key_col).distinct()
    spine = patient_id_list_df.crossJoin(date_list_df)
    features = [c for c in df.columns if c not in [key_col, date_col]]
    return spine.join(df, on=[key_col, date_col], how='left').fillna(0, subset=features)

def step3_lag(df, key_col, date_col, last_i_month_list):
    window_base = Window.partitionBy(key_col).orderBy(date_col)
    features = [c for c in df.columns if c not in [key_col, date_col]]
    last_i_month = [
        F.sum(c).over(window_base.rowsBetween(-i+1, 0)).alias(f"{c}_IN_LAST_{i}_MONTH")
        for i in last_i_month_list for c in features
    ]
    return df.select(key_col, date_col, *last_i_month)

def process_and_join(df, last_i_month_list):
    filled = step2_fill_missing(df, "PROVIDER_ID", "SVC_DT_M")
    lagged = step3_lag(filled, "PROVIDER_ID", "SVC_DT_M", last_i_month_list)
    keep_cols = ['PROVIDER_ID', 'SVC_DT_M'] + [c for c in lagged.columns if '_IN_LAST_' in c]
    return lagged.select(keep_cols)
```

```python
# Cell 6: Generate lag features
freq_features = freq_rx_claims.select(*freq_rx_claims.columns)
lag_freq_features = process_and_join(df=freq_rx_claims, last_i_month_list=[1, 2, 3, 6, 12])
```

```python
# Cell 7: Save
freq_features.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(
    f"{BASE}/rx_frequency_features")
lag_freq_features.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(
    f"{BASE}/rx_lag_frequency_features")
```

## Regenerating Change in Frequency (Sub-type C)

```python
# Requires lag_freq_features from Sub-type B + HCP universe + cohort dates
hcp_universe = spark.read.format("delta").load(hcp_universe_path).select('PROVIDER_ID').distinct()
cohort_df = spark.createDataFrame(pd.read_csv(
    ".../query_output/hcp_model_inference_anchor_dates.csv"
))
cohort_df = cohort_df.withColumn("SVC_DT_M", F.trunc(cohort_df["LOOKBACK_END_DATE"], "MM"))
updated_cohort_df = cohort_df.select("SVC_DT_M", "COHORT")
hcp_universe = hcp_universe.crossJoin(updated_cohort_df)

# Filter lag_freq to HCP universe × cohort months
lag_freq_features = hcp_universe.select("PROVIDER_ID", "SVC_DT_M").distinct().join(
    lag_freq_features, on=["PROVIDER_ID", "SVC_DT_M"], how='inner'
)

# Compute change
recent_windows = [1, 2, 3, 6]
new_columns = []
for event in event_names:
    col_12 = F.col(f"FREQ_{event}_IN_LAST_12_MONTH")
    for N in recent_windows:
        col_N = F.col(f"FREQ_{event}_IN_LAST_{N}_MONTH")
        change_name = f"CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_{event}_IN_LAST_{N}_MONTH"
        change_expr = ((col_N / F.lit(N)) - ((col_12 - col_N) / F.lit(12 - N))).alias(change_name)
        new_columns.append(change_expr)

change_freq_features = lag_freq_features.select("PROVIDER_ID", "SVC_DT_M", *new_columns)
```

## Adapting for Other Claim Types

| Variable | RX | DX | PX | Lab |
| --- | --- | --- | --- | --- |
| Input path var | `rx1_file_path` | `dx1_file_path` | `px1_file_path` | `lab_data1_file_path` |
| Pivot column | `PRODUCT_GROUP` | `DIAGNOSIS_DESCRIPTION` | `PROCEDURE_DESCRIPTION` | `TEST_TYPE` |
| Output prefix | `rx_` | `dx_` | `px_` | `lab_data_` |
| Lag save format | Delta | Delta | Delta | **Parquet** |
| Patient count verb | `PRESCRIBED_WITH` | `DIAGNOSED_WITH` | `DID_PROCEDURE` | `DID_LAB_TEST` |

## EDA Patterns

### Pattern 1: Top Events by Claim Count

```python
from pyspark.sql.functions import sum as spark_sum

event_cols = [c for c in rx_freq.columns if c.startswith("FREQ_")]
totals = rx_freq.select([spark_sum(col(c)).alias(c) for c in event_cols])

# Transpose to sorted list
import pandas as pd
totals_pd = totals.toPandas().T.reset_index()
totals_pd.columns = ['event', 'total_claims']
totals_pd = totals_pd.sort_values('total_claims', ascending=False)
totals_pd.head(20)
```

### Pattern 2: Lag Frequency Trends for a Specific Drug

```python
# Kerendia lag frequency over time for a single HCP
sample_hcp = rx_lag.select("PROVIDER_ID").first()[0]
rx_lag.filter(col("PROVIDER_ID") == sample_hcp).select(
    "SVC_DT_M",
    "FREQ_KERENDIA_IN_LAST_1_MONTH",
    "FREQ_KERENDIA_IN_LAST_3_MONTH",
    "FREQ_KERENDIA_IN_LAST_6_MONTH",
    "FREQ_KERENDIA_IN_LAST_12_MONTH",
).orderBy("SVC_DT_M").show(24, truncate=False)
```

### Pattern 3: Change in Frequency Distribution

```python
# Which HCPs are accelerating Kerendia prescribing?
kerendia_change = "CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_KERENDIA_IN_LAST_3_MONTH"
if kerendia_change in rx_change.columns:
    rx_change.select(kerendia_change).summary().show()
    # Accelerating HCPs (positive change)
    accel = rx_change.filter(col(kerendia_change) > 0).count()
    decel = rx_change.filter(col(kerendia_change) < 0).count()
    print(f"Accelerating: {accel:,}, Decelerating: {decel:,}")
```

### Pattern 4: Unique Patient Counts Across Time Windows

```python
# Average patients per HCP for Kerendia across time windows
for w in [30, 60, 90, 180, 360]:
    col_name = f"NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_{w}_DAYS"
    if col_name in rx_pts.columns:
        avg_val = rx_pts.select(avg(col(col_name))).first()[0]
        print(f"  {w}d: {avg_val:.2f} avg patients")
```

### Pattern 5: Cross-Claim Frequency Summary

```python
# Compare total feature column counts across claim types
for name, df in [("RX", rx_freq), ("DX", dx_freq), ("PX", px_freq), ("Lab", lab_freq)]:
    event_cols = [c for c in df.columns if c.startswith("FREQ_")]
    print(f"{name}: {len(event_cols)} event columns, {df.count():,} rows")
```

## Important Constraints

1. **Grain differs from other feature types** — Frequency uses `PROVIDER_ID` × `SVC_DT_M` (monthly), NOT `HCP_COHORT_ID`. Sub-type D uses `PROVIDER_ID` × `COHORT`.
2. **Lab lag frequency is Parquet** — use `spark.read.parquet()`, not `spark.read.format("delta").load()`.
3. **Helper functions are inline** — `step2_fill_missing`, `step3_lag`, `process_and_join` are defined inside each notebook, NOT in a shared helper module.
4. **Change frequency formula baseline is 12M** — the `_IN_LAST_12_MONTH` column is always the reference. Recent windows `[1,2,3,6]` are compared against it.
5. **Two change frequency saves** — `_freq_and_change_frequency` (both) and `_change_frequency` (change only after dropping raw FREQ_* columns).
6. **Patient count time windows** differ from recency — `[30, 60, 90, 180, 360]` (no 270), vs recency's `[30, 60, 90, 180, 270, 360]`.
7. **Column sanitization** is applied — event names go through replace/upper before becoming column names.
8. **HCP universe cross-join** is required for Sub-types C and D — `hcp_universe_path` from config.
