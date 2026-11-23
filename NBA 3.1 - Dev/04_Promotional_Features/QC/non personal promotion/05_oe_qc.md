# QC 05: OE (Omnichannel Engine) promotional features, NBA 3.1

**QC status:** DONE (channel 5 of 5). 12 / 13 PASS; Q13 PARTIAL: job still runs another user's notebook copy (P5) and the client summary is stale (P7, docs)  
**Verdict:** READY for modelling. An independent recompute from raw NPP rows matches the output except 75 of 7,839,776 sample cells (-0.008%, both directions, not explained)  
**Final output:** written 23 Nov 2026 after fixes P1, P3, P4 and P6: 8,252,328 rows x 324 columns (4 keys + 320 features). Results below are on this output unless marked "before P6" (the previous run of the same day, which differs only in PeerDirect)

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `non_personal_promotional_features/OE/35_OE_Promotional_Features_NBA31` (18 cells) |
| Client summary | `OE/OE_Promotional_Features_Client_Summary.md` |
| Readiness | `OE/OE_Promotional_Features_Readiness.md`; `12_hcp_oe_digital_review_for_nba_3_1.md` |
| Source | `kerendia_oe_journey.oe_kerendia_fact_npp_inference` (NPP only; FACT_CALL and EVNT_PRSNL_PROM excluded) |
| Helper files | `OE/helper_files/`: `Content_tagging_6_5.xlsx`, `mdb_prep_config.xlsx` (`Metric Mappings`), `channel_mapping.xlsx` |
| Output | `{V31}/notebook_output/oe_nba_3_1/kerendia_nba_3_1_oe_promotional_features.parquet` |
| Universe / cohorts | HCP universe x `cohorts/promotional/cohorts.parquet` (c1 to c28) |
| Expected shape | 320 features = 80 base x 4 windows (P3 / P6 / P9 / P12): 22 R, 16 I, 14 E channel; 9 indication; 16 content tags; 3 touchpoints. Rows = universe x 28 = 8,252,328. The column set follows the source (`SAFETY_EFFICACY` has had no exposures since the 19 Nov source rebuild) |
| NBA 3.0 counterpart | OE 2.0 model features (not part of the NBA 3.0 752) |
| NBA 3.0 final model | MLflow run `f583bcbc9d56477fae983d44c16f8c70`, 752 features |

## 2. QC checklist

| # | Check | Pass when | Final result | Status |
| --- | --- | --- | --- | --- |
| Q1 | HCP universe | Same HCP set, `0` absent, 0 duplicates | 294,726 doctors = universe without placeholder `0`; 8,252,328 rows; `HCP_COHORT_ID` unique; 294,577 universe doctors have a BH_ID in the primary mapping (the rest can only map via the OE NPI fallback) | PASS |
| Q2 | Cohorts and windows | All match | +7 day promo lag (first lagged exposure 2024-11-26); 18th-to-17th periods 202412 to 202609; P3 / P6 / P9 / P12 end at END. c1 to c6 all 0 (data from 2024-11-19, by design); c7 to c9 P3 = P12 | PASS |
| Q3 | All features made | No missing / extra column | 320 features = 80 base x 4 windows, matching the cell 17 dictionary | PASS |
| Q4 | Business rules | All match | All 8 rules in section 4 match (after P4 and P6) | PASS |
| Q5 | Data sources | Matches readiness | NPP table only, Kerendia, SFMC excluded; only Doximity, Medscape, PeerDirect, PulsePoint produce features (P2, intended); tagging file read from `helper_files/` (P3) | PASS |
| Q6 | Fill rate | Near-constant flagged | 4 content tags with no doctors in c28 P12; GENERAL = 55.6% of c28 P12 content counts; near-constant: `PATIENT_PROFILE`, `EVENT`, `SOCIAL_PROOF` (section 3) | PASS |
| Q7 | NBA 3.0 model coverage | Mapped or dropped with reason | 0 of the 752 NBA 3.0 features are OE / NPP features | PASS |
| Q8 | Preserved vs new | Every feature labelled | All 320 new vs NBA 3.0; OE 2.0 features not compared | PASS |
| Q9 | HCP trace | Final value = output | 1,129 universe doctors x 28 cohorts x 248 non-content features recomputed from raw NPP: 75 of 7,839,776 cells differ (-0.008%, both directions, not explained; before P6). Content tags not recomputed | PASS |
| Q10 | Invariants | 0 violations | Final output: 0 violations (window nesting, I / E <= R, touchpoints = sum of channels, content sum <= exposure, no NULL / negative / non-integer) | PASS |
| Q11 | Reconciliation | Within expected range | 68,194,873 NPP rows (readiness about 68M), 7,853,188 interactions, 296,295 BH_IDs mapped, 192 metric-mapping rows; R / I / E flags per channel match the readiness file; yearly vendor volumes in section 3 | PASS |
| Q12 | Cross-block overlap | Overlap documented | SFMC absent (HQ email is notebook 15). Doximity, Medscape, PeerDirect, PulsePoint also appear in family 1 (overlap); the other vendors are only in family 1 | PASS |
| Q13 | Reproducibility and docs | No stale text | Same code gives the same schema on the same source; notebook cells 16 / 17 and the readiness file updated. Job 726629940364436 still runs another user's copy (P5); client summary last edited 19 Nov, still describes an earlier design (P7) | PARTIAL |

