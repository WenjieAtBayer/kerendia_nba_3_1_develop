# Step 2 explained: Cells 10–14 (basket reader, basket query, run, comparison) vs Cell 7 (3.0 lab query)

**Contents:** sections 1–6 = Cell 10 (2a); section 7 = Cell 11 (2b); section 8 = Cell 12 (2c); section 9 = Cell 13 (2d) checks and results; section 10 = review of Cell 14 (2e) findings; section 11 = how far Cells 16–30 (Steps 3, 4 and section 2) test the issues flagged in sections 6, 7.4, 9.3 and 10.  
**Results quoted:** from the notebook run of 2026-10-29 (cells 10–30 executed by the user; cell 31 failed, cell 33 skipped).

**Notebook:** `Patient_Journey_Validation/01_patient_journey_labs`  
**Cells compared:** Cell 7 "Load lab data" (3.0 baseline query) and Cell 10 "2a. Read and check the lab basket"  
**Basket read by Cell 10:** `/Workspace/Users/patricio.guledjian.ext@bayer.com/kerendia_nba_3_1_develop_hcp_claims/.../Final Product Basket/Kerendia_Lab_Final.csv`

---

## 1. The short version

Cell 10 contains **no SQL**. It does not change the query itself. Its job is to take every *test rule* that Cell 7 had typed into the SQL and read it from the basket CSV instead. It then checks that the file makes sense and passes the rules to Cell 11 (2b), which writes the SQL from them.

```
Cell 7:   rules typed inside the SQL  ->  query
Cell 10:  basket CSV -> checks -> lab_basket + lab_test_rules  ->  Cell 11 builds the query  ->  Cell 12 runs it
```

So the improvement is that **the rules now live in a file, not in the code**. To change a code, unit, range or cut-off, you edit the CSV. The SQL is not touched.

---

## 2. What Cell 10 does, line by line

| Step | Code | What it does |
| --- | --- | --- |
| 1 | `LAB_BASKET_PATH = ...Kerendia_Lab_Final.csv` | Points to the basket file |
| 2 | `pd.read_csv(..., dtype=str).fillna("")` | Reads every column as text, so codes like `9318-7` stay as written. Empty cells become `""`, so a PART row with no PRIORITY becomes `NULL` in the SQL later |
| 3 | `lab_basket[lab_basket["ACTIVE"] == "Y"]` | Keeps only active rows. Potassium (2823-3) and HbA1c (4548-4) are `N`, so they are left out |
| 4 | Check 1: same rules per test | Within RESULT rows, every row of one test (e.g. all GFR rows) must have the same `UNITS`, `VALID_MIN`, `VALID_MAX`, `STAGE_CUTOFFS`. `PRIORITY` is allowed to differ |
| 5 | Check 2: `ROLE` | Must be `RESULT` or `PART` |
| 6 | Check 3: `MATCH_TYPE` | Must be `LOINC` or `NAME` |
| 7 | Check 4: duplicate LOINC | A code cannot be listed twice (the earlier basket had 88294-4 twice) |
| 8 | Build `lab_test_rules` | One entry per test from the first RESULT row: allowed units (split on `\|`), valid min/max, cut-offs as (value, stage) pairs, and the `else` stage |
| 9 | Print + display | Summary line and a small table of the rules per test |

If any check fails, the cell stops with a clear message **before** any query is sent to Snowflake.

### What it produces today (I reran the cell's logic on the current file)

* Summary: **21 codes (10 results, 11 parts) and 5 name backups**, tests `GFR` and `UACR`
* All four checks pass (each test has exactly one set of rules)
* `lab_test_rules`:

| Test | Units | Valid range | Cut-offs | Else stage |
| --- | --- | --- | --- | --- |
| GFR | `ML/MIN/1.73M2` | 1 – 200 | <15 → 5, <30 → 4, <60 → 3, <90 → 2 | 1 |
| UACR | `MCG/MGCREAT`, `MG/GCREAT`, `MG/GCR`, `MG/G{CREAT}` | 0 – 10000 | <30 → 1, <300 → 2 | 3 |

Confirmed by the notebook run of 2026-10-29: cell 10 printed `Basket OK: 21 codes (10 results, 11 parts) and 5 name backups, for tests ['GFR', 'UACR']` and the same rules table.

---

## 3. Each hardcoded part of Cell 7 and where it comes from now

