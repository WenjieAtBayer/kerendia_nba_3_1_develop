# QC plan 02: HCP monthly Lab claims features, NBA 3.1

**Purpose:** plan the QC of the HCP-month Lab feature notebook `02_claim_lab_monthly_cohort` (run `full_2026_11_16`). The QC result goes in `02_lab_claims_features_qc.md` in this folder and follows `../00_qc_template.md` (Q1 to Q14, sections 1 to 11).  
**Rule source:** `../Feature_Evaluation/05_Feature_Views/NBA_3_1_LAAD_Feature_Views_Readiness_Plan.md` ("readiness"), section 6 (contender view readiness) and the Lab rows of sections 4, 5.3, 5.4 and 6.2. Section 7 (work plan) is out of scope: no new features, no Feature Views objects.  
**Developer rules:** `NBA_3_1_Lab_Claims_Features_Plan.md`, `NBA_3_1_Lab_Claims_Features_Client_Summary.md`, `NBA_3_1_HCP_Features_Decisions.md` (X13 to X24).  
**Mode:** read-only. No notebook is re-run (a re-run overwrites the outputs); no table is changed. Evidence = numbers from read-only queries on the written tables.  
**Date:** 2026-11-27

---

## 1. Lineage under QC

| Step | Asset | Role |
| --- | --- | --- |
| PJ01 Lab journey | `Patient_Journey_Validation/Lab Files/03_patient_journey_labs` + `NBA_3_1_Lab_Journey_Plan.md`, `NBA_3_1_Lab_Journey_Client_Summary.md` | Step 4 writes `full_2026_11_16_pull_lab_step4`: one row per NPI x patient x day x test, with `GFR_STAGE` / `UACR_STAGE` |
| PJ06 combine | `Patient_Journey_Validation/Combine Files/06_patient_journey_combine_3_1` | Writes `pj_pat_sglt2_filter_m` (`ELIGIBLE_PATIENT_FLAG` per patient-month) |
| NB02 HCP features | `hcp_level_features/02 Lab Claims Files/02_claim_lab_monthly_cohort` (37 cells) | Cells 8-23: GFR / UACR test counts by test and stage (1 / 3 / 6 / 12 months, `RUNNING_`, `PCT_`). Cell 25: potassium / HbA1c patient-month flags, all patients and eligible patients only (X18), eligibility from `get_patient_table_path("sglt2_filter_m")` |

Note to the brief: NB02 does not join the combine output for every feature. Only the 24 `ELIGIBLE_PATIENTS` columns use PJ06; the other features read the lab pull alone.

## 2. What was found during planning (read-only, 2026-11-27)

| Item | Value |
| --- | --- |
| NPI output | `kerendia_nba_3_1.full_2026_11_16_hcp_claim_lab_monthly_cohort`: 5,165,946 rows, 199,122 NPIs, 28 `COHORT_ID`, `PULL_DT` 2026-11-17, `CUTOFF_DATE` 2024-05-31 .. 2026-08-31, 152 columns (143 features + 9 metadata) |
| Provider output | `full_2026_11_16_hcp_provider_claim_lab_monthly_cohort`: 5,166,454 rows, 199,149 `PROVIDER_ID` |
| Lab input | `full_2026_11_16_pull_lab_step4`: 307,461,581 rows (= readiness section 4), 2023-01-01 .. 2026-09-30. GFR 174.6M rows / 198,843 NPIs; UACR 32.9M / 151,202; POTASSIUM 61.6M / 162,988; HBA1C 38.4M / 144,807 |
| Patient input | `full_2026_11_16_pj_pat_sglt2_filter_m` (readiness section 4: written by an earlier code version, 77% eligible patient-months vs 18.5% with current code) |
| Universe / cohorts | `input_hcp_universe`; `input_claims_cohorts` (28 cohorts, offset 0) |

Points Q1 must explain: 199,122 x 28 = 5,575,416 > 5,165,946 rows (an NPI gets a row only once it has a GFR / UACR test up to the cutoff); provider rows > NPI rows (+508, NPI to `PROVIDER_ID` fan-out); NPIs with only potassium / HbA1c tests (flag features are added to existing rows only).

## 3. Section 6 of the readiness: what applies to NB02 (Lab)

