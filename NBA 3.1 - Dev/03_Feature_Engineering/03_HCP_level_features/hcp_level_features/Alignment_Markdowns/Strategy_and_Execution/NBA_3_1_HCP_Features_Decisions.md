# NBA 3.1 – HCP-level features: decision log

**Date:** 2026-11-03  
**Scope:** HCP feature notebooks NB01–NB06 (`hcp_level_features/`), their inputs from the 3.1 patient journey (PJ01–PJ06), and the run setup.  
**How these were decided:** the project owner asked the team to make the open calls and document them. Each decision below gives the reason and how to reverse it.

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

## 2. Still open (needs the full run or other teams)

| Topic | Waiting for |
| --- | --- |
| ~~PJ03 Step 4d for all HCPs~~ | **Done 2026-11-03** (one-time run 114072068089102, 41 min): `full_2026_11_02/_stage/rx_hcp_pull` = 3,070,618,084 claims, 294,534 NPIs / 294,538 providers (all in the 3.1 universe of 294,727), 113.7 M patients, 2023-01-01 .. 2026-09-30 (350 M `HCP_ONLY` claims). Test HCPs: identical to the validation pull except HCP 1508230566 (2,468 claims, not in the 3.1 universe, X1). Rx journey rewritten with the same 2,840,023,664 patient-months |
| Full HCP run (job 36449327509782, `VALIDATION_MODE=false`, `RUN_OUTPUT_DIR=full_2026_11_02/`) | Next step |
| Patient-journey decisions C1 (SGLT2) and C9 (diabetes) | Patient-journey owners; HCP notebooks only need a re-run |
| HF / diabetes type features (new 3.1 columns) | Phase 2 |

## 3. Jobs (created 2026-11-03, serverless, defaults = validation run)

| Job | ID | Tasks |
| --- | --- | --- |
| NBA 3.1 HCP Level Features (NB01-NB06) | 36449327509782 | NB01–NB06 in parallel; needs a finished patient-journey run in `RUN_OUTPUT_DIR` |
| NBA 3.1 Patient Journey + HCP Features (PJ01-PJ06 -> NB01-NB06) | 1010893614518587 | PJ01–PJ06 as job 953988155823642, then NB01–NB06 in parallel after `pj06_combine` |

Both use the notebooks in `kerendia_nba_3_1_develop_pg` (PJ03 there includes Step 4d). The existing job 953988155823642 points to the copies in `kerendia_nba_3_1_develop_hcp_claims` and was not changed. Parameters (same as 953988155823642): `VALIDATION_MODE`, `RUN_OUTPUT_DIR`, `HCP_UNIVERSE_PATH`, `NPI_BHID_MAPPING_PATH`, `RUN_CHECKS`. Full run: `VALIDATION_MODE=false`, `RUN_OUTPUT_DIR=.../query_output/full_2026_11_02/`.

## 4. Where each decision is documented

* NB04: `04 Monthly Cohort Claims Files/NBA_3_1_Claims_Features_Plan.md` (D2) and client summary
* NB05: `05 Rx NPS Claims Files/NBA_3_1_Rx_NPS_Features_Plan.md` (D1)
* NB06: `06 Eligible HCP Claims Files/NBA_3_1_Eligible_HCP_Features_Plan.md` (D1, F7), client summary, notebook cell "What this notebook does"
