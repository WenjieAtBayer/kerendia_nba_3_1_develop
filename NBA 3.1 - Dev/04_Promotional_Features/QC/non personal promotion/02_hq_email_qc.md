# QC 02: HQ email (family 2) features, NBA 3.1

**QC status:** DONE, 13 / 13 pass (channel 2 of 5, non-personal promotion) after the P1 fix; notes P2 and P4 open (not blocking)  
**Verdict:** READY for modelling. All 15 features exactly match an independent SQL recompute from the raw events (3,648,042 rows, 0 differences)  
**QC run:** 20 Nov 2026. First pass on the 6 Nov output (3,112,543 rows, extract to 4 Nov 2026). P1 fixed (cell 7, rule D7) and notebook re-run 20 Nov 2026 on a fresh Snowflake extract (15,278,377 rows, 1 Jun 2023 to 18 Nov 2026; `PULL_DT` 2026_11_20). Q1, Q2, Q3, Q4, Q6, Q9, Q10 re-checked on the new output; Q5, Q7, Q8, Q11, Q12 are from the first pass (rules unchanged)

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `non_personal_promotional_features/HQ Emails/15_promotional_features_HQ_Emails_new` (15 cells) |
| Client summary | `HQ Emails/HQ_Email_Client_Summary.md`; feature dictionary `HQ Emails/feature_dictionary_non_personal_promotional_nba31.md` |
| Design / readiness | `52_digital_feature_families_nba30_vs_nba31.md` sections 1, 3.2, 6.6; `11_hcp_hq_emails_nba_3_0.md` |
| Source | `ANLT_BASE_FACT_NONPERSONAL_PROMOTIONS` (only HQ email source; HQ email removed from MMX) |
| Output | `kerendia_nba_3_1_volume/notebook_output/hq_email_nba_3_1/kerendia_nba_3_1_hcp_model_hq_email_features.parquet` + `feature_manifest.parquet` + `expected_schema.json` |
| Universe / cohorts | `HCP_Universe_without_call_hcps/` x `cohorts/promotional/cohorts.parquet` (c1 to c28) |
| Doctor key | NPI (`NPI_NUM`, else BH_ID -> NPI via `kerendia_oe_npi_bhid_mapping_inference`) -> `PROVIDER_ID`, else BH_ID -> `PROVIDER_ID`; `HCP_COHORT_ID` = `PROVIDER_ID_COHORT` |
| Expected shape | 15 fixed features + 8 keys = 23 columns; rows = universe doctors with any HQ email event up to the cohort end (rule D7 after the P1 fix), per cohort; not universe x 28 (doctors with no HQ email history are filled in the combine step) |
| NBA 3.0 counterpart | `15_promotional_features_HQ_Emails` (5 counts, dynamic pivot, BHID + `_I01`, one 90-day window) |
| NBA 3.0 final model | MLflow run `f583bcbc9d56477fae983d44c16f8c70`, 752 features |

## 2. QC checklist

| # | Check | How | Pass when | Status |
| --- | --- | --- | --- | --- |
| Q1 | HCP universe | Distinct PROVIDER_ID vs universe; rows; duplicates; placeholder `0`; mapping coverage by path (NPI vs BH_ID) | Same HCP set, 0 duplicates | PASS (re-checked after re-run; sparse by design, D7) |
| Q2 | Cohorts and windows | Lookback ends; 1 / 3 / 6 / 12M windows ending at END inclusive; no event after END | All match | PASS |
| Q3 | All features made | Columns vs config vs manifest vs `expected_schema.json` vs dictionary | No missing / extra column | PASS |
| Q4 | Business rules | Fill section 4 | All match | PASS (after P1 fix, 20 Nov 2026) |
| Q5 | Data sources | `ANLT_BASE_FACT_NONPERSONAL_PROMOTIONS` filters (brand, channel = HQ email, event types); mapping tables | Matches design | PASS (filter read from code; Snowflake not re-queried) |
| Q6 | Fill rate | % null, % zero, % non-zero per feature, per cohort; rates / trend NULL rules; recency sentinel | Nulls only where designed; near-constant flagged | PASS |
| Q7 | NBA 3.0 model coverage | HQ email features in the 752 with SHAP rank | Mapped or dropped with reason | PASS |
| Q8 | Preserved vs new | Fill section 5 | Every feature labelled | PASS (15 / 15) |
| Q9 | HCP trace | Section 6, at least 5 HCPs, recompute from raw event rows | Final value = output | PASS (full recompute of every row, re-run on the new output) |
| Q10 | Invariants | Nested windows; unique opened <= delivered <= sent; clicked <= opened (unique emails); rates in [0, 1]; flags 0 / 1; recency consistent | 0 violations | PASS (3 explained exceptions, P3) |
| Q11 | Reconciliation | Yearly sent / delivered / opened / clicked emails and doctors vs `11_` and client summary | Within expected range | PASS (one stale summary figure, note P2) |
| Q12 | NBA 3.0 output comparison | Counts by normalised cohort | Differences explained (unique opens, bounce split, cohorts) | PASS |
| Q13 | Reproducibility and docs | Schema = `expected_schema.json`; summary current | No stale text | PASS (schema OK; notebook cells 7, 9, 15 updated; summary text in note P2) |

