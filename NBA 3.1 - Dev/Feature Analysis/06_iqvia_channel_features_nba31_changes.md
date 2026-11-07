# NBA 3.1 IQVIA Channel Features: Changes

> **Data source update (Nov 2026):** NBA 3.1 now reads `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7` (LAAD-based LRx V7, weekly, history from Dec 2021) instead of `KERENDIA_LAAD_BASED_LRX_V6` and `KERENDIA_LAAD_BASED_LRX_FULL_DATA_STARTING_2021`. Read V6 references below as V7. V7 `WEEK_ENDING_DATE` / `PERIOD_ID` are DATEs, and `PRODUCT_GROUP` uses the lrx_nbrx names, except that the lrx_nbrx `OTHERS` bucket is split into NBA groups (METFORMIN, SULFONYLUREAS, DPP4, BASAL INSULIN, OTHER INSULIN, CGM, CCB, CKD SUPPORTIVE, VERQUVO, INPEFA) and Entresto generic, Baxfendy and Exenatide are included; NBRx is counted on these groups (see `lrx-features` SKILL.md Section 6.2). Numbers in this document were computed on V6.

This file lists the channel-feature changes for NBA 3.1: which NBA 3.0 features to remove (section 1) and the channel-mix features that replace them (section 2). How the NBA 3.0 features are built is in the companion file `NBA_3_1_IQVIA_Channel_Features_Analysis.md`. References written as "Analysis 1.x" point to sections in that file.

NBA 3.1 scope: the model target is still the HCP's **Kerendia NBRx in the 30-day prediction window**. Channel counts by month are already covered, with windows, by `1_Additional_HCP_level_features` (Analysis 1.4, item 4), so this notebook should only add what that notebook does not have: the channel **mix** of the HCP's patients.

SHAP ranks and shares come from `Final NBA 3.0 Modeling Features.xlsx` (752 features, mean absolute SHAP).

**How the signal was measured (backtest, run 2026-11-02).** Features were taken as of June 2026 (`SVC_DT_M = 2026-06-01`; windows end 2026-06-30), from the NBA 3.0 input `query_output/kerendia_nba_3_0_hcp_model_channel_23` and the NBA 3.0 output of this notebook. The target is "the HCP wrote at least one Kerendia NBRx in August 2026" (one-month gap, as in production), from `KERENDIA_LAAD_BASED_LRX_V6` with `PRODUCT_GROUP = 'KERENDIA'`. Population: the 314,920 HCPs in the NBA 3.1 universe (`kerendia_nba_3_1_volume/HCP_Universe/`), 6,704 writers, base rate 2.13%.

**Coverage of the input**: the NBA 3.0 channel input only holds HCPs of the NBA 3.0 ops universe. 223,050 of the 314,920 HCPs are in both universes. The other 91,870 have no channel data yet, so non-empty is at most 70.8% in the tables below. None of these 91,870 HCPs wrote Kerendia in August 2026, so the AUCs use all writers. The NBA 3.1 input pull (2.3) closes this gap.

* **AUC**: the chance that a random writer has a higher value than a random non-writer, over HCPs with a non-empty value. 0.50 = no signal. Below 0.50 means lower values go with more writers. In this file the direction is shown, for example "0.58 (inverse)".
* **AUC in size**: median AUC inside 3 equal groups of HCP size (all-market NBRx in January to June 2026). It shows signal that is not just "bigger HCP".
* **AUC new writers**: AUC among the 268,086 HCPs with no Kerendia NBRx since January 2023 (rate 0.55%). 22.0% of August writers came from this group, and NBA must find them.

---

## 1. Features to remove in NBA 3.1

| # | Feature group | Action | Reason |
| --- | --- | --- | --- |
| 1 | `Channel_A`, `Channel_L`, `Channel_M`, `Channel_R` (4) | Drop | None in the final 752. Single month (Analysis 1.4, item 1). Correlate 0.94 to 0.99 with the channel counts of `1_Additional_HCP_level_features`, which are in the model (15 features, 2.33% SHAP). Within size groups and for new writers they point the wrong way (AUC 0.40 to 0.52) |

