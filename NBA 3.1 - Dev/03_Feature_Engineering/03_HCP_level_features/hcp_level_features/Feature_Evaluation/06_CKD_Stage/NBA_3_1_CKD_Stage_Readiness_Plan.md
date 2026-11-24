# CKD Stage: NBA 3.1 Readiness Plan

**Group:** LAAD patient-state features (CKD stage for eligibility and for HCP features)  
**Purpose:** a step-by-step plan to turn the confirmed 3.1 CKD stage rule into a validated patient-month stage, a corrected eligibility flag and a tested HCP feature block (V7)  
**Builds on:** `../05_Feature_Views/NBA_3_1_LAAD_Feature_Views_Readiness_Plan.md` (sections 6.2 stage investigation, 6.3 eligibility test), `../01_Source_Review/NBA_3_1_Dx_Source_Review.md`, `../../../Patient_Journey_Validation/Lab Files/NBA_3_1_Lab_Data_Learnings_and_3_0_Review.md`, `../04_Feature_Ideas/NBA_3_1_HCP_Feature_Ideas_Draft.md`  
**NBA 3.1 notebooks concerned:** PJ01 `01_patient_journey_labs`, PJ02 Dx journey, PJ06 `06_patient_journey_combine_3_1` (C11 in cell 2b); HCP notebooks NB03 (`pat_new_ckd_stage`), NB04 families A / C (`pat_gfr_dx_stage`, `pat_uacr_stage`), NB06 (`pat_sglt2_filter_m`), as mapped in `00_cohort_config` (`HCP_PATIENT_TABLES`)  
**Status:** draft for discussion  
**Date:** November 24, 2026 | **Owner:** Wenjie Chen | **Branch:** `combine` (`kerendia_nba_3_1_develop_pg`)

**Decisions confirmed (2026-11-24, Wenjie):**

* **D1 Stage rule:** lab first (latest eGFR test in the last 12 months), eGFR 60+ counts as CKD only with damage evidence (UACR >= 30 mg/g or an N18 code), coded Dx stage of the last 12 months as fallback (not the worst stage ever), unknown otherwise. Applies to eligibility and to the V7 features.
* **D2 Eligibility variant B:** eGFR 60+ without damage evidence = stage unknown, so the SGLT2 rule can still admit the patient. Implemented as C11 in PJ06 cell 2b (`CKD_STAGE_31`, switch `CKD_STAGE_RULE`, default `3.1`). Not yet run in a pipeline.

## 1. Scope

| In scope | Out of scope (owned elsewhere or pending) |
| --- | --- |
| **Patient-month CKD stage** (1, 2, 3a, 3b, 4, 5, no CKD evidence, unknown) from actual tests and coded Dx | Changing the lab or Dx pulls themselves (PJ01 / PJ02 step 4), except adding a test-month flag (K3) |
| **Eligibility stage** in PJ06 (C11, variant B) and its effect on `ELIGIBLE_*` flags | Diabetes type (C2) and HFpEF proxy rules: separate open points |
| **HCP CKD stage features (V7)**: patients per stage, shares, progression, stage source, via the HCP-patient bridge | The bridge build itself (FV plan 6.1), only its use here |
| **Downstream switch** of NB03 / NB04 stage tables to the 3.1 stage (decision after E2) | Lab testing features without a stage (V10, F4-F6) |
| Experiments to judge model value | Clinical validation beyond what claims and labs show |

## 2. Goal and how we will judge success

**Goal.** Replace the NBA 3.0 stage, which is the worst Dx stage ever coded with an indefinitely carried lab stage behind it, by a stage that reflects **current evidence**, does not call normal eGFR without damage "CKD stage 2", and is used the same way in eligibility and in the HCP features.

| # | Criterion | How it is measured |
| --- | --- | --- |
| S1 | **Rule reproduced in the pipeline** | PJ06 run with C11 gives the 6.3 variant B shape: eligible patient-months about -16%, eligible patients about -18%, HF about unchanged vs `CKD_STAGE_RULE = "3.0"` on the same run |
| S2 | **No stale stage** | 0 patient-months with a stage whose last evidence is more than `CKD_LOOKBACK_MONTHS` old |
| S3 | **Stage source known** | Every patient-month has `CKD_STAGE_31_SRC` in (lab, dx, none) |
| S4 | **3a / 3b split** | Stage 3 split by eGFR value (lab) or `CKD_SUBSTAGE` (Dx); share of stage 3 without a split reported |
| S5 | **Stable schema** | Same V7 column list every run, from one config (stages x windows) |
| S6 | **Model value** | E2 (new stage features) not worse than E0 on the 3.1 validation metric; SHAP share of V7 reported |

## 3. Starting point (NBA 3.0 logic, still in 3.1 apart from C11)

All numbers: run `full_2026_11_16`, patient-months 2023-01..2026-09; details in the FV plan, 6.2-6.3.

