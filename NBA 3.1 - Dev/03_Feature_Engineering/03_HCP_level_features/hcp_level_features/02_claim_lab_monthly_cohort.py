# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# DBTITLE 1,Title
# MAGIC %md
# MAGIC # Claim Lab Monthly Features — Cohort-Based
# MAGIC
# MAGIC Refactored from `02_claim_lab_monthly` (NBA 3.0) to use the shared `00_cohort_config` (cohort month + offset). The feature logic is unchanged (TEST_TYPE / STAGE pivots, claim counts, `RUNNING_` totals, `PCT_` features); only the time windows change from monthly row-windows to date ranges ending at the cohort cutoff.
# MAGIC
# MAGIC * **Offset = 0** reproduces the original calendar-month values (see Validation section)
# MAGIC * **Lookback windows**: `LOOKBACK_WINDOWS` from config (1, 3, 6, 12, as 3.0)
# MAGIC * **Cohorts**: all cohorts from `COHORT_ORIGIN` (or the `COHORT_MONTHS` list) whose cutoff is on or before the last lab service date, so every window has complete data
# MAGIC * **Output grain**: one row per (NPI_NUMBER, COHORT_ID), one partition per cohort; the original had one row per (NPI_NUMBER, SVC_DT_M)
# MAGIC * **Outputs**: `notebook_output/claim_lab_monthly_cohort` and `provider_claim_lab_monthly_cohort`, partitioned by `COHORT_ID` (Wenjie's `_ZS` tables are not touched)
# MAGIC
# MAGIC Source notebook: `/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/02_claim_lab_monthly`

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature Engineering - Lab Test
# MAGIC #### Data source used
# MAGIC * PHCDW.PHCDW_DSAA.KERENDIA_LAB_QUEST_LABCORP_VIEW
# MAGIC * PHCDW.PHCDW_STG_CAR.STG_IQVIA_LAAD_DIM_PRODUCT 
# MAGIC
# MAGIC #### Steps:
# MAGIC 1. Query UACR/eGFR lab test claims data after 2018-01-01
# MAGIC 2. Get month level lab test aggregation for each neph
# MAGIC 3. Keep data only after April-2021 as Kerendia Got Launched in July-2021 (Keeping couple of months before July-2022 for adjustment of time-alignment in combined data notebook)
# MAGIC 4. Save table to databricks
# MAGIC
# MAGIC #### Notes:
# MAGIC 1. Time frame: SVC_DT >= '2018-01-01' 
# MAGIC 2. GFR test:  upper(LCL_LAB_TEST_NM) like '%GFR%' or upper(LCL_LAB_TEST_NM) like '%GLOMERULAR%' then 'GFR' 
# MAGIC 3. UACR test:  upper(LCL_LAB_TEST_NM) like '%ALB%' or upper(LCL_LAB_TEST_NM) like '%RATIO%' then 'UACR'
# MAGIC 4. GFR stage: 
# MAGIC     * when test_type = 'GFR'  and MEDIAN_TEST_RESULT <15 then 5
# MAGIC     * when test_type = 'GFR'  and MEDIAN_TEST_RESULT >=15 AND MEDIAN_TEST_RESULT <30 then 4
# MAGIC     * when test_type = 'GFR'  and MEDIAN_TEST_RESULT >=30 AND MEDIAN_TEST_RESULT <60 then 3
# MAGIC     * when test_type = 'GFR'  and MEDIAN_TEST_RESULT >=60 AND MEDIAN_TEST_RESULT <90 then 2
# MAGIC     * when test_type = 'GFR'  and MEDIAN_TEST_RESULT >=90 AND  MEDIAN_TEST_RESULT <=150 then 1
# MAGIC 5. UACR stage:
# MAGIC     * when test_type = 'UACR' and MEDIAN_TEST_RESULT <30 then 1
# MAGIC     * when test_type = 'UACR' and MEDIAN_TEST_RESULT >=30 and MEDIAN_TEST_RESULT <300 then 2
# MAGIC     * when test_type = 'UACR' and MEDIAN_TEST_RESULT >=300 then 3

# COMMAND ----------

# DBTITLE 1,Section: Connection and Config
# MAGIC %md ##0. Connection and Config

# COMMAND ----------

# MAGIC %run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"

# COMMAND ----------

# DBTITLE 1,Load cohort config (all params + helpers)
# MAGIC %run "../00_cohort_config"

# COMMAND ----------

# DBTITLE 1,Config confirmation
# All config (OFFSET_DAYS, COHORT_MONTHS, LOOKBACK_WINDOWS, NPI_COL, SVC_COL,
# VALIDATION_MODE, get_cohort_months, get_cohort_bounds, build_feature_group, ...)
# comes from 00_cohort_config. 00_step23_function is no longer needed.

_cohort_setting = (COHORT_MONTHS if COHORT_MONTHS is not None
                   else f"all {COHORT_ORIGIN[:7]} .. {COHORT_LAST[:7]} (complete data only)")
print(f"Offset: {OFFSET_DAYS} | Cohorts: {_cohort_setting} | Validation: {VALIDATION_MODE}")

# COMMAND ----------

# MAGIC %md ##1. Query Data

# COMMAND ----------

# DBTITLE 1,Load raw lab claims and define cohorts
# Paths and windows come from 00_cohort_config (HCP shared constants)
_QUERY_OUTPUT    = HCP_QUERY_OUTPUT
_NOTEBOOK_OUTPUT = HCP_NOTEBOOK_OUTPUT
# Lookbacks: LOOKBACK_WINDOWS from the config (= HCP_LOOKBACK_WINDOWS["lab"], 1/3/6/12)
df_lab_raw = spark.read.format("delta").load(_QUERY_OUTPUT + "Lab_03")

# Month truncation (date_trunc('MM', SVC_DT)) removed: daily SVC_DT is kept and
# windows are date ranges from each cohort month + OFFSET_DAYS (00_cohort_config).
df_lab = df_lab_raw.withColumn("PATIENT_ID", F.col("PATIENT_ID").cast('string'))

