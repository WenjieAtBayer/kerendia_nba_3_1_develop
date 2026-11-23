# Veeva Link Key People: Phase 2 Working Plan (T3 scores and leakage tests)

**Parent plan:** `50_veeva_link_nba_3_1_readiness_plan.md`, section 5, Phase 2 (R1 to R5), section 6 (E5 to E7), gate G2, decision D2  
**Builds on:** Phase 0 (`51_`, notebooks `52_` to `57_`, acceptance run `20261123T085928`, 21 of 21 pass) and Phase 1 (`70_`, notebooks `71_` and `72_`, run `20261123T085209`, K1 to K7 pass, keyword_list_v2)  
**Goal:** pass gate G2: prescribing-overlap and time-split tests done; one decision per T3 feature (model, business rule only, or wait for archive history); E5 and E6 run (E7 if the cross features are built)  
**Status:** in progress. R0 (`81_`, run `20261123T092427`) and R1 (`82_`, run `20261123T093214`) done, all checks pass (section 10). Next: R5, R4 (I6, I7 now readable). R2 waits on I5; R3 and E5 to E7 wait on I1 / I4  
**Date:** November 23, 2026

---

## 1. Starting point

| Already done | Where |
| --- | --- |
| T3 candidate table for 2 test anchors, one row per `PROVIDER_ID` (294,727 rows), 16 columns | `56_veeva_link_features_on_spine`, `OUT/features/t3/anchor=<a>/` |
| T1 + T2 block at `NPI_NUMBER` x `COHORT_ID` (294,542 NPIs x 43 cohorts) | `71_`, `OUT/features_phase1/t1_t2/` |
| Focus-name dictionary v1 (17 `CLINICAL_LEADER` / 147 `FOCUS_AREA` / 135 `DIGITAL_REACH`) | `OUT/config/focus_dictionary_v1` |
| Colocation x Veeva signal test (one feature at a time, not model lift) | `60_veeva_colocation_idn_combined_signal_test`; `50_` section 5.2 |

`OUT = /Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/veeva_link_to_people/`

### 1.1 Current T3 table (`56_`, anchor 2025-10-23, checked 2026-11-23)

| Column | Non-null HCPs | Source |
| --- | --- | --- |
| `veeva_best_decile` | 147,487 | max in-scope decile, CL / FA / DR |
| `veeva_decile_bin` | 228,930 | binned best decile, incl. unscored |
| `veeva_cl_decile_{ckd,hf,t2d,t1d,htn}` | 22,551 / 27,853 / 46,817 / 13,340 / 55,884 | `CLINICAL_LEADER`, disease |
| `veeva_cl_decile_mra_class`, `veeva_cl_decile_sglt2_class` | 48,562 / 39,166 | `CLINICAL_LEADER`, drug class |
| `veeva_fa_decile_max_inscope` | 29,032 | `FOCUS_AREA` |
| `veeva_dr_any_inscope` | 228,930 | `DIGITAL_REACH` (flag) |
| `veeva_index_{publication,trial,event,guideline}` | 46,957 / 18,460 / 24,726 / 4,339 | `INDEX`, 0 to 10 |
| `veeva_scientific_reach` | 26,737 | `INDEX`, 0 to 4 (kept apart) |

Non-target HCPs at best decile 8 to 10: 18,208 (9 to 10: 10,113); assessment v2 has 18,209, the 1 HCP gap is the same 2-NPI matching difference seen in `57_` (A3).

## 2. New facts that shape Phase 2

### 2.1 Where T3 is look-ahead and where it is not

The scores in the snapshot are the load of 2025-03-06 (child tables). The T3 risk in `50_` ("today's view only") depends on the cohort:

| Cohorts | Cut-off vs score load | T3 status |
| --- | --- | --- |
| NBA 3.1 C2 to C22 (2025-02 to 2026-10) | cut-off on or after 2025-03-06 | **Time-valid**: the 2025-03-06 scores were known at the anchor (stale, but not look-ahead) |
| NBA 3.1 C1 (2025-01), NBA 3.0 C15 to C23 (2024-06 to 2025-02) | cut-off 2024-07-06 to 2025-02-06 | Look-ahead with the snapshot, **but can be made time-valid** from the weekly loads kept in Snowflake (2.2) |
| NBA 3.0 C01 to C14 (2023-04 to 2024-05) | cut-off before the first kept load (2024-06-27) | Look-ahead; no history to fix it |

So for the NBA 3.1 model itself, the main T3 risk is **not look-ahead but overlap with prescribing volume** (`CLINICAL_LEADER` ranks patient volume, `50_` section 3.1): a decile that copies claims volume adds nothing, or leaks the target indirectly. R2 is the deciding test for NBA 3.1; R3 / E6 is the deciding test only where pre-score anchors are used (NBA 3.0 cohorts, or any training set that includes them).

