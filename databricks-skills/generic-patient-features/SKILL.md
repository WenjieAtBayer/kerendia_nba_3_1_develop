---
name: generic-patient-features
description: >
  Consolidated, data-source-agnostic reference for patient-level feature engineering in the
  Kerendia NBA 3.x pipeline. Covers First Occurrence, Recency, Frequency, and Hospitalization
  features across RX, DX, PX, and Lab claim types. Read this skill when generating, modifying,
  or understanding any patient feature notebook, when standardizing raw claim data to the
  canonical schema, or when optimizing feature computation at 100B-row scale.
---

# Generic Patient Feature Engineering

Single consolidated reference for all patient-level feature types in the Kerendia NBA 3.x
pipeline. The same computation patterns apply to RX, DX, PX, and Lab data -- only the source
column names and event semantics differ. This skill abstracts those differences into a
canonical input contract and documents the business rules, grain, column naming, and
performance patterns for each feature type.

## Feature Execution Order

Features are created in this order. Each step is independent but follows the same pipeline:

1. **First Occurrence** -- when an event first appeared in a patient's journey (full lookback)
2. **Recency** -- how recently and frequently events occurred (12M lookback, 6 sub-features)
3. **Frequency** -- monthly event counts, rolling lags, change in frequency, unique patient counts
4. **Hospitalization** -- fraction of claims involving hospitalized patients (DX/PX only)

---

## 1. Input Contract

Feature computation requires claims data standardized to the canonical schema below. This is
a **prerequisite** -- the feature logic assumes these column names exist and does not perform
source-specific renaming internally.

### 1.1 Canonical Columns

| Column | Type | Description | Required By |
| --- | --- | --- | --- |
| `PROVIDER_ID` | string | Healthcare provider (HCP) identifier | All features |
| `PATIENT_ID` | string | Patient identifier | First Occ, Recency, Freq Sub-D, Hosp Sub-D |
| `EVENT_NAME` | string | Event being measured (drug, diagnosis, procedure, test) | All features |
| `EVENT_DATE` | date | Date the event occurred | All features |
| `EVENT_TYPE` | string | Assigned label: `rx`, `dx`, `px`, or `lab` | First Occ, Recency |
| `CLAIM_ID` | string | Unique claim identifier | Optional (dedup) |
| `DATA_SOURCE` | string | Source system flag (e.g., `HX` for hospitalized) | Hospitalization only |

Columns not listed here (payer plans, ICD versions, HCP flags, referring/rendering provider
IDs) are **dropped** before feature computation. They add shuffle weight without contributing
to any feature.

### 1.2 Raw-Source Column Mapping

The current pipeline reads pre-processed Delta tables where upstream code already renamed
columns. When working from **arbitrary or raw sources**, produce the canonical schema first.

#### Direct Renames (same identifier, different column name)

| Canonical | RX Raw | DX Raw | PX Raw | Lab Raw | Other Common Variants |
| --- | --- | --- | --- | --- | --- |
| `PROVIDER_ID` | `PROVIDER_ID` | `PROVIDER_ID` | `PROVIDER_ID` | `PROVIDER_ID` | `HCP_ID`, `PHYSICIAN_ID`, `PROV_ID` |
| `PATIENT_ID` | `PATIENT_ID` | `PATIENT_ID` | `PATIENT_ID` | `PATIENT_ID` | `MEMBER_ID`, `ENROLLEE_ID`, `SUBSCRIBER_ID` |
| `EVENT_NAME` | `PRODUCT_GROUP` | `DIAGNOSIS_DESCRIPTION` | `PROCEDURE_DESCRIPTION` | `TEST_TYPE` | -- |
| `EVENT_DATE` | `SVC_DT` | `SVC_DT` | `SVC_DT` | `SVC_DT` | `SERVICE_DATE`, `CLAIM_DATE`, `FILL_DT` |
| `CLAIM_ID` | `CLAIM_ID` | `CLAIM_ID` | `CLAIM_ID` | `CLAIM_ID` | `CLAIM_NBR`, `CLAIM_NUMBER` |

#### Identifier Mapping (different identifier system)

When the raw source uses a different identifier system, a lookup/crosswalk table is needed.
This is common when integrating data from multiple vendors or when raw claims use national
identifiers:

| Raw Identifier | Mapping Approach | Target |
| --- | --- | --- |
| `NPI` (National Provider Identifier) | Join to crosswalk table (`NPI` -> `PROVIDER_ID`); broadcast the crosswalk if < 10MB | `PROVIDER_ID` |
| `BHID` (Bayer Healthcare ID) | Direct rename if 1:1 with `PROVIDER_ID`; otherwise crosswalk | `PROVIDER_ID` |
| `PROVIDER_NPI` | Same as `NPI` | `PROVIDER_ID` |

Pattern:
```python
# NPI -> PROVIDER_ID via crosswalk (small dimension, broadcast)
npi_crosswalk = spark.read.format("delta").load(crosswalk_path)
claims = claims.join(F.broadcast(npi_crosswalk), on="NPI", how="inner").drop("NPI")
```

#### IQVIA LAAD Specifics

IQVIA LAAD FCT_RX tables use `PHYSICIAN_ID` or `PROV_ID` for the provider and `FILL_DT` or
`SERVICE_DT` for the date. The product name comes from a DIM_PRD join (`PRODUCT_GROUP` where
`CLAIM_TYPE = 'PD'`). Standardize before loading into the feature pipeline:

```python
claims = (raw_rx
    .select(
        F.col("PHYSICIAN_ID").alias("PROVIDER_ID"),
        F.col("PATIENT_ID"),
        F.col("FILL_DT").cast("date").alias("EVENT_DATE"),
        F.col("PRODUCT_GROUP").alias("EVENT_NAME"),
    )
    .filter(F.col("PROVIDER_ID").isNotNull())
    .filter(F.col("EVENT_NAME").isNotNull())
)
```

### 1.3 Standardization Function

```python
COLUMN_MAP = {
    "PROVIDER_ID": ["PROVIDER_ID", "HCP_ID", "PHYSICIAN_ID", "PROV_ID", "BHID"],
    "PATIENT_ID":  ["PATIENT_ID", "MEMBER_ID", "ENROLLEE_ID", "SUBSCRIBER_ID"],
    "EVENT_NAME":  ["PRODUCT_GROUP", "DIAGNOSIS_DESCRIPTION",
                    "PROCEDURE_DESCRIPTION", "TEST_TYPE"],
    "EVENT_DATE":  ["SVC_DT", "SERVICE_DATE", "CLAIM_DATE", "FILL_DT"],
    "CLAIM_ID":    ["CLAIM_ID", "CLAIM_NBR", "CLAIM_NUMBER"],
}

def standardize(df, event_type):
    for canonical, variants in COLUMN_MAP.items():
        for v in variants:
            if v in df.columns and canonical not in df.columns:
                df = df.withColumnRenamed(v, canonical)
                break
    df = df.withColumn("EVENT_TYPE", F.lit(event_type))
    keep = [c for c in
            ["PROVIDER_ID", "PATIENT_ID", "EVENT_NAME", "EVENT_DATE",
             "EVENT_TYPE", "CLAIM_ID", "DATA_SOURCE"]
            if c in df.columns]
    return df.select(*keep)
```

### 1.4 Hospitalization-Specific Inputs

Hospitalization features (DX and PX only) require **two** input sources:

