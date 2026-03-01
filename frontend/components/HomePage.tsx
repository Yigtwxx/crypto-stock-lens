'use client';

import { useOnChainData, useFundingRates, useLiquidations, useMacroCalendar } from '@/hooks/queries';
import OnChainStats from './home/OnChainStats';
import FundingRates from './home/FundingRates';
import LiquidationFeed from './home/LiquidationFeed';
import MacroCalendar from './home/MacroCalendar';
import WatchlistWidget from './home/WatchlistWidget';
import { RefreshCw } from 'lucide-react';

export default function HomePage() {
    const onChain = useOnChainData();
    const funding = useFundingRates();
    const liquidations = useLiquidations();
    const macro = useMacroCalendar();

    const isLoading = onChain.isLoading || funding.isLoading || liquidations.isLoading || macro.isLoading;
    const isFetching = onChain.isFetching || funding.isFetching || liquidations.isFetching || macro.isFetching;

    const handleRefresh = () => {
        onChain.refetch();
        funding.refetch();
        liquidations.refetch();
        macro.refetch();
    };

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
                        {onChain.dataUpdatedAt > 0 && (
                            <span className="text-xs text-gray-500 font-mono">
                                Updated: {new Date(onChain.dataUpdatedAt).toLocaleTimeString()}
                            </span>
                        )}
                        <button
                            onClick={handleRefresh}
                            className="p-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors border border-white/5"
                        >
                            <RefreshCw className={`w-4 h-4 text-gray-400 ${isFetching ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                </div>

                {/* Top Row: On-Chain Stats */}
                <OnChainStats data={onChain.data ?? null} isLoading={isLoading} />

                {/* Middle Row: 3-Column Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[500px]">
                    {/* Col 1: Funding Rates */}
                    <FundingRates data={funding.data ?? []} isLoading={isLoading} />

                    {/* Col 2: Liquidations */}
                    <LiquidationFeed data={liquidations.data ?? []} isLoading={isLoading} />

                    {/* Col 3: Macro Calendar */}
                    <MacroCalendar data={macro.data ?? []} isLoading={isLoading} />
                </div>

                {/* Bottom Row: Watchlist */}
                <WatchlistWidget />
            </div>
        </div>
    );
}
