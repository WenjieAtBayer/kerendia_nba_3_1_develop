# HCP-Level Features: Runbook for a Specific Use Case

Reference for [SKILL.md](SKILL.md). Use it when someone wants to **run** the existing notebooks (NB01-NB05 in `hcp_level_features/` of the **hcp_claims copy**, the source of truth; the clone copy is stale, see [notebooks.md](notebooks.md)) for their own case: another offset, some cohorts only, their own HCP list, production, or one extra feature. Facts were read from the notebook code on 2026-10-23 and updated after the 2026-10-26 refresh run.

## Step 1. Pin down the use case (ask about anything missing)

| Question | Parameter | Where it is set | Default |
| --- | --- | --- | --- |
| Which cohort offset? (0 = calendar months, 7 = cohorts start on the 7th) | `OFFSET_DAY` | `00_cohort_config`, cell "Global parameters" | 7 |
| Which cohorts? | `COHORT_MONTHS` (list like `["2026-06", "2026-07"]`, or None = all from `COHORT_ORIGIN` to `COHORT_LAST`) | same cell | None |
| Which cohort is used in preview/display cells? | `COHORT_MONTH` | same cell | 2025-02 in recent runs (falls back to the first cohort if not in the list) |
| Which HCPs? | `VALIDATION_MODE` (True = only the NPI list in `get_test_npis()`, False = all HCPs) | same cell; NPI list in cell "Validation / Production filters" | True, 10 test NPIs |
| First date of data used? | `DATA_START_DATE` | same cell | 2023-01-01 |
| Which features? | the notebook(s): NB01 Rx, NB02 lab, NB03 Dx, NB04 Rx x patient stage / lab, NB05 new patient starts | see [notebooks.md](notebooks.md) | all five |
| NPI level or provider level? | NB01-NB04 write both; NB05 = provider only | notebook | - |

Rules for these parameters:
* **Cohorts only run when they are complete.** `get_hcp_cohort_months()` drops every cohort whose cutoff is after the common last service date of all HCP inputs. With data through 2026-09-30 (2026-10-26 refresh) at offset 7, the last cohort is 2026-08 (cutoff 2026-09-06): **20 cohorts**. The config confirmation prints the full range to `COHORT_LAST` ("2025-01 .. 2026-10", 22 months); that is not the count that runs. Before the refresh (data to 2026-08-28) it was 19 cohorts to 2026-07. If the user asks for a later cohort, tell them the input data must be refreshed first (`00_Write_Input_Files`, Wenjie).
* **`00_cohort_config` is shared** by all HCP and patient-journey notebooks. A change applies to every notebook that runs afterwards. Tell the user to set it back when finished (team defaults: offset 7, validation True).
* **Custom HCP list:** put the NPIs in the list returned by `get_test_npis()` and keep `VALIDATION_MODE = True`. NB05 filters on `NPI_NUMBER` too, so pass NPIs, not PROVIDER_IDs. The offset-0 comparison cells then compare those HCPs with 3.0.
* **Lookbacks are `[1,3,6,12]` in all five notebooks** (`LOOKBACK_WINDOWS` / `HCP_LOOKBACK_WINDOWS` in the config, = 3.0). Changing them changes the output columns, so ask first. Output tables are written with `mergeSchema`, so columns removed from the code stay in the table as nulls until the table is reset.
* **Output tables are keyed by `COHORT_ID` = `<month>_offset<N>`.** A run at another offset adds new partitions and keeps the existing ones. A rerun of the same cohorts replaces only those partitions.

## Step 2. Check the dependencies before running

