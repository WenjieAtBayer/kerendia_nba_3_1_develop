# RX Recency & First Occurrence Features — Cell-by-Cell Template

This template reproduces the notebook `01_rx_features_rec_&_first_occ` (35 cells).
Source: `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/01_Patient_Features/01_rx_features_rec_&_first_occ`

Each section below corresponds to one cell. Create cells in order.
Cell type is indicated as [md], [run], or [python].

**IMPORTANT — Markdown cells:** For [md] cells, the code block starts with `%md` followed by a newline.
When creating the notebook cell, set `language="markdown"` and use only the content AFTER the `%md\n` line
as the cell source. Do NOT include `%md` in the cell content — it is the cell language marker, not source code.

**[run] cells:** Set `language="run"` and include the full `%run "..."` line as the cell source.

---

## Cell 1 [md] — Title, Objective, Glossary, Input/Output

```python
%md
### Feature Engineering & Selection : Rx

##### Objective:
This notebook aims to create frequency, recency, and other features for Medical Prescriptions (Rx) data. 
- It leverages multiple helper modules to generate these features.
- The generated features are then passed through a feature reduction step, which uses AI/ML models to select the most influential features for further modeling.

##### Glossary:
- <B>Anchor Date/Cohort</B> - A Reference point. It serves as a fixed point in time from which other dates or events are measured or referenced.
- <B>Frequency</B> - Features determining occurrence of events in past n days, indicating how many times an event has ocurred in patient's journey.
- <B>Recency</B> - Features to assess how recently events occurred in the patient's journey.
- <B>Change in frequency</B> - Features capturing variations in the patient's event occurrence over time.
- <B>First Occurrence</B> - These features provide critical insights into the timing of significant events, helping to identify when an event occurred first time in a patient's journey in lookback duration.
- <B>Skewness</B> - Features determining concentration of events in patient's journey.

##### Input:
- Processed Rx claims data

  Required set of columns:
  1. Patient Identifier 
  2. Event name - Name of Rx/Px/Dx/Lab test etc.
  3. Event time - Days since event has happened from Anchor date.
  4. Type of event - Rx/Px/Dx/Lab etc.

##### Output:
- First Occurrence features

      "/FileStore/Feature Accelerator/Interim Output/rx_first_occurrence_features.parquet"

- Recency features

      "/FileStore/Feature Accelerator/Interim Output/rx_recency_features.parquet"

- Frequency features

      "/FileStore/Feature Accelerator/Interim Output/rx_frequency_features.parquet"

- Final dataFrame with most prominent & influential set of Rx features.
```

---

## Cell 2 [md] — Import Libraries header

```python
%md
##### Import Libraries
```

---

## Cell 3 [run] — Load connection helper (Snowflake auth, imports)

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"
```

---

## Cell 4 [md] — Input Parameters header

```python
%md
##### Input Parameters
```

---

## Cell 5 [md] — Description of cohort parameters

```python
%md
<i>Cohort Start Date - Reference start point from which the patient jounrney is analyzed<br>

<i>Cohort End Date- Reference end point until which the patient journey to be analyzed<br>

<i>Months Increment - Separation between each cohort in months<br>

<i>Lookback Duration - # of months required in lookback to analyze patient's journey<br>

<i>File Path - Path for input claims data<br>
```

---

## Cell 6 [run] — Load config helper (date params, file paths, column mappings)

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_config"
```

---

## Cell 7 [md] — Section A header: Data Ingestion & Processing

```python
%md
###A. Data Ingestion & Processing

<I>Load input data & transform to required format</I>
```

---

## Cell 8 [run] — Load DataFrameMerger helper class

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_load_processed_data"
```

---

## Cell 9 [python] — DataFrameMerger: blank out non-RX paths, merge all claims

```python
dx1_file_path =""
dx2_file_path =""
px1_file_path=""
px2_file_path=""
lab_data1_file_path=""
lab_data2_file_path=""

data_merger = DataFrameMerger(rx1_file_path, rx2_file_path, px1_file_path, px2_file_path, dx1_file_path , dx2_file_path,
                 lab_data1_file_path, lab_data2_file_path, cohort_start_date, cohort_end_date, months_increment,
                 lookback_duration, prediction_duration,claims_id_rx,claims_patient_id_rx,claims_event_date_rx ,claims_event_name_rx,event_prevalence)

