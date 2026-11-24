# NBA 3.1 — IQVIA LAAD Rx Source Review

**Purpose:** Source-level profile of the LAAD Rx claims that feed PJ03 (`03_patient_journey_rx`) and, through it, NB01 / NB05 / NB06.
**Date:** 2026-11-23 | **Window:** service months 2021-01 to 2026-10 (latest month in the table)
**Inputs:** `phcdw.phcdw_stg_car.stg_car_iqv_laad_fct_rx` (UC foreign table = Snowflake `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX`), `..._fct_rx_hist`, `..._dim_prvdr`
**Related docs:** `NBA_3_1_LAAD_Source_Review_Overview.md`, `../../../Patient_Journey_Validation/Rx Files/NBA_3_1_Rx_Journey_Plan.md`

---

## 1. Which table the pipeline reads

* PJ03 reads the **current** fact table `STG_CAR_IQV_LAAD_FCT_RX` (cells 9 and 23, `RX_FACT_30`), joined to `DIM_PRD`, `DIM_PRVDR`, `DIM_PLN`, `DIM_PTNT_DMGRPHC` and `PHCDW_DSAA.CKD_PRODUCT_MAPPING_VW`.
* PJ03 does **not** read `STG_CAR_IQV_LAAD_FCT_RX_HIST`.
* NB01 has no direct Snowflake reference; it reads the patient journey output (`get_patient_table_path`).

## 2. Volume by service month

70 service months, 2021-01 to 2026-10. Rows per month range from 69.2M (2021-02) to 99.3M (2025-12). No 2026-11 rows yet.

| Year | Typical month | Notes |
| --- | --- | --- |
| 2021 | 69M–81M | |
| 2022 | 74M–84M | |
| 2023 | 79M–89M | |
| 2024 | 83M–97M | |
| 2025 | 88M–99M | |
| 2026 (Jan–Oct) | 89M–97M | Oct 2026 = 93.2M, no visible drop-off |

The series grows steadily; there are no reload spikes like the lab HIST table.

## 3. Load pattern and duplicates

Checked for two months (2024-06 and 2026-09):

| Month | Rows | Distinct CLAIM_ID | Null patient | Null provider | DATA_DT values | Batches |
| --- | --- | --- | --- | --- | --- | --- |
| 2024-06 | 88,574,599 | 88,574,599 | 0 | 0 | 1 | 1 |
| 2026-09 | 92,703,507 | 92,703,507 | 0 | 0 | 1 (2026-11-20) | 1 |

* One row per claim; no duplicate loads in the months checked.
* Sep 2026 rows all carry `DATA_DT = 2026-11-20`, so the current table looks like a **full snapshot replaced each delivery**. Feed latency cannot be measured from it.
* **HIST is different:** June 2024 in `..._fct_rx_hist` has 761,430,435 rows over 11 `DATA_DT` loads (2024-08-13 to 2026-08-21), about 8.6x the current table. HIST stacks snapshots and must not be used without picking one load.

## 4. Claim type and status (Sep 2026)

Rows sum to the month total (92,703,507).

| CLAIM_TYPE | Rows | Share |
| --- | --- | --- |
| PD (paid) | 73,143,328 | 78.9% |
| RV (reversed) | 10,530,656 | 11.4% |
| RJ (rejected) | 9,029,523 | 9.7% |

`CLAIM_STATUS` values: S, F, I (meaning not documented here).

* Rows with no NPI after joining `DIM_PRVDR`: 205,364 (0.22%).
* Rows with null or non-positive `DAYS_SUPPLY`: 54,276 (0.06%).

## 5. Learnings

* **RX-A (high):** About 21% of Rx rows are reversed or rejected claims. Neither PJ03 nor NB01 references `CLAIM_TYPE` or `CLAIM_STATUS` (grep count 0), so these rows are very likely counted as fills, inflating TRx/NBRx counts and days on therapy. A reversed claim may also cancel a paid one.
* **RX-B:** The current table is clean on keys (one row per claim, no null IDs) in the months checked.
* **RX-C:** HIST stacks ~11 snapshots per month; any 3.0 or ad-hoc code that reads HIST overcounts heavily.
* **RX-D:** NPI coverage is high (99.8%).

## 6. Actions

| # | Action | Owner |
| --- | --- | --- |
| R1 | Decide the claim-type rule: keep `PD` only, or net `RV` against `PD`. Measure the change in Kerendia/competitor TRx and NBRx before adopting | Rx journey owner |
| R2 | Confirm with PHCDW that `FCT_RX` is a full replace per delivery | Data engineering |
| R3 | Ban `FCT_RX_HIST` in 3.1 code unless one `DATA_DT` is chosen | All |

## 7. Not checked

* Duplicates and null IDs in months other than 2024-06 and 2026-09.
* Share of Rx rows inside the 3.1 HCP universe.
* Meaning of `CLAIM_STATUS` codes S/F/I.
