# Personal Promotional Features

Consolidated reference for **personal promotional** feature engineering in the Kerendia NBA 3.x
pipeline. Personal promotions involve direct human interaction between a sales representative
and an HCP. Three channels are covered: F2F Sales Rep Calls, iRep Emails, and
ClickStream/CLM. All share a common 3-step pipeline but differ in source systems, binary
flag definitions, and pivot dimensions.

---

## 0. Shared Infrastructure

### 0.1 Notebook Design Convention

All promotional feature notebooks are **self-contained**: each notebook defines its own
utility functions inline (Get_Data_Snowflakes, step2/step3, sanitize). There are no `%run`
dependencies between generated notebooks and no `dbutils.widgets` parameterization.

The original Ops pipeline uses `%run` to import shared helpers from:
```
/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/
  NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection
  NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config
  NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_step23_function
```
The self-contained pattern avoids cross-notebook dependencies in the dev pipeline.

### 0.2 Snowflake Connection: `Get_Data_Snowflakes`

```python
def Get_Data_Snowflakes(query, Schema="PHCDW_CDM",
                        Role="BAY_CPH_CDP_PROD_CR_US_EAST_1_MVXPF_MVXPF"):
    """Execute a SQL query against Snowflake and return a Spark DataFrame."""
    scope = "US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair"
    private_key_pem = dbutils.secrets.get(scope, "snowflake-private-key")
    private_key_passphrase = dbutils.secrets.get(scope, "snowflake-private-key-passphrase")
    snowflake_user = dbutils.secrets.get(scope, "snowflake-user")
    snowflake_account = dbutils.secrets.get(scope, "snowflake-account")

    from cryptography.hazmat.primitives import serialization
    p_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"),
        password=private_key_passphrase.encode("utf-8"),
    )
    snowflake_pem_private_key = (
        p_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        .decode("utf-8")
        .replace("-----BEGIN PRIVATE KEY-----", "")
        .replace("-----END PRIVATE KEY-----", " ")
        .replace("\n", " ")
        .strip()
    )

    sfOptions = {
        "sfURL": "bayer_cphcdp_prod.us-east-1.snowflakecomputing.com:443",
        "sfUser": snowflake_user,
        "pem_private_key": snowflake_pem_private_key,
        "sfRole": Role,
        "sfSchema": Schema,
        "sfDatabase": "PHCDW",
        "sfWarehouse": "PROD_CYRUS_BI_WH",
        "purge": "off",
        "autopushdown": "on",
    }
    return (
        spark.read.format("net.snowflake.spark.snowflake")
        .options(**sfOptions)
        .option("query", query)
        .load()
    )
```

**Note:** Requires `%pip install snowflake-connector-python --quiet` and a Python restart
if the connector is not already installed.

**Digital (notebook 24) uses a different connection config** (`sfOptionscdpread`) with
schema `PHCDW_DSAA` and warehouse `PROD_DATA_SCIENCE_CYRUS_WH`. See the non-personal
skill Section 4 for the exact connection pattern.

### 0.3 Canonical Sanitize Function

Used across both personal and non-personal channels:

```python
import re
def sanitize_column_name(name):
    name = name.replace("+", "_AND_").replace("/", "_OR_")
    name = re.sub(r'[^A-Za-z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_')
    return name.upper()
```

### 0.4 Output Format Convention

All promotional feature notebooks write output as **Parquet** format (not Delta), using
`.write.format("parquet").mode("overwrite")`. The exception is Digital (notebook 24), which
uses `.write.format("delta").mode("overwrite").option("overwriteSchema", "true")` because
schema evolution from new pivot values requires `overwriteSchema`.

---

## 1. Channel Inventory

