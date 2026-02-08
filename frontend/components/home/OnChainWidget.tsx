'use client';

import React, { useEffect, useState } from 'react';
import { RefreshCw, TrendingUp, TrendingDown, Anchor, ArrowRightLeft, DollarSign } from 'lucide-react';

interface WhaleTrade {
    symbol: string;
    price: number;
    quantity: number;
    value: number;
    side: 'buy' | 'sell';
    timestamp: number;
}

interface OnChainStats {
    total_24h_volume?: number;
    net_flow?: number;
    buy_pressure_percent?: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function OnChainWidget() {
    const [trades, setTrades] = useState<WhaleTrade[]>([]);
    const [stats, setStats] = useState<OnChainStats>({});
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/onchain/whales`);
            if (res.ok) {
                const data = await res.json();
                setTrades(data.trades || []);
                setStats(data.stats || {});
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000); // Poll every 10s
        return () => clearInterval(interval);
    }, []);

    const formatMoney = (val: number) => {
        if (val >= 1000000) return `$${(val / 1000000).toFixed(2)}M`;
        return `$${(val / 1000).toFixed(0)}k`;
    };

    const getTimeAgo = (ts: number) => {
        const seconds = Math.floor((Date.now() - ts) / 1000);
        if (seconds < 60) return `${seconds}s ago`;
        return `${Math.floor(seconds / 60)}m ago`;
    };

    return (
        <div className="bg-oracle-card border border-oracle-border rounded-xl p-6 h-full flex flex-col relative overflow-hidden group hover:border-blue-500/30 transition-all duration-300">
            {/* Header */}
            <div className="flex items-center justify-between mb-4 z-10">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-blue-500/10 rounded-lg">
                        <Anchor className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                        <h3 className="font-bold text-white text-sm">Whale Radar</h3>
                        <p className="text-xs text-gray-400">On-Chain Activity {'>'} $500k</p>
                    </div>
                </div>
                {loading && <RefreshCw className="w-4 h-4 text-gray-500 animate-spin" />}
            </div>

            {/* Background Effect */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />

            {/* Stats Bar */}
            <div className="grid grid-cols-2 gap-3 mb-4 z-10">
                <div className="bg-[#0b0b15]/50 border border-white/5 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-1">
                        <DollarSign className="w-3.5 h-3.5 text-gray-400" />
                        <span className="text-xs text-gray-400">Net Flow (Recent)</span>
                    </div>
                    <span className={`text-lg font-mono font-bold ${(stats.net_flow || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {(stats.net_flow || 0) > 0 ? '+' : ''}{formatMoney(stats.net_flow || 0)}
                    </span>
                </div>
                <div className="bg-[#0b0b15]/50 border border-white/5 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-1">
                        <ArrowRightLeft className="w-3.5 h-3.5 text-gray-400" />
                        <span className="text-xs text-gray-400">Buy Pressure</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                            <div
                                className={`h-full rounded-full transition-all duration-500 ${(stats.buy_pressure_percent || 50) > 50 ? 'bg-green-500' : 'bg-red-500'
                                    }`}
                                style={{ width: `${stats.buy_pressure_percent || 50}%` }}
                            />
                        </div>
                        <span className="text-xs font-mono text-white">{(stats.buy_pressure_percent || 50).toFixed(0)}%</span>
                    </div>
                </div>
            </div>

            {/* Trade List */}
            <div className="flex-1 overflow-y-auto custom-scrollbar -mr-2 pr-2 z-10 space-y-2">
                {trades.length === 0 && !loading ? (
                    <div className="text-center py-8 text-gray-500 text-xs">No active whales detected...</div>
                ) : (
                    trades.map((trade, i) => (
                        <div key={i} className="flex items-center justify-between p-2.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors border border-transparent hover:border-white/10">
                            <div className="flex items-center gap-3">
                                <div className={`w-1.5 h-8 rounded-full ${trade.side === 'buy' ? 'bg-green-500' : 'bg-red-500'}`} />
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm font-bold text-white">{trade.symbol}</span>
                                        <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${trade.side === 'buy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                                            }`}>
                                            {trade.side}
                                        </span>
                                    </div>
                                    <span className="text-xs text-gray-500">{getTimeAgo(trade.timestamp)}</span>
                                </div>
                            </div>
                            <div className="text-right">
                                <div className="text-sm font-mono font-medium text-white">{formatMoney(trade.value)}</div>
                                <div className="text-xs text-gray-500">
                                    @{trade.price.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
