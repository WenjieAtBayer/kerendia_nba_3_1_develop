# NBA 3.1 Adoption Features (Invokana, Farxiga): Changes

> **Data source update (Nov 2026):** NBA 3.1 now reads `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7` (LAAD-based LRx V7, weekly, history from Dec 2021) instead of `KERENDIA_LAAD_BASED_LRX_V6` and `KERENDIA_LAAD_BASED_LRX_FULL_DATA_STARTING_2021`. Read V6 references below as V7. V7 `WEEK_ENDING_DATE` / `PERIOD_ID` are DATEs, and `PRODUCT_GROUP` uses the shorter lrx_nbrx names. Numbers in this document were computed on V6.

This file lists the adoption-feature changes for NBA 3.1: the three adoption features to build per drug group (section 1), and why the drug groups beyond Invokana and Farxiga were chosen (section 2). How the NBA 3.0 features are built is in the companion file `NBA_3_1_Adoption_Features_Inv_Far_Analysis.md`. References written as "Analysis 1.x" point to sections in that file.

NBA 3.1 scope:

* The model target is still the HCP's **Kerendia NBRx in the 30-day prediction window**.
* The features are built for **Invokana and Farxiga** (as in NBA 3.0), plus **Jardiance, a steroidal MRA group and Entresto** (chosen in section 2).

The idea behind the family stays the same: an HCP who quickly puts CKD patients on a newer, guideline-backed therapy is likely to adopt Kerendia too.

SHAP ranks and shares come from `Final NBA 3.0 Modeling Features.xlsx` (752 features, mean absolute SHAP).

**How the signal was measured (backtest, rerun 2026-11-02 on the NBA 3.1 universe).** The section 1 features are read from the NBA 3.1 output of `11_adoption_features` for cohort c26 (`lookback_end_date` 2026-06-01, so claims up to 2026-06-30 only), built from the NBA 3.1 inputs `query_output/Rx_01_new` and `query_output/Dx_03` (CKD codes), with all claim types as in the NBA 3.0 notebook. The target is "the HCP wrote at least one Kerendia NBRx in August 2026", from `KERENDIA_LAAD_BASED_LRX_V6` with `PRODUCT_GROUP = 'KERENDIA'`. Population: the 314,920 HCPs in the NBA 3.1 universe (`kerendia_nba_3_1_volume/HCP_Universe/`), 6,704 writers, base rate 2.13%.

* **AUC (speed)**: for a days feature, the chance that a random writer has a **smaller** value (faster) than a random non-writer, over HCPs with a non-empty value. 0.50 = no signal. Above 0.50 = faster HCPs write more Kerendia. Below 0.50 = slower HCPs write more.
* **AUC in size**: median AUC inside 3 equal groups of all-market NBRx (January to June 2026).
* **AUC new writers**: AUC among the 268,086 HCPs with no Kerendia NBRx since January 2023 (rate 0.55%, 22.0% of August writers).

---

## 1. Adoption features for NBA 3.1

Build these three features for the drug groups in 1.0. The first one is the NBA 3.0 feature with a clearer name.

| # | Feature | Replaces / new | Definition |
| --- | --- | --- | --- |
| 1 | `MIN_DAYS_TO_PRESCRIBE_{DRUG}_POST_CKD_DIAGNOSIS` | Renames `TIME_TO_ADOPT_{DRUG}` | Fewest days, over the HCP's patients, from the patient's first CKD diagnosis **by this HCP** to the patient's first Rx for the drug from this HCP |
| 2 | `HCP_TIME_TO_ADOPT_{DRUG}` | New | Days from the drug's FDA approval to the HCP's first-ever Rx for the drug (any patient). Not built for the steroidal MRA group |
| 3 | `MIN_DAYS_TO_PRESCRIBE_{DRUG}_POST_FIRST_CKD_DIAGNOSIS_ANY_HCP` | New | Same as #1, but from the patient's first CKD diagnosis by **any** provider |

### 1.0 Drug groups

| `{DRUG}` | `PRODUCT_NAME` values in `Rx_01_new` | Class | Why |
| --- | --- | --- | --- |
| `INVOKANA` | `INVOKANA` | SGLT2 | NBA 3.0 feature |
| `FARXIGA` | `FARXIGA` | SGLT2 | NBA 3.0 feature |
| `JARDIANCE` | `JARDIANCE` | SGLT2 | Section 2 |
| `STEROIDAL_MRA` | `SPIRONOLACTONE`, `EPLERENONE` | Steroidal MRA | Section 2 |
| `ENTRESTO` | `ENTRESTO` | ARNI (HF) | Section 2 |

For a group with more than one product (`STEROIDAL_MRA`), the patient's first Rx date is the first Rx for **any** product in the group from this HCP.

