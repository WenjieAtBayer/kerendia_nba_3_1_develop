# Hospitalization Features — Query & Exploration Template

Hospitalization features are **DX and PX only**. All are pre-materialized as Delta.

## Reading Pre-Materialized Outputs

```python
BASE = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output"

# Sub-type C: % Hospitalized (grain: PROVIDER_ID × SVC_DT_M)
dx_perc_hosp = spark.read.format("delta").load(f"{BASE}/dx_percentage_hospitalized_features")
px_perc_hosp = spark.read.format("delta").load(f"{BASE}/px_percentage_hospitalized_features")

# Sub-type D: Unique Hospitalized Patient Counts (grain: PROVIDER_ID × COHORT)
dx_hosp_pts = spark.read.format("delta").load(f"{BASE}/dx_num_hospitalized_patients_features")
px_hosp_pts = spark.read.format("delta").load(f"{BASE}/px_num_hospitalized_patients_features")

for name, df in [
    ("DX % hosp", dx_perc_hosp), ("PX % hosp", px_perc_hosp),
    ("DX hosp pts", dx_hosp_pts), ("PX hosp pts", px_hosp_pts),
]:
    print(f"{name}: {df.count():,} rows, {len(df.columns)} cols")
```

## Understanding the Schema

### % Hospitalized Features (Sub-type C)
**Key columns:** `PROVIDER_ID`, `SVC_DT_M`

**Feature columns:**
* `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_DIAGNOSIS_IN_LAST_{N}_MONTH` (DX, N ∈ {1,6,12})
* `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_PROCEDURES_IN_LAST_{N}_MONTH` (PX, N ∈ {1,6,12})
* `TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_{N}_MONTH` (DX)
* `TOTAL_HOSPITALIZED_CLAIMS_ALL_PROCEDURES_IN_LAST_{N}_MONTH` (PX)

```python
# List all feature columns
perc_cols = [c for c in dx_perc_hosp.columns if c.startswith("PERC_")]
hosp_cols = [c for c in dx_perc_hosp.columns if c.startswith("TOTAL_HOSPITALIZED_")]
print(f"DX: {len(perc_cols)} % cols, {len(hosp_cols)} total hospitalized cols")
for c in sorted(perc_cols + hosp_cols):
    print(f"  {c}")
```

### Unique Hospitalized Patient Counts (Sub-type D)
**Key columns:** `PROVIDER_ID`, `COHORT`

**Feature columns:**
* `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DIAGNOSED_IN_LAST_{N}_DAYS` (DX, N ∈ {30,180,360})
* `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DID_PROCEDURE_IN_LAST_{N}_DAYS` (PX, N ∈ {30,180,360})

## Regenerating Hospitalization Features

**Only use this if you need to regenerate. Prefer pre-materialized Delta outputs.**

### Sub-types A→C (% Hospitalized)

```python
# Cell 1–2: Setup
%run ".../00_connection"
%run ".../00_config"
```

```python
# Cell 3: Read two inputs (DX example)
dx_claims = spark.read.format("delta").load(dx1_file_path)
dx_hospitalized_claims = spark.read.format("delta").load(dx_hosp_file_path)

# Collapse to single event
dx_claims = dx_claims.select(
    "PROVIDER_ID", "CLAIM_ID", "PATIENT_ID", "SVC_DT",
    lit("ALL_DIAGNOSIS").alias("DIAGNOSIS_DESCRIPTION"),
    "PROVIDER_REFERRING_ID", "PROVIDER_RENDERING_ID", "PAYER_PLAN_ID", "ICD_VERSION_TYPE"
)
dx_hospitalized_claims = dx_hospitalized_claims.select(
    "PROVIDER_ID", "CLAIM_ID", "PATIENT_ID", "SVC_DT",
    lit("ALL_DIAGNOSIS").alias("DIAGNOSIS_DESCRIPTION"),
    "PROVIDER_REFERRING_ID", "PROVIDER_RENDERING_ID", "PAYER_PLAN_ID", "ICD_VERSION_TYPE"
)

# Drop HCP flags from hospitalized
dx_hospitalized_claims = dx_hospitalized_claims.drop(
    'KERENDIA_FLAG', 'SGLT2_GLP1_FLAG', 'NEPH_FLAG', 'TARGETING_HCP_FLAG', 'BPT_HCP_FLAG'
)

# Add monthly column
dx_claims = dx_claims.withColumn("SVC_DT_M", F.date_trunc('MM', col("SVC_DT")))
dx_hospitalized_claims = dx_hospitalized_claims.withColumn("SVC_DT_M", F.date_trunc('MM', col("SVC_DT")))
index_cols = ['PROVIDER_ID', 'SVC_DT_M']
```

