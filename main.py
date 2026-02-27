import os
import json
from utils.helpers import apply_header_mapping, load_config, format_transaction_date, standardize_output_records
from dotenv import load_dotenv
from datetime import datetime, timedelta
from parsers import parse_pdf, parse_excel
from exporter import json_exporter, csv_exporter
import pandas as pd

DEFAULT_FILE_TYPE = 'csv'  # Default file type
load_dotenv()  # Load environment variables from .env
GLOBAL_CONFIG = load_config('config.json')

def output_manager(df, output_type="json", filename=None):
    """
    Manages the output format of the DataFrame.
    Currently supports JSON output.
    """
    match output_type:
        case "json":
            return json_exporter(df, filename)
        case _:
            raise ValueError(f"Unsupported output type: {output_type}")

def readFile(filePath, filename):
    # check if the file exists with the current extension
    input_file = os.path.join(filePath, filename)
    print(f"\nChecking file: {input_file}")
    if os.path.exists(input_file):
        print(f"Using file: {input_file}")
        return input_file
    return None

if __name__ == "__main__":
#     input_file = os.getenv("INPUT_FILE", "xxx.pdf")  # Fallback to "default.csv"
#     bank_name = os.getenv("BANK_NAME", "DBS")           # Fallback to "DBS"
    password = os.getenv("PDF_PASSWORD", 'password')  # Optional password for PDF files
#     country_code = os.getenv("COUNTRY_CODE", "MY")  # Fallback to "MY"
#     country_code = os.getenv("COUNTRY_CODE", "SG")  # Fallback to "SG"
#     bank_code = os.getenv("BANK_CODE", "TNG")  # Fallback to "TNG"
#     bank_code = os.getenv("BANK_CODE", "PBB")  # Fallback to "PBB"
#     bank_code = os.getenv("BANK_CODE", "DBS")  # Fallback to "DBS"
#     bank_code = os.getenv("BANK_CODE", "CIMB")  # Fallback to "CIMB"
#     output_type = os.getenv("OUTPUT_TYPE", "json")  # Fallback to "json"
#     # output_filename = os.getenv("OUTPUT_FILENAME", None)  # Fallback to "json"

# ###########################################################################
    file_type = DEFAULT_FILE_TYPE  # Default file type
    folder_path = load_config('folder_paths.json')    
    source_paths = folder_path.get('folder_paths', {}).get("source", {})

    prev_month_date = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y%m")
    # print('prev_month_date', prev_month_date)
    # prev_month_date = '202512'
    yyyymm = prev_month_date if GLOBAL_CONFIG["read_date_format"]["format"] is None else GLOBAL_CONFIG["read_date_format"]["format"]
    all_dfs = []
    standardize_headers = None
    # raise KeyError # for testing purposes
    for key, value in source_paths.items():
        bank_country_code = f"{key.upper()}"
        filename_no_ext = f"{bank_country_code}_{yyyymm}"
        extension_priority = GLOBAL_CONFIG["read_extension_priority"]
        # set the `filename` extension based on the priority, and if file available then use it and skip for the rest extensions, otherwise continue to the next extension
        # the extension should follow the array get from `read_extension_priority` in the config.json
        for ext in extension_priority:
            filename = f"{filename_no_ext}.{ext}"
            currFile = readFile(value, filename)
            if currFile != None:
                input_file = currFile
                file_type = ext  # Update file type based on the found file
                break # if get file then no need to search/read for new file with diff ext
        
        match file_type:
            case "pdf":
                df = parse_pdf(input_file, bank_country_code, password=password)
            case "csv":
                df = parse_excel(input_file, bank_country_code, password=password)
        # print(f"\n{df}")    
        # print(f"\n{df.columns}")    

        
        bank_code = bank_country_code.split('_')[0]  # Extract bank code from the key
        country_code = bank_country_code.split('_')[1]  # Extract country code from the key
        # Apply header mapping
        df = apply_header_mapping(df, bank_code, country_code, mapping_path='bank_mappings.json')
        # print(f"\n{df}") 
        df = format_transaction_date(df, bank_country_code, yyyymm)
        # print(f"\n{df}") 
        df = standardize_output_records(df, bank_country_code)
        # print(f"\n{df}") 
        standardize_headers = df.columns

        ##################################################################################
        #####                     SHOULD HAVE MOVE TO A FUNCTION                     #####
        ##################################################################################
        all_dfs.append(df)
        #################################################################################

        output_type = GLOBAL_CONFIG["output"]["file_format"]
        output_filename = f"{bank_code}_{country_code}_output_"  # Default filename
        output_manager(df, output_type=output_type, filename=output_filename)  
    merged_df = pd.concat(all_dfs, ignore_index=True)
    merged_df.columns = standardize_headers    
    # Save to CSV
    csv_exporter(merged_df)
    # print(merged_df)      
