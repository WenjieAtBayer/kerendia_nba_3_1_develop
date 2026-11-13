# Kerendia NBA 3.1 – HCP-Level Features: End-to-End Full Run (2026-11-11)

**Scope:** full job from patient journey to cohort sets, for the full 3.1 HCP universe, with 28 cohorts (c1–c28, offset 0, claims cohort file).
**Run name:** `full_2026_11_11`. **Previous run:** `full_2026_11_07` (Parquet, cancelled — see `NBA_3_1_HCP_Features_E2E_Full_Run_2026_11_07.md`). **Before that:** `full_2026_11_05` (20 cohorts, offset 7).
**Status:** run 441950237921 finished with SUCCESS. NB01–NB06 succeeded; NB07 (cohort-set check) succeeded on attempt 5 after the fix to the duplicate check for empty `PROVIDER_ID` rows (O2).
**Correction 2026-11-12:** section 4 was re-done against the 3.0 production tables (`ops_pipeline/notebook_output/`). The earlier version compared against `ops_pipeline_bkp/notebook_output/` cohort tables. Those are test-HCP outputs of an early cohort version (152–190 rows), not 3.0 production; the NB02 one still had a 9-month window, and the NB04 one is the NPI-level intermediate table. This led to wrong removal reasons (six Rx categories, 9-month window, NB06 stage breakdowns). Details: readiness plan, Appendix A.2–A.8.

---

## 1. In short

* **First run with Delta output:** all HCP feature tables are Delta partitioned by `COHORT_SET` (7 groups) with `optimizeWrite`. The 2026-11-07 Parquet run wrote 455,057 small files for NB01 alone (about 65,000 per cohort set, 906 GB); this run writes a few large files per group (NB01: 156 files, 73.5 GB). On one cohort set, a row count is 307× faster and a null-count check 45× faster (section 5).
* **28 cohorts c1–c28** (May 2024 – Aug 2026), offset 0 (calendar months), from the claims cohort file `cohorts/claims/cohorts.parquet`.
* **Across the 6 notebooks, 3.1 has 8,360 features vs 9,617 in the 3.0 production tables.** 7,694 are kept, 666 added, 1,923 removed.
* **Key additions:** 234 Kerendia features (NB01, own treatment category), 180 Kerendia features (NB04), 48 HbA1c / Potassium lab features (NB02), 9 CKD Stage 5 features (NB03), 148 DM / HF features (NB06).
* **Removals (1,923):** 1,684 are single-month (window-less) columns that 3.0 kept next to the `_IN_LAST_1_MONTH` columns. They hold the same values (0 mismatches on all rows of the 3.0 tables: 7.4M rows for NB02, 13.0M–13.6M for the others), so this removes redundancy, not information. 220 NB04 stage × DPP-IV / other-glucose columns are dropped by decision X5. 19 are single-month columns that are **not** identical to the 1-month columns and need review (NB01: 4 averages / counts; NB06: 15 eligibility columns). **No treatment category was removed:** ACE/ARB, Calcium channel / Beta blocker, Combo drug, Diuretic non-MRA, Insulin and Metformin are all in the 3.1 output.
* **Provider tables (O2, open):** rows with an empty `PROVIDER_ID` (NPIs without a provider ID in the mapping table) are present in the provider-level tables. These are known and explained, not duplicates.

---

## 2. Run

Job **1010893614518587** ("NBA 3.1 Patient Journey + HCP Features"), run **441950237921**.
Parameters: `VALIDATION_MODE=false`, `RUN_OUTPUT_DIR=full_2026_11_11`, `EXPECTED_COHORTS=28`.

| Task | Duration | Result |
| --- | --- | --- |
| PJ01 lab / PJ02 Dx / PJ03 Rx (parallel) | 14.6 / 13.5 / 37.1 min | Success |
| PJ04 DM/HF flags / PJ05 Px | 5.9 / 1.3 min | Success |
| PJ06 combine | 15.5 min | Success |
| NB02 lab | 31.6 min | Success |
| NB03 Dx | 146.2 min | Success |
| NB05 Rx NPS | 148.6 min | Success |
| NB06 eligible | 146.5 min | Success |
| NB01 Rx | 151.9 min | Success |
| NB04 claims | 221.2 min | Success |
| NB07 cohort sets | attempts 1–4 failed; attempt 5: 3.0 min | Success |

