import type { Metadata, Viewport } from 'next'
import { Inter, Geist_Mono } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/app-sidebar'
import { PageHeader } from '@/components/page-header'
import './globals.css'

const _inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const _geistMono = Geist_Mono({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'NimbusBill - Usage-Based Billing Dashboard',
  description: 'Premium billing dashboard for usage-based billing. Manage customers, invoices, usage, and pricing.',
}

export const viewport: Viewport = {
  themeColor: '#0f172a',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <SidebarProvider>
          <AppSidebar />
          <SidebarInset>
            <PageHeader />
            <main className="flex-1 overflow-auto p-4 md:p-6">
              {children}
            </main>
          </SidebarInset>
        </SidebarProvider>
        <Analytics />
      </body>
    </html>
  )
}
