# NBA 3.0 Claim Comorbidity Features: How They Are Built

Notebook reviewed: `/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/09_claim_comorbidity`. NBA 3.1 changes are not part of this file.

## 1. How NBA 3.0 builds the claim comorbidity features

### 1.0 What is this section about?

The NBA (Next Best Action) model scores every HCP who could prescribe Kerendia and recommends the next promotional action. Besides promotional and Rx-volume features, the model uses **claim comorbidity features**: monthly counts of how many different patients an HCP sees with a kidney-disease diagnosis, split into three comorbidity groups (kidney disease only, diabetes plus kidney disease, cardiovascular plus kidney disease), and the share of the HCP's kidney patients that falls into each group.

This section explains how the **NBA 3.0 Ops pipeline** builds these features, so a reader can follow the logic without reading the code. Section 1.1 covers the shared foundations. Sections 1.2 to 1.5 cover one feature type each, in three parts: (a) data sources and what each column means, (b) preprocessing steps, (c) features created. 1.6 and 1.7 cover the output table and caveats. 1.8 to 1.10 cover the data used for this review, the model importance and the column volume. 1.11 lists every comorbidity feature that made it into the final 752-feature NBA 3.0 model. Numbers come from the latest ops run (pull date 2026-10-26, lookback 2025-09-30 to 2026-09-30, cohort `I01`, scoring month `SVC_DT_M = 2026-09-01`).

**In short**: for every HCP and calendar month, the notebook counts the distinct patients for whom the HCP was the referring (or rendering) doctor on a kidney-related diagnosis claim. It does this overall and for each of the three diagnosis groups, then averages these monthly counts over the last 1, 3, 6 and 12 months, keeps a running total since 2021, and divides each group by the overall count.

| Feature type | Business question | Section |
| --- | --- | --- |
| Monthly patient count | How many different kidney-disease patients did the HCP see this month, by comorbidity group? | 1.2 |
| Rolling average | What is the HCP's typical monthly kidney-patient volume over recent months? | 1.3 |
| Running total | How much kidney-disease experience has the HCP built up since 2021? | 1.4 |
| Group share (PCT) | What share of the HCP's kidney patients also have diabetes or cardiovascular disease? | 1.5 |

### 1.1 Shared foundations (apply to every feature type)

**Who is scored and on which date**

| Item | What it means | Last run |
| --- | --- | --- |
| HCP universe | `ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`: the LAAD `PROVIDER_ID`s the model scores. The input file `Dx_09` is inner-joined to it when it is written | 234,405 HCPs |
| Cohort | One scoring date per run, labelled `I01` | `I01` |
| Join key | `PROVIDER_ID` + `SVC_DT_M`. `99_Combine_Physician_Data` joins this table to the universe on `SVC_DT_M = trunc(LOOKBACK_END_DATE, 'MM')` | `SVC_DT_M = 2026-09-01` |

**Cohort dates** (from `00_config` and `query_output/hcp_model_inference_anchor_dates.csv`)

| Date | Rule | Last run |
| --- | --- | --- |
| Anchor date | First day of the prediction month | 2026-11-01 |
| Lookback start | Lookback end - 365 days | 2025-09-30 |
| Lookback end | Last day of the month two months before the anchor month | 2026-09-30 |
| Scoring month | First day of the lookback-end month | 2026-09-01 |
| Prediction window | 7th of the anchor month + 30 days | 2026-11-07 to 2026-12-07 |

The notebook itself does not use the lookback dates. It builds a full monthly history and the combine step picks the scoring month.

**Source tables** (IQVIA LAAD in Snowflake, pulled by `03_HCP_Level_Features/00_Write_Input_Files`, section "File Dx_09")

| Source | Table | One row is | Used for |
| --- | --- | --- | --- |
| Dx fact | `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX` | One diagnosis code on a medical claim | Patient, service date, provider |
| Diagnosis grouping | `PHCDW.PHCDW_SANDBOX.FIN_DIAG_CD` | One ICD code with its description and comorbidity group `DIAG_GRP` | Kept groups: `KD`, `DB-KD`, `CV-KD` |

