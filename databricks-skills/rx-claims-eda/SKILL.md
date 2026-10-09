---
name: rx-claims-eda
description: >
  Guidance for querying and exploring raw IQVIA LAAD RX claims data in the Chronic Kidney Disease (CKD)
  therapeutic area. Read this skill when the user asks to explore RX claims, prescription data, treatment
  categories, drug brands, patient prescriptions, or CKD-related medication queries against the PHCDW
  IQVIA LAAD tables.
---

# RX Claims EDA — IQVIA LAAD Data for CKD Therapeutic Area

This skill provides context and query patterns for exploratory data analysis on the raw IQVIA Longitudinal
Anonymized Analytic Dataset (LAAD) RX claims data, scoped to the Chronic Kidney Disease (CKD) therapeutic
area for the Kerendia (finerenone) franchise.

## Data Model — Star Schema

The IQVIA LAAD RX data follows a **star schema** with one fact table and four dimension tables, plus a
CKD-specific product mapping view.

### Fact Table

| Table | Description |
| --- | --- |
| `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX` | Core RX claims fact table. One row per prescription claim event. |

**Key columns:** `PATIENT_ID`, `PROVIDER_ID`, `SVC_DT` (service date), `DAYS_SUPPLY`, `QUANTITY`, `REFILL_CODE`, `REJECT_CODE`, `NDC_CD` (National Drug Code), `PAYER_PLAN_ID`.

### Dimension Tables

| Table | Join Key | Description |
| --- | --- | --- |
| `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PTNT_DMGRPHC` | `PATIENT_ID` | Patient demographics: `PATIENT_BIRTH_YEAR`, `PATIENT_GENDER`. |
| `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRVDR` | `PROVIDER_ID` | Provider/HCP info: `NPI_NUMBER`, `PRIMARY_SPECIALTY_CODE`, `PRIMARY_SPECIALTY_DESC`. |
| `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRD` | `NDC_CD` | Product/drug info: `PRODUCT_NAME`, `PRODUCT_STRENGTH`. |
| `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PLN` | `PAYER_PLAN_ID` | Payer/plan info: `METHOD_OF_PAYMENT`, `PAYER_NAME`, `PBM_NAME`, `PLAN_NAME`. |

### CKD Product Mapping

| Table | Join Key | Description |
| --- | --- | --- |
| `PHCDW.PHCDW_DSAA.CKD_PRODUCT_MAPPING_VW` | `PRODUCT_NAME` | Maps products to CKD-relevant `TREATMENT_CATEGORY`. This is the **required filter** to scope RX claims to CKD. |

Always JOIN on `CKD_PRODUCT_MAPPING_VW` to restrict the universe to CKD-relevant drugs.
Always filter out `LOWER(Treatment_Category) NOT LIKE 'other'` to exclude non-CKD drugs.

## Treatment Category Mapping

The `TREATMENT_CATEGORY` from the product mapping is re-categorized into consolidated therapeutic groups:

| Raw TREATMENT_CATEGORY values | Mapped Category |
| --- | --- |
| `ACE INHIBITORS, PLAIN`, `ARBs` | `ACE_or_ARB` |
| `CALCIUM CHANNEL BLOCKERS`, `BETA BLOCKING AGENTS` | `Calcium_channel_or_Beta_blocker` |
| `ARBs + Diuretic`, `Diuretic + Blood Pressure`, `ACE inhibitors and diuretics`, `ACE inhibitors and calcium channel blockers`, `ARBS+ Calcium Channel Blocker`, `ARBs + BETA BLOCKING AGENTS + diuretics`, `BETA BLOCKING AGENTS + Diuretic` | `Combo_drug` |
| `Diuretic` | `Diuretic_NON_MRA` |
| `Diuretic + MRA`, `SPIRONOLACTONE-MRA` | `MRA` |
| All others pass through as-is (e.g., `SGLT2`, `Insulin`, `metformin`) | Same as source |

## Brand-Level Drug Classification

