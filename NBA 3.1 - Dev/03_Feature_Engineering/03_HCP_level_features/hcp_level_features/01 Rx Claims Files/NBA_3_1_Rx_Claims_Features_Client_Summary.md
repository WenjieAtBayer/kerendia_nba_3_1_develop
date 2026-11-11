# Kerendia NBA 3.1 – HCP Rx Claims Features: Summary of Changes

> **Update 2026-11-11.** The sections below describe the Phase A sync (2026-11-03). Since then:
> * **Cohorts:** 28 cohorts c1–c28, offset 0, from the claims cohort file (`cohorts/claims/cohorts.parquet`). Replaces 20 cohorts at offset 7.
> * **Output:** Delta partitioned by COHORT_SET (7 groups), few large files per group. Replaces Delta partitioned by COHORT_ID (decision X14).
> * **Kerendia brand added (X16):** 234 new features (`TOTAL_RX_CLAIMS_KERENDIA_IN_LAST_{1,3,6,12}_MONTH`, age/gender/payer/supply/refill/running cross-cuts, rejection). Kerendia is now in the Rx product basket (2026-11-05 mapping update).
> * **6 treatment categories removed (X17):** 979 features for ACE_OR_ARB, CALCIUM_CHANNEL_OR_BETA_BLOCKER, COMBO_DRUG, DIURETIC_NON_MRA, INSULIN, METFORMIN. Outside the 3.1 HCP brand list.
> * **Feature count:** 3.0 = 5,411 features → 3.1 = 4,668 features (+236 new, −979 removed, net −743). Total columns = 4,677 (4,668 features + 9 metadata).
> * **Full run `full_2026_11_11`:** 28 cohorts, job 1010893614518587 run 441950237921, in progress (the 2026-11-07 Parquet run was cancelled before NB01 finished).
> * See decisions X13–X24 in `NBA_3_1_HCP_Features_Decisions.md` and the feature comparison in `NBA_3_1_HCP_Features_E2E_Full_Run_2026_11_07.md`.

**Scope:** HCP-level Rx claims features (`01_claim_rx_monthly_cohort`): what each HCP prescribed, per cohort, in the last 1, 3, 6 and 12 months  
**Baseline:** NBA 3.0 notebook `01_claim_rx_monthly` (calendar months)  
**Data used for validation:** IQVIA LAAD Rx claims of the 10 validation HCPs (9 have Rx claims), 20 cohorts 2025-01 .. 2026-08 at offset 7  
**Status:** validated on the 10 HCPs (2026-11-03); full run for all HCPs done and checked (2026-11-04, section 4.4)

---

## 1. Summary

The Rx claims features were already rebuilt for NBA 3.1 (cohorts with an offset, one run for all cohorts, checked against NBA 3.0). This step connects them to the **3.1 patient journey**.

* **One input comes from the patient journey:** the number of treatments each patient is on, and how many are new, per month. It feeds 72 of the 3,686 feature columns (`TOTAL_RX_CLAIMS_PATIENT_WITH_...`; the table also has 7 key and cohort columns). Everything else comes from the Rx claims directly.
* **The notebook was reading an old copy of that input.** It now reads the table written by the latest 3.1 patient-journey run.
* **Only those 72 columns changed, as expected.** The other 3,614 feature columns are identical to the previous output for every HCP and cohort.
* **The changes are small in the windows the model uses** (last 1 to 12 months: below 1% for most columns, up to 5.3% in small columns) and larger in the all-history `RUNNING_` columns, because the 3.1 Rx journey now sees treatments that started in late 2022.
* **All checks pass:** same result as NBA 3.0 at offset 0 (700,150 values, 0 differences), the fast engine = the step-by-step version, and a recount of one HCP from the raw claims (2,100 checks, 0 differences).
* **The Rx claims now come from the 3.1 Rx journey too** (section 3.3), like the lab and diagnosis features. The claims are the same as before: all 50,739 NBA 3.0 claims of the validation HCPs are there with the same values, plus 2 newer claims. GLP-1, DPP-IV and other glucose drugs are kept for the HCP features (decision 2026-11-03).
* **Drug list:** the HCP features use the NBA 3.0 drug list, now read from the 3.1 product basket. Kerendia, Mounjaro, Wegovy, Zepbound and generic dapagliflozin are not in it (decision for the next phase, section 5); a basket change will now reach the HCP features directly.
* **Full run (all HCPs, section 4.4):** 294,503 HCPs, 20 cohorts, all 172 selected model features present, 3 HCPs recounted from the full inputs with 0 differences. There are more columns (4,441 instead of 3,693) because rare values appear only when all HCPs are included; no selected feature is among them. In the provider table, 105 HCPs have no `PROVIDER_ID` and 52 HCPs appear twice: the NPI → `PROVIDER_ID` mapping table is correct for all other HCPs but misses or doubles these (open item, section 5).

