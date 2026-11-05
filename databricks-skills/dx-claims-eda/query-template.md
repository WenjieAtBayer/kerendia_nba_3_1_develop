# DX Claims Query Execution Template

All IQVIA LAAD DX claims queries run against **Snowflake** (not Databricks SQL). They **cannot** be
executed as standalone SQL. They must be wrapped in `Get_Data_Snowflakes(query)` after importing the
connection notebook.

## Required Setup (mandatory first cells)

Every notebook or Python file that queries IQVIA LAAD tables must begin with this connection import.
There are two versions depending on the pipeline branch:

### Ops Pipeline (production)
```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```

### Dev Pipeline (development)
```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.1 Dev - Pipeline/00_Helper_Notebooks/00_connection"
```

### What the connection notebook provides

1. **`snowflake-connector-python`** — installed via `%pip install` (auto-restarts kernel if needed)
2. **Snowflake credentials** — loaded from Databricks secrets scope `US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`:
   - `snowflake-private-key`
   - `snowflake-private-key-passphrase`
   - `snowflake-user`
   - `snowflake-account`
3. **`Get_Data_Snowflakes(query, Schema, Role)`** function — executes a SQL query against Snowflake and returns a PySpark DataFrame
4. **`sfOptionscdpread` / `sfOptionscdpwrite`** — Snowflake connection option dicts for direct `spark.read`/`spark.write` operations
5. **Common library imports** — pandas, numpy, pyspark.sql.functions, sklearn, matplotlib, etc.

## `Get_Data_Snowflakes` Function Signature

```python
def Get_Data_Snowflakes(
    query,
    Schema="PHCDW_CDM",
    Role="BAY_CPH_CDP_PROD_CR_US_EAST_1_MVXPF_MVXPF"
):
    """
    Executes a SQL query against the Bayer PHCDW Snowflake instance
    and returns the result as a PySpark DataFrame.

    Args:
        query (str): SQL query string (Snowflake SQL dialect)
        Schema (str): Snowflake schema, default "PHCDW_CDM"
        Role (str): Snowflake role for access control

    Returns:
        pyspark.sql.DataFrame
    """
```

**Snowflake connection details:**
- URL: `bayer_cphcdp_prod.us-east-1.snowflakecomputing.com:443`
- Database: `PHCDW`
- Warehouse: `PROD_CYRUS_BI_WH`
- Auth: PEM private key (loaded from secrets)

## DX-Specific Query Execution Patterns

When generating DX claims code, always produce notebook cells with one of these patterns:

### Pattern 1: Patient-Level DX Query (12M & First Occurrence)

```python
# Cell 1 — Connection (run once per session)
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```

```python
# Cell 2 — Config (for date parameters)
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config"
```

```python
# Cell 3 — Query DX claims with CKD diagnosis filter
dx_query = f"""
    SELECT DISTINCT CLAIM_ID, PATIENT_ID, SERVICE_DATE AS SVC_DT,
      DX_CLAIMS.DIAGNOSIS_CODE, DX_CODES.DIAGNOSIS_DESCRIPTION,
      COALESCE(PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID) AS PROVIDER_ID,
      PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID,
      PAYER_PLAN_ID, DX_CLAIMS.ICD_VERSION_TYPE
    FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX DX_CLAIMS
    INNER JOIN (
      SELECT DISTINCT DIAGNOSIS_CODE, DIAGNOSIS_DESCRIPTION, ICD_VERSION_TYPE
      FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_DIAG
    ) DX_CODES
      ON DX_CLAIMS.DIAGNOSIS_CODE = DX_CODES.DIAGNOSIS_CODE
    WHERE SVC_DT <= '{lookback_end}'
      AND DIAGNOSIS_DESCRIPTION IN (
        'CHRONIC KIDNEY DISEASE, STAGE 3 UNSPECIFIED',
        'END STAGE RENAL DISEASE',
        -- ... see SKILL.md for full 17-value list
      )
"""

df_dx = Get_Data_Snowflakes(dx_query)
df_dx.display()
```

### Pattern 2: Patient-Level DX Query (All Events — broad)

```python
# Cell 3 — Query all DX claims within lookback window
dx_query = f"""
    SELECT DISTINCT CLAIM_ID, PATIENT_ID, SERVICE_DATE AS SVC_DT,
      DX_CLAIMS.DIAGNOSIS_CODE, DX_CODES.DIAGNOSIS_DESCRIPTION,
      COALESCE(PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID) AS PROVIDER_ID,
      PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID,
      PAYER_PLAN_ID, DX_CLAIMS.ICD_VERSION_TYPE
    FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX DX_CLAIMS
    INNER JOIN (
      SELECT DISTINCT DIAGNOSIS_CODE, DIAGNOSIS_DESCRIPTION, ICD_VERSION_TYPE
      FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_DIAG
    ) DX_CODES
      ON DX_CLAIMS.DIAGNOSIS_CODE = DX_CODES.DIAGNOSIS_CODE
    WHERE SVC_DT >= '{lookback_start}' AND SVC_DT <= '{lookback_end}'
"""

df_dx = Get_Data_Snowflakes(dx_query)

# Post-filter to prevalent events
import pandas as pd
dx_event_list = pd.read_csv("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/feature_selection/Kerendia NBA 3.0 - Dx Event List.csv")
df_dx = df_dx.filter(col("DIAGNOSIS_DESCRIPTION").isin(dx_event_list["EVENT_NAME"].tolist()))
df_dx.display()
```