claims_data = data_merger.merge_all()
```

---

## Cell 10 [python] — Extract RX claims, compute EVENT_TIME (days from event to lookback end)

```python
rx_claims_loaded = claims_data ["rx_from_claims"]
rx_claims_loaded = rx_claims_loaded.withColumn("EVENT_TIME", datediff(rx_claims_loaded["LOOKBACK_END_DATE"], rx_claims_loaded["EVENT_DATE"]))
```

---

## Cell 11 [python] — Garbage collection after large merge

```python
gc.collect()
```

---

## Cell 12 [python] — Filter out future events (no data leakage): EVENT_TIME >= 0

```python
# filter feature for first occurence so it does not see future data

rx_claims_loaded = rx_claims_loaded.filter(col("EVENT_TIME") >= 0)
```

---

## Cell 13 [python] — Debug: display distinct SERIAL_NO values

```python
rx_claims_loaded.select("SERIAL_NO").distinct().display()
```

---

## Cell 14 [md] — Batch Processing header

```python
%md
##### Batch Processing
```

---

## Cell 15 [run] — Load DataFrameBatchProcessor helper class

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_batch_processing"
```

---

## Cell 16 [python] — Create batch processor and split claims into batches by cohort

```python
# Initialising Batch processor object
processor = DataFrameBatchProcessor(spark)

# Creating batches
batch_list_rx = processor.batch_creation_by_type(rx_claims_loaded)
print('# of Batches created:', len(batch_list_rx))
```

---

## Cell 17 [md] — Section B header: Feature Engineering

```python
%md
###B. Feature Engineering
```

---

## Cell 18 [md] — Section B1 header: First Occurrence Features

```python
%md
##### B1. First Occurrence Features
```

---

## Cell 19 [run] — Load first_occurrence_of_event helper class

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_first_occurrence_features"
```

---

## Cell 20 [python] — Loop over batches: compute first occurrence features (max EVENT_TIME per EVENT_NAME)

```python
# Passing the batches stored in the list one by one to create the 'First Occurence Event' for each batch.

# Create an empty list to store the First occurence features dataframe for each batch
first_occ_features_batch_list_rx = []
i = 0

for batch in batch_list_rx:
  # Check if batch is not empty
  if not batch.isEmpty():
    # Initialze the constructor to create object
    first_occ_features_rx = first_occurrence_of_event(spark, batch,'HCP_COHORT_ID','EVENT_NAME','EVENT_TIME','EVENT_TYPE')
    # Generate first occurence features
    rx_claims_first_occ_batch_df = first_occ_features_rx.aggregate_first_event_time()
    print('# of HCP-Cohorts in batch:',rx_claims_first_occ_batch_df.count())

    # Append to original feature list
    first_occ_features_batch_list_rx.append(rx_claims_first_occ_batch_df)
    i = i+1
    print('Batch',i,'completed\n')
    del rx_claims_first_occ_batch_df
    gc.collect()
```

---

## Cell 21 [python] — Union all first occurrence batch DataFrames

```python
# Convert all the batches into single dataframe using Union
if not first_occ_features_batch_list_rx:    
  raise ValueError("The list of DataFrames is empty.")

# Initilise the dataframe with first batch
rx_claims_first_occ_df = first_occ_features_batch_list_rx[0]

# Iterate over each batch and concatenate them together (Keep allow missing columns = True to avoid missing any column)
for df in first_occ_features_batch_list_rx[1:]:     
  rx_claims_first_occ_df = rx_claims_first_occ_df.unionByName(df, allowMissingColumns=True)

rx_claims_first_occ_df = rx_claims_first_occ_df
print('Shape:',rx_claims_first_occ_df.count(), len(rx_claims_first_occ_df.columns))
print('# distinct HCP-Inference:',rx_claims_first_occ_df.select("HCP_COHORT_ID").distinct().count())
```

---

## Cell 22 [python] — Save first occurrence features to Delta

```python

# Save the output file

rx_claims_first_occ_df.write \
    .format("delta") \
    .mode("overwrite") \
    .save("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/rx_first_occurrence_features")
