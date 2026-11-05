# Digital in NBA 3.1: Where We Are and What We Propose

**For:** Kerendia digital marketing team  
**From:** NBA team  
**Purpose of the meeting:** share what we found about digital in NBA 3.0, walk through what we propose for NBA 3.1, and **collect your concerns and suggestions** before we build anything  
**Status:** updated after the first meeting with the digital team (answers in section 7, new data assets in section 4.4); still a draft, nothing is decided  
**Date:** October 2026

---

## 1. What we need from you

You know the media partners, the placements and how campaigns were actually executed far better than the data shows. We would like your view on four things:

1. **Does our reading of the data match what really ran?** (sections 3 and 4)
2. **Is the proposed set-up for NBA 3.1 sensible from a marketing point of view?** (section 5)
3. **What are we missing?** Placements, campaigns, changes in tracking, upcoming launches.
4. **The specific questions in section 7**, where your answer changes what we build.

---

## 2. The short version

| | Today (NBA 3.0) | What we propose (NBA 3.1) |
| --- | --- | --- |
| **HCP digital** (media partners, HQ email) | About 680 digital columns are built, but only 9 are kept by the model, and none of them names a media partner. The best one ranks 68th of 752. | A smaller, fixed set of features organised by **vendor and placement** (every vendor kept on its own), as in OE, plus engagement rates, recency, indication and (later) content. A separate family for **high-intent signals** such as Request-a-Rep. |
| **DTC** (patients) | 9 features kept (Health Union, WebMD, Sharecare, Healthline, Facebook / Instagram). Most of these channels **stopped in 2024 – early 2025**, so the features are now zero. | Hold until we know the DTC plans for the upcoming launch. Paid search is the one active channel; it now has regional data **by state** only. |
| **CLM / clickstream** (rep tablet content) | Built, but no feature kept by the model. Less than 1% of Kerendia calls use CLM. | At most a few simple flags; revisit once the new iVA shows up in the data. |

The main message: **digital matters in NBA 3.0 less than it should, mostly because of how the features are built, not because digital does not work.** OE already shows a better way to describe digital, and we want to reuse it.

---

## 3. HCP digital today

### 3.1 What the NBA 3.0 model keeps

NBA 3.0 reads the MMX table (`MMX_FNL_COMBINED_AGGR_TAB`) and builds columns for each channel, vendor and tactic over 1, 3 and 6 months. Of about 680 columns, the model keeps 9:

| What the feature says | In practice | Best rank (of 752) |
| --- | --- | --- |
| Banner tactic exposure, last 3 months | Doceree, OpenEvidence and PeerDirect banners. **Zero before April 2025**, so it partly acts as a "before / after" marker | 68 |
| Banner channel exposure (3 features) | Almost entirely **PulsePoint** (105.5M of 107.2M banner rows) | 151 |
| HQ email exposure and light engagement (3 features) | SFMC HQ email | 688 |
| iRep email exposure (2 features) | Rep-sent email | 738 |

For comparison, the top features are rep visits, Kerendia prescribing history and patient features.

### 3.2 Why digital looks weak in NBA 3.0

We believe these are mostly **build problems**, which we can fix:

| Issue | What happens | Example |
| --- | --- | --- |
| **Brand filter too strict** | Only rows with brand exactly `KERENDIA` are kept; indication-tagged rows (`KERENDIA HF`, `KERENDIA_CKD`, `KERENDIA UACR`, ...) are dropped | About 88% of Doceree and 74% of PeerDirect email activity is lost |
| **Placements are mixed together** | Tactics are matched on exact names; anything else goes to one "other" bucket | PulsePoint display, Medscape BrandAlert, Doximity DocPoint and PeerDirect web all end up in the same bucket |
| **Columns change from run to run** | New vendor or tactic names create new columns | The model cannot rely on a stable set of inputs |
| **Double counting** | HQ email is counted in three places; iRep email in two | Same touch, several features |
| **No content, no timing** | Only counts by channel | Nothing on what message was shown, or how recently |
| **Engagement levels not written down** | "Light" and "deep" engagement are **our internal definitions** (not vendor-reported), but the rule for each vendor metric is not documented next to the NBA features | Hard to explain or compare across vendors; to be documented and aligned with OE's reach / interaction / engagement levels |

### 3.3 What OE does differently

OE 2.0 (which recommends doctors to Doximity, Medscape, PeerDirect, PulsePoint and SFMC every week) already describes digital in a way that fits how campaigns are run:

