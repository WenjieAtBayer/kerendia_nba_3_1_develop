# RX Feature QC & EDA — Cell-by-Cell Template

This template reproduces the QC validation notebook `rx_feature_qc_eda` (~60 cells).
It independently recomputes RX feature values from raw source data for a stratified sample
of HCPs and compares them side-by-side against the feature notebooks' output Delta tables.

Each section below corresponds to one cell. Create cells in order.
Cell type is indicated as [md], [run], or [python].

**IMPORTANT — Markdown cells:** For [md] cells, the code block starts with `%md` followed
by a newline. When creating the notebook cell, set `language="markdown"` and use only the
content AFTER the `%md\n` line as the cell source.

**[run] cells:** Set `language="run"` and include the full `%run "..."` line as source.

**Serverless compute note:** If running on serverless compute, replace `.persist(StorageLevel.MEMORY_ONLY)` calls with
`.persist(StorageLevel.MEMORY_ONLY)` and add `from pyspark.storagelevel import StorageLevel`
to Cell 4. On serverless, `.persist(StorageLevel.MEMORY_ONLY)` triggers `PERSIST TABLE` which is not supported.
Alternatively, collect DataFrames to Python lists after each action to avoid re-computation.

---

## Cell 1 [md] — Title, purpose, what it validates

```python
%md
### RX Feature QC & EDA — Independent Recomputation Validation

##### Purpose:
This notebook independently recomputes RX feature values from raw source data for a
stratified sample of HCPs, then compares them side-by-side against the feature notebooks'
output Delta tables. It validates that the pipeline code computes what it claims to compute.

##### What it validates:
- First Occurrence, Recency (6 sub-features), Frequency (claim count, lag, change, patient counts)
- For 5-6 stratified HCPs (high/medium/low volume)

##### What it does NOT validate:
- Bugs upstream of rx1_file_path (Snowflake extraction, NPI mapping, product group mapping)
- Semantic correctness of feature definitions
- EVENT_TYPE assignment (hardcoded as "rx" — acceptable for RX-only QC)
```

---

## Cell 2 [run] — Load connection helper (Snowflake auth, imports)

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```

---

## Cell 3 [run] — Load config helper (file paths, date params, time_windows)

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config"
```

---

## Cell 4 [python] — Define BASE path and comparison helper functions

```python
BASE = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output"
ANCHOR_CSV = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/hcp_model_inference_anchor_dates.csv"

# Results accumulator — collects all checks across all sections
qc_results = []

def compare_values(manual_val, notebook_val, feature_name, hcp_id, tolerance=0):
    """Compare manual vs notebook value, record result in qc_results."""
    if manual_val is None and notebook_val is None:
        status = "MATCH"
        delta = 0
    elif manual_val is None or notebook_val is None:
        status = "MISMATCH"
        delta = None
    elif tolerance > 0:
        delta = abs(float(manual_val) - float(notebook_val))
        status = "MATCH" if delta < tolerance else "MISMATCH"
    else:
        status = "MATCH" if manual_val == notebook_val else "MISMATCH"
        delta = (manual_val - notebook_val) if status == "MISMATCH" and isinstance(manual_val, (int, float)) else None

    qc_results.append({
        "hcp_id": hcp_id,
        "feature": feature_name,
        "manual": manual_val,
        "notebook": notebook_val,
        "status": status,
        "delta": delta
    })
    return status

print("Helpers defined. qc_results initialized.")
```

---

## Cell 5 [python] — Read HCP universe and raw claims for volume counting

```python
# Read HCP universe
hcp_universe = spark.read.format("delta").load(hcp_universe_path).select("PROVIDER_ID").distinct()

# Read raw claims to count volume per HCP
raw_claims_for_volume = spark.read.format("delta").load(rx1_file_path).select("PROVIDER_ID", "SVC_DT")

# Read anchor dates to get lookback window
anchor_dates = spark.createDataFrame(pd.read_csv(ANCHOR_CSV))
min_lb = anchor_dates.agg(F.min("LOOKBACK_START_DATE")).first()[0]
max_lb = anchor_dates.agg(F.max("LOOKBACK_END_DATE")).first()[0]

# Filter claims to lookback window for volume counting
raw_claims_for_volume = raw_claims_for_volume.filter(
    (F.col("SVC_DT") >= F.lit(min_lb)) & (F.col("SVC_DT") <= F.lit(max_lb))
)

# Count claims per HCP
hcp_volume = raw_claims_for_volume.groupBy("PROVIDER_ID").agg(
    F.count(F.lit(1)).alias("claim_count")
).orderBy(F.col("claim_count").desc())

# Join with HCP universe (only HCPs in the universe)
hcp_volume = hcp_universe.join(hcp_volume, on="PROVIDER_ID", how="inner").orderBy(F.col("claim_count").desc())

print(f"HCP universe size: {hcp_universe.count()}")
print(f"HCPs with claims in lookback: {hcp_volume.count()}")
```

---

## Cell 6 [python] — Stratified sampling: bin HCPs into tertiles by claim volume

