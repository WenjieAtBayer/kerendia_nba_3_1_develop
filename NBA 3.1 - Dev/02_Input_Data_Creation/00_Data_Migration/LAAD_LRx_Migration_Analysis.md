# LAAD-Based LRx Table Migration Analysis

**Date:** October 2026  
**Source Pipeline:** `/Workspace/Users/wenjie.chen@bayer.com/kerendia_data_needs/LAAD based LRx Pipeline/Ops Pipeline`  
**Target:** Migrate from Snowflake sources to Unity Catalog (PACE) in-house tables  
**Status:** Analysis Phase

---

## 1. Pipeline Overview

The LAAD-based LRx pipeline produces `KERENDIA_LAAD_BASED_LRX_V6` — a weekly-refreshed HCP-level claims table with **30 columns** and ~1.95B rows. It currently reads from **11 Snowflake sources** and writes to both Snowflake and a UC Delta table.

> **Migration Scope:** The raw IQVIA claims tables (`STG_CAR_IQV_LAAD_FCT_RX` and `STG_CAR_IQV_LAAD_FACT_DX`) are foundational IQVIA LAAD data that provide REFILL_CODE, SOB, Dx codes, and all raw claim fields, and will continue to be used as-is. The migration covers **9 of 11 Snowflake sources**: the Galaxy-derived tables (#6–9), dimension tables (#3–5), HCP profile (#10), and the output target (#11).

### 1.1 Pipeline Execution Flow

```
00_params ─────────────────┐
00_connection ─────────────┤
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ Helper Notebooks (run in parallel, before master chain)      │
│                                                              │
│  2.1 Indication Group & Hyt. Flag                            │
│      Snowflake: STG_CAR_IQV_LAAD_FCT_RX (Rx claims)         │
│                 STG_CAR_IQV_LAAD_FACT_DX (Dx claims)         │
│      → Patient-level earliest indication dates               │
│        (T2D, CKD, CVD, HF, HT)                              │
│                                                              │
│  2.2 Switch From, Add-on To                                  │
│      Snowflake: STG_CAR_IQV_LAAD_FCT_RX (Rx claims)         │
│      → Claim-level SWITCH_FROM & ADD_ON_TO labels            │
│        (lookback=60d, grace=14d, overlap=-7d)                │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ Master Notebooks (sequential chain)                          │
│                                                              │
│  1.1 Data Preprocessing                                      │
│      Snowflake: STG_CAR_IQV_LAAD_FCT_RX                     │
│      + Product Mapping Excel (NDC → Product Group)           │
│      → Filtered paid Rx claims for last 1 year               │
│                                                              │
│  3.1 NBRx Calculation                                        │
│      → NBRX_FLAG (first claim or >365d gap per patient×prod) │
│      → NRX_FLAG (REFILL_CODE=0 or NBRX=1)                   │
│      → Filter to last 13 weeks                               │
│                                                              │
│  3.2 Patient Attributes & Plan Info                          │
│      Snowflake: STG_CAR_IQV_LAAD_DIM_PTNT_DMGRPHC           │
│                 STG_CAR_IQV_LAAD_DIM_PLN                     │
│      → Add GENDER, AGE_GROUP, PAY_TYPE                       │
│                                                              │
│  3.3 Switch From & Indication Group                          │
│      → Join indication dates (from 2.1)                      │
│      → Create INDICATION_GROUP (T2D+CKD+CVD+HF concat)      │
│      → Create HYPERTENSION_FLAG                              │
│      → Join switch/add-on (from 2.2)                         │
│                                                              │
│  3.4 HCP Level Claims                                        │
│      → Add WEEK_ENDING_DATE, PERIOD_ID, PERIOD_TYPE          │
│      → GROUP BY 14 dimensions → SUM(NBRX), SUM(NRX),        │
│        COUNT_DISTINCT(CLAIM_ID) as TRX                       │
│                                                              │
│  3.5 HCP Attributes                                          │
│      Snowflake: STG_CAR_IQV_LAAD_DIM_PRVDR                  │
│                 Galaxy: MAP_CUSTOMER_XREF                     │
│                         DIM_CUSTOMER_HCP                      │
│                         FACT_IQV_LAAD_SUB_NATIONAL            │
│                         FACT_IQV_LAAD_SUB_NATIONAL_XREF       │
│                 MDM_STG_HCP_PRFL                              │
│                 Specialty Mapping CSV                         │
│      → Add NPI, BH_ID, name, address, specialty              │
│                                                              │
│  3.6 Save to Snowflake                                       │
│      → Backup existing V6                                    │
│      → Remove overlapping weeks from original                │
│      → Append new 13 weeks                                   │
│      → Write to Snowflake + UC Delta                         │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Output Schema: KERENDIA_LAAD_BASED_LRX_V6 (30 columns)

| # | Column | Type | Source Step | Category |
|---|--------|------|-------------|----------|
| 1 | `WEEK_ENDING_DATE` | STRING | 3.4 | Time |
| 2 | `PROVIDER_ID` | STRING | 1.1 | HCP ID |
| 3 | `PERIOD_ID` | DATE | 3.4 | Time |
| 4 | `PERIOD_TYPE` | STRING | 3.4 | Time |
| 5 | `SPECIALTY_GROUP` | STRING | 3.5 | HCP Attribute |
| 6 | `PRODUCT_GROUP` | STRING | 1.1 | Rx |
| 7 | `SWITCH_FROM` | STRING | 2.2 → 3.3 | Transition |
| 8 | `ADD_ON_TO` | STRING | 2.2 → 3.3 | Transition |
| 9 | `AGE_GROUP` | STRING | 3.2 | Patient |
| 10 | `GENDER` | STRING | 3.2 | Patient |
| 11 | `PAY_TYPE` | STRING | 3.2 | Payer |
| 12 | `SOURCE_OF_BUSINESS` | STRING | 1.1 | Rx |
| 13 | `RX_CHANNEL` | STRING | 1.1 | Rx |
| 14 | `INDICATION_GROUP` | STRING | 2.1 → 3.3 | Indication |
| 15 | `HYPERTENSION_FLAG` | STRING | 2.1 → 3.3 | Indication |
| 16 | `PAYER_PLAN_ID` | STRING | 1.1 | Payer |
| 17 | `NBRX` | DECIMAL | 3.1 | Metric |
| 18 | `TRX` | DECIMAL | 3.4 | Metric |
| 19 | `NRX` | DECIMAL | 3.1 | Metric |
| 20 | `NPI` | STRING | 3.5 | HCP ID |
| 21 | `FIRST_NAME` | STRING | 3.5 | HCP Attribute |
| 22 | `MIDDLE_NAME` | STRING | 3.5 | HCP Attribute |
| 23 | `LAST_NAME` | STRING | 3.5 | HCP Attribute |
| 24 | `ADDRESS_LINE_1` | STRING | 3.5 | HCP Attribute |
| 25 | `CITY` | STRING | 3.5 | HCP Attribute |
| 26 | `STATE` | STRING | 3.5 | HCP Attribute |
| 27 | `ZIP` | STRING | 3.5 | HCP Attribute |
| 28 | `PRI_SPCL_DESC` | STRING | 3.5 | HCP Attribute |
| 29 | `BH_ID_VIA_NPI` | STRING | 3.5 | HCP ID |
| 30 | `REFRESH_DATE` | DATE | 3.6 | Metadata |

---

## 3. Snowflake Source → UC Replacement Mapping

### 3.1 Complete Source Inventory

| # | Snowflake Source | Pipeline Step | Columns Used | UC Replacement | Status |
|---|-----------------|---------------|-------------|----------------|--------|
| 1 | `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX` | 1.1, 2.1, 2.2 | CLAIM_ID, PATIENT_ID, SVC_DT, PROVIDER_ID, PAYER_PLAN_ID, NDC_CD, PRODUCT_GROUP, DAYS_SUPPLY, REFILL_CODE, SOB, RX_CHANNEL, CLAIM_TYPE | **No change — continue using raw IQVIA Rx claims as-is** | **NO CHANGE** |
| 2 | `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX` | 2.1 | PATIENT_ID, SERVICE_DATE, DIAGNOSIS_CODE | **No change — continue using raw IQVIA Dx claims as-is** | **NO CHANGE** |
| 3 | `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PTNT_DMGRPHC` | 3.2 | PATIENT_ID, PATIENT_GENDER, PATIENT_BIRTH_YEAR | `pt_lvl_trx` already has AGE, AGE_GROUP, GENDER | **ELIMINATED** |
| 4 | `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PLN` | 3.2 | PAYER_PLAN_ID, METHOD_OF_PAYMENT | `pt_lvl_trx` already has PAY_TYPE | **ELIMINATED** |
| 5 | `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRVDR` | 3.5 | PROVIDER_ID, FIRST_NAME, LAST_NAME, ADDRESS, CITY, STATE_CODE, ZIP_CODE, PRIMARY_SPECIALTY_DESC | `pace_ker_in_house_schema.pha_hcp_demographics_np_pa_aligned_mar2026` + `kerendia_nba_3.stg_car_iqv_laad_dim_prvdr` | **AVAILABLE** |
| 6 | `CPH_DB_PROD.MODEL_V2.FACT_IQV_LAAD_SUB_NATIONAL` | 3.5 | PRVDR_ID (WHERE PROJD_NBRX > 0) | `pace_ker_in_house_schema.lrx_nbrx` | **AVAILABLE** |
| 7 | `CPH_DB_PROD.MODEL_V2.FACT_IQV_LAAD_SUB_NATIONAL_XREF` | 3.5 | PRVDR_ID, NPI | `pace_ker_in_house_schema.pha_hcp_demographics_np_pa_aligned_mar2026` (PROVIDER_ID → HCP_NPI_ID) | **AVAILABLE** |
| 8 | `CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF` | 3.5 | SOURCE_CUST_ID → BAYER_CUST_ID (BH_ID) | `pace_ker_in_house_schema.pha_hcp_demographics_np_pa_aligned_mar2026` (PROVIDER_ID → BH_ID) | **AVAILABLE** |
| 9 | `CPH_DB_PROD.MODEL_V2.DIM_CUSTOMER_HCP` | 3.5 | NPI_NUM → BAYER_CUST_ID (BH_ID fallback) | `pace_ker_in_house_schema.mdm_stg_hcp_prfl` (NPI_NUM → BH_ID) | **AVAILABLE** |
| 10 | `PHCDW.PHCDW_STG.MDM_STG_HCP_PRFL` | 3.5 | BH_ID, FIRST_NAME, MIDDLE_NAME, LAST_NAME | `pace_ker_in_house_schema.mdm_stg_hcp_prfl` | **AVAILABLE** |
| 11 | `PHCDW.PHCDW_DSAA.KERENDIA_LAAD_BASED_LRX_V6` | 3.6 | Full table (read for append) | `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v6` | **AVAILABLE** |

### 3.2 External Files Used

| File | Purpose | UC Replacement | Status |
|------|---------|----------------|--------|
| `Kerendia_Market_Basket_Product_Group_Mapping_and_Priority_v3.xlsx` | NDC → Product Group mapping | `pt_lvl_trx` already has PRODUCT_GROUP + PRODUCT_CLASS; also `pha_lrx_transition_product_mapping` (NDC_CD → PROD_CUSTOM_LVL4_DESC, CLASSIFICATION) | **ELIMINATED** |
| `LRX_LAAD_Specialty_Mapping.csv` | PRI_SPCL_DESC → SPECIALTY_GROUP | `pt_lvl_trx` already has SPECIALTY_GROUP; also `default.lrx_laad_specialty_mapping` | **ELIMINATED** |

---

## 4. Column-by-Column Migration Feasibility

### 4.1 Columns Fully Available in UC (22 of 30)

| V6 Column | UC Source | UC Column(s) | Notes |
|-----------|-----------|-------------|-------|
| `PROVIDER_ID` | pt_lvl_trx / lrx_nbrx | PROVIDER_ID | Direct match |
| `WEEK_ENDING_DATE` | pt_lvl_trx / lrx_nbrx | WEEK_ENDING_DATE | Direct match |
| `PERIOD_ID` | pt_lvl_nbrx / lrx_nbrx | PERIOD_ID | Direct match |
| `PERIOD_TYPE` | pt_lvl_nbrx / lrx_nbrx | PERIOD_TYPE | Direct match |
| `SPECIALTY_GROUP` | pt_lvl_trx / lrx_nbrx | SPECIALTY_GROUP | Direct — eliminates 4-table join chain |
| `PRODUCT_GROUP` | pt_lvl_trx / lrx_nbrx | PRODUCT_GROUP | Direct — eliminates Excel mapping |
| `AGE_GROUP` | pt_lvl_trx / lrx_nbrx | AGE_GROUP | Direct — eliminates DIM_PTNT join |
| `GENDER` | pt_lvl_trx / lrx_nbrx | GENDER | Direct — eliminates DIM_PTNT join |
| `PAY_TYPE` | pt_lvl_trx / lrx_nbrx | PAY_TYPE | Direct — eliminates DIM_PLN join |
| `RX_CHANNEL` | pt_lvl_trx / lrx_nbrx | RX_CHANNEL | Direct match |
| `PAYER_PLAN_ID` | pt_lvl_trx / lrx_nbrx | PAYER_PLAN_ID | Direct match |
| `NBRX` | pt_lvl_nbrx / lrx_nbrx | Count of NBRx claims / NBRX | Pre-computed NBRx available |
| `TRX` | pt_lvl_trx | COUNT(DISTINCT CLAIM_ID) | Derivable from claim-level TRx |
| `NPI` | pha_hcp_demographics | HCP_NPI_ID | Direct match |
| `FIRST_NAME` | pha_hcp_demographics | HCP_FIRST_NAME | Direct match |
| `LAST_NAME` | pha_hcp_demographics | HCP_LAST_NAME | Direct match |
| `MIDDLE_NAME` | mdm_stg_hcp_prfl | MIDDLE_NAME (via BH_ID join) | Same table as Snowflake |
| `ADDRESS_LINE_1` | pha_hcp_demographics | HCP_ADDR_1 | Direct match |
| `CITY` | pha_hcp_demographics | HCP_ADDR_CITY | Direct match |
| `STATE` | pha_hcp_demographics | STATE_CODE | Direct match |
| `ZIP` | pha_hcp_demographics | ZIP | Direct match |
| `BH_ID_VIA_NPI` | pha_hcp_demographics | BH_ID | Simplified — single table replaces 4-table cascade |
| `PRI_SPCL_DESC` | pha_hcp_demographics / stg_car_iqv_laad_dim_prvdr (kerendia_nba_3) | MDM_SPECIALTY / PRIMARY_SPECIALTY_DESC | Available from both sources |
| `REFRESH_DATE` | — | Derived at pipeline runtime | Metadata column |

### 4.2 Columns Not in PACE UC Tables — No Gap (Sourced from Raw IQVIA Claims)

The following 6 columns are not available in any PACE UC table. However, they are **not migration gaps** because the raw IQVIA claims tables (`STG_CAR_IQV_LAAD_FCT_RX` and `STG_CAR_IQV_LAAD_FACT_DX`) are outside the migration scope and continue to be used as-is. These are foundational IQVIA LAAD data — all existing business logic that reads from them remains unchanged.

| # | V6 Column | Not in PACE UC Because | Source (Unchanged) | Pipeline Step |
|---|-----------|------------------------|--------------------|--------------|
| 1 | **`REFILL_CODE`** → `NRX` | Raw claim-level field; PACE tables are pre-aggregated | `STG_CAR_IQV_LAAD_FCT_RX` | 3.1 (NRX = REFILL_CODE=0 or NBRX=1) |
| 2 | **`SOURCE_OF_BUSINESS`** (SOB) | Raw claim-level field; PACE tables don't carry SOB | `STG_CAR_IQV_LAAD_FCT_RX` | 1.1 |
| 3 | **`SWITCH_FROM`** | Derived via lookback window logic on claim history | `STG_CAR_IQV_LAAD_FCT_RX` | 2.2 (Helper) |
| 4 | **`ADD_ON_TO`** | Derived alongside SWITCH_FROM | `STG_CAR_IQV_LAAD_FCT_RX` | 2.2 (Helper) |
| 5 | **`HYPERTENSION_FLAG`** | HT is not tracked in PACE indication tables (only T1D/T2D/CKD/HF) | `STG_CAR_IQV_LAAD_FACT_DX` (HT DX codes) | 2.1 (Helper) |

> **Summary:** All 30 output columns can be produced with the exact same business logic. The migration scope is limited to replacing the **downstream/derived** Snowflake tables (Galaxy tables #6–9, dimension tables #3–5, HCP profile #10) with their PACE UC equivalents. The raw IQVIA claims and all computations that depend on them are unchanged.

### 4.3 How SWITCH_FROM and ADD_ON_TO Are Derived

These columns are computed in **Helper 2.2** at the **claim level** (Patient × Claim grain), then carried through to V6 as GROUP BY dimensions in **Step 3.4**.

**Source:** `STG_CAR_IQV_LAAD_FCT_RX` (raw Rx claims — no change in migration)  
**Parameters** (from `00_params`): `lookback_window=60d`, `grace_period=14d`, `lookforward_window=60d`, `overlap_window=-7d`

#### Helper 2.2 Logic — Claim-Level Classification

```
For each current Rx claim (last 13 weeks):

  Step 1: Self-join to find all PREVIOUS claims by the same PATIENT_ID
          with a DIFFERENT PRODUCT_GROUP, within 1 year lookback.

  Step 2: Rank previous products by:
          1st: PRIORITY (ascending — higher-priority product first)
          2nd: PREV_SVC_DT_END (most recent first)
          Pick Rank = 1 as the candidate transition product.

  Step 3: Split into two zones:
          • Within lookback (PREV_SVC_DT_END ≥ CURR_SVC_DT - 74 days)
          • Before lookback (PREV_SVC_DT_END < CURR_SVC_DT - 74 days)

  Step 4: Compute LOOKBACK_GAP = days from PREV_SVC_DT_END to CURR_SVC_DT
          Classify based on gap:

          ┌───────────────────────────────────────────────────────────────┐
          │  LOOKBACK_GAP > 365 days                               │
          │  → NEITHER (no switch, no add-on)                     │
          └───────────────────────────────────────────────────────────────┘
          ┌───────────────────────────────────────────────────────────────┐
          │  74 days < LOOKBACK_GAP ≤ 365 days                     │
          │  → SWITCH_FROM (patient stopped old drug long ago)    │
          └───────────────────────────────────────────────────────────────┘
          ┌───────────────────────────────────────────────────────────────┐
          │  LOOKBACK_GAP ≤ 74 days AND ≥ -7 days (overlap)       │
          │  → CHECK_LOOKFORWARD (ambiguous — need more info)     │
          └───────────────────────────────────────────────────────────────┘
          ┌───────────────────────────────────────────────────────────────┐
          │  LOOKBACK_GAP ≤ 74 days AND < -7 days                 │
          │  → CHECK_LOOKFORWARD_ADDON (overlapping supply,       │
          │    likely concurrent use — cannot be a switch)         │
          └───────────────────────────────────────────────────────────────┘

  Step 5: LOOKFORWARD check (for ambiguous cases):
          Look if patient filled the PREVIOUS product AGAIN
          within 60 days after PREV_SVC_DT_END.

          CHECK_LOOKFORWARD:
            • Lookforward present  → ADD_ON_TO  (still taking old drug)
            • Lookforward absent   → SWITCH_FROM (stopped old drug)

          CHECK_LOOKFORWARD_ADDON:
            • Lookforward present  → ADD_ON_TO
            • Lookforward absent   → NEITHER (overlapping but stopped)

  Step 6: Assign columns:
          SWITCH_FROM = PREV_PRODUCT_GROUP  (if classified as switch)
          ADD_ON_TO   = PREV_PRODUCT_GROUP  (if classified as add-on)
          Both NULL                         (if neither)
```

**Output:** One row per `CLAIM_ID` with `SWITCH_FROM` and `ADD_ON_TO` (at most one is non-NULL per claim).

#### Step 3.4 — HCP-Level Rollup

`SWITCH_FROM` and `ADD_ON_TO` are **kept as GROUP BY dimensions** (not aggregated). Each unique combination becomes a separate row:

```
GROUP BY: PROVIDER_ID, PERIOD_ID, PRODUCT_GROUP, AGE_GROUP, GENDER,
          PAY_TYPE, RX_CHANNEL, PAYER_PLAN_ID, SOURCE_OF_BUSINESS,
          SWITCH_FROM, ADD_ON_TO, INDICATION_GROUP,
          HYPERTENSION_FLAG, WEEK_ENDING_DATE

AGGREGATE: SUM(NBRX_FLAG) → NBRX
           SUM(NRX_FLAG)  → NRX
           COUNT_DISTINCT(CLAIM_ID) → TRX
```

A single HCP can have many rows in V6 — one for each distinct combination of switch/add-on label, product, indication, demographics, and time period across their patients’ claims.

#### V6 Distribution

| Column | Non-NULL Rows | % of 3.17B Total | Distinct Values | Top Values |
|--------|--------------|-------------------|-----------------|------------|
| `SWITCH_FROM` | 442M | 14% | 73 products | ARBs (83M), ACE Inhibitors (78M), Diuretics (49M), JARDIANCE (31M) |
| `ADD_ON_TO` | 1.38B | 43% | 71 products | ARBs (293M), ACE Inhibitors (230M), JARDIANCE (132M), Diuretics (118M) |
| `NRX` (from REFILL_CODE) | 3.17B (all) | 100% (no NULLs) | — | Total NRX = 1.53B; 1.51B rows have NRX > 0 |

> Add-ons (43%) are more common than switches (14%) because patients often start a new drug while continuing existing therapy. 86% of V6 rows have NULL SWITCH_FROM (no switch detected), and 57% have NULL ADD_ON_TO (no add-on detected).

---

## 5. Simplification Opportunities

The PACE UC tables have already pre-computed many intermediate results, offering significant pipeline simplification:

### 5.1 Steps That Can Be Eliminated

| Old Step | What It Did | Why Eliminable |
|----------|------------|----------------|
| **1.1 Data Preprocessing** (partial) | Product Group mapping via Excel | `pt_lvl_trx` already has PRODUCT_GROUP + PRODUCT_CLASS |
| **3.1 NBRx Calculation** | Computed NBRX_FLAG from claim history | `pt_lvl_nbrx` already identifies NBRx claims |
| **3.2 Patient Attributes** | Joined DIM_PTNT_DMGRPHC (gender, age) + DIM_PLN (pay type) | `pt_lvl_trx` already has AGE_GROUP, GENDER, PAY_TYPE |
| **3.5 HCP Attributes** (partial) | 4-table Galaxy cascade for BH_ID mapping | `pha_hcp_demographics` has PROVIDER_ID → BH_ID in single table |
| **3.5 HCP Attributes** (partial) | Specialty CSV mapping | `pt_lvl_trx` already has SPECIALTY_GROUP |

### 5.2 Steps That Must Be Retained

| Step | What It Does | Source (Revised) |
|------|-------------|------------------|
| **1.1 Data Preprocessing** | Load raw Rx claims, filter paid, map products | **No change** — continues using `STG_CAR_IQV_LAAD_FCT_RX` + Product Mapping Excel |
| **2.1 Indication Group** | Patient-level indication dates (T2D, CKD, CVD, HF, HT) | **No change** — continues using `STG_CAR_IQV_LAAD_FCT_RX` + `STG_CAR_IQV_LAAD_FACT_DX` |
| **2.2 Switch From/Add-on** | Claim-level transition labeling | **No change** — continues using `STG_CAR_IQV_LAAD_FCT_RX` |
| **3.1 NBRx Calculation** | NBRX_FLAG + NRX_FLAG computation | **No change** — REFILL_CODE available from raw claims |
| **3.3 Switch From & Indication** | Join indication + switch/add-on labels | **No change** — outputs from 2.1 and 2.2 |
| **3.4 HCP Roll-up** | Aggregate patient→HCP level claims | **No change** — GROUP BY 14 dimensions |
| **3.5 HCP Attributes** (reduced) | NPI, BH_ID, name, address | **Changed** — single join to `pha_hcp_demographics` + `mdm_stg_hcp_prfl` (replaces 4-table Galaxy cascade) |

---

## 6. Proposed Migration Architecture

### 6.1 Revised Pipeline — Hybrid Architecture (Raw IQVIA + PACE UC)

```
┌──────────────────────────────────────────────────────────────┐
│ Sources: NO CHANGE (Raw IQVIA Claims)                        │
│                                                              │
│  STG_CAR_IQV_LAAD_FCT_RX   (Rx claims)                      │
│    → CLAIM_ID, PATIENT_ID, SVC_DT, PROVIDER_ID,             │
│      NDC_CD, DAYS_SUPPLY, REFILL_CODE, SOB, RX_CHANNEL      │
│                                                              │
│  STG_CAR_IQV_LAAD_FACT_DX   (Dx claims)                      │
│    → PATIENT_ID, SERVICE_DATE, DIAGNOSIS_CODE                │
│    → Used for indication group (T2D, CKD, CVD, HF, HT)      │
└──────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────┴────────────────────────────────┐
│ Sources: MIGRATED (Snowflake → PACE UC)                       │
│                                                              │
│  DIM_PTNT_DMGRPHC  → ELIMINATED (in pt_lvl_trx)             │
│  DIM_PLN           → ELIMINATED (in pt_lvl_trx)             │
│  DIM_PRVDR         → pha_hcp_demographics / stg_car_dim_prvdr│
│  Galaxy cascade    → pha_hcp_demographics + mdm_stg_hcp_prfl │
│    (MAP_CUSTOMER_XREF, DIM_CUSTOMER_HCP,                     │
│     FACT_IQV_LAAD_SUB_NATIONAL, _XREF)                       │
│  MDM_STG_HCP_PRFL  → mdm_stg_hcp_prfl (same, now in UC)     │
│  V6 append target  → kerendia_laad_based_lrx.v6 (UC Delta)   │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ Pipeline Steps (mostly unchanged)                            │
│                                                              │
│  1.1 Data Preprocessing   [NO CHANGE — raw Rx claims]        │
│  2.1 Indication Group     [NO CHANGE — raw Rx + Dx claims]   │
│  2.2 Switch From/Add-on   [NO CHANGE — raw Rx claims]        │
│  3.1 NBRx Calculation     [NO CHANGE — REFILL_CODE avail.]   │
│  3.2 Patient Attributes   [ELIMINATED — in pt_lvl_trx]       │
│  3.3 Switch & Indication  [NO CHANGE]                        │
│  3.4 HCP Roll-up          [NO CHANGE]                        │
│                                                              │
│  3.5 HCP Attributes       [CHANGED — migration target]       │
│    → Galaxy 4-table cascade replaced by:                     │
│      pha_hcp_demographics (BH_ID, NPI, name, address)        │
│      + mdm_stg_hcp_prfl (MIDDLE_NAME, BH_ID fallback)        │
│                                                              │
│  3.6 Save                 [CHANGED — UC Delta only]          │
│    → Write to UC Delta (deprecate Snowflake write)            │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. Decisions Required

| # | Decision | Status | Details |
|---|----------|--------|---------|
| 1 | **Pipeline output destination** | **DECISION NEEDED** | **(A) UC Delta only** or **(B) UC Delta + Snowflake.** Recommend migrating to UC-only write. |
| 2 | **3.5 HCP Attributes source** | **DECISION NEEDED** | Replace Galaxy 4-table cascade with `pha_hcp_demographics` + `mdm_stg_hcp_prfl` (see NPI/BH_ID Mapping Migration Analysis for overlap data). |
| 3 | **3.2 Patient Attributes** | **DECISION NEEDED** | Can be eliminated if using `pt_lvl_trx` which already has AGE_GROUP, GENDER, PAY_TYPE. Validate value alignment first. |

---

## 8. Additional UC Tables Discovered

| Table | Schema | Relevance |
|-------|--------|----------|
| `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v6` | kerendia_laad_based_lrx | Existing V6 in UC Delta — the append target |
| `kerendia_nba_3.kerendia_laad_based_lrx_v6` | kerendia_nba_3 | Another copy of V6 in the NBA schema |
| `kerendia_nba_3.stg_car_iqv_laad_dim_prvdr` | kerendia_nba_3 | Provider dimension already migrated to UC (30 cols including PROVIDER_ID, names, address, specialty, NPI_NUMBER) |
| `kerendia_nba_3_pace.pha_weekly_laad_patient_lvl_nbrx_internal_with_ker_pxy_rules` | kerendia_nba_3_pace | Weekly-dated NBRx table from PACE (26 cols) — similar to pt_lvl_nbrx but with weekly snapshots |
| `kerendia_nba_3_pace.pha_weekly_laad_patient_lvl_trx_internal_with_ker_pxy_rules` | kerendia_nba_3_pace | Weekly-dated TRx table from PACE (25 cols) — similar to pt_lvl_trx but with weekly snapshots |
| `pace_ker_in_house_schema.lrx_indication` | pace_ker_in_house_schema | Patient-level indication dates (T1D/T2D/CKD/HF) — subset of indication_table, 15 cols |
| `pace_ker_in_house_schema.pha_lrx_transition_product_mapping` | pace_ker_in_house_schema | NDC → Product mapping — potential replacement for Excel mapping |

---

## 9. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Galaxy → UC BH_ID mapping discrepancies (3.5) | **Medium** | 93.9% exact match; 3.3% improved; 0.1% degraded (see NPI/BH_ID Mapping Migration Analysis) |
| DIM_PTNT / DIM_PLN elimination (3.2) | **Low** | Validate AGE_GROUP, GENDER, PAY_TYPE in pt_lvl_trx match original dimension values |
| Snowflake write deprecation (3.6) | **Low** | Coordinate with downstream consumers of Snowflake V6 table |
| Weekly snapshot alignment (PACE vs old pipeline) | **Low** | Validate that pt_lvl_trx date ranges cover same period as raw claims |

---

## 10. Next Steps

- [ ] **Validate 3.2 elimination:** Compare AGE_GROUP, GENDER, PAY_TYPE from `pt_lvl_trx` vs original `DIM_PTNT_DMGRPHC` + `DIM_PLN` values
- [ ] **Validate 3.5 migration:** Compare BH_ID, NPI output from `pha_hcp_demographics` cascade vs Galaxy cascade (see NPI/BH_ID Mapping Migration Analysis — 93.9% exact match confirmed)
- [ ] **Decide output destination:** UC Delta only vs UC Delta + Snowflake
- [ ] **Build migrated 3.5 notebook:** Replace Galaxy cascade with `pha_hcp_demographics` + `mdm_stg_hcp_prfl` joins
- [ ] **Build migrated 3.6 notebook:** Write to UC Delta only (deprecate Snowflake write)
- [ ] **End-to-end validation:** Run migrated pipeline and compare full V7 output against V6 for a sample refresh cycle

---

*Generated by Genie Code — October 2026*