1. **Inputs are fresh** in `query_output/` (`Rx_01_new`, `Lab_03`, `Lab_04`, `Dx_03`, `kerendia_nba_3_0_Rx_05`, `kerendia_nba_3_0_npi_bhid_mapping`). They are written by `00_Write_Input_Files` (3.0, Snowflake). Check the max `SVC_DT` if the user expects recent cohorts.
2. **Patient tables have to be built at the same offset** for the notebooks that join them: NB01 (`pat_new_and_total_treatments`), NB03 (`pat_new_ckd_stage`), NB04 (GFR and UACR tables). NB02 and NB05 have no patient-table input.
   * Validation mode reads the 3.1 `*_validation` tables from `Patient_Journey_Validation` (01 labs -> 02 dx -> 03 rx -> 04 t2d -> 05 px -> 06 combine). Rerun them in that order with the same `OFFSET_DAY` and test NPIs first.
   * Production mode still reads the **3.0** patient tables (calendar months). At offset > 0 that is a month mismatch; tell the user before running in production. **Since 2026-10-26 these 3.0 tables are missing from `query_output/`**, so NB01/NB03/NB04 production fails with `PATH_NOT_FOUND` until they are restored or `get_patient_table` points to full-population 3.1 tables (needs PJ01-PJ06 in production mode). Check with `os.path.exists` before any production run.
   * As of 2026-10-26 the 3.1 validation tables were written at **offset 7** (PJ01-PJ06 rerun after the data refresh). Rerun them whenever the offset, the test NPIs or the input data change.
    * PJ01/PJ02 run the original 3.0 Snowflake queries (they need `%run 00_config` from 3.0 and Snowflake access). PJ03-PJ05 query Snowflake directly. PJ06 needs all five intermediate tables. Its write cells can be blocked for the assistant; ask the user to run them.
3. **Compute:** serverless. No cache; the notebooks use `materialize()`.

## Step 3. Run the notebooks

* **Quick refresh (logic unchanged, user wants speed):** run only these cells, in order, and skip the display, preview, "Check: fast engine = ...", offset-0 parity and trace cells. All names are cell titles.
  * NB01: `00_connection`, cohort config, "Config confirmation", "Load raw Rx claims and define cohorts", "Fixed pivot values", the 7 feature-group cells ("NPI universe + Treatment Category + Brand + Total" .. "AVG features with monthly zero-fill"), "Combine all feature groups", "SGLT2 WO INVOKANA derived features", "PCT features", "Difference and Ratio features", "Add cohort metadata + final output", "Fast cohort engine", "Build and write every cohort", "All cohorts per NPI", "Provider ID mapping and provider-level output".
  * NB02: same idea (load, feature functions, PCT, metadata, fast engine, write, reload, completeness, provider mapping, provider write, null count).
  * NB03: `00_connection`, config, confirmation, "Load Dx claims...", "Index columns", "Dx stage, patient stage and total features per window", "RUNNING features", "Combine feature groups", "PCT features", "Add cohort metadata", "Fast cohort engine", write, completeness, provider output.
  * NB04: `00_connection`, config, "Load all input tables", "Label helpers", the three Family A/B/C claim-level cells (they define the claim-level tables, not only display), "Feature rows (once) and cohort list", "Build one cohort (functions + preview)", "Fast cohort engine", write, completeness, provider output.
  * NB05: `00_connection`, config, "Load input table", "Feature rows (once) and cohort list" (it reads `df_rx_all` for the start list), "Build one cohort (functions + preview)", "Fast cohort engine (all cohorts in one query)", "Build and write all cohorts (one write)", "All cohorts per provider (completeness checks)".
  * Measured 2026-10-26 (10 test NPIs, 20 cohorts): each notebook finishes in a few minutes this way.
* **Full run (logic changed): run every notebook top to bottom (Run all).** Later cells use functions and variables from earlier ones. In NB01-NB03 the fast-engine cell builds `OUTPUT_COLS = build_cohort_slow(cb_preview).columns`, so the step-by-step cells have to run first. `00_connection` can restart Python, so never start in the middle after a restart.
* The notebooks are independent of each other. Any order works, but each needs its own inputs from step 2.
* **Writes:** the assistant's write calls can be blocked. If a write is denied, ask the user to run that cell.
* **Reset cells** ("One-time reset: delete old tables", NB01 and NB02) delete the output tables and are always blocked for the assistant. Both were run on 2026-10-26 and are now commented out. If one is needed again (columns removed from the code): uncomment it, ask the user to select it and use "Run all above" and then run it, then the assistant runs the write and checks and comments it out again.

