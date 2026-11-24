# NBA 3.1 – Lab data learnings and NBA 3.0 lab review

**Date:** 2026-11-23  
**Purpose:** first section of the NBA 3.1 Lab readiness plan. What the lab source holds today, what we learned from profiling it, and how NBA 3.0 used lab data.  
**Related docs (not repeated here):** `Lab Files/NBA_3_1_Lab_Journey_Plan.md` (PJ01 3.0 -> 3.1 changes), `hcp_level_features/02 Lab Claims Files/NBA_3_1_Lab_Claims_Features_Plan.md` (NB02), `Product_Group_Mapping/NBA_3_1_Feature_Code_Recommendations.md` and `NBA all Codes analysis.md` (code triage), `Combine Files/NBA_3_1_E2E_Full_Run_2026_11_02.md` (B1).

---

## 1. Decisions and pending items

| # | Item | Status |
| --- | --- | --- |
| S1 | **Lab source for NBA 3.1 = `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_QUEST_TO_LAAD_HIST` only** (Quest `LAB_IDENTIFIER = 'Q'` + LabCorp `'P'`). Do not union `..._QUEST_TO_LAAD_FULL` (it holds fewer LabCorp rows than HIST in every month checked, see 2.3) | Confirmed 2026-11-23 |
| S2 | **Second LabCorp file from Prognos.** Prognos sends two LabCorp files each time: (1) a tokenized file (LabCorp records tokenized to the LAAD patient ID) – this is what the HIST `'P'` rows hold; (2) a full file with all LabCorp records. File (2) is still being chased | Pending (Phase B source). When it arrives: profile overlap with HIST, patient-matching rate, and duplicates before use |
| S3 | **Duplicate loads in HIST** (section 3): history reload of 2025-03-06/07 was appended on top of the original monthly loads | Open: agree a dedup rule; confirm with PHCDW whether the reload was meant to replace the original loads |

---

## 2. What the lab source holds today

### 2.1 HIST by year and lab (all rows as stored, before dedup)

| Year | Lab | Rows | Rows without patient ID | eGFR rows | UACR rows | Potassium rows | HbA1c rows |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2021 | Quest | 144,927,096 | 0 | 137,247,140 | 7,394,619 | 0 | 0 |
| 2022 | Quest | 245,777,101 | 0 | 225,627,105 | 17,778,677 | 0 | 0 |
| 2023 | Quest | 176,771,513 | 0 | 154,047,761 | 19,892,406 | 0 | 0 |
| 2024 | Quest | 188,835,975 | 0 | 163,187,271 | 23,133,648 | 0 | 0 |
| 2025 | Quest | 73,450,367 | 0 | 60,292,728 | 12,141,660 | 0 | 0 |
| 2026 (to Sep) | Quest | 66,727,862 | 0 | 43,511,045 | 22,674,845 | 0 | 0 |
| 2021 | LabCorp | 108,627,900 | 60,519,638 | 41,819,854 | 6,821,084 | 30,733,505 | 29,253,457 |
| 2022 | LabCorp | 340,557,893 | 194,895,655 | 86,669,275 | 21,395,257 | 88,779,744 | 85,886,224 |
| 2023 | LabCorp | 408,823,989 | 238,050,924 | 126,469,071 | 27,012,492 | 99,223,927 | 100,422,801 |
| 2024 | LabCorp | 639,697,969 | 378,201,309 | 219,107,315 | 37,144,294 | 216,886,615 | 166,288,930 |
| 2025 | LabCorp | 199,700,978 | 65,123,684 | 59,533,442 | 13,448,525 | 70,971,543 | 43,626,956 |
| 2026 (to Oct) | LabCorp | 140,622,952 | 0 | 51,274,721 | 10,752,631 | 50,491,192 | 28,104,408 |

Test families counted by LOINC: eGFR = 98979-8, 50210-4, 48642-3, 62238-1, 88293-6, 88294-4, 98980-6, 33914-3; UACR = 9318-7, 14957-5, 2161-8, 1754-1, 14958-3, 35674-1, 14683-7 (includes UACR components); potassium = 2823-3; HbA1c = 4548-4. A few LabCorp rows have invalid months (null, `101`, `2001`; 65 rows in total).

