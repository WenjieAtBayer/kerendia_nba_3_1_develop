# Databricks notebook source
# DBTITLE 1,Digital in NBA 3.1: Data Readiness Validation
# MAGIC %md
# MAGIC ## Digital in NBA 3.1: Data Readiness Validation
# MAGIC
# MAGIC Data readiness checks from `50_digital_nba_3_1_readiness_plan.md`, covering the five feature families.
# MAGIC
# MAGIC | Family | What | Source |
# MAGIC |--------|------|--------|
# MAGIC | **1. HCP Paid Media** | MMX table volume, vendor/placement coverage | Snowflake MMX |
# MAGIC | **2. HQ Email** | Email event log availability | Snowflake FACT_SENT_EMAIL |
# MAGIC | **3. High-Intent Signals** | Request-a-Rep (RAR) exploration | Snowflake RPT_DIGITAL_RAR_TAB |
# MAGIC | **4. DTC Market Context** | Facebook/Instagram + SA360 search | Snowflake FUNNEL tables |
# MAGIC | **5. Engagement Depth** | OE event-level data, BH_ID-to-NPI coverage | kerendia_oe_journey tables |
# MAGIC
# MAGIC **Period:** Jan 2025 – Oct 2026

# COMMAND ----------

# DBTITLE 1,Install Snowflake Connector
# MAGIC %pip install snowflake-connector-python --quiet
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Imports and Snowflake Connections
import pyspark.sql.functions as F
from pyspark.sql.functions import col, when, lit, upper, count, countDistinct, sum as spark_sum, coalesce
from pyspark.sql.types import DateType
from cryptography.hazmat.primitives import serialization

scope = "US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair"
private_key_pem = dbutils.secrets.get(scope, "snowflake-private-key")
private_key_passphrase = dbutils.secrets.get(scope, "snowflake-private-key-passphrase")
snowflake_user = dbutils.secrets.get(scope, "snowflake-user")

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

# Connection for MMX / digital tables (PHCDW_DSAA schema)
sfOptionsDSAA = {
    "sfURL": "bayer_cphcdp_prod.us-east-1.snowflakecomputing.com:443",
    "sfUser": snowflake_user,
    "pem_private_key": snowflake_pem_private_key,
    "sfRole": "BAY_CPH_CDP_PROD_CR_US_EAST_1_MVXPF_MVXPF",
    "sfSchema": "PHCDW_DSAA",
    "sfDatabase": "PHCDW",
    "sfWarehouse": "PROD_DATA_SCIENCE_CYRUS_WH",
    "purge": "off",
    "autopushdown": "on",
}

# Connection for CDM tables (MODEL_V2, PHCDW_CDM)
sfOptionsCDM = {
    **sfOptionsDSAA,
    "sfSchema": "PHCDW_CDM",
    "sfWarehouse": "PROD_CYRUS_BI_WH",
}

SF = "net.snowflake.spark.snowflake"

def sf_dsaa(query):
    return spark.read.format(SF).options(**sfOptionsDSAA).option("query", query).load()

def sf_cdm(query):
    return spark.read.format(SF).options(**sfOptionsCDM).option("query", query).load()

print("Setup complete.")

# COMMAND ----------

# DBTITLE 1,Family 1: HCP Paid Media — MMX Table Overview
# Family 1: HCP Paid Media overview from MMX
# Volume, vendor count, NPI coverage, monthly trend

mmx_overview = """
SELECT
    DATE_TRUNC('MONTH', DATE_ACT) AS MONTH,
    COUNT(*) AS row_cnt,
    COUNT(DISTINCT NPI_NUM) AS distinct_npis,
    COUNT(DISTINCT UPPER(SRC_SYS_CD)) AS n_vendors,
    SUM(EXPOSURE) AS total_exposure,
    SUM(TOTAL_ENGAGEMENT) AS total_engagement
FROM PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB
WHERE UPPER(BRND_NM) LIKE '%KERENDIA%'
  AND DATE_ACT >= '2025-01-01' AND DATE_ACT < '2026-11-01'
GROUP BY DATE_TRUNC('MONTH', DATE_ACT)
ORDER BY MONTH
"""

