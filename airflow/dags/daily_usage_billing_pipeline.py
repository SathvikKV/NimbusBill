from airflow import DAG
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.operators.python import PythonOperator
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
    'daily_usage_billing_pipeline',
    default_args=default_args,
    description='Daily ingestion and billing calculation pipeline',
    schedule_interval='0 2 * * *',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['billing', 'daily'],
)

PROCESS_DATE = "{{ ds }}"
BATCH_ID = "run_{{ run_id }}"

def load_bronze_data(ds, **kwargs):
    from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
    import os
    
    file_path = f"/opt/airflow/datagen/data/usage_events_{ds}.jsonl"
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found. Skipping ingestion.")
        return

    hook = SnowflakeHook(snowflake_conn_id='snowflake_default')
    conn = hook.get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"PUT file://{file_path} @NIMBUSBILL.BRONZE.%USAGE_EVENTS_RAW AUTO_COMPRESS=TRUE")
        
        run_id = kwargs.get('run_id')
        cursor.execute(f"""
            COPY INTO NIMBUSBILL.BRONZE.USAGE_EVENTS_RAW (INGEST_TS, SOURCE, DT, BATCH_ID, FILE_NAME, RAW)
            FROM (
                SELECT 
                    CURRENT_TIMESTAMP(), 
                    'API', 
                    '{ds}', 
                    '{run_id}', 
                    METADATA$FILENAME, 
                    $1 
                FROM @NIMBUSBILL.BRONZE.%USAGE_EVENTS_RAW
            )
            FILE_FORMAT = (TYPE = 'JSON' STRIP_OUTER_ARRAY = FALSE)
            PURGE = TRUE
        """)
        print("Ingestion complete.")
    finally:
        cursor.close()
        conn.close()

ingest_bronze = PythonOperator(
    task_id='ingest_bronze_usage',
    python_callable=load_bronze_data,
    dag=dag,
)

silver_clean_merge = SnowflakeOperator(
    task_id='silver_clean_merge',
    sql="""
    MERGE INTO NIMBUSBILL.SILVER.USAGE_EVENTS_CLEAN T
    USING (
        SELECT * 
        FROM NIMBUSBILL.SILVER.V_USAGE_EVENTS_PARSED 
        WHERE EVENT_DATE = '{{ ds }}'
        QUALIFY ROW_NUMBER() OVER (PARTITION BY EVENT_ID ORDER BY EVENT_TS DESC) = 1
    ) S
    ON T.EVENT_ID = S.EVENT_ID
    WHEN MATCHED THEN
        UPDATE SET T.LOAD_TS = CURRENT_TIMESTAMP(), T.BATCH_ID = '{{ run_id }}', T.RAW_HASH = S.RAW_HASH
    WHEN NOT MATCHED THEN
        INSERT (EVENT_ID, EVENT_TS, EVENT_DATE, CUSTOMER_ID, PRODUCT_ID, PLAN_ID, REGION, UNIT, QUANTITY, SOURCE, LOAD_TS, BATCH_ID, RAW_HASH)
        VALUES (S.EVENT_ID, S.EVENT_TS, S.EVENT_DATE, S.CUSTOMER_ID, S.PRODUCT_ID, S.PLAN_ID, S.REGION, S.UNIT, S.QUANTITY, S.SOURCE, CURRENT_TIMESTAMP(), '{{ run_id }}', S.RAW_HASH);
    """,
    snowflake_conn_id='snowflake_default',
    dag=dag,
)

silver_daily_agg = SnowflakeOperator(
    task_id='silver_daily_agg_rebuild',
    sql="""
    DELETE FROM NIMBUSBILL.SILVER.USAGE_DAILY_AGG WHERE EVENT_DATE = '{{ ds }}';

    INSERT INTO NIMBUSBILL.SILVER.USAGE_DAILY_AGG (EVENT_DATE, CUSTOMER_ID, PRODUCT_ID, UNIT, TOTAL_QUANTITY, EVENT_COUNT, LAST_EVENT_TS, LOAD_TS, BATCH_ID)
    SELECT
        EVENT_DATE, CUSTOMER_ID, PRODUCT_ID, UNIT, SUM(QUANTITY), COUNT(*), MAX(EVENT_TS), CURRENT_TIMESTAMP(), '{{ run_id }}'
    FROM NIMBUSBILL.SILVER.USAGE_EVENTS_CLEAN
    WHERE EVENT_DATE = '{{ ds }}'
    GROUP BY 1, 2, 3, 4;
    """,
    snowflake_conn_id='snowflake_default',
    dag=dag,
)

gold_daily_costs = SnowflakeOperator(
    task_id='gold_compute_daily_costs',
    sql="""
    DELETE FROM NIMBUSBILL.GOLD.FACT_CUSTOMER_DAILY_USAGE WHERE DATE_ID = '{{ ds }}';

    INSERT INTO NIMBUSBILL.GOLD.FACT_CUSTOMER_DAILY_USAGE (
        DATE_ID, CUSTOMER_SK, PRODUCT_ID, UNIT, TOTAL_QUANTITY, BILLABLE_QUANTITY, COST_AMOUNT, CURRENCY, RATE_SK, LOAD_TS, BATCH_ID
    )
    SELECT
        agg.EVENT_DATE,
        c.CUSTOMER_SK,
        agg.PRODUCT_ID,
        agg.UNIT,
        agg.TOTAL_QUANTITY,
        agg.TOTAL_QUANTITY,
        (agg.TOTAL_QUANTITY * p.UNIT_PRICE),
        p.CURRENCY,
        p.RATE_SK,
        CURRENT_TIMESTAMP(),
        '{{ run_id }}'
    FROM NIMBUSBILL.SILVER.USAGE_DAILY_AGG agg
    JOIN NIMBUSBILL.GOLD.DIM_CUSTOMER c ON agg.CUSTOMER_ID = c.CUSTOMER_ID AND c.IS_CURRENT = TRUE
    JOIN NIMBUSBILL.GOLD.DIM_PRICING_RATE p ON agg.PRODUCT_ID = p.PRODUCT_ID AND agg.UNIT = p.UNIT 
        AND (agg.EVENT_DATE BETWEEN p.EFFECTIVE_FROM AND COALESCE(p.EFFECTIVE_TO, '9999-12-31'))
    WHERE agg.EVENT_DATE = '{{ ds }}';
    """,
    snowflake_conn_id='snowflake_default',
    dag=dag,
)

dq_check_duplicates = SnowflakeOperator(
    task_id='dq_check_duplicates',
    sql="""
    SELECT 1 / IFF(COUNT(*) > 0, 0, 1)
    FROM (SELECT EVENT_ID FROM NIMBUSBILL.SILVER.USAGE_EVENTS_CLEAN GROUP BY EVENT_ID HAVING COUNT(*) > 1);
    """,
    snowflake_conn_id='snowflake_default',
    dag=dag,
)

audit_log = SnowflakeOperator(
    task_id='write_pipeline_audit',
    sql="""
    INSERT INTO NIMBUSBILL.OPS.PIPELINE_RUN_AUDIT (RUN_ID, DAG_ID, TASK_ID, EXECUTION_DATE, STATUS, CREATED_TS)
    VALUES ('{{ run_id }}', 'daily_usage_billing_pipeline', 'ALL', '{{ ts }}', 'SUCCESS', CURRENT_TIMESTAMP());
    """,
    snowflake_conn_id='snowflake_default',
    dag=dag,
)

ingest_bronze >> silver_clean_merge >> silver_daily_agg >> gold_daily_costs >> dq_check_duplicates >> audit_log