```python
# Get claim counts as percentiles for tertile boundaries
total_hcps = hcp_volume.count()
tertile_size = total_hcps // 3

# Assign tertile labels using row number
from pyspark.sql.window import Window
w = Window.orderBy(F.col("claim_count").desc())
hcp_volume_ranked = hcp_volume.withColumn("rank", F.row_number().over(w))
hcp_volume_ranked = hcp_volume_ranked.withColumn(
    "tertile",
    F.when(F.col("rank") <= tertile_size, F.lit("high"))
     .when(F.col("rank") <= tertile_size * 2, F.lit("medium"))
     .otherwise(F.lit("low"))
)

hcp_volume_ranked.persist(StorageLevel.MEMORY_ONLY)
print(f"High tertile: {hcp_volume_ranked.filter(F.col('tertile') == 'high').count()} HCPs")
print(f"Medium tertile: {hcp_volume_ranked.filter(F.col('tertile') == 'medium').count()} HCPs")
print(f"Low tertile: {hcp_volume_ranked.filter(F.col('tertile') == 'low').count()} HCPs")
```

---

## Cell 7 [python] — Sample 2 high, 2 medium, 2 low HCPs with seed=42

```python
# Optional: pin specific PROVIDER_IDs for reproducibility
# Set to None to use random sampling
pinned_hcps = None  # e.g., ["PRV001", "PRV002", "PRV003", "PRV004", "PRV005", "PRV006"]

if pinned_hcps:
    sampled_hcps = hcp_volume_ranked.filter(F.col("PROVIDER_ID").isin(pinned_hcps))
    print("Using pinned HCPs")
else:
    # Stratified sample: 2 from each tertile, seeded
    seed = 42
    high_sample = hcp_volume_ranked.filter(F.col("tertile") == "high").sample(fraction=2.0/max(hcp_volume_ranked.filter(F.col("tertile")=="high").count(), 1), seed=seed).limit(2)
    medium_sample = hcp_volume_ranked.filter(F.col("tertile") == "medium").sample(fraction=2.0/max(hcp_volume_ranked.filter(F.col("tertile")=="medium").count(), 1), seed=seed).limit(2)
    low_sample = hcp_volume_ranked.filter(F.col("tertile") == "low").sample(fraction=2.0/max(hcp_volume_ranked.filter(F.col("tertile")=="low").count(), 1), seed=seed).limit(2)
    sampled_hcps = high_sample.union(medium_sample).union(low_sample)

sampled_hcps.persist(StorageLevel.MEMORY_ONLY)
print(f"Sampled {sampled_hcps.count()} HCPs")
```

---

## Cell 8 [python] — Display sample with claim counts and tertile labels

```python
sampled_hcps.select("PROVIDER_ID", "claim_count", "tertile").orderBy(F.col("claim_count").desc()).display()
```

---

## Cell 9 [python] — Read raw claims for sampled HCPs and cross-join with anchor dates

```python
sampled_ids = [row["PROVIDER_ID"] for row in sampled_hcps.select("PROVIDER_ID").collect()]

# Read raw claims filtered to sampled HCPs
raw_claims = spark.read.format("delta").load(rx1_file_path).filter(
    F.col("PROVIDER_ID").isin(sampled_ids)
)

# Read anchor dates
anchor_df = spark.createDataFrame(pd.read_csv(ANCHOR_CSV))

# Cross-join claims with anchor dates (broadcast small anchor DF)
claims_cross = raw_claims.crossJoin(F.broadcast(anchor_df))

print(f"Raw claims for sampled HCPs: {raw_claims.count():,}")
print(f"After cross-join: {claims_cross.count():,}")
```

---

## Cell 10 [python] — Compute EVENT_TIME, create HCP_COHORT_ID, split into full-lookback and 12M

```python
# Compute EVENT_TIME and HCP_COHORT_ID
claims_cross = claims_cross.withColumn(
    "EVENT_TIME", F.datediff(F.col("LOOKBACK_END_DATE"), F.col("SVC_DT"))
).withColumn(
    "HCP_COHORT_ID", F.concat_ws("_", F.col("PROVIDER_ID"), F.col("COHORT"))
)

# Set EVENT_TYPE to "rx" (hardcoded — see SKILL.md for limitation)
claims_cross = claims_cross.withColumn("EVENT_TYPE", F.lit("rx"))

# Full lookback for First Occurrence (EVENT_TIME >= 0, no lower bound)
full_lookback_claims = claims_cross.filter(F.col("EVENT_TIME") >= 0)

# 12M filtered for Recency
claims_12m = claims_cross.filter(
    (F.col("SVC_DT") >= F.col("LOOKBACK_START_DATE")) &
    (F.col("SVC_DT") <= F.col("LOOKBACK_END_DATE"))
)

# Get sampled HCP_COHORT_IDs
sampled_hcp_cohort_ids = [row["HCP_COHORT_ID"] for row in full_lookback_claims.select("HCP_COHORT_ID").distinct().collect()]

print(f"Sampled HCP_COHORT_IDs: {sampled_hcp_cohort_ids}")
print(f"Full lookback claims: {full_lookback_claims.count():,}")
print(f"12M claims: {claims_12m.count():,}")
```

---

## Cell 11 [md] — Section: First Occurrence QC

```python
%md
### First Occurrence QC

Manual recomputation: groupBy(HCP_COHORT_ID).pivot(PRODUCT_GROUP).agg(max(EVENT_TIME))
Compare against rx_first_occurrence_features output.
```

---

## Cell 12 [python] — Manual: compute first occurrence from raw claims