Within certain treatment categories, products are further classified to brand level:

### SGLT2 Inhibitors
| Product Pattern | Brand |
| --- | --- |
| `PRODUCT_NAME LIKE '%INVOKANA%'` AND `PRODUCT_STRENGTH = '100 MG'` | `INVOKANA 100MG` |
| `PRODUCT_NAME LIKE '%INVOKANA%'` AND `PRODUCT_STRENGTH = '300 MG'` | `INVOKANA 300MG` |
| `PRODUCT_NAME LIKE '%JARDIANCE%'` | `JARDIANCE` |
| `PRODUCT_NAME LIKE '%FARXIGA%'` | `FARXIGA` |

### MRA
| Product Pattern | Brand |
| --- | --- |
| `PRODUCT_NAME LIKE '%SPIRONOLACTONE%'` | `SPIRONOLACTONE-MRA` |

### DPP-IV Inhibitors
Generic names: `ALOGLIPTIN BENZOATE`, `ALOGLIPTIN-METFORMIN HCL`, `ALOGLIPTIN-PIOGLITAZONE`, `SITAGLIPTIN-METFORMIN HCL`, `SITAGLIPTIN PHOSPHATE`, `LINAGLIPTIN-METFORMIN HCL`, `SAXAGLIPTIN-METFORMIN HCL`, `SAXAGLIPTIN HCL`, `LINAGLIPTIN`, `ALOGLIPTIN`, `ALOGLIPTIN/METFORMIN HCL`, `ALOGLIPTIN/PIOGLITAZONE`.
Brand names: `JANUMET`, `JANUMET XR`, `JANUVIA`, `JENTADUETO`, `JENTADUETO XR`, `KAZANO`, `KOMBIGLYZE XR`, `NESINA`, `ONGLYZA`, `OSENI`, `TRADJENTA`.

### GLP-1 Receptor Agonists
Generic names: `LIXISENATIDE`, `EXENATIDE`, `SEMAGLUTIDE`, `ALBIGLUTIDE`, `DULAGLUTIDE`, `LIRAGLUTIDE`, `INSULIN DEGLUDEC-LIRAGLUTIDE`.
Brand names: `ADLYXIN`, `ADLYXIN STARTER PACK`, `BYDUREON`, `BYDUREON BCISE`, `BYDUREON PEN`, `BYETTA`, `OZEMPIC`, `RYBELSUS`, `TANZEUM`, `TRULICITY`, `VICTOZA`, `XULTOPHY 100/3.6`.

## Derived Columns

| Column | Logic |
| --- | --- |
| `REJECTION_FLAG` | `CASE WHEN REJECT_CODE IS NULL THEN 0 ELSE 1 END` |
| `REFILL_FLAG` | `CASE WHEN REFILL_CODE = 0 THEN 'NEW_PRESCRIPTION' ELSE 'REFILL' END` |
| `DAYS_SUPPLY` | Use `MAX(DAYS_SUPPLY)` when grouping |

## Two Levels of RX Claims Queries

The IQVIA LAAD RX data is queried at **two levels** depending on the analytical objective:

| Level | Purpose | Key Granularity | Source Notebook |
| --- | --- | --- | --- |
| **HCP-Level** | Monthly treatment category/brand aggregation per provider | `NPI_NUMBER` + `SVC_DT_M` (service month) | `00_Write_Input_Files` Cell 6 |
| **Patient-Level (12M Features)** | Claim-level detail for a rolling 12-month lookback window per patient | `PATIENT_ID` + `PROVIDER_ID` + `SVC_DT` | `01_Input_data_creation` Cell 9 |
| **Patient-Level (Total Events & First Occurrence)** | Full claim history per patient for first-occurrence and total-event features | `PATIENT_ID` + `PROVIDER_ID` + `SVC_DT` | `01_Input_data_creation` Cell 16 |

---

## HCP-Level Canonical Query