| # | Channel | Notebook | Source System | Output Rows | Feature Count | Distinct HCPs | Sparsity (% zeros) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F2F Sales Rep Calls | `25_promotional_features_call` | `CPH_DB_PROD.MODEL_V2.FACT_CALL` + `MAP_CUSTOMER_XREF` | 2,086,597 | 212 | 129,787 | 94.3% |
| 2 | iRep Emails | `16_promotional_features_irep` | `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_IREP` | 966,322 | 86 | 79,627 | 97.2% |
| 3 | ClickStream/CLM | `18_promotional_ClickStream_features` | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM` + `FACT_CALL` | 191,214 | 26 | 18,804 | 67.2% |

All channels share:
- **Grain:** HCP-level via `BHID` (Bayer Healthcare ID)
- **Join key:** `HCP_COHORT_ID` = `{BHID}_{COHORT}` (e.g., `BH12345678_C01`)
- **Date range:** 2022-03-17 to 2025-04-16
- **Null/zero convention:** `fillna(0)` — zeros, not nulls, for missing promotional activity. Downstream models interpret 0 as "HCP was not promoted via this channel."

---

## 2. Shared Pipeline Architecture

All three channels follow an identical 3-step pipeline:

### Step 1: Load, Process, Create Binary Flags

1. Load raw data from Snowflake via `Get_Data_Snowflakes(query)`
2. Filter to `KERENDIA` brand, valid BHID, and date range
3. Create binary indicator columns for each dimension (channel type, call type, etc.)
4. Cross-join with **cohort anchor dates** (26 cohorts, C01–C26)
5. Filter to lookback window: `MONTH_ID BETWEEN LOOKBACK_START_DATE AND LOOKBACK_END_DATE`
6. Create `HCP_COHORT_ID = concat(BHID, '_', COHORT)`
7. GroupBy `[HCP_COHORT_ID, LOOKBACK_START_DATE, LOOKBACK_END_DATE, MONTH_ID]` and aggregate (SUM for counts, AVG for durations)

### Step 2: Fill Missing Dates (Dense Spine)

```python
def step2_fill_missing_dates(df):
    cohort_ranges_df = (
        df.select("HCP_COHORT_ID", "LOOKBACK_START_DATE", "LOOKBACK_END_DATE")
        .dropDuplicates()
        .withColumn("EXPANDED_DATE",
            F.explode(F.expr("sequence(LOOKBACK_START_DATE, LOOKBACK_END_DATE, interval 1 day)")))
    )
    cohort_dates_df = cohort_ranges_df.withColumnRenamed("EXPANDED_DATE", "MONTH_ID").drop("LOOKBACK_START_DATE")
    df_filled = (
        cohort_dates_df
        .join(df.drop("LOOKBACK_START_DATE", "LOOKBACK_END_DATE"),
              on=["HCP_COHORT_ID", "MONTH_ID"], how="left")
        .orderBy("HCP_COHORT_ID", "MONTH_ID")
    )
    return df_filled
```

**Critical note:** This expands each HCP-cohort to ~395 rows (one per day in the 13-month
lookback). With 26 cohorts and ~130K HCPs, this can produce billions of rows. See Section 7
for memory implications.

After expansion, all feature columns are filled with 0 for missing days.

### Step 3: Lag Features (Rolling Windows)

```python
def step3_lag_date(df, key_col, date_col, last_i_days_list):
    window_base = Window.partitionBy(key_col).orderBy(date_col)
    features = [col for col in df.columns
                if col not in [key_col, date_col, 'LOOKBACK_END_DATE']]
    last_i_month = [
        F.sum(col).over(window_base.rowsBetween(-i+1, 0))
         .alias(f"{col}_IN_LAST_{int(i / 30)}_MONTH")
        for i in last_i_days_list for col in features
    ]
    return df.select("*", *last_i_month)
```

**Rolling windows:** `last_i_days_list = [30, 60, 90, 120, 150, 180]` → produces
`_IN_LAST_1_MONTH` through `_IN_LAST_6_MONTH` suffixes.

After lag computation, the pipeline filters to `MONTH_ID == LOOKBACK_END_DATE` (keeping only
the anchor-date row per cohort), drops the raw base columns (keeping only `_IN_LAST_*`
columns), and renames `MONTH_ID` to `SVC_DT`.

### Cohort Anchor Dates

Loaded from:
```
/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/
  hcp_level_model/dev_folder/query_output/promotional_features_hcp_model_cohort_anchor_dates.csv
```

| Column | Type | Description |
| --- | --- | --- |
| `LOOKBACK_START_DATE` | date | Start of 13-month lookback window |
| `LOOKBACK_END_DATE` | date | End of lookback / anchor date |
| `COHORT` | string | Cohort label (C01–C26) |

### NPI-to-BHID Crosswalk

Used by ClickStream (which starts with NPI via the calls join):
```
/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/
  hcp_level_features/query_output/kerendia_nba_3_0_npi_bhid_mapping.parquet
