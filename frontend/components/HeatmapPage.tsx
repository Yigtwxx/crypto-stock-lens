'use client';

import { useState } from 'react';
import HeatmapWidget from './overview/HeatmapWidget';
import AdvancedHeatmap from './overview/AdvancedHeatmap';
import { Bitcoin, LineChart, Layers, Sparkles } from 'lucide-react';

export default function HeatmapPage() {
    const [marketType, setMarketType] = useState<'advanced' | 'crypto' | 'nasdaq' | 'liquidation'>('advanced');

    return (
        <div className="h-full flex flex-col bg-oracle-darker">
            {/* Toolbar */}
            <div className="h-14 border-b border-oracle-border flex items-center px-6 gap-4 bg-oracle-dark/50">
                <h2 className="text-lg font-semibold text-white mr-4">Market Heatmap</h2>

                <div className="flex bg-oracle-dark rounded-lg p-1 border border-oracle-border">
                    <button
                        onClick={() => setMarketType('advanced')}
                        className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${marketType === 'advanced'
                            ? 'bg-purple-500/20 text-purple-400 shadow-sm'
                            : 'text-gray-400 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        <Sparkles className="w-4 h-4" />
                        <span>Gelişmiş</span>
                    </button>
                    <button
                        onClick={() => setMarketType('crypto')}
                        className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${marketType === 'crypto'
                            ? 'bg-indigo-500/20 text-indigo-400 shadow-sm'
                            : 'text-gray-400 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        <Bitcoin className="w-4 h-4" />
                        <span>Crypto</span>
                    </button>
                    <button
                        onClick={() => setMarketType('nasdaq')}
                        className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${marketType === 'nasdaq'
                            ? 'bg-cyan/20 text-cyan shadow-sm'
                            : 'text-gray-400 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        <LineChart className="w-4 h-4" />
                        <span>Nasdaq</span>
                    </button>
                    <button
                        onClick={() => setMarketType('liquidation')}
                        className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${marketType === 'liquidation'
                            ? 'bg-red-500/20 text-red-400 shadow-sm'
                            : 'text-gray-400 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        <Layers className="w-4 h-4" />
                        <span>Likidasyon</span>
                    </button>
                </div>
            </div>

            {/* Heatmap Content */}
            <div className="flex-1 overflow-hidden">
                {marketType === 'advanced' ? (
                    <AdvancedHeatmap />
                ) : (
                    <div className="p-4 h-full">
                        <HeatmapWidget marketType={marketType} className="h-full w-full" />
                    </div>
                )}
            </div>
        </div>
    );
}

