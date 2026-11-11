# NBA 3.1 – HCP-level features: decision log

**Date:** 2026-11-03, updated 2026-11-11  
**Scope:** HCP feature notebooks NB01–NB07 (`hcp_level_features/`), their inputs from the 3.1 patient journey (PJ01–PJ06), and the run setup.  
**How these were decided:** the project owner asked the team to make the open calls and document them. Each decision below gives the reason and how to reverse it.  
**Latest full run:** `full_2026_11_11` (job 1010893614518587, run 441950237921, in progress): 28 cohorts c1–c28, offset 0, claims cohort file, Delta partitioned by COHORT_SET (X14). The previous run `full_2026_11_07` (run 477251413108207, Parquet) was cancelled before NB01 and NB04 finished.

---

## 1. Decisions

| ID | Notebook | Question | Decision | Why | To reverse |
| --- | --- | --- | --- | --- | --- |
| X1 | All | HCP universe | **3.1 universe** (`kerendia_nba_3_1_volume/HCP_Universe_without_call_hcps/`), same as the patient journey. Test HCP 1508230566 is not in it and drops out (9 of 10 test HCPs remain) | One universe for the patient journey and the HCP features | Job parameter `HCP_UNIVERSE_PATH` |
| X2 | NB01, NB04, NB06 | Rx claims source | **3.1 HCP Rx pull** (PJ03 Step 4d, `<run folder>/_stage/rx_hcp_pull`) from `DATA_START_DATE`, `Rx_01_new` before | Same basket and rules as the 3.1 Rx journey | `HCP_RX_SOURCE = "3.0"` in `00_cohort_config` |
| X3 | NB02, NB04 | Lab pull location | **Keep the pull in the run folder** (`<run folder>/_stage/lab_step4_pull`) | It is written by every PJ01 run, so each run folder is complete | `HCP_LAB_SOURCE = "3.0"` |
| X4 | NB03 | Stage 5 columns | **Keep** (new 3.1 stage from the Dx codes) | Real patients in stage 5; dropping them would hide them in "unknown" | Column list in NB03 |
| X5 | NB04 | 9 selected model features with DPP-IV / other glucose (family C) not in the 3.1 patient treatment table | **Keep the patient-journey rule; drop the 9 features from the model list.** The 3.1 model is retrained and its feature selection rerun on the 3.1 output | Changing PJ06 for the HCP features only would make the patient tables differ from the journey used everywhere else | Keep `Other- glucose mgmt` in PJ06's patient treatment table and rerun PJ06 + NB04 |
| X6 | NB04 | 7 selected `..._WITH_GLP_1` features absent for the test HCPs | **No change**; checked in the full run | GLP-1 is in the 3.1 data, only the test HCPs have no such patients | – |
| X7 | NB05 | Rx source for first starts | **Keep 3.0 `Rx_05`** (all HCPs since 2021) | A first start needs the full history of every HCP; the 3.1 pull starts at `DATA_START_DATE`. Output identical for the test HCPs | Revisit when new drugs join the basket |
| X8 | NB06 | Window rule (`_IN_LAST_N_MONTH`) | **Sum of the last N monthly counts.** 3.0 stored the mean of N+1 monthly counts | Same rule as NB01–NB05 and the column names; base-month, `RUNNING_` and dialysis logic unchanged; the selected NB06 feature is a `RUNNING_` column | Average in NB06's window step |
| X9 | NB06 | Offset-0 parity failure (6,264 window cells) | **Accepted**, explained by X8 | Base-month counts match 3.0 (0 of 171 mismatches) | – |
| X10 | All | Run folder | **One folder per run** (`RUN_OUTPUT_DIR`): validation `validation_2026_10_30/`, full `full_2026_11_02/`; HCP feature outputs go to `notebook_output/` | Same as PJ01–PJ06 | Job parameter `RUN_OUTPUT_DIR` |
| X11 | All | Orchestration | **One job for NB01–NB06** (all six run in parallel, as they do not read each other), with the same parameters as the patient-journey job (953988155823642) | Same pattern as PJ01–PJ06; NB04 reads the inputs, not the NB01–NB03 outputs | – |
| X12 | Config | `HCP_CLAIMS_LAB_TABLE` missing in `HCP_SOURCE_TABLES` (common end date) | **Not changed now** (same end date as `Lab_04` today); add when the lab pull end date can differ | No impact today | – |
| X13 | All | Cohort source | **Claims cohort file** (`cohorts/claims/cohorts.parquet`): 28 cohorts c1–c28, offset 0 (calendar months), `COHORT_ORIGIN=2024-05`, `COHORT_LAST=2026-08`. Replaces the 20 inline cohorts at offset 7 | Standard cohort grid aligned with the model training plan; offset 0 = calendar months | `COHORT_MONTHS` list in `00_cohort_config` |
| X14 | All | Output format | **Delta partitioned by COHORT_SET**, with optimizeWrite (few large files per group). 7 groups: C1-C5_training, C6-C10_training, C11-C15_training, C16-C20_training, C21-C24_training, C25-C26_validation, C27-C28_backtesting. Replaces Delta partitioned by COHORT_ID. **History:** the 2026-11-07 run wrote Parquet by COHORT_SET, which gave about 455,000 files of about 8 rows per table (NB01: 906 GB, 75% of it file metadata) and very slow reads and QC; switched to Delta on 2026-11-11 (test on one group of NB01: 12 files / 5.4 GB instead of 64,998 / 121 GB, read 0.7 s instead of 215 s) | Downstream consumers read one training/validation/backtesting set at a time; 7 groups instead of 28 cohorts. Delta keeps the files large and the reads fast, as in 3.0 | `write_hcp_output` / `read_hcp_output` in `00_cohort_config` (the reader also reads older Parquet runs) |
| X15 | NB07 | Cohort-set splitting | **NB07 is check-only** (no longer splits tables). The 7 COHORT_SET groups are written directly by `write_hcp_output` in each notebook | Splitting is no longer needed: the write step already partitions by COHORT_SET | Re-add the split logic in NB07 |
| X16 | NB01 | Kerendia brand features | **Added:** 234 Kerendia brand features (`TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_{1,3,6,12}_MONTH`, age/gender/payer/supply/refill/running cross-cuts, rejection). Kerendia is now in the Rx product basket (2026-11-05 mapping update) | Kerendia Rx visibility is a core 3.1 requirement | Remove Kerendia from the basket |
| X17 | NB01 | 6 removed treatment categories | **Removed:** 979 features for ACE_OR_ARB, CALCIUM_CHANNEL_OR_BETA_BLOCKER, COMBO_DRUG, DIURETIC_NON_MRA, INSULIN, METFORMIN. These categories are outside the 3.1 HCP brand list | Focus on the drugs relevant to Kerendia prescribers | Re-add the categories to the brand filter |
| X18 | NB02 | HbA1c and Potassium lab features | **Added:** 48 features for HbA1c ≥ 9 and Potassium > 5 (total tested, total/eligible above threshold, PCT, each × 4 windows). Potassium LOINC 2823-3, HbA1c LOINC 4548-4 | Kerendia safety monitoring (hyperkalemia) and diabetes control | Remove the lab flag code in NB02 |
| X19 | NB02 | 9-month lookback window | **Removed:** 21 features with `IN_LAST_9_MONTH`. Windows standardized to [1, 3, 6, 12] months across all notebooks | Consistency with NB01, NB03–NB06 | Add 9 back to `HCP_LOOKBACK_WINDOWS["lab"]` |
| X20 | NB06 | Diabetes and HF type features | **Added:** 128 DM/HF type features (`DM_TYPE_{NONE,OTHER,T1D,T2D}`, `HF_TYPE_{NONE,HFPEF,HFREF,HF_UNSPECIFIED}`, total/eligible × Rx/eligible patients × 4 windows) + 20 HF eligibility features. Source: PJ04 `dm_hf_flags` table. **Dropped (−15):** old GFR/UACR stage breakdowns (stages UNKNOWN, 2, 3, 4) replaced by the new windowed family structure | Kerendia indications: CKD with T2D and HF with LVEF ≥ 40% | Remove the DM/HF code in NB06; re-add old stage columns |
| X21 | Config | `write_hcp_output` return type | **Returns `spark.read.parquet(path)`** (was: path string). Required for `.transform(lambda _d: write_hcp_output(...))` in NB04 and NB06 | `.transform()` needs a DataFrame return | Return the path string |
| X22 | Config | `builtins.sum` in self-test | **Uses `builtins.sum`** (was: bare `sum`). PJ notebooks star-import `pyspark.sql.functions`, which replaces Python's `sum` with Spark's | Config code is called from PJ notebooks that shadow `sum` | – |
| X23 | All | Null-count QC batching | **Batched in groups of 200 columns** (was: single-pass `F.sum(isNull)` over all columns). NB01 (~4,668 cols) and NB04 (~3,065 cols) stalled 15+ hours on serverless with the single-pass approach | Spark Connect plan compiler cannot handle ~4,500 sum expressions in one query | Single-pass (if plan compiler is fixed) |
| X24 | All | `HCP_ALLOW_OVERWRITE` parameter | **New job parameter** (`false` default, `true` for repairs). When true, `hcp_output_path()` allows overwriting an existing table | Repairs need to re-run notebooks whose NPI-level tables already exist | Remove the parameter |

