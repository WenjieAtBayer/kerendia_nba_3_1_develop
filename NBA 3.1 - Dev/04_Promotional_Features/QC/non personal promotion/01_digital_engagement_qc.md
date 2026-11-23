# QC 01: Digital engagement (HCP paid media, family 1) features, NBA 3.1

**QC status:** DONE, 13 / 13 PASS (channel 1 of 5, non-personal promotion)  
**Verdict:** READY for modelling. One question to the MMX owner is open (P5, identical rows); the answer could change exposure volumes, not engagement  
**Final output:** written 20 Nov 2026 on the current MMX (rebuilt 19 Nov 2026), placement dictionary `0cd3298cbf` (44 rules). All results below are on this output

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `non_personal_promotional_features/Digital_Engagement/24_Features_Digital_NBA31` (13 cells) |
| Client summary | `Digital_Engagement/Digital_Engagement_Features_Client_Summary.md` |
| Design / readiness | `52_digital_feature_families_nba30_vs_nba31.md` section 3.1 (Family 1); `50_digital_nba_3_1_readiness_plan.md` |
| Source | UC `kerendia_oe_journey.mmx_fnl_combined_aggr_tab` (copy of Snowflake `MMX_FNL_COMBINED_AGGR_TAB`) |
| Output | `{V31}/notebook_output/digital_engagement_nba_3_1/kerendia_nba_3_1_hcp_model_digital_paid_media_features.parquet` (+ `feature_manifest.parquet`, `expected_schema.json`, `placement_dictionary.parquet`, `unmapped_report.parquet`, `_stage_paid_media_monthly.parquet`) |
| Universe / cohorts | `HCP_Universe_without_call_hcps/` x `cohorts/promotional/cohorts.parquet` (c1 to c28) |
| Doctor key | NPI (10-digit only) -> `PROVIDER_ID` via `SOURCE_PROVIDER_BHID_NPI_MAPPING` |
| Shape | 8,252,328 rows x 152 columns (8 keys + 144 features) |
| Config | `DIGITAL_DATA_START` 2025-01-01; windows 1 / 3 / 6 / 12 months; `RECENCY_SENTINEL` 999; `TREND_MIN_HISTORY` 6; `UNMAPPED_ALERT_SHARE` 1% |
| NBA 3.0 counterpart | `03_HCP_Level_Features/24_Features_Digital` (684 dynamic columns, NPI x month, cohort I01) |
| NBA 3.0 final model | MLflow run `f583bcbc9d56477fae983d44c16f8c70`, 752 features, `Shap_Importances.csv` |

## 2. QC checklist

| # | Check | Pass when | Final result | Status |
| --- | --- | --- | --- | --- |
| Q1 | HCP universe | Same HCP set, 0 duplicates | 294,726 doctors = universe without placeholder `0`; 8,252,328 rows = 294,726 x 28; 0 duplicate (PROVIDER_ID, COHORT) | PASS |
| Q2 | Cohorts and windows | All match | `SVC_DT`, `PREDICTION_MONTH`, `DATASET` match the cohorts file for all 28 cohorts; windows `(END - w months, END]`; nothing after END. `DIGITAL_HISTORY_MONTHS` 0 for c1 to c8, 12 from c20 (c8 has partial-month data, see P2) | PASS |
| Q3 | All features made | No missing / extra column | 144 features = manifest = `expected_schema.json` (152 columns, same order); no `RUNNING_` column | PASS |
| Q4 | Business rules | All match | All 8 rules in section 4 match (after P1 and P7) | PASS |
| Q5 | Data sources | Matches design | MMX UC table; brand `LIKE '%KERENDIA%'`; paid media only (banner, 3rd-party email, custom); 10-digit NPI; 0 unmapped placements | PASS |
| Q6 | Fill rate | Nulls only where designed; near-constant flagged | NULLs only in the 7 rate and 3 trend features; 9 placement engagement features always 0 (section 3) | PASS |
| Q7 | NBA 3.0 model coverage | Mapped or dropped with reason | 9 digital features in the NBA 3.0 752: the 4 paid-media banner exposure features (ranks 68, 151, 200, 644) are mapped (section 5); the other 5 are HQ / iRep email (other families) | PASS |
| Q8 | Preserved vs new | Every feature labelled | 144 / 144 labelled: 9 preserved, 9 preserved with changed definition, 6 replace `RUNNING_`, 120 new | PASS |
| Q9 | HCP trace | Final value = output | All 294,726 c28 HCPs x 12 window features vs raw recompute: 0 differences | PASS |
| Q10 | Invariants | 0 violations | 56 rules (window nesting, channel and placement sums = totals, engagement <= exposure everywhere, rates, recency, trend): 0 violations. Days since last engagement < days since last exposure in 7,024 rows (1 to 27 days): by design, a click can come later in the month than the impression | PASS |
| Q11 | Reconciliation | Within expected range | 1,572,189 HCP-months up to Aug 2026 identical to an independent raw MMX recompute (exposure and engagement, total and per channel) | PASS |
| Q12 | NBA 3.0 output comparison | Differences explained | NBA 3.0 monthly totals reproduced; every difference traced to the brand filter, the NPI rule, the partial Oct 2026 pull or the MMX rebuild (section 8) | PASS |
| Q13 | Reproducibility and docs | No stale text | Schema identical across runs; unmapped 0; notebook cells 1 / 9 / 13 and client summary updated | PASS |

