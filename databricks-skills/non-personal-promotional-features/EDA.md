# Non-Personal Promotional Features — EDA Reference

Exploratory Data Analysis patterns and known data characteristics for the seven non-personal
promotional channels: Digital Engagement, HQ Emails, DTC Direct Buy, Meta/Instagram Ads,
Samples, Speaker Programs, and Free Trial Program. Use this reference to validate feature
outputs, detect data quality issues, and understand distributions before model training.

---

## 1. Output Parquet Paths

| Channel | Path |
| --- | --- |
| Digital Engagement | `.../notebook_output/kerendia_nba_3_0_hcp_model_paid_search_features.parquet` |
| HQ Emails | `.../notebook_output/kerendia_nba_3_hcp_model_hq_email_features.parquet` |
| DTC Direct Buy + Meta/IG | `.../notebook_output/kerendia_nba_3_hcp_model_DTC_PROMOTION.parquet` |
| Samples | `.../notebook_output/kerendia_nba_3_hcp_model_samples_features.parquet` |
| Speaker Programs | `.../notebook_output/kerendia_nba_3_hcp_model_speaker_program.parquet` |
| Free Trial Program | `.../notebook_output/kerendia_nba_3_hcp_model_ftp_features.parquet` |

Base volume: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/dev_folder/`

---

## 2. Standard EDA Checks

### 2.1 Schema and Dimensions

```python
df = spark.read.parquet(path)
print(f"Rows: {df.count()}, Columns: {len(df.columns)}")
df.printSchema()
```

Expected dimensions:

| Channel | Expected Rows | Expected Columns | Key Column |
| --- | --- | --- | --- |
| Digital Engagement | ~17,296,750 | 665 | `NPI_NUMBER` + `SVC_DT_M` |
| HQ Emails | ~2,476,618 | 32 | `HCP_COHORT_ID` |
| DTC + Meta/IG | ~7,052 | 12 | `DMA_Code` + `DATA_MONTH` |
| Samples | ~519,959 | 56 | `HCP_COHORT_ID` |
| Speaker Programs | ~156,677 | 68 | `HCP_COHORT_ID` |
| Free Trial Program | ~718,520 | 9 | `HCP_COHORT_ID` |

### 2.2 Key Integrity

For HCP_COHORT_ID-keyed channels (HQ Emails, Samples, Speaker Programs, FTP):

```python
assert df.count() == df.select("HCP_COHORT_ID").distinct().count(), "Duplicate HCP_COHORT_IDs"

from pyspark.sql import functions as F
df_split = df.withColumn("BHID", F.split("HCP_COHORT_ID", "_").getItem(0)) \
             .withColumn("COHORT", F.split("HCP_COHORT_ID", "_").getItem(1))
print(f"Distinct BHIDs: {df_split.select('BHID').distinct().count()}")
print(f"Distinct Cohorts: {df_split.select('COHORT').distinct().count()}")
```

For Digital (NPI-keyed):

```python
assert df.count() == df.select("NPI_NUMBER", "SVC_DT_M").distinct().count(), "Duplicate NPI+month"
print(f"Distinct NPIs: {df.select('NPI_NUMBER').distinct().count()}")
```

For DTC (DMA-keyed):

```python
assert df.count() == df.select("DMA_Code", "DATA_MONTH").distinct().count(), "Duplicate DMA+month"
print(f"Distinct DMAs: {df.select('DMA_Code').distinct().count()}")
```

Expected entity counts:

| Channel | Distinct Entities |
| --- | --- |
| Digital Engagement | ~402,250 NPIs |
| HQ Emails | ~190,860 BHIDs |
| DTC + Meta/IG | DMA-level (geographic) |
| Samples | ~35,546 BHIDs |
| Speaker Programs | ~17,151 BHIDs |
| Free Trial Program | NPI→BHID mapped |

### 2.3 Sparsity Analysis

```python
from pyspark.sql import functions as F

