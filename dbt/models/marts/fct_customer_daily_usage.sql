-- Daily usage costs per customer x product, joined with pricing rates.

WITH daily_agg AS (
    SELECT
        event_date,
        customer_id,
        product_id,
        unit,
        SUM(quantity)  AS total_quantity,
        COUNT(*)       AS event_count
    FROM {{ ref('stg_usage_events') }}
    GROUP BY 1, 2, 3, 4
),

customers AS (
    SELECT * FROM NIMBUSBILL.GOLD.DIM_CUSTOMER
    WHERE IS_CURRENT = TRUE
),

pricing AS (
    SELECT * FROM {{ ref('stg_pricing') }}
)

SELECT
    agg.event_date                          AS date_id,
    c.CUSTOMER_SK                           AS customer_sk,
    agg.product_id,
    agg.unit,
    agg.total_quantity,
    agg.total_quantity                      AS billable_quantity,
    (agg.total_quantity * p.unit_price)     AS cost_amount,
    p.currency,
    agg.event_count
FROM daily_agg agg
JOIN customers c
    ON agg.customer_id = c.CUSTOMER_ID
JOIN pricing p
    ON agg.product_id = p.product_id
    AND agg.unit = p.unit
    AND agg.event_date BETWEEN p.effective_from
        AND COALESCE(p.effective_to, '9999-12-31')