These are the Step 1 items (Cell 8) that Cell 10 covers: 1–5 and 14.

| # | Cell 7 (3.0, typed in the SQL) | Cell 10 (read from the basket) | What improves |
| --- | --- | --- | --- |
| 1 | **Which tests count:** only name patterns `%GFR%`, `%GLOMERULAR%`, `%ALB%`, `%RATIO%` | `lab_basket` rows with `MATCH_TYPE = LOINC` (21 codes); the 3.0 patterns stay as `NAME` backup rows | Tests are found by LOINC code first. Renamed tests are no longer lost, and other tests with "ALB" in the name no longer get in |
| 2 | **Test labels** `'GFR'` / `'UACR'` typed in every `CASE` | `TEST_TYPE` column; `lab_test_rules` has one key per test | Adding a test means adding rows to the CSV. The output stage columns (`GFR_STAGE`, `UACR_STAGE`) are named from these keys |
| 3 | **Units:** one list for both tests | `lab_test_rules[t]["units"]`, one list per test | A UACR unit can no longer be accepted for an eGFR result, or the other way round |
| 4 | **Cut-offs** 15/30/60/90 and 30/300 typed in `CASE` | `STAGE_CUTOFFS` → `cuts` + `top_stage` | Changing a cut-off (e.g. splitting stage 3 into 3a/3b) is a CSV edit |
| 5 | **Valid range:** none. eGFR over 150 → stage 0; eGFR = 0 → stage 5 | `valid_min` / `valid_max` per test | Values out of range are dropped, not given a wrong stage. eGFR 150–200 is now stage 1 |
| 14 | **Same day:** `MEDIAN` of every result for the patient, day, NPI and test | `PRIORITY` column kept in `lab_basket` | Cell 11 keeps only the lowest priority per day. Race-free CKD-EPI 2021 (1) beats older equations (2), which beat the Black equation (3), instead of all being averaged |
| – | **Parts of a test:** not separated. Any `%ALB%` / `%RATIO%` row (urine creatinine, albumin concentration, urine volume...) could be staged | `ROLE = PART` for 11 UACR codes | Cell 11 drops PART rows (`ROLE = 'RESULT'`), so only real ratios (9318-7, 14958-3) are staged |
| – | **No checks:** a typo in the SQL fails late in Snowflake, or silently gives wrong stages | Four checks before any query is sent | Basket errors are caught early with a clear message |

### What Cell 10 does NOT change (handled later)

| Kept as in 3.0 at this step | Moved in |
| --- | --- |
| Start date `2021-11-30`, specialty list (set in Cell 11 as `LAB_START_DATE`, `LAB_SPECIALTIES`) | Step 3, `LAB_CONFIG` (Cell 16) |
| Value format (`>`, `<`, `^` dropped), patient ID rule | Step 4, `VALUE_RULES` / `PATIENT_ID_RULE` (Cell 22) |
| Source table and column names | Step 3 (Cell 16) |

This is on purpose. Step 2 changes only the basket, so the comparison in Cell 13 (2d) shows only the basket's effect.

---

## 4. How the rules flow into the query (Cell 11)

| Cell 10 output | Used in Cell 11 as | SQL piece |
| --- | --- | --- |
| LOINC rows of `lab_basket` | `code_values` | `basket` CTE: `VALUES ('98979-8', 'GFR', 'RESULT', 1), ...` |
| NAME rows of `lab_basket` | `name_type`, `name_role`, `name_prio` (longest pattern first) | `CASE WHEN TEST_NM LIKE '%AMONG BLACKS%' ...` backup for rows without a basket code |
| `units`, `valid_min`, `valid_max` | `valid` | `(TEST_TYPE = 'GFR' AND UOM IN (...) AND TEST_NUM BETWEEN 1 AND 200) OR (...)` |
| `cuts`, `top_stage` | `stages` | `CASE WHEN MEDIAN_TEST_RESULT < 15 THEN 5 ... ELSE 1 END AS GFR_STAGE` |
| `PRIORITY` | `QUALIFY` | `PRIORITY = MIN(PRIORITY) OVER (PARTITION BY patient, NPI, day, test)` |
| `ROLE` | `kept` filter | `WHERE ROLE = 'RESULT'` |

---

## 5. Effect measured in Cell 13 / 14 (Step 2 vs 3.0, all US, 2025-01 to 2026-09)

