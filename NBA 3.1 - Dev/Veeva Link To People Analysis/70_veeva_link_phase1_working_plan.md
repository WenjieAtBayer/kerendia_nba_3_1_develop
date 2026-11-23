# Veeva Link Key People: Phase 1 Working Plan (T1 and T2 block)

**Parent plan:** `50_veeva_link_nba_3_1_readiness_plan.md`, section 5, Phase 1 (P1 to P5), section 6 (E0 to E4), gate G1  
**Builds on:** Phase 0 (`51_veeva_link_phase0_working_plan.md`; notebooks `52_` to `57_`; acceptance run `20261119T103159`, 21 of 21 pass)  
**Goal:** pass gate G1: T1 and T2 block built for all training instances, leakage check passed, fixed schema on two runs, spot-check done, E1 to E4 run and compared with E0  
**Status:** in progress: P1, P2, P4 done; keyword_list_v2 applied (run `20261123T085209`); P3 and P5 manual review open; E0 to E4 waiting on I1 / I4  
**Date:** November 19, 2026 (last update November 23, 2026)

---

## 1. Starting point

| Already done in Phase 0 | Where |
| --- | --- |
| Frozen snapshot (15 tables), DQ rules, config v1 (dictionary, keywords, stop-list, windows) | `OUT/snapshot/load=2025-06-30/`, `OUT/config/` |
| Spine `PROVIDER_ID` to `SE_ID`, three-state coverage | `OUT/spine/veeva_npi_se_map/` |
| Long, dated activity tables | `OUT/activity/{trials,publications,events,payments}/` |
| Candidate features for 2 test anchors: 29 T1 + 13 T2 (`t1_t2`), 16 T3 (`t3`), schema `config/feature_schema_v1` | `56_veeva_link_features_on_spine`, `OUT/features/` |

`56_` already covers most of P1 to P4 for single anchor dates. Phase 1 turns it into the **NBA 3.1 grain** and adds the missing pieces, the checks and the experiments.

`OUT = /Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/veeva_link_to_people/`

## 2. New facts found while preparing this plan (2026-11-19)

### 2.1 Grain of the NBA 3.1 model

The NBA 3.1 HCP features are keyed on **`NPI_NUMBER` x `COHORT_ID`** (`YYYY-MM_offset7`). Cohorts C1 to C22 = 2025-01 to 2026-10; cohort cut-off = month end + 6 days; windows end at the cut-off (inclusive) and start `w` months earlier (exclusive). NBA 3.0 cohorts C01 to C26 have anchors 2023-04 to 2025-05. (Read from `51_digital_nba_phase1_features`, which mirrors `00_cohort_config`; `00_cohort_config` itself is not readable from this account, so the rules must be confirmed there.)

### 2.2 Most NBA 3.1 cohorts see the same Veeva data

The Veeva child-table cut-off is 2025-03-06. Cohort C1 (2025-01) ends 2025-02-06; **C2 (2025-02) ends exactly on 2025-03-06**, and every later cohort ends after it. So:

* For C2 to C22, every T1 window is capped at 2025-03-06: **T1 values are the same for 21 of 22 cohorts**. Only C1 differs, by one month.
* Payment program years are 2021 to 2023 for every NBA 3.1 cohort (program year 2024 is not in the data).
* Inside NBA 3.1 cohorts, T1 behaves like a static attribute. **E2 (static totals) and E3 (windowed) will be almost the same on C1 to C22**, so the E2 vs E3 leakage test (section 6 of `50_`) only works on anchors before the cut-off, that is the NBA 3.0 cohorts (C01 to C26, 2023-04 to 2025-05).
* For inference cohorts (2026) the newest Veeva activity is 20+ months old (risk R1 below).

### 2.3 Spine and grain checks

* 11 NPIs sit on more than one `PROVIDER_ID` in the crosswalk; 174 providers have no NPI. At NPI grain these need a rule (task P1.2).
* The HCP Universe parquet holds only `PROVIDER_ID` and `C1_FLAG` to `C5_FLAG`, **no specialty**. The Veeva-specialty fallback of P3 needs the NBA 3.1 specialty source (open input I3). Veeva `SPECIALTY_1` is filled for 148,034 of 228,928 matched experts.
* Publication dates start in 2019. For NBA 3.0 anchors before 2024-01 the 5-year publication window is cut on the left (only data from 2019 onward).

## 3. Decisions for Phase 1