```

---

## 3. Input Contract

### 3.1 Canonical Columns (Post-Processing)

| Canonical | Type | Description | Used By |
| --- | --- | --- | --- |
| `BHID` | string | Bayer Healthcare ID (HCP identifier) | All channels |
| `MONTH_ID` | date | Event date (daily grain, not truncated) | All channels |
| `HCP_COHORT_ID` | string | `{BHID}_{COHORT}` composite key | All channels |
| `LOOKBACK_START_DATE` | date | Cohort lookback start | All channels |
| `LOOKBACK_END_DATE` | date | Cohort lookback end / anchor | All channels |

### 3.2 Raw-Source Column Mapping

| Canonical | Calls Raw | iRep Raw | ClickStream Raw |
| --- | --- | --- | --- |
| `BHID` | `BAYER_CUST_ID` (via `MAP_CUSTOMER_XREF`) | `ACCT_IDNTFR` (direct) | `BAYER_HCP_ID` (via `ANLT_BASE_FACT_CLKSTRM`) |
| `MONTH_ID` | `CALL_DATE` (cast to date) | `EMAIL_SENT_DT` (cast to date) | `DATE_ID` (parsed from `yyyyMMdd` int) |
| Event filter | `UPPER(DETL_PROD) = 'KERENDIA'`, `UPPER(STAT) = 'SUBMITTED_VOD'` | `Email_Status = 'Delivered'`, `acct_idntfr NOT LIKE 'BHO%'` | `BAYER_PROD_NM = 'KERENDIA'` |

---

## 4. Channel: F2F Sales Rep Calls

### What It Measures

Frequency and type of direct sales rep interactions with HCPs for Kerendia, decomposed
across three orthogonal dimensions: channel type, call type, and call purpose.

### Source Query

```sql
SELECT B.BAYER_CUST_ID AS BHID,
       to_date(A.CALL_DATE) as MONTH_ID,
       CASE WHEN CALL_REC_TYP_NM LIKE '%BPH_Face2Face_SIG%' THEN 'F2F'
            WHEN CALL_REC_TYP_NM LIKE '%BPH_Non_Face2Face%' THEN 'PHONE'
            WHEN UPPER(CALL_REC_TYP_NM) IN ('BPH_GROUP_CALL_SIG','EVENT_VOD') THEN 'GROUP_CALL'
            WHEN CALL_REC_TYP_NM LIKE '%BPH_Remote%' THEN 'REMOTE_CALL'
            ELSE CALL_REC_TYP_NM END AS CHNNL_NM,
       CALL_TYP AS CALL_TYP_CD,
       CALL_DUR AS CALL_DURTN,
       CALL_PURPS AS CALL_PRPSE
FROM CPH_DB_PROD.MODEL_V2.FACT_CALL A
LEFT JOIN CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF B ON A.SOURCE_CUST_ID = B.SOURCE_CUST_ID
WHERE UPPER(STAT) = 'SUBMITTED_VOD'
  AND UPPER(DETL_PROD) = 'KERENDIA'
  AND BAYER_CUST_ID NOT LIKE '%BHO%'
  AND BAYER_CUST_ID IS NOT NULL