**Do not read the 2024 -> 2025 fall as a real drop.** Most of it is duplicate loads (section 3).

### 2.2 Learnings

* **L-A. LabCorp is the only source of potassium and HbA1c.** Quest has 0 rows for both in every year. Any Phase B potassium (Kerendia hyperkalemia monitoring) or HbA1c feature depends fully on LabCorp.
* **L-B. LabCorp is now the larger eGFR source.** 2026: LabCorp 51.3M eGFR rows vs Quest 43.5M.
* **L-C. LabCorp patient matching changed in mid-2025.** Rows without a patient ID: 56–59% of LabCorp rows in 2021–2024, 33% in 2025, 0% in 2026. From the 2025-08 service month on, every LabCorp row has a patient ID, i.e. only the tokenized LabCorp file is loaded. Non-tokenized LabCorp records (the full file, S2) are no longer in HIST.
* **L-D. The 3.1 lab journey drops rows without a numeric patient ID** (`REGEXP_LIKE(PATIENT_ID, '^[0-9]+$')`), so pre-2025 LabCorp history is thinner than the row counts suggest. This matters for `RUNNING_` features that start 2023-01-01.
* **L-E. PJ01 already reads both labs.** `01_patient_journey_labs` (cell 12) reads HIST with no `LAB_IDENTIFIER` filter. Docs that call the source "Quest only" and list LabCorp as open (Lab Journey Plan L-O3, Lab Strategy File) are out of date.

### 2.3 HIST vs `STG_CAR_IQV_QUEST_TO_LAAD_FULL`

`FULL` is almost all LabCorp: 648,603,816 `'P'` rows (2021-08 .. 2026-10; 279,120,489 without patient ID) and only 15 Quest rows. For LabCorp, HIST has more rows than FULL in every month from 2025-01 to 2026-10, and FULL has a gap in 2025-07 .. 2025-09 (2.70M, 0.47M, 1.00M rows vs 16.0M, 16.2M, 14.2M in HIST). From 2025-10 on, rows with a patient ID differ (e.g. 2026-06: HIST 15,052,511 vs FULL 13,531,718). Record-level overlap was not checked, but a union of the two would at least double count the shared LabCorp loads.

---

## 3. Duplicate loads – the 2024 -> 2025 "drop"

### 3.1 What happened

HIST keeps every delivery (`DATA_DT`) as new rows. A history reload on **2025-03-06/07** was added on top of the original monthly loads instead of replacing them.

* **Quest:** every service month 2023-07 .. 2024-12 has 2 load dates (the original monthly load + the 2025-03 reload). For 2024-06 the original load has 4,993,178 rows and the reload 9,986,356 rows (exactly 2x). So 2024-06 is held 3 times; the other pre-2025 Quest months show the same two-load pattern (sizes checked only for 2024-06). From 2025-01 on each Quest month has 1 load, except 2025-05 (2 loads, 11.07M rows vs ~5.4M in nearby months).
* **LabCorp:** each month has the original load, the 2025-03-07 reload, and small late additions in every later monthly delivery (2024-06: 29 load dates; original 20,818,541 rows, reload 34,910,414). The 2025-07-21 delivery repeats the 2025-06-19 delivery (same row counts in both service months checked: 2024-06 19,814; 2025-06 327,774).

### 3.2 Unique records, sample months

| Lab | Month | Rows in HIST | Unique records | Duplicate share |
| --- | --- | --- | --- | --- |
| Quest | 2024-06 | 14,979,534 | 4,634,221 | 69% |
| Quest | 2025-06 | 5,277,092 | 5,038,288 | 5% |
| LabCorp | 2024-06 | 57,318,053 | 23,696,057 | 59% |
| LabCorp | 2025-06 | 15,393,087 | 12,618,796 | 18% |

Unique key: Quest = patient, NPI, service date, LOINC, test name, value, unit, accession hash (Quest has no `RECORD_ID`); LabCorp = `RECORD_ID`.

LabCorp unique records **with a patient ID**: 2024-06 9,511,515; 2025-06 6,267,644; 2026-06 13,588,436.

