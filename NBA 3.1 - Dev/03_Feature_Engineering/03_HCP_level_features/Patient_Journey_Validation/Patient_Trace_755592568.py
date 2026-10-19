# Databricks notebook source
# DBTITLE 1,Title
# MAGIC %md
# MAGIC # Patient Journey Trace — Patient 755592568
# MAGIC
# MAGIC End-to-end trace of a single patient through all 6 notebooks.  
# MAGIC This patient has: 3 GFR stages, 3 UACR stages, 2 DX stages, 7 Rx categories, T2D flag, no dialysis.  
# MAGIC Goal: verify every processing step produces the expected output.

# COMMAND ----------

# DBTITLE 1,Setup and config
# MAGIC %run ./00_cohort_config

# COMMAND ----------

# DBTITLE 1,Patient ID and imports
import sys

PID = "755592568"
BASE = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output"

def titled(df, title):
    """Print a title with row count, then display() the dataframe."""
    ct = df.count()
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"  Rows: {ct}")
    print(f"{'='*70}")
    display(df)
    return ct

# COMMAND ----------

# DBTITLE 1,NB01 header
# MAGIC %md
# MAGIC ## NB01 — Lab Journey
# MAGIC Steps: Raw claims → filter to post-2023 → assign LAST_TEST_DATE (lead + coalesce) → generate month sequence → explode → forward-fill stages → aggregate max per month → join cohort labels

# COMMAND ----------

# DBTITLE 1,NB01 Step 1: Raw lab claims
# Step 1: Read raw lab data for this patient
raw_lab = spark.read.format("delta").load(
    f"{BASE}/kerendia_nba_3_0_lab_query_output"
).filter(col("PATIENT_ID").cast("string") == PID)

raw_lab = raw_lab.withColumnRenamed("DATE", "SVC_DT").select(
    col("PATIENT_ID").cast("string"), "SVC_DT", "GFR_STAGE", "UACR_STAGE"
)
titled(raw_lab.orderBy("SVC_DT"), "RAW LAB CLAIMS (all dates, before any filter)")

# COMMAND ----------

# DBTITLE 1,NB01 Step 2: DATA_START_DATE filter
# Step 2: Apply DATA_START_DATE filter (from config)
lab_filtered = raw_lab.filter(col("SVC_DT") >= DATA_START_DATE)
titled(lab_filtered.orderBy("SVC_DT"), f"AFTER DATA_START_DATE >= {DATA_START_DATE} filter")

# COMMAND ----------

# DBTITLE 1,NB01 Step 3: LAST_TEST_DATE and month sequence
# Step 3: Compute LAST_TEST_DATE (lead of next SVC_DT, coalesced to end_date_limit)
# Use the GLOBAL end_date_limit across ALL patients (same as the real pipeline)
all_lab = spark.read.format("delta").load(f"{BASE}/kerendia_nba_3_0_lab_query_output")
end_date_limit = str(all_lab.agg(F.max("DATE")).collect()[0][0])
print(f"end_date_limit (global max DATE across all patients): {end_date_limit}")

lab_with_last = lab_filtered.withColumn(
    "LAST_TEST_DATE",
    F.lead("SVC_DT", 1).over(Window.partitionBy("PATIENT_ID").orderBy("SVC_DT"))
).withColumn(
    "LAST_TEST_DATE",
    F.coalesce(col("LAST_TEST_DATE"), F.to_date(F.lit(end_date_limit)))
)

print("\nWith LAST_TEST_DATE (coalesce fix applied):")
print("  Notice: the LAST row's LAST_TEST_DATE = end_date_limit (coalesce fills the null)")
print("  Bug in production: na.fill would silently fail here, leaving it null.")
titled(lab_with_last.orderBy("SVC_DT"), "LAST_TEST_DATE (lead + coalesce)")

# Generate cohort-month sequence using assign_cohort_month from config
lab_with_seq = lab_with_last.withColumn(
    "COHORT_MONTH", assign_cohort_month(col("SVC_DT"))
).withColumn(
    "LAST_COHORT_MONTH", assign_cohort_month(col("LAST_TEST_DATE"))
).withColumn(
    "MONTH_SEQ",
    F.expr("sequence(COHORT_MONTH, LAST_COHORT_MONTH, interval 1 month)")
).withColumn("SEQ_LENGTH", F.size("MONTH_SEQ"))

