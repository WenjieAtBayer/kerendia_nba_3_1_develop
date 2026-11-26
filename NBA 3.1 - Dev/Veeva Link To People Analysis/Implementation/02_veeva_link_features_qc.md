# QC 02: Veeva Link features, NBA 3.1

**Status (25 Nov 2026):** PASS with actions. 15 / 15 checks pass on the latest run. Open: 1 access fix (F9) and 2 notes (F2, F14). All other findings are fixed or accepted (section 8).

**Latest run:** job `1033762529783538`, run `2403914065583` (25 Nov 2026, keyword list v4, `veeva_specialty_fallback` dropped).

| Task | Task run | Result | Checks |
| --- | --- | --- | --- |
| Phase 1 (T1 / T2) | `1095326056522913` | SUCCESS | K `run=20261125T142345`: 8 / 8 pass |
| Phase 2 (T3, cross, tests) | `20927110826976` | FAILED at 2.A only (F9); 2.1 to 2.4 wrote their outputs | L `run=20261125T143039` 6 / 6 and `_cross` 4 / 4 pass; segment test `run=20261125T143520` S1 to S4 pass |
| Phase 3 (business outputs) | `479773548077857` | SUCCESS | |
| Phase 4 (operations) | `132736229171268` | SUCCESS | feature dictionary `run=20261125T144209`: N10 to N12 pass (82 rows) |
| QC fill rate | | | `<OUT>qc/fill_rate/run=20261125T144622/` (5,376 rows) |

`<OUT>` = `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/veeva_link_to_people/`. `<SF>` = Snowflake `CPH_DB_PROD.ANALYTICS_V2.ANLT_VEEVA_LINK_*`.

The HCP trace, the independent recompute, the cross-feature recompute and the keyword samples were last run on the previous run `250832260996735` (same code and keyword list v4; the only later change is dropping one all-null column). The latest fill rate equals that run's fill rate on every remaining column (0.00 pt difference), and K5 (c12 vs the stand-alone build) passes again.

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebooks | `Implementation/10_phase0_data_foundation`, `20_phase1_t1_t2_features`, `30_phase2_t3_features_and_tests`; `40_` and `50_` for the M / N checks |
| Rule files | `50_veeva_link_nba_3_1_readiness_plan.md` (sections 4, 5.1, 8.1); phase plans in `01_veeva_link_plans.md` |
| Inputs | `<SF>` 15 in-use tables frozen to `<OUT>snapshot/load=2025-06-30/`; `config/focus_dictionary_v1` (299 names); `config/keyword_list_v4` (209 patterns: 166 include, 43 exclude); HCP Universe; NPI crosswalk; MDM affiliation and hierarchy |
| Outputs | `<OUT>features_phase1/t1_t2/`; `<OUT>features_phase2/t3/` and `cross/` (versions `snapshot`, `asof`); schema locks in each `schema_lock/` |
| Universe | `kerendia_nba_3_1_volume/HCP_Universe_without_call_hcps`: 294,727 providers -> 294,542 NPIs |
| Cohorts | 28 claims cohorts c1 to c28 (`cohorts/claims/cohorts.parquet`; Training c1 to c24, Testing c25 to c26, Holdout c27 to c28). Anchor = `lookback_end_date` (c1 2024-05-01 to c28 2026-08-01). Reference cohort c12 (first anchor past the 2025-03-06 data cut-off); list date c28 |
| Grain | One row per `NPI_NUMBER` x `COHORT_ID` (T3 / cross also x `version`) |
| Features | 74: T1 38, T2 13 (incl. `veeva_coverage_status`), T3 18, cross 5. Locks: T1 / T2 58 columns, T3 23, cross 8; 82 distinct columns incl. 8 keys / metadata |
| NBA 3.0 | 752-feature final model (`Final NBA 3.0 Modeling Features.xlsx`); no Veeva block |

## 2. Checklist and evidence

Results are from the latest run unless the row says "previous run" (`250832260996735`, same code and keyword list).

