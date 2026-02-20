"""
backfill_history.py

Generates N days of synthetic usage events and loads each day through
the full Bronze -> Silver -> Gold pipeline in Snowflake.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import snowflake.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv
from datagen.generate_usage_events import generate_events, save_events

load_dotenv()

ACCOUNT   = os.environ["SNOWFLAKE_ACCOUNT"]
USER      = os.environ["SNOWFLAKE_USER"]
PASSWORD  = os.environ["SNOWFLAKE_PASSWORD"]
WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
DATABASE  = os.getenv("SNOWFLAKE_DATABASE",  "NIMBUSBILL")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "datagen", "data")


def get_connection():
    return snowflake.connector.connect(
        user=USER, password=PASSWORD, account=ACCOUNT,
        warehouse=WAREHOUSE, database=DATABASE, schema="PUBLIC",
    )


def load_day(cursor, date_str: str, batch_id: str):
    """Load one day of events through Bronze -> Silver -> Gold."""
    file_path = os.path.abspath(
        os.path.join(DATA_DIR, f"usage_events_{date_str}.jsonl")
    )
    if not os.path.exists(file_path):
        print(f"  Warning: {file_path} not found, skipping")
        return

    # Bronze: stage and copy raw JSON
    cursor.execute(
        f"PUT file://{file_path} @NIMBUSBILL.BRONZE.%USAGE_EVENTS_RAW "
        f"AUTO_COMPRESS=TRUE OVERWRITE=TRUE"
    )
    cursor.execute(f"""
        COPY INTO NIMBUSBILL.BRONZE.USAGE_EVENTS_RAW
            (INGEST_TS, SOURCE, DT, BATCH_ID, FILE_NAME, RAW)
        FROM (
            SELECT CURRENT_TIMESTAMP(), 'BACKFILL', '{date_str}',
                   '{batch_id}', METADATA$FILENAME, $1
            FROM @NIMBUSBILL.BRONZE.%USAGE_EVENTS_RAW
        )
        FILE_FORMAT = (TYPE = 'JSON' STRIP_OUTER_ARRAY = FALSE)
        PURGE = TRUE
    """)

    # Silver: merge and deduplicate
    cursor.execute(f"""
        MERGE INTO NIMBUSBILL.SILVER.USAGE_EVENTS_CLEAN T
        USING (
            SELECT *
            FROM NIMBUSBILL.SILVER.V_USAGE_EVENTS_PARSED
            WHERE EVENT_DATE = '{date_str}'
            QUALIFY ROW_NUMBER() OVER (PARTITION BY EVENT_ID ORDER BY EVENT_TS DESC) = 1
        ) S
        ON T.EVENT_ID = S.EVENT_ID
        WHEN MATCHED THEN
            UPDATE SET T.LOAD_TS = CURRENT_TIMESTAMP(),
                       T.BATCH_ID = '{batch_id}', T.RAW_HASH = S.RAW_HASH
        WHEN NOT MATCHED THEN
            INSERT (EVENT_ID, EVENT_TS, EVENT_DATE, CUSTOMER_ID, PRODUCT_ID,
                    PLAN_ID, REGION, UNIT, QUANTITY, SOURCE, LOAD_TS, BATCH_ID, RAW_HASH)
            VALUES (S.EVENT_ID, S.EVENT_TS, S.EVENT_DATE, S.CUSTOMER_ID, S.PRODUCT_ID,
                    S.PLAN_ID, S.REGION, S.UNIT, S.QUANTITY, S.SOURCE,
                    CURRENT_TIMESTAMP(), '{batch_id}', S.RAW_HASH);
    """)

    # Silver: rebuild daily aggregates for this date
    cursor.execute(f"DELETE FROM NIMBUSBILL.SILVER.USAGE_DAILY_AGG WHERE EVENT_DATE = '{date_str}'")
    cursor.execute(f"""
        INSERT INTO NIMBUSBILL.SILVER.USAGE_DAILY_AGG
            (EVENT_DATE, CUSTOMER_ID, PRODUCT_ID, UNIT, TOTAL_QUANTITY,
             EVENT_COUNT, LAST_EVENT_TS, LOAD_TS, BATCH_ID)
        SELECT EVENT_DATE, CUSTOMER_ID, PRODUCT_ID, UNIT,
               SUM(QUANTITY), COUNT(*), MAX(EVENT_TS),
               CURRENT_TIMESTAMP(), '{batch_id}'
        FROM NIMBUSBILL.SILVER.USAGE_EVENTS_CLEAN
        WHERE EVENT_DATE = '{date_str}'
        GROUP BY 1, 2, 3, 4
    """)

    # Gold: compute daily costs
    cursor.execute(f"DELETE FROM NIMBUSBILL.GOLD.FACT_CUSTOMER_DAILY_USAGE WHERE DATE_ID = '{date_str}'")
    cursor.execute(f"""
        INSERT INTO NIMBUSBILL.GOLD.FACT_CUSTOMER_DAILY_USAGE
            (DATE_ID, CUSTOMER_SK, PRODUCT_ID, UNIT, TOTAL_QUANTITY,
             BILLABLE_QUANTITY, COST_AMOUNT, CURRENCY, RATE_SK, LOAD_TS, BATCH_ID)
        SELECT
            agg.EVENT_DATE, c.CUSTOMER_SK, agg.PRODUCT_ID, agg.UNIT,
            agg.TOTAL_QUANTITY, agg.TOTAL_QUANTITY,
            (agg.TOTAL_QUANTITY * p.UNIT_PRICE), p.CURRENCY, p.RATE_SK,
            CURRENT_TIMESTAMP(), '{batch_id}'
        FROM NIMBUSBILL.SILVER.USAGE_DAILY_AGG agg
        JOIN NIMBUSBILL.GOLD.DIM_CUSTOMER c
            ON agg.CUSTOMER_ID = c.CUSTOMER_ID AND c.IS_CURRENT = TRUE
        JOIN NIMBUSBILL.GOLD.DIM_PRICING_RATE p
            ON agg.PRODUCT_ID = p.PRODUCT_ID AND agg.UNIT = p.UNIT
            AND (agg.EVENT_DATE BETWEEN p.EFFECTIVE_FROM
                 AND COALESCE(p.EFFECTIVE_TO, '9999-12-31'))
        WHERE agg.EVENT_DATE = '{date_str}'
    """)


def main():
    parser = argparse.ArgumentParser(description="Backfill historical usage data")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--customers", type=int, default=10)
    parser.add_argument("--events", type=int, default=5, help="avg events per customer per day")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)

    today = datetime.now().date()
    dates = [(today - timedelta(days=d)).isoformat() for d in range(args.days, 0, -1)]

    print(f"Generating {args.days} days of usage events...")
    for d in dates:
        events = generate_events(
            d,
            num_customers=args.customers,
            events_per_customer=args.events,
            late_prob=0.02,
            duplicate_prob=0.01,
        )
        save_events(events, d, DATA_DIR)

    print("Loading into Snowflake (Bronze -> Silver -> Gold)...")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for i, d in enumerate(dates, 1):
            batch_id = f"backfill_{d}"
            print(f"  [{i:>2}/{len(dates)}] {d} ... ", end="", flush=True)
            load_day(cursor, d, batch_id)
            print("done")
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    print("Writing pipeline audit records...")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for d in dates:
            cursor.execute(f"""
                INSERT INTO NIMBUSBILL.OPS.PIPELINE_RUN_AUDIT
                    (RUN_ID, DAG_ID, TASK_ID, EXECUTION_DATE, STATUS, CREATED_TS)
                VALUES ('backfill_{d}', 'daily_usage_billing_pipeline', 'ALL',
                        '{d}', 'SUCCESS', CURRENT_TIMESTAMP())
            """)
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    print(f"Backfill complete: {args.days} days loaded.")


if __name__ == "__main__":
    main()
