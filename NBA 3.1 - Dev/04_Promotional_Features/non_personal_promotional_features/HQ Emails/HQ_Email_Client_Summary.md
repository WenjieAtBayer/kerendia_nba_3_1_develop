# HQ Email Features (Family 2): NBA 3.0 vs NBA 3.1

**Audience:** Kerendia brand, analytics, OE and CRM / email teams  
**Scope:** Family 2, HQ email (Kerendia marketing emails sent by Bayer head office, and what the doctor did with them)  
**Notebook:** `HQ Emails/15_promotional_features_HQ_Emails_new` (rewrite of NBA 3.0 `03_HCP_Level_Features/15_promotional_features_HQ_Emails`)  
**Based on:** sections 1, 3.2 and 6.6 of `52_digital_feature_families_nba30_vs_nba31.md`, the NBA 3.1 notebook code and its run on 6 November 2026 (team cohorts, `PROVIDER_ID` key, team output layout)  
**Date:** 6 November 2026

> iRep email (sent by a rep), HCP paid media, calls, samples and DTC (patient) media are **not** in this family. Each has its own feature notebook.

---

## Summary in one page

* **The problem.** In NBA 3.0, **none** of the 5 HQ email features was kept by the model. The same emails also reached the model a second time through the Digital block (MMX), where they ranked **688, 695 and 698 of 752**.
* **Why.** (1) Every repeat open and click was counted, so one doctor reopening an email 20 times looked like 20 opens. (2) There was one 90-day window for one cohort only. (3) Unsubscribes and bounces were counts in 90 days, not an answer to "can we still email this doctor?". (4) The columns came from a dynamic pivot. (5) The NBA 3.0 source table (`HCP_EMAIL_LIST`) can no longer be read.
* **What NBA 3.1 does.** It reads **one** source (`ANLT_BASE_FACT_NONPERSONAL_PROMOTIONS`, channel `HQ EMAIL`), keys doctors by **`PROVIDER_ID`** (the key used by the other NBA 3.1 promotional blocks, NBA 3.1 HCP universe only), uses the team's **28 promotional cohorts c1 to c28** (lookback ends on the 17th) with **1 / 3 / 6 / 12 month windows**, counts **unique** opens and clicks per email, and adds rates, a trend, recency and **status flags** (currently unsubscribed, emailable). **15 fixed features.**
* **Result.** 3,112,543 `PROVIDER_ID` x cohort rows (cohorts c1 to c28, lookback ends 17 Jun 2024 to 17 Sep 2026; all 28 built, each with a full 12 months of data). All quality checks (QC1 to QC10) pass, including a hand recompute of 5 doctors and a monthly reconciliation with MMX (0.97 to 0.99 every month).
* **Aligned with the team (6 Nov 2026).** Same cohorts, doctor key (`HCP_COHORT_ID` = `PROVIDER_ID` + `_` + cohort), cohort columns and output folder / format as the Digital Engagement and High-Intent blocks. 78.8% of HQ email rows reach a universe `PROVIDER_ID`; the rest belong to doctors outside the NBA 3.1 universe or not in the mapping table and are dropped, as in the other blocks.
* **What this gives the business.** The model can tell a doctor who **reads** HQ emails from one who only **receives** them, see email fatigue, and NBA can stop proposing HQ email to doctors who have unsubscribed or whose address bounces.
* **Main open point.** Notebook 51 still builds 12 `DIGITAL_HQ_EMAIL_*` features from MMX. They are the same emails, so only one of the two blocks may go into the model (section 7).

---

## 1. NBA 3.0 compared with NBA 3.1

### 1.1 What was happening in NBA 3.0

The NBA 3.0 notebook read the Snowflake email log `PHCDW.PHCDW_CDM.HCP_EMAIL_LIST` (Kerendia emails, doctors keyed by BH_ID), kept the events of the single inference cohort `I01` and built **5 counts over the last 90 days** with a dynamic pivot on the event type:

| NBA 3.0 feature | Meaning | Kept by the model? |
| --- | --- | --- |
| `TOTAL_SENT_IN_LAST_3_MONTH` | HQ emails sent | No |
| `TOTAL_OPEN_IN_LAST_3_MONTH` | Open events (every reopen counted) | No |
| `TOTAL_CLICK_IN_LAST_3_MONTH` | Click events (every click counted) | No |
| `TOTAL_BOUNCE_IN_LAST_3_MONTH` | Bounces of any kind | No |
| `TOTAL_UNSUBSCRIBE_IN_LAST_3_MONTH` | Unsubscribe events | No |

