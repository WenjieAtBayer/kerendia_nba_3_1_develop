# NBA 3.0 Patient Features: How They Are Built

The NBA 3.1 changes and additions are in the companion file `NBA_3_1_Patient_Features_Recommendations.md`.

## 1. How NBA 3.0 builds the patient features

### 1.0 What is this section about?

The NBA (Next Best Action) model scores every HCP who could prescribe Kerendia and recommends the next promotional action. Besides promotional and Rx-volume features, the model uses **patient features**: numbers that describe the patients each HCP treats, built from IQVIA LAAD patient-level claims.

This section explains how the **NBA 3.0 Ops pipeline** (`/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/`) builds these features, so a reader can follow the logic without reading the code. Section 1.1 covers what all feature types share. Sections 1.2 to 1.9 then cover one feature type each, in three parts: (a) data sources and what each column means, (b) preprocessing steps, (c) features created. 1.10 and 1.11 cover the output tables and caveats. 1.12 to 1.14 cover the data used for this review, the model importance of each family and the column volume. 1.15 lists every patient feature that made it into the final 752-feature NBA 3.0 model, with its type. Numbers come from the latest ops run (lookback 2025-09-30 to 2026-09-30, cohort `I01`).

**In short**: for every HCP, the pipeline looks at the claims where that HCP is the prescriber (Rx), the referring or treating doctor on a diagnosis (Dx) or procedure (Px), or the doctor who ordered a kidney lab test (Lab). For each drug, diagnosis, procedure or test it then asks: how long has the HCP been seeing this, how recently, how often, is it going up or down, how many different patients, and how much of it happens in hospital.

| Feature type | Business question | Section |
| --- | --- | --- |
| First occurrence | How long has the HCP been seeing this event? | 1.2 |
| Recency | How recently did the HCP last see it? | 1.3 |
| Event volume (total / unique events) | How much activity, and how many different products or conditions? | 1.4 |
| Skewness | Is the activity concentrated recently or earlier in the year? | 1.5 |
| Frequency | How many claims in the last 1 to 12 months? | 1.6 |
| Change in frequency | Is the HCP writing or billing more or less than before? | 1.7 |
| Unique patients | How many different patients does this involve? | 1.8 |
| Hospitalization | How much of the HCP's activity is hospital-based? | 1.9 |

### 1.1 Shared foundations (apply to every feature type)

**Who is scored and on which date**

| Item | What it means | Last run |
| --- | --- | --- |
| HCP universe | `ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`: the LAAD `PROVIDER_ID`s the model scores. Every input file is inner-joined to it, with one exception (Dx all-events file, see 1.11) | 234,405 HCPs |
| Cohort | One scoring date per run, labelled `I01` | `I01` |
| `HCP_COHORT_ID` | `PROVIDER_ID` + `_` + cohort. This is the join key of every patient output | `7933852_I01` |

**Cohort dates** (set in `00_config` from the approved control dates, then derived in `00_load_processed_data`)

| Date | Rule | Last run |
| --- | --- | --- |
| Anchor date | First day of the prediction month | 2026-11-01 |
| Prediction start | 7th of the anchor month | 2026-11-07 |
| Prediction end | Prediction start + 30 days | 2026-12-07 |
| Lookback end | Last day of the month two months before the anchor month | 2026-09-30 |
| Lookback start | Lookback end - 365 days | 2025-09-30 |

There is one full month (October) between the lookback end and the prediction start, to allow for the lag in claims data. The dates are written to `ops_pipeline/query_output/hcp_model_inference_anchor_dates.csv`. The frequency, unique-patient and hospitalization notebooks read them back from that file.

**Source tables** (IQVIA LAAD in Snowflake, schema `PHCDW.PHCDW_STG_CAR`, pulled by `02_Input_Data_Creation/01_Input_data_creation`)

| Source | Fact table | Lookup table | One row is | Event name used |
| --- | --- | --- | --- | --- |
| Rx | `STG_CAR_IQV_LAAD_FCT_RX` | `STG_CAR_IQV_LAAD_DIM_PRD` (NDC to product) | One pharmacy claim | `PRODUCT_GROUP` (brand or molecule group, e.g. KERENDIA, FARXIGA) |
| Dx | `STG_CAR_IQV_LAAD_FACT_DX` | `STG_CAR_IQV_LAAD_DIM_DIAG` (ICD code to description) | One diagnosis code on a medical claim | `DIAGNOSIS_DESCRIPTION` |
| Px | `STG_CAR_IQV_LAAD_FACT_PX` | `STG_CAR_IQV_LAAD_DIM_PRCDR_CD` (CPT/HCPCS code to description) | One procedure code on a medical claim | `PROCEDURE_DESCRIPTION` |
| Lab | `STG_CAR_IQV_QUEST_TO_LAAD_HIST` | `STG_CAR_IQV_LAAD_DIM_PRVDR` (NPI to specialty) | One Quest lab result linked to LAAD | `TEST_TYPE` (GFR or UACR) |

**Columns used by the patient features** (other pulled columns, such as `DAYS_SUPPLY`, `REFILL_CODE`, `PAYER_PLAN_ID`, `SOB`, `COPAY_CARD_FLG` or `MEDIAN_TEST_RESULT`, are not used by these features)

| Column | What it means | Example |
| --- | --- | --- |
| `PROVIDER_ID` | LAAD ID of the HCP. Rx: the prescriber. Dx and Px: the referring doctor, or the rendering doctor if there is no referring doctor. Lab: the doctor who ordered the test | 7933852 |
| `PATIENT_ID` | De-identified LAAD patient ID. Stable across Rx, Dx, Px and Lab | 123456789 |
| `SVC_DT` | Date of service. Rx: fill date. Dx and Px: service date. Lab: test date | 2026-03-14 |
| Event name | The drug, diagnosis, procedure or test (see table above) | KERENDIA; TYPE 2 DIABETES MELLITUS WITH DIABETIC CHRONIC KIDNEY DISEASE; UACR |
| `DATA_SOURCE` (Dx, Px) | Where LAAD got the claim. `HX` = hospital-sourced claim. Used only for hospitalization (1.9) | HX |

**Input files** (`ops_pipeline/query_output/`) and their filter rules