feature_cols = [c for c in df.columns if c not in ['HCP_COHORT_ID', 'SVC_DT', 'SVC_DT_M',
    'NPI_NUMBER', 'DMA_Code', 'DATA_MONTH', 'BHID', 'COHORT', 'PULL_DT',
    'LOOKBACK_END_DATE', 'PROVIDER_ID']]
total = df.count()

stats = []
for col_name in feature_cols:
    zero_count = df.filter(F.col(col_name) == 0).count()
    null_count = df.filter(F.col(col_name).isNull()).count()
    stats.append((col_name, zero_count, null_count, round(zero_count / total * 100, 1)))

stats_df = spark.createDataFrame(stats, ["feature", "zero_count", "null_count", "zero_pct"])
stats_df.orderBy("zero_pct", ascending=False).display()
```

Expected sparsity:

| Channel | Avg Zero % | Interpretation |
| --- | --- | --- |
| Digital Engagement | 99.1% | Extremely sparse; 665 columns from triple-pivot explosion |
| HQ Emails | 76.9% | Moderate; many HCPs receive at least some emails |
| DTC + Meta/IG | 36.9% | Low; DMA-level aggregation has more density |
| Samples | 84.1% | High; only a subset of HCPs receive samples |
| Speaker Programs | 96.9% | Very sparse; niche channel |
| Free Trial Program | 80.7% | High; FTP is product-specific |

**Digital sparsity note:** At 99.1%, most Digital features will be zero for most HCPs in
most months. This is expected given 665 columns from 22+70+58 pivot categories. Consider
zero-variance filtering at model training time.

### 2.4 Zero-Variance Feature Detection

```python
from pyspark.sql import functions as F

feature_cols = [c for c in df.columns if c not in key_cols]
zero_var = []
for col_name in feature_cols:
    std = df.select(F.stddev(col_name)).first()[0]
    mx = df.select(F.max(col_name)).first()[0]
    if std == 0 or std is None:
        zero_var.append((col_name, mx))

print(f"Zero-variance features: {len(zero_var)}")
for name, mx in zero_var:
    print(f"  {name}: max={mx}")
```

---

## 3. Channel-Specific EDA Findings

### 3.1 Digital Engagement

**Key stats:**
- Output rows: ~17.3M (NPI × months)
- 665 columns (from ~600 base features × 3 lag windows, pruned)
- Highest dimensionality of any promotional channel

**Column prefix:** All features start with `DIGITAL_`

**Triple-pivot characteristics:**
- Pivot by CHANNEL (22 values): most populated pivots are BANNER, EMAIL, PAID_SEARCH
- Pivot by SRC_SYS_CD (70 values): many systems have very sparse data
- Pivot by TACTIC_NAME (58 values): DocSpot, Brand Alert are among the most active

**Lag window note:** Uses `[1, 3, 6]` months (NOT day-level [1–6] months). This is
intentional — Digital/MMX data is only available at monthly granularity.

**Column sanitization artifacts:**
- `FB+IG` → `FB_AND_IG` in column names
- `HAYMARKET-DISPLAY` → `HAYMARKET_DISPLAY`
- Check for any remaining special characters:

```python
import re
bad_cols = [c for c in df.columns if re.search(r'[^A-Za-z0-9_]', c)]
print(f"Columns with special chars: {bad_cols}")
```

**NPI key validation:**
```python
# Digital uses NPI, not BHID
assert "NPI_NUMBER" in df.columns, "Missing NPI_NUMBER key"
assert "BHID" not in df.columns, "BHID should not be in Digital output"
```

### 3.2 HQ Emails

**Key stats:**
- Output rows: ~2.5M
- 32 columns (5 event types × 6 rolling windows + 2 keys)
- 190,860 distinct HCPs

**Event type distribution:**
- `TOTAL_SENT_*`: highest counts (every email generates a Sent event)
- `TOTAL_OPEN_*`: subset of Sent
- `TOTAL_CLICK_*`: subset of Open
- `TOTAL_BOUNCE_*`: small fraction
- `TOTAL_UNSUBSCRIBE_*`: very rare

**Expected funnel relationship:**
```
Sent ≥ Open + Bounce + Unsubscribe
Open ≥ Click
```

Validation:
```python
for suffix in ['_IN_LAST_1_MONTH', '_IN_LAST_6_MONTH']:
    sent = df.select(F.sum(f"TOTAL_SENT{suffix}")).first()[0]
    opened = df.select(F.sum(f"TOTAL_OPEN{suffix}")).first()[0]
    clicked = df.select(F.sum(f"TOTAL_CLICK{suffix}")).first()[0]
    bounced = df.select(F.sum(f"TOTAL_BOUNCE{suffix}")).first()[0]
    print(f"{suffix}: Sent={sent}, Open={opened}, Click={clicked}, Bounce={bounced}")
