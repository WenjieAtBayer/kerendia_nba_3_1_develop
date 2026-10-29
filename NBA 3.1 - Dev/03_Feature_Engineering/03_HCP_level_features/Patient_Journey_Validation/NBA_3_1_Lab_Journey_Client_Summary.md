# Kerendia NBA 3.1 – Lab Patient Journey: Summary of Changes

**Scope:** Lab patient journey (eGFR and UACR staging), from the lab test list to the patient-month lab stage table  
**Baseline:** NBA 3.0 lab notebook and query  
**Data used for validation:** IQVIA Quest lab data, all US patients, 2025-01 to 2026-09, plus 10 validation HCPs, 2023-01 to 2026-09

---

## 1. Summary

In NBA 3.0, every lab rule was written directly into the SQL query. This includes which tests count, units, stage cut-offs, dates, specialties and table names. Any change needed a code edit.

In NBA 3.1, these rules sit in three places: one lab test list, one settings block and one set of value rules. The query is generated from them. Adding a test code or changing a rule is now a file edit, not a code change.

* **Results are almost unchanged:** 99.9% of eGFR test-days and 99.5% of UACR test-days keep the same stage as in NBA 3.0.
* **Deliberate fixes:** UACR components no longer get a stage. eGFR 150–200 is stage 1 instead of 0. On the same day, the preferred eGFR equation is used.
* **More data used:** about 35.7K more eGFR test-days (26.8K patients) are now kept, from results such as `>90` and `75^`.
* **Faster:** 19% less data is pulled from Snowflake.
* **Visible data loss:** every run now prints a report of the rows dropped and why.
* **Validation HCPs:** no change in patients, test-days or CKD stage 3–5 months.

---

## 2. Product basket: old vs new snapshot

The product basket is the list of lab test codes the notebook uses. The old basket only listed the codes. The new basket also holds the rules for each code, so the notebook reads them from the file instead of the SQL.

### 2.1 What changed in the basket

| | Old basket | New basket |
| --- | --- | --- |
| File | `Kerendia NBA 3.1 - Lab Event List.csv` (kept unchanged) | `Kerendia_Lab_Final.csv` |
| Columns | 4: `EVENT_NAME`, `EVENT_CODE`, `EVENT_GROUP`, `IS_CLUBBED` | 12: `MATCH_TYPE`, `MATCH_VALUE`, `TEST_TYPE`, `ACTIVE`, `ROLE`, `PRIORITY`, `UNITS`, `VALID_MIN`, `VALID_MAX`, `STAGE_CUTOFFS`, `TEST_FAMILY`, `NOTE` |
| Rows | 23 LOINC codes | 23 LOINC codes (the same codes) + 5 test-name backup rows |
| eGFR codes | 8, all "eGFR TEST (ALL LOINC VARIANTS)" | Same 8, each with a same-day priority (1 to 3) |
| UACR codes | 13, all labelled "Albumin/Creatinine [Mass Ratio] in Urine" | Same 13: 2 staged ratios (`RESULT`) and 11 components that are never staged (`PART`) |
| Potassium, HbA1c | Listed, not grouped (`IS_CLUBBED = NO`) | Listed with units and valid range; switched off (`ACTIVE = N`) |
| Rules (units, valid range, stage cut-offs) | Not in the file (written in the SQL) | One column each, per code |
| Used by the notebook | No | Yes, read at the start of every run |

### 2.2 Old basket (`Kerendia NBA 3.1 - Lab Event List.csv`)

