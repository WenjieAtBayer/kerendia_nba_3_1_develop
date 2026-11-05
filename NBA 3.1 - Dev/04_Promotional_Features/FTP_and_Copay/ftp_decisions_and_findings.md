# FTP Features — Notebook Run Findings & Design Decisions

**Notebook:** `19_ftp_features` (NBA 3.1)  
**Run date:** 30 October 2026  
**Cohort:** I01 | Lookback: 2025-10-17 → 2026-10-17  
**Output path:** `.../ops_pipeline/notebook_output/kerendia_nba_3_1_hcp_model_ftp_features_for_inference`

---

## 1. Run Results

| Step | Count | Notes |
| --- | --- | --- |
| Raw FTP rows from new source | 268,015 | All-time FTP transactions, all HCPs |
| Distinct HCPs in raw data | 18,263 | `BAYER_HCP_ID IS NOT NULL` |
| Base aggregated (HCP × day) | 112,934 | `SUM(FTP_TRX)` per BHID per MONTH_ID |
| HCPs active in lookback window | ~4,556 unique | After cross-join filter to 2025-10-17–2026-10-17 |
| **Final output rows** | **4,556** | One row per HCP with ≥1 FTP in the lookback |
| **Final output columns** | **9** | See schema below |
| Written to Delta | ✅ | Overwrite succeeded |

### Output Schema

| Column | Type | Description |
| --- | --- | --- |
| `HCP_COHORT_ID` | string | Bayer HCP ID + cohort (e.g. BH10000526_I01) |
| `PULL_DT` | date | Anchor / lookback end date (2026-10-17) |
| `TOTAL_RX_FTP_IN_LAST_1_MONTH` | double | FTP transactions in last 30 days |
| `TOTAL_RX_FTP_IN_LAST_2_MONTH` | double | FTP transactions in last 60 days |
| `TOTAL_RX_FTP_IN_LAST_3_MONTH` | double | FTP transactions in last 90 days |
| `TOTAL_RX_FTP_IN_LAST_4_MONTH` | double | FTP transactions in last 120 days |
| `TOTAL_RX_FTP_IN_LAST_5_MONTH` | double | FTP transactions in last 150 days |
| `TOTAL_RX_FTP_IN_LAST_6_MONTH` | double | FTP transactions in last 180 days |
| `RUNNING_TOTAL_RX_FTP` | double | Cumulative FTP transactions over the full lookback |

### Sample Output

| HCP_COHORT_ID | PULL_DT | last_1M | last_2M | last_3M | last_4M | last_5M | last_6M | RUNNING |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BH10000526_I01 | 2026-10-17 | 6.0 | 9.0 | 9.0 | 15.0 | 15.0 | 15.0 | 18.0 |
| BH10001167_I01 | 2026-10-17 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2.0 |
| BH10002507_I01 | 2026-10-17 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2.0 | 2.0 |
| BH10003840_I01 | 2026-10-17 | 0.0 | 0.0 | 2.0 | 2.0 | 2.0 | 2.0 | 4.0 |

**Validation checks passed:**
* Lag features are monotonically non-decreasing (last_1 ≤ last_2 ≤ ... ≤ last_6) ✅
* RUNNING_TOTAL ≥ TOTAL_IN_LAST_6_MONTH ✅
* PULL_DT = cohort LOOKBACK_END_DATE (2026-10-17) for all rows ✅
* No nulls in feature columns (fillna(0) applied) ✅
* Output is sparse: only HCPs with ≥1 FTP event in lookback are included; downstream joins should use a left join to assign 0 to the rest ✅

---

## 2. Design Decisions on Open Questions

### Decision 1: Include BRIDGE rows?
**Decision: No. Keep FTP only.**

Rationale: BRIDGE (`SALE_TYP = 'BRIDGE'`, 1,265 rows) is a bridge-to-insurance program — it covers patients while they wait for insurance approval. It is a distinct market access program from FTP. Mixing them would change the feature’s meaning: `TOTAL_RX_FTP` should specifically represent free-trial starts, not all Bayer-subsidised dispensings. BRIDGE should be its own notebook/feature if needed.

### Decision 2: Add FTP_NRX (new Rx only) as separate features?
**Decision: Not included in this run; flag as a future enhancement.**

Rationale: `FTP_NRX` counts only first-ever FTP prescriptions (new patient starts), which is a potentially valuable NBA signal. However, adding 6 more lag columns doubles the feature set without a validated need from the model team. Keeping the current 6 `TOTAL_RX_FTP` (all transactions) features is the conservative choice. If feature importance analysis later shows `FTP_NRX`-style features are needed, add a second aggregation block in the notebook.

### Decision 3: Which SALE_CHNL_DESC values to include?
**Decision: All SALE_TYP='FTP' rows regardless of channel.**

Rationale: The `SALE_TYP='FTP'` filter is the primary business selector. The three channel values — "Bayer FTP" (224K rows), "FTP" (43K rows), "SP" (12 rows) — all represent legitimate FTP transactions. The `SALE_CHNL_DESC` distinction reflects the data feed source/formatting, not a meaningful programmatic difference. A channel-level split would add noise without clear benefit. The old view also didn’t distinguish by channel.

### Decision 4: Filter out PDRP-opted HCPs?
**Decision: No explicit PDRP filter needed.**

Rationale: Some rows have `HCP_NPI_NUM = 'PDRP'` (Patient Data Request Protection opt-out, meaning NPI was masked), but their `BAYER_HCP_ID` is a valid Bayer HCP ID. FTP transactions for these HCPs are legitimate and already filtered at source by `SALE_TYP='FTP'`. The old notebook filtered on `PRSC_NPI IS NOT NULL`, which would still have included PDRP-NPI rows if their NPI was populated. The current filter `BAYER_HCP_ID IS NOT NULL` is equivalent. If compliance rules require PDRP exclusion at the NBA level, that is handled in the HCP universe filter upstream, not here.

---

## 3. Comparison with NBA 3.0 Output

| Metric | NBA 3.0 | NBA 3.1 |
| --- | --- | --- |
| HCPs in output | ~13,388 | 4,556 |
| Lookback window | 2024-09-17 → 2025-09-17 | 2025-10-17 → 2026-10-17 |
| Anchor date (PULL_DT) | 2025-09-17 | 2026-10-17 |
| Features | 6 lag (TOTAL_RX_FTP_IN_LAST_N_MONTH) | 6 lag + RUNNING_TOTAL_RX_FTP |
| Reversal handling | Yes (2nd Snowflake query) | None needed |
| NPI→BHID mapping | Yes (inner join) | None needed |

The lower HCP count (4,556 vs 13,388) reflects the different lookback window and cohort date, not a data loss. The lookback starts October 2025, and FTP activity has lower density in the most recent period.

---

## 4. Known Limitations & Future Improvements

| Item | Detail |
| --- | --- |
| Sparse output | HCPs with 0 FTP in the lookback are absent from the output. Downstream must use a left join. |
| RUNNING_TOTAL scope | Runs only within the lookback window (not all-time). Doctors who started FTP before the lookback will show 0s in the lag features even if RUNNING_TOTAL > 0. |
| FTP_NRX not used | Could add 6 FTP_NRX lag features (new starts only) in a future iteration. |
| BRIDGE not tracked | SALE_TYP='BRIDGE' is not captured. Add a separate feature if bridge program tracking is needed. |
