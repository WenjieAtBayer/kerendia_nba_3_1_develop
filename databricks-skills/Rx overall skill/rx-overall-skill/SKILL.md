---
name: rx-overall-skill
description: >
  Consolidated skill for generating RX patient-level feature engineering notebooks in the
  Kerendia NBA 3.x pipeline. Covers First Occurrence, Recency, and Frequency features.
  Read this skill when the user asks to generate, reproduce, or modify any RX feature
  notebook (01_rx_features_rec_&_first_occ or 01_rx_frequency_features). Designed to
  be extended to DX, PX, and Lab claim types without restructuring. Hospitalization
  is documented as a future extension (DX/PX only — not applicable to RX).
---

# RX Overall Skill — Patient-Level Feature Engineering

This skill consolidates four feature-engineering patterns — First Occurrence, Recency,
Frequency, and Hospitalization — into a single skill for the Kerendia NBA 3.x pipeline.
**Scope for this round: RX only.** The architecture is designed so DX, PX, and Lab can be
added later by creating new template files and extending the parameterization table below.

## When to Read This Skill

Read this skill when the user asks to:
- Generate or reproduce an RX feature engineering notebook
- Understand the RX feature pipeline (First Occurrence, Recency, Frequency)
- Modify an existing RX feature notebook (add events, change time windows, etc.)
- Extend the skill to cover DX, PX, or Lab claim types

## Architecture Overview

Two target notebooks are reproducible from this skill:

| Notebook | Template File | Cells | Features |
| --- | --- | --- | --- |
| `01_rx_features_rec_&_first_occ` | [rx-rec-and-first-occ-template.md](rx-rec-and-first-occ-template.md) | 35 | First Occurrence (B1) + Recency (B2) |
| `01_rx_frequency_features` | [rx-frequency-template.md](rx-frequency-template.md) | 66 | Claim Count + Lag + Change Freq + Patient Counts + Combine |

Both notebooks live in:
`/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/01_Patient_Features/`

---

## Shared Context

### Volume Paths

All Delta outputs are written under:
```
/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/
```

Cohort anchor dates CSV:
```
/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/hcp_model_inference_anchor_dates.csv
```

### Helper Notebooks (loaded via %run)

All helper notebooks live in:
`/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/`

| Helper | File | Purpose |
| --- | --- | --- |
| `00_connection` | `00_connection` | Snowflake auth, imports (pyspark, pandas, etc.) |
| `00_config` | `00_config` | Date params, file paths, column mappings, time_windows, event_prevalence |
| `00_load_processed_data` | `00_load_processed_data` | `DataFrameMerger` class — standardizes claims, generates anchor dates, creates HCP_COHORT_ID |
| `00_batch_processing` | `00_batch_processing` | `DataFrameBatchProcessor` class — splits by cohort suffix into batches |
| `00_first_occurrence_features` | `00_first_occurrence_features` | `first_occurrence_of_event` class — max(EVENT_TIME) pivot |
| `00_recency_features` | `00_recency_features` | `recency` class — 6 sub-features (min event time, counts, skewness) |

### Config Variables (from `00_config`)

| Variable | RX Value | Description |
| --- | --- | --- |
| `rx1_file_path` | Delta path to RX total events input | Used by DataFrameMerger (rec_&_first_occ) |
| `rx2_file_path` | Delta path to RX total events input (second file) | Used by DataFrameMerger (rec_&_first_occ) |
| `rx_freq_file_path` | Delta path to RX 12M claims input | Used by frequency notebook (reads Delta directly) |
| `hcp_universe_path` | Delta path to HCP universe | PROVIDER_ID distinct list |
| `cohort_start_date` | e.g. `'2025-10-01'` | Anchor date generation start |
| `cohort_end_date` | e.g. `'2025-10-01'` | Anchor date generation end |
| `months_increment` | e.g. `3` | Months between cohorts |
| `lookback_duration` | `365` | Days of lookback from anchor |
| `prediction_duration` | e.g. `30` | Days of prediction window |
| `event_prevalence` | `0.01` | Event prevalence threshold (1% = keep events appearing in >= 1% of HCPs) |
| `time_windows` | `[30, 60, 90, 180, 270, 360]` | Recency time windows (days) |
| `claims_id_rx` | `PROVIDER_ID` | Claim ID column for RX |
| `claims_patient_id_rx` | `PATIENT_ID` | Patient ID column for RX |
| `claims_event_date_rx` | `SVC_DT` | Event date column for RX |
| `claims_event_name_rx` | `PRODUCT_GROUP` | Event name column for RX |

