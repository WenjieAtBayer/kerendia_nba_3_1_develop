---
name: lab-claims-eda
description: >
  Guidance for querying and exploring IQVIA LAAD lab test data (GFR/eGFR and UACR) for the Chronic
  Kidney Disease (CKD) therapeutic area. Read this skill when the user asks to explore lab test
  results, GFR values, UACR levels, CKD staging from lab data, kidney function markers, or
  Quest/LabCorp/Prognose lab queries against the PHCDW IQVIA tables.
---

# Lab Claims EDA — IQVIA LAAD Data for CKD Therapeutic Area

This skill provides context and query patterns for exploratory data analysis on the IQVIA lab test data
(Quest/LabCorp/Prognose), scoped to the Chronic Kidney Disease (CKD) therapeutic area for the Kerendia
(finerenone) franchise.

**Key difference from RX/DX/PX:** Lab data comes from a single historical source table
(`STG_CAR_IQV_QUEST_TO_LAAD_HIST`) — not a fact+dimension star schema. It requires significant
data-quality filtering and date-format parsing.

## Data Model

### Primary Source Table

| Table | Description |
| --- | --- |
| `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_QUEST_TO_LAAD_HIST` | Historical lab test results from Quest Diagnostics, LabCorp, and Prognose. Contains raw GFR and UACR test data. |

**Key columns:** `NPI_ID`, `PATIENT_ID`, `SVC_DT` (text — requires parsing), `LCL_LAB_TEST_NM` / `LCL_LAB_TEST_NM_CLEAN`, `LCL_LAB_TEST_VAL_TXT`, `LCL_LAB_TEST_RSLT_UOM_CD` / `LCL_LAB_TEST_RSLT_UOM_CD_CLEAN`.

**IMPORTANT — Date parsing required:** `SVC_DT` is stored as **text** in two formats:
```sql
CASE
  WHEN SVC_DT LIKE '%/%/%' THEN TO_DATE(SVC_DT, 'MM/DD/YYYY')
  ELSE TO_DATE(LEFT(SVC_DT, 9), 'DDMONYYYY')
END AS SVC_DT_STD
```

### Provider Dimension Tables (varies by query)

| Table | Used In | Join |
| --- | --- | --- |
| `PHCDW.PHCDW_STG_CAR.STG_IQVIA_LAAD_DIM_PROVIDER` | Lab_03 (HCP-level) | `NPI_ID = NPI_NUMBER` |
| `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRVDR` | Patient-level, Pat Journey Lab | `NPI_ID = NPI_NUMBER` |

---

## Test Type Classification

Lab test names are classified into two CKD-relevant test types:

```sql
CASE
  WHEN UPPER(LCL_LAB_TEST_NM) LIKE '%GFR%'
    OR UPPER(LCL_LAB_TEST_NM) LIKE '%GLOMERULAR%' THEN 'GFR'
  WHEN UPPER(LCL_LAB_TEST_NM) LIKE '%ALB%'
    OR UPPER(LCL_LAB_TEST_NM) LIKE '%RATIO%' THEN 'UACR'
  ELSE 'OTHER'
END AS TEST_TYPE
```

**Note:** Some queries use `LCL_LAB_TEST_NM_CLEAN` (cleaned column) instead of `LCL_LAB_TEST_NM`.

## Mandatory Data Quality Filters

All lab queries apply these filters to clean raw test values:

```sql
WHERE LCL_LAB_TEST_VAL_TXT IS NOT NULL
  AND TRIM(LCL_LAB_TEST_VAL_TXT) NOT ILIKE '%-%'
  AND TRIM(LCL_LAB_TEST_VAL_TXT) NOT ILIKE '%>%'
  AND TRIM(LCL_LAB_TEST_VAL_TXT) NOT ILIKE '%<%'
  AND REGEXP_LIKE(TRIM(LCL_LAB_TEST_VAL_TXT), '^[0-9]+(\\.[0-9]+)?$')
```