# Validation mode: restrict to the 10 test HCPs (no-op when VALIDATION_MODE = False)
df_lab = apply_npi_filter(df_lab, NPI_COL)

# Team rule (3.1, option B): every feature, RUNNING_ included, uses lab claims from DATA_START_DATE on.
# df_lab_all keeps the full history only for the offset-0 parity check against the 3.0 original.
df_lab_all = df_lab
df_lab = df_lab.filter(F.col(SVC_COL) >= F.lit(DATA_START_DATE))

# ---------- Cohorts to process ----------
# Every cohort (COHORT_ORIGIN..COHORT_LAST, or the COHORT_MONTHS list) whose cutoff is on or
# before the common last service date of all HCP inputs (get_hcp_cohort_months, 00_cohort_config),
# so every HCP feature table has the same COHORT_IDs. DATA_MAX_DT (Lab_03 only) is kept for parity.
import builtins
DATA_MAX_DT   = df_lab_raw.agg(F.max(SVC_COL)).first()[0]
COHORT_LIST   = get_hcp_cohort_months()
COHORT_BOUNDS = {m: get_cohort_bounds(m) for m in COHORT_LIST}
COHORT_IDS    = [COHORT_BOUNDS[m]["cohort_id"] for m in COHORT_LIST]
print(f"Lab data through {DATA_MAX_DT} -> {len(COHORT_LIST)} complete cohorts: "
      f"{COHORT_LIST[0]} .. {COHORT_LIST[-1]}")

# ---------- Fixed pivot values: same columns for every cohort (as in the original) ----------
TEST_TYPE_VALUES = sorted(r[0] for r in df_lab_raw.select("TEST_TYPE").distinct().collect() if r[0] is not None)
STAGE_VALUES     = sorted(r[0] for r in df_lab_raw.select("STAGE").distinct().collect() if r[0] is not None)
print(f"TEST_TYPE values: {TEST_TYPE_VALUES}")
print(f"STAGE values ({len(STAGE_VALUES)}): {STAGE_VALUES}")

# ---------- Pre-filter to the widest range over all cohorts ----------
_max_window = builtins.max(LOOKBACK_WINDOWS)
_max_start  = COHORT_BOUNDS[COHORT_LIST[0]]["window_bounds"][_max_window]["start"]
_end        = COHORT_BOUNDS[COHORT_LIST[-1]]["window_bounds"][_max_window]["end"]

df_lab_filtered = df_lab.filter(
    (F.col(SVC_COL) > F.lit(_max_start)) &
    (F.col(SVC_COL) <= F.lit(_end))
)

print(f"Filtered lab claims to ({_max_start}, {_end}]")
print(f"Row count: {df_lab_filtered.count():,}")

# COMMAND ----------

# DBTITLE 1,Preview filtered lab claims
display(df_lab_filtered.limit(100))

# COMMAND ----------

# DBTITLE 1,Date range and cohort bounds check
# Claims from DATA_START_DATE (used for RUNNING_) and windowed range (used for _IN_LAST_N_MONTH)
display(df_lab.agg(F.min(SVC_COL).alias("min_svc_dt"), F.max(SVC_COL).alias("max_svc_dt"), F.count(F.lit(1)).alias("rows")))
display(df_lab_filtered.agg(F.min(SVC_COL).alias("min_svc_dt"), F.max(SVC_COL).alias("max_svc_dt"), F.count(F.lit(1)).alias("rows")))

# Cutoff and window start (exclusive) for every cohort; every window ends at the cutoff
display(spark.createDataFrame(
    [(COHORT_BOUNDS[m]["cohort_id"], COHORT_BOUNDS[m]["cutoff"].strftime("%Y-%m-%d"),
      *[COHORT_BOUNDS[m]["window_bounds"][w]["start"] for w in LOOKBACK_WINDOWS])
     for m in COHORT_LIST],
    "COHORT_ID string, CUTOFF_DATE string, " +
    ", ".join(f"START_{w}M string" for w in LOOKBACK_WINDOWS)
))

# COMMAND ----------

# MAGIC %md ##2. Create Features

# COMMAND ----------

# DBTITLE 1,Index columns
# Features are built per cohort on NPI; COHORT_ID is added afterwards, so the
# output grain is one row per NPI per cohort (was NPI x SVC_DT_M)
index_cols = [NPI_COL]

# COMMAND ----------

# MAGIC %md ####2.1 Lab Test

# COMMAND ----------

# DBTITLE 1,Lab test features per window (TEST_TYPE, STAGE, total)
# ---- 2.1 Lab Test features per lookback window (one cohort) ----
# Same pivots and counts as the original (TEST_TYPE, STAGE, total claims), but each
# window is a date range from the cohort's window_bounds instead of a row-window over
# monthly rows. Column names are unchanged: TOTAL_LAB_CLAIMS_{VALUE}_IN_LAST_{N}_MONTH
# Fixed pivot values -> every cohort gets the same columns (0 when no claims).

def build_window_features(df, cb):
    wb = cb["window_bounds"]
    df_test_type = build_feature_group(
        df, NPI_COL, SVC_COL, pivot_col="TEST_TYPE", prefix="TOTAL_LAB_CLAIMS_",
        window_bounds=wb, pivot_values=TEST_TYPE_VALUES)
    df_stage = build_feature_group(
        df, NPI_COL, SVC_COL, pivot_col="STAGE", prefix="TOTAL_LAB_CLAIMS_",
        window_bounds=wb, pivot_values=STAGE_VALUES)
    # get total claims (denominator for PCT)
    df_total = build_total_col(df, NPI_COL, SVC_COL, wb, total_name="TOTAL_LAB_CLAIMS")
    return df_test_type, df_stage, df_total


def _display_with_bounds(df, cb, n=100):
    """Display-only: COHORT_ID plus a WINDOW_{N}M column with its (start, end] date range
    in front of each window's features. The feature DataFrames are not changed."""
    _df_cols = df.columns
    _cols = [F.col(NPI_COL), F.lit(cb["cohort_id"]).alias("COHORT_ID")]
    for w in sorted(cb["window_bounds"]):
        b = cb["window_bounds"][w]
        _cols.append(F.lit(f"({b['start']}, {b['end']}]").alias(f"WINDOW_{w}M"))
        _cols += [F.col(c) for c in _df_cols if c.endswith(f"_IN_LAST_{w}_MONTH")]
    display(df.select(*_cols).limit(n))