### DataFrameMerger API

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
- Generates anchor dates from `cohort_start_date` to `cohort_end_date` at `months_increment` intervals
- For each anchor: `LOOKBACK_END_DATE` = last day of month 2 months before anchor, `LOOKBACK_START_DATE` = LOOKBACK_END_DATE - lookback_duration days
- Creates `HCP_COHORT_ID` = `{PROVIDER_ID}_{COHORT}` where COHORT = `I01`, `I02`, etc.
- Standardizes all claim types to: `PROVIDER_ID`, `PATIENT_ID`, `EVENT_NAME`, `EVENT_DATE`, `EVENT_TYPE`
- Applies event prevalence filter (default 0% — keeps all events)
- Saves anchor dates CSV to `.../query_output/hcp_model_inference_anchor_dates.csv`

**Per-claim-type invocation pattern** (blanks out all non-target paths):
```python
# RX example — only RX paths filled, all others blanked:
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
rx_claims_loaded = claims_data["rx_from_claims"]
```

**Dict keys per claim type:**

| Claim | Dict Key |
| --- | --- |
| RX | `rx_from_claims` |
| DX | `dx_from_claims` |
| PX | `px_from_claims` |
| Lab | `lab_data_from_claims` |

### DataFrameBatchProcessor API

```python
processor = DataFrameBatchProcessor(spark)
batch_list = processor.batch_creation_by_type(claims_loaded, batch_size=6)
```

- Extracts COHORT suffix from `HCP_COHORT_ID` using regex `_(C\d+)$`
- Groups distinct cohorts into batches of `batch_size` (default 6)
- Returns `list[DataFrame]` — each batch contains claims for a subset of cohorts

### first_occurrence_of_event API

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
# Core: groupBy(HCP_COHORT_ID).pivot(EVENT_NAME).agg(max(EVENT_TIME))
# Column renaming: add "_first_occurrence" suffix to all non-ID columns
# Output: one row per HCP_COHORT_ID, one column per EVENT_NAME
# Value = days since first occurrence from anchor (higher = earlier event)
```

### recency API

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

Produces 6 sub-features joined on `HCP_COHORT_ID`:

| # | Sub-Feature | Method | Output Columns |
| --- | --- | --- | --- |
| 1 | Most Recent Event | `aggregate_min_event_time()` | `min(EVENT_TIME)_{EVENT_NAME}_time_min` |
| 2 | Total & Unique Events | `calculate_event_counts()` | `total_events`, `unique_events` |
| 3 | Event Counts by Time Window | `calculate_event_counts_for_time_windows()` | `total_events_time_{N}_days`, `unique_events_time_{N}_days` |
| 4 | Event Counts by Type | `calculate_event_counts_by_type()` | `total_{type}`, `unique_{type}` |
| 5 | Event Counts by Type x Window | `calculate_event_counts_by_type_and_window()` | `total_events_time_{N}_days_{type}`, `unique_events_time_{N}_days_{type}` |
| 6 | Skewness | `skewness()` | `skewness_time_{N}_days_{type}` |

### Column Name Sanitization (Frequency notebook)

Applied to pivot output column names before adding `FREQ_` prefix:
```python
c.replace(", ", " ")     # comma-space -> space
 .replace(",", " ")      # lone comma -> space
 .replace("+", "and")   # plus -> and
 .replace("/", " or")    # slash -> or (note: space before or, no space after)
 .replace("-", "_")      # hyphen -> underscore
 .replace(" ", "_")      # space -> underscore
 .replace("__", "_")     # double underscore -> single underscore
 .replace("(", "")       # remove open paren
 .replace(")", "")       # remove close paren
 .replace("[", "")       # remove open bracket
 .replace("]", "")       # remove close bracket
 .upper()                # UPPERCASE