**Columns used** (input file `ops_pipeline/query_output/Dx_09`)

| Column | What it means | Example |
| --- | --- | --- |
| `PROVIDER_ID` | LAAD ID of the HCP: the referring doctor, or the rendering doctor if there is no referring doctor (`COALESCE(PROVIDER_REFERRING_ID, PROVIDER_RENDERING_ID)`) | 10000307 |
| `PATIENT_ID` | De-identified LAAD patient ID | 123456789 |
| `SVC_DT` | Service date of the claim | 2026-03-14 |
| `DIAG_GRP` | Comorbidity group from `FIN_DIAG_CD` | `KD`, `DB-KD`, `CV-KD` |
| `DIAGNOSIS_DESCRIPTION` | ICD description. Not used by the features, only for review | TYPE 2 DIABETES MELLITUS WITH DIABETIC CHRONIC KIDNEY DISEASE |

**The three comorbidity groups** (distinct patients in `Dx_09`, 2021-01-02 to 2026-09-30)

| `DIAG_GRP` | Business meaning | Descriptions | Patients | Largest descriptions |
| --- | --- | --- | --- | --- |
| `KD` | Kidney disease codes without a diabetes or heart link: CKD stages, ESRD, dialysis, kidney transplant aftercare, hypertensive CKD | 28 | 12.65M | Hypertensive CKD stage 1-4 (6.98M), CKD unspecified (4.00M), CKD stage 2 (3.14M), CKD stage 4 (2.43M), ESRD (1.71M) |
| `DB-KD` | Diabetes with a kidney complication (diabetic CKD / nephropathy). Closest to Kerendia's CKD-with-T2D label | 15 | 7.25M | T2D with diabetic CKD (5.51M), T2D with diabetic nephropathy (1.78M), T2D with other diabetic kidney complication (1.32M) |
| `CV-KD` | Hypertensive heart and chronic kidney disease, with or without heart failure | 9 | 3.46M | Hypertensive heart and CKD with HF, stage 1-4 (2.57M), without HF, stage 1-4 (0.73M) |

**Input file**

| File | What is kept | Period | Last run |
| --- | --- | --- | --- |
| `query_output/Dx_09` | Distinct patient, service date, description, group and provider for codes in the three groups. Provider not null. Inner-joined to the HCP universe | `analysis_start_month` (201901 in `00_config`) to `current_month` (lookback-end month). LAAD data itself starts 2021-01-02 | 532.5M rows, 228,582 HCPs, 2021-01-02 to 2026-09-30 |

**Common preprocessing** (used by all feature types)

1. **Month bucket.** *What:* `SVC_DT_M` = first day of the claim month. *Why:* every feature is monthly.
2. **Monthly distinct patients.** *What:* per `PROVIDER_ID` and `SVC_DT_M`, count distinct `PATIENT_ID` overall (`TOTAL_DX_PATIENTS`) and per `DIAG_GRP` (pivot, one column per group). *Detail to know:* a patient with codes from two groups counts once in the total but once in each group, so the group counts can add up to more than the total. This happens for 81,346 of the 152,307 HCPs with a value in September 2026.
3. **Full calendar** (`step2_fill_missing` in `00_Helper_Notebooks/00_step23_function`). *What:* cross-join every HCP with every month from the first to the last month in the file (2021-01 to 2026-09) and left-join the counts. *Detail to know:* months with no claims stay **empty (null), not 0**. This matters for the averages in 1.3.

---

### 1.2 Monthly patient count

**a. Data sources**

`Dx_09` after the common steps. Columns used: `PROVIDER_ID`, `PATIENT_ID`, `SVC_DT`, `DIAG_GRP`.

**b. Preprocessing steps**

