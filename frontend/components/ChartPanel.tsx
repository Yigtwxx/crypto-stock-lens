'use client';

import { useStore } from '@/store/useStore';
import { AdvancedRealTimeChart } from 'react-ts-tradingview-widgets';
import { BarChart3, Maximize2, Settings, Bell } from 'lucide-react';

export default function ChartPanel() {
    const { chartSymbol, selectedNews, toggleAlertModal, priceAlerts } = useStore();

    const activeAlertsCount = priceAlerts.filter(a => a.isActive && a.symbol === chartSymbol).length;

    return (
        <div className="flex flex-col h-full">
            {/* Header - Fixed height to align with other panels */}
            <div className="h-14 px-4 border-b border-oracle-border flex items-center justify-between bg-gradient-to-r from-oracle-dark via-oracle-dark to-teal/5">
                <div className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-teal" />
                    <h2 className="font-semibold bg-gradient-to-r from-white to-teal bg-clip-text text-transparent">The Chart</h2>
                    <span className="text-xs text-gray-500 ml-1">{chartSymbol.split(':')[1] || chartSymbol}</span>
                </div>
                <div className="flex items-center gap-1">
                    {/* Alert Button */}
                    <button
                        onClick={() => toggleAlertModal(true)}
                        className="p-2 rounded-lg hover:bg-amber-500/10 transition-colors relative"
                        title="Set Price Alert"
                    >
                        <Bell className="w-4 h-4 text-gray-400 hover:text-amber-400" />
                        {activeAlertsCount > 0 && (
                            <span className="absolute -top-1 -right-1 w-4 h-4 bg-amber-500 rounded-full text-[10px] font-bold text-black flex items-center justify-center">
                                {activeAlertsCount}
                            </span>
                        )}
                    </button>
                    <button className="p-2 rounded-lg hover:bg-teal/10 transition-colors" title="Settings">
                        <Settings className="w-4 h-4 text-gray-400 hover:text-teal" />
                    </button>
                    <button className="p-2 rounded-lg hover:bg-teal/10 transition-colors" title="Fullscreen">
                        <Maximize2 className="w-4 h-4 text-gray-400 hover:text-teal" />
                    </button>
                </div>
            </div>

            {/* Active Symbol Banner */}
            {selectedNews && (
                <div className={`px-4 py-2 border-b flex items-center gap-2 ${selectedNews.asset_type === 'crypto'
                    ? 'bg-crypto/10 border-crypto/30'
                    : 'bg-stock/10 border-stock/30'
                    }`}>
                    <span className={`w-2 h-2 rounded-full animate-pulse ${selectedNews.asset_type === 'crypto' ? 'bg-crypto' : 'bg-stock'
                        }`}></span>
                    <span className={`text-sm font-medium ${selectedNews.asset_type === 'crypto' ? 'text-crypto' : 'text-stock'
                        }`}>
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
                    key={chartSymbol}
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
                    container_id={`tradingview_${chartSymbol.replace(':', '_')}`}
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
