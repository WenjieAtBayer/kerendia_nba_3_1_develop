# NBA 3.1 – Px patient journey (PJ05): analysis and plan

**Status (2026-10-29):** plan approved; decisions D1–D5 taken as proposed (section 6). Phase A Steps 0–5 built and run in `05_patient_journey_px`; Step 5 (write) is switched off (`WRITE_OUTPUT = False`) and goes live only together with the 3.1 Dx table. D1 confirmed after the Dx check (section 0, item 1). Results summary in section 0.  
**Old notebook:** `Px Files/(Clone) 05_patient_journey_px` (created 2026-10-29 from the 3.0 cells, kept unchanged as the baseline; see section 9)  
**New notebook:** `Px Files/05_patient_journey_px`  
**Original Px basket:** `Final Product Basket/Kerendia NBA 3.1 - PX Event List.csv` (the former `Kerendia_Px_Final.csv`, renamed with `git mv`, content unchanged; decision D4)  
**New Px basket:** `Final Product Basket/Kerendia_Px_Final.csv` (145 rows = 152 codes, new format of section 5: the 130 original rows + 15 added under D2; 29 codes counted as dialysis)  
**Related:** Dx plan item Q2 (dialysis and transplant procedure codes in the old Dx list belong in Px), `06_patient_journey_combine` cell "Add dialysis flag"  
**Approach:** same as the lab and Dx notebooks: keep the 3.0 query as the baseline, add one step at a time, and compare each step with the one before.  
**Scope:** Phase A only (match 3.0, make it dynamic, measure every change). HF and T1D procedures are Phase B (section 8).

---

## 0. Implementation results

Run 2026-10-29, all US patients (all history to `date_end` 2026-09-30) and validation patients (4,238 patients of the 10 validation HCPs, 137,373 patient-months, `DIALYSIS_FLAG` built as in `06_patient_journey_combine`).

| Step | Check | Result |
| --- | --- | --- |
| 0 | 3.0 query vs the table last written by the old notebook | Identical: 1,489,202 patients, 0 different first dates, 0 empty `PATIENT_ID` |
| 1 | Profile of the `'%DIALYSIS%'` text match | 32 codes (31 with claims, ICD-9 `39.95` has none). 15 were not in the basket (added under D2, see below). Not caught: ESRD monthly services 90960 / 90961 / 90962, home visit 99512, difelikefalin J0879. Procedure history starts 2021-01-02 |
| 2a | Basket vs original Px Event List | 130 original rows identical (codes, patient counts, flags) + 15 rows added (D2); 29 codes count as dialysis |
| 2 | Basket query vs 3.0, all US | Same 1,087,148; earlier 268,617 (median 134 days, from 90960–90962); later 45,596 (median 20 days); gained 134,972 (90960–90962); lost 87,841 (access only: C1750, 36800, C1752). Total 1,489,202 → 1,536,333 (+3.2%) |
| 2 | Validation patients | Months flagged 7,649 → 8,413 (844 months 0 → 1, 80 months 1 → 0); patients ever flagged 325 → 363 |
| 3 | Config query vs Step 2 | Identical except 281 patients whose first dialysis is after `date_end` (2026-10-01 / 10-02); validation identical |
| 4 | Output columns + dropped-rows report | Identical first dates (1,536,052 patients); dropped: 10,169 rows after `date_end` (0.0044%), 0 empty patient or date. First event: session 61.5%, ESRD monthly 34.2%, ESRD drug 2.6%, training 1.7% |
| 5 | Write | Switched off; the table still holds the 3.0 output of 2026-10-26 |

**D2 additions to `Kerendia_Px_Final.csv`** (`NOTE = Added 2026-10-29 (D2): caught by 3.0 text match`, `PATIENTS_TOTAL` empty):

| PX_GROUP | Counted | Codes | Patients (all history) |
| --- | --- | --- | --- |
| ESRD_MONTHLY | Y | 90970, 90969, 90968, 90967, 90965, 90964, 90963 | 172,178 / 815 / 511 / 804 / 1,129 / 807 / 389 |
| DIALYSIS_DRUG | Y | Q0139 (ferumoxytol), J0890 (peginesatide), J3591 (unclassified ESRD drug), J0886 (epoetin alfa 1000 U) | 5,774 / 206 / 142 / 99 |
| DIALYSIS_ACCESS | N | 36838 (DRIL), 36815 (AV cannula), 90940, 90939 (access flow study) | 2,455 / 287 / 1,715 / 8 |

