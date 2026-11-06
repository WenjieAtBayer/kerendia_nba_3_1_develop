---
name: promotional-data-eda
description: Guidance for querying and exploring raw Kerendia promotional data across all channels (Calls, Speaker Programs, HQ Emails, iRep Emails, Samples, ClickStream, IQVIA Channel, Digital/MMX). Read this skill when the user asks about Kerendia promotional data, promotional channel tables, HCP engagement metrics, or wants to explore raw promotional activity.
---

# Promotional Data EDA — Kerendia

This skill provides guidance for querying the raw promotional data sources used in the Kerendia NBA 3.x pipeline. These tables feed into HCP-level promotional feature engineering.

## Data Access Pattern

All Snowflake tables are queried via `Get_Data_Snowflakes(query)` helper function (loaded from `00_connection` notebook). Databricks Delta tables are read via `spark.read.format("delta").load(path)`. Unity Catalog tables are queried via `spark.sql(query)`.

Connection and helper notebooks:
```
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_step23_function"
```

## Common Reference Data

### Cohort Anchor Dates
All promotional notebooks use lookback windows defined by cohort anchor dates:
```python
cohort_anchor_dates = spark.read.format("delta").load(
    "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/promotional_cohort_inference_dates"
)
LOOKBACK_START_DATE = cohort_anchor_dates.filter(F.col("COHORT") == "I01").first()["LOOKBACK_START_DATE"]
LOOKBACK_END_DATE = cohort_anchor_dates.filter(F.col("COHORT") == "I01").first()["LOOKBACK_END_DATE"]
```

### HCP Universe
```python
hcp_universe = spark.read.format("delta").load(
    "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference"
)
```

### NPI ↔ BHID Mapping
```python
df_hcp_npi_mapping = spark.read.format("delta").load(
    "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/kerendia_nba_3_0_npi_bhid_mapping"
)
# Columns: NPI_NUMBER, BH_ID (BHID), PROVIDER_ID, PULL_DT
```

### Provider ↔ BHID/NPI Mapping (Unity Catalog)
```sql
SELECT DISTINCT PROVIDER_ID, BH_ID AS BHID
FROM `ph-com-ai-us-prod-catalog-2553213839599380`.`kerendia_nba_3`.SOURCE_PROVIDER_BHID_NPI_MAPPING
```

---

## Promotional Channel Tables

### 1. Calls (BHO-level) — Notebook 13
**Source notebook:** `13_promotional_features_bho_calls` (ID: 2494728515032391)

**Snowflake Tables:**
- `CPH_DB_PROD.MODEL_V2.FACT_CALL` — Main calls fact table
- `CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF` — Maps SOURCE_CUST_ID → BAYER_CUST_ID
- `PHCDW.PHCDW_STG.MDM_STG_HCP_ACCT_AFFL` — Maps BH_ID (BHID) → BHO_ID

**Query Pattern (BHO-level calls):**
```sql
SELECT B.BAYER_CUST_ID AS BHO_ID, TO_DATE(A.CALL_DATE) AS MONTH_ID,
  CASE
    WHEN UPPER(CALL_REC_TYP_NM) LIKE '%BPH_FACE2FACE_SIG%' OR UPPER(CALL_REC_TYP_NM) LIKE 'FACE2FACE SIGNED' THEN 'F2F'
    WHEN UPPER(CALL_REC_TYP_NM) LIKE '%BPH_NON_FACE2FACE%' THEN 'PHONE'
    WHEN UPPER(CALL_REC_TYP_NM) IN ('BPH_GROUP_CALL_SIG', 'EVENT_VOD') THEN 'GROUP_CALL'
    WHEN UPPER(CALL_REC_TYP_NM) LIKE '%BPH_REMOTE%' THEN 'REMOTE_CALL'
    ELSE CALL_REC_TYP_NM
  END AS CHNNL_NM,
  CALL_TYP AS CALL_TYP_CD, CALL_DUR AS CALL_DURTN, CALL_PURPS AS CALL_PRPSE
FROM CPH_DB_PROD.MODEL_V2.FACT_CALL A
LEFT JOIN CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF B
  ON A.SOURCE_CUST_ID = B.SOURCE_CUST_ID
WHERE UPPER(STAT) = 'SUBMITTED_VOD'
  AND UPPER(DETL_PROD) = 'KERENDIA'
  AND BAYER_CUST_ID LIKE '%BHO%'
  AND BAYER_CUST_ID IS NOT NULL
  AND TO_DATE(A.CALL_DATE) >= '{lookback_start_date}'
  AND TO_DATE(A.CALL_DATE) <= '{lookback_end_date}'
```

