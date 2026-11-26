# Veeva Link Key People: NBA 3.1 Readiness Plan

**Group:** HCP influence and scientific activity (new feature block for NBA 3.1)  
**Purpose:** a step-by-step plan to turn Veeva Link Key People ("Veeva Link to People") data into a clean, leakage-safe and tested feature block for the NBA 3.1 HCP-level model, and into business inputs for the NBA list  
**Builds on:** files 10 to 40 in this folder (see `00_README_folder_guide.md`), mainly `40_veeva_link_data_assessment_v2.md` (sections 1 to 11), `33_veeva_link_feature_engineering_plan.md` (66 planned features) and `11_veeva_link_data_sources_and_feature_feasibility` (feasibility of 56 catalog features and a 153-feature pilot on 100 HCPs)  
**Same structure as:** `04_Promotional_Features/non_personal_promotional_features/13_hcp_digital_nba_3_1_readiness_plan.md` and `50_digital_nba_3_1_readiness_plan.md`, and `personal_promotional_features/40_field_activity_nba_3_1_readiness_plan.md`  
**Source:** Snowflake `CPH_DB_PROD.ANALYTICS_V2.ANLT_VEEVA_LINK_*` (17 tables)  
**Status:** draft for discussion  
**Date:** November 18, 2026 (cohort anchor updated November 25, 2026: principle 4, U7, P2)

---

## 1. Scope

| In scope | Out of scope (owned elsewhere) |
| --- | --- |
| **Coverage flags**: has a Veeva profile, has a Kerendia-relevant decile | Bayer speaker programmes and Bayer events (personal block, `personal_promotional_features/14_speaker_programs_nba_3_0.md`); Veeva Link only adds **external** activity |
| **Influence rankings**: `CLINICAL_LEADER`, `FOCUS_AREA`, `DIGITAL_REACH_FOCUS_AREA`, `INDEX` | Bayer MSL interactions (personal block, MSL flag MD-1 in `40_...`) |
| **Clinical-trial experience**: `SCIENTIFIC_EXPERT_CLINICAL_TRIAL` + `CLINICAL_TRIAL` | Prescribing behaviour (claims blocks; Veeva is not a prescriber database) |
| **Scientific and congress activity**: publications, events | HCP specialty as a primary attribute (HCP Universe / NPPES); Veeva specialty is a fallback only |
| **Industry relationships**: `PAYMENT` (CMS Open Payments), `COMPANY_SPONSORSHIP` | Non-US experts (12.5% of Veeva; no NPI) |
| **Profile**: expert type, degree, academic affiliation, associations | `COMPANY_COLLABORATION` (empty), `COMMUNITY_LEADER_FOCUS_AREA` (deprecated), `SCIENTIFIC_EXPERT_CHANGELOG` and `SCIREACH_MAPPING` (not in the warehouse) |
| **Business use in the NBA**: untargeted authorities and channel hints | Changing the call plan itself (brand / sales operations decision) |

## 2. Goal and how we will judge success

**Goal.** Add a **small, fixed and documented** Veeva Link block that brings a signal claims do not carry (how influential and clinically active an HCP is) without introducing look-ahead bias, and use the same data to point the NBA at influential HCPs and the right type of action.

**Success criteria** (to agree with the modelling team):

| # | Criterion | How it is measured |
| --- | --- | --- |
| S1 | **Stable schema** | Same columns every run; column list fixed in a config table; a new focus name or event type adds no column |
| S2 | **Correct joins** | HCP Universe to Veeva match rate reproduces the assessment: 77.7% overall (228,932 of 294,727), 83.2% for segments A to E; any run more than 1 point off fails |
| S3 | **Missing is not zero** | Every HCP carries a three-state coverage flag (not in Veeva / in Veeva, unscored / scored); no feature imputes 0 for HCPs not in Veeva without the flag |
| S4 | **No look-ahead bias** | Every feature has a leakage tier (T1 / T2 / T3, section 4) and passes the time-split check (experiment E6) |
| S5 | **Model value** | Validation metric improves over the NBA 3.1 model without Veeva (E0) |
| S6 | **Adds new information** | Veeva features keep importance after the claims, call-plan and field blocks are in the model (no near-duplicate of claims volume) |
| S7 | **Explainable and compliant** | Every kept feature maps to a Veeva table and a plain-language rule; licence and compliance approval for commercial use recorded (Q1, Q2) |

## 3. Starting point

### 3.1 What we know about the data (assessment v2)

