# Kerendia NBA 3.1 – Diagnosis Patient Journey: Summary of Changes

**Scope:** Diagnosis (Dx) patient journey: CKD stage per patient and month from diagnosis claims, from the diagnosis code list to the patient-month Dx stage table  
**Baseline:** NBA 3.0 Dx notebook and query  
**Data used for validation:** IQVIA LAAD diagnosis claims, all US patients, 2025-01 to 2026-09, plus 10 validation HCPs, 2023-01 to 2026-09  
**Status:** built and validated; the new output table is not written yet (waiting for the review in section 9.2)

---

## 1. Summary

In NBA 3.0, the diagnosis codes and the CKD stage were written directly into the SQL query. The stage was read from the text of the code description, and only descriptions that matched exactly got a stage. Any change needed a code edit.

In NBA 3.1, the codes and their stage sit in one diagnosis code list, and the run settings in one settings block. The query is generated from them. Adding a code or changing a stage is now a file edit, not a code change.

* **CKD stage 3 and stage 5 were missing in NBA 3.0 and are now found.** The 3.0 list had none of the current stage-3 codes (`N18.30`, `N18.31`, `N18.32`) and none of the stage-5 or end-stage codes (`N18.5`, `N18.6`, `I12.0`, `I13.11`, `I13.2`). For the 10 validation HCPs, patients with stage 3 go from 0 to 690 and patients with stage 5 from 0 to 326.
* **No stage gets worse information:** every stage change versus NBA 3.0 is a move from "stage unknown" or a lower stage to the stage now coded. No stage goes down because of the new list.
* **Almost nothing is lost:** 2,612 patient-days out of about 150M (0.002%), from 3.0 codes that are not in the 3.1 list (section 7.1).
* **Better monthly table:** a patient's months start at the first CKD diagnosis, and "stage unknown" is empty instead of 0, so the lab stage can be used in its place downstream (section 4.6).
* **New information ready for the new indications:** each code carries its diabetes type (T2D / T1D / other) and, for heart failure codes, a heart failure type, for the planned T1D and HF work.
* **Faster:** 29% less data is pulled from Snowflake.
* **Visible data loss:** every run now prints a report of the rows dropped and why.

---

## 2. Product basket: old vs new snapshot

The product basket is the list of diagnosis codes for the Kerendia patient journey. The NBA 3.0 notebook did not read it: it used its own 163-code list typed in the SQL. The new basket holds the codes and their rules, and the notebook reads it at the start of every run.

### 2.1 What changed in the basket

| | Old basket | New basket |
| --- | --- | --- |
| File | `Kerendia NBA 3.1 - DX Event List.csv` (kept unchanged) | `Kerendia_Dx_Final.csv` |
| Columns | 9: `DIAGNOSIS_CODE`, `DIAGNOSIS_DESCRIPTION`, `patients_total`, `is_defining`, `club_members`, `n_members`, `in_752_features`, `is_clubbed`, `club_reason` | 15: `MATCH_TYPE`, `MATCH_VALUE`, `CLUB_ID`, `DIAGNOSIS_DESCRIPTION`, `CONDITION`, `ACTIVE_STAGING`, `CKD_STAGE`, `CKD_SUBSTAGE`, `DM_TYPE`, `HF_TYPE`, `FLAG`, `IS_DEFINING`, `IN_752_FEATURES`, `PATIENTS_TOTAL`, `NOTE` |
| Rows | 240 (5 clubbed groups) | 240 (the same rows) = 368 single codes |
| Clubbed groups | One row with a code such as `E11.3x_CLUBBED` and the member codes in a text column | `MATCH_TYPE = LIST`: the member codes are matched directly |
| What each code is about | Not stored | `CONDITION`: CKD, T2D, T1D, other diabetes, heart failure, dialysis, transplant, ... |
| CKD stage | Not stored (3.0 read it from the description text) | `CKD_STAGE` per code (1–5, or 0 = CKD with stage unknown); `CKD_SUBSTAGE` = 3a / 3b / ESRD |
| Used for the CKD journey | – | `ACTIVE_STAGING = Y` on the 31 CKD codes |
| New indications | – | `DM_TYPE` (T2D / T1D / OTHER) and `HF_TYPE` (heart failure type) |
| Special conditions | – | `FLAG`: HF, DIALYSIS, TRANSPLANT, PROTEINURIA, KIDNEY_CV |
| Used by the notebook | No | Yes; the notebook checks that it has exactly the codes, patient counts and flags of the old basket |