# Then prepended with "FREQ_" prefix
```

### HCP Universe Cross-Join Pattern

Used in Frequency notebook (Sub-types C and D) and the Combine Everything section:
```python
hcp_universe = spark.read.format("delta").load(hcp_universe_path).select('PROVIDER_ID').distinct()
cohort_df = spark.createDataFrame(pd.read_csv(".../query_output/hcp_model_inference_anchor_dates.csv"))
cohort_df = cohort_df.withColumn("SVC_DT_M", F.trunc(cohort_df["LOOKBACK_END_DATE"], "MM"))
updated_cohort_df = cohort_df.select("SVC_DT_M", "COHORT")
hcp_universe = hcp_universe.crossJoin(updated_cohort_df)
```

The `skeleton_df` (used in Combine Everything) creates `HCP_COHORT_ID`:
```python
skeleton_df = hcp_universe.select("PROVIDER_ID", "COHORT").distinct().withColumn(
    "HCP_COHORT_ID", concat_ws("_", hcp_universe["PROVIDER_ID"], hcp_universe["COHORT"])
)
```

---

## Claim-Type Parameterization Table

This table is the single source of truth for adapting templates to different claim types.
To add DX/PX/Lab, create a new template file and substitute values from this table.

| Parameter | RX | DX | PX | Lab |
| --- | --- | --- | --- | --- |
| **Notebook (rec_&_first_occ)** | `01_rx_features_rec_&_first_occ` | `02_dx_features_rec_&_first_occ` | `03_px_features_rec_&_first_occ` | `04_lab_features_rec_&_first_occ` |
| **Notebook (frequency)** | `01_rx_frequency_features` | `02_dx_frequency_features` | `03_px_frequency_features` | `04_lab_frequency_features` |
| **File path var (merger)** | `rx1_file_path`, `rx2_file_path` | `dx1_file_path`, `dx2_file_path` | `px1_file_path`, `px2_file_path` | `lab_data1_file_path`, `lab_data2_file_path` |
| **File path var (freq)** | `rx_freq_file_path` | `dx1_file_path` | `px1_file_path` | `lab_data1_file_path` |
| **Dict key (merger)** | `rx_from_claims` | `dx_from_claims` | `px_from_claims` | `lab_data_from_claims` |
| **claims_id** | `claims_id_rx` (`PROVIDER_ID`) | `claims_id_dx` (`PROVIDER_ID`) | `claims_id_px` (`PROVIDER_ID`) | `claims_id_lab` (`PROVIDER_ID`) |
| **claims_patient_id** | `claims_patient_id_rx` (`PATIENT_ID`) | `claims_patient_id_dx` (`PATIENT_ID`) | `claims_patient_id_px` (`PATIENT_ID`) | `claims_patient_id_lab` (`PATIENT_ID`) |
| **claims_event_date** | `claims_event_date_rx` (`SVC_DT`) | `claims_event_date_dx` (`SVC_DT`) | `claims_event_date_px` (`SVC_DT`) | `claims_event_date_lab` (`SVC_DT`) |
| **claims_event_name** | `claims_event_name_rx` (`PRODUCT_GROUP`) | `claims_event_name_dx` (`DIAGNOSIS_DESCRIPTION`) | `claims_event_name_px` (`PROCEDURE_DESCRIPTION`) | `claims_event_name_lab` (`TEST_TYPE`) |
| **Pivot column (frequency)** | `PRODUCT_GROUP` | `DIAGNOSIS_DESCRIPTION` | `PROCEDURE_DESCRIPTION` | `TEST_TYPE` |
| **Output prefix** | `rx_` | `dx_` | `px_` | `lab_data_` (Lab uses `lab_data_` not `lab_`) |
| **Patient count verb** | `PRESCRIBED_WITH` | `DIAGNOSED_WITH` | `DID_PROCEDURE` | `DID_LAB_TEST` |
| **Combine suffix** | `_RX` | `_DX` | `_PX` | `_LAB` |
| **Accelerator output** | `rx_accelerator_features` | `dx_accelerator_features` | `px_accelerator_features` | `lab_data_accelerator_features` |

### Key Differences Between Notebooks

| Aspect | rec_&_first_occ | frequency |
| --- | --- | --- |
| **Grain** | `HCP_COHORT_ID` (patient-level) | `PROVIDER_ID x SVC_DT_M` (HCP-level, monthly) |
| **Data loading** | `DataFrameMerger.merge_all()` | `spark.read.format("delta").load(rx_freq_file_path)` |
| **Batching** | `DataFrameBatchProcessor` | None |
| **Lookback scope** | Full lookback (EVENT_TIME >= 0) + 12M filter for recency | 12M input claims (no additional filter for sub-types A-B) |
| **Helper modules** | `00_first_occurrence_features`, `00_recency_features` | Inline functions (step2_fill_missing, step3_lag, process_and_join) |
| **Outputs** | 2 Delta tables (first_occurrence + recency) | 5 Delta tables (freq, lag_freq, freq_and_change, change_freq, num_patients) + 1 combined (accelerator) |

---

## RX Output Delta Tables

| Output | Path suffix | Grain | Notebook |
| --- | --- | --- | --- |
| First Occurrence | `rx_first_occurrence_features` | `HCP_COHORT_ID` | rec_&_first_occ |
| Recency | `rx_recency_features` | `HCP_COHORT_ID` | rec_&_first_occ |
| Claim Count | `rx_frequency_features` | `PROVIDER_ID, SVC_DT_M` | frequency |
| Lag Frequency | `rx_lag_frequency_features` | `PROVIDER_ID, SVC_DT_M` | frequency |
| Change + Lag | `rx_freq_and_change_frequency` | `PROVIDER_ID, SVC_DT_M` | frequency |
| Change Only | `rx_change_frequency` | `PROVIDER_ID, SVC_DT_M` | frequency |
| Patient Counts | `rx_num_patients_features` | `PROVIDER_ID, COHORT` | frequency |
| Combined | `rx_accelerator_features` | `HCP_COHORT_ID` | frequency (Combine Everything) |

All paths prefixed with the notebook_output volume path above.

---

## Hospitalization (Future Extension — DX/PX Only)

Hospitalization features are **not applicable to RX**. They exist only for DX and PX.
When extending this skill to DX/PX, add a `dx-hospitalization-template.md` and
`px-hospitalization-template.md` using the existing `hospitalization-features` skill
as reference.

**Key hospitalization patterns (for future reference):**
- DX and PX only — no RX or Lab hospitalization notebooks exist
- Event collapse: `lit("ALL_DIAGNOSIS")` (DX) / `lit("ALL_PROCEDURES")` (PX)
- Two input sources: total claims + hospitalized-only claims (DATA_SOURCE='HX')
- Rolling windows: `[1, 6, 12]` months (shorter than frequency's `[1,2,3,6,12]`)
- Patient count windows: `[30, 180, 360]` days (shorter than frequency's `[30,60,90,180,360]`)
- Validation filter: remove rows where TOTAL < HOSPITALIZED
- % Hospitalized = HOSP / TOTAL per window
- Combine: joins % hospitalized + patient counts on HCP_COHORT_ID; PX appends `_PX` suffix

---

## How to Use This Skill to Generate a Notebook

1. Read this SKILL.md for the architecture, config, and parameterization table.
2. Open the appropriate template file:
   - For `01_rx_features_rec_&_first_occ`: read [rx-rec-and-first-occ-template.md](rx-rec-and-first-occ-template.md)
   - For `01_rx_frequency_features`: read [rx-frequency-template.md](rx-frequency-template.md)
3. Each template contains a **cell-by-cell verbatim blueprint** with:
   - A 1-2 line comment preamble explaining the cell's purpose
   - The exact code (Python, %run, or %md) for that cell
   - Cell numbering matching the original notebook
4. Create a new notebook and add cells in order from the template.
5. Do NOT read the original source notebooks during generation — the skill contains all needed detail.

### Extending to DX/PX/Lab

To add a new claim type:
1. Create a new template file (e.g., `dx-rec-and-first-occ-template.md`)
2. Copy the RX template and substitute values from the parameterization table above
3. Update the parameterization table with any claim-specific notes
4. Do NOT restructure SKILL.md — just add the new template file and a row in the notebook inventory

The shared context (helper APIs, volume paths, sanitization rules, HCP universe pattern)
is claim-agnostic and applies to all claim types without modification.


---

## How to Modify

This section turns the skill from reproduction-only into reproduction + modification.
It covers (a) change points by intent, (b) the data source contract, and (c) extension points.

### (a) Change Points by Intent

| Intent | File to Edit | Cell | Variable / Code | What Breaks Downstream |
| --- | --- | --- | --- | --- |
| Add a drug that already exists in PRODUCT_GROUP | `00_config` | Cell 11 | Add drug name to `relevant_rx_events` list | Nothing — drug will always survive prevalence filter |
| Add a drug not in source data | Upstream Snowflake query (not in scope) | N/A | Add to source table's PRODUCT_GROUP dimension | Must re-run input data creation pipeline before feature notebooks |
| Change lookback duration | `00_config` | Cell 7 | `lookback_duration = 365` | All recency + first occurrence features re-compute; anchor dates CSV regenerated; frequency NOT affected (reads 12M claims directly) |
| Change recency time windows | `00_config` | Cell 7 | `time_windows = [30, 60, 90, 180, 270, 360]` | Recency output gains/loses `*_time_{N}_days`, `*_time_{N}_days_{type}`, `skewness_time_{N}_days_{type}` columns; no notebook code changes needed |
| Change frequency lag windows | `rx-frequency-template.md` | Cell 14 | `last_i_month_list = [1,2,3,6,12]` | Lag frequency output columns change; `recent_windows = [1,2,3,6]` in Cell 27 must be a subset of `last_i_month_list` — enforced by runtime column reference (`F.col(f"FREQ_{event}_IN_LAST_{N}_MONTH")` fails if N is not in lag windows), not by explicit validation |
| Change patient count time windows | `rx-frequency-template.md` | Cell 43 | `time_windows = [30, 60, 90, 180, 360]` | Patient count columns change; Cell 47 `stack(5, ...)` count must match len(time_windows); Cell 48 regex extracts window number from column name |
| Change event prevalence threshold | `00_config` | Cell 22 | `event_prevalence = 0.01` | Fewer event columns in first occurrence + recency outputs; drugs in `relevant_rx_events` bypass this filter; frequency NOT affected (reads Delta directly, no prevalence filter) |
| Change cohort date range | `00_config` | Cell 7 | `cohort_start_date`, `cohort_end_date`, `months_increment` | New anchor dates generated; HCP_COHORT_ID set changes; all features re-compute; hcp_model_inference_anchor_dates.csv regenerated |
| Swap RX data source (different Snowflake table) | `00_config` | Cell 10 | Update `rx1_file_path`, `rx2_file_path`, `rx_freq_file_path` | Must preserve data source contract (see below); no notebook code changes if columns match |
| Change pivot/event column (e.g., PRODUCT_GROUP to GENERIC_NAME) | `00_config` | Cell 11 | `claims_event_name_rx = "PRODUCT_GROUP"` | All event-derived column names change; frequency pivot column changes; patient count column names change; downstream model must be retrained |
| Add new aggregation to recency class | `00_recency_features` helper | N/A (helper notebook) | Add new method to `recency` class; call it in `recency_features()` orchestrator | Recency output gains new columns; no notebook code changes needed |
| Add new sub-feature to frequency | `rx-frequency-template.md` | After Cell 53 (before Combine) | Add inline code block + save to new Delta | Must also add to Combine Everything: read new output, join on HCP_COHORT_ID |
| Change column sanitization rules | `rx-frequency-template.md` | Cell 10 | Modify `.replace()` chain in the select expression | All FREQ_ column names change; lag, change, and patient count columns all derive from sanitized names |
| Change combine suffix | `rx-frequency-template.md` | Cell 63 | `f"{c}_RX"` | All non-key columns in accelerator output get new suffix; downstream model must expect new suffix |

### (b) Data Source Contract

The downstream code in both notebooks depends on specific columns from the RX Delta input tables.
When swapping data sources, these columns MUST be present with the same names and semantics.

**Required source columns (must exist in Delta tables at `rx1_file_path` / `rx2_file_path` / `rx_freq_file_path`):**

| Column | Type | Used By | Purpose |
| --- | --- | --- | --- |
| `PROVIDER_ID` | string | Both notebooks | HCP identifier — grain for frequency, part of HCP_COHORT_ID for recency |
| `PATIENT_ID` | string | Frequency (Sub-type D only) | Patient identifier for countDistinct in patient count features |
| `SVC_DT` | date | Both notebooks | Event/service date — used for filtering, monthly grouping (SVC_DT_M), days_diff |
| `PRODUCT_GROUP` | string | Both notebooks | Event name dimension — pivoted in frequency, mapped to EVENT_NAME by DataFrameMerger |

**Columns generated by DataFrameMerger (not from source — created in rec_&_first_occ notebook):**

| Column | Source | Purpose |
| --- | --- | --- |
| `EVENT_DATE` | Mapped from `SVC_DT` via `claims_event_date_rx` | Standardized event date |
| `EVENT_NAME` | Mapped from `PRODUCT_GROUP` via `claims_event_name_rx` | Standardized event name |
| `EVENT_TYPE` | Set to `"rx"` by DataFrameMerger | Event type for recency class grouping |
| `EVENT_TIME` | `datediff(LOOKBACK_END_DATE, EVENT_DATE)` | Days from event to anchor |
| `LOOKBACK_START_DATE` | `LOOKBACK_END_DATE - lookback_duration` | Start of lookback window |
| `LOOKBACK_END_DATE` | Last day of month 2 months before anchor | End of lookback window |
| `HCP_COHORT_ID` | `concat_ws("_", PROVIDER_ID, COHORT)` | Patient-cohort composite key |

**Columns from cohort anchor dates CSV (used by frequency notebook):**

| Column | Type | Purpose |
| --- | --- | --- |
| `COHORT` | string | Cohort identifier (e.g., I01, I02) |
| `LOOKBACK_START_DATE` | date | Start of lookback window for patient count filtering |
| `LOOKBACK_END_DATE` | date | End of lookback window; also used to derive SVC_DT_M |

**Optional columns (present but not functionally required downstream):**

| Column | Notes |
| --- | --- |
| `CLAIM_ID` | Passed through by DataFrameMerger; not referenced in feature computation |
| `SERIAL_NO` | Used only in debug cells (Cell 13 in rec_&_first_occ, dropped in Cell 38 of frequency) |
| `DAYS_SUPPLY`, `NDC_CD`, `PRODUCT_STRENGTH`, `GENERIC_NAME`, `REFILL_CODE`, `REJECT_CODE`, `PAYER_PLAN_ID`, `SOB`, `CLAIM_TYPE` | Passed through by DataFrameMerger but never referenced in feature computation |

**Data source swap safety checklist:**
1. New table has `PROVIDER_ID`, `PATIENT_ID`, `SVC_DT`, `PRODUCT_GROUP` columns
2. `SVC_DT` is a date type (or castable to date)
3. `PRODUCT_GROUP` values match expected drug names (e.g., KERENDIA, FARXIGA, etc.)
4. If `PRODUCT_GROUP` column name differs, update `claims_event_name_rx` in `00_config`
5. If `PROVIDER_ID` or `PATIENT_ID` column names differ, update `claims_id_rx` / `claims_patient_id_rx` in `00_config`
6. No changes needed to the notebook templates themselves — only `00_config` values change

### (c) Extension Points

**Where to add a new sub-feature type:**

| Context | Insert Point | What to Add | Downstream Impact |
| --- | --- | --- | --- |
| New recency sub-feature (e.g., entropy) | `00_recency_features` helper notebook | New method on `recency` class + call in `recency_features()` | Recency output gains columns; no notebook code changes |
| New frequency sub-feature (e.g., monthly average) | `rx-frequency-template.md` after Cell 53 | New inline code block + save to new Delta | Must add read-back + join in Combine Everything (Cells 55-63) |
| New patient-level feature family (e.g., diversity) | New notebook (like hospitalization is separate) | Full notebook with its own helper or inline code | Add to Combine Everything section in frequency notebook, or create separate combine step |
| New claim type (DX/PX/Lab) | New template files in this skill folder | Copy RX template, substitute from parameterization table | No SKILL.md restructuring; just add template + parameterization row |

**Plug-in architecture for Combine Everything (frequency notebook):**

The Combine Everything section (Cells 54-64) follows a repeatable pattern:
1. Cell 55: Create `hcp_universe` cross-join (shared skeleton)
2. Cell 57: Create `skeleton_df` with `HCP_COHORT_ID`
3. For each feature output to combine: read Delta, join with `hcp_universe`, add `HCP_COHORT_ID`, drop keys
4. Cell 61: Left-join all on `HCP_COHORT_ID` from `skeleton_df`
5. Cell 63: Append claim-type suffix (`_RX`) to non-protected columns
6. Cell 64: Save to `rx_accelerator_features`

To add a new feature output to the combine:
```python
# After Cell 60, add:
new_features = spark.read.format("delta").load(".../new_output_path")
new_features = hcp_universe.select("PROVIDER_ID", "COHORT").distinct().join(
    new_features, on=["PROVIDER_ID", "COHORT"], how="inner"
)
new_features = new_features.withColumn(
    "HCP_COHORT_ID",
    concat_ws("_", new_features["PROVIDER_ID"], new_features["COHORT"])
).drop("PROVIDER_ID", "COHORT")