| Notebook | Cells that write | Write style | Measured write time (10 test NPIs, 20 cohorts, 2026-10-26) |
| --- | --- | --- | --- |
| NB01 `01_claim_rx_monthly_cohort` | "Build and write every cohort (one query, one write)" + "Provider ID mapping and provider-level output" | all cohorts, one write, `replaceWhere COHORT_ID IN (...)` | 1.3 min; offset-0 parity about 7 min (19 cohorts, 2026-10-23) |
| NB02 `02_claim_lab_monthly_cohort` | "Build and write every cohort" + "Write provider-level output" | one write | 0.1 min |
| NB03 `03_claim_diagnosis_monthly_cohort` | "Build and write every cohort" + "Provider ID mapping and provider-level output" | one write | 0.2 min |
| NB04 `04_claims_monthly_cohort` | "Build and write all cohorts (one write)" + "Provider ID mapping and provider-level output" | one write, `replaceWhere COHORT_ID IN (...)` | 0.6 min |
| NB05 `05_claim_rx_nps_monthly_cohort` | "Build and write all cohorts (one write)" | one write, `replaceWhere COHORT_ID IN (...)` | 0.3 min; offset-0 parity about 6 min (5 of them building the offset-0 feature rows) |

Production (`VALIDATION_MODE = False`) has never been run for these notebooks. Before the first production run, tell the user:
* Runtimes above are for 10 HCPs only. Rx tables are 27-31 GB, about 4B rows, so plan a test on one cohort first (`COHORT_MONTHS = ["2025-01"]`).
* `materialize()` then writes staging Delta tables (`notebook_output/<name>_stage_*` or `*_feature_rows_*`). They can be deleted after the run, but only with the user's OK.
* Several cells call `toPandas()` or `display()` on full outputs (fast vs step-by-step check, completeness "full table" display, preview displays, trace). Skip them or add a limit in production. The offset-0 comparison cells skip themselves in production (`_npis is None`).
* NB05 then computes first-start dates over the full Rx_05 table (all patients). This is the heaviest step.

## Step 4. Check the results

Read the completeness cell of each notebook: all expected `COHORT_IDS` present, duplicates 0, null cells 0, same columns in every cohort. Then compare the rows with what the use case expects. Examples:

```python
OUT = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/"
df = (spark.read.format("delta").load(OUT + "claim_lab_monthly_cohort")
      .filter(F.col("COHORT_ID").isin("2026-06_offset7", "2026-07_offset7")))
display(df.groupBy("COHORT_ID", "CUTOFF_DATE").count())
```

If the use case changed the logic or used new inputs, also run the fast-vs-slow check, the offset-0 comparison and the HCP trace cells (validation mode). All must show 0 mismatches, apart from the known quirks in [notebooks.md](notebooks.md).

* **Offset-0 comparison prints `SKIPPED — 3.0 reference table(s) missing`:** expected since 2026-10-26 (the 3.0 tables are gone). It's not a failure. Report "parity not run (3.0 tables missing), last PASS 2026-10-22/23" and rely on fast-vs-slow + trace. Don't try to rebuild the 3.0 tables.
* **HCP trace:** check the printed claim counts. A trace with all-zero raw counts tests nothing; use an NPI that has claims (NB02 does this on its own).

## Step 5. Report to the user

State: parameters used (offset, cohorts, HCP set, mode), tables and partitions written, rows and columns per table, check results, and caveats that apply (patient tables at another offset, DATA_START_DATE differences, 3.0 patient tables in production). Then remind them to reset `00_cohort_config` if it was changed.

## Common use cases

