# Kerendia NBA 3.1 – HCP-Level Features: End-to-End Full Run (2026-11-04)

**Scope:** the six HCP feature notebooks (NB01–NB06) run for the full 3.1 HCP universe, 20 cohorts 2025-01 .. 2026-08 at offset 7  
**Inputs:** patient-journey run folder `query_output/full_2026_11_02/` (3.1 universe, 294,727 providers)  
**Outputs:** `notebook_output/` (one NPI-level and one provider-level table per notebook; NB05 provider-level only)  
**Status:** all six outputs written and checked. Open: `PROVIDER_ID` mapping of the provider tables (section 6), plus the decisions in section 8

---

## 1. In short

* **All six notebooks are written for the full universe:** about 294K HCPs, 20 cohorts, no duplicate keys and no empty cells in the NPI-level tables.
* **268 of the 277 selected model features are present.** The 9 missing are the DPP-IV / other glucose features of NB04 that leave the model list (decision X5). The 7 GLP-1 features (X6) are present and populated.
* **Recounts from the full inputs match:** NB01 8,621 checks, NB04 96,300 checks, NB06 8 test HCPs, all with 0 differences.
* **More columns than in validation** (NB01 4,441 instead of 3,693, NB04 2,892 instead of 1,785). The columns are built from the values found in the data, and rare values only show up with all HCPs. No selected feature is among the extra columns and no validation column is lost (section 5).
* **Provider tables (open item):** 105 HCPs (NB01 / NB04) have no `PROVIDER_ID` and 52 appear twice. The NPI → `PROVIDER_ID` mapping table (`kerendia_nba_3_0_npi_bhid_mapping`, the agreed BHID-NPI mapping) is correct for all other HCPs; it misses or doubles these. The 3.1 inputs have one `PROVIDER_ID` for each of them (section 6).

---

## 2. Runs

| Step | Run | Result |
| --- | --- | --- |
| Patient journey PJ01–PJ06 (3.1 universe) | Job 953988155823642, run 1066154679479482 (2026-11-02) | Patient tables + lab and Dx pulls in `full_2026_11_02/` |
| HCP Rx pull (PJ03 Step 4d) | One-time run 114072068089102 (2026-11-03, 41 min) | `_stage/rx_hcp_pull`: 3.07B claims, 294,534 NPIs, all in the 3.1 universe |
| HCP job NB01–NB06 | Job 36449327509782, run 361860399857197 (2026-11-03) | Attempt 1: all six stopped at 37 min (serverless "transient issue"). Attempt 2: NB02 (15 min), NB03 (42), NB05 (57), NB06 (53) succeeded; NB01 ran out of memory (53 min), NB04 failed (99 min) |
| Re-run NB01 + NB04 | Same job, run 1050221322333806 (2026-11-04) | NB01 success (198 min), NB04 success (195 min) |

**Cause of the NB01 / NB04 failures:** a check cell compared the two engines by loading two full cohorts (all HCPs, about 4,400 columns) into the notebook's memory. **Fix:** in full mode that check, and NB01's table preview, use the trace HCPs only. The features and the write step are unchanged.

---

## 3. Output tables

| Table | Rows | HCPs | Columns | Duplicate keys | Empty cells |
| --- | --- | --- | --- | --- | --- |
| `claim_rx_monthly_cohort` (NB01) | 5,830,945 | 294,503 NPIs | 4,441 | 0 | 0 |
| `provider_claim_rx_monthly_cohort` | 5,831,886 | 294,450 providers | 4,441 | see section 6 | `PROVIDER_ID` only |
| `claim_lab_monthly_cohort` (NB02) | 3,803,309 | 199,335 NPIs | 102 | 0 | 0 |
| `provider_claim_lab_monthly_cohort` | 3,803,718 | 199,362 providers | 102 | 0 | 0 |
| `claim_diagnosis_monthly_cohort` (NB03) | 5,518,531 | 283,010 NPIs | 120 | 0 | 0 |
| `provider_claim_diagnosis_monthly_cohort` | 5,519,206 | 283,015 providers | 120 | see section 6 | `PROVIDER_ID` only |
| `claims_monthly_cohort` (NB04) | 5,830,945 | 294,503 NPIs | 2,892 | 0 | 0 |
| `final_claims_monthly_cohort` | 5,831,886 | 294,450 providers | 2,892 | see section 6 | `PROVIDER_ID` only |
| `claim_rx_nps_monthly_cohort` (NB05) | 4,645,269 | 234,178 providers | 161 | 0 | 0 |
| `claim_eligible_patient_cohort` (NB06) | 5,828,621 | 294,443 NPIs | 76 | 0 | 0 |
| `provider_claim_eligible_patient_cohort` | 5,829,558 | 294,394 providers | 76 | see section 6 | `PROVIDER_ID` only |

