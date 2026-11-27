# QC plan 06: HCP monthly Eligible HCP claims features, NBA 3.1

**Purpose:** plan the QC of the HCP-month eligible-patient notebook `06_claim_eligible_hcp` (run `full_2026_11_16`). The QC result goes in `06_eligible_hcp_claims_features_qc.md` in this folder and follows `../00_qc_template.md` (Q1 to Q14, sections 1 to 11).  
**Rule source:** `../Feature_Evaluation/05_Feature_Views/NBA_3_1_LAAD_Feature_Views_Readiness_Plan.md` ("readiness"), section 6 (contender view readiness, incl. 6.1 bridge and 6.2 CKD stage) and the related rows of sections 4, 5.3 and 5.4. Section 7 (work plan) is out of scope: no new features, no Feature Views objects.  
**Developer rules:** `NBA_3_1_Eligible_HCP_Features_Plan.md`, `NBA_3_1_Eligible_HCP_Features_Client_Summary.md`, `NBA_3_1_HCP_Features_Decisions.md` (X13 to X24).  
**Mode:** read-only. No notebook is re-run (a re-run overwrites the outputs); no table is changed. Evidence = numbers from read-only queries on the written tables.  
**Date:** 2026-11-27

---

## 1. Lineage under QC

| Step | Asset | Role |
| --- | --- | --- |
| PX journey | `Patient_Journey_Validation/Px Files/05_patient_journey_px` + `NBA_3_1_Px_Journey_Plan.md`, `NBA_3_1_Px_Journey_Client_Summary.md` | Writes `full_2026_11_16_pj_px`: one row per patient, `FIRST_DIALYSIS_DATE` (STRING, readiness section 4) |
| PJ04 / PJ06 combine | `Patient_Journey_Validation/Combine Files/06_patient_journey_combine_3_1` | Writes `pj_pat_sglt2_filter_m` (`ELIGIBLE_PATIENT_FLAG`, `GFR_DX_STAGE`, `UACR_STAGE` per patient-month) and `pj_dm_hf_flags` (`DM_TYPE`, `HF_TYPE`, `HF_FIRST_DATE` per patient) |
| NB06 HCP features | `hcp_level_features/06 Eligible HCP Claims Files/06_claim_eligible_hcp` (35 cells) | Cell 7: Rx pull `HCP_RX_TABLE` (NPI, patient, day only). Cell 15: distinct (NPI, patient, month) joined to eligibility (flag = 1); dialysis flag per (NPI, day). Cells 21-26: stage counts, windows 1 / 3 / 6 / 12, `RUNNING_`, `PCT_`. Cell 27: DM / HF type features (all Rx patients and eligible patients). Cell 29: write. Cell 31: `PROVIDER_ID` mapping |

Note to the brief: NB06 uses the PX journey only through `FIRST_DIALYSIS_DATE` (`DIALYSIS_FLAG`); the combine outputs give eligibility, stage, DM and HF type.

## 2. What was found during planning (read-only, 2026-11-27)

| Item | Value |
| --- | --- |
| NPI output | `kerendia_nba_3_1.full_2026_11_16_hcp_claim_eligible_patient_cohort`: 8,085,306 rows, 294,535 NPIs, 28 `COHORT_ID`, `PULL_DT` 2026-11-17, `CUTOFF_DATE` 2024-05-31 .. 2026-08-31, 0 null NPI, 226 columns (= docs; an early planning estimate of ~277 was a mis-count, corrected in the QC) |
| Provider output | `full_2026_11_16_hcp_provider_claim_eligible_patient_cohort`: 8,086,528 rows (+1,222 vs NPI), 294,459 `PROVIDER_ID`, **3,001 rows with null `PROVIDER_ID`** |
| Other copies | `validation_2026_11_16_uc_*` eligible tables in the same schema: not under QC |
| HF type values | Output: `HFPEF_PROXY`, `HFREF_PROXY`, `MIXED`, `UNKNOWN`; Client Summary says `HFPEF`, `HFREF`, `HF_UNSPECIFIED` (stale text) |
| Rx claim status | NB06 reads no claim-status column: rejected claims (`REJECTION_FLAG = 1`) may count as patients seen (to check) |

Points Q1 must explain: 294,535 x 28 = 8,246,980 > 8,085,306 rows (an NPI gets a row only once it has an Rx claim up to the cutoff); provider rows > NPI rows (NPI to `PROVIDER_ID` fan-out); null `PROVIDER_ID` (NPIs not in the mapping table).

## 3. Section 6 of the readiness: what applies to NB06

