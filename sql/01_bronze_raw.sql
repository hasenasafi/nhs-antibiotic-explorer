-- BRONZE: load every raw JSON file into one table, exactly as it arrived.
-- Nothing is cleaned here, so any problem can be traced back to the source.

-- Rebuilt from scratch every run (idempotent)
CREATE OR REPLACE TABLE raw_antibiotics AS
SELECT
    filename AS source_file, -- Keep the file name: it holds the month and the download time
    UNNEST(json_extract(json, '$.result.result.records[*]')) AS record   -- split each record into its own row
FROM read_json_objects('data/raw/*.json', filename = true);