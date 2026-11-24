# NBA 3.1 LAAD features: Databricks Feature Views readiness plan

**Purpose:** Decide how the LAAD (Rx, Dx, Px, Lab) HCP features of NBA 3.1 should use Databricks Feature Views, check what is ready today, and set the steps to get the contender views (V1-V10) into feature selection.

**Date:** 2026-11-23 | **Owner:** Wenjie Chen | **Branch:** `combine` (`kerendia_nba_3_1_develop_pg`)

**Inputs:** UC schema `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_nba_3_1` (run `full_2026_11_16_*`, `input_claims_cohorts`, `input_hcp_universe`); sandbox `nba_fv_test`; `00_cohort_config` (`03_HCP_level_features/`); team test notebook `NBA_3_1_Feature_Views_Investigation` (`kerendia_nba_3_1_develop`, 2026-11-17/20).

**Related docs:** `../01_Source_Review/NBA_3_1_LAAD_Source_Review_Overview.md`, `../02_NBA_3_0_Model_Evaluation/NBA_3_0_Model_Feature_Evaluation.md`, `../04_Feature_Ideas/NBA_3_1_HCP_Feature_Ideas_Draft.md`, `../../Alignment_Markdowns/Strategy_and_Execution/NBA_3_1_HCP_Features_Fill_Missing_and_Lag.md`.

Nothing in this doc changes a pipeline notebook, model or table.

**Decisions (2026-11-23, Wenjie):**

* **Schema:** all registered features and feature tables live in `kerendia_nba_3_1` (no new schema). Names follow section 5.3.
* **Distinct counts:** `ApproxCountDistinct` is good enough. Accuracy is reported, not used as a gate.
* **CKD stage (V7):** investigated in section 6.2. Recommendation: current lab eGFR first, Dx as fallback, eGFR stage 1-2 counted as CKD only with kidney-damage evidence.

---

## 1. Short answer

Use two tracks.

| Track | What | For which features | Readiness |
| --- | --- | --- | --- |
| **R: register** | Register the NB01-NB06 output tables as time-series feature tables (`create_table` with `NPI_NUMBER` + cutoff timestamp). No logic change. | All existing 3.1 HCP features (~8,360 columns), incl. V1 (NBRx, NPS) | Proven on a sample (team Test A: 100% value match, point-in-time join worked). Not tested at full width (NB01 = 4,677 columns). |
| **C: compute** | Define new contender features as Feature Views (`Feature` + `DeltaTableSource`) on stable LAAD source tables, built with `create_training_set` at the cohort cutoffs. | New 3.1 contenders: V2, V6-V10, F9, F10 | Needs source prep (section 4). Calendar-month parity needs the month-bucket method (section 5.2), not yet tested. |

Why not compute everything as Feature Views: the team test (Test B) showed 30-day / 365-day rolling windows on raw claims match the calendar-month NB01 features only 38-46% of the time (max diff 29-65 claims). For new features there is no 3.0 parity to keep, and section 5.2 shows a way to get exact calendar months, so Track C is reasonable for new features only.

## 2. What the team already tested (2026-11-17/20)

From `NBA_3_1_Feature_Views_Investigation` (sample: 252 NB01 rows, 51,646 raw Rx claims, 9 test HCPs x 28 cohorts):

| Test | What | Result |
| --- | --- | --- |
| A | Register NB01 output as time-series feature table, build training set | Worked; 0 mismatches; point-in-time join correct (first cohort null as expected) |
| B | Compute claim counts from raw Rx with `RollingWindow` 30d / 31d / 365d | Worked technically; only 38-46% exact match to calendar-month features |
| C | Register single columns with `ColumnSelection` | Worked, 100% match; one call per column, so only for a hand-picked subset |
| D | Plain table with PRIMARY KEY only | Not visible to Feature Store, no point-in-time lookup |

Not tested by the team: full-size tables, online store, `fe.log_model`, job service principal `CREATE FEATURE`, `score_batch`, materialization.

A likely contributor to the Test B gap (not verified): the label timestamp was the cutoff day at 00:00, so claims on the cutoff day fall outside the window. Section 5.1 fixes the timestamp convention.

## 3. Requirements Feature Views puts on the sources