### 2.2 Score history in Snowflake

From the Phase 0 profile (2026-11-19, to re-check in R0): the raw `ANLT_VEEVA_LINK_*` tables keep weekly full loads from 2024-06-27 to 2025-03-06 (33 to 41 `LOAD_ID`s per table), so assessment 1.5 (1) "no history" is wrong for that period. Scores look almost static: the `CLINICAL_LEADER` T2D decile is the same for 73,840 of 73,842 experts from August 2024 to March 2025. Consequences:

* An **as-of T3** (latest load on or before the cohort cut-off) can be built for cohort months 2024-06 to 2025-02 (9 months). This is the archive history that D2 says to wait for, available now for a short period.
* If scores are this stable, snapshot T3 and as-of T3 will be nearly equal, and the time-split test will mostly measure **target drift**, not score leakage. R0 measures the stability per score family so E6 can be read correctly.

### 2.3 Grain

The `56_` T3 table is keyed on `PROVIDER_ID` with one anchor. Phase 2 needs `NPI_NUMBER` x `COHORT_ID`, the same as `71_` (same NPI rule: 174 providers without NPI dropped; 11 NPIs on 2+ providers kept once, all share one `SE_ID`).

## 3. Decisions for Phase 2

| # | Decision | Detail |
| --- | --- | --- |
| P2-D1 | **Separate table** | T3 stays in `OUT/features_phase2/t3/COHORT_ID=<id>/`, never joined into `features_phase1/t1_t2/` (P1-D4, D2). Only E5 to E7 and the business lists read it |
| P2-D2 | **Two T3 versions** | `t3_snapshot` (2025-03-06 load for every cohort) and `t3_asof` (latest load on or before the cut-off; null before 2024-06-27). Same columns |
| P2-D3 | **Default use** | Business rules and segmentation only (D2) until R2 and E6 say otherwise for a given feature |
| P2-D4 | **Overlap rule (R2)** | A decile is a near copy of claims volume if Spearman rho >= 0.8 with any claims volume feature of the same theme, on matched scored HCPs at cohort C2. Near copies are dropped from the model. 0.5 to 0.8: keep only if it still separates the target within claims-volume deciles (R2.3) |
| P2-D5 | **Writer definition** | KER-10 `active_nbrx_writers` in `kerendia_metric_views.mv_kerendia_nbrx` (Q11, closed). Used in R4, R5 re-run and any direct target check |
| P2-D6 | **Expert flag for R5** | Best in-scope decile 8 to 10 from the T3 version that matches the cohort (as-of where available) |
| P2-D7 | **INDEX scales** | The four 0-to-10 indices and the 0-to-4 Scientific Reach stay separate columns; no combined index |

## 4. Output layout

| Path | Content | Written by |
| --- | --- | --- |
| `features_phase2/score_history/` | Per score family x load: rows, experts, share of experts whose decile changed vs the previous load | R0 |
| `features_phase2/t3/version=snapshot/COHORT_ID=<id>/` | One row per NPI x cohort: keys, coverage status, 16 T3 columns, `veeva_score_load_date` | R1 |
| `features_phase2/t3/version=asof/COHORT_ID=<id>/` | Same, as-of load; null rows before 2024-06-27 | R1 |
| `features_phase2/cross/COHORT_ID=<id>/` | `veeva_idn_expert_share`, `veeva_idn_expert_share_zero_flag`, `veeva_practice_expert_peer_flag` | R5 |
| `features_phase2/tests/{overlap,segment,timesplit}/run=<ts>/` | One row per feature x test x measure | R2, R3, R4 |
| `features_phase2/t3_decisions/` | One row per T3 / cross feature: model / business rule / wait, with the reason | G2 |
| `features_phase2/checks/run=<ts>/` | Checks L1 to L6 (section 5.2) | R1, R5 |
| `experiments/run=<ts>/` | E5 to E7, one row per experiment x measure | E-tasks |

## 5. Tasks, notebooks and checks

