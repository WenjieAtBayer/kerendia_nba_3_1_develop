# Veeva Link Key People: Phase 0 Working Plan (Track U and Track X)

**Parent plan:** `50_veeva_link_nba_3_1_readiness_plan.md`, section 5, Phase 0  
**Data reference:** `40_veeva_link_data_assessment_v2.md`  
**Goal:** pass gate G0 (entry to Phase 1) with a frozen, tested Veeva snapshot and config, without waiting on external teams  
**Status:** Track U done on 2026-11-19; acceptance run `20261119T103159` passes 21 of 21 (see section 8). Track X requests still to send  
**Date:** November 19, 2026

---

## 1. Decisions for Phase 0

| # | Decision | Detail |
| --- | --- | --- |
| P0-D1 | **Source** | Snowflake `CPH_DB_PROD.ANALYTICS_V2.ANLT_VEEVA_LINK_*` through the Spark Snowflake connector (secret scope `US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`, role `BAY_CPH_CDP_PROD_CR_US_EAST_1_MVXPF_MVXPF`, warehouse `PROD_CYRUS_BI_WH`). Not the Unity Catalog copy `cph_db_prod.analytics_v2` |
| P0-D2 | **Verification** | Acceptance numbers are re-computed against the Snowflake tables as well as against the copy (two independent routes) |
| P0-D3 | **Storage** | Parquet files (not Delta tables for now) under `OUT = /Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/veeva_link_to_people/` |
| P0-D4 | **Push down, then land** | Filters (latest, not deleted, tenant) and column selection run inside Snowflake in the connector `query`. All joins and free-text matching run in Spark on the parquet copy, so the `REGEXP_LIKE` connector trap does not apply |

Checked on 2026-11-19: the Snowflake connector works from serverless; the output folder exists, is empty and is writable (parquet write, read and delete test passed).

## 2. New facts found while preparing this plan (2026-11-19)

Profiled in Snowflake with one count per table (total rows, latest rows, latest and not deleted, latest and not deleted and US).

### 2.1 Assessment 1.4 counts are latest rows across all tenants

The "Rows" column in assessment section 1.4 equals `IS_LATEST_FLAG = 'Y' AND not deleted`, **all tenants**, for every table (exact match on all 16 non-empty tables). The snapshot keeps US rows only on person tables, so it has its own baseline:

| Table | Latest, all tenants (= assessment 1.4) | Latest, US (snapshot baseline) | Raw rows in Snowflake | Loads (`LOAD_ID`) |
| --- | ---: | ---: | ---: | ---: |
| `FOCUS_AREA` | 182,423,886 | 147,166,660 | 4,568,096,086 | 38 |
| `PAYMENT` | 108,908,302 | 108,862,934 | 3,932,279,371 | 38 |
| `CLINICAL_LEADER` | 91,060,114 | 91,048,138 | 2,991,049,239 | 33 |
| `DIGITAL_REACH_FOCUS_AREA` | 27,681,001 | 22,927,230 | 677,551,241 | 38 |
| `SCIENTIFIC_EXPERT_PUBLICATION` | 11,822,427 | 9,475,374 | 355,803,504 | 38 |
| `PUBLICATION` (tenant `XX`) | 6,395,291 | n/a, keep all | 146,929,942 | 40 |
| `EVENT_ATTENDEE` | 4,917,373 | 3,829,146 | 144,643,794 | 38 |
| `INDEX` | 3,991,179 | 3,171,071 | 130,920,546 | 38 |
| `ADDRESS` | 2,771,121 | 2,417,226 | 100,909,369 | 38 |
| `SCIENTIFIC_EXPERT` | 2,531,920 | 2,215,203 | 2,573,673 | 7 |
| `SCIENTIFIC_EXPERT_CLINICAL_TRIAL` | 889,413 | 789,599 | 28,567,651 | 38 |
| `ASSOCIATION` | 803,819 | 625,710 | 24,728,891 | 38 |
| `MEDICAL_EVENT` (tenant `XX`) | 677,395 | n/a, keep all | 18,131,915 | 41 |
| `COMPANY_SPONSORSHIP` | 543,811 | 491,115 | 17,783,293 | 38 |
| `CLINICAL_TRIAL` (tenant `XX`) | 200,065 | n/a, keep all | 4,738,364 | 41 |
| `COMMUNITY_LEADER_FOCUS_AREA` (not copied) | 4,579,943 | 4,579,726 | 50,211,724 | 11 |
| `COMPANY_COLLABORATION` (not copied) | 0 | 0 | 0 | 0 |