The Digital block (`24_Features_Digital`) also kept HQ email from MMX as a channel and as a vendor; those copies were kept by the model at ranks 688, 695 and 698 of 752.

### 1.2 What the data showed (the five findings behind the change)

**Finding A: the NBA 3.0 source is gone, and MMX has the same emails with less detail.** `HCP_EMAIL_LIST` cannot be read (the view failed to compile in the Phase 1 run). `ANLT_BASE_FACT_NONPERSONAL_PROMOTIONS` holds the same activity with every event type, the NPI and the email name. Comparison with MMX, Jan 2025 to Oct 2026:

| Measure | MMX (HQ email channel) | ANLT (channel `HQ EMAIL`) | MMX / ANLT |
| --- | --- | --- | --- |
| Sent | 3,872,999 | 3,922,208 | 0.97 to 0.99 every month |
| Opens | 1,121,013 | 1,122,475 | about 1.00 |
| Clicks | 64,316 | 64,364 | about 1.00 |

MMX has **no bounce, no unsubscribe and no email name**, so it cannot give unique opens or status flags.

**Finding B: repeat opens inflate the counts.** 1,526,458 open rows correspond to only 1,112,114 distinct (doctor, email) pairs. The heaviest re-opener had **451 open rows for one email**.

**Finding C: unsubscribe and hard bounce are not permanent.** Of 10,437 doctors who ever unsubscribed, **829 still received a delivered HQ email more than 30 days later** (487 of them opened one). Of 20,708 doctors with a hard bounce, 5,893 later had a delivery (another address). A count of events in 90 days does not say whether the doctor can be emailed today.

**Finding D: five different bounce types were added together.** The source has `HARD BOUNCE` (address invalid) and `SOFT`, `BLOCK`, `TECHNICAL/OTHER`, `UNKNOWN BOUNCE` (temporary problems such as a full mailbox). NBA 3.0 mixed them in one count.

**Finding E: HQ email was counted twice.** Once in this family and again in the Digital block (MMX), so the model saw the same activity in two places.

### 1.3 What changed in NBA 3.1

| Topic | NBA 3.0 | NBA 3.1 |
| --- | --- | --- |
| Source | `HCP_EMAIL_LIST` (no longer readable) | `ANLT_BASE_FACT_NONPERSONAL_PROMOTIONS`, channel `HQ EMAIL`, read live from Snowflake |
| Doctor key | BH_ID (`HCP_COHORT_ID` = BH_ID + `_I01`) | `PROVIDER_ID` (team key): NPI (from the source, else BH_ID mapped to NPI) mapped to `PROVIDER_ID`, else BH_ID mapped directly; NBA 3.1 HCP universe only; `HCP_COHORT_ID` = `PROVIDER_ID` + `_` + cohort |
| Time grain | One inference cohort (`I01`) | The 28 team promotional cohorts c1 to c28 (`cohorts/promotional/cohorts.parquet`; c1 to c24 training, c25 to c26 testing, c27 to c28 holdout) |
| Windows | 90 days only | 1 / 3 / 6 / 12 months ending on each cohort's lookback end date (the 17th, inclusive) |
| Opens and clicks | Every event counted | Distinct emails opened / clicked |
| Rates and trend | None | Open rate, click rate (6 months, capped at 1); opens last 3 months vs prior 3 months |
| Unsubscribe / bounce | Counts in 90 days; all bounce types together | Status at the cutoff (unsubscribed, hard bounce, emailable); temporary bounces not used |
| Recency | None | Days since the last send, open and click |
| Feature list | Dynamic pivot (5 columns that depend on the data) | **Fixed list of 15 features** with a feature manifest and an expected schema |
| Duplication | Also in the Digital block | Counted once (notebook 51 decision open, section 7) |
| Quality checks | None built in | QC1 to QC10, including MMX reconciliation and a hand recompute; the notebook refuses to write if one fails |

---

## 2. Step-by-step feature creation

