# NBA 3.1 – HCP Dx Claims Features (NB03): Change Plan

> **Update 2026-11-11.** This plan describes the Phase A sync (2026-11-03). Since then: 28 cohorts c1–c28 at offset 0 (claims cohort file, X13), Delta by COHORT_SET (X14). Feature count: 104 → 113 (+9 Stage 5, net +9). Open decisions in section 5 resolved. See `NBA_3_1_HCP_Features_Decisions.md`.

**Notebook:** `03 Diagnosis Claims Files/03_claim_diagnosis_monthly_cohort` (moved into this folder 2026-11-03; `%run "../../00_cohort_config"`; cohort-based since 2026-10; 3.0 source `kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/03_claim_diagnosis_monthly`, unchanged)  
**Outputs:** `notebook_output/claim_diagnosis_monthly_cohort`, `notebook_output/provider_claim_diagnosis_monthly_cohort`  
**Validation set:** 10 test HCPs, 20 cohorts 2025-01 .. 2026-08, offset 7  
**Date:** 2026-11-03

---

## 1. What the notebook reads (before this change)

| Input | Used for | Source |
| --- | --- | --- |
| `query_output/Dx_03` | All Dx counts: total, by Dx stage (`TOTAL_DX_CLAIMS_STAGE_*`), `RUNNING_`, `PCT_` | 3.0 query (`00_Write_Input_Files`), 3.0 text mapping of the CKD stage |
| `query_output/kerendia_nba_3_1_pat_new_ckd_stage_validation` (root copy, 2026-10-26) | Patient-stage counts (`TOTAL_DX_CLAIMS_WITH_PATIENT_NEW_TO_STAGE_*`) | 3.1 patient journey, but an **older copy** than the validation run |

## 2. Findings

### F1. `Dx_03` misses the stage 3 sub-codes and every stage 5 code
`Dx_03` maps the stage from the diagnosis description text (the 3.0 PJ02 bug fixed in the 3.1 Dx journey). Codes not in `Dx_03` at all: N18.30, N18.31, N18.32, N18.5, N18.6 (ESRD), I12.0, I13.11, I13.2 and the T1D kidney codes E10.21/22/29.

| All US, Dx rows since 2023 | `Dx_03` (3.0) | 3.1 Dx journey pull |
| --- | --- | --- |
| Rows | 284.9M | 473.1M |
| HCPs (NPI) | 226.9K | 283.3K |
| Stage 1 | 1.24M | 1.26M |
| Stage 2 | 9.24M | 9.42M |
| Stage 3 | **12.6K** | **65.3M** |
| Stage 4 | 16.3M | 16.7M |
| Stage 5 | **0** | **115.8M** |
| Unspecified (0) | 258.1M | 264.6M |

Pull rows on the codes missing in `Dx_03`: 182.5M; the other 290.6M rows are close to the `Dx_03` total (284.9M). So the difference is the missing codes, not a different claim definition.

Consequence in today's output: `TOTAL_DX_CLAIMS_STAGE_3_*` is almost always 0, there are **no `STAGE_5` columns** (the pivot values come from the data), and ESRD / stage 3a-3b claims are not counted in `TOTAL_DX_CLAIMS` at all.

### F2. The 3.1 Dx journey has an NPI-level pull with the 3.1 rules
`query_output/full_2026_11_02/_stage/dx_step4_pull` (PJ02 Step 4 of the full run): one row per NPI x patient x day x diagnosis code, 31 CKD basket codes, `DX_STAGE` by code (0–5), `CKD_SUBSTAGE`, `DM_TYPE`, 2023-01-01 .. 2026-09-30, 3.1 HCP universe. Same idea as the lab pull now used by NB02. The Dx journey plan (`Patient_Journey_Validation/Dx Files/NBA_3_1_Dx_Journey_Plan.md`, step 7 and decision D3) already lists "HCP `Dx_03` with the same basket" as a follow-up and expects NB03 to gain `STAGE_5` columns; using the pull does this without a second query.

### F3. Test HCPs

| | `Dx_03` | 3.1 pull |
| --- | --- | --- |
| Rows since 2023 | 6,815 | 8,991 |
| HCPs with Dx | 9 | 9 |
| Stage 3 / stage 5 rows | 0 / 0 | 1,604 / 2,429 |

* 1528629052: 0 → 83 rows (not in 3.0 Dx universe). 1508230566: 1,681 → 0 (not in the 3.1 HCP universe, checked 2026-11-03; same HCP as in NB02).
* NPI-patient-days in both: 3,801. Highest stage per day: same in all except 1,769 days that were stage 0 in `Dx_03` and are 3 (704) or 5 (1,065) in the pull, and 8 days that go up one stage (extra code the same day). No day goes down.
* `Dx_03` has 242 repeated rows (same NPI, patient, day, category = several claims); the pull counts each code once per NPI-patient-day, as the lab pull does.

### F4. Patient-stage table read from an old copy
NB03 reads `query_output/<table>` directly, not through `get_patient_table_path()` (NB01 fix C1). Root copy 2026-10-26 (4,238 patients) vs validation run `validation_2026_10_30/` 2026-11-02 (4,431 patients). Of the 1,085 pull patients of the test HCPs, 1,053 are in the validation-run table and 895 in the root copy. The root copy predates the PJ02 code-based stage: patient-months new to stage 3 / stage 5 = 83 / 18 (root) vs 862 / 382 (validation run). With the root copy the test HCPs had **no** claims with a patient new to stage 3 or 5.

### F5. Trace HCP drops out
`HCP_TRACE_NPIS["dx"] = 1508230566` has no rows in the 3.1 pull. Busiest test HCP in the pull: 1841364841 (2,669 rows).

---

## 3. Changes

