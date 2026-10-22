# Personal Promotional Features — Strategic File (Kerendia NBA 3.0 Legacy / Ops)

**Scope:** Rep-driven (personal) promotional channels in the NBA 3.0 **Ops inference** pipeline  
**Legacy location:** `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Channels covered:** BHO (organization) Calls (`13`), Non-BHO Sales Rep Calls (`25`), iRep Emails (`16`), ClickStream / CLM (`18`)  
**Built from:** cell-by-cell review of the four legacy notebooks (code + last saved outputs) and `EDA Promotion/promotional_features_nba_3_0_documentation.md`  
**Companion file:** `personal_promotional_features_strategic_file.md` (NBA 3.1 Dev)  
**Date:** October 22, 2026

> Purpose of this file: document what the legacy pipeline **actually does in production**, so NBA 3.1 can (a) keep the parts that work, (b) not re-introduce known defects, and (c) reproduce legacy features exactly where parity with the 3.0 model is required.

---

## 1. Strategic Context — What "Legacy" Means Here

The NBA 3.0 Ops notebooks are the **inference** variant of the 3.0 feature pipeline, not the training variant:

* Every notebook reads `ops_pipeline/notebook_output/promotional_cohort_inference_dates` (Delta) and pulls `LOOKBACK_START_DATE` / `LOOKBACK_END_DATE` from cohort **`I01`**.
* `I01` is a single 12-month lookback that rolls forward each refresh (observed: `2024-09-17 → 2025-09-17`, `2025-04-16 → 2026-04-16`, `2025-05-17 → 2026-05-17`, `2025-07-17 → 2026-07-17`).
* Outputs are Delta tables with the suffix `_for_inference` under `ops_pipeline/notebook_output/`.
* Window lists were **trimmed to what the final 3.0 model uses**: Calls and iRep only produce the 90-day (`_IN_LAST_3_MONTH`) window; BHO Calls and ClickStream keep all six.

Strategic implication: the legacy feature set is a **model-selected subset**, not the full feature space. NBA 3.1 re-expands to six windows everywhere, so 3.1 vs 3.0 comparisons must be restricted to `_IN_LAST_3_MONTH` columns for Calls and iRep.

---

## 2. Channel Portfolio at a Glance

| # | Channel | Notebook | Source (current code) | Grain / ID | Windows | Feature prefix | Output (Delta, `ops_pipeline/notebook_output/`) | Last interactive run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | BHO Calls | `13_promotional_features_bho_calls` | `FACT_CALL` (BHO accounts) + `MDM_STG_HCP_ACCT_AFFL` | BHO → affiliated BHID | 6 (30–180d) | `BHO_` | `kerendia_nba_3_hcp_model_call_features_bhoid_for_inference` | 2025-11-27 |
| 2 | Sales Rep Calls | `25_promotional_features_call` | `CPH_DB_PROD.MODEL_V2.FACT_CALL` + `MAP_CUSTOMER_XREF` (non-BHO) | BHID | **1 (90d)** | none | `kerendia_nba_3_hcp_model_call_features_for_inference` | 2026-07-29 |
| 3 | iRep Emails | `16_promotional_features_irep` | `CPH_DB_PROD.MODEL_V2.FACT_SENT_EMAIL` + `DIM_APPROVED_DOCUMENT` + `MDM_STG_HCP_XREF` | BHID | **1 (90d)** | `TOTAL_IREP_` | `kerendia_nba_3_hcp_model_irep_features_for_inference` | 2026-05-04 |
| 4 | ClickStream / CLM | `18_promotional_ClickStream_features` | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM` ⋈ `FACT_CALL` | BHID | 6 (30–180d) | `CLICKSTREAM_` | `kerendia_nba_3_hcp_model_clickstream_features_for_inference` | 2025-10-07 |

Observed volumes (last saved outputs):

* Calls (`25`): 484,119 raw call rows for the `2025-07-17 → 2026-07-17` window; current call types in source = `Detail Only`, `Group Detail`, `Group Detail with Sample`, `Detail with Sample` (no `Event Detail`).
* BHO Calls (`13`): 376,617 BHO call rows → **30,351,434 rows after the BHO→BHID affiliation join** (about 80x fan-out); HCP universe = 222,125.
* "Last interactive run" is the notebook cell timestamp. Job-scheduled runs do not update it, so stale dates (ClickStream) need a job-history check, not an assumption that the notebook is dead.

---

## 3. Shared Legacy Pipeline