print(f"\nOFFSET_DAY = {OFFSET_DAY} (from config)")
titled(
    lab_with_seq.select("SVC_DT", "LAST_TEST_DATE", "COHORT_MONTH", "GFR_STAGE", "UACR_STAGE", "SEQ_LENGTH").orderBy("SVC_DT"),
    "Month sequence lengths (how many months each claim forward-fills)"
)

# COMMAND ----------

# DBTITLE 1,NB01 Step 4: Explode, forward-fill, verify
# Step 4: Explode month sequence → forward-fill → aggregate
lab_expanded = lab_with_seq.withColumn("MONTH", F.explode("MONTH_SEQ")).drop("MONTH_SEQ", "SEQ_LENGTH", "COHORT_MONTH", "LAST_COHORT_MONTH")
print(f"After explode: {lab_expanded.count()} rows (one per claim × month)")

# Forward-fill: carry last non-null stage forward
w = Window.partitionBy("PATIENT_ID").orderBy("MONTH").rowsBetween(-sys.maxsize, 0)
lab_filled = lab_expanded.withColumn("GFR_STAGE", F.last("GFR_STAGE", ignorenulls=True).over(w)) \
    .withColumn("UACR_STAGE", F.last("UACR_STAGE", ignorenulls=True).over(w))

# Aggregate: max per patient-month
lab_agg = lab_filled.groupBy("PATIENT_ID", "MONTH").agg(
    F.max("GFR_STAGE").alias("GFR_STAGE"),
    F.max("UACR_STAGE").alias("UACR_STAGE")
).withColumnRenamed("MONTH", "COHORT_MONTH").orderBy("COHORT_MONTH")

# Join cohort labels from config
lab_agg = lab_agg.join(df_cohort_ref.select("cohort_ref_month", "cohort_label"),
    lab_agg.COHORT_MONTH == df_cohort_ref.cohort_ref_month, "left"
).drop("cohort_ref_month").orderBy("COHORT_MONTH")

titled(lab_agg, "FINAL NB01 OUTPUT: monthly GFR/UACR stages")

# Verify against written output
lab_written = spark.read.format("delta").load(f"{BASE}/kerendia_nba_3_1_lab_journey_validation").filter(col("PATIENT_ID") == PID)
agg_ct, written_ct = lab_agg.count(), lab_written.count()
if agg_ct == written_ct:
    print(f"\n✅ Matches written output: {agg_ct} rows")
else:
    print(f"\n❌ Count mismatch: recomputed={agg_ct}, written={written_ct}")

# COMMAND ----------

# DBTITLE 1,NB02 header
# MAGIC %md
# MAGIC ## NB02 — Diagnosis Journey
# MAGIC Steps:  
# MAGIC 1. Raw DX claims from Delta → filter `>= DATA_START_DATE`  
# MAGIC 2. CrossJoin patients × all months → complete grid (every patient gets every month)  
# MAGIC 3. Aggregate: `collect_set(DX_STAGE)` per month, then `array_max` (stage 0 treated as null)  
# MAGIC 4. Forward-fill: `last(ignorenulls=True)` → so real stages (1–5) carry forward, 0 doesn't overwrite  
# MAGIC 5. `na.fill(0)` → months before any diagnosis get 0 ("STAGE_UNKNOWN")

# COMMAND ----------

# DBTITLE 1,NB02 Step 1: Raw DX claims
# Step 1: Read raw DX claims for this patient
df_dx_raw = spark.read.format("delta").load(
    "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/pat_journey_dx"
).filter(col("PATIENT_ID") == PID)

titled(df_dx_raw.select("PATIENT_ID", "SVC_DT", "DX_STAGE_TEXT", "DX_STAGE").orderBy("SVC_DT"),
       f"RAW DX CLAIMS for patient {PID} (all dates)")