| # | Change | Where |
| --- | --- | --- |
| C1 | Dx input = 3.1 Dx journey pull (`load_dx_input()`), same columns as `Dx_03` for the features (`NPI_NUMBER`, `PATIENT_ID`, `SVC_DT`, `DX_STAGE`, `PROVIDER_ID`); null-stage assert | NB03 load cell |
| C2 | Run params `HCP_DX_SOURCE` (`"3.1"` default / `"3.0"`), `HCP_DX31_PULL_TABLE` (default `full_2026_11_02/_stage/dx_step4_pull`), `HCP_DX_TABLE`; `HCP_SOURCE_TABLES` uses `HCP_DX_TABLE` (common end date unchanged, 2026-09-30) | `00_cohort_config` |
| C3 | Fixed Dx-stage pivot values `STAGE_1..STAGE_5, STAGE_UNSPECIFIED` (no scan of the input): every run and every input gets the same columns. **Adds the `STAGE_5` columns** (window, `PCT_`, `RUNNING_`); all other names unchanged | NB03 load cell |
| C4 | Patient-stage table through `get_patient_table_path("new_ckd_stage")` (validation run copy) | NB03 load cell |
| C5 | Trace HCP `dx` = 1841364841 | `00_cohort_config` |
| C6 | Docs: title cell and section notes | NB03 |

Not changed: feature logic, windows (1, 3, 6, 12), `DATA_START_DATE` rule, offset-0 parity (still on the 3.0 reference `Dx_03` + 3.0 patient table, so it tests the logic only).

## 4. Validation

1. Fast engine = step-by-step (first and last cohort).
2. Write: 20 cohorts, no duplicates, no nulls; provider table.
3. HCP trace 1841364841, every cohort.
4. Independent pandas recount from the pull + patient table, every row.
5. Offset-0 parity vs 3.0 `provider_claim_diagnosis_monthly` (3.0 inputs).
6. Before (Delta v1, `Dx_03`) vs after.

## 5. Open decisions

| # | Topic |
| --- | --- |
| D1 | Use the 3.1 pull as Dx input (same as NB02 lab D1) – applied, switch back with `HCP_DX_SOURCE = "3.0"` |
| D2 | Save the Dx pull as a named output of every patient-journey run (same as NB02 D2) |
| D3 | HCP universe: 1508230566 drops out because it is not in the 3.1 universe (as in NB02) |
| D4 | New `STAGE_5` columns: confirm. No HCP notebook reads the NB03 output; of the 277 selected features (`Feature Analysis/NBA_3_1_HCP_Claims_Selected_Features_277.csv`) 3 come from NB03 (`TOTAL_DX_CLAIMS_STAGE_UNSPECIFIED_IN_LAST_3_MONTH`, `..._WITH_PATIENT_NO_NEW_STAGE_IN_LAST_6/12_MONTH`), none is a `STAGE_5` column |
| D5 | T1D kidney codes (E10.21/22/29: 1.39M rows all US, 14 for the test HCPs) are in the pull and counted as Dx claims (stage unspecified); `Dx_03` had none. Keep, or drop with `DM_TYPE = 'T1D'`? |

## 6. Results (run 2026-11-03, Delta version 2)

| Check | Result |
| --- | --- |
| Input | `full_2026_11_02/_stage/dx_step4_pull`, 8,991 rows for 9 test HCPs, 0 rows without `DX_STAGE`; common end date 2026-09-30 (unchanged) -> 20 cohorts |
| Patient table | `validation_2026_10_30/kerendia_nba_3_1_pat_new_ckd_stage_validation` |
| Fast engine = step-by-step (2025-01, 2026-08) | PASS, 2 x 1,062 cells, 0 mismatches |
| Write | 20 cohorts, 180 rows (9 HCPs x 20), 120 columns, 0 duplicates, 0 null cells, no missing / extra cohorts |
| Provider table | 180 rows, 0 null `PROVIDER_ID`, 0 duplicates |
| HCP trace 1841364841 | 20 cohorts, 1,300 checks, 0 mismatches |
| Independent pandas recount (pull + patient table, every row; window, stage, patient-stage, `PCT_` stage, `RUNNING_`) | 16,020 checks, 0 mismatches |
| Offset-0 parity vs 3.0 `provider_claim_diagnosis_monthly` (3.0 `Dx_03` + 3.0 patient table) | PASS, 19 months, 127 columns, 0 mismatching cells |

**Before (v1: `Dx_03`, root patient table) vs after (v2: 3.1 pull, run patient table)**

| | Before | After |
| --- | --- | --- |
| Rows / HCPs | 180 / 9 | 180 / 9 (1508230566 out, 1528629052 in) |
| Columns | 111 | 120 (+9: `STAGE_5` x 4 windows, 4 `PCT_`, 1 `RUNNING_`); none dropped |
| Last cohort (2026-08), all HCPs: Dx claims in 12 months | 1,753 | 3,210 |
| ... of which stage 3 / stage 5 | 0 / – | 501 / 1,034 |
| ... stage unspecified | 1,634 | 1,558 |
| `RUNNING_TOTAL_DX_CLAIMS` (last cohort) | 6,692 | 8,760 |
| `RUNNING_` claims with patient new to stage 3 / 5 | 0 / 0 | 623 / 171 |

* 8 HCPs in both: 3,938 of 9,600 count cells change (41%), 671 lower, the rest higher.
* The 3 NB03 features in the selected-277 list: `STAGE_UNSPECIFIED_IN_LAST_3_MONTH` changes in 62 of 160 HCP-cohorts (sum 6,574 -> 6,277); `WITH_PATIENT_NO_NEW_STAGE_IN_LAST_6 / 12_MONTH` change in 135 / 148 of 160 (sums about +86% / +83%, from the added stage 3 / 5 claims).