## 3. Final results

| Item | Result |
| --- | --- |
| Engagement kept by the P1 rule (all months) | 3rd-party email 225,247 engaged messages (exposure 1,276,472); banner 68,344 (exposure 103,390,220); custom 229,360 (exposure 3,780,132) |
| c28, 12 months | Banner engagement 40,527, 3rd-party email 193,878, custom 117,024, total 351,429; total exposure about 66.37 million |
| Engagement fill (12M, share of rows > 0) | Banner 4.61%, 3rd-party email 5.91%, custom 9.54%, total 14.42% |
| HCPs with 12M engagement | 0 in c1 to c7; 1.6% (c8) to 30.8% (c28) |
| NULLs | Only the 7 engagement rates (NULL when exposure is 0) and the 3 trend features (NULL when history < 6 months: c1 to c13). No negative values outside trend (min -1, by design) |
| Always 0 (candidates to drop) | `DIGITAL_PLC_*_ENGAGEMENT_6M` for Medscape banner, OpenEvidence direct banner, ReachMD banner, ConnectiveRx banner, Healthcast banner, MJH banner, LinkedIn banner, Haymarket custom, MJH custom |
| Invariants | 0 rows with engagement > exposure (total, XPP, 3 channels x 4 windows, 3 indications, every placement); all rates in [0, 1]; placement sum = total in all 8,252,328 rows |
| Placement mapping | 44 rules, 0 unmapped rows |

## 4. Business rules (design vs notebook)

| Rule | Design (`52_` 3.1) | Notebook | Match |
| --- | --- | --- | --- |
| Brand filter | Every brand value containing Kerendia; indication (HF / CKD) kept as a dimension | `UPPER(BRND_NM) LIKE '%KERENDIA%'`; indication from `BRND_NM` + `CF_INDICATION` (HF / FINEARTS, CKD / UACR / FINEONE, BOTH) | Yes (code read) |
| Scope | Paid media only (banner, 3rd-party email, custom); calls, samples, HQ email, iRep email excluded | Role from placement dictionary; only paid-media roles kept | Yes (raw recompute on the 3 channels identical up to Aug 2026, Q11; OTHER channel 0) |
| Placement mapping | Fixed dictionary (regex on `UPPER(TRIM())`), each vendor on its own, unmapped report each run | 44 rules; 0 unmapped; placements sum to total in every row | Yes (after P7 fix) |
| Schema | Fixed list from config; no `RUNNING_` features | Yes, 144 fixed features | Yes |
| Windows | 1 / 3 / 6 / 12 months ending at `LOOKBACK_END_DATE` inclusive | Monthly buckets 18th to 17th | Yes (Q9, Q11) |
| History | Data from Jan 2025; trend NULL when history < 6 months | Trend NULL exactly when history < 6 (0 violations): c1 to c13 | Yes |
| NPI quality | Only 10-digit NPIs | `NPI_NUM` rlike `^[0-9]{10}$` | Yes (code read) |
| Engagement rule | One engagement per exposure | Engaged messages (HCP x channel x vendor x tactic x campaign x content x month) with exposure in the same month | Yes (after P1 fix) |

