import os
import sys
import pandas as pd
import numpy as np
import tempfile
# sys.path.append("../../")
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.NBA.utils.handy_functions import standardize_columns
from src.NBA.utils.data_processing import Transactions, SequenceProcessor
from src.NBA.utils.utils import create_experience_bucket, create_age_bucket, get_highest_priority
from src.NBA.utils.Sequence_Generation_Engine import zs_pa_dataprep as seq_gen
from datetime import datetime, date
from src.NBA.utility.setup_cluster import run_setup
run_setup()
import re
from src.NBA.utility.utils import save_file, save_to_s3, get_logger, close_logger_and_save
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import col, to_date, date_format, when, lit
from pyspark.sql.types import StringType, NumericType
from pyspark.sql.functions import col, upper

from importlib import reload
import logging
import io
reload(logging)

argument_list = sys.argv[1:]
log_file_path = argument_list[0]
env = argument_list[1]  # env can be dev, tst or prd passed from databricks job's input parameter


# Initialize logger
logger, log_buffer, log_path = get_logger(log_file_path, "data_processing")
logger.info("Logger initialized successfully.")

SPARK = SparkSession.builder.appName("Sequence Generation").getOrCreate()
P3_LAG_MONTH = 1

def get_cvi_dataset(env, spark, df_target):

    # path = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/oe_journey/oe_volume_space/query_output/oe_bayer_modeling_nbrx_may_26"
    # df = spark.read.format("delta").load(path)

    # path = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/oe_journey/oe_volume_space/blink_kerendia_nbrx_rj_rv_pd_may_26"
    # df_blinkrx = spark.read.format("parquet").load(path)

    # trx_path = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/oe_journey/oe_volume_space/notebook_output/nba_oe_pd_rj_rv_trx_may_26"
    # df_trx = spark.read.format("delta").load(trx_path)

    df = spark.table("`ph-com-ai-us-prod-catalog-2553213839599380`.kerendia_oe_journey.oe_bayer_modeling_nbrx_final_inference")
    df_blinkrx = spark.table("`ph-com-ai-us-prod-catalog-2553213839599380`.kerendia_oe_journey.blink_kerendia_nbrx_rj_rv_pd_inference")
    df_trx = spark.table("`ph-com-ai-us-prod-catalog-2553213839599380`.kerendia_oe_journey.nba_oe_pd_rj_rv_trx_inference")

    df_blinkrx = (
        df_blinkrx
        .groupBy("BH_ID", "month")
        .pivot("COVERAGE_CODE")
        .agg(F.sum("NBRx"))
        .fillna(0)
    )

    df_blinkrx = df_blinkrx.withColumn(
        "Total_Blinkrx",
        F.col("ABANDON") + F.col("P") + F.col("R")
    )

    df_blinkrx = df_blinkrx.withColumnRenamed("month", "SVC_MONTH")

    df_blinkrx = df_blinkrx.select(['BH_ID', 'SVC_MONTH', 'Total_Blinkrx'])

    df = df.join(df_blinkrx, on=["BH_ID","SVC_MONTH"], how="left")
    # df = df.withColumn(
    #     "TOTAL_NBRX",
    #     F.col("TOTAL_NBRX") + F.col("Total_Blinkrx")
    # )

    df = df.withColumn(
        "TOTAL_NBRX",
        F.coalesce(F.col("TOTAL_NBRX"), F.lit(0)) +
        F.coalesce(F.col("Total_Blinkrx"), F.lit(0))
    )

    df = df.select("BH_ID", "SVC_MONTH", "TOTAL_NBRX")


    df_trx = (
        df_trx
        .groupBy("BH_ID", "SVC_MONTH")
        .agg(
            F.sum(F.coalesce(F.col("TOTAL_TRX"), F.lit(0))).alias("TOTAL_TRX"),
            F.sum(F.coalesce(F.col("PD_TRX"),    F.lit(0))).alias("PD_TRX"),
        )
    )
    df = df.join(df_trx, on=["BH_ID", "SVC_MONTH"], how="outer")
    df = df.withColumn("TOTAL_NBRX", F.coalesce(F.col("TOTAL_NBRX"), F.lit(0)))
    df = df.withColumn("TOTAL_TRX",  F.coalesce(F.col("TOTAL_TRX"),  F.lit(0)))
    df = df.withColumn("PD_TRX",     F.coalesce(F.col("PD_TRX"),     F.lit(0)))

    df = df.select("BH_ID", "SVC_MONTH", "TOTAL_NBRX", "TOTAL_TRX", "PD_TRX")



    df = df.join( df_target, on='BH_ID', how="inner")
    df = df.toPandas()

    df['SVC_MONTH_DT'] = pd.to_datetime(df['SVC_MONTH']).dt.to_period('M').dt.to_timestamp()
    df = df.rename(columns={'BH_ID': 'CUSTOMER_ID'})

    df = (
        df.groupby(['CUSTOMER_ID', 'SVC_MONTH_DT'], as_index=False)
        .agg(TOTAL_NBRX=('TOTAL_NBRX', 'sum'),
               TOTAL_TRX =('TOTAL_TRX',  'sum'),
               PD_TRX    =('PD_TRX',     'sum'))
    )

    if df.empty:
        return pd.DataFrame(columns=['CUSTOMER_ID', 'SVC_YRMO',
                                    'TOTAL_NBRX_C3', 'TOTAL_NBRX_P3',
                                    'TOTAL_TRX_C3',  'TOTAL_TRX_P3',
                                    'PD_TRX_C3',     'PD_TRX_P3',])

    full_months = pd.date_range(df['SVC_MONTH_DT'].min(),
                                df['SVC_MONTH_DT'].max(), freq='MS')
    customers = df['CUSTOMER_ID'].unique()
    grid = pd.MultiIndex.from_product(
        [customers, full_months], names=['CUSTOMER_ID', 'SVC_MONTH_DT']
    ).to_frame(index=False)

    df = grid.merge(df, on=['CUSTOMER_ID', 'SVC_MONTH_DT'], how='left')
    for m in ['TOTAL_NBRX', 'TOTAL_TRX', 'PD_TRX']:
        df[m] = df[m].fillna(0)
    df = df.sort_values(['CUSTOMER_ID', 'SVC_MONTH_DT']).reset_index(drop=True)

    # Current month's NBRx (name kept for downstream compatibility)
    df['TOTAL_NBRX_C3'] = df['TOTAL_NBRX']
    df['TOTAL_TRX_C3']  = df['TOTAL_TRX']
    df['PD_TRX_C3']     = df['PD_TRX']


    # P3 column: NBRx from 3 calendar months ago, per customer.
    # When the consumer sums this over a 3-month C3 window, it yields P3 (the 3 months before C3).
    g = df.groupby('CUSTOMER_ID')
    df['TOTAL_NBRX_P3'] = g['TOTAL_NBRX'].shift(3 + P3_LAG_MONTH).fillna(0)
    df['TOTAL_TRX_P3']  = g['TOTAL_TRX'].shift(3 + P3_LAG_MONTH).fillna(0)
    df['PD_TRX_P3']     = g['PD_TRX'].shift(3 + P3_LAG_MONTH).fillna(0)

    df['SVC_YRMO'] = df['SVC_MONTH_DT'].dt.strftime('%Y%m').astype('Int64')
    df = df[[
        'CUSTOMER_ID', 'SVC_YRMO',
        'TOTAL_NBRX_C3', 'TOTAL_NBRX_P3',
        'TOTAL_TRX_C3',  'TOTAL_TRX_P3',
        'PD_TRX_C3',     'PD_TRX_P3',
    ]]

    return df

