# Kerendia Data Sources

| S.No | Dataset Name/Use | Table Name | Source | New Table Name (PharmAce) | Data Migration Assessment |
| --- | --- | --- | --- | --- | --- |
| 1 | LAAD - Dx Data | PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX | IQVIA | No Expected Change | |
| 2 | LAAD - Px Data | PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_PX | IQVIA | No Expected Change | |
| 3 | LAAD - Rx Data | PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX | IQVIA | No Expected Change | |
| 4 | LRx Data | PHCDW.PHCDW_DSAA.KERENDIA_LAAD_BASED_LRX_V6 and lrx_nbrx (For T1D)  | ZS | No Expected Change | From where are the new 56K (3.3%) HCPs coming? |
| 5 | Lab Tests | PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_QUEST_TO_LAAD_HIST | IQVIA | No Expected Change | |
| 6 | Copay Program | PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_COPAY_PROGRAM | PACE | To be Decided | |
| 7 | DTC Direct Buy | Before: CPH_DB_PROD.ENRICH_V2.MMX_FLASHTALKING_NEW_DAILYFILES_V1 / After: CPH_DB_PROD.ENRICH.FLASHTALKING_DMA | Galaxy | Galaxy Table - Confirmation Required | |
| 8 | Digital Engagement | PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB | PACE | No Expected Change | |
| 9 | F2F Calls | Current: CPH_DB_PROD.MODEL_V2.FACT_CALL; Suggested: CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CUST_CALL_ACTY | Galaxy | Galaxy Table - Confirmation Required (TBD) |  |
| 10 | FTP Scripts | PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP | PACE | To Be Decided | |
| 11 | Meta-Instagram Ads | FUNNEL_PROD_INB2.FUNNEL_MK7FZ_CN_UWQY_VMROR.FUNNEL_DATA_FACEBOOKADS_GEO | PACE | No Expected Change | |
| 12 | Samples | Current: CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER / Previous: CPH_DB_PROD.ANALYTICS_V2.KERENDIA_SAMPLES, CPH_DB_PROD.ANALYTICS_V2.KERENDIA_SAMPLES_SHIPPED | Galaxy | Galaxy Table - Confirmation Required (To Be Decided) | Used in 17_promotional_features_samples |
| 13 | Speaker Programs | CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM | Galaxy | Galaxy Table - Confirmation Required | |
| 14 | iRep Emails | CPH_DB_PROD.MODEL_V2.FACT_SENT_EMAIL | Galaxy | Galaxy Table - Confirmation Required | |
| 15 | ClickStream Data | CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM | Galaxy | Galaxy Table - Confirmation Required | Used in 18_promotional_ClickStream_features |
| 16 | Drug Formulary History (Deprecated - Replaced by MMIT) | CPH_DB_PROD.ANALYTICS_V2.ANLT_DRG_FRMLRY_HIST | Galaxy | Galaxy Table - Confirmation Required | Used in 2.1/2.2/2.3_DRG_Features (Kerendia, Farxiga, Jardiance) |
| 17 | MSL Visits / MSL Calls | CPH_DB_PROD.MODEL_V2.FACT_CALL / CPH_DB_PROD.ANALYTICS.FACT_CALL | Galaxy | Galaxy Table - Confirmation Required | Used in 32_MSL_Visits_features, 00_Write_Input_Files |
| 18 | Colocation Flag | PHCDW.PHCDW_STG.MDM_STG_HCP_ADDR | IQVIA | Confirmation Required | |
| 19 | Business Positioning Tool | PHCDW.PHCDW_TARGETING.BPT_KER_HCP | PACE | No Expected Change | UC Table Assesed |
| 20 | Territory Alignment (Target) and Call Targeting Data | PHCDW.PHCDW_TARGETING.CP_KER_HCP | PACE | No Expected Change | UC Table Assesed |
| 21 | Territory Alignment (Non Target) and Specialty Data | PHCDW.PUB.CUST_MDM_BEST_AFFL_PUBLISH_PD_OUTP_STATIC | PACE | No Expected Change | UC Table Assesed |
| 22 | Territory Alignment (Non Target - Proxy Source) | CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_HCP_BRAND_PRFL_KER_UNIV | Galaxy | Galaxy Table - Confirmation Required | Need a Proxy Source for Territory Alignment of Non Target HCPs |
| 23 | SGLT2 GLP1 Product List | Product List Dump (sglt2_glp1_product_list_df.xlsx) | Internal - ZS | No Expected Change | |
| 24 | Specialty Code to Group Mapping | specialty_cd_to_group_mapping_path | Bayer Data Team | No Expected Change | |
| 25 | Product Group Mapping | Product Mapping Dump (Kerendia_Market_Basket_Product_Group_Mapping_and_Priority_v3.xlsx) | Bayer Data Team | pha_lrx_transition_product_mapping | WIP |

# IQVIA Support Tables

## Galaxy Team Support Tables

| # | Galaxy Table | Role | Key Columns |
|---|---|---|---|
| 1 | `CPH_DB_PROD.MODEL_V2.FACT_IQV_LAAD_SUB_NATIONAL` | Base NBRx providers (WHERE PROJD_NBRX > 0) | PRVDR_ID |
| 2 | `CPH_DB_PROD.MODEL_V2.FACT_IQV_LAAD_SUB_NATIONAL_XREF` | PROVIDER_ID → NPI cross-reference | PRVDR_ID, NPI |
| 3 | `CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF` | PROVIDER_ID → BH_ID (primary path, WHERE SOURCE_CUST_ID_TYP = 'IQV_LAAD') | SOURCE_CUST_ID → BAYER_CUST_ID |
| 4 | `CPH_DB_PROD.MODEL_V2.DIM_CUSTOMER_HCP` | NPI → BH_ID (fallback path) | NPI_NUM → BAYER_CUST_ID |
| 5 | `CPH_DB_PROD.ANALYTICS.DIM_PRODUCT` | Product Dimensions (MSL Visits) | Used in 32_MSL_Visits_features, 00_Write_Input_Files |
| 6 | `CPH_DB_PROD.MODEL_V2.DIM_APPROVED_DOCUMENT` | iRep Approved Documents | Used in 16_promotional_features_irep |