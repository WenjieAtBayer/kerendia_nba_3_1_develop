# QC 01: F2F (core field interaction) features, NBA 3.1

**QC status:** DONE, 20 Nov 2026 (channel 1 of 6)  
**Verdict:** PASS with actions. The feature values are correct (Q9: 90 of 90 recomputed values match). 3 documentation fixes and 3 modelling decisions are open (section 8).  
**QC run:** 20 Nov 2026, serverless, on the outputs of the last notebook run. The notebook was not re-run.

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `personal_promotional_features/F2F/f2f_feature` (28 cells) |
| Client summary | `F2F/f2f_feature_nba_3_1_client_summary.md` |
| Readiness file | `personal_promotional_features/40_field_activity_nba_3_1_readiness_plan.md`: Phase 0 V1, V2, V3, V9 and Phase 1 C1 to C8 |
| Output | `kerendia_nba_3_1_volume/notebook_output/field_activity_nba_3_1/kerendia_nba_3_1_hcp_model_field_core_features.parquet` |
| Final output (core + C9) | `.../field_activity_nba_3_1/kerendia_nba_3_1_hcp_model_field_core_account_features.parquet`: 53 core + 4 C9 direct account call features = 57 (cells 21 to 25). C9-only file: `..._field_account_call_features.parquet` |
| Intermediates | Only `field_interaction_detail.parquet` is written. `field_interaction` and `field_org_link` are kept in memory and not saved, although the readiness plan lists them as intermediate tables |
| Universe | `kerendia_nba_3_1_volume/HCP_Universe_without_call_hcps/` (294,727 PROVIDER_IDs, 294,726 without placeholder `0`) |
| Cohorts | `kerendia_nba_3_1_volume/cohorts/promotional/cohorts.parquet` (c1 to c28: c1 to c24 train, c25 and c26 test, c27 and c28 back-test) |
| Expected shape | 53 core features (57 with C9) + 6 key columns, rows = universe x 28 |
| NBA 3.0 counterpart | `25_promotional_features_call` (27 features, 3M) and `13_promotional_features_bho_calls` (90 features, 15 x 1 to 6M) |
| NBA 3.0 final model | LightGBM, MLflow run `f583bcbc9d56477fae983d44c16f8c70`, 752 features, `Shap_Importances.csv` |

## 2. QC checklist

Status values: `PASS` / `FAIL` / `OPEN` (not yet run) / `N/A`. Record evidence (number, cell, query) in section 3.

| # | Check | How | Pass when | Status |
| --- | --- | --- | --- | --- |
| Q1 | HCP universe | Distinct PROVIDER_ID in output vs universe file; rows = HCPs x 28; duplicate (PROVIDER_ID, COHORT_ID) keys; HCPs in output but not in universe; placeholder `0` handling; BHID to PROVIDER_ID mapping coverage and HCPs on more than one BHID | Same HCP set as universe (minus `0` if excluded on purpose), 0 duplicates, 0 extra HCPs, mapping loss documented | PASS (2 notes) |
| Q2 | Cohorts and windows | 28 cohort IDs present; `LOOKBACK_END_DATE` per cohort equals cohorts.parquet; 1, 3, 6, 12M = 30, 91, 182, 365 days ending at lookback end; `DATA_START` (2022-01-01) covers c1 lookback minus 12M | All match, no event after lookback end (no leakage) | PASS |
| Q3 | All features made | Output columns vs `expected_feature_columns()` in the config cell vs readiness C1 to C8 list; data types | 53 features, no missing / extra column, numeric types | PASS |
| Q4 | Business rules: readiness vs notebook | Fill the rule table in section 4, one row per rule, citing the notebook cell | Every rule matches, or the difference is documented and agreed | PASS (C9 not in readiness) |
| Q5 | Data sources vs readiness | Tables, joins and filters used in the notebook vs readiness section 5 (`FACT_CALL`, `MAP_CUSTOMER_XREF`, `FACT_CALL_KEY_MESSAGE`, `FACT_CALL_DETAIL`) | Same tables; any extra or missing source explained | PASS (1 extra source, C9) |
| Q6 | Fill rate | Per feature: % null, % zero, % non-zero, min / max; all cohorts, per split (train / test / back-test) and latest cohort (c28) | No unexpected nulls; flags raised for > 99.5% zero, constant, or sudden change between cohorts; sentinels (999, 365) reported separately | PASS (3 flags) |
| Q7 | NBA 3.0 model coverage | List every call / BHO feature from the 752 with its SHAP rank; map each to a 3.1 feature or a drop reason | No 3.0 model feature dropped without a written reason | PASS |
| Q8 | Preserved vs new | Fill section 5 | Every 3.1 feature is labelled preserved, replaced or new | PASS |
| Q9 | HCP trace (step by step) | Section 6, at least 5 HCPs, recomputed from Snowflake | Final value equals output for every HCP and feature traced | PASS (90 / 90) |
| Q10 | Invariants | 1M <= 3M <= 6M <= 12M; F2F + GROUP + REMOTE <= TOTAL; KER_ONLY + KER_CODETAIL = Kerendia interactions; shares in [0, 1]; `FLD_DAYS_SINCE_LAST_INT` = 999 when 0 interactions in 12M (past bug: filled with 0) | 0 violations | PASS |
| Q11 | Reconciliation | Year 2 (Nov 2025 to Oct 2026) Kerendia doctor records vs Phase 0 target | HCP_INTERACTION about 606K, ACCOUNT_OFFICE about 70K, total about 676K calls / 105K doctors (within 1%) | PASS |
| Q12 | NBA 3.0 output comparison | F2F 6M totals by normalised cohort (c1 to C01) vs NBA 3.0 output | Differences explained (cohort dates differ, stricter classification, co-detail gap fixed) | PASS |
| Q13 | Reproducibility and docs | Re-run gives the same schema and row count; notebook header and client summary match the current run | Same columns twice; no stale text | FAIL (stale docs; re-run not done) |

