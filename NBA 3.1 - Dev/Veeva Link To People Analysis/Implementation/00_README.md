# Veeva Link Key People for NBA 3.1: Implementation (start here)

This folder is a tidied copy of everything numbered 50 and above in the parent folder `Veeva Link To People Analysis`. The 28 original files are reduced to 8: one plan file, one notebook per phase, this README and the spot-check CSV. The originals in the parent folder are unchanged.

**Source:** Snowflake `CPH_DB_PROD.ANALYTICS_V2.ANLT_VEEVA_LINK_*` (15 in-use tables), read through the Spark Snowflake connector with secret scope `US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`.
**Output root (`OUT`):** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/veeva_link_to_people/`
**Refresh cadence:** Veeva Link is purchased, HCP-level, slow-changing data (closer to demographic data than to claims). The flow is re-run only when a new Veeva delivery is bought and loaded, not on a monthly schedule.
**Status (2026-11-23):** Phases 0 and 1 are done. Phase 2 is done except the model tests, which wait for the NBA 3.1 model (I1, I4). Phase 3 is built, but the review pack has not been sent yet. Phase 4 monitoring and docs are built; the archive copy and the refresh owner are waiting on decisions.

---

## 1. What is in this folder

| # | File | Type | What it is |
| --- | --- | --- | --- |
| 00 | `00_README.md` | Guide | This file: map, run order, results, traps, open items |
| 01 | `01_veeva_link_plans.md` | Plan | Master readiness plan + the 5 phase working plans, in one file (Parts 0 to 5) |
| 10 | `10_phase0_data_foundation` | Notebook | Phase 0: snapshot, config, spine, activity, features, acceptance checks |
| 20 | `20_phase1_t1_t2_features` | Notebook | Phase 1: T1 / T2 features on the cohort calendar + spot check |
| 21 | `21_spot_check_review_template.csv` | Data | Blank sheet for business review of the 10 spot-check HCPs |
| 30 | `30_phase2_t3_features_and_tests` | Notebook | Phase 2: score history, T3 + cross features, signal and segment tests |
| 40 | `40_phase3_business_outputs` | Notebook | Phase 3: business lists, action hints, review pack |
| 50 | `50_phase4_operations` | Notebook | Phase 4: freshness, archive / refresh, dictionary report, feature dictionary |

The numbers follow the phases (10 = Phase 0, 20 = Phase 1, and so on), so the folder sorts in run order.

Every phase notebook has the same layout:
* A **Read me first** cell at the top with a step table: what each step does, which original notebook it came from, its checks, when to run it, and the last run results.
* A **Feature dictionary** cell (second cell) in `10_`, `20_` and `30_`: every feature built in that notebook with tier, family, source tables, formula / rule, window and status, plus the business rules and logic of that phase. `40_` has a **Business rules dictionary** instead (list definitions and the B2 hint rules), because it builds no model features. The feature rows come from the feature dictionary output of step 4.4 (run `20261123T111314`) and the `FEATURE_SPEC` lists in the code.
* One section per original notebook, headed `## <step> <name>` with *Original notebook: `NN_...`* under it. Each cell title starts with the step number (for example `0.3 | Checks A2 to A5`), so the notebook outline in the side bar reads in order.
* The code is copied **unchanged** from the original notebooks; only empty cells were dropped and headings moved one level down.

## 2. Where each original file went

