# DTC Market Context Features (Family 4): NBA 3.0 vs NBA 3.1

**Audience:** Kerendia brand, analytics, OE and consumer (DTC) media teams  
**Scope:** Family 4, DTC (direct-to-consumer) media: Kerendia ads shown to **patients** in the doctor's area (Facebook + Instagram, patient branded search)  
**Notebook:** `DTC/34_promotional_features_DTC` (rewrite of NBA 3.0 `03_HCP_Level_Features/34_promotional_features_DTC`)  
**Based on:** sections 1 and 3.4 of `52_digital_feature_families_nba30_vs_nba31.md`, `21_dtc_data_findings_2024_2026_and_open_questions.md`, the NBA 3.1 notebook code and its run on 6 November 2026 (team cohorts, team output layout)  
**Date:** 6 November 2026

> HCP paid media (ads shown to doctors), HQ email, iRep email and all rep activity are **not** in this family. DTC is **market background** (a control variable): it describes the doctor's area and is never an action or a reason shown in NBA.

---

## Summary in one page

* **The problem.** In NBA 3.0, DTC features ranked high (Health Union impressions was the **best non-personal feature, rank 32 of 752**; Facebook + Instagram clicks and impressions ranks 93 and 124; WebMD rank 107). But the four direct-buy publishers have been **zero since early 2025** and their input files no longer exist, so at prediction time these features only tell the model "old period".
* **Why else.** (1) Raw totals mostly measured **region size**: regions rank almost the same every year (rank correlation 0.98). (2) The doctor's **same** month was used, which can include days after the prediction date. (3) Months without data were left empty (NULL) instead of 0. (4) Columns came from a dynamic pivot by vendor. (5) Patient search (SA360) was never used.
* **What NBA 3.1 does.** It keeps **Facebook + Instagram by DMA** (media region) and adds **SA360 patient branded search by state**, scales both **per 1,000 adults**, uses only **complete months up to the cohort month**, fixes a click-tracking outlier, and keeps the block to **8 fixed features**. The output has one row per **ZIP x cohort**, ready to join on the doctor's practice ZIP.
* **Result.** The team's 28 promotional cohorts c1 to c28 (lookback ends 17 Jun 2024 to 17 Sep 2026): 5,880 DMA x cohort rows (210 x 28), 1,020 state x cohort rows (51 states x 20 cohorts, c9 to c28, because search starts in January 2025) and **904,540 ZIP x cohort rows**. All quality checks pass, including the national check (adult-weighted DMA rate = national rate, 32.324 vs 32.324 for c6).
* **Aligned with the team (6 Nov 2026).** Same cohorts, cohort columns (`COHORT`, `DATASET`, `PREDICTION_MONTH`, `SVC_DT`) and output folder / format as the Digital Engagement and High-Intent blocks. DTC has no doctor key (it is built by area), so the `PROVIDER_ID` change does not apply here.
* **What this gives the business.** The model can account for how much Kerendia patient advertising and patient search there is around each doctor, on a scale that compares a large and a small region fairly, without mistaking it for something a rep did.
* **Main open point.** Facebook + Instagram data ends on **22 June 2026**: social volume features are empty from cohort c26 (cohort month June 2026) until we know whether the campaign stopped or the feed is late.

---

## 1. NBA 3.0 compared with NBA 3.1

### 1.1 What was happening in NBA 3.0

The NBA 3.0 notebook did not read Snowflake. It read tables saved earlier by other notebooks, one row per DMA x month x vendor, pivoted by vendor into **10 columns** (impressions and clicks for Health Union, Healthline, Sharecare, WebMD and Facebook + Instagram). PulsePoint and The Trade Desk DTC were loaded but never used. There was no date filter (all months from January 2023) and doctors got the value of their DMA for the same calendar month.

Where the DTC features ranked in NBA 3.0 (out of 752 features; rank 1 = most useful):

