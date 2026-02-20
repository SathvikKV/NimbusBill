const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface DashboardSummary {
  total_revenue_mtd: number;
  total_customers: number;
  active_invoices: number;
  total_events_today: number;
  avg_daily_revenue: number;
}

export interface Customer {
  customer_sk: number;
  customer_id: string;
  customer_name: string;
  status: string;
  country: string;
  plan_id: string;
  is_current: boolean;
}

export interface Invoice {
  invoice_id: string;
  customer_sk: number;
  customer_name: string;
  billing_period_start: string;
  billing_period_end: string;
  issued_ts: string;
  status: string;
  subtotal: number;
  tax: number;
  total: number;
  currency: string;
}

export interface LineItem {
  line_item_id: string;
  line_type: string;
  product_id: string;
  unit: string;
  quantity: number;
  unit_price: number;
  amount: number;
}

export interface InvoiceDetail extends Invoice {
  line_items: LineItem[];
}

export interface UsageRecord {
  date_id: string;
  product_id: string;
  unit: string;
  total_quantity: number;
  cost_amount: number;
  currency: string;
}

export interface PricingRecord {
  product_id: string;
  plan_id: string;
  unit: string;
  unit_price: number;
  currency: string;
  effective_from: string;
  effective_to: string | null;
}

export interface PipelineRun {
  run_id: string;
  dag_id: string;
  status: string;
  created_ts: string;
}

async function apiFetch<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value) url.searchParams.set(key, value);
    });
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

export function fetchDashboardSummary() {
  return apiFetch<DashboardSummary>('/dashboard/summary');
}

export function fetchCustomers() {
  return apiFetch<Customer[]>('/customers');
}

export function fetchCustomerUsage(customerId: string) {
  return apiFetch<UsageRecord[]>(`/customers/${customerId}/usage`);
}

export function fetchInvoices(params?: { customer_id?: string; status?: string }) {
  return apiFetch<Invoice[]>('/invoices', params as Record<string, string>);
}

export function fetchInvoiceDetail(invoiceId: string) {
  return apiFetch<InvoiceDetail>(`/invoices/${invoiceId}`);
}

export function fetchUsage(params?: { date_from?: string; date_to?: string; product_id?: string; customer_id?: string }) {
  return apiFetch<UsageRecord[]>('/usage', params as Record<string, string>);
}

export function fetchPricing() {
  return apiFetch<PricingRecord[]>('/pricing');
}

export function fetchPipelineStatus(limit = 20) {
  return apiFetch<PipelineRun[]>('/pipeline/status', { limit: String(limit) });
}

export function formatCurrency(amount: number, currency = 'USD') {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  }).format(amount);
}

export function formatNumber(num: number) {
  return new Intl.NumberFormat('en-US').format(num);
}

export function formatProductName(productId: string) {
  return productId
    .replace('prod_', '')
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}
