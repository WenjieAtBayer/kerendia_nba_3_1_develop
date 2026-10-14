# Personal Promotional Features — EDA Reference

Exploratory Data Analysis patterns and known data characteristics for the three personal
promotional channels: F2F Sales Rep Calls, iRep Emails, and ClickStream/CLM. Use this
reference to validate feature outputs, detect data quality issues, and understand feature
distributions before model training.

---

## 1. Output Parquet Paths

| Channel | Path |
| --- | --- |
| F2F Sales Rep Calls | `.../notebook_output/kerendia_nba_3_hcp_model_call_features.parquet` |
| iRep Emails | `.../notebook_output/kerendia_nba_3_hcp_model_irep_features.parquet` |
| ClickStream/CLM | `.../notebook_output/kerendia_nba_3_hcp_model_clickstream_features.parquet` |

Base volume: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/dev_folder/`

---

## 2. Standard EDA Checks

Run these checks against each channel’s output parquet to validate correctness.

### 2.1 Schema and Dimensions

```python
df = spark.read.parquet(path)
print(f"Rows: {df.count()}, Columns: {len(df.columns)}")
df.printSchema()
```

Expected dimensions:

| Channel | Expected Rows | Expected Columns |
| --- | --- | --- |
| F2F Sales Rep Calls | ~2,086,597 | 212 |
| iRep Emails | ~966,322 | 86 |
| ClickStream/CLM | ~191,214 | 26 |

### 2.2 Key Integrity

```python
# HCP_COHORT_ID should be unique per row
assert df.count() == df.select("HCP_COHORT_ID").distinct().count(), "Duplicate HCP_COHORT_IDs found"

# HCP_COHORT_ID format: {BHID}_{COHORT}
from pyspark.sql import functions as F
bad_keys = df.filter(~F.col("HCP_COHORT_ID").rlike(r"^BH\d+_C\d{2}$")).count()
print(f"Malformed HCP_COHORT_IDs: {bad_keys}")

# Distinct HCPs and cohorts
df_split = df.withColumn("BHID", F.split("HCP_COHORT_ID", "_").getItem(0)) \
             .withColumn("COHORT", F.split("HCP_COHORT_ID", "_").getItem(1))
print(f"Distinct BHIDs: {df_split.select('BHID').distinct().count()}")
print(f"Distinct Cohorts: {df_split.select('COHORT').distinct().count()}")
```

Expected distinct HCPs:

| Channel | Distinct HCPs |
| --- | --- |
| F2F Sales Rep Calls | ~129,787 |
| iRep Emails | ~79,627 |
| ClickStream/CLM | ~18,804 |

### 2.3 Sparsity Analysis

```python
from pyspark.sql import functions as F

feature_cols = [c for c in df.columns if c not in ['HCP_COHORT_ID', 'SVC_DT', 'BHID', 'COHORT']]
total = df.count()

stats = []
for col_name in feature_cols:
    zero_count = df.filter(F.col(col_name) == 0).count()
    null_count = df.filter(F.col(col_name).isNull()).count()
    stats.append((col_name, zero_count, null_count, round(zero_count / total * 100, 1)))

stats_df = spark.createDataFrame(stats, ["feature", "zero_count", "null_count", "zero_pct"])
stats_df.orderBy("zero_pct", ascending=False).display()
```

Expected average sparsity:

| Channel | Avg Zero % | Interpretation |
| --- | --- | --- |
| F2F Sales Rep Calls | 94.3% | Most HCPs receive no calls in most windows |
| iRep Emails | 97.2% | Very sparse; iRep is niche |
| ClickStream/CLM | 67.2% | Less sparse; CLM records have continuous metrics |

### 2.4 Feature Distribution Statistics

```python
from pyspark.sql import functions as F

feature_cols = [c for c in df.columns if c.endswith('_MONTH')]

# Summary stats for all lag features
df.select([F.mean(c).alias(f"{c}_mean") for c in feature_cols[:10]]).display()  # sample 10
df.select([F.stddev(c).alias(f"{c}_std") for c in feature_cols[:10]]).display()
df.select([F.max(c).alias(f"{c}_max") for c in feature_cols[:10]]).display()