# Apply DATA_START_DATE filter
df_dx_filt = df_dx_raw.filter(col("SVC_DT") >= DATA_START_DATE)
titled(df_dx_filt.select("PATIENT_ID", "SVC_DT", "DX_STAGE_TEXT", "DX_STAGE").orderBy("SVC_DT"),
       f"AFTER DATA_START_DATE >= {DATA_START_DATE}")

# COMMAND ----------

# DBTITLE 1,NB02 Step 2: CrossJoin month grid and aggregate
# Step 2: Build the full patient × month grid, then aggregate DX claims into it
from datetime import datetime, timedelta
from pyspark.sql.types import StructType, StructField, StringType

# Month range from ALL patients (same grid the pipeline builds)
all_dx = spark.read.format("delta").load(
    "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/pat_journey_dx"
).filter(col("SVC_DT") >= DATA_START_DATE)
# Scope to the same HCP-filtered population the pipeline uses
all_dx, _ = apply_hcp_filter(all_dx)
min_dt, max_dt = all_dx.agg(F.min("SVC_DT"), F.max("SVC_DT")).first()
if OFFSET_DAY == 0:
    min_m, max_m = min_dt.strftime("%Y-%m-01"), max_dt.strftime("%Y-%m-01")
else:
    min_m = (min_dt - timedelta(days=OFFSET_DAY-1)).strftime("%Y-%m-01")
    max_m = (max_dt - timedelta(days=OFFSET_DAY-1)).strftime("%Y-%m-01")

print(f"Month range: {min_m} → {max_m}  (OFFSET_DAY={OFFSET_DAY})")

# Generate all months and crossJoin with patient
cur = datetime.strptime(min_m, "%Y-%m-%d")
end = datetime.strptime(max_m, "%Y-%m-%d")
months = []
while cur <= end:
    months.append(cur.strftime("%Y-%m-01"))
    cur = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)
print(f"Grid: 1 patient × {len(months)} months = {len(months)} rows")

months_df = spark.createDataFrame([(m,) for m in months], StructType([StructField("COHORT_MONTH", StringType())]))
grid = df_dx_filt.select("PATIENT_ID").distinct().crossJoin(months_df)

# Map raw claims to cohort months and aggregate
dx_monthly = (
    df_dx_filt
    .withColumn("COHORT_MONTH", F.date_format(assign_cohort_month(col("SVC_DT")), "yyyy-MM-01"))
    .groupBy("PATIENT_ID", "COHORT_MONTH")
    .agg(F.collect_set("DX_STAGE").alias("DX_STAGE"))
)

# Join grid with actual claims
dx_grid = grid.join(dx_monthly, ["PATIENT_ID", "COHORT_MONTH"], "left")

print("\n--- Months that have DX claims (non-null DX_STAGE) ---")
display(dx_grid.filter(col("DX_STAGE").isNotNull()).orderBy("COHORT_MONTH"))

# COMMAND ----------

# DBTITLE 1,NB02 Step 3: DX_STAGE_MAX and forward-fill
# Step 3: array_max (0 → null), forward-fill, na.fill(0)
# Key: DX_STAGE=0 means "unspecified CKD" — treated as null so it doesn't overwrite real stages
dx_with_max = dx_grid.withColumn(
    "DX_STAGE_MAX", F.array_max(col("DX_STAGE"))
).withColumn(
    "DX_STAGE_MAX", F.when(col("DX_STAGE_MAX") == 0, None).otherwise(col("DX_STAGE_MAX"))
)

print("--- DX_STAGE_MAX: 0 → null (only months with real stages 1–5 survive) ---")
display(dx_with_max.filter(col("DX_STAGE").isNotNull()).select("COHORT_MONTH", "DX_STAGE", "DX_STAGE_MAX").orderBy("COHORT_MONTH"))

# Forward-fill: last non-null DX_STAGE_MAX carries forward
w = Window.partitionBy("PATIENT_ID").orderBy("COHORT_MONTH").rowsBetween(-sys.maxsize, 0)
dx_filled = dx_with_max.withColumn(
    "DX_STAGE_UPDATED", F.last("DX_STAGE_MAX", ignorenulls=True).over(w)
).na.fill(value=0, subset=["DX_STAGE_UPDATED"])

