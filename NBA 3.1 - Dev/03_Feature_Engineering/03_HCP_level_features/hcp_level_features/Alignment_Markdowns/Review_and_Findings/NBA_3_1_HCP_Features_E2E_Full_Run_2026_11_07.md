# Kerendia NBA 3.1 – HCP-Level Features: End-to-End Full Run (2026-11-07)

**Scope:** full job from patient journey to cohort sets, for the full 3.1 HCP universe, with 28 cohorts (c1–c28, offset 0, claims cohort file).
**Run name:** `full_2026_11_07`. **Previous run:** `NBA_3_1_HCP_Features_E2E_Full_Run_2026_11_05.md` (20 cohorts, offset 7).
**Status:** run in progress — NB01 and NB04 still running; all other tasks succeeded. Feature comparison below is complete for all 6 NPI-level tables.

---

## 1. In short

* **First run with the claims cohort file:** 28 cohorts c1–c28 (May 2024 – Aug 2026), offset 0 (calendar months), read from `cohorts/claims/cohorts.parquet`.
* **Output format changed:** Parquet partitioned by COHORT_SET (7 groups: 5 training, 1 validation, 1 backtesting). No full Delta table any more.
* **Update 2026-11-11:** this run wrote about 455,000 small files per table (NB01: 906 GB), which made reads and QC very slow; it was cancelled before NB01 and NB04 finished. From 2026-11-11 the outputs are Delta, still partitioned by COHORT_SET (decision X14); the next full run is `full_2026_11_11`.
* **Across all 6 NPI-level notebooks, 3.1 has 8,360 features vs 7,440 in 3.0 — a net gain of +920 features.** 1,935 new features were added and 1,015 were intentionally removed.
* **Key additions:** 234 Kerendia brand features (NB01), 48 HbA1c / Potassium lab features (NB02), 9 CKD Stage 5 features (NB03), 128 DM/HF type features (NB06).
* **Key removals:** 979 features from 6 treatment categories outside the 3.1 brand list (NB01), 21 features with the retired 9-month lookback window (NB02), 15 incomplete GFR/UACR stage breakdowns (NB06).

---

## 2. Run

Job **1010893614518587** ("NBA 3.1 Patient Journey + HCP Features"), run **477251413108207**.
Defaults: `VALIDATION_MODE=false`, `RUN_OUTPUT_DIR=full_2026_11_07`, `EXPECTED_COHORTS=28`.

| Task | Duration | Result |
| --- | --- | --- |
| PJ01 lab / PJ02 Dx / PJ03 Rx (parallel) | 8 / 14 / 19 min | Success |
| PJ04 DM/HF flags / PJ05 Px | 1 / 1 min | Success |
| PJ06 combine | 14 min | Success |
| NB02 lab / NB03 Dx / NB05 Rx NPS | 13 / 28 / 35 min | Success |
| NB06 eligible | 39 min | Success |
| NB01 Rx | ~135 min (still running) | In progress |
| NB04 claims | ~135 min (still running) | In progress |
| NB07 cohort sets | — | Blocked (waiting for NB01/NB04) |

---

## 3. Where things are

| What | Location |
| --- | --- |
| Patient-journey tables | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/full_2026_11_07/patient_journey/` |
| Query pulls (Rx, lab, Dx) | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/query_output/full_2026_11_07/` |
| HCP feature tables (Parquet) | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/full_2026_11_07/hcp_claims/<table>/COHORT_SET=<group>/` |
| Claims cohort file | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/cohorts/claims/cohorts.parquet` |
| Code | Branch `dev/hcp-claims-features` |

To read a table back from its sets: `read_cohort_sets(table)` in `00_cohort_config`.

---

## 4. Feature comparison: 3.0 vs 3.1

All comparisons are at **NPI level** (the canonical output per notebook). The provider-level tables have the same feature columns (NPI_NUMBER replaced by PROVIDER_ID), so feature counts are identical.

### 4a. Summary per notebook (feature columns only, excluding metadata)

