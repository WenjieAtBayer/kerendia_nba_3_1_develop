# Lab Claims Query Execution Template

All IQVIA LAAD lab queries run against **Snowflake** (not Databricks SQL). They **cannot** be
executed as standalone SQL. They must be wrapped in `Get_Data_Snowflakes(query)` after importing the
connection notebook.

## Required Setup (mandatory first cells)

### Ops Pipeline (production)
```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```

### Dev Pipeline (development)
```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.1 Dev - Pipeline/00_Helper_Notebooks/00_connection"
```

### What the connection notebook provides

1. **`snowflake-connector-python`** — installed via `%pip install`
2. **Snowflake credentials** — from Databricks secrets scope `US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`
3. **`Get_Data_Snowflakes(query, Schema, Role)`** — returns a PySpark DataFrame
4. **Common library imports** — pandas, numpy, pyspark.sql.functions, etc.

## Lab-Specific Query Execution Patterns

### Pattern 1: Patient-Level (12M & First Occurrence)

```python
# Cell 1 — Connection
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```

```python
# Cell 2 — Config
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config"
```

```python
# Cell 3 — Query GFR/UACR lab results (median per patient-provider-date)
query = '''
    SELECT PROVIDER_ID, PATIENT_ID, SVC_DT, TEST_TYPE,
      MEDIAN(LCL_LAB_TEST_VAL_TXT_FLOAT) AS MEDIAN_TEST_RESULT
    FROM (
      SELECT DISTINCT
        CAST(PROVIDER_ID AS VARCHAR(64)) AS PROVIDER_ID,
        CAST(CAST(PATIENT_ID AS INT) AS VARCHAR(64)) AS PATIENT_ID,
        SVC_DT_STD AS SVC_DT, TEST_TYPE,
        TRY_TO_DOUBLE(TRIM(LCL_LAB_TEST_VAL_TXT)) AS LCL_LAB_TEST_VAL_TXT_FLOAT
      FROM (
        SELECT *,
          CASE WHEN UPPER(LCL_LAB_TEST_NM_CLEAN) LIKE '%GFR%'
                 OR UPPER(LCL_LAB_TEST_NM_CLEAN) LIKE '%GLOMERULAR%' THEN 'GFR'
               WHEN UPPER(LCL_LAB_TEST_NM_CLEAN) LIKE '%ALB%'
                 OR UPPER(LCL_LAB_TEST_NM_CLEAN) LIKE '%RATIO%' THEN 'UACR'
               ELSE 'OTHER' END AS TEST_TYPE,
          CASE WHEN SVC_DT LIKE '%/%/%' THEN TO_DATE(SVC_DT,'MM/DD/YYYY')
               ELSE TO_DATE(LEFT(SVC_DT,9),'DDMONYYYY') END AS SVC_DT_STD
        FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_QUEST_TO_LAAD_HIST
        WHERE REGEXP_LIKE(PATIENT_ID, '^[0-9]+$')
          AND LCL_LAB_TEST_VAL_TXT IS NOT NULL
          AND TRIM(LCL_LAB_TEST_VAL_TXT) NOT ILIKE '%-%'
          AND TRIM(LCL_LAB_TEST_VAL_TXT) NOT ILIKE '%>%'
          AND TRIM(LCL_LAB_TEST_VAL_TXT) NOT ILIKE '%<%'
          AND REGEXP_LIKE(TRIM(LCL_LAB_TEST_VAL_TXT), '^[0-9]+(\\.[0-9]+)?$')
      ) lab1
      LEFT JOIN PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRVDR dct
        ON lab1.NPI_ID = dct.NPI_NUMBER
      WHERE UPPER(REPLACE(LCL_LAB_TEST_RSLT_UOM_CD_CLEAN, ' ','')) IN
        ('ML/MIN/1.73M2','MCG/MGCREAT','MG/G{CREAT}','MG/GCREAT','MG/GCR')
        AND PRIMARY_SPECIALTY_CODE IN ('FM','FPG','GP','GPM','IFP','IM','IMG','IPM','NRP','PHA')
        AND TEST_TYPE <> 'OTHER'
    ) LAB
    GROUP BY 1, 2, 3, 4
'''

df_lab = Get_Data_Snowflakes(query)

# Post-filter to lookback window
df_lab = df_lab.filter(col("SVC_DT") <= lit(lookback_end))
df_lab.display()
```

### Pattern 2: HCP-Level Lab_03 (CKD Staging — Text Labels)

