# Personal Promotional Features (Field Activity): Folder Guide and Introduction

**Group:** Personal promotional features (promotion that involves a sales rep, or a speaker in person or live)  
**Notebooks:** in `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Built from:** a review of the notebook code, plus a check of the saved tables  
**Date:** October 22, 2026

## What is this folder about?

Bayer uses a model called **Next Best Action (NBA)** to suggest, for each doctor, which Kerendia promotional action is most useful next. Kerendia is a Bayer medicine for chronic kidney disease in people with type 2 diabetes (and, more recently, heart failure). The model needs each doctor's recent history, turned into numbers called **features** (one fact about a doctor written as a number).

This folder explains the **personal** features: promotion delivered by people, mainly Bayer sales representatives ("reps") who visit, call and email doctors, and speaker programs where a doctor presents to other doctors. Reps record their work in **Veeva CRM**, the software they use to plan and log their visits; values ending in `_vod` come from Veeva. It describes the **old version** of the pipeline (NBA 3.0); a "pipeline" is the chain of notebooks that runs one after another to prepare the data for the model.

**Channels in this folder (one file each):**

| Channel | Notebook | File | Saved table |
| --- | --- | --- | --- |
| Sales Rep Calls | `25_promotional_features_call` | `10_sales_rep_calls_nba_3_0.md` | `kerendia_nba_3_hcp_model_call_features_for_inference` |
| BHO (organisation) Calls | `13_promotional_features_bho_calls` | `11_bho_calls_nba_3_0.md` | `kerendia_nba_3_hcp_model_call_features_bhoid_for_inference` |
| iRep Emails | `16_promotional_features_irep` | `12_irep_emails_nba_3_0.md` | `kerendia_nba_3_hcp_model_irep_features_for_inference` |
| ClickStream / CLM | `18_promotional_ClickStream_features` | `13_clickstream_clm_nba_3_0.md` | `kerendia_nba_3_hcp_model_clickstream_features_for_inference` |
| Speaker Programs | `14_promotional_features_speaker_program` | `14_speaker_programs_nba_3_0.md` | `kerendia_nba_3_hcp_model_speaker_program_for_inference` |

**Files in this folder (numbered so they sort in reading order):**

| Range | Purpose | Files |
| --- | --- | --- |
| `00` | This guide, and the key ideas shared by all channels (section 0) | `00_README_folder_guide.md` |
| `10` – `14` | How each NBA 3.0 channel's features are built (legacy, from the notebook code) | `10_sales_rep_calls_nba_3_0.md`, `11_bho_calls_nba_3_0.md`, `12_irep_emails_nba_3_0.md`, `13_clickstream_clm_nba_3_0.md`, `14_speaker_programs_nba_3_0.md` |
| `20` – `29` | Data reviews of the last two years (Nov 2024 – Oct 2026), with trends, gaps and open questions for NBA 3.1 | `20_field_activity_data_review_2024_2026.md` (calls, BHO, iRep, speaker programs, plus unused Veeva tables), `21_clickstream_clm_data_review_2024_2026.md` (CLM / iVA) |
| `30` – `39` | Briefings for partner teams (plain-language summary of current state and NBA 3.1 proposals, with questions and an answers table) | `30_field_analytics_team_briefing_nba_3_1.md` (Field Analytics team, meeting 29 Oct 2026) |

Files were renamed on 28 October 2026 (old names: `00_introduction.md`, `sales_rep_calls.md`, `bho_calls.md`, `irep_emails.md`, `clickstream_clm.md`, `speaker_programs.md`, `clickstream_clm_data_review_2024_2026.md`).

Speaker Programs were previously documented with the non-personal features; they were moved here by decision of the team.

**How to read this folder.** Read this introduction first: it explains the key ideas shared by all channels (section 0). Each channel file then has: 1. In short, 2. Where the data comes from, 3. How the features are built step by step, 4. The features explained, 5. What the final table looks like, 6. Things to watch out for.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code. Its meaning is always given next to it. Codes such as LK-1 or LSP-1 refer to the companion legacy file; each problem is also explained in the channel file.

**About the numbers.** Figures from **inside a notebook** come from its last hand run; figures about a **saved table** come from a check of the table as it is now. Each channel file says which is which. They will change at the next run.

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
| `MERGE_KEY` | A helper column (always `1`) that other notebooks use to attach these dates to their tables. Not used by these notebooks. | `1` |
| `COHORT` | Cohort name | `I01` |
| `LOOKBACK_START_DATE` | First day of the lookback | `2025-09-16` |
| `LOOKBACK_END_DATE` | Last day of the lookback | `2026-09-16` |

**Run dates.** The saved tables were last built at different times, and the hand runs whose figures appear inside the notebooks used older dates:

| Notebook | Saved table last built | Last hand run (figures in the notebook) |
| --- | --- | --- |
| Sales Rep Calls | 24 September 2026 (lookback to 16 September 2026) | 29 July 2026 (lookback 17 July 2025 to 17 July 2026) |
| BHO Calls | 24 September 2026 | 27 November 2025 (lookback 16 November 2024 to 16 November 2025) |
| iRep Emails | 24 September 2026 | 4 May 2026 |
| ClickStream / CLM | 24 September 2026 | 7 October 2025 (lookback 17 September 2024 to 17 September 2025) |
| Speaker Programs | | 4 May 2026 |

### 0.2 Things the notebooks share, and how they differ

**Shared:**

| Topic | What happens |
| --- | --- |
| Doctor key | The doctor is identified with `HCP_COHORT_ID` = BHID + `_` + cohort, for example `BH10000342_I01`. The **BHID** is Bayer's own ID for a doctor (`BH` followed by digits). Organisations have their own Bayer ID starting with `BHO`. In real use the cohort is always `_I01`. |
| Attaching the dates | Each notebook does a **cross join** between its data and the dates table: every row gets the lookback start and end dates (and the cohort name) written next to it. Then rows outside the lookback are removed. The notebooks do **not** first keep only `I01`: with one row in the dates table nothing is duplicated, but if the table holds several cohorts, every row is copied once per cohort (this happened in one iRep run). |
| Helper notebook `00_connection` | Run at the start of every notebook. It installs the Snowflake connector (Snowflake is Bayer's central data warehouse), reads the Snowflake login (user, account and private key) from the secure secret store (`US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`), and defines `Get_Data_Snowflakes(query)`: a function that sends a SQL query to Snowflake and returns the result as a table. |
| Helper notebook `00_step23_function` | Run at the start of every notebook. Its monthly functions are not used; each notebook writes its own daily versions of the calendar fill and the period totals (0.3). |
| Unused input | Every notebook loads the NPI-to-BHID translation table (`kerendia_nba_3_0_npi_bhid_mapping`; NPI is a doctor's official US ID) but none uses it, because the data already carries the BHID. |
| Where tables are saved | As Delta tables (the Databricks table format) in `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/`. Each run **overwrites** the previous table completely, including its list of columns. |
| Which doctors appear | A doctor appears only if they had at least one activity of that channel **during the whole lookback year**. Others are missing and are treated as 0 later. Because some features only look at the last 90 days, many doctors can appear with all features 0. |
| What happens next | A later notebook, `99_Combine_Physician_Data_Promotional&Acc`, combines all channel tables into one row per doctor for the model. |

**Differences between the notebooks:**

| | Sales Rep Calls | BHO Calls | iRep Emails | ClickStream / CLM | Speaker Programs |
| --- | --- | --- | --- | --- | --- |
| `00_config` run | Yes | No | No | No | Yes |
| Periods | 90 days only | 1 to 6 months | 90 days only | 1 to 6 months | 1 to 6 months |
| Feature prefix | None | `BHO_` | None | `CLICKSTREAM_` | None |
| Calendar fill function | `step2_fill_missing_dates` | `step2_fill_missing_dates` | `step2_fill_missing_date` | `step2_fill_missing_dates` | `step2_fill_missing_date` |
| Separate `BHID` column | Yes | Yes | Yes | **No** | Yes |
| Run date `PULL_DT` | A real date | Text (`2026_09_24`) | Text | Text | Text |
| Extra inputs | | HCP universe, provider-to-BHID table, doctor-organisation links | | Submitted calls (to keep valid call IDs) | |

(`00_config` loads the latest approved run dates from a control table, `get_latest_approved_dates()`, plus shared file paths and settings for other feature notebooks. The notebooks still take their dates from `promotional_cohort_inference_dates`.)

### 0.3 How "in the last N months" is calculated

1. **Fill in the calendar**: for every doctor with at least one activity in the lookback, the notebook creates one row for **every day** of the lookback. Days with nothing get 0.
2. **Add up the periods** (`step3_lag_date`): for each day, it **adds up** that day and the days before it, for 90 days only (Sales Rep Calls, iRep Emails) or for 30, 60, 90, 120, 150 and 180 days (BHO Calls, ClickStream, Speaker Programs). Because there is exactly one row per day, "the last 90 rows" equals "the last 90 days". One "month" = 30 days: `_IN_LAST_1_MONTH` = last 30 days, `_3_` = 90, `_6_` = 180.
3. **Keep the last day**: only the row for the last day of the lookback is kept, so each value covers the period up to the end of the lookback.

Without step 1, "the last 90 rows" could reach back much more than 90 days. Step 2 always adds up, even for columns that are daily averages (ClickStream, see its file).

---

## Summary of the channels

| Channel | What it tells the model | One row is | What is counted | Periods | Number of features |
| --- | --- | --- | --- | --- | --- |
| Sales Rep Calls | How much rep contact has the doctor had, and of what kind? | A doctor | Calls (and call length) | 3 months | 27 in the saved table (changes with the data; up to 35) |
| BHO Calls | How much rep activity at the doctor's organisations? | A doctor | Organisation calls | 1 to 6 months | 90 |
| iRep Emails | Does the doctor read the rep's emails? | A doctor | Emails | 3 months | 14 |
| ClickStream / CLM | Does the doctor spend time on the rep's tablet material? | A doctor | Time | 1 to 6 months | 24 |
| Speaker Programs | Does the doctor attend our educational talks? | A doctor | Events attended | 1 to 6 months | 66 |
