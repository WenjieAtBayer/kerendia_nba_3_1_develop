# Digital in NBA 3.1: Readiness Plan

**Group:** Non-personal promotional features (HCP digital, high-intent digital signals, DTC)  
**Purpose:** one plan for how digital features go into NBA 3.1: what we build, from which data, in which order, how we test it, and when it is ready  
**Builds on:** all files in this folder, the digital team meeting (answers in `40_digital_team_briefing_nba_3_1.md`, section 7), the CLM review (`personal_promotional_features/clickstream_clm.md`) and the Snowflake data checks of October 2026  
**Detailed HCP paid-media work plan:** `13_hcp_digital_nba_3_1_readiness_plan.md` (foundation tasks F1 to F9, placement dictionary, feature list); this file is the overall plan and does not repeat that detail  
**Status:** draft for review with the NBA, digital and OE teams  
**Date:** October 30, 2026

---

## 1. In short

* **Today digital adds little to NBA 3.0.** The model keeps 18 non-personal digital features out of 752. The best DTC feature (rank 32) is a direct-buy vendor that stopped running in early 2025. The best HCP digital feature (rank 68) mostly marks the period after April 2025. No feature names a media-partner placement, and none of the 24 CLM features was kept.
* **The data has changed since NBA 3.0.** DTC direct buys have stopped. SA360 no longer delivers Metro. New vendors started in April 2025. OE has been fully rolled out since 18 September 2026. New signals exist: Request-a-Rep, New Writers, Impiricus SMS, health-system formulary wins, the new iVA campaign and dynamically refreshed target lists.
* **What we propose for NBA 3.1:** five feature families: (1) HCP paid media by vendor and placement, every vendor kept on its own; (2) HQ email from one source; (3) **high-intent signals** (new), with Request-a-Rep first; (4) DTC market context rebuilt on what still runs; (5) engagement depth and content, reusing OE (later). **Indication** (HF / T1D / CKD) is kept as a dimension. They are built in five phases, each tested against the NBA 3.0 digital block in a fixed set of experiments.
* **NBA and OE stay complementary.** NBA = **who and why** (monthly target list and drivers); OE = **when, what and how** (weekly sequencing, content, channel, cadence).

---

## 2. What we learned (the evidence behind this plan)

