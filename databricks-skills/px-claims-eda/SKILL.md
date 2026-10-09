---
name: px-claims-eda
description: >
  Guidance for querying and exploring raw IQVIA LAAD PX (procedure) claims data in the Chronic Kidney
  Disease (CKD) therapeutic area. Read this skill when the user asks to explore procedure claims,
  CPT/HCPCS codes, dialysis procedures, echocardiograms, lab procedure codes, or CKD-related
  procedure queries against the PHCDW IQVIA LAAD tables.
---

# PX Claims EDA — IQVIA LAAD Data for CKD Therapeutic Area

This skill provides context and query patterns for exploratory data analysis on the raw IQVIA Longitudinal
Anonymized Analytic Dataset (LAAD) PX (procedure) claims data, scoped to the Chronic Kidney Disease (CKD)
therapeutic area for the Kerendia (finerenone) franchise.

**Note:** Unlike RX and DX claims, PX claims are used **only at the patient level** — there are no
HCP-level PX queries in the pipeline.

## Data Model

The IQVIA LAAD PX data uses a simple **fact + dimension** structure.

### Fact Table

| Table | Description |
| --- | --- |
| `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_PX` | Core PX claims fact table. One row per procedure claim event. |

**Key columns:** `CLAIM_ID`, `PATIENT_ID`, `SERVICE_DATE` (always aliased as `SVC_DT`), `PROCEDURE_CODE`, `PROVIDER_RENDERING_ID`, `PROVIDER_REFERRING_ID`, `PAYER_PLAN_ID`, `DATA_SOURCE`.

**Provider ID handling:** Same pattern as DX claims — the fact table has **two** provider columns:
```sql
COALESCE(PX.PROVIDER_REFERRING_ID, PX.PROVIDER_RENDERING_ID) AS PROVIDER_ID
```

### Dimension Table

| Table | Join Key | Description |
| --- | --- | --- |
| `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRCDR_CD` | `PROCEDURE_CODE` | Procedure descriptions. Columns: `PROCEDURE_CODE`, `PROCEDURE_DESCRIPTION`. |

---

## Three Patient-Level PX Queries

All PX claims queries are patient-level only (no HCP-level PX queries exist).

| Level | Purpose | Key Filter | Source |
| --- | --- | --- | --- |
| **12M & First Occurrence** | CKD-specific procedures for frequency/recency features | 5 CKD `PROCEDURE_DESCRIPTION` values, `SVC_DT <= lookback_end` | `01_Input_data_creation` Cell 40 |
| **All Events** | Broad procedure claims for all-event features | `SVC_DT <= lookback_end`, post-filtered by `Px Event List.csv` + echo test grouping | `01_Input_data_creation` Cells 47–54 |
| **Hospitalization** | Hospital-only PX claims | `DATA_SOURCE = 'HX'`, no date filter, post-filtered by `Px Event List.csv` | `01_Input_data_creation` Cells 57–59 |

---

## Patient-Level Query: 12-Month & First Occurrence Features

Filters to **5 specific CKD-relevant procedure descriptions**. No date lower bound — retrieves full history up to `lookback_end`.

```sql
SELECT
  PX.CLAIM_ID, PX.PATIENT_ID,
  PX.SERVICE_DATE AS SVC_DT,
  PX.PROCEDURE_CODE,
  PX_CODES.PROCEDURE_DESCRIPTION,
  COALESCE(PX.PROVIDER_REFERRING_ID, PX.PROVIDER_RENDERING_ID) AS PROVIDER_ID,
  PX.PROVIDER_REFERRING_ID, PX.PROVIDER_RENDERING_ID,
  PX.PAYER_PLAN_ID
FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_PX PX
INNER JOIN (
  SELECT DISTINCT PROCEDURE_CODE, PROCEDURE_DESCRIPTION
  FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRCDR_CD
) PX_CODES
  ON PX.PROCEDURE_CODE = PX_CODES.PROCEDURE_CODE
WHERE PROCEDURE_DESCRIPTION IN (
  'ALBUMIN; URINE (EG, MICROALBUMIN), QUANTITATIVE',
  'CREATININE; OTHER SOURCE',
  'END-STAGE RENAL DISEASE (ESRD) RELATED SERVICES MONTHLY, FOR PATIENTS 20 YEARS OF AGE AND OLDER; WIT',
  'GLUCOSE; QUANTITATIVE, BLOOD (EXCEPT REAGENT STRIP)',
  'UNLISTED DIALYSIS PROCEDURE, INPATIENT OR OUTPATIENT'
)
  AND SVC_DT <= '{lookback_end}'
```

**CKD-Relevant Procedures (5 values):**