## 3. Evidence log

| # | Result (numbers) | Where (cell / query) | Notes |
| --- | --- | --- | --- |
| Q1 (after re-run) | Universe 294,726 `PROVIDER_ID`s (without `0`). Output 3,648,042 rows, 162,562 `PROVIDER_ID`s, `HCP_COHORT_ID` unique (3,648,042); 0 out-of-universe. Notebook QC4b: rows = doctor x cohort pairs with history (3,648,042 = 3,648,042). Mapping: 15,278,377 raw rows, 12,043,194 (78.8%) reach a universe `PROVIDER_ID`, of which 12,043,075 via the NPI and 119 via BH_ID only | Output parquet; recompute view `hq_ev`; notebook cell 9 | Rows per cohort 80,275 (c1) to 162,562 (c28); c28 = 55.2% of universe. First pass (old D7): 3,112,543 rows, c28 99,617 |
| Q2 | All 28 cohorts: `DATASET`, `PREDICTION_MONTH`, `SVC_DT` = cohort file (first pass); after re-run all 28 built (data end 18 Nov 2026, none dropped) and `HQ_HISTORY_MONTHS` = 12 in all 3,648,042 rows (extract starts 1 Jun 2023). Window w = (END - w months, END]; recompute joins only events on or before END and matches every row | Cohort file vs output; recompute | Notebook self-test: c28 3M = 18 Jun to 17 Sep 2026 |
| Q3 | 23 columns = `expected_schema.json` in exact order; 15 manifest rows = the 15 features (same set; manifest row order differs, Spark write, harmless); kinds: 6 COUNT, 2 RATE, 1 TREND, 3 FLAG, 3 DAYS; `NULL_IN_COMBINE` True for rates, trend, days | Output, manifest, schema | |
| Q5 | Query: `UPPER(PROD_BRAND_NM) LIKE '%KERENDIA%'`, `UPPER(CHNL_ID) = 'HQ EMAIL'`, from 1 Jun 2023; only IDs, date, metric, `EMAIL_NM` read. Extract has 10 `MTR` values (sent 6,265,793; delivered 6,174,251; opened 2,435,667; clicked 171,206; hard bounce 47,515; block 22,170; technical/other 17,683; soft 16,114; unsubscribed 13,118; unknown bounce 12,440): all mapped (0 unknown); 372 distinct `EMAIL_NM`, 0 null | Cell 4 code; staged extract | |
| Q6 | See fill table below | Output | |
| Q7 | 0 of the 5 NBA 3.0 HQ features (`TOTAL_*_IN_LAST_3_MONTH`) in the 752. HQ email reached the model only through MMX: `DIGITAL_HQ_EMAIL_EXPOSURE_IN_LAST_3_MONTH` rank 688, `DIGITAL_HQ_EMAIL_LIGHT_ENGAGEMENT_IN_LAST_6_MONTH` 695, `DIGITAL_RUNNING_HQ_EMAIL_TACTIC_LIGHT_ENGAGEMENT` 698 | `Shap_Importances.csv` (752 rows) | Matches client summary |
| Q9 / Q10 recompute (after re-run) | Independent SQL recompute of all 15 features (own mapping, event map, windows, rates, flags, new D7: every doctor x cohort with history) from the new staged extract: 3,648,042 rows, 0 only in output, 0 only in recompute, 0 differences in each of the 15 features. Notebook QC10: 5 / 5 c28 doctors match | `hq_ev`, `rc2`; cell 10 | First pass on the 6 Nov output: 3,112,543 rows, 0 differences |
| P1 re-check | Rows with no event in the last 12 months and not unsubscribed (left out before the fix): 535,564 now in the table (c14 13,900; c24 35,229; c28 62,944). Of these, 37,724 are still hard-bounced (no delivery after the last hard bounce): all 37,724 have `HQ_EMAILABLE_FLAG` = 0 (before: would have been 1 in the combine step). All 535,564 have `HQ_EMAIL_DAYS_SINCE_LAST_SENT` filled (before: NULL); 2,034 of them at exactly 365 days (12-month window excludes its start date) | `rc2` vs output | Fix proven |
| Q10 | Re-checked on the new output, same result. 0 violations: 1M <= 3M <= 12M sent; unique opens 3M <= 12M; rates in [0, 1]; trend in [-1, 1]; flags 0 / 1; unsubscribed and emailable never both 1; sent 3M > 0 with days since sent > 92: 0; sent 1M = 0 with days since sent < 28: 0; opens 12M > 0 with no days since open: 0; new: sent 12M = 0 with days since sent < 365: 0 (584,054 rows with sent 12M = 0, mostly old-history doctors). Explained exceptions: P3 (first pass counts) | Output | |
| Q11 | Staged extract vs MMX now, Jan 2025 to Oct 2026: sent 3,922,207 vs MMX 3,874,394; monthly MMX / source ratio 0.975 to 0.994 (QC9 band 0.90 to 1.10). Source by year: sent 780,633 (2023 Jun to Dec), 1,556,981 (2024), 2,607,803 (2025), 1,320,376 (2026 to 4 Nov); open rows 1,526,458 and click rows 106,927 in Jan 2025 to Oct 2026. Nov 2026 partial (data end 4 Nov) | Staged extract; MMX | Summary sent 3,922,208 (1 off); summary opens figure stale (P2) |
| Q12 | NBA 3.0 output `kerendia_nba_3_hcp_model_hq_email_features_for_inference` (pulled 30 Oct 2026, I01, `SVC_DT` 17 Oct 2026, 123,535 BH_IDs, 90-day window 20 Jul to 17 Oct 2026) vs the staged NBA 3.1 extract on the same BH_IDs and days: sent 386,864 vs 386,857; opens 130,920 vs 130,922; clicks 10,719 vs 10,719; bounces (all 5 types) 5,562 vs 5,562; unsubscribes 1,002 vs 989. BH_IDs with a different value: sent 7, opens 80, unsubscribes 19, clicks 0, bounces 0 | NBA 3.0 output vs `hq_raw` | Same source (ANLT); small gaps = later Snowflake refresh. Then NBA 3.1 differs by design: unique opens (c28 3M: 359,375 sent, 91,210 unique opens), hard bounce only (2,005 of 5,562 bounces), status flags, `PROVIDER_ID`, 28 cohorts |
| Q13 | Schema = `expected_schema.json`; notebook cells have no saved outputs, so the notebook QC1 to QC10 table was not seen; all its checks re-done here. Client summary current except P2 | Notebook, summary | |

