# NBA3.0 FTP and Copay Summary

Date: 2026-11-18. Review only: no notebook or table was changed.

Scope: what exists in NBA 3.0 today for FTP (Free Trial Program) and Copay (copay card), based on the **NBA 3.0 Ops - Pipeline** (inference) notebooks and their saved outputs. All numbers below come from queries run on 2026-11-18 on the latest saved outputs (PULL_DT 2026-10-27, inference cohort I01) and on the two Snowflake source views 3.0 reads, unless stated otherwise. The views, cut to records loaded up to 2026-10-20, reproduce the saved FTP output exactly (section 1d).

The document covers FTP first (section 1), then Copay (section 2); inputs used by both are in section 3.

**In one line:** 3.0 builds 6 FTP features and 15 copay features, but only **4 FTP features** are in the final 752-feature model, and they matter very little (ranks 500 to 661 of 752, 0.09% of total mean absolute SHAP); **no copay feature is used by the model**. FTP has a non-zero value for at most 2,074 of 234,405 HCPs (0.9%); every other HCP gets 0.

---

## 1. FTP (Free Trial Program)

### 1a. Where things are

| Item | Location |
| --- | --- |
| Feature notebook | `kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/19_ftp_features` |
| Source (Snowflake) | `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP` |
| Promotional cohort dates | volume `hcp_level_model/ops_pipeline/notebook_output/promotional_cohort_inference_dates` (Delta) |
| Output | volume `hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_ftp_features_v2_for_inference` |

Shared inputs (NPI mapping, HCP universe, combine notebook, 752 list, final model input, SHAP) are in section 3.

### 1b. What 3.0 reads

The notebook reads Snowflake through `Get_Data_Snowflakes` (connection in `00_connection`).

| | FTP |
| --- | --- |
| View | `VIEW_RB_KERENDIA_VOUCHER_FTP` |
| Filter | `PRSC_NPI IS NOT NULL AND USE_SLS = 'Y'` |
| Columns selected | `PRSC_NPI` (as `NPI_NUMBER`), `CLM_AUTH_NUM`, `ORGN_CLM_AUTH_NUM`, `RX_DT` |
| Extra query (reversal removal) | `ORGN_CLM_AUTH_NUM`, `DAY_SUPPLY` (filter `USE_SLS = 'Y'` only) |
| Grain | One row per source record (payment, reversal, correction) |

### 1c. All columns in the FTP view and their fill rate

Source: `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP`, queried on 2026-11-18 with the 3.0 connection (`00_connection`). The view is live, so the rows are cut to what the last 3.0 run saw: records loaded up to 2026-10-20 (`INSRT_DT < 2026-10-21`). This cut-off reproduces the saved FTP output exactly (section 1d); later loads (2026-10-26 onward) were not in the run.

Fill rate = not null and not blank, over all view rows (before the 3.0 filter). One row = one source record (payment, reversal or correction).

| | FTP view |
| --- | --- |
| Columns | 73 |
| Rows (loaded up to 2026-10-20) | 135,453 |
| Rows after the 3.0 filter (`PRSC_NPI IS NOT NULL AND USE_SLS = 'Y'`) | 134,054 |
| `RX_DT` range | 2021-01-13 to 2026-10-16 |
| Latest load (`INSRT_DT`) | 2026-10-20 |

Almost all columns are stored as text (`RX_DT` is text `MM/DD/YYYY HH24:MI:SS`; 3.0 converts it with `TO_DATE`).