**Correction to section 2 (Q2):** the text match has no wrong matches of the kind expected. C1751 and 93985 / 93986 are not caught by it. The first dates that come too early, or patients without dialysis, come from access codes (catheters C1750 / C1752, cannula 36800), which no longer count under D1.

**For review:**
1. **DECIDED 2026-10-29 (user): D1 final, access procedures stay out of the dialysis flag. Go-live rule: the 3.1 Px table is written only when the 3.1 Dx table goes live too (not before).** Background: keeping access out means 87,841 access-only patients are no longer flagged, and 45,596 get a later first date. Switching is a basket edit (`ACTIVE_DIALYSIS = Y` on `DIALYSIS_ACCESS`).
   **Dx check (cell 2f, 2026-10-29):** ESRD or dialysis diagnosis (`N18.6`, `Z99.2`, `Z49.x`) for 88.6% of the patients still counted (reference), against 8.8% for short-term catheter C1752 (24,300 patients; 87.5% have none of the codes checked), 48.6% for long-term catheter C1750 (31,669), 25.7% for cannula 36800 (31,350) and 57.1% for other access (522). Overall about 25,900 of the 87,841 (29%) have such a diagnosis. AKI (`N17`) cannot be checked: there are no `N17` rows in the Dx fact table.
   **Recommendation: keep access out (D1 as is).** Counting it would make about 62,000 patients with no dialysis diagnosis not eligible in PJ06 (`DIALYSIS_FLAG = 1` → `ELIGIBLE_PATIENT_FLAG = 0`), almost all the C1752 patients among them. The end-stage patients among them are caught by the Dx stage 5 (`N18.6`), which is not eligible. **Condition:** that only holds with the 3.1 Dx output, and PJ06 still reads the 3.0 Dx table. So write the 3.1 Px table together with the 3.1 Dx table, not before.
2. Effect on `06_patient_journey_combine`: it drops only `FIRST_DIALYSIS_DATE` after the join, so the new QC columns `FIRST_DIALYSIS_CODE` and `FIRST_DIALYSIS_GROUP` would be carried into the combined table. Either drop them in PJ06, or write only `PATIENT_ID` and `FIRST_DIALYSIS_DATE`.
3. PJ06's `< 2017-01-01` rule never applies (history starts 2021). Keep it or remove it.
4. Switch on the write (Step 5): **on hold** until the 3.1 Dx table goes live (rule in item 1). Items 2 and 3 are done in the same `06_patient_journey_combine` update as the Dx changes; PJ06 stays as it is until then (user, 2026-10-29).

---

## 1. Current notebook: what it does

| Cell | What it does |
| --- | --- |
| 1 | Header (out of date: names `PUB_CAR_IQV_LAAD_PX_FCT`; the code reads `STG_CAR_IQV_LAAD_FACT_PX`) |
| 2–3 | `00_connection`, `00_cohort_config` |
| 4 | **3.0 Px query** from Snowflake |
| 5 | Review markdown (added 2026-10-29) |
| 6 | Write `kerendia_nba_3_1_px_validation` |

Output columns: `PATIENT_ID, FIRST_DIALYSIS_DATE, DIALYSIS_FLAG (always 1)`. One row per patient, all US (1,489,202 rows on 2026-10-26).

### 1.1 The 3.0 query in short

1. Reads `PATIENT_ID, SERVICE_DATE, PROCEDURE_CODE` from all of `STG_CAR_IQV_LAAD_FACT_PX`.
2. Inner-joins `STG_IQVIA_LAAD_DIM_PROCEDURE`, filtered to `UPPER(PROCEDURE_DESCRIPTION) LIKE '%DIALYSIS%'`.
3. Keeps the earliest `SERVICE_DATE` per patient as `FIRST_DIALYSIS_DATE`.

### 1.2 How the output is used downstream

`06_patient_journey_combine`, cell "Add dialysis flag":
* Left-joins the Px table to the patient-month spine on `PATIENT_ID`.
* `DIALYSIS_FLAG = 1` from the month of `FIRST_DIALYSIS_DATE` on (and always 1 if the first date is before 2017-01-01), else 0.
* Drops `FIRST_DIALYSIS_DATE` after use.