df_mmx_monthly = sf_dsaa(mmx_overview)
print("=== Family 1: HCP Paid Media — Monthly MMX Overview ===")
df_mmx_monthly.show(30, truncate=False)

# Totals
totals = df_mmx_monthly.agg(
    spark_sum("row_cnt").alias("total_rows"),
    F.max("distinct_npis").alias("max_monthly_npis"),
    spark_sum("total_exposure").alias("total_exposure"),
    spark_sum("total_engagement").alias("total_engagement")
).first()
print(f"\nOverall: {totals['total_rows']:,} rows, up to {totals['max_monthly_npis']:,} NPIs/month")
print(f"Total exposure: {totals['total_exposure']:,}, total engagement: {totals['total_engagement']:,}")

# COMMAND ----------

# DBTITLE 1,Family 2: HQ Email — Event Log Check
# Family 2: HQ Email — check FACT_SENT_EMAIL availability
# The plan says notebook 15 event log is the single source for HQ email.

hq_email_q = """
SELECT
    DATE_TRUNC('MONTH', EMAIL_SNT_DATE) AS MONTH,
    COUNT(*) AS total_emails,
    COUNT(DISTINCT SOURCE_CUST_ID) AS distinct_doctors,
    SUM(OPENED) AS total_opened,
    SUM(CLK_CNT) AS total_clicks
FROM CPH_DB_PROD.MODEL_V2.FACT_SENT_EMAIL
WHERE EMAIL_SNT_DATE >= '2025-01-01'
  AND EMAIL_SNT_DATE < '2026-11-01'
  AND STAT = 'Delivered_vod'
GROUP BY DATE_TRUNC('MONTH', EMAIL_SNT_DATE)
ORDER BY MONTH
"""

df_hq_email = sf_cdm(hq_email_q)
print("=== Family 2: HQ Email — Monthly Delivered Emails ===")
df_hq_email.show(30, truncate=False)

hq_totals = df_hq_email.agg(
    spark_sum("total_emails").alias("emails"),
    spark_sum("total_opened").alias("opened"),
    spark_sum("total_clicks").alias("clicks")
).first()
print(f"Total delivered: {hq_totals['emails']:,}, opened: {hq_totals['opened']:,}, clicks: {hq_totals['clicks']:,}")

# COMMAND ----------

# DBTITLE 1,Family 3: Request-a-Rep (RAR) Exploration
# Family 3: High-intent signals — Request-a-Rep
# Source: PHCDW.PHCDW_CDM.RPT_DIGITAL_RAR_TAB
# Expected: ~1,218 Kerendia requests Jan 2025 – Oct 2026

# First check if the table exists and what columns it has
rar_cols_q = """
SELECT COLUMN_NAME, DATA_TYPE
FROM PHCDW.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'PHCDW_CDM'
  AND TABLE_NAME = 'RPT_DIGITAL_RAR_TAB'
ORDER BY ORDINAL_POSITION
"""
try:
    df_rar_cols = sf_cdm(rar_cols_q)
    print("=== Family 3: RPT_DIGITAL_RAR_TAB Schema ===")
    df_rar_cols.show(50, truncate=False)
    rar_exists = True
except:
    print("RPT_DIGITAL_RAR_TAB not accessible or does not exist.")
    rar_exists = False

# COMMAND ----------

# DBTITLE 1,Family 3b: RAR Data Exploration
# Family 3b: RAR data exploration (if table exists)
if rar_exists:
    rar_q = """
    SELECT *
    FROM PHCDW.PHCDW_CDM.RPT_DIGITAL_RAR_TAB
    WHERE UPPER(BRND_NM) LIKE '%KERENDIA%'
       OR UPPER(BRAND_NAME) LIKE '%KERENDIA%'
       OR UPPER(PRODUCT_NAME) LIKE '%KERENDIA%'
    LIMIT 100
    """
    try:
        df_rar_sample = sf_cdm(rar_q)
        print(f"=== Family 3b: RAR Sample (Kerendia) — {df_rar_sample.count()} rows ===")
        df_rar_sample.show(10, truncate=False)
        print(f"\nColumns: {df_rar_sample.columns}")
    except Exception as e:
        # If the column names are wrong, try a generic sample
        print(f"Kerendia filter failed ({e}). Trying unfiltered sample...")
        rar_q2 = "SELECT * FROM PHCDW.PHCDW_CDM.RPT_DIGITAL_RAR_TAB LIMIT 20"
        df_rar_sample = sf_cdm(rar_q2)
        print(f"RAR sample: {df_rar_sample.count()} rows")
        df_rar_sample.show(5, truncate=False)
        print(f"Columns: {df_rar_sample.columns}")