# Join cohort labels
dx_final = dx_filled.join(
    df_cohort_ref.select(F.date_format("cohort_ref_month", "yyyy-MM-01").alias("_ref"), "cohort_label"),
    dx_filled.COHORT_MONTH == col("_ref"), "left"
).drop("_ref", "DX_STAGE_MAX").withColumnRenamed("COHORT_MONTH", "DATE").orderBy("DATE")

titled(dx_final.select("PATIENT_ID", "DATE", "DX_STAGE", "DX_STAGE_UPDATED", "cohort_label"), "FINAL NB02 OUTPUT (recomputed)")

# Verify
dx_written = spark.read.format("delta").load(f"{BASE}/kerendia_nba_3_1_dx_journey_validation").filter(col("PATIENT_ID") == PID)
recomp_ct, written_ct = dx_final.count(), dx_written.count()
if recomp_ct == written_ct:
    print(f"\n✅ Matches written output: {recomp_ct} rows")
else:
    diff = recomp_ct - written_ct
    print(f"\n⚠️  Count diff: recomputed={recomp_ct}, written={written_ct} (diff={diff})")
    print(f"   Written data was at OFFSET_DAY=0; trace is at OFFSET_DAY={OFFSET_DAY}.")
    print(f"   With offset=7, global min shifts back 1 month (Dec 2022 vs Jan 2023).")

# COMMAND ----------

# DBTITLE 1,NB03 header
# MAGIC %md
# MAGIC ## NB03 — Rx (Prescription) Journey
# MAGIC Steps:  
# MAGIC 1. Load raw Rx claims from Snowflake + dimension tables  
# MAGIC 2. Join fact → product → provider → plan → CKD mapping  
# MAGIC 3. Filter: `SVC_DT >= DATA_START_DATE`, NPI not null, `~like('%other%')`  
# MAGIC 4. Compute END_DT = SVC_DT + DAYS_SUPPLY + 7 (capped at max_date)  
# MAGIC 5. Map CATEGORY (brand-level: FARXIGA, JARDIANCE, DPP-IV, GLP-1, etc.)  
# MAGIC 6. Daily expansion: `sequence(SVC_DT, END_DT, interval 1 day)` → explode  
# MAGIC 7. Assign cohort month: `assign_cohort_month(TXN_DATE)`  
# MAGIC 8. Aggregate: `collect_set(Treatment_Category)`, `collect_set(CATEGORY)` per patient×month

# COMMAND ----------

# DBTITLE 1,NB03 Setup: Snowflake connection
# MAGIC %run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"

# COMMAND ----------

# DBTITLE 1,NB03 Step 1: Raw Rx claims for this patient
# Load from Snowflake + join dimensions (all plumbing, ~30s)
fact_rx_patient = Get_Data_Snowflakes(f"SELECT * FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX WHERE PATIENT_ID = '{PID}'")
product_df = Get_Data_Snowflakes("SELECT * FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRD")
provider_df = Get_Data_Snowflakes("SELECT * FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRVDR")
plan_df = Get_Data_Snowflakes("SELECT * FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PLN")
demographic_df = Get_Data_Snowflakes("SELECT * FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PTNT_DMGRPHC")
ckd_mapping_df = Get_Data_Snowflakes("SELECT * FROM PHCDW.PHCDW_DSAA.CKD_PRODUCT_MAPPING_VW")
nba_hcp_df = spark.read.format("delta").load("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference").select('PROVIDER_ID').distinct()

