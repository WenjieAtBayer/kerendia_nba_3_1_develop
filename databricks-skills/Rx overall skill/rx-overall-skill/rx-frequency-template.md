# RX Frequency Features — Cell-by-Cell Template

This template reproduces the notebook `01_rx_frequency_features` (66 cells).
Source: `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/01_Patient_Features/01_rx_frequency_features`

Each section below corresponds to one cell. Create cells in order.
Cell type is indicated as [md], [run], or [python].

**IMPORTANT — Markdown cells:** For [md] cells, the code block starts with `%md` followed by a newline.
When creating the notebook cell, set `language="markdown"` and use only the content AFTER the `%md\n` line
as the cell source. Do NOT include `%md` in the cell content — it is the cell language marker, not source code.

**[run] cells:** Set `language="run"` and include the full `%run "..."` line as the cell source.

This notebook has 4 logical sections:
- Sub-type A: Claim Count (monthly pivot) — Cells 1-18
- Sub-type B+C: Change in Frequency — Cells 19-35
- Sub-type D: Unique Patient Counts — Cells 36-53
- Combine Everything — Cells 54-66

---

## Cell 1 [md] — Title, Objective, Glossary, Input/Output

```python
%md
### Feature Engineering of Frequency Features

##### Objective:
This notebook aims to create frequency features for Medical Prescriptions (rx) data. 
- It leverages multiple helper modules to generate these features.
- The generated features are then passed through a feature reduction step, which uses AI/ML models to select the most influential features for further modeling.

##### Glossary:
- <B>Anchor Date/Cohort</B> - A Reference point. It serves as a fixed point in time from which other dates or events are measured or referenced.
- <B>Frequency</B> - Features determining occurrence of events in past n days, indicating how many times an event has ocurred in patient's journey.


##### Input:
- Processed rx claims data

  Required set of columns:
  1. Patient Identifier 
  2. Event name - Name of Rx/Px/rx/Lab test etc.
  3. Event time - Days since event has happened from Anchor date.
  4. Type of event - Rx/Px/rx/Lab etc.

##### Output:

- Frequency features

      "/FileStore/Feature Accelerator/Interim Output/rx_frequency_features.parquet"

- Final dataFrame with most prominent & influential set of rx features.
```

---

## Cell 2 [md] — Section header: Rx count and Lag Rx Count Features

```python
%md
## Rx count and Lag Rx Count Features 
```

---

## Cell 3 [run] — Load connection helper (Snowflake auth, imports)

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```

---

## Cell 4 [run] — Load config helper (file paths, column mappings)

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config"
```

---

## Cell 5 [python] — Read RX claims from rx_freq_file_path (12M claims Delta)

```python
# Reading rx Claims
rx_claims = spark.read.format("delta").load(rx_freq_file_path)

print("Shape :", rx_claims.count(), len(rx_claims.columns))
```

---

## Cell 6 [python] — Add monthly column SVC_DT_M from SVC_DT

```python
# Creating a month column using SVC_DT
rx_claims = rx_claims.withColumn("SVC_DT_M", F.date_trunc('MM', col("SVC_DT")))
```

---

## Cell 7 [python] — Define index columns for grouping

```python
index_cols = ['PROVIDER_ID', 'SVC_DT_M']
```

---

## Cell 8 [python] — Commented out date filter (for manual debugging)

```python
# rx_claims = rx_claims.filter((col("SVC_DT")>='2022-02-01') & (col("SVC_DT")<='2025-03-31'))
# print("Shape :", rx_claims.count(), len(rx_claims.columns))
```

---

## Cell 9 [md] — Section header: Frequency Features

```python
%md
##### Frequency Features 
```

---

## Cell 10 [python] — Pivot by PRODUCT_GROUP, count claims, sanitize column names with FREQ_ prefix