| | eGFR | UACR |
| --- | --- | --- |
| Same stage | 106.73M test-days | 19.81M |
| One stage different (priority rule, 150–200 fix) | 55K (0.05%) | 27K (0.14%) |
| Lost | 260 (212 above 200, 48 = 0) | 68.4K parts + 2.5K above 10000 |
| Gained | 0 | 0 |
| Validation HCPs | No change | No change |

---

## 6. Points to watch in Cell 10

1. **The basket path is in another user's folder.** `LAB_BASKET_PATH` reads Patricio's copy (`patricio.guledjian.ext@bayer.com/kerendia_nba_3_1_develop_hcp_claims/...`), not the file in this repo's `Final Product Basket` folder. Today the two files are identical (checked), but an edit to the local copy would not be picked up. Point it to the local file, or move the path into `LAB_CONFIG`.
2. **Turning on Potassium or HbA1c will break this cell.** Those rows have no `STAGE_CUTOFFS`. If `ACTIVE` is set to `Y`, the cut-off parsing fails with `ValueError: not enough values to unpack` (reproduced). Cell 22 (4a) already handles a test without cut-offs ("value but no stage"), but Cells 10 and 11 do not. So new tests only work with the Step 4 query.
3. **Cut-offs are kept as text and their order is not checked.** That's fine for the SQL, but a CSV entry like `30:4|15:5` would pass this cell and give wrong stages in Cell 11. Cell 22 adds the low-to-high check; it could be added here too.
4. **Some checks are missing.** Nothing checks that PART rows belong to an active RESULT test, that NAME patterns are unique, that every RESULT row has a numeric `PRIORITY`, or that `UNITS` is not empty. With the current file this causes no problem, but these checks would protect future edits.
5. **Name backups can overlap.** `%GFR%` and `%AMONG BLACKS%` can both match one row. Cell 11 tries the longest pattern first (`%AMONG BLACKS%` > `%GLOMERULAR%` > `%RATIO%` > `%GFR%` = `%ALB%`), so the Black version (priority 3) wins as intended. One side effect: a name with no basket code that contains both "RATIO" and "GFR" is now read as UACR. In 3.0 it was read as GFR, because GFR was checked first. The per-test unit check then drops it if the unit doesn't match. This only affects rows matched by name.

---

## 7. Cell 11 – 2b. Lab query built from the basket

Cell 11 defines `build_lab_query_basket(basket, rules, start_date)`. The function fills Cell 10's rules into a SQL template and stores the result in `lab_query_basket`. Nothing runs in Snowflake in this cell; it only builds and prints the SQL.

### 7.1 Settings still fixed in this cell

| Setting | Value | Note |
| --- | --- | --- |
| `LAB_START_DATE` | `2021-11-30` | Same as 3.0; moved to `LAB_CONFIG` in Step 3 |
| `LAB_SPECIALTIES` | `FM, FPG, GP, GPM, IFP, IM, IMG, IPM, NRP, PHA` | Same as 3.0; moved to `LAB_CONFIG` in Step 3 |
| `_q()` helper | Turns a list into `'a', 'b', 'c'` for SQL `IN (...)` | Reused in later steps |

### 7.2 Python pieces generated from the basket

| Python variable | Built from | Becomes in SQL |
| --- | --- | --- |
| `code_values` | LOINC rows (21) | `VALUES ('98979-8','GFR','RESULT',1), ..., ('2161-8','UACR','PART',NULL)` |
| `names` sorted by length | NAME rows (5) | Order of the name `CASE`: `%AMONG BLACKS%`, `%GLOMERULAR%`, `%RATIO%`, `%GFR%`, `%ALB%` |
| `name_type`, `name_role`, `name_prio` | NAME rows | Three `CASE WHEN TEST_NM LIKE ... THEN ...` for test, role and priority |
| `valid` | `lab_test_rules` units + range | `(TEST_TYPE='GFR' AND UOM IN ('ML/MIN/1.73M2') AND TEST_NUM BETWEEN 1 AND 200) OR (TEST_TYPE='UACR' AND UOM IN (...) AND TEST_NUM BETWEEN 0 AND 10000)` |
| `stages` | `lab_test_rules` cut-offs | `CASE WHEN TEST_TYPE='GFR' THEN CASE WHEN MEDIAN_TEST_RESULT < 15 THEN 5 ... ELSE 1 END END AS GFR_STAGE`, and the same for `UACR_STAGE` |