| Original file (parent folder) | Now in | Step |
| --- | --- | --- |
| `50_veeva_link_nba_3_1_readiness_plan.md` | `01_veeva_link_plans.md` | Part 0 |
| `51_veeva_link_phase0_working_plan.md` | `01_veeva_link_plans.md` | Part 1 |
| `52_post_implementation_readme.md` | `00_README.md` (rewritten) | - |
| `52_veeva_link_snapshot_freeze` | `10_phase0_data_foundation` | 0.1 |
| `53_veeva_link_config_v1` | `10_phase0_data_foundation` | 0.2 |
| `54_veeva_link_spine_map` | `10_phase0_data_foundation` | 0.3 |
| `55_veeva_link_long_activity` | `10_phase0_data_foundation` | 0.4 |
| `56_veeva_link_features_on_spine` | `10_phase0_data_foundation` | 0.5 |
| `57_veeva_link_acceptance_checks` | `10_phase0_data_foundation` | 0.6 |
| `60_veeva_colocation_idn_combined_signal_test` | `30_phase2_t3_features_and_tests` | 2.A (appendix, reference) |
| `70_veeva_link_phase1_working_plan.md` | `01_veeva_link_plans.md` | Part 2 |
| `71_veeva_link_phase1_features` | `20_phase1_t1_t2_features` | 1.1 |
| `72_veeva_link_spot_check` | `20_phase1_t1_t2_features` | 1.2 |
| `72_veeva_link_review_template.csv` | `21_spot_check_review_template.csv` | - |
| `80_veeva_link_phase2_working_plan.md` | `01_veeva_link_plans.md` | Part 3 |
| `81_veeva_link_score_history` | `30_phase2_t3_features_and_tests` | 2.1 |
| `82_veeva_link_t3_features` | `30_phase2_t3_features_and_tests` | 2.2 |
| `82_veeva_colocation_idn_signal_test_ker_10` | `30_phase2_t3_features_and_tests` | 2.3 |
| `83_veeva_link_t3_tests` | `30_phase2_t3_features_and_tests` | 2.4 |
| `90_veeva_link_phase3_working_plan.md` | `01_veeva_link_plans.md` | Part 4 |
| `91_veeva_link_business_lists` | `40_phase3_business_outputs` | 3.1 |
| `92_veeva_link_action_hints` | `40_phase3_business_outputs` | 3.2 |
| `93_veeva_link_review_pack` | `40_phase3_business_outputs` | 3.3 |
| `95_veeva_link_phase4_working_plan.md` | `01_veeva_link_plans.md` | Part 5 |
| `96_veeva_link_freshness_check` | `50_phase4_operations` | 4.1 |
| `97_veeva_link_archive_refresh` | `50_phase4_operations` | 4.2 |
| `98_veeva_link_dictionary_report` | `50_phase4_operations` | 4.3 |
| `99_veeva_link_feature_docs` | `50_phase4_operations` | 4.4 |

The signal test `60_` was run before Phase 1 (plan Part 0, section 5.2) and is superseded by its KER-10 re-run (step 2.3), so it now sits as an appendix next to that re-run.

## 3. The flow at a glance

```
Snowflake ANLT_VEEVA_LINK_*
  -> Phase 0  (10_)  snapshot -> config -> spine -> activity -> features -> acceptance A1-A21   [gate G0]
  -> Phase 1  (20_)  T1 / T2 features x 43 cohorts (K1-K7) -> spot check                        [gate G1]
  -> Phase 2  (30_)  score history (H) -> T3 + cross features (L) -> tests (C, S, R2)             [gate G2, model tests open]
  -> Phase 3  (40_)  B0 / B1 / B4 lists (M) -> B2 hints -> B3 review pack (P)                   [G3 business part, offline only]
  -> Phase 4  (50_)  on a new data purchase: freshness -> archive / refresh -> dictionary report -> feature docs (N)
```

## 4. How to run

### 4.1 Before you start

* Attach serverless compute (the Snowflake connector works from serverless). Use Spark (`spark.read`, `dbutils.fs.ls`) for the volume; `os.listdir` on the volume fails on serverless.
* Check access: Snowflake secrets in the scope above, read on `kerendia_metric_views.mv_kerendia_nbrx` (KER-10), the HCP Universe parquet, the MDM affiliation and hierarchy tables, and `cp_ker_hcp_2026q4` (segments).
* Every step writes a new `run=<ts>` folder or overwrites only its own outputs; `archive/` is never overwritten.
* **Run step by step, not with Run all.** Each step begins with its own setup cell, so it can be run alone. Read the check table at the end of each step and stop if a check fails.

### 4.2 Full build, in order