## 2. Still open (needs the full run or other teams)

| Topic | Status |
| --- | --- |
| ~~PJ03 Step 4d for all HCPs~~ | **Done 2026-11-03** |
| ~~Full HCP run (20 cohorts, offset 7)~~ | **Done 2026-11-04/05** (job 36449327509782) |
| Full HCP run (28 cohorts, offset 0, claims cohort file, Delta) | **In progress 2026-11-11** (job 1010893614518587, run 441950237921, `full_2026_11_11/`). The 2026-11-07 Parquet run (477251413108207) was cancelled: NB01 and NB04 were still in the QC step after more than 5 hours |
| ~~HF / diabetes type features~~ | **Done 2026-11-06** (X20): 128 DM/HF type + 20 HF eligibility features in NB06 |
| ~~HbA1c / Potassium lab features~~ | **Done 2026-11-06** (X18): 48 lab flag features in NB02 |
| ~~Kerendia brand features~~ | **Done 2026-11-05** (X16): 234 Kerendia features in NB01, product mapping updated |
| Patient-journey decisions C1 (SGLT2) and C9 (diabetes) | Patient-journey owners; HCP notebooks only need a re-run |
| `PROVIDER_ID` gaps (O2) | 105 HCPs without an ID, 52 with two IDs. Proposal: fill from the 3.1 Rx input. Not applied yet |
| Null-count QC timing | On the Parquet output one 200-column pass took about 100 s per group; on Delta the same pass took 2 s in the test. Check the QC time in `full_2026_11_11`; skip the full null count in full runs only if it is still slow |
| Update `HCP_LATEST_FULL_RUN` | Point to `full_2026_11_11` after the run finishes and passes its checks |
| Job 36449327509782 | Still points at the 3.0 volume; update or retire |

