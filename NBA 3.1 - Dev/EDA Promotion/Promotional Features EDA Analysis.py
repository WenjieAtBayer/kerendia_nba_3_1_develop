# Databricks notebook source
# DBTITLE 1,Header
# MAGIC %md
# MAGIC # Kerendia NBA 3.0 — Promotional Features EDA
# MAGIC
# MAGIC Comprehensive analysis of **9 promotional feature notebooks** used in the HCP-level model, categorized into **Personal** vs **Non-Personal** promotions.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Channel Classification
# MAGIC
# MAGIC | # | Notebook | Channel | Promotion Type | Granularity | Source System |
# MAGIC |---|----------|---------|---------------|-------------|---------------|
# MAGIC | 1 | `25_promotional_features_call` | **Sales Rep Calls** (F2F, Phone, Remote, Group) | **Personal** | HCP (BHID) | CPH_DB_PROD.MODEL_V2.FACT_CALL |
# MAGIC | 2 | `14_promotional_features_speaker_program` | **Speaker Programs** (events attended by format/topic) | **Personal** | HCP (BHID) | CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM |
# MAGIC | 3 | `17_promotional_features_samples` | **Samples** (10mg/20mg dropped/shipped) | **Personal** | HCP (BHID) | PHCDW.PHCDW_DSAA.VIEW_KERENDIA_SAMPLES_DROPPED_SHIPPED |
# MAGIC | 4 | `18_promotional_ClickStream_features` | **ClickStream/CLM** (content shown during calls) | **Personal** | HCP (BHID) | CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM |
# MAGIC | 5 | `16_promotional_features_irep` | **iRep Emails** (rep-triggered approved emails) | **Personal** | HCP (BHID) | PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_IREP |
# MAGIC | 6 | `15_promotional_features_HQ_Emails` | **HQ Emails** (HQ-initiated mass emails) | **Non-Personal** | HCP (BHID) | PHCDW.PHCDW_CDM.HCP_EMAIL_LIST |
# MAGIC | 7 | `24_Features_Digital` | **Digital/Paid Media** (programmatic, paid search, display) | **Non-Personal** | HCP (NPI) | PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB |
# MAGIC | 8 | `34_promotional_features_DTC` | **DTC** (Direct-to-Consumer: Healthline, WebMD, FB+IG) | **Non-Personal** | DMA (geographic) | Parquet files (DirectBuys, PulsePoint, TTD, Social) |
# MAGIC | 9 | `19_ftp_features` | **Free Trial Program** (voucher/copay redemptions) | **Non-Personal** | HCP (NPI→BHID) | PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP |

# COMMAND ----------

# DBTITLE 1,Setup & Read Output Parquet Files
import pandas as pd
import numpy as np
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Base volume path
base_vol = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/dev_folder/notebook_output"

# --- Read output parquet files from each promotional notebook ---

# 1. Calls (Personal)
try:
    df_calls = spark.read.parquet(f"{base_vol}/kerendia_nba_3_hcp_model_call_features.parquet")
    calls_shape = (df_calls.count(), len(df_calls.columns))
except Exception as e:
    df_calls = None
    calls_shape = (0, 0)
    print(f"Calls load error: {e}")

print(f"Calls: rows={calls_shape[0]:,}, cols={calls_shape[1]}")

# COMMAND ----------

# DBTITLE 1,Read Speaker Program & HQ Emails Output
# 2. Speaker Programs (Personal)
try:
    df_speaker = spark.read.parquet(f"{base_vol}/kerendia_nba_3_hcp_model_speaker_program.parquet")
    speaker_shape = (df_speaker.count(), len(df_speaker.columns))
except Exception as e:
    df_speaker = None
    speaker_shape = (0, 0)
    print(f"Speaker load error: {e}")

print(f"Speaker Programs: rows={speaker_shape[0]:,}, cols={speaker_shape[1]}")

# 3. HQ Emails (Non-Personal)
try:
    df_hq_emails = spark.read.parquet(f"{base_vol}/kerendia_nba_3_hcp_model_hq_email_features.parquet")
    hq_emails_shape = (df_hq_emails.count(), len(df_hq_emails.columns))