```

### Binary Flag Definitions

**Dimension 1 — Channel Type (4 flags):**

| Flag | Condition | Meaning |
| --- | --- | --- |
| `F2F` | `CHNNL_NM == 'F2F'` | Face-to-face visit |
| `PHONE` | `CHNNL_NM == 'PHONE'` | Phone call |
| `GROUP_CALL` | `CHNNL_NM == 'GROUP_CALL'` | Group call / event |
| `REMOTE_CALL` | `CHNNL_NM == 'REMOTE_CALL'` | Remote / virtual meeting |

**Dimension 2 — Call Type (5 flags):**

| Flag | Condition | Meaning |
| --- | --- | --- |
| `DETAIL_ONLY` | `CALL_TYP_CD == 'Detail Only'` | Product detail, no sample |
| `DETAIL_WITH_SAMPLE` | `CALL_TYP_CD == 'Detail with Sample'` | Detail + sample left |
| `GROUP_DETAIL` | `CALL_TYP_CD == 'Group Detail'` | Group detail session |
| `GROUP_DETAIL_WITH_SAMPLE` | `CALL_TYP_CD == 'Group Detail with Sample'` | Group detail + sample |
| `EVENT_DETAIL` | `CALL_TYP_CD == 'Event Detail'` | Event-related detail |

**Dimension 3 — Call Purpose (5 flags):**

| Flag | Condition | Meaning |
| --- | --- | --- |
| `CALL_PURPOSE_PROMOTIONAL_ACTIVITY` | `CALL_PRPSE == 'Promotional Activity'` | Standard promotion |
| `CALL_PURPOSE_PROMOTIONAL_ACTIVITY_WITH_MEAL` | `CALL_PRPSE == 'Promotional Activity with meal'` | Promotion with meal |
| `CALL_PURPOSE_EVENT_RELATED_PROMOTIONAL_ACTIVITY` | `CALL_PRPSE == 'Event Related Promotional Activity'` | Event-tied promotion |
| `CALL_PURPOSE_NON_PROMOTIONAL_ACTIVITY` | `CALL_PRPSE == 'Non-Promotional Activity'` | Admin / non-promotional |
| `CALL_PURPOSE_MISCELLANEOUS` | `CALL_PRPSE` not in above | Catch-all |

**Dimension 4 — Call Duration (1 numeric):**

| Feature | Formula | Notes |
| --- | --- | --- |
| `CALL_DURATION` | `WHEN CAST(CALL_DURTN AS FLOAT) > 0 THEN CAST(CALL_DURTN AS FLOAT) ELSE 0` | Guards against historical DQ issues (negative/non-numeric durations). Do not remove the cast+guard. |

### Cross-Product Features

For every `(channel_type, call_type)` pair, a cross-product feature is generated:

```python
for channel in chnnl_nm:  # [F2F, PHONE, GROUP_CALL, REMOTE_CALL]
    for call_type in call_typ_cd:  # [DETAIL_ONLY, DETAIL_WITH_SAMPLE, ...]
        df = df.withColumn(
            f"TOTAL_{channel}_AND_{call_type}",
            least(f"TOTAL_{channel}", f"TOTAL_{call_type}")
        )
```

**Semantics:** `least(flag_a, flag_b)` acts as logical AND for binary flags — returns 1 only
when both are 1. This is intentional. For example, `TOTAL_F2F_AND_DETAIL_WITH_SAMPLE`
counts calls that were both face-to-face AND included a sample detail.

### Aggregation

```
groupBy(HCP_COHORT_ID, LOOKBACK_START_DATE, LOOKBACK_END_DATE, MONTH_ID)
  .agg(
    sum(F2F)                     -> TOTAL_F2F,
    sum(PHONE)                   -> TOTAL_PHONE,
    sum(GROUP_CALL)              -> TOTAL_GROUP_CALL,
    sum(REMOTE_CALL)             -> TOTAL_REMOTE_CALL,
    sum(DETAIL_ONLY)             -> TOTAL_DETAIL_ONLY,
    sum(DETAIL_WITH_SAMPLE)      -> TOTAL_DETAIL_WITH_SAMPLE,
    sum(GROUP_DETAIL)            -> TOTAL_GROUP_DETAIL,
    sum(GROUP_DETAIL_WITH_SAMPLE)-> TOTAL_GROUP_DETAIL_WITH_SAMPLE,
    sum(EVENT_DETAIL)            -> TOTAL_EVENT_DETAIL,
    sum(call_purpose_flags...)   -> TOTAL_CALL_PURPOSE_*,
    sum(call_duration_cleaned)   -> TOTAL_CALL_DURATION,
    -- plus all 20 cross-product features
  )
```

Base features: 4 + 5 + 5 + 1 + 20 cross-products = **35 base features**
After 6 rolling windows: 35 × 6 = **210 lag features** + `HCP_COHORT_ID` + `SVC_DT` = **212 columns**

### Output Column Naming

`TOTAL_{FLAG}_IN_LAST_{N}_MONTH`

Examples:
- `TOTAL_F2F_IN_LAST_1_MONTH`
- `TOTAL_F2F_AND_DETAIL_WITH_SAMPLE_IN_LAST_3_MONTH`
- `TOTAL_CALL_DURATION_IN_LAST_6_MONTH`

### Output Path

```
/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/
  hcp_level_model/dev_folder/notebook_output/kerendia_nba_3_hcp_model_call_features.parquet