**Total wall-clock (PJ01 start to NB04 finish): 4 h 40 min** (from the Jobs API start / end times; whole run including NB07 retries: 17 h 40 min).

### Comparison with the 2026-11-07 Parquet run

| Task | 2026-11-07 (Parquet) | 2026-11-11 (Delta) |
| --- | --- | --- |
| NB01 Rx | > 5 h (cancelled) | 151.9 min |
| NB04 claims | > 5 h (cancelled) | 221.2 min |
| NB01 file count | 455,057 (about 65,000 per cohort set) | 156 |
| NB01 total size | ~906 GB | 73.5 GB |

---

## 3. Where things are

| What | Location |
| --- | --- |
| Patient-journey tables | `…/notebook_output/full_2026_11_11/patient_journey/` |
| Query pulls (Rx, lab, Dx) | `…/query_output/full_2026_11_11/` |
| HCP feature tables (Delta) | `…/notebook_output/full_2026_11_11/hcp_claims/<table>/` (partitioned by `COHORT_SET=<group>/`) |
| Claims cohort file | `…/kerendia_nba_3_1_volume/cohorts/claims/cohorts.parquet` |
| Code | Branch `dev/hcp-claims-features`, commits `b1ebbf9`, `4fb6f67`, `81d9cb6` |

To read a table back from its sets: `read_cohort_sets(table)` in `00_cohort_config`.

---

## 4. Feature comparison: 3.0 vs 3.1

Counts are the column names of the output tables. 3.0 = the 3.0 production tables written by the 3.0 notebooks (`kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/`); 3.1 = `full_2026_11_11/hcp_claims/`. For NB03 and NB04 the provider-level tables are compared (no 3.0 NPI-level table exists); the provider and NPI tables have the same feature columns.

### 4a. Summary per notebook (feature columns only, excluding metadata)

| Notebook | 3.0 table → 3.1 table | 3.0 features | 3.1 features | New | Dropped | Net |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| NB01 | `claim_rx_monthly` → `claim_rx_monthly_cohort` | 5,411 | 4,668 | +236 | −979 | −743 |
| NB02 | `claim_lab_monthly_ZS` → `claim_lab_monthly_cohort` | 116 | 143 | +48 | −21 | +27 |
| NB03 | `provider_claim_diagnosis_monthly` → `provider_claim_diagnosis_monthly_cohort` | 127 | 113 | +9 | −23 | −14 |
| NB04 | `final_claims_monthly` → `final_claims_monthly_cohort` | 3,691 | 3,065 | +225 | −851 | −626 |
| NB05 | `kerendia_nba_3_0_claim_rx_nps_monthly` → `claim_rx_nps_monthly_cohort` | 188 | 154 | 0 | −34 | −34 |
| NB06 | `kerendia_nba_3_0_claim_eligible_patient` → `claim_eligible_patient_cohort` | 84 | 217 | +148 | −15 | +133 |
| **Total** | | **9,617** | **8,360** | **+666** | **−1,923** | **−1,257** |

Feature counts exclude metadata columns (NPI_NUMBER, PROVIDER_ID, COHORT_ID, COHORT_MONTH, OFFSET_DAYS, CUTOFF_DATE, SVC_DT_M, PULL_DT, DATASET, COHORT_SET).

**Why the dropped columns are dropped:**

| Notebook | Single-month copies (identical to `_IN_LAST_1_MONTH`) | Decision X5 | Not identical, needs review |
| --- | ---: | ---: | ---: |
| NB01 | 975 | – | 4 (`AVG_PATIENT_AGE`, `AVG_TREATMENT_PER_PATIENT`, `TOTAL_PATIENT_COUNT`, `TOTAL_TREATMENT_COUNT`) |
| NB02 | 21 | – | – |
| NB03 | 23 | – | – |
| NB04 | 631 | 220 | – |
| NB05 | 34 | – | – |
| NB06 | – | – | 15 |
| **Total** | **1,684** | **220** | **19** |

