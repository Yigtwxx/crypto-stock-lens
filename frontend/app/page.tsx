'use client';

import { useState } from 'react';
import NewsFeed from '@/components/NewsFeed';
import ChartPanel from '@/components/ChartPanel';
import OraclePanel from '@/components/OraclePanel';
import OverviewPage from '@/components/OverviewPage';
import PriceAlertModal from '@/components/PriceAlertModal';
import { usePriceAlerts } from '@/hooks/usePriceAlerts';
import { Zap, LayoutDashboard, BarChart3 } from 'lucide-react';

type TabType = 'dashboard' | 'overview';

export default function Dashboard() {
    const [activeTab, setActiveTab] = useState<TabType>('dashboard');

    // Initialize price alert monitoring
    usePriceAlerts();

    return (
        <div className="h-screen flex flex-col overflow-hidden">
            {/* Header */}
            <header className="h-12 border-b border-oracle-border bg-gradient-to-r from-oracle-dark via-oracle-dark to-violet/5 backdrop-blur-md flex items-center px-6 sticky top-0 z-50">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet via-pink to-cyan flex items-center justify-center shadow-lg shadow-pink/20">
                        <Zap className="w-4 h-4 text-white" />
                    </div>
                    <h1 className="text-lg font-bold bg-gradient-to-r from-white via-pink to-cyan bg-clip-text text-transparent">
                        Oracle-X
                    </h1>
                </div>

                {/* Tab Navigation */}
                <div className="flex items-center gap-1 ml-8 bg-oracle-darker/50 rounded-lg p-1 border border-oracle-border">
                    <button
                        onClick={() => setActiveTab('dashboard')}
                        className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === 'dashboard'
                                ? 'bg-oracle-accent text-white shadow-lg shadow-oracle-accent/30'
                                : 'text-gray-400 hover:text-white hover:bg-oracle-card'
                            }`}
                    >
                        <LayoutDashboard className="w-4 h-4" />
                        <span>Dashboard</span>
                    </button>
                    <button
                        onClick={() => setActiveTab('overview')}
                        className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === 'overview'
                                ? 'bg-oracle-accent text-white shadow-lg shadow-oracle-accent/30'
                                : 'text-gray-400 hover:text-white hover:bg-oracle-card'
                            }`}
                    >
                        <BarChart3 className="w-4 h-4" />
                        <span>Overview</span>
                    </button>
                </div>

                <span className="text-xs text-gray-500 hidden sm:inline ml-auto">Financial Intelligence Terminal</span>
            </header>

            {/* Main Content - Conditional based on active tab */}
            {activeTab === 'dashboard' ? (
                <main className="flex-1 grid grid-cols-[22%_50%_28%] gap-0 overflow-hidden h-[calc(100vh-48px)]">
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
            ) : (
                <main className="flex-1 overflow-hidden h-[calc(100vh-48px)]">
                    <OverviewPage />
                </main>
            )}

            {/* Price Alert Modal */}
            <PriceAlertModal />
        </div>
    );
}
