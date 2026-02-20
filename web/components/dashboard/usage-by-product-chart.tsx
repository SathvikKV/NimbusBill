'use client';

import { useMemo } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Skeleton } from '@/components/ui/skeleton';
import { ErrorState } from '@/components/error-state';
import { useUsage } from '@/lib/use-api';
import { formatNumber, formatProductName, type UsageRecord } from '@/lib/api';

const COLORS = ['#8b5cf6', '#3b82f6', '#22c55e', '#f59e0b', '#ef4444'];

export function UsageByProductChart() {
  const { data, error, isLoading, mutate } = useUsage();

  const chartData = useMemo(() => {
    if (!data) return [];
    const grouped: Record<string, number> = {};
    data.forEach((r: UsageRecord) => {
      grouped[r.product_id] = (grouped[r.product_id] || 0) + r.total_quantity;
    });
    return Object.entries(grouped).map(([product, quantity], i) => ({
      product: formatProductName(product),
      quantity,
      fill: COLORS[i % COLORS.length],
    }));
  }, [data]);

  if (isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-5 backdrop-blur-sm">
        <Skeleton className="mb-4 h-5 w-40 bg-muted" />
        <Skeleton className="h-64 w-full bg-muted" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-border bg-card p-5 backdrop-blur-sm">
        <h3 className="mb-4 text-sm font-medium text-foreground">Usage by Product</h3>
        <ErrorState onRetry={() => mutate()} />
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card p-5 backdrop-blur-sm">
      <h3 className="mb-4 text-sm font-medium text-foreground">Usage by Product</h3>
      {chartData.length === 0 ? (
        <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
          No usage data available yet
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => formatNumber(v)}
            />
            <YAxis
              type="category"
              dataKey="product"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={120}
            />
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
  );
}
