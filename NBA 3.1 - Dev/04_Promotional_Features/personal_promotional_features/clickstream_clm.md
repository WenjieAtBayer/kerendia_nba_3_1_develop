# ClickStream / CLM Features — NBA 3.0 (Legacy)

**Group:** Personal promotional features (promotion that involves a sales rep)  
**Notebook:** `18_promotional_ClickStream_features` in `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Saved table:** `kerendia_nba_3_hcp_model_clickstream_features_for_inference`  
**Built from:** a review of the notebook code, plus a check of the saved table  
**Date:** October 22, 2026

## What is this document about?

Bayer uses a model called **Next Best Action (NBA)** to suggest, for each doctor, which Kerendia promotional action is most useful next. Kerendia is a Bayer medicine for chronic kidney disease in people with type 2 diabetes (and, more recently, heart failure). The model needs each doctor's recent history, turned into numbers called **features** (one fact about a doctor written as a number).

This document explains the **ClickStream / CLM** features: how long a Bayer sales representative ("rep") showed Kerendia slides on a tablet during calls with each doctor. It describes the **old version** of the pipeline (NBA 3.0); a "pipeline" is the chain of notebooks that runs one after another to prepare the data for the model.

**How it is organised:** the key ideas shared by the channels of this folder (time frame, dates table, doctor key, helper notebooks, how "last N months" is calculated) are in `00_introduction.md`. This file has: 1. In short, 2. Where the data comes from, 3. How the features are built step by step, 4. The features explained, 5. What the final table looks like, 6. Things to watch out for. Codes such as LK-1 refer to the companion legacy file; each problem is also explained here.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code. Its meaning is always given next to it.

**About the numbers.** Figures from **inside the notebook** come from the last hand run (7 October 2025). Figures about the **saved table** come from a check of the table as it is now (last saved 24 September 2026). Both will change at the next run.

---

## 1. In short

During a call, reps can show Kerendia slides and videos on a tablet. This is called **CLM** ("Closed Loop Marketing"). The tablet records how the content was used during each call; this record is the **clickstream**.

This channel adds up, for each doctor, **how much time** Kerendia tablet content was used during their calls, for six periods (1 to 6 months).

It helps the model answer: *"When the rep visits, does this doctor spend time on our material?"*

## 2. Where the data comes from

**Tables** (in Snowflake):

| Table | What one line is | Role |
| --- | --- | --- |
| `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM` | One piece of tablet content used in one call | The time measures |
| `CPH_DB_PROD.MODEL_V2.FACT_CALL` + `MAP_CUSTOMER_XREF` | One call record; the cross-reference translates the Veeva customer ID into the Bayer ID | Keeps only real, submitted Kerendia calls to doctors |

**Columns used:**

| Column | What it means |
| --- | --- |
| `CALL_ID` | The call the content was shown in. Links the two tables. |
| `BAYER_HCP_ID` | The doctor's Bayer ID. Renamed `BHID`. |
| `DATE_ID` | Day of the call, written as text `yyyyMMdd` (e.g. `20250917`) |
| `USAGE_DUR` | "Usage duration": a time measure recorded by the tablet app. The code does not define it or its unit; the name suggests how long the content was in use. |
| `PRESN_DUR` | "Presentation duration": a second time measure, probably how long the content was being presented. Not defined in the code either. |
| `BAYER_PROD_NM` | Product of the content. Used only to keep Kerendia. |
| From the calls: `STAT`, `DETL_PROD`, `BAYER_CUST_ID` | Used only to keep submitted (`SUBMITTED_VOD`) Kerendia calls to doctors (not organisations, whose IDs start with `BHO`) |

**Which lines are kept:**

* Clickstream: product is Kerendia, date is not after the end of the lookback (`SELECT DISTINCT`).
* Calls: submitted, Kerendia, doctor ID present and not `BHO`; **no date filter** (only the call ID is used).

**Size at the hand run of 7 October 2025:** 92,081 calls for 27,537 doctors (after step 4, before the lookback filter).

## 3. How the features are built, step by step

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

**Step 8. Fill in the calendar and add up the periods** for 30, 60, 90, 120, 150 and 180 days (see the introduction file, section 0.3). All four values are **added up**, including the two averages (see section 6).

**Step 9. Keep the last day only and save.** Keep the row for `LOOKBACK_END_DATE`, remove the daily columns, put `CLICKSTREAM_` in front of every feature, rename the day column `SVC_DT`, add `PULL_DT` (text), overwrite `kerendia_nba_3_hcp_model_clickstream_features_for_inference`. The BHID is **not** put in its own column (that step and a join with the NPI table are switched off).

## 4. The features explained

4 measures x 6 periods = **24 features**:

| Feature (for N = 1 to 6) | What it means |
| --- | --- |
| `CLICKSTREAM_TOTAL_USAGE_DURATION_IN_LAST_N_MONTH` | Total usage time of Kerendia tablet content in the doctor's calls in the last N x 30 days |
| `CLICKSTREAM_TOTAL_PRESN_DURATION_IN_LAST_N_MONTH` | Same, for presentation time |
| `CLICKSTREAM_AVG_USAGE_DURATION_IN_LAST_N_MONTH` | The **sum of the daily averages** of usage time (not an average over the period, see section 6) |
| `CLICKSTREAM_AVG_PRESN_DURATION_IN_LAST_N_MONTH` | Same, for presentation time |

**Example.** In the last 30 days Dr. Rossi had calls on two days. Day 1: two calls with usage 4 and 6 (average 5). Day 2: one call with usage 10. Then total usage = 4 + 6 + 10 = 20, and "average" usage = 5 + 10 = 15 (a true average per call would be 6.7).

## 5. What the final table looks like

One row per doctor with at least one Kerendia CLM call in the lookback year (3,237 doctors in the saved table of 24 September 2026):

| Column | Meaning |
| --- | --- |
| `HCP_COHORT_ID` | The doctor (Bayer ID + `_I01`) |
| `SVC_DT` | The end of the lookback |
| 24 features | Above |
| `PULL_DT` | Date the notebook ran (text) |

Unlike most other tables, there is **no `BHID` column**.

## 6. Things to watch out for

* **The "average" features are not averages** (LK-1). Daily averages are added up over the period (example above), so they grow with the number of call days, like the totals.
* **Only the longest content per call is counted** (step 3), so total time is probably too low for calls with several pieces of content.
* **Units and definitions are not documented.** What usage and presentation duration measure, and in what unit, should be confirmed with the CLM / data team.
* **Few doctors.** Only 3,237 doctors in the saved table, against 88,511 in Sales Rep Calls, so for most doctors these features are missing (treated as 0).
* **No `BHID` column**, unlike most other tables; a later step must take it from `HCP_COHORT_ID`.
* **Unused helper column** `SUBMITTED_CALL_COUNT` (step 5): a per-period count of CLM calls was probably intended but is not produced.