| Notebook | Table | 3.0 features | 3.1 features | New | Dropped | Net |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| NB01 | `claim_rx_monthly_cohort` | 5,411 | 4,668 | +236 | −979 | −743 |
| NB02 | `claim_lab_monthly_cohort` | 116 | 143 | +48 | −21 | +27 |
| NB03 | `claim_diagnosis_monthly_cohort` | 104 | 113 | +9 | 0 | +9 |
| NB04 | `claims_monthly_cohort` | 1,571 | 3,065 | +1,494 | 0 | +1,494 |
| NB05 | `claim_rx_nps_monthly_cohort` | 154 | 154 | 0 | 0 | 0 |
| NB06 | `claim_eligible_patient_cohort` | 84 | 217 | +148 | −15 | +133 |
| **Total** | | **7,440** | **8,360** | **+1,935** | **−1,015** | **+920** |

3.0 baselines: NB01 uses `claim_rx_monthly` (the clean production table, not the cohort table inflated by Delta mergeSchema). NB06 uses `kerendia_nba_3_0_claim_eligible_patient`. All others use their cohort tables in `ops_pipeline_bkp/notebook_output/`. Feature counts exclude metadata columns (NPI_NUMBER, COHORT_ID, COHORT_MONTH, OFFSET_DAYS, CUTOFF_DATE, SVC_DT_M, PULL_DT, DATASET, COHORT_SET).

### 4b. Feature categories per notebook

#### NB01 — Rx Claims

| Category | 3.0 | 3.1 | Delta | Notes |
| --- | ---: | ---: | ---: | --- |
| Total Rx Claims | 496 | 382 | −114 | 6 non-brand categories removed |
| Percentage (PCT) | 2,485 | 2,052 | −433 | Same cause |
| Brand | 626 | 572 | −54 | +234 Kerendia, −GLP-1 treatment-category overlap |
| Patient Attributes (Age/Gender) | 922 | 800 | −122 | Fewer categories to cross |
| Running (cumulative) | 511 | 520 | +9 | +Kerendia running features |
| Refill | 85 | 32 | −53 | Non-brand categories removed |
| Treatment Category | 238 | 182 | −56 | GLP-1 → Other- glucose mgmt (option C) |
| Ratio / Difference / Average | 22 | 20 | −2 | Minor |
| SGLT2 WO INVOKANA (derived) | 40 | 32 | −8 | Fewer cross-cuts |
| Other | 90 | 76 | −14 | — |
| **Total** | **5,515** | **4,668** | **−847** | |

**Added (+236):**
* 234 Kerendia brand features, following the same cross-cut pattern as other brands:
  * `TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_{1,3,6,12}_MONTH`, `PCT_TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_{1,3,6,12}_MONTH`
  * Age: `KERENDIA_AGE_GROUP_{0_10, 10_20, ..., ABOVE_80, IGNORE}` × 4 windows
  * Gender: `KERENDIA_{F, M, U}` × 4 windows
  * Payer: `KERENDIA_{CASH, COMMERCIAL, MEDICARE, MEDICARE_PART_D, FFS_MEDICAID, MGD_MEDICAID}` × 4 windows
  * Supply: `KERENDIA_{30, 60, 90, NOT_30_60_90, DAYS_SUPPLY_UNKNOWN}_DAYS_SUPPLY` × 4 windows
  * Refill: `KERENDIA_{NEW_PRESCRIPTION, REFILL}` × 4 windows
  * Running: `RUNNING_TOTAL_RX_CLAIMS_KERENDIA` and cross-cuts
  * Rejection: `TOTAL_REJECTED_RX_CLAIMS_KERENDIA_IN_LAST_{1,3,6,12}_MONTH`, `PCT_TOTAL_REJECTED_RX_CLAIMS_KERENDIA_IN_LAST_{1,3,6,12}_MONTH`
* 2 running features: `RUNNING_TOTAL_RX_CLAIMS_SGLT2_WO_INVOKANA_300MG_DAYS_SUPPLY_UNKNOWN`, `RUNNING_TOTAL_RX_CLAIMS_SGLT2_WO_INVOKANA_300MG_NOT_30_60_90_DAYS_SUPPLY`

