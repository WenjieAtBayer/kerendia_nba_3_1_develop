---
name: iqvia-claims-overview
description: >
  High-level overview of all IQVIA LAAD claims data (RX, DX, PX, Lab) for the CKD/Kerendia
  therapeutic area. Read this skill FIRST when the user asks a broad question about IQVIA claims,
  patient journeys across claim types, the overall data model, shared infrastructure, or when you
  need to decide which specialized claim skill to load. Routes to rx-claims-eda, dx-claims-eda,
  px-claims-eda, or lab-claims-eda for detailed query patterns.
---

# IQVIA LAAD Claims Overview — CKD / Kerendia Therapeutic Area

This is the **master routing skill** for the IQVIA Longitudinal Anonymized Analytic Dataset (LAAD)
used in the Kerendia (finerenone) NBA (Next Best Action) pipeline. It maps the full data landscape
across four claim types and routes to specialized skills for detailed queries.

## When to Use This Skill vs Specialized Skills

| User Question | Load This Skill | Then Route To |
| --- | --- | --- |
| Broad IQVIA data questions, data model overview | Yes | — |
| Cross-claim patient journey analysis | Yes | Multiple specialized skills |
| Prescription/drug/treatment queries | No | `rx-claims-eda` directly |
| Diagnosis/ICD/CKD staging queries | No | `dx-claims-eda` directly |
| Procedure/CPT/dialysis queries | No | `px-claims-eda` directly |
| Lab test/GFR/UACR queries | No | `lab-claims-eda` directly |

---

## The Four Claim Types at a Glance

| Claim Type | Fact Table | Dimension(s) | Event Key | Provider ID Pattern | HCP-Level? | Patient-Level? |
| --- | --- | --- | --- | --- | --- | --- |
| **RX** (Prescriptions) | `STG_CAR_IQV_LAAD_FCT_RX` | `DIM_PRD` (product), `DIM_PLN` (plan), `DIM_PTNT_DMGRPHC` (patient), `DIM_PRVDR` (provider) + `CKD_PRODUCT_MAPPING_VW` | `NDC_CD` → `PRODUCT_NAME` / `PRODUCT_GROUP` | Direct `PROVIDER_ID` | Yes (Rx_01) | Yes (12M, Total Events) |
| **DX** (Diagnoses) | `STG_CAR_IQV_LAAD_FACT_DX` | `DIM_DIAG` / `DIM_DIAGNOSIS` + `FIN_DIAG_CD` (comorbidity) | `DIAGNOSIS_CODE` → `DIAGNOSIS_DESCRIPTION` | `COALESCE(REFERRING, RENDERING)` | Yes (DX_03, DX_09) | Yes (12M, All Events, Hosp) |
| **PX** (Procedures) | `STG_CAR_IQV_LAAD_FACT_PX` | `DIM_PRCDR_CD` | `PROCEDURE_CODE` → `PROCEDURE_DESCRIPTION` | `COALESCE(REFERRING, RENDERING)` | **No** | Yes (12M, All Events, Hosp) |
| **Lab** (GFR/UACR) | `STG_CAR_IQV_QUEST_TO_LAAD_HIST` | `DIM_PRVDR` / `DIM_PROVIDER` | `LCL_LAB_TEST_NM` → `TEST_TYPE` (GFR/UACR) | `NPI_ID` (via provider dim) | Yes (Lab_03, Lab_04, Pat Journey) | Yes (12M) |

All tables are in schema **`PHCDW.PHCDW_STG_CAR`** except `CKD_PRODUCT_MAPPING_VW` (`PHCDW.PHCDW_DSAA`) and `FIN_DIAG_CD` (`PHCDW.PHCDW_SANDBOX`).

---

## Complete Query Inventory

### Patient-Level Queries (from `01_Input_data_creation`)

