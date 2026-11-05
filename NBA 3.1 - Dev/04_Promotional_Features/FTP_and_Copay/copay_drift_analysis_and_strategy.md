# Copay & BlinkRX Features — Drift Analysis & NBA 3.1 Revamp Strategy

**Channel:** Copay / BlinkRX — Market access promotional features  
**Old notebook:** `22_copay_features` in `.../NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**New notebook target:** `.../NBA 3.1 - Dev/04_Promotional_Features/FTP_and_Copay/22_copay_features`  
**Date:** 30 October 2026  
**Built from:** reading old and new data sources via Snowflake and comparing schemas, counts, and sample data

---

## 1. Data Source Change Summary

| Aspect | Old (NBA 3.0) | New (NBA 3.1) |
| --- | --- | --- |
| **Table** | `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_COPAY_PROGRAM` | `CPH_DB_PROD.MODEL_V2.TRMN_CSMR_PROF_MDM` |
| **Type** | Snowflake view | Snowflake base table |
| **Granularity** | Claim-level (one row per pharmacy copay claim transaction) | **Consumer profile-level** (one row per consumer × data source × brand) |
| **Total columns** | 72 | 47 |
| **Rows** | 118,659 (USE_SLS='Y', NPI not null) | 1,558,642 (per Snowflake metadata; **0 accessible with current role**) |
| **Distinct HCPs** | 9,422 NPIs | N/A — this table tracks **consumers/patients**, not HCPs |
| **Date range** | Jan 2023 – Dec 2025 | Unknown (table inaccessible) |
| **HCP identifier** | `PRSC_NPI` (prescriber NPI) | **Not directly available** — table has `CNS_ID`, `LEGACY_BH_ID` (consumer IDs) |
| **Date column** | `RX_DT` (datetime string) | `CONSENT_CAPTURE_DATE` (timestamp), `SYS_CREATED_ON`, `SYS_MODIFIED_ON` |
| **Claim tracking** | `CLM_AUTH_NUM`, `ORGN_CLM_AUTH_NUM`, `DAY_SUPPLY` | **Not available** — no claim-level data |
| **Database** | `PHCDW` (Snowflake) | `CPH_DB_PROD` (Snowflake) |

---

## 2. CRITICAL: Fundamental Schema Change

**This is NOT a simple column mapping — the new table is a completely different type of data.**

The old source (`VIEW_RB_KERENDIA_COPAY_PROGRAM`) was a **pharmacy claims table**: each row was one Rx claim where a copay card was used. The notebook counted how many times each HCP's patients used a copay card.

The new source (`TRMN_CSMR_PROF_MDM`) is a **consumer/patient master data management (MDM) table**: each row represents a consumer profile, with demographics, marketing attribution (UTM parameters, landing pages), consent status, and source tracking. It has **no prescription or claim columns**.

### What the New Table Contains

| Column Group | Columns | Description |
| --- | --- | --- |
| Consumer identity | `CNS_ID`, `LEGACY_BH_ID`, `SOURCE_CONSUMER_ID` | Unique consumer identifiers |
| Data provenance | `DATA_SOURCE`, `BRAND`, `DISEASE_STATE` | Which program/brand the consumer came from |
| Demographics | `FIRST_NAME`, `MIDDLE_NAME`, `LAST_NAME`, `GENDER`, `DATE_OF_BIRTH`, `AGE` | Consumer PII |
| Contact | `EMAIL`, `PHONE_NUMBER`, `ADDRESS_LINE_1/2`, `ZIP`, `CITY`, `STATE`, `COUNTRY_CODE` | Contact info |
| Consent | `EMAIL_OPT_STATUS`, `PHONE_OPT_STATUS`, `CONSENT_CAPTURE_DATE`, `OPTIN_LEVEL` | Communication preferences |
| Marketing attribution | `UTM_SOURCE`, `UTM_MEDIUM`, `UTM_CAMPAIGN`, `LANDING_PAGE_URL` | How the consumer arrived |
| Source tracking | `SOURCE`, `PFRC_SOURCE`, `PFRC_SOURCE_DETAIL`, `LOCATION_OF_FORM` | Registration source |
| DTC/content | `DTC_TYPE`, `TOPIC_KEY`, `TOPIC_TYPE` | DTC content type |
| Flags | `MDM_FLAG`, `PFRC_FLAG`, `LCD_FLAG`, `TRGT_FLAG`, `IS_LATEST_FLAG`, `SYS_DELETE_FLAG` | Record status |
| System | `LOAD_ID`, `SYS_LOADED_ON`, `SYS_CREATED_BY`, `SYS_CREATED_ON`, `SYS_MODIFIED_ON`, `HASH_KEY` | ETL metadata |

### What the New Table Does NOT Contain

* No `PRSC_NPI` or any prescriber/HCP identifier
* No `CLM_AUTH_NUM`, `ORGN_CLM_AUTH_NUM` (claim tracking)
* No `DAY_SUPPLY`, `QTY`, `PTNT_COPAY`, `PATOOP` (Rx/copay values)
* No `RX_DT`, `RX_FILL_DT` (prescription dates)
* No `NDC_NUM`, `DRG_DESC` (drug info)

---

## 3. Column-Level Drift Analysis

### 3.1 Old Columns Used by the Copay Notebook

| Old Column | Used For | New Table Equivalent | Status |
| --- | --- | --- | --- |
| `PRSC_NPI` | Identify prescribing HCP | — | **MISSING** — no HCP identifier in new table |
| `RX_DT` | Event date (truncated to month) | `CONSENT_CAPTURE_DATE` | **Different meaning** — consent date, not Rx date |
| `CLM_AUTH_NUM` | Claim ID | — | **MISSING** |
| `ORGN_CLM_AUTH_NUM` | Reversal grouping | — | **MISSING** |
| `DAY_SUPPLY` | Reversal detection (negative = cancellation) | — | **MISSING** |
| `GRP_NUM` | Group number (for PCT features) | — | **MISSING** |
| `PTNT_COPAY` | Copay amount (for PCT features) | — | **MISSING** |
| `PATOOP` | Patient out-of-pocket (for PCT features) | — | **MISSING** |
| `USE_SLS` | Filter valid claims | `IS_LATEST_FLAG`, `SYS_DELETE_FLAG` | Different filter logic |

### 3.2 New Columns That Could Generate Features

| New Column | Potential Feature | Notes |
| --- | --- | --- |
| `CNS_ID` / `LEGACY_BH_ID` | Count of unique consumers per HCP | Requires a **consumer-to-HCP linkage** (not in this table) |
| `DATA_SOURCE` | Flag for source type (copay vs BlinkRX) | Could distinguish Copay and BlinkRX features |
| `CONSENT_CAPTURE_DATE` | Temporal features (enrollment timing) | Registration date, not Rx date |
| `SOURCE` / `PFRC_SOURCE` | Enrollment channel features | How the consumer found the program |
| `DTC_TYPE` / `TOPIC_KEY` | Content engagement features | What DTC content drove enrollment |
| `IS_LATEST_FLAG` | Record currency filter | Filter to latest record per consumer |

---

## 4. Access Issue

**The `TRMN_CSMR_PROF_MDM` table returns 0 rows when queried**, despite Snowflake metadata reporting 1,558,642 rows. This is likely caused by:
* Row-level security (RLS) policy on the table that filters data for our Snowflake role
* Column-level security masking
* The table being mid-refresh (last altered: 2026-10-30 11:00)

**Action needed:** confirm with the Galaxy/data engineering team which Snowflake role has SELECT access to this table, or request access for `BAY_CPH_CDP_PROD_CR_US_EAST_1_MVXPF_MVXPF`.

---

## 5. Revamp Strategy Options

Given the fundamental schema change, there are **three possible approaches**:

### Option A: Consumer-Count Features (If HCP→Consumer Linkage Exists)

If we can link consumers in `TRMN_CSMR_PROF_MDM` to prescribing HCPs (via a separate mapping table or via claims), we could build:
* `TOTAL_COPAY_ENROLLMENTS`: count of consumers enrolled in copay per HCP, per time window
* `TOTAL_BLINKRX_ENROLLMENTS`: same for BlinkRX
* Rolling window features (30/60/90/120/150/180 days) using `CONSENT_CAPTURE_DATE`

**Requires:** a consumer→HCP mapping table (possibly from claims data or from `LEGACY_BH_ID` if it maps to HCP).

### Option B: Use Sales Aligned Table for Copay Too

The `ANLT_BASE_FACT_SALES_ALIGNED` table has `SALE_TYP` values beyond FTP. While there’s no explicit `COPAY` type, the following may represent copay activity:
* `COMMERCIALRX` rows with copay-related `SALE_CHNL_DESC`
* Or a separate column in the 495-column table that captures copay status

**Requires:** deeper exploration of `ANLT_BASE_FACT_SALES_ALIGNED` columns to find copay indicators.

### Option C: Keep Old Source Until New Is Ready

If the `TRMN_CSMR_PROF_MDM` table is not yet populated or accessible, keep using `VIEW_RB_KERENDIA_COPAY_PROGRAM` for NBA 3.1 and migrate later.

### Recommended Approach

**Start with Option A** (if linkage exists) or **Option B** (if copay data is in the sales table). Flag the access issue for the data team. In the meantime, create the notebook shell with the old logic as a reference, and add a clear TODO marker for the data source swap.

---

## 6. Old Copay Notebook Logic (Reference)

The old copay notebook follows this pipeline:

1. **Load copay claims** from `VIEW_RB_KERENDIA_COPAY_PROGRAM` (filter: `USE_SLS='Y'`, `PRSC_NPI IS NOT NULL`)
2. **Truncate date to month** (`date_trunc('MM', RX_DT)`)
3. **Remove reversals** via `ORGN_CLM_AUTH_NUM` grouping (same logic as FTP)
4. **Aggregate** per NPI per month: `count(lit(1))` → `TOTAL_RX_COPAY`
5. **Fill missing months** using `step2_fill_missing`
6. **Generate lag features** (1–6 months) using `step3_lag`
7. **Create PCT features**: for each window, `PCT_TOTAL_RX_COPAY_IN_LAST_N_MONTH = count / total`
8. **Filter** to dates >= 2022-01-01
9. **Join NPI→BHID mapping** (inner join)
10. **Add PULL_DT** and **save** to Delta

### Output Columns (Old)
* `NPI_NUMBER` (or `BHID` after join)
* `SVC_DT_M` (month)
* `TOTAL_RX_COPAY`
* 6 lag features: `TOTAL_RX_COPAY_IN_LAST_1_MONTH` through `_6_MONTH`
* 6 PCT features: `PCT_TOTAL_RX_COPAY_IN_LAST_1_MONTH` through `_6_MONTH`
* `PROVIDER_ID`, `BHID`
* `PULL_DT`

---

## 7. Validation Plan

| Check | Method |
| --- | --- |
| Table accessibility | Confirm SELECT access on `TRMN_CSMR_PROF_MDM` with correct role |
| Brand/disease filter | Once accessible, check `BRAND` and `DISEASE_STATE` values for Kerendia |
| Consumer-HCP linkage | Identify if `LEGACY_BH_ID` maps to HCP BHIDs or if a separate join table exists |
| Feature parity | Ensure revamped notebook produces the same feature structure (lag + PCT) |
| Schema match | Final output must have: HCP_COHORT_ID, PULL_DT, lag features, PCT features |

---

## 8. Open Questions (Require User / Data Team Input)

1. **Which Snowflake role** has access to `CPH_DB_PROD.MODEL_V2.TRMN_CSMR_PROF_MDM`?
2. **How do we link consumers to HCPs?** The old source had `PRSC_NPI` per claim; the new source has consumer IDs but no HCP.
3. **What is `DATA_SOURCE`?** Does it distinguish Copay vs BlinkRX? What are the distinct values?
4. **Is BlinkRX a new feature** not in NBA 3.0, or a replacement for copay?
5. **Should we use the sales aligned table instead?** `ANLT_BASE_FACT_SALES_ALIGNED` might have copay-equivalent data under a different `SALE_TYP`.
6. **What PCT features should be retained?** The old notebook had `PCT_TOTAL_RX_COPAY_IN_LAST_N_MONTH` (copay count / total count). With a consumer profile table, the denominator changes.
