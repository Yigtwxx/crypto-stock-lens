'use client';

import { Coins, Globe, ArrowUp, ArrowDown } from 'lucide-react';
import { MarketOverview } from '@/lib/api';
import SparklineChart from './SparklineChart';
import {
    getAssetLogo,
    getAssetName,
    formatPrice,
    formatVolume,
    generateSparkline,
    getSeeded7dChange
} from './overview-utils';

interface AssetTableProps {
    marketData: MarketOverview | null;
    marketType: 'crypto' | 'nasdaq';
    isLoading: boolean;
}

export default function AssetTable({ marketData, marketType, isLoading }: AssetTableProps) {
    return (
        <div className="rounded-xl bg-oracle-card border border-oracle-border overflow-hidden">
            <div className="px-4 py-3 border-b border-oracle-border flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Coins className="w-5 h-5 text-cyan" />
                    <h2 className="font-semibold text-white">
                        {marketType === 'nasdaq' ? 'Hisse Senedi Listesi' : 'Kripto Para Listesi'}
                    </h2>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Globe className="w-3.5 h-3.5" />
                    <span>{marketData?.active_cryptocurrencies?.toLocaleString() || '--'} {marketType === 'nasdaq' ? 'aktif hisse' : 'aktif kripto'}</span>
                </div>
            </div>

            {/* Table Header */}
            <div className="grid grid-cols-[40px_1fr_120px_100px_100px_130px_130px_110px] gap-2 px-4 py-2 text-xs text-gray-400 border-b border-oracle-border bg-oracle-dark/50">
                <div className="text-center">#</div>
                <div>Name</div>
                <div className="text-right">Price</div>
                <div className="text-right">24h %</div>
                <div className="text-right">7d %</div>
                <div className="text-right">Market Cap</div>
                <div className="text-right">Volume (24h)</div>
                <div className="text-right">Last 7 Days</div>
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
                        const sparklineData = generateSparkline(coin.change_24h, coin.symbol);
                        const change7d = getSeeded7dChange(coin.change_24h, coin.symbol);

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
                                        src={getAssetLogo(coin.symbol, coin.logo, marketType)}
                                        alt={coin.symbol}
                                        className="w-8 h-8 rounded-full object-cover bg-oracle-border"
                                        onError={(e) => { e.currentTarget.src = `https://ui-avatars.com/api/?name=${coin.symbol}&background=4f46e5&color=fff&size=64&bold=true`; }}
                                    />
                                    <div>
                                        <p className="font-medium text-white group-hover:text-cyan transition-colors">
                                            {getAssetName(coin.symbol, coin.name, marketType)}
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
                                    {formatVolume(coin.market_cap)}
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
    );
}
