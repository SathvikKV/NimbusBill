-- Latest pricing rates per product/plan from Bronze catalog.

WITH parsed AS (
    SELECT
        RAW:product_id::STRING       AS product_id,
        RAW:plan_id::STRING          AS plan_id,
        RAW:unit::STRING             AS unit,
        RAW:price::FLOAT             AS unit_price,
        RAW:currency::STRING         AS currency,
        RAW:effective_from::DATE     AS effective_from,
        TRY_CAST(RAW:effective_to::STRING AS DATE) AS effective_to,
        INGEST_TS,
        ROW_NUMBER() OVER (
            PARTITION BY RAW:product_id::STRING, RAW:plan_id::STRING
            ORDER BY INGEST_TS DESC
        ) AS _row_num
    FROM {{ source('bronze', 'PRICING_CATALOG_RAW') }}
    WHERE RAW:product_id IS NOT NULL
)

SELECT
    product_id,
    plan_id,
    unit,
    unit_price,
    currency,
    effective_from,
    effective_to
FROM parsed
WHERE _row_num = 1