* **Vendor + placement** as one unit (for example Doximity DocSpot, Medscape 3rd-party email, PeerDirect MDFI web): 12 placements it can recommend.
* **Three written levels per vendor metric:** reach (shown / delivered), interaction (opened / viewed), engagement (clicked through).
* **Content category** of every touch (guidelines, access and coverage, mechanism of action, patient profile, ...).
* **Timing**: a 7-day response lag and the gaps between touches.
* **MMX fills the gaps** for vendors without event data (Epocrates, Prescriber Point, custom programs).

---

## 4. What the data shows (last two years)

### 4.1 HCP digital: activity by vendor and placement

MMX rows, January 2025 – October 2026, all Kerendia brand values. "OE" = placement OE can recommend.

| Channel | Vendor and placement | Rows | OE |
| --- | --- | --- | --- |
| Banner | PulsePoint programmatic display | 105.5M | Yes |
| Banner | Doceree EHR banner | 834k | No |
| Banner | Medscape banner | 274k | Yes |
| Banner | PeerDirect banners (MDFI, MD Minute, ...) | 67k | No |
| Banner | OpenEvidence direct banner | 26k | No |
| 3rd-party email | Medscape email alert | 1.75M | Yes |
| 3rd-party email | PeerDirect MDFI email | 493k | Yes |
| 3rd-party email | PeerDirect MD Minute email | 266k | Yes |
| Custom | Doximity DocNews / DocPoint / DocSpot / Announcement | 1.14M / 133k / 112k / 18k | Yes |
| Custom | Medscape BrandAlert | 1.12M | Yes |
| Custom | Medscape offsite media | 1.23M | No |
| Custom | Epocrates (monograph, DocAlert, search) | 183k | No |
| Custom | Prescriber Point monograph | 115k | No |
| HQ email | SFMC HQ email (incl. copay, FTO and voucher journeys) | 9.37M | Yes |

**Smaller vendors, now listed on their own** (added after the meeting, A1 / A2). Same table and period; doctors = distinct NPIs.

| Channel | Vendor | Rows | Doctors (NPI) | Active period in the data | Note |
| --- | --- | --- | --- | --- | --- |
| Banner | Biopharm | 301k | 11.3k | Dec 2025 – Mar 2026 | |
| 3rd-party email | Biopharm | 190k | 27.2k | Dec 2025 – May 2026 | |
| 3rd-party email | Haymarket | 245k | 25.5k | Sep 2025 – Jun 2026 | Also 11k banner and 3k custom rows |
| Custom | ReachMD | 25k | 5.6k | Jul 2025 – Jun 2026 | Also 2k banner rows (Mar – May 2026); optional OE addition |
| 3rd-party email | MJH Life Sciences | 13k | 1.2k | Feb 2025 – Apr 2026 | |
| Custom | **Impiricus (SMS messages)** | 12k | 10.1k | Mar – Dec 2025 | Being added as an **SMS channel in the Q4 OE scope** |
| Custom | MD Calc | 11k | 4.0k | Nov 2025 – Jul 2026 | |

ConnectiveRx, Nativo and Healthcast did not appear under those names in 2025 – 2026; we will check their vendor codes with you.

This is the first version of a **placement dictionary** we want to use for NBA 3.1 (section 5.1). The full table, with raw tactic names, is in `13_hcp_digital_nba_3_1_readiness_plan.md`, section 5.1.

**OE roll-out.** OE ran a 3-month pilot with test and control groups and has been fully rolled out since 18 September 2026, with no control group after that date. We expect the digital mix and volume to shift around that date, and we will check it.

### 4.2 DTC (patients)

Impressions in millions per year:

| Channel | 2023 | 2024 | 2025 | 2026 (Jan – Oct) | Status |
| --- | --- | --- | --- | --- | --- |
| Direct buys (Health Union, Healthline, Sharecare, WebMD) | 34.6 | 8.4 | 0.05 | 0.02 | Stopped (WebMD trace only) |
| Facebook / Instagram | 202.8 | 97.1 | 41.7 | 22.3 (to June) | Running, declining |
| PulsePoint DTC display | 143.4 | 199.0 | – | – | Stopped Sep 2024 |
| The Trade Desk display / CTV / audio | 428.6 | ~0 | – | – | Stopped Dec 2023 |
| Connected TV / online video (Disney, Hulu, Discovery) | 38.1 | 15.9 | – | – | Stopped mid-2024 |
| Paid search, **DTC campaigns** (`KER_DTC_`) | | | 1.47 | 1.36 | Running, branded only |

