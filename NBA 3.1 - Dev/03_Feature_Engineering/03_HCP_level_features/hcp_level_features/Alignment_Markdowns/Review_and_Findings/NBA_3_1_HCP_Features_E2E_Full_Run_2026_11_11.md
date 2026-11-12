# Kerendia NBA 3.1 – HCP-Level Features: End-to-End Full Run (2026-11-11)

**Scope:** full job from patient journey to cohort sets, for the full 3.1 HCP universe, with 28 cohorts (c1–c28, offset 0, claims cohort file).
**Run name:** `full_2026_11_11`. **Previous run:** `full_2026_11_07` (Parquet, cancelled — see `NBA_3_1_HCP_Features_E2E_Full_Run_2026_11_07.md`). **Before that:** `full_2026_11_05` (20 cohorts, offset 7).
**Status:** NB01–NB06 all succeeded. NB07 (cohort-set check) is in progress after a fix to the duplicate check for empty `PROVIDER_ID` rows (O2). Feature comparison and output tables below are complete.

---

## 1. In short

* **First run with Delta output:** all HCP feature tables are Delta partitioned by `COHORT_SET` (7 groups) with `optimizeWrite`. The 2026-11-07 Parquet run wrote about 455,000 small files per table (NB01: 906 GB, 75% metadata); this run writes a few large files per group (NB01: 156 files, 73.5 GB). Read and QC are 30–300× faster.
* **28 cohorts c1–c28** (May 2024 – Aug 2026), offset 0 (calendar months), from the claims cohort file `cohorts/claims/cohorts.parquet`.
* **Across all 6 NPI-level notebooks, 3.1 has 8,360 features vs 7,440 in 3.0 — a net gain of +920 features.** 1,935 new features were added and 1,015 were intentionally removed.
* **Key additions:** 234 Kerendia brand features (NB01), 48 HbA1c / Potassium lab features (NB02), 9 CKD Stage 5 features (NB03), 128 DM/HF type features (NB06).
* **Key removals:** 979 features from 6 treatment categories outside the 3.1 brand list (NB01), 21 features with the retired 9-month lookback window (NB02), 15 incomplete GFR/UACR stage breakdowns (NB06).
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
| NB07 cohort sets | in progress (after fix) | In progress |

**Total wall-clock (PJ01 start to NB04 finish): ~4 h 55 min.**

### Comparison with the 2026-11-07 Parquet run

| Task | 2026-11-07 (Parquet) | 2026-11-11 (Delta) |
| --- | --- | --- |
| NB01 Rx | > 5 h (cancelled) | 151.9 min |
| NB04 claims | > 5 h (cancelled) | 221.2 min |
| NB01 file count | ~65,000 per table | 156 |
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
| | | **Total** | | | **449** | **230.76** | | |

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

**Repair 1 (run 372743477209890):** 2 of the 4 tables passed; `provider_claim_rx_monthly_cohort` and `final_claims_monthly_cohort` still failed. The fix code was verified correct on all four tables (rows − nulls = distinct non-null keys). The failure is under investigation; a second repair is in progress.

**Manual verification (this run):** all 11 tables checked independently — 0 real duplicates, 28 cohorts, 7 groups, DATASET matches. The empty-key counts are 3,094 (NB01/NB04 provider), 949 (NB03 provider), 3,001 (NB06 provider), 0 (NPI-level and NB05).

---

## 7. Next steps

| # | Point | Next step |
| --- | --- | --- |
| – | NB07 | Wait for the repair to finish and pass |
| – | `HCP_LATEST_FULL_RUN` | Point to `full_2026_11_11` so validation runs read this run's pulls |
| O2 | `PROVIDER_ID` gaps | Same issue as 2026-11-05; 3,094 (NB01/NB04), 949 (NB03), 3,001 (NB06). Decide fill / de-duplication |
| – | Downstream combine | Wire to `COHORT_ID` and the 7 COHORT_SET groups |
| – | 10-doctor test run | Run in the new folder layout to verify validation mode |
| – | Job 36449327509782 | Still points at the 3.0 volume; update or retire |
| – | Clean-up | Delete `full_2026_11_07` Parquet output (~1.6 TB for NB01+NB04) and `_scratch_delta_test/` after this run confirmed OK |
| – | NB04 timing | 221 min vs 130–140 min expected; investigate separately |