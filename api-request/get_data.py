import requests
import os
import pandas as pd
import json
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('API_KEY')
API_URL = os.getenv('API_URL')
print("API KEY:", API_KEY)
print("API URL:", API_URL)

def request_data(url,key,ticker,multiplier,timespan,start='2025-05-06',end='2026-05-06'):
    url = f"{url}{ticker}/range/{multiplier}/{timespan}/{start}/{end}"
    params ={
        'apiKey': key
    }
    try:
        response =requests.get(url=url,params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error fetching data", e)
        return None
        
    else:
        data = response.json()['results']
        return data
def mock_data():
    with open('./example_data.txt','r') as f:
        data = json.load(f)
        data = pd.DataFrame(data)
        col =['ticker'] + data.columns.to_list()  
        data['ticker'] = 'AAPL'
        data = data[col]
        return data