**Reading:** Quest unique records went up ~9% from 2024-06 to 2025-06, so there is no real Quest drop. LabCorp tokenized records dipped in 2025-06 (changeover to tokenized-only delivery, L-C) and were higher in 2026-06 than in 2024-06.

### 3.3 Duplicates in the eGFR / UACR rows used by the lab journey (2025-01 .. 2026-10)

Rows with a patient ID and the eGFR / UACR LOINC codes in 2.1. Exact duplicate = same patient, NPI, service date, LOINC, value and unit (removed by the PJ01 `DISTINCT`). Same-day, different value = same patient, NPI, day and LOINC with another value (combined by the median).

| Lab | Year | Test | Rows | Exact duplicates | Same day, different value | Patient x NPI x day x LOINC |
| --- | --- | --- | --- | --- | --- | --- |
| LabCorp | 2025 | eGFR | 44,082,661 | 5,795,174 (13.1%) | 8,739,461 (19.8%) | 29,548,026 |
| LabCorp | 2025 | UACR | 8,771,121 | 1,163,417 (13.3%) | 1,051,178 (12.0%) | 6,556,526 |
| LabCorp | 2026 | eGFR | 51,274,721 | 2,779,824 (5.4%) | 7,467,693 (14.6%) | 41,027,204 |
| LabCorp | 2026 | UACR | 10,752,631 | 651,903 (6.1%) | 1,209,270 (11.2%) | 8,891,458 |
| Quest | 2025 | eGFR | 60,292,728 | 5,671,457 (9.4%) | 2,012,709 (3.3%) | 52,608,562 |
| Quest | 2025 | UACR | 12,141,660 | 836,767 (6.9%) | 246,562 (2.0%) | 11,058,331 |
| Quest | 2026 | eGFR | 43,511,045 | 748,764 (1.7%) | 1,465,567 (3.4%) | 41,296,714 |
| Quest | 2026 | UACR | 22,674,845 | 117,825 (0.5%) | 533,877 (2.4%) | 22,023,143 |
| **Total** | | | **253.5M** | **17.8M (7.0%)** | **22.7M (9.0%)** | **213.0M** |

### 3.4 What this means

* **Lab stages (PJ01):** mostly safe, because exact copies are removed by `DISTINCT` before the median. Reload copies with a changed value can still move the median – to be tested.
* **Counts are inflated for pre-2025 months:** any row-based volume (e.g. the 3.0 "GFR 201M rows" figure), the row and no-patient counts in 2.1, and any feature that counts rows rather than distinct test-days.
* **Proposed rule (to agree):** dedup LabCorp on `RECORD_ID` and Quest on the full-row key above (or keep the latest `DATA_DT` per record) before the journey query; add a dedup check to the dropped-rows report.
* **Not yet measured:** unique records for every month 2021–2026 (only 2024-06, 2025-06, 2026-06 checked); duplicates before 2025 at the eGFR / UACR level.

---

## 4. How NBA 3.0 used lab data

### 4.1 Source and rules

* **Source:** `STG_CAR_IQV_QUEST_TO_LAAD_HIST` (both the patient-journey input query and the HCP `Lab_03` query). The 3.0 notebook headers still mention `PHCDW_SANDBOX.IQV_QUEST_LAB`, which is out of date. 3.0 treated the source as Quest, but the `Lab_03` query has no `LAB_IDENTIFIER` filter, so LabCorp rows were included too (the 3.0 patient-journey query was not re-checked for this).
* **Tests:** two types only, found by **test name**, not LOINC: GFR = name like `%GFR%` or `%GLOMERULAR%`; UACR = name like `%ALB%` or `%RATIO%`. No LOINC code was carried forward.
* **Filters:** units in one shared list (`ML/MIN/1.73M2`, `MCG/MGCREAT`, `MG/G {CREAT}`, `MG/GCR`); plain numeric values only; NPI not null; **primary-care specialties only** (`FM, FPG, GP, GPM, IFP, IM, IMG, IPM, NRP, PHA`).
* **Staging:** median result per patient, NPI, day and test. eGFR: <15 = 5, 15–30 = 4, 30–60 = 3, 60–90 = 2, otherwise 1; eGFR > 150 = 0 and no valid range; UACR stages A1–A3. Same-day median mixed all eGFR equations.
* **Not used:** potassium and HbA1c; per the team code notes, `MEDIAN_TEST_RESULT` was loaded in the patient-level lab input but no feature used it.