| # | Decision | Detail |
| --- | --- | --- |
| P1-D1 | **Grain** | `NPI_NUMBER` x `COHORT_ID`, the same as the NBA 3.1 HCP claims features; cohort helpers copied from `00_cohort_config` with its self-test |
| P1-D2 | **Cohort lists** | NBA 3.1 C1 to C22 (model); NBA 3.0 C01 to C26 (leakage test E2 vs E3 only). Both from one cohort config parameter |
| P1-D3 | **Storage** | Parquet partitioned by `COHORT_ID` under `OUT/features_phase1/` (same as P0-D3). A switch to Delta is one line if the model pipeline needs it |
| P1-D4 | **T3 stays out** | The T3 table from `56_` is not joined to any Phase 1 output; it is read only in Phase 2 (D2) |
| P1-D5 | **Indication views** | Add HF, CKD and T1D in-scope counts for trials, publications and events (D5); Kerendia total stays the main view |
| P1-D6 | **Static variant** | For E2, build the same T1 columns from the full snapshot (no window), suffix `_all` instead of `_3y` / `_5y`, in a separate table |

## 4. Output layout

| Path | Content | Written by |
| --- | --- | --- |
| `features_phase1/t1_t2/COHORT_ID=<id>/` | One row per NPI x cohort: keys, coverage flags, T1, T2, `veeva_snapshot_id`, `veeva_window_end` | P4 |
| `features_phase1/t1_static/` | E2 static T1 totals, one row per NPI | P2 |
| `features_phase1/feature_manifest/` | One row per feature: name, tier, family, rule, indication, used in E1 / E2 / E3 / E4, kept after constant check | P4 |
| `features_phase1/checks/run=<ts>/` | One row per check (section 5.2) | P4 |
| `features_phase1/spot_check/` | Profile cards for the 10 spot-check HCPs | P5 |
| `experiments/run=<ts>/` | One row per experiment x measure | E-tasks |

## 5. Tasks, notebooks and checks

| Order | ID | Notebook | Work | Done when (check) |
| --- | --- | --- | --- | --- |
| Day 1 | P1.1 | `71_veeva_link_phase1_features` | Cohort helpers and self-test copied from `00_cohort_config` (via `51_digital_nba_phase1_features`); anchor = cohort cut-off; window end = min(cut-off, table cut-off from the `52_` manifest) | Self-test passes; C1 to C22 and C01 to C26 listed with window ends |
| Day 1 | P1.2 | `71_` | NPI grain: drop the 174 providers with no NPI; for the 11 NPIs on 2+ providers keep one row (same `SE_ID`, so same values) and log them | One row per NPI per cohort; 294,542 NPIs |
| Day 1 | P1 | `71_` | Coverage flags (`veeva_coverage_status`, `veeva_has_profile`, `veeva_has_inscope_decile`, `veeva_n_inscope_themes`) at NPI grain | Counts equal the spine (`SCORED` 147,487 etc., less the NPI rule) |
| Days 2 to 3 | P2 | `71_` | T1 for every cohort from the `55_` tables, reusing `t1_features()` of `56_`; add the HF / CKD / T1D in-scope views (P1-D5); add `t1_static` (P1-D6) | Values for cohort C2 equal those of the 2025-10-23 anchor in `56_` |
| Day 3 | P3 | `71_` | T2 as in `56_`; add `veeva_specialty_fallback` (Veeva `SPECIALTY_1` only where the NBA 3.1 specialty is missing; needs I3) | Filled share reported; fallback never overrides the main specialty |
| Days 4 to 5 | P4 | `71_` | Assemble per cohort; missing rule (null for `NOT_IN_VEEVA`); composites standardised on matched HCPs of each cohort; drop features constant on the full population; write manifest | Checks K1 to K7 below pass |
| Day 5 | P5 | `72_veeva_link_spot_check` | Pick 10 HCPs from `31_veeva_kol_list.csv` (mix of segment, decile, trial / podium / no activity); print one profile card each (coverage, trials with names, publications, events, payments, profile). **Manual step**: compare each card with the Veeva Link web profile and note mismatches | 10 cards written; mismatch notes added to section 8 |
| Days 6 to 9 | E0 to E4 | `73_veeva_link_phase1_experiments` | Same NBA 3.1 model, target, split and selection method; only the Veeva block changes (section 6). E2 vs E3 also run on NBA 3.0 cohorts | All runs logged; comparison table written |
| Day 10 | G1 | update this file | Results and G1 checklist | G1 checklist complete |

