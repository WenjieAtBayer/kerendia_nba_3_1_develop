# Veeva Link Key People for NBA 3.1: all plans in one file

This file joins the master readiness plan and the five phase working plans. The text is unchanged; only every heading is one level lower so the parts nest under this title. Notebook names inside the plans are the original ones (`52_` ... `99_`); `00_README.md` maps them to the new notebooks.

| Part | Content | Original file | Notebook |
| --- | --- | --- | --- |
| Part 0 | Master readiness plan (phases 0 to 4, gates, risks) | `50_veeva_link_nba_3_1_readiness_plan.md` | all |
| Part 1 | Phase 0 working plan: data foundation | `51_veeva_link_phase0_working_plan.md` | `10_phase0_data_foundation` |
| Part 2 | Phase 1 working plan: T1 / T2 features | `70_veeva_link_phase1_working_plan.md` | `20_phase1_t1_t2_features` |
| Part 3 | Phase 2 working plan: T3 scores and tests | `80_veeva_link_phase2_working_plan.md` | `30_phase2_t3_features_and_tests` |
| Part 4 | Phase 3 working plan: business use | `90_veeva_link_phase3_working_plan.md` | `40_phase3_business_outputs` |
| Part 5 | Phase 4 working plan: operations | `95_veeva_link_phase4_working_plan.md` | `50_phase4_operations` |

---

# Part 0: Master readiness plan (phases 0 to 4, gates, risks)

*Original file: `50_veeva_link_nba_3_1_readiness_plan.md`*

## Veeva Link Key People: NBA 3.1 Readiness Plan

**Group:** HCP influence and scientific activity (new feature block for NBA 3.1)  
**Purpose:** a step-by-step plan to turn Veeva Link Key People ("Veeva Link to People") data into a clean, leakage-safe and tested feature block for the NBA 3.1 HCP-level model, and into business inputs for the NBA list  
**Builds on:** files 10 to 40 in this folder (see `00_README_folder_guide.md`), mainly `40_veeva_link_data_assessment_v2.md` (sections 1 to 11), `33_veeva_link_feature_engineering_plan.md` (66 planned features) and `11_veeva_link_data_sources_and_feature_feasibility` (feasibility of 56 catalog features and a 153-feature pilot on 100 HCPs)  
**Same structure as:** `04_Promotional_Features/non_personal_promotional_features/13_hcp_digital_nba_3_1_readiness_plan.md` and `50_digital_nba_3_1_readiness_plan.md`, and `personal_promotional_features/40_field_activity_nba_3_1_readiness_plan.md`  
**Source:** Snowflake `CPH_DB_PROD.ANALYTICS_V2.ANLT_VEEVA_LINK_*` (17 tables)  
**Status:** draft for discussion  
**Date:** November 18, 2026

---

### 1. Scope

| In scope | Out of scope (owned elsewhere) |
| --- | --- |
| **Coverage flags**: has a Veeva profile, has a Kerendia-relevant decile | Bayer speaker programmes and Bayer events (personal block, `personal_promotional_features/14_speaker_programs_nba_3_0.md`); Veeva Link only adds **external** activity |
| **Influence rankings**: `CLINICAL_LEADER`, `FOCUS_AREA`, `DIGITAL_REACH_FOCUS_AREA`, `INDEX` | Bayer MSL interactions (personal block, MSL flag MD-1 in `40_...`) |
| **Clinical-trial experience**: `SCIENTIFIC_EXPERT_CLINICAL_TRIAL` + `CLINICAL_TRIAL` | Prescribing behaviour (claims blocks; Veeva is not a prescriber database) |
| **Scientific and congress activity**: publications, events | HCP specialty as a primary attribute (HCP Universe / NPPES); Veeva specialty is a fallback only |
| **Industry relationships**: `PAYMENT` (CMS Open Payments), `COMPANY_SPONSORSHIP` | Non-US experts (12.5% of Veeva; no NPI) |
| **Profile**: expert type, degree, academic affiliation, associations | `COMPANY_COLLABORATION` (empty), `COMMUNITY_LEADER_FOCUS_AREA` (deprecated), `SCIENTIFIC_EXPERT_CHANGELOG` and `SCIREACH_MAPPING` (not in the warehouse) |
| **Business use in the NBA**: untargeted authorities and channel hints | Changing the call plan itself (brand / sales operations decision) |

### 2. Goal and how we will judge success

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

### 3. Starting point

#### 3.1 What we know about the data (assessment v2)

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

#### 3.2 What has been built so far

| Asset | State | Gap for NBA 3.1 |
| --- | --- | --- |
| `33_veeva_link_feature_engineering_plan.md` | 66 features in 13 tables, leakage tiers, naming `veeva_` | Written before v2: uses High / Medium / Low tiers and the narrow focus list (34.8% scored vs 64.4% in v2); target described as T1D / T2D / HTN NBRx |
| `11_veeva_link_data_sources_and_feature_feasibility` notebook | Feasibility of 56 catalog features (36 ready, 12 with caveat, 4 substitute, 1 external, 2 not feasible); 153-feature pilot on 100 HCPs | Pilot keyed on `SE_ID`, not the HCP Universe spine; disease deciles in section B partly read from deprecated `COMMUNITY_LEADER_FOCUS_AREA`; composites z-scored on 100 HCPs; `DIGITAL_REACH` matched 1 of 100 (ID format, "CG"-prefixed IDs) |
| `22_veeva_link_focus_name_taxonomy.csv` and assessment section 5.3 | Curated Kerendia-relevant focus names: 17 `CLINICAL_LEADER`, 147 `FOCUS_AREA`, 135 `DIGITAL_REACH` | Not yet a config table; three different scoping methods in use (v2 lists, pilot regex, EDA regex) |
| `30_veeva_link_kol_identification_and_activity_eda`, `31_veeva_kol_list.csv`, `32_veeva_hcp_decile_segments.csv` | KOL lists and decile segments | One-off extracts, not a pipeline |

NBA 3.0 has no Veeva Link feature block (to confirm against the NBA 3.0 final feature list).

### 4. Design principles for NBA 3.1

1. **Claims HCP Universe is the spine.** HCP Universe (`PROVIDER_ID`) to `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING` (NPI, BH_ID) to `SCIENTIFIC_EXPERT.NPI` (US, not deleted) to child tables on `SE_ID`. Every HCP keeps a row.
2. **Three-state coverage, never silent zeros.** `veeva_coverage_status` = `NOT_IN_VEEVA` / `IN_VEEVA_UNSCORED` / `SCORED`. Count features are 0 only for HCPs in Veeva; for HCPs not in Veeva they stay null (or 0 plus the flag, depending on the model library).
3. **Leakage tier on every feature.**
   * **T1 (low)**: dated activity (trials, publications, events, payments). Windowed relative to the anchor month.
   * **T2 (medium)**: slow-moving profile (expert type, degree, academic affiliation, associations, sponsorship). Used as static attributes.
   * **T3 (high)**: vendor scores (`CLINICAL_LEADER`, `FOCUS_AREA`, `DIGITAL_REACH`, `INDEX`). Today's view only; used only if they pass E6, otherwise kept for business rules.
4. **Windows respect the data cut-off.** For T1 features, the window ends at the earlier of the anchor month and the table's data cut-off (`veeva_data_cutoff`, today 2025-03-06). Windows are fixed (3 and 5 years), not running. A `veeva_data_age_months` value is logged per run (not a model feature) so stale loads are visible.
5. **One focus-name dictionary.** The v2 curated lists (section 5.3 of the assessment) become a config table: table, `FOCUS_NAME`, theme (Kerendia / MRA, SGLT2, GLP-1, DPP-4, other T2D, ACE / ARB, hyperkalemia, hypertension, CKD, heart failure, T2D, T1D, diabetes general, cardiometabolic), indication (HF / T1D / CKD / other). Free-text scoping of trial, publication and event names uses one keyword list (feature plan section 7) with `ILIKE`, never `REGEXP_LIKE` through the Spark connector.
6. **Indication as a dimension.** Same rule as the digital plan: keep the Kerendia total and add HF, T1D and CKD views where the data supports it (deciles and trials), not as filters.
7. **Few, meaningful features.** Build a candidate set of about 60 to 80 columns from the 153 pilot features and 66 planned features, then select down (target 15 to 30 in the model). Prefer flags, log counts and bins.
8. **No double counting with internal data.** Bayer speaker programmes and MSL contacts stay in the personal block; Veeva payment features exclude Bayer or keep Bayer as a separate flag only (decision D3).
9. **Language.** Describe the NBA output as the NBA dropdown list; Veeva rankings are "influence" or "authority", not "KOL status" unless Medical Affairs confirms the definition.

### 5. Work plan

The work is split into phases. Each phase ends with a gate (section 7).

#### Phase 0, optimized: unblock the feature build

**Problem with the first draft.** Phase 0 mixed in-house tasks with tasks that depend on other teams (Veeva refresh, archive history, licence, compliance, Medical review). Treated as one blocking phase, feature building would wait weeks for answers that do not change the build itself. The data we have today (the 2025-03 / 2025-06 snapshot) is enough to build, test and select features; a refresh only changes the input rows, not the code.

**Principle.** Split Phase 0 into two parallel tracks. **Track U (unblock)** is in-house, starts now and is the only thing that blocks Phase 1. **Track X (external)** runs at the same time and gates only production release, rep-facing use and T3 scores, not the build.

##### 0.1 Blockers and how each is removed

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

##### 0.2 Track U: in-house, blocks Phase 1 (target: about 2 weeks, an estimate)

| ID | Task | Detail | Done when |
| --- | --- | --- | --- |
| U1 | Freeze the snapshot in Delta | One-time copy of the 15 in-use `ANLT_VEEVA_LINK_*` tables (all except the empty `COMPANY_COLLABORATION` and the deprecated `COMMUNITY_LEADER_FOCUS_AREA`) to `kerendia_nba_3` as `veeva_link_<table>_snapshot`, with standard filters applied once (`IS_LATEST_FLAG = 'Y'`, `COALESCE(SYS_DELETE_FLAG, 0) = 0`, `ISDELETED` on `SCIENTIFIC_EXPERT`; `SYS_TENANT = 'US'` on person tables only, never on `PUBLICATION` / `CLINICAL_TRIAL` / `MEDICAL_EVENT`) and `load_date` / `src_load_id` columns. This is also archive point 1 | Row counts match assessment 1.4 for latest rows |
| U2 | Spine and mapping table | `veeva_npi_se_map`: HCP Universe `PROVIDER_ID` to `SOURCE_PROVIDER_BHID_NPI_MAPPING` (NPI, BH_ID) to `SE_ID`, with match route; handle the 2 providers that share an `SE_ID` | 228,932 matched of 294,727 (77.7%) |
| U3 | Long activity tables | One row per expert x item with date and role, for the matched experts only: trials (`SE_ID`, trial, role, phase, start, end, in-scope tags), publications (author position, date, type, tags), events (position, start date, tags), payments (program year, nature, type, company, amount). Profile and score tables stay one row per expert or expert x focus name | Totals match assessment 8.1 (358,601 publications, 54,673 trials, 152,510 events) |
| U4 | Config tables v1 | (a) Focus-name dictionary from assessment 5.3 (17 / 147 / 135 names, theme, indication) plus `22_veeva_link_focus_name_taxonomy.csv`; (b) free-text keyword list from `33_...` section 7 with a talk-title stop-list; (c) window list (3 and 5 years) | Best-decile coverage reproduces 147,489 (64.4%) |
| U5 | Data-quality rules in the copy step | Drop column-shifted `EVENT_TYPE` rows; ignore `PAST_POSITION`; drop orphan `ADDRESS` rows; normalise `PUBLICATION_TYPE`; `LPAD` ZIP; hardcode the 0 to 4 Scientific Reach lookup; keep 0 to 10 and 0 to 4 indices apart. Only rules that touch planned features; the rest are logged | DQ log written per run |
| U6 | Pilot code fixes | Move disease deciles off `COMMUNITY_LEADER_FOCUS_AREA` to `CLINICAL_LEADER` and `FOCUS_AREA`; standardise composites on the full universe; one-day time-box for the `DIGITAL_REACH` ID check | Pilot sections A to K run on the spine |
| U7 | As-of rule and fixed schema | T1 windows end at min(anchor month, table data cut-off); cut-off stored per table from U1; output columns generated from U4 and filled per principle 2 | Same columns on two consecutive runs |
| U8 | Acceptance checks | One notebook that re-computes the assessment's key numbers from the Delta copy (U1 counts, U2 match 77.7% / 83.2% for A to E, U4 coverage 64.4%, segment by decile table 7.2) and fails if any is more than 1 point off | All checks pass |

