'use client';

import { useMemo } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { ErrorState } from '@/components/error-state';
import { usePricing } from '@/lib/use-api';
import { formatCurrency, formatProductName, type PricingRecord } from '@/lib/api';

const planColors: Record<string, { border: string; badge: string; glow: string }> = {
  plan_free: {
    border: 'border-border',
    badge: 'bg-muted text-muted-foreground',
    glow: '',
  },
  plan_starter: {
    border: 'border-[#3b82f6]/30',
    badge: 'bg-[#3b82f6]/15 text-[#3b82f6]',
    glow: 'hover:shadow-[#3b82f6]/5',
  },
  plan_pro: {
    border: 'border-[#8b5cf6]/30',
    badge: 'bg-[#8b5cf6]/15 text-[#8b5cf6]',
    glow: 'hover:shadow-[#8b5cf6]/5',
  },
  plan_enterprise: {
    border: 'border-[#f59e0b]/30',
    badge: 'bg-[#f59e0b]/15 text-[#f59e0b]',
    glow: 'hover:shadow-[#f59e0b]/5',
  },
};

function formatPlanLabel(planId: string) {
  return planId.replace('plan_', '').charAt(0).toUpperCase() + planId.replace('plan_', '').slice(1);
}

export default function PricingPage() {
  const { data, error, isLoading, mutate } = usePricing();

  const grouped = useMemo(() => {
    if (!data) return {};
    const groups: Record<string, PricingRecord[]> = {};
    data.forEach((r) => {
      if (!groups[r.plan_id]) groups[r.plan_id] = [];
      groups[r.plan_id].push(r);
    });
    return groups;
  }, [data]);

  const plans = Object.keys(grouped);

  if (error && !data) {
    return <ErrorState message="Failed to load pricing data" onRetry={() => mutate()} />;
  }

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-10 w-96 bg-muted" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-36 rounded-xl bg-muted" />
          ))}
        </div>
      </div>
    );
  }

  if (plans.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        No pricing data available
      </div>
    );
  }

  return (
    <Tabs defaultValue={plans[0]} className="flex flex-col gap-6">
      <TabsList className="w-fit bg-secondary border border-border">
        {plans.map((plan) => (
          <TabsTrigger key={plan} value={plan} className="text-muted-foreground data-[state=active]:text-foreground data-[state=active]:bg-accent">
            {formatPlanLabel(plan)}
          </TabsTrigger>
        ))}
      </TabsList>

      {plans.map((plan) => {
        const colors = planColors[plan] || planColors.plan_free;
        return (
          <TabsContent key={plan} value={plan}>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {grouped[plan].map((item, idx) => (
                <div
                  key={`${item.product_id}-${item.plan_id}-${idx}`}
                  className={`group rounded-xl border ${colors.border} bg-card p-5 backdrop-blur-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg ${colors.glow}`}
                >
                  <div className="flex items-start justify-between">
                    <h3 className="font-semibold text-foreground">{formatProductName(item.product_id)}</h3>
                    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${colors.badge}`}>
                      {formatPlanLabel(item.plan_id)}
                    </span>
                  </div>
                  <div className="mt-4">
                    <span className="text-2xl font-bold text-foreground">
                      {formatCurrency(item.unit_price)}
                    </span>
                    <span className="text-sm text-muted-foreground"> / {item.unit}</span>
                  </div>
                  <div className="mt-3 text-xs text-muted-foreground">
                    <p>
                      Effective from{' '}
                      {new Date(item.effective_from).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </p>
                    {item.effective_to && (
                      <p>
                        Until{' '}
                        {new Date(item.effective_to).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>
        );
      })}
    </Tabs>
  );
}
