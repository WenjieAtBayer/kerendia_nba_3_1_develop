# Veeva Link Key People: Phase 4 Working Plan (operations)

**Parent plan:** `50_veeva_link_nba_3_1_readiness_plan.md`, section 5, Phase 4 (O1 to O4), Track X (X1, X2, X5), gate G3 ("fresh load used or its absence accepted", "feature dictionary written"), risks "stale data" and "load-to-load changes in focus names"  
**Builds on:** Phase 0 (`52_` snapshot freeze, `53_` config, `54_` spine, `55_` long activity, `56_` features, `57_` acceptance), Phase 1 (`71_` T1 / T2, schema lock), Phase 2 (`81_` score history and load archive, `82_` T3 + cross, `83_` tests), Phase 3 (`91_` to `93_` business outputs)  
**Goal:** the Veeva block can be refreshed, monitored and explained without manual work: a monthly archive and refresh job (O1), a freshness check on every run (O2), a monthly dictionary report (O3) and the final feature dictionary (O4)  
**Status:** draft for discussion. O2, O3, O4 can start now; O1 as a scheduled job needs an owner (X1) and approval before it is created  
**Date:** November 23, 2026

---

## 1. Starting point

| Already in place | Where | Reuse in Phase 4 |
| --- | --- | --- |
| One-time copy of 15 `ANLT_VEEVA_LINK_*` tables with standard filters (archive point 1) | `52_veeva_link_snapshot_freeze`, `OUT/snapshot/load=2025-06-30/` | O1 copy step |
| Per-load archive of the 4 score tables (`CLINICAL_LEADER`, `FOCUS_AREA`, `DIGITAL_REACH_FOCUS_AREA`, `INDEX`), load calendar, stability | `81_veeva_link_score_history`, `OUT/features_phase2/score_history/` | O1 archive step, O2 load dates |
| Acceptance checks (21 of 21) | `57_veeva_link_acceptance_checks` | O1 post-run checks |
| Feature chain | `54_` -> `55_` -> `56_` -> `71_` -> `82_` -> `91_` / `92_` | O1 refresh runbook |
| Schema locks | `features_phase1/schema_lock/columns.json` (T1 / T2), `features_phase2/schema_lock/t3_columns.json` (23), `cross_columns.json` (8) | O1 schema check, O4 column list |
| Config tables | `config/focus_dictionary_v1` (299 rows: 17 CL / 147 FA / 135 DR), `config/keyword_list_v2` (86 include + 13 exclude) | O3 |
| Feature manifest | `features_phase1/feature_manifest` (52 T1 / T2 features) | O4 |

`OUT = /Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/veeva_link_to_people/`

## 2. Facts that shape Phase 4

| Fact (source) | Effect |
| --- | --- |
| Raw Snowflake tables keep weekly full loads: score tables 2024-06-27 (CL 2024-08-01) to 2025-03-06, 33 to 38 loads; `SCIENTIFIC_EXPERT` loads in June 2025 (`81_`, Phase 0 profile) | O1 can archive by `LOAD_ID`; a run with no new `LOAD_ID` is a valid "no new load" result, not a failure |
| No new load since 2025-03-06 (children) / 2025-06-30 (hub; `96_` run `20261123T110157`): data age 19.3 months at the Phase 3 list date (`91_`) | O2 warns today on the "> 12 months" rule; G3 needs X2 (fresh load) or an explicit acceptance of the stale data |
| Hub vs children gap is 3.8 months (`96_`) | Under the 6-month rule of O2, but logged every run |
| `IS_LATEST_FLAG = 'Y'` keeps stale rows from older loads (`81_`: DR 37,968 of 63,674 in-scope rows) | O1 archives per load, not only latest rows; O2 reports the stale-row share per score table |
| Some features read fixed windows that end at the data cut-off (U7) | A refresh changes inputs only; code and schema stay the same (risk "building on old data" in `50_` 9) |
| `REGEXP_LIKE` fails silently through the Spark connector; DATE columns in `PUBLICATION` / `MEDICAL_EVENT` are VARCHAR | O1 and O3 keep the `ILIKE` / `TRY_TO_DATE` rules of Phase 0 |
| T3 decisions per feature are not final (`80_` checklist; E5 / E6 blocked on I1) | O4 writes a status column (model / business rule / wait) and is re-issued when G2 closes |

## 3. Decisions for Phase 4