### 2.2 Old basket (`Kerendia NBA 3.1 - DX Event List.csv`): example rows

| DIAGNOSIS_CODE | DIAGNOSIS_DESCRIPTION | patients_total | is_defining | is_clubbed |
| --- | --- | --- | --- | --- |
| E11.9 | Type 2 diabetes mellitus without complications | 16,948,649 | YES | NO |
| I12.9 | Hypertensive CKD with stage 1–4 or unspecified CKD | 5,105,633 | YES | NO |
| N18.31 | Chronic kidney disease, stage 3a | 4,358,658 | YES | NO |
| I50.9 | Heart failure, unspecified | 4,073,730 | YES | NO |
| E11.3x_CLUBBED | T2D diabetic retinopathy (46 codes) | 2,501,901 | YES | YES |

The old basket lists the codes but gives no stage, no condition and no rule, so it could not drive the CKD staging.

### 2.3 New basket (`Kerendia_Dx_Final.csv`): codes used for CKD staging

Patients = all US patients with the code in the claims, 2025-01 to 2026-09.

| CKD stage | Codes | Patients | In the 3.0 query? |
| --- | --- | --- | --- |
| 1 | N18.1 | 0.37M | Yes |
| 2 | N18.2 | 2.16M | Yes |
| 3 | N18.31 (3a), N18.32 (3b), N18.30 (3, unspecified) | 4.87M, 3.09M, 2.82M | **No** |
| 3 | N18.3 (old code, replaced in 2020) | 3.4K | Yes |
| 4 | N18.4 | 1.53M | Yes |
| 5 | N18.6 (end-stage renal disease, `CKD_SUBSTAGE = ESRD`) | 1.12M | **No** |
| 5 | I12.0, I13.2, N18.5, I13.11 (stage 5 or end stage) | 0.66M, 0.39M, 0.36M, 0.06M | **No** |
| 0 (CKD, stage unknown) | I12.9, N18.9, I13.0, I13.10 (hypertensive or unspecified CKD) | 5.72M, 3.31M, 2.62M, 0.49M | Yes |
| 0 | E11.22, E11.21, E11.29 (T2D with kidney disease, `DM_TYPE = T2D`) | 4.74M, 1.00M, 0.82M | Yes |
| 0 | E10.22, E10.21, E10.29 (T1D with kidney disease, `DM_TYPE = T1D`) | 0.12M, 0.04M, 0.03M | **No** (new, decision D2) |
| 0 | E08.21/22/29, E13.21/22/29, E09.22 (other diabetes with kidney disease, `DM_TYPE = OTHER`) | 0.14M in total | Yes |
| 0 | D63.1 (anemia in CKD) | 1.76M | Yes |
| 0 | Z99.2 (dependence on dialysis, `FLAG = DIALYSIS`) | 0.79M | Yes |

### 2.4 New basket: codes not used for CKD staging

These 337 codes stay in the basket for the other patient features (diabetes, heart failure, comorbidities). They have no stage and do not change the CKD journey.

| Condition | Codes | Notes |
| --- | --- | --- |
| T2D | 78 | Includes the clubbed retinopathy group E11.3x (46 codes); `DM_TYPE = T2D` |
| T1D | 49 | Includes E10.3x (28 codes); `DM_TYPE = T1D` |
| Other diabetes | 94 | Includes E08.3x (39) and E13.3x (15); `DM_TYPE = OTHER` |
| Heart failure | 24 | `FLAG = HF`, with `HF_TYPE` (section 4.5) |
| Peripheral vascular disease | 47 | Includes I70.3xx (5 codes) |
| Cardiomyopathy, hypertension, atherosclerosis, anemia, hyperlipidemia | 24 | |
| Diabetes treatment (insulin, oral drugs, pump) and diabetes in pregnancy | 13 | |
| Dialysis encounters (Z49.01, Z49.02, Z49.31, Z49.32) | 4 | `FLAG = DIALYSIS` (decision D5a) |
| Kidney transplant (Z48.22) | 1 | `FLAG = TRANSPLANT` (decision D5a) |
| Proteinuria (R80.9) | 1 | `FLAG = PROTEINURIA` (decision D5b) |
| Renal artery disease (I70.1), renovascular hypertension (I15.1) | 2 | `FLAG = KIDNEY_CV` (decision D5b) |

