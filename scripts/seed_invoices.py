"""
seed_invoices.py

Generate invoices and line items from existing FACT_CUSTOMER_DAILY_USAGE data.
Groups usage by customer and month, creates invoice headers and per-product line items.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import snowflake.connector
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


def main():
    conn = get_connection()
    cur = conn.cursor()

    try:
        print("Generating invoice headers from usage data...")
        cur.execute("""
            INSERT INTO NIMBUSBILL.GOLD.FACT_INVOICES (
                INVOICE_ID, CUSTOMER_SK, BILLING_PERIOD_START, BILLING_PERIOD_END,
                ISSUED_TS, STATUS, SUBTOTAL, TAX, TOTAL, CURRENCY, LOAD_TS, BATCH_ID
            )
            SELECT
                UUID_STRING(),
                CUSTOMER_SK,
                DATE_TRUNC('MONTH', MIN(DATE_ID))::DATE,
                LAST_DAY(MAX(DATE_ID)),
                CURRENT_TIMESTAMP(),
                'issued',
                SUM(COST_AMOUNT),
                ROUND(SUM(COST_AMOUNT) * 0.08, 2),
                ROUND(SUM(COST_AMOUNT) * 1.08, 2),
                MAX(CURRENCY),
                CURRENT_TIMESTAMP(),
                'seed_invoices'
            FROM NIMBUSBILL.GOLD.FACT_CUSTOMER_DAILY_USAGE
            WHERE DATE_ID >= DATE_TRUNC('MONTH', CURRENT_DATE()) - INTERVAL '2 MONTHS'
            GROUP BY CUSTOMER_SK, DATE_TRUNC('MONTH', DATE_ID)
            HAVING SUM(COST_AMOUNT) > 0
        """)
        inv_count = cur.rowcount
        print(f"  Created {inv_count} invoices.")

        print("Generating line items per product...")
        cur.execute("""
            INSERT INTO NIMBUSBILL.GOLD.FACT_INVOICE_LINE_ITEMS (
                INVOICE_ID, LINE_ITEM_ID, LINE_TYPE, PRODUCT_ID, UNIT,
                QUANTITY, UNIT_PRICE, AMOUNT, RATE_SK,
                USAGE_WINDOW_START, USAGE_WINDOW_END, CALC_BATCH_ID, LOAD_TS
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
                MAX(u.RATE_SK),
                MIN(u.DATE_ID),
                MAX(u.DATE_ID),
                'seed_invoices',
                CURRENT_TIMESTAMP()
            FROM NIMBUSBILL.GOLD.FACT_CUSTOMER_DAILY_USAGE u
            JOIN NIMBUSBILL.GOLD.FACT_INVOICES inv
                ON u.CUSTOMER_SK = inv.CUSTOMER_SK
                AND u.DATE_ID BETWEEN inv.BILLING_PERIOD_START AND inv.BILLING_PERIOD_END
            LEFT JOIN NIMBUSBILL.GOLD.DIM_PRICING_RATE r ON u.RATE_SK = r.RATE_SK
            WHERE inv.BATCH_ID = 'seed_invoices'
            GROUP BY inv.INVOICE_ID, u.PRODUCT_ID, u.UNIT
        """)
        li_count = cur.rowcount
        print(f"  Created {li_count} line items.")

        conn.commit()
        print(f"Done. {inv_count} invoices with {li_count} line items seeded.")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
