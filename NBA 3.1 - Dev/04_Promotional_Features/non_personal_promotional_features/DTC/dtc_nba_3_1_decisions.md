# DTC Market Context Features for NBA 3.1: Decisions and Evidence

**Notebook:** `DTC/34_promotional_features_DTC` (rebuilt from the NBA 3.0 notebook of the same name)  
**Spec followed:** `52_digital_feature_families_nba30_vs_nba31.md` sections 1 (shared rules) and 3.4 (family 4: DTC market context)  
**Other inputs:** `20_dtc_direct_buy_social_nba_3_0.md` (NBA 3.0 problems), `21_dtc_data_findings_2024_2026_and_open_questions.md` (questions Q-B7, Q-C2, Q-D4), notebook `50_digital_nba_phase0_validation` (fixed Facebook and SA360 queries)  
**Checks run:** 5 November 2026 on serverless (Snowflake Funnel tables, ACS and DMA mapping in Unity Catalog / volume)  
**Status:** notebook **run end to end on 5 Nov 2026** (serverless). All QC PASS: 4,620 DMA x cohort rows (210 x 22), 1,122 state x cohort rows (51 x 22), 710,710 ZIP x cohort rows; QC6 adult-weighted DMA rate = national rate (42.173 vs 42.173, cohort 2025-06). Market values identical to the prototype in section 4. To review by the team.

---

## 1. In short

DTC = Kerendia ads shown to **patients** in the doctor's area. It is market background (a control variable), not something a rep can act on. NBA 3.0 used raw impressions and clicks of four direct-buy publishers and Facebook + Instagram per DMA and month; the publishers stopped by early 2025 and their input files no longer exist. NBA 3.1 keeps **Facebook + Instagram at DMA level** and adds **SA360 DTC branded search at state level**, scales both **per 1,000 adults**, uses only **complete months up to the cohort month**, and keeps the block at **8 fixed features**.

---

## 2. Decisions

### D1. Grain and timing: market x cohort, complete calendar months up to the cohort month

* Same cohorts as all NBA 3.1 blocks (monthly from 2025-01, offset 7). Cohort `2026-09_offset7` has cutoff 6 Oct 2026; its "1M" window is **September 2026** (the last complete calendar month before the cutoff), "3M" = July to September.
* This is the "lag one month" in 52: the prediction period starts after the cutoff, so the newest month used is always the month before the prediction month. NBA 3.0 joined the doctor's **same** month (contemporaneous), which can include days after the prediction date.
* The 6 days of the next month before the cutoff are **not** used: a partial month would not be comparable with full months.

### D2. Sources

| Source | Decision | Reason / evidence |
| --- | --- | --- |
| Direct buys (Health Union, Healthline, Sharecare, WebMD) | Dropped | Zero (or a trace of WebMD) since early 2025; input files gone (52, 3.4). A feature that is 0 at prediction time only tells the model "old period" |
| PulsePoint, The Trade Desk DTC | Dropped | Loaded but never used in NBA 3.0; no current source |
| **Facebook + Instagram** (`FUNNEL_DATA_FACEBOOKADS_GEO_DMA`, `DATA_SOURCE_NAME = 'Bayer_Kerendia'`) | **Kept**, DMA x month | 211 DMAs every month from Jan 2024; read live from Snowflake instead of the old saved file |
| **SA360 search, campaigns `KER_DTC_`** (`FUNNEL_DATA_NEW_SA360_REGION`) | **Added**, state x month | Still running every month; patient branded search. `KER_HCP_` campaigns are doctor search and are excluded |

### D3. Start months

* Social from **Jan 2024**: 211 DMAs in every month, so even cohort 2025-01 has a full 3-month window.
* Search from **Jan 2025**: in 2024 SA360 reported only 8 regions; from Jan 2025 it reports 53 (50 states, DC, and two California sub-regions). Search 3M features are therefore NULL for cohorts 2025-01 and 2025-02 (window starts before the data).

### D4. Geography

* **Social:** DMA names from Facebook are matched (lower case, trimmed) to `DMA_Names_Codes.csv`. All names match except `unknown` (264,895 impressions, 0.16%), which is dropped. The notebook stops if more than 1% is unmatched.
* **Search:** state level only (DMA / Metro search data stopped in Jan 2025). `San Francisco Bay Area` and `Silicon Valley` are added to California. Decision on Q-B7: a doctor gets the value of **their state**; no population split of states into DMAs, because that would invent DMA variation that does not exist in the data.
* **Doctor link:** the output has one row per **ZIP x cohort** with `DMA_CODE` and `STATE_NAME`, so the combine step only joins on the doctor's 5-digit practice ZIP. ZIP -> DMA uses the same `DMA Zip Mapping.parquet` as NBA 3.0 (leading zeros restored; 3,268 rows with DMA code `?` dropped).

### D5. Per 1,000 adults (ACS 2020, civilian population 18+)

* Table: `whc_data_zone1_prod.dem_zip_sdoh_acs20`, column `ACS_TOT_CIVIL_POP_ABOVE18_ZC`, US states and DC only.
* **Pitfall found:** the table has one row per ZIP but the population is at ZCTA level and repeats for each ZIP of the same ZCTA. Summing ZIP rows gives about 420M adults; **deduplicating by ZCTA gives 251,961,127** (realistic). The notebook asserts 230M to 280M.
* Why per 1,000 adults: raw totals mostly measure region size (regions rank almost the same every year, 52 / 21). Per-capita makes New York and a small DMA comparable.
* DMA code 646 (`No DMA`) has no population and gets NULL.

### D6. Click outlier (Q-C2)