---

## 3. Old vs new at a glance

| Area | Old notebook (NBA 3.0) | New notebook (NBA 3.1) | Benefit |
| --- | --- | --- | --- |
| Input data | Read a pre-built 3.0 Dx table | Runs the Dx query directly from Snowflake | No dependency on a table that can be removed in a data refresh |
| Which codes count | 163 codes typed in the SQL; 131 of them can never match diagnosis data (old ICD-9 codes and procedure codes) | 31 CKD codes from the basket | Only real, current CKD codes; the list is a file edit |
| How the stage is found | From the description text; only 5 exact descriptions get a stage | `CKD_STAGE` per code in the basket | Stage 3 and stage 5 found; no dependency on description wording |
| Run settings (dates, tables, provider rule) | Written in the SQL; two start dates (2019-01 in the SQL, 2023-01-01 afterwards) | One settings block (`DX_CONFIG`); one start date, applied in the query; checks that tables and columns exist | One place to change settings; clear error if a table is renamed |
| Data loss | Silent | Dropped-rows report on every run | Full transparency of what is excluded and why |
| Monthly table | Every patient x every month of the whole period, also before the first diagnosis; 0 for both "stage unknown" and "no diagnosis yet" | Months from the patient's first CKD diagnosis; "stage unknown" is empty | Smaller table; the lab stage can fill "stage unknown" downstream |
| Output | Patient, month, list of stages of the month, carried-forward stage, cohort label | Patient, month, highest stage of the month, carried-forward stage, sub-stage (3a / 3b / ESRD), CKD flag, cohort label | Easier to use; ready for the stage 3a / 3b and ESRD features |
| Validation | None in the notebook | Row-by-row comparison after each step (all US + validation HCPs) | Every change is measured |

---

## 4. Diagnoses covered

### 4.1 Why stage 3 and stage 5 were missing in NBA 3.0

The 3.0 query gave a stage only when the code description was exactly one of these texts: `CHRONIC KIDNEY DISEASE, STAGE 1`, `... STAGE 2 (MILD)`, `... STAGE 3 (MODERATE)`, `... STAGE 4 (SEVERE)`, or a text containing `STAGE 5`. Two problems:

| Problem | Effect |
| --- | --- |
| In October 2020, US coding replaced `N18.3` (stage 3) with `N18.30`, `N18.31` (3a) and `N18.32` (3b). These new codes were not in the 3.0 list | Stage 3 almost disappeared: only 3.4K patients still coded with the old `N18.3`, against 10.8M patient-codes with the new ones |
| No stage-5 or end-stage code (`N18.5`, `N18.6`, `I12.0`, `I13.11`, `I13.2`) was in the 3.0 list | No patient ever got stage 5 |

Patients with stage 3 or 5 were therefore shown as "stage unknown" (0), or kept an older stage.

### 4.2 Why this matters for the business

The patient journey feeds the eligibility rule in the combine notebook (PJ06): stage 2–4 = eligible for Kerendia, stage 1 or 5 = not eligible, unknown = unknown.

| Change | Effect on eligibility |
| --- | --- |
| Stage 3 now found | Stage 3 is the largest Kerendia-eligible CKD group. These patients were "unknown" before and are now eligible |
| Stage 5 / end stage now found | Kerendia is not for end-stage kidney disease. These patients were "unknown" before and are now correctly not eligible, so HCPs with many dialysis patients are no longer over-counted |

**Stage 3a and 3b.** CKD stage 3 is split into two sub-stages by kidney function (eGFR, in mL/min/1.73m²).