| Column | Type | Fill % | Used by 3.0? |
| --- | --- | --- | --- |
| `TRNS_ID` | TEXT | 100.00 | No |
| `INSRT_DT` | TEXT | 100.00 | No |
| `EXCLD_CD` | TEXT | 100.00 | No |
| `USE_SLS` | TEXT | 100.00 | **Filter** (`= 'Y'`) |
| `SHLD_ID` | TEXT | 100.00 | No |
| `HCP_ID` | TEXT | 99.89 | No |
| `ACCT_ID` | TEXT | 99.89 | No |
| `CLM_AUTH_NUM` | TEXT | 100.00 | Loaded, not used in features |
| `ORGN_CLM_AUTH_NUM` | TEXT | 100.00 | **Yes** (reversal removal key) |
| `RX_NUM` | TEXT | 100.00 | No |
| `RX_FILL_DT` | TEXT | 100.00 | No (pickup date not used) |
| `RX_DT` | TEXT | 100.00 | **Yes** (feature date) |
| `DAY_SUPPLY` | TEXT | 100.00 | **Yes** (reversal detection only) |
| `DAW` | TEXT | 100.00 | No |
| `NDC_NUM` | TEXT | 100.00 | No |
| `DRG_DESC` | TEXT | 100.00 | No |
| `NEW_REFILL_CD` | TEXT | 100.00 | No |
| `RX_REFILLS` | TEXT | 100.00 | No |
| `OTHR_CVRG_CD` | TEXT | 100.00 | No |
| `GRP_NUM` | TEXT | 100.00 | No |
| `MMBR_ID` | TEXT | 100.00 | No |
| `PAT_GNDR` | TEXT | 100.00 | No |
| `PAT_AGE` | TEXT | 85.14 | No |
| `PHMCY_NABP` | TEXT | 100.00 | No |
| `PHMCY_NM` | TEXT | 100.00 | No |
| `PHMCY_ADDR_1` | TEXT | 100.00 | No |
| `PHMCY_ADDR_2` | TEXT | 9.97 | No |
| `PHMCY_CTY` | TEXT | 100.00 | No |
| `PHMCY_STATE` | TEXT | 100.00 | No |
| `PHMCY_ZIP` | TEXT | 100.00 | No |
| `PRSC_NPI` | TEXT | 99.96 | **Yes** (HCP key; nulls filtered out) |
| `PRSC_NM` | TEXT | 99.98 | No |
| `PRSC_FIRST_NM` | TEXT | 99.94 | No |
| `PRSC_MID_INT_NM` | TEXT | 66.12 | No |
| `PRSC_LAST_NM` | TEXT | 99.98 | No |
| `PRSC_SFFX` | TEXT | 0.19 | No |
| `PRSC_PRFSN_DSG` | TEXT | 72.20 | No |
| `PRSC_SPCLTY_1` | TEXT | 96.35 | No |
| `PRSC_SPCLTY_2` | TEXT | 12.57 | No |
| `PRSC_ADDR_1` | TEXT | 99.94 | No |
| `PRSC_ADDR_2` | TEXT | 44.26 | No |
| `PRSC_CTY` | TEXT | 99.94 | No |
| `PRSC_STATE` | TEXT | 99.94 | No |
| `PRSC_ZIP` | TEXT | 99.94 | No |
| `SBMSSN_MTHD` | TEXT | 100.00 | No |
| `QTY` | TEXT | 100.00 | No |
| `PTNT_BNFT` | TEXT | 100.00 | No |
| `PTNT_COPAY` | TEXT | 100.00 | No |
| `PATOOP` | TEXT | 100.00 | No |
| `PHMCY_TRANS_FEE` | FLOAT | 100.00 | No |
| `OTHR_PYR_BIN_NM_PRMY` | TEXT | 3.72 | No |
| `CO_B_PRMY_OTHR_PYR_ID_BIN` | TEXT | 2.08 | No |
| `DATA_DT` | TEXT | 100.00 | No |
| `BU_NM` | TEXT | 100.00 | No |
| `SRC_SYS_CD` | TEXT | 100.00 | No |
| `PROD_CD` | TEXT | 100.00 | No |
| `BTCHADT_ID_SK` | NUMBER | 100.00 | No |
| `JOBADT_ID_SK` | NUMBER | 100.00 | No |
| `CRTD_DT` | TEXT | 100.00 | No |
| `MDFD_DT` | TEXT | 100.00 | No |
| `CLAIM_COUNT_NBR` | NUMBER | 100.00 | No |
| `BH_ID` | TEXT | 99.95 | No |
| `MDM_FIRST_NAME` | TEXT | 99.95 | No |
| `MDM_LAST_NAME` | TEXT | 99.95 | No |
| `SPECIALTY` | TEXT | 99.95 | No |
| `KER_ADDRESS_1` | TEXT | 94.19 | No |
| `KER_ADDRESS_2` | TEXT | 3.20 | No |
| `KER_CITY` | TEXT | 94.19 | No |
| `KER_STATE` | TEXT | 94.19 | No |
| `KER_ZIP_CODE` | TEXT | 99.91 | No |
| `KER_SPECIALTY` | TEXT | 99.91 | No |
| `RX_FILL_DATE` | DATE | 100.00 | No |
| `INSERT_DATE` | DATE | 100.00 | No |

**In short:** out of 73 columns, the FTP features depend on only 4: `PRSC_NPI`, `ORGN_CLM_AUTH_NUM`, `RX_DT` and `DAY_SUPPLY` (plus the `USE_SLS` filter). All 4 are 99.96%–100% filled. The view also carries a ready Bayer ID (`BH_ID`, 99.95% filled), which 3.0 does not use (it maps NPI to Bayer ID through the volume mapping instead, section 3b).

### 1d. What the 3.0 steps do to the FTP view rows (records loaded up to 2026-10-20)

| Step | FTP view |
| --- | --- |
| All rows | 135,453 |
| `USE_SLS = 'Y'` | 134,109 |
| Distinct claims (`ORGN_CLM_AUTH_NUM`) with `USE_SLS = 'Y'` | 119,112 |
| Reversed claims dropped (`SUM(DAY_SUPPLY) = 0`) | 13,704 claims, 27,408 rows |
| Rows kept (also `PRSC_NPI` not null) | 106,654 |
| Claims kept | 105,361 |
| Negative `DAY_SUPPLY` rows left after the step | 0 |
| Kept claims with a second, duplicate row (same `CLM_AUTH_NUM`) | 1,292 claims, 1,293 extra rows |

The reversal step removes every reversal: no negative `DAY_SUPPLY` row is left. What it does not remove is a second copy of the same claim (same `ORGN_CLM_AUTH_NUM` and `CLM_AUTH_NUM`), which 3.0 counts twice: 1.2% of kept FTP rows.

**Reproduction check.** Rebuilding the FTP features from the view (rows above → inner join to the NPI mapping → `RX_DT` in 2025-10-17 to 2026-10-17 → count per HCP over the last 30–180 days) gives the saved FTP output exactly: the same 3,893 HCPs, and the same HCP counts and record sums for all 6 windows (for example 423 HCPs / 579 records in 30 days, 2,154 / 4,219 in 180 days). Per-HCP 6-month values match one for one.

