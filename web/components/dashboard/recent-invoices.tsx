'use client';

import { useRouter } from 'next/navigation';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ErrorState } from '@/components/error-state';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useInvoices } from '@/lib/use-api';
import { formatCurrency } from '@/lib/api';

const statusStyles: Record<string, string> = {
  issued: 'bg-[#3b82f6]/15 text-[#3b82f6] border-[#3b82f6]/20',
  paid: 'bg-[#22c55e]/15 text-[#22c55e] border-[#22c55e]/20',
  draft: 'bg-muted text-muted-foreground border-border',
};

export function RecentInvoices() {
  const router = useRouter();
  const { data, error, isLoading, mutate } = useInvoices();

  if (isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-5 backdrop-blur-sm">
        <Skeleton className="mb-4 h-5 w-40 bg-muted" />
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-10 w-full bg-muted" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-border bg-card p-5 backdrop-blur-sm">
        <h3 className="mb-4 text-sm font-medium text-foreground">Recent Invoices</h3>
        <ErrorState onRetry={() => mutate()} />
      </div>
    );
  }

  const invoices = (data || []).slice(0, 5);

  return (
    <div className="rounded-xl border border-border bg-card p-5 backdrop-blur-sm">
      <h3 className="mb-4 text-sm font-medium text-foreground">Recent Invoices</h3>
      {invoices.length === 0 ? (
        <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
          No invoices found
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead className="text-muted-foreground">Invoice ID</TableHead>
              <TableHead className="text-muted-foreground">Customer</TableHead>
              <TableHead className="text-muted-foreground">Amount</TableHead>
              <TableHead className="text-muted-foreground">Status</TableHead>
              <TableHead className="text-muted-foreground">Date</TableHead>
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
                <TableCell className="text-foreground">{formatCurrency(inv.total, inv.currency)}</TableCell>
                <TableCell>
                  <Badge
                    variant="outline"
                    className={statusStyles[inv.status] || statusStyles.draft}
                  >
                    {inv.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {new Date(inv.issued_ts).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