Used for **HCP-level feature engineering** (monthly aggregation of treatment categories, brand share, rejection rates per provider). This query joins all 5 tables plus the CKD product mapping.

```sql
SELECT
  C.NPI_NUMBER,
  A.PROVIDER_ID,
  C.PRIMARY_SPECIALTY_CODE,
  A.PATIENT_ID,
  A.SVC_DT,
  D.PRODUCT_NAME,
  D.PRODUCT_STRENGTH,
  -- Apply treatment category mapping (see Treatment Category Mapping section)
  CASE
    WHEN MAP.TREATMENT_CATEGORY IN ('ACE INHIBITORS, PLAIN','ARBs') THEN 'ACE_or_ARB'
    WHEN MAP.TREATMENT_CATEGORY IN ('CALCIUM CHANNEL BLOCKERS','BETA BLOCKING AGENTS') THEN 'Calcium_channel_or_Beta_blocker'
    WHEN MAP.TREATMENT_CATEGORY IN ('ARBs + Diuretic','Diuretic + Blood Pressure',
         'ACE inhibitors and diuretics','ACE inhibitors and calcium channel blockers',
         'ARBS+ Calcium Channel Blocker','ARBs + BETA BLOCKING AGENTS + diuretics',
         'BETA BLOCKING AGENTS + Diuretic') THEN 'Combo_drug'
    WHEN MAP.TREATMENT_CATEGORY IN ('Diuretic') THEN 'Diuretic_NON_MRA'
    WHEN MAP.TREATMENT_CATEGORY IN ('Diuretic + MRA','SPIRONOLACTONE-MRA') THEN 'MRA'
    ELSE MAP.TREATMENT_CATEGORY
  END AS TREATMENT_CATEGORY,
  MAX(A.DAYS_SUPPLY) AS DAYS_SUPPLY,
  -- Apply brand classification (see Brand-Level Drug Classification section)
  CASE
    WHEN D.PRODUCT_NAME LIKE '%INVOKANA%' AND D.PRODUCT_STRENGTH = '100 MG' THEN 'INVOKANA 100MG'
    WHEN D.PRODUCT_NAME LIKE '%INVOKANA%' AND D.PRODUCT_STRENGTH = '300 MG' THEN 'INVOKANA 300MG'
    WHEN D.PRODUCT_NAME LIKE '%JARDIANCE%' THEN 'JARDIANCE'
    WHEN D.PRODUCT_NAME LIKE '%FARXIGA%' THEN 'FARXIGA'
    WHEN D.PRODUCT_NAME LIKE '%SPIRONOLACTONE%' THEN 'SPIRONOLACTONE-MRA'
    -- DPP-IV list (see section above)
    WHEN D.PRODUCT_NAME IN ('ALOGLIPTIN BENZOATE','SITAGLIPTIN PHOSPHATE','LINAGLIPTIN',
         'SAXAGLIPTIN HCL','JANUMET','JANUVIA','TRADJENTA','ONGLYZA' /* ...full list */ ) THEN 'DPP-IV'
    -- GLP-1 list (see section above)
    WHEN D.PRODUCT_NAME IN ('SEMAGLUTIDE','DULAGLUTIDE','LIRAGLUTIDE',
         'OZEMPIC','RYBELSUS','TRULICITY','VICTOZA' /* ...full list */ ) THEN 'GLP-1'
    ELSE MAP.TREATMENT_CATEGORY
  END AS CATEGORY,
  CASE WHEN A.REJECT_CODE IS NULL THEN 0 ELSE 1 END AS REJECTION_FLAG,
  E.METHOD_OF_PAYMENT,
  B.PATIENT_BIRTH_YEAR,
  B.PATIENT_GENDER,
  CASE WHEN A.REFILL_CODE = 0 THEN 'NEW_PRESCRIPTION' ELSE 'REFILL' END AS REFILL_FLAG
FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX A
LEFT JOIN (
  SELECT DISTINCT PATIENT_ID, PATIENT_BIRTH_YEAR, PATIENT_GENDER
  FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PTNT_DMGRPHC
) B ON A.PATIENT_ID = B.PATIENT_ID
LEFT JOIN PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRVDR C
  ON A.PROVIDER_ID = C.PROVIDER_ID
LEFT JOIN PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRD D
  ON A.NDC_CD = D.NDC_CD
LEFT JOIN PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PLN E
  ON A.PAYER_PLAN_ID = E.PAYER_PLAN_ID
JOIN PHCDW.PHCDW_DSAA.CKD_PRODUCT_MAPPING_VW MAP
  ON D.PRODUCT_NAME = MAP.PRODUCT_NAME
WHERE (EXTRACT(YEAR FROM A.SVC_DT) * 100 + EXTRACT(MONTH FROM A.SVC_DT)) >= 201901
  AND A.PROVIDER_ID IS NOT NULL
  AND LOWER(MAP.TREATMENT_CATEGORY) NOT LIKE 'other'
GROUP BY
  C.NPI_NUMBER, A.PROVIDER_ID, C.PRIMARY_SPECIALTY_CODE, A.PATIENT_ID,
  A.SVC_DT, D.PRODUCT_NAME, D.PRODUCT_STRENGTH, MAP.TREATMENT_CATEGORY,
  REJECTION_FLAG, E.METHOD_OF_PAYMENT, B.PATIENT_BIRTH_YEAR,
  B.PATIENT_GENDER, REFILL_FLAG
ORDER BY A.PATIENT_ID, A.SVC_DT
```

