# NBA 3.1 – Lab patient journey (PJ01): analysis and plan

**Status (2026-11-02):** Phase A Steps 0–5 built and run. Validation run (10 HCPs) and full HCP universe run both succeeded. Write is on (the lab table is written in every run, to its own folder). Open: L1–L3 (section 8), B1 (section 9), Phase B additions (section 10).  
**Old notebook:** `Lab Files/(Clone) 01_patient_journey_labs` (frozen 3.0 baseline; its pre-built input table was removed in the 2026-10-26 refresh, so the 3.0 query now runs directly from Snowflake)  
**New notebook:** `Lab Files/01_patient_journey_labs` (33 cells; steps added after the 3.0 cells, same approach as Dx, Rx and Px)  
**Lab basket:** `Final Product Basket/Kerendia_Lab_Final.csv` (28 rows = 23 LOINC codes + 5 test-name backups; the original `Kerendia NBA 3.1 - Lab Event List.csv` is kept unchanged)  
**Downstream:** `06_patient_journey_combine` (lab stage feeds the `GFR_STAGE`, `UACR_STAGE` and `GFR_UACR_DX_STAGE` columns in the eligibility table), `Patient_Trace_755592568`, HCP-level notebooks  
**Approach:** keep the 3.0 query as the baseline, add one step at a time, compare each step row by row with the one before.  
**Scope:** Phase A = match 3.0, make it dynamic, measure every change. Potassium, HbA1c and other new lab features are Phase B (section 10).  
**Go-live:** the 3.1 lab table is written in every run (validation and full). The combine stays as it is until the 3.1 Dx / Px / flags tables go live (G1).
**Client summary:** `Lab Files/NBA_3_1_Lab_Journey_Client_Summary.md` (team-facing, no code).  
**Changes walkthrough:** `Lab Files/NBA_3_1_Lab_Journey_Changes_Walkthrough.md` (layer-by-layer, for the Argentina team review).  
**Full-run findings:** `Combine Files/NBA_3_1_E2E_Full_Run_2026_11_02.md`, section 2 (lab) and section 4.2 (B1: the 3.0 Ops combine used only ~18% of 3.0 lab stages).

---

## 0. Implementation results

### 0.1 Validation run (10 test HCPs, 2023-01 to 2026-09)

Run 2026-11-02 in `01_patient_journey_labs` (cells 2a–2e, 3a–3e, 4a–4e, cleanup, write).

| Step | Check | Result |
| --- | --- | --- |
| 2 | Basket query vs 3.0, all US 2025-01 to 2026-09 | eGFR: 106.73M test-days same stage (99.9%), 55K changed (preferred equation), 260 lost (212 above 200, 48 = 0), 0 gained. UACR: 19.81M same (99.5%), 27.4K changed, 68.4K lost (components), 2.5K lost (above 10,000), 0 gained |
| 3 | Config query vs Step 2 | Identical. 19% less data pulled from Snowflake (312.9M → 252.2M rows; dates applied inside the SQL) |
| 4 | Code rules vs Step 3 | eGFR: 107.17M identical, +35.7K gained (`>90`, `75^`, etc.; 26.8K patients), 0 lost. UACR: 19.86M identical, +1.3K gained, 0 lost. Dropped-rows report on every run |
| 5 | Validation HCPs (10 doctors) | **No change:** 225 patients, 878 eGFR test-days, 289 UACR test-days, 6,139 patient-months. +26 patient-months with eGFR stage (150–200 now stage 1). CKD stage 3–5 months: 2,347 (same) |
| Write | `kerendia_nba_3_1_lab_journey_validation` | 6,171 patient-months, 225 patients (validation folder) |

### 0.2 Full HCP universe run (2026-11-02)

Job run 1066154679479482, `VALIDATION_MODE = false`, HCP universe = 294,726 HCPs (3.1 `HCP_Universe_without_call_hcps`). Task `pj01_lab` succeeded in 11 minutes.

| Metric | 3.1 full | 3.0 full |
| --- | --- | --- |
| Lab journey rows | 1,750,760,310 | 2,212,793,523 |
| Lab journey patients | 64,594,814 | 65,590,422 |

3.1 covers 46 months (Dec 2022 – Sep 2026); 3.0 covers Jan 2021 – Oct 2026, so 3.0 has more rows from the extra years. The patient count is slightly lower in 3.1 because the 3.1 HCP universe is different (294,726 vs 234,404 HCPs; different universe, not a subset).

### 0.3 Key finding from the full run (B1)

