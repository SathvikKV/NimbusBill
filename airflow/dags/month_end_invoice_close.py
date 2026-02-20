from airflow import DAG
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta

default_args = {
    'owner': 'nimbus_bill',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'month_end_invoice_close',
    default_args=default_args,
    description='Generate final monthly invoices',
    schedule_interval='0 4 1 * *',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['billing', 'monthly'],
)

BILLING_START = "{{ data_interval_start.replace(day=1).subtract(months=1).date() }}"
BILLING_END = "{{ data_interval_start.replace(day=1).subtract(days=1).date() }}"
BATCH_ID = "inv_close_{{ run_id }}"

generate_invoices = SnowflakeOperator(
    task_id='generate_invoice_headers',
    sql="""
    INSERT INTO NIMBUSBILL.GOLD.FACT_INVOICES (
        INVOICE_ID, CUSTOMER_SK, BILLING_PERIOD_START, BILLING_PERIOD_END, ISSUED_TS, STATUS, SUBTOTAL, TAX, TOTAL, CURRENCY, LOAD_TS, BATCH_ID
    )
    SELECT
        UUID_STRING(),
        CUSTOMER_SK,
        '{{ prev_ds_month_start }}'::DATE,
        '{{ prev_ds_month_end }}'::DATE,
        CURRENT_TIMESTAMP(),
        'issued',
        SUM(COST_AMOUNT),
        0,
        SUM(COST_AMOUNT),
        MAX(CURRENCY),
        CURRENT_TIMESTAMP(),
        '{{ run_id }}'
    FROM NIMBUSBILL.GOLD.FACT_CUSTOMER_DAILY_USAGE
    WHERE DATE_ID BETWEEN '{{ prev_ds_month_start }}'::DATE AND '{{ prev_ds_month_end }}'::DATE
    GROUP BY CUSTOMER_SK;
    """,
    snowflake_conn_id='snowflake_default',
    dag=dag,
)

generate_line_items = SnowflakeOperator(
    task_id='generate_invoice_line_items',
    sql="""
    INSERT INTO NIMBUSBILL.GOLD.FACT_INVOICE_LINE_ITEMS (
        INVOICE_ID, LINE_ITEM_ID, LINE_TYPE, PRODUCT_ID, UNIT, QUANTITY, UNIT_PRICE, AMOUNT, RATE_SK, USAGE_WINDOW_START, USAGE_WINDOW_END, CALC_BATCH_ID, LOAD_TS
    )
    SELECT
        inv.INVOICE_ID,
        UUID_STRING(),
        'usage',
        u.PRODUCT_ID,
        u.UNIT,
        SUM(u.BILLABLE_QUANTITY),
        AVG(r.UNIT_PRICE),
        SUM(u.COST_AMOUNT),
        u.RATE_SK,
        MIN(u.DATE_ID),
        MAX(u.DATE_ID),
        '{{ run_id }}',
        CURRENT_TIMESTAMP()
    FROM NIMBUSBILL.GOLD.FACT_CUSTOMER_DAILY_USAGE u
    JOIN NIMBUSBILL.GOLD.FACT_INVOICES inv 
        ON u.CUSTOMER_SK = inv.CUSTOMER_SK 
        AND u.DATE_ID BETWEEN inv.BILLING_PERIOD_START AND inv.BILLING_PERIOD_END
    LEFT JOIN NIMBUSBILL.GOLD.DIM_PRICING_RATE r ON u.RATE_SK = r.RATE_SK
    WHERE inv.BATCH_ID = '{{ run_id }}'
    GROUP BY inv.INVOICE_ID, u.PRODUCT_ID, u.UNIT, u.RATE_SK;
    """,
    snowflake_conn_id='snowflake_default',
    dag=dag,
)

check_integrity = SnowflakeOperator(
    task_id='check_invoice_integrity',
    sql="""
    SELECT 1 / IFF(
        ABS(COALESCE(SUM(i.TOTAL), 0) - COALESCE(SUM(li.AMOUNT), 0)) > 0.01,
        0,
        1
    )
    FROM NIMBUSBILL.GOLD.FACT_INVOICES i
    LEFT JOIN NIMBUSBILL.GOLD.FACT_INVOICE_LINE_ITEMS li ON i.INVOICE_ID = li.INVOICE_ID
    WHERE i.BATCH_ID = '{{ run_id }}';
    """,
    snowflake_conn_id='snowflake_default',
    dag=dag,
)

generate_invoices >> generate_line_items >> check_integrity