| Step | What happens | Why / business rule |
| --- | --- | --- |
| **1. Configuration** | Sets the source, the team cohort file, the HCP universe, the `PROVIDER_ID` mapping table, output paths and rules: data loaded from 1 Jun 2023, windows 1 / 3 / 6 / 12 months, rate cap 1, MMX ratio band 0.90 to 1.10. | All rules in one place, applied the same way at every run. |
| **2. Team cohorts and self-test** | Reads the 28 promotional cohorts c1 to c28 and checks there are 28, unique and in date order. The cutoff is the lookback end date (the 17th, inclusive); window w = `(cutoff - w months, cutoff]`. A self-test checks the c28 window edges (3M = 18 Jun to 17 Sep 2026). | Same cohorts as the Digital Engagement, High-Intent and personal-promotion blocks; nothing after the cutoff is used. |
| **3. Load HQ email events** | Reads Kerendia rows with channel `HQ EMAIL` from Snowflake from 1 Jun 2023 and stages them as parquet: **15,175,957 rows**, 1 Jun 2023 to **4 Nov 2026**. | c1's 12-month window starts on 18 Jun 2023, so every cohort has a full 12 months of data (`HQ_HISTORY_MONTHS` = 12 for all 28). |
| **4. Event types** | Maps `MTR_NM` to 7 event types: SENT, DELIVERED, OPEN, CLICK, UNSUB, HARD_BOUNCE, OTHER_BOUNCE. The notebook stops if a new `MTR_NM` value appears. | Address-invalid bounces are kept apart from temporary ones; a new event type is caught instead of silently creating a column. |
| **5. Doctor key (`PROVIDER_ID`)** | First the NPI: `NPI_NUM` when it is a valid 10-digit NPI, otherwise the NPI mapped from the BH_ID through `kerendia_oe_npi_bhid_mapping_inference`. The NPI is then mapped to `PROVIDER_ID` through `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING`; if it does not map, the BH_ID is mapped directly through the same table. Only `PROVIDER_ID`s in the NBA 3.1 HCP universe (`HCP_Universe_without_call_hcps`, 294,726 doctors) are kept; an NPI or BH_ID on several `PROVIDER_ID`s goes to the smallest one. | Same key, universe and tie rule as the Digital Engagement and High-Intent blocks, so the combine step joins on `HCP_COHORT_ID` with no extra mapping. Coverage: 89.0% of rows have an NPI and **78.8% reach a universe `PROVIDER_ID`** (almost all through the NPI). |
| **6. Cohorts with complete data** | Keeps only cohorts whose lookback end is on or before the last date in the source. All 28 are kept (c28 ends 17 Sep 2026; data ends 4 Nov 2026). | A cohort with missing days would look like a drop in activity. |
| **7. Build features** | For each `PROVIDER_ID` x cohort: sends, unique opens and clicks per window, rates, trend, status flags and recency (section 4). | See sections 3 and 4. |
| **8. Fixed schema and manifest** | Checks the columns against the fixed list of 15 features and writes a **feature manifest** (name, type, window, meaning, value to use for doctors not in the table). | Same columns at every run, each one documented. |
| **9. QC1 to QC9** | `HCP_COHORT_ID` unique, no event after the cutoff, fixed schema, every `PROVIDER_ID` in the HCP universe, rates between 0 and 1, trend between -1 and +1, nested windows (1M <= 3M <= 12M), days-since never negative, and the monthly MMX / ANLT sent ratio within 0.90 to 1.10 (result **0.971 to 0.994**). | Catches errors before the features reach the model. |
| **10. QC10 hand recompute** | Recomputes 3 features (sent 3M, unique opens 3M, days since last send) for 5 doctors of c28 directly from the raw events with separate code: **5 of 5 match**. | Independent check of the feature logic. |
| **11. Write outputs** | Writes the features (parquet, same layout as the other NBA 3.1 promotional blocks), the manifest and `expected_schema.json`. The write runs only if all checks pass. | No partial or unchecked output. |
| **12. Summary by cohort** | Doctors, sends, unique opens, open rate and unsubscribed doctors per cohort (section 3). | Quick view of how HQ email changes over time. |

**Outputs** (folder `kerendia_nba_3_1_volume/notebook_output/hq_email_nba_3_1/`, next to `digital_engagement_nba_3_1` and `high_intent_signals_nba_3_1`): `kerendia_nba_3_1_hcp_model_hq_email_features.parquet`, `feature_manifest.parquet` and `expected_schema.json`. Identifier columns: `HCP_COHORT_ID`, `PROVIDER_ID`, `COHORT`, `DATASET`, `PREDICTION_MONTH`, `SVC_DT` (lookback end), `HQ_HISTORY_MONTHS`, `PULL_DT`.

---

## 3. Cross join with the team cohorts (`PROVIDER_ID` x cohort level)

**Done.** Every HQ email event is crossed with the cohorts and kept for each cohort whose lookback end is on or after the event; the windows are then measured back from each cohort's lookback end.