# Percentile distribution for non-zero values
for col_name in feature_cols[:5]:
    non_zero = df.filter(F.col(col_name) > 0)
    non_zero.select(
        F.percentile_approx(col_name, [0.25, 0.5, 0.75, 0.90, 0.99]).alias("percentiles")
    ).display()
```

### 2.5 Zero-Variance Feature Detection

```python
from pyspark.sql import functions as F

feature_cols = [c for c in df.columns if c not in ['HCP_COHORT_ID', 'SVC_DT']]
zero_var = []
for col_name in feature_cols:
    std = df.select(F.stddev(col_name)).first()[0]
    mx = df.select(F.max(col_name)).first()[0]
    if std == 0 or std is None:
        zero_var.append((col_name, mx))

print(f"Zero-variance features: {len(zero_var)}")
for name, mx in zero_var:
    print(f"  {name}: max={mx}")
```

---

## 3. Channel-Specific EDA Findings

### 3.1 F2F Sales Rep Calls

**Key stats from current output:**
- Raw source records: 1,806,358
- Output rows after cohort cross-join: 2,086,597
- 212 columns (35 base features × 6 rolling windows + 2 keys)

**Distribution patterns:**
- Channel type features (`TOTAL_F2F_*`, `TOTAL_PHONE_*`): heavily right-skewed; most
  HCPs receive 0–2 calls per window, small tail with 50+ calls
- Call duration (`TOTAL_CALL_DURATION_*`): wide range (0–several thousand), reflecting
  defensive casting that zeroes out negative/invalid durations (historical DQ guard)
- Cross-product features (`TOTAL_{CHANNEL}_AND_{TYPE}_*`): extremely sparse since they
  require both flags = 1; zero rates above 98% are typical

**Known patterns:**
- F2F is the dominant channel type; REMOTE_CALL and GROUP_CALL have much lower volumes
- `TOTAL_CALL_PURPOSE_MISCELLANEOUS_*` is the catch-all and can absorb unusual values

### 3.2 iRep Emails

**Key stats from current output:**
- Raw source records: 530,237
- Output rows: 966,322
- 86 columns (14 base features × 6 rolling windows + 2 keys)

**Known zero-variance issues:**
- `TOTAL_IREP_APPRVD_DOC_NM_FDA_IN_LAST_*_MONTH`: mean=0, stddev=0, max=0
- `TOTAL_IREP_APPRVD_DOC_NM_PSP_PRESCRIBING_IN_LAST_*_MONTH`: mean=0, stddev=0, max=0
- `TOTAL_IREP_APPRVD_DOC_NM_BRANDED_ASSET_IN_LAST_*_MONTH`: mean=0, stddev=0, max=0
- `TOTAL_IREP_APPRVD_DOC_NM_NATIONAL_BROADCAST_IN_LAST_*_MONTH`: mean=0, stddev=0, max=0

These are historical/inactive document categories that were present in the `APPRVD_DOC_NM`
mapping but have no data in the current date range. They are expected to be zero. Zero-variance
filtering is a model-training concern, not handled in feature engineering.

**Delivery status features:**
- `TOTAL_IREP_EMAIL_DELIVERED_*`: non-zero for most HCPs in the universe (this is the
  pre-filter, so all records are delivered)
- `TOTAL_IREP_EMAIL_CLICKED_*` and `TOTAL_IREP_EMAIL_OPENED_*`: lower counts, representing
  engagement downstream of delivery

### 3.3 ClickStream/CLM

**Key stats from current output:**
- Output rows: 191,214
- 26 columns (4 base metrics × 6 rolling windows + 2 keys)
- Smallest personal channel by HCP count (18,804)

**Duration metrics:**
- `CLICKSTREAM_TOTAL_USAGE_DURATION_*`: max observed = 429,708 (unit unclear — likely
  seconds based on magnitude; document as TBD if not confirmed)
- `CLICKSTREAM_TOTAL_PRESN_DURATION_*`: max observed = 7,468
- `CLICKSTREAM_AVG_USAGE_DURATION_*` and `CLICKSTREAM_AVG_PRESN_DURATION_*`: derived from
  the SUM/COUNT pattern; check for division-by-zero artifacts

**Dedup impact:**
- Inner join with FACT_CALL silently drops orphan clickstream events (events without a
  matching submitted call). This is intentional. To measure drop rate:

```python
raw_click = spark.read.parquet("...raw_clickstream...")
joined = raw_click.join(calls, on='CALL_ID', how='inner')
print(f"Raw clickstream: {raw_click.count()}")
print(f"After inner join: {joined.count()}")
print(f"Drop rate: {1 - joined.count() / raw_click.count():.1%}")
```

---

## 4. Cross-Channel Alignment Checks

### 4.1 Cohort Coverage

All channels should have exactly 26 cohorts (C01–C26):

```python
for name, path in [("Calls", calls_path), ("iRep", irep_path), ("ClickStream", click_path)]:
    df = spark.read.parquet(path)
    cohorts = df.withColumn("COHORT", F.split("HCP_COHORT_ID", "_").getItem(1)) \
                .select("COHORT").distinct().orderBy("COHORT").collect()
    print(f"{name}: {len(cohorts)} cohorts — {[r.COHORT for r in cohorts[:3]]}...{[r.COHORT for r in cohorts[-3:]]}")