```

---

## 5. Channel: iRep Emails

### What It Measures

Frequency of rep-triggered approved emails sent to HCPs via Veeva iRep, decomposed by
delivery status (delivered, clicked, opened) and by approved document content category.

### Source Query

```sql
SELECT ACCT_IDNTFR AS BHID, EMAIL_SENT_DT, EMAIL_CLCKD_FLG,
       EMAIL_OPND_FLG, EMAIL_STATUS, APPRVD_DOC_NM
FROM PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_IREP
WHERE acct_idntfr NOT LIKE 'BHO%'
  AND Email_Status = 'Delivered'
  AND DATE_TRUNC('MONTH', EMAIL_SENT_DT) <= '2025-04-16'
```

### Binary Flag Definitions

**Delivery Status (3 flags):**

| Flag | Condition | Meaning |
| --- | --- | --- |
| `IREP_EMAIL_DELIVERED_FLAG` | `EMAIL_STATUS == 'Delivered'` | Email successfully delivered |
| `IREP_EMAIL_CLICKED_FLAG` | `EMAIL_CLCKD_FLG == 1` | Recipient clicked a link |
| `IREP_EMAIL_OPENED_FLAG` | `EMAIL_OPND_FLG == 1` | Recipient opened email |

**Approved Document Name Categories (11 flags):**

| Flag | Condition (APPRVD_DOC_NM matches) |
| --- | --- |
| `IREP_APPRVD_DOC_NM_FDA` | `APPRVD_DOC_NM.isin("Kerendia FDA-Approved Announcement", "Kerendia FDA-Approved iRep Email Announcement")` |
| `IREP_APPRVD_DOC_NM_PSP_PRESCRIBING` | `APPRVD_DOC_NM.isin("Kerendia Patient Support Program iRep Email", "Kerendia Prescribing Information Email")` |
| `IREP_APPRVD_DOC_NM_BRANDED_ASSET` | `APPRVD_DOC_NM.isin("Kerendia Branded Asset Share Email")` |
| `IREP_APPRVD_DOC_NM_NATIONAL_BROADCAST` | `APPRVD_DOC_NM.isin("Kerendia National Broadcast Email")` |
| `IREP_APPRVD_DOC_NM_KIDNEY` | `APPRVD_DOC_NM.isin("Kerendia CKD Screening iRep Email", "Kerendia Kidney Profile iRep Email")` |
| `IREP_APPRVD_DOC_NM_INVITE` | `APPRVD_DOC_NM.isin("Kerendia Meeting Invite Email", "Kerendia Remote Meeting Engage or Zoom Invitation")` |
| `IREP_APPRVD_DOC_NM_EDUCATION` | `APPRVD_DOC_NM.isin("Kerendia NACE Educational Event iRep Email", "Kerendia Virtual Educational Event iRep Email")` |
| `IREP_APPRVD_DOC_NM_BACC_ACCESS` | `APPRVD_DOC_NM.isin("BACC - Kerendia - Commercial Access_12.21", "BACC - Kerendia - Medicare Access", "BACC - Kerendia - Medicare Access_12.21", "Kerendia - Commercial Access", "Kerendia - Commercial Access Update")` |
| `IREP_APPRVD_DOC_NM_EXCLUSIVE_BROADCAST` | `APPRVD_DOC_NM.isin("Kerendia Neph Exclusive Broadcast Email 1")` |
| `IREP_APPRVD_DOC_NM_TRIAL` | `APPRVD_DOC_NM.isin("Kerendia Free Trial Conversion iRep Email")` |
| `IREP_APPRVD_DOC_NM_MISCELLANEOUS` | `APPRVD_DOC_NM.isin("Kerendia Speaker Program Thank You iRep Email", "MAC-FINE-US-0036-1 Adding Kerendia to Preference List for Epic", "MAC-FINE-US-0052-1 iRep Adding Kerendia to Favorite List for Cerner")` |

**Note on zero-variance categories:** Several doc-name categories (FDA, PSP_PRESCRIBING,
BRANDED_ASSET, NATIONAL_BROADCAST) show all-zero values in current data. These are
historical/inactive categories that may repopulate with future data. They are present but may
be zero. Zero-variance filtering is a model-training concern, not handled in feature
engineering.

### Aggregation

Base features: 3 (delivery) + 11 (doc categories) = **14 base features**
After 6 rolling windows: 14 × 6 = **84 lag features** + `HCP_COHORT_ID` + `SVC_DT` = **86 columns**

### Output Column Naming

`TOTAL_{FLAG}_IN_LAST_{N}_MONTH`

Examples:
- `TOTAL_IREP_EMAILS_DELIVERED_IN_LAST_1_MONTH`
- `TOTAL_IREP_EMAILS_CLICKED_IN_LAST_3_MONTH`
- `TOTAL_IREP_APPRVD_DOC_NM_KIDNEY_IN_LAST_6_MONTH`

### Output Path

```
.../notebook_output/kerendia_nba_3_hcp_model_irep_features.parquet
```

---

## 6. Channel: ClickStream/CLM

### What It Measures

Duration and intensity of Closed-Loop Marketing content presented to HCPs during sales rep
calls. Captures how long reps spend showing Kerendia content and how long the presentation
lasts per call.

### Two-Source Join Pattern

ClickStream requires joining two sources:

1. **Calls** (`CPH_DB_PROD.MODEL_V2.FACT_CALL` + `MAP_CUSTOMER_XREF`): provides `CALL_ID`
   and `CALL_STATUS` filter. **Note:** BHID is loaded from the calls join but then
   **dropped** (`df_calls_raw = df_calls_raw.drop('BHID')`) — the BHID used in the final
   output comes from the ClickStream table.
2. **ClickStream** (`CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM`): provides `CALL_ID`,
   `BHID` (via `BAYER_HCP_ID`), `DATE_ID`, `USAGE_DUR`, `PRESN_DUR`

### Exact Source Queries

**Calls query:**
```sql
SELECT DISTINCT BAYER_CUST_ID AS BHID, CALL_ID, A.STAT AS CALL_STATUS
FROM (SELECT * FROM CPH_DB_PROD.MODEL_V2.FACT_CALL) A
LEFT JOIN (SELECT source_cust_id, bayer_cust_id
           FROM CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF) B
  ON A.SOURCE_CUST_ID = B.SOURCE_CUST_ID
