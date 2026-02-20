-- Parse raw JSON from Bronze and deduplicate by event_id.

WITH parsed AS (
    SELECT
        RAW:event_id::STRING           AS event_id,
        RAW:event_timestamp::TIMESTAMP_NTZ AS event_ts,
        TO_DATE(RAW:event_timestamp::TIMESTAMP_NTZ) AS event_date,
        RAW:customer_id::STRING        AS customer_id,
        RAW:product_id::STRING         AS product_id,
        RAW:plan_id::STRING            AS plan_id,
        RAW:region::STRING             AS region,
        RAW:unit::STRING               AS unit,
        RAW:quantity::NUMBER(38,6)     AS quantity,
        SOURCE,
        BATCH_ID,
        MD5(RAW)                       AS raw_hash,
        ROW_NUMBER() OVER (
            PARTITION BY RAW:event_id::STRING
            ORDER BY RAW:event_timestamp::TIMESTAMP_NTZ DESC
        ) AS _row_num
    FROM {{ source('bronze', 'USAGE_EVENTS_RAW') }}
    WHERE RAW:event_id IS NOT NULL
)

SELECT
    event_id,
    event_ts,
    event_date,
    customer_id,
    product_id,
    plan_id,
    region,
    unit,
    quantity,
    source,
    batch_id,
    raw_hash
FROM parsed
WHERE _row_num = 1
