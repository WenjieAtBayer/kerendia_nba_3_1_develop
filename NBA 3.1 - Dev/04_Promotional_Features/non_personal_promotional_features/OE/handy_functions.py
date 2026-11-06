import re
import datetime
import pandas as pd

def nan_handler(dataframe:pd.DataFrame,rules = {'drop':["hcp_id", "exposed_on", "channel_id"],'fill':{1:['count']}}):
    """
        Warning: This function is designed to work with NBA projects 
        Input:
            dataframe: Relevant dataframe for NBA POC
            rules: Dictionary that defines the rules
        Output:
            dataframe
        Default rules for processing:
            1. Instances where the HCP_ID, Exposed_on, Channel is NaN are dropped
            2. Replacing NaN
                1. Count ------> 1
    """
    if rules['drop']:
        dataframe = dataframe.dropna(axis = 0, subset = rules['drop'])
    if rules['fill']:
        for key in rules['fill'].keys():
            dataframe[rules['fill'][key]] = dataframe[rules['fill'][key]].fillna(value=key,axis=0)
    dataframe.isna().any()
    return dataframe.copy(deep=True)

def handling_datatime(dataframe:pd.DataFrame, columns_for_datetime:list, column_for_yrmo:str='exposed_on'):
    for column in columns_for_datetime:
        dataframe[column] = pd.to_datetime(dataframe[column]).dt.strftime("%d-%m-%Y")
    dataframe['YRMO'] = pd.to_datetime(dataframe[column_for_yrmo],infer_datetime_format=True).dt.strftime("%m%Y")
    return dataframe.copy(deep=True)

def convert_to_numeric(dataframe:pd.DataFrame,column):
    try:
        dataframe[column] = pd.to_numeric(dataframe[column])
        return dataframe.copy(deep=True)
    except ValueError:
        id_list = []
        problem_list = []
        for index,val in dataframe.iterrows():
            value = val[column]
            try:
                id_list.append(int(value))
            except ValueError:
                id_list.append(value)
                problem_list.append(value)
        dataframe[column] = id_list
    print(problem_list)
    return dataframe.copy(deep=True)

def categorical(dataframe:pd.DataFrame,columns=None,limit=20):
    if not columns:
        columns = dataframe.columns
    for column in columns:
        num_uniques = dataframe[column].nunique()
        print()
        print(column+" has "+str(num_uniques)+" unique values")
        if num_uniques < limit:
            print("Following is a list of unique values with count\n")
            print(dataframe[column].value_counts(dropna=False))
        print()
        print("<"+"-"*20+">")

def standardize_column_header(dataframe:pd.DataFrame, rename_columns:dict = None, replace_phrase:dict = None):
    pattern = re.compile('[a-zA-Z0-9]+')
    if rename_columns:
        dataframe = dataframe.rename(columns=rename_columns)
    if replace_phrase:
        for key,value in replace_phrase.items():
            dataframe.columns = [x.replace(key,value) for x in dataframe.columns]
    maps = {name:"_".join(re.findall(pattern,name)).upper() for name in dataframe.columns}
    dataframe = dataframe.rename(columns=maps)
    return dataframe.copy(deep=True)

def standardize_columns(dataframe,columns=[]):
    pattern = re.compile('[a-zA-Z0-9]+')
    for column in columns:
        dataframe[column] = dataframe[column].apply(lambda value: "_".join(re.findall(pattern,str(value))).upper())
    return dataframe.copy()

def generate_year_months(start_month, end_month):
    """
    Inputs:
        start_month = YYYYMM
        end_month = YYYYMM
    Output:
        List of YRMO
    """
    year_months = []
    curr_month = start_month
    while curr_month <= end_month:
        year_months.append(curr_month)
        year = curr_month // 100
        month = curr_month % 100
        month += 1
        if month > 12:
            month = 1
            year += 1
        curr_month = year * 100 + month
    return year_months

def get_past_date(year_month, month_difference):
    year = year_month // 100
    month = year_month % 100
    start_date = datetime.date(year, month, 1)
    difference = datetime.timedelta(days=month_difference*30)
    past_date = start_date - difference 
    return int(past_date.strftime('%Y%m'))