---

## 2. What the Rx claims features use

| Input | Used for | Changed in 3.1? |
| --- | --- | --- |
| Rx claims (HCP Rx pull of the 3.1 Rx journey; was `Rx_01_new`) | 3,614 columns: claims by drug class, brand, rejection, days supply, refill, payer, age, gender; totals, shares, `RUNNING_`, averages | **Source changed** (section 3.3); same claims as NBA 3.0 plus newer data |
| Patient treatments per month (`pat_new_and_total_treatments`, from the patient journey) | 72 columns: claims of patients with no / 1 / 2–3 / more than 3 active treatments, and no / 1 / 2–3 / more than 3 new treatments | **Yes:** built by the 3.1 Rx journey |

Each Rx claim is matched to its patient's row for the same cohort month (offset 7). 98.7% of the claims of the validation HCPs find a row; the others count as "no active treatment", as in NBA 3.0.

---

## 3. What changed

### 3.1 The notebook now reads the latest patient-journey output

| | Before | Now |
| --- | --- | --- |
| Table read | Copy in `query_output/` (written 2026-10-26, before the 3.1 Rx journey) | Folder of the latest patient-journey run (`validation_2026_10_30/`, written 2026-11-02) |
| Patient-months | 137,373 (4,238 patients) | 140,370 (4,431 patients) |
| Rule | Fixed table name | Shared setting: the folder of the patient-journey run (`RUN_OUTPUT_DIR`) when the table is there |

The same rule will be used in the full run: the job points to the full patient-journey run folder, so the HCP features always use the patient table of the same run. Without it, production would read the NBA 3.0 table, which is in calendar months and would not match the offset-7 cohorts (claims from the 1st to the 6th of a month would get the wrong month).

### 3.2 Why the patient-treatment columns changed

The 3.1 Rx journey (see the Rx journey summary) keeps the same drugs and categories as NBA 3.0, with two changes that reach these columns:

* **Look-back:** a 90-day fill from late 2022 now counts for the days it covers in 2023. These patients are seen on more treatments in early 2023, and a drug started in late 2022 is no longer a "new" treatment in 2023.
* **Patients of the validation run:** the 3.1 run includes the patients of the lab, diagnosis and Rx journeys of the 10 HCPs (193 more patients in the table).

### 3.3 The Rx claims now come from the 3.1 Rx journey

Before, the Rx claims came from a separate NBA 3.0 table (`Rx_01_new`), while the lab and diagnosis features already used the 3.1 journeys. The Rx journey now also writes the claims for the HCP features (new step, the patient journey itself is not changed):

| | NBA 3.0 table | 3.1 HCP Rx pull |
| --- | --- | --- |
| Drug list and labels | Snowflake view + typed lists | 3.1 product basket (same drugs and labels) |
| HCP universe, dates | Own rules | Same as the 3.1 Rx journey |
| GLP-1, DPP-IV, other glucose drugs | Kept | **Kept** (the patient journey does not count them; decision 2026-11-03) |
| Rejection, refill, payer, age, gender | Yes | Yes (same definitions) |

Result for the 9 validation HCPs with Rx claims (2023-01 .. 2026-09): all 50,739 NBA 3.0 claims are in the new input with the same drug class, brand, rejection, payer, age, gender, refill and days supply; 2 claims are new (newer data). The features changed for 1 HCP only (one new Ozempic claim in July 2026); the other 8 HCPs are identical. The 3,693 columns are unchanged.