| Order | ID | Notebook | Work | Done when (check) |
| --- | --- | --- | --- | --- |
| Day 1 | R0 | `81_veeva_link_score_history` | Snowflake route: list `LOAD_ID` / load dates per score table (`CLINICAL_LEADER`, `FOCUS_AREA`, `DIGITAL_REACH_FOCUS_AREA`, `INDEX`) for US experts; per load, experts with an in-scope decile and share whose decile changed vs the previous load (filters pushed to Snowflake, P0-D4; no `REGEXP_LIKE`) | Load calendar written; stability per family reported; 2.2 confirmed or corrected |
| Days 1 to 2 | R1 | `82_veeva_link_t3_features` | Build T3 at NPI x cohort for all 43 cohorts from the `56_` logic and dictionary v1; `t3_snapshot` from the frozen snapshot; `t3_asof` from the load picked per cohort in R0 (latest load <= cut-off) | Checks L1 to L4 pass |
| Day 2 | R4 | `83_veeva_link_t3_tests` | Within each call-plan segment (A to E, Non-target): KER-10 writer rate and new-writer rate by `veeva_decile_bin` at cohort C2, forward 12 months; same split within claims-volume bands | Monotonic or not, per segment; table written |
| Days 2 to 3 | R2 | `83_` | (1) Spearman rho of each CL disease / class decile, FA and INDEX vs the same-theme claims volume features (DX patient counts CKD / HF / T2D, RX class volume MRA / SGLT2, Kerendia NBRx history) at C2; (2) share of variance of the decile explained by claims volume (rank regression); (3) writer rate by decile within claims-volume deciles | One row per T3 feature with rho, R², within-band lift; overlap rule P2-D4 applied |
| Days 3 to 4 | R5 | `82_` | Cross features from `60_` logic: L1 practice = BEST_AFFL `BRAND_RANK = 1`, L4 IDN = `mdm_stg_acct_hrchy_ker` ('NA' / 'Multiple Doctors' = no IDN); self excluded; share + zero flag at IDN, practice flag only with practice size. Re-run the `60_` signal test on KER-10 writers before reusing its numbers | Checks L5 and L6 pass; `60_` results on KER-10 written next to the originals |
| Days 5 to 8 | R3 / E5 to E7 | `84_veeva_link_phase2_experiments` | Same model, target, split and selection as E0 to E4 (`73_`); add T3 (E5), time split (E6), cross features (E7). Section 6 | All runs logged; comparison with E4 written |
| Day 9 | G2 | update this file and `50_` | Decision per T3 feature (`t3_decisions`), G2 checklist | G2 checklist complete |

### 5.1 Feature list for Phase 2

| Family | Columns | Count |
| --- | --- | --- |
| Best decile | `veeva_best_decile`, `veeva_decile_bin` | 2 |
| `CLINICAL_LEADER` disease | `veeva_cl_decile_{ckd,hf,t2d,t1d,htn}` | 5 |
| `CLINICAL_LEADER` drug class | `veeva_cl_decile_mra_class`, `veeva_cl_decile_sglt2_class` | 2 |
| `FOCUS_AREA`, `DIGITAL_REACH` | `veeva_fa_decile_max_inscope`, `veeva_dr_any_inscope` | 2 |
| `INDEX` | `veeva_index_{publication,trial,event,guideline}`, `veeva_scientific_reach` | 5 |
| Cross (R5) | `veeva_idn_expert_share`, `veeva_idn_expert_share_zero_flag`, `veeva_practice_expert_peer_flag` | 3 |
| Logged, not features | `veeva_score_load_date`, `veeva_score_age_months`, `t3_version` | n/a |

19 candidate columns. Missing rule as in Phase 1: null for `NOT_IN_VEEVA`; deciles null (not 0) for unscored experts, with `veeva_coverage_status` from `71_` as the flag.

### 5.2 Checks (written to `features_phase2/checks/`)

| # | Check | Pass rule |
| --- | --- | --- |
| L1 | Grain | One row per `NPI_NUMBER` x `COHORT_ID`; NPI set equals `71_` (294,542 per cohort) |
| L2 | Reproduces Phase 0 | `t3_snapshot` for C2 equals `56_` t3 anchor 2025-10-23 on every column (after the NPI rule); coverage counts equal `57_` (scored 147,487) |
| L3 | Missing is not zero | 0 non-null T3 values for `NOT_IN_VEEVA`; no decile = 0 |
| L4 | As-of is as-of | For every cohort, `veeva_score_load_date` <= cohort cut-off in `t3_asof`; null for cut-offs before the first load |
| L5 | Self excluded | No HCP counted in its own practice or IDN share; recount on 100 random HCPs by direct self-join matches |
| L6 | Fixed schema | Columns and order equal the Phase 2 manifest on two consecutive runs |

## 6. Experiments E5 to E7 (and R3)

Same NBA 3.1 model, target, validation split and feature-selection method as E0 to E4; E4 (coverage + T1 + T2) is the comparison point.

