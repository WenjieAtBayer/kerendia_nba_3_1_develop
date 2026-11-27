# QC plan 05: HCP monthly Rx new patient starts (NPS) features, NBA 3.1

**Purpose:** plan the QC of the HCP-month NPS feature notebook `05_claim_rx_nps_monthly_cohort` (run `full_2026_11_16`). The QC result goes in `05_rx_nps_claims_features_qc.md` in this folder and follows `../00_qc_template.md` (Q1 to Q14, sections 1 to 11).  
**Rule source:** `../Feature_Evaluation/05_Feature_Views/NBA_3_1_LAAD_Feature_Views_Readiness_Plan.md` ("readiness"), section 6 (contender view readiness) and the Rx rows of sections 4, 5.1, 5.3 and 5.4. Section 7 (work plan) is out of scope: no new features, no Feature Views objects.  
**Developer rules:** `NBA_3_1_Rx_NPS_Features_Plan.md`, `NBA_3_1_Rx_NPS_Features_Client_Summary.md`, `NBA_3_1_HCP_Features_Decisions.md`.  
**Mode:** read-only. No notebook is re-run (a re-run overwrites the outputs); no table is changed. Evidence = numbers from read-only queries on the written tables.  
**Date:** 2026-11-27

---

## 1. Lineage under QC

