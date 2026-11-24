# NBA 3.1 — LAAD Source Review Overview (Rx, Dx, Px, Lab)

**Purpose:** One-page comparison of the four claim sources behind the NBA 3.1 patient journeys and HCP claims features.
**Date:** 2026-11-23 | **Window:** 2021-01 to the latest month in each table
**Inputs:** the three source reviews in this folder, plus the Lab review
**Related docs:** `NBA_3_1_Rx_Source_Review.md`, `NBA_3_1_Dx_Source_Review.md`, `NBA_3_1_Px_Source_Review.md`, `../../../Patient_Journey_Validation/Lab Files/NBA_3_1_Lab_Data_Learnings_and_3_0_Review.md`

Source tier 4 (raw vendor staging tables, no semantic layer). All queries were read-only aggregates through the UC foreign catalog `phcdw` (Snowflake `PHCDW`).

---

## 1. Comparison

| | Rx | Dx | Px | Lab |
| --- | --- | --- | --- | --- |
| Table read by journey | `STG_CAR_IQV_LAAD_FCT_RX` | `STG_CAR_IQV_LAAD_FACT_DX` | `STG_CAR_IQV_LAAD_FACT_PX` | `STG_CAR_IQV_QUEST_TO_LAAD_HIST` |
| Journey | PJ03 | PJ02, PJ04 | PJ05 | PJ01 |
| Latest service month | 2026-10 | 2026-10 (partial) | 2026-10 (partial) | 2026-10 |
| Rows / month (2026) | 89M–97M (Jan–Oct) | 98M–109M (Jan–Sep; Oct 79.6M) | 25M–28M (Jan–Sep; Oct 24.1M) | see Lab review |
| Load structure | Full snapshot (one `DATA_DT`) | 14 non-overlapping loads | 14 non-overlapping loads | **Stacked reloads** (2025-03 history reload on top of original) |
| Duplicate loads | None found (2 months) | None | None | Yes: Jun 2024 Quest 69%, LabCorp 59% duplicate |
| Repeat rows within a load | None (1 row per claim) | ~27% repeat claim + code | None (1 row per claim line) | Same-day repeats (eGFR/UACR 2025–26: 7% exact) |
| Null patient | 0 | 0 | 0 | LabCorp 2021–2024: 56–59% no patient ID; 2025: 33%; from 2025-08: 0% |
| Unattributed provider | 0.22% no NPI | ~20% no referring/rendering | 0.68% | see Lab review |
| Jan 2023 coverage step | No | **Yes** (+16% in a month) | **Yes** (+22%) | n/a |
| Main open issue | 21% reversed/rejected claims counted | coverage step, thin latest month | string `SERVICE_DATE` | dedup rule for reloads |

## 2. Top issues for NBA 3.1 features

1. **Rx reversed/rejected claims (RX-A).** 11.4% reversed + 9.7% rejected rows (Sep 2026); no filter in PJ03 or NB01. Affects every Rx count feature (NB01, NB05 NPS, NB06 eligible HCP).
2. **Lab stacked reloads (S3).** Pre-2025 months are counted more than once unless de-duplicated (Jun 2024: Quest 69% and LabCorp 59% duplicate rows). Affects NB02 lab counts and any lab trend.
3. **Dx/Px Jan 2023 coverage step (DX-A, PX-B).** Growth and running-total features that span Jan 2023 show artificial growth. 3.1 windows start 2023-01, so the impact is mostly on 3.0 comparisons and on any longer look-back.
4. **Thin latest month (DX-B, PX-D).** Dx/Px Oct 2026 is incomplete; the newest month should be lagged or flagged.
5. **Unattributed Dx rows (DX-D).** ~20% of diagnosis rows have no referring/rendering provider and never reach an HCP.

## 3. Decisions needed

| # | Decision | Docs |
| --- | --- | --- |
| R1 | Rx claim-type rule (`PD` only, or net reversals) | Rx review |
| S3 | Lab dedup rule for HIST reloads | Lab review |
| D3 | Data lag rule for the latest month (Dx/Px) | Dx, Px reviews |
| D1 | Ask IQVIA what changed in Jan 2023 | Dx review |

## 4. Not checked across sources

* Duplicates and nulls outside the 1–2 months checked per source.
* Share of each source inside the 3.1 HCP universe.
* Record-level overlap between sources (e.g. same patient-day in Dx and Lab).