* **Cohorts:** the 28 NBA 3.1 promotional cohorts from `kerendia_nba_3_1_volume/cohorts/promotional/cohorts.parquet`, the same file as the Digital Engagement, High-Intent and personal-promotion blocks. c1 (lookback end 17 Jun 2024, prediction month Jul 2024) to c28 (17 Sep 2026, prediction month Oct 2026). c1 to c24 training, c25 to c26 testing, c27 to c28 holdout. All 28 are built.
* **History:** the extract starts on 1 Jun 2023, so every cohort, including c1, has a full 12 months of data (`HQ_HISTORY_MONTHS` = 12 for all 28).
* **Rows in the table:** one row per `PROVIDER_ID` x cohort for universe doctors with **any HQ email event in the last 12 months, or who are currently unsubscribed**. Total: **3,112,543 rows**.
* **Doctors not in the table** are filled in the combine step: counts and flags 0, `HQ_EMAILABLE_FLAG` = 1, rates, trend and days-since NULL (column `NULL_IN_COMBINE` of the manifest).
* **Status flags use the full history** from Jun 2023, so an unsubscribe from 18 months ago still counts if no delivered email followed it.

How HQ email builds up over the cohorts (6 Nov 2026 run):

| Cohort | Dataset | Lookback end | Doctors in the table | Sent, last 3M | Unique opens, last 3M | Average open rate, 6M | Currently unsubscribed | Share emailable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| c1 | Training | 17 Jun 2024 | 80,286 | 307,667 | 83,792 | 0.261 | 1,059 | 0.964 |
| c8 | Training | 17 Jan 2025 | 90,383 | 168,500 | 53,581 | 0.275 | 2,110 | 0.949 |
| c14 | Training | 17 Jul 2025 | 127,892 | 717,827 | 205,458 | 0.273 | 4,507 | 0.936 |
| c20 | Training | 17 Jan 2026 | 120,205 | 384,544 | 117,300 | 0.309 | 5,588 | 0.926 |
| c25 | Testing | 17 Jun 2026 | 122,083 | 285,892 | 82,257 | 0.288 | 6,505 | 0.923 |
| c28 | Holdout | 17 Sep 2026 | 99,617 | 359,375 | 91,210 | 0.276 | 7,033 | 0.896 |

What the cohorts show:

* **HQ email peaked in spring 2025:** 761,131 to 930,560 sends in 3 months for c11 to c13 (lookback ends Apr to Jun 2025) and 717,827 for c14, against 168,500 to 469,909 in every other cohort.
* **Fewer doctors from c26** (100,443, down from 122,083 in c25): most likely because the last of the spring 2025 peak (June to mid-July 2025) leaves the 12-month window, so fewer doctors still have activity in the last 12 months.
* **Unsubscribes keep growing** (1,059 in c1 to 7,033 in c28) and the share of emailable doctors falls from 96.4% to 89.6%.
* **Open rate is stable** at 0.26 to 0.31 across all cohorts.

---

## 4. Types of HQ email features created

There are **15 features** in 6 groups, plus the identifier columns (`HCP_COHORT_ID`, `PROVIDER_ID`, `COHORT`, `DATASET`, `PREDICTION_MONTH`, `SVC_DT`, `HQ_HISTORY_MONTHS`, `PULL_DT`).

| Group | Features | Count | Rule |
| --- | --- | --- | --- |
| **Volume** | `HQ_EMAIL_SENT_1M`, `HQ_EMAIL_SENT_3M`, `HQ_EMAIL_SENT_12M` | 3 | Send events in the window: how much HQ emailed the doctor |
| **Unique engagement** | `HQ_EMAIL_UNIQUE_OPENS_3M`, `HQ_EMAIL_UNIQUE_OPENS_12M`, `HQ_EMAIL_UNIQUE_CLICKS_12M` | 3 | Distinct emails (`EMAIL_NM`) opened / clicked in the window |
| **Rates** | `HQ_EMAIL_OPEN_RATE_6M`, `HQ_EMAIL_CLICK_RATE_6M` | 2 | Unique emails opened (clicked) / unique emails sent in the same 6 months, capped at 1; NULL when nothing was sent |
| **Trend** | `HQ_EMAIL_OPENS_3M_VS_PRIOR_3M` | 1 | (opens last 3M - prior 3M) / (sum), from -1 to +1 |
| **Status at the cutoff** | `HQ_EMAIL_UNSUBSCRIBED_FLAG`, `HQ_EMAIL_HARD_BOUNCE_FLAG_12M`, `HQ_EMAILABLE_FLAG` | 3 | Unsubscribed = latest unsubscribe not followed by a delivered email; hard bounce in 12 months; emailable = not unsubscribed and not currently hard-bouncing |
| **Recency** | `HQ_EMAIL_DAYS_SINCE_LAST_SENT`, `HQ_EMAIL_DAYS_SINCE_LAST_OPEN`, `HQ_EMAIL_DAYS_SINCE_LAST_CLICK` | 3 | Days from the last event to the cutoff |
| **Total** | | **15** | |

