# NBA 3.1 HCP features: why `step2_fill_missing` and `step3_lag` were dropped

For: Raman. Status: 2026-11-05. Scope: the windowed claim-count features (`..._IN_LAST_{N}_MONTH`) of the HCP notebooks, shown with NB01 `01_claim_rx_monthly_cohort`. The other HCP notebooks rely on the same identity. NB04 and NB05 use the all-cohorts engine in `00_cohort_config` (`build_all_cohorts_from_months`), which counts by cohort month inside each window and checks that every window starts and ends on a cohort-month boundary.

## Short answer

In 3.0, a window feature was built in three steps: count claims per NPI per month, add a row for every month with no claims (`step2_fill_missing`), then add up the last N rows (`step3_lag`). 3.1 counts the claims dated inside the window directly. Both give the same number. 3.1 doesn't need the monthly table, so it doesn't need the step that fills its gaps either. The date form is also the only one that works for the 3.1 cohorts with offset 7, whose months don't start on the 1st.

## The identity it relies on

In 3.0, a feature for an NPI at month M and window N is the sum of that NPI's monthly counts for months M-N+1 through M. Each claim belongs to exactly one month, so that sum equals the number of claims dated in those N months.

3.1 counts those claims directly and skips the monthly table. Because the window is defined by dates, months with no claims don't need a placeholder row, and that placeholder row was all `step2_fill_missing` provided.

`step3_lag` needed the grid because it counts rows, not months: `rowsBetween(-N+1, 0)` means "the last N rows". That equals "the last N months" only if every month has a row. Without the grid, the last 3 rows of an NPI with claims in January and May are January and May (and whatever came before), not March to May.

## Step-by-step mapping

| 3.0 step | What it did | 3.1 equivalent (`build_feature_group` in `00_cohort_config`) |
| --- | --- | --- |
| `date_trunc` + `groupBy(NPI, month).pivot().count()` | Monthly counts per pivot value | `pivoted_counts`: the same pivot and count, over the window's claims instead of one month |
| `step2_fill_missing` | One row per NPI per month, so that rows = months | Not needed: the window is a date range, so missing months can't shift it |
| `step3_lag`, `rowsBetween(-N+1, 0)` | Sum of the last N rows (= N months only because of the grid) | `filter_to_window(start, end)`, with bounds from `_build_bounds` (start exclusive, end inclusive) |
| Filter before pivot (e.g. `REJECTION_FLAG = 1`, brand list) | Restricts which claims are counted | `extra_filter` |
| Compound pivot (treatment x `DAYS_SUPPLY_BIN`, etc.) | Concatenated pivot key | `combine_cols` -> `concat_ws("_")` |
| `fillna(0)` after the grid join | Months with no claims count as 0 | `na.fill(0)` in `pivoted_counts`, plus the outer join across windows with `na.fill(0)` |
| `_IN_LAST_{N}_MONTH` naming | Column suffix | Same suffix |
| Pivot over the full history | Every month gets the same columns | `pivot_values`: a fixed list (NB01 cell 11), so every cohort gets the same columns |

## Worked example (offset 0, cohort 2025-05, N = 3)

* `_build_bounds` gives start 2025-02-28 (exclusive) and end 2025-05-31 (inclusive), so the window is March, April and May.
* That's exactly the three grid rows `rowsBetween(-2, 0)` reads at May.
* NPI A has claims only in January (2) and May (1). Both versions give `N_IN_LAST_3_MONTH = 1`.
* Without the grid, 3.0 would have read the January and May rows as "the last 3" and returned 3.

Toy test (run 2026-11-05 with the real `build_feature_group` and `get_cohort_bounds`; NPI B has 1 claim in February 2025 only). Values are the 1, 3 and 12-month counts at cohort 2025-05:

| Method | NPI A (1 / 3 / 12) | NPI B (1 / 3 / 12) |
| --- | --- | --- |
| 3.0 with the grid (`step2_fill_missing` + `step3_lag`) | 1 / 1 / 3 | 0 / 0 / 1 |
| 3.0 without the grid (`step3_lag` only) | 1 / **3** / 3 | no May row |
| 3.1 `build_feature_group` | 1 / 1 / 3 | 0 / 0 / 1 |

The 3.1 result equals 3.0 with the grid. The middle row shows what the grid protected against. The scratch cell is in `Final Product Basket/00_product_mapping_update_2026_11_05` ("Scratch: toy test of the 3.0 vs 3.1 window identity").

Beyond the toy test, NB01's offset-0 parity check compares 3.1 with the 3.0 output on the test HCPs. It uses the full Rx history (`df_rx_all`) and the 3.0 reference snapshot.

## Why the outer join matters

An NPI with claims in the 12-month window but none in the last month has no row in the 1-month result. The outer join brings it back, and `na.fill(0)` sets it to 0. That's the same value 3.0 got from a gridded row with null counts. NPI B in the toy test is that case: 0 for 1 month, 1 for 12 months.

## What it does not replace

The grid had other jobs, which live in other cells of NB01:

* **Month dimension:** 3.0 produced every (NPI, month) row in one pass. 3.1 builds one row per NPI per cohort, and the cohort list comes from `get_hcp_cohort_months()` (NB01 cell 10; section 3 of NB01 runs every cohort).
* **`RUNNING_` features:** these use a window with no lower bound (all history up to the cohort cutoff), built in NB01 cell 18.
* **AVG features:** an average needs to know how many months had no claims, so NB01 cell 19 still zero-fills months. With `AVG_EXTRA_MONTH = True` (as in 3.0), the AVG window is one month wider and the sum is divided by N+1.
* **Inactive NPIs:** HCPs with only older history (non-zero `RUNNING_` values, no claims in the windows) are added back in NB01 cell 21, so they get 0 for the window features instead of being dropped.

## Why the date-range form is needed for 3.1

With offset 7, cohorts don't match calendar months. For example, cohort 2026-03 runs from Mar 7 to Apr 6. Monthly rows can't represent that window without re-bucketing the claims. A date range like (2026-03-06, 2026-04-06] can; that's what `get_cohort_bounds("2026-03")` returns for the 1-month window.

At offset 0, `_build_bounds` puts the start on a month boundary, so 3.1 reproduces the 3.0 calendar-month features. That's the basis of the offset-0 parity checks.

## Where the code is

* `00_cohort_config`: `build_feature_group`, `pivoted_counts`, `filter_to_window`, `_build_bounds`, `get_cohort_bounds`.
* NB01 `01_claim_rx_monthly_cohort`: cell 11 (fixed pivot values), cells 13-17 (feature groups), 18 (`RUNNING_`), 19 (AVG), 21 (combine and widen the NPI universe).
* 3.0: `step2_fill_missing`, `step3_lag`, `step3_lag_avg` in `00_step23_function` (no longer used by the 3.1 HCP notebooks).
