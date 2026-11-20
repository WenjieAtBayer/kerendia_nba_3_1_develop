# Analysis: HCP Census features (nb 08_census_features)

NBA 3.0 profile of the census (SDoH) feature family. For NBA 3.1 readiness, see `08_2_census_data_assessment.md` in this folder. Section 7 below lists the points in this profile that the 3.1 checks have since settled.

## 1. Notebook Overview
This notebook creates Social Determinants of Health (SDoH) features from US Census American Community Survey (ACS) data at ZIP code level. They describe the local demographics, education, poverty, transportation, employment, income and insurance of the areas where HCPs practice. The table has no HCP key. It reaches HCPs only through the nb 20 geo output (HCP ZIP), which `99_Combine_Physician_Data` joins on.

## 2. Data Sources Used

| Source | File/Path | Purpose |
| --- | --- | --- |
| Databricks Volume | `SDoH Walgreens v2.csv` in `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/input_files/` | US Census ACS data by ZIP code / ZCTA (41,011 ZIPs) |
| Pipeline output (nb 20) | `kerendia_nba_3_hcp_model_geographic_features_for_inference` | HCP to ZIP link used by the combine step |

The CSV is an extract of the AHRQ SDOH Database 2020 ZIP file (ACS 2016-2020 5-year estimates). Its UC source is `dem_zip_sdoh_acs20` (verified in the data assessment, Section 1.1).

## 3. Data Source Column Usage

**Method.** Total columns come from the CSV header. Source fill rates are on all 41,011 ZIPs. HCP fill rates are after the ZIP join to the NBA 3.0 universe (234,405 HCPs).

### 3.1 Summary

| Source | Table/File | Total Columns | Columns Used | Usage Rate |
| --- | --- | --- | --- | --- |
| Databricks (Volume) | `SDoH Walgreens v2.csv` | 24 | 23 | 95.8% |

### 3.2 SDoH Walgreens v2.csv (24 columns, 23 used)

All 24 columns are read. ZCTA is dropped after load. The other 23 columns (ZIPCODE + 22 ACS features) are saved to the output.

| Column | Fill Rate (source ZIPs) | Fill Rate (HCP level) | Used For |
| --- | --- | --- | --- |
| ZIPCODE | 100% | 91.2% | Join key |
| ZCTA | 100% | - | Dropped |
| ACS_PCT_HISPANIC_ZC | 99.1% | 90.9% | Feature (SHAP rank 26) |
| ACS_PCT_LT_HS_ZC | 99.1% | 90.9% | Feature (SHAP rank 66) |
| ACS_PCT_UNEMPLOY_ZC | 99.2% | 90.8% | Feature (SHAP rank 99) |
| ACS_PCT_WHITE_ZC | 99.1% | 90.9% | Feature (SHAP rank 101) |
| ACS_PCT_OTHER_RACE_ZC | 99.1% | 90.9% | Feature (SHAP rank 149) |
| ACS_PCT_ASIAN_ZC | 99.1% | 90.9% | Feature (SHAP rank 159) |
| ACS_PCT_POV_BLACK_ZC | 96.4% | 88.9% | Feature (SHAP rank 203) |
| ACS_PCT_GRADUATE_DGR_ZC | 99.1% | 90.9% | Feature (SHAP rank 208) |
| ACS_PCT_TRANSPORT_ZC | 99.2% | 90.8% | Feature (SHAP rank 228) |
| ACS_PCT_UNINSURED_BELOW64_ZC | 99.2% | 90.8% | Feature (SHAP rank 243) |
| ACS_PCT_BACHELOR_DGR_ZC | 99.1% | 90.9% | Feature (SHAP rank 246) |
| ACS_PCT_HS_GRADUATE_ZC | 99.1% | 90.9% | Feature (SHAP rank 249) |
| ACS_PCT_COLLEGE_ASSOCIATE_DGR_ZC | 99.1% | 90.9% | Feature (SHAP rank 252) |
| ACS_PCT_POSTHS_ED_ZC | 99.1% | 90.9% | Feature (SHAP rank 261) |
| ACS_PCT_PUBL_TRANSIT_ZC | 99.2% | 90.8% | Feature (SHAP rank 272) |
| ACS_PCT_POV_ASIAN_ZC | 94.7% | 87.2% | Feature (SHAP rank 275) |
| ACS_PCT_BLACK_ZC | 99.1% | 90.9% | Feature (SHAP rank 286) |
| ACS_PER_CAPITA_INC_ZC | 99.1% | 90.9% | Feature (SHAP rank 302) |
| ACS_PCT_EDUC_ZC | 99.2% | 90.8% | Feature (SHAP rank 318) |
| ACS_PCT_UNINSURED_ZC | 99.2% | 90.8% | Feature (SHAP rank 328) |
| ACS_PCT_POV_HISPANIC_ZC | 98.3% | 90.0% | Feature (SHAP rank 361) |
| ACS_PCT_POV_WHITE_ZC | 99.0% | 90.6% | Feature (SHAP rank 410) |