File 52 asked for about 12 features (sent, unique open and click, open rate, click rate, bounce flag, unsubscribe status, days since last open). All are covered; the extra 3 (emailable flag, trend, days since last send / click) come from `30_nba_3_1_proposed_additional_features.md` section 2 and can be pruned after the model experiment.

Why rates are capped: a rate can exceed 1 when the doctor opens an email sent before the window (up to 1,972 doctors per cohort). Sent stays an event count, because it measures how much HQ pushed.

---

## 5. Changes in preprocessing

| Preprocessing step | NBA 3.0 | NBA 3.1 | Effect |
| --- | --- | --- | --- |
| Source | `HCP_EMAIL_LIST` | `ANLT_BASE_FACT_NONPERSONAL_PROMOTIONS`, `CHNL_ID = 'HQ EMAIL'` | Readable source with every event type, NPI and email name |
| Brand filter | Product type contains "Kerendia" | Kerendia rows of the HQ email channel | Same scope |
| Event types | Dynamic pivot on `EVENTTYPE` | Fixed mapping of `MTR_NM` to 7 types; stop on a new value | Stable columns; new event types flagged |
| Bounces | All types in one count | Hard bounce kept; soft, block, technical and unknown bounces grouped and not used | "Address invalid" no longer mixed with "mailbox full" |
| Doctor key | BH_ID | `PROVIDER_ID`: NPI (source first, else BH_ID mapped to NPI) mapped through `SOURCE_PROVIDER_BHID_NPI_MAPPING`, else BH_ID mapped directly; NBA 3.1 HCP universe only | Same key as the other NBA 3.1 promotional blocks; 78.8% of rows kept, doctors outside the universe dropped |
| Repeat events | Every open and click counted | Distinct emails per window | One heavy re-opener no longer looks like many readers |
| Time window | 90 days before the `I01` lookback end | 1 / 3 / 6 / 12 months ending on each team cohort's lookback end (the 17th); data from 1 Jun 2023 | Full windows for every cohort, c1 included; no information after the lookback end |
| Incomplete data | Not checked | Cohorts with a cutoff after the data end are dropped | No false drop in activity at the latest cohort |
| Unsubscribe | Count in 90 days | Status at the cutoff using the full history | Answers "can we email this doctor today?" |
| Missing values | Doctors with no activity not in the table | Defaults set in the manifest for the combine step | Consistent defaults across the block |

---

## 6. Business explanation of the features

| Feature group | Business question it answers | How the NBA model can use it |
| --- | --- | --- |
| **Volume** | How much has HQ been emailing this doctor, recently and over the year? | Shows email pressure; together with engagement, it shows whether more email is likely to help. |
| **Unique engagement** | How many different HQ emails did the doctor open or click? | Separates a doctor who reads several emails from one who reopened a single email many times. Clicks are the strongest email signal. |
| **Rates** | When HQ emails this doctor, how often do they open or click? | Tells "receives a lot" apart from "reads". A high rate marks an email-responsive doctor; a near-zero rate with high volume suggests email is not landing. |
| **Trend** | Is the doctor reading more or less than 3 months ago? | A falling trend can signal email fatigue; a rising trend shows growing attention. |
| **Status at the cutoff** | Can we still email this doctor? | Both a feature and a **business rule**: NBA should not propose "send HQ email" to a doctor who is unsubscribed or not emailable. |
| **Recency** | How long ago did the doctor last get, open or click an HQ email? | A recent open or click is a good moment for a follow-up action; a long gap can mean the doctor has gone cold. |

---

## 7. Next steps for features not created (or not yet complete)

