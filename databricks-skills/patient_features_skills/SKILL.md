---
name: generic-patient-features
description: >
  Consolidated, data-source-agnostic reference for patient-level feature engineering in the
  Kerendia NBA 3.x pipeline. Covers First Occurrence, Recency, Frequency, and Hospitalization
  features across RX, DX, PX, and Lab claim types. Read this skill when generating, modifying,
  or understanding any patient feature notebook, when standardizing raw claim data to the
  canonical schema, or when optimizing feature computation at 100B-row scale.
  Feature family: CLAIMS ONLY. Every generated notebook declares FEATURE_FAMILY = "claims" and
  loads its cohorts with CohortGenerator("claims").load() from 00_cohort_generation. Do not use
  this skill for promotional, MMIT, LAAD LRx or any other family. Features are built only for
  HCPs in the NBA 3.1 HCP universe (HCP_UNIVERSE_PATH).
---

# Generic Patient Feature Engineering

Single consolidated reference for all patient-level feature types in the Kerendia NBA 3.x
pipeline. The same computation patterns apply to RX, DX, PX, and Lab data -- only the source
column names and event semantics differ. This skill abstracts those differences into a
canonical input contract and documents the business rules, grain, column naming, and
performance patterns for each feature type.

> **Feature family: CLAIMS ONLY.** This skill generates CLAIMS-type features only (RX, DX,
> PX, Lab, Hospitalization). Every notebook generated from this skill must declare
> `FEATURE_FAMILY = "claims"` and load its cohort with `CohortGenerator("claims").load()`.
> Do not pass `"promotional"`, `"mmit"`, `"laad_lrx"`, or any other value. Do not call the
> base primitives (`get_cohort_bounds`, `get_cohort_months`, `assign_cohort_month`) directly --
> the `CohortGenerator` wraps them with the correct claims offset (0) and the correct
> lookback-window formulas. If a future feature family is needed, create a separate skill --
> do not reuse this one.

### The one correct way to load cohorts in a claims feature notebook

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_1_develop_sa/NBA 3.1 - Dev/00_Helper_Notebooks/00_cohort_generation"

FEATURE_FAMILY = "claims"   # this skill's family — do not change
cohorts = CohortGenerator(FEATURE_FAMILY).load()
# cohorts is a 28-row DataFrame with: cohort_id, prediction_month, dataset,
# offset_days (=0), lookback_start_date, lookback_end_date
```

This snippet is the single idiom. Every later example in this skill starts from it ("the
loading idiom") and then uses the `cohorts` DataFrame. Details:

* `cohorts` is a **pandas** DataFrame, sorted c1..c28. The `%run` goes in its own cell, after
  `00_connection`. `%run` only accepts a literal path.
* Columns: `cohort_id` (`c1`..`c28`), `prediction_month` (1st of the month, c1 = 2024-07-01),
  `dataset` (`Training` c1-c24, `Testing` c25-c26, `Holdout (Backtesting)` c27-c28),
  `offset_days` (0), `lookback_start_date` and `lookback_end_date` (both 1st of a month,
  c1 = 2023-06-01 and 2024-05-01).
* `load()` reads `kerendia_nba_3_1_volume/cohorts/claims/cohorts.parquet` and never regenerates.
  It fails if the file is missing or was built at another offset; re-run `00_cohort_generation`.
* Iterate the cohorts with `for _, cohort_row in cohorts.iterrows():` and read
  `cohort_row["cohort_id"]`, `cohort_row["lookback_start_date"]`, `cohort_row["lookback_end_date"]`.
* Filter claims to a cohort as shown in Section 10.8.3, "Filtering claims to the lookback
  window". The end date is the first day of the last INCLUDED month.

### HCP universe: features only for HCPs in the universe (mandatory)

Every feature this skill creates is for HCPs in the NBA 3.1 HCP universe only. No output row may
have a `PROVIDER_ID` outside it. The universe is built by `01_HCP_Universe/Final Universe
Creation/01_Final_HCP_Universe_Creation`. It has one row per `PROVIDER_ID` (string, unique, no
nulls) plus the inclusion flags `C1_FLAG`..`C5_FLAG`. On 2026-10-28 it held 314,920 HCPs.

```python
HCP_UNIVERSE_PATH = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/HCP_Universe"   # the FOLDER

hcp_universe = spark.read.parquet(HCP_UNIVERSE_PATH).select("PROVIDER_ID").distinct()

# Right after standardize(), before any aggregation, for EVERY claims input of the notebook
# (total claims, hospitalized claims, ...):
claims = claims.join(F.broadcast(hcp_universe), "PROVIDER_ID", "left_semi")
```

Rules:

* **Filter early.** Apply the `left_semi` join to every claims DataFrame right after
  `standardize()`, so out-of-universe HCPs never reach a pivot, window or shuffle. Keep
  `PROVIDER_ID` as a string on both sides; do not cast it to a number.
* **The skeleton is the universe.** The output skeleton (Section 8.2) is `hcp_universe x
  cohorts`. It is NOT built from the 3.0 `hcp_universe_path`
  (`kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`) or from the HCPs found in the
  claims. Universe HCPs with no claims in a cohort keep their skeleton row, with null or 0
  feature values as each feature type defines.
* **Patient-level history is the one exception.** The patient-level status tables in Section
  13.0, and the patient-level washout checks such as the 13.2 triggers, are built from claims by
  ANY provider. Only the roll-up to HCP panels is restricted to the universe: join the panel
  to `hcp_universe` before you aggregate. Do not filter those patient-level inputs, or patients
  seen by out-of-universe HCPs would lose history and look "new".
* **Test runs sample the universe.** `TEST_HCP_SAMPLE` (Section 12.2) samples from
  `hcp_universe`, never from the claims.
* **Check before writing** (Section 10.8.6, check 5): `out.join(hcp_universe, "PROVIDER_ID",
  "left_anti").count() == 0`.
* **Always read the `HCP_Universe` folder, never a `part-*.parquet` file inside it.** The
  part-file name changes every time the universe notebook rewrites the folder, and Spark reads
  only the committed files of the latest write.

## Feature Execution Order

Features are created in this order. Each step is independent but follows the same pipeline:

1. **First Occurrence** -- when an event first appeared in a patient's journey (full lookback)
2. **Recency** -- how recently and frequently events occurred (12M lookback, 6 sub-features)
3. **Frequency** -- monthly event counts, rolling lags, change in frequency, unique patient counts
4. **Hospitalization** -- fraction of claims involving hospitalized patients (DX/PX only)

---

## 1. Input Contract

Feature computation requires claims data standardized to the canonical schema below. This is
a **prerequisite** -- the feature logic assumes these column names exist and does not perform
source-specific renaming internally.

### 1.1 Canonical Columns

| Column | Type | Description | Required By |
| --- | --- | --- | --- |
| `PROVIDER_ID` | string | Healthcare provider (HCP) identifier | All features |
| `PATIENT_ID` | string | Patient identifier | First Occ, Recency, Freq Sub-D, Hosp Sub-D |
| `EVENT_NAME` | string | Event being measured (drug, diagnosis, procedure, test) | All features |
| `EVENT_DATE` | date | Date the event occurred | All features |
| `EVENT_TYPE` | string | Assigned label: `rx`, `dx`, `px`, or `lab` | First Occ, Recency |
| `CLAIM_ID` | string | Unique claim identifier | Optional (dedup) |
| `DATA_SOURCE` | string | Source system flag (e.g., `HX` for hospitalized) | Hospitalization only |

Columns not listed here (payer plans, ICD versions, HCP flags, referring/rendering provider
IDs) are **dropped** before feature computation. They add shuffle weight without contributing
to any feature.

### 1.2 Raw-Source Column Mapping

The current pipeline reads pre-processed Delta tables where upstream code already renamed
columns. When working from **arbitrary or raw sources**, produce the canonical schema first.

#### Direct Renames (same identifier, different column name)

| Canonical | RX Raw | DX Raw | PX Raw | Lab Raw | Other Common Variants |
| --- | --- | --- | --- | --- | --- |
| `PROVIDER_ID` | `PROVIDER_ID` | `PROVIDER_ID` | `PROVIDER_ID` | `PROVIDER_ID` | `HCP_ID`, `PHYSICIAN_ID`, `PROV_ID` |
| `PATIENT_ID` | `PATIENT_ID` | `PATIENT_ID` | `PATIENT_ID` | `PATIENT_ID` | `MEMBER_ID`, `ENROLLEE_ID`, `SUBSCRIBER_ID` |
| `EVENT_NAME` | `PRODUCT_GROUP` | `DIAGNOSIS_DESCRIPTION` | `PROCEDURE_DESCRIPTION` | `TEST_TYPE` | -- |
| `EVENT_DATE` | `SVC_DT` | `SVC_DT` | `SVC_DT` | `SVC_DT` | `SERVICE_DATE`, `CLAIM_DATE`, `FILL_DT` |
| `CLAIM_ID` | `CLAIM_ID` | `CLAIM_ID` | `CLAIM_ID` | `CLAIM_ID` | `CLAIM_NBR`, `CLAIM_NUMBER` |

#### Identifier Mapping (different identifier system)

When the raw source uses a different identifier system, a lookup/crosswalk table is needed.
This is common when integrating data from multiple vendors or when raw claims use national
identifiers:

| Raw Identifier | Mapping Approach | Target |
| --- | --- | --- |
| `NPI` (National Provider Identifier) | Join to crosswalk table (`NPI` -> `PROVIDER_ID`); broadcast the crosswalk if < 10MB | `PROVIDER_ID` |
| `BHID` (Bayer Healthcare ID) | Direct rename if 1:1 with `PROVIDER_ID`; otherwise crosswalk | `PROVIDER_ID` |
| `PROVIDER_NPI` | Same as `NPI` | `PROVIDER_ID` |

Pattern:
```python
# NPI -> PROVIDER_ID via crosswalk (small dimension, broadcast)
npi_crosswalk = spark.read.format("delta").load(crosswalk_path)
claims = claims.join(F.broadcast(npi_crosswalk), on="NPI", how="inner").drop("NPI")
```

#### IQVIA LAAD Specifics

IQVIA LAAD FCT_RX tables use `PHYSICIAN_ID` or `PROV_ID` for the provider and `FILL_DT` or
`SERVICE_DT` for the date. The product name comes from a DIM_PRD join (`PRODUCT_GROUP` where
`CLAIM_TYPE = 'PD'`). Standardize before loading into the feature pipeline:

```python
claims = (raw_rx
    .select(
        F.col("PHYSICIAN_ID").alias("PROVIDER_ID"),
        F.col("PATIENT_ID"),
        F.col("FILL_DT").cast("date").alias("EVENT_DATE"),
        F.col("PRODUCT_GROUP").alias("EVENT_NAME"),
    )
    .filter(F.col("PROVIDER_ID").isNotNull())
    .filter(F.col("EVENT_NAME").isNotNull())
)
```

### 1.3 Standardization Function

```python
COLUMN_MAP = {
    "PROVIDER_ID": ["PROVIDER_ID", "HCP_ID", "PHYSICIAN_ID", "PROV_ID", "BHID"],
    "PATIENT_ID":  ["PATIENT_ID", "MEMBER_ID", "ENROLLEE_ID", "SUBSCRIBER_ID"],
    "EVENT_NAME":  ["PRODUCT_GROUP", "DIAGNOSIS_DESCRIPTION",
                    "PROCEDURE_DESCRIPTION", "TEST_TYPE"],
    "EVENT_DATE":  ["SVC_DT", "SERVICE_DATE", "CLAIM_DATE", "FILL_DT"],
    "CLAIM_ID":    ["CLAIM_ID", "CLAIM_NBR", "CLAIM_NUMBER"],
}

def standardize(df, event_type):
    for canonical, variants in COLUMN_MAP.items():
        for v in variants:
            if v in df.columns and canonical not in df.columns:
                df = df.withColumnRenamed(v, canonical)
                break
    df = df.withColumn("EVENT_TYPE", F.lit(event_type))
    keep = [c for c in
            ["PROVIDER_ID", "PATIENT_ID", "EVENT_NAME", "EVENT_DATE",
             "EVENT_TYPE", "CLAIM_ID", "DATA_SOURCE"]
            if c in df.columns]
    return df.select(*keep)
```

#### Column Sanitization (`sanitize_column_name`)

Event names from source data (`PRODUCT_GROUP`, `DIAGNOSIS_DESCRIPTION`,
`PROCEDURE_DESCRIPTION`) contain spaces, parentheses, slashes, and plus signs -- all
**invalid in Delta column names**. Delta forbids: ` ,;{}()\n\t=` in column names.

Every pivoted column name MUST be sanitized before writing to Delta:

```python
def sanitize_column_name(name):
    import re as _re
    name = _re.sub(r'[^A-Za-z0-9_]', '_', name.replace("+", "AND").replace("/", "_OR_"))
    name = _re.sub(r'_+', '_', name).strip('_')
    return name.upper()
```

**Backtick requirement:** When referencing pivoted columns whose names may contain
special characters, use backticks: `F.col(f"\`{col_name}\`")`. Bare `F.col(col_name)`
fails when the column name has spaces or parentheses.

> **Warning:** `standardize()` keeps only canonical columns (`PROVIDER_ID`, `PATIENT_ID`,
> `EVENT_NAME`, `EVENT_DATE`, `EVENT_TYPE`, `CLAIM_ID`, `DATA_SOURCE` if present). Any
> filter or reference to other columns (HCP flags, payer plans, ICD versions) must be
> applied BEFORE `standardize()` or will fail with `UNRESOLVED_COLUMN`.

### 1.4 Hospitalization-Specific Inputs

Hospitalization features (DX and PX only) require **two** input sources:

| Source | Filter | Used For |
| --- | --- | --- |
| Total claims (`dx1_file_path` / `px1_file_path`) | All claims | Denominator (total claim count) |
| Hospitalized claims (`dx_hosp_file_path` / `px_hosp_file_path`) | **Pre-filtered upstream** (no `DATA_SOURCE` column in file) | Numerator (hospitalized claim count) |

> **Important:** Hospitalized claims files are **pre-filtered upstream** -- they contain
> only hospitalized claims and do NOT have a `DATA_SOURCE` column. Do NOT apply a
> `DATA_SOURCE = 'HX'` filter; load and `standardize()` directly.

Both sources are collapsed to a single event literal: `lit("ALL_DIAGNOSIS")` (DX) or
`lit("ALL_PROCEDURES")` (PX). No per-event breakdown in hospitalization features.

### 1.5 Market Basket (REQUIRED for every claim type)

Every claim type MUST have a **market basket**: an explicit, curated list of the events that
features are built for. Features are generated **only** for basket events -- drugs (RX),
diagnoses (DX), procedures (PX) and lab tests (Lab). Claims for events outside the basket
are dropped right after `standardize()`.

> The market baskets are the NBA 3.1 event lists in `kerendia_nba_3_1_volume/feature_selection/`.
> They are loaded by the config notebook `00_event_list_config` (see below). Generated notebooks
> must `%run` that config and call `event_groups()`, `apply_event_list()`, and
> `validate_event_input()` -- they must NOT hard-code event lists.
>
> **Config notebook:** `/Users/wenjie.chen@bayer.com/kerendia_nba_3_1_develop_sa/NBA 3.1 - Dev/02_Input_Data_Creation/00_event_list_config`
>
> Load it with `%run` in its own cell, AFTER `00_connection` and BEFORE any feature code:
> ```python
> %run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_1_develop_sa/NBA 3.1 - Dev/02_Input_Data_Creation/00_event_list_config"
> ```

| Claim type | Event list CSV | Join key (source column) | EVENT_GROUPs | Clubbed rows |
| --- | --- | --- | --- | --- |
| RX | `Kerendia NBA 3.1 - Rx Event List.csv` | `EVENT_NAME` (Rx product name) | 258 | 116 |
| DX | `Kerendia NBA 3.1 - Dx Event List.csv` | `EVENT_CODE` (ICD-10) | 240 | 133 |
| PX | `Kerendia NBA 3.1 - Px Event List.csv` | `EVENT_CODE` (CPT/HCPCS) | 106 | 11 |
| Lab | `Kerendia NBA 3.1 - Lab Event List.csv` | `EVENT_CODE` (LOINC) | 4 | 21 |

> **Rx names:** The 3.1 Rx list uses `pt_lvl_nbrx.PRODUCT_NAME` (spelled-out names), not the
> 3.0 LAAD `PRODUCT_GROUP` (abbreviated). `01_Input_data_creation` joins an NDC crosswalk from
> `pt_lvl_nbrx` to map NDC_CD to PRODUCT_NAME before applying the event list.
>
> **Dx/Px join on code, not description:** Descriptions are truncated at ~100 chars and are
> not unique. Always join on `EVENT_CODE`.
>
> **Lab LOINC fallback:** Some lab records have null `LOINC_CD`. The config maps `TEST_TYPE`
> (GFR/UACR) to the first member LOINC of the same group, so those records are kept.

Rules:

1. **Input files are pre-clubbed.** `01_Input_data_creation` applies `apply_event_list()`
   before writing, so the `EVENT_NAME` column in the input files already holds the clubbed
   `EVENT_GROUP` value. Feature notebooks read these files and do NOT need to call
   `apply_event_list()` again.
2. **Pivot on the fixed list.** Use `event_groups(claim_type)` as the explicit pivot value
   list: `.pivot("EVENT_NAME", event_groups("rx"))`. The output schema is then fixed
   (identical across batches, cohorts and reruns), even when a basket event has no claims.
3. **Validate.** Call `validate_event_input(df, claim_type)` at the top of each notebook to
   guard against stale or unclubbed inputs.
4. The basket replaces `event_prevalence` and `relevant_rx_events` as the column-count
   control (Section 7.8). Remove those parameters from 3.1 notebooks.
5. Hospitalization (DX/PX) uses the basket-filtered claims for both the total and the
   hospitalized counts, then collapses them to `ALL_DIAGNOSIS` / `ALL_PROCEDURES`.

```python
# In every generated 3.1 feature notebook (after %run 00_event_list_config).
# Load via INPUT_PATHS_31 (set by 00_event_list_config; see Section 2.1 for key table):
claims = spark.read.format("delta").load(INPUT_PATHS_31["rx_all"])
validate_event_input(claims, "rx")  # guard: fail if EVENT_NAME values are not 3.1 EVENT_GROUPs

