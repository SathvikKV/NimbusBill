from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, datetime
from io import BytesIO
import snowflake.connector
import os
from dotenv import load_dotenv

load_dotenv()

SNOWFLAKE_CONFIG = {
    "account":   os.environ["SNOWFLAKE_ACCOUNT"],
    "user":      os.environ["SNOWFLAKE_USER"],
    "password":  os.environ["SNOWFLAKE_PASSWORD"],
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
    "database":  os.getenv("SNOWFLAKE_DATABASE",  "NIMBUSBILL"),
    "schema":    os.getenv("SNOWFLAKE_SCHEMA",    "PUBLIC"),
}


def get_connection():
    """Create a new Snowflake connection."""
    return snowflake.connector.connect(**SNOWFLAKE_CONFIG)


def query(sql: str, params: dict | None = None) -> list[dict]:
    """Execute a SQL query and return rows as list of dicts."""
    conn = get_connection()
    try:
        cur = conn.cursor(snowflake.connector.DictCursor)
        cur.execute(sql, params or {})
        rows = cur.fetchall()
        return [{k.lower(): v for k, v in row.items()} for row in rows]
    finally:
        conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        conn = get_connection()
        conn.cursor().execute("SELECT 1")
        conn.close()
        print("Snowflake connection verified")
    except Exception as e:
        print(f"Snowflake connection failed: {e}")
    yield



