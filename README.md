# NHS Antibiotic Prescribing Explorer

An end-to-end data pipeline that pulls antibiotic prescribing data for England from the NHS Business Services Authority (NHSBSA) API, stores it in DuckDB, transforms it with SQL and checks it with automated data-quality tests.

## What I built and who for

- **As a** hospital pharmacist,
- **I would like to** see how antibiotic prescribing in primary care changes over time and how it differs between NHS England regions,
- **therefore I have used** the NHSBSA Open Data Portal API to extract monthly antibiotic prescribing (BNF section 5.1) for the last 24 months, and built a pipeline that loads, cleans and tests it,
- **so I can conclude** which antibiotics are prescribed most, how each region's antibiotic mix compares, and how costs per item differ between drugs.

## The data

**Source:** [English Prescribing Dataset (EPD) with SNOMED Code](https://opendata.nhsbsa.net/dataset/english-prescribing-dataset-epd-with-snomed-code), published monthly by NHSBSA under the Open Government Licence. No API key is needed.

**Scope:** antibiotics only (BNF codes starting `0501`), September 2024 to August 2026, by NHS England region.

**Why I query the API with SQL instead of downloading files:** each month of the EPD has about 17 million rows. Instead of downloading everything, the extraction script sends a SQL query to the portal's `datastore_search_sql` endpoint, so the NHS server filters to antibiotics and adds up by region. Each month comes back as about 400 rows.

### Problems I found in the source data

1. **Hidden nesting:** the SQL endpoint wraps results one level deeper than expected (`result.result.records`, not `result.records`).
2. **Renamed columns (schema drift):** older months use different column names. In older files `BNF_CHEMICAL_SUBSTANCE` holds the drug *code*; in newer files it holds the drug *name*, and the code moved to `BNF_CHEMICAL_SUBSTANCE_CODE`. The extraction script checks each month's columns first and picks the right ones, so codes and names are never mixed up.
3. **Numbers stored as text:** from March 2025, `ITEMS` and `NIC` arrive as text, so the query converts them with `CAST(... AS FLOAT64)` before adding them up.
4. **Two month formats:** older months store `YEAR_MONTH` as `202409`, newer months as `'2026-08'`. The staging layer converts both into a proper date.

## How it works

```
NHSBSA API  →  data/raw/*.json  →  raw  →  staging  →  mart  →  tests
  (extract)       (raw files)        (DuckDB, SQL)              (pytest)
```

1. **Extract** (`extract/fetch_antibiotics.py`): loops over the months, detects each month's column layout, queries the API and saves every response untouched as a timestamped JSON file in `data/raw/`. It retries temporary failures (timeouts, 5xx errors) with increasing waits, stops immediately on 4xx errors (a bad request won't fix itself), and logs the server's error message.
2. **Raw** (`sql/01_raw.sql`): loads every JSON file into `raw_antibiotics`, one row per record, tagged with its source file.
3. **Staging** (`sql/02_staging.sql`): keeps only the most recent pull of each month (raw files are never overwritten, so a month can be pulled more than once), converts the month formats into one date, and sets clear names and types.
4. **Mart** (`sql/03_mart.sql`): the analysis-ready table `mart_antibiotics_monthly`, one row per month, region and antibiotic, with **cost per item** and each drug's **percentage of the region's antibiotic items** that month.
5. **Broad-spectrum mart** (`sql/04_mart_broad_spectrum.sql`): `mart_broad_spectrum_by_region`, one row per month and region, with the percentage of antibiotic items that are broad-spectrum (co-amoxiclav, cephalosporins and quinolones), the antibiotics most closely linked to resistance.
6. **Tests** (`tests/test_data_quality.py`): 9 checks: the mart has rows, 24 months, 7 regions, no duplicates, no missing key values, no negative values, and antibiotics only. One row per region and month in the broad-spectrum table, and percentages between 0 and 100.

**Idempotency:** every SQL model uses `CREATE OR REPLACE TABLE` and rebuilds from all raw files, so running the pipeline twice gives the same result.

**Reconciliation check:** the staging table has 9,686 rows, exactly matching the sum of rows logged by the extraction for the 24 months.

## Findings (September 2025 to August 2026)

| Region | Broad-spectrum share of antibiotic items |
|---|---|
| East of England | 9.80% |
| South East | 8.78% |
| London | 8.46% |
| South West | 8.30% |
| Midlands | 8.25% |
| North West | 7.48% |
| North East and Yorkshire | 6.74% |

- **East of England** has the highest share of broad-spectrum antibiotics, and **North East and Yorkshire** the lowest.
- **North East and Yorkshire** prescribes the second-highest number of antibiotic items but has the lowest broad-spectrum share, so high volume and broad-spectrum use don't necessarily go together.
- Because these are percentages, regions of different sizes can be compared fairly. They don't show overall overprescribing, which needs population data (see "What I would do next").

## Decisions

- **Cost uses NIC (net ingredient cost), not actual cost.** NHSBSA changed how actual cost is calculated from April 2024, so NIC is more consistent across the period.
- **Rows with region `UNIDENTIFIED` are kept in staging but excluded from the mart.** They are prescriptions that can't be linked to a region: about 53,000 items, under 0.1% of the total.
- **Region level, not GP practice level,** to keep the extraction small and the story clear.

## How to run it

```bash
git clone https://github.com/hasenasafi/nhs-antibiotic-explorer.git
cd nhs-antibiotic-explorer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python sql/run_models.py          # builds data/antibiotics.duckdb from the committed raw files (no internet needed)
python -m pytest tests/ -v        # runs the data-quality tests

# optional, needs internet: refresh the raw data from the API
python extract/fetch_antibiotics.py
```

## Limitations

## What I built and who for

- **As a** hospital pharmacist concerned about antimicrobial resistance,
- **I would like to** find out which regions of England may be overprescribing antibiotics, especially the broad-spectrum antibiotics most linked to resistance,
- **therefore I have used** the NHSBSA Open Data Portal API to extract monthly antibiotic prescribing (BNF section 5.1) for the last 24 months, and built a pipeline that loads, cleans and tests it,
- **so I can conclude** how each region's antibiotic prescribing compares, which regions rely most on broad-spectrum antibiotics (co-amoxiclav, cephalosporins and quinolones), and how this changes over time.

## What I would do next

- Add GP registered-patient numbers so regions can be compared fairly as antibiotic items per 1,000 patients, the key measure for identifying overprescribing.
- Connect the mart to Tableau to build a regional map and trend dashboards.
- Schedule the extraction to run monthly and only fetch new months (incremental loading).
- Break down to Integrated Care Board (ICB) level for a more local view.

## Where AI helped

I used Claude as a tutor while building this. It explained concepts, suggested code that I ran, tested and debugged step by step, and helped me investigate the problems listed above. I chose the topic and the scope, made the decisions in this README, and verified the results (for example, the reconciliation check and the test suite).