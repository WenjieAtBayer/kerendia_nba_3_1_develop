# NBA 3.1 – HCP Rx claims features (NB01): sync with the 3.1 patient journey, analysis and plan

**Status (2026-11-03):** C1–C5 applied and validated on the 10 test HCPs (section 0: C1–C3; section 0b: C4–C5, Rx input switched to the 3.1 Rx journey). Client summary: `01 Rx Claims Files/NBA_3_1_Rx_Claims_Features_Client_Summary.md`. Full run waits for the other HCP notebooks.  
**Notebook:** `hcp_level_features/01 Rx Claims Files/01_claim_rx_monthly_cohort` (moved into this folder 2026-11-03; config `%run` changed to `../../00_cohort_config` and checked) (cohort-based since 2026-10; 3.0 source `kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/01_claim_rx_monthly`, unchanged)  
**Inputs:** the HCP Rx pull of the 3.1 Rx journey (`<run>/_stage/rx_hcp_pull`, written by PJ03 Step 4d; C4; was `query_output/Rx_01_new`, written by `00_Write_Input_Files`) and the patient table `pat_new_and_total_treatments` (written by `06_patient_journey_combine`, from the Rx journey PJ03)  
**Outputs:** `notebook_output/claim_rx_monthly_cohort` (NPI x `COHORT_ID`) and `provider_claim_rx_monthly_cohort` (`PROVIDER_ID` x `COHORT_ID`)  
**Approach:** as for the patient journey notebooks: list what changed upstream, measure what reaches this notebook, change only that, then validate on the 10 test HCPs and write the client summary.  
**Scope:** sync with patient journey Phase A (what is built today). Phase B items of the patient journey (new drugs, HF / T1D groups) are listed in section 5, not applied.

---

## 0. Implementation results

Run 2026-11-03, validation mode (10 test HCPs, 9 with Rx claims), offset 7, cohorts 2025-01 .. 2026-08 (20). All code cells run except the disabled one-time reset.

| Check | Result |
| --- | --- |
| Patient table read (C1) | `query_output/validation_2026_10_30/kerendia_nba_3_1_pat_new_and_total_treatments_validation` (printed by the load cell) |
| Fast engine = step-by-step (2025-01, 2026-08) | PASS: 2 x 33,219 cells, 0 mismatches, same column order and types |
| Write | 20 cohorts in one write, 0.7 min; 180 rows, 3,693 columns, 0 duplicates, 0 null cells, no missing / extra cohort |
| Provider table | 180 rows, 0 null `PROVIDER_ID`, 0 duplicates |
| HCP trace (1386651560, pandas recount) | 20 cohorts, 2,100 checks, 0 mismatches |
| Offset-0 parity vs 3.0 `claim_rx_monthly` (19 months, 3.0 inputs) | PASS: 700,150 cells, 0 mismatches; 19 known-quirk cells (3.0 `RUNNING_TOTAL_REJECTED_RX_CLAIMS_SGLT2_WO_INVOKANA_300MG` 1 lower than its own SGLT2 − Invokana 300 MG) |
| Before (2026-10-26 output) vs after C1 | Same 180 (NPI, cohort) keys and columns. The 3,614 feature columns that do not use the patient table: **identical**. Of the 72 patient-treatment columns, 40 differ (2,566 of 12,960 cells): the 32 windowed new-treatment columns (incl. `PCT_`) and the 8 `RUNNING_` columns; the 32 windowed active-treatment columns are identical |

Size of the change (sum over 180 rows): windowed new-treatment columns −0.1% to +5.3% (e.g. 1 new treatment, last 12 months 21,940 → 22,048); at most 8 claims per row; largest share change 0.20 (NPI 1396374062, 2025-06, 5 claims in the month). `RUNNING_` columns: 1 active −3.0%, 3+ active +2.0%, 2–3 new −23.0%, 3+ new −35.1%, no new +1.3% (early-2023 look-back of the 3.1 Rx journey).

Correction to section 3 / 4: the feature columns are 3,686 (3,693 minus 7 key and cohort columns), so the columns that do not use the patient table are 3,614, not 3,621.

