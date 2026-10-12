# Non-Personal Promotional Features

Consolidated reference for **non-personal promotional** feature engineering in the Kerendia
NBA 3.x pipeline. Non-personal promotions are channels where HCPs are reached without direct
rep interaction — digital ads, mass emails, direct-to-consumer campaigns, drug samples,
speaker programs, and free trial programs. Seven channels are covered, spanning three
distinct pipeline architectures: day-level spine (5 channels), month-level spine (Digital),
and raw aggregation with no rolling windows (DTC).

---

## 0. Shared Infrastructure

See `personal-promotional-features/SKILL.md` Section 0 for the full shared infrastructure
reference. The same patterns apply here:

- **Get_Data_Snowflakes:** Defined in Section 0.2 of the personal skill. Uses
  `net.snowflake.spark.snowflake` format with PEM key-pair auth from Databricks secrets
  scope `US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`.
- **Digital uses a different connection config** (`sfOptionscdpread`): schema `PHCDW_DSAA`,
  warehouse `PROD_DATA_SCIENCE_CYRUS_WH` (vs the standard `PHCDW_CDM` / `PROD_CYRUS_BI_WH`).
- **Self-contained notebooks:** Each generated notebook defines utility functions inline
  (no `%run` dependencies, no `dbutils.widgets`).
- **Sanitize function:** Canonical version in personal skill Section 0.3.
- **Output format:** Parquet by default; Delta only for Digital (notebook 24) due to
  `overwriteSchema` needs from evolving pivots.

### 0.1 Running Total Convention

The `step3_lag` helper (from `00_step23_function`) computes **both** lag features **and**
running totals in a single pass:

```python
def step3_lag(df, key_col, date_col, last_i_month_list):
    window_base = Window.partitionBy(key_col).orderBy(date_col)
    features = [col for col in df.columns if col not in [key_col, date_col]]
    last_i_month = [
        F.sum(col).over(window_base.rowsBetween(-i + 1, 0))
        .alias(f"{col}_IN_LAST_{i}_MONTH")
        for i in last_i_month_list for col in features
    ]
    running_total = [
        F.sum(col).over(
            window_base.rowsBetween(Window.unboundedPreceding, Window.currentRow)
        ).alias(f"RUNNING_{col}")
        for col in features
    ]
    return df.select("*", *last_i_month, *running_total)
```

**Key:** `RUNNING_TOTAL` uses `Window.unboundedPreceding` to `Window.currentRow` — it is
a true cumulative sum from the earliest data, computed **before** the anchor-date filter.
After filtering to `MONTH_ID == LOOKBACK_END_DATE`, the running total reflects the
cumulative count up to the anchor date.

---

## 1. Channel Inventory

| # | Channel | Notebook | Source System | Output Rows | Feature Count | Distinct Entities | Sparsity | Grain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Digital Engagement | `24_Features_Digital` | `PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB` | 17,296,750 | 665 | 402,250 | 99.1% | HCP (NPI) |
| 2 | HQ Emails | `15_promotional_features_HQ_Emails` | `PHCDW.PHCDW_CDM.HCP_EMAIL_LIST` | 2,476,618 | 32 | 190,860 | 76.9% | HCP (BHID) |
| 3 | DTC Direct Buy | `34_promotional_features_DTC` (Direct Buy cells) | Parquet (Healthline, HealthUnion, ShareCare, WebMD) | 7,052 | 8 | DMA-level | 36.9% | DMA |
| 4 | Meta/Instagram Ads | `34_promotional_features_DTC` (Social cells) | Parquet (`kerendia_nba_3_0_hcp_model_social.parquet`) | (part of 7,052) | 2 | DMA-level | 36.9% | DMA |
| 5 | Samples | `17_promotional_features_samples` | `PHCDW.PHCDW_DSAA.VIEW_KERENDIA_SAMPLES_DROPPED_SHIPPED` | 519,959 | 56 | 35,546 | 84.1% | HCP (NPI→BHID) |
| 6 | Speaker Programs | `14_promotional_features_speaker_program` | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM` | 156,677 | 68 | 17,151 | 96.9% | HCP (BHID) |
| 7 | Free Trial Program | `19_ftp_features` | `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP` | 718,520 | 9 | NPI→BHID | 80.7% | HCP (NPI→BHID) |

**Null/zero convention:** All channels use `fillna(0)` — zeros, not nulls, for missing
promotional activity. Downstream models interpret 0 as "HCP was not promoted via this channel."

---

## 2. Pipeline Architectures

Non-personal channels use three distinct pipeline variants:

### Variant A: Day-Level Spine (HQ Emails, Samples, Speaker Programs, FTP)

Identical to the personal-channel pipeline. See `personal-promotional-features/SKILL.md`
Sections 2 for the full `step2_fill_missing_dates` / `step3_lag_date` implementations.

- **Spine grain:** Daily (one row per day in lookback)
- **Rolling windows:** `[30, 60, 90, 120, 150, 180]` days → `_IN_LAST_{1..6}_MONTH`
- **Join key:** `HCP_COHORT_ID = {BHID}_{COHORT}`

### Variant B: Month-Level Spine (Digital Engagement)

Digital data is available only at monthly granularity. Uses different fill/lag functions:

```python
def step2_fill_missing(df, key_col="NPI_NUMBER", date_col="SVC_DT_M"):
    """
    Creates a dense monthly spine per HCP using sequence(min, max, interval 1 month).
    Unlike day-level variant, expands one row per calendar month (not per day).
    """
    date_range = df.select(F.min(date_col), F.max(date_col)).first()
    all_months = spark.range(1).select(
        F.explode(F.expr(f"sequence('{date_range[0]}', '{date_range[1]}', interval 1 month)")).alias(date_col)
    )
    distinct_keys = df.select(key_col).distinct()
    spine = distinct_keys.crossJoin(all_months)
    return spine.join(df, on=[key_col, date_col], how="left").fillna(0)