| Topic | Finding | Consequence for NBA 3.1 | Source |
| --- | --- | --- | --- |
| NBA 3.0 model | 18 non-personal digital features kept (9 DTC, 9 HCP digital); best HCP digital rank 68; CLM 0 of 24 | Digital needs a cleaner, more meaningful block, not more columns | `12_...`, `clickstream_clm.md` section 7 |
| Brand filter | NBA 3.0 keeps only `BRND_NM = 'KERENDIA'`; drops 88% of Doceree and 74% of PeerDirect email | Use all Kerendia brand values and keep the indication | `01_...` section 6 |
| Dynamic pivots | Columns change between runs; tactic labels matched by exact, case-sensitive names | A fixed placement dictionary and a fixed schema | `10_...` section 6 |
| `BANNER_TACTIC` (rank 68) | Doceree + OpenEvidence + PeerDirect banners only; zero before April 2025 (confirmed by the digital team) | A period marker, not a media effect; handle the period explicitly | `01_...` section 3.1, A4 |
| Banner channel | About 98% PulsePoint | Report PulsePoint separately; totals with and without programmatic display | `01_...` |
| Double counting | HQ email counted three times; iRep twice | One source per activity | `11_...` section 6 |
| Light / deep engagement | **Our internal definitions, not vendor-reported**; rule per vendor metric not written down; total is not light + deep | Write the rule down and map it to OE's reach / interaction / engagement (R / I / E) | Meeting (A3), `10_...` section 2 |
| Smaller vendors | Biopharm, Haymarket, ReachMD, MJH, MD Calc, Impiricus active in 2025 to 2026 | Keep **each vendor on its own** (team request) | Meeting (A1, A2), `40_...` section 4.1 |
| OE 2.0 | Uses vendor + placement, R / I / E per vendor metric, content categories and timing; 12 recommended placements | Reuse OE's dictionary, flags and content tagging | `12_...` |
| OE roll-out | 3-month pilot with test and control; fully rolled out after 18 September 2026; no control group after that | Check whether digital features shift after the roll-out; no per-doctor OE flag | `12_...`, `13_...` O1 |
| DTC direct buys | Health Union, Healthline, Sharecare, WebMD stopped by early 2025 | 4 of the 9 kept DTC features describe channels that no longer run | `21_...` |
| DTC still running | Facebook + Instagram; SA360 paid search (6 branded DTC campaigns, about 12 to 18k clicks a month) | Rebuild DTC on what still runs | `21_...` |
| SA360 geography | Regional data by **US state** only; Metro (= DMA) not available for Kerendia after January 2025; region table misses 22 to 36% of HCP-campaign clicks from June 2026 | DTC search can only enter at state level | `21_...` |
| CLM | Below 1% of submitted Kerendia calls; mostly one standalone deck; last iVAs ended July 2025; new iVA campaign (about September 2026) not yet visible | CLM stays in the personal block; iVA needs campaign and content IDs | `clickstream_clm_data_review_2024_2026.md` |
| Request-a-Rep | Found in `PHCDW.PHCDW_CDM.RPT_DIGITAL_RAR_TAB`: 1,218 Kerendia requests January 2025 to October 2026, of which 340 followed by a rep call (median 7 to 9 days) | Strong intent signal, but rare; also a direct field action | Snowflake check, `40_...` section 4.4 |

---

## 3. Decisions taken (from the digital team meeting)

| # | Decision | Effect on the plan |
| --- | --- | --- |
| A1 / A2 | Each vendor kept on its own, including the smaller ones; Impiricus not grouped into "other" (Q4 OE scope for SMS); ReachMD optional | One dictionary entry per vendor and placement; no "other" bucket except for truly unmapped rows |
| A3 | Light and deep engagement are our internal definitions | Document the rule; crosswalk to OE's R / I / E |
| A4 | Doceree, OpenEvidence and PeerDirect banners started in April 2025 | Treat `BANNER_TACTIC` as a period effect; test training windows |
| A5 | New and changed signals must be included: iVA, Request-a-Rep, New Writers, Impiricus SMS, health-system formulary wins, dynamically refreshed target lists | New family 3; data acquisition in section 5 |
| A6 | Keep the indication (HF / T1D / CKD); Q4 target-list rule: HF = cardiologists, T1D = T1D target list, CKD = remaining HCPs | Indication field on every digital family |
| A7 | Not resolved; recommendation: digital / OE team owns the definitions, NBA / data team operationalises them | Roles in section 9 |
| D3 | NBA = who / why (monthly); OE = when / what / how (weekly); RAR and New Writers can supplement the list between refreshes | Interface in section 7 |

Still open: A8, B, C, D1 and D2 in `40_...` section 7.

---

## 4. Target design: the five feature families

All families share three rules: **NPI** as doctor key (BH_ID to NPI through `kerendia_oe_npi_bhid_mapping_inference`, joined to the NBA doctor key in the combine step); windows that end at the last **complete** month before the anchor date (1, 3, 6, 12 months; no moving-start `RUNNING_` features); and a **fixed schema** generated from config tables, not from run-time `distinct()`.