### 1e. How the features are built: business rules (`19_ftp_features`)

Rules as implemented in the 3.0 Ops notebook `19_ftp_features`, in the order they run.

**Source and record selection**

* Source is the Snowflake view `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP`, read through `Get_Data_Snowflakes`.
* Keep only records counted for sales: `USE_SLS = 'Y'`.
* Keep only records with a prescriber NPI: `PRSC_NPI IS NOT NULL` (renamed `NPI_NUMBER`).
* The event date is `RX_DT`, the date the prescription was **written**, converted with `TO_DATE`. The pickup date (`RX_FILL_DT`) is not used.
* Dates stay at **day** level; the monthly truncation in the notebook is commented out (the column is still called `MONTH_ID`).
* All records are taken from the view's full history; there is no date cut at load time, only the lookback filter below.

**Reversal removal**

* Notebook definition: a reversal is a record with negative values (`DAY_SUPPLY`, `QTY`, `PTNT_BNFT`, `PTNT_COPAY`, `PTNT_OOP`); its matching approval has the same original claim number (`ORGN_CLM_AUTH_NUM`) with positive values. `CLM_AUTH_NUM` can change between the two, `ORGN_CLM_AUTH_NUM` does not.
* As implemented, only `DAY_SUPPLY` is used: sum `DAY_SUPPLY` per `ORGN_CLM_AUTH_NUM` over all `USE_SLS = 'Y'` records.
* If the sum is exactly 0 (approval fully cancelled by its reversal), **every** record of that claim is removed.
* Claims whose sum is not 0 are kept with all their records; each record counts once. A row count (+1 / −1) is calculated in the query but not used in the rule.

**HCP mapping**

* Join `NPI_NUMBER` to the volume mapping `kerendia_nba_3_0_npi_bhid_mapping` to get the Bayer ID (`BH_ID` → `BHID`).
* Inner join: records whose NPI is not in the mapping are dropped. Records with a null `BHID` are also dropped.

**Cohort and lookback window**

* Cross join every record with the promotional cohort dates (`promotional_cohort_inference_dates`); at inference there is one cohort, `I01`.
* Keep records with `LOOKBACK_START_DATE <= RX_DT <= LOOKBACK_END_DATE` (both ends included). For I01: **2025-10-17 to 2026-10-17** (anchor 2026-11-01, prediction window 2026-11-07 to 2026-12-07).
* HCP key: `HCP_COHORT_ID` = `BHID` + `_` + cohort (for example `BH11046733_I01`).

**Counting**

* Daily count: `TOTAL_RX_FTP` = number of FTP records per `HCP_COHORT_ID` per day.
* The unit is a record, not a distinct claim, patient or prescription: a claim with two kept records counts 2 (section 1d).

**Rolling windows**

* Build a daily spine for each HCP: every day from the lookback start to the lookback end; days with no record get 0.
* For each day, sum the last N rows (days), current day included, for N = 30, 60, 90, 120, 150, 180.
* Name = `TOTAL_RX_FTP_IN_LAST_{N/30}_MONTH`, so 1 month = 30 days, 6 months = 180 days.

**Output**

* Keep only the row where the day equals `LOOKBACK_END_DATE` (2026-10-17): one row per HCP.
* Only HCPs with **at least one FTP record in the 12-month lookback** get a row; their windows can still be 0 if all records are older than 6 months.
* Missing values are filled with 0; the daily count column is dropped; `PULL_DT` = run date.
* Written (overwrite) as Delta to `kerendia_nba_3_hcp_model_ftp_features_v2_for_inference`.
* HCPs without a row get 0 later, in the combine step (section 1f).

| Feature | Definition | In final 752? | Mean abs SHAP | SHAP rank (of 752) | % of total SHAP |
| --- | --- | --- | --- | --- | --- |
| `TOTAL_RX_FTP_IN_LAST_1_MONTH` | FTP records written in the last 30 days | **Yes** | 0.00301 | 500 | 0.042 |
| `TOTAL_RX_FTP_IN_LAST_2_MONTH` | last 60 days | No | — | — | — |
| `TOTAL_RX_FTP_IN_LAST_3_MONTH` | last 90 days | **Yes** | 0.00118 | 661 | 0.016 |
| `TOTAL_RX_FTP_IN_LAST_4_MONTH` | last 120 days | **Yes** | 0.00137 | 645 | 0.019 |
| `TOTAL_RX_FTP_IN_LAST_5_MONTH` | last 150 days | No | — | — | — |
| `TOTAL_RX_FTP_IN_LAST_6_MONTH` | last 180 days | **Yes** | 0.00123 | 659 | 0.017 |

SHAP is from the 3.0 production model (`Shap_Importances.csv`, section 3a). Rank 1 = highest mean absolute SHAP. Together the 4 FTP features hold **0.09%** of the total mean absolute SHAP (7.20). For scale: the top feature (`TOTAL_F2F_IN_LAST_6_MONTH`) has 0.240 and the median feature 0.0048, so all 4 FTP features are below the median.

### 1f. How FTP reaches the model (`99_Combine_Physician_Data`)