def step3_lag(df, key_col, date_col, last_i_month_list=[1, 3, 6]):
    window_base = Window.partitionBy(key_col).orderBy(date_col)
    features = [c for c in df.columns if c not in [key_col, date_col]]
    lag_cols = [
        F.sum(col).over(window_base.rowsBetween(-i+1, 0))
         .alias(f"{col}_IN_LAST_{i}_MONTH")
        for i in last_i_month_list for col in features
    ]
    return df.select("*", *lag_cols)
```

**Key difference from day-level:** Rolling windows are `[1, 3, 6]` months (not 6 windows
from 1-6). This is intentional — Digital/MMX data is only available monthly, so 30-day
day-level windows are meaningless. The `_IN_LAST_1_MONTH` label looks identical to the
day-level variant but has different semantics: 1 calendar month vs 30 calendar days.

### Variant C: No Rolling Windows (DTC Direct Buy, Meta/Instagram Ads)

DTC features are raw monthly aggregates with no rolling-window pipeline applied. This is
intentional — DTC is used as a contemporaneous market-pressure feature, not a lookback.
Features capture the current month's advertising spend/reach in the HCP's geographic area.

- **Spine grain:** Monthly (`DATA_MONTH`)
- **Rolling windows:** None
- **Join key:** `DMA_Code` + `SVC_DT_M` (geographic, not HCP-level)

---

## 3. Cohort Anchor Dates

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

Used by HQ Emails, Samples, Speaker Programs, and FTP. Digital and DTC use different
time-alignment patterns (see respective channel sections).

### NPI-to-BHID Crosswalk

Used by Samples and FTP (which start with NPI from their source systems):
```
/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/
  hcp_level_features/query_output/kerendia_nba_3_0_npi_bhid_mapping.parquet
```

---

## 4. Channel: Digital Engagement

### What It Measures

Multi-channel digital engagement from Marketing Mix Modeling (MMX). Captures HCP exposure
and engagement across paid media channels (banner, display, email, social, EHR, CTV, etc.).

### Source Query

Digital uses the `sfOptionscdpread` connection instead of `Get_Data_Snowflakes`.
This config differs in schema (`PHCDW_DSAA`), warehouse (`PROD_DATA_SCIENCE_CYRUS_WH`),
and adds `sfTracing`:

```python
sfOptionscdpread = {
    "sfURL": "bayer_cphcdp_prod.us-east-1.snowflakecomputing.com:443",
    "sfUser": snowflake_user,
    "pem_private_key": snowflake_pem_private_key,
    "sfRole": "BAY_CPH_CDP_PROD_CR_US_EAST_1_MVXPF_MVXPF",
    "sfSchema": "PHCDW_DSAA",
    "sfDatabase": "PHCDW",
    "sfWarehouse": "PROD_DATA_SCIENCE_CYRUS_WH",
    "purge": "off",
    "autopushdown": "on",
    "sfTracing": "on"
}
SNOWFLAKE_SOURCE_NAME = "net.snowflake.spark.snowflake"
```

Usage pattern (replaces `Get_Data_Snowflakes()` for this notebook only):
```python
df = spark.read.format(SNOWFLAKE_SOURCE_NAME).options(**sfOptionscdpread).option("query", query).load()
```

The auth variables (`snowflake_user`, `snowflake_pem_private_key`) are set up identically to
`Get_Data_Snowflakes` — see personal skill Section 0.2 for the full auth setup block.

```sql
SELECT NPI_NUMBER, SVC_DT_M,
       UPPER(CHANNEL) AS CHANNEL,
       UPPER(SRC_SYS_CD) AS SRC_SYS_CD,
       TACTIC_NAME,
       SUM(DEEP_ENGAGEMENT)  AS DEEP_ENGAGEMENT,
       SUM(LIGHT_ENGAGEMENT) AS LIGHT_ENGAGEMENT,
       SUM(TOTAL_ENGAGEMENT) AS TOTAL_ENGAGEMENT,
       SUM(EXPOSURE)         AS EXPOSURE
