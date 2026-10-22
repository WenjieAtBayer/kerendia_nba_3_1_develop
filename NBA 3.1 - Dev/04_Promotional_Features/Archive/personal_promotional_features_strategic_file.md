# Personal Promotional Features — Strategic File (Kerendia NBA 3.1)

**Scope:** Rep-driven (personal) promotional channels feeding the Kerendia NBA 3.1 HCP-level model  
**Folder:** `NBA 3.1 - Dev/04_Promotional_Features/`  
**Channels covered:** F2F Sales Rep Calls (`25`), iRep Emails (`16`), ClickStream / CLM (`18`)  
**Built from:** `personal-promotional-features` skill + line-by-line review of the three NBA 3.1 Dev notebooks + `EDA Promotion/promotional_features__nba_3_0_documentation.md`  
**Date:** October 22, 2026  
**Status:** Dev notebooks have been written but there is no execution output in the current session. Row, feature, and sparsity numbers below are the **NBA 3.0 / skill baseline** and still need to be re-checked after the first 3.1 run.

---

## 1. Strategic Role of Personal Promotion in NBA

Personal promotion is the channel set that the NBA engine **directly recommends and the field force directly executes**. That means these features do two jobs:

1. **Predictors**: they describe each HCP's recent rep-exposure history, which drives NBRx / TRx response.
2. **Levers**: the next-best-action output is expressed in these units ("one more F2F detail with sample", "send the CKD Screening iRep email"). The feature definitions therefore set the vocabulary of the recommendations.

Because of this, features in this family must be **actionable and attributable**. Every feature should map to something a rep can actually do, at a grain the field can follow.

| Channel | Business question answered | Lever type | Recommendation it supports |
| --- | --- | --- | --- |
| F2F Sales Rep Calls | How often, in what mode, and with what content/purpose was the HCP called on? | Primary lever | Call frequency, channel mix (F2F vs remote vs phone), sampling |
| iRep Emails | Did the rep follow up digitally, and with which approved content? Did the HCP engage? | Secondary lever / follow-up | Content selection (CKD screening, access, education, trial) |
| ClickStream / CLM | How deep was the in-call content engagement? | Quality modifier of calls | Call quality / content depth, not frequency |

---

## 2. Channel Portfolio at a Glance