```python
freq_rx_claims = rx_claims.groupBy(index_cols).pivot("PRODUCT_GROUP").agg(F.count(F.lit(1)).alias("claim_count"))#.na.fill(value = 0)

# Removing unwanted characters and making feature names to uppercase
freq_rx_claims = freq_rx_claims.select([F.col(c).alias('FREQ_' + c.replace(", ", " ").replace("+", "and").replace("/", " or").replace("-", "_").replace(" ", "_").replace("__", "_").replace("(", "").replace(")", "").replace("[", "").replace("]", "").upper()) if c not in index_cols else col(c) for c in freq_rx_claims.columns])
print("Shape :", freq_rx_claims.count(), len(freq_rx_claims.columns))
```

---

## Cell 11 [python] — Define step2_fill_missing: creates dense spine (all HCP x all months)

```python
def step2_fill_missing(df, key_col, date_col):

  # get all possible dates
  date_list_df = (
    df
    .select(date_col)
    .agg(F.min(date_col).alias('min_date'), 
         F.max(date_col).alias('max_date'))
    .withColumn(date_col, F.explode(F.expr('sequence(min_date, max_date, interval 1 month)'))).drop("min_date", "max_date")
  ) 

  # get patient id distinct list
  patient_id_list_df = df.select(key_col).distinct()

  # create all possible hcp id list and date list
  patient_date_full_list = patient_id_list_df.crossJoin(date_list_df).orderBy(key_col, date_col)

  # 
  step2_output = (patient_date_full_list
                  .join(df, on=[key_col, date_col], how="left")
  #               .fillna(0)
               )

  return step2_output
```

---

## Cell 12 [python] — Define step3_lag: rolling window sums over N months

```python
def step3_lag(df, key_col, date_col, last_i_month_list):

  window_base = Window.partitionBy(key_col).orderBy(date_col)

  # get the feature cols
  features = [col for col in df.columns if col not in [key_col, date_col]]

  last_i_month = [F.sum(col).over(window_base.rowsBetween(-i+1, 0)).alias(col +"_IN_LAST_" + str(i) + "_MONTH") for i in last_i_month_list for col in features]


  step3_output = df.select("*", *last_i_month)#, *running_total)

  return step3_output
```

---

## Cell 13 [python] — Define process_and_join: orchestrates fill_missing -> lag -> drop original feature cols

```python
def process_and_join(df, last_i_month_list):
    # Step 1
    df_spine_step2 = step2_fill_missing(df, key_col="PROVIDER_ID", date_col="SVC_DT_M")

    # Step 2
    df_spine_step3 = step3_lag(df_spine_step2, key_col="PROVIDER_ID", date_col="SVC_DT_M", last_i_month_list=last_i_month_list)
    # Step 3
    keep_cols = ['PROVIDER_ID', 'SVC_DT_M']
    cols_to_drop = [col_name for col_name in df_spine_step2.columns if col_name not in keep_cols]

    df_spine_step3 = df_spine_step3.drop(*cols_to_drop)
    # df_spine_step3 = df_spine_step3.filter(col("SVC_DT_M") >= lit(min_lookback_end_date))

    # Cleanup
    del df_spine_step2, df
    gc.collect()

    return df_spine_step3
```

---

## Cell 14 [python] — Generate lag features with rolling windows [1, 2, 3, 6, 12] months

```python
freq_features= freq_rx_claims.select(*freq_rx_claims.columns)
for df in [freq_rx_claims]:
    lag_freq_features = process_and_join(df=freq_rx_claims, last_i_month_list = [1,2,3,6,12])
```

---

## Cell 15 [python] — Debug: display lag freq columns (commented out)

```python
# pd.DataFrame(freq_features.columns).display()
```

---

## Cell 16 [python] — Display lag freq columns as DataFrame

```python
pd.DataFrame(lag_freq_features.columns).display()
```

---

## Cell 17 [python] — Save claim count features to Delta (rx_frequency_features)

```python
freq_features.write \
    .format("delta") \
    .mode("overwrite") \
    .save("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/rx_frequency_features")
```

---

## Cell 18 [python] — Save lag frequency features to Delta (rx_lag_frequency_features)

