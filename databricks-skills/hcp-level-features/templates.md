# HCP-Level Feature Notebooks: Code Templates

Reference for [SKILL.md](SKILL.md). These templates are generalised from NB02 (pattern A, the smallest example) and NB05 (pattern B). Replace `<...>` with your values. Everything not defined here (`F`, `assign_cohort_month`, `get_cohort_bounds`, `materialize`, `clean_col_name`, `NPI_COL`, `SVC_COL`, ...) comes from `00_cohort_config`.

## T1. Header cells

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```
```python
%run "../00_cohort_config"
```
```python
X_LOOKBACK_WINDOWS = <LOOKBACK_WINDOWS or the original last_i_month_list, e.g. [1, 3, 6, 12]>
_cohort_setting = (COHORT_MONTHS if COHORT_MONTHS is not None
                   else f"all {COHORT_ORIGIN[:7]} .. {COHORT_LAST[:7]} (complete data only)")
print(f"Offset: {OFFSET_DAYS} | Cohorts: {_cohort_setting} | Validation: {VALIDATION_MODE}")
```

If the notebook uses lookbacks other than `LOOKBACK_WINDOWS`, build the bounds with `_build_bounds(X_LOOKBACK_WINDOWS, cb["cutoff"], cohort_start, False, cb["offset_days"])`, or loop only over `X_LOOKBACK_WINDOWS` when you read `cb["window_bounds"]` (the config builds bounds for 1, 3, 6, 9 and 12).

## T2. Load cell

```python
import builtins, time
_VOLUME = ("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/"
           "kerendia_nba_3_volume/hcp_level_model/ops_pipeline/")
_QUERY_OUTPUT, _NOTEBOOK_OUTPUT = _VOLUME + "query_output/", _VOLUME + "notebook_output/"

df_x_raw = spark.read.format("delta").load(_QUERY_OUTPUT + "<SOURCE_TABLE>")
df_x = <same cleaning as the 3.0 original>(df_x_raw)

DATA_MAX_DT = df_x_raw.agg(F.max(SVC_COL)).first()[0]      # before any filter
df_x = apply_npi_filter(df_x, NPI_COL)                      # no-op in production
df_x_all = df_x                                             # full history: pivot values + parity only
df_x = df_x.filter(F.col(SVC_COL) >= F.to_date(F.lit(DATA_START_DATE)))

COHORT_LIST    = get_hcp_cohort_months()   # common end date of all HCP inputs; DATA_MAX_DT kept for parity
COHORT_BOUNDS  = {m: get_cohort_bounds(m) for m in COHORT_LIST}
COHORT_IDS     = [COHORT_BOUNDS[m]["cohort_id"] for m in COHORT_LIST]
PREVIEW_COHORT = COHORT_MONTH if COHORT_MONTH in COHORT_LIST else COHORT_LIST[0]
cb_preview     = COHORT_BOUNDS[PREVIEW_COHORT]

# Fixed pivot values from the FULL history -> same columns in every cohort and as 3.0
<GROUP>_VALUES = sorted(r[0] for r in df_x_raw.select("<PIVOT_COL>").distinct().collect() if r[0] is not None)
print(f"Data through {DATA_MAX_DT} -> {len(COHORT_LIST)} cohorts: {COHORT_LIST[0]} .. {COHORT_LIST[-1]}")
```

For patient tables, select the 3.1 validation table when `VALIDATION_MODE` is on, and the 3.0 table otherwise. Print which one was loaded.

## T3. Pattern A fast engine (month-key table)

```python
from datetime import date
_SEP = "\u0001"
_STAGE_PREFIX = _NOTEBOOK_OUTPUT + "<output_name>_stage_"     # used by materialize() in production
_GROUPS = [("<PIVOT_COL_1>", <GROUP1>_VALUES), ("<PIVOT_COL_2>", <GROUP2>_VALUES)]
TOTAL_NAME = "TOTAL_<X>_CLAIMS"

def build_long(df, offset_days):
    d = (df.filter(F.col(NPI_COL).isNotNull())
           .withColumn("_CM", assign_cohort_month(F.col(SVC_COL), offset_days)))
    keys = [F.lit("total" + _SEP)] + [F.concat(F.lit(g + _SEP), F.col(g)) for g, _ in _GROUPS]
    # Conditional groups: F.when(<condition>, F.concat(...)) -> null key when the condition is false
    return (d.select(NPI_COL, "_CM", F.explode(F.array(*keys)).alias("KEY"))
             .filter(F.col("KEY").isNotNull())
             .groupBy(NPI_COL, "_CM", "KEY").agg(F.count(F.lit(1)).alias("N")))

