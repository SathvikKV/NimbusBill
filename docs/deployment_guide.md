# NimbusBill Deployment & Command Cheat Sheet

This guide lists every command required to set up, deploy, and run the NimbusBill platform.

## 0. Prerequisites
- Docker & Docker Compose
- Python 3.9+
- Node.js 18+
- Snowflake Account

## 1. Environment Setup

### 1.1 Configure Credentials
Create the Airflow environment file and add your Snowflake/AWS credentials.
```bash
# In ./airflow directory
cp .env.example .env 
# Edit .env with your actual Snowflake/AWS keys
# Format: snowflake://user:pass@account/DB/SCHEMA?warehouse=WH&role=ROLE
```

### 1.2 Python Setup
Create a virtual environment and install dependencies.
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r airflow/requirements.txt
pip install -r api/requirements.txt
```

## 2. Database Initialization (Snowflake)
Run the SQL scripts in your Snowflake Worksheet or via SnowSQL CLI.
Order matters!

1. `sql/00_create_db_schemas.sql`
2. `sql/01_create_bronze_tables.sql`
3. `sql/02_create_silver_tables.sql`
4. `sql/03_create_gold_tables.sql`
5. `sql/04_create_ops_tables.sql`
6. `sql/05_views_and_helpers.sql`
7. `sql/06_billing_calculations.sql` (Note: Logic file, check if specific init needed)
8. `sql/07_reconciliation.sql` (Note: Logic file)

## 3. Data Generation
Generate synthetic data for testing.
```bash
# From project root
python datagen/generate_pricing.py --output ./datagen/data
python datagen/generate_customers.py --output ./datagen/data
python datagen/generate_usage_events.py --date 2023-10-01 --output ./datagen/data
```
*Note: In a real deployment, upload these files to your S3 bucket.*

## 4. Launch Airflow (Orchestration)
Start the Airflow containers.
```bash
cd airflow
docker-compose up -d
```
- Access UI: http://localhost:8081
- Login: `admin` / `admin`
- Enable the DAGs: `daily_usage_billing_pipeline`, `month_end_invoice_close`, etc.

## 5. Launch API
Start the FastAPI backend service.
```bash
cd api
uvicorn main:app --reload --port 8000
```
- Swagger UI: http://localhost:8000/docs

## 6. Launch Frontend
Start the Next.js billing dashboard.
```bash
cd web
npm install
npm run dev
```
- Dashboard: http://localhost:3000

## 7. Verification Steps
1. **Trigger DAG**: Go to Airflow UI -> `daily_usage_billing_pipeline` -> Trigger DAG.
2. **Check Logs**: Ensure tasks `ingest_bronze`, `silver_clean_merge`, `gold_compute_daily_costs` succeed.
3. **Check API**: `curl http://localhost:8000/invoices`
4. **Check UI**: Visit http://localhost:3000/invoices to see generated data.

## Troubleshooting
- **Airflow Connection Failed**: Check `airflow/.env` connection string format.
- **Missing Data**: Ensure `datagen` scripts ran and files exist (or Snowflake loading logic finds them).
- **Docker Errors**: Run `docker-compose logs -f` to see container errors.