So the output contract is: one row per patient with `PATIENT_ID` and `FIRST_DIALYSIS_DATE`. Phase A keeps this contract; new columns can be added, none removed.

---

## 2. Bottlenecks found

| # | Hardcoded / issue | Effect | Fix goes in |
| --- | --- | --- | --- |
| Q1 | **Which procedures count: text match `'%DIALYSIS%'` on the description** | No list to review; any code with the word counts, any code without it is missed | Basket |
| Q2 | **Wrong matches (from the basket descriptions):** C1751 catheter "(OTHER THAN HEMODIALYSIS)", 93985 / 93986 scans "prior to creation" of the access | First dialysis date can be too early or a patient flagged who never had dialysis. To measure in Step 1 | Basket |
| Q3 | **Possible misses:** ESRD monthly services 90960 / 90961 / 90962 / 90966 (`is_defining = YES` in the basket), hemodialysis access codes (36800–36909), home hemodialysis visit 99512 may not contain the word | Real dialysis patients missed or found late. To measure in Step 1 | Basket |
| Q4 | **Mixed signal types under one flag:** dialysis sessions, ESRD monthly services, access procedures (fistula, catheter), dialysis training, and drugs billed "for ESRD on dialysis" (epoetin, cinacalcet, difelikefalin) | Access is often created months before dialysis starts; drugs prove the patient is on dialysis but are not the procedure. One flag hides the difference | Basket (`PX_GROUP` column) |
| Q5 | **No end date** | Future-dated or wrong service dates can set the first date | Config (`date_end`) |
| Q6 | **Table and column names** typed in the SQL | A rename breaks the query | Config |
| Q7 | **`DISTINCT` and `GROUP BY` together; constant `DIALYSIS_FLAG = 1`** | Double work; a column with no information | Code |
| Q8 | **Code of the first event not in the output** | No QC: cannot see which code set the first date | Code |
| Q9 | **No dropped-rows report** | Rows with no patient, no date or a code not in the dimension table are lost silently | Code |
| Q10 | **No validation scope** (unlike the other journey notebooks) | Comparisons always run on all US | Config (validation patients for the comparisons only) |

**Not a bottleneck: the date window.** The query uses all history on purpose: it looks for the *first* dialysis ever, and PJ06 treats a first date before 2017 as "on dialysis". Applying `DATA_START_DATE` (2023-01-01) would move first dates later and turn the flag off for patients on dialysis since before 2023. Decision D3 keeps all history.

---

## 3. Current Px basket (`Kerendia_Px_Final.csv`)

* **130 rows**, columns: `PROCEDURE_CODE, PROCEDURE_DESCRIPTION, patients_total, proc_category, is_defining, club_members, n_members, in_752_features, is_clubbed, club_reason`.
* Covers much more than dialysis: labs (A1C, creatinine, UACR parts, NT-proBNP, lipids), echo, diabetes training, CGM and insulin pump supplies, injectable drugs, dialysis and dialysis access, kidney transplant.
* **4 clubbed rows** with the code `[CLUBBED]` and the member codes in `club_members` (lipoprotein fractionation, glucagon, echo variants, adjunctive CGM). They must be expanded before matching.
* `is_defining` mixes `YES`, `no` and `MIXED`.
* **Descriptions are cut at 100 characters**, and echo rows have the description `echo_tests` instead of the real one. The text match of the 3.0 query cannot be reproduced from the basket; codes must be the key.
* No column says which codes are dialysis, so the notebook cannot use it directly.

Dialysis-related rows in the basket today (by `proc_category`):

| Group | Codes in the basket |
| --- | --- |
| Dialysis sessions | 90935, 90937 (hemodialysis); 90945, 90947 (other than hemodialysis, e.g. peritoneal); 90999 (unlisted); 99512 (home visit for hemodialysis) |
| ESRD monthly services | 90960, 90961, 90962, 90966 |
| Dialysis training | 90989, 90993 |
| Dialysis access | 36800, 36831, 36832, 36833, 36901–36909, 49421, C1750, C1752, 93990 (duplex scan of an existing access) |
| Before access creation | 93985, 93986 (pre-op vessel scan) |
| Drugs "for ESRD on dialysis" | Q4081, J0887, Q5105, J0882, J0604, J0879 |
| Not dialysis | C1751 ("other than hemodialysis") |
| Transplant | 50360 |

---