_W = [str(w) for w in sorted(X_LOOKBACK_WINDOWS)]
COUNT_SPECS = []                                   # (pivot key, output column), fixed order
for _t in _W + ["RUN"]:
    _pre = "RUNNING_" if _t == "RUN" else ""
    _sfx = "" if _t == "RUN" else f"_IN_LAST_{_t}_MONTH"
    COUNT_SPECS.append((f"total{_SEP}{_SEP}{_t}", f"{_pre}{TOTAL_NAME}{_sfx}"))
    for _g, _vals in _GROUPS:
        COUNT_SPECS += [(f"{_g}{_SEP}{v}{_SEP}{_t}", f"{_pre}{TOTAL_NAME}_{clean_col_name(v)}{_sfx}") for v in _vals]

def _cm_of(d, off):
    return (d - timedelta(days=off - 1)).replace(day=1) if off > 0 else d.replace(day=1)

def _window_months(b, off):
    s, e = datetime.strptime(b["start"], "%Y-%m-%d"), datetime.strptime(b["end"], "%Y-%m-%d")
    lo, hi = _cm_of(s + timedelta(days=1), off), _cm_of(e, off)
    if _cm_of(s, off) == lo or _cm_of(e + timedelta(days=1), off) == hi:
        raise ValueError(f"Window {b} does not line up with cohort months at offset {off}")
    return lo.date(), hi.date()

FAST_SOURCES = {"run": lambda: df_x, "orig": lambda: df_x_all}
_FAST_LONG = {}
def get_long(off, source="run"):
    if (source, off) not in _FAST_LONG:
        _FAST_LONG[(source, off)] = materialize(build_long(FAST_SOURCES[source](), off), f"long_{source}_offset{off}")
    return _FAST_LONG[(source, off)]

_EARLIEST = date(1900, 1, 1)
_META_COLS = ["COHORT_ID", "COHORT_MONTH", "OFFSET_DAYS", "CUTOFF_DATE", "SVC_DT_M", "PULL_DT"]

def build_all_cohorts_fast(cbs, source="run"):
    offs = {cb["offset_days"] for cb in cbs}
    if len(offs) != 1:
        raise ValueError(f"All cohorts must share one offset, got {offs}")
    off = offs.pop()
    tag_rows, meta_rows = [], []
    for cb in cbs:
        cm = datetime.strptime(f"{cb['cohort_month']}-01", "%Y-%m-%d").date()
        for w in X_LOOKBACK_WINDOWS:
            lo, hi = _window_months(cb["window_bounds"][w], off)
            if hi != cm:
                raise ValueError(f"{cb['cohort_id']}: window {w} ends in {hi}, expected {cm}")
            tag_rows.append((cb["cohort_id"], str(w), lo, cm))
        tag_rows.append((cb["cohort_id"], "RUN", _EARLIEST, cm))
        meta_rows.append((cb["cohort_id"], cb["cohort_month"], int(off), cb["cutoff"].strftime("%Y-%m-%d")))
    tags = F.broadcast(spark.createDataFrame(tag_rows, "_COHORT string, _TAG string, _LO date, _HI date"))
    df = (get_long(off, source)
          .join(tags, (F.col("_CM") >= F.col("_LO")) & (F.col("_CM") <= F.col("_HI")))
          .withColumn("_PK", F.concat(F.col("KEY"), F.lit(_SEP), F.col("_TAG")))
          .groupBy(NPI_COL, "_COHORT").pivot("_PK", [k for k, _ in COUNT_SPECS]).agg(F.sum("N"))
          .toDF(NPI_COL, "_COHORT", *[c for _, c in COUNT_SPECS])
          .na.fill(0))
    df = add_pct_features(df)                       # row-wise: cohorts don't mix
    meta = (spark.createDataFrame(meta_rows, "COHORT_ID string, COHORT_MONTH string, OFFSET_DAYS int, CUTOFF_DATE string")
            .withColumns({"SVC_DT_M": F.to_timestamp(F.concat(F.col("COHORT_MONTH"), F.lit("-01"))),
                          "PULL_DT": F.current_date()}))
    feat = [c for c in df.columns if c not in (NPI_COL, "_COHORT")]
    return (df.join(F.broadcast(meta), F.col("_COHORT") == F.col("COHORT_ID"))
              .select(NPI_COL, *feat, *_META_COLS))
