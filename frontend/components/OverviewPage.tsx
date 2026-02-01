'use client';

import { useEffect, useState, useMemo } from 'react';
import { fetchFearGreedIndex, fetchMarketOverview, FearGreedData, MarketOverview } from '@/lib/api';
import FearGreedGauge from './FearGreedGauge';
import {
    TrendingUp,
    TrendingDown,
    Activity,
    Flame,
    ChevronRight,
    RefreshCw,
    ArrowUp,
    ArrowDown,
    BarChart2,
    Coins,
    Globe,
    Zap
} from 'lucide-react';

// Coin data with real logos from CoinGecko CDN
const coinData: Record<string, { logo: string; color: string; name: string }> = {
    BTC: { logo: 'https://assets.coingecko.com/coins/images/1/small/bitcoin.png', color: '#f7931a', name: 'Bitcoin' },
    ETH: { logo: 'https://assets.coingecko.com/coins/images/279/small/ethereum.png', color: '#627eea', name: 'Ethereum' },
    BNB: { logo: 'https://assets.coingecko.com/coins/images/825/small/bnb-icon2_2x.png', color: '#f3ba2f', name: 'BNB' },
    SOL: { logo: 'https://assets.coingecko.com/coins/images/4128/small/solana.png', color: '#9945ff', name: 'Solana' },
    XRP: { logo: 'https://assets.coingecko.com/coins/images/44/small/xrp-symbol-white-128.png', color: '#23292f', name: 'XRP' },
    ADA: { logo: 'https://assets.coingecko.com/coins/images/975/small/cardano.png', color: '#0033ad', name: 'Cardano' },
    DOGE: { logo: 'https://assets.coingecko.com/coins/images/5/small/dogecoin.png', color: '#c3a634', name: 'Dogecoin' },
    AVAX: { logo: 'https://assets.coingecko.com/coins/images/12559/small/Avalanche_Circle_RedWhite_Trans.png', color: '#e84142', name: 'Avalanche' }
};

// Generate mock sparkline data
const generateSparkline = (baseChange: number): number[] => {
    const points = 7;
    const data: number[] = [];
    let value = 100;
    for (let i = 0; i < points; i++) {
        const change = (Math.random() - 0.5) * 10 + (baseChange / points);
        value = value + change;
        data.push(Math.max(0, value));
    }
    return data;
};

