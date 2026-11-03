# Patient journey in NBA 3.1: Readiness Plan

**Group:** Patient-level claims journey (lab tests, diagnoses, prescriptions, procedures, diabetes / heart-failure flags, combine)  
**Purpose:** one plan for how the patient journey goes into NBA 3.1: what we build, from which data, in which order, how we test it, and when it is ready  
**Builds on:** the five individual plan files (Lab, Dx, Rx, Px, DM/HF Flags), the full HCP universe run of 2026-11-02 (`Combine Files/NBA_3_1_E2E_Full_Run_2026_11_02.md`), and the proposals document (`NBA_3_1_Patient_Journey_Changes_Proposals.md`)  
**Status:** Phase A built and run (validation + full universe). Phase B (new features) and team reviews pending.  
**Date:** November 3, 2026

This file combines the full detail of each individual plan. The original plan files remain in their folders for reference.

---

## 1. In short

* **The patient journey is rebuilt in five notebooks (PJ01–PJ05) and combined in PJ06.** Each notebook keeps the 3.0 query as a baseline, adds one step at a time, and compares each step row by row with the one before. Every rule that was hardcoded in SQL is moved to a basket CSV, a settings block, or a code-rules block.
* **Phase A is complete.** Validation run (10 test HCPs) and full HCP universe run (294,726 HCPs, 148.0M patients) both succeeded. The six tasks run as one Lakeflow Job in about 35 minutes.
* **Results are almost unchanged for validation HCPs.** 98.5% of shared patient-months keep the same eligibility. The differences that do appear are all corrections: stage 5 / ESRD codes now read, dialysis found or dated more accurately, lab stage no longer hidden by Dx stage 0.
* **The SGLT2 rule issue (C1) is the most important open decision.** 56% of eligible months have no known stage and never an SGLT2. The rule is meant to exclude them, but a bug (copied from 3.0) means it never applies. Fixing it roughly halves the eligible population.
* **Diabetes is not required for eligibility (C9).** 58% of eligible months belong to patients with no T1D or T2D diagnosis. If the Kerendia indication means CKD with T2D, they should not be eligible.
* **One baseline question (B1):** the 3.0 production combine used only ~18% of the 3.0 lab stages. Most of the full-scale eligibility difference comes from this, not from the 3.1 lab logic. Needs confirmation from Wenjie's 3.0 Ops combine notebook.
* **New in 3.1:** diabetes type (`DM_TYPE`), heart failure (`HF_FLAG`, `HF_TYPE`, `HF_FIRST_DATE`), and a monthly HF flag in the eligibility table. They are reported but do not change eligibility yet (that needs the 3.1 rules per indication, C3).

---

## 2. What we learned (the evidence behind this plan)

| Topic | Finding | Consequence for NBA 3.1 | Source |
| --- | --- | --- | --- |
| Lab (PJ01) | 3.0 had all rules in SQL (test names, cut-offs, dates, specialties, table names); UACR components were staged as results; eGFR 150–200 = stage 0 | Move rules to basket CSV; `ROLE = PART` for components; valid range 1–200 | Lab plan sections 2–3 |
| Lab result | 99.9% of eGFR and 99.5% of UACR test-days unchanged; +35.7K eGFR test-days gained (`>90`, `75^`); 19% less data pulled | Phase A complete; write is on | Lab plan section 7 |
| Dx (PJ02) | 3.0 staged from description text; stage 3a/3b and stage 5 codes not read; every patient had rows before first diagnosis; stage 0 hid the lab stage | Stage from code; start at first CKD Dx; null instead of 0; `DX_CKD_FLAG` added | Dx plan sections 2–4 |
| Dx result | Stage 3 (0 → 690 patients) and stage 5 (0 → 326) now appear on 10 HCPs; 14.3M months / 0.99M patients excluded as stage 5 at full scale | Phase A complete; biggest real 3.1 correction | E2E section 4.1 |
| Rx (PJ03) | 3.0 product list in SQL; fills before start date not counted; Kerendia, generic dapagliflozin, GLP-1s not in the view | Basket from CSV; 97-day look-back; Phase B for missing drugs | Rx plan sections 2–3 |
| Rx result | 98.8% of shared months same drug classes; look-back adds Dec 2022–Mar 2023 months | Phase A complete; write off until Dx goes live | Rx plan section 0 |
| Px (PJ05) | 3.0 used `%DIALYSIS%` text match; missed ESRD monthly codes; access procedures counted as dialysis | Basket with `PX_GROUP` and `ACTIVE_DIALYSIS`; access excluded (D1) | Px plan sections 2–5 |
| Px result | 1,537,460 vs 1,489,202 patients with dialysis date; 525,674 have ESRD monthly as first event | Phase A complete; write off until Dx goes live | E2E section 7 |
| Flags (PJ04) | 3.0 had only "diabetic yes/no"; no T1D, no HF; SGLT2 alone made a patient T2D | New `DM_TYPE`, `HF_FLAG`, `HF_TYPE`, `HF_FIRST_DATE`; SGLT2 alone no longer T2D (D1) | Flags plan sections 2–3 |
| Flags result | 73.6M T2D (was 77.3M), 1.9M T1D, 23.8M HF; 0 differences vs independent recount | Phase A complete; write off until Dx goes live | E2E section 7 |
| Combine (PJ06) | SGLT2 rule never applies (compares stage with -1); 3.0 diabetic flag joined but never used; `COALESCE(DX_STAGE, GFR_STAGE)` returned 0 when Dx was 0 | Fix SGLT2 rule (C1); null instead of 0 lets lab stage show; add `HF_FLAG` and `DM_TYPE` | E2E sections 6, 8 |
| Full run | 148.0M patients, 3.17B eligible months, 77.5M eligible patients in Sep 2026; 56% of eligible months have no known stage; 58% have no diabetes | C1 and C9 are the biggest decisions; B1 explains the gap with 3.0 | E2E section 10 |
| 3.0 baseline (B1) | 3.0 full combine carries a lab stage in only ~18% of 3.0 lab-journey months | Most full-scale differences are a 3.0 baseline artefact, not 3.1 | E2E section 4.2 |

---

## 3. The five notebooks and what they do

| Notebook | Folder | What it builds | Basket file | Key output columns | Plan file |
| --- | --- | --- | --- | --- | --- |
| **PJ01 Lab** | `Lab Files/` | eGFR and UACR stages from Quest lab data | `Kerendia_Lab_Final.csv` (28 rows) | `PATIENT_ID, DATE, GFR_STAGE, UACR_STAGE` | `NBA_3_1_Lab_Journey_Plan.md` |
| **PJ02 Dx** | `Dx Files/` | CKD stage from diagnosis codes | `Kerendia_Dx_Final.csv` (240 rows, 31 staging codes) | `PATIENT_ID, DATE, DX_STAGE_UPDATED, DX_CKD_FLAG` | `NBA_3_1_Dx_Journey_Plan.md` |
| **PJ03 Rx** | `Rx Files/` | Treatment categories and brand labels from prescription fills | `Kerendia_Rx_Final.csv` (367 rows, 254 active) | `PATIENT_ID, DATE, TREATMENT_CATEGORY, CATEGORY` | `NBA_3_1_Rx_Journey_Plan.md` |
| **PJ04 Flags** | `T2D-T1D-HF Files/` | Diabetes type and heart failure flags | `Kerendia_Dx_Final.csv` + `Kerendia_Dx_Flag_Additions.csv` (116 codes) | `PATIENT_ID, T2D_FLAG_30, DM_TYPE, T1D_FLAG, HF_FLAG, HF_TYPE, HF_FIRST_DATE` | `NBA_3_1_DM_HF_Flags_Plan.md` |
| **PJ05 Px** | `Px Files/` | First dialysis date | `Kerendia_Px_Final.csv` (145 rows, 29 dialysis codes) | `PATIENT_ID, FIRST_DIALYSIS_DATE, FIRST_DIALYSIS_CODE, FIRST_DIALYSIS_GROUP` | `NBA_3_1_Px_Journey_Plan.md` |
| **PJ06 Combine** | `Combine Files/` | Eligibility table: joins all five, sets stage and dialysis flag | – | `PATIENT_ID, SVC_DT_M, ELIGIBLE_PATIENT_FLAG, GFR_UACR_DX_STAGE, HF_FLAG, DM_TYPE` | `NBA_3_1_E2E_Full_Run_2026_11_02.md` |

**Run order:** PJ01, PJ02, PJ03 in parallel; PJ04 and PJ05 after them (they use the patient set); PJ06 last.

---

## 4. PJ01 Lab patient journey

**Notebook:** `Lab Files/01_patient_journey_labs` (33 cells)  
**Old notebook:** `Lab Files/(Clone) 01_patient_journey_labs` (12 cells; pre-built input table removed in 2026-10-26 refresh)  
**Basket:** `Final Product Basket/Kerendia_Lab_Final.csv` (28 rows = 23 LOINC codes + 5 test-name backups)  
**Downstream:** `06_patient_journey_combine` (`GFR_STAGE`, `UACR_STAGE` feed `GFR_UACR_DX_STAGE`)  
**Full plan:** `Lab Files/NBA_3_1_Lab_Journey_Plan.md`

### 4.1 Current notebook (3.0)

| Cell | What it does |
| --- | --- |
| 1 | Header (out of date: lists `IQV_QUEST_LAB`, dates 2017) |
| 2 | `00_connection`, `00_cohort_config` (path broken since the move to `Lab Files`) |
| 3 | **Load:** reads a pre-built Delta table `kerendia_nba_3_0_lab_query_output` (removed in the 2026-10-26 refresh) |
| 4 | **Cleanup:** month sequence between tests, forward fill, max per patient-cohort-month, cohort label join |
| 5–7 | Comparison with production, write `kerendia_nba_3_1_lab_journey_validation` |

The lab rules were not visible in this notebook: they lived in the 3.0 query that built the input table.