Suggested order: U1 and U4 in parallel (days 1 to 3), then U2 and U5, then U3 and U6, then U7 and U8. U8 is the entry ticket to Phase 1.

##### 0.3 Track X: external, in parallel (gates release, not the build)

| ID | Task | Gates | Owner |
| --- | --- | --- | --- |
| X1 | Monthly archive job, reusing U1 code, with row-count and match-rate checks | T3 in NBA 3.2 | Data Engineering + NBA team |
| X2 | Fresh, aligned load and refresh cadence (hub 2025-06-25, children 2025-03-06) | Production release (G3) | Data Engineering, Vendor Management |
| X3 | Licence and compliance answers (Q1, Q2), asked in week 1 | Production release and Phase 3 rep-facing use | Vendor Management, Legal, Compliance |
| X4 | Veeva questions: history or changelog (Q4), `COMPANY_COLLABORATION` (Q5), what `CLINICAL_LEADER` and `DIGITAL_REACH` measure (Q6) | T3 decision (G2) | Vendor Management, NBA team |
| X5 | Medical / brand review of dictionary v1 (Q7) | Final block (G3) | Medical Affairs, brand |

#### 5.1 Candidate feature list, first version

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

#### 5.2 Combined colocation, IDN and Veeva features: signal test (2026-11-18)

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

#### Phase 1: T1 and T2 block (low risk)

| ID | Task | Detail | Dependency |
| --- | --- | --- | --- |
| P1 | Build coverage flags | Three-state status on the full HCP Universe | U2 |
| P2 | Build T1 activity features | Trials, publications, events, payments with 3- and 5-year windows ending at min(anchor, data cut-off); PI role, senior author, podium role; in-scope versions from U4 | U3, U4, U7 |
| P3 | Build T2 profile features | Expert type, degree, academic affiliation, associations, sponsorship; Veeva specialty only where HCP Universe specialty is missing | U1, U5 |
| P4 | Move pilot to production | Turn the pilot build (sections A to K of `11_veeva_link_data_sources_and_feature_feasibility`) into a feature notebook keyed on the spine, all 294,727 HCPs; drop features constant on the full population | P1 to P3, U6 |
| P5 | Spot-check | Compare 10 known HCPs (from `31_veeva_kol_list.csv`) against their Veeva Link web profiles | P4 |

#### Phase 2: T3 scores and leakage tests

| ID | Task | Detail | Dependency |
| --- | --- | --- | --- |
| R1 | Build T3 features | Best decile and per-theme deciles from `CLINICAL_LEADER` (disease and drug class), `FOCUS_AREA`, `DIGITAL_REACH`; `INDEX` pivot (4 indices on 0 to 10; Scientific Reach separate). Written to a separate table read only by E5 / E6 | U4, U6 |
| R2 | Prescribing-overlap test | `CLINICAL_LEADER` ranks patient volume. Correlate the MRA-class, SGLT2-class and CKD deciles with claims volume and Kerendia NBRx features already in the model; if a decile is a near copy of claims volume, drop it | R1, NBA 3.1 claims block |
| R3 | Time-split test | Train on anchors before the score date and test on anchors after; compare with the same model without T3 (E6) | R1 |
| R4 | Segment added-value test | Within each call-plan segment A to E, check that decile still separates NBRx (as it separates trial involvement in assessment 8.3) | R1 |
| R5 | Build cross features | `veeva_idn_expert_share` + zero flag, and `veeva_practice_expert_peer_flag`, from the colocation L1 / L4 keys, self excluded; written to the T3 table (section 5.2) | R1, colocation L1 / L4 keys |

#### Phase 3: Business use in the NBA

| ID | Task | Detail |
| --- | --- | --- |
| B1 | Untargeted-authority list | Share the 18,209 Non-target HCPs at deciles 8 to 10 (10,113 at 9 to 10) with brand and sales operations for target-list review, split by specialty and indication |
| B2 | Action hints | Map activity type to the NBA reason or channel: podium speakers to peer-to-peer or speaker programme invitation, trial investigators to clinical-evidence messaging, MRA / SGLT2 class authorities to cardiorenal messaging. Business rules on the NBA dropdown list, not model features |
| B3 | Field review | Review hints and lists with Field Analytics and Medical Affairs before any rep-facing use |
| B4 | Low-adoption IDN expert list | 19,252 non-writing experts in 2,524 IDNs with a peer writer share of 5% or less (10,790 Non-target), by IDN, specialty and segment, for brand and key account teams (section 5.2, idea 3) |

#### Phase 4: Operations

| ID | Task | Detail |
| --- | --- | --- |
| O1 | Monthly archive job | Production version of X1 |
| O2 | Freshness check | Each run logs data cut-off per table and data age; warn if a child table is more than 6 months older than the hub or more than 12 months old |
| O3 | Dictionary upkeep | Monthly report of new focus names and new unmapped keyword hits |
| O4 | Documentation | Final feature dictionary with business descriptions in this folder, same style as the digital and field documents |

### 6. Model experiments

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

### 7. Readiness gates

| Gate | Ready when |
| --- | --- |
| G0 (after Track U; entry to Phase 1) | Snapshot frozen in Delta (U1); acceptance checks pass (U8, S2); config tables v1 loaded (U4); fixed schema on two runs (U7); Track X requests sent (X1 to X5). Track X answers are **not** needed for G0 |
| G1 (after Phase 1) | T1 and T2 block built for all training instances; leakage check passed (no event after the anchor); fixed schema on two runs; spot-check done; E1 to E4 run and compared with E0 |
| G2 (after Phase 2) | Prescribing-overlap and time-split tests done; decision per T3 feature: model, business rule only, or wait for archive history (D2); E5 and E6 run |
| G3 (before NBA 3.1 freeze) | Final Veeva block chosen; feature dictionary written; licence and compliance answers received (X3); fresh load used or its absence accepted (X2); dictionary reviewed (X5); business lists and action hints reviewed with brand, Field Analytics and Medical Affairs |

### 8. Decisions and open questions

#### 8.1 Proposed decisions

| # | Decision | Proposal |
| --- | --- | --- |
| D1 | Spine and key | Claims HCP Universe, joined on NPI; Veeva never filters the universe |
| D2 | T3 scores in NBA 3.1 | Default: business rules and segmentation only; into the model only if E6 passes and R2 shows they are not a copy of claims volume. Full time-valid use from the archive in NBA 3.2 |
| D3 | Bayer payments | Keep internal speaker data in the personal block; in Veeva, use a separate Bayer flag only, and test competitor payments separately |
| D4 | Missing values | Three-state coverage flag (principle 2) |
| D5 | Indication | Kerendia total plus HF / T1D / CKD views, same rule as the digital plan |
| D6 | Feature prefix | `veeva_` for all features |
| D7 | Colocation, IDN and Veeva | Separate blocks on the same spine. The cross features (R5) live in the Veeva T3 table and reuse the colocation L1 / L4 keys; the IDN peer writer share stays in the colocation notebook (section 5.2) |

#### 8.2 Open questions

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

### 9. Risks

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

---

# Part 1: Phase 0 working plan: data foundation

*Original file: `51_veeva_link_phase0_working_plan.md`*

## Veeva Link Key People: Phase 0 Working Plan (Track U and Track X)

**Parent plan:** `50_veeva_link_nba_3_1_readiness_plan.md`, section 5, Phase 0  
**Data reference:** `40_veeva_link_data_assessment_v2.md`  
**Goal:** pass gate G0 (entry to Phase 1) with a frozen, tested Veeva snapshot and config, without waiting on external teams  
**Status:** Track U done on 2026-11-19; acceptance run `20261119T103159` passes 21 of 21 (see section 8). Track X requests still to send  
**Date:** November 19, 2026

---

### 1. Decisions for Phase 0

| # | Decision | Detail |
| --- | --- | --- |
| P0-D1 | **Source** | Snowflake `CPH_DB_PROD.ANALYTICS_V2.ANLT_VEEVA_LINK_*` through the Spark Snowflake connector (secret scope `US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`, role `BAY_CPH_CDP_PROD_CR_US_EAST_1_MVXPF_MVXPF`, warehouse `PROD_CYRUS_BI_WH`). Not the Unity Catalog copy `cph_db_prod.analytics_v2` |
| P0-D2 | **Verification** | Acceptance numbers are re-computed against the Snowflake tables as well as against the copy (two independent routes) |
| P0-D3 | **Storage** | Parquet files (not Delta tables for now) under `OUT = /Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/veeva_link_to_people/` |
| P0-D4 | **Push down, then land** | Filters (latest, not deleted, tenant) and column selection run inside Snowflake in the connector `query`. All joins and free-text matching run in Spark on the parquet copy, so the `REGEXP_LIKE` connector trap does not apply |

Checked on 2026-11-19: the Snowflake connector works from serverless; the output folder exists, is empty and is writable (parquet write, read and delete test passed).

### 2. New facts found while preparing this plan (2026-11-19)

Profiled in Snowflake with one count per table (total rows, latest rows, latest and not deleted, latest and not deleted and US).

#### 2.1 Assessment 1.4 counts are latest rows across all tenants

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

#### 2.2 Correction to assessment 1.5 (1): the raw tables do keep load history

* Assessment 1.5 (1) says `IS_LATEST_FLAG = 'Y'` on 100% of rows. That is true only after the latest filter. The raw tables keep **weekly full loads from 2024-06-27 to 2025-03-06** (33 to 41 `LOAD_ID`s per table; about 90M rows per load for `CLINICAL_LEADER`). `SCIENTIFIC_EXPERT` has 7 loads, 2025-06-25 to 2025-06-30.
* Latest rows come almost entirely from the last load (90,852,830 of 91,060,114 `CLINICAL_LEADER` latest rows are from load 2025-03-06). About 207K latest rows sit in older loads (rows not present in later loads); they are kept, to match the assessment, and counted in the DQ log.
* Scores barely move between loads: for `CLINICAL_LEADER` 'Type 2 Diabetes Mellitus', 73,840 of 73,842 US experts present in both the 2024-08-01 and 2025-03-06 loads have the same decile.
* **What it changes:** Q4 (history) is partly answered: about 9 months of weekly history exist, all before the data cut-off. They do not make T3 time-valid for 2025 to 2026 anchors, and the scores are close to static, so D2 stays as it is. The history is still useful for a stability check of T3 (Phase 2) and as the first archive points (X1). Section 1.5 (1) of the assessment should be corrected.