| What 3.0 does | Problem | Evidence |
| --- | --- | --- |
| `GFR_UACR_DX_STAGE = coalesce(DX_STAGE_UPDATED, GFR_STAGE, UACR_STAGE)` (Dx first) | Dx wins even when a newer lab says otherwise | Carried Dx vs current lab (86.9M patient-months): exact 66.1%, lab lower 25.9%; carried Dx 5: lab lower 54.4% |
| `DX_STAGE_UPDATED` = worst stage ever | Never goes down; 79% of its values are carried, not coded that month | 302,724,133 of 384,936,352 values carried |
| Lab journey carries `GFR_STAGE` / `UACR_STAGE` forward with no limit (PJ01) | Journey months are not test months | 5% sample: 86,161,823 journey months with an eGFR stage vs 8,375,158 months with an actual eGFR test |
| eGFR 60+ alone gives stage 1-2 | Normal kidney function counted as CKD | Lab-only eGFR stage 2: only 3.9% of patient-months with UACR >= 30; stage 1: 2.6% |
| SGLT2 rule compared stage to -1 | Never true, so the rule never applied | Fixed as C1 (2026-11-23) |
| Stored `pat_sglt2_filter_m` | Written by an earlier code version | Flag = 1 on 77% of patient-months; current code gives 18.5% on the 5% sample |
| Journey `GFR_STAGE` has stage 3 only | No 3a / 3b in the lab path | Lab pull stage 3 rows: 15,284,530 with eGFR >= 45, 6,525,421 below 45 (split possible from `MEDIAN_TEST_RESULT`) |

Who is right when lab and Dx disagree (first actual eGFR test 3-12 months later, 5% sample): the later test matches the lab about 61-63% of the time, the Dx stage about 32-33%.

## 4. Design principles

1. **Evidence, not memory.** A stage needs a test or a code in the last `CKD_LOOKBACK_MONTHS` (default 12) months; no stage is carried beyond that.
2. **Lab first.** The latest eGFR test sets the stage; a Dx stage 5 coded after it wins (stage 5 / dialysis exclusion).
3. **Damage required for eGFR 60+.** Stage 1-2 only with UACR >= 30 mg/g or an N18 code in the window.
4. **Unknown is a value.** "No CKD evidence" (eGFR 60+ without damage) and "unknown" (no evidence) are kept apart in features; eligibility treats both as unknown (variant B).
5. **One rule, two uses.** Eligibility and V7 read the same patient-month stage table.
6. **Source kept.** Every stage carries its source and age, so features and checks can split lab vs Dx.
7. **Switchable.** `CKD_STAGE_RULE = "3.0"` reproduces the old stage for comparison runs until the gates pass.
8. **Fixed schema.** V7 columns generated from one config of stages and windows; missing combinations filled with 0.

## 5. Target data model

```
ckd_evidence_month   (patient x calendar month with a test or code)
  eGFR stage and value (worst test of the month), UACR >= 30 flag, coded Dx stage 1-5, CKD_SUBSTAGE, N18 flag
        |
ckd_stage_month      (patient x spine month, PJ06)
  CKD_STAGE_31 (1, 2, 3a, 3b, 4, 5, NO_CKD_EVIDENCE, UNKNOWN), source (lab / dx / none),
  months since evidence, confirmed flag (two eGFR tests >= 90 days apart, same stage)
        |                                   |
  eligibility (PJ06 cell 4, variant B)    HCP-patient bridge -> V7 HCP features (patients per stage)
```

Today (C11) cell 2b builds `CKD_STAGE_31` as an integer 1-5 with null for both no-CKD-evidence and unknown, without the 3a / 3b split. Phase 1 adds the rest.

## 6. Work plan

Each phase ends with a gate (section 8).

### Phase 0: Validation (blocking)

| ID | Task | Detail | Owner |
| --- | --- | --- | --- |
| K1 | Validation run | Run PJ06 in validation mode with C11 and with `CKD_STAGE_RULE = "3.0"`; compare eligible counts per indication | NBA team |
| K2 | Full run | Next full patient-journey run writes `pat_sglt2_filter_m` with `CKD_STAGE_31`; replaces the 77% table; reconcile with 6.3 (S1) | NBA team |
| K3 | Lab coverage | The step-4 pulls hold tests of NPI-matched HCPs in the 3.1 HCP universe only. Add a test-month flag (or last test date) to the PJ01 output so the stage can use every test; measure the difference | NBA team |
| K4 | Lookback sensitivity | Compare 6, 12 and 24 months on the 5% sample (eligible counts, stage mix) | NBA team |
| K5 | UACR testing rate | Share of patients and of HCPs with any UACR in 12 months; decides how much "no CKD evidence" means "not tested" | NBA team |
| K6 | 3a / 3b split | Lab: eGFR 45-59 = 3a, 30-44 = 3b. Dx: `CKD_SUBSTAGE` (pull: stage 3 rows 24,512,925 3a, 20,661,766 3b, 20,323,915 unspecified). Report unsplit share | NBA team |
| K7 | Stage 5 and dialysis | Check stage 5 (lab / Dx) against `FIRST_DIALYSIS_DATE`; both exclude from eligibility | NBA team |
| K8 | PJ01 monthly pick | Confirm how PJ01 picks one eGFR per patient-month (worst vs latest) and align the rule | NBA team |