---

## Patient-Level Query: 12-Month Based Features

Used for **patient-level feature engineering** with a rolling 12-month lookback window. This query is simpler — it joins only the fact table with the product dimension, filters to `CLAIM_TYPE = 'PD'` (paid claims), and restricts to a curated list of 29 CKD-relevant `PRODUCT_GROUP` values selected for the final NBA model.

**Key differences from HCP-level query:**
* Uses `PRODUCT_GROUP` from `DIM_PRD` instead of `TREATMENT_CATEGORY` from `CKD_PRODUCT_MAPPING_VW`
* Filters to `CLAIM_TYPE = 'PD'` (paid claims only)
* Includes additional claim-detail columns: `CLAIM_ID`, `SOB`, `CLAIM_TYPE`, `DAW_CODE`, `ZIP_CODE`, `CHANNEL_CODE`, `CLAIM_STATUS`, `COPAY_CARD_FLG`
* Bounded by a 12-month `lookback_start` to `lookback_end` date window
* No aggregation — returns distinct claim-level rows

```sql
SELECT DISTINCT
  A.CLAIM_ID, A.PROVIDER_ID, A.PATIENT_ID, A.SVC_DT,
  A.DAYS_SUPPLY, A.NDC_CD,
  C.PRODUCT_GROUP, C.PRODUCT_STRENGTH, C.GENERIC_NAME,
  A.REFILL_CODE, A.REJECT_CODE, A.PAYER_PLAN_ID,
  A.SOB, A.CLAIM_TYPE, A.DAW_CODE, A.ZIP_CODE,
  A.CHANNEL_CODE, A.CLAIM_STATUS, A.COPAY_CARD_FLG
FROM (
  SELECT CLAIM_ID, PATIENT_ID, SVC_DT, DAYS_SUPPLY, QUANTITY,
         REFILL_CODE, REJECT_CODE, PROVIDER_ID, NDC_CD,
         PAYER_PLAN_ID, SOB, CLAIM_TYPE, DAW_CODE, ZIP_CODE,
         CHANNEL_CODE, CLAIM_STATUS, COPAY_CARD_FLG
  FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX
  WHERE CLAIM_TYPE = 'PD'
) A
INNER JOIN PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRD C
  ON A.NDC_CD = C.NDC_CD
WHERE A.PROVIDER_ID IS NOT NULL
  AND C.PRODUCT_GROUP IN (
    'CALCITRIOL', 'CALCIUM ACE', 'DILT-XR', 'EDARBI', 'EDARBYCLOR',
    'FUROSEMIDE', 'GLIPIZIDE', 'IRBESARTAN', 'KERENDIA', 'LABETALOL HCL',
    'METOLAZONE', 'METOPROLOL TART', 'NADOLOL', 'NIFEDIPINE ER',
    'PROPRANOLOL HCL', 'TELMISARTAN', 'AMLODIP BES/OLMESAR',
    'AMLODIP BES/VALSAR', 'DILTIAZEM HCL', 'DILTIAZEM SR', 'ENTRESTO',
    'FARXIGA', 'LOSARTAN POT', 'SEVELAMER CARB', 'SYNJARDY',
    'BENAZEPRIL HCL', 'HYDROCHLOROTHIAZIDE', 'LISINOPRIL/HCTZ', 'RYBELSUS'
  )
  AND A.SVC_DT >= '{lookback_start}'
  AND A.SVC_DT <= '{lookback_end}'
```

