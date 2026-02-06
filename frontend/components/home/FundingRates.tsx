'use client';

import { FundingRate } from '@/lib/api';
import { Flame, Clock } from 'lucide-react';

interface FundingRatesProps {
    data: FundingRate[];
    isLoading: boolean;
}

export default function FundingRates({ data, isLoading }: FundingRatesProps) {
    if (isLoading) {
        return (
            <div className="h-[300px] w-full bg-oracle-card/50 rounded-xl border border-oracle-border/50 animate-pulse"></div>
        );
    }

    return (
        <div className="bg-oracle-card rounded-xl border border-oracle-border overflow-hidden flex flex-col h-full">
            <div className="p-4 border-b border-oracle-border bg-oracle-dark/50 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Flame className="w-4 h-4 text-orange-400" />
                    <h3 className="font-semibold text-white">Funding Rates (Real-time)</h3>
                </div>
                <div className="text-xs text-gray-500 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    Next funding in: 4h 12m
                </div>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar">
                <table className="w-full text-sm">
                    <thead className="bg-oracle-dark/30 text-xs text-gray-500 sticky top-0 backdrop-blur-sm z-10">
                        <tr>
                            <th className="px-4 py-3 text-left font-medium">Symbol</th>
                            <th className="px-4 py-3 text-right font-medium">Rate (8h)</th>
                            <th className="px-4 py-3 text-right font-medium">APR</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-oracle-border/50">
                        {data.map((item) => {
                            const isPositive = item.rate > 0;
                            const intensity = Math.min(Math.abs(item.rate) * 5000, 100); // Visual intensity

                            return (
                                <tr key={item.symbol} className="hover:bg-white/5 transition-colors">
                                    <td className="px-4 py-3 font-medium text-white">{item.symbol}</td>
                                    <td className="px-4 py-3 text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <span className={`${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                                                {item.rate_formatted}
                                            </span>
                                            {/* Heatmap-like bar */}
                                            <div className="w-16 h-1 bg-gray-800 rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full ${isPositive ? 'bg-green-500' : 'bg-red-500'}`}
                                                    style={{ width: `${intensity}%`, marginLeft: isPositive ? '0' : 'auto' }}
                                                />
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-right text-gray-400">
                                        {(item.rate * 3 * 365 * 100).toFixed(2)}%
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            <div className="p-3 bg-oracle-dark/30 border-t border-oracle-border text-[10px] text-gray-500 text-center">
                Positive rate: Longs pay Shorts (Bullish sentiment)
            </div>
        </div>
    );
}