| # | Family | What it describes | Main source | Grain | Example features | Approx. candidates | Detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **HCP paid media** | Exposure and engagement with medical websites, apps and 3rd-party emails, by vendor and placement | `kerendia_oe_journey.mmx_fnl_combined_aggr_tab` + placement dictionary | NPI × month | `DIGITAL_TOTAL_EXPOSURE_3M`, `DIGITAL_PLC_DOXIMITY_DOCSPOT_EXPOSURE_3M`, `DIGITAL_ENGAGEMENT_RATE_6M`, `DIGITAL_DAYS_SINCE_LAST_ENGAGEMENT`, `DIGITAL_N_VENDORS_3M` | 100 to 140 | `13_...` P1 to P7 |
| 2 | **HQ email** | Bayer head-office email (SFMC) | Notebook 15 email event log (single source); MMX HQ email excluded | BH_ID × event | Sent, unique open / click, open and click rate, unsubscribe and bounce status, days since last open | about 12 | `13_...` P8, `30_...` section 2 |
| 3 | **High-intent signals** (new) | The doctor **asked** for something, or a strong market event happened | RAR table, New Writer, formulary wins, Impiricus SMS | Doctor × event date | `RAR_LAST_6M_FLAG`, `RAR_COUNT_12M`, `DAYS_SINCE_LAST_RAR`, `RAR_TYPE_SAMPLES_FLAG`, `NEW_WRITER_LAST_3M_FLAG`, `FORMULARY_WIN_AFFIL_6M_FLAG`, `SMS_ENGAGED_3M_FLAG` | 10 to 15 | Section 4.1 |
| 4 | **DTC market context** | Patient-facing media pressure where the doctor practises; a **control**, not a doctor lever | Facebook + Instagram (DMA), SA360 DTC branded search (state) | DMA or state × month, assigned to doctors | `DTC_SOCIAL_IMPRESSIONS_3M_PER_1K_ADULTS`, `DTC_SEARCH_CLICKS_3M_PER_1K_ADULTS` (state), `DTC_MONTHS_SINCE_LAST_CAMPAIGN` | 4 to 8 | Section 4.2 |
| 5 | **Engagement depth and content** (later) | OE-style R / I / E per placement and content categories | `kerendia_oe_journey.oe_kerendia_fact_npp_inference`, OE flag file, OE content tagging, message-arc / content ID document, iVA IDs | NPI × month | `DIGITAL_EVT_DOXIMITY_DOCSPOT_E_3M`, `DIGITAL_CONTENT_ACCESS_COVERAGE_6M` | 40 to 60 | `13_...` Phase 2 |
| all | **Indication dimension** | HF / T1D / CKD split of the main totals | Brand value + Q4 target-list rule + T1D list | Same as the family | `DIGITAL_HF_EXPOSURE_3M` | 6 to 12 | A6 |

Feature selection uses the same method as the main NBA 3.1 model. Expected result: about 30 to 60 digital features kept.

### 4.1 High-intent signals: how to use them

These signals are rare (about 1,200 Request-a-Rep requests in 22 months, against an NBA universe of tens of thousands of doctors) and very close to a field action. We therefore propose **two uses**, to be decided with the NBA and field teams:

| Use | How | Pros | Cons |
| --- | --- | --- | --- |
| **A. Model features** | Flags, counts and recency (as above), built strictly before the anchor | Lets the model learn how much a request is worth | Few positive doctors; importance may be unstable; risk of leakage through the follow-up |
| **B. Business rule in the NBA dropdown list** | A doctor with an open request (no follow-up call within N days) is always shown, with the reason "requested a rep on <date>" | Direct, explainable value: about 880 requests had no follow-up call | Not learned from data; needs a rule owner |

**Recommendation:** build both; test A in experiment E6 (section 8); implement B regardless of the model result, because it answers a clear business need.

**Leakage rule.** Only information known at the anchor may be used: request date and type, and follow-up status **as of** the anchor date. A call made after the anchor must never mark a request as followed up.

### 4.2 DTC: what changes

