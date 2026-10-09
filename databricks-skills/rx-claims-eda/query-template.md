# RX Claims Query Execution Template

All IQVIA LAAD RX claims queries run against **Snowflake** (not Databricks SQL). They **cannot** be
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

## Query Execution Pattern

When generating code for a user, always produce a notebook cell (or Python file) with this pattern:

```python
# Cell 1 — Connection (run once per session)
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```

```python
# Cell 2 — Query
query = """
    SELECT ...
    FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX A
    ...
"""

df = Get_Data_Snowflakes(query)
df.display()
```

## Optional Config Import

If using date parameters (`lookback_start`, `lookback_end`, `analysis_start_month`, etc.), also import
the config notebook:

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

## SQL Dialect Notes

Since queries execute on **Snowflake** (not Databricks SQL), use Snowflake SQL syntax:
- `EXTRACT(YEAR FROM date_col)` — works in both
- `REGEXP` — Snowflake regex (not `RLIKE`)
- `TO_DATE(string, format)` — Snowflake date parsing
- `MEDIAN()` — native Snowflake aggregate (not available in Databricks SQL)
- `ILIKE` — case-insensitive LIKE (Snowflake-native)
- String functions use Snowflake semantics

## Important Constraints

1. **Never execute these queries via `spark.sql()` or Databricks SQL endpoints** — the tables live in Snowflake, not Unity Catalog.
2. **Always use `Get_Data_Snowflakes(query)`** to execute.
3. **The connection notebook must be `%run` before any query** — it sets up authentication and the function.
4. **Secrets scope access required** — the user's cluster must have permission to read from `US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`.
5. **Pre-materialized Delta outputs** exist for common queries (see SKILL.md) — prefer reading those with `spark.read.format("delta").load(path)` when the data is already available, to avoid re-querying Snowflake.
