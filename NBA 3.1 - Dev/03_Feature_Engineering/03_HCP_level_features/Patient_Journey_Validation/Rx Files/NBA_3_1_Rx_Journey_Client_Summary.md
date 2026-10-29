# Kerendia NBA 3.1 – Prescription Patient Journey: Summary of Changes

**Scope:** Prescription (Rx) patient journey: which drugs each patient is on, per cohort month, from pharmacy claims, from the drug list to the patient-month table  
**Baseline:** NBA 3.0 Rx notebook  
**Data used for validation:** IQVIA LAAD pharmacy claims; the patients of the 10 validation HCPs (the table the journey writes), and all US fills since 2023-01 for the checks on the drug list  
**Status:** built and validated (Phase A: same drugs and categories as NBA 3.0, now driven by the product basket). The new output table goes live together with the NBA 3.1 diagnosis and procedure tables, not before (section 9.2)

---

## 1. Summary

In NBA 3.0, the drugs that count and their category came from a Snowflake view outside the project (`CKD_PRODUCT_MAPPING_VW`), and the brand labels from lists typed into the code. The product basket was not used.

In NBA 3.1, the drugs, their category and their brand label sit in the product basket, and the run settings sit in one settings block. The query is generated from them. Adding a drug or changing its category is now a file edit, not a code change.

* **Same drugs and categories as NBA 3.0.** The new basket reproduces the 3.0 rules exactly: for the validation HCPs the output is identical (107,616 patient-months), and for every product in the IQVIA product table the rule is the same (685 of 685 product / strength pairs).
* **Much lighter run.** The notebook now pulls 160,029 rows from Snowflake instead of the full Rx claims table (about 6 billion rows) plus 4 full tables.
* **First months of 2023 now complete.** A 90-day fill from late 2022 now counts for the days it covers in 2023 (look-back). For the validation HCPs: +2,525 patient-months, all in the first four cohort months.
* **End date aligned with the other journeys** (2026-09-30 instead of the last claim date).
* **Nothing is lost silently.** Every run prints a report of the fills dropped and why. A data issue that spread a fill with an empty days supply to the end of the data is fixed.
* **The 3.0 drug list has gaps,** made visible by this work and kept as they are for now: **Kerendia itself, the GLP-1 drugs (Ozempic, Mounjaro, Wegovy, Zepbound, Trulicity), generic dapagliflozin and generic Entresto are not in the journey.** Generic dapagliflozin patients do not get the SGLT2 flag. These are decisions for the next phase (section 5).

---

## 2. Who uses the Rx journey

The output has one row per patient and cohort month: the set of treatment categories (`TREATMENT_CATEGORY`) and of brand labels (`CATEGORY`) the patient was on that month. The combine notebook (PJ06) uses it for:

| Use in PJ06 | How |
| --- | --- |
| **SGLT2 flag** | A patient with any month where `TREATMENT_CATEGORY` contains `SGLT2` gets the SGLT2 flag. When the CKD stage is unknown, an SGLT2 patient counts as eligible |
| Treatment counts | Number of treatments per month, new treatments |
| Brand list | `CATEGORY` becomes the brand column (Jardiance, Farxiga, Invokana 100 / 300 MG, ...) |
| Patient-months | Rx months also create patient-months in the combined table |

The output columns and the category texts are unchanged, so PJ06 does not need a change.

---

## 3. Product basket: old vs new

### 3.1 Files (same naming as the lab, diagnosis and procedure baskets)

