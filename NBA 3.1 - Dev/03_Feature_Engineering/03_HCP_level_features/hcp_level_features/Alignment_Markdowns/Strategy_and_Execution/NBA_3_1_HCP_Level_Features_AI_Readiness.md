# HCP-level claims features in NBA 3.1: Readiness Plan

**Group:** HCP-level claims features (Rx, lab, diagnosis, combined claims, new patient starts, eligible patients), notebooks NB01–NB06 in `hcp_level_features/` and the shared config `../00_cohort_config`  
**Purpose:** one plan for how the HCP-level claims features go into NBA 3.1: what we build, from which data, in which order, how we test it, and when it is ready  
**Builds on:** the six individual plan files and client summaries (one per notebook folder), the decision log (`NBA_3_1_HCP_Features_Decisions.md`), the selected feature list (`Feature Analysis/NBA_3_1_HCP_Claims_Selected_Features_277.csv`) and the patient journey readiness plan (`Patient_Journey_Validation/Alignment_Markdowns/Strategy and Execution/AI_Readiness_Plan.md`)  
**Status:** Phase A built and validated on the test HCPs in all six notebooks. Full HCP universe run: all six written and checked (2026-11-04, E2E file in `Review_and_Findings/`). Code committed as `2d978d1`; the 2026-11-04 documentation is not committed yet.  
**Update 2026-11-06:** storyline 3.0 -> 3.1 added (section 1a): per-notebook changes, codes that reach each notebook, and which patient-journey output each notebook reads. New in the code (not run yet, next full run `full_2026_11_06`): NB02 lab flag features (potassium > 5.0, HbA1c >= 9%, 48 columns) and NB06 diabetes / HF type features (148 columns).  
**Date:** November 6, 2026 (first version November 4, 2026)

This file combines the detail of each individual plan. The original plan files remain in their folders for reference.

---

## 1. In short

* **Six notebooks (NB01–NB06) build the HCP-level claims features at the 3.1 cohort grain:** one row per HCP and cohort (`COHORT_ID`, offset 7, 20 cohorts 2025-01 .. 2026-08), windows of 1, 3, 6 and 12 months ending at the cohort cutoff, `RUNNING_` from `DATA_START_DATE` (2023-01-01) and `PCT_`. The feature logic is the 3.0 logic; only the time grain changed.
* **Each notebook is synced with the 3.1 patient journey (Phase A).** The Rx, lab and Dx inputs are now the NPI-level pulls of the 3.1 journeys (PJ03 Step 4d, PJ01 Step 4, PJ02 Step 4), and the patient tables are read from the patient-journey run folder (`RUN_OUTPUT_DIR`). One switch per source in `00_cohort_config` goes back to the 3.0 input. NB05 keeps its 3.0 input on purpose (X7).
* **Validation on the test HCPs passed in every notebook:** fast engine = step-by-step, completeness (0 duplicates, 0 null cells), HCP trace, independent recount and offset-0 parity with 3.0. The only parity failure (NB06, window columns) is explained by the 3.0 window rule and accepted (X8, X9).
* **The biggest 3.1 changes that reach the features:** Dx stage 3 and stage 5 are now counted (NB03, NB04, NB06); many more lab tests are counted (NB02, NB04: the 3.0 inputs `Lab_03` / `Lab_04` held far fewer tests than the lab journey). The Rx claims of NB01 are the same as 3.0 apart from newer data.
* **One HCP universe (3.1, 294,727 providers) for the patient journey and the HCP features (X1).** Test HCP 1508230566 is not in it, so 9 of the 10 test HCPs remain. Checked 2026-11-04: the full patient-journey run used the 3.1 universe; the validation patient-journey run used the 3.0 universe (parameter left empty, so the config default applied).
* **Full run (job 36449327509782):** all six notebooks are written for the full universe and checked (section 11.2). NB01 and NB04 first failed because a check cell loaded two full cohorts into the notebook's memory; after the fix (trace HCPs only in full mode) the re-run passed. Recounts from the full inputs: 0 differences. Open: the provider tables still use the NBA 3.0 NPI mapping (O2).
* **277 features were selected for the model:** NB01 170, NB01 + NB04 2, NB03 3, NB04 87, NB05 14, NB06 1. 9 NB04 features (DPP-IV / other glucose in family C) are no longer produced under the patient-journey rule and are dropped from the list (X5); the 3.1 model is retrained and its feature selection rerun on the 3.1 output.

---

## 1a. Storyline: from 3.0 to 3.1

For the details of each patient-journey notebook (baskets, rules, numbers) see the patient journey readiness plan: `Patient_Journey_Validation/Alignment_Markdowns/Strategy and Execution/AI_Readiness_Plan.md`. This section shows what reaches the HCP features.

### 1a.1 The story in four steps

| Step | What happened | Effect on the HCP features |
| --- | --- | --- |
| 1. NBA 3.0 | Six notebooks on calendar-month rows; inputs from the 3.0 queries (`Rx_01_new`, `Lab_03`, `Lab_04`, `Dx_03`, `kerendia_nba_3_0_Rx_05`) with the rules written in SQL (test names, stage texts, product lists) | Baseline |
| 2. Cohort grain (Phase A) | One row per HCP and cohort (offset 7, 20 cohorts), windows of 1, 3, 6, 12 months ending at the cutoff, counts from `DATA_START_DATE` (2023-01-01), fixed column lists. Feature logic unchanged | Same features, new time grain; offset-0 parity with 3.0 passed (NB06 window rule explained, X8) |
| 3. Sync with the 3.1 patient journey | Inputs = the NPI-level pulls of the 3.1 journeys (PJ01 / PJ02 / PJ03 Step 4) and the patient tables of the run folder (`RUN_OUTPUT_DIR`). Codes come from dated product mapping files (`final_product_mapping/`, loader `product_mapping_path()`) instead of SQL | More tests and codes counted (table 1a.2); NB05 kept on its 3.0 input (X7) |
| 4. New 3.1 features (2026-11-06) | Lab flags in NB02 (potassium, HbA1c) and diabetes / HF type in NB06, from the new 3.1 patient-journey outputs | +48 columns NB02, +148 columns NB06; existing columns unchanged by design |

### 1a.2 Per notebook: 3.0 vs 3.1

| Notebook | 3.0 input | 3.1 input | What changes in the features | Codes / products that now reach it |
| --- | --- | --- | --- | --- |
| **NB01 Rx** | `Rx_01_new` | HCP Rx pull (PJ03 Step 4d) + patient treatments (PJ06) | Cohort grain; new `..._KERENDIA_...` category columns; GLP-1 counted under `Other- glucose mgmt` as in 3.0 (option C) | Mapping 2026_11_05: 13 GLP-1 products (Ozempic, Mounjaro, Trulicity, Rybelsus, Victoza, liraglutide, Bydureon BCise, Byetta, exenatide, Wegovy, Wegovy HD, Zepbound, Saxenda), Kerendia (own category), generic dapagliflozin (+ metformin) as SGLT2 |
| **NB02 Lab** | `Lab_03` (test-name match) | Lab pull (PJ01 Step 4) | eGFR / UACR features: same columns, many more tests counted. New: 48 lab flag columns | eGFR LOINC 98979-8, 98980-6 (race-free 2021), 62238-1, 33914-3, 48642-3, 88294-4, 50210-4, 88293-6; UACR LOINC 9318-7, 14958-3; 3.0 name rules kept as backup. 2026_11_06: potassium 2823-3 and HbA1c 4548-4 (value only, no stage) |
| **NB03 Dx** | `Dx_03` (stage from description text) | Dx pull (PJ02 Step 4) + new CKD stage table (PJ06) | Stage from the code: stage 3 and stage 5 counted (were missing) | Stage 3: N18.30, N18.31 (3a), N18.32 (3b); stage 5: N18.5, N18.6 (ESRD), I12.0, I13.11, I13.2 |
| **NB04 Combined** | `Rx_01_new`, `Lab_04`, 3.0 patient tables | Rx pull, lab pull (eGFR / UACR only), GFR / Dx and UACR stage tables (PJ06) | Patients' stage now includes Dx stage 3 / 5 and the 3.1 lab stages; GLP-1 option C; 9 selected family C features no longer produced (X5) | Same codes as NB01 (Rx), NB02 (eGFR / UACR) and NB03 (Dx stage), through the patient tables |
| **NB05 New starts** | `kerendia_nba_3_0_Rx_05` | Same (kept, X7) | Cohort grain only | None |
| **NB06 Eligible** | `Rx_01_new`, 3.0 eligibility table, 3.0 `df_px` | Rx pull, eligibility table (PJ06), dialysis table (PJ05), diabetes / HF flags (PJ04) | Eligibility from the 3.1 journey (stage 3 / 5, dialysis dates). New: 148 diabetes / HF type columns | Dialysis basket (30 codes, J0606 added 2026_11_05; ESRD monthly codes); diabetes and HF codes of PJ04 (`Kerendia_Dx_Final` + `Kerendia_Dx_Flag_Additions`, 116 codes) |