| File | What is kept | Period | Feeds | Last run |
| --- | --- | --- | --- | --- |
| `rx_input_claims_12M_features_input` | Paid claims (`CLAIM_TYPE = 'PD'`) for 29 named product groups (Kerendia market basket and related CV/renal drugs) | Lookback only | Rx frequency, change (1.6, 1.7) | 188.1M rows, 230,779 HCPs |
| `rx_input_claims_total_events_and_first_occ_features_input` | Paid claims for the 243 product groups in `feature_selection/Kerendia NBA 3.0 - Rx Event List.csv` | 2021-01-02 to lookback end | Rx first occurrence, recency, volume, skewness, unique patients | 3.66B rows, 234,391 HCPs |
| `dx_input_claims_all_events_features_input` | Diagnoses in `Kerendia NBA 3.0 - Dx Event List.csv` (351 rows, 345 found). Not joined to the HCP universe | Lookback only | All Dx features | 1.20B rows, 1.57M HCPs |
| `dx_hospitalization_claims_all_events_features_input` | Same diagnoses, only `DATA_SOURCE = 'HX'` | Lookback only | Dx hospitalization (1.9) | 204.0M rows, 208,953 HCPs |
| `px_input_claims_all_events_features_input` | Procedures in `Kerendia NBA 3.0 - Px Event List.csv` (138 rows). 35 echocardiography codes (93303 to 93356, 93662, 0439T, 0932T, C8921 to C8930, C9786) are relabelled `echo_tests` | 2021-01-02 to lookback end | All Px features | 929.5M rows, 232,025 HCPs |
| `px_hospitalization_claims_all_events_features_input` | Same procedures, only `DATA_SOURCE = 'HX'` | No date filter (to 2026-10-02) | Px hospitalization (1.9) | 387.9M rows, 214,089 HCPs |
| `lab_input_claims_12M_and_first_occ_features_input` | eGFR and UACR results (rules below) | 2001-01-01 to lookback end | All Lab features | 244.8M rows, 170,304 HCPs |

Lab rules: a test is GFR if its name contains "GFR" or "GLOMERULAR", and UACR if it contains "ALB" or "RATIO". Other tests are dropped. The unit must be mL/min/1.73m2 or mg/g creatinine. Only plain numeric results are kept (values such as "<5", ">90" or ranges are dropped). The ordering HCP must be in primary care, internal medicine, NP or PA (`FM, FPG, GP, GPM, IFP, IM, IMG, IPM, NRP, PHA`). One row is kept per HCP, patient, day and test type.

`00_config` also lists `dx_freq_file_path` and `px_freq_file_path` (17 named diagnoses and 5 named procedures, full history). The patient notebooks reviewed here do not read these files.

**Common preprocessing** (in `00_load_processed_data`, used by the first-occurrence, recency, volume and skewness features)

1. **Standardize columns.** *What:* rename to `PROVIDER_ID`, `PATIENT_ID`, `EVENT_NAME`, `EVENT_DATE` and add `EVENT_TYPE` (`rx`, `dx`, `px`, `lab_data`). *Why:* one set of feature functions can then run on all four sources.
2. **One row per HCP, patient, event and day.** *What:* exact duplicates are removed. *Detail to know:* counts in 1.4 are therefore patient-days, not claims. A patient with two Kerendia claims from the same HCP on the same day counts once.
3. **Event prevalence filter.** *What:* events seen by fewer than `event_prevalence` of HCPs are dropped. *Detail to know:* the threshold is 0%, so in practice nothing is dropped. Kerendia, Invokana and Steglatro are always kept.
4. **Clean event names.** *What:* special characters become spaces, the name is lowercased, spaces become `_` and the source is added. *Example:* "AMLODIP BES/VALSAR" becomes `amlodip_bes_valsar_rx`.
5. **Attach cohort dates** and build `HCP_COHORT_ID`.
6. **Event time.** *What:* `EVENT_TIME` = days from the event date to the lookback end (0 = on the lookback end day, 30 = one month before). Rows after the lookback end are removed. *Why:* every feature is measured from the same reference date, and nothing from the prediction period can leak in.

---

### 1.2 First occurrence

**a. Data sources**

| Source | Input file | History covered | Events |
| --- | --- | --- | --- |
| Rx | `rx_input_claims_total_events_and_first_occ_features_input` | 2021-01-02 to lookback end | 243 product groups |
| Dx | `dx_input_claims_all_events_features_input` | Lookback only (12 months) | 345 diagnoses |
| Px | `px_input_claims_all_events_features_input` | 2021-01-02 to lookback end | 124 procedures |
| Lab | `lab_input_claims_12M_and_first_occ_features_input` | 2001-01-01 to lookback end | GFR, UACR |

Columns used: `PROVIDER_ID`, `PATIENT_ID`, `SVC_DT` and the event name (see 1.1).

**b. Preprocessing steps**

1. Apply the common steps in 1.1. All history up to the lookback end is kept (no 12-month cut).
2. For each `HCP_COHORT_ID` and event, take the **largest** `EVENT_TIME`, i.e. the oldest record.
3. Pivot so that each event becomes one column.

*Detail to know:* the notebooks (`01_rx_features_rec_&_first_occ` and the dx, px and lab equivalents) split the data into batches by cohort. The batch rule looks for IDs ending in `_C##`, but the IDs end in `_I01`, so everything runs as one batch. The result is still correct.

**c. Features created**

| Feature | Business meaning | Example (last run) |
| --- | --- | --- |
| `{event}_{src}_first_occurrence` | Number of days before the lookback end that the HCP's first patient record for this event appears in the data. A higher value means longer experience with the drug, condition or test | `kerendia_rx_first_occurrence`: 80,221 HCPs have a value, median 740 days (about 2 years), max 1,888 days (around Kerendia launch in mid-2021) |

* Empty (null) means the HCP never had this event in the data.
* The highest possible value depends on how far back the data goes: about 2,100 days for Rx and Px, 365 days for Dx (12-month input), and much longer for Lab.
* Outputs: `rx_first_occurrence_features` (243 features), `dx_` (345), `px_` (124), `lab_` (2).

---

### 1.3 Recency (time since the last event)

**a. Data sources**

Same input files and columns as 1.2, but only records inside the cohort's lookback (`LOOKBACK_START_DATE` to `LOOKBACK_END_DATE`).

**b. Preprocessing steps**

1. Apply the common steps in 1.1.
2. Keep only records inside the 12-month lookback.
3. For each `HCP_COHORT_ID` and event, take the **smallest** `EVENT_TIME`, i.e. the most recent record.
4. Pivot so that each event becomes one column.

**c. Features created**

| Feature | Business meaning | Example |
| --- | --- | --- |
| `{event}_{src}_time_min` | Days since the HCP's most recent patient record for this event. Range 0 to 365. A small value means the HCP is active with this drug, condition or test right now | `kerendia_rx_time_min = 12`: the last paid Kerendia fill from this HCP was 12 days before the lookback end |