| Finding | Impact on NBA 3.1 | Where it is explained |
| --- | --- | --- |
| **No history**: `IS_LATEST_FLAG = 'Y'` on 100% of rows; current state only | Scores and profile fields cannot be rebuilt for past model months; only dated activity can be windowed | assessment, 1.5 (1) and 3 |
| **Stale and misaligned loads**: `SCIENTIFIC_EXPERT` 2025-06-25, all child tables 2025-03-06 | Activity after March 2025 is missing; for 2026 inference months the data is 18+ months old; new experts look inactive | assessment, 1.5 (2) |
| **Activity date ranges**: publications 2020 to 2024, payments `PROGRAM_YEAR` 2013 to 2023, trials end dates to 2026 | Windows that end after the data cut-off are truncated and look like a decline | assessment, 3 and 4.7 |
| **Coverage**: 77.7% of the HCP Universe in Veeva; 64.4% of matched HCPs have a Kerendia-relevant decile (`CLINICAL_LEADER` 58.9%, `FOCUS_AREA` 12.7%, `DIGITAL_REACH` 2.1%) | Two kinds of missing (not in Veeva 22.3%; in Veeva but unscored 35.6%) | assessment, 5 |
| **Segments agree with deciles**: A mean best decile 7.23, B 6.51, Non-target 4.80 | Part of the decile signal is already in the call-plan segment; must show added value within segment | assessment, 7 |
| **Decile separates within segment**: in segment A, 3.4% of decile-1 HCPs run trials vs 16.5% at decile 10 | Veeva adds information the call plan does not carry | assessment, 8.3 |
| **Untargeted authorities**: 18,209 Non-target HCPs at deciles 8 to 10 (10,113 at 9 to 10) | Business input for target-list review | assessment, 7.4 and 9.2 |
| **`CLINICAL_LEADER` ranks patient volume**, including drug classes (MRA, SGLT2) | Possible overlap with, or leakage of, prescribing volume (to test) | assessment, 4.2 and 8.4 |
| **Skewed activity**: median 0 publications, trials and events in every group | Flags, logs or bins rather than raw counts | assessment, 8 |
| **Data-quality issues**: `MEDICAL_EVENT.EVENT_TYPE` column shift (~0.3%), `ASSOCIATION.PAST_POSITION` always 'N', 239,201 orphan `ADDRESS` rows, `EXPERT_TYPE` remapped, `PUBLICATION_TYPE` multilingual | Field-level rules and exclusions | assessment, 4 and 11 |

### 3.2 What has been built so far

| Asset | State | Gap for NBA 3.1 |
| --- | --- | --- |
| `33_veeva_link_feature_engineering_plan.md` | 66 features in 13 tables, leakage tiers, naming `veeva_` | Written before v2: uses High / Medium / Low tiers and the narrow focus list (34.8% scored vs 64.4% in v2); target described as T1D / T2D / HTN NBRx |
| `11_veeva_link_data_sources_and_feature_feasibility` notebook | Feasibility of 56 catalog features (36 ready, 12 with caveat, 4 substitute, 1 external, 2 not feasible); 153-feature pilot on 100 HCPs | Pilot keyed on `SE_ID`, not the HCP Universe spine; disease deciles in section B partly read from deprecated `COMMUNITY_LEADER_FOCUS_AREA`; composites z-scored on 100 HCPs; `DIGITAL_REACH` matched 1 of 100 (ID format, "CG"-prefixed IDs) |
| `22_veeva_link_focus_name_taxonomy.csv` and assessment section 5.3 | Curated Kerendia-relevant focus names: 17 `CLINICAL_LEADER`, 147 `FOCUS_AREA`, 135 `DIGITAL_REACH` | Not yet a config table; three different scoping methods in use (v2 lists, pilot regex, EDA regex) |
| `30_veeva_link_kol_identification_and_activity_eda`, `31_veeva_kol_list.csv`, `32_veeva_hcp_decile_segments.csv` | KOL lists and decile segments | One-off extracts, not a pipeline |

NBA 3.0 has no Veeva Link feature block (to confirm against the NBA 3.0 final feature list).

## 4. Design principles for NBA 3.1

1. **Claims HCP Universe is the spine.** HCP Universe (`PROVIDER_ID`) to `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING` (NPI, BH_ID) to `SCIENTIFIC_EXPERT.NPI` (US, not deleted) to child tables on `SE_ID`. Every HCP keeps a row.
2. **Three-state coverage, never silent zeros.** `veeva_coverage_status` = `NOT_IN_VEEVA` / `IN_VEEVA_UNSCORED` / `SCORED`. Count features are 0 only for HCPs in Veeva; for HCPs not in Veeva they stay null (or 0 plus the flag, depending on the model library).
3. **Leakage tier on every feature.**
   * **T1 (low)**: dated activity (trials, publications, events, payments). Windowed relative to the cohort anchor date (principle 4).
   * **T2 (medium)**: slow-moving profile (expert type, degree, academic affiliation, associations, sponsorship). Used as static attributes.
   * **T3 (high)**: vendor scores (`CLINICAL_LEADER`, `FOCUS_AREA`, `DIGITAL_REACH`, `INDEX`). Today's view only; used only if they pass E6, otherwise kept for business rules.