1. Common steps 1 and 2.
2. Column names are cleaned: `TOTAL_DX_PATIENTS_` + group name, with `-` replaced by `_` (e.g. `DB-KD` becomes `DB_KD`).

**c. Features created**

| Feature | Business meaning | Example (scoring month, last run) |
| --- | --- | --- |
| `TOTAL_DX_PATIENTS` | Distinct patients with any kidney-related diagnosis from the HCP in the scoring month | 152,307 HCPs have a value; median 4, 90th percentile 22, max 1,862 |
| `TOTAL_DX_PATIENTS_KD` | Same, `KD` group only | Median 3 (130,563 HCPs) |
| `TOTAL_DX_PATIENTS_DB_KD` | Same, diabetic kidney disease only | Median 2 (111,870 HCPs) |
| `TOTAL_DX_PATIENTS_CV_KD` | Same, cardio-renal only | Median 1 (64,384 HCPs) |

* Empty means no such patient in that month (not 0).
* This is one calendar month (September 2026), not the last 30 days.

---

### 1.3 Rolling average

**a. Data sources**

The monthly counts from 1.2 after the full calendar (common step 3).

**b. Preprocessing steps** (`step3_lag_avg`)

1. For each HCP, order the months and take `AVG` of the monthly count over the window `rowsBetween(-i, 0)`, for i = 1, 3, 6, 12.
2. *Detail to know:* `rowsBetween(-i, 0)` covers **i + 1 months** (the current month plus the i months before it). So `_IN_LAST_1_MONTH` is the average of August and September 2026, and `_IN_LAST_12_MONTH` is the average over 13 months (September 2025 to September 2026). Verified on HCP 10000307: monthly values 3 (Aug) and 4 (Sep) give `TOTAL_DX_PATIENTS_IN_LAST_1_MONTH = 3.5`.
3. *Detail to know:* `AVG` ignores empty months, so the value is the average **per active month**, not per calendar month. An HCP with one patient in one month and nothing else has an average of 1.0, the same as an HCP with one patient every month. The helper's own code comment flags this.

**c. Features created**

| Feature | Business meaning | Example (scoring month) |
| --- | --- | --- |
| `TOTAL_DX_PATIENTS_IN_LAST_{i}_MONTH`, i = 1, 3, 6, 12 | Average monthly distinct kidney patients over the last i + 1 months (active months only) | `TOTAL_DX_PATIENTS_IN_LAST_12_MONTH`: 215,200 HCPs have a value, median 2.8, 90th percentile 18.2 |
| `TOTAL_DX_PATIENTS_{KD, DB_KD, CV_KD}_IN_LAST_{i}_MONTH` | Same, per comorbidity group | `TOTAL_DX_PATIENTS_KD_IN_LAST_12_MONTH`: median 2.0 |

* Empty only when the HCP had no patient in the group in the whole window.
* Because it is an average of monthly distinct counts, it is not the number of different patients in the window. HCP 10000307 averages 2.1 patients per month over 13 months but saw 23 different patients in the 12 months.

---

### 1.4 Running total

**a. Data sources**

Same as 1.3.

**b. Preprocessing steps** (`step3_lag_avg`)

1. For each HCP, `SUM` of the monthly count from the first month (2021-01) to the current month (`rowsBetween(unboundedPreceding, currentRow)`).

**c. Features created**

| Feature | Business meaning | Example (scoring month, universe HCPs) |
| --- | --- | --- |
| `RUNNING_TOTAL_DX_PATIENTS` | Sum of monthly distinct kidney patients since January 2021. A size-of-practice and experience measure | Median 139, 90th percentile 1,065 |
| `RUNNING_TOTAL_DX_PATIENTS_KD` | Same, `KD` group | Median 82, 90th percentile 688 |
| `RUNNING_TOTAL_DX_PATIENTS_DB_KD` | Same, diabetic kidney disease | Median 56, 90th percentile 426 |
| `RUNNING_TOTAL_DX_PATIENTS_CV_KD` | Same, cardio-renal | |

