# Non-Personal Promotional Features — Strategic File (Kerendia NBA 3.1)

**Scope:** Non-rep (non-personal) promotional channels feeding the Kerendia NBA 3.1 HCP-level model  
**Folder:** `NBA 3.1 - Dev/04_Promotional_Features/`  
**Channels covered:** Digital Engagement / MMX (`24`), HQ Emails (`15`), DTC Direct Buy + Meta/IG (`34`), Samples (`17`), Speaker Programs (`14`), Free Trial Program / FTP (`19`)  
**Built from:** `non-personal-promotional-features` skill + line-by-line review of the six NBA 3.1 Dev notebooks + `EDA Promotion/promotional_features__nba_3_0_documentation.md`  
**Date:** October 22, 2026  
**Status:** Dev notebooks have been written but there is no execution output in the current session. Volumes below are the **NBA 3.0 / skill baseline** and still need to be re-checked after the first 3.1 run.

---

## 1. Strategic Role of Non-Personal Promotion in NBA

Non-personal channels reach the HCP (or the HCP's market) **without a rep in the room**. In NBA they play three distinct strategic roles. Mixing these roles is the most common design error in this family.

| Role | Channels | How NBA should use it |
| --- | --- | --- |
| **Orchestrated levers**: HQ or marketing can trigger them for a named HCP | HQ Emails, Digital (HCP-targeted media), Speaker Programs (invitation) | Candidate actions in the recommendation set, alongside personal levers |
| **Rep-adjacent / conversion enablers**: fulfilment of access or trial | Samples, FTP | Predictors of near-term Rx conversion. FTP behaves partly like an **outcome**, so treat it carefully (see 4.6) |
| **Market-pressure context**: geography-level, not HCP-addressable | DTC Direct Buy, Meta/IG | Control variables only. They explain baseline demand and are **never** recommended per HCP |

---

## 2. Channel Portfolio at a Glance

| # | Channel | Notebook | Source | Grain / key | Pipeline variant | Windows | Output cols | Ref. entities | Ref. sparsity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Digital Engagement | `24_Features_Digital` | `PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB` | `NPI_NUMBER × SVC_DT_M` | B, monthly spine | 1, 3, 6 months | ~665–896 (drifts) | 402,250 NPIs | 99.1% |
| 2 | HQ Emails | `15_promotional_features_HQ_Emails` | `PHCDW.PHCDW_CDM.HCP_EMAIL_LIST` | `HCP_COHORT_ID` | A, daily spine | 30–180d (6) | 32 | 190,860 | 76.9% |
| 3 | DTC Direct Buy | `34_promotional_features_DTC` | Delta: `ops_pipeline/query_output/kerendia_nba_3_0_hcp_model_DirectBuys` | `DMA_Code × DATA_MONTH` | C, no windows | none | 8 | DMA | 36.9% |
| 4 | Meta / IG Ads | `34_promotional_features_DTC` | Delta: `ops_pipeline/query_output/kerendia_nba_3_0_hcp_model_social` | `DMA_Code × DATA_MONTH` | C, no windows | none | 2 | DMA | (with DTC) |
| 5 | Samples | `17_promotional_features_samples` | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER` | `HCP_COHORT_ID` | A, daily spine | 30–180d (6) | 122 | 35,546 | 84.1% |
| 6 | Speaker Programs | `14_promotional_features_speaker_program` | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM` | `HCP_COHORT_ID` | A, daily spine | 30–180d (6) | 68 | 17,151 | 96.9% |
| 7 | FTP | `19_ftp_features` | `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP` | `HCP_COHORT_ID` (NPI → BHID) | A, daily spine | 30–180d (6) + running | 9 | NPI → BHID | 80.7% |

**Three keys, three join contracts.** `HCP_COHORT_ID` (BHID-based) for channels 2, 5, 6, 7. `NPI_NUMBER + SVC_DT_M` for Digital. `DMA_Code + SVC_DT_M` for DTC, broadcast to HCPs via DMA → ZIP → HCP in `99_Combine_Physician_Data_Promotional&Acc`. Any change to one key affects only its own branch of the combine notebook.

---

## 3. Pipeline Variants

| Variant | Channels | Spine | Lag function | Anchor handling |
| --- | --- | --- | --- | --- |
| **A**: day-level | HQ Emails, Samples, Speaker, FTP | ~395 days per HCP-cohort | `step3_lag_date`, rolling SUM over rows [30…180] | Keep the row where `MONTH_ID == LOOKBACK_END_DATE` |
| **B**: month-level | Digital | Global min→max month × every NPI | `step3_lag`, rolling SUM over [1, 3, 6] rows | **No cohort snapshot**: every NPI-month is output |
| **C**: none | DTC, Meta/IG | n/a | n/a | Contemporaneous month |

**Strategic observations:**

* **Variant A spine is over-built.** Only the anchor row is kept and the widest window is 180 days, so 54% of the 395-day spine is dead weight (HQ Emails alone is about 1.96B spine rows). Conditional sums (`SUM(CASE WHEN MONTH_ID > END − i THEN flag END)`) give the same output with no spine.
* **Window semantics differ.** `_IN_LAST_1_MONTH` means 30 days in Variant A, but 1 calendar month **including the full anchor month** in Variant B. If the anchor is mid-month (for example `2025-04-16`) and Digital is joined on the anchor's month, up to about 2 weeks of **post-anchor** exposure leaks into the features. See D-4.

---

## 4. Channel Deep-Dives

### 4.1 Digital Engagement / MMX (`24_Features_Digital`)

**Strategic role:** This is the broadest non-personal signal: HCP-addressable paid media (banner, EHR, Doximity, DocNews, CTV, and others) with exposure vs engagement depth. It is the strongest candidate for an "omnichannel" NBA action, and also the biggest dimensionality and governance risk.

**As implemented in 3.1 Dev:**

* Connection is `sfOptionscdpread` via the Spark Snowflake connector, not `Get_Data_Snowflakes`.
* Filters: `UPPER(BRND_NM) = 'KERENDIA'`, `NPI_NUM IS NOT NULL`, `DATE_TRUNC('MONTH', DATE_ACT) >= min(LOOKBACK_START_DATE)`.
* Aggregated in SQL to `NPI × month × CHANNEL × SRC_SYS_CD × TACTIC_NAME` with SUMs of 4 metrics: `DEEP_ENGAGEMENT`, `LIGHT_ENGAGEMENT`, `TOTAL_ENGAGEMENT`, `EXPOSURE`.
* Triple pivot (CHANNEL / SRC_SYS_CD / TACTIC_NAME) with NULL-safe value lists, `CH_` / `SRC_` / `TAC_` prefixes, outer joins, then sanitization.
* Monthly spine, rolling [1, 3, 6], zero-variance columns dropped, `DIGITAL_` prefix applied with `.toDF()`, written as Parquet.

**Risks and gaps:**

| ID | Risk | Impact |
| --- | --- | --- |
| D-1 | **`CHANNEL NOT IN ('CALLS','SAMPLES')` filter is missing.** The skill and the 3.0 logic both exclude these channels; the 3.1 query does not. | **Critical: double counting.** Calls and samples enter Digital features and duplicate notebooks 25 and 17. |
| D-2 | **Channel and tactic standardization from 3.0 is missing.** 3.0 remapped `CALL→CALLS`, `HQ EMAIL→HQ_EMAILS`, `IREP EMAIL→IREP_EMAILS`, `SAMPLE→SAMPLES` and normalized 14 tactic labels. | Column names differ from 3.0, so downstream feature lists and driver mappings break. HQ / iRep email channels inside MMX also **overlap with notebooks 15 and 16**. |
| D-3 | **`prefix_pivot_cols` uses chained `.withColumnRenamed()` in a loop** (about 600 columns). | RecursionError or hang on Spark Connect (skill §12.7). The final prefix uses `.toDF()`; this one does not. |
| D-4 | **No cohort snapshot or anchor alignment.** Output is all NPI-months. Monthly windows include the whole anchor month. | Possible post-anchor leakage, and a different alignment from every other channel. |
| D-5 | **Zero-variance drop at feature-engineering time.** | The schema changes between runs (665 → 896 observed), so a trained model's feature list can fail at inference. This contradicts the "zero-variance is a training concern" principle used everywhere else. |
| D-6 | **Pivot explosion.** About 150 pivot values × 4 metrics × 3 windows. 99.1% sparse. | Low signal per column, plus SHAP noise. Most columns are not actionable at SRC_SYS_CD level. |
| D-7 | **Misleading output name** `…_paid_search_features.parquet` (legacy). | Confusing for consumers. |
| D-8 | **NPI grain** while the other channels use BHID. | An extra NPI → PROVIDER_ID / BHID hop in the combine step. NPIs with no mapping are silently lost. |

**Recommendations:**

* Restore the `CHANNEL NOT IN ('CALLS','SAMPLES')` exclusion and decide explicitly whether HQ EMAIL / IREP EMAIL stay in MMX or are excluded in favour of notebooks 15 and 16.
* Restore the 3.0 channel/tactic standardization maps so the schema stays comparable.
* Convert `prefix_pivot_cols` to `.toDF()`.
* Replace the run-time zero-variance drop with a **frozen feature whitelist** (versioned CSV). Missing columns are added as 0 and extra columns are logged.
* Reduce dimensionality: keep the CHANNEL and TACTIC pivots, and collapse SRC_SYS_CD to vendors above a prevalence threshold (an `OTHER` bucket covers the rest). Consider only `TOTAL_ENGAGEMENT` + `EXPOSURE` (Light = Total − Deep is redundant).
* Align to cohort anchors: snapshot at the anchor month, using the **prior complete month** when the anchor is mid-month.

---

### 4.2 HQ Emails (`15_promotional_features_HQ_Emails`)

**Strategic role:** A centrally orchestrated, low-cost lever that HQ can deploy at scale. The engagement funnel (sent → open → click, unsubscribe as negative) gives a direct read on HCP digital receptivity.

**As implemented:** `HCP_EMAIL_LIST`, `UPPER(EMAILPRODUCTTYPE) LIKE '%KERENDIA%'`, `BH_ID AS BHID`. Five event flags: `TOTAL_BOUNCE`, `TOTAL_CLICK`, `TOTAL_OPEN`, `TOTAL_SENT`, `TOTAL_UNSUBSCRIBE`. Variant A with 6 windows, giving 30 features + 2 keys.

**Risks and gaps:**

| ID | Risk | Impact |
| --- | --- | --- |
| H-1 | **No de-duplication.** Repeat opens and clicks of one email each count as events. | Engagement counts are inflated by a few heavy openers, and the signal skews toward "opened many times". |
| H-2 | **No NULL-BHID filter in the query.** Null BHIDs produce a NULL `HCP_COHORT_ID` that flows into the spine. | Junk rows. The 3.0 version filtered null BHIDs explicitly. |
| H-3 | **Counts without rates.** | Open and click rates separate receptivity from send volume. |
| H-4 | **Overlaps with MMX `HQ EMAIL`** (see D-2). | Collinear features across notebooks. |
| H-5 | **Window change from 3.0** (inference used only 90d; 3.1 uses six windows). | Not a bug, but the feature list is no longer comparable to 3.0. |

**Recommendations:** Count distinct emails (an email/campaign ID, if one is available) per event type. Add `BHID IS NOT NULL`. Derive `OPEN_RATE` / `CLICK_RATE` / `UNSUB_FLAG` at the anchor. Choose one source of truth for HQ email (this notebook vs MMX).

---

### 4.3 DTC Direct Buy + Meta / IG (`34_promotional_features_DTC`)

**Strategic role:** Market-level advertising pressure (Healthline, HealthUnion, ShareCare, WebMD, FB+IG) at DMA × month. **Not an HCP lever.** It controls for patient-pull demand so that personal-lever effects are not over-credited.

**As implemented:** Reads two Delta tables from `hcp_level_model/ops_pipeline/query_output/` (not the `notebook_output/*.delta` paths given in the skill). Renames `MONTH → DATA_MONTH`, pivots by vendor (`TOTAL_IMPRESSIONS`, `TOTAL_CLICKS`), sanitizes, adds the `DTC_PROMOTION_` prefix with `.toDF()`, outer-joins Direct Buy and Social, applies `fillna(0)`, and writes Parquet. This is the 3.0 doc's "not documented" notebook; it is now documented here and in the skill.

**Risks and gaps:**

| ID | Risk | Impact |
| --- | --- | --- |
| T-1 | **Dynamic vendor pivot.** Vendor values are collected at run time. | A new or removed vendor changes the schema silently. |
| T-2 | **Column-name drift vs the skill.** `sanitize_dtc` maps `+` to `and` with no underscores, so a vendor value `FB+IG` becomes `FBANDIG`, not `FB_AND_IG` as documented. | The combine step or model feature lists may not find the expected column. Verify against the actual `VENDOR` values. |
| T-3 | **Zero vs not-running is ambiguous.** `fillna(0)` after the outer join equates "no campaign" with "campaign, no impressions". | Acceptable for pressure, but document it. |
| T-4 | **Contemporaneous month** joined on `SVC_DT_M`. | Same mid-month leakage risk as D-4. |
| T-5 | **Upstream dependency on the ops-pipeline path** (`kerendia_nba_3_0_*`). | Refresh owner and cadence are unclear, and the data may be stale for 3.1. |
| T-6 | **PulsePoint / TTD display cells exist in 3.0 but were never executed.** | Scope decision still pending. |
| T-7 | **DMA broadcast.** Every HCP in a DMA gets the same value. | Effective sample size is about 210 DMAs, not hundreds of thousands of HCPs. Models can overfit to geography. |

**Recommendations:** Freeze the vendor list (config) and use `sanitize()` from notebook 24 for consistent naming. Lag DTC by one month (`SVC_DT_M − 1`) to remove leakage. Optionally add 3-month rolling pressure. Confirm the refresh owner of the ops-pipeline Delta inputs. In driver analysis, report DTC as a control and not as an actionable driver.

---

### 4.4 Samples (`17_promotional_features_samples`)

**Strategic role:** Samples are a strong conversion enabler and a rep-adjacent lever (dropped samples are executed by reps; shipped samples are requested remotely). Dose-level detail (10 / 20 / 40 mg) also signals titration intent.

**As implemented:** Single consolidated source (since 2025-12-19), `BHID` direct, `SELECT DISTINCT`. Dual FLAG + QTY for 7 sample names, 2 delivery statuses (`DROPPED` / `SHIPPED`), and overall, with `KERENDIA PATIENT BROCHURES BRC` excluded. That gives 20 base features × 6 windows = 120 features + 2 keys, built with `.withColumns({})`.

**Improvements over 3.0:** 3.0 had 9 QTY-only features and was missing `40MG_BRC`. 3.1 adds `FLAG` counts (number of sample events vs units) and the 40 mg BRC SKU.

**Risks and gaps:**

| ID | Risk | Impact |
| --- | --- | --- |
| S-1 | **`SELECT DISTINCT` can collapse legitimate duplicate rows** (same HCP, day, SKU, and qty on two calls). | Slight undercount. `SMPLE_CALL_NM` is selected (which partly protects against this) but is then unused. |
| S-2 | **Non-Kerendia / unknown SKU names** still count in `OVERALL`. Only brochures are excluded. | `OVERALL` can exceed the sum of named SKUs. Add an `OTHER` bucket to reconcile. |
| S-3 | **3.0 HCP-universe inner-join step dropped.** 3.0 restricted output to in-universe providers; 3.1 does not. | Larger output. Universe filtering now happens only in the combine step, which is acceptable if that is intended. |
| S-4 | **No null-BHID or null-date guard.** | Same as H-2. |
| S-5 | **Overlap with Calls `DETAIL_WITH_SAMPLE`.** | Collinearity. Keep both only if their correlation is below about 0.8. |

**Recommendations:** Keep `SMPLE_CALL_NM` in the DISTINCT key and drop it afterwards. Add `SAMPLE_*_OTHER`. Add null guards. Run a QC check that `OVERALL = Σ named + OTHER` and `DROPPED + SHIPPED = OVERALL`.

---

### 4.5 Speaker Programs (`14_promotional_features_speaker_program`)

**Strategic role:** Peer-to-peer education is a high-cost, high-impact lever. Attendance is a strong advocacy signal, and topic (CKD vs cardiorenal vs intro) maps to where the HCP is on the adoption curve.

**As implemented:** `ATND = 'ATTENDED'`, `PROD_BRAND_NM = 'KERENDIA'`, `EVNT_START_DATE BETWEEN '2022-03-17' AND '2025-04-16'`. Event format (5), event type (2, with the 3.0 `'SPEAKER PROGRAMS'` casing bug **fixed** to `'Speaker Program'`), and topic (4). That gives 11 base features × 6 windows = 66 features + 2 keys.

**Risks and gaps:**

| ID | Risk | Impact |
| --- | --- | --- |
| SP-1 | **Hard-coded date window `'2022-03-17'–'2025-04-16'`.** | **Critical.** Any NBA 3.1 cohort anchored after April 2025 loses all recent speaker attendance. |
| SP-2 | **`SPKR_EVNT_FMT_OTHER` tests `EVNT_TPIC_NM IS NULL`**, i.e. the **topic** column instead of the format column. | The format "other" bucket is semantically wrong and duplicates `SPKR_TOPIC_OTHER` (null part). |
| SP-3 | **`NON_SPKR_PRGM` uses `!=`.** NULL `EVNT_TYP` evaluates to NULL and then 0. | Null-type events fall in neither bucket. |
| SP-4 | **Topic coverage is about 50%.** 49 uncategorized topics (Dual Dilemma, HF/LVEF ≥ 40%, GDMT, asterisk variants). | Half of attendance carries no topic signal, and new HF-indication content is invisible, which matters for the NBA 3.1 indication-based universe. |
| SP-5 | **No dedup** (3.0 deduplicated raw attendance) and **no overall attendance count** (3.0 had `TOTAL_SPEAKER_PROGRAMS_ATTENDED`). | Possible double counting, and a missing headline feature. |
| SP-6 | **Column name drift.** The notebook uses `EVNT_START_DATE`; the skill documents `EVNT_STRT_DT`. | Verify against the source and update whichever is wrong. |

**Recommendations:** Derive the date window from the cohort file. Fix `FMT_OTHER` to `~EVNT_FMT.isin(known) OR EVNT_FMT IS NULL`. Make the type flags NULL-safe. Restore `dropDuplicates()` and `TOTAL_SPEAKER_PROGRAMS_ATTENDED`. Add pattern-based topic buckets (`CKD`, `CVR/HF`, `INTRO`, `GDMT`, `OTHER`) with brand input.

---

### 4.6 Free Trial Program / FTP (`19_ftp_features`)

**Strategic role:** FTP redemptions show that the HCP has **already written Kerendia** under a voucher. That makes this channel part promotion and part **outcome**. It is a powerful predictor and also the channel most at risk of **target leakage** when the target is NBRx / TRx.

**As implemented:** View columns are aliased (`PRSC_NPI`, `RX_FILL_DT`, `CLAIM_COUNT_NBR`). `MM/dd/yyyy HH:mm:ss` dates are parsed. Reversals are removed (groups with net `DAY_SUPPLY ≤ 0` or net count `= 0`, anti-join). NPI → BHID uses an **inner** broadcast join to the 3.0 mapping parquet. The pipeline counts `TOTAL_RX_FTP`, applies 6 windows plus `RUNNING_TOTAL_RX_FTP`, and outputs `PULL_DT` (not `SVC_DT`).

**Risks and gaps:**

| ID | Risk | Impact |
| --- | --- | --- |
| F-1 | **Target leakage / circularity.** FTP fills are Kerendia Rx. | If the label window overlaps the FTP window, or FTP Rx are counted in the target, the model learns "Rx predicts Rx". |
| F-2 | **`RUNNING_TOTAL_RX_FTP` is not lifetime.** It is computed inside the cohort spine, so it equals the sum since `LOOKBACK_START_DATE` (13 months). | Misnamed. It is effectively a 13-month window, and genuine first-FTP history is lost. |
| F-3 | **3.0 NPI→BHID mapping with an inner join.** Unmapped NPIs are dropped, and NPIs with multiple BHIDs are duplicated. | Coverage loss or inflation. The UC migration analysis shows the new 2-table chain resolves 93.2% proper BH_ID vs 83.1% in the old chain. |
| F-4 | **Key naming inconsistency.** `PULL_DT` here vs `SVC_DT` everywhere else (and `PULL_DT` means run date in 3.0 docs). | Combine-step confusion. |
| F-5 | **Sandbox view dependency** (`PHCDW_SANDBOX`). | Production risk, as with the iRep view. |

**Recommendations:** Confirm with modelling that FTP Rx are excluded from the target, or that the FTP window ends strictly before the label window. Rename `RUNNING_TOTAL` to `TOTAL_RX_FTP_IN_LOOKBACK`, or compute a real lifetime total from the raw claims before the cohort filter. Switch to the NBA 3.1 UC NPI → BH_ID mapping and assert one BHID per NPI. Standardize on `SVC_DT`.

---

## 5. Cross-Channel Consistency Matrix

| Aspect | Digital | HQ Email | DTC | Samples | Speaker | FTP |
| --- | --- | --- | --- | --- | --- | --- |
| Date bound | cohort min start | none | n/a | none | **hard-coded** | none |
| Null-key guard | NPI not null | **missing** | n/a | **missing** | none | inner join |
| Dedup | SQL group-by | **none** | n/a | DISTINCT | **none** | reversal logic |
| Overall total | via channel pivot | `TOTAL_SENT` | n/a | `OVERALL` | **missing** | `TOTAL_RX_FTP` |
| Unmapped bucket | n/a (dynamic) | n/a | n/a | **missing** | partial | n/a |
| Schema stability | **unstable** (ZV drop, dynamic pivot) | stable | **unstable** (dynamic pivot) | stable | stable | stable |
| Date key name | `SVC_DT_M` | `SVC_DT` | `DATA_MONTH` | `SVC_DT` | `SVC_DT` | **`PULL_DT`** |
| Loop-rename safety | **chained rename** | ok | `.toDF()` | `.withColumns` | ok | ok |

**Cross-notebook overlaps to resolve (collinearity / double counting):**

* Digital `CALLS` / `SAMPLES` channels vs notebooks 25 and 17 (D-1)
* Digital `HQ EMAIL` vs notebook 15, and Digital `IREP EMAIL` vs notebook 16 (D-2)
* Samples vs Calls `DETAIL_WITH_SAMPLE` (S-5)
* FTP vs Rx targets (F-1)

---

## 6. Migration (Snowflake to Unity Catalog) Implications

| Channel | Current source | Migration note |
| --- | --- | --- |
| Digital | `PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB` (via `sfOptionscdpread`) | Single wide source. Plan a parity check on the distinct CHANNEL / SRC / TACTIC lists |
| HQ Emails | `PHCDW_CDM.HCP_EMAIL_LIST` | `BH_ID` native; low risk |
| DTC | Delta in the UC volume already | No Snowflake dependency; confirm refresh owner |
| Samples | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER` | Consolidated table (2025-12-19); BHID native |
| Speaker | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM` | Verify the date column name (SP-6) |
| FTP | `PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP` + 3.0 NPI–BHID parquet | Move to the UC NPI → BH_ID chain (`mdm_stg_hcp_prfl` / `pha_hcp_demographics_np_pa_aligned_mar2026`) |

All Snowflake access continues through the team's `Get_Data_Snowflakes` helper (or `sfOptionscdpread` for Digital) until UC equivalents are signed off.

---

## 7. Prioritized Action Plan

| Priority | Action | Channel | Effort |
| --- | --- | --- | --- |
| **P0-1** | Restore `CHANNEL NOT IN ('CALLS','SAMPLES')` and the 3.0 channel/tactic standardization | Digital | XS |
| **P0-2** | Replace the hard-coded speaker date window with cohort-derived bounds | Speaker | XS |
| **P0-3** | Confirm FTP vs target separation (leakage review) with modelling | FTP | S |
| **P0-4** | Convert `prefix_pivot_cols` to `.toDF()` (RecursionError risk) | Digital | XS |
| **P1-1** | Fix `SPKR_EVNT_FMT_OTHER`, make type flags NULL-safe, restore dedup and the overall attendance count | Speaker | S |
| **P1-2** | Replace the run-time zero-variance drop and dynamic pivots with frozen, versioned feature whitelists (Digital + DTC) | Digital / DTC | M |
| **P1-3** | Align Digital and DTC to the cohort anchor (prior complete month; lag DTC by one month) | Digital / DTC | M |
| **P1-4** | Add null-BHID guards and dedup (HQ Emails, Samples) | HQ / Samples | S |
| **P1-5** | Switch FTP to the UC NPI → BH_ID chain; fix `RUNNING_TOTAL` semantics; rename `PULL_DT` → `SVC_DT` | FTP | S |
| **P2-1** | Replace the Variant A spine with conditional-sum windows (more than 50% compute saving) | HQ / Samples / Speaker / FTP | M |
| **P2-2** | Expand speaker topic buckets (HF, GDMT) aligned with the indication-based universe | Speaker | M |
| **P2-3** | Collapse SRC_SYS_CD long tail; drop `LIGHT_ENGAGEMENT` (= Total − Deep) | Digital | S |
| **P2-4** | Add rate features (HQ email open/click rate) | HQ Emails | S |
| **P2-5** | Rename the Digital output from `paid_search` to `digital_features` (coordinate with the combine notebook) | Digital | XS |

---

## 8. Validation Checklist (First 3.1 Run)

* Row count, distinct entities, and % zeros per channel vs the Section 2 baseline
* Digital: no column contains `CALLS` or `SAMPLES`; channel names match the 3.0 standardized labels; the column count is logged and diffed against the whitelist
* Speaker: non-zero attendance in cohorts anchored after 2025-04; `SPKR_EVNT_TYP_SPKR_PRGM` is non-zero-variance (casing fix confirmed)
* Samples: `DROPPED + SHIPPED = OVERALL`, and `Σ named + OTHER = OVERALL`
* FTP: NPI → BHID match rate and duplicate-BHID count; `RUNNING_TOTAL ≥ IN_LAST_6_MONTH`
* DTC: vendor list equals the expected 5; DMA count about 210; no NULL `DMA_Code`
* Monotonicity `IN_LAST_1 ≤ … ≤ IN_LAST_6` for every Variant A SUM feature
* Run the standard QC from the `promotional-features-qc-eda` skill / `EDA Promotion/promotional_features_qc`

---

## 9. Open Questions for the Domain / Brand Team

1. Should MMX `HQ EMAIL` / `IREP EMAIL` be the single source for email engagement, or should notebooks 15 and 16 be kept and those channels excluded from Digital?
2. Is FTP a promotional lever or an outcome for NBA 3.1, and is it excluded from the Rx target?
3. Which DTC vendors are in scope for 3.1 (PulsePoint / TTD)?
4. What is the target topic taxonomy for speaker programs now that HF is part of the indication-based universe?
5. Who owns the refresh of the `ops_pipeline/query_output` DTC Delta tables and the sandbox FTP view in production?