## 0b. Rx input from the 3.1 Rx journey (C4, C5)

Run 2026-11-03 (evening), same settings. Why: NB02 and NB03 read the lab and Dx pulls of the 3.1 journeys; NB01 still read the 3.0 `Rx_01_new`, so the three HCP inputs did not use the same rules.

**What was built.** The Rx journey pull (`rx_fills_tagged`, PJ03 Step 4a) has no rejection, refill, payer, birth year or gender columns, and the journey drops `Other- glucose mgmt` (GLP-1, DPP-IV, sulfonylureas). So a new step was added to PJ03, **Step 4d (HCP Rx pull)**, which leaves the journey itself unchanged. It uses the same tables, Rx basket, dates, HCP universe and drop rules as Step 4a, plus:

| # | Added for the HCP features | Why |
| --- | --- | --- |
| H1 | `REJECTION_FLAG`, `REFILL_FLAG`, `METHOD_OF_PAYMENT`, `PATIENT_BIRTH_YEAR`, `PATIENT_GENDER` (3.0 definitions) | Rejection, refill, payer, age and gender features |
| H2 | The view's `Other- glucose mgmt` products; GLP-1 / DPP-IV labels from the 3.0 lists | **User decision 2026-11-03: keep GLP-1 / DPP-IV for NB01** |
| H3 | Brand label `SPIRONOLACTONE-MRA` (3.0 rule) | In the HCP brand list; the basket labels these fills `MRA` |
| H4 | One row per 3.0 claim key (`MAX(DAYS_SUPPLY)`) | Same claim count as 3.0 |
| H5 | Empty days supply kept; no look-back | A claim is a claim; the look-back only matters for days on therapy |

Output: `<run>/_stage/rx_hcp_pull`, written now for the validation run (`validation_2026_10_30/`). Config (`00_cohort_config`): `HCP_RX_SOURCE` (`"3.1"` default, `"3.0"` = `Rx_01_new`), `HCP_RX31_PULL_TABLE`, `HCP_RX_TABLE` (added to `HCP_SOURCE_TABLES`; `Rx_01_new` stays there for NB04 / NB06).

**C5. Column set.** The pull starts at 2023-01-01, so 144 value combinations seen only before 2023 (e.g. rejected Invokana 300 MG, age 0–10 groups) lost their column; the first run left them empty (null) in the table. Fix: with the 3.1 input, the fixed pivot values also take the combinations of the 3.0 `Rx_01_new` history (same NPIs). The columns are back to the 3.0 set and are 0, as before (they were 0 in the 3.0-input run too).

| Check | Result |
| --- | --- |
| Pull vs `Rx_01_new` (9 test HCPs, 2023-01-01 .. 2026-09-30), row by row on NPI, patient, date, product, strength | 50,739 of 50,739 3.0 claims in the pull with **all 8 feature columns equal** (category, brand, rejection, payer, birth year, gender, refill, days supply); 2 extra claims in the pull (newer data: Ozempic 2026-07-18 for NPI 1659887388, lisinopril 2026-09-30 for 1801062104) |
| Labels in the pull | GLP-1 2,793, DPP-IV 335, other glucose 1,580, spironolactone 808: same as 3.0 |
| Patients with more than one demographics row | 0 |
| Fast engine = step-by-step (2 cohorts) | PASS: 2 x 33,219 cells, 0 mismatches |
| Write | 20 cohorts, 180 rows, 3,693 columns, 0 duplicates, **0 null cells** |
| HCP trace (1386651560) | 2,100 checks, 0 mismatches |
| Own recount from the pull (GLP-1, DPP-IV, spironolactone, other glucose; 4 windows, 20 cohorts, 9 NPIs) | 2,880 checks, 0 mismatches (1,583 non-zero) |
| Offset-0 parity vs 3.0 (3.0 inputs) | PASS: 700,150 cells, 0 mismatches, 19 known-quirk cells (as before) |
| Before (3.0 input) vs after (3.1 input) | Same keys and columns. 1,731 of 663,480 cells differ, **all for NPI 1659887388** (the extra Ozempic claim; the lisinopril claim is after the last cutoff). Other 8 HCPs identical |