FROM (
    SELECT NPI_NUM AS NPI_NUMBER,
           DATE_ACT,
           DATE_TRUNC('MONTH', DATE_ACT) AS SVC_DT_M,
           CHANNEL, SRC_SYS_CD, TACTIC_NAME, BRND_NM,
           DEEP_ENGAGEMENT, LIGHT_ENGAGEMENT, TOTAL_ENGAGEMENT, EXPOSURE
    FROM PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB
    WHERE UPPER(BRND_NM) = 'KERENDIA'
      AND NPI_NUM IS NOT NULL
      AND DATE_TRUNC('MONTH', DATE_ACT) >= '{digital_start}'
)
GROUP BY NPI_NUMBER, SVC_DT_M, CHANNEL, SRC_SYS_CD, TACTIC_NAME
ORDER BY NPI_NUMBER, SVC_DT_M DESC, CHANNEL, SRC_SYS_CD, TACTIC_NAME
```

**Key details:**
- Source column is `NPI_NUM`, aliased to `NPI_NUMBER` (NOT BHID — the skill previously
  listed BHID incorrectly).
- `CHANNEL` and `SRC_SYS_CD` are uppercased in the query.
- Pre-aggregation happens at the Snowflake level (GROUP BY).
- `digital_start` = `LOOKBACK_START_DATE` from the inference cohort anchor dates.

### Triple-Pivot Architecture

Digital features are generated via three independent pivots, each producing a wide DataFrame:

**Pivot 1 — By Channel (22 distinct values):**

| Example Channels | Metric per Channel |
| --- | --- |
| BANNER, BRAND_ALERT, CTV, DOCNEWS, DOCSPOT, EHR, EMAIL, FORMULARY, IMPIRICUS, LINKEDIN, NATIVEVIDEO, PAID_SEARCH, PROGRAMMATIC_DISPLAY, SOCIAL, VIDEO | DEEP_ENGAGEMENT, LIGHT_ENGAGEMENT, TOTAL_ENGAGEMENT, EXPOSURE |

Columns: 22 channels × 4 metrics = **88 base features**

**Pivot 2 — By SRC_SYS_CD (70 distinct values):**

Systems like Doximity, Healio, WebMD, Impiricus, etc. × 4 metrics = **280 base features**

**Pivot 3 — By TACTIC_NAME (58 distinct values):**

Tactics like DocSpot, Brand Alert, CTV Household, Formulary, Native Video, etc. × 4 metrics = **232 base features**

Each pivot is aggregated independently with `groupBy(NPI_NUMBER, SVC_DT_M)` before pivoting,
then all three are joined together on `[NPI_NUMBER, SVC_DT_M]`.

### Month-Level Lag Windows

After pivot+join, the combined DataFrame goes through `step2_fill_missing` (monthly spine)
and `step3_lag` with `last_i_month_list = [1, 3, 6]`:

- Each of ~600 base features × 3 windows = **~1800 lag features** → pruned to ~665 after
  dropping zero-variance columns

### Column Prefix

All output columns are prefixed with `DIGITAL_`:

```python
for col in df.columns:
    if col not in ['NPI_NUMBER', 'SVC_DT_M']:
        df = df.withColumnRenamed(col, f"DIGITAL_{col}")
```

### Column Sanitization

MMX channel/tactic names can contain hyphens, slashes, and plus signs:
- `HAYMARKET-DISPLAY` → `HAYMARKET_DISPLAY`
- `FB+IG` → `FB_AND_IG`
- Forward slashes → `_OR_`

```python
import re
def sanitize(name):
    name = name.replace("+", "_AND_").replace("/", "_OR_")
    name = re.sub(r'[^A-Za-z0-9_]', '_', name)
    return re.sub(r'_+', '_', name).strip('_').upper()
