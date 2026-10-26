# HCP Digital: Paid Media Features — NBA 3.0 (Legacy)

**Group:** Non-personal promotional features (promotion that does not involve a sales rep)  
**Notebook:** `24_Features_Digital` in `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Saved table:** `kerendia_nba_3_0_hcp_model_paid_search_features_for_inference`  
**Built from:** a review of the notebook code  
**Date:** October 22, 2026

## What is this document about?

Bayer uses a model called **Next Best Action (NBA)** to suggest, for each doctor, which Kerendia promotional action is most useful next. Kerendia is a Bayer medicine for chronic kidney disease in people with type 2 diabetes (and, more recently, heart failure). The model needs each doctor's recent history, turned into numbers called **features** (one fact about a doctor written as a number).

This document explains the **Digital** features: how often each doctor saw and interacted with Kerendia content online. It describes the **old version** of the pipeline (NBA 3.0); a "pipeline" is the chain of notebooks that runs one after another to prepare the data for the model.

**How it is organised:** the key ideas shared by the channels of this folder (time frame, dates table, helper notebooks, how monthly totals work) are in `00_README_folder_guide.md`. This file has: 1. In short, 2. Where the data comes from, 3. How the features are built step by step (*what*, *why*, *detail to know*), 4. The features explained, 5. What the final table looks like, 6. Things to watch out for.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code. Its meaning is always given next to it.

**About the numbers.** Figures come from the last time the notebook was run (29 April 2026). They will be different at the next run.

---

## 1. In short

This channel counts how often each doctor **saw** Kerendia online content (ads on medical websites and apps, digital emails, videos) and how often they **interacted** with it (opened, clicked). It answers questions like *"Has this doctor been seeing our banner ads? Do they click on them?"*

The data comes from Bayer's marketing-mix table ("MMX"), which collects reports from all digital vendors (companies such as Doximity or Medscape that show the content to doctors) into one place.

## 2. Where the data comes from

**Table:** `PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB` in Snowflake (database `PHCDW`, schema `PHCDW_CDM`). It is read with the `sfOptionscdpread` connection settings (see the introduction file). The doctor is identified by **NPI** ("National Provider Identifier", a doctor's official 10-digit US ID), not by the BHID.

**History of the source.** Until 29 April 2025 the notebook combined this table with an older one, `..._AGGR_TAB_TEMP`, for months before the lookback. That older table was retired ("deprecated"), so that version of the query is now commented out (switched off) and only the main table is used.

**One line of the table** = one piece of digital activity reported for one doctor on one day (one channel, one vendor, one tactic).

**Columns used:**

| Column | What it means | Example |
| --- | --- | --- |
| `NPI_NUM` | The doctor's NPI. Renamed `NPI_NUMBER`. | `1234567890` |
| `DATE_ACT` | Date of the activity | 2026-03-12 |
| `BRND_NM` | Brand name. Used only to keep Kerendia. | `Kerendia` |
| `CHANNEL` | The **type** of media | Banner, 3rd party email, HQ email, iRep email, Custom |
| `SRC_SYS_CD` | "Source system code": the **vendor or platform** that delivered the content and reported it | Doximity, Medscape, Epocrates |
| `TACTIC_NAME` | The **format** of the message | Banner, DocNews, Brand Alert, Video |
| `EXPOSURE` | Number of times the doctor was shown / sent the content | 5 |
| `LIGHT_ENGAGEMENT` | Number of small interactions (for example opening or viewing) | 2 |
| `DEEP_ENGAGEMENT` | Number of strong interactions (for example clicking through to read more) | 1 |
| `TOTAL_ENGAGEMENT` | Number of interactions overall, as reported by the vendor | 2 |

What exactly counts as "light" or "deep" is decided by the vendors and the marketing-mix (MMX) team, not by this notebook. One thing is visible in the data: total is **not** always light + deep. The notebook includes a check of HQ emails by month, and there total equals light every month (for example March 2026: light 26,341, total 26,341, deep 1,446). Ask the MMX team for the definitions before combining these measures.

**Which lines are kept:**

* Brand is Kerendia (in any capitalisation: `UPPER(BRND_NM) = 'KERENDIA'`).
* The doctor's NPI is not empty.
* The month of the activity is on or after the lookback start (`digital_start`, see step 1).
* There is **no end date**: everything up to today is kept.

**Size at the last run (29 April 2026):** 3,218,056 lines after the monthly summary in step 2.

## 3. How the features are built, step by step

**Step 1. Find the start date.**
*What:* read the dates table and take the lookback start of cohort `I01` (16 April 2025 at the last run). The code calls it `digital_start`.
*Why:* only the last year of activity is needed.

**Step 2. Read the data and add it up by month.**
*What:* the SQL query turns each activity date into the first day of its month (`DATE_TRUNC('MONTH', DATE_ACT)`, saved as `SVC_DT_M`, "service date, month"), converts channel and vendor names to capital letters, and adds up the four measures for each doctor, month, channel, vendor and tactic.
*Why:* the model uses monthly totals.
*Detail to know:* the query compares the **first day of the month** with the start date. With a start date of 16 April 2025, "1 April 2025" is earlier than "16 April 2025", so **April 2025 is left out completely** and the data starts in May 2025. And because there is no end date, the most recent (unfinished) month is included.

**Step 3. Make channel names consistent.**
*What:* four channel names are renamed: `CALL` becomes `CALLS`, `HQ EMAIL` becomes `HQ_EMAILS`, `IREP EMAIL` becomes `IREP_EMAILS`, `SAMPLE` becomes `SAMPLES`. Other channels keep their name.
*Why:* so the names match the rest of the pipeline and step 5 can remove calls and samples by name.

**Step 4. Make tactic names consistent.**
*What:* every tactic name is cleaned (spaces at the start and end removed) and translated to one of 15 fixed labels:

| Tactic name in the data | Becomes | What it is (general meaning; confirm details with the digital team) |
| --- | --- | --- |
| Any name **containing** "Banner" | `BANNER_TACTIC` | Display (picture) ad on a website or app. Since April 2025 banner names start with the campaign name, which is why the code looks for the word "Banner" anywhere in the name. |
| `CTV` | `CTV_TACTIC` | Connected TV ad (TV ads delivered over the internet). Marked as discontinued in the code. |
| `HQ Email` | `HQ_EMAIL_TACTIC` | Email from Bayer HQ. |
| `DocNews` | `DOCNEWS_TACTIC` | Sponsored news item shown to doctors. |
| `Video` | `VIDEO_TACTIC` | Video ad. |
| `IRep Email` | `IREP_EMAIL_TACTIC` | Email sent by a rep. |
| `Monograph Message` | `MONOGRAPH_MESSAGE_TACTIC` | Message shown next to the drug's information page in a medical reference app. |
| `DocSpot` | `DOCSPOT_TACTIC` | Sponsored placement in a doctor app. |
| `Brand Alert` | `BRAND_ALERT_TACTIC` | Short sponsored brand message in a doctor app. |
| `DocAlert` (was "Doc Alert" before April 2025) | `DOC_ALERT_TACTIC` | Short clinical message in a doctor app. |
| `Email` | `EMAIL_TACTIC` | Email from a vendor. |
| `Email Alert` | `EMAIL_ALERT_TACTIC` | Short alert email from a vendor. |
| `NativeVideo` | `NATIVEVIDEO_TACTIC` | Video that looks like the website's own content. |
| `FormularyOne` (was "Formulary" before April 2025) | `FORMULARY_TACTIC` | Message about insurance coverage ("formulary" = the list of medicines an insurer pays for). |
| Anything else | `OTHER_TACTIC` | Any tactic not in this list. |

*Why:* vendors rename tactics from time to time. Without this step, every renaming would create new, separate features for the same thing.
*Detail to know:* apart from Banner, a name must match **exactly** (after removing outer spaces); a small spelling change sends it to `OTHER_TACTIC`.

**Step 5. Remove rep calls and samples.**
*What:* lines with channel `CALLS` or `SAMPLES` are removed.
*Why:* rep calls and samples are already counted by their own notebooks (`25_promotional_features_call` and `17_promotional_features_samples`). The code comment notes the assumption that "calls" and "samples" vendors only appear with those channels.
*Detail to know:* HQ emails and rep (iRep) emails are **not** removed, even though they also have their own notebooks (`15` and `16`). See section 6.

**Step 6. Turn values into columns (three pivots).**
*What:* a **pivot** turns the values of one column into separate columns. The notebook builds three separate tables, each with one row per doctor and month:

* by **channel**: one set of 4 columns per channel (e.g. `BANNER_EXPOSURE`, `BANNER_LIGHT_ENGAGEMENT`, `BANNER_DEEP_ENGAGEMENT`, `BANNER_TOTAL_ENGAGEMENT`);
* by **vendor**: one set of 4 columns per vendor (e.g. `DOXIMITY_EXPOSURE`, ...);
* by **tactic**: one set of 4 columns per tactic label (e.g. `BANNER_TACTIC_EXPOSURE`, ...).

Each cell is the monthly total; empty cells are filled with 0. This is a **dynamic** pivot: the columns are created from whatever channels, vendors and tactics are in the data that day.
*Why:* the model needs one number per thing it measures, side by side.

Example of what a pivot does:

| Before: doctor | month | channel | exposure |
| --- | --- | --- | --- |
| Dr. Lee | 2026-03 | BANNER | 2 |
| Dr. Lee | 2026-03 | CUSTOM | 1 |

| After: doctor | month | BANNER_EXPOSURE | CUSTOM_EXPOSURE |
| --- | --- | --- | --- |
| Dr. Lee | 2026-03 | 2 | 1 |

**Step 7. Fill in the months and calculate the totals over time.**
*What:* for each of the three tables, `step2_fill_missing` gives every doctor a row for every month, and `step3_lag` adds the totals for the last 1, 3 and 6 months and the running total (see the introduction file, section 0.3). Empty cells are filled with 0.
*Why:* so that "last 3 months" really covers three months, even when a doctor had no activity in some of them.

**Step 8. Remove the single-month tactic columns.**
*What:* in the tactic table only, the original single-month columns (e.g. `BANNER_TACTIC_EXPOSURE`) are removed; the 1, 3 and 6-month and running totals stay. The channel and vendor tables keep their single-month columns.
*Why:* the code does not say. In practice nothing is lost, because `_IN_LAST_1_MONTH` has the same value as the single-month column.

**Step 9. Put the three tables together and rename.**
*What:* the tactic, channel and vendor tables are joined side by side on doctor + month (left joins starting from the tactic table; all three contain the same doctors and months, so no rows are lost). Remaining empty cells become 0. Every feature column gets the prefix `DIGITAL_`, spaces become `_`, and everything is in capital letters (e.g. `3RD PARTY EMAIL_EXPOSURE` becomes `DIGITAL_3RD_PARTY_EMAIL_EXPOSURE`).
*Why:* one table with clear, unique names.

**Step 10. Save.**
*What:* add the run date `PULL_DT` and overwrite the table `kerendia_nba_3_0_hcp_model_paid_search_features_for_inference`. Despite "paid search" in the name, it contains all digital channels. At the last run the table had 686 columns plus `PULL_DT`.

**Check cells in the notebook** (they do not change the data): a monthly summary of HQ email activity (number of doctors, light, deep, total, exposure), displays of the column lists, a row count, and a count of empty values per column.

## 4. The features explained

There are many digital features (684 at the last run), but they are all built from the same three building blocks. Once you know the blocks, you can read any name. Every feature counts **times shown** or **interactions**, for one doctor.

**Block 1: what the feature is about** (one of three kinds)

| Kind | Possible values (last run) | Question it answers |
| --- | --- | --- |
| Channel (type of media) | `3RD_PARTY_EMAIL`, `BANNER`, `CUSTOM`, `HQ_EMAILS`, `IREP_EMAILS` | *Which type of media reached the doctor?* |
| Source (vendor / website) | See the vendor table below | *Which website or app reached the doctor?* |
| Tactic (format) | `BANNER_TACTIC`, `BRAND_ALERT_TACTIC`, `CTV_TACTIC` (TV ads, discontinued), `DOC_ALERT_TACTIC`, `DOCNEWS_TACTIC`, `DOCSPOT_TACTIC`, `EMAIL_TACTIC`, `EMAIL_ALERT_TACTIC`, `FORMULARY_TACTIC` (insurance coverage message), `HQ_EMAIL_TACTIC`, `IREP_EMAIL_TACTIC`, `MONOGRAPH_MESSAGE_TACTIC` (drug information message), `NATIVEVIDEO_TACTIC`, `VIDEO_TACTIC`, `OTHER_TACTIC` | *What kind of message reached the doctor?* |

The list depends on the data: if a new vendor appears, new features appear automatically.

**Channels** (type of media):

| Value | What it is |
| --- | --- |
| `3RD_PARTY_EMAIL` | Emails sent to doctors by outside vendors on Bayer's behalf |
| `BANNER` | Display (picture) ads on websites and apps |
| `CUSTOM` | Custom (made-to-measure) programs with a vendor |
| `HQ_EMAILS` | Emails sent by Bayer HQ |
| `IREP_EMAILS` | Emails sent by reps |

**Vendors** seen in the saved list of the notebook (general descriptions; confirm with the digital team):

| Value | What it is |
| --- | --- |
| `DOCEREE` | Advertising network for doctors |
| `DOXIMITY` | Professional network and news app for US doctors |
| `EPOCRATES` | Drug-reference app for doctors |
| `HQ_EMAIL` | Bayer HQ email system |
| `IMPIRICUS` | Messaging platform for doctors |
| `IREP_EMAIL` | Rep email system |
| `MD_CALC` | Medical calculator app (MDCalc) |
| `MEDSCAPE` | Medical news and education website |
| `MJHLIFESCIENCES` | Medical publisher (journals and news sites) |
| `NATIVO` | Native-advertising platform (ads that look like site content) |
| `OPENEVIDENCE` | Medical search / AI answer app |
| `PEERDIRECT` | Media vendor for doctors |
| `PRESCRIBER_POINT` | Prescriber information platform |
| `PULSEPOINT` | Programmatic advertising platform (places ads automatically across many sites) |
| `REACHMD` | Medical audio / video programs |

The saved list shows 15 vendors, while the column count of the last run implies 18 (see below), so three more vendors appeared after that list was saved. To see the current list, run the cell that displays `df_src_sys_cd.columns` in the notebook.

**Tactics:** the 15 labels from step 4. A tactic only gets features if it appears in the data (14 did at the last run).

**Block 2: what is counted**

| Name part | What it counts | In plain words |
| --- | --- | --- |
| `EXPOSURE` | Times the doctor was shown the content | "How much did we reach them?" |
| `LIGHT_ENGAGEMENT` | Small interactions (open, view) | "Did they glance at it?" |
| `DEEP_ENGAGEMENT` | Strong interactions (click through) | "Were they really interested?" |
| `TOTAL_ENGAGEMENT` | All interactions | "How much did they respond overall?" |

**Block 3: over which period**

| Name looks like | Period | Example meaning |
| --- | --- | --- |
| no time ending | That month only | `DIGITAL_BANNER_EXPOSURE` = banner ads seen this month |
| `_IN_LAST_1_MONTH` | That month only (same as above) | |
| `_IN_LAST_3_MONTH` | That month and the 2 before it | |
| `_IN_LAST_6_MONTH` | That month and the 5 before it | |
| starts with `RUNNING_` | Everything since the start of the data | `DIGITAL_RUNNING_BANNER_EXPOSURE` = all banner ads seen since May 2025 |

(Tactic features do not have the "no time ending" version, see step 8.)

**How many columns.** Each channel and each vendor gives 4 measures x 5 periods = 20 columns. Each tactic gives 4 x 4 = 16 columns. At the last run: 5 channels x 20 + 18 vendors x 20 + 14 tactics x 16 = 100 + 360 + 224 = **684 features**, plus the 2 key columns = 686.

**Putting it together.** Every name is `DIGITAL_` + block 1 + block 2 + block 3:

| Feature | How to read it |
| --- | --- |
| `DIGITAL_BANNER_EXPOSURE` | Number of Kerendia banner ads the doctor was shown this month. |
| `DIGITAL_DOXIMITY_TOTAL_ENGAGEMENT_IN_LAST_3_MONTH` | Number of times the doctor interacted with Kerendia content on Doximity in the last 3 months. |
| `DIGITAL_HQ_EMAILS_DEEP_ENGAGEMENT_IN_LAST_6_MONTH` | Number of strong interactions (clicks) with HQ emails in the last 6 months. |
| `DIGITAL_RUNNING_DOCNEWS_TACTIC_EXPOSURE` | Number of DocNews items the doctor was shown since the start of the data. |

**Example.** Dr. Lee saw 4 banner ads in January, 0 in February and 2 in March. In her March row: `DIGITAL_BANNER_EXPOSURE` = 2, `DIGITAL_BANNER_EXPOSURE_IN_LAST_3_MONTH` = 6, `DIGITAL_RUNNING_BANNER_EXPOSURE` = 6 (if the data starts in January).

## 5. What the final table looks like

One row per doctor per month (a different shape from the other channels):

| Column | Meaning |
| --- | --- |
| `NPI_NUMBER` | The doctor (NPI) |
| `SVC_DT_M` | The month (written as its first day, e.g. 2026-03-01). Every doctor has every month from the first to the last month in the data. |
| `DIGITAL_...` | All the features above (684 at the last run) |
| `PULL_DT` | Date the notebook was run (text, e.g. `2026_04_29`) |

Because there is a row for every month, a later step has to choose the right month for each doctor. The doctor is identified by NPI here, not by BHID.

## 6. Things to watch out for

* **The first lookback month is missing.** Because the query compares the first day of each month with a mid-month start date (step 2), the month in which the lookback starts is left out (April 2025 at the last run).
* **The latest month may be incomplete.** There is no end date, so the current month is included even if its data has not fully arrived.
* **HQ emails and rep emails are counted twice in the model.** They are kept here (as `HQ_EMAILS` / `IREP_EMAILS` channels and `HQ_EMAIL` / `IREP_EMAIL` vendors) and are also counted by their own notebooks (`15` HQ Emails and `16` iRep).
* **"Since the start" (`RUNNING_`) features depend on when the data starts.** Since the start moves with every run, the same doctor in the same month can get a different running total in different runs.
* **The features change from run to run.** Because the pivots are dynamic, a new vendor or tactic adds columns and a vanished one removes them. The model may then find columns missing or unexpected.
* **Exact tactic matching.** A small change in a tactic name (other than Banner) silently moves its activity into `OTHER_TACTIC`.
* **"Light" and "deep" are not documented.** Their definitions come from the vendors; total is not always light + deep (section 2).
* **A later step must pick the right month.** Because every month is kept, the combining notebook must use the last full month before the anchor date; using a later month would let the model see data from after the lookback.