| Step | FTP |
| --- | --- |
| HCP universe | 234,405 providers, cohort I01 |
| Join key | `HCP_COHORT_ID` (`BHID_I01`), left join |
| Date used | FTP lookback end 2026-10-17 |
| HCPs without a match | Filled with **0** (`fillna(0)` after selection) |
| Final 752 selection | 4 features kept (SHAP ranks 500, 645, 659, 661) |

The 752 list has 753 rows; a search for "FTP" in it returns only the 4 FTP features above. The same search in `Shap_Importances.csv` (752 features, all of them in the 752 list) also returns only these 4.

### 1g. The FTP output table (`..._ftp_features_v2_for_inference`)

| | Value |
| --- | --- |
| Rows | 3,893 (one per HCP, cohort I01) |
| Date (`MONTH_ID`) | 2026-10-17 for every row |
| PULL_DT | 2026-10-27 |
| Columns | `HCP_COHORT_ID`, `MONTH_ID`, 6 features, `PULL_DT` |
| Fill rate | 100% in every column (zeros, never null) |

| Feature | Rows with value > 0 | Rows = 0 |
| --- | --- | --- |
| `TOTAL_RX_FTP_IN_LAST_1_MONTH` | 423 | 3,470 |
| `TOTAL_RX_FTP_IN_LAST_2_MONTH` | 844 | 3,049 |
| `TOTAL_RX_FTP_IN_LAST_3_MONTH` | 1,220 | 2,673 |
| `TOTAL_RX_FTP_IN_LAST_4_MONTH` | 1,512 | 2,381 |
| `TOTAL_RX_FTP_IN_LAST_5_MONTH` | 1,821 | 2,072 |
| `TOTAL_RX_FTP_IN_LAST_6_MONTH` | 2,154 | 1,739 |

1,739 HCPs are in the table with 0 in all six features: their FTP records were 7–12 months back, inside the 12-month lookback but outside the 6-month windows.

### 1h. FTP against the HCP universe (234,405 providers)

| Step | HCPs |
| --- | --- |
| Universe | 234,405 |
| With a Bayer ID in the mapping | 234,327 (78 without) |
| With a row in the FTP output (before fill) | 3,790 (1.6%) |
| With no FTP row → null, then filled with 0 | 230,537 among those with a Bayer ID |
| FTP output rows not in the universe | 106 (lost in the join) |

| Feature | HCPs with value > 0 | HCPs = 0 or empty (filled 0) | Total FTP records (sum) |
| --- | --- | --- | --- |
| `TOTAL_RX_FTP_IN_LAST_1_MONTH` | 402 | 234,003 | 557 |
| `TOTAL_RX_FTP_IN_LAST_2_MONTH` | 807 | 233,598 | 1,238 |
| `TOTAL_RX_FTP_IN_LAST_3_MONTH` | 1,169 | 233,236 | 1,948 |
| `TOTAL_RX_FTP_IN_LAST_4_MONTH` | 1,450 | 232,955 | 2,565 |
| `TOTAL_RX_FTP_IN_LAST_5_MONTH` | 1,750 | 232,655 | 3,294 |
| `TOTAL_RX_FTP_IN_LAST_6_MONTH` | 2,074 | 232,331 | 4,131 |

### 1i. FTP in the final model input (`kerendia_nba_3_hcp_selected_features_data`)

| | Value |
| --- | --- |
| Rows / columns | 245,174 rows, 755 columns, cohort I01 |
| Distinct `HCP_COHORT_ID` | 234,405 (2,743 IDs appear more than once) |
| FTP features present | `_1_MONTH`, `_3_MONTH`, `_4_MONTH`, `_6_MONTH` |
| Nulls in FTP features | 0 (all filled with 0) |
| Distinct HCPs with value > 0 | 402 / 1,169 / 1,450 / 2,074 (same as 1h) |
| Max value | 9 / 34 / 35 / 70 |

Cross-check: the HCP counts with a value in the final input are exactly the counts from joining the FTP output to the universe (1h).

### 1j. FTP: known issues in the 3.0 logic

| # | Issue | Effect |
| --- | --- | --- |
| 1 | Features use the **written** date (`RX_DT`), not the pickup date (`RX_FILL_DT`) | Training sees pickups that had not happened yet at the cohort date (look-ahead); FTP records reach the view a median 20 days after the written date (90th percentile 89 days), so the last weeks are undercounted at inference |
| 2 | Reversal removal works (no negative rows left), but **duplicate rows** of the same claim (same `ORGN_CLM_AUTH_NUM` and `CLM_AUTH_NUM`) are kept and counted twice | 1,293 extra rows (1.2%) (section 1d) |
| 3 | Counts are records, not distinct claims or patients | A duplicated claim counts twice |
| 4 | FTP rows exist only for HCPs with an FTP record in the 12-month lookback; everyone else is filled with 0 | 0 means both "no FTP" and "not in the FTP data" |
| 5 | The 4 FTP features rank 500 to 661 of 752 by SHAP (0.09% of total) | FTP has almost no effect on the 3.0 model |

---

## 2. Copay (copay card)

### 2a. Where things are

| Item | Location |
| --- | --- |
| Feature notebook | `kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/22_copay_features` |
| Helper (rolling windows) | `NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_step23_function` (`step2_fill_missing`, `step3_lag`) |
| Source (Snowflake) | `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_COPAY_PROGRAM` |
| HCP model cohort dates | volume `hcp_level_model/ops_pipeline/query_output/hcp_model_inference_anchor_dates.csv` |
| Output | volume `hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_copay_features_for_inference` |