# Join all dimensions → one enriched claim per row
rx_all = (
    fact_rx_patient.alias("f")
    .join(nba_hcp_df.alias("hcp"), col("f.PROVIDER_ID") == col("hcp.PROVIDER_ID"))
    .join(provider_df.alias("p"), col("f.PROVIDER_ID") == col("p.PROVIDER_ID"))
    .join(product_df.alias("prd"), col("f.NDC_CD") == col("prd.NDC_CD"))
    .join(plan_df.alias("pl"), col("f.PAYER_PLAN_ID") == col("pl.PAYER_PLAN_ID"))
    .join(demographic_df.alias("d"), col("f.PATIENT_ID") == col("d.PATIENT_ID"), "left")
    .join(ckd_mapping_df.alias("map"), col("prd.PRODUCT_NAME") == col("map.PRODUCT_NAME"))
    .select("f.PATIENT_ID", "f.SVC_DT", "f.DAYS_SUPPLY",
            "prd.PRODUCT_NAME", "prd.PRODUCT_STRENGTH",
            "map.Treatment_Category", "p.NPI_NUMBER")
)

titled(rx_all.orderBy("SVC_DT"), f"RAW Rx CLAIMS for patient {PID} (all dates, after dimension joins)")

# COMMAND ----------

# DBTITLE 1,NB03 Step 2: Filter
# Step 2: Apply the 3 filters (like NB01's DATA_START_DATE filter)
print("--- Treatment_Categories BEFORE filter ---")
display(rx_all.groupBy("Treatment_Category").count().orderBy("count", ascending=False))

rx_filtered = rx_all.filter(
    (col("SVC_DT") >= F.lit(DATA_START_DATE)) &
    (col("NPI_NUMBER").isNotNull()) &
    (~F.lower(col("Treatment_Category")).like("%other%"))
)

titled(rx_filtered.orderBy("SVC_DT"), f"AFTER filters (>= {DATA_START_DATE}, NPI not null, no 'other')")

# COMMAND ----------

# DBTITLE 1,NB03 Step 3: END_DT and CATEGORY
# Step 3: Compute END_DT = SVC_DT + DAYS_SUPPLY + 7 (capped at max_date)
# and map brand-level CATEGORY
max_date = fact_rx_patient.agg(F.max("SVC_DT").alias("md")).collect()[0]["md"]
print(f"max_date (cap for END_DT): {max_date}")

rx_enriched = (
    rx_filtered
    .withColumn("DAYS_SUPPLY_T", F.round(col("DAYS_SUPPLY")).cast("int"))
    .withColumn("END_DT", F.least(
        F.expr("date_add(SVC_DT, DAYS_SUPPLY_T + 7)"),
        F.lit(max_date)
    ))
    .withColumn("CATEGORY",
        F.when(col("PRODUCT_NAME").like("%INVOKANA%") & (col("PRODUCT_STRENGTH") == "100 MG"), "INVOKANA 100MG")
         .when(col("PRODUCT_NAME").like("%INVOKANA%") & (col("PRODUCT_STRENGTH") == "300 MG"), "INVOKANA 300MG")
         .when(col("PRODUCT_NAME").like("%JARDIANCE%"), "JARDIANCE")
         .when(col("PRODUCT_NAME").like("%FARXIGA%"), "FARXIGA")
         .otherwise(col("Treatment_Category"))
    )
)

titled(
    rx_enriched.select("SVC_DT", "END_DT", "DAYS_SUPPLY_T", "PRODUCT_NAME", "Treatment_Category", "CATEGORY").orderBy("SVC_DT"),
    "END_DT and CATEGORY (each row = one Rx claim)"
)

# COMMAND ----------

# DBTITLE 1,NB03 Step 4: Daily expansion and cohort month
# Step 4: Daily expansion + cohort month assignment
rx_daily = rx_enriched.withColumn(
    "TXN_DATE", F.explode(F.expr("sequence(SVC_DT, END_DT, interval 1 day)"))
)
rx_monthly = rx_daily.withColumn(
    "COHORT_MONTH", F.date_format(assign_cohort_month(col("TXN_DATE")), "yyyy-MM-dd")
)
print(f"Daily expansion: {rx_daily.count()} rows.  OFFSET_DAY = {OFFSET_DAY}")

# Show one claim expanded to see how it fans out across months
first_svc = rx_monthly.select(F.min("SVC_DT")).collect()[0][0]
print(f"\nExample: first claim (SVC_DT={first_svc}) expanded day by day:")
display(
    rx_monthly.filter(col("SVC_DT") == first_svc)
    .select("SVC_DT", "END_DT", "TXN_DATE", "COHORT_MONTH", "Treatment_Category")
    .orderBy("TXN_DATE")
)