The 15 hardcoded parts of the 3.0 query (Q1–Q15) and their 3.1 fixes are in `NBA_3_1_Lab_Journey_Plan.md` section 2.

### 4.2 Where lab data went in 3.0

| Use | How | 3.0 issue found |
| --- | --- | --- |
| **Patient eligibility** (patient journey -> combine) | Lab stage per patient-month; combine `GFR_UACR_DX_STAGE = COALESCE(Dx stage, GFR stage, UACR stage)`; eligible = stage 2–4 and not on dialysis | Dx stage was often 0 (not null), which hid the lab stage; the 3.0 production combine carried a lab stage in only ~18% of the months that had one (B1). SGLT2 rule for unknown stage never applied (C1, fixed in 3.1 PJ06) |
| **HCP lab features** (`02_claim_lab_monthly`) | Input `Lab_03` (separate 3.0 query in `00_Write_Input_Files`); counts of lab claims per window (1, 3, 6, 12 months) by test type, by stage, total; `RUNNING_` totals; `PCT_` shares (102 columns) | `Lab_03` held far fewer tests than the patient-journey input: 108.8M rows / 122.9K NPIs vs 190.1M / 167.1K (since 2023-01-01). The 3.1 pull has 207.5M / 199.9K. Older provider table, raw name and unit columns |
| **Patient-level lab features** | `lab_input_claims_12M_and_first_occ_features_input` (recency, first occurrence, frequency) | Per the team code notes: name-based tests, no LOINC, GFR 201M rows / 65.3M patients, UACR 36.9M rows / 16.4M patients (row counts likely include the duplicate loads in section 3). 3.0 patient-feature code not re-reviewed here |

### 4.3 What the team already analysed

Sehar's code-level triage (`Product_Group_Mapping`, commits 2026-10-22 "Market Basket Analysis Rx, Px, Dx, Lab" and 2026-10-27): `Kerendia_Lab_Code_Analysis.xlsx`, `lab_code_indication_summary.csv`, `NBA all Codes analysis.md`, `NBA_3_1_Feature_Code_Recommendations.md`. It covers **which LOINC codes to keep** (45 LOINC x name combinations over 24 months, all specialties; 4 families: eGFR, UACR, HbA1c, potassium; no BNP, troponin, glucose or T1D antibody labs). Largest codes by patients: 98979-8 eGFR 67.0M, 2823-3 potassium 27.8M, 4548-4 HbA1c 18.3M, 9318-7 UACR 16.1M.

**Not covered by any existing analysis (gaps this doc starts to fill):** Quest vs LabCorp composition, patient-matching rate over time, duplicate loads and true volume trend, FULL vs HIST, feed timing (latest month per lab). The same source-level review is still missing for LAAD Rx, Dx and Px.

---

## 5. Next steps for the Lab readiness plan

1. Agree the dedup rule (S3) and measure its effect on lab stages and on NB02 counts.
2. Unique records per month 2021–2026 per lab (true volume trend); raise the 2025-03 reload with PHCDW.
3. Distinct patients and NPIs per lab and year after dedup.
4. Close L1 (specialty filter: 211.4M eGFR rows excluded), L2 (`>60` results), L3 (lab settings location) in the Lab Journey Plan.
5. Phase B: potassium and HbA1c (LabCorp only), eGFR value / decline, 3a/3b split; LabCorp full file (S2) when received.
6. Update stale docs: "Quest only" source wording (Lab Journey Plan, Lab Strategy File, NB02 header F4).

---

## Appendix – how the numbers were produced (2026-11-23)

All queries on Unity Catalog `phcdw.phcdw_stg_car.stg_car_iqv_quest_to_laad_hist` and `..._full` (Snowflake federation), serverless. Year = `LEFT(MONTH_ID, 4)`. Checks: duplicate table rows add up (exact + same-day + distinct keys = rows); 2026 Quest eGFR and LabCorp UACR totals match table 2.1; Quest 2024-06 load sizes 4,993,178 + 9,986,356 = 14,979,534 = month total.
