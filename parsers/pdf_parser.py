import os
import pandas as pd
import pdfplumber
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env


def parse_pdf(input_file, password=None):
    with pdfplumber.open(input_file, password=password) as pdf:
        if len(pdf.pages) > 0:
            # print(f"Number of pages: {len(pdf.pages)}")
            headers = pdf.pages[0].extract_table()[0] if pdf.pages[0].extract_table() else []
            # print(f"Headers: {headers}")  # Headers

            array_data = []
            for i in range(len(pdf.pages)):
                print(f"Page {i + 1}:") 
                page = pdf.pages[i]

                table = page.extract_table()
                # print(f"\ntable: {table}")  # Tables

                if table is None:
                    print(f"No table found on page {i + 1}. Skipping...")
                    continue
                transactions = table[1:] if table[0] == headers else table # prevent header duplication
                # print(f"\ntransactions: {transactions}")  # transactions

                array_data += transactions

                # df = pd.DataFrame(array_data, columns=headers)
                df = pd.DataFrame(array_data)

            headers = [header.replace('\n', '_')
                             .replace(' ', '_')
                             .upper()  # Clean and format headers
                             .strip() for header in headers]  # Clean header
            df.columns = headers
            return df
        return pd.DataFrame()  # Return an empty DataFrame if no pages are found
    