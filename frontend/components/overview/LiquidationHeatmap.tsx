'use client';

import React, { useEffect, useState } from 'react';
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';
import { RefreshCw } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api';

interface LiquidationData {
    symbol: string;
    value: number;       // total_usd
    long_liq: number;
    short_liq: number;
    count: number;
}

const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
        const data = payload[0].payload;
        return (
            <div className="bg-oracle-card border border-oracle-border p-3 rounded-lg shadow-xl backdrop-blur-md">
                <p className="font-bold text-white mb-1">{data.symbol}</p>
                <p className="text-gray-300 text-sm">
                    Total: <span className="text-white font-mono">${data.value.toLocaleString()}</span>
                </p>
                <div className="my-1 h-px bg-white/10" />
                <p className="text-red-400 text-sm">
                    Longs: ${data.long_liq.toLocaleString()}
                </p>
                <p className="text-green-400 text-sm">
                    Shorts: ${data.short_liq.toLocaleString()}
                </p>
                <p className="text-xs text-gray-500 mt-1">{data.count} events</p>
            </div>
        );
    }
    return null;
};

const CustomContent = (props: any) => {
    const { root, depth, x, y, width, height, index, colors, name, value, long_liq, short_liq } = props;

    // Determine color based on dominant side
    // Longs > Shorts -> Red (Sell pressure)
    // Shorts > Longs -> Green (Buy pressure)
    const isLongDominant = long_liq > short_liq;

    // Calculate intensity (e.g. 60% vs 90% dominance)
    // const total = long_liq + short_liq;
    // const ratio = total > 0 ? (isLongDominant ? long_liq : short_liq) / total : 0;

    // Base colors
    const startColor = isLongDominant ? '#ef4444' : '#22c55e'; // red-500 : green-500

    return (
        <g>
            <rect
                x={x}
                y={y}
                width={width}
                height={height}
                style={{
                    fill: startColor,
                    stroke: '#1e293b', // slate-800
                    strokeWidth: 1,
                    strokeOpacity: 1,
                    fillOpacity: 0.8,
                }}
            />
            {width > 30 && height > 30 && (
                <text
                    x={x + width / 2}
                    y={y + height / 2}
                    textAnchor="middle"
                    fill="#fff"
                    fontSize={Math.min(width / 4, 14)}
                    fontWeight="bold"
                    style={{ pointerEvents: 'none' }}
                >
                    {name}
                </text>
            )}
            {width > 50 && height > 50 && (
                <text
                    x={x + width / 2}
                    y={y + height / 2 + 14}
                    textAnchor="middle"
                    fill="#fff"
                    fontSize={Math.min(width / 6, 10)}
                    fillOpacity={0.8}
                    style={{ pointerEvents: 'none' }}
                >
                    ${(value / 1000).toFixed(0)}k
                </text>
            )}
        </g>
    );
};

export default function LiquidationHeatmap() {
    const [data, setData] = useState<LiquidationData[]>([]);
    const [loading, setLoading] = useState(true);
    const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

    const fetchData = async () => {
        try {
            // Check if we are in dev mode and use localhost directly if API_BASE_URL is relative
            // However, typically API_BASE_URL should be configured correctly.
            // Assuming API_BASE_URL is 'http://localhost:8000' or similar
            const res = await fetch(`${API_BASE_URL}/api/liquidations/heatmap`);
            if (!res.ok) throw new Error('Failed to fetch');
            const json = await res.json();

            // Recharts Treemap needs 'name' and 'children' or flat array with name/size
            // But standard Treemap can take flat data if configured right, or we map it
            // For simple Recharts Treemap, it expects flat array with `dataKey` for value.
            // We'll pass the array directly and map 'symbol' -> 'name' if needed, but 'dataKey="value"' works.

            // Map symbol to name for Recharts
            const formatted = json.map((item: any) => ({
                ...item,
                name: item.symbol
            }));

            setData(formatted);
            setLastUpdated(new Date());
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000); // Update every 5s
        return () => clearInterval(interval);
    }, []);

    if (loading && data.length === 0) {
        return (
            <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                Loading Liquidations...
            </div>
        );
    }

    if (data.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-gray-400 text-sm text-center p-4">
                <p>No liquidation data yet.</p>
                <p className="text-xs mt-1 opacity-70">Waiting for live events from Binance...</p>
            </div>
        );
    }

    return (
        <div className="w-full h-full flex flex-col">
            <div className="flex justify-between items-center mb-1 px-1">
                <span className="text-[10px] text-gray-400">
                    Live from Binance • 1h Rolling Window
                </span>
                <span className="text-[10px] text-gray-500">
                    Updated: {lastUpdated.toLocaleTimeString()}
                </span>
            </div>
            <div className="flex-1 w-full min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                    <Treemap
                        data={data as any}
                        dataKey="value"
                        aspectRatio={4 / 3}
                        stroke="#fff"
                        fill="#8884d8"
                        content={<CustomContent />}
                        animationDuration={500}
                    >
                        <Tooltip content={<CustomTooltip />} />
                    </Treemap>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
