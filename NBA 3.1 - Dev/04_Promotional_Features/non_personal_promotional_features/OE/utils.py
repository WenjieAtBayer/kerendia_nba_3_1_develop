# Import libraries
import pandas as pd
import sys
import numpy as np
import mlflow
import re
import os
import warnings
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType
from statsmodels.api import OLS, add_constant
import logging
import io
from datetime import datetime

from sklearn.model_selection import train_test_split
import boto3
from io import StringIO
# Ignore all warnings
warnings.filterwarnings("ignore")

os.environ["PYSPARK_PIN_THREAD"]="-1"

def get_highest_priority(specialty_str, priority):

    if not isinstance(specialty_str, str) or specialty_str.strip() == '':
        return 'OTHERS'
    
    specialties = [spec.strip().upper() for spec in specialty_str.split('|')]

    for spec in priority:
        if spec.strip().upper() in specialties:
            return spec.strip().upper()
    return 'OTHERS'  

def create_age_bucket(age):

    try:
        age = float(age)
    except (ValueError, TypeError):
        return 'OTHERS'
    if pd.isnull(age):
        return 'OTHERS'
    elif 25 < age <= 40:
        return '25_40'
    elif 40 < age <= 55:
        return '41_55'
    elif 55 < age <= 70:
        return '56_70'
    elif 70 < age <= 85:
        return '71_85'
    else:
        return 'OTHERS'


def create_experience_bucket(experience):

    try:
        exp = float(experience)
    except (ValueError, TypeError):
        return 'OTHERS'

    if 0 <= exp < 10:
        return '0_10'
    elif 10 <= exp < 20:
        return '11_20'
    elif 20 <= exp < 30:
        return '21_30'
    elif 30 <= exp < 40:
        return '31_40'
    elif 40 <= exp < 50:
        return '41_50'
    elif 50 <= exp <= 65:
        return '51_65'
    else:
        return 'OTHERS'


def content_tagging(df, column_name , content_dict=None):

    def prioritize_content(value):
        if pd.isna(value) or not value.strip():
            return None
    
        elements = value.split('|')
        count_dict = {}
    
        for el in elements:
            count_dict[el] = count_dict.get(el, 0) + 1
    
        sorted_elements = sorted(
            count_dict.keys(),
            key=lambda x: (-count_dict[x], elements.index(x))
        )
        
        return sorted_elements[0] if sorted_elements else None

    df[column_name] = df[column_name].apply(prioritize_content)

    if content_dict is not None: # perform content translation if content_dict is present
        df[column_name] = df[column_name].map(content_dict)

    return df[column_name]

    # def map_and_prioritize(value):
    #     if pd.isna(value):
    #         return None

    #     mapped = []
    #     for item in value.split('|'):
    #         mapped.append(str(content_dict.get(item, 'None')))

    #     if not mapped:
    #         return None

    #     count_dict = {}
    #     for element in mapped:
    #         count_dict[element] = count_dict.get(element, 0) + 1

    #     sorted_elements = sorted(
    #         count_dict.keys(),
    #         key=lambda x: (-count_dict[x], mapped.index(x))
    #     )

    #     return sorted_elements[0] if sorted_elements else None

    # df['COUNTRY_MESSAGE_CATEGORY'] = df[column_name].apply(map_and_prioritize)
    # return df
    