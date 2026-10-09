---
name: frequency-features
description: >
  Guidance for understanding and exploring Frequency features in the Kerendia NBA 3.x pipeline.
  Read this skill when the user asks about frequency features, lag frequency, change in frequency,
  unique patient counts, the _frequency_features notebooks, or rolling window claim counts.
  Covers RX, DX, PX, and Lab claim types. These are HCP-level features (grain = PROVIDER_ID
  × SVC_DT_M or PROVIDER_ID × COHORT), unlike First Occurrence and Recency which are
  patient-level (HCP_COHORT_ID).
---

# Frequency Features — HCP-Level Feature Engineering

Frequency features capture **how often events occur** at the HCP (provider) level, aggregated
at monthly grain. Unlike First Occurrence and Recency (which are patient-level with
`HCP_COHORT_ID` grain), Frequency features use `PROVIDER_ID` × `SVC_DT_M` (monthly) or
`PROVIDER_ID` × `COHORT` as the grain.

As per your instructions, these features feed the BERT Transformer model trained on Kerendia
Drug Events for Masked Event Prediction, Next Event Prediction, and Shuffled Order correction.

## Architecture: 4 Sub-Feature Types

Each of the 4 frequency notebooks (RX, DX, PX, Lab) produces 5 Delta outputs across 4
sub-feature types:

```
Input: 12M claims Delta (e.g. rx1_file_path)
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Sub-type A: Claim Count (monthly pivot)                 │
│  → {claim}_frequency_features                            │
└─────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Sub-type B: Lag Frequency (rolling monthly windows)     │
│  step2_fill_missing → step3_lag → process_and_join       │
│  → {claim}_lag_frequency_features                        │
└─────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Sub-type C: Change in Frequency                         │
│  (FREQ_N/N_days) - ((FREQ_12 - FREQ_N)/(12 - N_days))   │
│  → {claim}_freq_and_change_frequency (before drop)       │
│  → {claim}_change_frequency (after drop FREQ_* cols)     │
└─────────────────────────────────────────────────────────────────┘
      (independent from above)
┌─────────────────────────────────────────────────────────────────┐
│  Sub-type D: Unique Patient Counts per HCP               │
│  Cross-join with hcp_model_inference_anchor_dates.csv    │
│  → {claim}_num_patients_features                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Sub-Type A: Claim Count (Monthly Pivot)

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

```python
# 1. Add monthly column
claims = claims.withColumn("SVC_DT_M", F.date_trunc('MM', col("SVC_DT")))

# 2. Pivot by event column, count claims
freq_claims = claims.groupBy(['PROVIDER_ID', 'SVC_DT_M']).pivot(EVENT_COL).agg(F.count(F.lit(1)))

# 3. Clean column names: add FREQ_ prefix, sanitize
#    Replace: ", " → " ", "+" → "and", "/" → " or", "-" → "_", spaces → "_", UPPER
```

**Output columns:** `FREQ_{EVENT_NAME}` per unique event per `[PROVIDER_ID, SVC_DT_M]`

**Pivot column per claim type:**

| Claim | Pivot Column | Example Feature |
| --- | --- | --- |
| RX | `PRODUCT_GROUP` | `FREQ_KERENDIA` |
| DX | `DIAGNOSIS_DESCRIPTION` | `FREQ_CHRONIC_KIDNEY_DISEASE` |
| PX | `PROCEDURE_DESCRIPTION` | `FREQ_OFFICE_OUTPATIENT_VISIT_EST` |
| Lab | `TEST_TYPE` | `FREQ_ESTIMATED_GFR` |

---

## Sub-Type B: Lag Frequency (Rolling Monthly Windows)

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

Builds rolling-window sums on top of the Claim Count pivot using 3 helper functions defined
inline in each notebook (NOT in a shared helper module):

### `step2_fill_missing(df, key_col, date_col)`
```python
# 1. Get min/max date range
# 2. Generate sequence of all months between min → max
# 3. Cross-join with all distinct PROVIDER_IDs
# 4. Left-join original data, fillna(0) for all feature columns
# Result: every PROVIDER_ID has a row for every month (sparse → dense)
```

### `step3_lag(df, key_col, date_col, last_i_month_list)`
```python
# For each feature column × each rolling window [1, 2, 3, 6, 12]:
F.sum(col).over(
    Window.partitionBy(key_col).orderBy(date_col).rowsBetween(-i+1, 0)
).alias(f"{col}_IN_LAST_{i}_MONTH")
```

### `process_and_join(df, last_i_month_list)`
Orchestrator: `fill_missing` → `lag` → keep only `_IN_LAST_` columns + keys → join back.

**Rolling windows:** `[1, 2, 3, 6, 12]` months

**Output columns:** `FREQ_{EVENT}_IN_LAST_{N}_MONTH` for each event × each window

---

## Sub-Type C: Change in Frequency

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

Measures whether event frequency is **accelerating or decelerating** compared to the 12-month
baseline.

**Formula:**
```python
CHANGE = (FREQ_{EVENT}_IN_LAST_{N}_MONTH / N_months) - 
         ((FREQ_{EVENT}_IN_LAST_12_MONTH - FREQ_{EVENT}_IN_LAST_{N}_MONTH) / (12 - N_months))
