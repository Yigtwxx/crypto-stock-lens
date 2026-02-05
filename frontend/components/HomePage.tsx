'use client';

import { useEffect, useState } from 'react';
import { fetchFundingRates, fetchLiquidations, fetchOnChainData, FundingRate, Liquidation, OnChainData } from '@/lib/api';
import OnChainStats from './home/OnChainStats';
import FundingRates from './home/FundingRates';
import LiquidationFeed from './home/LiquidationFeed';
import { RefreshCw } from 'lucide-react';

export default function HomePage() {
    const [onChainData, setOnChainData] = useState<OnChainData | null>(null);
    const [fundingData, setFundingData] = useState<FundingRate[]>([]);
    const [liquidationData, setLiquidationData] = useState<Liquidation[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

    const loadData = async () => {
        setIsLoading(true);
        try {
            const [onChain, funding, liquidations] = await Promise.all([
                fetchOnChainData(),
                fetchFundingRates(),
                fetchLiquidations()
            ]);

            setOnChainData(onChain);
            setFundingData(funding);
            setLiquidationData(liquidations);
            setLastUpdated(new Date());
        } catch (error) {
            console.error("Failed to load home data", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadData();
        // Auto-refresh every 30 seconds
        const interval = setInterval(loadData, 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="h-full overflow-y-auto bg-oracle-darker p-6">
            <div className="max-w-[1600px] mx-auto space-y-6">

                {/* Header Section */}
                <div className="flex items-center justify-between mb-2">
                    <div>
                        <h2 className="text-2xl font-bold text-white tracking-tight">Market Intelligence</h2>
                        <p className="text-sm text-gray-500">Real-time on-chain data, funding rates, and liquidation events.</p>
                    </div>
                    <div className="flex items-center gap-3">
                        {lastUpdated && (
                            <span className="text-xs text-gray-600 font-mono hidden sm:inline-block">
                                Updated: {lastUpdated.toLocaleTimeString()}
                            </span>
                        )}
                        <button
                            onClick={loadData}
                            className="p-2 rounded-lg bg-oracle-card border border-oracle-border hover:bg-white/5 transition-colors group"
                            title="Refresh Data"
                        >
                            <RefreshCw className={`w-4 h-4 text-gray-400 group-hover:text-cyan group-hover:rotate-180 transition-all duration-500 ${isLoading ? 'animate-spin text-cyan' : ''}`} />
                        </button>
                    </div>
                </div>

                {/* 1. On-Chain Stats Row */}
                <OnChainStats data={onChainData} isLoading={isLoading} />

                {/* 2. Split View: Funding & Liquidations */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[600px]">
                    <FundingRates data={fundingData} isLoading={isLoading} />
                    <LiquidationFeed data={liquidationData} isLoading={isLoading} />
                </div>

            </div>
        </div>
    );
}