The 3.0 full combine table (`pat_gfr_dx_stage_and_treatment_category`, written 2026-10-27) carries a lab stage in only ~18% of the months that have one in the 3.0 lab journey output (`kerendia_nba_3_0_lab_journey_output`). The 3.1 combine uses the lab stages as intended (the `COALESCE` falls back to the lab stage when the Dx stage is null). This means most of the full-scale eligibility differences between 3.0 and 3.1 come from the 3.0 production combine not using its own lab data, not from the 3.1 lab logic. See `NBA_3_1_E2E_Full_Run_2026_11_02.md` section 4.2. **Open: confirm which lab input the 3.0 Ops combine read** (B1, section 9).

---

## 1. Current notebook: what it does

### 1.1 Old notebook (`(Clone) 01_patient_journey_labs`, 12 cells)

| Cell | What it does |
| --- | --- |
| 1 | Header (out of date: lists `IQV_QUEST_LAB`, dates 2017) |
| 2 | `00_connection`, `00_cohort_config` (path broken since the move to `Lab Files`) |
| 3 | **Load:** reads a pre-built Delta table `kerendia_nba_3_0_lab_query_output` (removed in the 2026-10-26 refresh) |
| 4 | **Cleanup:** month sequence between tests, forward fill, max per patient-cohort-month, cohort label join |
| 5–7 | Comparison with production, write `kerendia_nba_3_1_lab_journey_validation` |

The lab rules were not visible in this notebook: they lived in the 3.0 query that built the input table.

### 1.2 New notebook (`01_patient_journey_labs`, 33 cells)

| Cells | Section | What it does |
| --- | --- | --- |
| 1–2 | Header + optimization summary | Goal, steps, findings, decisions |
| 4–6 | Setup | `00_connection`, `00_config` (added for `date_end` and HCP universe paths), `../../00_cohort_config` |
| 7 | **3.0 baseline query** | The 3.0 SQL runs directly from Snowflake (the pre-built table was removed). HCP universe join, validation filter. Produces `df_lab` |
| 8 | Step 1 (markdown) | Inventory of 15 hardcoded parts of the 3.0 query, grouped: basket (1–5, 14), config (7–12), code (6, 13, 15) |
| 9–14 | **Step 2: basket** | 2a reads and validates `Kerendia_Lab_Final.csv`; 2b builds the SQL from the basket; 2c runs it; 2d compares with 3.0; 2e findings |
| 15–20 | **Step 3: config** | 3a `LAB_CONFIG` + checks that tables/columns exist; 3b query; 3c run; 3d compare with Step 2; 3e findings |
| 21–26 | **Step 4: code rules** | 4a `VALUE_RULES`, `PATIENT_ID_RULE`, per-test rules; 4b query + dropped-rows report; 4c run; 4d compare with Step 3; 4e findings |
| 27–33 | Cleanup, comparison, write | Same cleanup logic, now on the Step 4 output (was on `df_lab`). Write adds `overwriteSchema` |

Each step includes the previous one, so Step 4 = basket + config + code rules.

### 1.3 Output and how it is used downstream

Output columns: `PATIENT_ID, DATE, GFR_STAGE, UACR_STAGE, cohort_label`.

`06_patient_journey_combine`:
* Full join with the Dx and Rx journeys on `PATIENT_ID, DATE` (lab months also create patient-months in the spine).
* `GFR_DX_STAGE = COALESCE(DX_STAGE_UPDATED, GFR_STAGE)`: the lab stage is used when the Dx stage is null.
* `GFR_UACR_DX_STAGE = COALESCE(DX_STAGE_UPDATED, GFR_STAGE, UACR_STAGE)`: the UACR stage is used when both Dx and eGFR are null.
* Eligibility: stage 2–4 (from `GFR_UACR_DX_STAGE`) and not on dialysis. Stage 1 and 5 are not eligible.

The lab stage is the **fallback** for the Dx stage. In 3.0, the Dx stage was often 0 ("unknown"), which hid the lab stage because `COALESCE(0, GFR_STAGE)` returns 0. In 3.1, the Dx stage is null when no stage is known, so `COALESCE(null, GFR_STAGE)` returns the lab stage (Dx plan N1). This is the main mechanism by which the lab now affects eligibility.

---

## 2. Bottlenecks found in the 3.0 query