Additional standard filters:
* **Unit of measure:** `UPPER(REPLACE(LCL_LAB_TEST_RSLT_UOM_CD, ' ','')) IN ('ML/MIN/1.73M2', 'MCG/MGCREAT', 'MG/G{CREAT}', 'MG/GCREAT', 'MG/GCR')`
* **Specialty codes:** `PRIMARY_SPECIALTY_CODE IN ('FM', 'FPG', 'GP', 'GPM', 'IFP', 'IM', 'IMG', 'IPM', 'NRP', 'PHA')`
* **Test type:** `TEST_TYPE <> 'OTHER'`
* **Patient ID validation:** `REGEXP_LIKE(PATIENT_ID, '^[0-9]+$')`

## CKD Staging from Lab Results

### GFR → CKD Stage (text labels)

| GFR Value | Stage Label |
| --- | --- |
| < 15 | CHRONIC KIDNEY DISEASE, STAGE 5 |
| 15–29 | CHRONIC KIDNEY DISEASE, STAGE 4 (SEVERE) |
| 30–59 | CHRONIC KIDNEY DISEASE, STAGE 3 (MODERATE) |
| 60–89 | CHRONIC KIDNEY DISEASE, STAGE 2 (MILD) |
| 90–150 | CHRONIC KIDNEY DISEASE, STAGE 1 |

### GFR → CKD Stage (numeric, used in Pat Journey Lab)

| GFR Value | GFR_STAGE |
| --- | --- |
| < 15 | 5 |
| 15–29 | 4 |
| 30–59 | 3 |
| 60–89 | 2 |
| 90–150 | 1 |

### UACR Staging

| UACR Value | Stage (text) | UACR_STAGE (numeric) |
| --- | --- | --- |
| < 30 | A1 | 1 |
| 30–299 | A2 | 2 |
| >= 300 | A3 | 3 |

---

## Four Lab Query Levels

| Level | Purpose | Output Columns | Source |
| --- | --- | --- | --- |
| **Patient-Level (12M & First Occ)** | GFR/UACR median per patient-provider-date | `PROVIDER_ID`, `PATIENT_ID`, `SVC_DT`, `TEST_TYPE`, `MEDIAN_TEST_RESULT` | `01_Input_data_creation` Cell 61 |
| **HCP-Level (Lab_03)** | CKD staging with text labels per NPI | `NPI_NUMBER`, `PATIENT_ID`, `SVC_DT`, `TEST_TYPE`, `MEDIAN_TEST_RESULT`, `STAGE` | `00_Write_Input_Files` Cell 17 |
| **HCP-Level (Lab_04)** | Same as Lab_03, uses cleaned column names | Same as Lab_03 | `00_Write_Input_Files` Cell 32 |
| **HCP-Level (Pat Journey Lab)** | Numeric GFR/UACR stages for patient journey | `PATIENT_ID`, `DATE`, `NPI_NUMBER`, `TEST_TYPE`, `MEDIAN_TEST_RESULT`, `GFR_STAGE`, `UACR_STAGE` | `00_Write_Input_Files` Cell 61 |

**Note:** A legacy "Komodo Lab 24" query (Cell 87) exists but is **fully commented out / deprecated** and should not be used.

---

## Patient-Level Query: 12M & First Occurrence

Aggregates lab results to `MEDIAN(test_value)` per provider–patient–date–test_type. No date lower bound in SQL; filtered in PySpark to `SVC_DT <= lookback_end`.