### 7.3 The SQL, CTE by CTE, compared with Cell 7

| CTE | What it does | Same as 3.0 | Different from 3.0 |
| --- | --- | --- | --- |
| `basket` | Inline table of the 21 basket codes with test, role, priority | – | New. 3.0 had no list of codes |
| `src` | Reads the Quest table | Same value filters: numeric patient ID, value not null, no `-`, `>`, `<`, plain numbers only; same date `CASE` | **Adds `LOINC_CD`**. **Filters early:** keeps only rows whose LOINC is in the basket **or** whose name matches a backup pattern (`LIKE ANY`). 3.0 read every row and dropped `TEST_TYPE = 'OTHER'` at the end |
| `typed` | Assigns test, role, priority to each row | Name patterns are the 3.0 ones | **LOINC first:** basket values via `LEFT JOIN`; the name `CASE` is used only when the code is not in the basket (`COALESCE`). Adds `MATCHED_BY` = `BASKET` or `NAME` |
| `kept` | Applies row filters | Same specialty list (via `DIM_PRVDR`), same start date, NPI not null | **`ROLE = 'RESULT'`** removes the 11 UACR parts. **Units and valid range per test** (3.0: one unit list for both tests, no range). **`QUALIFY PRIORITY = MIN(PRIORITY)`** per patient, NPI, day, test keeps only the best equation of the day |
| `vals` | `DISTINCT` patient, NPI, day, test, value | Same as the 3.0 `SELECT DISTINCT` before the median | – |
| `info` | Per patient-day-test: list of LOINC codes used, `MATCHED_BY` (`MIN` = `BASKET` if any basket code) | – | New audit columns |
| `agg` | `MEDIAN(TEST_NUM)` per patient, NPI, day, test | Same median | Median now only over values of the winning priority |
| final `SELECT` | Output | Same first five columns (`PATIENT_ID, DATE, NPI_NUMBER, TEST_TYPE, MEDIAN_TEST_RESULT`) and `GFR_STAGE`, `UACR_STAGE` | **No `ELSE 0` stage**: out-of-range values are already removed in `kept`. Two extra columns `LOINC_CDS`, `MATCHED_BY` |

### 7.4 Things to know about Cell 11

* **Equations with the same priority are still averaged.** For example, MDRD (33914-3) and CKD-EPI 2009 (62238-1) are both priority 2. If a patient has both on the same day and no priority-1 result, the median mixes them, as 3.0 did. Only different priorities are separated.
* **Priority is compared within one NPI.** The partition includes `NPI_ID`, so two doctors on the same day each keep their own best result.
* **Rows with a LOINC code not in the basket** (e.g. 14959-1) can still come in through the name backup, at priority 2.
* **The stage cut-offs are inserted as text** (`< 15`), which is valid SQL. The order of the `CASE` follows the CSV order, so the CSV must list cut-offs from low to high (see section 6, point 3).

---

## 8. Cell 12 – 2c. Run the basket query

| Step | Code | Same as Cell 7? |
| --- | --- | --- |
| 1 | `Get_Data_Snowflakes(lab_query_basket)` | Yes (same helper) |
| 2 | `.filter(DATE <= date_end)` | Yes |
| 3 | `.join(_hcp_universe, on="NPI_NUMBER")` inner join | Yes (reuses `_hcp_universe` built in Cell 7) |
| 4 | Rename `DATE` → `SVC_DT`, filter `SVC_DT >= DATA_START_DATE` | Yes |
| 5 | Cast `GFR_STAGE`, `UACR_STAGE` to `int` | **New.** Snowflake returns them as decimals; the cast makes the type match what section 2 expects |
| 6 | `apply_hcp_filter` → 10 validation HCPs | Yes |
| 7 | Select `PATIENT_ID, SVC_DT, GFR_STAGE, UACR_STAGE` → `df_lab_basket` | Yes, same 4 columns as `df_lab` |

Outputs: `df_lab_basket_all` (all columns, including `LOINC_CDS`, `MATCHED_BY`, for review) and `df_lab_basket` (the 4 columns). Section 2 could use `df_lab_basket` instead of `df_lab` with no other change. This is not done yet.

**Dependency:** Cell 12 needs Cell 7 to have run first, because it uses `_hcp_universe`, `date_end` and `apply_hcp_filter`.

