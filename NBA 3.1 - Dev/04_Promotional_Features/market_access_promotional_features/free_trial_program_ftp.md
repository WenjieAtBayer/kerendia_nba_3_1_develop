# Free Trial Program (FTP) Features — NBA 3.0 (Legacy)

**Group:** Market access promotional features (helping patients get started on and pay for Kerendia)  
**Notebook:** `19_ftp_features` in `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Saved table:** `kerendia_nba_3_hcp_model_ftp_features_v2_for_inference`  
**Built from:** a review of the notebook code  
**Date:** October 22, 2026

## What is this document about?

Bayer uses a model called **Next Best Action (NBA)** to suggest, for each doctor, which Kerendia promotional action is most useful next. Kerendia is a Bayer medicine for chronic kidney disease in people with type 2 diabetes (and, more recently, heart failure). The model needs each doctor's recent history, turned into numbers called **features** (one fact about a doctor written as a number).

This document explains the **Free Trial Program (FTP)** features: how many free-trial vouchers were used on each doctor's prescriptions. FTP was previously documented with the non-personal features; it now belongs to the market access group. It describes the **old version** of the pipeline (NBA 3.0); a "pipeline" is the chain of notebooks that runs one after another to prepare the data for the model.

**How it is organised:** the key ideas shared by the channels of this folder (time frame, dates table, doctor key, helper notebooks, how "last N months" is calculated) are in `00_introduction.md`. This file has: 1. In short, 2. Where the data comes from, 3. How the features are built step by step (*what*, *why*, *detail to know*), 4. The features explained, 5. What the final table looks like, 6. Things to watch out for. Codes such as LF-2 refer to the companion legacy file; each problem is also explained here.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code. Its meaning is always given next to it.

**About the numbers.** Figures come from the last time the notebook was run (8 October 2025). They will be different at the next run.

---

## 1. In short

The **Free Trial Program (FTP)** gives patients their first supply of Kerendia **for free**, using a voucher. Each time a patient uses a voucher at the pharmacy, a "claim" is recorded, together with the doctor who wrote the prescription.

This channel counts **how many free-trial vouchers were used on each doctor's prescriptions**. Many vouchers usually means the doctor is starting new patients on Kerendia.

## 2. Where the data comes from

**Table:** `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP` in Snowflake, read with `Get_Data_Snowflakes`.

**One line of the table** = one claim transaction: an approval, or a cancellation ("reversal") of an earlier claim.

**Columns used:**

| Column | What it means |
| --- | --- |
| `PRSC_NPI` | The NPI of the prescribing doctor. Renamed `NPI_NUMBER`. |
| `RX_DT` | The prescription date. Converted to a date and used as the event day (saved as `SVC_DT_M`, later renamed `MONTH_ID`, even though it is a day, not a month). |
| `CLM_AUTH_NUM` | The authorisation number of this one claim transaction. |
| `ORGN_CLM_AUTH_NUM` | The number of the **original** claim. A claim and every later cancellation or re-approval of it share this number. |
| `DAY_SUPPLY` | How many days of medicine the claim covers. A cancellation has a negative value. Used only to find cancelled claims (step 2). |
| `USE_SLS` | Whether the line may be used for sales reporting (`Y` = yes). |

**Which lines are kept:**

* The prescriber NPI is not empty.
* `USE_SLS = 'Y'`.
* There is no date filter in the query; the lookback is applied in step 4.

**Dates at the last run (8 October 2025):** claims from 13 January 2021 to 29 September 2025.

**How a cancellation looks.** Sometimes a claim is cancelled (for example because the patient never collected the medicine). The cancellation is an extra line with negative quantities and the same `ORGN_CLM_AUTH_NUM`:

| Line | `ORGN_CLM_AUTH_NUM` | `DAY_SUPPLY` |
| --- | --- | --- |
| Approval | 111 | 30 |
| Cancellation | 111 | -30 |
| **Total for 111** | | **0**: the patient did not get the medicine |

If the claim was then approved again, a third line (+30) makes the total 30 again.

## 3. How the features are built, step by step

**Step 1. Get the lookback dates** (cohort `I01`).

**Step 2. Read the claims and remove cancelled ones.**
*What:* a second query adds up `DAY_SUPPLY` per original claim number. Claim numbers whose total is **0** (approved and then fully cancelled) are collected into a list, and all their lines are removed from the claims. Claim numbers with a positive total are kept **with all their lines** (approval, cancellation and re-approval).
*Why:* a fully cancelled claim means the patient did not start therapy.
*Detail to know:* the list of cancelled claims is first copied from Spark (the data-processing tool) into the memory of the main computer (`toPandas()`) and then used as a filter (`isin`). This works for small lists but may become slow or fail as the list grows (LF-4).

**Step 3. Translate NPI to BHID.**
*What:* an **inner join** with the NPI-to-BHID mapping (`kerendia_nba_3_0_npi_bhid_mapping`). Claims whose NPI has no BHID are removed. If one NPI has several BHIDs, the claim is copied once for each (LF-5).
*Size after this step:* 96,231 lines for 13,388 doctors. Some doctor IDs are not in the usual `BH...` form (for example `31403984`).

**Step 4. Attach the dates and build the doctor key** (cross join, keep claims inside the lookback, remove empty BHIDs, create `HCP_COHORT_ID`).

**Step 5. Count claims per doctor and day.**
*What:* the number of lines for each doctor and day becomes `TOTAL_RX_FTP` ("total prescriptions with free trial").

**Step 6. Fill in the calendar and add up the periods** (30, 60, 90, 120, 150, 180 days; see the introduction file, section 0.3), then keep the row for `LOOKBACK_END_DATE`.

**Step 7. Tidy up.**
*What:* a list of columns to keep (`keep_cols`) is applied. It contains `LOOKBACK_END_MONTH`, a misspelling of `LOOKBACK_END_DATE` (LF-2), so the lookback end column is removed together with the daily count. Unlike the other daily notebooks, the day column is **not** renamed to `SVC_DT` (it stays `MONTH_ID`) and the BHID is **not** put in its own column.

**Step 8. Save.**
*What:* add `PULL_DT` as a real date (`current_date()`, not text) and overwrite `kerendia_nba_3_hcp_model_ftp_features_v2_for_inference`. The save cell appears twice in the notebook; running both gives the same result.

## 4. The features explained

One measure for 6 periods = **6 features**:

| Feature | What it means |
| --- | --- |
| `TOTAL_RX_FTP_IN_LAST_1_MONTH` | Number of free-trial voucher claims on this doctor's prescriptions in the last 30 days |
| `TOTAL_RX_FTP_IN_LAST_2_MONTH` | Same, last 60 days |
| `TOTAL_RX_FTP_IN_LAST_3_MONTH` | Same, last 90 days |
| `TOTAL_RX_FTP_IN_LAST_4_MONTH` | Same, last 120 days |
| `TOTAL_RX_FTP_IN_LAST_5_MONTH` | Same, last 150 days |
| `TOTAL_RX_FTP_IN_LAST_6_MONTH` | Same, last 180 days |

How to interpret it: roughly, **how many patients this doctor started on Kerendia with a free trial** recently. It counts claim **lines**, not patients: a claim that was cancelled and approved again keeps all three lines (step 2), so it counts 3.

**Example.** Three of Dr. Novak's patients used a free-trial voucher in the last 2 months, and one more about 135 days ago. If one of the three was in the last 30 days, her features are: last 1 month = 1, last 2 months = 3, last 3 and 4 months = 3, last 5 and 6 months = 4.

## 5. What the final table looks like

One row per doctor with at least one voucher claim in the lookback:

| Column | Meaning |
| --- | --- |
| `HCP_COHORT_ID` | The doctor (Bayer ID + `_I01`) |
| `MONTH_ID` | The end of the lookback (other channels call this `SVC_DT`) |
| 6 features | Above |
| `PULL_DT` | Date the notebook was run (stored as a date, not as text like most others) |

Unlike most other doctor tables, there is no separate `BHID` column.

## 6. Things to watch out for

* **A claim that was cancelled and then approved again counts more than once**, because all its lines are kept (step 2).
* **One prescriber number can match several Bayer IDs** (LF-5), so the same claim can be counted for more than one doctor.
* **Some doctor IDs do not look like normal Bayer IDs** (e.g. `31403984` instead of `BH...`). They come from the mapping table and may not match other channels.
* **The saved table is old.** It was last built on 8 October 2025 (lookback ending 17 September 2025), much earlier than the other channels, so its features describe an older period.
* **Misspelled column name** (LF-2). `LOOKBACK_END_MONTH` in the keep list should be `LOOKBACK_END_DATE`; as a result the lookback end date is missing from the table.
* **Cancelled-claim list is loaded into memory** (LF-4). This may become slow or fail when the list grows.
* **Different column names from the other doctor tables.** The date is `MONTH_ID` (not `SVC_DT`), there is no `BHID` column, and `PULL_DT` is a date (not text). A later step must handle these differences.
