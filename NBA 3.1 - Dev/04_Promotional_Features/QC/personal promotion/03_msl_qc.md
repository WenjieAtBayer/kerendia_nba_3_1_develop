# QC 03: MSL interaction flag, NBA 3.1

**QC status:** DONE, 20 Nov 2026 (channel 3 of 6)  
**Verdict:** PASS. The flags are correct (Q9: 10 of 10 recomputed values match), with no overlap with the F2F block. Q13 docs were not reviewed.  
**QC run:** 20 Nov 2026, serverless, on the output of the last notebook run. The notebook was not re-run.

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | `personal_promotional_features/MSL/msl_feature` (17 cells) |
| Client summary | `MSL/msl_feature_nba_3_1_client_summary.md` |
| Readiness file | `40_field_activity_nba_3_1_readiness_plan.md`: Phase 0 V10, Phase 3 MD-1 (X3 richer features out of scope) |
| Output | `kerendia_nba_3_1_volume/notebook_output/field_activity_nba_3_1/kerendia_nba_3_1_hcp_model_field_msl_features.parquet` |
| Universe / cohorts | `HCP_Universe_without_call_hcps/` x `cohorts/promotional/cohorts.parquet` (c1 to c28); `EXCLUDE_PROVIDER_IDS = ["0"]` |
| Expected shape | 2 features (`FLD_MSL_INTERACTION_6M`, `FLD_MSL_INTERACTION_12M`) + keys, 8,252,328 rows (294,726 x 28) |
| NBA 3.0 counterpart | `32_MSL_Visits_features` (3 features, 1M, keyed PROVIDER_ID + month / year) |
| NBA 3.0 final model | MLflow run `f583bcbc9d56477fae983d44c16f8c70`, 752 features, `Shap_Importances.csv` |

## 2. QC checklist

| # | Check | How | Pass when | Status |
| --- | --- | --- | --- | --- |
| Q1 | HCP universe | Distinct PROVIDER_ID vs universe minus `0`; rows = 294,726 x 28; duplicates; extra HCPs; mapping coverage (only 62.9% of Finerenone MSL BHIDs are in the universe) | Same HCP set, `0` absent, 0 duplicates | PASS |
| Q2 | Cohorts and windows | Lookback ends; 6M = 182 and 12M = 365 days; no record after lookback end | All match | PASS |
| Q3 | All features made | Columns vs config vs readiness MD-1 | 2 features, binary 0 / 1 | PASS |
| Q4 | Business rules | Fill section 4 | All match | PASS |
| Q5 | Data sources | Notebook: `FACT_CALL`, `MAP_CUSTOMER_XREF`; readiness V10: medical records in `FACT_CALL` | Same | PASS |
| Q6 | Fill rate | % null, % 1 per feature, all cohorts, per split, c28 | 0 nulls; 12M flag on about 4,100 to 4,400 HCPs from c14 | PASS |
| Q7 | NBA 3.0 model coverage | MSL features in the 752 with SHAP rank | Mapped or dropped with reason | PASS |
| Q8 | Preserved vs new | Fill section 5 | Every feature labelled | PASS |
| Q9 | HCP trace | Section 6, at least 5 HCPs | Final value = output | PASS (10 / 10) |
| Q10 | Invariants | 6M flag = 1 implies 12M flag = 1; values only 0 / 1 | 0 violations | PASS |
| Q11 | Reconciliation | Medical interactions per year vs V10 | About 10,500 to 10,900 interactions and 6,400 to 6,800 doctors a year (all doctors, before universe filter) | PASS |
| Q12 | Cross-block | No `MEDICAL` record counted as `HCP_INTERACTION` in the F2F block | 0 overlap | PASS |
| Q13 | Reproducibility and docs | Same schema on re-run; summary current | No stale text | OPEN (not reviewed) |

## 3. Evidence log