```

### Output Key and Path

- **Key:** `NPI_NUMBER` + `SVC_DT_M` (NOT BHID — Digital stays at NPI grain)
- **Downstream join:** NPI is mapped to PROVIDER_ID via
  `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRVDR` in the combine notebook

```
.../notebook_output/kerendia_nba_3_0_hcp_model_paid_search_features.parquet
```

**665 output columns** (highest dimensionality of any promotional channel)

---

## 5. Channel: HQ Emails

### What It Measures

Frequency of HQ-triggered mass email campaigns to HCPs, decomposed by email event type.
No rep involvement — these are centrally orchestrated marketing emails.

### Source Query

```sql
SELECT BHID, EVENTDATE, EVENTTYPE
FROM PHCDW.PHCDW_CDM.HCP_EMAIL_LIST
WHERE UPPER(EMAILPRODUCTTYPE) LIKE '%KERENDIA%'
```

### Binary Flag Definitions (5 event types)

| Flag | Condition | Meaning |
| --- | --- | --- |
| `TOTAL_BOUNCE` | `EVENTTYPE == 'Bounce'` | Email bounced |
| `TOTAL_CLICK` | `EVENTTYPE == 'Click'` | Recipient clicked a link |
| `TOTAL_OPEN` | `EVENTTYPE == 'Open'` | Recipient opened email |
| `TOTAL_SENT` | `EVENTTYPE == 'Sent'` | Email was sent to HCP |
| `TOTAL_UNSUBSCRIBE` | `EVENTTYPE == 'Unsubscribe'` | HCP unsubscribed |

### Pipeline

Uses Variant A (day-level spine):
- Cross-join with cohort anchor dates
- `step2_fill_missing_dates` → daily spine
- `step3_lag_date` with `[30, 60, 90, 120, 150, 180]` day windows
- Filter to `MONTH_ID == LOOKBACK_END_DATE`

### Output

5 base features × 6 windows = **30 lag features** + `HCP_COHORT_ID` + `SVC_DT` = **32 columns**

**Note:** HQ Emails retains `LOOKBACK_END_DATE` in its output, unlike other channels which
drop it. This can cause schema issues in the combine step — the combine notebook explicitly
drops it: `hq_email_features = hq_email_features.drop("BHID", "SVC_DT", "LOOKBACK_END_DATE")`.

### Output Column Naming

`TOTAL_{EVENTTYPE}_IN_LAST_{N}_MONTH`

Examples:
- `TOTAL_BOUNCE_IN_LAST_1_MONTH`
- `TOTAL_CLICK_IN_LAST_3_MONTH`
- `TOTAL_UNSUBSCRIBE_IN_LAST_6_MONTH`

### Output Path

```
.../notebook_output/kerendia_nba_3_hcp_model_hq_email_features.parquet
```

---

## 6. Channel: DTC Direct Buy

### What It Measures

Direct-to-consumer advertising impressions and clicks from publisher direct-buy campaigns,
aggregated at the **DMA (Designated Market Area) geographic level**, not HCP level.

### Source Data

A single consolidated Delta table containing all four vendors:

```python
df_db = spark.read.format("delta").load(
    "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/"
    "kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/"
    "kerendia_nba_3_0_hcp_model_DirectBuys"
)
```

| Column | Type | Description |
| --- | --- | --- |
| `DMA_Code` | string | Designated Market Area code |
| `MONTH` | date | Calendar month (renamed to `DATA_MONTH` after loading) |
| `VENDOR` | string | Vendor name |
| `IMPRESSIONS` | numeric | Ad impressions |
| `CLICKS` | numeric | Ad clicks |

**Vendors in data:** `"Health Union"`, `"Sharecare"`, `"Healthline"`, `"WebMD"`

### Pivot Structure

Data is pivoted by vendor name, producing two metrics per vendor:

| Feature | Formula |
| --- | --- |
| `DTC_PROMOTION_{VENDOR}_TOTAL_IMPRESSIONS` | `SUM(IMPRESSIONS)` per DMA × month |
| `DTC_PROMOTION_{VENDOR}_TOTAL_CLICKS` | `SUM(CLICKS)` per DMA × month |

**DTC column sanitization** uses a vendor-specific pattern (different from the canonical
sanitize function):
```python
c.replace(", ", " ").replace("+", "and").replace("/", " or ")
 .replace("-", "_").replace(" ", "_").replace("__", "_")
 .replace("(", "").replace(")", "").replace("&", "").upper()
```

Vendors: Healthline, HealthUnion, ShareCare, WebMD → 4 vendors × 2 metrics = **8 features**

### No Rolling Windows

DTC Direct Buy does **not** use rolling windows. Features are raw monthly aggregates. This
is intentional — DTC is used as a contemporaneous market-pressure feature (how much
advertising is this HCP's geographic area receiving this month), not a lookback feature.

### Output Key

- `DMA_Code` (geographic) + `DATA_MONTH` (monthly)
- **NOT** HCP-level — joined to HCP downstream

### Unexecuted Cells (TBD)

Notebook 34 contains cells for **PulsePoint Programmatic Display** and **TTD Display**
that have never been executed (`state=input`). It is unclear whether these vendors will be
added to the output in a future iteration. If activated, they would add 2 vendors × 2
metrics = 4 more features.

### Output Path

```
.../notebook_output/kerendia_nba_3_hcp_model_DTC_PROMOTION.parquet
```

---

## 7. Channel: Meta/Instagram Ads

### What It Measures

Impressions and clicks from Meta (Facebook + Instagram) social media advertising campaigns,
aggregated at the **DMA geographic level**.

### Source Data

Loaded from a pre-aggregated Delta table:
```python
df_social = spark.read.format("delta").load(
    "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/"
    "kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/"
    "kerendia_nba_3_0_hcp_model_social"
)
```
Same schema as Direct Buy: `DMA_Code`, `MONTH`, `VENDOR` (`"FB+IG"`), `IMPRESSIONS`, `CLICKS`.

### Features (2 columns)

| Feature | Formula |
| --- | --- |
| `DTC_PROMOTION_FB_AND_IG_TOTAL_IMPRESSIONS` | `SUM(Impressions)` per DMA × month |
| `DTC_PROMOTION_FB_AND_IG_TOTAL_CLICKS` | `SUM(Clicks)` per DMA × month |

### Pipeline

Same as DTC Direct Buy — no rolling windows, raw monthly aggregates. The Social data is
merged into the same DTC output DataFrame before writing.

### Output

Merged into the DTC Direct Buy output file (same parquet file). The combined DTC+Social
output has 10 features: 8 Direct Buy + 2 Meta/IG = **10 total features**.

---

## 8. Channel: Samples

### What It Measures

Frequency and type of drug sample distribution to HCPs, including dosage variants and
delivery status (hand-delivered vs mailed).

### Source Query

```sql
SELECT NPI_NUMBER, SAMPLE_DATE, SAMPLE_FLAG, SAMPLE_NAME
FROM PHCDW.PHCDW_DSAA.VIEW_KERENDIA_SAMPLES_DROPPED_SHIPPED
```

### ID Resolution

Samples uses NPI_NUMBER in the source. Mapped to BHID via the NPI-to-BHID crosswalk
parquet before cross-joining with cohort dates.

### Binary Flag Definitions

**Delivery Status (2 flags):**

| Flag | Condition | Meaning |
| --- | --- | --- |
| `SAMPLE_DROPPED` | `SAMPLE_FLAG == 'DROPPED'` | Sample hand-delivered by rep |
| `SAMPLE_SHIPPED` | `SAMPLE_FLAG == 'SHIPPED'` | Sample mailed to HCP |

Both states exist and represent an operational distinction (hand-delivery vs mailed). Both
are counted in `TOTAL_OVERALL_SAMPLE`.

**Sample Name Categories (7 flags + 1 aggregate):**

| Flag | Condition |
| --- | --- |
| `TOTAL_SAMPLE_KERENDIA_20MG` | `SAMPLE_NAME == 'KERENDIA 20MG'` |
| `TOTAL_SAMPLE_KERENDIA_10MG` | `SAMPLE_NAME == 'KERENDIA 10MG'` |
| `TOTAL_SAMPLE_KERENDIA_10MG_BRC` | `SAMPLE_NAME == 'KERENDIA 10MG BRC'` |
| `TOTAL_SAMPLE_KERENDIA_20MG_BRC` | `SAMPLE_NAME == 'KERENDIA 20MG BRC'` |
| `TOTAL_SAMPLE_KERENDIA_SAMPLING_KIT_BRC` | `SAMPLE_NAME == 'KERENDIA SAMPLING KIT BRC'` |
| `TOTAL_SAMPLE_KERENDIA_SAMPLE_HOUSING_BOX_BRC` | `SAMPLE_NAME == 'KERENDIA SAMPLE HOUSING BOX BRC'` |
| `TOTAL_OVERALL_SAMPLE` | Count of all samples (any name) |

**Excluded:** `KERENDIA PATIENT BROCHURES BRC` is explicitly excluded from sample counts.

### Pipeline

Uses Variant A (day-level spine) with `[30, 60, 90, 120, 150, 180]` day windows.

### Output

~9 base features × 6 windows = **54 lag features** + `HCP_COHORT_ID` + `SVC_DT` = **56 columns**

Max sample value observed: 290 (for a single HCP in a single window).

### Output Column Naming

`TOTAL_{SAMPLE_FLAG/NAME}_IN_LAST_{N}_MONTH`

### Output Path

```
.../notebook_output/kerendia_nba_3_hcp_model_samples_features.parquet
```

---

## 9. Channel: Speaker Programs

### What It Measures

HCP attendance at Kerendia speaker program events, decomposed by event format, event type,
and topic.

### Source Query

```sql
SELECT BAYER_HCP_ID AS BHID, EVNT_STRT_DT AS MONTH_ID,
       EVNT_FMT, EVNT_TYP, EVNT_TPIC_NM, ATND
