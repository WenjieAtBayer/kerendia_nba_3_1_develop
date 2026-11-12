# NBA 3.0 Adoption Features (Invokana, Farxiga): How They Are Built

Notebook reviewed: `/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/11_adoption_features_inv_far`. NBA 3.1 changes are not part of this file.

## 1. How NBA 3.0 builds the adoption features

### 1.0 What is this section about?

The NBA (Next Best Action) model scores every HCP who could prescribe Kerendia and recommends the next promotional action. **Adoption features** describe how quickly an HCP has taken up earlier CKD launches. Invokana (canagliflozin) got its CKD indication in October 2019 and Farxiga (dapagliflozin) in April 2021. The idea is that an HCP who started CKD patients on these drugs quickly is also likely to adopt Kerendia quickly.

This section explains how the **NBA 3.0 Ops pipeline** builds these features, so a reader can follow the logic without reading the code. Section 1.1 covers the shared foundations. Section 1.2 covers the single feature type in three parts: (a) data sources and what each column means, (b) preprocessing steps, (c) features created. 1.3 and 1.4 cover the output table and caveats. 1.5 to 1.7 cover the data used, the model importance and the column volume. 1.8 lists the adoption feature in the final 752-feature NBA 3.0 model. Numbers come from the latest ops run (pull date 2026-10-26).

**In short**: for every HCP, the notebook looks at patients the HCP both diagnosed with CKD and prescribed Invokana (or Farxiga), measures the days from the patient's first CKD diagnosis to the patient's first Rx of the drug from that HCP, and keeps the **shortest** such gap across the HCP's patients.

| Feature type | Business question | Section |
| --- | --- | --- |
| Time to adopt | How fast does the HCP put a CKD patient on Invokana / Farxiga after the CKD diagnosis? | 1.2 |

### 1.1 Shared foundations

**Who is scored and on which date**

| Item | What it means | Last run |
| --- | --- | --- |
| HCP universe | `ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`. Both input files are inner-joined to it when they are written | 234,405 HCPs |
| Grain | **One row per HCP, no month and no cohort.** `99_Combine_Physician_Data` joins on `PROVIDER_ID` only, so every cohort gets the same value | 234,338 rows |
| Dates | No lookback filter. The feature uses all history in the input files | 2021-01-02 to 2026-10-02 |

**Source tables** (IQVIA LAAD in Snowflake, pulled by `03_HCP_Level_Features/00_Write_Input_Files`)

| Source | Fact table | Lookup tables | One row is |
| --- | --- | --- | --- |
| Rx (`Rx_01_new`) | `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX` | `STG_CAR_IQV_LAAD_DIM_PRD` (NDC to product), `STG_CAR_IQV_LAAD_DIM_PRVDR`, `STG_CAR_IQV_LAAD_DIM_PLN`, `STG_CAR_IQV_LAAD_DIM_PTNT_DMGRPHC`, product mapping `PHCDW.PHCDW_DSAA.CKD_PRODUCT_MAPPING_VW` | One prescriber x patient x day x product x strength (grouped) |
| Dx (`Dx_03`) | `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX` | `STG_IQVIA_LAAD_DIM_DIAGNOSIS` (hard-coded CKD code list), `STG_CAR_IQV_LAAD_DIM_PRVDR` | One distinct patient x service date x CKD description x provider |

**Columns used**

| Column | What it means | Example |
| --- | --- | --- |
| `PROVIDER_ID` | LAAD ID of the HCP. Rx: the prescriber. Dx: the referring doctor, or the rendering doctor if there is no referring doctor | 8910607 |
| `PATIENT_ID` | De-identified LAAD patient ID. Same ID in Rx and Dx | 123456789 |
| `SVC_DT` | Rx: fill date. Dx: service date | 2022-05-10 |
| `PRODUCT_NAME` (Rx) | LAAD product name. Filtered with `LIKE '%INVOKANA%'` and `LIKE '%FARXIGA%'`. Values found: `INVOKANA` (100 MG and 300 MG) and `FARXIGA` | FARXIGA |
| `CATEGORY` (Dx) | CKD diagnosis description (41 values). Not used by the feature: any row counts as a CKD diagnosis | CHRONIC KIDNEY DISEASE, STAGE 4 (SEVERE) |

**Input files** (`ops_pipeline/query_output/`)

