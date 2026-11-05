# Kerendia NBA 3.1 – HCP-Level Features: End-to-End Full Run (2026-11-05)

**Scope:** one job from the patient journey to the cohort sets, for the full 3.1 HCP universe, with 20 cohorts (2025-01 .. 2026-08, offset 7).
**Run name:** `full_2026_11_05`. **Previous run:** `NBA_3_1_HCP_Features_E2E_Full_Run_2026_11_04.md` (HCP notebooks only, 3.0 volume, product mapping 2026_11_04).
**Status:** all 13 tasks succeeded and the outputs were checked. Open: `PROVIDER_ID` gaps (O2) and the points in section 7.

---

## 1. In short

* **First run of the whole chain in one job:** PJ01–PJ06, then NB01–NB06, then NB07. Everything is written to `kerendia_nba_3_1_volume`; the 3.0 volume is only read.
* **New in this run:**
  * Product mapping 2026_11_05 (13 GLP-1 products, Kerendia and generic dapagliflozin switched on; Px J0606).
  * GLP-1 counted as `Other- glucose mgmt` in the HCP Rx features (option C).
  * Cohort sets: 5 Parquet sub files of 4 cohorts per table.
* **All 11 tables have the 20 cohorts.** The NPI-level tables have no duplicate keys and no empty keys.
* **No column of the 2026-11-04 run is lost**, so the 268 selected features are all still present. The only new columns are Kerendia columns: NB01 +234 (4,441 -> 4,675) and NB04 +180 (2,892 -> 3,072). NB01 has no duplicate column names, so the GLP-1 clash is solved.
* **Cohort sets match the source:** all 11 tables x 5 sets x 4 cohorts, with the same row counts as the source tables.

---

## 2. Run

Job **1010893614518587** ("NBA 3.1 Patient Journey + HCP Features"), run **1082029547613419**. Defaults: `VALIDATION_MODE=false`, `RUN_OUTPUT_DIR=full_2026_11_05`, `COHORTS_PER_SET=4`, `EXPECTED_COHORTS=20`.

| Task | Duration | Result |
| --- | --- | --- |
| PJ01 lab / PJ02 Dx / PJ03 Rx (parallel) | 18 / 21 / 42 min | Success |
| PJ04 DM/HF flags / PJ05 Px | 6 / 1 min | Success |
| PJ06 combine | 21 min | Success |
| NB02 / NB03 / NB04 / NB05 / NB06 | 10 / 27 / 99 / 33 / 31 min | Success |
| NB01 Rx | 112 min (repair) | 2 failed attempts, then success in the repair |
| NB07 cohort sets | 16 min (repair) | Success |

**NB01 failure and fix:** the preview trace cell read NB01's own output table before section 3 writes it. Earlier runs passed only because an older output already existed in the 3.0 volume; this was the first write into the 3.1 folder. The cell now skips the trace when the output does not exist yet. Features and the write step are unchanged. Only NB01 and NB07 were rerun (repair).

---

## 3. Where things are

| What | Location |
| --- | --- |
| Patient-journey tables | `kerendia_nba_3_1_volume/notebook_output/patient_journey_features/full_2026_11_05/` |
| Query pulls (Rx, lab, Dx) | `kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/query_output/full_2026_11_05/` |
| HCP feature tables (Delta) | `kerendia_nba_3_1_volume/notebook_output/hcp_claims_features/<table>/` |
| Cohort sets (Parquet) | `.../hcp_claims_features/cohort_sets/4_cohorts_per_set/<table>/set_01_2025-01_to_2025-04/` .. `set_05_2026-05_to_2026-08/` |
| Product mapping | `kerendia_nba_3_1_volume/final_product_mapping/*_2026_11_05.csv` |
| Code | Branch `dev/hcp-claims-features`, commit `3726caf` |

To read a table back from its sets: `read_cohort_sets(table)` in `00_cohort_config`.

---

## 4. Output tables