# ---- Preview on one cohort (all cohorts are built and written in section 4) ----
PREVIEW_COHORT = COHORT_MONTH if COHORT_MONTH in COHORT_LIST else COHORT_LIST[0]
cb_preview = COHORT_BOUNDS[PREVIEW_COHORT]

display(spark.createDataFrame(
    [(cb_preview["cohort_id"], f"_IN_LAST_{w}_MONTH",
      cb_preview["window_bounds"][w]["start"], cb_preview["window_bounds"][w]["end"])
     for w in sorted(cb_preview["window_bounds"])],
    "COHORT_ID string, COLUMN_SUFFIX string, SVC_DT_AFTER string, SVC_DT_UP_TO string"
))

df_test_type, df_stage, df_total = build_window_features(df_lab_filtered, cb_preview)
_display_with_bounds(df_test_type, cb_preview)
_display_with_bounds(df_stage, cb_preview)
_display_with_bounds(df_total, cb_preview)

print(f"Preview {cb_preview['cohort_id']} | Test type cols: {len(df_test_type.columns) - 1} | "
      f"Stage cols: {len(df_stage.columns) - 1} | Total cols: {len(df_total.columns) - 1}")

# COMMAND ----------

# DBTITLE 1,RUNNING features from full history
# ---- 2.1b RUNNING_ features (full lab history through CUTOFF_DATE) ----
# Reproduces step3_lag's unbounded-preceding RUNNING_ columns: every lab claim from the
# start of Lab_03 history up to and including the cohort cutoff.
# Names unchanged: RUNNING_TOTAL_LAB_CLAIMS_{VALUE}, RUNNING_TOTAL_LAB_CLAIMS

def build_running_features(df, cb):
    cutoff_lit = F.to_date(F.lit(cb["cutoff"].strftime("%Y-%m-%d")))
    df_lab_running = df.filter(F.col(SVC_COL) <= cutoff_lit)

    df_running_test_type = pivoted_counts(df_lab_running, NPI_COL, "TEST_TYPE",
                                          "RUNNING_TOTAL_LAB_CLAIMS_", "", values=TEST_TYPE_VALUES)
    df_running_stage     = pivoted_counts(df_lab_running, NPI_COL, "STAGE",
                                          "RUNNING_TOTAL_LAB_CLAIMS_", "", values=STAGE_VALUES)
    df_running_total     = (
        df_lab_running.groupBy(NPI_COL)
        .agg(F.count(F.lit(1)).alias("RUNNING_TOTAL_LAB_CLAIMS"))
    )

    return (
        df_running_total
        .join(df_running_test_type, on=NPI_COL, how="left")
        .join(df_running_stage, on=NPI_COL, how="left")
        .na.fill(0)
    )


# ---- Preview on one cohort ----
df_running = build_running_features(df_lab, cb_preview)
print(f"Preview {cb_preview['cohort_id']} | Running universe: {df_running.count():,} NPIs | "
      f"RUNNING_ cols: {len([c for c in df_running.columns if c.startswith('RUNNING_')])}")

# COMMAND ----------

# MAGIC %md ####2.2 Combine

# COMMAND ----------

# DBTITLE 1,Combine feature groups
# combine features — one row per NPI
# NPI universe = NPIs with lab claims in the widest window + NPIs with older history only,
# so their RUNNING_ values are kept (same approach as NB01).
# Column-name cleaning is done inside build_feature_group / pivoted_counts (clean_col_name).
def combine_features(df, df_test_type, df_stage, df_total, df_running, cb):
    _wb = cb["window_bounds"][_max_window]
    npi_universe = filter_to_window(df, SVC_COL, _wb["start"], _wb["end"]).select(NPI_COL).distinct()
    npi_universe_wide = npi_universe.union(df_running.select(NPI_COL)).distinct()
    return (
        npi_universe_wide
        .join(df_test_type, how='left', on=index_cols)
        .join(df_stage, how='left', on=index_cols)
        .join(df_total, how='left', on=index_cols)
        .join(df_running, how='left', on=index_cols)
        .na.fill(value=0)
    )


# ---- Preview on one cohort ----
df_spine = combine_features(df_lab_filtered, df_test_type, df_stage, df_total, df_running, cb_preview)
print(f"Preview {cb_preview['cohort_id']} | Combined spine: {df_spine.count():,} NPIs, "
      f"{len(df_spine.columns)} columns")
df_spine.limit(100).display()

# COMMAND ----------

# DBTITLE 1,Section: Pct Features
# MAGIC %md ##3. Create Pct Features

# COMMAND ----------

# DBTITLE 1,PCT features
# ---- PCT features: each feature / TOTAL_LAB_CLAIMS in the same window ----
# Same definition as the original (PCT_ + feature name), without exec().
# Safe division as in NB01: 0.0 when the window total is 0.
total_col = "TOTAL_LAB_CLAIMS"

def add_pct_features(df_spine):
    _spine_cols = df_spine.columns
    pct_features = []
    for i in LOOKBACK_WINDOWS:
        denominator = f"{total_col}_IN_LAST_{i}_MONTH"
        features_i = [c for c in _spine_cols
                      if c.endswith(f"_IN_LAST_{i}_MONTH") and c != denominator]
        pct_features += [
            F.when(F.col(denominator) != 0, F.col(feature) / F.col(denominator))
             .otherwise(F.lit(0.0))
             .alias('PCT_' + feature)
            for feature in features_i
        ]
    return df_spine.select("*", *pct_features)


# ---- Preview on one cohort ----
df_spine = add_pct_features(df_spine)
print(f"Preview {cb_preview['cohort_id']} | After PCT: {len(df_spine.columns)} columns")

# COMMAND ----------