```

### 4.2 HCP Overlap Across Channels

```python
calls_hcps = calls_df.withColumn("BHID", F.split("HCP_COHORT_ID", "_").getItem(0)).select("BHID").distinct()
irep_hcps = irep_df.withColumn("BHID", F.split("HCP_COHORT_ID", "_").getItem(0)).select("BHID").distinct()
click_hcps = click_df.withColumn("BHID", F.split("HCP_COHORT_ID", "_").getItem(0)).select("BHID").distinct()

print(f"Calls ∩ iRep: {calls_hcps.intersect(irep_hcps).count()}")
print(f"Calls ∩ ClickStream: {calls_hcps.intersect(click_hcps).count()}")
print(f"iRep ∩ ClickStream: {irep_hcps.intersect(click_hcps).count()}")
print(f"All three: {calls_hcps.intersect(irep_hcps).intersect(click_hcps).count()}")
```

### 4.3 Date Range Consistency

```python
for name, df in [("Calls", calls_df), ("iRep", irep_df), ("ClickStream", click_df)]:
    dates = df.select(F.min("SVC_DT"), F.max("SVC_DT")).first()
    print(f"{name}: {dates[0]} to {dates[1]}")
```

Expected date range: Each channel’s `SVC_DT` should align with the cohort anchor
`LOOKBACK_END_DATE` values (C01=2023-02, C26=2025-04 approximately).

---

## 5. Combine-Step Validation

After all personal channels are joined in the combine notebook, validate the combined output:

```python
combined = spark.read.parquet(combined_path)

# Expected column count: ~212 (calls) + ~84 (irep) + ~24 (clickstream) + keys
print(f"Combined columns: {len(combined.columns)}")

# Null rate after left join (channels with fewer HCPs will have nulls)
for prefix in ['TOTAL_F2F', 'TOTAL_IREP', 'CLICKSTREAM_TOTAL']:
    sample_col = [c for c in combined.columns if c.startswith(prefix)][0]
    null_rate = combined.filter(F.col(sample_col).isNull()).count() / combined.count()
    print(f"{prefix}* null rate after join: {null_rate:.1%}")
```

Expected null rates (before fillna):
- Calls features: ~0% (largest HCP universe, 130K)
- iRep features: ~40–50% (only 80K HCPs)
- ClickStream features: ~85% (only 19K HCPs)

After `fillna(0)`, all nulls become zeros.

---

## 6. Data Quality Red Flags

| Check | Expected | Red Flag |
| --- | --- | --- |
| Row count changes > 10% | Stable across runs | Source data load issue or filter change |
| New zero-variance features | Only known inactive categories | Possible upstream schema change |
| `CALL_DURATION` negative values | 0 (guarded by cast) | Guard removed or bypassed |
| Cohort count ≠ 26 | Exactly 26 | Anchor dates file changed |
| HCP_COHORT_ID duplicates | 0 | Aggregation or join producing duplicates |
| ClickStream > Calls HCP count | ClickStream ≤ Calls | Inner join not filtering properly |
| Feature max > 10,000 for counts | Unusual | Possible aggregation error |