### 3. Output layout (parquet)

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

### 4. Track U: tasks, notebooks and checks

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

#### 4.1 Acceptance checks (U8)

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

### 5. Track X: send in week 1 (does not block G0)

| ID | Request | To | Note from section 2 |
| --- | --- | --- | --- |
| X1 | Monthly archive job reusing `52_` | Data Engineering, NBA team | The weekly loads already in Snowflake (2024-06 to 2025-03) can be copied as the first archive points |
| X2 | Fresh, aligned load and refresh cadence (Q3) | Data Engineering, Vendor Management | Hub 2025-06-30, children 2025-03-06; no load since |
| X3 | Licence and compliance (Q1, Q2) | Vendor Management, Legal, Compliance | Features stay model-only until answered |
| X4 | Changelog (Q4), `COMPANY_COLLABORATION` (Q5), what `CLINICAL_LEADER` and `DIGITAL_REACH` measure (Q6) | Vendor Management | Q4 narrowed: ask for loads after 2025-03 and for `SCIENTIFIC_EXPERT_CHANGELOG` (merges) |
| X5 | Review of dictionary v1 (Q7) | Medical Affairs, brand | Send the `53_` output |
| Q10 | Does NBA 3.0 use any Veeva or KOL attribute? | NBA team | Quick check against the NBA 3.0 feature list |

### 6. Gate G0 checklist

* [x] U1 snapshot written; A1 passes
* [x] U4 config v1 written; A5 passes
* [x] U2 spine written; A2 to A4 pass
* [x] U3 activity tables written; A7 passes
* [x] U6 candidate features run on the spine (as a new notebook, see section 8.2)
* [x] U7 fixed schema; A8 passes
* [x] U8 acceptance table: all checks pass, on both the Spark and Snowflake routes
* [ ] X1 to X5 requests sent (answers not needed)
* [ ] Assessment section 1.5 (1) corrected (section 2.2 here)

### 7. Risks for Phase 0

| Risk | Mitigation |
| --- | --- |
| Connector time-outs on `FOCUS_AREA` (147M US rows) and `PAYMENT` (109M) | Read in chunks; select only needed columns; write each chunk to parquet |
| Snowflake and parquet counts differ because of types (`SE_ID` mixed formats, text dates) | Cast `SE_ID::VARCHAR` and parse dates in the pushdown query; A1 compares both routes |
| Old-load latest rows (about 207K in `CLINICAL_LEADER`) change counts if excluded | Keep them (matches the assessment); count them in the DQ log |
| A refresh lands during Phase 0 | New `load=` folder; re-run 52 to 57; acceptance values for A1 move to the new baseline |

### 8. Results (2026-11-19)

#### 8.1 Acceptance run `acceptance/run=20261119T103159` (notebook `57_`)

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

#### 8.2 Notes by notebook

* **52** (U1, U5): DQ log `dq_log/run=20261119T100328/`. R1 shifted `EVENT_TYPE` = 45 rows (0.007%, not about 0.3%); R3 orphan US `ADDRESS` = 219,567; R4 normalised publication types = 891,954; R7 `CLINICAL_LEADER` latest rows from older loads = 206,914 (kept).
* **53** (U4): `focus_dictionary_v1` 299 rows (17 / 147 / 135, all found in the snapshot); `keyword_list_v1` 86 patterns in 12 tags; stop-list 12 rows (64,847 of 3,829,146 talk titles hit); `windows_v1` 3 and 5 years. Fixed a parser bug that put the cardiorenal block under `ckd`.
* **54** (U2): `spine/veeva_npi_se_map/`, one row per `PROVIDER_ID`. Coverage: `SCORED` 147,487, `IN_VEEVA_UNSCORED` 81,443, `NOT_IN_VEEVA` 65,797 (65,623 NPI not in Veeva, 174 no NPI in crosswalk). 2 `SE_ID`s shared by 4 providers, flagged. No NPI maps to more than one `SE_ID`.
* **55** (U3): `activity/{trials,publications,events,payments}/`. Publication dates run from 2019 to 2025 (2019: 25,097 rows; 2025: 11,652), wider than the 2020 to 2024 in the assessment. 59 trial links and 39 event links have no dimension row.
* **56** (U6, U7), deviation: built as a new notebook `56_veeva_link_features_on_spine`, not a copy of `11_` sections A to K. It produces the section 5.1 candidates for all 294,727 HCPs: `features/t1_t2/anchor=<A>/` (29 T1 + 13 T2) and `features/t3/anchor=<A>/` (16 T3, for E5 and E6 only), schema in `config/feature_schema_v1`. Run for anchors 2025-10-23 and 2024-06-30. The `DIGITAL_REACH` ID problem of the pilot does not occur on string `SE_ID` (4,710 scored), so `DIGITAL_REACH` stays in v1. `PAYMENT.AMOUNT` is text in the snapshot and is cast in `56_`.
* **57** (U8): as in 8.1.

#### 8.3 Still open for G0

* X1 to X5 requests and Q10 not sent yet.
* Assessment section 1.5 (1) correction: deferred (user, 2026-11-19); section 2.2 here is the reference until then.

---

# Part 2: Phase 1 working plan: T1 / T2 features

*Original file: `70_veeva_link_phase1_working_plan.md`*

## Veeva Link Key People: Phase 1 Working Plan (T1 and T2 block)

**Parent plan:** `50_veeva_link_nba_3_1_readiness_plan.md`, section 5, Phase 1 (P1 to P5), section 6 (E0 to E4), gate G1  
**Builds on:** Phase 0 (`51_veeva_link_phase0_working_plan.md`; notebooks `52_` to `57_`; acceptance run `20261119T103159`, 21 of 21 pass)  
**Goal:** pass gate G1: T1 and T2 block built for all training instances, leakage check passed, fixed schema on two runs, spot-check done, E1 to E4 run and compared with E0  
**Status:** in progress: P1, P2, P4 done; keyword_list_v2 applied (run `20261123T085209`); P3 and P5 manual review open; E0 to E4 waiting on I1 / I4  
**Date:** November 19, 2026 (last update November 23, 2026)

---

### 1. Starting point

| Already done in Phase 0 | Where |
| --- | --- |
| Frozen snapshot (15 tables), DQ rules, config v1 (dictionary, keywords, stop-list, windows) | `OUT/snapshot/load=2025-06-30/`, `OUT/config/` |
| Spine `PROVIDER_ID` to `SE_ID`, three-state coverage | `OUT/spine/veeva_npi_se_map/` |
| Long, dated activity tables | `OUT/activity/{trials,publications,events,payments}/` |
| Candidate features for 2 test anchors: 29 T1 + 13 T2 (`t1_t2`), 16 T3 (`t3`), schema `config/feature_schema_v1` | `56_veeva_link_features_on_spine`, `OUT/features/` |

`56_` already covers most of P1 to P4 for single anchor dates. Phase 1 turns it into the **NBA 3.1 grain** and adds the missing pieces, the checks and the experiments.

`OUT = /Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/veeva_link_to_people/`

### 2. New facts found while preparing this plan (2026-11-19)

#### 2.1 Grain of the NBA 3.1 model

The NBA 3.1 HCP features are keyed on **`NPI_NUMBER` x `COHORT_ID`** (`YYYY-MM_offset7`). Cohorts C1 to C22 = 2025-01 to 2026-10; cohort cut-off = month end + 6 days; windows end at the cut-off (inclusive) and start `w` months earlier (exclusive). NBA 3.0 cohorts C01 to C26 have anchors 2023-04 to 2025-05. (Read from `51_digital_nba_phase1_features`, which mirrors `00_cohort_config`; `00_cohort_config` itself is not readable from this account, so the rules must be confirmed there.)

#### 2.2 Most NBA 3.1 cohorts see the same Veeva data

The Veeva child-table cut-off is 2025-03-06. Cohort C1 (2025-01) ends 2025-02-06; **C2 (2025-02) ends exactly on 2025-03-06**, and every later cohort ends after it. So:

* For C2 to C22, every T1 window is capped at 2025-03-06: **T1 values are the same for 21 of 22 cohorts**. Only C1 differs, by one month.
* Payment program years are 2021 to 2023 for every NBA 3.1 cohort (program year 2024 is not in the data).
* Inside NBA 3.1 cohorts, T1 behaves like a static attribute. **E2 (static totals) and E3 (windowed) will be almost the same on C1 to C22**, so the E2 vs E3 leakage test (section 6 of `50_`) only works on anchors before the cut-off, that is the NBA 3.0 cohorts (C01 to C26, 2023-04 to 2025-05).
* For inference cohorts (2026) the newest Veeva activity is 20+ months old (risk R1 below).

#### 2.3 Spine and grain checks

* 11 NPIs sit on more than one `PROVIDER_ID` in the crosswalk; 174 providers have no NPI. At NPI grain these need a rule (task P1.2).
* The HCP Universe parquet holds only `PROVIDER_ID` and `C1_FLAG` to `C5_FLAG`, **no specialty**. The Veeva-specialty fallback of P3 needs the NBA 3.1 specialty source (open input I3). Veeva `SPECIALTY_1` is filled for 148,034 of 228,928 matched experts.
* Publication dates start in 2019. For NBA 3.0 anchors before 2024-01 the 5-year publication window is cut on the left (only data from 2019 onward).

### 3. Decisions for Phase 1

| # | Decision | Detail |
| --- | --- | --- |
| P1-D1 | **Grain** | `NPI_NUMBER` x `COHORT_ID`, the same as the NBA 3.1 HCP claims features; cohort helpers copied from `00_cohort_config` with its self-test |
| P1-D2 | **Cohort lists** | NBA 3.1 C1 to C22 (model); NBA 3.0 C01 to C26 (leakage test E2 vs E3 only). Both from one cohort config parameter |
| P1-D3 | **Storage** | Parquet partitioned by `COHORT_ID` under `OUT/features_phase1/` (same as P0-D3). A switch to Delta is one line if the model pipeline needs it |
| P1-D4 | **T3 stays out** | The T3 table from `56_` is not joined to any Phase 1 output; it is read only in Phase 2 (D2) |
| P1-D5 | **Indication views** | Add HF, CKD and T1D in-scope counts for trials, publications and events (D5); Kerendia total stays the main view |
| P1-D6 | **Static variant** | For E2, build the same T1 columns from the full snapshot (no window), suffix `_all` instead of `_3y` / `_5y`, in a separate table |

### 4. Output layout

| Path | Content | Written by |
| --- | --- | --- |
| `features_phase1/t1_t2/COHORT_ID=<id>/` | One row per NPI x cohort: keys, coverage flags, T1, T2, `veeva_snapshot_id`, `veeva_window_end` | P4 |
| `features_phase1/t1_static/` | E2 static T1 totals, one row per NPI | P2 |
| `features_phase1/feature_manifest/` | One row per feature: name, tier, family, rule, indication, used in E1 / E2 / E3 / E4, kept after constant check | P4 |
| `features_phase1/checks/run=<ts>/` | One row per check (section 5.2) | P4 |
| `features_phase1/spot_check/` | Profile cards for the 10 spot-check HCPs | P5 |
| `experiments/run=<ts>/` | One row per experiment x measure | E-tasks |

### 5. Tasks, notebooks and checks

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

#### 5.1 Feature list for Phase 1

Starts from the 42 columns of `config/feature_schema_v1` (`t1_t2` table) and adds:

| Family | Added columns | Tier |
| --- | --- | --- |
| Trials | `veeva_trial_n_inscope_{hf,ckd,t1d}_5y` | T1 |
| Publications | `veeva_pub_n_inscope_{hf,ckd,t1d}_5y` | T1 |
| Events | `veeva_event_n_inscope_{hf,ckd,t1d}_3y` | T1 |
| Profile | `veeva_specialty_fallback` | T2 |
| Data age (logged, not a feature) | `veeva_window_end`, `veeva_data_age_months` | n/a |

About 52 candidate columns in total, before the constant check. Feature selection to 15 to 30 happens inside E1 to E4 with the main model's method.

#### 5.2 Checks in `71_` (written to `features_phase1/checks/`)

| # | Check | Pass rule |
| --- | --- | --- |
| K1 | Grain | One row per `NPI_NUMBER` x `COHORT_ID`; NPI count per cohort equals the NBA 3.1 HCP claims features for the same cohort |
| K2 | Fixed schema | Columns and order equal the manifest on two consecutive runs |
| K3 | No look-ahead | For every cohort, the latest activity date used is on or before the window end; no payment program year after the publication rule |
| K4 | Missing is not zero | 0 non-null T1 / T2 values for `NOT_IN_VEEVA` |
| K5 | Reproduces Phase 0 | Cohort C2 values equal `56_` anchor 2025-10-23 for every common column |
| K6 | Cohort identity | Share of HCPs whose T1 values change between consecutive cohorts; expected 0 for C2 to C22 (section 2.2), non-zero for NBA 3.0 cohorts |
| K7 | Constant features | Features with one value on the full population are dropped and listed |

### 6. Experiments E0 to E4

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

### 7. Inputs needed from other teams

| # | Input | From | Needed for |
| --- | --- | --- | --- |
| I1 | NBA 3.1 model notebook, target table and validation split (E0) | NBA modelling team | E0 to E4 |
| I2 | Read access to `00_cohort_config` (and `00_cohort_generation`) to confirm the cohort rules | Notebook owner | P1.1 |
| I3 | NBA 3.1 HCP specialty source | NBA team | P3 fallback |
| I4 | NBA 3.0 cohort feature table and target (C01 to C26) | NBA modelling team | E2 vs E3 leakage test |

If I1 or I4 are late, `71_` and `72_` still run; only the experiments wait.

### 8. Gate G1 checklist

* [x] P1 coverage flags at NPI x cohort grain (`71_`, 294,542 NPIs x 43 cohorts)
* [x] P2 T1 for C1 to C22 and C01 to C26, plus `t1_static` (23 window signatures)
* [ ] P3 T2 built; specialty fallback column kept but null, waiting on I3
* [x] P4 checks K1 to K7 pass (runs `20261119T113924` and `20261123T085209`); manifest written. K1 claims comparison not run (claims cohort output not readable)
* [ ] P5 spot-check: 10 cards built by `72_` (`OUT/features_phase1/spot_check/`), re-run on v2 features (same 10 HCPs, 0 card values changed); manual Veeva Link web review and mismatch notes still to do. Review template exported to `72_veeva_link_review_template.csv` (this folder) and `OUT/features_phase1/spot_check/review_template.csv`; fill in `web_matches`, `mismatch_note`, `reviewer`, `review_date`
  * MRA tag audit (2026-11-23): card 1's SZC trial is a real MRA-context hit (patients receiving spironolactone). A keyword screen for off-topic spironolactone uses (androgen excess, alopecia, transgender care, PAH) found trials 6 of 54 MRA rows, publications 4 of 407, events 1 of 138; the MRA flag flips for 4 / 4 / 1 experts. **Applied as `keyword_list_v2`** (section 10)
* [ ] E0 to E4 run and compared; E2 vs E3 on NBA 3.0 cohorts reported
* [x] Fixed schema on two runs (K2): run `20261123T085209` columns equal the schema lock of run `20261119T113924`

### 9. Risks for Phase 1

| # | Risk | Mitigation |
| --- | --- | --- |
| R1 | Stale data: T1 is the same for C2 to C22 and 20+ months old at 2026 inference | Report it as a static block; `veeva_data_age_months` logged; refresh (X2) is a re-run of `52_` to `71_` |
| R2 | E2 vs E3 cannot detect leakage on NBA 3.1 cohorts | Run the test on NBA 3.0 cohorts (I4) |
| R3 | Left-cut publication windows for anchors before 2024-01 (data from 2019) | Flag affected cohorts; compare with 3-year window in E3 |
| R4 | Payment features are the same for every NBA 3.1 cohort (program years 2021 to 2023) | Treat as static; check importance stability across folds |
| R5 | Cohort rules differ from `00_cohort_config` | Confirm with I2; self-test in P1.1 |
| R6 | Model inputs (I1) not available in time | Build and checks continue; experiments move, G1 waits |

### 10. Run log

#### 2026-11-23: keyword_list_v2 applied (`55_` -> `56_` -> `71_` -> `57_` -> `72_`)

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

---

# Part 3: Phase 2 working plan: T3 scores and tests

*Original file: `80_veeva_link_phase2_working_plan.md`*

## Veeva Link Key People: Phase 2 Working Plan (T3 scores and leakage tests)

**Parent plan:** `50_veeva_link_nba_3_1_readiness_plan.md`, section 5, Phase 2 (R1 to R5), section 6 (E5 to E7), gate G2, decision D2  
**Builds on:** Phase 0 (`51_`, notebooks `52_` to `57_`, acceptance run `20261123T085928`, 21 of 21 pass) and Phase 1 (`70_`, notebooks `71_` and `72_`, run `20261123T085209`, K1 to K7 pass, keyword_list_v2)  
**Goal:** pass gate G2: prescribing-overlap and time-split tests done; one decision per T3 feature (model, business rule only, or wait for archive history); E5 and E6 run (E7 if the cross features are built)  
**Status:** in progress. R0 (`81_`, run `20261123T092427`) and R1 (`82_`, run `20261123T093214`) done, all checks pass (section 10). Next: R5, R4 (I6, I7 now readable). R2 waits on I5; R3 and E5 to E7 wait on I1 / I4  
**Date:** November 23, 2026

---

### 1. Starting point

| Already done | Where |
| --- | --- |
| T3 candidate table for 2 test anchors, one row per `PROVIDER_ID` (294,727 rows), 16 columns | `56_veeva_link_features_on_spine`, `OUT/features/t3/anchor=<a>/` |
| T1 + T2 block at `NPI_NUMBER` x `COHORT_ID` (294,542 NPIs x 43 cohorts) | `71_`, `OUT/features_phase1/t1_t2/` |
| Focus-name dictionary v1 (17 `CLINICAL_LEADER` / 147 `FOCUS_AREA` / 135 `DIGITAL_REACH`) | `OUT/config/focus_dictionary_v1` |
| Colocation x Veeva signal test (one feature at a time, not model lift) | `60_veeva_colocation_idn_combined_signal_test`; `50_` section 5.2 |

`OUT = /Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/veeva_link_to_people/`

#### 1.1 Current T3 table (`56_`, anchor 2025-10-23, checked 2026-11-23)

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

### 2. New facts that shape Phase 2

#### 2.1 Where T3 is look-ahead and where it is not

The scores in the snapshot are the load of 2025-03-06 (child tables). The T3 risk in `50_` ("today's view only") depends on the cohort:

| Cohorts | Cut-off vs score load | T3 status |
| --- | --- | --- |
| NBA 3.1 C2 to C22 (2025-02 to 2026-10) | cut-off on or after 2025-03-06 | **Time-valid**: the 2025-03-06 scores were known at the anchor (stale, but not look-ahead) |
| NBA 3.1 C1 (2025-01), NBA 3.0 C15 to C23 (2024-06 to 2025-02) | cut-off 2024-07-06 to 2025-02-06 | Look-ahead with the snapshot, **but can be made time-valid** from the weekly loads kept in Snowflake (2.2) |
| NBA 3.0 C01 to C14 (2023-04 to 2024-05) | cut-off before the first kept load (2024-06-27) | Look-ahead; no history to fix it |

So for the NBA 3.1 model itself, the main T3 risk is **not look-ahead but overlap with prescribing volume** (`CLINICAL_LEADER` ranks patient volume, `50_` section 3.1): a decile that copies claims volume adds nothing, or leaks the target indirectly. R2 is the deciding test for NBA 3.1; R3 / E6 is the deciding test only where pre-score anchors are used (NBA 3.0 cohorts, or any training set that includes them).

#### 2.2 Score history in Snowflake

From the Phase 0 profile (2026-11-19, to re-check in R0): the raw `ANLT_VEEVA_LINK_*` tables keep weekly full loads from 2024-06-27 to 2025-03-06 (33 to 41 `LOAD_ID`s per table), so assessment 1.5 (1) "no history" is wrong for that period. Scores look almost static: the `CLINICAL_LEADER` T2D decile is the same for 73,840 of 73,842 experts from August 2024 to March 2025. Consequences:

* An **as-of T3** (latest load on or before the cohort cut-off) can be built for cohort months 2024-06 to 2025-02 (9 months). This is the archive history that D2 says to wait for, available now for a short period.
* If scores are this stable, snapshot T3 and as-of T3 will be nearly equal, and the time-split test will mostly measure **target drift**, not score leakage. R0 measures the stability per score family so E6 can be read correctly.

#### 2.3 Grain

The `56_` T3 table is keyed on `PROVIDER_ID` with one anchor. Phase 2 needs `NPI_NUMBER` x `COHORT_ID`, the same as `71_` (same NPI rule: 174 providers without NPI dropped; 11 NPIs on 2+ providers kept once, all share one `SE_ID`).

### 3. Decisions for Phase 2

| # | Decision | Detail |
| --- | --- | --- |
| P2-D1 | **Separate table** | T3 stays in `OUT/features_phase2/t3/COHORT_ID=<id>/`, never joined into `features_phase1/t1_t2/` (P1-D4, D2). Only E5 to E7 and the business lists read it |
| P2-D2 | **Two T3 versions** | `t3_snapshot` (2025-03-06 load for every cohort) and `t3_asof` (latest load on or before the cut-off; null before 2024-06-27). Same columns |
| P2-D3 | **Default use** | Business rules and segmentation only (D2) until R2 and E6 say otherwise for a given feature |
| P2-D4 | **Overlap rule (R2)** | A decile is a near copy of claims volume if Spearman rho >= 0.8 with any claims volume feature of the same theme, on matched scored HCPs at cohort C2. Near copies are dropped from the model. 0.5 to 0.8: keep only if it still separates the target within claims-volume deciles (R2.3) |
| P2-D5 | **Writer definition** | KER-10 `active_nbrx_writers` in `kerendia_metric_views.mv_kerendia_nbrx` (Q11, closed). Used in R4, R5 re-run and any direct target check |
| P2-D6 | **Expert flag for R5** | Best in-scope decile 8 to 10 from the T3 version that matches the cohort (as-of where available) |
| P2-D7 | **INDEX scales** | The four 0-to-10 indices and the 0-to-4 Scientific Reach stay separate columns; no combined index |

### 4. Output layout

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

### 5. Tasks, notebooks and checks

