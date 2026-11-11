# =============================================================================
# TRANSFORM: build the DuckDB database from the raw JSON files
#
# Runs every SQL file in the sql/ folder, in number order:
#   01_bronze_raw.sql      -> load the raw JSON files, as they arrived
#   02_silver_staging.sql  -> clean: latest pull per month, fixed formats and types
#   03_gold_mart.sql       -> analysis-ready table with the broad-spectrum flag
#
# Why DuckDB: the raw JSON is nested, has repeated pulls and mixed formats.
# DuckDB combines and cleans it with SQL, in a single file with no server.
#
# Run with: python src/transform.py (or the whole pipeline: python src/run.py)
# =============================================================================

from pathlib import Path          # to find the SQL files in the sql/ folder

import duckdb                     # the database (installed via requirements.txt)

DB_PATH = "data/antibiotics.duckdb"   # the database file (in .gitignore: rebuilt, not stored)
SQL_DIR = Path("sql")                 # where the SQL layer files live

# Open the database file, or create it if it doesn't exist yet
con = duckdb.connect(DB_PATH)

# sorted() puts the files in name order, so the 01_, 02_, 03_ prefixes
# guarantee bronze runs before silver, and silver before gold
for sql_file in sorted(SQL_DIR.glob("*.sql")):
    print(f"Running {sql_file.name}")
    con.execute(sql_file.read_text())   # read the SQL file and run it

# Close the connection so the database file is saved and released
con.close()
print("Done")