# Use event_groups() as the explicit pivot list (fixed schema across cohorts):
event_keys = event_groups("rx")
# ... .pivot("EVENT_NAME", event_keys) ...
```

---

## 2. Anchor Dates and Cohort Generation

Each HCP is observed across multiple cohorts (time snapshots). Cohort parameters come from
`00_config`:

| Parameter | Description | Default |
| --- | --- | --- |
| `cohort_start_date` | First anchor date | -- |
| `cohort_end_date` | Last anchor date | -- |
| `months_increment` | Months between cohorts | `2` |
| `lookback_duration` | Days of history per cohort | `365` |
| `prediction_duration` | Days after anchor for label | `90` |
| `cohort_day_offset` | Day of month that starts each custom-month (1 = calendar month) | `1` |

**Derivation per cohort (default, `cohort_day_offset = 1`):**

- `LOOKBACK_END_DATE` = last day of the month, 2 months before the anchor
- `LOOKBACK_START_DATE` = `LOOKBACK_END_DATE - lookback_duration` days
- `HCP_COHORT_ID` = `{PROVIDER_ID}_{COHORT}` (e.g., `PRV123_I01`)
- `SVC_DT_M` = `date_trunc('MM', EVENT_DATE)` (monthly grain for frequency features)
- `EVENT_TIME` = `datediff(LOOKBACK_END_DATE, EVENT_DATE)` (days from event to anchor)

When `cohort_day_offset` is set to a value other than `1`, cohort boundaries shift to
custom-month windows (e.g., offset=15 means each "month" runs from the 15th to the 14th).
See Section 10 for the full custom cohort boundary specification.

> **NBA 3.1:** the 28 cohorts (c1-c28) are generated once and saved by
> `00_cohort_generation`. Every notebook from this skill gets them with the loading idiom at
> the top of this skill (`CohortGenerator("claims").load()`) and follows Section 10.8. Do not
> build cohorts or cohort dates in the notebook, and do not use `custom_month_bucket`.
>
> **Cohort config path:** generated notebooks `%run` the cohort-generation notebook, which
> holds the per-family offsets and the saved 28-cohort schedule:
> `COHORT_CONFIG_PATH = /Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_1_develop_sa/NBA 3.1 - Dev/00_Helper_Notebooks/00_cohort_generation`.
> Load it with `%run` in its own cell, AFTER `00_connection`. `%run` only accepts a literal
> path, not a variable, so if the path changes, update the loading idiom, this note,
> Sections 9, 10.8 and 12.1, and every generated notebook. Do NOT `%run` the base
> `00_cohort_config` directly.
>
> **Claims cohorts (this skill's family).** Use the loading idiom exactly, then iterate the
> rows:
> ```python
> %run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_1_develop_sa/NBA 3.1 - Dev/00_Helper_Notebooks/00_cohort_generation"
>
> FEATURE_FAMILY = "claims"   # this skill's family — do not change
> cohorts = CohortGenerator(FEATURE_FAMILY).load()
> # cohorts is a 28-row DataFrame with: cohort_id, prediction_month, dataset,
> # offset_days (=0), lookback_start_date, lookback_end_date
>
> for _, cohort_row in cohorts.iterrows():
>     COHORT              = cohort_row["cohort_id"]            # c1..c28
>     LOOKBACK_START_DATE = cohort_row["lookback_start_date"]  # 1st of the first included month
>     LOOKBACK_END_DATE   = cohort_row["lookback_end_date"]    # 1st of the LAST included month
>     ...                                                       # split: cohort_row["dataset"]
> ```
> * In this skill, the 3.0 names `LOOKBACK_START_DATE` / `LOOKBACK_END_DATE` and
>   `HCP_COHORT_ID = {PROVIDER_ID}_{COHORT}` now come from these columns, not from `00_config`.
> * Month-boundary semantics: `LOOKBACK_END_DATE = 2024-05-01` means all of May 2024 is
>   included. See "Filtering claims to the lookback window" in Section 10.8.3.

Anchor dates are saved to `hcp_model_inference_anchor_dates.csv` for downstream joins.

### 2.1 Default File Paths

When generating notebooks from this skill, pre-fill file paths with the values below. Do NOT
leave paths as empty strings -- the pipeline will fail with `FileNotFoundError` at runtime.

> **Hard rule:** All paths in this skill must be under `kerendia_nba_3_1_volume`. Never write to
> `kerendia_nba_3_volume` — that is the 3.0 production Volume and must not be modified.

**Base paths:**

| Path | Value |
| --- | --- |
| Input claims (`INPUT_PATHS_31`) | Nine Delta tables in `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/ops_pipeline/query_output/`; see key table below. Loaded by `%run 00_event_list_config`. |
| HCP universe (`HCP_UNIVERSE_PATH`) | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/HCP_Universe` (folder, 314,920 HCPs) |
| Notebook output base (`OUTPUT_BASE`) | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/notebook_output/patient_features/` — subfolders: `rx/`, `dx/`, `px/`, `lab/` (created 2026-10-28) |

> All nine input files are Delta tables with `PROVIDER_ID` as a string (no nulls), written
> 2026-10-28 by job `665032125276460` / run `5189509327097` using the 3.1 HCP universe
> (314,920 HCPs) and the 3.1 event lists. Read them via `INPUT_PATHS_31` — never hardcode
> paths into notebooks; never read from `kerendia_nba_3_volume` (that is the 3.0 production
> Volume and must not be modified).

```python
# 00_event_list_config sets INPUT_PATHS_31 — use its keys, never a hardcoded path:
claims = spark.read.format("delta").load(INPUT_PATHS_31["rx_all"])
```

**Input claims paths** (`INPUT_PATHS_31` keys, set by `00_event_list_config`):

| Source | First Occ + Recency | Frequency | Hospitalized (HX) |
| --- | --- | --- | --- |
| RX | `INPUT_PATHS_31["rx_all"]` | `INPUT_PATHS_31["rx_12m"]` | -- |
| DX | `INPUT_PATHS_31["dx_full_history"]` (full history, 2021-01-02→2026-08-31) | `INPUT_PATHS_31["dx_12m"]` (windowed, 2023-05-01→2026-08-31) | `INPUT_PATHS_31["dx_hosp"]` (windowed, 2023-05-01→2026-08-31) |
| PX | `INPUT_PATHS_31["px_all"]` | `INPUT_PATHS_31["px_all"]` (same file; no windowed PX variant) | `INPUT_PATHS_31["px_hosp"]` |
| Lab | `INPUT_PATHS_31["lab"]` | same key (Frequency too) | -- |

> **3.1 data coverage — all 9 files verified from Delta log (2026-10-28, job `665032125276460` /
> run `5189509327097`). All files end at 2026-08-31.**
>
> | Key | File (under `query_output/`) | `SVC_DT` min | Row count | Notes |
> | --- | --- | --- | --- | --- |
> | `rx_all` | `rx_input_claims_total_events_and_first_occ_features_input` | 2021-01-02 | 4.03B | Full history |
> | `rx_12m` | `rx_input_claims_12M_features_input` | 2023-05-01 | 2.55B | Windowed (lookback_start) |
> | `dx_full_history` | `dx_input_claims_all_events_features_input` | 2021-01-02 | 1.93B | Full history |
> | `dx_12m` | `dx_input_claims_12M_and_first_occ_features_input` | 2023-05-01 | 1.22B | Windowed (lookback_start) |
> | `dx_hosp` | `dx_hospitalization_claims_all_events_features_input` | 2023-05-01 | 567M | Windowed; covers all 28 cohorts |
> | `px_all` | `px_input_claims_all_events_features_input` | 2021-01-02 | 673M | Full history |
> | ~~`px_full_history`~~ | ~~`px_input_claims_12M_and_first_occ_features_input`~~ | 2021-01-02 | 673M | **Removed from `INPUT_PATHS_31`** — identical query to `px_all` (no windowed PX variant in the source data); key dropped 2026-10-28 |
> | `px_hosp` | `px_hospitalization_claims_all_events_features_input` | 2021-01-02 | 315M | Full history |
> | `lab` | `lab_input_claims_12M_and_first_occ_features_input` | 2021-07-01 | 389M | Full history (lab data starts Jul 2021) |
>
> All full-history files start before 2023-06-01 (c1 `lookback_start_date`) ✔. All windowed
> files start at 2023-05-01 (= `min(lookback_start_date) − 1 month`) ✔. All 9 files cover
> all 28 cohorts.
>
> **PX windowed variant:** PX has no windowed variant. The `px_full_history` key
> was removed from `INPUT_PATHS_31` (2026-10-28) after confirming the two PX queries in
> `01_Input_data_creation` were byte-for-byte identical (same SQL, same `SVC_DT <= lookback_end`,
> same event list, same row count 673M). Use `INPUT_PATHS_31["px_all"]` for all PX feature
> types (First Occ, Recency, Frequency).
>
> The DX name/content mismatch present in the 3.0 Volume is **fixed** in the 3.1 Volume:
> `dx_full_history` → `dx_input_claims_all_events_features_input` (full history) and
> `dx_12m` → `dx_input_claims_12M_and_first_occ_features_input` (windowed). The previous
> note about DX hospitalization being unusable is **obsolete** — `dx_hosp` covers all
> 28 cohorts.

**Output paths**:

| Variable | Value |
| --- | --- |
| `OUTPUT_BASE` | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/notebook_output/patient_features/` |
| Notebook subfolder | `rx/` (RX), `dx/` (DX), `px/` (PX), `lab/` (Lab) — all created 2026-10-28 |
| `anchor_dates_path` | `{OUTPUT_BASE}{notebook_subfolder}/hcp_model_inference_anchor_dates.csv` |
| `HCP_UNIVERSE_PATH` (NBA 3.1) | `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/HCP_Universe` (folder, 314,920 HCPs; input, not output). Replaces the 3.0 `hcp_universe_path` (`kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`); do not use the 3.0 path. |
| Feature outputs | `{OUTPUT_BASE}{notebook_subfolder}/{source}_{feature_type}_features` (Delta; e.g., `rx/rx_first_occurrence_features`, `dx/dx_recency_features`) |

---

## 3. Feature Type 1: First Occurrence

### What it answers

*How many days before the anchor date did this event first appear in the patient's journey?*

### How It Works

Raw claims are first collapsed to one row per `(PROVIDER_ID, EVENT_NAME)` pair, recording
only the earliest `EVENT_DATE`. This intermediate (typically N-million rows) is then
**pivoted wide per HCP first**, and only then cross-joined with the cohort anchor dates to
compute `EVENT_TIME` for each event column. Joining 100B raw claims directly against the
cohort dates before aggregating would produce a 100B x N_cohorts cross-join that does not
scale. The pre-aggregation step is what makes the pipeline feasible at production data
volumes.

```
Step 1: Collapse raw claims
  groupBy(PROVIDER_ID, EVENT_NAME)
    .agg(min(EVENT_DATE) -> FIRST_OCCURRENCE_DATE)
  -> save intermediate to Delta/Parquet               (millions of rows)

Step 2: Pivot wide (once, cohort-independent)
  groupBy(PROVIDER_ID)
    .pivot(EVENT_KEY, event_keys)                     -- explicit list = market basket keys
    .agg(min(FIRST_OCCURRENCE_DATE))
  -> one row per HCP, one DATE column per event

Step 3: Attach cohort dates and compute EVENT_TIME
  wide
    .crossJoin(broadcast(cohort_anchor_dates))        (~100 rows, broadcast)
    .select(per event column:
        when(datediff(LOOKBACK_END_DATE, col) >= 0,   -- future leakage guard
             datediff(LOOKBACK_END_DATE, col))
        -> MAX_EVENT_TIME_{EVENT_KEY}_FIRST_OCCURRENCE)
  -> drop HCP-cohort rows where every event column is NULL
```

```python
pre = (claims.groupBy("PROVIDER_ID", "EVENT_KEY")
             .agg(F.min("EVENT_DATE").alias("FIRST_OCCURRENCE_DATE")))            # Step 1
wide = pre.groupBy("PROVIDER_ID").pivot("EVENT_KEY", event_keys).agg(F.min("FIRST_OCCURRENCE_DATE"))  # Step 2
fo_cols = [f"MAX_EVENT_TIME_{k}_FIRST_OCCURRENCE" for k in event_keys]
out = (wide.crossJoin(F.broadcast(cohorts.select("COHORT", "LOOKBACK_END_DATE")))     # Step 3
           .select("PROVIDER_ID", "COHORT",
                   *[F.when(F.datediff("LOOKBACK_END_DATE", k) >= 0,
                            F.datediff("LOOKBACK_END_DATE", k)).alias(c)
                     for k, c in zip(event_keys, fo_cols)])
           .filter(F.greatest(*[F.col(c).isNotNull().cast("int") for c in fo_cols]) == 1)
           .withColumn("HCP_COHORT_ID", F.concat_ws("_", "PROVIDER_ID", "COHORT")))
```

> **Why pivot before the cross-join (changed 2026-10):** the earlier order was Step 1 ->
> cross-join -> pivot. That multiplied the 21.4M (HCP, event) rows by the number of cohorts
> (~406M rows for 19 cohorts) BEFORE the pivot shuffle. Pivoting first shuffles only the
> 21.4M rows, once. The cross-join then becomes a cheap broadcast with a narrow `select` and no
> second shuffle. On serverless (RX, full universe of 231K HCPs, 243 events, 19 cohorts at
> offset 7), Steps 2+3 took **0.21 min vs 1.31 min (~6x faster)**. The output was identical:
> 4,366,572 rows and 0 differences after dropping the all-NULL HCP-cohort rows. The gain grows
> linearly with the number of cohorts, and the new order needs no cohort batching. Step 1 is
> unchanged in both orders (2.9 min: 3.6B claims down to 21.4M pairs).
> Only fall back to cross-join -> pivot if the event list is too large to pivot in a single
> pass (thousands of events). With a market basket (Section 1.5), that does not happen.