FROM CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM
WHERE UPPER(ATND) = 'ATTENDED'
  AND UPPER(PROD_BRAND_NM) = 'KERENDIA'
  AND EVNT_STRT_DT BETWEEN '2022-03-17' AND '2025-04-16'
```

### Binary Flag Definitions

**Dimension 1 — Event Format (4 flags + 1 other):**

| Flag | Condition |
| --- | --- |
| `SPKR_EVNT_FMT_F2F` | `EVNT_FMT == 'Face-to-Face'` |
| `SPKR_EVNT_FMT_REMOTE` | `EVNT_FMT == 'Remote'` |
| `SPKR_EVNT_FMT_HYBRID` | `EVNT_FMT == 'Hybrid'` |
| `SPKR_EVNT_FMT_IN_OFFC_MEAL` | `EVNT_FMT == 'In-Office Meal'` |
| `SPKR_EVNT_FMT_OTHER` | `EVNT_TPIC_NM.isNull()` (rows where topic is null) |

**Dimension 2 — Event Type (2 flags):**

| Flag | Condition |
| --- | --- |
| `SPKR_EVNT_TYP_SPKR_PRGM` | `EVNT_TYP.isin("SPEAKER PROGRAMS")` |
| `SPKR_EVNT_TYP_NON_SPKR_PRGM` | `EVNT_TYP.isin("NON-SPEAKER PROGRAMS")` |

**Note:** Event type values are uppercase in the source data.

**Note on zero-variance features:** Both `SPKR_EVNT_TYP_SPKR_PRGM` and
`SPKR_EVNT_TYP_NON_SPKR_PRGM` show stddev=0, max=0 in the current output. These features
currently carry no signal. Zero-variance filtering is a model-training concern.

**Dimension 3 — Event Topic (4 flags):**

| Flag | Exact `EVNT_TPIC_NM.isin(...)` Values |
| --- | --- |
| `SPKR_TOPIC_CKD` | `"Recognizing The Gap Diagnosis and Treatment of CKD Associated with T2D PP-KER-US-02241"`, `"***Discover More About Kidney and Heart Outcomes with a Treatment for CKD Associated with T2D PP-KER-US-0225-1"`, `"Discover More About Kidney and Heart Outcomes with a Treatment for CKD Associated with T2D PP-KER-US-0225-1"` |
| `SPKR_TOPIC_CVR` | `"KERENDIA Cardiorenal Connection PP-KER-US-1038-1"`, `"KERENDIA Heart of the Matter PP-KER-US-0743-1"` |
| `SPKR_TOPIC_INTRO` | `"SHORT Introduction to KERENDIA CONDENSED (PP-FINE-US-0620-2)"`, `"Introduction to KERENDIA (PP-FINE-US-0626-4)"`, `"KERENDIA Recognizing The Gap PP-KER-US-1039-2"`, `"KERENDIA Exploring a Fundamental Pillar PP-KER-US-1455-1"`, `"Introduction to KERENDIA (PP-FINE-US-0626-3)"`, `"KERENDIA CONDENSED PP-KER-US-1340-1"`, `"SHORT Introduction to KERENDIA CONDENSED (PP-FINE-US-0620-1)"`, `"Kerendia Case Based Learning Program PP-KER-US-0044-1"`, `"***Kerendia Case Based Learning Program PP-KER-US-0044-1"`, `"KERENDIA Case Based Learning Program PP-KER-US-1040-1"` |
| `SPKR_TOPIC_OTHER` | `EVNT_TPIC_NM.isin("Display/Exhibit")` OR `EVNT_TPIC_NM.isNull()` |

**Note:** Topic flag names use `SPKR_TOPIC_` prefix (not `SPKR_EVNT_TPIC_`).
The matching uses exact `.isin()` — these are Veeva document PP-codes, not free text.

### Pipeline

Uses Variant A (day-level spine) with `[30, 60, 90, 120, 150, 180]` day windows.

### Output

~11 base features × 6 windows = **66 lag features** + `HCP_COHORT_ID` + `SVC_DT` = **68 columns**

### Output Column Naming

`TOTAL_{FLAG}_IN_LAST_{N}_MONTH`

Examples:
- `TOTAL_SPKR_EVNT_FMT_F2F_IN_LAST_1_MONTH`
- `TOTAL_SPKR_EVNT_TPIC_CKD_IN_LAST_6_MONTH`

### Output Path

```
.../notebook_output/kerendia_nba_3_hcp_model_speaker_program.parquet
```

---

## 10. Channel: Free Trial Program / FTP

### What It Measures

Patient copay/voucher redemptions (Free Trial Program) mapped back to prescribing HCPs.
Captures how many FTP prescriptions an HCP has written over rolling windows.

### Source Query

```sql
SELECT PROVIDER_ID, MONTH_ID, DAY_SUPPLY, ROW_COUNT, ORGN_CLM_AUTH_NUM
FROM PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP
WHERE USE_SLS = 'Y'
```

### Reversal Handling

FTP source data includes claim reversals. The pipeline identifies and removes them:

1. Group claims by `ORGN_CLM_AUTH_NUM`
2. Compute `SUM(DAY_SUPPLY)` and `SUM(ROW_COUNT)` per group
3. Remove claims where net `DAY_SUPPLY <= 0` or net `ROW_COUNT == 0`
4. This removes both the original claim and its reversal

```python
# Identify net-zero or net-negative claim groups (reversals)
reversal_groups = (
    df.groupBy("ORGN_CLM_AUTH_NUM")
    .agg(F.sum("DAY_SUPPLY").alias("NET_SUPPLY"),
         F.sum("ROW_COUNT").alias("NET_COUNT"))
    .filter((col("NET_SUPPLY") <= 0) | (col("NET_COUNT") == 0))
)
# Anti-join to remove reversed claims
df_clean = df.join(reversal_groups.select("ORGN_CLM_AUTH_NUM"),
                   on="ORGN_CLM_AUTH_NUM", how="left_anti")
