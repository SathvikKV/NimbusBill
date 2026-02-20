"""
init_snowflake.py

Runs the DDL scripts (sql/00–05) to create all Snowflake databases,
schemas, tables, and views. Idempotent — safe to re-run.
"""
import snowflake.connector
import os
from dotenv import load_dotenv

load_dotenv()

ACCOUNT   = os.environ["SNOWFLAKE_ACCOUNT"]
USER      = os.environ["SNOWFLAKE_USER"]
PASSWORD  = os.environ["SNOWFLAKE_PASSWORD"]
WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")


def get_connection():
    return snowflake.connector.connect(
        user=USER, password=PASSWORD,
        account=ACCOUNT, warehouse=WAREHOUSE,
    )


def run_sql_file(cursor, filepath):
    print(f"Running {filepath}...")
    with open(filepath, "r") as f:
        lines = [l for l in f.readlines() if not l.strip().startswith("--")]
        sql_content = "".join(lines)

    for stmt in (s.strip() for s in sql_content.split(";") if s.strip()):
        try:
            cursor.execute(stmt)
        except Exception as e:
            print(f"  Error: {stmt[:60]}...\n  {e}")

    print(f"  Done.")


def main():
    conn = get_connection()
    cur = conn.cursor()

    sql_dir = os.path.join(os.path.dirname(__file__), "..", "sql")
    ddl_files = [
        "00_create_db_schemas.sql",
        "01_create_bronze_tables.sql",
        "02_create_silver_tables.sql",
        "03_create_gold_tables.sql",
        "04_create_ops_tables.sql",
        "05_views_and_helpers.sql",
    ]

    for filename in ddl_files:
        path = os.path.join(sql_dir, filename)
        if os.path.exists(path):
            run_sql_file(cur, path)
        else:
            print(f"  Skipped (not found): {path}")

    cur.close()
    conn.close()
    print("Database initialization complete.")


if __name__ == "__main__":
    main()
