import json
import os
import pandas as pd

def apply_header_mapping(df, bank_code, country_code, mapping_path='bank_mappings.json'):
    """
    Loads a column mapping from JSON and renames DataFrame columns accordingly.
    """
    try:
        mapping_json = load_config(mapping_path)

        column_mapping = mapping_json.get('bank_mappings', {}).get(bank_code, {}).get(country_code, {})
        # print(f"Column mapping loaded: {column_mapping}")
        # Optionally: Keep only columns defined in the mapping
        df = df[[col for col in df.columns if col in column_mapping]]
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error on applying header mapping: {e}")
        return pd.DataFrame()  # Return the empty DataFrame if mapping fails

    return df.rename(columns=column_mapping)

def load_config(name):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # This gets the root 'transacparser/' dir
    # print(f"Base directory: {base_dir}")
    config_path = os.path.join(base_dir, 'configs', name)
    # print(f"Mapping file path: {name}")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Mapping file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        json_content = json.load(f)
    return json_content


def format_transaction_date(df, bank_country_code, yyyymm):
    """
    Format transaction dates based on bank country code
    
    Args:
        df (pd.DataFrame): DataFrame containing transaction data
        bank_country_code (str): Bank and country code (e.g. 'CIMB_SG')
        yyyymm (str): Year and month in YYYYMM format
        
    Returns:
        pd.DataFrame: DataFrame with formatted dates
    """
    if bank_country_code == "CIMB_SG":
        year = yyyymm[:4]
        df['date'] = df['date'] + f' {year}'
        
        # Convert to datetime[ns]
        df['date'] = pd.to_datetime(df['date'], format='%d %b %Y')
        # print(df['date'].dtypes)  # Check the dtype
        
        # Format to 'dd-mm-yyyy'
        df['date'] = df['date'].dt.strftime('%d-%m-%Y')
    else:
        # print(f"\n{df.columns}")
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce').dt.strftime('%d-%m-%Y')
    
    return df