**Key Columns:**
| Column | Description |
| --- | --- |
| CALL_DATE | Date of the call |
| CALL_REC_TYP_NM | Record type → maps to channel (F2F, PHONE, GROUP_CALL, REMOTE_CALL) |
| CALL_TYP (CALL_TYP_CD) | Call type code |
| CALL_DUR (CALL_DURTN) | Call duration |
| CALL_PURPS (CALL_PRPSE) | Call purpose |
| STAT | Status — filter on 'SUBMITTED_VOD' |
| DETL_PROD | Detail product — filter on 'KERENDIA' |

**Features Created:** Channel-based (F2F, Phone, Group Call, Remote Call), Call Type-based, Call Purpose-based, Call Duration

---

### 2. Calls (Non-BHO / BHID-level) — Notebook 25
**Source notebook:** `25_promotional_features_call` (ID: 2494728515032377)

**Snowflake Tables:**
- `CPH_DB_PROD.MODEL_V2.FACT_CALL`
- `CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF`

**Query Pattern (Non-BHO calls):**
```sql
SELECT B.BAYER_CUST_ID AS BHID, TO_DATE(A.CALL_DATE) AS MONTH_ID,
  CASE
    WHEN UPPER(CALL_REC_TYP_NM) LIKE '%BPH_FACE2FACE_SIG%' OR UPPER(CALL_REC_TYP_NM) LIKE 'FACE2FACE_SIG%' THEN 'F2F'
    WHEN UPPER(CALL_REC_TYP_NM) LIKE '%BPH_NON_FACE2FACE%' THEN 'PHONE'
    WHEN UPPER(CALL_REC_TYP_NM) IN ('BPH_GROUP_CALL_SIG', 'GROUP CALL SIGNED', 'EVENT_VOD') THEN 'GROUP_CALL'
    WHEN UPPER(CALL_REC_TYP_NM) LIKE '%BPH_REMOTE%' THEN 'REMOTE_CALL'
    ELSE CALL_REC_TYP_NM
  END AS CHNNL_NM,
  CALL_TYP AS CALL_TYP_CD, CALL_DUR AS CALL_DURTN, CALL_PURPS AS CALL_PRPSE, CALL_REC_TYP_NM
FROM CPH_DB_PROD.MODEL_V2.FACT_CALL A
LEFT JOIN CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF B
  ON A.SOURCE_CUST_ID = B.SOURCE_CUST_ID
WHERE UPPER(STAT) = 'SUBMITTED_VOD'
  AND UPPER(DETL_PROD) = 'KERENDIA'
  AND BAYER_CUST_ID NOT LIKE '%BHO%'
  AND BAYER_CUST_ID IS NOT NULL
  AND TO_DATE(A.CALL_DATE) >= '{LOOKBACK_START_DATE}'
  AND TO_DATE(A.CALL_DATE) <= '{LOOKBACK_END_DATE}'
```

**Note:** This is the same source as NB13 but filtered to non-BHO (individual HCP) calls (`NOT LIKE '%BHO%'`). Features are the same as NB13.

---

### 3. Speaker Programs — Notebook 14
**Source notebook:** `14_promotional_features_speaker_program` (ID: 2494728515032361)

**Snowflake Table:**
- `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM` — Speaker program / promotional event data

**Query Pattern:**
```sql
SELECT DISTINCT EVNT_ID, CUST_HCP_ID, ATND, EVNT_START_DATE, EVNT_FMT, EVNT_TYP, EVNT_TPIC_NM
FROM CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM
WHERE PROD_BRAND_NM = 'KERENDIA'
  AND CUST_HCP_ID LIKE '%BH%'
  AND CUST_HCP_ID IS NOT NULL
  AND CUST_HCP_ID NOT LIKE ''
  AND UPPER(ATND) = 'ATTENDED'
  AND TO_DATE(EVNT_START_DATE) >= '{LOOKBACK_START_DATE}'
  AND TO_DATE(EVNT_START_DATE) <= '{LOOKBACK_END_DATE}'
```

