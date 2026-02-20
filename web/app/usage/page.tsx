'use client';

import { useState, useMemo } from 'react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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
import { useUsage, useCustomers } from '@/lib/use-api';
import {
  formatCurrency,
  formatNumber,
  formatProductName,
  type UsageRecord,
} from '@/lib/api';

const COLORS = ['#8b5cf6', '#3b82f6', '#22c55e', '#f59e0b', '#ef4444'];

export default function UsageExplorerPage() {
  const [productFilter, setProductFilter] = useState<string>('all');
  const [customerFilter, setCustomerFilter] = useState<string>('all');
  const { data: usage, error, isLoading, mutate } = useUsage();
  const { data: customers } = useCustomers();

  const products = useMemo(() => {
    if (!usage) return [];
    return [...new Set(usage.map((r) => r.product_id))];
  }, [usage]);

  const filtered = useMemo(() => {
    if (!usage) return [];
    return usage.filter((r) => {
      if (productFilter !== 'all' && r.product_id !== productFilter) return false;
      return true;
    });
  }, [usage, productFilter]);

  const dailyTrend = useMemo(() => {
    const grouped: Record<string, number> = {};
    filtered.forEach((r) => {
      grouped[r.date_id] = (grouped[r.date_id] || 0) + r.total_quantity;
    });
    return Object.entries(grouped)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, quantity]) => ({
        date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        quantity,
      }));
  }, [filtered]);

  const productSummary = useMemo(() => {
    const grouped: Record<string, { quantity: number; cost: number; unit: string }> = {};
    filtered.forEach((r) => {
      if (!grouped[r.product_id]) grouped[r.product_id] = { quantity: 0, cost: 0, unit: r.unit };
      grouped[r.product_id].quantity += r.total_quantity;
      grouped[r.product_id].cost += r.cost_amount;
    });
    return Object.entries(grouped).map(([product, vals], i) => ({
      product,
      name: formatProductName(product),
      fill: COLORS[i % COLORS.length],
      ...vals,
    }));
  }, [filtered]);

  const costTrend = useMemo(() => {
    const grouped: Record<string, number> = {};
    filtered.forEach((r) => {
      grouped[r.date_id] = (grouped[r.date_id] || 0) + r.cost_amount;
    });
    return Object.entries(grouped)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, cost]) => ({
        date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        cost,
      }));
  }, [filtered]);

  if (error && !usage) {
    return <ErrorState message="Failed to load usage data" onRetry={() => mutate()} />;
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Select value={productFilter} onValueChange={setProductFilter}>
          <SelectTrigger className="w-48 bg-card border-border text-foreground">
            <SelectValue placeholder="All Products" />
          </SelectTrigger>
          <SelectContent className="bg-popover border-border text-popover-foreground">
            <SelectItem value="all">All Products</SelectItem>
            {products.map((p) => (
              <SelectItem key={p} value={p}>
                {formatProductName(p)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="flex flex-col gap-6">
          <Skeleton className="h-72 rounded-xl bg-muted" />
          <div className="grid gap-6 lg:grid-cols-2">
            <Skeleton className="h-72 rounded-xl bg-muted" />
            <Skeleton className="h-72 rounded-xl bg-muted" />
          </div>
        </div>
      ) : (
        <>
          {/* Usage volume trend */}
          <div className="rounded-xl border border-border bg-card p-5 backdrop-blur-sm">
            <h3 className="mb-4 text-sm font-medium text-foreground">Daily Usage Volume</h3>
            {dailyTrend.length === 0 ? (
              <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
                No usage data available
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={dailyTrend}>
                  <defs>
                    <linearGradient id="usageGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" />
                  <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => formatNumber(v)} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid rgba(148,163,184,0.12)',
                      borderRadius: '8px',
                      color: '#f1f5f9',
                      fontSize: '12px',
                    }}
                    formatter={(value: number) => [formatNumber(value), 'Quantity']}
                  />
                  <Area type="monotone" dataKey="quantity" stroke="#3b82f6" strokeWidth={2} fill="url(#usageGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            {/* Cost trend */}
            <div className="rounded-xl border border-border bg-card p-5 backdrop-blur-sm">
              <h3 className="mb-4 text-sm font-medium text-foreground">Daily Cost Trend</h3>
              {costTrend.length === 0 ? (
                <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
                  No cost data available
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <AreaChart data={costTrend}>
                    <defs>
                      <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
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
                    <Area type="monotone" dataKey="cost" stroke="#8b5cf6" strokeWidth={2} fill="url(#costGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Product breakdown bar */}
            <div className="rounded-xl border border-border bg-card p-5 backdrop-blur-sm">
              <h3 className="mb-4 text-sm font-medium text-foreground">Usage by Product</h3>
              {productSummary.length === 0 ? (
                <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
                  No product data
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={productSummary} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" horizontal={false} />
                    <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => formatNumber(v)} />
                    <YAxis type="category" dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} width={120} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e293b',
                        border: '1px solid rgba(148,163,184,0.12)',
                        borderRadius: '8px',
                        color: '#f1f5f9',
                        fontSize: '12px',
                      }}
                      formatter={(value: number) => [formatNumber(value), 'Quantity']}
                    />
                    <Bar dataKey="quantity" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Detail table */}
          <div className="rounded-xl border border-border bg-card p-5 backdrop-blur-sm">
            <h3 className="mb-4 text-sm font-medium text-foreground">Product Cost Summary</h3>
            {productSummary.length === 0 ? (
              <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
                No data available
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-border hover:bg-transparent">
                    <TableHead className="text-muted-foreground">Product</TableHead>
                    <TableHead className="text-muted-foreground">Unit</TableHead>
                    <TableHead className="text-right text-muted-foreground">Total Quantity</TableHead>
                    <TableHead className="text-right text-muted-foreground">Total Cost</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {productSummary.map((row) => (
                    <TableRow key={row.product} className="border-border">
                      <TableCell className="font-medium text-foreground">{row.name}</TableCell>
                      <TableCell className="text-muted-foreground">{row.unit}</TableCell>
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
