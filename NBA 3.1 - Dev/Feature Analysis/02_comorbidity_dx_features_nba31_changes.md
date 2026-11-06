# NBA 3.1 Claim Comorbidity Features: Changes and Additions

> **Data source update (Nov 2026):** NBA 3.1 now reads `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7` (LAAD-based LRx V7, weekly, history from Dec 2021) instead of `KERENDIA_LAAD_BASED_LRX_V6` and `KERENDIA_LAAD_BASED_LRX_FULL_DATA_STARTING_2021`. Read V6 references below as V7. V7 `WEEK_ENDING_DATE` / `PERIOD_ID` are DATEs, and `PRODUCT_GROUP` uses the shorter lrx_nbrx names. Numbers in this document were computed on V6.

This file lists the claim comorbidity changes for NBA 3.1: which NBA 3.0 features to remove or rebuild (section 1), and which new features to add (section 2). How the NBA 3.0 features are built is in the companion file `NBA_3_1_Claim_Comorbidity_Features_Analysis.md`. References written as "Analysis 1.x" point to sections in that file.

NBA 3.1 scope: the model target is still the HCP's **Kerendia NBRx in the 30-day prediction window**, but the indications now cover **heart failure (HF, LVEF >= 40%) and type 1 diabetes (T1D) with CKD**, in addition to type 2 diabetes (T2D) with CKD. The NBA 3.0 comorbidity groups (`KD`, `DB-KD`, `CV-KD`) were built around CKD only, so the family needs to be rebuilt around the indications.

SHAP ranks and shares come from `Final NBA 3.0 Modeling Features.xlsx` (752 features, mean absolute SHAP).

**How the signal was measured (backtest, rerun 2026-11-02 on the NBA 3.1 universe).** Features were taken as of June 2026 (scoring month `SVC_DT_M = 2026-06-01`, the same position the ops run uses for a lookback ending 2026-06-30). The NBA 3.0 features were rebuilt with the NBA 3.0 logic from the NBA 3.1 `Dx_09` (`kerendia_nba_3_1_volume/hcp_level_model/ops_pipeline/query_output/Dx_09`). On the 218,110 HCPs that are in both, the rebuilt values match the NBA 3.0 output exactly. The target is "the HCP wrote at least one Kerendia NBRx in August 2026" (one-month gap, as in production), from `KERENDIA_LAAD_BASED_LRX_V6` with `PRODUCT_GROUP = 'KERENDIA'`. Population: the 314,920 HCPs in the NBA 3.1 universe (`kerendia_nba_3_1_volume/HCP_Universe/`), 6,704 writers, base rate 2.13%.

* **AUC**: the chance that a random writer has a higher value than a random non-writer, over HCPs with a non-empty value. 0.50 = no signal. Below 0.50 means lower values go with more writers. In this file the direction is shown, for example "0.68 (inverse)".
* **AUC in size**: median AUC inside 3 equal groups of HCP size (all-market NBRx in January to June 2026). It shows signal that is not just "bigger HCP".
* **AUC new writers**: AUC among the 268,086 HCPs with no Kerendia NBRx since January 2023 (rate 0.55%). 22.0% of August writers came from this group, and NBA must find them.
* New Dx-based features use the NBA 3.1 `query_output/dx_input_claims_all_events_features_input`, which starts on 2021-01-02, so their backtest uses the full 365-day window (2025-07-01 to 2026-06-30).

---

## 1. Features to remove or change in NBA 3.1

| # | Feature group | Action | Reason |
| --- | --- | --- | --- |
| 1 | Single-month counts and shares: `TOTAL_DX_PATIENTS`, `TOTAL_DX_PATIENTS_{KD,DB_KD,CV_KD}`, `PCT_TOTAL_DX_PATIENTS_{KD,DB_KD,CV_KD}` (7) | Drop | One calendar month is noisy. 0.96 correlation with the 1-month average. None in the final 752 |
| 2 | Rolling averages `TOTAL_DX_PATIENTS_*_IN_LAST_{1,3,6,12}_MONTH` (16) | Replace with distinct patients in 3 and 12 months | Adjacent windows correlate up to 0.97. The windows are one month longer than the name, and the average skips empty months (Analysis 1.3). None in the 752 |
| 3 | Running totals `RUNNING_TOTAL_DX_PATIENTS*` (4) | Replace with distinct patients in a fixed 24 months | Depend on the data start and grow every run (Analysis 1.7). Overall and `KD` correlate 0.97. Almost no signal for new writers (0.50 to 0.53) |
| 4 | Window shares `PCT_TOTAL_DX_PATIENTS_*_IN_LAST_{1,3,6}_MONTH` (9) | Drop. Keep the 12-month share only, rebuilt on distinct patients | Adjacent windows correlate 0.88 to 0.97. Shares can be above 1 (Analysis 1.5) and mostly reflect small panels |
| 5 | Diagnosis groups from `FIN_DIAG_CD` (`KD`, `DB-KD`, `CV-KD`) | Rebuild on the NBA 3.1 Dx event list, grouped by indication | No HF-only group, no T1D group, and CKD stage 3a/3b codes are missing (Analysis 1.7, item 5) |