## 3. Evidence log

| # | Result (numbers) | Where (cell / query) | Notes |
| --- | --- | --- | --- |
| Q1 | Universe: 294,727 rows / 294,727 distinct, 0 null or blank, 1 placeholder `0`. Output: 8,252,328 rows = 294,726 HCPs x 28 cohorts; every HCP has 28 cohorts, every cohort has 294,726 rows. 0 duplicate (PROVIDER_ID, COHORT), 0 duplicate `HCP_COHORT_ID`, `HCP_COHORT_ID` = `PROVIDER_ID_COHORT` on all rows. 0 HCPs in output not in universe; only `0` is in universe but not in output. Mapping: 294,577 HCPs have a BHID, 149 have none (none has any activity in any cohort, so they get 0 / defaults). 0 HCPs map to more than 1 BHID. 38 BHIDs map to 2 universe HCPs each (76 HCPs, 42 active in 12M at c28), so their calls count for both HCPs. Reference: 85,247 HCPs have `FLD_INT_TOTAL_12M` > 0 at c28 | QC session 20 Nov 2026 (serverless): output parquet, universe, `SOURCE_PROVIDER_BHID_NPI_MAPPING`; notebook cell 5 | `0` dropped on purpose in cell 5 (`universe.filter(PROVIDER_ID != "0")`). Shared BHIDs: 76 of 294,726 HCPs (0.03%), accepted as known limitation unless modelling objects |
| Q2 | Partial: the 28 output cohorts match cohorts.parquet on cohort ID, `DATASET` (24 Training / 2 Testing / 2 Holdout), `PREDICTION_MONTH` and `SVC_DT` = `lookback_end_date` (c1 2024-06-17 to c28 2026-09-17): 0 mismatches. Windows: config 1 / 3 / 6 / 12M = 30 / 91 / 182 / 365 days, with an event in window if days before END < N (cell 10). The window edge is confirmed by trace HCP 2: last call 30 days before END, so it is counted in 3M and not in 1M. Leakage: cell 10 checks that every event is in (END - 365, END] (assert); the independent recompute (Q9) used only calls on or before END and matched. `DATA_START` 2022-01-01 is before the c1 window start (2023-06-18) | Cell 4, cell 10; Q9 | Cell 4 comment `first cohort lookback starts 2022-03-17` is out of date (old cohorts) |
| Q3 | Output feature columns = `expected_feature_columns()`, same order: 53 = C1 16, C2 6, C3 12, C4 4, C5 4, C6 5, C7 4, C8 2 (matches readiness Phase 1 status). Combined file adds 4 C9 columns (57). All long / int / double. 0 nulls in all 57 | Cell 4 config run in QC session; output schema | |
| Q4 | All readiness rules found in code (section 4). One addition not in readiness: C9 direct account calls (rule from the client team; Kerendia-only scope chosen by the user on 11 Nov 2026) | Cells 6, 7, 9 to 13, 21 to 23 | Add C9 to readiness |
| Q5 | Core: `FACT_CALL`, `MAP_CUSTOMER_XREF`, `FACT_CALL_KEY_MESSAGE`, `FACT_CALL_DETAIL` (Snowflake `CPH_DB_PROD.MODEL_V2`) + `SOURCE_PROVIDER_BHID_NPI_MAPPING`, as in readiness section 5. Filters: `UPPER(STAT) = 'SUBMITTED_VOD'`, `CALL_DATE >= 2022-01-01`, `BAYER_CUST_ID` not null. Extra for C9: `pace_ker_in_house_schema.cust_mdm_best_affl_publish_pd_outp_static` (Kerendia, `BRAND_RANK = 1`, single snapshot) | Cells 6, 22 | |
| Q6 | 0% null for all 57 features. Non-default share per feature in appendix A. Flags: (1) C9 `FLD_ACCT_DIRECT_CALL_*` and `FLD_DAYS_SINCE_ACCT_DIRECT_CALL`: 0.00% train and test, 0.03% holdout, so effectively constant; (2) very sparse (> 99.5% zero): `FLD_INT_REMOTE_1M/3M/6M/12M` (0.05 to 0.39%), `FLD_INT_GROUP_1M/3M` (0.21 / 0.41%); (3) drift: co-detail 12M is 1.69% in train vs 11.78% test / 13.82% holdout, and `FLD_CODETAIL_PERIOD_FLAG` is 20.8% in train and 100% in test / holdout (expected: co-detail starts Jan 2026). Outliers: `FLD_ORG_COLLEAGUE_INT_6M` max 818, `FLD_ORG_N_COLLEAGUES_CALLED_6M` max 212 (large organisations) | QC session, combined output | |
| Q7 | 21 of the 752 NBA 3.0 model features come from the call / BHO blocks (18 from `25_` call output, 3 from `13_` BHO output), 8.867% of total mean abs SHAP. All 21 are mapped in section 5: 9 replaced, 12 dropped with a reason, 0 skipped silently | MLflow run `f583bcbc...` `Shap_Importances.csv` (752 rows) vs NBA 3.0 output columns (dev_folder and ops_pipeline) | Name match on exact column names |
| Q8 | See section 5 | | |
| Q9 | 6 HCPs (5 at c28, 1 at c10), 15 features each = 90 values recomputed in pandas from raw Snowflake rows: 90 match, 0 mismatch (section 6) | QC session; raw `FACT_CALL` / `FACT_CALL_DETAIL` / `FACT_CALL_KEY_MESSAGE` | HCPs on shared BHIDs or with no BHID left out of the sample |
| Q10 | 56 invariant checks on all 8,252,328 rows, 0 violations: nested windows (TOTAL, F2F, GROUP, REMOTE, MEAL, KER_*, ACCT_OFFICE, C9, org, reps, active months); F2F + GROUP + REMOTE <= TOTAL; KER_ONLY + KER_CODETAIL = TOTAL; KER_PRIMARY <= TOTAL; 6 shares in [0, 1]; recency 999 exactly when 12M count = 0 (core, account / office, C9); recency in [0, 364] or 999; median gap 365 when < 2 dates; reps > 0 exactly when TOTAL_12M > 0; co-detail flag = END >= 2026-01-01; no negative counts except the trend difference; org flag 0 implies org counts 0 | QC session | Also run in notebook cell 14 |
| Q11 | Recomputed in Snowflake today, Year 2 (Nov 2025 to Oct 2026), Kerendia detail, submitted: HCP_INTERACTION 609,332 calls / 97,045 doctors; ACCOUNT_OFFICE 70,238 / 27,385; doctor total 679,570 / 105,206. Last notebook run: 606,357 / 69,906 / 676,263 calls, 104,867 doctors (+0.5% calls, +0.3% doctors, most likely late-arriving Snowflake data). Phase 0 target 676,136 / 104,752 | QC session, direct Snowflake SQL | Within 1% |
| Q12 | NBA 3.1 F2F 6M total / NBA 3.0 `TOTAL_F2F_IN_LAST_6_MONTH` by cohort: 60.8% (c8) to 99.5% (c24) in training, 104.7% c25, 119.0% c26; HCPs with F2F 6M > 0: 48,915 vs 62,997 at c1, 66,036 vs 56,416 at c26. Lower in early cohorts (stricter `HCP_INTERACTION` class, no BHO copies, different cohort dates), higher from c25 (likely the co-detail calls that NBA 3.0 misses, readiness section 3) | QC session; NBA 3.0 `dev_folder/.../kerendia_nba_3_hcp_model_call_features.parquet` | Approximate: cohort dates differ (c1 vs C01) |
| Q13 | Not re-run (it would overwrite the outputs); schema is fixed by config asserts (cells 13, 23, 25). Stale docs: notebook cell 1 says cohorts end at C26; cell 4 comment says lookback starts 2022-03-17; readiness says `26 cohorts` and has no C9; client summary has no C9 | QC session | Fix docs, then re-run once to confirm |