```

PCT helper (one `select`, no loop of `withColumn`):

```python
def add_pct_features(df):
    cols, exprs = df.columns, []
    for w in X_LOOKBACK_WINDOWS:
        sfx, denom = f"_IN_LAST_{w}_MONTH", f"{TOTAL_NAME}_IN_LAST_{w}_MONTH"
        for c in cols:
            if c.endswith(sfx) and c != denom:
                exprs.append(F.when(F.col(denom) != 0, F.col(c) / F.col(denom)).otherwise(F.lit(0.0)).alias(f"PCT_{c}"))
    return df.select("*", *exprs)
```

## T4. Pattern B fast engine (date-level feature rows)

```python
def build_feature_rows(df_in, offset_days=None):
    """(KEY_COL, SVC_DT, FEATURE, N). FEATURE = final cleaned base column name.
    Do the claim-level joins of the original here (patient tables on PATIENT_ID + assign_cohort_month)."""
    rx = df_in.withColumn("_M", assign_cohort_month(F.col(SVC_COL), offset_days))
    ...
    return rows_a.unionByName(rows_b)   # .groupBy(KEY_COL, SVC_COL, "FEATURE").agg(F.sum("N").alias("N"))

_STAGE_PREFIX = _NOTEBOOK_OUTPUT + "<output_name>_feature_rows_"
df_feat = materialize(build_feature_rows(df_x, OFFSET_DAYS), f"offset{OFFSET_DAYS}")
FEATURE_VALUES = sorted(r[0] for r in df_feat.select("FEATURE").distinct().collect())  # or 3.0 column list

def build_cohort(cb, L=None):
    L = df_feat if L is None else L
    cutoff = F.to_date(F.lit(cb["cutoff"].strftime("%Y-%m-%d")))
    sfx = F.array(F.lit("RUNNING"), *[
        F.when(F.col(SVC_COL) > F.to_date(F.lit(cb["window_bounds"][w]["start"])), F.lit(f"_IN_LAST_{w}_MONTH"))
        for w in X_LOOKBACK_WINDOWS])
    long = (L.filter(F.col(SVC_COL) <= cutoff)
             .withColumn("_s", F.explode(sfx)).filter(F.col("_s").isNotNull())
             .withColumn("FEATURE_OUT", F.when(F.col("_s") == "RUNNING", F.concat(F.lit("RUNNING_"), F.col("FEATURE")))
                                         .otherwise(F.concat(F.col("FEATURE"), F.col("_s")))))
    win = [f"{f}_IN_LAST_{w}_MONTH" for w in X_LOOKBACK_WINDOWS for f in FEATURE_VALUES]
    run = [f"RUNNING_{f}" for f in FEATURE_VALUES]
    out = long.groupBy("<KEY_COL>").pivot("FEATURE_OUT", values=win + run).agg(F.sum("N")).na.fill(0)
    out = add_pct_features(out.select("<KEY_COL>", *win, *run))
    return out.withColumns({
        "COHORT_ID": F.lit(cb["cohort_id"]), "COHORT_MONTH": F.lit(cb["cohort_month"]),
        "OFFSET_DAYS": F.lit(cb["offset_days"]), "CUTOFF_DATE": F.lit(cb["cutoff"].strftime("%Y-%m-%d")),
        "SVC_DT_M": F.to_timestamp(F.lit(f"{cb['cohort_month']}-01")), "PULL_DT": F.current_date()})
```

`build_cohort` is the reference (exact dates, `SVC_DT > start`). The output is written with the all-cohorts engine of `00_cohort_config` (as NB04/NB05):

```python
OUTPUT_COLS = build_cohort(cb_preview).columns          # schema only
_FEAT_MONTHS = {}
def get_feat_months(L, off, name):
    if name not in _FEAT_MONTHS:
        _FEAT_MONTHS[name] = materialize(feature_rows_to_months(L, "<KEY_COL>", off), f"months_{name}")
    return _FEAT_MONTHS[name]

def build_all_cohorts_fast(cbs, L=None, name="run"):
    L = df_feat if L is None else L
    off = cbs[0]["offset_days"]
    wide = build_all_cohorts_from_months(get_feat_months(L, off, f"{name}_offset{off}"), cbs, "<KEY_COL>",
                                         FEATURE_VALUES, X_LOOKBACK_WINDOWS)
    return add_cohort_meta(add_pct_features(wide), cbs).select(*OUTPUT_COLS)
