'use client';

import { use } from 'react';
import Link from 'next/link';
import { ArrowLeft, Download } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { ErrorState } from '@/components/error-state';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useInvoiceDetail } from '@/lib/use-api';
import { formatCurrency, formatNumber, formatProductName } from '@/lib/api';

const statusStyles: Record<string, string> = {
  issued: 'bg-[#3b82f6]/15 text-[#3b82f6] border-[#3b82f6]/20',
  paid: 'bg-[#22c55e]/15 text-[#22c55e] border-[#22c55e]/20',
  draft: 'bg-muted text-muted-foreground border-border',
};

export default function InvoiceDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: invoice, error, isLoading, mutate } = useInvoiceDetail(id);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-8 w-48 bg-muted" />
        <Skeleton className="h-40 rounded-xl bg-muted" />
        <Skeleton className="h-64 rounded-xl bg-muted" />
      </div>
    );
  }

  if (error || !invoice) {
    return <ErrorState message="Failed to load invoice details" onRetry={() => mutate()} />;
  }

  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <Button asChild variant="ghost" className="w-fit gap-2 text-muted-foreground hover:text-foreground">
          <Link href="/invoices">
            <ArrowLeft className="size-4" />
            Back to Invoices
          </Link>
        </Button>
        <Button
          asChild
          variant="outline"
          className="gap-2 border-border text-foreground hover:bg-accent"
        >
          <a
            href={`${apiBase}/invoices/${id}/pdf`}
            target="_blank"
            rel="noopener noreferrer"
          >
            <Download className="size-4" />
            Download PDF
          </a>
        </Button>
      </div>

      <div className="rounded-xl border border-border bg-card p-6 backdrop-blur-sm">
        <div className="flex flex-wrap items-start gap-3">
          <h2 className="text-xl font-bold text-foreground">Invoice {invoice.invoice_id.slice(0, 8)}...</h2>
          <Badge
            variant="outline"
            className={statusStyles[invoice.status] || statusStyles.draft}
          >
            {invoice.status}
          </Badge>
        </div>
        <div className="mt-4 grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-muted-foreground">Customer</p>
            <p className="font-medium text-foreground">{invoice.customer_name}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Billing Period</p>
            <p className="font-medium text-foreground">
              {new Date(invoice.billing_period_start).toLocaleDateString()} - {new Date(invoice.billing_period_end).toLocaleDateString()}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Issued</p>
            <p className="font-medium text-foreground">
              {new Date(invoice.issued_ts).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Currency</p>
            <p className="font-medium text-foreground">{invoice.currency}</p>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card p-5 backdrop-blur-sm">
        <h3 className="mb-4 text-sm font-medium text-foreground">Line Items</h3>
        {!invoice.line_items || invoice.line_items.length === 0 ? (
          <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
            No line items
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="border-border hover:bg-transparent">
                <TableHead className="text-muted-foreground">Product</TableHead>
                <TableHead className="text-muted-foreground">Type</TableHead>
                <TableHead className="text-right text-muted-foreground">Quantity</TableHead>
                <TableHead className="text-right text-muted-foreground">Unit Price</TableHead>
                <TableHead className="text-right text-muted-foreground">Amount</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invoice.line_items.map((item) => (
                <TableRow key={item.line_item_id} className="border-border">
                  <TableCell className="font-medium text-foreground">
                    {formatProductName(item.product_id)}
                  </TableCell>
                  <TableCell className="text-muted-foreground capitalize">{item.line_type}</TableCell>
                  <TableCell className="text-right text-foreground">
                    {formatNumber(item.quantity)} {item.unit}
                  </TableCell>
                  <TableCell className="text-right text-foreground">
                    {formatCurrency(item.unit_price)}
                  </TableCell>
                  <TableCell className="text-right font-medium text-foreground">
                    {formatCurrency(item.amount)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}

        <Separator className="my-4 bg-border" />
        <div className="flex flex-col items-end gap-1 text-sm">
          <div className="flex gap-8">
            <span className="text-muted-foreground">Subtotal</span>
            <span className="text-foreground">{formatCurrency(invoice.subtotal, invoice.currency)}</span>
          </div>
          <div className="flex gap-8">
            <span className="text-muted-foreground">Tax</span>
            <span className="text-foreground">{formatCurrency(invoice.tax, invoice.currency)}</span>
          </div>
          <div className="mt-2 flex gap-8 border-t border-border pt-2">
            <span className="text-base font-bold text-foreground">Total</span>
            <span className="text-base font-bold text-foreground">
              {formatCurrency(invoice.total, invoice.currency)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