```

**Schema note:** HQ Emails retains `LOOKBACK_END_DATE` in its output, unlike other
channels. The combine notebook explicitly drops it:
`hq_email_features.drop("BHID", "SVC_DT", "LOOKBACK_END_DATE")`.

### 3.3 DTC Direct Buy

**Key stats:**
- Output rows: ~7,052 (DMA × months, including Meta/IG)
- 12 columns total (8 Direct Buy + 2 Meta/IG + DMA_Code + DATA_MONTH)
- DMA-level, NOT HCP-level

**Vendor-level validation:**
```python
vendors = ['HEALTHLINE', 'HEALTHUNION', 'SHARECARE', 'WEBMD']
for v in vendors:
    imp_col = f"DTC_PROMOTION_{v}_TOTAL_IMPRESSIONS"
    clk_col = f"DTC_PROMOTION_{v}_TOTAL_CLICKS"
    total_imp = df.select(F.sum(imp_col)).first()[0]
    total_clk = df.select(F.sum(clk_col)).first()[0]
    print(f"{v}: Impressions={total_imp}, Clicks={total_clk}, CTR={total_clk/total_imp:.4f}")
```

**No rolling windows:** DTC features are raw monthly aggregates with no rolling-window
pipeline. This is intentional — DTC is used as a contemporaneous market-pressure feature.

**Unexecuted cells:** PulsePoint and TTD Display cells in the source notebook have never
been executed (`state=input`). If activated, they would add 4 more features (2 vendors × 2
metrics). Check whether these columns exist in the output:

```python
pulse_cols = [c for c in df.columns if 'PULSEPOINT' in c.upper()]
ttd_cols = [c for c in df.columns if 'TTD' in c.upper()]
print(f"PulsePoint columns: {pulse_cols}")
print(f"TTD columns: {ttd_cols}")
```

### 3.4 Meta/Instagram Ads

**Key stats:**
- Part of the DTC output file (same parquet)
- 2 columns: `DTC_PROMOTION_FB_AND_IG_TOTAL_IMPRESSIONS`, `DTC_PROMOTION_FB_AND_IG_TOTAL_CLICKS`
- DMA-level grain

**Validation:**
```python
fb_imp = df.select(F.sum("DTC_PROMOTION_FB_AND_IG_TOTAL_IMPRESSIONS")).first()[0]
fb_clk = df.select(F.sum("DTC_PROMOTION_FB_AND_IG_TOTAL_CLICKS")).first()[0]
print(f"Meta/IG: Impressions={fb_imp}, Clicks={fb_clk}")

# Check for nulls (should be 0-filled)
null_imp = df.filter(F.col("DTC_PROMOTION_FB_AND_IG_TOTAL_IMPRESSIONS").isNull()).count()
print(f"Null impressions: {null_imp}")
```

### 3.5 Samples

**Key stats:**
- Output rows: ~519,959
- 56 columns (~9 base features × 6 rolling windows + 2 keys)
- 35,546 distinct HCPs

**Sample category validation:**
```python
for suffix in ['_IN_LAST_6_MONTH']:
    for cat in ['KERENDIA_20MG', 'KERENDIA_10MG', 'KERENDIA_10MG_BRC',
                'KERENDIA_20MG_BRC', 'KERENDIA_SAMPLING_KIT_BRC',
                'KERENDIA_SAMPLE_HOUSING_BOX_BRC']:
        col_name = f"TOTAL_SAMPLE_{cat}{suffix}"
        if col_name in df.columns:
            total = df.select(F.sum(col_name)).first()[0]
            print(f"{cat}: {total}")
