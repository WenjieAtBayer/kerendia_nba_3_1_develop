# PX Claims Query Execution Template

All IQVIA LAAD PX claims queries run against **Snowflake** (not Databricks SQL). They **cannot** be
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

## PX-Specific Query Execution Patterns

All PX queries are **patient-level only** (no HCP-level PX queries exist in the pipeline).

### Pattern 1: 12-Month & First Occurrence (5 CKD Procedures)

```python
# Cell 1 — Connection (run once per session)
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```

```python
# Cell 2 — Config (for date parameters)
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config"
```

```python
# Cell 3 — Query CKD-specific procedures
px_query = f"""
    SELECT PX.CLAIM_ID, PX.PATIENT_ID, PX.SERVICE_DATE AS SVC_DT,
      PX.PROCEDURE_CODE, PX_CODES.PROCEDURE_DESCRIPTION,
      COALESCE(PX.PROVIDER_REFERRING_ID, PX.PROVIDER_RENDERING_ID) AS PROVIDER_ID,
      PX.PROVIDER_REFERRING_ID, PX.PROVIDER_RENDERING_ID, PX.PAYER_PLAN_ID
    FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_PX PX
    INNER JOIN (
      SELECT DISTINCT PROCEDURE_CODE, PROCEDURE_DESCRIPTION
      FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRCDR_CD
    ) PX_CODES
      ON PX.PROCEDURE_CODE = PX_CODES.PROCEDURE_CODE
    WHERE PROCEDURE_DESCRIPTION IN (
      'ALBUMIN; URINE (EG, MICROALBUMIN), QUANTITATIVE',
      'CREATININE; OTHER SOURCE',
      'END-STAGE RENAL DISEASE (ESRD) RELATED SERVICES MONTHLY, FOR PATIENTS 20 YEARS OF AGE AND OLDER; WIT',
      'GLUCOSE; QUANTITATIVE, BLOOD (EXCEPT REAGENT STRIP)',
      'UNLISTED DIALYSIS PROCEDURE, INPATIENT OR OUTPATIENT'
    )
      AND SVC_DT <= '{lookback_end}'
"""

df_px = Get_Data_Snowflakes(px_query)
df_px.display()
```

### Pattern 2: All Events (broad + echo test grouping)

```python
# Cell 3 — Query all PX claims within lookback window
px_query = f"""
    SELECT PX.CLAIM_ID, PX.PATIENT_ID, PX.SERVICE_DATE AS SVC_DT,
      PX.PROCEDURE_CODE, PX_CODES.PROCEDURE_DESCRIPTION,
      COALESCE(PX.PROVIDER_REFERRING_ID, PX.PROVIDER_RENDERING_ID) AS PROVIDER_ID,
      PX.PROVIDER_REFERRING_ID, PX.PROVIDER_RENDERING_ID, PX.PAYER_PLAN_ID
    FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_PX PX
    INNER JOIN (
      SELECT DISTINCT PROCEDURE_CODE, PROCEDURE_DESCRIPTION
      FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRCDR_CD
    ) PX_CODES
      ON PX.PROCEDURE_CODE = PX_CODES.PROCEDURE_CODE
    WHERE SVC_DT <= '{lookback_end}'
"""

df_px = Get_Data_Snowflakes(px_query)
```

```python
# Cell 4 — Post-filter to prevalent events
import pandas as pd
px_event_list = pd.read_csv(
    "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/feature_selection/Kerendia NBA 3.0 - Px Event List.csv"
)
df_px = df_px.filter(col("PROCEDURE_DESCRIPTION").isin(px_event_list["EVENT_NAME"].tolist()))
```