| Procedure Description | Clinical Significance |
| --- | --- |
| ALBUMIN; URINE (EG, MICROALBUMIN), QUANTITATIVE | UACR testing — kidney damage marker |
| CREATININE; OTHER SOURCE | eGFR calculation — kidney function marker |
| END-STAGE RENAL DISEASE (ESRD) RELATED SERVICES MONTHLY... | ESRD management services |
| GLUCOSE; QUANTITATIVE, BLOOD (EXCEPT REAGENT STRIP) | Diabetes monitoring (CKD comorbidity) |
| UNLISTED DIALYSIS PROCEDURE, INPATIENT OR OUTPATIENT | Dialysis — advanced CKD treatment |

---

## Patient-Level Query: All Events Features

Retrieves the **full procedure universe** up to `lookback_end`. No procedure filter in SQL — post-filtered in PySpark against a dynamic `Px Event List.csv`, then echocardiogram procedure codes are grouped into a single `echo_tests` category.

```sql
SELECT
  PX.CLAIM_ID, PX.PATIENT_ID,
  PX.SERVICE_DATE AS SVC_DT,
  PX.PROCEDURE_CODE,
  PX_CODES.PROCEDURE_DESCRIPTION,
  COALESCE(PX.PROVIDER_REFERRING_ID, PX.PROVIDER_RENDERING_ID) AS PROVIDER_ID,
  PX.PROVIDER_REFERRING_ID, PX.PROVIDER_RENDERING_ID,
  PX.PAYER_PLAN_ID
FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_PX PX
INNER JOIN (
  SELECT DISTINCT PROCEDURE_CODE, PROCEDURE_DESCRIPTION
  FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRCDR_CD
) PX_CODES
  ON PX.PROCEDURE_CODE = PX_CODES.PROCEDURE_CODE
WHERE SVC_DT <= '{lookback_end}'
```

**Post-query PySpark processing:**
```python
# Step 1: Filter to prevalent events
px_event_list = pd.read_csv("/Volumes/.../feature_selection/Kerendia NBA 3.0 - Px Event List.csv")
px_claims_filtered = px_claims_filtered.filter(
    col("PROCEDURE_DESCRIPTION").isin(px_event_list["EVENT_NAME"].tolist())
)

# Step 2: Group echocardiogram procedure codes into single "echo_tests" category
echo_test_procedure_codes = [
    "93303", "93304", "93306", "93307", "93308", "93312", "93313", "93314",
    "93315", "93316", "93317", "93318", "93319", "93320", "93321", "93325",
    "93350", "93351", "93352", "93355", "93356", "93662",
    "0439T", "0932T",
    "C8921", "C8922", "C8923", "C8924", "C8925", "C8926",
    "C8927", "C8928", "C8929", "C8930", "C9786"
]
px_claims_filtered = px_claims_filtered.withColumn(
    "PROCEDURE_DESCRIPTION",
    when(col("PROCEDURE_CODE").isin(echo_test_procedure_codes), "echo_tests")
    .otherwise(col("PROCEDURE_DESCRIPTION"))
)
```

### Echocardiogram Code Grouping

The pipeline groups **35 CPT/HCPCS codes** for echocardiogram-related procedures into a single event called `echo_tests`. These codes cover transthoracic echocardiography (TTE), transesophageal echocardiography (TEE), stress echocardiography, and related add-on codes.

Code prefixes:
* `933xx` — CPT codes for echocardiography
* `0439T`, `0932T` — Category III CPT tracking codes
* `C89xx`, `C97xx` — HCPCS codes for echocardiography services

---

## Patient-Level Query: Hospitalization Events

Retrieves **hospital-only PX claims** via `DATA_SOURCE = 'HX'`. Note: unlike the other two queries, this one has **no date filter** in SQL — it pulls the full hospitalization history.

```sql
SELECT
  PX.CLAIM_ID, PX.PATIENT_ID,
  PX.SERVICE_DATE AS SVC_DT,
  PX.PROCEDURE_CODE,
  PX_CODES.PROCEDURE_DESCRIPTION,
  COALESCE(PX.PROVIDER_REFERRING_ID, PX.PROVIDER_RENDERING_ID) AS PROVIDER_ID,
  PX.PROVIDER_REFERRING_ID, PX.PROVIDER_RENDERING_ID,
  PX.PAYER_PLAN_ID
FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_PX PX
INNER JOIN (
  SELECT DISTINCT PROCEDURE_CODE, PROCEDURE_DESCRIPTION
  FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRCDR_CD
) PX_CODES
  ON PX.PROCEDURE_CODE = PX_CODES.PROCEDURE_CODE
WHERE DATA_SOURCE = 'HX'
```

**Post-query PySpark filtering:** Same `Px Event List.csv` filter as All Events.

---

## Key Differences: PX vs DX vs RX Claims

