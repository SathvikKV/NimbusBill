'use client';

import { useMemo } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Skeleton } from '@/components/ui/skeleton';
import { ErrorState } from '@/components/error-state';
import { useUsage } from '@/lib/use-api';
import { formatCurrency, type UsageRecord } from '@/lib/api';

export function RevenueChart() {
  const { data, error, isLoading, mutate } = useUsage();

  const chartData = useMemo(() => {
    if (!data) return [];
    const grouped: Record<string, number> = {};
    data.forEach((r: UsageRecord) => {
      grouped[r.date_id] = (grouped[r.date_id] || 0) + r.cost_amount;
    });
    return Object.entries(grouped)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, revenue]) => ({
        date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        revenue,
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
        <h3 className="mb-4 text-sm font-medium text-foreground">Revenue Over Time</h3>
        <ErrorState onRetry={() => mutate()} />
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card p-5 backdrop-blur-sm">
      <h3 className="mb-4 text-sm font-medium text-foreground">Revenue Over Time</h3>
      {chartData.length === 0 ? (
        <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
          No revenue data available yet
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" />
            <XAxis
              dataKey="date"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `$${v}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid rgba(148,163,184,0.12)',
                borderRadius: '8px',
                color: '#f1f5f9',
                fontSize: '12px',
              }}
              formatter={(value: number) => [formatCurrency(value), 'Revenue']}
            />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="#8b5cf6"
              strokeWidth={2}
              fill="url(#revenueGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