| # | What we checked | What we found | Status |
| --- | --- | --- | --- |
| Q1 | Is every HCP in the output exactly once, and nobody from outside the HCP Universe? | Yes. Every cohort has the same 294,542 HCPs (NPIs), one row each, 8,247,176 rows in total. 185 of the 294,727 universe providers have no row of their own: 174 have no NPI in the mapping table and 11 share an NPI with another provider | PASS (F8) |
| Q2 | Do we find the same share of HCPs in Veeva as the original assessment? | Yes. 228,928 HCPs (77.7%) are in Veeva, the same as the readiness plan; 83.2% in call-plan segments A to E. 65,614 HCPs are not in Veeva. Each HCP stays in the same group (scored / in Veeva but unscored / not in Veeva) in every cohort | PASS |
| Q3 | Does any feature use data from after the cohort's anchor date (look-ahead)? | No. Every activity window ends on the anchor date or on the Veeva data cut-off 2025-03-06, whichever is earlier, and no activity after the window end is counted. Trials and publications look back 5 years, events and payments 3 years. Payments use only CMS years already published at the anchor (2020 to 2022 for c1 and c2, 2021 to 2023 from c3). The `asof` vendor scores never use a load newer than the anchor | PASS |
| Q4 | Is the source data complete and filtered as planned? | Yes. All 15 Veeva tables in our frozen copy have the same row counts as Snowflake, with the planned filters (latest rows, not deleted, US only on person tables). The 2 out-of-scope tables are never read (checked 24 Nov; does not depend on cohorts) | PASS |
| Q5 | Do the keyword lists tag the right titles, and do they miss many? | Mostly right: 98% of the titles newly tagged by keyword list v4 are correct (145 of 148 checked); 99% for the earlier v3 list. A sample of untagged titles found 35 that should have been tagged, mostly SGLT2 spelling variants (F14). Previous run | PASS (F13, F14) |
| Q6 | Are all planned columns there, and only those? | Yes. The T1 / T2 table has exactly the 58 columns of the new fixed column list (the dropped specialty column is gone), with 51 features (38 T1, 13 T2). The feature dictionary describes all 82 columns once each | PASS |
| Q7 | Do the business rules match the readiness plan? | Yes. All 16 rules match; 3 small additions are documented in section 3 | PASS |
| Q8 | How full is each feature? | Empty values occur only for HCPs not in Veeva, as intended. No feature is fully empty or constant; 8 features are very sparse (section 4) | PASS (F4) |
| Q9 | Did NBA 3.0 already have Veeva-type features we must keep? | No. Only 1 of the 752 NBA 3.0 features matched (Bayer speaker programmes), and it belongs to the personal promotion block | PASS |
| Q10 | Which features are new, kept or replaced vs NBA 3.0? | All 74 Veeva features are new; no NBA 3.0 feature is lost (section 5) | PASS |
| Q11 | Do values recomputed by hand for real HCPs match the output? | Yes. 72 of 72 traced values for 6 HCPs match, and an independent recompute of the in-scope counts matches 136 of 136 values (section 6). Previous run | PASS |
| Q12 | Do the values follow basic logic? | Yes. Flags are only 0 or 1, a sub-count never exceeds its total, deciles are 1 to 10, shares are between 0 and 1, no disease or focus-area decile is higher than the HCP's best decile, and the best decile equals the one in the HCP match table (all 28 cohorts on the previous run; vendor scores at c28 re-checked on the latest run) | PASS |
| Q13 | How different are the two vendor-score versions (`asof` vs `snapshot`)? | The best decile differs for 64% of in-Veeva HCPs in c1 to c3 (no `asof` scores exist yet), 3.8% in c4 falling to 0.8% in c11, and 0.66% from c12 on. The 0.66% is caused by stale rows from older loads (F10). The segment test now uses the look-ahead-free `asof` version (F7) | PASS |
| Q14 | Do repeated builds give the same answer? | Yes. Cohort c12 matches the earlier stand-alone build exactly (0 differences in 40 columns for all 294,542 HCPs), and T1 values do not change from c12 to c28 | PASS |
| Q15 | Is anything sensitive or out of date in what reps see or in the docs? | No payment columns and no "KOL" wording in the business lists. The `20_` read-me, feature dictionary and 1.1 intro now say 51 features, cohorts c1 to c28 and keyword list v4; 2 old cells still need deleting (section 8) | PASS |