**Product Groups (29 CKD-relevant drugs):** `CALCITRIOL`, `CALCIUM ACE`, `DILT-XR`, `EDARBI`, `EDARBYCLOR`, `FUROSEMIDE`, `GLIPIZIDE`, `IRBESARTAN`, `KERENDIA`, `LABETALOL HCL`, `METOLAZONE`, `METOPROLOL TART`, `NADOLOL`, `NIFEDIPINE ER`, `PROPRANOLOL HCL`, `TELMISARTAN`, `AMLODIP BES/OLMESAR`, `AMLODIP BES/VALSAR`, `DILTIAZEM HCL`, `DILTIAZEM SR`, `ENTRESTO`, `FARXIGA`, `LOSARTAN POT`, `SEVELAMER CARB`, `SYNJARDY`, `BENAZEPRIL HCL`, `HYDROCHLOROTHIAZIDE`, `LISINOPRIL/HCTZ`, `RYBELSUS`.

---

## Patient-Level Query: Total Events & First Occurrence Features

Used for **first-occurrence and total-event patient-level features**. This query is identical in structure to the 12-month query but with two critical differences:

1. **No date lower bound** — retrieves the patient's full claim history up to `lookback_end` (needed to determine when an event *first* occurred).
2. **No `PRODUCT_GROUP` filter in SQL** — the full product universe is pulled, then post-filtered in PySpark against a dynamic `rx_event_list` CSV of prevalent events.

```sql
SELECT DISTINCT
  A.CLAIM_ID, A.PROVIDER_ID, A.PATIENT_ID, A.SVC_DT,
  A.DAYS_SUPPLY, A.NDC_CD,
  C.PRODUCT_GROUP, C.PRODUCT_STRENGTH, C.GENERIC_NAME,
  A.REFILL_CODE, A.REJECT_CODE, A.PAYER_PLAN_ID,
  A.SOB, A.CLAIM_TYPE, A.DAW_CODE, A.ZIP_CODE,
  A.CHANNEL_CODE, A.CLAIM_STATUS, A.COPAY_CARD_FLG
FROM (
  SELECT CLAIM_ID, PATIENT_ID, SVC_DT, DAYS_SUPPLY, QUANTITY,
         REFILL_CODE, REJECT_CODE, PROVIDER_ID, NDC_CD,
         PAYER_PLAN_ID, SOB, CLAIM_TYPE, DAW_CODE, ZIP_CODE,
         CHANNEL_CODE, CLAIM_STATUS, COPAY_CARD_FLG
  FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX
  WHERE CLAIM_TYPE = 'PD'
) A
INNER JOIN PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRD C
  ON A.NDC_CD = C.NDC_CD
WHERE A.PROVIDER_ID IS NOT NULL
  AND A.SVC_DT <= '{lookback_end}'
```

