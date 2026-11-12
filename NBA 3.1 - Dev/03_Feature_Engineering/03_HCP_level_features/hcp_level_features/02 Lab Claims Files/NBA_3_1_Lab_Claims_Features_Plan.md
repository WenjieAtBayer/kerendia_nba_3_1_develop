# NBA 3.1 – HCP Lab claims features (NB02): sync with the 3.1 patient journey, analysis and plan

> **Update 2026-11-11.** This plan describes the Phase A sync (2026-11-03). Since then: 28 cohorts c1–c28 at offset 0 (claims cohort file, X13), Delta by COHORT_SET (X14), HbA1c/Potassium features added (+48, X18), 9-month window removed (−21, X19). Lookback windows: [1, 3, 6, 12]. Feature count: 116 → 143 (net +27). D2–D4 resolved. See `NBA_3_1_HCP_Features_Decisions.md`.

**Status (2026-11-03):** C1–C3 applied and validated on the 10 test HCPs (section 0). NB02 now reads the 3.1 lab data. Client summary: `02 Lab Claims Files/NBA_3_1_Lab_Claims_Features_Client_Summary.md`. D2–D4 open.  
**Notebook:** `hcp_level_features/02_claim_lab_monthly_cohort` (to be moved into `02 Lab Claims Files/`, then `%run "../../00_cohort_config"`; cohort-based since 2026-10; 3.0 source `kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/02_claim_lab_monthly`, unchanged)  
**Input before:** `query_output/Lab_03` (3.0 query in `00_Write_Input_Files`, not the patient journey)  
**Input now:** the NPI x patient x day lab pull of the 3.1 lab journey, `query_output/full_2026_11_02/_stage/lab_step4_pull` (PJ01 Step 4, written by the full patient-journey run 2026-11-02). Switch: `HCP_LAB_SOURCE` in `00_cohort_config` (`3.1` default, `3.0` = `Lab_03`)  
**Outputs:** `notebook_output/claim_lab_monthly_cohort` (NPI x `COHORT_ID`) and `provider_claim_lab_monthly_cohort` (`PROVIDER_ID` x `COHORT_ID`)  
**Approach:** same as NB01: list what changed upstream, measure what reaches this notebook, change only that, validate on the 10 test HCPs, write the client summary.  
**Scope:** sync with patient journey Phase A (lab journey PJ01, built and run 2026-11-02).

---

## 0. Implementation results

Run 2026-11-03 16:46, validation mode (10 test HCPs), offset 7, cohorts 2025-01 .. 2026-08 (20), input = 3.1 lab pull. All code cells run except the disabled one-time reset.

| Check | Result |
| --- | --- |
| Input | 3.1 pull, 498 lab test-days of the test HCPs (2023-01-04 .. 2026-09-29), 9 of the 10 NPIs; every row has a stage (load cell check). Common end date of the HCP inputs unchanged (2026-09-30) -> same 20 cohorts |
| Stage mapping | `GFR_STAGE` 1–5 / `UACR_STAGE` 1–3 -> the `Lab_03` texts; same 2 test types and 8 stages, same 102 columns as before |
| Fast engine = step-by-step (2025-01, 2026-08) | PASS: 2 x 900 cells, 0 mismatches |
| Write | 20 cohorts in one write; 180 rows (9 NPIs x 20), 102 columns, 0 duplicates, 0 null cells, no missing / extra cohort |
| Provider table | 180 rows, 0 null cells, 0 duplicates |
| HCP trace (default NPI 1528629052, now has lab claims) | 20 cohorts, 900 checks, 0 mismatches |
| Independent recount (pandas, straight from the pull, all 180 rows: total, eGFR, stage 3, A2 per window + `RUNNING_` total) | 3,060 checks, 0 mismatches |
| Offset-0 parity vs 3.0 `claim_lab_monthly_ZS` (reference `Lab_03` + 3.0 output, 19 months) | PASS: 8 NPIs x 116 columns x 19 months, 0 mismatches (feature logic unchanged) |
| Before (`Lab_03`, Delta version 1, same values as the 2026-10-26 write) vs after | See section 3, F5 |

---

## 1. Current notebook: what it does

| Part | What it does |
| --- | --- |
| Header (cells 1–2) | Title, 3.0 notes on the lab rules (test names, stage cut-offs) |
| Config (cells 4–6) | `00_connection` + `../00_cohort_config` |
| Load (cell 8) | Lab input (before: `Lab_03`; now: `HCP_LAB_TABLE`, C1) (validation: 10 test HCPs), claims from `DATA_START_DATE` (2023-01-01), cohort list, fixed pivot values (`TEST_TYPE`: GFR, UACR; `STAGE`: 5 eGFR stages + A1/A2/A3) |
| Features (cells 14–20) | Per window (1, 3, 6, 12 months): claims by `TEST_TYPE`, by `STAGE`, total; `RUNNING_` (all claims up to the cutoff); `PCT_` (share of the total); cohort metadata |
| Engine + checks (cells 23–24) | Fast all-cohorts engine, check fast = step-by-step on 2 cohorts |
| Write (cells 27–31) | One write of all cohorts, completeness checks, NPI to `PROVIDER_ID`, provider table |
| Validation (cells 34–35) | Offset-0 parity with the 3.0 output `claim_lab_monthly_ZS` (reference snapshot), HCP trace for every cohort |

