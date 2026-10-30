# NBA 3.1 Claim Comorbidity Features: Changes and Additions

This file lists the claim comorbidity changes for NBA 3.1: which NBA 3.0 features to remove or rebuild (section 1), and which new features to add (section 2). How the NBA 3.0 features are built is in the companion file `NBA_3_1_Claim_Comorbidity_Features_Analysis.md`. References written as "Analysis 1.x" point to sections in that file.

NBA 3.1 scope: the model target is still the HCP's **Kerendia NBRx in the 30-day prediction window**, but the indications now cover **heart failure (HF, LVEF >= 40%) and type 1 diabetes (T1D) with CKD**, in addition to type 2 diabetes (T2D) with CKD. The NBA 3.0 comorbidity groups (`KD`, `DB-KD`, `CV-KD`) were built around CKD only, so the family needs to be rebuilt around the indications.

SHAP ranks and shares come from `Final NBA 3.0 Modeling Features.xlsx` (752 features, mean absolute SHAP).

**How the signal was measured (backtest).** Features were taken as of June 2026 (scoring month `SVC_DT_M = 2026-06-01`, the same position the ops run uses for a lookback ending 2026-06-30). The target is "the HCP wrote at least one Kerendia NBRx in August 2026" (one-month gap, as in production), from `KERENDIA_LAAD_BASED_LRX_V6` with `PRODUCT_GROUP = 'KERENDIA'`. Population: the 234,405 HCPs in the ops universe, base rate 2.87%.

* **AUC**: the chance that a random writer has a higher value than a random non-writer, over HCPs with a non-empty value. 0.50 = no signal. Below 0.50 means lower values go with more writers. In this file the direction is shown, for example "0.66 (inverse)".
* **AUC in size**: median AUC inside 3 equal groups of HCP size (all-market NBRx in January to June 2026). It shows signal that is not just "bigger HCP".
* **AUC new writers**: AUC among the 187,490 HCPs with no Kerendia NBRx since January 2023 (rate 0.8%). 22% of August writers came from this group, and NBA must find them.
* New Dx-based features use `query_output/dx_input_claims_all_events_features_input`, which starts on 2025-09-30, so their backtest window is 9 months (2025-09-30 to 2026-06-30) instead of 12.

---

## 1. Features to remove or change in NBA 3.1

| # | Feature group | Action | Reason |
| --- | --- | --- | --- |
| 1 | Single-month counts and shares: `TOTAL_DX_PATIENTS`, `TOTAL_DX_PATIENTS_{KD,DB_KD,CV_KD}`, `PCT_TOTAL_DX_PATIENTS_{KD,DB_KD,CV_KD}` (7) | Drop | One calendar month is noisy. 0.96 correlation with the 1-month average. None in the final 752 |
| 2 | Rolling averages `TOTAL_DX_PATIENTS_*_IN_LAST_{1,3,6,12}_MONTH` (16) | Replace with distinct patients in 3 and 12 months | Adjacent windows correlate 0.95 to 0.98. The windows are one month longer than the name, and the average skips empty months (Analysis 1.3). None in the 752 |
| 3 | Running totals `RUNNING_TOTAL_DX_PATIENTS*` (4) | Replace with distinct patients in a fixed 24 months | Depend on the data start and grow every run (Analysis 1.7). Overall and `KD` correlate 0.97. No signal for new writers |
| 4 | Window shares `PCT_TOTAL_DX_PATIENTS_*_IN_LAST_{1,3,6}_MONTH` (9) | Drop. Keep the 12-month share only, rebuilt on distinct patients | Adjacent windows correlate 0.96 to 0.97. Shares can be above 1 (Analysis 1.5) and mostly reflect small panels |
| 5 | Diagnosis groups from `FIN_DIAG_CD` (`KD`, `DB-KD`, `CV-KD`) | Rebuild on the NBA 3.1 Dx event list, grouped by indication | No HF-only group, no T1D group, and CKD stage 3a/3b codes are missing (Analysis 1.7, item 5) |

Column impact: 39 columns become 2 rebuilt NBA 3.0 features (1.3, 1.4) plus the new indication features in section 2.

### 1.1 Single-month counts and shares (#1)