4. **Windows respect the data cut-off.** The **anchor date** of each cohort is its `lookback_end_date` in the NBA 3.1 claims cohorts (`kerendia_nba_3_1_volume/cohorts/claims/cohorts.parquet`: 28 cohorts `c1` to `c28`, `offset_days = 0`, the same cohorts as the claims HCP features), e.g. c1 2024-05-01, c12 2025-04-01, c28 2026-08-01. For T1 features, the window ends at the earlier of the anchor date (inclusive) and the table's data cut-off (`veeva_data_cutoff`, today 2025-03-06); the window start is excluded. Payments use CMS program years: a year counts only if it was published (30 June of the following year) by the window end. Result (run of 25 Nov 2026): c1 to c11 (anchors 2024-05-01 to 2025-03-01) each have their own windows; from c12 (anchor 2025-04-01) every window is capped at 2025-03-06, so T1 values are the same for c12 to c28. Payment years are 2020 to 2022 for c1 and c2, 2021 to 2023 from c3. Windows are fixed (3 and 5 years), not running. A `veeva_data_age_months` value is logged per run (not a model feature) so stale loads are visible.
5. **One focus-name dictionary.** The v2 curated lists (section 5.3 of the assessment) become a config table: table, `FOCUS_NAME`, theme (Kerendia / MRA, SGLT2, GLP-1, DPP-4, other T2D, ACE / ARB, hyperkalemia, hypertension, CKD, heart failure, T2D, T1D, diabetes general, cardiometabolic), indication (HF / T1D / CKD / other). Free-text scoping of trial, publication and event names uses one keyword list (feature plan section 7) with `ILIKE`, never `REGEXP_LIKE` through the Spark connector.
6. **Indication as a dimension.** Same rule as the digital plan: keep the Kerendia total and add HF, T1D and CKD views where the data supports it (deciles and trials), not as filters.
7. **Few, meaningful features.** Build a candidate set of about 60 to 80 columns from the 153 pilot features and 66 planned features, then select down (target 15 to 30 in the model). Prefer flags, log counts and bins.
8. **No double counting with internal data.** Bayer speaker programmes and MSL contacts stay in the personal block; Veeva payment features exclude Bayer or keep Bayer as a separate flag only (decision D3).
9. **Language.** Describe the NBA output as the NBA dropdown list; Veeva rankings are "influence" or "authority", not "KOL status" unless Medical Affairs confirms the definition.

## 5. Work plan

The work is split into phases. Each phase ends with a gate (section 7).

### Phase 0, optimized: unblock the feature build

**Problem with the first draft.** Phase 0 mixed in-house tasks with tasks that depend on other teams (Veeva refresh, archive history, licence, compliance, Medical review). Treated as one blocking phase, feature building would wait weeks for answers that do not change the build itself. The data we have today (the 2025-03 / 2025-06 snapshot) is enough to build, test and select features; a refresh only changes the input rows, not the code.

**Principle.** Split Phase 0 into two parallel tracks. **Track U (unblock)** is in-house, starts now and is the only thing that blocks Phase 1. **Track X (external)** runs at the same time and gates only production release, rep-facing use and T3 scores, not the build.

#### 0.1 Blockers and how each is removed

| Blocker in the first draft | Why it blocked | Optimized approach | Effect |
| --- | --- | --- | --- |
| Fresh, aligned Veeva load | Waiting on Veeva and Data Engineering | Build on the current snapshot; all windows use the as-of rule (U7), so a refresh is a re-run, not a redesign | Build starts now |
| Monthly archive | Needs a scheduled job and an owner | First archive point = the one-time snapshot copy (U1); the monthly job (X1) reuses the same code | No wait; history starts today |
| Slow, fragile Snowflake reads | 182M `FOCUS_AREA` and 109M `PAYMENT` rows pulled again for each feature family; `REGEXP_LIKE` returns 0 rows on free text through the Spark connector | Copy latest US rows once into Delta (U1), then do all joins and text matching in Databricks SQL | Fast reruns; the regex trap goes away |
| Pilot code keyed on 100 `SE_ID`s | Every family query is filtered with `in_coh()` | Swap the cohort for the spine (U2); the 11 family builds (A to K) stay as they are | Pilot code reused, not rewritten |
| Feature windows per anchor month | Re-querying raw rows for every anchor is slow | Build long, dated activity tables once (U3); windowing becomes a cheap join to the anchor list | Window choices can change without new extracts |
| Medical / brand review of the focus-name dictionary | Review meetings take time | Load the curated v2 lists as dictionary v1 now (U4); the review edits rows later (X5) and gates only G3 | No wait |
| `DIGITAL_REACH` ID mismatch | 1 of 100 pilot matches | Time-box the check to one day (U6); if not solved, leave `DIGITAL_REACH` out of v1 (2.1% coverage of matched HCPs) | Small gap, no blocker |
| Licence and compliance (Q1, Q2) | Answers can take weeks | Ask in week 1 (X3); keep features offline and model-only until answered; nothing is shown to reps | Build and experiments continue |
| T3 leakage question | Unclear if scores may be used | Build T3 but keep it in a separate table that only E5 / E6 read (default D2) | No wait |

