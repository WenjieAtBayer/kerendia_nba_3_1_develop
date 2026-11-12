# DTC Data Findings (2024–2026) and Open Questions

**Group:** Non-personal promotional features (promotion that does not involve a sales rep)  
**Purpose:** summarise what Kerendia DTC data exists for the last two years, how it compares with what NBA 3.0 used, and list the questions to clear in meetings before the DTC part of NBA 3.1 is planned.  
**Built from:** direct queries of the Snowflake source tables (including `FUNNEL_DATA_NEW_SA360_REGION`, added 26 October 2026) and of the OE copies in `kerendia_oe_journey`, plus a review of the NBA 3.0, OE 2.0 and older monthly-production `00_Write_Input_Files` notebooks  
**Date:** October 26, 2026

## What is this document about?

"DTC" means **Direct-to-Consumer**: Kerendia ads shown to the **public (patients)**, not to doctors (for example on WebMD, Facebook / Instagram, connected TV, or as paid search results on Google and Bing). The ads are not linked to a doctor, so the data is per **region** (DMA, Designated Market Area: about 210 media regions in the US) or, for some sources, has no region at all. In NBA, each doctor gets the numbers of the region where they work, as background information about the doctor's surroundings.

This document is **not** a plan. It records the facts found in the data and the open questions. The NBA 3.0 DTC pipeline itself is described in `20_dtc_direct_buy_social_nba_3_0.md`.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code.

**About the numbers.** Figures were pulled on 26 October 2026. "FT V1" is short for the Flashtalking table `cph_db_prod.enrich_v2.MMX_FLASHTALKING_NEW_DAILYFILES_V1`. Impressions = times an ad was shown; clicks = times someone clicked it. October 2026 is probably an incomplete month.

---

## 1. In short

* **Display, video and direct-buy DTC have almost completely stopped.** Since early 2025 the only ones still running are Facebook / Instagram and a trace of WebMD (about 2–3 thousand impressions a month).
* **Paid search is the one channel that never stopped**, and it has been growing again since mid-2025: about 0.5–1.0 million impressions and 55–180 thousand clicks a month (HCP and DTC campaigns together), with the number of campaigns rising from 36 to more than 100. **NBA 3.0 never used paid search.**
* **Paid search now has a regional source, but by US state, not by DMA.** The new table `FUNNEL_DATA_NEW_SA360_REGION` (section 4.3) covers 13 July 2024 – 26 October 2026 and splits paid search by **state** (50 states + District of Columbia, plus two Google regions: "San Francisco Bay Area" and "Silicon Valley"). For DTC campaigns it matches the national table to within about 1%. The older SA360 tables with a DMA stop in January 2025 (Funnel DMA tab) or January 2026 (Flashtalking, clicks only).
* **Most Kerendia paid search is HCP search, not DTC.** Campaign names start with `KER_HCP_` or `KER_DTC_`. Only 6 of 153 campaigns are DTC, about 15% of clicks; DTC paid search is about 0.1 – 0.2 million impressions and 12 – 18 thousand clicks a month in 2025 – 2026, all branded search.
* **The NBA 3.0 DTC features are effectively empty at prediction time.** Its strongest DTC feature (Health Union impressions, rank 32 in the model) and the other direct-buy features have been zero since early 2025. The next prediction looks back to 30 September 2026, but the copied DTC data ends in June 2026.
* **NBA 3.0 read only part of the DTC data**: 4 direct-buy websites plus Facebook / Instagram. PulsePoint and The Trade Desk were loaded but never used; connected TV / online video, GoodRx and paid search were not loaded at all.

## 2. Source tables