## 5. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature | In the 752 (rank) | NBA 3.1 feature | Status | Reason |
| --- | --- | --- | --- | --- |
| `DIGITAL_BANNER_TACTIC_EXPOSURE_IN_LAST_3_MONTH` | 68 | `DIGITAL_CH_BANNER_EXPOSURE_3M` (placement split: `DIGITAL_PLC_*_BANNER_EXPOSURE_3M`) | Preserved (renamed) | Tactic pivot replaced by fixed channel / placement list |
| `DIGITAL_RUNNING_BANNER_EXPOSURE` | 151 | `DIGITAL_CH_BANNER_EXPOSURE_12M` | Replaced | No `RUNNING_` features in NBA 3.1; 12M is the longest window |
| `DIGITAL_BANNER_EXPOSURE_IN_LAST_3_MONTH` | 200 | `DIGITAL_CH_BANNER_EXPOSURE_3M` | Preserved (renamed) | |
| `DIGITAL_BANNER_EXPOSURE_IN_LAST_1_MONTH` | 644 | `DIGITAL_CH_BANNER_EXPOSURE_1M` | Preserved (renamed) | |
| HQ email (688, 695, 698), iRep email (738, 743) | | Not in this block | Moved | HQ email = notebook 15 (QC 02); iRep email = personal promotion |
| All other NBA 3.1 features | | | See Q8 labelling below | |

### Q8 labelling of all 144 features

Counterpart = column in the NBA 3.0 output `kerendia_nba_3_0_hcp_model_paid_search_features_for_inference` (699 columns, checked: every counterpart named below exists).

| NBA 3.1 features | Count | Label | NBA 3.0 counterpart | Note |
| --- | --- | --- | --- | --- |
| `DIGITAL_CH_{BANNER, 3P_EMAIL, CUSTOM}_EXPOSURE_{1, 3, 6}M` | 9 | Preserved (renamed) | `DIGITAL_{BANNER, 3RD_PARTY_EMAIL, CUSTOM}_EXPOSURE_IN_LAST_{1, 3, 6}_MONTH` | Brand filter, NPI rule and window end changed (Q12) |
| `DIGITAL_CH_{BANNER, 3P_EMAIL, CUSTOM}_ENGAGEMENT_{1, 3, 6}M` | 9 | Preserved (renamed, definition changed) | `DIGITAL_{...}_TOTAL_ENGAGEMENT_IN_LAST_{1, 3, 6}_MONTH` | NBA 3.0 summed raw `TOTAL_ENGAGEMENT`; NBA 3.1 counts engaged messages (P1 fix) |
| `DIGITAL_CH_{...}_{EXPOSURE, ENGAGEMENT}_12M` | 6 | New (replaces `RUNNING_`) | `DIGITAL_RUNNING_{...}_{EXPOSURE, TOTAL_ENGAGEMENT}` | All-time totals removed; 12M is the longest window |
| P1 totals and XPP (`DIGITAL_TOTAL_*`, `DIGITAL_TOTAL_XPP_*`) | 16 | New | None (NBA 3.0 had no all-channel total) | |
| P3 placements (`DIGITAL_PLC_*`, 38 x 2) | 76 | New | Closest: vendor pivot (`DIGITAL_MEDSCAPE_EXPOSURE_*`, ...) and tactic pivot (`DIGITAL_BANNER_TACTIC_*`, ...) | Placement = channel x vendor x tactic; NBA 3.0 vendor pivot mixed channels incl. HQ / iRep email |
| P4 rates | 7 | New | None | |
| P5 recency | 4 | New | None | |
| P6 diversity | 5 | New | None | |
| P7 trend | 3 | New | None | |
| IND indication | 9 | New | None (NBA 3.0 kept only brand `= 'KERENDIA'`) | |
| **Total** | **144** | 24 with a counterpart, 120 new | | |

