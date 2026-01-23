'use client';

import NewsFeed from '@/components/NewsFeed';
import ChartPanel from '@/components/ChartPanel';
import OraclePanel from '@/components/OraclePanel';
import { Activity, Zap } from 'lucide-react';

export default function Dashboard() {
    return (
        <div className="min-h-screen flex flex-col">
            {/* Header */}
            <header className="h-16 border-b border-oracle-border bg-oracle-dark/80 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-50">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-oracle-accent to-purple-600 flex items-center justify-center glow-accent">
                        <Zap className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                            Oracle-X
                        </h1>
                        <p className="text-xs text-gray-500">Financial Intelligence Terminal</p>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-oracle-card border border-oracle-border">
                        <span className="w-2 h-2 rounded-full bg-oracle-bullish live-indicator"></span>
                        <span className="text-sm text-gray-400">Live</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                        <Activity className="w-4 h-4" />
                        <span>Sepolia Testnet</span>
                    </div>
                </div>
            </header>

            {/* Main 3-Column Grid */}
            <main className="flex-1 grid grid-cols-[20%_50%_30%] gap-0 overflow-hidden">
                {/* Left Panel - The Feed (20%) */}
                <aside className="border-r border-oracle-border overflow-hidden flex flex-col bg-oracle-dark/50">
                    <NewsFeed />
                </aside>

                {/* Middle Panel - The Chart (50%) */}
                <section className="overflow-hidden flex flex-col bg-oracle-darker">
                    <ChartPanel />
                </section>

                {/* Right Panel - The Oracle (30%) */}
                <aside className="border-l border-oracle-border overflow-hidden flex flex-col bg-oracle-dark/50">
                    <OraclePanel />
                </aside>
            </main>
        </div>
    );
}
