import requests

url = "https://opendata.nhsbsa.net/api/3/action/datastore_search"
params = {"resource_id": "EPD_SNOMED_202608", "limit": 1}

response = requests.get(url, params=params, timeout=60)
print("Status code:", response.status_code)

data = response.json()

print("\nColumn names:")
for field in data["result"]["fields"]:
    print(field["id"])

print("\nOne example row:")
print(data["result"]["records"][0])