```python
lag_freq_features.write \
    .format("delta") \
    .mode("overwrite") \
    .save("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/rx_lag_frequency_features")
```

---

## Cell 19 [md] — Section header: Change Frequency of Rx count Features

```python
%md
## Change Frequency of Rx count Features
```

---

## Cell 20 [python] — Read cohort anchor dates CSV, add SVC_DT_M from LOOKBACK_END_DATE

```python
import pandas as pd
import pyspark.sql.functions as F
cohort_df = spark.createDataFrame(pd.read_csv("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/hcp_model_inference_anchor_dates.csv"))


cohort_df = cohort_df.withColumn("SVC_DT_M", F.trunc(cohort_df["LOOKBACK_END_DATE"], "MM"))

updated_cohort_df = cohort_df.select("SVC_DT_M","COHORT")
```

---

## Cell 21 [python] — Read HCP universe, crossJoin with cohort dates to create full HCP x cohort grid

```python
hcp_universe = spark.read.format("delta").load(hcp_universe_path).select('PROVIDER_ID').distinct()

cohort_df = spark.createDataFrame(pd.read_csv("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/hcp_model_inference_anchor_dates.csv"))


cohort_df = cohort_df.withColumn("SVC_DT_M", F.trunc(cohort_df["LOOKBACK_END_DATE"], "MM"))

updated_cohort_df = cohort_df.select("SVC_DT_M","COHORT")

hcp_universe = hcp_universe.crossJoin(updated_cohort_df)
hcp_universe.count()
```

---

## Cell 22 [python] — Debug: display updated cohort DataFrame

```python
updated_cohort_df.display()
```

---

## Cell 23 [python] — Join lag_freq_features with HCP universe to filter to valid HCP x cohort months

```python
# Joining with hcp_universe to get features data for COHORTS from LOOKBACK_START_DATE to LOOKBACK_END_DATE
lag_freq_features = hcp_universe.select("PROVIDER_ID", "SVC_DT_M").distinct().join(lag_freq_features, on = ["PROVIDER_ID", "SVC_DT_M"], how='inner')
print("Shape :", lag_freq_features.count(), len(lag_freq_features.columns))
```

---

## Cell 24 [python] — Debug: count distinct PROVIDER_ID x SVC_DT_M

```python
lag_freq_features.select("PROVIDER_ID", "SVC_DT_M").distinct().count()
```

---

## Cell 25 [python] — Debug: search for JARDIANCE columns

```python
for cols in lag_freq_features.columns:
    if 'JARDIANCE' in cols:
        print(cols)
```

---

## Cell 26 [python] — Extract event names from lag column names using regex

```python
columns = lag_freq_features.columns

# Regex pattern to extract event names
pattern = r"FREQ_(.*)_IN_LAST_\d+_MONTH"

# Extract event names using regex
event_names = [re.match(pattern, col).group(1) for col in columns if re.match(pattern, col)]

from collections import OrderedDict
event_names = list(OrderedDict.fromkeys(event_names))

print("# Events :", len(event_names))
```

---

## Cell 27 [python] — Compute change in frequency: (recent/N) - ((12M - recent)/(12-N))

```python
from pyspark.sql import functions as F

# Keep a list of all new columns to be added
new_columns = []
recent_windows = [1,2,3,6]

for event in event_names:
    col_12 = F.col(f"FREQ_{event}_IN_LAST_12_MONTH")
    for N_month in recent_windows:
        N_days = N_month
        col_N = F.col(f"FREQ_{event}_IN_LAST_{N_month}_MONTH")
        change_col_name = f"CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_{event}_IN_LAST_{N_month}_MONTH"
        change_expr = ((col_N / F.lit(N_days)) - ((col_12 - col_N) / F.lit(12 - N_days))).alias(change_col_name)
        new_columns.append(change_expr)

# Select everything in one go
change_freq_features = lag_freq_features.select("*", *new_columns)
```

---

## Cell 28 [python] — Debug: inspect a single change column expression