```python
# Cell 3 — Lab_03: CKD staging with text STAGE column
query = """
    WITH AGGREGATED_LAB_RESULT AS (
      SELECT DISTINCT SVC_DT, NPI_ID, TEST_TYPE,
        CAST(CAST(PATIENT_ID AS INT) AS VARCHAR(64)) AS PATIENT_ID,
        MEDIAN(LCL_LAB_TEST_VAL_TXT) AS MEDIAN_TEST_RESULT
      FROM (
        SELECT DISTINCT
          CASE WHEN svc_dt LIKE '%/%/%' THEN TO_DATE(svc_dt, 'MM/DD/YYYY')
               ELSE TO_DATE(LEFT(svc_dt, 9), 'DDMONYYYY') END AS SVC_DT,
          NPI_ID, TEST_TYPE,
          CAST(CAST(PATIENT_ID AS INT) AS VARCHAR(64)) AS PATIENT_ID,
          LCL_LAB_TEST_VAL_TXT
        FROM (
          SELECT *,
            CASE WHEN UPPER(LCL_LAB_TEST_NM) LIKE '%GFR%'
                   OR UPPER(LCL_LAB_TEST_NM) LIKE '%GLOMERULAR%' THEN 'GFR'
                 WHEN UPPER(LCL_LAB_TEST_NM) LIKE '%ALB%'
                   OR UPPER(LCL_LAB_TEST_NM) LIKE '%RATIO%' THEN 'UACR'
                 ELSE 'OTHER' END AS TEST_TYPE,
            CASE WHEN SVC_DT LIKE '%/%/%' THEN TO_DATE(SVC_DT,'MM/DD/YYYY')
                 ELSE TO_DATE(LEFT(SVC_DT,9),'DDMONYYYY') END AS SVC_DT_STD
          FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_QUEST_TO_LAAD_HIST
          WHERE LCL_LAB_TEST_VAL_TXT IS NOT NULL
            AND TRIM(LCL_LAB_TEST_VAL_TXT) NOT ILIKE '%-%'
            AND TRIM(LCL_LAB_TEST_VAL_TXT) NOT ILIKE '%>%'
            AND TRIM(LCL_LAB_TEST_VAL_TXT) NOT ILIKE '%<%'
            AND REGEXP_LIKE(TRIM(LCL_LAB_TEST_VAL_TXT), '^[0-9]+(\\.[0-9]+)?$')
        ) LAB1
        LEFT JOIN PHCDW.PHCDW_STG_CAR.STG_IQVIA_LAAD_DIM_PROVIDER DCT
          ON LAB1.NPI_ID = DCT.NPI_NUMBER
        WHERE UPPER(REPLACE(LCL_LAB_TEST_RSLT_UOM_CD,' ','')) IN
          ('ML/MIN/1.73M2','MCG/MGCREAT','MG/GCREAT','MG/GCR','MG/G {CREAT}')
          AND PRIMARY_SPECIALTY_CODE IN ('FM','FPG','GP','GPM','IFP','IM','IMG','IPM','NRP','PHA')
          AND TEST_TYPE <> 'OTHER'
          AND LCL_LAB_TEST_VAL_TXT REGEXP '[0-9]+'
          AND NPI_ID IS NOT NULL
      ) LAB
      GROUP BY SVC_DT, NPI_ID, PATIENT_ID, TEST_TYPE
    )
    SELECT SVC_DT, NPI_ID AS NPI_NUMBER, PATIENT_ID, TEST_TYPE, MEDIAN_TEST_RESULT,
      CASE
        WHEN TEST_TYPE = 'GFR'  AND MEDIAN_TEST_RESULT <15 THEN 'CHRONIC KIDNEY DISEASE, STAGE 5'
        WHEN TEST_TYPE = 'GFR'  AND MEDIAN_TEST_RESULT >=15 AND MEDIAN_TEST_RESULT <30 THEN 'CHRONIC KIDNEY DISEASE, STAGE 4 (SEVERE)'
        WHEN TEST_TYPE = 'GFR'  AND MEDIAN_TEST_RESULT >=30 AND MEDIAN_TEST_RESULT <60 THEN 'CHRONIC KIDNEY DISEASE, STAGE 3 (MODERATE)'
        WHEN TEST_TYPE = 'GFR'  AND MEDIAN_TEST_RESULT >=60 AND MEDIAN_TEST_RESULT <90 THEN 'CHRONIC KIDNEY DISEASE, STAGE 2 (MILD)'
        WHEN TEST_TYPE = 'GFR'  AND MEDIAN_TEST_RESULT >=90 AND MEDIAN_TEST_RESULT <=150 THEN 'CHRONIC KIDNEY DISEASE, STAGE 1'
        WHEN TEST_TYPE = 'UACR' AND MEDIAN_TEST_RESULT <30 THEN 'A1'
        WHEN TEST_TYPE = 'UACR' AND MEDIAN_TEST_RESULT >=30 AND MEDIAN_TEST_RESULT <300 THEN 'A2'
        WHEN TEST_TYPE = 'UACR' AND MEDIAN_TEST_RESULT >=300 THEN 'A3'
        WHEN MEDIAN_TEST_RESULT IS NULL THEN NULL
        ELSE 'IGNORE'
      END AS STAGE
    FROM AGGREGATED_LAB_RESULT
    WHERE STAGE <> 'IGNORE'
    ORDER BY SVC_DT, NPI_ID, PATIENT_ID, TEST_TYPE, STAGE
"""

df_lab = Get_Data_Snowflakes(query)
df_lab = df_lab.filter(col("SVC_DT") <= date_end)
df_lab.display()
```

