# Kerendia NBA 3.1 – Procedure Patient Journey: Summary of Changes

**Scope:** Procedure (Px) patient journey: the first dialysis date per patient from procedure claims, from the procedure code list to the patient-level dialysis table  
**Baseline:** NBA 3.0 Px notebook and query  
**Data used for validation:** IQVIA LAAD procedure claims, all US patients, all available history (from 2021-01) to 2026-09, plus the patients of the 10 validation HCPs  
**Status:** built and validated; access decision confirmed (D1). The new output table goes live together with the NBA 3.1 diagnosis table, not before (section 9.2)

---

## 1. Summary

In NBA 3.0, a procedure counted as dialysis when its description contained the word "DIALYSIS". There was no list to review: any code with the word counted, and any code without it was missed.

In NBA 3.1, the dialysis codes sit in the procedure code list (product basket), each with its group (dialysis session, monthly ESRD service, training, ESRD drug, access, transplant), and the run settings sit in one settings block. The query is generated from them. Adding a code or changing what counts as dialysis is now a file edit, not a code change.

* **Monthly ESRD services were missing in NBA 3.0 and are now found.** The monthly nephrologist services for dialysis patients (`90960`, `90961`, `90962`) do not contain the word "DIALYSIS", so 3.0 missed them. With them, 134,972 patients are newly found on dialysis, and 268,617 patients get an earlier first dialysis date (median 134 days earlier).
* **Access procedures no longer count as dialysis.** Catheters and fistula / cannula procedures are often done months before dialysis starts, or without dialysis following. Under NBA 3.0, 87,841 patients were flagged only because of such a procedure; they are no longer flagged, and 45,596 patients get a later first date, at the real start of dialysis. Confirmed after a check in the diagnosis claims (section 4.3); it can still be reversed with a file edit.
* **Nothing is lost silently.** All 31 codes the 3.0 word match found in the claims are in the new list: 15 of them were added to the list during this work.
* **Overall:** 1,489,202 → 1,536,052 patients with a first dialysis date (+3.1%). For the validation HCPs: 325 → 363 patients flagged on dialysis at some point.
* **Clearer output:** each patient now has the code and group of the first dialysis event, so every first date can be checked.
* **Visible data loss:** every run now prints a report of the rows dropped and why.

---

## 2. Product basket: old vs new snapshot

The product basket is the list of procedure codes for the Kerendia patient journey. The NBA 3.0 notebook did not read it: it used the word "DIALYSIS" in the code description. The new basket holds the codes and their rules, and the notebook reads it at the start of every run.

### 2.1 What changed in the basket

| | Old basket | New basket |
| --- | --- | --- |
| File | `Kerendia NBA 3.1 - PX Event List.csv` (kept unchanged) | `Kerendia_Px_Final.csv` |
| Columns | 10: `PROCEDURE_CODE`, `PROCEDURE_DESCRIPTION`, `patients_total`, `proc_category`, `is_defining`, `club_members`, `n_members`, `in_752_features`, `is_clubbed`, `club_reason` | 12: `MATCH_TYPE`, `MATCH_VALUE`, `CLUB_ID`, `PROCEDURE_DESCRIPTION`, `PROC_CATEGORY`, `CONDITION`, `PX_GROUP`, `ACTIVE_DIALYSIS`, `IS_DEFINING`, `IN_752_FEATURES`, `PATIENTS_TOTAL`, `NOTE` |
| Rows | 130 (4 clubbed groups) = 137 codes | 145 = 152 codes: the same 130 rows + 15 codes added from the 3.0 word match |
| Clubbed groups | One row with the code `[CLUBBED]` and the member codes in a text column | `MATCH_TYPE = LIST`: the member codes are matched directly |
| What each code is about | Category only (lab, cardiology, dialysis, supplies, ...) | `CONDITION`: CKD, HF, DM, T1D, lipids, other |
| Dialysis group | Not stored | `PX_GROUP`: dialysis session, ESRD monthly service, dialysis training, ESRD drug, dialysis access, pre-access scan, transplant |
| Used for the dialysis date | – | `ACTIVE_DIALYSIS = Y` on the 29 dialysis codes |
| Used by the notebook | No | Yes; the notebook checks that it has exactly the codes, patient counts and flags of the old basket, plus the codes added on purpose |

