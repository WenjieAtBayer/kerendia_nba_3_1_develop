# NBA 3.1 – HCP combined claims features (NB04): sync with the 3.1 patient journey, analysis and plan

> **Update 2026-11-11.** This plan describes the Phase A sync (2026-11-03). Since then: 28 cohorts c1–c28 at offset 0 (claims cohort file, X13), Parquet by COHORT_SET (X14). Feature count: 1,571 → 3,065 (+1,494 net) — Kerendia brand, HbA1c/Potassium and Stage 5 features from NB01/NB02/NB03 flow into the combined table. Total columns = 3,074. Previous full run had 2,892. See `NBA_3_1_HCP_Features_Decisions.md`.

**Status (2026-11-03):** C1–C7 applied and validated on the 10 test HCPs (section 5). Client summary: `04 Monthly Cohort Claims Files/NBA_3_1_Claims_Features_Client_Summary.md`.  
**Notebook:** `hcp_level_features/04 Monthly Cohort Claims Files/04_claims_monthly_cohort` (3.0 source `04_claims_monthly`)  
**Outputs:** `notebook_output/claims_monthly_cohort` (NPI x `COHORT_ID`) and `final_claims_monthly_cohort` (`PROVIDER_ID` x `COHORT_ID`)  
**What it builds:** every Rx claim of an HCP, split by what was known about the patient's kidneys at that time: (A) the patient's GFR / UACR stage that month, (B) a GFR / UACR lab test on the same day, (C) the patient's stage x the patient's treatments that month. Windows 1/3/6/12 months, `RUNNING_`, `PCT_`.

---

## 1. Inputs before and after

| Input | 3.0 / before | 3.1 / now |
| --- | --- | --- |
| Rx claims | `Rx_01_new` | HCP Rx pull of the 3.1 Rx journey (`HCP_RX_TABLE`, PJ03 Step 4d), same as NB01 |
| Same-day lab tests (family B) | `Lab_04` | 3.1 lab pull (`HCP_CLAIMS_LAB_TABLE` = `HCP_LAB31_PULL_TABLE`), same as NB02 |
| Patient stage per month (A) | `query_output/kerendia_nba_3_1_pat_gfr_dx_stage_validation` (copy of 2026-10-26) | Patient-journey run folder (`get_patient_table_path`, `validation_2026_10_30/`, 2026-11-02) |
| Patient stage x treatment (C) | `query_output/kerendia_nba_3_1_pat_uacr_stage_validation` (copy of 2026-10-26) | Same, run folder |
| `Dx_03` | Read, never used | Not read |

---

## 2. Findings

**F1. Patient tables read from an old copy** (same as NB03 F4). NB04 read `query_output/<table>` directly. The copy (2026-10-26, 4,238 patients) predates the code-based CKD stage of PJ02 (N18.3x = stage 3, ESRD = stage 5): for the test HCPs' patients it has 13,665 patient-months at GFR stage `0` ("unspecified", labelled `GFR_STAGE_UNKNOWN`) and 138 at stage 3; the run-folder table (4,431 patients) has no stage 0 and 8,991 patient-months at stage 3.

**F2. Rx input** = 3.0 `Rx_01_new`, while NB01 now reads the 3.1 HCP Rx pull (NB01 C4). Same claims (50,739 of 50,739 + 2 newer, NB01 plan section 0b).

**F3. `Lab_04` misses most UACR tests and part of the GFR tests.** All US: `Lab_04` has GFR tests for 42.4 M patients and UACR tests for **12.9 K**; the 3.1 lab pull has 63.9 M and **16.1 M**. For the patients of the test HCPs (2023-01 .. 2026-09): 853 patient-day tests in `Lab_04` (all GFR), 2,838 in the pull (2,177 GFR, 661 UACR); the 809 in both have the same stage. Both have a few patient-days with 2 rows (tests from 2 HCPs); NB04 keeps the 3.0 rule (lab from any HCP, each row counts).

**F4. Pull history starts at `DATA_START_DATE`.** `Rx_01_new` and `Lab_04` start earlier (2019 / 2021-07). NB04 takes its column list from the full history, so a pull-only input could drop columns.

**F5. 27 family-A columns no longer produced.** `GFR_STAGE_UNKNOWN_AND_UACR_STAGE_1/2/3` (windows, `RUNNING_`, `PCT_`) only came from the stage-0 months of F1. With the 3.1 patient tables they had no claim, and the first run left them null (old schema kept by `mergeSchema`).

**F6. DPP-IV / other glucose treatments missing in family C.** The 3.1 patient table (PJ06) drops the `Other- glucose mgmt` category (patient journey rule), so family C has no `..._WITH_DPP_IV` / `..._WITH_OTHER_GLUCOSE_MGMT` column (the 3.0 table had them). 9 of the 89 selected NB04 model features (`Feature Analysis/NBA_3_1_HCP_Claims_Selected_Features_277.csv`) are such columns. 7 more selected `..._WITH_GLP_1` columns are absent in validation only because the 10 test HCPs have no such patient-month (GLP-1 is in the 3.1 table as a brand); the full run decides.

