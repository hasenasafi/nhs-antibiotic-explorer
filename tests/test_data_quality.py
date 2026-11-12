# =============================================================================
# TESTS: check the gold table is correct before it goes to Tableau
#
# Each test checks one thing about mart_antibiotics_monthly. If any test
# fails, run.py stops, so the export (and Tableau) never gets bad data.
#
# Run with: python -m pytest tests/ -v (or the whole pipeline: python src/run.py)
# =============================================================================

import duckdb       # the database (installed via requirements.txt)
import pytest       # the testing tool (installed via requirements.txt)

DB_PATH = "data/antibiotics.duckdb"     # the database built by transform.py
MART = "mart_antibiotics_monthly"       # the gold table being tested


# Open the database once and share it with every test.
# read_only=True: tests can look at the data but never change it.
@pytest.fixture(scope="module")
def con():
    con = duckdb.connect(DB_PATH, read_only=True)
    yield con           # hand the connection to the tests
    con.close()         # close it when all the tests have finished


# Small helper: run a SQL query and return the single number it gives back
def query_one(con, sql):
    return con.sql(sql).fetchone()[0]


# --- The tests ----------------------------------------------------------------
# "assert" means "this must be true". If it isn't, the test fails.

# Catches: an empty table, e.g. if loading failed
def test_mart_has_rows(con):
    assert query_one(con, f"SELECT COUNT(*) FROM {MART}") > 0


# Catches: a missing month, e.g. if one month failed to download (Sep 2023 to Aug 2026)
def test_has_36_months(con):
    assert query_one(con, f"SELECT COUNT(DISTINCT month) FROM {MART}") == 36


# Catches: a region lost or renamed, e.g. if the NHS changed the data again
def test_has_7_regions(con):
    assert query_one(con, f"SELECT COUNT(DISTINCT region) FROM {MART}") == 7


# Catches: duplicates, e.g. if the "keep the newest download" step in silver broke.
# Each month + region + drug should appear only once.
def test_no_duplicate_rows(con):
    sql = f"""
    SELECT COUNT(*) FROM (
        SELECT month, region, bnf_code
        FROM {MART}
        GROUP BY month, region, bnf_code
        HAVING COUNT(*) > 1
    )
    """
    assert query_one(con, sql) == 0


# Catches: blanks in the key columns, e.g. if a column was renamed and not picked up
def test_no_missing_key_values(con):
    sql = f"""
    SELECT COUNT(*) FROM {MART}
    WHERE month IS NULL OR region IS NULL OR bnf_code IS NULL OR items IS NULL
    """
    assert query_one(con, sql) == 0


# Catches: impossible values: you can't prescribe fewer than 0 items
def test_no_negative_values(con):
    assert query_one(con, f"SELECT COUNT(*) FROM {MART} WHERE items < 0 OR nic_gbp < 0") == 0


# Catches: non-antibiotics sneaking in, e.g. if the 0501 filter in extract broke
def test_only_antibiotics(con):
    assert query_one(con, f"SELECT COUNT(*) FROM {MART} WHERE bnf_code NOT LIKE '0501%'") == 0


# Catches: a broken broad-spectrum flag.
# Every row must have TRUE or FALSE, and at least some rows must be TRUE.
def test_broad_spectrum_flag_is_set(con):
    assert query_one(con, f"SELECT COUNT(*) FROM {MART} WHERE is_broad_spectrum IS NULL") == 0
    assert query_one(con, f"SELECT COUNT(*) FROM {MART} WHERE is_broad_spectrum") > 0