**Removed (−979):** All features for 6 treatment categories that are outside the 3.1 HCP brand list (each with ~54 columns for total, pct, age, gender, payer, supply cross-cuts × 4 windows + running):
* `ACE_OR_ARB` (54 columns): `TOTAL_RX_CLAIMS_ACE_OR_ARB_IN_LAST_{1,3,6,12}_MONTH`, `PCT_...`, `ACE_OR_ARB_{F,M,U}`, `ACE_OR_ARB_{CASH,COMMERCIAL,...}`, etc.
* `CALCIUM_CHANNEL_OR_BETA_BLOCKER` (54 columns): same cross-cut pattern
* `COMBO_DRUG` (54 columns): same pattern
* `DIURETIC_NON_MRA` (54 columns): same pattern
* `INSULIN` (54 columns): same pattern
* `METFORMIN` (52 columns): same pattern (slightly fewer cross-cuts)
* Plus 657 columns that were overall cross-cuts of the removed categories: standalone `AGE_GROUP_*`, `F/M/U`, `CASH/COMMERCIAL/MEDICARE/...` totals and percentages without a brand prefix, per-brand rejection totals without a window (`PCT_TOTAL_REJECTED_RX_CLAIMS_DPP_IV`, etc.), and `AVG_PATIENT_AGE`, `AVG_TREATMENT_PER_PATIENT`, `TOTAL_PATIENT_COUNT`, `TOTAL_TREATMENT_COUNT`.

#### NB02 — Lab Claims

| Category | 3.0 | 3.1 | Delta | Notes |
| --- | ---: | ---: | ---: | --- |
| GFR tests | 5 | 4 | −1 | 9-month window removed |
| UACR tests | 5 | 4 | −1 | 9-month window removed |
| Lab tests (combined) | 45 | 36 | −9 | 9-month window removed |
| Percentage | 50 | 56 | +6 | New lab test percentages |
| Running (cumulative) | 11 | 11 | 0 | — |
| HbA1c / Potassium (new) | 0 | 32 | +32 | New in 3.1 |
| **Total** | **116** | **143** | **+27** | |

**Added (+48):** HbA1c and Potassium lab features, each across 4 lookback windows (1, 3, 6, 12 months):
* `TOTAL_PATIENTS_HBA1C_TESTED_IN_LAST_{1,3,6,12}_MONTH` — patients with any HbA1c test
* `TOTAL_PATIENTS_HBA1C_GE_9_IN_LAST_{1,3,6,12}_MONTH` — patients with HbA1c ≥ 9
* `PCT_PATIENTS_HBA1C_GE_9_IN_LAST_{1,3,6,12}_MONTH` — % of tested patients above threshold
* `TOTAL_ELIGIBLE_PATIENTS_HBA1C_TESTED_IN_LAST_{1,3,6,12}_MONTH` — same, eligible patients only
* `TOTAL_ELIGIBLE_PATIENTS_HBA1C_GE_9_IN_LAST_{1,3,6,12}_MONTH`
* `PCT_ELIGIBLE_PATIENTS_HBA1C_GE_9_IN_LAST_{1,3,6,12}_MONTH`
* Same 6 patterns for Potassium > 5: `..._POTASSIUM_TESTED_...`, `..._POTASSIUM_GT_5_...`, `PCT_..._POTASSIUM_GT_5_...`

**Removed (−21):** All 21 features with the `IN_LAST_9_MONTH` lookback window. 3.0 used windows [1, 3, 6, 9, 12]; 3.1 standardized to [1, 3, 6, 12]. Examples:
* `TOTAL_LAB_CLAIMS_GFR_IN_LAST_9_MONTH`, `TOTAL_LAB_CLAIMS_UACR_IN_LAST_9_MONTH`, `TOTAL_LAB_CLAIMS_IN_LAST_9_MONTH`
* `TOTAL_LAB_CLAIMS_A1_IN_LAST_9_MONTH`, `..._A2_...`, `..._A3_...`
* `TOTAL_LAB_CLAIMS_CHRONIC_KIDNEY_DISEASE_STAGE_{1,2_MILD,3_MODERATE,4_SEVERE,5}_IN_LAST_9_MONTH`
* `PCT_TOTAL_LAB_CLAIMS_*_IN_LAST_9_MONTH` (same set)

#### NB03 — Diagnosis Claims

