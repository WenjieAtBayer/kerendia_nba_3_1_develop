# Fix: Replace chained `.withColumn()` with batch `.withColumns()` to prevent RecursionError

**Date:** 2026-10-12  
**Author:** Saurabh Modi  
**Job Run:** [332252756505567](https://dbc-7281de76-54c6.cloud.databricks.com/?o=2553213839599380#job/505043739538330/run/332252756505567)

---

## Problem

The `DX_Features` and `RX_Features` tasks in the **Patient Features Pipeline (10K HCP Test)** job failed with:

```
RecursionError: maximum recursion depth exceeded
```

Each `.withColumn()` call in a loop adds a nested `WithColumns` node to PySpark's logical plan. With hundreds of unique DX/RX event types × 5 lag windows, the plan reached **1,373+ levels deep** — exceeding Python's recursion limit when Spark Connect (DBR 18.x) serialized the plan.

## Root Cause

Two code patterns in the Frequency feature cells were responsible:

1. **`apply_lag()` function** (Frequency Sub-B): Looped `result = result.withColumn(...)` for every `freq_col × window` combination.
2. **Change in Frequency loop** (Frequency Sub-C): Looped `freq_subC = freq_subC.withColumn(...)` for every `event × change_window` combination.

Both patterns compound: Sub-B builds a deep plan, and Sub-C starts from that already-deep DataFrame and adds more layers.

## Fix

Replaced all chained `.withColumn()` loops with single `.withColumns(dict)` calls, which add all columns in **one flat plan node** regardless of event count.

### Before

```python
# apply_lag — one .withColumn() per column × window
result = df
for col_name in freq_cols:
    for n_months in windows:
        result = result.withColumn(
            f"{col_name}_IN_LAST_{n_months}_MONTH",
            F.sum(col_name).over(w.rowsBetween(-n_months + 1, 0))
        )
return result
```

### After

```python
# apply_lag — single .withColumns() call
new_cols = {}
for col_name in freq_cols:
    for n_months in windows:
        new_cols[f"{col_name}_IN_LAST_{n_months}_MONTH"] = (
            F.sum(col_name).over(w.rowsBetween(-n_months + 1, 0))
        )
return df.withColumns(new_cols)
```

## Notebooks Changed

| Notebook | Cells Changed | Function / Block |
|---|---|---|
| `DX_Patient_Features` | 13, 14 | `apply_lag()`, Change in Frequency loop |
| `RX_Patient_Features` | 16, 17 | `apply_lag()`, Change in Frequency loop |
| `PX_Patient_Features` | 13, 14 | `apply_lag()`, Change in Frequency loop |
| `LAB_Patient_Features` | 13, 14 | `apply_lag()`, Change in Frequency loop |

## Why All Four Notebooks

PX and LAB succeeded in the failed run only because they have fewer distinct event types (~procedures and ~2 lab test types). The same anti-pattern would fail at scale as event counts grow. Hospitalization cells (DX/PX only) were left as-is — they iterate over just 2 columns × 3 windows = 6 calls, well within safe limits.

## Impact

**No functional change** — output columns, names, and values are identical. Only the internal Spark logical plan structure changes.

## Verification

Repair the failed job run to re-execute only the failed tasks:

```bash
databricks jobs repair-run 332252756505567 --rerun-all-failed-tasks
```