| Source | Filter | Used For |
| --- | --- | --- |
| Total claims (`dx1_file_path` / `px1_file_path`) | All claims | Denominator (total claim count) |
| Hospitalized claims (`dx_hosp_file_path` / `px_hosp_file_path`) | `DATA_SOURCE = 'HX'` | Numerator (hospitalized claim count) |

Both sources are collapsed to a single event literal: `lit("ALL_DIAGNOSIS")` (DX) or
`lit("ALL_PROCEDURES")` (PX). No per-event breakdown in hospitalization features.

---

## 2. Anchor Dates and Cohort Generation

Each HCP is observed across multiple cohorts (time snapshots). Cohort parameters come from
`00_config`:

| Parameter | Description | Default |
| --- | --- | --- |
| `cohort_start_date` | First anchor date | -- |
| `cohort_end_date` | Last anchor date | -- |
| `months_increment` | Months between cohorts | `2` |
| `lookback_duration` | Days of history per cohort | `365` |
| `prediction_duration` | Days after anchor for label | `90` |
| `cohort_day_offset` | Day of month that starts each custom-month (1 = calendar month) | `1` |

**Derivation per cohort (default, `cohort_day_offset = 1`):**

- `LOOKBACK_END_DATE` = last day of the month, 2 months before the anchor
- `LOOKBACK_START_DATE` = `LOOKBACK_END_DATE - lookback_duration` days
- `HCP_COHORT_ID` = `{PROVIDER_ID}_{COHORT}` (e.g., `PRV123_I01`)
- `SVC_DT_M` = `date_trunc('MM', EVENT_DATE)` (monthly grain for frequency features)
- `EVENT_TIME` = `datediff(LOOKBACK_END_DATE, EVENT_DATE)` (days from event to anchor)

When `cohort_day_offset` is set to a value other than `1`, cohort boundaries shift to
custom-month windows (e.g., offset=15 means each "month" runs from the 15th to the 14th).
See Section 10 for the full custom cohort boundary specification.

Anchor dates are saved to `hcp_model_inference_anchor_dates.csv` for downstream joins.

### 2.1 Default File Paths

When generating notebooks from this skill, pre-fill file paths with the values below (from
`00_config`). Do NOT leave paths as empty strings -- the pipeline will fail with
`FileNotFoundError` at runtime.

**Base paths:**

| Path | Value |
| --- | --- |
| Query output base | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/` |
| Notebook output base | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/` |

**Input claims paths** (under query output base):

| Source | First Occ + Recency | Frequency | Hospitalized (HX) |
| --- | --- | --- | --- |
| RX | `rx_input_claims_total_events_and_first_occ_features_input` | `rx_input_claims_12M_features_input` | -- |
| DX | `dx_input_claims_all_events_features_input` | `dx_input_claims_12M_and_first_occ_features_input` | `dx_hospitalization_claims_all_events_features_input` |
| PX | `px_input_claims_all_events_features_input` | `px_input_claims_12M_and_first_occ_features_input` | `px_hospitalization_claims_all_events_features_input` |
| Lab | `lab_input_claims_12M_and_first_occ_features_input` | -- | -- |

**Output paths** (under notebook output base):

| Variable | Value |
| --- | --- |
| `anchor_dates_path` | `hcp_model_inference_anchor_dates.csv` |
| `hcp_universe_path` | `kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` |
| Feature outputs | `{source}_{feature_type}_features` (e.g., `rx_first_occurrence_features`, `dx_recency_features`) |

---

## 3. Feature Type 1: First Occurrence

### What it answers

*How many days before the anchor date did this event first appear in the patient's journey?*

### How It Works

Raw claims are first collapsed to one row per `(PROVIDER_ID, EVENT_NAME)` pair, recording
only the earliest `EVENT_DATE`. This intermediate -- typically N-million rows -- is then
cross-joined with the cohort anchor dates to compute `EVENT_TIME` and pivot wide. The
alternative of joining 100B raw claims directly against cohort dates before aggregating would
produce a 100B x N_cohorts cross-join that does not scale; the pre-aggregation step is what
makes the pipeline feasible at production data volumes.

```
Step 1: Collapse raw claims
  groupBy(PROVIDER_ID, EVENT_NAME)
    .agg(min(EVENT_DATE) -> FIRST_OCCURRENCE_DATE)
  -> save intermediate to Parquet                    (millions of rows)

Step 2: Attach cohort dates
  intermediate
    .crossJoin(broadcast(cohort_anchor_dates))        (~100 rows, broadcast)
    .withColumn("EVENT_TIME",
        datediff(LOOKBACK_END_DATE, FIRST_OCCURRENCE_DATE))
    .filter(EVENT_TIME >= 0)                          -- future leakage guard

Step 3: Pivot wide
  groupBy(HCP_COHORT_ID)
    .pivot(EVENT_NAME)
    .agg(max(EVENT_TIME))
  -> suffix non-ID columns with "_first_occurrence"
```

### Business Rules

| Rule | Detail | Hard / Tunable |
| --- | --- | --- |
| Lookback scope | Full history (`EVENT_TIME >= 0`, no lower bound) | **Hard** |
| Future leakage guard | `filter(EVENT_TIME >= 0)` after computing `EVENT_TIME` | **Hard** |
| Core aggregation | `max(EVENT_TIME)` per `HCP_COHORT_ID` per `EVENT_NAME` | **Hard** |
| Interpretation | `max(EVENT_TIME)` = earliest event (most days before anchor) | -- |
| Event prevalence filter | `event_prevalence` threshold (0.00 = keep all) | **Tunable** |
| Bypass list | `relevant_rx_events` force-keeps specific drugs (RX only) | **Tunable** |
| Batch size | Cohorts per batch (`batch_size=6`) | **Tunable** |

### Grain

`HCP_COHORT_ID` -- one row per HCP-cohort, one column per distinct `EVENT_NAME`.

### Column Naming

`max(EVENT_TIME)_{EVENT_NAME}_first_occurrence`

Example: `max(EVENT_TIME)_KERENDIA_first_occurrence = 287` means the patient's first Kerendia
prescription was 287 days before the anchor date.

### Cross-Source Variation

| Aspect | RX | DX | PX | Lab |
| --- | --- | --- | --- | --- |
| EVENT_NAME source | `PRODUCT_GROUP` | `DIAGNOSIS_DESCRIPTION` | `PROCEDURE_DESCRIPTION` | `TEST_TYPE` |
| Typical event count | ~29 | ~17 | ~5 | ~2 |

The computation is **identical** across sources -- only `EVENT_NAME` values differ.

### Historical Note

Earlier versions of the pipeline used a direct
`groupBy(HCP_COHORT_ID).pivot(EVENT_NAME).agg(max(EVENT_TIME))` on the full claims table
after joining with cohort dates. This was replaced by the pre-aggregation pattern above
because the 100B-row x N_cohorts cross-join before aggregation does not scale to production
data volumes.

---

## 4. Feature Type 2: Recency

### What it answers

*How recently did events occur, and how concentrated was the activity in the patient's recent
history?*

### Business Rules

| Rule | Detail | Hard / Tunable |
| --- | --- | --- |
| Lookback scope | 12M only: `EVENT_DATE BETWEEN LOOKBACK_START AND LOOKBACK_END` | **Hard** |
| Re-filtering | Claims are re-filtered to 12M, then re-batched | **Hard** |
| Most recent event | `min(EVENT_TIME)` per `HCP_COHORT_ID` per `EVENT_NAME` | **Hard** |
| Time windows | `[30, 60, 90, 180, 270, 360]` days | **Tunable** |
| Event types | `rx`, `dx`, `px`, `lab` (from `EVENT_TYPE` column) | **Hard** |