* **Drop** the direct-buy vendor columns (Health Union, Healthline, Sharecare, WebMD). Their source has stopped, so at inference they are zero or stale; in NBA 3.0 they mostly carry a period effect.
* **Keep** Facebook + Instagram at DMA × month, lagged by one month and expressed per 1,000 adults.
* **Add** SA360 DTC branded search at **state** × month (Metro / DMA is not delivered for Kerendia after January 2025).
* **Optional:** HCP paid search (`KER_HCP_` campaigns, about 85% of Kerendia SA360 clicks) at state level as market context, only if the region-table gap from June 2026 is explained.
* Keep the block small (4 to 8 features): there are about 210 DMAs and 50 states.
* Answer the open questions Q-A1 to Q-D6 and Q-B7 to Q-B10 in `21_...` first.

### 4.3 What stays out of the digital block

* **iRep email** and **CLM / clickstream**: personal promotional block (avoids double counting).
* **New iVA campaign**: joins family 5 once campaign and content IDs are available.
* **OE recommendations as an NBA input**: not in v1 (circularity risk); revisit after the roll-out check.

---

## 5. Data readiness

| Data | Location | Coverage / key | Status | Gap / action | Owner |
| --- | --- | --- | --- | --- | --- |
| MMX paid media + HQ email | `kerendia_oe_journey.mmx_fnl_combined_aggr_tab` (refreshed by the `Digital` notebook) | All Kerendia brand values; NPI; `DATE_ACT` | **Ready** | Placement dictionary with every vendor on its own; vendor codes for ConnectiveRx, Nativo, Healthcast; written light / deep rule | NBA team (build), digital team (review) |
| HQ email events | `HCP_EMAIL_LIST` (notebook 15) | BH_ID; event date | **Ready** | Confirm a campaign / email ID for unique opens | NBA team |
| Request-a-Rep | `PHCDW.PHCDW_CDM.RPT_DIGITAL_RAR_TAB` (daily); raw history from January 2024 in `KERENDIA_HCP_RAR_EXTRACTS` | 1,218 Kerendia requests since January 2025; BH_ID on almost all rows, NPI on about 46% | **Found** | Map BH_ID to NPI; count distinct doctors and overlap with the NBA universe; decide on the 2024 raw history; do not copy personal data (name, email, phone) | NBA team |
| New Writer | First Kerendia Rx per doctor, from the claims data behind the NBA 3.1 Rx features | NPI; first Rx date | **To confirm** | Agree the definition used by OE's dynamic target list (lookback, claims source) | NBA and OE teams |
| Impiricus SMS | MMX, tactic `SMS Messages` | March to December 2025; 10.1k doctors | **Partial** | No rows after December 2025 in MMX: confirm whether SMS continues and where 2026 data lands | Digital team |
| Health-system formulary wins | Not located yet | Health system, date, affiliated doctors | **Missing** | Source and format from the OE enhancement scope; affiliation via MDM best affiliation | Digital / OE team |
| Indication / T1D target list | T1D list file (Samantha Meyers); digital-target table to get an HF / T1D / CKD field | Doctor; indication | **Requested** | Receive the file; apply the Q4 rule | Brand team (Samantha Meyers) |
| OE event-level digital | `kerendia_oe_journey.oe_kerendia_fact_npp_inference` + OE flag file | BH_ID; event date; five vendors | **Ready (OE)** | Measure BH_ID to NPI coverage | NBA team |
| OE content mapping / message arc | OE content tagging; message-arc / content ID document (OE SOW) | Content ID, category | **In progress (OE SOW)** | Bayer stakeholder validation of historical content mapping | OE team, digital team |
| iVA engagement | Veeva / clickstream, once tagged | Campaign and content IDs | **Missing** | Get campaign and content IDs for the new iVA campaign | Digital team |
| DTC social | `FUNNEL_PROD_INB2.FUNNEL__MK7FZ_CN_UWQY_VMROR.funnel_data_FacebookAds_Geo_dma` | DMA × day | **Ready** | Open questions in `21_...` | NBA team, DTC team |
| DTC search | `FUNNEL_PROD_INB2.FUNNEL__MK7FZ_CN_UWQY_VMROR.FUNNEL_DATA_NEW_SA360_REGION` | State × day, from July 2024 | **Ready (state only)** | No Metro; HCP-campaign click gap from June 2026 | NBA team, media agency |
| Population denominator | ACS / SDOH tables already used in Kerendia pipelines | DMA, state | **Ready** | Pick one vintage | NBA team |