**Post-query PySpark filtering:**
```python
# Filter to prevalent events from external CSV
rx_event_list = pd.read_csv("/Volumes/.../feature_selection/Kerendia NBA 3.0 - Rx Event List.csv")
rx_claims_filtered = rx_claims_filtered.filter(
    col("PRODUCT_GROUP").isin(rx_event_list["EVENT_NAME"].tolist())
)
```

### Downstream Feature Engineering

The patient-level queries feed into a **cohort-based feature accelerator** with these concepts:

| Concept | Description |
| --- | --- |
| **Anchor Date** | Reference point in time from which patient journey is measured |
| **Lookback Window** | Period before anchor date for computing features (default 12 months for frequency features) |
| **Prediction Window** | Period after anchor date for computing target labels |
| **EVENT_TIME** | `DATEDIFF(LOOKBACK_END_DATE, EVENT_DATE)` — days since event from end of lookback |

Feature types generated:
* **Frequency** — Count of events in past N days
* **Recency** — Days since most recent occurrence of each event
* **Change in Frequency** — Variation in event occurrence over time
* **First Occurrence** — When an event first appeared in the patient's history
* **Skewness** — Concentration of events in the patient's journey

---

## Common EDA Query Patterns

Adapt the HCP-level or patient-level queries above for these common exploration tasks:

### 1. Claims Volume by Treatment Category (Monthly)
```sql
SELECT
  DATE_TRUNC('MONTH', SVC_DT) AS SVC_MONTH,
  TREATMENT_CATEGORY,
  COUNT(*) AS claim_count,
  COUNT(DISTINCT PATIENT_ID) AS unique_patients
FROM <base_query_as_CTE>
GROUP BY 1, 2
ORDER BY 1, 2
```

### 2. New vs Refill Prescriptions
```sql
SELECT
  REFILL_FLAG,
  TREATMENT_CATEGORY,
  COUNT(*) AS claim_count
FROM <base_query_as_CTE>
GROUP BY 1, 2
```

### 3. SGLT2 Brand Share
```sql
SELECT
  CATEGORY,
  COUNT(*) AS claim_count,
  COUNT(DISTINCT PATIENT_ID) AS unique_patients
FROM <base_query_as_CTE>
WHERE TREATMENT_CATEGORY = 'SGLT2'
GROUP BY 1
```

### 4. Provider Specialty Distribution
```sql
SELECT
  PRIMARY_SPECIALTY_CODE,
  COUNT(DISTINCT NPI_NUMBER) AS provider_count,
  COUNT(*) AS total_claims
FROM <base_query_as_CTE>
GROUP BY 1
ORDER BY 2 DESC
```

### 5. Rejection Rate Analysis
```sql
SELECT
  TREATMENT_CATEGORY,
  SUM(REJECTION_FLAG) AS rejected_claims,
  COUNT(*) AS total_claims,
  ROUND(SUM(REJECTION_FLAG) * 100.0 / COUNT(*), 2) AS rejection_pct
FROM <base_query_as_CTE>
GROUP BY 1
ORDER BY 4 DESC
```

### 6. Patient Demographics by Treatment
```sql
SELECT
  TREATMENT_CATEGORY,
  PATIENT_GENDER,
  COUNT(DISTINCT PATIENT_ID) AS unique_patients
FROM <base_query_as_CTE>
GROUP BY 1, 2
```

## Related Data Sources

For broader CKD EDA beyond RX claims, these companion tables may be useful:

| Table / View | Purpose |
| --- | --- |
| `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_QUEST_TO_LAAD_HIST` | Lab test results (GFR/UACR) from Quest/LabCorp for CKD staging |
| `PHCDW.PHCDW_DSAA.KERENDIA_LAB_QUEST_LABCORP_VIEW` | Curated lab view for Kerendia CKD analysis |
| `PHCDW.PHCDW_STG_CAR.STG_IQVIA_LAAD_DIM_PROVIDER` | Extended provider dimension (alternate alias for provider lookups) |
| `PHCDW.PHCDW_STG_CAR.STG_IQVIA_LAAD_DIM_PRODUCT` | Extended product dimension |
| `PHCDW.PHCDW_STG_CAR.STG_IQVIA_LAAD_DIM_PLAN` | Extended plan dimension |