```

Add the check cell (fast vs `build_cohort`, first and last cohort, same order, types and values). For offset-0 parity, rebuild `df_feat` with `offset_days=0` and the original's inputs and call `build_all_cohorts_fast(cbs0, df_feat0, name="parity")` once for all months.

## T5. Write all cohorts (one write) + provider output

```python
OUTPUT_PATH = _NOTEBOOK_OUTPUT + "<output_name>_cohort"
_ids_sql = ", ".join(f"'{c}'" for c in COHORT_IDS)
_t0 = time.time()
_df_out = build_all_cohorts_fast([COHORT_BOUNDS[m] for m in COHORT_LIST])
OUTPUT_COLS = _df_out.columns
(_df_out.write.format("delta").mode("overwrite")
    .option("mergeSchema", "true")
    .option("replaceWhere", f"COHORT_ID IN ({_ids_sql})")
    .partitionBy("COHORT_ID").save(OUTPUT_PATH))
print(f"{len(COHORT_IDS)} cohorts written to {OUTPUT_PATH} in {(time.time() - _t0) / 60:,.1f} min")

# Provider level (when the source is NPI-level)
_map = (spark.read.format("delta").load(_QUERY_OUTPUT + "kerendia_nba_3_0_npi_bhid_mapping")
        .select("NPI_NUMBER", "PROVIDER_ID").distinct())
(spark.read.format("delta").load(OUTPUT_PATH).filter(F.col("COHORT_ID").isin(COHORT_IDS))
    .join(_map, on="NPI_NUMBER", how="left").drop("NPI_NUMBER")
    .write.format("delta").mode("overwrite").option("mergeSchema", "true")
    .option("replaceWhere", f"COHORT_ID IN ({_ids_sql})")
    .partitionBy("COHORT_ID").save(_NOTEBOOK_OUTPUT + "provider_<output_name>_cohort"))
```

## T6. Completeness checks

```python
df_all = spark.read.format("delta").load(OUTPUT_PATH)
_ids   = sorted(r[0] for r in df_all.select("COHORT_ID").distinct().collect())
df_all = df_all.filter(F.col("COHORT_ID").isin(COHORT_IDS)).select(*OUTPUT_COLS)
_n, _k = df_all.count(), df_all.select(NPI_COL, "COHORT_ID").distinct().count()
_nulls = builtins.sum(v or 0 for v in df_all.agg(
    *[F.sum(F.col(c).isNull().cast("int")).alias(f"_n{i}") for i, c in enumerate(OUTPUT_COLS)]).first())
print(f"missing: {sorted(set(COHORT_IDS) - set(_ids)) or 'none'} | extra: {sorted(set(_ids) - set(COHORT_IDS)) or 'none'} | "
      f"rows {_n:,} | duplicates {_n - _k} | null cells {_nulls:,} | columns {len(OUTPUT_COLS):,}")
display(df_all.groupBy("COHORT_ID", "CUTOFF_DATE").count().orderBy("COHORT_ID"))
```

## T7. Offset-0 parity vs 3.0 (every cohort)

```python
import numpy as np, pandas as pd
_npis = get_test_npis()
_orig = (spark.read.format("delta").load(_NOTEBOOK_OUTPUT + "<3.0 table>")
         .filter(F.col(NPI_COL).isin(_npis)).withColumn("_M", F.date_format("SVC_DT_M", "yyyy-MM")))
_months = {r[0] for r in _orig.select("_M").distinct().collect()}
PARITY_MONTHS = [m for m in get_cohort_months(max_data_date=DATA_MAX_DT, offset_days=0) if m in _months]
pd_orig = _orig.filter(F.col("_M").isin(PARITY_MONTHS)).toPandas()
_cbs0 = {m: get_cohort_bounds(m, offset_days=0) for m in PARITY_MONTHS}
pd_new = build_all_cohorts_fast(list(_cbs0.values()), source="orig").toPandas()   # original inputs

_skip = {"SVC_DT_M", "PULL_DT", "_M", NPI_COL, "PROVIDER_ID", *_META_COLS}
def _num(df):
    obj = list(df.columns[(df.dtypes == object).values])
    if obj:
        df = df.copy(); df[obj] = df[obj].apply(pd.to_numeric, errors="coerce")
    return df.astype(float).fillna(0)                 # 3.0 null == 3.1 zero