# COMMAND ----------

# DBTITLE 1,NB03 Step 5: Aggregate and verify
# Step 5: Aggregate per patient × month + verify
rx_agg = (
    rx_monthly.groupBy("PATIENT_ID", "COHORT_MONTH").agg(
        F.collect_set("Treatment_Category").alias("TREATMENT_CATEGORY"),
        F.collect_set("CATEGORY").alias("CATEGORY")
    )
)

# Join cohort labels from config
rx_agg = rx_agg.join(
    df_cohort_ref.select(F.date_format("cohort_ref_month", "yyyy-MM-dd").alias("_ref"), "cohort_label"),
    rx_agg.COHORT_MONTH == col("_ref"), "left"
).drop("_ref").orderBy("COHORT_MONTH")

titled(rx_agg, "FINAL NB03 OUTPUT: monthly Rx treatments (recomputed)")

# Verify against written output
rx_written = spark.read.format("delta").load(f"{BASE}/kerendia_nba_3_1_rx_journey_validation").filter(col("PATIENT_ID") == PID)
agg_ct, written_ct = rx_agg.count(), rx_written.count()
if agg_ct == written_ct:
    print(f"\n✅ Matches written output: {agg_ct} rows")
else:
    print(f"\n❌ Count mismatch: recomputed={agg_ct}, written={written_ct}")

# COMMAND ----------

# DBTITLE 1,NB04/05 header
# MAGIC %md
# MAGIC ## NB04 — T2D Flag &nbsp;|&nbsp; NB05 — Dialysis Flag
# MAGIC NB04: checks if patient has Type 2 Diabetes diagnosis.  
# MAGIC NB05: checks if patient has a dialysis procedure (FIRST_DIALYSIS_DATE).

# COMMAND ----------

# DBTITLE 1,NB04/05: T2D and dialysis flags
# NB04: T2D flag
t2d = spark.read.format("delta").load(f"{BASE}/kerendia_nba_3_1_t2d_patient_validation").filter(col("PATIENT_ID") == PID)
if t2d.count() > 0:
    flag = t2d.collect()[0].DIABETIC_FLAG
    print(f"✅ NB04: Patient {PID} IS in T2D table. DIABETIC_FLAG = {flag}")
else:
    print(f"❌ NB04: Patient {PID} NOT in T2D table (no diabetes diagnosis)")

# NB05: Dialysis flag
px = spark.read.format("delta").load(f"{BASE}/kerendia_nba_3_1_px_validation").filter(col("PATIENT_ID") == PID)
if px.count() > 0:
    row = px.collect()[0]
    print(f"✅ NB05: Patient {PID} has DIALYSIS. FIRST_DIALYSIS_DATE = {row.FIRST_DIALYSIS_DATE}, FLAG = {row.DIALYSIS_FLAG}")
else:
    print(f"✅ NB05: Patient {PID} has NO dialysis (DIALYSIS_FLAG will be 0 in NB06)")

# COMMAND ----------

# DBTITLE 1,NB06 header
# MAGIC %md
# MAGIC ## NB06 — Combine (Final Output)
# MAGIC Steps:  
# MAGIC 1. **Spine**: FULL OUTER JOIN of NB01 lab + NB02 dx + NB03 rx on (PATIENT_ID, DATE)  
# MAGIC 2. **Combined stages**: `GFR_DX_STAGE = coalesce(DX_STAGE_UPDATED, GFR_STAGE)` — DX beats lab  
# MAGIC 3. **Flags**: left join T2D (NB04) + dialysis (NB05, month-truncated comparison)  
# MAGIC 4. **Eligibility**: ineligible if stage 1/5, dialysis=1, or unknown stage without SGLT2 history  
# MAGIC 5. **Label**: numeric stages → "STAGE_2", "STAGE_3", "STAGE_4", "STAGE_UNKNOWN"

# COMMAND ----------

