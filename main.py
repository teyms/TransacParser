import os
import pdfplumber
import pandas as pd
import json
from utils.helpers import apply_header_mapping
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

def pdf_formarter(pdf, header_appears_once , password=None):
    with pdfplumber.open(input_file, password=password) as pdf:
        if len(pdf.pages) > 0:
            # print(f"Number of pages: {len(pdf.pages)}")
            headers = pdf.pages[0].extract_table()[0]
            array_data = []
            for i in range(len(pdf.pages)):
                print(f"Page {i + 1}:") 
                page = pdf.pages[i]
                table = page.extract_table()

                # skip header for first page, to get only the transactions data
                if i == 0 or not header_appears_once: 
                    transactions = table[1:]
                else:
                    transactions = table
                # print(transactions)  # Tables
                array_data += transactions
                # print(f"Number of pages: {len(pdf.pages)}")
                # print(f"Metadata: {pdf.metadata}")    
                # print(page.extract_text())  # Text
                print()
                # print(transactions)  # Tables
                # print(json_data)  # Tables
                df = pd.DataFrame(array_data, columns=headers)
                # print(df)  # Tables
            # print(headers)

            return df
        return pd.DataFrame()  # Return an empty DataFrame if no pages are found


if __name__ == "__main__":
    input_file = os.getenv("INPUT_FILE", "xxx.pdf")  # Fallback to "default.csv"
    bank_name = os.getenv("BANK_NAME", "DBS")           # Fallback to "DBS"
    password = os.getenv("PDF_PASSWORD", 'password')  # Optional password for PDF files

    print(f"PDF loaded successfully: {os.path.exists(input_file)}")

    df = pdf_formarter(input_file, True, password=password)
    # Apply header mapping
    df = apply_header_mapping(df, 'TNG_MY', mapping_path='bank_mappings.json')
    print(df)
    # Convert to JSON string
    json_str = df.to_json(orient='records')
    print('\n'+json_str)