```python
new_columns[1]
```

---

## Cell 29 [python] — Debug: count and column count of change freq features

```python
change_freq_features.count(), len(change_freq_features.columns)
```

---

## Cell 30 [python] — Save combined lag + change frequency to Delta (rx_freq_and_change_frequency)

```python
change_freq_features.write \
    .format("delta") \
    .mode("overwrite") \
    .save("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/rx_freq_and_change_frequency")
```

---

## Cell 31 [python] — Debug: display change freq features

```python
change_freq_features.display()
```

---

## Cell 32 [python] — Identify raw FREQ_ columns (not CHANGE_IN_FREQ_) to drop

```python
freq_columns = [col_name for col_name in change_freq_features.columns if "FREQ_" in col_name and "CHANGE_IN_FREQ_" not in col_name]
len(freq_columns)
```

---

## Cell 33 [python] — Drop raw FREQ_ columns, keep only CHANGE_IN_FREQ_ features

```python
change_freq_features = change_freq_features.drop(*freq_columns)
print("Shape :", change_freq_features.count(), len(change_freq_features.columns))
```

---

## Cell 34 [python] — Debug: display remaining columns after drop

```python
pd.DataFrame(change_freq_features.columns).display()
```

---

## Cell 35 [python] — Save change-only frequency to Delta (rx_change_frequency)

```python
# Save the output file
change_freq_features.write \
    .format("delta") \
    .mode("overwrite") \
    .save("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline//notebook_output/rx_change_frequency")
```

---

## Cell 36 [md] — Section header: Unique Counts of patients

```python
%md
## Unique Counts of patients
```

---

## Cell 37 [python] — Read RX claims from rx1_file_path (total claims, NOT rx_freq_file_path)

```python
# Reading rx Claims
rx_claims = spark.read.format("delta").load(rx1_file_path)

print("Shape :", rx_claims.count(), len(rx_claims.columns))
```

---

## Cell 38 [python] — Read cohort anchor dates, drop non-essential columns

```python
cohort_anchor_dates =  spark.createDataFrame(pd.read_csv("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/hcp_model_inference_anchor_dates.csv"))
cohort_anchor_dates = cohort_anchor_dates.drop('SERIAL_NO', 'ANCHOR_DATE', "PREDICTION_END_DATE", "PREDICTION_START_DATE", 'MERGE_KEY')
cohort_anchor_dates.show(5)
```

---

## Cell 39 [python] — Filter claims to lookback date range to reduce volume

```python
# Step 1: Filter claims to reduce data volume
max_lookback_end = cohort_anchor_dates.agg(F.max("LOOKBACK_END_DATE")).first()[0]
min_lookback_start = cohort_anchor_dates.agg(F.min("LOOKBACK_START_DATE")).first()[0]
print("Min lookback start:", min_lookback_start)
print("Max lookback end:", max_lookback_end)

rx_claims_filtered = rx_claims.filter(
    (F.col("SVC_DT") >= F.lit(min_lookback_start)) &
    (F.col("SVC_DT") <= F.lit(max_lookback_end))
)
print("Shape after filtering:", rx_claims_filtered.count(), len(rx_claims_filtered.columns))
```

---

## Cell 40 [python] — Broadcast cross-join claims with cohort anchor dates

```python
# Step 2: Broadcast Anchor Dates and perform cross join
claims_cross = rx_claims_filtered.crossJoin(F.broadcast(cohort_anchor_dates))
print("Shape after cross Join:", claims_cross.count(), len(claims_cross.columns))
```

---

## Cell 41 [python] — Filter to claims within cohort-specific lookback window

```python
# Step 3: Filter to claims within cohort-specific lookback window
claims_valid = claims_cross.filter(
    (F.col("SVC_DT") >= F.col("LOOKBACK_START_DATE")) &
    (F.col("SVC_DT") <= F.col("LOOKBACK_END_DATE"))
)
print("Shape after cross Join filtering:", claims_valid.count(), len(claims_valid.columns))
```