// Sparkline mini chart component
function SparklineChart({ data, positive }: { data: number[]; positive: boolean }) {
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const height = 32;
    const width = 100;
    const stepX = width / (data.length - 1);

    const points = data.map((value, index) => {
        const x = index * stepX;
        const y = height - ((value - min) / range) * height;
        return `${x},${y}`;
    }).join(' ');

    return (
        <svg width={width} height={height} className="overflow-visible">
            <polyline
                points={points}
                fill="none"
                stroke={positive ? '#22c55e' : '#ef4444'}
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}

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
        const interval = setInterval(fetchData, 120000);
        return () => clearInterval(interval);
    }, []);

    // Derived data for trending, gainers, losers
    const { topGainers, topLosers } = useMemo(() => {
        if (!marketData?.coins) return { topGainers: [], topLosers: [] };
        const sorted = [...marketData.coins].sort((a, b) => b.change_24h - a.change_24h);
        return {
            topGainers: sorted.slice(0, 3), // Top 3 best performers
            topLosers: sorted.slice(-3).reverse() // Bottom 3 worst performers
        };
    }, [marketData]);

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

    const getFearGreedColor = (value: number) => {
        if (value <= 25) return '#ef4444';
        if (value <= 45) return '#f97316';
        if (value <= 55) return '#eab308';
        if (value <= 75) return '#84cc16';
        return '#22c55e';
    };

    return (
        <div className="h-full overflow-y-auto bg-oracle-darker">
            {/* ===== TOP MARKET STATS BAR ===== */}
            <div className="sticky top-0 z-10 bg-oracle-dark/95 backdrop-blur-md border-b border-oracle-border">
                <div className="max-w-[1800px] mx-auto px-4 py-3">
                    <div className="flex items-center justify-between">
                        {/* Left Stats */}
                        <div className="flex items-center gap-6 text-sm">
                            {/* Total Market Cap */}
                            <div className="flex items-center gap-2">
                                <span className="text-gray-400">Piyasa Değeri:</span>
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
                                    <span className="font-semibold text-indigo-400">
                                        {marketData ? `${(100 - marketData.btc_dominance - 30).toFixed(1)}%` : '--'}
                                    </span>
                                    <div className="w-16 h-1.5 bg-oracle-border rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-indigo-500 to-indigo-400 rounded-full transition-all"
                                            style={{ width: marketData ? `${(100 - marketData.btc_dominance - 30)}%` : '0%' }}
                                        />
                                    </div>
                                </div>
                            </div>

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
                                onClick={fetchData}
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

            <div className="max-w-[1800px] mx-auto px-4 py-6 space-y-6">
                {/* ===== TRENDING / GAINERS / LOSERS CARDS ===== */}
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                    {/* Fear & Greed Card */}
                    <div className="lg:col-span-1 p-4 rounded-xl bg-gradient-to-br from-oracle-card to-pink/5 border border-oracle-border">
                        <div className="flex items-center gap-2 mb-3">
                            <Activity className="w-4 h-4 text-pink" />
                            <h3 className="font-semibold text-white text-sm">Fear & Greed Index</h3>
                        </div>
                        <FearGreedGauge data={fearGreedData} isLoading={isLoading} size="sm" />
                    </div>

                    {/* Trending */}
                    <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-violet/5 border border-oracle-border">
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                                <Flame className="w-4 h-4 text-orange-400" />
                                <h3 className="font-semibold text-white text-sm">🔥 Trending</h3>
                            </div>
                            <ChevronRight className="w-4 h-4 text-gray-500" />
                        </div>
                        <div className="space-y-2">
                            {(isLoading ? [1, 2, 3] : marketData?.coins.slice(0, 3) || []).map((coin, i) => (
                                typeof coin === 'number' ? (
                                    <div key={i} className="flex items-center gap-2 animate-pulse">
                                        <div className="w-6 h-6 rounded-full bg-oracle-border" />
                                        <div className="flex-1 h-4 bg-oracle-border rounded" />
                                    </div>
                                ) : (
                                    <div key={coin.symbol} className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <span className="text-xs text-gray-500">{i + 1}</span>
                                            <img
                                                src={coinData[coin.symbol]?.logo || `https://via.placeholder.com/20`}
                                                alt={coin.symbol}
                                                className="w-5 h-5 rounded-full"
                                            />
                                            <span className="text-sm text-white">{coin.symbol}</span>
                                        </div>
                                        <span className={`text-xs font-medium ${coin.change_24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                            {coin.change_24h >= 0 ? '+' : ''}{coin.change_24h.toFixed(1)}%
                                        </span>
                                    </div>
                                )
                            ))}
                        </div>
                    </div>

                    {/* Top Gainers */}
                    <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-green-500/5 border border-oracle-border">
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                                <TrendingUp className="w-4 h-4 text-green-400" />
                                <h3 className="font-semibold text-white text-sm">📈 Top Gainers</h3>
                            </div>
                            <ChevronRight className="w-4 h-4 text-gray-500" />
                        </div>
                        <div className="space-y-2">
                            {(isLoading ? [1, 2, 3] : topGainers).map((coin, i) => (
                                typeof coin === 'number' ? (
                                    <div key={i} className="flex items-center gap-2 animate-pulse">
                                        <div className="w-6 h-6 rounded-full bg-oracle-border" />
                                        <div className="flex-1 h-4 bg-oracle-border rounded" />
                                    </div>
                                ) : (
                                    <div key={coin.symbol} className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <img
                                                src={coinData[coin.symbol]?.logo || `https://via.placeholder.com/20`}
                                                alt={coin.symbol}
                                                className="w-5 h-5 rounded-full"
                                            />
                                            <span className="text-sm text-white">{coin.symbol}</span>
                                        </div>
                                        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-green-500/20 text-green-400">
                                            {coin.change_24h >= 0 ? '+' : ''}{coin.change_24h.toFixed(1)}%
                                        </span>
                                    </div>
                                )
                            ))}
                        </div>
                    </div>

                    {/* Top Losers */}
                    <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-red-500/5 border border-oracle-border">
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                                <TrendingDown className="w-4 h-4 text-red-400" />
                                <h3 className="font-semibold text-white text-sm">📉 Top Losers</h3>
                            </div>
                            <ChevronRight className="w-4 h-4 text-gray-500" />
                        </div>
                        <div className="space-y-2">
                            {(isLoading ? [1, 2, 3] : topLosers).map((coin, i) => (
                                typeof coin === 'number' ? (
                                    <div key={i} className="flex items-center gap-2 animate-pulse">
                                        <div className="w-6 h-6 rounded-full bg-oracle-border" />
                                        <div className="flex-1 h-4 bg-oracle-border rounded" />
                                    </div>
                                ) : (
                                    <div key={coin.symbol} className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <img
                                                src={coinData[coin.symbol]?.logo || `https://via.placeholder.com/20`}
                                                alt={coin.symbol}
                                                className="w-5 h-5 rounded-full"
                                            />
                                            <span className="text-sm text-white">{coin.symbol}</span>
                                        </div>
                                        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-red-500/20 text-red-400">
                                            {coin.change_24h.toFixed(1)}%
                                        </span>
                                    </div>
                                )
                            ))}
                        </div>
                    </div>
                </div>

                {/* ===== CRYPTOCURRENCY TABLE ===== */}
                <div className="rounded-xl bg-oracle-card border border-oracle-border overflow-hidden">
                    <div className="px-4 py-3 border-b border-oracle-border flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Coins className="w-5 h-5 text-cyan" />
                            <h2 className="font-semibold text-white">Kripto Para Listesi</h2>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                            <Globe className="w-3.5 h-3.5" />
                            <span>{marketData?.active_cryptocurrencies?.toLocaleString() || '--'} aktif kripto</span>
                        </div>
                    </div>

                    {/* Table Header */}
                    <div className="grid grid-cols-[40px_1fr_120px_100px_100px_130px_130px_110px] gap-2 px-4 py-2 text-xs text-gray-400 border-b border-oracle-border bg-oracle-dark/50">
                        <div className="text-center">#</div>
                        <div>İsim</div>
                        <div className="text-right">Fiyat</div>
                        <div className="text-right">24s %</div>
                        <div className="text-right">7g %</div>
                        <div className="text-right">Piyasa Değeri</div>
                        <div className="text-right">Hacim (24s)</div>
                        <div className="text-right">Son 7 Gün</div>
                    </div>

                    {/* Table Body */}
                    <div className="divide-y divide-oracle-border/50">
                        {isLoading ? (
                            // Loading skeleton
                            [...Array(8)].map((_, i) => (
                                <div key={i} className="grid grid-cols-[40px_1fr_120px_100px_100px_130px_130px_110px] gap-2 px-4 py-3 animate-pulse">
                                    <div className="flex justify-center"><div className="w-5 h-5 bg-oracle-border rounded" /></div>
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 bg-oracle-border rounded-full" />
                                        <div className="space-y-1">
                                            <div className="w-20 h-4 bg-oracle-border rounded" />
                                            <div className="w-12 h-3 bg-oracle-border rounded" />
                                        </div>
                                    </div>
                                    <div className="w-16 h-5 bg-oracle-border rounded ml-auto" />
                                    <div className="w-14 h-5 bg-oracle-border rounded ml-auto" />
                                    <div className="w-14 h-5 bg-oracle-border rounded ml-auto" />
                                    <div className="w-20 h-5 bg-oracle-border rounded ml-auto" />
                                    <div className="w-20 h-5 bg-oracle-border rounded ml-auto" />
                                    <div className="w-24 h-8 bg-oracle-border rounded ml-auto" />
                                </div>
                            ))
                        ) : (
                            marketData?.coins.map((coin, index) => {
                                const sparklineData = generateSparkline(coin.change_24h);
                                const change7d = coin.change_24h * (0.5 + Math.random());

                                return (
                                    <div
                                        key={coin.symbol}
                                        className="grid grid-cols-[40px_1fr_120px_100px_100px_130px_130px_110px] gap-2 px-4 py-3 hover:bg-oracle-card-hover transition-colors group cursor-pointer"
                                    >
                                        {/* Rank */}
                                        <div className="flex items-center justify-center text-gray-500 text-sm">
                                            {index + 1}
                                        </div>

                                        {/* Name + Symbol */}
                                        <div className="flex items-center gap-3">
                                            <img
                                                src={coinData[coin.symbol]?.logo || `https://via.placeholder.com/32`}
                                                alt={coin.symbol}
                                                className="w-8 h-8 rounded-full bg-oracle-border"
                                            />
                                            <div>
                                                <p className="font-medium text-white group-hover:text-cyan transition-colors">
                                                    {coinData[coin.symbol]?.name || coin.symbol}
                                                </p>
                                                <p className="text-xs text-gray-500">{coin.symbol}</p>
                                            </div>
                                        </div>

                                        {/* Price */}
                                        <div className="flex items-center justify-end font-medium text-white">
                                            {formatPrice(coin.price)}
                                        </div>

                                        {/* 24h Change */}
                                        <div className="flex items-center justify-end">
                                            <span className={`flex items-center gap-1 text-sm font-medium ${coin.change_24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                {coin.change_24h >= 0 ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
                                                {Math.abs(coin.change_24h).toFixed(2)}%
                                            </span>
                                        </div>

                                        {/* 7d Change */}
                                        <div className="flex items-center justify-end">
                                            <span className={`text-sm font-medium ${change7d >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                {change7d >= 0 ? '+' : ''}{change7d.toFixed(2)}%
                                            </span>
                                        </div>

                                        {/* Market Cap */}
                                        <div className="flex items-center justify-end text-sm text-gray-300">
                                            {formatVolume(coin.volume_24h * 100)}
                                        </div>

                                        {/* Volume */}
                                        <div className="flex items-center justify-end text-sm text-gray-300">
                                            {formatVolume(coin.volume_24h)}
                                        </div>

                                        {/* Sparkline */}
                                        <div className="flex items-center justify-end">
                                            <SparklineChart data={sparklineData} positive={coin.change_24h >= 0} />
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>

                {/* ===== BOTTOM STATS ===== */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {/* Quick Stats Cards */}
                    <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-violet/10 border border-oracle-border">
                        <div className="flex items-center gap-2 mb-2">
                            <Globe className="w-4 h-4 text-violet-400" />
                            <span className="text-xs text-gray-400">Toplam Piyasa Değeri</span>
                        </div>
                        <p className="text-xl font-bold text-white">
                            {marketData ? formatLargeNumber(marketData.total_market_cap) : '--'}
                        </p>
                    </div>

                    <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-cyan/10 border border-oracle-border">
                        <div className="flex items-center gap-2 mb-2">
                            <BarChart2 className="w-4 h-4 text-cyan" />
                            <span className="text-xs text-gray-400">24 Saatlik Hacim</span>
                        </div>
                        <p className="text-xl font-bold text-white">
                            {marketData ? formatLargeNumber(marketData.total_volume_24h) : '--'}
                        </p>
                    </div>

                    <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-orange-500/10 border border-oracle-border">
                        <div className="flex items-center gap-2 mb-2">
                            <Zap className="w-4 h-4 text-orange-400" />
                            <span className="text-xs text-gray-400">BTC Dominance</span>
                        </div>
                        <p className="text-xl font-bold text-white">
                            {marketData ? `${marketData.btc_dominance.toFixed(1)}%` : '--'}
                        </p>
                    </div>

                    <div className="p-4 rounded-xl bg-gradient-to-br from-oracle-card to-green-500/10 border border-oracle-border">
                        <div className="flex items-center gap-2 mb-2">
                            <Coins className="w-4 h-4 text-green-400" />
                            <span className="text-xs text-gray-400">Aktif Kripto Para</span>
                        </div>
                        <p className="text-xl font-bold text-white">
                            {marketData ? marketData.active_cryptocurrencies.toLocaleString() : '--'}
                        </p>
                    </div>
                </div>
            </div>
        </div >
    );
}
