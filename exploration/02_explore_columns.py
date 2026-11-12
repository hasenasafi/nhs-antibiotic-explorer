# =============================================================================
# EXPLORATION 2 (not part of the pipeline)
# Asks the API for one row and prints the column names. Running it for an
# older month (Sep 2024) and a newer month (Aug 2026) showed the NHS had
# renamed its columns (schema drift), which extract.py now handles.
# =============================================================================
import requests

url = "https://opendata.nhsbsa.net/api/3/action/datastore_search"
params = {"resource_id": "EPD_SNOMED_202409", "limit": 1}

response = requests.get(url, params=params, timeout=60)
print("Status code:", response.status_code)

data = response.json()

print("\nColumn names:")
for field in data["result"]["fields"]:
    print(field["id"])

print("\nOne example row:")
print(data["result"]["records"][0])