```python
# Manual first occurrence: max(EVENT_TIME) per HCP_COHORT_ID per PRODUCT_GROUP
manual_first_occ = full_lookback_claims.groupBy("HCP_COHORT_ID").pivot("PRODUCT_GROUP").agg(
    F.max("EVENT_TIME").alias("max_EVENT_TIME")
)

# Rename columns to match notebook output format
# First occurrence uses different sanitization than frequency:
#   - lowercase, "/" → "_", " " → "_", remove special chars, add "_rx_first_occurrence" suffix
def sanitize_first_occ(product_group):
    name = product_group.lower()
    name = name.replace("/", "_").replace(" ", "_").replace("-", "_")
    name = name.replace("(", "").replace(")", "").replace("[", "").replace("]", "")
    name = name.replace(",", "").replace("+", "and")
    while "__" in name:
        name = name.replace("__", "_")
    return f"{name}_rx_first_occurrence"

rename_cols = [F.col(c).alias(sanitize_first_occ(c)) for c in manual_first_occ.columns if c != "HCP_COHORT_ID"]
manual_first_occ = manual_first_occ.select(F.col("HCP_COHORT_ID"), *rename_cols)

# Filter to sampled HCPs
manual_first_occ = manual_first_occ.filter(F.col("HCP_COHORT_ID").isin(sampled_hcp_cohort_ids))
manual_first_occ.persist(StorageLevel.MEMORY_ONLY)

print(f"Manual first occurrence: {manual_first_occ.count()} rows, {len(manual_first_occ.columns)} cols")
```

---

## Cell 13 [python] — Read notebook output and compare

```python
# Read notebook output
nb_first_occ = spark.read.format("delta").load(f"{BASE}/rx_first_occurrence_features")
nb_first_occ = nb_first_occ.filter(F.col("HCP_COHORT_ID").isin(sampled_hcp_cohort_ids))
nb_first_occ.persist(StorageLevel.MEMORY_ONLY)

# Get common feature columns (excluding HCP_COHORT_ID)
manual_cols = set(manual_first_occ.columns) - {"HCP_COHORT_ID"}
nb_cols = set(nb_first_occ.columns) - {"HCP_COHORT_ID"}
common_cols = sorted(manual_cols & nb_cols)
manual_only = sorted(manual_cols - nb_cols)
nb_only = sorted(nb_cols - manual_cols)

print(f"Common columns: {len(common_cols)}")
if manual_only:
    print(f"Manual-only columns: {manual_only}")
if nb_only:
    print(f"Notebook-only columns: {nb_only}")

# Join and compare
joined = manual_first_occ.alias("m").join(nb_first_occ.alias("n"), on="HCP_COHORT_ID", how="inner")

for col_name in common_cols:
    for row in joined.select("HCP_COHORT_ID", F.col(f"m.{col_name}").alias("manual"), F.col(f"n.{col_name}").alias("notebook")).collect():
        compare_values(row["manual"], row["notebook"], col_name, row["HCP_COHORT_ID"])

fo_pass = sum(1 for r in qc_results if r["feature"] in common_cols and r["status"] == "MATCH")
fo_fail = sum(1 for r in qc_results if r["feature"] in common_cols and r["status"] == "MISMATCH")
print(f"\nFirst Occurrence: {fo_pass} pass, {fo_fail} fail")
```

---

## Cell 14 [python] — Display raw claims for one HCP x drug (eyeball check)

```python
# Show raw claims for one HCP_COHORT_ID and one drug (e.g., KERENDIA)
sample_hcp = sampled_hcp_cohort_ids[0]
sample_drug = "KERENDIA"

raw_for_eyeball = full_lookback_claims.filter(
    (F.col("HCP_COHORT_ID") == sample_hcp) & (F.col("PRODUCT_GROUP") == sample_drug)
).select("SVC_DT", "LOOKBACK_END_DATE", "EVENT_TIME", "PATIENT_ID", "CLAIM_ID").orderBy("EVENT_TIME")

print(f"Raw claims for {sample_hcp} x {sample_drug}: {raw_for_eyeball.count()} claims")
raw_for_eyeball.display()
print(f"\nManual max(EVENT_TIME): {manual_first_occ.filter(F.col('HCP_COHORT_ID') == sample_hcp).select(f'max(EVENT_TIME)_{sample_drug}_first_occurrence').collect()[0][0]}")
print(f"Notebook max(EVENT_TIME): {nb_first_occ.filter(F.col('HCP_COHORT_ID') == sample_hcp).select(f'max(EVENT_TIME)_{sample_drug}_first_occurrence').collect()[0][0]}")
```

---

## Cell 15 [md] — Section: Recency QC

```python
%md
### Recency QC

Manual recomputation of all 6 sub-features from 12M-filtered claims.
Compare against rx_recency_features output.
Note: EVENT_TYPE hardcoded as "rx" — see SKILL.md for limitation.
```

---

## Cell 16 [python] — Manual sub-feature 1: min(EVENT_TIME) per drug

```python
manual_min_event_time = claims_12m.groupBy("HCP_COHORT_ID").pivot("PRODUCT_GROUP").agg(
    F.min("EVENT_TIME").alias("min_EVENT_TIME")
)
rename_cols = [F.col(c).alias(f"min(EVENT_TIME)_{c}_time_min") for c in manual_min_event_time.columns if c != "HCP_COHORT_ID"]
manual_min_event_time = manual_min_event_time.select(F.col("HCP_COHORT_ID"), *rename_cols)
manual_min_event_time = manual_min_event_time.filter(F.col("HCP_COHORT_ID").isin(sampled_hcp_cohort_ids))
manual_min_event_time.persist(StorageLevel.MEMORY_ONLY)
print(f"Sub-feature 1 (min event time): {manual_min_event_time.count()} rows, {len(manual_min_event_time.columns)} cols")
```