except Exception as e:
    df_hq_emails = None
    hq_emails_shape = (0, 0)
    print(f"HQ Emails load error: {e}")

print(f"HQ Emails: rows={hq_emails_shape[0]:,}, cols={hq_emails_shape[1]}")

# COMMAND ----------

# DBTITLE 1,Read iRep, Samples & ClickStream Output
# 4. iRep Emails (Personal)
try:
    df_irep = spark.read.parquet(f"{base_vol}/kerendia_nba_3_hcp_model_irep_features.parquet")
    irep_shape = (df_irep.count(), len(df_irep.columns))
except Exception as e:
    df_irep = None
    irep_shape = (0, 0)
    print(f"iRep load error: {e}")

print(f"iRep Emails: rows={irep_shape[0]:,}, cols={irep_shape[1]}")

# 5. Samples (Personal)
try:
    df_samples = spark.read.parquet(f"{base_vol}/kerendia_nba_3_hcp_model_samples_features.parquet")
    samples_shape = (df_samples.count(), len(df_samples.columns))
except Exception as e:
    df_samples = None
    samples_shape = (0, 0)
    print(f"Samples load error: {e}")

print(f"Samples: rows={samples_shape[0]:,}, cols={samples_shape[1]}")

# 6. ClickStream (Personal)
try:
    df_clickstream = spark.read.parquet(f"{base_vol}/kerendia_nba_3_hcp_model_clickstream_features.parquet")
    clickstream_shape = (df_clickstream.count(), len(df_clickstream.columns))
except Exception as e:
    df_clickstream = None
    clickstream_shape = (0, 0)
    print(f"ClickStream load error: {e}")

print(f"ClickStream: rows={clickstream_shape[0]:,}, cols={clickstream_shape[1]}")

# COMMAND ----------

# DBTITLE 1,Read FTP, Digital & DTC Output
# 7. FTP (Non-Personal)
try:
    df_ftp = spark.read.parquet(f"{base_vol}/kerendia_nba_3_hcp_model_ftp_features.parquet")
    ftp_shape = (df_ftp.count(), len(df_ftp.columns))
except Exception as e:
    df_ftp = None
    ftp_shape = (0, 0)
    print(f"FTP load error: {e}")

print(f"FTP: rows={ftp_shape[0]:,}, cols={ftp_shape[1]}")

# 8. Digital (Non-Personal) - notebook 24 writes to paid_search_features
try:
    df_digital = spark.read.parquet(f"{base_vol}/kerendia_nba_3_0_hcp_model_paid_search_features.parquet")
    digital_shape = (df_digital.count(), len(df_digital.columns))
except Exception as e:
    df_digital = None
    digital_shape = (0, 0)
    print(f"Digital load error: {e}")

print(f"Digital: rows={digital_shape[0]:,}, cols={digital_shape[1]}")

# 9. DTC (Non-Personal)
try:
    df_dtc = spark.read.parquet(f"{base_vol}/kerendia_nba_3_hcp_model_DTC_PROMOTION.parquet")
    dtc_shape = (df_dtc.count(), len(df_dtc.columns))
except Exception as e:
    df_dtc = None
    dtc_shape = (0, 0)
    print(f"DTC load error: {e}")

print(f"DTC: rows={dtc_shape[0]:,}, cols={dtc_shape[1]}")

# COMMAND ----------

