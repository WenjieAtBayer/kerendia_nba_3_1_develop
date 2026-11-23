import os
import sys
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
from src.NBA.utility.setup_cluster import run_setup
run_setup()

from src.NBA.model_training.nba_model_training import driver

if __name__ == "__main__":

    argument_list = sys.argv[1:]
    mdb_path = argument_list[0]
    env = argument_list[1]
    log_file_path = argument_list[2]
    experiment_name = argument_list[3]
    
    config_file_path = os.path.abspath(f'../config_file/NBA Model Architecture.xlsx')


    _, extra_data = driver(
        config_file_path = config_file_path, 
        mdb_path = mdb_path,
        log_file_path = log_file_path,
        experiment_name=experiment_name,
        env=env,
    )
    unsupported_types = [np.int8, np.uint8, pd.Int8Dtype()]

    # Convert each unsupported type to int32
    for col in extra_data.columns:
        dtype = extra_data[col].dtype
        if dtype in unsupported_types or str(dtype) in ["int8", "Int8", "uint8"]:
            extra_data[col] = extra_data[col].astype(np.int32)

    # extra_data.head(100).to_parquet("/Workspace/Users/wenjie.chen@bayer.com/OE/GA Run/Data/extra_data_all_features_27.parquet")
    # spark = SparkSession.builder.appName("nba_model_runner").getOrCreate()
    # schema_name = f"`ph-com-ai-us-prod-catalog-2553213839599380`.kerendia_oe_journey.Bayer_Kerendia_ga_demog_db."
    # spark.createDataFrame(extra_data).write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{schema_name}Bayer_OE_4C_GA_DEMOG")