**Key Columns:**
| Column | Description |
| --- | --- |
| EVNT_ID | Event identifier |
| CUST_HCP_ID | HCP identifier (BHID) |
| ATND | Attendance status — filter on 'ATTENDED' |
| EVNT_START_DATE | Event start date |
| EVNT_FMT | Event format (Face-to-Face, Virtual, Webcast) |
| EVNT_TYP | Event type (Out of Office, Parent-Out Of Office, WebCon Out of Office) |
| EVNT_TPIC_NM | Event topic name (e.g., 'Introduction to KERENDIA (PP-FINE-US-0626-3)') |
| PROD_BRAND_NM | Product brand — filter on 'KERENDIA' |

**Features Created:** Event Format-based (F2F, Virtual, Webcast), Event Type-based, Topic Name-based

---

### 4. HQ Emails — Notebook 15
**Source notebook:** `15_promotional_features_HQ_Emails` (ID: 2494728515032345)

**Snowflake Table:**
- `PHCDW.PHCDW_CDM.HCP_EMAIL_LIST` — HQ email engagement data

**Query Pattern:**
```sql
SELECT EVENTDATE AS MONTH_ID, EVENTTYPE, BH_ID AS BHID
FROM PHCDW.PHCDW_CDM.HCP_EMAIL_LIST
WHERE UPPER(EMAILPRODUCTTYPE) LIKE '%KERENDIA%'
  AND BH_ID LIKE 'BH%'
  AND TO_DATE(EVENTDATE) >= '{LOOKBACK_START_DATE}'
  AND TO_DATE(EVENTDATE) <= '{LOOKBACK_END_DATE}'
```

**Key Columns:**
| Column | Description |
| --- | --- |
| EVENTDATE | Date of the email event |
| EVENTTYPE | Type of email event (Bounce, Clicked, Open, Sent, Unsubscribed) |
| BH_ID | HCP Bayer identifier (BHID) |
| EMAILPRODUCTTYPE | Email product type — filter on 'KERENDIA' |

**Features Created:** Counts by EVENTTYPE (TOTAL_BOUNCE, TOTAL_CLICKED, TOTAL_OPEN, TOTAL_SENT, TOTAL_UNSUBSCRIBED)

---

### 5. iRep Emails — Notebook 16
**Source notebook:** `16_promotional_features_irep` (ID: 2494728515032386)

**Snowflake Tables:**
- `CPH_DB_PROD.MODEL_V2.FACT_SENT_EMAIL` — iRep sent email fact table
- `CPH_DB_PROD.MODEL_V2.DIM_APPROVED_DOCUMENT` — Approved document dimension
- `PHCDW.PHCDW_STG.MDM_STG_HCP_XREF` — HCP cross-reference (SOURCE_CD IN ('K2_AC2','VAULT_CRM_AC2'))
- `PHCDW.PHCDW_STG.MDM_STG_HCP_PRFL` — HCP profile

**Query Pattern:**
```sql
SELECT DISTINCT
  B.BH_ID AS ACCT_IDNTFR,
  A.EMAIL_SNT_DATE AS EMAIL_SENT_DT,
  A.CLICKED AS EMAIL_CLCKD_FLG,
  A.OPENED AS EMAIL_OPND_FLG,
  A.STAT AS EMAIL_STATUS,
  DOC.NM AS APPRVD_DOC_NM
FROM CPH_DB_PROD.MODEL_V2.FACT_SENT_EMAIL A
LEFT JOIN CPH_DB_PROD.MODEL_V2.DIM_APPROVED_DOCUMENT DOC
  ON A.APV_EMAIL_TEMPLATE = DOC.APV_DOC_ID
LEFT OUTER JOIN (
    SELECT * FROM PHCDW.PHCDW_STG.MDM_STG_HCP_XREF
    WHERE SOURCE_CD IN ('K2_AC2','VAULT_CRM_AC2')
) B ON A.SOURCE_CUST_ID = B.SOURCE_ID
LEFT OUTER JOIN PHCDW.PHCDW_STG.MDM_STG_HCP_PRFL C
  ON B.BH_ID = C.BH_ID
WHERE A.EMAIL_SNT_DATE IS NOT NULL
  AND UPPER(DOC.NM) LIKE '%KERENDIA%'
  AND UPPER(EMAIL_STATUS) LIKE 'DELIVERED%'
  AND ACCT_IDNTFR NOT LIKE 'BHO%'
  AND TO_DATE(DATE_TRUNC('MONTH', A.EMAIL_SNT_DATE)) <= TO_DATE('{LOOKBACK_END_DATE}')
```