Last cohort (2026-08), 9 HCPs, last 12 months: GLP-1 698, DPP-IV 35, other glucose 1,035, all Rx claims 12,837.

**Universe.** The validation run of the patient journey uses the 3.0 HCP universe (config default); the full run uses the 3.1 universe. HCP 1508230566 is in the 3.0 universe but **not in the 3.1 universe**: this is why it drops out of NB02 and NB03 (which read full-run pulls), not its specialty. In NB01 validation it stays (validation pull); in the full run it will drop out of NB01 too.

---

## 1. Current notebook: what it does

| Part | What it does |
| --- | --- |
| Part 1 (cells 2–4) | Reverse engineering of the 3.0 notebook: pipeline, feature groups, where the monthly logic was hardcoded |
| Part 2 (cell 5) | Cohort design: windows of 1, 3, 6, 12 months ending at the cohort cutoff (offset 7) |
| Config (cells 7–9) | `00_connection` + `../00_cohort_config` |
| Load (cell 10) | `Rx_01_new` (validation: 10 test HCPs), the patient table `pat_new_and_total_treatments`, brand filter, derived columns (days supply bin, payer, age, gender) |
| Features (cells 11–19) | Fixed pivot values; groups 2.1 treatment category, 2.2 brand, 2.3 rejection, 2.4 duration, 2.5 refill, 2.6 payer, 2.7 patient attributes, **2.8 patient treatment** (the only group that uses the patient journey); `RUNNING_`; AVG family |
| Derived (cells 21–25) | `SGLT2_WO_INVOKANA_300MG`, `PCT_`, difference and ratio columns, cohort metadata |
| Engine + checks (cells 27–29) | Fast all-cohorts engine, check fast = step-by-step on 2 cohorts, single HCP trace |
| Write (cells 32–35) | One write of all cohorts (`replaceWhere` on `COHORT_ID`), completeness checks, NPI to `PROVIDER_ID`, HCP trace for every cohort |
| Validation (cell 37) | Offset-0 parity with the 3.0 output `claim_rx_monthly` (reference snapshot `ops_pipeline_bkp/`) |
| Part 4 (cell 38) | Status notes (partly out of date, see C3) |

The output has 3,693 columns per NPI and cohort (20 cohorts in the last write, 2026-10-26).

---

## 2. What changed in the patient journey (3.1) and what reaches NB01

NB01 uses the patient journey in **one place only**: group 2.8 (patient treatment). Each Rx claim is joined to the patient's row of `pat_new_and_total_treatments` for the claim's cohort month, and the claim is counted under the patient's number of active treatments (`NO` / `1` / `2_OR_3` / `3_MORE_ACTIVE_TREATMENTS`) and of new treatments (same buckets). 72 columns (`TOTAL_RX_CLAIMS_PATIENT_WITH_*`: 8 buckets x 4 windows + `RUNNING_` + `PCT_`).

| Patient journey change (3.1, Phase A) | Reaches NB01? | How |
| --- | --- | --- |
| Rx journey: drug list and categories from the product basket, identical to 3.0 (PJ03) | No change in categories | Same treatment categories, so the treatment counts keep their meaning |
| Rx journey: 97-day look-back (fills from late 2022 that cover 2023 now count) | **Yes**, through 2.8 | More active treatments in 2022-12 .. 2023-03; fewer "new" treatments in early 2023 (a drug started in late 2022 is no longer new in 2023) |
| Rx journey: end date 2026-09-30, empty days supply dropped | Yes, very small | A few patient-months at the end |
| Combine (PJ06 3.1): months are cohort months at offset 7, history from 2022-12 | Already handled | NB01 joins on `assign_cohort_month(SVC_DT)` at the cohort's offset (fixed 2026-10-22) |
| Combine: validation patients = patients of the lab / Dx / Rx journeys of the 10 HCPs | Yes, small | The table has 193 more patients |
| Lab / Dx / Px / DM-HF flags / eligibility (PJ01, PJ02, PJ04, PJ05, PJ06 eligibility) | No | NB01 does not use them |
| Run folders (`RUN_OUTPUT_DIR`: `validation_2026_10_30/`, `full_2026_11_02/`) | **Yes** | NB01 still reads an older copy in the `query_output/` root, not the run folder (finding F1) |