* Source must be a UC Delta table (`DeltaTableSource`). The raw LAAD tables in `phcdw.phcdw_stg_car` are FOREIGN (Snowflake), so they cannot be used directly. The `kerendia_nba_3_1` pulls are MANAGED Delta tables and can.
* `entity` columns cannot be DATE/TIMESTAMP; `timeseries_column` must be DATE or TIMESTAMP.
* No exact distinct count: only `ApproxCountDistinct(relativeSD=...)`.
* No ratios or cross-feature math inside a `Feature`; shares and rates are computed after `create_training_set`.
* `filter_condition` (SQL WHERE) and `transformation_sql` run before aggregation; that is how product, claim type, stage and test filters are expressed.
* Runtime: serverless or DBR 17.0 ML+, `databricks-feature-engineering` installed; `CREATE FEATURE` on the target schema (`READ FEATURE` to use).

## 4. Source readiness (checked 2026-11-23 on run `full_2026_11_16`)

| Source table (`kerendia_nba_3_1.`) | Rows | Service dates | Entity / time columns | Ready? | Gap |
| --- | --- | --- | --- | --- | --- |
| `full_2026_11_16_pull_rx_hcp` | 3,275,477,893 | 2023-01-01..2026-09-30 | `NPI_NUMBER` STRING (0 null), `SVC_DT` DATE | Partly | No `CLAIM_TYPE` column: only `REJECTION_FLAG` (0/1). Reversed (RV) claims cannot be split out; R1 needs PJ03 to add `CLAIM_TYPE`. |
| `full_2026_11_16_pull_dx_step4` | 475,010,310 | 2023-01-01..2026-09-30 | `NPI_NUMBER` (0 null), `SVC_DT` DATE | Yes | `CKD_SUBSTAGE` only has 3a / 3b / ESRD; stage 2 and 4 come from `DX_STAGE`. |
| `full_2026_11_16_pull_lab_step4` | 307,461,581 | 2023-01-01..2026-09-30 | `NPI_NUMBER` (0 null), `SVC_DT` DATE | Yes, after dedup check | Test types UACR, GFR, POTASSIUM, HBA1C present. Confirm the S3 dedup (HIST reloads) is applied before this pull. |
| `full_2026_11_16_pj_pat_new_ckd_stage` | 4,123,720,085 | months 2023-01..2026-09 | `PATIENT_ID`, `SVC_DT_M` DATE | No | Patient x month grid (150,897,177 patients), stages 1-5; no HCP column, needs the HCP-patient bridge. |
| `full_2026_11_16_pj_pat_sglt2_filter_m` | 4,123,720,085 | months 2023-01..2026-09 | `PATIENT_ID`, `SVC_DT_M` DATE | No | No HCP column. Built before the C1 SGLT2 fix (2026-11-23). Has only `ELIGIBLE_PATIENT_FLAG` (1 on 3,174,179,271 patient-months = 77%), not the per-indication flags. Written by an earlier code version: the current PJ06 code gives 18.5% on a 5% sample (6.3). |
| `full_2026_11_16_pj_dm_hf_flags` | not counted | patient-level, `HF_FIRST_DATE` | `PATIENT_ID` | No | No HCP column; one row per patient, so only usable joined to the bridge. |
| `full_2026_11_16_pj_px` | not counted | `FIRST_DIALYSIS_DATE` is STRING | `PATIENT_ID` | No | Cast date; no HCP column. |
| `input_claims_cohorts` | 28 | lookback end 2024-05-01..2026-08-01; last prediction month 2026-10-01 | `cohort_id` | Yes | Training / Testing / Holdout (Backtesting). This is the label spine. |
| `input_hcp_universe` | not counted | - | `PROVIDER_ID` (C1-C5 flags) | Check | Keyed by `PROVIDER_ID`, features by `NPI_NUMBER`: confirm the mapping (open point O2, 157 HCPs). |

The pulls end 2026-09-30, the lag month of the last cohort (lookback Aug 2026, lag Sep, prediction Oct). That matches the one-month data-lag rule in `00_cohort_config`.

**Table names are run-specific** (`full_2026_11_16_...`). A `Feature` is bound to one table name, so Track C needs stable source tables (e.g. `fv_src_rx_claims`) that each full run overwrites.

## 5. Design rules for Track C

### 5.1 Keys and timestamps