| Exp. | Veeva columns | Cohorts | Question |
| --- | --- | --- | --- |
| E5 | E4 + T3 (`t3_snapshot`), after the R2 drops | NBA 3.1 | Do rankings add value on top of activity and profile? |
| E6a | E5 with a time split: train on NBA 3.0 C01 to C23 + NBA 3.1 C1 (cut-off before 2025-03-06), test on NBA 3.1 C2 onward | NBA 3.0 + 3.1 | Does the E5 gain hold on anchors after the score date? |
| E6b | E6a with `t3_asof` instead of `t3_snapshot` on the 2024-06 to 2025-02 cohorts | NBA 3.0 C15 to C23, NBA 3.1 C1 | Does using the score known at the time change the gain? (snapshot much better than as-of = look-ahead) |
| E7 | E5 + cross features (R5), colocation block in the baseline | NBA 3.1 | Do cross features add value on top of colocation and Veeva? Keep only if E7 beats E5, also within segments and for new writers |

**Measures** (as in `50_` section 6): validation metric, SHAP share of the T3 block and of the whole Veeva block, rank of the best T3 feature, T3 features kept after selection, stability across time folds, gain within segments A to E (R4).

**How to read E6.** Gain(E5 - E4) on the post-score test cohorts should be close to the in-time gain. A drop much larger than the drop seen for E4 alone (same split) points to T3 look-ahead; a similar drop for both is target drift. Read together with R0: if scores are static, E6b and E6a should agree.

### 6.1 Decision rule per T3 feature (G2)

| R2 overlap | R4 within segment | E5 / E6 | Decision |
| --- | --- | --- | --- |
| rho >= 0.8 | any | any | **Business rule only** (copy of claims volume) |
| rho < 0.8 | separates in most segments | kept by selection, gain holds in E6 | **Model** |
| rho < 0.8 | separates | not kept, or gain lost in E6 | **Business rule only** (B1, B2 lists) |
| any | does not separate | any | **Drop** from model and from business rules |
| as-of differs from snapshot (R0) and E6b < E6a | | | **Wait for archive history** (NBA 3.2, X1) |

## 7. Inputs needed

| # | Input | From | Needed for |
| --- | --- | --- | --- |
| I1 | NBA 3.1 model notebook, target and validation split | NBA modelling team | E5 to E7 (same as Phase 1) |
| I4 | NBA 3.0 cohort feature table and target (C01 to C26) | NBA modelling team | E6a / E6b |
| I5 | Readable NBA 3.1 HCP claims features per cohort (DX patient counts, RX class volume, Kerendia NBRx history); candidates under `03_Feature_Engineering/03_HCP_level_features/` and `03_HCP_Level_Features/10_kerendia_prior_writing` | NBA team | R2 (and the open K1 comparison of Phase 1) |
| I6 | Read access to `kerendia_metric_views.mv_kerendia_nbrx` (KER-10) | NBA team | R4, R5 re-run |
| I7 | Colocation L1 / L4 keys (BEST_AFFL, `mdm_stg_acct_hrchy_ker`) as used in `60_` | Colocation owner | R5 |
| X4 / Q6 | What `CLINICAL_LEADER` and `DIGITAL_REACH` measure | Veeva via Vendor Management | Reading R2 |

If I1 or I4 are late, R0, R1, R4 and R5 still run; R2 waits only on I5.

## 8. Gate G2 checklist

* [x] R0 score history: load calendar and stability per family (`81_`, run `20261123T092427`, H1 to H3 pass)
* [x] R1 T3 at NPI x cohort, `t3_snapshot` and `t3_asof`; L1 to L4 pass, L6 lock written (`82_`, run `20261123T093214`)
* [ ] R2 prescribing-overlap test; overlap rule applied (`83_`) — interim run on raw claims done (`83_veeva_link_t3_tests`, run `20261123T101417`); re-run on the model's claims features when I5 is available
* [ ] R3 / E6a and E6b time-split results (`84_`) — **blocked** on I1 / I4 (no NBA 3.1 model notebook, target or split; no E0 to E4 `73_` run found, checked 2026-11-23). `84_` not created
* [x] R4 segment added-value table (`83_veeva_link_t3_tests`, run `20261123T100623`; volume bands are an interim market-TRx proxy until I5)
* [x] R5 cross features built; L5, L6 pass (`82_` run `20261123T093214`); `60_` re-run on KER-10 writers (`82_veeva_colocation_idn_signal_test_ker_10` run `20261123T095952`)
* [ ] E5 run and compared with E4; E7 if R5 built — **blocked** on I1 (same reason)
* [ ] Decision per T3 / cross feature written (`t3_decisions`) and copied to `50_` (D2)

## 9. Risks for Phase 2