### 2.2 Correction to assessment 1.5 (1): the raw tables do keep load history

* Assessment 1.5 (1) says `IS_LATEST_FLAG = 'Y'` on 100% of rows. That is true only after the latest filter. The raw tables keep **weekly full loads from 2024-06-27 to 2025-03-06** (33 to 41 `LOAD_ID`s per table; about 90M rows per load for `CLINICAL_LEADER`). `SCIENTIFIC_EXPERT` has 7 loads, 2025-06-25 to 2025-06-30.
* Latest rows come almost entirely from the last load (90,852,830 of 91,060,114 `CLINICAL_LEADER` latest rows are from load 2025-03-06). About 207K latest rows sit in older loads (rows not present in later loads); they are kept, to match the assessment, and counted in the DQ log.
* Scores barely move between loads: for `CLINICAL_LEADER` 'Type 2 Diabetes Mellitus', 73,840 of 73,842 US experts present in both the 2024-08-01 and 2025-03-06 loads have the same decile.
* **What it changes:** Q4 (history) is partly answered: about 9 months of weekly history exist, all before the data cut-off. They do not make T3 time-valid for 2025 to 2026 anchors, and the scores are close to static, so D2 stays as it is. The history is still useful for a stability check of T3 (Phase 2) and as the first archive points (X1). Section 1.5 (1) of the assessment should be corrected.

## 3. Output layout (parquet)

All paths are under `OUT`. Every run writes into a folder named after the snapshot, so later loads stack up as an archive (X1 reuses the same code).

| Path | Content | Written by |
| --- | --- | --- |
| `snapshot/load=<hub_load_date>/<table>/` | 15 tables, latest, not deleted, US on person tables, plus `load_date`, `src_load_id`, `snapshot_id` | U1 |
| `snapshot/load=<hub_load_date>/_manifest/` | Table, row count, max `SYS_CREATED_DT` (data cut-off), source filter, run time | U1 |
| `config/focus_dictionary_v1/`, `config/keyword_list_v1/`, `config/windows_v1/` | Config tables | U4 |
| `spine/veeva_npi_se_map/` | `PROVIDER_ID`, `NPI`, `BH_ID`, `SE_ID`, `match_route`, `veeva_coverage_status` | U2 |
| `activity/{trials,publications,events,payments}/` | Long, dated activity, matched experts only | U3 |
| `dq_log/run=<ts>/` | One row per DQ rule: rule, table, rows affected, action | U5 |
| `acceptance/run=<ts>/` | One row per check: expected, Spark value, Snowflake value, diff, pass | U8 |

## 4. Track U: tasks, notebooks and checks

Notebooks use the next free numbers in this folder. Shared helpers (Snowflake reader, paths, filters) live in the first cell of each notebook until a helper notebook is agreed.