### 1a.3 Which patient-journey output each HCP notebook reads

| Patient-journey output (run folder) | Written by | Read by | Used for |
| --- | --- | --- | --- |
| `_stage/rx_hcp_pull` | PJ03 Step 4d | NB01, NB04, NB06 | Rx claims per HCP (base of every Rx feature) |
| `_stage/lab_step4_pull` | PJ01 Step 4 | NB02, NB04 | NB02: eGFR / UACR features + potassium / HbA1c flags. NB04: eGFR / UACR only |
| `_stage/dx_step4_pull` | PJ02 Step 4 | NB03 | Dx claims by CKD stage |
| `kerendia_nba_3_1_pat_new_and_total_treatments_validation` | PJ06 | NB01 | Group 2.8 (active / new treatments of the patient) |
| `kerendia_nba_3_1_pat_new_ckd_stage_validation` | PJ06 | NB03 | Claims of patients new to a stage |
| `kerendia_nba_3_1_pat_gfr_dx_stage_validation` | PJ06 | NB04 | Families A and C (GFR / Dx stage) |
| `kerendia_nba_3_1_pat_uacr_stage_validation` | PJ06 | NB04 | Family C (UACR stage x treatment) |
| `kerendia_nba_3_1_pat_sglt2_filter_m_validation` | PJ06 | NB06, NB02 | `ELIGIBLE_PATIENT_FLAG`: NB06 eligible features; NB02 eligible lab flag counts (new) |
| `kerendia_nba_3_1_px_validation` | PJ05 | NB06 | `DIALYSIS_FLAG` |
| `kerendia_nba_3_1_dm_hf_flags_validation` | PJ04 | NB06 (new, 2026-11-06) | `DM_TYPE`, `HF_TYPE`, `HF_FIRST_DATE`: diabetes / HF type features |
| `kerendia_nba_3_1_lab_flags_validation` | PJ01 (new, 2026-11-06) | None (check table) | Per patient-day potassium / HbA1c values and flags; NB02 builds its flags from the lab pull with the same rules (`LAB_FLAG_RULES`) |
| `kerendia_nba_3_1_{lab,dx,rx}_journey_validation` | PJ01 / PJ02 / PJ03 | Not read by NB01–NB06 | Inputs of PJ06 |

### 1a.4 New 3.1 features (2026-11-06, code ready, not run yet)

**NB02 lab flags** (user decision 2026-11-06: potassium and HbA1c lab tests only; no Dx E87.5, no potassium binders, no Px HbA1c codes):

| Flag | Rule | Why |
| --- | --- | --- |
| `POTASSIUM_GT_5` | Potassium (LOINC 2823-3) > 5.0 mmol/L | Kerendia must not be started above 5.0 mmol/L (US label) |
| `HBA1C_GE_9` | HbA1c (LOINC 4548-4) >= 9% | Uncontrolled diabetes |

Per flag and window (1, 3, 6, 12 months): `TOTAL_PATIENTS_<TEST>_TESTED`, `TOTAL_PATIENTS_<FLAG>`, `PCT_PATIENTS_<FLAG>` (base = patients tested for that test) and the same for eligible patients (`TOTAL_ELIGIBLE_PATIENTS_...`, `PCT_ELIGIBLE_PATIENTS_...`). Counted per patient-month, as NB06. Data check (Quest, 2023+, primary-care NPIs): potassium 328.9M rows / 29.1M patients / 455.7K NPIs, 23.4M results > 5.0; HbA1c 286.6M rows / 20.0M patients / 357.5K NPIs, 15.6M results >= 9%.

**NB06 diabetes / HF type** (`DM_TYPE` and `HF_TYPE` from PJ04): per window (1, 3, 6, 12 months), all Rx patients (`TOTAL_RX_PATIENTS_...`) and eligible patients (`TOTAL_ELIGIBLE_PATIENTS_...`) by `DM_TYPE` (T2D, T1D, OTHER, NONE), with HF that month (`_HF`) and by `HF_TYPE` (HFPEF_PROXY, HFREF_PROXY, MIXED, UNKNOWN), plus `PCT_` shares. HF in a month = month on or after the month of `HF_FIRST_DATE` (same rule as the monthly `HF_FLAG` of PJ06). Why: Kerendia's indications are CKD with T2D and HF with LVEF >= 40% (HFpEF proxy); the patient journey reports these flags but does not use them for eligibility yet (PJ readiness plan C3, C9).

**Existing features unchanged:** NB02 and NB04 keep only eGFR / UACR (`LAB_STAGED_TESTS`) for every existing feature; PJ01 keeps the stage table to eGFR / UACR, so PJ06 eligibility does not change. Tested on toy data (known values, all pass); the real check is the before-vs-after comparison of the `full_2026_11_06` run with `full_2026_11_05`.

---

## 2. What we learned (the evidence behind this plan)

| Topic | Finding | Consequence for NBA 3.1 | Source |
| --- | --- | --- | --- |
| Cohort design (all) | 3.0 built calendar-month rows, hardcoded the start date and filled missing months with a cross join | Cohort windows ending at each cutoff, parameters in `00_cohort_config`, fixed pivot values, one fast all-cohorts engine per notebook | Section 4 |
| NB01 Rx input | The 3.1 HCP Rx pull has the same claims as `Rx_01_new` for the test HCPs (50,739 of 50,739, all 8 feature columns equal) plus 2 newer claims | Switch to the pull (C4); journey rules and HCP features use one basket | NB01 plan 0b |
| NB01 patient table | NB01 read an older root copy of the patient table (F1); production would have joined a calendar-month table on offset-7 months (F4) | Patient tables through `get_patient_table_path()` from the run folder (C1, C2) | NB01 plan 3 |
| NB02 lab input | `Lab_03`: 108.8M rows, 122.9K NPIs since 2023; 3.1 lab pull: 207.5M rows, 199.9K NPIs; tests in both have the same stage | Switch to the pull (C1); test HCPs 240 → 498 test-days | NB02 plan 3 |
| NB03 Dx input | `Dx_03` staged from the description text and misses the stage 3 sub-codes and every stage 5 code: stage 3 12.6K rows vs 65.3M, stage 5 0 vs 115.8M (all US since 2023) | Switch to the 3.1 Dx pull; `STAGE_5` columns added (111 → 120 columns) | NB03 plan 2 |
| NB04 lab input | `Lab_04` has UACR tests for 12.9K patients, the 3.1 lab pull for 16.1M | Switch to the pull (C2) | NB04 plan F3 |
| NB04 patient tables | The old copy had 13,665 stage-0 ("unknown") patient-months for the test HCPs' patients; the run-folder table has none | Run folder (C3); family A always has the full stage grid (C6) | NB04 plan F1, F5 |
| NB04 family C | The 3.1 patient treatment table drops `Other- glucose mgmt` (patient-journey rule), so 9 selected features have no column | Keep the patient-journey rule; drop the 9 features from the model list (X5) | NB04 plan F6, D2 |
| NB05 new starts | A first start needs the claims of every HCP since 2021; the 3.1 pull starts in 2023 and covers the universe only | Keep `kerendia_nba_3_0_Rx_05` (X7); output identical to before | NB05 plan F1–F3 |
| NB06 windows | The 3.0 windows are the mean of N+1 monthly counts; the refactor sums N months (as NB01–NB05) | Keep the sum (X8); parity difference accepted (X9) | NB06 plan F7 |
| HCP universe | 1508230566 is in the 3.0 universe but not in the 3.1 universe | 9 test HCPs in the 3.1 outputs | Decision log X1 |
| Full run memory | The NB01 check cell (fast engine vs step-by-step) loaded 2 full cohorts x about 4,400 columns into the notebook's memory | In full mode the check runs on the trace HCPs only (same fix in NB04) | Section 11 |

