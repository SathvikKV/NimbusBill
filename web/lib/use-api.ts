'use client';

import useSWR from 'swr';
import {
  fetchDashboardSummary,
  fetchCustomers,
  fetchCustomerUsage,
  fetchInvoices,
  fetchInvoiceDetail,
  fetchUsage,
  fetchPricing,
  fetchPipelineStatus,
} from './api';

export function useDashboardSummary() {
  return useSWR('dashboard-summary', fetchDashboardSummary);
}

export function useCustomers() {
  return useSWR('customers', fetchCustomers);
}

export function useCustomerUsage(customerId: string) {
  return useSWR(customerId ? `customer-usage-${customerId}` : null, () =>
    fetchCustomerUsage(customerId)
  );
}

export function useInvoices(params?: { customer_id?: string; status?: string }) {
  const key = `invoices-${params?.customer_id || ''}-${params?.status || ''}`;
  return useSWR(key, () => fetchInvoices(params));
}

export function useInvoiceDetail(invoiceId: string) {
  return useSWR(invoiceId ? `invoice-${invoiceId}` : null, () =>
    fetchInvoiceDetail(invoiceId)
  );
}

export function useUsage(params?: { date_from?: string; date_to?: string; product_id?: string; customer_id?: string }) {
  const key = `usage-${params?.date_from || ''}-${params?.date_to || ''}-${params?.product_id || ''}-${params?.customer_id || ''}`;
  return useSWR(key, () => fetchUsage(params));
}

export function usePricing() {
  return useSWR('pricing', fetchPricing);
}

export function usePipelineStatus(limit = 20) {
  return useSWR(`pipeline-${limit}`, () => fetchPipelineStatus(limit));
}