| | Old basket | New basket |
| --- | --- | --- |
| File | `Kerendia NBA 3.1 - RX Event List.csv` (content unchanged, renamed) | `Kerendia_Rx_Final.csv` |
| Columns | 10: `PRODUCT_NAME`, `PRODUCT_GROUP`, `patients_total`, `providers_total`, `nbrx_total`, `club_members`, `n_members`, `in_752_features`, `is_clubbed`, `club_reason` | 12: `MATCH_TYPE`, `MATCH_VALUE`, `CLUB_ID`, `PRODUCT_GROUP`, `TREATMENT_CATEGORY`, `BRAND_LABEL`, `STRENGTH`, `CONDITION`, `ACTIVE_JOURNEY`, `PATIENTS_TOTAL`, `IN_752_FEATURES`, `NOTE` |
| Rows | 258 (28 clubbed groups) = 346 product names | 367 = 440 product names |
| Journey category | Not stored (groups such as ACE, ARB, BB, OTHERS do not match the journey categories) | `TREATMENT_CATEGORY`, same texts as NBA 3.0 |
| Brand label | Not stored | `BRAND_LABEL`; `STRENGTH` where the label depends on it (Invokana 100 / 300 MG) |
| In the journey | – | `ACTIVE_JOURNEY = Y` on the 254 drugs NBA 3.0 counts |
| Used by the notebook | No | Yes, read and checked at the start of every run |

### 3.2 How the 367 rows were made

| Rows | Why |
| --- | --- |
| 258 → 271 | All rows of the old basket. 13 clubbed groups were split in two because their members follow different NBA 3.0 rules (e.g. Lantus is counted as insulin, the generic insulin glargine members are not) |
| + 94 | Drugs NBA 3.0 counts that were missing from the basket (e.g. indapamide, Cardizem, Coreg, Glucophage, Avapro, Hyzaar); marked "Added (D2)" |
| + 2 | Invokana brand label by strength |
| **= 367** | 229 rows in the journey, 138 not (reason in `NOTE`) |

### 3.3 Categories in the journey

| Journey category | Drugs | Brand labels |
| --- | --- | --- |
| Calcium channel / Beta blocker | 56 | category |
| ACE/ ARB | 32 (incl. Entresto) | category |
| Combo drug | 45 | category |
| Diuretic_NON_MRA | 30 | category |
| metformin | 6 | category |
| Insulin | 67 | category; Xultophy as `GLP-1` |
| SGLT2 | 13 | Jardiance, Farxiga, Invokana 100MG / 300MG; others `SGLT2` |
| MRA | 5 (spironolactone, eplerenone, ...) | category |

---

## 4. Old vs new at a glance

| Area | Old notebook (NBA 3.0) | New notebook (NBA 3.1) | Benefit |
| --- | --- | --- | --- |
| Which drugs count, category | Snowflake view outside the project, matched on product name; categories with "other" dropped | Product basket (`ACTIVE_JOURNEY`, `TREATMENT_CATEGORY`) | A reviewed list in the project; a change is a file edit |
| Brand labels | Typed in the code (23 DPP-IV and 19 GLP-1 names, of which only 1 could ever be used) | `BRAND_LABEL` in the basket | Visible and editable |
| Data pulled | Full Rx claims table (≈ 6 billion rows) + 4 full tables | 160,029 rows (filters run in Snowflake) | Faster, cheaper |
| Run settings | Table names, paths, dates, grace days in the code | One settings block (`RX_CONFIG`), checked before the run | One place to change; clear error if a table is renamed |
| End date | Last date in the claims (2026-10-02) | End of the run window (2026-09-30) | Aligned with the other journeys |
| Start of the data | Fills from 2023-01-01 only | Also fills from up to 97 days before that still cover 2023 | First months complete |
| Joins | Plan and demographics tables joined, not used | Removed | Simpler, no hidden filter |
| Empty days supply | Fill spread to the end of the data | Dropped and reported | No false long treatment |
| Data loss | Silent | Dropped-rows report on every run | Full transparency |
| Validation | None in the notebook | Comparison after each step | Every change is measured |

---

## 5. Gaps in the 3.0 drug list: is it a problem, and what happens

The NBA 3.0 drug list (the Snowflake view) leaves out several important drugs. Phase A keeps the NBA 3.0 list on purpose, so that each change can be measured on its own. The basket now holds these drugs with `ACTIVE_JOURNEY = N`, so turning them on is a file edit.

Patients = all US patients with a fill since 2023.