**F7. `%run` path** after the move into the subfolder: fixed to `../../00_cohort_config`.

---

## 3. Changes

| ID | Change | Where |
| --- | --- | --- |
| C1 | Rx input = `HCP_RX_TABLE` (`load_claims_rx_input()`), as NB01 | NB04 load cell |
| C2 | Lab input = 3.1 lab pull (`load_claims_lab_input()`): `GFR_STAGE` / `UACR_STAGE` mapped to the `Lab_04` stage texts, `MEDIAN_TEST_RESULT` cast to `decimal(12,3)`; new config `HCP_CLAIMS_LAB_TABLE` (pull when `HCP_LAB_SOURCE = "3.1"`, else `Lab_04`) | NB04 load cell, `00_cohort_config` |
| C3 | Patient tables through `get_patient_table_path()` (run folder) | NB04 load cell |
| C4 | 3.0 rows before `DATA_START_DATE` (`Rx_01_new`, `Lab_04`) added for the column list; they never count (feature rows are filtered at `DATA_START_DATE`, as before) | NB04 load cell |
| C5 | `Dx_03` not read | NB04 load cell |
| C6 | Family A always has the full stage grid (GFR 1–5 / UNKNOWN x UACR 1–3 / UNKNOWN): F5 columns back, as 0 | NB04 "Feature rows" cell |
| C7 | `%run` path; docs (title, section 1 and 1.5) | NB04 |

Not changed: joins, labels, the n x n family-C rule, windows, `RUNNING_` / `PCT_`, offset-0 parity (still on the 3.0 reference inputs).

---

## 4. Decisions

| ID | Question | Proposal |
| --- | --- | --- |
| D1 | Use the 3.1 Rx and lab pulls (C1, C2) | Applied (same choice as NB01 / NB02); switch back with `HCP_RX_SOURCE` / `HCP_LAB_SOURCE = "3.0"` |
| D2 | F6: family C without DPP-IV / other glucose (9 selected model features) | **Decided 2026-11-03: (a) keep the patient-journey rule.** The patient treatment table follows the 3.1 Rx journey (no `Other- glucose mgmt`), so NB04 family C has no DPP-IV / other-glucose columns. The 9 features are removed from the model feature list; the 3.1 model is retrained and its feature selection rerun on the 3.1 output. Changing PJ06 for the HCP features only (b) would make the patient tables differ from the patient journey used everywhere else. The 7 `..._WITH_GLP_1` features are checked in the full run |
| D3 | HCP universe (1508230566 not in the 3.1 universe) | Same as NB01–NB03 |
| D4 | Lab pull location (`full_2026_11_02/_stage/`) | Same as NB02 D2 (named output of every patient-journey run) |

---

## 5. Validation (10 test HCPs, offset 7, run 2026-11-03)

| Check | Result |
| --- | --- |
| Fast engine = step-by-step (first and last cohort) | PASS: 2 x 16,047 cells, 0 mismatches |
| Write | 20 cohorts, 180 rows (9 HCPs), 1,785 columns, 0 duplicates, **0 null cells** |
| Provider table | 180 rows, 0 null `PROVIDER_ID`, 0 duplicates |
| HCP trace 1386651560, every cohort | PASS: 19,800 checks, 0 mismatches |
| Own recount from the inputs (last cohort, 12 months): total Rx, family A per GFR stage, family B per lab stage | PASS: total equal for all 9 HCPs (12,837); family A 54 checks, family B 72 checks, 0 mismatches |
| Offset-0 parity vs 3.0 `final_claims_monthly` (3.0 inputs) | PASS: 19 months, 2,217 columns, 0 mismatches |

**Before (copy tables, 3.0 Rx and lab) vs now**, 9 test HCPs (recount, the 2026-10-26 output can no longer be read: Delta retention):

| Measure | Before | Now |
| --- | --- | --- |
| Rx claims, last cohort, 12 months | 12,836 | 12,837 |
| Family A, claims with a known GFR stage (12 months) | 770 | 2,502 |
| ... stage 3 / stage 5 | 37 / 7 | 1,765 / 216 |
| ... stage 4 | 291 | 162 |
| Family B, Rx claims with a same-day test since 2023 (GFR / UACR) | 2 / 0 | 13 / 11 |
| Family C, counted rows since 2023 | 337,113 | 341,098 (+1.2%) |
| Columns | 1,560 | 1,785 (+225: new stage x drug combinations, mainly stage 3 / 5 and UACR tests) |

Most of the change is family A / C (F1: stage-3 and stage-5 patients that were "unspecified"), as in NB03. Family B stays very small (same-day tests are rare).

---

## 6. Next steps

1. D2 decided (keep the patient-journey rule; drop the 9 features from the model list at retraining).
2. Full run: run folder `full_2026_11_02/` (patient tables, Rx pull of PJ03 Step 4d, lab pull).