# DBTITLE 1,Summary Overview Table
# Build summary dataframe
summary_data = [
    ('Sales Rep Calls', '25', 'Personal', 'HCP (BHID)', calls_shape[0], calls_shape[1], 'CPH_DB_PROD.MODEL_V2.FACT_CALL', 'F2F, Phone, Remote, Group calls; Call type, purpose, duration'),
    ('Speaker Programs', '14', 'Personal', 'HCP (BHID)', speaker_shape[0], speaker_shape[1], 'CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM', 'Events attended by format (F2F/Remote/Hybrid), topic'),
    ('Samples', '17', 'Personal', 'HCP (BHID)', samples_shape[0], samples_shape[1], 'PHCDW.PHCDW_DSAA.VIEW_KERENDIA_SAMPLES_DROPPED_SHIPPED', 'Sample counts by dosage (10mg/20mg), shipped/dropped'),
    ('ClickStream/CLM', '18', 'Personal', 'HCP (BHID)', clickstream_shape[0], clickstream_shape[1], 'CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM', 'Usage duration, presentation duration during calls'),
    ('iRep Emails', '16', 'Personal', 'HCP (BHID)', irep_shape[0], irep_shape[1], 'PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_IREP', 'Rep-triggered emails: delivered, clicked, opened, by doc name'),
    ('HQ Emails', '15', 'Non-Personal', 'HCP (BHID)', hq_emails_shape[0], hq_emails_shape[1], 'PHCDW.PHCDW_CDM.HCP_EMAIL_LIST', 'HQ mass emails: Bounce, Click, Open, Sent, Unsubscribe'),
    ('Digital/Paid Media', '24', 'Non-Personal', 'HCP (NPI)', digital_shape[0], digital_shape[1], 'PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB', 'Multi-channel engagement: deep/light/total, exposure'),
    ('DTC Promotions', '34', 'Non-Personal', 'DMA (geographic)', dtc_shape[0], dtc_shape[1], 'Parquet (DirectBuys, PulsePoint, TTD, Social)', 'Impressions & clicks: Healthline, WebMD, FB+IG, PulsePoint'),
    ('Free Trial Program', '19', 'Non-Personal', 'HCP (NPI->BHID)', ftp_shape[0], ftp_shape[1], 'PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP', 'Voucher/copay redemption counts with reversal handling'),
]

df_summary = spark.createDataFrame(summary_data, 
    ['Channel', 'Notebook_ID', 'Promotion_Type', 'Granularity', 'Rows', 'Columns', 'Source_System', 'Features_Description'])

display(df_summary)

# COMMAND ----------

# DBTITLE 1,Section: Feature Engineering Patterns
# MAGIC %md
# MAGIC ## Feature Engineering Patterns
# MAGIC
# MAGIC All notebooks follow a **consistent 3-step pattern**:
# MAGIC 1. **Step 1**: Load raw data from Snowflake/parquet → process → create binary flags
# MAGIC 2. **Step 2**: Cross-join with cohort anchor dates (26 monthly cohorts C01–C26) → filter to lookback window
# MAGIC 3. **Step 3**: Aggregate features per `HCP_COHORT_ID` using rolling windows (last 1/3/6/9/12 months)
# MAGIC
# MAGIC **Common Aggregations**: SUM, MEAN, MAX, COUNT across lookback periods
# MAGIC
# MAGIC **Key Identifier**: All features eventually map to `BHID` (Bayer HCP ID) + `COHORT` → `HCP_COHORT_ID`

# COMMAND ----------

# DBTITLE 1,Feature Column Analysis by Channel
# List feature columns for each channel (excluding ID/date columns)
id_cols = {'HCP_COHORT_ID', 'BHID', 'NPI_NUMBER', 'MONTH_ID', 'SVC_DT_M', 'COHORT', 
           'LOOKBACK_START_DATE', 'LOOKBACK_END_DATE', 'DMA_Code', 'DATA_MONTH'}

results = []

for name, df_obj in [('Sales Rep Calls', df_calls), ('Speaker Programs', df_speaker), 
                      ('Samples', df_samples), ('ClickStream/CLM', df_clickstream),
                      ('iRep Emails', df_irep), ('HQ Emails', df_hq_emails),
                      ('Digital/Paid Media', df_digital), ('DTC Promotions', df_dtc),
                      ('Free Trial Program', df_ftp)]:
    if df_obj is not None:
        feat_cols = [c for c in df_obj.columns if c not in id_cols]
        results.append((name, len(feat_cols), ', '.join(feat_cols[:10]) + ('...' if len(feat_cols) > 10 else '')))
    else:
        results.append((name, 0, 'NOT LOADED'))

