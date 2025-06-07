import os
import pandas as pd
import pdfplumber
from dotenv import load_dotenv
import re
from datetime import datetime

load_dotenv()  # Load environment variables from .env


def parse_pdf(input_file, bank_country_code, password=None):
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

                match bank_country_code:
                    case "CIMB_SG":
                        # Alternatively try extracting text first
                        text = page.extract_text()
                        print(text)                
                        df_cimb_sg = cimb_sg_formatter(text)  # Format CIMB SG transactions  
                        if df_cimb_sg.empty:
                            print(f"No transactions found on page {i + 1}. Skipping...")
                            continue
                        headers = df_cimb_sg.columns.tolist()  # Get headers from the formatted DataFrame
                        transactions = df_cimb_sg.values.tolist()  # Get transactions from the formatted DataFrame
                    case _:
                        transactions = table[1:] if table[0] == headers else table # prevent header duplication

                array_data += transactions

            df = pd.DataFrame(array_data)

            headers = [header.replace('\n', '_')
                             .replace(' ', '_')
                             .upper()  # Clean and format headers
                             .strip() for header in headers]  # Clean header
            df.columns = headers
            return df
        return pd.DataFrame()  # Return an empty DataFrame if no pages are found

def cimb_sg_formatter(text):
    # Step 1: Locate the header line
    header_match = re.search(r'^.*DATE.*TRANSACTION DETAILS.*$', text, re.MULTILINE | re.IGNORECASE)    
    # header_line = header_match.group(0) if header_match else ""
    header_line = header_match.group(0) if header_match else None  # Return an empty DataFrame if no header found
    if not header_line:
        print("No header line found in the text.")
        return pd.DataFrame()
    header_parts = header_line.split()
    final_header = [header_parts[0], ' '.join(header_parts[1:3]), *header_parts[3:]]
    # print(f"\ncolumns_line:\n{final_header}")  # Debugging: print the header line

    # Step 2: Extract everything starting from the first line with a date
    start_match = re.search(r'^\d{2} [A-Za-z]{3} .+', text, flags=re.MULTILINE)

    # Step 3: Extract only the transaction section
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
    transaction_records = header_line + "\n" + transaction_section.strip()
    # print(f"\ntransaction_records representation:\n{repr(transaction_records)}")  # Debugging: print the text content

    transaction_records = transaction_records.split('\n')[1:] # Skip the header line
    # print(f"\transaction_records length:\n{len(transaction_records)}\n")
    # print(f"\transaction_records Result:\n{transaction_records}\n")

    date_pattern = r"\d{2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    desc_pattern = r"^(.*?)\s+\d{1,3}(?:,\d{3})*\.\d{2}"
    amount_pattern = r"\d{1,3}(?:,\d{3})*\.\d{2}"
    df = pd.DataFrame(columns=final_header)

    prev_amount = 0 #Use to calculate the difference in amounts
    prev_date = None # Use to keep track of the last date for records without a date

    for i, line in enumerate(transaction_records):
        if line.strip() == "": # Skip empty lines
            continue

        str_date = re.findall(date_pattern, line)
        if len(str_date) > 0:
            # new record with date
            str_without_date = re.sub(date_pattern, "", line)

            # Extract everything before the FIRST amount (e.g., "Service Fee")
            #    - Use \s+ to ensure the amount is separated by whitespace            
            desc_match = re.search(desc_pattern, str_without_date)
            str_desc = desc_match.group(1).strip()

            str_amounts = str_without_date.replace(desc_match.group(1).strip(), "").replace(",", "")
            str_amount_lists = str_amounts.split()
            num_amount_lists = [float(num.replace(',', '')) for num in str_amount_lists]           
            amount = num_amount_lists[-1] - prev_amount
        else:
            str_amount_lists = re.findall(amount_pattern, line)
            if len(str_amount_lists) > 0:
                # if no date but got amount, then it is a new record 
                str_date = [prev_date]
                desc_match = re.search(desc_pattern, line)
                str_desc = desc_match.group(1).strip()                
                num_amount_lists = [float(num.replace(',', '')) for num in str_amount_lists]        
                amount = num_amount_lists[-1] - prev_amount           
            else:
                # if no date and no amount, then it is the desc for the previous record
                str_desc = line.strip()
                df.at[df.index[-1], 'TRANSACTION DETAILS'] += f' {str_desc}' # Append to the previous record's description
                continue #skip to next iteration, since its the leftover desc for the previous record

        new_row = {
            'DATE': [str_date[0]],
            'TRANSACTION DETAILS': [str_desc],
            'WITHDRAWAL': [amount if len(num_amount_lists) > 0 and amount < 0 else 0],
            'DEPOSIT': [amount if len(num_amount_lists) > 0 and amount > 0 else 0],
            'BALANCE': [num_amount_lists[-1]]
        }        

        df = pd.concat([df, pd.DataFrame(new_row)], ignore_index=True)
        if len(num_amount_lists) > 0:
            prev_amount = num_amount_lists[-1]           
        prev_date = str_date[0]          
    # print(df)
    return df