# First Occurrence Features — Query & Exploration Template

All first occurrence features are **pre-materialized as Delta tables** under the notebook_output
volume. These are PySpark DataFrames — not Snowflake queries — so read them directly.

## Reading Pre-Materialized Outputs

```python
BASE = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output"

# All 4 claim types
rx_first_occ  = spark.read.format("delta").load(f"{BASE}/rx_first_occurrence_features")
dx_first_occ  = spark.read.format("delta").load(f"{BASE}/dx_first_occurrence_features")
px_first_occ  = spark.read.format("delta").load(f"{BASE}/px_first_occurrence_features")
lab_first_occ = spark.read.format("delta").load(f"{BASE}/lab_first_occurrence_features")

for name, df in [("RX", rx_first_occ), ("DX", dx_first_occ), ("PX", px_first_occ), ("Lab", lab_first_occ)]:
    print(f"{name}: {df.count():,} rows, {len(df.columns)} cols")
```

## Understanding the Schema

**Key column:** `HCP_COHORT_ID` — format: `{PROVIDER_ID}_{COHORT}` (e.g., `PRV123_I01`)

**Feature columns:** `max(EVENT_TIME)_{EVENT_NAME}_first_occurrence`
* Value = number of days between the first occurrence and the anchor date
* Higher value = earlier first occurrence (more days ago)
* NULL = event never occurred for this patient in the lookback period

```python
# List all first occurrence event columns for RX
event_cols = sorted([c for c in rx_first_occ.columns if c.endswith("_first_occurrence")])
print(f"RX has {len(event_cols)} event features:")
for c in event_cols:
    print(f"  {c}")
```

## Regenerating First Occurrence Features (if needed)

This is the canonical notebook pattern used in Section B1 of each `_rec_&_first_occ` notebook.
**Only use this if you need to regenerate — prefer reading pre-materialized Delta outputs.**

```python
# Cell 1 — Setup
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```

```python
# Cell 2 — Config
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config"
```

```python
# Cell 3 — Load processed data helper
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_load_processed_data"
```

```python
# Cell 4 — DataFrameMerger (RX example — blank out all non-RX paths)
dx1_file_path = ""
dx2_file_path = ""
px1_file_path = ""
px2_file_path = ""
lab_data1_file_path = ""
lab_data2_file_path = ""

data_merger = DataFrameMerger(
    rx1_file_path, rx2_file_path, px1_file_path, px2_file_path,
    dx1_file_path, dx2_file_path, lab_data1_file_path, lab_data2_file_path,
    cohort_start_date, cohort_end_date, months_increment,
    lookback_duration, prediction_duration,
    claims_id_rx, claims_patient_id_rx, claims_event_date_rx, claims_event_name_rx,
    event_prevalence
)
claims_data = data_merger.merge_all()
```

```python
# Cell 5 — Extract target claim type + compute EVENT_TIME
rx_claims_loaded = claims_data["rx_from_claims"]
rx_claims_loaded = rx_claims_loaded.withColumn(
    "EVENT_TIME", datediff(rx_claims_loaded["LOOKBACK_END_DATE"], rx_claims_loaded["EVENT_DATE"])
)
# No future data leakage
rx_claims_loaded = rx_claims_loaded.filter(col("EVENT_TIME") >= 0)
```

```python
# Cell 6 — Batch processing
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_batch_processing"

processor = DataFrameBatchProcessor(spark)
batch_list_rx = processor.batch_creation_by_type(rx_claims_loaded)
print(f"# of Batches created: {len(batch_list_rx)}")
```

```python
# Cell 7 — First Occurrence feature generation
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_first_occurrence_features"

first_occ_batches = []
for i, batch in enumerate(batch_list_rx):
    if not batch.isEmpty():
        first_occ = first_occurrence_of_event(
            spark, batch, 'HCP_COHORT_ID', 'EVENT_NAME', 'EVENT_TIME', 'EVENT_TYPE'
        )
        result = first_occ.aggregate_first_event_time()
        first_occ_batches.append(result)
        print(f"Batch {i+1}: {result.count()} HCP-Cohorts")
        del result
        gc.collect()
```

```python
# Cell 8 — Union all batches
rx_first_occ_df = first_occ_batches[0]
for df in first_occ_batches[1:]:
    rx_first_occ_df = rx_first_occ_df.unionByName(df, allowMissingColumns=True)

print(f"Shape: {rx_first_occ_df.count()} rows, {len(rx_first_occ_df.columns)} cols")
```