| File | What is kept | Period | Last run |
| --- | --- | --- | --- |
| `Rx_01_new` | Products in `CKD_PRODUCT_MAPPING_VW` (CKD / cardio-renal-metabolic basket), treatment category not "other", provider not null. **All claim types, including rejected claims** (`REJECTION_FLAG = 1` for 8.6% of rows) | `analysis_start_month` (201901) onwards. LAAD data starts 2021-01-02 | 4.11B rows, 234,338 HCPs, to 2026-10-02 |
| `Dx_03` | Hard-coded list of 163 ICD-9 / ICD-10 CKD-related codes (diabetic CKD, hypertensive CKD, N18.x stages, D63.1 anemia in CKD, dialysis and transplant status). Provider not null | `complete_history_start_month` (201901) to `complete_history_end_month` (lookback-end month) | 417.5M rows, 228,182 HCPs, 15.96M patients, to 2026-09-30 |

Invokana and Farxiga rows in `Rx_01_new`:

| Product | Rows | Rejected rows | HCPs |
| --- | --- | --- | --- |
| FARXIGA | 51.7M | 5.5M (10.7%) | 223,131 |
| INVOKANA 300 MG | 2.4M | 0.35M | 86,155 |
| INVOKANA 100 MG | 1.7M | 0.30M | 94,872 |

---

### 1.2 Time to adopt

**a. Data sources**

`Rx_01_new` (`PROVIDER_ID`, `PATIENT_ID`, `SVC_DT`, `PRODUCT_NAME`) and `Dx_03` (`PROVIDER_ID`, `PATIENT_ID`, `SVC_DT`).

**b. Preprocessing steps**

1. **Indication start dates.** *What:* keep Dx and Rx records on or after 2019-10-01 for Invokana and on or after 2021-04-01 for Farxiga (the CKD approval dates). *Detail to know:* LAAD data starts 2021-01-02, so the Invokana filter has no effect.
2. **First CKD date per patient.** *What:* for each HCP and patient, the earliest CKD diagnosis date (`MIN_CKD_DATE_INV`, `MIN_CKD_DATE_FAR`) where this HCP is the Dx provider.
3. **First Rx date per patient.** *What:* for each HCP and patient, the earliest Invokana (or Farxiga) Rx date written by this HCP. The product names are pivoted into columns `INVOKANA` and `FARXIGA`.
4. **Match.** *What:* start from all HCPs in `Rx_01_new`, left-join the CKD patients, then left-join the Rx dates on HCP and patient. Keep only patients with both dates. *Detail to know:* the same HCP must be both the diagnosing and the prescribing doctor for that patient.
5. **Gap.** *What:* `TIME_TO_ADOPT_* = DATEDIFF(first Rx date, first CKD date)` in days. Negative gaps (Rx before the first CKD code) are dropped.
6. **HCP value.** *What:* take the **minimum** gap across the HCP's patients.
7. **Combine.** Left-join both features to all HCPs in `Rx_01_new`. Missing stays empty (the fill with 0 is commented out).

**c. Features created**

| Feature | Business meaning | Example (last run) |
| --- | --- | --- |
| `TIME_TO_ADOPT_INVOKANA` | Shortest number of days, across the HCP's patients, between a patient's first CKD diagnosis and that patient's first Invokana Rx from the same HCP. Lower = faster uptake | 17,529 HCPs have a value. Quartiles 7 / 92 / 323 days, 90th percentile 683, max 2,086. 2,489 HCPs have 0 |
| `TIME_TO_ADOPT_FARXIGA` | Same for Farxiga, from April 2021 | 116,911 HCPs have a value. Quartiles 1 / 37 / 226 days, 90th percentile 578, max 2,005. 28,926 HCPs have 0 |

*Example:* HCP 8910607 has `TIME_TO_ADOPT_FARXIGA = 2`: one of their CKD patients filled a Farxiga Rx from them 2 days after the patient's first CKD code from the same HCP. Recomputed independently from the input files for this and two other HCPs (values 2, 828 and 13 days), with identical results.

* Empty means the HCP never diagnosed CKD and prescribed the drug to the same patient (or only did so in the wrong order). 114,948 HCPs are empty for both features.
* 0 means the Rx and the first CKD code are on the same day.

---

### 1.3 What the final table looks like

| Output | Rows | Columns | Contains |
| --- | --- | --- | --- |
| `ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_adoption_features_inv_far_for_inference` | 234,338 (one per HCP) | 4 (2 features + `PROVIDER_ID`, `PULL_DT`) | 1.2 |

