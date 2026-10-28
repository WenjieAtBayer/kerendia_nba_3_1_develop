# Kerendia Data Sources

**Dates checked on: 2026-10-21** (Min/Max Service Date and Last Updated values are as of this date)

| S.No | Dataset Name/Use | Table Name | Source | New Table Name (PharmAce) | Data Migration Assessment | Min Service Date | Max Service Date | Last Updated |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | LAAD - Dx Data | PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX | IQVIA | No Expected Change | | 2021-01-02 | 2026-09-25 | 2026-10-16 |
| 2 | LAAD - Px Data | PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_PX | IQVIA | No Expected Change | | 2021-01-02 | 2026-09-25 | 2026-10-16 |
| 3 | LAAD - Rx Data | PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX | IQVIA | No Expected Change | | 2021-01-02 | 2026-09-25 | 2026-10-16 |
| 4 | LRx Data | PHCDW.PHCDW_DSAA.KERENDIA_LAAD_BASED_LRX_V6 and lrx_nbrx (For T1D)  | ZS | No Expected Change | From where are the new 56K (3.3%) HCPs coming? | LRX_V6: 2023-01-06; lrx_nbrx: 2021-07-30 | LRX_V6: 2026-09-25; lrx_nbrx: 2026-09-25 | LRX_V6: 2026-10-18; lrx_nbrx: 2026-10-19 |
| 5 | Lab Tests | PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_QUEST_TO_LAAD_HIST | IQVIA | No Expected Change | | 2001-01-01 (excl. 8 rows with 0001-01-01) | 2026-10-05 | 2026-10-20 |
| 6 | Copay Program | PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_COPAY_PROGRAM | PACE | To be Decided | | 2021-08-04 | 2026-10-09 | 2023-10-12 (view DDL) |
| 7 | DTC Direct Buy | Before: CPH_DB_PROD.ENRICH_V2.MMX_FLASHTALKING_NEW_DAILYFILES_V1 / After: CPH_DB_PROD.ENRICH.FLASHTALKING_DMA | Galaxy | Galaxy Table - Confirmation Required | | Before: 2023-01-01; After: 2023-01-01 | Before: 2026-06-14; After: 2026-10-20 | Before: 2026-06-15; After: 2026-10-21 |
| 8 | Digital Engagement | PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB | PACE | No Expected Change | | 2023-01-01 | 2026-10-16 | 2026-10-19 |
| 9 | F2F Calls | Current: CPH_DB_PROD.MODEL_V2.FACT_CALL; Suggested: CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CUST_CALL_ACTY | Galaxy | Galaxy Table - Confirmation Required (TBD) |  | Current: 2017-12-31; Suggested: 2017-12-31 | Current: 2026-10-16 (excl. bad 2107 dates); Suggested: 2026-10-16 | Current: 2026-10-21; Suggested: 2026-10-21 |
| 10 | FTP Scripts | PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP | PACE | To Be Decided | | 2021-10-11 | 2026-10-09 | 2023-01-06 (view DDL) |
| 11 | Meta-Instagram Ads | FUNNEL_PROD_INB2.FUNNEL__MK7FZ_CN_UWQY_VMROR.FUNNEL_DATA_FACEBOOKADS_GEO | PACE | No Expected Change | | 2023-05-09 | 2026-10-20 | 2026-10-21 (view) |
| 12 | Samples | Current: CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER / Previous: CPH_DB_PROD.ANALYTICS_V2.KERENDIA_SAMPLES, CPH_DB_PROD.ANALYTICS_V2.KERENDIA_SAMPLES_SHIPPED | Galaxy | Galaxy Table - Confirmation Required (To Be Decided) | Used in 17_promotional_features_samples | Current: 2021-08-02; KERENDIA_SAMPLES: 2021-07-29; KERENDIA_SAMPLES_SHIPPED: 2021-07-29 | Current: 2026-10-16; KERENDIA_SAMPLES: 2025-10-24; KERENDIA_SAMPLES_SHIPPED: 2025-10-24 | Current: 2026-10-21; KERENDIA_SAMPLES: 2025-10-30; KERENDIA_SAMPLES_SHIPPED: 2025-10-30 |
| 13 | Speaker Programs | CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM | Galaxy | Galaxy Table - Confirmation Required | | 2018-02-08 | 2026-10-21 (events scheduled up to 2027-02-05) | 2026-10-21 |
| 14 | HQ Email Engagement Status | PHCDW.PHCDW_CDM.HCP_EMAIL_LIST | PACE | No Expected Change | | | | |
| 15 | iRep Emails | CPH_DB_PROD.MODEL_V2.FACT_SENT_EMAIL | Galaxy | Galaxy Table - Confirmation Required | | 2019-07-08 | 2026-10-19 | 2026-10-21 |
| 16 | ClickStream Data | CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM | Galaxy | Galaxy Table - Confirmation Required | Used in 18_promotional_ClickStream_features | 2019-07-12 | 2026-10-16 | 2026-10-21 |
| 17 | Drug Formulary History (Deprecated - Replaced by MMIT) | CPH_DB_PROD.ANALYTICS_V2.ANLT_DRG_FRMLRY_HIST | Galaxy | Galaxy Table - Confirmation Required | Used in 2.1/2.2/2.3_DRG_Features (Kerendia, Farxiga, Jardiance) | 2021-07 (data month) | 2025-11 (data month) | 2026-09-28 |
| 18 | MSL Visits / MSL Calls | CPH_DB_PROD.MODEL_V2.FACT_CALL / CPH_DB_PROD.ANALYTICS.FACT_CALL | Galaxy | Galaxy Table - Confirmation Required | Used in 32_MSL_Visits_features, 00_Write_Input_Files | MODEL_V2: 2017-12-31; ANALYTICS: 2016-10-01 | MODEL_V2: 2026-10-16; ANALYTICS: 2026-06-19 (both excl. bad 2107 dates) | MODEL_V2: 2026-10-21; ANALYTICS: 2026-07-11 |
| 19 | Colocation Flag | PHCDW.PHCDW_STG.MDM_STG_HCP_ADDR | IQVIA | Confirmation Required | | 2017-10-12 (record created) | 2026-10-15 (record created) | 2026-10-16 |
| 20 | Business Positioning Tool | PHCDW.PHCDW_TARGETING.BPT_KER_HCP | PACE | No Expected Change | UC Table Assesed | N/A (quarterly snapshot) | N/A (quarterly snapshot) | 2026-09-28 |
| 21 | Territory Alignment (Target) and Call Targeting Data | PHCDW.PHCDW_TARGETING.CP_KER_HCP | PACE | No Expected Change | UC Table Assesed | 2026-10-01 (call plan start) | 2026-12-31 (call plan end) | 2026-10-16 |
| 22 | Territory Alignment (Non Target) and Specialty Data | PHCDW.PUB.CUST_MDM_BEST_AFFL_PUBLISH_PD_OUTP_STATIC | PACE | No Expected Change | UC Table Assesed | 2025-08-04 (record modified) | 2026-10-13 (record modified) | 2026-10-13 |
| 23 | Territory Alignment (Non Target - Proxy Source) | CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_HCP_BRAND_PRFL_KER_UNIV | Galaxy | Galaxy Table - Confirmation Required | Need a Proxy Source for Territory Alignment of Non Target HCPs | N/A (HCP snapshot) | N/A (HCP snapshot) | 2026-10-18 |
| 24 | SGLT2 GLP1 Product List | Product List Dump (sglt2_glp1_product_list_df.xlsx) | Internal - ZS | No Expected Change | | N/A (file) | N/A (file) | N/A (file) |
| 25 | Specialty Code to Group Mapping | specialty_cd_to_group_mapping_path | Bayer Data Team | No Expected Change | | N/A (file) | N/A (file) | N/A (file) |
| 26 | Product Group Mapping | Product Mapping Dump (Kerendia_Market_Basket_Product_Group_Mapping_and_Priority_v3.xlsx) | Bayer Data Team | pha_lrx_transition_product_mapping | WIP | N/A (file) | N/A (file) | N/A (file) |

