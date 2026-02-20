-- 07_reconciliation.sql
-- Logic to handle late arriving events that affect closed invoices.

-- 1. Identify Late Events
-- Events with EVENT_DATE < Invoice Period End but Ingested AFTER Invoice Issue Date
CREATE OR REPLACE TEMPORARY TABLE TMP_LATE_EVENTS AS
SELECT
    e.EVENT_ID,
    e.EVENT_DATE,
    e.CUSTOMER_ID,
    e.PRODUCT_ID,
    e.QUANTITY,
    e.UNIT,
    i.INVOICE_ID,
    i.ISSUED_TS
FROM NIMBUSBILL.SILVER.USAGE_EVENTS_CLEAN e
JOIN NIMBUSBILL.GOLD.FACT_INVOICES i 
    ON e.CUSTOMER_ID = (SELECT CUSTOMER_ID FROM NIMBUSBILL.GOLD.DIM_CUSTOMER WHERE CUSTOMER_SK = i.CUSTOMER_SK LIMIT 1) -- Simplify for example
    AND e.EVENT_DATE BETWEEN i.BILLING_PERIOD_START AND i.BILLING_PERIOD_END
WHERE i.STATUS = 'issued'
  AND e.LOAD_TS > i.ISSUED_TS;

-- 2. Calculate Delta (Adjustment Amount)
-- (Simplified for initial implementation)
-- In a full implementation, we would insert into FACT_INVOICE_LINE_ITEMS
