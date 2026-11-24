# NBA 3.1 — IQVIA LAAD Dx Source Review

**Purpose:** Source-level profile of the LAAD diagnosis claims that feed PJ02 (`02_patient_journey_dx`), PJ04 (DM/HF flags) and, through them, NB03 / NB04 / NB06.
**Date:** 2026-11-23 | **Window:** service months 2021-01 to 2026-10 (latest month in the table)
**Inputs:** `phcdw.phcdw_stg_car.stg_car_iqv_laad_fact_dx` (UC foreign table = Snowflake `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX`)
**Related docs:** `NBA_3_1_LAAD_Source_Review_Overview.md`, `../../../Patient_Journey_Validation/Dx Files/NBA_3_1_Dx_Journey_Plan.md`

---

## 1. Which table the pipeline reads

* PJ02 reads `STG_CAR_IQV_LAAD_FACT_DX` (`DX_CONFIG.source.table`), provider = `COALESCE(PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID)`, joined to `DIM_PRVDR`.
* The 3.1 query de-duplicates on `DISTINCT NPI_NUMBER, PROVIDER_ID, PATIENT_ID, SVC_DT, DIAGNOSIS_CODE`.
* Grain: one row per claim × diagnosis code (a claim carries several codes).

## 2. Volume by service month

70 service months, 2021-01 to 2026-10. Rows per month: 68.3M (2021-02) to 109.4M (2026-03).

| Period | Typical month | Notes |
| --- | --- | --- |
| 2021–2022 | 68M–84M | |
| 2023 onward | 92M–109M | **Step up in Jan 2023:** Dec 2022 83.5M → Jan 2023 97.2M |
| 2026-10 | 79.6M | Likely incomplete (prior months 98M–109M) |

## 3. Load pattern

14 `DATA_DT` loads hold all rows since 2021 (totals reconcile: 6,414,314,355 rows by load = by service month).

| DATA_DT | Service dates covered | Rows |
| --- | --- | --- |
| 2026-08-21 | 2021-01-02 to 2026-02-13 | 5,553,895,632 |
| 2026-08-28 to 2026-11-13 (12 weekly loads) | one service week each, 2026-02-14 to 2026-05-08 | 23.3M–28.1M each (297,639,101 total) |
| 2026-11-20 | 2026-05-09 to 2026-10-30 | 562,779,622 |

* Each service date appears under exactly one load, so there are **no stacked duplicate loads** (unlike the lab HIST table).
* The weekly loads trail the service week by about six months; the 2026-11-20 load then filled May–Oct 2026 in one go. The **refresh cadence is irregular**, and the latest month (Oct 2026, 79.6M rows) is thin.

## 4. Keys, providers, duplicates (2024-06 and 2026-09)

| Month | Rows | Distinct CLAIM_ID | Distinct CLAIM_ID + code | Repeat share | Null patient | No referring or rendering provider |
| --- | --- | --- | --- | --- | --- | --- |
| 2024-06 | 92,898,498 | 37,712,215 | 68,105,445 | 26.7% | 0 | 18,362,681 (19.8%) |
| 2026-09 | 98,217,655 | 39,396,702 | 71,749,670 | 26.9% | 0 | 19,781,367 (20.1%) |

* About 27% of rows repeat a claim + code already seen (other columns may differ, e.g. provider roles). Row counts overstate diagnoses unless de-duplicated; PJ02 3.1 does de-duplicate.
* About 20% of rows have neither a referring nor a rendering provider, so they cannot be attributed to an HCP.
* `ICD_VERSION_TYPE` (2026-09-01 to 09-07): `'2'` = 21,624,120 rows, `'1'` = 2 rows. `'2'` is very likely ICD-10 (not confirmed with IQVIA).

## 5. Indication codes by year

Rows / distinct patients. 2026 = Jan–Oct with Oct partial.

| Code group | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --- | --- | --- | --- | --- | --- | --- |
| N18 CKD | 90.6M / 8.47M | 96.7M / 8.92M | 124.2M / 10.28M | 122.8M / 10.90M | 132.4M / 11.62M | 112.6M / 11.19M |
| E11.22 T2D + CKD | 18.1M / 2.69M | 19.2M / 2.93M | 28.3M / 3.59M | 30.2M / 3.87M | 32.0M / 4.20M | 27.6M / 4.03M |
| I50 HF | 60.7M / 5.76M | 63.4M / 6.01M | 94.3M / 7.08M | 98.6M / 7.26M | 102.3M / 7.78M | 87.6M / 7.26M |
| E10 T1D | 11.6M / 1.49M | 11.8M / 1.47M | 13.5M / 1.52M | 11.9M / 1.45M | 11.5M / 1.40M | 9.1M / 1.25M |

## 6. Learnings

* **DX-A (high):** The Jan 2023 step (+16% rows in one month; I50 rows +49%, E11.22 +47%, N18 +28% from 2022 to 2023) looks like a **coverage change**, not a clinical trend. Features that compare 2023+ to 2022 (growth, running totals from before 2023) will pick it up. 3.1 starts `DATA_START_DATE` at 2023-01-01, so most 3.1 windows sit after the step.
* **DX-B:** Latest-month data is thin and the refresh cadence is irregular; the newest 1–2 months should be flagged or lagged in features.
* **DX-C:** ~27% of rows repeat claim + code; raw row counts are not diagnosis counts.
* **DX-D:** ~20% of rows cannot be attributed to an HCP (no referring/rendering provider).
* **DX-E:** HF (I50) patients grew from 5.76M (2021) to 7.78M (2025); T1D (E10) patients are flat at ~1.4–1.5M. Both matter for the new indications.

## 7. Actions

| # | Action | Owner |
| --- | --- | --- |
| D1 | Ask IQVIA/PHCDW what changed in Jan 2023 (new data supplier?) | Data engineering |
| D2 | Confirm `ICD_VERSION_TYPE` coding | Data engineering |
| D3 | Decide a data lag rule (e.g. drop the latest month or use months up to the last full one) | Feature owners |
| D4 | Check NB03 counts distinct claims/patients, not rows | NB03 owner |

## 8. Not checked

* Duplicates and provider nulls in months other than 2024-06 and 2026-09.
* NPI match rate and share inside the 3.1 HCP universe.
* Which provider role (`BILLING`, `FACILITY`) could recover the ~20% unattributed rows.
