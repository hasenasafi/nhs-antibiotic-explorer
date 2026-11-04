import json
from datetime import datetime
from pathlib import Path

import requests

URL = "https://opendata.nhsbsa.net/api/3/action/datastore_search_sql"
RAW_DIR = Path("data/raw")


def build_sql(month):
    return f"""
    SELECT
        YEAR_MONTH,
        REGIONAL_OFFICE_NAME,
        BNF_CHEMICAL_SUBSTANCE_CODE,
        BNF_CHEMICAL_SUBSTANCE,
        SUM(ITEMS) AS total_items,
        SUM(NIC) AS total_nic
    FROM `EPD_SNOMED_{month}`
    WHERE BNF_CHEMICAL_SUBSTANCE_CODE LIKE '0501%'
    GROUP BY YEAR_MONTH, REGIONAL_OFFICE_NAME,
             BNF_CHEMICAL_SUBSTANCE_CODE, BNF_CHEMICAL_SUBSTANCE
    """


def fetch_month(month):
    params = {"resource_id": f"EPD_SNOMED_{month}", "sql": build_sql(month)}
    response = requests.get(URL, params=params, timeout=120)
    response.raise_for_status()
    return response.json()


def save_raw(month, data):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RAW_DIR / f"antibiotics_{month}_{timestamp}.json"
    path.write_text(json.dumps(data, indent=2))
    return path


month = "202608"
data = fetch_month(month)
path = save_raw(month, data)
print("Saved:", path)