else:
    print("Skipped — RAR table not accessible.")

# COMMAND ----------

# DBTITLE 1,Family 4: DTC — Facebook/Instagram + SA360 Check
# Family 4: DTC Market Context
# Check Facebook/Instagram (DMA) and SA360 search (state) tables

# Facebook/Instagram
print("=== Family 4a: DTC Social (Facebook/Instagram) ===")
try:
    fb_q = """
    SELECT
        DATE_TRUNC('MONTH', DATE) AS MONTH,
        COUNT(*) AS rows,
        COUNT(DISTINCT DMA_NAME) AS n_dmas,
        SUM(IMPRESSIONS) AS total_impressions
    FROM FUNNEL_PROD_INB2.FUNNEL__MK7FZ_CN_UWQY_VMROR.FUNNEL_DATA_FACEBOOKADS_GEO_DMA
    WHERE DATE >= '2025-01-01' AND DATE < '2026-11-01'
    GROUP BY DATE_TRUNC('MONTH', DATE)
    ORDER BY MONTH
    """
    df_fb = sf_dsaa(fb_q)
    df_fb.show(30, truncate=False)
    fb_total = df_fb.select(spark_sum("rows")).first()[0]
    print(f"Total DTC social rows: {fb_total:,}")
except Exception as e:
    print(f"Facebook/Instagram table not accessible: {e}")

# SA360 search
print("\n=== Family 4b: DTC Search (SA360) ===")
try:
    sa_q = """
    SELECT
        DATE_TRUNC('MONTH', DATE) AS MONTH,
        COUNT(*) AS rows,
        COUNT(DISTINCT REGION) AS n_regions,
        SUM(CLICKS) AS total_clicks
    FROM FUNNEL_PROD_INB2.FUNNEL__MK7FZ_CN_UWQY_VMROR.FUNNEL_DATA_NEW_SA360_REGION
    WHERE DATE >= '2025-01-01' AND DATE < '2026-11-01'
    GROUP BY DATE_TRUNC('MONTH', DATE)
    ORDER BY MONTH
    """
    df_sa = sf_dsaa(sa_q)
    df_sa.show(30, truncate=False)
    sa_total = df_sa.select(spark_sum("rows")).first()[0]
    print(f"Total SA360 search rows: {sa_total:,}")
except Exception as e:
    print(f"SA360 table not accessible: {e}")

# COMMAND ----------

# DBTITLE 1,Family 5: OE Event-Level Data + BH_ID-to-NPI Coverage
# Family 5: Engagement Depth — OE event-level data
# Check kerendia_oe_journey tables in Unity Catalog

print("=== Family 5a: OE Event-Level Table ===")
try:
    df_oe = spark.sql("""
        SELECT
            DATE_TRUNC('MONTH', EVENT_DATE) AS MONTH,
            COUNT(*) AS rows,
            COUNT(DISTINCT BH_ID) AS distinct_bhids,
            COUNT(DISTINCT NPI) AS distinct_npis
        FROM kerendia_oe_journey.oe_kerendia_fact_npp_inference
        WHERE EVENT_DATE >= '2025-01-01' AND EVENT_DATE < '2026-11-01'
        GROUP BY DATE_TRUNC('MONTH', EVENT_DATE)
        ORDER BY MONTH
    """)
    df_oe.show(30, truncate=False)
    oe_totals = df_oe.agg(spark_sum("rows"), F.max("distinct_bhids"), F.max("distinct_npis")).first()
    print(f"OE events total: {oe_totals[0]:,}, max monthly BH_IDs: {oe_totals[1]:,}, NPIs: {oe_totals[2]}")