| Item | Status | Next step |
| --- | --- | --- |
| **HQ email counted once** (12 `DIGITAL_HQ_EMAIL_*` features in notebook 51) | Open. Notebook 51 left unchanged, as agreed on 5 Nov 2026 | When notebook 51 next runs, either (a) remove its HQ email part P8 (its schema check then needs a config change, and doctors with HQ email but no paid media leave the digital table), or (b) drop the `DIGITAL_HQ_EMAIL_*` columns in the combine step. Never use both. Also confirm the older notebook `14_hcp_digital_phase1_feature_block` (which also builds P8) is not used. |
| `HQ_BOUNCE_RATE` (file 30) | Not built | Bounces are rare; the hard-bounce flag carries the signal. |
| `HQ_OPENS_PER_OPEN_DAY` (file 30) | Not built | Replaced by true unique opens per email. |
| HQ email content (what the email was about) | Not built here | `EMAIL_NM` is available on every row; content themes are covered by the OE family (Family 5, content tagging). |
| Join to the NBA 3.1 HCP feature table | Not done (combine step) | Join on `HCP_COHORT_ID` (`PROVIDER_ID` + cohort), as for the Digital Engagement and High-Intent blocks, and apply the defaults in the manifest. |
| Feature pruning | After the first model run | Drop low-SHAP features; the 3 sent windows and the 2 unique-open windows are correlated. |

Reverted test on notebook 51 (5 Nov 2026): a switch to remove P8 was added and the first cells were run, then the code was restored at the team's request. Its main output `hcp_digital_phase1_features` was not touched. Side effects: the placement dictionary was rewritten with identical content, one row was added to the unmapped report and the paid-media stage table was rebuilt. Some cell outputs in notebook 51 still show messages from that run and can be cleared.

---

## 8. Client alignment needed

| # | Topic | Question for the client | Current choice |
| --- | --- | --- | --- |
| 1 | `FACT_SENT_EMAIL` | Its status `Delivered_vod` is Veeva CRM naming and its 438,854 delivered emails do not match HQ volumes. Is it rep-triggered (iRep) email, or HQ email? | Treated as iRep; not used here. |
| 2 | Unsubscribe scope | Does a Kerendia unsubscribe block **all** HQ email or only Kerendia? 829 doctors still received deliveries after unsubscribing (brand-level opt-out or re-subscription?). | Status rule: unsubscribed until a later delivered email. |
| 3 | HQ email counted once | Which option for notebook 51: remove P8 there, or drop the columns in the combine step? | Decide when notebook 51 next runs. |
| 4 | Cohorts and doctor key across families | **Resolved (6 Nov 2026).** This block now uses the team's 28 promotional cohorts c1 to c28 and `PROVIDER_ID`, the same as Digital Engagement and High-Intent. | Team cohorts and `PROVIDER_ID`. |
| 5 | Doctors outside the NBA 3.1 universe | 21.2% of HQ email rows belong to doctors outside `HCP_Universe_without_call_hcps` or not in `SOURCE_PROVIDER_BHID_NPI_MAPPING`. Is it right to drop them, as the other blocks do? | Dropped (team rule). |
| 6 | Doctor universe | Doctors with no HQ email in 12 months and not unsubscribed get defaults in the combine step. Is "emailable = 1" the right default for them? | Yes (no evidence they cannot be emailed). |

---

## 9. Data sources missing or incomplete

| Source | Issue | Impact |
| --- | --- | --- |
| `PHCDW.PHCDW_CDM.HCP_EMAIL_LIST` (NBA 3.0 source) | No access; the view fails to compile | Replaced by ANLT; same activity confirmed with MMX. |
| Doctor ID on ANLT rows | Over the full load (Jun 2023 to Nov 2026): 89.0% of rows have an NPI, 78.8% reach a universe `PROVIDER_ID` | Rows with no universe `PROVIDER_ID` (21.2%) are dropped. |
| MMX HQ email | No bounce, unsubscribe or email name | Used only as a reconciliation check (QC9), not as a feature source. |
| Data end | Source ended on 4 Nov 2026 at the last run | All 28 cohorts built (c28 ends 17 Sep 2026). The next team cohort (lookback end 17 Oct 2026) would also have complete data if added to the cohort file. |

Figures confirmed by the 6 Nov 2026 run: 15,175,957 rows loaded, mapping coverage (89.0% NPI, 78.8% `PROVIDER_ID`), 294,726 universe doctors, 3,112,543 output rows, cohort results, MMX / ANLT ratio 0.971 to 0.994, hand recompute. Figures from the earlier exploration, not re-measured in the run: Findings A to C (Jan 2025 to Oct 2026 totals, repeat opens, unsubscribe and bounce counts) and the `FACT_SENT_EMAIL` count (438,854).