| Source | Snowflake table | What it holds | Region? | Period with data |
| --- | --- | --- | --- | --- |
| Flashtalking (FT V1) | `cph_db_prod.enrich_v2.MMX_FLASHTALKING_NEW_DAILYFILES_V1` | Ad-server data for all `KER_DTC%` campaigns: direct buys, programmatic display, connected TV / video, GoodRx, and Google / Bing search clicks | DMA, per day | 2023 – Jun 2026 (WebMD only after Jan 2025) |
| Flashtalking (other version) | `CPH_DB_PROD.ENRICH.FLASHTALKING_DMA` | Used by the NBA 3.0 ops pipeline instead of FT V1 (per a code comment) | DMA | Not profiled |
| SA360 old | `CPH_DB_PROD.MODEL_V2.SA_360_FUNNEL` | Paid search on Google Ads and Bing Ads, by keyword and device | **No** | Jul 2021 – Sep 2024 (a few rows in Oct 2024) |
| SA360 new | `CPH_DB_PROD.ENRICH_V2.FUNNEL_NEW_SA360` | Paid search (New Search Ads 360), by campaign, ad group, keyword and device | **No** | Jan 2024 – Oct 2026 |
| SA360 DMA tab | `FUNNEL_PROD_INB2.FUNNEL__MK7FZ_CN_UWQY_VMROR.SA_360_FUNNEL_DMA_TAB` | Paid search with region (`DMA_REGION_MATCHED__FILE_IMPORT`) | DMA (210) | Jan 2022 – Jan 2025 |
| **SA360 region (new)** | `FUNNEL_PROD_INB2.FUNNEL__MK7FZ_CN_UWQY_VMROR.FUNNEL_DATA_NEW_SA360_REGION` | Paid search (New Search Ads 360) by campaign and region, per day, all Bayer brands (44 SA360 accounts; Kerendia in 4) | **State** (51 incl. DC) + 2 Google regions; not DMA | 13 Jul 2024 – 26 Oct 2026 |
| Facebook / Instagram | `FUNNEL_PROD_INB2.FUNNEL__MK7FZ_CN_UWQY_VMROR.funnel_data_FacebookAds_Geo_dma` (`DATA_SOURCE_NAME = 'Bayer_Kerendia'`) | Social ads | DMA (210) | Feb 2023 – Jun 2026 (from the OE copy `kerendia_oe_journey.hcp_model_social_inference`) |
| The Trade Desk (2022) | `FUNNEL_PROD_INB2.FUNNEL__MK7FZ_CN_UWQY_VMROR.Tradedesk_Funnel_DMA` | Programmatic display, 2022 only | DMA | 2022 |
| CM360 (2022) | `FUNNEL_PROD_INB2.FUNNEL__MK7FZ_CN_UWQY_VMROR.CM_360` | Direct buys and PulsePoint, 2022 only | DMA | 2022 |

As instructed: SA360 should be read from `SA_360_FUNNEL` up to 30 September 2024 and from `FUNNEL_NEW_SA360` from 1 October 2024; Flashtalking should be read from FT V1. For regional paid search, the new source to use is `FUNNEL_DATA_NEW_SA360_REGION` (given on 26 October 2026, profiled in section 4.3).

## 3. What ran, by year

Impressions in millions (clicks in thousands in brackets). "–" = no data.

| Channel (source) | 2023 | 2024 | 2025 | 2026 (Jan–Oct) | Last real month | In NBA 3.0? |
| --- | --- | --- | --- | --- | --- | --- |
| Direct buys: Health Union, Healthline, Sharecare, WebMD (FT V1) | 34.6 (59) | 8.4 (23) | 0.05 (0.2) | 0.02 (0.1) | Health Union: Sep 2024; Sharecare: Dec 2024 (small); Healthline: Jan 2023; WebMD: trace only | Yes (8 columns) |
| Facebook / Instagram (Funnel) | 202.8 (630) | 97.1 (561) | 41.7 (239) | 22.3 (210), Jan–Jun only | still running | Yes (2 columns) |
| PulsePoint DTC display (FT V1) | 143.4 (91) | 199.0 (122) | – | – | Sep 2024 | Loaded, never used |
| The Trade Desk display + connected TV + audio (FT V1) | 428.6 (242) | ~0 | – | – | Dec 2023 | Display loaded, never used; CTV / audio not loaded |
| Mediacom connected TV / online video: Disney, Hulu, Discovery (FT V1) | 38.1 (4) | 15.9 (1) | – | – | mid-2024 | Not loaded |
| GoodRx / SingleCare / CBS News display (FT V1) | 0.4 (2) | 2.5 (2) | ~0 | – | Jan 2025 | Not loaded |
| Paid search, SA360 old + new (no region) | 72.8 (7,346) | see note | 8.8 (1,232) | 6.8 (1,226) | still running | Not loaded |
| Paid search, SA360 DMA tab (with region) | 205.0 (2,132) | 5.2 (1,135) | 0.2 (30), Jan only | – | Jan 2025 | Not loaded |
| Paid search, SA360 region, **DTC campaigns only** (state) | – | 0.17 (33), Jul–Dec only | 1.47 (186) | 1.36 (144) | still running | Not loaded |
| Paid search, SA360 region, HCP campaigns (state) | – | 2.87 (267), Jul–Dec only | 7.00 (973) | 4.84 (828) | still running | Not loaded (HCP, not DTC) |
| Paid search clicks in FT V1 (Google, Bing; region but no impressions) | 0 (1,118) | 0 (1,269) | 0 (131) | ~0 | Bing: Oct 2025; Google: Jan 2026 | Not loaded |