| Sub-stage | eGFR | Kidney function | ICD-10 code | Patients (all US, 2025-01 to 2026-09) |
| --- | --- | --- | --- | --- |
| 3a | 45–59 | Mild to moderate decrease | `N18.31` | 4.87M |
| 3b | 30–44 | Moderate to severe decrease | `N18.32` | 3.09M |
| 3, not split | 30–59 | Sub-stage not coded | `N18.30` (and the old `N18.3`) | 2.82M (+3.4K) |

**Why the 3a / 3b split matters.**

| Aspect | Explanation |
| --- | --- |
| Clinical risk | Patients in 3b have a clearly higher risk than those in 3a of moving to stage 4–5, of cardiovascular events, and of death. KDIGO guidelines treat 3a and 3b as separate risk groups and recommend more frequent monitoring in 3b |
| Kerendia eligibility | Both sub-stages are within the eGFR range where Kerendia can be started (eGFR ≥ 25 per the label, to be confirmed with Medical). The split does not change eligibility |
| Use for NBA | 3b patients are closer to the lower eGFR limit of the label and are more often followed by nephrologists. An HCP with many 3b patients may respond to different messages (for example, slowing progression) than one with mostly 3a patients |
| Coding history | `N18.30`, `N18.31` and `N18.32` replaced `N18.3` in October 2020. None of the new codes were in the NBA 3.0 list (section 4.1) |

**ESRD (end-stage renal disease).** ESRD is permanent kidney failure: the patient needs dialysis or a kidney transplant to survive. It is the last point of CKD and a subset of stage 5.

| | CKD stage 5 | ESRD |
| --- | --- | --- |
| Kidney function | eGFR below 15 mL/min/1.73m² | Usually eGFR below 15 |
| Treatment | May not be on dialysis yet | On regular dialysis or has had a kidney transplant |
| ICD-10 code | `N18.5` | `N18.6` (doctors are told to also code `Z99.2`, dialysis dependence) |
| Patients (all US, 2025-01 to 2026-09) | 0.36M | 1.12M |
| US specifics | – | A formal category: these patients qualify for Medicare whatever their age |

**Why ESRD matters.**

| Aspect | Explanation |
| --- | --- |
| Kerendia eligibility | Kerendia is not for these patients: the label does not recommend starting it at low eGFR (below 25), and it was not studied in dialysis patients (to be confirmed with Medical). PJ06 treats stage 5 as not eligible |
| Effect of the NBA 3.0 gap | No ESRD code was in the 3.0 list, so ESRD patients showed as "stage unknown" and could be counted as possible Kerendia patients. This is the largest change in section 7.1: 52.19M patient-days move from unknown to stage 5 |
| Claim volume | `N18.6` has 69.4M claim rows (2025-01 to 2026-09) for 1.12M patients, because dialysis takes place several times a week and each session is a claim |
| Codes that do not separate stage 5 from ESRD | `I12.0`, `I13.11`, `I13.2` ("stage 5 CKD or end-stage renal disease"): stage 5, no sub-stage |

**How the sub-stages are stored in NBA 3.1.**

| Code | `CKD_STAGE` | `CKD_SUBSTAGE` | Validation HCPs: patients with at least one month |
| --- | --- | --- | --- |
| `N18.31` | 3 | 3a | 379 |
| `N18.32` | 3 | 3b | 364 |
| `N18.30`, `N18.3` | 3 | (empty) | 210 |
| `N18.6` | 5 | ESRD | 292 |
| `N18.5`, `I12.0`, `I13.11`, `I13.2` | 5 | (empty) | 134 |

In the monthly table, the sub-stage is carried forward together with the stage (`DX_SUBSTAGE_UPDATED`). On the lab side, the same 3a / 3b split could come from the eGFR value (45–59 = 3a, 30–44 = 3b), by changing the eGFR cut-offs in the lab test list (lab summary, section 9.3).

### 4.3 End-stage, dialysis and transplant (decisions D3–D5)