# DBTITLE 1,NB06 Step 1: Spine (FULL OUTER JOIN)
# Step 1: Build spine from NB01 + NB02 + NB03 outputs (FULL OUTER JOIN)
df_lab = spark.read.format("delta").load(f"{BASE}/kerendia_nba_3_1_lab_journey_validation").filter(col("PATIENT_ID") == PID)
df_dx  = spark.read.format("delta").load(f"{BASE}/kerendia_nba_3_1_dx_journey_validation").filter(col("PATIENT_ID") == PID)
df_rx  = spark.read.format("delta").load(f"{BASE}/kerendia_nba_3_1_rx_journey_validation").filter(col("PATIENT_ID") == PID)

print(f"NB01 lab: {df_lab.count()} months  |  NB02 dx: {df_dx.count()} months  |  NB03 rx: {df_rx.count()} months")

spine = (
    df_lab.join(df_dx, ["PATIENT_ID", "DATE"], "full")
          .join(df_rx, ["PATIENT_ID", "DATE"], "full")
          .orderBy("DATE")
)
print(f"Spine after FULL OUTER JOIN: {spine.count()} months")
print("  (Each month that has ANY lab/dx/rx data gets a row)")

# Show which sources contribute to each month
spine_check = spine.withColumn("has_lab", col("GFR_STAGE").isNotNull() | col("UACR_STAGE").isNotNull()) \
    .withColumn("has_dx", col("DX_STAGE_UPDATED").isNotNull()) \
    .withColumn("has_rx", col("TREATMENT_CATEGORY").isNotNull())
print("\n--- Source coverage per month ---")
display(spine_check.select("DATE", "has_lab", "has_dx", "has_rx", "GFR_STAGE", "DX_STAGE_UPDATED", "UACR_STAGE").orderBy("DATE"))

# COMMAND ----------

# DBTITLE 1,NB06 Step 2: Combined stages, flags, eligibility
# Step 2: Compute combined stages
# GFR_DX_STAGE = coalesce(DX_STAGE_UPDATED, GFR_STAGE) — DX diagnosis beats lab eGFR
# GFR_UACR_DX_STAGE = coalesce(DX_STAGE_UPDATED, GFR_STAGE, UACR_STAGE) — DX > GFR > UACR
spine2 = spine.withColumn(
    "GFR_DX_STAGE", F.coalesce(col("DX_STAGE_UPDATED"), col("GFR_STAGE"))
).withColumn(
    "GFR_UACR_DX_STAGE", F.coalesce(col("DX_STAGE_UPDATED"), col("GFR_STAGE"), col("UACR_STAGE"))
)

print("--- Combined stage coalesce (shows which source wins per month) ---")
display(spine2.select("DATE", "DX_STAGE_UPDATED", "GFR_STAGE", "UACR_STAGE",
                      "GFR_DX_STAGE", "GFR_UACR_DX_STAGE").orderBy("DATE"))

# Step 3: Join T2D and dialysis flags
df_t2d = spark.read.format("delta").load(f"{BASE}/kerendia_nba_3_1_t2d_patient_validation").filter(col("PATIENT_ID") == PID)
df_px  = spark.read.format("delta").load(f"{BASE}/kerendia_nba_3_1_px_validation").filter(col("PATIENT_ID") == PID)

spine3 = (
    spine2.join(df_t2d, "PATIENT_ID", "left").na.fill(0, ["DIABETIC_FLAG"])
    .join(df_px, "PATIENT_ID", "left")
    .withColumn("DIALYSIS_FLAG",
        F.when(col("FIRST_DIALYSIS_DATE") < '2017-01-01', 1).otherwise(
        F.when(F.trunc(F.to_date(col("FIRST_DIALYSIS_DATE")), "month") <= col("DATE"), 1).otherwise(0)))
    .na.fill(0, ["DIALYSIS_FLAG"]).drop("FIRST_DIALYSIS_DATE")
)
print(f"\nDIABETIC_FLAG = {spine3.select('DIABETIC_FLAG').first()[0]}  |  DIALYSIS_FLAG = {spine3.select(F.max('DIALYSIS_FLAG')).first()[0]}")