In the full run the new input also uses the 3.1 HCP universe: one validation HCP (1508230566) is not in it, which is why it is already missing from the lab and diagnosis features.

---

## 4. Results (10 validation HCPs, 20 cohorts)

### 4.1 Which columns changed

| Columns | Number | Values that changed |
| --- | --- | --- |
| Not using the patient journey | 3,614 | **0** (identical) |
| Patient treatment, active treatments, last 1–12 months | 32 (incl. shares) | 0 |
| Patient treatment, new treatments, last 1–12 months | 32 (incl. shares) | 1 to 106 of 180 rows per column |
| Patient treatment, `RUNNING_` (all history from 2023) | 8 | 60 to 180 of 180 rows |

### 4.2 Size of the changes (sum over all HCPs and cohorts)

| Column | Before | Now | Change |
| --- | --- | --- | --- |
| Claims of patients with 1 new treatment, last 12 months | 21,940 | 22,048 | +0.5% |
| ... with 2–3 new treatments, last 12 months | 2,940 | 2,994 | +1.8% |
| ... with more than 3 new treatments, last 12 months | 879 | 873 | −0.7% |
| ... with no new treatment, last 12 months | 249,301 | 249,145 | −0.1% |
| ... with 2–3 new treatments, last month | 226 | 238 | +5.3% |
| `RUNNING_` 1 active treatment | 193,347 | 187,587 | −3.0% |
| `RUNNING_` more than 3 active treatments | 312,525 | 318,685 | +2.0% |
| `RUNNING_` 2–3 new treatments | 13,762 | 10,591 | −23.0% |
| `RUNNING_` more than 3 new treatments | 5,636 | 3,658 | −35.1% |

Reading the table: in the last-month to last-12-month windows the change per HCP and cohort is at most 8 claims. The largest change in a share column is 0.20, for an HCP with 5 claims in the month (1 of the 5 claims is no longer counted under "no new treatment"). The `RUNNING_` columns add up all months from 2023-01, so they carry the early-2023 effect of the look-back: fewer "new" treatments, more patients on several treatments.

### 4.3 Checks

| Check | Result |
| --- | --- |
| Same as NBA 3.0 at offset 0 (19 months, NBA 3.0 inputs) | **PASS:** 700,150 values compared, 0 differences. 19 values in one known NBA 3.0 inconsistency (`RUNNING_ ... SGLT2_WO_INVOKANA_300MG`, 3.0 is 1 lower than its own SGLT2 minus Invokana 300 MG); 3.1 keeps the consistent value |
| Fast engine = step-by-step engine (first and last cohort) | **PASS:** 66,438 values, 0 differences |
| Recount of HCP 1386651560 from the raw claims, every cohort | **PASS:** 2,100 checks, 0 differences |
| Output complete | 20 cohorts, 180 rows (9 HCPs x 20), 3,693 columns, no duplicates, no empty values |
| Provider table | 180 rows, every NPI mapped to a `PROVIDER_ID`, no duplicates |
| 3.1 Rx input vs NBA 3.0 table, claim by claim | **PASS:** 50,739 of 50,739 claims with the same values; 2 newer claims |
| Rerun with the 3.1 Rx input: same checks | **PASS:** NBA 3.0 at offset 0 700,150 values, 0 differences; fast engine 66,438, 0; HCP recount 2,100, 0; own recount of GLP-1 / DPP-IV / spironolactone / other glucose 2,880, 0; 3,693 columns, no empty values |

### 4.4 Full run (all HCPs, 2026-11-04)

Job run 1050221322333806 (198 min), patient-journey run folder `full_2026_11_02/`, 3.1 HCP universe. The first attempt ran out of memory in a check cell; in the full run that check now uses the trace HCPs only (the features are not changed).

| Check | Result |
| --- | --- |
| Output complete | 20 cohorts, 5,830,945 rows, 294,503 HCPs, 4,441 columns, no duplicates, no empty values |
| Selected model features | 172 of 172 present |
| Recount of 3 HCPs (1386651560, 1528629052, 1841364841) from the full Rx input and the full patient table, every cohort | **PASS:** 8,621 checks, 0 differences. Covers drug class, brand, rejected claims, payer, gender, total, `RUNNING_` and the 72 patient-treatment columns; columns without claims are 0 and the drug classes add up to the total |
| Validation run vs full run, the 8 validation HCPs in both | The 3,615 claim columns are identical. Only the 72 patient-treatment columns differ (6,369 values): the full patient-journey run is a separate run, on the 3.1 HCP universe. HCP 1508230566 is not in the full run (not in the 3.1 universe) |

