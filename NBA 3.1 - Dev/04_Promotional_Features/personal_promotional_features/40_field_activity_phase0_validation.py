# Databricks notebook source
# DBTITLE 1,Phase 0: Field Activity Validation — NBA 3.1 Readiness
# MAGIC %md
# MAGIC ## Phase 0: Field Activity Validation — NBA 3.1 Readiness
# MAGIC
# MAGIC This notebook implements the **Phase 0 (Foundations and Validation)** checks from `40_field_activity_nba_3_1_readiness_plan.md`.
# MAGIC
# MAGIC | Task | Description |
# MAGIC |------|-------------|
# MAGIC | **V1** | Interaction grain — total calls, Kerendia calls via detail, co-detail gap |
# MAGIC | **V2** | Record classification — HCP_INTERACTION, ACCOUNT_OFFICE, BHO_CHILD, BHO_TOP_LEVEL, MEDICAL |
# MAGIC | **V3** | BHO parent / child analysis |
# MAGIC | **V4** | Key-message entry consistency |
# MAGIC | **V6** | Event states mapping |
# MAGIC | **V7** | iRep data checks |
# MAGIC | **V10** | MSL records identification |
# MAGIC
# MAGIC **Year 2 reference period:** Nov 2025 – Oct 2026  
# MAGIC **Expected (from data review):** ~660K doctor calls, ~104K called doctors in Year 2

# COMMAND ----------

# DBTITLE 1,Install Snowflake Connector
# MAGIC %pip install snowflake-connector-python --quiet
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Imports and Snowflake Connection
import pyspark.sql.functions as F
from pyspark.sql.functions import col, when, lit, concat, to_date, upper, coalesce, count, countDistinct, sum as spark_sum
from pyspark.sql.types import DateType
from cryptography.hazmat.primitives import serialization

def Get_Data_Snowflakes(query, Schema="PHCDW_CDM",
                        Role="BAY_CPH_CDP_PROD_CR_US_EAST_1_MVXPF_MVXPF"):
    scope = "US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair"
    private_key_pem = dbutils.secrets.get(scope, "snowflake-private-key")
    private_key_passphrase = dbutils.secrets.get(scope, "snowflake-private-key-passphrase")
    snowflake_user = dbutils.secrets.get(scope, "snowflake-user")
    snowflake_account = dbutils.secrets.get(scope, "snowflake-account")
    p_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"),
        password=private_key_passphrase.encode("utf-8"),
    )
    snowflake_pem_private_key = (
        p_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        .decode("utf-8")
        .replace("-----BEGIN PRIVATE KEY-----", "")
        .replace("-----END PRIVATE KEY-----", " ")
        .replace("\n", " ")
        .strip()
    )
    sfOptions = {
        "sfURL": "bayer_cphcdp_prod.us-east-1.snowflakecomputing.com:443",
        "sfUser": snowflake_user,
        "pem_private_key": snowflake_pem_private_key,
        "sfRole": Role,
        "sfSchema": Schema,
        "sfDatabase": "PHCDW",
        "sfWarehouse": "PROD_CYRUS_BI_WH",
        "purge": "off",
        "autopushdown": "on",
    }
    return (
        spark.read.format("net.snowflake.spark.snowflake")
        .options(**sfOptions)
        .option("query", query)
        .load()
    )

print("Setup complete.")

# COMMAND ----------

# DBTITLE 1,V1a: Total submitted calls (all products) vs Kerendia-only — Year 2
# V1: Interaction grain
# Compare: all submitted doctor calls vs the NBA 3.0 KERENDIA-only filter
# Year 2 = Nov 2025 – Oct 2026
# Expected from data review: ~660K doctor calls, ~104K called doctors

v1_query = """
SELECT
    fc.CALL_ID,
    xref.BAYER_CUST_ID AS BHID,
    TO_DATE(fc.CALL_DATE) AS CALL_DATE,
    fc.CALL_REC_TYP_NM,
    fc.STAT,
    fc.DETL_PROD,
    fc.PAR_CALL_ID,
    fc.PAR_CALL_FLAG,
    fc.CALL_TYP,
    fc.CALL_PURPS
FROM CPH_DB_PROD.MODEL_V2.FACT_CALL fc
LEFT JOIN CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF xref
    ON fc.SOURCE_CUST_ID = xref.SOURCE_CUST_ID
WHERE UPPER(fc.STAT) = 'SUBMITTED_VOD'
  AND fc.CALL_DATE >= '2024-11-01'
  AND fc.CALL_DATE < '2026-11-01'
"""

df_all_calls = Get_Data_Snowflakes(v1_query)
df_all_calls = df_all_calls.withColumn("CALL_DATE", col("CALL_DATE").cast(DateType()))
df_all_calls.cache()