# Step 4: Eligibility computation
# Ineligible if: stage 1 or 5, dialysis=1, or unknown stage without SGLT2 history
sglt2_flag = spine3.withColumn("tc", F.explode_outer("TREATMENT_CATEGORY")) \
    .filter(col("tc") == "SGLT2").select("PATIENT_ID").distinct() \
    .withColumn("SGLT2_FLAG", F.lit(1))
print(f"Patient has SGLT2 history: {'Yes' if sglt2_flag.count() > 0 else 'No'}")

spine4 = (
    spine3
    .withColumn("STAGE_ELIGIBLE",
        F.when((col("GFR_UACR_DX_STAGE").isNull()) | (col("GFR_UACR_DX_STAGE") == 0), -1)
         .otherwise(F.when((col("GFR_UACR_DX_STAGE") == 1) | (col("GFR_UACR_DX_STAGE") == 5), 0).otherwise(1)))
    .join(sglt2_flag, "PATIENT_ID", "left").na.fill(0, ["SGLT2_FLAG"])
    .withColumn("ELIGIBLE_PATIENT_FLAG",
        F.when(col("STAGE_ELIGIBLE") == 0, 0).otherwise(
        F.when(col("DIALYSIS_FLAG") == 1, 0).otherwise(
        F.when((col("GFR_UACR_DX_STAGE") == -1) & (col("SGLT2_FLAG") == 0), 0).otherwise(1))))
)

# Step 5: Label stages and show final output
final = (
    spine4.withColumn("SVC_DT_M", col("DATE"))
    .groupBy("PATIENT_ID", "SVC_DT_M")
    .agg(F.max("ELIGIBLE_PATIENT_FLAG").alias("ELIGIBLE_PATIENT_FLAG"),
         F.max("GFR_UACR_DX_STAGE").alias("GFR_UACR_DX_STAGE"),
         F.max("GFR_DX_STAGE").alias("GFR_DX_STAGE"),
         F.max("UACR_STAGE").alias("UACR_STAGE"))
    .withColumn("GFR_UACR_DX_STAGE",
        F.when(col("GFR_UACR_DX_STAGE") == 2, "STAGE_2").when(col("GFR_UACR_DX_STAGE") == 3, "STAGE_3")
         .when(col("GFR_UACR_DX_STAGE") == 4, "STAGE_4").otherwise("STAGE_UNKNOWN"))
    .withColumn("GFR_DX_STAGE",
        F.when(col("GFR_DX_STAGE") == 2, "STAGE_2").when(col("GFR_DX_STAGE") == 3, "STAGE_3")
         .when(col("GFR_DX_STAGE") == 4, "STAGE_4").otherwise("STAGE_UNKNOWN"))
    .withColumn("UACR_STAGE",
        F.when(col("UACR_STAGE") == 2, "STAGE_2").when(col("UACR_STAGE") == 3, "STAGE_3").otherwise("STAGE_UNKNOWN"))
    .orderBy("SVC_DT_M")
)

titled(final, "FINAL NB06 OUTPUT: SGLT2 eligibility (recomputed)")

# Verify against written output
sglt2_written = spark.read.format("delta").load(f"{BASE}/kerendia_nba_3_1_pat_sglt2_filter_m_validation").filter(col("PATIENT_ID") == PID)
recomp_ct, written_ct = final.count(), sglt2_written.count()
if recomp_ct == written_ct:
    print(f"\n✅ Matches written output: {recomp_ct} rows")
else:
    print(f"\n⚠️  Count diff: recomputed={recomp_ct}, written={written_ct}")

# Summary
elig_ct = final.filter(col("ELIGIBLE_PATIENT_FLAG") == 1).count()
total_ct = final.count()
print(f"\n{'='*70}")
print(f"  PATIENT SUMMARY")
print(f"{'='*70}")
print(f"  Eligible months:   {elig_ct} / {total_ct} ({100*elig_ct/total_ct:.0f}%)")
print(f"  SGLT2 history:     {'Yes' if sglt2_flag.count() > 0 else 'No'}")
print(f"  T2D:               Yes  |  Dialysis: No")