New notebook (33 cells): header + optimization summary; setup; 3.0 baseline query (direct from Snowflake); Step 1 markdown inventory; Step 2 basket (2a–2e); Step 3 config (3a–3e); Step 4 code rules (4a–4e); cleanup, comparison, write.

Output columns: `PATIENT_ID, DATE, GFR_STAGE, UACR_STAGE, cohort_label`.

### 4.2 Bottlenecks found in the 3.0 query

| # | Hardcoded / issue | Effect | Fix goes in |
| --- | --- | --- | --- |
| Q1 | **Test identification by name text only** (`%GFR%`, `%GLOMERULAR%`, `%ALB%`, `%RATIO%`) | Renamed tests are lost; unrelated tests with "ALB" or "RATIO" included | Basket (LOINC codes + name backup) |
| Q2 | **Stage cut-offs written in the SQL** | Changing a cut-off means editing the SQL | Basket (`STAGE_CUTOFFS` column) |
| Q3 | **Units: one list shared by both tests** | A UACR unit can pass for eGFR and vice versa | Basket (one unit list per test) |
| Q4 | **Valid range: none. eGFR > 150 = stage 0, eGFR = 0 = stage 5** | Invalid values get a wrong stage | Basket (`VALID_MIN` / `VALID_MAX`) |
| Q5 | **Same-day aggregation: median of all eGFR equations** | Black and non-Black equations mixed | Basket (`PRIORITY` column) |
| Q6 | **Value format: plain numbers only** | `75^` and `>90` dropped; lab flags lose valid results | Code (`VALUE_RULES`) |
| Q7 | **Start date written twice** (`2021-11-30` + `DATA_START_DATE`) | Conflicting dates | Config (`LAB_CONFIG`) |
| Q8 | **End date applied after pulling all history** | 19% more data pulled than needed | Config (dates inside the SQL) |
| Q9 | **Date formats in a fixed `CASE`** | A new format fails silently | Config (`TRY_TO_DATE` over a format list) |
| Q10 | **Specialty filter: 10 primary-care codes in the SQL** | 211.4M eGFR rows excluded (largest single exclusion) | Config (`LAB_CONFIG`) |
| Q11 | **Table and column names in the SQL** | A rename breaks the query | Config (`LAB_CONFIG`) |
| Q12 | **No dropped-rows report** | Losses are silent | Code (Step 4b report) |
| Q13 | **UACR components staged as results** | Urine creatinine, serum albumin etc. get UACR stages (wrong) | Basket (`ROLE = PART`) |
| Q14 | **eGFR 150–200 = stage 0** | Valid stage 1 results treated as invalid | Basket (valid range extended to 200) |
| Q15 | **Patient ID rule in the SQL** | Not visible, not checked | Code (`PATIENT_ID_RULE`) |

### 4.3 Lab basket design (`Kerendia_Lab_Final.csv`)

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

**Switched off (`ACTIVE = N`):** Potassium (LOINC 2823-3, MMOL/L, 1–10); HbA1c (LOINC 4548-4, %, 3–20). Both for Phase B.

### 4.4 Build plan

| Step | What | Comparison / check | Expected result |
| --- | --- | --- | --- |
| 0 | Copy old notebook; rewrite header; run 3.0 SQL directly from Snowflake | Same output as old notebook (10 HCPs) | Identical |
| 1 | Markdown inventory of 15 hardcoded parts | Review only | – |
| 2 | **Basket:** read `Kerendia_Lab_Final.csv`, checks, build SQL from basket; stage from `STAGE_CUTOFFS`; UACR parts excluded by `ROLE` | Part A all US (test-days): same / different / lost / gained. Part B 10 HCPs | eGFR 99.9% same; UACR 99.5% same |
| 3 | **Config:** `LAB_CONFIG` (dates in SQL, specialty filter, date formats, table/column names); checks tables/columns exist | Part A identical; rows pulled before/after | Same output, 19% less data |
| 4 | **Code rules and report:** `VALUE_RULES`, `PATIENT_ID_RULE`, dropped-rows report | Part A identical + gains; Part B validation; Part C report | +35.7K eGFR test-days gained; losses visible |
| 5 | Cleanup: same logic as 3.0, now on Step 4 output | Patient-months and stage counts vs 3.0 | No change for validation HCPs; +26 months with eGFR stage |
| 6 | Write `kerendia_nba_3_1_lab_journey_validation` | Write succeeds | Done |

### 4.5 Run settings (`LAB_CONFIG`)

| Setting | 3.0 | Now |
| --- | --- | --- |
| Start date | `'2021-11-30'` in SQL + `DATA_START_DATE` in Spark | `DATA_START_DATE` only, inside the SQL |
| End date | Applied in Spark after pulling all history | Inside the SQL |
| Specialties | 10 primary-care codes in SQL | Same list in config; `None` = no filter |
| Date formats | `CASE` with `TO_DATE` | `TRY_TO_DATE` over a format list |
| Source table | `PHCDW_SANDBOX.IQV_QUEST_LAB` | Same, in config (checked before run) |
| Provider table | `STG_IQVIA_LAAD_DIM_PRVDR` | Same, in config (checked before run) |

### 4.6 Dropped-rows report (new in 3.1)

All US, 2023-01 to 2026-09, source rows.

| Reason | eGFR rows | UACR rows | Can be recovered? |
| --- | --- | --- | --- |
| Patient ID missing or invalid | 65.6M | 11.8M | No |
| Prescriber NPI missing | 24.3M | 3.8M | No |
| Component of a test, not a result | – | 16.0M | No (by design) |
| Value empty or text | 12.3M | 6.8M | No |
| Unit not allowed | – | 32.8K | Possibly |
| Outside valid range | 4.6M | 26.2K | No |
| `>` / `<` value with unclear stage | 827K | 314 | Decision (L2) |
| **Specialty not in the 10 codes** | **211.4M** | **21.2M** | **Decision (L1)** |
| **Kept** | **631.9M** | **106.9M** | – |

### 4.7 Validation results

**All US, 2025-01 to 2026-09 (test-days):**

| Result | eGFR | UACR |
| --- | --- | --- |
| Same stage as 3.0 | 106.73M (99.9%) | 19.81M (99.5%) |
| Stage changed | 65.3K (0.06%) | 27.4K (0.14%) |
| No longer included | 260 (above 200 or = 0) | 71.0K (68.4K components, 2.5K above 10,000) |
| Newly included | +35.7K (26.8K patients) | +1.3K |

**Validation HCPs (10 doctors):** 225 patients, 878 eGFR test-days, 289 UACR test-days, 6,139 patient-months — all unchanged. +26 months with eGFR stage (150–200 now stage 1).

**Full universe:** 1.75B rows, 64.6M patients (3.0: 2.21B, 65.6M).

**Run efficiency:** 312.9M → 252.2M rows pulled (−19%); 38 empty dates, 0 unknown format.

### 4.8 Decisions

**Made:**

| # | Decision | Choice | Reason |
| --- | --- | --- | --- |
| L-D1 | eGFR valid maximum | 200 (was 150) | Values 150–200 are stage 1 |
| L-D2 | Source of lab test rules | One lab test list (CSV) | Single place for all test rules |
| L-D3 | Test-name backup | Kept | Rows without a LOINC code still found |
| L-D4 | Same-day results | Lowest priority wins; exact beats `>` / `<` | Uses preferred eGFR equation |
| L-D5 | Lab flags (`^`) | Read as the number | Valid results not lost |
| L-D6 | UACR components | `ROLE = PART`, never staged | Not ratios; staging gives wrong UACR |
| L-D7 | Basket file name | `Kerendia_Lab_Final.csv` | Consistent with Dx, Rx, Px |
| L-D8 | Cleanup on Step 4 output | Switched from `df_lab` to `df_lab_step4` | New query connected to written table |

**Open:**

| # | Decision | Options | Impact | Status |
| --- | --- | --- | --- | --- |
| L1 | **Specialty filter** | (a) keep 10 codes, (b) remove, (c) add cardiology/endo/nephro | Removing adds ~16% eGFR, ~13% UACR patients | Open |
| L2 | **`>60` eGFR** (827K rows) | (a) keep excluded, (b) count as "not CKD 3+" | (b) adds unlikely CKD patients | Open |
| L3 | **Config location** | (a) lab notebook, (b) shared config | (b) shares settings with other notebooks | Open |

### 4.9 Phase B: planned lab additions

| What | What it means | Priority |
| --- | --- | --- |
| Switch on Potassium (2823-3) | Last value; flag > 5.0 mmol/L for "Kerendia-ready" and hyperkalemia | High |
| Switch on HbA1c (4548-4) | Last value; flag at 9%+ (uncontrolled diabetes) | Medium |
| Missing codes 14959-1, 48643-1 | Add rows to existing tests | Low |
| Lab-based CKD flag | Two eGFR < 60 or two UACR >= 30, 90 days apart (KDIGO) | Medium |
| eGFR value and decline | Last value; 30%+ fall within 24 months | Medium |
| CKD stage 3a / 3b split | eGFR 45–59 = 3a, 30–44 = 3b | Low |
| Lab testing from procedure claims | CPT codes for HCPs without Quest data | Medium |
| LabCorp | Second lab source | Low |

All value-based features require the result value in the output (today only stages are kept).

---

## 5. PJ02 Dx patient journey

**Notebook:** `Dx Files/02_patient_journey_dx`  
**Old notebook:** `Dx Files/(Clone) 02_patient_journey_dx`  
**Basket:** `Final Product Basket/Kerendia_Dx_Final.csv` (240 rows = 368 codes; 31 staging codes)  
**Downstream:** `06_patient_journey_combine` (`DX_STAGE_UPDATED` feeds `GFR_DX_STAGE` and `GFR_UACR_DX_STAGE`)  
**Full plan:** `Dx Files/NBA_3_1_Dx_Journey_Plan.md`