# In Cell 61, add another .join():
combined_features = skeleton_df \
    .join(rx_lag_freq_and_change_freq_features, on="HCP_COHORT_ID", how="left") \
    .join(rx_num_patients_features, on="HCP_COHORT_ID", how="left") \
    .join(new_features, on="HCP_COHORT_ID", how="left")  # NEW
```


### After Modifying — How to Verify

After any change to config, templates, or helper notebooks, run these sanity checks
to confirm the change worked correctly before promoting to production.

**For deeper validation after modification**, run the QC notebook from the companion skill
[rx-feature-qc-eda](../rx-feature-qc-eda/SKILL.md). That skill generates a notebook that
independently recomputes feature values from raw source data for a stratified sample of HCPs
and compares them side-by-side against the notebook outputs — catching computation bugs
that row-count and schema checks alone would miss.

**1. Row count check — verify output grain is unchanged**

```python
BASE = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output"

# For rec_&_first_occ outputs (grain: HCP_COHORT_ID)
for table in ["rx_first_occurrence_features", "rx_recency_features"]:
    df = spark.read.format("delta").load(f"{BASE}/{table}")
    print(f"{table}: {df.count():,} rows, {len(df.columns)} cols")

# For frequency outputs (grain varies)
for table in ["rx_frequency_features", "rx_lag_frequency_features",
              "rx_freq_and_change_frequency", "rx_change_frequency",
              "rx_num_patients_features", "rx_accelerator_features"]:
    df = spark.read.format("delta").load(f"{BASE}/{table}")
    print(f"{table}: {df.count():,} rows, {len(df.columns)} cols")