def demog_processing(demog:pd.DataFrame, df_target = None, **kwargs):
    demog = demog.join(df_target, on="BH_ID", how="inner")
    demog = demog.select(
        "BH_ID",
        "HCP_SPECIALTY",
        "HCP_MEDICAL_DEGREE",
        "HCO_TYPE_DESCRIPTION",
        "MAJOR_CLASS_OF_TRADE",
        "HCO_SPECIALTY",
        "PROD_BRAND_NM",
        "TC_NM",
        "BRAND_SALES_SCORE",
        "COMPETITOR_SALES_SCORE",
        "CALLS_SCORE",
        "CLAIMS_SCORE",
        "SPECIALTY_SCORE",
        "CARESET_VALIDATION_FLAG",
        "CARESET_NEW_AFFL_FLAG",
        "PARENT_ACCOUNT_PRIORITY_SCORE",
        "PROXIMITY_SCORE",
        "RELATIONSHIP_STRENGTH_SCORE",
        "EMPLOYMENT_FLAG",
        "SOLICITED_FEEDBACK_FLAG",
        "FIELD_FEEDBACK_FLAG",
        "FIELD_FEEDBACK_SCORE",
        "FINAL_SCORE",
        "BRAND_RANK",
        "PRIMARY_AFFILIATION_CONFIDENCE_LEVEL"
    )

    string_cols = [f.name for f in demog.schema.fields if isinstance(f.dataType, StringType)]
    numeric_cols = [f.name for f in demog.schema.fields if isinstance(f.dataType, NumericType)]

    demog = demog.fillna("other", subset=string_cols).fillna(0, subset=numeric_cols)
    demog = demog.toPandas()
    demog.rename(
        columns={
            'BH_ID': 'CUSTOMER_ID',
            'PROD_BRAND_NM': 'PRODUCT_ID',
            'HCP_SPECIALTY': 'SPECIALTY',
        },
        inplace=True
    )
    demog.drop_duplicates(["CUSTOMER_ID"], inplace=True)
    return demog

