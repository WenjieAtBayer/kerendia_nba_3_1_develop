# Databricks notebook source
# DBTITLE 1,Phase 0: HCP Digital Validation — NBA 3.1
# MAGIC %md
# MAGIC ## Phase 0: HCP Digital Validation — NBA 3.1 Readiness
# MAGIC
# MAGIC Validation checks from `13_hcp_digital_nba_3_1_readiness_plan.md` (Phase 0 foundations).
# MAGIC
# MAGIC | Task | Description |
# MAGIC |------|-------------|
# MAGIC | **F1** | Brand filter — `= 'KERENDIA'` vs `LIKE '%KERENDIA%'` |
# MAGIC | **F2/F3** | Placement dictionary — vendor/channel/tactic distribution, case sensitivity |
# MAGIC | **F4** | Unmapped report — share of rows in OTHER |
# MAGIC | **F7** | HQ email duplication check |
# MAGIC | **F8** | iRep presence in digital block |
# MAGIC | **F9** | Schema stability — distinct column sets across months |
# MAGIC
# MAGIC **Source:** `PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB` (Snowflake)
# MAGIC **Period:** Jan 2025 – Oct 2026

# COMMAND ----------

# DBTITLE 1,Install Snowflake Connector
# MAGIC %pip install snowflake-connector-python --quiet
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Imports and Snowflake Connection (sfOptionscdpread)
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

