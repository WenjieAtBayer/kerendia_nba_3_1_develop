# NBA 3.0 IQVIA Channel Features: How They Are Built

Notebook reviewed: `/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/23_IQVIA_channel_features`. NBA 3.1 changes are not part of this file.

## 1. How NBA 3.0 builds the channel features

### 1.0 What is this section about?

The NBA (Next Best Action) model scores every HCP who could prescribe Kerendia and recommends the next promotional action. **Channel features** describe through which pharmacy channel the HCP's patients fill their cardio-renal-metabolic prescriptions: retail, mail order, long-term care or atypical (specialty and other non-retail pharmacies). The idea is that the channel mix tells something about the HCP's patients and practice setting (for example, many long-term care fills point to nursing-home patients).

This section explains how the **NBA 3.0 Ops pipeline** builds these features, so a reader can follow the logic without reading the code. Section 1.1 covers the shared foundations. Section 1.2 covers the single feature type in three parts: (a) data sources and what each column means, (b) preprocessing steps, (c) features created. 1.3 and 1.4 cover the output table and caveats. 1.5 to 1.7 cover the data used, the model importance and the column volume. 1.8 lists the channel features in the final 752-feature NBA 3.0 model. Numbers come from the latest ops run (input pulled 2026-10-26, output `PULL_DT = 2026_10_27`).

**In short**: for every HCP and calendar month, the notebook counts the distinct patient fill-days in each of the four pharmacy channels, across all CKD-basket products. The model receives the counts for **one month only**: the lookback-end month of each cohort.

| Feature type | Business question | Section |
| --- | --- | --- |
| Channel claim counts | How many patient fill-days did the HCP's prescriptions generate in retail, mail order, long-term care and atypical pharmacies in the month? | 1.2 |

### 1.1 Shared foundations

**Who is scored and on which date**

| Item | What it means | Last run |
| --- | --- | --- |
| HCP universe | `ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`. The input file is inner-joined to it when it is written | 234,405 HCPs |
| Grain | One row per HCP and calendar month (`SVC_DT_M`) with at least one fill. `99_Combine_Physician_Data` joins on `PROVIDER_ID` + `SVC_DT_M`, where `SVC_DT_M` is the first day of each cohort's `LOOKBACK_END_DATE` month (`hcp_model_inference_anchor_dates.csv`) | 18,592,989 rows, 234,278 HCPs |
| Dates | All months in the input. No window: the model only sees the lookback-end month | 2019-01 to 2026-09 (93 months) |

**Source tables** (IQVIA LAAD in Snowflake, pulled by `03_HCP_Level_Features/00_Write_Input_Files`, section "File Channel 23")

| Source | Fact table | Lookup tables | One row is |
| --- | --- | --- | --- |
| Rx (`kerendia_nba_3_0_hcp_model_channel_23`) | `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX_HIST` | `STG_CAR_IQV_LAAD_DIM_PRD` (NDC to product), `STG_CAR_IQV_LAAD_DIM_PRVDR` (NPI), `STG_CAR_IQV_LAAD_DIM_PLN`, `STG_CAR_IQV_LAAD_DIM_PTNT_DMGRPHC`, product mapping `PHCDW.PHCDW_DSAA.CKD_PRODUCT_MAPPING_VW` | One distinct prescriber x patient x fill date x channel (`SELECT DISTINCT PROVIDER_ID, PATIENT_ID, SVC_DT, CHANNEL_CODE`) |

**Columns used**

| Column | What it means | Example |
| --- | --- | --- |
| `PROVIDER_ID` | LAAD ID of the prescriber | 22591625 |
| `PATIENT_ID` | De-identified LAAD patient ID | 123456789 |
| `SVC_DT` | Fill date | 2026-06-12 |
| `CHANNEL_CODE` | Pharmacy channel of the fill: `A` = Atypical (specialty, clinic and other non-retail pharmacies), `L` = Long-term care, `M` = Mail order, `R` = Retail (notebook header) | R |

**Input file** (`ops_pipeline/query_output/`)

| File | What is kept | Period | Last run |
| --- | --- | --- | --- |
| `kerendia_nba_3_0_hcp_model_channel_23` | Products in `CKD_PRODUCT_MAPPING_VW` (CKD / cardio-renal-metabolic basket), treatment category not "other", `NPI_NUMBER` not null, `CHANNEL_CODE` not null. **All claim types**: there is no filter on `REJECT_CODE`, so paid, rejected and reversed claims all count. The product, treatment category and category columns are computed in the SQL but dropped by `SELECT DISTINCT` | `analysis_start_month` (201901) to `current_month` | 3.91B rows, 234,339 HCPs, 128.8M patients, 2019-01-01 to 2026-09-30 |

Rows by channel in the input:

| Channel | Rows | Share of rows | HCPs |
| --- | --- | --- | --- |
| R (Retail) | 3.47B | 88.8% | 234,295 |
| M (Mail order) | 243.4M | 6.2% | 227,385 |
| L (Long-term care) | 99.0M | 2.5% | 216,691 |
| A (Atypical) | 96.7M | 2.5% | 221,097 |