#### 0.2 Track U: in-house, blocks Phase 1 (target: about 2 weeks, an estimate)

| ID | Task | Detail | Done when |
| --- | --- | --- | --- |
| U1 | Freeze the snapshot in Delta | One-time copy of the 15 in-use `ANLT_VEEVA_LINK_*` tables (all except the empty `COMPANY_COLLABORATION` and the deprecated `COMMUNITY_LEADER_FOCUS_AREA`) to `kerendia_nba_3` as `veeva_link_<table>_snapshot`, with standard filters applied once (`IS_LATEST_FLAG = 'Y'`, `COALESCE(SYS_DELETE_FLAG, 0) = 0`, `ISDELETED` on `SCIENTIFIC_EXPERT`; `SYS_TENANT = 'US'` on person tables only, never on `PUBLICATION` / `CLINICAL_TRIAL` / `MEDICAL_EVENT`) and `load_date` / `src_load_id` columns. This is also archive point 1 | Row counts match assessment 1.4 for latest rows |
| U2 | Spine and mapping table | `veeva_npi_se_map`: HCP Universe `PROVIDER_ID` to `SOURCE_PROVIDER_BHID_NPI_MAPPING` (NPI, BH_ID) to `SE_ID`, with match route; handle the 2 providers that share an `SE_ID` | 228,932 matched of 294,727 (77.7%) |
| U3 | Long activity tables | One row per expert x item with date and role, for the matched experts only: trials (`SE_ID`, trial, role, phase, start, end, in-scope tags), publications (author position, date, type, tags), events (position, start date, tags), payments (program year, nature, type, company, amount). Profile and score tables stay one row per expert or expert x focus name | Totals match assessment 8.1 (358,601 publications, 54,673 trials, 152,510 events) |
| U4 | Config tables v1 | (a) Focus-name dictionary from assessment 5.3 (17 / 147 / 135 names, theme, indication) plus `22_veeva_link_focus_name_taxonomy.csv`; (b) free-text keyword list from `33_...` section 7 with a talk-title stop-list; (c) window list (3 and 5 years) | Best-decile coverage reproduces 147,489 (64.4%) |
| U5 | Data-quality rules in the copy step | Drop column-shifted `EVENT_TYPE` rows; ignore `PAST_POSITION`; drop orphan `ADDRESS` rows; normalise `PUBLICATION_TYPE`; `LPAD` ZIP; hardcode the 0 to 4 Scientific Reach lookup; keep 0 to 10 and 0 to 4 indices apart. Only rules that touch planned features; the rest are logged | DQ log written per run |
| U6 | Pilot code fixes | Move disease deciles off `COMMUNITY_LEADER_FOCUS_AREA` to `CLINICAL_LEADER` and `FOCUS_AREA`; standardise composites on the full universe; one-day time-box for the `DIGITAL_REACH` ID check | Pilot sections A to K run on the spine |
| U7 | As-of rule and fixed schema | T1 windows end at min(anchor date = claims cohort `lookback_end_date`, table data cut-off); cut-off stored per table from U1; output columns generated from U4 and filled per principle 2 | Same columns on two consecutive runs |
| U8 | Acceptance checks | One notebook that re-computes the assessment's key numbers from the Delta copy (U1 counts, U2 match 77.7% / 83.2% for A to E, U4 coverage 64.4%, segment by decile table 7.2) and fails if any is more than 1 point off | All checks pass |

Suggested order: U1 and U4 in parallel (days 1 to 3), then U2 and U5, then U3 and U6, then U7 and U8. U8 is the entry ticket to Phase 1.

#### 0.3 Track X: external, in parallel (gates release, not the build)

| ID | Task | Gates | Owner |
| --- | --- | --- | --- |
| X1 | Monthly archive job, reusing U1 code, with row-count and match-rate checks | T3 in NBA 3.2 | Data Engineering + NBA team |
| X2 | Fresh, aligned load and refresh cadence (hub 2025-06-25, children 2025-03-06) | Production release (G3) | Data Engineering, Vendor Management |
| X3 | Licence and compliance answers (Q1, Q2), asked in week 1 | Production release and Phase 3 rep-facing use | Vendor Management, Legal, Compliance |
| X4 | Veeva questions: history or changelog (Q4), `COMPANY_COLLABORATION` (Q5), what `CLINICAL_LEADER` and `DIGITAL_REACH` measure (Q6) | T3 decision (G2) | Vendor Management, NBA team |
| X5 | Medical / brand review of dictionary v1 (Q7) | Final block (G3) | Medical Affairs, brand |