1. `%run 00_Helper_Notebooks/00_connection` (Snowflake `Get_Data_Snowflakes`), `00_config` (25 only), `00_step23_function`.
2. Read the cohort Delta, take `I01` dates, and push the window into the Snowflake SQL where possible.
3. One-hot flags → `crossJoin(cohort_anchor_date)` → filter to `[LOOKBACK_START_DATE, LOOKBACK_END_DATE]` → `HCP_COHORT_ID = BHID_COHORT`.
4. Group by `HCP_COHORT_ID × day` (`MONTH_ID` is a **day**, not a month; the `trunc(..., 'month')` lines are commented out).
5. `step2_fill_missing_dates` (redefined inline in each notebook, shadowing the helper) → dense daily spine → `fillna(0)`.
6. `step3_lag_date` with `rowsBetween(-i+1, 0)` → keep anchor row → drop base columns → `MONTH_ID → SVC_DT`.
7. Add `PULL_DT` and overwrite the Delta path.

Strategic observations:

* **Helper vs inline drift.** `%run 00_step23_function` is executed but every notebook redefines `step2_*` / `step3_*` locally. The helper's monthly `step2_fill_missing` / `step3_lag` is only used by Digital (`24`). Two implementations of "the same" logic live side by side.
* **`PULL_DT` type is inconsistent.** It is a string `yyyy_MM_dd` in 13 / 16 / 18 and a `DATE` (`current_date()`) in 25.
* **Daily spine over 12 months** (≈366 rows per HCP-cohort) while the widest kept window is 180 days (90 for Calls/iRep). Same over-build as 3.1, but worse for 25/16 where only 90 days are needed.

---

## 4. Channel Deep Dives and Risks

### 4.1 Sales Rep Calls (`25_promotional_features_call`)

**Logic (2025-09-10 query):** `UPPER(STAT)='SUBMITTED_VOD'`, `UPPER(DETL_PROD)='KERENDIA'`, `BAYER_CUST_ID NOT LIKE '%BHO%'`, I01 date window. `CALL_REC_TYP_NM` → `F2F` / `PHONE` / `GROUP_CALL` / `REMOTE_CALL`, else the raw value.

Base features: 4 channel + 5 call type + 5 purpose (incl. a hard-coded MISCELLANEOUS list) + `TOTAL_CALL_DURATION` = 15, plus data-driven `channel × call type` cross features. Only `_IN_LAST_3_MONTH` is output.

| ID | Risk | Evidence | Impact |
| --- | --- | --- | --- |
| LC-1 | **Cross features are computed on daily totals with `least()`**, not at call level | `TOTAL_F2F_AND_DETAIL_ONLY = least(TOTAL_F2F, TOTAL_DETAIL_ONLY)` after the day group-by | Upper-bound approximation. An HCP with one F2F-with-sample and one Phone-detail-only on the same day gets `F2F_AND_DETAIL_ONLY = 1` although no such call happened. 3.1 must decide whether to replicate (parity) or fix (row-level AND). |
| LC-2 | **Cross-feature list is data-driven** | `chnnl_nm` / `call_typ_cd` from `distinct().collect()` of the raw pull, minus `DO_NOT_SELECT`, `FACE2FACE_KAM_CALL` | Any new unmapped `CALL_REC_TYP_NM` falls through the `ELSE` and produces `TOTAL_<raw>`, which does not exist → `AnalysisException`. Schema also changes run to run (e.g. no `EVENT_DETAIL` crosses today). |
| LC-3 | `CALL_DURATION` is a string | `CALL_DUR` → blank → `None`, then `sum()` | Implicit cast. Non-numeric strings silently become NULL. |
| LC-4 | `EVENT_DETAIL` flag is always 0 in current data | Distinct `CALL_TYP` shows 4 values, no `Event Detail` | Constant column in the model input. |
| LC-5 | Only 90-day window | `last_i_days_list = [90]` | 3.1 (6 windows) cannot be compared 1-to-1 beyond `_IN_LAST_3_MONTH`. |
| LC-6 | NPI mapping loaded but unused | `df_hcp_npi_mapping` read, never joined | Dead read; harmless but confusing. |

### 4.2 BHO Calls (`13_promotional_features_bho_calls`)

**Logic:** HCP universe (`PROVIDER_ID`) → BHID via `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING` → BHO via `PHCDW.PHCDW_STG.MDM_STG_HCP_ACCT_AFFL` (928,773 BHID–BHO pairs) → join to BHO-account calls. Same flag set as `25`; all features prefixed `BHO_`; six windows.

