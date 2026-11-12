# FTP Features — Drift Analysis & NBA 3.1 Revamp Strategy

**Channel:** Free Trial Program (FTP) — Market access promotional features  
**Old notebook:** `19_ftp_features` in `.../NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**New notebook target:** `.../NBA 3.1 - Dev/04_Promotional_Features/FTP_and_Copay/19_ftp_features`  
**Date:** 30 October 2026  
**Built from:** reading both old and new data sources via Snowflake and comparing schemas, counts, and sample data

---

## 1. Data Source Change Summary

| Aspect | Old (NBA 3.0) | New (NBA 3.1) |
| --- | --- | --- |
| **Table** | `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP` | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_SALES_ALIGNED` |
| **Type** | Snowflake view | Snowflake table |
| **Granularity** | Claim-level (one row per pharmacy claim transaction) | Sales-fact-level (one row per HCP × date × product × channel) |
| **Total columns** | 73 | 495 |
| **Rows (FTP-filtered)** | 134,311 (USE_SLS='Y', NPI not null) | 268,020 (SALE_TYP='FTP') |
| **Distinct HCPs** | 16,066 NPIs | 18,263 BAYER_HCP_IDs |
| **Date range** | Jan 2023 – Dec 2025 | Aug 2019 – Oct 2026 |
| **HCP identifier** | `PRSC_NPI` (prescriber NPI, needs mapping to BHID) | `BAYER_HCP_ID` / `CUST_HCP_ID` (direct Bayer HCP ID) |
| **Date column** | `RX_DT` (datetime string "MM/dd/yyyy HH:mm:ss") | `DATE_ID` (text, YYYYMMDD format) |
| **Claim tracking** | `CLM_AUTH_NUM`, `ORGN_CLM_AUTH_NUM` (for reversal handling) | Not available — pre-aggregated |
| **FTP metric** | Derived by counting claim rows | Pre-computed: `FTP_TRX`, `FTP_NRX`, `FTP_UNIT` |
| **Filter** | `USE_SLS = 'Y'` and `PRSC_NPI IS NOT NULL` | `SALE_TYP = 'FTP'` |
| **Database** | `PHCDW` (Snowflake) | `CPH_DB_PROD` (Snowflake) |

---

## 2. Column-Level Drift Analysis

### 2.1 Old Columns Used by the Notebook → New Mapping

| Old Column | Used For | New Column | Notes |
| --- | --- | --- | --- |
| `PRSC_NPI` | Identify prescribing HCP | `HCP_NPI_NUM` | Still available but **not needed** — use `BAYER_HCP_ID` directly |
| `RX_DT` | Event date (cast to DateType) | `DATE_ID` | Text YYYYMMDD → parse with `to_date(DATE_ID, 'yyyyMMdd')` |
| `CLM_AUTH_NUM` | Individual claim ID | — | Not available; not needed (no claim-level tracking) |
| `ORGN_CLM_AUTH_NUM` | Group claims for reversal detection | — | Not available; reversal handling is **eliminated** |
| `DAY_SUPPLY` | Detect reversals (negative = cancellation) | `FTP_UNIT` | Pre-aggregated units; negative-value reversals already netted out |
| `USE_SLS` | Filter valid claims | `SALE_TYP` | Filter `SALE_TYP = 'FTP'` replaces `USE_SLS = 'Y'` |
| `CLAIM_COUNT_NBR` | (renamed `ROW_COUNT` in NBA 3.1 draft) | `FTP_TRX` | Pre-computed FTP transaction count |

### 2.2 New Columns Available (Not in Old Source)

| New Column | Type | Potential Use |
| --- | --- | --- |
| `BAYER_HCP_ID` | TEXT | **Direct BHID** — eliminates NPI-to-BHID mapping step entirely |
| `FTP_NRX` | NUMBER | New Rx count (new patients started on FTP) |
| `FTP_TRX` | NUMBER | Total Rx count (all FTP transactions) |
| `FTP_UNIT` | NUMBER | Units dispensed via FTP |
| `FTP_NPS` | NUMBER | Net product sales for FTP (usually NULL for FTP) |
| `PROD_ID` | TEXT | Product identifier (e.g. P50419-540-01, P50419-541-01 = Kerendia) |
| `SALE_CHNL_DESC` | TEXT | Channel description ("Bayer FTP", "FTP", "SP") |
| `BRIDGE_*` | NUMBER | Bridge program metrics (NRX, TRX, NPS, UNIT) — if Bridge features needed |
| `PRMRY_TERR_FLAG` | TEXT | Whether HCP is in primary territory |
| `HCP_TRGT_FLAG` | NUMBER | HCP targeting flag |
| Various HCP dims | TEXT | HCP specialty, address, segment info (available inline) |

### 2.3 Old Columns No Longer Available

| Old Column | Was Used? | Impact |
| --- | --- | --- |
| `CLM_AUTH_NUM` | Yes (claim ID) | **None** — claim-level identity not needed in aggregated table |
| `ORGN_CLM_AUTH_NUM` | Yes (reversal grouping) | **None** — reversals pre-handled at source |
| `DAY_SUPPLY` (raw) | Yes (reversal detection) | **Replaced** by `FTP_UNIT` (net units) |
| `GRP_NUM`, `MMBR_ID` | No | N/A |
| Patient demographics (`PAT_GNDR`, `PAT_AGE`) | No | N/A |
| Pharmacy details (`PHMCY_*`) | No | N/A |

---

## 3. Record-Level Drift Analysis

### 3.1 Volume Comparison