| The user wants | Do this |
| --- | --- |
| Features at another offset (e.g. 14) for the test HCPs | Set `OFFSET_DAY = 14`; rerun the patient journey at 14 if NB01/NB03/NB04 are needed; Run all in each notebook; new partitions `*_offset14` appear next to the offset-7 ones. |
| Only the newest cohort(s) | `COHORT_MONTHS = ["2026-07"]` (or a list); Run all; only those partitions are replaced. |
| Their own HCPs | Replace the list in `get_test_npis()`, keep `VALIDATION_MODE = True`; check those NPIs exist in the source (`apply_npi_filter` silently returns 0 rows for unknown NPIs). |
| All HCPs (production) | `VALIDATION_MODE = False`; first check the 3.0 patient tables exist (missing since 2026-10-26, which blocks NB01/NB03/NB04) and are acceptable for the offset; then a one-cohort test run; skip the heavy pandas cells. NB02 and NB05 have no patient-table input. |
| Reproduce 3.0 monthly values | `OFFSET_DAY = 0`; NB01-NB03 also need `df_x_all` (full history) and 3.0 patient tables, which is what the offset-0 comparison cells already do, so use those cells instead of a new run. |
| A new feature in an existing notebook | Pattern A (NB01-NB03): add the group to the key list and `COUNT_SPECS` of the fast engine, its fixed pivot values, and the same group in the step-by-step functions. Pattern B (NB04-NB05): add rows in `build_feature_rows` and make sure the name is in `FEATURE_VALUES` (both `build_cohort` and the fast engine read them; rerun the fast-engine check cell). Then rerun the fast vs step-by-step check, completeness and trace. Note that the offset-0 comparison has nothing to compare new columns against. |
| A new feature notebook | Follow the workflow in [SKILL.md](SKILL.md) section 5 and the code in [templates.md](templates.md). |

## Known differences between the notebooks (state them when relevant)

* **DATA_START_DATE is applied in all five notebooks** (NB04/NB05 aligned on 2026-10-23). NB05 still uses the full history for first-start dates only. The offset-0 comparisons use the full history in every notebook.
* **One cohort list for all notebooks:** `get_hcp_cohort_months()` in `00_cohort_config` uses the earliest last `SVC_DT` over `HCP_SOURCE_TABLES` (Rx_01_new, Lab_03, Lab_04, Dx_03, Rx_05). After the 2026-10-26 refresh: Rx_01_new 2026-10-02, the others 2026-09-30 -> common end 2026-09-30. If a new HCP input is added, add it to `HCP_SOURCE_TABLES`.
* **Production patient tables are 3.0** (calendar months) in NB01, NB03 and NB04.
* **NB01 provider-level output** (`provider_claim_rx_monthly_cohort`) first ran on 2026-10-26 (180 rows, 0 null PROVIDER_ID, 0 duplicates).
* **Row counts differ by notebook:** a notebook only creates rows for HCPs with at least one claim of its own type. With the 10 test NPIs: NB01/NB03/NB04 9 NPIs (180 rows), NB05 9 providers (180 rows), NB02 7 NPIs (140 rows). 1528629052 has no claims in any source, and 1396374062 has no lab claims.
* **NB01 has two trace cells:** "Single HCP Journey - Full Feature Trace (preview cohort)" (older, one cohort) and "HCP trace across all cohorts" (the one to use).

## Publishing (only when the user asks to push)

1. Edit the skill in the clone folder (`kerendia_nba_3_1_develop_clone/databricks-skills/hcp-level-features/`), which is not a git folder.
2. In the hcp_claims worktree (`kerendia_nba_3_1_develop_hcp_claims`, branch `dev/hcp-claims-features`), stage the clone's skill files with `git --work-tree=<clone folder> add databricks-skills/hcp-level-features`, then `git restore databricks-skills/hcp-level-features` so the worktree files match the index.
3. `git status`, commit the notebooks + skill with a message that lists the validation state, `git push origin dev/hcp-claims-features`. Never push to `main`; a PR is a separate user decision.