| Code | Meaning | NBA 3.0 | NBA 3.1 |
| --- | --- | --- | --- |
| N18.6 | End-stage renal disease | Not in the list | Stage 5, sub-stage ESRD |
| I12.0, I13.11, I13.2 | Hypertensive CKD with stage 5 or end stage | Not in the list | Stage 5 (the code does not separate stage 5 from end stage) |
| N18.5 | CKD stage 5 | Not in the list | Stage 5 |
| Z99.2 | Dependence on dialysis | Stage 0 | Stage 0 (as 3.0) + dialysis flag |
| Z49.01, Z49.02, Z49.31, Z49.32 | Dialysis encounter | Not in the list | Not staged; dialysis flag |
| Z48.22 | Follow-up after kidney transplant | Not in the list | Not staged; transplant flag |
| R80.9 | Proteinuria | Not in the list | Not staged; proteinuria flag |
| I70.1, I15.1 | Renal artery disease, renovascular hypertension | Not in the list | Not staged; kidney-cardiovascular flag |

The flags are stored in the basket now; turning them into patient features is part of the next phases (section 9.3).

### 4.4 Type 1 diabetes with kidney disease (decision D2)

Kerendia is being studied in new indications, including CKD with type 1 diabetes. The T1D kidney codes `E10.21`, `E10.22` and `E10.29` are added as "CKD, stage unknown" with `DM_TYPE = T1D` (about 0.2M patients, 2025-01 to 2026-09). They add CKD patients but do not change any stage. Whether T1D patients count as eligible is controlled later by a switch that is off by default (section 9.3).

### 4.5 Heart failure codes (prepared for the HF indication)

Kerendia's second indication is heart failure with LVEF ≥ 40% (see the lab summary, section 9.4). Diagnosis codes do not hold the LVEF value, but the type of heart failure in the code is a useful proxy:

| `HF_TYPE` | Codes | Meaning | Link to the HF indication |
| --- | --- | --- | --- |
| HFPEF_PROXY | I50.30–I50.33 (diastolic HF) | Usually preserved ejection fraction | Likely covered |
| HFREF_PROXY | I50.20–I50.23 (systolic HF) | Usually reduced ejection fraction | Likely not covered |
| COMBINED | I50.40–I50.43 | Systolic and diastolic | Unclear |
| UNKNOWN | I50.9, I50.1, I50.8x, I11.0, I13.0, I13.2, I09.81 | Type not coded | Unknown |

Heart failure codes do not change the CKD stage. They are prepared for the HF flag and eligibility in the next phases.

### 4.6 "Stage unknown" and the lab stage

In the combine notebook (PJ06), the CKD stage is the Dx stage if there is one, otherwise the lab (eGFR) stage. In NBA 3.0 "stage unknown" was stored as 0. Because 0 is a value, the lab stage was never used for these months, even when an eGFR result showed the stage. In NBA 3.1 "stage unknown" is empty, so the lab stage fills it, with no change to PJ06. A new column `DX_CKD_FLAG = 1` still shows that the patient has a CKD diagnosis.

---

## 5. Each rule in the old notebook and where it is now

| # | Old notebook (written in the SQL or the code) | New notebook | What improves |
| --- | --- | --- | --- |
| 1 | **Code list:** 163 codes typed in the SQL | 31 CKD codes from the basket (`ACTIVE_STAGING = Y`) | Adding a code is a file edit |
| 2 | **Codes that cannot match:** 32 ICD-9 codes and 99 procedure codes in the Dx list | Removed; dialysis and transplant are covered by diagnosis codes with flags (procedures belong to the procedure journey) | The list shows what it really covers |
| 3 | **Stage from the description text** | `CKD_STAGE` per code | Stage 3 and stage 5 found |
| 4 | **Header codes** (`N18`, `I12`, `E11.2`, ...) and `E09.21`, `E09.29`, `N25.81`, `Z94.0` | Not in the 3.1 basket; effect measured (2,612 patient-days) | Known, small loss (section 9.2) |
| 5 | **Date filter** on year and month of every row, plus a second start date afterwards | One start and end date, applied on the service date in the query | 29% less data pulled; no conflicting dates |
| 6 | **Patient demographics join** never used | Removed | Faster, same result |
| 7 | **Table and column names** in the SQL | Settings block, checked before the run | Clear error if the vendor renames a table or column |
| 8 | **Provider rule** (referring doctor, otherwise rendering doctor) in the SQL | Same rule, in the settings block (decision N3) | Same rule, now visible |
| 9 | **Diagnosis code** not in the output | Kept, with sub-stage and diabetes type | QC by code; ready for new features |
| 10 | **No report** of excluded rows | Dropped-rows report | Losses visible on every run |
| 11 | **Monthly table** from the first to the last date of all patients | From each patient's first CKD diagnosis to the end date (decision N2) | No months before the diagnosis; every patient reaches the latest month |
| 12 | **0 = stage unknown and 0 = no diagnosis yet** | Empty when no stage is known, plus `DX_CKD_FLAG` (decision N1) | Lab stage can be used for "stage unknown" months |
| 13 | **Stages of the month as a list** | Highest stage of the month (`DX_STAGE_MONTH`) | Easier to use |