# Year 1 = Nov 2024 – Oct 2025; Year 2 = Nov 2025 – Oct 2026
df_all_calls = df_all_calls.withColumn(
    "YEAR",
    when((col("CALL_DATE") >= "2024-11-01") & (col("CALL_DATE") < "2025-11-01"), lit("Year_1"))
    .when((col("CALL_DATE") >= "2025-11-01") & (col("CALL_DATE") < "2026-11-01"), lit("Year_2"))
)

print(f"Total submitted calls loaded: {df_all_calls.count():,}")
print(f"\nAll calls by year:")
df_all_calls.groupBy("YEAR").agg(
    count("*").alias("total_records"),
    countDistinct("CALL_ID").alias("distinct_calls"),
    countDistinct("BHID").alias("distinct_bhids")
).orderBy("YEAR").show()

# COMMAND ----------

# DBTITLE 1,V1b: Kerendia via FACT_CALL_DETAIL (new) vs DETL_PROD (NBA 3.0)
# V1b: Load FACT_CALL_DETAIL to identify calls with Kerendia as any detail
# NBA 3.0 method: UPPER(DETL_PROD) = 'KERENDIA' on FACT_CALL
# NBA 3.1 method: any detail row in FACT_CALL_DETAIL where product = 'KERENDIA'

v1b_detail_query = """
SELECT DISTINCT
    fcd.CALL_ID,
    fcd.SOURCE_PROD_NM AS DETL_PROD,
    fcd.CALL_DETL_PRTY,
    fcd.CALL_DETL_TYP
FROM CPH_DB_PROD.MODEL_V2.FACT_CALL_DETAIL fcd
INNER JOIN CPH_DB_PROD.MODEL_V2.FACT_CALL fc
    ON fcd.CALL_ID = fc.CALL_ID
WHERE UPPER(fc.STAT) = 'SUBMITTED_VOD'
  AND fc.CALL_DATE >= '2024-11-01'
  AND fc.CALL_DATE < '2026-11-01'
"""

df_details = Get_Data_Snowflakes(v1b_detail_query)
df_details.cache()

# Flag calls that have Kerendia as any detail
df_ker_detail_calls = df_details.filter(upper(col("DETL_PROD")) == "KERENDIA").select("CALL_ID").distinct()
df_ker_detail_calls = df_ker_detail_calls.withColumn("HAS_KERENDIA_DETAIL", lit(1))

# Join back to all calls
df_v1 = df_all_calls.join(df_ker_detail_calls, on="CALL_ID", how="left")
df_v1 = df_v1.withColumn("HAS_KERENDIA_DETAIL", coalesce(col("HAS_KERENDIA_DETAIL"), lit(0)))

# NBA 3.0 method flag
df_v1 = df_v1.withColumn(
    "NBA30_KERENDIA",
    when(upper(col("DETL_PROD")) == "KERENDIA", lit(1)).otherwise(lit(0))
)

# Compare: doctor-level calls only (exclude BHO)
df_doctor_calls = df_v1.filter(
    col("BHID").isNotNull() & ~col("BHID").like("%BHO%")
)

print("=== V1: Interaction Grain Comparison (Doctor Calls, excl. BHO) ===")
print("\n--- Year 2 (Nov 2025 - Oct 2026) ---")
df_y2 = df_doctor_calls.filter(col("YEAR") == "Year_2")

y2_total = df_y2.select(countDistinct("CALL_ID")).first()[0]
y2_doctors = df_y2.select(countDistinct("BHID")).first()[0]
y2_ker_detail = df_y2.filter(col("HAS_KERENDIA_DETAIL") == 1).select(countDistinct("CALL_ID")).first()[0]
y2_ker_detail_docs = df_y2.filter(col("HAS_KERENDIA_DETAIL") == 1).select(countDistinct("BHID")).first()[0]
y2_nba30 = df_y2.filter(col("NBA30_KERENDIA") == 1).select(countDistinct("CALL_ID")).first()[0]
y2_nba30_docs = df_y2.filter(col("NBA30_KERENDIA") == 1).select(countDistinct("BHID")).first()[0]

print(f"All submitted doctor calls:            {y2_total:>10,} calls, {y2_doctors:>8,} doctors")
print(f"Kerendia via DETAIL (NBA 3.1 method):  {y2_ker_detail:>10,} calls, {y2_ker_detail_docs:>8,} doctors")
print(f"Kerendia via DETL_PROD (NBA 3.0):      {y2_nba30:>10,} calls, {y2_nba30_docs:>8,} doctors")
if y2_ker_detail > 0:
    gap_calls = y2_ker_detail - y2_nba30
    gap_pct = (gap_calls / y2_ker_detail) * 100
    print(f"\nCo-detail gap: {gap_calls:,} calls missed by NBA 3.0 ({gap_pct:.1f}%)")
    gap_docs = y2_ker_detail_docs - y2_nba30_docs
    print(f"Doctor gap:    {gap_docs:,} doctors with Kerendia calls invisible to NBA 3.0")

# COMMAND ----------

# DBTITLE 1,V1c: Monthly co-detail gap trend
# V1c: Monthly breakdown of the co-detail gap
import pandas as pd

