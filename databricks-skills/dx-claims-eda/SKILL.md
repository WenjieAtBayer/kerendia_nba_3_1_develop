---
name: dx-claims-eda
description: >
  Guidance for querying and exploring raw IQVIA LAAD DX (diagnosis) claims data in the Chronic Kidney
  Disease (CKD) therapeutic area. Read this skill when the user asks to explore diagnosis claims,
  ICD codes, CKD staging from claims, comorbidity data, hospitalization events, or CKD-related
  diagnosis queries against the PHCDW IQVIA LAAD tables.
---

# DX Claims EDA — IQVIA LAAD Data for CKD Therapeutic Area

This skill provides context and query patterns for exploratory data analysis on the raw IQVIA Longitudinal
Anonymized Analytic Dataset (LAAD) DX (diagnosis) claims data, scoped to the Chronic Kidney Disease (CKD)
therapeutic area for the Kerendia (finerenone) franchise.

## Data Model

The IQVIA LAAD DX data uses a **fact + dimension** structure distinct from RX claims.

### Fact Table

| Table | Description |
| --- | --- |
| `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX` | Core DX claims fact table. One row per diagnosis claim event. |

**Key columns:** `CLAIM_ID`, `PATIENT_ID`, `SERVICE_DATE` (always aliased as `SVC_DT`), `DIAGNOSIS_CODE`, `PROVIDER_RENDERING_ID`, `PROVIDER_REFERRING_ID`, `PAYER_PLAN_ID`, `DATA_SOURCE`, `ICD_VERSION_TYPE`.

**Important — Provider ID handling:** Unlike the RX fact table (which has a single `PROVIDER_ID`), the DX fact table has **two** provider columns. Always derive the provider with:
```sql
COALESCE(PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID) AS PROVIDER_ID
```

### Dimension Tables

| Table | Join Key | Description |
| --- | --- | --- |
| `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_DIAG` | `DIAGNOSIS_CODE` | Diagnosis descriptions and ICD version. Columns: `DIAGNOSIS_CODE`, `DIAGNOSIS_DESCRIPTION`, `ICD_VERSION_TYPE`. Used in **patient-level** queries. |
| `PHCDW.PHCDW_STG_CAR.STG_IQVIA_LAAD_DIM_DIAGNOSIS` | `DIAGNOSIS_CODE` | Alternative diagnosis dimension with same structure. Used in **HCP-level DX_03** query for ICD code filtering. |
| `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PTNT_DMGRPHC` | `PATIENT_ID` | Patient demographics: `PATIENT_BIRTH_YEAR`, `PATIENT_GENDER`. |
| `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRVDR` | `PROVIDER_ID` | Provider info: `NPI_NUMBER`, `PRIMARY_SPECIALTY_CODE`, `PRIMARY_SPECIALTY_DESC`. |

### CKD Comorbidity Mapping (HCP-level only)

| Table | Join Key | Description |
| --- | --- | --- |
| `PHCDW.PHCDW_SANDBOX.FIN_DIAG_CD` | `DIAGNOSIS_CODE` | Maps diagnosis codes to comorbidity groups. Columns: `DIAGNOSIS_CODE`, `DIAGNOSIS_DESCRIPTION`, `DIAG_GRP`. Used in **DX_09** for CKD comorbidity features. Key groups: `'KD'` (Kidney Disease), `'CV-KD'` (Cardiovascular-KD), `'DB-KD'` (Diabetes-KD). |

---

## Five Levels of DX Claims Queries

The IQVIA LAAD DX data is queried at **five levels** depending on the analytical objective:

| Level | Purpose | Key Filter | Source |
| --- | --- | --- | --- |
| **Patient-Level (12M & First Occ)** | Claim-level detail for CKD-specific diagnoses | 17 CKD `DIAGNOSIS_DESCRIPTION` values, `SVC_DT <= lookback_end` | `01_Input_data_creation` Cell 23 |
| **Patient-Level (All Events)** | Broad diagnosis claims for all-event features | Date-bounded, post-filtered by `Dx Event List.csv` | `01_Input_data_creation` Cell 28 |
| **Patient-Level (Hospitalization)** | Hospital-only DX claims | `DATA_SOURCE = 'HX'`, post-filtered by `Dx Event List.csv` | `01_Input_data_creation` Cell 35 |
| **HCP-Level (DX_03)** | CKD staging per provider with ICD code list | 100+ ICD codes, full history window | `00_Write_Input_Files` Cell 25 |
| **HCP-Level (DX_09)** | Comorbidity features per provider | `DIAG_GRP IN ('KD','CV-KD','DB-KD')` via `FIN_DIAG_CD` | `00_Write_Input_Files` Cell 44 |