* Empty means the event did not occur in the last 12 months.
* Outputs: `rx_recency_features`, `dx_`, `px_`, `lab_recency_features`. The same tables also hold the features in 1.4 and 1.5.

---

### 1.4 Event volume (total and unique events)

**a. Data sources**

Same 12-month data as 1.3.

**b. Preprocessing steps**

1. Same data as 1.3.
2. For each window (30, 60, 90, 180, 270 and 360 days before the lookback end), keep the records with `EVENT_TIME` at or below the window.
3. Count all records (total) and the number of different events (unique) per `HCP_COHORT_ID`, overall and by source.

**c. Features created** (built in the same recency function as 1.3)

| Feature | Business meaning |
| --- | --- |
| `total_events`, `unique_events` | Patient-days with any event in the last 12 months, and the number of different drugs, diagnoses, procedures or tests |
| `total_events_time_{w}_days`, `unique_events_time_{w}_days` | Same, in the last w days |
| `total_{src}`, `unique_{src}` | Same as the first row, for one source only (`rx`, `dx`, `px`, `lab_data`) |
| `total_events_time_{w}_days_{src}`, `unique_events_time_{w}_days_{src}` | Same as the second row, for one source only |

*Example:* `unique_events_time_90_days_rx = 18` means the HCP's patients filled 18 different product groups in the last 90 days, which points to a broad cardio-renal-metabolic practice.

*Detail to know:* each notebook only loads its own source. In `rx_recency_features`, the `_dx`, `_px` and `_lab_data` columns are therefore always empty, and `total_events` equals `total_rx`. The same applies to the other sources.

---

### 1.5 Skewness of event timing

**a. Data sources**

Same 12-month data as 1.3.

**b. Preprocessing steps**

1. Flag each record as inside or outside each window (30, 60, 90, 180, 270, 360 days).
2. For each source and window, compute the statistical skewness of `EVENT_TIME` over the HCP's records in that window.

**c. Features created**

| Feature | Business meaning |
| --- | --- |
| `skewness_time_{w}_days_days_{src}` (the word "days" appears twice in the name) | Shape of the HCP's activity over time within the window. Positive: most records are close to the lookback end, with a tail of older ones, so activity is concentrated recently. Negative: most records are older, so activity is slowing down. Near 0: activity is spread evenly |

* Empty when the HCP has too few records in the window, or all records are on the same day, so there is no spread to measure.
* Only the HCP's own source is filled in (same as 1.4).

---

### 1.6 Frequency (claim counts over the last 1 to 12 months)

**a. Data sources**

| Source | Input file | Events | History |
| --- | --- | --- | --- |
| Rx | `rx_input_claims_12M_features_input` | 29 product groups | Lookback only |
| Dx | `dx_input_claims_all_events_features_input` | 345 diagnoses | Lookback only |
| Px | `px_input_claims_all_events_features_input` | 124 procedures | Since 2021 |
| Lab | `lab_input_claims_12M_and_first_occ_features_input` | GFR, UACR | Since 2001 |

Columns used: `PROVIDER_ID`, `SVC_DT` and the event name. These notebooks (`01_rx_frequency_features` and the dx, px and lab equivalents) read the input files directly, without the common steps in 1.1. Each row is therefore one claim line, not a patient-day.

**b. Preprocessing steps**

1. **Month bucket.** `SVC_DT_M` = first day of the claim month.
2. **Monthly counts.** Count claim lines per HCP, month and event (one column per event).
3. **Full calendar.** *What:* give every HCP every month from the first to the last month in the file. *Why:* rolling windows can then count rows as months. *Detail to know:* months with no claims stay empty (not 0).
4. **Rolling sums.** Add up the last 1, 2, 3, 6 and 12 months, ending at each month.
5. **Pick the scoring month.** Keep only the month of the lookback end (September 2026 in the last run) for each cohort.
6. **Combine.** Start from the full HCP universe x cohort list, left-join the features, and add the source suffix (`_RX`, `_DX`, `_PX`, `_LAB_DATA`). The result is written to `{src}_accelerator_features`, together with the features in 1.7 and 1.8.

**c. Features created**

| Feature | Business meaning | Example |
| --- | --- | --- |
| `FREQ_{EVENT}_IN_LAST_{N}_MONTH_{SRC}`, N = 1, 2, 3, 6, 12 | Number of claims for this event from the HCP in the last N calendar months, ending with the lookback-end month | `FREQ_KERENDIA_IN_LAST_3_MONTH_RX = 12`: 12 paid Kerendia claims written by the HCP in July to September 2026 |

* Empty means the HCP had no claims for this event in the window.
* Windows are calendar months: "last 1 month" = 1 to 30 September 2026, not the last 30 days.
* Rx frequency only covers the 29 product groups in the 12-month file, not all 243.

---

### 1.7 Change in frequency

**a. Data sources**

The frequency features from 1.6 (same table and month).

**b. Preprocessing steps**

1. Take `FREQ_{EVENT}_IN_LAST_{N}_MONTH` and `FREQ_{EVENT}_IN_LAST_12_MONTH` from 1.6.
2. Compute the monthly claim rate in the last N months and in the earlier 12 - N months, and subtract.
3. Drop the single-month counts and keep the rolling and change columns.

**c. Features created**

| Feature | Formula | Business meaning |
| --- | --- | --- |
| `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_{EVENT}_IN_LAST_{N}_MONTH_{SRC}`, N = 1, 2, 3, 6 | FREQ_N / N - (FREQ_12 - FREQ_N) / (12 - N) | Above 0: the HCP writes or bills this event more per month recently than in the rest of the year (gaining momentum). Below 0: slowing down |

*Example:* 12 Kerendia claims in the last 3 months and 24 in 12 months gives 12/3 - 12/9 = 4.0 - 1.3 = +2.7 claims per month, so the HCP is accelerating.

* Empty when either input is empty.
* This is an absolute difference in claims per month, so large HCPs show larger swings than small ones.

---

### 1.8 Unique patients

**a. Data sources**

| Source | Input file | Events |
| --- | --- | --- |
| Rx | `rx_input_claims_total_events_and_first_occ_features_input` | 243 product groups |
| Dx | `dx_input_claims_all_events_features_input` | 345 diagnoses |
| Px | `px_input_claims_all_events_features_input` | 124 procedures |
| Lab | `lab_input_claims_12M_and_first_occ_features_input` | GFR, UACR |

Columns used: `PROVIDER_ID`, `PATIENT_ID`, `SVC_DT` and the event name.

**b. Preprocessing steps**