### 5.1 Current notebook (3.0)

| Cell | What it does |
| --- | --- |
| 1–2 | Header (out of date: lists `IQV_LAAD_DX_VW`, `DIM_PRODUCT`, dates 2016/2017) |
| 3–5 | `00_connection`, `00_config`, `00_cohort_config` |
| 6 | **3.0 Dx query** from Snowflake, HCP universe join, validation filter |
| 7–10 | QC cells, all commented out |
| 12 | Monthly patient journey: patients × all cohort-months grid, max stage per month, stage 0 → null, forward fill, null → 0, cohort label |
| 13–16 | Rename, drop, print shape, cast `DATE` |
| 17 | Compare with production `df_dx_combine` |
| 18 | Write `kerendia_nba_3_1_dx_journey_validation` |

Output columns: `PATIENT_ID, DATE, DX_STAGE (array), DX_STAGE_UPDATED, cohort_label`.

The 3.0 query: reads all of `STG_CAR_IQV_LAAD_FACT_DX`; joins demographics and provider on `COALESCE(REFERRING, RENDERING)`; inner-joins `DIM_DIAGNOSIS` filtered to **163 codes**; sets stage from **description text** (`CATEGORY = 'CHRONIC KIDNEY DISEASE, STAGE 1'` → 1, etc.); filters months by `YEAR*100 + MONTH`.

### 5.2 Bottlenecks found

| # | Hardcoded / issue | Effect | Fix goes in |
| --- | --- | --- | --- |
| Q1 | **163-code list typed in the SQL** | Adding/removing a code means editing SQL | Basket |
| Q2 | **131 of 163 codes cannot match:** 32 ICD-9 (retired 2015) and 99 procedure codes reformatted as diagnoses | Can only match by accident; intent (dialysis/transplant) belongs in Px | Basket; move to Px |
| Q3 | **Stage from description text, not code** | `N18.30/31/32` (stage 3a/3b, ~9.6M patients) and stage 5 codes not in list. **For 10 HCPs: 0 stage-3 and 0 stage-5 Dx patients** | Basket (stage per code) |
| Q4 | Header codes and non-basket codes | Small volume; not in 3.1 basket | Basket |
| Q5 | **Descriptions cut at 100 characters** | Text match on descriptions is fragile | Basket (codes as key) |
| Q6 | **Date filter** `EXTRACT(YEAR)*100 + EXTRACT(MONTH)` on every row | Cannot skip data; number vs string comparison | Config |
| Q7 | **Unused join:** demographics (birth year, gender) joined but never used | Extra cost on largest table | Code |
| Q8 | **Table and column names in SQL** | A rename breaks the query | Config |
| Q9 | **Provider rule** `COALESCE(REFERRING, RENDERING)` typed twice | Choice not visible | Config |
| Q10 | **`DIAGNOSIS_CODE` not in output** | No QC by code | Code |
| Q11 | **No dropped-rows report** | Losses silent | Code |
| C1 | **Dense grid:** every patient × every month from global first to last | Very large for all US; rows before first diagnosis | Start at first Dx month |
| C2 | **Stage 0 means two things:** "CKD stage unknown" and "before any diagnosis" | Downstream can't tell; in PJ06 the 0 hides lab stage | Null when no stage known + `DX_CKD_FLAG` |
| C3 | Grid ends at max service date, not `date_end` | End month depends on data | Use `date_end` |
| C4 | Self-join to add `DX_STAGE_UPDATED` | Extra join with no need | One window column |
| C5 | `DX_STAGE` kept as array | Hard to use | Replace with `DX_STAGE_MONTH` |

### 5.3 New basket design (`Kerendia_Dx_Final.csv`)

One row per real ICD-10 code (clubbed rows expanded).

| Column | Values | Purpose |
| --- | --- | --- |
| `DIAGNOSIS_CODE` | e.g. `N18.31` | Match key (exact code) |
| `DIAGNOSIS_DESCRIPTION` | From current basket | Reference only, never used to match |
| `CONDITION` | `CKD`, `T2D`, `T1D`, `OTHER_DM`, `HF`, `DIALYSIS`, `TRANSPLANT`, `ANEMIA_CKD`, `PVD`, `CARDIOMYOPATHY`, `HTN_SECONDARY`, `DM_TREATMENT`, `PROTEINURIA`, `OTHER` | Groups codes for journey and flags |
| `ACTIVE_STAGING` | `Y` / `N` | `Y` = used by PJ02 (CKD subset, D1) |
| `CKD_STAGE` | `1`–`5`, `0` = unknown, empty = not CKD | Replaces description-text `CASE` |
| `CKD_SUBSTAGE` | `3a`, `3b`, `ESRD`, empty | For stage 3a/3b and ESRD features |
| `DM_TYPE` | `T2D` (E11), `T1D` (E10), `OTHER` (E08/E09/E13), empty | Diabetes type on every diabetes code (feeds PJ04) |
| `HF_TYPE` | `HFPEF_PROXY`, `HFREF_PROXY`, `COMBINED`, `UNKNOWN`, empty | HF type proxy for LVEF >= 40% indication |
| `FLAG` | `DIALYSIS`, `TRANSPLANT`, `HF`, `T2D`, ... or empty | Feeds planned patient flags |
| `IS_DEFINING` | `Y` / `N` (cleaned) | From current basket |
| `CLUB_ID` | e.g. `E11.3x` or empty | Link to original clubbed row |
| `PATIENTS_TOTAL` | From current basket | Reference |
| `NOTE` | Free text | Why a code has this stage or role |

**Proposed `CKD_STAGE` values:**

| Stage | Codes |
| --- | --- |
| 1 | N18.1 |
| 2 | N18.2 |
| 3 | N18.3, N18.30, N18.31 (3a), N18.32 (3b) |
| 4 | N18.4 |
| 5 | N18.5, N18.6 (ESRD), I12.0, I13.11, I13.2 |
| 0 (unknown) | N18.9, I12.9, I13.0, I13.10, E11.21, E11.22, E11.29, **E10.21, E10.22, E10.29** (D2), E08.21/22/29, E13.21/22/29, E09.22, D63.1, Z99.2 (`FLAG = DIALYSIS`, D4) |
| Not staged, flag only | Z49.01/02/31/32 (`FLAG = DIALYSIS`); Z48.22 (`FLAG = TRANSPLANT`); R80.9 (`FLAG = PROTEINURIA`); I15.1, I70.1 (kidney/CV comorbidity) |
| Not staged (`ACTIVE_STAGING = N`) | All other codes: T2D, T1D, other diabetes without kidney involvement, HF without CKD, PVD, ... (D1). They keep `DM_TYPE` / `HF_TYPE` / `FLAG` for Phases B–C |

### 5.4 Build plan

| Step | What | Comparison / check | Expected result |
| --- | --- | --- | --- |
| 0 | Copy old notebook; rewrite header; remove dead QC cells; keep cell 6 as 3.0 baseline | Same output as old notebook (10 HCPs) | Identical |
| 1 | Markdown inventory of hardcoded parts | Review only | – |
| 2 | **Basket:** read `Kerendia_Dx_Final.csv`, checks, build query from basket; stage from `CKD_STAGE` by code; keep `DIAGNOSIS_CODE` | Part A all US: same / different stage / lost / gained, by code. Part B 10 HCPs + stage crosstab | Stage 3 (0→690) and 5 (0→326) appear; dead codes lose nothing |
| 3 | **Config:** `DX_CONFIG` (dates in SQL, table/column names, provider rule); checks tables/columns; remove unused demographics join | Part A identical to Step 2; rows pulled before/after | Same output, less data pulled |
| 4 | **Code rules and report:** dropped-rows report (no provider, not in HCP universe, code not in basket, outside dates); output columns follow basket | Part A identical to Step 3; report totals | Losses visible |
| 5 | **Processing:** per-patient month range (first CKD Dx → `date_end`, N2), one window for forward fill, `DX_STAGE_UPDATED` null when no stage + `DX_CKD_FLAG` (N1), replace `DX_STAGE` array | Patient-months and stage counts vs Step 4; simulate PJ06 `COALESCE` and count where lab stage now shows | Fewer rows (no pre-diagnosis months); lab stage no longer hidden |
| 6 | Switch to Step 5 output (after review), write | Write succeeds; schema check | – |
| 7 | Downstream: PJ06 re-run; HCP `Dx_03` with same basket; Phase B (T2D/T1D flags from `DM_TYPE`); Phase C (`HF_FLAG` + `HF_TYPE`); Phase D (PJ06 eligibility per indication) | Stage counts before/after in PJ06 and NB03 | – |

### 5.5 Implementation results

| Step | Check | Result |
| --- | --- | --- |
| 0 | 3.0 query + processing vs table last written | Identical: 37,582 patient-months, 817 patients, 0 differences |
| 2a | Basket vs original Dx Event List | Same 368 codes, same patient counts and flags |
| 2 | Basket query vs 3.0, all US | Same 70.9M; different 79.4M (all upward: 0→5 52.2M, 0→3 26.8M); gained 37.1M; lost 2,612 (E09.21/29, header, ICD-9) |
| 2 | Validation HCPs | Patients 817 → 1,163; stage 3: 0 → 690, stage 5: 0 → 326 |
| 3 | Config query vs Step 2 | Identical rows (368.3M all US; 70,892 validation); 29% fewer rows from Snowflake |
| 4 | Output + dropped-rows report | Identical rows; report: before start 27.2%, no provider 12.1%, not in HCP universe 24.9%, kept 35.7% |
| 5 | 3.1 processing vs 3.0 (same input) | 33,102 same stage; 5,873 months 0 → null; 14,523 months before first Dx removed; 0 stage changes |

**Full universe:** 497.7M rows, 16.7M patients (3.0: 409.2M, 16.0M).

### 5.6 Decisions