## 4. Business rules to verify (readiness vs notebook)

| Rule | Readiness file says | Notebook does (cell) | Match |
| --- | --- | --- | --- |
| Grain | One HCP interaction = one submitted call on a doctor; products are details below it | Cell 6: `STAT = SUBMITTED_VOD`; cell 7: `dropDuplicates(CALL_ID, BHID)`; details aggregated per call | Yes |
| Kerendia interaction | Any detail row in `FACT_CALL_DETAIL` is Kerendia (`SOURCE_PROD_NM` = `Kerendia`); no text match on `DETL_PROD` | Cell 7: `HAS_KERENDIA_DETAIL` from `PRODUCT == 'Kerendia'` | Yes |
| One class per record | `HCP_INTERACTION`, `ACCOUNT_OFFICE`, `BHO_CHILD`, `BHO_TOP_LEVEL`, `MEDICAL`; only `HCP_INTERACTION` feeds C1 to C5 and C8 | Cell 7: one `when` chain, in order BHO child, BHO top level, medical, account / office, else HCP; cell 10: core events = `HCP_INTERACTION` + Kerendia | Yes |
| Account / office | From `FACT_CALL_KEY_MESSAGE.KEY_MSG_NM` (`5- Acct Call`, `2-Account Call Only`, `vOffice call (no HCP)`, `Account Call`, `Office call (no HCP)`) | Cell 4 list, same 5 values; cell 6 join | Yes |
| Record type mapping | Old names (`BPH_Face2Face_SIG`, ...) until mid-2025 and new names (`Face2Face Signed`, ...) after, both mapped; rest = OTHER (TOTAL only) | Cell 4 `RECORD_TYPE_GROUP` (4 old names + 5 new names, the new ones including `Face2Face KAM Call`); unmapped = OTHER | Yes |
| Doctor child records | Doctor records with `PAR_CALL_ID` stay `HCP_INTERACTION` | Cell 7: `PAR_CALL_ID` only used for BHO records | Yes |
| Medical | Finerenone / medical record types excluded from HCP counts | Cell 4 regex: record type `interaction[ _]med`, `^bph_med_`, `^event call report`; `DETL_PROD` contains `finerenone`. Note: the cell 16 Snowflake check uses `Finerenone%` (starts with), slightly different | Yes |
| Organisation link (C7) | BHO child of the doctor call, or doctor attendee of a BHO group call; no sibling link; focal HCP excluded; BHO top-level out until V3 | Cell 9 paths A and C only; cell 12 primary org, colleague counts = org total - own | Yes |
| Co-detail | Kerendia + another brand on the same interaction; `FLD_CODETAIL_PERIOD_FLAG` from 2026-01-01 | Cell 7: other product = not Kerendia and not a `[...]` medical product; cell 13 flag = END >= 2026-01-01 | Yes |
| Dropped | Call length, phone, `Group Detail`, rare purpose / type features | None of these in the schema | Yes |
| Defaults | Counts 0, recency 999, median gap 365 when fewer than 2 dates | Cell 4 `FILL_DEFAULTS` (also trend ratio 1.0, shares 0) | Yes |
| Not in readiness | (none) | C9 direct account calls credited to HCPs with Kerendia primary affiliation; Kerendia detail only (cell 21 says about 11 such calls since 2022) | Addition |