### Business Rules

| Rule | Detail | Hard / Tunable |
| --- | --- | --- |
| Lookback scope | Full history (`EVENT_TIME >= 0`, no lower bound) | **Hard** |
| Future leakage guard | `when(EVENT_TIME >= 0, EVENT_TIME)` per event column (NULL if the first event is after the cutoff), then drop all-NULL rows | **Hard** |
| Core aggregation | `min(FIRST_OCCURRENCE_DATE)` per HCP per event, then `datediff(cutoff, date)`; equals `max(EVENT_TIME)` per `HCP_COHORT_ID` per `EVENT_NAME` | **Hard** |
| Step order | Pre-aggregate -> pivot -> cross-join cohorts (see the note under How It Works) | **Hard** (default) |
| Interpretation | `max(EVENT_TIME)` = earliest event (most days before anchor) | -- |
| Event prevalence filter | `event_prevalence` threshold (0.00 = keep all) | **Tunable** |
| Bypass list | `relevant_rx_events` force-keeps specific drugs (RX only) | **Tunable** |
| Batch size | Not needed for First Occurrence (output is N_HCP x N_cohorts rows) | -- |

### NBA 3.1 Feature Removal Notes (First Occurrence)

> **We are commenting out (removing) the following first-occurrence features in NBA 3.1 because
> they are left-censored -- the data starts on 2021-01-02, and for long-established drugs most
> HCPs' first claim falls within 60 days of the data start, so the value measures the data
> start date, not when the HCP adopted the drug. 34 of 243 Rx events have >50% of HCPs
> censored (lisinopril 76%, amlodipine 76%, losartan 73%, metformin 70%, spironolactone 64%,
> etc.). These features survive model selection only as proxies for HCP size/specialty,
> which the model already captures from volume features.**
>
> **Action:**
> 1. Drop `FIRST_OCCURRENCE` columns for the 34 censored events listed in `CENSORED_EVENTS`
>    (kept in `00_cohort_config`).
> 2. For the remaining established events, replace the value with `min(days, 365)` and add a
>    flag column `FIRST_CLAIM_BEFORE_WINDOW`.
> 3. Keep first-occurrence features for drugs launched within the data window (Kerendia,
>    Mounjaro, Inpefa, and other recent brands where the share near the data start is low).
>
> The 3.1 event list clubbing (Section 1.5) already rolls up split product variants, so the
> split-name problem (metformin ER F/G/Z, etc.) is handled at the event-list level.

### Grain

`HCP_COHORT_ID` -- one row per HCP-cohort, one column per distinct `EVENT_NAME`.

### Column Naming

`max(EVENT_TIME)_{EVENT_NAME}_first_occurrence`

Example: `max(EVENT_TIME)_KERENDIA_first_occurrence = 287` means the patient's first Kerendia
prescription was 287 days before the anchor date.

### Cross-Source Variation

| Aspect | RX | DX | PX | Lab |
| --- | --- | --- | --- | --- |
| EVENT_NAME source | `PRODUCT_GROUP` | `DIAGNOSIS_DESCRIPTION` | `PROCEDURE_DESCRIPTION` | `TEST_TYPE` |
| Typical event count | ~29 | ~17 | ~5 | ~2 |

The computation is **identical** across sources -- only `EVENT_NAME` values differ.

### Historical Note

Earlier versions of the pipeline used a direct
`groupBy(HCP_COHORT_ID).pivot(EVENT_NAME).agg(max(EVENT_TIME))` on the full claims table
after joining with cohort dates. This was replaced by the pre-aggregation pattern because
the 100B-row x N_cohorts cross-join before aggregation does not scale to production data
volumes. In 2026-10, the order after pre-aggregation changed from cross-join -> pivot to
pivot -> cross-join (see the note under How It Works).

---

## 4. Feature Type 2: Recency

### What it answers

*How recently did events occur, and how concentrated was the activity in the patient's recent
history?*

### Business Rules

| Rule | Detail | Hard / Tunable |
| --- | --- | --- |
| Lookback scope | 12M only: `EVENT_DATE BETWEEN LOOKBACK_START AND LOOKBACK_END` | **Hard** |
| Re-filtering | Claims are re-filtered to 12M, then re-batched | **Hard** |
| Most recent event | `min(EVENT_TIME)` per `HCP_COHORT_ID` per `EVENT_NAME` | **Hard** |
| Time windows | `[30, 60, 90, 180, 270, 360]` days | **Tunable** |
| Event types | `rx`, `dx`, `px`, `lab` (from `EVENT_TYPE` column) | **Hard** |

### The 12M Filter (critical distinction from First Occurrence)

```python
claims_12m = claims.filter(
    (col("EVENT_DATE") >= col("LOOKBACK_START_DATE")) &
    (col("EVENT_DATE") <= col("LOOKBACK_END_DATE"))
)
```

First Occurrence uses **full history** (all events where `EVENT_TIME >= 0`).
Recency uses **only the 12M window**.

### Six Sub-Features (all joined on `HCP_COHORT_ID`)

| # | Sub-Feature | Method | Output Columns | Description |
| --- | --- | --- | --- | --- |
| 1 | Most Recent Event | `min(EVENT_TIME)` pivot | `min(EVENT_TIME)_{EVENT_NAME}_time_min` | Fewest days before anchor = most recent |
| 2 | Total and Unique Events | `count` / `countDistinct` | `total_events`, `unique_events` | Overall volume per HCP-Cohort |
| 3 | Counts by Time Window | filter + count per window | `total_events_time_{N}_days`, `unique_events_time_{N}_days` | Events in last N days |
| 4 | Counts by Type | filter by EVENT_TYPE + count | `total_{type}`, `unique_{type}` | Per event type (rx/dx/px/lab) |
| 5 | Counts by Type x Window | filter by type AND window | `total_events_time_{N}_days_{type}`, `unique_events_time_{N}_days_{type}` | Cross of types x windows |
| 6 | Skewness | `skewness(EVENT_TIME)` per type x window | `skewness_time_{N}_days_{type}` | Concentration of events within window |

### NBA 3.1 Feature Removal Notes (Recency)

> **We are commenting out (removing) the unsuffixed recency totals in NBA 3.1 because they are
> exact duplicates of the type-suffixed versions. The recency helper writes `TOTAL_EVENTS`,
> `UNIQUE_EVENTS` and `{TOTAL,UNIQUE}_EVENTS_TIME_{N}_DAYS` once with no source suffix, and again
> with the source suffix (`_RX`, `_DX`, `_PX`, `_LAB_DATA`). Because each recency notebook
> processes one source, the two versions are identical (zero mismatches confirmed). This
> removes 56 columns across the four recency outputs. None of the unsuffixed columns is in the
> final 752-feature model.**
>
> **Action:** after the recency helper returns, drop the unsuffixed totals before saving:
> ```python
> suffix = EVENT_TYPE.upper()  # "RX", "DX", "PX", "LAB_DATA"
> unsuffixed = [c for c in df.columns
>     if c.startswith(("TOTAL_", "UNIQUE_")) and not any(c.endswith(s) for s in ("_RX","_DX","_PX","_LAB_DATA"))]
> df = df.drop(*unsuffixed)
> ```

### Grain

`HCP_COHORT_ID`

### Column Naming

Sub-feature 1: `min(EVENT_TIME)_{EVENT_NAME}_time_min`
Sub-features 2-6: see table above

### Cross-Source Variation

Computation is identical. `EVENT_TYPE` values (`rx`, `dx`, `px`, `lab`) are assigned during
standardization. Time windows and skewness formula are source-agnostic.

### Business Purpose by Sub-feature

| # | Sub-Feature | Business Purpose |
| --- | --- | --- |
| 1 | Most Recent Event | How recently the HCP last performed this event. A small `EVENT_TIME` (few days) means the event is current in the HCP's practice; a large value means it has not occurred for a long time. This is the simplest recency signal: is this event still part of the HCP's active behavior? |
| 2 | Total and Unique Events | Overall event volume and breadth. `total_events` captures raw activity level (how busy the HCP is); `unique_events` captures diversity (how many distinct event types the HCP engages with). High total with low unique suggests repetitive focus on a few events; high unique suggests broad engagement. |
| 3 | Counts by Time Window | Event density at different recency levels. Comparing counts across windows (e.g., 30 vs 180 vs 360 days) reveals whether activity is increasing or decreasing over time. A HCP with 20 events in 30 days but only 5 in the next 30 is accelerating; the reverse is decelerating. |
| 4 | Counts by Type | The HCP's event-type mix within the lookback period. An HCP with mostly `rx` events is prescription-driven; one with mostly `dx` is diagnosis-driven. This captures the HCP's clinical focus and practice pattern. |
| 5 | Counts by Type x Window | The intersection of event type and recency. This reveals whether the HCP's practice pattern is shifting -- e.g., a HCP whose `rx` count is stable but `dx` count dropped in the last 60 days may be changing their diagnostic focus. The cross provides finer granularity than either dimension alone. |
| 6 | Skewness | Temporal concentration of events within a window x type slice. Input scope: 12M-filtered claims, further filtered to `EVENT_TIME <= N` and `EVENT_TYPE == t`. Returns `NULL` when fewer than 3 events exist in the slice (Spark requires >= 3 values) or when all events share the same `EVENT_TIME` (zero variance). Positive skew = events clustered far back (front-loaded, tapering off); negative skew = events clustered near anchor (recent intensification); zero/null = too few events or evenly spread. Captures acceleration signal that raw counts cannot. |

---

## 5. Feature Type 3: Frequency

### What it answers

*How often does each event occur at the HCP level, and is the rate accelerating or
decelerating?*

Four sub-types, each saved as a separate Delta/Parquet output.

### Sub-type A: Monthly Claim Count

**What it measures:** The raw count of each event per HCP per month. This is the foundational
frequency feature -- a time series of monthly event volumes.

**Input scope:** All standardized claims (no cohort or lookback filter). Every claim is
assigned to its `SVC_DT_M` month and counted per `EVENT_NAME`.

**Business purpose:** Monthly claim count is the baseline signal for all other frequency
sub-types. It captures the HCP's baseline activity level for each event -- is this a
high-volume or low-volume event for this HCP? The monthly time series also reveals seasonality
and trend patterns that feed into the lag and change-in-frequency computations.

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

```
groupBy(PROVIDER_ID, SVC_DT_M)
  .pivot(EVENT_NAME)
  .agg(count(*))
  -> prefix "FREQ_", sanitize column names, uppercase
```

**Column naming:** `FREQ_{EVENT_NAME}` (e.g., `FREQ_KERENDIA`)

**Sanitization rules:** `,` -> removed, `+` -> `and`, `/` -> ` or`, `-` -> `_`, spaces -> `_`,
uppercase.

### NBA 3.1 Feature Removal Notes (Frequency Sub-type A: Monthly Claim Count)

> **We are commenting out (removing) the `FREQ_*` monthly claim count columns in NBA 3.1 where a
> unique-patient equivalent exists, because the three counts per event (claims per month,
> events per day window, unique patients per window) are near-duplicates. Claim counts are
> highly correlated across windows (median correlation of 1M vs 3M: Rx 0.96, Dx 0.82, Px 0.90)
> and follow the same patients as the unique-patient counts. Unique patients is the easiest to
> interpret and has the highest SHAP share per feature. Keep `NUM_OF_PATIENTS_*` (90/180/360 d)
> and the event counts `TOTAL_EVENTS_TIME_*` (by source). Drop the matching `FREQ_*` claim
> counts once the unique-patient version exists.**
>
> **Action:**
> 1. Generate unique patients only for 90/180/360 d (Sub-type D).
> 2. After Sub-type D output exists, drop `FREQ_*_IN_LAST_*` for events that have a
>    `NUM_OF_PATIENTS_*` equivalent.
> 3. Watch: the top frequency feature `FREQ_ALBUMIN__URINE_EG_MICROALBUMIN_QUANTITATIVE_IN_LAST_12_MONTH_PX`
>    (rank 20) must keep a unique-patient equivalent before its FREQ version is dropped.

### Sub-type B: Lag Frequency (Rolling Windows)

**What it measures:** Rolling cumulative event counts over trailing windows of 1, 2, 3, 6,
and 12 months. Each value is the sum of monthly counts in the last N months ending at the
current `SVC_DT_M`.

**Input scope:** Sub-type A output (monthly claim counts). The `fill_missing` step creates a
dense spine by cross-joining all HCPs with all months, ensuring every HCP has a row for every
month (with 0 for months with no activity).

**Business purpose:** Rolling windows smooth out month-to-month noise and capture sustained
activity levels. A 1-month window shows immediate activity; a 12-month window shows the
annual baseline. Comparing across windows (e.g., 1-month vs 12-month) reveals whether recent
activity is above or below the annual norm. These rolling sums are the direct inputs to
Sub-type C (change in frequency).

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

Three-step process:

1. **`fill_missing`** -- Create dense spine: cross-join all distinct `PROVIDER_ID`s with all
   months from min to max date. Left-join original data, `fillna(0)`.

2. **`lag`** -- Rolling window sums via `Window.partitionBy(PROVIDER_ID).orderBy(SVC_DT_M)`:
   ```python
   F.sum(col).over(window.rowsBetween(-i+1, 0))
       .alias(f"{col}_IN_LAST_{i}_MONTH")
   ```

3. **`process_and_join`** -- Orchestrator: `fill_missing` -> `lag` -> drop raw columns,
   keep only `_IN_LAST_` columns + keys.

**Rolling windows:** `[1, 2, 3, 6, 12]` months (**Tunable**)

**Column naming:** `FREQ_{EVENT}_IN_LAST_{N}_MONTH`

### Sub-type C: Change in Frequency

**What it measures:** Whether the HCP's event rate is accelerating or decelerating compared
to its own 12-month baseline. A positive value means recent activity exceeds the remainder
rate; a negative value means it has slowed.

**Input scope:** Sub-type B output (lag frequency rolling sums).

**Business purpose:** Change in frequency detects momentum shifts in an HCP's practice. A
positive value signals the HCP is ramping up activity for this event beyond their own norm;
a negative value signals they are pulling back. This is a leading indicator of behavioral
change that raw counts or rolling sums alone cannot surface.

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

```
CHANGE = (FREQ_{EVENT}_IN_LAST_{N}_MONTH / N_months)
       - ((FREQ_{EVENT}_IN_LAST_12_MONTH - FREQ_{EVENT}_IN_LAST_{N}_MONTH) / (12 - N_months))
```

**Recent windows:** `[1, 2, 3, 6]` (12M is the baseline, not computed)

**Column naming:** `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_{EVENT}_IN_LAST_{N}_MONTH`

After computing, raw `FREQ_*_IN_LAST_*` columns are **dropped**.

### NBA 3.1 Feature Removal Notes (Frequency Sub-type C: Change in Frequency)

> **We are replacing the absolute-difference change feature with a log-ratio in NBA 3.1 because
> the absolute difference grows with HCP volume, so it mostly repeats volume instead of
> momentum. Correlation of |change| with 12-month volume is 0.59 (Rx), 0.74 (Dx), 0.68 (Px) for
> 1M windows. The log-ratio measures the relative trend separately from size (correlation drops
> to -0.07, 0.21, 0.06 respectively). A large HCP moving from 40 to 44 claims/month gets +4,
> while a small HCP doubling from 2 to 4 gets +2 -- the absolute version favors size. The
> log-ratio treats both as equal momentum.**
>
> **Action:**
> 1. Replace `CHANGE_IN_FREQ_*` with `LOGRATIO_FREQ_*` only for N = 3 and 6.
> 2. Formula: `LOGRATIO_FREQ_{EVENT}_IN_LAST_{N}_MONTH = ln((f_N / N + 0.5) / ((f_12 - f_N) / (12 - N) + 0.5))`
>    where `f_N` = claims in the last N months, `f_12` = claims in the last 12 months.
>    The 0.5 added to both sides keeps it defined when a period has zero claims.
> 3. Drop the old `CHANGE_IN_FREQ_*` columns (1M and 2M windows are also dropped -- only N=3 and
>    N=6 survive).