HCP fill rates are 87-91%. The gap from 100% is the leading-zero ZIP mismatch (12,705 HCPs, 5.4%) plus 7,977 HCPs (3.4%) with no geo row (Section 6.1). Race-specific poverty columns have more nulls in the source itself (POV_ASIAN 5.3%, POV_BLACK 3.6%, POV_HISPANIC 1.7%).

## 4. Features Created

22 feature columns, grouped as below. Descriptions are from the 3.0 analysis file (based on the column names); the exact definitions are in the AHRQ SDOH 2020 codebook.

### Race / Ethnicity (5)
| Feature | Description |
| --- | --- |
| ACS_PCT_ASIAN_ZC | % Asian population in ZIP |
| ACS_PCT_BLACK_ZC | % Black population in ZIP |
| ACS_PCT_HISPANIC_ZC | % Hispanic population in ZIP |
| ACS_PCT_OTHER_RACE_ZC | % Other race population in ZIP |
| ACS_PCT_WHITE_ZC | % White population in ZIP |

### Education (7)
| Feature | Description |
| --- | --- |
| ACS_PCT_EDUC_ZC | % with education attainment |
| ACS_PCT_COLLEGE_ASSOCIATE_DGR_ZC | % with college associate degree |
| ACS_PCT_BACHELOR_DGR_ZC | % with bachelor's degree |
| ACS_PCT_GRADUATE_DGR_ZC | % with graduate degree |
| ACS_PCT_HS_GRADUATE_ZC | % high school graduate |
| ACS_PCT_LT_HS_ZC | % with less than high school |
| ACS_PCT_POSTHS_ED_ZC | % with post-high-school education (equals ASSOCIATE + BACHELOR + GRADUATE; see Section 7) |

### Poverty (4)
| Feature | Description |
| --- | --- |
| ACS_PCT_POV_ASIAN_ZC | % of Asian population in poverty |
| ACS_PCT_POV_BLACK_ZC | % of Black population in poverty |
| ACS_PCT_POV_HISPANIC_ZC | % of Hispanic population in poverty |
| ACS_PCT_POV_WHITE_ZC | % of White population in poverty |

### Transportation (2)
| Feature | Description |
| --- | --- |
| ACS_PCT_TRANSPORT_ZC | % using transportation (general) |
| ACS_PCT_PUBL_TRANSIT_ZC | % using public transit |

### Employment and Income (2)
| Feature | Description |
| --- | --- |
| ACS_PCT_UNEMPLOY_ZC | % unemployed |
| ACS_PER_CAPITA_INC_ZC | Per capita income |

### Insurance (2)
| Feature | Description |
| --- | --- |
| ACS_PCT_UNINSURED_ZC | % uninsured |
| ACS_PCT_UNINSURED_BELOW64_ZC | % uninsured, under 64 |

## 5. Business Rules Applied
1. ZIPCODE is zero-padded to 5 digits (`str.zfill(5)`).
2. ZCTA is dropped.
3. The pandas frame is converted to a Spark DataFrame.
4. PULL_DT (run date) is added as a metadata column.
5. Output is written as Delta (overwrite).

Output: `kerendia_nba_3_volume/hcp_level_model/ops_pipeline/notebook_output/kerendia_nba_3_hcp_model_sdoh_features_for_inference` (41,011 rows, one per 5-digit ZIPCODE).

## 6. NBA 3.0 Feature Profile (HCP counts, nulls, distribution)