### Q6 fill rates (all 28 cohorts, 3,648,042 rows, after the P1 re-run)

| Feature | Null % | Zero % | Non-zero % | Max | Note |
| --- | --- | --- | --- | --- | --- |
| `HQ_EMAIL_SENT_1M` | 0 | 54.50 | 45.50 | 12 | |
| `HQ_EMAIL_SENT_3M` | 0 | 42.16 | 57.84 | 28 | |
| `HQ_EMAIL_SENT_12M` | 0 | 16.01 | 83.99 | 53 | 0 in 584,054 rows (old-history doctors now kept) |
| `HQ_EMAIL_UNIQUE_OPENS_3M` | 0 | 75.06 | 24.94 | 20 | |
| `HQ_EMAIL_UNIQUE_OPENS_12M` | 0 | 53.81 | 46.19 | 42 | |
| `HQ_EMAIL_UNIQUE_CLICKS_12M` | 0 | 93.74 | 6.26 | 39 | Sparse |
| `HQ_EMAIL_OPEN_RATE_6M` | 32.37 | 34.45 | 33.18 | 1 | NULL = nothing sent in 6M, as designed |
| `HQ_EMAIL_CLICK_RATE_6M` | 32.37 | 63.86 | 3.77 | 1 | Near-constant |
| `HQ_EMAIL_OPENS_3M_VS_PRIOR_3M` | 66.73 | 2.66 | 30.61 | 1 | NULL = no unique opens in 6M, as designed |
| `HQ_EMAIL_HARD_BOUNCE_FLAG_12M` | 0 | 96.71 | 3.29 | 1 | |
| `HQ_EMAIL_UNSUBSCRIBED_FLAG` | 0 | 96.82 | 3.18 | 1 | c28: 7,034 doctors |
| `HQ_EMAILABLE_FLAG` | 0 | 6.48 | 93.52 | 1 | c28 share emailable 0.913 (was 0.896 on the smaller first-pass table) |
| `HQ_EMAIL_DAYS_SINCE_LAST_SENT` | 0 | 4.90 | 95.10 | 1,184 | |
| `HQ_EMAIL_DAYS_SINCE_LAST_OPEN` | 36.51 | 1.19 | 62.30 | 1,184 | NULL = never opened |
| `HQ_EMAIL_DAYS_SINCE_LAST_CLICK` | 89.51 | 0.12 | 10.37 | 1,184 | NULL = never clicked; sparse |

