'use client';

import React, { useEffect, useRef, useState, useCallback, useLayoutEffect } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi, Time } from 'lightweight-charts';
import { API_BASE_URL } from '@/lib/api';
import { useStore } from '@/store/useStore';
import { RefreshCw } from 'lucide-react';

interface LiquidationEvent {
    price: number;
    amount_usd: number;
    side: 'Likidasyon' | 'SHORT' | 'SELL' | 'BUY';
    timestamp: number;
}

interface Candle {
    time: Time;
    open: number;
    high: number;
    low: number;
    close: number;
}

// Time+Price based bin for Coinglass-style heatmap
interface TimePriceBin {
    time: Time;      // Candle time
    priceIndex: number; // Price bin index
    price: number;   // Actual price level
    volume: number;  // Liquidation USD value
}

// Coinglass-style Legend Component
const HeatmapLegend = ({ maxValue }: { maxValue: number }) => {
    const formatValue = (val: number) => {
        if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
        if (val >= 1_000) return `${(val / 1_000).toFixed(0)}K`;
        return val.toFixed(0);
    };

    return (
        <div className="absolute left-2 top-1/2 -translate-y-1/2 z-30 flex items-center gap-2">
            {/* Gradient Bar */}
            <div
                className="w-3 h-32 rounded-sm"
                style={{
                    background: 'linear-gradient(to bottom, #FCFF00 0%, #00CED1 35%, #0066CC 60%, #3D0C74 100%)',
                    boxShadow: '0 0 12px rgba(252, 255, 0, 0.3)'
                }}
            />
            {/* Labels */}
            <div className="flex flex-col justify-between h-32 text-[9px] font-mono">
                <span className="text-yellow-400">{formatValue(maxValue)}</span>
                <span className="text-cyan-400">{formatValue(maxValue * 0.5)}</span>
                <span className="text-purple-400">0</span>
            </div>
        </div>
    );
};

