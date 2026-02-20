-- Latest customer snapshot per customer_id from Bronze.

WITH parsed AS (
    SELECT
        RAW:customer_id::STRING    AS customer_id,
        RAW:customer_name::STRING  AS customer_name,
        RAW:status::STRING         AS status,
        RAW:country::STRING        AS country,
        RAW:plan_id::STRING        AS plan_id,
        INGEST_TS,
        ROW_NUMBER() OVER (
            PARTITION BY RAW:customer_id::STRING
            ORDER BY INGEST_TS DESC
        ) AS _row_num
    FROM {{ source('bronze', 'CUSTOMERS_RAW') }}
    WHERE RAW:customer_id IS NOT NULL
)

SELECT
    customer_id,
    customer_name,
    status,
    country,
    plan_id
FROM parsed
WHERE _row_num = 1