WHERE UPPER(STAT) = 'SUBMITTED_VOD'
  AND UPPER(DETL_PROD) = 'KERENDIA'
  AND BAYER_CUST_ID NOT LIKE '%BHO%'
  AND BAYER_CUST_ID IS NOT NULL
```
Then: `df_calls_raw = df_calls_raw.drop('BHID')` — keeps only `CALL_ID`, `CALL_STATUS`.

**ClickStream query:**
```sql
SELECT DISTINCT CALL_ID,
       BAYER_HCP_ID AS BHID,
       DATE_ID,
       USAGE_DUR,
       PRESN_DUR
FROM CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM
WHERE BAYER_PROD_NM = 'KERENDIA'
  AND date_id <= {LOOKBACK_END_DATE_YYYYMMDD}
```
**Note:** `LOOKBACK_END_DATE` must be formatted as `yyyyMMdd` integer for the `date_id`
filter (e.g., `20250917`).

### Deduplication

Before joining, ClickStream records are deduplicated per `CALL_ID`:

```python
w = Window.partitionBy('CALL_ID').orderBy(
    col('USAGE_DUR').desc(), col('PRESN_DUR').desc()
)
click_stream_df = click_stream_data.select(
    '*', row_number().over(w).alias('row_number')
).filter('row_number = 1').drop('row_number')
```

This keeps the record with the highest usage/presentation duration per call. The deduped
clickstream is then inner-joined to calls:

```python
click_stream_call = click_stream_df.join(df_calls_raw, on='CALL_ID', how='inner')
```

**Silent drop behavior:** ClickStream events without a matching `FACT_CALL` record are
intentionally dropped by the inner join. Events that can't be attributed to a specific
submitted call are excluded by design.

### Metric Definitions (4 base features)

| Feature | Formula | Meaning |
| --- | --- | --- |
| `TOTAL_USAGE_DURATION` | `SUM(MAX_USAGE_DUR)` | Total content viewing time across calls |
| `TOTAL_PRESN_DURATION` | `SUM(MAX_PRESN_DUR)` | Total presentation time across calls |
| `AVG_USAGE_DURATION` | `AVG(MAX_USAGE_DUR)` | Average content viewing time per call |
| `AVG_PRESN_DURATION` | `AVG(MAX_PRESN_DUR)` | Average presentation time per call |

### Column Prefix

All output columns are prefixed with `CLICKSTREAM_`:

```python
df = df.select("HCP_COHORT_ID", "SVC_DT",
    *[F.col(c).alias("CLICKSTREAM_" + c)
      for c in df.columns if c not in ['HCP_COHORT_ID', 'SVC_DT', 'LOOKBACK_END_DATE']])