| View | Lab link | How it is checked in the QC | Expected status |
| --- | --- | --- | --- |
| V10 Lab monitoring | `pull_lab_step4`: UACR / eGFR testing, potassium tested and high, HbA1c | Q5 / Q6: columns exist and follow the rules; S3 dedup: duplicates on NPI x patient x `SVC_DT` x `TEST_TYPE` in the pull; potassium / HbA1c LabCorp only (L-A) | PASS or finding |
| V6 Eligible panel | `pj_pat_sglt2_filter_m` | Q4 / Q6: the 24 eligible columns read the stale table; eligible share in the table and in the output | Finding (fix: PJ06 re-run with C1 / C11) |
| V7 CKD stage mix | Lab `GFR_STAGE`; rule 6.2 (lab first, 3a / 3b from the eGFR value, stage 1-2 needs damage evidence) | Q6: NB02 counts tests by eGFR stage 1-5 only (no 3a / 3b, no damage rule) | Documented, not built (section 7) |
| F9 completeness | Readiness 5.4 | Q14: monthly pull volume per test Jul 2025 .. Sep 2026 vs the 95%-of-median rule | Report, owner NBA team |
| F10 trends | 3 months vs previous 3 | Q5: no trend columns in NB02 | N/A, noted |
| V1-V3, V8, V9 | Rx, Dx, bridge | Not in NB02 | N/A with reason |
| Section 4 Lab row | Pull ready after dedup check, 0 null NPI | Q4: rows, null NPI, dates, duplicates | PASS if same |

## 4. How the template is adapted for Lab

* **Rule file:** readiness (sections 4, 5.3, 5.4, 6, 6.2) replaces `60_ftp_copay_nba_3_1_readiness_plan.md`.
* **Grain (Q1):** one row per `NPI_NUMBER` x `COHORT_ID` only for NPIs with a GFR / UACR test up to the cutoff; "universe x 28" is checked as "output NPIs within universe, gap explained".
* **Q3:** E = `CUTOFF_DATE`; test counted if `SVC_DT` in (E - N months, E]; `RUNNING_` from `DATA_START_DATE` 2023-01-01. No `INSERT_TS`: load-date point-in-time not testable, noted with readiness 5.4.
* **Q8 / Q9:** NBA 3.0 116 features vs 3.1 143 (+48 X18, -21 X19); 752 xlsx for SHAP; OPEN if unreadable.
* **Q12:** 3.0 `claim_lab_monthly` (or `_ZS` reference) vs 3.1 c28 on common HCPs.
* **Q14:** test basket and `LAB_FLAG_RULES` thresholds vs the pull; per `DATASET` active HCPs and 12M tests vs training.

## 5. Steps

| # | Step | Checks | Done when |
| --- | --- | --- | --- |
| 1 | Read rule and context sources: Lab Journey plan + summary; PJ01 Step 4; PJ06 `sglt2_filter_m`; NB02 cells 10, 14-15, 23-36; `00_cohort_config` (`HCP_LAB_TABLE`, `LAB_FLAG_RULES`, `get_patient_table_path`); X13-X24 | - | Each Q has its rule source noted |
| 2 | Fill template sections 1 and 2 | - | Paths, counts and Lab-specific How / Pass-when filled |
| 3 | Universe and grain | Q1 | Keys, rows per cohort, duplicates, NPIs outside universe, null `PROVIDER_ID`, gap and fan-out explained, flag-only NPIs counted |
| 4 | Cohorts, windows, sources | Q2, Q3, Q4 | Cohort fields = `input_claims_cohorts`; edge days; sources vs section 4; S3 duplicates; eligible share |
| 5 | Features and rules vs section 6 | Q5, Q6 | 143 columns mapped to families; V10 / V6 / V7 / F9 / F10 rows documented; stage mapping and `PCT_` rule |
| 6 | Fill rate | Q7 | All 143 features, all / train / test / holdout / c28, flags |
| 7 | NBA 3.0 map | Q8, Q9 | Every 3.0 Lab feature labelled |
| 8 | HCP trace and invariants | Q10, Q11 | 5-6 cases recomputed from the pull + eligibility; invariants (nesting, GFR + UACR = total, stage sums, eligible <= all, flagged <= tested, `PCT_` in [0, 1], `RUNNING_` >= 12M) |
| 9 | 3.0 comparison, reproducibility, drift | Q12, Q13, Q14 | Spearman / totals vs 3.0; `PULL_DT`, Delta history, stale text; F9 completeness; drift per `DATASET` |
| 10 | Write `02_lab_claims_features_qc.md` | All | All 11 template sections, findings with severity, sign-off n / 14 |
| 11 | Verify the QC file | - | Re-read vs template; 3 numbers re-queried; no notebook or table changed |

## 6. Open points for the user

1. Output file name: `02_lab_claims_features_qc.md` (same numbering as Rx 01 and Dx 03).
2. Sign-off: "QC by / date" filled; reviewer and NBA-team drift sign-off left blank.