Column impact: 39 columns become 2 rebuilt NBA 3.0 features (1.3, 1.4) plus the new indication features in section 2.

### 1.1 Single-month counts and shares (#1)

The monthly values are what the rolling features are built from, and the model receives them only for the scoring month. A single month mostly reflects visit timing. `TOTAL_DX_PATIENTS` correlates 0.96 with `TOTAL_DX_PATIENTS_IN_LAST_1_MONTH` (Spearman, June 2026). None of the 7 columns is in the final 752.

**Decision**: drop all 7.

### 1.2 Rolling averages (#2)

Of the 39 columns, 11 pairs correlate at 0.95 or more. 6 of these pairs are adjacent windows of the same rolling average (for example 3M vs 6M: 0.973 overall, 0.963 `KD`, 0.959 `DB_KD`) and 3 are adjacent windows of the `CV_KD` share. The average is "patients per active month", not the number of different patients, so a patient seen every month counts many times (Analysis 1.3). Signal is similar across windows: `TOTAL_DX_PATIENTS_IN_LAST_{1,3,6,12}_MONTH` have AUC 0.695, 0.695, 0.694 and 0.694 (in size 0.70 to 0.71), and none of the 16 is in the 752.

**Decision**: replace with `NUM_OF_PATIENTS_IN_HCP_DX_PANEL_WITH_{GROUP}_IN_LAST_{90,365}_DAYS` = distinct patients in the window, for the new groups in section 2. Drop the 1M and 6M windows.

### 1.3 Running totals (#3)

| Feature | In the 752 | AUC | AUC in size | AUC new writers |
| --- | --- | --- | --- | --- |
| `RUNNING_TOTAL_DX_PATIENTS_DB_KD` | Rank 133, 0.18% | 0.670 | 0.633 | 0.501 |
| `RUNNING_TOTAL_DX_PATIENTS_KD` | Rank 237, 0.11% | 0.694 | 0.683 | 0.526 |
| `RUNNING_TOTAL_DX_PATIENTS` | No | 0.698 | 0.668 | 0.521 |

The running totals count patient-months since January 2021, so they are mostly "how long and how much the HCP has billed CKD". They carry signal for established writers but almost none for new writers (AUC 0.50 to 0.53). Because the start date is fixed, a training cohort in 2024 sees about 40 months of history and the 2026 inference run sees about 69, so the same HCP drifts upward over time.