---

## 6. Work plan

Each phase ends with a gate (section 8). Phases 2 and 3 do not depend on phase 1 and can run in parallel with it.

| Phase | Content | Main tasks | Experiments | Depends on |
| --- | --- | --- | --- | --- |
| **0. Foundations** | Fix what is broken in NBA 3.0 | `13_...` F1 to F9 (brand filter, placement dictionary with every vendor on its own, case-insensitive mapping, unmapped report, complete months, no `RUNNING_`, one HQ email source, iRep out, fixed schema); indication field; written light / deep rule and crosswalk to R / I / E | E1 | Dictionary review by the digital team |
| **1. HCP paid media + HQ email** | Families 1 and 2 | Totals, channels, placements, rates, recency, diversity, trend; HQ email block | E2, E3 | Phase 0 |
| **2. High-intent signals** | Family 3 | RAR features (strictly before the anchor), New Writer, Impiricus SMS; formulary wins when the data arrives; RAR business rule specified for the NBA dropdown list | E6 | RAR NPI mapping; New Writer definition; SMS 2026 data |
| **3. DTC refresh** | Family 4 | Drop direct-buy vendors; social (DMA) and DTC search (state), lagged and per 1,000 adults | E7 | Answers to `21_...` questions |
| **4. Depth and content** | Family 5 | OE R / I / E for the five event-level vendors; content categories; iVA when IDs exist | E4, E5 | BH_ID to NPI coverage; validated content mapping |
| **5. OE roll-out and freeze** | All | Roll-out stability check (before / after 18 September 2026); training window; final block; documentation in this folder | E8 | Phases 1 to 4 |

---

## 7. How NBA 3.1 and OE work together

| | NBA 3.1 | OE |
| --- | --- | --- |
| Question | **Who** to focus on, and **why** | **When**, **what** content, **how** (channel, cadence) |
| Refresh | Monthly HCP target list with drivers | Weekly sequencing |
| Digital in the model | Digital history as features (families 1 to 5) | Journey of recommended placements and content |
| Between refreshes | — | Request-a-Rep and New Writers can dynamically supplement the list |
| Output language | Actions in the **NBA dropdown list** | Doctors **recommended** to media partners (not "reached") |

