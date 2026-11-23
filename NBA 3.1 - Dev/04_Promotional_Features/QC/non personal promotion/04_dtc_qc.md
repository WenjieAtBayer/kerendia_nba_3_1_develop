# QC 04: DTC market context (family 4) features, NBA 3.1

**QC status:** DONE (channel 4 of 5). 12 / 13 PASS; Q13 PARTIAL: client summary not updated for P4 / P5 (P6, docs only)  
**Verdict:** READY for modelling. Feature values match an independent recompute (0 differences in all 8 features). Open points are a constant feature (P2) and the social feed ending 22 Jun 2026 (P3): notes / questions, not errors  
**Final output:** written 23 Nov 2026 (`PULL_DT` 2026_11_23) on Facebook + Instagram and SA360 read from Snowflake that day; notebook checks QC1 to QC9 all PASS. All results below are on this output

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `non_personal_promotional_features/DTC/34_promotional_features_DTC` (15 cells after the doctor-table cell was added) |
| Client summary | `DTC/DTC_Client_Summary.md` |
| Design / readiness | `52_digital_feature_families_nba30_vs_nba31.md` sections 1, 3.4; `20_dtc_direct_buy_social_nba_3_0.md`; `21_dtc_data_findings_2024_2026_and_open_questions.md` |
| Sources | Facebook + Instagram (Funnel, DMA x day); SA360 DTC branded search (`KER_DTC_` campaigns, state x day), live from Snowflake; ACS 2020 adults 18+ |
| Outputs | `notebook_output/dtc_nba_3_1/`: `kerendia_nba_3_1_hcp_model_dtc_features.parquet` (doctor x cohort, for the combine step), `kerendia_nba_3_1_dtc_zip_features.parquet` (ZIP x cohort), `kerendia_nba_3_1_dtc_social_dma_features.parquet`, `kerendia_nba_3_1_dtc_search_state_features.parquet`, `feature_manifest.parquet`, `expected_schema.json` |
| Grain | Features are built by market (DMA for social, state for search) x cohort; the doctor table gives each doctor the values of their practice ZIP (MDM best-affiliation `HCP_ZIP`) |
| Cohorts | `cohorts/promotional/cohorts.parquet` (c1 to c28); complete calendar months on or before END |
| Expected shape | 8 fixed features (4 social at DMA, 4 search at state). Doctor table 8,252,328 rows = 294,726 doctors x 28, 20 columns |
| NBA 3.0 counterpart | `34_promotional_features_DTC` (10 dynamic-pivot columns, DMA x month) |
| NBA 3.0 final model | MLflow run `f583bcbc9d56477fae983d44c16f8c70`, 752 features |

## 2. QC checklist