### Pattern 3: Patient-Level DX Query (Hospitalization only)

```python
# Cell 3 — Query hospital-only DX claims
dx_query = f"""
    SELECT DISTINCT CLAIM_ID, PATIENT_ID, SERVICE_DATE AS SVC_DT,
      DX_CLAIMS.DIAGNOSIS_CODE, DX_CODES.DIAGNOSIS_DESCRIPTION,
      COALESCE(PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID) AS PROVIDER_ID,
      PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID,
      PAYER_PLAN_ID, DX_CLAIMS.ICD_VERSION_TYPE
    FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX DX_CLAIMS
    INNER JOIN (
      SELECT DISTINCT DIAGNOSIS_CODE, DIAGNOSIS_DESCRIPTION, ICD_VERSION_TYPE
      FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_DIAG
    ) DX_CODES
      ON DX_CLAIMS.DIAGNOSIS_CODE = DX_CODES.DIAGNOSIS_CODE
    WHERE DATA_SOURCE = 'HX'
      AND SVC_DT >= '{lookback_start}' AND SVC_DT <= '{lookback_end}'
"""

df_dx_hosp = Get_Data_Snowflakes(dx_query)
df_dx_hosp.display()
```

### Pattern 4: HCP-Level DX_03 (CKD Staging)

```python
# Cell 3 — Query CKD staging by provider (full ICD code list)
query = f"""
    SELECT DISTINCT PATIENT_ID, SERVICE_DATE AS SVC_DT,
      CD.DIAGNOSIS_DESCRIPTION AS Category,
      CASE
        WHEN CATEGORY = 'CHRONIC KIDNEY DISEASE, STAGE 1' THEN 1
        WHEN CATEGORY = 'CHRONIC KIDNEY DISEASE, STAGE 2 (MILD)' THEN 2
        WHEN CATEGORY = 'CHRONIC KIDNEY DISEASE, STAGE 3 (MODERATE)' THEN 3
        WHEN CATEGORY = 'CHRONIC KIDNEY DISEASE, STAGE 4 (SEVERE)' THEN 4
        WHEN CATEGORY LIKE '%STAGE 5%' THEN 5
        ELSE 0
      END AS DX_STAGE,
      NPI_NUMBER,
      COALESCE(PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID) AS PROVIDER_ID,
      PROVIDER_RENDERING_ID, PROVIDER_REFERRING_ID,
      PRIMARY_SPECIALTY_CODE
    FROM (
      SELECT C.NPI_NUMBER, A.PATIENT_ID, A.SERVICE_DATE,
             A.PROVIDER_RENDERING_ID, A.PROVIDER_REFERRING_ID,
             A.DIAGNOSIS_CODE, B.PATIENT_BIRTH_YEAR, C.PRIMARY_SPECIALTY_CODE
      FROM (
        SELECT PATIENT_ID, CLAIM_ID, DIAGNOSIS_CODE, SERVICE_DATE,
               PROVIDER_RENDERING_ID, PROVIDER_REFERRING_ID
        FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX
      ) A
      LEFT JOIN (
        SELECT DISTINCT PATIENT_ID, PATIENT_BIRTH_YEAR, PATIENT_GENDER
        FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PTNT_DMGRPHC
      ) B ON A.PATIENT_ID = B.PATIENT_ID
      LEFT JOIN PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRVDR C
        ON COALESCE(A.PROVIDER_REFERRING_ID, A.PROVIDER_RENDERING_ID) = C.PROVIDER_ID
    ) DX
    INNER JOIN (
      SELECT DISTINCT DIAGNOSIS_CODE, DIAGNOSIS_DESCRIPTION
      FROM PHCDW.PHCDW_STG_CAR.STG_IQVIA_LAAD_DIM_DIAGNOSIS
      WHERE DIAGNOSIS_CODE IN (
        -- See SKILL.md for full 100+ ICD code list
        'N18', 'N18.1', 'N18.2', 'N18.3', 'N18.4', 'N18.9',
        'I12', 'I12.9', 'I13', 'I13.0', 'I13.1', 'I13.10',
        'E11.2', 'E11.21', 'E11.22', 'E11.29',
        'D63.1', 'Z94.0', 'Z99.2'
        -- ...
      )
    ) CD ON DX.DIAGNOSIS_CODE = CD.DIAGNOSIS_CODE
    WHERE (EXTRACT(YEAR FROM SVC_DT)*100 + EXTRACT(MONTH FROM SVC_DT))
          >= {{complete_history_start_month}}
      AND (EXTRACT(YEAR FROM SVC_DT)*100 + EXTRACT(MONTH FROM SVC_DT))
          <= {{complete_history_end_month}}
      AND PROVIDER_ID IS NOT NULL
"""

df_dx = Get_Data_Snowflakes(query)
df_dx.display()
```

