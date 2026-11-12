# Non-Personal Promotional Features — Strategic File (Kerendia NBA 3.0 Legacy / Ops)

**Scope:** Non-rep (non-personal) promotional channels in the NBA 3.0 **Ops inference** pipeline  
**Legacy location:** `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Channels covered:** Digital / Paid Media (`24`), HQ Emails (`15`), DTC (`34`), Samples (`17`), Speaker Programs (`14`), Free Trial Program / FTP (`19`)  
**Built from:** cell-by-cell review of the six legacy notebooks (code + last saved outputs) and `EDA Promotion/promotional_features_nba_3_0_documentation.md`  
**Companion file:** `non_personal_promotional_features_strategic_file.md` (NBA 3.1 Dev)  
**Date:** October 22, 2026

> Purpose of this file: record what the legacy pipeline actually computes, so NBA 3.1 can keep what works, avoid known defects, and reproduce legacy features where parity with 3.0 scores is required.

---

## 1. Strategic Context

The legacy non-personal notebooks are not one pipeline. They follow **three different architectures**:

| Architecture | Notebooks | Grain | Time logic |
| --- | --- | --- | --- |
| A. Cohort day-spine (same template as personal channels) | HQ Emails `15`, Samples `17`, Speaker `14`, FTP `19` | `HCP_COHORT_ID` (BHID) at anchor date | `I01` lookback → daily spine → rolling SUM → anchor row |
| B. Monthly panel | Digital `24` | `NPI_NUMBER × SVC_DT_M` (all months) | Helper `step2_fill_missing` / `step3_lag`, windows 1/3/6 months, no cohort key |
| C. Geographic panel | DTC `34` | `DMA_Code × DATA_MONTH` (all months) | No windows, no cohort, raw monthly totals |

Strategic implication: the combine step (`99_Combine_Physician_Data_Promotional&Acc`) has to reconcile three keys (BHID, NPI, DMA) and two time conventions (anchor date vs calendar month). Any 3.1 redesign that unifies these needs to keep the combine-step mapping logic in view.

All Architecture A notebooks read cohort `I01` from `ops_pipeline/notebook_output/promotional_cohort_inference_dates`. See risk X-1 on how this table's content changed between runs.

---

## 2. Channel Portfolio at a Glance

| # | Channel | Notebook | Source (current code) | Grain | Windows | Base feats | Output (Delta, `ops_pipeline/notebook_output/`) | Last interactive run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Digital / Paid Media | `24_Features_Digital` | `PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB` (via `sfOptionscdpread`) | NPI × month | 1, 3, 6 months | 3 pivots (CHANNEL, SRC_SYS_CD, TACTIC) × 4 metrics | `kerendia_nba_3_0_hcp_model_paid_search_features_for_inference` | 2026-04-29 |
| 2 | HQ Emails | `15_promotional_features_HQ_Emails` | `PHCDW.PHCDW_CDM.HCP_EMAIL_LIST` | BHID | **90d only** | dynamic pivot on `EVENTTYPE` | `kerendia_nba_3_hcp_model_hq_email_features_for_inference` | 2026-05-04 |
| 3 | DTC | `34_promotional_features_DTC` | `query_output/kerendia_nba_3_0_hcp_model_DirectBuys`, `..._social` (Delta) | DMA × month | none | 5 vendors × 2 metrics = 10 | `kerendia_nba_3_hcp_model_DTC_PROMOTION_for_inference` | 2026-07-31 |
| 4 | Samples | `17_promotional_features_samples` | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER` | BHID | 30–180d | 9 (quantity-based) | `kerendia_nba_3_hcp_model_samples_features_for_inference` | 2026-05-27 |
| 5 | Speaker Programs | `14_promotional_features_speaker_program` | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM` | BHID | 30–180d | 11 | `kerendia_nba_3_hcp_model_speaker_program_for_inference` | 2026-05-04 |
| 6 | FTP | `19_ftp_features` | `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP` (`USE_SLS='Y'`) | BHID (via NPI) | 30–180d | 1 (`TOTAL_RX_FTP`) | `kerendia_nba_3_hcp_model_ftp_features_v2_for_inference` | 2025-10-08 |

Observed volumes (last saved outputs):

* Digital: 3,218,056 raw NPI × month × channel × source × tactic rows from `2025-04-16`. HQ_EMAILS monthly reach 25k–73k NPIs.
* HQ Emails: 5,740,895 events, 191,020 BHIDs.
* Samples: 159,970 rows, latest `SMPLE_CALL_DT` = 2026-05-19. Observed names: `KERENDIA 10MG / 20MG / 40MG BRC`, `SAMPLING KIT BRC`, `SAMPLE HOUSING BOX BRC`, `PATIENT BROCHURES BRC`.
* Speaker: 10,766 attended rows in the I01 window.
* FTP: voucher claims `2021-01-13 → 2025-09-29` at the last run.
* DTC: monthly from 2023-01; output columns verified: `DTC_PROMOTION_{HEALTH_UNION|HEALTHLINE|SHARECARE|WEBMD|FB_AND_IG}_TOTAL_{IMPRESSIONS|CLICKS}`.

---

## 3. Cross-Cutting Risks

| ID | Risk | Evidence | Impact |
| --- | --- | --- | --- |
| X-1 | **The "inference" cohort table is mutable and was multi-cohort at times** | On the 2026-05-04 runs (HQ, Speaker, iRep), `promotional_cohort_inference_dates` displayed C01, C02, … rows. HQ cross-join went 5,740,895 → 149,263,270 rows (exactly ×26). On 2026-04-29 / 2026-05-27 runs it held only `I01`. | When multi-cohort, SQL is still bounded by the `I01` window, so non-I01 cohorts get **truncated or empty** event history. Outputs carry whichever cohorts were present. A shared path with two meanings is a silent-failure risk. |
| X-2 | Window lists differ by channel | HQ = 90 only; Samples/Speaker/FTP = 30–180; Digital = 1/3/6 months on a monthly panel | Feature names look aligned (`_IN_LAST_3_MONTH`) but Digital's "3 months" = 3 calendar-month rows, while others = 90 daily rows. |
| X-3 | Output contract varies | Samples and HQ keep `LOOKBACK_END_DATE`; Speaker drops it; FTP keeps `MONTH_ID` (not renamed to `SVC_DT`) and has no `BHID`; Digital/DTC have no cohort key | The combine step needs per-notebook special cases. |
| X-4 | Digital double-counts email channels | Digital keeps `HQ_EMAILS` and `IREP_EMAILS` channels / tactics; HQ (`15`) and iRep (`16`) features also exist | Same exposure enters the model twice from different sources with different definitions. |
| X-5 | `PULL_DT` type | String in 15/14/17/24/34, `DATE` in 19 | Minor contract inconsistency. |

---

## 4. Channel Deep Dives

### 4.1 Digital / Paid Media (`24_Features_Digital`)

**Logic:** Kerendia rows from `MMX_FNL_COMBINED_AGGR_TAB` (replaced the deprecated `_TEMP` table on 2025-04-29), month-level, `>= I01 LOOKBACK_START_DATE`, no upper bound. Channel standardization (`CALL→CALLS`, `HQ EMAIL→HQ_EMAILS`, `IREP EMAIL→IREP_EMAILS`, `SAMPLE→SAMPLES`); 14 named tactics + `OTHER_TACTIC` (Banner names collapsed to `BANNER_TACTIC`, `DocAlert`, `FormularyOne`); **`CHANNEL NOT IN ('CALLS','SAMPLES')` filter applied**. Three pivots × {DEEP, LIGHT, TOTAL engagement, EXPOSURE}; `DIGITAL_` prefix.

| ID | Risk | Evidence | Impact |
| --- | --- | --- | --- |
| LD-1 | No upper date bound | `DATE_TRUNC('MONTH', DATE_ACT) >= digital_start` only | Months after the anchor are in the panel; the combine step must pick the anchor month or leakage occurs. |
| LD-2 | Mixed base and lag columns | Tactic base columns are dropped; channel and source base columns (current month) are kept | Inconsistent feature family. Current-month columns behave like a `_IN_LAST_1_MONTH` duplicate. |
| LD-3 | Dynamic pivots | `pivot('CHANNEL' / 'SRC_SYS_CD' / 'TACTIC_NAME')` without a value list | Schema drifts when new channels or sources appear; a model expecting fixed columns breaks or silently gets zeros. |
| LD-4 | Partial windows at panel start | Panel starts at `I01` start; 6-month lag for the first months covers fewer months | Only an issue if non-anchor months are used. |
| LD-5 | `sfOptionscdpread` direct connector | Not `Get_Data_Snowflakes` | Separate credential path; UC migration must cover it. |

**Legacy vs 3.1:** legacy **has** the CALLS/SAMPLES filter and the channel/tactic standardization. Their absence in 3.1 (D-1, D-2 in the 3.1 file) is a **regression**, not an inherited gap. Port the legacy cell as-is.

### 4.2 HQ Emails (`15_promotional_features_HQ_Emails`)

**Logic:** `HCP_EMAIL_LIST` where `UPPER(EMAILPRODUCTTYPE) LIKE '%KERENDIA%'`, `BH_ID LIKE 'BH%'`, I01 window. `FLAG = 1`, pivot on `EVENTTYPE`, `TOTAL_<EVENTTYPE>` naming, 90-day window only.

| ID | Risk | Evidence | Impact |
| --- | --- | --- | --- |
| LH-1 | Dynamic pivot on `EVENTTYPE` | No value list | New event types create new columns; renamed types silently drop. |
| LH-2 | Cross-join volume | 149M rows when the cohort table was multi-cohort (X-1) | Cost and correctness both depend on X-1. |
| LH-3 | Only 90-day window | `last_i_days_list = [90]` | 3.1 vs 3.0 comparable only on `_IN_LAST_3_MONTH`. |

### 4.3 DTC (`34_promotional_features_DTC`)

**Logic:** DirectBuys (Health Union, Healthline, Sharecare, WebMD) and Social (FB+IG) Delta tables, each pivoted by `VENDOR` on `DMA_Code × MONTH` (`TOTAL_IMPRESSIONS`, `TOTAL_CLICKS`), then full-joined.

| ID | Risk | Evidence | Impact |
| --- | --- | --- | --- |
| LT-1 | **PulsePoint and TTD Display are loaded and pivoted but never merged** | `df_plsp_grouped`, `df_ttdDisplay_grouped` unused; merge = DirectBuys ⋈ Social only | Wasted compute; two DTC vendors silently excluded. Decide whether that is intended. |
| LT-2 | NULLs after full join | `na.fill(0)` happens before the join, not after | DMA-months present in one source only carry NULLs (e.g. FB+IG NULL for 2023-01). |
| LT-3 | No time window and no HCP key | DMA × month panel | The combine step must map HCP → DMA and pick the anchor month. The HCP→DMA mapping is the real feature definition and lives outside this notebook. |
| LT-4 | Upstream tables are snapshots | Inputs are `query_output` Delta tables, not live sources | Freshness depends on a separate load; no check in this notebook. |

**Legacy vs 3.1:** legacy output column is `FB_AND_IG` (verified in the saved output). Re-check the 3.1 T-2 finding (`FBANDIG`) against an actual 3.1 run before treating it as a bug.

### 4.4 Samples (`17_promotional_features_samples`)

**Logic (2025-12-19 source):** `SAMPLE_<category> = SMPLE_QTY` for 6 hard-coded categories, `OVERALL_SAMPLE` (all except brochures), `SAMPLE_DROPPED` / `SAMPLE_SHIPPED` (quantity, brochures excluded). 9 base × 6 windows = 54 features. Output is **inner-joined to the HCP universe** (`base_hcp_universe_for_inference` → `SOURCE_PROVIDER_BHID_NPI_MAPPING`).

| ID | Risk | Evidence | Impact |
| --- | --- | --- | --- |
| LS-1 | **Category list does not match the data** | List has `KERENDIA 10MG` / `20MG` (non-BRC), which do not exist in the data, and omits `KERENDIA 40MG BRC`, which does | `TOTAL_SAMPLE_10MG*` / `20MG*` are constant 0; 40 mg samples only appear inside `OVERALL_SAMPLE`. |
| LS-2 | Quantity only, no event flag | All features sum `SMPLE_QTY` | Bulk drops dominate; no "number of sample events". 3.1 adds FLAG + QTY (improvement). |
| LS-3 | `SELECT DISTINCT` on the sample row | Query | Identical same-day drops collapse. |
| LS-4 | Only notebook that filters to the HCP universe | Universe inner join | Different population from every other channel; combine-step left join hides this, but sparsity statistics are not comparable. |

### 4.5 Speaker Programs (`14_promotional_features_speaker_program`)

**Logic:** attended Kerendia events in the I01 window (**dynamic**, not hard-coded), `dropDuplicates()` before dropping `EVNT_ID`, format / type / topic flags, 11 aggregates × 6 windows (1 overall + 4 format + 2 type + 4 topic; `IN_OFFC_MEAL` is not aggregated).

| ID | Risk | Evidence | Impact |
| --- | --- | --- | --- |
| LSP-1 | **Event-type flags likely always 0** | `EVNT_TYP.isin("SPEAKER PROGRAMS")` / `"NON-SPEAKER PROGRAMS"` (upper case, plural); saved data shows `EVNT_TYP = "Speaker Program"` | `TOTAL_SPKR_EVNT_TYP_*` constant 0. Validate with a distinct-value query. |
| LSP-2 | `SPKR_EVNT_FMT_OTHER` tests `EVNT_TPIC_NM IS NULL` | Flag definition | Wrong column; inherited by 3.1 (SP-2). |
| LSP-3 | Naming break | `sum("SPKR_TOPIC_OTHER").alias("SPKR_TOPIC_OTHER")` (no `TOTAL_`) | Pattern-based column selection downstream misses it. |
| LSP-4 | `IN_OFFC_MEAL` flag computed but not aggregated | Commented in agg | Dead flag. |
| LSP-5 | Hard-coded topic lists | CKD / CVR / INTRO lists with deck codes | New decks fall to no bucket (OTHER only catches `Display/Exhibit` and NULL). |

**Legacy vs 3.1:** legacy uses the dynamic I01 window. The hard-coded `'2022-03-17'–'2025-04-16'` window in 3.1 (P0-2 in the 3.1 file) is a **regression**.

### 4.6 FTP (`19_ftp_features`)

**Logic:** voucher claims (`USE_SLS='Y'`). Every `ORGN_CLM_AUTH_NUM` whose net `DAY_SUPPLY = 0` (reversal fully offsets approval) is removed. NPI → BHID inner join (NBA 3.0 crosswalk). `TOTAL_RX_FTP = count(rows)` per day, six windows.

| ID | Risk | Evidence | Impact |
| --- | --- | --- | --- |
| LF-1 | Partial reversals counted as claims | Count of rows regardless of sign when net ≠ 0 | Reversal rows of partially reversed claims add +1 instead of −1. |
| LF-2 | **`keep_cols` typo** | `'LOOKBACK_END_MONTH'` instead of `'LOOKBACK_END_DATE'` | Works by accident (date column dropped after the anchor filter); fragile. |
| LF-3 | **Key not renamed** | Output has `HCP_COHORT_ID`, `MONTH_ID`, features, `PULL_DT`; no `SVC_DT`, no `BHID` | Breaks the shared contract; combine step needs special handling. |
| LF-4 | Reversal list collected to the driver | `toPandas()` → `isin(list)` | Scales poorly; use an anti-join. |
| LF-5 | NPI→BHID fan-out | Inner join on a non-unique NPI | One claim can count for several BHIDs. |
| LF-6 | Duplicate write cell; last run 2025-10-08 | Cells 36–37; metadata | Confirm job schedule. |

**Legacy vs 3.1:** 3.1 reads the **same view** with `USE_SLS = 'Y'` (columns aliased `PRSC_NPI`, `RX_FILL_DT`, `CLAIM_COUNT_NBR`) and also counts rows. The differences are a stricter reversal rule (net `DAY_SUPPLY <= 0` or net count `= 0`, via anti-join), an added `RUNNING_TOTAL_RX_FTP`, and the anchor date output as `PULL_DT`. Decide which reversal rule is correct.

---

## 5. Cross-Channel Consistency Matrix (Legacy)

| Attribute | Digital 24 | HQ 15 | DTC 34 | Samples 17 | Speaker 14 | FTP 19 |
| --- | --- | --- | --- | --- | --- | --- |
| Key | NPI + `SVC_DT_M` | HCP_COHORT_ID + SVC_DT + BHID | DMA + DATA_MONTH | HCP_COHORT_ID + SVC_DT + BHID | HCP_COHORT_ID + SVC_DT + BHID | HCP_COHORT_ID + **MONTH_ID** |
| Windows | 1/3/6 mo | 90d | none | 30–180d | 30–180d | 30–180d |
| SQL date bound | start only | start + end | none | none | start + end | none |
| Dynamic schema | yes (3 pivots) | yes (pivot) | yes (vendor pivot) | no | no | no |
| Universe filter | no | no | n/a | **yes** | no | no |
| `LOOKBACK_END_DATE` kept | n/a | yes | n/a | yes | no | no |
| Prefix | `DIGITAL_` | `TOTAL_` | `DTC_PROMOTION_` | `TOTAL_SAMPLE_` | `TOTAL_SPKR_` (one exception) | `TOTAL_RX_FTP` |

---

## 6. Legacy → NBA 3.1 Delta

| Channel | Kept in 3.1 | Fixed in 3.1 | Regressed in 3.1 | Inherited defect |
| --- | --- | --- | --- | --- |
| Digital | Pivots, `DIGITAL_` prefix, NPI grain | — | CALLS/SAMPLES filter and channel/tactic standardization removed (D-1, D-2) | Dynamic pivots, no upper bound |
| HQ Emails | Pivot logic | 6 windows | — | Dynamic `EVENTTYPE` pivot |
| DTC | DirectBuys + Social | — | Verify FB_AND_IG naming (T-2) | PulsePoint/TTD unmerged, NULLs after full join |
| Samples | Categories | FLAG + QTY, 20 base features | — | Verify 40 mg coverage |
| Speaker | Flags, topics | — | Hard-coded date window (P0-2) | FMT_OTHER bug, event-type case |
| FTP | Six windows | — | Different source and definition | NPI fan-out |

---

## 7. Prioritized Action Plan

**P0 — correctness / parity blockers**

* P0-1: Split the cohort tables: one immutable `I01` inference table and a separate training-cohort table (X-1). Add an assertion that the inference table has exactly one row.
* P0-2: Port the legacy Digital standardization + CALLS/SAMPLES filter into 3.1 (LD vs D-1/D-2).
* P0-3: Replace the hard-coded 3.1 Speaker window with the legacy dynamic window.
* P0-4: Run distinct-value checks for `EVNT_TYP` (LSP-1) and `UPPER_SMPLE_NM` (LS-1), then fix the lists.

**P1 — feature semantics**

* P1-1: Decide FTP definition (legacy voucher + reversal vs 3.1 claim count) and name features accordingly.
* P1-2: Decide whether HQ/iRep exposure comes from Digital or from the dedicated notebooks (X-4); drop the duplicate.
* P1-3: Decide on PulsePoint/TTD in DTC (LT-1); fill NULLs after the join (LT-2).
* P1-4: Freeze pivot value lists for Digital, HQ, DTC.

**P2 — contract / hygiene**

* P2-1: Same output contract everywhere: `HCP_COHORT_ID`, `BHID`, `SVC_DT`, features, `PULL_DT DATE`.
* P2-2: Fix FTP `keep_cols` typo and rename `MONTH_ID → SVC_DT`; remove the duplicate write.
* P2-3: Fix `SPKR_TOPIC_OTHER` alias; remove dead flags.
* P2-4: Add an upper date bound to Digital and FTP pulls.

---

## 8. Validation Checklist (Legacy vs 3.1 Parity)

* [ ] Inference cohort table has exactly one row (`I01`) at run time.
* [ ] Digital: no `CALLS` / `SAMPLES` columns; tactic columns match the 14 + OTHER list.
* [ ] HQ: event-type column set identical between legacy and 3.1.
* [ ] DTC: column list equals the 10 verified feature names; no NULLs after fill.
* [ ] Samples: `TOTAL_SAMPLE_10MG*`, `TOTAL_SAMPLE_20MG*` non-zero after the list fix; 40 mg represented.
* [ ] Speaker: `TOTAL_SPKR_EVNT_TYP_SPKR_PRGM_IN_LAST_*` non-zero.
* [ ] FTP: reversal-removed count ≤ raw count; one claim maps to one BHID.

---

## 9. Open Questions

1. Who writes `promotional_cohort_inference_dates`, and why did it hold multiple cohorts on 2026-05-04?
2. Were PulsePoint and TTD Display intentionally excluded from the 3.0 model?
3. Is FTP (`19`) still scheduled (last interactive run 2025-10-08)?
4. Which HCP→DMA mapping does the combine step use for DTC?
5. Should 3.1 keep Digital's monthly panel, or move Digital onto the cohort day-spine?
