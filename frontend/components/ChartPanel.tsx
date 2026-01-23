'use client';

import { useStore } from '@/store/useStore';
import { AdvancedRealTimeChart } from 'react-ts-tradingview-widgets';
import { BarChart3, Maximize2, Settings } from 'lucide-react';

export default function ChartPanel() {
    const { chartSymbol, selectedNews } = useStore();

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="p-4 border-b border-oracle-border flex items-center justify-between bg-oracle-dark/50">
                <div className="flex items-center gap-3">
                    <BarChart3 className="w-5 h-5 text-oracle-accent" />
                    <div>
                        <h2 className="font-semibold text-white">The Chart</h2>
                        <p className="text-xs text-gray-500">{chartSymbol}</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button className="p-2 rounded-lg hover:bg-oracle-card transition-colors" title="Settings">
                        <Settings className="w-4 h-4 text-gray-400" />
                    </button>
                    <button className="p-2 rounded-lg hover:bg-oracle-card transition-colors" title="Fullscreen">
                        <Maximize2 className="w-4 h-4 text-gray-400" />
                    </button>
                </div>
            </div>

            {/* Active Symbol Banner */}
            {selectedNews && (
                <div className="px-4 py-2 bg-oracle-accent/10 border-b border-oracle-accent/30 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-oracle-accent animate-pulse"></span>
                    <span className="text-sm text-oracle-accent font-medium">
                        Viewing: {selectedNews.symbol.split(':')[1]}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">
                        — {selectedNews.title.slice(0, 50)}...
                    </span>
                </div>
            )}

            {/* TradingView Chart */}
            <div className="flex-1 relative">
                <AdvancedRealTimeChart
                    symbol={chartSymbol}
                    theme="dark"
                    autosize
                    interval="D"
                    timezone="Etc/UTC"
                    style="1"
                    locale="en"
                    enable_publishing={false}
                    hide_top_toolbar={false}
                    hide_legend={false}
                    save_image={false}
                    container_id="tradingview_chart"
                    copyrightStyles={{
                        parent: {
                            display: 'none',
                        },
                    }}
                />
            </div>
        </div>
    );
}
