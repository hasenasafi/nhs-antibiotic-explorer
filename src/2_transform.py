# TRANSFORM: build the DuckDB database by running the SQL layers in order:
# bronze (load raw JSON), silver (clean), gold (final table for Tableau).

from pathlib import Path

import duckdb

DB_PATH = "data/antibiotics.duckdb"
SQL_DIR = Path("sql")

# Open the database (created if it doesn't exist)
con = duckdb.connect(DB_PATH)

# Run every SQL file in number order: 01 bronze, 02 silver, 03 gold
for sql_file in sorted(SQL_DIR.glob("*.sql")):
    print(f"Running {sql_file.name}")
    con.execute(sql_file.read_text())

con.close()
print("Done")