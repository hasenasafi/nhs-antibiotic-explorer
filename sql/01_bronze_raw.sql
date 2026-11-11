-- =============================================================================
-- BRONZE LAYER: copy the raw data into the database
--
-- Takes every JSON file in data/raw/ and puts its rows into one table.
-- Nothing is cleaned or changed. It's an exact copy of what the API sent.
--
-- What goes in:  66 JSON files (one or more per month)
-- What comes out: one table called raw_antibiotics, with:
--    source_file = the name of the file the row came from
--    record      = one row of data (region, drug, items, cost), still as raw JSON
-- =============================================================================

-- Make the table. If it already exists, replace it with a fresh copy.
CREATE OR REPLACE TABLE raw_antibiotics AS
SELECT

    -- Keep the file name, so later we can tell which month each row is from
    -- and when it was downloaded
    filename AS source_file,

    -- Each file has the rows tucked inside: result > result > records.
    -- This line goes inside to find the rows, then splits them out
    -- so each one gets its own line in the table.
    UNNEST(json_extract(json, '$.result.result.records[*]')) AS record

-- Read every .json file in the data/raw folder
FROM read_json_objects('data/raw/*.json', filename = true);