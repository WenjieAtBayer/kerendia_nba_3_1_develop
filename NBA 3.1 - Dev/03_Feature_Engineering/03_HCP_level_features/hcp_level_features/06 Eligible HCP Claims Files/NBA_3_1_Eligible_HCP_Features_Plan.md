# NBA 3.1 – HCP eligible patient features (NB06): sync with the 3.1 patient journey, analysis and plan

> **Update 2026-11-11.** This plan describes the Phase A sync (2026-11-03). Since then: 28 cohorts c1–c28 at offset 0 (claims cohort file, X13), Delta by COHORT_SET (X14), DM/HF type features added (+128 DM/HF type + 20 HF eligibility = +148, X20), old stage breakdowns dropped (−15). Feature count: 84 → 217 (net +133). Total columns = 226. D3 ("no new columns yet") is now **done**. See `NBA_3_1_HCP_Features_Decisions.md`.

**Status (2026-11-03):** C1–C4 applied; validation run done (one-time job run 584967146244150 on cluster `1103-195306-9x8evoxv-v2n`, 7.6 min, section 5). All checks pass except the offset-0 parity, which fails on the window columns only: the 3.0 notebook averages the windows, the refactor sums them (F7; D1 decided 2026-11-03: keep the sum). Client summary: `06 Eligible HCP Claims Files/NBA_3_1_Eligible_HCP_Features_Client_Summary.md`.  
**Notebook:** `hcp_level_features/06 Eligible HCP Claims Files/06_claim_eligible_hcp` (3.0 source `06_claim_eligible_hcp`)  
**Outputs:** `notebook_output/claim_eligible_patient_cohort` (NPI x `COHORT_ID`) and `provider_claim_eligible_patient_cohort` (`PROVIDER_ID` x `COHORT_ID`); written 2026-11-03 (180 rows each)  
**What it builds:** per HCP, the patients with an Rx claim who were eligible for Kerendia that month (`ELIGIBLE_PATIENT_FLAG = 1` of the patient journey), total and by GFR / Dx stage and UACR stage; windows 1/3/6/12 months, `RUNNING_`, `PCT_`; `DIALYSIS_FLAG` for the cohort month.

---

## 1. Inputs before and after

| Input | Before | 3.1 / now |
| --- | --- | --- |
| Rx claims (HCP, patient, day only) | `Rx_01_new` | HCP Rx pull of the 3.1 Rx journey (`HCP_RX_TABLE`) from `DATA_START_DATE`, `Rx_01_new` before (column list only), as NB04 |
| Eligibility per patient-month | Run folder (`get_patient_table_path("sglt2_filter_m")`), already | Same |
| First dialysis date | Run folder (`get_patient_table_path("px")`), already | Same |

NB06 already read the patient tables from the run folder (unlike NB03 / NB04), so the 3.1 eligibility rules (PJ06) reach it directly.

## 2. Findings

**F1. Patient tables:** already from the run folder (`validation_2026_10_30/`, 2026-11-02). The older copy in `query_output/` (2026-10-26) differs: for the test HCPs, last cohort, 12 months: 7,544 eligible patient-months in the copy, 7,479 in the run folder; GFR / Dx stage 3: 23 vs 980, stage 4: 170 vs 114, unknown: 7,207 vs 6,259 (the code-based stage of PJ02, as NB03 / NB04). Dialysis patients of the test HCPs' patients: 215 vs 232.

**F2. Rx input** = 3.0 `Rx_01_new`, while NB01 / NB04 read the 3.1 HCP Rx pull. Test HCPs since 2023: 29,973 (HCP, patient, cohort month) in `Rx_01_new`, 29,974 in the pull, all 29,973 in both; eligible: 28,405 vs 28,406; last cohort 12 months: 7,479 in both.

**F3. Stage labels:** the 3.1 eligibility table only has `STAGE_2/3/4/UNKNOWN` (GFR / Dx) and `STAGE_2/3/UNKNOWN` (UACR) on eligible rows, the 7 fixed stage columns of 3.0. No new column.

**F4. New columns in the 3.1 table** (`HF_FLAG`, `DM_TYPE`, `GFR_UACR_DX_STAGE`): not used (decision D3 already in the notebook: no new columns yet).

**F5. `%run` path** after the move into the subfolder.