---

## Cell 17 [python] — Manual sub-features 2-3: total/unique counts + time window counts

```python
# Sub-feature 2: total and unique events
manual_counts = claims_12m.filter(F.col("HCP_COHORT_ID").isin(sampled_hcp_cohort_ids)).groupBy("HCP_COHORT_ID").agg(
    F.count("EVENT_NAME").alias("total_events"),
    F.countDistinct("EVENT_NAME").alias("unique_events")
)

# Sub-feature 3: counts per time window
for w in time_windows:
    w_df = claims_12m.filter((F.col("HCP_COHORT_ID").isin(sampled_hcp_cohort_ids)) & (F.col("EVENT_TIME") <= w)).groupBy("HCP_COHORT_ID").agg(
        F.count("EVENT_NAME").alias(f"total_events_time_{w}_days"),
        F.countDistinct("EVENT_NAME").alias(f"unique_events_time_{w}_days")
    )
    manual_counts = manual_counts.join(w_df, on="HCP_COHORT_ID", how="left")

manual_counts = manual_counts.na.fill(0)
manual_counts.persist(StorageLevel.MEMORY_ONLY)
print(f"Sub-features 2-3 (counts): {manual_counts.count()} rows, {len(manual_counts.columns)} cols")
```

---

## Cell 18 [python] — Manual sub-features 4-5: by-type counts + type x window counts

```python
# Sub-feature 4: counts by event type
for et in ["rx", "px", "dx", "lab_data"]:
    et_df = claims_12m.filter((F.col("HCP_COHORT_ID").isin(sampled_hcp_cohort_ids)) & (F.col("EVENT_TYPE") == et)).groupBy("HCP_COHORT_ID").agg(
        F.count("EVENT_NAME").alias(f"total_{et}"),
        F.countDistinct("EVENT_NAME").alias(f"unique_{et}")
    )
    manual_counts = manual_counts.join(et_df, on="HCP_COHORT_ID", how="left")

# Sub-feature 5: counts by type x window
for et in ["rx", "px", "dx", "lab_data"]:
    for w in time_windows:
        tw_df = claims_12m.filter(
            (F.col("HCP_COHORT_ID").isin(sampled_hcp_cohort_ids)) &
            (F.col("EVENT_TIME") <= w) & (F.col("EVENT_TYPE") == et)
        ).groupBy("HCP_COHORT_ID").agg(
            F.count("EVENT_NAME").alias(f"total_events_time_{w}_days_{et}"),
            F.countDistinct("EVENT_NAME").alias(f"unique_events_time_{w}_days_{et}")
        )
        manual_counts = manual_counts.join(tw_df, on="HCP_COHORT_ID", how="left")

manual_counts = manual_counts.na.fill(0)
manual_counts.persist(StorageLevel.MEMORY_ONLY)
print(f"Sub-features 4-5 (type counts): {manual_counts.count()} rows, {len(manual_counts.columns)} cols")
```

---

## Cell 19 [python] — Manual sub-feature 6: skewness per type x window

```python
manual_skewness = None
for et in ["rx", "px", "dx", "lab_data"]:
    for w in time_windows:
        skew_df = claims_12m.filter(
            (F.col("HCP_COHORT_ID").isin(sampled_hcp_cohort_ids)) &
            (F.col("EVENT_TIME") <= w) & (F.col("EVENT_TYPE") == et)
        ).groupBy("HCP_COHORT_ID").agg(
            F.skewness("EVENT_TIME").alias(f"skewness_time_{w}_days_{et}")
        )
        if manual_skewness is None:
            manual_skewness = skew_df
        else:
            manual_skewness = manual_skewness.join(skew_df, on="HCP_COHORT_ID", how="outer")

manual_skewness = manual_skewness.filter(F.col("HCP_COHORT_ID").isin(sampled_hcp_cohort_ids))
manual_skewness.persist(StorageLevel.MEMORY_ONLY)
print(f"Sub-feature 6 (skewness): {manual_skewness.count()} rows, {len(manual_skewness.columns)} cols")
```

---

## Cell 20 [python] — Join all 6 recency sub-features on HCP_COHORT_ID

```python
manual_recency = manual_min_event_time.join(manual_counts, on="HCP_COHORT_ID", how="left")
manual_recency = manual_recency.join(manual_skewness, on="HCP_COHORT_ID", how="left")
manual_recency.persist(StorageLevel.MEMORY_ONLY)
print(f"Manual recency (all 6 sub-features): {manual_recency.count()} rows, {len(manual_recency.columns)} cols")
```

---

## Cell 21 [python] — Read notebook recency output and compare