# DBTITLE 1,Add cohort metadata
# ---- Add cohort metadata (replaces the hardcoded SVC_DT_M >= '2022-01-01' filter) ----
def add_cohort_metadata(df_spine, cb):
    return (
        df_spine
        .withColumn("COHORT_ID", F.lit(cb["cohort_id"]))
        .withColumn("COHORT_MONTH", F.lit(cb["cohort_month"]))
        .withColumn("OFFSET_DAYS", F.lit(cb["offset_days"]))
        .withColumn("CUTOFF_DATE", F.lit(cb["cutoff"].strftime("%Y-%m-%d")))
        .withColumn("SVC_DT_M", F.to_timestamp(F.lit(f"{cb['cohort_month']}-01")))
    )


# ---- Preview on one cohort ----
claim_lab_monthly = add_cohort_metadata(df_spine, cb_preview)
print(f"Preview {cb_preview['cohort_id']} | Final output columns: {len(claim_lab_monthly.columns)}")

# COMMAND ----------

claim_lab_monthly.limit(100).display()

# COMMAND ----------

# DBTITLE 1,Section: Fast cohort engine
# MAGIC %md
# MAGIC ####2.3 Fast Cohort Engine (used by section 4)
# MAGIC Same features as the step-by-step functions above (`build_cohort_slow`), but all cohorts in **one query**, the same approach as NB01:
# MAGIC 1. **Once per run**: each lab claim becomes its feature keys (total, `TEST_TYPE = x`, `STAGE = y`), counted per **NPI x cohort month x key**. Kept in memory (validation) or saved to a staging Delta table (production).
# MAGIC 2. **All cohorts**: each month is tagged with every (cohort, window) it belongs to (1, 3, 6, 12 months, RUNNING_) through a small broadcast table, then one pivot by NPI x cohort. PCT and metadata use the same functions.
# MAGIC
# MAGIC The windows line up exactly with cohort months (checked for every cohort), so counting by month gives the same result as filtering by date. The next cell checks the engine against `build_cohort_slow`.

# COMMAND ----------

# DBTITLE 1,Fast cohort engine
# ============================================================
# FAST COHORT ENGINE — lab claims read once, all cohorts in one query
# ============================================================
import time
from datetime import date

_SEP = "\u0001"   # separator inside pivot keys (never appears in the data)
_STAGE_PREFIX = _NOTEBOOK_OUTPUT + "claim_lab_monthly_cohort_stage_"


# materialize(df, name) comes from 00_cohort_config (in memory in validation, staging Delta table
# _STAGE_PREFIX + name in production).


def build_cohort_slow(cb):
    """Step-by-step version (same functions as the preview cells): reference for the fast engine."""
    df_test_type, df_stage, df_total = build_window_features(df_lab_filtered, cb)
    df_running = build_running_features(df_lab, cb)
    df_spine   = combine_features(df_lab_filtered, df_test_type, df_stage, df_total, df_running, cb)
    df_spine   = add_pct_features(df_spine)
    return add_cohort_metadata(df_spine, cb).withColumn("PULL_DT", F.current_date())


# ---------- Step 1: claims -> (NPI, cohort month, feature key, N) ----------
_LAB_GROUPS = [("TEST_TYPE", TEST_TYPE_VALUES), ("STAGE", STAGE_VALUES)]

def build_lab_long(df, offset_days):
    d = (df.filter(F.col(NPI_COL).isNotNull())
           .withColumn("_CM", assign_cohort_month(F.col(SVC_COL), offset_days)))
    keys = [F.lit("total" + _SEP)] + [F.concat(F.lit(g + _SEP), F.col(g)) for g, _ in _LAB_GROUPS]
    return (d.select(NPI_COL, "_CM", F.explode(F.array(*keys)).alias("KEY"))
             .filter(F.col("KEY").isNotNull())            # null TEST_TYPE / STAGE -> not counted (like pivot)
             .groupBy(NPI_COL, "_CM", "KEY").agg(F.count(F.lit(1)).alias("N")))


# ---------- Output columns: (pivot key, column name), same names as the step-by-step functions ----------
_W = [str(w) for w in sorted(LOOKBACK_WINDOWS)]
COUNT_SPECS = []
for _t in _W + ["RUN"]:
    _pre = "RUNNING_" if _t == "RUN" else ""
    _sfx = "" if _t == "RUN" else f"_IN_LAST_{_t}_MONTH"
    COUNT_SPECS.append((f"total{_SEP}{_SEP}{_t}", f"{_pre}TOTAL_LAB_CLAIMS{_sfx}"))
    for _g, _vals in _LAB_GROUPS:
        COUNT_SPECS += [(f"{_g}{_SEP}{v}{_SEP}{_t}", f"{_pre}TOTAL_LAB_CLAIMS_{clean_col_name(v)}{_sfx}")
                        for v in _vals]


# ---------- Window -> cohort-month range (checked: windows must line up with cohort months) ----------
def _cm_of(d, off):
    """Python version of assign_cohort_month."""
    return (d - timedelta(days=off - 1)).replace(day=1) if off > 0 else d.replace(day=1)

def _window_months(b, off):
    s = datetime.strptime(b["start"], "%Y-%m-%d")    # exclusive
    e = datetime.strptime(b["end"], "%Y-%m-%d")      # inclusive
    lo, hi = _cm_of(s + timedelta(days=1), off), _cm_of(e, off)
    if _cm_of(s, off) == lo or _cm_of(e + timedelta(days=1), off) == hi:
        raise ValueError(f"Window {b} does not line up with cohort months at offset {off}")
    return lo.date(), hi.date()


# ---------- Staged input (built on first use, one per source x offset) ----------
# "run"  = this run's claims (from DATA_START_DATE); "orig" = full history (offset-0 parity only)
FAST_SOURCES = {"run": lambda: df_lab, "orig": lambda: df_lab_all}
_FAST_LONG = {}

def get_lab_long(off, source="run"):
    key = (source, off)
    if key not in _FAST_LONG:
        _t = time.time()
        _FAST_LONG[key] = materialize(build_lab_long(FAST_SOURCES[source](), off), f"lab_long_{source}_offset{off}")
        print(f"Lab feature-key table ({source}, offset {off}) built in {time.time() - _t:,.0f}s")
    return _FAST_LONG[key]


