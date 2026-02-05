'use client';

import { useEffect, useState } from 'react';
import { fetchFundingRates, fetchLiquidations, fetchOnChainData, fetchMacroCalendar, FundingRate, Liquidation, OnChainData, MacroEvent } from '@/lib/api';
import OnChainStats from './home/OnChainStats';
import FundingRates from './home/FundingRates';
import LiquidationFeed from './home/LiquidationFeed';
import MacroCalendar from './home/MacroCalendar';
import WatchlistWidget from './home/WatchlistWidget';
import { RefreshCw } from 'lucide-react';

export default function HomePage() {
    const [onChainData, setOnChainData] = useState<OnChainData | null>(null);
    const [fundingData, setFundingData] = useState<FundingRate[]>([]);
    const [liquidationData, setLiquidationData] = useState<Liquidation[]>([]);
    const [macroEvents, setMacroEvents] = useState<MacroEvent[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [lastUpdated, setLastUpdated] = useState<string | null>(null);

    const loadData = async () => {
        setIsLoading(true);
        try {
            const [onChain, funding, liquidations, macro] = await Promise.all([
                fetchOnChainData(),
                fetchFundingRates(),
                fetchLiquidations(),
                fetchMacroCalendar()
            ]);
            setOnChainData(onChain);
            setFundingData(funding);
            setLiquidationData(liquidations);
            setMacroEvents(macro);
            setLastUpdated(new Date().toLocaleTimeString());
        } catch (error) {
            console.error("Failed to fetch home data", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadData();
        // Set initial timestamp on client only to avoid hydration mismatch
        setLastUpdated(new Date().toLocaleTimeString());
    }, []);

    return (
        <div className="h-full overflow-y-auto bg-oracle-darker p-6">
            <div className="max-w-[1600px] mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-white">Market Intelligence</h1>
                        <p className="text-gray-400 text-sm mt-1">Real-time on-chain data, funding rates, and macroeconomic events.</p>
                    </div>
                    <div className="flex items-center gap-4">
                        {lastUpdated && (
                            <span className="text-xs text-gray-500 font-mono">Updated: {lastUpdated}</span>
                        )}
                        <button
                            onClick={loadData}
                            className={`p-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors border border-white/5 ${isLoading ? 'animate-spin' : ''}`}
                        >
                            <RefreshCw className="w-4 h-4 text-gray-400" />
                        </button>
                    </div>
                </div>

                {/* Top Row: On-Chain Stats */}
                <OnChainStats data={onChainData} isLoading={isLoading} />

                {/* Middle Row: 3-Column Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[500px]">
                    {/* Col 1: Funding Rates */}
                    <FundingRates data={fundingData} isLoading={isLoading} />

                    {/* Col 2: Liquidations */}
                    <LiquidationFeed data={liquidationData} isLoading={isLoading} />

                    {/* Col 3: Macro Calendar */}
                    <MacroCalendar data={macroEvents} isLoading={isLoading} />
                </div>

                {/* Bottom Row: Watchlist */}
                <WatchlistWidget />
            </div>
        </div>
    );
}
