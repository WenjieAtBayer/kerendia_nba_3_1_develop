# NBA 3.1 — IQVIA LAAD Px Source Review

**Purpose:** Source-level profile of the LAAD procedure claims that feed PJ05 (`05_patient_journey_px`, dialysis flag) and the 3.1 eligibility rule `DIALYSIS_FLAG = 0`.
**Date:** 2026-11-23 | **Window:** service months 2021-01 to 2026-10 (latest month in the table)
**Inputs:** `phcdw.phcdw_stg_car.stg_car_iqv_laad_fact_px` (UC foreign table = Snowflake `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_PX`)
**Related docs:** `NBA_3_1_LAAD_Source_Review_Overview.md`, `../../../Patient_Journey_Validation/Px Files/NBA_3_1_Px_Journey_Plan.md`

---

## 1. Which table the pipeline reads

* PJ05 reads `STG_CAR_IQV_LAAD_FACT_PX` joined to `STG_IQVIA_LAAD_DIM_PROCEDURE` (3.0 rule: description `LIKE '%DIALYSIS%'`; 3.1 adds explicit dialysis codes) and keeps the first dialysis date per patient.
* Grain: one row per claim service line (`CLAIM_ID` + `CLAIM_SERVICE_NUMBER`).
* **`SERVICE_DATE` is a STRING** in this table (it is a DATE in Dx). All rows with service date ≥ 2021 are in `YYYY-MM-DD` format (0 bad-format or null rows found).

## 2. Volume by service month

70 service months, 2021-01 to 2026-10. Rows per month: 19.4M (2021-02) to 28.9M (2023-03).

| Period | Typical month | Notes |
| --- | --- | --- |
| 2021–2022 | 19M–24M | |
| 2023 onward | 24M–29M | **Step up in Jan 2023:** Dec 2022 21.9M → Jan 2023 26.8M (same as Dx) |
| 2026-10 | 24.1M | Slightly low; probably incomplete |

## 3. Load pattern

Same structure as Dx: 14 `DATA_DT` loads, totals reconcile (1,738,770,602 rows by load = by service month).

| DATA_DT | Service dates covered | Rows |
| --- | --- | --- |
| 2026-08-21 | 2021-01-02 to 2026-02-13 | 1,510,642,455 |
| 2026-08-28 to 2026-11-13 (12 weekly loads) | one service week each, 2026-02-14 to 2026-05-08 | 6.0M–7.0M each |
| 2026-11-20 | 2026-05-09 to 2026-10-30 | 150,978,721 |

Load ranges do not overlap, so no stacked duplicate loads.

## 4. Keys and providers (2026-09)

| Rows | Distinct claim lines | Null patient | No referring or rendering provider |
| --- | --- | --- | --- |
| 26,209,372 | 26,209,372 | 0 | 178,478 (0.68%) |

## 5. Dialysis trend (proxy)

Proxy = CPT 90935–90999 (dialysis services). This is **not** PJ05's exact basket (which also uses description matching and home-visit codes).

| Year | Rows | Distinct patients |
| --- | --- | --- |
| 2021 | 29,651,025 | 578,165 |
| 2022 | 32,305,187 | 571,370 |
| 2023 | 35,735,259 | 592,126 |
| 2024 | 31,395,522 | 600,297 |
| 2025 | 34,160,962 | 571,857 |
| 2026 (Jan–Oct) | 28,992,183 | 589,783 |

## 6. Learnings

* **PX-A:** Px is clean on keys (one row per claim line, no null patient, <1% unattributed provider) in the month checked.
* **PX-B:** The Jan 2023 coverage step seen in Dx is also in Px (+22% in one month), but dialysis patients stay flat at ~0.57M–0.60M per year, so the dialysis exclusion is stable across the step.
* **PX-C:** `SERVICE_DATE` as string means date filters compare strings; they work only while the ISO format holds. Cast explicitly in 3.1 code.
* **PX-D:** Same irregular refresh and thin latest month as Dx; a patient's dialysis start in the last 1–2 months may be missed.

## 7. Actions

| # | Action | Owner |
| --- | --- | --- |
| P1 | Cast `SERVICE_DATE` to DATE in PJ05 | Px journey owner |
| P2 | Compare PJ05 basket patient counts with the CPT 90935–90999 proxy above | Px journey owner (with Raman) |

## 8. Not checked

* Duplicates and provider nulls in months other than 2026-09.
* `PRC_VERS_TYP_ID` meaning (it is `'-1'` in the 5 sample rows looked at).
* NPI match rate and share inside the 3.1 HCP universe.