```

**Dropped vs Shipped:**
- `SAMPLE_DROPPED` = hand-delivered by rep during visit
- `SAMPLE_SHIPPED` = mailed to HCP
- Both contribute to `TOTAL_OVERALL_SAMPLE`
- Operational distinction; no modeling implication prescribed

**Max sample value:** 290 observed for a single HCP in a single window. This is plausible
for high-volume prescribers but worth flagging if it grows significantly.

**Exclusion:** `KERENDIA PATIENT BROCHURES BRC` is explicitly excluded from sample counts.
Verify:
```python
brc_cols = [c for c in df.columns if 'PATIENT_BROCHURE' in c.upper()]
assert len(brc_cols) == 0, f"Patient brochure columns found: {brc_cols}"
```

### 3.6 Speaker Programs

**Key stats:**
- Output rows: ~156,677
- 68 columns (~11 base features × 6 rolling windows + 2 keys)
- 17,151 distinct HCPs (smallest HCP-level non-personal channel)

**Known zero-variance features:**
- `TOTAL_SPKR_EVNT_TYP_SPKR_PRGM_IN_LAST_*_MONTH`: stddev=0, max=0
- `TOTAL_SPKR_EVNT_TYP_NON_SPKR_PRGM_IN_LAST_*_MONTH`: stddev=0, max=0

Both event type features carry no signal in the current data. Zero-variance filtering
is a model-training concern.

**Event format distribution:**
- Face-to-Face and In-Office Meal are typically the most common formats
- Remote and Hybrid formats increased post-2020 but may still be sparse
- Out-Office Meal is the least common

**Topic mapping validation:**
```python
for topic in ['CKD', 'CVR', 'INTRO', 'OTHER']:
    col_name = f"TOTAL_SPKR_EVNT_TPIC_{topic}_IN_LAST_6_MONTH"
    if col_name in df.columns:
        non_zero = df.filter(F.col(col_name) > 0).count()
        print(f"{topic}: {non_zero} non-zero rows")
```

### 3.7 Free Trial Program

**Key stats:**
- Output rows: ~718,520
- 9 columns (6 lag windows + RUNNING_TOTAL + HCP_COHORT_ID + PULL_DT)
- Date range: 2021-01-13 to 2025-07-18

**Reversal handling validation:**
```python
# After reversal removal, no net-zero claim groups should remain
# This is already handled in the pipeline, but verify:
running_total = df.select(F.min("RUNNING_TOTAL_RX_FTP"), F.max("RUNNING_TOTAL_RX_FTP")).first()
print(f"Running total range: {running_total[0]} to {running_total[1]}")

# Negative running totals would indicate reversal logic failure
neg_running = df.filter(F.col("RUNNING_TOTAL_RX_FTP") < 0).count()
print(f"Negative running totals: {neg_running}")
assert neg_running == 0, "Reversal handling may have failed"
```

**ID key note:** FTP uses `PROVIDER_ID` (NPI-based) as its native key, unlike most channels
that use BHID. The NPI→BHID mapping is applied before cross-joining with cohort dates.

---

## 4. Cross-Channel Alignment Checks

### 4.1 Cohort Coverage

For HCP_COHORT_ID-keyed channels (HQ Emails, Samples, Speaker Programs, FTP):

```python
for name, path in channel_paths.items():
    df = spark.read.parquet(path)
    if 'HCP_COHORT_ID' in df.columns:
        cohorts = df.withColumn("COHORT", F.split("HCP_COHORT_ID", "_").getItem(1)) \
                    .select("COHORT").distinct().orderBy("COHORT").collect()
        print(f"{name}: {len(cohorts)} cohorts")
```

Expected: 26 cohorts (C01–C26) for each channel.

### 4.2 HCP Overlap Across Channels

```python
from functools import reduce