The monthly values are what the rolling features are built from, and the model receives them only for the scoring month. A single month mostly reflects visit timing. `TOTAL_DX_PATIENTS` correlates 0.96 with `TOTAL_DX_PATIENTS_IN_LAST_1_MONTH` (Spearman, June 2026). None of the 7 columns is in the final 752.

**Decision**: drop all 7.

### 1.2 Rolling averages (#2)

Of the 39 columns, 12 pairs correlate at 0.95 or more, and 8 of these pairs are adjacent windows of the same rolling average (for example 3M vs 6M: 0.976 overall, 0.967 `KD`, 0.962 `DB_KD`). The average is "patients per active month", not the number of different patients, so a patient seen every month counts many times (Analysis 1.3). Signal is similar across windows: `TOTAL_DX_PATIENTS_IN_LAST_{1,3,6,12}_MONTH` have AUC 0.678, 0.674, 0.671 and 0.668 (in size 0.70 to 0.68), and none of the 16 is in the 752.

**Decision**: replace with `NUM_OF_PATIENTS_IN_HCP_DX_PANEL_WITH_{GROUP}_IN_LAST_{90,365}_DAYS` = distinct patients in the window, for the new groups in section 2. Drop the 1M and 6M windows.

### 1.3 Running totals (#3)

| Feature | In the 752 | AUC | AUC in size | AUC new writers |
| --- | --- | --- | --- | --- |
| `RUNNING_TOTAL_DX_PATIENTS_DB_KD` | Rank 133, 0.18% | 0.634 | 0.602 | 0.452 |
| `RUNNING_TOTAL_DX_PATIENTS_KD` | Rank 237, 0.11% | 0.664 | 0.655 | 0.485 |
| `RUNNING_TOTAL_DX_PATIENTS` | No | 0.665 | 0.642 | - |

The running totals count patient-months since January 2021, so they are mostly "how long and how much the HCP has billed CKD". They carry signal for established writers but none for new writers (AUC below 0.5). Because the start date is fixed, a training cohort in 2024 sees about 40 months of history and the 2026 inference run sees about 69, so the same HCP drifts upward over time.