| Rank | NBA 3.0 feature | Comment |
| --- | --- | --- |
| 32 | `DTC_PROMOTION_HEALTH_UNION_TOTAL_IMPRESSIONS` | Best non-personal feature; vendor stopped by early 2025 |
| 93 / 124 | `DTC_PROMOTION_FB_AND_IG_TOTAL_CLICKS` / `_IMPRESSIONS` | Only source still running in 2026 (to June) |
| 107 | `DTC_PROMOTION_WEBMD_TOTAL_IMPRESSIONS` | Only a trace left (2 to 3 thousand impressions a month) |
| 283 to 632 | Sharecare, Health Union clicks, WebMD clicks, Healthline | Vendors stopped |

### 1.2 What the data showed (the five findings behind the change)

**Finding A: the direct-buy publishers stopped.** Health Union, Healthline, Sharecare and WebMD are zero (or a trace of WebMD) since early 2025, and the NBA 3.0 input files no longer exist. A feature that is 0 at prediction time cannot help the model.

**Finding B: two sources still run.** Facebook + Instagram, by DMA (211 DMAs every month from January 2024), and SA360 paid search. Patient branded search (campaigns `KER_DTC_`) is about 15% of Kerendia search clicks, 12 to 18 thousand clicks a month. Search is reported by **US state only**: DMA (Metro) data stopped in January 2025.

**Finding C: raw totals measure region size.** Regions rank almost the same every year (rank correlation 0.98), so "impressions in New York" mostly says New York is large. Dividing by the adult population makes regions comparable.

**Finding D: one month of clicks is a tracking outlier.** National Facebook click-through rate (CTR) per month, January 2024 to May 2026: median **0.60%**, May 2026 **2.31%** (105,643 clicks), the only month above twice the median.

**Finding E: the data has holes and a recent end.** Facebook + Instagram data ends on **22 June 2026** (last complete month May 2026). SA360 reported only 8 regions in 2024 and 53 from January 2025. NBA 3.0 also left months without data empty instead of 0.

### 1.3 What changed in NBA 3.1

| Topic | NBA 3.0 | NBA 3.1 |
| --- | --- | --- |
| Sources | 4 direct buys + Facebook / Instagram, from saved tables | Facebook + Instagram (`FUNNEL_DATA_FACEBOOKADS_GEO_DMA`) and SA360 patient search (`FUNNEL_DATA_NEW_SA360_REGION`, campaigns `KER_DTC_`), read live from Snowflake |
| Geography | DMA | Social by DMA; search by state (the only level available) |
| Scale | Raw impressions and clicks | Per 1,000 adults (ACS 2020, civilian population 18+) |
| Timing | The doctor's same calendar month | Complete calendar months on or before the cohort's lookback end (c28, end 17 Sep 2026: "1M" = August 2026) |
| Time grain | All months from January 2023, no cohort | The 28 team promotional cohorts c1 to c28 (`cohorts/promotional/cohorts.parquet`; c1 to c24 training, c25 to c26 testing, c27 to c28 holdout) |
| Missing months | NULL | 0 for months with no campaign; NULL only for months after the data end |
| Outliers | Not checked | Generic rule: clicks re-estimated in any month whose national CTR is above twice the median |
| Feature list | Dynamic pivot by vendor (10 columns) | **Fixed list of 8 features** with a feature manifest and an expected schema |
| Link to doctors | In a later step, by DMA | Output already at ZIP x cohort (with DMA and state), joined on the doctor's practice ZIP |
| Quality checks | One check that 9 expected names exist | Keys, fixed schema, population check, unmatched-DMA alert, national-rate check (QC6) |

---

## 2. Step-by-step feature creation

