# =============================================================================
# EXPLORATION 1 (not part of the pipeline)
# My first script: checks I can connect to the NHSBSA API and read the
# dataset's details. It found 70 monthly files, from November 2020
# (EPD_SNOMED_202011) to August 2026 (EPD_SNOMED_202608).
# =============================================================================
import requests

url = "https://opendata.nhsbsa.net/api/3/action/package_show"
params = {"id": "english-prescribing-dataset-epd-with-snomed-code"}

response = requests.get(url, params=params, timeout=30)
print("Status code:", response.status_code)

data = response.json()
print("Success:", data["success"])
print("Dataset:", data["result"]["title"])
print("Number of monthly files:", len(data["result"]["resources"]))
print("First file:", data["result"]["resources"][0]["name"])
print("Last file:", data["result"]["resources"][-1]["name"])
