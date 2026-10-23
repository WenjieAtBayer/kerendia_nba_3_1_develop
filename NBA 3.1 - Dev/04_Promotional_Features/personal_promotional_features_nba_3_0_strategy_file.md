# Personal Promotional Features — NBA 3.0 (Legacy)

**Scope:** promotion that involves a sales rep: Sales Rep Calls (`25`), BHO (organisation) Calls (`13`), iRep Emails (`16`), ClickStream / CLM (`18`)  
**NBA 3.0 (legacy Ops):** `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Companion file:** `personal_promotional_features_strategic_file_nba_3_0_legacy.md`  
**Built from:** a review of the code in each notebook listed above, plus a check of the tables they last saved  
**Date:** October 22, 2026

## What is this document about?

Bayer uses a model called **Next Best Action (NBA)** to suggest, for each doctor, which Kerendia promotional action is most useful next (for example: a rep visit, a rep email, an event invitation). Kerendia is a Bayer medicine for chronic kidney disease in people with type 2 diabetes (and, more recently, heart failure).

To make its suggestions, the model needs to know each doctor's recent history. That history is turned into numbers called **features**. A feature is simply one fact about a doctor written as a number, for example *"this doctor received 3 face-to-face rep visits in the last 3 months"*.

This document explains the features about **personal promotion**: promotion that involves a Bayer **sales representative** ("rep"). There are four channels:

| Channel | In plain words | Notebook |
| --- | --- | --- |
| Sales Rep Calls | Visits ("calls") a rep made to the doctor: in person, by phone, remotely, or in a group | `25_promotional_features_call` |
| BHO Calls | Rep calls recorded against the doctor's **organisation** (practice, clinic, hospital) instead of the doctor personally, given to every doctor of that organisation | `13_promotional_features_bho_calls` |
| iRep Emails | Emails the rep sent to the doctor from approved templates | `16_promotional_features_irep` |
| ClickStream / CLM | How long the rep showed Kerendia slides on a tablet during calls | `18_promotional_ClickStream_features` |

This describes the **old version** of the pipeline (NBA 3.0). A "pipeline" is the chain of notebooks that runs one after another to prepare the data for the model.

**How each channel section is organised:**

1. **In short**: what the channel is and why it matters.
2. **Where the data comes from**: the exact tables, what one line represents, every column used and what it means, and which lines are kept.
3. **How the features are built, step by step**: every step the notebook takes. For each step: *what happens*, *why*, and the details to know.
4. **The features explained**: every feature, what it counts, how to interpret it, with an example.
5. **What the final table looks like**: every column of the saved table.
6. **Things to watch out for**: every known problem, fully explained. Codes such as LK-1 refer to the companion file; each problem is also explained here.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code, so you can search for it. Its meaning is always given next to it.

**About the numbers.** Two kinds of numbers appear. Figures from **inside the notebooks** (for example "484,119 calls") come from the last time someone ran the notebook by hand; the date is always given. Figures about the **saved tables** come from a check of the tables as they are now (all four were last saved on 24 September 2026). Both will change at the next run.

---

## 0. Key ideas to understand first

### 0.1 The time frame: what period do the features cover?

The model is used on an **anchor date** (the first day of a month). It looks back over the previous year of activity (the **lookback**), but stops about two weeks early, because recent data takes time to arrive. With the current dates:

| Date | Meaning |
| --- | --- |
| 16 September 2025 | Start of the lookback |
| 16 September 2026 | End of the lookback (the "as of" date for every feature) |
| 1 October 2026 | Anchor date: the model makes its suggestions |
| 7 October to 6 November 2026 | The period the model tries to predict |

So every feature answers a question like *"what happened up to 16 September 2026?"*.

**Where these dates come from.** Every notebook reads a small table called `promotional_cohort_inference_dates` (saved in `ops_pipeline/notebook_output/`) and takes the row for cohort `I01` (a cohort is a "snapshot" of all doctors at one anchor date; when the model is used for real there is only one, `I01`). Its columns:

| Column | Meaning | Current value |
| --- | --- | --- |
| `SERIAL_NO` | Row number | `1` |
| `ANCHOR_DATE` | The anchor date | `2026-10-01` |
| `PREDICTION_START_DATE` | First day of the prediction window | `2026-10-07` |
| `PREDICTION_END_DATE` | Last day of the prediction window | `2026-11-06` |
| `MERGE_KEY` | A helper column (always `1`) that other notebooks use to attach these dates to their tables. Not used by these four notebooks. | `1` |
| `COHORT` | Cohort name | `I01` |
| `LOOKBACK_START_DATE` | First day of the lookback | `2025-09-16` |
| `LOOKBACK_END_DATE` | Last day of the lookback | `2026-09-16` |

The hand-run outputs inside each notebook used older dates (given in each section).

### 0.2 Things every notebook shares

| Topic | What happens |
| --- | --- |
| Doctor key | Every notebook identifies a doctor with `HCP_COHORT_ID` = BHID + `_` + cohort, for example `BH10000342_I01`. The **BHID** is Bayer's own ID for a doctor (`BH` followed by digits). Joining the cohort name keeps doctors separate across cohorts during training; in real use it is always `_I01`. |
| Attaching the dates | Each notebook does a **cross join** between its data and the dates table: every row gets the lookback start and end dates (and the cohort name) written next to it. Then rows outside the lookback are removed. A cross join pairs every row with **every** row of the dates table, and the notebooks do **not** first keep only `I01`: with one row in the dates table nothing is duplicated, but if the table holds several cohorts, every row is copied once per cohort (this happened in one iRep run, see section 3.6). |
| "In the last N months" | One "month" means 30 days, counted back from the end of the lookback and including that day: `_IN_LAST_1_MONTH` = last 30 days, `_2_` = 60, `_3_` = 90, `_4_` = 120, `_5_` = 150, `_6_` = 180. How it is calculated is explained in section 1.3, step 9. |
| Helper notebook `00_connection` | Run at the start of every notebook. It installs the Snowflake connector (Snowflake is Bayer's central data warehouse), reads the Snowflake login from the secure secret store (`US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`), and defines `Get_Data_Snowflakes(query)`: a function that sends a SQL query to Snowflake and returns the result as a table. All four notebooks read Snowflake with it. |
| Helper notebook `00_step23_function` | Run by all four notebooks. It defines shared time-window functions, but these notebooks do not use them: each writes its own daily versions (`step2_fill_missing_dates` / `step2_fill_missing_date` and `step3_lag_date`). |
| Helper notebook `00_config` | Only run by Sales Rep Calls. It loads shared settings, file paths and run dates from a control table (`get_latest_approved_dates()`); the notebook still takes its dates from `promotional_cohort_inference_dates`. |
| Unused input | All four load the NPI-to-BHID translation table (`kerendia_nba_3_0_npi_bhid_mapping`; NPI is a doctor's official US ID) but never use it, because the call and email data already carry the BHID. |
| Run date `PULL_DT` | Added to every saved table: the date the notebook ran. Stored as text like `2026_09_24`, except in the Sales Rep Calls table, where it is a real date. |
| Where tables are saved | As Delta tables (the Databricks table format) in `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/`. Each run **overwrites** the previous table completely, including its list of columns. |
| Which doctors appear | A doctor appears only if they had at least one activity in that channel **during the whole lookback year**. Because the features only look at the last 30 to 180 days, many doctors appear with all features 0 (for example, 46,250 of the 88,511 doctors in the Sales Rep Calls table had no call in the last 90 days). Doctors with no activity all year are missing and are treated as 0 later. |
| What happens next | A later notebook, `99_Combine_Physician_Data_Promotional&Acc`, combines all channel tables into one row per doctor for the model. |

---

## 1. Sales Rep Calls (`25_promotional_features_call`)

### 1.1 In short

A **call** is a contact between a Bayer rep and a doctor to talk about Kerendia ("detailing" = presenting a product to a doctor). Reps record every call in **Veeva CRM**, the software they use to plan and log their visits. Values ending in `_vod` come from Veeva.

This channel counts, for each doctor, how many Kerendia calls they received in the **last 3 months**, broken down by **how** the call was held (in person, phone, remote, group), **what kind** of call it was (with or without samples), **why** it was made (its purpose), and how long the calls lasted.

It helps the model answer: *"How much rep contact has this doctor had recently, and of what kind?"*

### 1.2 Where the data comes from

**Tables** (in Snowflake, read with `Get_Data_Snowflakes`):

| Table | What one line is | Role |
| --- | --- | --- |
| `CPH_DB_PROD.MODEL_V2.FACT_CALL` | One call record for one product discussed (`DETL_PROD`). Only the Kerendia lines are kept. | The calls |
| `CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF` | One link between a Veeva customer ID (`SOURCE_CUST_ID`) and a Bayer customer ID (`BAYER_CUST_ID`) | Translates the Veeva ID into the doctor's BHID |

**Columns used:**

| Column | What it means | Renamed to |
| --- | --- | --- |
| `SOURCE_CUST_ID` | The customer's ID in Veeva; used to find the BHID | |
| `BAYER_CUST_ID` | The Bayer ID of the customer (a doctor `BH...`, or an organisation `BHO...`) | `BHID` |
| `CALL_DATE` | Day of the call (converted to a date) | `MONTH_ID` (despite the name, it is a day) |
| `CALL_REC_TYP_NM` | The Veeva "record type": the form the rep used to log the call, which says **how** the call was held (e.g. `BPH_Face2Face_SIG`) | Translated into `CHNNL_NM` (step 3) |
| `CALL_TYP` | **What kind** of call: `Detail Only`, `Detail with Sample`, `Group Detail`, `Group Detail with Sample`, `Event Detail` | `CALL_TYP_CD` |
| `CALL_PURPS` | **Why** the call was made (purpose, see step 4) | `CALL_PRPSE` |
| `CALL_DUR` | Length of the call, as text. The code does not state the unit; values such as 30 per call suggest minutes. | `CALL_DURATION` |
| `STAT` | Status of the call record | Used only to filter |
| `DETL_PROD` | Product discussed | Used only to filter |

**Which lines are kept:**

* Status is submitted (`UPPER(STAT) = 'SUBMITTED_VOD'`): the rep finalised the call in Veeva. Draft or planned calls are removed.
* Product is Kerendia.
* The Bayer ID exists and does **not** contain `BHO` (calls to organisations go to the BHO notebook, section 2).
* The call date is inside the lookback.

The translation table is attached with a left join, but because the Bayer ID must not be empty, only calls that found a Bayer ID remain.

**History of the source.** The query was updated on 10 September 2025 (the F2F rule was widened and `GROUP CALL SIGNED` was added to group calls). The older query is still in the notebook, switched off ("commented out").

**Size at the hand run of 29 July 2026** (lookback 17 July 2025 to 17 July 2026): 484,119 calls for 89,462 doctors. Calls by channel (after step 3):

| Channel | Calls |
| --- | --- |
| `F2F` | 465,516 |
| `GROUP_CALL` | 16,375 |
| `REMOTE_CALL` | 2,188 |
| `PHONE` | 35 |
| `Do not select` (not translated) | 2 |
| `Face2Face KAM Call` (not translated) | 3 |

Call types seen: `Detail Only`, `Detail with Sample`, `Group Detail`, `Group Detail with Sample` (no `Event Detail`).

### 1.3 How the features are built, step by step

**Step 1. Get the lookback dates** (cohort `I01`, section 0.1).

**Step 2. Read the calls** with the filters above.

**Step 3. Translate the record type into a channel.**
*What:* the record type is converted to capital letters and compared with these rules:

| Record type (in capital letters) | Becomes channel | Meaning |
| --- | --- | --- |
| Contains `BPH_FACE2FACE_SIG`, or starts with `FACE2FACE_SIG` | `F2F` | Face-to-face visit |
| Contains `BPH_NON_FACE2FACE` | `PHONE` | Not in person (phone) |
| Exactly `BPH_GROUP_CALL_SIG`, `GROUP CALL SIGNED` or `EVENT_VOD` | `GROUP_CALL` | Several doctors at once, or at an event |
| Contains `BPH_REMOTE` | `REMOTE_CALL` | Video / online meeting |
| Anything else | Keeps its original value (e.g. `Do not select`, `Face2Face KAM Call`) | Not counted in any channel feature |


**Step 4. Give each call a set of yes/no labels.**
*What:* each call gets a 1 (yes) or 0 (no) in each of these columns. Call type and purpose must match the text **exactly**, including capital letters:

| Label | Is 1 when |
| --- | --- |
| `F2F`, `PHONE`, `GROUP_CALL`, `REMOTE_CALL` | The channel from step 3 |
| `DETAIL_ONLY` | Call type is `Detail Only`: the rep discussed Kerendia, no samples |
| `DETAIL_WITH_SAMPLE` | `Detail with Sample`: discussed and left samples |
| `GROUP_DETAIL` | `Group Detail`: discussed with several people at once |
| `GROUP_DETAIL_WITH_SAMPLE` | `Group Detail with Sample` |
| `EVENT_DETAIL` | `Event Detail`: discussed at an event |
| `CALL_PURPOSE_PROMOTIONAL_ACTIVITY` | Purpose is `Promotional Activity` |
| `CALL_PURPOSE_PROMOTIONAL_ACTIVITY_WITH_MEAL` | `Promotional Activity with meal` |
| `CALL_PURPOSE_EVENT_RELATED_PROMOTIONAL_ACTIVITY` | `Event related Promotional Activity` |
| `CALL_PURPOSE_NON_PROMOTIONAL_ACTIVITY` | `Other non-promotional Activity` |
| `CALL_PURPOSE_MISCELLANEOUS` | One of 9 other purposes: `Contract negotiation / Tender assistance`, `Technical Operation/Installation`, `Reactive Sample / HVPI`, `Market Access`, `Regulatory Compliance`, `Education / Training`, `Technical Information`, `Handover of SPC (Summary of Product Characteristics)`, `Handover of Scientific Publication / Reprint` |

**Step 5. Clean the duration.** Empty duration text becomes empty (NULL, no value), so it is ignored when adding up. The text is not explicitly turned into a number; Spark (the data-processing tool) converts it automatically when adding up.

**Step 6. Attach the dates and build the doctor key** (cross join with the dates table, keep calls inside the lookback, remove rows without a BHID, create `HCP_COHORT_ID`; section 0.2).

**Step 7. Add up per doctor and day.** For each doctor and day, the labels and the duration are added up, and `TOTAL_` is put in front of each name (e.g. `TOTAL_F2F` = number of face-to-face calls that day).

**Step 8. Build the "channel and call type" combinations.**
*What:* for every channel and every call type found in the data that day, a combined column is created: `TOTAL_<channel>_AND_<call type>`, for example `TOTAL_F2F_AND_DETAIL_ONLY`. Its value is the **smaller** of the two daily totals (`least()`).
*Which combinations:* the lists of channels and call types are read from the data at run time, leaving out `Do not select` and `Face2Face KAM Call`. So the number of combinations depends on which values exist (see 1.6).
*Why the smaller number:* the daily totals no longer say which call had which type, so the smaller number is used as an estimate of "calls that were both". It is exact when a doctor had only one kind of call that day, but can be too high otherwise (example in 1.6).

**Step 9. Fill in the calendar and add up the last 90 days.**
*What:* for every doctor with at least one call in the lookback, the notebook creates one row for **every day** of the lookback (`step2_fill_missing_dates`); days without calls get 0. Then, for each day, it adds up that day and the 89 days before it (`step3_lag_date` with the single period 90 days). Because there is exactly one row per day, "the last 90 rows" equals "the last 90 days". The new column is called `<name>_IN_LAST_3_MONTH`.
*Why:* without the empty days, "the last 90 rows" could reach back much more than 90 days.

**Step 10. Keep the last day only and save.**
*What:* keep only the row for the last day of the lookback (`LOOKBACK_END_DATE`), remove the daily columns, rename the day column `SVC_DT`, take the BHID out of `HCP_COHORT_ID` into its own column, add `PULL_DT` as a real date (`current_date()`), and overwrite `kerendia_nba_3_hcp_model_call_features_for_inference`.

**Check cell** (does not change the data): a count of empty values per column (all 0 at the last hand run).

### 1.4 The features explained

Every feature covers **the last 90 days** (`_IN_LAST_3_MONTH`) and counts **calls** (except duration).

**How the call was held (channel):**

| Feature | What it means |
| --- | --- |
| `TOTAL_F2F_IN_LAST_3_MONTH` | Face-to-face calls |
| `TOTAL_PHONE_IN_LAST_3_MONTH` | Phone calls |
| `TOTAL_GROUP_CALL_IN_LAST_3_MONTH` | Group calls (several doctors, or at an event) |
| `TOTAL_REMOTE_CALL_IN_LAST_3_MONTH` | Remote (video / online) calls |

**What kind of call (call type):**

| Feature | What it means |
| --- | --- |
| `TOTAL_DETAIL_ONLY_IN_LAST_3_MONTH` | Calls where Kerendia was discussed, no samples |
| `TOTAL_DETAIL_WITH_SAMPLE_IN_LAST_3_MONTH` | Calls where Kerendia was discussed and samples were left |
| `TOTAL_GROUP_DETAIL_IN_LAST_3_MONTH` | Group discussions |
| `TOTAL_GROUP_DETAIL_WITH_SAMPLE_IN_LAST_3_MONTH` | Group discussions with samples |
| `TOTAL_EVENT_DETAIL_IN_LAST_3_MONTH` | Discussions at events |

**Why the call was made (purpose):**

| Feature | What it means |
| --- | --- |
| `TOTAL_CALL_PURPOSE_PROMOTIONAL_ACTIVITY_IN_LAST_3_MONTH` | Promotional calls |
| `TOTAL_CALL_PURPOSE_PROMOTIONAL_ACTIVITY_WITH_MEAL_IN_LAST_3_MONTH` | Promotional calls with a meal |
| `TOTAL_CALL_PURPOSE_EVENT_RELATED_PROMOTIONAL_ACTIVITY_IN_LAST_3_MONTH` | Promotional calls linked to an event |
| `TOTAL_CALL_PURPOSE_NON_PROMOTIONAL_ACTIVITY_IN_LAST_3_MONTH` | Non-promotional calls |
| `TOTAL_CALL_PURPOSE_MISCELLANEOUS_IN_LAST_3_MONTH` | Calls with one of the 9 other purposes (step 4) |

**How long:**

| Feature | What it means |
| --- | --- |
| `TOTAL_CALL_DURATION_IN_LAST_3_MONTH` | Total recorded length of all calls (unit not stated; probably minutes). Calls with no recorded length add nothing. |

**Combinations (channel and call type):** `TOTAL_<channel>_AND_<call type>_IN_LAST_3_MONTH`, an estimate of the calls that were both (step 8). In the saved table of 24 September 2026 there are 12: `F2F`, `GROUP_CALL` and `REMOTE_CALL`, each combined with `DETAIL_ONLY`, `DETAIL_WITH_SAMPLE`, `GROUP_DETAIL` and `GROUP_DETAIL_WITH_SAMPLE`. (No phone calls happened in that lookback, so there are no `PHONE_AND_...` columns; at the hand run of 29 July 2026 there were 16, including phone.)

**How many features:** 15 base features + the combinations. Saved table: 15 + 12 = **27**. Hand run of 29 July 2026: 15 + 16 = 31. The most possible is 15 + 4 x 5 = 35.

There is **no "total calls" feature**. The total is roughly the sum of the four channel features (calls with an untranslated record type are in none of them).

**Example.** In the 90 days before the end of the lookback, Dr. Garcia had 2 face-to-face calls where samples were left (30 minutes each) and 1 remote call without samples (15 minutes), all promotional, on different days. Her features: F2F = 2, remote = 1, detail with sample = 2, detail only = 1, promotional activity = 3, duration = 75, F2F and detail with sample = 2, remote and detail only = 1, all others 0.

In the saved table, the busiest features over all doctors are face-to-face (100,719 calls), group detail (78,862) and detail only (20,023); phone and event detail are 0 for everyone.

### 1.5 What the final table looks like

One row per doctor with at least one Kerendia call in the lookback year (88,511 doctors in the saved table of 24 September 2026):

| Column | Meaning |
| --- | --- |
| `HCP_COHORT_ID` | The doctor (Bayer ID + `_I01`) |
| `SVC_DT` | The end of the lookback (the "as of" date) |
| 27 features | Above |
| `BHID` | The doctor's Bayer ID |
| `PULL_DT` | Date the notebook ran (a real date, not text as in the other channels) |

### 1.6 Things to watch out for

* **The combinations are an estimate and can be too high.** They use the smaller of two daily totals. Example: one day Dr. Garcia had 1 face-to-face call with only discussion (detail only) and 1 remote group discussion. Face-to-face = 1 and group detail = 1, so `TOTAL_F2F_AND_GROUP_DETAIL` = 1, although she had no face-to-face group discussion.
* **The number of combination features changes with the data.** The lists are read from the data each run: 16 columns on 29 July 2026, 12 on 24 September 2026. The model expects a fixed list of columns.
* **The notebook can stop with an error when a new value appears.** If the data contains a new record type or call type, the combination step looks for a `TOTAL_...` column that was never created, and the run fails. Only `Do not select` and `Face2Face KAM Call` are excluded by hand.
* **Exact text matching.** Call types and purposes must match exactly; a call with a new or differently written purpose is counted in no purpose feature.
* **Some channels and types are always 0 right now.** Phone and event detail are 0 for every doctor in the saved table.
* **Duration is loosely handled.** The unit is not stated, the text is converted to a number automatically, and calls without a recorded length add nothing.
* **Many doctors are all zeros.** 46,250 of the 88,511 doctors had calls earlier in the year but none in the last 90 days.
* **Only a 3-month period exists.**
* **`PULL_DT` has a different type** (date) from the other tables (text).

---

## 2. BHO Calls (`13_promotional_features_bho_calls`)

### 2.1 In short

Some rep calls are recorded not against one doctor but against an **organisation**: a practice, clinic or hospital. Organisations have their own Bayer ID, starting with `BHO` (the "BHO ID"). These calls are left out of the Sales Rep Calls features (section 1).

This notebook gives each organisation call to **every doctor linked to that organisation**, and builds the same kind of counts as section 1, with `BHO_` in front of every name and six periods (1 to 6 months) instead of one.

It helps the model answer: *"How much rep activity has there been at the places where this doctor works?"* It does not mean the doctor personally met the rep.

### 2.2 Where the data comes from

**Tables:**

| Table | What one line is | Role |
| --- | --- | --- |
| `CPH_DB_PROD.MODEL_V2.FACT_CALL` + `MAP_CUSTOMER_XREF` (Snowflake) | One call record, as in section 1.2 | The calls, here only for organisations |
| `kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` (saved table) | One doctor the model is allowed to score (the "HCP universe"), identified by `PROVIDER_ID` | Decides which doctors get features |
| `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING` (Unity Catalog table) | One link between `PROVIDER_ID` and `BH_ID` | Translates the universe into BHIDs |
| `PHCDW.PHCDW_STG.MDM_STG_HCP_ACCT_AFFL` (Snowflake) | One link between a doctor (`BH_ID`) and an organisation (`BHO_ID`) it is affiliated with ("MDM" = Bayer's master data on doctors and organisations) | Says which doctors belong to which organisation |

**Columns used from the calls:** the same as section 1.2 (record type, call type, duration, purpose, date, status, product). Here `BAYER_CUST_ID` is renamed `BHO_ID`.

**Which calls are kept:** submitted, Kerendia, inside the lookback, and the Bayer ID **contains** `BHO` (the opposite of section 1).

**Size at the hand run of 27 November 2025** (lookback 16 November 2024 to 16 November 2025):

| Item | Number |
| --- | --- |
| Doctors in the HCP universe | 222,125 |
| Of these, found in the provider-to-BHID table | 222,051 |
| Doctor-organisation links for those doctors | 928,773 |
| Organisation calls | 376,617 |
| Rows after giving each call to every linked doctor | 30,351,434 (about 80 doctors per call) |
| Doctors who received at least one call this way | 163,233 |

### 2.3 How the features are built, step by step

**Step 1. Get the lookback dates** (cohort `I01`).

**Step 2. List the target doctors.** Read the HCP universe and translate `PROVIDER_ID` into BHID with an **inner join** (only doctors found in both are kept).

**Step 3. Link doctors to organisations.** Inner join with the affiliation table: one row per doctor-organisation pair. A doctor linked to 5 organisations appears 5 times.

**Step 4. Read the organisation calls and translate the record type into a channel.** The rules are **not the same** as in section 1:

| Record type (in capital letters) | Becomes channel | Difference from section 1 |
| --- | --- | --- |
| Contains `BPH_FACE2FACE_SIG`, or is exactly `FACE2FACE SIGNED` | `F2F` | Section 1 accepts anything starting with `FACE2FACE_SIG` |
| Contains `BPH_NON_FACE2FACE` | `PHONE` | Same |
| Exactly `BPH_GROUP_CALL_SIG` or `EVENT_VOD` | `GROUP_CALL` | `GROUP CALL SIGNED` is missing |
| Contains `BPH_REMOTE` | `REMOTE_CALL` | Same |
| Anything else | Keeps its original value | Same |

**Step 5. Give each call to every linked doctor.** Inner join of the calls with the doctor-organisation pairs on `BHO_ID`. A call at an organisation with 80 linked doctors becomes 80 rows, one per doctor.

**Step 6. Labels.** Exactly the same yes/no labels as section 1.3, step 4 (channel, call type, purpose, with the same lists).

**Step 7. Clean the duration.** Different from section 1: any duration that is not a plain number (only digits and a dot) becomes `0`, then the text is turned into a number. Empty values stay empty and are ignored when adding up.

**Step 8. Attach the dates and build the doctor key** (cross join, keep the lookback, remove rows without a BHID, create `HCP_COHORT_ID`).

**Step 9. Add up per doctor and day**, with `TOTAL_` in front of each name (same 15 measures as section 1). **No combination features** are built here.

**Step 10. Fill in the calendar and add up the periods**, as in section 1.3 step 9, but for 30, 60, 90, 120, 150 and 180 days.

**Step 11. Keep the last day only and save.** Keep the row for `LOOKBACK_END_DATE`, remove the daily columns, put `BHO_` in front of every feature, rename the day column `SVC_DT`, put the BHID in its own column, add `PULL_DT` (text) and overwrite `kerendia_nba_3_hcp_model_call_features_bhoid_for_inference`.

### 2.4 The features explained

The 15 measures of section 1.4 (4 channels, 5 call types, 5 purposes, duration), each for 6 periods: **15 x 6 = 90 features**. The name pattern is `BHO_TOTAL_<measure>_IN_LAST_<N>_MONTH`, for example:

| Feature | What it means |
| --- | --- |
| `BHO_TOTAL_F2F_IN_LAST_3_MONTH` | Face-to-face calls at any of the doctor's organisations in the last 90 days |
| `BHO_TOTAL_DETAIL_WITH_SAMPLE_IN_LAST_1_MONTH` | Organisation calls with samples in the last 30 days |
| `BHO_TOTAL_CALL_PURPOSE_PROMOTIONAL_ACTIVITY_IN_LAST_6_MONTH` | Promotional organisation calls in the last 180 days |
| `BHO_TOTAL_CALL_DURATION_IN_LAST_2_MONTH` | Total length of organisation calls in the last 60 days |

How to interpret them: the **amount of rep activity around the doctor**, not contact with the doctor personally.

**Example.** Dr. Kim is linked to two organisations, Clinic A and Hospital B. In the last 30 days a rep made 2 face-to-face calls at Clinic A and 1 at Hospital B. Then `BHO_TOTAL_F2F_IN_LAST_1_MONTH` = 3 for Dr. Kim, and also 2 for every other doctor of Clinic A, even those who were not there.

### 2.5 What the final table looks like

One row per universe doctor linked to an organisation with at least one call in the lookback year (170,883 doctors in the saved table of 24 September 2026):

| Column | Meaning |
| --- | --- |
| `HCP_COHORT_ID` | The doctor (Bayer ID + `_I01`) |
| `SVC_DT` | The end of the lookback |
| 90 features | Above |
| `BHID` | The doctor's Bayer ID |
| `PULL_DT` | Date the notebook ran (text) |

### 2.6 Things to watch out for

* **One call is counted for many doctors.** Each organisation call is copied to every linked doctor (about 80 on average). Totals are therefore very large: in the saved table, 6.2 million face-to-face "calls" in the last 3 months, against about 100,000 in the personal Sales Rep Calls table.
* **Doctors linked to several organisations collect calls from all of them.**
* **Group calls are always 0.** The group rule is missing `GROUP CALL SIGNED` (probably the reason), and the face-to-face rule is stricter than in section 1, so the same call can be classified differently in the two notebooks. In the saved table, phone, group call, detail with sample and event detail are 0 for every doctor.
* **Only doctors in the HCP universe are included** (steps 2 and 3).
* **No combination features.** An earlier version of this document said the combinations of section 1 were also built here; the code does not do this.
* **Different duration cleaning** from section 1 (step 7), so the two duration features are not calculated the same way.
* **The same exact-text matching issues as section 1** for call types and purposes.

---

## 3. iRep Emails (`16_promotional_features_irep`)

### 3.1 In short

An **iRep email** is an email that a rep sends to a doctor from Veeva, using a template approved by Bayer's review team (an "approved document"). It is different from HQ emails, which are sent centrally by Bayer's head office (non-personal file).

This channel counts, for each doctor, how many Kerendia iRep emails were delivered, opened and clicked in the **last 3 months**, and which templates were used.

It helps the model answer: *"Is this doctor reading the emails their rep sends?"*

### 3.2 Where the data comes from

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
* The **month** of the sent date is not after the end of the lookback. There is no start date here; older emails are removed in step 3.

**History of the source.** This query was received from the data team on 29 October 2025. The older source (`PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA...`) is still in the notebook, switched off.

**Size at the hand run of 4 May 2026:** 581,135 emails for 101,022 doctors (before the lookback filter).

### 3.3 How the features are built, step by step

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

**Step 6. Fill in the calendar and add up the last 90 days** (as in section 1.3, step 9).

**Step 7. Keep the last day only and save.** Keep the row for `LOOKBACK_END_DATE`, remove the daily columns, rename the day column `SVC_DT`, put the BHID in its own column, add `PULL_DT` (text), overwrite `kerendia_nba_3_hcp_model_irep_features_for_inference`.

**Check cell** (does not change the data): counts the template columns ending in `LAST_1_MONTH` (there are none, since only 3 months is built).

### 3.4 The features explained

**14 features**, all for **the last 90 days**:

| Feature | What it means |
| --- | --- |
| `TOTAL_IREP_EMAILS_DELIVERED_IN_LAST_3_MONTH` | Rep emails delivered (but see 3.6: currently always 0) |
| `TOTAL_IREP_EMAILS_OPENED_IN_LAST_3_MONTH` | Rep emails the doctor opened (each email counts once, however often it was opened) |
| `TOTAL_IREP_EMAILS_CLICKED_IN_LAST_3_MONTH` | Rep emails in which the doctor clicked a link (each email once) |
| `TOTAL_IREP_APPRVD_DOC_NM_<group>_IN_LAST_3_MONTH` (11 features, one per group above) | Rep emails sent with a template from that group |

**Example.** In the last 90 days Dr. Ahmed's rep sent her 4 Kerendia emails: 2 meeting invitations and 2 with a template not in any list. She opened 3 (one of them twice) and clicked in 1. Her features: opened = 3, clicked = 1, invite = 2, all other template groups = 0, delivered = 0 (see 3.6).

### 3.5 What the final table looks like

One row per doctor with at least one delivered Kerendia rep email in the lookback year (17,460 doctors in the saved table of 24 September 2026):

| Column | Meaning |
| --- | --- |
| `HCP_COHORT_ID` | The doctor (Bayer ID + `_I01`) |
| `SVC_DT` | The end of the lookback |
| 14 features | Above |
| `BHID` | The doctor's Bayer ID |
| `PULL_DT` | Date the notebook ran (text) |

### 3.6 Things to watch out for

* **"Delivered" is always 0.** The query keeps statuses that **start with** "Delivered", but the label requires the status to be **exactly** `Delivered`. In the saved table the delivered feature is 0 for every doctor, so the real status text must be slightly different (for example with a suffix). The number of emails sent is therefore not available.
* **Most template features are 0.** In the saved table only `INVITE` is above 0 (31 emails); all other groups are 0, so current templates have names that are not in the hard-coded lists.
* **Opened and clicked are yes/no per email**, not counts of opens and clicks. This is different from HQ emails, where every open counts.
* **Only a 3-month period exists.**
* **Rows can be multiplied when the dates table has several cohorts.** At the hand run of 4 May 2026 the dates table held 26 training cohorts (`C01` to `C26`, each with a 90-day lookback) instead of `I01`; the cross join turned 581,135 emails into 15,109,510 rows (26 copies). The saved table of 24 September 2026 is correct (only `I01`), but the notebook does not protect against this.
* **These emails are also counted in Digital.** The Digital notebook (non-personal file) keeps rep emails as a channel (`IREP_EMAILS`) and as a vendor (`IREP_EMAIL`), so the model sees them twice.

---

## 4. ClickStream / CLM (`18_promotional_ClickStream_features`)

### 4.1 In short

During a call, reps can show Kerendia slides and videos on a tablet. This is called **CLM** ("Closed Loop Marketing"). The tablet records how the content was used during each call; this record is the **clickstream**.

This channel adds up, for each doctor, **how much time** Kerendia tablet content was used during their calls, for six periods (1 to 6 months).

It helps the model answer: *"When the rep visits, does this doctor spend time on our material?"*

### 4.2 Where the data comes from

**Tables** (in Snowflake):

| Table | What one line is | Role |
| --- | --- | --- |
| `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM` | One piece of tablet content used in one call | The time measures |
| `CPH_DB_PROD.MODEL_V2.FACT_CALL` + `MAP_CUSTOMER_XREF` | One call record (section 1.2) | Keeps only real, submitted Kerendia calls to doctors |

**Columns used:**

| Column | What it means |
| --- | --- |
| `CALL_ID` | The call the content was shown in. Links the two tables. |
| `BAYER_HCP_ID` | The doctor's Bayer ID. Renamed `BHID`. |
| `DATE_ID` | Day of the call, written as text `yyyyMMdd` (e.g. `20250917`) |
| `USAGE_DUR` | "Usage duration": a time measure recorded by the tablet app. The code does not define it or its unit; the name suggests how long the content was in use. |
| `PRESN_DUR` | "Presentation duration": a second time measure, probably how long the content was being presented. Not defined in the code either. |
| `BAYER_PROD_NM` | Product of the content. Used only to keep Kerendia. |
| From the calls: `STAT`, `DETL_PROD`, `BAYER_CUST_ID` | Used only to keep submitted Kerendia calls to doctors (not organisations) |

**Which lines are kept:**

* Clickstream: product is Kerendia, date is not after the end of the lookback (`SELECT DISTINCT`).
* Calls: submitted, Kerendia, doctor ID present and not `BHO`; **no date filter** (only the call ID is used).

**Size at the hand run of 7 October 2025** (lookback 17 September 2024 to 17 September 2025): 92,081 calls for 27,537 doctors (after step 4, before the lookback filter).

### 4.3 How the features are built, step by step

**Step 1. Get the lookback dates** (cohort `I01`). The end date is also written as text `yyyyMMdd` to compare it with `DATE_ID`.

**Step 2. Read the clickstream and the submitted call IDs.**

**Step 3. Keep one line per call.**
*What:* when a call has several lines, only the line with the **highest usage duration** is kept (if two are equal, the one with the highest presentation duration).
*Detail to know:* if a rep showed several pieces of content in one call, only the longest one is counted, not their total.

**Step 4. Keep only submitted calls.** Inner join with the submitted call IDs. The time columns are renamed `MAX_USAGE_DUR` and `MAX_PRESN_DUR`.

**Step 5. Turn `DATE_ID` into a date.** A helper column `SUBMITTED_CALL_COUNT = 1` is also created, but it is never used.

**Step 6. Attach the dates and build the doctor key** (cross join, keep the lookback, remove rows without a BHID, create `HCP_COHORT_ID`).

**Step 7. Add up per doctor and day.** Four daily values:

* `TOTAL_USAGE_DURATION`: sum of usage duration of that day's calls.
* `TOTAL_PRESN_DURATION`: sum of presentation duration.
* `AVG_USAGE_DURATION`: average usage duration per call that day.
* `AVG_PRESN_DURATION`: average presentation duration per call that day.

**Step 8. Fill in the calendar and add up the periods** (as in section 1.3 step 9) for 30, 60, 90, 120, 150 and 180 days. All four values are **added up**, including the two averages (see 4.6).

**Step 9. Keep the last day only and save.** Keep the row for `LOOKBACK_END_DATE`, remove the daily columns, put `CLICKSTREAM_` in front of every feature, rename the day column `SVC_DT`, add `PULL_DT` (text), overwrite `kerendia_nba_3_hcp_model_clickstream_features_for_inference`. The BHID is **not** put in its own column (that step and a join with the NPI table are switched off).

### 4.4 The features explained

4 measures x 6 periods = **24 features**:

| Feature (for N = 1 to 6) | What it means |
| --- | --- |
| `CLICKSTREAM_TOTAL_USAGE_DURATION_IN_LAST_N_MONTH` | Total usage time of Kerendia tablet content in the doctor's calls in the last N x 30 days |
| `CLICKSTREAM_TOTAL_PRESN_DURATION_IN_LAST_N_MONTH` | Same, for presentation time |
| `CLICKSTREAM_AVG_USAGE_DURATION_IN_LAST_N_MONTH` | The **sum of the daily averages** of usage time (not an average over the period, see 4.6) |
| `CLICKSTREAM_AVG_PRESN_DURATION_IN_LAST_N_MONTH` | Same, for presentation time |

**Example.** In the last 30 days Dr. Rossi had calls on two days. Day 1: two calls with usage 4 and 6 (average 5). Day 2: one call with usage 10. Then total usage = 4 + 6 + 10 = 20, and "average" usage = 5 + 10 = 15 (a true average per call would be 6.7).

### 4.5 What the final table looks like

One row per doctor with at least one Kerendia CLM call in the lookback year (3,237 doctors in the saved table of 24 September 2026):

| Column | Meaning |
| --- | --- |
| `HCP_COHORT_ID` | The doctor (Bayer ID + `_I01`) |
| `SVC_DT` | The end of the lookback |
| 24 features | Above |
| `PULL_DT` | Date the notebook ran (text) |

Unlike the other tables, there is **no `BHID` column**.

### 4.6 Things to watch out for

* **The "average" features are not averages** (LK-1). Daily averages are added up over the period (example above), so they grow with the number of call days, like the totals.
* **Only the longest content per call is counted** (step 3), so total time is probably too low for calls with several pieces of content.
* **Units and definitions are not documented.** What usage and presentation duration measure, and in what unit, should be confirmed with the CLM / data team.
* **Few doctors.** Only 3,237 doctors in the saved table, against 88,511 in Sales Rep Calls, so for most doctors these features are missing (treated as 0).
* **No `BHID` column**, unlike the other tables; a later step must take it from `HCP_COHORT_ID`.
* **Unused helper column** `SUBMITTED_CALL_COUNT` (step 5): a per-period count of CLM calls was probably intended but is not produced.

---

## 5. Summary

| Channel | What it tells the model | One row is | What is counted | Periods | Number of features | Doctors (saved table) |
| --- | --- | --- | --- | --- | --- | --- |
| Sales Rep Calls | How much and what kind of rep contact the doctor had | A doctor | Calls (and minutes) | 3 months | 27 (15 + combinations that depend on the data) | 88,511 |
| BHO Calls | How much rep activity there was at the doctor's organisations | A doctor | Organisation calls, copied to every linked doctor | 1 to 6 months | 90 | 170,883 |
| iRep Emails | Does the doctor read the rep's emails | A doctor | Emails | 3 months | 14 | 17,460 |
| ClickStream / CLM | How much time was spent on tablet content during calls | A doctor | Time | 1 to 6 months | 24 | 3,237 |

**Saved tables** (all under `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/`):

| Channel | Table |
| --- | --- |
| Sales Rep Calls | `kerendia_nba_3_hcp_model_call_features_for_inference` |
| BHO Calls | `kerendia_nba_3_hcp_model_call_features_bhoid_for_inference` |
| iRep Emails | `kerendia_nba_3_hcp_model_irep_features_for_inference` |
| ClickStream / CLM | `kerendia_nba_3_hcp_model_clickstream_features_for_inference` |