| # | Claim | Query | Cell | Date Filter | Post-Filter | Delta Output |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | RX | 12M Features | 9 | `lookback_start` → `lookback_end` | 29 PRODUCT_GROUPs | `rx_input_claims_12M_features_input` |
| 2 | RX | Total Events & First Occ | 16 | ≤ `lookback_end` | `Rx Event List.csv` | `rx_input_claims_total_events_and_first_occ_features_input` |
| 3 | DX | 12M & First Occ | 23 | ≤ `lookback_end` | 17 DIAGNOSIS_DESCRIPTIONs | `dx_input_claims_12M_and_first_occ_features_input` |
| 4 | DX | All Events | 28 | `lookback_start` → `lookback_end` | `Dx Event List.csv` | `dx_input_claims_all_events_features_input` |
| 5 | DX | Hospitalization | 35 | `lookback_start` → `lookback_end` | `DATA_SOURCE='HX'` + `Dx Event List.csv` | `dx_hospitalization_claims_all_events_features_input` |
| 6 | PX | 12M & First Occ | 40 | ≤ `lookback_end` | 5 PROCEDURE_DESCRIPTIONs | `px_input_claims_12M_and_first_occ_features_input` |
| 7 | PX | All Events | 47 | ≤ `lookback_end` | `Px Event List.csv` + echo grouping | `px_input_claims_all_events_features_input` |
| 8 | PX | Hospitalization | 57 | None | `DATA_SOURCE='HX'` + `Px Event List.csv` | `px_hospitalization_claims_all_events_features_input` |
| 9 | Lab | 12M & First Occ | 61 | ≤ `lookback_end` (PySpark) | Specialty + UOM filters | `lab_input_claims_12M_and_first_occ_features_input` |

### HCP-Level Queries (from `00_Write_Input_Files`)

| # | Claim | Query | Cell | Key Feature | Delta Output |
| --- | --- | --- | --- | --- | --- |
| 1 | RX | Rx_01 | 6 | Treatment category + brand mapping via `CKD_PRODUCT_MAPPING_VW` | `Rx_01_new` |
| 2 | DX | DX_03 | 25 | CKD staging (Stage 1–5) from 100+ ICD codes | `Dx_03` |
| 3 | DX | DX_09 | 44 | Comorbidity groups (KD, CV-KD, DB-KD) via `FIN_DIAG_CD` | `Dx_09` |
| 4 | Lab | Lab_03 | 17 | CKD staging text labels, uncleaned columns | `Lab_03` |
| 5 | Lab | Lab_04 | 32 | CKD staging text labels, cleaned columns | `Lab_04` |
| 6 | Lab | Pat Journey Lab | 61 | Numeric GFR_STAGE/UACR_STAGE, date ≥ 2021-11-30 | `kerendia_nba_3_0_lab_query_output` |

---

## Shared Infrastructure

### Connection (mandatory for ALL queries)

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```

Provides `Get_Data_Snowflakes(query)` — the **only** way to execute IQVIA queries. All tables live in Snowflake, not Databricks SQL.

### Config

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config"
```

Provides:

**Date parameters (dynamically loaded from control dates table):**

| Parameter | Description | Example |
| --- | --- | --- |
| `lookback_start` | Start of lookback window | `2024-08-31` |
| `lookback_end` | End of lookback window | `2025-09-30` |
| `date_start` / `date_end` | String versions of above | `"2024-08-31"` |
| `analysis_start_month` | YYYYMM integer for analysis start | `201901` |
| `current_month` | YYYYMM integer for current run | `202509` |
| `complete_history_start_month` | Full history start | `201901` |
| `complete_history_end_month` | Full history end | `202509` |
| `cohort_start_date` / `cohort_end_date` | Patient-level cohort boundaries | `"2025-11-01"` |
| `prediction_start` / `prediction_end` | Prediction window | `2025-11-07` / `2025-12-07` |
| `lookback_duration` | Days | `365` |
| `prediction_duration` | Days | `30` |
| `time_windows` | Feature engineering windows | `[30, 60, 90, 180, 270, 360]` |

**Column mappings per claim type:**

| Claim | ID Column | Patient Column | Date Column | Event Column |
| --- | --- | --- | --- | --- |
| RX | `PROVIDER_ID` | `PATIENT_ID` | `SVC_DT` | `PRODUCT_GROUP` |
| DX | `PROVIDER_ID` | `PATIENT_ID` | `SVC_DT` | `DIAGNOSIS_DESCRIPTION` |
| PX | `PROVIDER_ID` | `PATIENT_ID` | `SVC_DT` | `PROCEDURE_DESCRIPTION` |
| Lab | `PROVIDER_ID` | `PATIENT_ID` | `SVC_DT` | `TEST_TYPE` |

