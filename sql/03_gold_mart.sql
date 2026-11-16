-- GOLD: the final table exported to Tableau, one row per month, region and drug.

CREATE OR REPLACE TABLE mart_antibiotics_monthly AS
SELECT
    month,
    region,
    bnf_code,
    bnf_name,
    items,
    nic_gbp,
    -- Broad-spectrum flag: co-amoxiclav, cephalosporins and quinolones
    (bnf_code LIKE '0501013K0%'
        OR bnf_code LIKE '0501021%'
        OR bnf_code LIKE '050112%') AS is_broad_spectrum
FROM stg_antibiotics
-- Leave out rows with no region (under 0.1% of items; still kept in silver)
WHERE region <> 'UNIDENTIFIED';