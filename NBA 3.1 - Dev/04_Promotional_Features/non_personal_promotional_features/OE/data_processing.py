import pandas as pd
import numpy as np

from functools import reduce
from typing import List, Dict
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import col, to_date, date_format, when, lit
from pyspark.sql.window import Window
import re
from src.NBA.utils.utils import content_tagging
from src.NBA.utils.handy_functions import (
    nan_handler,
    standardize_columns,
    convert_to_numeric
)

class Transactions:
    def __init__(self, start_yrmo, end_yrmo, product_key, country, metric_mapping, df_flag_new,df_target,df_tagg, env='dev'):
        """
        Initialize the Transactions with basic parameters
        """
        self.START_YRMO = start_yrmo
        self.END_YRMO = end_yrmo
        self.PRODUCT_KEY = product_key
        self.COUNTRY = country
        self.metric_mapping = metric_mapping
        self.df_flag_new = df_flag_new
        self.env = env
        self.df_target = df_target
        self.df_tagg = df_tagg

        # Initialize Spark session
        self.spark = SparkSession.builder.appName("Sequence Generation").getOrCreate()
        
    def calls_processing(self):
        """Process calls data"""
        # path = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_oe_journey/kerendia_oe_volume/Inference/Promotional_data_ingestion/oe_kerendia_june_fact_call"
        # df = self.spark.read.format("delta").load(path)
        df = self.spark.table("`ph-com-ai-us-prod-catalog-2553213839599380`.kerendia_oe_journey.oe_kerendia_fact_call_inference")
        df = df.filter((col("DETL_PROD")=="Kerendia") & (col("BHID").isNotNull()))

        df = df.join( self.df_target, (df["BHID"] == self.df_target["BH_ID"]), "inner")
        
        PROMO_LAG_DAYS = 7
        start_date_boundary = pd.to_datetime(str(self.START_YRMO), format='%Y%m').date() - pd.Timedelta(days=PROMO_LAG_DAYS)
        end_date_boundary = (pd.to_datetime(str(self.END_YRMO), format='%Y%m') + pd.offsets.MonthEnd(0)).date() - pd.Timedelta(days=PROMO_LAG_DAYS)

        df = (
            df
            .withColumn("EXPOSED_ON", to_date(col("DATE_ID").cast("string"), "yyyyMMdd"))
            .filter(
                col("EXPOSED_ON").between(
                    start_date_boundary,
                    end_date_boundary,
                )
            )
        )
        df = df.withColumn("CONTENT_TAG", F.lit("General"))
        df = df.withColumnsRenamed({
            "BHID": "CUSTOMER_ID",
            "CHNNL_NM": "CHANNEL_ID",
            "DETL_PROD": "PRODUCT_ID",
            "CALL_ID": "INTERACTION_ID"
        })
        df = df.withColumn("ENGAGED_ON", col("EXPOSED_ON")).withColumn("ACTED_ON", col("EXPOSED_ON"))
        df = df.select("CUSTOMER_ID", "CHANNEL_ID", "CONTENT_TAG", "PRODUCT_ID", "INTERACTION_ID", "EXPOSED_ON", "ENGAGED_ON", "ACTED_ON")
        df = df.toPandas()
        return df

    def email_processing(self):
        """Process email data"""
        # path = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_oe_journey/kerendia_oe_volume/Inference/Promotional_data_ingestion/oe_kerendia_june_fact_npp"
        # df = self.spark.read.format("delta").load(path)
        df = self.spark.table("`ph-com-ai-us-prod-catalog-2553213839599380`.kerendia_oe_journey.oe_kerendia_fact_npp_inference")
        df = df.filter((col("PROD_BRAND_NM")=="KERENDIA") & (col("BAYER_HCP_ID").isNotNull()))
        
        PROMO_LAG_DAYS = 7
        start_date_boundary = pd.to_datetime(str(self.START_YRMO), format='%Y%m').date() - pd.Timedelta(days=PROMO_LAG_DAYS)
        end_date_boundary = (pd.to_datetime(str(self.END_YRMO), format='%Y%m') + pd.offsets.MonthEnd(0)).date() - pd.Timedelta(days=PROMO_LAG_DAYS)
        
        
        df = df.join( self.df_target, (df["CUST_ID"] == self.df_target["BH_ID"]), "inner")

        print(df.count())
        df = (
            df
            .withColumn("DATE_ID_DT", to_date(col("DATE_ID").cast("string"), "yyyyMMdd"))
            .filter(
                col("DATE_ID_DT").between(
                    start_date_boundary,
                    end_date_boundary,
                )
            )
        )
        print(df.count())

        # df = df.filter((col("DATE_ID_DT")>=start_date_boundary ) & (col("DATE_ID_DT")<=end_date_boundary))

        df = df.dropDuplicates([
            "UNIQ_NPP_ID",
            "DATE_ID",
            "CUST_ID",
            "VEND_NM",
            "CHNL_NM",
            "MTR_NM"
        ])
        df = df.withColumn("DEVC_VEND_PROD", F.concat_ws("_", F.col("DEVC"), F.col("VEND_PROD")))

        cols = [
            'VEND_NM', 'CHNL_NM', 'MTR_NM', "DEVC_VEND_PROD", "CPGN_NM", "TACT_NM"
        ]
        for c in cols:
            df = df.withColumn(f"{c}_copy", F.col(c))


        merge_cols = [
            'CHNL_NM', 'VEND_NM', 'LITCODE', 'CNTT_NM', 'EMAIL_SUBJ_LN', 'CRTV_NM',
            'TACT_NM', 'CPGN_NM', 'PRMRY_KEY_MSG', 'CF_NAME', 'CF_INDICATION',
            'RPT_CHNL', 'CHNL_TYP', 'TACT_TYP'
        ]
        missing_placeholder = "_"

        def clean_merge_columns_spark(df, cols, missing_placeholder="_"):
            missing_strings = [
                "", " ", "None", "none",
                "NaN", "nan",
                "NULL", "null", "Null",
                "N/A", "n/a", "NA"
            ]

            for col_name in cols:
                df = df.withColumn(
                    col_name,
                    F.col(col_name).cast("string")
                )

                df = df.withColumn(
                    col_name,
                    F.trim(F.col(col_name))
                )

                df = df.withColumn(
                    col_name,
                    F.when(
                        F.col(col_name).isNull() | F.col(col_name).isin(missing_strings),
                        F.lit(missing_placeholder)
                    ).otherwise(F.col(col_name))
                )

                df = df.withColumn(
                    col_name,
                    F.regexp_replace(F.col(col_name), r"[^\w]+", "_")
                )

                df = df.withColumn(
                    col_name,
                    F.regexp_replace(F.col(col_name), r"_+", "_")
                )

                df = df.withColumn(
                    col_name,
                    F.regexp_replace(F.col(col_name), r"^_+|_+$", "")
                )

                df = df.withColumn(
                    col_name,
                    F.when(
                        F.col(col_name).isNull() | (F.col(col_name) == ""),
                        F.lit(missing_placeholder)
                    ).otherwise(F.col(col_name))
                )

            return df

        df = clean_merge_columns_spark(df, merge_cols, missing_placeholder)
        df_tagg = clean_merge_columns_spark(self.df_tagg, merge_cols, missing_placeholder)

        df_tagg = df_tagg.dropDuplicates(merge_cols)

        df = df.join(df_tagg, on=merge_cols, how="left")

        df = df.withColumn(
            "Content Category",
            F.when(
                F.col("Content Category").isin("-", "Not Needed") | F.col("Content Category").isNull(),
                F.lit("General")
            ).otherwise(F.col("Content Category"))
        )

        for c in cols:
            df = df.withColumn(c, F.col(f"{c}_copy"))

        df = df.drop(*[f"{c}_copy" for c in cols])

        df = df.withColumnsRenamed({
            "Content Category": "CONTENT_TAG"
        })

        # === NEW: Derive CHNL_NM_NEW from TACT_NM ===
        _tact = F.upper(F.col('TACT_NM'))
        _prefix = F.upper(F.regexp_extract(F.col('TACT_NM'), r'(?i)(?:KERENDIA|Kerendiafinerenone)_([A-Za-z]+)', 1))

        df = df.withColumn('CHNL_NM_NEW',
            F.when(F.col('VEND_NM') == 'DOXIMITY',
                F.when(_tact.contains('DOCNEWS'), F.lit('DocNews'))
                .when(_tact.contains('DOCSPOT'), F.lit('DocSpot'))
                .when(_tact.contains('DOCPOINT'), F.lit('DocPoint'))
                .when(_tact.contains('FORMULARY'), F.lit('FormularyOne'))
                .when(_tact.contains('ANNOUNCE'), F.lit('Announcement'))
                .when(_tact.rlike(r'\bDN\b'), F.lit('DocNews'))
                .when(_tact.rlike(r'\bF1\b'), F.lit('FormularyOne'))
                .when(_tact.rlike(r'\bAN/F1\b'), F.lit('FormularyOne'))
                .when(_tact.rlike(r'\bAN\b'), F.lit('Announcement'))
            )
            .when(F.col('VEND_NM') == 'MEDSCAPE',
                F.when(_prefix == 'EA',    F.lit('3rd Party Email'))
                .when(_prefix == 'BA',   F.lit('BrandAlert'))
                .when(_prefix == 'BS',   F.lit('BrandSpot'))
                .when(_prefix == 'PP',   F.lit('PulsePoint Banner'))
                .when(_prefix == 'FFQ',  F.lit('FFQ'))
                .when(_prefix == 'RECAP',F.lit('RECAP'))
                .when(_prefix == 'TLM',  F.lit('BANNER'))
                .when(_prefix == 'PPEHR',F.lit('EHR'))
                .when(_prefix == 'FAP',  F.lit('FAP'))
                .when(_prefix == 'DDTRD',F.lit('DDTRD'))
            )
            .when(F.col('VEND_NM') == 'PEERDIRECT',
                F.when(_tact.contains('MDFI - EMAIL'),         F.lit('MDFI - Email'))
                .when(_tact.contains('MDFI - WEB'),          F.lit('MDFI - Web'))
                .when(_tact.contains('MDFI - BANNER'),       F.lit('MDFI - Banner'))
                .when(_tact.contains('MD MINUTE - EMAIL'),   F.lit('MD Minute - Email'))
                .when(_tact.contains('MD MINUTE - WEB'),     F.lit('MD Minute - Web'))
                .when(_tact.contains('MD MINUTE - BANNER'),  F.lit('MD Minute - Banner'))
                .when(_tact.contains('MD SHUFFLE - BANNER'), F.lit('MD Shuffle - Banner'))
                .when(_tact.contains('MD SHUFFLE - WEB'),    F.lit('MD Shuffle - Web'))
                .when(_tact.contains('PV COMPENDIUM'),       F.lit('FFQ'))
            )
            .when(F.col('VEND_NM') == 'SFMC',       F.lit('HQ Email'))
            .when(F.col('VEND_NM') == 'PULSEPOINT', F.lit('Banner'))
        )

        # === NEW: Build flag lookup (MAX agg at 3-col grain, non-null flags only) ===
        _target_vendors = ['DOXIMITY', 'MEDSCAPE', 'SFMC', 'PEERDIRECT', 'PULSEPOINT']
        flag_lookup = (
            self.df_flag_new
            .filter(F.upper(F.col('VEND_NM')).isin(_target_vendors))
            .filter(
                F.col('Exposure Flag').isNotNull() |
                F.col('Engagement Flag').isNotNull() |
                F.col('Acted Flag').isNotNull()
            )
            .groupBy('VEND_NM', 'CHNL_NM_NEW', 'MTR_NM')
            .agg(
                F.max('Exposure Flag').alias('Exposure Flag'),
                F.max('Engagement Flag').alias('Engagement Flag'),
                F.max('Acted Flag').alias('Acted Flag'),
            )
        )

        # === NEW: Join on 3-col key with upper+trim normalization ===
        _join_cols = ['VEND_NM', 'CHNL_NM_NEW', 'MTR_NM']
        df = df.withColumns({f'{c}_JK': F.upper(F.trim(F.col(c))) for c in _join_cols})
        flag_lookup = flag_lookup.withColumns({f'{c}_JK': F.upper(F.trim(F.col(c))) for c in _join_cols})

        _jk = [f'{c}_JK' for c in _join_cols]
        df = df.join(
            flag_lookup.drop('VEND_NM', 'CHNL_NM_NEW', 'MTR_NM'),
            on=_jk, how='left'
        )
        df = df.drop(*_jk)

        # === Filter: keep rows with derived CHNL_NM_NEW and at least one flag matched ===
        df = df.filter(
            F.col('CHNL_NM_NEW').isNotNull() &
            (
                F.col('Exposure Flag').isNotNull() |
                F.col('Engagement Flag').isNotNull() |
                F.col('Acted Flag').isNotNull()
            )
        )
        # df = df.withColumn("Acted Flag", col("Engagement Flag"))
        df = df.na.drop(subset=["UNIQ_NPP_ID"]) # TODO : added newly
        # df = df.withColumn("CONTENT_TAG", F.lit("General"))
        df = df.select(["CUST_ID", "VEND_NM", "CHNL_NM_NEW", 'CONTENT_TAG', 
                        "PROD_BRAND_NM", "UNIQ_NPP_ID", 'Exposure Flag', 'Engagement Flag', 
                        'Acted Flag', "DATE_ID_DT"]).dropDuplicates()
        # df = df.select(["CUST_ID", "VEND_NM", "CHNL_NM_NEW",
        #                 "PROD_BRAND_NM", "UNIQ_NPP_ID", 'Exposure Flag', 'Engagement Flag', 
        #                 'Acted Flag', "DATE_ID_DT"]).dropDuplicates()
        # df = df.withColumn("CONTENT_TAG", F.lit("General"))

        keys = [
            "CUST_ID",
            "VEND_NM",
            "CHNL_NM_NEW",
            "CONTENT_TAG",
            "PROD_BRAND_NM",
            "UNIQ_NPP_ID"
        ]

        # window for sequencing events by date within each key combination
        w = Window.partitionBy(*keys).orderBy("DATE_ID_DT")

        # Exposure events
        exposure_df = (
            df
            .filter(F.col("Exposure Flag") == 1)
            .withColumn("event_seq", F.row_number().over(w))
            .select(*keys, "event_seq", F.col("DATE_ID_DT").alias("EXPOSED_ON"))
        )

        # Engagement events
        engagement_df = (
            df
            .filter(F.col("Engagement Flag") == 1)
            .withColumn("event_seq", F.row_number().over(w))
            .select(*keys, "event_seq", F.col("DATE_ID_DT").alias("ENGAGED_ON"))
        )

        # Action events
        acted_df = (
            df
            .filter(F.col("Acted Flag") == 1)
            .withColumn("event_seq", F.row_number().over(w))
            .select(*keys, "event_seq", F.col("DATE_ID_DT").alias("ACTED_ON"))
        )

        # combine nth exposure with nth engagement with nth action
        result_df = (
            exposure_df
            .join(engagement_df, keys + ["event_seq"], "full_outer")
            .join(acted_df, keys + ["event_seq"], "full_outer")
            .orderBy(*keys, "event_seq")
        )

        result_df = result_df.withColumn(
            "CHANNEL_ID",
            F.concat_ws("_", F.col("VEND_NM"), F.col("CHNL_NM_NEW"))
        )

        result_df = result_df.withColumnsRenamed({
            "CUST_ID": "CUSTOMER_ID",
            "PROD_BRAND_NM": "PRODUCT_ID",
            "CONTENT_TAG": "CONTENT_TAG",
            "UNIQ_NPP_ID": "INTERACTION_ID",
        })
        result_df = result_df.select("CUSTOMER_ID", "CHANNEL_ID", "CONTENT_TAG", "PRODUCT_ID", "INTERACTION_ID", "EXPOSED_ON", "ENGAGED_ON", "ACTED_ON")
        result_df = result_df.dropDuplicates(["CUSTOMER_ID", "CHANNEL_ID", "CONTENT_TAG", "INTERACTION_ID"])
        result_df = result_df.toPandas()
        return result_df
    

    # def email_processing(self):
    #     """Process email data"""
    #     # path = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_oe_journey/kerendia_oe_volume/Inference/Promotional_data_ingestion/oe_kerendia_june_fact_npp"
    #     # df = self.spark.read.format("delta").load(path)
    #     df = self.spark.table("`ph-com-ai-us-prod-catalog-2553213839599380`.kerendia_oe_journey.oe_kerendia_fact_npp_inference")
    #     df = df.filter((col("PROD_BRAND_NM")=="KERENDIA") & (col("BAYER_HCP_ID").isNotNull()))
        
    #     PROMO_LAG_DAYS = 7
    #     start_date_boundary = pd.to_datetime(str(self.START_YRMO), format='%Y%m').date() - pd.Timedelta(days=PROMO_LAG_DAYS)
    #     end_date_boundary = (pd.to_datetime(str(self.END_YRMO), format='%Y%m') + pd.offsets.MonthEnd(0)).date() - pd.Timedelta(days=PROMO_LAG_DAYS)
        
        
    #     df = df.join( self.df_target, (df["CUST_ID"] == self.df_target["BH_ID"]), "inner")

    #     print(df.count())
    #     df = (
    #         df
    #         .withColumn("DATE_ID_DT", to_date(col("DATE_ID").cast("string"), "yyyyMMdd"))
    #         .filter(
    #             col("DATE_ID_DT").between(
    #                 start_date_boundary,
    #                 end_date_boundary,
    #             )
    #         )
    #     )
    #     print(df.count())

    #     # df = df.filter((col("DATE_ID_DT")>=start_date_boundary ) & (col("DATE_ID_DT")<=end_date_boundary))

    #     df = df.dropDuplicates([
    #         "UNIQ_NPP_ID",
    #         "DATE_ID",
    #         "CUST_ID",
    #         "VEND_NM",
    #         "CHNL_NM",
    #         "MTR_NM"
    #     ])
    #     df = df.withColumn("DEVC_VEND_PROD", F.concat_ws("_", F.col("DEVC"), F.col("VEND_PROD")))

    #     cols = [
    #         'VEND_NM', 'CHNL_NM', 'MTR_NM', "DEVC_VEND_PROD", "CPGN_NM", "TACT_NM"
    #     ]
    #     for c in cols:
    #         df = df.withColumn(f"{c}_copy", F.col(c))


    #     merge_cols = [
    #         'CHNL_NM', 'VEND_NM', 'LITCODE', 'CNTT_NM', 'EMAIL_SUBJ_LN', 'CRTV_NM',
    #         'TACT_NM', 'CPGN_NM', 'PRMRY_KEY_MSG', 'CF_NAME', 'CF_INDICATION',
    #         'RPT_CHNL', 'CHNL_TYP', 'TACT_TYP'
    #     ]
    #     missing_placeholder = "_"

    #     def clean_merge_columns_spark(df, cols, missing_placeholder="_"):
    #         missing_strings = [
    #             "", " ", "None", "none",
    #             "NaN", "nan",
    #             "NULL", "null", "Null",
    #             "N/A", "n/a", "NA"
    #         ]

    #         for col_name in cols:
    #             df = df.withColumn(
    #                 col_name,
    #                 F.col(col_name).cast("string")
    #             )

    #             df = df.withColumn(
    #                 col_name,
    #                 F.trim(F.col(col_name))
    #             )

    #             df = df.withColumn(
    #                 col_name,
    #                 F.when(
    #                     F.col(col_name).isNull() | F.col(col_name).isin(missing_strings),
    #                     F.lit(missing_placeholder)
    #                 ).otherwise(F.col(col_name))
    #             )

    #             df = df.withColumn(
    #                 col_name,
    #                 F.regexp_replace(F.col(col_name), r"[^\w]+", "_")
    #             )

    #             df = df.withColumn(
    #                 col_name,
    #                 F.regexp_replace(F.col(col_name), r"_+", "_")
    #             )

    #             df = df.withColumn(
    #                 col_name,
    #                 F.regexp_replace(F.col(col_name), r"^_+|_+$", "")
    #             )

    #             df = df.withColumn(
    #                 col_name,
    #                 F.when(
    #                     F.col(col_name).isNull() | (F.col(col_name) == ""),
    #                     F.lit(missing_placeholder)
    #                 ).otherwise(F.col(col_name))
    #             )

    #         return df

    #     df = clean_merge_columns_spark(df, merge_cols, missing_placeholder)
    #     df_tagg = clean_merge_columns_spark(self.df_tagg, merge_cols, missing_placeholder)

    #     df_tagg = df_tagg.dropDuplicates(merge_cols)

    #     df = df.join(df_tagg, on=merge_cols, how="left")

    #     df = df.withColumn(
    #         "Content Category",
    #         F.when(
    #             F.col("Content Category").isin("-", "Not Needed") | F.col("Content Category").isNull(),
    #             F.lit("General")
    #         ).otherwise(F.col("Content Category"))
    #     )

    #     for c in cols:
    #         df = df.withColumn(c, F.col(f"{c}_copy"))

    #     df = df.drop(*[f"{c}_copy" for c in cols])

    #     df = df.withColumnsRenamed({
    #         "Content Category": "CONTENT_TAG"
    #     })

    #     df = df.fillna("Unknown", subset=["DEVC_VEND_PROD", "CPGN_NM", "TACT_NM"])
    #     flag_new = self.df_flag_new.fillna("Unknown", subset=["DEVC_VEND_PROD", "CPGN_NM", "TACT_NM"])

    #     cols_to_fill = ["DEVC_VEND_PROD", "CPGN_NM", "TACT_NM"]

    #     def replace_blank_with_unknown(df, cols):
    #         for c in cols:
    #             df = df.withColumn(
    #                 c,
    #                 F.when(
    #                     F.col(c).isNull() | (F.trim(F.col(c)) == "") | (F.col(c) == "NA") | (F.col(c) == "unknown_") | 
    #                     (F.col(c) == "_") | (F.col(c) == "Unknown")  | (F.col(c) == "desktop_")  | (F.col(c) == "mobile_")  | (F.col(c) == "tablet_"),
    #                     F.lit("Unknown")
    #                 ).otherwise(F.col(c))
    #             )
    #         return df

    #     df = replace_blank_with_unknown(df, cols_to_fill)
    #     flag_new = replace_blank_with_unknown(flag_new, cols_to_fill)

    #     cols = [
    #         'VEND_NM', 'CHNL_NM', 'MTR_NM', "DEVC_VEND_PROD", "CPGN_NM", "TACT_NM"
    #     ]
    #     df = df.join(flag_new.select('VEND_NM', 'CHNL_NM', 'MTR_NM',"DEVC_VEND_PROD", 'CHNL_NM_NEW', "CPGN_NM", "TACT_NM",  'Exposure Flag', 'Engagement Flag', 'Acted Flag', 'PP_NPP_Flag'), on=cols, how="left")

    #     df = df.fillna("Unknown", subset=['VEND_NM', 'CHNL_NM', 'MTR_NM',"DEVC_VEND_PROD", "CPGN_NM","TACT_NM",'CHNL_NM_NEW', 'Exposure Flag','Engagement Flag', 'Acted Flag', 'PP_NPP_Flag'])

    #     df = df.filter(
    #         col("PP_NPP_Flag").isNotNull() &
    #         col("CHNL_NM_NEW").isNotNull() &
    #         (col("PP_NPP_Flag") != "Unknown") &
    #         (col("CHNL_NM_NEW") != "Unknown")
    #     )
    #     # df = df.withColumn("Acted Flag", col("Engagement Flag"))
    #     df = df.na.drop(subset=["UNIQ_NPP_ID"]) # TODO : added newly
    #     # df = df.withColumn("CONTENT_TAG", F.lit("General"))
    #     df = df.select(["CUST_ID", "VEND_NM", "CHNL_NM_NEW", 'CONTENT_TAG', 
    #                     "PROD_BRAND_NM", "UNIQ_NPP_ID", 'Exposure Flag', 'Engagement Flag', 
    #                     'Acted Flag', "DATE_ID_DT"]).dropDuplicates()
    #     # df = df.select(["CUST_ID", "VEND_NM", "CHNL_NM_NEW",
    #     #                 "PROD_BRAND_NM", "UNIQ_NPP_ID", 'Exposure Flag', 'Engagement Flag', 
    #     #                 'Acted Flag', "DATE_ID_DT"]).dropDuplicates()
    #     # df = df.withColumn("CONTENT_TAG", F.lit("General"))

    #     keys = [
    #         "CUST_ID",
    #         "VEND_NM",
    #         "CHNL_NM_NEW",
    #         "CONTENT_TAG",
    #         "PROD_BRAND_NM",
    #         "UNIQ_NPP_ID"
    #     ]

    #     # window for sequencing events by date within each key combination
    #     w = Window.partitionBy(*keys).orderBy("DATE_ID_DT")

    #     # Exposure events
    #     exposure_df = (
    #         df
    #         .filter(F.col("Exposure Flag") == 1)
    #         .withColumn("event_seq", F.row_number().over(w))
    #         .select(*keys, "event_seq", F.col("DATE_ID_DT").alias("EXPOSED_ON"))
    #     )

    #     # Engagement events
    #     engagement_df = (
    #         df
    #         .filter(F.col("Engagement Flag") == 1)
    #         .withColumn("event_seq", F.row_number().over(w))
    #         .select(*keys, "event_seq", F.col("DATE_ID_DT").alias("ENGAGED_ON"))
    #     )

    #     # Action events
    #     acted_df = (
    #         df
    #         .filter(F.col("Acted Flag") == 1)
    #         .withColumn("event_seq", F.row_number().over(w))
    #         .select(*keys, "event_seq", F.col("DATE_ID_DT").alias("ACTED_ON"))
    #     )

    #     # combine nth exposure with nth engagement with nth action
    #     result_df = (
    #         exposure_df
    #         .join(engagement_df, keys + ["event_seq"], "full_outer")
    #         .join(acted_df, keys + ["event_seq"], "full_outer")
    #         .orderBy(*keys, "event_seq")
    #     )

    #     # df = (
    #     #     df
    #     #     .withColumn(
    #     #         "EXPOSED_ON",
    #     #         F.when(F.col("Exposure Flag") == 1, F.col("DATE_ID_DT"))
    #     #     )
    #     #     .withColumn(
    #     #         "ENGAGED_ON",
    #     #         F.when(F.col("Engagement Flag") == 1, F.col("DATE_ID_DT"))
    #     #     )
    #     #     .withColumn(
    #     #         "ACTED_ON",
    #     #         F.when(F.col("Acted Flag") == 1, F.col("DATE_ID_DT"))
    #     #     )
    #     #     .groupBy(
    #     #         "CUST_ID",
    #     #         "VEND_NM",
    #     #         "CHNL_NM_NEW",
    #     #         "CONTENT_TAG",
    #     #         "PROD_BRAND_NM",
    #     #         "UNIQ_NPP_ID"
    #     #     )
    #     #     .agg(
    #     #         F.min("EXPOSED_ON").alias("EXPOSED_ON"),
    #     #         F.min("ENGAGED_ON").alias("ENGAGED_ON"),
    #     #         F.min("ACTED_ON").alias("ACTED_ON")
    #     #     )
    #     # )

    #     result_df = result_df.withColumn(
    #         "CHANNEL_ID",
    #         F.concat_ws("_", F.col("VEND_NM"), F.col("CHNL_NM_NEW"))
    #     )

    #     result_df = result_df.withColumnsRenamed({
    #         "CUST_ID": "CUSTOMER_ID",
    #         "PROD_BRAND_NM": "PRODUCT_ID",
    #         "CONTENT_TAG": "CONTENT_TAG",
    #         "UNIQ_NPP_ID": "INTERACTION_ID",
    #     })
    #     result_df = result_df.select("CUSTOMER_ID", "CHANNEL_ID", "CONTENT_TAG", "PRODUCT_ID", "INTERACTION_ID", "EXPOSED_ON", "ENGAGED_ON", "ACTED_ON")
    #     result_df = result_df.dropDuplicates(["CUSTOMER_ID", "CHANNEL_ID", "CONTENT_TAG", "INTERACTION_ID"])
    #     result_df = result_df.toPandas()
    #     return result_df

    def pp_processing(self):
        """Process event data"""
        # path = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_oe_journey/kerendia_oe_volume/Inference/Promotional_data_ingestion/oe_kerendia_june_fact_evnt_prsnl_prom"
        # df = self.spark.read.format("delta").load(path)

        df = self.spark.table("`ph-com-ai-us-prod-catalog-2553213839599380`.kerendia_oe_journey.oe_kerendia_fact_evnt_prsnl_prom_inference")
        df = df.filter((col("PROD_BRAND_NM")=="KERENDIA") & (col("CUST_HCP_ID").isNotNull()))

        df = df.join( self.df_target, (df["CUST_HCP_ID"] == self.df_target["BH_ID"]), "inner")
        df = df.dropDuplicates([
            "EVNT_ID",
            "DATE_ID",
            "CUST_HCP_ID",
            "EVNT_CAT",
            "EVNT_TYP",
            "EVNT_SUB_TYP",
            "ATND"
        ])

        df = df.withColumnsRenamed({
            "CUST_HCP_ID": "CUSTOMER_ID",
            "EVNT_TYP": "CHANNEL_ID",   # EVNT_CAT
            "PROD_BRAND_NM": "PRODUCT_ID",
            "EVNT_ID": "INTERACTION_ID"
        })

        df = df.withColumn("CONTENT_TAG", F.lit("General"))

        PROMO_LAG_DAYS = 7
        start_date_boundary = pd.to_datetime(str(self.START_YRMO), format='%Y%m').date() - pd.Timedelta(days=PROMO_LAG_DAYS)
        end_date_boundary = (pd.to_datetime(str(self.END_YRMO), format='%Y%m') + pd.offsets.MonthEnd(0)).date() - pd.Timedelta(days=PROMO_LAG_DAYS)

        df = (
            df
            .withColumn("EXPOSED_ON", to_date(col("DATE_ID").cast("string"), "yyyyMMdd"))
            .filter(
                col("EXPOSED_ON").between(
                    start_date_boundary,
                    end_date_boundary,
                )
            )
        )
        df = df.withColumn("ENGAGED_ON", col("EXPOSED_ON")).withColumn("ACTED_ON", col("EXPOSED_ON"))
        df = df.select("CUSTOMER_ID", "CHANNEL_ID", "CONTENT_TAG", "PRODUCT_ID", "INTERACTION_ID", "EXPOSED_ON", "ENGAGED_ON", "ACTED_ON")
        df = df.toPandas()
        return df    

    def get_transaction_idc(self):

        PROMO_LAG_DAYS = 7

        """Get and process all transaction data"""
        calls_idc = self.calls_processing()
        emails_idc = self.email_processing()
        events_idc = self.pp_processing()
        
        proto_idc = pd.concat([calls_idc, emails_idc,events_idc])

        # proto_idc.to_parquet("/Workspace/Users/wenjie.chen@bayer.com/OE/nba_model_run/test_file/proto_idc_22_04.parquet")
        
        for column in ['EXPOSED_ON', 'ENGAGED_ON', 'ACTED_ON']:
            proto_idc.loc[:, column] = proto_idc[column].astype(str)
            proto_idc.loc[:, 'RAW_'+column] = proto_idc[column]
            proto_idc.loc[:, column] = pd.to_datetime(proto_idc[column], errors='coerce').dt.date
        

        #TODO Updated 7 Days lag
        
        start_date_boundary = pd.to_datetime(str(self.START_YRMO), format='%Y%m').date() - pd.Timedelta(days=PROMO_LAG_DAYS)
        end_date_boundary = (pd.to_datetime(str(self.END_YRMO), format='%Y%m') + pd.offsets.MonthEnd(0)).date() - pd.Timedelta(days=PROMO_LAG_DAYS)

        proto_idc = proto_idc[
            (proto_idc['EXPOSED_ON'] >= start_date_boundary) &
            (proto_idc['EXPOSED_ON'] <= end_date_boundary)
        ].copy(deep=True)

        for column in ['EXPOSED_ON', 'ENGAGED_ON', 'ACTED_ON']:
            proto_idc[column] = (
                pd.to_datetime(proto_idc[column]) + pd.Timedelta(days=PROMO_LAG_DAYS)
            ).dt.date


        proto_idc['YRMO'] = pd.to_datetime(proto_idc['EXPOSED_ON']).dt.strftime("%Y%m")
        proto_idc['YRMO'] = pd.to_numeric(proto_idc['YRMO'])
        proto_idc = proto_idc[(proto_idc.YRMO >= self.START_YRMO) & (proto_idc.YRMO <= self.END_YRMO)].copy(deep=True)
        
        proto_idc = proto_idc[[
            'CUSTOMER_ID', 'PRODUCT_ID', 'CHANNEL_ID', 'CONTENT_TAG',
            'EXPOSED_ON', 'ACTED_ON', 'ENGAGED_ON', 'INTERACTION_ID', 'YRMO'
        ]].drop_duplicates()
        proto_idc['COUNT'] = 1
        proto_idc = standardize_columns(proto_idc, ['CHANNEL_ID', 'CONTENT_TAG'])
        
        rules = {
            'drop': ["CUSTOMER_ID", "EXPOSED_ON", "CHANNEL_ID"],
            'fill': {
                1: ['COUNT'],
                'NO_ID': ['INTERACTION_ID'],
                'GENERAL': ['CONTENT_TAG'],
                pd.to_datetime(0): ['ACTED_ON', 'ENGAGED_ON']
            }
        }
        
        proto_idc = nan_handler(proto_idc, rules=rules)
        proto_idc = convert_to_numeric(proto_idc, 'COUNT')
        proto_idc = standardize_columns(proto_idc, ['CHANNEL_ID'])
        proto_idc['CONTENT_TAG'] = proto_idc['CONTENT_TAG'].replace(['NONE', None, np.nan, 'NAN', '', ' ','OTHERS'], 'GENERAL')
        
        proto_idc = proto_idc[(proto_idc.YRMO >= self.START_YRMO) & (proto_idc.YRMO <= self.END_YRMO)].copy(deep=True)
        
        print(f"Idc3 file shape:{proto_idc.shape}")
        proto_idc = proto_idc.copy()

        text_cols = ['CUSTOMER_ID', 'INTERACTION_ID', 'CHANNEL_ID', 'CONTENT_TAG']
        for c in text_cols:
            proto_idc[c] = proto_idc[c].astype(str)
            
        date_cols = ['EXPOSED_ON', 'ACTED_ON', 'ENGAGED_ON']
        for c in date_cols:
            proto_idc[c] = pd.to_datetime(proto_idc[c], errors='coerce')

        sort_cols = [
            'CUSTOMER_ID', 'INTERACTION_ID', 'CHANNEL_ID', 'CONTENT_TAG',
            'EXPOSED_ON', 'ACTED_ON', 'ENGAGED_ON'
        ]

        proto_idc = (
            proto_idc
            .sort_values(sort_cols, ascending=True)
            .groupby(['CUSTOMER_ID', 'INTERACTION_ID', 'CHANNEL_ID', 'EXPOSED_ON'], as_index=False)
            .head(1)
        )

        proto_idc = proto_idc[
            ['CUSTOMER_ID', 'PRODUCT_ID', 'CHANNEL_ID', 'CONTENT_TAG',
            'EXPOSED_ON', 'ACTED_ON', 'ENGAGED_ON', 'INTERACTION_ID',
            'YRMO', 'COUNT']
        ]

        #TODO: temp change, remove it
        # mask = proto_idc["CHANNEL_ID"].str.contains("BANNER", case=False, na=False)
        # proto_idc.loc[mask, "EXPOSED_ON"] = proto_idc.loc[mask, "ENGAGED_ON"]
        # proto_idc = proto_idc[proto_idc["EXPOSED_ON"].notna()]

        # final_mdb_spark = self.spark.createDataFrame(proto_idc)

        # final_mdb_spark.write.format("delta") \
        # .mode("overwrite") \
        # .option("overwriteSchema", "true") \
        # .save("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/oe_journey/oe_volume_space/notebook_output/final_idc_sequence_original")

        # proto_idc.to_parquet("/Workspace/Users/wenjie.chen@bayer.com/OE/GA Run/Data/final_idc_sequence_eda.parquet")
        return proto_idc

    def process_counts(self, prod_idc, metric_type, channel_col='CHANNEL_ID'):
        """Process counts based on metric type"""
        channels = self.metric_mapping[metric_type].keys()
        idc_counts = prod_idc[prod_idc[channel_col].isin(channels)]
        idc_counts = idc_counts[(idc_counts.YRMO >= self.START_YRMO) & (idc_counts.YRMO <= self.END_YRMO)]
        
        if metric_type == 'R':
            idc_counts['EXPOSED_ON'] = pd.to_datetime(idc_counts['EXPOSED_ON'], errors='coerce')
            idc_counts['YRMO'] = idc_counts.EXPOSED_ON.dt.strftime('%Y%m')
        elif metric_type == 'I':
            idc_counts['ENGAGED_ON'] = pd.to_datetime(idc_counts['ENGAGED_ON'], errors='coerce')
            idc_counts['YRMO'] = idc_counts.ENGAGED_ON.dt.strftime('%Y%m')
        elif metric_type == 'E':
            idc_counts['ACTED_ON'] = pd.to_datetime(idc_counts['ACTED_ON'], errors='coerce')
            idc_counts['YRMO'] = idc_counts.ACTED_ON.dt.strftime('%Y%m')
        
        a = idc_counts[['CUSTOMER_ID', f'{channel_col}', 'YRMO', 'COUNT']].groupby(
            ['CUSTOMER_ID', 'YRMO', f'{channel_col}']
        ).COUNT.sum().to_frame('COUNT').reset_index()
        
        eng_counts = pd.pivot_table(
            a,
            values='COUNT',
            index=['CUSTOMER_ID', 'YRMO'],
            columns=f'{channel_col}',
            aggfunc=sum,
            fill_value=0
        )
        
        eng_counts.columns = [
            channel + '_' + self.metric_mapping[metric_type][channel] + '_' + metric_type
            for channel in eng_counts.columns.to_list()
        ]
        eng_counts = eng_counts.reset_index()
        return eng_counts

    def content_counts(self, transactions):
        """Process content counts"""
        idc_counts = transactions.copy()
        idc_counts = idc_counts[(idc_counts.YRMO >= self.START_YRMO) & (idc_counts.YRMO <= self.END_YRMO)]
        idc_counts['EXPOSED_ON'] = pd.to_datetime(idc_counts['EXPOSED_ON'], errors='coerce')
        idc_counts['YRMO'] = idc_counts.EXPOSED_ON.dt.strftime('%Y%m')
        
        a = idc_counts[['CUSTOMER_ID', 'CONTENT_TAG', 'YRMO', 'COUNT']].groupby(
            ['CUSTOMER_ID', 'YRMO', 'CONTENT_TAG']
        ).COUNT.sum().to_frame('COUNT').reset_index()
        
        eng_counts = pd.pivot_table(
            a,
            values='COUNT',
            index=['CUSTOMER_ID', 'YRMO'],
            columns='CONTENT_TAG',
            aggfunc=sum,
            fill_value=0
        )
        
        eng_counts.columns = [channel + '_COUNT' for channel in eng_counts.columns.to_list()]
        eng_counts = eng_counts.reset_index()
        return eng_counts

    def get_counts(self, transactions=None):
        if transactions is None:
            transactions = self.get_transaction_idc()
        transactions['CONTENT_TAG'] = transactions['CONTENT_TAG'].replace(
            [
                'NONE', None, np.nan, 'NAN', ''
            ], 'GENERAL'
        )
        
        count_dfs = [
            self.process_counts(transactions, 'R'),
            self.process_counts(transactions, 'I'),
            self.process_counts(transactions, 'E'),
            self.content_counts(transactions),
        ]
        
        cnts = reduce(
            lambda x, y: pd.merge(x, y, on=['CUSTOMER_ID', 'YRMO'], how='outer', validate= 'one_to_one'),
            count_dfs
        ).fillna(0)
        cnts.YRMO = cnts.YRMO.astype('Int64')


        return cnts

