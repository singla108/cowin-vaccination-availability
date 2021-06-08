import datetime
import json
import numpy as np
import requests
import pandas as pd
import streamlit as st
from copy import deepcopy
from fake_useragent import UserAgent
from footer_utils import image, link, layout, footer

import time
import csv 

st.set_page_config(layout='wide',
                   initial_sidebar_state='collapsed',
                   page_icon="Vaccination.png",
                   page_title="COVID-19 NCR Vaccination Slot Availability")

@st.cache(allow_output_mutation=True, suppress_st_warning=True)

def load_mapping():
    df = pd.read_csv("district_mapping.csv")
    return df

def filter_column(df, col, value):
    df_temp = deepcopy(df.loc[df[col] == value, :])
    return df_temp

def filter_capacity(df, col, value):
    df_temp = deepcopy(df.loc[df[col] > value, :])
    return df_temp

@st.cache(allow_output_mutation=True)
def Pageviews():
    return []

mapping_df = load_mapping()

rename_mapping = {
    'date': 'Date',
    'min_age_limit': 'Minimum Age Limit',
    'available_capacity': 'Available Capacity',
    'available_capacity_dose1' : 'Dose 1',
    'available_capacity_dose2' : 'Dose 2',
    'vaccine': 'Vaccine',
    'pincode': 'Pincode',
    'name': 'Hospital Name',
    'state_name' : 'State',
    'district_name' : 'District',
    'fee_type' : 'Fees'
    }


st.success('CoWIN NCR vaccination slot availability application for today + 5 days')

valid_states = list(np.unique(mapping_df["state_name"].values))

unique_districts_all = []
temp_districts = []

numdays = 5 # [CONFIGURATIONS WHICH CAN CHANGE] Give number of days i.e. today + days to get the data from COWIN public APIs 

# [CONFIGURATIONS WHICH CAN CHANGE] provide districts to get data, please use district_mapping.csv to get India district names to change 
district_inp = ['Gurgaon', 'Faridabad', 'Gautam Buddha Nagar', 'New Delhi', 'South Delhi', 'South East Delhi', 'South West Delhi','Central Delhi','East Delhi','Shahdara','North Delhi', 'North East Delhi','North West Delhi','West Delhi'] 
    
for DISTRICT_NAME in district_inp:
            mapping_dict = filter_column(mapping_df, "district name", DISTRICT_NAME)
            temp_district_id = mapping_dict.loc[:, "district id"].values.item()
            temp_districts.append(temp_district_id)

st.write ('Selected NCR Districts to fetch data')
st.success (district_inp) 

    
base = datetime.datetime.today()
date_list = [base + datetime.timedelta(days=x) for x in range(numdays)]
date_str = [x.strftime("%d-%m-%Y") for x in date_list]

temp_user_agent = UserAgent(verify_ssl=False)
browser_header = {'User-Agent': temp_user_agent.random}

final_df = None

# Program run in loop for Date and then fetched Ditrict Ids and connect to Public Cowin API to get data from districts and on date 
for INP_DATE in date_str:
       for DIST_IDs in temp_districts:
            URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={}&date={}".format(DIST_IDs, INP_DATE)
            response = requests.get(URL, headers=browser_header)
            if (response.ok) and ('centers' in json.loads(response.text)):
                resp_json = json.loads(response.text)['centers']
                if resp_json is not None:
                    df = pd.DataFrame(resp_json)
                    if len(df):
                        df = df.explode("sessions")
                        df['min_age_limit'] = df.sessions.apply(lambda x: x['min_age_limit'])
                        df['vaccine'] = df.sessions.apply(lambda x: x['vaccine'])
                        df['available_capacity'] = df.sessions.apply(lambda x: x['available_capacity'])
                        df['available_capacity_dose1'] = df.sessions.apply(lambda x: x['available_capacity_dose1'])
                        df['available_capacity_dose2'] = df.sessions.apply(lambda x: x['available_capacity_dose2'])
                        df['date'] = df.sessions.apply(lambda x: x['date'])
                        df = df[["date", "available_capacity","available_capacity_dose1","available_capacity_dose2", "vaccine", "min_age_limit", "pincode", "name", "state_name", "district_name", "fee_type"]]
                        if final_df is not None:
                            final_df = pd.concat([final_df, df])
                        else:
                            final_df = deepcopy(df)
                else:
                    st.error("No rows in the data Extracted from the API")


if (final_df is not None) and (len(final_df)):
    final_df.drop_duplicates(inplace=True)
    final_df.rename(columns=rename_mapping, inplace=True)

    # [CONFIGURATIONS WHICH CAN CHANGE] uncomment the following lines if you want to filter the output with that filter
    #final_df = filter_column(final_df, "Minimum Age Limit", 18)
    #final_df = filter_column(final_df, "Minimum Age Limit", 45)
    #final_df = filter_column(final_df, "Vaccine", "COVISHIELD")
    #final_df = filter_column(final_df, "Vaccine", "COVAXIN")
    final_df = filter_capacity(final_df, "Available Capacity", 5)
    #final_df = filter_capacity(final_df, "Dose 1", 0)
    #final_df = filter_capacity(final_df, "Dose 2", 0)
    #final_df = filter_column(final_df, "Fees", "Paid")

    # Print current date and time 
    st.write('Date/Time: ' + datetime.datetime.now().strftime("%d/%B/%Y, %H:%M:%S"))
    table = deepcopy(final_df)
    table.reset_index(inplace=True, drop=True)
    
    # Display the data in table 
    st.table(table)

else:
    st.error("Unable to fetch data currently, please try after sometime")
        

pageviews=Pageviews()
pageviews.append('dummy')
pg_views = len(pageviews)
footer(pg_views)
