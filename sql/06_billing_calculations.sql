-- 06_billing_calculations.sql
-- This file contains the logic for the daily and monthly billing processes.
-- In a real Airflow setup, these would be executed as separate tasks.

-- Variables (to be replaced by Airflow)
-- SET PROCESS_DATE = '2023-10-27';
-- SET BATCH_ID = 'run_123';

-----------------------------------------------------------
-- 1. Silver Transformation (Merge/Dedupe)
-----------------------------------------------------------
-- MERGE into USAGE_EVENTS_CLEAN
MERGE INTO NIMBUSBILL.SILVER.USAGE_EVENTS_CLEAN T
USING (
    SELECT * 
    FROM NIMBUSBILL.SILVER.V_USAGE_EVENTS_PARSED 
    WHERE EVENT_DATE = $PROCESS_DATE
    QUALIFY ROW_NUMBER() OVER (PARTITION BY EVENT_ID ORDER BY EVENT_TS DESC) = 1
) S
ON T.EVENT_ID = S.EVENT_ID
WHEN MATCHED THEN
    UPDATE SET 
        T.LOAD_TS = CURRENT_TIMESTAMP(), 
        T.BATCH_ID = $BATCH_ID,
        T.RAW_HASH = S.RAW_HASH
WHEN NOT MATCHED THEN
    INSERT (EVENT_ID, EVENT_TS, EVENT_DATE, CUSTOMER_ID, PRODUCT_ID, PLAN_ID, REGION, UNIT, QUANTITY, SOURCE, LOAD_TS, BATCH_ID, RAW_HASH)
    VALUES (S.EVENT_ID, S.EVENT_TS, S.EVENT_DATE, S.CUSTOMER_ID, S.PRODUCT_ID, S.PLAN_ID, S.REGION, S.UNIT, S.QUANTITY, S.SOURCE, CURRENT_TIMESTAMP(), $BATCH_ID, S.RAW_HASH);

-----------------------------------------------------------
-- 2. Silver Daily Aggregate (Rolling Window)
-----------------------------------------------------------
-- Delete existing aggregates for the process date (Idempotency)
DELETE FROM NIMBUSBILL.SILVER.USAGE_DAILY_AGG WHERE EVENT_DATE = $PROCESS_DATE;

-- Insert aggregated usage
INSERT INTO NIMBUSBILL.SILVER.USAGE_DAILY_AGG (EVENT_DATE, CUSTOMER_ID, PRODUCT_ID, UNIT, TOTAL_QUANTITY, EVENT_COUNT, LAST_EVENT_TS, LOAD_TS, BATCH_ID)
SELECT
    EVENT_DATE,
    CUSTOMER_ID,
    PRODUCT_ID,
    UNIT,
    SUM(QUANTITY),
    COUNT(*),
    MAX(EVENT_TS),
    CURRENT_TIMESTAMP(),
    $BATCH_ID
FROM NIMBUSBILL.SILVER.USAGE_EVENTS_CLEAN
WHERE EVENT_DATE = $PROCESS_DATE
GROUP BY 1, 2, 3, 4;

-----------------------------------------------------------
-- 3. Gold Daily Costs (Apply Pricing)
-----------------------------------------------------------
-- Delete existing Gold facts for the process date
DELETE FROM NIMBUSBILL.GOLD.FACT_CUSTOMER_DAILY_USAGE WHERE DATE_ID = $PROCESS_DATE;

INSERT INTO NIMBUSBILL.GOLD.FACT_CUSTOMER_DAILY_USAGE (
    DATE_ID, CUSTOMER_SK, PRODUCT_ID, UNIT, TOTAL_QUANTITY, BILLABLE_QUANTITY, COST_AMOUNT, CURRENCY, RATE_SK, LOAD_TS, BATCH_ID
)
SELECT
    agg.EVENT_DATE,
    c.CUSTOMER_SK,
    agg.PRODUCT_ID,
    agg.UNIT,
    agg.TOTAL_QUANTITY,
    agg.TOTAL_QUANTITY AS BILLABLE_QUANTITY, -- Logic for tiered pricing could replace this
    (agg.TOTAL_QUANTITY * p.UNIT_PRICE) AS COST_AMOUNT,
    p.CURRENCY,
    p.RATE_SK,
    CURRENT_TIMESTAMP(),
    $BATCH_ID
FROM NIMBUSBILL.SILVER.USAGE_DAILY_AGG agg
JOIN NIMBUSBILL.GOLD.DIM_CUSTOMER c 
    ON agg.CUSTOMER_ID = c.CUSTOMER_ID 
    AND c.IS_CURRENT = TRUE -- Simplified for daily run; strictly should check effective dates
JOIN NIMBUSBILL.GOLD.DIM_PRICING_RATE p 
    ON agg.PRODUCT_ID = p.PRODUCT_ID 
    AND agg.UNIT = p.UNIT 
    AND (agg.EVENT_DATE BETWEEN p.EFFECTIVE_FROM AND COALESCE(p.EFFECTIVE_TO, '9999-12-31'))
WHERE agg.EVENT_DATE = $PROCESS_DATE;