1. Keep records inside the cohort's 12-month lookback.
2. Compute days before the lookback end, and flag each record for the 30, 60, 90, 180 and 360-day windows.
3. Keep one row per HCP, cohort, event and patient.
4. Count distinct patients per HCP, cohort, event and window, then pivot to one column per event and window.

**c. Features created**

| Source | Feature | Business meaning |
| --- | --- | --- |
| Rx | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_{PRODUCT}_IN_LAST_{w}_DAYS_RX` | Different patients the HCP wrote this drug for in the last w days |
| Dx | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_{DIAGNOSIS}_IN_LAST_{w}_DAYS_DX` | Different patients with this diagnosis on the HCP's claims |
| Px | `NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_{PROCEDURE}_IN_LAST_{w}_DAYS_PX` | Different patients with this procedure |
| Lab | `NUM_OF_PATIENTS_THE_HCP_DID_LAB_TEST_{GFR or UACR}_IN_LAST_{w}_DAYS_LAB_DATA` | Different patients the HCP ordered this test for |

*Example:* `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_360_DAYS_RX = 5` means 5 different patients filled Kerendia prescribed by this HCP in the last year. This measures how widely an HCP uses a drug, which a claim count cannot show (one patient with 12 refills is not the same as 12 patients).

* Empty means the HCP had no patient with this event in the 12 months. 0 means patients exist, but only outside the window.
* In the names, every non-alphanumeric character becomes `_`, so double underscores can appear (e.g. `ADJUNCTIVE__NON_IMPLANTED_...`).

---

### 1.9 Hospitalization

**a. Data sources** (Dx and Px only)

| Role | Dx file | Px file |
| --- | --- | --- |
| All claims (denominator) | `dx_input_claims_all_events_features_input` (lookback) | `px_input_claims_all_events_features_input` (since 2021) |
| Hospital claims (numerator) | `dx_hospitalization_claims_all_events_features_input` | `px_hospitalization_claims_all_events_features_input` |

A hospital claim is a LAAD claim with `DATA_SOURCE = 'HX'` (hospital-sourced). Columns used: `PROVIDER_ID`, `PATIENT_ID`, `SVC_DT`.

**b. Preprocessing steps** (`02_dx_hospitalization_features`, `03_px_hospitalization_features`)

1. **One bucket for everything.** *What:* every diagnosis is relabelled `ALL_DIAGNOSIS` (Px: `ALL_PROCEDURES`). *Why:* the question is how hospital-heavy the HCP is overall, not per condition.
2. **Monthly counts** of all claims and of hospital claims per HCP. Months with claims but no hospital claims get 0.
3. **Full calendar and rolling sums** over the last 1, 6 and 12 months, as in 1.6.
4. **Consistency check.** *What:* HCP-months where hospital claims are higher than all claims in any window are removed. *Detail to know:* these HCPs end up empty, not 0.
5. **Share.** Hospital claims / all claims. Empty if all claims = 0. The all-claims columns are then dropped.
6. **Pick the scoring month** (lookback-end month), as in 1.6.
7. **Hospitalized patients.** Count distinct patients with a hospital claim in the last 30, 180 and 360 days.
8. **Combine** with the HCP universe x cohort list and add the suffix `_DX` or `_PX`.

**c. Features created** (9 per source)

| Feature (Dx shown; Px uses `ALL_PROCEDURES`, `DID_PROCEDURE` and `_PX`) | Business meaning |
| --- | --- |
| `TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_{1,6,12}_MONTH_DX` | Hospital claims linked to the HCP in the last 1, 6 or 12 months |
| `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_DIAGNOSIS_IN_LAST_{1,6,12}_MONTH_DX` | Share of the HCP's claims that are hospital-based (0 to 1) |
| `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DIAGNOSED_IN_LAST_{30,180,360}_DAYS_DX` | Different patients with a hospital claim from this HCP |

*Example:* `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_DIAGNOSIS_IN_LAST_12_MONTH_DX = 0.40` means 40% of the HCP's diagnosis claims in the year came from hospital settings. This often points to hospitalists or to HCPs managing acute heart failure or advanced CKD.

---

### 1.10 What the final tables look like

All tables are in `ops_pipeline/notebook_output/`, one row per `HCP_COHORT_ID`. Column counts include the keys.

| Output | Rows | Columns | Contains |
| --- | --- | --- | --- |
| `rx_first_occurrence_features` | 234,391 | 244 | 1.2 |
| `rx_recency_features` | 232,152 | 338 | 1.3 (243) + 1.4 and 1.5 (94) |
| `rx_accelerator_features` | 234,405 | 1,479 | 1.6, 1.7 (29 products), 1.8 (243 products) |
| `dx_first_occurrence_features` | 1,572,181 | 346 | 1.2 |
| `dx_recency_features` | 1,572,181 | 440 | 1.3 to 1.5 |
| `dx_accelerator_features` | 234,405 | 4,833 | 1.6 to 1.8 |
| `px_first_occurrence_features` | 232,025 | 125 | 1.2 |
| `px_recency_features` | 225,488 | 219 | 1.3 to 1.5 |
| `px_accelerator_features` | 234,405 | 1,739 | 1.6 to 1.8 |
| `lab_first_occurrence_features` | 170,304 | 3 | 1.2 |
| `lab_recency_features` | 150,719 | 97 | 1.3 to 1.5 |
| `lab_data_accelerator_features` | 234,405 | 31 | 1.6 to 1.8 |
| `dx_combined_hospitalization` | 234,405 | 12 | 1.9 |
| `px_combined_hospitalization_features` | 234,405 | 12 | 1.9 |

The first-occurrence and recency tables only have rows for HCPs with at least one record. The accelerator and hospitalization tables start from the full HCP universe, so HCPs without data have a row with empty values.

### 1.11 Things to watch out for

1. **Run order and anchor dates.** The frequency, unique-patient and hospitalization notebooks read cohort dates from `query_output/hcp_model_inference_anchor_dates.csv`, which the first-occurrence and recency loader writes. If that file is stale, the wrong month is picked.
2. **Dx first occurrence only covers 12 months.** Its input is lookback-only, so it means "first time in the last year", not "first time ever". Rx and Px are capped at 2021-01-02, so long-time prescribers all show about the same value (left-censored).
3. **Dx first-occurrence and recency outputs are not limited to the HCP universe** (1.57M rows). They are limited later, when the tables are combined.
4. **Different counting units.** 1.4 counts patient-days, 1.6, 1.7 and 1.9 count claim lines, and 1.8 and 1.9 patient features count distinct patients.
5. **Always-empty columns.** In each recency table, the 1.4 and 1.5 columns for the other three sources are always empty.
6. **Lab specialty filter.** Only primary care, internal medicine, NP and PA orderers are kept, so nephrologists, endocrinologists and cardiologists have no lab features (the lab specialty fix is in the Recommendations file).
7. **Px hospital file has no date filter.** This is safe: only the lookback-end month is used for claim counts, and patient counts are limited to the lookback.
8. **Month windows vs day windows.** Frequency and hospitalization windows are calendar months. Recency, volume, skewness and unique-patient windows are rolling days before the lookback end.