What this means:
* **The DTC features NBA 3.0 relies on are now zero.** The strongest one (Health Union, rank 32) has had no data since early 2025.
* **Paid search** never stopped, but **about 85% of Kerendia paid search is HCP search** (`KER_HCP_` campaigns), not DTC. DTC search is 6 branded campaigns.
* **Regional data:** SA360 no longer delivers DMA; the new regional feed (`FUNNEL_DATA_NEW_SA360_REGION`) is **by state**, with no Metro. In July – December 2024, DTC search ran in only six states (TX, CA, FL, NY, GA, NC).
* **Facebook / Instagram** regions rank almost the same every year, so the numbers mostly reflect region size.

Full detail: `21_dtc_data_findings_2024_2026_and_open_questions.md`.

### 4.3 CLM / clickstream (rep tablet content)

* About 500 – 900 CLM calls a month, **under 1% of Kerendia calls**, about 4,000 doctors a year.
* No content named "iVA" appears after July 2025. The new iVA campaign is **not yet visible** in the clickstream data (data to 23 October 2026).
* Usage duration has been mostly zero since May 2025 (a tracking change?); presentation duration is still filled in.

Full detail: `personal_promotional_features/clickstream_clm_data_review_2024_2026.md`.

### 4.4 New data assets raised in the meeting

The meeting made clear that the historical MMX structure is **not complete**: several new or changed digital signals should be part of the NBA 3.1 data review.

| Asset | What we would need | Why it matters | Status / source |
| --- | --- | --- | --- |
| **Request-a-Rep (RAR)** / hand-raisers | Request date, HCP, follow-up status and date, and later Rx behaviour | About **1,200 RARs since 2025, but follow-up for only about 340**; Samantha Meyers highlighted the potentially significant commercial value of these hand-raisers | **Found in Snowflake:** `PHCDW.PHCDW_CDM.RPT_DIGITAL_RAR_TAB` (refreshed daily; same content as `FINAL_RAR_TABLE_VW`). Kerendia: 1,218 requests from Jan 2025 to Oct 2026 (512 in 2025, 706 in 2026), of which 340 have a rep call afterwards (median 7 – 9 days later). This matches the meeting figures. It also has request type (contact by rep 578, samples 523), UTM source (Google 560), iRep / HQ email and sample follow-up dates, territory and BH_ID (almost all rows; NPI on only about 46%). Raw web-form history from Jan 2024: `KERENDIA_HCP_RAR_EXTRACTS`. Included in the Q4 OE scope; not in the MMX table |
| **New Writer** signal | HCP, date of first Kerendia Rx | Another input to OE's dynamic target list | OE dynamic-target-list input |
| **iVA engagement** | Actual campaign and content IDs, Veeva metadata | New iVA campaign not yet visible in the clickstream data (4.3) | To be provided (C1) |
| **Impiricus SMS** engagement | Sends, opens / clicks per HCP and date | Newly activated channel | In MMX as `SMS Messages` (Mar – Dec 2025); Q4 OE scope |
| **Health-system formulary wins** | Health system, date of the win, affiliated HCPs | Access change that can drive prescribing | Included in the OE enhancement scope |
| **Indication / T1D target list** | HCP with indication: HF = cardiologists, T1D = T1D target list, CKD = remaining HCPs | Lets NBA keep indication as a dimension (A6) | Samantha Meyers to provide the T1D target-list file; the digital-target table then receives an HF / T1D / CKD indication field |
| **OE content mapping / message arc** | Content ID, content category, message-arc document | Moves NBA features from exposure counts to recognisable content categories | The OE SOW calls for Bayer stakeholder validation of historical content mapping and a message-arc / content ID document |

---

## 5. What we propose for NBA 3.1

### 5.1 HCP digital: three steps

**Step 1. Fix the foundations** (no new features yet)
* Include all Kerendia brand values (HF, CKD, UACR, ...), and **keep the indication** (HF / T1D / CKD) as a dimension rather than throwing it away (A6).
* One fixed **placement dictionary** (the tables in 4.1): every MMX row is mapped to a vendor, placement and channel. **Each vendor keeps its own entry**, including the smaller ones (Biopharm, Haymarket, ReachMD, MJH, MD Calc, Impiricus, ...), as the team asked (A2). Anything unmapped is reported, not silently pivoted.
* Write down our internal light / deep engagement rule per vendor metric, and align it with OE's reach / interaction / engagement levels (A3).
* One source per activity: HQ email from the email event log only; iRep email only in the rep (personal) block.
* The same columns every run.

**Step 2. A small, clean feature set** (about 120 – 160 candidates; the model is expected to keep 30 – 60)