### 5.1 Candidate feature list, first version

From the feature plan and the 153-feature pilot, reduced to what the v2 findings support. Names follow `veeva_{group}_{metric}_{window}`.

| Family | Tier | Example features | Approx. count | Why (assessment section) |
| --- | --- | --- | --- | --- |
| Coverage | T2 | `veeva_coverage_status`, `veeva_has_profile`, `veeva_has_inscope_decile`, `veeva_n_inscope_themes` | 4 | Unscored HCPs are far less active than scored ones (8) |
| Clinical trials | T1 | `veeva_trial_any_5y`, `veeva_trial_pi_flag_5y`, `veeva_trial_n_inscope_5y`, `veeva_trial_max_phase_inscope`, `veeva_trial_active_flag`, `veeva_trial_finerenone_flag`, `veeva_trial_mra_flag`, `veeva_trial_sglt2_flag`, `veeva_trial_cardiorenal_n_5y` | 10 to 12 | Trials and PI role rise with decile and separate HCPs within segment (8.1, 8.3) |
| Publications | T1 | `veeva_pub_any_5y`, `veeva_pub_log_n_5y`, `veeva_pub_senior_author_flag_5y`, `veeva_pub_n_inscope_5y`, `veeva_pub_months_since_last` | 6 to 8 | Share who publish is flat across deciles but high vs unscored (8.4); segment D most active (8.2) |
| Congress | T1 | `veeva_event_any_3y`, `veeva_event_podium_flag_3y`, `veeva_event_n_inscope_3y`, `veeva_event_poster_flag_3y` | 4 to 6 | Podium roles = peer influence; channel hint for speaker / peer-to-peer (9.2) |
| Industry payments | T1 | `veeva_pay_any_3y`, `veeva_pay_log_total_3y`, `veeva_pay_n_companies_3y`, `veeva_pay_speaker_consult_flag_3y`, `veeva_pay_competitor_flag_3y`, `veeva_pay_research_flag_3y`, `veeva_pay_excl_food_log_3y` | 7 to 9 | Payments rise with decile (USD 1,035 to 8,510 median); segment A highest (8.1, 8.2) |
| Profile | T2 | `veeva_expert_type`, `veeva_is_md_do`, `veeva_is_phd`, `veeva_is_academic`, `veeva_emerging_expert`, `veeva_n_editorial_boards`, `veeva_n_society_roles`, `veeva_kidney_society_flag`, `veeva_n_sponsors` | 8 to 10 | Practice setting and seniority (4.1, 4.8, 4.9) |
| Influence rankings | T3 | `veeva_best_decile`, `veeva_decile_bin`, `veeva_cl_decile_{ckd,hf,t2d,t1d,htn}`, `veeva_cl_decile_mra_class`, `veeva_cl_decile_sglt2_class`, `veeva_fa_decile_max_inscope`, `veeva_dr_any_inscope`, `veeva_index_{publication,trial,event,guideline}` | 14 to 18 | Rank HCPs by disease authority (7); only if E6 passes |
| Composites | mixed | `veeva_industry_engagement`, `veeva_network_breadth` | 2 to 4 | Standardised on the full HCP Universe, not the pilot |
| Colocation x Veeva (cross) | T3 | `veeva_idn_expert_share`, `veeva_idn_expert_share_zero_flag`, `veeva_practice_expert_peer_flag` | 3 | Signal test, section 5.2 |

Candidate set: about 60 to 80 columns. Feature selection (section 6) is expected to keep 15 to 30.

### 5.2 Combined colocation, IDN and Veeva features: signal test (2026-11-18)

**Question.** Should the colocation / IDN block and the Veeva block be combined, or built separately? **Answer:** build them as separate blocks on the same spine, plus a small set of cross features that passed the signal test below. Colocation peer writing is dated and low risk; Veeva scores are a snapshot (T3), so a full merge would carry T3 risk into the colocation features.

**Method.** Notebook `60_veeva_colocation_idn_combined_signal_test`, the same method as `33_2_colocation_idn_data_assessment.md` (in the `_pg` repo copy, `NBA 3.0 Static Feature Analysis`; the colocation / IDN readiness plan is `33_3_colocation_idn_nba_3_1_readiness_plan.md` in the same folder):