### 2.2 Old basket (`Kerendia NBA 3.1 - PX Event List.csv`): example rows

| PROCEDURE_CODE | PROCEDURE_DESCRIPTION | patients_total | proc_category | is_defining |
| --- | --- | --- | --- | --- |
| 90960 | ESRD related services monthly, patients 20 years and older | 345,750 | Dialysis/Nephrology | YES |
| 90935 | Hemodialysis procedure with single evaluation | 236,525 | Dialysis/Nephrology | YES |
| 90999 | Unlisted dialysis procedure | 201,341 | Dialysis/Nephrology | no |
| Q4081 | Injection, epoetin alfa (for ESRD on dialysis) | 87,054 | HCPCS Q codes | no |
| C1750 | Catheter, hemodialysis / peritoneal, long-term | 10,089 | HCPCS C codes | no |

The old basket lists the codes but does not say which ones mean dialysis, so it could not drive the dialysis date.

### 2.3 New basket (`Kerendia_Px_Final.csv`): codes counted as dialysis

Patients = all US patients whose first dialysis event (NBA 3.1) is in the group.

| Group | Codes | Patients (first event) | In the 3.0 word match? |
| --- | --- | --- | --- |
| Dialysis session | 90935, 90937 (hemodialysis); 90945, 90947 (peritoneal and other); 90999 (unlisted); 99512 (home visit for hemodialysis) | 944,618 | Yes, except 99512 |
| ESRD monthly service | 90960, 90961, 90962 (monthly visits, 20 years and older) | 525,030 (all ESRD codes) | **No** |
| ESRD monthly service | 90963–90970 (home dialysis per month, younger patients, less than a full month) | (included above) | Yes (90966 was already in the list; the others were added) |
| Dialysis training | 90989, 90993 | 26,100 | Yes |
| ESRD drug (billed only for patients on dialysis) | Epoetin Q4081, J0887, Q5105, J0886; darbepoetin J0882; cinacalcet J0604; difelikefalin J0879; ferumoxytol Q0139; peginesatide J0890; unclassified ESRD drug J3591 | 40,304 | Yes, except J0879 |
| **Total** | 29 codes | **1,536,052** | |

### 2.4 New basket: codes not counted as dialysis

| Group | Codes | Why not counted |
| --- | --- | --- |
| Dialysis access (21) | Catheters C1750, C1752; cannula / fistula procedures 36800, 36815, 36831–36833, 36838; dialysis circuit procedures 36901–36909; peritoneal catheter 49421; access scans and flow studies 93990, 90939, 90940 | Often done before dialysis starts, or without dialysis following (decision D1) |
| Pre-access scan (2) | 93985, 93986 | Done before the access is created |
| Transplant (1) | 50360 (kidney transplant) | Not dialysis; kept for a later transplant flag |
| Other procedures (99) | Labs (A1C, creatinine, urine albumin, NT-proBNP, lipids), echocardiography, diabetes training, CGM and insulin pump supplies, injectable drugs | Not about dialysis; kept for the other patient features |

---

## 3. Old vs new at a glance