**Why 4,441 columns instead of 3,693.** The columns are built from the values found in the data. With all HCPs, rare values show up that the 10 validation HCPs never had: gender "U" (94,106 claims from 12,549 HCPs in the last 12 months of the last cohort), empty days supply (1,999 claims), young patients (age groups 0–30, mostly brands), Cash / Medicare for some brands, and one claim whose patient birth year is after the service date (column `..._AGE_GROUP_10_0`, a negative age). That adds 748 columns: 332 counts for the last 1–12 months, 332 shares and 84 `RUNNING_` columns. All 3,693 validation columns are still there, and none of the 748 new ones is a selected model feature.

**Provider table (`provider_claim_rx_monthly_cohort`).** It has 5,831,886 rows, 941 more than the NPI table, and 1,911 rows with an empty `PROVIDER_ID`. Both come from the NPI → `PROVIDER_ID` mapping table `query_output/kerendia_nba_3_0_npi_bhid_mapping`. This is the agreed BHID-NPI mapping and it is correct for almost all HCPs: for 294,345 of the 294,346 HCPs with one ID in it, the 3.1 Rx input has the same `PROVIDER_ID`. The issue is limited to 157 HCPs:

* **105 HCPs are not in the 3.0 mapping** (these are the 1,911 empty rows; together they have 1,513 of the 832 million claims in the last 12 months). The 3.1 Rx input gives each of them a `PROVIDER_ID`, and all of those IDs are in the 3.1 HCP universe.
* **52 HCPs have two `PROVIDER_ID`s in the 3.0 mapping**, so their rows are written twice (941 rows). The 3.1 Rx input has one of the two IDs for each of them. Keeping only IDs of the 3.1 universe would solve 41 of the 52; for 11 HCPs both IDs are in the universe.

No `PROVIDER_ID` appears twice in the same cohort. The NPI-level table is not affected. This stays an open item (section 5).

---

## 5. Open points for the next phase

| Topic | Today | Proposal |
| --- | --- | --- |
| Drug list of the HCP features | 3.1 product basket (same drugs as NBA 3.0) | Change together with the Rx journey Phase B, so the HCP and patient levels keep the same list |
| Kerendia, Mounjaro, Wegovy, Zepbound, generic dapagliflozin | Not active in the product basket yet | Phase B: activate in the basket; they then reach the HCP features directly |
| GLP-1 / DPP-IV and other glucose drugs | Kept at HCP level (decision 2026-11-03), not counted in the patient's number of treatments | Revisit with the Rx journey Phase B |
| Full run of the new Rx input | **Done:** full run 2026-11-04, 294,534 HCPs (section 4.4) | - |
| `PROVIDER_ID` of the provider table (**open**) | Mapping table `kerendia_nba_3_0_npi_bhid_mapping` (agreed BHID-NPI mapping): 105 HCPs without an ID, 52 HCPs written twice (section 4.4) | Keep the mapping table; only for these 157 HCPs take the `PROVIDER_ID` of the 3.1 Rx input (fill the missing ones, pick one of the two). Same rule in all six HCP notebooks; only the provider tables are rewritten. To be decided before the outputs are combined; not applied yet |
| Rare values at full scale (gender "U", empty days supply, negative age) | Kept as their own columns (none is a selected feature) | Keep for now; revisit if the feature selection is rerun on 3.1 |

---

## 6. Next steps

1. ~~Same sync for the other HCP notebooks~~ (done 2026-11-03).
2. ~~Full HCP run with all six notebooks~~ (done 2026-11-04, section 4.4).
3. Decide the `PROVIDER_ID` gap fill for the 157 HCPs (open item, section 5).
4. Drug-list decisions with the Rx journey Phase B (section 5).

Details: `01 Rx Claims Files/NBA_3_1_Rx_Claims_Features_Plan.md`.