---

## Patient-Level Query: 12-Month & First Occurrence Features

Used for **patient-level feature engineering** (frequency, recency, first-occurrence of CKD-related diagnoses). Filters to 17 specific CKD-relevant `DIAGNOSIS_DESCRIPTION` values. No date lower bound — retrieves full history up to `lookback_end`.

```sql
SELECT DISTINCT
  CLAIM_ID, PATIENT_ID,
  SERVICE_DATE AS SVC_DT,
  DX_CLAIMS.DIAGNOSIS_CODE,
  DX_CODES.DIAGNOSIS_DESCRIPTION,
  COALESCE(PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID) AS PROVIDER_ID,
  PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID,
  PAYER_PLAN_ID, DX_CLAIMS.ICD_VERSION_TYPE
FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX DX_CLAIMS
INNER JOIN (
  SELECT DISTINCT DIAGNOSIS_CODE, DIAGNOSIS_DESCRIPTION, ICD_VERSION_TYPE
  FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_DIAG
) DX_CODES
  ON DX_CLAIMS.DIAGNOSIS_CODE = DX_CODES.DIAGNOSIS_CODE
WHERE SVC_DT <= '{lookback_end}'
  AND DIAGNOSIS_DESCRIPTION IN (
    'CHRONIC KIDNEY DISEASE, STAGE 3 UNSPECIFIED',
    'END STAGE RENAL DISEASE',
    'MIXED HYPERLIPIDEMIA',
    'PROTEINURIA, UNSPECIFIED',
    'TYPE 2 DIABETES MELLITUS WITH DIABETIC CHRONIC KIDNEY DISEASE',
    'CHRONIC COMBINED SYSTOLIC (CONGESTIVE) AND DIASTOLIC (CONGESTIVE) HEART FAILURE',
    'ACUTE ON CHRONIC SYSTOLIC (CONGESTIVE) HEART FAILURE',
    'ANEMIA IN CHRONIC KIDNEY DISEASE',
    'ATHEROSCLEROSIS OF AORTA',
    'CHRONIC KIDNEY DISEASE, STAGE 1',
    'HEART FAILURE, UNSPECIFIED',
    'UNSPECIFIED SYSTOLIC (CONGESTIVE) HEART FAILURE',
    'ATHEROSCLEROSIS OF RENAL ARTERY',
    'HYPERTENSIVE CHRONIC KIDNEY DISEASE WITH STAGE 5 CHRONIC KIDNEY DISEASE OR END STAGE RENAL DISEASE',
    'HYPERTENSIVE HEART AND CHRONIC KIDNEY DISEASE WITH HEART FAILURE AND STAGE 1 THROUGH STAGE 4 CHRONIC',
    'DIABETES MELLITUS DUE TO UNDERLYING CONDITION WITH DIABETIC NEPHROPATHY',
    'SECONDARY SIDEROBLASTIC ANEMIA DUE TO DISEASE'
  )
```

**CKD-Relevant Diagnosis Descriptions (17 values):** CKD Stage 1, CKD Stage 3 Unspecified, End Stage Renal Disease, Proteinuria, T2DM with Diabetic CKD, Heart Failure variants (combined systolic/diastolic, acute on chronic systolic, unspecified), Anemia in CKD, Atherosclerosis (aorta, renal artery), Hypertensive CKD (Stage 5/ESRD, with HF Stage 1-4), Diabetic Nephropathy, Mixed Hyperlipidemia, Secondary Sideroblastic Anemia.

---

## Patient-Level Query: All Events Features

Used for **broad diagnosis event features**. Date-bounded within the lookback window. No diagnosis filter in SQL — post-filtered in PySpark against a dynamic `Dx Event List.csv`.