**Method.** Profiled on 2026-11-17 from the NBA 3.0 ops output. I rebuilt the `99_Combine_Physician_Data` join: NBA 3.0 universe (**234,405 HCPs**), left join to the nb 20 geo output (`ZIP_CODE` renamed `ZIP_CODE_GEO`), then left join to the census table on `ZIP_CODE_GEO == ZIPCODE`. "HCPs with value" = universe HCPs with a non-null value after that join. The features are static, so the percentages are the same in every cohort.

### 6.1 HCP coverage funnel

| Step | HCPs | % of universe |
| --- | --- | --- |
| NBA 3.0 universe | 234,405 | 100% |
| With a nb 20 geo row (ZIP_CODE) | 226,428 | 96.6% |
| Matched to a census ZIP **as the pipeline joins today** | 213,660 | **91.2%** |
| Would match if ZIP_CODE_GEO were zero-padded to 5 digits | 226,365 | 96.6% |
| **Lost to the leading-zero mismatch** | **12,705** | **5.4%** |
| No geo row at all (no ZIP) | 7,977 | 3.4% |

**Join defect.** nb 20 strips leading zeros from ZIP_CODE, but nb 08 zero-pads ZIPCODE. All 12,707 universe HCPs with a 3- or 4-digit ZIP (ZIPs starting with 0: Puerto Rico / USVI and New England / NJ) get null for every SDoH feature; padding recovers 12,705 of them. These HCPs are not missing at random, which matters for a geography-driven feature family.

### 6.2 Per-feature profile (HCP level, n = 234,405)

| Feature | HCPs with value | % | Null HCPs | Null % | Distinct values | HCPs = 0 | Min | P25 | Median | Mean | P75 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ACS_PCT_HISPANIC_ZC | 213,150 | 90.9% | 21,255 | 9.1% | 4,155 | 1,077 (0.5%) | 0 | 4.08 | 8.74 | 17.11 | 20.83 | 100 |
| ACS_PCT_LT_HS_ZC | 213,143 | 90.9% | 21,262 | 9.1% | 3,127 | 688 (0.3%) | 0 | 5.35 | 9.15 | 11.23 | 14.75 | 83.19 |
| ACS_PCT_UNEMPLOY_ZC | 212,847 | 90.8% | 21,558 | 9.2% | 1,658 | 485 (0.2%) | 0 | 3.68 | 4.96 | 5.57 | 6.65 | 100 |
| ACS_PCT_WHITE_ZC | 213,150 | 90.9% | 21,255 | 9.1% | 5,761 | 6 (0.0%) | 0 | 59.72 | 75.48 | 70.65 | 86.41 | 100 |
| ACS_PCT_OTHER_RACE_ZC | 213,150 | 90.9% | 21,255 | 9.1% | 1,981 | 7,118 (3.0%) | 0 | 0.77 | 1.99 | 4.65 | 4.88 | 73.31 |
| ACS_PCT_ASIAN_ZC | 213,150 | 90.9% | 21,255 | 9.1% | 1,993 | 7,149 (3.0%) | 0 | 1.04 | 2.81 | 5.88 | 6.68 | 75.59 |
| ACS_PCT_POV_BLACK_ZC | 208,334 | 88.9% | 26,071 | 11.1% | 4,681 | 11,621 (5.0%) | 0 | 9.44 | 19.54 | 22.68 | 31.86 | 100 |
| ACS_PCT_GRADUATE_DGR_ZC | 213,143 | 90.9% | 21,262 | 9.1% | 3,231 | 504 (0.2%) | 0 | 7.07 | 11.36 | 14.21 | 18.70 | 74.19 |
| ACS_PCT_TRANSPORT_ZC | 212,844 | 90.8% | 21,561 | 9.2% | 1,468 | 985 (0.4%) | 0 | 3.48 | 4.74 | 5.15 | 6.36 | 100 |
| ACS_PCT_UNINSURED_BELOW64_ZC | 212,825 | 90.8% | 21,580 | 9.2% | 2,773 | 306 (0.1%) | 0 | 5.42 | 8.47 | 9.99 | 13.05 | 80 |
| ACS_PCT_BACHELOR_DGR_ZC | 213,143 | 90.9% | 21,262 | 9.1% | 3,630 | 473 (0.2%) | 0 | 13.70 | 19.82 | 21.05 | 27.71 | 100 |
| ACS_PCT_HS_GRADUATE_ZC | 213,143 | 90.9% | 21,262 | 9.1% | 4,269 | 273 (0.1%) | 0 | 18.10 | 25.56 | 25.20 | 32.10 | 100 |
| ACS_PCT_COLLEGE_ASSOCIATE_DGR_ZC | 213,143 | 90.9% | 21,262 | 9.1% | 3,253 | 211 (0.1%) | 0 | 23.97 | 29.03 | 28.32 | 33.17 | 100 |
| ACS_PCT_POSTHS_ED_ZC | 213,143 | 90.9% | 21,262 | 9.1% | 5,607 | 171 (0.1%) | 0 | 52.50 | 63.50 | 63.58 | 75.18 | 100 |
| ACS_PCT_PUBL_TRANSIT_ZC | 212,849 | 90.8% | 21,556 | 9.2% | 1,832 | 23,491 (10.0%) | 0 | 0.29 | 1.11 | 4.97 | 3.96 | 100 |
| ACS_PCT_POV_ASIAN_ZC | 204,470 | 87.2% | 29,935 | **12.8%** | 3,308 | 35,072 (15.0%) | 0 | 2.42 | 8.66 | 13.86 | 18.92 | 100 |
| ACS_PCT_BLACK_ZC | 213,150 | 90.9% | 21,255 | 9.1% | 3,798 | 2,574 (1.1%) | 0 | 2.19 | 6.13 | 12.84 | 16.34 | 100 |
| ACS_PER_CAPITA_INC_ZC | 212,970 | 90.9% | 21,435 | 9.1% | 12,016 | 0 | 1,989 | 25,944 | 32,294 | 36,377 | 42,540 | 244,496 |
| ACS_PCT_EDUC_ZC | 212,844 | 90.8% | 21,561 | 9.2% | 2,905 | 127 (0.1%) | 0 | 20.34 | 23.65 | 24.50 | 27.53 | 100 |
| ACS_PCT_UNINSURED_ZC | 212,830 | 90.8% | 21,575 | 9.2% | 2,429 | 290 (0.1%) | 0 | 4.59 | 7.17 | 8.51 | 11.05 | 67.21 |
| ACS_PCT_POV_HISPANIC_ZC | 211,069 | 90.0% | 23,336 | 10.0% | 4,552 | 9,944 (4.2%) | 0 | 8.60 | 15.84 | 18.74 | 25.68 | 100 |
| ACS_PCT_POV_WHITE_ZC | 212,377 | 90.6% | 22,028 | 9.4% | 2,923 | 348 (0.1%) | 0 | 5.87 | 9.27 | 11.25 | 14.06 | 100 |