class SequenceProcessor:
    def __init__(self):
        self.channel_encodings = None
        self.content_encodings = None
        self.channel_encodings_dict = {}
        self.content_encodings_dict = {}

    def preprocess_activity_data(self, 
                               idc: pd.DataFrame,
                               content_rename: Dict = None) -> pd.DataFrame:
        """
        Preprocesses the activity data with optimized operations
        """

        # #TODO: new added
        mask = idc["CHANNEL_ID"].str.contains("BANNER", case=False, na=False)
        idc.loc[mask, "EXPOSED_ON"] = idc.loc[mask, "ENGAGED_ON"]
        idc = idc[idc["EXPOSED_ON"].notna()]


        # Optimize data types
        activity_data = idc.astype({
            'CUSTOMER_ID': str,
            'YRMO': int
        }).rename(columns={'CONTENT_TAG': 'CONTENT_CATEGORY'})

        # Select required columns using efficient indexing
        activity_data = activity_data[[
            'CUSTOMER_ID', 'EXPOSED_ON', 'CHANNEL_ID',
            'CONTENT_CATEGORY', 'COUNT', 'YRMO',
            'PRODUCT_ID', 'INTERACTION_ID'
        ]].copy()

        # Uppercase conversion
        activity_data.loc[:, 'CONTENT_CATEGORY'] = activity_data['CONTENT_CATEGORY'].str.upper()
        # Channel priority processing
        # channel_priority = (pep.sort_values('PRIORITIZATION_SCORE', ascending=True)
        #                   .drop_duplicates('DIMENSION1', keep='first')
        #                   [['DIMENSION1', 'PRIORITIZATION_SCORE']]
        #                   .rename(columns={'DIMENSION1': 'CHANNEL_ID'}))
        # Merge and sort operations
        # activity_data = (
        #     pd.merge(
        #         activity_data,
        #         channel_priority, 
        #         on=['CHANNEL_ID'],
        #         how='left',
        #         validate='many_to_many'
        #     ).sort_values(['CUSTOMER_ID', 'EXPOSED_ON', 'PRIORITIZATION_SCORE']).drop_duplicates(subset=['CUSTOMER_ID', 'EXPOSED_ON', 'CHANNEL_ID', 'INTERACTION_ID'], keep='first'))

        # Content renaming if provided
        # if content_rename:
        #     activity_data['CONTENT_CATEGORY'].replace(content_rename, inplace=True)
        # Channel product creation and cleanup
        activity_data['CHANNEL_PRODUCT'] = (activity_data['CHANNEL_ID'].astype(str) + 
                                          '&' + activity_data['PRODUCT_ID'].astype(str))
        activity_data = activity_data.drop('CHANNEL_ID', axis=1)
        return activity_data

    def create_encodings(self, activity_data: pd.DataFrame) -> None:
        """
        Creates channel and content encodings with vectorized operations
        """
        channel_list = sorted(list(activity_data['CHANNEL_PRODUCT'].unique()))
        total_contents = sorted(activity_data['CONTENT_CATEGORY'].unique())
        # Create encodings using vectorized operations
        self.channel_encodings = pd.DataFrame({
            'CHANNEL_ID': channel_list + ['ZG', 'LG', 'MG', 'HG'],
            'CHANNEL_CODE': range(1, len(channel_list) + 5)
        })

        self.content_encodings = pd.DataFrame({
            'CONTENT_CATEGORY': total_contents + ['ZG', 'LG', 'MG', 'HG'],
            'CONTENT_CODE': range(1, len(total_contents) + 5)
        })

        # Create dictionaries for faster lookups
        self.channel_encodings_dict = dict(zip(
            self.channel_encodings['CHANNEL_ID'].str.upper(),
            self.channel_encodings['CHANNEL_CODE']
        ))

        self.content_encodings_dict = dict(zip(
            self.content_encodings['CONTENT_CATEGORY'],
            self.content_encodings['CONTENT_CODE']
        ))

    @staticmethod
    def convert_seq(seq: List) -> List:
        """
        Converts sequence to Gap Group sequence using vectorized operations
        """        
        # Convert input list to numpy array for vectorized operations
        arr = np.array(seq)
        
        # Find indices of non-GAP elements using np.nonzero instead of np.where
        non_gap_indices = np.nonzero(arr != "GAP")[0]
        
        if len(non_gap_indices) == 0:
            return []  # Handle case with only GAPs
        
        # Calculate consecutive GAPs before each non-GAP element
        gap_counts = np.zeros_like(non_gap_indices)
        if non_gap_indices[0] > 0:
            gap_counts[0] = non_gap_indices[0]
        
        for i in range(1, len(non_gap_indices)):
            gap_counts[i] = non_gap_indices[i] - non_gap_indices[i-1] - 1
        
        # Use np.select to determine gap types
        conditions = [
            (gap_counts >= 0) & (gap_counts <= 3),
            (gap_counts >= 4) & (gap_counts <= 10),
            (gap_counts >= 11) & (gap_counts <= 17),
            (gap_counts > 17)
        ]
        
        choices = ["ZG", "LG", "MG", "HG"]
        gap_types = np.select(conditions, choices, default="ZG")
        
        # Build the output list
        seq_out = []
        for i in range(len(non_gap_indices)):
            seq_out.append(gap_types[i])
            seq_out.append(arr[non_gap_indices[i]])
        
        return seq_out

    def generate_gap_sequences(self, df_final: pd.DataFrame) -> pd.DataFrame:
        """
        Generates Gap group sequences using vectorized operations
        """
        gap_grp = pd.DataFrame()
        # Generate channel sequences
        channel_seqs = df_final['full_channelName_seq'].apply(self.convert_seq)
        gap_grp['full_channelName_seq_GAP_grp'] = channel_seqs
        gap_grp['full_channelCode_seq_GAP_grp'] = channel_seqs.apply(
            lambda x: [self.channel_encodings_dict[i] for i in x]
        )
        # Generate content sequences
        content_seqs = df_final['full_contentName_seq'].apply(self.convert_seq)
        gap_grp['full_contentName_seq_GAP_grp'] = content_seqs
        gap_grp['full_contentCode_seq_GAP_grp'] = content_seqs.apply(
            lambda x: [self.content_encodings_dict[i] for i in x]
        )
        return gap_grp

    def process_sequences(self, 
                         idc: pd.DataFrame,
                         seq_gen_obj: object,
                         start_date: str,
                         end_date: str,
                         content_rename: Dict = None) -> pd.DataFrame:

        """
        Main method to process all sequences
        """
        # Preprocess activity data
        activity_data = self.preprocess_activity_data(idc, content_rename)
        # Create encodings
        self.create_encodings(activity_data)
        # Merge encodings
        activity_data = pd.merge(
            activity_data, 
            self.channel_encodings,
            left_on='CHANNEL_PRODUCT',
            right_on='CHANNEL_ID',
            how='left',
            validate='many_to_many'
        ).merge(
            self.content_encodings,
            on='CONTENT_CATEGORY',
            how='left',
            validate='many_to_many'
        )

        # Select final columns

        activity_data = activity_data[[
            'CUSTOMER_ID', 'PRODUCT_ID', 'CHANNEL_PRODUCT', 'CHANNEL_CODE',
            'CONTENT_CATEGORY', 'CONTENT_CODE', 'COUNT', 'EXPOSED_ON', 'YRMO'
        ]]

        # Process timeframes
        p3 = list(activity_data.YRMO.nsmallest(3))
        c3 = list(activity_data.YRMO.nlargest(3))
        activity_data['TimeFrame'] = np.select(
            [activity_data['YRMO'].isin(p3), activity_data['YRMO'].isin(c3)],
            ['P3', 'C3'],
            default='0'
        )

        # Convert dates
        activity_data['EXPOSED_ON'] = pd.to_datetime(activity_data.EXPOSED_ON)

        # Generate sequences
        sequence_data = seq_gen_obj.journey_rollup(
            activity_data=activity_data,
            start_date=start_date,
            end_date=end_date
        )
        # Rename columns
        sequence_data.columns = [
            'CUSTOMER_ID', 'full_channelName_seq', 'full_channelCode_seq',
            'channelName_seq', 'channelCode_seq', 'full_contentName_seq',
            'full_contentCode_seq', 'contentName_seq', 'contentCode_seq', 'timeSeq'
        ]
        # Generate counts
        channel_list = list(activity_data['CHANNEL_PRODUCT'].unique())
        content_list = list(activity_data['CONTENT_CATEGORY'].unique())
        channel_counts = seq_gen_obj.channel_count(
            master_data=sequence_data,
            event_name="channelName_seq",
            channel_list=channel_list
        )
        content_counts = seq_gen_obj.content_count(
            master_data=sequence_data,
            event_name="channelName_seq",
            content_list=content_list
        )
        # Merge all dataframes
        final_df = reduce(
            lambda left, right: pd.merge(left, right, on=['CUSTOMER_ID'], how='inner', validate='one_to_one'),
            [sequence_data, channel_counts, content_counts]
        )


        # Generate gap sequences
        gap_sequences = self.generate_gap_sequences(sequence_data)
        # Final merge
        return pd.concat([final_df, gap_sequences], axis=1)