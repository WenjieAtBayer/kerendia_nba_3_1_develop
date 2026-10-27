# Speaker Program Features — NBA 3.0 (Legacy)

**Group:** Personal promotional features (promotion that involves a sales rep or a speaker in person or live)  
**Notebook:** `14_promotional_features_speaker_program` in `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Saved table:** `kerendia_nba_3_hcp_model_speaker_program_for_inference`  
**Built from:** a review of the notebook code  
**Date:** October 22, 2026

## What is this document about?

Bayer uses a model called **Next Best Action (NBA)** to suggest, for each doctor, which Kerendia promotional action is most useful next. Kerendia is a Bayer medicine for chronic kidney disease in people with type 2 diabetes (and, more recently, heart failure). The model needs each doctor's recent history, turned into numbers called **features** (one fact about a doctor written as a number).

This document explains the **Speaker Program** features: Kerendia educational events each doctor attended. Speaker programs were previously documented with the non-personal features; they now belong to the personal group. It describes the **old version** of the pipeline (NBA 3.0); a "pipeline" is the chain of notebooks that runs one after another to prepare the data for the model.

**How it is organised:** the key ideas shared by the channels of this folder (time frame, dates table, doctor key, helper notebooks, how "last N months" is calculated) are in `00_introduction.md`. This file has: 1. In short, 2. Where the data comes from, 3. How the features are built step by step (*what*, *why*, *detail to know*), 4. The features explained, 5. What the final table looks like, 6. Things to watch out for. Codes such as LSP-1 refer to the companion legacy file; each problem is also explained here.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code. Its meaning is always given next to it.

**About the numbers.** Figures come from the last time the notebook was run (4 May 2026). They will be different at the next run.

---

## 1. In short

A **speaker program** is an educational event about Kerendia where a doctor (the "speaker") presents approved slides to other doctors. It can be in person, online, or both. This channel counts **how many of these events each doctor attended**, and of which kind: in person or online, and on which topic.

A doctor who keeps attending Kerendia talks is clearly interested in learning about the medicine.

## 2. Where the data comes from

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

## 3. How the features are built, step by step

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
*What:* the labels are added up for each doctor and day, giving the 11 measures of section 4. `ATTENDED_FLAG` becomes `TOTAL_SPEAKER_PROGRAMS_ATTENDED`; the others get `TOTAL_` in front, except `SPKR_TOPIC_OTHER`, which keeps its name (LSP-3). The in-office-meal label is not added up (that line is commented out, LSP-4).

**Step 6. Fill in the calendar and add up the periods** (30, 60, 90, 120, 150, 180 days; see the introduction file, section 0.3).

**Step 7. Keep the last day only and tidy up.**
*What:* keep the row for `LOOKBACK_END_DATE`, remove the daily totals, rename the day column `SVC_DT`, put the BHID in its own column, and remove the cohort and lookback-end columns.

**Step 8. Save.**
*What:* add `PULL_DT` (text) and overwrite `kerendia_nba_3_hcp_model_speaker_program_for_inference`.

**Check cells** (they do not change the data): a check for duplicate lines and a monthly count of attending doctors.

## 4. The features explained

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

## 5. What the final table looks like

One row per doctor who attended at least one event:

| Column | Meaning |
| --- | --- |
| `HCP_COHORT_ID` | The doctor (Bayer ID + `_I01`) |
| `SVC_DT` | The end of the lookback (the "as of" date) |
| 66 features | Above |
| `BHID` | The doctor's Bayer ID |
| `PULL_DT` | Date the notebook was run |

## 6. Things to watch out for

* **The two "type" features are probably always 0** (LSP-1). The code looks for the exact text "SPEAKER PROGRAMS" (plural, capital letters), but the data says "Speaker Program" (singular, mixed case), so the texts never match.
* **The "format other" feature actually checks for a missing topic** (LSP-2). It is 1 when the presentation name is empty, whatever the format was.
* **In-office meal events are labelled but not counted** (LSP-4). The label is created in step 3, but the line that adds it up is switched off, so there is no in-office meal feature.
* **Topic lists are fixed by hand.** The names must match exactly, including the approval code. New or renamed presentations fall outside every topic group.
* **One feature name breaks the pattern** (LSP-3). `SPKR_TOPIC_OTHER_IN_LAST_...` has no `TOTAL_` at the start, unlike all the others.
