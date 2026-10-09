---
name: mmit-ingestion
description: Ingesting MMIT market access data feeds into Bronze/Silver Delta tables. Load when the user asks about MMIT data, formulary data ingestion, market access data pipelines, the MMIT volume, Bronze or Silver table structure for market access, or troubleshooting MMIT ingestion issues.
---

# MMIT Market Access Data Ingestion

This skill covers ingesting MMIT (Managed Markets Insight & Technology) historical data feeds from a UC Volume into a Medallion architecture (Bronze → Silver) for market access analytics and ML model training.

## Data Source

- **Volume**: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/market_access/mmit_historical_uploads`
- **Catalog.Schema**: `ph-com-ai-us-prod-catalog-2553213839599380`.`market_access`
- **Format**: Weekly zip files, two feed types per week
- **Delivery cadence**: Weekly (Thursday/Friday)
- **History**: 98 zip files spanning Jun 2025 – Sep 2026 (~320 GB uncompressed)

### Feed Types

| Feed | Prefix | Size/week | Content |
|---|---|---|---|
| Pharmacy/Formulary | `MMITDataFeed2.0_MM_DD_YYYY.zip` | ~4.4 GB | Formulary statuses, restrictions, drugs, plans, geography, bridges |
| PAR/Medical | `MMITPARFeed2.0_MM_DD_YYYY.zip` | ~1.9 GB | Prior auth, step therapy, medical benefit, UDFs, medical geography |

### File Format Inside Zips

- All data files are **pipe-delimited (`|`) `.txt`** files
- Some fields are **double-quoted** (`"`)
- Each zip also contains a `CONTROL.txt` with expected row counts per file (for reconciliation) and a documentation `.xlsx` (skip both during ingestion)

## Bronze Layer — 24 Delta Tables

### DataFeed File → Table Mapping (11 tables)

| Source File | Bronze Table | Rows/week | Description |
|---|---|---|---|
| STATUSES.txt | `bronze_statuses` | ~12M | Core formulary status per drug/plan — **primary signal** |
| RESTRICTIONS.txt | `bronze_restrictions` | ~4.5M | Restriction codes (PA, ST, QL) and detail text |
| DRUGS.txt | `bronze_drugs` | ~5.7K | Drug reference dimension |
| PLANDETAILS.txt | `bronze_plan_details` | ~8.4K | Plan/formulary/controller/PBM hierarchy (29 cols) |
| PLANSCONTROLLERMCO.txt | `bronze_plans_controller_mco` | ~8.4K | Plan-MCO relationship |
| Zip_Code.txt | `bronze_zip_code` | ~25.6M | Plan coverage by zip code + lives |
| STATES.txt | `bronze_states` | ~39K | Plan coverage by state + lives |
| CBSAS.txt | `bronze_cbsas` | ~746K | Plan coverage by CBSA + lives |
| IQVIA_Bridge.txt | `bronze_iqvia_bridge` | ~105K | OrgId → IMSPayerPlanId crosswalk |
| NDC_Bridge.txt | `bronze_ndc_bridge` | ~42K | MedId → NDC crosswalk |
| Medispan_Bridge.txt | `bronze_medispan_bridge` | ~4.6K | MedId → DDI crosswalk |

### PARFeed File → Table Mapping (13 tables)

| Source File | Bronze Table | Rows/week | Description |
|---|---|---|---|
| PA_v2.txt | `bronze_pa_v2` | ~107K | Prior auth criteria (indication, age, gender, duration) |
| ST.txt | `bronze_st` | ~29K | Step therapy details |
| Medical.txt | `bronze_medical` | ~123K | Medical benefit coverage flags |
| MedicalPA.txt | `bronze_medical_pa` | ~72K | Medical prior auth details |
| MedicalST.txt | `bronze_medical_st` | ~14K | Medical step therapy details |
| Products.txt | `bronze_products` | ~5.7K | Product reference (PAR feed) |
| DerivedFields.txt | `bronze_derived_fields` | ~18K | Custom Bayer-derived fields |
| PAUdf.txt | `bronze_pa_udf` | ~2.8M | Granular PA criteria details |
| MedicalUdf.txt | `bronze_medical_udf` | ~3.6M | Granular medical criteria details |
| MedicalGroups.txt | `bronze_medical_groups` | ~5.7K | Medical group → plan mapping |
| MEDICAL_Zip_Code.txt | `bronze_medical_zip_code` | ~8.6M | Medical plan coverage by zip |
| MEDICAL_STATES.txt | `bronze_medical_states` | ~16K | Medical plan coverage by state |
| MEDICAL_CBSAS.txt | `bronze_medical_cbsas` | ~252K | Medical plan coverage by CBSA |

