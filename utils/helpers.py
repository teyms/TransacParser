import json
import os
import pandas as pd

def apply_header_mapping(df, bank_code, country_code, mapping_path='bank_mappings.json'):
    """
    Loads a column mapping from JSON and renames DataFrame columns accordingly.
    """
    try:
        mapping_json = load_config(mapping_path)
        # print(f"df before applying header mapping: {df.columns}")  # Debugging line to check DataFrame before mapping
        column_mapping = mapping_json.get('bank_mappings', {}).get(bank_code, {}).get(country_code, {})
        # print(f"Column mapping loaded: {column_mapping}")
        # Optionally: Keep only columns defined in the mapping
        df = df[[col for col in df.columns if col in column_mapping]]
        # print(f"DataFrame after filtering columns: {df.head()}")  # Debugging line to check DataFrame after filtering   
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
        # Try common date formats for other banks
        date_formats = [
            '%d-%m-%Y',   # Day-month-year
            '%d/%m/%Y',    # Day/month/year
            '%Y-%m-%d',    # Year-month-day
            '%Y/%m/%d',    # Year/month/day
            '%m/%d/%Y',    # Month/day/year (US format)
            '%b %d, %Y',   # "Jan 01, 2023"
            '%d %b %Y',    # "01 Jan 2023"
            '%B %d, %Y',   # "January 01, 2023"
        ]
        
        # Try each format until one works
        for fmt in date_formats:
            try:
                df['date'] = pd.to_datetime(df['date'], format='%d %b %Y', errors='raise')
                break
            except ValueError:
                continue
        else:
            # If none of the formats worked, fall back to dayfirst=True
            df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    
    # Format all dates consistently to 'dd-mm-yyyy'
    df['date'] = df['date'].dt.strftime('%d-%m-%Y')
    
    
    return df

def standardize_output_records(df, bank_country_code):
    """
    Standardize output records ensuring all the output columsn from diff banks are output in the same format
    
    Args:
        df (pd.DataFrame): DataFrame containing transaction data
    
    Returns:
        pd.DataFrame: DataFrame with standardized columns
    """
    # Define the standard columns
    standard_columns = [
        'date', 'description', 'amount', 'currency', 'balance', 'bank_type', 'status'
    ]

    currency_mapping = {
        'MY': 'MYR',
        'SG': 'SGD',
    }
    # print(f"bank_country_code: {bank_country_code}")
    # print(f"df: {df}")

    # get country code from bank_country_code
    bank_country_code_split = bank_country_code.split('_')  # Extract country code from bank_country_code
    
    # Ensure all standard columns are present
    for col in standard_columns:
        

            match bank_country_code.strip():
                case "TNG_MY":                    
                    if col not in df.columns: # create missing columns
                        if col == 'currency': df[col] = currency_mapping[bank_country_code_split[-1]]
                        elif col == 'bank_type': df[col] = bank_country_code_split[0]
                        else: df[col] = pd.NA
                    else: # reformat existing columns
                        if col == 'amount': 
                            df['amount'] = (
                                df['amount']
                                .astype(str)
                                .str.replace(',', '', regex=False)
                                .str.replace('RM', '', regex=False)
                                .apply(pd.to_numeric, errors='coerce')  # Convert to numeric, invalid values will be NaN
                            )  
                            # Mark specific transaction types as negative or positive based on transaction type
                            debit_trans_type = ['DUITNOW_RECEI']
                            df['amount'] = df.apply(
                                lambda row: +row['amount'] if any(keyword in row['transaction_type'] for keyword in debit_trans_type) 
                                            else -row['amount'],
                                axis=1
                            )                        
                            df[col] = df['amount']  # Use 'amount' column directly       
                        elif col == 'balance':
                            df['balance'] = (
                                df['balance']
                                .astype(str)
                                .str.replace(',', '', regex=False)
                                .str.replace('RM', '', regex=False)
                                .apply(pd.to_numeric, errors='coerce')  # Convert to numeric, invalid values will be NaN
                            )  
                            df[col] = df['balance']  # Use 'balance' column directly                                   
                            # print(f"df['balance'] after conversion:\n{df['balance']}")  # Debugging line to check 'amount' column



                case "PBB_MY":
                    if col not in df.columns:
                        if col == 'currency': df[col] = currency_mapping[bank_country_code_split[-1]]
                        elif col == 'bank_type': df[col] = bank_country_code_split[0]
                        elif col == 'amount': 
                            # Ensure both 'amount+' and 'amount-' columns are converted to numeric
                            df['amount+'] = (
                                df['amount+']
                                .astype(str)
                                .str.replace(',', '', regex=False)
                                .apply(pd.to_numeric, errors='coerce')  # Convert to numeric, invalid values will be NaN
                            )

                            df['amount-'] = (
                                df['amount-']
                                .astype(str)
                                .str.replace(',', '', regex=False)
                                .apply(pd.to_numeric, errors='coerce')  # Convert to numeric, invalid values will be NaN
                            )

                            # Combine 'amount+' and 'amount-' into 'amount'
                            df[col] = df['amount+'].fillna(0) - df['amount-'].fillna(0)  # 'amount+' minus 'amount-' (negate the 'amount-')          
                        else:
                            df[col] = pd.NA
                case _:    
                    df[col] = pd.NA  # Add missing columns with NA values
    
    # Reorder the DataFrame to match the standard columns
    df = df[standard_columns]
    
    return df
