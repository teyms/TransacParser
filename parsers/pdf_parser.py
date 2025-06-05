import os
import pandas as pd
import pdfplumber
from dotenv import load_dotenv
import re

load_dotenv()  # Load environment variables from .env


def parse_pdf(input_file, bank_code, country_code, password=None):
    bank_country_code = f"{bank_code}_{country_code}".upper()
    with pdfplumber.open(input_file, password=password) as pdf:
        if len(pdf.pages) > 0:
            print(f"Number of pages: {len(pdf.pages)}")
            headers = pdf.pages[0].extract_table()[0] if pdf.pages[0].extract_table() else []
            print(f"Headers: {headers}")  # Headers

            array_data = []
            for i in range(len(pdf.pages)):
                print(f"Page {i + 1}:") 
                page = pdf.pages[i]

                table = page.extract_table()
                # print(f"\ntable: {table}")  # Tables
                if table is None:
                    print(f"No table found on page {i + 1}. Skipping...")
                    continue

                # Alternatively try extracting text first
                text = page.extract_text()
                # print(text)                

                cimb_sg_formatter(text)  # Format CIMB SG transactions      

                # match bank_country_code:
                #     case "DBS_SG":
                #         print(f"\ntable: {table}")  # Tables
                #     case _:
                #         raise ValueError(f"Unsupported output type: {output_type}")


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
    
# def parse_pdf(input_file, password=None):
#     with pdfplumber.open(input_file, password=password) as pdf:
#         if len(pdf.pages) > 0:
#             # print(f"Number of pages: {len(pdf.pages)}")
#             headers = pdf.pages[0].extract_table()[0] if pdf.pages[0].extract_table() else []
#             print(f"Headers: {headers}")  # Headers

#             array_data = []
#             for i in range(len(pdf.pages)):
#                 print(f"Page {i + 1}:") 
#                 page = pdf.pages[i]

#                 table = page.extract_table()
#                 # print(f"\ntable: {table}")  # Tables

#                 if table is None:
#                     print(f"No table found on page {i + 1}. Skipping...")
#                     continue
#                 transactions = table[1:] if table[0] == headers else table # prevent header duplication
#                 # print(f"\ntransactions: {transactions}")  # transactions

#                 array_data += transactions

#                 # df = pd.DataFrame(array_data, columns=headers)
#                 df = pd.DataFrame(array_data)

#             headers = [header.replace('\n', '_')
#                              .replace(' ', '_')
#                              .upper()  # Clean and format headers
#                              .strip() for header in headers]  # Clean header
#             df.columns = headers
#             return df
#         return pd.DataFrame()  # Return an empty DataFrame if no pages are found


def cimb_sg_formatter(text):
    print(f"\ntext:\n{text}")  # Debugging: print the text content
    # Step 1: Locate the header line
    header_match = re.search(r'^.*DATE\s+TRANSACTION DETAILS.*$', text, re.MULTILINE | re.IGNORECASE)
    header_line = header_match.group(0) if header_match else ""

    # Step 2: Extract everything starting from the first line with a date
    start_match = re.search(r'^\d{2} [A-Za-z]{3} .+', text, flags=re.MULTILINE)

    # Step 3: Cut the text starting from that point
    transaction_section = ""
    if start_match:
        start_pos = start_match.start()
        transaction_section = text[start_pos:]

        # Optionally, stop at the disclaimer or any line that marks the end of transactions
        # e.g., line that contains "Please check through your statement" or "Deposit Insurance Scheme"
        stop_match = re.search(r'(?m)^Pleasecheckthroughyourstatement|^Deposit Insurance Scheme|^Balance carried forward|^D D DDD D D DD D D D', transaction_section)
        if stop_match:
            transaction_section = transaction_section[:stop_match.start()]

    # Step 4: Combine header + transaction block
    result = header_line + "\n" + transaction_section.strip()

    print(f"\nresult:\n{result}")
    