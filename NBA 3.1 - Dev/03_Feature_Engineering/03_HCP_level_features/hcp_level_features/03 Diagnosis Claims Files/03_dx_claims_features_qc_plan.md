# QC plan 03: HCP monthly Dx claims features, NBA 3.1

**Purpose:** plan the QC of the HCP-month Dx feature notebook `03_claim_diagnosis_monthly_cohort` (run `full_2026_11_16`). The QC result goes in `03_dx_claims_features_qc.md` in this folder and follows `../00_qc_template.md` (Q1 to Q14, sections 1 to 11).  
**Rule source:** `../Feature_Evaluation/05_Feature_Views/NBA_3_1_LAAD_Feature_Views_Readiness_Plan.md` ("readiness"), section 6 (contender view readiness) and the Dx rows of sections 4, 5.4 and 6.2. Section 7 (work plan) is out of scope: no new features, no Feature Views objects.  
**Developer rules:** `NBA_3_1_Dx_Claims_Features_Plan.md`, `NBA_3_1_Dx_Claims_Features_Client_Summary.md`, `NBA_3_1_HCP_Features_Decisions.md` (X1 to X24).  
**Mode:** read-only. No notebook is re-run (a re-run overwrites the outputs); no table is changed. Evidence = numbers from read-only queries on the written tables.  
**Date:** 2026-11-27

---

## 1. Lineage under QC

Names below are the names found in the workspace; two differ from the task brief.

| Step | Asset (actual name) | Role | Brief said |
| --- | --- | --- | --- |
| PJ02 Dx journey | `Patient_Journey_Validation/Dx Files/02_patient_journey_dx` + `NBA_3_1_Dx_Journey_Plan.md`, `NBA_3_1_Dx_Journey_Client_Summary.md` | Dx pull (Step 4: NPI x patient x day x code, stage by code) and patient-month Dx journey | `03_patient_journey_dx` |
| PJ06 combine | `Patient_Journey_Validation/Combine Files/06_patient_journey_combine_3_1` | Patient-month table `pat_new_ckd_stage` (stage the patient is new to) | same |
| NB03 HCP features | `hcp_level_features/03 Diagnosis Claims Files/03_claim_diagnosis_monthly_cohort` (37 cells) | Joins Dx pull with `pat_new_ckd_stage`, aggregates to NPI x cohort | `01_claim_dx_monthly_cohort` |

Note: the brief says "prescription based features" for the Dx journey; the QC treats it as the Dx journey.

## 2. What was found during planning (read-only, 2026-11-27)

| Item | Value |
| --- | --- |
| NPI output | `kerendia_nba_3_1.full_2026_11_16_hcp_claim_diagnosis_monthly_cohort`: 7,588,208 rows, 282,971 NPIs, 28 `COHORT_ID`, `PULL_DT` 2026-11-17, `CUTOFF_DATE` 2024-05-31 .. 2026-08-31 |
| Provider output | `full_2026_11_16_hcp_provider_claim_diagnosis_monthly_cohort`: 7,588,997 rows, 282,975 `PROVIDER_ID`, 28 cohorts |
| Columns | `NPI_NUMBER`, 113 features (4 windows x {total, 6 Dx stages, 6 patient stages}, 13 `RUNNING_`, 48 `PCT_`), 8 metadata (`COHORT_ID`, `COHORT_MONTH`, `OFFSET_DAYS`, `CUTOFF_DATE`, `SVC_DT_M`, `PULL_DT`, `DATASET`, `COHORT_SET`) |
| Dx input | `full_2026_11_16_pull_dx_step4`: 475,010,310 rows, 2023-01-01 .. 2026-09-30 (readiness section 4) |
| Patient input | `full_2026_11_16_pj_pat_new_ckd_stage` (4.12B patient-months, readiness section 4); exact path NB03 reads via `get_patient_table_path("new_ckd_stage")` to confirm |
| Universe / cohorts | `input_hcp_universe`; `input_claims_cohorts` (28 cohorts, offset 0) |

Points Q1 must explain: 282,971 x 28 = 7,923,188 > 7,588,208 rows (NPIs missing in some cohorts, e.g. no Dx before the cohort), and provider rows > NPI rows (+789: one NPI with several `PROVIDER_ID`s; the client summary reports 698 null `PROVIDER_ID` and 675 second copies on the 2026-11-04 run).

## 3. Section 6 of the readiness: what applies to NB03 (Dx)

| View | Dx link | How it is checked in the QC | Expected status |
| --- | --- | --- | --- |
| V7 CKD stage mix | Uses Dx `DX_STAGE` and `pj_pat_new_ckd_stage`; 6.2 says Dx stage is carried forward as worst-ever (`DX_STAGE_UPDATED`) and recommends lab first, Dx coded-in-12-months as fallback | Q6: NB03 counts claims by the stage **coded on the claim** (`DX_STAGE` of the pull), not the carried stage; patient-stage features read `NEW_CKD_STAGE` built by PJ06 with the current (Dx-first, 3.0) rule, C11 / `CKD_STAGE_31` not yet in the run. Check `CKD_SUBSTAGE` (3a / 3b / ESRD only) is not used for features. Q5: no 3a / 3b split exists in NB03 | Rule documented; V7 itself not built (section 7) |
| V9 T1D + CKD | `pull_dx_step4` `DM_TYPE`, `DX_STAGE`; D5: T1D kidney codes E10.21/22/29 kept as stage unspecified | Q6 / Q11: count T1D rows in the pull and their share in `STAGE_UNSPECIFIED`; confirm decision "T1D codes kept" (client summary update) | PASS if counted as documented |
| F9 completeness | Readiness 5.4: newest month thin (raw Dx Oct 2026 79.6M vs 98-109M) | Q14: monthly row counts of the pull Jul 2025 .. Sep 2026 vs the 95%-of-median rule; last cohort (lag Sep 2026) affected? | Report, owner NBA team |
| F10 trends | 3 months vs previous 3 | Q5: NB03 has no trend / DIFF columns | N/A (not in NB03), noted |
| V2, V10 | Rx claim type, lab | Not Dx | N/A |
| V3, V6, V8 | Patient state + bridge (SGLT2, eligibility, HF) | Not in NB03 | N/A with reason |
| Section 4 Dx row | Pull ready, 0 null NPI, `SVC_DT` DATE | Q4: rows, null NPI, date range, null `DX_STAGE` (notebook asserts 0) | PASS if same |