| EVENT_NAME | EVENT_CODE | EVENT_GROUP | IS_CLUBBED |
| --- | --- | --- | --- |
| eGFR | 33914-3 | eGFR TEST (ALL LOINC VARIANTS) | YES |
| eGFR | 48642-3 | eGFR TEST (ALL LOINC VARIANTS) | YES |
| eGFR | 50210-4 | eGFR TEST (ALL LOINC VARIANTS) | YES |
| eGFR | 62238-1 | eGFR TEST (ALL LOINC VARIANTS) | YES |
| eGFR AMONG BLACKS | 88293-6 | eGFR TEST (ALL LOINC VARIANTS) | YES |
| eGFR AMONG NON-BLACKS | 88294-4 | eGFR TEST (ALL LOINC VARIANTS) | YES |
| eGFR | 98979-8 | eGFR TEST (ALL LOINC VARIANTS) | YES |
| eGFR | 98980-6 | eGFR TEST (ALL LOINC VARIANTS) | YES |
| Albumin/Creatinine [Mass Ratio] in Urine | 13362-9 | UACR TEST (ALL LOINC VARIANTS) | YES |
| Albumin/Creatinine [Mass Ratio] in Urine | 14683-7 | UACR TEST (ALL LOINC VARIANTS) | YES |
| Albumin/Creatinine [Mass Ratio] in Urine | 14957-5 | UACR TEST (ALL LOINC VARIANTS) | YES |
| Albumin/Creatinine [Mass Ratio] in Urine | 14958-3 | UACR TEST (ALL LOINC VARIANTS) | YES |
| Albumin/Creatinine [Mass Ratio] in Urine | 1754-1 | UACR TEST (ALL LOINC VARIANTS) | YES |
| Albumin/Creatinine [Mass Ratio] in Urine | 19153-6 | UACR TEST (ALL LOINC VARIANTS) | YES |
| Albumin/Creatinine [Mass Ratio] in Urine | 2160-0 | UACR TEST (ALL LOINC VARIANTS) | YES |
| Albumin/Creatinine [Mass Ratio] in Urine | 2161-8 | UACR TEST (ALL LOINC VARIANTS) | YES |
| Albumin/Creatinine [Mass Ratio] in Urine | 34535-5 | UACR TEST (ALL LOINC VARIANTS) | YES |
| Albumin/Creatinine [Mass Ratio] in Urine | 35674-1 | UACR TEST (ALL LOINC VARIANTS) | YES |
| Albumin/Creatinine [Mass Ratio] in Urine | 49023-5 | UACR TEST (ALL LOINC VARIANTS) | YES |
| Albumin/Creatinine [Mass Ratio] in Urine | 61151-7 | UACR TEST (ALL LOINC VARIANTS) | YES |
| Albumin/Creatinine [Mass Ratio] in Urine | 9318-7 | UACR TEST (ALL LOINC VARIANTS) | YES |
| Potassium [Moles/volume] in Serum or Plasma | 2823-3 | Potassium [Moles/volume] in Serum or Plasma | NO |
| Hemoglobin A1c/Hemoglobin.total in Blood | 4548-4 | Hemoglobin A1c/Hemoglobin.total in Blood | NO |

### 2.3 New basket (`Kerendia_Lab_Final.csv`)

`TEST_FAMILY` is not shown: it is the same for every row of a test (GFR = "eGFR (CKD function)", UACR = "UACR (CKD albuminuria)", POTASSIUM = "Potassium (Kerendia safety)", HBA1C = "HbA1c (diabetes control)"). UACR units are `MCG/MGCREAT`, `MG/GCREAT`, `MG/GCR`, `MG/G{CREAT}`.

| MATCH_TYPE | MATCH_VALUE | TEST_TYPE | ACTIVE | ROLE | PRIORITY | UNITS | VALID_MIN | VALID_MAX | STAGE_CUTOFFS | NOTE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LOINC | 98979-8 | GFR | Y | RESULT | 1 | ML/MIN/1.73M2 | 1 | 200 | 15:5 \| 30:4 \| 60:3 \| 90:2 \| else:1 | CKD-EPI 2021 creatinine - race-free |
| LOINC | 98980-6 | GFR | Y | RESULT | 1 | ML/MIN/1.73M2 | 1 | 200 | 15:5 \| 30:4 \| 60:3 \| 90:2 \| else:1 | CKD-EPI 2021 creatinine + cystatin C - race-free |
| LOINC | 62238-1 | GFR | Y | RESULT | 2 | ML/MIN/1.73M2 | 1 | 200 | 15:5 \| 30:4 \| 60:3 \| 90:2 \| else:1 | CKD-EPI 2009 |
| LOINC | 33914-3 | GFR | Y | RESULT | 2 | ML/MIN/1.73M2 | 1 | 200 | 15:5 \| 30:4 \| 60:3 \| 90:2 \| else:1 | MDRD |
| LOINC | 48642-3 | GFR | Y | RESULT | 2 | ML/MIN/1.73M2 | 1 | 200 | 15:5 \| 30:4 \| 60:3 \| 90:2 \| else:1 | MDRD - non-Black |
| LOINC | 88294-4 | GFR | Y | RESULT | 2 | ML/MIN/1.73M2 | 1 | 200 | 15:5 \| 30:4 \| 60:3 \| 90:2 \| else:1 | CKD-EPI 2009 - non-Black |
| LOINC | 50210-4 | GFR | Y | RESULT | 2 | ML/MIN/1.73M2 | 1 | 200 | 15:5 \| 30:4 \| 60:3 \| 90:2 \| else:1 | cystatin C |
| LOINC | 88293-6 | GFR | Y | RESULT | 3 | ML/MIN/1.73M2 | 1 | 200 | 15:5 \| 30:4 \| 60:3 \| 90:2 \| else:1 | CKD-EPI 2009 - Black - used only if nothing else that day |
| NAME | %AMONG BLACKS% | GFR | Y | RESULT | 3 | ML/MIN/1.73M2 | 1 | 200 | 15:5 \| 30:4 \| 60:3 \| 90:2 \| else:1 | backup for rows without a basket code - Black version |
| NAME | %GFR% | GFR | Y | RESULT | 2 | ML/MIN/1.73M2 | 1 | 200 | 15:5 \| 30:4 \| 60:3 \| 90:2 \| else:1 | backup for rows without a basket code (3.0 rule) |
| NAME | %GLOMERULAR% | GFR | Y | RESULT | 2 | ML/MIN/1.73M2 | 1 | 200 | 15:5 \| 30:4 \| 60:3 \| 90:2 \| else:1 | backup for rows without a basket code (3.0 rule) |
| LOINC | 9318-7 | UACR | Y | RESULT | 1 | UACR units | 0 | 10000 | 30:1 \| 300:2 \| else:3 | albumin/creatinine ratio |
| LOINC | 14958-3 | UACR | Y | RESULT | 1 | UACR units | 0 | 10000 | 30:1 \| 300:2 \| else:3 | microalbumin/creatinine ratio |
| LOINC | 2161-8 | UACR | Y | PART | | | | | | urine creatinine - not a ratio - never staged |
| LOINC | 14683-7 | UACR | Y | PART | | | | | | urine creatinine - never staged |
| LOINC | 35674-1 | UACR | Y | PART | | | | | | urine creatinine - never staged |
| LOINC | 2160-0 | UACR | Y | PART | | | | | | serum creatinine - never staged |
| LOINC | 14957-5 | UACR | Y | PART | | | | | | microalbumin concentration - never staged |
| LOINC | 1754-1 | UACR | Y | PART | | | | | | urine albumin concentration - never staged |
| LOINC | 61151-7 | UACR | Y | PART | | | | | | serum albumin - never staged |
| LOINC | 19153-6 | UACR | Y | PART | | | | | | urine volume - never staged |
| LOINC | 13362-9 | UACR | Y | PART | | | | | | collection duration - never staged |
| LOINC | 49023-5 | UACR | Y | PART | | | | | | 24h albumin - not a ratio - never staged |
| LOINC | 34535-5 | UACR | Y | PART | | | | | | text results only - never staged |
| NAME | %ALB% | UACR | Y | RESULT | 2 | UACR units | 0 | 10000 | 30:1 \| 300:2 \| else:3 | backup for rows without a basket code (3.0 rule) |
| NAME | %RATIO% | UACR | Y | RESULT | 2 | UACR units | 0 | 10000 | 30:1 \| 300:2 \| else:3 | backup for rows without a basket code (3.0 rule) |
| LOINC | 2823-3 | POTASSIUM | N | RESULT | 1 | MMOL/L | 1 | 10 | | not used in the lab journey yet (new features) |
| LOINC | 4548-4 | HBA1C | N | RESULT | 1 | % | 3 | 20 | | not used in the lab journey yet (new features) |