* National Facebook CTR per month (Jan 2024 to May 2026, complete months): median 0.60%; **May 2026 = 2.31%** (105,643 clicks), the only month above twice the median.
* Rule (generic, not a hard-coded month): in a month whose national CTR is above 2x the median, clicks per DMA are re-estimated as impressions x median CTR. Impressions are not changed. The months fixed are written to `expected_schema.json`.
* August 2025 has far fewer rows (24,842) but normal impressions (2.05M), so no fix is applied.

### D7. Missing months are NULL, quiet months are 0

* A dense calendar (every market x every month from the start month to the source's last complete month) is built, so a month with no campaign = 0 (NBA 3.0 left NULL).
* A month is complete only if the source has its last day. Facebook data ends **22 June 2026**, so its last complete month is **May 2026**; social volume features are NULL from cohort 2026-06. They are not set to 0, because we do not know yet whether the campaign stopped or the feed is late (Q-D4).
* `DTC_SOCIAL_MONTHS_SINCE_LAST_CAMPAIGN` keeps counting (1, 2, 3, ...) after the data end: it is the honest social feature if the campaign stopped (52, 3.4).

### D8. Eight features (52 asks for 4 to 8)

| Feature | Level | Meaning |
| --- | --- | --- |
| `DTC_SOCIAL_IMPRESSIONS_PER_1K_ADULTS_1M` | DMA | Facebook + Instagram impressions in the cohort month per 1,000 adults |
| `DTC_SOCIAL_IMPRESSIONS_PER_1K_ADULTS_3M` | DMA | Same, last 3 complete months (sustained pressure) |
| `DTC_SOCIAL_CLICKS_PER_1K_ADULTS_3M` | DMA | Patient response, 3 months |
| `DTC_SOCIAL_MONTHS_SINCE_LAST_CAMPAIGN` | DMA | 0 = active in the cohort month |
| `DTC_SEARCH_IMPRESSIONS_PER_1K_ADULTS_3M` | State | Patients searching for Kerendia, 3 months |
| `DTC_SEARCH_CLICKS_PER_1K_ADULTS_1M` | State | Search clicks in the cohort month |
| `DTC_SEARCH_CLICKS_PER_1K_ADULTS_3M` | State | Search clicks, 3 months |
| `DTC_SEARCH_MONTHS_SINCE_LAST_CAMPAIGN` | State | 0 = active in the cohort month |

Not built (from file 30, section 3): CTR (clicks and impressions per adult already carry it; a ratio of two small numbers is noisy), 6-month windows, trend, per-HCP pressure and pressure index. With only about 210 DMAs and 51 states there is little independent information; more columns would mainly risk geographic overfitting.

---

## 3. NBA 3.0 vs NBA 3.1

| Topic | NBA 3.0 | NBA 3.1 |
| --- | --- | --- |
| Columns | 10, dynamic pivot by vendor | 8, fixed |
| Vendors | 4 direct buys + FB+IG (direct buys stopped) | FB+IG + SA360 DTC search |
| Row | DMA x calendar month | ZIP x cohort (plus DMA x cohort and state x cohort tables) |
| Timing | Same month as the doctor's month | Complete months up to the cohort month |
| Scale | Raw counts | Per 1,000 adults |
| Missing | NULL for months without data | 0 for quiet months, NULL for months after the data end |
| Dates table | Not read (all months from Jan 2023) | Cohort rules shared with all NBA 3.1 blocks |

---

## 4. Prototype results (market level, full data)

| Cohort | Social impressions per 1k, 3M (DMA average) | Social months since last | Search clicks per 1k, 3M (state average) |
| --- | --- | --- | --- |
| 2025-01_offset7 | 25.4 | 0 | NULL (window before data) |
| 2025-06_offset7 | 52.4 | 0 | 0.172 |
| 2026-05_offset7 | 50.5 | 0 | 0.130 |
| 2026-06_offset7 | NULL | 1 | 0.144 |
| 2026-09_offset7 | NULL | 4 | 0.184 |

Checks: one row per market x cohort for both sources (210 DMAs, 51 states). Second-method check: national FB+IG impressions Nov 2024 to Jan 2025 (5,121,895) / 251.96M adults = 20.3 per 1,000; the plain DMA average (25.4) is higher because small DMAs count equally. The notebook's QC6 checks the **adult-weighted** DMA average against the national rate (must agree within 0.1%).

The prototype covered cohorts 2025-01 to 2026-09. The notebook also builds **2026-10** (search data is complete for October 2026), and adds the ZIP-level table and QC6, which were not part of the prototype.

---

## 5. Open points for the team

0. **Figure check (5 Nov run):** confirmed by the run: 'unknown' DMA = 0.16% of impressions, 251,961,127 adults, last complete social month May 2026, May 2026 the only outlier month, national rate check (QC6). Not re-measured: the ~420M summed-ZIP total, 8 SA360 regions in 2024, the August 2025 row count, and the 5,121,895 / 20.3 example in section 4.

1. **Q-D4:** did Facebook + Instagram stop after June 2026 or is the feed late? If stopped, keep only `DTC_SOCIAL_MONTHS_SINCE_LAST_CAMPAIGN` from social; if late, re-run when it returns.
2. **Q-C2:** confirm the May 2026 click spike is a tracking error (our fix assumes so).
3. **Doctor ZIP:** the combine step needs the doctor's primary practice ZIP (5 digits); confirm which table it comes from in NBA 3.1.
4. **ACS year:** ACS 2020 is used; switch if a newer SDOH release is loaded.
5. ~~Run the notebook~~ Done 5 Nov 2026; results match section 4 (cohort 2026-10 added: search clicks 0.185 per 1,000, social months since last campaign 5).
6. Keep DTC as a control: never show these features as an NBA reason or action.