---

### 1.2 Channel claim counts

**a. Data sources**

`kerendia_nba_3_0_hcp_model_channel_23` (`PROVIDER_ID`, `PATIENT_ID`, `SVC_DT`, `CHANNEL_CODE`) and the ID mapping `query_output/kerendia_nba_3_0_npi_bhid_mapping` (`PROVIDER_ID`, `BH_ID`).

**b. Preprocessing steps**

1. **Month.** *What:* `SVC_DT_M = date_trunc('MM', SVC_DT)`.
2. **Count per channel.** *What:* group by `PROVIDER_ID` and `SVC_DT_M`, pivot on `CHANNEL_CODE`, count rows. *Detail to know:* a row is a distinct patient x fill date x channel, so a patient who fills three basket drugs at a retail pharmacy on the same day counts **once**. The value is "patient fill-days", not claims or prescriptions.
3. **Fill with 0.** *What:* a channel without fills in a month the HCP has other fills gets 0.
4. **Rename.** *What:* `A`, `L`, `M`, `R` become `Channel_A`, `Channel_L`, `Channel_M`, `Channel_R`.
5. **Add BHID.** *What:* inner join to the ID mapping on `PROVIDER_ID`, keep `BHID`, drop `NPI_NUMBER`. HCPs without a mapping are dropped (234,339 to 234,278 HCPs).
6. **Save** with `PULL_DT`.

**c. Features created**

| Feature | Business meaning | Example (June 2026, 228,247 HCPs with a row) |
| --- | --- | --- |
| `Channel_A` | Patient fill-days at atypical pharmacies in the month | Median 1, 90th percentile 13, max 1,739. 112,214 HCPs have 0 |
| `Channel_L` | Patient fill-days at long-term care pharmacies | Median 1, 90th percentile 11, max 2,554. 91,824 HCPs have 0 |
| `Channel_M` | Patient fill-days at mail-order pharmacies | Median 9, 90th percentile 33, max 458. 32,814 HCPs have 0 |
| `Channel_R` | Patient fill-days at retail pharmacies | Median 170, 90th percentile 410, max 4,128. 1,279 HCPs have 0 |

*Example:* HCP 22591625 has, for June 2026, `Channel_A = 0`, `Channel_L = 6`, `Channel_M = 9`, `Channel_R = 272`. Recounting the distinct patient x day rows per channel in the input for that HCP and month gives the same values.

* Empty (in the combined table) means the HCP had no basket fill at all in that month.
* 0 means the HCP had fills in other channels but none in this one.

---

### 1.3 What the final table looks like

| Output | Rows | Columns | Contains |
| --- | --- | --- | --- |
| `ops_pipeline/notebook_output/kerendia_nba_3_0_hcp_model_channel_feature_for_inference` | 18,592,989 (one per HCP and month with fills) | 8 (4 features + `PROVIDER_ID`, `SVC_DT_M`, `BHID`, `PULL_DT`) | 1.2 |

All rows are in the HCP universe. For June 2026, 228,247 of the 234,405 universe HCPs (97.4%) have a row.

### 1.4 Things to watch out for

1. **One month only.** The combine picks the row for the lookback-end month, so each feature is a single calendar month. One month mostly reflects refill timing and is noisy. There are no 3, 6 or 12-month windows.
2. **Patient fill-days, not claims.** `SELECT DISTINCT` on patient x day x channel collapses products and claims. The names suggest claim counts.
3. **Mostly a size measure.** All four are counts, so they grow with the HCP's panel. `Channel_R` correlates 0.81 (Spearman, June 2026) with the HCP's all-market NBRx in January to June 2026, and 0.70 with `Channel_M`. Nothing describes the channel **mix** (shares).
4. **Duplicated by another notebook.** `02_Other_Features - DRG, Claim-related/1_Additional_HCP_level_features` builds the same four channels from the raw LAAD Rx table (paid claims only, claim counts), with 1, 2, 3, 6 and 12-month windows, running totals and splits by drug class. Its overall channel counts correlate **0.94 to 0.99** (Spearman, September 2026) with the same counts rebuilt from this notebook's input, and are 7% to 28% higher at the median because they count claims, not patient-days. Those are the channel features that made it into the final model (1.6).
5. **All claim types.** Rejected and reversed claims count as fills, although a rejected claim was never dispensed.
6. **Different fact table.** The input uses `STG_CAR_IQV_LAAD_FCT_RX_HIST` (starts 2019-01-01), while the other HCP inputs use `STG_CAR_IQV_LAAD_FCT_RX`.
7. **Empty, not 0, for months without fills.** About 2.6% of universe HCPs have no row in a given month (June 2026), so all four features are empty for them.
8. **Same patient-day in two channels.** A patient filling at retail and mail order on the same day counts once in each channel (72,540 such patient-days in June 2026, out of 52.9M rows).
9. **Extra `BHID` column.** The output carries `BHID`, which no feature needs, and the inner join to the ID mapping drops 61 HCPs.