### Natural Keys (CRITICAL)

- **STATUSES and RESTRICTIONS**: The grain is `(FormularyId, MedId, TherapeuticClass)` — NOT `(FormularyId, MedId)`. The same drug-formulary pair appears under multiple therapeutic classes. Do not treat `(FormularyId, MedId)` as unique.
- **PA_v2**: The grain is `(FormularyId, MedId, IndicationId)`.
- **Geography files**: The grain is `(OrgId, State, ZipCode)` for zip-level, `(OrgId, State)` for state-level.
- **Bridge files**: `OrgId → IMSPayerPlanId` (IQVIA), `MedId → NDC` (NDC), `MedId → DDI` (Medispan).

### HCP-Level Join Path

To connect MMIT formulary data to HCP-level data:

```
HCP (NPI → practice zip) → bronze_zip_code (ZipCode → OrgId + Lives)
  → bronze_plan_details (OrgId → FormularyId)
  → bronze_statuses (FormularyId + MedId → coverage status)
```

Use the `Lives` column in geography tables to weight each plan's formulary decision by its coverage in the HCP's geography.

## Ingestion Process

### Step 1: Extract from zip to Volume staging

Serverless compute **cannot access local `/tmp`**. Extract files to a staging subdirectory within the UC Volume:

```python
import zipfile, os, shutil

VOLUME_PATH = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/market_access/mmit_historical_uploads"
STAGING_DIR = f"{VOLUME_PATH}/_staging"
os.makedirs(STAGING_DIR, exist_ok=True)

with zipfile.ZipFile(zip_path, "r") as zf:
    with zf.open(txt_filename) as src, open(staged_path, "wb") as dst:
        shutil.copyfileobj(src, dst)
```

Always clean up the staging directory after ingestion:
```python
shutil.rmtree(STAGING_DIR, ignore_errors=True)
```

### Step 2: Read with Spark

```python
df = (spark.read.format("csv")
      .option("header", "true")
      .option("inferSchema", "true")
      .option("delimiter", "|")
      .option("quote", '"')
      .option("multiLine", "false")
      .option("escape", '"')
      .load(staged_path))
```

### Step 3: Add feed_date and write to Delta

The catalog name contains hyphens — **always backtick-quote identifiers**:

```python
from pyspark.sql import functions as F
from pyspark.sql.types import DateType
import re

# Parse date from zip filename: MMITDataFeed2.0_MM_DD_YYYY.zip
match = re.search(r"(\d{2})_(\d{2})_(\d{4})\.zip$", zip_filename)
feed_date = f"{match.group(3)}-{match.group(1)}-{match.group(2)}"  # YYYY-MM-DD

df = df.withColumn("feed_date", F.lit(feed_date).cast(DateType()))

# MUST backtick-quote because catalog name has hyphens
(df.write.format("delta")
 .mode("append")
 .option("mergeSchema", "true")
 .partitionBy("feed_date")
 .saveAsTable(f"`{CATALOG}`.`{SCHEMA}`.`{table_name}`"))
```

### Step 4: Idempotency

The batch ingestion job checks which `feed_date` values already exist in `bronze_statuses` (for DataFeed) and `bronze_pa_v2` (for PARFeed) and skips those dates. Safe to re-run.

**Caveat**: If a run is interrupted mid-zip, some files for that date may be ingested while others are not. The skip logic sees the date as "done" and misses the remaining files. To guard against this, check per-table coverage rather than just per-date in a single reference table, or use a control/checkpoint table.

### Reconciliation with CONTROL.txt

Each zip contains `CONTROL.txt` with expected row counts:
```
ClientId|TableName|RowCount|ProcessingDate|BeginPeriod|EndPeriod
13186|STATUSES|12245553|2026-01-08 09:32:46|202601|202601
```
Compare against actual row counts per `feed_date` partition to detect incomplete ingestion.

## Silver Layer — 5 Tables

### Change Detection (optimized with window functions)

Use `lag()` window functions instead of iterative joins for each date pair. This is critical at scale — the iterative approach would take 30+ minutes vs 2-3 minutes with windows.

#### silver_status_changes

Detects formulary status changes between consecutive weekly snapshots:

