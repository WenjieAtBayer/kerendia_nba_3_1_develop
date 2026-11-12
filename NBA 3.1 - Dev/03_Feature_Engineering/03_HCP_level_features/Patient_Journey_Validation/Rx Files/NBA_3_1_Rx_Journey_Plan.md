# NBA 3.1 – Rx patient journey (PJ03): analysis and plan

**Status (2026-10-29):** D1–D8 applied as proposed. **Phase A complete: Steps 0–5 built and run** (results in section 0). Write switched off until the 3.1 Dx / Px tables go live. Client summary: `Rx Files/NBA_3_1_Rx_Journey_Client_Summary.md`.  
**Old notebook:** `Rx Files/(Clone) 03_patient_journey_rx` (frozen 3.0 baseline, created 2026-10-29; its write cell is not run)  
**New notebook:** `Rx Files/03_patient_journey_rx` (steps added after the 3.0 cells, as in Dx and Px)  
**Rx basket:** `Final Product Basket/Kerendia_Rx_Final.csv` = new format (367 rows, read by the notebook from Step 2). The original basket (258 rows, Sehar's) keeps its content as `Kerendia NBA 3.1 - RX Event List.csv` (renamed 2026-10-29, D1, same naming as Lab, Dx and Px)  
**Downstream:** `06_patient_journey_combine` (SGLT2 flag, treatment counts, brand lists), `Patient_Trace_755592568`, and the validation spine of the Px notebook  
**Approach:** same as lab, Dx and Px: keep the 3.0 code as the baseline, add one step at a time, compare each step with the one before.  
**Scope:** Phase A only (match 3.0, make it dynamic, measure every change). HF and T1D drug groups, newer GLP-1s and new features are Phase B (section 8).  
**Go-live:** like Px, the 3.1 Rx table is written only when the Dx (and Px) 3.1 tables go live; `06_patient_journey_combine` stays as it is until then.

---

## 0. Implementation results

Run 2026-10-29 in `03_patient_journey_rx` (cells 0a/0b, 1b/1c/1c-2/1d, 2a–2e, 3a–3e, 4a/4b/4b-2/4c, Step 5).

| Step | Check | Result |
| --- | --- | --- |
| 0 | 3.0 code vs the table last written (`kerendia_nba_3_1_rx_journey_validation`, 107,616 rows, 2026-10-26) | **Identical:** 107,616 patient-months, 3,645 patients, all "same"; per-category months identical; 902 SGLT2 patients (same 902). 126,903 fills used. Last Rx claim date still 2026-10-02 |
| 1 | Profile: products in `CKD_PRODUCT_MAPPING_VW`, typed DPP-IV / GLP-1 lists, basket; rows each filter removes | View: 476 names (one row each), 254 kept, 222 in "Other" / "Other- glucose mgmt". Typed lists: 41 of 42 names never labelled. 94 view products missing from the basket; 186 of 346 basket names not kept. Funnel adds up (3,740,781,815 US fills since 2023): "other" 13.3%, no NPI 0.3%, plan join 0 |
| 2 | Basket query vs 3.0 | **Identical.** New basket `Final Product Basket/Kerendia_Rx_Final.csv` (built as `..._3_1_draft.csv`, renamed under D1): 367 rows = 258 original + 13 from 13 split clubbed rows + 94 added (D2) + 2 Invokana strength rows; 440 product names, 254 active (= the 254 the view keeps); 229 active rows, 138 inactive rows. Validation HCPs: 126,903 fills, 107,616 patient-months all "same", no change in any category, 902 SGLT2 patients (same 902). All products in the IQVIA product table: 685 name + strength pairs (221 names) the same, 0 only in 3.0, 0 only in the basket, 0 different. Original basket content unchanged, now `Kerendia NBA 3.1 - RX Event List.csv` |
| 3 | Config query vs Step 2 | `RX_CONFIG` checks passed (4 tables, mapped columns, 2023-01-01 → 2026-09-30, HCP universe 234,405 providers). Rows pulled from Snowflake: 160,029 (3.0: full Rx fact table 5,989,489,699 rows + 4 full tables). With the 3.0 dates: identical to Step 2 (126,903 fills, 107,616 patient-months all "same", 902 SGLT2 patients). End = `date_end` 2026-09-30 (3.0: 2026-10-02): 126,561 fills (−342), 107,524 patient-months (107,508 same, 16 categories differ, 92 only old from 5 patients; −2 in every month from 2023-04), 900 SGLT2 patients. + look-back 97 days: 134,389 fills (+7,828), 110,049 patient-months (+2,525 new, 1,247 categories differ, 2 labels differ), 909 SGLT2 patients; changes only in cohort months 2022-12 (+1,601), 2023-01 (+637), 2023-02 (+238), 2023-03 (+44) |
| 4 | Output + dropped-rows report | Identical to Step 3: 110,049 patient-months all "same" (3,643 patients), no change in any category, 909 SGLT2 patients. Report (158,983 fills of the validation patients pulled; rows add up): kept 131,949 (83.0%); provider not in provider table 0; no NPI 216 (0.14%); after end date 213 (0.13%); days supply empty 0; before start date and not reaching it 3,094 (1.95%); prescriber not in HCP universe 23,511 (14.79%). Second check: 0 fills only in Step 4; 2,440 only in Step 3, all look-back fills that end before 2023-01-01 |
| 5 | Write | `WRITE_OUTPUT = False`; output = Step 4, same 5 columns as 3.0 (assert passed); nothing written |

Other facts from Steps 0–1:
* The `metformin` category text has a trailing space (`"metformin "`), as it comes from the view; kept for parity.
* Product names: the IQVIA product table stores at most 25 characters (111 names of exactly 25), and every basket name matches it. **The 25-character cut is not a problem.**
* Invokana has only two strength texts (`100 MG`, `300 MG`), so the 3.0 rule labels all Invokana fills.
* Days supply: empty for 3,750 US fills (2,686 kept, 2,273 patients), 0 for the validation HCPs. In the 3.0 code an empty days supply gives `END_DT = max_date` (Spark `least()` skips nulls), so such a fill is spread to the end of the data. Proposal for Step 4: drop them and report them. Days supply 0: 1.2 M US fills (spread over 8 days). Over 365 days (max 999): 57,982 US fills, 4 validation fills; no change in Phase A.

**Facts for D2 (parity source, basket additions)**
* 94 product names the 3.0 code keeps are not in the Rx basket: 61 with fills, 33 without (Humulin / Novolin, hydralazine, clonidine, prazosin, Omnipod packs; no NDC under that name). Largest: indapamide (289,510 patients), Cardizem LA/CD, Coreg (CR), Lopressor, Innopran XL, Glumetza, Glucophage (XR), Avapro, Atacand, Tribenzor, Hyzaar, Exforge (HCT), Azor.
* All 94 to be added to the new basket with their view category (`NOTE`: "Added (D2): in the view, not in the basket"); the 186 basket names not kept get `ACTIVE_JOURNEY = N`.

**Facts for D3 (Phase B: drugs the view leaves out)**
* Not in the view at all: **Kerendia** (446 K patients since 2023), Mounjaro (11.0 M), Wegovy (4.3 M), Zepbound (4.1 M), **generic dapagliflozin** (4.3 M; brand Farxiga is kept as SGLT2), **generic sacubitril/valsartan** (1.7 M; brand Entresto is kept as ACE/ ARB), **nebivolol** (1.5 M; other beta blockers are kept), generic insulin glargine (Glargine-YFGN 2.5 M, Glargine Solostar 1.2 M; the view has 46 insulin names with fills), Brenzavvy, Inpefa, Trijardy XR, dapagliflozin/metformin, CGMs.
* In the view but dropped as "Other- glucose mgmt": Ozempic (13.2 M), Trulicity (4.2 M), Rybelsus, Victoza, the DPP-IVs in the view (Januvia, Tradjenta, Janumet, ...), sulfonylureas, pioglitazone.
* Effect: Kerendia never appears in the Rx journey; generic dapagliflozin patients do not get the PJ06 SGLT2 flag; `GLP-1` label in 14 patient-months only (Xultophy), `DPP-IV` never.
* SGLT2 combinations in the view (Synjardy, Xigduo XR, Glyxambi, Invokamet, Segluromet, Steglujan, Qtern) count as SGLT2 with label `SGLT2`.

**Facts for D6 (joins)**
* Plan join: removes **0** fills (all US); no plan column used → can be removed with no effect.
* Demographics join: left join, no column used → can be removed.
* Provider join: 44 fills without a provider row; the NPI filter removes 12.1 M fills (0.3%, 3.2 M patients). Kept (the HCP filter needs the provider).
* No duplicate keys in product, provider, plan or view, so no join repeats fills.

---

## 1. Current notebook: what it does

| Cell | What it does |
| --- | --- |
| 1 | Header (out of date: names `IQV_LAAD_RX_VW`, "after 2017 for neph patients"; the code reads `STG_CAR_IQV_LAAD_FCT_RX` from `DATA_START_DATE`) |
| 3–5 | `00_connection`, `00_config`, `../00_cohort_config` (path broken since the move to `Rx Files`, needs `../../`) |
| 8 | **Step 1:** pulls 5 full tables into Spark (`SELECT *`): Rx fact, patient demographics, provider, product, plan; plus the HCP universe and the view `PHCDW_DSAA.CKD_PRODUCT_MAPPING_VW` |
| 9 | **Step 2:** joins them; keeps `SVC_DT >= DATA_START_DATE`, `NPI_NUMBER` not empty, view category not like "other"; validation filter (10 HCPs) |
| 10 | **Step 3:** `END_DT = SVC_DT + days supply + 7`, capped at the last date in the Rx table |
| 11 | **Step 4:** brand label `CATEGORY`: Invokana 100 / 300 MG by strength text, Jardiance, Farxiga, 23 DPP-IV names, 19 GLP-1 names; else the view category |
| 12 | **Step 5:** one row per day from `SVC_DT` to `END_DT`, then cohort month |
| 13 | **Step 6:** per patient and cohort month, the set of view categories (`TREATMENT_CATEGORY`) and brand labels (`CATEGORY`); joins the cohort label |
| 14 | Review markdown (added 2026-10-29) |
| 15–19 | Rename `COHORT_MONTH` → `DATE`, write `kerendia_nba_3_1_rx_journey_validation` |

### 1.1 Output and how it is used downstream

Output columns: `PATIENT_ID, DATE, TREATMENT_CATEGORY (array), CATEGORY (array), cohort_label`. Validation HCPs only (107,616 patient-months on 2026-10-26).

`06_patient_journey_combine`:
* Full join with the lab and Dx journeys on `PATIENT_ID, DATE` (Rx months also create patient-months in the spine).
* **SGLT2 flag:** a patient with any month where `TREATMENT_CATEGORY` contains the exact text `SGLT2` gets `SGLT2_FLAG = 1`. When the CKD stage is unknown, an SGLT2 patient counts as eligible. So the text of the categories is part of the contract.
* Treatment counts per month (`TOTAL_TREATMENTS`, new treatments) and the brand list (`CATEGORY` → `BRAND`).

Output contract for Phase A: same columns, same category texts. New columns can be added, none removed.

---

## 2. Bottlenecks found

From the code (review markdown, cell 14). *To measure* = checked with data in Step 1.

| # | Hardcoded / issue | Effect | Fix goes in |
| --- | --- | --- | --- |
| R1 | **Which drugs count and their category** come from a Snowflake view (`CKD_PRODUCT_MAPPING_VW`), matched on product name | Rules live outside the project; not visible in the basket; a new drug needs a change in someone else's view | Basket |
| R2 | **Categories with "other" excluded** by text match | A category renamed or added to the view changes the result silently | Basket (active flag) |
| R3 | **Brand labels typed in the code:** Invokana by strength text, Jardiance, Farxiga, 23 DPP-IV names, 19 GLP-1 names | Lists can only label products that are already in the view; a name not in the view is never labelled. *To measure* | Basket (brand label column) |
| R4 | **Newer GLP-1s not in the list:** Mounjaro, Zepbound, Wegovy (among the largest products in the basket) | Not labelled GLP-1; *to measure* whether the view keeps them at all | Phase A: measure; Phase B: decide (D3) |
| R5 | **Rx basket not used and not aligned:** its groups (ACE, ARB, BB, DIURETICS, OTHERS, brands) do not match the journey categories (e.g. metformin and Januvia are `OTHERS` in the basket; `metformin` and DPP-IV in the journey) | Two different code lists for the same thing | Basket (new columns, D1) |
| R6 | **Product names cut at 25 characters** in the basket (e.g. `METFORMIN HYDROCHLORIDE E`) | Matching on name may fail if the source has the full name. *To measure* (the IQVIA product table may also store 25 characters) | Basket check |
| R7 | **7 grace days; end date = last date in the Rx table** (not `date_end`); start = `DATA_START_DATE` on the fill date, so a fill from late 2022 that covers early 2023 is not counted | Run window not aligned with the other journeys; first months under-counted | Config (D4, D5) |
| R8 | **Joins that remove or add nothing:** patient demographics (left join, never used); plan table (inner join: drops fills whose plan is not in the plan table) | Extra work; silent loss. *To measure* | Code (D6) |
| R9 | **Five full tables pulled into Spark** (`SELECT *` of the Rx fact) and filtered there | Slow and heavy; filters could run in Snowflake | Config + code (D7) |
| R10 | **Table names, HCP universe path and output path typed in full** | A rename breaks the notebook | Config |
| R11 | **No dropped-rows report** | Losses are silent (name not in the view, "other" category, plan join, no NPI, empty days supply) | Code |
| R12 | **Brand label only for some SGLT2s:** combo products (Synjardy, Xigduo, Glyxambi, Trijardy, Invokamet, Qtern, Steglujan, Segluromet) and new SGLT2s (Brenzavvy, Inpefa) get the view category only; Kerendia has no label of its own. *To measure* | Kerendia and combo use not visible per brand | Basket (Phase A: measure; Phase B: decide) |

---

## 3. Current Rx basket (`Kerendia_Rx_Final.csv`)

* **258 rows**, columns: `PRODUCT_NAME, PRODUCT_GROUP, patients_total, providers_total, nbrx_total, club_members, n_members, in_752_features, is_clubbed, club_reason`.
* **28 clubbed rows** (`PRODUCT_GROUP = CLUBBED`, member names in `club_members`, comma-separated): insulin families (Lantus, Humalog, NovoLog, Tresiba, ...), CGMs (Libre, Dexcom, Guardian, Eversense), pumps (Omnipod, Tandem, iLet, V-Go), glucagon (Baqsimi, Gvoke), Edarbi, Diovan HCT, Micardis, Inderal. They must be expanded before matching.
* `PRODUCT_GROUP` mixes classes (ACE, ARB, BB, DIURETICS, OTHERS) and brands (JARDIANCE, OZEMPIC, MOUNJARO, KERENDIA, ENTRESTO BRAND, ...).
* Covers more than the 3.0 journey: HF drugs (Entresto, ivabradine / Corlanor, Verquvo, Inpefa), T1D devices (CGMs, pumps, glucagon), anemia and mineral drugs for CKD (iron, epoetin, phosphate binders, calcitriol), newer GLP-1s (Mounjaro, Zepbound, Wegovy).
* No column with the journey category (the 3.0 categories: ACE/ ARB, Calcium channel / Beta blocker, Combo drug, Diuretic_NON_MRA, Insulin, metformin, MRA, SGLT2, plus the brand labels).

---

## 4. Plan (Phase A)

Same layout as Dx and Px: title markdown, checks, the query alone in its cell, run, compare, findings markdown.

| Step | What | Comparison |
| --- | --- | --- |
| Setup | Clone the current notebook as `(Clone) 03_patient_journey_rx` (3.0 baseline; only the `../../00_cohort_config` path fixed). New header markdown in the main notebook | – |
| 0 | Run the 3.0 code unchanged; compare with the table last written | Patient-months and categories identical, or differences explained (data refresh) |
| 1 | Hardcoded-parts markdown + **profile**: the view (products, categories), the typed DPP-IV / GLP-1 lists vs the view, the basket vs the view (names, 25-character question), and the rows each filter removes (validation HCPs and all US, in Snowflake) | – (facts for D1–D3) |
| 2 | **Basket:** the product list, journey category and brand label come from the new Rx basket (section 5); built to reproduce the view and the typed lists exactly | vs 3.0: patient-months same / category added / removed, by product |
| 3 | **Config:** `RX_CONFIG` (tables, columns, dates, grace days, HCP universe path); filters run in Snowflake (one SQL instead of five full tables); checks that tables and columns exist | vs Step 2: identical expected, except the end date (`date_end`) and the start look-back if approved (D4); rows pulled |
| 4 | **Code:** remove the unused demographic join and, if approved, the plan join (D6); dropped-rows report; output columns unchanged | vs Step 3; report of rows dropped by reason |
| 5 | **Write:** switched off (`WRITE_OUTPUT = False`); goes live with the Dx / Px 3.1 tables | – |

Every comparison is shown for the validation HCPs (exact patient-month output, as `06_patient_journey_combine` uses it, incl. the SGLT2 flag) and, where cheap, for all US at fill level in Snowflake.

---

## 5. Proposed new Rx basket

Same style as the lab, Dx and Px baskets: one row per product or per clubbed group; all 258 rows kept; the original file renamed `Kerendia NBA 3.1 - RX Event List.csv` (unchanged, as for Px).

| Column | Meaning |
| --- | --- |
| `MATCH_TYPE` | `NAME` (one product name) or `LIST` (clubbed group, names separated by `\|`) |
| `MATCH_VALUE` | Product name(s), exactly as in the IQVIA product table |
| `CLUB_ID` | Name of the clubbed group (as today) |
| `PRODUCT_GROUP` | Kept from the original basket |
| `TREATMENT_CATEGORY` | Journey category, same texts as 3.0 (`ACE/ ARB`, `SGLT2`, `MRA`, ...); empty = not in the journey |
| `BRAND_LABEL` | The 3.0 `CATEGORY` value (`JARDIANCE`, `FARXIGA`, `DPP-IV`, `GLP-1`, ...); empty = use `TREATMENT_CATEGORY` |
| `STRENGTH` | Only where the label depends on it (Invokana 100 / 300 MG) |
| `CONDITION` | CKD / HF / DM / T1D / HTN / OTHER (what the drug is about) |
| `ACTIVE_JOURNEY` | `Y` = in the Rx journey (Phase A: exactly the 3.0 products) |
| `PATIENTS_TOTAL`, `IN_752_FEATURES` | Kept from the original basket |
| `NOTE` | Why a row was added or changed (e.g. `Added (D2): in the view, not in the basket`) |

Products in the view but not in the basket are added (marked in `NOTE`), so nothing is lost silently. Basket products not in the view get `ACTIVE_JOURNEY = N` in Phase A.

---

## 6. Decisions (applied as proposed, 2026-10-29)

| # | Decision | Proposal | Why |
| --- | --- | --- | --- |
| D1 | Basket format | Section 5; original kept as `Kerendia NBA 3.1 - RX Event List.csv` | Same as Px; one place for the drug rules |
| D2 | Parity source | Phase A reproduces the view + typed lists exactly; view products missing from the basket are added | Measure the basket effect alone; nothing lost silently |
| D3 | Newer GLP-1s (Mounjaro, Zepbound, Wegovy), SGLT2 combos, Kerendia label | Phase A: measure only (Step 1); Phase B: decide labels | Changes the brand lists and treatment counts in PJ06; needs a business decision |
| D4 | Date window | End = `date_end`; start look-back: also read fills from up to 97 days (90 days supply + 7) before `DATA_START_DATE` that still cover it; measured separately in Step 3 | Aligns with the other journeys; first months complete |
| D5 | Grace days | 7, moved to `RX_CONFIG` | Same rule, visible |
| D6 | Plan and demographic joins | Remove the unused demographic join; keep the plan join only if Step 1 shows it removes no rows (or confirm it is wanted) | No silent loss |
| D7 | Speed | One Snowflake SQL with the filters (dates, product list, HCP list), instead of 5 full tables in Spark | Faster; same result |
| D8 | Output and go-live | Same columns and category texts; write off until the Dx / Px 3.1 tables go live; PJ06 unchanged | PJ06 depends on the exact `SGLT2` text |

---

## 7. Not changed in Phase A

* The day-by-day spreading of fills (days supply + grace days) and the cohort-month logic (`assign_cohort_month`).
* The validation filter (`apply_hcp_filter`, 10 HCPs) for the written table.
* The categories and labels themselves (only where they come from).

---

## 8. Phase B (later)

* HF drug groups: ARNI (Entresto, sacubitril/valsartan), ivabradine, vericiguat, SGLT2 for HF; MRA already exists as a journey category (*to check* in Step 1 which category the view gives Kerendia, spironolactone and eplerenone).
* T1D signals: insulin pumps, CGMs, glucagon (already clubbed in the basket).
* GLP-1 / GIP-GLP-1 labels for Mounjaro, Zepbound, Wegovy; SGLT2 combo labels; Kerendia as its own label.
* CKD supportive drugs (iron, epoetin, phosphate binders) as signals of advanced CKD.
* Patient features from the basket `CONDITION` column (e.g. on HF therapy, on T1D devices).
