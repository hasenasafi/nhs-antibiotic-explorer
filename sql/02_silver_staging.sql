-- =============================================================================
-- SILVER LAYER: clean the raw data
--
-- Takes the raw table from bronze and tidies it up in three ways:
--   1. Keeps only the newest download of each month (removes duplicates)
--   2. Makes the month the same format for every row
--   3. Gives each column a clear name and the right type (text, number, date)
--
-- What goes in:  raw_antibiotics (from bronze)
-- What comes out: stg_antibiotics, one clean row per month, region and drug
-- =============================================================================

-- Make the table. If it already exists, replace it with a fresh copy.
CREATE OR REPLACE TABLE stg_antibiotics AS

-- STEP 1: unpack each row into separate columns.
-- (WITH ... AS creates a temporary step, like doing working on paper.)
WITH parsed AS (
    SELECT
        -- From the file name, take the month the data is for.
        -- e.g. antibiotics_202309_20261110_153412.json -> 202309
        regexp_extract(source_file, 'antibiotics_(\d{6})_', 1) AS file_month,

        -- From the file name, take when it was downloaded.
        -- e.g. antibiotics_202309_20261110_153412.json -> 20261110_153412
        regexp_extract(source_file, 'antibiotics_\d{6}_(\d{8}_\d{6})', 1) AS pulled_at,

        -- Take each value out of the raw JSON row (->> means "get this field as text")
        record ->> 'YEAR_MONTH' AS year_month_raw,
        record ->> 'REGIONAL_OFFICE_NAME' AS region,
        record ->> 'bnf_code' AS bnf_code,
        record ->> 'bnf_name' AS bnf_name,

        -- Turn items and cost into numbers, so they can be added up
        CAST(record ->> 'total_items' AS DOUBLE) AS items,
        CAST(record ->> 'total_nic' AS DOUBLE) AS nic_gbp
    FROM raw_antibiotics
),

-- STEP 2: for every row, find the newest download of that month.
-- If September 2023 was downloaded twice, both copies get told
-- which download time is the newest.
latest AS (
    SELECT
        *,
        MAX(pulled_at) OVER (PARTITION BY file_month) AS latest_pull
    FROM parsed
)

-- STEP 3: keep only rows from the newest download, and tidy the columns
SELECT
    -- The NHS used two month formats: 202409 (older) and '2026-08' (newer).
    -- Remove the dash so both look like 202409, then turn it into a real date
    -- (the 1st of that month), e.g. 2024-09-01.
    CAST(strptime(replace(year_month_raw, '-', ''), '%Y%m') AS DATE) AS month,

    region,
    bnf_code,
    bnf_name,
    CAST(items AS INTEGER) AS items,      -- items are whole numbers
    ROUND(nic_gbp, 2) AS nic_gbp,         -- cost in pounds, to 2 decimal places
    pulled_at                             -- kept, so you can see which download was used
FROM latest

-- Only keep rows from the newest download of each month (this removes duplicates)
WHERE pulled_at = latest_pull;