## 3. Final results

| Item | Result |
| --- | --- |
| Source | Kerendia NPP 136,648,558 rows (2024-11-19 to 2026-11-18); 68,194,873 after filters; 7,853,188 interactions; 296,295 BH_IDs mapped |
| Vendors | Only Doximity, Medscape, PeerDirect, PulsePoint produce features; the other vendors have no `CHNL_NM_NEW` and are covered by family 1 (P2); SFMC excluded |
| Yearly interactions (exposure / engagement / doctors) | Doximity 2025 243,972 / 47,330 / 48,737, 2026 223,718 / 37,356 / 57,116. Medscape 2025 626,679 / 98,064 / 92,111, 2026 543,147 / 128,428 / 97,565. PulsePoint 2025 2,565,506 / 31,089 / 99,391, 2026 2,922,187 / 30,095 / 130,991. PeerDirect 2025 89,449 / 2,003 / 22,773 BH_IDs, 2026 222,650 / 560 / 57,102 BH_IDs (after P6) |
| Engagement rate | Doximity 17 to 19%, Medscape 16 to 24%, PulsePoint about 1%, PeerDirect below 3% |
| Content tags | 16 tags; GENERAL = 55.6% of c28 P12 content counts; `ACCESS_COVERAGE`, `MECHANISM_OF_DISEASE`, `PATIENT_PROFILE`, `STUDY_DESIGN` have no doctors in c28 P12; near-constant `PATIENT_PROFILE`, `EVENT`, `SOCIAL_PROOF`; `SAMPLES` excluded, so content sum < exposure |
| Dropped by design | 22 exposures with NULL `UNIQ_NPP_ID`; engagements dated after the raw load end 2026-09-23; PeerDirect `PV Compendium Quiz` (13,478 rows in 2025) and `MD Shuffle` (2026) placements have no channel rule (accepted, 23 Nov 2026) |
| Invariants (final output) | 0 violations; see Q10 |

## 4. Business rules (readiness vs notebook)

| Rule | Readiness | Notebook | Match |
| --- | --- | --- | --- |
| Promo lag | +7 days | `PROMO_LAG_DAYS = 7`; first lagged exposure 2024-11-26 | Yes |
| Periods | 18th to 17th lookback periods | `CUTOFF_DAY = 17`; confirmed by recompute (Q9) | Yes |
| Content tag | Left join on 14 attributes; untagged, `-`, `Not Needed` = GENERAL; `SAMPLES` excluded | Same in `npp_processing()`; no `OE_SAMPLES_*` columns; 470,895 SAMPLES transactions excluded | Yes |
| R / I / E flags | From `mdb_prep_config.xlsx` `Metric Mappings` + `EXTRA_METRIC_MAPPINGS` | 160 + 32 = 192 rows; flags per channel match readiness section 7 (Q11) | Yes |
| One engagement per exposure | Engagement / action <= exposure | 0 violations on final output; joined on the interaction without `CONTENT_TAG` (P4) | Yes (after P4) |
| Excluded vendors | SFMC HQ email (notebook 15) | `EXCLUDE_VENDORS = ['SFMC']`; no `OE_SFMC_*` | Yes |
| Indications | HF, CKD, T2D (no T1D records) | 36 `OE_IND_*` columns; T1D none | Yes |
| Channel derivation | Section 4.4 (TACT_NM rules) | Same, plus PeerDirect `TACT_TYP` fallback when `TACT_NM` is NULL (P6). Readiness file updated 23 Nov 2026 (sections 2, 3, 4.1, 4.4, 4.6, 4.10, 5, 7, 9) | Yes |