### The 12M Filter (critical distinction from First Occurrence)

```python
claims_12m = claims.filter(
    (col("EVENT_DATE") >= col("LOOKBACK_START_DATE")) &
    (col("EVENT_DATE") <= col("LOOKBACK_END_DATE"))
)
```

First Occurrence uses **full history** (all events where `EVENT_TIME >= 0`).
Recency uses **only the 12M window**.

### Six Sub-Features (all joined on `HCP_COHORT_ID`)

| # | Sub-Feature | Method | Output Columns | Description |
| --- | --- | --- | --- | --- |
| 1 | Most Recent Event | `min(EVENT_TIME)` pivot | `min(EVENT_TIME)_{EVENT_NAME}_time_min` | Fewest days before anchor = most recent |
| 2 | Total and Unique Events | `count` / `countDistinct` | `total_events`, `unique_events` | Overall volume per HCP-Cohort |
| 3 | Counts by Time Window | filter + count per window | `total_events_time_{N}_days`, `unique_events_time_{N}_days` | Events in last N days |
| 4 | Counts by Type | filter by EVENT_TYPE + count | `total_{type}`, `unique_{type}` | Per event type (rx/dx/px/lab) |
| 5 | Counts by Type x Window | filter by type AND window | `total_events_time_{N}_days_{type}`, `unique_events_time_{N}_days_{type}` | Cross of types x windows |
| 6 | Skewness | `skewness(EVENT_TIME)` per type x window | `skewness_time_{N}_days_{type}` | Concentration of events within window |

### Grain

`HCP_COHORT_ID`

### Column Naming

Sub-feature 1: `min(EVENT_TIME)_{EVENT_NAME}_time_min`
Sub-features 2-6: see table above

### Cross-Source Variation

Computation is identical. `EVENT_TYPE` values (`rx`, `dx`, `px`, `lab`) are assigned during
standardization. Time windows and skewness formula are source-agnostic.

### Business Purpose by Sub-feature

| # | Sub-Feature | Business Purpose |
| --- | --- | --- |
| 1 | Most Recent Event | How recently the HCP last performed this event. A small `EVENT_TIME` (few days) means the event is current in the HCP's practice; a large value means it has not occurred for a long time. This is the simplest recency signal: is this event still part of the HCP's active behavior? |
| 2 | Total and Unique Events | Overall event volume and breadth. `total_events` captures raw activity level (how busy the HCP is); `unique_events` captures diversity (how many distinct event types the HCP engages with). High total with low unique suggests repetitive focus on a few events; high unique suggests broad engagement. |
| 3 | Counts by Time Window | Event density at different recency levels. Comparing counts across windows (e.g., 30 vs 180 vs 360 days) reveals whether activity is increasing or decreasing over time. A HCP with 20 events in 30 days but only 5 in the next 30 is accelerating; the reverse is decelerating. |
| 4 | Counts by Type | The HCP's event-type mix within the lookback period. An HCP with mostly `rx` events is prescription-driven; one with mostly `dx` is diagnosis-driven. This captures the HCP's clinical focus and practice pattern. |
| 5 | Counts by Type x Window | The intersection of event type and recency. This reveals whether the HCP's practice pattern is shifting -- e.g., a HCP whose `rx` count is stable but `dx` count dropped in the last 60 days may be changing their diagnostic focus. The cross provides finer granularity than either dimension alone. |
| 6 | Skewness | Temporal concentration of events within a window x type slice. Input scope: 12M-filtered claims, further filtered to `EVENT_TIME <= N` and `EVENT_TYPE == t`. Returns `NULL` when fewer than 3 events exist in the slice (Spark requires >= 3 values) or when all events share the same `EVENT_TIME` (zero variance). Positive skew = events clustered far back (front-loaded, tapering off); negative skew = events clustered near anchor (recent intensification); zero/null = too few events or evenly spread. Captures acceleration signal that raw counts cannot. |

---

## 5. Feature Type 3: Frequency

### What it answers

*How often does each event occur at the HCP level, and is the rate accelerating or
decelerating?*

Four sub-types, each saved as a separate Delta/Parquet output.

### Sub-type A: Monthly Claim Count

**What it measures:** The raw count of each event per HCP per month. This is the foundational
frequency feature -- a time series of monthly event volumes.

**Input scope:** All standardized claims (no cohort or lookback filter). Every claim is
assigned to its `SVC_DT_M` month and counted per `EVENT_NAME`.

**Business purpose:** Monthly claim count is the baseline signal for all other frequency
sub-types. It captures the HCP's baseline activity level for each event -- is this a
high-volume or low-volume event for this HCP? The monthly time series also reveals seasonality
and trend patterns that feed into the lag and change-in-frequency computations.

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

```
groupBy(PROVIDER_ID, SVC_DT_M)
  .pivot(EVENT_NAME)
  .agg(count(*))
  -> prefix "FREQ_", sanitize column names, uppercase
```

**Column naming:** `FREQ_{EVENT_NAME}` (e.g., `FREQ_KERENDIA`)

**Sanitization rules:** `,` -> removed, `+` -> `and`, `/` -> ` or`, `-` -> `_`, spaces -> `_`,
uppercase.

### Sub-type B: Lag Frequency (Rolling Windows)

**What it measures:** Rolling cumulative event counts over trailing windows of 1, 2, 3, 6,
and 12 months. Each value is the sum of monthly counts in the last N months ending at the
current `SVC_DT_M`.

**Input scope:** Sub-type A output (monthly claim counts). The `fill_missing` step creates a
dense spine by cross-joining all HCPs with all months, ensuring every HCP has a row for every
month (with 0 for months with no activity).

**Business purpose:** Rolling windows smooth out month-to-month noise and capture sustained
activity levels. A 1-month window shows immediate activity; a 12-month window shows the
annual baseline. Comparing across windows (e.g., 1-month vs 12-month) reveals whether recent
activity is above or below the annual norm. These rolling sums are the direct inputs to
Sub-type C (change in frequency).

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

Three-step process:

1. **`fill_missing`** -- Create dense spine: cross-join all distinct `PROVIDER_ID`s with all
   months from min to max date. Left-join original data, `fillna(0)`.

2. **`lag`** -- Rolling window sums via `Window.partitionBy(PROVIDER_ID).orderBy(SVC_DT_M)`:
   ```python
   F.sum(col).over(window.rowsBetween(-i+1, 0))
       .alias(f"{col}_IN_LAST_{i}_MONTH")
   ```

3. **`process_and_join`** -- Orchestrator: `fill_missing` -> `lag` -> drop raw columns,
   keep only `_IN_LAST_` columns + keys.

**Rolling windows:** `[1, 2, 3, 6, 12]` months (**Tunable**)

**Column naming:** `FREQ_{EVENT}_IN_LAST_{N}_MONTH`

### Sub-type C: Change in Frequency

**What it measures:** Whether the HCP's event rate is accelerating or decelerating compared
to its own 12-month baseline. A positive value means recent activity exceeds the remainder
rate; a negative value means it has slowed.

**Input scope:** Sub-type B output (lag frequency rolling sums).