All rows are in the HCP universe. 67 universe HCPs have no row.

### 1.4 Things to watch out for

1. **It is a minimum, not a typical adoption time.** One fast patient is enough for a low value, so HCPs with many CKD patients are more likely to get low values. The feature mixes "speed" with "volume".
2. **It does not measure time since launch.** The question in the notebook header is "time taken by a physician to adopt Invokana / Farxiga", but the clock starts at each patient's first CKD code in the data, not at the indication date. Because the data starts 2021-01-02, "first CKD code" is really "first CKD code since 2021" (left-censored).
3. **Static over time (possible leakage in training).** There is no cohort or lookback filter. The feature uses all data up to the latest pull (Rx to 2026-10-02, two days after the lookback end), and the combine joins on `PROVIDER_ID` only, so every training cohort gets today's value, including adoption that happened after that cohort's prediction window.
4. **Rejected and reversed claims are included.** `Rx_01_new` keeps all claim types, so a rejected Farxiga claim counts as adoption.
5. **Generic dapagliflozin is not captured.** The filter is `PRODUCT_NAME LIKE '%FARXIGA%'`, and no DAPAGLIFLOZIN product appears in `Rx_01_new`. As generics grow, recent Farxiga-molecule uptake is missed.
6. **Same doctor for Dx and Rx.** Patients diagnosed by one HCP and treated by another are dropped. This penalizes HCPs who receive referred patients with an existing CKD code (for example, nephrologists).
7. **Dx code list is hard-coded and partly stale.** It contains N18.3 but not N18.30 / N18.31 / N18.32 (stage 3a / 3b, billed since October 2020), nor N18.5 / N18.6 (stage 5 / ESRD), and some entries that are not ICD diagnosis codes (for example ICD-10-PCS-like values such as `0TY0.0Z0`, `5A1.D00Z`). Stage 3 rows are only 63,004 of 417.5M, against 23.5M for stage 4.
8. **Empty, not 0.** Missing values stay empty. A 0 means "same day", which is the fastest possible value.

### 1.5 Data used and terms

**Data used**

| Source | Path (under `.../hcp_level_model/ops_pipeline/`) | Notes |
| --- | --- | --- |
| Rx input | `query_output/Rx_01_new` | Was renamed from `Rx_01` after a backup issue |
| Dx input | `query_output/Dx_03` | Pulled 2026-10-26 |
| Output | `notebook_output/kerendia_nba_3_hcp_model_adoption_features_inv_far_for_inference` | `PULL_DT = 2026_10_26` |
| HCP universe | `notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` | 234,405 HCPs |
| Final 752 feature list | `/Users/sehar.aejaz.ext@bayer.com/Extra Notebooks/Final NBA 3.0 Modeling Features.xlsx` | Used for 1.6 and 1.8 |

**Terms used in this document**

| Term | Meaning |
| --- | --- |
| Adoption | Starting a CKD patient on a newly indicated drug |
| First CKD date | The earliest CKD code for a patient on a claim where the HCP is the Dx provider, on or after the indication date filter |
| Left-censored | A first date stuck at the data start, because the event happened before the data begins |
| SHAP share | A feature's mean absolute SHAP value divided by the sum over all 752 features |

### 1.6 Importance in the NBA 3.0 model (share of total mean absolute SHAP)

1 of the 2 features is among the final 752: `TIME_TO_ADOPT_FARXIGA`, rank 13 with **1.10%** of total SHAP. This is one of the strongest single HCP-level claim features in the model. `TIME_TO_ADOPT_INVOKANA` was dropped (only 17,529 HCPs have a value). The Excel files the feature under "Claim-based features / Rx Claim-based".

| Family | Features created | Features kept | SHAP share |
| --- | --- | --- | --- |
| Time to adopt (1.2) | 2 | 1 | 1.10% |

### 1.7 Column volume

| Family | Invokana | Farxiga | Total |
| --- | --- | --- | --- |
| Time to adopt | 1 | 1 | 2 |

---

### 1.8 Adoption features used in the final NBA 3.0 model

Source: `Final NBA 3.0 Modeling Features.xlsx`. SHAP rank is 1-752 by mean absolute SHAP.

| SHAP rank | Feature | Type | SHAP share |
| --- | --- | --- | --- |
| 13 | `TIME_TO_ADOPT_FARXIGA` | Time to adopt (1.2) | 1.10% |
