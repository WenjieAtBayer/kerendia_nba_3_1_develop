# NBA 3.1 – HCP new patient starts features (NB05): sync with the 3.1 patient journey, analysis and plan

> **Update 2026-11-11.** 28 cohorts c1–c28 at offset 0 (claims cohort file, X13), Delta by COHORT_SET (X14). No feature changes: 154 features, total 163 columns. Input stays 3.0 `Rx_05` (X7). See `NBA_3_1_HCP_Features_Decisions.md`.

**Status (2026-11-03):** analysed and validated on the 10 test HCPs; only the `%run` path changed (C1). Client summary: `05 Rx NPS Claims Files/NBA_3_1_Rx_NPS_Features_Client_Summary.md`.  
**Notebook:** `hcp_level_features/05 Rx NPS Claims Files/05_claim_rx_nps_monthly_cohort` (3.0 source `05_claim_rx_nps_monthly`)  
**Output:** `notebook_output/claim_rx_nps_monthly_cohort` (`PROVIDER_ID` x `COHORT_ID`; the input already has `PROVIDER_ID`)  
**What it builds:** per HCP, patients visiting (distinct patients with an Rx claim) and patients who **started** a drug class or one of the brands with that HCP. A start = the patient's first claim of the class / brand in the whole table, by any HCP. Windows 1/3/6/12 months, `RUNNING_`, `PCT_` (start / visits).

---

## 1. What could reach NB05 from the 3.1 patient journey

| Upstream 3.1 change | Reaches NB05? |
| --- | --- |
| Patient tables (PJ01–PJ06) | No: NB05 reads no patient table |
| Rx journey drug list / labels | Only if the input switches to the 3.1 HCP Rx pull (NB01 C4) |
| HCP universe (3.1) | Only through the Rx pull |
| Cohorts, `DATA_START_DATE`, common end date | Already in the cohort refactor |

## 2. Findings

**F1. Input `kerendia_nba_3_0_Rx_05`:** Rx claims of every HCP since 2021-01-02 (4.03 B rows), ends 2026-09-30. A start needs the patient's claims by **any** HCP and the history **before** 2023 (otherwise patients already on a drug in 2022 look like new starts in 2023).

**F2. The 3.1 HCP Rx pull cannot replace it:** it starts at `DATA_START_DATE` (2023-01-01) and only has the claims of the HCP universe.

**F3. Same claims for the counted HCPs.** Test HCPs, 2023-01-01 .. 2026-09-30, on (NPI, patient, date, class, brand): `Rx_05` 49,140 keys, pull 49,142; all 49,140 in both; the 2 extra keys in the pull are the 2 newer claims seen in NB01 (Ozempic 2026-07-18, lisinopril 2026-09-30). Same class and brand labels (GLP-1, DPP-IV, other glucose included).

**F4. `%run` path** after the move into the subfolder.

**F5. Model features:** 14 of the 277 selected features come from NB05; all 14 are in the output.

## 3. Changes

| ID | Change | Where |
| --- | --- | --- |
| C1 | `%run "../../00_cohort_config"` | NB05 config cell |
| C2 | Comment in the load cell: why `Rx_05` stays (F1–F3) | NB05 load cell |

Not changed: input, feature logic, columns, windows, parity.

## 4. Decisions

| ID | Question | Proposal |
| --- | --- | --- |
| D1 | Keep `Rx_05` as the NB05 input | Yes (F1–F3). Revisit with the Rx journey Phase B: if new drugs are added to the basket (Kerendia, Mounjaro, ...), NB05 needs a basket-based all-HCP input from 2021 for their starts |
| D2 | HCP universe | NB05 counts the HCPs of `Rx_05` (3.0 universe); the model joins on the HCP list of the full run. Same decision as NB01–NB04 |

## 5. Validation (10 test HCPs, offset 7, run 2026-11-03)

| Check | Result |
| --- | --- |
| Fast engine = step-by-step (first and last cohort) | PASS: 2 x 1,431 cells, 0 mismatches |
| Write | 20 cohorts, 180 rows (9 providers), 161 columns, 0 duplicates, 0 null cells |
| HCP trace 1386651560 / provider 7608159, every cohort | PASS: 3,080 checks, 0 mismatches |
| Offset-0 parity vs 3.0 `kerendia_nba_3_0_claim_rx_nps_monthly` | PASS: 19 months, 35,720 cells, 0 mismatches |
| Own recount (pandas, first-start dates from all claims of the patients; last cohort, 12 months: SGLT2, ACE/ARB, Jardiance, GLP-1 starts) | PASS: 84 / 72 / 82 / 22 starts, 0 mismatches per provider |
| Before (2026-10-26 output) vs now | Identical: 0 of 27,720 cells changed |
