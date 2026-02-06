'use client';

import { CryptoCoinsHeatmap, StockHeatmap } from 'react-ts-tradingview-widgets';
import { Layers } from 'lucide-react';

import LiquidationChart from '../charts/LiquidationChart';

interface HeatmapWidgetProps {
    marketType?: 'crypto' | 'nasdaq' | 'liquidation';
    className?: string;
}

export default function HeatmapWidget({ marketType = 'crypto', className = '' }: HeatmapWidgetProps) {
    const getTitle = () => {
        switch (marketType) {
            case 'nasdaq': return 'Nasdaq Heatmap';
            case 'liquidation': return 'Liquidation Heatmap';
            default: return 'Crypto Heatmap';
        }
    };

    return (
        <div className={`flex flex-col h-full bg-gradient-to-br from-oracle-card to-purple-900/10 border border-oracle-border rounded-xl p-4 overflow-hidden ${className}`}>
            <div className="flex items-center gap-2 mb-3 shrink-0">
                <Layers className="w-4 h-4 text-indigo-400" />
                <h3 className="font-semibold text-white text-sm">
                    {getTitle()}
                </h3>
            </div>

            <div className="relative flex-1 min-h-[150px] w-full rounded-lg overflow-hidden border border-white/5 bg-[#0b0b15]">
                {marketType === 'crypto' && (
                    <CryptoCoinsHeatmap
                        colorTheme="dark"
                        width="100%"
                        height="100%"
                        locale="en"
                    />
                )}
                {marketType === 'nasdaq' && (
                    <StockHeatmap
                        colorTheme="dark"
                        width="100%"
                        height="100%"
                        exchanges={["NASDAQ"]}
                        locale="en"
                        dataSource="SPX500"
                    />
                )}
                {marketType === 'liquidation' && (
                    <LiquidationChart />
                )}
            </div>
        </div>
    );
}
