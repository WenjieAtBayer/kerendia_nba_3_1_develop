---
name: hcp-level-features
description: Build, refactor, or validate Kerendia NBA 3.1 HCP-level claim features (one row per NPI or PROVIDER_ID per COHORT_ID, with _IN_LAST_N_MONTH, RUNNING_ and PCT_ columns on offset-aligned cohort windows). Read this skill when the user asks to run the HCP-level feature notebooks for a specific use case (another offset, specific cohorts, their own HCP list, production), create a new HCP-level feature notebook, port a 3.0 monthly claims notebook (Wenjie's 03_HCP_Level_Features) to cohort/offset windows, add a feature family to notebooks 01-05 in hcp_level_features, or check HCP features against the 3.0 output (offset-0 parity, HCP trace).
---

# HCP-Level Claim Features (Kerendia NBA 3.1)

This skill covers how the five cohort notebooks in `kerendia_nba_3_1_develop_clone/hcp_level_features` were built, so the same method can be reused for any new HCP-level feature. Follow the workflow below. Copy code from [templates.md](templates.md). Use [notebooks.md](notebooks.md) for the source tables, feature families, output paths and known quirks of each notebook.

**To run the existing notebooks for a use case** (another offset, some cohorts, a custom HCP list, production, one extra feature), follow [runbook.md](runbook.md): pin down the parameters, check the dependencies (inputs, patient tables at the same offset), Run all each notebook, check the results, report.

## 1. What an HCP-level feature notebook produces

* **Grain:** one row per `NPI_NUMBER` (or `PROVIDER_ID`) per `COHORT_ID`. The 3.0 grain was one row per NPI per calendar month (`SVC_DT_M`).
* **Feature columns** (count of claims, patients or events):
  * `<FEATURE>_IN_LAST_<N>_MONTH`: date-range window ending at the cohort cutoff.
  * `RUNNING_<FEATURE>`: everything from `DATA_START_DATE` up to the cutoff.
  * `PCT_<FEATURE>_IN_LAST_<N>_MONTH`: feature / total of the same window, 0.0 when the total is 0.
  * Notebook-specific extras: AVG, DIFF (`_IN_LAST_3_6_MONTH`), RATIO (`RATIO_..._IN_PRIOR_3_LAST_3_MONTH`), `SGLT2_WO_INVOKANA_300MG` (NB01 only).
* **Metadata columns** (same names, order and types in every notebook): `COHORT_ID` (e.g. `2025-02_offset7`), `COHORT_MONTH` (`YYYY-MM`), `OFFSET_DAYS` (int), `CUTOFF_DATE` (string `YYYY-MM-DD`), `SVC_DT_M` (timestamp = first day of the cohort month, kept for `99_Combine_Physician_Data`), `PULL_DT` (current_date).
* **Storage:** Delta, `partitionBy("COHORT_ID")`, written with `replaceWhere` on the cohorts of this run, so other cohorts and offsets in the table are kept. Never overwrite Wenjie's 3.0 tables. Always write to a new `*_cohort` path.
* **Null handling:** features are 0 (never null) when there is no activity. The 3.0 tables often had nulls, so comparisons treat null as 0.

## 2. Rules from the user (follow them every time)

1. **Keep the feature logic identical to the 3.0 original.** Only the time grain (cohort month and offset windows) and the config change. If the original has a bug, reproduce it, document it as a finding, and ask the user before you fix it. (Source: the user.)
2. **Use one shared config.** Run `%run "../00_cohort_config"` after `00_connection`. Never hardcode offsets, dates, windows or test NPIs in a feature notebook. Shared values live in the config cell "HCP shared constants": `HCP_QUERY_OUTPUT` / `HCP_NOTEBOOK_OUTPUT` (paths; notebooks alias them as `_QUERY_OUTPUT` / `_NOTEBOOK_OUTPUT`), `HCP_BRANDS` / `HCP_BRAND_FILTER`, `HCP_LOOKBACK_WINDOWS[<rx|lab|dx|claims|nps>]`, `get_patient_table(key)` (mode-aware) and `get_patient_table_30(key)` (3.0 table for parity), `HCP_NPI_MAPPING_TABLE`, `HCP_RX_HISTORY_START`; trace HCPs in `HCP_TRACE_NPIS[<key>]` (validation cell). A new notebook adds its own key to these dicts.
3. **Offset rule:** the offset-th day starts the NEW cohort. With offset 7, the February cohort runs from Feb 7 to Mar 6 (cutoff = month end + offset - 1). Offset 0 = calendar months and must reproduce 3.0 exactly.
4. **Run all cohorts in one run:** every cohort from `COHORT_ORIGIN` (2025-01) to `COHORT_LAST` whose cutoff is on or before the common last service date of all HCP inputs (complete windows only). Use `get_hcp_cohort_months()` from the config (earliest end over `HCP_SOURCE_TABLES`; add new inputs there), not `get_cohort_months(max_data_date=<own source>)`, so every table has the same `COHORT_ID`s. Pivot values are fixed, so every cohort has the same columns.
5. **`DATA_START_DATE = 2023-01-01` applies to every feature, `RUNNING_` included** (team decision, option B). Keep the full history only in a `df_<x>_all` variable for fixed pivot values and offset-0 parity. All five notebooks apply it (NB04 filters the feature rows, NB05 the counted claims; NB05 keeps the full history for first-start dates). Any "first-ever" logic must keep looking at the full history.
6. **Don't mix calendar-month patient tables with offset-month claims.** Patient-journey tables must be built at the same offset as the HCP features before the outputs are final.
7. **Validation mode first:** `VALIDATION_MODE = True` runs on the 10 test NPIs. Production (`False`) runs on all HCPs. Both paths must run the same code.
8. **Work in the CLONE folder** (`kerendia_nba_3_1_develop_clone`). Push to the Git folder (`kerendia_nba_3_1_develop`, branch `dev/hcp-claims-features`) only when the user asks.
9. **Confirm open business questions with Wenjie** (null vs 0, data leaks, quirks). List them in a findings cell. Don't decide them yourself.

## 3. Shared config: `00_cohort_config` (ID 4005178662472033)

Path: `/Users/patricio.guledjian.ext@bayer.com/kerendia_nba_3_1_develop_clone/00_cohort_config`. It provides:

| Name | Purpose |
| --- | --- |
| `OFFSET_DAY` / `OFFSET_DAYS` (7), `DATA_START_DATE`, `COHORT_ORIGIN`, `COHORT_LAST`, `COHORT_MONTH` (preview), `COHORT_MONTHS` (None = all), `VALIDATION_MODE` | Global parameters |
| `NPI_COL = "NPI_NUMBER"`, `SVC_COL = "SVC_DT"`, `LOOKBACK_WINDOWS = [1,3,6,12]` (= 3.0 windows, same in all 5 notebooks; 9m dropped 2026-10-23), `AVG_EXTRA_MONTH = True` | HCP constants |
| `assign_cohort_month(col, offset_days=None)` | Date -> cohort month (`trunc(date_sub(d, off-1), 'month')`, or `trunc` at offset 0). Always pass `cb["offset_days"]` inside cohort code. |
| `get_cohort_months(max_data_date, offset_days)` | Complete cohorts to process |
| `get_cohort_bounds(month, offset_days)` | `cb` dict: `cohort_month`, `cohort_id`, `offset_days`, `cutoff` (datetime), `window_bounds`, `avg_window_bounds` (`{N: {"start", "end"}}`, start exclusive, end inclusive) |
| `get_test_npis()`, `apply_npi_filter(df, npi_col)`, `apply_hcp_filter(df)` | Validation filters (no-op in production). `apply_npi_filter` = HCP notebooks. `apply_hcp_filter` = patient-level notebooks. |
| `clean_col_name(v)` | 3.0 column cleaning: `", "->" "`, strip `()`, `+->and`, `/->" or"`, `- -> _`, space -> `_`, `__ -> _`, upper |
| `pivoted_counts`, `filter_to_window`, `build_feature_group`, `build_total_col` | Step-by-step (slow) helpers. Use them for the reference version. |
| `materialize(df, name, stage_prefix=None)` | Serverless replacement for `.cache()`. Keeps data in memory in validation mode and writes a staging Delta table `_STAGE_PREFIX + name` in production. Set `_STAGE_PREFIX` in the notebook. |

Window math (check with `cb` before you build):

| Cohort | Offset | Cutoff | Last 1m | Last 3m |
| --- | --- | --- | --- | --- |
| 2025-02 | 0 | 2025-02-28 | (2025-01-31, 2025-02-28] | (2024-11-30, 2025-02-28] |
| 2025-02 | 7 | 2025-03-06 | (2025-02-06, 2025-03-06] | (2024-12-06, 2025-03-06] |

At offset 0 the window start snaps to calendar months. At offset > 0, start = cutoff - N months. AVG windows are one month wider when `AVG_EXTRA_MONTH = True` (3.0 `step3_lag_avg` used `rowsBetween(-i, 0)`).

## 4. Standard notebook layout

Use the same sections in every notebook. The user reads them top to bottom.

0. Title (markdown): what the notebook does, 3.0 source path, output grain, output tables.
1. "What this notebook does, in plain words" + a feature-family table (question answered, extra table joined, column prefix).
2. Connection and config: `%run 00_connection` -> `%run "../00_cohort_config"` -> config confirmation print. `00_connection` may restart Python, so nothing goes before it.
3. Input tables: one load cell, then one display cell per table (filtered to the run's NPIs or their patients).
4. Claim-level walkthrough of what the original builds (display cells), then the original output for one test HCP.
5. Walkthrough findings table (`#`, finding, evidence, impact on the refactor). Mark the items to confirm with Wenjie.
6. Cohort features: functions + a preview on one cohort (`cb_preview`).
7. Fast engine + a check cell that compares the fast engine with the step-by-step version on 2 cohorts (0 mismatches, same column order and types).
8. Build and write all cohorts in one query and **one write** (`replaceWhere COHORT_ID IN (...)`, all five notebooks since 2026-10-23) -> completeness checks -> provider mapping and provider-level output.
9. Validation: offset-0 parity vs the 3.0 table (every cohort) + HCP trace (pandas recount from raw claims, every cohort).
10. Status and open items (flags for Wenjie).

## 5. Workflow for a new or ported feature notebook

1. **Read the 3.0 original end to end.** List inputs, joins, filters, feature families, pivot columns, column cleaning, lookbacks (`last_i_month_list`), `step2_fill_missing` / `step3_lag*` usage, the final output table and its column count. Record where monthly logic is hardcoded (`date_trunc('MM')`, `sequence(... interval 1 month)`, `rowsBetween`).
2. **Profile the inputs** on the test NPIs: grain, date range, null keys, distinct pivot values, duplicates. Check whether patient tables are monthly (`SVC_DT_M`) and at which offset they were built.
3. **Write the findings cell** before the refactor.
4. **Load cell:** read the source, use the original cleaning, `DATA_MAX_DT` from the unfiltered source, `apply_npi_filter`, then `df_x_all = df_x` and `df_x = df_x.filter(SVC >= DATA_START_DATE)`. Build `COHORT_LIST`, `COHORT_BOUNDS`, `COHORT_IDS`, `cb_preview`.
5. **Fixed pivot values** from the full history (`df_x_all`, or the 3.0 output column list) so every cohort has the same columns and matches 3.0.
6. **Step-by-step version** (`build_cohort_slow(cb)`) with the config helpers. This is the readable reference.
7. **Fast engine.** Choose the pattern (section 6). Then add the check cell: fast = slow on the first and last cohort.
8. **Write all cohorts**, then the completeness checks: all `COHORT_IDS` present, rows = distinct (key, COHORT_ID), 0 nulls, same columns per cohort.
9. **Provider mapping** when the source is NPI-level: left join `kerendia_nba_3_0_npi_bhid_mapping` (`NPI_NUMBER`, `PROVIDER_ID` distinct), drop `NPI_NUMBER`, write `provider_<name>_cohort` with the same `replaceWhere`.
10. **Validate:** offset-0 parity and the HCP trace (section 8). Report the results in a table: cohorts, columns, cells compared, mismatches.
11. **Update the status cell** and tell the user what is still open.

## 6. Fast engine patterns (serverless has no cache)

The step-by-step version filters and pivots the claims once per feature group x window. On serverless that rescans the source each time (NB01: about 140 scans, 10-15 min per cohort). The fast engines read the claims once.

**Pattern A: month-key table (NB01, NB02, NB03).** Use it when every feature is a count that can be added up by cohort month.
1. `build_long(df, off)`: tag each claim with `_CM = assign_cohort_month(SVC_DT, off)`, build one key per feature group (`group + SEP + value`, null value -> null key -> dropped, same as pivot), `explode`, then `groupBy(NPI, _CM, KEY).count() as N`. Run `materialize()` once per (source, offset).
2. `_window_months(bounds, off)` turns each window into a cohort-month range and raises if the window doesn't line up with cohort months.
3. `build_all_cohorts_fast(cbs)`: broadcast a tag table (`_COHORT, _TAG, _LO, _HI`, where `_TAG` = window or `RUN` with `_LO = 1900-01-01`), join on `_CM BETWEEN _LO AND _HI`, pivot `KEY + SEP + _TAG` with a fixed `COUNT_SPECS` list, `na.fill(0)`, add the derived columns, then join the metadata. One query plans the ~4,500 columns once instead of once per cohort.

**Pattern B: date-level feature rows (NB04, NB05), then the same all-cohorts engine.** Use it when features come from claim-level joins (patient stage, same-day lab, first-start dates) or when the 3.0 cleaning differs from `clean_col_name`.
1. `build_feature_rows(...)` returns `(KEY_COL, SVC_DT, FEATURE, N)`, with FEATURE already being the final cleaned base column name. Run `materialize()` once. Distinct counts (NB05 visits, new patients) must already be one row per patient per cohort month here.
2. `FEATURE_VALUES` = fixed sorted list (from the feature rows or from the 3.0 output columns).
3. `build_cohort(cb)` (reference only): filter `SVC_DT <= cutoff`, explode a suffix array (`RUNNING` + `_IN_LAST_N_MONTH` when `SVC_DT > window start`), pivot with the fixed list, `na.fill(0)`, PCT, metadata.
4. `build_all_cohorts_fast(cbs)` (writes the output): shared engine in `00_cohort_config`: `feature_rows_to_months(rows, key, off)` (materialized, rows with N = 0 kept) -> `build_all_cohorts_from_months(monthly, cbs, key, FEATURE_VALUES, windows)` (window tags + one pivot) -> notebook PCT -> `add_cohort_meta(df, cbs)` -> `select(*build_cohort(cb).columns)`. A check cell compares it with `build_cohort` on the first and last cohort; the offset-0 parity uses it too.

NB04 validation (2026-10-23, 10 test HCPs): fast = per-cohort for all 19 cohorts (0 mismatching cells), 12 s vs 141 s for the 19 builds. NB05: 19 cohorts, 0 mismatching cells.

Both patterns: separator `\u0001` inside pivot keys, an explicit pivot value list (never let Spark discover values), and one `withColumns`/`select` for derived columns instead of `withColumn` loops (deep plans are slow).

## 7. Derived features (copy the 3.0 semantics)

* **PCT_:** feature / `TOTAL_*_IN_LAST_N_MONTH` of the same window, 0.0 if the denominator is 0. No PCT for AVG-family columns or `RUNNING_` (3.0 has none).
* **RUNNING_:** count from `DATA_START_DATE` to the cutoff. Widen the key universe so HCPs whose only claims are older than the widest window still get a row.
* **AVG (NB01):** monthly value per NPI x cohort month, zero-filled months, sum / fixed denominator (N+1 when `AVG_EXTRA_MONTH`). `TOTAL_PATIENT_COUNT` counts distinct patients on non-'other' `TREATMENT_CATEGORY` claims only.
* **DIFF/RATIO (NB01):** `_IN_LAST_3_6_MONTH = last6 - last3`, set to 0 when the feature's group had no claims in the last 3 months (3.0 null behaviour). `RATIO = (last6 - last3) / last3`, 0 if `last3 = 0`.
* **Patient-table joins:** join on `(PATIENT_ID, assign_cohort_month(SVC_DT, cb offset))` = patient table `SVC_DT_M`. A left join keeps every claim; an inner join drops unmatched claims. Use the same join type as the original.

## 8. Validation standard (all four checks are required)

1. **Fast = slow:** first and last cohort, all cells equal (`np.isclose` rtol/atol 1e-9), same column order and types.
2. **Completeness:** expected vs written cohorts, duplicates = 0, null cells = 0 (sum one flat aggregate per column in Python; a deep `a+b+c` expression hits `RecursionError` on Spark Connect), rows per cohort.
3. **Offset-0 parity:** rebuild every cohort at offset 0 with the original's inputs (full history `df_x_all` + 3.0 patient tables, via `FAST_SOURCES["orig"]`), then compare every shared column with the 3.0 table for the same `SVC_DT_M` (null = 0). Also check that original-only window columns and original-only NPIs are all 0. Report known quirks separately; don't hide them. Target: 0 mismatches.
4. **HCP trace:** take the busiest test NPI, recount the raw claims per cohort and window in pandas (code independent of Spark), and compare with the written table. Target: 0 mismatches.

Vectorise the pandas comparisons. Convert only the object columns with `pd.to_numeric`, then `astype(float).fillna(0)`. Per-column loops over thousands of columns take minutes.

## 9. Serverless and environment gotchas

* `00_connection` runs `from pyspark.sql.functions import *`, which shadows `sum`, `max`, `min`, `round`, `abs`. Use `builtins.sum` and the like.
* No `.cache()` or `.persist()`. Use `materialize()`. Avoid `count()` and `display()` on intermediate wide frames, because each one recomputes the whole plan.
* Spark Connect: no RDD, `_jvm` or `_jdf`. Read `.columns` once outside loops (lint SCPAP001).
* `00_connection` may call `restartPython()`. Define parameters after it.
* The user's write calls can be blocked for the assistant. If a write is denied, ask the user to run that cell.

## 10. Working with this user

* The user often wants **guidance only** ("don't run or change anything"). Respect that: explain what the code does, where to add filters and what to check, and say what you read in the code versus what you are guessing.
* Keep answers short and organised. Small worked examples (input claims -> feature rows -> pivoted cohort row) help the user most.
* Use the 10 test NPIs from `get_test_npis()`. They were chosen to have 5-30 patients, both GFR and UACR labs, several stages and a date range of more than 1 year.
* Don't delete stale partitions or tables without asking (e.g. `2025-02_offset0` left in `claim_rx_monthly_cohort`).
