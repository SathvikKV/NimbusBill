# NimbusBill Frontend — Vercel v0 Specification

## Overview

Build a **premium, dark-themed billing dashboard** for NimbusBill — a usage-based billing platform. The dashboard consumes a FastAPI backend (running at `http://localhost:8000`) and displays real billing data from Snowflake.

**Tech Stack**: Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, Recharts for charts.

---

## Design Language

- **Theme**: Dark mode primary (slate-900/950 backgrounds), with subtle purple/blue accent gradients
- **Style**: Glassmorphism cards with `backdrop-blur`, subtle border glow effects, smooth micro-animations
- **Typography**: Inter font, clean hierarchy
- **Colors**:
  - Background: `#0f172a` (slate-900)
  - Cards: `rgba(30, 41, 59, 0.8)` with backdrop blur
  - Primary accent: Purple-to-blue gradient (`#8b5cf6` → `#3b82f6`)
  - Success: `#22c55e`, Warning: `#f59e0b`, Error: `#ef4444`
  - Text: `#f1f5f9` (primary), `#94a3b8` (secondary)
- **Animations**: Fade-in on page load, hover scale on cards, smooth number counters for KPIs

---

## Pages & Components

### 1. Sidebar Navigation (Persistent)

A vertical sidebar on the left side with icon + label links:
- ☁️ **NimbusBill** (logo/brand at top)
- 📊 **Dashboard** (`/`)
- 👥 **Customers** (`/customers`)
- 📄 **Invoices** (`/invoices`)
- 📈 **Usage Explorer** (`/usage`)
- 💰 **Pricing** (`/pricing`)
- ⚙️ **Pipeline Status** (`/pipeline`)

The sidebar should be collapsible, show active page highlight, and use icons from Lucide React.

---

### 2. Dashboard Page (`/`) — Main Overview

**API Endpoint**: `GET /dashboard/summary`

**Response format**:
```json
{
  "total_revenue_mtd": 1250.75,
  "total_customers": 10,
  "active_invoices": 2,
  "total_events_today": 47,
  "avg_daily_revenue": 625.38
}
```

**Layout**:

#### Row 1: KPI Cards (4 cards, grid)
| Card | Value Source | Icon | Accent Color |
|------|-------------|------|-------------|
| Total Revenue (MTD) | `total_revenue_mtd` | DollarSign | Purple gradient |
| Active Customers | `total_customers` | Users | Blue |
| Pending Invoices | `active_invoices` | FileText | Amber |
| Events Today | `total_events_today` | Activity | Green |

Each card should have:
- Icon in a rounded colored background
- Large bold number (animated counter on load)
- Label below in muted text
- Subtle hover lift effect

#### Row 2: Charts (2 columns)
**Left: Revenue Over Time** (Line chart)
- API: `GET /usage` → aggregate `cost_amount` by `date_id`
- X-axis: dates, Y-axis: revenue
- Purple gradient fill under the line
- Tooltip on hover showing date + revenue

**Right: Usage by Product** (Bar chart)
- API: `GET /usage` → aggregate `total_quantity` by `product_id`
- Horizontal bars with product labels
- Color-coded by product

#### Row 3: Recent Activity (Table)
- Latest 5 invoices from `GET /invoices`
- Columns: Invoice ID, Customer, Amount, Status (badge), Date
- Status badges: `issued` = blue, `paid` = green, `draft` = gray
- Clickable rows → navigate to `/invoices/{id}`

---

### 3. Customers Page (`/customers`)

**API Endpoint**: `GET /customers`

**Response format** (array):
```json
[
  {
    "customer_sk": 1,
    "customer_id": "cust_1",
    "customer_name": "Acme Corp",
    "status": "active",
    "country": "US",
    "plan_id": "plan_pro",
    "is_current": true
  }
]
```

**Layout**:
- Search bar at top (filter client-side by name)
- Grid of customer cards, each showing:
  - Customer name (bold)
  - Status badge (active = green, churned = red, trial = yellow)
  - Country flag emoji
  - Plan badge (starter/pro/enterprise with different colors)
- Click a card → navigate to customer detail

#### Customer Detail (`/customers/[id]`)
- **API**: `GET /customers/{customer_id}/usage`
- Header: Customer name, status, plan, country
- Chart: Daily usage trend (line chart of `cost_amount` over `date_id`)
- Table: Usage breakdown by product with quantity and cost columns

---

### 4. Invoices Page (`/invoices`)

**API Endpoint**: `GET /invoices`