| Finding | Patients | Is it a problem today? | Phase A (now) | Phase B (proposal) |
| --- | --- | --- | --- | --- |
| **Kerendia** not in the drug list | 446 K | **Yes:** Kerendia use is not visible in the Rx journey | Kept as 3.0 | Add, with its own brand label |
| **Generic dapagliflozin** not in the list (brand Farxiga is) | 4.3 M | **Yes:** these patients do not get the PJ06 SGLT2 flag | Kept as 3.0 | Add as SGLT2 (changes the SGLT2 flag) |
| GLP-1 / GIP-GLP-1: Mounjaro, Wegovy, Zepbound not in the list; Ozempic, Trulicity, Rybelsus, Victoza dropped as "Other- glucose mgmt" | 11.0 M, 4.3 M, 4.1 M; 13.2 M, 4.2 M, ... | Yes: GLP-1 use is almost invisible (label in 14 patient-months only) | Kept as 3.0 | Add a GLP-1 category / label |
| DPP-IVs (Januvia, Tradjenta, Janumet), sulfonylureas, pioglitazone dropped as "Other- glucose mgmt" | – | Partly: other diabetes treatment not visible | Kept as 3.0 | Decide whether they are needed |
| **Generic Entresto** (sacubitril/valsartan) not in the list (brand Entresto is, as ACE/ ARB) | 1.7 M | Yes, for HF (new in 3.1) | Kept as 3.0 | Add, with an HF group |
| Nebivolol (beta blocker) not in the list | 1.5 M | Yes: a common beta blocker is missing | Kept as 3.0 | Add as Calcium channel / Beta blocker |
| Generic insulin glargine (Glargine-YFGN, Solostar) not in the list (Lantus is) | 2.5 M, 1.2 M | Yes: part of insulin use missing | Kept as 3.0 | Add as Insulin |
| SGLT2 combinations (Synjardy, Xigduo XR, Glyxambi, Invokamet, ...) | 13 K–444 K each | No: counted as SGLT2 | Same | Optional brand labels |
| CGMs, insulin pumps, glucagon; HF drugs (ivabradine, vericiguat); CKD drugs (iron, epoetin, phosphate binders) | – | Not used today | In the basket, not active | Candidates for T1D, HF and advanced-CKD features |
| Empty days supply spread to the end of the data | 2,686 fills, 2,273 patients (none for the validation HCPs) | Yes, in an all-US run | **Fixed:** dropped and reported | – |
| Plan and demographics joins | 0 fills removed | No: no effect, only cost | **Removed** | – |
| Product names cut at 25 characters in the basket | – | No: the IQVIA product table uses the same 25-character names; every basket name matches | Nothing to do | – |
| Very long days supply (up to 999 days) | 57,982 fills over 365 days | Minor (4 fills for the validation HCPs) | Kept as 3.0 | Decide on a cap |

---

## 6. How the new notebook works

| Step | Input | What it does | Output |
| --- | --- | --- | --- |
| 1. Read the basket | `Kerendia_Rx_Final.csv` | Expands clubbed rows; checks for duplicate names, valid flags and a category on every active row | Active drugs, category, brand label |
| 2. Read settings | `RX_CONFIG` | Tables and columns, dates, look-back, grace days, paths; checks that tables and columns exist | Run settings |
| 3. Build and run the query | Steps 1–2 | Generates the SQL and runs it in Snowflake; HCP universe and validation HCPs applied | Fills with category and label |
| 4. Months | Fills | Spreads each fill over its days supply + 7 grace days, by cohort month (unchanged from 3.0) | Patient-month table |
| 5. Dropped-rows report | Same query | Counts every fill under the rule that removes it | Report of excluded data |

Each change was introduced in a separate step and compared with the step before. Before any change, the 3.0 code was checked against the last 3.0 output: identical (107,616 patient-months, 3,645 patients).

---

## 7. Validation results (patients of the 10 validation HCPs)

### 7.1 Step by step