| # | Hardcoded / issue | Effect | Fix goes in |
| --- | --- | --- | --- |
| Q1 | **Test identification by name text only** (`%GFR%`, `%GLOMERULAR%`, `%ALB%`, `%RATIO%`) | Renamed tests are lost; unrelated tests with "ALB" or "RATIO" in the name are included | Basket (LOINC codes + name backup) |
| Q2 | **Stage cut-offs written in the SQL** | Changing a cut-off (e.g. stage 3a/3b) means editing the SQL | Basket (`STAGE_CUTOFFS` column) |
| Q3 | **Units: one list shared by both tests** | A UACR unit can pass for eGFR and vice versa | Basket (one unit list per test) |
| Q4 | **Valid range: none. eGFR > 150 = stage 0, eGFR = 0 = stage 5** | Invalid values get a wrong stage | Basket (`VALID_MIN` / `VALID_MAX`) |
| Q5 | **Same-day aggregation: median of all eGFR equations** | Black and non-Black equations are mixed on the same day | Basket (`PRIORITY` column) |
| Q6 | **Value format: plain numbers only** | `75^` and `>90` are dropped; lab flags lose valid results | Code (`VALUE_RULES`) |
| Q7 | **Start date written twice** (`2021-11-30` in SQL + `DATA_START_DATE` in Spark) | Conflicting dates | Config (`LAB_CONFIG`) |
| Q8 | **End date applied after pulling all history** | More data pulled than needed (19% more) | Config (dates inside the SQL) |
| Q9 | **Date formats in a fixed `CASE`** | A new format fails silently | Config (`TRY_TO_DATE` over a format list) |
| Q10 | **Specialty filter: 10 primary-care codes in the SQL** | Removing or adding a code means editing the SQL; 211.4M eGFR rows excluded (the largest single exclusion) | Config (`LAB_CONFIG`) |
| Q11 | **Table and column names in the SQL** | A rename breaks the query | Config (`LAB_CONFIG`) |
| Q12 | **No dropped-rows report** | Losses are silent | Code (Step 4b report) |
| Q13 | **UACR components staged as results** | Urine creatinine, serum albumin etc. get UACR stages (wrong) | Basket (`ROLE = PART`) |
| Q14 | **eGFR 150–200 = stage 0** | These are valid stage 1 results, not invalid | Basket (valid range extended to 200) |
| Q15 | **Patient ID rule in the SQL** | Not visible, not checked | Code (`PATIENT_ID_RULE`) |

---

## 3. Lab basket design (`Kerendia_Lab_Final.csv`)

