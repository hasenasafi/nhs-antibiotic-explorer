import duckdb
import pytest

DB_PATH = "data/antibiotics.duckdb"
MART = "mart_antibiotics_monthly"


@pytest.fixture(scope="module")
def con():
    con = duckdb.connect(DB_PATH, read_only=True)
    yield con
    con.close()


def query_one(con, sql):
    return con.sql(sql).fetchone()[0]


def test_mart_has_rows(con):
    assert query_one(con, f"SELECT COUNT(*) FROM {MART}") > 0


def test_has_24_months(con):
    assert query_one(con, f"SELECT COUNT(DISTINCT month) FROM {MART}") == 24


def test_has_7_regions(con):
    assert query_one(con, f"SELECT COUNT(DISTINCT region) FROM {MART}") == 7


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


def test_no_missing_key_values(con):
    sql = f"""
    SELECT COUNT(*) FROM {MART}
    WHERE month IS NULL OR region IS NULL OR bnf_code IS NULL OR items IS NULL
    """
    assert query_one(con, sql) == 0


def test_no_negative_values(con):
    assert query_one(con, f"SELECT COUNT(*) FROM {MART} WHERE items < 0 OR nic_gbp < 0") == 0


def test_only_antibiotics(con):
    assert query_one(con, f"SELECT COUNT(*) FROM {MART} WHERE bnf_code NOT LIKE '0501%'") == 0

def test_broad_spectrum_one_row_per_region_month(con):
    assert query_one(con, "SELECT COUNT(*) FROM mart_broad_spectrum_by_region") == 24 * 7


def test_broad_spectrum_pct_is_valid(con):
    sql = """
    SELECT COUNT(*) FROM mart_broad_spectrum_by_region
    WHERE broad_spectrum_pct IS NULL OR broad_spectrum_pct < 0 OR broad_spectrum_pct > 100
    """
    assert query_one(con, sql) == 0