```python
nb_recency = spark.read.format("delta").load(f"{BASE}/rx_recency_features")
nb_recency = nb_recency.filter(F.col("HCP_COHORT_ID").isin(sampled_hcp_cohort_ids))
nb_recency.persist(StorageLevel.MEMORY_ONLY)

# Identify common columns
manual_cols = set(manual_recency.columns) - {"HCP_COHORT_ID"}
nb_cols = set(nb_recency.columns) - {"HCP_COHORT_ID"}
common_cols = sorted(manual_cols & nb_cols)

# Skewness columns use tolerance; others use exact
skewness_cols = [c for c in common_cols if c.startswith("skewness_")]
exact_cols = [c for c in common_cols if not c.startswith("skewness_")]

joined = manual_recency.alias("m").join(nb_recency.alias("n"), on="HCP_COHORT_ID", how="inner")

# Compare exact columns
for col_name in exact_cols:
    for row in joined.select("HCP_COHORT_ID", F.col(f"m.{col_name}").alias("manual"), F.col(f"n.{col_name}").alias("notebook")).collect():
        compare_values(row["manual"], row["notebook"], col_name, row["HCP_COHORT_ID"])

# Compare skewness columns with tolerance
for col_name in skewness_cols:
    for row in joined.select("HCP_COHORT_ID", F.col(f"m.{col_name}").alias("manual"), F.col(f"n.{col_name}").alias("notebook")).collect():
        compare_values(row["manual"], row["notebook"], col_name, row["HCP_COHORT_ID"], tolerance=1e-4)

rec_pass = sum(1 for r in qc_results if r["feature"] in common_cols and r["status"] == "MATCH")
rec_fail = sum(1 for r in qc_results if r["feature"] in common_cols and r["status"] == "MISMATCH")
print(f"\nRecency: {rec_pass} pass, {rec_fail} fail (of {len(common_cols)} common columns)")
```

---

## Cell 22 [md] — Section: Frequency Claim Count QC

```python
%md
### Frequency Claim Count QC

Manual recomputation: groupBy([PROVIDER_ID, SVC_DT_M]).pivot(PRODUCT_GROUP).agg(count)
Compare against rx_frequency_features output.
```

---

## Cell 23 [python] — Manual: pivot and count claims per [PROVIDER_ID, SVC_DT_M, PRODUCT_GROUP]

```python
# Read raw claims from rx_freq_file_path (12M claims)
raw_freq_claims = spark.read.format("delta").load(rx_freq_file_path).filter(
    F.col("PROVIDER_ID").isin(sampled_ids)
)
raw_freq_claims = raw_freq_claims.withColumn("SVC_DT_M", F.date_trunc('MM', F.col("SVC_DT")))

# Manual pivot and count
index_cols = ['PROVIDER_ID', 'SVC_DT_M']
manual_freq = raw_freq_claims.groupBy(index_cols).pivot("PRODUCT_GROUP").agg(
    F.count(F.lit(1)).alias("claim_count")
)

# Apply same column sanitization as the notebook
manual_freq = manual_freq.select([
    F.col(c).alias('FREQ_' + c.replace(", ", " ").replace("+", "and").replace("/", " or").replace("-", "_")
        .replace(" ", "_").replace("__", "_").replace("(", "").replace(")", "").replace("[", "").replace("]", "")
        .upper()) if c not in index_cols else F.col(c)
    for c in manual_freq.columns
])

manual_freq.persist(StorageLevel.MEMORY_ONLY)
print(f"Manual frequency: {manual_freq.count()} rows, {len(manual_freq.columns)} cols")
```

---

## Cell 24 [python] — Read notebook frequency output and compare

```python
nb_freq = spark.read.format("delta").load(f"{BASE}/rx_frequency_features")
nb_freq = nb_freq.filter(F.col("PROVIDER_ID").isin(sampled_ids))
nb_freq.persist(StorageLevel.MEMORY_ONLY)

# Compare
manual_cols = set(manual_freq.columns) - set(index_cols)
nb_cols = set(nb_freq.columns) - set(index_cols)
common_cols = sorted(manual_cols & nb_cols)

joined = manual_freq.alias("m").join(nb_freq.alias("n"), on=index_cols, how="inner")

for col_name in common_cols:
    for row in joined.select(*index_cols, F.col(f"m.{col_name}").alias("manual"), F.col(f"n.{col_name}").alias("notebook")).collect():
        hcp_key = f"{row['PROVIDER_ID']}_{row['SVC_DT_M']}"
        compare_values(row["manual"], row["notebook"], col_name, hcp_key)

freq_pass = sum(1 for r in qc_results if r["feature"] in common_cols and r["status"] == "MATCH")
freq_fail = sum(1 for r in qc_results if r["feature"] in common_cols and r["status"] == "MISMATCH")
print(f"\nFrequency Claim Count: {freq_pass} pass, {freq_fail} fail")
```

---

## Cell 25 [md] — Section: Frequency Lag QC

```python
%md
### Frequency Lag QC

Manual recomputation: step2_fill_missing + step3_lag with [1,2,3,6,12] months
Compare a chosen drug's lag columns against rx_lag_frequency_features.
```

---

## Cell 26 [python] — Manual: compute lag features from the claim count pivot

