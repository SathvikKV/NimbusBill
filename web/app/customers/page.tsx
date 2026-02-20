'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ErrorState } from '@/components/error-state';
import { useCustomers } from '@/lib/use-api';

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

const countryFlags: Record<string, string> = {
  US: '\u{1F1FA}\u{1F1F8}',
  GB: '\u{1F1EC}\u{1F1E7}',
  DE: '\u{1F1E9}\u{1F1EA}',
  FR: '\u{1F1EB}\u{1F1F7}',
  JP: '\u{1F1EF}\u{1F1F5}',
  CA: '\u{1F1E8}\u{1F1E6}',
  AU: '\u{1F1E6}\u{1F1FA}',
  BR: '\u{1F1E7}\u{1F1F7}',
  IN: '\u{1F1EE}\u{1F1F3}',
};

function formatPlanName(planId: string) {
  return planId.replace('plan_', '').charAt(0).toUpperCase() + planId.replace('plan_', '').slice(1);
}

export default function CustomersPage() {
  const { data, error, isLoading, mutate } = useCustomers();
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    if (!data) return [];
    if (!search) return data;
    return data.filter((c) =>
      c.customer_name.toLowerCase().includes(search.toLowerCase())
    );
  }, [data, search]);

  if (error && !data) {
    return <ErrorState message="Failed to load customers" onRetry={() => mutate()} />;
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search customers..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9 bg-card border-border text-foreground placeholder:text-muted-foreground"
        />
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-36 rounded-xl bg-muted" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
          {search ? 'No customers match your search' : 'No customers found'}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((customer) => (
            <Link
              key={customer.customer_sk}
              href={`/customers/${customer.customer_id}`}
              className="group rounded-xl border border-border bg-card p-5 backdrop-blur-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-border/80 hover:shadow-lg hover:shadow-[#8b5cf6]/5"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-foreground">{customer.customer_name}</h3>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {countryFlags[customer.country] || ''} {customer.country}
                  </p>
                </div>
                <Badge
                  variant="outline"
                  className={statusStyles[customer.status] || statusStyles.active}
                >
                  {customer.status}
                </Badge>
              </div>
              <div className="mt-4">
                <Badge
                  variant="outline"
                  className={planStyles[customer.plan_id] || planStyles.plan_free}
                >
                  {formatPlanName(customer.plan_id)}
                </Badge>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
