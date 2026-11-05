# BHO (Organisation) Call Features — NBA 3.0 (Legacy)

**Group:** Personal promotional features (promotion that involves a sales rep)  
**Notebook:** `13_promotional_features_bho_calls` in `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Saved table:** `kerendia_nba_3_hcp_model_call_features_bhoid_for_inference`  
**Built from:** a review of the notebook code, plus a check of the saved table  
**Date:** October 22, 2026

## What is this document about?

Bayer uses a model called **Next Best Action (NBA)** to suggest, for each doctor, which Kerendia promotional action is most useful next. Kerendia is a Bayer medicine for chronic kidney disease in people with type 2 diabetes (and, more recently, heart failure). The model needs each doctor's recent history, turned into numbers called **features** (one fact about a doctor written as a number).

This document explains the **BHO Call** features: rep calls recorded against the doctor's organisation (practice, clinic, hospital) instead of the doctor personally. It describes the **old version** of the pipeline (NBA 3.0); a "pipeline" is the chain of notebooks that runs one after another to prepare the data for the model.

**How it is organised:** the key ideas shared by the channels of this folder (time frame, dates table, doctor key, helper notebooks, how "last N months" is calculated) are in `00_README_folder_guide.md`. This file has: 1. In short, 2. Where the data comes from, 3. How the features are built step by step, 4. The features explained, 5. What the final table looks like, 6. Things to watch out for. The labels and rules shared with the Sales Rep Calls notebook are repeated here in full, so this file can be read on its own.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code. Its meaning is always given next to it.

**About the numbers.** Figures from **inside the notebook** come from the last hand run (27 November 2025). Figures about the **saved table** come from a check of the table as it is now (last saved 24 September 2026). Both will change at the next run.

---

## 1. In short

Some rep calls are recorded not against one doctor but against an **organisation**: a practice, clinic or hospital. Organisations have their own Bayer ID starting with `BHO` (the "BHO ID"). Reps record every call in **Veeva CRM**, the software they use to plan and log their visits. These organisation calls are left out of the Sales Rep Calls features.

This notebook gives each organisation call to **every doctor linked to that organisation**, and builds the same kind of counts as Sales Rep Calls, with `BHO_` in front of every name and six periods (1 to 6 months) instead of one.

It helps the model answer: *"How much rep activity has there been at the places where this doctor works?"* It does not mean the doctor personally met the rep.

## 2. Where the data comes from

**Tables:**

| Table | What one line is | Role |
| --- | --- | --- |
| `CPH_DB_PROD.MODEL_V2.FACT_CALL` + `MAP_CUSTOMER_XREF` (Snowflake) | One call record for one product discussed; the cross-reference translates the Veeva customer ID (`SOURCE_CUST_ID`) into the Bayer ID (`BAYER_CUST_ID`) | The calls, here only for organisations |
| `kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` (saved table) | One doctor the model is allowed to score (the "HCP universe"), identified by `PROVIDER_ID` | Decides which doctors get features |
| `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING` (Unity Catalog table) | One link between `PROVIDER_ID` and `BH_ID` | Translates the universe into BHIDs |
| `PHCDW.PHCDW_STG.MDM_STG_HCP_ACCT_AFFL` (Snowflake) | One link between a doctor (`BH_ID`) and an organisation (`BHO_ID`) it is affiliated with ("MDM" = Bayer's master data on doctors and organisations) | Says which doctors belong to which organisation |

**Columns used from the calls:**

| Column | What it means | Renamed to |
| --- | --- | --- |
| `BAYER_CUST_ID` | The organisation's Bayer ID (`BHO...`) | `BHO_ID` |
| `CALL_DATE` | Day of the call | `MONTH_ID` (a day) |
| `CALL_REC_TYP_NM` | The Veeva "record type": **how** the call was held | Translated into `CHNNL_NM` (step 4) |
| `CALL_TYP` | **What kind** of call (`Detail Only`, `Detail with Sample`, `Group Detail`, `Group Detail with Sample`, `Event Detail`) | `CALL_TYP_CD` |
| `CALL_PURPS` | **Why** the call was made | `CALL_PRPSE` |
| `CALL_DUR` | Length of the call, as text (unit not stated; probably minutes) | `CALL_DURATION` |
| `STAT`, `DETL_PROD` | Status and product | Used only to filter |

**Which calls are kept:** submitted (`UPPER(STAT) = 'SUBMITTED_VOD'`), Kerendia, inside the lookback, and the Bayer ID **contains** `BHO` (the opposite of Sales Rep Calls).

**Size at the hand run of 27 November 2025:**

| Item | Number |
| --- | --- |
| Doctors in the HCP universe | 222,125 |
| Of these, found in the provider-to-BHID table | 222,051 |
| Doctor-organisation links for those doctors | 928,773 |
| Organisation calls | 376,617 |
| Rows after giving each call to every linked doctor | 30,351,434 (about 80 doctors per call) |
| Doctors who received at least one call this way | 163,233 |

## 3. How the features are built, step by step

**Step 1. Get the lookback dates** (cohort `I01`).

**Step 2. List the target doctors.** Read the HCP universe and translate `PROVIDER_ID` into BHID with an **inner join** (only doctors found in both are kept).

**Step 3. Link doctors to organisations.** Inner join with the affiliation table: one row per doctor-organisation pair. A doctor linked to 5 organisations appears 5 times.

**Step 4. Read the organisation calls and translate the record type into a channel.** The rules are **not the same** as in Sales Rep Calls:

| Record type (in capital letters) | Becomes channel | Difference from Sales Rep Calls |
| --- | --- | --- |
| Contains `BPH_FACE2FACE_SIG`, or is exactly `FACE2FACE SIGNED` | `F2F` (face-to-face) | Sales Rep Calls accepts anything starting with `FACE2FACE_SIG` |
| Contains `BPH_NON_FACE2FACE` | `PHONE` | Same |
| Exactly `BPH_GROUP_CALL_SIG` or `EVENT_VOD` | `GROUP_CALL` | `GROUP CALL SIGNED` is missing |
| Contains `BPH_REMOTE` | `REMOTE_CALL` | Same |
| Anything else | Keeps its original value; not counted in any channel feature | Same |

**Step 5. Give each call to every linked doctor.** Inner join of the calls with the doctor-organisation pairs on `BHO_ID`. A call at an organisation with 80 linked doctors becomes 80 rows, one per doctor.

**Step 6. Labels.** Each call gets a 1 (yes) or 0 (no) in each of these columns. Call type and purpose must match the text **exactly**:

| Label | Is 1 when |
| --- | --- |
| `F2F`, `PHONE`, `GROUP_CALL`, `REMOTE_CALL` | The channel from step 4 |
| `DETAIL_ONLY` | Call type is `Detail Only`: Kerendia discussed, no samples |
| `DETAIL_WITH_SAMPLE` | `Detail with Sample`: discussed and samples left |
| `GROUP_DETAIL` | `Group Detail`: discussed with several people at once |
| `GROUP_DETAIL_WITH_SAMPLE` | `Group Detail with Sample` |
| `EVENT_DETAIL` | `Event Detail`: discussed at an event |
| `CALL_PURPOSE_PROMOTIONAL_ACTIVITY` | Purpose is `Promotional Activity` |
| `CALL_PURPOSE_PROMOTIONAL_ACTIVITY_WITH_MEAL` | `Promotional Activity with meal` |
| `CALL_PURPOSE_EVENT_RELATED_PROMOTIONAL_ACTIVITY` | `Event related Promotional Activity` |
| `CALL_PURPOSE_NON_PROMOTIONAL_ACTIVITY` | `Other non-promotional Activity` |
| `CALL_PURPOSE_MISCELLANEOUS` | One of 9 other purposes: `Contract negotiation / Tender assistance`, `Technical Operation/Installation`, `Reactive Sample / HVPI`, `Market Access`, `Regulatory Compliance`, `Education / Training`, `Technical Information`, `Handover of SPC (Summary of Product Characteristics)`, `Handover of Scientific Publication / Reprint` |

**Step 7. Clean the duration.** Different from Sales Rep Calls: any duration that is not a plain number (only digits and a dot) becomes `0`, then the text is turned into a number. Empty values stay empty and are ignored when adding up.

**Step 8. Attach the dates and build the doctor key** (cross join, keep the lookback, remove rows without a BHID, create `HCP_COHORT_ID`).

**Step 9. Add up per doctor and day**, with `TOTAL_` in front of each name (15 measures: 4 channels, 5 call types, 5 purposes, duration). **No combination features** are built here.

**Step 10. Fill in the calendar and add up the periods** for 30, 60, 90, 120, 150 and 180 days (see the introduction file, section 0.3).

**Step 11. Keep the last day only and save.** Keep the row for `LOOKBACK_END_DATE`, remove the daily columns, put `BHO_` in front of every feature, rename the day column `SVC_DT`, put the BHID in its own column, add `PULL_DT` (text) and overwrite `kerendia_nba_3_hcp_model_call_features_bhoid_for_inference`.

## 4. The features explained

The 15 measures of step 9, each for 6 periods: **15 x 6 = 90 features**. The name pattern is `BHO_TOTAL_<measure>_IN_LAST_<N>_MONTH`:

| Measure | What it counts (at any of the doctor's organisations) |
| --- | --- |
| `F2F`, `PHONE`, `GROUP_CALL`, `REMOTE_CALL` | Organisation calls held face-to-face, by phone, as a group call, or remotely |
| `DETAIL_ONLY`, `DETAIL_WITH_SAMPLE`, `GROUP_DETAIL`, `GROUP_DETAIL_WITH_SAMPLE`, `EVENT_DETAIL` | Organisation calls of each call type |
| `CALL_PURPOSE_PROMOTIONAL_ACTIVITY`, `..._WITH_MEAL`, `..._EVENT_RELATED_PROMOTIONAL_ACTIVITY`, `..._NON_PROMOTIONAL_ACTIVITY`, `..._MISCELLANEOUS` | Organisation calls of each purpose |
| `CALL_DURATION` | Total recorded length of organisation calls |

Examples:

| Feature | What it means |
| --- | --- |
| `BHO_TOTAL_F2F_IN_LAST_3_MONTH` | Face-to-face calls at any of the doctor's organisations in the last 90 days |
| `BHO_TOTAL_DETAIL_WITH_SAMPLE_IN_LAST_1_MONTH` | Organisation calls with samples in the last 30 days |
| `BHO_TOTAL_CALL_PURPOSE_PROMOTIONAL_ACTIVITY_IN_LAST_6_MONTH` | Promotional organisation calls in the last 180 days |
| `BHO_TOTAL_CALL_DURATION_IN_LAST_2_MONTH` | Total length of organisation calls in the last 60 days |

How to interpret them: the **amount of rep activity around the doctor**, not contact with the doctor personally.

**Example.** Dr. Kim is linked to two organisations, Clinic A and Hospital B. In the last 30 days a rep made 2 face-to-face calls at Clinic A and 1 at Hospital B. Then `BHO_TOTAL_F2F_IN_LAST_1_MONTH` = 3 for Dr. Kim, and also 2 for every other doctor of Clinic A, even those who were not there.

## 5. What the final table looks like

One row per universe doctor linked to an organisation with at least one call in the lookback year (170,883 doctors in the saved table of 24 September 2026):

| Column | Meaning |
| --- | --- |
| `HCP_COHORT_ID` | The doctor (Bayer ID + `_I01`) |
| `SVC_DT` | The end of the lookback |
| 90 features | Above |
| `BHID` | The doctor's Bayer ID |
| `PULL_DT` | Date the notebook ran (text) |

## 6. Things to watch out for

* **One call is counted for many doctors.** Each organisation call is copied to every linked doctor (about 80 on average). Totals are therefore very large: in the saved table, 6.2 million face-to-face "calls" in the last 3 months, against about 100,000 in the personal Sales Rep Calls table.
* **Doctors linked to several organisations collect calls from all of them.**
* **Group calls are always 0.** The group rule is missing `GROUP CALL SIGNED` (probably the reason), and the face-to-face rule is stricter than in Sales Rep Calls, so the same call can be classified differently in the two notebooks. In the saved table, phone, group call, detail with sample and event detail are 0 for every doctor.
* **Only doctors in the HCP universe are included** (steps 2 and 3).
* **No combination features.** An earlier version of the documentation said the channel-and-call-type combinations of Sales Rep Calls were also built here; the code does not do this.
* **Different duration cleaning** from Sales Rep Calls (step 7), so the two duration features are not calculated the same way.
* **Exact text matching.** Call types and purposes must match exactly; new or differently written values are counted in no feature of that group.