df_feat_summary = spark.createDataFrame(results, ['Channel', 'Feature_Count', 'Sample_Features'])
display(df_feat_summary)

# COMMAND ----------

# DBTITLE 1,Null Percentage Analysis
# Analyze null/zero percentages for each loaded dataset (numeric cols only)
from pyspark.sql import functions as F
from pyspark.sql.types import NumericType

null_results = []

for name, df_obj, promo_type in [
    ('Sales Rep Calls', df_calls, 'Personal'), 
    ('Speaker Programs', df_speaker, 'Personal'), 
    ('Samples', df_samples, 'Personal'), 
    ('ClickStream/CLM', df_clickstream, 'Personal'),
    ('iRep Emails', df_irep, 'Personal'), 
    ('HQ Emails', df_hq_emails, 'Non-Personal'),
    ('Digital/Paid Media', df_digital, 'Non-Personal'), 
    ('DTC Promotions', df_dtc, 'Non-Personal'),
    ('Free Trial Program', df_ftp, 'Non-Personal')]:
    
    if df_obj is not None:
        total_rows = df_obj.count()
        # Only select numeric feature columns for zero analysis
        numeric_feat_cols = [f.name for f in df_obj.schema.fields 
                            if f.name not in id_cols and isinstance(f.dataType, NumericType)]
        
        if numeric_feat_cols and total_rows > 0:
            sample_cols = numeric_feat_cols[:30]  # Limit for performance
            null_exprs = [F.sum(F.when(F.col(c).isNull(), 1).otherwise(0)).alias(c) for c in sample_cols]
            zero_exprs = [F.sum(F.when(F.col(c) == 0, 1).otherwise(0)).alias(c) for c in sample_cols]
            
            null_counts = df_obj.select(null_exprs).collect()[0]
            zero_counts = df_obj.select(zero_exprs).collect()[0]
            
            avg_null_pct = round(sum([null_counts[c] for c in sample_cols]) / (total_rows * len(sample_cols)) * 100, 2)
            avg_zero_pct = round(sum([zero_counts[c] for c in sample_cols]) / (total_rows * len(sample_cols)) * 100, 2)
            
            null_results.append((name, promo_type, total_rows, len(numeric_feat_cols), avg_null_pct, avg_zero_pct, round(100 - avg_null_pct - avg_zero_pct, 2)))
        else:
            null_results.append((name, promo_type, total_rows, 0, 0.0, 0.0, 0.0))
    else:
        null_results.append((name, promo_type, 0, 0, 0.0, 0.0, 0.0))

df_quality = spark.createDataFrame(null_results, 
    ['Channel', 'Promotion_Type', 'Total_Rows', 'Numeric_Feature_Count', 'Avg_Null_Pct', 'Avg_Zero_Pct', 'Avg_NonZero_Pct'])
display(df_quality)

# COMMAND ----------

# DBTITLE 1,HCP Coverage Analysis
# Analyze distinct HCP count per channel
hcp_coverage = []

for name, df_obj, promo_type in [
    ('Sales Rep Calls', df_calls, 'Personal'), 
    ('Speaker Programs', df_speaker, 'Personal'), 
    ('Samples', df_samples, 'Personal'), 
    ('ClickStream/CLM', df_clickstream, 'Personal'),
    ('iRep Emails', df_irep, 'Personal'), 
    ('HQ Emails', df_hq_emails, 'Non-Personal'),
    ('Digital/Paid Media', df_digital, 'Non-Personal'), 
    ('DTC Promotions', df_dtc, 'Non-Personal'),
    ('Free Trial Program', df_ftp, 'Non-Personal')]:
    
    if df_obj is not None:
        # Try to find the HCP identifier column
        hcp_col = None
        for candidate in ['HCP_COHORT_ID', 'BHID', 'NPI_NUMBER']:
            if candidate in df_obj.columns:
                hcp_col = candidate
                break
        
        if hcp_col == 'HCP_COHORT_ID':
            # Extract BHID from HCP_COHORT_ID (format: BHID_COHORT)
            distinct_hcps = df_obj.withColumn('_bhid', F.regexp_extract(F.col('HCP_COHORT_ID'), r'^(BH\d+)', 1)).select('_bhid').distinct().count()
        elif hcp_col:
            distinct_hcps = df_obj.select(hcp_col).distinct().count()
        else:
            distinct_hcps = 0
        
        hcp_coverage.append((name, promo_type, distinct_hcps, hcp_col or 'DMA_Code (geo)'))
    else:
        hcp_coverage.append((name, promo_type, 0, 'N/A'))

