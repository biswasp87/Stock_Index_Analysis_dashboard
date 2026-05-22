import pandas as pd
import numpy as np
from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError

def load_data():
    project_id = "phrasal-fire-373510"
    table_id = "phrasal-fire-373510.Big_Bull_Analysis.Master_Data_Indices"

    try:
        client = bigquery.Client()
        query = f"SELECT * FROM `{table_id}` ORDER BY Date DESC"
        df = client.query(query).to_dataframe()
        print("Data loaded from BigQuery")
        return df
    except (DefaultCredentialsError, Exception) as e:
        print(f"Failed to load data from BigQuery: {e}")
        print("Loading mock data instead...")
        return generate_mock_data()

def generate_mock_data():
    indices = ["Nifty50", "SENSEX", "Nifty Bank", "Nifty IT", "Nifty Auto"]
    dates = pd.date_range(end=pd.Timestamp.now(), periods=500, freq='D')

    data = []
    for index in indices:
        # Generate some random walk data
        values = 10000 + np.cumsum(np.random.normal(0, 50, len(dates)))
        if index == "SENSEX":
            values = 60000 + np.cumsum(np.random.normal(0, 300, len(dates)))
        elif index == "Nifty50":
            values = 18000 + np.cumsum(np.random.normal(0, 100, len(dates)))

        for d, v in zip(dates, values):
            data.append({
                "Date": d,
                "Index_Name": index,
                "Close_Index_Value": v
            })

    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])
    return df
