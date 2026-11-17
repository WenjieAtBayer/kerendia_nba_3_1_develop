# NBA 3.1 — FTP & Copay: can we rebuild the 3.0 features from the new claims tables?

Date: 2026-11-17. Analysis only: no notebook or table was changed.

**In one line:** yes, almost exactly — but only by copying two 3.0 mistakes (clawbacks counted twice, and a date that lets the features see the future). 3.1 should not copy them.

## Where to find things

| Item | Location |
| --- | --- |
| New FTP table | `ph-com-ai-us-prod-catalog-2553213839599380.market_access.kerendia_ftp_claims` |
| New copay table | `ph-com-ai-us-prod-catalog-2553213839599380.market_access.kerendia_copay_claims` |
| 3.0 FTP notebook (training) | `kerendia_nba_3_0_develop/NBA 3.0 Dev/08_HCP_Level_Model/03_Feature_Engineering/03_HCP_Level_Features/19_ftp_features` |
| 3.0 copay notebook (training) | same folder, `22_copay_features` |
| 3.0 FTP / copay notebooks (inference) | `kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/` (same logic, different dates) |
| 3.0 FTP output used for the comparison | volume `kerendia_nba_3_volume/hcp_level_model/dev_folder/notebook_output/kerendia_nba_3_hcp_model_ftp_features_v2.parquet` (139,264 rows, written 2025-07-28) |
| 3.0 copay output used for the comparison | volume `kerendia_nba_3_volume/hcp_level_model/dev_folder/notebook_output/kerendia_nba_3_hcp_model_copay_features.parquet` (276,533 rows, 6,431 providers, 2022-01 to 2025-07, written 2025-07-23) |
| 3.0 FTP cohort dates | volume `kerendia_nba_3_volume/hcp_level_model/dev_folder/query_output/promotional_features_hcp_model_cohort_anchor_dates.csv` (C01–C26) |
| 3.0 NPI→Bayer ID / provider list (inference) | volume `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/kerendia_nba_3_0_npi_bhid_mapping` (1,659,041 rows; columns `PROVIDER_ID`, `NPI_NUMBER`, `BH_ID`) |
| 3.0 NPI→provider list (dev export) | volume `kerendia_nba_3_volume/hcp_level_model/dev_folder/query_output/provider_npi_mapping_df.parquet` (221,723 rows) |
| Builder of the new tables | `kerendia_data_needs/Copay_FTP/02_refresh_copay_ftp` (from the table description; source `phcdw.phcdw_stg_common.stg_gtn_copay`) |
| Part 2 (new feature ideas) | `NBA_3_1_FTP_Copay_Feature_Opportunities.md` (this folder) |

**How the check was done:** every 3.0 feature was rebuilt from the new tables and compared doctor by doctor, cohort by cohort, against what 3.0 actually saved. "Verified" in this document means that comparison was run. Everything else is marked "not checked" and listed in section 7.

## Words used in this document

| Word | Meaning |
| --- | --- |
| Fill | One time a patient picked up Kerendia at the pharmacy |
| FTP | Free Trial Program: Bayer pays the full first fill(s) |
| Copay | Copay card: Bayer pays part of the patient's cost |
| Claim number | `ORGN_CLM_AUTH_NUM`: the ID of the original pharmacy claim. Corrections to a claim carry the same number |
| Source record | One row in the raw source (`stg_gtn_copay`). One fill can have several (payment, correction) |
| Reversal | The pharmacy cancels the whole claim (drug not dispensed). Already removed from the new tables |
| Clawback | The fill happened, but Bayer later took its payment back. Stays in the new tables, flagged |
| Written date | `RX_WRITTEN_DATE` / `RX_DT`: when the doctor wrote the prescription |
| Pickup date | `RX_FILL_DATE`: when the patient got the drug |
| Load date | `INSERT_TS`: when the fill arrived in the source |
| Cohort | One training example date. 3.0: C01–C26; 3.1: c1–c28 |
| Exact match | The rebuilt value equals the 3.0 value for the same doctor and cohort / month |

---

## 1. What the two new tables are

Each table is a list of pharmacy fills — every time a patient picked up Kerendia under the program (source: queries on both tables, 2026-11-17).