```

---

## Cell 23 [python] — Debug: display first occurrence (commented out)

```python
# rx_claims_first_occ_df.display()
```

---

## Cell 24 [python] — Free memory: delete merger objects before recency section

```python
del claims_data, data_merger
```

---

## Cell 25 [python] — Garbage collection before recency processing

```python
gc.collect()
```

---

## Cell 26 [run] — Load recency helper class (6 sub-features)

```python
%run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_recency_features"
```

---

## Cell 27 [python] — Recency-specific 12M filter: keep events within LOOKBACK_START to LOOKBACK_END

```python
# Filter claims for last 12 months from Anchor
rx_claims_last_12_months_filtered = rx_claims_loaded.filter((col("EVENT_DATE") >= col("LOOKBACK_START_DATE")) & 
                                                                (col("EVENT_DATE") <= col("LOOKBACK_END_DATE")))
```

---

## Cell 28 [md] — Batch Processing header (for recency re-batching)

```python
%md
###### Batch Processing
```

---

## Cell 29 [python] — Re-batch after 12M filter (recency uses only 12M data)

```python
# Initialising Batch processor object
processor = DataFrameBatchProcessor(spark)

# Creating batches
batch_list_rx = processor.batch_creation_by_type(rx_claims_last_12_months_filtered)
print('# of Batches created:', len(batch_list_rx))
```

---

## Cell 30 [python] — Loop over batches: compute recency features (6 sub-features per HCP_COHORT_ID)

```python
# Load the claims data and apply the features creation function on each batch and finally concatenate the batches to form the final dataframe
recency_features_batch_list_rx = []
i = 0

for batch in batch_list_rx:
  # Check if batch is not empty
  if not batch.isEmpty():
    # Initialze the constructor to create object
    recency_features_rx = recency(spark,batch,'HCP_COHORT_ID','EVENT_NAME','EVENT_TIME','EVENT_TYPE',time_windows)
    # Generate Recency features
    recency_batch = recency_features_rx.recency_features()
    print('# of Patient Cohorts in batch:', recency_batch.count())

    # Append to original feature list
    recency_features_batch_list_rx.append(recency_batch)
    i = i+1
    print('Batch',i,'completed\n')
    del recency_batch
    gc.collect()
```

---

## Cell 31 [python] — Union all recency batch DataFrames

```python
# Convert all the batches into single dataframe using Union

if not recency_features_batch_list_rx:    
  raise ValueError("The list of DataFrames is empty.")

# Initilise the dataframe with first batch
final_concatenated_recency_rx_df = recency_features_batch_list_rx[0]

# Iterate over each batch and concatenate them together (Keep allow missing columns = True to avoid missing any column)
for df in recency_features_batch_list_rx[1:]:     
  final_concatenated_recency_rx_df  = final_concatenated_recency_rx_df.unionByName(df, allowMissingColumns=True)

# final_concatenated_recency_rx_df = final_concatenated_recency_rx_df.cache()
print('Shape:', final_concatenated_recency_rx_df.count(), len(final_concatenated_recency_rx_df.columns))
print('# distinct Patient-Cohorts:', final_concatenated_recency_rx_df.select("HCP_COHORT_ID").distinct().count())
```

---

## Cell 32 [python] — Save recency features to Delta

```python
# Save the output file
final_concatenated_recency_rx_df.write \
    .format("delta") \
    .mode("overwrite") \
    .save("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/rx_recency_features")
```

---

## Cell 33 [python] — Verification: read back recency features from Delta

```python
recency = spark.read.format("delta").load("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/rx_recency_features")
```

---

## Cell 34 [python] — Display recency features for verification

```python
recency.display()
```

---

## Cell 35 [python] — Empty trailing cell

```python
```

---

## Adapting for Other Claim Types

To switch from RX to another claim type, change these values (see parameterization table in SKILL.md):

| Variable | RX | DX | PX | Lab |
| --- | --- | --- | --- | --- |
| Non-blank file path | `rx1_file_path`, `rx2_file_path` | `dx1_file_path`, `dx2_file_path` | `px1_file_path`, `px2_file_path` | `lab_data1_file_path`, `lab_data2_file_path` |
| Config column vars | `claims_id_rx`, etc. | `claims_id_dx`, etc. | `claims_id_px`, etc. | `claims_id_lab`, etc. |
| Dict key | `rx_from_claims` | `dx_from_claims` | `px_from_claims` | `lab_data_from_claims` |
| Output names | `rx_first_occurrence_features`, `rx_recency_features` | `dx_first_occurrence_features`, `dx_recency_features` | `px_first_occurrence_features`, `px_recency_features` | `lab_first_occurrence_features`, `lab_recency_features` |