sfOptions = {
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
SF = "net.snowflake.spark.snowflake"

def sf_query(query):
    return spark.read.format(SF).options(**sfOptions).option("query", query).load()

print("Setup complete.")

# COMMAND ----------

# DBTITLE 1,F1: Brand Filter — KERENDIA exact vs LIKE %KERENDIA%
# F1: Brand filter validation
# NBA 3.0 uses UPPER(BRND_NM) = 'KERENDIA' — drops indication-tagged rows
# Plan: use UPPER(BRND_NM) LIKE '%KERENDIA%'

f1_query = """
SELECT
    UPPER(BRND_NM) AS BRND_NM,
    COUNT(*) AS row_cnt,
    COUNT(DISTINCT NPI_NUM) AS distinct_npis
FROM PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB
WHERE UPPER(BRND_NM) LIKE '%KERENDIA%'
  AND DATE_ACT >= '2025-01-01'
  AND DATE_ACT < '2026-11-01'
GROUP BY UPPER(BRND_NM)
ORDER BY row_cnt DESC
"""

df_f1 = sf_query(f1_query)
df_f1.cache()

print("=== F1: Brand Filter — Distinct BRND_NM values containing KERENDIA ===")
df_f1.show(50, truncate=False)

# Compare exact vs LIKE
f1_exact = """
SELECT
    'EXACT' AS METHOD,
    COUNT(*) AS row_cnt,
    COUNT(DISTINCT NPI_NUM) AS npis
FROM PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB
WHERE UPPER(BRND_NM) = 'KERENDIA'
  AND DATE_ACT >= '2025-01-01' AND DATE_ACT < '2026-11-01'
UNION ALL
SELECT
    'LIKE' AS METHOD,
    COUNT(*) AS row_cnt,
    COUNT(DISTINCT NPI_NUM) AS npis
FROM PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB
WHERE UPPER(BRND_NM) LIKE '%KERENDIA%'
  AND DATE_ACT >= '2025-01-01' AND DATE_ACT < '2026-11-01'
"""
df_f1_compare = sf_query(f1_exact)
print("\n--- Exact vs LIKE comparison ---")
df_f1_compare.show(truncate=False)

# Per-vendor gap
f1_vendor_gap = """
SELECT
    UPPER(SRC_SYS_CD) AS VENDOR,
    SUM(CASE WHEN UPPER(BRND_NM) = 'KERENDIA' THEN 1 ELSE 0 END) AS exact_rows,
    COUNT(*) AS like_rows,
    ROUND(100.0 * (COUNT(*) - SUM(CASE WHEN UPPER(BRND_NM) = 'KERENDIA' THEN 1 ELSE 0 END)) / NULLIF(COUNT(*), 0), 1) AS gap_pct
FROM PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB
WHERE UPPER(BRND_NM) LIKE '%KERENDIA%'
  AND DATE_ACT >= '2025-01-01' AND DATE_ACT < '2026-11-01'
GROUP BY UPPER(SRC_SYS_CD)
ORDER BY gap_pct DESC
"""
df_f1_vendor = sf_query(f1_vendor_gap)
print("\n--- Per-vendor brand filter gap (rows lost by NBA 3.0 exact filter) ---")
df_f1_vendor.show(30, truncate=False)

# COMMAND ----------

# DBTITLE 1,F2/F3: Vendor, Channel, Tactic Distribution + Case Sensitivity
# F2/F3: Placement dictionary foundation — vendor, channel, tactic distribution
# Check case sensitivity issues in tactic names

f2_query = """
SELECT
    UPPER(CHANNEL) AS CHANNEL,
    UPPER(SRC_SYS_CD) AS VENDOR,
    TACTIC_NAME,
    UPPER(TRIM(TACTIC_NAME)) AS TACTIC_UPPER,
    COUNT(*) AS row_cnt,
    COUNT(DISTINCT NPI_NUM) AS distinct_npis,
    SUM(EXPOSURE) AS total_exposure,
    SUM(TOTAL_ENGAGEMENT) AS total_engagement
FROM PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB
WHERE UPPER(BRND_NM) LIKE '%KERENDIA%'
  AND DATE_ACT >= '2025-01-01' AND DATE_ACT < '2026-11-01'
GROUP BY UPPER(CHANNEL), UPPER(SRC_SYS_CD), TACTIC_NAME, UPPER(TRIM(TACTIC_NAME))
ORDER BY row_cnt DESC
"""

df_f2 = sf_query(f2_query)
df_f2.cache()

print("=== F2: Channel Distribution ===")
df_f2.groupBy("CHANNEL").agg(
    spark_sum("row_cnt").alias("rows"),
    spark_sum("total_exposure").alias("exposure"),
    spark_sum("total_engagement").alias("engagement")
).orderBy(col("rows").desc()).show(truncate=False)

print("\n=== F2: Vendor (SRC_SYS_CD) Distribution ===")
df_f2.groupBy("VENDOR").agg(
    spark_sum("row_cnt").alias("rows"),
    spark_sum("distinct_npis").alias("npi_touches"),
    spark_sum("total_exposure").alias("exposure")
).orderBy(col("rows").desc()).show(30, truncate=False)

print("\n=== F2: Top 30 Vendor × Tactic combinations ===")
df_f2.groupBy("VENDOR", "TACTIC_UPPER").agg(
    spark_sum("row_cnt").alias("rows"),
    spark_sum("total_exposure").alias("exposure")
).orderBy(col("rows").desc()).show(30, truncate=False)

# F3: Case sensitivity check — tactic names that differ only by case/whitespace
print("\n=== F3: Case Sensitivity Issues ===")
print("Tactic names where raw != UPPER(TRIM(raw)):")
df_case = df_f2.filter(col("TACTIC_NAME") != col("TACTIC_UPPER"))
df_case.select("VENDOR", "TACTIC_NAME", "TACTIC_UPPER", "row_cnt").orderBy(col("row_cnt").desc()).show(30, truncate=False)
print(f"Rows affected by case/whitespace: {df_case.select(spark_sum('row_cnt')).first()[0] or 0:,}")

# COMMAND ----------

# DBTITLE 1,F4: Unmapped Share (rows not matching known placements)
# F4: Unmapped report
# The placement dictionary maps SRC_SYS_CD + TACTIC_NAME to a vendor/placement.
# Rows not matching any known placement go to OTHER.
# Check: what share of rows would be unmapped with the dictionary from section 5.1?

# Known placement patterns from the readiness plan
known_patterns = [
    # (vendor_upper, tactic_pattern)
    ('PULSEPOINT', '%DISPLAY%'),
    ('MEDSCAPE', '%'),  # Banner, Email Alert, Brand Alert, etc.
    ('DOCEREE', '%'),
    ('PEERDIRECT', '%'),
    ('OPENEVIDENCE', '%'),
    ('DOXIMITY', '%'),
    ('EPOCRATES', '%'),
    ('PRESCRIBER POINT', '%'),
    ('HQ EMAIL', '%'),
    ('BIOPHARM', '%'),
    ('HAYMARKET', '%'),
    ('REACHMD', '%'),
    ('MJH', '%'),
    ('IMPIRICUS', '%'),
    ('CONNECTIVERX', '%'),
    ('NATIVO', '%'),
    ('HEALTHCAST', '%'),
    ('MD CALC', '%'),
]
known_vendors = [v for v, _ in known_patterns]

df_f4 = df_f2.withColumn(
    "IS_MAPPED",
    when(col("VENDOR").isin(known_vendors), lit("MAPPED")).otherwise(lit("UNMAPPED"))
)

print("=== F4: Unmapped Share ===")
df_f4_summary = df_f4.groupBy("IS_MAPPED").agg(
    spark_sum("row_cnt").alias("rows"),
    spark_sum("total_exposure").alias("exposure")
)
total_rows = df_f4_summary.select(spark_sum("rows")).first()[0]
df_f4_summary = df_f4_summary.withColumn("pct", F.round(col("rows") / lit(total_rows) * 100, 2))
df_f4_summary.show(truncate=False)

print("\n--- Unmapped vendors ---")
df_f4.filter(col("IS_MAPPED") == "UNMAPPED").groupBy("VENDOR").agg(
    spark_sum("row_cnt").alias("rows"),
    spark_sum("total_exposure").alias("exposure")
).orderBy(col("rows").desc()).show(20, truncate=False)

# COMMAND ----------

# DBTITLE 1,F7: HQ Email Duplication Check
# F7: HQ email duplication
# Check: is HQ EMAIL present in the MMX table as a vendor?
# If yes, it's being double-counted with notebook 15.

print("=== F7: HQ Email Duplication Check ===")

hq_email_query = """
SELECT
    UPPER(CHANNEL) AS CHANNEL,
    UPPER(SRC_SYS_CD) AS VENDOR,
    UPPER(TRIM(TACTIC_NAME)) AS TACTIC,
    COUNT(*) AS row_cnt,
    COUNT(DISTINCT NPI_NUM) AS distinct_npis,
    SUM(EXPOSURE) AS exposure
FROM PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB
WHERE UPPER(BRND_NM) LIKE '%KERENDIA%'
  AND DATE_ACT >= '2025-01-01' AND DATE_ACT < '2026-11-01'
  AND (UPPER(SRC_SYS_CD) LIKE '%HQ%EMAIL%' OR UPPER(SRC_SYS_CD) LIKE '%SFMC%'
       OR UPPER(CHANNEL) LIKE '%HQ%EMAIL%')
GROUP BY UPPER(CHANNEL), UPPER(SRC_SYS_CD), UPPER(TRIM(TACTIC_NAME))
ORDER BY row_cnt DESC
"""

df_hq = sf_query(hq_email_query)
df_hq.show(20, truncate=False)

total_hq = df_hq.select(spark_sum("row_cnt")).first()[0] or 0
print(f"\nTotal HQ email rows in MMX: {total_hq:,}")
print("If > 0, these rows would be double-counted with notebook 15's email event log.")

# COMMAND ----------

# DBTITLE 1,F8: iRep Presence in Digital Block
# F8: iRep in digital block
# Check: is iRep email present in the MMX table?
# If yes, it's being double-counted with the personal promotional block (notebook 16).

print("=== F8: iRep Presence in Digital Block ===")

irep_query = """
SELECT
    UPPER(CHANNEL) AS CHANNEL,
    UPPER(SRC_SYS_CD) AS VENDOR,
    TACTIC_NAME,
    COUNT(*) AS row_cnt,
    COUNT(DISTINCT NPI_NUM) AS distinct_npis
FROM PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB
WHERE UPPER(BRND_NM) LIKE '%KERENDIA%'
  AND DATE_ACT >= '2025-01-01' AND DATE_ACT < '2026-11-01'
  AND (UPPER(SRC_SYS_CD) LIKE '%IREP%' OR UPPER(TACTIC_NAME) LIKE '%IREP%'
       OR UPPER(TACTIC_NAME) LIKE '%I_REP%')
GROUP BY UPPER(CHANNEL), UPPER(SRC_SYS_CD), TACTIC_NAME
ORDER BY row_cnt DESC
"""

df_irep = sf_query(irep_query)
df_irep.show(20, truncate=False)

total_irep = df_irep.select(spark_sum("row_cnt")).first()[0] or 0
print(f"\nTotal iRep email rows in MMX: {total_irep:,}")
print("If > 0, these rows are double-counted with the personal promo block (notebook 16).")

# COMMAND ----------

# DBTITLE 1,F9: Schema Stability — Distinct vendor/tactic sets per month
# F9: Schema stability
# The NBA 3.0 dynamic pivot creates different columns each run.
# Check: how many distinct vendor and tactic combinations appear per month?

f9_query = """
SELECT
    DATE_TRUNC('MONTH', DATE_ACT) AS MONTH,
    COUNT(DISTINCT UPPER(SRC_SYS_CD)) AS n_vendors,
    COUNT(DISTINCT UPPER(TRIM(TACTIC_NAME))) AS n_tactics,
    COUNT(DISTINCT UPPER(SRC_SYS_CD) || '|' || UPPER(TRIM(TACTIC_NAME))) AS n_vendor_tactic_combos
FROM PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB
WHERE UPPER(BRND_NM) LIKE '%KERENDIA%'
  AND DATE_ACT >= '2025-01-01' AND DATE_ACT < '2026-11-01'
GROUP BY DATE_TRUNC('MONTH', DATE_ACT)
ORDER BY MONTH
"""

df_f9 = sf_query(f9_query)
print("=== F9: Schema Stability — Distinct vendors/tactics per month ===")
df_f9.show(30, truncate=False)

# Check if vendor-tactic combos change month to month
min_combos = df_f9.select(F.min("n_vendor_tactic_combos")).first()[0]
max_combos = df_f9.select(F.max("n_vendor_tactic_combos")).first()[0]
print(f"Vendor×Tactic combos range: {min_combos} to {max_combos}")
if min_combos != max_combos:
    print("UNSTABLE: the pivot schema changes between months — confirms the need for a fixed dictionary.")
else:
    print("STABLE: same combo count every month.")

# COMMAND ----------

# DBTITLE 1,F1b: Indication Dimension from Brand Values
# F1b: Indication dimension
# Can we derive HF / T1D / CKD indication from the brand name values?

print("=== F1b: Indication from BRND_NM (Kerendia variants) ===")
df_f1.select("BRND_NM", "row_cnt", "distinct_npis").orderBy(col("row_cnt").desc()).show(50, truncate=False)

# Monthly trend of exact vs indication-tagged
f1b_monthly = """
SELECT
    DATE_TRUNC('MONTH', DATE_ACT) AS MONTH,
    SUM(CASE WHEN UPPER(BRND_NM) = 'KERENDIA' THEN 1 ELSE 0 END) AS exact_rows,
    SUM(CASE WHEN UPPER(BRND_NM) LIKE '%KERENDIA%' AND UPPER(BRND_NM) != 'KERENDIA' THEN 1 ELSE 0 END) AS indication_rows,
    COUNT(*) AS total_rows
FROM PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB
WHERE UPPER(BRND_NM) LIKE '%KERENDIA%'
  AND DATE_ACT >= '2025-01-01' AND DATE_ACT < '2026-11-01'
GROUP BY DATE_TRUNC('MONTH', DATE_ACT)
ORDER BY MONTH
"""
df_f1b = sf_query(f1b_monthly)
print("\n--- Monthly exact vs indication-tagged rows ---")
df_f1b.show(30, truncate=False)

# COMMAND ----------

# DBTITLE 1,Phase 0 HCP Digital Validation — Main Findings
# MAGIC %md
# MAGIC # Phase 0 HCP Digital Validation — Main Findings
# MAGIC
# MAGIC **Run date:** Nov 2, 2026  |  **Source:** Snowflake `PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB`  |  **Period:** Jan 2025 – Oct 2026
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## F1 — Brand Filter Gap (Exact vs LIKE)
# MAGIC
# MAGIC The NBA 3.0 filter `UPPER(BRND_NM) = 'KERENDIA'` captures **128,464,904 rows** (456,863 NPIs). Using `LIKE '%KERENDIA%'` adds **1,440,538 rows** (145 additional NPIs) — a **1.1% gap** overall, but concentrated in specific vendors.
# MAGIC
# MAGIC ### Per-vendor gap (rows lost by NBA 3.0 exact filter)
# MAGIC
# MAGIC | Vendor | Exact Rows | LIKE Rows | Gap % |
# MAGIC |--------|-----------|-----------|-------|
# MAGIC | DOCEREE | 98,530 | 855,022 | **88.5%** |
# MAGIC | REACHMD | 6,240 | 46,329 | **86.5%** |
# MAGIC | PEERDIRECT | 308,129 | 950,133 | **67.6%** |
# MAGIC | DOXIMITY | 1,450,873 | 1,452,826 | 0.1% |
# MAGIC | All others | — | — | 0.0% |
# MAGIC
# MAGIC Doceree (88.5%) matches the expected ~88%; PeerDirect (67.6%) is below the expected ~74%. The gap is driven by indication-tagged brand names (KERENDIA HF, KERENDIA_CKD, etc.) that only these three vendors carry.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## F1b — Indication Dimension from Brand Values
# MAGIC
# MAGIC **11 distinct BRND_NM values** containing KERENDIA were found:
# MAGIC
# MAGIC | BRND_NM | Rows | Distinct NPIs |
# MAGIC |---------|------|-------------|
# MAGIC | KERENDIA | 128,464,904 | 456,863 |
# MAGIC | KERENDIA HF | 443,082 | 12,736 |
# MAGIC | KERENDIA_HF | 370,520 | 33,860 |
# MAGIC | KERENDIA_CKD | 271,484 | 27,715 |
# MAGIC | KERENDIA CKD | 205,959 | 1,484 |
# MAGIC | KERENDIA UACR | 109,404 | 2,126 |
# MAGIC | KERENDIAAD | 18,403 | 3,433 |
# MAGIC | KERENDIA-CKD | 14,370 | 2,280 |
# MAGIC | KERENDIA-HF | 4,268 | 1,206 |
# MAGIC | KERENDIA-FINEARTS | 1,929 | 815 |
# MAGIC | KERENDIA-FINEONE | 1,119 | 489 |
# MAGIC
# MAGIC Indication-tagged rows appeared starting **Apr 2025** (45,841 rows) and continue through Oct 2026 (79,947 rows). HF and CKD are the main indications, with UACR (albuminuria) also present. **KERENDIAAD** and **KERENDIA-FINEARTS/FINEONE** need investigation — these may be data entry errors or new programs.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## F2 — Vendor / Channel / Tactic Distribution
# MAGIC
# MAGIC ### Channel distribution
# MAGIC
# MAGIC | Channel | Rows | Exposure | Engagement |
# MAGIC |---------|------|----------|------------|
# MAGIC | BANNER | 110,585,310 | 110,986,846 | 92,435 |
# MAGIC | HQ EMAIL | 9,500,178 | 3,872,999 | 1,121,013 |
# MAGIC | CUSTOM | 4,308,266 | 4,308,266 | 409,685 |
# MAGIC | 3RD PARTY EMAIL | 3,159,505 | 1,353,888 | 391,620 |
# MAGIC | CALL | 1,634,169 | 1,634,169 | 1,634,169 |
# MAGIC | IREP EMAIL | 541,094 | 202,312 | 128,911 |
# MAGIC | SAMPLE | 176,920 | 176,920 | 176,920 |
# MAGIC
# MAGIC PulsePoint (programmatic display) dominates with 108.9M rows (84% of total). 25 distinct vendors across 7 channels.
# MAGIC
# MAGIC ### Top vendor × tactic combos
# MAGIC
# MAGIC PULSEPOINT/PROGRAMATIC_DISPLAY (108.9M), HQ EMAIL/HQ EMAIL (9.4M), MEDSCAPE/EMAIL ALERT (1.3M), DOXIMITY/DOCNEWS (1.2M), DOCEREE/EHR BANNER (855K), PEERDIRECT/MDFI-EMAIL (547K).
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## F3 — Case Sensitivity Issues
# MAGIC
# MAGIC **128,101,062 rows (98.5% of all rows) have tactic names that differ from their UPPER(TRIM()) form.** Virtually every tactic name in the raw data uses mixed case. Examples:
# MAGIC
# MAGIC | Vendor | Raw TACTIC_NAME | UPPER(TRIM()) | Rows |
# MAGIC |--------|----------------|---------------|------|
# MAGIC | PULSEPOINT | Programatic_DISPLAY | PROGRAMATIC_DISPLAY | 108,886,402 |
# MAGIC | HQ EMAIL | HQ Email | HQ EMAIL | 9,392,066 |
# MAGIC | CALL | F2F Call | F2F CALL | 1,625,843 |
# MAGIC | MEDSCAPE | Email Alert | EMAIL ALERT | 1,269,480 |
# MAGIC | DOXIMITY | DocNews | DOCNEWS | 1,156,341 |
# MAGIC
# MAGIC **Conclusion:** All tactic matching must use `UPPER(TRIM(TACTIC_NAME))` to avoid duplicate dictionary entries.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## F4 — Unmapped Share
# MAGIC
# MAGIC | Status | Rows | Exposure | Pct |
# MAGIC |--------|------|----------|-----|
# MAGIC | MAPPED | 127,046,329 | 120,228,785 | 97.80% |
# MAGIC | UNMAPPED | 2,859,113 | 2,306,615 | **2.20%** |
# MAGIC
# MAGIC The unmapped share is **2.2%, above the 1% threshold**. The largest unmapped vendors are:
# MAGIC
# MAGIC | Vendor | Rows | Reason |
# MAGIC |--------|------|--------|
# MAGIC | CALL | 1,634,169 | Not in dictionary (personal promo overlap) |
# MAGIC | IREP EMAIL | 541,094 | Not in dictionary (personal promo overlap) |
# MAGIC | HAYMARKET-DISPLAY | 259,166 | Name mismatch: dict has 'HAYMARKET' |
# MAGIC | SAMPLE | 176,920 | Not in dictionary |
# MAGIC | PRESCRIBER_POINT | 115,484 | Name mismatch: dict has 'PRESCRIBER POINT' (space) |
# MAGIC | MJHLIFESCIENCES | 12,829 | Name mismatch: dict has 'MJH' |
# MAGIC | MD_CALC | 11,331 | Name mismatch: dict has 'MD CALC' (space) |
# MAGIC
# MAGIC Three vendor name mismatches (HAYMARKET, MJH, MD CALC) account for ~283K rows that should be mapped. Fixing these would reduce unmapped to ~1.9%.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## F7 — HQ Email Duplication
# MAGIC
# MAGIC **9,500,178 HQ email rows** are present in the MMX table. These would be double-counted with notebook 15's email event log if both sources are used without deduplication.
# MAGIC
# MAGIC | Vendor | Rows | NPIs | Exposure |
# MAGIC |--------|------|------|----------|
# MAGIC | HQ EMAIL | 9,392,066 | 188,780 | 3,837,466 |
# MAGIC | COPAY | 70,281 | 12 | 23,342 |
# MAGIC | KERENDIA_FTO | 32,667 | 6 | 10,703 |
# MAGIC | KERENDIA_SIGNUP | 5,164 | 1 | 1,488 |
# MAGIC
# MAGIC **Action:** Exclude `CHANNEL = 'HQ EMAIL'` from the MMX digital block, or deduplicate against notebook 15.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## F8 — iRep Duplication
# MAGIC
# MAGIC **541,094 iRep email rows** are present in the MMX table (31,746 distinct NPIs). These overlap with the personal promotional block (notebook 16 / 41_field_activity) which already captures iRep email from `FACT_SENT_EMAIL`.
# MAGIC
# MAGIC **Action:** Exclude `SRC_SYS_CD = 'IREP EMAIL'` from the MMX digital block.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## F9 — Schema Stability
# MAGIC
# MAGIC The vendor×tactic combo count **ranges from 16 (Jan 2025) to 42 (Jul–Aug 2026)** — the pivot schema is **UNSTABLE** across months. This confirms the need for a fixed placement dictionary rather than NBA 3.0's dynamic pivot.
# MAGIC
# MAGIC | Period | Vendors | Tactics | Combos |
# MAGIC |--------|---------|--------|--------|
# MAGIC | Jan 2025 | 8 | 16 | 16 |
# MAGIC | Jul 2025 | 11 | 30 | 30 |
# MAGIC | Apr 2026 | 20 | 37 | 40 |
# MAGIC | Oct 2026 | 13 | 23 | 26 |
# MAGIC
# MAGIC The combo count roughly doubled over the period, with new vendors and tactics appearing mid-2025 and peaking in summer 2026.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Summary of Key Issues
# MAGIC
# MAGIC 1. **Brand filter gap (F1):** 1.44M rows lost by exact `= 'KERENDIA'` filter, concentrated in Doceree (88.5%), ReachMD (86.5%), and PeerDirect (67.6%). Use `LIKE '%KERENDIA%'`.
# MAGIC 2. **Indication tags (F1b):** 11 brand variants encode HF, CKD, UACR indications. Two unknown values (KERENDIAAD, KERENDIA-FINEARTS/FINEONE) need investigation.
# MAGIC 3. **Case sensitivity (F3):** 98.5% of rows have mixed-case tactic names. All matching must use `UPPER(TRIM())`.
# MAGIC 4. **Unmapped share (F4):** 2.2% unmapped, above the 1% threshold. Three vendor name mismatches (HAYMARKET, MJH, MD CALC) account for ~283K fixable rows.
# MAGIC 5. **HQ email duplication (F7):** 9.5M HQ email rows in MMX overlap with notebook 15. Must exclude.
# MAGIC 6. **iRep duplication (F8):** 541K iRep rows in MMX overlap with personal promo block. Must exclude.
# MAGIC 7. **Schema instability (F9):** Vendor×tactic combos range 16–42 across months. Fixed dictionary required.