**F7. 3.0 windows are averages, not sums.** In `kerendia_nba_3_0_claim_eligible_patient` every `_IN_LAST_N_MONTH` column is the **mean of N+1 monthly counts** (the month itself and the N months before; e.g. provider 10221757, 2025-01: stage 2 = 7, 2024-12 = 4, `..._STAGE_2_IN_LAST_1_MONTH` = 5.5). Checked on all 9 test providers: 0 mismatches against mean(N+1) for every window and stage column (14,544 cells after the burn-in months), while most cells differ from a sum of N months. The base-month counts agree with an own recount from the 3.0 inputs (171 provider-months, 0 mismatches). D1 in the notebook ("sum of monthly counts, as 3.0") was based on a wrong reading: the refactor sums N months, like NB01–NB05 and their 3.0 originals.

**F6. Model features:** 1 of the 277 selected features (`RUNNING_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_4`) comes from NB06; it is one of the fixed columns.

## 3. Changes

| ID | Change | Where |
| --- | --- | --- |
| C1 | `%run "../../00_cohort_config"` | NB06 config cell |
| C2 | Rx input = `HCP_RX_TABLE` from `DATA_START_DATE` + `Rx_01_new` before (only the 3 used columns, `SVC_DT` as date); `HCP_RX_SOURCE = "3.0"` gives `Rx_01_new` only | NB06 load cell |
| C3 | Docs | NB06 load cell, this plan |
| C4 | Rx pull path read as `_QUERY_OUTPUT + HCP_RX_TABLE` (the config value is relative to `query_output/`, as in NB01); the first run failed with "Path must be absolute" | NB06 load cell |

Not changed: eligibility rule (patient journey), counting rule (D1), dialysis rule (D2), columns (D3), parity (3.0 reference inputs).

## 4. Decisions

| ID | Question | Proposal |
| --- | --- | --- |
| D1 | Window = sum of N monthly counts (refactor) or mean of N+1 monthly counts (3.0, F7) | **Decided 2026-11-03: keep the sum.** Same rule as NB01–NB05, whole numbers, matches the column names (`_IN_LAST_N_MONTH`). The offset-0 parity difference on the 60 window / window-`PCT_` columns is accepted and explained by F7; base-month, `RUNNING_` and `DIALYSIS_FLAG` logic are unchanged. The selected model feature (a `RUNNING_` column) is not affected; the model is retrained on the 3.1 features |
| D2–D3 | Dialysis month, no new columns | Already applied in the notebook (2026-11-03) |
| D4 | Patient-journey decisions C1 (SGLT2 rule) and C9 (diabetes) | Change `ELIGIBLE_PATIENT_FLAG` only; NB06 needs a re-run, no code change |
| D5 | HCP universe | Same as NB01–NB05 |

## 5. Validation

| Check | Result |
| --- | --- |
| Inputs | Rx 75,671 claims, 9 NPIs, 4,995 patients; eligibility rows of those patients 115,332, one row per patient-month (0 duplicates); 236 dialysis rows |
| Cohorts | Common end 2026-09-30, 20 cohorts 2025-01 .. 2026-08 (offset 7); 22,143 feature rows, 7,234 dialysis rows, 8 feature columns per window (total + the 7 fixed stage columns) |
| Fast engine = step-by-step (first and last cohort) | PASS |
| Write | 20 cohorts, 180 rows, 9 NPIs, 76 columns, 0 duplicates, **0 null cells** |
| Provider table | 180 rows, 0 null `PROVIDER_ID`, 0 duplicates |
| HCP trace 1386651560, every cohort | PASS: 10,836 eligible patient-months, 820 checks, 0 mismatches |
| Own recount (Spark, outside the notebook), last cohort, 12 months | PASS: total 7,479 (GFR / Dx stage 2 / 3 / 4 / unknown = 126 / 980 / 114 / 6,259; UACR 2 / 3 / unknown = 25 / 11 / 7,443), equal to the output; per HCP 0 of 8 mismatches (the 9th HCP has no eligible patient in the window) |
| Offset-0 parity vs 3.0 `kerendia_nba_3_0_claim_eligible_patient` (3.0 inputs) | **FAIL, explained by F7:** 19 months x 10 providers x 84 columns, 6,264 mismatching cells; all listed mismatches are window or window-`PCT_` columns. Base-month counts: 0 of 171 mismatches (own recount). Accepted (D1) |
| Selected model feature `RUNNING_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_4` | Present |
