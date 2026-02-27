'use client';

import React, { useEffect, useState, useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { RefreshCw } from 'lucide-react';
import { useStore } from '@/store/useStore';
import { API_BASE_URL } from '@/lib/api';

interface Candle {
    time: number; // Unix timestamp in seconds
    open: number;
    high: number;
    low: number;
    close: number;
}

interface LiquidationEvent {
    price: number;
    amount_usd: number;
    side: 'SELL' | 'BUY';
    timestamp: number; // ms
}

export default function LiquidationEChart() {
    const { chartSymbol } = useStore();
    const [candles, setCandles] = useState<Candle[]>([]);
    const [liquidations, setLiquidations] = useState<LiquidationEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

    const fetchData = async (isInitial = false) => {
        if (isInitial) setLoading(true);
        else setRefreshing(true);

        try {
            const cleanSymbol = chartSymbol.split(':').pop() || chartSymbol;

            // Fetch Candles
            const candleRes = await fetch(`${API_BASE_URL}/api/market/candles/${cleanSymbol}?interval=1h&limit=168`);
            if (candleRes.ok) {
                const candleData = await candleRes.json();
                setCandles(candleData);
            }

            // Fetch Liquidations
            const liqRes = await fetch(`${API_BASE_URL}/api/liquidations/history/${cleanSymbol}`);
            if (liqRes.ok) {
                const liqData = await liqRes.json();
                setLiquidations(liqData);
            }

            setLastUpdated(new Date());
        } catch (error) {
            console.error("Failed to load chart data:", error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchData(true);
        // Refresh every 30 seconds
        const interval = setInterval(() => fetchData(false), 30000);
        return () => clearInterval(interval);
    }, [chartSymbol]);

    // Build ECharts Options safely
    const option = useMemo(() => {
        if (!candles.length) return {};

        // Format Candles for ECharts: [timestamp_ms, open, close, low, high]
        const formattedCandles = candles.map(c => [
            c.time * 1000,
            c.open,
            c.close,
            c.low,
            c.high
        ]);

        // Format Liquidations for Scatter: [timestamp_ms, price, amount_usd, side]
        // Filter out extreme outliers just in case, but usually binance force orders are fine
        const formattedLiquidations = liquidations.map(l => [
            l.timestamp,
            l.price,
            l.amount_usd,
            l.side
        ]);

        const maxLiqVolume = liquidations.length > 0
            ? Math.max(...liquidations.map(l => l.amount_usd))
            : 10000;

        return {
            backgroundColor: 'transparent',
            animation: false,
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross',
                    label: {
                        backgroundColor: '#2A2E39'
                    }
                },
                backgroundColor: 'rgba(26, 26, 46, 0.9)',
                borderColor: '#6b21a8',
                textStyle: { color: '#E5E7EB' },
                formatter: function (params: any) {
                    let result = '';
                    params.forEach((param: any) => {
                        if (param.seriesType === 'candlestick') {
                            const date = new Date(param.value[0]);
                            result += `<div className="font-semibold text-purple-400 mb-1">${date.toLocaleString()}</div>`;
                            result += `<div>Open: <span class="font-mono text-gray-300">$${param.value[1]}</span></div>`;
                            result += `<div>Close: <span class="font-mono text-gray-300">$${param.value[2]}</span></div>`;
                            result += `<div>Low: <span class="font-mono text-gray-300">$${param.value[3]}</span></div>`;
                            result += `<div>High: <span class="font-mono text-gray-300">$${param.value[4]}</span></div><br/>`;
                        } else if (param.seriesType === 'scatter') {
                            const liqAmount = param.value[2];
                            const side = param.value[3] === 'SELL' ? 'Long Liq' : 'Short Liq';
                            const color = param.value[3] === 'SELL' ? '#ef4444' : '#22c55e';
                            if (liqAmount > 0) {
                                result += `<div style="color:${color}; font-weight:bold;">${side} @ $${param.value[1]}</div>`;
                                result += `<div>Vol: <span class="font-mono">$${liqAmount.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span></div>`;
                            }
                        }
                    });
                    return result;
                }
            },
            grid: {
                left: '2%',
                right: '4%',
                bottom: '3%',
                top: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'time',
                axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } },
                splitLine: { show: true, lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } },
                axisLabel: { color: '#9ca3af' }
            },
            yAxis: {
                type: 'value',
                scale: true,
                position: 'right',
                axisLine: { show: false },
                splitLine: { show: true, lineStyle: { color: 'rgba(255, 255, 255, 0.03)' } },
                axisLabel: { color: '#9ca3af' }
            },
            dataZoom: [
                { type: 'inside', xAxisIndex: [0, 1] },
                { type: 'inside', yAxisIndex: [0, 1] }
            ],
            visualMap: {
                show: false,
                seriesIndex: 1, // Apply to the scatter series only
                dimension: 2,   // The 3rd array element (amount_usd)
                min: 0,
                max: maxLiqVolume,
                inRange: {
                    // Coinglass style glow: Deep Purple -> Cyan -> Yellow
                    color: [
                        'rgba(61, 12, 116, 0.3)',
                        'rgba(0, 206, 209, 0.7)',
                        'rgba(252, 255, 0, 1)'
                    ],
                    symbolSize: [5, 40] // Smaller bubbles for less liq, huge for massive liq
                }
            },
            series: [
                {
                    name: 'Price',
                    type: 'candlestick',
                    data: formattedCandles,
                    itemStyle: {
                        color: 'rgba(34, 197, 94, 0.8)',
                        color0: 'rgba(239, 68, 68, 0.8)',
                        borderColor: 'rgba(34, 197, 94, 1)',
                        borderColor0: 'rgba(239, 68, 68, 1)'
                    },
                    zlevel: 1
                },
                {
                    name: 'Liquidations',
                    type: 'scatter',
                    symbol: 'circle',
                    data: formattedLiquidations,
                    itemStyle: {
                        // Inherits color from visualMap, but we can add shadow
                        shadowBlur: 15,
                        shadowColor: 'rgba(252, 255, 0, 0.5)'
                    },
                    zlevel: 2
                }
            ]
        };
    }, [candles, liquidations]);

    return (
        <div className="flex flex-col w-full h-full bg-[#0a0a14]">
            {/* Header */}
            <div className="shrink-0 flex items-center justify-between px-4 py-2 border-b border-purple-900/30 bg-[#0d0d1a]">
                <div className="flex items-center gap-3">
                    <span className="text-xs font-semibold text-purple-400">Real-Time Liquidations</span>
                    <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-white/5 text-gray-300">
                        {chartSymbol.split(':').pop()}
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    {lastUpdated && (
                        <span className="text-[10px] text-gray-500 font-mono">
                            {lastUpdated.toLocaleTimeString('tr-TR')}
                        </span>
                    )}
                    <button
                        onClick={() => fetchData(false)}
                        disabled={refreshing || loading}
                        className={`
                            flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                            bg-[#1a1a2e] border border-purple-900/50
                            text-xs font-medium transition-all
                            ${refreshing || loading
                                ? 'opacity-50 cursor-not-allowed text-gray-500'
                                : 'hover:bg-purple-900/30 hover:border-purple-600/50 text-gray-300 hover:text-white'
                            }
                        `}
                        title="Verileri yenile"
                    >
                        <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
                        <span>{refreshing ? 'Yenileniyor...' : 'Yenile'}</span>
                    </button>
                </div>
            </div>

            {/* Chart Container */}
            <div className="relative flex-1 min-h-0 w-full">
                {loading ? (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm z-20">
                        <div className="flex flex-col items-center gap-3">
                            <RefreshCw className="w-8 h-8 animate-spin text-purple-400" />
                            <span className="text-sm text-gray-400">Loading chart data...</span>
                        </div>
                    </div>
                ) : (
                    <ReactECharts
                        option={option}
                        style={{ height: '100%', width: '100%' }}
                        opts={{ renderer: 'canvas' }}
                        notMerge={true}
                        lazyUpdate={true}
                    />
                )}
            </div>
        </div>
    );
}