| Step | What happens | Why / business rule |
| --- | --- | --- |
| **1. Configuration** | Sets sources, paths and rules: social from 1 Jan 2024, search from 1 Jan 2025, windows 1 and 3 months, outlier rule (CTR above 2x the median), unmatched-DMA alert above 1%, population band 230M to 280M adults. | All rules in one place, applied the same way at every run. |
| **2. Team cohorts and Snowflake reader** | Reads the 28 promotional cohorts c1 to c28 (same file as the Digital Engagement, High-Intent and personal-promotion blocks) and checks there are 28. The **cohort month** is the last calendar month fully on or before the lookback end: c28 (lookback end 17 Sep 2026) uses August 2026 as "1M" and June to August as "3M". A self-test checks this rule. | The 1 to 17 September days are not used, because a partial month is not comparable with full months; nothing after the lookback end is used. |
| **3. Geography and population** | ZIP to DMA from `DMA Zip Mapping.parquet` (leading zeros restored; 3,268 rows with DMA code `?` dropped); DMA names from `DMA_Names_Codes.csv`; adults 18+ from `dem_zip_sdoh_acs20` (`ACS_TOT_CIVIL_POP_ABOVE18_ZC`), US states and DC. | **Pitfall:** population is at ZCTA level and repeats for each ZIP of the same ZCTA. Summing ZIP rows gives about 420M adults; deduplicating by ZCTA gives **251,961,127**. The notebook asserts 230M to 280M. |
| **4. Facebook + Instagram, DMA x month** | Reads `DATA_SOURCE_NAME = 'Bayer_Kerendia'`, matches DMA names (lower case, trimmed) to codes, builds a dense calendar (every DMA x every month), keeps complete months only, and applies the click-outlier rule. | All names match except `unknown` (0.16% of impressions), dropped; the notebook stops if more than 1% is unmatched. Quiet months = 0. May 2026 clicks re-estimated as impressions x median CTR (impressions unchanged). |
| **5. SA360 search, state x month** | Reads campaigns starting `KER_DTC_` (doctor search `KER_HCP_` excluded), adds `San Francisco Bay Area` and `Silicon Valley` to California, builds a dense state x month calendar. | Patient branded search: a sign of patient interest in Kerendia. A doctor gets the value of **their state**; states are not split into DMAs, because that would invent variation that is not in the data. |
| **6. Cohorts and market features** | For each market x cohort: impressions and clicks per 1,000 adults over 1 and 3 complete months, and months since the last campaign. | One row per market x cohort. |
| **7. Fixed schema and ZIP table** | Checks the 8 features against the fixed list, writes the feature manifest, and spreads the DMA and state values to every ZIP (`DMA_CODE`, `STATE_NAME`). | The combine step needs only the doctor's 5-digit practice ZIP. |
| **8. QC** | One row per market x cohort and per ZIP x cohort, fixed schema, no month after the cohort month, non-negative values, and **QC6**: the adult-weighted DMA average equals the national rate (32.324 vs 32.324 for cohort c6; must agree within 0.1%). | Catches errors before the features reach the model. |
| **9. Write outputs** | Writes the ZIP, DMA and state tables, the manifest and `expected_schema.json` (which also lists the months fixed by the outlier rule). | No partial or unchecked output. |
| **10. Summary by cohort** | Average values and months since the last campaign per cohort (section 3). | Quick view of DTC pressure over time. |

**Outputs** (folder `kerendia_nba_3_1_volume/notebook_output/dtc_nba_3_1/`, parquet, next to `digital_engagement_nba_3_1` and `high_intent_signals_nba_3_1`): `kerendia_nba_3_1_dtc_zip_features.parquet`, `kerendia_nba_3_1_dtc_social_dma_features.parquet`, `kerendia_nba_3_1_dtc_search_state_features.parquet`, `feature_manifest.parquet` and `expected_schema.json`.

---

## 3. Cross join with the monthly cohorts (market x cohort, then ZIP x cohort)

**Done.** Every DMA (social) and state (search) is crossed with every cohort, then spread to ZIPs.

