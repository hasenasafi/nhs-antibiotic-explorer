import json
import logging
import time
from datetime import datetime
from pathlib import Path

import requests

SQL_URL = "https://opendata.nhsbsa.net/api/3/action/datastore_search_sql"
SEARCH_URL = "https://opendata.nhsbsa.net/api/3/action/datastore_search"
RAW_DIR = Path("data/raw")
START_MONTH = "202409"
END_MONTH = "202608"
MAX_ATTEMPTS = 3

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def months_between(start, end):
    months = []
    year, month = int(start[:4]), int(start[4:])
    while f"{year}{month:02d}" <= end:
        months.append(f"{year}{month:02d}")
        month += 1
        if month == 13:
            month = 1
            year += 1
    return months


def get_columns(month):
    params = {"resource_id": f"EPD_SNOMED_{month}", "limit": 1}
    response = requests.get(SEARCH_URL, params=params, timeout=60)
    response.raise_for_status()
    return [field["id"] for field in response.json()["result"]["fields"]]


def build_sql(month, columns):
    if "BNF_CHEMICAL_SUBSTANCE_CODE" in columns:
        code_col = "BNF_CHEMICAL_SUBSTANCE_CODE"
        name_col = "BNF_CHEMICAL_SUBSTANCE"
    else:
        code_col = "BNF_CHEMICAL_SUBSTANCE"
        name_col = "CHEMICAL_SUBSTANCE_BNF_DESCR"

    return f"""
    SELECT
        YEAR_MONTH,
        REGIONAL_OFFICE_NAME,
        {code_col} AS bnf_code,
        {name_col} AS bnf_name,
        SUM(CAST(ITEMS AS FLOAT64)) AS total_items,
        SUM(CAST(NIC AS FLOAT64)) AS total_nic
    FROM `EPD_SNOMED_{month}`
    WHERE {code_col} LIKE '0501%'
    GROUP BY YEAR_MONTH, REGIONAL_OFFICE_NAME, {code_col}, {name_col}
    """


def fetch_month(month, sql):
    params = {"resource_id": f"EPD_SNOMED_{month}", "sql": sql}
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(SQL_URL, params=params, timeout=120)
            if 400 <= response.status_code < 500:
                raise RuntimeError(f"{month}: request rejected: {response.text[:500]}")
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as error:
            logging.warning(f"{month}: attempt {attempt} failed: {error}")
            if attempt == MAX_ATTEMPTS:
                raise
            time.sleep(5 * attempt)


def save_raw(month, data):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RAW_DIR / f"antibiotics_{month}_{timestamp}.json"
    path.write_text(json.dumps(data, indent=2))
    return path


for month in months_between(START_MONTH, END_MONTH):
    logging.info(f"{month}: requesting")
    columns = get_columns(month)
    sql = build_sql(month, columns)
    data = fetch_month(month, sql)
    rows = len(data["result"]["result"]["records"])
    path = save_raw(month, data)
    logging.info(f"{month}: saved {rows} rows to {path}")
    time.sleep(1) 

    