| # | Check | Pass when | Final result | Status |
| --- | --- | --- | --- | --- |
| Q1 | Market and doctor universe | Every HCP ZIP has a row; 0 duplicates | ZIP table: 40,818 postal ZIPs x 28 = 1,142,904 rows, ZIP x cohort unique; every ACS postal ZIP (states + DC) has a row (QC4b). Doctor table: 8,252,328 rows = 294,726 x 28; 282,881 doctors have a practice ZIP, 280,676 (95.2%) match a DTC row; the other 2,205 with a ZIP are 2,181 in US territories (excluded by design) and 24 not in ACS | PASS |
| Q2 | Cohorts and windows | All match | Cohort month = last calendar month fully on or before END for all 28 cohorts (c1 -> May 2024, c28 -> Aug 2026). Social last complete month May 2026 (data to 22 Jun 2026), search Oct 2026 (data to 22 Nov 2026); later months NULL | PASS |
| Q3 | All features made | No missing / extra column | ZIP table 17 columns = `expected_schema.json`; manifest 8 features (4 social DMA, 4 search state); social table 5,880 rows (210 DMAs x 28), search 1,020 rows (51 states x 20); doctor table 20 columns | PASS |
| Q4 | Business rules | All match | All 6 rules in section 4 match (join after P1) | PASS |
| Q5 | Data sources | Matches design | FB + IG `FUNNEL_DATA_FACEBOOKADS_GEO_DMA` (`Bayer_Kerendia`, from 2024-01-01, 2,115,981 rows); SA360 `FUNNEL_DATA_NEW_SA360_REGION` (`KER_DTC_`, from 2025-01-01, 188,594 rows); ACS 2020 adults 18+ (251,961,127); direct buys, PulsePoint, TTD not read | PASS |
| Q6 | Fill rate | Nulls only where designed | NULL only before the data start or after the source's last complete month (section 3); both months-since features (almost) constant 0 (P2); social NULL in c26 to c28 (P3) | PASS |
| Q7 | NBA 3.0 model coverage | Mapped or dropped with reason | 9 NBA 3.0 DTC features in the 752 (ranks 32 to 632), all mapped or dropped with a reason (section 5) | PASS |
| Q8 | Preserved vs new | Every feature labelled | 2 NBA 3.0 features preserved in changed form as 3 NBA 3.1 features, 12 dropped, 5 new | PASS |
| Q9 | Market trace | Final value = output | Independent recompute from the raw daily rows: 0 differences in all 8 features (section 6) | PASS |
| Q10 | Invariants | 0 violations | 0 violations: 1M <= 3M, clicks <= impressions, no negative values, social months-since = 0 exactly when 1M impressions > 0, no DMA with NULL social in c1 to c25, ZIP / doctor value = its DMA / state value | PASS |
| Q11 | Reconciliation | Within expected range | FB + IG and SA360 yearly and monthly impressions and clicks match `21_` within rounding / late data (e.g. FB + IG 2025 41.71M vs 41.7M; SA360 2025 1.47M vs 1.47M) | PASS |
| Q12 | NBA 3.0 output comparison | Differences explained | NBA 3.0 `DTC_PROMOTION` vs raw FB + IG (Jan 2024 to May 2025): -2.8% impressions, -2.7% clicks (likely an earlier pull, not verified); the OE copy matches the raw rows exactly | PASS |
| Q13 | Reproducibility and docs | No stale text | Schema = `expected_schema.json`; notebook header updated. Client summary updated for P1 only: it still says DTC has no doctor key and does not mention the doctor table (P5) or the P4 rule (P6) | PARTIAL |

## 3. Final results

| Item | Result |
| --- | --- |
| Doctor coverage | 294,726 doctors: 280,676 (95.2%) get DTC values (7,858,928 rows); 11,845 have no MDM practice ZIP, 2,181 are in US territories, 24 have a ZIP not in ACS; unmatched rows are NULL |
| Hospital / PO-box ZIPs (P1) | Now covered: 4,397 doctors in 236 postal ZIPs that differ from their ZCTA (e.g. Cleveland Clinic 44195, UCSF 94143, UTSW 75390) take their ZCTA's DMA / state values |
| Markets | 210 DMAs, 51 states (incl. DC); 0 NULL DMA / state |
| Social (FB + IG) | Data to 22 Jun 2026, last complete month May 2026; May 2026 clicks re-estimated (only outlier month; median national CTR 0.604%); `Unknown` DMA name dropped (0.164% of impressions) |
| Search (SA360) | Data to 22 Nov 2026, last complete month Oct 2026; ran in every state every month (51 x 22 complete months, 0 state-months with 0 impressions) |
| Population scale | ACS 2020 adults 18+, deduplicated by ZCTA: 251,961,127; national check 32.324 vs 32.324 |

### Fill rates (final ZIP table, 1,142,904 rows; zero % and max over non-NULL rows)

| Feature | NULL % | Zero % of non-NULL | Max | NULL by cohort |
| --- | --- | --- | --- | --- |
| `DTC_SOCIAL_IMPRESSIONS_PER_1K_ADULTS_1M` | 10.714 | 0.014 | 241.36 | c26-c28 (cohort months Jun-Aug 2026, after the last complete social month May 2026) |
| `DTC_SOCIAL_IMPRESSIONS_PER_1K_ADULTS_3M` | 10.714 | 0.007 | 723.03 | c26-c28 |
| `DTC_SOCIAL_CLICKS_PER_1K_ADULTS_3M` | 10.714 | 0.088 | 4.518 | c26-c28 |
| `DTC_SOCIAL_MONTHS_SINCE_LAST_CAMPAIGN` | 10.714 | 99.986 | 4 | c26-c28 (P4); almost constant 0 elsewhere (P2) |
| `DTC_SEARCH_IMPRESSIONS_PER_1K_ADULTS_3M` | 35.714 | 0 | 3.784 | c1-c10 (search from Jan 2025; 3M window must be inside the data) |
| `DTC_SEARCH_CLICKS_PER_1K_ADULTS_1M` | 28.571 | 0 | 0.185 | c1-c8 |
| `DTC_SEARCH_CLICKS_PER_1K_ADULTS_3M` | 35.714 | 0 | 0.496 | c1-c10 |
| `DTC_SEARCH_MONTHS_SINCE_LAST_CAMPAIGN` | 28.571 | 100 | 0 | c1-c8; constant 0 elsewhere (P2) |