## 5. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature | In 752? (SHAP rank) | NBA 3.1 feature | Status (preserved / replaced / dropped / new) | Reason |
| --- | --- | --- | --- | --- |
| `TOTAL_F2F_IN_LAST_1/2/3/4/5/6_MONTH` (6) | Yes: ranks 29, 17, 8, 9, 6, 1 (8.350% SHAP) | `FLD_INT_F2F_1M/3M/6M/12M` (+ `FLD_INT_TOTAL_*`) | Replaced | Same concept on the new interaction grain (all Kerendia calls, one count per call). Windows are now 1 / 3 / 6 / 12M, so the 2, 4 and 5M versions have no exact equivalent |
| `BHO_TOTAL_F2F_IN_LAST_1/2/3_MONTH` (3) | Yes: ranks 504, 278, 111 (0.345%) | `FLD_ORG_COLLEAGUE_INT_3M/6M`, `FLD_ORG_N_COLLEAGUES_CALLED_6M`, `FLD_ORG_LINKED_FLAG` | Replaced | NBA 3.0 gave each BHO copy to every doctor of the organisation (readiness section 3); C7 counts colleague interactions with the focal HCP excluded |
| `TOTAL_F2F_AND_GROUP_DETAIL_IN_LAST_5/6_MONTH`, `..._GROUP_DETAIL_WITH_SAMPLE_IN_LAST_6_MONTH` (3) | Yes: ranks 663, 231, 749 (0.131%) | None (F2F volume in `FLD_INT_F2F_*`) | Dropped | `Group Detail` call type not used by Field Analytics (F-4, PF-4) |
| `TOTAL_F2F_AND_DETAIL_ONLY_IN_LAST_2/5/6_MONTH` (3) | Yes: ranks 734, 669, 719 (0.023%) | None (F2F volume in `FLD_INT_F2F_*`) | Dropped | Call-type split dropped (PF-4) |
| `TOTAL_F2F_AND_DETAIL_WITH_SAMPLE_IN_LAST_2/3/4_MONTH` (3) | Yes: ranks 742, 741, 725 (0.008%) | Samples block (QC 05) | Dropped here | Samples built once from `FACT_CALL_SAMPLE` (S3); check in QC 05 |
| `TOTAL_CALL_DURATION_IN_LAST_3/5/6_MONTH` (3) | Yes: ranks 735, 739, 718 (0.010%) | None | Dropped | Duration is `30` on 97% of calls since 28 Jul 2025 (PF-3) |