def process_timeframes(counts_df, start_date, end_date):
    """
    Process data based on automatically calculated timeframes C1, C3, and P3.
    
    Args:
        counts_df (pd.DataFrame): Input DataFrame with 'CUSTOMER_ID' and 'YRMO' columns
        start_date (str): Start date in format 'MM/DD/YYYY'
        end_date (str): End date in format 'MM/DD/YYYY'
    
    Returns:
        pd.DataFrame: Processed DataFrame with aggregated values for each timeframe
    """
    # Convert dates to datetime objects
    if isinstance(start_date, str):
        start_dt = datetime.strptime(start_date, '%m/%d/%Y')
    else:
        start_dt = start_date
    # Calculate C1 (first month)


    C1 = {int(start_dt.strftime('%Y%m'))}
    # Calculate C3 (three months starting with start date)
    C3 = set()
    current_dt = start_dt
    for _ in range(3):
        C3.add(int(current_dt.strftime('%Y%m')))
        # Get the first day of next month
        if current_dt.month == 12:
            current_dt = datetime(current_dt.year + 1, 1, 1)
        else:
            current_dt = datetime(current_dt.year, current_dt.month + 1, 1)
    # Calculate P3 (previous three months)
    P3 = set()
    current_dt = start_dt

    # Skip P3_LAG_MONTH months to create the gap between C3 and P3
    # for _ in range(P3_LAG_MONTH):
    #     if current_dt.month == 1:
    #         current_dt = datetime(current_dt.year - 1, 12, 1)
    #     else:
    #         current_dt = datetime(current_dt.year, current_dt.month - 1, 1)

    for _ in range(3):
        # Move to first day of previous month
        if current_dt.month == 1:
            current_dt = datetime(current_dt.year - 1, 12, 1)
        else:
            current_dt = datetime(current_dt.year, current_dt.month - 1, 1)
        P3.add(int(current_dt.strftime('%Y%m')))

    # After building P3, add P6 and P12
    P6 = set()
    current_dt = start_dt
    for _ in range(6):
        if current_dt.month == 1:
            current_dt = datetime(current_dt.year - 1, 12, 1)
        else:
            current_dt = datetime(current_dt.year, current_dt.month - 1, 1)
        P6.add(int(current_dt.strftime('%Y%m')))

    P12 = set()
    current_dt = start_dt
    for _ in range(12):
        if current_dt.month == 1:
            current_dt = datetime(current_dt.year - 1, 12, 1)
        else:
            current_dt = datetime(current_dt.year, current_dt.month - 1, 1)
        P12.add(int(current_dt.strftime('%Y%m')))

    # Create timeframes dictionary
    timeframes = {'C1': C1, 'C3': C3, 'P3': P3, 'P6': P6, 'P12': P12}
    # Create a copy of the input DataFrame
    df = counts_df.copy()
    # Create an empty DataFrame to store results
    result = pd.DataFrame(df['CUSTOMER_ID'].unique(), columns=['CUSTOMER_ID'])
    # Process each timeframe
    for label, timeframe in timeframes.items():
        # Create boolean mask for rows in the timeframe
        mask = df['YRMO'].isin(timeframe)
        # Group by CUSTOMER_ID and sum
        aggregated = df[mask].groupby('CUSTOMER_ID').sum()
        # Drop the YRMO column from aggregated results
        aggregated.drop(columns='YRMO', inplace=True)

        # compute rollup touchpoint features before suffixing 
        cols = aggregated.columns.tolist()

        # Non-banner R columns + banner I columns → exposure touchpoint
        exposure_cols = [
                    c for c in cols
                    if ('_R_' in c or c.endswith('_R')) and 'BANNER' not in c.upper()
                ] + [
                    c for c in cols
                    if ('_I_' in c or c.endswith('_I')) and 'BANNER' in c.upper()
                ]

        # Pure exposure: R for ALL channels (including banners)
        exposure_all_cols = [c for c in cols if '_R_' in c or c.endswith('_R')]

        # All I columns → engagement touchpoint
        engagement_cols = [c for c in cols if '_I_' in c or c.endswith('_I')]

        # All E columns → interaction touchpoint
        interaction_cols = [c for c in cols if '_E_' in c or c.endswith('_E')]

        # Sum (0 if no matching columns)
        aggregated['EXPOSURE_TOUCHPOINT']  = aggregated[exposure_all_cols].sum(axis=1) if exposure_all_cols else 0
        aggregated['EXPOSURE_TOUCHPOINT_BANNER_ENGAGEMENT']    = aggregated[exposure_cols].sum(axis=1)    if exposure_cols    else 0
        aggregated['ENGAGEMENT_TOUCHPOINT']  = aggregated[engagement_cols].sum(axis=1)  if engagement_cols  else 0
        aggregated['INTERACTION_TOUCHPOINT'] = aggregated[interaction_cols].sum(axis=1) if interaction_cols else 0
        # ----------------------------------------------------------------


        # Add suffix to column names
        aggregated.columns = [f"{col}_{label}" for col in aggregated.columns]
        # Merge with results
        result = result.merge(aggregated, on='CUSTOMER_ID', how='left', validate = 'one_to_one')
    # Replace NaN with 0 for customers without activity in some timeframes
    result.fillna(0, inplace=True)
    
    return result, timeframes