How this was checked: each 3.0-only column `X` without a window suffix was matched to `X_IN_LAST_1_MONTH`, which exists in both 3.0 and 3.1. The values of `X` and `X_IN_LAST_1_MONTH` were then compared on all rows of the 3.0 table (NB01 13.6M, NB02 7.4M, NB03 13.0M, NB04 13.6M, NB05 13.4M, NB06 13.6M rows). For NB04, 671 columns were compared: the 631 single-month columns and the 40 single-month columns among the 220 X5 columns; all 671 match. The NB01 averages differ because the 3.0 averages cover one extra month (`step3_lag_avg`, kept in 3.1 as `AVG_EXTRA_MONTH`). The NB06 columns differ because the 3.0 NB06 windows are averages of N+1 months (X8).

### 4b. Feature categories per notebook

#### NB01 — Rx Claims

Kept 4,432, added 236, removed 979 (all single-month columns). Every windowed and running column of 3.0 is in 3.1, so the columns per group are unchanged: ACE/ARB, Calcium channel / Beta blocker, Combo drug, Diuretic non-MRA, Insulin and SGLT2 245 each, Metformin 236, Other glucose mgmt 243, Farxiga 254, Jardiance 263, Invokana 100 mg 261, Invokana 300 mg 252, Spironolactone-MRA 254, DPP-IV 252, GLP-1 261; SGLT2 without Invokana 300 mg 153 → 155 (+2 running totals). Counts are all 3.1 columns named after the group (look-back, running total, ratio and 3–6-month difference); SGLT2 and Invokana 300 mg exclude the SGLT2-without-Invokana-300-mg columns.

**Added (+236):**
* 234 Kerendia features. They come from the treatment-category pivot (Kerendia is its own `TREATMENT_CATEGORY` in the 2026-11-05 product mapping; it is not in `HCP_BRANDS`) and follow the same cross-cut pattern as the other groups:
  * `TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_{1,3,6,12}_MONTH`, `PCT_TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_{1,3,6,12}_MONTH`
  * Age: `KERENDIA_AGE_GROUP_{0_10, 10_20, ..., ABOVE_80, IGNORE}` × 4 windows
  * Gender: `KERENDIA_{F, M, U}` × 4 windows
  * Payer: `KERENDIA_{CASH, COMMERCIAL, MEDICARE, MEDICARE_PART_D, FFS_MEDICAID, MGD_MEDICAID}` × 4 windows
  * Supply: `KERENDIA_{30, 60, 90, NOT_30_60_90, DAYS_SUPPLY_UNKNOWN}_DAYS_SUPPLY` × 4 windows
  * Refill: `KERENDIA_{NEW_PRESCRIPTION, REFILL}` × 4 windows
  * Running: `RUNNING_TOTAL_RX_CLAIMS_KERENDIA` and cross-cuts
  * Rejection: `TOTAL_REJECTED_RX_CLAIMS_KERENDIA_IN_LAST_{1,3,6,12}_MONTH`, `PCT_TOTAL_REJECTED_RX_CLAIMS_KERENDIA_IN_LAST_{1,3,6,12}_MONTH`
* 2 running features: `RUNNING_TOTAL_RX_CLAIMS_SGLT2_WO_INVOKANA_300MG_DAYS_SUPPLY_UNKNOWN`, `RUNNING_TOTAL_RX_CLAIMS_SGLT2_WO_INVOKANA_300MG_NOT_30_60_90_DAYS_SUPPLY`