**Prerequisite:** HCP universe cross-join with cohort anchor dates:
```python
hcp_universe = hcp_universe.crossJoin(cohort_anchor_dates)
lag_freq = hcp_universe.join(lag_freq, on=["PROVIDER_ID", "SVC_DT_M"], how="inner")
```

### Sub-type D: Unique Patient Counts per HCP

**What it measures:** The number of distinct patients an HCP has seen for each event type
within time windows from the cohort's lookback end date.

**Input scope:** All standardized claims, cross-joined with cohort anchor dates, then filtered
to `EVENT_DATE BETWEEN LOOKBACK_START AND LOOKBACK_END`. Patients are deduplicated per
`[PROVIDER_ID, COHORT, EVENT_NAME, PATIENT_ID]` before counting.

**Business purpose:** Unique patient count measures the HCP's patient reach for each event
type. Two HCPs with the same total claim count may differ in patient breadth: one seeing 100
patients once each vs another seeing 10 patients 10 times each. Patient reach is a stronger
signal for market opportunity and HCP influence than raw claim volume.

**Grain:** `[PROVIDER_ID, COHORT]` (NOT monthly)

| Step | Operation |
| --- | --- |
| 1 | Cross-join claims with `hcp_model_inference_anchor_dates.csv` (broadcast) |
| 2 | Filter: `EVENT_DATE BETWEEN LOOKBACK_START AND LOOKBACK_END` |
| 3 | `days_diff = datediff(LOOKBACK_END_DATE, EVENT_DATE)` |
| 4 | Flag: `when(days_diff <= N, 1).otherwise(0)` for each window |
| 5 | Dedup on `[PROVIDER_ID, COHORT, EVENT_NAME, PATIENT_ID]` |
| 6 | `countDistinct(PATIENT_ID)` per `[PROVIDER_ID, COHORT, EVENT_NAME]` per flag |
| 7 | Unpivot -> Pivot wide with descriptive column names |

**Time windows:** `[30, 60, 90, 180, 360]` days (**Tunable**)

**Column naming (varies by claim type):**

| Claim | Prefix |
| --- | --- |
| RX | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_{EVENT}_IN_LAST_{N}_DAYS` |
| DX | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_{EVENT}_IN_LAST_{N}_DAYS` |
| PX | `NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_{EVENT}_IN_LAST_{N}_DAYS` |
| Lab | `NUM_OF_PATIENTS_THE_HCP_DID_LAB_TEST_{EVENT}_IN_LAST_{N}_DAYS` |

### Hard Constraints vs Tunable Parameters

| Parameter | Value | Type |
| --- | --- | --- |
| Monthly grain (Sub-types A-C) | `PROVIDER_ID x SVC_DT_M` | **Hard** |
| Cohort grain (Sub-type D) | `PROVIDER_ID x COHORT` | **Hard** |
| Lag rolling windows | `[1, 2, 3, 6, 12]` months | **Tunable** |
| Change recent windows | `[1, 2, 3, 6]` (excludes 12) | **Tunable** |
| Patient count time windows | `[30, 60, 90, 180, 360]` days | **Tunable** |
| Column sanitization rules | Character replacement map | **Hard** |

---

## 6. Feature Type 4: Hospitalization

### What it answers

*What fraction of an HCP's claims involve hospitalized patients, and how many unique
hospitalized patients did the HCP see?*

**DX and PX only** -- no RX or Lab hospitalization features exist.

### Key Design Decisions

1. **Single collapsed event** -- no per-event breakdown. All claims collapsed to
   `lit("ALL_DIAGNOSIS")` (DX) or `lit("ALL_PROCEDURES")` (PX).
2. **Two input sources** -- total claims + hospitalized-only claims (pre-filtered upstream, no `DATA_SOURCE` column in file).
3. **HCP flags dropped** -- `KERENDIA_FLAG`, `SGLT2_GLP1_FLAG`, `NEPH_FLAG`,
   `TARGETING_HCP_FLAG`, `BPT_HCP_FLAG` removed from hospitalized claims.