| View | NB06 link | How it is checked in the QC | Expected status |
| --- | --- | --- | --- |
| V6 Eligible panel | Core of NB06: `pj_pat_sglt2_filter_m` flag; no per-indication flags | Q4 / Q6: eligible share in the table and output (77% stale vs 18.5% current code, readiness 6.3) | Finding (blocked: PJ06 re-run with C1) |
| V7 CKD stage mix | `GFR_DX_STAGE` (Dx first, then lab), stage 3 only | Q6: rule 6.2 (lab first, 3a / 3b, stage 1-2 needs damage evidence) vs notebook | Documented, not built (section 7) |
| V8 HF | `HF_TYPE` proxies from `pj_dm_hf_flags`; HF month = month >= `HF_FIRST_DATE` month | Q6 / Q10: values and rule | PASS or finding |
| V9 T1D + CKD | `TOTAL_ELIGIBLE_PATIENTS_DM_TYPE_T1D_*` | Q7: fill rate (little history) | Note |
| V1 / V2 | Rx input | Q4: share of distinct patient-months that come only from rejected claims | Finding if > 0 |
| 6.1 bridge | NB06 builds an Rx-only HCP-patient-month bridge | Q6: note for the bridge design (Rx only, no Dx / Lab) | Note |
| F9 completeness | Readiness 5.4 | Q14: monthly Rx patient-months Jul 2025 .. Aug 2026 vs 95%-of-median rule | Report, owner NBA team |
| F10 trends | 3 months vs previous 3 | Q5: no trend columns | N/A, noted |
| V3, V4, V5, V10 | SGLT2 add-on, calls, practice, lab | Not in NB06 | N/A with reason |
| Section 4 rows | `pj_pat_sglt2_filter_m`, `pj_dm_hf_flags`, `pj_px` | Q4: rows, dates, types | Same or explained |

## 4. How the template is adapted for NB06

* **Rule file:** readiness (sections 4, 5.3, 5.4, 6, 6.1, 6.2) replaces `60_ftp_copay_nba_3_1_readiness_plan.md`.
* **Grain (Q1):** one row per `NPI_NUMBER` x `COHORT_ID` only for NPIs with an Rx claim up to the cutoff; "universe x 28" is checked as "output NPIs within universe, gap explained".
* **Q3:** E = `CUTOFF_DATE`; a patient-month counts in window N if its month is in the N months ending with the cohort month; window = **sum** of N monthly counts (D1), not the 3.0 mean of N+1 (F7). `RUNNING_` from `DATA_START_DATE` 2023-01-01. No `INSERT_TS`: load-date point-in-time not testable, noted with readiness 5.4.
* **Q8 / Q9:** NBA 3.0 84 features vs 3.1 217 (+148 / -15, X20), reconciled with the real column count; selected 3.0 feature `RUNNING_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_4`; 752 xlsx for SHAP, OPEN if unreadable.
* **Q12:** 3.0 `kerendia_nba_3_0_claim_eligible_patient` vs 3.1 c28 on common HCPs: `RUNNING_` and 1-month columns comparable; window columns differ by design (F7).
* **Q14:** `DM_TYPE` / `HF_TYPE` values vs the notebook lists; per `DATASET` active HCPs and 12M eligible patient-months vs training.

## 5. Steps

| # | Step | Checks | Done when |
| --- | --- | --- | --- |
| 1 | Read rule and context sources: Px Journey plan + summary; PJ06 `sglt2_filter_m`; NB06 cells 21-35; `00_cohort_config`; X13-X24 | - | Each Q has its rule source |
| 2 | Fill template sections 1 and 2 | - | Paths, counts and NB06-specific How / Pass-when filled |
| 3 | Universe and grain | Q1 | Keys, rows per cohort, duplicates, NPIs outside universe, null `PROVIDER_ID`, gap and fan-out explained |
| 4 | Cohorts, windows, sources | Q2, Q3, Q4 | Cohort fields = `input_claims_cohorts`; edge days; sources vs section 4; eligible share; rejected-only patient-months |
| 5 | Features and rules vs section 6 | Q5, Q6 | Every column mapped to a family; V6 / V7 / V8 / V9 / V1-V2 / 6.1 / F9 / F10 rows documented |
| 6 | Fill rate | Q7 | All features, all / train / test / holdout / c28, flags |
| 7 | NBA 3.0 map | Q8, Q9 | Every 3.0 feature labelled |
| 8 | HCP trace and invariants | Q10, Q11 | 5-6 cases recomputed from Rx pull + eligibility + dialysis + DM / HF; invariants (nesting, stage sums = total, eligible <= Rx patients, DM sum = total, HF types sum = HF, `PCT_` in [0, 1], `RUNNING_` >= 12M, `DIALYSIS_FLAG` in {0, 1}) |
| 9 | 3.0 comparison, reproducibility, drift | Q12, Q13, Q14 | Totals / Spearman vs 3.0; `PULL_DT`, Delta history, stale text; F9 completeness; drift per `DATASET` |
| 10 | Write `06_eligible_hcp_claims_features_qc.md` | All | All 11 template sections, findings with severity, sign-off n / 14 |
| 11 | Verify the QC file | - | Re-read vs template; 3 numbers re-queried; no notebook or table changed |

## 6. Open points for the user

1. Output file name: `06_eligible_hcp_claims_features_qc.md` (same numbering as 02 Lab, 03 Dx, 05 Rx NPS).
2. Sign-off: "QC by / date" filled; reviewer and NBA-team drift sign-off left blank.
