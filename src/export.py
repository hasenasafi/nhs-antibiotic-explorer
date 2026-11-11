# =============================================================================
# EXPORT: hand the gold table to Tableau
#
# Copies the gold table out of DuckDB into a CSV file in data/exports/.
# Tableau Public can't connect to a DuckDB file directly, but it reads CSV,
# so this is the "serve" step that gets the data to the dashboard.
#
# Run with: python src/export.py (or the whole pipeline: python src/run.py)
# =============================================================================

from pathlib import Path          # to work with the export folder

import duckdb                     # the database (installed via requirements.txt)

DB_PATH = "data/antibiotics.duckdb"   # the database built by transform.py
OUT_DIR = Path("data/exports")        # where the CSV files are saved

# The tables to export. Only the gold table is needed: the bronze and silver tables are intermediate steps.
# To export another table later, add its name to this list.
TABLES = ["mart_antibiotics_monthly"]

OUT_DIR.mkdir(parents=True, exist_ok=True)       # create data/exports if it doesn't exist

# read_only=True: the export only reads the data, so it can never change it
con = duckdb.connect(DB_PATH, read_only=True)

for table in TABLES:
    path = OUT_DIR / f"{table}.csv"        # Builds the file path, e.g. data/exports/mart_antibiotics_monthly.csv
    # COPY ... TO writes a whole table to a file in one step.
    # HEADER puts the column names in the first row (Tableau uses them as field names).
    con.execute(f"COPY {table} TO '{path}' (HEADER, DELIMITER ',')")        #HEADER: put the column names on the first row, DELIMITER ',': separate the values with commas
    print(f"Exported {table} to {path}")

con.close()                                      # release the database file