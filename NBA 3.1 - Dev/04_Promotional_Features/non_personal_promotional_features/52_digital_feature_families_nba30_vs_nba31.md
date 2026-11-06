# Digital Feature Families: NBA 3.0 vs NBA 3.1

**Group:** Non-personal promotional features (HCP digital, high-intent signals, DTC)  
**Based on:** `50_digital_nba_3_1_readiness_plan.md` (section 4), `10_hcp_digital_paid_media_nba_3_0.md`, `11_hcp_hq_emails_nba_3_0.md`, `20_dtc_direct_buy_social_nba_3_0.md`, `13_hcp_digital_nba_3_1_readiness_plan.md`, the notebook `50_digital_nba_phase0_validation`, and new checks on `kerendia_oe_journey.mmx_fnl_combined_aggr_tab` run on 5 November 2026 (Kerendia rows, January 2025 to October 2026)  
**Date:** November 5, 2026

Note: iRep email and CLM / clickstream are part of the **personal** promotional block and are not covered here.

---

## 1. Rules shared by all NBA 3.1 families

* **Doctor key:** NPI (BH_ID to NPI through `kerendia_oe_npi_bhid_mapping_inference`).
* **Windows:** only complete months before the anchor date (1, 3, 6, 12 months); no `RUNNING_` features.
* **Schema:** fixed and generated from config tables, replacing the dynamic pivots used in NBA 3.0.

---

## 2. Words you need first (glossary)

| Word | Plain meaning |
| --- | --- |
| **Feature** | One number about a doctor that the model uses, e.g. "banner ads seen in the last 3 months". |
| **NBA model** | The Next Best Action model. It ranks doctors and suggests the next Kerendia action. NBA 3.0 is the current version, NBA 3.1 the next one. |
| **Rank (SHAP rank)** | How useful a feature is to the model. Rank 1 = most useful. NBA 3.0 has 752 features, so rank 700 means almost useless. |
| **MMX table** | Bayer's marketing-mix table. One row = one doctor, one day, one vendor, one tactic, with counts of exposure and engagement. Main source for HCP digital. |
| **Vendor** | The company that shows our content to doctors (Doximity, Medscape, PulsePoint, Epocrates, ...). Column `SRC_SYS_CD`. |
| **Tactic / placement** | The format or the exact "spot" inside a vendor, e.g. Doximity DocSpot, Epocrates Monograph Message. A placement = vendor + tactic. |
| **Exposure** | How many times the doctor was **shown** or **sent** the content. |
| **Engagement** (light / deep / total) | How many times the doctor **reacted** (opened, viewed, clicked). Light / deep are Bayer's internal definitions, not reported by vendors. |
| **Pivot (dynamic)** | Turning row values into columns. "Dynamic" = the columns are created from whatever values exist on the day of the run, so the list of features changes between runs. |
| **Window / anchor date** | The anchor is the "as of" date of a prediction. A 3-month window = the 3 complete months before the anchor. |
| **Leakage** | Using information that would not have been known at the anchor date. It makes a model look better in testing than it really is. |
| **DMA** | One of about 210 US media regions (roughly one per big city). Used for patient (DTC) ads. |
| **OE** | Omnichannel Engine: a separate Bayer system that decides *when* and *what* digital content to send each week. NBA decides *who* and *why*. |

---

## 3. Family-by-family explanation (with data)

Each family follows the same five headings: **what it is**, **what NBA 3.0 had**, **what the data shows**, **what changes in NBA 3.1**, **why**.

Sources of the numbers: **[Q]** = my query on the MMX table in Unity Catalog on 5 November 2026; **[P0]** = Phase 0 validation notebook; **[Doc]** = the NBA 3.0 / 3.1 documents in this folder (Snowflake checks I did not repeat).

### 3.0 Starting point: digital is weak in NBA 3.0

Only **18 of 752** NBA 3.0 features are non-personal promotion. Their ranks [Doc, `12_...`]:

| Rank (of 752) | Feature | Family |
| --- | --- | --- |
| 32 | `DTC_PROMOTION_HEALTH_UNION_TOTAL_IMPRESSIONS` | 4 DTC |
| 68 | `DIGITAL_BANNER_TACTIC_EXPOSURE_IN_LAST_3_MONTH` | 1 HCP paid media |
| 93 / 124 | `DTC_PROMOTION_FB_AND_IG_TOTAL_CLICKS` / `_IMPRESSIONS` | 4 DTC |
| 107 | `DTC_PROMOTION_WEBMD_TOTAL_IMPRESSIONS` | 4 DTC |
| 151 / 200 / 644 | `DIGITAL_RUNNING_BANNER_EXPOSURE`, `DIGITAL_BANNER_EXPOSURE_IN_LAST_3_MONTH`, `..._1_MONTH` | 1 HCP paid media |
| 283 to 632 | Sharecare, Health Union clicks, WebMD clicks, Healthline | 4 DTC |
| 688 / 695 / 698 | HQ email exposure / light engagement (from MMX) | 2 HQ email (duplicate) |
| 738 / 743 | iRep email exposure (from MMX) | personal block (duplicate) |

How to read this: the best HCP digital feature is only rank 68, the best DTC feature is a vendor that has stopped, and the email features are at the bottom. No feature names a media partner (Doximity, Medscape, Epocrates, ...). So the goal of NBA 3.1 is **a smaller, cleaner and more meaningful block**, not more columns.

---

### 3.1 Family 1: HCP paid media

**What it is.** Ads, sponsored messages and 3rd-party emails that doctors see on medical websites and apps (Doximity, Medscape, Epocrates, PulsePoint, ...).

**What NBA 3.0 had.** Notebook `24_Features_Digital` read MMX, kept only rows with brand exactly `KERENDIA`, and built three dynamic pivots (by channel, by vendor, by tactic) x 4 measures x 1 / 3 / 6 months and "running" totals. Result: **684 columns**, of which the model kept 9 (mostly banner, HQ email, iRep email).

**What the data shows.**

*Evidence A: the brand filter throws away data* [Q]. Kerendia rows carry indication-specific brand values (`KERENDIA HF`, `KERENDIA_CKD`, `KERENDIA UACR`, ...). NBA 3.0 only kept the exact value `KERENDIA`:

| Vendor | Exposure, all Kerendia brand values | Exposure kept by NBA 3.0 | Share dropped |
| --- | --- | --- | --- |
| Doceree | 854,996 | 98,527 | **88.5%** |
| ReachMD | 46,329 | 6,240 | **86.5%** |
| PeerDirect | 502,571 | 164,369 | **67.3%** |
| Doximity | 1,452,826 | 1,450,873 | 0.1% |
| All other vendors | | | 0% |

*Evidence B: the rank-68 banner feature is a calendar marker, not a media effect* [Q]. Monthly exposure for tactics whose name contains "Banner":

| Month | All Kerendia brand values | With NBA 3.0 filter |
| --- | --- | --- |
| Jan to Mar 2025 | 0 | 0 |
| Apr 2025 | 850 | 0 |
| Jun 2025 | 11,702 | 0 |
| Jul 2025 | 33,970 | 32,892 |
| Sep 2025 | 1,556 | 0 |
| Nov 2025 | 82,652 | 34,138 |
| Dec 2025 | 43,635 | 0 |
| Mar 2026 | 77,487 | 3,559 |
| Oct 2026 | 83,520 | 3,577 |

The feature is zero until April 2025 (when Doceree, OpenEvidence and PeerDirect banners started), and with the NBA 3.0 filter it switches on and off from month to month. A model can learn "after April 2025" from it, not "banners work".