## 4. Plan (Phase A)

Same layout as the lab and Dx notebooks: title markdown, checks, the query alone in its cell, run, compare, findings markdown.

| Step | What | Comparison |
| --- | --- | --- |
| Setup | Clone the current notebook as `(Clone) 05_patient_journey_px` (3.0 baseline, unchanged). New header markdown in the main notebook | – |
| 0 | Run the 3.0 query unchanged; compare with the table last written (`kerendia_nba_3_1_px_validation`, 2026-10-26) | Patients and first dates identical, or differences explained (data refresh) |
| 1 | Hardcoded-parts markdown (from the review cell) + **profile**: every code the text match catches, with description, patients and first-date counts; check which basket dialysis codes it misses (Q2, Q3) | – (facts for decision D1) |
| 2 | **Basket:** the code list and `PX_GROUP` come from the new Px basket (section 5); only groups chosen in D1 count as dialysis | vs 3.0: same patients / same first date, first date earlier, later, gained, lost, each split by the code that caused it |
| 3 | **Config:** `PX_CONFIG` block (table and column names, `date_end`, history start = none, validation patients for comparisons); checks that tables and columns exist | vs Step 2: identical rows expected; rows pulled from Snowflake |
| 4 | **Code:** output columns from the basket (`FIRST_DIALYSIS_DATE` kept; add `FIRST_DIALYSIS_CODE` for QC); remove the constant flag and the double `DISTINCT`; dropped-rows report | vs Step 3: identical first dates; report of rows dropped by reason |
| 5 | **Write:** switched off until review (`WRITE_OUTPUT = False`), same path as today | – |

Every comparison is shown for (a) all US patients and (b) the validation patients (patients of the 10 validation HCPs, from the lab and Dx validation tables), month by month as PJ06 uses it: patient-months with `DIALYSIS_FLAG = 1`, 3.0 vs new.

---

## 5. Proposed new Px basket

One row per code, same style as the lab and Dx baskets. All 130 rows are kept; only the dialysis rows are used in Phase A.

| Column | Meaning | Example |
| --- | --- | --- |
| `MATCH_TYPE` | `CODE` (one code) or `LIST` (clubbed group, members separated by a pipe) | `CODE` |
| `MATCH_VALUE` | The code, or the member codes | `90935` |
| `CLUB_ID` | Name of the clubbed group (LIST rows) | `ECHO_VARIANTS` |
| `PROCEDURE_DESCRIPTION` | As in the old basket | |
| `PROC_CATEGORY` | As in the old basket | `Dialysis/Nephrology` |
| `CONDITION` | CKD / HF / DM / T1D / LIPIDS / OTHER | `CKD` |
| `PX_GROUP` | DIALYSIS_SESSION / ESRD_MONTHLY / DIALYSIS_TRAINING / DIALYSIS_ACCESS / PRE_ACCESS / DIALYSIS_DRUG / TRANSPLANT / blank | `DIALYSIS_SESSION` |
| `ACTIVE_DIALYSIS` | `Y` = counts for `FIRST_DIALYSIS_DATE` (decision D1) | `Y` |
| `IS_DEFINING`, `IN_752_FEATURES`, `PATIENTS_TOTAL`, `NOTE` | As in the old basket (Y/N cleaned) | |

Codes caught by the 3.0 text match but not in the basket (found in Step 1) are added with `PX_GROUP` and `ACTIVE_DIALYSIS` set per decision D1.

---

## 6. Decisions

**Decided 2026-10-29: all five as proposed** (Patricio: "go with your proposals and document everything").

| # | Decision | Options | Decided |
| --- | --- | --- | --- |
| D1 | **Which groups count as dialysis** for `FIRST_DIALYSIS_DATE` | Any combination of the `PX_GROUP` values | Sessions, ESRD monthly, home visit, training, drugs "for ESRD on dialysis" = **Y**. Access = **N** in Phase A (created before dialysis starts; measured in Step 2 so the effect is visible). Pre-access scans, C1751, transplant = **N**. Final list after the Step 1 profile |
| D2 | Codes caught by the 3.0 text match that are not in the basket | (a) add with a group, (b) leave out | (a), so nothing is lost silently |
| D3 | History window | (a) all history (as 3.0), (b) `DATA_START_DATE` | (a): the first dialysis ever is needed (section 2) |
| D4 | Basket files | (a) save the current file unchanged as `Kerendia NBA 3.1 - PX Event List.csv` and rewrite `Kerendia_Px_Final.csv` (the Dx way), (b) keep `Kerendia_Px_Final.csv` and add a new file | (a), same as Dx |
| D5 | Patient scope of the output | (a) all US (as 3.0; PJ06 left-joins on patient), (b) validation patients only | (a) for the output; comparisons shown for both |

