# Personal Promotional Features — NBA 3.0 (Legacy)

**Scope:** Rep-driven (personal) promotional channels: BHO Calls (`13`), Sales Rep Calls (`25`), iRep Emails (`16`), ClickStream / CLM (`18`)  
**NBA 3.0 (legacy Ops):** `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Companion file:** `personal_promotional_features_strategic_file_nba_3_0_legacy.md`  
**Built from:** the legacy notebook code (feature names checked against the `withColumn` / `alias` statements)  
**Date:** October 22, 2026

For each channel, this file gives: (1) the source, (2) the preprocessing steps, (3) the features. Risk IDs (LC-*, LI-*, LK-*, LB-*) refer to the companion strategic file.

---

## 0. Shared Framework (applies to every channel)

| Aspect | NBA 3.0 (legacy Ops) |
| --- | --- |
| Purpose | Inference |
| Step 2 / Step 3 | `%run 00_step23_function`, then `step2_fill_missing_date` / `step3_lag_date` redefined inline |
| Time grain | Daily spine, rolling `rowsBetween(-i+1, 0)` |
| Windows | Calls, iRep: 90d only. BHO Calls, ClickStream: 30/60/90/120/150/180d |
| Output | Delta, overwrite, `ops_pipeline/notebook_output/..._for_inference` |
| Output keys | `HCP_COHORT_ID`, `BHID` (not ClickStream), `SVC_DT`, `PULL_DT` |

---

## 1. Sales Rep Calls (`25_promotional_features_call`)

### 1.1 Source

| Item | NBA 3.0 |
| --- | --- |
| Fact table | `CPH_DB_PROD.MODEL_V2.FACT_CALL` |
| ID mapping | `CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF` (`SOURCE_CUST_ID → BAYER_CUST_ID`) |

### 1.2 Preprocessing

1. Read cohort Delta, take `I01` `LOOKBACK_START_DATE` / `LOOKBACK_END_DATE`.
2. Snowflake pull: `UPPER(STAT) = 'SUBMITTED_VOD'`, `UPPER(DETL_PROD) = 'KERENDIA'`, `BAYER_CUST_ID NOT LIKE '%BHO%'`, `CALL_DATE` between the `I01` dates.
3. Map `UPPER(CALL_REC_TYP_NM)` to `CHNNL_NM` = `F2F` / `PHONE` / `GROUP_CALL` / `REMOTE_CALL`; anything else keeps its raw value.
4. One-hot flags for channel (4), call type (5, exact-case Veeva values), call purpose (5). `MISCELLANEOUS` = explicit list of 9 purpose values (Contract negotiation, Technical Operation, Reactive Sample / HVPI, Market Access, Regulatory Compliance, Education / Training, Technical Information, Handover of SPC, Handover of Scientific Publication).
5. `CALL_DURATION`: empty string → NULL (no explicit cast; summed as string-to-number implicitly).
6. Cross-join with cohort, filter to the lookback window, drop NULL BHID, `HCP_COHORT_ID = BHID_COHORT`.
7. Group by `HCP_COHORT_ID × day` and SUM all flags → `TOTAL_*`.
8. Cross features **after the daily aggregation**: `TOTAL_<CH>_AND_<CT> = least(TOTAL_<CH>, TOTAL_<CT>)`. The channel and call-type lists are collected from the raw data (`distinct().collect()`), minus `DO_NOT_SELECT` and `FACE2FACE_KAM_CALL`.
9. Step 2 daily spine + `fillna(0)`; Step 3 with `last_i_days_list = [90]`.
10. Keep the anchor row, drop base columns, `MONTH_ID → SVC_DT`, split `BHID`, add `PULL_DT` (`current_date()`), write Delta `kerendia_nba_3_hcp_model_call_features_for_inference`.

### 1.3 Features

Window: `_IN_LAST_3_MONTH` only.

| Group | Features (each with `_IN_LAST_3_MONTH`) |
| --- | --- |
| Channel (4) | `TOTAL_F2F`, `TOTAL_PHONE`, `TOTAL_GROUP_CALL`, `TOTAL_REMOTE_CALL` |
| Call type (5) | `TOTAL_DETAIL_ONLY`, `TOTAL_DETAIL_WITH_SAMPLE`, `TOTAL_GROUP_DETAIL`, `TOTAL_GROUP_DETAIL_WITH_SAMPLE`, `TOTAL_EVENT_DETAIL` |
| Purpose (5) | `TOTAL_CALL_PURPOSE_PROMOTIONAL_ACTIVITY`, `..._PROMOTIONAL_ACTIVITY_WITH_MEAL`, `..._EVENT_RELATED_PROMOTIONAL_ACTIVITY`, `..._NON_PROMOTIONAL_ACTIVITY`, `..._MISCELLANEOUS` |
| Duration (1) | `TOTAL_CALL_DURATION` |
| Cross (data-driven) | `TOTAL_<CH>_AND_<CT>`. Last run (2026-07-29): 4 channels × 4 call types = **16** (no `EVENT_DETAIL` in data) |

**Total:** 15 base + 16 cross = **31 features** (last run). The 3.0 documentation says 20 cross features; that holds only when all 5 call types appear in the data.

---

## 2. BHO Calls (`13_promotional_features_bho_calls`)

### 2.1 Source

| Item | NBA 3.0 |
| --- | --- |
| Fact table | `CPH_DB_PROD.MODEL_V2.FACT_CALL` ⋈ `MAP_CUSTOMER_XREF` (BHO accounts) |
| HCP spine | `ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` (222,125 HCPs) |
| ID chain | `PROVIDER_ID → BHID` via `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING`; `BHID → BHO_ID` via `PHCDW.PHCDW_STG.MDM_STG_HCP_ACCT_AFFL` |

### 2.2 Preprocessing

1. Load HCP universe; map `PROVIDER_ID → BHID → BHO_ID` (928,773 BHID–BHO pairs).
2. Pull Kerendia submitted calls on accounts `LIKE '%BHO%'` within the `I01` window (376,617 rows).
3. Join calls to every affiliated BHID (30,351,434 rows; about 80× fan-out).
4. Same flags, duration cleaning, cohort cross-join, daily aggregation and `least()` cross features as notebook `25`.
5. Step 2 daily spine; Step 3 with six windows (30–180d).
6. Keep the anchor row, prefix all features with `BHO_`, split `BHID`, add `PULL_DT` (string), write Delta `kerendia_nba_3_hcp_model_call_features_bhoid_for_inference`.

### 2.3 Features

`BHO_` + the notebook `25` feature set (channel, call type, purpose, duration, data-driven crosses) × 6 windows, e.g. `BHO_TOTAL_F2F_IN_LAST_3_MONTH`, `BHO_TOTAL_CALL_DURATION_IN_LAST_6_MONTH`.

---

## 3. iRep Emails (`16_promotional_features_irep`)

### 3.1 Source

| Item | NBA 3.0 |
| --- | --- |
| Tables | `CPH_DB_PROD.MODEL_V2.FACT_SENT_EMAIL` ⋈ `CPH_DB_PROD.MODEL_V2.DIM_APPROVED_DOCUMENT` ⋈ `PHCDW.PHCDW_STG.MDM_STG_HCP_XREF` (+ `MDM_STG_HCP_PRFL`, unused) |
| BHID | `MDM_STG_HCP_XREF.BH_ID` (`SOURCE_CD IN ('K2_AC2','VAULT_CRM_AC2')`) |

### 3.2 Preprocessing

1. Read cohort Delta, take `I01` dates.
2. `SELECT DISTINCT` BHID, sent date, clicked, opened, status, document name; filters `UPPER(DOC.NM) LIKE '%KERENDIA%'`, `UPPER(EMAIL_STATUS) LIKE 'DELIVERED%'`, non-BHO, sent date `<= LOOKBACK_END_DATE` (no lower bound in SQL).
3. Flags: `IREP_EMAIL_DELIVERED_FLAG` (`EMAIL_STATUS == 'Delivered'`, exact), `IREP_EMAIL_CLICKED_FLAG`, `IREP_EMAIL_OPENED_FLAG`; 11 `IREP_APPRVD_DOC_NM_*` flags from hard-coded `isin` lists.
4. Cross-join with cohort, filter to the lookback window, drop NULL BHID, build `HCP_COHORT_ID`.
5. Group by `HCP_COHORT_ID × day`; explicit aliases (`TOTAL_IREP_EMAILS_DELIVERED`, etc.).
6. Step 2 daily spine + `fillna(0)`; Step 3 with `[90]`.
7. Keep the anchor row, split `BHID`, add `PULL_DT` (string), write Delta `kerendia_nba_3_hcp_model_irep_features_for_inference`.

### 3.3 Features

Window: `_IN_LAST_3_MONTH` only. **14 features.**

| Group | Features |
| --- | --- |
| Engagement (3) | `TOTAL_IREP_EMAILS_DELIVERED`, `TOTAL_IREP_EMAILS_CLICKED`, `TOTAL_IREP_EMAILS_OPENED` |
| Document (11) | `TOTAL_IREP_APPRVD_DOC_NM_` + `FDA`, `PSP_PRESCRIBING`, `BRANDED_ASSET`, `NATIONAL_BROADCAST`, `KIDNEY`, `INVITE`, `EDUCATION`, `BACC_ACCESS`, `EXCLUSIVE_BROADCAST`, `TRIAL`, `MISCELLANEOUS` |

---

## 4. ClickStream / CLM (`18_promotional_ClickStream_features`)

### 4.1 Source

| Item | NBA 3.0 |
| --- | --- |
| ClickStream | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM` |
| Calls (for `CALL_ID`) | `FACT_CALL` ⋈ `MAP_CUSTOMER_XREF` (submitted, Kerendia, non-BHO) |
| BHID | `BAYER_HCP_ID` from ClickStream |