| # | Risk | Mitigation |
| --- | --- | --- |
| R2-1 | Scores are near static, so E6 cannot separate look-ahead from drift | R0 stability first; compare E5 vs E4 drop on the same split; E6b as-of variant |
| R2-2 | `CLINICAL_LEADER` is a copy of claims patient volume | R2 overlap rule; business-rule use only |
| R2-3 | Claims features not readable (I5) | R2 can start on the raw IQVIA LAAD DX / RX tables with the same windows; replace with the model's features when available |
| R2-4 | Score history in Snowflake is dropped or shortened by the vendor feed | R0 copies the load calendar and the per-load deciles needed for `t3_asof` to the volume once (archive point, X1) |
| R2-5 | Cross features act as practice / IDN size proxies | Shares, not flags, at IDN level; practice flag only with practice size in the model (`50_` 5.2) |
| R2-6 | T3 shown to reps before licence and compliance answers (Q1, Q2) | T3 stays model-only / offline business lists until X3 is answered |
| R2-7 | Same stale-data problem as Phase 1 (scores 20+ months old at 2026 inference) | `veeva_score_age_months` logged; refresh (X2) is a re-run of `52_` onward |
| R2-8 | (new, R0) The frozen snapshot (`IS_LATEST_FLAG = 'Y'`) keeps 'stale latest' rows the vendor stopped sending, mostly `DIGITAL_REACH` | Keep both versions; `t3_asof` uses only the rows in the picked load. Decide in G2 which one the model uses for C2 onward |

## 10. Run log

### 10.1 R0, `81_veeva_link_score_history`, run `20261123T092427` (H1 to H3 pass)

| Table | Loads (US) | First / last load | Re-loads |
| --- | --- | --- | --- |
| `CLINICAL_LEADER` | 33 | 2024-08-01 / 2025-03-06 | 1 |
| `FOCUS_AREA` | 38 | 2024-06-27 / 2025-03-06 | 1 |
| `DIGITAL_REACH_FOCUS_AREA` | 38 | 2024-06-27 / 2025-03-06 | 1 |
| `INDEX` | 38 | 2024-06-27 / 2025-03-06 | 1 |

Corrections to section 2.2:

* `CLINICAL_LEADER` starts on **2024-08-01**, not 2024-06-27. So the as-of T3 has all four tables only for cut-offs from 2024-08-06 (cohort 2024-07). The as-of T3 covers 28 cohorts; the 15 cohorts with a cut-off before 2024-08-01 get a null as-of T3.
* Only `CLINICAL_LEADER` is near static: 0 to 0.04% of in-scope rows change score vs the final load. The other families are not: `FOCUS_AREA` 29 to 46%, `DIGITAL_REACH` 35 to 66%, `INDEX` 8 to 18% of rows present in both loads have a different score (picked loads 2024-07-04 to 2025-02-06 vs 2025-03-06).
* Best in-scope decile (CL / FA / DR) differs from the final load for 3.5% to 6.4% of experts (cohorts 2024-07 to 2025-01); the top-decile flag (8 to 10) for 0.3% to 0.6%.
* `DIGITAL_REACH` shrinks at the 2025-01-02 load: matched experts with an in-scope DR score 4,540 (2024-12-05) to 2,967 (2025-01-02), 2,741 at 2025-03-06.
* **Stale latest rows (new finding):** the frozen snapshot = all rows of the 2025-03-06 load + rows whose latest version comes from an older load. In-scope, matched experts: CL 435 rows (125 experts), FA 14,823 (2,119 experts only in stale rows), DR 37,968 (1,969), INDEX 14,602 (8,148). Largest DR source: 33,108 rows from load 2024-12-26.

Outputs: `features_phase2/score_history/{load_calendar, cohort_load_pick, loads/<table>/LOAD_ID=<id>, stability, stability_best_decile, checks/run=<ts>}`. The `loads/` folder is the archive point for R2-4.

### 10.2 R1, `82_veeva_link_t3_features`, run `20261123T093214` (L1 to L4, L6 pass)

* L1: 294,542 rows in each of 86 partitions (43 cohorts x 2 versions).
* L2: `t3_snapshot` C2 equals `56_` anchor 2025-10-23 on all 16 columns (0 mismatches); 147,487 scored NPIs.
* L3: 0 non-null T3 values for `NOT_IN_VEEVA`; no decile = 0. L4: no as-of load date after its cut-off; null before 2024-08-01. L6: lock written (`schema_lock/t3_columns.json`, 23 columns); second-run comparison still to do.
* As-of uses 8 distinct load sets. Share of matched NPIs whose `veeva_best_decile` differs between snapshot and as-of: 3.8% (2024-07) down to 2.7% (2025-01); 0.66% for cohorts 2025-02 to 2025-10 (same 2025-03-06 load; the gap is the stale rows). `veeva_fa_decile_max_inscope` differs for 4.1% to 5.7% (2024-07 to 2025-01), CL CKD decile for at most 0.05%.
* Reading for E6: the CL deciles are effectively the same in both versions, so E6 cannot show CL look-ahead (R2-1); FA, DR and INDEX change enough for E6b to be informative.

Outputs: `features_phase2/t3/version={snapshot,asof}/COHORT_ID=<id>/`, `t3_version_diff`, `checks/run=20261123T093214`.