```python
# Define inline helpers (same logic as the notebook, reimplemented independently)
def step2_fill_missing(df, key_col, date_col):
    date_list_df = (
        df.select(date_col)
        .agg(F.min(date_col).alias('min_date'), F.max(date_col).alias('max_date'))
        .withColumn(date_col, F.explode(F.expr('sequence(min_date, max_date, interval 1 month)')))
        .drop("min_date", "max_date")
    )
    patient_id_list_df = df.select(key_col).distinct()
    patient_date_full_list = patient_id_list_df.crossJoin(date_list_df).orderBy(key_col, date_col)
    step2_output = patient_date_full_list.join(df, on=[key_col, date_col], how="left")
    return step2_output

def step3_lag(df, key_col, date_col, last_i_month_list):
    window_base = Window.partitionBy(key_col).orderBy(date_col)
    features = [col for col in df.columns if col not in [key_col, date_col]]
    last_i_month = [F.sum(col).over(window_base.rowsBetween(-i+1, 0)).alias(col + "_IN_LAST_" + str(i) + "_MONTH") for i in last_i_month_list for col in features]
    return df.select("*", *last_i_month)

# Generate lag features
manual_lag = step2_fill_missing(manual_freq, "PROVIDER_ID", "SVC_DT_M")
manual_lag = step3_lag(manual_lag, "PROVIDER_ID", "SVC_DT_M", [1, 2, 3, 6, 12])
keep = ['PROVIDER_ID', 'SVC_DT_M'] + [c for c in manual_lag.columns if '_IN_LAST_' in c]
manual_lag = manual_lag.select(keep)
manual_lag.persist(StorageLevel.MEMORY_ONLY)
print(f"Manual lag: {manual_lag.count()} rows, {len(manual_lag.columns)} cols")
```

---

## Cell 27 [python] — Read notebook lag output and compare a chosen drug

```python
nb_lag = spark.read.format("delta").load(f"{BASE}/rx_lag_frequency_features")
nb_lag = nb_lag.filter(F.col("PROVIDER_ID").isin(sampled_ids))
nb_lag.persist(StorageLevel.MEMORY_ONLY)

# Choose a drug to compare (e.g., KERENDIA)
chosen_drug = "KERENDIA"
lag_cols = [f"FREQ_{chosen_drug}_IN_LAST_{n}_MONTH" for n in [1, 2, 3, 6, 12]]
lag_cols = [c for c in lag_cols if c in manual_lag.columns and c in nb_lag.columns]

joined = manual_lag.alias("m").join(nb_lag.alias("n"), on=["PROVIDER_ID", "SVC_DT_M"], how="inner")

for col_name in lag_cols:
    for row in joined.select("PROVIDER_ID", "SVC_DT_M", F.col(f"m.{col_name}").alias("manual"), F.col(f"n.{col_name}").alias("notebook")).collect():
        hcp_key = f"{row['PROVIDER_ID']}_{row['SVC_DT_M']}"
        compare_values(row["manual"], row["notebook"], col_name, hcp_key)

lag_pass = sum(1 for r in qc_results if r["feature"] in lag_cols and r["status"] == "MATCH")
lag_fail = sum(1 for r in qc_results if r["feature"] in lag_cols and r["status"] == "MISMATCH")
print(f"\nFrequency Lag ({chosen_drug}): {lag_pass} pass, {lag_fail} fail")
```

---

## Cell 28 [md] — Section: Frequency Change QC

```python
%md
### Frequency Change QC

Manual recomputation: change formula = (FREQ_N/N) - ((FREQ_12 - FREQ_N)/(12-N))
Compare against rx_change_frequency output. Uses tolerance 1e-4 for float comparison.
```

---

## Cell 29 [python] — Manual: compute change in frequency from lag features

```python
# Extract event names from lag columns
import re
columns = manual_lag.columns
pattern = r"FREQ_(.*)_IN_LAST_\d+_MONTH"
event_names = list(dict.fromkeys([re.match(pattern, c).group(1) for c in columns if re.match(pattern, c)]))

# Compute change features
new_columns = []
recent_windows = [1, 2, 3, 6]
for event in event_names:
    col_12 = F.col(f"FREQ_{event}_IN_LAST_12_MONTH")
    for N in recent_windows:
        col_N = F.col(f"FREQ_{event}_IN_LAST_{N}_MONTH")
        change_name = f"CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_{event}_IN_LAST_{N}_MONTH"
        change_expr = ((col_N / F.lit(N)) - ((col_12 - col_N) / F.lit(12 - N))).alias(change_name)
        new_columns.append(change_expr)

manual_change = manual_lag.select("*", *new_columns)
manual_change.persist(StorageLevel.MEMORY_ONLY)
print(f"Manual change: {manual_change.count()} rows, {len(manual_change.columns)} cols ({len(event_names)} events)")
```

---

## Cell 30 [python] — Read notebook change output and compare

```python
nb_change = spark.read.format("delta").load(f"{BASE}/rx_change_frequency")
nb_change = nb_change.filter(F.col("PROVIDER_ID").isin(sampled_ids))
nb_change.persist(StorageLevel.MEMORY_ONLY)

# Get common change columns
change_cols = [c for c in manual_change.columns if c.startswith("CHANGE_IN_FREQ_")]
change_cols = [c for c in change_cols if c in nb_change.columns]

joined = manual_change.alias("m").join(nb_change.alias("n"), on=["PROVIDER_ID", "SVC_DT_M"], how="inner")

for col_name in change_cols:
    for row in joined.select("PROVIDER_ID", "SVC_DT_M", F.col(f"m.{col_name}").alias("manual"), F.col(f"n.{col_name}").alias("notebook")).collect():
        hcp_key = f"{row['PROVIDER_ID']}_{row['SVC_DT_M']}"
        compare_values(row["manual"], row["notebook"], col_name, hcp_key, tolerance=1e-4)

chg_pass = sum(1 for r in qc_results if r["feature"] in change_cols and r["status"] == "MATCH")
chg_fail = sum(1 for r in qc_results if r["feature"] in change_cols and r["status"] == "MISMATCH")
print(f"\nFrequency Change: {chg_pass} pass, {chg_fail} fail (of {len(change_cols)} columns)")
```