```sql
SELECT PROVIDER_ID, PATIENT_ID, SVC_DT, TEST_TYPE,
  MEDIAN(LCL_LAB_TEST_VAL_TXT_FLOAT) AS MEDIAN_TEST_RESULT
FROM (
  SELECT DISTINCT
    CAST(PROVIDER_ID AS VARCHAR(64)) AS PROVIDER_ID,
    CAST(CAST(PATIENT_ID AS INT) AS VARCHAR(64)) AS PATIENT_ID,
    SVC_DT_STD AS SVC_DT, TEST_TYPE,
    TRY_TO_DOUBLE(TRIM(LCL_LAB_TEST_VAL_TXT)) AS LCL_LAB_TEST_VAL_TXT_FLOAT
  FROM (
    SELECT *,
      CASE WHEN UPPER(LCL_LAB_TEST_NM_CLEAN) LIKE '%GFR%' OR UPPER(LCL_LAB_TEST_NM_CLEAN) LIKE '%GLOMERULAR%' THEN 'GFR'
           WHEN UPPER(LCL_LAB_TEST_NM_CLEAN) LIKE '%ALB%' OR UPPER(LCL_LAB_TEST_NM_CLEAN) LIKE '%RATIO%' THEN 'UACR'
           ELSE 'OTHER' END AS TEST_TYPE,
      CASE WHEN SVC_DT LIKE '%/%/%' THEN TO_DATE(SVC_DT,'MM/DD/YYYY')
           ELSE TO_DATE(LEFT(SVC_DT,9),'DDMONYYYY') END AS SVC_DT_STD
    FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_QUEST_TO_LAAD_HIST
    WHERE REGEXP_LIKE(PATIENT_ID, '^[0-9]+$')
      AND LCL_LAB_TEST_VAL_TXT IS NOT NULL
      AND TRIM(LCL_LAB_TEST_VAL_TXT) NOT ILIKE '%-%'
      AND TRIM(LCL_LAB_TEST_VAL_TXT) NOT ILIKE '%>%'
      AND TRIM(LCL_LAB_TEST_VAL_TXT) NOT ILIKE '%<%'
      AND REGEXP_LIKE(TRIM(LCL_LAB_TEST_VAL_TXT), '^[0-9]+(\\.[0-9]+)?$')
  ) lab1
  LEFT JOIN PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRVDR dct
    ON lab1.NPI_ID = dct.NPI_NUMBER
  WHERE UPPER(REPLACE(LCL_LAB_TEST_RSLT_UOM_CD_CLEAN, ' ','')) IN
    ('ML/MIN/1.73M2','MCG/MGCREAT','MG/G{CREAT}','MG/GCREAT','MG/GCR')
    AND PRIMARY_SPECIALTY_CODE IN ('FM','FPG','GP','GPM','IFP','IM','IMG','IPM','NRP','PHA')
    AND TEST_TYPE <> 'OTHER'
) LAB
GROUP BY 1, 2, 3, 4
```

---

## HCP-Level Query: Lab_03 — CKD Staging (Text Labels)

CTE-based query that computes median lab values per NPI–patient–date, then derives CKD `STAGE` as text labels. Uses **`LCL_LAB_TEST_NM`** (uncleaned) and **`LCL_LAB_TEST_RSLT_UOM_CD`** (uncleaned). Joins to `STG_IQVIA_LAAD_DIM_PROVIDER`.

Output: `SVC_DT, NPI_NUMBER, PATIENT_ID, TEST_TYPE, MEDIAN_TEST_RESULT, STAGE`

See [query-template.md](query-template.md) Pattern 2 for the full query.

---

## HCP-Level Query: Lab_04 — CKD Staging (Cleaned Columns)

Nearly identical to Lab_03 but uses **`LCL_LAB_TEST_RSLT_UOM_CD_CLEAN`** (cleaned UOM column) and adds `REGEXP_LIKE(PATIENT_ID, '^[0-9]+$')` validation. Same staging logic.

See [query-template.md](query-template.md) Pattern 3 for the full query.

---

## HCP-Level Query: Pat Journey Lab — Numeric Staging

Used for **patient journey features** in the HCP-level pipeline. Returns **numeric** `GFR_STAGE` (1–5) and `UACR_STAGE` (1–3) instead of text labels. Has a hardcoded date lower bound of `SVC_DT_STD >= '2021-11-30'` (near Kerendia launch).

Output: `PATIENT_ID, DATE, NPI_NUMBER, TEST_TYPE, MEDIAN_TEST_RESULT, GFR_STAGE, UACR_STAGE`

See [query-template.md](query-template.md) Pattern 4 for the full query.

---

## Key Differences: Lab vs RX/DX/PX

| Aspect | Lab Data | RX/DX/PX Claims |
| --- | --- | --- |
| Source structure | Single historical table | Fact + dimension star schema |
| Source table | `STG_CAR_IQV_QUEST_TO_LAAD_HIST` | `STG_CAR_IQV_LAAD_FCT_RX` / `FACT_DX` / `FACT_PX` |
| Date column | `SVC_DT` (text, needs parsing) | `SVC_DT` or `SERVICE_DATE` (date type) |
| Provider column | `NPI_ID` (join to dim for PROVIDER_ID) | `PROVIDER_ID` or `COALESCE(REFERRING, RENDERING)` |
| Aggregation in SQL | `MEDIAN()` per patient-date-test | Usually no aggregation (distinct rows) |
| Key metric | `MEDIAN_TEST_RESULT` (numeric) | Claim counts / event presence |
| CKD scoping | Test type classification (GFR/UACR) | Product mapping / ICD codes / procedure descriptions |