| Area | Old notebook (NBA 3.0) | New notebook (NBA 3.1) | Benefit |
| --- | --- | --- | --- |
| Which codes count | Any code whose description contains "DIALYSIS" (32 codes) | 29 dialysis codes from the basket (`ACTIVE_DIALYSIS = Y`) | A reviewed list; a change is a file edit |
| Monthly ESRD services | Missed (no word "DIALYSIS" in the description) | Counted | 134,972 more patients found; earlier first dates |
| Access procedures | Counted as dialysis | Kept in the basket, not counted | First date at the real start of dialysis |
| Run settings (tables, dates) | Written in the SQL; no end date | One settings block (`PX_CONFIG`); end date = end of the run window; checks that tables and columns exist | One place to change settings; clear error if a table is renamed |
| History | All history | All history (kept on purpose: the first dialysis ever is needed) | Same as 3.0 |
| Data loss | Silent | Dropped-rows report on every run | Full transparency of what is excluded and why |
| Output | Patient, first dialysis date, a flag that is always 1 | Patient, first dialysis date, code and group of the first event | Every first date can be checked |
| Validation | None in the notebook | Comparison after each step (all US + validation HCPs) | Every change is measured |

---

## 4. Dialysis covered

### 4.1 Why monthly ESRD services were missing in NBA 3.0

Patients on dialysis are billed in two ways: the dialysis sessions themselves, and a monthly service by the nephrologist who manages them ("ESRD related services monthly"). The most common monthly codes, `90960`, `90961` and `90962`, describe the number of visits in the month but do not contain the word "DIALYSIS". The 3.0 word match therefore did not find them.

| Effect | Patients (all US) |
| --- | --- |
| Found on dialysis only through these codes (newly found) | 134,673 |
| First dialysis date moves earlier because of these codes | 268,377 |

### 4.2 Why this matters for the business

The combine notebook (PJ06) turns the first dialysis date into a monthly dialysis flag: from the month of the first dialysis on, the patient is flagged as on dialysis. Dialysis patients have end-stage kidney disease, for which Kerendia is not indicated (to be confirmed with Medical).

| Change | Effect |
| --- | --- |
| Monthly ESRD services now found | More dialysis patients are recognised, and earlier, so HCPs with many dialysis patients are not over-counted as Kerendia opportunities |
| Access procedures no longer count | Patients who only had a catheter or fistula procedure are no longer treated as on dialysis; patients with an access procedure before dialysis are flagged from the real start |

### 4.3 Access procedures (decision D1)

A dialysis access (a fistula, graft or catheter) is needed before hemodialysis or peritoneal dialysis can start. It is often created months in advance, and some patients never start dialysis.

| | NBA 3.0 | NBA 3.1 |
| --- | --- | --- |
| Access procedures | Counted as dialysis when the description contains the word (e.g. C1750, C1752, 36800) | In the basket as `DIALYSIS_ACCESS`, not counted |
| Patients flagged only by an access procedure | 87,841 | 0 |
| Patients whose first date moves later, to the first real dialysis event | – | 45,596 (median 20 days) |

**Are the access-only patients on dialysis? Check in the diagnosis claims.** For each group: the share of patients with an end-stage or dialysis diagnosis (`N18.6` end-stage renal disease, `Z99.2` dialysis dependence, `Z49.x` dialysis encounter) at any time.

| Group | Patients | End-stage or dialysis diagnosis | None of the kidney codes checked (not even stage 4) |
| --- | --- | --- | --- |
| Reference: patients counted as on dialysis in NBA 3.1 | 1,401,361 | 88.6% | 9.3% |
| Short-term catheter (C1752) | 24,300 | 8.8% | 87.5% |
| Long-term catheter (C1750) | 31,669 | 48.6% | 47.7% |
| Cannula (36800) | 31,350 | 25.7% | 65.8% |
| Other access | 522 | 57.1% | 41.0% |
| **All access-only patients** | **87,841** | **29% (about 25,900)** | **65%** |

* **Short-term catheters are mostly not chronic dialysis.** They are used for temporary dialysis (for example in hospital after acute kidney injury) and for other procedures such as plasma exchange. Acute kidney injury cannot be confirmed: the diagnosis table does not contain its codes (`N17`).
* **Long-term catheters are mixed:** about half of these patients have an end-stage or dialysis diagnosis.
* **Patients who are really in end stage are already excluded through the diagnosis journey:** `N18.6` gives CKD stage 5, which is not eligible for Kerendia.