Percentiles are approximate (Spark `percentile_approx`).

### 6.3 What the nulls are made of
* About 20,745 nulls are shared by every SDoH column. These are HCPs that never get a census row: 7,977 with no geo row plus 12,768 whose ZIP finds no census match (12,705 of those are the leading-zero defect).
* Matched ZIPs add their own source nulls: 510 HCPs for the race columns, and more for the race-specific poverty columns (POV_ASIAN 12.8% total null, POV_BLACK 11.1%, POV_HISPANIC 10.0%).
* Several columns reach 0 or 100 (PUBL_TRANSIT = 0 for 10.0% of HCPs, POV_ASIAN = 0 for 15.0%). Section 7 checks these against ZIP population.

## 7. Points Settled by the 3.1 Checks (2026-11-18)

These were open or assumed in the 3.0 profile. Detail is in `08_2_census_data_assessment.md`.

| Point | Finding |
| --- | --- |
| Data vintage | ACS 2016-2020 5-year estimates (AHRQ SDOH Database 2020 ZIP file). Source table `dem_zip_sdoh_acs20`; the CSV is an exact extract of it. |
| ACS_PCT_POSTHS_ED_ZC | Equals ASSOCIATE + BACHELOR + GRADUATE for every ZIP (max abs difference 0.01, rounding). It is redundant. |
| Zeros vs ZIP population | Checked on the 3.1 universe with population from `dem_zip_sdoh_acs20`. PUBL_TRANSIT = 0 for 28,386 HCPs: their median ZIP population is 11,527 vs 30,480 for HCPs with a value > 0, and 22.8% of the zero HCPs are in ZIPs under 5,000 people. POV_ASIAN = 0 for 45,060 HCPs: median ZIP population 16,121 vs 32,240, and 9.8% under 5,000. Zeros lean to smaller ZIPs, but most sit in ZIPs of 5,000+, so they are mostly real low values, not small-sample artefacts. |
| Leading-zero defect | Still relevant: the 3.1 draft joins on ZCTA instead of ZIPCODE, which loses 4,443 HCPs (a different defect with the same effect). |
| "Static" assumption | The census values are static per ZIP, but an HCP's ZIP is not: 7-9% of HCPs had a different BEST_AFFL ZIP in the Q2 and Q3 2026 snapshots. |