**Business purpose:** Change in frequency detects momentum shifts in an HCP's practice. A
positive value signals the HCP is ramping up activity for this event beyond their own norm;
a negative value signals they are pulling back. This is a leading indicator of behavioral
change that raw counts or rolling sums alone cannot surface.

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

```
CHANGE = (FREQ_{EVENT}_IN_LAST_{N}_MONTH / N_months)
       - ((FREQ_{EVENT}_IN_LAST_12_MONTH - FREQ_{EVENT}_IN_LAST_{N}_MONTH) / (12 - N_months))
```

**Recent windows:** `[1, 2, 3, 6]` (12M is the baseline, not computed)

**Column naming:** `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_{EVENT}_IN_LAST_{N}_MONTH`

After computing, raw `FREQ_*_IN_LAST_*` columns are **dropped**.

**Prerequisite:** HCP universe cross-join with cohort anchor dates:
```python
hcp_universe = hcp_universe.crossJoin(cohort_anchor_dates)
lag_freq = hcp_universe.join(lag_freq, on=["PROVIDER_ID", "SVC_DT_M"], how="inner")
```

### Sub-type D: Unique Patient Counts per HCP

**What it measures:** The number of distinct patients an HCP has seen for each event type
within time windows from the cohort's lookback end date.

**Input scope:** All standardized claims, cross-joined with cohort anchor dates, then filtered
to `EVENT_DATE BETWEEN LOOKBACK_START AND LOOKBACK_END`. Patients are deduplicated per
`[PROVIDER_ID, COHORT, EVENT_NAME, PATIENT_ID]` before counting.

**Business purpose:** Unique patient count measures the HCP's patient reach for each event
type. Two HCPs with the same total claim count may differ in patient breadth: one seeing 100
patients once each vs another seeing 10 patients 10 times each. Patient reach is a stronger
signal for market opportunity and HCP influence than raw claim volume.

**Grain:** `[PROVIDER_ID, COHORT]` (NOT monthly)

| Step | Operation |
| --- | --- |
| 1 | Cross-join claims with `hcp_model_inference_anchor_dates.csv` (broadcast) |
| 2 | Filter: `EVENT_DATE BETWEEN LOOKBACK_START AND LOOKBACK_END` |
| 3 | `days_diff = datediff(LOOKBACK_END_DATE, EVENT_DATE)` |
| 4 | Flag: `when(days_diff <= N, 1).otherwise(0)` for each window |
| 5 | Dedup on `[PROVIDER_ID, COHORT, EVENT_NAME, PATIENT_ID]` |
| 6 | `countDistinct(PATIENT_ID)` per `[PROVIDER_ID, COHORT, EVENT_NAME]` per flag |
| 7 | Unpivot -> Pivot wide with descriptive column names |

**Time windows:** `[30, 60, 90, 180, 360]` days (**Tunable**)

**Column naming (varies by claim type):**

| Claim | Prefix |
| --- | --- |
| RX | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_{EVENT}_IN_LAST_{N}_DAYS` |
| DX | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_{EVENT}_IN_LAST_{N}_DAYS` |
| PX | `NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_{EVENT}_IN_LAST_{N}_DAYS` |
| Lab | `NUM_OF_PATIENTS_THE_HCP_DID_LAB_TEST_{EVENT}_IN_LAST_{N}_DAYS` |

### Hard Constraints vs Tunable Parameters

| Parameter | Value | Type |
| --- | --- | --- |
| Monthly grain (Sub-types A-C) | `PROVIDER_ID x SVC_DT_M` | **Hard** |
| Cohort grain (Sub-type D) | `PROVIDER_ID x COHORT` | **Hard** |
| Lag rolling windows | `[1, 2, 3, 6, 12]` months | **Tunable** |
| Change recent windows | `[1, 2, 3, 6]` (excludes 12) | **Tunable** |
| Patient count time windows | `[30, 60, 90, 180, 360]` days | **Tunable** |
| Column sanitization rules | Character replacement map | **Hard** |

---

## 6. Feature Type 4: Hospitalization

### What it answers

*What fraction of an HCP's claims involve hospitalized patients, and how many unique
hospitalized patients did the HCP see?*

**DX and PX only** -- no RX or Lab hospitalization features exist.

### Key Design Decisions

1. **Single collapsed event** -- no per-event breakdown. All claims collapsed to
   `lit("ALL_DIAGNOSIS")` (DX) or `lit("ALL_PROCEDURES")` (PX).
2. **Two input sources** -- total claims + hospitalized-only claims (`DATA_SOURCE='HX'`).
3. **HCP flags dropped** -- `KERENDIA_FLAG`, `SGLT2_GLP1_FLAG`, `NEPH_FLAG`,
   `TARGETING_HCP_FLAG`, `BPT_HCP_FLAG` removed from hospitalized claims.
