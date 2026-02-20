'use client';

import { RefreshCw, CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ErrorState } from '@/components/error-state';
import { usePipelineStatus } from '@/lib/use-api';

const statusConfig: Record<string, { icon: typeof CheckCircle2; color: string; badge: string }> = {
  SUCCESS: {
    icon: CheckCircle2,
    color: 'text-[#22c55e]',
    badge: 'bg-[#22c55e]/15 text-[#22c55e] border-[#22c55e]/20',
  },
  FAILED: {
    icon: XCircle,
    color: 'text-destructive',
    badge: 'bg-destructive/15 text-destructive border-destructive/20',
  },
  RUNNING: {
    icon: Loader2,
    color: 'text-[#3b82f6]',
    badge: 'bg-[#3b82f6]/15 text-[#3b82f6] border-[#3b82f6]/20',
  },
};

const defaultStatus = {
  icon: Clock,
  color: 'text-muted-foreground',
  badge: 'bg-muted text-muted-foreground border-border',
};

export default function PipelinePage() {
  const { data, error, isLoading, mutate } = usePipelineStatus();

  if (error && !data) {
    return <ErrorState message="Failed to load pipeline status" onRetry={() => mutate()} />;
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Recent pipeline runs
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => mutate()}
          className="gap-2 border-border text-foreground hover:bg-accent"
        >
          <RefreshCw className="size-3" />
          Refresh
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-xl bg-muted" />
          ))}
        </div>
      ) : !data || data.length === 0 ? (
        <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
          No pipeline runs found
        </div>
      ) : (
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-[19px] top-6 bottom-6 w-px bg-border" />

          <div className="flex flex-col gap-4">
            {data.map((run, idx) => {
              const cfg = statusConfig[run.status] || defaultStatus;
              const Icon = cfg.icon;
              return (
                <div key={`${run.run_id}-${idx}`} className="relative flex gap-4 pl-0">
                  <div className="relative z-10 flex size-10 shrink-0 items-center justify-center rounded-full border border-border bg-card">
                    <Icon className={`size-5 ${cfg.color} ${run.status === 'RUNNING' ? 'animate-spin' : ''}`} />
                  </div>
                  <div className="flex-1 rounded-xl border border-border bg-card p-4 backdrop-blur-sm transition-all hover:border-border/80">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-medium text-foreground">{run.dag_id.replace(/_/g, ' ')}</p>
                        <p className="mt-1 font-mono text-xs text-muted-foreground">{run.run_id}</p>
                      </div>
                      <Badge variant="outline" className={cfg.badge}>
                        {run.status}
                      </Badge>
                    </div>
                    <p className="mt-2 text-xs text-muted-foreground">
                      {new Date(run.created_ts).toLocaleDateString('en-US', {
                        weekday: 'short',
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