*Evidence C: one vendor dominates the totals* [Q]. PulsePoint (programmatic display) has 109.3M of the 111.0M banner exposures (**98.5%**) and **93.7%** of all paid-media exposure (banner + custom + 3rd-party email, 116.6M). But doctors react to it very rarely:

| Vendor / channel | Exposure | Engagement | Engagement per exposure |
| --- | --- | --- | --- |
| PulsePoint banner | 109,297,058 | 83,898 | 0.08% |
| Medscape 3rd-party email | 754,668 | 337,909 | 44.8% |
| Epocrates custom | 182,828 | 83,553 | 45.7% |
| Doximity custom | 1,452,826 | 154,700 | 10.6% |

A plain "total exposure" therefore mostly measures PulsePoint. Smaller placements with much higher response are hidden inside it.

*Evidence D: the vendor list keeps changing* [Q]. Number of paid-media vendors active per month: 4 (Jan 2025), 8 (Apr 2025), 14 (Dec 2025), 6 (Oct 2026). With a dynamic pivot, each change adds or removes columns.

**What changes in NBA 3.1.**

* Keep **all** Kerendia brand values (and use them for the indication, see 3.6).
* A fixed **placement dictionary**: every vendor kept on its own (including small ones such as Impiricus, MDCalc, Biopharm), case-insensitive mapping, and a report of unmapped rows.
* A **fixed list** of features, built for complete months only, with no `RUNNING_` features.
* New kinds of features (P1 to P7 in `13_...`): totals; channel totals (with and without PulsePoint); vendor x placement totals (about 60 to 80); engagement rates; recency (days since last exposure / engagement); diversity (number of vendors, placements, active months); trend (last 3 months vs the 3 before).
* Remove calls, samples, HQ email and iRep email from this family (they have their own families).

**Why.** Evidence A: up to 88% of some vendors' data was missing. Evidence B: the best feature was a period marker. Evidence C: totals hide the placements that doctors actually respond to; rates and placement detail separate "shown a lot" from "responds". OE's own model found its strongest digital features at placement level (Epocrates, Prescriber Point, Doximity DocSpot) [Doc, `12_...`]. Evidence D: a fixed list is needed so the model gets the same columns at every run.

---

### 3.2 Family 2: HQ email

**What it is.** Marketing emails sent by Bayer head office (SFMC), and what the doctor did: opened, clicked, unsubscribed, or the email bounced.

**What NBA 3.0 had.** Notebook `15_promotional_features_HQ_Emails`: 5 counts over the last 3 months (`TOTAL_SENT`, `TOTAL_OPEN`, `TOTAL_CLICK`, `TOTAL_BOUNCE`, `TOTAL_UNSUBSCRIBE`). **None of these 5 was kept by the model.** The same emails also came in through MMX (as a channel and as a vendor) and those copies were kept, at ranks 688, 695 and 698.

**What the data shows.**

* HQ email in MMX: 3,837,466 exposures for 188,780 doctors (Jan 2025 to Oct 2026) [Q]. So the same activity was counted in notebook 15 **and twice** in Digital.
* Delivered-email log (`FACT_SENT_EMAIL`): 438,854 delivered, 29.4% opened, 9.2% clicked; open rate fell from about 37% (early 2025) to about 20% (Oct 2026) [P0]. The MMX and email-log volumes are very different, so the two sources do not describe the activity in the same way; this has to be reconciled before choosing.
* Repeat opens count every time in NBA 3.0, so "open" can be higher than "sent" [Doc, `11_...`].

**What changes in NBA 3.1.** One source only (the email event log); HQ email removed from MMX features. About 12 features: sent, **unique** open and click, open rate, click rate, bounce flag, unsubscribe status, days since last open.

**Why.** Counting the same email three times gives the model three correlated copies of one signal. Rates and unique counts separate "we emailed a lot" from "the doctor reads our emails", which matters more now that open rates are falling. An unsubscribe tells NBA not to recommend email.

**Status note.** In the Phase 1 run (notebook 51), the Snowflake email log failed (view compilation error), so MMX was used as a fallback and bounce / unsubscribe were empty.

---

### 3.3 Family 3: High-intent signals (new)

**What it is.** Moments when the doctor **asked** for something (Request-a-Rep form), started prescribing (New Writer), engaged by SMS (Impiricus), or a strong market event happened (health-system formulary win).

**What NBA 3.0 had.** Nothing.

**Source tables.** This family has no single source; each signal comes from a different place [Doc, `50_...` section 5]:

| Signal | Source table | Doctor key | Status | Action needed |
| --- | --- | --- | --- | --- |
| Request-a-Rep (priority) | `PHCDW.PHCDW_CDM.RPT_DIGITAL_RAR_TAB` (Snowflake, refreshed daily); raw history from January 2024 in `KERENDIA_HCP_RAR_EXTRACTS` | BH_ID (almost all rows); NPI on about 46% | Found | Filter on `BRAND_NAME`; map BH_ID to NPI via `kerendia_oe_npi_bhid_mapping_inference`; do not copy name / email / phone |
| New Writer | No separate table: first Kerendia Rx per doctor from the claims data behind the NBA 3.1 Rx features | NPI + first Rx date | To confirm | Agree the definition (lookback, claims source) with OE's dynamic target list |
| Impiricus SMS | MMX: `PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB` (UC copy `kerendia_oe_journey.mmx_fnl_combined_aggr_tab`), vendor `IMPIRICUS`, tactic `SMS Messages` | NPI | Partial | Confirm where 2026 data lands (no rows after December 2025) |
| Health-system formulary wins | Not located yet | Health system, linked to doctors via MDM best affiliation | Missing | Digital / OE team to provide source and format |

Key columns of `RPT_DIGITAL_RAR_TAB` [P0]: `TRANSACTION_ID`, `BRAND_NAME`, `BH_ID`, `NPI`, `CREATE_DATE` (request date), `REQUEST_TYPE`, `REP_TYPE`, `CALL_DATE` (follow-up call), `WEBFORM_SOURCE`, `UTM_SOURCE` / `UTM_MEDIUM` / `UTM_CAMPAIGN`.

**The Request-a-Rep table explained (`PHCDW.PHCDW_CDM.RPT_DIGITAL_RAR_TAB`).** A small reporting table of **requests doctors send through the form on Bayer's HCP brand websites** ("send me samples", "have a rep contact me", "send patient support information"). One row per request, plus whether a rep **followed up** (call, sample, iRep email, HQ email) and how many days later. RAR most likely stands for **Request a Rep**.

**Size and coverage** (Snowflake, queried 5 Nov 2026):

* **5,818 rows**, one per request (`TRANSACTION_ID` unique).
* Requests from **1 Jan 2025 to 4 Nov 2026**; every row has `SOURCE_CD = 'HCP_SITE'` (brand website form).
* 12 brands: Mirena 2,509, **Kerendia 1,385**, Lynkuet 597, Kyleena 395, Nubeqa 288, Adempas 232, and 6 smaller ones.
* Table created **15 Sep 2026**, last refreshed 5 Nov 2026, so the 2025 history was loaded in one go.

**Schema (66 columns), grouped:**