```python
# Cell 4: Sub-type A — Total & Hospitalized counts
total_dx = dx_claims.groupBy(index_cols).pivot("DIAGNOSIS_DESCRIPTION").agg(F.count(F.lit(1)))
# Rename with TOTAL_CLAIMS_ prefix + sanitize

total_hosp_dx = dx_hospitalized_claims.groupBy(index_cols).pivot("DIAGNOSIS_DESCRIPTION").agg(F.count(F.lit(1)))
# Rename with TOTAL_HOSPITALIZED_CLAIMS_ prefix + sanitize

combined = total_dx.join(total_hosp_dx, on=index_cols, how='left').fillna(0)
```

```python
# Cell 5: Sub-type B — Lag with [1, 6, 12] months
# (step2_fill_missing, step3_lag, process_and_join defined inline — same as Frequency)
lag_hosp = process_and_join(df=combined, last_i_month_list=[1, 6, 12])
```

```python
# Cell 6: Validation filter
lag_hosp = lag_hosp.filter(
    (col("TOTAL_CLAIMS_ALL_DIAGNOSIS_IN_LAST_1_MONTH") >=
     col("TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_1_MONTH")) &
    (col("TOTAL_CLAIMS_ALL_DIAGNOSIS_IN_LAST_6_MONTH") >=
     col("TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_6_MONTH")) &
    (col("TOTAL_CLAIMS_ALL_DIAGNOSIS_IN_LAST_12_MONTH") >=
     col("TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_12_MONTH"))
)
```

```python
# Cell 7: Sub-type C — % Hospitalized
recent_windows = [1, 6, 12]
new_columns = []
for event in event_names:  # ['ALL_DIAGNOSIS']
    for N in recent_windows:
        col_N = F.col(f"TOTAL_HOSPITALIZED_CLAIMS_{event}_IN_LAST_{N}_MONTH")
        col_D = F.col(f"TOTAL_CLAIMS_{event}_IN_LAST_{N}_MONTH")
        change_name = f"PERC_HOSPITALIZED_HCP_CLAIMS_FOR_{event}_IN_LAST_{N}_MONTH"
        new_columns.append(F.when(col_D != 0, col_N / col_D).otherwise(None).alias(change_name))

percentage_hosp = lag_hosp.select("PROVIDER_ID", "SVC_DT_M", *new_columns,
    *[c for c in lag_hosp.columns if c.startswith("TOTAL_HOSPITALIZED_")])

# Drop TOTAL_CLAIMS_* columns (keep only TOTAL_HOSPITALIZED_* and PERC_*)
```

```python
# Cell 8: Save
percentage_hosp.write.format("delta").mode("overwrite").save(
    f"{BASE}/dx_percentage_hospitalized_features")
```

### Sub-type D (Unique Hospitalized Patient Counts)

```python
# Same cohort cross-join pattern as Frequency Sub-type D:
# 1. Read hcp_model_inference_anchor_dates.csv
# 2. Cross-join HOSPITALIZED claims (not total) with cohort_anchor_dates
# 3. Filter to lookback window
# 4. days_diff = DATEDIFF(LOOKBACK_END_DATE, SVC_DT)
# 5. Flag for [30, 180, 360] days
# 6. Dedup on [PROVIDER_ID, COHORT, EVENT_COL, PATIENT_ID]
# 7. countDistinct(PATIENT_ID) → hospitalized_pt_cnt_{N}_days
# 8. Unpivot → Pivot with descriptive column name
# 9. Save as {claim}_num_hospitalized_patients_features
```

## Adapting Between DX and PX

| Variable | DX | PX |
| --- | --- | --- |
| Total claims path | `dx1_file_path` | `px1_file_path` |
| Hospitalized path | `dx_hosp_file_path` | `px_hosp_file_path` |
| Event column | `DIAGNOSIS_DESCRIPTION` | `PROCEDURE_DESCRIPTION` |
| Collapsed event | `ALL_DIAGNOSIS` | `ALL_PROCEDURES` |
| % output | `dx_percentage_hospitalized_features` | `px_percentage_hospitalized_features` |
| Pts output | `dx_num_hospitalized_patients_features` | `px_num_hospitalized_patients_features` |
| Patient count verb | `DIAGNOSED` | `DID_PROCEDURE` |
| PX suffix in combine | N/A | `_PX` appended |