* **Cohorts:** the 28 team promotional cohorts, c1 (lookback end 17 Jun 2024, cohort month May 2024) to c28 (17 Sep 2026, cohort month Aug 2026). All 28 are built.
* **Rows:** 5,880 DMA x cohort (210 x 28), 1,020 state x cohort (51 x 20) and **904,540 ZIP x cohort** (every ZIP x 28 cohorts).
* **Doctor link:** each doctor gets the row of their practice ZIP for the cohort. DMA 646 (`No DMA`) has no population and gets NULL.
* **Empty vs zero:** a month with no campaign is 0; a month after the source's last complete month is NULL.
  * **Social** (data 1 Jan 2024 to 22 Jun 2026): built for all 28 cohorts; volume features NULL from c26 (cohort month June 2026).
  * **Search** (data from 1 Jan 2025): no rows for c1 to c8 (cohort month before January 2025), so all 4 search features are NULL for those cohorts in the ZIP table. 3-month search features are also NULL for c9 and c10 (window starts before January 2025).
* **`DTC_SOCIAL_MONTHS_SINCE_LAST_CAMPAIGN`** keeps counting (1, 2, 3, ...) after the data end, so it is still meaningful if the campaign stopped.

How DTC builds up over the cohorts (6 Nov 2026 run):

| Cohort | Lookback end | Cohort month (1M) | Social impressions per 1,000 adults, 3M (DMA average) | Social months since last campaign (max over DMAs) | Search clicks per 1,000 adults, 3M (state average) |
| --- | --- | --- | --- | --- | --- |
| c1 | 17 Jun 2024 | May 2024 | 175.9 | 0 | No search data yet |
| c6 | 17 Nov 2024 | Oct 2024 | 37.9 | 2 | No search data yet |
| c9 | 17 Feb 2025 | Jan 2025 | 25.4 | 0 | NULL (window before the data) |
| c11 | 17 Apr 2025 | Mar 2025 | 31.2 | 0 | 0.142 |
| c14 | 17 Jul 2025 | Jun 2025 | 52.4 | 0 | 0.172 |
| c20 | 17 Jan 2026 | Dec 2025 | 69.2 | 0 | 0.167 |
| c25 | 17 Jun 2026 | May 2026 | 50.5 | 0 | 0.130 |
| c26 | 17 Jul 2026 | Jun 2026 | NULL | 1 | 0.144 |
| c28 | 17 Sep 2026 | Aug 2026 | NULL | 3 | 0.175 |

What the cohorts show:

* **Social pressure was highest in early 2024** (175.9 per 1,000 adults for c1), fell to 22.9 by c8 (cohort month Dec 2024), and rose again to about 50 to 70 from mid-2025 (c14 to c24).
* **Some DMAs had a social gap in late 2024:** the longest gap since the last campaign reached 4 months for c8.
* **Search clicks** stay at 0.12 to 0.18 per 1,000 adults a quarter.
* **Cross-check with the 5 Nov run:** cohorts with the same cohort month give the same values (e.g. c9 = old `2025-01_offset7`: 25.4; c14 = old `2025-06_offset7`: 52.4 and 0.172; c25 = old `2026-05_offset7`: 50.5 and 0.130), so the cohort change moved only the dates, not the logic.

The plain DMA average (25.4 for c9) is higher than the national rate (about 20.3 per 1,000) because small DMAs count equally; QC6 checks the **adult-weighted** average, which matches the national rate.

---

## 4. Types of DTC features created

There are **8 features** in 2 groups, plus the identifier columns (`ZIP5`, `DMA_CODE`, `STATE_NAME`, `COHORT`, `DATASET`, `PREDICTION_MONTH`, `SVC_DT`, `COHORT_MONTH`, `PULL_DT`).