| Group | Columns | What they hold |
| --- | --- | --- |
| Request | `TRANSACTION_ID`, `CREATE_DATE`, `REQUEST_WEEK`, `REQUEST_MONTH`, `BRAND_NAME`, `REQUEST_TYPE`, `REQUEST_DETAILS`, `REP_TYPE` | ID, date, brand, what was asked for, which kind of rep (`REQUEST_WEEK` / `REQUEST_MONTH` are week-end / month-end dates stored as text) |
| Doctor identity | `BH_ID`, `NPI`, `HCP_ID`, `MASTERED_NON_MASTERED`, `HCP_STATUS`, `HCP_TYPE`, `SPECIALTY`, `TITLE`, `GENDER`, `TARGET_SEGMENT` | Bayer ID, NPI, matched to the customer master or not, status (A = active), type (P = prescriber), segment |
| Personal data (PII) | `FIRSTNAME`, `LASTNAME`, `EMAIL`, `PHONE`, `ADDRESS_LINE_1/2`, `CITY`, `STATE`, `POSTAL_CODE`, `PRIMARY_COUNTRY` | What the doctor typed into the form. **Not to be read by the feature pipeline** |
| Territory and rep | `SRC_TERR_CD`, `TERR_NUM`, `TERRITORY`, `REGN_CD`, `REGION`, `AREA_CD`, `AREA`, `REP_EMAIL_ADDRESS`, `REP_MANAGER_EMAIL_ADDRESS`, `EMAIL_ADDRESS` | Who the request was routed to |
| Web source | `SOURCE_CD`, `REFERRAL`, `UTM`, `UTM_SOURCE`, `UTM_MEDIUM`, `UTM_CAMPAIGN`, `LANDING_PAGE_URL`, `WEBFORM_SOURCE` | How the doctor reached the form (Google ad, CRM email, organic search, ...) |
| Follow-up: call | `CALL` (0 / 1), `CALL_DATE`, `LAG_TIME_CALL` | Whether and when a rep called after the request (days) |
| Follow-up: sample | `SAMPLE_DATE`, `LAG_TIME_SAMPLE` | Sample after the request |
| Follow-up: iRep email | `SENT_IREP` (0 / 1), `IREP_EMAIL_SENT_DATE`, `LAG_TIME_IREP`, `CLICKED_IREP`, `VIEWED_IREP`, `DELIVERED_IREP` | iRep email after the request |
| Follow-up: HQ email | `SENT_HQ`, `HQ_EMAIL_SENT_DATE`, `LAG_HQ`, `CLICKED_HQ`, `VIEWED_HQ`, `DELIVERED_HQ` | HQ email after the request |
| Other | `LAG_TIME_REP`, `NA1`, `NA2` | Placeholders |

**Kerendia rows (1,385 requests).**

* **1,214 doctors**; 1,138 asked once, a few asked repeatedly (one doctor 18 times). `BH_ID` filled on 98.6% of rows, `NPI` on only half.
* 55 – 190 requests a quarter, with a spike to **421 in Q1 2026**.
* Follow-up: **29.7% followed by a call** (median 9 days; 25% within 3 days, 75% within 36; no call dated before the request); **273 followed by a sample**; only **10 by an iRep email**; HQ email follow-up never filled.

| Request type | Requests | Followed by a call | Median days to call | Followed by a sample |
| --- | --- | --- | --- | --- |
| `Samples` | 581 | 52.3% | 8 | 224 |
| `Contact by Rep` | 521 | **7.1%** | 17 | 15 |
| Empty | 187 | 31.0% | 7 | 31 |
| `News & Announcements` | 54 | 13.0% | 93 | 1 |
| `Other` | 42 | 11.9% | 10 | 2 |

**Data quality points.**

* **Completely empty columns:** `REQUEST_DETAILS`, `WEBFORM_SOURCE`, `NA1`, `NA2`, `LAG_TIME_REP`, `CLICKED_IREP`, and every HQ follow-up column (`SENT_HQ`, `HQ_EMAIL_SENT_DATE`, `LAG_HQ`, `CLICKED_HQ`, `VIEWED_HQ`, `DELIVERED_HQ`).
* **`REQUEST_TYPE` can hold several values in one text** (e.g. `News & Announcements, Contact by Rep, Clinical Data`) and has a typo (`Full Prescribing Information Information`).
* **`REP_TYPE` sometimes holds request-type text** (about 115 rows): values look shifted.
* **"Contact by Rep" is rarely followed by a call (7.1%).** Either the call is logged without a link, or the follow-up matching misses it. To ask the table owner.
* **Follow-up columns are outcomes after the request.** They may be used only when the follow-up date is on or before the cohort cutoff (leakage rule below).

**What the data shows.**

* Request-a-Rep [Doc, `40_...`]: 1,218 Kerendia requests (Jan 2025 to Oct 2026); only **340 (28%)** were followed by a rep call, after a median of 7 to 9 days, so about **880 requests had no follow-up call**. BH_ID on almost every row, NPI on only about 46%. The table exists and has 66 columns; its brand column is `BRAND_NAME`, not `BRND_NM` [P0].
* Impiricus SMS [Q]: exposure only in Mar, Apr, Jun, Nov and Dec 2025, about 10,000 doctors, and **zero in 2026**.
* New Writer: definition still to be agreed with OE. Formulary wins: source not found yet [Doc].

**What changes in NBA 3.1.** About 10 to 15 features such as `RAR_LAST_6M_FLAG`, `RAR_COUNT_12M`, `DAYS_SINCE_LAST_RAR`, `RAR_TYPE_SAMPLES_FLAG`, `NEW_WRITER_LAST_3M_FLAG`, `SMS_ENGAGED_3M_FLAG`, `FORMULARY_WIN_AFFIL_6M_FLAG`. Plus a **business rule**: a doctor with an open request (no follow-up call yet) is always shown in the NBA dropdown list with the reason "requested a rep on <date>".

**RAR features: two levels.** RAR features are built (a) on **all RAR events** and (b) on **each type of RAR follow-up: Call, Samples, iRep email and HQ email**.

| Level | Events counted | Example features | Source columns |
| --- | --- | --- | --- |
| All RAR events | Every Kerendia request (`BRAND_NAME = 'KERENDIA'`), whatever was asked and whatever followed | `RAR_COUNT_3M / 6M / 12M`, `RAR_LAST_6M_FLAG`, `DAYS_SINCE_LAST_RAR`, `RAR_OPEN_REQUEST_FLAG` | `CREATE_DATE` |
| RAR + Call | Requests followed by a rep call | `RAR_CALL_COUNT_12M`, `RAR_CALL_SHARE_12M` (share of requests answered by a call), `RAR_OPEN_NO_CALL_FLAG` | `CALL`, `CALL_DATE`, `LAG_TIME_CALL` |
| RAR + Samples | Requests followed by a sample | `RAR_SAMPLE_COUNT_12M`, `RAR_SAMPLE_SHARE_12M`, `RAR_OPEN_NO_SAMPLE_FLAG` | `SAMPLE_DATE`, `LAG_TIME_SAMPLE` |
| RAR + iRep email | Requests followed by an iRep email | `RAR_IREP_COUNT_12M`, `RAR_IREP_SHARE_12M` | `SENT_IREP`, `IREP_EMAIL_SENT_DATE`, `LAG_TIME_IREP` |
| RAR + HQ email | Requests followed by an HQ email | `RAR_HQ_COUNT_12M`, `RAR_HQ_SHARE_12M` | `SENT_HQ`, `HQ_EMAIL_SENT_DATE`, `LAG_HQ` |

Rules for the type-level features:

* **Leakage:** a follow-up counts only if its date (`CALL_DATE`, `SAMPLE_DATE`, `IREP_EMAIL_SENT_DATE`, `HQ_EMAIL_SENT_DATE`) is **on or before the cohort cutoff**; otherwise the request is still "open" for that type at the cutoff.
* **Expected sparsity (Kerendia):** Call 411 of 1,385 requests, Samples 273, iRep 10, HQ email 0 (columns empty today). iRep and HQ email features are built so the schema is fixed, but will be almost all zero until the table owner fills the HQ columns; review them after E6.
* Request type (`Samples`, `Contact by Rep`, ...) stays a separate feature (`RAR_TYPE_SAMPLES_FLAG`), since what the doctor asked for differs from what the rep did.