# IQVIA Support Tables

## Galaxy Team Support Tables

| # | Galaxy Table | Role | Key Columns | Last Updated |
|---|---|---|---|---|
| 1 | `CPH_DB_PROD.MODEL_V2.FACT_IQV_LAAD_SUB_NATIONAL` | Base NBRx providers (WHERE PROJD_NBRX > 0) | PRVDR_ID | 2026-10-16 |
| 2 | `CPH_DB_PROD.MODEL_V2.FACT_IQV_LAAD_SUB_NATIONAL_XREF` | PROVIDER_ID → NPI cross-reference | PRVDR_ID, NPI | 2026-10-16 |
| 3 | `CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF` | PROVIDER_ID → BH_ID (primary path, WHERE SOURCE_CUST_ID_TYP = 'IQV_LAAD') | SOURCE_CUST_ID → BAYER_CUST_ID | 2026-10-17 |
| 4 | `CPH_DB_PROD.MODEL_V2.DIM_CUSTOMER_HCP` | NPI → BH_ID (fallback path) | NPI_NUM → BAYER_CUST_ID | 2026-10-17 |
| 5 | `CPH_DB_PROD.ANALYTICS.DIM_PRODUCT` | Product Dimensions (MSL Visits) | Used in 32_MSL_Visits_features, 00_Write_Input_Files | 2026-07-11 |
| 6 | `CPH_DB_PROD.MODEL_V2.DIM_APPROVED_DOCUMENT` | iRep Approved Documents | Used in 16_promotional_features_irep | 2026-10-21 |