| # | Result (numbers) | Where (cell / query) | Notes |
| --- | --- | --- | --- |
| Q1 | Output 8,252,328 rows = 294,726 HCPs x 28; every cohort 294,726 rows; 0 duplicate (PROVIDER_ID, COHORT_ID) or `HCP_COHORT_ID`; `HCP_COHORT_ID` = `PROVIDER_ID_COHORT_ID`; 0 HCPs outside the universe; only `0` missing (`EXCLUDE_PROVIDER_IDS`, cell 5). Same mapping as F2F / iRep (294,577 with BHID, 38 shared BHIDs) | QC session | 62.9% recomputed 20 Nov 2026 with cell 9 logic: saved record file 10,117 of 16,085 in-scope BHIDs (62.9%; 3,980 not in mapping, 1,988 mapped outside the universe), Y2 4,365 of 6,971 (62.6%). Today's Snowflake data: 10,252 of 16,390 (62.6%; 4,108 not in mapping, 2,030 outside), Y2 4,410 of 7,121 (61.9%) |
| Q2 | 28 cohorts match cohorts.parquet (0 mismatches). Windows 6M = 182, 12M = 365 days, record in window if days before END < N; cell 10 asserts every record is in (END - 365, END]. Trace confirms the edges: 225 days = 12M only; 377 days = outside | Cells 4, 10, 11; Q9 | `DATA_START` 2023-06-01 is before the c1 window start (2023-06-18; assert in cell 5) |
| Q3 | 2 features `FLD_MSL_INTERACTION_6M`, `FLD_MSL_INTERACTION_12M`, same order as config, int, values only 0 / 1, 0 nulls | QC session | |
| Q4 | Section 4: all rules match | Cells 4, 6, 10 | |
| Q5 | `FACT_CALL` + `MAP_CUSTOMER_XREF` (`CPH_DB_PROD.MODEL_V2`) + `SOURCE_PROVIDER_BHID_NPI_MAPPING`. Filters: `SUBMITTED_VOD`, call date >= 2023-06-01, BHID not null and not BHO, dedup on (CALL_ID, BHID) | Cell 6 | |
| Q6 | 0 nulls. HCPs with 12M flag: 2,685 (c1) rising to 4,107 (c14), then 4,095 to 4,356 (c14 to c28; c24 4,095). Share of rows with flag = 1: 12M 1.25% train, 1.44% test, 1.48% holdout; 6M 0.75 / 0.81 / 0.89%. Upward trend over cohorts (training lower than test) | QC session | Flag only (compliance) |
| Q7 | No feature in the 752 has `MSL` or `MEDICAL` in its name, so the NBA 3.0 `32_MSL_Visits_features` features were not used by the model | MLflow `Shap_Importances.csv` | Name search only; `32_` output columns not opened |
| Q8 | Section 5 | | |
| Q9 | 5 HCPs (4 at c28, 1 at c10) x 2 flags = 10 values recomputed from raw `FACT_CALL`: 10 match (section 6) | QC session | |
| Q10 | 6M = 1 with 12M = 0: 0 rows; values only 0 / 1 | QC session | |
| Q11 | Snowflake today, Finerenone records (submitted, non-BHO doctors): Y1 10,462 records / 6,409 doctors (= notebook 43 reference); Y2 11,471 / 7,121 (reference 11,180 / 6,964: +2.6% / +2.3%, within the notebook's 3% tolerance; late MSL entries) | Direct SQL | |
| Q12 | Medical records are excluded from F2F by the same rules (F2F cell 4 uses the same record-type regex and `finerenone` product rule, and gives `MEDICAL` before `HCP_INTERACTION`). Data check: 0 of the 30,948 in-scope MSL call IDs appear in the F2F `field_interaction_detail.parquet` with product `Kerendia` | F2F cells 4, 7; QC session | |
| Q13 | Not checked in this session | | |

## 4. Business rules to verify (readiness vs notebook)

| Rule | Readiness file says | Notebook does (cell) | Match |
| --- | --- | --- | --- |
| Medical record | Product text `Finerenone [...]`; record types `Face2Face Interaction Med`, `BPH_MED_*`, `Remote Interaction Med`, `Event Call Report` | Cell 4: record type regex `(interaction[ _]med|^bph_med_|^event call report)` or product `finerenone`; cell 6 applies it again in Spark after the wider SQL pre-filter | Yes |
| Scope | `MSL_SCOPE = "FINERENONE"`; no Asundexian (decision 5 Nov 2026) | Cell 4 `MSL_SCOPE = "FINERENONE"`; `IN_SCOPE` = Finerenone flag; cell 10 asserts no non-Finerenone record enters | Yes |
| Flag | 1 if any medical interaction with the HCP in the window, else 0; flag only (compliance) | Cell 11: max over records of days before < window | Yes |
| Ordering | Drop medical records before any `DETL_PROD ILIKE '%kerendia%'` rule (Finerenone text contains Kerendia) | Separate block; F2F gives `MEDICAL` before `HCP_INTERACTION` (Q12) | Yes |
| Usage | Not used in rep-facing driver text unless agreed | Not testable in data; stated in cell 1 | Note |
| `Event_vod` | (open) | 25 `Event_vod` records, all in scope (Finerenone product, no medical record type). 25 Finerenone records have no medical record type; `REQUIRE_MEDICAL_REC_TYPE = False` keeps them | To agree |

## 5. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature | In 752? (SHAP rank) | NBA 3.1 feature | Status | Reason |
| --- | --- | --- | --- | --- |
| `32_MSL_Visits_features` (3 features, 1M) | No (no `MSL` / `MEDICAL` name in the 752) | `FLD_MSL_INTERACTION_6M`, `FLD_MSL_INTERACTION_12M` | Replaced | Flag only (compliance, 30 Oct 2026); Finerenone scope (5 Nov 2026) |

Summary: 0 NBA 3.0 model features to map; both NBA 3.1 features labelled (replaced).

## 6. HCP trace (step-by-step recompute)

HCPs: MSL visit 2 to 5 months before lookback end (6M = 1), visit 7 to 11 months before (6M = 0, 12M = 1), visit just over 12M before (both 0), no MSL contact, `Event_vod` type record (25 exist).

| Step | What | Value |
| --- | --- | --- |
| 1 | PROVIDER_ID to BHID(s) | |
| 2 | Raw `FACT_CALL` medical rows | |
| 3 | After Finerenone scope and record type rule | |
| 4 | Dates vs lookback end (days) | |
| 5 | Flag per window | |
| 6 | Final feature value | |
| 7 | Match | |

**Results (20 Nov 2026).** Raw `FACT_CALL` rows per BHID, 2023-06-01 to 2026-09-17; rules applied in pandas.

| Case | PROVIDER_ID / BHID | Cohort | All calls | Medical | Finerenone, submitted | In 12M (days before END) | Output 6M / 12M | Match |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 Visit within 6M | 31074283 / BH48783944 | c28 | 38 | 4 | 4 | 4 (115, 208, 252, 343) | 1 / 1 | Yes |
| 2 Visit 7 to 11 months before | 11650911 / BH12677549 | c28 | 5 | 1 | 1 | 1 (225) | 0 / 1 | Yes |
| 3 No MSL contact | 7826645 / BH11773490 | c28 | 12 | 0 | 0 | 0 | 0 / 0 | Yes |
| 4 Visit just over 12M before | 10269286 / BH10251922 | c28 | 40 | 1 | 1 | 0 (nearest 377) | 0 / 0 | Yes |
| 5 Training cohort | 27636499 / BH28769912 | c10 | 39 | 2 | 2 | 1 (14) | 1 / 1 | Yes |

Not traced: an `Event_vod` record (25 exist; counted, see section 4).

## 7. Points found during QC

* 37% of Finerenone MSL doctors are outside the universe (cell 9 figure, not recomputed): confirm this is expected.
* `Event_vod` records (25) are counted as MSL interactions (Finerenone product, no medical record type).
* MSL flag share rises over the cohorts (12M: 0.91% at c1, 1.48% at c28).
* Same 38 shared BHIDs as F2F / iRep.

## 8. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | 12 / 13 (Q13 not reviewed) |
| Decisions (to agree) | (a) Keep the 25 `Event_vod` records or set `REQUIRE_MEDICAL_REC_TYPE = True`. (b) Confirm the 37% of MSL doctors outside the universe is expected |
| Fixes made to the notebook | None (QC was read-only) |
| Ready for modelling | Yes |
| Next channel | 04 Message features |