## 8. Features in the 752 Final NBA 3.0 Modeling Features

**All 22 features** appear in the final 752 (Category: Geographic Features, Sub Category: SDoH), a 100% retention rate.

Ranked by Mean_Abs_SHAP:

| Feature | Mean_Abs_SHAP | Share of total SHAP | Overall rank (of 752) | Rank in SDoH (of 22) |
| --- | --- | --- | --- | --- |
| **ACS_PCT_HISPANIC_ZC** | 0.041448 | 0.58% | 26 | 1st |
| ACS_PCT_LT_HS_ZC | 0.021943 | 0.31% | 66 | 2nd |
| ACS_PCT_UNEMPLOY_ZC | 0.015822 | 0.22% | 99 | 3rd |
| ACS_PCT_WHITE_ZC | 0.015638 | 0.22% | 101 | 4th |
| ACS_PCT_OTHER_RACE_ZC | 0.011785 | 0.17% | 149 | 5th |
| ACS_PCT_ASIAN_ZC | 0.011211 | 0.16% | 159 | 6th |
| ACS_PCT_POV_BLACK_ZC | 0.008922 | 0.13% | 203 | 7th |
| ACS_PCT_GRADUATE_DGR_ZC | 0.008663 | 0.12% | 208 | 8th |
| ACS_PCT_TRANSPORT_ZC | 0.008173 | 0.11% | 228 | 9th |
| ACS_PCT_UNINSURED_BELOW64_ZC | 0.007733 | 0.11% | 243 | 10th |
| ACS_PCT_BACHELOR_DGR_ZC | 0.007580 | 0.11% | 246 | 11th |
| ACS_PCT_HS_GRADUATE_ZC | 0.007461 | 0.10% | 249 | 12th |
| ACS_PCT_COLLEGE_ASSOCIATE_DGR_ZC | 0.007385 | 0.10% | 252 | 13th |
| ACS_PCT_POSTHS_ED_ZC | 0.007166 | 0.10% | 261 | 14th |
| ACS_PCT_PUBL_TRANSIT_ZC | 0.006979 | 0.10% | 272 | 15th |
| ACS_PCT_POV_ASIAN_ZC | 0.006846 | 0.10% | 275 | 16th |
| ACS_PCT_BLACK_ZC | 0.006485 | 0.09% | 286 | 17th |
| ACS_PER_CAPITA_INC_ZC | 0.006072 | 0.09% | 302 | 18th |
| ACS_PCT_EDUC_ZC | 0.005680 | 0.08% | 318 | 19th |
| ACS_PCT_UNINSURED_ZC | 0.005441 | 0.08% | 328 | 20th |
| ACS_PCT_POV_HISPANIC_ZC | 0.004768 | 0.07% | 361 | 21st |
| ACS_PCT_POV_WHITE_ZC | 0.003886 | 0.05% | 410 | 22nd |

## 9. Key Observations
* ACS_PCT_HISPANIC_ZC has the highest SHAP in the family (0.041448, rank 26). It is the only census feature in the top 50.
* Education (LT_HS rank 66, GRADUATE rank 208) and unemployment (rank 99) follow. Together the 22 features are 2.9% of the 752 and about 3.2% of total SHAP (sum of the rounded shares above).
* All 22 survived selection despite overlap: POSTHS_ED is an exact sum of three other columns (Section 7). Retention does not mean each column adds information.
* About 9% of HCPs get null for every census feature in 3.0, mostly because of the leading-zero join defect, and those HCPs are concentrated in the North-East and Puerto Rico.
* SHAP shows importance, not direction. The direction of the effect (higher LT_HS goes with more writing; higher WHITE with less) is measured in the 3.1 data assessment, Section 3.