| Order | Notebook | Step | Check | Typical use |
| --- | --- | --- | --- | --- |
| 1 | `50_phase4_operations` | 4.1 freshness | N1, N2; `new_load`, warn flags | Always first: tells you whether there is new data |
| 2 | `10_phase0_data_foundation` | 0.1 snapshot | A1 | Only on a new load |
| 3 | `10_phase0_data_foundation` | 0.2 config | config row counts | Normally skip (config is fixed, P4-D7) |
| 4 | `10_phase0_data_foundation` | 0.3 to 0.5 | A2 to A5, A7, A8 | After step 0.1 |
| 5 | `10_phase0_data_foundation` | 0.6 acceptance | A1 to A21 all pass | Gate before Phase 1 |
| 6 | `20_phase1_t1_t2_features` | 1.1 | K1 to K7 | T1 / T2 features for all cohorts |
| 7 | `20_phase1_t1_t2_features` | 1.2 | spot-check pass | Optional after each rebuild |
| 8 | `30_phase2_t3_features_and_tests` | 2.1 then 2.2 | H1 to H3, L1 to L6 | T3 + cross features |
| 9 | `30_phase2_t3_features_and_tests` | 2.3, 2.4 | C1 to C3, S1 to S4 | Optional tests; R2 waits for HCP claims features (I5) |
| 10 | `40_phase3_business_outputs` | 3.1 to 3.3 | M1 to M8, P1, P2 | Business outputs, on request |
| 11 | `50_phase4_operations` | 4.3 | N8, N9 | After a new load; send the review sheet to Medical Affairs / brand |
| 12 | `50_phase4_operations` | 4.4 | N10 to N12 | After any feature change |

### 4.3 Refresh when new Veeva data is bought (`50_phase4_operations`)

Run this only when a new Veeva delivery has been purchased and loaded in Snowflake. Between deliveries the features do not change, so nothing needs to run.

1. Run 4.1 to confirm the new delivery has landed. If `new_load` = 0: the delivery is not in Snowflake yet; stop. (Today all 15 tables warn as older than 12 months; for purchased data this only says when the last delivery was.)
2. If `new_load` = 1: run 4.2 with `MODE = plan` to see what is missing, then `MODE = copy` with the agreed `SCOPE`. On a new load 4.2 also runs the refresh chain (`52_` -> `54_` -> `55_` -> `56_` -> `71_` -> `82_` -> `57_`) and checks the schemas against the locks.
3. Run 4.3 and send new names / near misses for review; approved changes become `focus_dictionary_v2` / `keyword_list_v3` (never edit v1 in place).
4. Re-run 4.4 if any feature or status changed.
5. Phase 3 (`40_`) is not part of the refresh; re-run only on request.

Archive scopes in 4.2 (run `20261123T112007`): `final_plus_small` 399 loads / 1.12 bn rows; `score_full` 147 loads / 7.43 bn rows; `all` 542 loads / 12.09 bn rows.

### 4.4 Constants you may need to update

| Where | Constant | Why |
| --- | --- | --- |
| 3.2 setup | `B0_RUN = "20261123T103200"` | Must be the run id printed by step 3.1 |
| 3.3 | runs of 3.1 / 3.2 it reads | Check they are the runs just built |
| 0.2 setup | `DOCS` | Points to `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_1_develop_sm/...` |
| 1.2 setup | `KOL_CSV` | Points to `31_veeva_kol_list.csv` in the same `wenjie.chen` folder; the review CSV is written next to it |
| 2.A setup | `MD` | Points to `40_veeva_link_data_assessment_v2.md` in `wenjie.chen/.../kerendia_nba_3_1_develop` |
| 4.2 cell O1b | `HERE`, `CHAIN` | Refresh chain calls the original step notebooks in the `wenjie.chen ..._sm` folder by path |
| several steps (e.g. 1.2, 4.1, 4.3) | `snapshot/load=2025-06-30/` | After a new load, 0.1 writes a new `load=<date>` folder; update the constant |

2026-11-24: the files in `wenjie.chen` folders no longer exist, so in these Implementation notebooks `DOCS` (0.2), `KOL_CSV` (1.2) and `MD` (2.A) now point to the parent folder `Veeva Link To People Analysis` (your copies), and the 1.2 review CSV is written to `21_spot_check_review_template.csv` in this folder. `HERE` / `CHAIN` in 4.2 still point to `wenjie.chen` and would fail on a new load. Step 2.A also needs `USE CATALOG` on `cph_db_prod` (it fails without it).

## 5. Results so far (QC summary)

Full numbers are in the run logs of `01_veeva_link_plans.md` (Part 1 section 8, Part 2 section 10, Part 3 section 10, Part 4 section 10, Part 5 section 10).