### 10.3 R5 cross features, `82_` cells R5, run `20261123T093214` (L1, L4, L5, L6 pass)

* Groups over the 294,542 NPIs: 282,856 with a practice (90,861 practices), 210,415 in a real IDN (33,061 IDNs). Keys are 1:1 (1 BH_ID per provider, 1 L1 per BH_ID, 1 hierarchy row per L1), so no fan-out.
* Cohort C2: `veeva_idn_expert_share` non-null for 186,898 NPIs (IDN with at least one other HCP), mean 0.129; zero-share flag = 1 for 20,168 (snapshot) / 20,180 (as-of); `veeva_practice_expert_peer_flag` non-null for 233,072, = 1 for 126,019 (snapshot) / 125,921 (as-of).
* L5: 100 random HCPs recounted by direct self-join, 0 mismatches. As-of cross is null for the 15 cohorts without as-of T3. L6 lock written (`schema_lock/cross_columns.json`, 8 columns).
* Outputs: `features_phase2/cross/version={snapshot,asof}/COHORT_ID=<id>/`. Groups use today's affiliation for every cohort (same as the colocation block).

### 10.4 R5 `60_` re-run on KER-10 writers, `82_veeva_colocation_idn_signal_test_ker_10`, run `20261123T095952`

Same universe, keys, windows and tests as `60_`; both writer definitions in one run. `LRX_V7` reproduces the `60_` base (233,102 HCPs with an L1 peer, 65,122 with an L1 peer writer). Partition and writer-free count checks pass.

* Writers: look-back LRx V7 9,720 vs KER-10 11,353 (every LRx writer is also a KER-10 writer); outcome 28,629 vs 31,428 (28,253 in both). KER-10 data ends at week 2026-10-16, one week before the outcome end (2026-10-23).
* Baseline outcome rate 9.7% -> 10.7% (new-writer view 5.4% -> 6.1%). All rates rise about 0.5 to 1.5 points; the reading of each test is unchanged except idea 2.

| Test (KER-10) | Result | Same reading as `60_`? |
| --- | --- | --- |
| 1a L1 expert colleague | 11.6% vs 9.5%; within own experts 22.3% vs 22.8% (no gain) | yes |
| 1b-size, peer writer = 1 | expert colleague 42.3 vs 37.1 (1-4 peers), 26.5 vs 23.2 (5-19), 10.6 vs 8.7 (20+) | yes, small gain inside size bands |
| 1c IDN expert share | zero share 12.3%, Q1 7.2% rising to Q5 13.5% (U-shape) | yes |
| 1d top writer share x top expert share | 19.5% vs 14.2% (top writer share only) | yes (LRx: 19.4 vs 13.2) |
| 2a expert peer writer (L1) | 17.2% vs 16.5%; inside writer-count bands the sign flips (1 writer 19.2 vs 16.0; 2-3 writers 16.9 vs 17.9; 4+ 16.0 vs 15.8) | **no**: LRx signs differ in 2 of 3 bands, so idea 2 is not robust |
| 3 non-writing experts in IDNs with writer share <= 5% | 18,254 experts in 2,454 IDNs (LRx 19,252 / 2,524); 10,450 non-target | yes |

Reading for R5 / E7: keep `veeva_idn_expert_share` (+ zero flag) and `veeva_practice_expert_peer_flag` (with practice size) as E7 candidates; do not build an expert-peer-writer feature (idea 2). Outputs: `features_phase2/tests/colocation_ker10/run=20261123T095952/{long, side_by_side}`.

### 10.5 R4 segment test, `83_veeva_link_t3_tests`, run `20261123T100623` (checks S1 to S4 pass, Spark recount matches)

C2 (cut-off 2025-03-06), 294,542 NPIs; outcome = KER-10 writer in weeks 2025-03-07 to 2026-03-06: 26,535 writers (9.0%); 13,888 new writers (no KER-06 NBRx in the prior 12 months). Volume band = market TRx (all LRx V7 products except Kerendia) in the prior 12 months, quartile cuts 542 / 1,619 / 3,118 (interim for I5). Segments = 2026 Q4 call plan (later than C2).

Writer rate (%) by snapshot bin 1-3 / 4-7 / 8-10, and ratio 8-10 vs 1-3:

| Segment | 1-3 | 4-7 | 8-10 | Ratio | Monotonic (rate / new-writer rate) |
| --- | --- | --- | --- | --- | --- |
| All | 6.88 | 12.2 | 20.43 | 2.97 | yes / yes |
| A High potential writer | 79.24 | 84.46 | 87.09 | 1.10 | yes / yes |
| B High potential non-writer | 3.29 | 3.93 | 5.67 | 1.72 | yes / no |
| C Lower potential writer | 76.03 | 79.85 | 81.57 | 1.07 | yes / yes |
| D Lower potential non-writer | 14.88 | 13.33 | 11.95 | 0.80 | **no (falls)** / no |
| E Field added | 0 | 0.13 | 0.18 | n/a | yes / no |
| Non-target | 0.11 | 0.29 | 0.52 | 4.73 | yes / yes |