### 5.1 Feature list for Phase 1

Starts from the 42 columns of `config/feature_schema_v1` (`t1_t2` table) and adds:

| Family | Added columns | Tier |
| --- | --- | --- |
| Trials | `veeva_trial_n_inscope_{hf,ckd,t1d}_5y` | T1 |
| Publications | `veeva_pub_n_inscope_{hf,ckd,t1d}_5y` | T1 |
| Events | `veeva_event_n_inscope_{hf,ckd,t1d}_3y` | T1 |
| Profile | `veeva_specialty_fallback` | T2 |
| Data age (logged, not a feature) | `veeva_window_end`, `veeva_data_age_months` | n/a |

About 52 candidate columns in total, before the constant check. Feature selection to 15 to 30 happens inside E1 to E4 with the main model's method.

### 5.2 Checks in `71_` (written to `features_phase1/checks/`)

| # | Check | Pass rule |
| --- | --- | --- |
| K1 | Grain | One row per `NPI_NUMBER` x `COHORT_ID`; NPI count per cohort equals the NBA 3.1 HCP claims features for the same cohort |
| K2 | Fixed schema | Columns and order equal the manifest on two consecutive runs |
| K3 | No look-ahead | For every cohort, the latest activity date used is on or before the window end; no payment program year after the publication rule |
| K4 | Missing is not zero | 0 non-null T1 / T2 values for `NOT_IN_VEEVA` |
| K5 | Reproduces Phase 0 | Cohort C2 values equal `56_` anchor 2025-10-23 for every common column |
| K6 | Cohort identity | Share of HCPs whose T1 values change between consecutive cohorts; expected 0 for C2 to C22 (section 2.2), non-zero for NBA 3.0 cohorts |
| K7 | Constant features | Features with one value on the full population are dropped and listed |

## 6. Experiments E0 to E4

All runs use the NBA 3.1 HCP-level model, target, validation split and feature-selection method; only the Veeva block changes.

| Exp. | Veeva columns | Cohorts | Question |
| --- | --- | --- | --- |
| E0 | none | NBA 3.1 | Baseline |
| E1 | coverage flags | NBA 3.1 | Is being tracked by Veeva informative? |
| E2 | E1 + `t1_static` | NBA 3.1, and NBA 3.0 | Does activity add value, ignoring timing? |
| E3 | E1 + T1 windowed | NBA 3.1, and NBA 3.0 | Does correct timing change the result? On NBA 3.0 cohorts, E2 much better than E3 points to leakage |
| E4 | E3 + T2 | NBA 3.1 | Do profile attributes add value? |

**Measures** (as in `50_` section 6): validation metric, SHAP share of the Veeva block, rank of the best Veeva feature, number of Veeva features kept after selection, stability of importance across time folds, gain within call-plan segments A to E.

**How to read E2 vs E3 on NBA 3.1 cohorts:** they are expected to be nearly the same (section 2.2); that is not a pass of the leakage test. The test is the NBA 3.0 run.

## 7. Inputs needed from other teams

| # | Input | From | Needed for |
| --- | --- | --- | --- |
| I1 | NBA 3.1 model notebook, target table and validation split (E0) | NBA modelling team | E0 to E4 |
| I2 | Read access to `00_cohort_config` (and `00_cohort_generation`) to confirm the cohort rules | Notebook owner | P1.1 |
| I3 | NBA 3.1 HCP specialty source | NBA team | P3 fallback |
| I4 | NBA 3.0 cohort feature table and target (C01 to C26) | NBA modelling team | E2 vs E3 leakage test |

If I1 or I4 are late, `71_` and `72_` still run; only the experiments wait.

## 8. Gate G1 checklist

