# NBA 3.1 Kerendia Prior Writing Features: Changes

This file lists the prior-writing changes for NBA 3.1: the new data source and methodology for the Kerendia NBRx and TRx features (section 1). How the NBA 3.0 features are built is in the companion file `NBA_3_1_Kerendia_Prior_Writing_Features_Analysis.md`. References written as "Analysis 1.x" point to sections in that file.

NBA 3.1 scope: the model target is the HCP's **Kerendia NBRx in the 30-day prediction window**. Kerendia now covers **T2D with CKD, T1D with CKD and HF with LVEF >= 40%**. Prior writing is the strongest signal family in the model, so the goal here is a Kerendia writing history that adds information beyond the paid-claims features in `26_Features_NBRx`.

SHAP ranks and shares come from `Final NBA 3.0 Modeling Features.xlsx` (752 features, mean absolute SHAP).

**How the signal was measured (backtest).** Features were taken as of June 2026 (lookback end 2026-06-30). The target is "the HCP wrote at least one Kerendia NBRx in August 2026" (one-month gap, as in production), from `KERENDIA_LAAD_BASED_LRX_V6` with `PRODUCT_GROUP = 'KERENDIA'`. Population: the 234,405 HCPs in the ops universe, base rate 2.87%.

* **AUC**: the chance that a random writer has a higher value than a random non-writer. 0.50 = no signal. Below 0.50 means lower values go with more writers, shown as "(inverse)".
* **AUC in size**: median AUC inside 3 equal groups of all-market NBRx (January to June 2026). It shows signal that is not just "bigger HCP".
* **Prior writers**: 46,915 HCPs (20%) with any Kerendia NBRx from January 2023 to June 2026. Their August writer rate is 11.1%.
* **New writers**: the other 187,490 HCPs. Their writer rate is 0.8%, but they supply 22% of August writers.

---

## 1. Features to remove or change in NBA 3.1

| # | Feature group | Action | Reason |
| --- | --- | --- | --- |
| 1 | `KERENDIA_NBRX_IN_LAST_{1..6}_MONTH` (6 columns, 5 in the 752) | Replace the current values (built from LRx V6) | They are redundant with the Kerendia NBRx features in `26_Features_NBRx`, which come from the same LRx table and paid claims (Analysis 1.4, item 1) |
| 2 | Data source of `10_kerendia_prior_writing` | **Change to the raw FCT_RX Kerendia table (all claim types)** and rebuild NBRx in the same format. Add TRx in the same format. Add the same NBRx and TRx features for **rejected**, **reversed** and **approved (paid + reversed)** claims | All claim types (paid, rejected, reversed) give a Kerendia writing signal that `26_Features_NBRx` (paid only) does not have |
| 3 | Six adjacent windows (1 to 6 months) | Keep the original 1 to 6-month format | Same format as the NBA 3.0 table. Adjacent windows are highly correlated, so feature selection is expected to keep only some of them |

### 1.1 The current features repeat `26_Features_NBRx` (#1)

`26_Features_NBRx` reads the same LRx table (paid claims), pivots `PRODUCT_GROUP`, and builds 1/3/6/12-month and running totals. For the scoring month (September 2026), the Kerendia NBRx over the last 1, 3 and 6 months from `10_kerendia_prior_writing` matches `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_{1,3,6}_MONTH` for all 234,403 universe HCPs (0 differences). The 2, 4 and 5-month windows are adjacent windows of the same count. The Kerendia columns from `26_Features_NBRx` are already the strongest prior-writing features in the 752:

| Feature in the 752 | Rank | SHAP share |
| --- | --- | --- |
| `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_12_MONTH` | 2 | 2.18% |
| `RUNNING_TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA` | 5 | 1.64% |
| `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_6_MONTH` | 194 | 0.13% |
| `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_3_MONTH` | 317 | 0.08% |
| `TOTAL_HCP_NBRX_CLAIMS_PRODUCT_GROUP_KERENDIA_IN_LAST_1_MONTH` | 514 | 0.04% |

The 12 Kerendia product-group features from `26_Features_NBRx` (NBRx, NRx, TRx) hold 4.6% of SHAP together. Kerendia recency is also covered by `KERENDIA_RX_TIME_MIN` (rank 3).

