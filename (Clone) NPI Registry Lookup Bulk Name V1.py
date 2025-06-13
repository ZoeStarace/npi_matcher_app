# Databricks notebook source
# MAGIC %md
# MAGIC # Bulk NPI Lookup
# MAGIC ### Version 1.0
# MAGIC ### Creator: Randall Smith
# MAGIC The following program reads in a text file with Rec_ID, First_Name, and Last_Name and matches the name and state (optional) to the NPI Registry API.  
# MAGIC  

# COMMAND ----------

# MAGIC %pip install flatten_json

# COMMAND ----------

import requests
import json
import pandas as pd
import numpy as np
from pprint import pprint
from flatten_json import flatten

# COMMAND ----------

# MAGIC %md
# MAGIC #### Comment Out
# MAGIC #create sample dataframe for testing
# MAGIC data = {'Row_ID':[1,2,3,4,5,6], 'Last_Name':['Abungu', 'Addesa', 'Ahmad ', ' Ahmed', 'Al Alwani', 'Al-Gharazi'], 'First_Name':['Billy Scott', 'Anthony ', 'Muhammad Afzal', 'Rashid', 'Khaled ', ' Mohammed' ]}
# MAGIC df = pd.DataFrame(data)
# MAGIC print(df.shape)
# MAGIC display(df.head(n=10))

# COMMAND ----------

#import codecs
in_file = "/Volumes/hradev/fa_data_hra_dss_genai/basic_rag_demo_payload_request_logs_checkpoints/RTS/2024-2025 CRH Roster Clean V2.txt"

#thefile = codecs.open(in_file, 'rU', encoding='UTF-16')

df = pd.read_csv(in_file, sep='\t', encoding='cp1252')
#df = pd.read_csv(in_file, sep='\t', encoding='utf_7', errors='ignore')
print(df.shape)
display(df.head(n=10))

# COMMAND ----------

#strip any white space in front or back of name
df['Last_Name'] = df['Last_Name'].str.strip()
df['First_Name'] = df['First_Name'].str.strip()

#create list for middle name
m_name_list = []
for i in range(df.shape[0]):
  #print("*"+df.loc[i,'Last_Name']+"*"+df.loc[i,'First_Name']+"*")
  #if first name has multiple names, split, correct first and add middle to list
  if len(df.loc[i,'First_Name'].split()) > 1:
    m_name_list.append(df.loc[i,'First_Name'].split()[1])
    df.loc[i,'First_Name'] = df.loc[i,'First_Name'].split()[0]
  else:
    m_name_list.append("")

#print(m_name_list)
df["Middle_Name"] = m_name_list
display(df.head(n=10))

# COMMAND ----------


df.rename(columns={"Rec_ID": "Row_ID"}, inplace=True)

# COMMAND ----------

#version
Version = 2.1
#limit
Limit = 5
#state (if you don't want to limit to one state, make value blank "")
State = "NY"

#create list to hold all results (more efficient that concat to df)
main_list = []

