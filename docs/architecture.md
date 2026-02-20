# NimbusBill Architecture

## Overview
NimbusBill uses a warehouse-native approach, treating the Data Warehouse (Snowflake) as the source of truth for billing.

## Medallion Layers

### Bronze (Raw)
- **Purpose**: Immutable history of all inputs.
- **Tables**: `USAGE_EVENTS_RAW`, `CUSTOMERS_RAW`, `PRICING_CATALOG_RAW`
- **Pattern**: Append-only, variant columns (JSON).

### Silver (Clean & Enriched)
- **Purpose**: Deduplication, schema enforcement, standardizing types.
- **Tables**: `USAGE_EVENTS_CLEAN`
- **Logic**:
  - `MERGE` on `event_id` to handle duplicate delivery.
  - Parsing JSON to typed columns.
  - Daily Aggregates (`USAGE_DAILY_AGG`) for performance.

### Gold (Business Layer)
- **Purpose**: Dimensional model for reporting and invoicing.
- **Tables**:
  - `DIM_CUSTOMER`, `DIM_PRICING_RATE` (SCD Type 2).
  - `FACT_CUSTOMER_DAILY_USAGE`: Daily costs per customer/product.
  - `FACT_INVOICES`: Monthly invoice headers.
  - `FACT_INVOICE_LINE_ITEMS`: Detailed line items.

## Orchestration (Airflow)

### 1. Daily Usage Pipeline
Runs at 2 AM.
1. Ingest Bronze.
2. Silver Clean & Dedupe.
3. Update Dimensions (SCD2).
4. Compute Daily Costs (Gold Fact).
5. DQ Checks.

### 2. Month-End Close
Runs on 1st of Month.
1. Freeze billing period (e.g., Oct 1-31).
2. Generate `FACT_INVOICES`.
3. Generate `FACT_INVOICE_LINE_ITEMS` from daily usage.
4. Verify Totals.

### 3. Late Arrival Reconciliation
Runs Daily at 6 AM.
1. Check for `USAGE_EVENTS_CLEAN` rows with `EVENT_DATE` in closed periods.
2. If `LOAD_TS` > `INVOICE_ISSUED_TS`:
   - Calculate price difference.
   - Insert `adjustment` line item to `FACT_INVOICE_LINE_ITEMS`.
   - Update Invoice Totals.