---

### 6.1 How D1 is applied in the new basket

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

Notes:
* J0606 etelcalcetide is used only in hemodialysis patients but its description has no "DIALYSIS": kept N with a note, Phase B candidate.
* `CONDITION` per code: CKD (dialysis, access, kidney labs, iron and vitamin D drugs), HF (echo, NT-proBNP, loop diuretics), DM (A1C, glucose, CGM, insulin, pump supplies, diabetes training), T1D (islet cell antibody), LIPIDS, OTHER.
* `IS_DEFINING` / `IN_752_FEATURES` cleaned to Y / N; the 4 clubbed rows keep `IS_DEFINING = MIXED` as in the original.
* **D2 is applied after the first run:** cell 2a lists the codes caught by the 3.0 text match that are not in the basket (list A). They are added to the basket with a `PX_GROUP` and `ACTIVE_DIALYSIS` following the table above, then Steps 2–4 are re-run.

---

## 7. What does not change in Phase A

* Output contract for PJ06 (`PATIENT_ID`, `FIRST_DIALYSIS_DATE`); PJ06 itself is not edited.
* Output path `kerendia_nba_3_1_px_validation`, written only after review.
* The old notebook `(Clone) 05_patient_journey_px`.

---

## 8. Phase B (after review, not in this plan)

* **HF procedures:** echo (93306, 93308, 93350, 93351, ...), NT-proBNP (83880).
* **T1D / diabetes signals:** insulin pump and CGM supplies, islet cell antibody (86341), glucagon, diabetes self-management training (G0108, G0109).
* **Separate flags and dates per group:** dialysis type (hemo / peritoneal / home), first access date, transplant.
* **Dx plan Q2:** the dialysis and transplant procedure codes in the old Dx list (CPT 909xx, HCPCS G codes, ICD-10-PCS, revenue codes 0800–0889) are checked against the Px data and added to the Px basket if they exist there.
* **Access as an early signal:** a first access date (fistula / catheter) as its own column, once Step 2 shows how far it precedes the first dialysis.

---

## 9. Implementation notes (2026-10-29)

**Notebook layout (`05_patient_journey_px`, 28 cells):** header; section 1 setup (`00_connection`, 3.0 `00_config` for `date_end`, `00_cohort_config`); 3.0 query (unchanged); Step 0 check; Step 1 markdown + 1b profile; Step 2 (2a–2e); Step 3 (3a–3e); Step 4 (4a–4d); Step 5 markdown + write cell (off).

**Comparisons in every step:** (A) all US patients, first date same / earlier / later / gained / lost, with the median shift in days; (B, Step 2) the same split by the code that caused it; (C) validation patients = patients of the lab, Dx and Rx validation tables, `DIALYSIS_FLAG` per patient-month built with the exact rule of `06_patient_journey_combine`.

**Things found while building:**
* **`%run "../00_cohort_config"` no longer resolves** since the notebooks were moved into the `Lab Files` / `Dx Files` / `Px Files` subfolders (`00_cohort_config` is two levels up). Fixed to `../../00_cohort_config` in `05_patient_journey_px` and in the Px clone (the only change to the clone). **The same path is still `../` in `01_patient_journey_labs` and `02_patient_journey_dx`; not changed here (owners to fix).**
* The Px notebook did not run the 3.0 `00_config`; it now does (needed for `date_end`), as the Dx notebook does.
* Basket path: the notebook reads our basket folder in this repo. The Dx notebook reads `wenjie.chen@bayer.com/kerendia_nba_3_1_develop_sm/...`, which does not have the new Px files until they are pushed and synced.
* The 3.0 query groups every row with an empty `PATIENT_ID` into one output row; Step 0 counts it and Step 4 drops it.
* The first review markdown called the "for ESRD on dialysis" drugs wrong matches; corrected in the Step 1 markdown (they count, D1).
* The clone does not include the review markdown; it holds only the 3.0 cells (header, connection, cohort config, query, write).