Backtest of the paid Kerendia NBRx counts (June 2026 features, August 2026 target): AUC 0.650 / 0.739 / 0.787 / 0.820 for 1 / 3 / 6 / 12 months, 0.642 / 0.745 / 0.791 / 0.825 within size groups. This signal is already in the model through `26_Features_NBRx`.

**Decision**: keep `10_kerendia_prior_writing`, but stop building it from LRx V6. Rebuild it from the all-claims source in 1.2 so that it adds information instead of repeating `26_Features_NBRx`.

### 1.2 New data source: Kerendia NBRx and TRx from raw FCT_RX, all claim types (#2)

**New source**: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/dev_folder_3_1/notebook_output/kerendia_nbrx_from_raw_fct_rx/` (Delta). It is written by the notebook `Kerendia_NBRX_From_Raw_FCT_RX` (`01_HCP_Universe/Raw Claims NBRX Calculation/`).

**How it differs from `26_Features_NBRx`**: this table counts Kerendia NBRx over **all claim types: paid (PD), rejected (RJ) and reversed (RV)**. `26_Features_NBRx` uses LRx V6, which counts **paid claims only**. A rejected or reversed claim still shows that the HCP chose to write Kerendia, even if the patient did not get the drug. This is the writing signal the target is about, and it is lost when only paid claims are counted.

| Item | Definition in the source notebook |
| --- | --- |
| Claims | IQVIA LAAD `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX` joined to `STG_CAR_IQV_LAAD_DIM_PRD` on `NDC_CD`, `PRODUCT_GROUP = 'KERENDIA'`, full history, all `CLAIM_TYPE` values |
| NBRx | Per patient: the first-ever Kerendia claim, or a claim more than 365 days after the patient's previous Kerendia claim. One claim per patient per day (lowest `CLAIM_ID`) |
| TRx | Every Kerendia claim counts as one TRx |
| Columns | `NBRX_KERENDIA_OVERALL` (all claim types), `NBRX_KERENDIA_PD` (paid only), `TRX_KERENDIA_OVERALL`, `TRX_KERENDIA_PD`, `FIRST_KERENDIA_CLAIM`, `LAST_KERENDIA_CLAIM` |

Content at review (written 2026-10-16): 91,751 HCPs (84,828 in the NBA 3.1 universe), claims from 2021-07-20 to 2026-09-18.

| Measure | All claim types | Paid only | Ratio |
| --- | --- | --- | --- |
| Kerendia NBRx | 494,371 | 241,041 | 2.05x |
| Kerendia TRx | 4,256,864 | 2,904,663 | 1.47x |
| HCPs with NBRx > 0 | 61,583 | 43,114 | 18,469 HCPs have non-paid NBRx only |

About half of all Kerendia NBRx and 18,469 writers are not visible in paid claims. These are HCPs who already write Kerendia but look like non-writers in `26_Features_NBRx`.

**New features (same format as the NBA 3.0 table)**

| Feature | Definition |
| --- | --- |
| `KERENDIA_NBRX_IN_LAST_{N}_MONTH`, N = 1 to 6 | Sum of monthly Kerendia NBRx, **all claim types**, over the last N calendar months ending with the lookback-end month |
| `KERENDIA_TRX_IN_LAST_{N}_MONTH`, N = 1 to 6 | Sum of monthly Kerendia TRx, **all claim types**, over the same windows |
| `KERENDIA_NBRX_REJECTED_IN_LAST_{N}_MONTH`, `KERENDIA_TRX_REJECTED_IN_LAST_{N}_MONTH` | Same, **rejected claims only** (`CLAIM_TYPE = 'RJ'`) |
| `KERENDIA_NBRX_REVERSED_IN_LAST_{N}_MONTH`, `KERENDIA_TRX_REVERSED_IN_LAST_{N}_MONTH` | Same, **reversed claims only** (`CLAIM_TYPE = 'RV'`) |
| `KERENDIA_NBRX_APPROVED_IN_LAST_{N}_MONTH`, `KERENDIA_TRX_APPROVED_IN_LAST_{N}_MONTH` | Same, **approved claims = paid + reversed** (`CLAIM_TYPE IN ('PD', 'RV')`) |

That is 4 claim-type groups x 2 measures (NBRx, TRx) x 6 windows = **48 features**. The all-claim-types features keep the NBA 3.0 names. By construction, all claim types = approved + rejected for every window.

**How the claim-type split works for NBRx**: the NBRx flag (step 3) is set on the patient's full history across all claim types. A new-to-brand event is then counted in the group of the claim that carries the flag (the first claim of that patient on that day, lowest `CLAIM_ID`). So the rejected NBRx count is "new Kerendia patients whose first claim was rejected", not a separate NBRx history built from rejected claims only. This keeps the groups additive and "first-ever" correct.

**How to get the last N month claims (logic of `Kerendia_NBRX_From_Raw_FCT_RX`, all claim types)**

The saved table has one row per HCP with lifetime totals and no date column, so the N-month windows are built from the same claim-level logic as that notebook, kept at month level instead of rolled up to the HCP. Steps 1 to 3 are copied unchanged from the notebook. Steps 4 to 6 replace its HCP-level rollup.

1. **Pull Kerendia claims, all claim types.** `SELECT DISTINCT CLAIM_ID, PATIENT_ID, TO_DATE(SVC_DT) AS SVC_DT, PROVIDER_ID, CLAIM_TYPE, TRIM(UPPER(PRODUCT_GROUP)) AS PRODUCT_GROUP` from `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX` inner-joined to `STG_CAR_IQV_LAAD_DIM_PRD` on `NDC_CD`, `WHERE TRIM(UPPER(PRODUCT_GROUP)) = 'KERENDIA'`. No date window and no `CLAIM_TYPE` filter, so paid (PD), rejected (RJ) and reversed (RV) claims are all kept. `PROVIDER_ID` is cast to string.
2. **One claim per patient per day.** `CLAIM_RANK = row_number()` over `PATIENT_ID`, `PRODUCT_GROUP`, `SVC_DT` ordered by `CLAIM_ID`. Only `CLAIM_RANK = 1` can be an NBRx.
3. **NBRx flag, per patient across all HCPs.** Over `PATIENT_ID`, `PRODUCT_GROUP` ordered by `SVC_DT`: `NBRX_FLAG = 1` when (`SVC_DT` = the patient's first-ever Kerendia date and `CLAIM_RANK = 1`) or (the previous claim date `LAG(SVC_DT)` is more than 365 days earlier and `CLAIM_RANK = 1`), else 0. Compute this on the **full** history and before any universe or date filter, otherwise "first-ever" and the 365-day gap are wrong.
4. **Monthly totals per HCP and claim-type group** (replaces the HCP-level rollup). `CLAIM_TYPE` is trimmed and upper-cased. Group by `PROVIDER_ID` and `SVC_DT_M = trunc(SVC_DT, 'month')`, and for each group `G`:
   * `NBRX_KERENDIA_{G} = SUM(NBRX_FLAG)` over the claims of group `G`
   * `TRX_KERENDIA_{G} = COUNT(claims)` of group `G` (every claim row)

   | Group `G` | Claims |
   | --- | --- |
   | `OVERALL` | All claim types (PD + RJ + RV) |
   | `PD` | Paid. Check column only, not a feature |
   | `RJ` | Rejected |
   | `RV` | Reversed |
   | `APPROVED` | Paid + reversed |

   Check: `OVERALL = PD + RJ + RV` and `APPROVED = PD + RV` on every row. If it fails, `CLAIM_TYPE` has values other than PD, RJ and RV.
5. **Last N months per cohort.** For each claims cohort (`kerendia_nba_3_1_volume/cohorts/claims/cohorts.parquet`), the N-month window is the N calendar months ending with the cohort's `lookback_end_date`: `SVC_DT_M` from `add_months(lookback_end_date, -(N-1))` to `lookback_end_date`.
   * `KERENDIA_NBRX_IN_LAST_{N}_MONTH = SUM(NBRX_KERENDIA_OVERALL)` over that window
   * `KERENDIA_TRX_IN_LAST_{N}_MONTH = SUM(TRX_KERENDIA_OVERALL)` over that window
   * `KERENDIA_{NBRX,TRX}_REJECTED_IN_LAST_{N}_MONTH` from `..._RJ`, `KERENDIA_{NBRX,TRX}_REVERSED_IN_LAST_{N}_MONTH` from `..._RV`, `KERENDIA_{NBRX,TRX}_APPROVED_IN_LAST_{N}_MONTH` from `..._APPROVED`
   * N = 1 to 6
   
   This gives the same values as the 3.0 build (full calendar with empty months = 0, then `step3_lag` sums over exactly N months), read at `SVC_DT_M = lookback_end_date`.
6. **Universe and output.** Keep HCPs in the NBA 3.1 universe (`kerendia_nba_3_1_volume/HCP_Universe/`, 314,920 HCPs). Cross-join them with the cohorts, left-join the windows, and fill 0 for HCPs with no Kerendia claim in a window. Key on `PROVIDER_ID`, `cohort_id`, `SVC_DT_M` and `HCP_COHORT_ID`. Save to `kerendia_nba_3_1_volume/notebook_output/hcp_features/kerendia_prior_writing`.

*Example:* for cohort c28 (`lookback_end_date` 2026-08-01), `KERENDIA_NBRX_IN_LAST_3_MONTH` is the HCP's NBRx flags over all claim types with `SVC_DT` from 2026-06-01 to 2026-08-31. `KERENDIA_TRX_IN_LAST_3_MONTH` is the count of all the HCP's Kerendia claims in the same months. `KERENDIA_TRX_REJECTED_IN_LAST_3_MONTH` counts only the rejected ones, and `KERENDIA_TRX_APPROVED_IN_LAST_3_MONTH` the paid and reversed ones.

The paid columns (`NBRX_KERENDIA_PD`, `TRX_KERENDIA_PD`) are not features. They are kept to check that paid NBRx is in line with the LRx-based `26_Features_NBRx` counts.

**Checks before using the features**

* The NBRx flag only looks back at the patient's earlier claims, so monthly values use no future data. Still cap the features at each cohort's lookback end.
* A reversed claim is usually paired with the original paid claim. For NBRx, a paid and a reversed claim on the same day count once (step 2). On different days they can count twice, if the gap is over 365 days. **TRx counts every claim row, so a paid + reversed pair always counts as 2 TRx.** Check how often this happens before relying on `KERENDIA_TRX_IN_LAST_{N}_MONTH`. The same applies to the approved group, which counts a paid claim and its reversal as 2 approved TRx.
* "Approved" here is defined as paid + reversed. A reversed claim was paid first and then cancelled, so the group means "claims the payer accepted at least once". Rejected claims were never accepted.
* Refresh the claim pull before each run so it covers the latest cohort `lookback_end_date` (the saved HCP-level table ends on 2026-09-18).
* Backtest the all-claims NBRx and TRx against the paid-only `26_Features_NBRx` columns (AUC, AUC in size, new writers) before adding them to the model.

### 1.3 Window count (#3)

Adjacent N-month windows share most of their months (for example 5M and 6M share 5 of 6 months), so they carry nearly the same information. The Kerendia NBRx counts gain signal mostly between 1, 3, 6 and 12 months (AUC 0.65, 0.74, 0.79, 0.82).

**Decision**: the rebuilt `KERENDIA_NBRX_IN_LAST_{N}_MONTH` and `KERENDIA_TRX_IN_LAST_{N}_MONTH` keep the 1 to 6-month format of the NBA 3.0 table, and so do the rejected, reversed and approved versions. Feature selection drops the redundant windows and groups.

### 1.4 Where each change is implemented

| Change | Notebook (under `03_HCP_Level_Features`) | What to change |
| --- | --- | --- |
| New data source and methodology (#1, #2) | `NBA 3.1 - Dev/03_HCP_Level_Features/10_kerendia_prior_writing` | Replace the LRx V6 query with the all-claims Kerendia pull and NBRx logic of `Kerendia_NBRX_From_Raw_FCT_RX` (1.2, steps 1 to 3). Save the monthly table (step 4) to `kerendia_nba_3_1_volume/hcp_level_model/ops_pipeline/query_output/kerendia_claims_monthly_from_raw_fct_rx`. Build `KERENDIA_NBRX_IN_LAST_{1..6}_MONTH` and `KERENDIA_TRX_IN_LAST_{1..6}_MONTH` (all claim types), plus the `_REJECTED`, `_REVERSED` and `_APPROVED` versions, per claims cohort (steps 5 and 6). 48 features |
| Combine step | `99_Combine_Physician_Data` (3.1 version) | Join on `HCP_COHORT_ID` and add the 42 new columns (6 TRx + 36 claim-type columns) to the feature list |