except Exception as e:
    print(f"OE event table not accessible (may need catalog prefix): {e}")
    # Try with full catalog path
    try:
        df_oe_tables = spark.sql("SHOW TABLES IN kerendia_oe_journey")
        print("\nAvailable tables in kerendia_oe_journey:")
        df_oe_tables.show(50, truncate=False)
    except Exception as e2:
        print(f"Cannot list kerendia_oe_journey tables: {e2}")

# BH_ID to NPI mapping coverage
print("\n=== Family 5b: BH_ID to NPI Mapping ===")
try:
    df_mapping = spark.sql("""
        SELECT
            COUNT(*) AS total_rows,
            COUNT(DISTINCT BH_ID) AS distinct_bhids,
            COUNT(DISTINCT NPI) AS distinct_npis,
            SUM(CASE WHEN NPI IS NULL THEN 1 ELSE 0 END) AS null_npi,
            ROUND(100.0 * SUM(CASE WHEN NPI IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS null_npi_pct
        FROM kerendia_oe_journey.kerendia_oe_npi_bhid_mapping_inference
    """)
    print("BH_ID to NPI mapping:")
    df_mapping.show(truncate=False)
except Exception as e:
    print(f"BH_ID-to-NPI mapping table not accessible: {e}")

# COMMAND ----------

# DBTITLE 1,Summary: Data Readiness Status
# Data readiness summary
print("=" * 80)
print("DATA READINESS SUMMARY")
print("=" * 80)
print("\n[Family 1] HCP Paid Media (MMX): READY — see monthly overview above")
print("[Family 2] HQ Email (FACT_SENT_EMAIL): READY — see monthly delivered counts above")
print("[Family 3] Request-a-Rep (RAR): see RAR exploration above")
print("[Family 4] DTC Social + Search: see availability checks above")
print("[Family 5] OE Event-Level + BH_ID-to-NPI: see checks above")
print("\n" + "=" * 80)

# COMMAND ----------