---

## Cell 42 [python] — Compute days_diff from LOOKBACK_END_DATE to SVC_DT

```python
# Step 4: Compute difference in days from lookback_end
claims_with_diff = claims_valid.withColumn(
    "days_diff", F.datediff(F.col("LOOKBACK_END_DATE"), F.col("SVC_DT"))
)
print("Shape:", claims_with_diff.count(), len(claims_with_diff.columns))
```

---

## Cell 43 [python] — Flag claims within each time window [30, 60, 90, 180, 360]

```python
# Step 5: Flag for each time window
time_windows = [30, 60, 90, 180, 360]
for w in time_windows:
    claims_with_diff = claims_with_diff.withColumn(
        f"flag_{w}", F.when(F.col("days_diff") <= w, 1).otherwise(0)
    )
```

---

## Cell 44 [python] — Dedup on [PROVIDER_ID, COHORT, PRODUCT_GROUP, PATIENT_ID] + flags

```python
# Step 6: Drop duplicate patient-HCP-rx-cohort combinations
claims_dedup = claims_with_diff.select(
    "PROVIDER_ID", "COHORT", "PRODUCT_GROUP", "PATIENT_ID", *[f"flag_{w}" for w in time_windows]
).dropDuplicates()
print("Shape :", claims_dedup.count(), len(claims_dedup.columns))
```

---

## Cell 45 [python] — Aggregate countDistinct(PATIENT_ID) per [PROVIDER_ID, COHORT, PRODUCT_GROUP] per window

```python
# Step 7: Aggregate unique patient counts by window
final_result = claims_dedup.groupBy("PROVIDER_ID", "COHORT", "PRODUCT_GROUP").agg(
    *[
        F.countDistinct(F.when(F.col(f"flag_{w}") == 1, F.col("PATIENT_ID"))).alias(f"pt_cnt_{w}_days")
        for w in time_windows
    ]
)
```

---

## Cell 46 [python] — Debug: display final_result columns

```python
final_result.columns
```

---

## Cell 47 [python] — Unpivot wide pt_cnt_{w}_days columns to long format using stack(5, ...)

```python
# Step 1: Unpivot wide columns to long format
time_windows = [30, 60, 90, 180, 360]

melted = final_result.selectExpr(
    "PROVIDER_ID", "COHORT", "PRODUCT_GROUP",
    *[f"pt_cnt_{w}_days as pt_cnt_{w}_days" for w in time_windows]
).selectExpr(
    "PROVIDER_ID", "COHORT", "PRODUCT_GROUP",
    "stack(5, " + ", ".join([f"'pt_cnt_{w}_days', pt_cnt_{w}_days" for w in time_windows]) + ") as (time_window, patient_count)"
)
print("Shape :", melted.count(), len(melted.columns))
```

---

## Cell 48 [python] — Create descriptive pivot column name: NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_{EVENT}_IN_LAST_{N}_DAYS

```python
# Step 2: Create final pivot column name
melted = melted.withColumn(
    "pivot_col_name",
    F.concat_ws(
        "_",
        F.lit("NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH"),
        F.upper(F.regexp_replace("PRODUCT_GROUP", "[^a-zA-Z0-9]", "_")),
        F.lit("IN_LAST"),
        F.regexp_extract("time_window", r"\d+", 0),  # extract window number
        F.lit("DAYS")
    )
)
print("Shape :", melted.count(), len(melted.columns))
```

---

## Cell 49 [python] — Pivot by pivot_col_name to create wide format with one column per event x window

```python
# Step 3: Pivot
pivoted = melted.groupBy("PROVIDER_ID", "COHORT").pivot("pivot_col_name").agg(F.first("patient_count"))
print("Shape :", pivoted.count(), len(pivoted.columns))
```

---

## Cell 50 [python] — Debug: display pivoted column names

```python
pd.DataFrame(pivoted.columns).display()
```

---

## Cell 51 [python] — Save patient count features to Delta (rx_num_patients_features)