**How to read `STAGE_CUTOFFS`:** `15:5 | 30:4 | 60:3 | 90:2 | else:1` means below 15 → stage 5, below 30 → stage 4, below 60 → stage 3, below 90 → stage 2, otherwise stage 1.

---

## 3. Old vs new at a glance

| Area | Old notebook (NBA 3.0) | New notebook (NBA 3.1) | Benefit |
| --- | --- | --- | --- |
| Input data | Read a pre-built 3.0 lab table | Runs the lab query directly from Snowflake | No dependency on a table that can be removed in a data refresh |
| Which tests count | Test name text search only (`%GFR%`, `%GLOMERULAR%`, `%ALB%`, `%RATIO%`) | LOINC codes from the lab test list; the old name search is kept as a backup | Renamed tests are not lost; unrelated tests with "ALB" or "RATIO" in the name are left out |
| Test rules | Written in the SQL | Lab test list (CSV), one row per code | Adding a test or changing a rule is a file edit |
| Run settings (dates, specialties, tables) | Written in the SQL; two start dates (`2021-11-30` and `2023-01-01`) | One settings block (`LAB_CONFIG`); one start date; checks that tables and columns exist | One place to change settings; clear error if a table is renamed |
| Reading result values | Plain numbers only; `>`, `<`, `^` dropped | Lab flags removed (`75^` → 75); `>X` / `<X` kept when the stage is certain | More valid results kept |
| Same-day results | Median of all eGFR equations | Preferred equation first (priority), then median | Black and non-Black equations no longer mixed |
| Data loss | Silent | Dropped-rows report on every run | Full transparency of what is excluded and why |
| Output | Patient, date, eGFR stage, UACR stage | Same 4 columns (plus LOINC codes used and matching method, for review) | Downstream notebooks need no change |
| Validation | None in the notebook | Row-by-row comparison after each step (all US + validation HCPs) | Every change is measured |

---

## 4. Lab tests covered

### 4.1 Tests: what was already there and what is new