Not carried over from NBA 3.0: deep / light engagement split, HQ email and iRep email channels / vendors (other families), non-paid-media vendors (`COPAY`, `KERENDIA_FTO`, `KERENDIA_SIGNUP`), and all `RUNNING_` columns.

## 6. Independent recompute (final output)

Rebuilt from raw MMX rows: Kerendia brand values, 10-digit NPI, channels BANNER / CUSTOM / 3RD PARTY EMAIL, smallest `PROVIDER_ID` per NPI, months 18th to 17th, engagement by the engaged-message rule.

| Level | Scope | Result |
| --- | --- | --- |
| Monthly stage (Q11) | 1,572,189 HCP-months up to Aug 2026; total and per-channel exposure and engagement | 0 differences |
| Cohort features (Q9) | All 294,726 c28 HCPs; total exposure / engagement, banner exposure / engagement, 3rd-party email engagement, custom engagement; 12M and 3M | 0 differences on 12 features |

Months after Aug 2026 are not used by any cohort.

## 7. Fixes applied

| # | Problem found | Fix | Final result | Status |
| --- | --- | --- | --- | --- |
| P1 | Banner and 3rd-party email engagement were 0 in every row: MMX logs clicks / opens on separate rows with `EXPOSURE` = 0, and cell 6 capped engagement at the same row's exposure | Cell 6: cap removed. Engagement = engaged messages (HCP x channel x vendor x tactic x campaign x content) exposed in the same month; assert engagement <= exposure in every stage row | Banner and 3rd-party email engagement now filled (section 3); 0 rows with engagement > exposure. Repeat opens of one message in a month count once; engagement in a later month than the send is not counted | FIXED |
| P7 | 4 Medscape banner tactics new since the 19 Nov MMX rebuild (`TARGET LIST MEDIA`, `BRANDSPOT`, `FAST FIVE QUIZ`, `OFFSITE MEDIA`; 0.22% of rows, below the 1% alert) were unmapped: in channel and total, but in no placement | Cell 4: rule B02 (Medscape banner) widened to these tactics, placement `MEDSCAPE_BANNER`; schema unchanged | 0 unmapped rows; placement sum = total in all 8,252,328 rows | FIXED |
| P3 | MMX was rebuilt on 19 Nov 2026, after the 13 Nov run | Notebook re-run on the current MMX | Q11 recompute identical up to Aug 2026 | DONE |
| P2 | `DIGITAL_HISTORY_MONTHS` counts complete months only, so c8 shows 0 although it has partial-month data | Wording in notebook cells 1 and 13 and the client summary | Values unchanged, text correct | DONE |
| P6 | Cell 9 check label still read `engagement capped <= raw` | Label renamed | Cell 9 QC all PASS | DONE |
| P4 | 11 NPIs map to 2 universe `PROVIDER_ID`s | None needed: notebook keeps the smallest `PROVIDER_ID` per NPI | No double counting | CLOSED |
| P5 | MMX has many fully identical rows (section 9) | Not de-duplicated until the owner answers | Open | OPEN |

## 8. NBA 3.0 output comparison (Q12)

NBA 3.0 output: `kerendia_nba_3_0_hcp_model_paid_search_features_for_inference` (inference cohort I01, pulled 27 Oct 2026; 3,440,604 rows; 286,717 NPIs; calendar months Nov 2025 to Oct 2026). Compared per calendar month with the current MMX table (channel exposure; current-month columns `DIGITAL_{BANNER, 3RD_PARTY_EMAIL, CUSTOM}_EXPOSURE`). Grain differs (NPI x calendar month vs PROVIDER_ID x cohort window), so the comparison is on monthly totals.