**Decision**: replace the two kept features with `NUM_OF_PATIENTS_IN_HCP_DX_PANEL_WITH_DIABETIC_CKD_IN_LAST_730_DAYS` and `..._WITH_CKD_IN_LAST_730_DAYS` (distinct patients, fixed 24-month window ending at each cohort's lookback end). Drop the overall and `CV_KD` running totals.

### 1.4 Window shares (#4)

`PCT_TOTAL_DX_PATIENTS_CV_KD_IN_LAST_12_MONTH` is the strongest comorbidity feature in the 752 (rank 88, 0.25%), but the direction is the opposite of what the name suggests: AUC 0.344, so **0.66 (inverse)**, and 0.68 (inverse) in size. A high share mostly means a small kidney panel where one or two cardio-renal patients give 50 to 100%. The `DB_KD` share behaves the same (0.35, in size 0.29). For new writers the signal is close to none (0.54).

**Decision**: keep one 12-month share per indication group, rebuilt as distinct patients in the group / distinct patients in the HCP's Dx panel (always between 0 and 1). Drop the 1/3/6-month shares. Keep the existing 752 feature only until the rebuilt share is tested.

### 1.5 Diagnosis groups (#5)

`FIN_DIAG_CD` groups only kidney codes. For NBA 3.1:

* HF patients without a kidney code are invisible, although HF (LVEF >= 40%) is now an indication.
* T1D is not grouped at all. In the final 752 no feature mentions T1D.
* CKD stage 3 has 23,981 patients in `Dx_09` (one description, `N18.3`), against 9.69M for the 4 descriptions that mention stage 4 (these include the hypertensive CKD "stage 1 through stage 4" codes), because N18.30 / N18.31 / N18.32 are missing. Stage 3 is the core Kerendia population, and the stage 3 share is the best new Dx feature in the backtest (2.2).

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

Feature naming: each stem gives `NUM_OF_PATIENTS_IN_HCP_DX_PANEL_WITH_{stem}_IN_LAST_365_DAYS_DX` and `PCT_OF_PATIENTS_IN_HCP_DX_PANEL_WITH_{stem}_IN_LAST_365_DAYS_DX` (= NUM / panel size). Median Dx panel: 125 patients.

### 2.1 Indication mix of the Dx panel (#1): Dx

**Business meaning**: how many of the HCP's patients fit each Kerendia indication. This tells NBA which HCPs see the T2D-CKD, T1D-CKD and HF populations that Kerendia now covers. For HF and T1D this is the first time the model sees these populations at all.

| Stem | Non-zero | Median NUM / PCT | AUC (NUM / PCT) | AUC in size (NUM / PCT) | AUC new writers (NUM / PCT) |
| --- | --- | --- | --- | --- | --- |
| `T2D_CKD` | 92.2% | 15 / 0.124 | 0.696 / 0.683 | 0.659 / 0.676 | 0.545 / 0.594 |
| `T1D_CKD` | 49.9% | 1 / 0.001 | 0.662 / 0.629 | 0.635 / 0.616 | 0.546 / - |
| `HF_LVEF_GE_40_PROXY` | 85.8% | 6 / 0.049 | 0.662 / 0.597 | 0.649 / 0.632 | 0.553 / 0.588 |
| `CKD_AND_HF` | 89.4% | 9 / 0.073 | 0.697 / 0.655 | 0.680 / 0.693 | 0.571 / 0.616 |
| `ANY_KERENDIA_INDICATION` | 93.9% | 20 / 0.171 | 0.694 / 0.680 | 0.659 / 0.689 | 0.550 / 0.615 |
| For comparison: `PCT_TOTAL_DX_PATIENTS_CV_KD_IN_LAST_12_MONTH` (NBA 3.0, rank 88) | 65.3% | - / 0.38 | 0.66 (inverse) | 0.68 (inverse) | 0.54 |

The shares (PCT) are the stronger version for new writers (0.59 to 0.62 vs 0.54 for the NBA 3.0 share), so they help the model find HCPs that have not written Kerendia yet. The counts (NUM) are stronger overall but partly repeat HCP size.

**Decision**: add NUM and PCT for `T2D_CKD`, `CKD_AND_HF`, `HF_LVEF_GE_40_PROXY` and `ANY_KERENDIA_INDICATION`. Add `T1D_CKD` as NUM only (the share is near 0 for most HCPs) and keep it even if selection drops it, as long as the T1D indication is in scope, so the model can learn it once T1D writing starts. Do not add plain `T2D`, `T1D` or `HF` counts (AUC in size 0.62, 0.62 and 0.66 for NUM). They are less specific and repeat the patient pipeline Dx features.

### 2.2 CKD stage mix (#2): Dx

**Business meaning**: Kerendia is started at eGFR >= 25 (CKD stages 1 to 4), so stage 3 and 4 patients are the core of the label population. Stage-coded CKD also means the HCP stages kidney disease actively.

| Stem | Non-zero | Median NUM / PCT | AUC | AUC in size | AUC new writers |
| --- | --- | --- | --- | --- | --- |
| `PCT_..._CKD_STAGE_3` | 92.7% | 17 / 0.150 | 0.656 | **0.714** | 0.590 |

The stage 3 share has the highest AUC in size of all Dx features tested here. This needs the stage 3a/3b codes (1.5).

**Decision**: add `PCT_..._CKD_STAGE_3` and `PCT_..._CKD_STAGE_4` (stage 4 not tested yet, same definition with `N18.4`). Do not add a stage 5 / ESRD share: ESRD is outside the label.

### 2.3 Change in indicated patients (#3): Dx

**Business meaning**: an HCP whose indicated panel is growing (new clinic, new referral source, more HF patients after a hospital affiliation) is a better target than one with a flat panel of the same size.

**Definition**: `LOGRATIO_PATIENTS_ANY_KERENDIA_INDICATION_3M = ln((n_3M / 3 + 0.5) / ((n_12M - n_3M) / 9 + 0.5))`, where n = distinct patients with any indication in the window. Same formula as the log-ratio in Patient Features Recommendations 1.4.

Not tested yet: the Dx input only starts 2025-09-30, so a 12-month backtest window was not available. The same idea for Kerendia NBRx (Prior Writing Recommendations 2.4) showed no signal (AUC 0.51), so this is medium priority and should be dropped if feature selection does not keep it.

**Decision**: build for `ANY_KERENDIA_INDICATION` only, test in selection.