* All HCPs, within volume bands (4 bands with >= 100 HCPs at 8-10): rate monotonic in 4 of 4 (new-writer rate 3 of 4), median ratio 2.87 (new-writer 2.04). So the bins are not only a copy of market volume.
* Within segments the gain is small where the segment already holds the writing (median ratio within bands A 1.12, C 1.06), and reversed in D. It is real but small in absolute terms in B and Non-target.
* As-of gives the same reading (ratios within 0.1 of snapshot at C2).
* Reading for G2: T3 bins separate writers overall and beyond market volume, but mostly re-state the call-plan segments; added value is limited to B and Non-target (business-list use: B1/B2), not a case for model use on its own. Final call waits on R2 (claims overlap) and E5.

Outputs: `features_phase2/tests/segment/run=20261123T100623/{rates_by_segment, shape_by_segment, rates_by_segment_volume, shape_by_segment_volume, summary_within_volume, checks}`.

### 10.6 R2 prescribing-overlap test (interim, raw claims), `83_veeva_link_t3_tests`, run `20261123T101417`

C2 base (294,542 NPIs), claims window 2024-03-07 to 2025-03-06. DX = IQVIA LAAD DX distinct patients by ICD-10 prefix (Snowflake, 279,564 NPIs with at least one theme patient); RX = LRx V7 class TRx; KER-06 paid NBRx. Rho on HCPs with a non-null feature (snapshot). Within-band = writer rate (KER-10, forward 12 months) high vs low feature band inside deciles of the same-theme claims feature (cells with >= 50 HCPs in low and high).

| Feature | Same-theme claims | rho | R² all claims | Bands read (monotonic) | Ratio within bands | Raw ratio | Reading |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `veeva_best_decile` | MKT_TRX (max) | 0.435 | 0.171 | 10 (10) | 2.22 | 2.97 | separates |
| `veeva_cl_decile_ckd` | DX_CKD_PTS | 0.588 | 0.262 | 4 (4) | 1.86 | 3.54 | separates (0.5-0.8 band, passes) |
| `veeva_cl_decile_hf` | DX_HF_PTS | 0.334 | 0.095 | 10 (0) | 0.83 | 1.09 | no separation |
| `veeva_cl_decile_t2d` | DX_T2D_PTS | 0.466 | 0.165 | 10 (10) | 1.77 | 2.39 | separates |
| `veeva_cl_decile_t1d` | DX_T1D_PTS | 0.744 | 0.409 | 4 (0) | 1.00 | 1.19 | no separation (0.5-0.8 band, fails) |
| `veeva_cl_decile_htn` | DX_HTN_PTS | 0.389 | 0.129 | 10 (6) | 1.35 | 1.67 | separates |
| `veeva_cl_decile_mra_class` | RX_MRA_TRX | 0.286 | 0.065 | 10 (3) | 1.00 | 1.41 | no separation |
| `veeva_cl_decile_sglt2_class` | RX_SGLT2_TRX | 0.662 | 0.232 | 6 (2) | 1.03 | 2.57 | no separation (0.5-0.8 band, fails) |
| `veeva_fa_decile_max_inscope` | MKT_TRX (max) | -0.101 | 0.037 | 10 (7) | 1.63 | 1.52 | separates |
| `veeva_index_publication` | MKT_TRX (max) | -0.239 | 0.091 | 10 (4) | 1.09 | 0.93 | no separation |
| `veeva_index_trial` | RX_KER_TRX (max) | 0.104 | 0.017 | 9 (1) | 0.98 | 1.54 | no separation |
| `veeva_index_event` | MKT_TRX (max) | -0.176 | 0.049 | 10 (4) | 1.06 | 0.93 | no separation |
| `veeva_index_guideline` | DX_T2D_PTS (max) | -0.119 | 0.031 | 10 (1) | 1.18 | 1.04 | weak |
| `veeva_scientific_reach` | MKT_TRX (max) | -0.134 | 0.033 | 10 (5) | 1.08 | 0.96 | no separation |

* P2-D4: no feature reaches rho >= 0.8, so none is dropped as a copy. CL deciles are the closest to claims volume (T1D 0.74, SGLT2 0.66, CKD 0.59).
* Keep as E5 candidates (separate writers inside claims bands): best decile, CL CKD, CL T2D, CL HTN, FA max in-scope.
* Raw signal is claims volume only (business rule at most): CL SGLT2 (raw 2.57 -> 1.03), CL T1D, CL MRA class, CL HF.
* INDEX scales and Scientific Reach carry no writer signal inside claims bands (ratios 0.98 to 1.18).
* Caveats: raw claims, not the model's features (I5); CKD and T1D read in only 4 bands; single cohort (C2).