```python
# Cell 5 — Group echocardiogram codes into single "echo_tests" event
from pyspark.sql.functions import when, col

echo_test_procedure_codes = [
    "93303", "93304", "93306", "93307", "93308", "93312", "93313", "93314",
    "93315", "93316", "93317", "93318", "93319", "93320", "93321", "93325",
    "93350", "93351", "93352", "93355", "93356", "93662",
    "0439T", "0932T",
    "C8921", "C8922", "C8923", "C8924", "C8925", "C8926",
    "C8927", "C8928", "C8929", "C8930", "C9786"
]

df_px = df_px.withColumn(
    "PROCEDURE_DESCRIPTION",
    when(col("PROCEDURE_CODE").isin(echo_test_procedure_codes), "echo_tests")
    .otherwise(col("PROCEDURE_DESCRIPTION"))
)

df_px.display()
```

### Pattern 3: Hospitalization Only

```python
# Cell 3 — Query hospital-only PX claims (no date filter)
px_query = f"""
    SELECT PX.CLAIM_ID, PX.PATIENT_ID, PX.SERVICE_DATE AS SVC_DT,
      PX.PROCEDURE_CODE, PX_CODES.PROCEDURE_DESCRIPTION,
      COALESCE(PX.PROVIDER_REFERRING_ID, PX.PROVIDER_RENDERING_ID) AS PROVIDER_ID,
      PX.PROVIDER_REFERRING_ID, PX.PROVIDER_RENDERING_ID, PX.PAYER_PLAN_ID
    FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_PX PX
    INNER JOIN (
      SELECT DISTINCT PROCEDURE_CODE, PROCEDURE_DESCRIPTION
      FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRCDR_CD
    ) PX_CODES
      ON PX.PROCEDURE_CODE = PX_CODES.PROCEDURE_CODE
    WHERE DATA_SOURCE = 'HX'
"""

df_px_hosp = Get_Data_Snowflakes(px_query)

# Post-filter to prevalent events
df_px_hosp = df_px_hosp.filter(
    col("PROCEDURE_DESCRIPTION").isin(px_event_list["EVENT_NAME"].tolist())
)
df_px_hosp.display()
```

## Optional Config Import

If using date parameters (`lookback_start`, `lookback_end`, etc.), also import the config notebook:

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config"
```

This provides:
- `lookback_start`, `lookback_end` — dynamically loaded from control dates table
- `prediction_start`, `prediction_end` — prediction window boundaries
- `cohort_start_date`, `cohort_end_date` — cohort boundaries for patient-level features
- `lookback_duration` (365 days), `prediction_duration` (30 days)
- `time_windows` — `[30, 60, 90, 180, 270, 360]` for feature engineering
- All file paths for Delta materialized outputs and input files

## PX-Specific SQL Patterns

Since queries execute on **Snowflake** (not Databricks SQL), use Snowflake SQL syntax.

### Provider ID derivation (always required)
```sql
-- PX fact table has two provider columns; always coalesce (same as DX)
COALESCE(PX.PROVIDER_REFERRING_ID, PX.PROVIDER_RENDERING_ID) AS PROVIDER_ID
```

### Date column aliasing
```sql
-- PX fact table uses SERVICE_DATE, not SVC_DT (same as DX)
PX.SERVICE_DATE AS SVC_DT
```

### Hospitalization filtering
```sql
-- DATA_SOURCE = 'HX' for hospital/inpatient claims only
WHERE DATA_SOURCE = 'HX'
```

### Single dimension table
```sql
-- Only one procedure dimension table (simpler than DX)
PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRCDR_CD
```

## Important Constraints

1. **Never execute these queries via `spark.sql()` or Databricks SQL endpoints** — the tables live in Snowflake, not Unity Catalog.
2. **Always use `Get_Data_Snowflakes(query)`** to execute.
3. **The connection notebook must be `%run` before any query** — it sets up authentication and the function.
4. **Secrets scope access required** — the user's cluster must have permission to read from `US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`.
5. **Pre-materialized Delta outputs** exist for all 3 PX queries (see SKILL.md) — prefer reading those with `spark.read.format("delta").load(path)` when the data is already available, to avoid re-querying Snowflake.
6. **Always use COALESCE for PROVIDER_ID** — same as DX claims, PX claims have separate referring and rendering provider columns.
7. **Echo test grouping is PySpark-only** — the 35 echocardiogram procedure codes are grouped into `echo_tests` in post-processing, not in SQL.