rows = []
for m in PARITY_MONTHS:
    n = pd_new[pd_new["COHORT_ID"] == _cbs0[m]["cohort_id"]].set_index(NPI_COL)
    o = pd_orig[pd_orig["_M"] == m].set_index(NPI_COL)
    common = sorted(set(n.index) & set(o.index))
    cols = sorted((set(n.columns) & set(o.columns)) - _skip)
    bad = ~np.isclose(_num(o.loc[common, cols]).values, _num(n.loc[common, cols]).values, rtol=1e-9, atol=1e-9)
    rows.append({"cohort": _cbs0[m]["cohort_id"], "npis_common": len(common),
                 "npis_only_original": len(set(o.index) - set(n.index)), "npis_only_new": len(set(n.index) - set(o.index)),
                 "columns": len(cols), "cells": int(bad.size), "mismatches": int(bad.sum())})
display(pd.DataFrame(rows))
```

Variants used in the notebooks:
* **Run only in validation mode:** wrap the cell in `if _npis is None: print("Production mode: parity check skipped") else: ...`.
* **"orig" source:** before the build, register the original inputs: full history (`df_x_all`, no `DATA_START_DATE`) and the 3.0 patient tables restricted to the test HCPs' patients, e.g. `FAST_SOURCES["orig"] = lambda: (df_rx_all, _pat30)` (NB01) or `lambda off: (_dx0, add_patient_stage(_dx0, off, pat_df=_pat30))` (NB03). Pattern B notebooks rebuild `df_feat0 = materialize(build_feature_rows(..., 0), "offset0")` and call `build_cohort(cb0, df_feat0, ...)` per month.
* **3.0 table at provider level (NB03-NB05; NB01 and NB02 compare at NPI level):** map `pd_new[NPI_COL]` to `PROVIDER_ID` with `kerendia_nba_3_0_npi_bhid_mapping` and index both sides on `PROVIDER_ID`.
* **3.0 base-month columns without a suffix (NB03-NB05):** map them before comparing: `_map = {oc: oc if ("_IN_LAST_" in oc or oc.startswith("RUNNING_")) else f"{oc}_IN_LAST_1_MONTH" for oc in orig_cols}`; then compare `o[list(_map)]` with `n[list(_map.values())]`.

Add these checks when they apply: original-only window columns must be all 0, original-only NPIs must be all 0, known quirks are counted in their own column, and the first 50 mismatches are listed (cohort, NPI, column, original, new).

## T8. HCP trace (independent pandas recount)

```python
TRACE_NPI = df_x.groupBy(NPI_COL).count().orderBy(F.desc("count")).first()[NPI_COL]
_raw = df_x.filter(F.col(NPI_COL) == TRACE_NPI).select(SVC_COL, "<PIVOT_COLS>").toPandas()
_raw[SVC_COL] = pd.to_datetime(_raw[SVC_COL])
_out = (spark.read.format("delta").load(OUTPUT_PATH)
        .filter((F.col(NPI_COL) == TRACE_NPI) & F.col("COHORT_ID").isin(COHORT_IDS)).toPandas().set_index("COHORT_ID"))
def _v(d, k):
    x = d.get(k, 0)
    return 0 if pd.isna(x) else int(x)

bad = []
for m in COHORT_LIST:
    cb = COHORT_BOUNDS[m]; feat = _out.loc[cb["cohort_id"]].to_dict() if cb["cohort_id"] in _out.index else {}
    for w in X_LOOKBACK_WINDOWS:
        b = cb["window_bounds"][w]
        sel = _raw[(_raw[SVC_COL] > pd.Timestamp(b["start"])) & (_raw[SVC_COL] <= pd.Timestamp(b["end"]))]
        expected = {f"{TOTAL_NAME}_IN_LAST_{w}_MONTH": len(sel)}
        # + one entry per pivot value: int((sel["<PIVOT_COL>"] == v).sum())
        for k, v in expected.items():
            if _v(feat, k) != v:
                bad.append({"cohort": cb["cohort_id"], "feature": k, "raw": v, "written": feat.get(k)})
    run = int((_raw[SVC_COL] <= pd.Timestamp(cb["cutoff"])).sum())
    if _v(feat, f"RUNNING_{TOTAL_NAME}") != run:
        bad.append({"cohort": cb["cohort_id"], "feature": f"RUNNING_{TOTAL_NAME}", "raw": run,
                    "written": feat.get(f"RUNNING_{TOTAL_NAME}")})
print(f"Trace NPI {TRACE_NPI}: {len(bad)} mismatches")
if bad: display(pd.DataFrame(bad).head(50))
```