```

### Output

Base features: 4 → After 6 rolling windows: 4 × 6 = **24 lag features** +
`HCP_COHORT_ID` + `SVC_DT` = **26 columns**

### Output Column Naming

`CLICKSTREAM_{METRIC}_IN_LAST_{N}_MONTH`

Examples:
- `CLICKSTREAM_TOTAL_USAGE_DURATION_IN_LAST_1_MONTH`
- `CLICKSTREAM_AVG_PRESN_DURATION_IN_LAST_6_MONTH`

### Output Path

```
.../notebook_output/kerendia_nba_3_hcp_model_clickstream_features.parquet
```

---

## 7. Performance Guidance

### 7.1 No `.cache()` on Serverless

All promotional notebooks run on serverless compute. Do not use `.cache()` or
`.persist()` — serverless does not support persistent in-memory caching. Write
intermediates to Parquet instead.

### 7.2 Day-Level Spine Expansion Memory

The `step2_fill_missing_dates` function creates ~395 rows per HCP-cohort (one per day in
the 13-month lookback). With 26 cohorts and 130K HCPs:

- Calls: 130K × 26 × 395 ≈ **1.3B rows** in the dense spine
- ClickStream: 19K × 26 × 395 ≈ **195M rows**

Limit to necessary cohorts when running partial recomputation. The full spine is the primary
memory bottleneck.

### 7.3 Broadcast Joins

| Table | Typical Size | Strategy |
| --- | --- | --- |
| Cohort anchor dates | ~26 rows | **Always broadcast** |
| NPI-to-BHID mapping | ~1M rows | Broadcast if < 10MB |
| `MAP_CUSTOMER_XREF` | ~1M rows | Broadcast if < 10MB |
| Calls × ClickStream | >1M rows | Shuffle join (never broadcast) |

### 7.4 Column Sanitization

Calls notebook generates column names from raw `CHNNL_NM` and `CALL_TYP_CD` values that
can contain spaces. The pipeline replaces spaces with underscores and uppercases everything.
When writing to Delta, ensure all column names are sanitized:

```python
import re
def sanitize_column_name(name):
    name = re.sub(r'[^A-Za-z0-9_]', '_', name.replace("+", "AND").replace("/", "_OR_"))
    name = re.sub(r'_+', '_', name).strip('_')
    return name.upper()