| Step | Banner | 3rd-party email | Custom | Explains |
| --- | --- | --- | --- | --- |
| A. NBA 3.0 output vs MMX with the NBA 3.0 filter (`BRND_NM = 'KERENDIA'`, all NPIs) | Within 0.11% every month Nov 2025 to Sep 2026 (e.g. Nov 4,353,532 vs 4,354,821) | Within 2.3% (e.g. Aug 2026 74,285 vs 75,997) | Within 4% except Sep 2026 (NBA 3.0 122,976 vs 78,273 now) | Same logic reproduces NBA 3.0; small gaps = MMX rebuilt after the NBA 3.0 pull. Oct 2026 is a partial month in NBA 3.0 (pulled 27 Oct: banner 3,426,826 vs 7,114,313 now) |
| B. Brand `= 'KERENDIA'` -> `LIKE '%KERENDIA%'` | +0.4% to +1.6% a month | Up to +96% (Mar 2026 57,975 -> 113,787; Apr +54%, May +55%, Dec 2025 +39%); 0 from Jul 2026 | Up to +7.2% (Apr 2026) | Indication brand values (HF / CKD) recovered |
| C. 10-digit NPI only | About -3% a month (-2.8% to -3.4%) | About -3% to -5% | About -3% to -6% | `PDRP` / `'NULL'` NPIs removed |
| D. Universe mapping and cohort months | | | | Then equal to the NBA 3.1 stage table (Q11: identical up to Aug 2026) |

Engagement: NBA 3.0 summed raw `TOTAL_ENGAGEMENT` (3rd-party email Nov 2025 to Oct 2026: 298,650 in the output vs 322,959 in MMX now with the NBA 3.0 filter; most of the gap is the partial Oct 2026 pull, 7,537 vs 27,105); NBA 3.1 counts engaged messages, so lower by design (P1 fix log).

## 9. Open: P5 identical MMX rows (question for the table owner, draft)

If the identical rows are load duplicates, exposure is overstated by about 37% (banner) and 44% (custom). Engagement is not affected, because it already counts each message once per month (P1).

> **Subject:** Kerendia MMX (`MMX_FNL_COMBINED_AGGR_TAB` / UC `kerendia_oe_journey.mmx_fnl_combined_aggr_tab`): fully identical rows
>
> We found many rows that are identical in every column (same NPI, date, vendor, tactic, campaign, content, exposure, engagement). The table has no impression ID or timestamp, so we cannot tell repeats from duplicates. From 1 Jan 2025, Kerendia brand values, 10-digit NPIs: identical copies carry 37.1% of banner exposure, 44.1% of custom exposure and 1.2% of 3rd-party email exposure (engagement: banner 11.7%, custom 19.9%, 3rd-party email 15.1%). They are concentrated in some vendors: Medscape (banner 68%, custom 56%), Haymarket banner 68%, Nativo 64%, Doceree 55%, PulsePoint 37%, MJH email 49%; others have none (ConnectiveRx, Healthcast banner, Prescriber Point, Biopharm email). The banner share rose from 26% (2025) to 44% (2026).
>
> Example: Medscape `BA360 - Brand Alert`, campaign `Kerendiafinerenone_PP_396170.31`, one NPI, 24 Jan 2025: 1,780 identical rows with exposure 1. The 5 largest groups are all this campaign (22 to 30 Jan 2025, 1,325 to 1,780 copies each).
>
> Questions: (1) Is each row one impression / send (so identical rows are real repeats on the same day), or can rows be loaded more than once? (2) Did the 19 Nov 2026 rebuild change this? (3) Is there a field we can use to tell repeats from duplicates? (4) For PulsePoint programmatic display (40.9M of 110.7M exposures in copies), are same-day repeats expected?

Until the answer: exposure is not de-duplicated.

## 10. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 13 / 13 |
| Fixes made | P1 (cell 6, engagement rule), P7 (cell 4, rule B02), P3 (re-run on current MMX), P2 / P6 (notebook text and client summary); final output written 20 Nov 2026 |
| Open issues | P5 (MMX identical rows; question drafted in section 9, waiting for the owner) |
| Ready for modelling | Yes, with caveat P5 (exposure volumes may change if identical rows are duplicates) |
| Next channel | 02 HQ email |