| Order | ID | Notebook | Work | Done when (check) |
| --- | --- | --- | --- | --- |
| Days 1 to 3 | U1 + U5 | `52_veeva_link_snapshot_freeze` | For each of the 15 tables: one connector query with `IS_LATEST_FLAG = 'Y'`, `COALESCE(SYS_DELETE_FLAG, 0) = 0` (`ISDELETED` on `SCIENTIFIC_EXPERT`), `SYS_TENANT = 'US'` only on person tables, `SE_ID::VARCHAR`, `TRY_TO_DATE` on the text date columns. Large tables (`FOCUS_AREA`, `PAYMENT`, `CLINICAL_LEADER`) read in chunks by `SE_ID` hash or `SYS_TENANT` to avoid connector time-outs. DQ rules at copy time: drop column-shifted `EVENT_TYPE` rows, drop `PAST_POSITION`, drop orphan `ADDRESS` rows, normalise `PUBLICATION_TYPE`, `LPAD` ZIP to 5, Scientific Reach lookup 0 to 4, latest rows from older loads counted | Parquet row counts equal the US baseline in section 2.1; Snowflake recount equal; DQ log written |
| Days 1 to 3 | U4 | `53_veeva_link_config_v1` | Focus dictionary read verbatim from assessment 5.3 (same parser as notebook 60, cell 3) joined to `22_veeva_link_focus_name_taxonomy.csv` for theme and indication; keyword list and talk-title stop-list from `33_` section 7; windows 3 and 5 years | 17 / 147 / 135 names; every name found in the snapshot; best-decile coverage 147,489 (`CLINICAL_LEADER` 134,930, `FOCUS_AREA` 29,033, `DIGITAL_REACH` 4,710) |
| Days 4 to 5 | U2 | `54_veeva_link_spine_map` | HCP Universe parquet (`HCP_Universe_without_call_hcps`, 294,727) to `kerendia_nba_3.source_provider_bhid_npi_mapping` to snapshot `SCIENTIFIC_EXPERT` on NPI; match route recorded; the one `SE_ID` shared by 2 providers kept for both and flagged; three-state `veeva_coverage_status` | 228,932 matched (77.7%), 228,930 distinct `SE_ID`; segments A to E 65,549 of 78,813 (83.2%); unmatched 65,795 |
| Days 6 to 8 | U3 | `55_veeva_link_long_activity` | One row per expert x item: trials (role, phase, start, end, in-scope tags), publications (author position, date, type, tags), events (position, start date, tags), payments (program year, nature, type, company, amount). Tags from U4 with `ILIKE` style matching in Spark | 358,601 publications; 54,673 trials (26,006 as PI); 152,510 events; 38,305,022 payment records |
| Days 6 to 8 | U6 | copy of `11_` as `56_veeva_link_pilot_on_spine` | Replace `in_coh()` (100 `SE_ID`s) with the spine; disease deciles from `CLINICAL_LEADER` / `FOCUS_AREA` instead of `COMMUNITY_LEADER_FOCUS_AREA`; composites standardised on the full universe; one day for the `DIGITAL_REACH` ID check, then drop it from v1 if not solved | Sections A to K run on all 294,727 HCPs |
| Days 9 to 10 | U7 | inside `56_` | T1 windows end at min(anchor month, table cut-off from the U1 manifest); output columns generated from the U4 config; nulls for `NOT_IN_VEEVA` | Same column list and order on two runs |
| Day 10 | U8 | `57_veeva_link_acceptance_checks` | Re-computes every number below twice: from the parquet copy in Spark, and directly in Snowflake. Fails if any value is more than 1 point (or 1%) off | All checks pass; table written to `acceptance/` |

### 4.1 Acceptance checks (U8)

| # | Check | Expected | Source of expected value |
| --- | --- | --- | --- |
| A1 | Snapshot row counts per table | US baseline, section 2.1 | Snowflake profile, 2026-11-19 |
| A2 | HCP Universe size | 294,727 | Assessment 5.2 |
| A3 | Matched to Veeva | 228,932 (77.7%); 228,930 `SE_ID` | Assessment 5.2 |
| A4 | Segments A to E in Veeva | 65,549 of 78,813 (83.2%); A 10,401 of 11,367 (91.5%) | Assessment 6.2 |
| A5 | In-scope decile coverage | 147,489 (64.4%); CL 134,930; FA 29,033; DR 4,710 | Assessment 6.3 |
| A6 | Segment x best decile table | Table 7.2 cell by cell | Assessment 7.2 |
| A7 | Activity totals on the overlap | 358,601 / 54,673 (26,006 PI) / 152,510 / 38,305,022 | Assessment 8.1 |
| A8 | Fixed schema | Same columns on two runs | U7 |

