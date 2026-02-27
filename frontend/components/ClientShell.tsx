'use client';

import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/queryClient';
import Navigation from '@/components/Navigation';
import GlobalTicker from '@/components/GlobalTicker';
import PriceAlertModal from '@/components/PriceAlertModal';
import ToastProvider from '@/components/ToastProvider';
import { usePriceAlerts } from '@/hooks/usePriceAlerts';

export default function ClientShell({ children }: { children: React.ReactNode }) {
    // Initialize price alert monitoring globally
    usePriceAlerts();

    return (
        <QueryClientProvider client={queryClient}>
            <div className="h-screen flex flex-col overflow-hidden">
                {/* Header Navigation */}
                <Navigation />

                {/* Global Ticker Tape */}
                <GlobalTicker />

                {/* Page Content */}
                <main className="flex-1 overflow-hidden h-[calc(100vh-80px)]">
                    {children}
                </main>

                {/* Global Price Alert Modal */}
                <PriceAlertModal />
            </div>

            {/* Global Toast Notifications */}
            <ToastProvider />
        </QueryClientProvider>
    );
}
