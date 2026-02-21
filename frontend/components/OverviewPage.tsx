'use client';

import { useEffect, useState, useMemo } from 'react';
import { fetchFearGreedIndex, fetchMarketOverview, FearGreedData, MarketOverview, API_BASE_URL } from '@/lib/api';
import FearGreedGauge from './FearGreedGauge';
import { TrendingUp, TrendingDown, Activity, Flame } from 'lucide-react';
import MarketStatsBar from './overview/MarketStatsBar';
import AssetListCard from './overview/AssetListCard';
import AssetTable from './overview/AssetTable';
import BottomStatsGrid from './overview/BottomStatsGrid';

export default function OverviewPage({ marketType = 'crypto' }: { marketType?: 'crypto' | 'nasdaq' }) {
    const [fearGreedData, setFearGreedData] = useState<FearGreedData | null>(null);
    const [marketData, setMarketData] = useState<MarketOverview | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

    const fetchData = async () => {
        setIsLoading(true);
        try {
            if (marketType === 'nasdaq') {
                // Fetch NASDAQ data (includes Fear & Greed)
                const response = await fetch(`${API_BASE_URL}/api/nasdaq-overview`);
                const nasdaqData = await response.json();

                // Set market data
                setMarketData(nasdaqData);

                // Set Fear & Greed from NASDAQ response
                if (nasdaqData.fear_greed) {
                    setFearGreedData({
                        value: nasdaqData.fear_greed.value,
                        classification: nasdaqData.fear_greed.classification,
                        timestamp: nasdaqData.fear_greed.timestamp,
                        history: []
                    });
                }
            } else {
                // Fetch Crypto data
                const [fgData, mktData] = await Promise.all([
                    fetchFearGreedIndex(),
                    fetchMarketOverview()
                ]);
                setFearGreedData(fgData);
                setMarketData(mktData);
            }
            setLastUpdate(new Date());
        } catch (error) {
            console.error('Failed to fetch overview data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 120000);
        return () => clearInterval(interval);
    }, [marketType]);

    // Derived data for trending, gainers, losers
    const { topGainers, topLosers } = useMemo(() => {
        if (!marketData?.coins) return { topGainers: [], topLosers: [] };
        const sorted = [...marketData.coins].sort((a, b) => b.change_24h - a.change_24h);
        return {
            topGainers: sorted.slice(0, 3), // Top 3 best performers
            topLosers: sorted.slice(-3).reverse() // Bottom 3 worst performers
        };
    }, [marketData]);

    return (
        <div className="h-full overflow-y-auto bg-oracle-darker">
            {/* ===== TOP MARKET STATS BAR ===== */}
            <MarketStatsBar
                marketData={marketData}
                fearGreedData={fearGreedData}
                marketType={marketType}
                isLoading={isLoading}
                lastUpdate={lastUpdate}
                onRefresh={fetchData}
            />

            <div className="max-w-[1800px] mx-auto px-4 py-6 space-y-6">
                {/* ===== TRENDING / GAINERS / LOSERS CARDS ===== */}
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                    {/* Fear & Greed Card */}
                    <div className="lg:col-span-1 p-4 rounded-xl bg-gradient-to-br from-oracle-card to-pink/5 border border-oracle-border">
                        <div className="flex items-center gap-2 mb-3">
                            <Activity className="w-4 h-4 text-pink" />
                            <h3 className="font-semibold text-white text-sm">Fear & Greed Index</h3>
                        </div>
                        <FearGreedGauge data={fearGreedData} isLoading={isLoading} size="sm" />
                    </div>

                    {/* Trending Card */}
                    <AssetListCard
                        title="🔥 Trending"
                        icon={Flame}
                        iconColor="text-orange-400"
                        data={marketData?.coins.slice(0, 3) || []}
                        isLoading={isLoading}
                        marketType={marketType}
                        type="trending"
                    />

                    {/* Top Gainers Card */}
                    <AssetListCard
                        title="📈 Top Gainers"
                        icon={TrendingUp}
                        iconColor="text-green-400"
                        data={topGainers}
                        isLoading={isLoading}
                        marketType={marketType}
                        type="gainer"
                    />

                    {/* Top Losers Card */}
                    <AssetListCard
                        title="📉 Top Losers"
                        icon={TrendingDown}
                        iconColor="text-red-400"
                        data={topLosers}
                        isLoading={isLoading}
                        marketType={marketType}
                        type="loser"
                    />
                </div>

                {/* ===== ASSET TABLE ===== */}
                <AssetTable
                    marketData={marketData}
                    marketType={marketType}
                    isLoading={isLoading}
                />

                {/* ===== BOTTOM STATS ===== */}
                <BottomStatsGrid
                    marketData={marketData}
                    marketType={marketType}
                />
            </div>
        </div>
    );
}
