# Non-Personal Promotional Features — NBA 3.0 (Legacy)

**Scope:** Non-rep (non-personal) channels: Digital / MMX (`24`), HQ Emails (`15`), DTC (`34`), Samples (`17`), Speaker Programs (`14`), Free Trial Program / FTP (`19`)  
**NBA 3.0 (legacy Ops):** `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Companion file:** `non_personal_promotional_features_strategic_file_nba_3_0_legacy.md`  
**Built from:** the legacy notebook code (feature names checked against the `withColumn` / `alias` statements)  
**Date:** October 22, 2026

For each channel, this file gives: (1) the source, (2) the preprocessing steps, (3) the features. 


---

## 0. Shared Framework

| Aspect | NBA 3.0 (legacy Ops) |
| --- | --- |
| Purpose | Inference |
| Cohort source | Delta `ops_pipeline/notebook_output/promotional_cohort_inference_dates`, cohort `I01` |
| Connection / helpers | `%run 00_connection`, `00_config`, `00_step23_function` (Digital: `sfOptionscdpread`) |
| Architectures | A: cohort day-spine (HQ, Samples, Speaker, FTP); B: monthly NPI panel (Digital); C: DMA × month (DTC) |
| Output | Delta `ops_pipeline/notebook_output/..._for_inference` |

---

## 1. Digital / Paid Media (`24_Features_Digital`)

### 1.1 Source

| Item | NBA 3.0 |
| --- | --- |
| Table | `PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB` (replaced `_TEMP` on 2025-04-29) |
| Connector | `sfOptionscdpread` (Spark Snowflake connector) |
| Grain | `NPI_NUMBER × SVC_DT_M` |

### 1.2 Preprocessing

1. Read cohort Delta; `digital_start = I01 LOOKBACK_START_DATE`.
2. Pull Kerendia rows (`BRND_NM = 'KERENDIA'`) with `DATE_TRUNC('MONTH', DATE_ACT) >= digital_start` (no upper bound).
3. **Standardize channels:** `CALL → CALLS`, `HQ EMAIL → HQ_EMAILS`, `IREP EMAIL → IREP_EMAILS`, `SAMPLE → SAMPLES`.
4. **Standardize tactics** to 14 labels + `OTHER_TACTIC`.
5. **Filter `CHANNEL NOT IN ('CALLS','SAMPLES')`.**
6. Three dynamic pivots (`CHANNEL`, `SRC_SYS_CD`, `TACTIC_NAME`) × 4 metrics (`DEEP_ENGAGEMENT`, `LIGHT_ENGAGEMENT`, `TOTAL_ENGAGEMENT`, `EXPOSURE`).
7. Helper `step2_fill_missing` (monthly spine) + `step3_lag` with windows 1, 3, 6 months for each pivot set.
8. Drop tactic base columns (channel and source base columns are kept).
9. Left-join the 3 sets on `NPI_NUMBER + SVC_DT_M`, prefix `DIGITAL_`, add `PULL_DT`, write Delta `kerendia_nba_3_0_hcp_model_paid_search_features_for_inference`.

### 1.3 Features

Pattern: `DIGITAL_<VALUE>_<METRIC>_IN_LAST_{1,3,6}_MONTH` for each pivot value of `CHANNEL`, `SRC_SYS_CD`, `TACTIC_NAME`, plus current-month channel and source base columns.

* Channels: digital channels after standardization, including `HQ_EMAILS` and `IREP_EMAILS` (no `CALLS` / `SAMPLES`).
* Tactics (15): `BANNER_TACTIC`, `CTV_TACTIC`, `HQ_EMAIL_TACTIC`, `DOCNEWS_TACTIC`, `VIDEO_TACTIC`, `IREP_EMAIL_TACTIC`, `MONOGRAPH_MESSAGE_TACTIC`, `DOCSPOT_TACTIC`, `BRAND_ALERT_TACTIC`, `DOC_ALERT_TACTIC`, `EMAIL_TACTIC`, `EMAIL_ALERT_TACTIC`, `NATIVEVIDEO_TACTIC`, `FORMULARY_TACTIC`, `OTHER_TACTIC`.
* Metrics: `DEEP_ENGAGEMENT`, `LIGHT_ENGAGEMENT`, `TOTAL_ENGAGEMENT`, `EXPOSURE`.
* Example: `DIGITAL_HQ_EMAILS_DEEP_ENGAGEMENT_IN_LAST_3_MONTH`.

---

## 2. HQ Emails (`15_promotional_features_HQ_Emails`)

### 2.1 Source

| Item | NBA 3.0 |
| --- | --- |
| Table | `PHCDW.PHCDW_CDM.HCP_EMAIL_LIST` |
| Other inputs | `kerendia_nba_3_0_npi_bhid_mapping` (loaded, reference only) |

### 2.2 Preprocessing

1. Read cohort Delta, `I01` dates.
2. Pull `EVENTDATE`, `EVENTTYPE`, `BH_ID` where `UPPER(EMAILPRODUCTTYPE) LIKE '%KERENDIA%'`, `BH_ID LIKE 'BH%'`, event date within the `I01` window (5,740,895 events, 191,020 BHIDs).
3. Cast `EVENTDATE` to date, `FLAG = 1`.
4. Cross-join with cohort, window filter, drop NULL BHID, `HCP_COHORT_ID`.
5. Group by `HCP_COHORT_ID × day`, **dynamic pivot** on `EVENTTYPE`, rename to `TOTAL_<EVENTTYPE>`.
6. Step 2 daily spine + `fillna(0)`; Step 3 with `[90]`.
7. Keep the anchor row (`LOOKBACK_END_DATE` kept), split `BHID`, add `PULL_DT`, write Delta `kerendia_nba_3_hcp_model_hq_email_features_for_inference`.

### 2.3 Features

Window: `_IN_LAST_3_MONTH` only. **5 features:** `TOTAL_BOUNCE`, `TOTAL_CLICK`, `TOTAL_OPEN`, `TOTAL_SENT`, `TOTAL_UNSUBSCRIBE` (set depends on the event types present, LH-1).

---

## 3. DTC Direct Buy + Social (`34_promotional_features_DTC`)

### 3.1 Source

| Item | NBA 3.0 |
| --- | --- |
| Direct Buy | Delta `ops_pipeline/query_output/kerendia_nba_3_0_hcp_model_DirectBuys` |
| Social (FB + IG) | Delta `ops_pipeline/query_output/kerendia_nba_3_0_hcp_model_social` |
| PulsePoint, TTD Display | Loaded and pivoted, **never merged** (LT-1) |
| Grain | `DMA_Code × month` |

These are pre-built Delta snapshots, not live tables.

### 3.2 Preprocessing

1. Load Direct Buy and Social Delta tables (plus PulsePoint and TTD, unused).
2. Group by `DMA_Code × MONTH × VENDOR`; SUM impressions and clicks.
3. Dynamic pivot on `VENDOR`; `na.fill(0)` **before** the join.
4. Full outer join Direct Buy ⋈ Social on `DMA_Code + DATA_MONTH` (NULLs remain for one-sided months, LT-2).
5. Prefix `DTC_PROMOTION_`, add `PULL_DT`, write Delta `kerendia_nba_3_hcp_model_DTC_PROMOTION_for_inference`.

### 3.3 Features

**10 features** (verified in saved output), no time windows:
`DTC_PROMOTION_{HEALTH_UNION | HEALTHLINE | SHARECARE | WEBMD | FB_AND_IG}_TOTAL_{IMPRESSIONS | CLICKS}`.

---

## 4. Samples (`17_promotional_features_samples`)

### 4.1 Source

| Item | NBA 3.0 |
| --- | --- |
| Table | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER` (since 2025-12-19; earlier `PHCDW_DSAA.VIEW_KERENDIA_SAMPLES_DROPPED_SHIPPED` and a 2025-10-30 union query, both commented) |
| HCP universe | `base_hcp_universe_for_inference` + `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING` |

