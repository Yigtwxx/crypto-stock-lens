'use client';

import { useState, useRef } from 'react';
import NewsFeed from '@/components/NewsFeed';
import ChartPanel from '@/components/ChartPanel';
import OraclePanel from '@/components/OraclePanel';
import OverviewPage from '@/components/OverviewPage';
import HomePage from '@/components/HomePage';
import PriceAlertModal from '@/components/PriceAlertModal';
import { usePriceAlerts } from '@/hooks/usePriceAlerts';
import { Zap, LayoutDashboard, BarChart3, ChevronDown, Bitcoin, LineChart, MessageCircle, Home } from 'lucide-react';
import OracleChatPage from '@/components/OracleChatPage';

type TabType = 'home' | 'dashboard' | 'overview' | 'chat';
type OverviewType = 'crypto' | 'nasdaq';

export default function Dashboard() {
    const [activeTab, setActiveTab] = useState<TabType>('home');
    const [overviewType, setOverviewType] = useState<OverviewType>('crypto');
    const [showDropdown, setShowDropdown] = useState(false);
    const closeTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    // Handle dropdown open with delay cancellation
    const handleDropdownOpen = () => {
        if (closeTimeoutRef.current) {
            clearTimeout(closeTimeoutRef.current);
            closeTimeoutRef.current = null;
        }
        setShowDropdown(true);
    };

    // Handle dropdown close with delay
    const handleDropdownClose = () => {
        closeTimeoutRef.current = setTimeout(() => {
            setShowDropdown(false);
        }, 200); // 200ms delay before closing
    };

    // Initialize price alert monitoring
    usePriceAlerts();

    const handleOverviewSelect = (type: OverviewType) => {
        setOverviewType(type);
        setActiveTab('overview');
        setShowDropdown(false);
    };

    return (
        <div className="h-screen flex flex-col overflow-hidden">
            {/* Header */}
            <header className="h-12 border-b border-oracle-border bg-gradient-to-r from-oracle-dark via-oracle-dark to-violet/5 backdrop-blur-md flex items-center px-6 sticky top-0 z-50">
                {/* Logo - Left */}
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet via-pink to-cyan flex items-center justify-center shadow-lg shadow-pink/20">
                        <Zap className="w-4 h-4 text-white" />
                    </div>
                    <h1 className="text-lg font-bold bg-gradient-to-r from-white via-pink to-cyan bg-clip-text text-transparent">
                        Oracle-X
                    </h1>
                </div>

                {/* Tab Navigation - Centered */}
                <div className="flex-1 flex justify-center">
                    <div className="flex items-center gap-6">
                        {/* Home Tab */}
                        <button
                            onClick={() => setActiveTab('home')}
                            className={`flex items-center gap-2 px-2 py-2 text-sm font-medium transition-all duration-200 ${activeTab === 'home'
                                ? 'text-purple-400'
                                : 'text-gray-400 hover:text-white'
                                }`}
                        >
                            <Home className="w-4 h-4" />
                            <span>Home</span>
                        </button>

                        <button
                            onClick={() => setActiveTab('dashboard')}
                            className={`flex items-center gap-2 px-2 py-2 text-sm font-medium transition-all duration-200 ${activeTab === 'dashboard'
                                ? 'text-cyan'
                                : 'text-gray-400 hover:text-white'
                                }`}
                        >
                            <LayoutDashboard className="w-4 h-4" />
                            <span>Dashboard</span>
                        </button>

                        {/* Overview Dropdown */}
                        <div
                            className="relative"
                            onMouseEnter={handleDropdownOpen}
                            onMouseLeave={handleDropdownClose}
                        >
                            <button
                                className={`flex items-center gap-2 px-2 py-2 text-sm font-medium transition-all duration-200 ${activeTab === 'overview'
                                    ? 'text-yellow-400'
                                    : 'text-amber-400 hover:text-white'
                                    }`}
                            >
                                <BarChart3 className="w-4 h-4" />
                                <span>Overview</span>
                                <ChevronDown className={`w-3 h-3 transition-transform ${showDropdown ? 'rotate-180' : ''}`} />
                            </button>

                            {/* Dropdown Menu - using pt-2 for seamless hover area */}
                            {showDropdown && (
                                <div className="absolute top-full left-0 pt-2 z-50">
                                    <div className="w-48 py-2 bg-oracle-card border border-oracle-border rounded-lg shadow-xl shadow-black/50">
                                        <button
                                            onClick={() => handleOverviewSelect('crypto')}
                                            className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${overviewType === 'crypto' && activeTab === 'overview'
                                                ? 'bg-violet/20 text-cyan'
                                                : 'text-gray-300 hover:bg-oracle-border/50 hover:text-white'
                                                }`}
                                        >
                                            <Bitcoin className="w-4 h-4 text-orange-400" />
                                            <span>Crypto</span>
                                            {overviewType === 'crypto' && activeTab === 'overview' && (
                                                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-cyan" />
                                            )}
                                        </button>
                                        <button
                                            onClick={() => handleOverviewSelect('nasdaq')}
                                            className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${overviewType === 'nasdaq' && activeTab === 'overview'
                                                ? 'bg-violet/20 text-cyan'
                                                : 'text-gray-300 hover:bg-oracle-border/50 hover:text-white'
                                                }`}
                                        >
                                            <LineChart className="w-4 h-4 text-green-400" />
                                            <span>NASDAQ</span>
                                            {overviewType === 'nasdaq' && activeTab === 'overview' && (
                                                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-cyan" />
                                            )}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Chat Tab */}
                        <button
                            onClick={() => setActiveTab('chat')}
                            className={`flex items-center gap-2 px-2 py-2 text-sm font-medium transition-all duration-200 ${activeTab === 'chat'
                                ? 'text-pink'
                                : 'text-gray-400 hover:text-white'
                                }`}
                        >
                            <MessageCircle className="w-4 h-4" />
                            <span>Chat</span>
                        </button>
                    </div>
                </div>

                {/* Right side */}
                <span className="text-xs text-gray-500 hidden sm:inline">Financial Intelligence Terminal</span>
            </header>

            {/* Main Content - Conditional based on active tab */}
            {activeTab === 'home' ? (
                <main className="flex-1 overflow-hidden h-[calc(100vh-48px)]">
                    <HomePage />
                </main>
            ) : activeTab === 'dashboard' ? (
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
            ) : activeTab === 'chat' ? (
                <main className="flex-1 overflow-hidden h-[calc(100vh-48px)]">
                    <OracleChatPage />
                </main>
            ) : (
                <main className="flex-1 overflow-hidden h-[calc(100vh-48px)]">
                    <OverviewPage marketType={overviewType} />
                </main>
            )}

            {/* Price Alert Modal */}
            <PriceAlertModal />
        </div>
    );
}