| Phase | Step | Run | Checks | Key numbers |
| --- | --- | --- | --- | --- |
| 0 | 0.6 acceptance | `20261119T103159`, re-run `20261123T085928` | A1 to A21 pass (21 of 21) | Universe 294,727; matched 228,930 (77.7%); scored 147,487; Spark and Snowflake routes give the same value on every check; gaps vs the assessment within 0.05% |
| 0 | 0.3 spine | - | A2 to A5 pass | SCORED 147,487 / IN_VEEVA_UNSCORED 81,443 / NOT_IN_VEEVA 65,797 |
| 1 | 1.1 features | `20261123T085209` | K1 to K7 pass | 52 features, 294,542 NPIs x 43 cohorts |
| 1 | 1.2 spot check | 2026-11-23 | pass | 10 HCPs; 0 card values changed after keyword_list_v2; KOL-list counts 0 differences |
| 2 | 2.1 score history | `20261123T092427` | H1 to H3 pass | 33 to 38 loads per score table; `CLINICAL_LEADER` starts 2024-08-01 |
| 2 | 2.2 T3 + cross | `20261123T093214` | L1 to L6 pass | 86 partitions (43 cohorts x 2 versions); as-of null for 15 early cohorts |
| 2 | 2.3 KER-10 signal test | `20261123T095952` | partition / writer checks pass | Idea 2 (expert peer writer) not robust; keep IDN expert share and practice peer flag as E7 candidates |
| 2 | 2.4 R4 / R2 tests | `20261123T100623`, `20261123T101417` | S1 to S4 pass | R2 interim (raw claims) |
| 3 | 3.1 lists | `20261123T103200` | M1 to M4, M6, M8 pass | B1 18,208 Non-target experts; B4 13,499 experts in 2,296 IDNs |
| 3 | 3.2 hints | `20261123T103700` | M5 to M7 pass | 32,133 NPIs (10.9%) with a hint |
| 3 | 3.3 review pack | `20261123T103851` | P1, P2, M6 pass | 150 rows; not yet sent |
| 4 | 4.1 freshness | `20261123T110157` | N1, N2 pass | No new load; all 15 tables older than 12 months |
| 4 | 4.2 archive / refresh | `20261123T112007` | N4, N6, N7 pass; N3, N5 n/a | Plan mode; archive empty; schemas equal the locks |
| 4 | 4.3 dictionary report | `20261123T110829` | N8, N9 pass | 0 new / removed names; review sheet 21 rows |
| 4 | 4.4 feature dictionary | `20261123T111314` | N10 to N12 pass | 83 locked columns |

## 6. Known traps

* `IS_LATEST_FLAG = 'Y'` also keeps "stale latest" rows from older loads; steps 2.1 and 4.1 report them.
* Through the Spark connector: `REGEXP_LIKE` fails silently (use `ILIKE` / `LIKE`); `AS rows` is reserved (use `row_count`); `DATE` / `START_DATE` in `PUBLICATION` and `MEDICAL_EVENT` are VARCHAR (use `TRY_TO_DATE`); cast `SE_ID::VARCHAR`; cast DECIMAL counts to double before `.toPandas()`.
* `SYS_TENANT`: filter `'US'` on person tables only, never on `PUBLICATION`, `CLINICAL_TRIAL`, `MEDICAL_EVENT`.
* `LOAD_ID` as a partition folder reads back as a number; cast to string before joins.
* KER-10 metric view: use `MEASURE()`, `GROUP BY ALL`, aggregate before joining.
* Veeva data stop at 2025-03-06 (hub 2025-06-30): T1 / T3 are identical for NBA 3.1 cohorts C2 to C22.
* No payment columns in any field-facing export; use "influence / authority" wording, not "KOL".
* Phase 4 in one notebook: 4.2 takes `new_load` from a job task named `freshness`; when run interactively it falls back to the latest 4.1 run. If a job is ever built from `50_phase4_operations`, revisit that task-value hand-off.

## 7. Open items

* Archive scope decision for 4.2, then a `copy` run (N3).
* Refresh owner (X1): who triggers the refresh when a new delivery is bought. A scheduled monthly job (plan Part 5, section 6) is no longer needed; at most an on-demand job.
* Fresh Veeva load (X2), or a written acceptance of the stale data for G3.
* Reviewers (Q9) for the 3.3 review pack and the 4.3 review sheet (X5).
* NBA 3.1 model, target and split (I1, I4) for the Phase 2 model tests (E5 to E7) and `t3_decisions`.
* Licence / compliance answers (X3: Q1, Q2) before any rep-facing use.
* Markdown version of the feature dictionary.