## 4. Business rules (design vs notebook)

| Rule | Design | Notebook | Match |
| --- | --- | --- | --- |
| Role | Control variable (market context), not a doctor action | Manifest `ROLE = CONTROL`, `FAMILY = 4_DTC` for all 8 | Yes |
| Sources | FB + IG (DMA x day) and SA360 branded search (state x day) only | Cells 5-6: Funnel FB DMA table (`Bayer_Kerendia`) and SA360 region table (`KER_DTC_`); nothing else read | Yes |
| Months | Complete calendar months on or before END | `last_complete_month()` + cohort month rule; recompute same (Q2) | Yes |
| Scale | Per 1,000 adults (ACS 2020, 18+) | ZCTA-deduplicated adults, 251,961,127; QC6 national check 32.324 vs 32.324 | Yes |
| Gaps | Dense calendar: no campaign = 0; after last complete source month = NULL | `market_features()`; Q6 NULL pattern exactly c26-c28 (social), c1-c8 / c1-c10 (search) | Yes |
| Join | ZIP -> DMA / state; doctor's ZIP | Postal ZIP -> its ZCTA's DMA / state; doctor table uses the MDM practice ZIP (Q1) | Yes (after P1, P5) |

## 5. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature | In the 752 (rank) | NBA 3.1 feature | Status | Reason |
| --- | --- | --- | --- | --- |
| `DTC_PROMOTION_FB_AND_IG_TOTAL_IMPRESSIONS` | 124 | `DTC_SOCIAL_IMPRESSIONS_PER_1K_ADULTS_1M`, `_3M` | Preserved (changed) | Same source; per 1,000 adults, complete months, 1M / 3M windows |
| `DTC_PROMOTION_FB_AND_IG_TOTAL_CLICKS` | 93 | `DTC_SOCIAL_CLICKS_PER_1K_ADULTS_3M` | Preserved (changed) | Same; May 2026 clicks re-estimated (outlier) |
| `DTC_PROMOTION_HEALTH_UNION_TOTAL_IMPRESSIONS` / `_CLICKS` | 32 / 392 | none | Dropped | Zero after Jan 2025 (NBA 3.0 table); only marks the old period |
| `DTC_PROMOTION_WEBMD_TOTAL_IMPRESSIONS` / `_CLICKS` | 107 / 431 | none | Dropped | Trace only since 2025 (`21_` 4.4) |
| `DTC_PROMOTION_SHARECARE_TOTAL_IMPRESSIONS` / `_CLICKS` | 283 / 559 | none | Dropped | Stopped (`21_` 3, 4.4) |
| `DTC_PROMOTION_HEALTHLINE_TOTAL_IMPRESSIONS` / `_CLICKS` | 632 / not in 752 | none | Dropped | Last real month Jan 2023 (`21_` 3) |
| `DTC_PROMOTION_PULSE_POINT_TOTAL_IMPRESSIONS` / `_CLICKS` | not in 752 | none | Dropped | Nothing since Sep 2024 (`21_` 3) |
| `DTC_PROMOTION_THE_TRADE_DESK_DISPLAY_TOTAL_IMPRESSIONS` / `_CLICKS` | not in 752 | none | Dropped | Nothing since Dec 2023 (`21_` 3) |
| none | | `DTC_SOCIAL_MONTHS_SINCE_LAST_CAMPAIGN` | New | Recency of social pressure |
| none | | `DTC_SEARCH_IMPRESSIONS_PER_1K_ADULTS_3M`, `DTC_SEARCH_CLICKS_PER_1K_ADULTS_1M`, `_3M`, `DTC_SEARCH_MONTHS_SINCE_LAST_CAMPAIGN` | New | SA360 patient branded search by state (never in NBA 3.0) |

