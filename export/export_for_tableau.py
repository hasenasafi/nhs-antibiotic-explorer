from pathlib import Path

import duckdb

DB_PATH = "data/antibiotics.duckdb"
OUT_DIR = Path("data/exports")
TABLES = ["mart_antibiotics_monthly", "mart_broad_spectrum_by_region"]

OUT_DIR.mkdir(parents=True, exist_ok=True)
con = duckdb.connect(DB_PATH, read_only=True)

for table in TABLES:
    path = OUT_DIR / f"{table}.csv"
    con.execute(f"COPY {table} TO '{path}' (HEADER, DELIMITER ',')")
    print(f"Exported {table} to {path}")

con.close()