---

## 3. The six notebooks and what they do

| Notebook | Folder | What it builds | 3.1 inputs | Outputs (`notebook_output/`) | Columns | Selected features | Plan file |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **NB01 Rx** | `01 Rx Claims Files/` | Rx claims by treatment category, brand, rejection, duration, refill, payer, patient age / gender, patient treatment; AVG family | HCP Rx pull (`_stage/rx_hcp_pull`), `pat_new_and_total_treatments` | `claim_rx_monthly_cohort`, `provider_claim_rx_monthly_cohort` | 3,693 (validation); 4,441 full run | 170 + 2 shared with NB04 | `NBA_3_1_Rx_Claims_Features_Plan.md` |
| **NB02 Lab** | `02 Lab Claims Files/` | Lab tests by test type (GFR, UACR) and stage | Lab pull (`_stage/lab_step4_pull`), eligibility table (lab flags, new) | `claim_lab_monthly_cohort`, `provider_claim_lab_monthly_cohort` | 102 (+48 lab flag columns from the next run) | 0 | `NBA_3_1_Lab_Claims_Features_Plan.md` |
| **NB03 Dx** | `03 Diagnosis Claims Files/` | Dx claims by CKD stage; claims of patients new to a stage | Dx pull (`_stage/dx_step4_pull`), `pat_new_ckd_stage` | `claim_diagnosis_monthly_cohort`, `provider_claim_diagnosis_monthly_cohort` | 120 | 3 | `NBA_3_1_Dx_Claims_Features_Plan.md` |
| **NB04 Combined** | `04 Monthly Cohort Claims Files/` | Rx claims by the patient's GFR / UACR stage (A), same-day lab test (B), stage x treatment (C) | HCP Rx pull, lab pull, `pat_gfr_dx_stage`, `pat_uacr_stage` | `claims_monthly_cohort`, `final_claims_monthly_cohort` | 1,785 (validation); 2,892 full run | 87 + 2 shared with NB01 | `NBA_3_1_Claims_Features_Plan.md` |
| **NB05 New starts** | `05 Rx NPS Claims Files/` | Patients visiting and patients starting a drug class or brand | `kerendia_nba_3_0_Rx_05` (3.0, kept) | `claim_rx_nps_monthly_cohort` (`PROVIDER_ID` level) | 161 | 14 | `NBA_3_1_Rx_NPS_Features_Plan.md` |
| **NB06 Eligible** | `06 Eligible HCP Claims Files/` | Eligible patients (patient journey `ELIGIBLE_PATIENT_FLAG`) by GFR / Dx and UACR stage; dialysis flag | HCP Rx pull (`Rx_01_new` before 2023 for the column list), `sglt2_filter_m`, `px` | `claim_eligible_patient_cohort`, `provider_claim_eligible_patient_cohort` | 76 (+148 diabetes / HF columns from the next run) | 1 | `NBA_3_1_Eligible_HCP_Features_Plan.md` |

**Run order:** the six notebooks do not read each other, so they run in parallel, after a patient-journey run (PJ01–PJ06, with PJ03 Step 4d) has written its run folder.

| Job | ID | Tasks |
| --- | --- | --- |
| NBA 3.1 HCP Level Features (NB01-NB06) | 36449327509782 | NB01–NB06 in parallel |
| NBA 3.1 Patient Journey + HCP Features (PJ01-PJ06 -> NB01-NB06) | 1010893614518587 | PJ01–PJ06, then NB01–NB06 after `pj06_combine` |

Both use the notebooks in `kerendia_nba_3_1_develop_pg` and the parameters `VALIDATION_MODE`, `RUN_OUTPUT_DIR`, `HCP_UNIVERSE_PATH`, `NPI_BHID_MAPPING_PATH`, `RUN_CHECKS`. Defaults = validation run.

---

## 4. Common design (all six notebooks)

### 4.1 What changed from 3.0 to 3.1

| Aspect | NBA 3.0 (original) | NBA 3.1 (cohort-based) |
| --- | --- | --- |
| Time grain | Calendar month (`date_trunc('MM', SVC_DT)` to `SVC_DT_M`) | Daily `SVC_DT` kept; date-range windows ending at each cohort cutoff |
| Output grain | 1 row per (NPI, SVC_DT_M) | 1 row per (NPI, COHORT_ID), partitioned by `COHORT_ID` |
| Lookback windows | `Window.rowsBetween(-i+1, 0)` over monthly rows | `SVC_DT > start AND SVC_DT <= cutoff`, windows 1, 3, 6, 12 months |
| Fill missing months | `step2_fill_missing` (cross join NPI x months) | Not needed. NPI universe = NPIs in the widest window plus NPIs with older history (keeps `RUNNING_` values) |
| AVG features | `step3_lag_avg` (window one month wider) | Two-stage: monthly aggregate, zero-fill, fixed denominator. `AVG_EXTRA_MONTH = True` reproduces 3.0 |
| `RUNNING_` features | Unbounded preceding sum | Kept. All claims from `DATA_START_DATE` up to the cohort cutoff |
| Start-date filter | Hardcoded `SVC_DT_M >= '2022-01-01'` | Cohort config plus team rule `DATA_START_DATE = 2023-01-01` |
| Pivot columns | Values found in the run's data | Fixed pivot values, so every cohort has the same columns (0 when no claims) |
| Inputs | 3.0 queries in `00_Write_Input_Files` (`Rx_01_new`, `Lab_03`, `Lab_04`, `Dx_03`) | NPI-level pulls of the 3.1 patient journey (switch per source) |
| Parameters | Hardcoded | `00_cohort_config` and job parameters |

**How the offset works:** `assign_cohort_month(SVC_DT, offset)`: offset 0 = calendar month; offset 7 = cohort boundaries on the 7th, the 7th starts the new cohort. Cutoff of a cohort = month end (offset 0) or month end + (offset - 1) days (for example the Feb cohort at offset 7 runs up to Mar 6). `COHORT_ID` = `YYYY-MM_offset{N}` (for example `2025-02_offset7`).

### 4.2 Shared configuration (`00_cohort_config`)

| Parameter / helper | Value / role |
| --- | --- |
| `OFFSET_DAY` | 7 |
| `DATA_START_DATE` | 2023-01-01 (no data before this date, `RUNNING_` included) |
| `COHORT_ORIGIN` / `COHORT_LAST` | 2025-01-01 / 2026-10-01; only cohorts with complete data are built: 20 cohorts, 2025-01 .. 2026-08 (common end date of the inputs 2026-09-30) |
| `LOOKBACK_WINDOWS` | [1, 3, 6, 12] |
| `AVG_EXTRA_MONTH` | True (replicates 3.0 `step3_lag_avg`) |
| `VALIDATION_MODE`, `RUN_OUTPUT_DIR`, `HCP_UNIVERSE_PATH`, `NPI_BHID_MAPPING_PATH`, `RUN_CHECKS` | Job parameters. `HCP_UNIVERSE_PATH` falls back to the 3.0 universe when empty |
| `HCP_RX_SOURCE`, `HCP_RX31_PULL_TABLE`, `HCP_RX_TABLE` | `"3.1"` default = HCP Rx pull of the run folder; `"3.0"` = `Rx_01_new` |
| `HCP_LAB_SOURCE`, `HCP_LAB31_PULL_TABLE`, `HCP_LAB_TABLE`, `HCP_CLAIMS_LAB_TABLE` | `"3.1"` default = `full_2026_11_02/_stage/lab_step4_pull`; `"3.0"` = `Lab_03` (NB02) / `Lab_04` (NB04) |
| `HCP_DX_SOURCE`, `HCP_DX31_PULL_TABLE`, `HCP_DX_TABLE` | `"3.1"` default = `full_2026_11_02/_stage/dx_step4_pull`; `"3.0"` = `Dx_03` |
| `get_patient_table_path()` | Patient tables from the patient-journey run folder (`RUN_OUTPUT_DIR`) when present |
| `HCP_SOURCE_TABLES`, `get_hcp_cohort_months()` | Common end date of the inputs, so every HCP table has the same `COHORT_ID`s |
| `HCP_TRACE_NPIS` | Fixed trace HCP per notebook (rx 1386651560, lab 1528629052, dx 1841364841, claims 1386651560) |
| `HCP_BRANDS`, `HCP_NPI_MAPPING_TABLE` | 8 brands; `kerendia_nba_3_0_npi_bhid_mapping` |
| 3.0 reference snapshot | `ops_pipeline_bkp/` (`HCP_REF_*`), used only for the offset-0 parity |