```

### 7.5 `F.count(F.lit(1))` Instead of `F.count("*")`

In pivot aggregations, use `F.count(F.lit(1))` rather than `F.count("*")`. The latter can
fail or produce unexpected results in some Spark versions when used inside a pivot context.

### 7.6 `overwriteSchema` for Evolving Pivots

When new call types or doc-name categories appear in source data, the pivot produces new
columns. Use `.option("overwriteSchema", "true")` on Delta writes to handle schema
evolution:

```python
df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(path)
```

---

## 8. Cross-Channel Parameterization

| Parameter | Calls | iRep Emails | ClickStream |
| --- | --- | --- | --- |
| Source table | `FACT_CALL` + `MAP_CUSTOMER_XREF` | `VIEW_RB_KERENDIA_IREP` | `ANLT_BASE_FACT_CLKSTRM` + `FACT_CALL` |
| Raw ID column | `BAYER_CUST_ID` | `ACCT_IDNTFR` | `BAYER_HCP_ID` |
| Raw date column | `CALL_DATE` | `EMAIL_SENT_DT` | `DATE_ID` (int yyyyMMdd) |
| Brand filter | `DETL_PROD = 'KERENDIA'` | `EMAILPRODUCTTYPE LIKE '%KERENDIA%'` | `BAYER_PROD_NM = 'KERENDIA'` |
| Status filter | `STAT = 'SUBMITTED_VOD'` | `Email_Status = 'Delivered'` | (via FACT_CALL join) |
| Pivot dimensions | Channel × Call Type × Purpose (+ cross-products) | Delivery status × Doc name category | None (4 fixed metrics) |
| Base feature count | 35 | 14 | 4 |
| Rolling windows | `[30, 60, 90, 120, 150, 180]` days | `[30, 60, 90, 120, 150, 180]` days | `[30, 60, 90, 120, 150, 180]` days |
| Output feature count | 212 | 86 | 26 |
| Column prefix | None (TOTAL_) | None (TOTAL_IREP_) | `CLICKSTREAM_` |

**Prefix convention:** Channels that could collide with identically named columns from other
channels receive a prefix. `CLICKSTREAM_` distinguishes ClickStream duration features from
potential Calls duration features. Calls and iRep feature names are already unique
(`TOTAL_F2F_...`, `TOTAL_IREP_EMAIL_...`) and need no additional prefix.
| Dedup required | No | No | Yes (`row_number()` per CALL_ID) |
| Output path suffix | `call_features.parquet` | `irep_features.parquet` | `clickstream_features.parquet` |

---

## 9. Output Schema and Join Strategy

### 9.1 Join Key

All three channel outputs share the key `HCP_COHORT_ID`. In the combine notebook
(`99_Combine_Physician_Data_Promotional&Acc`), each is left-joined to the HCP universe
skeleton:

```python
hcp_universe_promotional = (
    hcp_universe_bhid
    .join(call_features, on=['HCP_COHORT_ID'], how='left')
    .join(irep_features, on=['HCP_COHORT_ID'], how='left')
    .join(clickstream_features, on=['HCP_COHORT_ID'], how='left')
)
```

Before joining, `BHID` and `SVC_DT` columns are dropped from each feature DataFrame
(keeping only `HCP_COHORT_ID` + feature columns) to avoid column-name collisions.

### 9.2 Final Output Columns

```
HCP_COHORT_ID                                          -- composite key

-- Calls (212 cols)
TOTAL_F2F_IN_LAST_{1..6}_MONTH                         -- channel type × 6 windows
TOTAL_PHONE_IN_LAST_{1..6}_MONTH
TOTAL_GROUP_CALL_IN_LAST_{1..6}_MONTH
TOTAL_REMOTE_CALL_IN_LAST_{1..6}_MONTH
TOTAL_{CALL_TYPE}_IN_LAST_{1..6}_MONTH                  -- 5 call types × 6
TOTAL_CALL_PURPOSE_{PURPOSE}_IN_LAST_{1..6}_MONTH       -- 5 purposes × 6
TOTAL_CALL_DURATION_IN_LAST_{1..6}_MONTH                -- duration × 6
TOTAL_{CHANNEL}_AND_{CALL_TYPE}_IN_LAST_{1..6}_MONTH    -- 20 cross-products × 6

-- iRep (86 cols)
TOTAL_IREP_EMAILS_{STATUS}_IN_LAST_{1..6}_MONTH        -- 3 statuses × 6
TOTAL_IREP_APPRVD_DOC_NM_{CATEGORY}_IN_LAST_{1..6}_MONTH -- 11 categories × 6

-- ClickStream (26 cols)
CLICKSTREAM_TOTAL_USAGE_DURATION_IN_LAST_{1..6}_MONTH
CLICKSTREAM_TOTAL_PRESN_DURATION_IN_LAST_{1..6}_MONTH
CLICKSTREAM_AVG_USAGE_DURATION_IN_LAST_{1..6}_MONTH
CLICKSTREAM_AVG_PRESN_DURATION_IN_LAST_{1..6}_MONTH
```

**Total personal promotional features: ~324 columns**