# ---------- Step 2: all cohorts in ONE query ----------
_EARLIEST = date(1900, 1, 1)
_META_COLS = ["COHORT_ID", "COHORT_MONTH", "OFFSET_DAYS", "CUTOFF_DATE", "SVC_DT_M", "PULL_DT"]
# Column order of the step-by-step output (schema only, nothing is computed)
OUTPUT_COLS = build_cohort_slow(cb_preview).columns

def build_all_cohorts_fast(cbs, source="run"):
    """Same columns and values as build_cohort_slow for each cohort, one row per NPI x COHORT_ID.
    NPI universe = NPIs with a lab claim up to the cutoff (as combine_features: widest window + RUNNING_)."""
    offs = {cb["offset_days"] for cb in cbs}
    if len(offs) != 1:
        raise ValueError(f"All cohorts must share one offset, got {offs}")
    off = offs.pop()

    tag_rows, meta_rows = [], []
    for cb in cbs:
        cm = datetime.strptime(f"{cb['cohort_month']}-01", "%Y-%m-%d").date()
        for w in LOOKBACK_WINDOWS:
            _lo, _hi = _window_months(cb["window_bounds"][w], off)
            if _hi != cm:
                raise ValueError(f"{cb['cohort_id']}: window {w} ends in {_hi}, expected {cm}")
            tag_rows.append((cb["cohort_id"], str(w), _lo, cm))
        tag_rows.append((cb["cohort_id"], "RUN", _EARLIEST, cm))   # RUNNING_: every month up to the cohort
        meta_rows.append((cb["cohort_id"], cb["cohort_month"], int(cb["offset_days"]), cb["cutoff"].strftime("%Y-%m-%d")))

    tags = F.broadcast(spark.createDataFrame(tag_rows, "_COHORT string, _TAG string, _LO date, _HI date"))
    df = (
        get_lab_long(off, source)
        .join(tags, (F.col("_CM") >= F.col("_LO")) & (F.col("_CM") <= F.col("_HI")))
        .withColumn("_PK", F.concat(F.col("KEY"), F.lit(_SEP), F.col("_TAG")))
        .groupBy(NPI_COL, "_COHORT").pivot("_PK", [k for k, _ in COUNT_SPECS]).agg(F.sum("N"))
        .toDF(NPI_COL, "_COHORT", *[c for _, c in COUNT_SPECS])
        .na.fill(0)
    )
    df = add_pct_features(df)   # row-wise, cohorts don't mix

    meta = (spark.createDataFrame(meta_rows, "COHORT_ID string, COHORT_MONTH string, OFFSET_DAYS int, CUTOFF_DATE string")
            .withColumns({"SVC_DT_M": F.to_timestamp(F.concat(F.col("COHORT_MONTH"), F.lit("-01"))),
                          "PULL_DT": F.current_date()}))
    return (df.join(F.broadcast(meta), F.col("_COHORT") == F.col("COHORT_ID"))
              .select(*OUTPUT_COLS))


# Same column set as the step-by-step output (fails here, before anything is computed, if not)
_fast_cols = [NPI_COL] + [c for _, c in COUNT_SPECS] + _META_COLS
_missing = sorted(set(OUTPUT_COLS) - set(_fast_cols) - {c for c in OUTPUT_COLS if c.startswith("PCT_")})
_extra   = sorted(set(_fast_cols) - set(OUTPUT_COLS))
if _missing or _extra:
    raise ValueError(f"Fast engine columns differ from build_cohort_slow: missing {_missing}, extra {_extra}")
print(f"Fast engine ready: {len(COUNT_SPECS)} count columns, {len(OUTPUT_COLS)} output columns per cohort")

# COMMAND ----------

# DBTITLE 1,Check: fast engine = step-by-step (2 cohorts)
# ---- Check: the all-cohorts query gives exactly what the step-by-step functions give ----
# First and last cohort, nothing is written.
import builtins   # round/sum are shadowed by a pyspark.sql.functions star import
import numpy as np
import pandas as pd

_check = [COHORT_LIST[0], COHORT_LIST[-1]]
_t0 = time.time()
_pd_all = build_all_cohorts_fast([COHORT_BOUNDS[m] for m in _check]).toPandas()
print(f"All-cohorts query ({len(_check)} cohorts): {time.time() - _t0:,.0f}s")

_rows = []
for m in _check:
    cb = COHORT_BOUNDS[m]
    _t0 = time.time()
    pd_one = build_cohort_slow(cb).toPandas().set_index(NPI_COL)
    _t_one = time.time() - _t0
    pd_all = _pd_all[_pd_all["COHORT_ID"] == cb["cohort_id"]].set_index(NPI_COL)

    same_order = list(pd_one.columns) == list(pd_all.columns)
    same_types = (pd_one.dtypes.astype(str) == pd_all.dtypes.reindex(pd_one.columns).astype(str)).all()
    cols = [c for c in pd_one.columns if c in pd_all.columns and c != "PULL_DT"]
    num = [c for c in cols if pd.api.types.is_numeric_dtype(pd_one[c])]
    txt = [c for c in cols if c not in num]
    common = sorted(set(pd_one.index) & set(pd_all.index))
    o = pd_one.loc[common, num].astype(float).values
    n = pd_all.loc[common, num].astype(float).values
    bad = ~np.isclose(o, n, rtol=1e-9, atol=1e-9, equal_nan=True)
    txt_bad = int((pd_one.loc[common, txt].astype(str).values != pd_all.loc[common, txt].astype(str).values).sum())
    _rows.append({"cohort": cb["cohort_id"], "npis_slow": len(pd_one), "npis_fast": len(pd_all),
                  "npis_common": len(common), "columns": len(pd_one.columns),
                  "same_column_order": same_order, "same_types": bool(same_types),
                  "cells_compared": int(bad.size) + len(common) * len(txt),
                  "mismatching_cells": int(bad.sum()) + txt_bad, "slow_seconds": builtins.round(_t_one)})
    if bad.any():
        i, j = np.argwhere(bad)[0]
        print(f"  {cb['cohort_id']} first mismatch: NPI {common[i]} {num[j]} slow={o[i, j]} fast={n[i, j]}")