| # | Decision | Default | Alternative |
| --- | --- | --- | --- |
| D1 | PJ02 uses only CKD subset of basket | **Decided: yes.** Only codes with CKD stage (0–5) have `ACTIVE_STAGING = Y` | Use full basket (rejected: millions of non-CKD patients) |
| D2 | T1D kidney codes E10.21/22/29 | **Decided: include as stage 0** with `DM_TYPE = T1D` | Exclude (rejected) |
| D3 | ESRD codes | **Decided: stage 5**, `CKD_SUBSTAGE = ESRD` for N18.6 | Separate value 6 (rejected: makes ESRD eligible) |
| D4 | Z99.2 (dialysis dependence) | **Decided: stage 0** and `FLAG = DIALYSIS` | Stage 5 (rejected) |
| D5a | Z49.01/02/31/32, Z48.22 | **Decided: not staged.** Z49 → `FLAG = DIALYSIS`; Z48.22 → `FLAG = TRANSPLANT` | Add to staging (rejected) |
| D5b | R80.9, I15.1, I70.1 | **Decided: not staged.** Kept for flags: proteinuria, kidney/CV comorbidity | Add to staging (rejected) |
| N1 | Meaning of 0 vs null | **Decided: fix in PJ02.** `DX_STAGE_UPDATED` = null when no stage known; new `DX_CKD_FLAG` = 1 | Treat 0 as null in PJ06 (not chosen) |
| N2 | Per-patient month range | **Decided: yes.** Each patient from first CKD Dx to `date_end` | Keep global grid (rejected) |
| N3 | Provider rule | **Decided: keep** `COALESCE(REFERRING, RENDERING)` | Rendering first (rejected) |
| N4 | Basket file name | **Decided:** `Kerendia_Dx_Final.csv` | Other name (rejected) |

**Open:** X1 (Dx end-to-end review with Saurabh); X2 (latest staged Dx wins — 906 months 4→3, 424 months 2→3); X3–X6 (see Dx plan).

### 5.7 Downstream use of the Dx stage (checked 2026-10-29, by reading the code)

| Where | How stage 5 is used | What a value 6 would do |
| --- | --- | --- |
| PJ06 cell 7 | `GFR_DX_STAGE = COALESCE(DX_STAGE_UPDATED, GFR_STAGE)`; `GFR_UACR_DX_STAGE = COALESCE(DX, GFR, UACR)`. Dx stage wins over lab when not null | 6 passes through into the combined stage |
| PJ06 cell 18 (eligibility) | `STAGE_ELIGIBLE`: null/0 → −1 (unknown); **1 or 5 → 0 (not eligible)**; otherwise → 1 (eligible). `DIALYSIS_FLAG = 1` → not eligible. Labels: only `STAGE_2/3/4`, everything else `STAGE_UNKNOWN` | Stage 5 = not eligible. **6 → eligible** (falls into "otherwise"). Wrong |
| NB03 | `DX_STAGE` 1–5 → `STAGE_1`…`STAGE_5`, else `STAGE_UNSPECIFIED` | 6 → `STAGE_UNSPECIFIED` (silently lost) |
| NB04 | `gfr_label`: 1–5 → `GFR_STAGE_1`…`_5`, else `GFR_STAGE_UNKNOWN` | 6 → `GFR_STAGE_UNKNOWN` (silently lost) |

**Conclusion for D3:** ESRD = stage 5. Every consumer handles 1–5 only; a value 6 would make ESRD patients eligible in PJ06 and drop them into "unknown" in NB03/NB04 features.

**Important for N1/N2:** in 3.0, every Dx patient has a row for every month (global grid) with nulls filled as 0. Because PJ06 uses `COALESCE(DX_STAGE_UPDATED, GFR_STAGE)`, a Dx value of 0 is not null, so it hides the lab stage. A patient with only N18.9 (stage unknown) and a lab eGFR of stage 3 ends up with `GFR_DX_STAGE = 0` ("unknown" in eligibility). **Fix (N1):** PJ02 outputs null instead of 0 when no stage is known, plus `DX_CKD_FLAG`. In PJ06, null Dx + null lab still gives "unknown" (−1), the same as 0 today, so only the hidden-lab cases change.

### 5.8 New indications: 4-phase plan

| Phase | Notebook | What changes | When |
| --- | --- | --- | --- |
| A | PJ02 + basket | E10.21/22/29 become stage 0 (D2). New basket columns `DM_TYPE` and `HF_TYPE` | Done |
| B | PJ04 | T2D / T1D flags from `DM_TYPE` | Done |
| C | PJ04 + PJ05 | HF flag + HF type; dialysis / transplant flags | Done (flags); Phase B (Px procedures) |
| D | PJ06 | Eligibility per indication (T2D + CKD, T1D + CKD, HF) | Open (C3, needs Medical) |

---

## 6. PJ03 Rx patient journey

**Notebook:** `Rx Files/03_patient_journey_rx`  
**Old notebook:** `Rx Files/(Clone) 03_patient_journey_rx` (frozen 3.0 baseline)  
**Basket:** `Final Product Basket/Kerendia_Rx_Final.csv` (367 rows, 254 active); original kept as `Kerendia NBA 3.1 - RX Event List.csv`  
**Downstream:** `06_patient_journey_combine` (SGLT2 flag, treatment counts, brand lists)  
**Full plan:** `Rx Files/NBA_3_1_Rx_Journey_Plan.md`

### 6.1 Current notebook (3.0)

| Cell | What it does |
| --- | --- |
| 1 | Header (out of date: names `IQV_LAAD_RX_VW`, dates 2017) |
| 3–5 | `00_connection`, `00_config`, `00_cohort_config` (path broken since move to `Rx Files`) |
| 8 | **Step 1:** pulls 5 full tables into Spark (`SELECT *`): Rx fact, demographics, provider, product, plan; plus HCP universe and view `CKD_PRODUCT_MAPPING_VW` |
| 9 | **Step 2:** joins them; keeps `SVC_DT >= DATA_START_DATE`, NPI not empty, view category not "other"; validation filter |
| 10 | **Step 3:** `END_DT = SVC_DT + days supply + 7`, capped at last Rx date |
| 11 | **Step 4:** brand label `CATEGORY`: Invokana by strength, Jardiance, Farxiga, 23 DPP-IV names, 19 GLP-1 names; else view category |
| 12 | **Step 5:** one row per day from `SVC_DT` to `END_DT`, then cohort month |
| 13 | **Step 6:** per patient and cohort month, the set of view categories (`TREATMENT_CATEGORY`) and brand labels (`CATEGORY`) |
| 15–19 | Rename, write `kerendia_nba_3_1_rx_journey_validation` |

Output columns: `PATIENT_ID, DATE, TREATMENT_CATEGORY (array), CATEGORY (array), cohort_label`.

`06_patient_journey_combine`:
* Full join with lab and Dx journeys on `PATIENT_ID, DATE`.
* **SGLT2 flag:** a patient with any month where `TREATMENT_CATEGORY` contains `SGLT2` gets `SGLT2_FLAG = 1`. When CKD stage is unknown, an SGLT2 patient counts as eligible.
* Treatment counts per month (`TOTAL_TREATMENTS`, new treatments) and the brand list (`CATEGORY` → `BRAND`).

### 6.2 Bottlenecks found

| # | Hardcoded / issue | Effect | Fix goes in |
| --- | --- | --- | --- |
| R1 | **Which drugs count and their category** come from a Snowflake view (`CKD_PRODUCT_MAPPING_VW`), matched on product name | Rules live outside the project; not visible in the basket; a new drug needs a change in someone else's view | Basket |
| R2 | **Categories with "other" excluded** by text match | A category renamed or added to the view changes the result silently | Basket (active flag) |
| R3 | **Brand labels typed in the code:** Invokana by strength, Jardiance, Farxiga, 23 DPP-IV names, 19 GLP-1 names | Lists can only label products already in the view; a name not in the view is never labelled | Basket (brand label column) |
| R4 | **Newer GLP-1s not in the list:** Mounjaro, Zepbound, Wegovy (among the largest products) | Not labelled GLP-1; to measure whether the view keeps them at all | Phase A: measure; Phase B: decide (D3) |
| R5 | **Rx basket not used and not aligned:** its groups do not match the journey categories | Two different code lists for the same thing | Basket (new columns, D1) |
| R6 | **Product names cut at 25 characters** in the basket | Matching on name may fail | Basket check |
| R7 | **7 grace days; end date = last date in Rx table** (not `date_end`); start = `DATA_START_DATE` on the fill date | Run window not aligned with other journeys; first months under-counted | Config (D4, D5) |
| R8 | **Joins that remove or add nothing:** demographics (left join, never used); plan table (inner join: drops fills whose plan is not in the plan table) | Extra work; silent loss | Code (D6) |
| R9 | **Five full tables pulled into Spark** (`SELECT *`) and filtered there | Slow and heavy; filters could run in Snowflake | Config + code (D7) |
| R10 | **Table names, HCP universe path and output path typed in full** | A rename breaks the notebook | Config |
| R11 | **No dropped-rows report** | Losses are silent | Code |
| R12 | **Brand label only for some SGLT2s:** combo products and new SGLT2s get the view category only; Kerendia has no label of its own | Kerendia and combo use not visible per brand | Basket (Phase A: measure; Phase B: decide) |

### 6.3 New Rx basket (`Kerendia_Rx_Final.csv`)

Same style as the lab, Dx and Px baskets: one row per product or per clubbed group; all 258 rows kept; original file renamed `Kerendia NBA 3.1 - RX Event List.csv`.