| Test | Purpose | Old notebook (3.0) | New notebook (3.1) | Status |
| --- | --- | --- | --- | --- |
| **eGFR** | CKD stage (kidney function) | Yes, found by test name | Yes, 8 LOINC codes + name backup | **Existing**, improved |
| **UACR** | Albuminuria stage (A1–A3) | Yes, found by test name | Yes, 2 ratio codes staged + 11 component codes excluded + name backup | **Existing**, improved |
| **Potassium** (LOINC 2823-3) | Kerendia safety monitoring (hyperkalemia) | No | In the lab test list with units (mmol/L) and valid range (1–10); switched off (`ACTIVE = N`) | **New**, ready to switch on |
| **HbA1c** (LOINC 4548-4) | Diabetes control (T2D) | No | In the lab test list with units (%) and valid range (3–20); switched off (`ACTIVE = N`) | **New**, ready to switch on |

Potassium and HbA1c are prepared for the new patient features planned for NBA 3.1. They do not affect the CKD staging today. To use them, set `ACTIVE = Y` in the lab test list. The business reasoning for Potassium is in section 4.4, and for HbA1c in section 4.5.

### 4.2 eGFR codes and same-day priority

| Priority | LOINC | Equation | Old notebook | New notebook |
| --- | --- | --- | --- | --- |
| 1 | 98979-8 | CKD-EPI 2021, creatinine, race-free | Found by name, averaged with other equations | Preferred result of the day |
| 1 | 98980-6 | CKD-EPI 2021, creatinine + cystatin C, race-free | Same | Preferred result of the day |
| 2 | 62238-1 | CKD-EPI 2009 | Same | Used if no priority-1 result |
| 2 | 33914-3 | MDRD | Same | Used if no priority-1 result |
| 2 | 48642-3 | MDRD, non-Black | Same | Used if no priority-1 result |
| 2 | 88294-4 | CKD-EPI 2009, non-Black | Same | Used if no priority-1 result |
| 2 | 50210-4 | Cystatin C | Same | Used if no priority-1 result |
| 3 | 88293-6 | CKD-EPI 2009, Black | Same | Used only if nothing else that day |
| 2 / 3 | Name backup | `%GFR%`, `%GLOMERULAR%`, `%AMONG BLACKS%` | Only method | Used for rows without a listed code |

### 4.3 UACR codes: results vs components

**What the `ROLE` column means.** Every code in the lab test list has a role:

| ROLE | Meaning | What the notebook does |
| --- | --- | --- |
| `RESULT` | The answer of the test: the value a doctor uses to stage the patient | Kept, ranked by same-day priority, and staged with the cut-offs |
| `PART` | A measurement taken while doing the test, or a related value, but not the test result itself | Recognised, then excluded. Never staged |

**Why UACR needs this.** UACR is a ratio: urine albumin divided by urine creatinine, reported in mg/g. To produce it, the lab also measures albumin alone (mg/L), creatinine alone (mg/dL), and sometimes urine volume and collection time. Each of these is reported as a separate row with its own LOINC code. Applying the UACR cut-offs (30 / 300 mg/g) to these values would give wrong stages: for example, a urine albumin concentration of 45 mg/L is not stage A2. The old list labelled all 13 UACR codes as "Albumin/Creatinine [Mass Ratio] in Urine". The new list marks only the 2 real ratio codes as `RESULT` and the other 11 as `PART`. All 8 eGFR codes are results, so eGFR has no `PART` rows.

| Role | LOINC | What it measures | Old notebook | New notebook |
| --- | --- | --- | --- | --- |
| Result (staged) | 9318-7 | Albumin/creatinine ratio | Staged | Staged |
| Result (staged) | 14958-3 | Microalbumin/creatinine ratio | Staged | Staged |
| Component | 2161-8, 14683-7, 35674-1 | Urine creatinine | Could be staged if the name matched | Not staged |
| Component | 2160-0 | Serum creatinine | Could be staged | Not staged |
| Component | 14957-5, 1754-1 | Albumin concentration (not a ratio) | Could be staged | Not staged |
| Component | 61151-7 | Serum albumin | Could be staged | Not staged |
| Component | 19153-6, 13362-9 | Urine volume, collection duration | Could be staged | Not staged |
| Component | 49023-5 | 24-hour albumin (not a ratio) | Could be staged | Not staged |
| Component | 34535-5 | Text results only | Could be staged | Not staged |
| Result (backup) | Name backup | `%ALB%`, `%RATIO%` | Only method | Used for rows without a listed code |

**Why the components stay in the list instead of being removed.** If the 11 component codes were deleted, many of their rows would come back through the test-name backup. A test named "MICROALBUMIN, URINE" matches `%ALB%` and would be read as a UACR result. The listed code is always checked before the name backup, so keeping these codes as `PART` blocks them from being staged.

**How `ROLE` is used in the notebook.**

| Where | Use of `ROLE` |
| --- | --- |
| Reading the lab test list | Checks that every row is `RESULT` or `PART`. Test rules (units, valid range, cut-offs) are built from `RESULT` rows only, so `PART` rows have empty `PRIORITY`, `UNITS`, `VALID_MIN`, `VALID_MAX` and `STAGE_CUTOFFS` |
| Lab query | Keeps only `RESULT` rows, before the same-day priority and the median |
| Dropped-rows report | Counts excluded components as "part of a test, not a result": 16.0M UACR source rows, 2023-01 to 2026-09 (section 8) |
| Validation | Most of the 68.4K UACR test-days no longer included vs NBA 3.0 are these components (section 7.1) |

