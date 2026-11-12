# NBA 3.1 – Lab patient journey: walkthrough of the Argentina team's changes

**Date:** 2026-10-28  
**Scope:** agenda item 1 (Lab basket) and part of item 5 (lab source) of `NBA_3_1_Patient_Journey_Changes_Proposals.md`  
**Files compared:**
* Basket, original: `Final Product Basket/Kerendia NBA 3.1 - Lab Event List.csv` (Sehar's file, untouched)
* Basket, enhanced: `Final Product Basket/Kerendia_Lab_Final.csv`
* Notebook, before: `Patient_Journey_Validation/(Clone) 01_patient_journey_labs`
* Notebook, after: `Patient_Journey_Validation/01_patient_journey_labs`
* Context: the EOD email of 2026-10-28

This document explains what changed, layer by layer, from the basket file down to the tables the rest of the pipeline reads. It is a reading of the files; no notebook was run and nothing was written.

---

## 0. One-paragraph summary

The 3.0 lab query had all its rules written into the SQL (test name patterns, units, cut-offs, dates, specialties, table names). The team moved those rules out of the SQL in three layers: **test rules → basket CSV**, **run settings → `LAB_CONFIG`**, **value / patient-ID parsing → `VALUE_RULES` / `PATIENT_ID_RULE`**. The SQL is now generated from these three. Each step was compared row by row with the one before. The result is almost identical to 3.0 (99.9% of eGFR test-days unchanged), with a few deliberate fixes (UACR "parts" no longer staged, eGFR 150–200 = stage 1, preferred eGFR formula on the same day, `75^` and `>90` values kept). **The new query is not yet connected to the output:** the cleanup section and the written table still use the 3.0 query result (`df_lab`).

---

## 1. Layer 1 – Product basket: original vs enhanced

### 1.1 Structure

| | Original `Lab Event List.csv` | Enhanced `Kerendia_Lab_Final.csv` |
| --- | --- | --- |
| Purpose | List of codes (what the tests are) | List of codes **plus the rules to use them** |
| Columns | `EVENT_NAME, EVENT_CODE, EVENT_GROUP, IS_CLUBBED` | `MATCH_TYPE, MATCH_VALUE, TEST_TYPE, ACTIVE, ROLE, PRIORITY, UNITS, VALID_MIN, VALID_MAX, STAGE_CUTOFFS, TEST_FAMILY, NOTE` |
| Rows | 23 (8 eGFR, 13 UACR, potassium, HbA1c) | 28 (23 LOINC rows + 5 test-name backups) |
| Used by code | No | Yes: read by cell 2a, drives the SQL |

New columns explained:

| Column | Meaning | Example |
| --- | --- | --- |
| `MATCH_TYPE` | How the row is matched: `LOINC` code or `NAME` pattern (backup) | `LOINC`, `NAME` |
| `MATCH_VALUE` | The LOINC code or the `LIKE` pattern | `98979-8`, `%GFR%` |
| `TEST_TYPE` | Test label in the output (becomes `<TEST_TYPE>_STAGE`) | `GFR`, `UACR`, `POTASSIUM` |
| `ACTIVE` | `Y` = used in the lab journey | Potassium, HbA1c = `N` |
| `ROLE` | `RESULT` = staged; `PART` = component of a test, never staged | urine creatinine = `PART` |
| `PRIORITY` | Same patient, day and NPI: lowest number wins | race-free CKD-EPI 2021 = 1, Black eGFR = 3 |
| `UNITS` | Allowed units, pipe-separated, per test | `ML/MIN/1.73M2` |
| `VALID_MIN` / `VALID_MAX` | Values outside are dropped | eGFR 1–200, UACR 0–10000 |
| `STAGE_CUTOFFS` | `value:stage` pairs separated by a pipe, "below value → stage" | 15:5 \| 30:4 \| 60:3 \| 90:2 \| else:1 |

### 1.2 Codes: what changed

**eGFR (TEST_TYPE = GFR)** – same 8 LOINC codes as the original, now ranked:

| Priority | Codes | Equation |
| --- | --- | --- |
| 1 | 98979-8, 98980-6 | CKD-EPI 2021, race-free (creatinine; creatinine + cystatin C) |
| 2 | 62238-1, 33914-3, 48642-3, 88294-4, 50210-4 | CKD-EPI 2009, MDRD, MDRD non-Black, CKD-EPI 2009 non-Black, cystatin C |
| 3 | 88293-6 | CKD-EPI 2009 Black – used only if nothing else that day |
| 2 / 3 | NAME `%GFR%`, `%GLOMERULAR%` (2), `%AMONG BLACKS%` (3) | 3.0 name rule kept as a backup for rows without a basket code |

**UACR (TEST_TYPE = UACR)** – the original listed 13 codes all as "Albumin/Creatinine ratio". The enhanced file separates them:

| Role | Codes | What they are |
| --- | --- | --- |
| RESULT (staged) | 9318-7, 14958-3 | Albumin/creatinine and microalbumin/creatinine ratio |
| PART (never staged) | 2161-8, 14683-7, 35674-1 | Urine creatinine |
| PART | 2160-0 | Serum creatinine |
| PART | 14957-5, 1754-1 | Albumin concentration (not a ratio) |
| PART | 61151-7 | Serum albumin |
| PART | 19153-6, 13362-9 | Urine volume, collection duration |
| PART | 49023-5 | 24h albumin (not a ratio) |
| PART | 34535-5 | Text results only |
| RESULT (backup) | NAME `%ALB%`, `%RATIO%` | 3.0 name rule for rows without a basket code |

This resolves the main point raised in section 1.2 of the proposals doc (components and collection codes would have been staged with the 30 / 300 mg/g cut-offs).

**Potassium 2823-3 and HbA1c 4548-4** – in the file with units and valid ranges but `ACTIVE = N` and no cut-offs: kept for new features (proposals section 6, P11 and P12), not used in staging.

### 1.3 Rules that are now in the basket (were in the SQL)

| Rule | 3.0 SQL | Basket | Effect |
| --- | --- | --- | --- |
| eGFR stages | 15 / 30 / 60 / 90, stage 1 up to 150, above 150 = stage 0 | Same cut-offs, valid range 1–200 | eGFR 150–200 now stage 1 (was 0); eGFR = 0 and > 200 dropped (was stage 5 / 0) |
| UACR stages | 30 / 300 | Same | Unchanged |
| UACR valid range | none | 0–10000 | ~2.5K test-days above 10000 dropped |
| Units | One list for both tests | One list per test | A UACR unit can no longer pass for eGFR and vice versa |
| Same-day aggregation | `MEDIAN` of all results | Lowest `PRIORITY` first, then median | No more mixing Black and non-Black eGFR on the same day |

### 1.4 Points still open in the basket

* **14959-1** (microalbumin/creatinine mass ratio, urine) and **48643-1** (MDRD Black), both flagged in the proposals doc, are still not in the file. Rows with these codes can still enter through the name backup (`%ALB%`/`%RATIO%`, `%GFR%`) at priority 2 if their name and unit match, so they are not necessarily lost, but this is worth a quick count.
* The proposals doc (section 1.2) refers to an earlier version of `Kerendia_Lab_Final.csv` (88294-4 duplicated, 3 `nan` rows). That version has been replaced; section 1.2 of the proposals doc should be updated.

---

## 2. Layer 2 – Notebook: before vs after

### 2.1 Before: `(Clone) 01_patient_journey_labs` (12 cells)

1. `%run 00_connection`, `%run ./00_cohort_config`
2. **Load:** reads a pre-built Delta table `kerendia_nba_3_0_lab_query_output` (output of the 3.0 "Pat Journey Lab" query in `00_Write_Input_Files`), filters `SVC_DT >= DATA_START_DATE`, applies the 10 validation HCPs, keeps `PATIENT_ID, SVC_DT, GFR_STAGE, UACR_STAGE`
3. **Cleanup:** month sequence between tests, forward fill of stages, max per patient-cohort-month, cohort label join
4. Comparison with production, write `kerendia_nba_3_1_lab_journey_validation`

The lab rules were not visible in this notebook at all; they lived in the 3.0 query that built the input table.

### 2.2 After: `01_patient_journey_labs` (33 cells)

| Cells | Section | What it does |
| --- | --- | --- |
| 1–2 | Header + **optimization summary** | Goal, steps, findings, decisions (the content of the email) |
| 4–6 | Setup | `00_connection`, **`00_config` added** (for `date_end` and HCP universe paths), `../00_cohort_config` |
| 7 | **Load lab data (3.0 baseline)** | The 3.0 SQL is now run directly from Snowflake, because the pre-built `kerendia_nba_3_0_lab_query_output` table was removed in the 2026-10-26 refresh. Then `date_end`, HCP universe join, validation filter. Produces `df_lab` |
| 8 | **Step 1** (markdown) | Inventory of 15 hardcoded parts of the 3.0 query, grouped: basket (1–5, 14), config (7–12), code (6, 13, 15) |
| 9–14 | **Step 2: basket** | 2a reads and validates the CSV (no duplicate codes, consistent rules per test, valid roles); 2b builds the SQL from the basket; 2c runs it; 2d compares with 3.0; 2e findings |
| 15–20 | **Step 3: config** | 3a `LAB_CONFIG` + checks that tables / columns exist; 3b query; 3c run; 3d compare with Step 2; 3e findings |
| 21–26 | **Step 4: code rules** | 4a `VALUE_RULES`, `PATIENT_ID_RULE`, per-test rules; 4b query + dropped-rows report; 4c run → `df_lab_step4`; 4d compare with Step 3; 4e findings |
| 27–33 | Cleanup, comparison, write | **Unchanged logic, still on `df_lab` (3.0 query)**. Production comparison is now skipped if the 3.0 table is missing; write adds `overwriteSchema` |

Each step includes the previous one, so Step 4 = basket + config + code rules.

### 2.3 Step 3 – `LAB_CONFIG` (run settings)

| Setting | 3.0 | Now |
| --- | --- | --- |
| Start date | `'2021-11-30'` in SQL + `DATA_START_DATE` in Spark | `DATA_START_DATE` only, inside the SQL |
| End date | `date_end` applied in Spark after pulling all history | Inside the SQL |
| Specialties | 10 primary-care codes in SQL | Same list in config; `None` = no filter |
| Date formats | `CASE` with `TO_DATE` (fails on a new format) | `TRY_TO_DATE` over a format list; unparsed dates counted |
| Source / provider tables and columns | In SQL | Config, with a LOINC column (`LOINC_CD`) mapped and checked |

Result: identical output to Step 2, 312.9M → 252.2M rows pulled (−19%). It also answers the proposals doc prerequisite: the Quest source has a LOINC column (`LOINC_CD`).

### 2.4 Step 4 – value and patient ID rules

| Rule | 3.0 | Now |
| --- | --- | --- |
| Lab flags (`75^`) | Dropped (not a number) | `^` removed, read as 75 |
| Above / below (`>90`, `<15`) | Dropped | Kept only when the whole range has one stage: eGFR `>` ≥ 90 → stage 1, `<` ≤ 15 → stage 5; UACR `<` ≤ 30 → A1, `>` ≥ 300 → A3. `>60` is not staged (could be 1 or 2). `<X` is staged as just below X |
| Same-day with exact and above/below | – | Exact value beats an above/below value at the same priority |
| Patient ID | Digits only, cast to INT | Same rule, now one shared function; failures counted |
| Output | `PATIENT_ID, DATE, NPI, TEST_TYPE, MEDIAN, GFR_STAGE, UACR_STAGE` | Same, plus `LOINC_CDS`, `MATCHED_BY` (BASKET / NAME), `ABOVE_BELOW_VALUE`; one stage column per basket test with cut-offs |
| Dropped rows | Silent | Report: every source row counted under the first rule it fails |

---

## 3. What the comparisons showed

All US, 2025-01 to 2026-09, unless noted.

| Comparison | eGFR | UACR |
| --- | --- | --- |
| Step 2 vs 3.0: same stage | 106.73M test-days (99.9%) | 19.81M |
| Step 2 vs 3.0: one stage different | 55K (0.05%), from priority rule and 150–200 fix | 27K (0.14%) |
| Step 2 vs 3.0: lost | 260 (212 above 200, 48 = 0) | 68.4K parts + 2.5K above 10000 |
| Step 3 vs Step 2 | Identical | Identical |
| Step 4 vs Step 3: gained | +35.7K (26.8K patients), above/below with clear stage | +535 above/below, +747 flags / leading dot |
| One-off 2023–2024 check | +75.7K from `75^` values (only in 2023 data) | +10.1K |
| Validation HCPs (2023-01 to 2026-09) | No change at any step: 225 patients, 6,139 patient-months | Same |

**Dropped-rows report** (2023-01 to 2026-09). The 3.0 query drops the same rows, just without telling:

| Reason | eGFR | UACR | Recoverable? |
| --- | --- | --- | --- |
| Patient ID empty / -1 | 65.6M | 11.8M | No |
| NPI missing | 24.3M | 3.8M | No |
| Part of a test | 0 | 16.0M | No (by design) |
| Value empty / text (DNR, See Comment) | 1.6M + 10.8M | 0.8M + 6.0M | No |
| Outside valid range | 4.6M | 26.2K | No |
| Unit not allowed | 0 | 32.8K | Possibly (add unit to basket) |
| Above/below, stage unclear (`>60`) | 827K | 314 | Decision |
| **Specialty not in the 10-code list** | **211.4M** | **21.2M** | **Decision (largest cut, real data)** |
| Kept | 631.9M | 106.9M | – |

The email notes that an earlier "~370M" total quoted from chat does not match these pieces; use the table above, not that number.

---

## 4. Layer 3 – Downstream: what reaches the pipeline

```
Kerendia_Lab_Final.csv ──► 2a lab_basket / rules
LAB_CONFIG (3a) ─────────► 4b SQL ──► 4c df_lab_step4   (new, NOT yet used below)
VALUE_RULES (4a) ────────┘

3.0 SQL (cell 7) ────────► df_lab ──► cleanup (cell 28, forward fill by cohort month)
                                      ──► kerendia_nba_3_1_lab_journey_validation  (PJ01 output)
                                           ──► 06_patient_journey_combine (GFR_DX_STAGE, GFR_UACR_DX_STAGE, eligibility)
                                                ──► HCP notebooks NB01–NB06 (stage counts)
```

| Layer | Status today | After cut-over to `df_lab_step4` |
| --- | --- | --- |
| PJ01 output table | Built from the **3.0 query** (cell 7). Unchanged in content; only the source moved from a Delta table to a live Snowflake pull | One-variable change (`df_lab` → `df_lab_step4`); same schema (`PATIENT_ID, DATE, GFR_STAGE, UACR_STAGE, cohort_label`) |
| PJ06 combine | No change | Lab stage feeds `GFR_DX_STAGE` only where Dx has no stage. Expected change is small (validation HCPs identical) |
| HCP notebooks | No change | Same as PJ06; they also read `Lab_03`-style inputs built with the 3.0 rules, which would need the same basket to stay consistent |
| New features (proposals section 6) | Not started | Potassium / HbA1c: set `ACTIVE = Y` and add cut-offs or value columns; `LOINC_CDS` and `ABOVE_BELOW_VALUE` are already in the output for QC |

---

## 5. Decisions

**Already made by the team**
* eGFR valid max raised from 150 to 200.
* The enhanced basket CSV is the single source of lab test rules; Sehar's original is untouched.
* Test-name backup kept, so rows without a LOINC code are still found.
* Same-day: lowest `PRIORITY` wins; an exact value beats an above/below value.
* Lab flags (`^`) are read.

**For the final review**

| # | Decision | Options | Data |
| --- | --- | --- | --- |
| L1 | Specialty filter | (a) keep 10 primary-care codes, (b) remove, (c) add cardiology, endocrinology, nephrology | Removing adds ~16% eGFR and ~13% UACR patients; cuts 211M eGFR rows today |
| L2 | `>60` eGFR (827K rows) | (a) keep out, (b) count as "not stage 3+" | Conservative vs more patients |
| L3 | Where `LAB_CONFIG` lives | (a) this notebook, (b) `00_cohort_config` | Sharing with other PJ notebooks |

---

## 6. Observations from this review (not in the email)

* **Not connected yet:** the written table still comes from the 3.0 query. Until `df_lab_step4` replaces `df_lab` in cell 28, none of the basket fixes reach PJ06 or the HCP notebooks.
* **Two missing codes** (14959-1, 48643-1): check how many rows they have and whether the name backup already catches them; add them to the basket if not.
* **Specialty filter vs Kerendia's HF and nephrology use:** option (c) of L1 aligns with the HF features proposed in section 6 (cardiology) and the nephrology co-management feature (H22).
* **Not in Git:** the notebook and basket CSV are not version-controlled yet (noted in the notebook).
* **Proposals doc to update:** section 1.2 (codes reviewed, LOINC column confirmed, PJ01 change built) and the progress table (item 1 Lab: "built, waiting for final review").