| Group | Feature | Level | Meaning |
| --- | --- | --- | --- |
| **Social (Facebook + Instagram)** | `DTC_SOCIAL_IMPRESSIONS_PER_1K_ADULTS_1M` | DMA | Impressions in the cohort month per 1,000 adults |
| | `DTC_SOCIAL_IMPRESSIONS_PER_1K_ADULTS_3M` | DMA | Same, last 3 complete months (sustained pressure) |
| | `DTC_SOCIAL_CLICKS_PER_1K_ADULTS_3M` | DMA | Patient clicks, last 3 complete months |
| | `DTC_SOCIAL_MONTHS_SINCE_LAST_CAMPAIGN` | DMA | 0 = active in the cohort month |
| **Search (SA360, patient branded)** | `DTC_SEARCH_IMPRESSIONS_PER_1K_ADULTS_3M` | State | Patients searching for Kerendia, last 3 complete months |
| | `DTC_SEARCH_CLICKS_PER_1K_ADULTS_1M` | State | Search clicks in the cohort month |
| | `DTC_SEARCH_CLICKS_PER_1K_ADULTS_3M` | State | Search clicks, last 3 complete months |
| | `DTC_SEARCH_MONTHS_SINCE_LAST_CAMPAIGN` | State | 0 = active in the cohort month |
| **Total** | **8** | | |

File 52 asks for 4 to 8 features. With only about 210 DMAs and 51 states there is little independent information, so more columns would mainly risk the model learning geography.

---

## 5. Changes in preprocessing

| Preprocessing step | NBA 3.0 | NBA 3.1 | Effect |
| --- | --- | --- | --- |
| Source access | Saved tables from other notebooks (not refreshed) | Live Snowflake reads of the Funnel tables | Current data at every run |
| Vendor scope | 4 direct buys + Facebook / Instagram; PulsePoint and The Trade Desk loaded but unused | Facebook + Instagram and SA360 `KER_DTC_` search; `KER_HCP_` search excluded | Only sources that still run; doctor search kept out of patient media |
| DMA names | DMA codes from the saved tables | Facebook DMA names matched to codes (lower case, trimmed); stop if more than 1% unmatched | Unmatched regions caught; `unknown` (0.16%) dropped |
| Search geography | Not used | State level; two California sub-regions added to California | Patient search available for every state |
| ZIP to DMA | Done in a later step | Same mapping file, leading zeros restored, DMA code `?` dropped | Clean ZIP join in the output |
| Population | Not used | ACS 2020 adults 18+, deduplicated by ZCTA | Per-capita values; avoids the 420M double count |
| Calendar | Months with data only; NULL when a vendor was missing | Dense market x month calendar; 0 for quiet months, NULL after the data end | "No campaign" no longer confused with "no data" |
| Complete months | Not checked | A month counts only if the source has its last day | No partial months |
| Outliers | Not checked | Clicks re-estimated where national CTR is above 2x the median (May 2026) | One tracking spike no longer distorts click features |
| Timing | Same calendar month as the doctor's month | Complete months on or before each team cohort's lookback end | No information after the lookback end |

---

## 6. Business explanation of the features

| Feature group | Business question it answers | How the NBA model can use it |
| --- | --- | --- |
| **Social impressions (1M, 3M)** | How much Kerendia Facebook / Instagram advertising did patients around this doctor see, for the size of the area? | Background pressure: more patients aware of Kerendia may mean more patients asking the doctor about it. Used to adjust the effect of other actions, not as an action. |
| **Social clicks (3M)** | How many patients in the area reacted to the ads? | Patient interest, beyond just being shown an ad. |
| **Social months since last campaign** | Is Facebook / Instagram advertising running in the area, or how long ago did it stop? | Separates an active campaign from one that has ended; stays meaningful after the data end. |
| **Search impressions and clicks (1M, 3M)** | How many patients in the state searched for Kerendia and clicked the ad? | The most direct patient-interest signal in DTC: patients looking for Kerendia themselves. |
| **Search months since last campaign** | Is patient search advertising running in the state? | Same as for social. |

