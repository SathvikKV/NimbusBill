'use client';

import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({ message = 'Failed to load data', onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16">
      <div className="flex size-12 items-center justify-center rounded-full bg-destructive/10">
        <AlertCircle className="size-6 text-destructive" />
      </div>
      <div className="text-center">
        <p className="text-sm font-medium text-foreground">{message}</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Please check your API connection and try again.
        </p>
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry} className="gap-2 border-border text-foreground hover:bg-accent">
          <RefreshCw className="size-3" />
          Retry
        </Button>
      )}
    </div>
  );
}
