CREATE OR REPLACE TABLE mart_broad_spectrum_by_region AS
WITH flagged AS (
    SELECT
        month,
        region,
        items,
        (bnf_code LIKE '0501013K0%'
            OR bnf_code LIKE '0501021%'
            OR bnf_code LIKE '050112%') AS is_broad_spectrum
    FROM mart_antibiotics_monthly
)
SELECT
    month,
    region,
    SUM(items) AS total_antibiotic_items,
    SUM(CASE WHEN is_broad_spectrum THEN items ELSE 0 END) AS broad_spectrum_items,
    ROUND(100.0 * SUM(CASE WHEN is_broad_spectrum THEN items ELSE 0 END) / SUM(items), 2) AS broad_spectrum_pct
FROM flagged
GROUP BY month, region;