**Removed (−979):** all 979 are single-month columns without a window suffix (the 3.0 monthly value kept next to the lag columns). The cohort design builds only windowed columns. **No treatment category was removed**; the six categories below are in the 3.1 output with all their windowed columns.
* 322 single-month columns of the six non-brand categories: `ACE_OR_ARB`, `CALCIUM_CHANNEL_OR_BETA_BLOCKER`, `COMBO_DRUG`, `DIURETIC_NON_MRA`, `INSULIN` (54 each), `METFORMIN` (52). Examples: `TOTAL_RX_CLAIMS_ACE_OR_ARB` (kept as `TOTAL_RX_CLAIMS_ACE_OR_ARB_IN_LAST_1_MONTH`), `PCT_TOTAL_RX_CLAIMS_ACE_OR_ARB_F`, `TOTAL_RX_CLAIMS_ACE_OR_ARB_MEDICARE`.
* 653 single-month columns of the other groups (brands, standalone age / gender / payer totals, rejections, totals).
* 975 of the 979 equal their `_IN_LAST_1_MONTH` column. The 4 exceptions, `AVG_PATIENT_AGE`, `AVG_TREATMENT_PER_PATIENT`, `TOTAL_PATIENT_COUNT` and `TOTAL_TREATMENT_COUNT`, are single-month values not produced in 3.1 (needs review).
* Evidence: the 3.1 `TOTAL_RX_CLAIMS_ACE_OR_ARB_IN_LAST_12_MONTH` sums to 3,890,810,648 claims over the table.

#### NB02 — Lab Claims

| Group | 3.0 | 3.1 | Delta | Notes |
| --- | ---: | ---: | ---: | --- |
| Kept | 95 | 95 | 0 | eGFR / UACR / CKD stage lab features (windowed and running) |
| Single-month columns | 21 | 0 | −21 | Same values as `_IN_LAST_1_MONTH` |
| HbA1c / Potassium (new) | 0 | 48 | +48 | New in 3.1 |
| **Total** | **116** | **143** | **+27** | |

**Added (+48):** HbA1c and Potassium lab features, each across 4 lookback windows (1, 3, 6, 12 months):
* `TOTAL_PATIENTS_HBA1C_TESTED_IN_LAST_{1,3,6,12}_MONTH` — patients with any HbA1c test
* `TOTAL_PATIENTS_HBA1C_GE_9_IN_LAST_{1,3,6,12}_MONTH` — patients with HbA1c ≥ 9
* `PCT_PATIENTS_HBA1C_GE_9_IN_LAST_{1,3,6,12}_MONTH` — % of tested patients above threshold
* `TOTAL_ELIGIBLE_PATIENTS_HBA1C_TESTED_IN_LAST_{1,3,6,12}_MONTH` — same, eligible patients only
* `TOTAL_ELIGIBLE_PATIENTS_HBA1C_GE_9_IN_LAST_{1,3,6,12}_MONTH`
* `PCT_ELIGIBLE_PATIENTS_HBA1C_GE_9_IN_LAST_{1,3,6,12}_MONTH`
* Same 6 patterns for Potassium > 5: `..._POTASSIUM_TESTED_...`, `..._POTASSIUM_GT_5_...`, `PCT_..._POTASSIUM_GT_5_...`

**Removed (−21):** the 21 single-month columns (no window suffix): `TOTAL_LAB_CLAIMS`, `TOTAL_LAB_CLAIMS_{GFR,UACR,A1,A2,A3}`, `TOTAL_LAB_CLAIMS_CHRONIC_KIDNEY_DISEASE_STAGE_{1,2_MILD,3_MODERATE,4_SEVERE,5}` and the 10 matching `PCT_` columns. They equal their `_IN_LAST_1_MONTH` columns (0 mismatches). The 3.0 production table `claim_lab_monthly_ZS` has no 9-month columns. The earlier "9-month window" reason came from the `ops_pipeline_bkp` test table.

#### NB03 — Diagnosis Claims

| Category | 3.0 | 3.1 | Delta | Notes |
| --- | ---: | ---: | ---: | --- |
| CKD Stage | 44 | 48 | +4 | Stage 5 added |
| Dx Claims | 4 | 4 | 0 | — |
| Percentage | 44 | 48 | +4 | Stage 5 percentages |
| Running (cumulative) | 12 | 13 | +1 | Stage 5 running total |
| **Total (windowed and running)** | **104** | **113** | **+9** | |
| Single-month columns (3.0 only) | 23 | 0 | −23 | Same values as `_IN_LAST_1_MONTH` |
| **Total incl. single-month** | **127** | **113** | **−14** | |

