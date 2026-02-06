'use client';

import { Liquidation } from '@/lib/api';
import { Droplets, TrendingDown, TrendingUp } from 'lucide-react';

interface LiquidationFeedProps {
    data: Liquidation[];
    isLoading: boolean;
}

export default function LiquidationFeed({ data, isLoading }: LiquidationFeedProps) {
    if (isLoading) {
        return (
            <div className="h-[300px] w-full bg-oracle-card/50 rounded-xl border border-oracle-border/50 animate-pulse"></div>
        );
    }

    return (
        <div className="bg-oracle-card rounded-xl border border-oracle-border overflow-hidden flex flex-col h-full">
            <div className="p-4 border-b border-oracle-border bg-oracle-dark/50 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Droplets className="w-4 h-4 text-red-500" />
                    <h3 className="font-semibold text-white">Rekt Feed (Liquidations)</h3>
                </div>
                <div className="px-2 py-0.5 rounded text-[10px] bg-red-500/20 text-red-400 border border-red-500/20">
                    Live
                </div>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-0">
                <div className="divide-y divide-oracle-border/50">
                    {data.map((item, index) => {
                        const isLongLiq = item.side === 'Long'; // Long liquidated = Price dropped

                        return (
                            <div key={`${item.symbol}-${item.timestamp}-${index}`} className="px-4 py-3 hover:bg-white/5 transition-colors flex items-center justify-between group">
                                <div className="flex items-center gap-3">
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${isLongLiq ? 'bg-red-500/10 text-red-500' : 'bg-green-500/10 text-green-500'}`}>
                                        {isLongLiq ? <TrendingDown className="w-4 h-4" /> : <TrendingUp className="w-4 h-4" />}
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <span className="font-bold text-white">{item.symbol}</span>
                                            <span className={`text-xs px-1.5 py-0.5 rounded ${isLongLiq ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
                                                {item.side} Liq
                                            </span>
                                        </div>
                                        <div className="text-xs text-gray-500 mt-0.5">
                                            @ ${item.price.toLocaleString()}
                                        </div>
                                    </div>
                                </div>

                                <div className="text-right">
                                    <div className="font-mono font-medium text-white">
                                        ${item.amount_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                                    </div>
                                    <div className="text-xs text-gray-500">
                                        {item.time_ago}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
            <div className="p-3 bg-oracle-dark/30 border-t border-oracle-border text-[10px] text-gray-500 text-center">
                Long Liquidated = Forced Sell • Short Liquidated = Forced Buy
            </div>
        </div>
    );
}
