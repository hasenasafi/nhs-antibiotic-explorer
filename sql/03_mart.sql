CREATE OR REPLACE TABLE mart_antibiotics_monthly AS
SELECT
    month,
    region,
    bnf_code,
    bnf_name,
    items,
    nic_gbp,
    (bnf_code LIKE '0501013K0%'
        OR bnf_code LIKE '0501021%'
        OR bnf_code LIKE '050112%') AS is_broad_spectrum
FROM stg_antibiotics
WHERE region <> 'UNIDENTIFIED';