```

### ID Resolution

FTP uses `NPI_NUMBER` (labeled `PROVIDER_ID` in source) as its native key. Mapped to BHID
via the NPI-to-BHID crosswalk parquet before cross-joining with cohort dates.

### Metric Definition (1 base feature)

| Feature | Formula |
| --- | --- |
| `TOTAL_RX_FTP` | `COUNT(1)` per HCP × day (count of valid voucher redemptions) |

After step3_lag_date: 1 base feature × 6 windows = **6 lag features**

Additionally, `RUNNING_TOTAL_RX_FTP` is computed as a true cumulative sum from the
earliest data to the current row using:
```python
F.sum("TOTAL_RX_FTP").over(
    Window.partitionBy("HCP_COHORT_ID")
    .orderBy("MONTH_ID")
    .rowsBetween(Window.unboundedPreceding, Window.currentRow)
).alias("RUNNING_TOTAL_RX_FTP")
```
This is computed in step3 alongside the lag features, **before** the anchor-date filter.
See Section 0.1 for the full `step3_lag` implementation.

### Pipeline

Uses Variant A (day-level spine) with `[30, 60, 90, 120, 150, 180]` day windows.

### Output

6 lag features + RUNNING_TOTAL + `HCP_COHORT_ID` + `PULL_DT` = **9 columns**

Date range: 2021-01-13 to 2025-07-18

**Why `PULL_DT` instead of `SVC_DT`:** FTP intentionally uses `PULL_DT` (pull date) as its
output date column instead of `SVC_DT` used by other Variant A channels. This reflects the
claim-pull semantics of the voucher data — the date column represents when the voucher
claim was pulled/processed, not a service date. The combine notebook handles this
distinction.

### Output Column Naming

`TOTAL_RX_FTP_IN_LAST_{N}_MONTH`

### Output Path

```
.../notebook_output/kerendia_nba_3_hcp_model_ftp_features.parquet
```

---

## 11. DTC-to-HCP Geographic Join (Downstream Contract)

DTC Direct Buy and Meta/Instagram Ads features exist at DMA geographic level. They are
joined to HCP-level data in the combine notebook
(`99_Combine_Physician_Data_Promotional&Acc`, notebook ID 3598883070773244) via a two-step
geographic mapping:

### Step 1: DMA → ZIP

A DMA-to-ZIP mapping is loaded from:
```
/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/
  hcp_level_features/notebook_output/DTC/DMA Zip Mapping.parquet