**Response format** (array):
```json
[
  {
    "invoice_id": "abc-123",
    "customer_sk": 1,
    "customer_name": "Acme Corp",
    "billing_period_start": "2024-01-01",
    "billing_period_end": "2024-01-31",
    "issued_ts": "2024-02-01T04:00:00",
    "status": "issued",
    "subtotal": 125.50,
    "tax": 0.0,
    "total": 125.50,
    "currency": "USD"
  }
]
```

**Layout**:
- Filter bar with dropdowns: Status (all/issued/paid/draft), Customer
- Table with columns: Invoice ID (truncated), Customer, Period, Total, Status (badge), Actions
- Click row → navigate to invoice detail

#### Invoice Detail Page (`/invoices/[id]`)
- **API**: `GET /invoices/{invoice_id}`
- **Additional response field**: `line_items` array:
```json
{
  "line_items": [
    {
      "line_item_id": "li_1",
      "line_type": "usage",
      "product_id": "prod_api_requests",
      "unit": "requests",
      "quantity": 10000,
      "unit_price": 0.0001,
      "amount": 1.00
    }
  ]
}
```

**Layout**:
- Invoice header card: ID, customer, billing period, total, status
- Line items table: Product, Type, Quantity, Unit Price, Amount
- Summary section at bottom: Subtotal, Tax, **Total** (bold large)

---

### 5. Usage Explorer Page (`/usage`)

**API Endpoint**: `GET /usage?date_from=...&date_to=...&product_id=...&customer_id=...`

**Response format** (array):
```json
[
  {
    "date_id": "2024-01-15",
    "product_id": "prod_api_requests",
    "unit": "requests",
    "total_quantity": 150.0,
    "cost_amount": 0.015,
    "currency": "USD"
  }
]
```

**Layout**:
- Filters bar: Date range picker, Product dropdown, Customer dropdown
- Main chart: Stacked area chart of usage by product over time
- Table below: Date, Product, Unit, Quantity, Cost — sortable columns

---

### 6. Pricing Page (`/pricing`)

**API Endpoint**: `GET /pricing`

**Response format** (array):
```json
[
  {
    "product_id": "prod_api_requests",
    "plan_id": "plan_starter",
    "unit": "requests",
    "unit_price": 0.0001,
    "currency": "USD",
    "effective_from": "2024-01-01",
    "effective_to": null
  }
]
```

**Layout**:
- Group by plan (tabs or sections: Free, Starter, Pro, Enterprise)
- Each plan section shows a pricing card grid:
  - Product name, unit, price per unit
  - Effective date range
- Use a modern pricing table aesthetic (similar to SaaS pricing pages)

---

### 7. Pipeline Status Page (`/pipeline`)

**API Endpoint**: `GET /pipeline/status?limit=20`

**Response format** (array):
```json
[
  {
    "run_id": "manual__2024-01-15T02:00:00+00:00",
    "dag_id": "daily_usage_billing_pipeline",
    "status": "SUCCESS",
    "created_ts": "2024-01-15T02:05:32"
  }
]
```

**Layout**:
- Timeline view showing pipeline runs
- Each entry: DAG name, status (color-coded badge: SUCCESS=green, FAILED=red, RUNNING=blue), timestamp
- Refresh button to re-fetch

---

## Data Fetching Pattern

Use this pattern for all pages:

```typescript
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchDashboardSummary() {
  const res = await fetch(`${API_BASE}/dashboard/summary`);
  if (!res.ok) throw new Error('Failed to fetch dashboard summary');
  return res.json();
}

export async function fetchInvoices(params?: { customer_id?: string; status?: string }) {
  const url = new URL(`${API_BASE}/invoices`);
  if (params?.customer_id) url.searchParams.set('customer_id', params.customer_id);
  if (params?.status) url.searchParams.set('status', params.status);
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error('Failed to fetch invoices');
  return res.json();
}

// ... similar for all endpoints
```

Use `'use client'` components with `useEffect` + `useState` for data fetching, or React Server Components where appropriate.

---

## Environment Variable

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Important Notes for v0

1. **This is a data engineering portfolio project** — the dashboard should look premium and impressive
2. **All data comes from the API** — do NOT use hardcoded/mock data in the frontend
3. **Handle loading states** — show skeleton loaders while API data loads
4. **Handle empty states** — show a friendly message if no data exists yet
5. **Handle errors** — show error boundaries with retry buttons
6. **Format numbers properly** — use `Intl.NumberFormat` for currency and large numbers
7. **Responsive** — should work on desktop and tablet widths
8. The API returns **lowercase keys** (e.g., `invoice_id`, not `INVOICE_ID`)