```python
# Save the output file
pivoted.write \
    .format("delta") \
    .mode("overwrite") \
    .save("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline//notebook_output/rx_num_patients_features")
```

---

## Cell 52 [python] — Debug: count distinct PROVIDER_ID x COHORT

```python
pivoted.select("PROVIDER_ID","COHORT").distinct().count()
```

---

## Cell 53 [python] — Verification: read back patient count features from Delta

```python
rx_patient_count = spark.read.format("delta").load(
    "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/rx_num_patients_features"
)
```

---

## Cell 54 [md] — Section header: Combine Everything

```python
%md
### Combine Everything
```

---

## Cell 55 [python] — Create HCP universe x cohort crossJoin (same pattern as Cell 21)

```python
from pyspark.sql import functions as F

hcp_universe = spark.read.format("delta").load(hcp_universe_path).select('PROVIDER_ID').distinct()

cohort_df = spark.createDataFrame(pd.read_csv("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/query_output/hcp_model_inference_anchor_dates.csv"))

cohort_df = cohort_df.withColumn("SVC_DT_M", F.trunc(cohort_df["LOOKBACK_END_DATE"], "MM"))

updated_cohort_df = cohort_df.select("SVC_DT_M","COHORT")

hcp_universe = hcp_universe.crossJoin(updated_cohort_df)
hcp_universe.count()
```

---

## Cell 56 [python] — Debug: display cohort_df

```python
cohort_df.display()
```

---

## Cell 57 [python] — Create skeleton_df with HCP_COHORT_ID = PROVIDER_ID_COHORT

```python
from pyspark.sql.functions import concat_ws

skeleton_df = hcp_universe.select("PROVIDER_ID", "COHORT").distinct().withColumn(
    "HCP_COHORT_ID",
    concat_ws("_", hcp_universe["PROVIDER_ID"], hcp_universe["COHORT"])
)
```

---

## Cell 58 [python] — Read rx_frequency_features, join with HCP universe, add HCP_COHORT_ID

```python
from pyspark.sql.functions import concat_ws

rx_event_only_freq_features = spark.read.format("delta").load(
    "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/rx_frequency_features"
)



rx_event_only_freq_features = rx_event_only_freq_features.withColumn('SVC_DT_M', F.trunc(F.col('SVC_DT_M'), "MM"))

rx_event_only_freq_features = hcp_universe.select("PROVIDER_ID", "SVC_DT_M", "COHORT").distinct().join(rx_event_only_freq_features, on=["PROVIDER_ID","SVC_DT_M"], how="inner")

rx_event_only_freq_features = rx_event_only_freq_features.withColumn(
    "HCP_COHORT_ID",
    concat_ws("_", rx_event_only_freq_features["PROVIDER_ID"], rx_event_only_freq_features["COHORT"])
).drop("PROVIDER_ID", "SVC_DT_M", "COHORT")

```

---

## Cell 59 [python] — Read rx_freq_and_change_frequency, join with HCP universe, add HCP_COHORT_ID

```python
from pyspark.sql.functions import concat_ws

rx_lag_freq_and_change_freq_features = spark.read.format("delta").load("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/rx_freq_and_change_frequency")

rx_lag_freq_and_change_freq_features = rx_lag_freq_and_change_freq_features.withColumn('SVC_DT_M', F.trunc(F.col('SVC_DT_M'), "MM"))

rx_lag_freq_and_change_freq_features = hcp_universe.select("PROVIDER_ID", "SVC_DT_M", "COHORT").distinct().join(
    rx_lag_freq_and_change_freq_features, on=["PROVIDER_ID", "SVC_DT_M"], how="inner"
)

rx_lag_freq_and_change_freq_features = rx_lag_freq_and_change_freq_features.withColumn(
    "HCP_COHORT_ID",
    concat_ws("_", rx_lag_freq_and_change_freq_features["PROVIDER_ID"], rx_lag_freq_and_change_freq_features["COHORT"])
).drop("PROVIDER_ID", "SVC_DT_M", "COHORT")
```