Segment source for A4 and A6: Snowflake `PHCDW.PHCDW_TARGETING.CP_KER_HCP` (as in the assessment), `FF IN ('CR1','CR2','CR4','CR5')`, Kerendia in `PRODUCT_1` or `PRODUCT_2`, `NOTE_2` on `BAYER_ID` = `BH_ID`.

## 5. Track X: send in week 1 (does not block G0)

| ID | Request | To | Note from section 2 |
| --- | --- | --- | --- |
| X1 | Monthly archive job reusing `52_` | Data Engineering, NBA team | The weekly loads already in Snowflake (2024-06 to 2025-03) can be copied as the first archive points |
| X2 | Fresh, aligned load and refresh cadence (Q3) | Data Engineering, Vendor Management | Hub 2025-06-30, children 2025-03-06; no load since |
| X3 | Licence and compliance (Q1, Q2) | Vendor Management, Legal, Compliance | Features stay model-only until answered |
| X4 | Changelog (Q4), `COMPANY_COLLABORATION` (Q5), what `CLINICAL_LEADER` and `DIGITAL_REACH` measure (Q6) | Vendor Management | Q4 narrowed: ask for loads after 2025-03 and for `SCIENTIFIC_EXPERT_CHANGELOG` (merges) |
| X5 | Review of dictionary v1 (Q7) | Medical Affairs, brand | Send the `53_` output |
| Q10 | Does NBA 3.0 use any Veeva or KOL attribute? | NBA team | Quick check against the NBA 3.0 feature list |

## 6. Gate G0 checklist

* [x] U1 snapshot written; A1 passes
* [x] U4 config v1 written; A5 passes
* [x] U2 spine written; A2 to A4 pass
* [x] U3 activity tables written; A7 passes
* [x] U6 candidate features run on the spine (as a new notebook, see section 8.2)
* [x] U7 fixed schema; A8 passes
* [x] U8 acceptance table: all checks pass, on both the Spark and Snowflake routes
* [ ] X1 to X5 requests sent (answers not needed)
* [ ] Assessment section 1.5 (1) corrected (section 2.2 here)

## 7. Risks for Phase 0

| Risk | Mitigation |
| --- | --- |
| Connector time-outs on `FOCUS_AREA` (147M US rows) and `PAYMENT` (109M) | Read in chunks; select only needed columns; write each chunk to parquet |
| Snowflake and parquet counts differ because of types (`SE_ID` mixed formats, text dates) | Cast `SE_ID::VARCHAR` and parse dates in the pushdown query; A1 compares both routes |
| Old-load latest rows (about 207K in `CLINICAL_LEADER`) change counts if excluded | Keep them (matches the assessment); count them in the DQ log |
| A refresh lands during Phase 0 | New `load=` folder; re-run 52 to 57; acceptance values for A1 move to the new baseline |

## 8. Results (2026-11-19)

### 8.1 Acceptance run `acceptance/run=20261119T103159` (notebook `57_`)

The Spark route (parquet) and the Snowflake route (aggregation inside Snowflake) give the same value on every check.