**Added (+9):** CKD Stage 5 features (the 3.0 Dx input had no stage 5 claims):
* `TOTAL_DX_CLAIMS_STAGE_5_IN_LAST_{1,3,6,12}_MONTH`
* `PCT_TOTAL_DX_CLAIMS_STAGE_5_IN_LAST_{1,3,6,12}_MONTH`
* `RUNNING_TOTAL_DX_CLAIMS_STAGE_5`

**Removed (−23):** single-month columns `TOTAL_DX_CLAIMS`, `TOTAL_DX_CLAIMS_STAGE_{1,2,3,4,UNSPECIFIED}`, `TOTAL_DX_CLAIMS_WITH_PATIENT_NEW_TO_STAGE_{1..5}`, `TOTAL_DX_CLAIMS_WITH_PATIENT_NO_NEW_STAGE` and the 11 matching `PCT_` columns (0 mismatches).

#### NB04 — Combined Claims (NB01 + NB02 + NB03)

| Group | 3.0 | 3.1 | Delta | Notes |
| --- | ---: | ---: | ---: | --- |
| Kept | 2,840 | 2,840 | 0 | Rx claims by patient GFR / UACR stage and lab test (windowed and running) |
| Single-month columns | 631 | 0 | −631 | Same values as `_IN_LAST_1_MONTH` |
| Stage × DPP-IV / other glucose (family C) | 220 | 0 | −220 | Decision X5 |
| Kerendia (new) | 0 | 180 | +180 | Kerendia own category |
| UACR test stage × Invokana (new) | 0 | 45 | +45 | New combinations in the 3.1 data |
| **Total** | **3,691** | **3,065** | **−626** | |

The 3.0 baseline is the production table `final_claims_monthly` (3,694 columns). The earlier 1,571 came from the NPI-level `claims_monthly_cohort` test table in `ops_pipeline_bkp`.

**Added (+225):** 180 Kerendia columns (`..._WITH_KERENDIA...`) and 45 = 9 each of `TOTAL_RX_CLAIMS_PATIENT_WITH_TEST_UACR_STAGE_{1,3}_WITH_INVOKANA_{100MG,300MG}` and `..._STAGE_2_WITH_INVOKANA_300MG` (windows, PCT, running). NB02 / NB03 features are not part of this table.

**Removed (−851):** 631 single-month columns (0 mismatches) and 220 X5 columns: `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_{1..5,UNKNOWN}_WITH_{DPP_IV,OTHER_GLUCOSE_MGMT}` (132) and `..._DX_UACR_STAGE_{1,2,3,UNKNOWN}_WITH_{DPP_IV,OTHER_GLUCOSE_MGMT}` (88), with windows, PCT and running variants. 9 of them are in the 752 model features.

#### NB05 — Rx NPS Claims

Kept 154, added 0, removed 34. The removed columns are single-month columns (`TOTAL_PATIENTS_VISIT`, `TOTAL_NEW_PATIENT_START`, `TOTAL_PATIENTS_START_<category / brand>` and the matching `PCT_` columns); they equal their `_IN_LAST_1_MONTH` columns (0 mismatches). The 3.0 baseline is `kerendia_nba_3_0_claim_rx_nps_monthly` (190 columns: 188 features + `PROVIDER_ID`, `SVC_DT_M`).

#### NB06 — Eligible HCP

| Group | 3.0 | 3.1 | Delta | Notes |
| --- | ---: | ---: | ---: | --- |
| Kept | 69 | 69 | 0 | Eligible patients by GFR / Dx and UACR stage (windowed, running), dialysis flag |
| Single-month columns | 15 | 0 | −15 | Not identical to the 3.0 1-month columns (needs review) |
| Diabetes type (new) | 0 | 64 | +64 | DM_TYPE T2D / T1D / OTHER / NONE |
| HF type (new) | 0 | 64 | +64 | HF_TYPE HFPEF_PROXY / HFREF_PROXY / MIXED / UNKNOWN |
| Any HF (new) | 0 | 16 | +16 | |
| Total Rx patients (new) | 0 | 4 | +4 | Denominator per window |
| **Total** | **84** | **217** | **+133** | |