| Order | ID | Notebook | Work | Done when (check) |
| --- | --- | --- | --- | --- |
| Day 1 | R0 | `81_veeva_link_score_history` | Snowflake route: list `LOAD_ID` / load dates per score table (`CLINICAL_LEADER`, `FOCUS_AREA`, `DIGITAL_REACH_FOCUS_AREA`, `INDEX`) for US experts; per load, experts with an in-scope decile and share whose decile changed vs the previous load (filters pushed to Snowflake, P0-D4; no `REGEXP_LIKE`) | Load calendar written; stability per family reported; 2.2 confirmed or corrected |
| Days 1 to 2 | R1 | `82_veeva_link_t3_features` | Build T3 at NPI x cohort for all 43 cohorts from the `56_` logic and dictionary v1; `t3_snapshot` from the frozen snapshot; `t3_asof` from the load picked per cohort in R0 (latest load <= cut-off) | Checks L1 to L4 pass |
| Day 2 | R4 | `83_veeva_link_t3_tests` | Within each call-plan segment (A to E, Non-target): KER-10 writer rate and new-writer rate by `veeva_decile_bin` at cohort C2, forward 12 months; same split within claims-volume bands | Monotonic or not, per segment; table written |
| Days 2 to 3 | R2 | `83_` | (1) Spearman rho of each CL disease / class decile, FA and INDEX vs the same-theme claims volume features (DX patient counts CKD / HF / T2D, RX class volume MRA / SGLT2, Kerendia NBRx history) at C2; (2) share of variance of the decile explained by claims volume (rank regression); (3) writer rate by decile within claims-volume deciles | One row per T3 feature with rho, R², within-band lift; overlap rule P2-D4 applied |
| Days 3 to 4 | R5 | `82_` | Cross features from `60_` logic: L1 practice = BEST_AFFL `BRAND_RANK = 1`, L4 IDN = `mdm_stg_acct_hrchy_ker` ('NA' / 'Multiple Doctors' = no IDN); self excluded; share + zero flag at IDN, practice flag only with practice size. Re-run the `60_` signal test on KER-10 writers before reusing its numbers | Checks L5 and L6 pass; `60_` results on KER-10 written next to the originals |
| Days 5 to 8 | R3 / E5 to E7 | `84_veeva_link_phase2_experiments` | Same model, target, split and selection as E0 to E4 (`73_`); add T3 (E5), time split (E6), cross features (E7). Section 6 | All runs logged; comparison with E4 written |
| Day 9 | G2 | update this file and `50_` | Decision per T3 feature (`t3_decisions`), G2 checklist | G2 checklist complete |

#### 5.1 Feature list for Phase 2

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

#### 5.2 Checks (written to `features_phase2/checks/`)

| # | Check | Pass rule |
| --- | --- | --- |
| L1 | Grain | One row per `NPI_NUMBER` x `COHORT_ID`; NPI set equals `71_` (294,542 per cohort) |
| L2 | Reproduces Phase 0 | `t3_snapshot` for C2 equals `56_` t3 anchor 2025-10-23 on every column (after the NPI rule); coverage counts equal `57_` (scored 147,487) |
| L3 | Missing is not zero | 0 non-null T3 values for `NOT_IN_VEEVA`; no decile = 0 |
| L4 | As-of is as-of | For every cohort, `veeva_score_load_date` <= cohort cut-off in `t3_asof`; null for cut-offs before the first load |
| L5 | Self excluded | No HCP counted in its own practice or IDN share; recount on 100 random HCPs by direct self-join matches |
| L6 | Fixed schema | Columns and order equal the Phase 2 manifest on two consecutive runs |

### 6. Experiments E5 to E7 (and R3)

Same NBA 3.1 model, target, validation split and feature-selection method as E0 to E4; E4 (coverage + T1 + T2) is the comparison point.

| Exp. | Veeva columns | Cohorts | Question |
| --- | --- | --- | --- |
| E5 | E4 + T3 (`t3_snapshot`), after the R2 drops | NBA 3.1 | Do rankings add value on top of activity and profile? |
| E6a | E5 with a time split: train on NBA 3.0 C01 to C23 + NBA 3.1 C1 (cut-off before 2025-03-06), test on NBA 3.1 C2 onward | NBA 3.0 + 3.1 | Does the E5 gain hold on anchors after the score date? |
| E6b | E6a with `t3_asof` instead of `t3_snapshot` on the 2024-06 to 2025-02 cohorts | NBA 3.0 C15 to C23, NBA 3.1 C1 | Does using the score known at the time change the gain? (snapshot much better than as-of = look-ahead) |
| E7 | E5 + cross features (R5), colocation block in the baseline | NBA 3.1 | Do cross features add value on top of colocation and Veeva? Keep only if E7 beats E5, also within segments and for new writers |

**Measures** (as in `50_` section 6): validation metric, SHAP share of the T3 block and of the whole Veeva block, rank of the best T3 feature, T3 features kept after selection, stability across time folds, gain within segments A to E (R4).

**How to read E6.** Gain(E5 - E4) on the post-score test cohorts should be close to the in-time gain. A drop much larger than the drop seen for E4 alone (same split) points to T3 look-ahead; a similar drop for both is target drift. Read together with R0: if scores are static, E6b and E6a should agree.

#### 6.1 Decision rule per T3 feature (G2)

| R2 overlap | R4 within segment | E5 / E6 | Decision |
| --- | --- | --- | --- |
| rho >= 0.8 | any | any | **Business rule only** (copy of claims volume) |
| rho < 0.8 | separates in most segments | kept by selection, gain holds in E6 | **Model** |
| rho < 0.8 | separates | not kept, or gain lost in E6 | **Business rule only** (B1, B2 lists) |
| any | does not separate | any | **Drop** from model and from business rules |
| as-of differs from snapshot (R0) and E6b < E6a | | | **Wait for archive history** (NBA 3.2, X1) |

### 7. Inputs needed

| # | Input | From | Needed for |
| --- | --- | --- | --- |
| I1 | NBA 3.1 model notebook, target and validation split | NBA modelling team | E5 to E7 (same as Phase 1) |
| I4 | NBA 3.0 cohort feature table and target (C01 to C26) | NBA modelling team | E6a / E6b |
| I5 | Readable NBA 3.1 HCP claims features per cohort (DX patient counts, RX class volume, Kerendia NBRx history); candidates under `03_Feature_Engineering/03_HCP_level_features/` and `03_HCP_Level_Features/10_kerendia_prior_writing` | NBA team | R2 (and the open K1 comparison of Phase 1) |
| I6 | Read access to `kerendia_metric_views.mv_kerendia_nbrx` (KER-10) | NBA team | R4, R5 re-run |
| I7 | Colocation L1 / L4 keys (BEST_AFFL, `mdm_stg_acct_hrchy_ker`) as used in `60_` | Colocation owner | R5 |
| X4 / Q6 | What `CLINICAL_LEADER` and `DIGITAL_REACH` measure | Veeva via Vendor Management | Reading R2 |

If I1 or I4 are late, R0, R1, R4 and R5 still run; R2 waits only on I5.

### 8. Gate G2 checklist

* [x] R0 score history: load calendar and stability per family (`81_`, run `20261123T092427`, H1 to H3 pass)
* [x] R1 T3 at NPI x cohort, `t3_snapshot` and `t3_asof`; L1 to L4 pass, L6 lock written (`82_`, run `20261123T093214`)
* [ ] R2 prescribing-overlap test; overlap rule applied (`83_`) — interim run on raw claims done (`83_veeva_link_t3_tests`, run `20261123T101417`); re-run on the model's claims features when I5 is available
* [ ] R3 / E6a and E6b time-split results (`84_`) — **blocked** on I1 / I4 (no NBA 3.1 model notebook, target or split; no E0 to E4 `73_` run found, checked 2026-11-23). `84_` not created
* [x] R4 segment added-value table (`83_veeva_link_t3_tests`, run `20261123T100623`; volume bands are an interim market-TRx proxy until I5)
* [x] R5 cross features built; L5, L6 pass (`82_` run `20261123T093214`); `60_` re-run on KER-10 writers (`82_veeva_colocation_idn_signal_test_ker_10` run `20261123T095952`)
* [ ] E5 run and compared with E4; E7 if R5 built — **blocked** on I1 (same reason)
* [ ] Decision per T3 / cross feature written (`t3_decisions`) and copied to `50_` (D2)

### 9. Risks for Phase 2

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

### 10. Run log

#### 10.1 R0, `81_veeva_link_score_history`, run `20261123T092427` (H1 to H3 pass)

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

#### 10.2 R1, `82_veeva_link_t3_features`, run `20261123T093214` (L1 to L4, L6 pass)

* L1: 294,542 rows in each of 86 partitions (43 cohorts x 2 versions).
* L2: `t3_snapshot` C2 equals `56_` anchor 2025-10-23 on all 16 columns (0 mismatches); 147,487 scored NPIs.
* L3: 0 non-null T3 values for `NOT_IN_VEEVA`; no decile = 0. L4: no as-of load date after its cut-off; null before 2024-08-01. L6: lock written (`schema_lock/t3_columns.json`, 23 columns); second-run comparison still to do.
* As-of uses 8 distinct load sets. Share of matched NPIs whose `veeva_best_decile` differs between snapshot and as-of: 3.8% (2024-07) down to 2.7% (2025-01); 0.66% for cohorts 2025-02 to 2025-10 (same 2025-03-06 load; the gap is the stale rows). `veeva_fa_decile_max_inscope` differs for 4.1% to 5.7% (2024-07 to 2025-01), CL CKD decile for at most 0.05%.
* Reading for E6: the CL deciles are effectively the same in both versions, so E6 cannot show CL look-ahead (R2-1); FA, DR and INDEX change enough for E6b to be informative.

Outputs: `features_phase2/t3/version={snapshot,asof}/COHORT_ID=<id>/`, `t3_version_diff`, `checks/run=20261123T093214`.

#### 10.3 R5 cross features, `82_` cells R5, run `20261123T093214` (L1, L4, L5, L6 pass)

* Groups over the 294,542 NPIs: 282,856 with a practice (90,861 practices), 210,415 in a real IDN (33,061 IDNs). Keys are 1:1 (1 BH_ID per provider, 1 L1 per BH_ID, 1 hierarchy row per L1), so no fan-out.
* Cohort C2: `veeva_idn_expert_share` non-null for 186,898 NPIs (IDN with at least one other HCP), mean 0.129; zero-share flag = 1 for 20,168 (snapshot) / 20,180 (as-of); `veeva_practice_expert_peer_flag` non-null for 233,072, = 1 for 126,019 (snapshot) / 125,921 (as-of).
* L5: 100 random HCPs recounted by direct self-join, 0 mismatches. As-of cross is null for the 15 cohorts without as-of T3. L6 lock written (`schema_lock/cross_columns.json`, 8 columns).
* Outputs: `features_phase2/cross/version={snapshot,asof}/COHORT_ID=<id>/`. Groups use today's affiliation for every cohort (same as the colocation block).

#### 10.4 R5 `60_` re-run on KER-10 writers, `82_veeva_colocation_idn_signal_test_ker_10`, run `20261123T095952`

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

#### 10.5 R4 segment test, `83_veeva_link_t3_tests`, run `20261123T100623` (checks S1 to S4 pass, Spark recount matches)

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

#### 10.6 R2 prescribing-overlap test (interim, raw claims), `83_veeva_link_t3_tests`, run `20261123T101417`

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

#### 10.7 Inputs check (2026-11-23)

Readable from this workspace: I6 `kerendia_metric_views.mv_kerendia_nbrx` (KER-10 `active_nbrx_writers`, KER-06 `paid_nbrx`), I7 `source_provider_bhid_npi_mapping`, `cust_mdm_best_affl_publish_pd_outp_static`, `mdm_stg_acct_hrchy_ker`, and `cp_ker_hcp_2026q4` (segments for R4). Still open: I1, I4, I5.

### 11. Phase 3 results (business use of T3, copied from `90_veeva_link_phase3_working_plan.md` section 10)

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