* **Entity:** `NPI_NUMBER` (STRING) for all views.
* **Feature timeseries column:** `MONTH_TS` = first day of the service month (DATE) on the month-bucket tables; `SVC_DT` on event-level tables.
* **Label (training-set) timestamp:** first day of the month **after** the lookback end, with the same column name. Example: lookback ends May 2024 (`lookback_end_date` 2024-05-01), label `MONTH_TS` = 2024-06-01. Data up to 2024-05-31 is used; June (lag month) and July (prediction month) are not.
* **Label spine:** `input_claims_cohorts` (28 cohorts) x HCP universe, carrying `COHORT_ID`, `DATASET` and the target.

### 5.2 Calendar-month windows: month-bucket method

Feature Views windows are durations. To get exact calendar months for counts that can be added up across months:

1. Pre-aggregate the source to one row per `NPI_NUMBER` x month x filter value (counts), stamped at `MONTH_TS` = the 1st of the month.
2. Use `Sum` over a `RollingWindow` whose length falls strictly between the N-month and (N+1)-month spans.

Safe durations, checked on every month from 2024-02 to 2027-12:

| Window | N months reach back at most | N+1 months reach back at least | Safe duration (days) | Use |
| --- | --- | --- | --- | --- |
| 1 month | 31 | 59 | 32-58 | 45 |
| 3 months | 92 | 120 | 93-119 | 106 |
| 6 months | 184 | 212 | 185-211 | 198 |
| 12 months | 366 | 393 | 367-392 | 379 |
| 24 months | 731 | 758 | 732-757 | 744 |

The midpoint keeps the result safe whether the window edges are inclusive or exclusive. **Not yet tested in Feature Views**: Phase 2 checks it against NB01-style counts.

This method does **not** work for distinct-patient counts (patients seen in several months would be counted more than once). For those, use the event-level table with `ApproxCountDistinct(PATIENT_ID)` (accepted, see Decisions).

### 5.3 Other rules