One row per LOINC code (or name backup), with all rules in columns. The original `Kerendia NBA 3.1 - Lab Event List.csv` (Sehar's file) is kept unchanged.

| Column | Meaning | Example |
| --- | --- | --- |
| `MATCH_TYPE` | `LOINC` code or `NAME` pattern (backup) | `LOINC`, `NAME` |
| `MATCH_VALUE` | The LOINC code or the `LIKE` pattern | `98979-8`, `%GFR%` |
| `TEST_TYPE` | Test label (becomes `<TEST_TYPE>_STAGE` in the output) | `GFR`, `UACR` |
| `ACTIVE` | `Y` = used in the lab journey | Potassium, HbA1c = `N` |
| `ROLE` | `RESULT` = staged; `PART` = component, never staged | urine creatinine = `PART` |
| `PRIORITY` | Same patient, day, NPI: lowest number wins | race-free CKD-EPI 2021 = 1, Black eGFR = 3 |
| `UNITS` | Allowed units, pipe-separated, per test | `ML/MIN/1.73M2` |
| `VALID_MIN` / `VALID_MAX` | Values outside are dropped | eGFR 1–200, UACR 0–10,000 |
| `STAGE_CUTOFFS` | `value:stage` pairs, pipe-separated, "below value → stage" | `15:5 \| 30:4 \| 60:3 \| 90:2 \| else:1` |
| `TEST_FAMILY` | Group label | `eGFR (CKD function)`, `UACR (CKD albuminuria)` |
| `NOTE` | Free text | `CKD-EPI 2021 creatinine - race-free` |

**eGFR codes (8 LOINC + 3 name backups):**

| Priority | Codes | Equation |
| --- | --- | --- |
| 1 | 98979-8, 98980-6 | CKD-EPI 2021, race-free (creatinine; creatinine + cystatin C) |
| 2 | 62238-1, 33914-3, 48642-3, 88294-4, 50210-4 | CKD-EPI 2009, MDRD, MDRD non-Black, CKD-EPI 2009 non-Black, cystatin C |
| 3 | 88293-6 | CKD-EPI 2009 Black – used only if nothing else that day |
| 2 / 3 | NAME `%GFR%`, `%GLOMERULAR%` (2), `%AMONG BLACKS%` (3) | 3.0 name rule, kept as backup |

**UACR codes (2 staged + 11 parts + 2 name backups):**

| Role | Codes | What they are |
| --- | --- | --- |
| RESULT (staged) | 9318-7, 14958-3 | Albumin/creatinine ratio, microalbumin/creatinine ratio |
| PART (never staged) | 2161-8, 14683-7, 35674-1, 2160-0, 14957-5, 1754-1, 61151-7, 19153-6, 13362-9, 49023-5, 34535-5 | Urine creatinine, serum creatinine, albumin concentration, serum albumin, urine volume, collection duration, 24h albumin, text results |
| RESULT (backup) | NAME `%ALB%`, `%RATIO%` | 3.0 name rule for rows without a basket code |

**Switched off (`ACTIVE = N`):**

| Test | LOINC | Units | Valid range | Purpose |
| --- | --- | --- | --- | --- |
| Potassium | 2823-3 | MMOL/L | 1–10 | Kerendia safety monitoring (hyperkalemia); Phase B |
| HbA1c | 4548-4 | % | 3–20 | Diabetes control; Phase B |

**Points still open in the basket:**
* 14959-1 (microalbumin/creatinine mass ratio, urine) and 48643-1 (MDRD, Black) are not in the file. Rows with these codes can still enter through the name backup at priority 2 if their name and unit match, but this is worth a quick count.

---

## 4. Build plan (new notebook `01_patient_journey_labs`)

Each step adds cells and a comparison with the previous step; the 3.0 query is never changed.

| Step | What | Comparison / check | Expected result |
| --- | --- | --- | --- |
| 0 | Copy the old notebook; rewrite the header; run the 3.0 SQL directly from Snowflake (pre-built table was removed) | Same output as the old notebook (10 HCPs) | Identical |
| 1 | Markdown inventory of the 15 hardcoded parts (section 2 above) | Review only | – |
| 2 | **Basket:** read `Kerendia_Lab_Final.csv`, checks (no duplicate codes, consistent rules per test, valid roles), build the SQL from the basket; stage from `STAGE_CUTOFFS`; UACR parts excluded by `ROLE` | Part A all US (test-days): same / different / lost / gained. Part B 10 HCPs month by month | eGFR 99.9% same; UACR 99.5% same; components no longer staged |
| 3 | **Config:** `LAB_CONFIG` (start/end dates in the SQL, specialty filter, date formats, source/provider table and column names); checks that tables and columns exist | Part A identical to Step 2; rows pulled before/after | Same output, 19% less data pulled |
| 4 | **Code rules and report:** `VALUE_RULES` (lab flags, `>` / `<`), `PATIENT_ID_RULE`, dropped-rows report | Part A identical to Step 3 + gains; Part B validation HCPs; Part C dropped-rows report | +35.7K eGFR test-days gained; losses visible |
| 5 | Cleanup: same logic as 3.0 (month sequence, forward fill, max per patient-cohort-month, cohort label), now on the Step 4 output | Patient-months and stage counts vs 3.0 cleanup, 10 HCPs | No change for validation HCPs; +26 months with eGFR stage (150–200) |
| 6 | Write `kerendia_nba_3_1_lab_journey_validation` | Write succeeds; schema check against what PJ06 reads | Done |
| 7 | Downstream (separate tasks): PJ06 re-run; HCP-level notebooks; Phase B additions (section 10) | Stage counts before/after in PJ06 | – |

---

## 5. Run settings (`LAB_CONFIG`)

| Setting | 3.0 | Now |
| --- | --- | --- |
| Start date | `'2021-11-30'` in SQL + `DATA_START_DATE` in Spark | `DATA_START_DATE` only, inside the SQL |
| End date | `date_end` applied in Spark after pulling all history | Inside the SQL |
| Specialties | 10 primary-care codes in SQL | Same list in config; `None` = no filter |
| Date formats | `CASE` with `TO_DATE` (fails on a new format) | `TRY_TO_DATE` over a format list; unreadable dates counted |
| Source table | `PHCDW_SANDBOX.IQV_QUEST_LAB` | Same, in config (checked before run) |
| Provider table | `STG_IQVIA_LAAD_DIM_PRVDR` | Same, in config (checked before run) |

**Specialty filter:** the 10 primary-care specialty codes are the largest single exclusion (211.4M eGFR rows, 21.2M UACR rows, all US 2023–2026). Removing it adds about 16% more eGFR and 13% more UACR patients. This is an open decision (L1, section 8).

---

## 6. Dropped-rows report (new in 3.1)

All US, 2023-01 to 2026-09, source rows. 3.0 excluded the same rows but did not report them.

| Reason | eGFR rows | UACR rows | Can be recovered? |
| --- | --- | --- | --- |
| Patient ID missing or invalid | 65.6M | 11.8M | No |
| Prescriber NPI missing | 24.3M | 3.8M | No |
| Component of a test, not a result | – | 16.0M | No (by design) |
| Value empty or text (e.g. "DNR", "See comment") | 12.3M | 6.8M | No |
| Unit not allowed | – | 32.8K | Possibly (add unit to the list) |
| Outside valid range | 4.6M | 26.2K | No |
| `>` / `<` value with unclear stage (e.g. `>60`) | 827K | 314 | Decision (L2) |
| **Specialty not in the 10 primary-care codes** | **211.4M** | **21.2M** | **Decision (L1)** |
| **Kept** | **631.9M** | **106.9M** | – |

---

## 7. Validation results

### 7.1 All US, 2025-01 to 2026-09 (test-days = patient x day x test)

| Result | eGFR | UACR |
| --- | --- | --- |
| Same stage as 3.0 | 106.73M (99.9%) | 19.81M (99.5%) |
| Stage changed | 65.3K (0.06%) | 27.4K (0.14%) |
| – from eGFR 150–200 now stage 1 (was 0) | 10.4K | – |
| – from preferred equation on the same day | ~55K | 27.4K |
| No longer included | 260 (above 200 or = 0) | 71.0K (68.4K components, 2.5K above 10,000) |
| Newly included (`>90`, `<15`, `75^`, ...) | +35.7K (26.8K patients) | +1.3K |

### 7.2 Validation HCPs (10 doctors, 2023-01 to 2026-09)

| Metric | 3.0 | 3.1 | Change |
| --- | --- | --- | --- |
| Patients | 225 | 225 | 0 |
| eGFR test-days | 878 | 878 | 0 |
| UACR test-days | 289 | 289 | 0 |
| Patient-months | 6,139 | 6,139 | 0 |
| Patient-months with eGFR stage 3–5 | 2,347 | 2,347 | 0 |
| Patient-months with UACR A2–A3 | 1,504 | 1,504 | 0 |
| Patient-months with any eGFR stage | 5,981 | 6,007 | +26 (eGFR 150–200 now stage 1) |

### 7.3 Full HCP universe (2026-11-02)

| Metric | 3.1 full | 3.0 full |
| --- | --- | --- |
| Lab journey rows | 1,750,760,310 | 2,212,793,523 |
| Lab journey patients | 64,594,814 | 65,590,422 |

### 7.4 Run efficiency

| | 3.0 settings | 3.1 settings |
| --- | --- | --- |
| Rows pulled from Snowflake | 312.9M | 252.2M (−19%) |
| Unreadable service dates | Not reported | 38 empty, 0 unknown format (of 1.72B source rows) |

---

## 8. Decisions

### 8.1 Decisions made

| # | Decision | Choice | Reason |
| --- | --- | --- | --- |
| L-D1 | eGFR valid maximum | 200 (was 150) | Values 150–200 are stage 1, not invalid |
| L-D2 | Source of lab test rules | One lab test list (CSV); the original list is kept unchanged | Single place for all test rules |
| L-D3 | Test-name backup | Kept | Rows without a LOINC code are still found |
| L-D4 | Same-day results | Lowest priority number wins; exact value beats `>` / `<` at the same priority | Uses the preferred eGFR equation (race-free CKD-EPI 2021) |
| L-D5 | Lab flags (`^`) | Read as the number | Valid results are not lost |
| L-D6 | UACR components | `ROLE = PART`, never staged | Urine creatinine etc. are not ratios; staging them gives wrong UACR stages |
| L-D7 | Basket file name | `Final Product Basket/Kerendia_Lab_Final.csv` | Consistent with Dx, Rx, Px naming |
| L-D8 | Cleanup on Step 4 output | Switched from `df_lab` (3.0) to `df_lab_step4` | The new query output is now connected to the written table |

### 8.2 Decisions for the final review

| # | Decision | Options | Impact | Status |
| --- | --- | --- | --- | --- |
| L1 | **Specialty filter** | (a) keep the 10 primary-care codes, (b) remove the filter, (c) add cardiology, endocrinology and nephrology | Removing it adds about 16% more eGFR patients and 13% more UACR patients (all US) | Open |
| L2 | **`>60` eGFR results** (827K rows) | (a) keep excluded (conservative), (b) count as "not CKD stage 3+" | (b) adds patients who are very unlikely to be CKD stage 3+ | Open |
| L3 | **Where the settings block lives** | (a) lab notebook, (b) shared patient-journey config | (b) shares the same settings with the other patient-journey notebooks | Open |

---

## 9. Open points

| # | Point | Status | Effect |
| --- | --- | --- | --- |
| B1 | **Which lab input the 3.0 Ops combine read** in production: it uses about 18% of the 3.0 lab-journey stages. The 3.1 combine uses them as intended. Needed before the full-scale 3.0 vs 3.1 differences can be fully explained. To check in the 3.0 Ops combine notebook (owner: Wenjie). See `NBA_3_1_E2E_Full_Run_2026_11_02.md` section 4.2 | Open | Most of the full-scale eligibility difference is a 3.0 baseline artefact, not a 3.1 lab change |
| B4 | Volume: the lab table feeds 148.0M patients in the combine. Check that the HCP-level notebooks handle this volume | Open | – |
| L-O1 | Two missing codes: 14959-1 (microalbumin/creatinine ratio) and 48643-1 (MDRD, Black). Rows can still enter through the name backup, but a quick count is worth doing | Open | Small |
| L-O2 | Lab testing from procedure claims (CPT 82043, 82570, 82565, 80047–80053, 83036/83037) to cover HCPs without Quest lab data | Planned (Phase B) | "Tested yes / no" flags, no result values |
| L-O3 | LabCorp as a second lab source | Open | Same tests from a second lab; questions on availability, patient ID matching and overlap with Quest |

---

## 10. Phase B: planned lab additions

Potassium and HbA1c are in the lab test list with `ACTIVE = N`. The following additions are planned but not yet built:

| What | Planned item | What it means for the lab notebook | Priority |
| --- | --- | --- | --- |
| Switch on Potassium | LOINC 2823-3, keep the value (not a stage) in the output | Last potassium value; flag above 5.0 mmol/L for "Kerendia-ready" and hyperkalemia barrier counts | High |
| Switch on HbA1c | LOINC 4548-4, keep the value (not a stage) in the output | Last HbA1c value; flag at 9%+ (uncontrolled diabetes) | Medium |
| Missing codes | 14959-1 (UACR), 48643-1 (eGFR) | Add rows to the existing tests in the lab test list | Low |
| Lab-based CKD flag | Two eGFR < 60 or two UACR >= 30, at least 90 days apart (KDIGO) | New patient flag from existing eGFR / UACR results | Medium |
| eGFR value and decline | Last eGFR value; eGFR fall of 30%+ within 24 months | Needs the eGFR value kept in the output, not only the stage | Medium |
| CKD stage 3a / 3b split | eGFR 45–59 = stage 3a, 30–44 = stage 3b | Change to the eGFR stage cut-offs in the lab test list | Low |
| Lab testing from procedure claims | CPT codes for urine albumin, creatinine, HbA1c, panels | "Tested yes / no" flags from procedure claims, for HCPs without Quest data | Medium |
| LabCorp | Same tests from a second lab | Depends on data availability and patient ID matching | Low |

All value-based features (eGFR decline, Potassium, HbA1c) require the result value to be carried into the patient journey output. Today the output keeps the stage columns only.

---

## 11. References

* `Lab Files/NBA_3_1_Lab_Journey_Client_Summary.md`: team-facing summary (no code), including business reasoning for Potassium and HbA1c, and the LVEF / HF indication context
* `Lab Files/NBA_3_1_Lab_Journey_Changes_Walkthrough.md`: layer-by-layer walkthrough for the Argentina team review
* `Lab Files/NBA_3_1_Lab_Cell10_Basket_Reader_Explained.md`: how the basket reader (cell 2a) works
* `Alignment_Markdowns/NBA_3_1_Lab_Journey_Working.md`: working copy of the client summary
* `Combine Files/NBA_3_1_E2E_Full_Run_2026_11_02.md`: full HCP universe run findings (lab: section 2; B1: section 4.2)
* `NBA_3_1_Patient_Journey_Changes_Proposals.md`: original proposals (section 1.2: lab basket)
* Snowflake tables: `PHCDW.PHCDW_SANDBOX.IQV_QUEST_LAB`, `PHCDW.PHCDW_STG_CAR.STG_IQVIA_LAAD_DIM_PRVDR`