| Check | Expected | Spark = Snowflake | Diff | Pass |
| --- | ---: | ---: | ---: | --- |
| A1 snapshot rows = Snowflake | 15 tables | 15 | 0 | yes |
| A2 HCP Universe | 294,727 | 294,727 | 0 | yes |
| A3 matched | 228,932 (77.7%) | 228,930 (77.7%) | -2 | yes |
| A3 distinct `SE_ID` | 228,930 | 228,928 | -2 | yes |
| A4 A to E in Veeva | 65,549 of 78,813 (83.2%) | 65,549 of 78,813 (83.2%) | 0 | yes |
| A4 segment A in Veeva | 91.5% | 91.5% | 0 | yes |
| A5 scored (any) | 147,489 (64.4%) | 147,487 (64.4%) | -2 | yes |
| A5 CL / FA / DR | 134,930 / 29,033 / 4,710 | 134,929 / 29,032 / 4,710 | -1 / -1 / 0 | yes |
| A6 table 7.2, max cell diff | 0 | 1 (Non-target, deciles 3 and 8) | 1 | yes |
| A7 publications | 358,601 | 358,432 | -0.047% | yes |
| A7 trials (PI) | 54,673 (26,006) | 54,666 (26,005) | -0.013% | yes |
| A7 events | 152,510 | 152,468 | -0.028% | yes |
| A7 payment records | 38,305,022 | 38,304,582 | -0.001% | yes |
| A8 fixed schema | 2 runs | 2 runs | 0 | yes |

**Why 2 HCPs are missing:** their NPIs exist in `SCIENTIFIC_EXPERT` only on rows with `IS_LATEST_FLAG = 'N'` (load 20250625, "CG" `SE_ID`s). The assessment did not filter `SCIENTIFIC_EXPERT` on latest; Phase 0 does (P0-D4). The small A7 gaps follow from the same latest filter on the link tables.

### 8.2 Notes by notebook

* **52** (U1, U5): DQ log `dq_log/run=20261119T100328/`. R1 shifted `EVENT_TYPE` = 45 rows (0.007%, not about 0.3%); R3 orphan US `ADDRESS` = 219,567; R4 normalised publication types = 891,954; R7 `CLINICAL_LEADER` latest rows from older loads = 206,914 (kept).
* **53** (U4): `focus_dictionary_v1` 299 rows (17 / 147 / 135, all found in the snapshot); `keyword_list_v1` 86 patterns in 12 tags; stop-list 12 rows (64,847 of 3,829,146 talk titles hit); `windows_v1` 3 and 5 years. Fixed a parser bug that put the cardiorenal block under `ckd`.
* **54** (U2): `spine/veeva_npi_se_map/`, one row per `PROVIDER_ID`. Coverage: `SCORED` 147,487, `IN_VEEVA_UNSCORED` 81,443, `NOT_IN_VEEVA` 65,797 (65,623 NPI not in Veeva, 174 no NPI in crosswalk). 2 `SE_ID`s shared by 4 providers, flagged. No NPI maps to more than one `SE_ID`.
* **55** (U3): `activity/{trials,publications,events,payments}/`. Publication dates run from 2019 to 2025 (2019: 25,097 rows; 2025: 11,652), wider than the 2020 to 2024 in the assessment. 59 trial links and 39 event links have no dimension row.
* **56** (U6, U7), deviation: built as a new notebook `56_veeva_link_features_on_spine`, not a copy of `11_` sections A to K. It produces the section 5.1 candidates for all 294,727 HCPs: `features/t1_t2/anchor=<A>/` (29 T1 + 13 T2) and `features/t3/anchor=<A>/` (16 T3, for E5 and E6 only), schema in `config/feature_schema_v1`. Run for anchors 2025-10-23 and 2024-06-30. The `DIGITAL_REACH` ID problem of the pilot does not occur on string `SE_ID` (4,710 scored), so `DIGITAL_REACH` stays in v1. `PAYMENT.AMOUNT` is text in the snapshot and is cast in `56_`.
* **57** (U8): as in 8.1.

### 8.3 Still open for G0

* X1 to X5 requests and Q10 not sent yet.
* Assessment section 1.5 (1) correction: deferred (user, 2026-11-19); section 2.2 here is the reference until then.