```python
from pyspark.sql import functions as F, Window

w = Window.partitionBy("FormularyId", "MedId", "TherapeuticClass").orderBy("feed_date")
with_prev = (statuses
    .select("FormularyId", "MedId", "TherapeuticClass",
            "UniversalStatus", "UniversalStatusRollup", "RawStatus", "feed_date")
    .withColumn("prev_status", F.lag("UniversalStatus").over(w))
    .withColumn("prev_feed_date", F.lag("feed_date").over(w)))

changes = (with_prev
    .filter(F.col("prev_feed_date").isNotNull())
    .filter(F.col("UniversalStatus") != F.col("prev_status")))
```

#### silver_restriction_changes

Same pattern on `(FormularyId, MedId, TherapeuticClass, RestrictionCode)`, comparing `RestrictionDetail` via lag.

#### silver_pa_changes

Compares 9 PA attributes via MD5 hash of concatenated values on `(FormularyId, MedId, IndicationId)` grain.

### SCD Type 2 Dimensions

#### silver_drug_dim

Tracks drug attribute changes over time using MD5 hash comparison with `valid_from`, `valid_to`, `is_current`.

#### silver_plan_dim

Same SCD2 pattern for plan/formulary/PBM hierarchy. Note: only covers 22 dates due to the PLANDETAILS schema issue (see Known Gaps).

## Known Gaps and Workarounds

### Gap 1: bronze_plan_details — 22/50 dates (schema evolution)

**Cause**: `inferSchema` infers different column types across weeks. A column inferred as INT in early weeks becomes STRING in later weeks. `mergeSchema` cannot reconcile type mismatches.

**Fix**: Define an explicit schema with all STRING columns:
```python
from pyspark.sql.types import StructType, StructField, StringType
plan_schema = StructType([StructField(col, StringType(), True) for col in [
    "ClientId", "Period", "OrgId", "PlanName", "FormularyId", "FormularyName",
    "ControllerId", "ControllerName", "ParentId", "ParentName", "Channel",
    "PlanType", "PBMId", "PBMName", "PBMRelationship", "NotListedPolicy",
    "NonFormularyPolicy", "BenefitDesign", "Address1", "Address2", "City",
    "StateId", "Zip", "ZipExt", "Phone", "PriorAuthPhone", "PriorAuthFax",
    "MemberPhone", "ProcessingDate"
]])
df = spark.read.csv(path, header=True, schema=plan_schema, delimiter="|", quote='"')
```

**Workaround**: `bronze_plans_controller_mco` (50/50 dates) carries the same `OrgId` key with Channel, PlanType, and PBM fields.

### Gap 2: bronze_derived_fields — 41/48 dates

**Cause**: 7 early PARFeed zips (Jun–Nov 2025) did not include `DerivedFields.txt`. The file appeared starting Nov 2025.

**Action**: None — source data genuinely doesn't exist for these weeks.

### Gap 3: Early partial feeds — 3 dates (Jun–Aug 2025)

**Cause**: The first 3 feeds (2025-06-02, 2025-07-01, 2025-08-01) were starter subscription deliveries with only core files (~114K rows in STATUSES vs normal ~12M). Geography, bridge, and some PAR files were not included.

**Action**: None — these are genuinely partial. Filter them out for ML training if needed (`feed_date >= '2025-10-07'`).

### Gap 4: Partial ingestion from interrupted runs

**Cause**: If an interactive run times out mid-zip, some files are written but others are not. The batch job's skip logic (which checks a single reference table) sees the date as complete.

**Prevention**: Use per-table per-date coverage checks, or maintain a checkpoint table tracking `(zip_filename, txt_file, status)` tuples.

## Existing Assets

| Asset | ID | Purpose |
|---|---|---|
| MMIT Bronze Ingestion Prototype (notebook) | 3771248215232858 | Single-week prototype + helpers |
| MMIT Bronze Full Batch Ingestion (notebook) | 3771248215232867 | Full backfill with auto-skip |
| MMIT Silver Change Detection Layer (notebook) | 3771248215232863 | Silver layer code (window-function optimized) |
| MMIT Bronze Full Batch Ingestion (job) | 172904838614335 | Weekly scheduled job |

## Scale Reference

| Metric | Value |
|---|---|
| Total Bronze rows | ~3.1 billion |
| Largest table | bronze_zip_code (1.4B rows) |
| Weekly ingestion time | ~2 min/DataFeed zip + ~1.5 min/PARFeed zip |
| Full backfill time | ~104 minutes (98 zips) |
| Silver rebuild time | ~5 minutes (all 5 tables) |
| Delta compression ratio | ~5-6x (320 GB raw → ~55 GB Delta) |