### Pattern 5: HCP-Level DX_09 (Comorbidity Features)

```python
# Cell 3 — Query comorbidity features by provider
query = f"""
    SELECT DISTINCT PATIENT_ID, SVC_DT, DIAGNOSIS_DESCRIPTION, DIAG_GRP,
      PROVIDER_ID, PROVIDER_RENDERING_ID, PROVIDER_REFERRING_ID
    FROM (
      SELECT DISTINCT PATIENT_ID, SERVICE_DATE AS SVC_DT,
        CD.DIAGNOSIS_DESCRIPTION, DIAG_GRP,
        PROVIDER_RENDERING_ID, PROVIDER_REFERRING_ID, PROVIDER_ID
      FROM (
        SELECT PATIENT_ID, DIAGNOSIS_CODE, SERVICE_DATE,
               PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID,
               COALESCE(PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID) AS PROVIDER_ID
        FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX
      ) DX
      INNER JOIN (
        SELECT DISTINCT DIAGNOSIS_CODE, DIAGNOSIS_DESCRIPTION, DIAG_GRP
        FROM PHCDW.PHCDW_SANDBOX.FIN_DIAG_CD
        WHERE DIAG_GRP IN ('KD', 'CV-KD', 'DB-KD')
      ) CD ON DX.DIAGNOSIS_CODE = CD.DIAGNOSIS_CODE
      WHERE (EXTRACT(YEAR FROM SVC_DT)*100 + EXTRACT(MONTH FROM SVC_DT))
            >= {{analysis_start_month}}
        AND (EXTRACT(YEAR FROM SVC_DT)*100 + EXTRACT(MONTH FROM SVC_DT))
            <= {{current_month}}
        AND PROVIDER_ID IS NOT NULL
    )
"""

df_dx = Get_Data_Snowflakes(query)
df_dx.display()
```

## Optional Config Import

If using date parameters (`lookback_start`, `lookback_end`, `analysis_start_month`,
`complete_history_start_month`, `current_month`, etc.), also import the config notebook:

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config"
```

This provides:
- `lookback_start`, `lookback_end` — dynamically loaded from control dates table
- `analysis_start_month` — YYYYMM integer (default `201901`)
- `current_month` — YYYYMM integer for the current run
- `complete_history_start_month`, `complete_history_end_month` — full history window for HCP-level queries
- `prediction_start`, `prediction_end` — prediction window boundaries
- `cohort_start_date`, `cohort_end_date` — cohort boundaries for patient-level features
- `lookback_duration` (365 days), `prediction_duration` (30 days)
- `time_windows` — `[30, 60, 90, 180, 270, 360]` for feature engineering
- All file paths for Delta materialized outputs and input files

## DX-Specific SQL Patterns

Since queries execute on **Snowflake** (not Databricks SQL), use Snowflake SQL syntax.
DX queries have some unique patterns compared to RX:

### Provider ID derivation (always required)
```sql
-- DX fact table has two provider columns; always coalesce
COALESCE(PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID) AS PROVIDER_ID
```

### Date column aliasing
```sql
-- DX fact table uses SERVICE_DATE, not SVC_DT
SERVICE_DATE AS SVC_DT
```

### YYYYMM date filtering (HCP-level queries)
```sql
-- Convert date to YYYYMM integer for month-level filtering
(EXTRACT(YEAR FROM SVC_DT) * 100 + EXTRACT(MONTH FROM SVC_DT)) >= {analysis_start_month}
```

### Hospitalization filtering
```sql
-- DATA_SOURCE = 'HX' for hospital/inpatient claims only
WHERE DATA_SOURCE = 'HX'
```

### Two diagnosis dimension tables
```sql
-- Patient-level queries use:
PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_DIAG

-- HCP-level DX_03 query uses (different table, same structure):
PHCDW.PHCDW_STG_CAR.STG_IQVIA_LAAD_DIM_DIAGNOSIS

-- HCP-level DX_09 comorbidity query uses:
PHCDW.PHCDW_SANDBOX.FIN_DIAG_CD  -- has DIAG_GRP column
```

## Important Constraints

1. **Never execute these queries via `spark.sql()` or Databricks SQL endpoints** — the tables live in Snowflake, not Unity Catalog.
2. **Always use `Get_Data_Snowflakes(query)`** to execute.
3. **The connection notebook must be `%run` before any query** — it sets up authentication and the function.
4. **Secrets scope access required** — the user's cluster must have permission to read from `US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`.
5. **Pre-materialized Delta outputs** exist for all 5 DX queries (see SKILL.md) — prefer reading those with `spark.read.format("delta").load(path)` when the data is already available, to avoid re-querying Snowflake.
6. **Always use COALESCE for PROVIDER_ID** — unlike RX claims, DX claims have separate referring and rendering provider columns.