### Pattern 3: HCP-Level Lab_04 (Cleaned Columns Variant)

Same as Pattern 2, but uses **`LCL_LAB_TEST_RSLT_UOM_CD_CLEAN`** instead of `LCL_LAB_TEST_RSLT_UOM_CD` and adds `REGEXP_LIKE(PATIENT_ID, '^[0-9]+$')` validation. The SQL is identical in structure — only change those two column/filter differences from Pattern 2.

### Pattern 4: HCP-Level Pat Journey Lab (Numeric Staging)

```python
# Cell 3 — Pat Journey Lab: numeric GFR_STAGE and UACR_STAGE
query = """
    SELECT PATIENT_ID, SVC_DT_STD AS DATE, NPI_ID AS NPI_NUMBER, TEST_TYPE,
      MEDIAN(LCL_LAB_TEST_VAL_TXT_FLOAT) AS MEDIAN_TEST_RESULT,
      CASE WHEN TEST_TYPE = 'GFR' AND MEDIAN_TEST_RESULT <15 THEN 5
           WHEN TEST_TYPE = 'GFR' AND MEDIAN_TEST_RESULT >=15 AND MEDIAN_TEST_RESULT <30 THEN 4
           WHEN TEST_TYPE = 'GFR' AND MEDIAN_TEST_RESULT >=30 AND MEDIAN_TEST_RESULT <60 THEN 3
           WHEN TEST_TYPE = 'GFR' AND MEDIAN_TEST_RESULT >=60 AND MEDIAN_TEST_RESULT <90 THEN 2
           WHEN TEST_TYPE = 'GFR' AND MEDIAN_TEST_RESULT >=90 AND MEDIAN_TEST_RESULT <=150 THEN 1
           WHEN TEST_TYPE = 'UACR' THEN NULL
           ELSE 0 END AS GFR_STAGE,
      CASE WHEN TEST_TYPE = 'UACR' AND MEDIAN_TEST_RESULT <30 THEN 1
           WHEN TEST_TYPE = 'UACR' AND MEDIAN_TEST_RESULT >=30 AND MEDIAN_TEST_RESULT <300 THEN 2
           WHEN TEST_TYPE = 'UACR' AND MEDIAN_TEST_RESULT >=300 THEN 3
           WHEN MEDIAN_TEST_RESULT IS NULL THEN NULL
           WHEN TEST_TYPE = 'GFR' THEN NULL
           ELSE 0 END AS UACR_STAGE
    FROM (
      SELECT DISTINCT
        CAST(CAST(PATIENT_ID AS INT) AS VARCHAR(64)) AS PATIENT_ID,
        NPI_ID, SVC_DT_STD, TEST_TYPE,
        TRY_TO_DOUBLE(TRIM(LCL_LAB_TEST_VAL_TXT)) AS LCL_LAB_TEST_VAL_TXT_FLOAT
      FROM (
        SELECT *,
          CASE WHEN UPPER(LCL_LAB_TEST_NM_CLEAN) LIKE '%GFR%'
                 OR UPPER(LCL_LAB_TEST_NM_CLEAN) LIKE '%GLOMERULAR%' THEN 'GFR'
               WHEN UPPER(LCL_LAB_TEST_NM_CLEAN) LIKE '%ALB%'
                 OR UPPER(LCL_LAB_TEST_NM_CLEAN) LIKE '%RATIO%' THEN 'UACR'
               ELSE 'OTHER' END AS TEST_TYPE,
          CASE WHEN SVC_DT LIKE '%/%/%' THEN TO_DATE(SVC_DT,'MM/DD/YYYY')
               ELSE TO_DATE(LEFT(SVC_DT,9),'DDMONYYYY') END AS SVC_DT_STD
        FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_QUEST_TO_LAAD_HIST
        WHERE REGEXP_LIKE(PATIENT_ID, '^[0-9]+$')
          AND LCL_LAB_TEST_VAL_TXT IS NOT NULL
          AND TRIM(LCL_LAB_TEST_VAL_TXT) NOT ILIKE '%-%'
          AND TRIM(LCL_LAB_TEST_VAL_TXT) NOT ILIKE '%>%'
          AND TRIM(LCL_LAB_TEST_VAL_TXT) NOT ILIKE '%<%'
          AND REGEXP_LIKE(TRIM(LCL_LAB_TEST_VAL_TXT), '^[0-9]+(\\.[0-9]+)?$')
      ) lab1
      LEFT JOIN PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRVDR dct
        ON lab1.NPI_ID = dct.NPI_NUMBER
      WHERE UPPER(REPLACE(LCL_LAB_TEST_RSLT_UOM_CD_CLEAN, ' ','')) IN
        ('ML/MIN/1.73M2','MCG/MGCREAT','MG/GCREAT','MG/GCR','MG/G{CREAT}')
        AND PRIMARY_SPECIALTY_CODE IN ('FM','FPG','GP','GPM','IFP','IM','IMG','IPM','NRP','PHA')
        AND TEST_TYPE <> 'OTHER'
        AND SVC_DT_STD >= '2021-11-30'
        AND NPI_ID IS NOT NULL
    ) LAB
    GROUP BY 1, 2, 3, 4
"""

df_lab = Get_Data_Snowflakes(query)
df_lab = df_lab.filter(col("DATE") <= date_end)
df_lab.display()
```