---

# Part 4: Phase 3 working plan: business use

*Original file: `90_veeva_link_phase3_working_plan.md`*

## Veeva Link Key People: Phase 3 Working Plan (business use in the NBA)

**Parent plan:** `50_veeva_link_nba_3_1_readiness_plan.md`, section 5, Phase 3 (B1 to B4), gate G3 (business lists and action hints part), decisions D2, D3, D7, questions Q1, Q2, Q9  
**Builds on:** Phase 0 (`51_`, `52_` to `57_`), Phase 1 (`70_`, `71_`, `72_`), Phase 2 (`80_`: `81_` score history, `82_veeva_link_t3_features` T3 + cross features, `82_veeva_colocation_idn_signal_test_ker_10`, `83_veeva_link_t3_tests` R4 and interim R2)  
**Goal:** four reviewed, reproducible business outputs (two HCP lists, one action-hint table, one review pack), offline and not rep-facing until licence and compliance answers (X3) are in  
**Status:** B0 to B4 built and checked (2026-11-23, `91_` run `20261123T103200`, `92_` run `20261123T103700`, `93_` run `20261123T103851`); waiting on B3 review feedback and X3 / Q9 (section 10)  
**Date:** November 23, 2026

---

### 1. Why Phase 3 can start before G2 closes

* D2 / P2-D3: T3 scores are business rules and segmentation only until E6 and R2 say otherwise. Phase 3 is exactly that use, so it does not depend on the blocked model experiments (`84_`, E5 to E7).
* Phase 2 evidence supports business-rule use (`80_` sections 10.4 to 10.6):

| Evidence | Result | Meaning for Phase 3 |
| --- | --- | --- |
| R4, Non-target segment | KER-10 writer rate 0.11% / 0.29% / 0.52% at best decile 1-3 / 4-7 / 8-10 (4.73x) | Decile orders untargeted HCPs, but absolute rates are low: B1 is a review list, not a "will write" list |
| R4, segment B | 3.29% / 3.93% / 5.67% (1.72x) | Decile adds inside B: useful priority within B in B1 / B4 |
| R4, segments A, C, D | ratios 1.10, 1.07, 0.80 | Little or reversed: do not use decile to re-rank A / C / D |
| R2 (interim), best decile | rho 0.435 with market TRx; 2.22x within market-volume deciles | Not a copy of volume; ok as a list criterion |
| R2 (interim), CL MRA / SGLT2 class | no writer signal within claims bands (1.00x, 1.03x) | Fine as a **messaging** hint (B2), not as a writer predictor |
| R5 re-run on KER-10 | 18,254 non-writing experts in 2,454 IDNs with peer writer share <= 5% (10,450 Non-target) | B4 base numbers on the KER-10 rule (replace the LRx V7 numbers in `50_` 5.2) |

### 2. New facts that shape Phase 3

| Fact | Effect |
| --- | --- |
| Veeva scores and activity end 2025-03-06; at list date (2026-11) data age is about 20 months | Every list carries `veeva_data_cutoff` and `veeva_data_age_months`; experts new since 2025-03 are missing (risk P3-R1) |
| Snapshot T3 = as-of T3 for every cohort from 2025-03 on (`82_` L2) | Lists use the snapshot version; no version choice needed |
| Stale latest rows (`81_`): snapshot keeps 2,119 FA and 1,969 DR experts whose last load is older than 2025-03-06 | Keep them (vendor never deleted them) but flag `veeva_score_from_stale_load` so reviewers can drop them |
| 50_ numbers are from assessment v2 (18,209 / 10,113) and the LRx V7 writer rule | Phase 3 recomputes them at the list date with KER-10 and documents the gap |
| Call plan = `cp_ker_hcp_2026q4` (`NOTE_2`, FF CR1 / CR2 / CR4 / CR5, Kerendia) | Same segment rule as R4 and `60_` |

### 3. Decisions for Phase 3

| # | Decision | Detail |
| --- | --- | --- |
| P3-D1 | **Offline only until X3** | All outputs are files for brand, sales operations, Field Analytics and Medical Affairs. Nothing goes to the NBA dropdown or reps until Q1 (licence) is answered; payment-based content waits for Q2 |
| P3-D2 | **List date and writer rule** | List date = latest NBA 3.1 cohort C22 (`2026-10_offset7`, cut-off 2026-11-06). Writer = KER-10 `active_nbrx_writers` > 0 in the 12 months to the last KER-10 week (2026-10-16 today); new-writer view as Q11 |
| P3-D3 | **Expert / authority** | Best in-scope decile 8 to 10 (snapshot T3), the same rule as P2-D6. Top tier = 9 to 10 |
| P3-D4 | **Indication split** | Per HCP: indications where the CL disease decile is 8 to 10 (CKD, HF, T2D, T1D, HTN), plus class authority (MRA, SGLT2). An HCP can carry more than one; lists show all, counts are not summed across indications |
| P3-D5 | **Hints are rules, not scores** | B2 hints are deterministic rules on T1 / T2 / T3 columns, one primary hint per HCP by a fixed priority, other hints as secondary. No model output |
| P3-D6 | **Payments** | No payment feature in any hint or list column shown to the field (Q2, D3). Payments may be used only for internal sizing tables |
| P3-D7 | **Language** | "Influence" / "authority", not "KOL" (principle 9); the NBA output is the "NBA dropdown list" |
| P3-D8 | **Reproducible** | Every list is a parquet table with `run_ts`, input run ids (`82_` run, `61_`/`82_` KER-10 run, segment table) and a check table; Excel / CSV exports are made from it, never edited by hand |

### 4. Output layout

`OUT = /Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/veeva_link_to_people/`

| Path | Content | Written by |
| --- | --- | --- |
| `business/b1_untargeted_authority/run=<ts>/` | One row per Non-target NPI at decile 8 to 10: keys, specialty, state, decile, tier, indications, writer status, market volume band, stale-load flag | B1 |
| `business/b1_untargeted_authority/run=<ts>/summary` | Counts by specialty x indication x tier x writer status | B1 |
| `business/b2_action_hints/run=<ts>/` | One row per NPI with any hint: primary hint, secondary hints, rule evidence columns | B2 |
| `business/b4_low_adoption_idn_experts/run=<ts>/` | One row per non-writing expert in a low-adoption IDN: IDN, specialty, segment, IDN writer share, IDN size | B4 |
| `business/b4_low_adoption_idn_experts/run=<ts>/by_idn` | One row per IDN: experts, writers, writer share, segment mix | B4 |
| `business/review_pack/run=<ts>/` | Review samples and feedback template for B3 | B3 |
| `business/checks/run=<ts>/` | Checks M1 to M8 (section 5.2) | all |

### 5. Tasks, notebooks and checks

| Order | ID | Notebook | Work | Done when (check) |
| --- | --- | --- | --- | --- |
| Day 1 | B0 | `91_veeva_link_business_lists` (section 0) | Build the list base at C22: HCP Universe NPI spine, snapshot T3 (`82_`), T1 / T2 (`71_` C22 partition), segment, specialty (HCP Universe; Veeva specialty only if missing), state, KER-10 writer status, market TRx band (R4 rule), L1 / L4 keys and IDN writer share (`82_veeva_colocation_idn_signal_test_ker_10` logic) | One row per NPI (294,542); M1, M2 pass |
| Day 1 | B1 | `91_` (section 1) | Non-target x decile 8 to 10; tier 9 to 10; indications (P3-D4); writer / non-writer; priority inside the list = tier, then non-writer, then market volume band (R2: decile adds beyond volume) | M3: counts within 1% of `80_` 1.1 (18,208 / 10,113) or gap explained; summary by specialty x indication written |
| Day 2 | B4 | `91_` (section 4) | Non-writing experts (KER-10 look-back) in IDNs with peer writer share <= 5% (self excluded), by IDN, specialty, segment; IDN table with size and writer share | M4: reproduces the KER-10 run (18,254 experts / 2,454 IDNs at the `61_` windows) before moving the window to C22 |
| Days 2 to 3 | B2 | `92_veeva_link_action_hints` | Rule table (section 6) on T1 / T2 / T3 columns; one primary hint per HCP by priority; secondary hints; coverage per hint and per segment; overlap matrix between hints | M5: every hint traces to columns in `71_` / `82_` schema locks; M6: no payment column used; coverage table written |
| Day 3 | B2.1 | `92_` | Sense check of hints vs outcome at C2 (forward 12 months, KER-10): writer and new-writer rate per primary hint, inside segment; not a selection criterion, only to catch a hint that points at the wrong HCPs | Table written; any hint with a lower rate than its segment average is flagged for review |
| Day 4 | B3 | `93_veeva_link_review_pack` | Review pack for Field Analytics and Medical Affairs: per list / hint, 10 to 20 sampled HCPs with their Veeva evidence (trials, podium events, decile themes), same template style as `72_` spot check; feedback columns (agree / disagree / reason) | Pack exported; review meeting booked; feedback re-imported and logged |
| Day 5 | G3-B | `90_` (this file) | Write the outcome: lists and hints accepted / changed / dropped; copy to `50_` Phase 3 and gate G3 | Section 9 checklist complete except external answers |

#### 5.1 Inputs

| # | Input | State (2026-11-23) |
| --- | --- | --- |
| J1 | T3 snapshot and cross features (`82_`, run `20261123T093214`) | Ready |
| J2 | T1 / T2 at C22 (`71_`, run `20261123T085209`) | Ready |
| J3 | KER-10 writers (`mv_kerendia_nbrx`) | Ready (I6); last week 2026-10-16 |
| J4 | Segments `cp_ker_hcp_2026q4`, L1 / L4 keys (I7) | Ready |
| J5 | HCP Universe specialty and state | To confirm column names in the HCP Universe table |
| J6 | Licence and compliance answers (Q1, Q2 / X3) | **Open**; gates rep-facing use only |
| J7 | Reviewers named (Q9): brand, sales operations, Field Analytics, Medical Affairs | **Open** |

#### 5.2 Checks

| # | Check | Pass rule |
| --- | --- | --- |
| M1 | One row per NPI in the list base | rows = distinct NPIs = 294,542 |
| M2 | Coverage reproduces Phase 0 | SCORED 147,487 / unscored / not in Veeva as `57_` |
| M3 | B1 counts | Non-target 8-10 and 9-10 within 1% of 18,208 / 10,113 (snapshot, C22 segments) |
| M4 | B4 reproduces the KER-10 run | 18,254 experts, 2,454 IDNs, 10,450 Non-target at the `61_` windows |
| M5 | Hint traceability | Every rule column exists in `schema_lock/columns.json`, `t3_columns.json` or `cross_columns.json` |
| M6 | Compliance guard | No `veeva_pay_*` column in B1 / B2 / B4 field-facing exports |
| M7 | No HCP outside the universe or outside Veeva in hint rows | All hint rows have `veeva_coverage_status` = `SCORED` or `IN_VEEVA_UNSCORED` |
| M8 | Independent recount | 100 random B1 / B4 rows recounted from raw T3 and KER-10 with a separate query; 0 mismatches |

### 6. B2 action-hint rules (first version, to review in B3)

Priority = order in the table; the first rule that fires is the primary hint.

