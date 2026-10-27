# Sales Rep Call Features — NBA 3.0 (Legacy)

**Group:** Personal promotional features (promotion that involves a sales rep)  
**Notebook:** `25_promotional_features_call` in `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Saved table:** `kerendia_nba_3_hcp_model_call_features_for_inference`  
**Built from:** a review of the notebook code, plus a check of the saved table  
**Date:** October 22, 2026

## What is this document about?

Bayer uses a model called **Next Best Action (NBA)** to suggest, for each doctor, which Kerendia promotional action is most useful next. Kerendia is a Bayer medicine for chronic kidney disease in people with type 2 diabetes (and, more recently, heart failure). The model needs each doctor's recent history, turned into numbers called **features** (one fact about a doctor written as a number).

This document explains the **Sales Rep Call** features: visits a Bayer sales representative ("rep") made to each doctor. It describes the **old version** of the pipeline (NBA 3.0); a "pipeline" is the chain of notebooks that runs one after another to prepare the data for the model.

**How it is organised:** the key ideas shared by the channels of this folder (time frame, dates table, doctor key, helper notebooks, how "last N months" is calculated) are in `00_introduction.md`. This file has: 1. In short, 2. Where the data comes from, 3. How the features are built step by step (*what*, *why*, *detail to know*), 4. The features explained, 5. What the final table looks like, 6. Things to watch out for.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code. Its meaning is always given next to it.

**About the numbers.** Figures from **inside the notebook** come from the last hand run (29 July 2026). Figures about the **saved table** come from a check of the table as it is now (last saved 24 September 2026). Both will change at the next run.

---

## 1. In short

A **call** is a contact between a Bayer rep and a doctor to talk about Kerendia ("detailing" = presenting a product to a doctor). Reps record every call in **Veeva CRM**, the software they use to plan and log their visits. Values ending in `_vod` come from Veeva.

This channel counts, for each doctor, how many Kerendia calls they received in the **last 3 months**, broken down by **how** the call was held (in person, phone, remote, group), **what kind** of call it was (with or without samples), **why** it was made (its purpose), and how long the calls lasted.

It helps the model answer: *"How much rep contact has this doctor had recently, and of what kind?"*

## 2. Where the data comes from

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
* The Bayer ID exists and does **not** contain `BHO` (calls to organisations go to the BHO Calls notebook).
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

## 3. How the features are built, step by step

**Step 1. Get the lookback dates** (cohort `I01`; see the introduction file).

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

**Step 6. Attach the dates and build the doctor key** (cross join with the dates table, keep calls inside the lookback, remove rows without a BHID, create `HCP_COHORT_ID`; see the introduction file).

**Step 7. Add up per doctor and day.** For each doctor and day, the labels and the duration are added up, and `TOTAL_` is put in front of each name (e.g. `TOTAL_F2F` = number of face-to-face calls that day).

**Step 8. Build the "channel and call type" combinations.**
*What:* for every channel and every call type found in the data, a combined column is created: `TOTAL_<channel>_AND_<call type>`, for example `TOTAL_F2F_AND_DETAIL_ONLY`. Its value is the **smaller** of the two daily totals (`least()`).
*Which combinations:* the lists of channels and call types are read from the data at run time, leaving out `Do not select` and `Face2Face KAM Call`. So the number of combinations depends on which values exist (see section 6).
*Why the smaller number:* the daily totals no longer say which call had which type, so the smaller number is used as an estimate of "calls that were both". It is exact when a doctor had only one kind of call that day, but can be too high otherwise (example in section 6).

**Step 9. Fill in the calendar and add up the last 90 days.**
*What:* for every doctor with at least one call in the lookback, the notebook creates one row for **every day** of the lookback (`step2_fill_missing_dates`); days without calls get 0. Then, for each day, it adds up that day and the 89 days before it (`step3_lag_date` with the single period 90 days). Because there is exactly one row per day, "the last 90 rows" equals "the last 90 days". The new column is called `<name>_IN_LAST_3_MONTH` (one "month" = 30 days).
*Why:* without the empty days, "the last 90 rows" could reach back much more than 90 days.

**Step 10. Keep the last day only and save.**
*What:* keep only the row for the last day of the lookback (`LOOKBACK_END_DATE`), remove the daily columns, rename the day column `SVC_DT`, take the BHID out of `HCP_COHORT_ID` into its own column, add `PULL_DT` as a real date (`current_date()`), and overwrite `kerendia_nba_3_hcp_model_call_features_for_inference`.

**Check cell** (does not change the data): a count of empty values per column (all 0 at the last hand run).

## 4. The features explained

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

## 5. What the final table looks like

One row per doctor with at least one Kerendia call in the lookback year (88,511 doctors in the saved table of 24 September 2026):

| Column | Meaning |
| --- | --- |
| `HCP_COHORT_ID` | The doctor (Bayer ID + `_I01`) |
| `SVC_DT` | The end of the lookback (the "as of" date) |
| 27 features | Above |
| `BHID` | The doctor's Bayer ID |
| `PULL_DT` | Date the notebook ran (a real date, not text as in most other channels) |

## 6. Things to watch out for

* **The combinations are an estimate and can be too high.** They use the smaller of two daily totals. Example: one day Dr. Garcia had 1 face-to-face call with only discussion (detail only) and 1 remote group discussion. Face-to-face = 1 and group detail = 1, so `TOTAL_F2F_AND_GROUP_DETAIL` = 1, although she had no face-to-face group discussion.
* **The number of combination features changes with the data.** The lists are read from the data each run: 16 columns on 29 July 2026, 12 on 24 September 2026. The model expects a fixed list of columns.
* **The notebook can stop with an error when a new value appears.** If the data contains a new record type or call type, the combination step looks for a `TOTAL_...` column that was never created, and the run fails. Only `Do not select` and `Face2Face KAM Call` are excluded by hand.
* **Exact text matching.** Call types and purposes must match exactly; a call with a new or differently written purpose is counted in no purpose feature.
* **Some channels and types are always 0 right now.** Phone and event detail are 0 for every doctor in the saved table.
* **Duration is loosely handled.** The unit is not stated, the text is converted to a number automatically, and calls without a recorded length add nothing.
* **Many doctors are all zeros.** 46,250 of the 88,511 doctors had calls earlier in the year but none in the last 90 days.
* **Only a 3-month period exists.**
* **`PULL_DT` has a different type** (date) from most other tables (text).