```sql
SELECT DISTINCT
  CLAIM_ID, PATIENT_ID,
  SERVICE_DATE AS SVC_DT,
  DX_CLAIMS.DIAGNOSIS_CODE,
  DX_CODES.DIAGNOSIS_DESCRIPTION,
  COALESCE(PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID) AS PROVIDER_ID,
  PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID,
  PAYER_PLAN_ID, DX_CLAIMS.ICD_VERSION_TYPE
FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX DX_CLAIMS
INNER JOIN (
  SELECT DISTINCT DIAGNOSIS_CODE, DIAGNOSIS_DESCRIPTION, ICD_VERSION_TYPE
  FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_DIAG
) DX_CODES
  ON DX_CLAIMS.DIAGNOSIS_CODE = DX_CODES.DIAGNOSIS_CODE
WHERE SVC_DT >= '{lookback_start}'
  AND SVC_DT <= '{lookback_end}'
```

**Post-query PySpark filtering:**
```python
dx_event_list = pd.read_csv("/Volumes/.../feature_selection/Kerendia NBA 3.0 - Dx Event List.csv")
dx_claims_filtered = dx_claims_filtered.filter(
    col("DIAGNOSIS_DESCRIPTION").isin(dx_event_list["EVENT_NAME"].tolist())
)
```

---

## Patient-Level Query: Hospitalization Events

Used for **hospitalization-specific DX features**. Identical structure to the All Events query but filtered to hospital data only via `DATA_SOURCE = 'HX'`.

```sql
SELECT DISTINCT
  CLAIM_ID, PATIENT_ID,
  SERVICE_DATE AS SVC_DT,
  DX_CLAIMS.DIAGNOSIS_CODE,
  DX_CODES.DIAGNOSIS_DESCRIPTION,
  COALESCE(PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID) AS PROVIDER_ID,
  PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID,
  PAYER_PLAN_ID, DX_CLAIMS.ICD_VERSION_TYPE
FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX DX_CLAIMS
INNER JOIN (
  SELECT DISTINCT DIAGNOSIS_CODE, DIAGNOSIS_DESCRIPTION, ICD_VERSION_TYPE
  FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_DIAG
) DX_CODES
  ON DX_CLAIMS.DIAGNOSIS_CODE = DX_CODES.DIAGNOSIS_CODE
WHERE DATA_SOURCE = 'HX'
  AND SVC_DT >= '{lookback_start}'
  AND SVC_DT <= '{lookback_end}'
```

**Key:** `DATA_SOURCE = 'HX'` filters to hospital/inpatient claims only. Post-filtered against `Dx Event List.csv` same as the All Events query.

---

## HCP-Level Query: DX_03 — CKD Staging

Used for **HCP-level CKD staging features** (diagnosis stage per provider over time). This is the most complex DX query — it joins the fact table with patient demographics, provider dimension, and a curated list of 100+ ICD-9/ICD-10 codes for CKD, heart failure, diabetes-related kidney disease, dialysis, and transplant.

