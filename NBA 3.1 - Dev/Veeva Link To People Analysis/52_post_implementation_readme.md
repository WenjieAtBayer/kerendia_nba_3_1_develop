# Veeva Link Key People for NBA 3.1: README (files 50 to 99)

This guide covers every file numbered 50 to 99 in this folder: what each one is for, what it reads and writes, and how to run the flow from start to finish. Files 00 to 40 are the earlier exploration and assessment (see `00_README_folder_guide.md`).

**Source:** Snowflake `CPH_DB_PROD.ANALYTICS_V2.ANLT_VEEVA_LINK_*` (15 in-use tables), read through the Spark Snowflake connector with secret scope `US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`.  
**Output root (`OUT`):** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/veeva_link_to_people/`  
**Status (2026-11-23):** Phases 0 and 1 done; Phase 2 done except the model tests (blocked on the NBA 3.1 model, I1 / I4); Phase 3 built, review pack not yet sent; Phase 4 monitoring and docs built, archive copy and monthly job waiting on decisions.

---

## 1. Plans (read these first)

| File | Use |
| --- | --- |
| `50_veeva_link_nba_3_1_readiness_plan.md` | Master plan: goals, tiers T1 / T2 / T3, phases 0 to 4, gates G0 to G3, external track X, risks. Every other plan is a child of this one |
| `51_veeva_link_phase0_working_plan.md` | Phase 0 (data foundation): snapshot, config, spine, long activity, features, acceptance checks A1 to A21 |
| `70_veeva_link_phase1_working_plan.md` | Phase 1: T1 / T2 features on the NBA cohort calendar, checks K1 to K7 |
| `80_veeva_link_phase2_working_plan.md` | Phase 2: T3 score features (snapshot and as-of), cross features, overlap and segment tests; section 11 has the Phase 3 summary |
| `90_veeva_link_phase3_working_plan.md` | Phase 3: business lists (B0, B1, B4), action hints (B2), review pack (B3) |
| `95_veeva_link_phase4_working_plan.md` | Phase 4: freshness check, archive and refresh, dictionary upkeep, feature dictionary, monthly job design |

Each plan ends with a checklist and a run log (run ids, numbers, check results).

## 2. Notebooks and files

### Phase 0: data foundation

| File | What it does | Reads | Writes (under `OUT`) |
| --- | --- | --- | --- |
| `52_veeva_link_snapshot_freeze` | Copies the latest rows of the 15 tables (`IS_LATEST_FLAG = 'Y'`, not deleted, US on person tables) to parquet; adds DQ flags, drops no rows | Snowflake | `snapshot/load=<hub load date>/<table>/`, `_manifest`, `dq_log/` |
| `53_veeva_link_config_v1` | Writes the config tables: in-scope focus names and keyword rules | Snapshot, `40_` assessment | `config/focus_dictionary_v1` (299 names), `config/keyword_list_v2` (86 include + 13 exclude) |
| `54_veeva_link_spine_map` | Maps Veeva experts to the HCP Universe by NPI; coverage status SCORED / IN_VEEVA_UNSCORED / NOT_IN_VEEVA | Snapshot, HCP Universe | `spine/veeva_npi_se_map` |
| `55_veeva_link_long_activity` | One long table of dated activity (trials, publications, events, payments, roles) with keyword tags | Snapshot, config, spine | `activity/` |
| `56_veeva_link_features_on_spine` | Phase 0 features at one anchor date (2025-10-23) | Activity, spine | `features/` |
| `57_veeva_link_acceptance_checks` | Checks A1 to A21 (row counts, match rates, coverage, leakage) | All of the above | `acceptance/run=<ts>/` |

### Phase 1: T1 / T2 features on the cohort calendar

| File | What it does | Writes |
| --- | --- | --- |
| `71_veeva_link_phase1_features` | 52 features (38 T1 + 14 T2) for 294,542 NPIs x 43 cohorts, windows aligned to each cohort cut-off (offset 7) | `features_phase1/t1_t2/COHORT_ID=<id>/`, `t1_static/`, `feature_manifest/`, `cohort_windows/`, `schema_lock/columns.json`, `checks/` |
| `72_veeva_link_spot_check` | Recomputes a sample of HCPs by hand from the snapshot and activity (K-checks) | `spot_check/` tables |
| `72_veeva_link_review_template.csv` | Blank sheet for business review of sample HCPs | - |

### Phase 2: T3 scores and tests

| File | What it does | Writes |
| --- | --- | --- |
| `60_veeva_colocation_idn_combined_signal_test` | Original co-location / IDN signal test (before KER-10); kept for reference | - |
| `81_veeva_link_score_history` | Load calendar of the 4 score tables; picks, per cohort, the latest load on or before the cut-off; archives in-scope scores per load; stability (H1 to H3) | `features_phase2/score_history/{load_calendar, cohort_load_pick, loads/, stability, checks}` |
| `82_veeva_link_t3_features` | T3 decile / index features in two versions (`snapshot`, `asof`) + cross features (IDN expert share, practice peer flag) (L1 to L6) | `features_phase2/t3/version=<v>/COHORT_ID=<id>/`, `features_phase2/cross/...`, `schema_lock/t3_columns.json`, `cross_columns.json` |
| `82_veeva_colocation_idn_signal_test_ker_10` | Re-run of the `60_` test with KER-10 writers (C1 to C3) | `features_phase2/tests/colocation_ker10/run=<ts>/` |
| `83_veeva_link_t3_tests` | R4 segment added-value table (S1 to S4) and R2 overlap with claims (interim, raw claims) | test tables under `features_phase2/` |

### Phase 3: business use (offline only until X3)

| File | What it does | Writes |
| --- | --- | --- |
| `91_veeva_link_business_lists` | B0 list base at cohort `2026-10_offset7`; B1 untargeted-authority list; B4 low-adoption IDN experts (M1 to M4, M6, M8) | `business/b0_list_base/`, `b1_untargeted_authority/`, `b4_low_adoption_idn_experts/` (each `run=<ts>/`) |
| `92_veeva_link_action_hints` | Rule-based action hints (one primary per HCP), coverage, overlap, sense check vs writing (M5 to M7) | `business/b2_action_hints/run=<ts>/` |
| `93_veeva_link_review_pack` | 150-row review pack with evidence and blank feedback columns, cover note (P1, P2, M6) | `business/review_pack/run=<ts>/{pack, pack_csv, cover}` |

### Phase 4: operations

| File | What it does | Writes |
| --- | --- | --- |
| `96_veeva_link_freshness_check` | Per table: loads, last load, data age, hub gap, stale-row share, warn flags; sets job task value `new_load` (N1, N2). Read-only | `ops/freshness/run=<ts>/{freshness, load_calendar_snowflake, checks}` |
| `97_veeva_link_archive_refresh` | Archive plan per scope and copy (`MODE`, `SCOPE` widgets; default copies nothing); refresh chain on a new load; schema check (N3 to N7) | `archive/<table>/LOAD_ID=<id>/`, `archive/load_calendar`, `ops/refresh_log/run=<ts>/` |
| `98_veeva_link_dictionary_report` | New / removed focus names vs the seen list, keyword conflicts and near misses, review sheet (N8, N9) | `config/focus_names_seen_v1` (once), `ops/dictionary_report/run=<ts>/` |
| `99_veeva_link_feature_docs` | Feature dictionary built from the manifest and schema locks: 83 columns with source, rule, status, Phase 2 / 3 reading (N10 to N12) | `docs/feature_dictionary/run=<ts>/{dictionary, dictionary_csv, checks}` |
| `100_Readme.md` | This guide | - |

## 3. How to run the flow

### 3.1 Before you start

* Attach serverless compute (the Snowflake connector works from serverless). Use Spark (`spark.read`, `dbutils.fs.ls`) for the volume; `os.listdir` on the volume fails on serverless.
* Check access: Snowflake secrets in the scope above, read on `kerendia_metric_views.mv_kerendia_nbrx` (KER-10), the HCP Universe parquet, the MDM affiliation and hierarchy tables, and `cp_ker_hcp_2026q4` (segments).
* Every notebook writes a new `run=<ts>` folder or overwrites only its own outputs; `archive/` is never overwritten.
* Run each notebook top to bottom (Run all). Read its check table at the end before you go on; stop if any check fails.

### 3.2 Full build, in order

| Step | Notebook | Needs | Check to read | Typical use |
| --- | --- | --- | --- | --- |
| 1 | `96_veeva_link_freshness_check` | Snowflake | N1, N2; `new_load`, warn flags | Always first: tells you whether there is new data |
| 2 | `52_veeva_link_snapshot_freeze` | Snowflake | A1 row counts | Only on a new load (new `snapshot/load=<date>/` folder) |
| 3 | `53_veeva_link_config_v1` | Snapshot | config row counts | Only if the config is missing or a reviewed `v2` is approved; normally skip (config is fixed, P4-D7) |
| 4 | `54_veeva_link_spine_map` | Snapshot, HCP Universe | match rate, coverage | After step 2 |
| 5 | `55_veeva_link_long_activity` | Snapshot, config, spine | activity counts | After step 4 |
| 6 | `56_veeva_link_features_on_spine` | Activity, spine | - | After step 5 |
| 7 | `57_veeva_link_acceptance_checks` | Steps 2 to 6 | A1 to A21 all pass | Gate before Phase 1 |
| 8 | `71_veeva_link_phase1_features` | Steps 4 to 6, cohort calendar | K1 to K7 | T1 / T2 features for all cohorts |
| 9 | `72_veeva_link_spot_check` | Step 8 | spot-check pass | Optional after each rebuild |
| 10 | `81_veeva_link_score_history` | Snowflake, spine, cohorts from step 8 | H1 to H3 | Before T3 |
| 11 | `82_veeva_link_t3_features` | Steps 8 and 10 | L1 to L6 | T3 + cross features |
| 12 | `82_veeva_colocation_idn_signal_test_ker_10` | Step 11, KER-10 | C1 to C3 | Optional (test) |
| 13 | `83_veeva_link_t3_tests` | Step 11, KER-10, segments | S1 to S4 | Optional (test); R2 waits for HCP claims features (I5) |
| 14 | `91_veeva_link_business_lists` | Step 11, KER-10, HCP Universe | M1 to M4, M6, M8 | Business lists |
| 15 | `92_veeva_link_action_hints` | Steps 8, 11, 14 | M5 to M7 | Set `B0_RUN` to the new `91_` run id |
| 16 | `93_veeva_link_review_pack` | Steps 14, 15 | P1, P2, M6 | Check that the `91_` / `92_` runs it reads are the ones just built |
| 17 | `98_veeva_link_dictionary_report` | Snapshot, config | N8, N9 | After a new load; send the review sheet to Medical Affairs / brand |
| 18 | `99_veeva_link_feature_docs` | Schema locks, manifest (steps 8, 11) | N10 to N12 | After any feature change |

When a notebook reads a specific upstream run (for example `B0_RUN` in `92_`), update that constant to the run id printed by the upstream notebook.

### 3.3 Monthly operations (Phase 4)

1. Run `96_`. If `new_load` = 0: read the warn flags, stop (nothing to refresh). Today all 15 tables warn as older than 12 months.
2. If `new_load` = 1: run `97_` with `MODE = plan` first to see what is missing, then `MODE = copy` with the agreed `SCOPE` to archive the new load. On a new load `97_` also runs steps 2, 4, 5, 6, 8, 11 and 7 (`52_` -> `54_` -> `55_` -> `56_` -> `71_` -> `82_` -> `57_`) and checks the schemas against the locks.
3. Run `98_` and send new names / near misses for review; approved changes become `focus_dictionary_v2` / `keyword_list_v3` (never edit v1 in place).
4. Re-run `99_` if any feature or status changed.
5. Re-run `91_` to `93_` only on request (business lists are not part of the monthly job).

The monthly job (task 1 `96_`, task 2 `97_` only when `new_load` = 1) is designed in `95_` section 6 and will be created once an owner is named and approved.

### 3.4 Archive scopes in `97_` (from run `20261123T112007`)

| `SCOPE` | Loads | Rows |
| --- | --- | --- |
| `final_plus_small` (last load of every table + all loads of tables under 300 M rows) | 399 | 1.12 bn |
| `score_full` (all loads of the 4 score tables) | 147 | 7.43 bn |
| `all` | 542 | 12.09 bn |

## 4. Known traps

* `IS_LATEST_FLAG = 'Y'` also keeps "stale latest" rows from older loads; `81_` and `96_` report them.
* Through the Spark connector: `REGEXP_LIKE` fails silently (use `ILIKE` / `LIKE`); `AS rows` is reserved (use `row_count`); `DATE` / `START_DATE` in `PUBLICATION` and `MEDICAL_EVENT` are VARCHAR (use `TRY_TO_DATE`); cast `SE_ID::VARCHAR`; DECIMAL counts must be cast to double before `.toPandas()`.
* The snapshot folder `snapshot/load=2025-06-30/` is written as a constant in several notebooks (for example `96_`, `98_`, `72_`). After a new load, `52_` writes a new `load=<date>` folder: update those constants before re-running.
* `SYS_TENANT`: filter `'US'` on person tables only, never on `PUBLICATION`, `CLINICAL_TRIAL`, `MEDICAL_EVENT`.
* `LOAD_ID` as a partition folder reads back as a number; cast to string before joins.
* KER-10 metric view: use `MEASURE()`, `GROUP BY ALL`, aggregate before joining.
* Veeva data stop at 2025-03-06 (hub 2025-06-30): T1 / T3 are identical for NBA 3.1 cohorts C2 to C22.
* No payment columns in any field-facing export; use "influence / authority" wording, not "KOL".

## 5. Open items

* Archive scope decision for `97_`, then a `copy` run (N3).
* Monthly job owner (X1) and approval.
* Fresh Veeva load (X2), or a written acceptance of the stale data for G3.
* Reviewers (Q9) for the `93_` review pack and the `98_` review sheet (X5).
* NBA 3.1 model, target and split (I1, I4) for the Phase 2 model tests (E5 to E7) and `t3_decisions`.
* Licence / compliance answers (X3: Q1, Q2) before any rep-facing use.
* Markdown version of the feature dictionary (`99_veeva_link_feature_dictionary.md`).
