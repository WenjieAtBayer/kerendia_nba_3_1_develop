# HQ Email Features — NBA 3.0 (Legacy)

**Group:** Non-personal promotional features (promotion that does not involve a sales rep)  
**Notebook:** `15_promotional_features_HQ_Emails` in `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Saved table:** `kerendia_nba_3_hcp_model_hq_email_features_for_inference`  
**Built from:** a review of the notebook code  
**Date:** October 22, 2026

## What is this document about?

Bayer uses a model called **Next Best Action (NBA)** to suggest, for each doctor, which Kerendia promotional action is most useful next. Kerendia is a Bayer medicine for chronic kidney disease in people with type 2 diabetes (and, more recently, heart failure). The model needs each doctor's recent history, turned into numbers called **features** (one fact about a doctor written as a number).

This document explains the **HQ Email** features: emails sent by Bayer's head office and what the doctor did with them. It describes the **old version** of the pipeline (NBA 3.0); a "pipeline" is the chain of notebooks that runs one after another to prepare the data for the model.

**How it is organised:** the key ideas shared by the channels of this folder (time frame, dates table, doctor key, helper notebooks, how "last 3 months" is calculated) are in `00_introduction.md`. This file has: 1. In short, 2. Where the data comes from, 3. How the features are built step by step (*what*, *why*, *detail to know*), 4. The features explained, 5. What the final table looks like, 6. Things to watch out for. Codes such as LH-1 refer to the companion legacy file; each problem is also explained here.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code. Its meaning is always given next to it.

**About the numbers.** Figures come from the last time the notebook was run (4 May 2026). They will be different at the next run.

---

## 1. In short

Bayer's head office ("HQ") sends Kerendia marketing emails to doctors. These are different from emails a rep sends personally (iRep emails, in the personal features). This channel counts, for each doctor, how many HQ emails were **sent** in the last 3 months and what the doctor **did** with them: opened, clicked, unsubscribed, or whether the email failed to arrive ("bounced").

It helps the model answer: *"Does this doctor read our emails? Is email a good way to reach them?"*

## 2. Where the data comes from

An email log with one line for every email "event". An event is one thing that happened to one email:

| Event | What it means |
| --- | --- |
| Sent | Bayer sent an email to the doctor. |
| Open | The doctor opened an email. If they open the same email 3 times, that is 3 events. |
| Click | The doctor clicked a link inside an email. Each click is a separate event. |
| Bounce | The email could not be delivered (for example, the address no longer exists). |
| Unsubscribe | The doctor asked to stop receiving Kerendia emails. |

**Table:** `PHCDW.PHCDW_CDM.HCP_EMAIL_LIST` in Snowflake, read with `Get_Data_Snowflakes` (see the introduction file).

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

## 3. How the features are built, step by step

**Step 1. Get the lookback dates.**
*What:* read the dates table and take cohort `I01`.

**Step 2. Read the email events** with the filters above.

**Step 3. Attach the dates and build the doctor key.**
*What:* cross join with the dates (see the introduction file), keep events inside the lookback, remove rows without a BHID, and create `HCP_COHORT_ID` (e.g. `BH10000342_I01`).

**Step 4. Count events per doctor, per day, per type.**
*What:* every event gets a helper value `FLAG = 1`. Then a **pivot** on `EVENTTYPE` (turning each event type into its own column) adds up the flags for each doctor and day. The columns are renamed with `TOTAL_` in front: `TOTAL_SENT`, `TOTAL_OPEN`, `TOTAL_CLICK`, `TOTAL_BOUNCE`, `TOTAL_UNSUBSCRIBE`.
*Why:* adding up 1s is the same as counting events.
*Detail to know:* this is a **dynamic** pivot: the columns come from whatever event types exist in the data (see LH-1 in section 6).

**Step 5. Fill in the calendar and add up the last 90 days.**
*What:* `step2_fill_missing_date` gives each doctor one row per day of the lookback, empty days become 0, and `step3_lag_date` with the single period **90 days** adds up each day and the 89 days before it (see the introduction file, section 0.3).
*Why:* only the 3-month total is used by the model.

**Step 6. Keep the last day only and tidy up.**
*What:* keep only the row for `LOOKBACK_END_DATE`; remove the daily counts; rename the day column to `SVC_DT`; take the BHID out of `HCP_COHORT_ID` into its own column `BHID`.

**Step 7. Save.**
*What:* add `PULL_DT` (text) and overwrite the table `kerendia_nba_3_hcp_model_hq_email_features_for_inference`.

## 4. The features explained

There are **5 features**, all covering **the last 3 months (90 days)**:

| Feature | What it means | How to interpret it |
| --- | --- | --- |
| `TOTAL_SENT_IN_LAST_3_MONTH` | Number of Kerendia HQ emails sent to the doctor | How much we have been emailing this doctor. |
| `TOTAL_OPEN_IN_LAST_3_MONTH` | Number of times the doctor opened an email | Interest in our emails. Can be higher than "sent", because re-opening the same email counts again. |
| `TOTAL_CLICK_IN_LAST_3_MONTH` | Number of times the doctor clicked a link in an email | Strong interest: they wanted to read more. |
| `TOTAL_BOUNCE_IN_LAST_3_MONTH` | Number of emails that could not be delivered | The email address may be wrong; email may not reach this doctor. |
| `TOTAL_UNSUBSCRIBE_IN_LAST_3_MONTH` | Number of times the doctor unsubscribed | The doctor does not want our emails; email is probably not a good next action. |

**Example.** In the 90 days before the end of the lookback, Dr. Patel was sent 6 emails, opened 2 of them (one of them twice) and clicked once. Her features: sent = 6, open = 3, click = 1, bounce = 0, unsubscribe = 0.

## 5. What the final table looks like

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

## 6. Things to watch out for

* **Repeated opens and clicks count every time.** Opening the same email three times gives 3 opens, so "open" can be higher than "sent", and one very active reader can look like many readers.
* **Only a 3-month period exists.** An older version also built 1, 2, 4, 5 and 6 months, and old outputs saved in the notebook still show those columns, but the current code builds only 90 days.
* **The list of features depends on the data** (LH-1). Because the pivot is dynamic, a new event type (for example "Forward") would add a new feature automatically, and an event type that disappears would remove its feature. The model expects a fixed list of columns.
* **The same emails also appear in Digital.** Digital keeps HQ emails as a channel (`DIGITAL_HQ_EMAILS_...`) and as a vendor (`DIGITAL_HQ_EMAIL_...`), so the model sees this activity twice.
