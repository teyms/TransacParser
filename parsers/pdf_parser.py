import os
import pandas as pd
import pdfplumber
from dotenv import load_dotenv
import re
from datetime import datetime

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
                print(f"\ntable: {table}")  # Tables
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
    # print(f"\ntext:\n{text}")  # Debugging: print the text content
    # print(f"\ntext:\n{repr(text)}")  # Debugging: print the text content

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
    print(f"\nresult representation:\n{repr(result)}")  # Debugging: print the text content


    split_result = result.split('\n')
    print(f"\nSplit length:\n{len(split_result)}\n")
    print(f"\nSplit Result:\n{split_result}\n")

    pattern = r"\d{2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    matches = re.findall(pattern, split_result[2])
    print(f"\nDate:{matches}\n")


    # Extract everything before the FIRST amount (e.g., "Service Fee")
    #    - Use \s+ to ensure the amount is separated by whitespace
    string_without_date = re.sub(pattern, "", split_result[2])
    desc_pattern = r"^(.*?)\s+\d{1,3}(?:,\d{3})*\.\d{2}"
    match = re.search(desc_pattern, string_without_date)
    text_before_amount = match.group(1).strip()
    print("text_before_amount:", text_before_amount)  # Output: "Service Fee"

    string_without_desc = re.sub(desc_pattern, "", string_without_date)
    print("all_amount:", string_without_desc)  # Output: "Service Fee"


    return None # for testing only

    for i, line in enumerate(split_result):
        if line.strip() == "":
            split_result[i] = "EMPTY_LINE"
        else:
            split_result[i] = line.split()

    print(f"\nSplit length x 2 :\n{len(split_result)}\n")
    print(f"\nSplit Result x 2:\n{split_result}\n")

    print(f"\nresult:\n{result}")
    