| Column | Meaning |
| --- | --- |
| `MATCH_TYPE` | `NAME` (one product name) or `LIST` (clubbed group, names separated by `\|`) |
| `MATCH_VALUE` | Product name(s), exactly as in the IQVIA product table |
| `CLUB_ID` | Name of the clubbed group |
| `PRODUCT_GROUP` | Kept from the original basket |
| `TREATMENT_CATEGORY` | Journey category, same texts as 3.0 (`ACE/ ARB`, `SGLT2`, `MRA`, ...); empty = not in the journey |
| `BRAND_LABEL` | The 3.0 `CATEGORY` value (`JARDIANCE`, `FARXIGA`, `DPP-IV`, `GLP-1`, ...); empty = use `TREATMENT_CATEGORY` |
| `STRENGTH` | Only where the label depends on it (Invokana 100 / 300 MG) |
| `CONDITION` | CKD / HF / DM / T1D / HTN / OTHER |
| `ACTIVE_JOURNEY` | `Y` = in the Rx journey (Phase A: exactly the 3.0 products) |
| `PATIENTS_TOTAL`, `IN_752_FEATURES` | Kept from the original basket |
| `NOTE` | Why a row was added or changed |

Products in the view but not in the basket are added (marked in `NOTE`), so nothing is lost silently. Basket products not in the view get `ACTIVE_JOURNEY = N`.

**Key missing drugs (Phase B, D3):** Kerendia (446K patients since 2023), generic dapagliflozin (4.3M; brand Farxiga kept as SGLT2), Mounjaro (11.0M), Wegovy (4.3M), Zepbound (4.1M), generic sacubitril/valsartan (1.7M), nebivolol (1.5M). Ozempic (13.2M) and Trulicity (4.2M) are in the view but dropped as "Other-glucose mgmt".

### 6.4 Build plan

| Step | What | Comparison |
| --- | --- | --- |
| 0 | Run 3.0 code unchanged; compare with table last written | Patient-months and categories identical |
| 1 | Hardcoded-parts markdown + **profile**: the view, typed lists vs view, basket vs view, rows each filter removes | Facts for D1–D3 |
| 2 | **Basket:** product list, journey category and brand label from the new Rx basket; built to reproduce the view and typed lists exactly | vs 3.0: patient-months same / category added / removed, by product |
| 3 | **Config:** `RX_CONFIG` (tables, columns, dates, grace days, HCP universe); filters in Snowflake (one SQL instead of 5 full tables) | vs Step 2: identical expected, except end date and start look-back (D4) |
| 4 | **Code:** remove unused demographic join; dropped-rows report; output columns unchanged | vs Step 3; report of rows dropped by reason |
| 5 | **Write:** switched off; goes live with Dx / Px 3.1 tables | – |

### 6.5 Implementation results

| Step | Check | Result |
| --- | --- | --- |
| 0 | 3.0 code vs table last written | **Identical:** 107,616 patient-months, 3,645 patients, all "same"; 902 SGLT2 patients. 126,903 fills used |
| 1 | Profile: products in view, typed lists, basket | View: 476 names (254 kept, 222 in "Other"). 94 view products missing from basket; 186 basket names not kept. Funnel adds up (3.74B US fills) |
| 2 | Basket query vs 3.0 | **Identical.** New basket: 367 rows = 258 original + 13 split clubbed + 94 added (D2) + 2 Invokana strengths; 254 active. Validation: 126,903 fills, 107,616 patient-months all "same", 902 SGLT2 |
| 3 | Config query vs Step 2 | With 3.0 dates: identical. With `date_end`: 107,524 months (−92 from Oct fills). + 97-day look-back: 110,049 months (+2,525 new in Dec 2022–Mar 2023), 909 SGLT2 patients |
| 4 | Output + dropped-rows report | Identical to Step 3: 110,049 months all "same". Report (158,983 fills): kept 83.0%, no NPI 0.14%, after end 0.13%, before start 1.95%, not in HCP universe 14.79% |
| 5 | Write | `WRITE_OUTPUT = False`; nothing written |

### 6.6 Decisions

| # | Decision | Proposal | Why |
| --- | --- | --- | --- |
| D1 | Basket format | Section 6.3; original kept as `Kerendia NBA 3.1 - RX Event List.csv` | Same as Px; one place for drug rules |
| D2 | Parity source | Phase A reproduces the view + typed lists exactly; view products missing from the basket are added | Measure the basket effect alone; nothing lost silently |
| D3 | Newer GLP-1s, SGLT2 combos, Kerendia label | Phase A: measure only; Phase B: decide labels | Changes brand lists and treatment counts in PJ06; needs a business decision |
| D4 | Date window | End = `date_end`; start look-back: 97 days (90 supply + 7) before `DATA_START_DATE` | Aligns with other journeys; first months complete |
| D5 | Grace days | 7, moved to `RX_CONFIG` | Same rule, visible |
| D6 | Plan and demographic joins | Remove unused demographic join; keep plan join (removes 0 fills) | No silent loss |
| D7 | Speed | One Snowflake SQL with the filters, instead of 5 full tables in Spark | Faster; same result |
| D8 | Output and go-live | Same columns and category texts; write off until Dx / Px 3.1 tables go live; PJ06 unchanged | PJ06 depends on exact `SGLT2` text |

### 6.7 Phase B (later)

* HF drug groups: ARNI (Entresto, sacubitril/valsartan), ivabradine, vericiguat, SGLT2 for HF; MRA already exists.
* T1D signals: insulin pumps, CGMs, glucagon (already clubbed in the basket).
* GLP-1 / GIP-GLP-1 labels for Mounjaro, Zepbound, Wegovy; SGLT2 combo labels; Kerendia as its own label.
* CKD supportive drugs (iron, epoetin, phosphate binders) as signals of advanced CKD.

---

## 7. PJ04 Diabetes type and heart failure flags

**Notebook:** `T2D-T1D-HF Files/04_patient_journey_dm_hf_flags`  
**Old notebook:** `04_patient_journey_t2d_flag` (3.0, logic unchanged; only `%run` path updated)  
**Code lists:** `Kerendia_Dx_Final.csv` (read only, columns `DM_TYPE`, `HF_TYPE`) + `Kerendia_Dx_Flag_Additions.csv` (new, 116 codes)  
**Downstream:** `06_patient_journey_combine` (`DIABETIC_FLAG`, `HF_FLAG`, `DM_TYPE`)  
**Full plan:** `T2D-T1D-HF Files/NBA_3_1_DM_HF_Flags_Plan.md`

### 7.1 Old notebook: what it does

`04_patient_journey_t2d_flag` writes `kerendia_nba_3_1_t2d_patient_validation`: one row per patient, `DIABETIC_FLAG` = 1.

| Part | Rule |
| --- | --- |
| Dx | Any claim with a code whose description contains `TYPE 2 DIABETES` (word match on `STG_IQVIA_LAAD_DIM_DIAGNOSIS`), rendering provider present, any date |
| Dx sources | `PHCDW_DISCOVERY.STG_IQV_LAAD_DX` (until 2018-05-31) + `PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX` (from 2021-01-02) |
| Rx | Any claim of an NDC whose product is in `kerendia_pcp.diabetes_product` with `LOGIC = 1`, or `LOGIC = 2` and not an injection |
| Result | Dx OR Rx |

PJ06 joins this table as `DIABETIC_FLAG` (one row per patient).

### 7.2 Findings on the 3.0 logic

1. **No T1D.** T1D is not identified. A T1D patient with a single T2D claim, or with any drug from the 3.0 list, is counted as T2D: 1,165,299 of the 3.0 T2D patients have more T1D than T2D claim days.
2. **No HF.** There is no heart failure flag.
3. **SGLT2 alone.** 2,480,584 of the 3.0 T2D patients have no T1D/T2D code and their only 3.0 diabetes drug is an SGLT2 on its own; 1,095,883 of them have an HF code.
4. **No end date.** The 3.0 flag uses all claims; 7,555 patients have T2D codes only after `date_end`.
5. **Codes by word match, not by list.** The word match finds 124 T2D codes; the basket has 86 of them. The 38 others are E11 parent codes, retinopathy eye-side codes and O24.1x (pre-existing T2D in pregnancy).
6. **ICD-9.** The word match does not find ICD-9 codes (their description says `TYPE II`). Patients with ICD-9 codes only: T2D 4,347,621, T1D 1,140,938, HF 3,127,750.
7. **Dx gap.** No Dx claims from 2018-06 to 2020-12.
8. **Performance.** The old notebook pulls every (patient, NDC) pair into Spark to filter the drugs; the new notebook filters the NDC list in Snowflake.

### 7.3 New logic

One Snowflake query (`build_flags_query`), one row per patient with any flag. Claims up to `date_end`, rendering provider present.

| Column | Rule |
| --- | --- |
| `T2D_FLAG_30` | The 3.0 `DIABETIC_FLAG` (any T2D code at any date, or a 3.0 diabetes drug), kept for PJ06 |
| `T2D_DX_DAYS`, `T1D_DX_DAYS` | Distinct service dates with a T2D / T1D code |
| `DM_TYPE` | `T1D` if T1D days > T2D days; `T2D` if T2D days >= T1D days (> 0). No T1D/T2D code: `T2D` if a 3.0 diabetes drug other than an SGLT2 alone (D1), else `OTHER` if an other-diabetes code (E08/E09/E13), else empty |
| `T2D_FLAG`, `T1D_FLAG` | `DM_TYPE` = T2D / T1D |
| `DM_MIXED` | 1 when both T1D and T2D codes are present |
| `RX_T2D` | Any 3.0 diabetes drug |
| `RX_T2D_NON_SGLT2` | Any 3.0 diabetes drug other than an SGLT2 alone |
| `HF_FLAG` | Any HF code |
| `HF_TYPE` | `MIXED` (combined code, or both HFrEF and HFpEF codes), `HFREF_PROXY` (systolic, I50.2x), `HFPEF_PROXY` (diastolic, I50.3x), else `UNKNOWN` |
| `HF_FIRST_DATE` | First HF claim |

### 7.4 Code lists