* A patient seen in 10 different months counts 10 times. This is patient-months, not distinct patients.
* The start date is fixed at the data start (2021-01), so the window gets longer every run: about 69 months at the last run. Earlier training cohorts had shorter windows, so the value grows over time for the same HCP (see 1.7).

---

### 1.5 Group share (PCT)

**a. Data sources**

The monthly counts (1.2) and the rolling averages (1.3).

**b. Preprocessing steps**

1. Monthly share: each group count divided by `TOTAL_DX_PATIENTS` in the same month.
2. Window share: each group's rolling average divided by `TOTAL_DX_PATIENTS_IN_LAST_{i}_MONTH` for the same i.
3. Empty when the numerator is empty.

**c. Features created**

| Feature | Business meaning | Example (scoring month) |
| --- | --- | --- |
| `PCT_TOTAL_DX_PATIENTS_{KD, DB_KD, CV_KD}` | Share of this month's kidney patients that are in the group | `PCT_TOTAL_DX_PATIENTS_DB_KD`: median 0.50 |
| `PCT_TOTAL_DX_PATIENTS_{group}_IN_LAST_{i}_MONTH`, i = 1, 3, 6, 12 | Same idea over the window | `PCT_TOTAL_DX_PATIENTS_CV_KD_IN_LAST_12_MONTH`: 152,452 universe HCPs have a value, median 0.38, 90th percentile 0.86 |

*Example:* `PCT_TOTAL_DX_PATIENTS_CV_KD_IN_LAST_12_MONTH = 0.40` means that, on average, 40% of the HCP's monthly kidney patients carry a hypertensive heart and CKD code. This points to a cardio-renal practice (cardiology, or nephrology with many heart-failure patients).

* *Detail to know:* the window share is a ratio of two averages that can skip different empty months, so it can be above 1. 1,862 universe HCPs have `PCT_TOTAL_DX_PATIENTS_CV_KD_IN_LAST_12_MONTH > 1` (max 6.1), and 8,122 HCPs have the `KD` 12-month share above 1.
* Because a patient can be in more than one group, the three shares can add up to more than 1 even in a single month.

---

### 1.6 What the final table looks like

| Output | Rows | Columns | Contains |
| --- | --- | --- | --- |
| `ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_claim_comorbidity_for_inference` | 10,057,608 (228,582 HCPs x 44 months) | 42 (39 features + `PROVIDER_ID`, `SVC_DT_M`, `PULL_DT`) | 1.2 to 1.5, months 2023-02 to 2026-09 |

The notebook keeps months from `date_start = "2023-02-01"` onwards. This date is **hard-coded in the notebook** (cell 6, together with `analysis_start_month = 202201` and `current_month = 202505`), and overrides the values from `00_config`. Only `date_start` is used. The combine step uses only the scoring month, so the extra months are not used at inference. 5,823 universe HCPs have no row (no kidney diagnosis in the data) and get empty values after the left join.

### 1.7 Things to watch out for

1. **Windows are one month longer than the name says.** `_IN_LAST_1_MONTH` = 2 months, `_IN_LAST_12_MONTH` = 13 months (1.3). The prior-writing notebook uses a different helper (`step3_lag`) where the window does match the name.
2. **Averages skip empty months.** The rolling features are "patients per active month", which inflates low-volume HCPs (1.3).
3. **Shares can be above 1** because the numerator and denominator skip different months (1.5).
4. **Running totals depend on the data start.** They count patient-months since 2021-01, so they grow with each run and are not comparable between early training cohorts and the current inference run. Two of the three model features are running totals (1.11).
5. **CKD stage 3 is almost missing.** `KD` has only 23,981 patients with "CHRONIC KIDNEY DISEASE, STAGE 3 (MODERATE)" against 2.43M for stage 4. Since October 2020, stage 3 is billed as N18.30 / N18.31 / N18.32 (3a / 3b), and these codes do not appear in the `FIN_DIAG_CD` groups. Stage 3 is the core Kerendia population, so most stage 3 patients only appear here through hypertensive CKD or diabetic CKD codes.
6. **Groups overlap.** The group counts and shares can add up to more than the total (common step 2).
7. **Hard-coded dates in the notebook** (1.6). Harmless today, but the config values are silently overridden.
8. **Provider role.** The HCP is the referring doctor where present, else the rendering doctor. This is the same rule as the patient Dx features, so a nephrologist who only renders services may be credited less than expected.

