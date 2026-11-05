# Market Access Promotional Features — NBA 3.0 (Legacy): Introduction

**Group:** Market access promotional features (helping patients get started on and pay for Kerendia)  
**Notebooks:** in `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Built from:** a review of the notebook code  
**Date:** October 22, 2026

## What is this folder about?

Bayer uses a model called **Next Best Action (NBA)** to suggest, for each doctor, which Kerendia promotional action is most useful next. Kerendia is a Bayer medicine for chronic kidney disease in people with type 2 diabetes (and, more recently, heart failure). The model needs each doctor's recent history, turned into numbers called **features** (one fact about a doctor written as a number).

This folder explains the **market access** features: free samples and free-trial vouchers that help patients start Kerendia. Both were previously documented with the non-personal features; they were moved here by decision of the team. It describes the **old version** of the pipeline (NBA 3.0); a "pipeline" is the chain of notebooks that runs one after another to prepare the data for the model.

**Channels in this folder (one file each):**

| Channel | Notebook | File | Saved table |
| --- | --- | --- | --- |
| Samples | `17_promotional_features_samples` | `samples.md` | `kerendia_nba_3_hcp_model_samples_features_for_inference` |
| Free Trial Program (FTP) | `19_ftp_features` | `free_trial_program_ftp.md` | `kerendia_nba_3_hcp_model_ftp_features_v2_for_inference` |

**How to read this folder.** Read this introduction first: it explains the key ideas shared by both channels (section 0). Each channel file then has: 1. In short, 2. Where the data comes from, 3. How the features are built step by step (*what*, *why*, *detail to know*), 4. The features explained, 5. What the final table looks like, 6. Things to watch out for.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code. Its meaning is always given next to it. Codes such as LS-1 or LF-2 refer to the companion legacy file; each problem is also explained in the channel file.

**About the numbers.** Figures come from the last time each notebook was run. Each channel file gives its own run date. They will be different at the next run.

---

## 0. Key ideas to understand first

### 0.1 The time frame: what period do the features cover?

The model is used on an **anchor date**. It looks back over the previous year of activity (the **lookback**), but stops about two weeks early, because recent data takes time to arrive. Example from the Samples run of 27 May 2026:

| Date | Meaning |
| --- | --- |
| 17 May 2025 | Start of the lookback period |
| 17 May 2026 | End of the lookback period (the "as of" date for every feature) |
| 1 June 2026 | Anchor date: the model makes its suggestions |
| 7 June to 7 July 2026 | The period the model tries to predict |

So every feature answers a question like *"what happened up to 17 May 2026?"*.

**Where these dates come from.** Both notebooks read a small table called `promotional_cohort_inference_dates` (saved in `ops_pipeline/notebook_output/`) and take the row for cohort `I01` (a cohort is a "snapshot" of all doctors at one anchor date; when the model is used for real there is only one, `I01`). Its columns:

| Column | Meaning | Example value |
| --- | --- | --- |
| `SERIAL_NO` | Row number | `1` |
| `ANCHOR_DATE` | The anchor date | `2026-06-01` |
| `PREDICTION_START_DATE` | First day of the prediction window | `2026-06-07` |
| `PREDICTION_END_DATE` | Last day of the prediction window | `2026-07-07` |
| `MERGE_KEY` | A helper column (always `1`) that other notebooks use to attach these dates to their tables. Not used by these notebooks. | `1` |
| `COHORT` | Cohort name | `I01` |
| `LOOKBACK_START_DATE` | First day of the lookback | `2025-05-17` |
| `LOOKBACK_END_DATE` | Last day of the lookback | `2026-05-17` |

Because each notebook was last run on a different day, the saved tables use different dates:

| Notebook | Last run | Lookback used |
| --- | --- | --- |
| Samples | 27 May 2026 | 17 May 2025 to 17 May 2026 (anchor 1 June 2026) |
| FTP | 8 October 2025 | 17 September 2024 to 17 September 2025 (anchor 1 October 2025) |

### 0.2 Things the notebooks share, and how they differ

**Shared:**

| Topic | What happens |
| --- | --- |
| Doctor key | The doctor is identified with `HCP_COHORT_ID` = BHID + `_` + cohort, for example `BH10000342_I01`. The **BHID** is Bayer's own ID for a doctor (`BH` followed by digits). In real use the cohort is always `_I01`. |
| Attaching the dates | Each notebook does a **cross join** between its data and the dates table: every row gets the lookback start and end dates written next to it. With one cohort, this does not create extra rows; it only adds the date columns. Then rows outside the lookback are removed. |
| Helper notebook `00_connection` | Run at the start. It installs the Snowflake connector (Snowflake is Bayer's central data warehouse), reads the Snowflake login (user, account and private key) from the secure secret store (`US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`), and defines `Get_Data_Snowflakes(query)`: a function that sends a SQL query to Snowflake (database `PHCDW`, schema `PHCDW_CDM`, warehouse `PROD_CYRUS_BI_WH`) and returns the result as a table. |
| Helper notebook `00_config` | Run at the start. It loads the latest approved run dates from a control table (`get_latest_approved_dates()`), shared file paths, and settings for other (patient-level and claims) feature notebooks. Both notebooks still take their dates from `promotional_cohort_inference_dates`. |
| Helper notebook `00_step23_function` | Run at the start. Its monthly functions are not used here; the daily functions (`step2_fill_missing_date`, `step3_lag_date`) are written inside each notebook (0.3). |
| Where tables are saved | As Delta tables (the Databricks table format) in `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/`. Each run **overwrites** the previous table completely, including its list of columns. |
| What happens next | A later notebook, `99_Combine_Physician_Data_Promotional&Acc`, combines all channel tables into one row per doctor for the model. |

**Differences between the notebooks:**

| | Samples | FTP |
| --- | --- | --- |
| Doctor ID in the source | BHID | **NPI** of the prescriber ("National Provider Identifier", a doctor's official 10-digit US ID), translated into the BHID with `kerendia_nba_3_0_npi_bhid_mapping` |
| Doctors kept | Only doctors in the HCP universe (`kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`, the list of doctors the model is allowed to score) | All doctors found in the NPI-to-BHID table |
| Day column in the saved table | `SVC_DT` | `MONTH_ID` (even though it is a day) |
| Separate `BHID` column | Yes | No |
| Run date `PULL_DT` | Text, like `2026_05_27` | A real date (`current_date()`) |

### 0.3 How "in the last N months" is calculated

1. **Fill in the calendar** (`step2_fill_missing_date`): for every doctor with at least one delivery or claim in the lookback, the notebook creates one row for **every day** of the lookback. Days with nothing get 0.
2. **Add up the periods** (`step3_lag_date`): for each day, it adds up that day and the days before it, for 30, 60, 90, 120, 150 and 180 days. Because there is exactly one row per day, "the last 90 rows" equals "the last 90 days". One "month" = 30 days: `_IN_LAST_1_MONTH` = last 30 days, `_3_` = 90, `_6_` = 180.
3. **Keep the last day**: only the row for the last day of the lookback is kept, so each value covers the period up to the end of the lookback.

Without step 1, "the last 90 rows" could reach back much more than 90 days.

---

## Summary of the channels

| Channel | What it tells the model | One row is | What is counted | Periods | Number of features |
| --- | --- | --- | --- | --- | --- |
| Samples | How many free samples did the doctor get, and did they ask for them? | A doctor | Units | 1 to 6 months | 54 |
| FTP | Is the doctor starting patients with free-trial vouchers? | A doctor | Voucher claims | 1 to 6 months | 6 |