### 4.4 Why Potassium is added: business reasoning

**Clinical background.** Kerendia (finerenone) blocks the mineralocorticoid receptor. One effect is that the kidneys keep more potassium, so serum potassium can rise (hyperkalemia). The risk is higher when kidney function is low. For this reason, the Kerendia label ties treatment to serum potassium:

| Moment | What the label asks for (summary) |
| --- | --- |
| Before starting | Measure serum potassium and eGFR. Start only if potassium is ≤ 5.0 mmol/L |
| After starting or a dose change | Re-check potassium after about 4 weeks |
| During treatment | Monitor potassium regularly; adjust the dose, or pause treatment if potassium is too high |

*Exact thresholds and timing are to be confirmed against the current US label with Medical.*

This applies to **both** Kerendia indications: CKD associated with type 2 diabetes, and heart failure with LVEF ≥ 40% (section 9.4).

**Why it matters for the business.**

| Reason | Explanation | How it can be used in NBA 3.1 |
| --- | --- | --- |
| Potassium decides eligibility | A patient with CKD and T2D is only "ready" for Kerendia if potassium is ≤ 5.0 mmol/L | Count "Kerendia-ready" patients per HCP (CKD + T2D + potassium ≤ 5.0, not on Kerendia): HCPs with an eligible, untreated panel |
| Fear of hyperkalemia is a main prescribing barrier | HCPs often hesitate to start, or stop, MR-blocking drugs because of potassium concerns | Count patients with high potassium (> 5.0 mmol/L) per HCP: HCPs whose panel makes them likely to be concerned about safety |
| Different HCPs need different messages | An HCP with many eligible patients needs efficacy messages; an HCP with many high-potassium patients needs safety and potassium-management messages | Supports choosing the next best message per HCP, not only the next best HCP |
| Monitoring shows readiness to prescribe | HCPs who regularly test potassium already follow the monitoring routine the label requires | Potassium testing frequency per HCP as a readiness signal |
| Explains stopping treatment | A rise in potassium after starting is a common reason to pause or stop | Potassium after the first Kerendia prescription, to understand persistence |
| Wide data coverage | Serum potassium is part of the basic and comprehensive metabolic panels, so it is one of the most often ordered lab tests | Gives potassium values for most patients who have lab data |

**What is in place and what is next.**

| Item | Status |
| --- | --- |
| Potassium code (LOINC 2823-3) in the lab test list, with units (mmol/L) and valid range (1–10) | Done; switched off (`ACTIVE = N`) |
| Switch on and keep the potassium value (not a stage) in the patient journey output | Planned (section 9.3) |
| Patient features: last potassium value, flag above 5.0 mmol/L | Planned (section 9.3) |
| HCP features: "Kerendia-ready" patients, high-potassium patients | Planned |
| Potassium signal for patients without lab data: hyperkalemia diagnosis (E87.5) and potassium binders (Lokelma, Veltassa) | Planned in the Dx and Rx baskets (section 9.3) |
| Review other potassium codes (e.g. 6298-4, potassium in blood) for the lab test list | To review |

### 4.5 Why HbA1c is added: business reasoning

**Clinical background.** HbA1c (glycated haemoglobin) shows a patient's average blood sugar over the last 2–3 months, as a percentage. It is the standard test to diagnose type 2 diabetes (T2D) and to follow how well it is controlled.

| HbA1c | Usual reading |
| --- | --- |
| < 5.7% | Normal |
| 5.7–6.4% | Prediabetes |
| ≥ 6.5% | Diabetes |
| < 7% | Common treatment target for most adults with diabetes |
| ≥ 9% | Poorly controlled diabetes |

*Thresholds follow common diabetes guidelines; to be confirmed with Medical.*

Kerendia's first indication is CKD **associated with T2D**, so diabetes is part of the label population. Unlike potassium, HbA1c is **not** a label requirement for starting Kerendia, and Kerendia does not lower blood sugar. HbA1c is added to describe the patient and the HCP's panel, not as a safety check.

**Why it matters for the business.**