### 4.2 Preprocessing

1. Read cohort Delta, `I01` dates.
2. `SELECT DISTINCT BHID, SMPLE_CALL_DT, SMPLE_CALL_NM, UPPER(SMPLE_NM), SMPLE_QTY, SAMPLE_FLAG` (159,970 rows; max date 2026-05-19).
3. Quantity columns for 6 hard-coded names: `KERENDIA 10MG`, `KERENDIA 20MG`, `KERENDIA 10MG BRC`, `KERENDIA 20MG BRC`, `KERENDIA SAMPLING KIT BRC`, `KERENDIA SAMPLE HOUSING BOX BRC` (**`KERENDIA 40MG BRC` missing**, LS-1).
4. `OVERALL_SAMPLE`, `SAMPLE_DROPPED`, `SAMPLE_SHIPPED` (all quantity, brochures excluded).
5. Cross-join with cohort, window filter, drop NULL BHID, `HCP_COHORT_ID`.
6. Group by `HCP_COHORT_ID × day`, SUM → 9 `TOTAL_*` columns.
7. Step 2 daily spine + `fillna(0)`; Step 3 with six windows.
8. Keep the anchor row, split `BHID`.
9. **Inner join to the HCP universe spine** (LS-4), null check, `PULL_DT`, write Delta `kerendia_nba_3_hcp_model_samples_features_for_inference`.