| Flag | Basket (`Kerendia_Dx_Final.csv`) | Additions (`Kerendia_Dx_Flag_Additions.csv`) | Total |
| --- | --- | --- | --- |
| T2D | 86 | 38 (E11 parents, retinopathy eye-side codes, O24.1x) | 124 |
| T1D | 52 | 68 (E10 parents, eye-side codes, O24.0x) | 120 |
| HF | 26 | 10 (I50, I50.2, I50.3, I50.4, I50.8, I50.81 parents, I50.83, I97.13x) | 36 |
| OTHER diabetes | 101 | 0 | 101 |

The additions file has the same columns as `Kerendia_Dx_Final.csv`. It is separate because the Dx journey (PJ02) checks that its basket codes equal the original DX Event List (D6).

### 7.5 Numbers

**All US patients:**

| Measure | Patients |
| --- | --- |
| Patients with any flag code or 3.0 diabetes drug | 88,896,145 |
| T2D flag 3.0 | 77,186,262 |
| T2D code, any date (basket + additions) | 54,315,151 |
| 3.0 diabetes drug | 51,780,610 |
| `DM_TYPE` = T2D | 73,532,765 |
| of them by Rx only (no T1D/T2D code) | 20,196,245 |
| SGLT2 alone and no T1D/T2D code (T2D in 3.0, not T2D now, D1) | 2,480,584 (1,095,883 with HF) |
| `DM_TYPE` = T1D | 1,949,479 |
| of them T2D in 3.0 | 1,165,299 |
| `DM_TYPE` = OTHER | 342,430 |
| `DM_MIXED` = 1 | 3,625,338 (966,140 T1D; 143,765 ties set to T2D) |
| T2D in 3.0, no `DM_TYPE` now | 2,479,429 |
| `HF_FLAG` = 1 | 23,763,719 (5,065 only through added codes) |

**3.0 T2D vs 3.1 T2D:** 77,186,262 → 73,532,765 (−3,653,497) = 2,471,874 SGLT2 alone without a flag + 8,710 SGLT2 alone with an other-diabetes code (now OTHER) + 1,165,299 now T1D + 7,555 T2D codes only after `date_end` + 59 now OTHER.

**HF by type and diabetes type**

| `HF_TYPE` | T2D | T1D | OTHER | No diabetes | Total |
| --- | --- | --- | --- | --- | --- |
| HFPEF_PROXY | 3,117,540 | 42,284 | 14,719 | 2,996,035 | 6,170,578 |
| HFREF_PROXY | 2,034,796 | 31,245 | 10,387 | 2,324,418 | 4,400,846 |
| MIXED | 3,064,987 | 39,503 | 13,648 | 2,239,110 | 5,357,248 |
| UNKNOWN | 3,638,127 | 58,017 | 19,877 | 4,119,026 | 7,835,047 |
| Total | 11,855,450 | 171,049 | 58,631 | 11,678,589 | 23,763,719 |

**Validation patients (4,238):** T2D flag 3.0 = 2,490; `T2D_FLAG` = 2,339; `T1D_FLAG` = 39 (36 T2D in 3.0); `DM_MIXED` = 205; `HF_FLAG` = 1,309 (MIXED 424, HFPEF_PROXY 420, UNKNOWN 315, HFREF_PROXY 150). 0 differences vs independent pandas recount.

### 7.6 Decisions (2026-10-30)

| # | Question | Decision | Effect |
| --- | --- | --- | --- |
| D1 | No T1D/T2D code, only 3.0 diabetes drug is an SGLT2 alone | Not T2D. Kept in `T2D_FLAG_30`; visible as `RX_T2D` = 1, `RX_T2D_NON_SGLT2` = 0 | −2,480,584 T2D |
| D2 | Both T1D and T2D codes | More claim days wins, tie goes to T2D, `DM_MIXED` = 1 | 966,140 T1D, 143,765 ties |
| D3 | Insulins in the 3.0 drug list | Kept as in 3.0; they count only when there is no T1D/T2D code | None |
| D4 | CKD / eGFR eligibility for T1D | Not decided in PJ04; belongs to PJ06. Proposal: same CKD stage rule as T2D | None in PJ04 |
| D5 | ICD-9 codes | Not used, as in 3.0 | 4,347,621 T2D, 1,140,938 T1D, 3,127,750 HF ICD-9-only patients out |
| D6 | Additions file | Kept separate; merge into `Kerendia_Dx_Final.csv` with Saurabh once Dx 3.1 is live | None |

---

## 8. PJ05 Px patient journey

**Notebook:** `Px Files/05_patient_journey_px` (28 cells)  
**Old notebook:** `Px Files/(Clone) 05_patient_journey_px` (created 2026-10-29, kept unchanged as baseline)  
**Basket:** `Final Product Basket/Kerendia_Px_Final.csv` (145 rows = 152 codes; original kept as `Kerendia NBA 3.1 - PX Event List.csv`)  
**Downstream:** `06_patient_journey_combine` (cell "Add dialysis flag")  
**Full plan:** `Px Files/NBA_3_1_Px_Journey_Plan.md`

### 8.1 Current notebook (3.0)

| Cell | What it does |
| --- | --- |
| 1 | Header (out of date: names `PUB_CAR_IQV_LAAD_PX_FCT`; the code reads `STG_CAR_IQV_LAAD_FACT_PX`) |
| 2–3 | `00_connection`, `00_cohort_config` |
| 4 | **3.0 Px query** from Snowflake |
| 5 | Review markdown (added 2026-10-29) |
| 6 | Write `kerendia_nba_3_1_px_validation` |

Output columns: `PATIENT_ID, FIRST_DIALYSIS_DATE, DIALYSIS_FLAG (always 1)`. One row per patient, all US (1,489,202 rows on 2026-10-26).

The 3.0 query: reads `PATIENT_ID, SERVICE_DATE, PROCEDURE_CODE` from all of `STG_CAR_IQV_LAAD_FACT_PX`; inner-joins `DIM_PROCEDURE` filtered to `UPPER(PROCEDURE_DESCRIPTION) LIKE '%DIALYSIS%'`; keeps earliest `SERVICE_DATE` per patient as `FIRST_DIALYSIS_DATE`.

PJ06 left-joins the Px table to the patient-month spine; `DIALYSIS_FLAG = 1` from the month of `FIRST_DIALYSIS_DATE` on (and always 1 if the first date is before 2017-01-01), else 0.

### 8.2 Bottlenecks found

| # | Hardcoded / issue | Effect | Fix goes in |
| --- | --- | --- | --- |
| Q1 | **Which procedures count: text match `%DIALYSIS%`** | No list to review; any code with the word counts, any code without it is missed | Basket |
| Q2 | **Wrong matches:** C1751 catheter "(OTHER THAN HEMODIALYSIS)", 93985/93986 scans "prior to creation" | First dialysis date can be too early or a patient flagged who never had dialysis | Basket |
| Q3 | **Possible misses:** ESRD monthly services 90960/90961/90962/90966, hemodialysis access codes, home hemodialysis visit 99512 | Real dialysis patients missed or found late | Basket |
| Q4 | **Mixed signal types under one flag:** dialysis sessions, ESRD monthly services, access procedures, training, drugs | Access is often created months before dialysis starts; drugs prove the patient is on dialysis but are not the procedure. One flag hides the difference | Basket (`PX_GROUP` column) |
| Q5 | **No end date** | Future-dated or wrong service dates can set the first date | Config (`date_end`) |
| Q6 | **Table and column names** typed in the SQL | A rename breaks the query | Config |
| Q7 | **`DISTINCT` and `GROUP BY` together; constant `DIALYSIS_FLAG = 1`** | Double work; a column with no information | Code |
| Q8 | **Code of the first event not in the output** | No QC: cannot see which code set the first date | Code |
| Q9 | **No dropped-rows report** | Rows with no patient, no date or a code not in the dimension table are lost silently | Code |
| Q10 | **No validation scope** (unlike other journey notebooks) | Comparisons always run on all US | Config |

**Not a bottleneck: the date window.** The query uses all history on purpose: it looks for the *first* dialysis ever, and PJ06 treats a first date before 2017 as "on dialysis". Decision D3 keeps all history.

### 8.3 New Px basket (`Kerendia_Px_Final.csv`)

One row per code, same style as the lab and Dx baskets. All 130 rows are kept; only the dialysis rows are used in Phase A.

| Column | Meaning | Example |
| --- | --- | --- |
| `MATCH_TYPE` | `CODE` (one code) or `LIST` (clubbed group) | `CODE` |
| `MATCH_VALUE` | The code, or the member codes | `90935` |
| `CLUB_ID` | Name of the clubbed group | `ECHO_VARIANTS` |
| `PROCEDURE_DESCRIPTION` | As in the old basket | |
| `PROC_CATEGORY` | As in the old basket | `Dialysis/Nephrology` |
| `CONDITION` | CKD / HF / DM / T1D / LIPIDS / OTHER | `CKD` |
| `PX_GROUP` | DIALYSIS_SESSION / ESRD_MONTHLY / DIALYSIS_TRAINING / DIALYSIS_ACCESS / PRE_ACCESS / DIALYSIS_DRUG / TRANSPLANT / blank | `DIALYSIS_SESSION` |
| `ACTIVE_DIALYSIS` | `Y` = counts for `FIRST_DIALYSIS_DATE` (decision D1) | `Y` |
| `IS_DEFINING`, `IN_752_FEATURES`, `PATIENTS_TOTAL`, `NOTE` | As in the old basket (Y/N cleaned) | |

**D1 applied in the new basket:**

| `PX_GROUP` | `ACTIVE_DIALYSIS` | Codes |
| --- | --- | --- |
| DIALYSIS_SESSION | Y | 90935, 90937, 90945, 90947, 90999, 99512 |
| ESRD_MONTHLY | Y | 90960, 90961, 90962, 90966 |
| DIALYSIS_TRAINING | Y | 90989, 90993 |
| DIALYSIS_DRUG | Y | Q4081, J0887, Q5105, J0882, J0604, J0879 |
| DIALYSIS_ACCESS | N | 36800, 36831, 36832, 36833, 36901–36909, 49421, C1750, C1752, 93990 |
| PRE_ACCESS | N | 93985, 93986 |
| TRANSPLANT | N | 50360 |
| (none) | N | C1751 ("other than hemodialysis"), all non-dialysis codes |