df_hcp = spark.createDataFrame(hcp_coverage, ['Channel', 'Promotion_Type', 'Distinct_HCPs', 'ID_Column'])
display(df_hcp.orderBy(F.desc('Distinct_HCPs')))

# COMMAND ----------

# DBTITLE 1,Section: Detailed Channel Analysis
# MAGIC %md
# MAGIC ## Detailed Channel Analysis
# MAGIC
# MAGIC ### Personal Promotions
# MAGIC These channels involve **direct human interaction** between a sales representative and an HCP:
# MAGIC
# MAGIC * **Sales Rep Calls (25)**: Core personal channel. Features capture call frequency by channel type (F2F, Phone, Remote, Group), call type (Detail Only, Detail with Sample, Group Detail), call purpose (promotional vs non-promotional), and call duration.
# MAGIC * **Speaker Programs (14)**: Events organized for HCPs with speakers. Features track attendance by event format (Face-to-Face, Remote, Hybrid, In-Office Meal), event type, and speaker topic (e.g., Introduction to KERENDIA).
# MAGIC * **Samples (17)**: Drug sample distribution during rep visits. Features count samples by dosage (10mg, 20mg), form (regular, BRC), and status (dropped vs shipped).
# MAGIC * **ClickStream/CLM (18)**: Closed-Loop Marketing content presented during rep calls. Features capture max usage duration and presentation duration per call.
# MAGIC * **iRep Emails (16)**: Rep-initiated approved emails via Veeva iRep. Features track delivered, clicked, and opened emails, with breakdowns by approved document name.
# MAGIC
# MAGIC ### Non-Personal Promotions
# MAGIC These channels are **automated/digital** with no direct rep involvement:
# MAGIC
# MAGIC * **HQ Emails (15)**: Headquarters-triggered mass email campaigns. Features track Bounce, Click, Open, Sent, and Unsubscribe events per HCP.
# MAGIC * **Digital/Paid Media (24)**: Multi-channel digital engagement (Doximity, EHR, Display, Paid Search, Social, etc.). Features capture Deep/Light/Total engagement and Exposure by channel, source system code, and tactic name. **Highest feature dimensionality** (342+ from SRC_SYS_CD alone).
# MAGIC * **DTC Promotions (34)**: Direct-to-Consumer advertising at the **DMA (geographic) level**, not HCP-specific. Vendors include Healthline, HealthUnion, WebMD, Sharecare, PulsePoint, TTD Display, and Social (FB+IG). Features are Impressions and Clicks by vendor.
# MAGIC * **Free Trial Program (19)**: Patient copay/voucher redemptions mapped to prescribing HCPs. Includes reversal handling logic to remove cancelled claims.

# COMMAND ----------

# DBTITLE 1,Descriptive Stats for Each Personal Channel
# Descriptive statistics for personal promotion channels
for name, df_obj in [('Sales Rep Calls', df_calls), ('Speaker Programs', df_speaker), 
                      ('Samples', df_samples), ('ClickStream/CLM', df_clickstream),
                      ('iRep Emails', df_irep)]:
    if df_obj is not None:
        feat_cols = [c for c in df_obj.columns if c not in id_cols]
        if feat_cols:
            print(f"\n{'='*80}")
            print(f"PERSONAL | {name} - {len(feat_cols)} features")
            print(f"{'='*80}")
            # Show describe for first 8 feature columns
            df_obj.select(feat_cols[:8]).describe().display()
    else:
        print(f"\n{name}: NOT LOADED")

# COMMAND ----------