| | FTP (Free Trial Program) | Copay (copay card) |
| --- | --- | --- |
| What a row is | One free-trial fill | One fill where Bayer's copay card paid part |
| Fills (rows) | 105,995 | 106,029 |
| One row per original claim? | Yes (105,995 distinct claim numbers) | Yes (106,029) |
| Doctors (NPI / Bayer ID) | 16,016 / 16,008 | 9,446 / 9,442 |
| Patients | 67,891 | 19,783 |
| Fill dates | 2021-10-11 to 2026-11-06 | 2021-08-04 to 2026-11-06 |
| Prescription (written) dates | 2021-01-13 to 2026-11-06 | 2021-07-29 to 2026-11-06 |
| First fill of a prescription (new Rx) | 67,100 | 32,767 |
| Usual days of supply | 30 days (105,666 fills) | 30 days (92,213), 90 days (12,270) |
| Clawbacks | 1,328 | 7,212 (only from 2024: 1,413 / 2,754 / 3,045 in 2024 / 2025 / 2026) |
| Missing doctor (NPI / Bayer ID) | 47 / 55 | 43 / 54 |

Cancelled fills are already removed, and no fill has zero or negative days of supply.

**What a clawback is.** The patient got the drug, but Bayer later took its payment back. The fill stays in the table and is marked as clawed back; only the money is netted out. Most clawbacks (1,306 FTP, 7,203 copay) are made of two source records: the original payment and the correction that cancels it.

**Two dates per fill.** Every fill has the date the doctor wrote the prescription and the date the patient picked it up. The gap is short for FTP (12 days in the middle case) and long for copay (75 days), most likely because refills keep the date of the original prescription.

**Fills arrive late.** A fill usually lands in the table about 5 days after pickup; 95% within 14 days (FTP) / 11 days (copay); a few up to about a year later.

**FTP and copay cannot be linked per patient.** The two programs use different patient IDs (0 IDs in common). We can only see that the same doctor used both: 5,147 doctors appear in both tables.

**Doctor IDs.** Each NPI has one Bayer ID. Compared with the 3.0 NPI→Bayer ID list: FTP 15,848 same, 18 different, 145 not in the 3.0 list; copay 9,317 same, 14 different, 114 not in the list.

### 1a. More detail on the table contents

All values below are from queries on the two tables (2026-11-17).

| Column / topic | FTP | Copay |
| --- | --- | --- |
| `PROGRAM` | all `FTP` | all `COPAY` |
| `USE_SLS` / `EXCLD_CD` / `SRC_SYS_CD` | all `Y` / all `0` / all `PRM` | same |
| `GRP_NUM` (program group) | 7 values; largest 151194196WF (28,157), 171194196WF (26,319) | 3 values: 1BJEOFSFLDF (96,885), 121194196DF (7,426), 131194196DF (1,718) |
| `OTHR_CVRG_CD` (other coverage) | 00 (101,140), 03 (2,483), 01 (2,372) | 08 (87,191), 03 (18,838) |
| Largest NDCs | 50419054001 (76,466), 50419054101 (20,924) | — |
| `DAW` (dispense as written) | 0 for 102,428 | — |
| Fill number 0 / 1 / 2 | 67,100 / 21,116 / 14,791 | 32,767 / 21,822 / 16,544 (3: 10,811) |
| New Rx share | 63% | 31% (copay is used mostly for refills) |
| 90-day fills | barely any | 12,270 |
| Top specialties (`MDM_SPECIALTY`) | NEP 40,811, FM 22,240, IM 17,834, END 11,693 | NEP 40,372, FM 24,518, IM 15,579, END 14,845 |
| Average benefit Bayer paid (normal fills) | $649.51 | $393.04 |
| Average benefit after clawback | −$11.17 | −$0.52 |
| Notable missing values | `PAT_AGE` 14.95% | `PAT_AGE` 1.45%, `PRSC_MID_INT_NM` 77.63%, `PRSC_PRFSN_DSG` 76.14%, `PHMCY_ADDR_2` 96.45% |

