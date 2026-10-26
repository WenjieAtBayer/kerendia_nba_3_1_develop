# ARCHIVE — Non-Personal Promotional Features — NBA 3.0 (Legacy), combined version

> **Archived on October 26, 2026.** This earlier single-file review has been replaced by `00_README_folder_guide.md`, `10_hcp_digital_paid_media_nba_3_0.md`, `11_hcp_hq_emails_nba_3_0.md` and `20_dtc_direct_buy_social_nba_3_0.md`. Its Samples, Speaker Programs and FTP sections now belong to `market_access_promotional_features` and `personal_promotional_features`. Keep for reference only; do not update.

**Scope:** promotion that does not involve a sales rep: Digital (`24`), HQ Emails (`15`), DTC (`34`), Samples (`17`), Speaker Programs (`14`), Free Trial Program / FTP (`19`)  
**NBA 3.0 (legacy Ops):** `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Companion file:** `non_personal_promotional_features_strategic_file_nba_3_0_legacy.md`  
**Built from:** a review of the code in each notebook listed above  
**Date:** October 22, 2026

## What is this document about?

Bayer uses a model called **Next Best Action (NBA)** to suggest, for each doctor, which Kerendia promotional action is most useful next (for example: send an email, invite them to an event, deliver samples). Kerendia is a Bayer medicine for chronic kidney disease in people with type 2 diabetes (and, more recently, heart failure).

To make its suggestions, the model needs to know each doctor's recent history. That history is turned into numbers called **features**. A feature is simply one fact about a doctor written as a number, for example *"this doctor opened 4 Kerendia emails in the last 3 months"*.

This document explains the features about **non-personal promotion**: all the promotion that does **not** involve a sales rep meeting the doctor. There are six types ("channels"):

| Channel | In plain words | Notebook |
| --- | --- | --- |
| Digital | Online ads and digital messages the doctor saw (banners, medical websites, apps, emails) | `24_Features_Digital` |
| HQ Emails | Marketing emails sent to the doctor by Bayer's head office | `15_promotional_features_HQ_Emails` |
| DTC (Direct-to-Consumer) | Ads shown to **patients** (not doctors) in the doctor's area | `34_promotional_features_DTC` |
| Samples | Free Kerendia sample packs given to the doctor | `17_promotional_features_samples` |
| Speaker Programs | Educational talks about Kerendia that the doctor attended | `14_promotional_features_speaker_program` |
| Free Trial Program (FTP) | Patients who got their first Kerendia supply free with a voucher, on this doctor's prescription | `19_ftp_features` |

This describes the **old version** of the pipeline (NBA 3.0). A "pipeline" is the chain of notebooks that runs one after another to prepare the data for the model.

**How each channel section is organised:**

1. **In short**: what the channel is and why it matters.
2. **Where the data comes from**: the exact table, what one line of it represents, every column used and what it means, and which lines are kept.
3. **How the features are built, step by step**: every step the notebook takes. For each step: *what happens*, *why*, and *how it appears in the code*.
4. **The features explained**: every feature, what it counts, how to interpret it, with an example.
5. **What the final table looks like**: every column of the saved table.
6. **Things to watch out for**: every known problem, fully explained. Codes such as LH-1 or LSP-2 are references to the companion file (LH = HQ Emails, LT = DTC, LS = Samples, LSP = Speaker Programs, LF = Free Trial Program); the problem is also explained here, so you do not need the companion file to understand it.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code, so you can search for it. Its meaning is always given next to it.

**About the numbers.** Figures such as "159,970 rows" come from the last time each notebook was run (the date is given). They will be different the next time the notebook runs.

---

## 0. Key ideas to understand first

### 0.1 The time frame: what period do the features cover?

Imagine the model is used on **1 June 2026** (the anchor date). It looks back over the previous year of activity, but stops about two weeks early, because recent data takes time to arrive:

| Date | Meaning |
| --- | --- |
| 17 May 2025 | Start of the lookback period |
| 17 May 2026 | End of the lookback period (the "as of" date for every feature) |
| 1 June 2026 | Anchor date: the model makes its suggestions |
| 7 June to 7 July 2026 | The period the model tries to predict |

So every feature answers a question like *"what happened up to 17 May 2026?"*.

**Where these dates come from.** Every notebook reads a small table called `promotional_cohort_inference_dates` (saved in `ops_pipeline/notebook_output/`) and takes the row for cohort `I01`. Its columns:

| Column | Meaning | Example value |
| --- | --- | --- |
| `SERIAL_NO` | Row number | `1` |
| `ANCHOR_DATE` | The anchor date | `2026-06-01` |
| `PREDICTION_START_DATE` | First day of the prediction window | `2026-06-07` |
| `PREDICTION_END_DATE` | Last day of the prediction window | `2026-07-07` |
| `MERGE_KEY` | A helper column (always `1`) that other notebooks use to attach these dates to their tables. Not used by these six notebooks. | `1` |
| `COHORT` | Cohort name | `I01` |
| `LOOKBACK_START_DATE` | First day of the lookback | `2025-05-17` |
| `LOOKBACK_END_DATE` | Last day of the lookback | `2026-05-17` |

The example values come from the Samples run of 27 May 2026. Because each notebook was last run on a different day, the saved tables use different dates. For example, the Free Trial Program table was last built with a lookback ending 17 September 2025.

### 0.2 Things every notebook shares

| Topic | What happens |
| --- | --- |
| Doctor key | The four "one row per doctor" notebooks identify a doctor with `HCP_COHORT_ID` = BHID + `_` + cohort, for example `BH10000342_I01`. Joining the cohort name to the ID keeps doctors separate across cohorts during training; in inference it is always `_I01`. |
| Attaching the dates | Each of those notebooks does a **cross join** between its data and the dates table: every row gets the lookback start and end dates written next to it. With one cohort, this does not create extra rows; it only adds the date columns. Then rows outside the lookback are removed. |
| Helper notebook `00_connection` | Run at the start of every notebook. It installs the Snowflake connector, reads Bayer's Snowflake login (user, account and private key) from the secure secret store (`US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`), and defines `Get_Data_Snowflakes(query)`: a function that sends a SQL query to Snowflake (database `PHCDW`, schema `PHCDW_CDM`, warehouse `PROD_CYRUS_BI_WH`) and returns the result as a table. It also defines `sfOptionscdpread`, a second set of connection settings (schema `PHCDW_DSAA`, warehouse `PROD_DATA_SCIENCE_CYRUS_WH`) that the Digital notebook uses directly. Both reach the same Snowflake account. |
| Helper notebook `00_config` | Run at the start of every notebook except DTC. It loads the latest approved run dates from a control table (`get_latest_approved_dates()`), shared file paths, and settings for other (patient-level and claims) feature notebooks. The six notebooks here run it but take their dates from the `promotional_cohort_inference_dates` table instead. |
| Helper notebook `00_step23_function` | Run at the start of every notebook except DTC (which only runs `00_connection`). Defines the monthly functions `step2_fill_missing` and `step3_lag` (used by Digital) plus two variants not used here (`step3_lag_avg`, averages; `step3_lag_distinct`, distinct counts). The daily functions (`step2_fill_missing_date`, `step3_lag_date`) are written inside each daily notebook instead. |
| Run date `PULL_DT` | Added to every saved table: the date the notebook ran. Stored as text like `2026_05_27`, except in the Free Trial Program table, where it is a real date. |
| Where tables are saved | As Delta tables in `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/`. Each run **overwrites** the previous table completely, including its list of columns. |
| What happens next | A later notebook, `99_Combine_Physician_Data_Promotional&Acc`, combines all channel tables into one row per doctor for the model. |

---

## 1. Digital / Paid Media (`24_Features_Digital`)

### 1.1 In short

This channel counts how often each doctor **saw** Kerendia online content (ads on medical websites and apps, digital emails, videos) and how often they **interacted** with it (opened, clicked). It answers questions like *"Has this doctor been seeing our banner ads? Do they click on them?"*

The data comes from Bayer's marketing-mix table ("MMX"), which collects reports from all digital vendors (companies such as Doximity or Medscape that show the content to doctors) into one place.

### 1.2 Where the data comes from

**Table:** `PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB` in Snowflake (database `PHCDW`, schema `PHCDW_CDM`). It is read with the `sfOptionscdpread` connection settings (section 0.2).

**History of the source.** Until 29 April 2025 the notebook combined this table with an older one, `..._AGGR_TAB_TEMP`, for months before the lookback. That older table was retired ("deprecated"), so that version of the query is now commented out and only the main table is used.

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

### 1.3 How the features are built, step by step

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
*Detail to know:* HQ emails and rep (iRep) emails are **not** removed, even though they also have their own notebooks (`15` and `16`). See section 1.6.

**Step 6. Turn values into columns (three pivots).**
*What:* the notebook builds three separate tables, each with one row per doctor and month:

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
*What:* for each of the three tables, `step2_fill_missing` gives every doctor a row for every month, and `step3_lag` adds the totals for the last 1, 3 and 6 months and the running total. Empty cells are filled with 0.
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

### 1.4 The features explained

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

### 1.5 What the final table looks like

One row per doctor per month (a different shape from the other channels):

| Column | Meaning |
| --- | --- |
| `NPI_NUMBER` | The doctor (NPI) |
| `SVC_DT_M` | The month (written as its first day, e.g. 2026-03-01). Every doctor has every month from the first to the last month in the data. |
| `DIGITAL_...` | All the features above (684 at the last run) |
| `PULL_DT` | Date the notebook was run (text, e.g. `2026_04_29`) |

Because there is a row for every month, a later step has to choose the right month for each doctor. The doctor is identified by NPI here, not by BHID.

### 1.6 Things to watch out for

* **The first lookback month is missing.** Because the query compares the first day of each month with a mid-month start date (step 2), the month in which the lookback starts is left out (April 2025 at the last run).
* **The latest month may be incomplete.** There is no end date, so the current month is included even if its data has not fully arrived.
* **HQ emails and rep emails are counted twice in the model.** They are kept here (as `HQ_EMAILS` / `IREP_EMAILS` channels and `HQ_EMAIL` / `IREP_EMAIL` vendors) and are also counted by their own notebooks (`15` HQ Emails and `16` iRep).
* **"Since the start" (`RUNNING_`) features depend on when the data starts.** Since the start moves with every run, the same doctor in the same month can get a different running total in different runs.
* **The features change from run to run.** Because the pivots are dynamic, a new vendor or tactic adds columns and a vanished one removes them. The model may then find columns missing or unexpected.
* **Exact tactic matching.** A small change in a tactic name (other than Banner) silently moves its activity into `OTHER_TACTIC`.
* **"Light" and "deep" are not documented.** Their definitions come from the vendors; total is not always light + deep (section 1.2).
* **A later step must pick the right month.** Because every month is kept, the combining notebook must use the last full month before the anchor date; using a later month would let the model see data from after the lookback.

---

## 2. HQ Emails (`15_promotional_features_HQ_Emails`)

### 2.1 In short

Bayer's head office ("HQ") sends Kerendia marketing emails to doctors. These are different from emails a rep sends personally. This channel counts, for each doctor, how many HQ emails were **sent** in the last 3 months and what the doctor **did** with them: opened, clicked, unsubscribed, or whether the email failed to arrive ("bounced").

It helps the model answer: *"Does this doctor read our emails? Is email a good way to reach them?"*

### 2.2 Where the data comes from

An email log with one line for every email "event". An event is one thing that happened to one email:

| Event | What it means |
| --- | --- |
| Sent | Bayer sent an email to the doctor. |
| Open | The doctor opened an email. If they open the same email 3 times, that is 3 events. |
| Click | The doctor clicked a link inside an email. Each click is a separate event. |
| Bounce | The email could not be delivered (for example, the address no longer exists). |
| Unsubscribe | The doctor asked to stop receiving Kerendia emails. |

**Table:** `PHCDW.PHCDW_CDM.HCP_EMAIL_LIST` in Snowflake, read with `Get_Data_Snowflakes` (section 0.2).

**One line of the table** = one email event for one doctor.

**Columns used:**

| Column | What it means |
| --- | --- |
| `BH_ID` | The doctor's Bayer ID (BHID) |
| `EVENTDATE` | The day the event happened |
| `EVENTTYPE` | What happened: `Sent`, `Open`, `Click`, `Bounce` or `Unsubscribe` (table above) |
| `EMAILPRODUCTTYPE` | The product the email was about. Used only to keep Kerendia emails. |

**Which lines are kept:**

* The email is about Kerendia: the product type contains the word "Kerendia" in any capitalisation (`UPPER(EMAILPRODUCTTYPE) LIKE '%KERENDIA%'`).
* The doctor ID starts with `BH` (a real Bayer ID).
* The event date is inside the lookback (between `LOOKBACK_START_DATE` and `LOOKBACK_END_DATE` of cohort `I01`).

**Size at the last run (4 May 2026):** 5,740,895 events for 191,020 doctors.

**Other input:** the NPI-to-BHID mapping is loaded at the start but **not used** (the data already uses BHID).

### 2.3 How the features are built, step by step

**Step 1. Get the lookback dates.**
*What:* read the dates table and take cohort `I01`.

**Step 2. Read the email events** with the filters above.

**Step 3. Attach the dates and build the doctor key.**
*What:* cross join with the dates (section 0.2), keep events inside the lookback, remove rows without a BHID, and create `HCP_COHORT_ID` (e.g. `BH10000342_I01`).

**Step 4. Count events per doctor, per day, per type.**
*What:* every event gets a helper value `FLAG = 1`. Then a pivot on `EVENTTYPE` adds up the flags for each doctor and day, giving one column per event type. The columns are renamed with `TOTAL_` in front: `TOTAL_SENT`, `TOTAL_OPEN`, `TOTAL_CLICK`, `TOTAL_BOUNCE`, `TOTAL_UNSUBSCRIBE`.
*Why:* adding up 1s is the same as counting events.
*Detail to know:* this is a **dynamic** pivot: the columns come from whatever event types exist in the data (see LH-1 below).

**Step 5. Fill in the calendar and add up the last 90 days.**
*What:* `step2_fill_missing_date` gives each doctor one row per day of the lookback, empty days become 0, and `step3_lag_date` with the single period **90 days** adds up each day and the 89 days before it.
*Why:* only the 3-month total is used by the model.

**Step 6. Keep the last day only and tidy up.**
*What:* keep only the row for `LOOKBACK_END_DATE`; remove the daily counts; rename the day column to `SVC_DT`; take the BHID out of `HCP_COHORT_ID` into its own column `BHID`.

**Step 7. Save.**
*What:* add `PULL_DT` (text) and overwrite the table `kerendia_nba_3_hcp_model_hq_email_features_for_inference`.

### 2.4 The features explained

There are **5 features**, all covering **the last 3 months (90 days)**:

| Feature | What it means | How to interpret it |
| --- | --- | --- |
| `TOTAL_SENT_IN_LAST_3_MONTH` | Number of Kerendia HQ emails sent to the doctor | How much we have been emailing this doctor. |
| `TOTAL_OPEN_IN_LAST_3_MONTH` | Number of times the doctor opened an email | Interest in our emails. Can be higher than "sent", because re-opening the same email counts again. |
| `TOTAL_CLICK_IN_LAST_3_MONTH` | Number of times the doctor clicked a link in an email | Strong interest: they wanted to read more. |
| `TOTAL_BOUNCE_IN_LAST_3_MONTH` | Number of emails that could not be delivered | The email address may be wrong; email may not reach this doctor. |
| `TOTAL_UNSUBSCRIBE_IN_LAST_3_MONTH` | Number of times the doctor unsubscribed | The doctor does not want our emails; email is probably not a good next action. |

**Example.** In the 90 days before the end of the lookback, Dr. Patel was sent 6 emails, opened 2 of them (one of them twice) and clicked once. Her features: sent = 6, open = 3, click = 1, bounce = 0, unsubscribe = 0.

### 2.5 What the final table looks like

One row per doctor (about 166,000 doctors at the last run):

| Column | Meaning |
| --- | --- |
| `HCP_COHORT_ID` | The doctor (Bayer ID + `_I01`) |
| `SVC_DT` | The end of the lookback (the "as of" date) |
| `LOOKBACK_END_DATE` | Same date, kept again |
| 5 features | Above |
| `BHID` | The doctor's Bayer ID |
| `PULL_DT` | Date the notebook was run |

Doctors with no HQ email activity in the year are not in the table.

### 2.6 Things to watch out for

* **Repeated opens and clicks count every time.** Opening the same email three times gives 3 opens, so "open" can be higher than "sent", and one very active reader can look like many readers.
* **Only a 3-month period exists.** An older version also built 1, 2, 4, 5 and 6 months, and old outputs saved in the notebook still show those columns, but the current code builds only 90 days.
* **The list of features depends on the data** (LH-1). Because the pivot is dynamic, a new event type (for example "Forward") would add a new feature automatically, and an event type that disappears would remove its feature. The model expects a fixed list of columns.
* **The same emails also appear in Digital.** Digital keeps HQ emails as a channel (`DIGITAL_HQ_EMAILS_...`) and as a vendor (`DIGITAL_HQ_EMAIL_...`), so the model sees this activity twice.

---

## 3. DTC Direct Buy + Social (`34_promotional_features_DTC`)

### 3.1 In short

"DTC" means **Direct-to-Consumer**: Kerendia ads shown to the **public (patients)**, not to doctors. Examples are ads on health websites such as WebMD, or on Facebook and Instagram.

These ads are not targeted at a particular doctor, so the data is not per doctor. It is per **region**: the US is divided into about 210 media regions (called "DMAs", Designated Market Areas; roughly one per large city and its surroundings). Each doctor gets the numbers of the region where they work.

The idea: if many patients around a doctor saw Kerendia ads, more of them may ask that doctor about Kerendia. It describes the doctor's **surroundings**. It is not an action that can be taken with the doctor.

### 3.2 Where the data comes from

Unlike the other channels, this notebook does **not** read Snowflake. It reads tables that were prepared and saved earlier by other notebooks (as Delta tables). If those tables are not refreshed, this notebook produces the same numbers again.

**The input tables:**

| Table (saved path) | What it contains | Used? |
| --- | --- | --- |
| `ops_pipeline/query_output/kerendia_nba_3_0_hcp_model_DirectBuys` | **Direct buys**: ads bought directly from health websites. Vendors: Health Union, Healthline, Sharecare, WebMD. | Yes |
| `ops_pipeline/query_output/kerendia_nba_3_0_hcp_model_social` | **Social media**: Facebook and Instagram together. Vendor: `FB+IG`. | Yes |
| `ops_pipeline/notebook_output/DTC/Pulsepoint` | PulsePoint programmatic display ads (ads placed automatically across many websites) | Loaded and prepared, but **never added** to the result (LT-1) |
| `ops_pipeline/notebook_output/DTC/TTD Display` | The Trade Desk display ads (another automatic ad-placement platform) | Loaded and prepared, but **never added** (LT-1) |

**One line of each input** = one region, one month, one vendor.

**Columns used:**

| Column | What it means |
| --- | --- |
| `DMA_Code` | The region (DMA number, e.g. `500`) |
| `MONTH` | The month (its first day, e.g. 2023-02-01) |
| `VENDOR` | The website or platform that showed the ad |
| `IMPRESSIONS` | How many times the ad was shown to people in that region that month |
| `CLICKS` | How many times people clicked the ad |

No lines are removed and there is no date filter: the data starts in January 2023 and goes up to whatever the input tables contain.

### 3.3 How the features are built, step by step

**Step 1. Load the input tables** (all four).

**Step 2. For each input separately: add up and pivot.**
*What:* group by region and month, turn each vendor into its own columns, and add up impressions (`TOTAL_IMPRESSIONS`) and clicks (`TOTAL_CLICKS`). Empty cells are filled with 0. `MONTH` is renamed `DATA_MONTH`.
*Why:* one row per region and month, with one number per vendor.

**Step 3. Clean the column names.**
*What:* every feature column gets the prefix `DTC_PROMOTION_`; symbols and spaces are replaced (`+` becomes "and", spaces and `-` become `_`, brackets and `&` are removed) and everything is in capital letters. So vendor "Health Union" becomes `DTC_PROMOTION_HEALTH_UNION_TOTAL_IMPRESSIONS`, and "FB+IG" becomes `DTC_PROMOTION_FB_AND_IG_TOTAL_IMPRESSIONS`.

**Step 4. Combine direct buys and social media.**
*What:* a **full outer join** on region + month: every region-month that appears in either table is kept.
*Detail to know:* the 0-filling happened in step 2, **before** this join. So when a region-month exists in only one table, the columns of the other table are empty (NULL), not 0 (LT-2).

**Step 5. Save.**
*What:* add `PULL_DT` (text) and overwrite `kerendia_nba_3_hcp_model_DTC_PROMOTION_for_inference`. All months are kept; there is no lookback period here. Last run: 31 July 2026.

**Step 6. Check.** The last cell checks that 9 feature names expected by the model exist in the table (all but `DTC_PROMOTION_HEALTHLINE_TOTAL_CLICKS`). All 9 were found.

### 3.4 The features explained

**10 features**, each for **one region in one month** (no "last N months" totals):

| Feature | What it means |
| --- | --- |
| `DTC_PROMOTION_HEALTH_UNION_TOTAL_IMPRESSIONS` | Times a Kerendia ad was shown to people in the region on Health Union websites that month |
| `DTC_PROMOTION_HEALTH_UNION_TOTAL_CLICKS` | Times people in the region clicked those ads |
| `DTC_PROMOTION_HEALTHLINE_TOTAL_IMPRESSIONS` | Ads shown on Healthline |
| `DTC_PROMOTION_HEALTHLINE_TOTAL_CLICKS` | Clicks on Healthline ads |
| `DTC_PROMOTION_SHARECARE_TOTAL_IMPRESSIONS` | Ads shown on Sharecare |
| `DTC_PROMOTION_SHARECARE_TOTAL_CLICKS` | Clicks on Sharecare ads |
| `DTC_PROMOTION_WEBMD_TOTAL_IMPRESSIONS` | Ads shown on WebMD |
| `DTC_PROMOTION_WEBMD_TOTAL_CLICKS` | Clicks on WebMD ads |
| `DTC_PROMOTION_FB_AND_IG_TOTAL_IMPRESSIONS` | Ads shown on Facebook and Instagram |
| `DTC_PROMOTION_FB_AND_IG_TOTAL_CLICKS` | Clicks on Facebook and Instagram ads |

Impressions = how much patients were **exposed** to Kerendia ads; clicks = how many **responded**. Direct-buy values are stored as decimal numbers (e.g. `6180.0`), social-media values as whole numbers (e.g. `25855`); the meaning is the same.

**Example.** Region 500, February 2023: WebMD showed the ad 6,180 times and got 5 clicks; Facebook/Instagram showed it 25,855 times and got 51 clicks. Every doctor working in region 500 gets these numbers for that month.

### 3.5 What the final table looks like

One row per region per month:

| Column | Meaning |
| --- | --- |
| `DMA_Code` | The region |
| `DATA_MONTH` | The month (its first day) |
| 10 features | Above |
| `PULL_DT` | Date the notebook was run |

Linking regions to doctors is not done in this notebook; it happens in a later step.

### 3.6 Things to watch out for

* **Empty values instead of 0** (LT-2). If a region-month has direct-buy ads but no social ads (or the opposite), the missing side is empty (NULL), not 0, because the 0-filling happens before the two tables are combined. Example: region 500, January 2023 has direct-buy numbers but empty Facebook/Instagram columns. A later step must decide whether empty means "no ads" (0) or "unknown".
* **Two prepared sources are never used** (LT-1). PulsePoint and The Trade Desk are loaded and prepared (steps 1 to 3) but not included in the join of step 4, so their ads are not in any feature.
* **The data is only as recent as the prepared tables.** The notebook does not fetch new data; if the input tables are not refreshed, the features stay the same.
* **Pivot columns depend on the data.** A new vendor in an input table would add new columns; a vendor that disappears would remove them.
* **These are not doctor actions.** They describe the doctor's area. They should be treated as background information, not as something the model can recommend.
* **Linking to doctors happens later.** Each doctor's region (DMA) must be looked up in a later step; that link is not part of this notebook.

---

## 4. Samples (`17_promotional_features_samples`)

### 4.1 In short

Doctors can receive **free Kerendia samples** to give to patients, so a patient can start treatment straight away. Samples reach the doctor in two ways:

* **Dropped**: a sales rep hands them over in person during a visit.
* **Shipped**: the doctor orders them and they are sent to the office.

This channel counts **how many sample units** each doctor received, of which product, and in which way. A doctor who receives (and especially who **asks for**) many samples is often starting new patients on Kerendia.

### 4.2 Where the data comes from

**Table:** `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER` in Snowflake, read with `Get_Data_Snowflakes`. It contains both dropped and shipped samples in one table.

**History of the source.** This table has been used since 19 December 2025. The notebook still contains, switched off (commented out), the older sources: `PHCDW.PHCDW_DSAA.VIEW_KERENDIA_SAMPLES_DROPPED_SHIPPED`; a version from 30 October 2025 that combined `ANALYTICS_V2.KERENDIA_SAMPLES` (dropped) with `ANALYTICS_V2.KERENDIA_SAMPLES_SHIPPED` (shipped, leaving out the Bayer product `KYLEENA BRC`, which is not Kerendia); and a test table (`..._TEST`).

**One line of the table** = one delivery of one product to one doctor.

**Columns used:**

| Column | What it means |
| --- | --- |
| `BHID` | The doctor's Bayer ID |
| `SMPLE_CALL_DT` | The date of the delivery. Used as the event day (the code also copies it into a column called `MONTH_ID`, even though it is a day, not a month). |
| `SMPLE_CALL_NM` | The identifier of the visit or order the delivery belongs to |
| `SMPLE_NM` | The product delivered (converted to capital letters). Values: see the table below. |
| `SMPLE_QTY` | How many units were delivered |
| `SAMPLE_FLAG` | `DROPPED` (handed over by a rep during a visit) or `SHIPPED` (ordered and sent to the office) |

**Which lines are kept:** all of them in the query (it uses `SELECT DISTINCT`, which keeps only one copy of identical lines). The lookback dates are applied later, in step 4.

**Size at the last run (27 May 2026):** 159,970 lines; the latest delivery date was 19 May 2026.

**Other inputs:** the HCP universe (`kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`) and the provider mapping table `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING`, used in step 8 to keep only target doctors.

Products in the data:

| Product name in the data | What it is |
| --- | --- |
| Kerendia 10mg BRC | 10 mg tablets (usual starting dose for kidney disease with diabetes) |
| Kerendia 20mg BRC | 20 mg tablets (usual ongoing dose) |
| Kerendia 40mg BRC | 40 mg tablets (newer dose, used for heart failure) |
| Kerendia Sampling Kit BRC | A sampling kit (supply, not medicine) |
| Kerendia Sample Housing Box BRC | A box for storing samples in the office (supply) |
| Kerendia Patient Brochures BRC | Leaflets for patients; **ignored** in all features |

("BRC" is just part of the product code in the sample system.)

### 4.3 How the features are built, step by step

**Step 1. Get the lookback dates** (cohort `I01`).

**Step 2. Read the deliveries** (query above).

**Step 3. Split the quantity into columns.**
*What:* the notebook creates one column per product, from a fixed (hard-coded) list of six names. Each column holds the quantity when the line is for that product, and 0 otherwise:

| Column | Product name it looks for |
| --- | --- |
| `SAMPLE_10MG` | `KERENDIA 10MG` (an old name, no longer in the data) |
| `SAMPLE_20MG` | `KERENDIA 20MG` (an old name, no longer in the data) |
| `SAMPLE_10MG_BRC` | `KERENDIA 10MG BRC` |
| `SAMPLE_20MG_BRC` | `KERENDIA 20MG BRC` |
| `SAMPLE_SAMPLING_KIT_BRC` | `KERENDIA SAMPLING KIT BRC` |
| `SAMPLE_SAMPLE_HOUSING_BOX_BRC` | `KERENDIA SAMPLE HOUSING BOX BRC` |

There is **no column for `KERENDIA 40MG BRC`** (LS-1). Then three more columns, all leaving out patient brochures:

* `OVERALL_SAMPLE`: the quantity of every line (all products, **including** 40 mg, kits and boxes).
* `SAMPLE_DROPPED`: the quantity when the line is `DROPPED`.
* `SAMPLE_SHIPPED`: the quantity when the line is `SHIPPED`.

**Step 4. Attach the dates and build the doctor key.**
*What:* cross join with the dates, keep deliveries inside the lookback, remove rows without a BHID, create `HCP_COHORT_ID`.

**Step 5. Add up per doctor and day.**
*What:* add up each of the 9 columns for each doctor and day. The totals get `TOTAL_` in front (e.g. `TOTAL_SAMPLE_SHIPPED`).

**Step 6. Fill in the calendar and add up the periods.**
*What:* `step2_fill_missing_date`, empty days become 0, then `step3_lag_date` for 30, 60, 90, 120, 150 and 180 days.

**Step 7. Keep the last day only and tidy up.**
*What:* keep the row for `LOOKBACK_END_DATE`, remove the daily totals, rename the day column `SVC_DT`, put the BHID in its own column `BHID`.

**Step 8. Keep only target doctors.**
*What:* read the HCP universe (its doctor column is `PROVIDER_ID`), translate it to BHID with `SOURCE_PROVIDER_BHID_NPI_MAPPING`, attach the cohort and build `HCP_COHORT_ID`. Then an **inner join** with the features (LS-4): only doctors that are both in the universe **and** received samples remain. A check then counts empty values per column.
*Why:* the model only scores doctors in the universe.

**Step 9. Save.**
*What:* add `PULL_DT` (text) and overwrite `kerendia_nba_3_hcp_model_samples_features_for_inference`.

### 4.4 The features explained

All values are **numbers of units** (for example, packs), not numbers of deliveries. There are 9 measures, each for 6 periods (`_IN_LAST_1_MONTH` to `_IN_LAST_6_MONTH`) = **54 features**.

| Feature (+ period ending) | What it counts | How to interpret it |
| --- | --- | --- |
| `TOTAL_OVERALL_SAMPLE` | All sample units and supplies received (brochures excluded; includes 40 mg) | Overall sampling activity with this doctor |
| `TOTAL_SAMPLE_10MG_BRC` | 10 mg units | Samples for starting patients |
| `TOTAL_SAMPLE_20MG_BRC` | 20 mg units | Samples for patients continuing treatment |
| `TOTAL_SAMPLE_SAMPLING_KIT_BRC` | Sampling kits | Supplies to run sampling in the office |
| `TOTAL_SAMPLE_SAMPLE_HOUSING_BOX_BRC` | Storage boxes | Office set up to keep samples |
| `TOTAL_SAMPLE_DROPPED` | Units handed over by reps | Sampling driven by rep visits |
| `TOTAL_SAMPLE_SHIPPED` | Units the doctor ordered and had shipped | The doctor actively asked for samples: a strong interest signal |
| `TOTAL_SAMPLE_10MG` | Units with the old name "Kerendia 10mg" (without BRC) | This name no longer appears in the data, so always 0 |
| `TOTAL_SAMPLE_20MG` | Units with the old name "Kerendia 20mg" (without BRC) | Always 0, same reason |

Useful rule: **dropped + shipped = overall.**

**Example.** In the last 90 days, a rep gave Dr. Garcia 10 units of 20 mg, and she ordered 6 units of 10 mg by mail. Her features for `_IN_LAST_3_MONTH`: overall = 16, 20 mg = 10, 10 mg = 6, dropped = 10, shipped = 6.

### 4.5 What the final table looks like

One row per doctor:

| Column | Meaning |
| --- | --- |
| `HCP_COHORT_ID` | The doctor (Bayer ID + `_I01`) |
| `SVC_DT` | The end of the lookback (the "as of" date) |
| `LOOKBACK_END_DATE` | Same date, kept again |
| 54 features | Above |
| `BHID` | The doctor's Bayer ID |
| `PULL_DT` | Date the notebook was run |

### 4.6 Things to watch out for

* **No separate 40 mg feature** (LS-1). The fixed product list in step 3 has no 40 mg column, so 40 mg samples are only counted inside overall, dropped and shipped. With heart failure now a Kerendia use, this hides a potentially important signal.
* **Two features are always 0.** `TOTAL_SAMPLE_10MG` and `TOTAL_SAMPLE_20MG` look for old product names without "BRC", which no longer appear in the data.
* **Fixed product list.** Any new product name (for example a new kit) is counted only in overall / dropped / shipped, never in its own column.
* **Only doctors in the target list are kept** (LS-4). The inner join removes doctors outside the HCP universe, even if they received samples; and doctors in the universe without samples are not added (they are treated as 0 later).
* **Identical lines are merged.** `SELECT DISTINCT` keeps one copy of identical lines, so two genuinely separate deliveries with exactly the same doctor, date, visit, product, quantity and type would count once.

---

## 5. Speaker Programs (`14_promotional_features_speaker_program`)

### 5.1 In short

A **speaker program** is an educational event about Kerendia where a doctor (the "speaker") presents approved slides to other doctors. It can be in person, online, or both. This channel counts **how many of these events each doctor attended**, and of which kind: in person or online, and on which topic.

A doctor who keeps attending Kerendia talks is clearly interested in learning about the medicine.

### 5.2 Where the data comes from

**Table:** `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM` in Snowflake ("personal promotion events"), read with `Get_Data_Snowflakes`.

**One line of the table** = one doctor registered for one event.

**Columns used:**

| Column | What it means | Values seen |
| --- | --- | --- |
| `EVNT_ID` | The event's ID | Used only to remove duplicates |
| `CUST_HCP_ID` | The doctor's Bayer ID. Renamed `BHID`. | `BH...` |
| `ATND` | Whether the doctor attended | `Attended` (others are removed) |
| `EVNT_START_DATE` | The day of the event | |
| `EVNT_FMT` | How the event was held (format) | `Face-to-Face` (in person), `In-Office Meal` (a talk over a meal at the doctor's office), `Remote` (online), `Hybrid` (both) |
| `EVNT_TYP` | The kind of event | The data shows `Speaker Program` |
| `EVNT_TPIC_NM` | The name of the slide presentation, ending with its approval code (e.g. `PP-KER-US-0225-1`; every promotional material has such a code) | See the full list in step 3 |
| `PROD_BRAND_NM` | The brand of the event. Used only to keep Kerendia. | `KERENDIA` |

**Which lines are kept:**

* Brand is Kerendia.
* The doctor ID contains `BH` and is not empty.
* The doctor **attended** (`UPPER(ATND) = 'ATTENDED'`). Registrations without attendance are removed.
* The event date is inside the lookback.

**Size at the last run (4 May 2026):** 10,766 attendances.

**Other input:** the NPI-to-BHID mapping is loaded, but the step that would use it is switched off (commented out).

### 5.3 How the features are built, step by step

**Step 1. Get the lookback dates** (cohort `I01`).

**Step 2. Read the attendances** with the filters above (`SELECT DISTINCT`).

**Step 3. Remove duplicates and label each attendance.**
*What:* identical lines are removed (`dropDuplicates()`, comparing all columns including the event ID), then the event ID is dropped. Each remaining line is one doctor at one event. Each line then gets a set of 1/0 labels ("flags": 1 = yes, 0 = no):

| Label | Is 1 when |
| --- | --- |
| `ATTENDED_FLAG` | The doctor attended (always 1, since only attendances are kept) |
| `SPKR_EVNT_FMT_F2F` | Format is `Face-to-Face` |
| `SPKR_EVNT_FMT_IN_OFFC_MEAL` | Format is `In-Office Meal` (created, but never added up: LSP-4) |
| `SPKR_EVNT_FMT_REMOTE` | Format is `Remote` |
| `SPKR_EVNT_FMT_HYBRID` | Format is `Hybrid` |
| `SPKR_EVNT_FMT_OTHER` | The **topic** (`EVNT_TPIC_NM`) is empty. Despite its name, it does not look at the format (LSP-2). |
| `SPKR_EVNT_TYP_SPKR_PRGM` | Type is exactly `SPEAKER PROGRAMS` (the data says `Speaker Program`, so this is probably never 1: LSP-1) |
| `SPKR_EVNT_TYP_NON_SPKR_PRGM` | Type is exactly `NON-SPEAKER PROGRAMS` (same problem) |
| `SPKR_TOPIC_CKD`, `_CVR`, `_INTRO`, `_OTHER` | The presentation is in that topic list (below) |

**The full topic lists.** The notebook compares the presentation name **exactly** with these fixed lists:

| Topic group | Meaning | Presentations in the list |
| --- | --- | --- |
| CKD | Kidney disease in type 2 diabetes | "Recognizing The Gap Diagnosis and Treatment of CKD Associated with T2D PP-KER-US-02241"; "Discover More About Kidney and Heart Outcomes with a Treatment for CKD Associated with T2D PP-KER-US-0225-1" (with and without a `***` prefix) |
| CVR | Heart and kidneys together (cardiorenal) | "KERENDIA Cardiorenal Connection PP-KER-US-1038-1"; "KERENDIA Heart of the Matter PP-KER-US-0743-1" |
| INTRO | Introductions, overviews and case-based learning | "Introduction to KERENDIA" (PP-FINE-US-0626-3 and -4); "SHORT Introduction to KERENDIA CONDENSED" (PP-FINE-US-0620-1 and -2); "KERENDIA Recognizing The Gap PP-KER-US-1039-2"; "KERENDIA Exploring a Fundamental Pillar PP-KER-US-1455-1"; "KERENDIA CONDENSED PP-KER-US-1340-1"; "Kerendia Case Based Learning Program" (PP-KER-US-0044-1 with and without `***`, and PP-KER-US-1040-1) |
| OTHER | Exhibition stand, or no topic recorded | `Display/Exhibit`, or empty topic |

A presentation that is not on any list (for example "Underscoring Early Patient ID ... PP-KER-US-2149-1", which appears in the data) gets 0 in every topic group, but is still counted in the overall total.

**Step 4. Attach the dates and build the doctor key** (cross join, keep the lookback, remove empty BHIDs, create `HCP_COHORT_ID`).

**Step 5. Add up per doctor and day.**
*What:* the labels are added up for each doctor and day, giving the 11 measures of section 5.4. `ATTENDED_FLAG` becomes `TOTAL_SPEAKER_PROGRAMS_ATTENDED`; the others get `TOTAL_` in front, except `SPKR_TOPIC_OTHER`, which keeps its name (LSP-3). The in-office-meal label is not added up (that line is commented out, LSP-4).

**Step 6. Fill in the calendar and add up the periods** (30, 60, 90, 120, 150, 180 days).

**Step 7. Keep the last day only and tidy up.**
*What:* keep the row for `LOOKBACK_END_DATE`, remove the daily totals, rename the day column `SVC_DT`, put the BHID in its own column, and remove the cohort and lookback-end columns.

**Step 8. Save.**
*What:* add `PULL_DT` (text) and overwrite `kerendia_nba_3_hcp_model_speaker_program_for_inference`.

**Check cells** (they do not change the data): a check for duplicate lines and a monthly count of attending doctors.

### 5.4 The features explained

All values are **numbers of events attended**. There are 11 measures, each for 6 periods (`_IN_LAST_1_MONTH` to `_IN_LAST_6_MONTH`) = **66 features**.

| Feature (+ period ending) | What it counts | How to interpret it |
| --- | --- | --- |
| `TOTAL_SPEAKER_PROGRAMS_ATTENDED` | All Kerendia events attended | Overall interest in Kerendia education (the main feature) |
| `TOTAL_SPKR_EVNT_FMT_F2F` | Events attended in person ("face-to-face") | Likes in-person events |
| `TOTAL_SPKR_EVNT_FMT_REMOTE` | Events attended online | Likes online events |
| `TOTAL_SPKR_EVNT_FMT_HYBRID` | Events that were both in person and online | Mixed format |
| `TOTAL_SPKR_EVNT_FMT_OTHER` | Events **with no topic recorded** (despite the name, it does not look at the format) | Data-quality indicator rather than a format |
| `TOTAL_SPKR_EVNT_TYP_SPKR_PRGM` | Events of type "Speaker Programs" | Probably always 0 (see below) |
| `TOTAL_SPKR_EVNT_TYP_NON_SPKR_PRGM` | Events of type "Non-Speaker Programs" | Probably always 0 (see below) |
| `TOTAL_SPKR_TOPIC_CKD` | Events on kidney disease in diabetes | Interest in the kidney message |
| `TOTAL_SPKR_TOPIC_CVR` | Events on the heart-kidney link | Interest in the heart message (often cardiologists) |
| `TOTAL_SPKR_TOPIC_INTRO` | Introduction / case-based events | Early-stage learning about Kerendia |
| `SPKR_TOPIC_OTHER` | Exhibition stands or no topic | Note: this one has no `TOTAL_` at the start, so its names are `SPKR_TOPIC_OTHER_IN_LAST_...` |

**Example.** In the last 3 months, Dr. Kim attended one in-person CKD talk and one online introduction. Her `_IN_LAST_3_MONTH` features: attended = 2, F2F = 1, remote = 1, CKD = 1, INTRO = 1, all others 0.

The format features do not always add up to the total: in-office meal events are not counted in any format feature, and "format other" checks the topic instead of the format. The topic features do not always add up either, because some presentations are on no list.

### 5.5 What the final table looks like

One row per doctor who attended at least one event:

| Column | Meaning |
| --- | --- |
| `HCP_COHORT_ID` | The doctor (Bayer ID + `_I01`) |
| `SVC_DT` | The end of the lookback (the "as of" date) |
| 66 features | Above |
| `BHID` | The doctor's Bayer ID |
| `PULL_DT` | Date the notebook was run |

### 5.6 Things to watch out for

* **The two "type" features are probably always 0** (LSP-1). The code looks for the exact text "SPEAKER PROGRAMS" (plural, capital letters), but the data says "Speaker Program" (singular, mixed case), so the texts never match.
* **The "format other" feature actually checks for a missing topic** (LSP-2). It is 1 when the presentation name is empty, whatever the format was.
* **In-office meal events are labelled but not counted** (LSP-4). The label is created in step 3, but the line that adds it up is switched off, so there is no in-office meal feature.
* **Topic lists are fixed by hand.** The names must match exactly, including the approval code. New or renamed presentations fall outside every topic group.
* **One feature name breaks the pattern** (LSP-3). `SPKR_TOPIC_OTHER_IN_LAST_...` has no `TOTAL_` at the start, unlike all the others.

---

## 6. Free Trial Program / FTP (`19_ftp_features`)

### 6.1 In short

The **Free Trial Program (FTP)** gives patients their first supply of Kerendia **for free**, using a voucher. Each time a patient uses a voucher at the pharmacy, a "claim" is recorded, together with the doctor who wrote the prescription.

This channel counts **how many free-trial vouchers were used on each doctor's prescriptions**. Many vouchers usually means the doctor is starting new patients on Kerendia.

### 6.2 Where the data comes from

**Table:** `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP` in Snowflake, read with `Get_Data_Snowflakes`.

**One line of the table** = one claim transaction: an approval, or a cancellation ("reversal") of an earlier claim.

**Columns used:**

| Column | What it means |
| --- | --- |
| `PRSC_NPI` | The NPI of the prescribing doctor. Renamed `NPI_NUMBER`. |
| `RX_DT` | The prescription date. Converted to a date and used as the event day (saved as `SVC_DT_M`, later renamed `MONTH_ID`, even though it is a day, not a month). |
| `CLM_AUTH_NUM` | The authorisation number of this one claim transaction. |
| `ORGN_CLM_AUTH_NUM` | The number of the **original** claim. A claim and every later cancellation or re-approval of it share this number. |
| `DAY_SUPPLY` | How many days of medicine the claim covers. A cancellation has a negative value. Used only to find cancelled claims (step 2). |
| `USE_SLS` | Whether the line may be used for sales reporting (`Y` = yes). |

**Which lines are kept:**

* The prescriber NPI is not empty.
* `USE_SLS = 'Y'`.
* There is no date filter in the query; the lookback is applied in step 4.

**Dates at the last run (8 October 2025):** claims from 13 January 2021 to 29 September 2025.

**How a cancellation looks.** Sometimes a claim is cancelled (for example because the patient never collected the medicine). The cancellation is an extra line with negative quantities and the same `ORGN_CLM_AUTH_NUM`:

| Line | `ORGN_CLM_AUTH_NUM` | `DAY_SUPPLY` |
| --- | --- | --- |
| Approval | 111 | 30 |
| Cancellation | 111 | -30 |
| **Total for 111** | | **0**: the patient did not get the medicine |

If the claim was then approved again, a third line (+30) makes the total 30 again.

### 6.3 How the features are built, step by step

**Step 1. Get the lookback dates** (cohort `I01`).

**Step 2. Read the claims and remove cancelled ones.**
*What:* a second query adds up `DAY_SUPPLY` per original claim number. Claim numbers whose total is **0** (approved and then fully cancelled) are collected into a list, and all their lines are removed from the claims. Claim numbers with a positive total are kept **with all their lines** (approval, cancellation and re-approval).
*Why:* a fully cancelled claim means the patient did not start therapy.
*Detail to know:* the list of cancelled claims is first copied from Spark into the memory of the main computer (`toPandas()`) and then used as a filter (`isin`). This works for small lists but may become slow or fail as the list grows (LF-4).

**Step 3. Translate NPI to BHID.**
*What:* an **inner join** with the NPI-to-BHID mapping (`kerendia_nba_3_0_npi_bhid_mapping`). Claims whose NPI has no BHID are removed. If one NPI has several BHIDs, the claim is copied once for each (LF-5).
*Size after this step:* 96,231 lines for 13,388 doctors. Some doctor IDs are not in the usual `BH...` form (for example `31403984`).

**Step 4. Attach the dates and build the doctor key** (cross join, keep claims inside the lookback, remove empty BHIDs, create `HCP_COHORT_ID`).

**Step 5. Count claims per doctor and day.**
*What:* the number of lines for each doctor and day becomes `TOTAL_RX_FTP` ("total prescriptions with free trial").

**Step 6. Fill in the calendar and add up the periods** (30, 60, 90, 120, 150, 180 days), then keep the row for `LOOKBACK_END_DATE`.

**Step 7. Tidy up.**
*What:* a list of columns to keep (`keep_cols`) is applied. It contains `LOOKBACK_END_MONTH`, a misspelling of `LOOKBACK_END_DATE` (LF-2), so the lookback end column is removed together with the daily count. Unlike the other daily notebooks, the day column is **not** renamed to `SVC_DT` (it stays `MONTH_ID`) and the BHID is **not** put in its own column.

**Step 8. Save.**
*What:* add `PULL_DT` as a real date (`current_date()`, not text) and overwrite `kerendia_nba_3_hcp_model_ftp_features_v2_for_inference`. The save cell appears twice in the notebook; running both gives the same result.

### 6.4 The features explained

One measure for 6 periods = **6 features**:

| Feature | What it means |
| --- | --- |
| `TOTAL_RX_FTP_IN_LAST_1_MONTH` | Number of free-trial voucher claims on this doctor's prescriptions in the last 30 days |
| `TOTAL_RX_FTP_IN_LAST_2_MONTH` | Same, last 60 days |
| `TOTAL_RX_FTP_IN_LAST_3_MONTH` | Same, last 90 days |
| `TOTAL_RX_FTP_IN_LAST_4_MONTH` | Same, last 120 days |
| `TOTAL_RX_FTP_IN_LAST_5_MONTH` | Same, last 150 days |
| `TOTAL_RX_FTP_IN_LAST_6_MONTH` | Same, last 180 days |

How to interpret it: roughly, **how many patients this doctor started on Kerendia with a free trial** recently. It counts claim **lines**, not patients: a claim that was cancelled and approved again keeps all three lines (step 2), so it counts 3.

**Example.** Three of Dr. Novak's patients used a free-trial voucher in the last 2 months, and one more about 135 days ago. If one of the three was in the last 30 days, her features are: last 1 month = 1, last 2 months = 3, last 3 and 4 months = 3, last 5 and 6 months = 4.

### 6.5 What the final table looks like

One row per doctor with at least one voucher claim in the lookback:

| Column | Meaning |
| --- | --- |
| `HCP_COHORT_ID` | The doctor (Bayer ID + `_I01`) |
| `MONTH_ID` | The end of the lookback (other channels call this `SVC_DT`) |
| 6 features | Above |
| `PULL_DT` | Date the notebook was run (stored as a date, not as text like the others) |

Unlike the other doctor tables, there is no separate `BHID` column.

### 6.6 Things to watch out for

* **A claim that was cancelled and then approved again counts more than once**, because all its lines are kept (step 2).
* **One prescriber number can match several Bayer IDs** (LF-5), so the same claim can be counted for more than one doctor.
* **Some doctor IDs do not look like normal Bayer IDs** (e.g. `31403984` instead of `BH...`). They come from the mapping table and may not match other channels.
* **The saved table is old.** It was last built on 8 October 2025 (lookback ending 17 September 2025), much earlier than the other channels, so its features describe an older period.
* **Misspelled column name** (LF-2). `LOOKBACK_END_MONTH` in the keep list should be `LOOKBACK_END_DATE`; as a result the lookback end date is missing from the table.
* **Cancelled-claim list is loaded into memory** (LF-4). This may become slow or fail when the list grows.
* **Different column names from the other doctor tables.** The date is `MONTH_ID` (not `SVC_DT`), there is no `BHID` column, and `PULL_DT` is a date (not text). A later step must handle these differences.

---

## 7. Summary

| Channel | What it tells the model | One row is | What is counted | Periods | Number of features |
| --- | --- | --- | --- | --- | --- |
| Digital | Did the doctor see and click our online content? | A doctor in a month | Times shown / interactions | This month, 3 months, 6 months, since the start | About 684 (changes with the data) |
| HQ Emails | Does the doctor read our emails? | A doctor | Email events | 3 months | 5 |
| DTC | How much did patients in the doctor's area see our ads? | A region in a month | Ad views / clicks | That month only | 10 |
| Samples | How many free samples did the doctor get, and did they ask for them? | A doctor | Units | 1 to 6 months | 54 |
| Speaker Programs | Does the doctor attend our educational talks? | A doctor | Events attended | 1 to 6 months | 66 |
| FTP | Is the doctor starting patients with free-trial vouchers? | A doctor | Voucher claims | 1 to 6 months | 6 |

**Saved tables** (all under `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/`):

| Channel | Table |
| --- | --- |
| Digital | `kerendia_nba_3_0_hcp_model_paid_search_features_for_inference` |
| HQ Emails | `kerendia_nba_3_hcp_model_hq_email_features_for_inference` |
| DTC | `kerendia_nba_3_hcp_model_DTC_PROMOTION_for_inference` |
| Samples | `kerendia_nba_3_hcp_model_samples_features_for_inference` |
| Speaker Programs | `kerendia_nba_3_hcp_model_speaker_program_for_inference` |
| FTP | `kerendia_nba_3_hcp_model_ftp_features_v2_for_inference` |