4. **Rolling windows** -- `[1, 6, 12]` months (shorter than frequency's `[1, 2, 3, 6, 12]`).
5. **Validation filter** -- rows where `TOTAL < HOSPITALIZED` are removed (data quality).

### Sub-type A: Total and Hospitalized Claim Counts

**What it measures:** The total number of claims and the number of hospitalized-patient
claims per HCP per month. Since events are collapsed to a single `ALL_DIAGNOSIS` or
`ALL_PROCEDURES` literal, each source produces one count column.

**Input scope:** Two sources: (1) all claims for the total count, (2) claims filtered to
`DATA_SOURCE = 'HX'` for the hospitalized count. Both are grouped by `[PROVIDER_ID, SVC_DT_M]`
and pivoted on the collapsed event column.

**Business purpose:** These counts are the building blocks for Sub-type C (percent
hospitalized). The total count captures the HCP's overall volume; the hospitalized count
captures the subset involving inpatient stays. The ratio between them (computed in Sub-type C)
is the primary hospitalization feature.

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

```
total_claims = groupBy(index_cols).pivot(EVENT_COL).agg(count(*))  -> TOTAL_CLAIMS_{EVENT}
hosp_claims  = groupBy(index_cols).pivot(EVENT_COL).agg(count(*))  -> TOTAL_HOSPITALIZED_CLAIMS_{EVENT}
combined = total.join(hosp, how='left').fillna(0)
```

Since events are collapsed, this produces only:
- `TOTAL_CLAIMS_ALL_DIAGNOSIS` + `TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS` (DX)
- `TOTAL_CLAIMS_ALL_PROCEDURES` + `TOTAL_HOSPITALIZED_CLAIMS_ALL_PROCEDURES` (PX)

### Sub-type B: Lag Hospitalized Counts

**What it measures:** Rolling cumulative total and hospitalized claim counts over trailing
windows of 1, 6, and 12 months. Same `fill_missing` -> `lag` -> `process_and_join` pattern as
Frequency Sub-type B, but applied to both total and hospitalized claim counts.

**Input scope:** Sub-type A output (total and hospitalized monthly counts). The dense spine
and rolling window logic are identical to Frequency Sub-type B.

**Column naming:** `TOTAL_CLAIMS_{EVENT}_IN_LAST_{N}_MONTH` and
`TOTAL_HOSPITALIZED_CLAIMS_{EVENT}_IN_LAST_{N}_MONTH`.

**Business purpose:** Rolling window counts smooth month-to-month variation in
hospitalization rates. The validation filter (TOTAL >= HOSPITALIZED at every window) ensures
data quality before percentages are computed. These rolling counts feed directly into
Sub-type C (percent hospitalized).

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

Same `fill_missing` -> `lag` -> `process_and_join` pattern as Frequency Sub-type B, but:
- **Rolling windows:** `[1, 6, 12]` months
- **Validation filter:** Remove rows where any `TOTAL_CLAIMS_*_IN_LAST_*` <
  corresponding `TOTAL_HOSPITALIZED_CLAIMS_*_IN_LAST_*`:
  ```python
  lag = lag.filter(
      (col("TOTAL_CLAIMS_ALL_DIAGNOSIS_IN_LAST_1_MONTH") >=
       col("TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_1_MONTH")) &
      (col("TOTAL_CLAIMS_ALL_DIAGNOSIS_IN_LAST_6_MONTH") >=
       col("TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_6_MONTH")) &
      (col("TOTAL_CLAIMS_ALL_DIAGNOSIS_IN_LAST_12_MONTH") >=
       col("TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_12_MONTH"))
  )
  ```

### Sub-type C: Percent Hospitalized

**What it measures:** The fraction of an HCP's claims that involve hospitalized patients,
computed over rolling windows. A value of 0.15 means 15% of the HCP's claims in the last N
months were for hospitalized patients.

**Input scope:** Sub-type B output (lag total and hospitalized claim counts).

**Business purpose:** Percent hospitalized captures the severity of the HCP's patient mix.
An HCP with a high hospitalization percentage treats sicker patients (more inpatient stays);
one with a low percentage sees primarily outpatient cases. This severity signal helps
distinguish HCPs who manage complex, hospitalized cases from those focused on routine
outpatient care.

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

```
PERC = WHEN TOTAL_CLAIMS_{EVENT}_IN_LAST_{N}_MONTH != 0
       THEN TOTAL_HOSPITALIZED_CLAIMS_{EVENT}_IN_LAST_{N}_MONTH
            / TOTAL_CLAIMS_{EVENT}_IN_LAST_{N}_MONTH
       ELSE NULL
```

**Windows:** `[1, 6, 12]` months

After computing percent: `TOTAL_CLAIMS_*_IN_LAST_*` columns are **dropped**.
Kept: `PERC_HOSPITALIZED_*` + `TOTAL_HOSPITALIZED_*` + key columns.

**Column naming:** `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_{EVENT}_IN_LAST_{N}_MONTH`

### Sub-type D: Unique Hospitalized Patient Counts

**What it measures:** The number of distinct hospitalized patients an HCP has seen within time
windows from the cohort's lookback end date.

**Input scope:** Hospitalized claims only (`DATA_SOURCE = 'HX'`), using the same cohort
cross-join pattern as Frequency Sub-type D. Time windows are `[30, 180, 360]` days (NOT
`[30, 60, 90, 180, 360]`).

**Business purpose:** Unique hospitalized patient count measures the HCP's reach among
severely ill patients. An HCP with 50 unique hospitalized patients has a broader inpatient
practice than one with 5, even if their total claim counts are similar. This complements the
percent-hospitalized feature: percentage captures intensity, unique count captures breadth.

**Grain:** `[PROVIDER_ID, COHORT]`

**Column naming:**

| Claim | Prefix |
| --- | --- |
| DX | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DIAGNOSED_IN_LAST_{N}_DAYS` |
| PX | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DID_PROCEDURE_IN_LAST_{N}_DAYS` |

### Combine Everything

Both notebooks end with a "Combine Everything" section:

1. Build `skeleton_df` from `hcp_universe x cohort_anchor_dates` with `HCP_COHORT_ID`
2. Join percent-hospitalized features on `[PROVIDER_ID, SVC_DT_M]`
3. Join num-hospitalized-patient counts on `[PROVIDER_ID, COHORT]`
4. Both join on `HCP_COHORT_ID`
5. **PX adds `_PX` suffix** to all non-key columns to avoid name collisions with DX

### Hard Constraints vs Tunable Parameters

| Parameter | Value | Type |
| --- | --- | --- |
| Applicable sources | DX, PX only | **Hard** |
| Event collapse | Single `ALL_DIAGNOSIS` / `ALL_PROCEDURES` | **Hard** |
| Validation filter | TOTAL >= HOSPITALIZED | **Hard** |
| Percent formula | HOSP / TOTAL WHEN TOTAL != 0 ELSE NULL | **Hard** |
| Lag windows | `[1, 6, 12]` months | **Tunable** |
| Patient count windows | `[30, 180, 360]` days | **Tunable** |
| PX suffix | `_PX` on non-key columns | **Hard** (convention) |

---

## 7. Performance Guidance for ~100B Rows

### 7.1 Pre-Aggregation Before Cohort Expansion

The single most impactful pattern for any feature that needs a per-HCP aggregate before
cross-joining with cohort dates. The core principle: collapse ~100B raw claims to a narrow
per-HCP (or per-HCP-event) intermediate **before** attaching cohort dates, so the cross-join
operates on millions of rows rather than 100B.

First Occurrence already uses this as its default method -- see Section 3 for the full
step-by-step. The same pattern applies wherever an aggregate over raw claims must then be
repeated across cohorts:

**Recency `min(EVENT_TIME)` (Sub-feature 1):** Pre-aggregate raw claims to
`(PROVIDER_ID, EVENT_NAME, LATEST_EVENT_DATE)` using `groupBy(PROVIDER_ID, EVENT_NAME).agg(max(EVENT_DATE))`
before the cohort cross-join, then compute `EVENT_TIME = datediff(LOOKBACK_END_DATE, LATEST_EVENT_DATE)`.
This avoids attaching cohort rows to every individual claim before finding the most recent one.

General rule: if the computation is `agg(f(EVENT_DATE))` per `(PROVIDER_ID, EVENT_NAME)`, it
can always be pre-aggregated. The cross-join that would be 100B x N_cohorts becomes
millions x N_cohorts.

### 7.2 Broadcast Joins vs Shuffle Joins

| Table | Typical Size | Join Strategy |
| --- | --- | --- |
| Cohort anchor dates CSV | ~100 rows | **Broadcast** always |
| HCP universe | ~100K rows | **Broadcast** if < 10MB |
| Event prevalence filter | ~hundreds of events | **Broadcast** |
| NPI crosswalk | ~1M rows | **Broadcast** if memory allows |
| Claims x claims joins | 100B+ rows | **Shuffle** (never broadcast) |

```python
# Small dimension: broadcast
claims = claims.join(F.broadcast(anchor_dates), ...)

# Large fact-to-fact: let Spark shuffle
result = big_df1.join(big_df2, on="key", how="inner")
```

### 7.3 Caching and Persisting

| Intermediate | Action | Why |
| --- | --- | --- |
| Dense spine (after `fill_missing`) | `cache()` | Read N times by `step3_lag` (once per window) |
| Standardized claims | `persist(DISK_ONLY)` | Reused across feature types; too large for memory |
| Batch results (before union) | No cache -- write to Delta immediately | Frees memory |
| Pivoted result | No cache -- write immediately | Wide DataFrame, expensive to cache |

**Rule of thumb:** `cache()` for DataFrames read 2+ times in the same action chain.
`persist(DISK_ONLY)` for DataFrames reused across separate feature computations.
Never cache a wide pivoted result -- write it to storage instead.

### 7.4 Write Intermediates to Parquet / Delta

When a pipeline stage produces a large intermediate that feeds multiple downstream stages,
write it to storage and read it back rather than chaining in memory:

```python
# Bad: chained in memory -- Spark can't optimize across complex stages
result = stage3(stage2(stage1(raw)))

# Better: checkpoint intermediates
stage1_output.write.format("parquet").save(intermediate_path)
stage1_df = spark.read.parquet(intermediate_path)
stage2_output = stage2(stage1_df)
stage2_output.write.format("delta").save(another_intermediate)
```

**When to do this:**
- After pre-aggregation (before cohort cross-join)
- After `fill_missing` (dense spine is expensive to recreate)
- After any pivot (wide DataFrames are expensive to hold in memory)

### 7.5 Batch Processing by Cohort

The `DataFrameBatchProcessor` splits claims by COHORT suffix into batches of `batch_size`
(default 6). Each batch is processed independently, then merged via
`unionByName(allowMissingColumns=True)`.

**When to increase `batch_size`:** Small cohorts, limited total data -- fewer batches means
less union overhead.

**When to decrease:** OOM on wide pivots -- smaller batches reduce peak memory per stage.

**Key benefit:** Batches with different `EVENT_NAME` values produce different pivot columns.
`allowMissingColumns=True` in the union fills absent columns with null.

### 7.6 Early Column Pruning

Drop non-essential columns **immediately** after load, before any join or aggregation:

```python
claims = claims.select(
    "PROVIDER_ID", "PATIENT_ID", "EVENT_NAME", "EVENT_DATE",
    "EVENT_TYPE", "CLAIM_ID"
)
```

Every extra column in a shuffle stage costs bytes-per-row x number-of-rows. At 100B rows,
dropping 10 unnecessary columns before a shuffle can save terabytes of I/O.

### 7.7 Partitioning Strategy for Final Output

| Output | Partition By | Rationale |
| --- | --- | --- |
| First Occurrence, Recency | `COHORT` | Model training reads one cohort at a time |
| Frequency (monthly grain) | `SVC_DT_M` | Time-series reads slice by month |
| Frequency (cohort grain, Sub-D) | `COHORT` | Same as above |
| Hospitalization | `COHORT` | Same as above |

```python
df.write.format("delta").mode("overwrite")
  .partitionBy("COHORT")
  .save(output_path)
```

Partition pruning on `WHERE COHORT = 'I01'` avoids reading all cohorts.

### 7.8 Avoiding Pivot Explosion

When `EVENT_NAME` cardinality is high (>500 distinct values), the pivot produces a very wide
DataFrame. Controls:

1. **Event prevalence filter** -- `event_prevalence` threshold (e.g., 0.01 = keep events seen
   by >= 1% of HCPs). Primary control for column count.
2. **Bypass list** -- `relevant_rx_events` forces specific events through the filter.
3. **Batch by EVENT_NAME buckets** -- if filter alone is not enough, split events into
   buckets, pivot each separately, then join.

---

## 8. Final Output Schema and Join Strategy

### 8.1 Join Key

All feature outputs share a common key that enables a single unified feature table:

| Feature Type | Key | Grain |
| --- | --- | --- |
| First Occurrence | `HCP_COHORT_ID` | HCP x Cohort |
| Recency | `HCP_COHORT_ID` | HCP x Cohort |
| Frequency Sub-types A-C | `PROVIDER_ID, SVC_DT_M` | HCP x Month |
| Frequency Sub-type D | `PROVIDER_ID, COHORT` | HCP x Cohort |
| Hospitalization Sub-types A-C | `PROVIDER_ID, SVC_DT_M` | HCP x Month |
| Hospitalization Sub-type D | `PROVIDER_ID, COHORT` | HCP x Cohort |

**Unification key:** `HCP_COHORT_ID` = `{PROVIDER_ID}_{COHORT}`

Monthly-grain features (Frequency A-C, Hospitalization A-C) must be joined to cohort anchor
dates to convert `SVC_DT_M` -> `COHORT` -> `HCP_COHORT_ID` before merging with patient-level
features.

### 8.2 Join Strategy

```
Step 1: Build skeleton
  hcp_universe x cohort_anchor_dates -> skeleton(PROVIDER_ID, COHORT, HCP_COHORT_ID, SVC_DT_M)

Step 2: Join patient-level features (HCP_COHORT_ID grain)
  skeleton LEFT JOIN first_occurrence ON HCP_COHORT_ID
  skeleton LEFT JOIN recency ON HCP_COHORT_ID

Step 3: Join HCP-month features (convert to HCP_COHORT_ID via SVC_DT_M)
  skeleton LEFT JOIN frequency_subABC ON [PROVIDER_ID, SVC_DT_M]
  skeleton LEFT JOIN hospitalization_subABC ON [PROVIDER_ID, SVC_DT_M]

Step 4: Join HCP-cohort features
  skeleton LEFT JOIN frequency_subD ON [PROVIDER_ID, COHORT]
  skeleton LEFT JOIN hospitalization_subD ON [PROVIDER_ID, COHORT]

Step 5: Add source suffixes to avoid collisions
  RX features: no suffix (baseline)
  DX features: no suffix (or _DX if collision)
  PX features: _PX suffix
  Lab features: _LAB suffix
```

### 8.3 Final Output Schema

```
HCP_COHORT_ID          -- composite key: {PROVIDER_ID}_{COHORT}
PROVIDER_ID            -- HCP identifier
COHORT                 -- cohort label (I01, I02, ...)

-- First Occurrence (per source x per event)
max(EVENT_TIME)_{EVENT_NAME}_first_occurrence    -- int (days before anchor)

-- Recency (per source)
min(EVENT_TIME)_{EVENT_NAME}_time_min            -- int (days, most recent)
total_events, unique_events                      -- int
total_events_time_{N}_days, unique_events_time_{N}_days  -- int per window
total_{type}, unique_{type}                      -- int per event type
total_events_time_{N}_days_{type}               -- int per type x window
unique_events_time_{N}_days_{type}              -- int per type x window
skewness_time_{N}_days_{type}                   -- float per type x window

-- Frequency (per source x per event)
FREQ_{EVENT}_IN_LAST_{N}_MONTH                   -- int (rolling sum)
CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_{EVENT}_IN_LAST_{N}_MONTH  -- float
NUM_OF_PATIENTS_..._{EVENT}_IN_LAST_{N}_DAYS     -- int (distinct patients)

-- Hospitalization (DX, PX only)
PERC_HOSPITALIZED_HCP_CLAIMS_FOR_{EVENT}_IN_LAST_{N}_MONTH  -- float (0-1)
TOTAL_HOSPITALIZED_CLAIMS_{EVENT}_IN_LAST_{N}_MONTH         -- int
NUM_OF_HOSPITALIZED_PATIENTS_..._IN_LAST_{N}_DAYS           -- int
```

### 8.4 Output Volume Estimate

| Component | Formula | Approx. Columns |
| --- | --- | --- |
| First Occurrence | 1 per EVENT_NAME x 4 sources | ~53 |
| Recency (sub-features 1-6) | ~94 + per-event columns | ~94 + ~53 |
| Frequency (Sub-types A-D) | 4 sub-types x per-event x per-window | ~500+ |
| Hospitalization (Sub-types A-D) | DX + PX, collapsed events | ~30 |
| **Total** | | **~700+** |

---

## 9. Parameter Summary

| Parameter | Location | Default | Scope | Tunable? |
| --- | --- | --- | --- | --- |
| `cohort_start_date` | `00_config` | -- | All features | Yes |
| `cohort_end_date` | `00_config` | -- | All features | Yes |
| `months_increment` | `00_config` | `2` | All features | Yes |
| `lookback_duration` | `00_config` | `365` (days) | All features | Yes |
| `prediction_duration` | `00_config` | `90` (days) | Labels (not features) | Yes |
| `event_prevalence` | `00_config` | `0.00` | First Occ, Recency | Yes |
| `relevant_rx_events` | `00_config` | `['STEGLATRO','INVOKANA','KERENDIA']` | RX First Occ, Recency | Yes |
| `time_windows` (recency) | `00_config` | `[30, 60, 90, 180, 270, 360]` | Recency | Yes |
| Lag windows (freq) | inline in notebooks | `[1, 2, 3, 6, 12]` | Freq Sub-B, Hosp Sub-B | Yes |
| Change windows (freq) | inline in notebooks | `[1, 2, 3, 6]` | Freq Sub-C | Yes |
| Patient count windows (freq) | inline in notebooks | `[30, 60, 90, 180, 360]` | Freq Sub-D | Yes |
| Hosp patient count windows | inline in notebooks | `[30, 180, 360]` | Hosp Sub-D | Yes |
| `batch_size` | `DataFrameBatchProcessor` | `6` | First Occ, Recency | Yes |
| `cohort_day_offset` | `00_config` | `1` | All features (opt-in) | Yes |
| `rx_file_path` | `00_config` | `query_output/rx_input_claims_total_events_and_first_occ_features_input` | RX First Occ, Recency | Yes |
| `dx_file_path` | `00_config` | `query_output/dx_input_claims_all_events_features_input` | DX First Occ, Recency | Yes |
| `px_file_path` | `00_config` | `query_output/px_input_claims_all_events_features_input` | PX First Occ, Recency | Yes |
| `lab_file_path` | `00_config` | `query_output/lab_input_claims_12M_and_first_occ_features_input` | Lab First Occ, Recency | Yes |
| `output_base_path` | `00_config` | `notebook_output/` | All feature outputs | Yes |
| `anchor_dates_path` | `00_config` | `notebook_output/hcp_model_inference_anchor_dates.csv` | All features | Yes |
| `hcp_universe_path` | `00_config` | `notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` | Freq Sub-C/D, Hosp | Yes |

See Section 2.1 for full default file paths. Do NOT leave path variables as empty strings.

---

## 10. Custom Cohort Date Boundaries

By default, cohorts align to calendar months: each "month" runs from the 1st to the last
day of the month, and `SVC_DT_M = date_trunc('MM', EVENT_DATE)` snaps events to the 1st. When
`cohort_day_offset` is set to a value other than `1`, cohort boundaries shift to custom-month
windows. For example, `cohort_day_offset = 15` means each custom-month runs from the 15th of
one calendar month to the 14th of the next.

Cohorts snap to actual calendar dates -- each cohort's length equals the real number of days
between its start and end. Jan 15 to Feb 14 is 31 days, Feb 15 to Mar 14 is 28 days (or 29
in a leap year), Mar 15 to Apr 14 is 31 days. Cohorts are NOT fixed 30-day windows that drift
from the calendar; users can always point at a cohort and say "that is the 15th of month X
to the 14th of month X+1."

### 10.1 Configuration

A single parameter controls the behavior:

| Parameter | Default | Description |
| --- | --- | --- |
| `cohort_day_offset` | `1` | Day of month that starts each custom-month. `1` = calendar month (backward compatible). Valid range: 1-28. |

**Why 1-28:** Every calendar month has days 1-28, so offsets in this range guarantee that
the boundary day always exists. Offsets 29-31 are problematic because February (and some
months in 30-day calendars) lack those days. Use offset 28 if you need the latest possible
start date.

The offset feeds into two derivations:

**LOOKBACK_END_DATE:**

```
# Default (offset=1): last day of month, 2 months before anchor
# Custom (offset=D): last day of custom-month, 2 custom-months before anchor

custom_month_start = when(dayofmonth(anchor) >= offset,
                          date_add(date_trunc('MM', anchor), offset - 1))
                    .otherwise(
                          date_add(add_months(date_trunc('MM', anchor), -1), offset - 1))

LOOKBACK_END_DATE = date_sub(add_months(custom_month_start, -1), 1)
```

In plain terms: `LOOKBACK_END_DATE = add_months(anchor_custom_month_start, -2) - 1 day`.
Equivalently, go to the start of the custom-month that contains the anchor, step back 2
custom-months, then subtract 1 day to land on the last day of that earlier custom-month.

Example with `offset=15`, anchor = `2024-04-15`:
- Custom-month start = `2024-04-15`
- `add_months(2024-04-15, -1)` = `2024-03-15`
- `LOOKBACK_END_DATE = date_sub(2024-03-15, 1)` = `2024-03-14`

**LOOKBACK_START_DATE:** `LOOKBACK_END_DATE - lookback_duration` days -- unchanged from the
default pipeline. The start date is always a fixed day-count back from the end date, not a
custom-month boundary. This is intentional: the lookback window is a rolling N-day history
ending at `LOOKBACK_END_DATE`, not a fixed number of custom-months. Only `LOOKBACK_END_DATE`
shifts with the offset; `LOOKBACK_START_DATE` follows it by simple subtraction.

**SVC_DT_M (custom-month bucket):**

The standard `date_trunc('MM', EVENT_DATE)` is replaced with a custom bucketing function:

```python
def custom_month_bucket(event_date, offset):
    """Assign event_date to its custom-month bucket start date.

    With offset=1: equivalent to date_trunc('MM', event_date).
    With offset=15: April 20 -> April 15 (belongs to Apr 15 to May 14 bucket).
                    April 10 -> March 15 (belongs to Mar 15 to Apr 14 bucket).
    """
    month_start = F.date_trunc('MM', event_date)
    return F.when(
        F.dayofmonth(event_date) >= offset,
        F.date_add(month_start, offset - 1)
    ).otherwise(
        F.date_add(F.add_months(month_start, -1), offset - 1)
    )
```

Verification: offset=1, event on April 20 -> dayofmonth=20 >= 1 ->
date_add(2024-04-01, 0) = 2024-04-01. Matches `date_trunc('MM')`. Backward compatible.

### 10.2 Affected Feature Types

Custom bucketing affects only features that use `SVC_DT_M` as a grouping or ordering key:

| Feature Type | Uses SVC_DT_M? | Impact |
| --- | --- | --- |
| First Occurrence | No | None -- uses `EVENT_TIME` (days since anchor) |
| Recency | No | None -- uses `EVENT_TIME` (days since anchor) |
| Frequency Sub-A (Claim Count) | **Yes** | `groupBy(PROVIDER_ID, SVC_DT_M)` -- bucket assignment changes |
| Frequency Sub-B (Lag) | **Yes** | `fill_missing` + `lag` -- spine generation and window ordering change |
| Frequency Sub-C (Change) | **Yes** | Inherits from Sub-B -- denominator semantics affected (see 10.4) |
| Frequency Sub-D (Patient Counts) | No | Uses `COHORT` and `days_diff` -- not bucketed by month |
| Hospitalization Sub-A (Counts) | **Yes** | Same as Frequency Sub-A |
| Hospitalization Sub-B (Lag) | **Yes** | Same as Frequency Sub-B |
| Hospitalization Sub-C (% Hosp) | **Yes** | Inherits from Sub-B |
| Hospitalization Sub-D (Hosp Patients) | No | Uses `COHORT` and `days_diff` -- not bucketed by month |

### 10.3 Changes to Monthly Bucketing

**Sub-types A (Claim Count):** Replace `date_trunc('MM', EVENT_DATE)` with
`custom_month_bucket(EVENT_DATE, offset)` in the `withColumn("SVC_DT_M", ...)` step.
Everything else -- the pivot, column sanitization, prefix -- stays the same.

**Sub-types B (Lag):** Two changes:

1. **Dense spine generation:** The `fill_missing` function generates a date sequence via
   `sequence(min_date, max_date, interval 1 month)`. Since `SVC_DT_M` now contains custom
   bucket dates (e.g., `2024-01-15`, `2024-02-15`, ...), the sequence produces the correct
   custom-month boundaries. Spark's `add_months` handles variable-length months correctly
   when incrementing by 1 month from a fixed day-of-month.

2. **Window ordering:** `Window.partitionBy(PROVIDER_ID).orderBy(SVC_DT_M)` still works
   correctly -- the custom bucket dates are monotonically increasing and properly ordered.

The `rowsBetween(-i+1, 0)` clause counts N rows back, which now corresponds to N
custom-months rather than N calendar months. This is the desired behavior: "last 3 months"
means "last 3 custom-months" regardless of their day counts.

### 10.4 Variable-Length Cohorts and Rolling Windows

Each custom-month spans a variable number of days:

| Custom-Month | Day Count |
| --- | --- |
| Jan 15 to Feb 14 | 31 |
| Feb 15 to Mar 14 | 28 (or 29 in leap year) |
| Mar 15 to Apr 14 | 31 |
| Apr 15 to May 14 | 30 |

The lag windows (`[1, 2, 3, 6, 12]` months) mean "last N custom-months." A 3-month lag
window covering Feb 15 to May 14 spans 28+31+30 = 89 days (or 90 in a leap year), while the
next 3-month window (Mar 15 to Jun 14) spans 31+30+31 = 92 days. The raw event counts in
these windows will differ partly due to the day-count variation.

**Impact on Change-in-Frequency (Sub-type C):**

The formula normalizes by month count, not day count:

```
CHANGE = (FREQ_IN_LAST_N / N) - ((FREQ_IN_LAST_12 - FREQ_IN_LAST_N) / (12 - N))
```

Here, `N` is the number of custom-months (e.g., 3), not days. The comparison is "average
events per custom-month" in the recent window vs the remainder. Since custom-months vary by
+/-3 days (28-31), the per-month rate has a small day-count bias:

- A 1-month window in February (28 days) will tend to have slightly fewer events than a
  1-month window in March (31 days), even if the daily rate is identical.
- This bias is ~10% at most (28/31 = 0.90) and is the same bias that exists with calendar
  months in the default mode.

**When this matters:** If precise per-day normalization is needed, replace the denominator
with actual day counts:

```
CHANGE_PER_DAY = (FREQ_IN_LAST_N / days_in_window)
               - ((FREQ_IN_LAST_12 - FREQ_IN_LAST_N) / (days_in_12M - days_in_window))
```

where `days_in_window` is computed from the custom-month boundaries. This changes the feature
semantics (per-day rate vs per-month rate) and should be a deliberate choice. The default
per-month normalization is recommended for consistency with the existing pipeline.

**No impact on First Occurrence, Recency, Freq Sub-D, and Hosp Sub-D:**

These features use `EVENT_TIME` (days since anchor) or `days_diff` (days from lookback end),
both of which are day-based and independent of monthly bucketing. Only `LOOKBACK_END_DATE`
must be set correctly from the custom boundary (Section 10.1 formula).

### 10.5 What Stays Unchanged

| Component | Why it is unaffected |
| --- | --- |
| First Occurrence logic | `max(EVENT_TIME)` per `HCP_COHORT_ID` -- `EVENT_TIME` is day-based. **Note:** the computation logic is unchanged, but output values will differ from the default because `LOOKBACK_END_DATE` moves with the offset -- every `EVENT_TIME = datediff(LOOKBACK_END_DATE, EVENT_DATE)` shifts by however many days the anchor moved. |
| Recency 12M filter | `EVENT_DATE BETWEEN LOOKBACK_START AND LOOKBACK_END` -- uses dates, not buckets. **Note:** same caveat -- the filter bounds shift with `LOOKBACK_END_DATE`, so the 12M window covers a different calendar range and all time-window/skewness outputs will differ. |
| Recency time windows | `[30, 60, 90, 180, 270, 360]` are in days, not months |
| Recency skewness | `skewness(EVENT_TIME)` -- `EVENT_TIME` is day-based |
| Freq Sub-D patient counts | `days_diff` + day-based window flags -- not bucketed by month |
| Hosp Sub-D patient counts | Same as Freq Sub-D |
| Column naming conventions | Unchanged -- `_IN_LAST_{N}_MONTH` still refers to N custom-months |
| Column sanitization rules | Unchanged |
| Event prevalence filter | Unchanged |
| Batch processing | Unchanged -- batches by COHORT suffix, not by month |
| Performance patterns | Unchanged -- pre-aggregation, broadcast joins, caching all apply |

### 10.6 Backward Compatibility

`cohort_day_offset = 1` (default) reproduces the existing calendar-month behavior exactly:

| Derivation | offset=1 | Equivalent to |
| --- | --- | --- |
| Custom bucket | `date_add(date_trunc('MM', dt), 0)` | `date_trunc('MM', dt)` |
| LOOKBACK_END_DATE | `date_sub(add_months(date_trunc('MM', anchor), -1), 1)` | last day of month, 2 months before anchor |

No code changes are needed when `cohort_day_offset` is not set or is set to `1`. Custom
offsets are purely opt-in.

### 10.7 Edge Cases

**Short months (February):**

With `offset=15`, the custom-month Feb 15 to Mar 14 is 28 days (or 29 in a leap year),
shorter than the 30-31 day span of other custom-months. This affects:

- Lag window raw counts: A 1-month lag in February captures 3 fewer days than in March.
- Change-in-frequency: The per-month normalization absorbs this -- the denominator is N=1
  regardless of day count. The per-day bias is ~10% at worst.
- Dense spine: `sequence(min_date, max_date, interval 1 month)` correctly generates
  Feb 15 and Mar 15 as consecutive bucket dates regardless of February's length.

**Year-end rollover (Dec 15 to Jan 14):**

`add_months` handles year boundaries correctly:
- `add_months('2024-12-15', 1)` = `2025-01-15`
- `add_months('2025-01-15', -1)` = `2024-12-15`

The `sequence()` function and custom bucketing both rely on `add_months`, so year-end
rollovers work without special handling.

**Leap years:**

With `offset=15`, the custom-month Feb 15 to Mar 14 is 29 days in a leap year (e.g., 2024)
vs 28 days in a non-leap year (e.g., 2025). This means the same lag window covers one more
day of data in leap years. The impact is negligible for feature semantics and is the same
effect that exists with calendar-month bucketing (February has 28/29 days).

**Offset on day 29-31:**

Not recommended. February never has day 29-31 (except Feb 29 in leap years), so
`date_add(date_trunc('MM', '2024-02-01'), 28)` = Feb 29 in a leap year but would need
special handling in non-leap years. Restrict `cohort_day_offset` to 1-28 for safety.