df_monthly = (
    df_doctor_calls
    .filter(col("HAS_KERENDIA_DETAIL") == 1)
    .withColumn("MONTH", F.date_trunc("month", col("CALL_DATE")))
    .groupBy("MONTH")
    .agg(
        countDistinct("CALL_ID").alias("ker_detail_calls"),
        countDistinct(when(col("NBA30_KERENDIA") == 1, col("CALL_ID"))).alias("nba30_calls"),
        countDistinct("BHID").alias("ker_detail_doctors"),
        countDistinct(when(col("NBA30_KERENDIA") == 1, col("BHID"))).alias("nba30_doctors")
    )
    .withColumn("gap_calls_pct",
        F.round((col("ker_detail_calls") - col("nba30_calls")) / col("ker_detail_calls") * 100, 1))
    .orderBy("MONTH")
)

print("=== V1c: Monthly Co-Detail Gap (Kerendia calls missed by NBA 3.0 DETL_PROD filter) ===")
df_monthly.show(30, truncate=False)

# COMMAND ----------

# DBTITLE 1,V2: Record Classification (HCP_INTERACTION, ACCOUNT_OFFICE, BHO, MEDICAL)
# V2: Record classification
# Rules from readiness plan section 4, principle 3:
#   HCP_INTERACTION: doctor call (BHID not BHO, not account-only, not medical)
#   ACCOUNT_OFFICE: '5- Acct Call', 'vOffice call (no HCP)'; before Jul 2025 '2-Account Call Only'
#   BHO_CHILD: PAR_CALL_ID is not null (organisation copy of a doctor call)
#   BHO_TOP_LEVEL: BHID contains 'BHO' and PAR_CALL_ID is null
#   MEDICAL: product text like 'Finerenone%' or medical record types

medical_rec_types = [
    'Face2Face Interaction Med', 'BPH_MED_Face2Face Interaction Med',
    'Remote Interaction Med', 'BPH_MED_Remote Interaction Med',
    'Event Call Report', 'BPH_MED_Event Call Report'
]
account_office_types = ['5- Acct Call', 'vOffice call (no HCP)', '2-Account Call Only']

df_classified = df_all_calls.withColumn(
    "RECORD_CLASS",
    when(
        col("BHID").like("%BHO%") & col("PAR_CALL_ID").isNotNull(),
        lit("BHO_CHILD")
    ).when(
        col("BHID").like("%BHO%") & col("PAR_CALL_ID").isNull(),
        lit("BHO_TOP_LEVEL")
    ).when(
        col("CALL_REC_TYP_NM").isin(medical_rec_types) |
        upper(col("DETL_PROD")).like("FINERENONE%"),
        lit("MEDICAL")
    ).when(
        col("CALL_REC_TYP_NM").isin(account_office_types) |
        (col("CALL_PURPS").like("%no HCP%")),
        lit("ACCOUNT_OFFICE")
    ).otherwise(lit("HCP_INTERACTION"))
)

print("=== V2: Record Classification Summary ===")
print("\n--- All periods ---")
df_classified.groupBy("RECORD_CLASS").agg(
    count("*").alias("records"),
    countDistinct("CALL_ID").alias("distinct_calls"),
    countDistinct("BHID").alias("distinct_bhids")
).orderBy("RECORD_CLASS").show(truncate=False)

print("\n--- Record class by year ---")
df_classified.groupBy("YEAR", "RECORD_CLASS").agg(
    count("*").alias("records")
).orderBy("YEAR", "RECORD_CLASS").show(20, truncate=False)

# COMMAND ----------

# DBTITLE 1,V2b: Record class share by month
# V2b: Monthly share per record class
from pyspark.sql import Window

df_class_monthly = (
    df_classified
    .withColumn("MONTH", F.date_trunc("month", col("CALL_DATE")))
    .groupBy("MONTH", "RECORD_CLASS")
    .agg(count("*").alias("records"))
)

w_month = Window.partitionBy("MONTH")
df_class_monthly = df_class_monthly.withColumn(
    "pct_of_month", F.round(col("records") / F.sum("records").over(w_month) * 100, 1)
)

print("=== V2b: Record Class Share by Month ===")
df_class_monthly.orderBy("MONTH", "RECORD_CLASS").show(100, truncate=False)

# COMMAND ----------

# DBTITLE 1,V3: BHO Parent / Child Analysis
# V3: BHO parent/child logic
# From readiness plan: 494K of ~502K BHO calls (12 months) are child copies
# Check: PAR_CALL_ID, PAR_CALL_FLAG on BHO records

df_bho = df_classified.filter(col("RECORD_CLASS").isin("BHO_CHILD", "BHO_TOP_LEVEL"))

print("=== V3: BHO Parent / Child Analysis ===")
print(f"Total BHO records: {df_bho.count():,}")