D2 additions (codes caught by 3.0 text match but not in the basket):

| PX_GROUP | Counted | Codes | Patients |
| --- | --- | --- | --- |
| ESRD_MONTHLY | Y | 90970, 90969, 90968, 90967, 90965, 90964, 90963 | 172K–815 each |
| DIALYSIS_DRUG | Y | Q0139, J0890, J3591, J0886 | 99–5,774 each |
| DIALYSIS_ACCESS | N | 36838, 36815, 90940, 90939 | 8–2,455 each |

### 8.4 Build plan

| Step | What | Comparison |
| --- | --- | --- |
| 0 | Run 3.0 query unchanged; compare with table last written | Patients and first dates identical |
| 1 | Hardcoded-parts markdown + **profile**: every code the text match catches, with description, patients and first-date counts; check which basket dialysis codes it misses | Facts for D1 |
| 2 | **Basket:** code list and `PX_GROUP` from the new Px basket; only groups chosen in D1 count as dialysis | vs 3.0: same patients / same first date, earlier, later, gained, lost, split by the code that caused it |
| 3 | **Config:** `PX_CONFIG` (table/column names, `date_end`, history start = none, validation patients); checks tables/columns exist | vs Step 2: identical rows expected; rows pulled |
| 4 | **Code:** output columns from basket (`FIRST_DIALYSIS_DATE` kept; add `FIRST_DIALYSIS_CODE` for QC); remove constant flag and double `DISTINCT`; dropped-rows report | vs Step 3: identical first dates; report of rows dropped by reason |
| 5 | **Write:** switched off until review (`WRITE_OUTPUT = False`) | – |

### 8.5 Implementation results

| Step | Check | Result |
| --- | --- | --- |
| 0 | 3.0 query vs table last written | Identical: 1,489,202 patients, 0 different first dates |
| 1 | Profile of the `%DIALYSIS%` text match | 32 codes (31 with claims, ICD-9 39.95 has none). 15 not in the basket (added under D2) |
| 2 | Basket query vs 3.0, all US | Same 1,087,148; earlier 268,617 (median 134 days, from 90960–90962); later 45,596 (median 20 days); gained 134,972 (90960–90962); lost 87,841 (access only: C1750, 36800, C1752). Total 1,489,202 → 1,536,333 (+3.2%) |
| 2 | Validation patients | Months flagged 7,649 → 8,413; patients ever flagged 325 → 363 |
| 3 | Config query vs Step 2 | Identical except 281 patients whose first dialysis is after `date_end`; validation identical |
| 4 | Output columns + dropped-rows report | Identical first dates (1,536,052); dropped: 10,169 rows after `date_end` (0.0044%). First event: session 61.5%, ESRD monthly 34.2%, ESRD drug 2.6%, training 1.7% |
| 5 | Write | Switched off; table still holds 3.0 output of 2026-10-26 |

**D1 check (cell 2f):** ESRD or dialysis diagnosis (N18.6, Z99.2, Z49.x) for 88.6% of the patients still counted (reference), against 8.8% for short-term catheter C1752. About 25,900 of the 87,841 access-only patients (29%) have such a diagnosis. Recommendation: keep access out (D1 as is). Go-live rule: write 3.1 Px table together with 3.1 Dx table.

### 8.6 Decisions

**Decided 2026-10-29: all five as proposed.**

| # | Decision | Options | Decided |
| --- | --- | --- | --- |
| D1 | **Which groups count as dialysis** | Any combination of `PX_GROUP` values | Sessions, ESRD monthly, home visit, training, drugs = **Y**. Access = **N** (created before dialysis starts; measured in Step 2). Pre-access scans, C1751, transplant = **N** |
| D2 | Codes caught by 3.0 text match not in the basket | (a) add with a group, (b) leave out | (a), so nothing is lost silently |
| D3 | History window | (a) all history (as 3.0), (b) `DATA_START_DATE` | (a): the first dialysis ever is needed |
| D4 | Basket files | (a) save current unchanged and rewrite `Kerendia_Px_Final.csv`, (b) keep and add new file | (a), same as Dx |
| D5 | Patient scope of the output | (a) all US (PJ06 left-joins on patient), (b) validation only | (a) for output; comparisons for both |

### 8.7 Phase B (after review)

* HF procedures: echo (93306, 93308, 93350, 93351, ...), NT-proBNP (83880).
* T1D / diabetes signals: insulin pump and CGM supplies, islet cell antibody (86341), glucagon, diabetes self-management training (G0108, G0109).
* Separate flags and dates per group: dialysis type (hemo / peritoneal / home), first access date, transplant.
* Dx plan Q2: dialysis and transplant procedure codes in the old Dx list checked against Px data.
* Access as an early signal: a first access date (fistula / catheter) as its own column.

---

## 9. PJ06 Combine: findings from the full run

**Notebook:** `Combine Files/06_patient_journey_combine`  
**Full findings:** `Combine Files/NBA_3_1_E2E_Full_Run_2026_11_02.md`

### 9.1 What the combine does

Full join of PJ01-PJ05 on `PATIENT_ID, DATE`. Sets `GFR_UACR_DX_STAGE = COALESCE(DX_STAGE_UPDATED, GFR_STAGE, UACR_STAGE)`, `DIALYSIS_FLAG` from Px, `SGLT2_FLAG` from Rx, `ELIGIBLE_PATIENT_FLAG` based on stage 2-4, not on dialysis, and (in 3.1) the SGLT2 rule. Adds `HF_FLAG` and `DM_TYPE` from PJ04.

### 9.2 Full universe results (2026-11-02)

| Metric | 3.1 full | 3.0 full |
| --- | --- | --- |
| Patients in the combine | 148,004,353 | 156,438,251 |
| Patient-months | 3,113,063,984 | 3,488,872,653 |
| Eligible patients (Sep 2026) | 77,495,057 | -- |
| Lab journey rows | 1,750,760,310 | 2,212,793,523 |
| Lab journey patients | 64,594,814 | 65,590,422 |
| Dx journey rows | 497,753,762 | 409,207,520 |
| Dx journey patients | 16,734,829 | 16,023,045 |
| Rx journey rows | 7,500,830,652 | -- |
| Rx journey patients | 113,356,779 | -- |

### 9.3 Key findings

* **SGLT2 rule (C1):** 56% of eligible months have no known stage and never an SGLT2. The rule is meant to exclude them, but the condition compares stage with -1 (copied from 3.0), so it never applies.
* **Diabetes not required (C9):** 58% of eligible months belong to patients with no T1D or T2D diagnosis.
* **Dx stage 5 exclusion:** 14.3M months / 0.99M patients excluded as stage 5 at full scale -- the biggest real 3.1 correction.
* **HF flag:** 14.7M patients, 398.6M months. Output only; does not change eligibility yet.
* **DM_TYPE:** 32.3M eligible months have `DM_TYPE = T1D`; 339.1M of 394.0M HF months eligible through the CKD rule.
* **B1:** 3.0 full combine carries a lab stage in only ~18% of 3.0 lab-journey months. Most full-scale eligibility difference comes from this, not from 3.1 lab logic.

---

## 10. Decisions taken

### 10.1 Cross-notebook decisions (affect the combine)

| # | Decision | Status | Effect |
| --- | --- | --- | --- |
| C1 | **SGLT2 rule for unknown stage** — copied from 3.0 as is, so it never applies | **Open, most important** | Fixing it makes 1,745.6M of 3,113.0M eligible months (56%) not eligible |
| C2 | **Which diabetic flag** goes into the table: 3.0 rule or 3.1 T2D | Our choice, please confirm | 77.3M vs 73.6M diabetic patients |
| C3 | **Eligibility per indication** (T2D + CKD, T1D + CKD, HF) | Open (needs Medical for T1D) | 32.3M eligible months have `DM_TYPE = T1D`; 339.1M of 394.0M HF months eligible through CKD rule |
| C4 | **Monthly HF flag**: from first HF code on, never ends | Our choice, please confirm | 14.7M patients, 398.6M months; output only |
| C5 | Dialysis: first date carried into combine; 2017 rule kept | Our choice, please confirm | Never applies (history starts 2021) |
| C6 | **Output table shape**: `HF_FLAG` and `DM_TYPE` added; three `cohort_label` copies merged | Our choice, please confirm | All 3.0 columns unchanged |
| C7 | Lab-only months stay in the journey | Our choice, please confirm | Lab stage keeps its eligibility |
| C8 | Go-live of 3.1 combine | Open (after decisions and G1) | Written to `full_2026_11_02/` only |
| C9 | **Should eligibility require diabetes?** | Open | 1,795.9M eligible months (58%), 76.5M patients have no T1D/T2D diagnosis |
| C10 | Meaning of `DM_TYPE = OTHER` (342,541 patients) | Open | Confirm before using in eligibility |
| G1 | **Go-live together:** 3.1 Rx, Px, flags tables go live only with 3.1 Dx | Decided | Required: without 3.1 Dx stage 5, access-only dialysis patients would become eligible |

### 10.2 Per-notebook decisions (summary)

| Notebook | Decisions | Key ones |
| --- | --- | --- |
| PJ01 Lab | 8 made (L-D1 to L-D8), 3 open (L1–L3) | L1: specialty filter (211.4M eGFR rows excluded); L2: `>60` eGFR; L3: config location |
| PJ02 Dx | 9 made (D1–D5, N1–N4), 4 open (I1–I4) | X1: end-to-end review with Saurabh; X2: latest staged Dx wins; D2: T1D kidney codes included |
| PJ03 Rx | 8 made (D1–D8) | R1: missing drugs (generic dapagliflozin, Kerendia, GLP-1s) — Phase B |
| PJ04 Flags | 6 made (D1–D6) | D1: SGLT2 alone no longer T2D; D2: most claim days wins; D5: no ICD-9 |
| PJ05 Px | 5 made (D1–D5) | D1: access procedures excluded from dialysis; D3: all history kept |