### 1.5 Data used and terms

**Data used**

| Source | Path (under `.../hcp_level_model/ops_pipeline/`) | Notes |
| --- | --- | --- |
| Rx channel input | `query_output/kerendia_nba_3_0_hcp_model_channel_23` | Pulled 2026-10-26 |
| ID mapping | `query_output/kerendia_nba_3_0_npi_bhid_mapping` | `PROVIDER_ID` to `BH_ID` |
| Output | `notebook_output/kerendia_nba_3_0_hcp_model_channel_feature_for_inference` | `PULL_DT = 2026_10_27` |
| HCP universe | `notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` | 234,405 HCPs |
| Overlapping channel features | `notebook_output/kerendia_nba_3_hcp_model_additional_hcp_level_features_for_inference` | From `1_Additional_HCP_level_features` |
| Final 752 feature list | `/Users/sehar.aejaz.ext@bayer.com/Extra Notebooks/Final NBA 3.0 Modeling Features.xlsx` | Used for 1.6 and 1.8 |

**Terms used in this document**

| Term | Meaning |
| --- | --- |
| Channel | Type of pharmacy that filled the prescription (retail, mail order, long-term care, atypical) |
| Atypical | Pharmacies outside retail, mail and LTC, mostly specialty and clinic pharmacies |
| Patient fill-day | One patient with at least one basket fill in a channel on a given day |
| CKD basket | Products in `CKD_PRODUCT_MAPPING_VW` (ACE / ARB, SGLT2, GLP-1, MRA, diuretics, beta and calcium channel blockers, DPP-4 and others) |
| SHAP share | A feature's mean absolute SHAP value divided by the sum over all 752 features |

### 1.6 Importance in the NBA 3.0 model (share of total mean absolute SHAP)

**None of the 4 features is among the final 752.** The channel signal in the model comes from other notebooks:

| Family | Notebook | Features in the 752 | SHAP share | Top feature |
| --- | --- | --- | --- | --- |
| Channel counts (1.2) | `23_IQVIA_channel_features` | 0 of 4 | 0% | - |
| Rx claims by channel, overall and by drug class | `1_Additional_HCP_level_features` | 15 | 2.33% | `TOTAL_HCP_RX_MAIL_ORDER_CHANNEL_CLAIMS_IN_LAST_12_MONTH`, rank 10, 1.12% |
| Kerendia NBRx / NRx / TRx by channel (LRx) | `26_Features_NBRx`, `27_Features_NRx`, `28_Features_TRx` | 6 | 0.37% | `TOTAL_HCP_NBRX_CLAIMS_CHANNEL_R_IN_LAST_6_MONTH`, rank 211, 0.12% |

### 1.7 Column volume

| Family | Atypical | Long-term care | Mail order | Retail | Total |
| --- | --- | --- | --- | --- | --- |
| Channel counts | 1 | 1 | 1 | 1 | 4 |

---

### 1.8 Channel features used in the final NBA 3.0 model

Source: `Final NBA 3.0 Modeling Features.xlsx`. SHAP rank is 1-752 by mean absolute SHAP.

No feature from this notebook is in the final model. For reference, the top channel features from the other notebooks (1.6):

| SHAP rank | Feature | Notebook | SHAP share |
| --- | --- | --- | --- |
| 10 | `TOTAL_HCP_RX_MAIL_ORDER_CHANNEL_CLAIMS_IN_LAST_12_MONTH` | `1_Additional_HCP_level_features` | 1.12% |
| 58 | `TOTAL_HCP_RX_BETA_BLOCKERS_MAIL_ORDER_CHANNEL_CLAIMS_IN_LAST_6_MONTH` | `1_Additional_HCP_level_features` | 0.36% |
| 112 | `TOTAL_HCP_RX_ACE_ARBS_ATYPICAL_CHANNEL_CLAIMS_IN_LAST_3_MONTH` | `1_Additional_HCP_level_features` | 0.20% |
| 207 | `TOTAL_HCP_RX_ACE_ARBS_ATYPICAL_CHANNEL_CLAIMS_IN_LAST_1_MONTH` | `1_Additional_HCP_level_features` | 0.12% |
| 211 | `TOTAL_HCP_NBRX_CLAIMS_CHANNEL_R_IN_LAST_6_MONTH` | `26_Features_NBRx` | 0.12% |
| 220 | `TOTAL_HCP_NBRX_CLAIMS_CHANNEL_R_IN_LAST_12_MONTH` | `26_Features_NBRx` | 0.12% |
| 230 | `TOTAL_HCP_RX_DIURETICS_RETAIL_CHANNEL_CLAIMS_IN_LAST_12_MONTH` | `1_Additional_HCP_level_features` | 0.11% |
| 309 | `TOTAL_HCP_RX_RETAIL_CHANNEL_CLAIMS_IN_LAST_1_MONTH` | `1_Additional_HCP_level_features` | 0.08% |