---

## Cell 31 [md] — Section: Patient Counts QC

```python
%md
### Patient Counts QC

Manual recomputation: countDistinct(PATIENT_ID) per [PROVIDER_ID, COHORT, PRODUCT_GROUP]
per time window [30, 60, 90, 180, 360].
Compare against rx_num_patients_features output.
```

---

## Cell 32 [python] — Manual: cross-join, filter, flag, dedup, countDistinct

```python
# Reuse claims_cross from Cell 9, filter to valid lookback window
patient_claims = claims_cross.filter(
    (F.col("SVC_DT") >= F.col("LOOKBACK_START_DATE")) &
    (F.col("SVC_DT") <= F.col("LOOKBACK_END_DATE"))
)

# Compute days_diff
patient_claims = patient_claims.withColumn(
    "days_diff", F.datediff(F.col("LOOKBACK_END_DATE"), F.col("SVC_DT"))
)

# Flag time windows
pt_time_windows = [30, 60, 90, 180, 360]
for w in pt_time_windows:
    patient_claims = patient_claims.withColumn(
        f"flag_{w}", F.when(F.col("days_diff") <= w, 1).otherwise(0)
    )

# Dedup
claims_dedup = patient_claims.select(
    "PROVIDER_ID", "COHORT", "PRODUCT_GROUP", "PATIENT_ID", *[f"flag_{w}" for w in pt_time_windows]
).dropDuplicates()

# Aggregate
manual_patient_counts = claims_dedup.groupBy("PROVIDER_ID", "COHORT", "PRODUCT_GROUP").agg(
    *[F.countDistinct(F.when(F.col(f"flag_{w}") == 1, F.col("PATIENT_ID"))).alias(f"pt_cnt_{w}_days") for w in pt_time_windows]
)

print(f"Manual patient counts (pre-unpivot): {manual_patient_counts.count()} rows, {len(manual_patient_counts.columns)} cols")
```

---

## Cell 33 [python] — Manual: unpivot and create descriptive column names

```python
# Unpivot
melted = manual_patient_counts.selectExpr(
    "PROVIDER_ID", "COHORT", "PRODUCT_GROUP",
    *[f"pt_cnt_{w}_days as pt_cnt_{w}_days" for w in pt_time_windows]
).selectExpr(
    "PROVIDER_ID", "COHORT", "PRODUCT_GROUP",
    "stack(5, " + ", ".join([f"'pt_cnt_{w}_days', pt_cnt_{w}_days" for w in pt_time_windows]) + ") as (time_window, patient_count)"
)

# Create descriptive column name
melted = melted.withColumn(
    "pivot_col_name",
    F.concat_ws(
        "_",
        F.lit("NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH"),
        F.upper(F.regexp_replace("PRODUCT_GROUP", "[^a-zA-Z0-9]", "_")),
        F.lit("IN_LAST"),
        F.regexp_extract("time_window", r"\d+", 0),
        F.lit("DAYS")
    )
)

# Pivot wide
manual_patient_pivot = melted.groupBy("PROVIDER_ID", "COHORT").pivot("pivot_col_name").agg(F.first("patient_count"))
manual_patient_pivot = manual_patient_pivot.filter(F.col("PROVIDER_ID").isin(sampled_ids))
manual_patient_pivot.persist(StorageLevel.MEMORY_ONLY)
print(f"Manual patient counts (pivoted): {manual_patient_pivot.count()} rows, {len(manual_patient_pivot.columns)} cols")
```

---

## Cell 34 [python] — Read notebook patient counts output and compare

```python
nb_patients = spark.read.format("delta").load(f"{BASE}/rx_num_patients_features")
nb_patients = nb_patients.filter(F.col("PROVIDER_ID").isin(sampled_ids))
nb_patients.persist(StorageLevel.MEMORY_ONLY)

# Compare
manual_cols = set(manual_patient_pivot.columns) - {"PROVIDER_ID", "COHORT"}
nb_cols = set(nb_patients.columns) - {"PROVIDER_ID", "COHORT"}
common_cols = sorted(manual_cols & nb_cols)

joined = manual_patient_pivot.alias("m").join(nb_patients.alias("n"), on=["PROVIDER_ID", "COHORT"], how="inner")

for col_name in common_cols:
    for row in joined.select("PROVIDER_ID", "COHORT", F.col(f"m.{col_name}").alias("manual"), F.col(f"n.{col_name}").alias("notebook")).collect():
        hcp_key = f"{row['PROVIDER_ID']}_{row['COHORT']}"
        compare_values(row["manual"], row["notebook"], col_name, hcp_key)

pt_pass = sum(1 for r in qc_results if r["feature"] in common_cols and r["status"] == "MATCH")
pt_fail = sum(1 for r in qc_results if r["feature"] in common_cols and r["status"] == "MISMATCH")
print(f"\nPatient Counts: {pt_pass} pass, {pt_fail} fail (of {len(common_cols)} columns)")
```

---

## Cell 35 [md] — Section: Known-Discrepancy Self-Test

```python
%md
### Known-Discrepancy Self-Test

This cell intentionally corrupts one feature value in the notebook output to verify
that the QC actually detects mismatches. A QC that only ever reports "all passed"
is indistinguishable from one that doesn't check anything.
```

---

## Cell 36 [python] — Self-test: corrupt one value and confirm QC detects it