| Table | Rows | HCPs | Columns | Cohorts | Change vs 2026-11-04 |
| --- | --- | --- | --- | --- | --- |
| `claim_rx_monthly_cohort` (NB01) | 5,832,742 | 294,582 NPIs | 4,675 | 20 | +79 NPIs, +234 Kerendia columns |
| `provider_claim_rx_monthly_cohort` | 5,833,683 | 294,504 providers | 4,675 | 20 | see section 6 |
| `claim_lab_monthly_cohort` (NB02) | 3,803,309 | 199,335 NPIs | 102 | 20 | same |
| `provider_claim_lab_monthly_cohort` | 3,803,718 | 199,362 providers | 102 | 20 | same |
| `claim_diagnosis_monthly_cohort` (NB03) | 5,518,531 | 283,010 NPIs | 120 | 20 | same |
| `provider_claim_diagnosis_monthly_cohort` | 5,519,206 | 283,015 providers | 120 | 20 | same |
| `claims_monthly_cohort` (NB04) | 5,832,742 | 294,582 NPIs | 3,072 | 20 | +79 NPIs, +180 Kerendia columns |
| `final_claims_monthly_cohort` | 5,833,683 | 294,504 providers | 3,072 | 20 | see section 6 |
| `claim_rx_nps_monthly_cohort` (NB05) | 4,645,269 | 234,178 providers | 161 | 20 | same (3.0 new-start input, X7) |
| `claim_eligible_patient_cohort` (NB06) | 5,831,040 | 294,542 NPIs | 76 | 20 | +99 NPIs |
| `provider_claim_eligible_patient_cohort` | 5,831,978 | 294,467 providers | 76 | 20 | see section 6 |

The extra NPIs in NB01 / NB04 / NB06 most likely come from the products switched on in the mapping, e.g. HCPs whose only claims are Kerendia, Mounjaro or other GLP-1s that were not in the pull before. Not yet checked per NPI.

---

## 5. Checks done on this run

| Check | Result |
| --- | --- |
| Cohorts per table | 20 in all 11 tables (2025-01_offset7 .. 2026-08_offset7) |
| Duplicate (key, cohort) / empty key, NPI-level tables | 0 / 0 |
| Columns vs 2026-11-04 (6 NPI-level tables) | 0 lost; added only Kerendia columns (NB01 234, NB04 180) |
| Duplicate column names in NB01 (GLP-1 clash) | 0. `TOTAL_RX_CLAIMS_GLP_1_*` is the GLP-1 brand, as in 3.0; there is no GLP-1 treatment-category column |
| Cohort sets vs source (11 tables) | 5 sets x 4 cohorts each; rows equal to the source for every table |

Not redone in this run: the full-input recounts of 2026-11-04 (NB01 8,621 / NB04 96,300 checks, 0 differences). The feature logic is unchanged apart from option C and the new mapping.

---

## 6. Provider tables: `PROVIDER_ID` gaps (O2, still open)

The pattern is the same as on 2026-11-04 (mapping table `kerendia_nba_3_0_npi_bhid_mapping`). The only change is a few more HCPs without an ID, because of the new NPIs.

| Notebook | Rows with empty `PROVIDER_ID` (2026-11-04) | Extra rows from HCPs with 2 IDs (2026-11-04) |
| --- | --- | --- |
| NB01 / NB04 | 2,339 (1,911) | 941 (941) |
| NB03 Dx | 698 (698) | 675 (675) |
| NB06 Eligible | 2,274 (1,828) | 938 (937) |

The proposal is unchanged: keep the mapping table and, for the missing or doubled HCPs only, take the `PROVIDER_ID` of the 3.1 input. Only the provider tables are rewritten.

---

## 7. Next steps and open points

| # | Point | Next step |
| --- | --- | --- |
| – | `HCP_LATEST_FULL_RUN` in `00_cohort_config` | Point to `full_2026_11_05`, so validation runs read this run's pulls |
| O2 | `PROVIDER_ID` gaps (section 6) | Decide and apply the fill / de-duplication |
| X5 | 9 dropped NB04 features (DPP-IV / other glucose) | Write-up |
| – | Validation / backtest cohorts | Plan with Saurabh (today only 20 training cohorts) |
| D6 | Column list depends on the data | Fixed column list |
| O8–O11 | `RUNNING_` meaning, `SGLT2_WO_INVOKANA_300MG`, NB05 zeros, T1D codes | Confirm with Wenjie |
| O7 / O14 | Downstream combine | Wire to `COHORT_ID` and the cohort sets |

Related docs in `Alignment_Markdowns/Strategy_and_Execution/`:
* `NBA_3_1_Product_Mapping_Change_Log_2026_11_05.md`
* `NBA_3_1_HCP_Features_Fill_Missing_and_Lag.md`
* `NBA_3_1_HCP_Features_Decisions.md`