| ID | Risk | Evidence | Impact |
| --- | --- | --- | --- |
| LB-1 | **Org-call fan-out**: every call on an organization is credited to every affiliated HCP | 376,617 → 30,351,434 rows | Inflated exposure for HCPs in large groups; feature reflects org size more than rep effort. Needs either per-HCP weighting (`1 / #affiliated HCPs`) or a flag-only treatment. |
| LB-2 | Affiliation is current-state, not as-of | `MDM_STG_HCP_ACCT_AFFL` has no effective-date filter | Historical calls are attributed using today's affiliations (look-ahead for training, drift for inference). |
| LB-3 | `PULL_DT` string; `LOOKBACK_END_DATE` dropped | Output cells | Minor contract inconsistency vs `25`. |
| LB-4 | No 3.1 counterpart | 3.1 Dev has no BHO notebook | Either confirm BHO features are dropped in 3.1 or port with LB-1 fixed. |

### 4.3 iRep Emails (`16_promotional_features_irep`)

**Logic (2025-10-29 query from Data Team):** `FACT_SENT_EMAIL` ⋈ `DIM_APPROVED_DOCUMENT` (`UPPER(DOC.NM) LIKE '%KERENDIA%'`) ⋈ `MDM_STG_HCP_XREF` (`SOURCE_CD IN ('K2_AC2','VAULT_CRM_AC2')`), `UPPER(EMAIL_STATUS) LIKE 'DELIVERED%'`, non-BHO, upper date bound only. 3 engagement + 11 approved-document buckets = 14 base features, 90-day window only.

| ID | Risk | Evidence | Impact |
| --- | --- | --- | --- |
| LI-1 | **Status filter vs flag mismatch** | SQL keeps `LIKE 'DELIVERED%'`; flag is `EMAIL_STATUS == 'Delivered'` (exact) | If the source uses `Delivered_vod`, every row passes the filter but `TOTAL_IREP_EMAILS_DELIVERED = 0`. Must be checked on live data. |
| LI-2 | `SELECT DISTINCT` on (BHID, date, flags, status, doc) | Query | Two identical sends of the same doc on the same day collapse to one. |
| LI-3 | Hard-coded document lists | 11 `isin` lists | New Kerendia templates fall into no bucket (not even MISC) and are invisible except in the delivered/open/click totals. |
| LI-4 | `MDM_STG_HCP_PRFL` joined but unused | Query | Extra join cost; possible row duplication if PRFL is not unique on `BH_ID`. |
| LI-5 | **3.1 Dev still uses the pre-2025-10-29 source** | 3.1 iRep reads `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_IREP`, which is the commented-out legacy query | Source parity gap: 3.1 iRep features are built on a source that legacy deliberately replaced. |

### 4.4 ClickStream / CLM (`18_promotional_ClickStream_features`)

**Logic:** `ANLT_BASE_FACT_CLKSTRM` (`BAYER_PROD_NM='KERENDIA'`, `DATE_ID <= LOOKBACK_END_DATE`) → one row per `CALL_ID` (max usage, then max presentation duration) → inner join to submitted, non-BHO Kerendia `FACT_CALL` IDs (BHID taken from ClickStream) → daily SUM and AVG of usage/presentation duration → six windows → `CLICKSTREAM_` prefix.

| ID | Risk | Evidence | Impact |
| --- | --- | --- | --- |
| LK-1 | **AVG features rolled with SUM** | `AVG_*` daily → `F.sum(...).over(window)` | `AVG_USAGE_DURATION_IN_LAST_3_MONTH` is a sum of daily averages, not an average. Same defect carried into 3.1 (K-1). |
| LK-2 | No `BHID` column in output | BHID split cell commented out | Only `HCP_COHORT_ID`, `SVC_DT`, features. Combine step must parse BHID, unlike Calls/iRep. |
| LK-3 | `FACT_CALL` pulled with no date filter | Calls query | Full-history pull every run just to get call IDs. |
| LK-4 | Last interactive run 2025-10-07 | Cell metadata | Confirm whether it is still in the Ops job; if not, inference uses year-old ClickStream features. |

---

## 5. Cross-Channel Consistency Matrix (Legacy)