```sql
SELECT DISTINCT
  PATIENT_ID, SERVICE_DATE AS SVC_DT,
  CD.DIAGNOSIS_DESCRIPTION AS Category,
  CASE
    WHEN CATEGORY = 'CHRONIC KIDNEY DISEASE, STAGE 1' THEN 1
    WHEN CATEGORY = 'CHRONIC KIDNEY DISEASE, STAGE 2 (MILD)' THEN 2
    WHEN CATEGORY = 'CHRONIC KIDNEY DISEASE, STAGE 3 (MODERATE)' THEN 3
    WHEN CATEGORY = 'CHRONIC KIDNEY DISEASE, STAGE 4 (SEVERE)' THEN 4
    WHEN CATEGORY LIKE '%STAGE 5%' THEN 5
    ELSE 0
  END AS DX_STAGE,
  NPI_NUMBER,
  COALESCE(PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID) AS PROVIDER_ID,
  PROVIDER_RENDERING_ID, PROVIDER_REFERRING_ID,
  PRIMARY_SPECIALTY_CODE
FROM (
  SELECT C.NPI_NUMBER, A.PATIENT_ID, A.SERVICE_DATE,
         A.PROVIDER_RENDERING_ID, A.PROVIDER_REFERRING_ID,
         A.DIAGNOSIS_CODE, B.PATIENT_BIRTH_YEAR, C.PRIMARY_SPECIALTY_CODE
  FROM (
    SELECT PATIENT_ID, CLAIM_ID, DIAGNOSIS_CODE, SERVICE_DATE,
           PROVIDER_RENDERING_ID, PROVIDER_REFERRING_ID
    FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX
  ) A
  LEFT JOIN (
    SELECT DISTINCT PATIENT_ID, PATIENT_BIRTH_YEAR, PATIENT_GENDER
    FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PTNT_DMGRPHC
  ) B ON A.PATIENT_ID = B.PATIENT_ID
  LEFT JOIN PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRVDR C
    ON COALESCE(A.PROVIDER_REFERRING_ID, A.PROVIDER_RENDERING_ID) = C.PROVIDER_ID
) DX
INNER JOIN (
  SELECT DISTINCT DIAGNOSIS_CODE, DIAGNOSIS_DESCRIPTION
  FROM PHCDW.PHCDW_STG_CAR.STG_IQVIA_LAAD_DIM_DIAGNOSIS
  WHERE DIAGNOSIS_CODE IN (
    -- ICD-9 CKD/Diabetic nephropathy
    '249.4', '249.40', '249.41', '250.4', '250.40', '250.42',
    '285.21',
    -- ICD-9 Hypertensive CKD / Heart+CKD
    '403', '403.0', '403.00', '403.1', '403.10', '403.9', '403.90',
    '404', '404.0', '404.00', '404.01', '404.1', '404.10', '404.11',
    '404.9', '404.90', '404.91',
    -- ICD-9 CKD stages
    '585', '585.1', '585.2', '585.3', '585.4', '585.9', '588.81',
    -- ICD-10 DM with CKD
    'D63.1', 'E08.2', 'E08.21', 'E08.22', 'E08.29',
    'E09.2', 'E09.21', 'E09.22', 'E09.29',
    'E11.2', 'E11.21', 'E11.22', 'E11.29',
    'E13.2', 'E13.21', 'E13.22', 'E13.29',
    -- ICD-10 Hypertensive CKD
    'I12', 'I12.9', 'I13', 'I13.0', 'I13.1', 'I13.10',
    -- ICD-10 CKD stages
    'N18', 'N18.1', 'N18.2', 'N18.3', 'N18.4', 'N18.9', 'N25.81',
    -- Dialysis / Transplant / Other
    '503.60', '503.65', 'S20.65',
    '0TY0.0Z0', '0TY0.0Z1', '0TY0.0Z2',
    '0TY1.0Z0', '0TY1.0Z1', '0TY1.0Z2',
    'Z94.0', 'V42.0',
    -- Additional codes (heart failure, dialysis, fracture, etc.)
    '556.9', '909.18', '909.19', '909.20', '909.21', '909.22',
    '909.23', '909.24', '909.25', '909.35', '909.37', '909.45',
    '909.47', '909.51', '909.52', '909.53', '909.54', '909.55',
    '909.56', '909.57', '909.58', '909.59', '909.60', '909.61',
    '909.62', '909.63', '909.64', '909.65', '909.66', '909.67',
    '909.68', '909.69', '909.70', '909.99',
    '995.12', '995.59',
    'G02.57', 'G03.08', 'G03.09', 'G03.10', 'G03.11', 'G03.12',
    'G03.13', 'G03.14', 'G03.15', 'G03.16', 'G03.17', 'G03.18',
    'G03.19', 'G03.20', 'G03.21', 'G03.22', 'G03.23', 'G03.24',
    'G03.25', 'G03.26', 'G03.27', 'G90.13', 'G90.14',
    'S93.35', 'S93.39',
    '3E1.M39Z', '5A1.D00Z', '5A1.D60Z', '5A1.D70Z',
    '5A1.D80Z', '5A1.D90Z',
    'Z99.2',
    '399.5', '549.8',
    '800', '801', '802', '803', '804', '809', '820', '821',
    '829', '830', '831', '839', '840', '841', '849', '850',
    '851', '859', '880', '881', '889'
  )
) CD
  ON DX.DIAGNOSIS_CODE = CD.DIAGNOSIS_CODE
WHERE (EXTRACT(YEAR FROM SVC_DT) * 100 + EXTRACT(MONTH FROM SVC_DT))
      >= {complete_history_start_month}
  AND (EXTRACT(YEAR FROM SVC_DT) * 100 + EXTRACT(MONTH FROM SVC_DT))
      <= {complete_history_end_month}
  AND PROVIDER_ID IS NOT NULL
```

### CKD Stage Mapping (DX_STAGE column)