**Key Columns:**
| Column | Description |
| --- | --- |
| EMAIL_SNT_DATE | Email sent date |
| CLICKED (EMAIL_CLCKD_FLG) | Whether email was clicked (1/0) |
| OPENED (EMAIL_OPND_FLG) | Whether email was opened (1/0) |
| STAT (EMAIL_STATUS) | Email delivery status — filter on 'Delivered' |
| DOC.NM (APPRVD_DOC_NM) | Approved document name — filter on 'KERENDIA' |

**Features Created:** Email Delivered flag, Email Opened flag, Email Clicked flag, by Approved Doc Name

---

### 6. Samples — Notebook 17
**Source notebook:** `17_promotional_features_samples` (ID: 2494728515032373)

**Snowflake Table:**
- `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER` — Kerendia samples shipped/dropped

**Query Pattern:**
```sql
SELECT DISTINCT BHID, SMPLE_CALL_DT, SMPLE_CALL_DT AS MONTH_ID,
  SMPLE_CALL_NM, UPPER(SMPLE_NM) AS UPPER_SMPLE_NM, SMPLE_QTY, SAMPLE_FLAG
FROM CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER
```

**Key Columns:**
| Column | Description |
| --- | --- |
| BHID | HCP Bayer identifier |
| SMPLE_CALL_DT | Sample call date |
| SMPLE_CALL_NM | Sample call name |
| SMPLE_NM (UPPER_SMPLE_NM) | Sample name (e.g., KERENDIA 10MG, KERENDIA 20MG) |
| SMPLE_QTY | Sample quantity |
| SAMPLE_FLAG | Shipped/Dropped flag |

**Sample Categories:**
- KERENDIA 20MG
- KERENDIA 10MG BRC
- KERENDIA 20MG BRC
- KERENDIA SAMPLING KIT BRC
- KERENDIA SAMPLE HOUSING BOX BRC
- KERENDIA 10MG

**Features Created:** Sample Name-based (10mg vs 20mg), total samples, by dosage/quantity

---

### 7. ClickStream — Notebook 18
**Source notebook:** `18_promotional_ClickStream_features` (ID: 2494728515032379)

**Snowflake Tables:**
- `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM` — Clickstream fact data
- `CPH_DB_PROD.MODEL_V2.FACT_CALL` — Calls fact (for joining call IDs)
- `CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF` — Customer mapping

**ClickStream Query:**
```sql
SELECT DISTINCT CALL_ID, BAYER_HCP_ID AS BHID, DATE_ID, USAGE_DUR, PRESN_DUR
FROM CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM
WHERE BAYER_PROD_NM = 'KERENDIA'
  AND DATE_ID <= {LOOKBACK_END_DATE}
```

**Calls for ClickStream (to get valid CALL_IDs):**
```sql
SELECT DISTINCT BAYER_CUST_ID AS BHID, CALL_ID, A.STAT AS CALL_STATUS
FROM CPH_DB_PROD.MODEL_V2.FACT_CALL A
LEFT JOIN CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF B
  ON A.SOURCE_CUST_ID = B.SOURCE_CUST_ID
WHERE UPPER(STAT) = 'SUBMITTED_VOD'
  AND UPPER(DETL_PROD) = 'KERENDIA'
  AND BAYER_CUST_ID NOT LIKE '%BHO%'
  AND BAYER_CUST_ID IS NOT NULL
```

**Key Columns:**
| Column | Description |
| --- | --- |
| CALL_ID | Links to FACT_CALL |
| BAYER_HCP_ID (BHID) | HCP Bayer identifier |
| DATE_ID | Date identifier (yyyyMMdd format) |
| USAGE_DUR | Total usage duration |
| PRESN_DUR | Presentation duration |
| BAYER_PROD_NM | Product name — filter on 'KERENDIA' |