for i in range(df.shape[0]):
  First_Name  = df.loc[i,'First_Name']
  Last_Name   = df.loc[i,'Last_Name']
  Middle_Name = df.loc[i,'Middle_Name']
  Rec_ID      = df.loc[i,'Row_ID']
  

  #build request
  request = f'l.cms.hhs.gov/api/?number=&enumeration_type=NPI-1&taxonomy_description=&first_name={First_Name}&last_name={Last_Name}&organization_name=&address_purpose=&city=&state={State}&postal_code=&country_code=&limit={Limit}&skip=&version={Version}&use_first_name_alias=False'

  r = requests.get(request)
  results_json = r.json()
  
  #keep track of match level where 1 = first and last name and state (if present)
  if results_json['result_count'] > 0:
    Match_Level = 1
  
  #if no results search first (fuzzy), last name and state
  if results_json['result_count'] == 0:
    request = f'https://npiregistry.cms.hhs.gov/api/?number=&enumeration_type=NPI-1&taxonomy_description=&first_name={First_Name}&last_name={Last_Name}&organization_name=&address_purpose=&city=&state={State}&postal_code=&country_code=&limit={Limit}&skip=&version={Version}'
    r = requests.get(request)
    results_json = r.json()
    if results_json['result_count'] > 0:
      Match_Level = 2 #first (fuzzy), last name, and state match

  #if no results search first and last name only
  if results_json['result_count'] == 0:
    request = f'https://npiregistry.cms.hhs.gov/api/?number=&enumeration_type=NPI-1&taxonomy_description=&first_name={First_Name}&last_name={Last_Name}&organization_name=&address_purpose=&city=&state={""}&postal_code=&country_code=&limit={Limit}&skip=&version={Version}'
    r = requests.get(request)
    results_json = r.json()
    if results_json['result_count'] > 0:
      Match_Level = 3 #first and last name match with no state

  #if no results search on first name only
  if results_json['result_count'] == 0:
    request = f'https://npiregistry.cms.hhs.gov/api/?number=&enumeration_type=NPI-1&taxonomy_description=&first_name={""}&last_name={Last_Name}&organization_name=&address_purpose=&city=&state={State}&postal_code=&country_code=&limit={Limit}&skip=&version={Version}'
    r = requests.get(request)
    results_json = r.json()
    if results_json['result_count'] > 0:
      Match_Level = 4 #last name and state match
  
  
  result_count = results_json['result_count']

  if result_count == 0:
    Match_Level = 0
    i           = 0
    NPI         = ""
    creditial   = ""
    first_name  = "" 
    middle_name = ""
    last_name   = ""
    specialty1  = ""
    specialty2  = ""
    state1      = ""
    state2      = ""
    state3      = ""
    city1       = ""
    city2       = ""
    city3       = ""
    add1        = ""
    add2        = ""
    add3        = ""

    list_for_df = [Rec_ID, First_Name, Last_Name, Middle_Name, Match_Level, result_count, i, NPI, first_name, last_name, middle_name, creditial, specialty1, specialty2, add1, city1, state1, add2, city2, state2, add3, city3, state3]

    main_list.append(list_for_df)
        
  else:
    #iterate through results
    for j in range(result_count):
      #initialize variables
      NPI         = ""
      creditial   = ""
      first_name  = "" 
      middle_name = ""
      last_name   = ""
      specialty1  = ""
      specialty2  = ""
      state1      = ""
      state2      = ""
      state3      = ""
      city1       = ""
      city2       = ""
      city3       = ""
      add1        = ""
      add2        = ""
      add3        = ""

      NPI = results_json['results'][j]['number']
      if 'credential' in results_json['results'][j]['basic']:
        creditial = results_json['results'][j]['basic']['credential']
      first_name = results_json['results'][j]['basic']['first_name']
      last_name = results_json['results'][j]['basic']['last_name']
      if 'middle_name' in results_json['results'][j]['basic']:
        middle_name = results_json['results'][j]['basic']['middle_name']

      tax_len = len(results_json['results'][j]['taxonomies'])
      for i in range(tax_len):
        if i == 0:
          specialty1 = results_json['results'][j]['taxonomies'][i]['desc']
        elif i == 1:
          specialty2 = results_json['results'][j]['taxonomies'][i]['desc']

      add_len = len(results_json['results'][j]['addresses'])
      for i in range(add_len):
        if i == 0:
          state1 = results_json['results'][j]['addresses'][i]['state']
          add1   = results_json['results'][j]['addresses'][i]['address_1']
          city1  = results_json['results'][j]['addresses'][i]['city']
        elif i == 1:
          state2 = results_json['results'][j]['addresses'][i]['state']
          add2   = results_json['results'][j]['addresses'][i]['address_1']
          city2  = results_json['results'][j]['addresses'][i]['city']
        elif i == 2:
          state3 = results_json['results'][j]['addresses'][i]['state']
          add3   = results_json['results'][j]['addresses'][i]['address_1']
          city3  = results_json['results'][j]['addresses'][i]['city']
        
      list_for_df = [Rec_ID, First_Name, Last_Name, Middle_Name, Match_Level, result_count, j+1, NPI, first_name, last_name, middle_name, creditial, specialty1, specialty2, add1, city1, state1, add2, city2, state2, add3, city3, state3]

      main_list.append(list_for_df)

#create dataframe from list
if len(main_list) > 0:
  column_names = ['Row_ID', 'First_Name_Supplied', 'Last_Name_Supplied', 'Middle_Name_Supplied', 'Match_Level', 'Result_Count', 'Result', 'NPI', 'First_Name', 'Last_Name', 'Middle_Name', 'Creditials', 'Specialty_1', 'Specialty_2', 'Address_1', 'City_1', "State_1", 'Address_2', 'City_2', "State_2", 'Address_3', 'City_3', "State_3"]

  df_reg = pd.DataFrame(main_list, columns=column_names)
  df_reg = df_reg.astype({'Row_ID': 'int'})
  display(df_reg)
       

# COMMAND ----------

print(df_reg.shape)

# COMMAND ----------

df_nodups = df_reg.drop_duplicates(subset=['Row_ID'])
print("Record Count: ", df_nodups.shape[0])
print("\nDistribution of Match:\n", df_nodups['Match_Level'].value_counts(), sep="")
print("\nDistribution of Match:\n", df_nodups['Result_Count'].value_counts(), sep= "")

# COMMAND ----------

df_merge = pd.merge(df_reg, df[["Row_ID", "Specialty", "Suffix"]], on="Row_ID", how="left")

# COMMAND ----------

display(df_merge.head(n=20))

# COMMAND ----------

df_merge.dtypes

# COMMAND ----------

out_path = '/Volumes/hradev/fa_data_hra_dss_genai/basic_rag_demo_payload_request_logs_checkpoints/RTS/'
out_file = '202410_CRH_NPI_Reg_Results_V1.csv'

df_merge.to_csv(out_path+out_file, index=False)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Comment Out
# MAGIC import os
# MAGIC parent_dir = "/Volumes/hradev/fa_data_hra_dss_genai/basic_rag_demo_payload_request_logs_checkpoints"
# MAGIC new_dir    = "RTS"
# MAGIC full_path  =  os.path.join(parent_dir, new_dir) 
# MAGIC
# MAGIC #create directory
# MAGIC os.mkdir(full_path)
# MAGIC