| Step | Asset | Role | Note |
| --- | --- | --- | --- |
| PJ03 Rx journey | `Patient_Journey_Validation/Rx Files/03_patient_journey_rx` + `NBA_3_1_Rx_Journey_Plan.md`, `NBA_3_1_Rx_Journey_Client_Summary.md` | Step 4e writes the NB05 Rx pull `pull_rx_nps` (all-HCP claims of the universe's patients, from 2021) | Input of NB05 (`HCP_NPS_TABLE`) |
| PJ06 combine | `Patient_Journey_Validation/Combine Files/06_patient_journey_combine_3_1` | Patient-month combined tables | Brief: NB05 joins a PJ06 table. Code: NB05 reads only the Rx pull. To confirm in step 1 |
| NB05 HCP features | `hcp_level_features/05 Rx NPS Claims Files/05_claim_rx_nps_monthly_cohort` (31 cells) | First start per patient x class / brand across all HCPs, credited to the HCP who wrote it; aggregated to `PROVIDER_ID` x cohort | Under QC |

## 2. What was found during planning (read-only, 2026-11-27)

| Item | Value |
| --- | --- |
| Output | `kerendia_nba_3_1.full_2026_11_16_hcp_claim_rx_nps_monthly_cohort`: 8,088,324 rows, 294,579 `PROVIDER_ID`, 28 `COHORT_ID`, 0 duplicate keys, 0 null `PROVIDER_ID`, `PULL_DT` 2026-11-17, `CUTOFF_DATE` 2024-05-31 .. 2026-08-31 |
| Columns | 172 = `PROVIDER_ID` + 163 features (19 values x 4 windows, 19 `RUNNING_`, 17 starts x 4 `PCT_`) + 8 metadata |
| Input | `kerendia_nba_3_1.full_2026_11_16_pull_rx_nps`: 4,649,582,001 rows, `SVC_DT` 2021-01-02 .. 2026-09-30, 294,674 providers, 0 null provider / patient, 416,068,393 rows `REJECTION_FLAG = 1`, `RX_SOURCE` JOURNEY / HCP_ONLY, 12 classes, 17 categories |
| Stale docs (candidate) | NB05 plan and summary say "input stays 3.0 `Rx_05`" and "154 features / 163 columns"; the load cell (2026-11-13) reads the 3.1 pull and adds Kerendia starts |

Points Q1 must explain: 294,579 x 28 = 8,248,212 > 8,088,324 rows (providers absent in early cohorts).

## 3. Section 6 of the readiness: what applies to NB05

| View | NPS link | How it is checked in the QC | Expected status |
| --- | --- | --- | --- |
| V1 Kerendia writing (Track R, NB01 / NB05 output) | NPS is a registered (Track R) table; NBRx-like first claim is stateful, kept in notebooks | Entity: output keyed by `PROVIDER_ID`, readiness 5.1 needs `NPI_NUMBER` (mapping coverage). Timestamp: label = 1st of month after lookback end vs `SVC_DT_M` / `CUTOFF_DATE`. Width 163 features. Paid-only: are rejected claims counted as visits / starts? | Documented or finding |
| V2 Claim type | Rejected claims in the input | Share of rejected rows; starts whose first date is only a rejected claim; RV not separable | Finding / note |
| V3 SGLT2 add-on pool | SGLT2 and Kerendia starts exist; no "add-on" state | Q5 | N/A with reason |
| F9 completeness | Newest month thin (5.4) | Q14: monthly pull rows Jul 2025 .. Sep 2026 vs 95% of median of 3 prior months | Report, owner NBA team |
| F10 trends | 3 months vs previous 3 | Q5: no trend columns | N/A, noted |
| V4 to V10 (others) | Not Rx NPS | - | N/A |

## 4. How the template is adapted for NPS

* **Rule file:** readiness (sections 4, 5.1, 5.3, 5.4, 6) replaces `60_ftp_copay_nba_3_1_readiness_plan.md`.
* **Grain (Q1):** `PROVIDER_ID` x `COHORT_ID`, only providers with a counted claim from `DATA_START_DATE` (2023-01-01) to the cutoff; gap to universe x 28 explained by recount.
* **Q3:** E = `CUTOFF_DATE`; N-month window = N calendar months ending at E; `RUNNING_` from 2023-01-01; first-start dates from the full history (`HCP_RX_HISTORY_START`). No `INSERT_TS`: load-date part N/A.
* **Q8 / Q12:** NBA 3.0 `kerendia_nba_3_0_claim_rx_nps_monthly` and the 752 xlsx; 14 NB05 features in the selected 277.
* **Q14:** class / category basket vs config; monthly volumes; active providers and 12M starts per `DATASET`.

## 5. Steps

| # | Step | Checks | Done when |
| --- | --- | --- | --- |
| 1 | Read rule and context sources (readiness, NB05 plan / summary, PJ03 Step 4e, PJ06, `00_cohort_config`, NB05 cells 7, 19, 21, 23, 26-30) | - | Each Q has its rule source |
| 2 | Fill template sections 1 and 2 | - | Paths, counts, NPS-specific How / Pass-when |
| 3 | Grain, cohorts, windows, sources | Q1-Q4 | 0 duplicates, rows per cohort = recount, 0 cohort mismatches, edge days, sources = readiness |
| 4 | Features and rules vs section 6 | Q5, Q6 | 163 names 0 missing / unexpected; rules table; V1 / V2 / V3 / F9 / F10 rows |
| 5 | Fill rate | Q7 | All 163 features, all / train / test / holdout / c28, flags |
| 6 | NBA 3.0 map | Q8, Q9 | Each 3.0 NPS feature labelled |
| 7 | HCP trace and invariants | Q10, Q11 | Full independent SQL recompute of counts + 5-6 traced cases; invariants 0 violations |
| 8 | 3.0 comparison, reproducibility, drift | Q12-Q14 | Spearman / totals, Delta history, stale text, drift per `DATASET` |
| 9 | Write `05_rx_nps_claims_features_qc.md` | All | 11 sections, findings, sign-off n / 14 |
| 10 | Verify the QC file | - | Re-read vs template, 3 spot-check queries, nothing changed |

## 6. Open points (defaults applied)

1. Brief says NB05 joins a PJ06 combine table: QC the code as written and record the difference.
2. Rejected claims in starts: reported as a finding, not a FAIL.
3. Sign-off: "QC by / date" filled; reviewer and NBA-team drift sign-off left blank.
