import os
import pandas as pd
from dotenv import load_dotenv
import re
from datetime import datetime

load_dotenv()  # Load environment variables from .env


def parse_excel(input_file, bank_country_code, password=None):
    # print(f"bank_country_code: {bank_country_code}")
    # df = pd.read_excel(input_file, engine='openpyxl')
    df = pd.read_csv(input_file)
    headers = df.columns.tolist()  # Get headers from the DataFrame
    headers = [header.replace('\n', '_')
                    .replace(' ', '_')
                    .upper()  # Clean and format headers
                    .strip() for header in headers]  # Clean header
    df.columns = headers
    # print(f"DataFrame loaded with headers: {df.head()}")
    # print(f"DataFrame loaded with Date: {df['Date']}")
    # print(f"DataFrame loaded with shape: {df.shape}")

    return df