---

## 3. Findings (measured 2026-11-03)

**F1. NB01 reads an outdated copy of the patient table.**

| Table | Written | Rows (patient-months) | Patients | Months |
| --- | --- | --- | --- | --- |
| `query_output/kerendia_nba_3_1_pat_new_and_total_treatments_validation` (read today) | 2026-10-26, before the 3.1 Rx journey | 137,373 | 4,238 | 2022-12 .. 2026-09 |
| `query_output/validation_2026_10_30/kerendia_nba_3_1_pat_new_and_total_treatments_validation` (3.1 end-to-end run) | 2026-11-02 | 140,370 | 4,431 | 2022-12 .. 2026-09 |

Old vs new, patient-month by patient-month: 128,091 the same, 1,503 with a different number of treatments, 931 with a different number of new treatments, 9,845 only in the new table, 6,848 only in the old one. Most differences are in 2022-12 .. 2023 (look-back) and in the patient set; from 2025-01 the totals are almost equal (new treatments 3,301 vs 3,306, treatments 102,576 vs 102,433).

Effect on the Rx claims of the 10 test HCPs since 2023 (50,818 claims, offset 7): claims matched to a patient row 50,141 (old) vs 50,150 (new); claims of patients with at least one new treatment 5,396 vs 4,931 (−9%, nearly all in 2023, so mainly `RUNNING_` columns).

**F2. The month join is correct at offset 7.** 98.7% of the test HCPs' claims find their patient row; the unmatched claims are spread over all months (10–14 per month), i.e. patients with no journey row that month, not a month shift. They fall in `NO_ACTIVE_TREATMENT` / `NO_NEW_TREATMENT`, as in 3.0.

**F3. Cohorts are within the patient table.** The common end date of the HCP inputs is 2026-09-30 (`Rx_01_new` ends 2026-10-02), so the last cohort is 2026-08 (cutoff 2026-09-06). The patient table runs to 2026-09, so no cohort reads past its end.

**F4. Production would read a calendar-month table.** In production mode NB01 reads the 3.0 `pat_new_and_total_treatments` (calendar months) and joins it on offset-7 cohort months: each claim from the 1st to the 6th of a month would get the patient's row of the wrong month. The 3.1 full-run table exists (`full_2026_11_02/kerendia_nba_3_1_pat_new_and_total_treatments_validation`) but is not read.

**F5. NB01's own treatment categories do not come from the patient journey.** They come from `Rx_01_new` (3.0 Snowflake view), which is the same source the Rx journey Phase A reproduces. Two known differences between the HCP level and the patient level are inherited from 3.0 and unchanged:
* `Rx_01_new` keeps `Other- glucose mgmt` (338 M claims since 2023: GLP-1s such as Ozempic, DPP-IVs, sulfonylureas), so NB01 has a `TOTAL_RX_CLAIMS_OTHER_GLUCOSE_MGMT` column and `GLP-1` (187 M claims) and `DPP-IV` (39 M) brand columns. The Rx journey drops this category, so these drugs do not count in the patient's number of treatments.
* Kerendia, Mounjaro, Wegovy, Zepbound and generic dapagliflozin are not in `Rx_01_new` at all (same gap as the Rx journey, Phase B there).

**F6. Part 4 status cell is out of date.** It says the NPI to `PROVIDER_ID` mapping is not added (it is, cell 34) and mentions "cells 18, 19, 20" and "one cohort per run" (now all cohorts in one run).

---

## 4. Proposed changes