## 6. Independent recompute (final output)

All markets instead of 5: independent pandas recompute of the 8 features from the raw daily Snowflake rows (2,115,981 FB + IG rows, 188,594 SA360 rows) with its own DMA-name match, ZCTA population, dense calendar, complete-month windows and outlier rule.

| Table | Scope | Result |
| --- | --- | --- |
| Social DMA / search state | 5,880 + 1,020 rows, 8 features | 0 rows only on one side, 0 differences |
| ZIP table | 1,142,904 rows | Every row = its DMA / state values; every postal ZIP row = its ZCTA's row (1,142,876 pairs): 0 differences |
| Doctor table | 7,858,928 matched rows | = ZIP table values, 0 differences in all 8 features; unmatched rows NULL |
| Social months-since after P4 | Social table, 5,880 rows | NULL exactly in c26 to c28; = 0 exactly when 1M impressions > 0 in c1 to c25 (0 violations) |

The full market recompute was run before P4 / P5; P4 only changes `DTC_SOCIAL_MONTHS_SINCE_LAST_CAMPAIGN` in c26 to c28, checked directly (last row).

## 7. Fixes applied and notes

| # | Problem found | Fix | Final result | Status |
| --- | --- | --- | --- | --- |
| P1 | ZIP table was keyed on ZCTA, so hospital / PO-box postal ZIPs had no row: 4,397 doctors in 236 ZIPs got NULL for all 8 features | Cells 1, 4, 8, 9: ZIP list built from the ACS postal ZIPs, each taking its ZCTA's DMA / state (ZCTA kept for population only); new check QC4b | 40,818 ZIPs x 28 = 1,142,904 rows; every ACS postal ZIP has a row; 280,676 doctors covered (+4,397) | FIXED |
| P4 | Social months-since was 1, 2, 3 for all DMAs in c26 to c28 only because the FB + IG feed ends, which would mark the testing / holdout period | Cell 7: months-since NULL when the cohort month is after the source's last complete month (same rule as the volume features); new check QC4c | NULL exactly in c26 to c28; 0 violations | FIXED |
| P5 | No doctor-level DTC table for the combine step | New cell writes `kerendia_nba_3_1_hcp_model_dtc_features.parquet`: practice ZIP = MDM best-affiliation `HCP_ZIP` via BH_ID; 12 keys (incl. `ZIP5`, `DMA_CODE`, `STATE_NAME`, `DTC_ZIP_MATCHED`) + 8 features; placeholder doctor `0` dropped; checks QC7 to QC9 | 8,252,328 rows, 95.2% of doctors matched, matched rows = ZIP table values | ADDED |
| P2 | Both months-since features are (almost) constant: search 0 in every non-NULL row (SA360 ran in every state every month); social 0 in 99.986% of non-NULL rows | None; drop in feature selection or keep for schema stability | | NOTE |
| P3 | FB + IG data ends 22 Jun 2026 (unchanged at 23 Nov), so all 4 social features are NULL for c26 (testing) and c27 to c28 (holdout) | DTC team to confirm whether the campaign stopped or the feed is late | Train / test mismatch for the social features | OPEN (question) |
| P6 | Client summary `DTC_Client_Summary.md` updated for P1 only: it still says DTC has no doctor key and does not mention the doctor table (P5) or the P4 rule | Update the summary to the final run | | OPEN (docs) |

## 8. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 12 / 13 (Q13 PARTIAL: client summary not updated for P4 / P5, P6) |
| Fixes made | P1 (ZIP table keyed on postal ZIP, check QC4b), P4 (social months-since NULL after the data end, check QC4c), P5 (doctor x cohort table, checks QC7 to QC9); final output written 23 Nov 2026 |
| Open issues | P3 question (FB + IG data ends 22 Jun 2026: social NULL for c26 to c28); P6 (client summary, docs only). Note for modelling: P2 (both months-since features (almost) constant 0) |
| Ready for modelling | Yes |
| Next channel | 05 OE |
