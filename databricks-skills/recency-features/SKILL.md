---
name: recency-features
description: >
  Guidance for understanding and exploring Recency patient features in the Kerendia NBA 3.x
  pipeline. Read this skill when the user asks about recency features, how recently events occurred,
  event counts over time windows, skewness, the recency class, or the _rec_&_first_occ notebooks
  (Section B2). Covers RX, DX, PX, and Lab claim types.
---

# Recency Features — Patient-Level Feature Engineering

Recency features capture **how recently and how frequently** events occurred in a patient's journey
during the **12-month lookback period**. Unlike First Occurrence (which uses the full lookback),
Recency is scoped to the 12M window between `LOOKBACK_START_DATE` and `LOOKBACK_END_DATE`.

As per your instructions, these features feed the BERT Transformer model trained on Kerendia Drug
Events for Masked Event Prediction, Next Event Prediction, and Shuffled Order correction.

## What Recency Measures

The `recency` class produces **6 sub-feature types**, all joined on `HCP_COHORT_ID`:

| # | Sub-Feature | Method | Output Columns | Description |
| --- | --- | --- | --- | --- |
| 1 | **Most Recent Event** | `aggregate_min_event_time()` | `min(EVENT_TIME)_{EVENT_NAME}_time_min` | `min(EVENT_TIME)` = fewest days before anchor = most recent occurrence |
| 2 | **Total & Unique Events** | `calculate_event_counts()` | `total_events`, `unique_events` | Overall event volume per HCP-Cohort |
| 3 | **Event Counts by Time Window** | `calculate_event_counts_for_time_windows()` | `total_events_time_{N}_days`, `unique_events_time_{N}_days` | Events within last N days (N from `time_windows`) |
| 4 | **Event Counts by Type** | `calculate_event_counts_by_type()` | `total_{type}`, `unique_{type}` | Counts per event type (rx, px, dx, lab_data) |
| 5 | **Event Counts by Type × Window** | `calculate_event_counts_by_type_and_window()` | `total_events_time_{N}_days_{type}`, `unique_events_time_{N}_days_{type}` | Cross of time windows × event types |
| 6 | **Skewness** | `skewness()` | `skewness_time_{N}_days_{type}` | Concentration of events within time windows per type |

**`time_windows`** (from config): `[30, 60, 90, 180, 270, 360]`

---

## Data Pipeline Flow

```
Delta Input Claims (same as First Occurrence)
      │
      ▼
  DataFrameMerger.merge_all()  ← Standardizes columns, generates HCP_COHORT_ID
      │
      ▼
  Add EVENT_TIME = DATEDIFF(LOOKBACK_END_DATE, EVENT_DATE)
  Filter EVENT_TIME >= 0
      │
      ▼
  ┌────────────────────────────────────────────┐
  │  ** 12M FILTER (Recency-specific) **        │
  │  EVENT_DATE >= LOOKBACK_START_DATE           │
  │  EVENT_DATE <= LOOKBACK_END_DATE             │
  └────────────────────────────────────────────┘
      │
      ▼
  DataFrameBatchProcessor.batch_creation_by_type()  ← Re-batched after 12M filter
      │
      ▼
  recency(spark, batch, ..., time_windows)
    .recency_features()   ← Joins all 6 sub-features
      │
      ▼
  unionByName(allowMissingColumns=True)  ← Merge batches
      │
      ▼
  Write Delta to .../notebook_output/{claim}_recency_features
```

**Key difference from First Occurrence:** The claims are **re-filtered** to the 12M lookback
window and then **re-batched** before computing recency. First Occurrence uses the full
lookback (all events where `EVENT_TIME >= 0`).

---

## The `recency` Class (`00_recency_features`)

**Constructor:**
```python
recency_obj = recency(
    spark, batch,
    'HCP_COHORT_ID',   # patient_id_col
    'EVENT_NAME',      # event_name_col
    'EVENT_TIME',      # event_time_col
    'EVENT_TYPE',      # event_type_col
    time_windows       # [30, 60, 90, 180, 270, 360]
)
result_df = recency_obj.recency_features()
```

### Method Details

**1. `aggregate_min_event_time()`**
```python
# Core: min(EVENT_TIME) = most recent event (fewest days before anchor)
claims_data.groupBy(patient_id_col).pivot(event_name_col).agg({event_time_col: "min"})
# Output columns: min(EVENT_TIME)_{EVENT_NAME}_time_min
```

**2. `calculate_event_counts()`**
```python
claims_data.groupBy(patient_id_col).agg(
    count(event_name_col).alias("total_events"),
    countDistinct(event_name_col).alias("unique_events")
)
```

**3. `calculate_event_counts_for_time_windows()`**
```python
# For each window in [30, 60, 90, 180, 270, 360]:
claims_data.filter(event_time_col <= window_size).groupBy(patient_id_col).agg(
    count(event_name_col).alias(f"total_events_time_{window_size}_days"),
    countDistinct(event_name_col).alias(f"unique_events_time_{window_size}_days")
)
```

**4. `calculate_event_counts_by_type()`**
```python
# For each event_type in ['rx', 'px', 'dx', 'lab_data']:
claims_data.filter(event_type_col == event).groupBy(patient_id_col).agg(
    count(event_name_col).alias(f"total_{event}"),
    countDistinct(event_name_col).alias(f"unique_{event}")
)
```

