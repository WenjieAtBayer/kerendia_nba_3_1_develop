# IQVIA Claims — Cross-Claim Query Template

This template covers shared setup and **cross-claim** query patterns that span multiple IQVIA LAAD
claim types. For single-claim-type queries, see the specialized query-template.md in each skill.

## Universal Setup (required for ALL IQVIA queries)

```python
# Cell 1 — Connection (run once per session)
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```

```python
# Cell 2 — Config (for date parameters, file paths, drug lists)
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config"
```

```python
# Cell 3 — HCP Universe (standard filter applied to all queries)
hcp_universe = spark.read.format("delta").load(hcp_universe_path)
hcp_universe = hcp_universe.select("PROVIDER_ID").distinct()

provider_npi_mapping = spark.read.format("delta").load(provider_npi_bhid_mapping_path).select("PROVIDER_ID", "NPI_NUMBER")
hcp_universe = hcp_universe.join(provider_npi_mapping, on="PROVIDER_ID", how="left")
```

## Reading Pre-Materialized Delta Outputs

When querying across claim types, prefer reading the pre-materialized Delta files over re-querying
Snowflake. All outputs live under a common base path.

```python
BASE = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output"

# RX
df_rx_12m    = spark.read.format("delta").load(f"{BASE}/rx_input_claims_12M_features_input")
df_rx_total  = spark.read.format("delta").load(f"{BASE}/rx_input_claims_total_events_and_first_occ_features_input")
df_rx_hcp    = spark.read.format("delta").load(f"{BASE}/Rx_01_new")

# DX
df_dx_12m    = spark.read.format("delta").load(f"{BASE}/dx_input_claims_12M_and_first_occ_features_input")
df_dx_all    = spark.read.format("delta").load(f"{BASE}/dx_input_claims_all_events_features_input")
df_dx_hosp   = spark.read.format("delta").load(f"{BASE}/dx_hospitalization_claims_all_events_features_input")
df_dx_03     = spark.read.format("delta").load(f"{BASE}/Dx_03")
df_dx_09     = spark.read.format("delta").load(f"{BASE}/Dx_09")

# PX
df_px_12m    = spark.read.format("delta").load(f"{BASE}/px_input_claims_12M_and_first_occ_features_input")
df_px_all    = spark.read.format("delta").load(f"{BASE}/px_input_claims_all_events_features_input")
df_px_hosp   = spark.read.format("delta").load(f"{BASE}/px_hospitalization_claims_all_events_features_input")

# Lab
df_lab       = spark.read.format("delta").load(f"{BASE}/lab_input_claims_12M_and_first_occ_features_input")
df_lab_03    = spark.read.format("delta").load(f"{BASE}/Lab_03")
df_lab_04    = spark.read.format("delta").load(f"{BASE}/Lab_04")
df_lab_pj    = spark.read.format("delta").load(f"{BASE}/kerendia_nba_3_0_lab_query_output")
```

## Cross-Claim EDA Patterns

### Pattern 1: Patient Activity Summary Across All Claim Types

```python
# Count distinct events per patient across RX, DX, PX, Lab
from pyspark.sql.functions import countDistinct, lit

rx_summary = df_rx_12m.groupBy("PATIENT_ID").agg(
    countDistinct("CLAIM_ID").alias("rx_claims"),
    countDistinct("PRODUCT_GROUP").alias("rx_unique_drugs")
).withColumn("claim_type", lit("RX"))

dx_summary = df_dx_all.groupBy("PATIENT_ID").agg(
    countDistinct("CLAIM_ID").alias("dx_claims"),
    countDistinct("DIAGNOSIS_DESCRIPTION").alias("dx_unique_diagnoses")
).withColumn("claim_type", lit("DX"))

px_summary = df_px_all.groupBy("PATIENT_ID").agg(
    countDistinct("CLAIM_ID").alias("px_claims"),
    countDistinct("PROCEDURE_DESCRIPTION").alias("px_unique_procedures")
).withColumn("claim_type", lit("PX"))

lab_summary = df_lab.groupBy("PATIENT_ID").agg(
    F.count("*").alias("lab_tests"),
    countDistinct("TEST_TYPE").alias("lab_unique_tests")
).withColumn("claim_type", lit("Lab"))
```

### Pattern 2: Patient Timeline — Unified Event Stream

