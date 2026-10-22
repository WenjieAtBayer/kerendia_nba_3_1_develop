---
name: first-occurrence-features
description: >
  Guidance for understanding and exploring First Occurrence patient features in the Kerendia NBA 3.x
  pipeline. Read this skill when the user asks about first occurrence features, when an event first
  appeared in a patient's journey, the first_occurrence_of_event class, or the
  _rec_&_first_occ notebooks (Section B1). Covers RX, DX, PX, and Lab claim types.
---

# First Occurrence Features — Patient-Level Feature Engineering

First Occurrence features capture **when an event first appeared** in a patient's journey during
the lookback period. They answer: "How many days ago (from the anchor date) did this event
first happen for this patient?"

As per your instructions, these features feed the BERT Transformer model trained on Kerendia
Drug Events (Hospital visits, prescription claims, procedure codes, dialysis) for Masked Event
Prediction, Next Event Prediction, and Shuffled Order correction.

## What First Occurrence Measures

**Core metric:** `max(EVENT_TIME)` per `HCP_COHORT_ID` per `EVENT_NAME`.

Since `EVENT_TIME = DATEDIFF(LOOKBACK_END_DATE, EVENT_DATE)`, the **maximum** EVENT_TIME
corresponds to the **earliest** event (most days before the anchor). So `max(EVENT_TIME)` =
first occurrence in lookback.

**Example output column:** `max(EVENT_TIME)_KERENDIA_first_occurrence` = 287 means the patient's
first Kerendia prescription was 287 days before the anchor date.

---

## Data Pipeline Flow

```
Delta Input Claims
      │
      ▼
┌───────────────────────────────┐
│ DataFrameMerger.merge_all()  │  ← Standardizes columns, generates cohort anchor dates,
│   (00_load_processed_data)    │    creates HCP_COHORT_ID, applies event prevalence filter
└───────────────────────────────┘
      │
      ▼
  Add EVENT_TIME = DATEDIFF(LOOKBACK_END_DATE, EVENT_DATE)
  Filter EVENT_TIME >= 0  (no future data leakage)
      │
      ▼
┌───────────────────────────────┐
│ DataFrameBatchProcessor      │  ← Splits by COHORT suffix from HCP_COHORT_ID
│  .batch_creation_by_type()   │    Default batch_size=6 cohorts per batch
└───────────────────────────────┘
      │
      ▼
┌───────────────────────────────┐
│ first_occurrence_of_event    │  ← Per batch: groupBy(HCP_COHORT_ID)
│  .aggregate_first_event_time │    .pivot(EVENT_NAME).agg(max(EVENT_TIME))
└───────────────────────────────┘
      │
      ▼
  unionByName(allowMissingColumns=True)  ← Merge batches
      │
      ▼
  Write Delta to .../notebook_output/{claim}_first_occurrence_features
```

---

## Helper Modules

### 1. DataFrameMerger (`00_load_processed_data`)

**Constructor:**
```python
DataFrameMerger(
    rx1_file_path, rx2_file_path, px1_file_path, px2_file_path,
    dx1_file_path, dx2_file_path, lab_data1_file_path, lab_data2_file_path,
    cohort_start_date, cohort_end_date, months_increment,
    lookback_duration, prediction_duration,
    claims_id, claims_patient_id, claims_event_date, claims_event_name,
    event_prevalence
)
```

**Key behavior:**
* Generates anchor dates from `cohort_start_date` to `cohort_end_date` at `months_increment` intervals
* For each anchor: `LOOKBACK_END_DATE` = last day of month 2 months before anchor, `LOOKBACK_START_DATE` = LOOKBACK_END_DATE - lookback_duration days
* Creates `HCP_COHORT_ID` = `{PROVIDER_ID}_{COHORT}` where COHORT = `I01`, `I02`, etc.
* Standardizes all claim types to: `PROVIDER_ID`, `PATIENT_ID`, `EVENT_NAME`, `EVENT_DATE`, `EVENT_TYPE`
* Applies event prevalence filter (default 0% — keeps all events)
* Saves anchor dates CSV to `.../query_output/hcp_model_inference_anchor_dates.csv`

**Per-claim-type invocation pattern** (blanks out all non-target paths):
```python
# RX example:
data_merger = DataFrameMerger(
    rx1_file_path, rx2_file_path, "", "", "", "", "", "",  # only RX paths filled
    cohort_start_date, cohort_end_date, months_increment,
    lookback_duration, prediction_duration,
    claims_id_rx, claims_patient_id_rx, claims_event_date_rx, claims_event_name_rx,
    event_prevalence
)
claims_data = data_merger.merge_all()
rx_claims_loaded = claims_data["rx_from_claims"]
```

**Dict keys per claim type:**

| Claim | Dict Key |
| --- | --- |
| RX | `rx_from_claims` |
| DX | `dx_from_claims` |
| PX | `px_from_claims` |
| Lab | `lab_data_from_claims` |

### 2. DataFrameBatchProcessor (`00_batch_processing`)

```python
processor = DataFrameBatchProcessor(spark)
batch_list = processor.batch_creation_by_type(claims_loaded, batch_size=6)
```

* Extracts COHORT suffix from `HCP_COHORT_ID` using regex `_(C\d+)$`
* Groups distinct cohorts into batches of `batch_size` (default 6)
* Returns `list[DataFrame]` — each batch contains claims for a subset of cohorts

### 3. first_occurrence_of_event (`00_first_occurrence_features`)

```python
first_occ = first_occurrence_of_event(
    spark, batch,
    'HCP_COHORT_ID',   # patient_id_col
    'EVENT_NAME',      # event_name_col
    'EVENT_TIME',      # event_time_col
    'EVENT_TYPE'       # event_type_col
)
result_df = first_occ.aggregate_first_event_time()
```