**Why.** A doctor asking for a rep is the clearest signal of interest that exists, and 880 requests went unanswered. Because these events are rare (about 1,200 versus tens of thousands of doctors), the model alone may not learn them reliably, hence the extra business rule. **Leakage rule:** only use what was known at the anchor date; a call made after the anchor must not mark a request as answered.

---

### 3.4 Family 4: DTC market context

**What it is.** Kerendia ads shown to **patients** (not doctors) in the doctor's area. It is background, not something a rep can act on.

**What NBA 3.0 had.** Notebook `34_promotional_features_DTC`: impressions and clicks per DMA and month for Health Union, Healthline, Sharecare, WebMD and Facebook + Instagram (10 columns). PulsePoint and The Trade Desk DTC were loaded but never used. Missing values were left empty instead of 0.

**What the data shows** [Doc, `21_...`].

* The best non-personal feature in the model (Health Union impressions, rank 32) and the other direct-buy features have been **zero since early 2025**: the vendors stopped. Only a trace of WebMD remains (about 2 to 3 thousand impressions a month).
* The NBA 3.0 DTC input files no longer exist. The Facebook + Instagram source itself has no data after June 2026 (confirmed in Phase 0, below), while the next prediction looks back to 30 September 2026.
* What still runs: Facebook + Instagram (by DMA) and SA360 paid search. NBA 3.0 never used paid search. DTC branded search = 6 of 153 campaigns, about 15% of Kerendia search clicks, 12 to 18 thousand clicks a month; 1.47M impressions in 2025 and about 1.38M in Jan to Oct 2026 [P0].
* Paid search is available by **US state** only: DMA (Metro) stopped in January 2025.
* Regions rank almost identically each year (rank correlation 0.98), so raw totals mostly measure **region size**, not Kerendia pressure.

*Phase 0 check of the two sources that still run* [P0, run 5 November 2026, Jan 2025 to Oct 2026, after fixing the queries]:

| Source | Grain | Coverage | Volume | Issues |
| --- | --- | --- | --- | --- |
| Facebook + Instagram (`FUNNEL_DATA_FACEBOOKADS_GEO_DMA`, `DATA_SOURCE_NAME = 'Bayer_Kerendia'`) | DMA x day | 211 DMAs every month; Jan 2025 to **Jun 2026** only | 41.7M impressions in 2025, 22.3M in Jan to Jun 2026; 11.7K to 32.2K clicks a month | No rows Jul to Oct 2026; May 2026 has 105,643 clicks (2.31% of impressions vs the usual 0.5 to 0.7%); Aug 2025 has far fewer rows (24,842) with normal impressions |
| SA360 DTC search (`FUNNEL_DATA_NEW_SA360_REGION`, campaigns `KER_DTC_`) | State x day | 53 regions (50 states + DC + 2 Google regions); all 22 months | 6 campaigns; 2.85M impressions and 333K clicks (1.47M / 186K in 2025); 11.6K to 18.5K clicks a month | State only, no DMA |
| SA360 HCP search (campaigns `KER_HCP_`), for comparison | State x day | 53 regions; all 22 months | 30 campaigns (Jan 2025) growing to 110 (Oct 2026); 11.9M impressions, 1.81M clicks | Doctor search, not patient search: **84.4%** of Kerendia search clicks, so it must not be counted as DTC |

How to read this: the social feed is the bigger DTC source but **stops in June 2026**, so for the next prediction (last complete months July to September 2026) it would be empty, the same problem NBA 3.0 had with the direct buys. DTC search is small but steady and still running. The phase 0 numbers match those in `21_...`, which confirms the filters.

**What changes in NBA 3.1.** Drop the four direct-buy vendors. Keep Facebook + Instagram at DMA x month, lagged one month, **per 1,000 adults**. Add SA360 DTC branded search (`KER_DTC_` campaigns only) at **state** x month, per 1,000 adults. Add `DTC_MONTHS_SINCE_LAST_CAMPAIGN`. Only 4 to 8 features.

**Open points from Phase 0 before building.**

* Confirm with the DTC team whether Facebook + Instagram stopped after June 2026 or the feed is late (Q-D4 in `21_...`). If it stopped, `DTC_MONTHS_SINCE_LAST_CAMPAIGN` is the only honest social feature.
* Fix or exclude the May 2026 click outlier (Q-C2), and check the August 2025 row drop.
* Decide whether a doctor gets the numbers of their state, or a population-based split of the state into DMAs (Q-B7).

**Why.** A feature that is always zero at prediction time but was non-zero in training only tells the model "this is the old period". Per-1,000-adults removes the region-size effect. The block stays small because there are only about 210 DMAs and 50 states, so there is little independent information.

---

### 3.5 Family 5: Engagement depth and content (later phase)

**What it is.** A finer view of digital: did the doctor only see it (reach), interact with it, or engage deeply, and **what topic** was the content about (guidelines, access, safety, ...).

**What NBA 3.0 had.** Nothing. No content, no recency, no placement. None of the 24 CLM features was kept.

**What the data shows.**

* NBA 3.0's light / deep definition is not written down, and "total" is not light + deep. Example for HQ email, March 2026: light 26,341, total 26,341, deep 1,446 [Doc, `10_...`]. The model kept **no** deep-engagement feature [Doc, `12_...`].
* OE has a documented mapping of 160 rules for reach / interaction / engagement (R / I / E) per vendor metric, and its feature selection kept all 13 content-category counts [Doc, `12_...`].
* The OE event table exists but uses `CUST_ID` and `DATE_ID`, so it needs a mapping to BH_ID / NPI before use [P0].

**What changes in NBA 3.1.** Reuse OE's R / I / E flags per placement for the five vendors with event-level data (Doximity, Medscape, PeerDirect, PulsePoint, SFMC), e.g. `DIGITAL_EVT_DOXIMITY_DOCSPOT_E_3M`; add content-category counts; add the new iVA campaign once campaign and content IDs exist. About 40 to 60 features. They replace the family 1 placement features for those five vendors **only if** they test better (experiment E4 vs E3).

**Why.** Documented definitions make the features explainable and consistent with OE. Content is the dimension OE found useful and NBA does not have at all. It comes later because the ID mapping and content tagging are not ready.

---

### 3.6 Indication dimension (across families)

**What it is.** Splitting the main totals by indication: heart failure (HF), type 1 diabetes (T1D), chronic kidney disease (CKD).

**What NBA 3.0 had.** Nothing; the brand filter actually removed indication-tagged rows.

**What the data shows** [Q]. The indication is in the brand value, e.g. Doceree uses `KERENDIA CKD`, `KERENDIA HF`, `KERENDIA UACR`; PeerDirect uses `KERENDIA_HF`, `KERENDIA_CKD`; ReachMD uses `KERENDIA-CKD`, `KERENDIA-HF`. These are the rows NBA 3.0 dropped (Evidence A above).

**What changes in NBA 3.1.** 6 to 12 features such as `DIGITAL_HF_EXPOSURE_3M`, using the Q4 target-list rule (HF = cardiologists, T1D = T1D target list, CKD = remaining doctors).

**Why.** Kerendia now promotes several indications to different doctor groups. Without the split, an HF campaign to cardiologists and a CKD campaign to nephrologists look the same to the model.

---

## 4. Quick summary table