| Reason | Explanation | How it can be used in NBA 3.1 |
| --- | --- | --- |
| Confirms the T2D part of the label population | Today T2D is identified from diagnosis text and diabetes prescriptions. An HbA1c ≥ 6.5% is a lab confirmation, and can find patients whose diabetes is not coded | Supports the T2D flag and the "CKD + T2D" label patient count per HCP. HbA1c alone cannot tell type 1 from type 2, so it complements the Dx/Rx flag rather than replacing it |
| Shows how sick the diabetes panel is | Patients with poorly controlled diabetes (HbA1c ≥ 9%) have a higher risk of kidney disease getting worse | Share of an HCP's CKD + T2D patients with uncontrolled diabetes: HCPs with a higher-risk panel |
| Shows where the HCP's attention is | When blood sugar is far off target, HCPs often focus first on glucose-lowering drugs (e.g. GLP-1, SGLT2, insulin), and kidney protection may come later | Supports a message that Kerendia protects the kidneys and heart independently of blood sugar, for HCPs with many uncontrolled patients |
| Finds testing gaps | Guidelines recommend regular HbA1c and at least yearly UACR and eGFR in T2D. An HCP who tests HbA1c often but rarely tests UACR is unlikely to see albuminuria, and so may not identify Kerendia patients | HbA1c testing vs UACR testing per HCP: an education signal |
| Wide data coverage | HbA1c is ordered every 3–6 months for most people with diabetes. Testing can also be seen from procedure claims (CPT 83036 / 83037) | Gives a diabetes signal for most diabetic patients, including HCPs without Quest data (testing only, no value) |

In the NBA 3.1 plan, HbA1c features are optional (lower priority than Potassium), because the T2D flag already comes from diagnosis and prescription data.

**What is in place and what is next.**

| Item | Status |
| --- | --- |
| HbA1c code (LOINC 4548-4) in the lab test list, with unit (%) and valid range (3–20) | Done; switched off (`ACTIVE = N`) |
| Switch on and keep the HbA1c value (not a stage) in the patient journey output | Planned (section 9.3) |
| Patient features: last HbA1c value, flag at 9% or more | Planned (section 9.3) |
| HbA1c testing from procedure claims (CPT 83036 / 83037) | Planned (section 9.3) |
| HCP features: share of uncontrolled diabetes patients, HbA1c vs UACR testing | Candidate |
| Review other HbA1c codes for the lab test list (e.g. 17856-6 and 4549-2 for other test methods, 59261-8 for results in mmol/mol) | To review |

---

## 5. Each rule in the old notebook and where it is now

| # | Old notebook (written in the SQL) | New notebook | What improves |
| --- | --- | --- | --- |
| 1 | **Which tests count:** name text search | LOINC codes in the lab test list; name search kept as backup | Tests are identified by standard codes |
| 2 | **Test labels** `GFR` / `UACR` repeated in the SQL | `TEST_TYPE` column in the lab test list | A new test is added as new rows; its stage column is created automatically |
| 3 | **Units:** one list shared by both tests | One unit list per test | A UACR unit cannot be accepted for eGFR, and the other way round |
| 4 | **Stage cut-offs** 15/30/60/90 (eGFR) and 30/300 (UACR) in the SQL | `STAGE_CUTOFFS` column (same values) | A cut-off change (e.g. stage 3a/3b) is a file edit |
| 5 | **Valid range:** none. eGFR > 150 got stage 0; eGFR = 0 got stage 5 | eGFR 1–200, UACR 0–10,000 | Invalid values are excluded instead of getting a wrong stage; eGFR 150–200 is now stage 1 |
| 6 | **Value format:** plain numbers only | Lab flags removed; `>X` / `<X` kept when the stage is certain (e.g. `>90` = stage 1, `<15` = stage 5); `>60` not staged | More valid results kept, no guessing |
| 7 | **Specialty filter:** 10 primary-care codes in the SQL | Same list in the settings block; can be changed or removed | Ready for the specialty decision (section 9) |
| 8 | **Start date** written twice | One start date (`DATA_START_DATE`), applied in the query | No conflicting dates |
| 9 | **End date** applied after pulling all history | Applied in the query | 19% less data pulled |
| 10 | **Date formats** in a fixed `CASE` | List of formats, safely parsed; unreadable dates counted | New date formats are detected |
| 11–12 | **Table and column names** in the SQL | Settings block, checked before the run | Clear error if the vendor renames a table or column |
| 13 | **Patient ID rule** in the SQL | One shared rule; dropped rows counted | Same rule, now visible |
| 14 | **Same day:** median of all results | Priority per code, then median; exact values before `>` / `<` values at the same priority | Preferred equation is used |
| 15 | **Output columns** fixed | Follow the tests in the lab test list | New tests flow to the output with no code change |

---

## 6. How the new notebook works

| Step | Input | What it does | Output |
| --- | --- | --- | --- |
| 1. Read lab test list | `Kerendia_Lab_Final.csv` | Keeps active tests; checks for duplicate codes, consistent rules per test, valid roles; checks cut-offs go from low to high | Test rules per test |
| 2. Read settings | `LAB_CONFIG` | Dates, specialties, date formats, source tables and columns; checks that tables and columns exist | Run settings |
| 3. Value rules | `VALUE_RULES`, `PATIENT_ID_RULE` | How result values and patient IDs are read | Shared rules |
| 4. Build and run query | Steps 1–3 | Generates the SQL, runs it in Snowflake, joins the HCP universe | Patient × day × test stages |
| 5. Dropped-rows report | Same query steps | Counts every source row under the first rule it fails | Report of excluded data |
| 6. Patient journey | Step 4 | Monthly stages with carry-forward to the next test (unchanged from 3.0) | Lab stage table for the patient journey |

