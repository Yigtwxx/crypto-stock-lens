'use client';

import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Globe } from 'lucide-react';

interface MarketIndex {
    symbol: string;
    name: string;
    price: number;
    change_24h: number;
    region: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function GlobalTicker() {
    const [indices, setIndices] = useState<MarketIndex[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchIndices = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/market/indices`);
                if (res.ok) {
                    const data = await res.json();
                    setIndices(data);
                }
            } catch (error) {
                console.error("Failed to fetch indices", error);
            } finally {
                setLoading(false);
            }
        };

        fetchIndices();
        // Refresh every 5 minutes
        const interval = setInterval(fetchIndices, 300000);
        return () => clearInterval(interval);
    }, []);

    if (loading || indices.length === 0) return null;

    // Duplicate list for seamless infinite scroll
    const tickerItems = [...indices, ...indices, ...indices];

    return (
        <div className="h-8 bg-[#050508] border-b border-white/5 flex items-center relative overflow-hidden z-40">
            {/* Label */}
            <div className="absolute left-0 top-0 bottom-0 bg-[#050508] px-3 flex items-center gap-2 z-10 border-r border-yellow-500/20 shadow-[4px_0_10px_rgba(0,0,0,0.5)]">
                <Globe className="w-3.5 h-3.5 text-yellow-500 animate-pulse" />
                <span className="text-[10px] font-bold text-yellow-500 uppercase tracking-wider">Global Markets</span>
            </div>

            {/* Scrolling Ticker */}
            <div className="flex items-center overflow-hidden w-full mask-linear-fade">
                <div className="flex animate-ticker whitespace-nowrap pl-32 hover:pause-animation">
                    {tickerItems.map((item, index) => (
                        <div key={`${item.symbol}-${index}`} className="flex items-center gap-2 px-6 border-r border-white/5">
                            <span className="text-xs font-semibold text-gray-400">{item.name}</span>
                            <span className={`text-xs font-mono font-medium ${item.change_24h >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'}`}>
                                {item.price.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                            </span>
                            <div className={`flex items-center text-[10px] ${item.change_24h >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'}`}>
                                {item.change_24h >= 0 ? <TrendingUp className="w-3 h-3 mr-0.5" /> : <TrendingDown className="w-3 h-3 mr-0.5" />}
                                <span>{Math.abs(item.change_24h).toFixed(2)}%</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <style jsx>{`
                .animate-ticker {
                    animation: ticker 40s linear infinite;
                }
                .hover\\:pause-animation:hover {
                    animation-play-state: paused;
                }
                .mask-linear-fade {
                    mask-image: linear-gradient(to right, transparent 0%, black 100px, black calc(100% - 20px), transparent 100%);
                }
                @keyframes ticker {
                    0% { transform: translateX(0); }
                    100% { transform: translateX(-33.33%); } /* Move by 1/3 since we tripled the list */
                }
            `}</style>
        </div>
    );
}