df_fast_vs_slow = pd.DataFrame(_rows)
display(df_fast_vs_slow)
_ok = (df_fast_vs_slow["mismatching_cells"].sum() == 0 and df_fast_vs_slow["same_column_order"].all()
       and df_fast_vs_slow["same_types"].all()
       and (df_fast_vs_slow[["npis_slow", "npis_fast"]].values == df_fast_vs_slow[["npis_common"]].values).all())
print("PASS — fast engine = step-by-step" if _ok else "CHECK MISMATCHES")

# COMMAND ----------

# DBTITLE 1,Section: Build and Write All Cohorts
# MAGIC %md
# MAGIC ##4. Build and Write All Cohorts
# MAGIC Runs the same steps as section 2–3 (`build_window_features` → `build_running_features` → `combine_features` → `add_pct_features` → `add_cohort_metadata`) for every cohort in `COHORT_LIST` and writes one `COHORT_ID` partition per cohort. Partitions already written are kept if a later cohort fails.

# COMMAND ----------

# DBTITLE 1,One-time reset (DONE 2026-10-26, disabled)
# ---- ONE-TIME RESET: DONE on 2026-10-26, now disabled ----
# Removed the old tables so the 9-month columns are gone (the write uses mergeSchema, so dropped
# columns would otherwise stay in the table as nulls). Tables were rewritten right after:
# 20 cohorts, 102 columns. Only uncomment if columns are dropped from the code again.
# Safe: only our 3.1 tables are touched; Wenjie's 3.0 claim_lab_monthly_ZS is not affected.
#
# import os
# _RESET_PATHS = [
#     _NOTEBOOK_OUTPUT + "claim_lab_monthly_cohort",
#     _NOTEBOOK_OUTPUT + "provider_claim_lab_monthly_cohort",
# ]
# for _p in _RESET_PATHS:
#     if os.path.exists(_p):
#         dbutils.fs.rm(_p.replace("/Volumes/", "dbfs:/Volumes/"), recurse=True)
#         print(f"DELETED: {_p}")
#     else:
#         print(f"Not found (already clean): {_p}")
print("Reset disabled (done 2026-10-26)")

# COMMAND ----------

# DBTITLE 1,Build and write every cohort (one query, one write)
# New output path, partitioned by COHORT_ID so multiple cohorts/offsets coexist.
# Wenjie's claim_lab_monthly_ZS is NOT touched.
OUTPUT_PATH = _NOTEBOOK_OUTPUT + "claim_lab_monthly_cohort"

# Step-by-step version kept as build_cohort_slow (fast engine cell); switch back with
# per-cohort writes of build_cohort_slow(cb) if ever needed.
build_cohort = build_cohort_slow

# All cohorts in ONE query and ONE write (fast engine, section 2.3). Only this run's COHORT_IDs
# are replaced; other partitions in the table are kept.
_t0 = time.time()
_df_out = build_all_cohorts_fast([COHORT_BOUNDS[m] for m in COHORT_LIST])
(_df_out.write
    .format("delta")
    .mode("overwrite")
    .option("mergeSchema", "true")
    .option("replaceWhere", "COHORT_ID IN (" + ", ".join(f"'{c}'" for c in COHORT_IDS) + ")")
    .partitionBy("COHORT_ID")
    .save(OUTPUT_PATH))

print(f"{len(COHORT_IDS)} cohorts ({COHORT_IDS[0]} .. {COHORT_IDS[-1]}) written to {OUTPUT_PATH} "
      f"in {(time.time() - _t0) / 60:,.1f} min")


# COMMAND ----------

# DBTITLE 1,Reload all written cohorts
claim_lab_monthly = spark.read.format("delta").load(OUTPUT_PATH).filter(F.col("COHORT_ID").isin(COHORT_IDS))

# COMMAND ----------

# DBTITLE 1,All cohorts per NPI (completeness checks + full table)
# Read the written table directly (cell 26 later reassigns claim_lab_monthly and drops NPI_NUMBER)
df_all_cohorts = spark.read.format("delta").load(OUTPUT_PATH)

# ---- Completeness checks ----
_ids_in_table  = sorted(r[0] for r in df_all_cohorts.select("COHORT_ID").distinct().collect())
_missing       = sorted(set(COHORT_IDS) - set(_ids_in_table))
_extra         = sorted(set(_ids_in_table) - set(COHORT_IDS))
df_all_cohorts = df_all_cohorts.filter(F.col("COHORT_ID").isin(COHORT_IDS))
_n_rows        = df_all_cohorts.count()
_n_keys        = df_all_cohorts.select(NPI_COL, "COHORT_ID").distinct().count()
_n_npis        = df_all_cohorts.select(NPI_COL).distinct().count()

print(f"Cohorts expected: {len(COHORT_IDS)} | in table: {len(_ids_in_table)} | "
      f"missing: {_missing or 'none'} | extra (not in this run): {_extra or 'none'}")
print(f"Rows: {_n_rows:,} | distinct (NPI, COHORT_ID): {_n_keys:,} | "
      f"duplicates: {_n_rows - _n_keys} | NPIs: {_n_npis} | Columns: {len(df_all_cohorts.columns)}")
display(df_all_cohorts.groupBy("COHORT_ID", "CUTOFF_DATE").count().orderBy("COHORT_ID"))

# ---- Full table: every NPI x cohort, all columns (keys and dates first) ----
_key_cols = [NPI_COL, "COHORT_ID", "COHORT_MONTH", "OFFSET_DAYS", "CUTOFF_DATE", "SVC_DT_M", "PULL_DT"]
_feat_cols = [c for c in df_all_cohorts.columns if c not in _key_cols]
display(df_all_cohorts.select(*_key_cols, *_feat_cols).orderBy(NPI_COL, "COHORT_ID"))