**Recommendation: keep access procedures out of the dialysis flag.** In the combine notebook, the dialysis flag makes a patient not eligible from that month on. Counting access would remove about 62,000 patients with no dialysis diagnosis from the Kerendia opportunity, almost all the short-term-catheter patients among them. **Condition:** the stage-5 exclusion comes from the NBA 3.1 diagnosis journey, so the new procedure table should go live together with the new diagnosis table, not before. If the team still prefers to keep access as a dialysis signal, this is one setting per code in the basket (section 9.2).

### 4.4 Drugs billed for patients on dialysis

Some injectable drugs have codes that are billed only for patients with end-stage renal disease on dialysis (for example epoetin "for ESRD on dialysis"). They are not the dialysis itself, but they show that the patient is on dialysis. They are counted, as in NBA 3.0. For 40,304 patients, such a drug is the first dialysis event in the data.

### 4.5 History of the data

The procedure claims start in January 2021. "First dialysis" therefore means "first dialysis since 2021". The PJ06 rule that treats a first dialysis before 2017 as "on dialysis" never applies with this data (section 9.2).

---

## 5. Each rule in the old notebook and where it is now

| # | Old notebook (written in the SQL or the code) | New notebook | What improves |
| --- | --- | --- | --- |
| 1 | **Code list:** any code with the word "DIALYSIS" in the description | 29 dialysis codes from the basket (`ACTIVE_DIALYSIS = Y`) | Adding a code is a file edit |
| 2 | **Missed codes:** monthly ESRD services, home hemodialysis visit, one ESRD drug | In the basket and counted | More dialysis patients found, earlier |
| 3 | **Mixed signals under one flag:** sessions, monthly services, access, training, drugs | `PX_GROUP` per code; access not counted | First date at the real start of dialysis |
| 4 | **No end date** | End date of the run window, in the settings block | Output aligned with the other journeys |
| 5 | **Table and column names** in the SQL | Settings block, checked before the run | Clear error if the vendor renames a table or column |
| 6 | **Constant flag** (always 1) in the output | Removed; PJ06 builds the monthly flag itself | Simpler output |
| 7 | **Code of the first event** not in the output | Code and group of the first event kept | QC by code |
| 8 | **No report** of excluded rows | Dropped-rows report | Losses visible on every run |

---

## 6. How the new notebook works

| Step | Input | What it does | Output |
| --- | --- | --- | --- |
| 1. Read the basket | `Kerendia_Px_Final.csv` | Expands clubbed rows; checks for duplicate codes and valid groups; checks it has the same codes as the old basket, plus the codes added on purpose; checks that every code found by the 3.0 word match is in the list | Dialysis codes with their group |
| 2. Read settings | `PX_CONFIG` | Source table and columns, end date; checks that tables and columns exist | Run settings |
| 3. Build and run the query | Steps 1–2 | Generates the SQL and runs it in Snowflake | First dialysis date, code and group per patient |
| 4. Dropped-rows report | Same query steps | Counts every dialysis claim row under the rule that excludes it | Report of excluded data |

Each change was introduced in a separate step and compared with the step before. Before any change, the copied 3.0 query was checked against the last 3.0 output: identical (1,489,202 patients, same first dates).

---

## 7. Validation results

### 7.1 All US patients (first dialysis date)

| Result | Patients | Detail |
| --- | --- | --- |
| Same first date as NBA 3.0 | 1,087,148 | |
| First date earlier | 268,617 | Median 134 days; from the monthly ESRD services (268,377) |
| First date later | 45,596 | Median 20 days; 3.0 date came from an access procedure (45,237) |
| Newly included | 134,972 | Monthly ESRD services (134,673), home hemodialysis visit (281), difelikefalin (18) |
| No longer included | 87,841 | Access procedure only: long-term catheter (31,669), cannula (31,350), short-term catheter (24,300), other access (522) |
| After the end of the run window (removed by the end date) | 281 | First dialysis on 2026-10-01 or 10-02 |
| **Total** | 1,489,202 → **1,536,052** | +46,850 (+3.1%) |

