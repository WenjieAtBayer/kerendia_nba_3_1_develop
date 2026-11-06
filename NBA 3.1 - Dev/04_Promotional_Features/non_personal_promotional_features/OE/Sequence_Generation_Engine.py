# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 15:51:04 2018

@author: sp18898
"""


import pandas as pd
from datetime import datetime,timedelta
import numpy as np
from functools import reduce
from itertools import product
from collections import Counter
import math
import time

class zs_pa_dataprep:
    
    def __init__(self, customer_id, channel_name_col, channel_number_col, content_name_col,\
        content_number_col, date_column):
        """
        customre_id     : customer_id column name
        channel_name_col   : column name of channel names
        channel_number_col : column name of channel numbers
        content_name_col   : column name of content names
        content_number_col : column name of content numbers
        date_column     : column name containing dates
        """
        self.customer_id = customer_id
        self.channel_name_col = channel_name_col
        self.channel_number_col = channel_number_col
        self.content_name_col = content_name_col
        self.content_number_col = content_number_col
        self.date_column = date_column
        
    def journey_rollup(self, activity_data, start_date, end_date):
        '''
            Rollup patient journey at patient level or patient-HCP level
        '''

        # start_date = datetime.strptime(start_date,  "%m/%d/%Y") #TODO: UNCOMMENT if in str format
        # end_date = datetime.strptime(end_date,  "%m/%d/%Y") #TODO: UNCOMMENT if in str format

        # subset and sort activity and sales datasets
        activity_data = activity_data[(activity_data[self.date_column] >= start_date) & (activity_data[self.date_column] <= end_date)]
        activity_data = activity_data.sort_values([self.customer_id, self.date_column], ascending = [True, True])
        activity_data['days_since_start'] = (activity_data[self.date_column] - start_date).dt.days

        # unique customer ids
        customers = activity_data[self.customer_id].unique().tolist()
        # date range
        num_periods = (end_date - start_date).days
        datelist = pd.date_range(start_date, periods = num_periods+1).tolist()
        # all the combinations of customers and dates
        all_customer_dates = pd.DataFrame(list(product(customers, datelist)), columns = [self.customer_id, self.date_column])

        all_customer_dates[self.date_column] = pd.to_datetime(all_customer_dates[self.date_column])
        activity_data[self.date_column] = pd.to_datetime(activity_data[self.date_column])
        
        # creating whole activity data
        all_customer_dates = all_customer_dates.merge(activity_data, how = 'left', on = [self.customer_id, self.date_column], validate='many_to_many').reset_index()
        all_customer_dates[self.channel_name_col] =all_customer_dates[self.channel_name_col].fillna('GAP')
        all_customer_dates[self.channel_number_col] = all_customer_dates[self.channel_number_col].fillna(0)
        all_customer_dates[self.content_name_col] =all_customer_dates[self.content_name_col].fillna('GAP')
        all_customer_dates[self.content_number_col] = all_customer_dates[self.content_number_col].fillna(0)


        # initialize lists of sequences
        full_list_channel_name_seq = []
        full_list_channel_code_seq = []
        list_channel_name_seq = []
        list_channel_code_seq = []

        full_list_content_name_seq = []
        full_list_content_code_seq = []
        list_content_name_seq = []
        list_content_code_seq = []
        list_time_seq = []
        
        count=1
        
        grouped = all_customer_dates.groupby(self.customer_id)
        grouped_2 = activity_data.groupby(self.customer_id)
        
        for i in all_customer_dates[self.customer_id].unique():
            count+=1
            full_list_channel_name_seq.append(list(grouped.get_group(i)[self.channel_name_col]))
            full_list_channel_code_seq.append(list(grouped.get_group(i)[self.channel_number_col]))
            list_channel_name_seq.append(list(grouped_2.get_group(i)[self.channel_name_col]))
            list_channel_code_seq.append(list(grouped_2.get_group(i)[self.channel_number_col]))

            full_list_content_name_seq.append(list(grouped.get_group(i)[self.content_name_col]))
            full_list_content_code_seq.append(list(grouped.get_group(i)[self.content_number_col]))
            list_content_name_seq.append(list(grouped_2.get_group(i)[self.content_name_col]))
            list_content_code_seq.append(list(grouped_2.get_group(i)[self.content_number_col]))

            # append to time sequence
            time_seq = list(grouped_2.get_group(i)['days_since_start'])
            temp_time_seq = [(time_seq[i+1] - time_seq[i]) for i in range(len(time_seq)-1)]
            temp_time_seq.insert(0, time_seq[0])
            time_seq = temp_time_seq
            list_time_seq.append(time_seq)
            
        return_data = pd.DataFrame()

        return_data[self.customer_id] = all_customer_dates[self.customer_id].unique()
        return_data['full_channelName_seq'] = full_list_channel_name_seq
        return_data['full_channelCode_seq'] = full_list_channel_code_seq
        return_data['channelName_seq'] = list_channel_name_seq
        return_data['channelCode_seq'] = list_channel_code_seq

        return_data['full_contentName_seq'] = full_list_content_name_seq
        return_data['full_contentCode_seq'] = full_list_content_code_seq
        return_data['contentName_seq'] = list_content_name_seq
        return_data['contentCode_seq'] = list_content_code_seq
        return_data['timeSeq'] = list_time_seq

        return_data = return_data.fillna(0)
        return return_data
    
    def channel_count(self,master_data,event_name,channel_list):
        channel_count_data=pd.DataFrame()
        channel_count_data[self.customer_id]=master_data[self.customer_id]
        for channel in channel_list:
            channel_count_data[channel]=[x.count(channel) for x in master_data[event_name]]
        return channel_count_data

    def content_count(self,master_data,event_name,content_list):
        content_count_data=pd.DataFrame()
        content_count_data[self.customer_id]=master_data[self.customer_id]
        for content in content_list:
            content_count_data[content]=[x.count(content) for x in master_data[event_name]]
        return content_count_data