## Optional Config Import

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config"
```

Provides: `lookback_start`, `lookback_end`, `date_end`, and all file paths.

## Lab-Specific SQL Patterns

### Date parsing (always required)
```sql
-- SVC_DT is text in two formats; must parse
CASE WHEN SVC_DT LIKE '%/%/%' THEN TO_DATE(SVC_DT,'MM/DD/YYYY')
     ELSE TO_DATE(LEFT(SVC_DT,9),'DDMONYYYY') END AS SVC_DT_STD
```

### Numeric value extraction
```sql
-- Raw values are text; cast to double
TRY_TO_DOUBLE(TRIM(LCL_LAB_TEST_VAL_TXT)) AS LCL_LAB_TEST_VAL_TXT_FLOAT
```

### MEDIAN aggregation
```sql
-- Snowflake-native; not available in Databricks SQL
MEDIAN(LCL_LAB_TEST_VAL_TXT_FLOAT) AS MEDIAN_TEST_RESULT
```

### Two column name variants
```sql
-- Uncleaned (used in Lab_03):
LCL_LAB_TEST_NM, LCL_LAB_TEST_RSLT_UOM_CD

-- Cleaned (used in Patient-level, Lab_04, Pat Journey Lab):
LCL_LAB_TEST_NM_CLEAN, LCL_LAB_TEST_RSLT_UOM_CD_CLEAN
```

### Two provider dimension tables
```sql
-- Lab_03 uses:
PHCDW.PHCDW_STG_CAR.STG_IQVIA_LAAD_DIM_PROVIDER  -- join ON NPI_ID = NPI_NUMBER

-- Patient-level & Pat Journey Lab use:
PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRVDR   -- join ON NPI_ID = NPI_NUMBER
```

## Important Constraints

1. **Never execute these queries via `spark.sql()` or Databricks SQL endpoints** — tables live in Snowflake.
2. **Always use `Get_Data_Snowflakes(query)`** to execute.
3. **The connection notebook must be `%run` before any query.**
4. **`MEDIAN()` is Snowflake-native** — not available in Databricks SQL. Use `percentile_approx()` if rewriting for Spark.
5. **Date column is text** — always parse `SVC_DT` before filtering or aggregating.
6. **Data quality filters are mandatory** — raw values contain non-numeric entries, ranges, and symbols.
7. **Pre-materialized Delta outputs** exist for all 4 queries (see SKILL.md) — prefer reading those to avoid re-querying Snowflake.
