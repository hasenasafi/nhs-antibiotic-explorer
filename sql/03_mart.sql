CREATE OR REPLACE TABLE mart_antibiotics_monthly AS
WITH base AS (
    SELECT
        month,
        region,
        bnf_code,
        bnf_name,
        items,
        nic_gbp
    FROM stg_antibiotics
    WHERE region <> 'UNIDENTIFIED'
)
SELECT
    month,
    region,
    bnf_code,
    bnf_name,
    items,
    nic_gbp,
    ROUND(nic_gbp / NULLIF(items, 0), 2) AS cost_per_item_gbp,
    ROUND(100.0 * items / SUM(items) OVER (PARTITION BY month, region), 2) AS pct_of_region_items
FROM base;