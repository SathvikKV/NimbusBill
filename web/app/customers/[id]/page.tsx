'use client';

import { use, useMemo } from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
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
import { useCustomers, useCustomerUsage } from '@/lib/use-api';
import { formatCurrency, formatNumber, formatProductName, type UsageRecord } from '@/lib/api';

const statusStyles: Record<string, string> = {
  active: 'bg-[#22c55e]/15 text-[#22c55e] border-[#22c55e]/20',
  churned: 'bg-destructive/15 text-destructive border-destructive/20',
  trial: 'bg-[#f59e0b]/15 text-[#f59e0b] border-[#f59e0b]/20',
};

const planStyles: Record<string, string> = {
  plan_free: 'bg-muted text-muted-foreground border-border',
  plan_starter: 'bg-[#3b82f6]/15 text-[#3b82f6] border-[#3b82f6]/20',
  plan_pro: 'bg-[#8b5cf6]/15 text-[#8b5cf6] border-[#8b5cf6]/20',
  plan_enterprise: 'bg-[#f59e0b]/15 text-[#f59e0b] border-[#f59e0b]/20',
};

function formatPlanName(planId: string) {
  return planId.replace('plan_', '').charAt(0).toUpperCase() + planId.replace('plan_', '').slice(1);
}

export default function CustomerDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: customers, isLoading: loadingCustomers } = useCustomers();
  const { data: usage, error: usageError, isLoading: loadingUsage, mutate } = useCustomerUsage(id);

  const customer = useMemo(() => customers?.find((c) => c.customer_id === id), [customers, id]);

  const chartData = useMemo(() => {
    if (!usage) return [];
    const grouped: Record<string, number> = {};
    usage.forEach((r: UsageRecord) => {
      grouped[r.date_id] = (grouped[r.date_id] || 0) + r.cost_amount;
    });
    return Object.entries(grouped)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, cost]) => ({
        date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        cost,
      }));
  }, [usage]);

  const productBreakdown = useMemo(() => {
    if (!usage) return [];
    const grouped: Record<string, { quantity: number; cost: number }> = {};
    usage.forEach((r: UsageRecord) => {
      if (!grouped[r.product_id]) grouped[r.product_id] = { quantity: 0, cost: 0 };
      grouped[r.product_id].quantity += r.total_quantity;
      grouped[r.product_id].cost += r.cost_amount;
    });
    return Object.entries(grouped).map(([product, vals]) => ({
      product,
      ...vals,
    }));
  }, [usage]);

  if (loadingCustomers) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-8 w-48 bg-muted" />
        <Skeleton className="h-40 rounded-xl bg-muted" />
        <Skeleton className="h-64 rounded-xl bg-muted" />
      </div>
    );
  }

  if (!customer) {
    return (
      <div className="flex flex-col items-center gap-4 py-16">
        <p className="text-sm text-muted-foreground">Customer not found</p>
        <Button asChild variant="outline" className="border-border text-foreground hover:bg-accent">
          <Link href="/customers">Back to Customers</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <Button asChild variant="ghost" className="w-fit gap-2 text-muted-foreground hover:text-foreground">
        <Link href="/customers">
          <ArrowLeft className="size-4" />
          Back to Customers
        </Link>
      </Button>

      <div className="rounded-xl border border-border bg-card p-6 backdrop-blur-sm">
        <div className="flex flex-wrap items-start gap-3">
          <h2 className="text-xl font-bold text-foreground">{customer.customer_name}</h2>
          <Badge variant="outline" className={statusStyles[customer.status] || statusStyles.active}>
            {customer.status}
          </Badge>
          <Badge variant="outline" className={planStyles[customer.plan_id] || planStyles.plan_free}>
            {formatPlanName(customer.plan_id)}
          </Badge>
        </div>
        <p className="mt-2 text-sm text-muted-foreground">
          Country: {customer.country} | Customer ID: {customer.customer_id}
        </p>
      </div>

      {usageError ? (
        <ErrorState message="Failed to load usage data" onRetry={() => mutate()} />
      ) : loadingUsage ? (
        <Skeleton className="h-72 rounded-xl bg-muted" />
      ) : (
        <>
          <div className="rounded-xl border border-border bg-card p-5 backdrop-blur-sm">
            <h3 className="mb-4 text-sm font-medium text-foreground">Daily Usage Trend</h3>
            {chartData.length === 0 ? (
              <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
                No usage data available
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="custGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" />
                  <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${v}`} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid rgba(148,163,184,0.12)',
                      borderRadius: '8px',
                      color: '#f1f5f9',
                      fontSize: '12px',
                    }}
                    formatter={(value: number) => [formatCurrency(value), 'Cost']}
                  />
                  <Area type="monotone" dataKey="cost" stroke="#8b5cf6" strokeWidth={2} fill="url(#custGradient)" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="rounded-xl border border-border bg-card p-5 backdrop-blur-sm">
            <h3 className="mb-4 text-sm font-medium text-foreground">Usage Breakdown by Product</h3>
            {productBreakdown.length === 0 ? (
              <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
                No product usage data available
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-border hover:bg-transparent">
                    <TableHead className="text-muted-foreground">Product</TableHead>
                    <TableHead className="text-right text-muted-foreground">Quantity</TableHead>
                    <TableHead className="text-right text-muted-foreground">Cost</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {productBreakdown.map((row) => (
                    <TableRow key={row.product} className="border-border">
                      <TableCell className="font-medium text-foreground">{formatProductName(row.product)}</TableCell>
                      <TableCell className="text-right text-foreground">{formatNumber(row.quantity)}</TableCell>
                      <TableCell className="text-right text-foreground">{formatCurrency(row.cost)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </>
      )}
    </div>
  );
}