4. **Rolling windows** -- `[1, 6, 12]` months (shorter than frequency's `[1, 2, 3, 6, 12]`).
5. **Validation filter** -- rows where `TOTAL < HOSPITALIZED` are removed (data quality).

### Sub-type A: Total and Hospitalized Claim Counts

**What it measures:** The total number of claims and the number of hospitalized-patient
claims per HCP per month. Since events are collapsed to a single `ALL_DIAGNOSIS` or
`ALL_PROCEDURES` literal, each source produces one count column.

**Input scope:** Two sources: (1) all claims for the total count, (2) claims filtered to
`DATA_SOURCE = 'HX'` for the hospitalized count. Both are grouped by `[PROVIDER_ID, SVC_DT_M]`
and pivoted on the collapsed event column.

**Business purpose:** These counts are the building blocks for Sub-type C (percent
hospitalized). The total count captures the HCP's overall volume; the hospitalized count
captures the subset involving inpatient stays. The ratio between them (computed in Sub-type C)
is the primary hospitalization feature.

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

```
total_claims = groupBy(index_cols).pivot(EVENT_COL).agg(F.count(F.lit(1)))  -> TOTAL_CLAIMS_{EVENT}
hosp_claims  = groupBy(index_cols).pivot(EVENT_COL).agg(F.count(F.lit(1)))  -> TOTAL_HOSPITALIZED_CLAIMS_{EVENT}
combined = total.join(hosp, how='left').fillna(0)
```

Since events are collapsed, this produces only:
- `TOTAL_CLAIMS_ALL_DIAGNOSIS` + `TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS` (DX)
- `TOTAL_CLAIMS_ALL_PROCEDURES` + `TOTAL_HOSPITALIZED_CLAIMS_ALL_PROCEDURES` (PX)

### Sub-type B: Lag Hospitalized Counts

**What it measures:** Rolling cumulative total and hospitalized claim counts over trailing
windows of 1, 6, and 12 months. Same `fill_missing` -> `lag` -> `process_and_join` pattern as
Frequency Sub-type B, but applied to both total and hospitalized claim counts.

**Input scope:** Sub-type A output (total and hospitalized monthly counts). The dense spine
and rolling window logic are identical to Frequency Sub-type B.

**Column naming:** `TOTAL_CLAIMS_{EVENT}_IN_LAST_{N}_MONTH` and
`TOTAL_HOSPITALIZED_CLAIMS_{EVENT}_IN_LAST_{N}_MONTH`.

**Business purpose:** Rolling window counts smooth month-to-month variation in
hospitalization rates. The validation filter (TOTAL >= HOSPITALIZED at every window) ensures
data quality before percentages are computed. These rolling counts feed directly into
Sub-type C (percent hospitalized).

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

Same `fill_missing` -> `lag` -> `process_and_join` pattern as Frequency Sub-type B, but:
- **Rolling windows:** `[1, 6, 12]` months
- **Validation filter:** Remove rows where any `TOTAL_CLAIMS_*_IN_LAST_*` <
  corresponding `TOTAL_HOSPITALIZED_CLAIMS_*_IN_LAST_*`:
  ```python
  lag = lag.filter(
      (col("TOTAL_CLAIMS_ALL_DIAGNOSIS_IN_LAST_1_MONTH") >=
       col("TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_1_MONTH")) &
      (col("TOTAL_CLAIMS_ALL_DIAGNOSIS_IN_LAST_6_MONTH") >=
       col("TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_6_MONTH")) &
      (col("TOTAL_CLAIMS_ALL_DIAGNOSIS_IN_LAST_12_MONTH") >=
       col("TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_12_MONTH"))
  )
  ```

### Sub-type C: Percent Hospitalized

**What it measures:** The fraction of an HCP's claims that involve hospitalized patients,
computed over rolling windows. A value of 0.15 means 15% of the HCP's claims in the last N
months were for hospitalized patients.

**Input scope:** Sub-type B output (lag total and hospitalized claim counts).

**Business purpose:** Percent hospitalized captures the severity of the HCP's patient mix.
An HCP with a high hospitalization percentage treats sicker patients (more inpatient stays);
one with a low percentage sees primarily outpatient cases. This severity signal helps
distinguish HCPs who manage complex, hospitalized cases from those focused on routine
outpatient care.

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

```
PERC = WHEN TOTAL_CLAIMS_{EVENT}_IN_LAST_{N}_MONTH != 0
       THEN TOTAL_HOSPITALIZED_CLAIMS_{EVENT}_IN_LAST_{N}_MONTH
            / TOTAL_CLAIMS_{EVENT}_IN_LAST_{N}_MONTH
       ELSE NULL
```

**Windows:** `[1, 6, 12]` months

After computing percent: `TOTAL_CLAIMS_*_IN_LAST_*` columns are **dropped**.
Kept: `PERC_HOSPITALIZED_*` + `TOTAL_HOSPITALIZED_*` + key columns.

**Column naming:** `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_{EVENT}_IN_LAST_{N}_MONTH`

### Sub-type D: Unique Hospitalized Patient Counts

**What it measures:** The number of distinct hospitalized patients an HCP has seen within time
windows from the cohort's lookback end date.

**Input scope:** Hospitalized claims only (`DATA_SOURCE = 'HX'`), using the same cohort
cross-join pattern as Frequency Sub-type D. Time windows are `[30, 180, 360]` days (NOT
`[30, 60, 90, 180, 360]`).

**Business purpose:** Unique hospitalized patient count measures the HCP's reach among
severely ill patients. An HCP with 50 unique hospitalized patients has a broader inpatient
practice than one with 5, even if their total claim counts are similar. This complements the
percent-hospitalized feature: percentage captures intensity, unique count captures breadth.

**Grain:** `[PROVIDER_ID, COHORT]`

**Column naming:**

| Claim | Prefix |
| --- | --- |
| DX | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DIAGNOSED_IN_LAST_{N}_DAYS` |
| PX | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DID_PROCEDURE_IN_LAST_{N}_DAYS` |

### Combine Everything

Both notebooks end with a "Combine Everything" section:

1. Build `skeleton_df` from `hcp_universe x cohort_anchor_dates` with `HCP_COHORT_ID`
2. Join percent-hospitalized features on `[PROVIDER_ID, SVC_DT_M]`
3. Join num-hospitalized-patient counts on `[PROVIDER_ID, COHORT]`
4. Both join on `HCP_COHORT_ID`
5. **PX adds `_PX` suffix** to all non-key columns to avoid name collisions with DX

### Hard Constraints vs Tunable Parameters

| Parameter | Value | Type |
| --- | --- | --- |
| Applicable sources | DX, PX only | **Hard** |
| Event collapse | Single `ALL_DIAGNOSIS` / `ALL_PROCEDURES` | **Hard** |
| Validation filter | TOTAL >= HOSPITALIZED | **Hard** |
| Percent formula | HOSP / TOTAL WHEN TOTAL != 0 ELSE NULL | **Hard** |
| Lag windows | `[1, 6, 12]` months | **Tunable** |
| Patient count windows | `[30, 180, 360]` days | **Tunable** |
| PX suffix | `_PX` on non-key columns | **Hard** (convention) |

---

## 7. Performance Guidance for ~100B Rows

### 7.1 Pre-Aggregation Before Cohort Expansion

The single most impactful pattern for any feature that needs a per-HCP aggregate before
cross-joining with cohort dates. The core principle: collapse ~100B raw claims to a narrow
per-HCP (or per-HCP-event) intermediate **before** attaching cohort dates, so the cross-join
operates on millions of rows rather than 100B.

First Occurrence already uses this as its default method -- see Section 3 for the full
step-by-step. The same pattern applies wherever an aggregate over raw claims must then be
repeated across cohorts:

**Recency `min(EVENT_TIME)` (Sub-feature 1):** Pre-aggregate raw claims to
`(PROVIDER_ID, EVENT_NAME, LATEST_EVENT_DATE)` using `groupBy(PROVIDER_ID, EVENT_NAME).agg(max(EVENT_DATE))`
before the cohort cross-join, then compute `EVENT_TIME = datediff(LOOKBACK_END_DATE, LATEST_EVENT_DATE)`.
This avoids attaching cohort rows to every individual claim before finding the most recent one.

General rule: if the computation is `agg(f(EVENT_DATE))` per `(PROVIDER_ID, EVENT_NAME)`, it
can always be pre-aggregated. The cross-join that would be 100B x N_cohorts becomes
millions x N_cohorts.

### 7.2 Broadcast Joins vs Shuffle Joins

| Table | Typical Size | Join Strategy |
| --- | --- | --- |
| Cohort anchor dates CSV | ~100 rows | **Broadcast** always |
| HCP universe | ~100K rows | **Broadcast** if < 10MB |
| Event prevalence filter | ~hundreds of events | **Broadcast** |
| NPI crosswalk | ~1M rows | **Broadcast** if memory allows |
| Claims x claims joins | 100B+ rows | **Shuffle** (never broadcast) |

```python
# Small dimension: broadcast
claims = claims.join(F.broadcast(anchor_dates), ...)

# Large fact-to-fact: let Spark shuffle
result = big_df1.join(big_df2, on="key", how="inner")
```

### 7.3 Caching and Persisting

| Intermediate | Action | Why |
| --- | --- | --- |
| Dense spine (after `fill_missing`) | `cache()` | Read N times by `step3_lag` (once per window) |
| Standardized claims | `persist(DISK_ONLY)` | Reused across feature types; too large for memory |
| Batch results (before union) | No cache -- write to Delta immediately | Frees memory |
| Pivoted result | No cache -- write immediately | Wide DataFrame, expensive to cache |

**Rule of thumb:** `cache()` for DataFrames read 2+ times in the same action chain.
`persist(DISK_ONLY)` for DataFrames reused across separate feature computations.
Never cache a wide pivoted result -- write it to storage instead.

### 7.4 Write Intermediates to Parquet / Delta

When a pipeline stage produces a large intermediate that feeds multiple downstream stages,
write it to storage and read it back rather than chaining in memory:

```python
# Bad: chained in memory -- Spark can't optimize across complex stages
result = stage3(stage2(stage1(raw)))

# Better: checkpoint intermediates
stage1_output.write.format("parquet").save(intermediate_path)
stage1_df = spark.read.parquet(intermediate_path)
stage2_output = stage2(stage1_df)
stage2_output.write.format("delta").save(another_intermediate)
```

**When to do this:**
- After pre-aggregation (before cohort cross-join)
- After `fill_missing` (dense spine is expensive to recreate)
- After any pivot (wide DataFrames are expensive to hold in memory)

### 7.5 Batch Processing by Cohort

The `DataFrameBatchProcessor` splits claims by COHORT suffix into batches of `batch_size`
(default 6). Each batch is processed independently, then merged via
`unionByName(allowMissingColumns=True)`.

**When to increase `batch_size`:** Small cohorts, limited total data -- fewer batches means
less union overhead.

**When to decrease:** OOM on wide pivots -- smaller batches reduce peak memory per stage.

**Key benefit:** Batches with different `EVENT_NAME` values produce different pivot columns.
`allowMissingColumns=True` in the union fills absent columns with null.

### 7.6 Early Column Pruning

Drop non-essential columns **immediately** after load, before any join or aggregation:

```python
claims = claims.select(
    "PROVIDER_ID", "PATIENT_ID", "EVENT_NAME", "EVENT_DATE",
    "EVENT_TYPE", "CLAIM_ID"
)
```

Every extra column in a shuffle stage costs bytes-per-row x number-of-rows. At 100B rows,
dropping 10 unnecessary columns before a shuffle can save terabytes of I/O.

### 7.7 Partitioning Strategy for Final Output

| Output | Partition By | Rationale |
| --- | --- | --- |
| First Occurrence, Recency | `COHORT` | Model training reads one cohort at a time |
| Frequency (monthly grain) | `SVC_DT_M` | Time-series reads slice by month |
| Frequency (cohort grain, Sub-D) | `COHORT` | Same as above |
| Hospitalization | `COHORT` | Same as above |

```python
df.write.format("delta").mode("overwrite")
  .partitionBy("COHORT")
  .save(output_path)
```

Partition pruning on `WHERE COHORT = 'I01'` avoids reading all cohorts.

### 7.8 Avoiding Pivot Explosion

When `EVENT_NAME` cardinality is high (>500 distinct values), the pivot produces a very wide
DataFrame. Controls:

1. **Event prevalence filter** -- `event_prevalence` threshold (e.g., 0.01 = keep events seen
   by >= 1% of HCPs). Primary control for column count.
2. **Bypass list** -- `relevant_rx_events` forces specific events through the filter.
3. **Batch by EVENT_NAME buckets** -- if filter alone is not enough, split events into
   buckets, pivot each separately, then join.

---

## 8. Final Output Schema and Join Strategy

### 8.1 Join Key

All feature outputs share a common key that enables a single unified feature table:

| Feature Type | Key | Grain |
| --- | --- | --- |
| First Occurrence | `HCP_COHORT_ID` | HCP x Cohort |
| Recency | `HCP_COHORT_ID` | HCP x Cohort |
| Frequency Sub-types A-C | `PROVIDER_ID, SVC_DT_M` | HCP x Month |
| Frequency Sub-type D | `PROVIDER_ID, COHORT` | HCP x Cohort |
| Hospitalization Sub-types A-C | `PROVIDER_ID, SVC_DT_M` | HCP x Month |
| Hospitalization Sub-type D | `PROVIDER_ID, COHORT` | HCP x Cohort |

**Unification key:** `HCP_COHORT_ID` = `{PROVIDER_ID}_{COHORT}`

Monthly-grain features (Frequency A-C, Hospitalization A-C) must be joined to cohort anchor
dates to convert `SVC_DT_M` -> `COHORT` -> `HCP_COHORT_ID` before merging with patient-level
features.

### 8.2 Join Strategy

```
Step 1: Build skeleton
  hcp_universe x cohort_anchor_dates -> skeleton(PROVIDER_ID, COHORT, HCP_COHORT_ID, SVC_DT_M)
  (NBA 3.1: hcp_universe = HCP_UNIVERSE_PATH, cohorts = CohortGenerator("claims").load();
   see "HCP universe" at the top of this skill)

Step 2: Join patient-level features (HCP_COHORT_ID grain)
  skeleton LEFT JOIN first_occurrence ON HCP_COHORT_ID
  skeleton LEFT JOIN recency ON HCP_COHORT_ID

Step 3: Join HCP-month features (convert to HCP_COHORT_ID via SVC_DT_M)
  skeleton LEFT JOIN frequency_subABC ON [PROVIDER_ID, SVC_DT_M]
  skeleton LEFT JOIN hospitalization_subABC ON [PROVIDER_ID, SVC_DT_M]

Step 4: Join HCP-cohort features
  skeleton LEFT JOIN frequency_subD ON [PROVIDER_ID, COHORT]
  skeleton LEFT JOIN hospitalization_subD ON [PROVIDER_ID, COHORT]

Step 5: Add source suffixes to avoid collisions
  RX features: no suffix (baseline)
  DX features: no suffix (or _DX if collision)
  PX features: _PX suffix
  Lab features: _LAB suffix
```

### 8.3 Final Output Schema

```
HCP_COHORT_ID          -- composite key: {PROVIDER_ID}_{COHORT}
PROVIDER_ID            -- HCP identifier
COHORT                 -- cohort label (I01, I02, ...)

-- First Occurrence (per source x per event)
max(EVENT_TIME)_{EVENT_NAME}_first_occurrence    -- int (days before anchor)

-- Recency (per source)
min(EVENT_TIME)_{EVENT_NAME}_time_min            -- int (days, most recent)
total_events, unique_events                      -- int
total_events_time_{N}_days, unique_events_time_{N}_days  -- int per window
total_{type}, unique_{type}                      -- int per event type
total_events_time_{N}_days_{type}               -- int per type x window
unique_events_time_{N}_days_{type}              -- int per type x window
skewness_time_{N}_days_{type}                   -- float per type x window

-- Frequency (per source x per event)
FREQ_{EVENT}_IN_LAST_{N}_MONTH                   -- int (rolling sum)
CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_{EVENT}_IN_LAST_{N}_MONTH  -- float
NUM_OF_PATIENTS_..._{EVENT}_IN_LAST_{N}_DAYS     -- int (distinct patients)

-- Hospitalization (DX, PX only)
PERC_HOSPITALIZED_HCP_CLAIMS_FOR_{EVENT}_IN_LAST_{N}_MONTH  -- float (0-1)
TOTAL_HOSPITALIZED_CLAIMS_{EVENT}_IN_LAST_{N}_MONTH         -- int
NUM_OF_HOSPITALIZED_PATIENTS_..._IN_LAST_{N}_DAYS           -- int
```

### 8.4 Output Volume Estimate

| Component | Formula | Approx. Columns |
| --- | --- | --- |
| First Occurrence | 1 per EVENT_NAME x 4 sources | ~53 |
| Recency (sub-features 1-6) | ~94 + per-event columns | ~94 + ~53 |
| Frequency (Sub-types A-D) | 4 sub-types x per-event x per-window | ~500+ |
| Hospitalization (Sub-types A-D) | DX + PX, collapsed events | ~30 |
| **Total** | | **~700+** |

---

## 9. Parameter Summary

| Parameter | Location | Default | Scope | Tunable? |
| --- | --- | --- | --- | --- |
| `cohort_start_date` | `00_config` | -- | All features | Yes |
| `cohort_end_date` | `00_config` | -- | All features | Yes |
| `months_increment` | `00_config` | `2` | All features | Yes |
| `lookback_duration` | `00_config` | `365` (days) | All features | Yes |
| `prediction_duration` | `00_config` | `90` (days) | Labels (not features) | Yes |
| `event_prevalence` | `00_config` | **Removed in 3.1** (replaced by event list) | -- | No |
| `relevant_rx_events` | `00_config` | **Removed in 3.1** (replaced by event list) | -- | No |
| `time_windows` (recency) | `00_config` | `[30, 60, 90, 180, 270, 360]` | Recency | Yes |
| Lag windows (freq) | inline in notebooks | `[1, 2, 3, 6, 12]` | Freq Sub-B, Hosp Sub-B | Yes |
| Change windows (freq) | inline in notebooks | `[1, 2, 3, 6]` | Freq Sub-C | Yes |
| Patient count windows (freq) | inline in notebooks | `[30, 60, 90, 180, 360]` | Freq Sub-D | Yes |
| Hosp patient count windows | inline in notebooks | `[30, 180, 360]` | Hosp Sub-D | Yes |
| `batch_size` | `DataFrameBatchProcessor` | `6` | First Occ, Recency | Yes |
| `cohort_day_offset` | `00_config` | `1` | All features (opt-in) | Yes |
| `FEATURE_FAMILY` (NBA 3.1) | Generated notebook, after the `%run` | `"claims"` (this skill is claims-type) | `CohortGenerator("claims").load()` | No -- fixed for this skill |
| `CLAIMS_ANCHOR_OFFSET_DAYS` (NBA 3.1) | `00_cohort_generation` | `0` (month boundaries) | All notebooks from this skill | Yes -- in `00_cohort_generation` only, then re-run it |
| `OFFSET_DAY` (NBA 3.1) | base `00_cohort_config` | `7` (base value) | Not used by notebooks from this skill -- cohorts come only from `CohortGenerator("claims").load()` | No |
| `DATA_START_DATE` (NBA 3.1) | `00_cohort_config` | `2023-01-01` | Patient journey inputs | Yes |
| `COHORT_ORIGIN` / `COHORT_LAST` (NBA 3.1) | `00_cohort_config` | `2025-01-01` / `2026-10-01` | Base C1..C22 list -- NOT the 3.1 schedule; this skill uses c1..c28 from `CohortGenerator("claims").load()` | No |
| `COHORT_1_PREDICTION_MONTH` / `LOOKBACK_WINDOW_MONTHS` / `DATA_LAG_MONTHS` (NBA 3.1) | `00_cohort_generation` | `2024-07-01` / `12` / `1` | The 28-cohort schedule (c1-c28) | Yes -- in `00_cohort_generation` only, then re-run it |
| `LOOKBACK_WINDOWS` / `AVG_EXTRA_MONTH` (NBA 3.1) | `00_cohort_config` | `[1, 3, 6, 9, 12]` / `True` | HCP windowed + AVG features | Yes |
| `VALIDATION_MODE` (NBA 3.1) | `00_cohort_config` | `True` (10 test NPIs) | All 3.1 notebooks | Yes |
| `COHORT_CONFIG_PATH` (NBA 3.1) | Skill, Section 2 | `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_1_develop_sa/NBA 3.1 - Dev/00_Helper_Notebooks/00_cohort_generation` | `%run` target of every 3.1 notebook | Yes -- literal path |
| `COHORT_VOLUME_ROOT` (NBA 3.1) | `00_cohort_generation` | `kerendia_nba_3_1_volume/cohorts/<family>/cohorts.parquet` + `metadata.json` | `CohortGenerator(...).load()` | No (set in config) |
| `EVENT_LIST_CONFIG_PATH` (NBA 3.1) | Skill, Section 1.5 | `/Users/wenjie.chen@bayer.com/kerendia_nba_3_1_develop_sa/NBA 3.1 - Dev/02_Input_Data_Creation/00_event_list_config` | `%run` target of every 3.1 notebook (loads event lists + helpers) | Yes -- literal path |
| `INPUT_PATHS_31` (NBA 3.1) | `00_event_list_config` | Nine Delta tables in `kerendia_nba_3_1_volume/hcp_level_model/ops_pipeline/query_output/` (written 2026-10-28) | Primary input source — always use this; see Section 2.1 | No (set in config) |
| `TEST_HCP_SAMPLE` | Notebook widget | `500` (0 = full universe) | Test runs (Section 12.2) | Yes |
| `rx_file_path` | `INPUT_PATHS_31["rx_all"]` | `rx_all` for First Occ + Recency; `rx_12m` for Frequency | Yes |
| `dx_file_path` | `INPUT_PATHS_31["dx_full_history"]` | `dx_full_history` for First Occ; `dx_12m` for Recency/Frequency; `dx_hosp` for Hospitalization | Yes |
| `px_file_path` | `INPUT_PATHS_31["px_all"]` | All PX First Occ, Recency, and Frequency features; `px_hosp` for Hospitalization | Yes |
| `lab_file_path` | `INPUT_PATHS_31["lab"]` | All Lab features | Yes |
| `output_base_path` | Section 2.1 | `kerendia_nba_3_1_volume/notebook_output/patient_features/{rx\|dx\|px\|lab}/` | All feature outputs | Yes |
| `anchor_dates_path` | Section 2.1 | `{output_base_path}/hcp_model_inference_anchor_dates.csv` | All features | Yes |
| `HCP_UNIVERSE_PATH` (NBA 3.1) | Skill, "HCP universe" section at the top | `kerendia_nba_3_1_volume/HCP_Universe` (folder, 314,920 HCPs) | Claims filter, skeleton, test sample, output check -- every feature | Only when the universe is rebuilt |
| `hcp_universe_path` (3.0) | `00_config` | `notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` | Not used in NBA 3.1 -- replaced by `HCP_UNIVERSE_PATH` | No |

See Section 2.1 for full default file paths. Do NOT leave path variables as empty strings.

---

## 10. Custom Cohort Date Boundaries

By default, cohorts align to calendar months: each "month" runs from the 1st to the last
day of the month, and `SVC_DT_M = date_trunc('MM', EVENT_DATE)` snaps events to the 1st. When
`cohort_day_offset` is set to a value other than `1`, cohort boundaries shift to custom-month
windows. For example, `cohort_day_offset = 15` means each custom-month runs from the 15th of
one calendar month to the 14th of the next.

Cohorts snap to actual calendar dates -- each cohort's length equals the real number of days
between its start and end. Jan 15 to Feb 14 is 31 days, Feb 15 to Mar 14 is 28 days (or 29
in a leap year), Mar 15 to Apr 14 is 31 days. Cohorts are NOT fixed 30-day windows that drift
from the calendar; users can always point at a cohort and say "that is the 15th of month X
to the 14th of month X+1."

### 10.1 Configuration

A single parameter controls the behavior:

| Parameter | Default | Description |
| --- | --- | --- |
| `cohort_day_offset` | `1` | Day of month that starts each custom-month. `1` = calendar month (backward compatible). Valid range: 1-28. |

**Why 1-28:** Every calendar month has days 1-28, so offsets in this range guarantee that
the boundary day always exists. Offsets 29-31 are problematic because February (and some
months in 30-day calendars) lack those days. Use offset 28 if you need the latest possible
start date.

The offset feeds into two derivations:

**LOOKBACK_END_DATE:**

```
# Default (offset=1): last day of month, 2 months before anchor
# Custom (offset=D): last day of custom-month, 2 custom-months before anchor

custom_month_start = when(dayofmonth(anchor) >= offset,
                          date_add(date_trunc('MM', anchor), offset - 1))
                    .otherwise(
                          date_add(add_months(date_trunc('MM', anchor), -1), offset - 1))

LOOKBACK_END_DATE = date_sub(add_months(custom_month_start, -1), 1)
```

In plain terms: `LOOKBACK_END_DATE = add_months(anchor_custom_month_start, -2) - 1 day`.
Equivalently, go to the start of the custom-month that contains the anchor, step back 2
custom-months, then subtract 1 day to land on the last day of that earlier custom-month.

Example with `offset=15`, anchor = `2024-04-15`:
- Custom-month start = `2024-04-15`
- `add_months(2024-04-15, -1)` = `2024-03-15`
- `LOOKBACK_END_DATE = date_sub(2024-03-15, 1)` = `2024-03-14`

**LOOKBACK_START_DATE:** `LOOKBACK_END_DATE - lookback_duration` days -- unchanged from the
default pipeline. The start date is always a fixed day-count back from the end date, not a
custom-month boundary. This is intentional: the lookback window is a rolling N-day history
ending at `LOOKBACK_END_DATE`, not a fixed number of custom-months. Only `LOOKBACK_END_DATE`
shifts with the offset; `LOOKBACK_START_DATE` follows it by simple subtraction.

**SVC_DT_M (custom-month bucket):**

The standard `date_trunc('MM', EVENT_DATE)` is replaced with a custom bucketing function:

```python
def custom_month_bucket(event_date, offset):
    """Assign event_date to its custom-month bucket start date.

    With offset=1: equivalent to date_trunc('MM', event_date).
    With offset=15: April 20 -> April 15 (belongs to Apr 15 to May 14 bucket).
                    April 10 -> March 15 (belongs to Mar 15 to Apr 14 bucket).
    """
    month_start = F.date_trunc('MM', event_date)
    return F.when(
        F.dayofmonth(event_date) >= offset,
        F.date_add(month_start, offset - 1)
    ).otherwise(
        F.date_add(F.add_months(month_start, -1), offset - 1)
    )
```

Verification: offset=1, event on April 20 -> dayofmonth=20 >= 1 ->
date_add(2024-04-01, 0) = 2024-04-01. Matches `date_trunc('MM')`. Backward compatible.

### 10.2 Affected Feature Types

Custom bucketing affects only features that use `SVC_DT_M` as a grouping or ordering key:

| Feature Type | Uses SVC_DT_M? | Impact |
| --- | --- | --- |
| First Occurrence | No | None -- uses `EVENT_TIME` (days since anchor) |
| Recency | No | None -- uses `EVENT_TIME` (days since anchor) |
| Frequency Sub-A (Claim Count) | **Yes** | `groupBy(PROVIDER_ID, SVC_DT_M)` -- bucket assignment changes |
| Frequency Sub-B (Lag) | **Yes** | `fill_missing` + `lag` -- spine generation and window ordering change |
| Frequency Sub-C (Change) | **Yes** | Inherits from Sub-B -- denominator semantics affected (see 10.4) |
| Frequency Sub-D (Patient Counts) | No | Uses `COHORT` and `days_diff` -- not bucketed by month |
| Hospitalization Sub-A (Counts) | **Yes** | Same as Frequency Sub-A |
| Hospitalization Sub-B (Lag) | **Yes** | Same as Frequency Sub-B |
| Hospitalization Sub-C (% Hosp) | **Yes** | Inherits from Sub-B |
| Hospitalization Sub-D (Hosp Patients) | No | Uses `COHORT` and `days_diff` -- not bucketed by month |

### 10.3 Changes to Monthly Bucketing

**Sub-types A (Claim Count):** Replace `date_trunc('MM', EVENT_DATE)` with
`custom_month_bucket(EVENT_DATE, offset)` in the `withColumn("SVC_DT_M", ...)` step.
Everything else -- the pivot, column sanitization, prefix -- stays the same.

**Sub-types B (Lag):** Two changes:

1. **Dense spine generation:** The `fill_missing` function generates a date sequence via
   `sequence(min_date, max_date, interval 1 month)`. Since `SVC_DT_M` now contains custom
   bucket dates (e.g., `2024-01-15`, `2024-02-15`, ...), the sequence produces the correct
   custom-month boundaries. Spark's `add_months` handles variable-length months correctly
   when incrementing by 1 month from a fixed day-of-month.

2. **Window ordering:** `Window.partitionBy(PROVIDER_ID).orderBy(SVC_DT_M)` still works
   correctly -- the custom bucket dates are monotonically increasing and properly ordered.

The `rowsBetween(-i+1, 0)` clause counts N rows back, which now corresponds to N
custom-months rather than N calendar months. This is the desired behavior: "last 3 months"
means "last 3 custom-months" regardless of their day counts.

### 10.4 Variable-Length Cohorts and Rolling Windows

Each custom-month spans a variable number of days:

| Custom-Month | Day Count |
| --- | --- |
| Jan 15 to Feb 14 | 31 |
| Feb 15 to Mar 14 | 28 (or 29 in leap year) |
| Mar 15 to Apr 14 | 31 |
| Apr 15 to May 14 | 30 |

The lag windows (`[1, 2, 3, 6, 12]` months) mean "last N custom-months." A 3-month lag
window covering Feb 15 to May 14 spans 28+31+30 = 89 days (or 90 in a leap year), while the
next 3-month window (Mar 15 to Jun 14) spans 31+30+31 = 92 days. The raw event counts in
these windows will differ partly due to the day-count variation.

**Impact on Change-in-Frequency (Sub-type C):**

The formula normalizes by month count, not day count:

```
CHANGE = (FREQ_IN_LAST_N / N) - ((FREQ_IN_LAST_12 - FREQ_IN_LAST_N) / (12 - N))
```

Here, `N` is the number of custom-months (e.g., 3), not days. The comparison is "average
events per custom-month" in the recent window vs the remainder. Since custom-months vary by
+/-3 days (28-31), the per-month rate has a small day-count bias:

- A 1-month window in February (28 days) will tend to have slightly fewer events than a
  1-month window in March (31 days), even if the daily rate is identical.
- This bias is ~10% at most (28/31 = 0.90) and is the same bias that exists with calendar
  months in the default mode.

**When this matters:** If precise per-day normalization is needed, replace the denominator
with actual day counts:

```
CHANGE_PER_DAY = (FREQ_IN_LAST_N / days_in_window)
               - ((FREQ_IN_LAST_12 - FREQ_IN_LAST_N) / (days_in_12M - days_in_window))
```

where `days_in_window` is computed from the custom-month boundaries. This changes the feature
semantics (per-day rate vs per-month rate) and should be a deliberate choice. The default
per-month normalization is recommended for consistency with the existing pipeline.

**No impact on First Occurrence, Recency, Freq Sub-D, and Hosp Sub-D:**

These features use `EVENT_TIME` (days since anchor) or `days_diff` (days from lookback end),
both of which are day-based and independent of monthly bucketing. Only `LOOKBACK_END_DATE`
must be set correctly from the custom boundary (Section 10.1 formula).

### 10.5 What Stays Unchanged

| Component | Why it is unaffected |
| --- | --- |
| First Occurrence logic | `max(EVENT_TIME)` per `HCP_COHORT_ID` -- `EVENT_TIME` is day-based. **Note:** the computation logic is unchanged, but output values will differ from the default because `LOOKBACK_END_DATE` moves with the offset -- every `EVENT_TIME = datediff(LOOKBACK_END_DATE, EVENT_DATE)` shifts by however many days the anchor moved. |
| Recency 12M filter | `EVENT_DATE BETWEEN LOOKBACK_START AND LOOKBACK_END` -- uses dates, not buckets. **Note:** same caveat -- the filter bounds shift with `LOOKBACK_END_DATE`, so the 12M window covers a different calendar range and all time-window/skewness outputs will differ. |
| Recency time windows | `[30, 60, 90, 180, 270, 360]` are in days, not months |
| Recency skewness | `skewness(EVENT_TIME)` -- `EVENT_TIME` is day-based |
| Freq Sub-D patient counts | `days_diff` + day-based window flags -- not bucketed by month |
| Hosp Sub-D patient counts | Same as Freq Sub-D |
| Column naming conventions | Unchanged -- `_IN_LAST_{N}_MONTH` still refers to N custom-months |
| Column sanitization rules | Unchanged |
| Event prevalence filter | Unchanged |
| Batch processing | Unchanged -- batches by COHORT suffix, not by month |
| Performance patterns | Unchanged -- pre-aggregation, broadcast joins apply. **Note:** `.cache()`/`.persist()` NOT supported on serverless (see Section 11). |

### 10.6 Backward Compatibility

`cohort_day_offset = 1` (default) reproduces the existing calendar-month behavior exactly:

| Derivation | offset=1 | Equivalent to |
| --- | --- | --- |
| Custom bucket | `date_add(date_trunc('MM', dt), 0)` | `date_trunc('MM', dt)` |
| LOOKBACK_END_DATE | `date_sub(add_months(date_trunc('MM', anchor), -1), 1)` | last day of month, 2 months before anchor |

No code changes are needed when `cohort_day_offset` is not set or is set to `1`. Custom
offsets are purely opt-in.

### 10.7 Edge Cases

**Short months (February):**

With `offset=15`, the custom-month Feb 15 to Mar 14 is 28 days (or 29 in a leap year),
shorter than the 30-31 day span of other custom-months. This affects:

- Lag window raw counts: A 1-month lag in February captures 3 fewer days than in March.
- Change-in-frequency: The per-month normalization absorbs this -- the denominator is N=1
  regardless of day count. The per-day bias is ~10% at worst.
- Dense spine: `sequence(min_date, max_date, interval 1 month)` correctly generates
  Feb 15 and Mar 15 as consecutive bucket dates regardless of February's length.

**Year-end rollover (Dec 15 to Jan 14):**

`add_months` handles year boundaries correctly:
- `add_months('2024-12-15', 1)` = `2025-01-15`
- `add_months('2025-01-15', -1)` = `2024-12-15`

The `sequence()` function and custom bucketing both rely on `add_months`, so year-end
rollovers work without special handling.

**Leap years:**

With `offset=15`, the custom-month Feb 15 to Mar 14 is 29 days in a leap year (e.g., 2024)
vs 28 days in a non-leap year (e.g., 2025). This means the same lag window covers one more
day of data in leap years. The impact is negligible for feature semantics and is the same
effect that exists with calendar-month bucketing (February has 28/29 days).

**Offset on day 29-31:**

Not recommended. February never has day 29-31 (except Feb 29 in leap years), so
`date_add(date_trunc('MM', '2024-02-01'), 28)` = Feb 29 in a leap year but would need
special handling in non-leap years. Restrict `cohort_day_offset` to 1-28 for safety.

### 10.8 NBA 3.1 Canonical Offset Logic (`00_cohort_config`)

NBA 3.1 replaces the per-notebook bucketing above with one shared config notebook.
Notebooks from this skill load it through the shared config (`COHORT_CONFIG_PATH`, see
Section 2): `.../NBA 3.1 - Dev/00_Helper_Notebooks/00_cohort_generation`. That notebook
`%run`s the base `00_cohort_config` and holds the per-family offsets and the saved 28-cohort
schedule. Because this is a claims-only skill, every notebook gets its cohorts with the
loading idiom at the top of this skill (`CohortGenerator("claims").load()`) and never calls
the base primitives. Every notebook `%run`s `COHORT_CONFIG_PATH` AFTER `00_connection`
(which may restart Python) -- never a local copy of the cohort formulas. Sections 10.8.1 and
the labeling note below describe the base `00_cohort_config` for background only.

#### 10.8.1 Parameters and mapping to `cohort_day_offset`

| `00_cohort_config` | Meaning | Equivalent in Sections 10.1-10.7 |
| --- | --- | --- |
| `OFFSET_DAY = 0` (or 1) | Calendar months | `cohort_day_offset = 1` |
| `OFFSET_DAY = D` (2-28) | The D-th of each month starts the NEW cohort | `cohort_day_offset = D` |
| `DATA_START_DATE` | Earliest claim date read by the patient journey | -- |
| `COHORT_ORIGIN`, `COHORT_LAST` | Reference months of C1 and the last cohort | `cohort_start_date`, `cohort_end_date` |
| `LOOKBACK_WINDOWS`, `AVG_EXTRA_MONTH` | Window sizes in cohort-months; AVG uses N+1 months | Lag windows |

**Labeling convention (critical for joins):** 3.1 labels a cohort-month by the **1st of its
reference month** (`2025-02-01` = the Feb cohort, Feb 7 to Mar 6 at offset 7). This differs
from `custom_month_bucket`, which labels by the bucket START date (`2025-02-07`). All 3.1
patient tables (`DATE`, `SVC_DT_M`) and HCP outputs (`COHORT_MONTH`, `SVC_DT_M`) use the
1st-of-month label, so `custom_month_bucket` output will NOT join to them.

#### 10.8.2 Core rules (claims family)

Every cohort date comes from the `cohorts` DataFrame returned by the loading idiom (top of
this skill), reproduced here exactly:

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_1_develop_sa/NBA 3.1 - Dev/00_Helper_Notebooks/00_cohort_generation"

FEATURE_FAMILY = "claims"   # this skill's family — do not change
cohorts = CohortGenerator(FEATURE_FAMILY).load()
# cohorts is a 28-row DataFrame with: cohort_id, prediction_month, dataset,
# offset_days (=0), lookback_start_date, lookback_end_date
```

| Rule | Claims definition (offset 0, month boundaries) | Source |
| --- | --- | --- |
| Cohort key | `cohort_row["cohort_id"]` (`c1`..`c28`); `HCP_COHORT_ID = {PROVIDER_ID}_{cohort_id}` | `load()` |
| Model split | `cohort_row["dataset"]`: Training c1-c24, Testing c25-c26, Holdout (Backtesting) c27-c28 | `load()` |
| Lookback window | Calendar months `lookback_start_date` .. `lookback_end_date`, **both included** (12 months) | `load()` |
| Last included day | Last day of the `lookback_end_date` month: `F.date_sub(F.add_months(F.lit(cohort_row["lookback_end_date"]), 1), 1)` (c1: 2024-05-31) | Derived. TODO: expose via CohortGenerator |
| Data lag | `lookback_end_date` = `prediction_month` - 2 months. The month in between (c1: June 2024) is the claims data lag and is never used | `load()` |
| Monthly grain `SVC_DT_M` | 1st of the claim's calendar month (claims offset 0) | TODO: expose via CohortGenerator (see below) |
| `N`-month lag window | The last N months ending with the `lookback_end_date` month: `EVENT_DATE >= add_months(lookback_end_date, -(N-1))` and `< add_months(lookback_end_date, 1)` | Derived. TODO: expose via CohortGenerator |
| AVG window | N+1 months ending with the `lookback_end_date` month, zero-filled, divided by N+1 | Derived. TODO: expose via CohortGenerator |
| RUNNING_ | All history with `EVENT_DATE < add_months(lookback_end_date, 1)` | Derived from `load()` |
| Cohorts processed | All 28 rows. Skip a cohort only if its last included day is after the last claim date (`cohorts[...]` pandas filter) | `load()` |

> **TODO: expose via CohortGenerator.** The base primitives used to provide the monthly-grain
> function and the N-month / AVG window bounds. `CohortGenerator` does not expose them yet.
> Until it does, derive them from the `cohorts` columns as in the table above. For
> `SVC_DT_M`, use `F.trunc("EVENT_DATE", "month")`: at the claims offset (0) the cohort month
> is the calendar month, so this is the same label. Do NOT fall back to calling the
> primitives. Proposed additions: `CohortGenerator("claims").assign_month(col)`,
> `.last_included_day(cohort_row)` and `.window(cohort_row, n_months, avg=False)`.

**Worked example -- c1** (`prediction_month` 2024-07-01, Training, lookback 2023-06-01 to
2024-05-01):

| Window | Claims counted | AVG window (divide by) |
| --- | --- | --- |
| 1M | 2024-05-01 to 2024-05-31 | 2024-04-01 to 2024-05-31 (/2) |
| 3M | 2024-03-01 to 2024-05-31 | 2024-02-01 to 2024-05-31 (/4) |
| 6M | 2023-12-01 to 2024-05-31 | 2023-11-01 to 2024-05-31 (/7) |
| 12M (full lookback) | 2023-06-01 to 2024-05-31 | 2023-05-01 to 2024-05-31 (/13) |

A claim on 2024-05-31 is in c1's lookback; a claim on 2024-06-01 is not (June is the data lag).

#### 10.8.3 Applying it to patient features

Start from the loading idiom, then loop over the rows of `cohorts`:

| Patient-feature concept | 3.1 claims definition |
| --- | --- |
| `LOOKBACK_START_DATE` | `cohort_row["lookback_start_date"]` (first included day) |
| `LOOKBACK_END_DATE` | `cohort_row["lookback_end_date"]` = 1st of the LAST included month. It is not a cutoff day. |
| `EVENT_TIME` | `datediff(last included day, EVENT_DATE)`, keep `EVENT_TIME >= 0` (last included day per 10.8.2) |
| `SVC_DT_M` (monthly grain) | 1st of the calendar month (10.8.2, TODO note) |
| Lag / `_IN_LAST_{N}_MONTH` | Date-range filter for the N-month window in 10.8.2 (equivalent to `rowsBetween(-N+1, 0)` only on a dense monthly spine) |
| Month spine | `F.sequence(F.lit(add_months(lookback_start_date, -(max lag - 1))), F.lit(cohort_row["lookback_end_date"]), F.expr("interval 1 month"))` |
| Day-based features (Recency windows, Freq/Hosp Sub-D) | Unchanged; measured back from the last included day |
| Prediction / target window | `cohort_row["prediction_month"]` (2 months after `lookback_end_date`), so the features never overlap the target |

##### Filtering claims to the lookback window

The claims cohort uses month-boundary semantics. `lookback_end_date = 2024-05-01` means "all
of May 2024 is included." Filter claims as:

```python
df.filter(
    (F.col("EVENT_DATE") >= cohort_row["lookback_start_date"]) &
    (F.col("EVENT_DATE") < F.add_months(F.lit(cohort_row["lookback_end_date"]), 1))
)
```

Do not use `<= lookback_end_date` -- that would exclude all of May's claims except May 1. The end date is
the first day of the last INCLUDED month, not the last included day. (Equivalently, the
first EXCLUDED day is `add_months(lookback_end_date, 1)`.)

Full loop, after the loading idiom:

```python
from pyspark.sql import functions as F

for _, cohort_row in cohorts.iterrows():
    in_window = (claims
        .filter((F.col("EVENT_DATE") >= cohort_row["lookback_start_date"]) &
                (F.col("EVENT_DATE") < F.add_months(F.lit(cohort_row["lookback_end_date"]), 1)))
        .withColumn("COHORT", F.lit(cohort_row["cohort_id"])))
    # ... build features for this cohort; write with replaceWhere COHORT = cohort_row["cohort_id"]
```

#### 10.8.4 Mandatory rules (claims family)

1. **Cohorts come only from the loading idiom.** No hard-coded cohort dates or offsets, no
   `00_config` anchor dates, no direct calls to the base primitives (see Section 12.9). Use
   only the `cohorts` columns `cohort_id`, `prediction_month`, `dataset`, `offset_days`,
   `lookback_start_date` and `lookback_end_date`.
2. **Month-boundary windows.** Every window filter uses `>= start` and
   `< add_months(lookback_end_date, 1)` ("Filtering claims to the lookback window"). Never
   `<= lookback_end_date`.
3. **One month grain everywhere.** Every month label (`SVC_DT_M`, and flags derived from
   dates such as `FIRST_DIALYSIS_DATE` in `06_patient_journey_combine`) uses the claims monthly
   grain from 10.8.2. Patient tables (`pat_new_and_total_treatments`, `pat_new_ckd_stage`,
   `pat_gfr_dx_stage...`, `pat_uacr_stage...`) are joined on `(PATIENT_ID, SVC_DT_M)` and must be
   built on the same month grain. Tables built by the offset-7 notebooks (the base
   `00_cohort_config` / `*_Patient_Features_offset`) still join, but they put days 1-6 of a
   month into the previous month. Never mix them in.
4. **Apply `DATA_START_DATE` after forward-fill, not before**, for stage-carrying journeys
   (labs, dx); otherwise stages from earlier tests are lost and every patient looks "new" in
   the first cohort.
5. **RUNNING_ history and patient-table history must cover the same period.** A claim older
   than the patient journey's first month finds no patient row and falls into
   `NO_ACTIVE_TREATMENT` / `NO_NEW_TREATMENT`.
6. **History coverage:** input claims must start on or before
   `cohorts["lookback_start_date"].min()` (2023-06-01), minus the longest lag/AVG window if
   lag features reach before the lookback start.
7. **Overwrite only your cohort partitions** (`replaceWhere COHORT = '<cohort_id>'`) and
   remove partitions from older cohort schemes (e.g. `{YYYY-MM}_offset7` ids) before downstream use.

#### 10.8.5 Correct execution order

1. Run `00_cohort_generation` once (it saves the claims cohorts). Set `DATA_START_DATE` and
   `VALIDATION_MODE` in the base `00_cohort_config`.
2. Patient journey `01_labs`, `02_dx`, `03_rx`, `04_t2d_flag`, `05_px` (independent).
3. `06_patient_journey_combine` (needs all five).
4. HCP `01_claim_rx` (needs `pat_new_and_total_treatments`), `03_claim_diagnosis` (needs
   `pat_new_ckd_stage`), `04_claims` (needs GFR/UACR stage tables).
5. HCP `02_claim_lab` and `05_claim_rx_nps` (no patient-table dependency) -- any time.
6. Patient feature notebooks (First Occ / Recency / Frequency / Hosp): the loading idiom, then
   the loop in 10.8.3.

#### 10.8.6 Verification checks

```python
# Run right after the loading idiom (cohorts = CohortGenerator(FEATURE_FAMILY).load()).

# 1) Right family, right schedule
meta = cohorts.attrs["metadata"]                       # metadata.json, attached by load()
assert FEATURE_FAMILY == "claims" and meta["feature_family"] == "claims" and meta["offset_days"] == 0
assert list(cohorts["cohort_id"]) == [f"c{i}" for i in range(1, 29)]
c1 = cohorts.iloc[0]
assert (str(c1["lookback_start_date"]), str(c1["lookback_end_date"])) == ("2023-06-01", "2024-05-01")

# 2) Month-boundary filter: the last day of the end month is in, the 1st of the next month is out
test = spark.createDataFrame([("2024-05-31",), ("2024-06-01",)], "d string").select(F.to_date("d").alias("EVENT_DATE"))
kept = test.filter((F.col("EVENT_DATE") >= c1["lookback_start_date"]) &
                   (F.col("EVENT_DATE") < F.add_months(F.lit(c1["lookback_end_date"]), 1)))
assert [str(r.EVENT_DATE) for r in kept.collect()] == ["2024-05-31"]

# 3) Patient journey built on the claims month grain: events on days 1-6 sit in their OWN
#    calendar month (an offset-7 journey would put them in the previous month)
early = raw_dx.filter(F.dayofmonth("SVC_DT") < 7)
chk = (early.withColumn("_M", F.trunc("SVC_DT", "month"))
       .join(dx_journey.select("PATIENT_ID", F.col("DATE").alias("_M"),
                               F.size("DX_STAGE").alias("_n")), ["PATIENT_ID", "_M"], "left"))
assert chk.filter("_n IS NULL OR _n = 0").count() == 0, "journey not built on the claims month grain"

# 4) Output cohorts are exactly the loaded cohort ids
out_ids = {r.COHORT for r in out.select("COHORT").distinct().collect()}
assert out_ids <= set(cohorts["cohort_id"]), f"unexpected cohorts: {out_ids - set(cohorts['cohort_id'])}"

# 5) Every output HCP is in the HCP universe (see "HCP universe" at the top of this skill)
n_outside = out.select("PROVIDER_ID").distinct().join(hcp_universe, "PROVIDER_ID", "left_anti").count()
assert n_outside == 0, f"{n_outside} PROVIDER_IDs are not in the HCP universe"
```

Regression test for any change to the cohort schedule: re-run `00_cohort_generation` (its
own validation checks the 28 rows, the split and the c1 dates), then re-run check 1 above.

---

## 11. Serverless Compute and Delta Lake Constraints

When generating notebooks for **Databricks Serverless compute**, the following constraints
apply. Violating any of these causes runtime errors. All notebooks generated from this
skill MUST comply with these rules.

### 11.1 Serverless-Incompatible APIs

| API | Error | Replacement |
| --- | --- | --- |
| `.cache()` | `NOT_SUPPORTED_WITH_SERVERLESS: PERSIST TABLE is not supported` | Remove entirely -- recompute as needed |
| `.persist()` | Same as above | Same -- remove entirely |
| `.unpersist()` | Same as above | Same -- remove entirely |
| `F.count("*")` inside `.pivot().agg()` | `INVALID_USAGE_OF_STAR_OR_REGEX` | Use `F.count(F.lit(1))` |
| `F.count("*")` inside regular `.groupBy().agg()` | **OK** -- only fails inside pivot | No change needed |

**Where these commonly appear:**
* `process_and_join()` in Frequency Sub-B: `filled.cache()` before lag computation -- remove the cache and unpersist calls
* `fill_missing_hosp()` in Hospitalization Sub-B: `hosp_filled.cache()` before lag -- same fix
* All pivot operations (First Occurrence, Recency Sub-1, Frequency Sub-A/D, Hospitalization Sub-A): use `F.count(F.lit(1))` or `F.sum(...)`, never `F.count("*")`

### 11.2 Delta Column Naming Rules

Delta column names MUST NOT contain any of: ` ,;{}()\n\t=`

Event names from source data frequently contain these characters:
* Spaces: `METFORMIN ER`, `TYPE 2 DIABETES`
* Parentheses: `METFORMIN ER (F)`, `INSULIN ASP (MIX)`
* Slashes: `AMLODIP/VALSAR`, `HUMALOG 75/25`
* Plus signs: `HUMALOG 50+50`

**All pivoted column names must be sanitized** using `sanitize_column_name()` (see
Section 1.3) before writing to Delta. When referencing pivoted columns in code, use
backticks: `F.col(f"\`{col_name}\`")`.

### 11.3 Delta Write Best Practices

| Issue | Cause | Fix |
| --- | --- | --- |
| `DELTA_METADATA_MISMATCH` | Overwriting an existing Delta table whose schema differs from the new data (e.g., after changing column naming) | Add `.option("overwriteSchema", "true")` to ALL `.write.format("delta").mode("overwrite")` calls |
| `DELTA_INVALID_CHARACTERS_IN_COLUMN_NAMES` | Pivoted column names contain spaces, `()`, `/`, etc. | Apply `sanitize_column_name()` to all pivoted columns before write |
| `AnalysisException: partition column not found` | `.partitionBy("COHORT")` but `COHORT` is not in the output schema (e.g., after pivot) | Only `.partitionBy()` on columns that exist in the DataFrame being written |

**Recommended write pattern for all Delta outputs:**
```python
df.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .partitionBy("COHORT")  # ONLY if COHORT exists in df.columns
    .save(output_path)
```

### 11.4 GroupedData is Not a DataFrame

`.groupBy("column")` returns a `GroupedData` object, not a `DataFrame`. `GroupedData`
does not have `.join()`, `.select()`, `.withColumn()`, or other `DataFrame` methods.

**Bug pattern (causes `AttributeError: 'GroupedData' object has no attribute 'join'`):**
```python
# WRONG: groupBy returns GroupedData, not a DataFrame
result = claims.groupBy("HCP_COHORT_ID")
result = result.join(other_df, "HCP_COHORT_ID")  # AttributeError!
```

**Fix:**
```python
# Correct: use select().distinct() to get a DataFrame
result = claims.select("HCP_COHORT_ID").distinct()
result = result.join(other_df, "HCP_COHORT_ID")  # works
```

This pattern commonly appears in Recency Sub-features 3-6 where an empty skeleton
DataFrame is needed for left-joining computed features.

### 11.5 Hospitalization File Loading

Hospitalized claims files (`dx_hosp_file_path`, `px_hosp_file_path`) are
**pre-filtered upstream**. They:

* Contain ONLY hospitalized claims (no `DATA_SOURCE` column exists in the file)
* Do NOT require a `DATA_SOURCE = 'HX'` filter
* Are loaded and `standardize()`d the same way as total claims

**Bug pattern (causes `UNRESOLVED_COLUMN: 'DATA_SOURCE'`):**
```python
# WRONG: hospitalization file has no DATA_SOURCE column
hosp_claims = spark.read.format("delta").load(hosp_file_path)
hosp_claims = standardize(hosp_claims, "dx")
hosp_claims = hosp_claims.filter(F.col("DATA_SOURCE") == "HX")  # UNRESOLVED_COLUMN!
```

**Fix:**
```python
# Correct: load and standardize directly, no filter needed
hosp_claims = spark.read.format("delta").load(hosp_file_path)
hosp_claims = standardize(hosp_claims, "dx")
# No DATA_SOURCE filter -- file is already pre-filtered
```

### 11.6 Column Reference Safety After `standardize()`

`standardize()` keeps only: `PROVIDER_ID`, `PATIENT_ID`, `EVENT_NAME`, `EVENT_DATE`,
`EVENT_TYPE`, `CLAIM_ID`, and `DATA_SOURCE` (if present in the source). All other
columns are dropped.

Any code that references source-specific columns (HCP flags, payer plans, ICD versions,
referring/rendering provider IDs) AFTER `standardize()` will fail with
`UNRESOLVED_COLUMN`. Apply such filters or drops BEFORE `standardize()`, or guard with
`if col in df.columns`.

**HCP flag drops (Hospitalization Sub-A):** The skill mentions dropping HCP flags
(`KERENDIA_FLAG`, `SGLT2_GLP1_FLAG`, etc.) from hospitalized claims. After
`standardize()`, these columns do not exist. The `if flag in df.columns` guard makes
the drop a no-op -- this is defensive coding, not a functional requirement.

---

## 12. Known Gaps and How to Fill Them (2026-10 skill test)

These came from generating the RX/DX/PX/LAB offset-7 notebooks
(`NBA 3.1 - Dev/03_patient_features/*_offset`) from this skill alone and running them as a job.

### 12.1 Cohort config path

**Gap:** the config path in Section 10.8 no longer exists. **Fix:** `%run` the
`COHORT_CONFIG_PATH` from Section 2 (`00_cohort_generation`), in its own cell, before any
helper notebook, using the loading idiom at the top of this skill exactly. The `cohorts` date
columns are already Python `date`s, so `cohort_row["lookback_start_date"]` and
`cohort_row["lookback_end_date"]` can be used directly in Spark filters and `F.lit(...)`.

### 12.2 Validation IDs do not match `PROVIDER_ID`

**Gap:** the config's `get_test_npis()` / `apply_npi_filter()` hold NPIs, but `PROVIDER_ID`
in the claims files is an IQVIA provider id (e.g. `26620371`), so the 10 test NPIs match
nothing. **Fix:** either map the NPIs through a crosswalk (Section 1.2), or use a deterministic
sample of the HCP universe for test runs. Write test outputs to a separate `_test` folder.

```python
hcp_universe = spark.read.parquet(HCP_UNIVERSE_PATH).select("PROVIDER_ID").distinct()
if TEST_HCP_SAMPLE > 0:
    hcp_universe = (hcp_universe.orderBy(F.xxhash64("PROVIDER_ID"), "PROVIDER_ID")
                    .limit(TEST_HCP_SAMPLE))
claims = claims.join(F.broadcast(hcp_universe), "PROVIDER_ID", "left_semi")
```

### 12.3 Input files with less history than their names suggest

**Gap:** some default paths in Section 2.1 cover only the last 12M. **Fix:** see the data
coverage note in Section 2.1. Always check the date range against the earliest cohort's
lookback start before you choose a file.

### 12.4 Delta-safe names for the documented feature columns

**Gap:** the documented names `max(EVENT_TIME)_{EVENT}_first_occurrence` and
`min(EVENT_TIME)_{EVENT}_time_min` contain parentheses, which Delta rejects. **Fix:**
sanitize the whole name. The written names are then
`MAX_EVENT_TIME_{EVENT_KEY}_FIRST_OCCURRENCE` and `MIN_EVENT_TIME_{EVENT_KEY}_TIME_MIN`.
Sanitize the event names ONCE into an `EVENT_KEY` column (a broadcast join of a
`(EVENT_NAME, EVENT_KEY)` map), and pivot on `EVENT_KEY`. Every pivot then produces clean
columns, and no backticks are needed later. If two names sanitize to the same key, append
`_2`, `_3`, ...

### 12.5 Batching wide pivots

**Gap:** the skill says to batch by cohort, but it does not say how to keep the batch schemas
identical. **Fix:** always pass the explicit value list to `.pivot(col, values)`: the market
basket keys (Section 1.5). Write the first batch with `mode("overwrite")` +
`overwriteSchema`, and the later batches with `mode("append")`, partitioned by `COHORT`.
Pivoting with several aggregations names the columns `{value}_{alias}`; rename them to the
final names straight away. First Occurrence (Section 3, pivot -> cross-join) needs no batching.

### 12.6 Recency counts by type in single-source notebooks

**Gap:** each notebook processes one claim type, so `total_{type}` equals `total_events`, and
the other types' columns are always 0. **Fix:** pass only the notebook's own type
(`event_types=[EVENT_TYPE]`). Build the counts by type and by type x window only when RX, DX,
PX and Lab claims are unioned in one recency computation.

### 12.7 Monthly spine bounds

**Gap:** with data from 2001 (Lab), a min-to-max spine is needlessly large. **Fix:** bound the
spine to `[first cohort month - (max lag - 1) months, last cohort month]`. This gives
identical lag values for every cohort month. Take the bounds from `cohorts` (Section 10.8.3)
and assign `SVC_DT_M` with the claims monthly grain from Section 10.8.2.

### 12.8 Testing a generated notebook

Run the four notebooks as one job run with `TEST_HCP_SAMPLE=500` (about 6.5 min on
serverless). Checks: one row per `HCP_COHORT_ID`, `COHORT` values only from
`cohorts["cohort_id"]` (`c1`..`c28`), the Section 10.8.6 checks pass, and no stage folders
left behind.

### 12.9 Base primitives are still loaded -- never call them

**Gap:** the base primitives are still available in `00_cohort_generation` (via its `%run`
of the base `00_cohort_config`), but they must not be called directly from a claims feature
notebook generated from this skill. Do not call `get_cohort_bounds(`, `get_cohort_months(` or
`assign_cohort_month(`, and do not use the removed shared-config helpers (`use_feature_type`,
`load_cohorts`, the Delta cohort store). **Fix:** if a code review surfaces a direct primitive
call, that is a bug. Replace it with the `CohortGenerator('claims').load()` loading idiom
and the `cohorts` columns (Section 10.8). If the call computed something `cohorts` does not
hold (monthly grain, N-month / AVG window bounds, last included day), use the derivations in
Section 10.8.2 and keep the `TODO: expose via CohortGenerator` note.

---

## 13. NBA 3.1 Add-on Patient Features (generated at the end of every notebook run)

> **These add-on features are generated at the END every time patient feature notebooks are
> generated from this skill. They are built in a separate notebook cell block appended after
> the standard feature types (Sections 3-6). The output is saved to a separate Delta table
> `{source}_addon_patient_features` under the notebook output base.**
>
> Source: `NBA_3_1_Patient_Features_Recommendations.md` (Feature Analysis folder).

### What it answers

*Which HCPs have the most addressable Kerendia-eligible patients, recent trigger events, and
switch candidates -- and which face barriers to starting?*

### 13.0 Patient-level Building Blocks (shared by all add-on features)

Every add-on feature is built in two steps. First, a patient-level status table is built per
cohort from claims by **any** provider (a patient's diagnoses and therapies do not depend on
who coded them). Then the flags are rolled up to each HCP's panel (the distinct patients with
any paid Rx, Dx, lab or albuminuria-test claim from the HCP in the lookback). **Only HCPs in
the HCP universe get a panel.** Join the panel to `hcp_universe` before the roll-up; leave the
patient-level status inputs unfiltered (see "HCP universe" at the top of this skill).

**Parameters:**

| Parameter | Default | Description |
| --- | --- | --- |
| `ON_THERAPY_RECENT_DAYS` | `180` | Window for "currently on" therapy flags |
| `TRIGGER_WINDOW_DAYS` | `90` | Window for trigger events |
| `NEW_EVENT_WASHOUT_DAYS` | `365` | Washout period for "new" event detection |
| `LOOKBACK_END_DATE` | From cohort config | Anchor date for all patient-level windows |

**Building block definitions:**

| Block | Source | Definition |
| --- | --- | --- |
| T2D | Dx | Any ICD-10 `E11*` in the lookback |
| DKD code | Dx | `E11.21`, `E11.22`, `E11.29` |
| CKD (non-ESRD) | Dx | `N18.1`-`N18.5`, `N18.9`, `I12.9`, `I13.0`, `I13.10`, `E11.21/22/29`, `E08.21` |
| ESRD / dialysis | Dx | `N18.6`, `I12.0`, `I13.11`, `I13.2`, `Z99.2`, `Z49*` |
| Albuminuria Dx | Dx | `R80*` |
| Diabetic CKD (DKD) | Dx | T2D and (CKD or DKD code) and not ESRD |
| ACE/ARB | Rx | Product groups: `ACE INHIBITORS AND COMBOS`, `ANGIOTENSIN II RECEPTOR ANTAGONISTS AND COMBOS` |
| SGLT2 | Rx | The 10 `00_config` groups plus `INPEFA`, `BEXAGLIFLOZIN`, `GLYXAMBI`, `SEGLUROMET` |
| Steroidal MRA | Rx | `MINERALOCORTICOID RECEPTOR ANTAGONISTS` |
| GLP-1 RA | Rx | Product groups for Ozempic, Rybelsus, Trulicity, Victoza, Mounjaro (confirm class name) |
| Kerendia | Rx | `KERENDIA` |
| Loop diuretic | Rx | Furosemide, bumetanide, torsemide |
| Days supply | Rx | Paid claims only. Missing or >180 set to 30. Fill end = `SVC_DT + DAYS_SUPPLY - 1` |
| On ACE/ARB, on SGLT2 | Rx | Paid claim in the last `ON_THERAPY_RECENT_DAYS` of the lookback |
| Never on Kerendia | Rx | No paid Kerendia fill for the patient, from any prescriber, in full history up to `LOOKBACK_END_DATE` |
| Latest UACR / eGFR | Lab | Most recent result in the lookback. Plausibility: eGFR 1-200, UACR 0-20,000 |
| Albuminuria | Lab + Dx | Latest UACR >= 30, or an `R80*` Dx |
| Albuminuria test | Lab + Px | A UACR lab result or CPT 82043 (urine albumin, quantitative) |
| MRA current / stopped | Rx | Current: last fill end >= lookback end - 30 d. Stopped: last fill end + 60 d < lookback end |

**Null policy:** `NUM_*` and `TOTAL_*` are 0 when no patient qualifies. `PCT_*` and `RATIO_*`
stay null when the denominator is 0. LightGBM handles nulls natively. Do not fill with 0.

**Feature naming:** when a row lists a stem, there are two features: `NUM_OF_PATIENTS_{stem}`
and `PCT_OF_PATIENTS_{stem}` (= NUM / panel size).

### Grain

`HCP_COHORT_ID` -- one row per HCP-cohort, one column per add-on feature.

### 13.1 Untreated Eligible Pool (#1): Dx + Rx + Lab

**What it answers:** *How many patients does this HCP already treat who meet the Kerendia label
profile but have never received Kerendia?*

**Business meaning:** the patients this HCP already treats who have type 2 diabetes with CKD,
are already on the standard kidney-protecting therapy (ACE/ARB), but have never received
Kerendia. This is the pool the HCP could start on Kerendia without finding new patients.

| Stem | Sources | Non-zero | Median NUM / PCT |
| --- | --- | --- | --- |
| `IN_HCP_PANEL_WITH_DIABETIC_CKD_IN_LAST_365_DAYS_PATIENT` | Dx | 98.3% | 38 / 0.066 |
| `IN_HCP_PANEL_WITH_T2D_CKD_ON_ACE_ARB_NEVER_ON_KERENDIA_IN_LAST_365_DAYS_PATIENT` | Dx + Rx | 96.5% | 17 / 0.029 |
| `IN_HCP_PANEL_WITH_T2D_CKD_ON_ACE_ARB_NEVER_ON_KERENDIA_AND_UACR_GE_30_IN_LAST_365_DAYS_PATIENT` | Dx + Rx + Lab | 60.1% | 1 / 0.002 |
| `IN_HCP_PANEL_WITH_T2D_CKD_ON_ACE_ARB_NEVER_ON_KERENDIA_AND_UACR_GE_30_AND_EGFR_GE_25_IN_LAST_365_DAYS_PATIENT` | Dx + Rx + Lab | 57.2% | 1 / 0.001 |
| `IN_HCP_PANEL_ELIGIBLE_FOR_KERENDIA_IN_LAST_365_DAYS_PATIENT` | Dx + Rx | 96.8% | 18 / 0.031 |
| `IN_HCP_PANEL_ELIGIBLE_AND_ON_KERENDIA_IN_LAST_365_DAYS_PATIENT` | Dx + Rx | 48.4% | 0 / 0 |
| `PCT_OF_DIABETIC_CKD_PATIENTS_IN_HCP_PANEL_UNTREATED_ELIGIBLE_IN_LAST_365_DAYS_PATIENT` | Dx + Rx | 96.5% | median 0.45 |
| `RATIO_KERENDIA_TREATED_TO_ELIGIBLE_PATIENTS_IN_HCP_PANEL_IN_LAST_365_DAYS_PATIENT` | Dx + Rx | 48.4% | median 0.005 |
| `IN_HCP_PANEL_WITH_T2D_CKD_ON_ACE_ARB_ONLY_NEVER_ON_KERENDIA_IN_LAST_365_DAYS_PATIENT` | Dx + Rx | -- | New (not yet built) |
| `IN_HCP_PANEL_WITH_T2D_CKD_ON_SGLT2_OR_GLP1_ONLY_NEVER_ON_KERENDIA_IN_LAST_365_DAYS_PATIENT` | Dx + Rx | -- | New (not yet built) |

The UACR and eGFR variants are sparse (57-60% non-zero) because NBA 3.0 lab data covers only
primary-care orderers. They fill in once the lab specialty filter is removed.

**New split by background therapy:** the first new split (`ACE_ARB_ONLY`) requires DKD, on
ACE/ARB, no SGLT2 and no GLP-1 claim in the last 180 d, never on Kerendia. The second
(`SGLT2_OR_GLP1_ONLY`) requires DKD, on SGLT2 or GLP-1 in the last 180 d, no ACE/ARB, never on
Kerendia. Both need a GLP-1 class in the building blocks. Build as NUM and PCT of panel.

### 13.2 90-Day Trigger Events (#2): Dx, Rx, Lab/Px

**What it answers:** *Which HCPs have patients with recent new clinical events that typically
precede a Kerendia start?*

**Business meaning:** trigger events are new clinical moments when a doctor is most likely to
add a new therapy. Each one counts patients whose event happened in the last
`TRIGGER_WINDOW_DAYS` with no matching event in the `NEW_EVENT_WASHOUT_DAYS` before.

| Trigger | Source | Patient-level definition | % of HCPs with >= 1 | Lift |
| --- | --- | --- | --- | --- |
| Newly diagnosed diabetic CKD | Dx | First `E11.21/22/29` for the patient falls in the last 90 d (no earlier DKD code in history) | 31% | 1.30 |
| New SGLT2 start | Rx | Paid SGLT2 claim in the last 90 d and no SGLT2 claim in the prior 365 d | 74% | 2.21 |
| New albuminuria test | Lab + Px | UACR lab or CPT 82043/82044 in the last 90 d and none in the prior 365 d | 62% | 1.36 |

| Stem | Source | Non-zero | Median NUM / PCT |
| --- | --- | --- | --- |
| `THE_HCP_NEWLY_DIAGNOSED_WITH_DIABETIC_CKD_IN_LAST_90_DAYS_DX` | Dx | 30.9% | 0 / 0 |
| `THE_HCP_STARTED_ON_SGLT2_IN_LAST_90_DAYS_RX` | Rx | 74.0% | 2 / 0.004 |
| `THE_HCP_ORDERED_NEW_ALBUMINURIA_TEST_IN_LAST_90_DAYS_LAB_DATA` | Lab + Px | 62.1% | 2 / 0.007 |

Each trigger has a NUM and a PCT version, 6 features in total. The trigger is credited to the
HCP on the claim with the event date. The washout check is done at patient level, across all
providers.

### 13.3 HF with LVEF >= 40% (#3): Dx + Px + Rx

**What it answers:** *Which HCPs have heart failure patients with preserved or mildly reduced
ejection fraction, Kerendia's 2025 indication?*

**Business meaning:** Kerendia's heart failure indication (2025, FINEARTS-HF trial) is for HF
with mildly reduced or preserved ejection fraction (LVEF >= 40%). Claims data has no LVEF
value, so diagnosis codes are the proxy: diastolic HF (`I50.3x`) is close to HFpEF, and
systolic HF (`I50.2x`) is HFrEF.

| HF type | LVEF | ICD-10 proxy |
| --- | --- | --- |
| HFrEF (reduced) | <= 40% | `I50.2x` systolic |
| HFmrEF (mildly reduced) | 41-49% | No specific code |
| HFpEF (preserved) | >= 50% | `I50.3x` diastolic |
| Combined | Mixed | `I50.4x` |
| Unspecified | Unknown | `I50.9` |

| Stem | Sources | Definition |
| --- | --- | --- |
| `HFPEF_PROXY_IN_HCP_PANEL_IN_LAST_365_DAYS_PATIENT` | Dx | Any `I50.3x` in 365 d and no `I50.2x` / `I50.4x` |
| `HFPEF_PROXY_WITH_ECHO_IN_HCP_PANEL_IN_LAST_365_DAYS_PATIENT` | Dx + Px | HFpEF proxy plus an echo test within 365 d (confirms the HF work-up) |
| `HFPEF_PROXY_ON_LOOP_DIURETIC_NO_MRA_IN_HCP_PANEL_IN_LAST_365_DAYS_PATIENT` | Dx + Rx | HFpEF proxy, on a loop diuretic in the last 180 d, no steroidal MRA or Kerendia |
| `HFPEF_PROXY_NEVER_ON_KERENDIA_IN_HCP_PANEL_IN_LAST_365_DAYS_PATIENT` | Dx + Rx | HFpEF proxy and never on Kerendia |

Each as NUM and PCT of panel. A combined-HF (`I50.4x`) variant can be tested separately.

### 13.4 Potassium Barrier (#4): Dx + Rx + Lab

**What it answers:** *Which HCPs have hyperkalemic CKD patients, and which also use potassium
binders that enable RAAS/MRA therapy?*

**Business meaning:** Kerendia must not be started when serum potassium is above 5.0 mEq/L.
High potassium (hyperkalemia) is the most common reason doctors do not start an MRA, or stop
it. HCPs with many hyperkalemic CKD patients are less likely to start Kerendia, unless they
also use potassium binders.

**Upstream changes needed (already done in 3.1 event lists):** E87.5 added to Dx event list,
Lokelma and Veltassa added to Rx product basket, potassium (LOINC 2823-3 / 6298-4) added to
Lab test types in `01_Input_data_creation`.

| Stem | Sources | Definition |
| --- | --- | --- |
| `PCT_OF_DKD_PATIENTS_IN_HCP_PANEL_WITH_HYPERKALEMIA_IN_LAST_365_DAYS_PATIENT` | Dx + Lab | `E87.5` Dx or latest K+ > 5.0 mEq/L in the lookback |
| `PCT_OF_DKD_PATIENTS_IN_HCP_PANEL_ON_POTASSIUM_BINDER_IN_LAST_365_DAYS_PATIENT` | Dx + Rx | Paid Lokelma or Veltassa claim in the last 180 d |

Each as NUM and PCT of DKD patients in the panel.

### 13.5 MRA Switch Candidates (#5): Rx + Dx

**What it answers:** *Which HCPs have T2D + CKD patients currently on a steroidal MRA who are
natural Kerendia switch candidates, and which have patients who recently stopped an MRA?*

**Business meaning:** steroidal MRAs (spironolactone, eplerenone) are used for resistant
hypertension and HFrEF. In T2D + CKD, Kerendia is the evidence-based MRA (FIDELIO/FIGARO
trials), and steroidal MRAs carry more hyperkalemia risk and side effects. An HCP with T2D +
CKD patients on spironolactone is comfortable with the MRA class and has natural switch
candidates.

| Stem | Sources | Non-zero | Median NUM / PCT | Lift |
| --- | --- | --- | --- | --- |
| `THE_HCP_PRESCRIBED_WITH_STEROIDAL_MRA_CURRENTLY_ON_MRA_WITH_T2D_CKD_IN_LAST_365_DAYS_RX` | Rx + Dx | 51.3% | 1 / 0.001 | 1.49 |
| `THE_HCP_PRESCRIBED_WITH_STEROIDAL_MRA_THAT_STOPPED_MRA_WITH_T2D_CKD_IN_LAST_365_DAYS_RX` | Rx + Dx | 31.9% | 0 / 0 | -- |
| `PCT_OF_STEROIDAL_MRA_PATIENTS_THE_HCP_PRESCRIBED_THAT_STOPPED_MRA_IN_LAST_365_DAYS_RX` | Rx | 84.5% | median 0.25 | 1.17 |

> **NBA 3.1 Feature Removal Note (MRA):** We are commenting out (removing)
> `THE_HCP_PRESCRIBED_WITH_STEROIDAL_MRA_IN_LAST_365_DAYS_RX` because it has no signal (lift
> 0.98) and repeats the MRA volume features already in the 752-feature model (17 MRA features,
> 1.4% of SHAP combined). Keep only the T2D + CKD switch-candidate and stopped-MRA versions.

Attribution: patients for whom this HCP wrote spironolactone or eplerenone in the lookback.