Every table has the 20 cohorts. NB05 stays on the NBA 3.0 new-start input (X7), so it covers fewer HCPs.

---

## 4. Checks

### 4.1 Selected model features (277)

| Notebook | Selected | Present in the full output |
| --- | --- | --- |
| NB01 (incl. 2 shared with NB04) | 172 | 172 |
| NB03 | 3 | 3 |
| NB04 | 87 | 78 (the 9 DPP-IV / other glucose features, X5) |
| NB05 | 14 | 14 |
| NB06 | 1 | 1 |
| **Total** | **277** | **268** |

### 4.2 Recounts from the full inputs

Each recount rebuilds the feature values in pandas from the full inputs of `full_2026_11_02/` and compares them with the written table, for every cohort.

| Notebook | HCPs | What is checked | Checks | Differences |
| --- | --- | --- | --- | --- |
| NB01 Rx | 1386651560, 1528629052, 1841364841 | Drug class, brand, rejected claims, payer, gender, total and `RUNNING_` total (5,389); columns without claims are 0 (592); drug classes add up to the total (240); the 72 patient-treatment columns with the full patient table (2,400) | 8,621 | **0** |
| NB04 Combined | same 3 HCPs | Every count column (1,605 per row): total, patient stage (A), same-day test (B), stage x treatment (C), windows and `RUNNING_` | 96,300 | **0** |
| NB06 Eligible | 8 test HCPs | Eligible patients per stage, from the full inputs | all | **0** |

NB02, NB03 and NB05 have been checked for completeness (rows, cohorts, duplicates, empty cells) and selected features; there is no full-input recount for them yet. Their logic was recounted on the test HCPs (client summaries).

### 4.3 Validation run vs full run (test HCPs in both)

| Notebook | Same values | Different values | Why |
| --- | --- | --- | --- |
| NB01 | 3,615 claim columns, 8 HCPs | 72 patient-treatment columns (6,369 values) | The patient tables come from a different patient-journey run: the validation run used the 3.0 universe (empty `HCP_UNIVERSE_PATH`), the full run the 3.1 universe |
| NB04 | Totals and same-day test columns (B) | Patient stage (A) and stage x treatment (C) | Same reason |
| NB06 | – | 0–13% per value | Same reason (patient table `sglt2_filter_m`) |

HCP 1508230566 is not in the full run: it is not in the 3.1 universe. The Rx, lab and Dx claims of the other test HCPs are the same in both runs.

---

## 5. Why the full run has more columns

The count columns are built from the values that appear in the data (as in NBA 3.0). With 294K HCPs, rare values show up that the 10 test HCPs never had. All validation columns are still there.

| Notebook | Validation | Full run | Extra | Of which counts / shares / `RUNNING_` | Selected among extra |
| --- | --- | --- | --- | --- | --- |
| NB01 | 3,693 | 4,441 | 748 | 332 / 332 / 84 | 0 |
| NB04 | 1,785 | 2,892 | 1,107 | 492 / 492 / 123 | 0 |

**NB01 extra values** (last cohort, last 12 months, all HCPs):

* Gender "U": 94,106 claims from 12,549 HCPs.
* Empty days supply (`DAYS_SUPPLY_UNKNOWN` per drug class / brand): 1,999 claims from 1,607 HCPs.
* Young patients (age groups 0–10, 10–20, 20–30, mainly brands), and Cash / Medicare for some brands.
* One claim whose patient birth year is after the service date. It gets a negative age, and the column name becomes `..._AGE_GROUP_10_0` (from "-10_0"). It is a data-quality case, kept as in NBA 3.0.