### 4.3 Common notebook structure

1. `%run 00_connection`, then `%run "../../00_cohort_config"`, then a config confirmation
2. Load inputs; apply the NPI filter (validation) and `DATA_START_DATE`
3. Cohort list from `get_hcp_cohort_months()` and `COHORT_BOUNDS`
4. Step-by-step feature functions for one cohort with a preview
5. Fast all-cohorts engine and a check that it equals the step-by-step version (full mode: trace HCPs only)
6. One write of all cohorts: Delta, `partitionBy("COHORT_ID")`, `replaceWhere` on this run's `COHORT_ID`s, `mergeSchema`
7. Completeness checks: expected vs written cohorts, duplicate (NPI, COHORT_ID), null cells
8. NPI to `PROVIDER_ID` mapping and provider-level table
9. Validation: offset-0 parity (validation mode only) and HCP trace

Output metadata columns: `COHORT_ID`, `COHORT_MONTH`, `OFFSET_DAYS`, `CUTOFF_DATE`, `SVC_DT_M` (first day of the cohort month), `PULL_DT`.

### 4.4 Validation approach

| Check | What it does |
| --- | --- |
| Fast engine = step-by-step | Every cell of the first and last cohort, plus column order and types |
| Offset-0 parity | Rebuild every month at offset 0 for the test NPIs from the 3.0 reference inputs and compare with the 3.0 output (tests the feature logic only) |
| HCP trace | Recount raw claims of the trace HCP per cohort and window and compare with the written features |
| Independent recount | Recount from the input outside the engine (pandas or Spark) |
| Completeness | Cohorts expected vs written, duplicates, null cells, provider-level nulls and duplicates |
| Before vs after | Previous output vs new output; every difference explained by the input |

Test NPIs (validation mode): 1396374062, 1508230566, 1801062104, 1386651560, 1528629052, 1659887388, 1215675616, 1467950774, 1235697863, 1841364841 (1508230566 is not in the 3.1 universe).

---

## 5. NB01 Rx claims features

**Notebook:** `01 Rx Claims Files/01_claim_rx_monthly_cohort` (3.0 source `01_claim_rx_monthly`)  
**Inputs:** HCP Rx pull of the 3.1 Rx journey (`<run folder>/_stage/rx_hcp_pull`, PJ03 Step 4d; was `Rx_01_new`), patient table `pat_new_and_total_treatments` (run folder)  
**Outputs:** `claim_rx_monthly_cohort` (NPI x `COHORT_ID`), `provider_claim_rx_monthly_cohort` (`PROVIDER_ID` x `COHORT_ID`)  
**Full plan:** `01 Rx Claims Files/NBA_3_1_Rx_Claims_Features_Plan.md`

### 5.1 What the notebook builds

| Group | Pivot | Prefix |
| --- | --- | --- |
| Total | none (denominator for `PCT_`) | `TOTAL_RX_CLAIMS` |
| 2.1 Treatment category | `TREATMENT_CATEGORY` | `TOTAL_RX_CLAIMS_` |
| 2.2 Brand | `Category` in the 8 `HCP_BRANDS` | `TOTAL_RX_CLAIMS_` |
| 2.3 Rejection | category and brand, `REJECTION_FLAG = 1` | `TOTAL_REJECTED_RX_CLAIMS_` |
| 2.4 Duration | category / brand x days supply bin | `TOTAL_RX_CLAIMS_` |
| 2.5 Refill | brand x `REFILL_FLAG`, `REFILL_FLAG` alone | `TOTAL_RX_CLAIMS_` |
| 2.6 Payer | category / brand / alone x `METHOD_OF_PAYMENT` | `TOTAL_RX_CLAIMS_` |
| 2.7 Patient attributes | category / brand / alone x age bin and gender | `TOTAL_RX_CLAIMS_` |
| 2.8 Patient treatment | number of active / new treatments of the patient that month (the only group that uses the patient journey, 72 columns) | `TOTAL_RX_CLAIMS_PATIENT_WITH_` |
| Derived | `SGLT2_WO_INVOKANA_300MG`, `PCT_`, `_IN_LAST_3_6_MONTH`, `RATIO_..._IN_PRIOR_3_LAST_3_MONTH`, `RUNNING_` | |
| AVG family | `AVG_PATIENT_AGE`, `TOTAL_PATIENT_COUNT`, `AVG_TREATMENT_PER_PATIENT`, `TOTAL_TREATMENT_COUNT` | |

### 5.2 What changed upstream and reaches NB01