| Priority | Hint (NBA reason / channel) | Rule (columns) | Why |
| --- | --- | --- | --- |
| 1 | Peer-to-peer / speaker programme invitation | `veeva_event_podium_flag_3y` = 1 and `veeva_event_n_inscope_3y` > 0 | `50_` B2; podium = peer influence |
| 2 | Clinical-evidence messaging (trial investigator) | `veeva_trial_n_inscope_5y` > 0 (PI if `veeva_trial_pi_flag_5y` = 1), or `veeva_trial_finerenone_flag_5y` / `veeva_trial_mra_flag_5y` = 1 | `50_` B2; trials rise with decile (assessment 8.1) |
| 3 | Cardiorenal class messaging | `veeva_cl_decile_mra_class` or `veeva_cl_decile_sglt2_class` 8 to 10 | `50_` B2; R2: class deciles track volume, not writing, so messaging only |
| 4 | Disease-specific messaging (CKD / HF / T2D) | CL disease decile 8 to 10 for that indication (P3-D4) | Indication view (D5) |
| 5 | Scientific content (digital) | `veeva_dr_any_inscope` = 1 or `veeva_pub_n_inscope_5y` > 0 | Digital reach and publishing activity |

Not used as hints: payments (P3-D6), INDEX scales and Scientific Reach (R2: no writer signal within claims bands; may be shown as context only).

### 7. Order of work

1. B0 base and M1 / M2 (day 1).
2. B1 and B4 in `91_` (days 1 to 2); M3 / M4 first, then move B4 to the C22 window.
3. B2 rules and coverage in `92_` (days 2 to 3), B2.1 sense check.
4. B3 review pack (day 4); meeting with Field Analytics and Medical Affairs.
5. Write outcomes here and in `50_` (day 5).

### 8. Risks for Phase 3

| # | Risk | Mitigation |
| --- | --- | --- |
| P3-R1 | Data age about 20 months; new experts missing, retired experts still listed | Show data cut-off and age on every list; stale-load flag; refresh (X2) before any repeat |
| P3-R2 | Lists read as "will write" lists | State the R4 rates in the cover note (Non-target 8-10: 0.52% writer rate); position as target-list review input |
| P3-R3 | Licence / compliance does not allow commercial use | P3-D1: offline only; Medical Affairs-only fallback for B1 / B4 |
| P3-R4 | Hints overlap with internal speaker / MSL data (personal block) | B3 reviewers check against Bayer speaker lists; Veeva hints describe external activity only (D3) |
| P3-R5 | Old call plan / affiliation snapshot | Same Q4-2026 snapshot as colocation; re-run with the next call plan |
| P3-R6 | Segment D reversal (R4) | Do not use decile to prioritise inside D |

### 9. Phase 3 checklist (G3, business part)

* [x] B0 list base at C22; M1, M2 pass (`91_` run `20261123T103200`)
* [x] B1 untargeted-authority list and summary; M3, M8 pass (`91_`)
* [x] B4 low-adoption IDN expert list; M4, M8 pass (`91_`)
* [x] B2 action hints and coverage; M5 to M7 pass; B2.1 sense check (`92_` run `20261123T103700`)
* [ ] B3 review pack built (`93_` run `20261123T103851`, 150 rows, P1 / P2 / M6 pass); **not yet sent**; feedback not logged
* [ ] Outcomes copied to `50_` Phase 3 and G3
* [ ] External: X3 (Q1, Q2) answered before any rep-facing use; Q9 reviewers named

### 10. Run log

#### 10.1 B0, B1, B4: `91_veeva_link_business_lists`, run `20261123T103200` (M1 to M4, M6, M8 pass)

* B0: 294,542 NPIs at C22; coverage SCORED 147,487 / IN_VEEVA_UNSCORED 81,441 / NOT_IN_VEEVA 65,614 (= Phase 0). KER-10 last week 2026-10-16; 12-month window 2025-10-18 to 2026-10-16: 31,425 writers. Experts (decile 8-10) 37,075; 1,508 with a score from a stale load. Specialty filled 99.8% (BEST_AFFL, LRx V7 fallback). Data age 19.3 months.
* B1: 18,208 Non-target HCPs at decile 8-10 (top tier 9-10: 10,113; = `80_` 1.1). Non-writers in the last 12 months: 17,900; writers 308. Top specialties FM 6,338, IM 3,618, CD 2,311, END 1,210, GP 793, NEP 690. CL indication (HCP can carry several): HTN 3,294, MRA class 2,822, T2D 1,568, HF 1,473, SGLT2 class 915, T1D 530, CKD 348; 9,693 have no CL disease / class decile >= 8 (their best decile comes from other CL themes or FA / DR). 46 with stale-load scores.
* B4: M4 reproduces the KER-10 run exactly (18,254 experts / 2,454 IDNs / 10,450 Non-target). At the list date (13-week look-back 2026-07-18 to 2026-10-16): 13,499 experts in 2,296 IDNs; Non-target 7,986, B 2,561, D 1,148, A 756, C 624, E 424. Largest IDNs: Cleveland Clinic (393), Trinity (366), Piedmont (335), Ascension (319), Advocate (270). Top specialties FM, CD, IM, END, NEP.
* M8: 100-row recount of B1 (raw T3 + metric view) and B4 (IDN peers) with 0 mismatches. The B4 recount re-uses the same in-memory provider table, so it checks the grouping logic, not the source joins.

#### 10.2 B2, B2.1: `92_veeva_link_action_hints`, run `20261123T103700` (M5, M6, M7 pass)

32,133 NPIs (10.9%) have at least one hint (32,015 scored, 118 in Veeva unscored).

| Hint | Rule fires | Primary | Writer rate at C2 (forward 12M, all segments) |
| --- | --- | --- | --- |
| P2P_SPEAKER | 4,921 | 4,921 | 18.88% |
| CLINICAL_EVIDENCE | 4,810 | 3,333 | 22.71% |
| CARDIORENAL_CLASS | 10,173 | 9,456 | 26.46% |
| DISEASE_CKD | 2,060 | 1,743 | 59.72% |
| DISEASE_HF | 3,954 | 2,835 | 8.54% |
| DISEASE_T2D | 4,881 | 2,465 | 21.18% |
| SCIENTIFIC_CONTENT | 12,784 | 7,380 | 10.03% |
| (no hint) | | 262,409 | 7.55% |

* Largest overlaps: P2P_SPEAKER and SCIENTIFIC_CONTENT 3,573; CLINICAL_EVIDENCE and SCIENTIFIC_CONTENT 2,434; CARDIORENAL_CLASS and DISEASE_T2D 1,580.
* Hints are identical at C2 and C22 for all NPIs (T1 and T3 do not change after the 2025-03-06 cut-off).
* B2.1 flags (segment x primary hint, >= 100 HCPs, writer rate below the segment average), 20 cells: `DISEASE_HF` in A, B, D, E and Non-target; `P2P_SPEAKER` and `SCIENTIFIC_CONTENT` in A, B, D, E and Non-target (`SCIENTIFIC_CONTENT` also in C); in segment D also `CARDIORENAL_CLASS` and `CLINICAL_EVIDENCE` (5 of 7 hints; `DISEASE_CKD` and `DISEASE_T2D` not flagged); in segment E also `CARDIORENAL_CLASS` and `CLINICAL_EVIDENCE` (segment rate 0.14%, hint cells 0%).
* Reading for B3: `DISEASE_HF` points at HCPs who write less than their segment (same as R2: no writer signal for CL HF); keep it as a messaging hint only if reviewers agree, otherwise drop. In segment D, do not use hints for prioritisation (R4 reversal, P3-R6).

#### 10.3 B3: `93_veeva_link_review_pack`, run `20261123T103851` (P1, P2, M6 pass)

150 rows: 15 per group for B1 top tier, B1 tier 8, B4 and each of the 7 primary hints, with Veeva evidence and empty `REVIEW_AGREE` / `REVIEW_REASON` / `REVIEWER` columns; cover note with the data age, the R4 rate caveat and review questions. Output: `business/review_pack/run=20261123T103851/{pack, pack_csv, cover}`. Some B1 sample rows have no hint and `IDN_NAME` = 'NA' (no IDN); reviewers see Veeva decile and indication only for them.

Next: name reviewers (Q9), send the pack, log feedback, then decide which hints stay (G3). No rep-facing use until X3 (Q1, Q2).

---

# Part 5: Phase 4 working plan: operations

*Original file: `95_veeva_link_phase4_working_plan.md`*

## Veeva Link Key People: Phase 4 Working Plan (operations)

**Parent plan:** `50_veeva_link_nba_3_1_readiness_plan.md`, section 5, Phase 4 (O1 to O4), Track X (X1, X2, X5), gate G3 ("fresh load used or its absence accepted", "feature dictionary written"), risks "stale data" and "load-to-load changes in focus names"  
**Builds on:** Phase 0 (`52_` snapshot freeze, `53_` config, `54_` spine, `55_` long activity, `56_` features, `57_` acceptance), Phase 1 (`71_` T1 / T2, schema lock), Phase 2 (`81_` score history and load archive, `82_` T3 + cross, `83_` tests), Phase 3 (`91_` to `93_` business outputs)  
**Goal:** the Veeva block can be refreshed, monitored and explained without manual work: a monthly archive and refresh job (O1), a freshness check on every run (O2), a monthly dictionary report (O3) and the final feature dictionary (O4)  
**Status:** draft for discussion. O2, O3, O4 can start now; O1 as a scheduled job needs an owner (X1) and approval before it is created  
**Date:** November 23, 2026

---

### 1. Starting point

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

### 2. Facts that shape Phase 4

| Fact (source) | Effect |
| --- | --- |
| Raw Snowflake tables keep weekly full loads: score tables 2024-06-27 (CL 2024-08-01) to 2025-03-06, 33 to 38 loads; `SCIENTIFIC_EXPERT` loads in June 2025 (`81_`, Phase 0 profile) | O1 can archive by `LOAD_ID`; a run with no new `LOAD_ID` is a valid "no new load" result, not a failure |
| No new load since 2025-03-06 (children) / 2025-06-30 (hub; `96_` run `20261123T110157`): data age 19.3 months at the Phase 3 list date (`91_`) | O2 warns today on the "> 12 months" rule; G3 needs X2 (fresh load) or an explicit acceptance of the stale data |
| Hub vs children gap is 3.8 months (`96_`) | Under the 6-month rule of O2, but logged every run |
| `IS_LATEST_FLAG = 'Y'` keeps stale rows from older loads (`81_`: DR 37,968 of 63,674 in-scope rows) | O1 archives per load, not only latest rows; O2 reports the stale-row share per score table |
| Some features read fixed windows that end at the data cut-off (U7) | A refresh changes inputs only; code and schema stay the same (risk "building on old data" in `50_` 9) |
| `REGEXP_LIKE` fails silently through the Spark connector; DATE columns in `PUBLICATION` / `MEDICAL_EVENT` are VARCHAR | O1 and O3 keep the `ILIKE` / `TRY_TO_DATE` rules of Phase 0 |
| T3 decisions per feature are not final (`80_` checklist; E5 / E6 blocked on I1) | O4 writes a status column (model / business rule / wait) and is re-issued when G2 closes |

### 3. Decisions for Phase 4

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

### 4. Output layout

| Path | Content | Written by |
| --- | --- | --- |
| `archive/<table>/LOAD_ID=<id>/` | Raw rows of one load (US, not deleted), `load_date`, `src_load_id` | O1 |
| `archive/load_calendar/` | One row per table x `LOAD_ID`: load date, rows, experts, archived flag | O1 |
| `ops/freshness/run=<ts>/` | One row per table: last load date, data cut-off, data age (months), hub gap, stale-row share, warn flags | O2 |
| `ops/refresh_log/run=<ts>/` | Steps run, run ids of `52_` to `82_`, acceptance result, schema check | O1 |
| `ops/dictionary_report/run=<ts>/` | New focus names (by table, with expert counts), new keyword hits and near misses, removed names | O3 |
| `docs/feature_dictionary/run=<ts>/` | One row per feature: name, family, tier, source table, rule in plain language, window, null meaning, status (model / business rule / wait) | O4 |
| `99_veeva_link_feature_dictionary.md` (this folder) | Markdown version of O4 for business readers | O4 |