#1 and #3 for all 5 drug groups, #2 for the 4 groups with a launch date = **14 columns**, for example `MIN_DAYS_TO_PRESCRIBE_FARXIGA_POST_CKD_DIAGNOSIS` or `MIN_DAYS_TO_PRESCRIBE_STEROIDAL_MRA_POST_FIRST_CKD_DIAGNOSIS_ANY_HCP`.

### 1.1 `MIN_DAYS_TO_PRESCRIBE_{DRUG}_POST_CKD_DIAGNOSIS` (#1, renamed NBA 3.0 feature)

The logic is unchanged from the NBA 3.0 notebook (Analysis 1.2). Only the name changes, because "time to adopt" suggests days since launch (that is #2), while the feature measures days from CKD diagnosis to the first Rx.

1. **HCP-patient CKD date**: `MIN(SVC_DT)` from `Dx_03`, grouped by (`PROVIDER_ID`, `PATIENT_ID`).
2. **HCP-patient Rx date**: `MIN(SVC_DT)` from `Rx_01_new` for the drug, grouped by (`PROVIDER_ID`, `PATIENT_ID`).
3. **Join** on `PROVIDER_ID` + `PATIENT_ID`, so only patients this HCP both diagnosed and prescribed count.
4. **Gap**: `DATEDIFF(first Rx, first CKD)`. Drop negatives (patients on the drug before the CKD code).
5. **Rollup**: minimum per HCP. Empty for HCPs with no such patient.

As in NBA 3.0, Dx and Rx dates are taken on or after the drug's CKD-indication date: 2019-10-01 for Invokana (before the data start, so no effect) and 2021-04-01 for Farxiga. The new groups (Jardiance, steroidal MRA, Entresto) use the full history from 2021-01-02. The same floors apply to #3.

### 1.2 `HCP_TIME_TO_ADOPT_{DRUG}` (#2)

Built for Invokana, Farxiga, Jardiance and Entresto. **Not built for the steroidal MRA group**: spironolactone has been on the market since 1960, so the group has no meaningful launch date.

Days from the drug's FDA approval to the HCP's first Rx for the drug (`MIN(SVC_DT)` from `Rx_01_new` per `PROVIDER_ID`, any patient, no diagnosis needed). Empty if the HCP never wrote the drug before the lookback end.

| Drug | FDA approval (confirm with Medical) |
| --- | --- |
| Invokana | 2013-03-29 |
| Farxiga | 2014-01-08 |
| Jardiance | 2014-08-01 |
| Entresto | 2015-07-07 |

**Limitation**: all approvals are before the claims start (2021-01-02). An HCP who already wrote the drug before 2021 gets their first Rx in the data (early 2021) instead of their real first Rx. So the feature cannot tell early adopters from HCPs who started in 2020, and it mostly separates HCPs who started **after** 2021. An alternative with an approval inside the data is the Farxiga CKD indication (April 2021), with days to the first Farxiga Rx in a CKD patient.

### 1.3 `MIN_DAYS_TO_PRESCRIBE_{DRUG}_POST_FIRST_CKD_DIAGNOSIS_ANY_HCP` (#3)

For each prescribing HCP-patient pair, use the patient's first CKD date from **any** provider, not just this HCP. An HCP who receives referred patients (diagnosed by a PCP, then treated by a nephrologist) gets credit for them.

1. **Patient-level CKD date**: `MIN(SVC_DT)` from `Dx_03`, grouped by `PATIENT_ID` only (no `PROVIDER_ID` in the group-by).
2. **Prescriber Rx date**: unchanged, `MIN(SVC_DT)` from `Rx_01_new` grouped by (`PROVIDER_ID`, `PATIENT_ID`).
3. **Join on `PATIENT_ID`**: match every prescribing HCP's patient to that patient's global first CKD date, regardless of who diagnosed.
4. **Gap and rollup**: same as today. `DATEDIFF(first Rx, first CKD)`, drop negatives, take the minimum per HCP.

### 1.4 Backtest of the three features

Cutoff 2026-06-30, all claim types, NBA 3.1 inputs. "Non-empty" = share of the 314,920 HCPs with a value. Median = median value over HCPs with a value (days).

| Drug group | Feature | Non-empty | Median | AUC (speed) | AUC in size | AUC new writers |
| --- | --- | --- | --- | --- | --- | --- |
| Farxiga | #1 Min, same HCP | 41.6% | 36 | 0.666 | 0.656 | 0.568 |
| Farxiga | #2 Time since approval | 90.3% | 2,928 | 0.591 | 0.531 | 0.479 |
| Farxiga | #3 Min, any HCP | 69.2% | 120 | **0.706** | **0.695** | 0.569 |
| Invokana | #1 Min, same HCP | 6.0% | 91 | 0.565 | 0.541 | 0.524 |
| Invokana | #2 Time since approval | 44.6% | 2,945 | 0.548 | 0.482 | 0.477 |
| Invokana | #3 Min, any HCP | 11.7% | 245 | 0.596 | 0.593 | 0.526 |
| Jardiance | #1 Min, same HCP | 54.7% | 19 | 0.628 | 0.613 | 0.565 |
| Jardiance | #2 Time since approval | 95.0% | 2,517 | 0.542 | 0.456 | 0.448 |
| Jardiance | #3 Min, any HCP | 83.5% | 70 | **0.679** | **0.659** | 0.574 |
| Steroidal MRA | #1 Min, same HCP | 44.5% | 37 | 0.614 | 0.608 | 0.559 |
| Steroidal MRA | #3 Min, any HCP | 77.2% | 74 | **0.645** | **0.624** | **0.575** |
| Entresto | #1 Min, same HCP | 21.0% | 79 | 0.543 | 0.493 | **0.581** |
| Entresto | #2 Time since approval | 74.3% | 2,474 | 0.574 | 0.525 | 0.544 |
| Entresto | #3 Min, any HCP | 45.0% | 155 | 0.575 | 0.529 | **0.585** |

The Farxiga #1 value (0.666) is in line with the NBA 3.0 feature (0.66, rank 13, 1.10% SHAP), so the backtest reproduces the current build.

Correlation (Spearman, HCPs with both values) between #1 and #3: 0.63 to 0.75 across the five groups (Farxiga 0.68). They overlap, but are not duplicates.

What this shows:

* **#3 (minimum, any-provider CKD date) is the best feature for every group.** It is stronger than #1 and covers more HCPs (Farxiga 69.2% vs 41.6%), because nephrologists who treat referred patients now get a value.
* **#1 and #3 partly measure volume**: the minimum gets smaller when the HCP treats more CKD patients with the drug. An average gap per HCP (the HCP's usual speed) was also tested and had no signal for any group (0.44 to 0.54), so it is not built.
* **#2 (time since approval) is weak, and within size groups it is 0.46 to 0.53** (Jardiance 0.456: within the same size, HCPs whose first Jardiance claim came later write more Kerendia). The pre-2021 limitation in 1.2 applies to every group.
* **Entresto** is the best group for new writers (#1 0.581, #3 0.585), but weaker overall.
* **Invokana** is small (6% of HCPs for #1) and its signal is weak. It is kept because it is part of this feature family.

**Decision**: build #1 and #3 for all five drug groups and #2 for Invokana, Farxiga, Jardiance and Entresto (14 columns). Keep both #1 and #3 (0.63 to 0.75 correlation). Expect #2 to be dropped in feature selection.

### 1.5 Build notes

* **Per cohort**: the NBA 3.0 output is one static row per HCP built with all claims (Analysis 1.4), so training rows see future prescribing. Build each feature per claims cohort (`kerendia_nba_3_1_volume/cohorts/claims/cohorts.parquet`) with `SVC_DT` up to the cohort's `lookback_end_date`, and join on `HCP_COHORT_ID`.
* **Claim types**: as in NBA 3.0 (all claim types in `Rx_01_new`).
* **Inputs**: the NBA 3.1 `Dx_03` and `Rx_01_new` in `kerendia_nba_3_1_volume/hcp_level_model/ops_pipeline/query_output/`. `00_Write_HCP_Inputs_31` pulls `Rx_01_new` for the five drug groups only (`RX_ADOPTION_ONLY = True`, product list `ADOPTION_PRODUCTS`: Invokana, Farxiga, Jardiance, spironolactone, eplerenone, Entresto). Run it with job parameter `files = Rx_01_new` to refresh only that file.
* **Notebook**: `NBA 3.1 - Dev/03_HCP_Level_Features/11_adoption_features` (replaces `11_adoption_features_inv_far`). Output `kerendia_nba_3_1_volume/notebook_output/hcp_features/adoption_features`. Join in `99_Combine_Physician_Data` on `HCP_COHORT_ID` instead of `PROVIDER_ID`.

---

## 2. Other drugs for these features

**Question**: besides Invokana and Farxiga, which drugs give a useful adoption signal for Kerendia NBRx?

The same backtest was run for every large cardio-renal-metabolic brand (#1 and #3 shown), with claims up to 2026-06-30 and the NBA 3.1 `Dx_03` for the CKD dates. The chosen groups are backtested on all three features in 1.4.

* Farxiga, Jardiance, Spironolactone, Eplerenone, Entresto and Invokana use the NBA 3.1 `Rx_01_new`, which covers the whole 3.1 universe.
* The other brands (marked \*) are not in the NBA 3.1 `Rx_01_new` (it only holds the adoption products), so they use the NBA 3.0 `Rx_01_new`. That file only covers the 223,050 HCPs that are in both universes. The other 91,870 HCPs of the 3.1 universe are empty for these brands, so their non-empty shares are a lower bound (for losartan #3, 95.2% of the covered HCPs have a value). None of the 91,870 HCPs wrote Kerendia in August 2026, so the AUCs are computed on the same writers.

| Drug | Class | #1 non-empty | #1 AUC / in size / new writers | #3 non-empty | #3 AUC / in size / new writers |
| --- | --- | --- | --- | --- | --- |
| Farxiga (reference) | SGLT2 | 41.6% | 0.666 / 0.656 / 0.568 | 69.2% | 0.706 / 0.695 / 0.569 |
| **Jardiance** | SGLT2 | 54.7% | 0.628 / 0.613 / 0.565 | 83.5% | **0.679 / 0.659** / 0.574 |
| **Spironolactone** | Steroidal MRA | 43.9% | 0.612 / 0.608 / 0.562 | 76.6% | **0.643 / 0.623 / 0.574** |
| Losartan \* | ARB | 49.8% | 0.612 / 0.600 / 0.535 | 67.5% | 0.638 / 0.619 / 0.506 |
| Lisinopril \* | ACE inhibitor | 47.6% | 0.584 / 0.605 / 0.533 | 66.9% | 0.598 / 0.581 / 0.486 |
| **Entresto** | ARNI (HF) | 21.0% | 0.543 / 0.493 / **0.581** | 45.0% | 0.575 / 0.529 / **0.585** |
| Eplerenone | Steroidal MRA | 4.7% | 0.572 / 0.570 / 0.511 | 13.0% | 0.599 / 0.604 / 0.555 |
| Invokana (reference) | SGLT2 | 6.0% | 0.565 / 0.541 / 0.524 | 11.7% | 0.596 / 0.593 / 0.526 |
| Rybelsus \* | GLP-1 | 17.2% | 0.579 / 0.537 / 0.553 | 29.5% | 0.591 / 0.526 / 0.512 |
| Ozempic \* | GLP-1 | 39.7% | 0.562 / 0.506 / 0.524 | 56.6% | 0.572 / 0.493 / 0.485 |
| Trulicity \* | GLP-1 | 27.2% | 0.537 / 0.498 / 0.514 | 44.4% | 0.564 / 0.491 / 0.485 |
| Victoza \* | GLP-1 | 8.1% | 0.506 / 0.504 / 0.482 | 16.2% | 0.552 / 0.526 / 0.523 |
| Synjardy XR \* | SGLT2 combo | 3.4% | 0.555 / 0.553 / 0.500 | 7.5% | 0.572 / 0.477 / 0.442 |
| Xigduo XR \* | SGLT2 combo | 2.5% | 0.540 / 0.511 / 0.395 | 5.7% | 0.560 / 0.483 / 0.466 |

What this shows:

* **Jardiance** is the strongest drug after Farxiga and covers the most HCPs (83.5% for #3). It is the largest SGLT2 brand with a CKD indication, so it fills the gap for HCPs who use Jardiance instead of Farxiga.
* **Spironolactone** (steroidal MRA) holds its signal within size groups (0.608 to 0.623) and has one of the best new-writer values (0.574). Kerendia is a non-steroidal MRA, so HCPs who already start CKD patients on an MRA are the closest to adding Kerendia. Eplerenone has the same pattern but covers few HCPs. Combine both as a steroidal MRA group.
* **Entresto** has the best new-writer signal of all drugs (0.58 to 0.59). It marks HF prescribers, which matters for the new Kerendia HF indication (LVEF >= 40%).
* **Losartan and lisinopril** (RAAS blockers, the first CKD treatment step) have signal, but almost every HCP writes them (about 95% of the HCPs covered by the input), and new-writer signal is close to 0.50. They mostly measure how many CKD patients the HCP treats. Lower priority. If added, build one ACE inhibitor / ARB group.
* **GLP-1 brands** lose their signal within size groups (0.49 to 0.54). Do not add.
* **SGLT2 combos** (Synjardy XR, Xigduo XR) are too small to use alone.

**Decision**: add the section 1 features for **Jardiance**, a **steroidal MRA group** (spironolactone + eplerenone, without #2) and **Entresto**. As a group, the steroidal MRA features are about the same as spironolactone alone (#3: 0.645 vs 0.643), with slightly more HCPs (77.2% vs 76.6%). Optional: one ACE inhibitor / ARB group, if feature selection keeps it. Do not add GLP-1 brands.

**Not testable in the current data**: Kerendia itself (would only describe current writers, and is not in `Rx_01_new`), Mounjaro and generic dapagliflozin (not in `Rx_01_new`). Generic dapagliflozin should be added to the Farxiga group in the 3.1 input pull, because it has about 4 times the NBRx of Farxiga brand.

