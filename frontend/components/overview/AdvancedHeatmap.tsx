'use client';

import { useState, useEffect, useMemo } from 'react';
import { TrendingUp, TrendingDown, Volume2, MessageCircle, Code, Loader2, RefreshCw } from 'lucide-react';

interface CoinData {
    id: string;
    symbol: string;
    name: string;
    sector: string;
    image: string;
    price: number;
    market_cap: number;
    volume_24h: number;
    price_change_24h: number;
    social_score: number;
    developer_score: number;
    volume_score: number;
}

interface HeatmapData {
    coins: CoinData[];
    sectors: Record<string, CoinData[]>;
    timestamp: string;
}

type MetricType = 'price' | 'volume' | 'social' | 'developer';

const METRIC_CONFIG = {
    price: {
        label: 'Fiyat Değişimi',
        icon: TrendingUp,
        field: 'price_change_24h',
        suffix: '%',
        colorPositive: true,
    },
    volume: {
        label: 'Hacim',
        icon: Volume2,
        field: 'volume_score',
        suffix: '',
        colorPositive: false,
    },
    social: {
        label: 'Sosyal Hype',
        icon: MessageCircle,
        field: 'social_score',
        suffix: '',
        colorPositive: false,
    },
    developer: {
        label: 'Geliştirici',
        icon: Code,
        field: 'developer_score',
        suffix: '',
        colorPositive: false,
    },
};

function getHeatmapColor(value: number, metric: MetricType): string {
    if (metric === 'price') {
        // Price change: red for negative, green for positive
        if (value >= 5) return 'bg-green-500';
        if (value >= 3) return 'bg-green-600';
        if (value >= 1) return 'bg-green-700';
        if (value >= 0) return 'bg-green-800/50';
        if (value >= -1) return 'bg-red-800/50';
        if (value >= -3) return 'bg-red-700';
        if (value >= -5) return 'bg-red-600';
        return 'bg-red-500';
    } else {
        // Score-based: gradient from low to high
        if (value >= 80) return 'bg-purple-500';
        if (value >= 60) return 'bg-indigo-500';
        if (value >= 40) return 'bg-blue-600';
        if (value >= 20) return 'bg-cyan-700';
        return 'bg-gray-700';
    }
}

function formatValue(value: number, metric: MetricType): string {
    const config = METRIC_CONFIG[metric];
    if (metric === 'price') {
        return `${value >= 0 ? '+' : ''}${value.toFixed(1)}${config.suffix}`;
    }
    return `${Math.round(value)}`;
}

function formatPrice(price: number): string {
    if (price >= 1000) return `$${(price / 1000).toFixed(1)}K`;
    if (price >= 1) return `$${price.toFixed(2)}`;
    return `$${price.toFixed(4)}`;
}

function formatMarketCap(cap: number): string {
    if (cap >= 1e12) return `$${(cap / 1e12).toFixed(1)}T`;
    if (cap >= 1e9) return `$${(cap / 1e9).toFixed(1)}B`;
    if (cap >= 1e6) return `$${(cap / 1e6).toFixed(1)}M`;
    return `$${cap.toLocaleString()}`;
}