**Added (+148):** for each window 1 / 3 / 6 / 12 months:
* `TOTAL_RX_PATIENTS_DM_TYPE_{T2D,T1D,OTHER,NONE}`, `TOTAL_ELIGIBLE_PATIENTS_DM_TYPE_{...}` and the matching `PCT_RX_PATIENTS_` / `PCT_ELIGIBLE_PATIENTS_` columns (64)
* The same four patterns for `HF_TYPE_{HFPEF_PROXY,HFREF_PROXY,MIXED,UNKNOWN}` (64)
* `TOTAL_RX_PATIENTS_HF`, `TOTAL_ELIGIBLE_PATIENTS_HF`, `PCT_RX_PATIENTS_HF`, `PCT_ELIGIBLE_PATIENTS_HF` (16)
* `TOTAL_RX_PATIENTS_IN_LAST_{1,3,6,12}_MONTH` (4)

**Removed (−15):** single-month columns (no window suffix). The windowed versions are kept in 3.1. In the 3.0 table they differ from the 1-month column, because the 3.0 windows are averages of N+1 months (X8), so they need review:
* `TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_{2, 3, 4, UNKNOWN}`
* `PCT_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_{2, 3, 4, UNKNOWN}`
* `TOTAL_ELIGIBLE_PATIENTS_UACR_STAGE_{2, 3, UNKNOWN}`
* `PCT_TOTAL_ELIGIBLE_PATIENTS_UACR_STAGE_{2, 3, UNKNOWN}`
* `TOTAL_ELIGIBLE_PATIENTS` (single total, replaced by per-window totals)

### 4c. Net new features: what 3.1 adds over 3.0

| Feature group | Count | Source notebook |
| --- | ---: | --- |
| Kerendia Rx features (own treatment category) | 234 | NB01 |
| SGLT2 without Invokana 300 mg running totals | 2 | NB01 |
| HbA1c ≥ 9 / Potassium > 5 lab features | 48 | NB02 |
| CKD Stage 5 diagnosis features | 9 | NB03 |
| Kerendia by patient stage / lab test | 180 | NB04 |
| UACR test stage × Invokana | 45 | NB04 |
| DM / HF type, any HF, total Rx patients | 148 | NB06 |
| **Total new features** | **666** | |

| Removed group | Count | Reason |
| --- | ---: | --- |
| Single-month copies (NB01 975, NB02 21, NB03 23, NB04 631, NB05 34) | 1,684 | Same values as the kept `_IN_LAST_1_MONTH` columns; the cohort design builds only windowed columns |
| Stage × DPP-IV / other glucose, family C (NB04) | 220 | Decision X5 (patient-journey rule) |
| Single-month columns that are not identical (NB01 4, NB06 15) | 19 | Needs review |
| **Total removed features** | **1,923** | |

---

## 5. Output tables

All 11 tables written as Delta, partitioned by `COHORT_SET` (7 groups). Row counts are from the Delta tables read back after the run. Duplicate counts exclude rows with an empty `PROVIDER_ID` (O2).

| NB | Table | Key | Rows | Columns | Files | Size (GB) | Duplicates | Empty keys |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| NB01 | `claim_rx_monthly_cohort` | NPI | 8,088,309 | 4,677 | 156 | 73.50 | 0 | 0 |
| NB01 | `provider_claim_rx_monthly_cohort` | PID | 8,089,534 | 4,677 | 177 | 72.71 | 0 | 3,094 |
| NB02 | `claim_lab_monthly_cohort` | NPI | 5,166,341 | 152 | 7 | 0.96 | 0 | 0 |
| NB02 | `provider_claim_lab_monthly_cohort` | PID | 5,166,849 | 152 | 7 | 0.94 | 0 | 0 |
| NB03 | `claim_diagnosis_monthly_cohort` | NPI | 7,588,140 | 122 | 7 | 1.18 | 0 | 0 |
| NB03 | `provider_claim_diagnosis_monthly_cohort` | PID | 7,588,929 | 122 | 7 | 1.17 | 0 | 949 |
| NB04 | `claims_monthly_cohort` | NPI | 8,088,309 | 3,074 | 74 | 34.73 | 0 | 0 |
| NB04 | `final_claims_monthly_cohort` | PID | 8,089,534 | 3,074 | 77 | 34.68 | 0 | 3,094 |
| NB05 | `claim_rx_nps_monthly_cohort` | PID | 6,446,723 | 163 | 7 | 1.56 | 0 | 0 |
| NB06 | `claim_eligible_patient_cohort` | NPI | 8,085,228 | 226 | 16 | 4.67 | 0 | 0 |
| NB06 | `provider_claim_eligible_patient_cohort` | PID | 8,086,450 | 226 | 17 | 4.66 | 0 | 3,001 |
| | | **Total** | | | **552** | **230.76** | | |