* **Data start:** 2023-01-01 (as in `00_cohort_config`). The Jan-2023 Dx/Px coverage step does not affect features (decision D1).
* **Claim type (R1):** paid, reversed and rejected as separate features; target-aligned features (NBRx, TRx) paid only.
* **Lab (S3):** dedup before counting.
* **Window set:** 3 and 12 months, a running total (lifetime `SlidingWindow`, or Track R), and a trend (3 months vs the previous 3 via `delay`). Add 1 and 6 months only where the 3.0 SHAP justifies it (avoids the near-duplicate groups found in 3.0).
* **Shares and rates:** computed after `create_training_set`; null when the denominator is 0.
* **Naming in `kerendia_nba_3_1`** (stable names, no run prefix, so a model keeps pointing at the same objects; the run is recorded in the table comment and the Delta commit `userMetadata`, as in the team's time-travel demo):

| Object | Pattern | Example |
| --- | --- | --- |
| Feature View source table (Track C) | `fv_src_<source>[_<grain>]` | `fv_src_rx_claims`, `fv_src_rx_npi_month`, `fv_src_hcp_patient_month` |
| Registered feature (Track C) | `fv_<source>_<measure>_<filter>_<N>m` (`_lt` = lifetime, `_trend3m` = 3 vs previous 3 months) | `fv_rx_claims_rj_kerendia_3m`, `fv_lab_pts_gfr_tested_12m`, `fv_ckd_pts_stage_3b_12m` |
| Registered feature table (Track R) | `ft_hcp_<NB output name without run prefix>` | `ft_hcp_claim_rx_monthly_cohort` (from `full_<run>_hcp_claim_rx_monthly_cohort`) |

  Lower case, `<source>` one of `rx`, `dx`, `px`, `lab`, `ckd`, `elig`, `hf`; names generated from one config list, not by hand. Existing prefixes in the schema (`full_`, `validation_`, `input_`, `ref_`, `run_registry`) stay as they are; `fv_` / `ft_` are reserved for Feature Views objects. The sandbox `nba_fv_test` already uses the same `fv_` / `ft_` style.

### 5.4 Lag and point-in-time

* Feature Views point-in-time works on **service date**, not load date. Training cohorts therefore see months that later loads have filled in, while at scoring time the newest month is still thin (raw Dx Oct 2026 = 79.6M rows vs 98-109M in earlier months; Px Oct 2026 also looked partial). This is a train/score mismatch.
* Keep the one-month data-lag month (already in the cohort file).
* Set a data end per source: the last month whose volume is at least ~95% of the median of the 3 months before it. If a source misses it, shift that view's windows back with `RollingWindow(delay=...)` by one month, and add the completeness flag (F9).
* Document the rule in a new `Alignment_Markdowns/Strategy_and_Execution/NBA_3_1_Data_Lag_Rule.md`. The existing `..._Fill_Missing_and_Lag.md` covers the 3.0 rolling-window step, not data latency.

## 6. Contender view readiness

| View | Features | Source (Track) | Feature Views pattern | Status | Blocker / next step |
| --- | --- | --- | --- | --- | --- |
| V1 Kerendia writing | NBRx, TRx, running totals, time since first Kerendia Rx | NB01 / NB05 output (R) | Register | Needs prep | NBRx = first claim per patient-product-day (stateful), keep in notebooks. Paid-only filter needs `CLAIM_TYPE`. |
| V2 Claim type (F1) | PD / RV / RJ counts, rejection rate; Kerendia, SGLT2s, competitors | `fv_src_rx_claims` (C) | Month bucket + `Sum`; rate after join | Blocked (RV) / Ready (RJ) | Add `CLAIM_TYPE` (and `CLAIM_STATUS`) to the PJ03 pull. RJ can start now via `REJECTION_FLAG`. |
| V3 SGLT2 add-on pool (F7) | SGLT2 patients not on Kerendia, add-on starts | Rx + patient state (C) | Event level + `ApproxCountDistinct` | Needs prep | Patient-level state (on SGLT2, no Kerendia) per month. |
| V4 Calls, V5 Practice | F2F recency, affiliation | Not LAAD | - | Out of scope | Covered by the non-LAAD feature work. |
| V6 Eligible panel | Eligible CKD+T2D / CKD+T1D / HF patients, counts and shares | `pj_pat_sglt2_filter_m` + bridge (C) | Event level + `ApproxCountDistinct` | Blocked | Re-run PJ06 with the C1 fix; write per-indication flags; build the HCP-patient bridge. |
| V7 CKD stage mix | Patients in stage 2 / 3a / 3b / 4 / unknown, shares, stage progression | `pj_pat_new_ckd_stage`, lab `GFR_STAGE`, Dx `DX_STAGE` + bridge (C) | Event level + `ApproxCountDistinct`; progression = stage up within 3 / 6 months | Needs prep | Bridge; stage rule decided in 6.2 (needs eGFR value for 3a / 3b). |
| V8 HF (F2) | HFpEF-proxy patients, HF drugs | `pj_dm_hf_flags` + Rx + bridge (C) | Event level + `ApproxCountDistinct` | Needs prep | Bridge; HFpEF proxy adequacy (open question). |
| V9 T1D + CKD (F3) | E10 + N18 patients | `pull_dx_step4` (`DM_TYPE`, `DX_STAGE`) (C) | Event level + `ApproxCountDistinct` | Ready for pilot | Little history since the Sep 2026 approval. |
| V10 Lab monitoring (F4-F6) | UACR / eGFR testing, potassium tested and high, HbA1c | `pull_lab_step4` (C) | Month bucket + `Sum` (tests); `ApproxCountDistinct` (patients) | Ready after dedup check | Confirm S3 dedup; potassium/HbA1c are LabCorp only (L-A). |
| F9 Completeness | Latest-month volume vs normal, per source | Source monthly counts (C) | `ColumnSelection` on a per-month table | Needs prep | Build after the lag rule. |
| F10 Trends | 3 months vs previous 3 | Any month-bucket view (C) | Two `RollingWindow`s, one with `delay` | Ready with V2 / V10 | - |

Rough size: about 180-250 Track C features across V2, V6-V10 (estimate from filters x windows; to be fixed in the config list).

### 6.1 HCP-patient bridge (needed by V3, V6, V7, V8)

One row per `NPI_NUMBER` x `PATIENT_ID` x month in which the HCP had a Rx, Dx or Lab claim for the patient (from the three pulls), joined to that patient's state in that month (CKD stage, DM type, HF type, eligibility flags, SGLT2 / Kerendia status). Feature: `ApproxCountDistinct(PATIENT_ID)` with a `filter_condition` per state.

Risks: size (the Rx pull alone is 3.28B rows; the bridge is distinct NPI x patient x month, size not measured) and approximate counts (accepted; report `relativeSD` against exact counts on the pilot HCPs).

### 6.2 CKD stage source for V7: lab vs Dx (investigated 2026-11-23)

**How 3.1 builds the stage today (PJ06 cell 4, same as 3.0):** `GFR_UACR_DX_STAGE = coalesce(DX_STAGE_UPDATED, GFR_STAGE, UACR_STAGE)`, i.e. Dx first, then lab eGFR, then UACR. Data: run `full_2026_11_16`, `pj_dx_journey` and `pj_lab_journey`, patient-months 2023-01..2026-09.

**What the data shows**

| # | Check | Result |
| --- | --- | --- |
| 1 | Coverage | Lab journey: 1,739,332,889 patient-months, 64,592,304 patients, eGFR stage on 99%. Dx journey: 493,981,402 patient-months, 16,743,067 patients, stage coded in the month on 95,586,876. |
| 2 | Dx stage is carried forward as the worst stage ever | `DX_STAGE_UPDATED` is never below the stage coded that month (above it in 10,049,217 rows); 302,724,133 of its 384,936,352 values (79%) are carried, not coded that month. |
| 3 | Same-month agreement (Dx coded that month vs lab eGFR stage, 19,385,931 patient-months) | Exact 72.1%, within 1 stage 96.0%; lab lower than Dx 20.3%, higher 7.5%. Eligible band (2-4 vs other) agrees 91.4%. |
| 4 | Carried Dx vs current lab (86,919,304 patient-months) | Exact 66.1%; lab lower 25.9%. Carried Dx 4: lab lower 40.0%. Carried Dx 5: lab lower 54.4%. |
| 5 | Who is right when they disagree? First **actual** eGFR test 3-12 months later (5% patient sample, 280,124 months with both an eGFR test and a coded Dx stage; corrected 2026-11-24) | Lab lower than Dx (34,231): next test = lab 62.7%, = Dx 32.2%. Lab higher (13,239): = lab 60.8%, = Dx 33.0%. Agree (126,066): same stage 82.6%. Lab wins about 2:1. The first version (84-91% vs 7-14%) read the lab journey, which carries the stage forward, so it partly compared a carried value with itself. |
| 6 | Dx unspecified stage (`DX_STAGE_MONTH = 0`, 6,526,613 patient-months with a lab) | Lab gives a stage: 1 = 13.0%, 2 = 31.4%, 3 = 46.5%, 4 = 7.5%, 5 = 1.5%. |
| 7 | Lab-only stage 3 / 4 (no Dx stage) | Stage 3: 6,466,309 patients lab-only vs 3,107,023 with Dx; stage 4: 370,530 lab-only vs 619,163 with Dx. Lab roughly doubles the stage 3 pool. |
| 8 | eGFR stage 1-2 without kidney damage | Lab-only eGFR stage 2: 627,677,388 patient-months (29,107,725 patients), only 24,686,952 (3.9%) with UACR >= 30 mg/g. Stage 1: 2.6% with UACR >= 30. In the current rule these months get stage 2 (eligible band). |

**Recommended rule for V7 (current stage per patient-month)**

1. **Lab first:** latest eGFR stage within the last 12 months, with 3a (45-59) / 3b (30-44) split from the eGFR value (`MEDIAN_TEST_RESULT` in the lab pull; the journey `GFR_STAGE` has stage 3 only).
2. **eGFR 60+ (stage 1-2) is CKD only with kidney-damage evidence:** UACR >= 30 mg/g in the last 12 months or an N18 Dx code; otherwise "no CKD evidence", not stage 2.
3. **Dx fallback:** if no lab in the last 12 months, the latest stage **coded** in the last 12 months (`DX_STAGE_MONTH`), not the worst-ever `DX_STAGE_UPDATED`.
4. **Unspecified Dx (N18.9, stage 0):** lab stage if available, else "unknown".
5. **Stage 5:** a lab stage 5, dialysis (Px) or a Dx stage 5 coded in the last 12 months with no later better lab.
6. **Extra feature (optional):** "confirmed stage" = two labs at least 90 days apart in the same stage (KDIGO persistence).

V7 features then count patients per HCP by this stage: 2, 3a, 3b, 4, 5, unknown, plus stage source (lab / Dx) as a quality split.

**Caveats:** the lab journey (PJ01 cell 29) carries `GFR_STAGE` / `UACR_STAGE` forward month by month with no time limit (5% sample: 86,161,823 journey months with an eGFR stage vs 8,375,158 months with an actual eGFR test in the lab pull), so checks 1, 4, 7 and 8 count carried months, not test months. Check 5 compares lab with lab, so it partly measures the stability of eGFR itself. Lab covers Quest and LabCorp only, and LabCorp history before mid-2025 is thinner (L-C, L-D), so the Dx fallback is needed and lab coverage varies by HCP. How PJ01 picks one `GFR_STAGE` per month was not checked.

**Impact beyond V7 (not changed here):** the PJ06 eligibility stage uses the same Dx-first rule; tested in 6.3.

### 6.3 Test of the new stage rule on eligibility (2026-11-24, 5% patient sample)

**Method.** Rebuilt the PJ06 spine and flags (cells 4-6, current code with the C1 fix) from the `full_2026_11_16` journey tables for a 5% patient sample (`abs(hash(PATIENT_ID)) % 20 = 0`). Check: 206,159,007 patient-months, current stage equal to the stored `pj_pat_sglt2_filter_m` stage on 100% of them. Then replaced the stage with the 6.2 rule built from **actual tests** (lab pull: eGFR and UACR >= 30 per patient-month) and **coded** Dx (Dx pull: stage 1-5, any N18), 12-month lookback. Everything else (DM type, SGLT2 rule, dialysis, HF) unchanged. Two variants for eGFR 60+ without damage evidence: **A** = not CKD (not eligible), **B** = stage unknown (SGLT2 rule can still admit).

| Measure (sample) | Current | New A | New B |
| --- | --- | --- | --- |
| Eligible patient-months | 38,074,590 (18.5%) | 28,854,563 (-24.2%) | 31,837,057 (-16.4%) |
| CKD + T2D | 34,518,913 | 24,954,876 (-27.7%) | 28,013,675 (-18.8%) |
| CKD + T1D | 381,757 | 230,544 (-39.6%) | 245,698 (-35.6%) |
| HF | 5,094,965 | 5,122,211 (+0.5%) | 5,122,211 (+0.5%) |
| Patients ever eligible (of 7,543,020) | 1,312,649 | 1,072,974 (-18.3%) | 1,080,751 (-17.7%) |
| Eligible in Sep 2026 (of 5,718,988) | 1,045,277 | 714,781 (-31.6%) | 796,752 (-23.8%) |

**Why patient-months move (A vs current).** Lost 10,013,837, gained 793,810 (net matches the table):

* eGFR 60+ without UACR >= 30 or N18 in 12 months (current stage 2 / 3 / 4): 6,483,112 (65%), mostly current stage 2 (6,359,619).
* No lab or coded Dx stage in the last 12 months, current stage carried (2: 2,017,450; 3: 1,251,121; 4: 166,475), no SGLT2: 3,435,046 (34%).
* New stage 1 or 5: 95,679.
* Gained: lab stage 2-4 replaces a carried Dx stage 1 or 5, or an unknown stage.

**The 77% in the stored table** (section 4) is not the current code: on the same sample the stored flag is 1 on 158,641,272 of 206,159,007 patient-months (77%), while the current PJ06 code gives 18.5%. The stored table was written by an earlier code version (it has no per-indication columns), so the 77% goes away with the re-run.

**Reading.** The new rule cuts the eligible pool by about a fifth of patients (-18%) and a third of the latest month (-24% to -32%). Most of the cut is people with normal eGFR and no albuminuria evidence, plus stages carried for more than 12 months without new evidence. HF is unaffected. Variant B keeps about 3M more patient-months, through SGLT2 users with normal eGFR.

**Limits.** One run, 5% sample (scale x20 only as a rough guide). Lab tests come from the NPI-matched lab pull, which may hold fewer tests than PJ01 uses. UACR testing is rare, so missing UACR is not proof of no albuminuria (the case for variant B). The 12-month lookback is a parameter, not tested at other lengths. No HCP-level or model impact measured.

## 7. Work plan

| Phase | Work | Done when |
| --- | --- | --- |
| 0. Environment | Grant `CREATE FEATURE` / `READ FEATURE` on `kerendia_nba_3_1` to the job service principal; pin `databricks-feature-engineering` on the job compute; add the naming config (5.3). | The job principal creates and reads one `fv_` feature in `kerendia_nba_3_1`. |
| 1. Source prep | Stable `fv_src_*` tables per full run: Rx (with `CLAIM_TYPE`), Dx, Lab (deduped), month-bucket count tables, the HCP-patient bridge (after the PJ06 re-run with C1). Write `NBA_3_1_Data_Lag_Rule.md`. | Row counts reconcile to the pulls; 0 null keys; no duplicates on the declared grain; monthly completeness table per source. |
| 2. Pilot and parity | V9 + V2 (RJ) + V10 (one test). Compare month-bucket `Sum` with calendar-month counts on the 9 test HCPs x 28 cohorts; compare `ApproxCountDistinct` with exact distinct. | Counts: 100% match. Distinct: approximate error reported (accepted). Run time measured at full size. |
| 3. Build | V2 (all types), V6, V7, V10, then V8, V3, F9, F10, all from one config list. | Each view: null / zero rate, value range and correlation with existing features reported. |
| 4. Feature selection hand-off | `create_training_set` on the label spine; join with Track R features on `NPI_NUMBER` + cohort; export to the `_sm` feature selection notebooks. | Selection run includes the new views; SHAP share per view reported. |
| 5. Track R | Register the NB01-NB06 outputs of the next full run as time-series feature tables. | `create_table` works at full width (4,677 columns for NB01); training-set values match the tables. |
| 6. Operate | Monthly job: source prep, then training set or `score_batch` for scoring. Materialization and online store only if real-time serving is needed. | One monthly run end to end. |

Suggested order: Phase 0 and the `CLAIM_TYPE` / PJ06 re-runs in parallel, then the pilot on what is ready (V9, V2-RJ, V10), then V2-RV, V6, V7.

## 8. Open questions

1. ~~Target schema~~: decided, `kerendia_nba_3_1`. Still open: who grants `CREATE FEATURE` to the job service principal.
2. Can one `create_training_set` call take both Feature Views (`features=`) and Track R feature tables (`feature_lookups=`)? If not, build two training sets and join them on keys (to test in Phase 2).
3. Can a `DeltaTableSource` point at a view, or must the stable sources be tables? (To test.)
4. ~~Approximate distinct counts~~: decided, accepted.
5. ~~Lab vs Dx precedence for CKD stage~~: confirmed 2026-11-24 (Wenjie); roll-out in `../06_CKD_Stage/NBA_3_1_CKD_Stage_Readiness_Plan.md`.
6. `PROVIDER_ID` to `NPI_NUMBER` mapping for the universe (O2).
7. ~~77% eligible patient-months~~: explained, earlier code version; current code gives 18.5% (6.3). Re-run PJ06 to replace the table.
8. ~~PJ06 eligibility stage~~: decided 2026-11-24 (Wenjie), variant B, implemented as C11 in PJ06 cell 2b (`CKD_STAGE_31`; `CKD_STAGE_RULE = "3.0"` restores the old stage). Cell code reproduced the 6.3 variant B numbers exactly on the 5% sample. Not yet run in PJ06; next full run writes it.

## 9. What was checked and what was not

**Checked (2026-11-23):** table list and column types in `kerendia_nba_3_1` and `nba_fv_test`; row counts, service-date range, null `NPI_NUMBER` and category values of the pulls and patient-state tables listed in section 4; the cohort file (28 cohorts, dates, datasets); the team's Test A-D results and recommendation; the safe window durations in 5.2 (calendar arithmetic); the CKD stage checks in 6.2 (PJ06 stage code read; full-table counts, follow-up check on a 5% patient sample, redone with actual tests); the eligibility test in 6.3 (PJ06 rebuild matched the stored stage on 100% of 206,159,007 sample patient-months; lost / gained reconciles to the variant A total).

**Not checked:** the month-bucket method inside Feature Views; `ApproxCountDistinct` accuracy; full-size performance; bridge size; whether the lab pull is already deduped for S3; row counts of `pj_dm_hf_flags`, `pj_px` and `input_hcp_universe`; `create_table` at full width; online serving; `fe.log_model`.