# COMMAND ----------

# DBTITLE 1,Provider ID mapping
hcp_npi_mapping = spark.read.format('delta').load(_QUERY_OUTPUT + HCP_NPI_MAPPING_TABLE)

hcp_npi_mapping_df = hcp_npi_mapping.select('NPI_NUMBER', 'PROVIDER_ID').distinct()
 
 
claim_lab_monthly = claim_lab_monthly.join(hcp_npi_mapping_df, on='NPI_NUMBER', how='left')
claim_lab_monthly = claim_lab_monthly.drop('NPI_NUMBER')

# COMMAND ----------

# DBTITLE 1,Write provider-level output
# New output path (Wenjie's provider_claim_lab_monthly_ZS is NOT touched)
PROVIDER_OUTPUT_PATH = _NOTEBOOK_OUTPUT + "provider_claim_lab_monthly_cohort"

claim_lab_monthly.write.format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .option("replaceWhere", "COHORT_ID IN (" + ", ".join(f"'{c}'" for c in COHORT_IDS) + ")") \
    .partitionBy("COHORT_ID") \
    .save(PROVIDER_OUTPUT_PATH)

print(f"Written to {PROVIDER_OUTPUT_PATH} ({len(COHORT_IDS)} cohorts)")

# COMMAND ----------

from pyspark.sql.functions import col, sum as spark_sum

null_counts = claim_lab_monthly.select([
    spark_sum(col(c).isNull().cast("int")).alias(f"{c}_null_count") for c in claim_lab_monthly.columns
])

display(null_counts)

# COMMAND ----------

# DBTITLE 1,Section: Validation
# MAGIC %md
# MAGIC ##5. Validation
# MAGIC
# MAGIC 1. **Offset = 0 parity (every cohort)**: rebuild the features at offset 0 for the test NPIs with the same functions, and compare every shared column with Wenjie's `claim_lab_monthly_ZS` for each month. Original base-month columns (no suffix) are compared with `_IN_LAST_1_MONTH`; original nulls are treated as 0. NPIs that only exist in the original for a month (no lab history yet) must be all zeros.
# MAGIC 2. **HCP trace (every cohort)**: for the busiest test NPI, recount raw lab claims per cohort and window in pandas (independent of Spark) and compare with the written features.

# COMMAND ----------

# DBTITLE 1,Offset=0 parity vs claim_lab_monthly_ZS (every cohort)
# ---- Validation 1: offset = 0 parity vs original claim_lab_monthly_ZS, every cohort ----
import pandas as pd

_npis = get_test_npis()
# 3.0 output AND the Lab_03 it was built from both come from the reference snapshot
# (HCP_REF_VOLUME, 00_cohort_config): the refreshed Lab_03 restates history, so comparing it with
# the 3.0 output would mix two data versions. Skip (not fail) if the snapshot is gone.
_ref_missing = hcp_ref_missing([HCP_REF_NOTEBOOK_OUTPUT + "claim_lab_monthly_ZS",
                                HCP_REF_QUERY_OUTPUT + "Lab_03"])
if _npis is None:
    print("Production mode — parity check skipped (runs on the test NPIs only)")
elif _ref_missing:
    print("SKIPPED — 3.0 reference table(s) missing, rerun when restored:\n  " + "\n  ".join(_ref_missing))
else:
    # Same cleaning as the load cell, on the reference Lab_03 (full history, no DATA_START_DATE)
    _df_lab_ref = apply_npi_filter(load_ref_input("Lab_03")
                                   .withColumn("PATIENT_ID", F.col("PATIENT_ID").cast("string")), NPI_COL)
    FAST_SOURCES["orig"] = lambda: _df_lab_ref
    for _k in [k for k in _FAST_LONG if k[0] == "orig"]:
        del _FAST_LONG[_k]
    _REF_MAX_DT = _df_lab_ref.agg(F.max(SVC_COL)).first()[0]

    _orig_all = (
        spark.read.format("delta").load(HCP_REF_NOTEBOOK_OUTPUT + "claim_lab_monthly_ZS")
        .filter(F.col(NPI_COL).isin(_npis))
        .withColumn("_M", F.date_format("SVC_DT_M", "yyyy-MM"))
    )
    _orig_months = {r[0] for r in _orig_all.select("_M").distinct().collect()}
    # Same cohort range, but complete-data rule evaluated at offset 0
    _months0 = [m for m in get_cohort_months(max_data_date=_REF_MAX_DT, offset_days=0) if m in _orig_months]
    pd_orig_all = _orig_all.filter(F.col("_M").isin(_months0)).toPandas()

    _skip = {"SVC_DT_M", "PULL_DT", "_M", NPI_COL}
    _orig_cols = [c for c in pd_orig_all.columns if c not in _skip]
    # Original column -> cohort-based column (base-month columns map to _IN_LAST_1_MONTH)
    _map = {oc: (oc if ("_IN_LAST_" in oc or oc.startswith("RUNNING_")) else f"{oc}_IN_LAST_1_MONTH")
            for oc in _orig_cols}

    # Same input as the original: reference Lab_03, full history (no DATA_START_DATE). This checks the feature
    # LOGIC of the engine that writes the output; the 2023 start is a config choice.
    # All parity months in ONE query (same engine as section 4), compared month by month in pandas.
    _cbs0 = {m: get_cohort_bounds(m, offset_days=0) for m in _months0}
    pd_new_all = build_all_cohorts_fast(list(_cbs0.values()), source="orig").toPandas()

    summary, mismatches = [], []
    for m in _months0:
        cb0 = _cbs0[m]
        pd_new = pd_new_all[pd_new_all["COHORT_ID"] == cb0["cohort_id"]].set_index(NPI_COL)
        pd_orig = pd_orig_all[pd_orig_all["_M"] == m].set_index(NPI_COL)

        common    = sorted(set(pd_new.index) & set(pd_orig.index))
        only_orig = sorted(set(pd_orig.index) - set(pd_new.index))
        only_new  = sorted(set(pd_new.index) - set(pd_orig.index))

        n_bad = 0
        for oc, nc in _map.items():
            for npi in common:
                o = pd_orig.at[npi, oc]
                o = 0.0 if pd.isna(o) else float(o)
                n = float(pd_new.at[npi, nc]) if nc in pd_new.columns else 0.0
                if builtins.abs(o - n) > 1e-9:   # builtins: abs is shadowed by pyspark import *
                    n_bad += 1
                    mismatches.append({"cohort": cb0["cohort_id"], "NPI": npi, "original_col": oc,
                                       "new_col": nc, "original": o, "new": n})

        # NPIs only in the original (no lab history yet at that month) must be all zeros
        nonzero_only_orig = 0
        if only_orig:
            _vals = pd_orig.loc[only_orig, _orig_cols].fillna(0).astype(float)
            nonzero_only_orig = int((_vals != 0).any(axis=1).sum())

        summary.append({"cohort_offset0": cb0["cohort_id"], "cutoff": f"{cb0['cutoff']:%Y-%m-%d}",
                        "npis_common": len(common), "npis_only_original": len(only_orig),
                        "only_original_nonzero": nonzero_only_orig, "npis_only_new": len(only_new),
                        "columns_compared": len(_map), "mismatching_cells": n_bad})

    df_parity = pd.DataFrame(summary)
    display(df_parity)
    _ok = (df_parity["mismatching_cells"].sum() == 0 and df_parity["only_original_nonzero"].sum() == 0
           and df_parity["npis_only_new"].sum() == 0)
    print(f"Cohorts compared: {len(df_parity)} | Mismatching cells: {df_parity['mismatching_cells'].sum()} | "
          f"{'PASS' if _ok else 'CHECK MISMATCHES'}")
    if mismatches:
        display(pd.DataFrame(mismatches).head(50))