| Category | 3.0 | 3.1 | Delta | Notes |
| --- | ---: | ---: | ---: | --- |
| CKD Stage | 44 | 48 | +4 | Stage 5 added |
| Dx Claims | 4 | 4 | 0 | — |
| Percentage | 44 | 48 | +4 | Stage 5 percentages |
| Running (cumulative) | 12 | 13 | +1 | Stage 5 running total |
| **Total** | **104** | **113** | **+9** | |

**Added (+9):** CKD Stage 5 features (3.0 stopped at Stage 4):
* `TOTAL_DX_CLAIMS_STAGE_5_IN_LAST_{1,3,6,12}_MONTH`
* `PCT_TOTAL_DX_CLAIMS_STAGE_5_IN_LAST_{1,3,6,12}_MONTH`
* `RUNNING_TOTAL_DX_CLAIMS_STAGE_5`

**Removed:** none.

#### NB04 — Combined Claims (NB01 + NB02 + NB03)

| Category | 3.0 | 3.1 | Delta | Notes |
| --- | ---: | ---: | ---: | --- |
| Patient Attributes | 696 | 1,360 | +664 | Kerendia cross-cuts flow in |
| Percentage | 696 | 1,360 | +664 | Same cause |
| Running (cumulative) | 175 | 341 | +166 | Kerendia + new lab/dx running |
| Rx Claims | 4 | 4 | 0 | — |
| **Total** | **1,571** | **3,065** | **+1,494** | |

**Added (+1,494):** NB04 joins NB01+NB02+NB03 at NPI level. The 1,494 new features are the Kerendia Rx columns from NB01 (brand, age, gender, payer, supply, refill, rejection cross-cuts × 4 windows + running totals), plus the HbA1c/Potassium features from NB02 and the CKD Stage 5 features from NB03, all flowing into the combined table. Column name patterns: `TOTAL_RX_CLAIMS_KERENDIA_*`, `PCT_TOTAL_RX_CLAIMS_KERENDIA_*`, `RUNNING_TOTAL_RX_CLAIMS_KERENDIA*`, `*_HBA1C_*`, `*_POTASSIUM_*`, `*_STAGE_5_*`.

**Removed:** none.

#### NB05 — Rx NPS Claims

No feature changes. The 154 features are identical between 3.0 and 3.1. The total column count difference (161 → 163) comes from the DATASET and COHORT_SET metadata columns added by `write_hcp_output`.

#### NB06 — Eligible HCP

| Category | 3.0 | 3.1 | Delta | Notes |
| --- | ---: | ---: | ---: | --- |
| Eligible patients | 83 | 140 | +57 | New eligibility structure |
| DM/HF type (new in 3.1) | 0 | 64 | +64 | Diabetes type, HF type, per-window |
| Dialysis flag | 1 | 1 | 0 | — |
| Percentage / Totals | 0 | 12 | +12 | New summary features |
| **Total** | **84** | **217** | **+133** | |

**Added (+148):**
* 128 DM/HF type features from the new PJ04 diabetes and heart failure flags, each across 4 lookback windows (1, 3, 6, 12 months):
  * `TOTAL_ELIGIBLE_PATIENTS_DM_TYPE_{NONE, OTHER, T1D, T2D}_IN_LAST_{1,3,6,12}_MONTH`
  * `PCT_ELIGIBLE_PATIENTS_DM_TYPE_{NONE, OTHER, T1D, T2D}_IN_LAST_{1,3,6,12}_MONTH`
  * `TOTAL_ELIGIBLE_PATIENTS_HF_TYPE_{NONE, HFPEF, HFREF, HF_UNSPECIFIED}_IN_LAST_{1,3,6,12}_MONTH`
  * `PCT_ELIGIBLE_PATIENTS_HF_TYPE_{NONE, HFPEF, HFREF, HF_UNSPECIFIED}_IN_LAST_{1,3,6,12}_MONTH`
  * Same patterns for `TOTAL_RX_PATIENTS_DM_TYPE_*` and `TOTAL_RX_PATIENTS_HF_TYPE_*` (Rx-treated patients)