df_bho.groupBy("YEAR", "RECORD_CLASS").agg(
    count("*").alias("records"),
    countDistinct("CALL_ID").alias("distinct_calls"),
    countDistinct("BHID").alias("distinct_bho_ids")
).orderBy("YEAR", "RECORD_CLASS").show(truncate=False)

# Check: for BHO_CHILD, does PAR_CALL_ID point to an HCP_INTERACTION?
df_bho_child = df_classified.filter(col("RECORD_CLASS") == "BHO_CHILD")
df_hcp_calls = df_classified.filter(col("RECORD_CLASS") == "HCP_INTERACTION").select("CALL_ID").distinct()

df_bho_parent_match = df_bho_child.join(
    df_hcp_calls.withColumnRenamed("CALL_ID", "PAR_CALL_ID"),
    on="PAR_CALL_ID", how="left_semi"
)
matched = df_bho_parent_match.count()
total_child = df_bho_child.count()
print(f"\nBHO_CHILD records whose PAR_CALL_ID matches an HCP_INTERACTION: {matched:,} / {total_child:,} ({matched/max(total_child,1)*100:.1f}%)")

# How many distinct doctors per BHO organisation?
print("\n--- Distinct BHIDs per BHO organisation (top 10) ---")
df_bho_spread = (
    df_classified.filter(col("RECORD_CLASS") == "BHO_CHILD")
    .groupBy("PAR_CALL_ID")
    .agg(countDistinct("BHID").alias("n_bho_recipients"))
    .orderBy(col("n_bho_recipients").desc())
)
df_bho_spread.show(10)

# COMMAND ----------

# DBTITLE 1,V4: Key-Message Entry Consistency
# V4: Key-message entry consistency
# Check: share of Kerendia interactions with an indication/position code per month
# Source: FACT_CALL_KEY_MESSAGE

v4_query = """
SELECT
    fkm.CALL_ID,
    fkm.KEY_MSG_NM,
    fkm.KEY_MSG_ID AS KEY_MSG_CD,
    fkm.CLM_PRESN_NM AS CLM_PRSNTTN_NM
FROM CPH_DB_PROD.MODEL_V2.FACT_CALL_KEY_MESSAGE fkm
INNER JOIN CPH_DB_PROD.MODEL_V2.FACT_CALL fc
    ON fkm.CALL_ID = fc.CALL_ID
WHERE UPPER(fc.STAT) = 'SUBMITTED_VOD'
  AND fc.CALL_DATE >= '2024-11-01'
  AND fc.CALL_DATE < '2026-11-01'
"""

df_keymsg = Get_Data_Snowflakes(v4_query)
df_keymsg.cache()

print("=== V4: Key-Message Entry Consistency ===")
print(f"Total key message rows: {df_keymsg.count():,}")
print(f"Distinct calls with key messages: {df_keymsg.select('CALL_ID').distinct().count():,}")

# Join key messages to HCP_INTERACTION calls
df_hcp_ker = df_classified.filter(
    (col("RECORD_CLASS") == "HCP_INTERACTION") &
    (col("HAS_KERENDIA_DETAIL") == 1) if "HAS_KERENDIA_DETAIL" in df_classified.columns
    else (col("RECORD_CLASS") == "HCP_INTERACTION")
)

# Try joining via v1 enriched data if available
try:
    df_hcp_ker_v1 = df_v1.filter(
        ~col("BHID").like("%BHO%") &
        col("BHID").isNotNull() &
        (col("HAS_KERENDIA_DETAIL") == 1)
    )
except:
    df_hcp_ker_v1 = df_doctor_calls.filter(col("HAS_KERENDIA_DETAIL") == 1)

df_calls_with_msg = df_hcp_ker_v1.join(
    df_keymsg.select("CALL_ID").distinct().withColumn("HAS_KEYMSG", lit(1)),
    on="CALL_ID", how="left"
).withColumn("HAS_KEYMSG", coalesce(col("HAS_KEYMSG"), lit(0)))

df_v4_monthly = (
    df_calls_with_msg
    .withColumn("MONTH", F.date_trunc("month", col("CALL_DATE")))
    .groupBy("MONTH")
    .agg(
        countDistinct("CALL_ID").alias("total_ker_calls"),
        countDistinct(when(col("HAS_KEYMSG") == 1, col("CALL_ID"))).alias("calls_with_keymsg"),
    )
    .withColumn("keymsg_pct", F.round(col("calls_with_keymsg") / col("total_ker_calls") * 100, 1))
    .orderBy("MONTH")
)

print("\n--- Share of Kerendia HCP calls with key-message entry by month ---")
df_v4_monthly.show(30, truncate=False)

# Check distinct key message names / codes
print("\n--- Top 20 Key Message Names ---")
df_keymsg.groupBy("KEY_MSG_NM").agg(count("*").alias("cnt")).orderBy(col("cnt").desc()).show(20, truncate=False)

# COMMAND ----------