def get_demog(product_filter, country_filter, spark, df_target, env):
    # hcp_demog = spark.sql(f"""SELECT * FROM jp{env}_comm_navin.com_jp_mart_navin_nbe.hcp_attributes WHERE COUNTRY = '{country_filter}'""")
    # hcp_demog = hcp_demog.toPandas()

    path = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/oe_journey/oe_volume_space/notebook_output/temp_kerendia_hcp_attr"
    hcp_demog = spark.read.format("delta").load(path)

    demog_df = demog_processing(hcp_demog, df_target)
    return demog_df

def generate_mdb(
    date_ranges,
    product,
    country,
    metric_mapping,
    spark,
    env,
    flag="mdb",
    ):
    """
    Generate MDB for multiple date ranges and stack them together.
    Optimized to call transactions and counts only once for the entire date range.
    
    Parameters:
    date_ranges (list of tuples): List of (start_date, end_date) tuples in format "MM/DD/YYYY"
    product (str): Product name
    country (str): Country name
    grain (str): Time grain for analysis
    metric_mapping (dict): Dictionary containing metric mappings
    
    Returns:
    pandas.DataFrame: Stacked MDB with added Instance column
    """

    
    date_ranges_dt = [(pd.to_datetime(start), pd.to_datetime(end)) 
                      for start, end in date_ranges]
    
    logger.info(f"Date ranges: {date_ranges_dt}")

    absolute_start = min(start for start, _ in date_ranges_dt)
    absolute_end = max(end for _, end in date_ranges_dt)

    # p3_start = absolute_start - pd.DateOffset(months=3)
    p3_start = absolute_start - pd.DateOffset(months=12)
    p3_start_yrmo = int(p3_start.strftime('%Y%m'))
    absolute_end_yrmo = int(absolute_end.strftime('%Y%m'))
    logger.info(f"Absolute start: {absolute_start}, Absolute end: {absolute_end}")
    logger.info(f"P3 start year-month: {p3_start_yrmo}, Absolute end year-month: {absolute_end_yrmo}")

    df_flag_new = pd.read_excel("/Workspace/Users/wenjie.chen@bayer.com/OE/GA Run/Data_for_production/5_5_2026_Bayer_OE_updated_channel_eng_exp_flag_latest.xlsx")
    df_flag_new = spark.createDataFrame(df_flag_new)

    if flag == "4c":
        df_target = spark.table("`ph-com-ai-us-prod-catalog-2553213839599380`.kerendia_oe_journey.Bayer_Kerendia_ga_target_universe_q4_target")
        df_target = (
            df_target
            .withColumnRenamed("customer_id", "BH_ID")
            # .filter(col("Test/Control") == "Test")
        )
    else:
        path = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/oe_journey/oe_volume_space/notebook_output/13_5_oe_modelling_universe_final"
        df_target = spark.read.format("delta").load(path)
        df_target = df_target.filter(col("modelling_flag")=="Yes")

    df_tagg = pd.read_excel("/Workspace/Users/wenjie.chen@bayer.com/OE/GA Run/Data_for_production/Content_tagging_6_5.xlsx")
    df_tagg['LITCODE'] = df_tagg['LITCODE'].astype(str)
    df_tagg = spark.createDataFrame(df_tagg)

    # # ---- DEBUG ----
    # DEBUG_SAMPLE = True # TODO Remove this
    # if DEBUG_SAMPLE:
    #     df_target = df_target.orderBy(F.rand(seed=42)).limit(500)  # ~500 customers
    #     df_target = df_target.cache()
    #     print(f"[DEBUG] df_target limited to {df_target.count()} customers")
    # # ---------------

    generator = Transactions(
        start_yrmo=p3_start_yrmo,
        end_yrmo=absolute_end_yrmo,
        product_key=product,
        country=country,
        metric_mapping=metric_mapping,
        df_flag_new = df_flag_new,
        df_target = df_target,
        df_tagg = df_tagg,
        env= env,
    )
    
    transactions = generator.get_transaction_idc()

    logger.info(f"Transactions shape: {transactions.shape}")
    counts = generator.get_counts(transactions)
    cvi = get_cvi_dataset(env, SPARK, df_target)
    
    # Initialize sequence generator once
    seq_gen_instance = seq_gen(
        customer_id='CUSTOMER_ID',
        channel_name_col='CHANNEL_PRODUCT',
        channel_number_col='CHANNEL_CODE',
        content_name_col='CONTENT_CATEGORY',
        content_number_col='CONTENT_CODE',
        date_column='EXPOSED_ON'
    )
    
    # Get demographics once
    demographics = get_demog(product, country, spark, df_target, env)
    
    all_mdbs = []

    transactions["PRODUCT_ID"] = "KERENDIA"

    # transactions.to_excel("/Workspace/Users/wenjie.chen@bayer.com/OE/nba_model_run/test_file.xlsx")
    # Process each date range using the same transactions and counts
    for instance, (start_date, end_date) in enumerate(date_ranges, 1):
        logger.info(f"Processing instance {instance} with date range: {start_date} to {end_date}")
        # Process sequences
        processor = SequenceProcessor()
        final_df = processor.process_sequences(
            idc=transactions,
            seq_gen_obj=seq_gen_instance,
            start_date=start_date,
            end_date=end_date
        )



        logger.info("===== BEFORE process_timeframes =====")  # TODO Remove this

        logger.info(f"Counts shape: {counts.shape}")
        logger.info(f"Total columns: {len(counts.columns)}")

        dup_cols = counts.columns[counts.columns.duplicated()].tolist()
        logger.info(f"Duplicate columns BEFORE: {dup_cols}")

        # FIX: detect _x/_y anywhere in column name
        xy_cols = [c for c in counts.columns if '_x' in c or '_y' in c]
        logger.info(f"_x/_y columns BEFORE: {xy_cols}")

        logger.info(f"_x/_y column count BEFORE: {len(xy_cols)}")

        
        # Process timeframes
        result_df, calculated_timeframes = process_timeframes(counts, start_date, end_date)
        logger.info(f"calculated_timeframes: {calculated_timeframes}")
        logger.info(f"Result DataFrame shape for instance {instance}: {result_df.shape}")


        logger.info("===== AFTER process_timeframes =====") # TODO Remove this

        logger.info(f"Result shape: {result_df.shape}")
        logger.info(f"Total columns: {len(result_df.columns)}")

        dup_cols_after = result_df.columns[result_df.columns.duplicated()].tolist()
        logger.info(f"Duplicate columns AFTER: {dup_cols_after}")

        # detect _x/_y anywhere (not just at end)
        xy_cols_after = [c for c in result_df.columns if re.search(r'(_x|_y)(_|$)', c)]
        logger.info(f"_x/_y columns AFTER: {xy_cols_after}")

        # Optional: count (helps quickly see scale of issue)
        logger.info(f"_x/_y column count AFTER: {len(xy_cols_after)}")



        
        # Create MDB through sequential merges
        mdb = pd.merge(
            final_df,
            result_df,
            on='CUSTOMER_ID',
            how='left',
            validate = 'one_to_one'
        ).fillna(0)

        logger.info(f"Merged MDB shape for instance {instance}: {mdb.shape}")
        logger.info(f"Merged MDB columns for instance {instance}: {mdb.columns}")

        mdb = pd.merge(
            mdb,
            demographics,
            on='CUSTOMER_ID',
            how='left',
            validate = 'one_to_one'
        )

        logger.info("mdb with demog merged")
        logger.info(f"Merged MDB with demographics shape for instance {instance}: {mdb.shape}")
        logger.info(f"Merged MDB with demographics columns for instance {instance}: {mdb.columns}") 

        logger.info(start_date, end_date)
        cvi_instance = cvi[
                (cvi.SVC_YRMO >= int(pd.to_datetime(start_date).strftime('%Y%m'))) & 
                (cvi.SVC_YRMO <= int(pd.to_datetime(end_date).strftime('%Y%m')))
            ]
        cvi_instance = cvi_instance.groupby(["CUSTOMER_ID"]).aggregate({
            "SVC_YRMO": "first",
            "TOTAL_NBRX_C3": "sum",
            "TOTAL_NBRX_P3": "sum",
            "TOTAL_TRX_C3":  "sum",
            "TOTAL_TRX_P3":  "sum",
            "PD_TRX_C3":     "sum",
            "PD_TRX_P3":     "sum",
        }).reset_index()

        # NEW: change in NBRx between current and prior 3-month windows
        cvi_instance['TOTAL_NBRX_CHANGE'] = cvi_instance['TOTAL_NBRX_C3'] - cvi_instance['TOTAL_NBRX_P3']
        cvi_instance['TOTAL_TRX_CHANGE']  = cvi_instance['TOTAL_TRX_C3']  - cvi_instance['TOTAL_TRX_P3']
        cvi_instance['PD_TRX_CHANGE']     = cvi_instance['PD_TRX_C3']     - cvi_instance['PD_TRX_P3']


        mdb = pd.merge(
            mdb,
            cvi_instance,
            on='CUSTOMER_ID',
            how='left',
            validate = 'one_to_one'
        )
        logger.info(f"Merged MDB with CVI shape for instance {instance}: {mdb.shape}")
        logger.info(f"Merged MDB with CVI columns for instance {instance}: {mdb.columns}")   


        # ---------- P4, P6, P12 sales features (same lag as P3) ----------
        end_yrmo_p = int(pd.to_datetime(end_date).strftime('%Y%m'))

        for label, extra_months in [('P4', 1), ('P6', 3), ('P12', 9)]:
            win_start_yrmo = int(
                (pd.to_datetime(start_date) - pd.DateOffset(months=extra_months)).strftime('%Y%m')
            )

            win_agg = (
                cvi[(cvi.SVC_YRMO >= win_start_yrmo) & (cvi.SVC_YRMO <= end_yrmo_p)]
                .groupby('CUSTOMER_ID')[['TOTAL_NBRX_P3', 'TOTAL_TRX_P3', 'PD_TRX_P3']]
                .sum()
                .reset_index()
                .rename(columns={
                    'TOTAL_NBRX_P3': f'TOTAL_NBRX_{label}',
                    'TOTAL_TRX_P3':  f'TOTAL_TRX_{label}',
                    'PD_TRX_P3':     f'PD_TRX_{label}',
                })
            )

            mdb = pd.merge(mdb, win_agg, on='CUSTOMER_ID', how='left', validate='one_to_one')
            for c in [f'TOTAL_NBRX_{label}', f'TOTAL_TRX_{label}', f'PD_TRX_{label}']:
                mdb[c] = mdb[c].fillna(0)

        logger.info(f"Merged MDB with P4/P6/P12 shape for instance {instance}: {mdb.shape}")
        # -----------------------------------------------------------------

        # ---------- C4 = start_date .. end_date + 1 month (independent of C3/P3) ----------
        c4_end_dt = pd.to_datetime(end_date) + pd.DateOffset(months=1)
        c4_start_yrmo = int(pd.to_datetime(start_date).strftime('%Y%m'))
        c4_end_yrmo   = int(c4_end_dt.strftime('%Y%m'))

        cvi_instance_c4 = cvi[
            (cvi.SVC_YRMO >= c4_start_yrmo) &
            (cvi.SVC_YRMO <= c4_end_yrmo)
        ]
        cvi_instance_c4 = (
            cvi_instance_c4
            .groupby(["CUSTOMER_ID"])
            .aggregate({
                "TOTAL_NBRX_C3": "sum",   # per-month current value summed over 4 months
                "TOTAL_TRX_C3":  "sum",
                "PD_TRX_C3":     "sum",
            })
            .reset_index()
            .rename(columns={
                "TOTAL_NBRX_C3": "TOTAL_NBRX_C4",
                "TOTAL_TRX_C3":  "TOTAL_TRX_C4",
                "PD_TRX_C3":     "PD_TRX_C4",
            })
        )

        mdb = pd.merge(
            mdb,
            cvi_instance_c4,
            on='CUSTOMER_ID',
            how='left',
            validate='one_to_one'
        )
        for c in ["TOTAL_NBRX_C4", "TOTAL_TRX_C4", "PD_TRX_C4"]:
            mdb[c] = mdb[c].fillna(0)
        logger.info(f"Merged MDB with C4 shape for instance {instance}: {mdb.shape}")
        # ----------------------------------------------------------------------------------
 



        # Add instance number
        mdb['INSTANCE'] = instance
        mdb['CUSTOMER_INSTANCE'] = mdb.CUSTOMER_ID + '_' + mdb.INSTANCE.astype(str)
        
        
        # NEW: instance start month (YYYYMM as int) and year (YYYY as int)
        _start_dt = pd.to_datetime(start_date)
        mdb['INSTANCE_START_MONTH'] = int(_start_dt.strftime('%Y%m'))
        mdb['INSTANCE_START_YEAR']  = int(_start_dt.strftime('%Y'))
        

        all_mdbs.append(mdb)
    
    # Stack all MDBs
    final_mdb = pd.concat(all_mdbs, axis=0, ignore_index=True)

    final_mdb['SPECIALTY'] = final_mdb['SPECIALTY'].astype(str)
    final_mdb['SPECIALTY'] = final_mdb['SPECIALTY'].str.replace(' ', '_')
    # final_mdb['Ingestion_Date'] = pd.to_datetime(final_mdb['Ingestion_Date'], errors='coerce')
    # cols_to_replace = ["Source_Details", "Model", "Brand"]
    # final_mdb[cols_to_replace] = final_mdb[cols_to_replace].fillna("None")
    
    return final_mdb

