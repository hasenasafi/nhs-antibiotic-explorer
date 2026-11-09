from pathlib import Path

import duckdb

DB_PATH = "data/antibiotics.duckdb"
SQL_DIR = Path("sql")

con = duckdb.connect(DB_PATH)

for sql_file in sorted(SQL_DIR.glob("*.sql")):
    print(f"Running {sql_file.name}")
    con.execute(sql_file.read_text())

con.close()
print("Done")