# DBTITLE 1,Descriptive Stats for Each Non-Personal Channel
# Descriptive statistics for non-personal promotion channels
for name, df_obj in [('HQ Emails', df_hq_emails), ('Digital/Paid Media', df_digital), 
                      ('DTC Promotions', df_dtc), ('Free Trial Program', df_ftp)]:
    if df_obj is not None:
        feat_cols = [c for c in df_obj.columns if c not in id_cols]
        if feat_cols:
            print(f"\n{'='*80}")
            print(f"NON-PERSONAL | {name} - {len(feat_cols)} features")
            print(f"{'='*80}")
            # Show describe for first 8 feature columns
            df_obj.select(feat_cols[:8]).describe().display()
    else:
        print(f"\n{name}: NOT LOADED")

# COMMAND ----------

# DBTITLE 1,Feature Correlation within Calls (Top Channel)
# Correlation analysis for the largest personal channel (Calls)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

if df_calls is not None:
    feat_cols = [c for c in df_calls.columns if c not in id_cols]
    # Select core 1-month features for correlation
    month1_cols = [c for c in feat_cols if c.endswith('_IN_LAST_1_MONTH')][:12]
    short_labels = [c.replace('TOTAL_', '').replace('_IN_LAST_1_MONTH', '') for c in month1_cols]
    
    pdf_calls = df_calls.select(month1_cols).sample(fraction=0.01, seed=42).toPandas()
    pdf_calls = pdf_calls.apply(pd.to_numeric, errors='coerce')
    pdf_calls.columns = short_labels
    
    corr_matrix = pdf_calls.corr()
    
    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(corr_matrix.values, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
    ax.set_xticks(range(len(short_labels)))
    ax.set_yticks(range(len(short_labels)))
    ax.set_xticklabels(short_labels, rotation=45, ha='right', fontsize=8)
    ax.set_yticklabels(short_labels, fontsize=8)
    plt.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title('Feature Correlation Heatmap - Sales Rep Calls (1-month features)', fontsize=13)
    plt.tight_layout()
    plt.show()
else:
    print("Calls dataset not loaded")

# COMMAND ----------

# DBTITLE 1,Key Observations Summary
# MAGIC %md
# MAGIC ## Key Observations & Architectural Notes
# MAGIC
# MAGIC ### Data Architecture
# MAGIC * **Cohort-based design**: All features use 26 rolling monthly cohorts (C01–C26), each with a 13-month lookback window
# MAGIC * **Lookback aggregations**: Features are aggregated over last 1, 3, 6, 9, and 12 months using a step2/step3 helper function
# MAGIC * **Common join key**: `HCP_COHORT_ID` = `BHID` + `_` + `COHORT` (e.g., `BH12345678_C01`)
# MAGIC
# MAGIC ### Personal vs Non-Personal Balance
# MAGIC * **5 Personal channels**: Calls, Speaker Programs, Samples, ClickStream, iRep Emails
# MAGIC * **4 Non-Personal channels**: HQ Emails, Digital/Paid Media, DTC, FTP
# MAGIC * Personal channels generate features at **individual HCP level** (BHID)
# MAGIC * DTC is the only channel at **DMA (geographic) level** — not HCP-specific
# MAGIC
# MAGIC ### Feature Dimensionality
# MAGIC * **Digital/Paid Media** has the highest dimensionality (~500+ features) due to pivoting by Channel, SRC_SYS_CD, and Tactic Name
# MAGIC * **Calls** is the richest personal channel with features across 4 dimensions: channel type, call type, call purpose, and duration
# MAGIC * **DTC** features are sparse (impressions/clicks by vendor) and joined to HCPs via geographic DMA mapping
# MAGIC
# MAGIC ### Data Quality Considerations
# MAGIC * **Sparsity**: Most promotional features are highly sparse (majority zeros) since most HCPs don't receive all promotion types
# MAGIC * **Date ranges**: Data spans from ~2022-03 to 2025-04 across all channels
# MAGIC * **Reversal handling**: FTP notebook explicitly handles claim reversals (negative DAY_SUPPLY values)
# MAGIC * **Deduplication**: Speaker Programs and ClickStream notebooks include explicit deduplication logic