The output has 102 columns per NPI and cohort (write of 2026-10-26 from `Lab_03`: 7 test NPIs x 20 cohorts = 140 rows).

---

## 2. What changed in the patient journey (3.1) and what reaches NB02

**Before this change NB02 read no patient-journey data.** Its only input was `Lab_03`, a 3.0 lab query in `00_Write_Input_Files` (cells marked `%skip`). The 3.1 lab journey (PJ01) writes one stage per patient and month (no NPI) as its output, but its Step 4 pull keeps the NPI and the day: one row per NPI, patient, day and test with the median result and the 3.1 stage, the same grain as `Lab_03`. The full patient-journey run stores it as `full_2026_11_02/_stage/lab_step4_pull`. Reading it gives NB02 every 3.1 lab rule below at once.

| Lab journey change (PJ01 3.1) | In `Lab_03`? | In the 3.1 pull (NB02 now) |
| --- | --- | --- |
| Test list and rules in the lab basket (`Kerendia_Lab_Final.csv`: LOINC codes + test-name backup, units, valid range, cut-offs) | No: test-name rules in SQL (`%GFR%`, `%GLOMERULAR%`, `%ALB%`, `%RATIO%`), raw name / unit columns, older provider table | Yes (same cut-offs as 3.0) |
| eGFR valid range 1–200; 150–200 = stage 1 | No: eGFR > 150 dropped | Yes |
| UACR valid range 0–10,000 | No | Yes |
| UACR components (urine creatinine) never staged | No | Yes |
| Same day: preferred eGFR equation (race-free CKD-EPI 2021) instead of the median of all equations | No: median of all equations | Yes |
| Results such as `>90`, `75^` kept | No: plain numbers only | Yes |
| Specialty filter (10 primary-care codes) | Same 10 codes, from an older provider table | Same 10 codes, from `STG_CAR_IQV_LAAD_DIM_PRVDR` (open decision L1) |
| HCP universe | 3.0 universe | 3.1 universe of the full run (open decision D3) |
| Dates | 2021-07-01 .. 2026-09-30 (NB02 keeps claims from 2023-01-01) | 2023-01-01 .. 2026-09-30 = `DATA_START_DATE`; no change for NB02 |

---

## 3. Findings (measured 2026-11-03)

**F1. `Lab_03` holds far fewer lab test-days than the lab journey, already in 3.0.** Same source (Quest, `STG_CAR_IQV_QUEST_TO_LAAD_HIST`), same rules on paper, very different volume (rows = NPI x patient x day x test, since 2023-01-01):

| Table | Built by | Rows | NPIs |
| --- | --- | --- | --- |
| `Lab_03` (NB02 input before) | 3.0 query "File Lab_03" in `00_Write_Input_Files` (cells `%skip`) | 108.8M | 122.9K |
| `kerendia_nba_3_0_lab_query_output` (3.0 lab journey input) | 3.0 query "File Pat Journey Lab" | 190.1M | 167.1K |
| `full_2026_11_02/_stage/lab_step4_pull` (NB02 input now) | 3.1 lab journey, PJ01 Step 4 | 207.5M | 199.9K |

So the HCP lab features counted a different (smaller) set of tests than the patient journey, in 3.0 as well. Differences in the `Lab_03` query (from the code, not isolated one by one): an older provider table for the specialty filter (`STG_IQVIA_LAAD_DIM_PROVIDER`), the raw test-name and unit columns instead of the cleaned ones, and the unit `MG/G {CREAT}` written with a space. The pull starts on 2023-01-01, which is `DATA_START_DATE`, so no feature loses history.

**F2. Tests counted in both have the same stage.** 2025-06, all US: of the rows in both tables, UACR 367,633 of 367,633 and eGFR 1,983,797 of 1,984,267 have the same stage (470 differ: the 3.1 preferred eGFR equation). Test HCPs: 208 of 208 shared test-days same stage. The change is which tests are counted, not how they are staged.

**F3. The pull can replace `Lab_03` without other code changes.** Same grain and keys (`NPI_NUMBER`, `PATIENT_ID`, `SVC_DT`, `TEST_TYPE`, `PROVIDER_ID`); stages are numbers (`GFR_STAGE` 1–5, `UACR_STAGE` 1–3) instead of texts, so NB02 maps them to the `Lab_03` texts and every column keeps its name. Every row of the pull has exactly one stage (GFR 174.6M rows, UACR 32.9M).

