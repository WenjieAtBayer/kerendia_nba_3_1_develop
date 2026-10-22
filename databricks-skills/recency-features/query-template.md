# Recency Features — Query & Exploration Template

All recency features are **pre-materialized as Delta tables** under the notebook_output volume.
These are PySpark DataFrames — read them directly with `spark.read`.

## Reading Pre-Materialized Outputs

```python
BASE = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output"

rx_recency  = spark.read.format("delta").load(f"{BASE}/rx_recency_features")
dx_recency  = spark.read.format("delta").load(f"{BASE}/dx_recency_features")
px_recency  = spark.read.format("delta").load(f"{BASE}/px_recency_features")
lab_recency = spark.read.format("delta").load(f"{BASE}/lab_recency_features")

for name, df in [("RX", rx_recency), ("DX", dx_recency), ("PX", px_recency), ("Lab", lab_recency)]:
    print(f"{name}: {df.count():,} rows, {len(df.columns)} cols")
```

## Understanding the Schema

**Key column:** `HCP_COHORT_ID` — format: `{PROVIDER_ID}_{COHORT}` (e.g., `PRV123_I01`)

**Feature column naming conventions:**

| Prefix/Pattern | Sub-Feature | Example |
| --- | --- | --- |
| `min(EVENT_TIME)_{EVENT}_time_min` | Most recent event | `min(EVENT_TIME)_KERENDIA_time_min` |
| `total_events` | Total event count | `total_events` |
| `unique_events` | Unique event count | `unique_events` |
| `total_events_time_{N}_days` | Event count in last N days | `total_events_time_30_days` |
| `unique_events_time_{N}_days` | Unique events in last N days | `unique_events_time_90_days` |
| `total_{type}` | Count by event type | `total_rx`, `total_dx` |
| `unique_{type}` | Unique by event type | `unique_px`, `unique_lab_data` |
| `total_events_time_{N}_days_{type}` | Type × window count | `total_events_time_30_days_rx` |
| `unique_events_time_{N}_days_{type}` | Type × window unique | `unique_events_time_180_days_dx` |
| `skewness_time_{N}_days_{type}` | Skewness per type × window | `skewness_time_90_days_rx` |

Where `N` ∈ `{30, 60, 90, 180, 270, 360}` and `type` ∈ `{rx, px, dx, lab_data}`.

```python
# Categorize all feature columns
def categorize_recency_columns(df):
    cols = df.columns
    categories = {
        "recency_time_min": [c for c in cols if c.endswith("_time_min")],
        "total_unique_overall": [c for c in cols if c in ("total_events", "unique_events")],
        "time_window_counts": [c for c in cols if "events_time_" in c and not any(t in c for t in ["_rx", "_px", "_dx", "_lab_data"])],
        "type_counts": [c for c in cols if c.startswith(("total_rx", "total_px", "total_dx", "total_lab", "unique_rx", "unique_px", "unique_dx", "unique_lab"))],
        "type_window_counts": [c for c in cols if "events_time_" in c and any(t in c for t in ["_rx", "_px", "_dx", "_lab_data"])],
        "skewness": [c for c in cols if c.startswith("skewness_")],
    }
    for cat, col_list in categories.items():
        print(f"{cat}: {len(col_list)} columns")
    return categories

cats = categorize_recency_columns(rx_recency)
```

## Regenerating Recency Features (if needed)

**Only use this if you need to regenerate. Prefer pre-materialized Delta outputs.**

```python
# Cell 1–3 — Same setup as First Occurrence (connection, config, load_processed_data)
%run ".../00_connection"
%run ".../00_config"
%run ".../00_load_processed_data"
```

```python
# Cell 4 — DataFrameMerger (RX example)
# Same as First Occurrence — see first-occurrence-features/query-template.md
```

```python
# Cell 5 — Extract + EVENT_TIME (same as First Occurrence)
rx_claims_loaded = claims_data["rx_from_claims"]
rx_claims_loaded = rx_claims_loaded.withColumn(
    "EVENT_TIME", datediff(rx_claims_loaded["LOOKBACK_END_DATE"], rx_claims_loaded["EVENT_DATE"])
)
rx_claims_loaded = rx_claims_loaded.filter(col("EVENT_TIME") >= 0)
```

```python
# Cell 6 — ** RECENCY-SPECIFIC: 12M Filter **
rx_claims_last_12_months_filtered = rx_claims_loaded.filter(
    (col("EVENT_DATE") >= col("LOOKBACK_START_DATE")) &
    (col("EVENT_DATE") <= col("LOOKBACK_END_DATE"))
)
```

```python
# Cell 7 — Re-batch after 12M filter
%run ".../00_batch_processing"

processor = DataFrameBatchProcessor(spark)
batch_list_rx = processor.batch_creation_by_type(rx_claims_last_12_months_filtered)
print(f"# of Batches: {len(batch_list_rx)}")
```

