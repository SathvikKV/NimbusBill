from airflow import DAG
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta

default_args = {
    'owner': 'nimbus_bill',
    'depends_on_past': False,
    'email_on_failure': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'late_arrival_reconciliation',
    default_args=default_args,
    description='Detect late usage and create adjustment line items',
    schedule_interval='0 6 * * *',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['billing', 'reconciliation'],
)

detect_late_events = SnowflakeOperator(
    task_id='detect_late_events',
    sql="""
    CREATE OR REPLACE TEMPORARY TABLE TMP_LATE_ADJUSTMENTS AS
    SELECT
        e.EVENT_ID,
        e.EVENT_DATE,
        i.INVOICE_ID,
        e.PRODUCT_ID,
        e.UNIT,
        e.QUANTITY,
        p.UNIT_PRICE,
        (e.QUANTITY * p.UNIT_PRICE) as ADJUSTMENT_AMOUNT,
        p.RATE_SK
    FROM NIMBUSBILL.SILVER.USAGE_EVENTS_CLEAN e
    JOIN NIMBUSBILL.GOLD.DIM_CUSTOMER c ON e.CUSTOMER_ID = c.CUSTOMER_ID AND c.IS_CURRENT = TRUE
    JOIN NIMBUSBILL.GOLD.FACT_INVOICES i ON c.CUSTOMER_SK = i.CUSTOMER_SK
    JOIN NIMBUSBILL.GOLD.DIM_PRICING_RATE p ON e.PRODUCT_ID = p.PRODUCT_ID AND e.UNIT = p.UNIT 
        AND e.EVENT_DATE BETWEEN p.EFFECTIVE_FROM AND COALESCE(p.EFFECTIVE_TO, '9999-12-31')
    WHERE 
        e.EVENT_DATE BETWEEN i.BILLING_PERIOD_START AND i.BILLING_PERIOD_END
        AND i.STATUS = 'issued'
        AND e.LOAD_TS > i.ISSUED_TS
        AND e.EVENT_ID NOT IN (SELECT LINE_ITEM_ID FROM NIMBUSBILL.GOLD.FACT_INVOICE_LINE_ITEMS WHERE LINE_TYPE='adjustment_ref'); 
    """,
    snowflake_conn_id='snowflake_default',
    dag=dag,
)

create_adjustments = SnowflakeOperator(
    task_id='create_adjustment_lines',
    sql="""
    INSERT INTO NIMBUSBILL.GOLD.FACT_INVOICE_LINE_ITEMS (
        INVOICE_ID, LINE_ITEM_ID, LINE_TYPE, PRODUCT_ID, UNIT, QUANTITY, UNIT_PRICE, AMOUNT, RATE_SK, USAGE_WINDOW_START, USAGE_WINDOW_END, CALC_BATCH_ID, LOAD_TS
    )
    SELECT
        INVOICE_ID,
        UUID_STRING(),
        'adjustment',
        PRODUCT_ID,
        UNIT,
        QUANTITY,
        UNIT_PRICE,
        ADJUSTMENT_AMOUNT,
        RATE_SK,
        EVENT_DATE,
        EVENT_DATE,
        '{{ run_id }}',
        CURRENT_TIMESTAMP()
    FROM TMP_LATE_ADJUSTMENTS;
    """,
    snowflake_conn_id='snowflake_default',
    dag=dag,
)

update_invoice_headers = SnowflakeOperator(
    task_id='update_invoice_totals',
    sql="""
    MERGE INTO NIMBUSBILL.GOLD.FACT_INVOICES T
    USING (
        SELECT INVOICE_ID, SUM(AMOUNT) as ADJ_TOTAL
        FROM NIMBUSBILL.GOLD.FACT_INVOICE_LINE_ITEMS
        WHERE CALC_BATCH_ID = '{{ run_id }}' AND LINE_TYPE = 'adjustment'
        GROUP BY INVOICE_ID
    ) S
    ON T.INVOICE_ID = S.INVOICE_ID
    WHEN MATCHED THEN
        UPDATE SET T.TOTAL = T.TOTAL + S.ADJ_TOTAL, T.SUBTOTAL = T.SUBTOTAL + S.ADJ_TOTAL;
    """,
    snowflake_conn_id='snowflake_default',
    dag=dag,
)

detect_late_events >> create_adjustments >> update_invoice_headers