```

```python
dma_zip_mapping = spark.read.parquet("...DMA Zip Mapping.parquet")
dma_zip_mapping = dma_zip_mapping.select('ZIP Code', 'DMA Code') \
    .withColumnRenamed('ZIP Code', 'ZIP_CODE_GEO') \
    .withColumnRenamed('DMA Code', 'DMA_Code') \
    .dropDuplicates()

dtc_with_zip = dtc_features.join(dma_zip_mapping, on='DMA_Code', how='left')
```

### Step 2: ZIP → HCP

The HCP universe skeleton already has `ZIP_CODE_GEO` from geographic features. DTC is
joined on `[ZIP_CODE_GEO, SVC_DT_M]`:

```python
hcp_with_dtc = hcp_universe_promotional.join(
    dtc_with_zip, on=['ZIP_CODE_GEO', 'SVC_DT_M'], how='left'
)
```

**DTC `DATA_MONTH` must be renamed to `SVC_DT_M`** before joining:
```python
dtc_features = dtc_features.withColumnRenamed("DATA_MONTH", "SVC_DT_M")
```

### Required Columns for Downstream Join

| Column | Source | Description |
| --- | --- | --- |
| `DMA_Code` | DTC output | Designated Market Area code |
| `SVC_DT_M` | DTC output (renamed from `DATA_MONTH`) | Calendar month |
| `ZIP_CODE_GEO` | DMA Zip Mapping parquet | ZIP code |
| `ZIP_CODE_GEO` | HCP universe (from geo_features) | HCP's ZIP code |

**One-to-many:** One DMA maps to many ZIP codes. One ZIP may contain many HCPs. So the
same DTC feature values are broadcast to all HCPs within that DMA — this is by design
(market-level pressure applied equally to all HCPs in the area).

---

## 12. Performance Guidance

### 12.1 No `.cache()` on Serverless

All promotional notebooks run on serverless compute. Do not use `.cache()` or
`.persist()` — serverless does not support persistent in-memory caching.

### 12.2 Day-Level Spine Memory Impact

The `step2_fill_missing_dates` expansion creates ~395 rows per HCP-cohort. For the larger
non-personal channels:

- HQ Emails: 191K × 26 × 395 ≈ **1.96B rows** in dense spine
- Samples: 36K × 26 × 395 ≈ **370M rows**
- Speaker Programs: 17K × 26 × 395 ≈ **175M rows**

Limit to necessary cohorts when running partial recomputation.

### 12.3 Digital-Specific: Pivot Explosion

Digital's triple-pivot produces ~600 base columns from 22+70+58 pivot values × 4 metrics.
Each additional pivot value adds 4 × 3 = 12 lag columns. When new channels or tactics
appear in the MMX source:

- Monitor column count growth
- Use `.option("overwriteSchema", "true")` on Delta writes
- Consider applying an `event_prevalence` filter if column count becomes unmanageable

### 12.4 Broadcast Joins

| Table | Typical Size | Strategy |
| --- | --- | --- |
| Cohort anchor dates | ~26 rows | **Always broadcast** |
| NPI-to-BHID mapping | ~1M rows | Broadcast if < 10MB |
| DMA-to-ZIP mapping | ~42K rows | **Always broadcast** |
| NPI-to-PROVIDER_ID mapping | ~1M rows | Broadcast if < 10MB |

### 12.5 Column Sanitization

Digital channel/tactic names contain special characters:
- `HAYMARKET-DISPLAY` → `HAYMARKET_DISPLAY`
- `FB+IG` → `FB_AND_IG`

Use the sanitization function from Section 4 before any Delta write.

### 12.6 `F.count(F.lit(1))` Instead of `F.count("*")`

FTP already uses `F.count(F.lit(1))` for its `TOTAL_RX_FTP` aggregation. Use this pattern
consistently across all channels.

---

## 13. Cross-Channel Parameterization

| Parameter | Digital | HQ Emails | DTC Direct Buy | Meta/IG Ads | Samples | Speaker Programs | FTP |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Source | MMX_FNL_COMBINED_AGGR_TAB | HCP_EMAIL_LIST | Parquet (4 vendors) | Parquet (social) | VIEW_KERENDIA_SAMPLES | ANLT_BASE_FACT_EVNT_PRSNL_PROM | VIEW_RB_KERENDIA_VOUCHER_FTP |
| ID column | NPI_NUMBER | BHID | DMA_Code | DMA_Code | NPI→BHID | BHID | NPI→BHID |
| Pipeline variant | B (monthly) | A (day-level) | C (no windows) | C (no windows) | A (day-level) | A (day-level) | A (day-level) |
| Rolling windows | [1, 3, 6] months | [30-180] days | None | None | [30-180] days | [30-180] days | [30-180] days |
| Base features | ~600 | 5 | 8 | 2 | ~9 | ~11 | 1 |
| Output features | 665 | 32 | 8 | 2 | 56 | 68 | 9 |
| Column prefix | DIGITAL_ | None | DTC_PROMOTION_ | DTC_PROMOTION_ | None | None | None |
| Join key | NPI_NUMBER + SVC_DT_M | HCP_COHORT_ID | DMA_Code + SVC_DT_M | DMA_Code + SVC_DT_M | HCP_COHORT_ID | HCP_COHORT_ID | HCP_COHORT_ID |
| Output file | paid_search_features | hq_email_features | DTC_PROMOTION | DTC_PROMOTION | samples_features | speaker_program | ftp_features |

**Prefix convention:** Channels whose raw feature names could collide with other channels
receive a disambiguating prefix: `DIGITAL_` for MMX digital features, `DTC_PROMOTION_` for
DTC/Social features. HQ Emails, Samples, Speaker Programs, and FTP have naturally unique
feature names (`TOTAL_BOUNCE_...`, `TOTAL_SAMPLE_...`, `TOTAL_SPKR_...`, `TOTAL_RX_FTP_...`)
and need no prefix.

---

## 14. Output Schema and Join Strategy

### 14.1 Join Keys

Non-personal channels use three different join keys in the combine notebook:

| Key Type | Channels | Join Column(s) |
| --- | --- | --- |
| `HCP_COHORT_ID` | HQ Emails, Samples, Speaker Programs, FTP, ClickStream | `HCP_COHORT_ID` |
| `NPI → PROVIDER_ID` + month | Digital | `PROVIDER_ID` + `SVC_DT_M` (after NPI mapping) |
| Geographic + month | DTC Direct Buy, Meta/IG Ads | `ZIP_CODE_GEO` + `SVC_DT_M` (after DMA mapping) |

### 14.2 Combine Notebook Join Order

From `99_Combine_Physician_Data_Promotional&Acc` (notebook ID 3598883070773244):

```python
# Step 1: Build skeleton
hcp_universe × cohort_dates → skeleton(PROVIDER_ID, COHORT, SVC_DT_M)

