-- =============================================================================
-- GOLD LAYER: the final table, ready for Tableau
--
-- Takes the clean table from silver and makes it ready for analysis:
--   1. Removes rows that can't be linked to a region (UNIDENTIFIED)
--   2. Adds a TRUE/FALSE column saying whether each drug is broad-spectrum
--
-- It only keeps numbers that can be added up (items and cost). Percentages,
-- like the broad-spectrum share, are worked out in Tableau from the totals,
-- so they're always calculated correctly .
--
-- What goes in:  stg_antibiotics (from silver)
-- What comes out: mart_antibiotics_monthly, the table exported to Tableau
-- =============================================================================

-- Make the table. If it already exists, replace it with a fresh copy.
CREATE OR REPLACE TABLE mart_antibiotics_monthly AS
SELECT
    month,
    region,
    bnf_code,
    bnf_name,
    items,
    nic_gbp,

    -- Broad-spectrum flag: TRUE if the drug is one of these, FALSE if not.
    -- These are the antibiotics most linked to resistance:
    --   0501013K0... = co-amoxiclav
    --   0501021...   = cephalosporins (e.g. cefalexin)
    --   050112...    = quinolones (e.g. ciprofloxacin)
    -- (% means "anything after this", e.g. '050112%' = starts with 050112)
    (bnf_code LIKE '0501013K0%'
        OR bnf_code LIKE '0501021%'
        OR bnf_code LIKE '050112%') AS is_broad_spectrum

FROM stg_antibiotics

-- Leave out rows with no region: they can't be shown on a regional chart.
-- They're under 0.1% of items, and still kept in silver, so nothing is lost.
WHERE region <> 'UNIDENTIFIED';