## 3. Jobs (created 2026-11-03, serverless)

| Job | ID | Tasks | Status |
| --- | --- | --- | --- |
| NBA 3.1 HCP Level Features (NB01-NB06) | 36449327509782 | NB01–NB06 in parallel | Still points at the 3.0 volume; needs update or retirement |
| NBA 3.1 Patient Journey + HCP Features (PJ01-PJ06 -> NB01-NB07) | 1010893614518587 | PJ01–PJ06, then NB01–NB06 in parallel, then NB07 | **Current job.** Parameters: `VALIDATION_MODE`, `RUN_OUTPUT_DIR`, `EXPECTED_COHORTS` (28), `HCP_ALLOW_OVERWRITE` |

## 4. Where each decision is documented

* X1–X12: this file (original decisions, 2026-11-03)
* X13–X24: this file (decisions made 2026-11-05 through 2026-11-07, added 2026-11-11)
* NB04: `04 Monthly Cohort Claims Files/NBA_3_1_Claims_Features_Plan.md` (D2) and client summary
* NB05: `05 Rx NPS Claims Files/NBA_3_1_Rx_NPS_Features_Plan.md` (D1)
* NB06: `06 Eligible HCP Claims Files/NBA_3_1_Eligible_HCP_Features_Plan.md` (D1, F7), client summary, notebook cell "What this notebook does"
* Feature comparison: `Review_and_Findings/NBA_3_1_HCP_Features_E2E_Full_Run_2026_11_07.md` (section 4)
* Product mapping update: `Strategy_and_Execution/NBA_3_1_Product_Mapping_Change_Log_2026_11_05.md`

## 5. Feature counts (full run `full_2026_11_07`, 28 cohorts)

| Notebook | Table | 3.0 features | 3.1 features | New | Dropped | Net |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| NB01 | `claim_rx_monthly_cohort` | 5,411 | 4,668 | +236 | −979 | −743 |
| NB02 | `claim_lab_monthly_cohort` | 116 | 143 | +48 | −21 | +27 |
| NB03 | `claim_diagnosis_monthly_cohort` | 104 | 113 | +9 | 0 | +9 |
| NB04 | `claims_monthly_cohort` | 1,571 | 3,065 | +1,494 | 0 | +1,494 |
| NB05 | `claim_rx_nps_monthly_cohort` | 154 | 154 | 0 | 0 | 0 |
| NB06 | `claim_eligible_patient_cohort` | 84 | 217 | +148 | −15 | +133 |
| **Total** | | **7,440** | **8,360** | **+1,935** | **−1,015** | **+920** |