* Universe and grouping: 294,727 HCPs. Practice (L1) = BEST_AFFL `BRAND_RANK = 1` account. IDN (L4) = `mdm_stg_acct_hrchy_ker`, with 'NA' / 'Multiple Doctors' counted as no IDN.
* Writers: LRx V7, weekly rows, Kerendia NBRx > 0.
* Windows: look-back 2025-07-25 to 2025-10-23; outcome 2025-10-24 to 2026-10-23. The HCP is always excluded from their own group.
* Expert: best Kerendia-relevant decile 8 to 10, computed with the section 5.3 lists of the assessment. That gives 37,076 experts (12.6% of the universe).
* Veeva loads (hub 2025-06-30, scores 2025-03-06) are earlier than both windows, so there is no look-ahead in this test.
* The baseline reproduces the colocation assessment exactly (233,102 HCPs with a practice peer; 15.7% vs 7.4%). Veeva coverage matches assessment v2 (228,932 matched; 147,489 with a decile).
* An independent self-join recount matched the practice results.
* These are one-feature-at-a-time checks, not model lift.

| Idea | Result (forward Kerendia writer rate) | New-writer view | Decision |
| --- | --- | --- | --- |
| 1a. Expert colleague in the practice (L1) | Raw 10.7% vs 8.6%, but confounded by size (median 23 peers with an expert colleague vs 3 without). Within size bands: 1 to 4 peers 15.3% vs 9.6%; 5 to 19 peers 12.2% vs 6.9%; 20+ peers 8.4% vs 5.2% | 7.6% vs 5.1%; 6.5% vs 4.2%; 5.3% vs 3.5% | **Test**, only together with practice size |
| 1b. Same, beyond the practice peer-writer flag | Practices with no peer writer, 5 to 19 peers: 7.7% vs 5.1%. Practices with a peer writer, 5 to 19 peers: 25.3% vs 22.1%. Without size bands the 2x2 reverses (14.2% vs 26.3%), so size control is required | 5.0% vs 3.6%; 11.7% vs 10.7% | Small gain on top of colocation |
| 1c. Expert colleague in the IDN (L4), yes / no | 8.9% vs 11.2% (reversed; 89% of IDN HCPs have an expert peer) | 5.1% vs 5.8% | **Drop** the flag |
| 1c. IDN expert share | Rises steadily from Q1 6.4% to Q5 12.3%; zero band (no expert peer) 11.2%. Holds for non-experts (Q1 5.6% to Q5 9.9%) | Q1 4.1% to Q5 6.8% | **Build** share + zero flag |
| 1d. IDN expert share beyond IDN writer share | Writer share not in top fifth: top-fifth expert share 9.5% vs 7.2%. Writer share in top fifth: 19.4% vs 13.2%. Spearman 0.43 between the two shares | 5.8% vs 4.5%; 9.5% vs 6.5% | Adds beyond colocation |
| 2a. Is the practice peer writer an expert? | 16.0% vs 15.3%. With the number of peer writers held fixed: 1 writer 17.7% vs 15.3%, 2 to 3 writers 15.4% vs 15.3%, 4+ writers 15.2% vs 16.8%. Reversed for non-expert HCPs (12.4% vs 13.5%) | 8.0% vs 7.6% | **Drop** |
| 2b. Expert share of IDN peer writers | U-shaped; within IDN writer-share quintiles mostly flat, except the top quintile | Mixed | **Drop**; the IDN writer share already covers it |
| 3. Non-writing experts in low-adoption IDNs | 33,601 experts with no look-back NBRx. 19,252 sit in 2,524 IDNs with a peer writer share of 5% or less: 10,790 Non-target, 3,842 segment B, 1,793 D, 1,255 A, 930 C, 642 E. Top specialties FM, CD, IM, END, NEP. Largest IDNs: HCA, CommonSpirit, Cleveland Clinic, Trinity, Piedmont. They still write at 12.5% to 14.0% vs 9.7% overall; experts in IDNs with a writer share above 20% write at 44.9% | 8.1% to 8.6% | **Business list** (B4), not a model feature |

**Notes.**

* The new-writer view here means no Kerendia TRx in the look-back (baseline 5.4%). The rule is now decided (Q11): writers and new writers come from KER-10 `active_nbrx_writers` in `kerendia_metric_views.mv_kerendia_nbrx`, so this test should be re-run on that definition before its numbers are reused.
* Practice and IDN come from the Q4-2026 snapshots applied to past months (same caveat as the colocation assessment).
* Ownership: the IDN peer **writer** share stays in the colocation notebook. The cross features need the Veeva expert flag, so they are built in the Veeva block from the colocation group keys (D7).

### Phase 1: T1 and T2 block (low risk)

