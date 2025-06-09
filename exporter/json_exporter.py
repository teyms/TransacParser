import json
import os
from datetime import datetime

# Generate timestamp (YearMonthDayHourMinuteSecond)
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # Now includes seconds
default_filename = f"output_{timestamp}.json"
def json_exporter(df, filename=default_filename):
    filename += f'{timestamp}.json'  # Ensure the filename ends with .json
    # Convert to JSON string
    json_str = df.to_json(orient='records')
    # print('\n'+json_str)
    # Save to a JSON file
    with open(f'./data/processed/{filename}', 'w') as f:
        json.dump(json.loads(json_str), f, indent=4)  # indent for pretty formatting
    print(f"Data saved to ./data/processed/{filename}")
    return filename  # Return the filename for further use if needed