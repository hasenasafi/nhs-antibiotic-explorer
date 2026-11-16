-- SILVER: clean the raw data.
-- Keeps only the newest download of each month, fixes the month format and sets types.

CREATE OR REPLACE TABLE stg_antibiotics AS

-- Part 1: read the month and download time from the file name,
-- and unpack each raw record into clear columns
WITH parsed AS (
    SELECT
        regexp_extract(source_file, 'antibiotics_(\d{6})_', 1) AS file_month,
        regexp_extract(source_file, 'antibiotics_\d{6}_(\d{8}_\d{6})', 1) AS pulled_at,
        record ->> 'YEAR_MONTH' AS year_month_raw,
        record ->> 'REGIONAL_OFFICE_NAME' AS region,
        record ->> 'bnf_code' AS bnf_code,
        record ->> 'bnf_name' AS bnf_name,
        CAST(record ->> 'total_items' AS DOUBLE) AS items
    FROM raw_antibiotics
),

-- Part 2: find the most recent download time for each month
latest AS (
    SELECT
        *,
        MAX(pulled_at) OVER (PARTITION BY file_month) AS latest_pull
    FROM parsed
)

-- Part 3: build the final table: one date format, whole-number items,
-- cost to 2 decimal places, and only the newest download of each month
SELECT
    CAST(strptime(replace(year_month_raw, '-', ''), '%Y%m') AS DATE) AS month,
    region,
    bnf_code,
    bnf_name,
    CAST(items AS INTEGER) AS items,
    pulled_at
FROM latest
WHERE pulled_at = latest_pull;