| DIAGNOSIS_DESCRIPTION pattern | DX_STAGE |
| --- | --- |
| `CHRONIC KIDNEY DISEASE, STAGE 1` | 1 |
| `CHRONIC KIDNEY DISEASE, STAGE 2 (MILD)` | 2 |
| `CHRONIC KIDNEY DISEASE, STAGE 3 (MODERATE)` | 3 |
| `CHRONIC KIDNEY DISEASE, STAGE 4 (SEVERE)` | 4 |
| Contains `STAGE 5` | 5 |
| All other diagnoses | 0 |

---

## HCP-Level Query: DX_09 — Comorbidity Features

Used for **HCP-level comorbidity claim features**. This query uses a different diagnosis mapping table (`FIN_DIAG_CD` from the sandbox schema) that groups ICD codes into CKD comorbidity groups.

```sql
SELECT DISTINCT
  PATIENT_ID, SVC_DT, DIAGNOSIS_DESCRIPTION, DIAG_GRP,
  PROVIDER_ID, PROVIDER_RENDERING_ID, PROVIDER_REFERRING_ID
FROM (
  SELECT DISTINCT
    PATIENT_ID, SERVICE_DATE AS SVC_DT,
    CD.DIAGNOSIS_DESCRIPTION, DIAG_GRP,
    PROVIDER_RENDERING_ID, PROVIDER_REFERRING_ID,
    PROVIDER_ID
  FROM (
    SELECT PATIENT_ID, DIAGNOSIS_CODE, SERVICE_DATE,
           PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID,
           COALESCE(PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID) AS PROVIDER_ID
    FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX
  ) DX
  INNER JOIN (
    SELECT DISTINCT DIAGNOSIS_CODE, DIAGNOSIS_DESCRIPTION, DIAG_GRP
    FROM PHCDW.PHCDW_SANDBOX.FIN_DIAG_CD
    WHERE DIAG_GRP IN ('KD', 'CV-KD', 'DB-KD')
  ) CD
    ON DX.DIAGNOSIS_CODE = CD.DIAGNOSIS_CODE
  WHERE (EXTRACT(YEAR FROM SVC_DT) * 100 + EXTRACT(MONTH FROM SVC_DT))
        >= {analysis_start_month}
    AND (EXTRACT(YEAR FROM SVC_DT) * 100 + EXTRACT(MONTH FROM SVC_DT))
        <= {current_month}
    AND PROVIDER_ID IS NOT NULL
)
```

### Comorbidity Groups (DIAG_GRP)

| DIAG_GRP | Description |
| --- | --- |
| `KD` | Kidney Disease |
| `CV-KD` | Cardiovascular complications of Kidney Disease |
| `DB-KD` | Diabetes-related Kidney Disease |

---

## Key Differences: DX vs RX Claims

| Aspect | DX Claims | RX Claims |
| --- | --- | --- |
| Fact table | `STG_CAR_IQV_LAAD_FACT_DX` | `STG_CAR_IQV_LAAD_FCT_RX` |
| Date column | `SERVICE_DATE` (aliased `SVC_DT`) | `SVC_DT` |
| Provider ID | `COALESCE(PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID)` | `PROVIDER_ID` (direct) |
| Product/Event key | `DIAGNOSIS_CODE` → `DIAGNOSIS_DESCRIPTION` | `NDC_CD` → `PRODUCT_NAME` / `PRODUCT_GROUP` |
| CKD scoping | Diagnosis description list or ICD code list | `CKD_PRODUCT_MAPPING_VW` join |
| Hospitalization filter | `DATA_SOURCE = 'HX'` | N/A |
| Comorbidity mapping | `FIN_DIAG_CD.DIAG_GRP` | N/A |

---

## Common EDA Query Patterns

Adapt the queries above for these common DX exploration tasks:

### 1. Diagnosis Volume by CKD Stage (Monthly)
```sql
SELECT
  DATE_TRUNC('MONTH', SVC_DT) AS SVC_MONTH,
  DX_STAGE,
  COUNT(*) AS claim_count,
  COUNT(DISTINCT PATIENT_ID) AS unique_patients
FROM <DX_03_query_as_CTE>
GROUP BY 1, 2
ORDER BY 1, 2
```

### 2. Top Diagnosis Descriptions by Frequency
```sql
SELECT
  DIAGNOSIS_DESCRIPTION,
  COUNT(*) AS claim_count,
  COUNT(DISTINCT PATIENT_ID) AS unique_patients
FROM <patient_level_query_as_CTE>
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20
```