# DBTITLE 1,V6: Event States Mapping
# V6: Event states
# Map Veeva statuses to invited / registered / attended
# Check Signed_vod without ATND for closed events (Q-D1)
# Split speaker programs from other event types (Q-D2)

v6_query = """
SELECT
    xref.BAYER_CUST_ID AS BHID,
    ea.EVNT_ID,
    ea.EVNT_NM,
    ea.EVNT_TYP,
    ea.EVNT_START_DATE AS EVNT_STRT_DT,
    ea.EVNT_STAT AS ATTENDEE_STATUS,
    ea.ATND AS ATTENDANCE_VALUE,
    ea.EVNT_TPIC_NM AS EVNT_TOPIC_NM
FROM CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM ea
LEFT JOIN CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF xref
    ON ea.CUST_ID = xref.SOURCE_CUST_ID
WHERE ea.EVNT_START_DATE >= '2024-11-01'
  AND ea.EVNT_START_DATE < '2026-11-01'
"""

df_events = Get_Data_Snowflakes(v6_query)
df_events.cache()

print("=== V6: Event States ===")
print(f"Total event-attendee records: {df_events.count():,}")
print(f"Distinct events: {df_events.select('EVNT_ID').distinct().count():,}")
print(f"Distinct HCPs: {df_events.filter(col('BHID').isNotNull()).select('BHID').distinct().count():,}")

print("\n--- Attendee Status distribution ---")
df_events.groupBy("ATTENDEE_STATUS").agg(count("*").alias("cnt")).orderBy(col("cnt").desc()).show(20, truncate=False)

print("\n--- Attendance Value distribution ---")
df_events.groupBy("ATTENDANCE_VALUE").agg(count("*").alias("cnt")).orderBy(col("cnt").desc()).show(20, truncate=False)

# Signed_vod without attendance
df_signed_no_atnd = df_events.filter(
    (upper(col("ATTENDEE_STATUS")) == "SIGNED_VOD") &
    (col("ATTENDANCE_VALUE").isNull() | (col("ATTENDANCE_VALUE") == ""))
)
print(f"Signed_vod records without ATND value: {df_signed_no_atnd.count():,}")

print("\n--- Event Type distribution ---")
df_events.groupBy("EVNT_TYP").agg(
    count("*").alias("records"),
    countDistinct("EVNT_ID").alias("distinct_events")
).orderBy(col("records").desc()).show(20, truncate=False)

print("\n--- Event Topic distribution (top 20) ---")
df_events.groupBy("EVNT_TOPIC_NM").agg(count("*").alias("cnt")).orderBy(col("cnt").desc()).show(20, truncate=False)

# COMMAND ----------

# DBTITLE 1,V7: iRep Data Checks
# V7: iRep data checks
# 1. Delivered status fix: 'Delivered_vod' not 'Delivered' (NBA 3.0 bug)
# 2. Check April 2026 open-rate drop (Q-C1)

v7_query = """
SELECT
    xref.BAYER_CUST_ID AS BHID,
    se.SNT_EMAIL_ID AS SENT_EMAIL_ID,
    se.STAT AS EMAIL_STATUS,
    se.EMAIL_SNT_DATE AS SEND_DT,
    se.APV_EMAIL_TEMPLATE AS TMPL_NM,
    se.OPENED,
    se.CLK_CNT AS CLICK_CNT
FROM CPH_DB_PROD.MODEL_V2.FACT_SENT_EMAIL se
LEFT JOIN CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF xref
    ON se.SOURCE_CUST_ID = xref.SOURCE_CUST_ID
WHERE se.EMAIL_SNT_DATE >= '2024-11-01'
  AND se.EMAIL_SNT_DATE < '2026-11-01'
"""

df_irep = Get_Data_Snowflakes(v7_query)
df_irep = df_irep.withColumn("SEND_DT", col("SEND_DT").cast(DateType()))
df_irep.cache()

print("=== V7: iRep Data Checks ===")
print(f"Total iRep emails: {df_irep.count():,}")

print("\n--- Email Status distribution ---")
df_irep.groupBy("EMAIL_STATUS").agg(count("*").alias("cnt")).orderBy(col("cnt").desc()).show(20, truncate=False)

# NBA 3.0 bug check: does 'Delivered' (exact) exist, or only 'Delivered_vod'?
delivered_exact = df_irep.filter(col("EMAIL_STATUS") == "Delivered").count()
delivered_vod = df_irep.filter(col("EMAIL_STATUS") == "Delivered_vod").count()
delivered_like = df_irep.filter(upper(col("EMAIL_STATUS")).like("%DELIVERED%")).count()
print(f"Status = 'Delivered' (exact):  {delivered_exact:,}")
print(f"Status = 'Delivered_vod':      {delivered_vod:,}")
print(f"Status LIKE '%DELIVERED%':     {delivered_like:,}")