Note for 2024 paid search: SA360 old has Jan–Sep 2024 (22.6M impressions, 3,189K clicks) and SA360 new has all of 2024 (12.8M, 1,731K). The two overlap for nine months and do **not** give the same numbers (see Q-D2).

## 4. The last two years in more detail (Nov 2024 – Oct 2026)

### 4.1 Paid search (SA360 new)

| Period | Impressions per month | Clicks per month | Cost per month | Campaigns |
| --- | --- | --- | --- | --- |
| Nov 2024 – Mar 2025 | 0.47 – 0.56M | 42 – 66K | about $0.22 – 0.36M | 36 |
| Apr – Jun 2025 | 0.65 – 0.85M | 109 – 180K | about $0.39 – 0.51M | 36 – 39 |
| Jul – Dec 2025 | 0.68 – 1.00M | 87 – 123K | about $0.36 – 0.50M | 76 – 86 |
| Jan – Sep 2026 | 0.50 – 0.81M | 90 – 165K | about $0.42 – 0.46M | 83 – 110 |
| Oct 2026 (probably partial) | 0.64M | 97K | about $0.35M | 114 |

The filter used was campaign name containing `KER` or data source name containing `KERENDIA`. **These totals mix HCP and DTC search.** Campaign names start with `KER_HCP_` or `KER_DTC_` (section 4.3); about 80 – 85% of the impressions and clicks are HCP search.

### 4.2 Facebook / Instagram

* 1.9 – 5.4 million impressions a month in 2025, 2.1 – 4.6 million in Jan – Jun 2026.
* Shown in all 210 regions every month.
* **The regions rank almost the same every year** (rank correlation 0.98 between Jan – Jun 2025 and Jan – Jun 2026). The numbers therefore mostly reflect how big each region is, not where Kerendia pushed harder.
* **May 2026 looks wrong:** 105,591 clicks for 4.6 million impressions (2.3% clicked) against the usual 0.5 – 0.7%.
* The copy used here (`hcp_model_social_inference`, pulled 1 October 2026) ends in **June 2026**.

### 4.3 Paid search by region: `FUNNEL_DATA_NEW_SA360_REGION`

**What it is.** One line = one day, one campaign, one region, in New Search Ads 360. The table holds all Bayer brands; Kerendia is in 4 of the 44 SA360 accounts (`DATA_SOURCE`). Main columns: `DATE`, `CAMPAIGN__NEW_SEARCH_ADS_360`, `REGION__NEW_SEARCH_ADS_360`, `GEO_TARGET_TYPE__NEW_SEARCH_ADS_360`, `COUNTRY__NEW_SEARCH_ADS_360`, `IMPRESSIONS`, `CLICKS`, `COST`; there are also ad group, keyword, device, conversions and visits columns.

**The region is a US state, not a DMA.** For Kerendia, `GEO_TARGET_TYPE` is `State` (51 values: 50 states + District of Columbia) or `Region` (2 values: "San Francisco Bay Area" and "Silicon Valley", about 2% of clicks). There is no DMA or Metro column, and `GEO_TARGETS__NEW_SEARCH_ADS_360` is empty for every Kerendia row. (SA360 no longer reports DMA; its **Metro** dimension holds the same values: in the old `SA_360_FUNNEL_DMA_TAB`, `METRO_AREA_MATCHED__FILE_IMPORT` equals `DMA_REGION_MATCHED__FILE_IMPORT` on all 4.7M Kerendia rows. Metro is the field to request going forward.) No current SA360 table in the Funnel schema has Metro for Kerendia: `SA_360_FUNNEL_DMA_TAB` stops in January 2025, `SA_360_FUNNEL_DMA` is empty, `BING_FUNNEL_DMA` (Bing only, Metro) stops in December 2024, and `FUNNEL_GOOGLE_ADWORDS_GEO` has Kerendia only for a 2023 YouTube campaign, with no Metro. Using the state table in NBA means giving each doctor the numbers of their **state**, or splitting each state across its DMAs (see Q-B7).