if __name__ == "__main__": # pragma: no cover
    
    # Load the Excel file
    file_path = "../config_file/mdb_prep_config.xlsx"  # Update this path if needed
    xls = pd.ExcelFile(file_path)

    # Read the Date Ranges sheet
    df_date_ranges = pd.read_excel(xls, sheet_name="Date Ranges")
    date_ranges = list(df_date_ranges.itertuples(index=False, name=None))

    # Read the Metric Mappings sheet
    df_metric_mapping = pd.read_excel(xls, sheet_name="Metric Mappings")

    # Convert metric mappings into a dictionary format
    metric_mapping = {}
    for _, row in df_metric_mapping.iterrows():
        category = row["Category"]
        event_type = row["Event Type"]
        mapped_metric = row["Mapped Metric"]

        if category not in metric_mapping:
            metric_mapping[category] = {}
        
        metric_mapping[category][event_type] = mapped_metric

    final_mdb = generate_mdb(
        date_ranges=date_ranges,
        product='KERENDIA',
        country='US',
        metric_mapping=metric_mapping,
        spark=SPARK,
        env=env,
    )

    logger.info(f'{final_mdb.head(3)}')
    # Save logs and shut down
    # close_logger_and_save(logger, log_buffer, log_path, SPARK)


    def ensure_list(x):
        if isinstance(x, np.ndarray):
            return x.tolist()
        elif x is None:
            return []
        elif isinstance(x, list):
            return x
        else:
            return [x]
    
    sequence_cols = [
        'full_channelName_seq', 'full_channelCode_seq',
        'channelName_seq', 'channelCode_seq',
        'full_contentName_seq', 'full_contentCode_seq',
        'contentName_seq', 'contentCode_seq',
        'timeSeq',
        'full_channelName_seq_GAP_grp', 'full_channelCode_seq_GAP_grp',
        'full_contentName_seq_GAP_grp', 'full_contentCode_seq_GAP_grp'
    ]

    for c in sequence_cols:
        final_mdb[c] = final_mdb[c].apply(ensure_list)



    logger.info("===== FINAL MDB COLUMN DEBUG =====") # TODO Remove this

    # Total columns
    logger.info(f"Total columns: {len(final_mdb.columns)}")

    # Duplicate columns
    dup_cols = final_mdb.columns[final_mdb.columns.duplicated()].tolist()
    logger.info(f"Duplicate columns: {dup_cols}")

    # _x / _y columns
    xy_cols = [c for c in final_mdb.columns if c.endswith('_x') or c.endswith('_y')]
    logger.info(f"_x/_y columns: {xy_cols}")

    # ✅ FIXED: detect _x/_y anywhere in column name
    xy_cols = [c for c in final_mdb.columns if '_x' in c or '_y' in c]
    logger.info(f"_x/_y columns: {xy_cols}")

    # Only log suspicious columns (IMPORTANT — avoids overflow)
    suspicious = [c for c in final_mdb.columns if 'GROUP_CALL' in c or '_x' in c or '_y' in c]
    logger.info(f"Suspicious columns: {suspicious}")



    # final_mdb = final_mdb[final_mdb["INSTANCE"].isin([7])]
    final_mdb_spark = SPARK.createDataFrame(final_mdb)


    # path = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/oe_journey/oe_volume_space/notebook_output/oe_final_nba_instance_features_v5"
    # df_nba_instance_features = SPARK.read.format("delta").load(path)
    
    # pvd_bhid_mapping = SPARK.read.format("delta").load(
    # "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/oe_journey/oe_volume_space/query_output/kerendia_nba_3_0_npi_bhid_mapping"
    # )
    # df_nba_instance_features = df_nba_instance_features.join(pvd_bhid_mapping.select("BH_ID", "PROVIDER_ID"), how="left", on="PROVIDER_ID")
    # df_nba_instance_features = df_nba_instance_features.drop("PROVIDER_ID")
    # df_nba_instance_features = df_nba_instance_features.withColumnRenamed("BH_ID", "CUSTOMER_ID")
    # df_nba_instance_features = df_nba_instance_features.withColumn("INSTANCE", F.substring_index(F.col("INSTANCE"), "_", -1))

    # final_mdb_spark = final_mdb_spark.join(
    #     df_nba_instance_features,
    #     on=["CUSTOMER_ID", "INSTANCE"],
    #     how="left"
    # )

    segment_path = "/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/oe_journey/oe_volume_space/notebook_output/customer_segment"
    segment_df = SPARK.read.format("delta").load(segment_path)

    filtered_segment_df = segment_df.filter(
        (col("BAYER_ID").isNotNull()) &
        (~col("BAYER_ID").like("%BHO%")) &
        (upper(col("PRODUCT_1")) == "KERENDIA")
    )

    unique_segment_df = (
        filtered_segment_df
        .select("BAYER_ID", "NOTE_2")
        .dropDuplicates(["BAYER_ID"])
        .withColumnRenamed("BAYER_ID", "CUSTOMER_ID")
        .withColumnRenamed("NOTE_2", "CUSTOMER_SEGMENT")
    )

    logger.info(f"Total records after filtering: {unique_segment_df.count()}")
    logger.info(f"Unique CUSTOMER_ID count: {unique_segment_df.select('CUSTOMER_ID').distinct().count()}")

    final_mdb_spark = final_mdb_spark.join(
    unique_segment_df,
    on="CUSTOMER_ID",
    how="left"
    )

    # Fill null segments
    final_mdb_spark = final_mdb_spark.fillna({
        "CUSTOMER_SEGMENT": "Unassigned"
    })

    # ---------- One-hot encode CUSTOMER_SEGMENT ----------
    segment_values = [
        row["CUSTOMER_SEGMENT"]
        for row in final_mdb_spark.select("CUSTOMER_SEGMENT").distinct().collect()
    ]
    logger.info(f"Distinct CUSTOMER_SEGMENT values found: {segment_values}")

    segment_ohe_cols = []

    for seg in segment_values:
        seg_upper = str(seg).upper()

        if seg_upper.endswith("SEGMENT") or seg_upper.endswith("SEGMENTED"):
            segment_col_name = seg_upper
        else:
            segment_col_name = f"{seg_upper}_SEGMENT"

        segment_ohe_cols.append(segment_col_name)

        final_mdb_spark = final_mdb_spark.withColumn(
            segment_col_name,
            F.when(F.col("CUSTOMER_SEGMENT") == F.lit(seg), F.lit(1)).otherwise(F.lit(0))
        )

    logger.info(f"One-hot encoded segment columns added: {segment_ohe_cols}")
    


    final_mdb_spark.write.format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .save("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/oe_journey/oe_volume_space/notebook_output/model_training_mdb_v6_p12_added")

    # df1 = final_mdb_spark.filter(F.col("INSTANCE").isin(1, 2, 3, 4))
    # df2 = final_mdb_spark.filter(F.col("INSTANCE").isin(5, 6, 7))

    # final_mdb_spark.write.format("delta") \
    #     .mode("overwrite") \
    #     .option("mergeSchema", "true") \
    #     .save("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/oe_journey/oe_volume_space/notebook_output/nba_mdb_all_instance_final_v4_all")

    # df2.write.format("delta") \
    #     .mode("overwrite") \
    #     .option("mergeSchema", "true") \
    #     .save("/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/oe_journey/oe_volume_space/notebook_output/nba_mdb_all_instance_final_v4_all_part2")

    # Convert the DataFrame to a Parquet file in a temporary file
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as temp_file:
        temp_path = temp_file.name  # Get the temporary file path
        final_mdb.to_parquet(temp_path, index=False)  # Save Parquet file to temp path

    # Read the temporary Parquet file into a BytesIO buffer
    with open(temp_path, 'rb') as f:
        buffer = io.BytesIO(f.read()) 
        
    # Cleanup: Remove the temporary file
    os.remove(temp_path)