### 2b. What 3.0 reads

| | Copay |
| --- | --- |
| View | `VIEW_RB_KERENDIA_COPAY_PROGRAM` |
| Filter | `PRSC_NPI IS NOT NULL AND USE_SLS = 'Y'` |
| Columns selected | `PRSC_NPI` (as `NPI_NUMBER`), `CLM_AUTH_NUM`, `ORGN_CLM_AUTH_NUM`, `RX_DT`, `GRP_NUM`, `PTNT_COPAY`, `PATOOP` |
| Extra query (reversal removal) | `ORGN_CLM_AUTH_NUM`, `DAY_SUPPLY` |
| Grain | One row per source record (payment, reversal, correction) |

### 2c. All columns in the copay view and their fill rate

Source: `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_COPAY_PROGRAM`, same query date, connection and cut-off as the FTP view (records loaded up to 2026-10-20).

| | Copay view |
| --- | --- |
| Columns | 72 (same as the FTP view, without `INSERT_DATE`) |
| Rows (loaded up to 2026-10-20) | 118,087 |
| Rows after the 3.0 filter (`PRSC_NPI IS NOT NULL AND USE_SLS = 'Y'`) | 117,651 |
| `RX_DT` range | 2021-07-29 to 2026-10-16 |
| Latest load (`INSRT_DT`) | 2026-10-20 |

| Column | Type | Fill % | Used by 3.0? |
| --- | --- | --- | --- |
| `TRNS_ID` | TEXT | 100.00 | No |
| `INSRT_DT` | TEXT | 100.00 | No |
| `EXCLD_CD` | TEXT | 100.00 | No |
| `USE_SLS` | TEXT | 100.00 | **Filter** (`= 'Y'`) |
| `SHLD_ID` | TEXT | 100.00 | No |
| `HCP_ID` | TEXT | 99.89 | No |
| `ACCT_ID` | TEXT | 99.89 | No |
| `CLM_AUTH_NUM` | TEXT | 100.00 | Loaded, not used in features |
| `ORGN_CLM_AUTH_NUM` | TEXT | 100.00 | **Yes** (reversal removal key) |
| `RX_NUM` | TEXT | 100.00 | No |
| `RX_FILL_DT` | TEXT | 100.00 | No (pickup date not used) |
| `RX_DT` | TEXT | 99.98 | **Yes** (feature date) |
| `DAY_SUPPLY` | TEXT | 100.00 | **Yes** (reversal detection only) |
| `DAW` | TEXT | 100.00 | No |
| `NDC_NUM` | TEXT | 100.00 | No |
| `DRG_DESC` | TEXT | 100.00 | No |
| `NEW_REFILL_CD` | TEXT | 100.00 | No |
| `RX_REFILLS` | TEXT | 100.00 | No |
| `OTHR_CVRG_CD` | TEXT | 100.00 | No |
| `GRP_NUM` | TEXT | 100.00 | Loaded, not used |
| `MMBR_ID` | TEXT | 100.00 | No |
| `PAT_GNDR` | TEXT | 100.00 | No |
| `PAT_AGE` | TEXT | 98.49 | No |
| `PHMCY_NABP` | TEXT | 100.00 | No |
| `PHMCY_NM` | TEXT | 100.00 | No |
| `PHMCY_ADDR_1` | TEXT | 100.00 | No |
| `PHMCY_ADDR_2` | TEXT | 4.02 | No |
| `PHMCY_CTY` | TEXT | 100.00 | No |
| `PHMCY_STATE` | TEXT | 100.00 | No |
| `PHMCY_ZIP` | TEXT | 100.00 | No |
| `PRSC_NPI` | TEXT | 99.96 | **Yes** (HCP key; nulls filtered out) |
| `PRSC_NM` | TEXT | 99.91 | No |
| `PRSC_FIRST_NM` | TEXT | 99.88 | No |
| `PRSC_MID_INT_NM` | TEXT | 24.88 | No |
| `PRSC_LAST_NM` | TEXT | 99.91 | No |
| `PRSC_SFFX` | TEXT | 0.06 | No |
| `PRSC_PRFSN_DSG` | TEXT | 26.63 | No |
| `PRSC_SPCLTY_1` | TEXT | 90.83 | No |
| `PRSC_SPCLTY_2` | TEXT | 5.01 | No |
| `PRSC_ADDR_1` | TEXT | 99.88 | No |
| `PRSC_ADDR_2` | TEXT | 17.45 | No |
| `PRSC_CTY` | TEXT | 99.88 | No |
| `PRSC_STATE` | TEXT | 99.88 | No |
| `PRSC_ZIP` | TEXT | 99.88 | No |
| `SBMSSN_MTHD` | TEXT | 100.00 | No |
| `QTY` | TEXT | 100.00 | No |
| `PTNT_BNFT` | TEXT | 100.00 | No |
| `PTNT_COPAY` | TEXT | 100.00 | Loaded, not used |
| `PATOOP` | TEXT | 100.00 | Loaded, not used |
| `PHMCY_TRANS_FEE` | FLOAT | 100.00 | No |
| `OTHR_PYR_BIN_NM_PRMY` | TEXT | 28.00 | No |
| `CO_B_PRMY_OTHR_PYR_ID_BIN` | TEXT | 97.47 | No |
| `DATA_DT` | TEXT | 100.00 | No |
| `BU_NM` | TEXT | 100.00 | No |
| `SRC_SYS_CD` | TEXT | 100.00 | No |
| `PROD_CD` | TEXT | 100.00 | No |
| `BTCHADT_ID_SK` | NUMBER | 100.00 | No |
| `JOBADT_ID_SK` | NUMBER | 100.00 | No |
| `CRTD_DT` | TEXT | 100.00 | No |
| `MDFD_DT` | TEXT | 100.00 | No |
| `CLAIM_COUNT_NBR` | NUMBER | 100.00 | No |
| `BH_ID` | TEXT | 99.96 | No |
| `MDM_FIRST_NAME` | TEXT | 99.96 | No |
| `MDM_LAST_NAME` | TEXT | 99.96 | No |
| `SPECIALTY` | TEXT | 99.96 | No |
| `KER_ADDRESS_1` | TEXT | 95.50 | No |
| `KER_ADDRESS_2` | TEXT | 3.07 | No |
| `KER_CITY` | TEXT | 95.50 | No |
| `KER_STATE` | TEXT | 95.50 | No |
| `KER_ZIP_CODE` | TEXT | 99.88 | No |
| `KER_SPECIALTY` | TEXT | 99.88 | No |
| `RX_FILL_DATE` | DATE | 100.00 | No |