---

## Common EDA Query Patterns

### 1. Lab Test Volume by Month and Test Type
```sql
SELECT DATE_TRUNC('MONTH', SVC_DT) AS SVC_MONTH, TEST_TYPE,
  COUNT(*) AS test_count, COUNT(DISTINCT PATIENT_ID) AS unique_patients
FROM <base_query_as_CTE>
GROUP BY 1, 2 ORDER BY 1, 2
```

### 2. CKD Stage Distribution from GFR
```sql
SELECT STAGE, COUNT(DISTINCT PATIENT_ID) AS unique_patients, COUNT(*) AS test_count
FROM <Lab_03_query_as_CTE>
WHERE TEST_TYPE = 'GFR'
GROUP BY 1 ORDER BY 1
```

### 3. UACR Stage Distribution
```sql
SELECT STAGE, COUNT(DISTINCT PATIENT_ID) AS unique_patients
FROM <Lab_03_query_as_CTE>
WHERE TEST_TYPE = 'UACR'
GROUP BY 1 ORDER BY 1
```

### 4. Median GFR Over Time per Provider
```sql
SELECT NPI_NUMBER, DATE_TRUNC('MONTH', SVC_DT) AS SVC_MONTH,
  MEDIAN(MEDIAN_TEST_RESULT) AS MONTHLY_MEDIAN_GFR
FROM <Lab_03_query_as_CTE>
WHERE TEST_TYPE = 'GFR'
GROUP BY 1, 2 ORDER BY 1, 2
```

---

## Downstream Feature Engineering

The patient-level lab query feeds the same **cohort-based feature accelerator** as RX/DX/PX:

| Concept | Description |
| --- | --- |
| **EVENT_NAME** | `TEST_TYPE` for lab claims (GFR or UACR) |
| **EVENT_TIME** | `DATEDIFF(LOOKBACK_END_DATE, EVENT_DATE)` |

Feature types: Frequency, Recency, Change in Frequency, First Occurrence, Skewness.

---

## Notebook References

**Patient-Level Pipeline:**
- Input data creation: [01_Input_data_creation](/editor/notebooks/2494728515032330) — Cell 61 (Lab 12M & First Occ query).
- Lab feature engineering: [04_lab_features_rec_&_first_occ](/editor/notebooks/2494728515032401) — Frequency, recency, first-occurrence, skewness features.

**HCP-Level Pipeline:**
- Query origin: [00_Write_Input_Files](/editor/notebooks/2494728515032387) — Cell 17 (Lab_03), Cell 32 (Lab_04), Cell 61 (Pat Journey Lab), Cell 87 (Komodo Lab — deprecated).
- Lab feature engineering: [02_claim_lab_monthly](/editor/notebooks/2494728515032388) — Monthly lab features per HCP.

**Shared Infrastructure:**
- Config: [00_config](/editor/notebooks/2494728515032290)
- Data loading: [00_load_processed_data](/editor/notebooks/2494728515032293)

---

## Execution Notes

> **CRITICAL:** All lab queries execute against **Snowflake**, NOT Databricks SQL.
> They **must** be executed using `Get_Data_Snowflakes(query)` after importing the connection notebook.

See [query-template.md](query-template.md) for the full setup boilerplate, all 4 query patterns, and dialect notes.

### Mandatory Setup

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```

### Pre-materialized Delta Outputs

- **Patient-level (12M & First Occ):** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/lab_input_claims_12M_and_first_occ_features_input`
- **HCP-level (Lab_03):** `.../query_output/Lab_03`
- **HCP-level (Lab_04):** `.../query_output/Lab_04`
- **HCP-level (Pat Journey Lab):** `.../query_output/kerendia_nba_3_0_lab_query_output`

(All under `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/`)
