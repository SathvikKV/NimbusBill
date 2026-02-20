"""
load_seed_data.py

Loads reference data (products, plans, customers, pricing) into
Snowflake via Bronze ingestion + Gold dimension updates.
"""
import snowflake.connector
import os
import glob
from dotenv import load_dotenv

load_dotenv()

ACCOUNT   = os.environ["SNOWFLAKE_ACCOUNT"]
USER      = os.environ["SNOWFLAKE_USER"]
PASSWORD  = os.environ["SNOWFLAKE_PASSWORD"]
WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
DATABASE  = os.getenv("SNOWFLAKE_DATABASE",  "NIMBUSBILL")


def get_connection():
    return snowflake.connector.connect(
        user=USER, password=PASSWORD, account=ACCOUNT,
        warehouse=WAREHOUSE, database=DATABASE, schema="PUBLIC",
    )


def load_products(cursor):
    print("Loading products...")
    path = os.path.abspath("seeds/products.csv")
    cursor.execute(f"PUT file://{path} @NIMBUSBILL.GOLD.%DIM_PRODUCT AUTO_COMPRESS=TRUE")
    cursor.execute("""
        COPY INTO NIMBUSBILL.GOLD.DIM_PRODUCT
        FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1)
        ON_ERROR = 'CONTINUE'
    """)


def load_plans(cursor):
    print("Loading plans...")
    path = os.path.abspath("seeds/plans.csv")
    cursor.execute(f"PUT file://{path} @NIMBUSBILL.GOLD.%DIM_PLAN AUTO_COMPRESS=TRUE")
    cursor.execute("""
        COPY INTO NIMBUSBILL.GOLD.DIM_PLAN
        FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1)
        ON_ERROR = 'CONTINUE'
    """)


def load_customers(cursor):
    print("Loading customers...")
    files = glob.glob("datagen/data/customers_*.jsonl")
    if not files:
        print("  No customer files found in datagen/data/")
        return

    latest = max(files, key=os.path.getctime)
    abs_path = os.path.abspath(latest)

    cursor.execute("DELETE FROM NIMBUSBILL.BRONZE.CUSTOMERS_RAW WHERE BATCH_ID = 'SEED_LOAD'")
    cursor.execute(f"PUT file://{abs_path} @NIMBUSBILL.BRONZE.%CUSTOMERS_RAW AUTO_COMPRESS=TRUE OVERWRITE=TRUE")
    cursor.execute("""
        COPY INTO NIMBUSBILL.BRONZE.CUSTOMERS_RAW (INGEST_TS, DT, BATCH_ID, RAW)
        FROM (
            SELECT CURRENT_TIMESTAMP(), CURRENT_DATE(), 'SEED_LOAD', $1
            FROM @NIMBUSBILL.BRONZE.%CUSTOMERS_RAW
        )
        FILE_FORMAT = (TYPE = 'JSON')
    """)

    cursor.execute("""
        MERGE INTO NIMBUSBILL.GOLD.DIM_CUSTOMER T
        USING (
            SELECT
                RAW:customer_id::STRING   AS CUSTOMER_ID,
                RAW:customer_name::STRING AS CUSTOMER_NAME,
                RAW:status::STRING        AS STATUS,
                RAW:country::STRING       AS COUNTRY,
                RAW:plan_id::STRING       AS PLAN_ID,
                CURRENT_TIMESTAMP()       AS EFFECTIVE_START
            FROM NIMBUSBILL.BRONZE.CUSTOMERS_RAW
            WHERE BATCH_ID = 'SEED_LOAD'
        ) S ON T.CUSTOMER_ID = S.CUSTOMER_ID
        WHEN MATCHED THEN UPDATE SET
            T.CUSTOMER_NAME = S.CUSTOMER_NAME,
            T.STATUS = S.STATUS,
            T.PLAN_ID = S.PLAN_ID,
            T.IS_CURRENT = TRUE
        WHEN NOT MATCHED THEN INSERT
            (CUSTOMER_ID, CUSTOMER_NAME, STATUS, COUNTRY, PLAN_ID, EFFECTIVE_START, IS_CURRENT)
            VALUES (S.CUSTOMER_ID, S.CUSTOMER_NAME, S.STATUS, S.COUNTRY, S.PLAN_ID, S.EFFECTIVE_START, TRUE)
    """)


def load_pricing(cursor):
    print("Loading pricing catalog...")
    path = os.path.abspath("datagen/data/pricing_catalog.csv")
    if not os.path.exists(path):
        print(f"  Not found: {path}")
        return

    cursor.execute("DELETE FROM NIMBUSBILL.BRONZE.PRICING_CATALOG_RAW WHERE BATCH_ID = 'SEED_LOAD'")
    cursor.execute(f"PUT file://{path} @NIMBUSBILL.BRONZE.%PRICING_CATALOG_RAW AUTO_COMPRESS=TRUE OVERWRITE=TRUE")
    cursor.execute("""
        COPY INTO NIMBUSBILL.BRONZE.PRICING_CATALOG_RAW (INGEST_TS, DT, BATCH_ID, RAW)
        FROM (
            SELECT
                CURRENT_TIMESTAMP(), CURRENT_DATE(), 'SEED_LOAD',
                OBJECT_CONSTRUCT(
                    'product_id', $2, 'plan_id', $3, 'unit', $4,
                    'price', $5, 'currency', $6,
                    'effective_from', $7, 'effective_to', $8
                )
            FROM @NIMBUSBILL.BRONZE.%PRICING_CATALOG_RAW
        )
        FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1)
    """)

    cursor.execute("""
        INSERT INTO NIMBUSBILL.GOLD.DIM_PRICING_RATE
            (PRODUCT_ID, PLAN_ID, UNIT, UNIT_PRICE, CURRENCY, EFFECTIVE_FROM, EFFECTIVE_TO, IS_CURRENT)
        SELECT
            RAW:product_id::STRING, RAW:plan_id::STRING, RAW:unit::STRING,
            RAW:price::FLOAT, RAW:currency::STRING,
            RAW:effective_from::DATE, TRY_CAST(RAW:effective_to::STRING AS DATE),
            TRUE
        FROM NIMBUSBILL.BRONZE.PRICING_CATALOG_RAW
        WHERE BATCH_ID = 'SEED_LOAD'
    """)


def main():
    conn = get_connection()
    cur = conn.cursor()
    try:
        load_products(cur)
        load_plans(cur)
        load_customers(cur)
        load_pricing(cur)
        print("All reference data loaded.")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