**Processing:** Deduplication by CALL_ID (keeping max USAGE_DUR, PRESN_DUR via window function), then joined with valid submitted calls.

**Features Created:** MAX_USAGE_DUR, MAX_PRESN_DUR by record type (Non-Face2Face, Face2Face, Remote Meeting, Remote Group Meeting, Group Call)

---

### 8. IQVIA Channel — Notebook 23
**Source notebook:** `23_IQVIA_channel_features` (ID: 2494728515032344)

**Delta Volume Path:**
```
/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/kerendia_nba_3_0_hcp_model_channel_23
```

**Key Columns:**
| Column | Description |
| --- | --- |
| PROVIDER_ID | Provider identifier |
| SVC_DT | Service date |
| CHANNEL_CODE | Channel code: A=Atypical, L=Long Term Care, M=Mail, R=Retail |

**Features Created:** Claim counts pivoted by CHANNEL_CODE → `Channel_A`, `Channel_L`, `Channel_M`, `Channel_R`

**Output Path:**
```
/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_0_hcp_model_channel_feature_for_inference
```

---

### 9. Digital / MMX (Paid Search, Display, etc.) — Notebook 24
**Source notebook:** `24_Features_Digital` (ID: 2494728515032382)

**Snowflake Table:**
- `PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB` — MMX final combined aggregated table (primary, current)

**Query Pattern:**
```sql
SELECT NPI_NUMBER, SVC_DT_M, UPPER(CHANNEL) AS CHANNEL,
  UPPER(SRC_SYS_CD) AS SRC_SYS_CD, TACTIC_NAME,
  SUM(DEEP_ENGAGEMENT) AS DEEP_ENGAGEMENT,
  SUM(LIGHT_ENGAGEMENT) AS LIGHT_ENGAGEMENT,
  SUM(TOTAL_ENGAGEMENT) AS TOTAL_ENGAGEMENT,
  SUM(EXPOSURE) AS EXPOSURE
FROM (
  SELECT NPI_NUM AS NPI_NUMBER, DATE_ACT,
    DATE_TRUNC('MONTH', DATE_ACT) AS SVC_DT_M,
    CHANNEL, SRC_SYS_CD, TACTIC_NAME, BRND_NM,
    DEEP_ENGAGEMENT, LIGHT_ENGAGEMENT, TOTAL_ENGAGEMENT, EXPOSURE
  FROM PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB
  WHERE UPPER(BRND_NM) = 'KERENDIA'
    AND NPI_NUM IS NOT NULL
    AND DATE_TRUNC('MONTH', DATE_ACT) >= '{digital_start}'
)
GROUP BY NPI_NUMBER, SVC_DT_M, CHANNEL, SRC_SYS_CD, TACTIC_NAME
ORDER BY NPI_NUMBER, SVC_DT_M DESC, CHANNEL, SRC_SYS_CD, TACTIC_NAME
```

**Key Columns:**
| Column | Description |
| --- | --- |
| NPI_NUM (NPI_NUMBER) | NPI number of the HCP |
| DATE_ACT | Activity date |
| SVC_DT_M | Service date truncated to month |
| CHANNEL | Channel (HQ_EMAILS, IREP_EMAILS, CALLS, SAMPLES, BANNER, CTV, etc.) |
| SRC_SYS_CD | Source system code |
| TACTIC_NAME | Tactic name |
| BRND_NM | Brand name — filter on 'KERENDIA' |
| DEEP_ENGAGEMENT | Deep engagement count |
| LIGHT_ENGAGEMENT | Light engagement count |
| TOTAL_ENGAGEMENT | Total engagement count |
| EXPOSURE | Exposure count |

**Channel Values:** HQ_EMAILS, IREP_EMAILS, CALLS (excluded), SAMPLES (excluded), BANNER, CTV, DISPLAY, SEARCH, VIDEO, and others.

