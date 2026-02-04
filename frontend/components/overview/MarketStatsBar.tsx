'use client';

import { Activity, RefreshCw } from 'lucide-react';
import { MarketOverview, FearGreedData } from '@/lib/api';
import { formatLargeNumber, getFearGreedColor } from './overview-utils';

interface MarketStatsBarProps {
    marketData: MarketOverview | null;
    fearGreedData: FearGreedData | null;
    marketType: 'crypto' | 'nasdaq';
    isLoading: boolean;
    lastUpdate: Date | null;
    onRefresh: () => void;
}

export default function MarketStatsBar({
    marketData,
    fearGreedData,
    marketType,
    isLoading,
    lastUpdate,
    onRefresh
}: MarketStatsBarProps) {
    return (
        <div className="sticky top-0 z-10 bg-oracle-dark/95 backdrop-blur-md border-b border-oracle-border">
            <div className="max-w-[1800px] mx-auto px-4 py-3">
                <div className="flex items-center justify-between">
                    {/* Left Stats */}
                    <div className="flex items-center gap-6 text-sm">
                        {/* Total Market Cap */}
                        <div className="flex items-center gap-2">
                            <span className="text-gray-400">Market Cap:</span>
                            <span className="font-semibold text-white">
                                {marketData ? formatLargeNumber(marketData.total_market_cap) : '--'}
                            </span>
                            {marketData && (
                                <span className={`text-xs px-1.5 py-0.5 rounded ${marketData.total_market_cap > 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                                    +2.4%
                                </span>
                            )}
                        </div>

                        <div className="w-px h-4 bg-oracle-border" />

                        {/* 24h Volume */}
                        <div className="flex items-center gap-2">
                            <span className="text-gray-400">24s Hacim:</span>
                            <span className="font-semibold text-white">
                                {marketData ? formatLargeNumber(marketData.total_volume_24h) : '--'}
                            </span>
                        </div>

                        {/* BTC & ETH Dominance - Only show for crypto */}
                        {marketType === 'crypto' && (
                            <>
                                <div className="w-px h-4 bg-oracle-border" />

                                {/* BTC Dominance */}
                                <div className="flex items-center gap-2">
                                    <span className="text-gray-400">BTC:</span>
                                    <div className="flex items-center gap-1.5">
                                        <span className="font-semibold text-orange-400">
                                            {marketData ? `${marketData.btc_dominance.toFixed(1)}%` : '--'}
                                        </span>
                                        <div className="w-16 h-1.5 bg-oracle-border rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-gradient-to-r from-orange-500 to-orange-400 rounded-full transition-all"
                                                style={{ width: marketData ? `${marketData.btc_dominance}%` : '0%' }}
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="w-px h-4 bg-oracle-border" />

                                {/* ETH Dominance */}
                                <div className="flex items-center gap-2">
                                    <span className="text-gray-400">ETH:</span>
                                    <div className="flex items-center gap-1.5">
                                        <span className="font-semibold text-purple-400">
                                            {marketData?.eth_dominance ? `${marketData.eth_dominance.toFixed(1)}%` : '--'}
                                        </span>
                                        <div className="w-16 h-1.5 bg-oracle-border rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-gradient-to-r from-purple-500 to-purple-400 rounded-full transition-all"
                                                style={{ width: marketData?.eth_dominance ? `${Math.min(100, marketData.eth_dominance * 4)}%` : '0%' }}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </>
                        )}

                        <div className="w-px h-4 bg-oracle-border" />

                        {/* Fear & Greed Compact */}
                        <div className="flex items-center gap-2">
                            <Activity className="w-3.5 h-3.5 text-pink" />
                            <span className="text-gray-400">F&G:</span>
                            {fearGreedData && (
                                <span
                                    className="font-bold"
                                    style={{ color: getFearGreedColor(fearGreedData.value) }}
                                >
                                    {fearGreedData.value}
                                </span>
                            )}
                        </div>
                    </div>

                    {/* Right - Refresh Button */}
                    <div className="flex items-center gap-3">
                        {lastUpdate && (
                            <span className="text-xs text-gray-500">
                                Son: {lastUpdate.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                            </span>
                        )}
                        <button
                            onClick={onRefresh}
                            disabled={isLoading}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-oracle-card border border-oracle-border rounded-lg hover:border-violet transition-colors text-sm disabled:opacity-50"
                        >
                            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
                            <span>Yenile</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