### 1.12 Data used and terms

**Data used**

| Source | Path (under `.../hcp_level_model/ops_pipeline/`) | Notes |
| --- | --- | --- |
| NBA 3.0 selected model features | `notebook_output/kerendia_nba_3_hcp_selected_features_data` | 755 cols (752 features), 240,806 HCPs, cohort I01 |
| SHAP values | `notebook_output/shap_values_insights.csv` | 11,525 samples x 752 features |
| Final 752 feature list | `/Users/sehar.aejaz.ext@bayer.com/Extra Notebooks/Final NBA 3.0 Modeling Features.xlsx` | Feature, mean absolute SHAP, share, category, sub-category. Used for 1.13 and 1.15 |
| NBA 3.0 patient intermediates | `notebook_output/{rx,dx,px,lab}_first_occurrence_features`, `*_recency_features`, `*_lag_frequency_features`, `*_accelerator_features` | Latest ops run |

**Terms used in this document**

| Term | Meaning |
| --- | --- |
| HCP x cohort (`HCP_COHORT_ID`) | One row per prescriber per cohort anchor date. Every patient feature is an aggregate over that HCP's patients in the cohort's lookback |
| Lookback | 365 days ending at `LOOKBACK_END_DATE`. The 30-day prediction window starts after it |
| Panel | Distinct patients with any paid Rx, Dx, lab or albuminuria-test claim from the HCP in the lookback. This is the denominator of every `PCT_OF_PATIENTS_*` feature |
| DKD / diabetic CKD | Type 2 diabetes plus CKD (or a T2D kidney-complication code), excluding ESRD. Exact codes in 3.0 |
| UACR | Urine albumin-to-creatinine ratio, mg/g. >= 30 = moderately increased albuminuria (Kerendia label). >= 300 = severely increased |
| eGFR | Estimated glomerular filtration rate, mL/min/1.73m2. Starting Kerendia requires eGFR >= 25 |
| NBRx / TRx | New-to-brand prescriptions / total prescriptions (new + refills) |
| PDC | Proportion of days covered by fills. This is the standard adherence measure |
| Left-censored | A first-occurrence value stuck at the data start, because the HCP was already prescribing before the data begins |
| SHAP share | A feature's mean absolute SHAP value divided by the sum over all 752 features |

### 1.13 Importance in the NBA 3.0 model (share of total mean absolute SHAP)

The model base table has about 1,264 columns, and feature selection keeps 752. 125 of the 752 come from the patient pipeline in this file and hold 13.7% of total SHAP. The rest come from other NBA 3.0 notebooks (claim-based Rx/Dx features, promotions, access, HCP demographics, geography). Source: `Final NBA 3.0 Modeling Features.xlsx`. The full list is in 1.15.

| Family | Features kept | SHAP share |
| --- | --- | --- |
| Claim-based features (Rx and Dx claim counts, prior writing, plan type, CKD stage, patient starts) | 495 | 60.6% |
| HCP promotions (F2F, DTC, digital, samples/FTP, speaker programs) | 53 | 11.4% |
| DRG access | 44 | 4.8% |
| HCP demographics | 10 | 4.3% |
| Unique patients (1.8) | 22 | 3.4% |
| Geographic (SDoH) | 22 | 3.2% |
| Recency (1.3) | 9 | 2.7% |
| Frequency (1.6) | 35 | 2.7% |
| Time-based | 3 | 2.1% |
| Change in frequency (1.7) | 33 | 1.5% |
| First occurrence (1.2) | 8 | 1.5% |
| Hospitalization (1.9) | 12 | 1.4% |
| Skewness (1.5) | 3 | 0.4% |
| Event volume (1.4) | 3 | 0.2% |