**Drug classification lists:**
* `kerendia_list` — `['KERENDIA']`
* `sglt2_list_by_prod_group` — FARXIGA, JARDIANCE, INVOKANA, STEGLATRO, BRENZAVVY, etc.
* `glp1_list` — TRULICITY, OZEMPIC, VICTOZA, RYBELSUS, etc.
* `ace_arbs_list`, `calcium_channel_blockers_list`, `diuretics_combos_list`, `beta_blockers_list`
* `mra_list`, `dpp4_list_by_prod_group`
* `echo_test_procedure_codes` — 35 CPT/HCPCS codes for echocardiogram grouping

### HCP Universe

All queries are filtered to a pre-defined HCP universe:
```python
hcp_universe = spark.read.format("delta").load(hcp_universe_path)
```
Path: `/Volumes/.../kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`

Provider-NPI mapping: `/Volumes/.../query_output/kerendia_nba_3_0_npi_bhid_mapping`

### Event Lists (for post-query filtering)

| Claim | CSV Path |
| --- | --- |
| RX | `/Volumes/.../feature_selection/Kerendia NBA 3.0 - Rx Event List.csv` |
| DX | `/Volumes/.../feature_selection/Kerendia NBA 3.0 - Dx Event List.csv` |
| PX | `/Volumes/.../feature_selection/Kerendia NBA 3.0 - Px Event List.csv` |

(All under `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/`)

### Feature Accelerator (shared across all claim types)

Patient-level queries feed into `DataFrameMerger` → cohort-based feature accelerator:
* **Frequency** — Count of events in past N days
* **Recency** — Days since most recent occurrence
* **Change in Frequency** — Variation over time
* **First Occurrence** — When event first appeared
* **Skewness** — Concentration of events

---

## Delta Output Volume Base Path

All materialized outputs live under:
```
/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/
```

---

## Specialized Skill Reference

| Skill | Files | Covers |
| --- | --- | --- |
| `rx-claims-eda` | `SKILL.md`, `query-template.md` | RX fact + 4 dims + CKD product mapping, treatment categories, brand classification, 3 queries |
| `dx-claims-eda` | `SKILL.md`, `query-template.md` | DX fact + diagnosis dims + comorbidity mapping, CKD staging, ICD codes, 5 queries |
| `px-claims-eda` | `SKILL.md`, `query-template.md` | PX fact + procedure dim, echo test grouping, 3 patient-level queries (no HCP-level) |
| `lab-claims-eda` | `SKILL.md`, `query-template.md` | Quest/LabCorp/Prognose lab data, GFR/UACR staging, date parsing, MEDIAN aggregation, 4 queries |

---

## Notebook References

**Input Data Creation:**
- [01_Input_data_creation](/editor/notebooks/2494728515032330) — All 9 patient-level queries (RX cells 9+16, DX cells 23+28+35, PX cells 40+47+57, Lab cell 61)
- [00_Write_Input_Files](/editor/notebooks/2494728515032387) — All 6 HCP-level queries (RX cell 6, DX cells 25+44, Lab cells 17+32+61)

**Feature Engineering:**
- [01_rx_features_rec_&_first_occ](/editor/notebooks/2494728515032398) — RX patient features
- [02_dx_features_rec_&_first_occ](/editor/notebooks/2494728515032399) — DX patient features
- [03_px_features_rec_&_first_occ](/editor/notebooks/2494728515032400) — PX patient features
- [04_lab_features_rec_&_first_occ](/editor/notebooks/2494728515032401) — Lab patient features
- [01_claim_rx_monthly](/editor/notebooks/2494728515032380) — RX HCP-level monthly features
- [02_claim_lab_monthly](/editor/notebooks/2494728515032388) — Lab HCP-level monthly features

**Shared Helpers:**
- [00_connection](/editor/notebooks/198916793189023) — Snowflake auth + `Get_Data_Snowflakes()`
- [00_config](/editor/notebooks/2494728515032290) — All date params, file paths, column mappings, drug lists
- [00_load_processed_data](/editor/notebooks/2494728515032293) — `DataFrameMerger` class for cohort generation