| ID | Task | Detail | Dependency |
| --- | --- | --- | --- |
| P1 | Build coverage flags | Three-state status on the full HCP Universe | U2 |
| P2 | Build T1 activity features | Trials, publications, events, payments with 3- and 5-year windows ending at min(anchor date, data cut-off), one row per NPI for each claims cohort c1 to c28; PI role, senior author, podium role; in-scope versions from U4 | U3, U4, U7 |
| P3 | Build T2 profile features | Expert type, degree, academic affiliation, associations, sponsorship; Veeva specialty only where HCP Universe specialty is missing | U1, U5 |
| P4 | Move pilot to production | Turn the pilot build (sections A to K of `11_veeva_link_data_sources_and_feature_feasibility`) into a feature notebook keyed on the spine, all 294,727 HCPs; drop features constant on the full population | P1 to P3, U6 |
| P5 | Spot-check | Compare 10 known HCPs (from `31_veeva_kol_list.csv`) against their Veeva Link web profiles | P4 |

### Phase 2: T3 scores and leakage tests

| ID | Task | Detail | Dependency |
| --- | --- | --- | --- |
| R1 | Build T3 features | Best decile and per-theme deciles from `CLINICAL_LEADER` (disease and drug class), `FOCUS_AREA`, `DIGITAL_REACH`; `INDEX` pivot (4 indices on 0 to 10; Scientific Reach separate). Written to a separate table read only by E5 / E6 | U4, U6 |
| R2 | Prescribing-overlap test | `CLINICAL_LEADER` ranks patient volume. Correlate the MRA-class, SGLT2-class and CKD deciles with claims volume and Kerendia NBRx features already in the model; if a decile is a near copy of claims volume, drop it | R1, NBA 3.1 claims block |
| R3 | Time-split test | Train on anchors before the score date and test on anchors after; compare with the same model without T3 (E6) | R1 |
| R4 | Segment added-value test | Within each call-plan segment A to E, check that decile still separates NBRx (as it separates trial involvement in assessment 8.3) | R1 |
| R5 | Build cross features | `veeva_idn_expert_share` + zero flag, and `veeva_practice_expert_peer_flag`, from the colocation L1 / L4 keys, self excluded; written to the T3 table (section 5.2) | R1, colocation L1 / L4 keys |

### Phase 3: Business use in the NBA

| ID | Task | Detail |
| --- | --- | --- |
| B1 | Untargeted-authority list | Share the 18,209 Non-target HCPs at deciles 8 to 10 (10,113 at 9 to 10) with brand and sales operations for target-list review, split by specialty and indication |
| B2 | Action hints | Map activity type to the NBA reason or channel: podium speakers to peer-to-peer or speaker programme invitation, trial investigators to clinical-evidence messaging, MRA / SGLT2 class authorities to cardiorenal messaging. Business rules on the NBA dropdown list, not model features |
| B3 | Field review | Review hints and lists with Field Analytics and Medical Affairs before any rep-facing use |
| B4 | Low-adoption IDN expert list | 19,252 non-writing experts in 2,524 IDNs with a peer writer share of 5% or less (10,790 Non-target), by IDN, specialty and segment, for brand and key account teams (section 5.2, idea 3) |

### Phase 4: Operations

| ID | Task | Detail |
| --- | --- | --- |
| O1 | Monthly archive job | Production version of X1 |
| O2 | Freshness check | Each run logs data cut-off per table and data age; warn if a child table is more than 6 months older than the hub or more than 12 months old |
| O3 | Dictionary upkeep | Monthly report of new focus names and new unmapped keyword hits |
| O4 | Documentation | Final feature dictionary with business descriptions in this folder, same style as the digital and field documents |

## 6. Model experiments

All experiments use the NBA 3.1 HCP-level model, target and validation split; only the Veeva block changes. All other blocks stay fixed.

| Exp. | Veeva block | Question answered |
| --- | --- | --- |
| E0 | None | Baseline: NBA 3.1 without Veeva |
| E1 | Coverage flags only (P1) | Is being tracked by Veeva itself informative? |
| E2 | E1 + T1 activity, static (full snapshot totals) | Does activity add value, ignoring timing? |
| E3 | E1 + T1 activity, windowed to the anchor (P2) | Does correct timing change the result vs E2? (E2 much better than E3 is a sign of leakage) |
| E4 | E3 + T2 profile (P3) | Do profile attributes add value? |
| E5 | E4 + T3 scores (R1) | Do Veeva rankings add value on top of activity? |
| E6 | E5 with time split (R3) | Does the E5 gain hold on anchors after the score date? |
| E7 | E5 + cross features (R5), with the colocation block in E0 | Do the cross features add value on top of both colocation and Veeva? Keep only if E7 beats E5, also within segments and for new writers |

**Measures for each experiment:** validation metric of the NBA 3.1 model (same as the main model), SHAP share of the Veeva block, rank of the best Veeva feature, number of Veeva features kept after selection, stability of importance across time folds, and the gain within call-plan segments A to E (R4). Feature selection uses the same method as the main NBA 3.1 model.

## 7. Readiness gates