The single most important patient feature is `KERENDIA_RX_TIME_MIN` (days since the HCP's last Kerendia claim), rank 3 of 752 with 2.0% of SHAP.

### 1.14 Column volume by family, before selection

Column counts in the latest ops intermediate outputs (keys excluded). Use them to size the drop rules in the Recommendations file. The model base table used for selection is much smaller (about 1,264 columns), so the combine step already removes most of these. The counts still show where the volume comes from.

| Family | Rx | Dx | Px | Lab | Total |
| --- | --- | --- | --- | --- | --- |
| First occurrence (1 per event) | 243 | 345 | 124 | 2 | 714 |
| Recency `TIME_MIN` (1 per event) | 243 | 345 | 124 | 2 | 714 |
| Recency summary stats (total/unique x 7 windows x 5 suffixes) | 70 | 70 | 70 | 70 | 280 |
| Skewness (6 windows x 4 suffixes) | 24 | 24 | 24 | 24 | 96 |
| Frequency 1/2/3/6/12M (`accelerator_features`) | 145 | 1,725 | 620 | (separate notebook) | 2,490 |
| Change 1/2/3/6M | 116 | 1,380 | 496 | - | 1,992 |
| Unique patients 30/60/90/180/360 d | 1,215 | 1,725 | 620 | - | 3,560 |
| **Total** | **2,056** | **5,614** | **2,078** | **98** | **9,846** |

Only 29 Rx products get frequency and change features, while all 243 Rx events get unique-patient counts. Dx has the largest volume because each of the 345 Dx events gets every family. `*_lag_frequency_features` is an intermediate table at `PROVIDER_ID x SVC_DT_M` grain that feeds `*_accelerator_features`. It does not go to the model.

---

### 1.15 Patient features used in the final NBA 3.0 model

Source: `/Users/sehar.aejaz.ext@bayer.com/Extra Notebooks/Final NBA 3.0 Modeling Features.xlsx` (752 features with mean absolute SHAP, category and sub-category). Of the 752, **125 come from the patient pipeline described in this file**: the 117 in the Excel category "Features via Accelerator", plus the 8 `TOTAL_HOSPITALIZED_*` / `PERC_HOSPITALIZED_*` features that the Excel files under "Claim-based features / Hospitalized" but which are built by the hospitalization notebooks (1.9). The type below is taken from the feature name, because some Excel sub-categories mix types (for example `TOTAL_EVENTS_TIME_*` sits under "Rx Frequency" and skewness under "Others"). SHAP rank is 1-752 by mean absolute SHAP; SHAP share is the feature's share of the total.

| Feature type | Section | Features kept | Rx | Dx | Px | Lab | SHAP share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| First occurrence | 1.2 | 8 | 3 | 2 | 2 | 1 | 1.5% |
| Recency | 1.3 | 9 | 3 | 2 | 3 | 1 | 2.7% |
| Event volume | 1.4 | 3 | 2 | 0 | 1 | 0 | 0.2% |
| Skewness | 1.5 | 3 | 2 | 0 | 1 | 0 | 0.4% |
| Frequency | 1.6 | 35 | 19 | 9 | 7 | 0 | 2.7% |
| Change in frequency | 1.7 | 33 | 18 | 7 | 4 | 4 | 1.5% |
| Unique patients | 1.8 | 22 | 12 | 5 | 4 | 1 | 3.4% |
| Hospitalization | 1.9 | 12 | 0 | 5 | 7 | 0 | 1.4% |
| **Total patient-pipeline features** | | **125** | 59 | 30 | 29 | 7 | **13.7%** |

The other 627 features come from other NBA 3.0 notebooks and are listed here only as context:

| Excel category / sub-category | Features | SHAP share |
| --- | --- | --- |
| Claim-based: Prior Writing | 145 | 25.0% |
| Claim-based: Rx Claim-based | 190 | 21.4% |
| Claim-based: Dx CKD stage | 91 | 5.2% |
| Claim-based: Plan Type & combination with Claims | 48 | 5.2% |
| Claim-based: # Patient Starts | 14 | 2.3% |
| Claim-based: Competitor Brands NBRx share | 4 | 0.8% |
| Claim-based: Dx Claim-based | 3 | 0.5% |
| HCP Promotions (F2F 21, DTC 9, Digital 9, Sample/FTP 10, Speaker Program 4) | 53 | 11.4% |
| DRG Access | 44 | 4.8% |
| HCP Demo | 10 | 4.3% |
| Geographic Features (SDoH) | 22 | 3.2% |
| Time-based features | 3 | 2.1% |

**First occurrence (8)**

| SHAP rank | Feature | Source | SHAP share |
| --- | --- | --- | --- |
| 34 | `SYNJARDY_XR_RX_FIRST_OCCURRENCE` | Rx | 0.48% |
| 56 | `TELMISARTAN_HCTZ_RX_FIRST_OCCURRENCE` | Rx | 0.37% |
| 92 | `ECHO_TESTS_PX_FIRST_OCCURRENCE` | Px | 0.25% |
| 139 | `AMILORIDE_HCL_RX_FIRST_OCCURRENCE` | Rx | 0.18% |
| 142 | `GFR_LAB_DATA_FIRST_OCCURRENCE` | Lab | 0.18% |
| 584 | `ATHEROSCLEROSIS_OF_RENAL_ARTERY_DX_FIRST_OCCURRENCE` | Dx | 0.03% |
| 691 | `REVISION_OPEN_ARTERIOVENOUS_FISTULA_WITHOUT_THROMBECTOMY_AUTOGENOUS_OR_NONAUTOGENOUS_DIALYSIS_GR_PX_FIRST_OCCURRENCE` | Px | 0.01% |
| 706 | `SECONDARY_SIDEROBLASTIC_ANEMIA_DUE_TO_DISEASE_DX_FIRST_OCCURRENCE` | Dx | 0.01% |

**Recency (9)**

| SHAP rank | Feature | Source | SHAP share |
| --- | --- | --- | --- |
| 3 | `KERENDIA_RX_TIME_MIN` | Rx | 1.96% |
| 90 | `CREATININE_OTHER_SOURCE_PX_TIME_MIN` | Px | 0.25% |
| 168 | `VICTOZA_3_PAK_RX_TIME_MIN` | Rx | 0.15% |
| 186 | `PROTEINURIA_UNSPECIFIED_DX_TIME_MIN` | Dx | 0.14% |
| 331 | `UACR_LAB_DATA_TIME_MIN` | Lab | 0.08% |
| 366 | `HEMOGLOBIN_GLYCOSYLATED_A1C_PX_TIME_MIN` | Px | 0.07% |
| 521 | `ECHO_TESTS_PX_TIME_MIN` | Px | 0.04% |
| 648 | `DIABETES_MELLITUS_DUE_TO_UNDERLYING_CONDITION_WITH_DIABETIC_NEPHROPATHY_DX_TIME_MIN` | Dx | 0.02% |
| 685 | `EDARBYCLOR_RX_TIME_MIN` | Rx | 0.01% |

**Event volume (3)**

| SHAP rank | Feature | Source | SHAP share |
| --- | --- | --- | --- |
| 315 | `TOTAL_EVENTS_TIME_180_DAYS_PX` | Px | 0.08% |
| 386 | `TOTAL_EVENTS_TIME_360_DAYS_RX` | Rx | 0.06% |
| 658 | `TOTAL_EVENTS_TIME_180_DAYS_RX` | Rx | 0.02% |

**Skewness (3)**

| SHAP rank | Feature | Source | SHAP share |
| --- | --- | --- | --- |
| 151 | `SKEWNESS_TIME_180_DAYS_DAYS_RX` | Rx | 0.16% |
| 253 | `SKEWNESS_TIME_360_DAYS_DAYS_RX` | Rx | 0.10% |
| 289 | `SKEWNESS_TIME_180_DAYS_DAYS_PX` | Px | 0.09% |

**Frequency (35)**

| SHAP rank | Feature | Source | SHAP share |
| --- | --- | --- | --- |
| 20 | `FREQ_ALBUMIN__URINE_EG_MICROALBUMIN_QUANTITATIVE_IN_LAST_12_MONTH_PX` | Px | 0.68% |
| 85 | `FREQ_ENTRESTO_IN_LAST_12_MONTH_RX` | Rx | 0.26% |
| 136 | `FREQ_ACUTE_ON_CHRONIC_COMBINED_SYSTOLIC_CONGESTIVE_AND_DIASTOLIC_CONGESTIVE_HEART_FAILURE_IN_LAST_12_MONTH_DX` | Dx | 0.18% |
| 150 | `FREQ_ECHO_TESTS_IN_LAST_12_MONTH_PX` | Px | 0.16% |
| 162 | `FREQ_ACUTE_ON_CHRONIC_SYSTOLIC_CONGESTIVE_HEART_FAILURE_IN_LAST_12_MONTH_DX` | Dx | 0.16% |
| 172 | `FREQ_METOPROLOL_TART_IN_LAST_12_MONTH_RX` | Rx | 0.15% |
| 179 | `FREQ_UNSPECIFIED_SYSTOLIC_CONGESTIVE_HEART_FAILURE_IN_LAST_6_MONTH_DX` | Dx | 0.14% |
| 258 | `FREQ_ECHO_TESTS_IN_LAST_6_MONTH_PX` | Px | 0.10% |
| 274 | `FREQ_FARXIGA_IN_LAST_3_MONTH_RX` | Rx | 0.10% |
| 301 | `FREQ_HEART_FAILURE_UNSPECIFIED_IN_LAST_12_MONTH_DX` | Dx | 0.09% |
| 326 | `FREQ_FUROSEMIDE_IN_LAST_12_MONTH_RX` | Rx | 0.08% |
| 351 | `FREQ_CREATININE__OTHER_SOURCE_IN_LAST_12_MONTH_PX` | Px | 0.07% |
| 391 | `FREQ_SEVELAMER_CARB_IN_LAST_1_MONTH_RX` | Rx | 0.06% |
| 459 | `FREQ_LOSARTAN_POT_IN_LAST_12_MONTH_RX` | Rx | 0.05% |
| 476 | `FREQ_TELMISARTAN_IN_LAST_3_MONTH_RX` | Rx | 0.04% |
| 484 | `FREQ_KERENDIA_IN_LAST_12_MONTH_RX` | Rx | 0.04% |
| 495 | `FREQ_AMLODIP_BES_OROLMESAR_IN_LAST_3_MONTH_RX` | Rx | 0.04% |
| 535 | `FREQ_SYNJARDY_IN_LAST_12_MONTH_RX` | Rx | 0.04% |
| 550 | `FREQ_DILTIAZEM_HCL_IN_LAST_3_MONTH_RX` | Rx | 0.03% |
| 559 | `FREQ_CALCITRIOL_IN_LAST_12_MONTH_RX` | Rx | 0.03% |
| 575 | `FREQ_KERENDIA_IN_LAST_6_MONTH_RX` | Rx | 0.03% |
| 579 | `FREQ_ANEMIA_IN_CHRONIC_KIDNEY_DISEASE_IN_LAST_6_MONTH_DX` | Dx | 0.03% |
| 590 | `FREQ_EDARBI_IN_LAST_3_MONTH_RX` | Rx | 0.03% |
| 591 | `FREQ_ATHEROSCLEROSIS_OF_AORTA_IN_LAST_12_MONTH_DX` | Dx | 0.03% |
| 678 | `FREQ_GLUCOSE__QUANTITATIVE_BLOOD_EXCEPT_REAGENT_STRIP_IN_LAST_12_MONTH_PX` | Px | 0.01% |
| 682 | `FREQ_PROTEINURIA_UNSPECIFIED_IN_LAST_6_MONTH_DX` | Dx | 0.01% |
| 690 | `FREQ_KERENDIA_IN_LAST_2_MONTH_RX` | Rx | 0.01% |
| 705 | `FREQ_END_STAGE_RENAL_DISEASE_ESRD_RELATED_SERVICES_MONTHLY_FOR_PATIENTS_20_YEARS_OF_AGE_AND_OLDER__WIT_IN_LAST_12_MONTH_PX` | Px | 0.01% |
| 708 | `FREQ_ANEMIA_IN_CHRONIC_KIDNEY_DISEASE_IN_LAST_2_MONTH_DX` | Dx | 0.01% |
| 710 | `FREQ_DILTIAZEM_SR_IN_LAST_6_MONTH_RX` | Rx | 0.01% |
| 731 | `FREQ_CHRONIC_KIDNEY_DISEASE_STAGE_1_IN_LAST_12_MONTH_DX` | Dx | 0.00% |
| 732 | `FREQ_AMLODIP_BES_ORVALSAR_IN_LAST_2_MONTH_RX` | Rx | 0.00% |
| 733 | `FREQ_KERENDIA_IN_LAST_3_MONTH_RX` | Rx | 0.00% |
| 740 | `FREQ_KERENDIA_IN_LAST_1_MONTH_RX` | Rx | 0.00% |
| 741 | `FREQ_UNLISTED_DIALYSIS_PROCEDURE_INPATIENT_OR_OUTPATIENT_IN_LAST_3_MONTH_PX` | Px | 0.00% |

**Change in frequency (33)**

| SHAP rank | Feature | Source | SHAP share |
| --- | --- | --- | --- |
| 109 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_METOPROLOL_TART_IN_LAST_2_MONTH_RX` | Rx | 0.21% |
| 126 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_ECHO_TESTS_IN_LAST_3_MONTH_PX` | Px | 0.19% |
| 174 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_ECHO_TESTS_IN_LAST_2_MONTH_PX` | Px | 0.15% |
| 177 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_PROPRANOLOL_HCL_IN_LAST_2_MONTH_RX` | Rx | 0.14% |
| 192 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_FUROSEMIDE_IN_LAST_3_MONTH_RX` | Rx | 0.13% |
| 262 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_ECHO_TESTS_IN_LAST_6_MONTH_PX` | Px | 0.10% |
| 342 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_GLIPIZIDE_IN_LAST_2_MONTH_RX` | Rx | 0.07% |
| 396 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_ECHO_TESTS_IN_LAST_1_MONTH_PX` | Px | 0.06% |
| 412 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_CHRONIC_KIDNEY_DISEASE_STAGE_3_UNSPECIFIED_IN_LAST_6_MONTH_DX` | Dx | 0.05% |
| 510 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_NIFEDIPINE_ER_IN_LAST_6_MONTH_RX` | Rx | 0.04% |
| 530 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_MIXED_HYPERLIPIDEMIA_IN_LAST_6_MONTH_DX` | Dx | 0.04% |
| 544 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_LABETALOL_HCL_IN_LAST_3_MONTH_RX` | Rx | 0.03% |
| 577 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_END_STAGE_RENAL_DISEASE_IN_LAST_3_MONTH_DX` | Dx | 0.03% |
| 582 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_GLIPIZIDE_IN_LAST_1_MONTH_RX` | Rx | 0.03% |
| 587 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_CALCIUM_ACE_IN_LAST_2_MONTH_RX` | Rx | 0.03% |
| 598 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_GFR_IN_LAST_1_MONTH_LAB_DATA` | Lab | 0.03% |
| 602 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_GFR_IN_LAST_6_MONTH_LAB_DATA` | Lab | 0.03% |
| 617 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_NIFEDIPINE_ER_IN_LAST_2_MONTH_RX` | Rx | 0.02% |
| 626 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_NADOLOL_IN_LAST_1_MONTH_RX` | Rx | 0.02% |
| 643 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_IRBESARTAN_IN_LAST_1_MONTH_RX` | Rx | 0.02% |
| 653 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_TYPE_2_DIABETES_MELLITUS_WITH_DIABETIC_CHRONIC_KIDNEY_DISEASE_IN_LAST_1_MONTH_DX` | Dx | 0.02% |
| 673 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_DILT_XR_IN_LAST_2_MONTH_RX` | Rx | 0.01% |
| 674 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_UACR_IN_LAST_6_MONTH_LAB_DATA` | Lab | 0.01% |
| 677 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_TELMISARTAN_IN_LAST_1_MONTH_RX` | Rx | 0.01% |
| 679 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_PROTEINURIA_UNSPECIFIED_IN_LAST_6_MONTH_DX` | Dx | 0.01% |
| 692 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_EDARBI_IN_LAST_6_MONTH_RX` | Rx | 0.01% |
| 695 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_PROTEINURIA_UNSPECIFIED_IN_LAST_3_MONTH_DX` | Dx | 0.01% |
| 701 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_UACR_IN_LAST_3_MONTH_LAB_DATA` | Lab | 0.01% |
| 707 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_PROTEINURIA_UNSPECIFIED_IN_LAST_1_MONTH_DX` | Dx | 0.01% |
| 720 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_CALCITRIOL_IN_LAST_1_MONTH_RX` | Rx | 0.01% |
| 722 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_METOLAZONE_IN_LAST_2_MONTH_RX` | Rx | 0.01% |
| 723 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_KERENDIA_IN_LAST_2_MONTH_RX` | Rx | 0.00% |
| 748 | `CHANGE_IN_FREQ_OF_HCP_CLAIMS_FOR_EDARBYCLOR_IN_LAST_1_MONTH_RX` | Rx | 0.00% |

**Unique patients (22)**

| SHAP rank | Feature | Source | SHAP share |
| --- | --- | --- | --- |
| 22 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_LISINOPRIL_HCTZ_IN_LAST_360_DAYS_RX` | Rx | 0.66% |
| 36 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_HYDROCHLOROTHIAZIDE_IN_LAST_360_DAYS_RX` | Rx | 0.47% |
| 47 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_RYBELSUS_IN_LAST_30_DAYS_RX` | Rx | 0.41% |
| 52 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_90_DAYS_RX` | Rx | 0.39% |
| 54 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_ENTRESTO_IN_LAST_360_DAYS_RX` | Rx | 0.37% |
| 67 | `NUM_OF_PATIENTS_THE_HCP_DID_LAB_TEST_GFR_IN_LAST_360_DAYS_LAB_DATA` | Lab | 0.31% |
| 121 | `NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_HEMOGLOBIN__GLYCOSYLATED__A1C__IN_LAST_90_DAYS_PX` | Px | 0.19% |
| 143 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_180_DAYS_RX` | Rx | 0.17% |
| 215 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_360_DAYS_RX` | Rx | 0.12% |
| 355 | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_HYPERTENSIVE_HEART_AND_CHRONIC_KIDNEY_DISEASE_WITH_HEART_FAILURE_AND_STAGE_1_THROUGH_STAGE_4_CHRONIC_IN_LAST_360_DAYS_DX` | Dx | 0.07% |
| 452 | `NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_ECHO_TESTS_IN_LAST_180_DAYS_PX` | Px | 0.05% |
| 455 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_DILTIAZEM_HCL_IN_LAST_90_DAYS_RX` | Rx | 0.05% |
| 497 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_60_DAYS_RX` | Rx | 0.04% |
| 520 | `NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_CREATININE__OTHER_SOURCE_IN_LAST_180_DAYS_PX` | Px | 0.04% |
| 543 | `NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_ECHO_TESTS_IN_LAST_360_DAYS_PX` | Px | 0.03% |
| 668 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_BENAZEPRIL_HCL_IN_LAST_30_DAYS_RX` | Rx | 0.02% |
| 680 | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_PROTEINURIA__UNSPECIFIED_IN_LAST_360_DAYS_DX` | Dx | 0.01% |
| 693 | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_PROTEINURIA__UNSPECIFIED_IN_LAST_180_DAYS_DX` | Dx | 0.01% |
| 711 | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_ATHEROSCLEROSIS_OF_RENAL_ARTERY_IN_LAST_90_DAYS_DX` | Dx | 0.01% |
| 721 | `NUM_OF_PATIENTS_THE_HCP_DIAGNOSED_WITH_HYPERTENSIVE_CHRONIC_KIDNEY_DISEASE_WITH_STAGE_5_CHRONIC_KIDNEY_DISEASE_OR_END_STAGE_RENAL_DISEASE_IN_LAST_180_DAYS_DX` | Dx | 0.01% |
| 725 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_KERENDIA_IN_LAST_30_DAYS_RX` | Rx | 0.00% |
| 752 | `NUM_OF_PATIENTS_THE_HCP_PRESCRIBED_WITH_EDARBYCLOR_IN_LAST_60_DAYS_RX` | Rx | 0.00% |

**Hospitalization (12)**

| SHAP rank | Feature | Source | SHAP share |
| --- | --- | --- | --- |
| 37 | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DID_PROCEDURE_IN_LAST_360_DAYS_PX` | Px | 0.47% |
| 107 | `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_PROCEDURES_IN_LAST_12_MONTH_PX` | Px | 0.21% |
| 160 | `TOTAL_HOSPITALIZED_CLAIMS_ALL_PROCEDURES_IN_LAST_12_MONTH_PX` | Px | 0.16% |
| 169 | `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_PROCEDURES_IN_LAST_6_MONTH_PX` | Px | 0.15% |
| 276 | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DID_PROCEDURE_IN_LAST_180_DAYS_PX` | Px | 0.10% |
| 325 | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DIAGNOSED_IN_LAST_360_DAYS_DX` | Dx | 0.08% |
| 433 | `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_DIAGNOSIS_IN_LAST_6_MONTH_DX` | Dx | 0.05% |
| 482 | `TOTAL_HOSPITALIZED_CLAIMS_ALL_PROCEDURES_IN_LAST_6_MONTH_PX` | Px | 0.04% |
| 505 | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DIAGNOSED_IN_LAST_180_DAYS_DX` | Dx | 0.04% |
| 580 | `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_ALL_DIAGNOSIS_IN_LAST_1_MONTH_DX` | Dx | 0.03% |
| 631 | `TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_1_MONTH_DX` | Dx | 0.02% |
| 703 | `TOTAL_HOSPITALIZED_CLAIMS_ALL_PROCEDURES_IN_LAST_1_MONTH_PX` | Px | 0.01% |