---

## Cell 60 [python] — Read rx_num_patients_features, join with HCP universe, add HCP_COHORT_ID

```python
rx_num_patients_features = spark.read.format("delta").load("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline//notebook_output/rx_num_patients_features")

for cols in rx_num_patients_features.columns:
    if cols == "COHORT":
        print(cols)

# rx_num_patients_features = rx_num_patients_features.withColumn('SVC_DT_M', F.trunc(F.col('SVC_DT_M'), "MM"))

rx_num_patients_features = hcp_universe.select("PROVIDER_ID", "COHORT").distinct().join(
    rx_num_patients_features, on=["PROVIDER_ID", "COHORT"], how="inner"
)

rx_num_patients_features = rx_num_patients_features.withColumn(
    "HCP_COHORT_ID",
    concat_ws("_", rx_num_patients_features["PROVIDER_ID"], rx_num_patients_features["COHORT"])
).drop("PROVIDER_ID", "SVC_DT_M", "COHORT")
```

---

## Cell 61 [python] — Join all feature sets on HCP_COHORT_ID (left joins from skeleton)

```python
combined_features = skeleton_df.join(rx_lag_freq_and_change_freq_features, on = "HCP_COHORT_ID", how = "left").join(rx_num_patients_features, on = "HCP_COHORT_ID", how = "left")
```

---

## Cell 62 [python] — Debug: check for duplicate column names

```python
columns = combined_features.columns
duplicates = [col for col in set(columns) if columns.count(col) > 1]

print("Duplicated columns:", duplicates)
```

---

## Cell 63 [python] — Append _RX suffix to all non-protected columns to avoid cross-claim collisions

```python
from pyspark.sql.functions import col

protected_cols = {"PROVIDER_ID", "SVC_DT_M", "COHORT", "HCP_COHORT_ID"}
combined_features = combined_features.select(
    [col(c) if c in protected_cols else col(c).alias(f"{c}_RX") for c in combined_features.columns]
)
```

---

## Cell 64 [python] — Save combined accelerator features to Delta (rx_accelerator_features)

```python
combined_features.write.format("delta").mode("overwrite").save(
    "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/rx_accelerator_features"
)
```

---

## Cell 65 [python] — Debug: count and column count of combined features

```python
combined_features.count(), len(combined_features.columns)
```

---

## Cell 66 [python] — Debug: print schema of combined features

```python
combined_features.printSchema()
```

---

## Adapting for Other Claim Types

To switch from RX to another claim type, change these values (see parameterization table in SKILL.md):

| Variable | RX | DX | PX | Lab |
| --- | --- | --- | --- | --- |
| Freq input path var | `rx_freq_file_path` | `dx1_file_path` | `px1_file_path` | `lab_data1_file_path` |
| Patient count input path var | `rx1_file_path` | `dx1_file_path` | `px1_file_path` | `lab_data1_file_path` |
| Pivot column | `PRODUCT_GROUP` | `DIAGNOSIS_DESCRIPTION` | `PROCEDURE_DESCRIPTION` | `TEST_TYPE` |
| Patient count verb | `PRESCRIBED_WITH` | `DIAGNOSED_WITH` | `DID_PROCEDURE` | `DID_LAB_TEST` |
| Combine suffix | `_RX` | `_DX` | `_PX` | `_LAB` |
| Output prefix | `rx_` | `dx_` | `px_` | `lab_data_` |

**Lab-specific note:** Lab lag_frequency is saved as Parquet (not Delta). Use `spark.read.parquet()` instead of `spark.read.format("delta").load()`.

**Key differences per claim type in Combine Everything:**
- Lab uses `lab_data_` prefix (not `lab_`) for output table names
- PX appends `_PX` suffix (not `_PX_` — no trailing underscore)
- Patient count verb varies: PRESCRIBED_WITH / DIAGNOSED_WITH / DID_PROCEDURE / DID_LAB_TEST