hcp_sets = {}
for name, df in channel_dfs.items():
    if 'HCP_COHORT_ID' in df.columns:
        hcps = df.withColumn("BHID", F.split("HCP_COHORT_ID", "_").getItem(0)) \
                 .select("BHID").distinct()
        hcp_sets[name] = hcps
        print(f"{name}: {hcps.count()} distinct BHIDs")

# Pairwise overlaps
names = list(hcp_sets.keys())
for i in range(len(names)):
    for j in range(i+1, len(names)):
        overlap = hcp_sets[names[i]].intersect(hcp_sets[names[j]]).count()
        print(f"{names[i]} ∩ {names[j]}: {overlap}")
```

### 4.3 DTC Geographic Coverage

```python
dtc_df = spark.read.parquet(dtc_path)
dma_count = dtc_df.select("DMA_Code").distinct().count()
month_count = dtc_df.select("DATA_MONTH").distinct().count()
print(f"DTC: {dma_count} distinct DMAs, {month_count} distinct months")

# Check DMA → ZIP mapping coverage
dma_zip = spark.read.parquet("...DMA Zip Mapping.parquet")
print(f"DMA Zip Mapping: {dma_zip.count()} rows, {dma_zip.select('DMA Code').distinct().count()} distinct DMAs")

# Unmatched DMAs
dtc_dmas = dtc_df.select("DMA_Code").distinct()
mapping_dmas = dma_zip.select(F.col("DMA Code").alias("DMA_Code")).distinct()
unmatched = dtc_dmas.subtract(mapping_dmas)
print(f"Unmatched DMAs in DTC (no ZIP mapping): {unmatched.count()}")
```

### 4.4 Digital NPI-to-PROVIDER_ID Mapping

Digital output uses NPI_NUMBER. In the combine notebook, NPI is mapped to PROVIDER_ID
via `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRVDR`. Validate mapping coverage:

```python
digital_npis = digital_df.select("NPI_NUMBER").distinct()
mapping_npis = spark.read.parquet("...npi_mapping...").select("NPI_NUMBER").distinct()
unmatched = digital_npis.subtract(mapping_npis)
print(f"Digital NPIs without PROVIDER_ID mapping: {unmatched.count()} / {digital_npis.count()}")
```

---

## 5. Combine-Step Validation

After all non-personal channels are joined in the combine notebook, validate:

```python
combined = spark.read.parquet(combined_path)

# Total expected non-personal features: ~832
print(f"Combined columns: {len(combined.columns)}")

# Null rate by channel prefix after left join (before fillna)
channel_prefixes = {
    'Digital': 'DIGITAL_',
    'HQ Emails': 'TOTAL_BOUNCE',
    'DTC': 'DTC_PROMOTION_',
    'Samples': 'TOTAL_SAMPLE_',
    'Speaker': 'TOTAL_SPKR_',
    'FTP': 'TOTAL_RX_FTP'
}

for name, prefix in channel_prefixes.items():
    sample_cols = [c for c in combined.columns if c.startswith(prefix)][:1]
    if sample_cols:
        null_rate = combined.filter(F.col(sample_cols[0]).isNull()).count() / combined.count()
        print(f"{name} null rate: {null_rate:.1%}")
```

---

## 6. Data Quality Red Flags

| Check | Expected | Red Flag |
| --- | --- | --- |
| Row count changes > 10% | Stable across runs | Source data or filter change |
| Digital column count growth | ~665 | New MMX channels/tactics added new pivots |
| DTC column count > 12 | 12 (8 + 2 + 2 keys) | PulsePoint/TTD cells were activated |
| Negative RUNNING_TOTAL_RX_FTP | 0 | Reversal logic failure |
| Cohort count ≠ 26 | Exactly 26 | Anchor dates file changed |
| HCP_COHORT_ID duplicates | 0 | Aggregation producing dupes |
| DMA codes unmatched in ZIP mapping | 0 | Mapping file outdated |
| HQ Emails Sent < Click | Sent ≥ Click | Data corruption or filter issue |
| Speaker event type features non-zero | Currently all zero | New data — update zero-variance note |
| Sample max > 500 in any window | Max ~290 observed | Possible aggregation error |
