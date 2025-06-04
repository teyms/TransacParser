
import json
import os
import pandas as pd

def apply_header_mapping(df, bank_code, country_code, mapping_path='bank_mappings.json'):
    """
    Loads a column mapping from JSON and renames DataFrame columns accordingly.
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # This gets the root 'transacparser/' dir
        print(f"Base directory: {base_dir}")
        mapping_path = os.path.join(base_dir, 'configs', mapping_path)
        print(f"Mapping file path: {mapping_path}")

        if not os.path.exists(mapping_path):
            raise FileNotFoundError(f"Mapping file not found: {mapping_path}")
        
        with open(mapping_path, 'r') as f:
            column_mapping = json.load(f)

        column_mapping = column_mapping.get('bank_mappings', {}).get(bank_code, {}).get(country_code, {})
        print(f"Column mapping loaded: {column_mapping}")
        # Optionally: Keep only columns defined in the mapping
        df = df[[col for col in df.columns if col in column_mapping]]
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error on applying header mapping: {e}")
        return pd.DataFrame()  # Return the empty DataFrame if mapping fails

    return df.rename(columns=column_mapping)