## 5. NBA 3.0 / OE 2.0 vs NBA 3.1 feature map

| Earlier feature | In the 752 (rank) | NBA 3.1 feature | Status | Reason |
| --- | --- | --- | --- | --- |
| None (no OE / NPP feature in the NBA 3.0 752) | - | All 320 `OE_*` features | New | OE features come from the OE 2.0 model, which NBA 3.0 did not use (Q7). Feature-by-feature comparison with OE 2.0 not done |

## 6. Independent recompute

Sample recompute instead of 5 single doctors: 1,129 universe doctors x 28 cohorts x 248 non-content features, rebuilt from raw NPP rows (Kerendia, mapped BH_ID, smallest `PROVIDER_ID` per BH_ID) through channel, R / I / E flags, +7 day lag, 18th-to-17th period and window sums.

| Scope | Result |
| --- | --- |
| Non-content features (before P6) | 75 of 7,839,776 cells differ (3,053,119 vs 3,053,367, -0.008%), both directions; not explained |
| Content-tag features | Not recomputed |
| Invariants (final output, independent check) | 0 violations (Q10) |

The notebook's own QC cell: all checks pass except the expected ones (c1 to c6 empty; 4 content tags with no doctors in c28; GENERAL 55.6% > 50%).

## 7. Fixes applied and notes

| # | Problem found | Fix | Final result | Status |
| --- | --- | --- | --- | --- |
| P1 | Placeholder doctor `0` in the output (28 rows) | Cell 6 filters `PROVIDER_ID <> '0'` | 294,726 doctors, 8,252,328 rows (same as the other blocks) | FIXED |
| P3 | `CONTENT_TAG_FILE` read another user's folder | Reads `{HELPER_DIR}/Content_tagging_6_5.xlsx` (byte-identical copy) | Notebook check "Content tagging file found" PASS | FIXED |
| P4 | Recompute was 5.8% above the output. Most of it was a QC sample error (339 sample doctors outside the universe). The rest (-0.14%): 22 NULL-ID exposures and 33 late engagements (by design), and 6 Medscape email engagements lost because rows of one interaction carried different content tags and engagement was joined on `CONTENT_TAG` | `npp_processing()` joins engagement / action to the exposure on the interaction without `CONTENT_TAG` | Residual 75 of 7,839,776 sample cells (-0.008%) | FIXED |
| P6 | PeerDirect 2025 (324,013 rows, NULL `TACT_NM`) produced no features | PeerDirect placement = `coalesce(TACT_NM, TACT_TYP)`, format from `CHNL_NM` when missing; `TACT_TYP` kept raw for this rule | 310,535 of 324,013 rows recovered; interactions 7,755,735 -> 7,853,188 (non-PeerDirect unchanged); 8 new `OE_PEERDIRECT_MDFI_EMAIL_I_*` / `_E_*` columns, 320 features | FIXED |
| P2 | Only 4 vendors become features | None: intended (user, 23 Nov 2026); other vendors covered by family 1 (Q12) | | CLOSED |
| P5 | Job 726629940364436 runs another user's copy (`/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_1_develop_sa/...`) | Repoint the job task to this notebook | Scheduled runs would not include P1 / P3 / P4 / P6 | OPEN |
| P7 | Client summary `OE/OE_Promotional_Features_Client_Summary.md` last edited 19 Nov 2026, before all fixes; still describes an earlier design (e.g. 195 features over 5 windows, SFMC in the vendor table) | Update the summary to the final run | | OPEN (docs) |
| Note | PV Compendium Quiz and MD Shuffle PeerDirect placements have no channel rule | Accepted (user, 23 Nov 2026) | About 25k source rows, mostly banner / web views | ACCEPTED |

## 8. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 12 / 13 (Q13 PARTIAL: job path P5, client summary P7) |
| Fixes made | P1 (drop doctor `0`), P3 (local tagging file), P4 (engagement / action joined without `CONTENT_TAG`), P6 (PeerDirect `TACT_TYP` fallback); notebook cells 16 / 17 and readiness file updated; final output written 23 Nov 2026 |
| Open issues | P5 (job path), P7 (client summary, docs only). Accepted: PV Compendium Quiz / MD Shuffle unmapped; 75-cell residual in Q9 (-0.008%) |
| Ready for modelling | Yes |
| Next channel | None (last non-personal channel) |