## 3. Business rules (readiness vs notebook)

| # | Rule | Notebook | Match |
| --- | --- | --- | --- |
| R1 | Universe is the spine; `PROVIDER_ID` -> crosswalk NPI -> `SCIENTIFIC_EXPERT.NPI`; Veeva never filters | 0.3 left joins; lowest `SE_ID` per NPI | Yes |
| R2 | Latest, not deleted, US tenant on person tables only | 0.1 filters | Yes |
| R3 | Missing is not zero | Not in Veeva -> null; in Veeva without activity -> 0 (K4: 0 non-null values for NOT_IN_VEEVA) | Yes |
| R4 | Leakage tiers T1 / T2 / T3 | T1 windowed per cohort; T2 static; T3 as `snapshot` and `asof` | Yes |
| R5 | Windows end at min(anchor, data cut-off); 3 and 5 years | `windows_for`; payment years with the 30 June publication rule | Yes (payment rule added) |
| R6 | One focus dictionary | `focus_dictionary_v1`, 299 names, 14 themes | Yes |
| R7 | One keyword list with `LIKE`, never `REGEXP_LIKE` | `keyword_list_v4`, Spark `LIKE`, include minus exclude | Yes |
| R8 | Kerendia total + HF / T1D / CKD views | in-scope totals + `_hf`, `_ckd`, `_t1d` counts | Yes |
| R9 | Flags, log counts, bins; 60 to 80 columns | 74 features | Yes |
| R10 | Bayer payments only as a separate flag | Every payment feature except `veeva_pay_bayer_flag_3y` uses non-Bayer rows (F6) | Yes |
| R11 | Composites standardised on the full universe | `zmean` over all NPIs of the cohort; not in Veeva = 0 for the statistics, output null (F5) | Yes |
| R12 | Deciles from CL, FA, DR; never `COMMUNITY_LEADER_FOCUS_AREA` | 0.3 / 2.2; 0 code references | Yes |
| R13 | IDN expert share, zero flag, practice peer flag | 2.2 R5, own `cross` table + 2 peer counts | Yes (separate table) |
| R14 | `veeva_` prefix; fixed columns | all features prefixed; locks 58 / 23 / 8 | Yes |
| R15 | Out of scope tables; specialty only as fallback | none read; fallback column dropped (F3) | Yes |
| R16 | "Influence / authority", not "KOL" | M6 | Yes |

Sources (24 Nov, unchanged): `SCIENTIFIC_EXPERT` 2,215,203 rows (hub 2025-06-30); scores `CLINICAL_LEADER` 91,048,138, `FOCUS_AREA` 147,166,660, `DIGITAL_REACH_FOCUS_AREA` 22,927,230, `INDEX` 3,171,071 (2025-03-06); activity tables cut-off 2025-03-06. MDM (re-checked 25 Nov): affiliation 4,374,496 rows, 1,368,947 at `BRAND_RANK = 1`; hierarchy 563,269 rows. At c28: practice for 282,838 NPIs (96.03%), IDN for 210,399 (71.43%).

## 4. Fill rate (c28, latest run)

NPIs: 294,542 total, 228,928 in Veeva. For every T1 / T2 feature the base null rate is 22.28% = NOT_IN_VEEVA, as the missing rule requires. In Veeva, only `veeva_pub_months_since_last` has nulls (HCPs who never published). No feature is all-null or constant.

| Family | Features | Median % non-zero (all / in Veeva) | Max move c1 to c28, in Veeva (pt) | Move c12 to c28 | Features < 0.5% non-zero in Veeva |
| --- | --- | --- | --- | --- | --- |
| Trials | 13 | 0.86 / 1.11 | 0.32 | 0 | finerenone flag 0.05, MRA flag 0.07, T1D count 0.12, SGLT2 flag 0.36 |
| Publications | 8 | 5.24 / 6.75 | 1.48 (`months_since_last`) | 0 | T1D count 0.26 |
| Events | 7 | 2.09 / 2.69 | 0.52 | 0 | T1D count 0.08 |
| Payments | 8 | 29.47 / 37.92 | 3.78 (`bayer_flag`) | 0 | - |
| Composites | 2 | 77.72 / 100 | 0 | 0 | - |
| Coverage (numeric) | 3 | 50.07 / 64.43 | 0 | 0 | - |
| Profile | 9 | 3.74 / 4.82 | 0 | 0 | emerging expert 0.45, kidney society 0.29 |
| T3 (snapshot) | 18 | 11.58 / 14.90 | 0, except `score_age_months` (0 to 16 by design) | same | - |
| Cross (snapshot) | 5 | 56.60 / 58.48 | 0 | 0 | - |