**Period:** 13 July 2024 – 26 October 2026 (July 2024 is partial). Updated daily.

**How complete it is, compared with the national table `FUNNEL_NEW_SA360`** (Kerendia, all campaigns):

| Period | Impressions found by region | Clicks found by region |
| --- | --- | --- |
| Aug 2024 – May 2026 | 92 – 98% | 83 – 98% |
| Jun – Oct 2026 | 84 – 90% | 64 – 78% |
| **DTC campaigns only**, Jul 2024 – Oct 2026 | about 99% | about 99% |

The gap in 2026 comes from HCP campaigns; DTC campaigns are almost fully covered (Q-B9).

**DTC and HCP campaigns.** Every Kerendia campaign name starts with `KER_DTC_` or `KER_HCP_`, which answers part of Q-B3:

| Type | Campaigns | Impressions (Jul 2024 – Oct 2026) | Clicks |
| --- | --- | --- | --- |
| DTC | 6 | 3.0M (17%) | 363K (15%) |
| HCP | 147 | 14.7M (83%) | 2,067K (85%) |

The 6 DTC campaigns are all branded (`BRN`) search on Google and Bing, for example `KER_DTC_cpc_google_BRN_BRN_X_MB_PHR_X_X` (mobile) and `..._DK_...` (desktop), plus two `FIN_BRN` campaigns.

**DTC paid search by month (state table):**

| Period | Impressions per month | Clicks per month | States / regions |
| --- | --- | --- | --- |
| Jul – Dec 2024 | 16 – 37K | 3.5 – 6.7K | **8 only**: Texas, California, Florida, New York, Georgia, North Carolina, SF Bay Area, Silicon Valley |
| Jan – Apr 2025 | 68 – 87K | 13 – 15K | all 53 |
| May 2025 – Oct 2026 | 105 – 175K | 11.6 – 18.5K | all 53 |

For comparison, national DTC paid search was 1.3 – 2.0M impressions and 200 – 316K clicks a month in January – April 2024, then dropped to about 30K impressions in May 2024. So DTC search is now about a tenth of its early-2024 size.

**Why this may be useful.** In July – December 2024 DTC search ran in only 6 states (plus 2 Bay Area regions) and from January 2025 in all states. This switch is a natural regional difference that the model could learn from, if the 6 states were chosen on purpose (Q-B10).

**Biggest states** (all Kerendia campaigns, clicks): Texas 216K, Florida 196K, California 192K, New York 174K, North Carolina 106K, Georgia 103K.

### 4.4 Everything else

* WebMD: 1 – 9 thousand impressions a month, in 80 – 150 regions. Too small to be useful.
* Health Union, Sharecare and GoodRx have a few rows in January 2025, then nothing.
* PulsePoint DTC, The Trade Desk, Mediacom video, Healthline, CBS News and SingleCare: nothing in the last two years.

## 5. What this means for NBA (facts, not decisions)

* **NBA 3.0 DTC features no longer carry information.** At the next prediction (anchor 1 November 2026, looking back to 30 September 2026) the direct-buy features are zero and Facebook / Instagram stops in June 2026. In training, the direct-buy features mainly tell the model whether a row is from before or after 2025.
* **Paid search now has regional data, by state.** `FUNNEL_DATA_NEW_SA360_REGION` gives state-level paid search from July 2024 onwards. For DTC, NBA would either use the doctor's state, or split each state's numbers across its DMAs (for example by population). History before July 2024 is only in the DMA tab (to January 2025, with the 2023 issue in Q-D3).
* **DTC paid search is small and branded only.** About 0.1 – 0.2M impressions and 12 – 18K clicks a month. HCP paid search is about five times bigger and belongs with the HCP digital features, not DTC.
* **Facebook / Instagram behaves like a region-size measure.** If kept, it would need to be per person (for example impressions per 1,000 adults) to say anything about Kerendia pressure.
* **Data delay.** The copied DTC data is about three months behind the prediction date.
* **Pipeline gaps found:** NBA 3.0 ops reads `CPH_DB_PROD.ENRICH.FLASHTALKING_DMA` instead of FT V1; its DTC input files in the volume (`ops_pipeline/query_output/kerendia_nba_3_0_hcp_model_DirectBuys`, `..._social`, `ops_pipeline/notebook_output/DTC/*`) no longer exist; the current copies are the OE tables in `kerendia_oe_journey` (`_hcp_model_directbuys_inference`, `hcp_model_social_inference`, `dtc_pulsepoint_inference`, `dtc_ttd_display_inference`).
* **Two data issues to explain before any use:** the SA360 DMA tab shows 30 – 40 million impressions a month in April – August 2023 against less than 1 million in other months, and SA360 old and new disagree in Jan – Sep 2024.

