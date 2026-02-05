'use client';

import { useEffect, useState } from 'react';
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, Legend } from 'recharts';
import { fetchLiquidations, Liquidation } from '@/lib/api';

interface LiquidationChartProps {
    className?: string;
}

export default function LiquidationChart({ className = '' }: LiquidationChartProps) {
    const [data, setData] = useState<Liquidation[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const loadData = async () => {
        try {
            const result = await fetchLiquidations();
            setData(result);
        } catch (error) {
            console.error("Failed to load liquidations", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 30000); // Poll every 30s
        return () => clearInterval(interval);
    }, []);

    // Process data for charts
    // Separate Longs (Red) and Shorts (Green)
    // "Long Liquidated" means they sold -> price went down. Usually colored RED in dashboards.
    // "Short Liquidated" means they bought -> price went up. Usually colored GREEN.
    const longLiquidations = data.filter(d => d.side === 'Long').map(d => ({
        x: d.timestamp,
        y: d.price,
        z: d.amount_usd,
        ...d
    }));

    const shortLiquidations = data.filter(d => d.side === 'Short').map(d => ({
        x: d.timestamp,
        y: d.price,
        z: d.amount_usd,
        ...d
    }));

    // Format X axis (time)
    const formatTime = (unixTime: number) => {
        return new Date(unixTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    // Format Tooltip
    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="bg-oracle-card border border-oracle-border p-3 rounded-lg shadow-xl text-xs">
                    <p className="font-bold text-white mb-1">{data.symbol} {data.side} Liq</p>
                    <p className="text-gray-300">Price: <span className="text-white">${data.price.toLocaleString()}</span></p>
                    <p className="text-gray-300">Value: <span className="text-white">${Math.round(data.amount_usd).toLocaleString()}</span></p>
                    <p className="text-gray-400 mt-1">{new Date(data.timestamp).toLocaleTimeString()}</p>
                </div>
            );
        }
        return null;
    };

    if (isLoading && data.length === 0) {
        return <div className="w-full h-full flex items-center justify-center text-gray-500">Loading Liquidation Data...</div>;
    }

    return (
        <div className={`relative w-full h-full bg-oracle-darker rounded-xl border border-oracle-border p-4 ${className}`}>
            <div className="absolute top-4 left-4 z-10">
                <h3 className="font-bold text-white text-lg">Liquidation Feed (Bubble Map)</h3>
                <p className="text-xs text-gray-400">Real-time liquidation events size=volume</p>
            </div>

            <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 60, right: 20, bottom: 20, left: 10 }}>
                    <XAxis
                        type="number"
                        dataKey="x"
                        domain={['auto', 'auto']}
                        name="Time"
                        tickFormatter={formatTime}
                        stroke="#4b5563"
                        tick={{ fill: '#9ca3af', fontSize: 10 }}
                    />
                    <YAxis
                        type="number"
                        dataKey="y"
                        domain={['auto', 'auto']}
                        name="Price"
                        unit="$"
                        stroke="#4b5563"
                        tick={{ fill: '#9ca3af', fontSize: 10 }}
                    />
                    <ZAxis type="number" dataKey="z" range={[50, 400]} name="Volume" />
                    <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
                    <Legend verticalAlign="top" height={36} iconType="circle" />

                    {/* Shorts Liquidated (Green - Price Up) */}
                    <Scatter name="Shorts Liquidated (Buys)" data={shortLiquidations} fill="#4ade80" fillOpacity={0.6} shape="circle" />

                    {/* Longs Liquidated (Red - Price Down) */}
                    <Scatter name="Longs Liquidated (Sells)" data={longLiquidations} fill="#ef4444" fillOpacity={0.6} shape="circle" />
                </ScatterChart>
            </ResponsiveContainer>
        </div>
    );
}