Best decile non-null at c28: 50.07% (`snapshot`), 49.65% (`asof`). Full table per feature x cohort x scope x version: appendix A.

## 5. NBA 3.0 vs NBA 3.1

The 752 NBA 3.0 features contain no Veeva Link feature. The one name hit, `TOTAL_SPEAKER_PROGRAMS_ATTENDED_IN_LAST_3_MONTH` (rank 747, 0.013% SHAP), is a Bayer speaker-programme feature and stays in the personal promotion block. All 74 Veeva features in 3.1 are new; none are preserved or dropped.

## 6. HCP trace (run `250832260996735`)

Recomputed from the frozen snapshot with QC code written separately from the notebooks (own windows, own `LIKE` tagging, payment years with the 30 June rule, `coalesce(FOOD_FLAG, 0)`, non-Bayer rows, log1p).

| Case | NPI | Tests | c28 values (`trial_log_n`, `pub_log_n`, `pay_log_total`, `pay_excl_food_log`, companies, Bayer flag) |
| --- | --- | --- | --- |
| 1 | 1003123415 | Scored expert, all activity; also c1 and c11 | 2.0794, 3.6376, 11.8689, 11.8684, 4, 0 |
| 2 | 1003088485 | In Veeva, unscored | 0, 0.6931, 6.8400, 4.6052, 5, 0 |
| 3 | 1003012451 | Not in Veeva | all null |
| 4 | 1003836602 | Window edge, Bayer payments | 2.8332, 3.6889, 14.3142, 14.2975, 29, 1 |
| 5 | 1154342277 | MRA exclusion (PAH title not tagged) | 1.0986, 4.8828, 0, 0, 0, 0 |
| 6 | 1790303782 | One NPI on 2 providers, shared `SE_ID` | 0, 0, 0, 0, 0, 0 |

Result: 72 / 72 traced values match; composite for case 1 = 2.330818 = output. Independent recompute of the 17 in-scope columns at 8 HCP-cohort points: 136 / 136. T3 and cross for all NPIs: 0 mismatches (cross at c5, c12, c28, both versions).

## 7. Feature inventory

| Step | Output | Family | Tier | Features |
| --- | --- | --- | --- | --- |
| 1.1 | `features_phase1/t1_t2` | trials / publications / events / payments / composites | T1 | 13 / 8 / 7 / 8 / 2 |
| 1.1 | | coverage (incl. status) / profile | T2 | 4 / 9 |
| 2.2 | `features_phase2/t3` | scores 13, index 5 | T3 | 18 |
| 2.2 | `features_phase2/cross` | cross | cross | 5 |
| all | keys / metadata | `NPI_NUMBER`, `PROVIDER_ID`, `COHORT_ID`, `t3_version`, `cohort_set`, `veeva_window_end`, `veeva_data_age_months`, `veeva_snapshot_id` | key | 8 |

Every readiness 5.1 candidate is built. 74 features is within the 60 to 80 target.

## 8. Findings