---

## 9. Cell 13 – 2d. How the old and new queries are compared

Cell 13 runs two independent comparisons.

### 9.1 Part A – all US patients, test-day level, inside Snowflake

**How it works**

1. `old` = the 3.0 query (`lab_query` from Cell 7), `new` = the basket query (`lab_query_basket`). Both are run as subqueries in **one** Snowflake SQL, from `CMP_START = 2025-01-01` to `date_end` (2026-09-30).
2. Each side is grouped to **patient × day × test**, with `MAX(COALESCE(GFR_STAGE, UACR_STAGE))` as the stage. The old side also keeps `MAX(MEDIAN_TEST_RESULT)` to explain losses.
3. `FULL OUTER JOIN` on `PATIENT_ID, DATE, TEST_TYPE`.
4. Each pair is put in one of four buckets:

| Bucket | Rule | Meaning |
| --- | --- | --- |
| 1. same stage | `STAGE_OLD = STAGE_NEW` | No change |
| 2. different stage | Both present, stages differ; detail shows `stage X -> Y` | A rule changed the stage |
| 3. only basket query (gained) | Old missing | New query found a test-day 3.0 did not |
| 4. only 3.0 query (lost) | New missing; detail explains why from the old value | A basket rule removed it |

5. Reasons for lost rows are assigned in this order: eGFR above `VALID_MAX` (3.0 gave stage 0), eGFR below `VALID_MIN` (3.0 gave stage 5), UACR above `VALID_MAX`, **any other lost UACR = "only a part of the test"**, anything else = `other`.
6. Counts: `TEST_DAYS` and distinct `PATIENTS` per bucket.

**Results (run 2026-10-29)**

| Test | Bucket | Detail | Test-days | Patients |
| --- | --- | --- | --- | --- |
| GFR | same stage | – | 106,733,012 | 55,131,175 |
| GFR | different | 1 → 2 | 19,465 | 16,851 |
| GFR | different | 2 → 3 | 11,031 | 9,487 |
| GFR | different | 0 → 1 (150–200 fix) | 10,352 | 7,506 |
| GFR | different | 3 → 2 | 10,255 | 8,680 |
| GFR | different | 2 → 1 | 9,389 | 8,265 |
| GFR | different | 4 → 3 | 3,554 | 2,759 |
| GFR | different | 3 → 4, 5 → 4, 4 → 5 | 708 / 401 / 129 | – |
| GFR | different | jumps of 2+ stages (3→1, 1→3, 3→5, 0→4, 0→3) | 31 | – |
| GFR | lost | eGFR above 200 | 212 | 193 |
| GFR | lost | eGFR below 1 (zeros) | 48 | 46 |
| UACR | same stage | – | 19,808,319 | 12,699,389 |
| UACR | different | 2 → 3 / 1 → 2 / 1 → 3 | 18,588 / 7,412 / 1,143 | – |
| UACR | different | 2 → 1 / 3 → 2 / 3 → 1 | 236 / 4 / 1 | – |
| UACR | lost | only a part of the test | 68,448 | 67,598 |
| UACR | lost | UACR above 10000 | 2,547 | 2,231 |
| both | gained | – | 0 | 0 |

Totals: eGFR different = 65,315 (0.06%), of which 10,355 come from stage 0 and about 55K from the priority rule. UACR different = 27,384 (0.14%). UACR lost = 70,995.

### 9.2 Part B – the 10 validation HCPs, patient-month level, in Spark

**How it works**

1. `to_patient_months(df)` turns test-days into patient-months:
   * per calendar month, keeps the stage of the **latest test** in the month (`max_by` on `SVC_DT`), for GFR and UACR separately
   * builds every month from the patient's first test month to `date_end`
   * carries the last known stage forward (`last(..., ignorenulls)`) until the next test
2. `summary(df, months)` counts 8 metrics: patients, eGFR test-days, UACR test-days, patient-months, patient-months with eGFR stage 1–5, eGFR stage 3–5, any UACR stage, UACR A2–A3.
3. The same two functions run on `df_lab` (3.0) and `df_lab_basket`; a `change` column shows the difference.
4. Two crosstabs (3.0 stage in rows, basket stage in columns), for GFR and UACR, after a full join on patient × month.

`to_patient_months` and `summary` are reused in Cells 19 (3d) and 25 (4d).

**Results (run 2026-10-29)**