**In short:** out of 72 columns, the copay features depend on the same 4 as FTP: `PRSC_NPI`, `ORGN_CLM_AUTH_NUM`, `RX_DT` and `DAY_SUPPLY` (plus the `USE_SLS` filter), all 99.96%–100% filled. `GRP_NUM`, `PTNT_COPAY` and `PATOOP` are loaded but not used. `BH_ID` is 99.96% filled and not used.

### 2d. What the 3.0 steps do to the copay view rows (records loaded up to 2026-10-20)

| Step | Copay view |
| --- | --- |
| All rows | 118,087 |
| `USE_SLS = 'Y'` | 117,700 |
| Distinct claims (`ORGN_CLM_AUTH_NUM`) with `USE_SLS = 'Y'` | 107,381 |
| Reversed claims dropped (`SUM(DAY_SUPPLY) = 0`) | 3,355 claims, 6,710 rows |
| Rows kept (also `PRSC_NPI` not null) | 110,947 |
| Claims kept | 103,983 |
| Negative `DAY_SUPPLY` rows left after the step | 0 |
| Kept claims with a second, duplicate row (same `CLM_AUTH_NUM`) | 6,964 claims, 6,964 extra rows |

As for FTP, every reversal is removed, but duplicate rows of the same claim stay and are counted twice: 6.3% of kept copay rows.

**Reproduction check.** Rebuilding the copay counts from the view (rows above → inner join to the NPI mapping → count per provider × written month from 2022-01) gives the same number of HCPs as the saved output in every month; record counts differ by 271 records in total over 2022-01 to 2026-10 (for example 2026-09: 873 vs 874 saved; 2026-08: 1,186 vs 1,190).

### 2e. How the features are built: business rules (`22_copay_features`)

Rules as implemented in the 3.0 Ops notebook `22_copay_features` (with the helper functions `step2_fill_missing` and `step3_lag` from `00_step23_function`), in the order they run.

**Source and record selection**

* Source is the Snowflake view `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_COPAY_PROGRAM`, read through `Get_Data_Snowflakes`.
* Keep only records counted for sales: `USE_SLS = 'Y'`.
* Keep only records with a prescriber NPI: `PRSC_NPI IS NOT NULL` (renamed `NPI_NUMBER`).
* Columns loaded: `NPI_NUMBER`, `CLM_AUTH_NUM`, `ORGN_CLM_AUTH_NUM`, `RX_DT`, `GRP_NUM`, `PTNT_COPAY`, `PATOOP`. `GRP_NUM`, `PTNT_COPAY` and `PATOOP` are never used after loading.
* The event date is `RX_DT`, the date the prescription was **written**. The pickup date (`RX_FILL_DT`) is not used.
* `RX_DT` is truncated to the **first day of its month** → `SVC_DT_M`. All features are monthly.
* All records are taken from the view's full history (first month 2021-07); there is no cohort or lookback window.

**Reversal removal (same rule as FTP)**

* Notebook definition: a reversal is a record with negative values (`DAY_SUPPLY`, `QTY`, `PTNT_BNFT`, `PTNT_COPAY`, `PTNT_OOP`); its matching approval has the same `ORGN_CLM_AUTH_NUM` with positive values; `CLM_AUTH_NUM` can change.
* As implemented, only `DAY_SUPPLY` is used: sum `DAY_SUPPLY` per `ORGN_CLM_AUTH_NUM` over all `USE_SLS = 'Y'` records.
* If the sum is exactly 0, **every** record of that claim is removed. All other records are kept and count once each. The +1 / −1 row count in the query is not used.

**Counting**

* Monthly count: `TOTAL_RX_COPAY` = number of copay records per `NPI_NUMBER` per `SVC_DT_M`.
* The unit is a record, not a distinct claim, patient or card: duplicate rows and refills each count (sections 2d and 2i).
* Counting is done at **NPI** level, before the mapping to Bayer ID / provider ID.

**Month spine (`step2_fill_missing`)**