| Family | What it captures | Example |
| --- | --- | --- |
| Totals | Overall digital pressure | Total exposure and engagement, last 3 months |
| Channel | Banner / 3rd-party email / custom / HQ email | Banner exposure, last 3 months |
| **Placement** | Each vendor placement | Doximity DocSpot exposure; Epocrates monograph exposure |
| Rates | Response, not just volume | Engagement / exposure, last 6 months |
| Recency | How recent the last touch was | Days since last engagement |
| Breadth | How many vendors / placements reach the doctor | Number of placements, last 3 months |
| Trend | Rising or falling pressure | Last 3 months vs the 3 months before |
| HQ email | Sent, open, click, rates, unsubscribe | Unique click rate, last 6 months |
| Indication | The same families split by HF / T1D / CKD, next to the Kerendia total | HF banner exposure, last 3 months |

**Step 2b. High-intent digital signals** (new family; our recommendation, not a meeting decision)

An HCP who **asks** for something is a very different signal from an HCP who was **shown** a banner. We propose to keep these signals in their own family, never mixed into exposure totals:

| Signal | Example features |
| --- | --- |
| Request-a-Rep | RAR in the last 3 / 6 months (flag and count), days since last RAR, RAR followed up yes / no, days from RAR to follow-up |
| New Writer | New Kerendia writer in the last 3 months, months since first Rx |
| Health-system formulary win | Formulary win at an affiliated health system in the last 6 months, days since the win |
| Impiricus SMS | SMS engagement (open / click) in the last 3 months |

RAR also gives the field a clear action (follow up the open requests); how it appears in the NBA dropdown list is to be agreed (D2).

**Step 3. Reuse OE's richer view** (if it tests better)
* OE's reach / interaction / engagement levels for Doximity, Medscape, PeerDirect, PulsePoint and SFMC.
* **Content counts** by category (guidelines, access and coverage, MOA, ...), using the OE content mapping and message-arc document once it is validated.
* iVA engagement, once the campaign and content IDs are available.
* Test the 7-day response lag.
* Check whether results differ before and after the OE roll-out.

### 5.2 DTC

* **Keep as is for now**, and decide after we know the DTC plans for the upcoming launch.
* If paid search is used: **DTC campaigns only**, by state or Metro, with HCP search kept with HCP digital.
* If Facebook / Instagram is kept: per person (for example per 1,000 adults), so it reflects pressure rather than region size.

### 5.3 CLM

* At most a few simple flags (any CLM call, number of CLM calls, recency), using presentation duration.
* Revisit when the iVA campaign appears in the data.

### 5.4 How NBA and OE fit together

From the meeting and the related design work: **NBA = who and why; OE = when, what and how.**
* NBA refreshes the HCP target list **monthly** and gives the drivers behind each HCP.
* OE consumes that list and adds **weekly** sequencing, content, channel and cadence.
* New signals such as Request-a-Rep and New Writers can **dynamically supplement** the list between NBA refreshes.

### 5.5 How we will decide

Each step is tested in the NBA 3.1 model against the NBA 3.0 digital block. A step is kept only if it improves the model, and every feature we keep must map to a vendor, placement or content you recognise. When NBA uses OE output, we speak of doctors **recommended** to vendors, not "reached".

---

## 6. What could go wrong (and what we plan to do)

| Risk | What we plan |
| --- | --- |
| Vendors rename tactics, activity drops into "other" | Pattern-based dictionary, monthly unmapped report |
| PulsePoint dominates volume, so totals = PulsePoint | Keep placement features next to totals; test totals without programmatic display |
| Small vendors are too sparse to learn from | Keep each vendor on its own (team request); let feature selection drop the ones with no signal, and report which were dropped |
| High-intent signals are rare (about 1,200 RARs) | Use flags and recency rather than counts; check how many HCPs have each signal before modelling |
| OE roll-out changes the data | Compare before / after 18 September 2026 |
| Digital effect stays weak | Accept a small block; do not force digital into the model |

---

## 7. Questions for you

Please add comments or answers in the last column, or bring them to the meeting.

### A. HCP digital

