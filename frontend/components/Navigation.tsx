'use client';

import { useState, useRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Zap, LayoutDashboard, BarChart3, ChevronDown, Bitcoin, LineChart, MessageCircle, Home, Layers, User, BrainCircuit, Users } from 'lucide-react';

export default function Navigation() {
    const pathname = usePathname();
    const [showDropdown, setShowDropdown] = useState(false);
    const closeTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    // Determine active tab from pathname
    const getActiveTab = () => {
        if (pathname === '/') return 'home';
        if (pathname.startsWith('/dashboard')) return 'dashboard';
        if (pathname.startsWith('/overview')) return 'overview';
        if (pathname.startsWith('/analysis')) return 'analysis';
        if (pathname.startsWith('/chat')) return 'chat';
        if (pathname.startsWith('/heatmap')) return 'heatmap';
        if (pathname.startsWith('/community')) return 'community';
        if (pathname.startsWith('/profile')) return 'profile';
        return 'home';
    };

    const activeTab = getActiveTab();

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

    return (
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
                    <Link
                        href="/"
                        className={`flex items-center gap-2 px-2 py-2 text-sm font-medium transition-all duration-300 ease-out hover:scale-105 active:scale-95 ${activeTab === 'home'
                            ? 'text-purple-400'
                            : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        <Home className="w-4 h-4" />
                        <span>Home</span>
                    </Link>

                    <Link
                        href="/dashboard"
                        className={`flex items-center gap-2 px-2 py-2 text-sm font-medium transition-all duration-300 ease-out hover:scale-105 active:scale-95 ${activeTab === 'dashboard'
                            ? 'text-cyan'
                            : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        <LayoutDashboard className="w-4 h-4" />
                        <span>Dashboard</span>
                    </Link>

                    {/* Overview Dropdown */}
                    <div
                        className="relative"
                        onMouseEnter={handleDropdownOpen}
                        onMouseLeave={handleDropdownClose}
                    >
                        <Link
                            href="/overview?type=crypto"
                            className={`flex items-center gap-2 px-2 py-2 text-sm font-medium transition-all duration-300 ease-out hover:scale-105 active:scale-95 ${activeTab === 'overview'
                                ? 'text-yellow-400'
                                : 'text-gray-400 hover:text-white'
                                }`}
                        >
                            <BarChart3 className="w-4 h-4" />
                            <span>Overview</span>
                            <ChevronDown className={`w-3 h-3 transition-transform ${showDropdown ? 'rotate-180' : ''}`} />
                        </Link>

                        {/* Dropdown Menu - using pt-2 for seamless hover area */}
                        {showDropdown && (
                            <div className="absolute top-full left-0 pt-2 z-50">
                                <div className="w-48 py-2 bg-oracle-card border border-oracle-border rounded-lg shadow-xl shadow-black/50">
                                    <Link
                                        href="/overview?type=crypto"
                                        onClick={() => setShowDropdown(false)}
                                        className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${pathname === '/overview' && new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '').get('type') !== 'nasdaq'
                                            ? 'bg-violet/20 text-cyan'
                                            : 'text-gray-300 hover:bg-oracle-border/50 hover:text-white'
                                            }`}
                                    >
                                        <Bitcoin className="w-4 h-4 text-orange-400" />
                                        <span>Crypto</span>
                                    </Link>
                                    <Link
                                        href="/overview?type=nasdaq"
                                        onClick={() => setShowDropdown(false)}
                                        className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${pathname === '/overview' && new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '').get('type') === 'nasdaq'
                                            ? 'bg-violet/20 text-cyan'
                                            : 'text-gray-300 hover:bg-oracle-border/50 hover:text-white'
                                            }`}
                                    >
                                        <LineChart className="w-4 h-4 text-green-400" />
                                        <span>NASDAQ</span>
                                    </Link>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Analysis Tab */}
                    <Link
                        href="/analysis"
                        className={`flex items-center gap-2 px-2 py-2 text-sm font-medium transition-all duration-300 ease-out hover:scale-105 active:scale-95 ${activeTab === 'analysis'
                            ? 'text-blue-400'
                            : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        <BrainCircuit className="w-4 h-4" />
                        <span>Analysis</span>
                    </Link>

                    {/* Chat Tab */}
                    <Link
                        href="/chat"
                        className={`flex items-center gap-2 px-2 py-2 text-sm font-medium transition-all duration-300 ease-out hover:scale-105 active:scale-95 ${activeTab === 'chat'
                            ? 'text-pink'
                            : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        <MessageCircle className="w-4 h-4" />
                        <span>Chat</span>
                    </Link>

                    {/* Heatmap Tab */}
                    <Link
                        href="/heatmap"
                        className={`flex items-center gap-2 px-2 py-2 text-sm font-medium transition-all duration-300 ease-out hover:scale-105 active:scale-95 ${activeTab === 'heatmap'
                            ? 'text-red-400'
                            : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        <Layers className="w-4 h-4" />
                        <span>Heatmap</span>
                    </Link>

                    {/* Community Tab */}
                    <Link
                        href="/community"
                        className={`flex items-center gap-2 px-2 py-2 text-sm font-medium transition-all duration-300 ease-out hover:scale-105 active:scale-95 ${activeTab === 'community'
                            ? 'text-orange-400'
                            : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        <Users className="w-4 h-4" />
                        <span>Community</span>
                    </Link>

                    {/* Profile Tab */}
                    <Link
                        href="/profile"
                        className={`flex items-center gap-2 px-2 py-2 text-sm font-medium transition-all duration-300 ease-out hover:scale-105 active:scale-95 ${activeTab === 'profile'
                            ? 'text-teal'
                            : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        <User className="w-4 h-4" />
                        <span>Profile</span>
                    </Link>
                </div>
            </div>

            {/* Right side */}
            <span className="text-xs text-gray-500 hidden sm:inline">Financial Intelligence Terminal</span>
        </header>
    );
}
