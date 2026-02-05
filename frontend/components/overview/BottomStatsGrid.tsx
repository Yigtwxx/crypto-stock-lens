'use client';

import { BarChart2, Coins, Globe, Zap } from 'lucide-react';
import { MarketOverview } from '@/lib/api';
import { formatLargeNumber } from './overview-utils';

interface BottomStatsGridProps {
    marketData: MarketOverview | null;
    marketType: 'crypto' | 'nasdaq';
}

export default function BottomStatsGrid({ marketData, marketType }: BottomStatsGridProps) {
    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Quick Stats Cards */}
            <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-violet/10 border border-oracle-border">
                <div className="flex items-center gap-2 mb-2">
                    <Globe className="w-4 h-4 text-violet-400" />
                    <span className="text-xs text-gray-400">Total Market Cap</span>
                </div>
                <p className="text-xl font-bold text-white">
                    {marketData ? formatLargeNumber(marketData.total_market_cap) : '--'}
                </p>
            </div>

            <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-cyan/10 border border-oracle-border">
                <div className="flex items-center gap-2 mb-2">
                    <BarChart2 className="w-4 h-4 text-cyan" />
                    <span className="text-xs text-gray-400">24h Volume</span>
                </div>
                <p className="text-xl font-bold text-white">
                    {marketData ? formatLargeNumber(marketData.total_volume_24h) : '--'}
                </p>
            </div>

            <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-orange-500/10 border border-oracle-border">
                <div className="flex items-center gap-2 mb-2">
                    <Zap className="w-4 h-4 text-orange-400" />
                    <span className="text-xs text-gray-400">{marketType === 'nasdaq' ? 'Tech Weight' : 'BTC Dominance'}</span>
                </div>
                <p className="text-xl font-bold text-white">
                    {marketType === 'nasdaq' ? 'N/A' : (marketData ? `${marketData.btc_dominance.toFixed(1)}%` : '--')}
                </p>
            </div>

            <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-green-500/10 border border-oracle-border">
                <div className="flex items-center gap-2 mb-2">
                    <Coins className="w-4 h-4 text-green-400" />
                    <span className="text-xs text-gray-400">{marketType === 'nasdaq' ? 'Aktif Hisse' : 'Aktif Kripto Para'}</span>
                </div>
                <p className="text-xl font-bold text-white">
                    {marketData ? marketData.active_cryptocurrencies.toLocaleString() : '--'}
                </p>
            </div>
        </div>
    );
}