**F4. The header cells describe 3.0.** Cell 2 lists `KERENDIA_LAB_QUEST_LABCORP_VIEW` and "after 2018 / April 2021".

**F5. Before vs after on the 10 test HCPs** (`Lab_03` output vs 3.1 output, 20 cohorts):

| | Before (`Lab_03`) | After (3.1 pull) |
| --- | --- | --- |
| Lab test-days since 2023 | 240 | 498 (208 in both, 32 only before, 290 only after) |
| NPIs with lab features | 7 | 9: +1215675616, +1396374062, +1528629052; -1508230566 |
| Rows (NPI x cohort) | 140 | 180 |
| Columns | 102 | 102 (same names) |
| `RUNNING_TOTAL_LAB_CLAIMS`, last cohort (2026-08), sum over NPIs | 238 | 480 |
| `TOTAL_LAB_CLAIMS_IN_LAST_12_MONTH`, last cohort, sum | 92 | 151 |

For the 6 NPIs in both outputs (120 rows): 1,706 of 6,600 count cells changed (214 lower, the rest higher) and 1,426 of 4,800 share (`PCT_`) cells. NPI 1508230566 has 26 tests in `Lab_03` and none in the 3.1 pull; it is in the 3.0 universe and its Rx specialty is `NRP`. **Cause (checked 2026-11-03, NB01 step):** its `PROVIDER_ID` 10828538 is in the 3.0 universe but not in the 3.1 universe (`HCP_Universe_without_call_hcps`), which the full-run pull uses. Not the specialty filter.

---

## 4. Proposed changes

| ID | Change | Where | Expected impact |
| --- | --- | --- | --- |
| **C1** | NB02 reads the 3.1 lab pull (F1, F3): `load_lab_input()` maps `GFR_STAGE` / `UACR_STAGE` to the `Lab_03` stage texts; the load cell stops if a row has no stage; fixed pivot values from the mapping (no scan of the input) | NB02 load cell | More tests per HCP (F5); 3 test NPIs gain and 1 loses lab features; same stages for tests counted in both (F2) |
| **C2** | Run settings `HCP_LAB_SOURCE` (`3.1` default, `3.0` = `Lab_03`), `HCP_LAB31_PULL_TABLE` (default `full_2026_11_02/_stage/lab_step4_pull`) and `HCP_LAB_TABLE`; the common end date of the HCP inputs (`HCP_SOURCE_TABLES`) uses `HCP_LAB_TABLE` instead of `Lab_03` | `00_cohort_config` (run parameters cell, HCP cohort parameters cell) | Back to `Lab_03` with one job parameter; same 20 cohorts (both end 2026-09-30) |
| **C3** | Documentation: 3.1 note in the title cell and cell 2 | NB02 cells 1, 2 | None on data |

Not changed (by design): feature logic, column list, windows, `PCT_` / `RUNNING_` rules, and the offset-0 parity (it rebuilds the 3.0 output from the reference `Lab_03`, so it still checks the feature logic). `Lab_04` (NB04) is a separate 3.0 lab input; see D4.

---

## 5. Decisions

| ID | Question | Proposal |
| --- | --- | --- |
| D1 | Which lab input for the HCP lab features? | **Applied (user, 2026-11-03):** the 3.1 lab pull (C1), so HCP features and patient journey count the same tests with the same rules |
| D2 | Where the pull lives. Today it is a staging table of the full patient-journey run (`_stage/`); a validation PJ run does not write it | Have PJ01 write it as a named output of every run (for example `kerendia_nba_3_1_lab_npi`) and point `HCP_LAB31_PULL_TABLE` to it; until then do not delete `full_2026_11_02/_stage/lab_step4_pull` |
| D3 | Specialty filter (lab journey L1) and HCP universe: the pull uses the 3.1 universe; one test NPI (1508230566) drops out because it is not in the 3.1 universe | Same decision for both levels; confirm the 3.1 universe for the HCP features before the full run |
| D4 | `Lab_04` (NB04 input) is a 3.0 lab query of the same family | Check in the NB04 plan whether it should also read the 3.1 pull |

---

## 6. Validation plan (10 test HCPs, offset 7)

1. Notebook checks: fast engine = step-by-step (2 cohorts), completeness (20 cohorts, no duplicates, no nulls), provider mapping, HCP trace for every cohort.
2. Offset-0 parity with the 3.0 output `claim_lab_monthly_ZS` (reference snapshot).
3. Independent recount from the pull in pandas (windows and `RUNNING_`), every row.
4. Before vs after (`Lab_03` output vs 3.1 output): same columns; every difference explained by the input (test-days only in one table, F5).

---

## 7. Next steps

1. Move NB02 into `02 Lab Claims Files/` and change its config cell to `%run "../../00_cohort_config"`.
2. D2–D4 before the full run.
3. Full run: NB02 with `VALIDATION_MODE = false` reads the whole pull (207.5M rows).