All DTC features are **controls**: they describe the doctor's surroundings, are the same for every doctor in the area, and must never be shown as an NBA reason or action.

---

## 7. Next steps for features not created (or not yet complete)

| Item | Status | Next step |
| --- | --- | --- |
| **Social data after June 2026** | Social volume features NULL from cohort c26 | Confirm whether the campaign stopped or the feed is late. If stopped, keep only `DTC_SOCIAL_MONTHS_SINCE_LAST_CAMPAIGN` from social; if late, rerun when the data returns. |
| Click-through rate (CTR) | Not built | Clicks and impressions per adult already carry it; a ratio of two small numbers is noisy. |
| 6-month windows, trend | Not built | Little extra information with about 210 DMAs and 51 states; revisit after the first model run. |
| Per-HCP pressure, pressure index (file 30) | Not built | Same reason: risk of the model learning geography. |
| Direct buys, PulsePoint, The Trade Desk DTC | Dropped | Add back only if a vendor restarts and a current source exists. |
| Join to the NBA 3.1 HCP feature table | Not done (combine step) | Join on the doctor's 5-digit practice ZIP + `COHORT` (c1 to c28, same as the other NBA 3.1 promotional blocks). |

---

## 8. Client alignment needed

| # | Topic | Question for the client | Current choice |
| --- | --- | --- | --- |
| 1 | Facebook + Instagram end (Q-D4) | Did the campaign stop after June 2026, or is the feed late? | Social volume NULL after May 2026; months-since keeps counting. |
| 2 | May 2026 click spike (Q-C2) | Is the 2.31% CTR in May 2026 a tracking error? | Treated as an error; clicks re-estimated with the median CTR. |
| 3 | Search geography (Q-B7) | Is state-level search acceptable, given that DMA search stopped in January 2025? | Doctor gets their state's value; no split into DMAs. |
| 4 | Doctor's practice ZIP | Which table gives the doctor's primary practice ZIP (5 digits) in NBA 3.1? | To confirm before the combine step. |
| 5 | Cohorts across families | **Resolved (6 Nov 2026).** This block now uses the team's 28 promotional cohorts c1 to c28, the same as Digital Engagement and High-Intent. | Team cohorts. |
| 6 | DTC as a control | Confirm DTC features are used only as background and never shown as a reason or action. | Control only. |
| 7 | Search for early cohorts | Search data starts in January 2025, so c1 to c8 have no search features (NULL). Is NULL acceptable for these training cohorts, or should search be left out of the model? | NULL for c1 to c8. |

---

## 9. Data sources missing or incomplete

| Source | Issue | Impact |
| --- | --- | --- |
| Direct buys (Health Union, Healthline, Sharecare, WebMD) | Zero since early 2025; input files gone | Dropped; NBA 3.0's best DTC features cannot be rebuilt. |
| Facebook + Instagram (`FUNNEL_DATA_FACEBOOKADS_GEO_DMA`) | No data after 22 June 2026 | Social volume features NULL from cohort c26. |
| SA360 search by DMA (Metro) | Stopped in January 2025 | Search only at state level. |
| SA360 search in 2024 | Only 8 regions reported | Search starts in January 2025: no search features for c1 to c8; 3-month search features NULL for c9 and c10. |
| Population | ACS 2020 is the latest loaded release | Switch if a newer SDOH release is loaded. |
| ZIP to DMA mapping | 3,268 rows with DMA code `?`; DMA 646 (`No DMA`) has no population | Those ZIPs get no DMA values (NULL). |

Figures confirmed by the 6 Nov 2026 run: row counts, cohort results, `unknown` DMA share (0.16%), 251,961,127 adults, last complete social month (May 2026), May 2026 as the only outlier month, and QC6. Figures from the earlier exploration, not re-measured in the run: the about 420M summed-ZIP population, the 8 SA360 regions in 2024, and the national 20.3 per 1,000 example.
