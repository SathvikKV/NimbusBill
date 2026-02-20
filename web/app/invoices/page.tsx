'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ErrorState } from '@/components/error-state';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useInvoices, useCustomers } from '@/lib/use-api';
import { formatCurrency } from '@/lib/api';

const statusStyles: Record<string, string> = {
  issued: 'bg-[#3b82f6]/15 text-[#3b82f6] border-[#3b82f6]/20',
  paid: 'bg-[#22c55e]/15 text-[#22c55e] border-[#22c55e]/20',
  draft: 'bg-muted text-muted-foreground border-border',
};

export default function InvoicesPage() {
  const router = useRouter();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [customerFilter, setCustomerFilter] = useState<string>('all');

  const params = useMemo(() => {
    const p: { status?: string; customer_id?: string } = {};
    if (statusFilter !== 'all') p.status = statusFilter;
    if (customerFilter !== 'all') p.customer_id = customerFilter;
    return p;
  }, [statusFilter, customerFilter]);

  const { data: invoices, error, isLoading, mutate } = useInvoices(params);
  const { data: customers } = useCustomers();

  if (error && !invoices) {
    return <ErrorState message="Failed to load invoices" onRetry={() => mutate()} />;
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap gap-3">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40 bg-card border-border text-foreground">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent className="bg-popover border-border">
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="issued">Issued</SelectItem>
            <SelectItem value="paid">Paid</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
          </SelectContent>
        </Select>
        <Select value={customerFilter} onValueChange={setCustomerFilter}>
          <SelectTrigger className="w-48 bg-card border-border text-foreground">
            <SelectValue placeholder="Customer" />
          </SelectTrigger>
          <SelectContent className="bg-popover border-border">
            <SelectItem value="all">All Customers</SelectItem>
            {customers?.map((c) => (
              <SelectItem key={c.customer_id} value={c.customer_id}>
                {c.customer_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="rounded-xl border border-border bg-card backdrop-blur-sm">
        {isLoading ? (
          <div className="space-y-3 p-5">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="h-10 w-full bg-muted" />
            ))}
          </div>
        ) : !invoices || invoices.length === 0 ? (
          <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
            No invoices found
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="border-border hover:bg-transparent">
                <TableHead className="text-muted-foreground">Invoice ID</TableHead>
                <TableHead className="text-muted-foreground">Customer</TableHead>
                <TableHead className="text-muted-foreground">Period</TableHead>
                <TableHead className="text-right text-muted-foreground">Total</TableHead>
                <TableHead className="text-muted-foreground">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invoices.map((inv) => (
                <TableRow
                  key={inv.invoice_id}
                  className="border-border cursor-pointer transition-colors hover:bg-accent/50"
                  onClick={() => router.push(`/invoices/${inv.invoice_id}`)}
                >
                  <TableCell className="font-mono text-xs text-foreground">
                    {inv.invoice_id.slice(0, 8)}...
                  </TableCell>
                  <TableCell className="text-foreground">{inv.customer_name}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {new Date(inv.billing_period_start).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    {' - '}
                    {new Date(inv.billing_period_end).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </TableCell>
                  <TableCell className="text-right font-medium text-foreground">
                    {formatCurrency(inv.total, inv.currency)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={statusStyles[inv.status] || statusStyles.draft}
                    >
                      {inv.status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
