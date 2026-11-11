CREATE OR REPLACE TABLE stg_antibiotics AS
WITH parsed AS (
    SELECT
        regexp_extract(source_file, 'antibiotics_(\d{6})_', 1) AS file_month,
        regexp_extract(source_file, 'antibiotics_\d{6}_(\d{8}_\d{6})', 1) AS pulled_at,
        record ->> 'YEAR_MONTH' AS year_month_raw,
        record ->> 'REGIONAL_OFFICE_NAME' AS region,
        record ->> 'bnf_code' AS bnf_code,
        record ->> 'bnf_name' AS bnf_name,
        CAST(record ->> 'total_items' AS DOUBLE) AS items,
        CAST(record ->> 'total_nic' AS DOUBLE) AS nic_gbp
    FROM raw_antibiotics
),
latest AS (
    SELECT
        *,
        MAX(pulled_at) OVER (PARTITION BY file_month) AS latest_pull
    FROM parsed
)
SELECT
    CAST(strptime(replace(year_month_raw, '-', ''), '%Y%m') AS DATE) AS month,
    region,
    bnf_code,
    bnf_name,
    CAST(items AS INTEGER) AS items,
    ROUND(nic_gbp, 2) AS nic_gbp,
    pulled_at
FROM latest
WHERE pulled_at = latest_pull;