| # | Family | NBA 3.0 | What Wenjie wants in NBA 3.1 |
| --- | --- | --- | --- |
| 1 | **HCP paid media** | `24_Features_Digital` on MMX: dynamic pivots by channel, vendor and tactic, giving 684 columns. Only `BRND_NM = 'KERENDIA'` was kept, which dropped 88% of Doceree and 74% of PeerDirect rows. Tactic names had to match exactly, so renamed ones fell into `OTHER_TACTIC`. The first lookback month was dropped and the unfinished current month was included. The model kept 9 features: PulsePoint banner, `BANNER_TACTIC` (rank 68, mostly a marker for the period after April 2025), plus HQ and iRep email duplicates. None was a media-partner placement. | A placement dictionary with every vendor kept on its own (including Impiricus, MDCalc, Biopharm) and an unmapped-rows report. Features: totals (P1), channels (P2), vendor x placement (P3, about 60 to 80), engagement rates (P4), recency (P5), diversity such as number of vendors / placements / active months (P6), and trend vs the prior 3 months (P7). About 100 to 140 candidates. |
| 2 | **HQ email** | `15_promotional_features_HQ_Emails`: 5 counts over 3 months (sent, open, click, bounce, unsubscribe) from a dynamic pivot. Repeat opens were counted each time. The same emails were also counted in Digital as a channel and as a vendor, so three times in total. | One source only (the SFMC event log), with HQ email removed from MMX. About 12 features: sent, unique open and click, open and click rates, bounce flag, unsubscribe status, days since last open. |
| 3 | **High-intent signals** (new) | Did not exist. | Request-a-Rep first: flag, count, recency, request type, and follow-up status as of the anchor date (to avoid leakage). Then New Writer, Impiricus SMS and health-system formulary wins. About 10 to 15 features. Also a business rule: a doctor with an open request always appears in the NBA dropdown list. |
| 4 | **DTC market context** | `34_promotional_features_DTC`: DMA x month impressions and clicks per vendor (Health Union, Healthline, Sharecare, WebMD, FB+IG), 10 columns. PulsePoint and The Trade Desk were loaded but never used. Missing values were left empty (NULL) instead of 0. 4 of the 9 DTC features the model kept describe vendors that stopped by early 2025. | Drop the stopped direct-buy vendors. Keep FB+IG at DMA level, lagged one month and per 1,000 adults. Add SA360 branded search at state level only, because DMA-level (Metro) data is no longer delivered. Treat it as a control, not a doctor action. Keep it small: 4 to 8 features. |
| 5 | **Engagement depth and content** (later) | Did not exist. None of the 24 CLM features was kept, and there were no content, recency or placement features. | Reuse OE's reach / interaction / engagement (R / I / E) flags per placement for five vendors (Doximity, Medscape, PeerDirect, PulsePoint, SFMC) from `kerendia_oe_journey.oe_kerendia_fact_npp_inference`. Add content-category counts (13 categories + `GENERAL`), and the new iVA campaign once its campaign and content IDs exist. About 40 to 60 features. These replace the family 1 placement features for those five vendors only if they test better (E4 vs E3). |
| all | **Indication dimension** | Not used; the brand filter dropped indication-tagged rows. | HF / T1D / CKD split of the main totals using the Q4 target-list rule (HF = cardiologists, T1D = T1D target list, CKD = remaining HCPs), e.g. `DIGITAL_HF_EXPOSURE_3M`. 6 to 12 features. |

The plan expects about 30 to 60 digital features to survive feature selection, compared with 18 kept in NBA 3.0 (9 HCP digital, 9 DTC).

---

## 5. Phase 0 data checks (from `50_digital_nba_phase0_validation`)

| Family | Status | Finding |
| --- | --- | --- |
| 1. HCP paid media | Ready | About 130M Kerendia MMX rows over 22 months; 8 to 20 vendors per month |
| 2. HQ email | Ready | 438,854 delivered emails; open rate falling from about 37% to about 20% |
| 3. Request-a-Rep | Exists | Brand column is `BRAND_NAME`, not `BRND_NM` |
| 4. DTC social + search | Ready (with gaps) | Queries fixed (reserved alias `rows`, column names, Kerendia filters). Social: 211 DMAs, but no data after Jun 2026 and a May 2026 click outlier. Search: state level only; DTC = 6 campaigns, 15.6% of Kerendia search clicks |
| 5. OE event-level | Exists | Uses `DATE_ID` and `CUST_ID`; needs a mapping to BH_ID / NPI |

---

## 6. Phase 1 output analysis (families 1 and 2)

**Notebook:** `51_digital_nba_phase1_features` (run 3 November 2026)  
**Output:** `.../dev_folder/notebook_output/nba_3_1_digital_phase1/hcp_digital_phase1_features` (Delta, partitioned by `COHORT_ID`)  
**Reviewed:** 5 November 2026, by reading all 19 cells and querying the output and the raw MMX table directly.

### 6.1 What Phase 1 builds, in plain words

Phase 1 turns the MMX table into **one row per doctor (NPI) per cohort** with 152 fixed features about HCP paid media (family 1) and HQ email (family 2). A **cohort** is one monthly prediction date: cohort `2026-09_offset7` means "as of 6 October 2026" (month end + 6 days, the same rule as the NBA 3.1 claims features). Every window (1, 3, 6, 12 months) ends on that cutoff, so nothing after it is used.

| Feature group | Count | Example | Question it answers |
| --- | --- | --- | --- |
| P1 Totals | 16 | `DIGITAL_TOTAL_EXPOSURE_3M`, `DIGITAL_TOTAL_XPP_EXPOSURE_3M` (XPP = without PulsePoint) | How much digital did the doctor get overall? |
| P2 Channel totals | 24 | `DIGITAL_CH_3P_EMAIL_ENGAGEMENT_6M` | Through which type of media? |
| P3 Placements | 76 | `DIGITAL_PLC_DOXIMITY_DOCSPOT_EXPOSURE_3M` | On which exact spot of which vendor? (experiment E3 only) |
| P4 Rates | 5 | `DIGITAL_ENGAGEMENT_RATE_6M` | Does the doctor react, or is he only shown a lot? |
| P5 Recency | 4 | `DIGITAL_DAYS_SINCE_LAST_ENGAGEMENT` | How long ago was the last reaction? |
| P6 Diversity | 3 | `DIGITAL_N_VENDORS_3M` | From how many sources? |
| P7 Trend | 3 | `DIGITAL_EXPOSURE_3M_VS_PRIOR_3M` (-1 to +1) | Is digital pressure rising or falling? |
| IND Indication | 9 | `DIGITAL_IND_HF_EXPOSURE_3M` | Which indication was the content about? |
| P8 HQ email | 12 | `DIGITAL_HQ_EMAIL_OPENS_PER_SENT_6M` | Does the doctor read Bayer emails? |
| **Total** | **152** | 76 in experiment E2 (no placements), all 152 in E3 | |

### 6.2 Is it correct? Review verdict

**Yes, the logic is correct and the numbers reproduce**, with three issues to fix before the E2 / E3 experiments (section 6.6).

Evidence:

| Check | Result |
| --- | --- |
| Notebook QC1 (schema, unique keys, no leakage, windows nested, total = sum of channels, ...) | 13 of 13 PASS (from the notebook's results cell) |
| Notebook QC2 (16 doctors, 2 cohorts, 4 features recomputed from raw MMX) | 64 of 64 MATCH (from the notebook's results cell) |
| Output shape (my check) | 5,893,532 rows = 5,893,532 unique NPI x cohort keys; 160 columns (8 key / meta + 152 features); 21 cohorts `2025-01` to `2026-09` |
| My independent recompute, cohort `2026-09_offset7`, all doctors (raw MMX, day-level dates 7 Jul to 6 Oct 2026, no dictionary) | Total paid-media exposure 18,116,708 in both; doctors with exposure 107,820 in both; share without PulsePoint 5.0% in both; HQ email sent 344,245 in both |

The placement dictionary maps 100% of paid-media rows (unmapped share 0.0000%), and every vendor has its own entry (38 placements, 18 vendors).

### 6.3 NBA 3.0 vs NBA 3.1: what changed in the output and why

| Topic | NBA 3.0 (`24_Features_Digital`) | NBA 3.1 Phase 1 | Why the change |
| --- | --- | --- | --- |
| Number of features | 684, created by dynamic pivots | 152, fixed list from the dictionary | Same columns at every run; the model kept only 9 of the 684 anyway |
| Row = | Doctor x calendar month, every month since data start | Doctor x cohort (prediction date) | Same grain as the NBA 3.1 claims features, so they join directly |
| Brand filter | `BRND_NM = 'KERENDIA'` only | Every brand value containing Kerendia | Indication-tagged rows (HF, CKD, UACR) were being thrown away |
| Doctor ID | Any non-empty NPI, including `PDRP` and `NULL` | Only real 10-digit NPIs | `PDRP` is not a doctor; NBA 3.0 counted it as one |
| HQ and iRep email | Inside the digital block (and again in notebooks 15 and 16) | Excluded from paid media; HQ email built once (P8); iRep left to the personal block | No double or triple counting |
| Windows | 1 / 3 / 6 months + `RUNNING_` since data start; first month dropped, unfinished current month included | 1 / 3 / 6 / 12 complete months ending at the cutoff | Same meaning at every cohort; no partial months |
| Detail | Channel, vendor and tactic as three separate pivots | Vendor + placement (e.g. `DOXIMITY_DOCSPOT`) | Placements are where OE found signal |
| New kinds of features | None | Rates, recency, diversity, trend, totals without PulsePoint, indication | Separate "shown a lot" from "responds" |

**The same 3-month window measured both ways** (7 July to 6 October 2026, my query on raw MMX):

| Item | Exposure |
| --- | --- |
| NBA 3.0 rules (exact brand, any NPI, all channels except calls and samples) | 18,718,576 |
| of which rows with an invalid NPI (`PDRP` / `NULL`), removed in NBA 3.1 | 511,831 |
| of which HQ email and iRep email, moved out of paid media in NBA 3.1 | 352,691 |
| Indication-tagged rows that NBA 3.0 dropped and NBA 3.1 adds | 254,208 |
| **NBA 3.1 paid media** | **18,116,708** |

The totals look similar, but the content is different: about 0.86M exposures that were not real doctors or were duplicates leave, and 0.25M exposures that were missing come in. (The three items do not add up exactly to the difference, because a few HQ / iRep rows also have an invalid NPI.)

### 6.4 The numbers explained: latest cohort `2026-09_offset7` (as of 6 October 2026)

The table has **288,768 doctors** for this cohort: every NPI with any paid-media or HQ email activity in the last 12 months. Doctors with no digital activity at all are not in the table; the combine step must give them 0.

**Who is reached** (last 3 months):

| Measure | Value | How to read it |
| --- | --- | --- |
| Doctors with any paid-media exposure | 107,820 (37.3%) | About 1 in 3 doctors of the table saw Kerendia paid media in the last 3 months |
| Doctors with any engagement | 18.7% | About half of the exposed doctors reacted at least once |
| Doctors sent an HQ email | 27.6% | |
| Exposure per doctor | median 0, top 1% at 379 or more, maximum 820 | Most doctors in the table had activity earlier in the year but not in the last 3 months; a few get very high volumes |
| Days since last engagement (doctors with one) | median 96 days | The typical last reaction was about 3 months before the cutoff |
| Vendors per doctor | 0.97 on average | Most doctors see one vendor only |

**PulsePoint dominates volume but not reactions:**

| Measure | Value |
| --- | --- |
| Total paid-media exposure | 18,116,708 |
| PulsePoint programmatic display | 17,211,270 (95.0%), reaching 34.0% of the doctors |
| Everything else (`XPP`) | 905,438 (5.0%) |
| Total engagement | 148,127 |
| Engagement from everything except PulsePoint | 138,149 (93.3%) |

In words: PulsePoint is 95% of what doctors are **shown** but only about 7% of what they **react** to. This is why NBA 3.1 has totals without PulsePoint (`XPP`) and rates.

**Average engagement rate per doctor** (6 months, doctors with exposure in the channel): banner 0.10%, 3rd-party email 32.2%, custom (medical sites and apps) 24.2%. 85 doctors have a rate above 1 (more reactions than exposures), because some vendors count several reactions per exposure.

**Placements, last 3 months** (exposure and share of the 288,768 doctors with a non-zero value):

| Placement | Exposure | Doctors reached |
| --- | --- | --- |
| PulsePoint programmatic display | 17,211,270 | 34.0% |
| Doceree EHR banner | 247,527 | 1.2% |
| Doximity DocNews | 167,269 | 12.9% |
| Medscape email alert | 156,731 | 24.7% |
| Medscape offsite media | 153,956 | 6.0% |
| PeerDirect MDFI email | 55,912 | 14.5% |
| Medscape Brand Alert | 29,148 | 3.1% |
| Doximity DocSpot | 15,713 | 1.9% |
| Doximity DocPoint | 12,712 | 1.2% |
| PeerDirect MD Minute email | 11,670 | 3.5% |
| Epocrates Monograph | 11,363 | 3.0% |
| 9 more placements | 294 to 8,907 each | 0.01% to 0.93% |
| **18 placements** (e.g. Impiricus SMS, Prescriber Point, MDCalc, Biopharm, Haymarket, ConnectiveRx, Nativo, MJH, LinkedIn, Medscape banner) | **0** | 0% |

Only 20 of the 38 placements had any activity in the last 3 months. Medscape email alert and Doximity DocNews reach many more doctors than their exposure suggests: small volume, wide reach.

**HQ email** (last 3 months, MMX source): 344,245 sent, 88,836 opens (25.8 per 100 sent), 6,343 clicks (1.8 per 100 sent).

**Indication:** HF 282,989, CKD 451,013, both 75,988 exposures: together 4.5% of paid media. The other 95.5% (mostly PulsePoint) carries no indication tag.

### 6.5 The numbers over time (all 21 cohorts)

| Cohort | Months of history | Doctors in table | % exposed 3M | % engaged 3M | % HQ sent 3M | Exposure 3M (M) | Share without PulsePoint | Avg trend |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-01 | 1 | 110,478 | 62.5% | 10.6% | 78.4% | 2.77 | 25.8% | 1.000 |
| 2025-02 | 2 | 125,074 | 68.6% | 14.0% | 69.5% | 4.80 | 17.0% | 1.000 |
| 2025-03 | 3 | 228,137 | 60.9% | 10.5% | 61.3% | 6.71 | 13.3% | 0.882 |
| 2025-04 | 4 | 236,259 | 58.9% | 10.9% | 50.6% | 7.86 | 5.6% | 0.613 |
| 2025-05 | 5 | 241,747 | 57.0% | 11.9% | 52.1% | 10.35 | 5.5% | 0.471 |
| 2025-06 | 6 | 243,319 | 35.2% | 11.6% | 51.0% | 12.32 | 4.8% | -0.260 |
| 2025-07 | 7 | 252,693 | 33.4% | 12.4% | 49.5% | 13.63 | 4.7% | -0.219 |
| 2025-08 | 8 | 260,773 | 36.5% | 14.8% | 46.0% | 14.45 | 5.5% | -0.186 |
| 2025-09 | 9 | 278,583 | 40.9% | 19.7% | 35.7% | 15.21 | 5.6% | 0.260 |
| 2025-10 | 10 | 293,285 | 44.9% | 20.2% | 20.5% | 14.60 | 6.1% | 0.407 |
| 2025-11 | 11 | 321,505 | 50.7% | 18.5% | 18.6% | 13.86 | 6.8% | 0.401 |
| 2025-12 | 12 | 354,102 | 53.2% | 13.0% | 16.7% | 13.73 | 8.0% | 0.361 |
| 2026-01 | 12 | 374,222 | 56.3% | 11.6% | 19.5% | 15.43 | 8.5% | 0.328 |
| 2026-02 | 12 | 381,988 | 52.6% | 11.1% | 19.0% | 19.42 | 6.7% | 0.179 |
| 2026-03 | 12 | 332,767 | 46.3% | 13.5% | 21.6% | 23.24 | 5.7% | -0.113 |
| 2026-04 | 12 | 325,077 | 40.1% | 13.2% | 21.2% | 23.54 | 5.1% | -0.183 |
| 2026-05 | 12 | 324,084 | 39.8% | 13.7% | 21.6% | 20.66 | 5.7% | -0.267 |
| 2026-06 | 12 | 326,236 | 42.1% | 15.1% | 23.4% | 17.46 | 6.6% | -0.233 |
| 2026-07 | 12 | 297,827 | 34.5% | 17.9% | 26.5% | 17.60 | 6.3% | -0.138 |
| 2026-08 | 12 | 296,608 | 36.6% | 18.9% | 25.7% | 18.58 | 5.4% | -0.124 |
| 2026-09 | 12 | 288,768 | 37.3% | 18.7% | 27.6% | 18.12 | 5.0% | -0.108 |

How to read it:

* **Months of history** = how many complete months of digital data exist before the cohort (MMX starts in January 2025). 12-month features are only complete from cohort 2025-12.
* **Volume** grew from 2.8M exposures (3M window, early 2025) to a peak of 23.5M (spring 2026), then settled around 18M.
* **Share without PulsePoint** fell from 26% to about 5% once PulsePoint scaled up in spring 2025, so plain totals became almost a PulsePoint measure.
* **HQ email reach** fell from 78% of the table to about 17% to 28%, partly because the table grew with paid-media-only doctors.
* **Avg trend = 1.000** in the first two cohorts is not real growth: there is no data in the "prior 3 months", so every doctor gets +1 (issue 1 below).

### 6.6 Issues found in the review

| # | Issue | Evidence | Effect | Fix |
| --- | --- | --- | --- | --- |
| 1 | **Trend features are artificial in early cohorts** | Average trend is exactly 1.000 for cohorts 2025-01 and 2025-02 and 0.88 for 2025-03: the prior 3 months fall before January 2025 | The model could learn "trend = +1 means early 2025", a period marker like `BANNER_TACTIC` in NBA 3.0 | Set the 3 trend features to NULL when `DIGITAL_HISTORY_MONTHS` < 6; also set 6M / 12M features to NULL (or exclude those cohorts from training) when history is shorter than the window |
| 2 | **HQ email ran on the MMX fallback** | Snowflake `HCP_EMAIL_LIST` failed; bounce and unsubscribe flags are NULL for every row (0 non-empty values) | 2 of the 12 HQ email features are empty; opens / clicks rely on the assumption EXPOSURE = sent, TOTAL_ENGAGEMENT = open, DEEP_ENGAGEMENT = click; repeat opens are counted | Fix the view, or switch to `FACT_SENT_EMAIL` (ready in Phase 0); until then drop the two flags |
| 3 | **Many placements are empty at prediction time** | 18 of 38 placements have zero exposure in the last 3 months of the latest cohort; the notebook reports 45 of 152 features non-zero for fewer than 0.1% of doctors | These features carry only old-period information | In E3 keep only placements with activity in the last 3 cohorts; review again when vendors restart |
| 4 | Indication split is thin | Only 4.5% of exposure carries an HF / CKD tag; T1D is not available yet | IND features describe a small part of the activity | Apply the doctor-level HF / T1D / CKD rule when the T1D list arrives |
| 5 | Engagement definition differs by vendor | 85 doctors have an engagement rate above 1; light / deep rule not written down | Rates are not fully comparable across vendors | Document the rule per vendor metric (map to OE's R / I / E); cap rates at 1 or use reacted-yes / no |
| 6 | Table holds only doctors with digital activity | 288,768 doctors in the latest cohort | Doctors without digital activity are missing | In the combine step: counts = 0, rates / trends / days-since = NULL (already noted in the notebook) |

### 6.7 Status and next steps

* **Gate G1:** met for build, leakage and fixed schema (second run gave an identical schema). Fix issues 1 and 2 before running the experiments.
* **Next:** run E2 (76 features, no placements) and E3 (all 152, after issue 3) against the NBA 3.0 digital block (E0) in the NBA 3.1 HCP model.
* **Open with the digital team:** vendor codes for ConnectiveRx, Nativo, Healthcast and LinkedIn; the Medscape custom entries (Digital Data Trends, Formulary Access Package); the light / deep rule; a campaign ID for unique opens.

---

## 7. Phase 2: high-intent signals (family 3)

**Notebook:** `53_digital_nba_phase2_high_intent_features` (written 5 November 2026, not run yet as a notebook)  
**Output (when run):** `.../dev_folder/notebook_output/nba_3_1_digital_phase2/hcp_digital_phase2_high_intent_features` (Delta, partitioned by `COHORT_ID`), plus `rar_open_requests_business_rule`, `feature_manifest`, `expected_schema.json`  
**Status of the numbers below:** New Writer and Impiricus SMS were computed by me on 5 November 2026 with the same logic as the notebook, on the Unity Catalog tables. Request-a-Rep needs the Snowflake connection, so its numbers come from the documents [Doc] until the notebook is run.

### 7.1 What Phase 2 builds, in plain words

One row per doctor (NPI) per cohort, with the **same 21 cohorts and cutoffs as Phase 1** (cohort `2026-09_offset7` = as of 6 October 2026), so it joins directly to the Phase 1 table and the claims features. 18 fixed features:

| Signal | Features | Question it answers | Source |
| --- | --- | --- | --- |
| Request-a-Rep (8) | `RAR_COUNT_3M / 6M / 12M`, `RAR_LAST_6M_FLAG`, `DAYS_SINCE_LAST_RAR`, `RAR_TYPE_SAMPLES_FLAG_12M`, `RAR_OPEN_REQUEST_FLAG`, `RAR_FOLLOWED_UP_SHARE_12M` | Did the doctor ask for a rep, how recently, for what, and did we answer (as of the cutoff)? | `RPT_DIGITAL_RAR_TAB` (Snowflake) |
| New Writer (5) | `KERENDIA_WRITER_EVER_FLAG`, `NEW_WRITER_LAST_3M / 6M / 12M_FLAG`, `DAYS_SINCE_FIRST_KERENDIA_RX` | Has the doctor just started prescribing Kerendia? | LAAD `kerendia_laad_based_lrx_v7` (replaced `_full_data_starting_2021` + `_v6`, Nov 2026) |
| Impiricus SMS (5) | `SMS_SENT_3M`, `SMS_EXPOSED_3M_FLAG`, `SMS_ENGAGED_6M / 12M_FLAG`, `DAYS_SINCE_LAST_SMS` | Did the doctor receive or react to a Kerendia text message? | MMX, vendor `IMPIRICUS` |
| Formulary wins (0) | none yet | | source not found |

Plus **use B, the business rule**: a list of doctors with an open request (made in the last 90 days, no rep call on or before the cutoff), with the reason "Requested a rep on <date>", saved as its own table for the NBA dropdown.

**Definitions chosen (to confirm with OE / the digital team):**

* **New Writer** = the week of the doctor's **first Kerendia prescription ever** (`PRODUCT_GROUP = 'KERENDIA'`, `TRX > 0`), looking back to the start of LAAD (December 2021). "New writer in the last 3 months" = that first week falls in the 3 months before the cutoff.
* **Open request** = no rep call yet, and not older than 90 days (`RAR_OPEN_DAYS`; an assumption, so that very old requests do not stay "open" forever).
* **Samples request** = `REQUEST_TYPE` contains "SAMPL" (to adjust once the real request-type values are printed by the notebook).

**Leakage rules built in:** only events on or before the cutoff; a request counts as answered only if the first call after it is **on or before the cutoff**; LAAD uses the week-ending date, so a week that ends after the cutoff is not used. A self-test with known answers checks these rules (it passed in my run), including the case "request on 20 September, call on 10 October, cutoff 6 October" = still open.

**Personal data:** the notebook reads only IDs, dates and request / rep type from the RAR table, no name, email or phone.

### 7.2 What the data shows

**New Writer** [Q, LAAD]: 80,830 doctors (valid NPI) have written Kerendia at least once; the first week in the data is 3 December 2021; LAAD runs to 9 October 2026. New writers per month are steady and rising: about 1,000 to 1,500 a month in 2024, 1,200 to 2,000 in 2025, and 1,650 to 2,300 in January to September 2026 (2,290 in July, 1,996 in August, 2,043 in September 2026).

**Impiricus SMS** [Q, MMX]: very small and stopped.

| Month | SMS sent | Doctors | Engagements |
| --- | --- | --- | --- |
| Mar 2025 | 292 | 274 | 7 |
| Apr 2025 | 618 | 554 | 56 |
| Jun 2025 | 3,047 | 2,821 | 63 |
| Nov 2025 | 5,331 | 5,288 | 43 |
| Dec 2025 | 3,155 | 3,140 | 16 |
| Jan to Oct 2026 | 0 | 0 | 0 |

In total 12,443 SMS and 185 engagements (1.5%). MMX itself has data up to 1 November 2026, so the zero in 2026 is not a late feed for MMX as a whole.

**Request-a-Rep** [Doc, `40_...`]: 1,218 Kerendia requests from January 2025 to October 2026; 340 (28%) followed by a rep call after a median of 7 to 9 days; about 880 without a call. NPI is on about 46% of rows, so the notebook maps BH_ID to NPI first and uses the RAR `NPI` column only as a fallback; it prints how many requests stay unmapped.

### 7.3 The numbers over time (New Writer and SMS, all 21 cohorts)

Number of doctors with the flag = 1, by cohort [Q, same logic as the notebook]:

| Cohort | Writers ever | New writer 3M | New writer 6M | New writer 12M | SMS exposed 3M | SMS engaged 6M | SMS engaged 12M |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-01 | 45,559 | 3,722 | 7,596 | 15,220 | 0 | 0 | 0 |
| 2025-02 | 46,900 | 3,607 | 7,485 | 15,389 | 0 | 0 | 0 |
| 2025-03 | 48,534 | 4,215 | 7,914 | 15,707 | 272 | 4 | 4 |
| 2025-04 | 49,840 | 4,281 | 8,003 | 15,923 | 825 | 42 | 42 |
| 2025-05 | 51,419 | 4,519 | 8,126 | 16,363 | 825 | 46 | 46 |
| 2025-06 | 52,593 | 4,059 | 8,274 | 15,838 | 3,274 | 95 | 95 |
| 2025-07 | 53,920 | 4,080 | 8,361 | 15,957 | 2,820 | 95 | 95 |
| 2025-08 | 55,673 | 4,254 | 8,773 | 16,258 | 2,813 | 95 | 95 |
| 2025-09 | 57,204 | 4,611 | 8,670 | 16,584 | 0 | 92 | 95 |
| 2025-10 | 58,813 | 4,893 | 8,973 | 16,976 | 0 | 57 | 95 |
| 2025-11 | 60,943 | 5,270 | 9,524 | 17,650 | 8,425 | 99 | 143 |
| 2025-12 | 62,498 | 5,294 | 9,905 | 18,179 | 8,425 | 51 | 145 |
| 2026-01 | 64,592 | 5,779 | 10,672 | 19,033 | 8,425 | 51 | 145 |
| 2026-02 | 66,418 | 5,475 | 10,745 | 19,518 | 2 | 51 | 145 |
| 2026-03 | 68,123 | 5,625 | 10,919 | 19,589 | 0 | 51 | 142 |
| 2026-04 | 69,842 | 5,250 | 11,029 | 20,002 | 0 | 51 | 107 |
| 2026-05 | 72,045 | 5,627 | 11,102 | 20,626 | 0 | 2 | 101 |
| 2026-06 | 73,837 | 5,714 | 11,339 | 21,244 | 0 | 0 | 51 |
| 2026-07 | 75,697 | 5,855 | 11,105 | 21,777 | 0 | 0 | 51 |
| 2026-08 | 78,193 | 6,148 | 11,775 | 22,520 | 0 | 0 | 51 |
| 2026-09 | 80,275 | 6,438 | 12,152 | 23,071 | 0 | 0 | 51 |

**Independent check** (direct SQL with fixed dates, a different method from the feature engine): cohort 2026-09 new writers 3M = 6,438 and writers ever = 80,275; cohort 2025-01 new writers 3M = 3,722. All three match the table.

How to read it:

* **New Writer is a usable signal**: about 6,400 doctors started Kerendia in the 3 months before the latest cutoff, and the count is never zero. Because LAAD goes back to 2021, "first Rx ever" is reliable from the first cohort, so it has no early-cohort problem like the Phase 1 trend features (issue 1).
* **SMS is a dead signal at prediction time**: no doctor was exposed in the 3 months before any cutoff since cohort 2026-03, and no doctor engaged in the last 6 months since cohort 2026-06. Only 51 doctors still carry the 12-month engaged flag. Like the stopped DTC vendors (3.4), it would only teach the model "old period".

### 7.4 Issues and decisions

| # | Issue | Evidence | Proposal |
| --- | --- | --- | --- |
| 1 | RAR not yet built from the data | Snowflake needed; not run in my session | Run notebook 53; check the printed request types, NPI mapping coverage, and that QC1 / QC2 pass |
| 2 | Impiricus SMS has no data in 2026 | Table 7.2; 0 exposed since cohort 2026-03 | Keep the 5 SMS features in the table but **exclude them from the experiment** until the digital team confirms whether Impiricus restarts (or where 2026 data lands) |
| 3 | New Writer overlaps with the Rx claims features | Both come from LAAD; NBRx features already count new-to-brand Rx | Keep only the flags and `DAYS_SINCE_FIRST_KERENDIA_RX` (first Rx **ever** is not in the NBRx counts); test their added value in E6; check that the model target is not "becomes a writer", otherwise drop them |
| 4 | Open-request window and samples rule are assumptions | 90 days and "SAMPL" chosen by me | Confirm with the digital / field team |
| 5 | RAR events are rare | about 1,200 requests in 22 months [Doc] | Use the business-rule list (use B) as the main output; the RAR features are a bonus for the model |
| 6 | Formulary wins missing | source not found | Digital / OE team to provide source and format |
| 7 | Table holds only doctors with an event | as in Phase 1 issue 6 | Combine step: counts / flags = 0, days-since / share = NULL |

### 7.5 Next steps

* Run `53_digital_nba_phase2_high_intent_features` end to end and copy the RAR numbers (requests per cohort, open requests in the latest cohort, NPI coverage) into this section.
* Experiment **E6**: Phase 1 block + RAR + New Writer (SMS excluded), against Phase 1 alone.
* Agree with OE: New Writer definition, open-request window, and how the use B list enters the NBA dropdown.