```python
# Take one HCP from the first occurrence comparison
test_hcp = sampled_hcp_cohort_ids[0]
test_feature = common_cols[0] if common_cols else "max(EVENT_TIME)_KERENDIA_first_occurrence"

# Get the real notebook value
if test_feature in nb_first_occ.columns:
    real_val = nb_first_occ.filter(F.col("HCP_COHORT_ID") == test_hcp).select(test_feature).first()[0]
    corrupted_val = real_val + 999 if real_val is not None else 1

    # Run comparison with corrupted value
    result = compare_values(real_val, corrupted_val, f"SELFTEST_{test_feature}", test_hcp)
    print(f"Self-test: corrupted {test_feature} for {test_hcp}")
    print(f"  Real value: {real_val}, Corrupted value: {corrupted_val}")
    print(f"  QC detected: {result} (expected MISMATCH)")

    if result == "MISMATCH":
        print("  SELF-TEST PASSED: QC correctly detected the discrepancy")
    else:
        print("  SELF-TEST FAILED: QC did not detect the discrepancy!")
else:
    print(f"Self-test skipped: {test_feature} not in first occurrence output")
```

---

## Cell 37 [md] — Section: Summary

```python
%md
### QC Summary

Aggregates all checks across all feature types and displays pass/fail counts
plus any mismatches with details for investigation.
```

---

## Cell 38 [python] — Aggregate all checks: total, pass, fail

```python
total = len(qc_results)
passes = sum(1 for r in qc_results if r["status"] == "MATCH")
fails = sum(1 for r in qc_results if r["status"] == "MISMATCH")

print(f"=== QC SUMMARY ===")
print(f"Total checks: {total}")
print(f"Passed: {passes}")
print(f"Failed: {fails}")
print(f"Pass rate: {passes/total*100:.1f}%" if total > 0 else "No checks run")

# Breakdown by feature type
feature_types = {
    "First Occurrence": ["first_occurrence"],
    "Recency": ["time_min", "total_events", "unique_events", "skewness"],
    "Frequency Count": ["FREQ_"],
    "Frequency Lag": ["IN_LAST_"],
    "Frequency Change": ["CHANGE_IN_FREQ"],
    "Patient Counts": ["NUM_OF_PATIENTS"],
    "Self-Test": ["SELFTEST"],
}

print("\n=== BREAKDOWN BY FEATURE TYPE ===")
for ftype, patterns in feature_types.items():
    type_results = [r for r in qc_results if any(p in r["feature"] for p in patterns)]
    t_pass = sum(1 for r in type_results if r["status"] == "MATCH")
    t_fail = sum(1 for r in type_results if r["status"] == "MISMATCH")
    print(f"  {ftype}: {t_pass} pass, {t_fail} fail")
```

---

## Cell 39 [python] — Display mismatch details for investigation

```python
mismatches = [r for r in qc_results if r["status"] == "MISMATCH"]

if mismatches:
    print(f"=== {len(mismatches)} MISMATCHES FOUND ===\n")
    for i, m in enumerate(mismatches[:50]):  # Show first 50
        print(f"{i+1}. HCP: {m['hcp_id']}")
        print(f"   Feature: {m['feature']}")
        print(f"   Manual: {m['manual']}")
        print(f"   Notebook: {m['notebook']}")
        print(f"   Delta: {m['delta']}")
        print()

    if len(mismatches) > 50:
        print(f"... and {len(mismatches) - 50} more mismatches")
else:
    print("=== ALL CHECKS PASSED ===")
    print("No mismatches found. All manually recomputed values match the notebook outputs.")
```

---

## Cell 40 [python] — Display overall pass/fail banner

```python
if fails == 0:
    print("=" * 50)
    print("  QC RESULT: ALL PASSED")
    print("=" * 50)
    print(f"  {passes} checks passed across {len(sampled_hcp_cohort_ids)} HCPs")
    print(f"  Feature types: First Occurrence, Recency, Frequency (4 sub-types)")
    print(f"  Self-test: MISMATCH detection confirmed")
    print("=" * 50)
else:
    print("=" * 50)
    print(f"  QC RESULT: {fails} FAILURES DETECTED")
    print("=" * 50)
    print(f"  {passes} passed, {fails} failed out of {total} total checks")
    print(f"  Review mismatch details above to investigate.")
    print("=" * 50)
```

---

## Notes

- **Column sanitization differs between feature types:** First occurrence uses lowercase
  with "/" → "_", while frequency uses uppercase with "/" → " OR ". This mirrors the
  different sanitization rules in the notebook's first_occurrence_of_event helper vs the
  frequency notebook's inline sanitization. The QC template applies the matching rules
  for each feature type.
- The QC notebook reads from the same `rx1_file_path` and `rx_freq_file_path` Delta tables
  as the feature notebooks — NOT from the feature output Delta tables (except to read the
  notebook's computed values for comparison).
- The QC does NOT use `DataFrameMerger` — it manually cross-joins raw claims with anchor dates.
- `EVENT_TYPE` is hardcoded as `"rx"` in the Recency QC. This matches DataFrameMerger's behavior
  for RX claims, but means the QC cannot catch bugs in how DataFrameMerger assigns event types.
- The stratified sample uses `seed=42` by default. Override `pinned_hcps` in Cell 7 to pin
  specific PROVIDER_IDs.
- The known-discrepancy self-test (Cell 36) intentionally corrupts a value to confirm the QC
  detects mismatches. If this test fails, the QC itself has a bug.