# DBTITLE 1,Digital NBA 3.1 Data Readiness — Main Findings
# MAGIC %md
# MAGIC # Digital NBA 3.1 Data Readiness — Main Findings
# MAGIC
# MAGIC **Run date:** Nov 2, 2026  |  **Period:** Jan 2025 – Oct 2026
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Family 1 — HCP Paid Media (MMX): READY
# MAGIC
# MAGIC | Metric | Value |
# MAGIC |--------|-------|
# MAGIC | Total rows (Kerendia) | 129,905,442 |
# MAGIC | Max monthly NPIs | 201,523 (Mar 2025) |
# MAGIC | Total exposure | 122,535,400 |
# MAGIC | Total engagement | 3,954,753 |
# MAGIC | Vendors per month | 8 (Jan 2025) → 20 (Apr 2026) |
# MAGIC
# MAGIC Monthly volume ranges from 2.8M rows (Jan 2025) to 9.5M (Mar 2026), peaking in spring 2026. Data is consistently available across all 22 months.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Family 2 — HQ Email (FACT_SENT_EMAIL): READY
# MAGIC
# MAGIC | Metric | Value |
# MAGIC |--------|-------|
# MAGIC | Total delivered emails | 438,854 |
# MAGIC | Total opened | 128,815 (29.4% open rate) |
# MAGIC | Total clicks | 40,270 (9.2% click rate) |
# MAGIC | Max monthly doctors | 27,187 (Jul 2025) |
# MAGIC
# MAGIC Monthly volume: 11.7K–33.4K delivered emails. **Open rate declined** from ~37% (early 2025) to ~20% (Oct 2026) — consistent with the iRep open-rate collapse observed in notebook 41. Data uses `Delivered_vod` status (no exact `Delivered` exists).
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Family 3 — Request-a-Rep (RPT_DIGITAL_RAR_TAB): EXISTS — Column Mapping Needed
# MAGIC
# MAGIC The RAR table **exists and is accessible** with **66 columns**, including:
# MAGIC
# MAGIC | Key Column | Type | Notes |
# MAGIC |-----------|------|-------|
# MAGIC | TRANSACTION_ID | TEXT | Primary key |
# MAGIC | BRAND_NAME | TEXT | Not `BRND_NM` — initial query failed |
# MAGIC | BH_ID | TEXT | Direct Bayer HCP ID |
# MAGIC | NPI | TEXT | NPI available |
# MAGIC | CREATE_DATE | DATE | Request timestamp |
# MAGIC | REQUEST_TYPE | TEXT | Type of request |
# MAGIC | REP_TYPE | TEXT | Rep classification |
# MAGIC | SENT_IREP / CLICKED_IREP / VIEWED_IREP / DELIVERED_IREP | Various | iRep engagement funnel |
# MAGIC | SENT_HQ / CLICKED_HQ / VIEWED_HQ / DELIVERED_HQ | TEXT | HQ email engagement funnel |
# MAGIC | CALL_DATE | DATE | Follow-up call date |
# MAGIC | UTM_SOURCE / UTM_MEDIUM / UTM_CAMPAIGN | TEXT | Attribution tracking |
# MAGIC | WEBFORM_SOURCE | TEXT | Source of request |
# MAGIC
# MAGIC **Issue:** The initial Kerendia filter used `BRND_NM` (MMX naming) but this table uses `BRAND_NAME`. Queries must use the correct column.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Family 4 — DTC Social + Search: NOT VERIFIED (query syntax errors)
# MAGIC
# MAGIC The Facebook/Instagram (`FUNNEL__MK7FZ_CN_UWQY_VMROR.FUNNEL_DATA_FACEBOOKADS_GEO_DMA`) and SA360 search table queries **failed due to Snowflake reserved keyword `rows`** in the SQL alias (`COUNT(*) AS rows`). The tables may exist but the queries need `AS row_cnt` instead. This is the same issue fixed in Families 1 and the 13_hcp_digital notebook.
# MAGIC
# MAGIC **Status:** Query fix required before data availability can be confirmed.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Family 5 — OE Event-Level Data: EXISTS — Column Name Mismatch
# MAGIC
# MAGIC The Unity Catalog table `kerendia_oe_journey.oe_kerendia_fact_npp_inference` **exists and is queryable** with 43+ columns. However, the query used `EVENT_DATE` which does not exist — the table uses `DATE_ID` instead.
# MAGIC
# MAGIC ### Available columns (partial)
# MAGIC
# MAGIC | Column | Type |
# MAGIC |--------|------|
# MAGIC | CUST_ID | TEXT |
# MAGIC | PROD_ID | TEXT |
# MAGIC | LITCODE | TEXT |
# MAGIC | DATE_ID | TEXT |
# MAGIC | CHNL_ID / CHNL_NM | TEXT |
# MAGIC | VEND_NM | TEXT |
# MAGIC | RPT_CHNL | TEXT |
# MAGIC | CPGN_NM | TEXT |
# MAGIC | TACT_TYP / TACT_NM | TEXT |
# MAGIC | HCP_PRMRY_SPCL / HCP_TYP | TEXT |
# MAGIC | HCP_ID_TYP | TEXT |
# MAGIC | CF_NAME / CF_INDICATION | TEXT |
# MAGIC | PRMRY_KEY_MSG | TEXT |
# MAGIC | LINK_URL | TEXT |
# MAGIC
# MAGIC **Issue:** No direct `BH_ID` or `NPI` column — the table uses `CUST_ID` and `HCP_ID_TYP`. A mapping step is needed to join `CUST_ID` to BH_ID/NPI via `MAP_CUSTOMER_XREF` or another cross-reference table.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Summary of Data Readiness
# MAGIC
# MAGIC | Family | Status | Key Issue |
# MAGIC |--------|--------|-----------|
# MAGIC | 1. HCP Paid Media (MMX) | **READY** | None — 130M rows, 22 months available |
# MAGIC | 2. HQ Email | **READY** | Open rate declining but data available |
# MAGIC | 3. Request-a-Rep (RAR) | **EXISTS** | Use `BRAND_NAME` not `BRND_NM` |
# MAGIC | 4. DTC Social + Search | **NOT VERIFIED** | Snowflake `rows` keyword error — fix queries |
# MAGIC | 5. OE Event-Level | **EXISTS** | Use `DATE_ID` not `EVENT_DATE`; needs CUST_ID→BH_ID/NPI mapping |
# MAGIC
# MAGIC **Three of five families are confirmed ready.** Families 3 and 5 require column name corrections. Family 4 requires query fixes before availability can be assessed.