```

**Recent windows:** `[1, 2, 3, 6]` (not 12 — 12M is the baseline)

**Output columns:** `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_{EVENT}_IN_LAST_{N}_MONTH`

**Key detail:** After computing change features, raw `FREQ_*_IN_LAST_*` columns are **dropped**.
Two saves happen:
1. `{claim}_freq_and_change_frequency` — contains BOTH lag freq + change freq (before drop)
2. `{claim}_change_frequency` — contains ONLY change freq + key columns (after drop)

**Prerequisite:** Requires HCP universe cross-join with cohort anchor dates before computing.
```python
hcp_universe = spark.read.format("delta").load(hcp_universe_path).select('PROVIDER_ID').distinct()
cohort_df = spark.createDataFrame(pd.read_csv(".../hcp_model_inference_anchor_dates.csv"))
cohort_df = cohort_df.withColumn("SVC_DT_M", F.trunc(cohort_df["LOOKBACK_END_DATE"], "MM"))
hcp_universe = hcp_universe.crossJoin(updated_cohort_df)
lag_freq_features = hcp_universe.select("PROVIDER_ID", "SVC_DT_M").distinct().join(
    lag_freq_features, on=["PROVIDER_ID", "SVC_DT_M"], how='inner'
)
```

---

## Sub-Type D: Unique Patient Counts per HCP

**Grain:** `[PROVIDER_ID, COHORT]` (NOT monthly — this is cohort-level)

Counts how many **distinct patients** an HCP saw for each event within various time windows
from the cohort's lookback end date.

**Steps:**
1. Cross-join claims with `hcp_model_inference_anchor_dates.csv` (COHORT, LOOKBACK_START, LOOKBACK_END)
2. Filter to cohort-specific lookback window: `SVC_DT BETWEEN LOOKBACK_START AND LOOKBACK_END`
3. `days_diff = DATEDIFF(LOOKBACK_END_DATE, SVC_DT)`
4. Flag for time windows: `[30, 60, 90, 180, 360]` days
5. Dedup on `[PROVIDER_ID, COHORT, EVENT_COL, PATIENT_ID]`
6. Aggregate: `countDistinct(PATIENT_ID)` per `[PROVIDER_ID, COHORT, EVENT_COL]` per flag
7. Unpivot → Pivot wide format with descriptive column names

**Feature prefix varies by claim type:**

| Claim | Feature Prefix |
| --- | --- |
| RX | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_{EVENT}_IN_LAST_{N}_DAYS` |
| DX | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_{EVENT}_IN_LAST_{N}_DAYS` |
| PX | `NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_{EVENT}_IN_LAST_{N}_DAYS` |
| Lab | `NUM_OF_PATIENTS_THE_HCP_DID_LAB_TEST_{EVENT}_IN_LAST_{N}_DAYS` |

---

## Per-Claim-Type Inventory

### Notebooks

| Claim | Notebook | ID | Cells |
| --- | --- | --- | --- |
| RX | `01_rx_frequency_features` | 2494728515032403 | 66 |
| DX | `02_dx_frequency_features` | 2494728515032402 | 65 |
| PX | `03_px_frequency_features` | 2494728515032404 | 66 |
| Lab | `04_lab_frequency_features` | 2494728515032405 | 62 |

### Delta Output Paths

All under `.../notebook_output/` in the volume.

| Sub-Type | RX | DX | PX | Lab |
| --- | --- | --- | --- | --- |
| A: Claim Count | `rx_frequency_features` | `dx_frequency_features` | `px_frequency_features` | `lab_data_frequency_features` |
| B: Lag Frequency | `rx_lag_frequency_features` | `dx_lag_frequency_features` | `px_lag_frequency_features` | `lab_data_lag_frequency_features` * |
| C: Change+Lag | `rx_freq_and_change_frequency` | `dx_freq_and_change_frequency` | `px_freq_and_change_frequency` | `lab_data_freq_and_change_frequency` |
| C: Change Only | `rx_change_frequency` | `dx_change_frequency` | `px_change_frequency` | `lab_data_change_frequency` |
| D: Patient Counts | `rx_num_patients_features` | `dx_num_patients_features` | `px_num_patients_features` | `lab_data_num_patients_features` |

\* **Lab lag_frequency is saved as Parquet** (not Delta) — use `spark.read.parquet()` instead of `spark.read.format("delta").load()`

### Input Delta Paths (from config)

| Claim | Config Variable | Points To |
| --- | --- | --- |
| RX | `rx1_file_path` | `.../query_output/rx_input_claims_12M_features_input` |
| DX | `dx1_file_path` | `.../query_output/dx_input_claims_12M_and_first_occ_features_input` |
| PX | `px1_file_path` | `.../query_output/px_input_claims_12M_and_first_occ_features_input` |
| Lab | `lab_data1_file_path` | `.../query_output/lab_input_claims_12M_and_first_occ_features_input` |

---

## Key Differences from First Occurrence & Recency

| Aspect | Frequency | First Occurrence | Recency |
| --- | --- | --- | --- |
| **Grain** | `PROVIDER_ID` × `SVC_DT_M` (or COHORT) | `HCP_COHORT_ID` | `HCP_COHORT_ID` |
| **Level** | HCP-level | Patient-level | Patient-level |
| **Helper module** | Inline functions (step2/step3) | `00_first_occurrence_features` | `00_recency_features` |
| **DataFrameMerger?** | No — reads Delta directly | Yes | Yes |
| **Batch processing?** | No — no batching | Yes | Yes |
| **Date scope** | 12M input claims | Full lookback | 12M filtered |
| **Sub-features** | 4 types (5 outputs) | 1 type (1 output) | 6 types (1 output) |

---

## Column Name Sanitization

All 4 notebooks apply the same cleaning rules to event names before creating feature columns:

```python
# Applied to pivot output column names:
c.replace(", ", " ")     # comma-space → space
 .replace(",", " ")      # lone comma → space
 .replace("+", "and")    # plus → and
 .replace("/", " or ")   # slash → or
 .replace("-", "_")      # hyphen → underscore
 .replace(" ", "_")      # space → underscore
 .upper()                 # UPPERCASE
# Then prepended with "FREQ_" prefix
```

---

## Notebook References

**Feature notebooks:**
* [01_rx_frequency_features](/editor/notebooks/2494728515032403) — RX frequency (66 cells)
* [02_dx_frequency_features](/editor/notebooks/2494728515032402) — DX frequency (65 cells)
* [03_px_frequency_features](/editor/notebooks/2494728515032404) — PX frequency (66 cells)
* [04_lab_frequency_features](/editor/notebooks/2494728515032405) — Lab frequency (62 cells)

**Config & infrastructure:**
* [00_config](/editor/notebooks/2494728515032290) — File paths, `hcp_universe_path`
* [00_connection](/editor/notebooks/198916793189023) — Imports
* `hcp_model_inference_anchor_dates.csv` — Cohort anchor dates for Sub-types C & D