**Key = NPI** → NPI_NUMBER; **Key = PID** → PROVIDER_ID. Empty keys are rows with `PROVIDER_ID = NULL` (NPIs without a provider ID in the mapping table, O2). The NPI-level tables have no empty keys.

### Delta vs Parquet (NB01, one group C25-C26_validation, 588k rows, 4,676 cols)

| Format | Files | Size | Read count | Null-count QC (200 cols) |
| --- | ---: | --- | --- | --- |
| Delta (this run) | 12 | 5.4 GB | 0.7 s | 2.2 s |
| Parquet (2026-11-07) | 64,998 | 121.4 GB | 214.9 s | 99.8 s |
| Improvement | 5,417× fewer files | 22× smaller | 307× faster | 45× faster |

---

## 6. NB07 cohort-set check

NB07 checks all 11 tables: exactly the 7 COHORT_SET groups; each group has its cohorts; all 28 cohorts; one row per (key, COHORT_ID); DATASET matches the cohort file.

**First attempt (run 608935029352160):** failed with `AssertionError: Cohort-set check failed for: ['provider_claim_rx_monthly_cohort', 'provider_claim_diagnosis_monthly_cohort', 'final_claims_monthly_cohort', 'provider_claim_eligible_patient_cohort']`.

**Root cause:** the duplicate check compared total rows with distinct `(key, COHORT_ID)` pairs. Rows with `PROVIDER_ID = NULL` collapse to one distinct key per cohort under a `DISTINCT` count, so each cohort with empty IDs appeared to have duplicates. The gap (rows − keys) exactly equals the empty-ID rows minus 28 (one per cohort).

**Fix applied to cell 5 of `07_split_cohort_sets` (committed `81d9cb6`):** count rows with an empty key separately (`NULL_KEYS`) and run the duplicate check only on rows with a non-null key. A real duplicate still fails the check.

**Repair 1 (run 372743477209890):** 2 of the 4 tables passed; `provider_claim_rx_monthly_cohort` and `final_claims_monthly_cohort` still failed. The fix code was verified correct on all four tables (rows − nulls = distinct non-null keys). Attempts 3 and 4 also failed. Attempt 5 succeeded (3.0 min, 2026-11-12).

**Manual verification (this run):** all 11 tables checked independently — 0 real duplicates, 28 cohorts, 7 groups, DATASET matches. The empty-key counts are 3,094 (NB01/NB04 provider), 949 (NB03 provider), 3,001 (NB06 provider), 0 (NPI-level and NB05).

---

## 7. Next steps

| # | Point | Next step |
| --- | --- | --- |
| – | NB07 | Done: passed on attempt 5 (2026-11-12) |
| – | `HCP_LATEST_FULL_RUN` | Point to `full_2026_11_11` so validation runs read this run's pulls |
| O2 | `PROVIDER_ID` gaps | Same issue as 2026-11-05; 3,094 (NB01/NB04), 949 (NB03), 3,001 (NB06). Decide fill / de-duplication |
| – | Downstream combine | Wire to `COHORT_ID` and the 7 COHORT_SET groups |
| – | 10-doctor test run | Run in the new folder layout to verify validation mode |
| – | Job 36449327509782 | Still points at the 3.0 volume; update or retire |
| – | Clean-up | Delete `full_2026_11_07` Parquet output (~1.6 TB for NB01+NB04) and `_scratch_delta_test/` after this run confirmed OK |
| – | NB04 timing | 221 min vs 130–140 min expected; investigate separately |