| Attribute | BHO Calls 13 | Calls 25 | iRep 16 | ClickStream 18 |
| --- | --- | --- | --- | --- |
| Windows | 30–180 | 90 | 90 | 30–180 |
| BHO handling | BHO only | `NOT LIKE '%BHO%'` | `NOT LIKE 'BHO%'` | non-BHO via FACT_CALL |
| Date bound in SQL | lookback | start + end | end only | end only (ClickStream) |
| `BHID` column in output | yes | yes | yes | **no** |
| `LOOKBACK_END_DATE` in output | dropped | dropped | dropped | dropped |
| `PULL_DT` type | string | date | string | string |
| Feature prefix | `BHO_` | none | `TOTAL_IREP_` | `CLICKSTREAM_` |
| Cross features | `least()` on daily totals | `least()` on daily totals | n/a | n/a |

---

## 6. Legacy → NBA 3.1 Delta

| Topic | Legacy 3.0 Ops | NBA 3.1 Dev | Verdict |
| --- | --- | --- | --- |
| Cohort source | Delta, single `I01` (inference) | CSV, C01–C26 (training) | Expected difference (training vs inference) |
| Connection/helpers | `%run 00_connection`, `00_step23_function` | Inline functions | 3.1 more self-contained; keep one implementation |
| Date window in SQL | Dynamic from `I01` | iRep hard-coded `'2025-04-16'` end date | **3.1 regression** (P0-1 in 3.1 file) |
| iRep source | `FACT_SENT_EMAIL` (2025-10-29) | `VIEW_RB_KERENDIA_IREP` | **3.1 regression** (LI-5) |
| Windows (Calls, iRep) | 90 only | 30–180 | 3.1 expansion; compare on 90d only |
| Cross features | `least()` on daily totals | Check implementation | Decide parity vs fix (LC-1) |
| ClickStream AVG | SUM of daily AVG | Same | Inherited defect (LK-1) |
| BHO Calls | Present | Absent | Decision needed (LB-4) |
| Output format | Delta `_for_inference` | Parquet in `dev_folder` | Align on Delta for 3.1 Ops |

---

## 7. Prioritized Action Plan

**P0 — correctness / parity blockers**

* P0-1: Check `FACT_SENT_EMAIL.STAT` distinct values; fix the `== 'Delivered'` flag (LI-1) in legacy, and switch 3.1 iRep to the legacy `FACT_SENT_EMAIL` query (LI-5).
* P0-2: Decide the BHO policy for 3.1 (drop or port), and if ported, de-duplicate the org-call fan-out (LB-1).
* P0-3: Make the cross-feature list static (LC-2) so that an unmapped `CALL_REC_TYP_NM` cannot break the Ops run.

**P1 — feature semantics**

* P1-1: Replace SUM-of-AVG in ClickStream with `SUM(duration) / SUM(calls)` per window (LK-1).
* P1-2: Document the `least()` cross-feature semantics; build the row-level version in 3.1 and measure the delta on one cohort (LC-1).
* P1-3: Cast `CALL_DURATION` explicitly and count rows that fail the cast (LC-3).

**P2 — hygiene / cost**

* P2-1: Remove dead reads (NPI mapping in 25, PRFL join in 16) and the unused helper `%run`.
* P2-2: Standardize `PULL_DT` to `DATE`, always output `BHID`.
* P2-3: Trim the daily spine to `LOOKBACK_END_DATE − max(window) + 1`.
* P2-4: Confirm the ClickStream job schedule (LK-4).

---

## 8. Validation Checklist (Legacy vs 3.1 Parity)

* [ ] For the same `I01` window, row counts of raw pulls match between legacy and 3.1 (Calls, iRep, ClickStream).
* [ ] `_IN_LAST_3_MONTH` Calls features: legacy vs 3.1 per-BHID difference = 0 for base features; cross-feature difference explained by LC-1 only.
* [ ] `TOTAL_IREP_EMAILS_DELIVERED_IN_LAST_3_MONTH` is non-zero for HCPs with delivered emails (LI-1).
* [ ] No new `TOTAL_<raw CALL_REC_TYP_NM>` columns in the Calls output.
* [ ] ClickStream AVG features ≤ max single-call duration after P1-1.
* [ ] BHO features: distribution of affiliated-HCP counts per BHO, top-10 BHOs by fan-out.

---

## 9. Open Questions

1. Which Ops job runs these notebooks, and is ClickStream (`18`) still in it?
2. Was the 90-day-only window for Calls and iRep driven by feature selection in the final 3.0 model? If so, should 3.1 keep six windows for training only?
3. Is BHO-level call activity a required driver for 3.1 recommendations?
4. What are the live values of `FACT_SENT_EMAIL.STAT` (`Delivered` vs `Delivered_vod`)?
5. Should 3.1 replicate the `least()` cross features for parity with 3.0 scores?