Column impact: the 4 NBA 3.0 columns are replaced by the 2 channel-mix features in section 2.

### 1.1 Backtest of the NBA 3.0 counts (#1)

The 1-month values are the NBA 3.0 features. The 12-month sums were added to check whether a longer window rescues them.

| Feature | Non-empty | AUC | AUC in size | AUC new writers |
| --- | --- | --- | --- | --- |
| `Channel_A` (1 month) | 69.4% | 0.540 | 0.521 | 0.491 |
| `Channel_L` (1 month) | 69.4% | 0.521 | 0.473 | 0.459 |
| `Channel_M` (1 month) | 69.4% | 0.500 | 0.477 | 0.417 |
| `Channel_R` (1 month) | 69.4% | 0.558 | 0.469 | 0.433 |
| `Channel_A` (12-month sum) | 70.4% | 0.553 | 0.518 | 0.470 |
| `Channel_L` (12-month sum) | 70.4% | 0.530 | 0.460 | 0.442 |
| `Channel_M` (12-month sum) | 70.4% | 0.500 | 0.453 | 0.395 |
| `Channel_R` (12-month sum) | 70.4% | 0.557 | 0.424 | 0.413 |

What this shows:

* **The overall signal is only size.** `Channel_R` reaches 0.558 because bigger HCPs write more Kerendia. It correlates 0.80 (Spearman) with all-market NBRx, and inside size groups the signal turns around (0.469, 0.424 for 12 months): among HCPs with the same NBRx volume, more fill-days means a refill-heavy panel, not a Kerendia writer.
* **No signal for new writers** (all below 0.50).
* **A longer window does not help.** The 12-month sums behave like the 1-month values.

### 1.2 Overlap with `1_Additional_HCP_level_features` (#1)

`1_Additional_HCP_level_features` builds `TOTAL_HCP_RX_{ATYPICAL, LTC, MAIL_ORDER, RETAIL}_CHANNEL_CLAIMS_IN_LAST_{1,2,3,6,12}_MONTH`, running totals and drug-class splits from paid claims. Rebuilt from this notebook's input for September 2026 (the month in the ops output), the same counts correlate:

| This notebook | `1_Additional_HCP_level_features` | Spearman |
| --- | --- | --- |
| `Channel_R`, 1 month | `TOTAL_HCP_RX_RETAIL_CHANNEL_CLAIMS_IN_LAST_1_MONTH` | 0.981 |
| Retail, 12 months | `TOTAL_HCP_RX_RETAIL_CHANNEL_CLAIMS_IN_LAST_12_MONTH` | 0.985 |
| Mail order, 12 months | `TOTAL_HCP_RX_MAIL_ORDER_CHANNEL_CLAIMS_IN_LAST_12_MONTH` (rank 10, 1.12%) | 0.979 |
| LTC, 12 months | `TOTAL_HCP_RX_LTC_CHANNEL_CLAIMS_IN_LAST_12_MONTH` | 0.960 |
| Atypical, 12 months | `TOTAL_HCP_RX_ATYPICAL_CHANNEL_CLAIMS_IN_LAST_12_MONTH` | 0.935 |

Computed on the 223,050 HCPs of the 3.1 universe that are in both tables.

**Decision**: drop the 4 columns. Keep channel counts in `1_Additional_HCP_level_features` only, so there is one owner for counts.

---

## 2. Features to add in NBA 3.1

| # | Feature | Source | Hypothesis | Value | Effort |
| --- | --- | --- | --- | --- | --- |
| 1 | `PCT_PATIENTS_RETAIL_CHANNEL_IN_LAST_12_MONTH` | Rx | Kerendia is filled at retail (89.9% of Kerendia NBRx). HCPs whose patients fill at retail can start Kerendia with less friction | Medium | Quick win (same input) |
| 2 | `PCT_PATIENTS_MAIL_ORDER_CHANNEL_IN_LAST_12_MONTH` | Rx | A mail-order heavy panel (stable, maintenance patients, often PBM-managed) starts fewer new brands | Medium | Quick win |

Both are shares, so they describe the mix and not the size of the panel.

### 2.1 Backtest of channel shares