| Patient journey change (3.1, Phase A) | Reaches NB01? |
| --- | --- |
| Rx journey drug list and categories from the basket (identical to 3.0) | No change in categories |
| Rx journey 97-day look-back | Yes, through 2.8: more active and fewer new treatments in early 2023 (mainly `RUNNING_`) |
| Combine (PJ06): cohort months at offset 7 | Already handled (join at the cohort's offset) |
| Lab / Dx / Px / flags / eligibility | No |
| Run folders (`RUN_OUTPUT_DIR`) | Yes: NB01 read an older root copy (F1), fixed by C1 |

### 5.3 Findings

| # | Finding |
| --- | --- |
| F1 | NB01 read an outdated root copy of the patient table (2026-10-26, 4,238 patients) instead of the run folder (2026-11-02, 4,431 patients) |
| F2 | The month join is correct at offset 7 (98.7% of the test HCPs' claims find their patient row) |
| F3 | Cohorts stay within the patient table (last cohort 2026-08, cutoff 2026-09-06) |
| F4 | Production would have joined the 3.0 calendar-month patient table on offset-7 months |
| F5 | NB01 keeps `Other- glucose mgmt` (GLP-1, DPP-IV, sulfonylureas), which the Rx journey drops; Kerendia, Mounjaro, Wegovy, Zepbound and generic dapagliflozin are missing in both (Phase B) |
| F6 | The Part 4 status cell was out of date |

### 5.4 Changes

| ID | Change |
| --- | --- |
| C1 | Patient table from the run folder through `get_patient_table_path()` |
| C2 | Same rule in production: the job's `RUN_OUTPUT_DIR` decides |
| C3 | Documentation (header, Part 4 status) |
| C4 | Rx input = HCP Rx pull of the 3.1 Rx journey (new PJ03 Step 4d) |
| C5 | Fixed pivot values also from the 3.0 `Rx_01_new` history, so the 3.0 column set is kept (144 combinations seen only before 2023) |
| C6 (2026-11-04) | Memory fix for the full run: the fast-engine check and the final table preview use the trace HCPs only in full mode |

**PJ03 Step 4d (HCP Rx pull)** uses the same tables, basket, dates, HCP universe and drop rules as the Rx journey, plus: rejection, refill, payer, birth year and gender columns (H1); the view's `Other- glucose mgmt` products with GLP-1 / DPP-IV labels (H2, user decision 2026-11-03); brand label `SPIRONOLACTONE-MRA` (H3); one row per 3.0 claim key (H4); empty days supply kept and no look-back (H5).

### 5.5 Validation results (test HCPs, 2026-11-03)

| Check | Result |
| --- | --- |
| Pull vs `Rx_01_new` (9 test HCPs) | 50,739 of 50,739 claims with all 8 feature columns equal; 2 newer claims in the pull |
| Fast engine = step-by-step | PASS: 2 x 33,219 cells, 0 mismatches |
| Write | 20 cohorts, 180 rows, 3,693 columns, 0 duplicates, 0 null cells |
| HCP trace (1386651560) | 2,100 checks, 0 mismatches |
| Own recount from the pull (GLP-1, DPP-IV, spironolactone, other glucose) | 2,880 checks, 0 mismatches |
| Offset-0 parity vs 3.0 `claim_rx_monthly` | PASS: 700,150 cells, 0 mismatches (19 known-quirk cells of 3.0) |
| Before (3.0 input) vs after (3.1 input) | 1,731 of 663,480 cells differ, all for NPI 1659887388 (the newer Ozempic claim) |

### 5.6 Decisions

| ID | Question | Decision |
| --- | --- | --- |
| D1 / D2 | Patient table in validation / full run | Run folder of the patient-journey run (`RUN_OUTPUT_DIR`) |
| D3 | Align categories with the patient journey? | Keep GLP-1 / DPP-IV for NB01 (user, 2026-11-03); revisit with Rx journey Phase B |
| D4 | Kerendia / new GLP-1 drugs | Phase B (a basket change now reaches NB01 through the pull) |
| D5 | Full run of the HCP Rx pull | Done 2026-11-03 (section 11) |
| D6 | Remove the C5 dependency on `Rx_01_new` | Later: fixed column list once the feature list is final |

---

## 6. NB02 Lab claims features

**Notebook:** `02 Lab Claims Files/02_claim_lab_monthly_cohort` (3.0 source `02_claim_lab_monthly`)  
**Input:** lab pull of the 3.1 lab journey (`full_2026_11_02/_stage/lab_step4_pull`, PJ01 Step 4; was `Lab_03`)  
**Outputs:** `claim_lab_monthly_cohort`, `provider_claim_lab_monthly_cohort`  
**Full plan:** `02 Lab Claims Files/NBA_3_1_Lab_Claims_Features_Plan.md`

### 6.1 What the notebook builds

Per window: lab tests by `TEST_TYPE` (GFR, UACR), by stage (5 eGFR stages + A1/A2/A3) and total; `RUNNING_`; `PCT_`. 102 columns.

### 6.2 What reaches NB02 from the 3.1 lab journey

Before, NB02 read no patient-journey data (`Lab_03` is a 3.0 query). The lab pull has the same grain as `Lab_03` (NPI x patient x day x test), so reading it brings every 3.1 lab rule at once: tests from the lab basket (LOINC + name backup), eGFR valid range 1–200, UACR 0–10,000, UACR components never staged, preferred eGFR equation on the same day, results such as `>90` / `75^` kept. Same 10 primary-care specialty codes (lab journey decision L1 open).

### 6.3 Findings

| # | Finding |
| --- | --- |
| F1 | `Lab_03` holds far fewer tests than the lab journey, already in 3.0: 108.8M rows / 122.9K NPIs vs 207.5M / 199.9K in the pull (since 2023) |
| F2 | Tests counted in both have the same stage (UACR 367,633 of 367,633; eGFR 1,983,797 of 1,984,267, 2025-06 all US) |
| F3 | The pull replaces `Lab_03` without other code changes (stages mapped to the `Lab_03` texts, same column names) |
| F4 | Header cells described 3.0 |
| F5 | Test HCPs: 240 → 498 test-days, 7 → 9 NPIs with lab features, same 102 columns |

### 6.4 Changes

| ID | Change |
| --- | --- |
| C1 | Read the 3.1 lab pull (`load_lab_input()`), stage numbers mapped to the `Lab_03` texts; stop if a row has no stage |
| C2 | Config switch `HCP_LAB_SOURCE`, `HCP_LAB31_PULL_TABLE`, `HCP_LAB_TABLE`; common end date uses `HCP_LAB_TABLE` |
| C3 | Documentation |

### 6.5 Validation results (test HCPs, 2026-11-03)

| Check | Result |
| --- | --- |
| Fast engine = step-by-step | PASS: 2 x 900 cells, 0 mismatches |
| Write | 20 cohorts, 180 rows, 102 columns, 0 duplicates, 0 null cells |
| HCP trace (1528629052) | 900 checks, 0 mismatches |
| Independent recount from the pull | 3,060 checks, 0 mismatches |
| Offset-0 parity vs 3.0 `claim_lab_monthly_ZS` | PASS: 0 mismatches |

### 6.6 Decisions

| ID | Question | Decision |
| --- | --- | --- |
| D1 | Lab input | 3.1 lab pull (user, 2026-11-03) |
| D2 | Where the pull lives | Keep it in the run folder (X3); do not delete `full_2026_11_02/_stage/lab_step4_pull` |
| D3 | Specialty filter and universe | 3.1 universe (X1); specialty filter follows lab journey L1 |
| D4 | `Lab_04` (NB04) | Also switched to the pull (NB04 C2) |

---

## 7. NB03 Diagnosis claims features

**Notebook:** `03 Diagnosis Claims Files/03_claim_diagnosis_monthly_cohort` (3.0 source `03_claim_diagnosis_monthly`)  
**Inputs:** Dx pull of the 3.1 Dx journey (`full_2026_11_02/_stage/dx_step4_pull`, PJ02 Step 4; was `Dx_03`), patient table `pat_new_ckd_stage` (run folder)  
**Outputs:** `claim_diagnosis_monthly_cohort`, `provider_claim_diagnosis_monthly_cohort`  
**Full plan:** `03 Diagnosis Claims Files/NBA_3_1_Dx_Claims_Features_Plan.md`

### 7.1 What the notebook builds

Dx claims by CKD stage (`TOTAL_DX_CLAIMS_STAGE_*`), claims of patients new to a stage that month (`TOTAL_DX_CLAIMS_WITH_PATIENT_*`), total, `RUNNING_`, `PCT_`.

### 7.2 Findings

| # | Finding |
| --- | --- |
| F1 | `Dx_03` stages from the description text and misses N18.30–N18.32, N18.5, N18.6, I12.0, I13.11, I13.2 and E10.21/22/29: stage 3 12.6K rows vs 65.3M in the pull, stage 5 0 vs 115.8M (all US since 2023); no `STAGE_5` columns |
| F2 | The 3.1 Dx journey has an NPI-level pull with the 3.1 rules (31 CKD basket codes, stage by code) |
| F3 | Test HCPs: 6,815 → 8,991 rows; stage 3 / 5 rows 0 / 0 → 1,604 / 2,429; no day goes down in stage |
| F4 | Patient-stage table read from an old root copy (with it, the test HCPs had no claims of patients new to stage 3 or 5) |
| F5 | Trace HCP 1508230566 has no rows in the pull (not in the 3.1 universe) |

### 7.3 Changes

| ID | Change |
| --- | --- |
| C1 | Dx input = 3.1 Dx pull (`load_dx_input()`), null-stage assert |
| C2 | Config switch `HCP_DX_SOURCE`, `HCP_DX31_PULL_TABLE`, `HCP_DX_TABLE` |
| C3 | Fixed stage pivot values `STAGE_1..STAGE_5, STAGE_UNSPECIFIED`: adds the `STAGE_5` columns |
| C4 | Patient-stage table through `get_patient_table_path()` |
| C5 | Trace HCP = 1841364841 |
| C6 | Documentation |

### 7.4 Validation results (test HCPs, 2026-11-03)

| Check | Result |
| --- | --- |
| Fast engine = step-by-step | PASS: 2 x 1,062 cells, 0 mismatches |
| Write | 20 cohorts, 180 rows, 120 columns (+9 `STAGE_5`), 0 duplicates, 0 null cells |
| HCP trace (1841364841) | 1,300 checks, 0 mismatches |
| Independent recount (pull + patient table) | 16,020 checks, 0 mismatches |
| Offset-0 parity vs 3.0 `provider_claim_diagnosis_monthly` | PASS: 0 mismatching cells |
| Before vs after, last cohort, 12 months | Dx claims 1,753 → 3,210; stage 3 / 5: 0 / – → 501 / 1,034 |

The 3 selected NB03 features change: `STAGE_UNSPECIFIED_IN_LAST_3_MONTH` in 62 of 160 HCP-cohorts; `WITH_PATIENT_NO_NEW_STAGE_IN_LAST_6 / 12_MONTH` in 135 / 148 of 160.

### 7.5 Decisions

| ID | Question | Decision |
| --- | --- | --- |
| D1 | Dx input | 3.1 Dx pull (switch back with `HCP_DX_SOURCE = "3.0"`) |
| D2 | Pull location | Keep in the run folder (as X3) |
| D3 | HCP universe | 3.1 (X1) |
| D4 | `STAGE_5` columns | Keep (X4); none of the selected features is a `STAGE_5` column |
| D5 | T1D kidney codes E10.21/22/29 counted as Dx claims (stage unspecified) | **Open** |

---

## 8. NB04 Combined claims features

**Notebook:** `04 Monthly Cohort Claims Files/04_claims_monthly_cohort` (3.0 source `04_claims_monthly`)  
**Inputs:** HCP Rx pull, lab pull, patient tables `pat_gfr_dx_stage` and `pat_uacr_stage` (run folder)  
**Outputs:** `claims_monthly_cohort`, `final_claims_monthly_cohort`  
**Full plan:** `04 Monthly Cohort Claims Files/NBA_3_1_Claims_Features_Plan.md`

### 8.1 What the notebook builds

Every Rx claim of an HCP, split by what was known about the patient's kidneys at that time:

| Family | Question | Joined table | Prefix |
| --- | --- | --- | --- |
| A | GFR / UACR stage of the patient that month | `pat_gfr_dx_stage` | `TOTAL_RX_CLAIMS_PATIENT_WITH_GFR_...` |
| B | Same-day GFR / UACR lab test and its stage | lab pull (was `Lab_04`) | `TOTAL_RX_CLAIMS_PATIENT_WITH_TEST_...` |
| C | Treatments of the patient that month, by stage | `pat_uacr_stage` | `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_...` |

### 8.2 Inputs before and after

| Input | 3.0 / before | 3.1 / now |
| --- | --- | --- |
| Rx claims | `Rx_01_new` | HCP Rx pull (as NB01) |
| Same-day lab tests (B) | `Lab_04` | 3.1 lab pull (`HCP_CLAIMS_LAB_TABLE`) |
| Patient stage (A) and stage x treatment (C) | Root copies of 2026-10-26 | Run folder |
| `Dx_03` | Read, never used | Not read |

### 8.3 Findings

| # | Finding |
| --- | --- |
| F1 | Patient tables read from an old copy with 13,665 stage-0 patient-months for the test HCPs' patients (run folder: none, 8,991 at stage 3) |
| F2 | Rx input was 3.0 `Rx_01_new` (same claims as the pull) |
| F3 | `Lab_04` has UACR tests for 12.9K patients, the pull for 16.1M; tests in both have the same stage |
| F4 | The pull starts at `DATA_START_DATE`; the column list needs the older history |
| F5 | 27 family-A columns (`GFR_STAGE_UNKNOWN_AND_UACR_STAGE_*`) only came from the stage-0 months |
| F6 | Family C has no DPP-IV / other-glucose columns (patient-journey rule): 9 of the 89 selected NB04 features; 7 `..._WITH_GLP_1` features absent for the test HCPs only |

### 8.4 Changes

| ID | Change |
| --- | --- |
| C1 | Rx input = `HCP_RX_TABLE` |
| C2 | Lab input = 3.1 lab pull, stages mapped to the `Lab_04` texts |
| C3 | Patient tables through `get_patient_table_path()` |
| C4 | 3.0 rows before `DATA_START_DATE` used for the column list only |
| C5 | `Dx_03` not read |
| C6 | Family A always has the full stage grid (F5 columns back, as 0) |
| C7 | `%run` path and documentation |
| C8 (2026-11-04) | Memory fix for the full run: the fast-engine check uses the trace HCPs only in full mode |

### 8.5 Validation results (test HCPs, 2026-11-03)

| Check | Result |
| --- | --- |
| Fast engine = step-by-step | PASS: 2 x 16,047 cells, 0 mismatches |
| Write | 20 cohorts, 180 rows, 1,785 columns, 0 duplicates, 0 null cells |
| HCP trace (1386651560) | 19,800 checks, 0 mismatches |
| Own recount (last cohort, 12 months) | Total, family A and family B: 0 mismatches |
| Offset-0 parity vs 3.0 `final_claims_monthly` | PASS: 0 mismatches |
| Before vs now | Family A claims with a known GFR stage 770 → 2,502 (stage 3 / 5: 37 / 7 → 1,765 / 216); columns 1,560 → 1,785 |

### 8.6 Decisions

| ID | Question | Decision |
| --- | --- | --- |
| D1 | 3.1 Rx and lab pulls | Applied (switch back with `HCP_RX_SOURCE` / `HCP_LAB_SOURCE = "3.0"`) |
| D2 | Family C without DPP-IV / other glucose | Keep the patient-journey rule; drop the 9 features from the model list (X5) |
| D3 | HCP universe | 3.1 (X1) |
| D4 | Lab pull location | Run folder (X3) |
| X6 | 7 `..._WITH_GLP_1` features | No change; **check in the full output** |

---

## 9. NB05 New patient starts features

**Notebook:** `05 Rx NPS Claims Files/05_claim_rx_nps_monthly_cohort` (3.0 source `05_claim_rx_nps_monthly`)  
**Input:** `kerendia_nba_3_0_Rx_05` (3.0, kept)  
**Output:** `claim_rx_nps_monthly_cohort` (`PROVIDER_ID` x `COHORT_ID`)  
**Full plan:** `05 Rx NPS Claims Files/NBA_3_1_Rx_NPS_Features_Plan.md`

### 9.1 What the notebook builds

Per HCP: patients visiting (`TOTAL_PATIENTS_VISIT`) and patients who started a drug class or brand with that HCP (`TOTAL_PATIENTS_START_*`, `TOTAL_NEW_PATIENT_START`). A start = the patient's first claim of the class / brand in the whole table, by any HCP. Windows, `RUNNING_`, `PCT_` (starts / visits).

### 9.2 Findings

| # | Finding |
| --- | --- |
| F1 | `Rx_05` = Rx claims of every HCP since 2021-01-02 (4.03B rows); a start needs that history |
| F2 | The 3.1 HCP Rx pull cannot replace it (starts 2023, universe HCPs only) |
| F3 | Same claims for the counted HCPs (49,140 keys in both; 2 newer in the pull) |
| F4 | `%run` path after the move |
| F5 | All 14 selected NB05 features are in the output |

**Changes:** C1 `%run` path; C2 comment on why `Rx_05` stays. Input, logic and columns unchanged.

### 9.3 Validation results (test HCPs, 2026-11-03)

| Check | Result |
| --- | --- |
| Fast engine = step-by-step | PASS: 2 x 1,431 cells, 0 mismatches |
| Write | 20 cohorts, 180 rows, 161 columns, 0 duplicates, 0 null cells |
| HCP trace | 3,080 checks, 0 mismatches |
| Offset-0 parity vs 3.0 | PASS: 35,720 cells, 0 mismatches |
| Own recount of starts | 0 mismatches |
| Before vs now | Identical (0 of 27,720 cells) |

### 9.4 Decisions

| ID | Question | Decision |
| --- | --- | --- |
| D1 / X7 | Keep `Rx_05` | Yes; revisit when new drugs join the basket (Phase B needs an all-HCP basket input from 2021) |
| D2 | HCP universe | NB05 counts the HCPs of `Rx_05`; the model joins on the HCP list of the run |

---

## 10. NB06 Eligible patient features

**Notebook:** `06 Eligible HCP Claims Files/06_claim_eligible_hcp` (3.0 source `06_claim_eligible_hcp`)  
**Inputs:** HCP Rx pull (`Rx_01_new` before `DATA_START_DATE` for the column list), patient tables `sglt2_filter_m` (eligibility) and `px` (first dialysis date), run folder  
**Outputs:** `claim_eligible_patient_cohort`, `provider_claim_eligible_patient_cohort`  
**Full plan:** `06 Eligible HCP Claims Files/NBA_3_1_Eligible_HCP_Features_Plan.md`

### 10.1 What the notebook builds

Per HCP: patients with an Rx claim who were eligible that month (`ELIGIBLE_PATIENT_FLAG = 1`), total and by GFR / Dx stage and UACR stage; windows, `RUNNING_`, `PCT_`; `DIALYSIS_FLAG` for the cohort month. 76 columns.

### 10.2 Findings

| # | Finding |
| --- | --- |
| F1 | Patient tables already read from the run folder (3.1 eligibility reaches NB06 directly) |
| F2 | Rx input was 3.0 `Rx_01_new` (29,973 of 29,973 keys also in the pull) |
| F3 | Only the 7 fixed stage columns of 3.0 occur; no new column |
| F4 | New 3.1 columns (`HF_FLAG`, `DM_TYPE`) not used yet (no new columns, D3) |
| F5 | `%run` path after the move |
| F6 | 1 selected feature (`RUNNING_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_4`), present |
| F7 | 3.0 windows are the mean of N+1 monthly counts; the refactor sums N months |

**Changes:** C1 `%run` path; C2 Rx input = `HCP_RX_TABLE` from `DATA_START_DATE` + `Rx_01_new` before; C3 docs; C4 absolute path for the pull.

### 10.3 Validation results (test HCPs, 2026-11-03)

| Check | Result |
| --- | --- |
| Fast engine = step-by-step | PASS |
| Write | 20 cohorts, 180 rows, 76 columns, 0 duplicates, 0 null cells |
| HCP trace (1386651560) | 820 checks, 0 mismatches |
| Own recount (last cohort, 12 months) | Total 7,479, per stage equal to the output |
| Offset-0 parity vs 3.0 | FAIL on window columns only (6,264 cells), explained by F7; base-month counts 0 of 171 mismatches; accepted (X9) |

### 10.4 Decisions

| ID | Question | Decision |
| --- | --- | --- |
| D1 / X8 | Window = sum of N months or mean of N+1 months | Sum (same rule as NB01–NB05) |
| D2–D3 | Dialysis month, no new columns | Applied |
| D4 | Patient-journey decisions C1 (SGLT2) and C9 (diabetes) | Change `ELIGIBLE_PATIENT_FLAG` only; NB06 needs a re-run, no code change |
| D5 | HCP universe | 3.1 (X1) |

---

## 11. Full HCP universe run

### 11.1 Inputs (run folder `full_2026_11_02/`)

| Input | Run | Content |
| --- | --- | --- |
| Patient tables (PJ01–PJ06) | Job 953988155823642, run 1066154679479482 (2026-11-02), `HCP_UNIVERSE_PATH` = 3.1 universe | Checked 2026-11-04: of the 1,482,453 providers dropped as "not in the HCP universe" in `_stage/rx_fills_tagged`, 0 are in the 3.1 universe |
| HCP Rx pull (PJ03 Step 4d) | One-time run 114072068089102 (2026-11-03, 41 min) | `_stage/rx_hcp_pull`: 3,070,618,084 claims, 294,534 NPIs, 2023-01-01 .. 2026-09-30 |
| Lab and Dx pulls | Full patient-journey run | `_stage/lab_step4_pull`, `_stage/dx_step4_pull` |

The validation patient-journey run (431087115996928) left `HCP_UNIVERSE_PATH` empty, so it used the 3.0 universe (config default). This explains why the test-HCP values of the validation and full runs differ (for example NB06).

### 11.2 Full run and checks (summary)

Full detail (runs, tables, checks, findings): `Alignment_Markdowns/Review_and_Findings/NBA_3_1_HCP_Features_E2E_Full_Run_2026_11_04.md`.

* **Runs:** HCP job 36449327509782, run 361860399857197 (NB02, NB03, NB05, NB06) and re-run 1050221322333806 (NB01 198 min, NB04 195 min) after the out-of-memory fix (engine check on the trace HCPs only in full mode).
* **Outputs:** all six written, 20 cohorts, 0 duplicate keys and 0 empty cells in the NPI-level tables (NB01 / NB04: 5,830,945 rows, 294,503 NPIs).
* **Selected features:** 268 of 277 present; the 9 missing are X5. The 7 GLP-1 features (X6) are populated.
* **Recounts from the full inputs:** NB01 8,621 checks, NB04 96,300 checks (3 trace HCPs, every cohort), NB06 8 test HCPs: 0 differences.
* **Columns (O3, explained):** NB01 4,441 / NB04 2,892 instead of 3,693 / 1,785, because the columns come from the values in the data (gender "U", empty days supply, young or negative ages, more stage x drug combinations). No validation column lost, no selected feature among the extra ones.
* **Provider tables (O2, open):** the mapping table `kerendia_nba_3_0_npi_bhid_mapping` (agreed BHID-NPI mapping, correct for all other HCPs) misses 105 HCPs (NB01 / NB04; 38 NB03, 101 NB06) and gives 52 HCPs two `PROVIDER_ID`s. The 3.1 inputs have one `PROVIDER_ID` per HCP, all in the 3.1 universe. Proposal: keep the mapping table and fill / de-duplicate only these HCPs from the 3.1 input.

---

## 12. Decisions taken

### 12.1 Cross-notebook decisions (decision log)

| ID | Notebook | Decision | To reverse |
| --- | --- | --- | --- |
| X1 | All | 3.1 HCP universe (`HCP_Universe_without_call_hcps/`), same as the patient journey | Job parameter `HCP_UNIVERSE_PATH` |
| X2 | NB01, NB04, NB06 | 3.1 HCP Rx pull (PJ03 Step 4d) from `DATA_START_DATE`, `Rx_01_new` before | `HCP_RX_SOURCE = "3.0"` |
| X3 | NB02, NB04 | Lab pull kept in the run folder | `HCP_LAB_SOURCE = "3.0"` |
| X4 | NB03 | Keep the stage 5 columns | Column list in NB03 |
| X5 | NB04 | Keep the patient-journey rule; drop the 9 DPP-IV / other-glucose features from the model list | Keep `Other- glucose mgmt` in PJ06 and rerun PJ06 + NB04 |
| X6 | NB04 | 7 `..._WITH_GLP_1` features: no change. **Closed:** present and populated in the full run | – |
| X7 | NB05 | Keep 3.0 `Rx_05` for first starts | Revisit with new drugs |
| X8 | NB06 | Windows = sum of the last N monthly counts | Average in NB06's window step |
| X9 | NB06 | Accept the 6,264 parity differences (explained by X8) | – |
| X10 | All | One folder per run (`RUN_OUTPUT_DIR`) | Job parameter |
| X11 | All | One job for NB01–NB06 in parallel | – |
| X12 | Config | `HCP_CLAIMS_LAB_TABLE` not added to `HCP_SOURCE_TABLES` now | – |

### 12.2 Per-notebook decisions (summary)

| Notebook | Decided | Open |
| --- | --- | --- |
| NB01 Rx | D1–D3, D5 | D4 (new drugs, Phase B), D6 (fixed column list) |
| NB02 Lab | D1–D4 | Lab journey L1 (specialty filter) |
| NB03 Dx | D1–D4 | D5 (T1D kidney codes) |
| NB04 Combined | D1–D4, X6 (closed) | – |
| NB05 New starts | D1–D2 | Phase B input for new drugs |
| NB06 Eligible | D1–D5 | Re-run after patient-journey C1 / C9 |

---

## 13. Data readiness

| Data | Source | Coverage | Status | Gap / action | Owner |
| --- | --- | --- | --- | --- | --- |
| HCP Rx pull | `full_2026_11_02/_stage/rx_hcp_pull` (PJ03 Step 4d) | 3.07B claims, 294,534 NPIs, 2023-01 .. 2026-09 | **Ready** | Lives in `_stage/` (do not delete) | NBA team |
| Lab pull | `full_2026_11_02/_stage/lab_step4_pull` (PJ01 Step 4) | 207.5M rows, 199.9K NPIs since 2023 | **Ready** | Lives in `_stage/` (X3) | NBA team |
| Dx pull | `full_2026_11_02/_stage/dx_step4_pull` (PJ02 Step 4) | 473.1M rows, 283.3K NPIs since 2023 | **Ready** | Lives in `_stage/` | NBA team |
| New-start input | `kerendia_nba_3_0_Rx_05` (3.0) | 4.03B rows, 2021-01-02 .. 2026-09-30 | **Ready** | Phase B: basket-based all-HCP input for new drugs | NBA team |
| `Rx_01_new` (column list before 2023) | 3.0 query output | NB01, NB04, NB06 | **Ready** | D6: replace with a fixed column list | NBA team |
| Patient tables | `full_2026_11_02/` (PJ01–PJ06, 3.1 universe) | Full universe | **Ready (Phase A)** | Re-run HCP notebooks after patient-journey C1 / C9 | Patient-journey owners |
| HCP universe (3.1) | `HCP_Universe_without_call_hcps` (Parquet) | 294,727 providers | **Ready** | Config default is still the 3.0 universe when the parameter is empty | NBA team |
| NPI to provider mapping | `kerendia_nba_3_0_npi_bhid_mapping` (agreed BHID-NPI mapping) | 1.57M NPIs; same ID as the 3.1 Rx input for all but 1 mapped HCP; misses 105 HCPs, 2 IDs for 52 HCPs | **Ready, with gaps (open)** | Fill / de-duplicate the 157 HCPs from the 3.1 input (O2, section 11.2) | NBA team |
| 3.0 reference snapshot | `ops_pipeline_bkp/` | Test HCPs | **Ready** | Parity only | NBA team |

---

## 14. Work plan

| Phase | Content | Main tasks | Status | Depends on |
| --- | --- | --- | --- | --- |
| **0. Build and validate** | NB01–NB06 synced with the 3.1 patient journey and validated on the test HCPs | Inputs switched to the 3.1 pulls, patient tables from the run folder, plans, client summaries, decision log, jobs | **Done** (2026-11-03) | Patient journey Phase A |
| **1. Full run** | All six notebooks written for the full universe, outputs checked | NB01 / NB04 re-run; output checks (duplicates, nulls, selected features, trace HCP recount); empty `PROVIDER_ID` rows | **Done** (2026-11-04); `PROVIDER_ID` mapping change open (O2) | Phase 0 |
| **2. Decisions and reviews** | Settle the open points that change values | Patient-journey C1 / C9 / C3 then re-run; NB03 D5; `RUNNING_` meaning; `SGLT2_WO_INVOKANA_300MG` family; NB05 null vs 0 | **In progress** | Phase 1 |
| **3. New features (Phase B)** | Follow the patient-journey Phase B | New drugs (Kerendia, Mounjaro, Wegovy, Zepbound, generic dapagliflozin) through the basket; NB05 input for their starts; `HF_FLAG` / `DM_TYPE` features | **Not started** | Patient journey Phase B |
| **4. Go-live** | HCP features feed the model | Downstream combine (`99_Combine_Physician_Data`) wired to `COHORT_ID`; feature list updated (X5) and model retrained; production paths; commit | **Not started** | Phases 1–2 |

---

## 15. Readiness gates

| Gate | Ready when | Status |
| --- | --- | --- |
| G0 | All six notebooks synced and validated on the test HCPs; plans, client summaries and decision log written | **Done** (2026-11-03) |
| G1 | All six written for the full universe; completeness checks pass (20 cohorts, 0 duplicates, 0 null cells); selected features present; trace HCP recount passes | **Done** (2026-11-04), except the provider-table mapping (O2) |
| G2 | Patient-journey decisions (C1, C9, C3) settled and HCP notebooks re-run; HCP open points (section 16) closed | Not started |
| G3 | Downstream combine wired; 3.1 feature list final (X5); model retrained on the 3.1 output | Not started |
| **G4 (freeze)** | Production paths, named pulls, old copies cleaned up, all changes committed | Not started |

---

## 16. Open points

| # | Point | Status | Effect |
| --- | --- | --- | --- |
| O1 | NB01 / NB04 full re-run (run 1050221322333806) | **Done** (2026-11-04) | – |
| O2 | Provider tables: empty `PROVIDER_ID` (1,911 NB01 / NB04, 698 NB03, 1,828 NB06) and HCPs written twice (52 / 43 / 52; 27 in NB02) | **Open (explained):** gaps of the agreed mapping table; proposal = keep it, fill / de-duplicate the 157 HCPs from the 3.1 input | Provider tables only; NPI-level tables not affected |
| O3 | NB01 4,441 / NB04 2,892 columns at full scale vs 3,693 / 1,785 in validation | **Explained:** rare values seen only with all HCPs; no selected feature among them | Column list depends on the run (D6) |
| O4 | 7 `..._WITH_GLP_1` features (X6) | **Closed:** present and populated | – |
| O5 | Pulls live in `_stage/` of the run folder | Open | Must not be deleted before the next run |
| O6 | `HCP_UNIVERSE_PATH` falls back to the 3.0 universe when empty | Proposal: default to the 3.1 path | A validation run can silently use 3.0 |
| O7 | `99_Combine_Physician_Data` joins on `SVC_DT_M`; 3.1 outputs are keyed by `COHORT_ID` | Open | Downstream not wired |
| O8 | `RUNNING_` meaning (from `DATA_START_DATE`) | Open, confirm with Wenjie | Differs from 3.0 for history before 2023 |
| O9 | `SGLT2_WO_INVOKANA_300MG` family (187 columns, r about 1.0 with SGLT2) | Awaiting decision (analysis recommendation R5 = drop) | Redundant columns |
| O10 | NB05: months without claims are 0 in 3.1, null in 3.0 | Confirm 0 | Small value differences vs 3.0 |
| O11 | NB03 D5: T1D kidney codes counted as Dx claims | Open | 1.39M rows all US |
| O12 | Patient-journey C1 (SGLT2 rule) and C9 (diabetes) | Open (patient-journey owners) | NB06 eligibility and the patient tables of NB01, NB03, NB04 change; re-run, no code change |
| O13 | Commit of the HCP work | **Done:** `2d978d1` (2026-11-04); the full-run documentation of 2026-11-04 is not committed yet | – |
| O14 | HCP notebooks outside this folder (the combine step) still use `00_step23_function` (3.0 logic) | Open | Refactor or confirm they stay on 3.0 logic |

---

## 17. Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| NB01 / NB04 run out of memory again | Full outputs missing for the two widest notebooks (most selected features) | Fix applied and passed (re-run 1050221322333806); if it fails again, write per cohort group |
| Patient-journey C1 / C9 change eligibility | NB06 and patient-based columns of NB01, NB03, NB04 change | Re-run the HCP job after the patient-journey re-run (one job: 1010893614518587) |
| Pulls deleted from `_stage/` | HCP notebooks cannot run | Keep until they are named outputs of every run |
| 3.0 universe used by mistake | Different HCP and patient set | Pass `HCP_UNIVERSE_PATH` in every run; change the default (O6) |
| Dropped model features (X5) | 9 selected NB04 features missing | Rerun the feature selection on the 3.1 output |
| Empty / repeated `PROVIDER_ID` rows | Repeated provider keys downstream | Fill / de-duplicate the 157 HCPs from the 3.1 input (O2) before the combine step |

---

## 18. Next actions

| # | Action | Owner |
| --- | --- | --- |
| 1 | ~~Check all six full outputs~~ (done 2026-11-04, E2E file) | Patricio |
| 2 | Decide the `PROVIDER_ID` gap fill (O2, open): keep the mapping table, fill / de-duplicate 157 HCPs from the 3.1 input; re-write the provider tables | NBA team, Patricio |
| 3 | ~~Check the 7 `..._WITH_GLP_1` features (X6)~~ (done) | Patricio |
| 4 | Review this plan with the NBA team | NBA team |
| 5 | Decide NB03 D5, `RUNNING_` meaning, `SGLT2_WO_INVOKANA_300MG`, NB05 null vs 0 | NBA team, Wenjie |
| 6 | Re-run the HCP job after the patient-journey decisions C1 / C9 | NBA team |
| 7 | Wire the cohort outputs into `99_Combine_Physician_Data` | NBA team |
| 8 | Commit and push the full-run documentation (when asked) | Patricio |

---

## 19. References

* `01 Rx Claims Files/NBA_3_1_Rx_Claims_Features_Plan.md` and `..._Client_Summary.md`: NB01
* `02 Lab Claims Files/NBA_3_1_Lab_Claims_Features_Plan.md` and `..._Client_Summary.md`: NB02
* `03 Diagnosis Claims Files/NBA_3_1_Dx_Claims_Features_Plan.md` and `..._Client_Summary.md`: NB03
* `04 Monthly Cohort Claims Files/NBA_3_1_Claims_Features_Plan.md` and `..._Client_Summary.md`: NB04
* `05 Rx NPS Claims Files/NBA_3_1_Rx_NPS_Features_Plan.md` and `..._Client_Summary.md`: NB05
* `06 Eligible HCP Claims Files/NBA_3_1_Eligible_HCP_Features_Plan.md` and `..._Client_Summary.md`: NB06
* `NBA_3_1_HCP_Features_Decisions.md`: decision log (X1–X12), jobs
* `Alignment_Markdowns/Review_and_Findings/NBA_3_1_HCP_Features_E2E_Full_Run_2026_11_04.md`: full run, checks and findings
* `../00_cohort_config`: shared configuration
* `../Patient_Journey_Validation/Alignment_Markdowns/Strategy and Execution/AI_Readiness_Plan.md`: patient journey readiness plan
* `Feature Analysis/NBA_3_1_HCP_Claims_Selected_Features_277.csv`: selected features
* 3.0 pipeline: `kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`
* Feature analysis docs: `kerendia_nba_3_1_develop/NBA 3.1 - Dev/Feature Analysis/NBA_3_1_HCP_Claims_Features_Analysis.md` and `..._Recommendations.md`
* Patient features readiness plan: `03_patient_features/NBA_3_1_Patient_Features_AI_Readiness_Plan.md`
