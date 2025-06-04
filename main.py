import os
import json
from utils.helpers import apply_header_mapping
from dotenv import load_dotenv
from datetime import datetime
from parsers import parse_pdf
from exporter import json_exporter

load_dotenv()  # Load environment variables from .env

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

if __name__ == "__main__":
    input_file = os.getenv("INPUT_FILE", "xxx.pdf")  # Fallback to "default.csv"
    bank_name = os.getenv("BANK_NAME", "DBS")           # Fallback to "DBS"
    password = os.getenv("PDF_PASSWORD", 'password')  # Optional password for PDF files
    country_code = os.getenv("COUNTRY_CODE", "MY")  # Fallback to "MY"
    bank_code = os.getenv("BANK_CODE", "TNG")  # Fallback to "TNG"
    bank_code = os.getenv("BANK_CODE", "PBB")  # Fallback to "TNG"


    output_type = os.getenv("OUTPUT_TYPE", "json")  # Fallback to "json"
    # output_filename = os.getenv("OUTPUT_FILENAME", None)  # Fallback to "json"

    print(f"PDF loaded successfully: {os.path.exists(input_file)}")

    df = parse_pdf(input_file, password=password)
    print(f"\n{df}")
    
    # Apply header mapping
    df = apply_header_mapping(df, bank_code, country_code, mapping_path='bank_mappings.json')
    # print(df)
    # # Convert to JSON string
    # json_str = df.to_json(orient='records')
    # print('\n'+json_str)
    output_filename = f"{bank_code}_{country_code}_output_"  # Default filename
    output_manager(df, output_type=output_type, filename=output_filename)