**Internal logic:**
```python
# Core transformation:
df = claims_data.groupBy(patient_id_col) \
    .pivot(event_name_col) \
    .agg({event_time_col: "max"})

# Column renaming: add "_first_occurrence" suffix to all non-ID columns
selected_columns = [col(patient_id_col)] + [
    col(c).alias(f"{c}_first_occurrence") for c in df.columns if c != patient_id_col
]
```

**Output schema:** One row per `HCP_COHORT_ID`, one column per distinct `EVENT_NAME`, values = days since first occurrence from anchor.

---

## Per-Claim-Type Details

| Claim | Notebook | ID | Section | Input Delta Path (from config) | Input Dict Key | Output Delta Path |
| --- | --- | --- | --- | --- | --- | --- |
| RX | `01_rx_features_rec_&_first_occ` | 2494728515032398 | Cells 18–22 | `rx_input_claims_total_events_and_first_occ_features_input` | `rx_from_claims` | `rx_first_occurrence_features` |
| DX | `02_dx_features_rec_&_first_occ` | 2494728515032399 | Cells 18–22 | `dx_input_claims_12M_and_first_occ_features_input` | `dx_from_claims` | `dx_first_occurrence_features` |
| PX | `03_px_features_rec_&_first_occ` | 2494728515032400 | Cells 18–22 | `px_input_claims_12M_and_first_occ_features_input` | `px_from_claims` | `px_first_occurrence_features` |
| Lab | `04_lab_features_rec_&_first_occ` | 2494728515032401 | Cells 18–22 | `lab_input_claims_12M_and_first_occ_features_input` | `lab_data_from_claims` | `lab_first_occurrence_features` |

All output paths under: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/`

### Config Column Mappings (from `00_config`)

| Claim | `claims_id` | `claims_patient_id` | `claims_event_date` | `claims_event_name` |
| --- | --- | --- | --- | --- |
| RX | `PROVIDER_ID` | `PATIENT_ID` | `SVC_DT` | `PRODUCT_GROUP` |
| DX | `PROVIDER_ID` | `PATIENT_ID` | `SVC_DT` | `DIAGNOSIS_DESCRIPTION` |
| PX | `PROVIDER_ID` | `PATIENT_ID` | `SVC_DT` | `PROCEDURE_DESCRIPTION` |
| Lab | `PROVIDER_ID` | `PATIENT_ID` | `SVC_DT` | `TEST_TYPE` |

---

## Key Differences: First Occurrence vs Recency

| Aspect | First Occurrence | Recency |
| --- | --- | --- |
| **Lookback scope** | Full lookback (all events where EVENT_TIME >= 0) | 12M only (EVENT_DATE between LOOKBACK_START and END) |
| **Helper module** | `00_first_occurrence_features` | `00_recency_features` |
| **Aggregation** | `max(EVENT_TIME)` per HCP_COHORT_ID per EVENT_NAME | Time-window based recency buckets |
| **Interpretation** | Days since first ever occurrence | How recently the event occurred |
| **Section in notebook** | B1 (cells 18–22) | B2 (cells 25–31) |

---

## Common EDA Patterns

### 1. Feature Column Inventory
```python
df = spark.read.format("delta").load(".../notebook_output/rx_first_occurrence_features")
print(f"Shape: {df.count()} rows, {len(df.columns)} columns")
# List all event names from column names
event_cols = [c for c in df.columns if c.endswith("_first_occurrence")]
print(f"Distinct events: {len(event_cols)}")
for c in sorted(event_cols): print(c)
```

### 2. Distribution of First Occurrence Timing
```python
# How many days ago did patients first get Kerendia?
df.select("max(EVENT_TIME)_KERENDIA_first_occurrence").summary().show()
```

### 3. Cross-Claim First Event Comparison
```python
# Compare first occurrence across claim types for the same patients
rx_fo = spark.read.format("delta").load(".../rx_first_occurrence_features")
dx_fo = spark.read.format("delta").load(".../dx_first_occurrence_features")
joined = rx_fo.join(dx_fo, on="HCP_COHORT_ID", how="inner")
```

### 4. Null Analysis (events that never occurred)
```python
from pyspark.sql.functions import sum as spark_sum, when, col
null_counts = df.select([
    spark_sum(when(col(c).isNull(), 1).otherwise(0)).alias(c)
    for c in event_cols
])
null_counts.show(vertical=True)
```

---

## Notebook References

**Feature notebooks (Section B1):**
* [01_rx_features_rec_&_first_occ](/editor/notebooks/2494728515032398) — RX first occurrence (cells 18–22)
* [02_dx_features_rec_&_first_occ](/editor/notebooks/2494728515032399) — DX first occurrence (cells 18–22)
* [03_px_features_rec_&_first_occ](/editor/notebooks/2494728515032400) — PX first occurrence (cells 18–22)
* [04_lab_features_rec_&_first_occ](/editor/notebooks/2494728515032401) — Lab first occurrence (cells 18–22)

**Helper notebooks:**
* [00_first_occurrence_features](/editor/notebooks/3340972492350419) — `first_occurrence_of_event` class
* [00_batch_processing](/editor/notebooks/3340972492350405) — `DataFrameBatchProcessor` class
* [00_load_processed_data](/editor/notebooks/2494728515032293) — `DataFrameMerger` class
* [00_config](/editor/notebooks/2494728515032290) — Date params, file paths, column mappings
* [00_connection](/editor/notebooks/198916793189023) — Snowflake auth + imports