**Tactic Mapping:**
| Raw Tactic | Mapped Name |
| --- | --- |
| Banner (or contains "Banner") | BANNER_TACTIC |
| CTV | CTV_TACTIC (discontinued) |
| HQ Email | HQ_EMAIL_TACTIC |
| DocNews | DOCNEWS_TACTIC |
| Video | VIDEO_TACTIC |
| IRep Email | IREP_EMAIL_TACTIC |
| Monograph Message | MONOGRAPH_MESSAGE_TACTIC |
| DocSpot | DOCSPOT_TACTIC |
| Brand Alert | BRAND_ALERT_TACTIC |
| DocAlert | DOC_ALERT_TACTIC |
| Email | EMAIL_TACTIC |
| Email Alert | EMAIL_ALERT_TACTIC |
| NativeVideo | NATIVEVIDEO_TACTIC |
| FormularyOne | FORMULARY_TACTIC |
| (all others) | OTHER_TACTIC |

**Note:** CALLS and SAMPLES channels are excluded from the digital features (they are handled separately in NB13/25 and NB17).

**Features Created:** Pivoted by CHANNEL (engagement metrics per channel), by SRC_SYS_CD, and by TACTIC_NAME.

---

## Summary Table of All Snowflake Source Tables

| Channel | Notebook | Snowflake Table(s) | Key Filter |
| --- | --- | --- | --- |
| Calls (BHO) | 13 | `CPH_DB_PROD.MODEL_V2.FACT_CALL` + `MAP_CUSTOMER_XREF` | DETL_PROD='KERENDIA', BHO-level |
| Calls (BHID) | 25 | `CPH_DB_PROD.MODEL_V2.FACT_CALL` + `MAP_CUSTOMER_XREF` | DETL_PROD='KERENDIA', non-BHO |
| Speaker Programs | 14 | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM` | PROD_BRAND_NM='KERENDIA' |
| HQ Emails | 15 | `PHCDW.PHCDW_CDM.HCP_EMAIL_LIST` | EMAILPRODUCTTYPE LIKE '%KERENDIA%' |
| iRep Emails | 16 | `CPH_DB_PROD.MODEL_V2.FACT_SENT_EMAIL` + `DIM_APPROVED_DOCUMENT` + `MDM_STG_HCP_XREF` | DOC.NM LIKE '%KERENDIA%' |
| Samples | 17 | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER` | (Kerendia-specific table) |
| ClickStream | 18 | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM` + `FACT_CALL` | BAYER_PROD_NM='KERENDIA' |
| IQVIA Channel | 23 | Delta volume (pre-queried) | Channel codes A/L/M/R |
| Digital/MMX | 24 | `PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB` | BRND_NM='KERENDIA' |

---

## Source Notebooks

All notebooks are in:
`/Workspace/Users/saurabh.modi.ext@bayer.com/NBA 3.1 Dev - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`

| Notebook | ID | Channel |
| --- | --- | --- |
| 13_promotional_features_bho_calls | 2494728515032391 | Calls (BHO-level) |
| 14_promotional_features_speaker_program | 2494728515032361 | Speaker Programs |
| 15_promotional_features_HQ_Emails | 2494728515032345 | HQ Emails |
| 16_promotional_features_irep | 2494728515032386 | iRep Emails |
| 17_promotional_features_samples | 2494728515032373 | Samples |
| 18_promotional_ClickStream_features | 2494728515032379 | ClickStream |
| 23_IQVIA_channel_features | 2494728515032344 | IQVIA Channel |
| 24_Features_Digital | 2494728515032382 | Digital / MMX |
| 25_promotional_features_call | 2494728515032377 | Calls (Non-BHO / BHID-level) |

---

## Tips for EDA

1. **Always filter by Kerendia:** Each table has a brand/product filter — ensure it is applied.
2. **Date range:** Use `LOOKBACK_START_DATE` and `LOOKBACK_END_DATE` from the cohort anchor dates table to scope queries to the correct period.
3. **ID mapping:** Snowflake tables use different ID systems (BHO_ID, BHID, NPI_NUMBER, PROVIDER_ID). Use the NPI-BHID mapping table to translate between them.
4. **BHO vs BHID:** NB13 uses BHO-level (account) calls, NB25 uses BHID-level (individual HCP) calls. Be aware of which level you need.
5. **Digital channel exclusions:** In NB24, CALLS and SAMPLES channels are excluded since they are handled by dedicated notebooks (NB13/25 and NB17).
6. **Snowflake access:** Use `Get_Data_Snowflakes(query)` function after running the `00_connection` helper notebook.
