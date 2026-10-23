# Non-Personal Promotional Features — NBA 3.0 (Legacy): Introduction

**Group:** Non-personal promotional features (promotion that does not involve a sales rep)  
**Notebooks:** in `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Built from:** a review of the notebook code  
**Date:** October 22, 2026

## What is this folder about?

Bayer uses a model called **Next Best Action (NBA)** to suggest, for each doctor, which Kerendia promotional action is most useful next. Kerendia is a Bayer medicine for chronic kidney disease in people with type 2 diabetes (and, more recently, heart failure). The model needs each doctor's recent history and situation, turned into numbers called **features** (one fact about a doctor written as a number).

This folder explains the **non-personal** features: promotion that reaches doctors (or their patients) without a sales rep. It describes the **old version** of the pipeline (NBA 3.0); a "pipeline" is the chain of notebooks that runs one after another to prepare the data for the model.

**Channels in this folder (one file each):**

| Channel | Notebook | File | Saved table |
| --- | --- | --- | --- |
| Digital / Paid Media | `24_Features_Digital` | `digital_paid_media.md` | `kerendia_nba_3_0_hcp_model_paid_search_features_for_inference` |
| HQ Emails | `15_promotional_features_HQ_Emails` | `hq_emails.md` | `kerendia_nba_3_hcp_model_hq_email_features_for_inference` |
| DTC Direct Buy + Social | `34_promotional_features_DTC` | `dtc_direct_buy_social.md` | `kerendia_nba_3_hcp_model_DTC_PROMOTION_for_inference` |

Samples and the Free Trial Program are now in `market_access_promotional_features`; Speaker Programs are in `personal_promotional_features`.

**How to read this folder.** Read this introduction first: it explains the key ideas shared by all channels (section 0). Each channel file then has: 1. In short, 2. Where the data comes from, 3. How the features are built step by step (*what*, *why*, *detail to know*), 4. The features explained, 5. What the final table looks like, 6. Things to watch out for.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code. Its meaning is always given next to it. Codes such as LH-1 or LT-1 refer to the companion legacy file; each problem is also explained in the channel file.

**About the numbers.** Figures come from the last time each notebook was run. Each channel file gives its own run date. They will be different at the next run.

---

## 0. Key ideas to understand first

### 0.1 The time frame: what period do the features cover?

Imagine the model is used on **1 June 2026** (the anchor date). It looks back over the previous year of activity (the **lookback**), but stops about two weeks early, because recent data takes time to arrive:

| Date | Meaning |
| --- | --- |
| 17 May 2025 | Start of the lookback period |
| 17 May 2026 | End of the lookback period (the "as of" date for every feature) |
| 1 June 2026 | Anchor date: the model makes its suggestions |
| 7 June to 7 July 2026 | The period the model tries to predict |

So every feature answers a question like *"what happened up to 17 May 2026?"*.

**Where these dates come from.** The notebooks read a small table called `promotional_cohort_inference_dates` (saved in `ops_pipeline/notebook_output/`) and take the row for cohort `I01` (a cohort is a "snapshot" of all doctors at one anchor date; when the model is used for real there is only one, `I01`). Its columns:

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

**Which dates each notebook uses.** The three notebooks do not use the dates in the same way:

| Notebook | Dates used |
| --- | --- |
| HQ Emails | Lookback start and end: only events inside the lookback are kept. |
| Digital | Lookback start only (16 April 2025 at the last run). There is no end date, so everything up to today is kept. |
| DTC | None. The dates table is not read; every month in the input tables is kept (from January 2023). |

Because each notebook was last run on a different day, the saved tables use different dates.

### 0.2 Things the notebooks share, and how they differ

**Shared:**

| Topic | What happens |
| --- | --- |
| Doctor key (HQ Emails) | The doctor is identified with `HCP_COHORT_ID` = BHID + `_` + cohort, for example `BH10000342_I01`. The **BHID** is Bayer's own ID for a doctor (`BH` followed by digits). In real use the cohort is always `_I01`. |
| Attaching the dates (HQ Emails) | A **cross join** between the data and the dates table: every row gets the lookback start and end dates written next to it. With one cohort, this does not create extra rows; it only adds the date columns. Then rows outside the lookback are removed. |
| Helper notebook `00_connection` | Run at the start of every notebook. It installs the Snowflake connector (Snowflake is Bayer's central data warehouse), reads the Snowflake login (user, account and private key) from the secure secret store (`US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`), and defines `Get_Data_Snowflakes(query)`: a function that sends a SQL query to Snowflake (database `PHCDW`, schema `PHCDW_CDM`, warehouse `PROD_CYRUS_BI_WH`) and returns the result as a table. It also defines `sfOptionscdpread`, a second set of connection settings (schema `PHCDW_DSAA`, warehouse `PROD_DATA_SCIENCE_CYRUS_WH`) that the Digital notebook uses directly. Both reach the same Snowflake account. |
| Helper notebook `00_config` | Run by Digital and HQ Emails (not DTC). It loads the latest approved run dates from a control table (`get_latest_approved_dates()`), shared file paths, and settings for other (patient-level and claims) feature notebooks. The notebooks here still take their dates from `promotional_cohort_inference_dates`. |
| Helper notebook `00_step23_function` | Run by Digital and HQ Emails (not DTC). Defines the monthly functions `step2_fill_missing` and `step3_lag` (used by Digital) plus two variants not used here (`step3_lag_avg`, averages; `step3_lag_distinct`, distinct counts). The daily functions (`step2_fill_missing_date`, `step3_lag_date`) are written inside the HQ Emails notebook instead. |
| Run date `PULL_DT` | Added to every saved table: the date the notebook ran, stored as text like `2026_05_04`. |
| Where tables are saved | As Delta tables (the Databricks table format) in `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/`. Each run **overwrites** the previous table completely, including its list of columns. |
| What happens next | A later notebook, `99_Combine_Physician_Data_Promotional&Acc`, combines all channel tables into one row per doctor for the model. |

**Differences between the notebooks:**

| | Digital | HQ Emails | DTC |
| --- | --- | --- | --- |
| Unit of one row | A doctor in a month | A doctor | A region (DMA) in a month |
| Doctor ID | **NPI** ("National Provider Identifier", a doctor's official 10-digit US ID) | BHID, in `HCP_COHORT_ID` | None (regions are linked to doctors later) |
| Reads Snowflake with | `sfOptionscdpread` | `Get_Data_Snowflakes` | Does not read Snowflake (reads saved tables) |
| Helper notebooks run | All three | All three | `00_connection` only |
| Time totals | Monthly (0.3) | Daily, 90 days (0.3) | None |
| Unused inputs | | NPI-to-BHID table (`kerendia_nba_3_0_npi_bhid_mapping`) loaded but not used | PulsePoint and The Trade Desk tables prepared but not used |
| Last run | 29 April 2026 | 4 May 2026 | 31 July 2026 |

### 0.3 How the totals over time are calculated

**Daily notebooks (HQ Emails).**

1. **Fill in the calendar** (`step2_fill_missing_date`): for every doctor with at least one event in the lookback, the notebook creates one row for **every day** of the lookback. Days with no events get 0.
2. **Add up the last 90 days** (`step3_lag_date`): for each day, it adds up that day and the 89 days before it. Because there is exactly one row per day, "the last 90 rows" equals "the last 90 days". The result is called `<name>_IN_LAST_3_MONTH` (one "month" = 30 days).
3. **Keep the last day**: only the row for the last day of the lookback is kept, so the value covers the 90 days up to the end of the lookback.

Without step 1, "the last 90 rows" could reach back much more than 90 days.

**Monthly notebook (Digital).** Digital works with **calendar months**:

1. `step2_fill_missing` (the calendar fill): finds the first and the last month present in the data, and gives **every doctor a row for every month** in between (empty months are filled with 0 afterwards).
2. `step3_lag` (the totals): for each doctor and month it adds:
   * `<measure>_IN_LAST_<i>_MONTH` for i = 1, 3, 6: the total of that month plus the i-1 months before it. So `_IN_LAST_1_MONTH` is that month alone, and `_IN_LAST_3_MONTH` is that month plus the two before.
   * `RUNNING_<measure>`: the total of all months from the first month in the data up to that month.

Unlike the other channels, Digital keeps **every month**, not only the last one.

**Example.** Dr. Lee saw 4 banner ads in January, 0 in February and 2 in March (and the data starts in January). In her March row: that month = 2, last 3 months = 4 + 0 + 2 = 6, running total = 6. In her February row: that month = 0, running total = 4.

**DTC** builds no totals over time: each value is for one region in one month.

---

## Summary of the channels

| Channel | What it tells the model | One row is | What is counted | Periods | Number of features |
| --- | --- | --- | --- | --- | --- |
| Digital | Did the doctor see and click our online content? | A doctor in a month | Times shown / interactions | This month, 3 months, 6 months, since the start | About 684 (changes with the data) |
| HQ Emails | Does the doctor read our emails? | A doctor | Email events | 3 months | 5 |
| DTC | How much did patients in the doctor's area see our ads? | A region in a month | Ad views / clicks | That month only | 10 |