### Phase 1: Patient-month stage table (PJ06 extension)

| ID | Item | Detail |
| --- | --- | --- |
| P1 | Substage | 3a / 3b from eGFR value or `CKD_SUBSTAGE` (K6) |
| P2 | Two unknown classes | `NO_CKD_EVIDENCE` vs `UNKNOWN` as separate values; eligibility unchanged (variant B) |
| P3 | Source and age | `CKD_STAGE_31_SRC` (exists), months since last evidence |
| P4 | Confirmed stage | Two eGFR tests >= 90 days apart in the same stage (KDIGO persistence), optional flag |
| P5 | Progression event | Stage worse than 3 / 6 months earlier, both from evidence |
| P6 | Write | New stage table (or columns in `pat_sglt2_filter_m`) in the run folder |

### Phase 2: HCP features (V7)

Via the HCP-patient bridge, `ApproxCountDistinct(PATIENT_ID)` per stage filter; windows 3 and 12 months; shares after the training-set join. Names follow the FV plan naming (`fv_ckd_*`).

| ID | Family | Example names | Approx. count |
| --- | --- | --- | --- |
| H1 | Patients by stage | `fv_ckd_pts_stage_3a_12m`, `fv_ckd_pts_stage_4_3m`, `fv_ckd_pts_no_ckd_evidence_12m` | 16 |
| H2 | Stage shares | `fv_ckd_share_stage_3b_plus_12m` | 4-6 |
| H3 | Progression | `fv_ckd_pts_progressed_6m` | 2 |
| H4 | Source and quality | `fv_ckd_share_lab_source_12m`, `fv_ckd_pts_confirmed_stage_12m` | 3-4 |
| H5 | Stage among Kerendia-relevant patients | stage 3-4 among SGLT2 users / eligible patients | 4-6 |

Candidate set: about 30 to 35 columns.

### Phase 3: Downstream switch

| ID | Item | Detail |
| --- | --- | --- |
| R1 | NB06 | Reads `pat_sglt2_filter_m`; picks up C11 at the next full run, no code change |
| R2 | NB03 / NB04 | `pat_new_ckd_stage`, `pat_gfr_dx_stage`, `pat_uacr_stage` still use the 3.0 stage; switch only if E2 shows no loss |
| R3 | NB01-NB06 re-run | After the PJ06 re-run (open point O12) |

## 7. Experiments

| ID | Setup | Question |
| --- | --- | --- |
| E0 | Baseline: 3.0 stage everywhere (`CKD_STAGE_RULE = "3.0"`) | Reference |
| E1 | C11 eligibility only | Effect of the smaller eligible pool on eligible-panel features and metric |
| E2 | E1 + V7 features | Do current-evidence stage features add value? |
| E3 | E2 with NB03 / NB04 on the 3.1 stage | Can the 3.0 stage tables be retired? |
| E4 | E2 with 6 / 24 month lookback | Lookback choice |

## 8. Gates

| Gate | Passes when |
| --- | --- |
| G0 | K1, K2 done; S1-S3 met on the full run |
| G1 | Phase 1 table: S2, S4 met; 0 duplicate patient-months |
| G2 | V7 built: S5 met; null / zero rate and correlation with existing stage features reported |
| G3 | E0-E2 done: S6 met; decision on R2 |

## 9. Decisions and open questions

**Decisions:** D1 and D2 above (2026-11-24). D3 (proposed): V7 keeps `NO_CKD_EVIDENCE` and `UNKNOWN` apart.

| # | Open question | Owner |
| --- | --- | --- |
| Q1 | Accept that the stage only sees tests of 3.1-universe HCPs until K3 is done? | NBA team |
| Q2 | Lookback 12 months final after K4? | NBA team |
| Q3 | Should "confirmed stage" (P4) replace the single-test stage for eligibility? | NBA team, medical |
| Q4 | Retire the 3.0 stage tables in NB03 / NB04 (R2)? | NBA team after E3 |
| Q5 | Does the smaller eligible pool need sign-off from brand / field before scoring? | Brand team |

## 10. What was checked and what was not

**Checked (2026-11-23/24):** PJ06 stage and eligibility code; the 6.2 / 6.3 analyses (5% sample, full-table counts); C11 cell code reproduced the 6.3 variant B counts exactly on the sample (31,837,057 eligible patient-months); coded Dx stage in the Dx journey equals the Dx pull (3,603,433 / 3,603,433 sample patient-months); eGFR value ranges per lab stage and Dx substage counts in the pulls; which HCP notebooks read the PJ06 tables (`00_cohort_config`).

**Not checked:** C11 in a pipeline run; tests outside the HCP-universe pulls; lookbacks other than 12 months; how NB03 / NB04 use the stage columns in detail; model impact.