# COMMAND ----------

# DBTITLE 1,HCP trace across all cohorts
# ---- Validation 2: HCP trace — raw lab claims recounted in pandas vs written features, every cohort ----
import pandas as pd

import builtins
TRACE_NPI = HCP_TRACE_NPIS["lab"]   # fixed trace HCP (00_cohort_config)
# If that HCP has no lab claims in this run (seen 2026-10-26 after the data refresh), the trace
# would only compare 0 with 0. Use the busiest HCP of the run instead and say so.
_trace_counts = {r[0]: r[1] for r in df_lab.groupBy(NPI_COL).count().collect()}
print("Lab claims per NPI in this run:", dict(sorted(_trace_counts.items(), key=lambda kv: -kv[1])))
if _trace_counts.get(TRACE_NPI, 0) == 0:
    _fallback = builtins.max(_trace_counts, key=_trace_counts.get)
    print(f"Trace NPI {TRACE_NPI} has no lab claims in this run -> using the busiest NPI {_fallback}")
    TRACE_NPI = _fallback

_raw = df_lab.filter(F.col(NPI_COL) == TRACE_NPI).select(SVC_COL, "TEST_TYPE", "STAGE").toPandas()
_raw[SVC_COL] = pd.to_datetime(_raw[SVC_COL])
_out = (spark.read.format("delta").load(OUTPUT_PATH)
        .filter((F.col(NPI_COL) == TRACE_NPI) & F.col("COHORT_ID").isin(COHORT_IDS))
        .toPandas().set_index("COHORT_ID"))

def _v(d, k):
    x = d.get(k, 0)
    return 0 if pd.isna(x) else int(x)

rows, bad = [], []
for m in COHORT_LIST:
    cb  = COHORT_BOUNDS[m]
    cid = cb["cohort_id"]
    feat = _out.loc[cid].to_dict() if cid in _out.index else {}   # no row = no history yet -> all 0
    row = {"COHORT_ID": cid, "CUTOFF_DATE": f"{cb['cutoff']:%Y-%m-%d}"}
    n_checks = n_bad = 0
    for w in LOOKBACK_WINDOWS:
        b = cb["window_bounds"][w]
        sel = _raw[(_raw[SVC_COL] > pd.Timestamp(b["start"])) & (_raw[SVC_COL] <= pd.Timestamp(b["end"]))]
        expected = {f"TOTAL_LAB_CLAIMS_IN_LAST_{w}_MONTH": len(sel)}
        for pcol, pvals in [("TEST_TYPE", TEST_TYPE_VALUES), ("STAGE", STAGE_VALUES)]:
            vc = sel[pcol].value_counts()
            for v in pvals:
                expected[f"TOTAL_LAB_CLAIMS_{clean_col_name(v)}_IN_LAST_{w}_MONTH"] = int(vc.get(v, 0))
        for fname, raw_n in expected.items():
            n_checks += 1
            if _v(feat, fname) != raw_n:
                n_bad += 1
                bad.append({"COHORT_ID": cid, "feature": fname, "raw": raw_n, "feature_value": _v(feat, fname)})
        row[f"{w}M_raw"]     = len(sel)
        row[f"{w}M_feature"] = _v(feat, f"TOTAL_LAB_CLAIMS_IN_LAST_{w}_MONTH")
    run_raw = int((_raw[SVC_COL] <= pd.Timestamp(cb["cutoff"])).sum())
    n_checks += 1
    if _v(feat, "RUNNING_TOTAL_LAB_CLAIMS") != run_raw:
        n_bad += 1
        bad.append({"COHORT_ID": cid, "feature": "RUNNING_TOTAL_LAB_CLAIMS", "raw": run_raw,
                    "feature_value": _v(feat, "RUNNING_TOTAL_LAB_CLAIMS")})
    row.update({"RUNNING_raw": run_raw, "RUNNING_feature": _v(feat, "RUNNING_TOTAL_LAB_CLAIMS"),
                "checks": n_checks, "mismatches": n_bad})
    rows.append(row)

trace = pd.DataFrame(rows)
print(f"Trace NPI: {TRACE_NPI} | cohorts: {len(trace)} | checks: {trace['checks'].sum()} | "
      f"mismatches: {trace['mismatches'].sum()}")
display(trace)
if bad:
    display(pd.DataFrame(bad).head(50))