Output: `features_phase2/tests/overlap/run=20261123T101417/overlap_by_feature`.

### 10.7 Inputs check (2026-11-23)

Readable from this workspace: I6 `kerendia_metric_views.mv_kerendia_nbrx` (KER-10 `active_nbrx_writers`, KER-06 `paid_nbrx`), I7 `source_provider_bhid_npi_mapping`, `cust_mdm_best_affl_publish_pd_outp_static`, `mdm_stg_acct_hrchy_ker`, and `cp_ker_hcp_2026q4` (segments for R4). Still open: I1, I4, I5.

## 11. Phase 3 results (business use of T3, copied from `90_veeva_link_phase3_working_plan.md` section 10)

Phase 3 uses the T3 and cross outputs of this phase as business rules only (D2, P2-D3), so it ran before G2 closed. Lists are at cohort C22 (`2026-10_offset7`), KER-10 writers, snapshot T3 (= as-of for every cohort from 2025-03 on). Offline only until X3 (Q1, Q2).

| Task | Notebook, run | Result | Checks |
| --- | --- | --- | --- |
| B0 list base | `91_veeva_link_business_lists`, `20261123T103200` | 294,542 NPIs; coverage SCORED 147,487 / unscored 81,441 / not in Veeva 65,614; 31,425 KER-10 writers in 2025-10-18 to 2026-10-16; 37,075 experts (1,508 with a stale-load score); data age 19.3 months | M1, M2 pass |
| B1 untargeted-authority list | `91_`, `20261123T103200` | 18,208 Non-target at decile 8-10 (10,113 at 9-10); 17,900 non-writers (12 months); top specialties FM 6,338, IM 3,618, CD 2,311; CL indication HTN 3,294, MRA class 2,822, T2D 1,568, HF 1,473 (an HCP can carry several) | M3, M6, M8 pass |
| B4 low-adoption IDN experts | `91_`, `20261123T103200` | Reproduces the KER-10 run exactly (18,254 / 2,454 IDNs / 10,450 Non-target); at the list date (13-week look-back to 2026-10-16) 13,499 experts in 2,296 IDNs (Non-target 7,986, B 2,561); largest IDNs Cleveland Clinic 393, Trinity 366, Piedmont 335 | M4, M6, M8 pass |
| B2 action hints | `92_veeva_link_action_hints`, `20261123T103700` | 32,133 NPIs (10.9%) with a hint; primary: CARDIORENAL_CLASS 9,456, SCIENTIFIC_CONTENT 7,380, P2P_SPEAKER 4,921, CLINICAL_EVIDENCE 3,333, DISEASE_HF 2,835, DISEASE_T2D 2,465, DISEASE_CKD 1,743 | M5, M6, M7 pass |
| B2.1 sense check at C2 | `92_` | Writer rate by primary hint: DISEASE_CKD 59.72%, CARDIORENAL_CLASS 26.46%, CLINICAL_EVIDENCE 22.71%, DISEASE_T2D 21.18%, P2P_SPEAKER 18.88%, SCIENTIFIC_CONTENT 10.03%, DISEASE_HF 8.54%, no hint 7.55%. 20 segment x hint cells below their segment average: DISEASE_HF in every segment tested (A, B, D, E, Non-target; C has only 92 HCPs, not tested); 5 of 7 hints in D | table written |
| B3 review pack | `93_veeva_link_review_pack`, `20261123T103851` | 150 rows (15 per list / hint) with evidence and feedback columns; cover note with data age and the R4 rate caveat | P1, P2, M6 pass; **not yet sent** |

What this means for the G2 decisions (`t3_decisions`, still open):

* `veeva_best_decile` / `veeva_decile_bin`: business-list use confirmed (B1, B4); model use still waits on E5 / E6 (blocked on I1).
* `veeva_cl_decile_hf`: no writer signal in R2 and below segment average as a hint in B2.1: candidate for drop from hints and from the model, pending B3 feedback.
* `veeva_cl_decile_mra_class`, `veeva_cl_decile_sglt2_class`: messaging hint only (R2: claims volume; B2.1: CARDIORENAL_CLASS above average outside D and E).
* Cross features: B4 uses the IDN peer writer share and the expert flag only; `veeva_idn_expert_share` and `veeva_practice_expert_peer_flag` stay E7 candidates.

Open for Phase 3: reviewers (Q9), send the pack and log feedback, X3 (Q1, Q2) before any rep-facing use.