Share = distinct patients with at least one fill in the channel in the 12 months / distinct patients with any basket fill in the 12 months (July 2025 to June 2026). A patient who uses two channels counts in both, so the shares can add up to more than 1.

| Feature (12 months) | Non-empty | Median | AUC | AUC in size | AUC new writers | Spearman with size |
| --- | --- | --- | --- | --- | --- | --- |
| Retail patient share | 70.4% | 0.929 | **0.547** | **0.546** | **0.534** | 0.04 |
| Mail-order patient share | 70.4% | 0.063 | 0.536 (inverse) | 0.551 (inverse) | **0.588 (inverse)** | 0.11 |
| Atypical patient share | 70.4% | 0.009 | 0.534 | 0.544 | 0.502 | 0.05 |
| LTC patient share | 70.4% | 0.007 | 0.519 | 0.513 | 0.481 | - |
| Retail fill-day share (for comparison) | 70.4% | 0.917 | 0.542 | 0.546 | 0.532 | 0.02 |
| Mail-order fill-day share (for comparison) | 70.4% | 0.047 | 0.536 (inverse) | 0.546 (inverse) | 0.576 (inverse) | 0.08 |

What this shows:

* **The shares carry signal that the counts do not.** They are almost independent of size (Spearman 0.04 to 0.11), and the signal holds inside size groups (0.55) and for new writers, where every count in 1.1 is below 0.50.
* **Retail share** is the most even signal across the three views (0.547 / 0.546 / 0.534). Kerendia NBRx are a bit more retail than the market (89.9% vs 86.8%, LRx V6, July 2025 to June 2026).
* **Mail-order share** is the best feature for new writers (0.588 inverse). It overlaps with the mail-order count already in the model (Spearman 0.79), so it may add less after the count; it should still be tested in feature selection.
* **Patient shares are slightly better than fill-day shares** and easier to explain, and the two correlate 0.93 to 0.95.
* **Atypical and LTC shares** are weak (0.48 to 0.54). The atypical share also correlates 0.89 with the atypical count. Do not add.

**Decision**: add the retail and mail-order patient shares over 12 months. Drop the atypical and LTC shares.

### 2.2 Build logic

For each claims cohort (`kerendia_nba_3_1_volume/cohorts/claims/cohorts.parquet`) and each HCP in the 3.1 universe:

1. **Window**: fills with `SVC_DT` from the first day of the month 11 months before `lookback_end_date` to the last day of the `lookback_end_date` month (12 full months).
2. **Panel**: distinct `PATIENT_ID` with any basket fill from this HCP in the window.
3. **Channel patients**: distinct `PATIENT_ID` with at least one fill in channel `R` (retail) or `M` (mail order) in the window.
4. **Share**: channel patients / panel. Empty when the panel is 0 (the HCP had no basket fill in the window).
5. **Claim types**: all claim types, as in the NBA 3.0 input and the backtest.
6. **Key**: `HCP_COHORT_ID` = `PROVIDER_ID` + `_` + `cohort_id`.

### 2.3 Where each change is implemented

| Change | Notebook | What to change |
| --- | --- | --- |
| Input | `NBA 3.1 - Dev/00_Helper_Notebooks/00_Write_HCP_Inputs_31` | Add the "File Channel 23" SQL (distinct `PROVIDER_ID`, `PATIENT_ID`, `SVC_DT`, `CHANNEL_CODE`, same product and channel filters). Join to the 3.1 universe, start at the first day of the month 11 months before the first cohort's `lookback_end_date` and end at the last cohort's lookback-end month. Save to `kerendia_nba_3_1_volume/hcp_level_model/ops_pipeline/query_output/Rx_channel_23` |
| Drop counts (#1) and add shares (2.1) | `23_IQVIA_channel_features` (NBA 3.1 version) | Replace the monthly pivot with the per-cohort patient shares in 2.2. Drop `Channel_A/L/M/R`, the `BHID` join and the ID-mapping input. Save to `kerendia_nba_3_1_volume/notebook_output/hcp_features/iqvia_channel_features` |
| Combine | `99_Combine_Physician_Data` | Join on `HCP_COHORT_ID` instead of `PROVIDER_ID` + `SVC_DT_M` |