### 4.3 Features

**9 × 6 = 54 features** (quantity only):
`TOTAL_OVERALL_SAMPLE`, `TOTAL_SAMPLE_10MG`, `TOTAL_SAMPLE_20MG`, `TOTAL_SAMPLE_10MG_BRC`, `TOTAL_SAMPLE_20MG_BRC`, `TOTAL_SAMPLE_SAMPLING_KIT_BRC`, `TOTAL_SAMPLE_SAMPLE_HOUSING_BOX_BRC`, `TOTAL_SAMPLE_DROPPED`, `TOTAL_SAMPLE_SHIPPED`, each `_IN_LAST_1_MONTH` … `_IN_LAST_6_MONTH`.

---

## 5. Speaker Programs (`14_promotional_features_speaker_program`)

### 5.1 Source

| Item | NBA 3.0 |
| --- | --- |
| Table | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM` |
| HCP ID column | `CUST_HCP_ID` (`LIKE '%BH%'`, not NULL, not empty) |

### 5.2 Preprocessing

1. Read cohort Delta, `I01` dates.
2. `SELECT DISTINCT EVNT_ID, CUST_HCP_ID, ATND, EVNT_START_DATE, EVNT_FMT, EVNT_TYP, EVNT_TPIC_NM`; `PROD_BRAND_NM = 'KERENDIA'`, `UPPER(ATND) = 'ATTENDED'`, event date within the **dynamic** `I01` window (10,766 rows).
3. `dropDuplicates()`, then drop `EVNT_ID`.
4. Flags: `ATTENDED_FLAG`; format (`F2F`, `IN_OFFC_MEAL`, `REMOTE`, `HYBRID`, `OTHER` = `EVNT_TPIC_NM IS NULL`, LSP-2); type (`isin('SPEAKER PROGRAMS')` / `'NON-SPEAKER PROGRAMS'`, likely always 0, LSP-1); topic (`CKD`, `CVR`, `INTRO` from hard-coded deck lists; `OTHER` = `Display/Exhibit` or NULL).
5. Cross-join with cohort, window filter, drop NULL BHID, `HCP_COHORT_ID`.
6. Group by `HCP_COHORT_ID × day`; explicit aliases. `IN_OFFC_MEAL` is **not** aggregated (LSP-4).
7. Step 2 daily spine + `fillna(0)`; Step 3 with six windows.
8. Keep the anchor row, split `BHID`, add `PULL_DT`, write Delta `kerendia_nba_3_hcp_model_speaker_program_for_inference`.

### 5.3 Features

**11 × 6 = 66 features:**

| Group | Features |
| --- | --- |
| Overall (1) | `TOTAL_SPEAKER_PROGRAMS_ATTENDED` |
| Format (4) | `TOTAL_SPKR_EVNT_FMT_F2F`, `TOTAL_SPKR_EVNT_FMT_REMOTE`, `TOTAL_SPKR_EVNT_FMT_HYBRID`, `TOTAL_SPKR_EVNT_FMT_OTHER` |
| Type (2) | `TOTAL_SPKR_EVNT_TYP_SPKR_PRGM`, `TOTAL_SPKR_EVNT_TYP_NON_SPKR_PRGM` |
| Topic (4) | `TOTAL_SPKR_TOPIC_CKD`, `TOTAL_SPKR_TOPIC_CVR`, `TOTAL_SPKR_TOPIC_INTRO`, `SPKR_TOPIC_OTHER` (no `TOTAL_` prefix, LSP-3) |

---

## 6. Free Trial Program / FTP (`19_ftp_features`)

### 6.1 Source

| Item | NBA 3.0 |
| --- | --- |
| Table | `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP` (`USE_SLS = 'Y'`) |
| NPI → BHID | Delta `ops_pipeline/query_output/kerendia_nba_3_0_npi_bhid_mapping` (inner join) |

### 6.2 Preprocessing

1. Read cohort Delta, `I01` dates.
2. Pull voucher claims with `USE_SLS = 'Y'`, `PRSC_NPI IS NOT NULL` (no date filter; 2021-01-13 → 2025-09-29 at last run).
3. Reversal removal: `ORGN_CLM_AUTH_NUM` groups with net `DAY_SUPPLY = 0` collected via `toPandas()` and excluded with `isin` (LF-4).
4. Inner join NPI → BHID (LF-5 fan-out).
5. Cross-join with cohort, window filter, `HCP_COHORT_ID`.
6. `TOTAL_RX_FTP = count(rows)` per `HCP_COHORT_ID × day`.
7. Step 2 daily spine + `fillna(0)`; Step 3 with six windows; keep the anchor row.
8. `keep_cols` uses `LOOKBACK_END_MONTH` (typo, LF-2); `MONTH_ID` is not renamed; add `PULL_DT` (`DATE`); write Delta `kerendia_nba_3_hcp_model_ftp_features_v2_for_inference` (duplicate write cell).

### 6.3 Features

**6 features:** `TOTAL_RX_FTP_IN_LAST_1_MONTH` … `TOTAL_RX_FTP_IN_LAST_6_MONTH`. Keys: `HCP_COHORT_ID`, `MONTH_ID`, `PULL_DT` (run date).

---

## 7. Summary

| Channel | Windows | Feature count | Output table |
| --- | --- | --- | --- |
| Digital (24) | 1 / 3 / 6 months | dynamic (pivot-driven) | `kerendia_nba_3_0_hcp_model_paid_search_features_for_inference` |
| HQ Emails (15) | 90d | 5 | `kerendia_nba_3_hcp_model_hq_email_features_for_inference` |
| DTC (34) | none | 10 | `kerendia_nba_3_hcp_model_DTC_PROMOTION_for_inference` |
| Samples (17) | 30–180d | 54 | `kerendia_nba_3_hcp_model_samples_features_for_inference` |
| Speaker (14) | 30–180d | 66 | `kerendia_nba_3_hcp_model_speaker_program_for_inference` |
| FTP (19) | 30–180d | 6 | `kerendia_nba_3_hcp_model_ftp_features_v2_for_inference` |