### 4.2 Preprocessing

1. Read cohort Delta, take `I01` dates.
2. Pull ClickStream with `BAYER_PROD_NM = 'KERENDIA'` and `DATE_ID <= LOOKBACK_END_DATE`; pull call IDs with no date filter.
3. Dedup: one row per `CALL_ID` (max `USAGE_DUR`, then max `PRESN_DUR`).
4. Inner join to submitted call IDs; parse `DATE_ID` (`yyyyMMdd`) to a date; add `SUBMITTED_CALL_COUNT = 1` (not output).
5. Cross-join with cohort, window filter, drop NULL BHID, `HCP_COHORT_ID`.
6. Daily aggregation: SUM and AVG of usage and presentation duration.
7. Step 2 daily spine + `fillna(0)`; Step 3 rolling **SUM** for all four (including the AVG columns, LK-1) over six windows.
8. Keep the anchor row, drop base columns, prefix `CLICKSTREAM_`, add `PULL_DT` (string), write Delta `kerendia_nba_3_hcp_model_clickstream_features_for_inference`. No `BHID` column.

### 4.3 Features

**4 × 6 = 24 features:** `CLICKSTREAM_TOTAL_USAGE_DURATION`, `CLICKSTREAM_TOTAL_PRESN_DURATION`, `CLICKSTREAM_AVG_USAGE_DURATION`, `CLICKSTREAM_AVG_PRESN_DURATION`, each `_IN_LAST_1_MONTH` … `_IN_LAST_6_MONTH`.

---

## 5. Summary

| Channel | Windows | Feature count | Output table |
| --- | --- | --- | --- |
| Calls (25) | 90d | 31 (last run) | `kerendia_nba_3_hcp_model_call_features_for_inference` |
| BHO Calls (13) | 30–180d | ~31 × 6 | `kerendia_nba_3_hcp_model_call_features_bhoid_for_inference` |
| iRep (16) | 90d | 14 | `kerendia_nba_3_hcp_model_irep_features_for_inference` |
| ClickStream (18) | 30–180d | 24 | `kerendia_nba_3_hcp_model_clickstream_features_for_inference` |