app = FastAPI(
    title="NimbusBill API",
    version="2.0.0",
    description="Usage-based billing platform API — powered by Snowflake",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class Invoice(BaseModel):
    invoice_id: str
    customer_sk: int
    customer_name: Optional[str] = None
    billing_period_start: date
    billing_period_end: date
    issued_ts: Optional[datetime] = None
    status: str
    subtotal: float
    tax: float
    total: float
    currency: str

class LineItem(BaseModel):
    line_item_id: str
    line_type: str
    product_id: Optional[str] = None
    unit: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: float

class InvoiceDetail(Invoice):
    line_items: List[LineItem] = []

class Customer(BaseModel):
    customer_sk: int
    customer_id: str
    customer_name: Optional[str] = None
    status: Optional[str] = None
    country: Optional[str] = None
    plan_id: Optional[str] = None
    is_current: bool = True

class DailyUsage(BaseModel):
    date_id: date
    product_id: str
    unit: str
    total_quantity: float
    cost_amount: float
    currency: Optional[str] = None

class DashboardSummary(BaseModel):
    total_revenue_mtd: float
    total_customers: int
    active_invoices: int
    total_events_today: int
    avg_daily_revenue: float

class PipelineStatus(BaseModel):
    run_id: Optional[str] = None
    dag_id: Optional[str] = None
    status: Optional[str] = None
    created_ts: Optional[datetime] = None


# Endpoints


@app.get("/health")
def health_check():
    """Health check with Snowflake connectivity test."""
    try:
        conn = get_connection()
        conn.cursor().execute("SELECT 1")
        conn.close()
        return {"status": "ok", "snowflake": "connected"}
    except Exception as e:
        return {"status": "degraded", "snowflake": str(e)}



@app.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary():
    """Aggregated KPIs for the dashboard overview."""
    rows = query("""
        SELECT
            COALESCE(SUM(f.COST_AMOUNT), 0) AS total_revenue_mtd,
            (SELECT COUNT(DISTINCT CUSTOMER_ID) FROM NIMBUSBILL.GOLD.DIM_CUSTOMER WHERE IS_CURRENT = TRUE) AS total_customers,
            (SELECT COUNT(*) FROM NIMBUSBILL.GOLD.FACT_INVOICES WHERE STATUS = 'issued') AS active_invoices,
            (SELECT COUNT(*) FROM NIMBUSBILL.SILVER.USAGE_EVENTS_CLEAN WHERE EVENT_DATE = CURRENT_DATE()) AS total_events_today,
            COALESCE(AVG(daily_total), 0) AS avg_daily_revenue
        FROM NIMBUSBILL.GOLD.FACT_CUSTOMER_DAILY_USAGE f
        LEFT JOIN (
            SELECT DATE_ID, SUM(COST_AMOUNT) AS daily_total
            FROM NIMBUSBILL.GOLD.FACT_CUSTOMER_DAILY_USAGE
            GROUP BY DATE_ID
        ) d ON 1=1
        WHERE f.DATE_ID >= DATE_TRUNC('MONTH', CURRENT_DATE())
    """)
    if rows:
        return DashboardSummary(**rows[0])
    return DashboardSummary(
        total_revenue_mtd=0, total_customers=0,
        active_invoices=0, total_events_today=0, avg_daily_revenue=0
    )



@app.get("/customers", response_model=List[Customer])
def list_customers(status: Optional[str] = None):
    """List all current customers, optionally filtered by status."""
    sql = """
        SELECT CUSTOMER_SK, CUSTOMER_ID, CUSTOMER_NAME, STATUS, COUNTRY, PLAN_ID, IS_CURRENT
        FROM NIMBUSBILL.GOLD.DIM_CUSTOMER
        WHERE IS_CURRENT = TRUE
    """
    if status:
        sql += f" AND STATUS = '{status}'"
    sql += " ORDER BY CUSTOMER_NAME"
    return [Customer(**r) for r in query(sql)]


@app.get("/customers/{customer_id}/usage", response_model=List[DailyUsage])
def get_customer_usage(
    customer_id: str,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    """Daily usage breakdown for a specific customer."""
    sql = """
        SELECT f.DATE_ID, f.PRODUCT_ID, f.UNIT, f.TOTAL_QUANTITY, f.COST_AMOUNT, f.CURRENCY
        FROM NIMBUSBILL.GOLD.FACT_CUSTOMER_DAILY_USAGE f
        JOIN NIMBUSBILL.GOLD.DIM_CUSTOMER c ON f.CUSTOMER_SK = c.CUSTOMER_SK
        WHERE c.CUSTOMER_ID = %(cid)s AND c.IS_CURRENT = TRUE
    """
    params = {"cid": customer_id}
    if date_from:
        sql += " AND f.DATE_ID >= %(df)s"
        params["df"] = str(date_from)
    if date_to:
        sql += " AND f.DATE_ID <= %(dt)s"
        params["dt"] = str(date_to)
    sql += " ORDER BY f.DATE_ID DESC, f.PRODUCT_ID"
    return [DailyUsage(**r) for r in query(sql, params)]



@app.get("/invoices", response_model=List[Invoice])
def list_invoices(customer_id: Optional[str] = None, status: Optional[str] = None):
    """List invoices with optional customer and status filters."""
    sql = """
        SELECT
            i.INVOICE_ID, i.CUSTOMER_SK,
            c.CUSTOMER_NAME,
            i.BILLING_PERIOD_START, i.BILLING_PERIOD_END,
            i.ISSUED_TS, i.STATUS, i.SUBTOTAL, i.TAX, i.TOTAL, i.CURRENCY
        FROM NIMBUSBILL.GOLD.FACT_INVOICES i
        LEFT JOIN NIMBUSBILL.GOLD.DIM_CUSTOMER c ON i.CUSTOMER_SK = c.CUSTOMER_SK AND c.IS_CURRENT = TRUE
        WHERE 1=1
    """
    if customer_id:
        sql += f" AND c.CUSTOMER_ID = '{customer_id}'"
    if status:
        sql += f" AND i.STATUS = '{status}'"
    sql += " ORDER BY i.ISSUED_TS DESC"
    return [Invoice(**r) for r in query(sql)]


@app.get("/invoices/{invoice_id}", response_model=InvoiceDetail)
def get_invoice_detail(invoice_id: str):
    """Full invoice with line items."""
    inv_rows = query("""
        SELECT
            i.INVOICE_ID, i.CUSTOMER_SK,
            c.CUSTOMER_NAME,
            i.BILLING_PERIOD_START, i.BILLING_PERIOD_END,
            i.ISSUED_TS, i.STATUS, i.SUBTOTAL, i.TAX, i.TOTAL, i.CURRENCY
        FROM NIMBUSBILL.GOLD.FACT_INVOICES i
        LEFT JOIN NIMBUSBILL.GOLD.DIM_CUSTOMER c ON i.CUSTOMER_SK = c.CUSTOMER_SK AND c.IS_CURRENT = TRUE
        WHERE i.INVOICE_ID = %(iid)s
    """, {"iid": invoice_id})

    if not inv_rows:
        raise HTTPException(status_code=404, detail="Invoice not found")

    li_rows = query("""
        SELECT LINE_ITEM_ID, LINE_TYPE, PRODUCT_ID, UNIT, QUANTITY, UNIT_PRICE, AMOUNT
        FROM NIMBUSBILL.GOLD.FACT_INVOICE_LINE_ITEMS
        WHERE INVOICE_ID = %(iid)s
        ORDER BY LOAD_TS
    """, {"iid": invoice_id})

    return InvoiceDetail(
        **inv_rows[0],
        line_items=[LineItem(**li) for li in li_rows],
    )



@app.get("/invoices/{invoice_id}/pdf")
def download_invoice_pdf(invoice_id: str):
    """Generate and return a downloadable PDF for an invoice."""
    try:
        from fpdf import FPDF
    except ImportError:
        raise HTTPException(status_code=500, detail="fpdf2 not installed")


    inv_rows = query("""
        SELECT
            i.INVOICE_ID, i.CUSTOMER_SK,
            c.CUSTOMER_NAME, c.CUSTOMER_ID,
            i.BILLING_PERIOD_START, i.BILLING_PERIOD_END,
            i.ISSUED_TS, i.STATUS, i.SUBTOTAL, i.TAX, i.TOTAL, i.CURRENCY
        FROM NIMBUSBILL.GOLD.FACT_INVOICES i
        LEFT JOIN NIMBUSBILL.GOLD.DIM_CUSTOMER c ON i.CUSTOMER_SK = c.CUSTOMER_SK AND c.IS_CURRENT = TRUE
        WHERE i.INVOICE_ID = %(iid)s
    """, {"iid": invoice_id})
    if not inv_rows:
        raise HTTPException(status_code=404, detail="Invoice not found")
    inv = inv_rows[0]


    li_rows = query("""
        SELECT LINE_ITEM_ID, LINE_TYPE, PRODUCT_ID, UNIT, QUANTITY, UNIT_PRICE, AMOUNT
        FROM NIMBUSBILL.GOLD.FACT_INVOICE_LINE_ITEMS
        WHERE INVOICE_ID = %(iid)s
        ORDER BY LOAD_TS
    """, {"iid": invoice_id})


    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()


    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 14, "NimbusBill", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, "Usage-Based Billing Platform", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)


    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, f"INVOICE", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(95, 6, f"Invoice ID: {inv['invoice_id'][:16]}...")
    pdf.cell(95, 6, f"Status: {inv['status'].upper()}", new_x="LMARGIN", new_y="NEXT")
    period_start = str(inv.get('billing_period_start', ''))[:10]
    period_end = str(inv.get('billing_period_end', ''))[:10]
    pdf.cell(95, 6, f"Period: {period_start} to {period_end}")
    issued = str(inv.get('issued_ts', ''))[:10]
    pdf.cell(95, 6, f"Issued: {issued}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)


    pdf.set_fill_color(248, 250, 252)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, "Bill To", new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"{inv.get('customer_name', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Customer ID: {inv.get('customer_id', inv.get('customer_sk', 'N/A'))}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)


    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(99, 102, 241)
    pdf.set_text_color(255, 255, 255)
    col_widths = [55, 25, 30, 30, 25, 25]
    headers = ["Product", "Type", "Quantity", "Unit", "Unit Price", "Amount"]
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, border=1, fill=True, align="C")
    pdf.ln()


    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    fill = False
    for li in li_rows:
        if fill:
            pdf.set_fill_color(248, 250, 252)
        else:
            pdf.set_fill_color(255, 255, 255)
        product_name = li['product_id'].replace('prod_', '').replace('_', ' ').title()
        pdf.cell(col_widths[0], 7, product_name, border=1, fill=True)
        pdf.cell(col_widths[1], 7, str(li.get('line_type', 'usage')), border=1, fill=True, align="C")
        pdf.cell(col_widths[2], 7, f"{li['quantity']:.2f}", border=1, fill=True, align="R")
        pdf.cell(col_widths[3], 7, str(li.get('unit', '')), border=1, fill=True, align="C")
        pdf.cell(col_widths[4], 7, f"${li['unit_price']:.4f}", border=1, fill=True, align="R")
        pdf.cell(col_widths[5], 7, f"${li['amount']:.2f}", border=1, fill=True, align="R")
        pdf.ln()
        fill = not fill

    pdf.ln(4)


    x_label = 120
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(71, 85, 105)
    pdf.set_x(x_label)
    pdf.cell(40, 7, "Subtotal:", align="R")
    pdf.cell(30, 7, f"${float(inv.get('subtotal', 0)):.2f}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(x_label)
    pdf.cell(40, 7, "Tax:", align="R")
    pdf.cell(30, 7, f"${float(inv.get('tax', 0)):.2f}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.set_x(x_label)
    pdf.cell(40, 9, "Total:", align="R")
    pdf.cell(30, 9, f"${float(inv.get('total', 0)):.2f}  {inv.get('currency', 'USD')}", align="R", new_x="LMARGIN", new_y="NEXT")


    pdf.ln(12)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 5, "Generated by NimbusBill | Usage-Based Billing Platform", align="C")


    buf = BytesIO(pdf.output())
    buf.seek(0)
    filename = f"invoice_{invoice_id[:8]}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )



@app.get("/usage", response_model=List[DailyUsage])
def get_usage(
    customer_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    product_id: Optional[str] = None,
):
    """Flexible usage query across all customers or filtered."""
    sql = """
        SELECT
            f.DATE_ID, f.PRODUCT_ID, f.UNIT,
            SUM(f.TOTAL_QUANTITY) AS TOTAL_QUANTITY,
            SUM(f.COST_AMOUNT) AS COST_AMOUNT,
            MAX(f.CURRENCY) AS CURRENCY
        FROM NIMBUSBILL.GOLD.FACT_CUSTOMER_DAILY_USAGE f
        JOIN NIMBUSBILL.GOLD.DIM_CUSTOMER c ON f.CUSTOMER_SK = c.CUSTOMER_SK AND c.IS_CURRENT = TRUE
        WHERE f.DATE_ID >= DATEADD('day', -90, CURRENT_DATE())
    """
    params: dict = {}
    if customer_id:
        sql += " AND c.CUSTOMER_ID = %(cid)s"
        params["cid"] = customer_id
    if date_from:
        sql += " AND f.DATE_ID >= %(df)s"
        params["df"] = str(date_from)
    if date_to:
        sql += " AND f.DATE_ID <= %(dt)s"
        params["dt"] = str(date_to)
    if product_id:
        sql += " AND f.PRODUCT_ID = %(pid)s"
        params["pid"] = product_id
    sql += " GROUP BY f.DATE_ID, f.PRODUCT_ID, f.UNIT ORDER BY f.DATE_ID DESC LIMIT 5000"
    return [DailyUsage(**r) for r in query(sql, params)]



@app.get("/pipeline/status", response_model=List[PipelineStatus])
def get_pipeline_status(limit: int = 10):
    """Latest pipeline run statuses from the audit table."""
    rows = query(f"""
        SELECT RUN_ID, DAG_ID, STATUS, CREATED_TS
        FROM NIMBUSBILL.OPS.PIPELINE_RUN_AUDIT
        ORDER BY CREATED_TS DESC
        LIMIT {limit}
    """)
    return [PipelineStatus(**r) for r in rows]



@app.get("/pricing")
def get_pricing():
    """Current pricing rates."""
    return query("""
        SELECT PRODUCT_ID, PLAN_ID, UNIT, UNIT_PRICE, CURRENCY, EFFECTIVE_FROM, EFFECTIVE_TO
        FROM NIMBUSBILL.GOLD.DIM_PRICING_RATE
        WHERE IS_CURRENT = TRUE
        ORDER BY PRODUCT_ID, PLAN_ID
    """)