* [x] P1 coverage flags at NPI x cohort grain (`71_`, 294,542 NPIs x 43 cohorts)
* [x] P2 T1 for C1 to C22 and C01 to C26, plus `t1_static` (23 window signatures)
* [ ] P3 T2 built; specialty fallback column kept but null, waiting on I3
* [x] P4 checks K1 to K7 pass (runs `20261119T113924` and `20261123T085209`); manifest written. K1 claims comparison not run (claims cohort output not readable)
* [ ] P5 spot-check: 10 cards built by `72_` (`OUT/features_phase1/spot_check/`), re-run on v2 features (same 10 HCPs, 0 card values changed); manual Veeva Link web review and mismatch notes still to do. Review template exported to `72_veeva_link_review_template.csv` (this folder) and `OUT/features_phase1/spot_check/review_template.csv`; fill in `web_matches`, `mismatch_note`, `reviewer`, `review_date`
  * MRA tag audit (2026-11-23): card 1's SZC trial is a real MRA-context hit (patients receiving spironolactone). A keyword screen for off-topic spironolactone uses (androgen excess, alopecia, transgender care, PAH) found trials 6 of 54 MRA rows, publications 4 of 407, events 1 of 138; the MRA flag flips for 4 / 4 / 1 experts. **Applied as `keyword_list_v2`** (section 10)
* [ ] E0 to E4 run and compared; E2 vs E3 on NBA 3.0 cohorts reported
* [x] Fixed schema on two runs (K2): run `20261123T085209` columns equal the schema lock of run `20261119T113924`

## 9. Risks for Phase 1

| # | Risk | Mitigation |
| --- | --- | --- |
| R1 | Stale data: T1 is the same for C2 to C22 and 20+ months old at 2026 inference | Report it as a static block; `veeva_data_age_months` logged; refresh (X2) is a re-run of `52_` to `71_` |
| R2 | E2 vs E3 cannot detect leakage on NBA 3.1 cohorts | Run the test on NBA 3.0 cohorts (I4) |
| R3 | Left-cut publication windows for anchors before 2024-01 (data from 2019) | Flag affected cohorts; compare with 3-year window in E3 |
| R4 | Payment features are the same for every NBA 3.1 cohort (program years 2021 to 2023) | Treat as static; check importance stability across folds |
| R5 | Cohort rules differ from `00_cohort_config` | Confirm with I2; self-test in P1.1 |
| R6 | Model inputs (I1) not available in time | Build and checks continue; experiments move, G1 waits |

## 10. Run log

### 2026-11-23: keyword_list_v2 applied (`55_` -> `56_` -> `71_` -> `57_` -> `72_`)

**Change.** `OUT/config/keyword_list_v2` (written by `53_`, cell "(d) keyword_list_v2") = the 86 v1 include patterns unchanged + 13 MRA exclude patterns (`%acne%`, `%androgen%`, `%hirsut%`, `%polycystic ovar%`, `%pcos%`, `%alopecia%`, `%hair loss%`, `%transgender%`, `%gender-affirming%`, `%gender affirming%`, `%feminiz%`, `%dermatolog%`, `%pulmonary arterial hypertension%`); new column `rule_type` (`include` / `exclude`). `55_` now reads v2: a tag is set when an include pattern matches and no exclude pattern of the same tag matches.

**Effect on the activity tables** (before vs after, saved and compared outside the notebooks):

| Measure | Trials | Publications | Events |
| --- | --- | --- | --- |
| `TAG_MRA` rows | 54 -> 48 | 407 -> 403 | 138 -> 137 |
| `TAG_ANY_INSCOPE` rows | 12,232 -> 12,226 | 57,414 -> 57,410 | 42,487 -> 42,486 |
| All other tags, row counts | unchanged | unchanged | unchanged |

**Effect on `71_` features** (sum over NPIs, cohort 2025-02): `veeva_trial_mra_flag_5y` 159 -> 155; `veeva_trial_n_inscope_5y` -6; `veeva_pub_n_inscope_5y` -4; `veeva_event_n_inscope_3y` -1; payment features unchanged. Same pattern on cohort 2024-06.

**Checks.**

| Notebook | Run | Result |
| --- | --- | --- |
| `55_` | A7 totals vs assessment 8.1 | unchanged, within 0.05% |
| `56_` | A8 fixed schema, row counts, missing rule | pass, both anchors |
| `71_` | `20261123T085209` | K1 to K7 all pass; K2 now compared with the previous run |
| `57_` | `20261123T085928` | 21 of 21 pass (checks do not use tags) |
| `72_` | spot-check re-run | same 10 HCPs; MRA candidate pool 100 -> 98; 0 card values changed; KOL-list counts 0 differences |

**Code fixes in this run.** `71_` write cell: the cohort-partition count used `os.listdir` on the volume, which failed on serverless (`Required key not available`); now counted with Spark. `53_` setup: documents path pointed to the old `kerendia_nba_3_1_develop` folder; now `_sm`. `72_`: new cell "Export review template to CSV" (refuses to overwrite a CSV that already has review entries).