```python
# Cell 8 — Recency feature generation
%run ".../00_recency_features"

recency_batches = []
for i, batch in enumerate(batch_list_rx):
    if not batch.isEmpty():
        recency_obj = recency(
            spark, batch,
            'HCP_COHORT_ID', 'EVENT_NAME', 'EVENT_TIME', 'EVENT_TYPE',
            time_windows  # [30, 60, 90, 180, 270, 360] from config
        )
        result = recency_obj.recency_features()
        recency_batches.append(result)
        print(f"Batch {i+1}: {result.count()} HCP-Cohorts")
        del result
        gc.collect()
```

```python
# Cell 9 — Union all batches
rx_recency_df = recency_batches[0]
for df in recency_batches[1:]:
    rx_recency_df = rx_recency_df.unionByName(df, allowMissingColumns=True)

print(f"Shape: {rx_recency_df.count()} rows, {len(rx_recency_df.columns)} cols")
```

```python
# Cell 10 — Save
rx_recency_df.write.format("delta").mode("overwrite").save(
    f"{BASE}/rx_recency_features"
)
```

## Adapting for Other Claim Types

| Variable | RX | DX | PX | Lab |
| --- | --- | --- | --- | --- |
| Non-blank file path | `rx1_file_path` | `dx1_file_path` | `px1_file_path` | `lab_data1_file_path` |
| Config column vars | `claims_id_rx`, etc. | `claims_id_dx`, etc. | `claims_id_px`, etc. | `claims_id_lab`, etc. |
| Dict key | `rx_from_claims` | `dx_from_claims` | `px_from_claims` | `lab_data_from_claims` |
| Output name | `rx_recency_features` | `dx_recency_features` | `px_recency_features` | `lab_recency_features` |

## EDA Patterns

### Pattern 1: Most Recent Event Across Drugs

```python
from pyspark.sql.functions import avg, col

recency_cols = [c for c in rx_recency.columns if c.endswith("_time_min")]
rx_recency.select([
    avg(col(c)).alias(c.replace("min(EVENT_TIME)_", "").replace("_time_min", ""))
    for c in recency_cols
]).show(vertical=True, truncate=False)
```

### Pattern 2: Event Volume Over Time Windows

```python
# Compare total events in 30d vs 90d vs 180d vs 360d
rx_recency.select(
    avg("total_events_time_30_days").alias("avg_30d"),
    avg("total_events_time_90_days").alias("avg_90d"),
    avg("total_events_time_180_days").alias("avg_180d"),
    avg("total_events_time_360_days").alias("avg_360d"),
).show()
```

### Pattern 3: Skewness Analysis

```python
# Are events concentrated in recent time for RX?
skew_cols = [c for c in rx_recency.columns if c.startswith("skewness_") and c.endswith("_rx")]
rx_recency.select([avg(col(c)).alias(c) for c in skew_cols]).show(vertical=True)
```

### Pattern 4: Cross-Claim Recency Comparison

```python
# Join RX and DX recency on HCP_COHORT_ID, compare most recent events
joined = rx_recency.select("HCP_COHORT_ID", "total_events", "unique_events") \
    .withColumnRenamed("total_events", "rx_total") \
    .withColumnRenamed("unique_events", "rx_unique") \
    .join(
        dx_recency.select("HCP_COHORT_ID", "total_events", "unique_events")
            .withColumnRenamed("total_events", "dx_total")
            .withColumnRenamed("unique_events", "dx_unique"),
        on="HCP_COHORT_ID", how="inner"
    )
joined.select(avg("rx_total"), avg("dx_total"), avg("rx_unique"), avg("dx_unique")).show()
```

### Pattern 5: Patients With High Recent Activity

```python
# Top 20 HCP-Cohorts by total events in last 30 days
rx_recency.orderBy(col("total_events_time_30_days").desc()).select(
    "HCP_COHORT_ID", "total_events_time_30_days", "unique_events_time_30_days", "total_events"
).limit(20).show(truncate=False)
```

## Important Constraints

1. **Pre-materialized Delta is preferred** — regenerating requires the full DataFrameMerger + batch + recency pipeline.
2. **12M filter is critical** — Recency ONLY looks at events within `LOOKBACK_START_DATE` to `LOOKBACK_END_DATE` (typically 365 days). This is applied AFTER `EVENT_TIME >= 0` but BEFORE batching.
3. **min(EVENT_TIME) = most recent** — opposite of First Occurrence where `max(EVENT_TIME)` = first ever. Lower value = more recent event.
4. **`time_windows` from config** — `[30, 60, 90, 180, 270, 360]`. If config changes, feature column names change.
5. **Type counts include all 4 types** (rx, px, dx, lab_data) even in single-claim notebooks — most will be NULL since only one claim type is loaded.
6. **Skewness can be NULL** when fewer than 3 events exist in a time window (PySpark skewness requires ≥3 values).
7. **allowMissingColumns=True** is critical during batch union — different batches may have different event-specific columns.