## 6. Open questions for the meetings

Each question has a code so the answers can be recorded in section 7.

### A. Brand / DTC marketing team: the upcoming launch

| Code | Question | Why it matters |
| --- | --- | --- |
| Q-A1 | Which DTC channels are planned for the upcoming launch (paid search, Facebook / Instagram, connected TV / online video, programmatic display, health-website direct buys, GoodRx-type pharmacy sites, others)? | Decides which sources NBA 3.1 must read |
| Q-A2 | When does each channel start, and for how long? Is it always-on or in bursts (flights)? | NBA needs several months of history before a feature can be learned |
| Q-A3 | Will any channel be **targeted by region or ZIP code**, or is everything national? Is there a test-and-control region design? | National buys give the model almost nothing to learn; regional differences or test regions make DTC measurable |
| Q-A4 | Which indication is each campaign for (CKD with type 2 diabetes, heart failure)? Will campaign names show it? | Lets NBA split DTC by indication, in line with HCP features |
| Q-A5 | Expected size (budget or impressions) by channel compared with 2023? | Shows whether DTC will be big enough to matter in the model |
| Q-A6 | What were the reasons for stopping direct buys, programmatic display and video in 2024? | Helps judge whether 2023 – 2024 history is comparable to the new launch |

### B. Media agency / search team: paid search

| Code | Question | Why it matters |
| --- | --- | --- |
| Q-B1 | Is there a current paid-search report **with region (DMA)** after January 2025? Can the agency add region to `FUNNEL_NEW_SA360` or deliver a geo report? | Without region, paid search cannot be given to doctors by area |
| Q-B2 | If no region is available, is it acceptable to split national search by region using population or by the region shares seen up to January 2025? | Fallback option; needs business agreement |
| Q-B3 | Which SA360 campaigns are **patient (DTC)** and which are **HCP** search? Is there a naming rule (for example `KER_DTC_cpc_...`)? | HCP search must not be counted as DTC |
| Q-B4 | What do the campaign codes mean (`BRN` / `UNBR` = branded / unbranded; `GEN`, `SYM`, `TRE`, `DIA`, `MAN`, `COM`, `FIN`; `DK` / `MB` / `TB` = desktop / mobile / tablet)? | Lets features separate branded from disease-awareness search |
| Q-B5 | Why do Google / Bing rows in Flashtalking have clicks but no impressions, and why do they stop in October 2025 (Bing) and January 2026 (Google)? | Decides whether Flashtalking search clicks can be used at all |
| Q-B6 | Why did the number of campaigns rise from 36 to more than 100 from July 2025? New campaigns or a naming / structure change? | A structure change could look like a jump in activity |
| Q-B7 | `FUNNEL_DATA_NEW_SA360_REGION` is by **state** and has no Metro column (`GEO_TARGETS__NEW_SEARCH_ADS_360` is empty). Can the agency add the SA360 **Metro** dimension to this feed? If not, is state level, or a split of states into Metros by population, acceptable? | NBA 3.0 DTC features are per DMA (= Metro) |
| Q-B8 | Are "San Francisco Bay Area" and "Silicon Valley" counted **in addition** to California, or inside it? | Avoid double counting California |
| Q-B9 | Why does the state table find only 64 – 78% of HCP search clicks from June 2026 (against 83 – 98% before)? | Missing rows would understate recent HCP search |
| Q-B10 | Why did DTC search run in only 6 states (TX, CA, FL, NY, GA, NC) from July to December 2024? Was it a planned regional test? | A planned regional test is the best way to learn the effect of DTC |

