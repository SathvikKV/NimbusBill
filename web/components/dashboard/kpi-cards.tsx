'use client';

import { DollarSign, Users, FileText, Activity } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { AnimatedCounter } from '@/components/animated-counter';
import { formatCurrency, formatNumber, type DashboardSummary } from '@/lib/api';

interface KpiCardsProps {
  data?: DashboardSummary;
  isLoading: boolean;
}

const kpiConfig = [
  {
    key: 'total_revenue_mtd' as const,
    label: 'Total Revenue (MTD)',
    icon: DollarSign,
    color: 'from-[#8b5cf6] to-[#3b82f6]',
    iconBg: 'bg-[#8b5cf6]/15',
    iconColor: 'text-[#8b5cf6]',
    formatter: (v: number) => formatCurrency(v),
  },
  {
    key: 'total_customers' as const,
    label: 'Active Customers',
    icon: Users,
    color: 'from-[#3b82f6] to-[#06b6d4]',
    iconBg: 'bg-[#3b82f6]/15',
    iconColor: 'text-[#3b82f6]',
    formatter: (v: number) => formatNumber(Math.round(v)),
  },
  {
    key: 'active_invoices' as const,
    label: 'Pending Invoices',
    icon: FileText,
    color: 'from-[#f59e0b] to-[#f97316]',
    iconBg: 'bg-[#f59e0b]/15',
    iconColor: 'text-[#f59e0b]',
    formatter: (v: number) => formatNumber(Math.round(v)),
  },
  {
    key: 'total_events_today' as const,
    label: 'Events Today',
    icon: Activity,
    color: 'from-[#22c55e] to-[#10b981]',
    iconBg: 'bg-[#22c55e]/15',
    iconColor: 'text-[#22c55e]',
    formatter: (v: number) => formatNumber(Math.round(v)),
  },
];

export function KpiCards({ data, isLoading }: KpiCardsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {kpiConfig.map((kpi) => (
        <div
          key={kpi.key}
          className="group relative overflow-hidden rounded-xl border border-border bg-card p-5 backdrop-blur-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-border/80 hover:shadow-lg hover:shadow-[#8b5cf6]/5"
        >
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r opacity-0 transition-opacity group-hover:opacity-100" style={{backgroundImage: `linear-gradient(to right, transparent, var(--primary), transparent)`}} />
          <div className="flex items-start justify-between">
            <div className="flex flex-col gap-1">
              {isLoading ? (
                <>
                  <Skeleton className="h-8 w-24 bg-muted" />
                  <Skeleton className="mt-1 h-4 w-32 bg-muted" />
                </>
              ) : (
                <>
                  <span className="text-2xl font-bold tracking-tight text-foreground">
                    <AnimatedCounter
                      value={data?.[kpi.key] ?? 0}
                      formatter={kpi.formatter}
                    />
                  </span>
                  <span className="text-xs font-medium text-muted-foreground">
                    {kpi.label}
                  </span>
                </>
              )}
            </div>
            <div className={`flex size-10 shrink-0 items-center justify-center rounded-lg ${kpi.iconBg}`}>
              <kpi.icon className={`size-5 ${kpi.iconColor}`} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
