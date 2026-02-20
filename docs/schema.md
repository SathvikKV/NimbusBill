# NimbusBill Database Schema

## ER Diagram (Conceptual)
```mermaid
erDiagram
    DIM_CUSTOMER ||--o{ FACT_INVOICES : has
    DIM_CUSTOMER ||--o{ FACT_CUSTOMER_DAILY_USAGE : generates
    FACT_INVOICES ||--|{ FACT_INVOICE_LINE_ITEMS : contains
    DIM_PRICING_RATE ||--o{ FACT_CUSTOMER_DAILY_USAGE : prices
    DIM_PRODUCT ||--o{ FACT_CUSTOMER_DAILY_USAGE : describes
```

## Table Definitions

### BRONZE (Raw)
- `USAGE_EVENTS_RAW`: Partitioned by `DT`. Full JSON in `RAW` variant.

### SILVER (Clean)
- `USAGE_EVENTS_CLEAN`: Primary Key `EVENT_ID`. Deduplicated.
- `USAGE_DAILY_AGG`: Aggregated by `DATE, CUSTOMER, PRODUCT`. Source for billing.

### GOLD (Business)
- `DIM_CUSTOMER`: SCD Type 2. Validation key for billing.
- `FACT_INVOICES`: The legal bill. Columns: `SUBTOTAL`, `TAX`, `TOTAL`.
- `FACT_INVOICE_LINE_ITEMS`:
  - `LINE_TYPE`: 'usage', 'base_fee', 'adjustment'.
  - `AMOUNT`: The financial impact.
