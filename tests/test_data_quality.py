# TESTS: data-quality checks on the gold table before it goes to Tableau.
# If any test fails, run.py stops, so the export never runs.

import duckdb
import pytest

DB_PATH = "data/antibiotics.duckdb"
MART = "mart_antibiotics_monthly"


# Open the database once, read-only, and share it with every test
@pytest.fixture(scope="module")
def con():
    con = duckdb.connect(DB_PATH, read_only=True)
    yield con
    con.close()


# Run a query and return the single number it gives back
def query_one(con, sql):
    return con.sql(sql).fetchone()[0]


# Not empty (an empty table would pass the other checks)
def test_mart_has_rows(con):
    rows = query_one(con, f"SELECT COUNT(*) FROM {MART}")
    print(f"\n  Rows in gold table: {rows}")
    assert rows > 0


# No month went missing (Sep 2023 to Aug 2026)
def test_has_36_months(con):
    months = query_one(con, f"SELECT COUNT(DISTINCT month) FROM {MART}")
    print(f"\n  Months found: {months} (expected 36)")
    assert months == 36


# No region lost or renamed
def test_has_7_regions(con):
    regions = query_one(con, f"SELECT COUNT(DISTINCT region) FROM {MART}")
    print(f"\n  Regions found: {regions} (expected 7)")
    assert regions == 7


# Each month, region and drug appears only once
def test_no_duplicate_rows(con):
    sql = f"""
    SELECT COUNT(*) FROM (
        SELECT month, region, bnf_code
        FROM {MART}
        GROUP BY month, region, bnf_code
        HAVING COUNT(*) > 1
    )
    """
    duplicates = query_one(con, sql)
    print(f"\n  Duplicate rows: {duplicates} (expected 0)")
    assert duplicates == 0


# No blanks in the key columns
def test_no_missing_key_values(con):
    sql = f"""
    SELECT COUNT(*) FROM {MART}
    WHERE month IS NULL OR region IS NULL OR bnf_code IS NULL OR items IS NULL
    """
    missing = query_one(con, sql)
    print(f"\n  Rows with missing key values: {missing} (expected 0)")
    assert missing == 0


# No negative item counts
def test_no_negative_values(con):
    negatives = query_one(con, f"SELECT COUNT(*) FROM {MART} WHERE items < 0")
    print(f"\n  Rows with negative items: {negatives} (expected 0)")
    assert negatives == 0


# Antibiotics only (BNF codes starting 0501)
def test_only_antibiotics(con):
    non_antibiotics = query_one(con, f"SELECT COUNT(*) FROM {MART} WHERE bnf_code NOT LIKE '0501%'")
    print(f"\n  Non-antibiotic rows: {non_antibiotics} (expected 0)")
    assert non_antibiotics == 0


# Every row has a broad-spectrum flag, and some are TRUE
def test_broad_spectrum_flag_is_set(con):
    missing_flag = query_one(con, f"SELECT COUNT(*) FROM {MART} WHERE is_broad_spectrum IS NULL")
    flagged = query_one(con, f"SELECT COUNT(*) FROM {MART} WHERE is_broad_spectrum")
    print(f"\n  Rows missing a flag: {missing_flag} (expected 0)")
    print(f"  Rows flagged broad-spectrum: {flagged} (expected more than 0)")
    assert missing_flag == 0
    assert flagged > 0