### C. Social and video

| Code | Question | Why it matters |
| --- | --- | --- |
| Q-C1 | Is Facebook / Instagram targeted by region, or delivered nationally? | If national, its regional numbers only reflect population |
| Q-C2 | What happened in May 2026 (2.3% of impressions clicked against the usual 0.5 – 0.7%)? A special campaign, a reporting change, or invalid clicks? | Outlier to fix or remove before training |
| Q-C3 | Will connected TV / online video come back? If yes, which partners, and will the data come through Flashtalking (FT V1) with region? | NBA 3.0 never loaded video |

### D. Data engineering / data owners

| Code | Question | Why it matters |
| --- | --- | --- |
| Q-D1 | Confirm FT V1 as the Flashtalking source for NBA 3.1. Why did NBA 3.0 ops switch to `CPH_DB_PROD.ENRICH.FLASHTALKING_DMA`, and do the two agree? | Avoid using two different versions of the same data |
| Q-D2 | SA360 old and new overlap in Jan – Sep 2024 but give different totals (for example January 2024: about 3.8M impressions / 512K clicks in old vs 1.9M / 256K in new). Which is right, and is the 30 Sep / 1 Oct 2024 cut-over enough to avoid double counting? | Needed to build one consistent paid-search history |
| Q-D3 | What explains the 30 – 40 million impressions a month in the SA360 DMA tab in April – August 2023? | Possible data error in the only regional search history |
| Q-D4 | How often are FT V1, `FUNNEL_NEW_SA360` and the Facebook table refreshed, and how far behind are they? | Sets the realistic lookback for DTC features at prediction time |
| Q-D5 | Who owns the DMA-to-doctor link (DMA codes and names file, doctor ZIP to DMA), and is it current? | Every DTC feature depends on it |
| Q-D6 | Is `PHCDW.PHCDW_CDM.DMA_DATA_SA360_BING_COMBINED` (used by the older monthly-production pipeline) still updated, and does it have region after January 2025? | Possible ready-made regional search source |

## 7. Answers (to fill in after the meetings)

| Code | Answer | Source (who / meeting / date) |
| --- | --- | --- |
| Q-A1 | | |
| Q-A2 | | |
| Q-A3 | | |
| Q-A4 | | |
| Q-A5 | | |
| Q-A6 | | |
| Q-B1 | Partly answered: use `FUNNEL_DATA_NEW_SA360_REGION` for regional SA360 (Jul 2024 – present). It is by **state**, not DMA (see Q-B7). | User, 26 Oct 2026; profiled the same day |
| Q-B2 | | |
| Q-B3 | Partly answered from the data: campaign names start with `KER_DTC_` (6 campaigns, branded only) or `KER_HCP_` (147). To confirm with the search team that this rule is reliable. | Profiling of `FUNNEL_DATA_NEW_SA360_REGION`, 26 Oct 2026 |
| Q-B4 | | |
| Q-B5 | | |
| Q-B6 | | |
| Q-B7 | | |
| Q-B8 | | |
| Q-B9 | | |
| Q-B10 | | |
| Q-C1 | | |
| Q-C2 | | |
| Q-C3 | | |
| Q-D1 | | |
| Q-D2 | | |
| Q-D3 | | |
| Q-D4 | | |
| Q-D5 | | |
| Q-D6 | | |

## 8. References

* `20_dtc_direct_buy_social_nba_3_0.md`: how the NBA 3.0 DTC features are built
* `30_nba_3_1_proposed_additional_features.md`, section 3: earlier DTC feature ideas for NBA 3.1
* NBA 3.0 ops: `kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/00_Write_Input_Files` (DTC queries) and `34_promotional_features_DTC` (DTC features)
* OE 2.0: `OE/Kerendia_OE_2.0/NBA_Notebooks/03_Feature_Engineering/03_HCP_Level_Features/00_Write_Input_Files` (reads FT V1)
* Older monthly production: `kerendia_nba_monthly_production/Feature_Engineering/00_Write_Input_Files` (also read connected TV, video, audio and SA360 with region)
* NBA 3.0 model: MLflow run `f583bcbc9d56477fae983d44c16f8c70` (9 DTC features kept, best rank 32)