* 20 HF-related eligibility features:
  * `TOTAL_ELIGIBLE_PATIENTS_HF_IN_LAST_{1,3,6,12}_MONTH` — eligible patients with any HF diagnosis
  * `PCT_ELIGIBLE_PATIENTS_HF_IN_LAST_{1,3,6,12}_MONTH`
  * `TOTAL_RX_PATIENTS_HF_IN_LAST_{1,3,6,12}_MONTH` — Rx-treated patients with HF
  * `PCT_RX_PATIENTS_HF_IN_LAST_{1,3,6,12}_MONTH`
  * 4 additional HF summary features

**Removed (−15):** Stage-level GFR/UACR breakdowns that were not windowed (replaced by the new family-based eligibility structure):
* `TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_{2, 3, 4, UNKNOWN}`
* `PCT_TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_{2, 3, 4, UNKNOWN}`
* `TOTAL_ELIGIBLE_PATIENTS_UACR_STAGE_{2, 3, UNKNOWN}`
* `PCT_TOTAL_ELIGIBLE_PATIENTS_UACR_STAGE_{2, 3, UNKNOWN}`
* `TOTAL_ELIGIBLE_PATIENTS` (single total, replaced by per-window totals)

### 4c. Net new features: what 3.1 adds over 3.0

| Feature group | Count | Source notebook |
| --- | ---: | --- |
| Kerendia brand Rx features | 234 | NB01 |
| HbA1c ≥ 9 / Potassium > 5 lab features | 48 | NB02 |
| CKD Stage 5 diagnosis features | 9 | NB03 |
| Kerendia + lab + Dx in the combined table | 1,494 | NB04 |
| DM/HF type + new eligibility features | 148 | NB06 |
| **Total new features** | **1,935** | |

| Removed group | Count | Reason |
| --- | ---: | --- |
| Non-brand treatment categories (NB01) | 979 | `ACE_OR_ARB`, `CALCIUM_CHANNEL_OR_BETA_BLOCKER`, `COMBO_DRUG`, `DIURETIC_NON_MRA`, `INSULIN`, `METFORMIN` — outside the 3.1 brand list |
| 9-month lookback window (NB02) | 21 | Window standardized to [1, 3, 6, 12] months |
| Old GFR/UACR stage breakdowns (NB06) | 15 | Replaced by windowed, family-based eligibility structure |
| **Total removed features** | **1,015** | |

---

## 5. Output tables (completed notebooks)

Row counts and HCP counts are from the NPI-level tables that have finished writing. NB01 and NB04 are still running; their columns are known from the NPI-level tables already on disk.

| Table | Columns | Cohorts | Status |
| --- | ---: | ---: | --- |
| `claim_rx_monthly_cohort` (NB01) | 4,677 | 28 | NPI written; QC + provider in progress |
| `claim_lab_monthly_cohort` (NB02) | 152 | 28 | Complete |
| `provider_claim_lab_monthly_cohort` | 152 | 28 | Complete |
| `claim_diagnosis_monthly_cohort` (NB03) | 122 | 28 | Complete |
| `provider_claim_diagnosis_monthly_cohort` | 122 | 28 | Complete |
| `claims_monthly_cohort` (NB04) | 3,074 | 28 | NPI written; QC + provider in progress |
| `claim_rx_nps_monthly_cohort` (NB05) | 163 | 28 | Complete |
| `claim_eligible_patient_cohort` (NB06) | 226 | 28 | Complete |
| `provider_claim_eligible_patient_cohort` | 226 | 28 | Complete |

---

## 6. Next steps

| # | Point | Next step |
| --- | --- | --- |
| – | NB01 / NB04 / NB07 | Wait for the run to finish; check NB07's validation of all 11 tables |
| – | `HCP_LATEST_FULL_RUN` | Point to `full_2026_11_07` so test runs read this run's pulls |
| O2 | `PROVIDER_ID` gaps | Same issue as 2026-11-05; decide fill / de-duplication |
| – | Downstream combine | Wire to `COHORT_ID` and the 7 COHORT_SET groups |
| – | 10-doctor test run | Run in the new folder layout to verify validation mode |
| – | Job 36449327509782 | Still points at the 3.0 volume; update or retire |