Written→pickup gap: median 12 days FTP (90th percentile 81), 75 days copay (90th percentile 245). Pickup→load gap: median 5 days; 95th percentile 14 (FTP) / 11 (copay); maximum 371 / 385 days.

### 1b. How fills are built from source records

| Pattern | FTP | Copay | Meaning |
| --- | --- | --- | --- |
| 1 record, no correction | 104,648 | 98,742 | Normal paid fill |
| 2 records, 1 benefit correction, clawed back, net benefit $0 | 1,306 | 7,203 | Typical clawback (example below) |
| 1 record, 1 correction, clawed back | 21 | 9 | Same count as clawed fills with a negative net benefit (21 / 9); row-level link not checked |
| 2 records, no correction, not clawed back | 19 | 0 | All 19 are 2025 fills, 30 days, benefit not zero. What the second record is: not known |
| 3 records, 1 correction, clawed back, net benefit not $0 | 1 | 0 | — |
| 1 record, benefit $0, not clawed back | 0 | 75 | Bayer paid nothing (patient copay = out-of-pocket) |

### 1c. Clawback — a real example (copay table)

1. On 2026-11-05 a patient picked up a 30-day supply of Kerendia.
2. The copay card paid $711.31 (first source record).
3. Later the payment was taken back (second source record). The net is $0, so the correction is most likely −$711.31; the raw records were not checked.

| Column | Value | Meaning |
| --- | --- | --- |
| `RX_FILL_DATE` | 2026-11-05 | The pickup happened |
| `DAY_SUPPLY_NUM` | 30 | 30 days of drug |
| `N_SOURCE_ROWS` | 2 | Payment + correction |
| `PTNT_BNFT` | $711.31 | What Bayer paid at first |
| `NET_PTNT_BNFT` | $0.00 | What Bayer paid in the end |
| `IS_BENEFIT_CLAWED_BACK` | True | The payment was taken back |

Across the copay table: 7,212 clawed fills, average first payment $496.40, average net −$0.52; normal fills $393.04 (no change).

3.0 counted such a fill **twice** (one per source record). The table has no column that says *when* the clawback happened.

---

## 2. What 3.0 built

**FTP — 6 features.** How many free-trial fills each doctor had in the last 1, 2, 3, 4, 5 and 6 months (30-day steps) before each cohort date. 3.0 had 26 cohorts (C01–C26), each with a 12-month lookback ending around the 17th of a month (e.g. C01: 2022-03-17 to 2023-03-17). Only doctors with at least one FTP fill in the lookback got a row.

**Copay — 15 features.** Per doctor and calendar month: copay fills in the month, in the last 1 to 6 months, and in total since the start. Plus 7 percentage features that divide those counts by the current month. The copay amount, patient out-of-pocket and program group were loaded but not used.

Both used the same 3.0 cleaning: drop claims whose records cancel each other out completely, count every remaining record, and put each fill in the month the prescription was **written**.

Key numbers of the 3.0 outputs:

| | FTP | Copay |
| --- | --- | --- |
| Source (Snowflake) | `VIEW_RB_KERENDIA_VOUCHER_FTP` | `VIEW_RB_KERENDIA_COPAY_PROGRAM` |
| Features | 6 | 15 |
| Output rows | 139,264 (doctor × cohort, 26 cohorts) | 276,533 (provider × month, 2022-01 to 2025-07) |
| Doctors / providers | — | 6,431 |
| Last training run | 2025-07-28 | 2025-07-23 |
| Last inference run | 2025-10-08 | 2025-10-07 |

---

## 3. Can we rebuild 3.0 from the new tables? Yes, almost exactly

To match 3.0 I had to copy two of its quirks and ignore data that arrived after 3.0 ran:

1. **Count clawbacks twice.** 3.0 counted the correction record of a clawback as a second fill. Rebuilding with "one count per fill" matches worse, and removing clawbacks matches worse still. So 3.0 kept clawbacks and double-counted them.
2. **Use the prescription (written) date**, not the pickup date.
3. **Ignore late data.** Only fills that were in the source before the 3.0 run date.

### FTP result (compared with the 139,264 rows 3.0 saved)