export default function AdvancedHeatmap() {
    const [data, setData] = useState<HeatmapData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedMetric, setSelectedMetric] = useState<MetricType>('price');
    const [viewMode, setViewMode] = useState<'grid' | 'sector'>('grid');
    const [hoveredCoin, setHoveredCoin] = useState<CoinData | null>(null);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch('http://localhost:8000/api/heatmap/data');
            if (!res.ok) throw new Error('Failed to fetch data');
            const json = await res.json();
            setData(json);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 60000); // Refresh every minute
        return () => clearInterval(interval);
    }, []);

    const sortedCoins = useMemo(() => {
        if (!data?.coins) return [];
        const field = METRIC_CONFIG[selectedMetric].field as keyof CoinData;
        return [...data.coins].sort((a, b) => {
            const aVal = Number(a[field]) || 0;
            const bVal = Number(b[field]) || 0;
            return bVal - aVal;
        });
    }, [data, selectedMetric]);

    if (loading && !data) {
        return (
            <div className="h-full flex items-center justify-center bg-oracle-darker">
                <div className="text-center">
                    <Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-3" />
                    <p className="text-gray-400">Isı haritası yükleniyor...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full flex items-center justify-center bg-oracle-darker">
                <div className="text-center">
                    <p className="text-red-400 mb-4">Hata: {error}</p>
                    <button onClick={fetchData} className="px-4 py-2 bg-purple-600 rounded-lg text-white hover:bg-purple-500">
                        Tekrar Dene
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col bg-oracle-darker overflow-hidden">
            {/* Metric Selector */}
            <div className="shrink-0 p-4 border-b border-oracle-border bg-oracle-dark/50">
                <div className="flex items-center justify-between">
                    <div className="flex gap-2">
                        {(Object.keys(METRIC_CONFIG) as MetricType[]).map((metric) => {
                            const config = METRIC_CONFIG[metric];
                            const Icon = config.icon;
                            return (
                                <button
                                    key={metric}
                                    onClick={() => setSelectedMetric(metric)}
                                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${selectedMetric === metric
                                            ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50'
                                            : 'bg-oracle-card text-gray-400 border border-oracle-border hover:text-white hover:border-gray-600'
                                        }`}
                                >
                                    <Icon className="w-4 h-4" />
                                    <span>{config.label}</span>
                                </button>
                            );
                        })}
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={fetchData}
                            disabled={loading}
                            className="p-2 rounded-lg bg-oracle-card border border-oracle-border hover:border-gray-600 transition-colors"
                        >
                            <RefreshCw className={`w-4 h-4 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
                        </button>
                        <div className="flex bg-oracle-card rounded-lg border border-oracle-border p-1">
                            <button
                                onClick={() => setViewMode('grid')}
                                className={`px-3 py-1 rounded text-xs font-medium transition-all ${viewMode === 'grid' ? 'bg-purple-500/30 text-purple-400' : 'text-gray-400'
                                    }`}
                            >
                                Grid
                            </button>
                            <button
                                onClick={() => setViewMode('sector')}
                                className={`px-3 py-1 rounded text-xs font-medium transition-all ${viewMode === 'sector' ? 'bg-purple-500/30 text-purple-400' : 'text-gray-400'
                                    }`}
                            >
                                Sektör
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Heatmap Grid */}
            <div className="flex-1 overflow-auto p-4">
                {viewMode === 'grid' ? (
                    <div className="grid grid-cols-5 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-10 gap-2">
                        {sortedCoins.map((coin, index) => {
                            const field = METRIC_CONFIG[selectedMetric].field as keyof CoinData;
                            const value = Number(coin[field]) || 0;
                            const colorClass = getHeatmapColor(value, selectedMetric);
                            const size = index < 3 ? 'col-span-2 row-span-2' : index < 8 ? 'col-span-1 row-span-1' : '';

                            return (
                                <div
                                    key={coin.id}
                                    className={`${size} ${colorClass} rounded-lg p-3 cursor-pointer transition-all hover:scale-105 hover:shadow-xl hover:z-10 relative group`}
                                    onMouseEnter={() => setHoveredCoin(coin)}
                                    onMouseLeave={() => setHoveredCoin(null)}
                                >
                                    <div className="flex flex-col h-full justify-between">
                                        <div>
                                            <div className="text-white font-bold text-sm">{coin.symbol}</div>
                                            {index < 8 && (
                                                <div className="text-white/60 text-xs truncate">{coin.name}</div>
                                            )}
                                        </div>
                                        <div className="mt-auto">
                                            <div className={`text-lg font-bold ${selectedMetric === 'price'
                                                    ? value >= 0 ? 'text-white' : 'text-white'
                                                    : 'text-white'
                                                }`}>
                                                {formatValue(value, selectedMetric)}
                                            </div>
                                            {index < 3 && (
                                                <div className="text-white/50 text-xs">
                                                    {formatPrice(coin.price)}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Hover Tooltip */}
                                    {hoveredCoin?.id === coin.id && (
                                        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-3 bg-oracle-dark border border-oracle-border rounded-lg shadow-2xl pointer-events-none">
                                            <div className="text-white font-bold mb-1">{coin.name}</div>
                                            <div className="text-gray-400 text-xs mb-2">{coin.sector}</div>
                                            <div className="space-y-1 text-xs">
                                                <div className="flex justify-between">
                                                    <span className="text-gray-500">Fiyat:</span>
                                                    <span className="text-white">{formatPrice(coin.price)}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-500">Market Cap:</span>
                                                    <span className="text-white">{formatMarketCap(coin.market_cap)}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-500">24h:</span>
                                                    <span className={coin.price_change_24h >= 0 ? 'text-green-400' : 'text-red-400'}>
                                                        {coin.price_change_24h >= 0 ? '+' : ''}{coin.price_change_24h.toFixed(1)}%
                                                    </span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-500">Sosyal:</span>
                                                    <span className="text-purple-400">{Math.round(coin.social_score)}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-500">Dev:</span>
                                                    <span className="text-cyan-400">{Math.round(coin.developer_score)}</span>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <div className="space-y-4">
                        {data?.sectors && Object.entries(data.sectors).map(([sector, coins]) => (
                            <div key={sector} className="bg-oracle-card rounded-xl border border-oracle-border p-4">
                                <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                                    {sector}
                                </h3>
                                <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2">
                                    {coins.map((coin) => {
                                        const field = METRIC_CONFIG[selectedMetric].field as keyof CoinData;
                                        const value = Number(coin[field]) || 0;
                                        const colorClass = getHeatmapColor(value, selectedMetric);

                                        return (
                                            <div
                                                key={coin.id}
                                                className={`${colorClass} rounded-lg p-2 text-center cursor-pointer hover:scale-105 transition-transform`}
                                            >
                                                <div className="text-white font-bold text-sm">{coin.symbol}</div>
                                                <div className="text-white/80 text-xs">{formatValue(value, selectedMetric)}</div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Legend */}
            <div className="shrink-0 p-3 border-t border-oracle-border bg-oracle-dark/50">
                <div className="flex items-center justify-center gap-4 text-xs">
                    {selectedMetric === 'price' ? (
                        <>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 rounded bg-red-500"></div>
                                <span className="text-gray-400">{'< -5%'}</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 rounded bg-red-700"></div>
                                <span className="text-gray-400">-3% ~ -5%</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 rounded bg-gray-600"></div>
                                <span className="text-gray-400">~0%</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 rounded bg-green-700"></div>
                                <span className="text-gray-400">1% ~ 3%</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 rounded bg-green-500"></div>
                                <span className="text-gray-400">{'> +5%'}</span>
                            </div>
                        </>
                    ) : (
                        <>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 rounded bg-gray-700"></div>
                                <span className="text-gray-400">Düşük</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 rounded bg-cyan-700"></div>
                                <span className="text-gray-400">Orta</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 rounded bg-blue-600"></div>
                                <span className="text-gray-400">İyi</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 rounded bg-indigo-500"></div>
                                <span className="text-gray-400">Yüksek</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 rounded bg-purple-500"></div>
                                <span className="text-gray-400">Çok Yüksek</span>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