```python
# Build a unified event timeline per patient across all claim types
from pyspark.sql.functions import col, lit

rx_events = df_rx_12m.select(
    col("PATIENT_ID"), col("PROVIDER_ID"), col("SVC_DT"),
    col("PRODUCT_GROUP").alias("EVENT_NAME"), lit("RX").alias("EVENT_TYPE")
)

dx_events = df_dx_all.select(
    col("PATIENT_ID"), col("PROVIDER_ID"), col("SVC_DT"),
    col("DIAGNOSIS_DESCRIPTION").alias("EVENT_NAME"), lit("DX").alias("EVENT_TYPE")
)

px_events = df_px_all.select(
    col("PATIENT_ID"), col("PROVIDER_ID"), col("SVC_DT"),
    col("PROCEDURE_DESCRIPTION").alias("EVENT_NAME"), lit("PX").alias("EVENT_TYPE")
)

lab_events = df_lab.select(
    col("PATIENT_ID"), col("PROVIDER_ID"), col("SVC_DT"),
    col("TEST_TYPE").alias("EVENT_NAME"), lit("LAB").alias("EVENT_TYPE")
)

# Union all events into a single timeline
patient_timeline = rx_events.unionByName(dx_events) \
    .unionByName(px_events) \
    .unionByName(lab_events) \
    .orderBy("PATIENT_ID", "SVC_DT")

patient_timeline.display()
```

### Pattern 3: Provider-Level Cross-Claim Profile

```python
# How many patients does each provider see across each claim type?
from pyspark.sql.functions import countDistinct

provider_profile = (
    df_rx_12m.select("PROVIDER_ID", "PATIENT_ID").withColumn("type", lit("RX"))
    .unionByName(df_dx_all.select("PROVIDER_ID", "PATIENT_ID").withColumn("type", lit("DX")))
    .unionByName(df_px_all.select("PROVIDER_ID", "PATIENT_ID").withColumn("type", lit("PX")))
    .unionByName(df_lab.select("PROVIDER_ID", "PATIENT_ID").withColumn("type", lit("Lab")))
    .groupBy("PROVIDER_ID").pivot("type")
    .agg(countDistinct("PATIENT_ID"))
    .na.fill(0)
    .orderBy("PROVIDER_ID")
)

provider_profile.display()
```

### Pattern 4: CKD Patient Journey — Diagnosis to Treatment

```python
# For patients with CKD diagnosis, find their RX treatment timeline
ckd_patients = df_dx_12m.filter(
    col("DIAGNOSIS_DESCRIPTION").like("%CHRONIC KIDNEY DISEASE%")
).select("PATIENT_ID").distinct()

ckd_rx = df_rx_12m.join(ckd_patients, on="PATIENT_ID", how="inner")
ckd_rx.groupBy("PRODUCT_GROUP").agg(
    countDistinct("PATIENT_ID").alias("ckd_patients"),
    F.count("*").alias("total_claims")
).orderBy(F.desc("ckd_patients")).display()
```

### Pattern 5: Lab-Informed CKD Staging + Treatment Overlap

```python
# Which treatments are prescribed to patients at different GFR stages?
lab_staged = df_lab_pj.filter(col("GFR_STAGE").isNotNull())

# Get latest GFR stage per patient
from pyspark.sql.window import Window
w = Window.partitionBy("PATIENT_ID").orderBy(F.desc("DATE"))
latest_stage = lab_staged.withColumn("rn", F.row_number().over(w)).filter(col("rn") == 1) \
    .select("PATIENT_ID", "GFR_STAGE")

# Join with RX claims
stage_rx = df_rx_12m.join(latest_stage, on="PATIENT_ID", how="inner")
stage_rx.groupBy("GFR_STAGE", "PRODUCT_GROUP").agg(
    countDistinct("PATIENT_ID").alias("patients")
).orderBy("GFR_STAGE", F.desc("patients")).display()
```

### Pattern 6: Hospitalization Event Cross-Reference

```python
# Patients with both DX and PX hospitalization events
dx_hosp_patients = df_dx_hosp.select("PATIENT_ID").distinct()
px_hosp_patients = df_px_hosp.select("PATIENT_ID").distinct()

both_hosp = dx_hosp_patients.join(px_hosp_patients, on="PATIENT_ID", how="inner")
print(f"Patients with both DX and PX hospitalization: {both_hosp.count()}")
print(f"DX hospitalization only: {dx_hosp_patients.subtract(px_hosp_patients).count()}")
print(f"PX hospitalization only: {px_hosp_patients.subtract(dx_hosp_patients).count()}")
```

## Important Constraints

1. **All IQVIA queries execute on Snowflake** via `Get_Data_Snowflakes(query)` — never `spark.sql()`.
2. **Pre-materialized Delta files** are the preferred way to do cross-claim analysis — avoids 15+ separate Snowflake queries.
3. **PATIENT_ID is the join key** across all claim types for patient-level analysis.
4. **PROVIDER_ID is the join key** for HCP-level analysis (note: derived via COALESCE for DX/PX).
5. **NPI_NUMBER** links to the HCP universe and provider dimensions.
6. **Date columns differ** — RX has native `SVC_DT`, DX/PX have `SERVICE_DATE` (aliased), Lab has text `SVC_DT` requiring parsing. When reading Delta outputs, all are standardized to `SVC_DT`.