Summary: of the 21 NBA 3.0 call / BHO features in the 752 (8.867% of SHAP), 9 are replaced (8.695% of SHAP) and 12 are dropped with a reason (0.172%); none is skipped silently. The other 192 NBA 3.0 call columns and 87 BHO columns were not in the 752. New in 3.1 (no 3.0 model equivalent): GROUP / REMOTE / TOTAL splits and 12M windows (C1), meal (C2), Kerendia only / co-detail / primary (C3), recency and regularity (C4), rep coverage (C5), account / office (C6), trend (C8) and C9 direct account calls.

## 6. HCP trace (step-by-step recompute)

Pick at least 5 HCPs and 1 cohort (c28, plus one training cohort):

1. High activity (many Kerendia interactions in 12M).
2. Low activity (1 interaction, ideally near a window edge, e.g. day 30 / 31 before lookback end).
3. In universe, no activity (all 0, recency 999).
4. Co-detail interaction (Kerendia + Lynkuet) in 2026.
5. Account / office record or BHO-linked colleague activity.

For each HCP print the value at every step:

| Step | What | Value |
| --- | --- | --- |
| 1 | PROVIDER_ID to BHID(s) via mapping | |
| 2 | Raw `FACT_CALL` records in the 12M window | |
| 3 | After Kerendia detail rule | |
| 4 | After record classification (count per class) | |
| 5 | After record type mapping (F2F / GROUP / REMOTE / OTHER) | |
| 6 | Per window (1 / 3 / 6 / 12M) | |
| 7 | Final feature value in output | |
| 8 | Match (step 6 = step 7) | |

**Results (20 Nov 2026).** Raw rows pulled from Snowflake for each BHID from 2024-03-01 to 2026-09-17; rules applied in pandas, independently of the notebook code.

| Case | PROVIDER_ID / BHID | Cohort | Raw rows | In 12M window | Submitted | Kerendia detail | Classes | HCP record types |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 High activity | 7809530 / BH10459894 | c28 | 175 | 82 | 82 | 82 | HCP 82 | F2F 82 |
| 2 Window edge (last call 30 days before END) | 10036694 / BH10643285 | c28 | 7 | 4 | 4 | 4 | HCP 4 | F2F 3, REMOTE 1 |
| 3 No activity | 15224815 / BH13469856 | c28 | 0 | 0 | 0 | 0 | none | none |
| 4 Co-detail + meal | 7760345 / BH10566306 | c28 | 66 | 29 | 29 | 28 | HCP 20, ACCOUNT_OFFICE 8 | F2F 20 |
| 5 Account / office + group | 7170604 / BH10629218 | c28 | 16 | 12 | 12 | 12 | HCP 7, ACCOUNT_OFFICE 5 | F2F 4, GROUP 3 |
| 6 Training cohort | 12026366 / BH12896607 | c10 | 9 | 7 | 7 | 5 | HCP 5 | F2F 3, REMOTE 2 |

