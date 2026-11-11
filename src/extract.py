# =============================================================================
# EXTRACT: get antibiotic prescribing data from the NHSBSA API
#
# For each month, this script asks the NHS server to filter the English
# Prescribing Dataset down to antibiotics (BNF section 5.1) and add them up
# by region. Each month's answer is saved, untouched, as a timestamped JSON
# file in data/raw/. This is the source for the bronze layer.
#
# Run it only when you want fresh data: python src/extract.py
# =============================================================================

import json                      # to save the API's answer as a JSON file
import logging                   # to record what happened, with timestamps
import time                      # to pause between requests and retries
from datetime import datetime    # to timestamp each saved file
from pathlib import Path         # to work with folder and file paths

import requests                  # to send requests to the API (installed via requirements.txt)

# --- Settings -----------------------------------------------------------------
# Kept at the top so they can be changed without touching the code below.

# The API "action" that runs my SQL query on the NHS server
SQL_URL = "https://opendata.nhsbsa.net/api/3/action/datastore_search_sql"
# The API "action" that returns rows, used here only to read column names
SEARCH_URL = "https://opendata.nhsbsa.net/api/3/action/datastore_search"

RAW_DIR = Path("data/raw")       # where the raw JSON files are saved
START_MONTH = "202309"           # first month to extract (Sep 2023)
END_MONTH = "202608"             # last month to extract (Aug 2026)
MAX_ATTEMPTS = 3                 # how many times to try a request before giving up

# Every log line shows the time, the level (INFO or WARNING) and the message
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def months_between(start, end):
    """Return every month from start to end, e.g. ["202309", "202310", ...]."""
    months = []
    year, month = int(start[:4]), int(start[4:])   # split "202309" into 2023 and 9
    while f"{year}{month:02d}" <= end:              # :02d keeps two digits, e.g. "09"
        months.append(f"{year}{month:02d}")
        month += 1
        if month == 13:                             # after December, roll into January
            month = 1
            year += 1
    return months


def get_columns(month):
    """Ask the API for one row, and return that month's column names.

    Needed because the NHS changed the column names partway through the
    dataset (schema drift), so older and newer months have different layouts.
    """
    params = {"resource_id": f"EPD_SNOMED_{month}", "limit": 1}
    response = requests.get(SEARCH_URL, params=params, timeout=60)
    response.raise_for_status()                     # stop if the server returned an error
    return [field["id"] for field in response.json()["result"]["fields"]]


def build_sql(month, columns):
    """Build the SQL query for one month, using that month's column layout."""

    # Schema drift: in newer months the drug code is BNF_CHEMICAL_SUBSTANCE_CODE.
    # In older months, BNF_CHEMICAL_SUBSTANCE holds the CODE instead, and the
    # drug name is in CHEMICAL_SUBSTANCE_BNF_DESCR. Pick the right pair.
    if "BNF_CHEMICAL_SUBSTANCE_CODE" in columns:
        code_col = "BNF_CHEMICAL_SUBSTANCE_CODE"
        name_col = "BNF_CHEMICAL_SUBSTANCE"
    else:
        code_col = "BNF_CHEMICAL_SUBSTANCE"
        name_col = "CHEMICAL_SUBSTANCE_BNF_DESCR"

    # The query runs on the NHS server, so only ~400 rows come back per month
    # instead of ~17 million.
    # - AS bnf_code / AS bnf_name: same output names whatever the layout
    # - CAST(... AS FLOAT64): from March 2025 ITEMS and NIC arrive as text,
    #   so convert them to numbers before adding them up
    # - LIKE '0501%': BNF codes starting 0501 are antibiotics (BNF section 5.1)
    # - GROUP BY: add up all GP practices into one row per region and drug
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
    """Send the query to the API, retrying temporary failures."""
    params = {"resource_id": f"EPD_SNOMED_{month}", "sql": sql}
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(SQL_URL, params=params, timeout=120)

            # A 4xx error means my request is wrong (e.g. a bad column name).
            # Asking again won't fix it, so stop straight away and show the
            # server's explanation.
            if 400 <= response.status_code < 500:
                raise RuntimeError(f"{month}: request rejected: {response.text[:500]}")

            response.raise_for_status()             # stop on 5xx server errors (retried below)
            return response.json()

        # Temporary problems (timeouts, dropped connections, 5xx errors):
        # log a warning, wait, and try again
        except (requests.RequestException, ValueError) as error:
            logging.warning(f"{month}: attempt {attempt} failed: {error}")
            if attempt == MAX_ATTEMPTS:
                raise                               # out of attempts: stop with the real error
            time.sleep(5 * attempt)                 # backoff: wait 5s, then 10s


def save_raw(month, data):
    """Save the API's answer, untouched, as a timestamped JSON file.

    Files are never overwritten, so every pull is kept. The silver layer
    later keeps only the latest pull for each month.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)      # create data/raw if it doesn't exist
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RAW_DIR / f"antibiotics_{month}_{timestamp}.json"
    path.write_text(json.dumps(data, indent=2))
    return path


# --- Main loop: run every step for each month ---------------------------------
for month in months_between(START_MONTH, END_MONTH):
    logging.info(f"{month}: requesting")
    columns = get_columns(month)                    # 1. find this month's layout
    sql = build_sql(month, columns)                 # 2. build the matching query
    data = fetch_month(month, sql)                  # 3. run it on the NHS server
    rows = len(data["result"]["result"]["records"]) # note: results are nested twice
    path = save_raw(month, data)                    # 4. save the untouched answer
    logging.info(f"{month}: saved {rows} rows to {path}")
    time.sleep(1)                                   # pause 1s to be polite to the server