| How it was rebuilt | Rows only in 3.0 | Rows only in rebuild | Exact match, last 1 month | Exact, 3 months | Exact, 6 months |
| --- | --- | --- | --- | --- | --- |
| One count per fill | 12 | 122 | 138,690 | 137,824 | 136,868 |
| One count per fill, clawbacks removed | 532 | 113 | 138,227 | 137,452 | 136,611 |
| Clawbacks counted twice (as 3.0) | 12 | 122 | 139,155 | 139,064 | 139,023 |
| As 3.0 + ignore late data (after 2025-07-28) | 12 | 8 | 139,246 | 139,236 | 139,224 |

* Best version: **139,224 of 139,264 rows exact (99.97%)**.
* Cohorts C01–C17 match perfectly even without ignoring late data. The newer cohorts C18–C26 differ a little, and in each of them the rebuild has more fills. Ignoring late data brings the 6-month differences from 229 rows down to 28 — so the differences come from data that arrived after 3.0 ran.

Per cohort (version "clawbacks counted twice", before ignoring late data; 6-month feature):

| Cohort | Rows | Rows different | 3.0 sum | Rebuild sum |
| --- | --- | --- | --- | --- |
| C01 | 7,255 | 0 | 19,414 | 19,414 |
| C02 | 7,128 | 0 | 16,191 | 16,191 |
| C03 | 7,207 | 0 | 12,538 | 12,538 |
| C04 | 7,316 | 0 | 10,096 | 10,096 |
| C05 | 7,291 | 0 | 9,223 | 9,223 |
| C06 | 7,212 | 0 | 8,630 | 8,630 |
| C07 | 6,990 | 0 | 7,980 | 7,980 |
| C08 | 6,841 | 0 | 7,494 | 7,494 |
| C09 | 6,583 | 0 | 7,246 | 7,246 |
| C10 | 6,298 | 0 | 6,863 | 6,863 |
| C11 | 6,139 | 0 | 6,445 | 6,445 |
| C12 | 5,976 | 0 | 6,392 | 6,392 |
| C13 | 5,483 | 0 | 5,505 | 5,505 |
| C14 | 5,164 | 0 | 4,750 | 4,750 |
| C15 | 4,782 | 0 | 4,221 | 4,221 |
| C16 | 4,515 | 0 | 3,733 | 3,733 |
| C17 | 4,355 | 0 | 3,677 | 3,677 |
| C18 | 4,166 | 1 | 3,429 | 3,431 |
| C19 | 4,027 | 4 | 3,862 | 3,867 |
| C20 | 3,869 | 7 | 4,237 | 4,245 |
| C21 | 3,668 | 12 | 4,507 | 4,521 |
| C22 | 3,514 | 19 | 4,698 | 4,726 |
| C23 | 3,393 | 24 | 4,710 | 4,744 |
| C24 | 3,223 | 37 | 4,788 | 4,845 |
| C25 | 3,368 | 51 | 4,882 | 4,962 |
| C26 | 3,489 | 74 | 4,776 | 4,888 |

The closer a cohort is to the 3.0 run date, the more late data it is missing — the pattern you expect if the only difference is late arrival.

| 3.0 feature | Rebuildable? | Exact rows (best version) |
| --- | --- | --- |
| `TOTAL_RX_FTP_IN_LAST_1_MONTH` | Yes (verified) | 139,246 |
| `TOTAL_RX_FTP_IN_LAST_2_MONTH` | Yes (verified) | 139,240 |
| `TOTAL_RX_FTP_IN_LAST_3_MONTH` | Yes (verified) | 139,236 |
| `TOTAL_RX_FTP_IN_LAST_4_MONTH` | Yes (verified) | 139,232 |
| `TOTAL_RX_FTP_IN_LAST_5_MONTH` | Yes (verified) | 139,228 |
| `TOTAL_RX_FTP_IN_LAST_6_MONTH` | Yes (verified) | 139,224 |

(A running total of FTP fills was added only in the 3.1 draft, not in 3.0. It is easy to build from the new table; nothing to compare it with.)

### Copay result (compared with 270,102 rows 3.0 saved for 2022-01 to 2025-06)