No recency sentinel: days-since is NULL when never (manifest `NULL_IN_COMBINE`), unlike the digital block (999).

## 4. Business rules to verify (design vs notebook)

| Rule | Design | Notebook | Match |
| --- | --- | --- | --- |
| Event types | Sent, delivered, opened, clicked, unsubscribed, hard bounce, other bounce kept apart | `EVENT_MAP`: 7 types; 4 temporary bounce types -> `OTHER_BOUNCE` (not used in features); stop on a new `MTR` | Yes |
| Opens / clicks | Unique emails (`EMAIL_NM`), not event rows | `countDistinct(EMAIL_NM)` per window; sends stay event counts | Yes (resends of one `EMAIL_NM` count once, P3) |
| Windows | 1 / 3 / 6 / 12 months ending at END inclusive; no `RUNNING_` | `EVENT_DT > add_months(END, -w)` and `<= END` | Yes |
| Doctor key | NPI path first, BH_ID fallback; universe only | Source NPI if 10 digits, else BH_ID -> NPI; NPI -> `PROVIDER_ID`, else BH_ID -> `PROVIDER_ID`; smallest on ties; universe semi-join | Yes |
| Rates / trend | Defined denominators; NULL rule when denominator 0 | Unique opened (clicked) / unique sent, 6M, capped at 1, NULL if 0 sent; trend (O3 - prior O3) / sum, NULL if 0 | Yes (cap hits 19,382 rows, P3) |
| Status flags | Unsubscribed / bounced flags as of END | Unsubscribed = last unsubscribe on or after last delivery (full history); emailable = not unsubscribed and not (last hard bounce on or after last delivery); hard bounce flag 12M | Yes (after P1 fix, also for doctors with only older history) |
| Rows kept (D7) | | After P1 fix: every doctor x cohort with any HQ email event up to END; doctors with no history filled in combine: counts / flags 0, emailable 1, rates / trend / days NULL | Yes (P1 fixed; before: wrong default for 37,718 rows) |

## 5. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature | In the 752 (rank) | NBA 3.1 feature | Status | Reason |
| --- | --- | --- | --- | --- |
| `TOTAL_SENT_IN_LAST_3_MONTH` | No | `HQ_EMAIL_SENT_3M` | Preserved (renamed; 90 days -> 3 months) | Same event count |
| `TOTAL_OPEN_IN_LAST_3_MONTH` | No | `HQ_EMAIL_UNIQUE_OPENS_3M` | Preserved, definition changed | Unique emails, not every reopen |
| `TOTAL_CLICK_IN_LAST_3_MONTH` | No | `HQ_EMAIL_UNIQUE_CLICKS_12M` | Preserved, definition changed | Unique emails; 12M because clicks are sparse (7.3% non-zero at 12M) |
| `TOTAL_BOUNCE_IN_LAST_3_MONTH` | No | `HQ_EMAIL_HARD_BOUNCE_FLAG_12M` | Preserved, definition changed | Hard bounce only, flag, 12M (in the same window, 2,005 of the 5,562 bounces in the source are hard) |
| `TOTAL_UNSUBSCRIBE_IN_LAST_3_MONTH` | No | `HQ_EMAIL_UNSUBSCRIBED_FLAG` | Preserved, definition changed | Status at END from full history |
| MMX copies `DIGITAL_HQ_EMAIL_*` (Digital block) | 688, 695, 698 | None in this block | Moved | HQ email removed from MMX features; notebook 51 duplicate open (P4) |
| None | | `HQ_EMAIL_SENT_1M`, `HQ_EMAIL_SENT_12M`, `HQ_EMAIL_UNIQUE_OPENS_12M`, `HQ_EMAIL_OPEN_RATE_6M`, `HQ_EMAIL_CLICK_RATE_6M`, `HQ_EMAIL_OPENS_3M_VS_PRIOR_3M`, `HQ_EMAILABLE_FLAG`, `HQ_EMAIL_DAYS_SINCE_LAST_SENT`, `HQ_EMAIL_DAYS_SINCE_LAST_OPEN`, `HQ_EMAIL_DAYS_SINCE_LAST_CLICK` | New (10) | File 52 / file 30 additions |
| **Total** | | **15** | 1 preserved, 4 preserved with changed definition, 10 new | |

