CREATE OR REPLACE TABLE raw_antibiotics AS
SELECT
    filename AS source_file,
    UNNEST(json_extract(json, '$.result.result.records[*]')) AS record
FROM read_json_objects('data/raw/*.json', filename = true);