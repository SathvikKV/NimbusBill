'use client';

import { usePathname } from 'next/navigation';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { Separator } from '@/components/ui/separator';

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/customers': 'Customers',
  '/invoices': 'Invoices',
  '/usage': 'Usage Explorer',
  '/pricing': 'Pricing',
  '/pipeline': 'Pipeline Status',
};

export function PageHeader() {
  const pathname = usePathname();
  const title =
    pageTitles[pathname] ||
    Object.entries(pageTitles).find(([key]) => pathname.startsWith(key) && key !== '/')?.[1] ||
    'NimbusBill';

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border px-4">
      <SidebarTrigger className="-ml-1 text-muted-foreground hover:text-foreground" />
      <Separator orientation="vertical" className="mr-1 h-4 bg-border" />
      <h1 className="text-sm font-medium text-foreground">{title}</h1>
    </header>
  );
}