* Take the earliest and latest month across the **whole** data set (not per NPI), and build every month in between.
* Cross join every NPI with every month, so each NPI gets all months, including months before its first copay record.
* Months with no record get `TOTAL_RX_COPAY = 0`.

**Rolling windows and running total (`step3_lag`)**

* For each NPI, ordered by month: `TOTAL_RX_COPAY_IN_LAST_{i}_MONTH` = sum of the last *i* rows (months), current month included, for i = 1–6.
* `_IN_LAST_1_MONTH` is therefore always equal to `TOTAL_RX_COPAY`.
* `RUNNING_TOTAL_RX_COPAY` = sum of all months from the first month of the data (2021-07) up to and including the current month.
* Missing values after this step are filled with 0.

**Percentage features**

* `PCT_<feature>` = feature ÷ `TOTAL_RX_COPAY` (the current month count), for the 6 window features and the running total: 7 features.
* If the current month count is 0, the percentage is left **empty** (null), not 0.
* These are ratios, not shares: values are 1 or more (the 1-month ratio is always exactly 1).
* The notebook also tries a second set of ratios per window (other `_i_MONTH` features ÷ the window total); with only one base feature there are none, so no extra columns are created.

**Output**

* Keep months from **2022-01-01** onward. This filter runs after the windows and running total, so 2021 months still count in the 2022 windows and in the running total.
* Join to the volume mapping `kerendia_nba_3_0_npi_bhid_mapping` on `NPI_NUMBER` (inner) → `BHID` and `PROVIDER_ID`; NPIs not in the mapping are dropped; `NPI_NUMBER` is dropped.
* One row per provider × month (all months to the latest month in the data, 2026-10 in the last run), with `PULL_DT` = run date as text `YYYY_MM_DD`.
* Written (overwrite) as Delta to `kerendia_nba_3_hcp_model_copay_features_for_inference`.
* The combine step uses only the month `SVC_DT_M = 2026-09-01` (section 2f).

| Feature | Definition | In final 752? |
| --- | --- | --- |
| `TOTAL_RX_COPAY` | copay records written in the month | No |
| `TOTAL_RX_COPAY_IN_LAST_1_MONTH` | same as the month count | No |
| `TOTAL_RX_COPAY_IN_LAST_2_MONTH` … `_6_MONTH` | rolling 2–6 month sums | No |
| `RUNNING_TOTAL_RX_COPAY` | all records since the first month | No |
| `PCT_TOTAL_RX_COPAY_IN_LAST_1_MONTH` … `_6_MONTH` | window ÷ current month | No |
| `PCT_RUNNING_TOTAL_RX_COPAY` | running total ÷ current month | No |

### 2f. How copay reaches the model (`99_Combine_Physician_Data`)

| Step | Copay |
| --- | --- |
| HCP universe | 234,405 providers, cohort I01 |
| Join key | `PROVIDER_ID` + `SVC_DT_M`, left join |
| Month used | `SVC_DT_M` = 2026-09-01 (month of the HCP model lookback end, 2026-09-30) |
| HCPs without a match | Dropped anyway: no copay feature in the 752 list |
| Final 752 selection | 0 features kept |

A search for "COPAY" in the 752 list and in `Shap_Importances.csv` returns nothing.

### 2g. The copay output table (`..._copay_features_for_inference`)

| | Value |
| --- | --- |
| Rows | 540,154 = 9,313 providers × 58 months |
| Months | 2022-01 to 2026-10 |
| Distinct `PROVIDER_ID` / `BHID` | 9,313 / 9,313 |
| PULL_DT | 2026_10_27 |

| Column | Fill % | Rows with value > 0 |
| --- | --- | --- |
| `SVC_DT_M`, `BHID`, `PROVIDER_ID`, `PULL_DT` | 100.0 | — |
| `TOTAL_RX_COPAY` | 100.0 | 29,698 |
| `TOTAL_RX_COPAY_IN_LAST_1_MONTH` | 100.0 | 29,698 |
| `TOTAL_RX_COPAY_IN_LAST_2_MONTH` | 100.0 | 53,538 |
| `TOTAL_RX_COPAY_IN_LAST_3_MONTH` | 100.0 | 73,809 |
| `TOTAL_RX_COPAY_IN_LAST_4_MONTH` | 100.0 | 90,824 |
| `TOTAL_RX_COPAY_IN_LAST_5_MONTH` | 100.0 | 105,481 |
| `TOTAL_RX_COPAY_IN_LAST_6_MONTH` | 100.0 | 118,498 |
| `RUNNING_TOTAL_RX_COPAY` | 100.0 | 274,726 |
| `PCT_TOTAL_RX_COPAY_IN_LAST_1_MONTH` … `_6_MONTH` | 5.5 each (29,698 rows) | 29,698 each |
| `PCT_RUNNING_TOTAL_RX_COPAY` | 5.5 (29,698 rows) | 29,698 |

The percentage features are filled only in the 29,698 rows (5.5%) where the HCP had a copay record in the current month; 94.5% of rows are empty.

### 2h. Copay against the HCP universe at the month the model uses (2026-09)

| | HCPs |
| --- | --- |
| Universe | 234,405 |
| With a copay row for 2026-09 | 9,238 (3.9%) |
| No copay row → empty | 225,167 |
| Copay providers not in the universe | 75 |