---

## 11. Data readiness

| Data | Source | Coverage | Status | Gap / action | Owner |
| --- | --- | --- | --- | --- | --- |
| Lab (eGFR / UACR) | `PHCDW_SANDBOX.IQV_QUEST_LAB` | All US, 64.6M patients | **Ready** | L1: specialty filter decision; L3: config location | NBA team |
| Dx (CKD stage) | `STG_CAR_IQV_LAAD_FACT_DX` + `DIM_DIAGNOSIS` | All US, 16.7M patients | **Ready** | X1: end-to-end review with Saurabh | NBA team, Saurabh |
| Rx (treatments) | `STG_CAR_IQV_LAAD_FCT_RX` + product / provider / plan | All US, 113.3M patients | **Ready** | R1: generic dapagliflozin, Kerendia, GLP-1s — Phase B | NBA team |
| Px (dialysis) | `STG_CAR_IQV_LAAD_FACT_PX` + `DIM_PROCEDURE` | All US, 1.54M patients | **Ready** | P3: how Px codes feed patient potential — Raman | NBA team, Raman |
| Flags (DM / HF) | Dx fact + Rx fact + `diabetes_product` | All US, 89.0M patients | **Ready** | D6: merge additions into Dx basket with Saurabh | NBA team |
| HCP universe (3.1) | `HCP_Universe_without_call_hcps` (Parquet) | 294,726 HCPs | **Ready** | C1-C5 flags not used as filters | NBA team |
| NPI-BHID mapping | `kerendia_nba_3_0_npi_bhid_mapping` (Delta) | 1.66M rows | **Ready** | – | NBA team |
| 3.0 combine baseline | `pat_gfr_dx_stage_and_treatment_category` | 156.4M patients | **Needs check (B1)** | Which lab input did 3.0 Ops combine read? | Wenjie |
| LabCorp | Second lab source | Unknown | **Missing** | Availability, patient ID matching, overlap with Quest | NBA team |

---

## 12. Work plan

Each phase ends with a gate (section 7). Phases are sequential: Phase 0 is done, Phase 1 is the decision phase, Phase 2 builds new features, Phase 3 is go-live.

| Phase | Content | Main tasks | Status | Depends on |
| --- | --- | --- | --- | --- |
| **0. Build and validate** | PJ01–PJ06 rebuilt, validated (10 HCPs) and run on full universe | All 5 notebooks: basket, config, code rules, dropped-rows report, write; combine: eligibility table with `HF_FLAG` and `DM_TYPE`; job: validation + full run | **Done** | – |
| **1. Decisions and team reviews** | Settle the open decisions that change eligibility | C1 (SGLT2 rule); C9 (diabetes requirement); C3 (eligibility per indication); C10 (`DM_TYPE = OTHER`); B1 (3.0 Ops combine lab input); L1 (specialty filter); X1 (Dx review with Saurabh); P1–P3 (Px review with Raman); D1–D6 (flags review) | **In progress** | Phase 0 |
| **2. New features** | Build Phase B additions per notebook | Lab: Potassium, HbA1c, eGFR value/decline, lab-based CKD flag, 3a/3b split; Rx: generic dapagliflozin, Kerendia, GLP-1s; Px: HF procedures, T1D signals; Flags: monthly flags; Combine: eligibility per indication (C3) | **Not started** | Phase 1 (C1, C3 settled) |
| **3. Go-live** | Switch PJ06 to the 3.1 tables; update HCP-level notebooks; rename tables; re-run | All tables written to the production path (not `full_2026_11_02/`); HCP-level notebooks checked for `HF_FLAG` and `DM_TYPE`; old test copies cleaned up | **Not started** | Phase 1 + Phase 2 (or Phase 1 only if Phase 2 is deferred) |

---

## 13. Readiness gates

| Gate | Ready when | Status |
| --- | --- | --- |
| G0 | All five notebooks built and run (validation + full); job succeeds; E2E findings documented | **Done** (2026-11-02) |
| G1 | Team reviews complete: X1 (Dx with Saurabh), P1–P3 (Px with Raman), D1–D6 (flags), L1–L3 (lab); B1 (3.0 Ops combine) checked | In progress |
| G2 | C1 (SGLT2 rule) decided; C9 (diabetes requirement) decided; C3 (eligibility per indication) decided, T1D confirmed by Medical; C10 (`DM_TYPE = OTHER`) confirmed | Not started |
| G3 | Phase 2 features built and tested (if not deferred); HCP-level notebooks updated for new columns | Not started |
| **G4 (freeze)** | Final eligibility table chosen; all tables written to production path; table names renamed (no `_validation` suffix); old test copies cleaned up; inference run reproduces training columns | Not started |

---

## 14. Open points from the full run

| # | Point | Status | Effect |
| --- | --- | --- | --- |
| B1 | **Which lab input the 3.0 Ops combine read** (uses ~18% of 3.0 lab stages) | Open — check Wenjie's 3.0 Ops combine notebook | Most full-scale eligibility difference is a 3.0 baseline artefact |
| B2 | Full-run table names still end in `_validation`; rename before go-live | Open | Cosmetic but confusing |
| B3 | Clean-up: `full_2026_11_02/_stage/` and old test copies of 26 Oct in `query_output/` root | Open | Storage |
| B4 | Volume: 77.5M eligible patients per month, 66% with unknown stage. Check HCP-level notebooks handle this; fixing C1 halves it | Open | Performance |
| L1 | Specialty filter: keep, remove, or add specialties | Open | Removing adds ~16% eGFR and ~13% UACR patients |
| X1 | Dx end-to-end review with Saurabh | Open | Dx changes cause most real 3.1 differences |
| R1 | Missing drugs (generic dapagliflozin, Kerendia, GLP-1s) | Open (Phase B) | Generic dapagliflozin patients miss the SGLT2 flag; matters once C1 is fixed |

---

## 15. Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| SGLT2 rule not fixed (C1) | 56% of eligible months have no known stage and no SGLT2; they should not be eligible | Decide C1 before go-live; fixes roughly halve the eligible population |
| Diabetes not required (C9) | 58% of eligible months have no T1D/T2D diagnosis; may not be in the Kerendia label population | Decide C9; if required, add `DM_TYPE` check to eligibility |
| B1 not checked | Full-scale differences attributed to 3.1 that are actually 3.0 baseline | Check 3.0 Ops combine lab input before sharing full-run numbers |
| Co-detail history short (from Jan 2026) | Product-detail features are 0 or uninformative for older training instances | Data-available flags; test recent-only training (E6) |
| Key messages entered unevenly | Message features reflect rep habits rather than doctor behaviour | V4 before use; coarse fallback; per-territory check |
| Table names end in `_validation` | Confusing at go-live | Rename as part of G4 |
| HCP-level notebooks not checked for `HF_FLAG` / `DM_TYPE` | New columns break downstream | Check as part of G3 |
| LabCorp not available | Lab coverage limited to Quest | Keep as a Phase B candidate |

---

## 16. Next actions

| # | Action | Owner |
| --- | --- | --- |
| 1 | Review this plan with the NBA and data teams | NBA team |
| 2 | Check B1: which lab input the 3.0 Ops combine read | Wenjie |
| 3 | Dx end-to-end review with Saurabh (X1) | NBA team, Saurabh |
| 4 | Px review with Raman (P1–P3) | NBA team, Raman |
| 5 | Flags review: D1–D6 (team) | NBA team |
| 6 | Lab decisions: L1 (specialty), L2 (`>60`), L3 (config location) | NBA team |
| 7 | Decide C1 (SGLT2 rule) and C9 (diabetes requirement) | NBA team |
| 8 | Medical confirmation for T1D eligibility (C3) | Medical affairs |
| 9 | Confirm `DM_TYPE = OTHER` meaning (C10) | NBA team |
| 10 | Commit and push all notebook changes and findings files | Patricio |

---

## 17. References

* `Lab Files/NBA_3_1_Lab_Journey_Plan.md`: PJ01 detailed plan
* `Dx Files/NBA_3_1_Dx_Journey_Plan.md`: PJ02 detailed plan
* `Rx Files/NBA_3_1_Rx_Journey_Plan.md`: PJ03 detailed plan
* `T2D-T1D-HF Files/NBA_3_1_DM_HF_Flags_Plan.md`: PJ04 detailed plan
* `Px Files/NBA_3_1_Px_Journey_Plan.md`: PJ05 detailed plan
* `Combine Files/NBA_3_1_E2E_Full_Run_2026_11_02.md`: full HCP universe run findings
* `Combine Files/NBA_3_1_E2E_Run_2026_10_30.md`: validation run findings (superseded by the full run file)
* `NBA_3_1_Patient_Journey_Changes_Proposals.md`: original proposals
* Client summaries: one per folder (Lab, Dx, Rx, Px, Flags)
* Snowflake tables: `IQV_QUEST_LAB`, `STG_CAR_IQV_LAAD_FACT_DX`, `STG_CAR_IQV_LAAD_FCT_RX`, `STG_CAR_IQV_LAAD_FACT_PX`, `STG_IQVIA_LAAD_DIM_DIAGNOSIS`, `STG_IQVIA_LAAD_DIM_PRD`, `STG_IQVIA_LAAD_DIM_PRVDR`, `STG_IQVIA_LAAD_DIM_PLN`, `CKD_PRODUCT_MAPPING_VW`, `diabetes_product`
* Job: `NBA 3.1 Patient Journey (PJ01-PJ06)` (ID 953988155823642)
