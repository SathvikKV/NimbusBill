-- Per-product line items for each monthly invoice.

WITH product_monthly AS (
    SELECT
        customer_sk,
        DATE_TRUNC('MONTH', date_id)::DATE  AS billing_period_start,
        product_id,
        unit,
        SUM(total_quantity)                 AS quantity,
        SUM(cost_amount)                    AS amount,
        MAX(currency)                       AS currency
    FROM {{ ref('fct_customer_daily_usage') }}
    GROUP BY 1, 2, 3, 4
),

invoices AS (
    SELECT invoice_id, customer_sk, billing_period_start
    FROM {{ ref('fct_invoices') }}
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['inv.invoice_id', 'pm.product_id']) }}
                                            AS line_item_id,
    inv.invoice_id,
    'usage'                                 AS line_type,
    pm.product_id,
    pm.unit,
    pm.quantity,
    CASE WHEN pm.quantity > 0
         THEN ROUND(pm.amount / pm.quantity, 6)
         ELSE 0 END                         AS unit_price,
    pm.amount,
    pm.currency
FROM product_monthly pm
JOIN invoices inv
    ON pm.customer_sk = inv.customer_sk
    AND pm.billing_period_start = inv.billing_period_start
WHERE pm.amount > 0
