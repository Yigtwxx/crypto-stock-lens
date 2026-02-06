'use client';

import { CryptoCoinsHeatmap, StockHeatmap } from 'react-ts-tradingview-widgets';
import { Layers } from 'lucide-react';

interface HeatmapWidgetProps {
    marketType?: 'crypto' | 'nasdaq';
    className?: string;
}

export default function HeatmapWidget({ marketType = 'crypto', className = '' }: HeatmapWidgetProps) {
    return (
        <div className={`flex flex-col h-full bg-gradient-to-br from-oracle-card to-purple-900/10 border border-oracle-border rounded-xl p-4 overflow-hidden ${className}`}>
            <div className="flex items-center gap-2 mb-3 shrink-0">
                <Layers className="w-4 h-4 text-indigo-400" />
                <h3 className="font-semibold text-white text-sm">
                    {marketType === 'crypto' ? 'Crypto Heatmap' : 'Nasdaq Heatmap'}
                </h3>
            </div>

            <div className="relative flex-1 min-h-[150px] w-full rounded-lg overflow-hidden border border-white/5">
                {marketType === 'crypto' ? (
                    // @ts-ignore - Library types might be missing for specific widgets
                    <CryptoCoinsHeatmap
                        colorTheme="dark"
                        width="100%"
                        height="100%"
                        locale="en"
                    />
                ) : (
                    // @ts-ignore
                    <StockHeatmap
                        colorTheme="dark"
                        width="100%"
                        height="100%"
                        exchanges={["NASDAQ"]}
                        locale="en"
                        dataSource="SPX500"
                    />
                )}
            </div>
        </div>
    );
}
