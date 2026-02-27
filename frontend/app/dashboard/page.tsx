'use client';

import NewsFeed from '@/components/NewsFeed';
import ChartPanel from '@/components/ChartPanel';
import OraclePanel from '@/components/OraclePanel';

export default function DashboardPage() {
    return (
        <div className="flex-1 grid grid-cols-[22%_50%_28%] gap-0 overflow-hidden h-full">
            {/* Left Panel - The Feed (22%) */}
            <aside className="border-r border-oracle-border overflow-hidden flex flex-col bg-oracle-dark/50">
                <NewsFeed />
            </aside>

            {/* Middle Panel - The Chart (50%) */}
            <section className="overflow-hidden flex flex-col bg-oracle-darker">
                <ChartPanel />
            </section>

            {/* Right Panel - The Oracle (28%) */}
            <aside className="border-l border-oracle-border overflow-hidden flex flex-col bg-oracle-dark/50">
                <OraclePanel />
            </aside>
        </div>
    );
}