| # | Finding | Action | Status |
| --- | --- | --- | --- |
| F1 | `pay_excl_food_log` dropped payments with null `FOOD_FLAG` | `coalesce(FOOD_FLAG, 0)` | FIXED |
| F2 | T1 / T2 identical for c12 to c28 (incl. all Testing and Holdout cohorts); only c1 to c11 vary. **Reason:** every window ends at the Veeva data cut-off 2025-03-06 from c12 on, and no Veeva data after March 2025 is loaded; CMS payment years stop at 2023 | Veeva acts as a static HCP attribute in NBA 3.1; a fresh Veeva load is needed for time-valid features | OPEN (note) |
| F3 | `veeva_specialty_fallback` 100% null (input I3 not delivered) | Column dropped from `20_` (spec, builder, checks, docs); schema lock reset (old lock kept as `schema_lock/columns_before_F3_20261125.json`); K2 wrote a new 58-column lock | FIXED (dropped) |
| F4 | 8 features < 0.5% non-zero in Veeva (section 4) | Keep; feature selection decides | ACCEPTED |
| F5 | Composites standardised on in-Veeva NPIs, not the full universe | Standardise over the full universe | FIXED |
| F6 | Bayer amounts inside the payment totals | Bayer rows only in the Bayer flag | FIXED |
| F7 | `snapshot` T3 for c1 to c11 uses the 2025-03-06 load (up to about 10 months of look-ahead) | 2.4 segment test uses `asof` as the main version (`30_` cells 2.4); `snapshot` kept as today's view for business lists | FIXED |
| F8 | 185 universe providers have no own row (174 without NPI, 11 sharing an NPI) | Join the Veeva block on `NPI_NUMBER`; the 174 get null + NOT_IN_VEEVA | ACCEPTED (documented) |
| F9 | Step 2.A fails: no `USE CATALOG` on `cph_db_prod` (failed again in run `2403914065583`) | Request access, or read the 4 tables from the frozen snapshot; no feature depends on 2.A | OPEN (access) |
| F10 | `asof` and `snapshot` best decile differ for 0.66% of in-Veeva NPIs from c12 on, though both use the 2025-03-06 load. **Reason:** 1,508 of 228,928 HCPs differ, all because of stale `IS_LATEST_FLAG = 'Y'` rows from older loads (53,226 rows, 9,487 experts, mostly the DR load of 2024-12-26). The snapshot keeps them; `asof` takes only the 2025-03-06 load. 1,260 HCPs have only stale rows (`asof` null), 248 have a snapshot decile raised by a stale row | Documented; `asof` is the clean version for modelling | EXPLAINED |
| F11 | Over-broad keyword patterns (v2 precision 91.7%) | `keyword_list_v3` (99.0%) | FIXED |
| F12 | Keyword recall gaps (RAAS, SGLT2, GLP-1, ERA, finerenone spellings) | `keyword_list_v4`, 209 patterns; new tags 98.0% precise | FIXED |
| F13 | `%glp-1%` / `%incretin%` also tag GLP-1 physiology titles (2 false in 148) | Titles are on-topic biology | ACCEPTED (documented) |
| F14 | v4 recall sample: 35 real misses in 343 untagged titles, 18 of them SGLT2 spellings (e.g. "sodium/glucose cotransporter 2", "SGLTi"), GLP-1 4, T1D 4, CKD 2, HF 2, 1 each MRA / RAAS / landmark / cardiorenal / finerenone | Optional `keyword_list_v5` if feature selection keeps these counts | OPEN (note) |

Doc note: `20_phase1_t1_t2_features` still contains the old read-me and feature dictionary cells (52 features, 43 cohorts, keyword list v2) at positions 3 and 4, below the updated ones. They have no stable cell id and must be deleted by hand.

Not covered: raw Snowflake rows per traced HCP (table-level counts match); the trace and recompute were not repeated on run `2403914065583` (only change: one all-null column dropped; fill rate identical on all other columns).

## 9. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 15 / 15, run `2403914065583` |
| QC by / date | Genie Code for Sehar Aejaz, 24 to 25 Nov 2026 |
| Reviewed by / date | |
| Next | F9 access; delete the 2 stale cells in `20_`; optional keyword list v5 (F14) |

## Appendix A. Fill rate per feature

`<OUT>qc/fill_rate/run=20261125T144622/`: 5,376 rows = (50 T1 / T2 + 18 T3 x 2 versions + 5 cross x 2 versions) x 28 cohorts x (all / in Veeva), with n, null, zero, non-zero counts and %. `veeva_coverage_status` is not in the table (string key, never null). Superseded: `run=20261125T133917` (before F3, 5,432 rows) and earlier runs.