July 2025 was left out because it was only half a month when 3.0 ran. 3.0 linked doctors to IQVIA provider IDs through an IQVIA table in Snowflake that I could not reach. I tried two stand-in NPI→provider lists that 3.0 saved on the volume; the inference list matches far better, so it is used below.

| Stand-in provider list | 3.0 rows with no rebuild row | Exact month count (best version) |
| --- | --- | --- |
| Inference list `ops_pipeline/query_output/kerendia_nba_3_0_npi_bhid_mapping` | 126 | 269,552 |
| Dev export `dev_folder/query_output/provider_npi_mapping_df.parquet` | 2,688 | 266,992 |

Results with the inference list (all 270,102 rows of 3.0):

| How it was rebuilt | No rebuild row | Exact, month | 1 m | 2 m | 3 m | 4 m | 5 m | 6 m | Running total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| One count per fill | 126 | 266,458 | 266,458 | 263,715 | 261,510 | 259,787 | 258,371 | 257,202 | 252,733 |
| Clawbacks removed (earlier run) | 1,302 | 265,301 | — | — | 260,377 | — | — | 256,017 | 251,452 |
| Clawbacks counted twice (as 3.0) | 126 | 267,713 | 267,713 | 266,103 | 264,952 | 264,142 | 263,549 | 263,114 | 262,405 |
| As 3.0 + ignore late data (after 2025-07-23) | 126 | 269,552 | 269,552 | 269,216 | 268,958 | 268,761 | 268,604 | 268,480 | 268,223 |

* Best version: **269,552 of 269,976 compared rows exact (99.84%)**.
* Without ignoring late data, 2022 and 2023 match perfectly (0 of 77,136 rows differ in each year); 2024 has 446 different rows and 2025 1,817. For 2025 the new table has 16,537 copay fills vs 9,059 in 3.0, because data kept arriving after 3.0 ran.
* After ignoring late data, 424 rows still differ (109 in 2024, 315 in 2025). In **every one** of them the rebuild is higher, never lower: 523 extra fills in total (64,549 vs 64,026 in 3.0 on the compared rows). A one-sided, recent-only difference points to more late data that carries an early load date; not checked row by row.
* 126 rows of 3.0 have no rebuild row (3 of them with fills). Likely differences between the stand-in list and the IQVIA table; not checked.

| 3.0 feature | Rebuildable? | Notes |
| --- | --- | --- |
| `TOTAL_RX_COPAY` (fills in the month) | Yes (verified: 269,552 exact) | |
| `TOTAL_RX_COPAY_IN_LAST_1_MONTH` | Yes (verified: 269,552 exact) | Always the same number as the month count |
| `TOTAL_RX_COPAY_IN_LAST_2_MONTH` | Yes (verified: 269,216 exact) | |
| `TOTAL_RX_COPAY_IN_LAST_3_MONTH` | Yes (verified: 268,958 exact) | |
| `TOTAL_RX_COPAY_IN_LAST_4_MONTH` | Yes (verified: 268,761 exact) | |
| `TOTAL_RX_COPAY_IN_LAST_5_MONTH` | Yes (verified: 268,604 exact) | |
| `TOTAL_RX_COPAY_IN_LAST_6_MONTH` | Yes (verified: 268,480 exact) | |
| `RUNNING_TOTAL_RX_COPAY` | Yes (verified: 268,223 exact) | New table starts in the same month as 3.0 (July 2021) |
| `PCT_TOTAL_RX_COPAY_IN_LAST_1_MONTH` | Yes (verified: 269,940 exact) | See section 5 — recommended to drop |
| `PCT_TOTAL_RX_COPAY_IN_LAST_2_MONTH` | Yes (verified: 269,799 exact) | |
| `PCT_TOTAL_RX_COPAY_IN_LAST_3_MONTH` | Yes (verified: 269,720 exact) | |
| `PCT_TOTAL_RX_COPAY_IN_LAST_4_MONTH` | Yes (verified: 269,654 exact) | |
| `PCT_TOTAL_RX_COPAY_IN_LAST_5_MONTH` | Yes (verified: 269,608 exact) | |
| `PCT_TOTAL_RX_COPAY_IN_LAST_6_MONTH` | Yes (verified: 269,582 exact) | |
| `PCT_RUNNING_TOTAL_RX_COPAY` | Yes (verified: 269,445 exact) | |