| # | Decision | Detail |
| --- | --- | --- |
| P4-D1 | **Monthly cadence, load-driven** | The job runs monthly (first working Monday). It archives and refreshes only if Snowflake shows a new `LOAD_ID` for any in-use table; otherwise it writes the freshness log (O2) and stops |
| P4-D2 | **Archive is append-only** | `OUT/archive/<table>/LOAD_ID=<id>/` with load date and row count; never overwritten. Snapshot copies (`OUT/snapshot/load=<date>/`) follow the same rule |
| P4-D3 | **Refresh = re-run, not redesign** | New load -> run the chain `52_` -> `54_` -> `55_` -> `56_` -> `71_` -> `82_` with the same code and config; `57_` acceptance thresholds are re-based on the new load (counts reported, match rate must stay within 1 point of 77.7% / 83.2%) |
| P4-D4 | **Schema is locked** | A refresh that changes any locked column list fails; new focus names or keyword hits go to the O3 report, never into new columns (S1) |
| P4-D5 | **Freshness thresholds** | Warn if a child table is more than 6 months older than the hub, or any table is more than 12 months old (`50_` O2). Warn does not stop the run; it is printed on every list and log |
| P4-D6 | **Job creation needs approval** | The scheduled job (O1) is created only after the owner (X1) is named and the user approves; until then the notebooks run on demand |
| P4-D7 | **Dictionary changes go through review** | O3 proposes rows; Medical Affairs / brand approve (X5); approved rows become `focus_dictionary_v2` / `keyword_list_v3`, never edited in place |
| P4-D8 | **One feature dictionary** | O4 is one table + one markdown file covering T1, T2, T3 and cross features, same style as the digital and field documents |

## 4. Output layout

| Path | Content | Written by |
| --- | --- | --- |
| `archive/<table>/LOAD_ID=<id>/` | Raw rows of one load (US, not deleted), `load_date`, `src_load_id` | O1 |
| `archive/load_calendar/` | One row per table x `LOAD_ID`: load date, rows, experts, archived flag | O1 |
| `ops/freshness/run=<ts>/` | One row per table: last load date, data cut-off, data age (months), hub gap, stale-row share, warn flags | O2 |
| `ops/refresh_log/run=<ts>/` | Steps run, run ids of `52_` to `82_`, acceptance result, schema check | O1 |
| `ops/dictionary_report/run=<ts>/` | New focus names (by table, with expert counts), new keyword hits and near misses, removed names | O3 |
| `docs/feature_dictionary/run=<ts>/` | One row per feature: name, family, tier, source table, rule in plain language, window, null meaning, status (model / business rule / wait) | O4 |
| `99_veeva_link_feature_dictionary.md` (this folder) | Markdown version of O4 for business readers | O4 |

## 5. Tasks, notebooks and checks