| # | Question | Your answer |
| --- | --- | --- |
| A1 | Does the **placement dictionary** in 4.1 match how you think about placements? Names, groupings, anything missing or wrongly merged? | We discussed those small vendors in A2 were missed from 4.1. |
| A2 | Is it acceptable to group small vendors (Biopharm, ConnectiveRx, Nativo, Haymarket, MJH, ReachMD, Impiricus, MD Calc, ...) into **"other" per channel**? Are any of them important enough to keep separately? | The team would rather to keep them as their own instead of clumping them into one bucket. Also Impiricus should not simply disappear into "other" because it is specifically being added as an SMS channel in the Q4 OE scope; ReachMD was also identified as an optional addition. |
| A3 | How do vendors define **"light" and "deep" engagement** in MMX? Is OE's reach / interaction / engagement split the right standard for NBA too? | Light and deep engagement are **not from the vendors**; they are our internal definition of engagement. To document the rule per vendor metric and align it with OE's levels. |
| A4 | Doceree, OpenEvidence and PeerDirect banners start in **April 2025**. Is that right, or were they tracked differently before? | Yes |
| A5 | Are there **tracking or naming changes** we should know about (vendor tactic renames, new placements, changes after the OE roll-out)? | There are clearly new/changed digital signals that need to be incorporated, including iVA, Request-a-Rep, New Writers, Impiricus SMS, health-system formulary wins and dynamically refreshed NBA target lists. These should be added to the data/placement review rather than assuming the historical MMX structure is complete. |
| A6 | Should HF and CKD activity be treated **separately** (the indication in the brand name), or is total Kerendia enough? | Evidence favors keeping indication available separately. A recent Q4 target-list workflow explicitly assigns an indication field using HF = CARDs, T1D = T1D target list, CKD = remaining HCPs. Therefore NBA 3.1 should avoid throwing away indication information. Total Kerendia can still be an aggregate feature, but indication should remain available as an additional dimension.|
| A7 | Who should **own the placement dictionary and the content tagging file** going forward? | Not resolved in the meeting artifacts. Recommend explicit ownership: Digital/OE business team owns placement/content definitions; NBA/data team operationalizes and monitors the mappings. The original OE SOW also calls for Bayer stakeholder validation of historical content mapping and a message-arc/content ID document.|
| A8 | Any placements you know work (or do not work) for Kerendia that we should make sure are visible to the model? | |

### B. DTC

| # | Question | Your answer |
| --- | --- | --- |
| B1 | Which DTC channels are planned for the upcoming launch, when, and how big compared with 2023? | |
| B2 | Will any DTC channel be **targeted by region**, or is it national? Is there a test-and-control region design? | |
| B3 | Was the July – December 2024 DTC search in six states a **planned regional test**? | |
| B4 | Can the search agency add **Metro** to the SA360 regional feed? If not, is state level acceptable? | |
| B5 | Is the `KER_DTC_` / `KER_HCP_` campaign naming reliable for splitting patient and HCP search? | |

### C. CLM

| # | Question | Your answer |
| --- | --- | --- |
| C1 | What is the **exact name** of the new iVA, and is it shown by reps on the tablet or used remotely / by email? | |
| C2 | Do you know why CLM usage duration became mostly zero from May 2025? | |

### D. Overall

| # | Question | Your answer |
| --- | --- | --- |
| D1 | Any **concerns** with the approach in section 5? | |
| D2 | Anything you would like NBA 3.1 to **show or explain** about digital in the NBA dropdown list? | |
| D3 | How should NBA and OE outputs be **presented together** so the field and the digital team get one consistent message? | This one is fairly well answered by the related design work: **NBA = who/why; OE = when/what/how**. The proposed operating model is for NBA to refresh the HCP target list monthly and provide the underlying drivers, while OE consumes that list and adds weekly sequencing, content, channel and cadence. New signals such as Request-a-Rep and New Writers can dynamically supplement that list.|

---

## 8. Next steps

1. Collect your feedback (this meeting and comments on this document). Answered: A1 – A7 and D3; open: A8, B, C, D1 – D2.
2. Update the placement dictionary with the smaller vendors as their own entries, and confirm the vendor codes for ConnectiveRx, Nativo and Healthcast.
3. Get the new data assets (4.4): RAR with follow-up status, New Writers, iVA IDs, Impiricus SMS, formulary wins, the T1D target list (Samantha Meyers), and the OE content mapping / message arc.
4. Document the internal light / deep engagement rule.
5. Step 1 (foundations), then Steps 2, 2b and 3, each tested in the model.
6. Come back to you with results: which digital features the model keeps and how they rank.

## 9. Background documents (in this folder)

| Topic | File |
| --- | --- |
| Vendor / channel / tactic / content map | `01_digital_entity_map_vendor_channel_tactic_content.md` |
| NBA 3.0 paid media and HQ email | `10_hcp_digital_paid_media_nba_3_0.md`, `11_hcp_hq_emails_nba_3_0.md` |
| OE 2.0 review | `12_hcp_oe_digital_review_for_nba_3_1.md` |
| Detailed HCP digital plan | `13_hcp_digital_nba_3_1_readiness_plan.md` |
| DTC findings and questions | `21_dtc_data_findings_2024_2026_and_open_questions.md` |
| CLM review | `../personal_promotional_features/clickstream_clm_data_review_2024_2026.md` |