### 7.2 Validation HCPs (patients of the 10 doctors, monthly dialysis flag as built in PJ06)

| Metric | NBA 3.0 | NBA 3.1 | Change |
| --- | --- | --- | --- |
| Patients | 4,238 | 4,238 | Same spine (lab, Dx and Rx journeys) |
| Patient-months | 137,373 | 137,373 | |
| Patient-months flagged on dialysis | 7,649 | 8,413 | +764 (844 months newly flagged, 80 no longer flagged) |
| Patients flagged on dialysis at some point | 325 | 363 | +38 |

### 7.3 First dialysis event by group (all US, NBA 3.1)

| Group | Patients | % |
| --- | --- | --- |
| Dialysis session | 944,618 | 61.5 |
| Monthly ESRD service | 525,030 | 34.2 |
| ESRD drug | 40,304 | 2.6 |
| Dialysis training | 26,100 | 1.7 |

---

## 8. What is excluded and why (new dropped-rows report)

All US, claim rows with a dialysis code. NBA 3.0 had no end date and no report.

| Reason | Claim rows | % | Can be recovered? |
| --- | --- | --- | --- |
| After the end date (2026-09-30) | 10,169 | 0.004 | By design (next run) |
| No patient or no service date | 0 | 0.0 | – |
| **Kept** | **230,410,450** | **99.996** | – |

---

## 9. Decisions

### 9.1 Decisions made

| Decision | Choice | Reason |
| --- | --- | --- |
| D1 | Dialysis = sessions, monthly ESRD services, home visit, training, drugs billed only for dialysis patients; access, pre-access scans and transplant not counted (confirmed after the diagnosis check, section 4.3) | First date at the real start of dialysis; only 29% of access-only patients have an end-stage or dialysis diagnosis |
| D2 | Every code found by the 3.0 word match is in the basket (15 added) | Nothing lost silently |
| D3 | All history (no start date) | The first dialysis ever is needed |
| D4 | New basket file `Kerendia_Px_Final.csv`; the old list is kept unchanged as `Kerendia NBA 3.1 - PX Event List.csv` | Single place for the code rules |
| D5 | Output for all US patients, as 3.0 | PJ06 joins it by patient |
| D6 | The new procedure table goes live together with the NBA 3.1 diagnosis table | The end-stage exclusion of access-only patients comes from the 3.1 diagnosis journey |

### 9.2 Decisions for the final review

| # | Decision | Options | Impact |
| --- | --- | --- | --- |
| 1 | New check columns in PJ06 (with the Dx update of PJ06) | (a) drop them in PJ06, (b) write only patient and first date | PJ06 currently drops only the first date after the join, so the code and group columns would appear in the combined table |
| 2 | PJ06 rule "first dialysis before 2017 = on dialysis" (with the Dx update of PJ06) | Keep or remove | No effect today: the data starts in 2021 |
| 3 | Write the new table | Together with the NBA 3.1 diagnosis table (D6) | Output columns: the constant flag is replaced by the first code and group |

### 9.3 Planned next phases (from the NBA 3.1 patient journey plan)

| Phase | What | Uses from the basket |
| --- | --- | --- |
| B | Heart failure signals: echocardiography, NT-proBNP | `CONDITION = HF` |
| B | Diabetes and T1D signals: insulin pump and CGM supplies, islet cell antibody, glucagon, diabetes training | `CONDITION = DM / T1D` |
| B | Separate dates per group: first access, dialysis type (hemo / peritoneal / home), transplant | `PX_GROUP` |
| B | Dialysis and transplant procedure codes from the old Dx list checked against the procedure data | Basket additions |
