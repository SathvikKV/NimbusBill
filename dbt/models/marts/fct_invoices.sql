-- Monthly invoice rollup: one row per customer per billing period.

WITH monthly_costs AS (
    SELECT
        customer_sk,
        DATE_TRUNC('MONTH', date_id)::DATE  AS billing_period_start,
        LAST_DAY(date_id)                   AS billing_period_end,
        SUM(cost_amount)                    AS subtotal,
        MAX(currency)                       AS currency
    FROM {{ ref('fct_customer_daily_usage') }}
    GROUP BY 1, 2, 3
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['customer_sk', 'billing_period_start']) }}
                                            AS invoice_id,
    customer_sk,
    billing_period_start,
    billing_period_end,
    CURRENT_TIMESTAMP()                     AS issued_ts,
    'issued'                                AS status,
    subtotal,
    0                                       AS tax,
    subtotal                                AS total,
    currency
FROM monthly_costs
WHERE subtotal > 0