**NB04 extra values:** stage x drug combinations that the test HCPs did not have, for example GLP-1 or Invokana claims of patients at each GFR / UACR stage, or same-day tests for more drug classes.

The column list therefore depends on the data of the run. Open point D6 (a fixed column list) would make it stable between runs.

---

## 6. Provider tables: empty and repeated `PROVIDER_ID`

The provider tables map each NPI to a `PROVIDER_ID` with `query_output/kerendia_nba_3_0_npi_bhid_mapping` (config `HCP_NPI_MAPPING_TABLE`; 1.57M NPIs). This is the agreed BHID-NPI mapping and it stays the source. It is correct for almost all HCPs: for 294,345 of the 294,346 NB01 HCPs with one ID in it, the 3.1 Rx input has the same `PROVIDER_ID` (1 HCP differs). Two gaps:

| Notebook | HCPs not in the 3.0 mapping | Rows with empty `PROVIDER_ID` | HCPs with 2 `PROVIDER_ID`s | Extra rows |
| --- | --- | --- | --- | --- |
| NB01 / NB04 | 105 | 1,911 | 52 | 941 |
| NB02 Lab | 0 | 0 | 27 | 409 |
| NB03 Dx | 38 | 698 | 43 | 675 |
| NB06 Eligible | 101 | 1,828 | 52 | 937 |

* **The HCPs without an ID are newer HCPs.** For NB01, all 105 have a `PROVIDER_ID` in the 3.1 Rx input, and all of those IDs are in the 3.1 HCP universe. They are small: 1,513 of the 832 million claims in the last 12 months of the last cohort.
* **The repeated HCPs** have two `PROVIDER_ID`s in the 3.0 mapping, so their row is written twice with the same values. The 3.1 Rx input has one ID for each of them, which is one of the two. Keeping only IDs of the 3.1 universe would solve 41 of the 52; for 11 HCPs both IDs are in the universe.
* No `PROVIDER_ID` is repeated within a cohort apart from the empty ones. The NPI-level tables are not affected.
* In the 3.1 Rx input, 4 of 294,534 NPIs have more than one `PROVIDER_ID` over the history, and every `PROVIDER_ID` belongs to one NPI only.

**Open item (not applied):** keep the mapping table; only for the HCPs it misses or doubles, take the `PROVIDER_ID` of the 3.1 input (fill the missing ones, pick one of the two). Same rule in all six notebooks; only the provider tables are rewritten, the features do not change. To be decided before the outputs are combined (`99_Combine_Physician_Data`).

---

## 7. What did not change

* NPI-level values: only the inputs of the run changed, not the feature logic. The offset-0 parity with NBA 3.0 was checked in validation (client summaries).
* Input pulls stay in `full_2026_11_02/_stage/` and must not be deleted (O5).
* The patient-table folder names end in `_validation` in the full run too (`kerendia_nba_3_1_..._validation`). This is only the name; the content is the full run.

---

## 8. Open points

| # | Point | Proposal |
| --- | --- | --- |
| O2 | `PROVIDER_ID` gaps of the mapping table (section 6) | Keep the mapping table; fill / de-duplicate the 157 HCPs with the 3.1 input's `PROVIDER_ID`; re-write the provider tables (open) |
| D6 | Column list depends on the data of the run (section 5) | Fixed column list, for example from the selected features plus the 3.0 list |
| O8 | Meaning of `RUNNING_` (from `DATA_START_DATE`) | Confirm with Wenjie |
| O9 | `SGLT2_WO_INVOKANA_300MG` family | Decide drop or keep |
| O10 | NB05: months without claims are 0 | Confirm 0 |
| O11 | NB03: type 1 diabetes kidney codes | Keep or exclude |
| O12 | Patient-journey decisions C1 / C9 | Re-run the HCP job after them (job 1010893614518587 runs PJ01–PJ06 and NB01–NB06) |
| O7 / O14 | Downstream combine uses `SVC_DT_M` and 3.0 logic | Wire to `COHORT_ID` |

Details per notebook: the client summaries in `01 Rx Claims Files/` .. `06 Eligible HCP Claims Files/`. Readiness plan: `Alignment_Markdowns/Strategy_and_Execution/NBA_3_1_HCP_Level_Features_AI_Readiness.md`.
