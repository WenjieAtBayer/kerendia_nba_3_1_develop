# iRep Email Features — NBA 3.0 (Legacy)

**Group:** Personal promotional features (promotion that involves a sales rep)  
**Notebook:** `16_promotional_features_irep` in `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Saved table:** `kerendia_nba_3_hcp_model_irep_features_for_inference`  
**Built from:** a review of the notebook code, plus a check of the saved table  
**Date:** October 22, 2026

## What is this document about?

Bayer uses a model called **Next Best Action (NBA)** to suggest, for each doctor, which Kerendia promotional action is most useful next. Kerendia is a Bayer medicine for chronic kidney disease in people with type 2 diabetes (and, more recently, heart failure). The model needs each doctor's recent history, turned into numbers called **features** (one fact about a doctor written as a number).

This document explains the **iRep Email** features: emails a Bayer sales representative ("rep") sent to each doctor, and what the doctor did with them. It describes the **old version** of the pipeline (NBA 3.0); a "pipeline" is the chain of notebooks that runs one after another to prepare the data for the model.

**How it is organised:** the key ideas shared by the channels of this folder (time frame, dates table, doctor key, helper notebooks, how "last N months" is calculated) are in `00_README_folder_guide.md`. This file has: 1. In short, 2. Where the data comes from, 3. How the features are built step by step, 4. The features explained, 5. What the final table looks like, 6. Things to watch out for.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code. Its meaning is always given next to it.

**About the numbers.** Figures from **inside the notebook** come from the last hand run (4 May 2026). Figures about the **saved table** come from a check of the table as it is now (last saved 24 September 2026). Both will change at the next run.

---

## 1. In short

An **iRep email** is an email that a rep sends to a doctor from **Veeva CRM** (the software reps use to plan and log their work), using a template approved by Bayer's review team (an "approved document"). It is different from HQ emails, which are sent centrally by Bayer's head office (non-personal features).

This channel counts, for each doctor, how many Kerendia iRep emails were delivered, opened and clicked in the **last 3 months**, and which templates were used.

It helps the model answer: *"Is this doctor reading the emails their rep sends?"*

## 2. Where the data comes from

**Tables** (in Snowflake):

| Table | What one line is | Role |
| --- | --- | --- |
| `CPH_DB_PROD.MODEL_V2.FACT_SENT_EMAIL` | One email sent by a rep to one customer | The emails |
| `CPH_DB_PROD.MODEL_V2.DIM_APPROVED_DOCUMENT` | One approved template (`APV_DOC_ID`, name `NM`) | Gives the template name; linked through `APV_EMAIL_TEMPLATE` |
| `PHCDW.PHCDW_STG.MDM_STG_HCP_XREF` | One link between a CRM customer ID (`SOURCE_ID`) and a Bayer ID (`BH_ID`) | Translates the customer into the BHID. Only links from the two Veeva sources `K2_AC2` and `VAULT_CRM_AC2` are used. |
| `PHCDW.PHCDW_STG.MDM_STG_HCP_PRFL` | One doctor profile | Joined, but none of its columns is used |

**Columns used:**

| Column | What it means | Renamed to |
| --- | --- | --- |
| `BH_ID` | The doctor's Bayer ID | `ACCT_IDNTFR`, then `BHID` |
| `EMAIL_SNT_DATE` | Day the email was sent | `EMAIL_SENT_DT`, then `MONTH_ID` (a day) |
| `CLICKED` | 1 if the doctor clicked at least one link in the email | `EMAIL_CLCKD_FLG` |
| `OPENED` | 1 if the doctor opened the email at least once | `EMAIL_OPND_FLG` |
| `STAT` | Delivery status of the email | `EMAIL_STATUS` |
| `NM` (approved document) | Template name, e.g. `Kerendia Meeting Invite Email` | `APPRVD_DOC_NM` |

**Which lines are kept** (`SELECT DISTINCT`, so identical lines are kept once):

* A sent date exists.
* The template name contains "Kerendia" (any capitalisation).
* The status starts with "Delivered" (any capitalisation).
* The doctor ID does not start with `BHO` (and is not empty).
* The **month** of the sent date is not after the end of the lookback. There is no start date here; older emails are removed in step 4.

**History of the source.** This query was received from the data team on 29 October 2025. The older source (`PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA...`) is still in the notebook, switched off ("commented out").

**Size at the hand run of 4 May 2026:** 581,135 emails for 101,022 doctors (before the lookback filter).

## 3. How the features are built, step by step

**Step 1. Get the lookback dates** (cohort `I01`).

**Step 2. Read the emails** with the filters above.

**Step 3. Give each email a set of yes/no labels:**

| Label | Is 1 when |
| --- | --- |
| `IREP_EMAIL_DELIVERED_FLAG` | Status is **exactly** `Delivered` |
| `IREP_EMAIL_CLICKED_FLAG` | Clicked = 1 |
| `IREP_EMAIL_OPENED_FLAG` | Opened = 1 |
| `IREP_APPRVD_DOC_NM_<group>` | The template name is in that group's list (table below) |

The template groups (names must match **exactly**):

| Group | What it is about | Template names in the list |
| --- | --- | --- |
| `FDA` | Announcement of the FDA approval (US medicines agency) | `Kerendia FDA-Approved Announcement`; `Kerendia FDA-Approved iRep Email Announcement` |
| `PSP_PRESCRIBING` | Patient support program, prescribing information | `Kerendia Patient Support Program iRep Email`; `Kerendia Prescribing Information Email` |
| `BRANDED_ASSET` | Sharing branded material | `Kerendia Branded Asset Share Email` |
| `NATIONAL_BROADCAST` | National broadcast (online event) | `Kerendia National Broadcast Email` |
| `KIDNEY` | Kidney disease screening and profile | `Kerendia CKD Screening iRep Email`; `Kerendia Kidney Profile iRep Email` |
| `INVITE` | Meeting invitations | `Kerendia Meeting Invite Email`; `Kerendia Remote Meeting Engage or Zoom Invitation` |
| `EDUCATION` | Educational events | `Kerendia NACE Educational Event iRep Email`; `Kerendia Virtual Educational Event iRep Email` |
| `BACC_ACCESS` | Insurance coverage and access (commercial insurance, Medicare) | `BACC - Kerendia - Commercial Access_12.21`; `BACC - Kerendia - Medicare Access`; `BACC - Kerendia - Medicare Access_12.21`; `Kerendia - Commercial Access`; `Kerendia - Commercial Access Update` |
| `EXCLUSIVE_BROADCAST` | Broadcast for nephrologists (kidney specialists) | `Kerendia Neph Exclusive Broadcast Email 1` |
| `TRIAL` | Free trial program | `Kerendia Free Trial Conversion iRep Email` |
| `MISCELLANEOUS` | Other | `Kerendia Speaker Program Thank You iRep Email`; two emails about adding Kerendia to the favourites list in hospital software (`MAC-FINE-US-0036-1 ... Epic ...`, `MAC-FINE-US-0052-1 ... Cerner ...`) |

An email with a template not in any list gets 0 in every template group (it still counts for delivered / opened / clicked).

**Step 4. Attach the dates and build the doctor key** (cross join, keep the lookback, remove rows without a BHID, create `HCP_COHORT_ID`).

**Step 5. Add up per doctor and day.** The labels are added up and renamed: `TOTAL_IREP_EMAILS_DELIVERED`, `TOTAL_IREP_EMAILS_CLICKED`, `TOTAL_IREP_EMAILS_OPENED`, and `TOTAL_IREP_APPRVD_DOC_NM_<group>`.

**Step 6. Fill in the calendar and add up the last 90 days** (see the introduction file, section 0.3).

**Step 7. Keep the last day only and save.** Keep the row for `LOOKBACK_END_DATE`, remove the daily columns, rename the day column `SVC_DT`, put the BHID in its own column, add `PULL_DT` (text), overwrite `kerendia_nba_3_hcp_model_irep_features_for_inference`.

**Check cell** (does not change the data): counts the template columns ending in `LAST_1_MONTH` (there are none, since only 3 months is built).

## 4. The features explained

**14 features**, all for **the last 90 days**:

| Feature | What it means |
| --- | --- |
| `TOTAL_IREP_EMAILS_DELIVERED_IN_LAST_3_MONTH` | Rep emails delivered (but see section 6: currently always 0) |
| `TOTAL_IREP_EMAILS_OPENED_IN_LAST_3_MONTH` | Rep emails the doctor opened (each email counts once, however often it was opened) |
| `TOTAL_IREP_EMAILS_CLICKED_IN_LAST_3_MONTH` | Rep emails in which the doctor clicked a link (each email once) |
| `TOTAL_IREP_APPRVD_DOC_NM_<group>_IN_LAST_3_MONTH` (11 features, one per group above) | Rep emails sent with a template from that group |

**Example.** In the last 90 days Dr. Ahmed's rep sent her 4 Kerendia emails: 2 meeting invitations and 2 with a template not in any list. She opened 3 (one of them twice) and clicked in 1. Her features: opened = 3, clicked = 1, invite = 2, all other template groups = 0, delivered = 0 (see section 6).

## 5. What the final table looks like

One row per doctor with at least one delivered Kerendia rep email in the lookback year (17,460 doctors in the saved table of 24 September 2026):

| Column | Meaning |
| --- | --- |
| `HCP_COHORT_ID` | The doctor (Bayer ID + `_I01`) |
| `SVC_DT` | The end of the lookback |
| 14 features | Above |
| `BHID` | The doctor's Bayer ID |
| `PULL_DT` | Date the notebook ran (text) |

## 6. Things to watch out for

* **"Delivered" is always 0.** The query keeps statuses that **start with** "Delivered", but the label requires the status to be **exactly** `Delivered`. In the saved table the delivered feature is 0 for every doctor, so the real status text must be slightly different (for example with a suffix). The number of emails sent is therefore not available.
* **Most template features are 0.** In the saved table only `INVITE` is above 0 (31 emails in the last 3 months); all other groups are 0, so current templates have names that are not in the hard-coded lists.
* **Opened and clicked are yes/no per email**, not counts of opens and clicks. This is different from HQ emails, where every open counts.
* **Only a 3-month period exists.**
* **Rows can be multiplied when the dates table has several cohorts.** At the hand run of 4 May 2026 the dates table held 26 training cohorts (`C01` to `C26`, each with a 90-day lookback) instead of `I01`; the cross join turned 581,135 emails into 15,109,510 rows (26 copies). The saved table of 24 September 2026 is correct (only `I01`), but the notebook does not protect against this.
* **These emails are also counted in Digital.** The Digital notebook (non-personal features) keeps rep emails as a channel (`IREP_EMAILS`) and as a vendor (`IREP_EMAIL`), so the model sees them twice.