| Feature (2026-09) | HCPs with value > 0 |
| --- | --- |
| `TOTAL_RX_COPAY` / `_IN_LAST_1_MONTH` | 571 |
| `TOTAL_RX_COPAY_IN_LAST_2_MONTH` | 1,101 |
| `TOTAL_RX_COPAY_IN_LAST_3_MONTH` | 1,607 |
| `TOTAL_RX_COPAY_IN_LAST_4_MONTH` | 2,070 |
| `TOTAL_RX_COPAY_IN_LAST_5_MONTH` | 2,437 |
| `TOTAL_RX_COPAY_IN_LAST_6_MONTH` | 2,861 |
| `RUNNING_TOTAL_RX_COPAY` | 9,178 |
| All 7 `PCT_` features | 571 |

These values are joined in the combine step but none reach the model (section 2f).

### 2i. Copay records per month (whole output)

| Month | HCPs with ≥1 record | Records |
| --- | --- | --- |
| 2022-01 | 144 | 477 |
| 2022-06 | 288 | 1,129 |
| 2022-12 | 382 | 1,084 |
| 2023-06 | 488 | 1,459 |
| 2023-12 | 482 | 1,431 |
| 2024-06 | 492 | 2,412 |
| 2024-12 | 591 | 2,422 |
| 2025-01 | 681 | 3,092 |
| 2025-06 | 658 | 2,973 |
| 2025-12 | 731 | 2,973 |
| 2026-03 | 781 | 2,788 |
| 2026-04 | 773 | 2,712 |
| 2026-05 | 665 | 2,007 |
| 2026-06 | 719 | 2,020 |
| 2026-07 | 677 | 1,622 |
| 2026-08 | 613 | 1,190 |
| 2026-09 | 578 | 874 |
| 2026-10 | 245 | 270 (partial month) |

Records fall from about 2,700–2,900 a month in early 2026 to 874 in September 2026. The copay view explains why: months come from the written date (`RX_DT`), and only 30% of copay records are new prescriptions (`NEW_REFILL_CD = '00'`); the rest are refills that keep the original written date. Copay records are picked up a median 76 days after the written date (90th percentile 246 days) and loaded about 5 days after pickup, so a record reaches the view a median 82 days after its written month (90th percentile 253 days). Recent months therefore keep filling after the run: in the view, 2026-09 grew from 877 records at the run to 962 by the 2026-10-27 load, and 2026-08 from 1,186 to 1,280. For FTP the gap is smaller (64% new prescriptions; median 20 days from written date to load, 90th percentile 89 days).

### 2j. Copay: known issues in the 3.0 logic

| # | Issue | Effect |
| --- | --- | --- |
| 1 | Features use the **written** date (`RX_DT`), not the pickup date (`RX_FILL_DT`) | Training sees pickups that had not happened yet at the cohort date (look-ahead); recent months are undercounted at inference (section 2i) |
| 2 | Reversal removal works (no negative rows left), but **duplicate rows** of the same claim are kept and counted twice | 6,964 extra rows (6.3%) (section 2d) |
| 3 | Counts are records, not distinct claims or patients, and include refills (70% of copay records) | A duplicated claim counts twice; one patient on refills counts every month |
| 4 | Percentage features are empty in 94.5% of rows, and the 1-month percentage is always 1 when filled (it divides the month count by itself) | No information; not used in the model |
| 5 | Copay amount (`PTNT_COPAY`), out-of-pocket (`PATOOP`) and program group (`GRP_NUM`) are loaded but never used | Unused information |
| 6 | No copay feature made the final 752 | Copay has no effect on the 3.0 model |

---

## 3. Shared by FTP and Copay

### 3a. Where things are

| Item | Location |
| --- | --- |
| Combine + 752 selection notebook | `NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/99_Combine_Physician_Data` |
| NPI → Bayer ID / provider mapping | volume `hcp_level_model/ops_pipeline/query_output/kerendia_nba_3_0_npi_bhid_mapping` (Delta) |
| HCP universe | volume `hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` |
| 752 feature list | volume `hcp_level_model/ops_pipeline/input_files/Kerendia_NBA_3_feature_list_752_features.csv` |
| Final model input | volume `hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_selected_features_data` |
| SHAP importance (3.0 production model) | MLflow run `f583bcbc9d56477fae983d44c16f8c70`, artifact `Shap_Importances.csv` (752 rows: `Feature`, `Mean_Abs_SHAP`) |

All volume paths are under `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/`.

### 3b. Mapping table (NPI → Bayer ID / provider ID)

| | Value |
| --- | --- |
| Rows | 1,659,041 |
| Columns | `PROVIDER_ID` (100% filled), `NPI_NUMBER` (1,574,045 filled, 94.9%), `BH_ID` (100% filled) |
| Distinct | 1,659,041 `PROVIDER_ID`, 1,573,534 `NPI_NUMBER`, 1,658,328 `BH_ID` |
| Used by | FTP: `NPI_NUMBER` → `BH_ID`. Copay: `NPI_NUMBER` → `BH_ID` + `PROVIDER_ID`. Combine: `PROVIDER_ID` → `BH_ID` |

### 3c. Known issue not specific to FTP or Copay

| Issue | Effect |
| --- | --- |
| 2,743 `HCP_COHORT_ID`s appear more than once in the final model input | Cause not checked; not FTP- or copay-specific |