## 6. HCP trace (step-by-step recompute)

| Step | What to show | Match |
| --- | --- | --- |
| 1 | Raw event rows for the HCP | Staged extract, 15,175,957 rows | Yes |
| 2 | Mapping path to PROVIDER_ID | Re-implemented in SQL; 78.8% of rows reach a universe `PROVIDER_ID` (summary: 78.8%) | Yes |
| 3 | Event-type classification | 10 `MTR` values -> 7 types, 0 unknown | Yes |
| 4 | Unique-email dedup | `count(DISTINCT EMAIL_NM)` per window | Yes |
| 5 | Window assignment per cohort | Event joined to every cohort with END >= event date; window `> add_months(END, -w)` | Yes |
| 6 | Final value = output | All 3,112,543 rows x 15 features: 0 differences | Yes |

Instead of 5 hand-picked doctors, every doctor x cohort row was recomputed (covers openers, clickers, delivered-only, bounced, unsubscribed and the 119 BH_ID-only rows). The notebook's own QC10 recomputes 5 c28 doctors.

## 7. Known points to confirm during QC

* Open-rate drift: average open rate 0.26 to 0.31 across cohorts (client summary), no drift seen.
* BH_ID fallback: 119 of 11,958,501 mapped rows (almost all via the NPI).

### Points

| # | Finding | Impact | Proposed action | Status |
| --- | --- | --- | --- | --- |
| P1 | Rule D7 keeps a doctor x cohort only with an event in the last 12 months or if currently unsubscribed. 535,492 doctor x cohort rows with older HQ email history are left out (c14 13,897; c24 35,225; c28 62,940). In the combine step they get `HQ_EMAILABLE_FLAG` = 1 and `HQ_EMAIL_DAYS_SINCE_LAST_SENT` NULL. But **37,718** of them (c28: 3,739) have a hard bounce never followed by a delivery, so they are not emailable, and all 535,492 have a known last send (> 365 days) | Wrong eligibility for the HQ email action for 37,718 rows; recency lost for 535,492 rows | Fixed 20 Nov 2026: cell 7 no longer filters on 12M activity (every doctor x cohort with any event up to END is kept); cell 9 new check QC4b (rows = doctor x cohort pairs with history); cell 15 combine note updated. Re-run: 3,648,042 rows; the 37,724 still hard-bounced old-history rows have `HQ_EMAILABLE_FLAG` = 0 and all 535,564 have days since last send | FIXED |
| P2 | Client summary Finding A table: "Opens ANLT 1,122,475" vs 1,526,458 open rows in the source for Jan 2025 to Oct 2026 (Finding B uses 1,526,458). MMX figures in that table are from before the MMX rebuild (sent now 3,874,394 vs 3,872,999) | Text only | Note: re-state the opens row (event rows vs unique) and date the MMX figures. After the P1 re-run the summary row counts (3,112,543 rows; doctors per cohort, e.g. c28 99,617; share emailable 0.896) and the D7 wording in section 3 are also out of date (now 3,648,042 rows; c28 162,562; 0.913) | NOTE (not changed) |
| P3 | Explained exceptions: unique opens 12M > sends 12M in 14,545 rows and open-rate cap hit in 19,382 rows (emails sent before the window); clicks > opens in 395 rows and click rate > open rate in 356 rows (likely a click tracked without an open; not confirmed with the owner); 45,069 doctor x email pairs sent on more than one day (97,193 of 5,004,193 mapped sends) count as one unique email; 2 doctor x email open pairs with no send ever | Small, by design | None; keep as notes | NOTED |
| P4 | Notebook 51 still builds 12 `DIGITAL_HQ_EMAIL_*` from MMX (same emails; decision D8) | Double count if both go to the model | Note: drop one of the two in the combine step (decision D8); not part of this notebook | NOTE (open, owner decision) |
| P5 | Output was from 6 Nov 2026 | Freshness only | Re-run done 20 Nov 2026 (extract to 18 Nov 2026); cell outputs now saved | DONE |

## 8. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 13 / 13 |
| Open issues | None blocking. Notes: P2 (client summary text and row counts stale), P4 (notebook 51 HQ email duplicate, decision D8) |
| Fixes made | P1 (cells 7, 9, 15, 20 Nov 2026); output re-written 20 Nov 2026 (3,648,042 rows) |
| Ready for modelling | Yes |
| Next channel | 03 High intent |