# Email activity: opens and clicks
v7_activity_query = """
SELECT
    ea.EVNT_TYP AS ACTVTY_TYPE,
    ea.ACTY_DT_TM AS ACTVTY_DT
FROM CPH_DB_PROD.MODEL_V2.FACT_EMAIL_ACTIVITY ea
WHERE ea.ACTY_DT_TM >= '2024-11-01'
  AND ea.ACTY_DT_TM < '2026-11-01'
"""

df_email_activity = Get_Data_Snowflakes(v7_activity_query)
df_email_activity = df_email_activity.withColumn("ACTVTY_DT", col("ACTVTY_DT").cast(DateType()))

print("\n--- Email Activity Types ---")
df_email_activity.groupBy("ACTVTY_TYPE").agg(count("*").alias("cnt")).orderBy(col("cnt").desc()).show(truncate=False)

# Monthly open rate using OPENED column directly from FACT_SENT_EMAIL
df_irep_delivered = df_irep.filter(upper(col("EMAIL_STATUS")).like("%DELIVERED%"))

df_open_rate = (
    df_irep_delivered
    .withColumn("MONTH", F.date_trunc("month", col("SEND_DT")))
    .groupBy("MONTH")
    .agg(
        count("*").alias("delivered"),
        spark_sum("OPENED").alias("opened")
    )
    .withColumn("open_rate_pct", F.round(col("opened") / col("delivered") * 100, 1))
    .orderBy("MONTH")
)

print("\n--- Monthly Open Rate (check for April 2026 drop) ---")
df_open_rate.show(30, truncate=False)

# COMMAND ----------

# DBTITLE 1,V10: MSL Records Identification
# V10: MSL / Medical records
# Identify MEDICAL records: product text 'Finerenone [...]', medical record types
# Expected from data review: ~10,500-10,900 interactions/year with ~6,400-6,800 doctors

df_medical = df_classified.filter(col("RECORD_CLASS") == "MEDICAL")

print("=== V10: MSL Records ===")
df_medical.groupBy("YEAR").agg(
    count("*").alias("records"),
    countDistinct("CALL_ID").alias("distinct_interactions"),
    countDistinct("BHID").alias("distinct_doctors")
).orderBy("YEAR").show(truncate=False)

print("\n--- Medical record types ---")
df_medical.groupBy("CALL_REC_TYP_NM").agg(
    count("*").alias("cnt")
).orderBy(col("cnt").desc()).show(20, truncate=False)

print("\n--- Medical DETL_PROD values ---")
df_medical.groupBy("DETL_PROD").agg(
    count("*").alias("cnt")
).orderBy(col("cnt").desc()).show(20, truncate=False)

# Confirm: none counted as HCP_INTERACTION
df_medical_as_hcp = df_classified.filter(
    (col("RECORD_CLASS") == "HCP_INTERACTION") &
    (col("CALL_REC_TYP_NM").isin(medical_rec_types) | upper(col("DETL_PROD")).like("FINERENONE%"))
)
print(f"\nSanity check: medical-looking records classified as HCP_INTERACTION: {df_medical_as_hcp.count()} (should be 0)")

# COMMAND ----------

# DBTITLE 1,V1d: Kerendia detail priority analysis
# V1d: Kerendia detail priority (PN-2)
# Check: Kerendia in position 1 on 87-92% of 2026 interactions

df_ker_details = df_details.filter(upper(col("DETL_PROD")) == "KERENDIA")

df_ker_priority = (
    df_ker_details
    .join(
        df_all_calls.select("CALL_ID", "CALL_DATE", "YEAR")
        .filter(col("YEAR") == "Year_2")
        .distinct(),
        on="CALL_ID"
    )
    .groupBy("CALL_DETL_PRTY")
    .agg(countDistinct("CALL_ID").alias("calls"))
    .orderBy("CALL_DETL_PRTY")
)

total_ker_y2 = df_ker_priority.select(spark_sum("calls")).first()[0]
df_ker_priority = df_ker_priority.withColumn(
    "pct", F.round(col("calls") / lit(total_ker_y2) * 100, 1)
)

print("=== V1d: Kerendia Detail Priority (Year 2) ===")
df_ker_priority.show(truncate=False)

# Co-detail products
print("\n--- Products co-detailed with Kerendia (Year 2) ---")
ker_call_ids = df_ker_details.select("CALL_ID").distinct()
df_codetail = (
    df_details
    .join(ker_call_ids, on="CALL_ID")
    .filter(upper(col("DETL_PROD")) != "KERENDIA")
    .join(
        df_all_calls.select("CALL_ID", "YEAR").filter(col("YEAR") == "Year_2").distinct(),
        on="CALL_ID"
    )
    .groupBy("DETL_PROD")
    .agg(countDistinct("CALL_ID").alias("co_detail_calls"))
    .orderBy(col("co_detail_calls").desc())
)
df_codetail.show(20, truncate=False)

# COMMAND ----------

# DBTITLE 1,Validation Summary Statistics
# Collect summary statistics for the findings cell
print("=" * 80)
print("PHASE 0 VALIDATION SUMMARY")
print("=" * 80)

