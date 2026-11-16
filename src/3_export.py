# EXPORT: write the gold table to a CSV for Tableau

from pathlib import Path

import duckdb

DB_PATH = "data/antibiotics.duckdb"
OUT_DIR = Path("data/exports")
TABLES = ["mart_antibiotics_monthly"]

# Create the exports folder if it doesn't already exist
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Open the database read-only, so exporting can't change the data
con = duckdb.connect(DB_PATH, read_only=True)

# Copy each table to a CSV, with column names in the first row
for table in TABLES:
    path = OUT_DIR / f"{table}.csv"
    con.execute(f"COPY {table} TO '{path}' (HEADER, DELIMITER ',')")
    print(f"Exported {table} to {path}")

con.close()