---

## 6. How the new notebook works

| Step | Input | What it does | Output |
| --- | --- | --- | --- |
| 1. Read the basket | `Kerendia_Dx_Final.csv` | Expands clubbed rows; checks for duplicate codes, valid stages, sub-stages, diabetes and HF types; checks it has the same codes as the old basket | CKD codes with their stage |
| 2. Read settings | `DX_CONFIG` | Dates, source and provider tables and columns, provider rule; checks that tables and columns exist | Run settings |
| 3. Build and run the query | Steps 1–2 | Generates the SQL, runs it in Snowflake, joins the HCP universe | Patient x day x code with stage |
| 4. Dropped-rows report | Same query steps | Counts every source row under the first rule it fails | Report of excluded data |
| 5. Patient journey | Step 3 | Highest stage per month; the latest known stage is carried forward to the next diagnosis; months from the first CKD diagnosis | Dx stage table for the patient journey |

Each change was introduced in a separate step and compared row by row with the step before. Before any change, the copied 3.0 query and processing were checked against the last 3.0 output: identical (37,582 patient-months, 817 patients).

---

## 7. Validation results

### 7.1 All US patients, 2025-01 to 2026-09 (patient-days = patient x day, highest stage of the day)

| Result | Patient-days | Detail |
| --- | --- | --- |
| Same stage as NBA 3.0 | 70.86M | |
| Stage changed | 79.42M | All upward: unknown → 5 (52.19M), unknown → 3 (26.77M), 4 → 5 (0.34M), 2 → 3 (92K), other (31K) |
| Newly included | 37.11M | Patient-days with no 3.0 code: stage 3 (22.71M), stage 5 (13.99M), stage unknown (0.40M, T1D kidney codes) |
| No longer included | 2,612 | 3.0 codes not in the 3.1 basket: `E09.21` / `E09.29` (drug-induced diabetes with kidney disease, 1,755), header codes (~850), a few ICD-9 rows. All were "stage unknown" in 3.0 |

The largest change, unknown → 5, comes from end-stage patients (N18.6, 1.12M patients): in NBA 3.0 they only had codes such as dialysis dependence (Z99.2) or anemia in CKD (D63.1), which give no stage.

### 7.2 Validation HCPs (10 doctors, 2023-01 to 2026-09)

| Metric | NBA 3.0 | NBA 3.1 | Change |
| --- | --- | --- | --- |
| Patients | 817 | 1,163 | +346 (only had codes missing from the 3.0 list) |
| Patients with stage 1 at some point | 12 | 9 | −3 (now coded with a higher stage) |
| Patients with stage 2 | 60 | 61 | +1 |
| Patients with stage 3 | 0 | 690 | +690 |
| Patients with stage 4 | 257 | 288 | +31 |
| Patients with stage 5 | 0 | 326 | +326 |
| Patient-months in the final table | 37,582 | 38,975 | +1,393 (more patients, but no months before the first diagnosis) |

The stage 3 and stage 5 counts match the expected impact stated in the NBA 3.1 change proposals.

### 7.3 Monthly table: old vs new processing on the same data

Same diagnosis data (NBA 3.1 query, validation HCPs) through the 3.0 and the 3.1 monthly processing:

| Result | Patient-months | Patients |
| --- | --- | --- |
| Same stage | 33,102 | 1,030 |
| "Stage unknown": 0 in 3.0, empty in 3.1 | 5,873 | 334 |
| Months before the first CKD diagnosis (removed) | 14,523 | 1,059 |
| Different stage | 0 | |