| Aspect | PX Claims | DX Claims | RX Claims |
| --- | --- | --- | --- |
| Fact table | `STG_CAR_IQV_LAAD_FACT_PX` | `STG_CAR_IQV_LAAD_FACT_DX` | `STG_CAR_IQV_LAAD_FCT_RX` |
| Dimension table | `STG_CAR_IQV_LAAD_DIM_PRCDR_CD` | `STG_CAR_IQV_LAAD_DIM_DIAG` | `STG_CAR_IQV_LAAD_DIM_PRD` |
| Event key | `PROCEDURE_CODE` → `PROCEDURE_DESCRIPTION` | `DIAGNOSIS_CODE` → `DIAGNOSIS_DESCRIPTION` | `NDC_CD` → `PRODUCT_NAME` |
| Provider ID | `COALESCE(REFERRING, RENDERING)` | `COALESCE(REFERRING, RENDERING)` | Direct `PROVIDER_ID` |
| HCP-level queries | **None** | DX_03, DX_09 | Rx_01 |
| Unique post-processing | Echo test code grouping | None | Treatment category mapping |

---

## Common EDA Query Patterns

### 1. Procedure Volume by Description (Monthly)
```sql
SELECT
  DATE_TRUNC('MONTH', SVC_DT) AS SVC_MONTH,
  PROCEDURE_DESCRIPTION,
  COUNT(*) AS claim_count,
  COUNT(DISTINCT PATIENT_ID) AS unique_patients
FROM <base_query_as_CTE>
GROUP BY 1, 2
ORDER BY 1, 2
```

### 2. Top Procedures by Frequency
```sql
SELECT
  PROCEDURE_DESCRIPTION,
  COUNT(*) AS claim_count,
  COUNT(DISTINCT PATIENT_ID) AS unique_patients
FROM <base_query_as_CTE>
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20
```

### 3. Hospitalization vs Outpatient Procedures
```sql
SELECT
  DATA_SOURCE,
  COUNT(*) AS claim_count,
  COUNT(DISTINCT PATIENT_ID) AS unique_patients,
  COUNT(DISTINCT PROCEDURE_CODE) AS unique_procedures
FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_PX
WHERE DATA_SOURCE IN ('HX', 'PB')
GROUP BY 1
```

### 4. CKD Lab Procedure Trends
```sql
SELECT
  DATE_TRUNC('MONTH', SVC_DT) AS SVC_MONTH,
  PROCEDURE_DESCRIPTION,
  COUNT(DISTINCT PATIENT_ID) AS unique_patients
FROM <12M_query_as_CTE>
WHERE PROCEDURE_DESCRIPTION IN (
  'ALBUMIN; URINE (EG, MICROALBUMIN), QUANTITATIVE',
  'CREATININE; OTHER SOURCE'
)
GROUP BY 1, 2
ORDER BY 1
```

---

## Downstream Feature Engineering

The patient-level PX queries feed into the same **cohort-based feature accelerator** as RX and DX claims:

| Concept | Description |
| --- | --- |
| **Anchor Date** | Reference point in time from which patient journey is measured |
| **Lookback Window** | Period before anchor date for computing features (default 12 months for frequency features) |
| **EVENT_TIME** | `DATEDIFF(LOOKBACK_END_DATE, EVENT_DATE)` — days since event from end of lookback |
| **EVENT_NAME** | `PROCEDURE_DESCRIPTION` for PX claims (with echo codes grouped into `echo_tests`) |

Feature types generated (same as RX/DX):
* **Frequency** — Count of procedure events in past N days
* **Recency** — Days since most recent occurrence of each procedure
* **Change in Frequency** — Variation in procedure occurrence over time
* **First Occurrence** — When a procedure first appeared in the patient's history
* **Skewness** — Concentration of procedure events in the patient's journey

---

## Notebook References

**Patient-Level Pipeline:**
- Input data creation: [01_Input_data_creation](/editor/notebooks/2494728515032330) — Cell 40 (12M & First Occ), Cells 47–54 (All Events + echo grouping), Cells 57–59 (Hospitalization).
- PX feature engineering: [03_px_features_rec_&_first_occ](/editor/notebooks/2494728515032400) — Frequency, recency, first-occurrence, skewness features.
- PX Event List: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/feature_selection/Kerendia NBA 3.0 - Px Event List.csv`

**Shared Infrastructure:**
- Config: [00_config](/editor/notebooks/2494728515032290) — Date parameters (`lookback_start`, `lookback_end`, etc.)
- Data loading: [00_load_processed_data](/editor/notebooks/2494728515032293) — Cohort generation, DataFrame merging.

---

## Execution Notes

> **CRITICAL:** All IQVIA LAAD PX claims queries execute against **Snowflake**, NOT Databricks SQL.
> They **cannot** be run via `spark.sql()` or a Databricks SQL warehouse. They **must** be executed
> using `Get_Data_Snowflakes(query)` after importing the connection notebook.

See [query-template.md](query-template.md) for the full setup boilerplate, all 3 PX query patterns
with ready-to-use code cells, and dialect notes.

### Mandatory Setup

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```

### Pre-materialized Delta Outputs

Prefer reading Delta when the data is already available:
- **12M & First Occ:** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/px_input_claims_12M_and_first_occ_features_input`
- **All Events:** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/px_input_claims_all_events_features_input`
- **Hospitalization:** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/px_hospitalization_claims_all_events_features_input`