| Metric | 3.0 | Basket | Change |
| --- | --- | --- | --- |
| Patients | 225 | 225 | 0 |
| eGFR test-days | 878 | 878 | 0 |
| UACR test-days | 289 | 289 | 0 |
| Patient-months | 6,139 | 6,139 | 0 |
| eGFR stage 1–5 months | 5,981 | 6,007 | +26 |
| eGFR stage 3–5 months | 2,347 | 2,347 | 0 |
| UACR stage months | 2,912 | 2,912 | 0 |
| UACR A2–A3 months | 1,504 | 1,504 | 0 |

Crosstabs: GFR is diagonal except **26 months 0 → 1**. UACR is diagonal except **4 months 2 → 3**. These 4 months don't show in the metrics because A2 and A3 are both counted in "A2–A3".

### 9.3 What the checks cover and what they don't

| Covered | Not covered |
| --- | --- |
| Every test-day in 2025-01 to 2026-09, all US, both directions (lost and gained) | 2021-11-30 to 2024-12 in Part A (Part B covers 2023+ for the 10 HCPs only) |
| Stage changes, with the reason for each lost row | **Value changes inside the same stage** (e.g. median eGFR 45 → 52 is "same stage") |
| Validation HCPs month by month, with carry-forward | **NPI level:** Part A joins on patient × day × test and takes `MAX` over NPIs, so a change for one of two doctors on the same day can be hidden |
| | Part A is **before** the HCP universe join, so it includes HCPs outside the universe |
| | Part B's monthly logic (latest test in a calendar month) is close to, but **not the same as**, section 2 (MAX stage per cohort month with the 7-day offset). It shows the trend, not the exact production table |
| | **"Part of the test" is a leftover bucket:** any lost UACR row that is not above 10000 is labelled a part. That's fine with today's rules, but a row lost to the new per-test unit check would also land there. A direct check would be to count lost rows by `LOINC_CD` / `ROLE` |

---

## 10. Cell 14 – 2e findings: check against the Cell 13 output

| Claim in Cell 14 | Cell 13 output | Status |
| --- | --- | --- |
| eGFR same 106.73M, different 65.3K (0.06%), lost 260, gained 0 | 106,733,012 / 65,315 / 212 + 48 / 0 | Matches |
| UACR same 19.81M, different 27.4K (0.14%), lost 71.0K, gained 0 | 19,808,319 / 27,384 / 70,995 / 0 | Matches |
| eGFR 150–200 → stage 1: 10.4K test-days | 0 → 1 = 10,352 (+3 for 0 → 3 and 0 → 4) | Matches |
| eGFR one-step changes ~55K, from priority | 54,960 not from stage 0, of which 28 jump 2+ stages (3→1, 1→3, 3→5) | Matches. "One-step" is slightly loose: 28 test-days jump 2+ stages |
| UACR mostly up: 2 → 3 18.6K, 1 → 2 7.4K | 18,588 / 7,412; also 1 → 3 1,143 and 241 moving down | Matches. 1 → 3 and the moves down are not mentioned |
| Lost UACR 68.4K parts + 2.5K above 10000 | 68,448 / 2,547 | Matches (see 9.3 on how "part" is assigned) |
| Validation: 225 patients, 878 / 289 test-days, 6,139 months | Same | Matches |
| "The only change: 26 patient-months eGFR 0 → 1" | GFR 26 months 0 → 1, **and UACR 4 months 2 → 3** | **Incomplete:** the UACR crosstab shows 4 more changed months |
| Nothing downstream uses it yet | Section 2 still reads `df_lab` | Correct |

**Suggested edits to Cell 14:** add the 4 UACR patient-months (2 → 3) to the validation findings. Say "about 55K test-days move, mostly by one stage" instead of "one-step". Mention UACR 1 → 3 (1.1K).

---

## 11. Cells 16–30: do they test the issues flagged above?

Results are from the run of 2026-10-29 (cells 16–30 executed).

### 11.1 What Cells 16–30 check