## EDA Patterns

### Pattern 1: Hospitalization Rate Distribution

```python
# What fraction of DX claims are hospitalized?
for N in [1, 6, 12]:
    col_name = f"PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_DIAGNOSIS_IN_LAST_{N}_MONTH"
    if col_name in dx_perc_hosp.columns:
        stats = dx_perc_hosp.select(avg(col(col_name)).alias("avg"),
            F.stddev(col(col_name)).alias("std")).first()
        print(f"  {N}M: avg={stats['avg']:.4f}, std={stats['std']:.4f}")
```

### Pattern 2: High Hospitalization HCPs

```python
# Top 20 HCPs by 12M hospitalization rate
col_12m = "PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_DIAGNOSIS_IN_LAST_12_MONTH"
dx_perc_hosp.filter(col(col_12m).isNotNull()).orderBy(col(col_12m).desc()).select(
    "PROVIDER_ID", "SVC_DT_M", col_12m,
    "TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_12_MONTH"
).limit(20).show(truncate=False)
```

### Pattern 3: DX vs PX Hospitalization Comparison

```python
# Join DX and PX on PROVIDER_ID × SVC_DT_M, compare rates
dx_12 = "PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_DIAGNOSIS_IN_LAST_12_MONTH"
px_12 = "PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_PROCEDURES_IN_LAST_12_MONTH"

joined = dx_perc_hosp.select("PROVIDER_ID", "SVC_DT_M", col(dx_12).alias("dx_rate")).join(
    px_perc_hosp.select("PROVIDER_ID", "SVC_DT_M", col(px_12).alias("px_rate")),
    on=["PROVIDER_ID", "SVC_DT_M"], how="inner"
)
joined.select(avg("dx_rate"), avg("px_rate")).show()
```

### Pattern 4: Hospitalized Patient Counts Over Windows

```python
# Average hospitalized patients per HCP by time window
for w in [30, 180, 360]:
    col_name = f"NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DIAGNOSED_IN_LAST_{w}_DAYS"
    if col_name in dx_hosp_pts.columns:
        avg_val = dx_hosp_pts.select(avg(col(col_name))).first()[0]
        print(f"  {w}d: {avg_val:.2f} avg hospitalized patients")
```

### Pattern 5: Null Rate (HCPs with no hospitalization data)

```python
from pyspark.sql.functions import sum as spark_sum, when

total = dx_perc_hosp.count()
for N in [1, 6, 12]:
    col_name = f"PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_DIAGNOSIS_IN_LAST_{N}_MONTH"
    if col_name in dx_perc_hosp.columns:
        null_count = dx_perc_hosp.filter(col(col_name).isNull()).count()
        print(f"  {N}M: {null_count:,} / {total:,} ({null_count/total*100:.1f}%) NULL (zero total claims)")
```

## Important Constraints

1. **DX and PX only** — no RX or Lab hospitalization features exist.
2. **Single collapsed event** — all claims map to `ALL_DIAGNOSIS` or `ALL_PROCEDURES` via `lit()`. There is no per-diagnosis or per-procedure hospitalization rate.
3. **Validation removes bad rows** — any row where `TOTAL < HOSPITALIZED` for any window is filtered out. This can reduce row count from the lag output.
4. **% is NULL when total = 0** — `WHEN TOTAL != 0 THEN HOSP/TOTAL ELSE NULL`. This means HCPs with zero claims in a window get NULL, not 0.
5. **Patient count windows differ** — `[30, 180, 360]` days, NOT the `[30, 60, 90, 180, 360]` used in frequency.
6. **PX columns get `_PX` suffix** in the final combine to avoid name collisions with DX columns.
7. **HCP flags are dropped** from hospitalized claims — `KERENDIA_FLAG`, `SGLT2_GLP1_FLAG`, `NEPH_FLAG`, `TARGETING_HCP_FLAG`, `BPT_HCP_FLAG`.
8. **Lag windows shorter** — `[1, 6, 12]` months vs frequency's `[1, 2, 3, 6, 12]`.
9. **Two intermediate outputs are NOT saved** — Sub-types A (raw counts) and B (lag counts) are in-memory only. Only Sub-types C and D are persisted to Delta.