### 1.8 Data used and terms

**Data used**

| Source | Path (under `.../hcp_level_model/ops_pipeline/`) | Notes |
| --- | --- | --- |
| Input | `query_output/Dx_09` | Pulled 2026-10-26 |
| Output | `notebook_output/kerendia_nba_3_hcp_model_claim_comorbidity_for_inference` | `PULL_DT = 2026_10_26` |
| HCP universe | `notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` | 234,405 HCPs |
| Final 752 feature list | `/Users/sehar.aejaz.ext@bayer.com/Extra Notebooks/Final NBA 3.0 Modeling Features.xlsx` | Used for 1.9 and 1.11 |
| Helper functions | `00_Helper_Notebooks/00_step23_function` | `step2_fill_missing`, `step3_lag_avg` |

**Terms used in this document**

| Term | Meaning |
| --- | --- |
| `KD` / `DB-KD` / `CV-KD` | Kidney disease / diabetes with kidney disease / cardiovascular (hypertensive heart) with kidney disease, as grouped in `PHCDW_SANDBOX.FIN_DIAG_CD` |
| Monthly distinct patients | Different patients with at least one claim in the group in that calendar month |
| Patient-months | A patient counted once for every month they appear. Used by the running totals |
| Active month | A month in which the HCP had at least one patient in the group |
| SHAP share | A feature's mean absolute SHAP value divided by the sum over all 752 features |

### 1.9 Importance in the NBA 3.0 model (share of total mean absolute SHAP)

3 of the 39 comorbidity features are among the final 752. Together they hold **0.54%** of total SHAP. The Excel files them under "Claim-based features / Dx Claim-based".

| Family | Features created | Features kept | SHAP share |
| --- | --- | --- | --- |
| Monthly patient count (1.2) | 4 | 0 | 0.00% |
| Rolling average (1.3) | 16 | 0 | 0.00% |
| Running total (1.4) | 4 | 2 | 0.29% |
| Group share (1.5) | 15 | 1 | 0.25% |
| **Total** | **39** | **3** | **0.54%** |

### 1.10 Column volume

| Family | Overall | `KD` | `DB_KD` | `CV_KD` | Total |
| --- | --- | --- | --- | --- | --- |
| Monthly patient count | 1 | 1 | 1 | 1 | 4 |
| Rolling average (4 windows) | 4 | 4 | 4 | 4 | 16 |
| Running total | 1 | 1 | 1 | 1 | 4 |
| Group share (monthly + 4 windows) | - | 5 | 5 | 5 | 15 |
| **Total** | **6** | **11** | **11** | **11** | **39** |

---

### 1.11 Comorbidity features used in the final NBA 3.0 model

Source: `Final NBA 3.0 Modeling Features.xlsx`. SHAP rank is 1-752 by mean absolute SHAP.

| SHAP rank | Feature | Type | SHAP share |
| --- | --- | --- | --- |
| 88 | `PCT_TOTAL_DX_PATIENTS_CV_KD_IN_LAST_12_MONTH` | Group share (1.5) | 0.25% |
| 133 | `RUNNING_TOTAL_DX_PATIENTS_DB_KD` | Running total (1.4) | 0.18% |
| 237 | `RUNNING_TOTAL_DX_PATIENTS_KD` | Running total (1.4) | 0.11% |