## 4. How the template is adapted for Dx

* **Rule file:** readiness (sections 4, 5.4, 6, 6.2) replaces `60_ftp_copay_nba_3_1_readiness_plan.md`.
* **Grain (Q1):** NB03 writes one row per `NPI_NUMBER` x `COHORT_ID` (and provider version per `PROVIDER_ID`), only for NPIs with Dx data, so "universe x 28" is checked as "output NPIs within universe, explained gap".
* **Q3:** window end E = `CUTOFF_DATE` (offset 0 = last day of the lookback month); claim counted if `SVC_DT` in (E - N months, E]; `RUNNING_` from `DATA_START_DATE` 2023-01-01. No `INSERT_TS` in the pull: load-date point-in-time is not testable, noted with readiness 5.4.
* **Q8 / Q9:** NBA 3.0 104 Dx features (`03_claim_diagnosis_monthly`) vs 3.1 113 (+9 `STAGE_5`); 752 xlsx for SHAP; 3 NB03 features in the selected-277 list.
* **Q12:** 3.0 `provider_claim_diagnosis_monthly` (closest month) vs 3.1 c28 on common HCPs.
* **Q14:** Dx code basket in the pull (31 codes) vs the PJ02 config list; per `DATASET` active HCPs and 12M Dx claims vs training.

## 5. Steps

| # | Step | Checks | Done when |
| --- | --- | --- | --- |
| 1 | Read rule and context sources: readiness 4, 5.4, 6, 6.2, 9; Dx Claims plan + summary; Dx Journey plan + summary; PJ06 cells writing `pat_new_ckd_stage`; NB03 cells 7, 16-18, 21, 25, 28-30; `00_cohort_config` (`HCP_DX_SOURCE`, `HCP_DX31_PULL_TABLE`, table naming, windows) | - | Each Q has its rule source noted |
| 2 | Fill template sections 1 and 2 | - | Paths, counts and Dx-specific How / Pass-when filled |
| 3 | Universe and grain | Q1 | Distinct keys, rows per cohort, duplicates on NPI x cohort, NPIs outside universe, null / placeholder `PROVIDER_ID`, gap and fan-out explained |
| 4 | Cohorts, windows, sources | Q2, Q3, Q4 | Output cohort fields = `input_claims_cohorts` (0 mismatches); no claim after E; edge days (E in, E+1 out); sources vs readiness section 4 |
| 5 | Features and rules vs section 6 | Q5, Q6 | Output columns vs plan families (C3 fixed pivot, `STAGE_5`, `PCT_`, `RUNNING_`); V7 / V9 / F9 / F10 rows of section 3 above documented |
| 6 | Fill rate | Q7 | All 113 features: % null, % zero, % non-zero, min / max; all, train, test, holdout, c28; flags (constant, > 99.5% zero, train vs holdout > 5 points) |
| 7 | NBA 3.0 map | Q8, Q9 | Each 3.0 Dx feature mapped (preserved / replaced / dropped / new); OPEN if xlsx unreadable |
| 8 | HCP trace and invariants | Q10, Q11 | 5-6 NPI x cohort cases recomputed from `pull_dx_step4` + `pat_new_ckd_stage` (high volume 1841364841, stage 5 heavy, T1D code, window edge, no claims in window, training cohort); invariants: 1 <= 3 <= 6 <= 12 months, stage sum = total, patient-stage sum = total, `PCT_` = count / total (null or 0 when total 0), `RUNNING_` >= 12M, no negatives |
| 9 | 3.0 comparison, reproducibility, drift | Q12, Q13, Q14 | Spearman and totals vs 3.0; `PULL_DT`, writer job / Delta history, stale text in header and docs (e.g. "20 cohorts, offset 7"); code basket and drift per `DATASET` |
| 10 | Write `03_dx_claims_features_qc.md` | All | All 11 template sections filled, findings with severity, sign-off n / 14 |
| 11 | Verify the QC file | - | Re-read against template; re-run 3 queries to spot-check numbers; confirm no notebook or table changed |

## 6. Open points for the user

1. Notebook names: QC uses the real names `02_patient_journey_dx` and `03_claim_diagnosis_monthly_cohort` (brief: `03_patient_journey_dx`, `01_claim_dx_monthly_cohort`).
2. Output file name: `03_dx_claims_features_qc.md` (same numbering as the Rx QC `01_rx_claims_features_qc.md`).
3. Sign-off: "QC by / date" filled; reviewer and NBA-team drift sign-off left blank.