```python
# Cell 9 — Save
rx_first_occ_df.write.format("delta").mode("overwrite").save(
    "/Volumes/.../notebook_output/rx_first_occurrence_features"
)
```

## Adapting for Other Claim Types

To switch from RX to another claim type, change these variables:

| Variable | RX | DX | PX | Lab |
| --- | --- | --- | --- | --- |
| Non-blank file path | `rx1_file_path` | `dx1_file_path` | `px1_file_path` | `lab_data1_file_path` |
| Config column vars | `claims_id_rx`, etc. | `claims_id_dx`, etc. | `claims_id_px`, etc. | `claims_id_lab`, etc. |
| Dict key | `rx_from_claims` | `dx_from_claims` | `px_from_claims` | `lab_data_from_claims` |
| Output name | `rx_first_occurrence_features` | `dx_first_occurrence_features` | `px_first_occurrence_features` | `lab_first_occurrence_features` |

## EDA Patterns

### Pattern 1: Feature Shape & Column Inventory

```python
for name, path_suffix in [
    ("RX", "rx_first_occurrence_features"),
    ("DX", "dx_first_occurrence_features"),
    ("PX", "px_first_occurrence_features"),
    ("Lab", "lab_first_occurrence_features"),
]:
    df = spark.read.format("delta").load(f"{BASE}/{path_suffix}")
    event_cols = [c for c in df.columns if c.endswith("_first_occurrence")]
    print(f"{name}: {df.count():,} rows, {len(event_cols)} event features")
```

### Pattern 2: Summary Statistics for Key Events

```python
from pyspark.sql.functions import avg, stddev, min as spark_min, max as spark_max, count, when

key_cols = [
    "max(EVENT_TIME)_KERENDIA_first_occurrence",
    "max(EVENT_TIME)_FARXIGA_first_occurrence",
    "max(EVENT_TIME)_JARDIANCE_first_occurrence",
]
rx_first_occ.select([
    avg(c).alias(f"avg_{c.split('_')[1]}") for c in key_cols if c in rx_first_occ.columns
]).show()
```

### Pattern 3: Null Rate Analysis (events never seen)

```python
from pyspark.sql.functions import sum as spark_sum

total = rx_first_occ.count()
event_cols = [c for c in rx_first_occ.columns if c.endswith("_first_occurrence")]

null_rates = rx_first_occ.select([
    (spark_sum(when(col(c).isNull(), 1).otherwise(0)) / total * 100).alias(c.replace("max(EVENT_TIME)_", "").replace("_first_occurrence", ""))
    for c in event_cols
])
null_rates.show(vertical=True, truncate=False)
```

### Pattern 4: Cross-Claim First Event Timeline

```python
# For a single HCP_COHORT_ID, compare when events first appeared across claim types
sample_id = rx_first_occ.select("HCP_COHORT_ID").first()[0]

for name, df in [("RX", rx_first_occ), ("DX", dx_first_occ), ("PX", px_first_occ), ("Lab", lab_first_occ)]:
    row = df.filter(col("HCP_COHORT_ID") == sample_id)
    if row.count() > 0:
        print(f"\n{name} first occurrences:")
        row.show(vertical=True, truncate=False)
```

### Pattern 5: Patients Who Never Had an Event

```python
# Which HCP-Cohorts never had a Kerendia prescription?
kerendia_col = "max(EVENT_TIME)_KERENDIA_first_occurrence"
if kerendia_col in rx_first_occ.columns:
    never_kerendia = rx_first_occ.filter(col(kerendia_col).isNull()).count()
    total = rx_first_occ.count()
    print(f"Never prescribed Kerendia: {never_kerendia:,} / {total:,} ({never_kerendia/total*100:.1f}%)")
```

## Important Constraints

1. **Pre-materialized Delta is preferred** — regenerating requires running the full pipeline (DataFrameMerger + batch processing + first_occ computation), which is expensive.
2. **HCP_COHORT_ID is the grain** — not just PROVIDER_ID. One provider can appear in multiple cohorts (I01, I02, etc.).
3. **max(EVENT_TIME) = first occurrence** — this is counterintuitive. Higher EVENT_TIME means more days before the anchor = earlier event.
4. **NULL means never occurred** — the event was not present for this HCP-Cohort in the lookback period.
5. **allowMissingColumns=True** is critical during batch union — different batches may have different event columns because not all events appear in all cohorts.
6. **EVENT_TIME >= 0 filter** prevents future data leakage — events after the anchor date are excluded.
