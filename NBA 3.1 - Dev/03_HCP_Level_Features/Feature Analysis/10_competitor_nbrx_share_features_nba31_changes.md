# NBA 3.1 Competitor NBRx Share Features: Changes

This file lists the competitor NBRx share changes for NBA 3.1. How the NBA 3.0 features are built is in `09_competitor_nbrx_share_features_analysis.md`.

NBA 3.1 scope: the model target is still the HCP’s **Kerendia NBRx in the 30-day prediction window**, with the indication set now covering HF (LVEF ≥ 40%) and T1D + CKD in addition to T2D + CKD.

References written as “Analysis 1.x” point to sections in `09_competitor_nbrx_share_features_analysis.md`.

---

## 1. Issues in the NBA 3.0 build to fix

| # | Issue | Action |
| --- | --- | --- |
| 1 | All indication groups, not CKD-only (Analysis 1.5, point 1) | Filter to CKD-relevant indications only |
| 2 | Denominator is only 4 SGLT2 drugs — no MRAs, no Kerendia (Analysis 1.5, point 2) | Keep as indication-scoped SGLT2 comparator; add a separate steroidal MRA comparator |
| 3 | Invokana and Steglatro near-zero by 2025–2026 (Analysis 1.5, point 3) | Keep in drug list but deprioritise in feature selection |
| 4 | Static build — no cohort window, potential data leakage in training (Analysis 1.5, point 4) | Rebuild per cohort, capped at `lookback_end_date` |
| 5 | Only a 12-month window; no shorter window for recent trend (Analysis 1.2) | Add a 3-month window to capture momentum |
| 6 | No indication-split feature — cannot distinguish CKD SGLT2 prescribing from T2D SGLT2 prescribing | Add CKD-filtered variant of total SGLT2 share |

---

## 2. New feature design

### 2.0 Indication scope

For NBA 3.1, compute two versions of the competitor features, distinguished by the `INDICATION_GROUP` filter applied when pulling the LRx data:

| Scope | Filter | Rationale |
| --- | --- | --- |
| CKD-relevant | `INDICATION_GROUP` contains `'CKD'` (e.g., CKD, T2D+CKD, T2D+CKD+CVD, T2D+CKD+HF, T2D+CKD+CVD+HF, CKD+CVD, CKD+HF, CKD+CVD+HF) | Directly measures SGLT2 adoption in CKD patients |
| All-indication | No filter (as in NBA 3.0) | Broader SGLT2 brand preference signal; easier to populate |

Both scopes use the same drug list (2.1).

### 2.1 Drug list

| `{DRUG}` | `PRODUCT_GROUP` values | Class | Change from NBA 3.0 |
| --- | --- | --- | --- |
| `FARXIGA` | `FARXIGA BRAND`, `FARXIGA GENERICS` | SGLT2 | Unchanged. Add generic dapagliflozin by ensuring LIKE '%FARXIGA%' keeps both. |
| `JARDIANCE` | `JARDIANCE`, `EMPAGLIFLOZIN_JARDIANCE COMBOS` | SGLT2 | Unchanged |
| `INVOKANA` | `INVOKANA`, `CANAGLIFLOZIN_INVOKANA COMBOS` | SGLT2 | Keep but low priority for selection |
| `STEGLATRO` | `STEGLATRO`, `ERTUGLIFLOZIN_STEGLATRO COMBOS` | SGLT2 | Keep but low priority for selection |
| `STEROIDAL_MRA` | `SPIRONOLACTONE`, `EPLERENONE` | Steroidal MRA | **New.** Same group added for the adoption features (file 04). HCPs who already use a steroidal MRA for CKD patients are the closest to Kerendia adoption. |

Note: Kerendia itself is not in the competitor drug list. It is the model target. If a Kerendia NBRx share feature is useful, it belongs in the prior-writing feature family (files 07–08).

### 2.2 Windows

| Window | Name suffix | Business meaning |
| --- | --- | --- |
| 3 months | `_IN_LAST_3_MONTH` | Recent momentum (was the HCP’s Jardiance prescribing accelerating?) |
| 12 months | `_IN_LAST_12_MONTH` | Stable practice pattern (NBA 3.0 window) |

Drop the 12-month running total (same leakage and data-start issue as in the comorbidity running totals; see file 02).

### 2.3 Features built

For each drug group D and window W:

| Feature | Description |
| --- | --- |
| `TOTAL_NBRX_{D}_{SCOPE}_{W}` | Sum of NBRx for drug D in window W, within the indication scope |
| `PERC_{D}_NBRX_SHARE_{SCOPE}_{W}` | `TOTAL_NBRX_{D}_{SCOPE}_{W}` / `TOTAL_NBRX_SGLT2_{SCOPE}_{W}` |

Total new features: 2 drugs (Farxiga + Jardiance, the two meaningful ones) × 2 scopes × 2 windows × 2 types (count + share) = 16 primary features, plus Invokana, Steglatro and steroidal MRA counts in CKD scope only = ~22 features total. Expect feature selection to drop most, keeping only the strongest 2–4.

### 2.4 Cohort logic

Build each feature per claims cohort (`kerendia_nba_3_1_volume/cohorts/lrx/cohorts.parquet`) with `PERIOD_ID` up to the cohort’s `lookback_end_date`. Join in `99_Combine_Physician_Data` on `HCP_COHORT_ID` instead of `NPI_NUMBER` + `SVC_DT_M`.

---

## 3. Where each change is implemented

| Change | Notebook | What to change |
| --- | --- | --- |
| Indication scope (# 1) | `31_Competitor_drugs_NBRX_share` (to be renamed or replaced) | Add `INDICATION_GROUP LIKE '%CKD%'` filter variant; add all-indication variant |
| Steroidal MRA group (# 2 new drug) | Same | Add `SPIRONOLACTONE`, `EPLERENONE` to the product filter; build denominator only for SGLT2 group |
| Cohort logic (# 4) | Same | Replace the static pull with a cohort loop over `lookback_end_date`, consistent with the pattern in `11_adoption_features` |
| 3-month window (# 5) | Same | Add `last_i_month_list = [3, 12]` in `step3_lag` |
| Inputs | `00_Write_HCP_Inputs_31` | Confirm LRx pull includes `INDICATION_GROUP` column |

---

## 4. Priority and expected value

| Feature | Expected signal | Priority |
| --- | --- | --- |
| `PERC_JARDIANCE_NBRX_SHARE_CKD_IN_LAST_12_MONTH` | HCPs with high Jardiance CKD share have already identified and treated CKD patients with SGLT2; lower bar to Kerendia | High |
| `PERC_FARXIGA_NBRX_SHARE_CKD_IN_LAST_12_MONTH` | Same logic; also captures generic dapagliflozin prescribers | High |
| `TOTAL_NBRX_JARDIANCE_CKD_IN_LAST_12_MONTH` | HCP size in CKD SGLT2; correlated with panel size | Medium (feature selection will decide) |
| `PERC_JARDIANCE_NBRX_SHARE_ALL_IN_LAST_3_MONTH` | Momentum in all-indication Jardiance prescribing; quick proxy for SGLT2-active HCPs | Medium |
| `TOTAL_NBRX_STEROIDAL_MRA_CKD_IN_LAST_12_MONTH` | Existing MRA use in CKD — the closest therapeutic predecessor to Kerendia | Medium |
| Invokana, Steglatro | Near-zero for most HCPs; keep for completeness but expect selection to drop | Low |