| Metric | Old | New | Change |
| --- | --- | --- | --- |
| FTP rows | 134,311 | 268,020 | +99.6% (roughly 2×) |
| Distinct HCPs | 16,066 NPIs | 18,263 BHIDs | +13.7% |
| Date range start | 2023-01-01 | 2019-08-12 | 3.4 years earlier |
| Date range end | 2025-12-31 | 2026-10-23 | 10 months later |

**Explanation of volume increase:**
* **Wider date range:** the new table goes back to Aug 2019 (vs Jan 2023), adding ~4 years of history.
* **Different granularity:** new table is per-HCP-per-date-per-product, potentially splitting a single old claim across products.
* **Possibly includes more channels:** old view only tracked one FTP channel; new table shows `SALE_CHNL_DESC` values "Bayer FTP" (224K), "FTP" (43K), and "SP" (12).

### 3.2 Identifier Change

* Old: identified HCPs by `PRSC_NPI`, then mapped to BHID via a separate `kerendia_nba_3_0_npi_bhid_mapping` table (inner join → dropped HCPs without a BHID match).
* New: `BAYER_HCP_ID` is directly available on each row. Some values may be `PDRP` or non-standard (observed `HCP_NPI_NUM = 'PDRP'` for some rows).
* **Impact:** the NPI-to-BHID mapping step is eliminated. More HCPs may be included since no inner-join filter is applied.

### 3.3 Reversal Handling Change

* Old: required a second Snowflake query to identify `ORGN_CLM_AUTH_NUM` groups with net `DAY_SUPPLY = 0` (fully cancelled claims), then anti-join to remove them. This was the most complex step.
* New: `FTP_TRX` and `FTP_UNIT` are pre-aggregated at the source. Negative-value reversals are already netted. **No reversal handling logic needed.**
* **Risk:** if the new table nets all transactions per HCP/date (including partial reversals), the count may differ slightly from the old "count of non-reversed claim lines" approach.

---

## 4. Revamp Strategy

### 4.1 What Changes

| Step | Old Logic | New Logic |
| --- | --- | --- |
| **Data load** | Snowflake query on `VIEW_RB_KERENDIA_VOUCHER_FTP` via `Get_Data_Snowflakes` | Snowflake query on `ANLT_BASE_FACT_SALES_ALIGNED` with `SALE_TYP = 'FTP'` |
| **Date parse** | `to_date(RX_DT, 'MM/dd/yyyy HH:mm:ss')` | `to_date(DATE_ID, 'yyyyMMdd')` |
| **Reversal removal** | Second query + anti-join on `ORGN_CLM_AUTH_NUM` | **Eliminated** — not needed |
| **NPI→BHID mapping** | Inner join with `npi_bhid_mapping` | **Eliminated** — use `BAYER_HCP_ID` directly as BHID |
| **Aggregation** | `count(lit(1))` → `TOTAL_RX_FTP` | `sum(FTP_TRX)` → `TOTAL_RX_FTP` |
| **Cohort cross-join** | Same pattern | Same pattern (unchanged) |
| **Fill dates + lag features** | Same pattern (step2/step3) | Same pattern (unchanged) |
| **Running total** | Same pattern | Same pattern (unchanged) |
| **Output** | 6 lag features + RUNNING_TOTAL + HCP_COHORT_ID + PULL_DT | Same columns (unchanged) |

### 4.2 What Stays the Same

* Cohort anchor dates loading and cross-join logic
* `step2_fill_missing_dates` (day-level spine expansion)
* `step3_lag_date` (rolling window sums: 30, 60, 90, 120, 150, 180 days)
* Running total computation
* Anchor-date filter (`MONTH_ID == LOOKBACK_END_DATE`)
* Output column structure: `HCP_COHORT_ID`, `PULL_DT`, 6 lag features, `RUNNING_TOTAL_RX_FTP`

### 4.3 Net Simplification

The revamped notebook will be **significantly simpler**:
* ~3 fewer cells (reversal handling and NPI mapping eliminated)
* No second Snowflake query needed
* No `toPandas()` / `isin` anti-pattern for reversal filtering
* Direct BHID means one fewer join

### 4.4 New Columns to SELECT

```sql
SELECT
    BAYER_HCP_ID AS BHID,
    DATE_ID,
    FTP_TRX,
    FTP_NRX,
    FTP_UNIT
FROM CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_SALES_ALIGNED
WHERE SALE_TYP = 'FTP'
  AND BAYER_HCP_ID IS NOT NULL
```

### 4.5 Open Questions

1. **Should we also include BRIDGE rows?** The old notebook only tracked FTP. The new table has `SALE_TYP = 'BRIDGE'` rows (1,265 total). If Bridge is a separate feature, it can be added as `TOTAL_RX_BRIDGE`.
2. **Should `FTP_NRX` (new Rx) be a separate feature?** Currently only `FTP_TRX` (all Rx) is used. FTP_NRX specifically counts new patient starts.
3. **Channel split:** `SALE_CHNL_DESC` has values "Bayer FTP" (224K), "FTP" (43K), and "SP" (12). Should all be included, or only "Bayer FTP"?
4. **HCP filter:** some `HCP_NPI_NUM` values are 'PDRP' (opted out). The old notebook filtered `PRSC_NPI IS NOT NULL`. Should we also filter out non-standard NPIs?

---

## 5. Validation Plan

After revamp, compare old vs new output:

| Check | Method |
| --- | --- |
| Row count alignment | Compare distinct HCP_COHORT_ID counts (old ~13K, new expected ~18K due to more HCPs) |
| Feature value comparison | For overlapping HCPs and overlapping date range (2023-2025), compare TOTAL_RX_FTP_IN_LAST_6_MONTH values |
| Date coverage | Verify new output covers the full lookback window |
| Schema match | Final output must have identical columns: HCP_COHORT_ID, PULL_DT, 6 lag features, RUNNING_TOTAL_RX_FTP |