| ID | Change | Where | Expected impact |
| --- | --- | --- | --- |
| **C1** | Read the patient table from the patient-journey run folder (`RUN_OUTPUT_DIR`) when it is there, else from `query_output/`: new rule in `get_patient_table_path()` of `00_cohort_config`; NB01 loads the table through it and prints the path | `00_cohort_config` (HCP shared constants), NB01 cell 10 | Validation: reads `validation_2026_10_30/` (F1). Only the 72 `TOTAL_RX_CLAIMS_PATIENT_WITH_*` columns can change; all other 3,614 feature columns must stay identical |
| **C2** | Same rule in production: when the job sets `RUN_OUTPUT_DIR` (e.g. `full_2026_11_02/`), the 3.1 full-run table is read; without it, the 3.0 table as today | Same function (no extra code) | Fixes F4 for the full run; nothing changes until the full run |
| **C4** | Rx input = HCP Rx pull of the 3.1 Rx journey (new PJ03 Step 4d, section 0b); switch `HCP_RX_SOURCE` in `00_cohort_config` | PJ03 (new Step 4d), `00_cohort_config`, NB01 cells 1, 10, 29 | Validated: same claims as `Rx_01_new` + newer data (section 0b) |
| **C5** | Fixed pivot values also from the 3.0 `Rx_01_new` history when the input is 3.1 | NB01 cell 11 | Same 3,693 columns, no nulls |
| **C3** | Documentation: header and Part 4 status updated (mapping done, all cohorts per run, patient table source, offset alignment); comment in cell 17 ("from NB06" is PJ06) | NB01 cells 1, 17, 38 | None on data |

Not changed (by design): feature logic, column list, windows, `PCT_` / `RUNNING_` / AVG rules, brand list, NPI filter.

The C1 rule is shared: NB06 (eligible patients) also reads its patient tables through `get_patient_table_path()`, so it will read the run folder too (it is not run in this step).

---

## 5. Decisions

| ID | Question | Proposal |
| --- | --- | --- |
| D1 | Which patient table in validation? | The run folder of the latest patient-journey run (C1) |
| D2 | Which patient table in the full run? | The full-run folder via the job parameter `RUN_OUTPUT_DIR` (C2); decided when the full run is planned |
| D3 | Align NB01's categories with the patient journey (drop `Other- glucose mgmt`, or add it to the journey)? | **Decided 2026-11-03 (user): keep GLP-1 / DPP-IV for NB01** (H2). The patient journey still drops them; revisit with Rx journey Phase B |
| D4 | Add Kerendia / new GLP-1 drugs to NB01? | Now possible: the HCP Rx pull is built from the product basket, so a basket change reaches NB01. Phase B |
| D5 | Full run of the HCP Rx pull | PJ03 Step 4d must run once in the full-run folder (`full_2026_11_02/`, all US, 3.1 universe) before NB01-NB06 run in production; until then production NB01 stops at the missing table (and `get_hcp_data_max_date()` for all HCP notebooks, since the pull is in `HCP_SOURCE_TABLES`) |
| D6 | Remove the C5 dependency on `Rx_01_new` | Later: replace it with a fixed column list (e.g. the 277 selected features + keys) once the feature list is final |

---

## 6. Validation plan (10 test HCPs, offset 7)

1. Notebook checks: fast engine = step-by-step (2 cohorts), completeness (20 cohorts, no duplicates, no nulls), HCP trace for every cohort, provider mapping.
2. Offset-0 parity with the 3.0 output (reference snapshot, 3.0 patient table): must still pass, since C1 does not change the parity inputs.
3. Before vs after C1 (the output written 2026-10-26 vs the new one): the 3,614 feature columns that do not use the patient table must be identical; the 72 patient-treatment columns are compared and the differences explained.

---

## 7. Next steps

1. Validation run (section 6), results in section 0.
2. Client summary: `01 Rx Claims Files/NBA_3_1_Rx_Claims_Features_Client_Summary.md`.
3. Full run: run PJ03 Step 4d in the full-run folder (D5), then set `RUN_OUTPUT_DIR` to the full-run folder (D2).
4. Phase B with the Rx journey (D4); NB04 also reads `Rx_01_new` (same switch to consider there).