### 3. Comorbidity Distribution Across Providers
```sql
SELECT
  DIAG_GRP,
  COUNT(DISTINCT PROVIDER_ID) AS provider_count,
  COUNT(DISTINCT PATIENT_ID) AS patient_count,
  COUNT(*) AS total_claims
FROM <DX_09_query_as_CTE>
GROUP BY 1
```

### 4. Hospitalization vs Non-Hospitalization Claims
```sql
SELECT
  DATA_SOURCE,
  COUNT(*) AS claim_count,
  COUNT(DISTINCT PATIENT_ID) AS unique_patients
FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX
WHERE DATA_SOURCE IN ('HX', 'PB')  -- HX = hospital, PB = professional/outpatient
GROUP BY 1
```

### 5. Provider Specialty vs CKD Stage
```sql
SELECT
  PRIMARY_SPECIALTY_CODE,
  DX_STAGE,
  COUNT(DISTINCT NPI_NUMBER) AS provider_count,
  COUNT(*) AS total_claims
FROM <DX_03_query_as_CTE>
WHERE DX_STAGE > 0
GROUP BY 1, 2
ORDER BY 1, 2
```

---

## Downstream Feature Engineering

The patient-level DX queries feed into the same **cohort-based feature accelerator** as RX claims:

| Concept | Description |
| --- | --- |
| **Anchor Date** | Reference point in time from which patient journey is measured |
| **Lookback Window** | Period before anchor date for computing features (default 12 months for frequency features) |
| **EVENT_TIME** | `DATEDIFF(LOOKBACK_END_DATE, EVENT_DATE)` — days since event from end of lookback |
| **EVENT_NAME** | `DIAGNOSIS_DESCRIPTION` for DX claims |

Feature types generated (same as RX):
* **Frequency** — Count of diagnosis events in past N days
* **Recency** — Days since most recent occurrence of each diagnosis
* **Change in Frequency** — Variation in diagnosis occurrence over time
* **First Occurrence** — When a diagnosis first appeared in the patient's history
* **Skewness** — Concentration of diagnosis events in the patient's journey

---

## Notebook References

**Patient-Level Pipeline:**
- Input data creation: [01_Input_data_creation](/editor/notebooks/2494728515032330) — Cell 23 (12M & First Occ query), Cell 28 (All Events query), Cell 35 (Hospitalization query).
- DX feature engineering: [02_dx_features_rec_&_first_occ](/editor/notebooks/2494728515032399) — Frequency, recency, first-occurrence, skewness features.
- DX Event List: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/feature_selection/Kerendia NBA 3.0 - Dx Event List.csv`

**HCP-Level Pipeline:**
- Query origin: [00_Write_Input_Files](/editor/notebooks/2494728515032387) — Cell 25 (DX_03: CKD Staging), Cell 44 (DX_09: Comorbidity).

**Shared Infrastructure:**
- Config: [00_config](/editor/notebooks/2494728515032290) — Date parameters (`analysis_start_month`, `complete_history_start_month`, `lookback_start`, etc.)
- Data loading: [00_load_processed_data](/editor/notebooks/2494728515032293) — Cohort generation, DataFrame merging.

---

## Execution Notes

> **CRITICAL:** All IQVIA LAAD DX claims queries execute against **Snowflake**, NOT Databricks SQL.
> They **cannot** be run via `spark.sql()` or a Databricks SQL warehouse. They **must** be executed
> using `Get_Data_Snowflakes(query)` after importing the connection notebook.

See [query-template.md](query-template.md) for the full setup boilerplate, all 5 DX query patterns
with ready-to-use code cells, DX-specific SQL patterns, and dialect notes.

### Mandatory Setup

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```

### Query Execution Pattern

```python
query = """
    SELECT ...
    FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX DX_CLAIMS
    ...
"""
df = Get_Data_Snowflakes(query)
```

### Pre-materialized Delta Outputs

Prefer reading Delta when the data is already available:
- **Patient-level (12M & First Occ):** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/dx_input_claims_12M_and_first_occ_features_input`
- **Patient-level (All Events):** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/dx_input_claims_all_events_features_input`
- **Patient-level (Hospitalization):** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/dx_hospitalization_claims_all_events_features_input`
- **HCP-level (DX_03):** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/Dx_03`
- **HCP-level (DX_09):** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/Dx_09`