Final values (output = recomputed for all 90 values):

| Feature | 1 | 2 | 3 | 4 | 5 | 6 |
| --- | --- | --- | --- | --- | --- | --- |
| `FLD_INT_TOTAL_1M` | 9 | 0 | 0 | 4 | 2 | 0 |
| `FLD_INT_TOTAL_3M` | 30 | 3 | 0 | 6 | 3 | 2 |
| `FLD_INT_TOTAL_6M` | 52 | 4 | 0 | 12 | 7 | 5 |
| `FLD_INT_TOTAL_12M` | 82 | 4 | 0 | 20 | 7 | 5 |
| `FLD_INT_F2F_12M` | 82 | 3 | 0 | 20 | 4 | 3 |
| `FLD_INT_GROUP_12M` | 0 | 0 | 0 | 0 | 3 | 0 |
| `FLD_INT_REMOTE_12M` | 0 | 1 | 0 | 0 | 0 | 2 |
| `FLD_INT_MEAL_12M` | 1 | 0 | 0 | 3 | 4 | 0 |
| `FLD_INT_KER_ONLY_6M` | 3 | 4 | 0 | 7 | 1 | 5 |
| `FLD_INT_KER_CODETAIL_6M` | 49 | 0 | 0 | 5 | 6 | 0 |
| `FLD_INT_KER_PRIMARY_6M` | 52 | 4 | 0 | 12 | 7 | 5 |
| `FLD_DAYS_SINCE_LAST_INT` | 0 | 30 | 999 | 2 | 8 | 33 |
| `FLD_N_REPS_12M` | 2 | 2 | 0 | 2 | 2 | 1 |
| `FLD_ACCT_OFFICE_12M` | 0 | 0 | 0 | 8 | 5 | 0 |
| `FLD_DAYS_SINCE_LAST_ACCT_OFFICE` | 999 | 999 | 999 | 7 | 21 | 999 |

Not traced: C7 organisation features, C4 median gap and active months, C5 main rep share and rep change, C8 trend, C9. They are covered by the invariant checks (Q10) only.

## 7. Points found during QC

* Placeholder `0`: resolved in Q1. Removed in cell 5 with a hard-coded filter rather than the `EXCLUDE_PROVIDER_IDS` setting used in the message and MSL notebooks. Works, but align the setting across notebooks.
* 38 BHIDs map to 2 universe PROVIDER_IDs each (76 HCPs); their activity is copied to both HCPs. Small, but flag to the modelling team.
* Notebook cell 1 still says the cohort file ends at C26 (2025-04-16), and the cell 4 comment says the first lookback starts 2022-03-17. Both are out of date (now c1 to c28, lookback end 2024-06-17 to 2026-09-17).
* The deliverable is the combined file (57 features), not only the 53-column core file. C9 is not in the readiness plan or the client summary.
* C9 direct account call features are almost constant (0.00% non-default in train and test).
* `field_interaction` and `field_org_link` are not saved as files, so other blocks cannot reuse them as the readiness plan intends.
* V3 (BHO parent / child with the CRM team) is still open, so BHO top-level calls stay out of the schema.
* Co-detail is low in training (12M non-zero 1.69% across c1 to c24) and high in test / holdout (11.78% / 13.82%). Per-cohort values were not checked.

## 8. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 12 / 13 (Q13 FAIL on documentation only) |
| Doc fixes (to do) | (1) Update notebook cell 1 and the cell 4 comment to c1 to c28. (2) Add C9 and the 57-feature combined output to the readiness plan (Phase 1) and the client summary; change `26 cohorts` in readiness. (3) Note in readiness that `field_interaction` / `field_org_link` are not persisted, or persist them |
| Modelling decisions (to agree) | (a) Drop or keep the 4 C9 features (almost constant). (b) Keep or merge the very sparse REMOTE 1 to 12M and GROUP 1M / 3M features. (c) Co-detail features and `FLD_CODETAIL_PERIOD_FLAG` change sharply from train to test (2026 start); decide whether to use them in training (readiness E6) |
| Known limitation | 38 BHIDs shared by 2 HCPs (76 HCPs) |
| Fixes made to the notebook | None (QC was read-only) |
| Ready for modelling | Yes, once decision (a) is made; doc fixes do not change values |
| Next channel | 02 iRep emails |