To agree with the OE team: which NBA drivers OE reuses (for example the high-intent flags); how the NBA dropdown list and OE recommendations are presented together (D2); how to avoid circularity (NBA should not learn from OE's own recommendations).

---

## 8. Experiments and readiness gates

All experiments use the NBA 3.1 HCP-level model, target and validation split; only the digital block changes.

| Exp. | Digital block | Question |
| --- | --- | --- |
| E0 | NBA 3.0 digital block (18 features) | Baseline |
| E1 | E0 with foundations fixed | Effect of brand filter, fixed mapping and de-duplication |
| E2 | Families 1 (without placements) + 2 | Does a small clean block beat the baseline? |
| E3 | E2 + placements, every vendor on its own | Does vendor / placement detail add value? |
| E4 | E3 with event-level R / I / E for the five OE vendors | Event-level vs MMX |
| E5 | E4 + content categories | Does content add value? |
| E6 | Best so far + high-intent signals | Do Request-a-Rep, New Writer and SMS add value as features? |
| E7 | Best so far + rebuilt DTC (instead of NBA 3.0 DTC) | Does current DTC context add value; does dropping the stopped vendors cost anything? |
| E8 | Best so far, trained post-roll-out only or with a period indicator | Does the OE roll-out change what works? |

**Measures:** NBA 3.1 validation metric; SHAP share of the digital families; rank of the best digital feature; number of digital features kept; stability of importance across time folds; and, for each kept feature, whether it maps to a vendor, placement, content or signal the business recognises.

| Gate | Ready when |
| --- | --- |
| G0 | Dictionary reviewed by the digital team (every vendor on its own); unmapped share below 1%; light / deep rule written; HQ email and iRep single-source decisions; fixed schema reproduced twice; E1 run |
| G1 | Families 1 and 2 built for all training instances; leakage check passed; E2 and E3 compared with E0 |
| G2 | RAR mapped to NPI with coverage known; New Writer definition agreed with OE; E6 run; RAR business rule specified |
| G3 | DTC questions in `21_...` answered; E7 run |
| G4 | BH_ID to NPI coverage measured; content mapping validated; E4 and E5 run |
| **G5 (freeze)** | Roll-out check done and training window chosen (E8); final digital block documented (same structure as files 10 and 11); feature list frozen in config; inference run reproduces training columns |

---

## 9. Roles

Following A7: the digital / OE team owns the **definitions**, the NBA / data team **operationalises** them.

| Area | Digital team | OE team | NBA team | Brand (Samantha Meyers) |
| --- | --- | --- | --- | --- |
| Placement dictionary, vendor codes | Owns and reviews | Shares OE placement names | Builds and monitors (unmapped report) | |
| Light / deep rule, R / I / E crosswalk | Owns the definition | Shares OE flag file | Documents and implements | |
| Request-a-Rep, Impiricus SMS, iVA IDs | Provides data and context | | Builds features and the business rule | Confirms business value |
| New Writer, dynamic target list | | Shares the definition | Builds the features | |
| Formulary wins | Provides data | Shares the OE enhancement design | Builds the features | |
| T1D target list, indication rule | | | Applies it | Provides the file |
| Content mapping / message arc | Validates | Delivers (SOW) | Uses it in family 5 | |
| Experiments, gates, freeze | Reviews results | Reviews coordination | Owns | Reviews results |

---

## 10. Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| Small vendors kept on their own are sparse | Many near-zero columns | Let feature selection drop them; report which vendors were dropped and why |
| High-intent signals are rare | Unstable importance | Flags and recency rather than counts; business rule (use B) regardless of model result |
| Leakage from follow-up or post-anchor data | Over-optimistic model | Everything as of the anchor; leakage check at every gate |
| Vendors rename tactics | Activity moves to unmapped | Pattern-based dictionary, unmapped report and alert |
| PulsePoint dominates volume | Totals reflect one vendor | Totals with and without programmatic display |
| OE roll-out changes digital patterns | Training and inference differ | E8; period indicator or post-roll-out training |
| DTC geography limited (no Metro, state-level search) | Weak DTC signal | Keep DTC small; treat it as a control |
| Data not delivered (formulary wins, iVA IDs, SMS 2026) | Families 3 and 5 incomplete | Build what is ready; leave missing items out of the frozen schema |
| Digital remains weak in NBA | Little model gain | Accept a small block; value can also come from the business rule and from OE |

---

## 11. Next actions

| # | Action | Owner |
| --- | --- | --- |
| 1 | Review this plan with the NBA, digital and OE teams | NBA team |
| 2 | Finalise the placement dictionary with every vendor on its own; confirm vendor codes (ConnectiveRx, Nativo, Healthcast) | NBA + digital team |
| 3 | Write down the internal light / deep rule per vendor metric | Digital team, with the NBA team |
| 4 | Map Request-a-Rep to NPI; count distinct doctors and overlap with the NBA universe; check prescribing after the request | NBA team |
| 5 | Agree the New Writer definition with OE | NBA + OE teams |
| 6 | Receive the T1D target list and apply the Q4 indication rule | Samantha Meyers, NBA team |
| 7 | Locate the formulary-win and Impiricus SMS 2026 data | Digital / OE team |
| 8 | Answer the DTC questions in `21_...` | NBA team, DTC team |
| 9 | Run E0 and E1 | NBA team |