| # | Channel | Notebook | Source | Base feats | Windows | Output cols | Ref. HCPs | Ref. sparsity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F2F Sales Rep Calls | `25_promotional_features_call` | `CPH_DB_PROD.MODEL_V2.FACT_CALL` + `MAP_CUSTOMER_XREF` | 35 (15 + 20 cross) | 6 (30–180d) | 212 | 129,787 | 94.3% |
| 2 | iRep Emails | `16_promotional_features_irep` | `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_IREP` | 14 (3 + 11 doc) | 6 (30–180d) | 86 | 79,627 | 97.2% |
| 3 | ClickStream / CLM | `18_promotional_ClickStream_features` | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM` + `FACT_CALL` | 4 | 6 (30–180d) | 26 | 18,804 | 67.2% |
| | **Total** | | | **53** | | **~324** | | |

Shared contract:

* **Key:** `HCP_COHORT_ID = {BHID}_{COHORT}` plus `SVC_DT` (= cohort `LOOKBACK_END_DATE`)
* **Cohorts:** `dev_folder/query_output/promotional_features_hcp_model_cohort_anchor_dates.csv` (C01–C26, 13-month lookback)
* **Output:** Parquet, overwrite, `dev_folder/notebook_output/kerendia_nba_3_hcp_model_{call|irep|clickstream}_features.parquet`
* **Null convention:** `fillna(0)` inside the spine. HCP-cohorts with no event in the lookback are **absent** from the output, so the combine step must fill them with 0 after the left join.

---

## 3. Shared Pipeline (Variant A — Day-Level Spine)

1. Pull raw events from Snowflake (`Get_Data_Snowflakes`, defined inline in each notebook; `00_connection` is not `%run`).
2. One-hot encode the dimensions into binary flags.
3. Cross-join with the broadcast cohort anchor dates, filter to `[LOOKBACK_START_DATE, LOOKBACK_END_DATE]`, and build `HCP_COHORT_ID`.
4. Aggregate to `HCP_COHORT_ID × day` (SUM, or AVG for ClickStream averages).
5. `step2_fill_missing_dates`: dense daily spine of about 395 rows per HCP-cohort, then `fillna(0)`.
6. `step3_lag_date`: `rowsBetween(-i+1, 0)` rolling SUM for i ∈ {30, 60, 90, 120, 150, 180}, producing `_IN_LAST_{1..6}_MONTH`.
7. Keep only the anchor row (`MONTH_ID == LOOKBACK_END_DATE`), keep only the `_IN_LAST_*` columns, and rename `MONTH_ID` to `SVC_DT`.

**Strategic observation: the spine is over-built.** Only the anchor row is kept, and the widest window is 180 days. Days older than `LOOKBACK_END_DATE − 179` add nothing to the output, yet the spine carries all 395 days. This is the main cost driver (about 1.3B spine rows for Calls). See Recommendation P1-4.

---

## 4. Channel Deep-Dives

### 4.1 F2F Sales Rep Calls (`25_promotional_features_call`)

**Strategic role:** This is the core field-force lever and the highest-dimensional personal channel. It is the most likely anchor for NBA "call" recommendations.

**Source and filters (as implemented):**

* `FACT_CALL A LEFT JOIN MAP_CUSTOMER_XREF B ON SOURCE_CUST_ID`
* `UPPER(STAT) = 'SUBMITTED_VOD'`, `UPPER(DETL_PROD) = 'KERENDIA'`, `BAYER_CUST_ID NOT LIKE '%BHO%'`, `BAYER_CUST_ID IS NOT NULL`. The NOT NULL condition turns the LEFT JOIN into an effective INNER join, which is intended.
* There is no explicit date filter in SQL. The cohort-window filter removes out-of-range dates, including the known bad `2107` `CALL_DATE` values.

**Feature design (35 base features × 6 windows = 210 features):**

| Dimension | Flags | Notes |
| --- | --- | --- |
| Channel (from `CALL_REC_TYP_NM`) | `F2F`, `PHONE`, `GROUP_CALL`, `REMOTE_CALL` | Any other record type falls through the CASE and is not flagged |
| Call type (`CALL_TYP`) | `DETAIL_ONLY`, `DETAIL_WITH_SAMPLE`, `GROUP_DETAIL`, `GROUP_DETAIL_WITH_SAMPLE`, `EVENT_DETAIL` | Exact-case Veeva values |
| Call purpose (`CALL_PURPS`) | `PROMOTIONAL_ACTIVITY`, `…_WITH_MEAL`, `EVENT_RELATED_…`, `NON_PROMOTIONAL_ACTIVITY`, `MISCELLANEOUS` | See risk C-2 |
| Duration | `CALL_DURATION` | Safe cast: empty string or NULL becomes 0, negative becomes 0 |
| Cross-products | 4 channels × 5 call types = 20 `{CH}_AND_{CT}` | `least()` works as a row-level AND; batched with `.withColumns()` |

**Strengths in the 3.1 Dev notebook:**

* The cross-product loop uses `.withColumns({})`, which removes the RecursionError risk.
* `CALL_DURATION` uses the empty-string-safe cast (about 45% empty strings, about 10% NULL).
* The 3.0 inference version used a single 90-day window. 3.1 restores all six windows, so models can learn recency decay.

**Risks and gaps:**

| ID | Risk | Impact | Evidence |
| --- | --- | --- | --- |
| C-1 | **UC migration gap.** The new UC calls table `ker_lynkuet_calls_data` lacks `CALL_TYPE`, `CALL_REC_TYPE`, `CALL_PRPSE`, `CALL_DURATION`. | **Critical.** Without these columns, 34 of 35 base features (all except a total-call count) cannot be built. | NBA 3.1 migration notes (open item) |
| C-2 | **Call-purpose literals disagree between notebook and skill.** The notebook uses `"Event related Promotional Activity"` and `"Other non-promotional Activity"`; the skill documents `"Event Related …"` and `"Non-Promotional Activity"`. | Wrong literals produce zero-variance flags, and those rows fall into `MISCELLANEOUS` instead. | Notebook cell "Create Binary Flags" vs skill §4 |
| C-3 | **NULL purpose is not counted anywhere.** `~isin(...)` on a NULL returns NULL, which goes to `otherwise(0)`. | Calls with a NULL purpose disappear from the purpose dimension, so purpose totals do not equal channel totals. | Spark three-valued logic |
| C-4 | **Unmapped record types are silent.** Record types outside the four CASE branches keep their raw name and get no channel flag. | Those calls are undercounted in channel and cross-product features. | Calls query CASE `ELSE CALL_REC_TYP_NM` |
| C-5 | **No call-level de-duplication.** If `FACT_CALL` has more than one Kerendia detail row per `CALL_ID`, the call is counted more than once. | Inflated counts. | Query has no `DISTINCT` and no `CALL_ID` |
| C-6 | **No overall call count.** The total is only implied by summing the channel flags. | The model and NBA output lack a single "calls in last N months" feature. | Feature list |
| C-7 | **Feature redundancy.** Cross-products are often near-collinear with their parent flags (for example `F2F_AND_DETAIL_ONLY` vs `DETAIL_ONLY`). Six windows of cumulative sums are also strongly correlated. | 210 features with heavy multicollinearity, which makes SHAP / driver attribution unstable. | Design |

**Recommendations:**

* Resolve C-1 with the table owners before any UC cut-over. Until then, keep reading from Snowflake `FACT_CALL`.
* Profile `CALL_PURPS`, `CALL_TYP`, and `CALL_REC_TYP_NM` (`distinct().show(100, False)`), fix the literals, and add an explicit `UNMAPPED` / `NULL` bucket for each dimension.
* Add `CALL_ID` to the query and run `countDistinct(CALL_ID)` vs `count(*)` as a QC check. Add `TOTAL_CALLS` as an explicit base feature.
* Before modelling, prune the cross-products to combinations with at least 1% prevalence (`F2F × DETAIL_WITH_SAMPLE` is the most action-relevant one).

---

### 4.2 iRep Emails (`16_promotional_features_irep`)

**Strategic role:** Rep-initiated digital follow-up. The content categories are the channel's main strategic value, because they let NBA recommend **which message** to send and not just whether to send.

**Source and filters (as implemented):**

* `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_IREP` (schema `PHCDW_SANDBOX`). The view is Kerendia-specific, so there is no brand filter.
* `ACCT_IDNTFR NOT LIKE 'BHO%'`, `Email_Status = 'Delivered'`, `DATE_TRUNC('MONTH', EMAIL_SENT_DT) <= '2025-04-16'`
* Change from 3.0: 3.0 joined `FACT_SENT_EMAIL + DIM_APPROVED_DOCUMENT + MDM_STG_HCP_XREF/PRFL`. 3.1 uses the curated sandbox view, which is simpler but adds a dependency on a sandbox object.

**Feature design (14 base features × 6 windows = 84 features):**

| Dimension | Flags |
| --- | --- |
| Engagement | `IREP_EMAIL_DELIVERED_FLAG`, `IREP_EMAIL_CLICKED_FLAG`, `IREP_EMAIL_OPENED_FLAG` |
| Approved document (11) | `FDA`, `PSP_PRESCRIBING`, `BRANDED_ASSET`, `NATIONAL_BROADCAST`, `KIDNEY`, `INVITE`, `EDUCATION`, `BACC_ACCESS`, `EXCLUSIVE_BROADCAST`, `TRIAL`, `MISCELLANEOUS` |

**Risks and gaps:**

| ID | Risk | Impact |
| --- | --- | --- |
| I-1 | **Hard-coded end date `'2025-04-16'`.** NBA 3.1 cohorts anchored after April 2025 get **no iRep activity** in recent windows. | **Critical.** Recent windows are silently truncated to zero, so the feature behaves like a shifted proxy. |
| I-2 | **`DELIVERED_FLAG` is redundant with the filter.** All rows are already `Delivered`, so this flag equals the total emails sent. | Fine as a volume measure, but the name is misleading and there is no undelivered/bounce signal. |
| I-3 | **Doc-name coverage is about 42.5%.** 49 uncategorized `APPRVD_DOC_NM` values (PP-code and date-stamped BACC variants) map to no bucket. | About 57% of email volume has no content signal, which weakens content-level NBA recommendations. |
| I-4 | **Zero-variance legacy buckets.** `FDA`, `PSP_PRESCRIBING`, `BRANDED_ASSET`, `NATIONAL_BROADCAST` are all zero in the current data. | Dead features. Keep them for schema stability, but exclude them at training time. |
| I-5 | **Rates are missing.** Only counts exist; there are no open-rate or click-rate features (opened / delivered). | Counts mix volume with responsiveness. Rates separate HCP receptivity from rep effort. |

**Recommendations:**

* Replace the literal date with `max(LOOKBACK_END_DATE)` from the cohort file, following the ClickStream pattern.
* Rename the delivered flag to `IREP_EMAIL_SENT` in documentation, or add a cohort-level `IREP_OPEN_RATE` / `IREP_CLICK_RATE` downstream.
* Move to **pattern-based** content bucketing (for example `LIKE '%CKD%' OR LIKE '%Kidney%'`, `LIKE 'BACC%'`, `PP-KER-US-*` lookup) with the brand team, and add an `UNCATEGORIZED` bucket so total volume is preserved.
* Ask the sandbox view owner about SLA and refresh cadence. A sandbox view is a production risk.

---

### 4.3 ClickStream / CLM (`18_promotional_ClickStream_features`)

**Strategic role:** This channel measures **call quality, not quantity**: how long Kerendia CLM content was shown during a submitted call. It is most useful as an interaction with call frequency ("calls with content" vs "calls without"), not as a standalone lever.

**Source and filters (as implemented):**

* Source 1: `FACT_CALL ⋈ MAP_CUSTOMER_XREF` (submitted, Kerendia, non-BHO). Only `CALL_ID` and `CALL_STATUS` are kept; BHID is dropped.
* Source 2: `ANLT_BASE_FACT_CLKSTRM` with `BAYER_PROD_NM = 'KERENDIA'` and `date_id <= max(LOOKBACK_END_DATE)`. The upper bound is derived from the cohort file, which is the correct pattern.
* Dedup: `row_number()` per `CALL_ID` ordered by `USAGE_DUR DESC, PRESN_DUR DESC`, then INNER join to calls. Unmatched clickstream rows are dropped by design.
* **BHID comes from ClickStream (`BAYER_HCP_ID`)**, not from the call.

**Feature design (4 base features × 6 windows = 24 features, prefix `CLICKSTREAM_`):**

| Feature | Daily aggregation | Rolling operation |
| --- | --- | --- |
| `TOTAL_USAGE_DURATION` | SUM | SUM |
| `TOTAL_PRESN_DURATION` | SUM | SUM |
| `AVG_USAGE_DURATION` | AVG | **SUM** |
| `AVG_PRESN_DURATION` | AVG | **SUM** |

**Risks and gaps:**

| ID | Risk | Impact |
| --- | --- | --- |
| K-1 | **The AVG features are not averages.** `step3_lag_date` takes a rolling SUM of daily averages, so `AVG_USAGE_DURATION_IN_LAST_6_MONTH` is a "sum of per-day averages". It grows with the number of active days. | Mislabelled feature that is largely collinear with call frequency, and misleading in driver reports. |
| K-2 | **No CLM call count.** There is no count of calls with CLM content in the window. | A true average (total / count) and a "% of calls with content" ratio cannot be built. |
| K-3 | **BHID source mismatch.** The calls notebook keys on `MAP_CUSTOMER_XREF` BHID, while ClickStream keys on `BAYER_HCP_ID`. | A small number of HCPs may resolve to different BHIDs across the two channels. |
| K-4 | **Dedup keeps the max-duration row.** This is reasonable, but multi-presentation calls are reduced to one record. | Duration is conservative. Acceptable, but document it. |
| K-5 | **Text `DATE_ID`.** The Galaxy `DATE_ID` is a `YYYYMMDD` value compared as an integer in SQL and parsed with `to_date(cast string)`. | Works today. It breaks if the format changes during the UC migration. |

**Recommendations:**

* Add `CLM_CALL_COUNT` (count of distinct `CALL_ID`) as a base feature. Derive the true average as `TOTAL_*_DURATION / CLM_CALL_COUNT` after the rolling step, and drop or rename the current `AVG_*` features.
* Add a cross-channel ratio downstream: `CLM_CALL_COUNT / TOTAL_CALLS` (content penetration).
* Run a QC that compares the BHID from the call (`MAP_CUSTOMER_XREF`) with `BAYER_HCP_ID` for joined `CALL_ID`s.

---

## 5. Cross-Channel Consistency Matrix

| Aspect | Calls | iRep | ClickStream | Strategic note |
| --- | --- | --- | --- | --- |
| Date upper bound | None (cohort filter only) | **Hard-coded 2025-04-16** | `max(LOOKBACK_END_DATE)` | Standardize on the cohort-derived bound |
| ID resolution | `MAP_CUSTOMER_XREF` | `ACCT_IDNTFR` (view) | `BAYER_HCP_ID` | Three different BHID paths; align with the NBA 3.1 UC ID chain |
| Dedup | None | None | `row_number` per `CALL_ID` | Add `CALL_ID` dedup to Calls |
| Overall volume feature | Implicit | `DELIVERED` (= sent) | None | Add an explicit total for each channel |
| Unmapped bucket | MISC (not NULL-safe) | None | n/a | Add an `UNMAPPED` bucket everywhere |
| Rolling op on AVG | n/a | n/a | SUM (bug) | Fix as in K-1 |
| Windows | 6 | 6 | 6 | Consistent (3.0 inference used only 90d for Calls/iRep) |
| Write format | Parquet | Parquet | Parquet | Consistent |

**Documentation drift to clean up:** `promotional_features__nba_3_0_documentation.md` describes Calls and iRep as using a single 90-day window and BHO-prefixed outputs. 3.1 Dev uses six windows with no BHO prefix, and `13_promotional_features_bho_calls` is not carried into 3.1. Update the doc once the 3.1 design is frozen.

---

## 6. Migration (Snowflake to Unity Catalog) Implications

| Channel | Current source | UC status | Blocker |
| --- | --- | --- | --- |
| Calls | `FACT_CALL` + `MAP_CUSTOMER_XREF` | `ker_lynkuet_calls_data` exists | **Yes**: missing call type, record type, purpose, duration (C-1) |
| iRep | `VIEW_RB_KERENDIA_IREP` (sandbox) | Not yet mapped | Unknown; needs an owner |
| ClickStream | `ANLT_BASE_FACT_CLKSTRM` + `FACT_CALL` | Not yet mapped | Depends on Calls (`CALL_ID` join) |
| BHID mapping | `MAP_CUSTOMER_XREF` | `pha_hcp_demographics_np_pa_aligned_mar2026` (PROVIDER_ID → BH_ID) | Re-validate BHID overlap for promoted HCPs |

Recommendation: keep personal channels on Snowflake for the first NBA 3.1 run. Migrate only after C-1 is closed, then run old-vs-new parity checks on feature totals per cohort.

---

## 7. Prioritized Action Plan

| Priority | Action | Channel | Effort |
| --- | --- | --- | --- |
| **P0-1** | Replace the hard-coded `'2025-04-16'` with the cohort-derived max end date | iRep | XS |
| **P0-2** | Profile and fix the call-purpose / call-type / record-type literals; add NULL-safe `UNMAPPED` buckets | Calls | S |
| **P0-3** | Escalate the UC calls column gap (C-1) to the table owners | Calls / ClickStream | n/a |
| **P1-1** | Fix the ClickStream AVG semantics (K-1); add `CLM_CALL_COUNT` | ClickStream | S |
| **P1-2** | Add `CALL_ID` dedup QC and an explicit `TOTAL_CALLS` | Calls | S |
| **P1-3** | Expand iRep doc-name bucketing to pattern-based rules with an `UNCATEGORIZED` bucket | iRep | M |
| **P1-4** | Cut the spine to the last 180 days before the anchor, or replace spine + window with conditional sums (`SUM(CASE WHEN MONTH_ID > END − i THEN flag END)`); expected compute reduction of more than 50% | All | M |
| **P2-1** | Add rate and ratio features (iRep open/click rate, CLM penetration) | iRep / ClickStream | S |
| **P2-2** | Prune collinear cross-products and windows at training time (prevalence or correlation filter) | Calls | S |
| **P2-3** | Move `Get_Data_Snowflakes` and step2/step3 into shared helpers (`%run`), replacing inline copies | All | S |

---

## 8. Validation Checklist (First 3.1 Run)

* Row count, distinct HCPs, and % zeros per channel vs the 3.0 baseline (Section 2)
* Each output has exactly `HCP_COHORT_ID`, `SVC_DT`, and N × 6 `_IN_LAST_*` columns (212 / 86 / 26)
* Monotonicity: `X_IN_LAST_1 ≤ X_IN_LAST_2 ≤ … ≤ X_IN_LAST_6` for every SUM feature
* Purpose-sum equals channel-sum equals total calls, after the `UNMAPPED` fix
* iRep: non-zero activity in cohorts anchored after 2025-04 (confirms P0-1)
* Zero-variance column list per channel, logged rather than dropped
* Use the `promotional-features-qc-eda` skill / `EDA Promotion/promotional_features_qc` notebook for the standard QC

---

## 9. Open Questions for the Domain / Brand Team

1. Should `GROUP_CALL` / `EVENT_VOD` remain a personal call channel, or move closer to Speaker Programs?
2. What is the target bucketing for the 49 uncategorized iRep documents (especially the PP-KER-US codes)?
3. Should non-promotional calls be kept as a feature, or excluded from rep-exposure totals?
4. For NBA recommendations, which grain is actionable: channel × call type (20 cross-products), or channel + sampling only?
5. Who owns `PHCDW_SANDBOX.VIEW_RB_KERENDIA_IREP` in production, and is there a UC equivalent planned?