## CKD Staging Reference (for Lab Context)

### GFR Stages
| GFR Value | CKD Stage |
| --- | --- |
| < 15 | Stage 5 |
| 15–29 | Stage 4 (Severe) |
| 30–59 | Stage 3 (Moderate) |
| 60–89 | Stage 2 (Mild) |
| 90–150 | Stage 1 |

### UACR Stages
| UACR Value | Stage |
| --- | --- |
| < 30 | A1 (Normal) |
| 30–299 | A2 (Moderately increased) |
| >= 300 | A3 (Severely increased) |

## Key Filters and Defaults

- **Time filter:** `(EXTRACT(YEAR FROM SVC_DT) * 100 + EXTRACT(MONTH FROM SVC_DT)) >= {analysis_start_month}` — default `201901`.
- **Provider filter:** `PROVIDER_ID IS NOT NULL`.
- **Product filter:** Always INNER JOIN on `CKD_PRODUCT_MAPPING_VW` and exclude `LOWER(Treatment_Category) NOT LIKE 'other'`.
- **Kerendia launch context:** Kerendia (finerenone) launched **July 2021**. Feature engineering typically retains data from April 2021 onward.

## Notebook References

**HCP-Level Pipeline:**
- Query origin: [00_Write_Input_Files](/editor/notebooks/2494728515032387) — Cell 6 contains the HCP-level canonical RX query.
- RX feature engineering: [01_claim_rx_monthly](/editor/notebooks/2494728515032380) — Monthly aggregation of RX claims per HCP.
- Lab feature engineering: [02_claim_lab_monthly](/editor/notebooks/2494728515032388) — Lab test (GFR/UACR) features.

**Patient-Level Pipeline:**
- Input data creation: [01_Input_data_creation](/editor/notebooks/2494728515032330) — Cell 9 (12M features query), Cell 16 (Total Events & First Occurrence query).
- RX feature engineering: [01_rx_features_rec_&_first_occ](/editor/notebooks/2494728515032398) — Frequency, recency, first-occurrence, skewness features.
- Data loading & processing: [00_load_processed_data](/editor/notebooks/2494728515032293) — Cohort date generation, DataFrame merging, event-time computation.
- RX Event List: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/feature_selection/Kerendia NBA 3.0 - Rx Event List.csv`

## Execution Notes

> **CRITICAL:** All IQVIA LAAD RX claims queries execute against **Snowflake**, NOT Databricks SQL.
> They **cannot** be run via `spark.sql()` or a Databricks SQL warehouse. They **must** be executed
> using `Get_Data_Snowflakes(query)` after importing the connection notebook.

See [query-template.md](query-template.md) for the full setup boilerplate, function signature, and
SQL dialect notes.

### Mandatory Setup

Every notebook or Python file that queries these tables must start with:

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```

This provides the `Get_Data_Snowflakes(query)` function, Snowflake authentication (via Databricks
secrets scope `US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`), and common library imports.

### Query Execution Pattern

```python
query = """
    SELECT ...
    FROM PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX A
    ...
"""
df = Get_Data_Snowflakes(query)
```

### When to skip Snowflake and read Delta directly

If the data has already been materialized, prefer reading the Delta output to avoid re-querying Snowflake:
- Pre-materialized Delta outputs:
  - **HCP-level:** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/Rx_01_new`
  - **Patient-level (12M):** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/rx_input_claims_12M_features_input`
  - **Patient-level (Total Events & First Occ):** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/rx_input_claims_total_events_and_first_occ_features_input`
- When reading the HCP-level Delta output, clean trailing whitespace from `TREATMENT_CATEGORY`: `.withColumn('TREATMENT_CATEGORY', F.regexp_replace('TREATMENT_CATEGORY', r'[\s]*$', ''))`.
