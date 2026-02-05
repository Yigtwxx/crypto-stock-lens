'use client';

import { ChevronRight, LucideIcon, ArrowUp, ArrowDown } from 'lucide-react';
import { getAssetLogo } from './overview-utils';

interface AssetListCardProps {
    title: string;
    icon: LucideIcon;
    iconColor: string;
    data: any[];
    isLoading: boolean;
    marketType: 'crypto' | 'nasdaq';
    type: 'trending' | 'gainer' | 'loser';
}

export default function AssetListCard({
    title,
    icon: Icon,
    iconColor,
    data,
    isLoading,
    marketType,
    type
}: AssetListCardProps) {
    return (
        <div className={`p-4 rounded-xl border border-oracle-border bg-gradient-to-br from-oracle-card ${type === 'trending' ? 'to-violet/5' : type === 'gainer' ? 'to-green-500/5' : 'to-red-500/5'}`}>
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <Icon className={`w-4 h-4 ${iconColor}`} />
                    <h3 className="font-semibold text-white text-sm">{title}</h3>
                </div>
                <ChevronRight className="w-4 h-4 text-gray-500" />
            </div>
            <div className="space-y-2">
                {(isLoading ? [1, 2, 3] : data).map((coin, i) => (
                    typeof coin === 'number' ? (
                        <div key={i} className="flex items-center gap-2 animate-pulse">
                            <div className="w-6 h-6 rounded-full bg-oracle-border" />
                            <div className="flex-1 h-4 bg-oracle-border rounded" />
                        </div>
                    ) : (
                        <div key={coin.symbol} className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                {type === 'trending' && <span className="text-xs text-gray-500">{i + 1}</span>}
                                <img
                                    src={getAssetLogo(coin.symbol, coin.logo, marketType)}
                                    alt={coin.symbol}
                                    className="w-5 h-5 rounded-full object-cover bg-oracle-border"
                                    onError={(e) => {
                                        const color = type === 'gainer' ? '22c55e' : type === 'loser' ? 'ef4444' : '6b21a8';
                                        e.currentTarget.src = `https://ui-avatars.com/api/?name=${coin.symbol}&background=${color}&color=fff&size=40&bold=true`;
                                    }}
                                />
                                <span className="text-sm text-white">{coin.symbol}</span>
                            </div>
                            <span className={`text-xs font-medium ${type === 'gainer' ? 'px-2 py-0.5 rounded-full bg-green-500/20 text-green-400' : type === 'loser' ? 'px-2 py-0.5 rounded-full bg-red-500/20 text-red-400' : coin.change_24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {type === 'trending' && (coin.change_24h >= 0 ? '+' : '')}
                                {type !== 'trending' && (coin.change_24h >= 0 ? '+' : '')}
                                {coin.change_24h.toFixed(1)}%
                            </span>
                        </div>
                    )
                ))}
            </div>
        </div>
    );
}