| Cell | Check | Result |
| --- | --- | --- |
| 16 (3a) | `LAB_CONFIG` asserts: start ≤ end, date formats not empty, specialties `None` or a list. Runs `SELECT <all mapped columns> FROM <table> LIMIT 1` on the source and provider tables | Passed: tables and all 7 + 2 columns found |
| 19 (3d) A | Step 2 vs Step 3, all US 2025-01 to 2026-09, joined on **patient × day × NPI × test**, "identical" = same stages **and same median value** | eGFR 107,166,104 and UACR 19,856,842 identical; nothing else |
| 19 (3d) B | Validation HCPs, the 8 metrics from 2d | All unchanged |
| 19 (3d) C | Rows pulled from Snowflake | 312,863,793 (2021-11-30 to 2026-10-05) → 252,155,111 (2023-01-01 to 2026-09-30), −19.4% |
| 19 (3d) D | Source rows for basket tests (all dates) whose date is empty or in no known format | 1,723,668,326 rows: 38 empty, **0 unknown format** |
| 22 (4a) | Cut-offs converted to numbers, **asserted low to high**; every staged test needs an `else` stage; flag characters cannot be digits or `.` | Passed |
| 25 (4d) A | Step 3 vs Step 4, same join as 3d, adds "same stage, value changed" bucket | eGFR 107,166,103 identical, 1 value changed (same stage), +35,719 gained (above/below); UACR 19,856,842 identical, +535 above/below, +747 flag / dot; 0 lost |
| 25 (4d) B | Validation HCPs | All unchanged |
| 25 (4d) C | Dropped-rows report: every source row (2023-01 to 2026-09) under the first rule it fails | Same numbers as Cell 26 (4e); kept 631.9M eGFR, 106.9M UACR source rows |
| 28–30 | Section 2 cleanup on `df_lab` (3.0 query) | 6,171 patient-months × 5 columns |
| 31 | Offset=0 vs production | **Failed: `SyntaxError: unterminated f-string literal`** (see 11.3) |
| 33 | Write validation table | **Skipped** because cell 31 failed |

### 11.2 Flagged issues vs what the cells test

Status: **Tested** = a cell output proves it; **Fixed, not tested** = code handles it but no run uses a case that triggers it; **Partly** = some evidence; **Open** = not addressed.

| # | Issue (where flagged) | Status | Evidence in Cells 16–30 |
| --- | --- | --- | --- |
| 1 | Basket read from Patricio's folder (6.1) | **Open** | `LAB_CONFIG` has no basket path; 2a path unchanged. Copies identical today |
| 2 | Activating Potassium / HbA1c breaks 2a (6.2) | **Fixed, not tested** | 4a handles a test without cut-offs (`pairs = [] if empty`) and 4c only adds stage columns for tests with cut-offs. But 4a reads `lab_basket` from 2a, and 2a still fails first, so `ACTIVE = Y` still stops the notebook at Cell 10. Also, a test without cut-offs would only appear as `MEDIAN_TEST_RESULT`; `df_lab_step4` keeps stage columns only, so section 2 would not get it |
| 3 | Cut-off order not checked (6.3) | **Fixed for Step 4, not tested** | 4a asserts low-to-high. Not added to 2a / 3b. No run with a wrong order |
| 4 | Missing basket checks: PART belongs to an active test, NAME unique, numeric PRIORITY, UNITS not empty (6.4) | **Open** | No new basket checks in 3a / 4a |
| 5 | Name overlap: `RATIO`+`GFR` names read as UACR (6.5) | **Open** | `MATCHED_BY` is output but no cell counts rows by `MATCHED_BY` or by matched pattern. The order is the same in 3b / 4b |
| 6 | Equations with the same priority still averaged (7.4) | **Open** | 4b `QUALIFY` adds exact-before-above/below but keeps the median within one priority |
| 7 | Priority compared within one NPI (7.4) | **By design** | Unchanged; 3d / 4d now compare at NPI level, so this is at least visible |
| 8 | Non-basket LOINC (e.g. 14959-1, 48643-1) entering via name backup (7.4, walkthrough) | **Open** | `LOINC_CDS` in 4b output would show them, but no cell counts them |
| 9 | Value changes within the same stage not checked (9.3) | **Tested for Steps 3 and 4** | 3d and 4d require the same median for "identical": 0 and 1 value changes. Still not checked for Step 2 vs 3.0, where the priority rule changes values most |
| 10 | NPI hidden by `MAX` over doctors (9.3) | **Tested for Steps 3 and 4** | 3d / 4d join on `NPI_NUMBER`. 2d (Step 2 vs 3.0) still does not |
| 11 | Part A before HCP universe join (9.3) | **Open** | 3d / 4d also compare raw query output; universe join only in 3c / 4c |
| 12 | Part A only 2025+ (9.3) | **Partly** | Still 2025+ in 3d / 4d. The 2023–2024 numbers in 4e come from a one-off chat run, not from a cell. 3d Part D (dates) covers all dates |
| 13 | Part B monthly logic ≠ section 2 (9.3) | **Tested, and confirmed** | Section 2 on `df_lab` gives **6,171** patient-months (Cell 30). Part B gives **6,139** for the same 3.0 data (Cells 13/19/25). The two methods differ by 32 months, so Part B is a trend check, not the production table |
| 14 | "Part of the test" is a leftover bucket in 2d (9.3) | **Partly, and confirmed** | 4d Part C counts parts directly (16.0M UACR source rows, `ROLE = PART`) and separately **32,801 UACR rows lost to "unit not allowed"**. 3.0 accepted any of the 5 units for both tests, so some of the 68,448 "parts" in 2d may really be unit losses. No cell splits the 68,448 |
| 15 | Cell 14 missing 4 UACR months 2 → 3 (10) | **Open** | 3d / 4d have no crosstab; their metrics would not show A2 → A3 moves either |
| 16 | New query not connected downstream (walkthrough) | **Confirmed** | Cell 28 still reads `df_lab`; and Cell 33 did not write in this run (11.3) |
| 17 | Unknown date formats (Step 1 item 10) | **Tested** | 3d Part D: 0 unknown formats in 1.72B rows |
| 18 | Table / column rename (items 11–12) | **Tested** | 3a stops with a clear message if any table or mapped column is missing; passed |