| Step | Change | Patient-months | Patients with an SGLT2 month | Result vs the step before |
| --- | --- | --- | --- | --- |
| 0 | NBA 3.0 code, rerun | 107,616 | 902 | Identical to the table written on 2026-10-26 |
| 2 | Drug rules from the basket | 107,616 | 902 | Identical; all 685 product / strength pairs same for all US |
| 3 | Settings block + one Snowflake query (3.0 dates) | 107,616 | 902 | Identical |
| 3 | End date 2026-09-30 | 107,524 | 900 | −92 patient-months (fills on 1–2 Oct 2026; 5 patients) |
| 3 | Look-back 97 days | 110,049 | 909 | +2,525 patient-months, only in the first 4 cohort months |
| 4 | Clean-up + report | 110,049 | 909 | Identical |
| **NBA 3.0 → NBA 3.1** | | **107,616 → 110,049** | **902 → 909** | **+2,433 patient-months (+2.3%)** |

### 7.2 Where the look-back adds months

| Cohort month | Before | After | Change |
| --- | --- | --- | --- |
| 2022-12 (first days of January 2023) | 375 | 1,976 | +1,601 |
| 2023-01 | 1,466 | 2,103 | +637 |
| 2023-02 | 1,901 | 2,139 | +238 |
| 2023-03 | 2,160 | 2,204 | +44 |
| From 2023-04 | – | – | none |

---

## 8. What is excluded and why (new dropped-rows report)

Fills of the validation patients pulled from Snowflake: 158,983.

| Reason | Fills | % | Comment |
| --- | --- | --- | --- |
| **Kept** | **131,949** | **83.0** | – |
| Prescriber not in the HCP universe | 23,511 | 14.8 | NBA 3.0 rule, unchanged; now visible |
| Fill before 2023 that does not reach 2023 | 3,094 | 1.9 | Read for the look-back, not needed |
| Provider has no NPI | 216 | 0.1 | NBA 3.0 rule |
| After the end date (2026-09-30) | 213 | 0.1 | By design (next run) |
| Days supply empty | 0 | 0 | 2,686 fills in all US |
| Provider not in the provider table | 0 | 0 | – |

---

## 9. Decisions

### 9.1 Decisions made

| Decision | Choice | Reason |
| --- | --- | --- |
| D1 | New basket `Kerendia_Rx_Final.csv`; the old list kept unchanged as `Kerendia NBA 3.1 - RX Event List.csv` | Same naming as lab, diagnosis and procedure; one place for the drug rules |
| D2 | Phase A reproduces the NBA 3.0 drug list exactly; the 94 drugs missing from the basket are added | Measure the basket change alone; nothing lost silently |
| D3 | Kerendia, GLP-1s, generic dapagliflozin and the other gaps: measured now, decided in Phase B | Changes the SGLT2 flag and the treatment counts; needs a business decision |
| D4 | End date = end of the run window; look-back of 97 days (90 days supply + 7 grace days); empty days supply dropped | Aligned with the other journeys; first months complete; no false long treatment |
| D5 | 7 grace days kept, now in the settings block | Same rule, visible |
| D6 | Plan and demographics joins removed | No effect (0 fills), only cost |
| D7 | One Snowflake query with the filters | 160,029 rows instead of ≈ 6 billion |
| D8 | Same output columns and category texts; table goes live with the NBA 3.1 diagnosis and procedure tables; PJ06 unchanged | PJ06 depends on the exact `SGLT2` text |

### 9.2 Go-live and open items for review

**Go-live:** the new Rx table is written only together with the NBA 3.1 diagnosis and procedure tables (write switched off until then). PJ06 needs no change: same columns and texts.

| # | Open item | Proposal |
| --- | --- | --- |
| 1 | **Phase B drug list:** Kerendia, generic dapagliflozin (SGLT2 flag), GLP-1 / GIP-GLP-1 drugs, generic Entresto and HF drugs, nebivolol, generic insulin glargine, DPP-IVs | Decide drug by drug; each is a file edit (`ACTIVE_JOURNEY`, category, label), measured against Phase A |
| 2 | Cap for very long days supply (up to 999 days) | Decide whether to cap (e.g. at 90 or 365 days) |
| 3 | Old file name: the old basket is now `Kerendia NBA 3.1 - RX Event List.csv` | Confirm with Sehar that nothing outside this project reads `Kerendia_Rx_Final.csv` expecting the old columns |
| 4 | `CONDITION` column of the basket is empty | Fill in Phase B (CKD, HF, DM, T1D, HTN) for the new patient features |