**5. `calculate_event_counts_by_type_and_window()`**
```python
# Cross of event_types × time_windows:
claims_data.filter((event_time_col <= window) & (event_type_col == event)).groupBy(patient_id_col).agg(
    count(event_name_col).alias(f"total_events_time_{window}_days_{event}"),
    countDistinct(event_name_col).alias(f"unique_events_time_{window}_days_{event}")
)
```

**6. `skewness()`**
```python
# For each event_type × time_window:
subset.groupBy(patient_id_col).agg(
    skewness(event_time_col).alias(f"skewness_time_{window}_days_{event}")
)
```

**7. `recency_features()`** — Orchestrator that left-joins all 6 sub-features on `patient_id_col`.

---

## Per-Claim-Type Details

| Claim | Notebook | ID | Section | 12M Filter Cell | Recency Cells | Output Delta Path |
| --- | --- | --- | --- | --- | --- | --- |
| RX | `01_rx_features_rec_&_first_occ` | 2494728515032398 | B2 | Cell 27 | Cells 26–32 | `rx_recency_features` |
| DX | `02_dx_features_rec_&_first_occ` | 2494728515032399 | B2 | Cell 26 | Cells 25–31 | `dx_recency_features` |
| PX | `03_px_features_rec_&_first_occ` | 2494728515032400 | B2 | Cell 26 | Cells 25–31 | `px_recency_features` |
| Lab | `04_lab_features_rec_&_first_occ` | 2494728515032401 | B2 | Cell 26 | Cells 25–31 | `lab_recency_features` |

All output paths under: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/`

### The 12M Filter (unique to Recency)

Applied in each notebook before re-batching:
```python
{claim}_claims_last_12_months_filtered = {claim}_claims_loaded.filter(
    (col("EVENT_DATE") >= col("LOOKBACK_START_DATE")) &
    (col("EVENT_DATE") <= col("LOOKBACK_END_DATE"))
)
```

---

## Feature Volume Estimate

Each claim type generates a large number of features:

| Component | Formula | Typical Count |
| --- | --- | --- |
| Most Recent Event | 1 column per EVENT_NAME | ~29 (RX), ~17 (DX), ~5 (PX), ~2 (Lab) |
| Total/Unique Events | 2 columns | 2 |
| Time Window Counts | 2 × len(time_windows) | 12 |
| Type Counts | 2 × 4 event types | 8 |
| Type × Window | 2 × 4 × len(time_windows) | 48 |
| Skewness | 4 × len(time_windows) | 24 |
| **Total (non-ID)** | Sum | **~94 + EVENT_NAMEs** |

---

## Key Differences: Recency vs First Occurrence

| Aspect | Recency | First Occurrence |
| --- | --- | --- |
| **Lookback scope** | 12M only (LOOKBACK_START → LOOKBACK_END) | Full lookback (EVENT_TIME >= 0) |
| **Data re-filtering** | Yes — 12M filter applied, then re-batched | No — uses data as-is |
| **Core aggregation** | `min(EVENT_TIME)` = most recent | `max(EVENT_TIME)` = first ever |
| **Feature count** | ∼94 + per-event columns | 1 per event |
| **Sub-features** | 6 types (recency, counts, skewness) | 1 type (first occ timing) |
| **Time windows** | `[30, 60, 90, 180, 270, 360]` | None |
| **Helper module** | `00_recency_features` | `00_first_occurrence_features` |
| **Section in notebook** | B2 (cells 25–31) | B1 (cells 18–22) |

---

## Common EDA Patterns

### 1. Feature Shape & Column Categories
```python
df = spark.read.format("delta").load(".../rx_recency_features")
time_min_cols = [c for c in df.columns if c.endswith("_time_min")]
skewness_cols = [c for c in df.columns if c.startswith("skewness_")]
event_count_cols = [c for c in df.columns if c.startswith("total_events_time_") or c.startswith("unique_events_time_")]
print(f"Recency columns: {len(time_min_cols)}, Skewness: {len(skewness_cols)}, Event counts: {len(event_count_cols)}")
```

### 2. Most Recent Event Distribution
```python
# When was the most recent Kerendia Rx? (lower = more recent)
df.select("min(EVENT_TIME)_KERENDIA_time_min").summary().show()
```

### 3. Event Volume Across Time Windows
```python
df.select(
    "total_events_time_30_days", "total_events_time_90_days",
    "total_events_time_180_days", "total_events_time_360_days"
).summary().show()
```

---

## Notebook References

**Feature notebooks (Section B2):**
* [01_rx_features_rec_&_first_occ](/editor/notebooks/2494728515032398) — RX recency (cells 26–32)
* [02_dx_features_rec_&_first_occ](/editor/notebooks/2494728515032399) — DX recency (cells 25–31)
* [03_px_features_rec_&_first_occ](/editor/notebooks/2494728515032400) — PX recency (cells 25–31)
* [04_lab_features_rec_&_first_occ](/editor/notebooks/2494728515032401) — Lab recency (cells 25–31)

**Helper notebooks:**
* [00_recency_features](/editor/notebooks/3340972492350424) — `recency` class (6 sub-feature methods)
* [00_batch_processing](/editor/notebooks/3340972492350405) — `DataFrameBatchProcessor` class
* [00_load_processed_data](/editor/notebooks/2494728515032293) — `DataFrameMerger` class
* [00_config](/editor/notebooks/2494728515032290) — Date params, file paths, `time_windows`
