'use client';

import { useDashboardSummary } from '@/lib/use-api';
import { ErrorState } from '@/components/error-state';
import { KpiCards } from '@/components/dashboard/kpi-cards';
import { RevenueChart } from '@/components/dashboard/revenue-chart';
import { UsageByProductChart } from '@/components/dashboard/usage-by-product-chart';
import { RecentInvoices } from '@/components/dashboard/recent-invoices';

export default function DashboardPage() {
  const { data, error, isLoading, mutate } = useDashboardSummary();

  if (error && !data) {
    return <ErrorState message="Failed to load dashboard data" onRetry={() => mutate()} />;
  }

  return (
    <div className="flex flex-col gap-6">
      <KpiCards data={data} isLoading={isLoading} />
      <div className="grid gap-6 lg:grid-cols-2">
        <RevenueChart />
        <UsageByProductChart />
      </div>
      <RecentInvoices />
    </div>
  );
}