# Step 2: Add BHID via PROVIDER_ID → BHID crosswalk
skeleton LEFT JOIN sspr_id_mapping → hcp_universe_bhid

# Step 3: Add geographic features
hcp_universe_bhid LEFT JOIN geo_features ON BHID → adds ZIP_CODE_GEO

# Step 4: Join HCP_COHORT_ID-keyed channels
hcp LEFT JOIN call_features ON HCP_COHORT_ID
hcp LEFT JOIN speaker_program ON HCP_COHORT_ID
hcp LEFT JOIN hq_email_features ON HCP_COHORT_ID
hcp LEFT JOIN irep_features ON HCP_COHORT_ID
hcp LEFT JOIN clickstream_features ON HCP_COHORT_ID
hcp LEFT JOIN ftp_features ON HCP_COHORT_ID
hcp LEFT JOIN samples_features ON HCP_COHORT_ID

# Step 5: Join Digital (NPI-keyed)
hcp_paid_search LEFT JOIN hcp_npi_mapping ON NPI_NUMBER → adds PROVIDER_ID
hcp LEFT JOIN hcp_paid_search ON [PROVIDER_ID, SVC_DT_M]

# Step 6: Join DTC (geographic-keyed)
dtc LEFT JOIN dma_zip_mapping ON DMA_Code → adds ZIP_CODE_GEO
hcp LEFT JOIN dtc ON [ZIP_CODE_GEO, SVC_DT_M]
```

### 14.3 Total Non-Personal Feature Count

Counts below are **feature columns only** (excluding key columns like `HCP_COHORT_ID`,
`SVC_DT`, `PROVIDER_ID`, etc.). The §13 cross-channel table counts include key columns
(+2 typically), so those numbers are slightly higher.

| Channel | Feature Columns | Total Columns (incl. keys) |
| --- | --- | --- |
| Digital Engagement | 665 | 667 (+ NPI_NUMBER, SVC_DT_M) |
| HQ Emails | 30 | 32 (+ HCP_COHORT_ID, SVC_DT) |
| DTC Direct Buy | 8 | 10 (+ DMA_Code, DATA_MONTH) |
| Meta/Instagram Ads | 2 | (merged into DTC output) |
| Samples | 54 | 56 (+ HCP_COHORT_ID, SVC_DT) |
| Speaker Programs | 66 | 68 (+ HCP_COHORT_ID, SVC_DT) |
| FTP | 7 | 9 (+ HCP_COHORT_ID, PULL_DT) |
| **Total features** | **~832** | |

---

## 15. Output File Paths

All outputs write to the same base volume:
```
/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/
  hcp_level_model/dev_folder/notebook_output/
```

| Channel | File Name |
| --- | --- |
| Digital Engagement | `kerendia_nba_3_0_hcp_model_paid_search_features.parquet` |
| HQ Emails | `kerendia_nba_3_hcp_model_hq_email_features.parquet` |
| DTC + Meta/IG | `kerendia_nba_3_hcp_model_DTC_PROMOTION.parquet` |
| Samples | `kerendia_nba_3_hcp_model_samples_features.parquet` |
| Speaker Programs | `kerendia_nba_3_hcp_model_speaker_program.parquet` |
| FTP | `kerendia_nba_3_hcp_model_ftp_features.parquet` |