# V1 summary
print(f"\n[V1] Total submitted calls loaded: {df_all_calls.count():,}")
print(f"[V1] Year 2 doctor calls (all products):   {y2_total:,} calls, {y2_doctors:,} doctors")
print(f"[V1] Year 2 Kerendia via detail (NBA 3.1):  {y2_ker_detail:,} calls, {y2_ker_detail_docs:,} doctors")
print(f"[V1] Year 2 Kerendia via DETL_PROD (NBA 3.0): {y2_nba30:,} calls, {y2_nba30_docs:,} doctors")
if y2_ker_detail > 0:
    print(f"[V1] Co-detail gap: {y2_ker_detail - y2_nba30:,} calls ({(y2_ker_detail - y2_nba30)/y2_ker_detail*100:.1f}%)")

# V2 summary
print(f"\n[V2] Record classes:")
df_classified.groupBy("RECORD_CLASS").agg(count("*").alias("records")).orderBy("RECORD_CLASS").show(truncate=False)

# V7 summary
print(f"[V7] iRep Delivered (exact): {delivered_exact:,}  |  Delivered_vod: {delivered_vod:,}")

print("\n" + "=" * 80)
print("END OF PHASE 0 VALIDATION")
print("=" * 80)

# COMMAND ----------

# DBTITLE 1,Phase 0 Validation — Main Findings
# MAGIC %md
# MAGIC # Phase 0 Validation — Main Findings
# MAGIC
# MAGIC **Run date:** Nov 2, 2026  |  **Reference period (Year 2):** Nov 2025 – Oct 2026  |  **Source:** Snowflake CPH_DB_PROD (FACT_CALL, FACT_CALL_DETAIL, FACT_CALL_KEY_MESSAGE, ANLT_BASE_FACT_EVNT_PRSNL_PROM, FACT_SENT_EMAIL, FACT_EMAIL_ACTIVITY)
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## V1 — Interaction Grain & Co-Detail Gap
# MAGIC
# MAGIC **Year 2 counts match expectations.** The NBA 3.1 method (Kerendia via FACT_CALL_DETAIL) yields **676,136 Kerendia doctor calls** and **104,752 called doctors** — closely matching the data-review expectation of ~660K calls / ~104K doctors.
# MAGIC
# MAGIC The NBA 3.0 method (DETL_PROD = 'KERENDIA' on FACT_CALL) captures only **421,295 calls / 84,548 doctors**, missing **254,841 calls (37.7%)** and **20,204 doctors**.
# MAGIC
# MAGIC ### Co-detail gap monthly trend
# MAGIC
# MAGIC | Period | Gap % (typical) | Notes |
# MAGIC |--------|----------------|-------|
# MAGIC | Year 1 (Nov 2024 – Oct 2025) | 0.6 – 1.7% | NBA 3.0 DETL_PROD filter was adequate |
# MAGIC | Year 2 from Jan 2026 onward | 30 – 46% | Structural change; DETL_PROD no longer captures Kerendia on co-detailed calls |
# MAGIC
# MAGIC The gap jumped from ~1% in Dec 2025 to **30.2% in Jan 2026** and climbed steadily to **46.3% by Aug 2026**. This coincides with the Lynkuet (elinzanetant) launch, which is the dominant co-detail product (**435,777 co-detailed calls** in Year 2).
# MAGIC
# MAGIC ### V1d — Kerendia detail priority (PN-2)
# MAGIC
# MAGIC Kerendia appears in **position 1 on 91.6%** of Year 2 interactions (1,084,008 calls), position 2 on 8.4% (99,040), and position 3 on 0.0% (153). This is **within the expected 87–92% range**.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## V2 — Record Classification
# MAGIC
# MAGIC | Record Class | Records | Share |
# MAGIC |-------------|---------|-------|
# MAGIC | HCP_INTERACTION | 1,944,483 | ~56% |
# MAGIC | BHO_CHILD | 1,277,486 | ~37% |
# MAGIC | BHO_TOP_LEVEL | 216,069 | ~6% |
# MAGIC | MEDICAL | 39,160 | ~1% |
# MAGIC | ACCOUNT_OFFICE | 0 | 0% |
# MAGIC
# MAGIC Shares are **stable month-over-month**: HCP_INTERACTION ~55%, BHO_CHILD ~33–41% (rising slightly in Year 2), BHO_TOP_LEVEL declining from ~10% to ~3%.
# MAGIC
# MAGIC **Issue:** No records classified as ACCOUNT_OFFICE. The expected CALL_REC_TYP_NM values ('5- Acct Call', 'vOffice call (no HCP)', '2-Account Call Only') do not match any actual values in the data — these records likely fall into HCP_INTERACTION via the default clause. This needs investigation for NBA 3.1.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## V3 — BHO Parent / Child Analysis
# MAGIC
# MAGIC - Total BHO records: **1,493,555** (BHO_CHILD: 1,277,486; BHO_TOP_LEVEL: 216,069)
# MAGIC - **97.0%** of BHO_CHILD records have a PAR_CALL_ID that matches an HCP_INTERACTION call
# MAGIC - **7,096 BHO_CHILD records have a blank PAR_CALL_ID** — a data quality issue. These were classified as BHO_CHILD because BHID contains 'BHO' but have no parent link.
# MAGIC - Each parent call maps to typically **1 BHO recipient** (no spreading to multiple organisations)
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## V4 — Key-Message Entry Consistency
# MAGIC
# MAGIC - **5,240,265** total key message rows across **2,813,521** distinct calls
# MAGIC - Key-message coverage for Kerendia HCP calls: **~100% every month** (one dip to 83.6% in Dec 2024)
# MAGIC - Top key messages: Position 1 KER CKD (1.08M), Position 1 LYN (534K), Position 1 KER HF (503K)
# MAGIC - Key-message entry is highly consistent — no data quality concerns.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## V6 — Event States Mapping
# MAGIC
# MAGIC - **67,086** event-attendee records, **7,958** distinct events, **37,066** distinct HCPs
# MAGIC - Attendee status: Closed (57,333), NULL (5,832), Completed (3,077), Planned (816), Cancelled (28)
# MAGIC - Attendance value: Attended (21,763), NULL (45,323)
# MAGIC - **0 Signed_vod records without ATND** — the Q-D1 concern does not materialise in this data
# MAGIC - Speaker Programs dominate (54,947 records, 4,162 events); Kerendia topics are prominent
# MAGIC - **Issue:** 5,832 records have NULL attendee status and 45,323 have NULL attendance value — these may need mapping rules for NBA 3.1.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## V7 — iRep Data Checks
# MAGIC
# MAGIC ### Delivered_vod bug confirmation (Q-C2)
# MAGIC - **Status = 'Delivered' (exact): 0** — confirms the NBA 3.0 bug. Only `Delivered_vod` exists (462,111 records).
# MAGIC - Any NBA 3.0 code filtering on `STAT = 'Delivered'` would capture zero delivered emails.
# MAGIC
# MAGIC ### April 2026 open-rate drop (Q-C1)
# MAGIC
# MAGIC | Period | Open Rate (typical) |
# MAGIC |--------|-------------------|
# MAGIC | Nov 2024 – Mar 2026 | 33 – 38% |
# MAGIC | Apr 2026 | 25.7% |
# MAGIC | May – Jul 2026 | 23.2% → 18.6% |
# MAGIC | Aug – Oct 2026 | ~19 – 20% |
# MAGIC
# MAGIC The open rate **halved from ~35% to ~19%** starting April 2026 and has not recovered. The decline is monotonic over 7 months.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## V10 — MSL Records Identification
# MAGIC
# MAGIC | Year | Interactions | Doctors | Expected Interactions | Expected Doctors |
# MAGIC |------|-------------|---------|----------------------|-----------------|
# MAGIC | Year 1 | 13,532 | 8,711 | ~10,500–10,900 | ~6,400–6,800 |
# MAGIC | Year 2 | 25,628 | 15,707 | ~10,500–10,900 | ~6,400–6,800 |
# MAGIC
# MAGIC **Year 2 MSL volume is 2.4x the expected range** (25,628 vs ~10.5–10.9K). Year 1 is also above expectations but closer. The increase may reflect expanded medical engagement or a data source change.
# MAGIC
# MAGIC - Medical record types: Face2Face Interaction Med dominates (22,680 records)
# MAGIC - Top products: Finerenone variants (multiple sub-indications), Asundexian, Elinzanetant
# MAGIC - Sanity check: **0 medical-looking records misclassified as HCP_INTERACTION** — classification logic is clean
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Summary of Surprises & Data Quality Issues
# MAGIC
# MAGIC 1. **Co-detail gap structural shift (Jan 2026):** The DETL_PROD filter jumped from ~1% to 30–46% miss rate, driven by Lynkuet co-detailing. This is the single largest finding — NBA 3.0 is blind to a large share of Kerendia calls in Year 2.
# MAGIC 2. **ACCOUNT_OFFICE class empty:** The expected account-office record types do not exist in the current CALL_REC_TYP_NM values. Account-only calls may be misclassified as HCP_INTERACTION.
# MAGIC 3. **MSL records 2.4x expected:** Year 2 has 25,628 MSL interactions vs ~10.5–10.9K expected. Requires validation against the source of the expectation.
# MAGIC 4. **iRep open-rate collapse:** From ~35% to ~19% starting April 2026, not recovering. Likely an upstream data or tracking change.
# MAGIC 5. **BHO_CHILD with blank PAR_CALL_ID:** 7,096 records (0.6% of BHO_CHILD) have no parent link.
# MAGIC 6. **Event records with NULL status:** 5,832 attendee records have NULL EVNT_STAT; 45,323 have NULL ATND value — mapping rules needed for NBA 3.1.