```

If row count drops unexpectedly, check whether the event prevalence filter or lookback
window change removed HCP-cohort combinations that previously had data.

**2. Schema diff — compare before/after column sets**

```python
# Before making changes, capture the schema:
# spark.read.format("delta").load(f"{BASE}/rx_recency_features").columns

# After changes, compare:
df = spark.read.format("delta").load(f"{BASE}/rx_recency_features")
expected_cols = {"HCP_COHORT_ID", "min(EVENT_TIME)_KERENDIA_time_min", "total_events", ...}
new_cols = set(df.columns) - expected_cols
dropped_cols = expected_cols - set(df.columns)
print(f"New columns: {new_cols}")
print(f"Dropped columns: {dropped_cols}")
```

For time window changes: verify the new `_{N}_days` columns appear in all three categories
(time_window counts, type x window counts, skewness). For lag window changes: verify
`_IN_LAST_{N}_MONTH` columns appear for each event x each new window.

**3. Spot-check a known HCP_COHORT_ID**

```python
# Pick a known provider-cohort and verify feature values are sensible
df = spark.read.format("delta").load(f"{BASE}/rx_first_occurrence_features")
sample = df.filter(col("HCP_COHORT_ID").isin(
    df.select("HCP_COHORT_ID").limit(5).rdd.flatMap(lambda x: x).collect()
))
sample.display()
```

Checks:
- First occurrence values should be >= 0 (days before anchor)
- Recency `min(EVENT_TIME)` should be <= `max(EVENT_TIME)` for the same event
- Frequency counts should be non-negative integers
- Patient counts should be non-negative integers, and `pt_cnt_{N}_days` should be
  monotonically non-decreasing as N increases (30 <= 60 <= 90 <= 180 <= 360)

**4. Null rate check — verify no unexpected nulls introduced**

```python
from pyspark.sql.functions import sum as spark_sum, when, col