## Appendix A. Fill rate (combined output, 57 features)

0% null for every feature. Values are % of rows not equal to the default (0, or 999 / 365 / 1.0 where noted). Train = c1 to c24, test = c25 to c26, holdout = c27 to c28.

| Feature | Default | All | Train | Test | Holdout | c28 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `FLD_INT_TOTAL_1M` | 0 | 8.92 | 8.43 | 11.46 | 12.22 | 12.47 | 16 |
| `FLD_INT_F2F_1M` | 0 | 8.73 | 8.27 | 11.13 | 11.85 | 12.09 | 16 |
| `FLD_INT_GROUP_1M` | 0 | 0.21 | 0.17 | 0.40 | 0.47 | 0.49 | 7 |
| `FLD_INT_REMOTE_1M` | 0 | 0.05 | 0.05 | 0.06 | 0.06 | 0.06 | 6 |
| `FLD_INT_TOTAL_3M` | 0 | 14.64 | 13.96 | 18.31 | 19.11 | 19.30 | 31 |
| `FLD_INT_F2F_3M` | 0 | 14.37 | 13.72 | 17.86 | 18.60 | 18.77 | 30 |
| `FLD_INT_GROUP_3M` | 0 | 0.41 | 0.34 | 0.77 | 0.87 | 0.90 | 16 |
| `FLD_INT_REMOTE_3M` | 0 | 0.13 | 0.13 | 0.13 | 0.14 | 0.15 | 17 |
| `FLD_INT_TOTAL_6M` | 0 | 18.59 | 17.88 | 22.17 | 23.65 | 23.86 | 52 |
| `FLD_INT_F2F_6M` | 0 | 18.29 | 17.61 | 21.71 | 23.14 | 23.34 | 52 |
| `FLD_INT_GROUP_6M` | 0 | 0.57 | 0.48 | 1.02 | 1.19 | 1.23 | 24 |
| `FLD_INT_REMOTE_6M` | 0 | 0.23 | 0.23 | 0.23 | 0.25 | 0.25 | 22 |
| `FLD_INT_TOTAL_12M` | 0 | 23.31 | 22.50 | 27.55 | 28.79 | 28.92 | 92 |
| `FLD_INT_F2F_12M` | 0 | 23.00 | 22.21 | 27.10 | 28.30 | 28.42 | 92 |
| `FLD_INT_GROUP_12M` | 0 | 0.77 | 0.67 | 1.32 | 1.52 | 1.56 | 39 |
| `FLD_INT_REMOTE_12M` | 0 | 0.39 | 0.40 | 0.36 | 0.39 | 0.39 | 35 |
| `FLD_INT_MEAL_1M` | 0 | 1.72 | 1.65 | 2.06 | 2.16 | 2.21 | 5 |
| `FLD_INT_MEAL_3M` | 0 | 3.80 | 3.66 | 4.60 | 4.63 | 4.66 | 12 |
| `FLD_INT_MEAL_6M` | 0 | 5.50 | 5.32 | 6.42 | 6.72 | 6.75 | 18 |
| `FLD_INT_MEAL_12M` | 0 | 7.67 | 7.46 | 8.77 | 9.11 | 9.13 | 32 |
| `FLD_INT_MEAL_SHARE_6M` | 0 | 5.50 | 5.32 | 6.42 | 6.72 | 6.75 | 1 |
| `FLD_INT_MEAL_SHARE_12M` | 0 | 7.67 | 7.46 | 8.77 | 9.11 | 9.13 | 1 |
| `FLD_INT_KER_ONLY_3M` | 0 | 12.92 | 13.09 | 11.82 | 11.89 | 11.88 | 31 |
| `FLD_INT_KER_CODETAIL_3M` | 0 | 2.55 | 1.38 | 9.14 | 10.01 | 10.19 | 28 |
| `FLD_INT_KER_PRIMARY_3M` | 0 | 14.27 | 13.69 | 17.30 | 18.15 | 18.31 | 31 |
| `FLD_INT_KER_ONLY_6M` | 0 | 17.14 | 17.40 | 15.30 | 15.82 | 15.95 | 51 |
| `FLD_INT_KER_CODETAIL_6M` | 0 | 3.04 | 1.53 | 11.56 | 12.64 | 12.80 | 49 |
| `FLD_INT_KER_PRIMARY_6M` | 0 | 18.26 | 17.69 | 20.88 | 22.52 | 22.78 | 52 |
| `FLD_INT_KER_ONLY_12M` | 0 | 22.52 | 22.17 | 24.61 | 24.63 | 24.38 | 92 |
| `FLD_INT_KER_CODETAIL_12M` | 0 | 3.27 | 1.69 | 11.78 | 13.82 | 14.29 | 60 |
| `FLD_INT_KER_PRIMARY_12M` | 0 | 23.08 | 22.35 | 26.89 | 27.99 | 28.08 | 92 |
| `FLD_KER_PRIMARY_SHARE_6M` | 0 | 18.26 | 17.69 | 20.88 | 22.52 | 22.78 | 1 |
| `FLD_KER_PRIMARY_SHARE_12M` | 0 | 23.08 | 22.35 | 26.89 | 27.99 | 28.08 | 1 |
| `FLD_CODETAIL_PERIOD_FLAG` | 0 | 32.14 | 20.83 | 100.00 | 100.00 | 100.00 | 1 |
| `FLD_DAYS_SINCE_LAST_INT` | 999 | 23.31 | 22.50 | 27.55 | 28.79 | 28.92 | 999 |
| `FLD_N_ACTIVE_MONTHS_6M` | 0 | 18.59 | 17.88 | 22.17 | 23.65 | 23.86 | 6 |
| `FLD_N_ACTIVE_MONTHS_12M` | 0 | 23.31 | 22.50 | 27.55 | 28.79 | 28.92 | 12 |
| `FLD_MEDIAN_GAP_DAYS_12M` | 365 | 17.69 | 17.08 | 20.83 | 21.96 | 22.11 | 365 |
| `FLD_N_REPS_6M` | 0 | 18.59 | 17.88 | 22.17 | 23.65 | 23.86 | 6 |
| `FLD_N_REPS_12M` | 0 | 23.31 | 22.50 | 27.55 | 28.79 | 28.92 | 7 |
| `FLD_REP_CHANGE_6M` | 0 | 4.17 | 4.37 | 2.58 | 3.37 | 3.65 | 1 |
| `FLD_MAIN_REP_SHARE_12M` | 0 | 23.31 | 22.50 | 27.55 | 28.79 | 28.92 | 1 |
| `FLD_ACCT_OFFICE_3M` | 0 | 3.84 | 3.80 | 4.00 | 4.08 | 4.02 | 16 |
| `FLD_ACCT_OFFICE_6M` | 0 | 5.92 | 5.94 | 5.57 | 6.08 | 6.11 | 28 |
| `FLD_ACCT_OFFICE_12M` | 0 | 9.11 | 9.13 | 8.97 | 9.04 | 8.98 | 60 |
| `FLD_DAYS_SINCE_LAST_ACCT_OFFICE` | 999 | 9.11 | 9.13 | 8.97 | 9.04 | 8.98 | 999 |
| `FLD_ACCT_OFFICE_SHARE_12M` | 0 | 9.11 | 9.13 | 8.97 | 9.04 | 8.98 | 1 |
| `FLD_ORG_LINKED_FLAG` | 0 | 21.36 | 20.35 | 26.67 | 28.15 | 28.39 | 1 |
| `FLD_ORG_COLLEAGUE_INT_3M` | 0 | 15.13 | 14.22 | 20.08 | 21.16 | 21.36 | 481 |
| `FLD_ORG_COLLEAGUE_INT_6M` | 0 | 16.62 | 15.71 | 21.44 | 22.77 | 22.95 | 818 |
| `FLD_ORG_N_COLLEAGUES_CALLED_6M` | 0 | 16.62 | 15.71 | 21.44 | 22.77 | 22.95 | 212 |
| `FLD_INT_3M_VS_PRIOR_3M` | 0 | 15.98 | 15.35 | 19.18 | 20.33 | 20.48 | 20 (min -27) |
| `FLD_INT_3M_PRIOR_3M_RATIO` | 1.0 | 15.98 | 15.35 | 19.18 | 20.33 | 20.48 | 20 (min 0.05) |
| `FLD_ACCT_DIRECT_CALL_3M` | 0 | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 1 |
| `FLD_ACCT_DIRECT_CALL_6M` | 0 | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 1 |
| `FLD_ACCT_DIRECT_CALL_12M` | 0 | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 1 |
| `FLD_DAYS_SINCE_ACCT_DIRECT_CALL` | 999 | 0.00 | 0.00 | 0.00 | 0.03 | 0.03 | 999 |