### 11.3 New points found in Cells 16–30

1. **Cell 31 fails and blocks the write.** `_COMPARISON_BODY` is a normal `'''...'''` string. Its `print(f"\nRows only ...")` lines have `\n` turned into a real line break before `exec`, which splits the f-string. Error at body line 14. The error happens inside `exec`, which only runs when the production table exists, so `kerendia_nba_3_0_lab_journey_output` is present. Because the cell fails, Cell 33 was skipped and **`kerendia_nba_3_1_lab_journey_validation` was not rewritten** in this run. Fix: make the body a raw string (`r'''`) or drop `exec` and run the code directly.
2. **"Exact beats above/below" holds only within one priority.** The 4b score is `PRIORITY * 10 + (0 if exact else 1)`. So a `>90` from CKD-EPI 2021 (score 11) beats an exact MDRD value (score 20) on the same day. The email and 4e say "an exact value beats an above/below value" without this condition. Probably fine clinically, but the wording should say "within the same priority".
3. **4d "lab flag or leading dot" is also a leftover bucket.** Any gained row without `ABOVE_BELOW_VALUE` gets this label (747 UACR rows). It is not checked against the raw value (`^` or leading `.`).
4. **The dropped-rows report is not reconciled with the query output.** The report counts source rows; the query outputs aggregated test-days after the same-day priority rule. No cell checks that "11. kept" source rows equal the rows feeding `kept`. They share the same CTEs, so they should match, but a count would confirm it.
5. **The "~370M" in the email:** the 4d report's non-kept rows add up to **378.9M** (eGFR 319.2M + UACR 59.7M), including the specialty cut. Without the specialty filter it is 146.2M (eGFR 107.7M + UACR 38.5M). The ~370M was probably the total dropped rows, rounded.
6. **Date checks agree.** 3d Part D finds 38 empty service dates. The 4d report finds 27 + 11 = 38 rows with "service date empty or unknown format". The report keeps NULL-date rows past the date filter (`SVC_DT_STD IS NULL OR ...`), so both cover all years, and the two independent counts match.

### 11.4 Suggested next checks (in priority order)

1. Fix Cell 31 and re-run 31–33, so the validation table is written.
2. Split the 68,448 lost UACR test-days in 2d by `LOINC_CD` and unit, to separate real parts from unit losses.
3. Count 4c output by `MATCHED_BY` and non-basket `LOINC_CDS`, to size issues 5 and 8 (name backup, 14959-1 / 48643-1).
4. Add a GFR / UACR crosstab to 3d / 4d Part B (as in 2d), so A2 ↔ A3 moves are visible.
5. Move the cut-off-order and missing-cut-off handling from 4a into 2a, so `ACTIVE = Y` for Potassium / HbA1c does not stop the notebook.