df = spark.read.format("delta").load(f"{BASE}/rx_recency_features")
total = df.count()
feature_cols = [c for c in df.columns if c != "HCP_COHORT_ID"]
null_rates = df.select([
    (spark_sum(when(col(c).isNull(), 1).otherwise(0)) / total * 100).alias(c)
    for c in feature_cols[:20]  # Check first 20 feature columns
])
null_rates.display()
```

Expected: events in `relevant_rx_events` (KERENDIA, STEGLATRO, INVOKANA) should have
low null rates. Other events may have high null rates if the prevalence filter was raised.

**5. Cross-table consistency check**

```python
# Verify HCP_COHORT_ID sets are consistent across outputs
first_occ_ids = spark.read.format("delta").load(f"{BASE}/rx_first_occurrence_features").select("HCP_COHORT_ID").distinct()
recency_ids = spark.read.format("delta").load(f"{BASE}/rx_recency_features").select("HCP_COHORT_ID").distinct()
accelerator_ids = spark.read.format("delta").load(f"{BASE}/rx_accelerator_features").select("HCP_COHORT_ID").distinct()

print(f"First occ IDs: {first_occ_ids.count():,}")
print(f"Recency IDs: {recency_ids.count():,}")
print(f"Accelerator IDs: {accelerator_ids.count():,}")
print(f"First occ - Recency: {first_occ_ids.exceptAll(recency_ids).count()} (should be 0)")
print(f"Recency - Accelerator: {recency_ids.exceptAll(accelerator_ids).count()} (should be 0)")
```

If any of these show non-zero differences, the lookback window or prevalence filter
change affected one feature type but not another — investigate before promoting.