export default function LiquidationChart() {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
    const overlayRef = useRef<HTMLDivElement>(null);
    const { chartSymbol } = useStore();

    // State
    const [candles, setCandles] = useState<Candle[]>([]);
    const [liquidations, setLiquidations] = useState<LiquidationEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
    const [timePriceBins, setTimePriceBins] = useState<TimePriceBin[]>([]);
    const [maxVolume, setMaxVolume] = useState(0);
    const [priceRange, setPriceRange] = useState<{ min: number; max: number; binSize: number }>({ min: 0, max: 0, binSize: 1 });

    // Fetch data function (manual trigger)
    const fetchData = useCallback(async (isInitial: boolean = false) => {
        if (isInitial) setLoading(true);
        else setRefreshing(true);

        try {
            const symbol = chartSymbol.split(':')[1] || chartSymbol;

            // 1. Fetch Candles
            const candleRes = await fetch(`${API_BASE_URL}/api/market/candles/${symbol}?interval=1h&limit=168`);
            if (candleRes.ok) {
                const candleData = await candleRes.json();
                setCandles(candleData);
            }

            // 2. Fetch Liquidation History
            const liqRes = await fetch(`${API_BASE_URL}/api/liquidations/history/${symbol}`);
            if (liqRes.ok) {
                const liqData = await liqRes.json();
                setLiquidations(liqData);
            }

            setLastUpdated(new Date());
        } catch (error) {
            console.error("Failed to load chart data", error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, [chartSymbol]);

    // Initial load only (no auto-refresh)
    useEffect(() => {
        fetchData(true);
    }, [fetchData]);

    // Build Time+Price based bins (Coinglass Style)
    const buildTimePriceBins = useCallback((events: LiquidationEvent[], candleData: Candle[]) => {
        if (events.length === 0 || candleData.length === 0) {
            setTimePriceBins([]);
            setMaxVolume(0);
            return;
        }

        // Get price range from all liquidations
        const prices = events.map(e => e.price);
        const minPrice = Math.min(...prices) * 0.995;
        const maxPrice = Math.max(...prices) * 1.005;

        // Create price bins
        const priceBinCount = 80; // Number of price levels
        const range = maxPrice - minPrice;
        const binSize = range / priceBinCount;

        setPriceRange({ min: minPrice, max: maxPrice, binSize });

        // Create a map for candle times -> index
        const candleTimeMap = new Map<number, number>();
        candleData.forEach((candle, idx) => {
            const time = typeof candle.time === 'number' ? candle.time : Number(candle.time);
            candleTimeMap.set(time, idx);
        });

        // Get candle times as numbers for matching
        const candleTimes = candleData.map(c => typeof c.time === 'number' ? c.time : Number(c.time));

        // Find nearest candle for a timestamp
        const findNearestCandleIndex = (timestamp: number): number => {
            let closestIdx = 0;
            let closestDiff = Infinity;

            for (let i = 0; i < candleTimes.length; i++) {
                const diff = Math.abs(candleTimes[i] - timestamp);
                if (diff < closestDiff) {
                    closestDiff = diff;
                    closestIdx = i;
                }
            }
            return closestIdx;
        };

        // Aggregate liquidations by time+price
        const binMap = new Map<string, TimePriceBin>();

        events.forEach(event => {
            const candleIdx = findNearestCandleIndex(event.timestamp);
            const candleTime = candleData[candleIdx].time;
            const priceIndex = Math.floor((event.price - minPrice) / binSize);

            if (priceIndex < 0 || priceIndex >= priceBinCount) return;

            const key = `${candleIdx}_${priceIndex}`;

            if (binMap.has(key)) {
                binMap.get(key)!.volume += event.amount_usd;
            } else {
                binMap.set(key, {
                    time: candleTime,
                    priceIndex,
                    price: minPrice + (priceIndex * binSize) + (binSize / 2),
                    volume: event.amount_usd
                });
            }
        });

        const bins = Array.from(binMap.values());

        // Find max volume for normalization
        let maxVol = 0;
        bins.forEach(b => {
            if (b.volume > maxVol) maxVol = b.volume;
        });

        setTimePriceBins(bins);
        setMaxVolume(maxVol);
    }, []);

    useEffect(() => {
        buildTimePriceBins(liquidations, candles);
    }, [liquidations, candles, buildTimePriceBins]);

    // Initialize Chart
    useEffect(() => {
        if (!chartContainerRef.current) return;

        if (chartRef.current) {
            chartRef.current.remove();
        }

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: 'transparent' },
                textColor: '#9ca3af',
            },
            grid: {
                vertLines: { color: 'rgba(60, 60, 80, 0.15)' },
                horzLines: { color: 'rgba(60, 60, 80, 0.15)' },
            },
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
                borderColor: '#1a1a2e',
            },
            rightPriceScale: {
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.1,
                },
                borderColor: '#1a1a2e',
            },
        });

        chartRef.current = chart;

        const candleSeries = chart.addCandlestickSeries({
            upColor: '#22c55e',
            downColor: '#ef4444',
            borderVisible: false,
            wickUpColor: '#22c55e',
            wickDownColor: '#ef4444',
        });

        candleSeriesRef.current = candleSeries;

        const handleResize = () => {
            if (chartContainerRef.current && chartRef.current) {
                chartRef.current.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                    height: chartContainerRef.current.clientHeight
                });
            }
        };
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            if (chartRef.current) {
                chartRef.current.remove();
                chartRef.current = null;
                candleSeriesRef.current = null;
            }
        };
    }, []);

    useEffect(() => {
        if (candleSeriesRef.current && candles.length > 0) {
            candleSeriesRef.current.setData(candles);
        }
    }, [candles]);

    // Coinglass-style Color Interpolator - ENHANCED VISIBILITY
    // Purple (low) → Blue → Cyan → Yellow (high)
    const getHeatmapColor = useCallback((t: number, forGlow: boolean = false) => {
        // t is normalized volume 0..1
        // Coinglass gradient: Purple → Blue → Cyan/Teal → Yellow
        // forGlow = true returns the raw RGB for glow effect

        const baseAlpha = forGlow ? 1 : (0.65 + t * 0.35); // Much higher base opacity

        if (t < 0.1) {
            // Deep Purple - more visible base
            return `rgba(75, 20, 130, ${baseAlpha})`;
        }
        if (t < 0.25) {
            // Purple to Blue transition
            const localT = (t - 0.1) / 0.15;
            const r = Math.floor(75 - 45 * localT);
            const g = Math.floor(20 + 60 * localT);
            const b = Math.floor(130 + 70 * localT);
            return `rgba(${r}, ${g}, ${b}, ${baseAlpha})`;
        }
        if (t < 0.5) {
            // Blue to Cyan/Teal
            const localT = (t - 0.25) / 0.25;
            const r = Math.floor(30 - 30 * localT);
            const g = Math.floor(80 + 126 * localT);
            const b = Math.floor(200 + 9 * localT);
            return `rgba(${r}, ${g}, ${b}, ${baseAlpha})`;
        }
        if (t < 0.75) {
            // Cyan to Yellow-Green
            const localT = (t - 0.5) / 0.25;
            const r = Math.floor(0 + 150 * localT);
            const g = Math.floor(206 + 40 * localT);
            const b = Math.floor(209 - 150 * localT);
            return `rgba(${r}, ${g}, ${b}, ${baseAlpha})`;
        }
        // Bright Yellow (highest intensity)
        const localT = (t - 0.75) / 0.25;
        const r = Math.floor(150 + 102 * localT);
        const g = Math.floor(246 + 10 * localT);
        const b = Math.floor(59 - 59 * localT);
        return `rgba(${r}, ${g}, ${b}, ${baseAlpha})`;
    }, []);

    // Sync Overlay (Animation Loop) - Coinglass style: draw cells per candle
    useEffect(() => {
        let animationFrameId: number;
        const canvas = overlayRef.current?.querySelector('canvas');
        const ctx = canvas?.getContext('2d');

        const renderLoop = () => {
            if (!chartRef.current || !candleSeriesRef.current || !canvas || !ctx || timePriceBins.length === 0) {
                animationFrameId = requestAnimationFrame(renderLoop);
                return;
            }

            const width = canvas.width;
            const height = canvas.height;

            ctx.clearRect(0, 0, width, height);

            if (maxVolume === 0) {
                animationFrameId = requestAnimationFrame(renderLoop);
                return;
            }

            // Calculate candle width from time scale
            const timeScale = chartRef.current.timeScale();

            // Estimate candle width - LARGER for visibility
            let candleWidth = 18; // Larger default
            if (candles.length >= 2) {
                const x1 = timeScale.timeToCoordinate(candles[0].time);
                const x2 = timeScale.timeToCoordinate(candles[1].time);
                if (x1 !== null && x2 !== null) {
                    candleWidth = Math.max(Math.abs(x2 - x1) * 1.2, 12); // 20% wider
                }
            }

            // Calculate cell height based on price bins
            const { binSize } = priceRange;

            // Sort bins by intensity for proper layering (low first, high on top)
            const sortedBins = [...timePriceBins].sort((a, b) => a.volume - b.volume);

            // Draw each time+price cell with enhanced visibility
            sortedBins.forEach(bin => {
                const x = timeScale.timeToCoordinate(bin.time);
                const y = candleSeriesRef.current!.priceToCoordinate(bin.price);

                if (x === null || y === null) return;
                if (x < -50 || x > width + 50 || y < -50 || y > height + 50) return;

                const intensity = bin.volume / maxVolume;

                // Lower threshold - show more data points
                if (intensity < 0.01) return;

                const color = getHeatmapColor(intensity);
                const glowColor = getHeatmapColor(intensity, true);

                // Calculate cell height in pixels - LARGER minimum
                const priceTop = bin.price + binSize / 2;
                const priceBottom = bin.price - binSize / 2;
                const yTop = candleSeriesRef.current!.priceToCoordinate(priceTop);
                const yBottom = candleSeriesRef.current!.priceToCoordinate(priceBottom);

                let cellHeight = 20; // Larger default
                if (yTop !== null && yBottom !== null) {
                    cellHeight = Math.max(Math.abs(yBottom - yTop), 14); // Minimum 14px
                }

                // Draw cell centered on candle time
                const cellX = x - candleWidth / 2;
                const cellY = y - cellHeight / 2;

                // Stronger glow effect for high intensity
                ctx.save();
                ctx.shadowColor = glowColor;
                ctx.shadowBlur = 12 + intensity * 20; // Dynamic blur based on intensity
                ctx.fillStyle = color;

                // Round rect for smoother look
                const radius = Math.min(4, cellHeight / 4);
                ctx.beginPath();
                ctx.moveTo(cellX + radius, cellY);
                ctx.lineTo(cellX + candleWidth - radius, cellY);
                ctx.quadraticCurveTo(cellX + candleWidth, cellY, cellX + candleWidth, cellY + radius);
                ctx.lineTo(cellX + candleWidth, cellY + cellHeight - radius);
                ctx.quadraticCurveTo(cellX + candleWidth, cellY + cellHeight, cellX + candleWidth - radius, cellY + cellHeight);
                ctx.lineTo(cellX + radius, cellY + cellHeight);
                ctx.quadraticCurveTo(cellX, cellY + cellHeight, cellX, cellY + cellHeight - radius);
                ctx.lineTo(cellX, cellY + radius);
                ctx.quadraticCurveTo(cellX, cellY, cellX + radius, cellY);
                ctx.closePath();
                ctx.fill();

                // Add extra glow layer for high intensity
                if (intensity > 0.5) {
                    ctx.shadowBlur = 25;
                    ctx.fill();
                }
                ctx.restore();
            });

            animationFrameId = requestAnimationFrame(renderLoop);
        };

        renderLoop();
        return () => cancelAnimationFrame(animationFrameId);
    }, [timePriceBins, maxVolume, getHeatmapColor, candles, priceRange]);

    // Update Canvas Size
    useLayoutEffect(() => {
        const canvas = overlayRef.current?.querySelector('canvas');
        const container = chartContainerRef.current;

        if (canvas && container) {
            const resizeCanvas = () => {
                canvas.width = container.clientWidth;
                canvas.height = container.clientHeight;
            };

            resizeCanvas();
            window.addEventListener('resize', resizeCanvas);
            const observer = new ResizeObserver(resizeCanvas);
            observer.observe(container);

            return () => {
                window.removeEventListener('resize', resizeCanvas);
                observer.disconnect();
            };
        }
    }, []);

    return (
        <div className="relative w-full h-full bg-[#0a0a14]">
            {/* Legend */}
            {maxVolume > 0 && <HeatmapLegend maxValue={maxVolume} />}

            {/* Refresh Button - Top Right */}
            <div className="absolute top-2 right-2 z-30 flex items-center gap-2">
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
                        bg-oracle-card border border-oracle-border
                        text-xs font-medium transition-all
                        ${refreshing || loading
                            ? 'opacity-50 cursor-not-allowed text-gray-500'
                            : 'hover:bg-oracle-accent/20 hover:border-oracle-accent/50 text-gray-300 hover:text-white'
                        }
                    `}
                    title="Verileri yenile"
                >
                    <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
                    <span>{refreshing ? 'Yenileniyor...' : 'Yenile'}</span>
                </button>
            </div>

            {/* 1. Heatmap Overlay (Background Layer) */}
            <div
                ref={overlayRef}
                className="absolute inset-0 z-0 pointer-events-none"
            >
                <canvas
                    className="w-full h-full"
                    style={{ filter: 'blur(2px)', opacity: 1 }}
                />
            </div>

            {/* 2. Chart (Foreground Layer) */}
            <div
                ref={chartContainerRef}
                className="absolute inset-0 z-10"
            />

            {loading && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm z-20">
                    <RefreshCw className="w-6 h-6 animate-spin text-white" />
                </div>
            )}
        </div>
    );
}