| Order | ID | Notebook | Work | Done when (check) |
| --- | --- | --- | --- | --- |
| Days 1 to 2 | O2 | `96_veeva_link_freshness_check` | Snowflake: max `LOAD_ID` / load date per in-use table (pushed down); volume: last archived load; data cut-off per table (max activity date where relevant: publications, events, trials, payments); data age vs today; hub gap; stale-row share for the 4 score tables (`IS_LATEST_FLAG = 'Y'` rows whose load is older than the table's last load) | N1: one row per in-use table (15); N2: latest cut-off per table = `52_` snapshot manifest, and the 4 score tables' last load = `81_` load calendar (the `81_` stale counts are on in-scope matched rows only, so they are not comparable with the all-row counts here); warn flags set as P4-D5 |
| Days 2 to 4 | O1a | `97_veeva_link_archive_refresh` (archive step) | From `52_` and `81_` code: list new `LOAD_ID`s vs `archive/load_calendar`; copy each new load once (P4-D2); back-fill the full history of all 15 in-use tables that are not yet archived (today only the 4 score tables are) | N3: archived row counts = Snowflake counts per load; N4: re-running with no new load writes nothing and exits "no new load" |
| Days 4 to 5 | O1b | `97_` (refresh step) | If O1a found a new load: run the chain (P4-D3) with `dbutils.notebook.run` or job tasks; collect run ids; run `57_`; compare schemas to the locks (P4-D4); re-run `91_` / `92_` only on request | N5: acceptance passes; N6: schemas equal the locks; N7: refresh log written. Dry run on the current snapshot (no new load) must reproduce Phase 0 to 2 numbers |
| Day 5 | O1c | Job (after approval, P4-D6) | Lakeflow Job: task 1 `96_`, task 2 `97_` (condition: new load), monthly schedule, failure email to the owner | Job created and one scheduled run succeeds |
| Days 3 to 4 | O3 | `98_veeva_link_dictionary_report` | (0) once: write `config/focus_names_seen_v1`, every distinct focus name in the current snapshot per table, in scope or not (v1 holds only the 299 in-scope names); (a) focus names in the latest `CLINICAL_LEADER` / `FOCUS_AREA` / `DIGITAL_REACH_FOCUS_AREA` rows not in the seen list, with expert counts and a suggested theme from `keyword_list_v2` hits; (b) names in the dictionary that no longer appear; (c) trial / publication / event titles that hit an include keyword but also an exclude, and titles with in-scope disease words but no keyword hit (near misses); (d) review sheet for X5 | N8: on the current snapshot the report finds 0 new names vs the seen list, and every v1 name is still present; N9: report rows have counts and a sample of 5 titles |
| Days 5 to 7 | O4 | `99_veeva_link_feature_docs` + `99_veeva_link_feature_dictionary.md` | Build the dictionary from the manifest (52 T1 / T2), T3 lock (23) and cross lock (8): family, tier (T1 / T2 / T3), source tables, plain-language rule, window, null / 0 meaning (three-state coverage), status from `t3_decisions` (or "wait: G2 open"); add Phase 3 business uses (B1, B2, B4) | N10: every locked column has exactly one dictionary row; N11: no row without source table and rule; N12: status column filled |

### 5.1 Inputs

| # | Input | State (2026-11-23) |
| --- | --- | --- |
| K1 | Snowflake access for load listing and copy (same `SF_OPTS` as Phase 0) | Ready |
| K2 | Owner for the monthly job (X1: Data Engineering + NBA team) | **Open** |
| K3 | Fresh, aligned load (X2) | **Open**; Phase 4 works without it (dry run) |
| K4 | Medical / brand reviewers for dictionary changes (X5, Q7) | **Open** |
| K5 | `t3_decisions` table (G2) | **Open**; O4 uses "wait" until written |
| K6 | Style of the digital / field feature dictionaries | To read: `04_Promotional_Features/.../50_digital_nba_3_1_readiness_plan.md` family docs |

## 6. Job design (O1c, for approval)

| Item | Proposal |
| --- | --- |
| Name | `veeva_link_monthly_archive_refresh` |
| Tasks | `freshness` (`96_`) -> `archive_refresh` (`97_`, runs only if `freshness` reports a new `LOAD_ID`; condition task on a task value) |
| Schedule | Monthly, first Monday 06:00 Europe/Berlin (to confirm with the owner) |
| Compute | Serverless (the Snowflake connector works from serverless, Phase 0) |
| Notifications | Failure and "freshness warn" to the owner and the NBA team |
| Run as | Service principal of the NBA pipeline (to confirm), with read on the Snowflake role and write on `OUT` |
| Not in the job | Business lists (`91_`, `92_`) and the review pack (`93_`): on request, after review (P3-D1) |

## 7. Order of work

1. O2 freshness check (days 1 to 2); confirms the stale-data status for G3.
2. O1a archive and back-fill (days 2 to 4), then O1b refresh dry run (days 4 to 5).
3. O3 dictionary report (days 3 to 4), in parallel.
4. O4 feature dictionary (days 5 to 7); re-issue when G2 closes.
5. O1c job, once K2 is named and the user approves.

## 8. Risks for Phase 4

| # | Risk | Mitigation |
| --- | --- | --- |
| P4-R1 | No new load ever arrives; the job only reports stale data | O2 makes the age visible on every run; G3 records "absence accepted" if X2 is not solved |
| P4-R2 | Vendor drops old `LOAD_ID`s from Snowflake before we archive them | Back-fill all 15 tables in O1a now (only the 4 score tables are archived today) |
| P4-R3 | A new load changes focus names or adds event types | Schema lock (P4-D4); O3 report; dictionary v2 through review |
| P4-R4 | Refresh changes acceptance numbers (new experts, new matches) | `57_` thresholds re-based on the new load; match rate must stay within 1 point; changes logged |
| P4-R5 | Snowflake connector traps (`REGEXP_LIKE`, VARCHAR dates, reserved `rows`) | Reuse Phase 0 query helpers; N3 row-count check per load |
| P4-R6 | Job runs without an owner | P4-D6: no job before K2 |
| P4-R7 | Feature dictionary drifts from the code | O4 built from the schema locks and manifest, not written by hand; N10 |

## 9. Phase 4 checklist (operations)

* [x] O2 freshness check; N1, N2 pass (`96_` run `20261123T110157`)
* [ ] O1a archive: `97_` built, plan run `20261123T112007` (N4 pass); copy waits on scope decision (N3)
* [x] O1b refresh dry run: no new load, chain not run; N6, N7 pass (`97_` run `20261123T112007`); N5 runs after the first real refresh
* [x] O3 dictionary report; N8, N9 pass (`98_` run `20261123T110829`)
* [ ] O4 feature dictionary: table done, N10 to N12 pass (`99_` run `20261123T111314`); markdown `99_veeva_link_feature_dictionary.md` not yet written
* [ ] O1c monthly job created after owner (K2) and approval; one scheduled run succeeds
* [ ] Copy outcomes to `50_` Phase 4 and G3 ("fresh load used or its absence accepted", "feature dictionary written")

## 10. Run log

### 10.1 O2: `96_veeva_link_freshness_check`, run `20261123T110157` (N1, N2 pass)

* No new load (`new_load` = 0). Hub `SCIENTIFIC_EXPERT`: 7 loads 2025-06-25 to 2025-06-30, data age 16.8 months. All 14 child tables: last load 2025-03-06 (`LOAD_ID` 20250306110047), data age 20.6 months, hub gap 3.8 months.
* Warn: all 15 tables over 12 months old; no table over the 6-month hub gap.
* Latest rows equal the `52_` manifest for all 15 tables.
* Stale latest rows (latest rows from an older `LOAD_ID` than the table's last load): highest shares are `SCIENTIFIC_EXPERT` 99.9% (most rows come from the 2025-06-25 load, 5 days before its last load), `DIGITAL_REACH_FOCUS_AREA` 82.0%, `FOCUS_AREA` 46.3%, `CLINICAL_TRIAL` 42.5%, `PUBLICATION` 40.9%; lowest `CLINICAL_LEADER` 0.2%, `PAYMENT` 1.0%.
* Activity cut-off in the snapshot (dates on or before today): payments 2023-12-31, publications 2025-12-31, trials 2026-11-01, events 2026-11-19 (trial and event dates after the load are planned dates).
* Size for O1a: **12,093,862,883 rows across all loads in Snowflake** (largest: `PAYMENT` 3.93 bn, `FOCUS_AREA` 3.77 bn, `CLINICAL_LEADER` 2.99 bn, `DIGITAL_REACH_FOCUS_AREA` 0.57 bn). Each load is a full copy, so a full back-fill is about 12 bn rows; scope decision needed before O1a.

### 10.2 O3: `98_veeva_link_dictionary_report`, run `20261123T110829` (N8, N9 pass)

* `config/focus_names_seen_v1` written once: 36,050 focus names (CL 704 name x type, FA 18,426, DR 16,920).
* New names vs seen list: 0; v1 names (299) no longer present: 0.
* Keyword conflicts (include and exclude of tag `mra` both hit): trials 8, events 2, publications 81 titles.
* Near misses (disease word, no include keyword): publications diabet 43,231, renal 32,967, kidney 26,509, nephr 7,012, aldosterone 637, cardiomyopath 473; events and trials smaller. 0 for heart failure, albuminuria, proteinuria, mineralocorticoid, cardiorenal (every title with these words already hits an include keyword).
* Review sheet 21 rows for X5 at `ops/dictionary_report/run=20261123T110829/review_sheet_csv`.

### 10.3 O4: `99_veeva_link_feature_docs`, run `20261123T111314` (N10, N11, N12 pass)

83 locked columns, one row each: T1 38 (kept), T2 13 (12 kept, 1 waiting I3), T3 18 and cross 5 (wait: G2 open, with Phase 2 / 3 reading), keys and metadata 9. Output `docs/feature_dictionary/run=20261123T111314/{dictionary, dictionary_csv, checks}`. First run failed N11 / N12 on 6 columns (2 composite features without a source mapping, 4 metadata columns); fixed and re-run.

### 10.4 O1: `97_veeva_link_archive_refresh`, run `20261123T112007` (plan mode; N4, N6, N7 pass; N3, N5 n/a)

* Parameters `MODE` (`plan` / `copy`) and `SCOPE` (`none` / `final_plus_small` / `score_full` / `all`); default `plan` / `none` copies nothing.
* Archive empty so far: 542 Snowflake loads missing (12,093,862,883 rows). Size per scope: `final_plus_small` 399 loads, 1.12 bn rows (all 15 tables); `score_full` 147 loads, 7.43 bn rows (4 score tables); `all` 542 loads, 12.09 bn rows.
* No new load, so the refresh chain did not run and nothing was written to the archive (N4).
* Schemas equal the locks: T1 / T2 59 columns, T3 23, cross 8 (N6).
* Refresh log at `ops/refresh_log/run=20261123T112007/` (N7).
* Still open: archive scope decision, then a `copy` run (N3); O1c job waits on owner (K2) and approval (P4-D6).
