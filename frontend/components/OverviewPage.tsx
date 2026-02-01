'use client';

import { useEffect, useState } from 'react';
import { fetchFearGreedIndex, fetchMarketOverview, FearGreedData, MarketOverview } from '@/lib/api';
import FearGreedGauge from './FearGreedGauge';
import {
    TrendingUp,
    TrendingDown,
    Activity,
    DollarSign,
    BarChart3,
    Globe,
    RefreshCw,
    Bitcoin,
    Coins
} from 'lucide-react';

// Coin icons mapping
const coinIcons: Record<string, string> = {
    BTC: '₿',
    ETH: 'Ξ',
    BNB: '◆',
    SOL: '◎',
    XRP: '✕',
    ADA: '₳',
    DOGE: 'Ð',
    AVAX: 'A'
};

// Coin colors
const coinColors: Record<string, string> = {
    BTC: '#f7931a',
    ETH: '#627eea',
    BNB: '#f3ba2f',
    SOL: '#9945ff',
    XRP: '#23292f',
    ADA: '#0033ad',
    DOGE: '#c3a634',
    AVAX: '#e84142'
};

export default function OverviewPage() {
    const [fearGreedData, setFearGreedData] = useState<FearGreedData | null>(null);
    const [marketData, setMarketData] = useState<MarketOverview | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

    const fetchData = async () => {
        setIsLoading(true);
        try {
            const [fgData, mktData] = await Promise.all([
                fetchFearGreedIndex(),
                fetchMarketOverview()
            ]);
            setFearGreedData(fgData);
            setMarketData(mktData);
            setLastUpdate(new Date());
        } catch (error) {
            console.error('Failed to fetch overview data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        // Refresh every 2 minutes
        const interval = setInterval(fetchData, 120000);
        return () => clearInterval(interval);
    }, []);

    const formatPrice = (price: number) => {
        if (price >= 1000) {
            return `$${price.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
        }
        return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    };

    const formatLargeNumber = (num: number) => {
        if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
        if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
        if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
        return `$${num.toLocaleString()}`;
    };

    const formatVolume = (num: number) => {
        if (num >= 1e9) return `$${(num / 1e9).toFixed(1)}B`;
        if (num >= 1e6) return `$${(num / 1e6).toFixed(1)}M`;
        return `$${num.toLocaleString()}`;
    };

    return (
        <div className="h-full overflow-y-auto p-6 bg-oracle-darker">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold bg-gradient-to-r from-white via-pink to-cyan bg-clip-text text-transparent">
                            Piyasa Genel Bakış
                        </h1>
                        <p className="text-sm text-gray-500 mt-1">
                            Kripto piyasası anlık veriler ve duygu analizi
                        </p>
                    </div>
                    <button
                        onClick={fetchData}
                        disabled={isLoading}
                        className="flex items-center gap-2 px-4 py-2 bg-oracle-card border border-oracle-border rounded-lg hover:border-oracle-accent transition-colors disabled:opacity-50"
                    >
                        <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                        <span className="text-sm">Yenile</span>
                    </button>
                </div>

                {/* Top Section - Fear & Greed + Market Stats */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Fear & Greed Card */}
                    <div className="lg:col-span-1 p-6 rounded-2xl bg-oracle-card border border-oracle-border">
                        <div className="flex items-center gap-2 mb-4">
                            <Activity className="w-5 h-5 text-pink" />
                            <h2 className="font-semibold text-white">Fear & Greed Index</h2>
                        </div>
                        <FearGreedGauge data={fearGreedData} isLoading={isLoading} size="lg" />

                        {/* 7-day history mini chart */}
                        {fearGreedData?.history && fearGreedData.history.length > 0 && (
                            <div className="mt-4 pt-4 border-t border-oracle-border">
                                <p className="text-xs text-gray-500 mb-2">Son 7 Gün</p>
                                <div className="flex items-end justify-between gap-1 h-12">
                                    {fearGreedData.history.slice().reverse().map((h, i) => (
                                        <div key={i} className="flex-1 flex flex-col items-center">
                                            <div
                                                className="w-full rounded-sm transition-all"
                                                style={{
                                                    height: `${(h.value / 100) * 40}px`,
                                                    backgroundColor: h.value <= 25 ? '#ef4444' :
                                                        h.value <= 45 ? '#f97316' :
                                                            h.value <= 55 ? '#eab308' :
                                                                h.value <= 75 ? '#84cc16' : '#22c55e'
                                                }}
                                            />
                                            <span className="text-[8px] text-gray-600 mt-1">{h.value}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Market Stats Cards */}
                    <div className="lg:col-span-2 grid grid-cols-2 gap-4">
                        {/* Total Market Cap */}
                        <div className="p-5 rounded-xl bg-gradient-to-br from-oracle-card to-violet/10 border border-oracle-border">
                            <div className="flex items-center gap-2 mb-2">
                                <Globe className="w-4 h-4 text-violet-400" />
                                <span className="text-xs text-gray-400">Toplam Piyasa Değeri</span>
                            </div>
                            <p className="text-2xl font-bold text-white">
                                {marketData ? formatLargeNumber(marketData.total_market_cap) : '--'}
                            </p>
                        </div>

                        {/* 24h Volume */}
                        <div className="p-5 rounded-xl bg-gradient-to-br from-oracle-card to-cyan/10 border border-oracle-border">
                            <div className="flex items-center gap-2 mb-2">
                                <BarChart3 className="w-4 h-4 text-cyan" />
                                <span className="text-xs text-gray-400">24s Hacim</span>
                            </div>
                            <p className="text-2xl font-bold text-white">
                                {marketData ? formatLargeNumber(marketData.total_volume_24h) : '--'}
                            </p>
                        </div>

                        {/* BTC Dominance */}
                        <div className="p-5 rounded-xl bg-gradient-to-br from-oracle-card to-orange-500/10 border border-oracle-border">
                            <div className="flex items-center gap-2 mb-2">
                                <Bitcoin className="w-4 h-4 text-orange-400" />
                                <span className="text-xs text-gray-400">BTC Dominance</span>
                            </div>
                            <p className="text-2xl font-bold text-white">
                                {marketData ? `${marketData.btc_dominance.toFixed(1)}%` : '--'}
                            </p>
                        </div>

                        {/* Active Cryptocurrencies */}
                        <div className="p-5 rounded-xl bg-gradient-to-br from-oracle-card to-green-500/10 border border-oracle-border">
                            <div className="flex items-center gap-2 mb-2">
                                <Coins className="w-4 h-4 text-green-400" />
                                <span className="text-xs text-gray-400">Aktif Kripto</span>
                            </div>
                            <p className="text-2xl font-bold text-white">
                                {marketData ? marketData.active_cryptocurrencies.toLocaleString() : '--'}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Coin Cards */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <DollarSign className="w-5 h-5 text-cyan" />
                        <h2 className="font-semibold text-white">Top Kripto Paralar</h2>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {isLoading ? (
                            // Loading skeleton
                            [...Array(8)].map((_, i) => (
                                <div key={i} className="p-4 rounded-xl bg-oracle-card border border-oracle-border animate-pulse">
                                    <div className="h-6 bg-oracle-border rounded w-16 mb-2" />
                                    <div className="h-8 bg-oracle-border rounded w-24 mb-2" />
                                    <div className="h-4 bg-oracle-border rounded w-20" />
                                </div>
                            ))
                        ) : (
                            marketData?.coins.map((coin) => (
                                <div
                                    key={coin.symbol}
                                    className="p-4 rounded-xl bg-oracle-card border border-oracle-border hover:border-oracle-accent transition-all group"
                                >
                                    <div className="flex items-center gap-2 mb-2">
                                        <span
                                            className="text-xl"
                                            style={{ color: coinColors[coin.symbol] || '#8b5cf6' }}
                                        >
                                            {coinIcons[coin.symbol] || '●'}
                                        </span>
                                        <span className="font-semibold text-white">{coin.symbol}</span>
                                    </div>
                                    <p className="text-xl font-bold text-white mb-1">
                                        {formatPrice(coin.price)}
                                    </p>
                                    <div className={`flex items-center gap-1 text-sm ${coin.change_24h >= 0 ? 'text-oracle-bullish' : 'text-oracle-bearish'
                                        }`}>
                                        {coin.change_24h >= 0 ? (
                                            <TrendingUp className="w-3 h-3" />
                                        ) : (
                                            <TrendingDown className="w-3 h-3" />
                                        )}
                                        <span>{coin.change_24h >= 0 ? '+' : ''}{coin.change_24h.toFixed(2)}%</span>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-2">
                                        Vol: {formatVolume(coin.volume_24h)}
                                    </p>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Last Update */}
                {lastUpdate && (
                    <p className="text-xs text-gray-600 text-center">
                        Son güncelleme: {lastUpdate.toLocaleTimeString('tr-TR')}
                    </p>
                )}
            </div>
        </div>
    );
}