| Gate | Ready when |
| --- | --- |
| G0 (after Track U; entry to Phase 1) | Snapshot frozen in Delta (U1); acceptance checks pass (U8, S2); config tables v1 loaded (U4); fixed schema on two runs (U7); Track X requests sent (X1 to X5). Track X answers are **not** needed for G0 |
| G1 (after Phase 1) | T1 and T2 block built for all training instances; leakage check passed (no event after the anchor); fixed schema on two runs; spot-check done; E1 to E4 run and compared with E0 |
| G2 (after Phase 2) | Prescribing-overlap and time-split tests done; decision per T3 feature: model, business rule only, or wait for archive history (D2); E5 and E6 run |
| G3 (before NBA 3.1 freeze) | Final Veeva block chosen; feature dictionary written; licence and compliance answers received (X3); fresh load used or its absence accepted (X2); dictionary reviewed (X5); business lists and action hints reviewed with brand, Field Analytics and Medical Affairs |

## 8. Decisions and open questions

### 8.1 Proposed decisions

| # | Decision | Proposal |
| --- | --- | --- |
| D1 | Spine and key | Claims HCP Universe, joined on NPI; Veeva never filters the universe |
| D2 | T3 scores in NBA 3.1 | Default: business rules and segmentation only; into the model only if E6 passes and R2 shows they are not a copy of claims volume. Full time-valid use from the archive in NBA 3.2 |
| D3 | Bayer payments | Keep internal speaker data in the personal block; in Veeva, use a separate Bayer flag only, and test competitor payments separately |
| D4 | Missing values | Three-state coverage flag (principle 2) |
| D5 | Indication | Kerendia total plus HF / T1D / CKD views, same rule as the digital plan |
| D6 | Feature prefix | `veeva_` for all features |
| D7 | Colocation, IDN and Veeva | Separate blocks on the same spine. The cross features (R5) live in the Veeva T3 table and reuse the colocation L1 / L4 keys; the IDN peer writer share stays in the colocation notebook (section 5.2) |

### 8.2 Open questions

| # | Question | Proposed answer | Owner |
| --- | --- | --- | --- |
| Q1 | Does our Veeva Link licence allow commercial use in the NBA (model features and rep-facing hints), or Medical Affairs use only? | To confirm before G0 | Vendor Management, Legal |
| Q2 | Can CMS Open Payments and competitor-payment features be used for commercial targeting? | To confirm with Compliance; until then payment features are model-only, not shown to reps | Compliance |
| Q3 | When is the next aligned load, and can we get monthly loads? | Ask Veeva and Data Engineering | Data Engineering, Vendor Management |
| Q4 | Can Veeva provide historical score snapshots or the changelog (`SCIENTIFIC_EXPERT_CHANGELOG`)? | Ask; would make T3 time-valid for NBA 3.1 | Vendor Management |
| Q5 | Is `COMPANY_COLLABORATION` in our subscription? | Ask; empty today | Vendor Management |
| Q6 | What exactly does `CLINICAL_LEADER` measure (data source of "patient volume") and `DIGITAL_REACH` (channels)? | Ask Veeva; needed for R2 | NBA team with Veeva |
| Q7 | Which focus names and keywords define "Kerendia-relevant"? | v2 lists as starting point; review with Medical and brand | Medical Affairs, brand |
| Q8 | Can the 65,795 unmatched providers be recovered through `VEEVA_ID` / Veeva Network? | Test; expected small gain | NBA team |
| Q9 | Who reviews the untargeted-authority list (B1) and how often? | Brand and sales operations, quarterly with the call plan | Brand, sales operations |
| Q10 | Does NBA 3.0 already use any Veeva Link or KOL attribute? | Check the NBA 3.0 final feature list | NBA team |
| Q11 | Which rule defines writers and the new-writer view? | **Closed** (user, 2026-11-18): KER-10 `active_nbrx_writers` in `kerendia_metric_views.mv_kerendia_nbrx`; new writers = not counted by KER-10 in the look-back. Same rule as colocation plan D8 | NBA team |

## 9. Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| Look-ahead bias from T3 scores | Model looks better in validation than in use | Leakage tiers, E3 vs E2, E6, D2 |
| Stale data at inference (data cut-off March 2025) | Activity features under-count recent activity; new experts look inactive | X2, O2; windows end at the data cut-off (U7) |
| Decile overlaps claims volume | No new information, or indirect target leakage | R2 |
| Signal already in the call-plan segment | Little added value | R4; report gain within segment |
| Licence or compliance blocks rep-facing use | Phase 3 cannot ship | X3 asked in week 1; model-only fallback |
| Load-to-load changes in focus names | Schema drift | U4, U7, O3 |
| Building on old data, then the refresh changes results | Feature selection redone | Same code re-runs on the refresh (U1, U7); repeat E3 to E5 only |
| Cross features driven by group size | Expert-colleague flags act as a practice-size proxy | Use shares, not flags, at IDN level; test the practice flag only with practice size in the model (section 5.2) |