Each change was introduced in a separate step and compared row by row with the step before.

---

## 7. Validation results

### 7.1 All US patients, 2025-01 to 2026-09 (test-days = patient × day × test)

| Result | eGFR | UACR |
| --- | --- | --- |
| Same stage as NBA 3.0 | 106.73M (99.9%) | 19.81M (99.5%) |
| Stage changed | 65.3K (0.06%) | 27.4K (0.14%) |
| – from eGFR 150–200 now stage 1 (was 0) | 10.4K | – |
| – from preferred equation on the same day | ~55K | 27.4K |
| No longer included | 260 (eGFR above 200 or equal to 0) | 71.0K (68.4K components, 2.5K above 10,000) |
| Newly included (`>90`, `<15`, `75^`, ...) | +35.7K (26.8K patients) | +1.3K |

An additional check on 2023–2024 data found +75.7K eGFR test-days from values with lab flags (`75^`), which appear only in 2023 data.

### 7.2 Validation HCPs (10 doctors, 2023-01 to 2026-09)

| Metric | NBA 3.0 | NBA 3.1 | Change |
| --- | --- | --- | --- |
| Patients | 225 | 225 | 0 |
| eGFR test-days | 878 | 878 | 0 |
| UACR test-days | 289 | 289 | 0 |
| Patient-months | 6,139 | 6,139 | 0 |
| Patient-months with eGFR stage 3–5 | 2,347 | 2,347 | 0 |
| Patient-months with UACR A2–A3 | 1,504 | 1,504 | 0 |
| Patient-months with any eGFR stage | 5,981 | 6,007 | +26 (eGFR 150–200 now stage 1) |

### 7.3 Run efficiency

| | NBA 3.0 settings | NBA 3.1 settings |
| --- | --- | --- |
| Rows pulled from Snowflake | 312.9M | 252.2M (−19%) |
| Unreadable service dates | Not reported | 38 empty, 0 unknown format (of 1.72B source rows) |

---

## 8. What is excluded and why (new dropped-rows report)

All US, 2023-01 to 2026-09, source rows. NBA 3.0 excluded the same rows but did not report them.

| Reason | eGFR rows | UACR rows | Can be recovered? |
| --- | --- | --- | --- |
| Patient ID missing or invalid | 65.6M | 11.8M | No |
| Prescriber NPI missing | 24.3M | 3.8M | No |
| Component of a test, not a result | – | 16.0M | No (by design) |
| Value empty or text (e.g. "DNR", "See comment") | 12.3M | 6.8M | No |
| Unit not allowed | – | 32.8K | Possibly (add unit to the list) |
| Outside valid range | 4.6M | 26.2K | No |
| `>` / `<` value with unclear stage (e.g. `>60`) | 827K | 314 | Decision (section 9) |
| **Specialty not in the 10 primary-care codes** | **211.4M** | **21.2M** | **Decision (section 9)** |
| **Kept** | **631.9M** | **106.9M** | – |

The specialty filter is the largest single exclusion, and the excluded rows are valid patient data.

---

## 9. Decisions

### 9.1 Decisions made

| Decision | Choice | Reason |
| --- | --- | --- |
| eGFR valid maximum | 200 (was 150) | Values 150–200 are stage 1, not invalid |
| Source of lab test rules | One lab test list (CSV); the original list is kept unchanged | Single place for all test rules |
| Test-name backup | Kept | Rows without a LOINC code are still found |
| Same-day results | Lowest priority number wins; an exact value beats a `>` / `<` value at the same priority | Uses the preferred eGFR equation |
| Lab flags (`^`) | Read as the number | Valid results are not lost |

### 9.2 Decisions for the final review

| # | Decision | Options | Impact |
| --- | --- | --- | --- |
| 1 | Specialty filter | (a) keep the 10 primary-care codes, (b) remove the filter, (c) add cardiology, endocrinology and nephrology | Removing it adds about 16% more eGFR patients and 13% more UACR patients |
| 2 | `>60` eGFR results (827K rows) | (a) keep excluded (conservative), (b) count as "not CKD stage 3+" | (b) adds patients who are very unlikely to be CKD stage 3+ |
| 3 | Location of the settings block | (a) lab notebook, (b) shared patient-journey config | (b) shares the same settings with the other patient-journey notebooks |

### 9.3 Planned lab additions (from the NBA 3.1 patient journey plan)

Potassium and HbA1c are the only new lab tests planned. The plan also includes the following lab-related additions, which extend the existing tests or add new signals around them:

| What | Planned item | What it means for the lab notebook |
| --- | --- | --- |
| Missing codes for existing tests | 14959-1 (microalbumin/creatinine ratio, UACR) and 48643-1 (MDRD, Black, eGFR) | Add rows to the existing UACR and eGFR tests in the lab test list |
| Lab testing from procedure claims | CPT 82043 (urine albumin), 82570 (urine creatinine), 82565 (serum creatinine), 80047 / 80048 / 80053 (panels with creatinine), 83036 / 83037 (HbA1c) | "Tested yes / no" flags from procedure claims, to cover HCPs without Quest lab data. No result values |
| Lab-based CKD flag | Two eGFR < 60 or two UACR ≥ 30, at least 90 days apart (KDIGO definition) | New patient flag built from existing eGFR / UACR results |
| eGFR value and decline | Last eGFR value; eGFR fall of 30% or more within 24 months | Needs the eGFR value kept in the output, not only the stage |
| Potassium features | Last potassium value; flag above 5.0 mmol/L | Used for "Kerendia-ready" and high-potassium barrier counts per HCP. Needs Potassium switched on and its value kept in the output |
| HbA1c features | Last HbA1c value; flag at 9% or more (uncontrolled diabetes) | Needs HbA1c switched on and its value kept in the output |
| CKD stage 3a / 3b split | eGFR 45–59 = stage 3a, 30–44 = stage 3b | Change to the eGFR stage cut-offs in the lab test list |
| Potassium signal without lab data | Hyperkalaemia diagnosis (E87.5) and potassium binders (Lokelma, Veltassa) | Added to the Dx and Rx product baskets, not the lab test list |
| Additional lab source | LabCorp | Same tests from a second lab, if a current LabCorp feed is available. Open questions on availability, patient ID matching and overlap with Quest |

All value-based features (eGFR decline, Potassium, HbA1c) require the result value to be carried into the patient journey output. Today the output keeps the stage columns only.

### 9.4 LVEF and the heart failure indication

**What LVEF is.** LVEF (left ventricular ejection fraction) is the share of blood the heart's main pumping chamber pushes out with each beat. It is the main measure used to classify heart failure (HF) and is usually measured by echocardiogram.

| LVEF | HF type | Kerendia HF indication |
| --- | --- | --- |
| ≥ 50% (normal about 50–70%) | HFpEF: preserved ejection fraction | Covered |
| 40–49% | HFmrEF: mildly reduced ejection fraction | Covered |
| < 40% | HFrEF: reduced ejection fraction | Not covered |

Kerendia's second indication is heart failure with LVEF ≥ 40% (FINEARTS-HF trial). Clinical guidelines usually define HFrEF as LVEF ≤ 40% and HFmrEF as 41–49%, so a patient at exactly 40% sits on the boundary. The exact cut-off wording is to be confirmed against the current US label with Medical.

**Where LVEF can be found in claims.** LVEF is an imaging result, not a lab test, so it is **not in the Quest lab data**. The value is recorded in the echo report or the medical record, which claims do not carry. Claims only give proxies:

| Claim type | What it shows | Example codes | Gives the LVEF? |
| --- | --- | --- | --- |
| Lab (Quest) | Nothing for LVEF | – | No |
| Dx (diagnosis) | Type of heart failure coded by the doctor | I50.2x systolic (reduced, mostly LVEF ≤ 40%), I50.3x diastolic (preserved), I50.4x combined, I50.9 unspecified | Indirectly (proxy) |
| Px (procedure): imaging | That LVEF was measured, not the result | CPT 93306 / 93303–93308 (echocardiogram), 93350 / 93351 (stress echo), 78472 (MUGA scan), 75557–75565 (cardiac MRI) | No |
| Px: quality codes (CPT II) | Quality-reporting codes some doctors add to claims | 3021F = LVEF < 40%, 3022F = LVEF ≥ 40%, 3020F = LV function assessed | Yes, as a 40% band, but only where reported (usually low coverage) |

**How it is used in NBA 3.1.**
* The planned HF features use the Dx-based HF type as the main proxy: diastolic HF (I50.3x) for the covered population (LVEF ≥ 40%), systolic HF (I50.2x) for the population outside the label.
* The proxy is approximate: diagnosis codes do not record the 40% threshold, and the unspecified code I50.9 is common.
* The CPT II codes 3021F / 3022F record the 40% band directly. Their coverage in procedure claims will be checked before the HF feature design is finalised.
* Echocardiogram procedure claims can support an "HF being evaluated" signal.

LVEF does not change the lab notebook. The HF features are built from the Dx and Px patient journeys.

---

## 10. Next steps

| Step | Description |
| --- | --- |
| 1 | Confirm the decisions in section 9.2 |
| 2 | Switch the patient-journey output from the NBA 3.0 query to the new query (one-variable change) and write the lab stage table |
| 3 | Re-run the downstream patient-journey combine and HCP-level notebooks, and compare stage counts |
| 4 | Switch on Potassium and HbA1c when the new patient features are built |
| 5 | Review two additional codes for the lab test list: 14959-1 (microalbumin/creatinine ratio) and 48643-1 (MDRD, Black) |