(Percentages: "exact" = same value within 0.000000001, or both empty. Same best version.)

---

## 4. The main problem: 3.0 could see the future

3.0 put each fill in the month the prescription was **written**. Take a prescription written in May and picked up in August: 3.0 counts it in May. If you build the May features today, they include a pickup that had not happened yet in May. The model learns from information it will not have when it is used.

How big this is (source: new tables, compared with the 3.0 run dates):

| | Fills written before the 3.0 run date but picked up after it |
| --- | --- |
| FTP | 554 |
| Copay | 8,979 |

Copay is hit much harder because the gap between writing and pickup is long (75 days in the middle case vs 12 for FTP).

Why this matters for the model: in training, a cohort's features are built from today's data and include those later pickups. At inference time the later pickups have not happened yet, so the same doctor gets a lower value. The model learns on numbers it will never see in production.

It also explains part of the copay drift above: the more time passes, the more late pickups get pulled back into old months.

**Fix for 3.1:** use the pickup date and count each fill once (clawbacks counted once, not twice).

---

## 5. The copay percentage features carried almost no information

Checked on the 3.0 output: in 258,082 of 276,533 rows (93%) the doctor had no copay fill in the current month, so every percentage was empty. The 1-month percentage was always exactly 1 when it had a value. The formula is the same in all 3.0 rows (0 mismatches against "rolling sum / current month").

The percentages also behave oddly: a doctor with 6 fills over 6 months and 1 this month gets 6.0; a doctor with the same 6 fills and 0 this month gets nothing. A value grows when the current month is small, which is the opposite of what a "share" usually means.

**Recommendation:** drop all 7 percentage features in 3.1.

---

## 6. What changes in 3.1 compared with 3.0

| Topic | 3.0 | 3.1 with the new tables | Why it matters |
| --- | --- | --- | --- |
| Cancelled fills | Removed with an extra query | Already removed | Simpler |
| Clawbacks | Counted twice | Counted once, and flagged | Counts drop slightly (FTP 6-month total over all cohorts 177,912 vs 180,765) |
| Date | Prescription written | Pickup | Removes the look-into-the-future problem |
| Doctor ID | NPI matched to a 3.0 list | Bayer ID on each fill | 18 FTP / 14 copay NPIs get a different Bayer ID than in 3.0; 145 / 114 were missing from the 3.0 list |
| Time windows | FTP: own dates (~17th); copay: plain calendar months | 3.1 cohorts c1–c28 | Same windows as all other 3.1 features (see part 2) |
| Copay percentages | 7 features | Dropped | Almost always empty |

---

## 7. Not checked yet / open points

| # | Point | Background | Options | Effect |
| --- | --- | --- | --- | --- |
| 1 | Copay doctor→provider link | 3.0 used an IQVIA table in Snowflake. Two stand-in lists were tried: inference list (126 rows without a rebuild row) and dev export (2,688) | Re-run the comparison with the IQVIA table | Could close the last 0.16% gap |
| 2 | Small unexplained differences | FTP: 12 rows only in 3.0, 8 only in rebuild, 28 different values; copay: 424 rows, all higher in the rebuild (+523 fills, 2024–2025 only), 126 rows only in 3.0 | Trace a few rows by hand | Small; does not change the conclusion |
| 3 | Old Snowflake views not compared directly | The check was against what 3.0 saved, not against the old source views | Compare row counts if the views still exist | Direct confirmation of the source change |
| 4 | 19 FTP fills with two records but no clawback | All in 2025, 30 days, no benefit correction; not clear what the second record is | Ask the table owner (builder notebook `kerendia_data_needs/Copay_FTP/02_refresh_copay_ftp`, not found in workspace search) | Very small |
| 5 | When a clawback happens | The table has no clawback date; `MDFD_DT`, `DATA_DT`, `CRTD_DT` exist but were not checked | Ask the table owner | Decides if clawback information can be used as a feature in 3.1 |
| 6 | 3.0 inference outputs not compared | Only the 3.0 training outputs were compared | Repeat the check on the inference outputs | Inference used the same logic; expected to match the same way |