Sub-stages in the final table (patients with at least one month): stage 3a 379, stage 3b 364, ESRD 292.

### 7.4 Run efficiency

| | NBA 3.0 settings | NBA 3.1 settings |
| --- | --- | --- |
| Rows pulled from Snowflake | 1,086.9M | 771.6M (−29%) |
| Same rows in the result | – | Yes, identical (368.3M rows all US 2025-01 to 2026-09; 70,892 rows validation HCPs) |

---

## 8. What is excluded and why (new dropped-rows report)

All US, claim rows with a CKD code, before removing duplicate rows. NBA 3.0 excluded the same rows but did not report them.

| Reason | Claim rows | % | Can be recovered? |
| --- | --- | --- | --- |
| Before the start date (2023-01-01) | 399.1M | 27.2 | By design |
| After the end date (2026-09-30) | 0.55M | 0.0 | By design |
| No doctor on the claim (referring and rendering both empty) | 178.3M | 12.1 | No (cannot be linked to an HCP) |
| Doctor not in the HCP universe | 365.6M | 24.9 | By design (HCP universe) |
| **Kept** | **524.4M** | **35.7** | – |

---

## 9. Decisions

### 9.1 Decisions made

| Decision | Choice | Reason |
| --- | --- | --- |
| D1 | Only CKD codes get a stage | The Dx journey is a CKD journey; other conditions become their own features |
| D2 | T1D kidney codes (E10.21/22/29) included as "CKD, stage unknown", with `DM_TYPE = T1D` | Prepares the T1D indication |
| D3 | End-stage renal disease = stage 5; sub-stage ESRD for N18.6 | Not eligible for Kerendia, like stage 5 |
| D4 | Z99.2 (dialysis dependence) stays "stage unknown" (as 3.0), plus dialysis flag | Dialysis alone does not give the CKD stage |
| D5 | Dialysis encounter and transplant codes: flags only; proteinuria and renal artery codes: flags only | Useful signals, but not a CKD stage |
| N1 | "Stage unknown" empty instead of 0, plus `DX_CKD_FLAG` | Lets the lab stage be used; no change in PJ06 |
| N2 | Months from the patient's first CKD diagnosis to the end date | No months before the diagnosis; smaller table |
| N3 | Provider = referring doctor, otherwise rendering doctor (as 3.0) | Same HCP attribution as 3.0 |
| N4 | New basket file `Kerendia_Dx_Final.csv`; the old list is kept unchanged | Single place for the code rules |

### 9.2 Decisions for the final review

| # | Decision | Options | Impact |
| --- | --- | --- | --- |
| 1 | `E09.21`, `E09.29` (drug-induced diabetes with kidney disease) | (a) leave out, as in the 3.1 list, (b) add as "CKD, stage unknown", like E08 / E13 | Up to 734 patients (2025-01 to 2026-09); no effect on any stage |
| 2 | Which stage is carried forward | (a) latest coded stage (3.0 rule, kept today), (b) highest stage ever coded | With (a), a later stage-3 code replaces an earlier stage 4 (906 validation patient-months). CKD rarely improves, so (b) may be closer to reality, but (a) follows the latest doctor's coding |
| 3 | Months before the first diagnosis | Confirm that PJ06 keeps months with lab data only | Needed before the new table is used |
| 4 | Write the new table | Write after the review | Output columns change: the list of stages is replaced by `DX_STAGE_MONTH`; `DX_SUBSTAGE_UPDATED` and `DX_CKD_FLAG` are added |

### 9.3 Planned next phases (from the NBA 3.1 patient journey plan)

| Phase | What | Uses from the basket |
| --- | --- | --- |
| B | T2D and T1D patient flags, with a rule for patients coded with both | `DM_TYPE` |
| C | Heart failure flag, first HF date and HF type | `FLAG = HF`, `HF_TYPE` |
| D | Eligibility per indication: CKD + T2D, CKD + T1D (behind a switch, off by default), HF, any indication | Phases B–C |
| – | Dialysis, transplant, proteinuria and kidney-cardiovascular flags as patient features | `FLAG` |
| – | Stage 3a / 3b and ESRD features | `DX_SUBSTAGE_UPDATED` |