**Decision**: replace the two kept features with `NUM_OF_PATIENTS_IN_HCP_DX_PANEL_WITH_DIABETIC_CKD_IN_LAST_730_DAYS` and `..._WITH_CKD_IN_LAST_730_DAYS` (distinct patients, fixed 24-month window ending at each cohort's lookback end). Drop the overall and `CV_KD` running totals.

### 1.4 Window shares (#4)

`PCT_TOTAL_DX_PATIENTS_CV_KD_IN_LAST_12_MONTH` is the strongest comorbidity feature in the 752 (rank 88, 0.25%), but the direction is the opposite of what the name suggests: AUC 0.320, so **0.68 (inverse)**, and 0.71 (inverse) in size. A high share mostly means a small kidney panel where one or two cardio-renal patients give 50 to 100%. The `DB_KD` share behaves the same (0.345, in size 0.28). For new writers there is no signal (0.505).

**Decision**: keep one 12-month share per indication group, rebuilt as distinct patients in the group / distinct patients in the HCP's Dx panel (always between 0 and 1). Drop the 1/3/6-month shares. Keep the existing 752 feature only until the rebuilt share is tested.

### 1.5 Diagnosis groups (#5)

`FIN_DIAG_CD` groups only kidney codes. For NBA 3.1:

* HF patients without a kidney code are invisible, although HF (LVEF >= 40%) is now an indication.
* T1D is not grouped at all. In the final 752 no feature mentions T1D.
* CKD stage 3 has 26,200 patients in the NBA 3.1 `Dx_09` (one description, `N18.3`), against 10.47M for the 4 descriptions that mention stage 4 (these include the hypertensive CKD "stage 1 through stage 4" codes), because N18.30 / N18.31 / N18.32 are missing. Stage 3 is the core Kerendia population, and the stage 3 and stage 4 shares are the best new Dx features within size groups in the backtest (2.2).

**Decision**: build the groups from the NBA 3.1 Dx event list (`kerendia_nba_3_1_volume/feature_selection/Kerendia NBA 3.1 - Dx Event List.csv`) using the building blocks in 2.0.

### 1.6 Where each change is implemented

| Change | Notebook | What to change |
| --- | --- | --- |
| Input (#5) | `03_HCP_Level_Features/00_Write_Input_Files`, section "File Dx_09" | Replace the `FIN_DIAG_CD` join with the NBA 3.1 Dx event codes (CKD, T2D, T1D, HF). Keep `DIAGNOSIS_CODE` in the output |
| Single months, windows, running totals (#1 to #4) | `09_claim_comorbidity` | Replace `step2_fill_missing` + `step3_lag_avg` with distinct-patient counts per cohort window (90, 365, 730 days). Read cohorts from `00_cohort_generation` (`CohortGenerator('claims')`) instead of the hard-coded `date_start` |
| Shares (#4) | Same | Denominator = distinct patients in the HCP's Dx panel in the same window |

---

## 2. Features to add in NBA 3.1

| # | Feature | Source | Hypothesis | Value | Effort |
| --- | --- | --- | --- | --- | --- |
| 1 | Indication mix of the Dx panel (T2D + CKD, T1D + CKD, HF LVEF >= 40% proxy, CKD + HF, any indication) | Dx | HCPs whose panels have more patients in the Kerendia label groups write more Kerendia, including new writers | High | Quick win (Dx only) |
| 2 | CKD stage mix (stage 3, stage 4) | Dx | Kerendia is started at eGFR >= 25, so a stage 3-4 heavy panel is the core opportunity | High | Quick win |
| 3 | Change in indicated patients (log-ratio) | Dx | A growing indicated panel signals a new referral stream or clinic | Medium | Quick win |

Source tells which LAAD files a feature needs. All features here are Dx-only. Features that combine Dx with Rx or Lab (untreated eligible pool, triggers, HFpEF with echo or loop diuretic) are already proposed in `NBA_3_1_Patient_Features_Recommendations.md` (2.1 to 2.3) and should not be duplicated here.

**What is new compared with NBA 3.0**

In NBA 3.0, the family only had **kidney features**. All 39 columns were built on 3 kidney diagnosis groups: `KD` (CKD), `DB_KD` (diabetic CKD) and `CV_KD` (cardio-renal CKD), as monthly patient counts, rolling averages, running totals and shares. Only 3 of them are in the final 752: `PCT_TOTAL_DX_PATIENTS_CV_KD_IN_LAST_12_MONTH` (rank 88), `RUNNING_TOTAL_DX_PATIENTS_DB_KD` (rank 133) and `RUNNING_TOTAL_DX_PATIENTS_KD` (rank 237). The model could not see HF patients without a kidney code, T1D patients, or how far CKD had progressed (stage 3a/3b codes were missing).

NBA 3.1 keeps the kidney view (rebuilt as 2 fixed 24-month counts, 1.3) and adds **12 new columns**:

* **Indication mix (2.1), 9 columns.** In NBA 3.0 we only had CKD features. Now we also add the Kerendia indications:
  * T2D + CKD: `NUM_` and `PCT_OF_PATIENTS_IN_HCP_DX_PANEL_WITH_T2D_CKD_IN_LAST_365_DAYS_DX` (2).
  * HF: `..._WITH_HF_LVEF_GE_40_PROXY_...` and `..._WITH_CKD_AND_HF_...`, NUM and PCT (4).
  * T1D + CKD: `NUM_OF_PATIENTS_IN_HCP_DX_PANEL_WITH_T1D_CKD_IN_LAST_365_DAYS_DX` (1, count only).
  * A combined `..._WITH_ANY_KERENDIA_INDICATION_...`, NUM and PCT (2).

  *Added value:* the model sees the HF and T1D populations for the first time. The new counts and shares find new writers better than the NBA 3.0 share: AUC 0.54 to 0.59, against 0.505 for `PCT_TOTAL_DX_PATIENTS_CV_KD_IN_LAST_12_MONTH`.
* **CKD stage mix (2.2), 2 columns.** In NBA 3.0 CKD was one block, and stage 3 was almost empty (26,200 patients) because N18.30 / N18.31 / N18.32 were missing. Now we add `PCT_OF_PATIENTS_IN_HCP_DX_PANEL_WITH_CKD_STAGE_3_IN_LAST_365_DAYS_DX` and `..._CKD_STAGE_4_...`. *Added value:* these show how much of the panel sits in the eGFR range where Kerendia is started. The stage 4 and stage 3 shares have the highest AUC in size of all Dx features tested (0.704 and 0.685), and 0.577 and 0.562 for new writers.
* **Change in indicated patients (2.3), 1 column.** In NBA 3.0 there were only levels (counts and shares), with no trend. Now we add `LOGRATIO_PATIENTS_ANY_KERENDIA_INDICATION_3M` (last 3 months vs the 9 months before). *Added value:* it flags HCPs whose indicated panel is growing. Backtest: AUC 0.629, 0.578 in size, 0.525 for new writers, so it is weaker than the levels and is kept only if feature selection keeps it.

| Area | NBA 3.0 (39 columns) | NBA 3.1 new features | New columns | Added value |
| --- | --- | --- | --- | --- |
| Indications covered | CKD only (`KD`, `DB_KD`, `CV_KD`) | T2D + CKD, T1D + CKD, HF LVEF >= 40% proxy, CKD + HF, any indication | 9 | HF and T1D visible for the first time. Better for new writers (AUC 0.54 to 0.59 vs 0.505) |
| CKD severity | None (stage 3a/3b codes missing) | Stage 3 and stage 4 shares | 2 | Best within-size signal (0.704 stage 4, 0.685 stage 3) |
| Trend | None | 3M vs prior 9M log-ratio | 1 | Growth in the indicated panel (AUC in size 0.578) |
| **Total** | | | **12** | |

### 2.0 Building blocks (shared by all new features)

Patient flags are set from claims by **any** provider in the lookback, then rolled up to each HCP's Dx panel: the distinct patients with any Dx event-list claim where the HCP is the referring (else rendering) doctor.

| Building block | Definition (ICD-10) |
| --- | --- |
| T2D | `E11*` |
| T1D | `E10*` |
| CKD (non-ESRD) | `N18.1` to `N18.5` (including `N18.30`, `N18.31`, `N18.32`), `N18.9`, `E11.21/22/29`, `E10.21/22/29`, `I12.9`, `I13.0`, `I13.10` |
| ESRD / dialysis (excluded) | `N18.6`, `Z99.2`, `I12.0`, `I13.11`, `I13.2` |
| CKD stage 3 | `N18.3`, `N18.30`, `N18.31`, `N18.32` |
| HF | `I50*` |
| HF LVEF >= 40% proxy | `I50.3x` (diastolic) and no `I50.2x` (systolic) in the lookback. Needs medical sign-off, as in Patient Features Recommendations 2.3 |
| T2D + CKD | T2D and CKD and not ESRD |
| T1D + CKD | T1D and CKD and not ESRD |
| Any indication | T2D + CKD, or T1D + CKD, or the HF proxy |

**Null policy**: `NUM_*` is 0 when no patient qualifies. `PCT_*` stays empty when the panel is empty.

Feature naming: each stem gives `NUM_OF_PATIENTS_IN_HCP_DX_PANEL_WITH_{stem}_IN_LAST_365_DAYS_DX` and `PCT_OF_PATIENTS_IN_HCP_DX_PANEL_WITH_{stem}_IN_LAST_365_DAYS_DX` (= NUM / panel size). Median Dx panel: 82 patients (109 for the HCPs also in the NBA 3.0 universe, 31 for the 91,870 HCPs new in the 3.1 universe).

### 2.1 Indication mix of the Dx panel (#1): Dx

**Business meaning**: how many of the HCP's patients fit each Kerendia indication. This tells NBA which HCPs see the T2D-CKD, T1D-CKD and HF populations that Kerendia now covers. For HF and T1D this is the first time the model sees these populations at all.

| Stem | Non-zero | Median NUM / PCT | AUC (NUM / PCT) | AUC in size (NUM / PCT) | AUC new writers (NUM / PCT) |
| --- | --- | --- | --- | --- | --- |
| `T2D_CKD` | 87.3% | 11 / 0.144 | 0.726 / 0.665 | 0.670 / 0.656 | 0.573 / 0.572 |
| `T1D_CKD` | 39.2% | 0 / 0.000 | 0.673 / 0.630 | 0.634 / 0.602 | 0.554 / - |
| `HF_LVEF_GE_40_PROXY` | 79.2% | 4 / 0.056 | 0.682 / 0.552 | 0.627 / 0.561 | 0.572 / 0.563 |
| `CKD_AND_HF` | 80.5% | 5 / 0.062 | 0.704 / 0.594 | 0.655 / 0.591 | 0.585 / 0.587 |
| `ANY_KERENDIA_INDICATION` | 89.8% | 16 / 0.207 | 0.723 / 0.649 | 0.670 / 0.653 | 0.578 / 0.592 |
| For comparison: `PCT_TOTAL_DX_PATIENTS_CV_KD_IN_LAST_12_MONTH` (NBA 3.0, rank 88) | 59.2% | - / 0.43 | 0.68 (inverse) | 0.71 (inverse) | 0.505 |

Both versions find new writers better than the NBA 3.0 share (0.54 to 0.59 vs 0.505), so they help the model find HCPs that have not written Kerendia yet. The counts (NUM) are stronger overall (0.67 to 0.73) but partly repeat HCP size (Spearman 0.43 with all-market NBRx for `ANY_KERENDIA_INDICATION`). The shares (PCT) are size-free (-0.05). For the two HF stems the share is weaker than the count (in size 0.56 to 0.59 vs 0.63 to 0.66).

**Decision**: add NUM and PCT for `T2D_CKD`, `CKD_AND_HF`, `HF_LVEF_GE_40_PROXY` and `ANY_KERENDIA_INDICATION`. Add `T1D_CKD` as NUM only (the share is near 0 for most HCPs) and keep it even if selection drops it, as long as the T1D indication is in scope, so the model can learn it once T1D writing starts. Do not add plain `T2D`, `T1D` or `HF` counts (AUC in size 0.63, 0.61 and 0.65 for NUM). They are less specific and repeat the patient pipeline Dx features.

### 2.2 CKD stage mix (#2): Dx

**Business meaning**: Kerendia is started at eGFR >= 25 (CKD stages 1 to 4), so stage 3 and 4 patients are the core of the label population. Stage-coded CKD also means the HCP stages kidney disease actively.

| Stem | Non-zero | Median NUM / PCT | AUC | AUC in size | AUC new writers |
| --- | --- | --- | --- | --- | --- |
| `PCT_..._CKD_STAGE_3` | 87.7% | 12 / 0.161 | 0.637 | **0.685** | 0.562 |
| `PCT_..._CKD_STAGE_4` (`N18.4`) | 72.9% | 3 / 0.029 | 0.665 | **0.704** | 0.577 |

The stage 4 and stage 3 shares have the highest AUC in size of all Dx features tested here. They correlate 0.47 (Spearman), so they are not duplicates. The stage 3 share needs the stage 3a/3b codes (1.5).

**Decision**: add `PCT_..._CKD_STAGE_3` and `PCT_..._CKD_STAGE_4`. Do not add a stage 5 / ESRD share: ESRD is outside the label.

### 2.3 Change in indicated patients (#3): Dx

**Business meaning**: an HCP whose indicated panel is growing (new clinic, new referral source, more HF patients after a hospital affiliation) is a better target than one with a flat panel of the same size.

**Definition**: `LOGRATIO_PATIENTS_ANY_KERENDIA_INDICATION_3M = ln((n_3M / 3 + 0.5) / ((n_12M - n_3M) / 9 + 0.5))`, where n = distinct patients with any indication in the window. Same formula as the log-ratio in Patient Features Recommendations 1.4.

Backtest (n from the HCP's Dx panel with an indication flag, windows ending 2026-06-30): AUC 0.629, in size 0.578, new writers 0.525. The signal is weaker than the levels in 2.1, so this is medium priority and should be dropped if feature selection does not keep it.

**Decision**: build for `ANY_KERENDIA_INDICATION` only, test in selection.