### 5. Tasks, notebooks and checks

| Order | ID | Notebook | Work | Done when (check) |
| --- | --- | --- | --- | --- |
| Days 1 to 2 | O2 | `96_veeva_link_freshness_check` | Snowflake: max `LOAD_ID` / load date per in-use table (pushed down); volume: last archived load; data cut-off per table (max activity date where relevant: publications, events, trials, payments); data age vs today; hub gap; stale-row share for the 4 score tables (`IS_LATEST_FLAG = 'Y'` rows whose load is older than the table's last load) | N1: one row per in-use table (15); N2: latest cut-off per table = `52_` snapshot manifest, and the 4 score tables' last load = `81_` load calendar (the `81_` stale counts are on in-scope matched rows only, so they are not comparable with the all-row counts here); warn flags set as P4-D5 |
| Days 2 to 4 | O1a | `97_veeva_link_archive_refresh` (archive step) | From `52_` and `81_` code: list new `LOAD_ID`s vs `archive/load_calendar`; copy each new load once (P4-D2); back-fill the full history of all 15 in-use tables that are not yet archived (today only the 4 score tables are) | N3: archived row counts = Snowflake counts per load; N4: re-running with no new load writes nothing and exits "no new load" |
| Days 4 to 5 | O1b | `97_` (refresh step) | If O1a found a new load: run the chain (P4-D3) with `dbutils.notebook.run` or job tasks; collect run ids; run `57_`; compare schemas to the locks (P4-D4); re-run `91_` / `92_` only on request | N5: acceptance passes; N6: schemas equal the locks; N7: refresh log written. Dry run on the current snapshot (no new load) must reproduce Phase 0 to 2 numbers |
| Day 5 | O1c | Job (after approval, P4-D6) | Lakeflow Job: task 1 `96_`, task 2 `97_` (condition: new load), monthly schedule, failure email to the owner | Job created and one scheduled run succeeds |
| Days 3 to 4 | O3 | `98_veeva_link_dictionary_report` | (0) once: write `config/focus_names_seen_v1`, every distinct focus name in the current snapshot per table, in scope or not (v1 holds only the 299 in-scope names); (a) focus names in the latest `CLINICAL_LEADER` / `FOCUS_AREA` / `DIGITAL_REACH_FOCUS_AREA` rows not in the seen list, with expert counts and a suggested theme from `keyword_list_v2` hits; (b) names in the dictionary that no longer appear; (c) trial / publication / event titles that hit an include keyword but also an exclude, and titles with in-scope disease words but no keyword hit (near misses); (d) review sheet for X5 | N8: on the current snapshot the report finds 0 new names vs the seen list, and every v1 name is still present; N9: report rows have counts and a sample of 5 titles |
| Days 5 to 7 | O4 | `99_veeva_link_feature_docs` + `99_veeva_link_feature_dictionary.md` | Build the dictionary from the manifest (52 T1 / T2), T3 lock (23) and cross lock (8): family, tier (T1 / T2 / T3), source tables, plain-language rule, window, null / 0 meaning (three-state coverage), status from `t3_decisions` (or "wait: G2 open"); add Phase 3 business uses (B1, B2, B4) | N10: every locked column has exactly one dictionary row; N11: no row without source table and rule; N12: status column filled |

#### 5.1 Inputs

| # | Input | State (2026-11-23) |
| --- | --- | --- |
| K1 | Snowflake access for load listing and copy (same `SF_OPTS` as Phase 0) | Ready |
| K2 | Owner for the monthly job (X1: Data Engineering + NBA team) | **Open** |
| K3 | Fresh, aligned load (X2) | **Open**; Phase 4 works without it (dry run) |
| K4 | Medical / brand reviewers for dictionary changes (X5, Q7) | **Open** |
| K5 | `t3_decisions` table (G2) | **Open**; O4 uses "wait" until written |
| K6 | Style of the digital / field feature dictionaries | To read: `04_Promotional_Features/.../50_digital_nba_3_1_readiness_plan.md` family docs |

### 6. Job design (O1c, for approval)

| Item | Proposal |
| --- | --- |
| Name | `veeva_link_monthly_archive_refresh` |
| Tasks | `freshness` (`96_`) -> `archive_refresh` (`97_`, runs only if `freshness` reports a new `LOAD_ID`; condition task on a task value) |
| Schedule | Monthly, first Monday 06:00 Europe/Berlin (to confirm with the owner) |
| Compute | Serverless (the Snowflake connector works from serverless, Phase 0) |
| Notifications | Failure and "freshness warn" to the owner and the NBA team |
| Run as | Service principal of the NBA pipeline (to confirm), with read on the Snowflake role and write on `OUT` |
| Not in the job | Business lists (`91_`, `92_`) and the review pack (`93_`): on request, after review (P3-D1) |

### 7. Order of work

1. O2 freshness check (days 1 to 2); confirms the stale-data status for G3.
2. O1a archive and back-fill (days 2 to 4), then O1b refresh dry run (days 4 to 5).
3. O3 dictionary report (days 3 to 4), in parallel.
4. O4 feature dictionary (days 5 to 7); re-issue when G2 closes.
5. O1c job, once K2 is named and the user approves.

### 8. Risks for Phase 4

| # | Risk | Mitigation |
| --- | --- | --- |
| P4-R1 | No new load ever arrives; the job only reports stale data | O2 makes the age visible on every run; G3 records "absence accepted" if X2 is not solved |
| P4-R2 | Vendor drops old `LOAD_ID`s from Snowflake before we archive them | Back-fill all 15 tables in O1a now (only the 4 score tables are archived today) |
| P4-R3 | A new load changes focus names or adds event types | Schema lock (P4-D4); O3 report; dictionary v2 through review |
| P4-R4 | Refresh changes acceptance numbers (new experts, new matches) | `57_` thresholds re-based on the new load; match rate must stay within 1 point; changes logged |
| P4-R5 | Snowflake connector traps (`REGEXP_LIKE`, VARCHAR dates, reserved `rows`) | Reuse Phase 0 query helpers; N3 row-count check per load |
| P4-R6 | Job runs without an owner | P4-D6: no job before K2 |
| P4-R7 | Feature dictionary drifts from the code | O4 built from the schema locks and manifest, not written by hand; N10 |

### 9. Phase 4 checklist (operations)

* [x] O2 freshness check; N1, N2 pass (`96_` run `20261123T110157`)
* [ ] O1a archive: `97_` built, plan run `20261123T112007` (N4 pass); copy waits on scope decision (N3)
* [x] O1b refresh dry run: no new load, chain not run; N6, N7 pass (`97_` run `20261123T112007`); N5 runs after the first real refresh
* [x] O3 dictionary report; N8, N9 pass (`98_` run `20261123T110829`)
* [ ] O4 feature dictionary: table done, N10 to N12 pass (`99_` run `20261123T111314`); markdown `99_veeva_link_feature_dictionary.md` not yet written
* [ ] O1c monthly job created after owner (K2) and approval; one scheduled run succeeds
* [ ] Copy outcomes to `50_` Phase 4 and G3 ("fresh load used or its absence accepted", "feature dictionary written")

### 10. Run log

#### 10.1 O2: `96_veeva_link_freshness_check`, run `20261123T110157` (N1, N2 pass)

* No new load (`new_load` = 0). Hub `SCIENTIFIC_EXPERT`: 7 loads 2025-06-25 to 2025-06-30, data age 16.8 months. All 14 child tables: last load 2025-03-06 (`LOAD_ID` 20250306110047), data age 20.6 months, hub gap 3.8 months.
* Warn: all 15 tables over 12 months old; no table over the 6-month hub gap.
* Latest rows equal the `52_` manifest for all 15 tables.
* Stale latest rows (latest rows from an older `LOAD_ID` than the table's last load): highest shares are `SCIENTIFIC_EXPERT` 99.9% (most rows come from the 2025-06-25 load, 5 days before its last load), `DIGITAL_REACH_FOCUS_AREA` 82.0%, `FOCUS_AREA` 46.3%, `CLINICAL_TRIAL` 42.5%, `PUBLICATION` 40.9%; lowest `CLINICAL_LEADER` 0.2%, `PAYMENT` 1.0%.
* Activity cut-off in the snapshot (dates on or before today): payments 2023-12-31, publications 2025-12-31, trials 2026-11-01, events 2026-11-19 (trial and event dates after the load are planned dates).
* Size for O1a: **12,093,862,883 rows across all loads in Snowflake** (largest: `PAYMENT` 3.93 bn, `FOCUS_AREA` 3.77 bn, `CLINICAL_LEADER` 2.99 bn, `DIGITAL_REACH_FOCUS_AREA` 0.57 bn). Each load is a full copy, so a full back-fill is about 12 bn rows; scope decision needed before O1a.

#### 10.2 O3: `98_veeva_link_dictionary_report`, run `20261123T110829` (N8, N9 pass)

* `config/focus_names_seen_v1` written once: 36,050 focus names (CL 704 name x type, FA 18,426, DR 16,920).
* New names vs seen list: 0; v1 names (299) no longer present: 0.
* Keyword conflicts (include and exclude of tag `mra` both hit): trials 8, events 2, publications 81 titles.
* Near misses (disease word, no include keyword): publications diabet 43,231, renal 32,967, kidney 26,509, nephr 7,012, aldosterone 637, cardiomyopath 473; events and trials smaller. 0 for heart failure, albuminuria, proteinuria, mineralocorticoid, cardiorenal (every title with these words already hits an include keyword).
* Review sheet 21 rows for X5 at `ops/dictionary_report/run=20261123T110829/review_sheet_csv`.

#### 10.3 O4: `99_veeva_link_feature_docs`, run `20261123T111314` (N10, N11, N12 pass)

83 locked columns, one row each: T1 38 (kept), T2 13 (12 kept, 1 waiting I3), T3 18 and cross 5 (wait: G2 open, with Phase 2 / 3 reading), keys and metadata 9. Output `docs/feature_dictionary/run=20261123T111314/{dictionary, dictionary_csv, checks}`. First run failed N11 / N12 on 6 columns (2 composite features without a source mapping, 4 metadata columns); fixed and re-run.

#### 10.4 O1: `97_veeva_link_archive_refresh`, run `20261123T112007` (plan mode; N4, N6, N7 pass; N3, N5 n/a)

* Parameters `MODE` (`plan` / `copy`) and `SCOPE` (`none` / `final_plus_small` / `score_full` / `all`); default `plan` / `none` copies nothing.
* Archive empty so far: 542 Snowflake loads missing (12,093,862,883 rows). Size per scope: `final_plus_small` 399 loads, 1.12 bn rows (all 15 tables); `score_full` 147 loads, 7.43 bn rows (4 score tables); `all` 542 loads, 12.09 bn rows.
* No new load, so the refresh chain did not run and nothing was written to the archive (N4).
* Schemas equal the locks: T1 / T2 59 columns, T3 23, cross 8 (N6).
* Refresh log at `ops/refresh_log/run=20261123T112007/` (N7).
* Still open: archive scope decision, then a `copy` run (N3); O1c job waits on owner (K2) and approval (P4-D6).
