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
    const [timePriceBins, setTimePriceBins] = useState<TimePriceBin[]>([]);
    const [maxVolume, setMaxVolume] = useState(0);
    const [priceRange, setPriceRange] = useState<{ min: number; max: number; binSize: number }>({ min: 0, max: 0, binSize: 1 });

    // Fetch initial data
    useEffect(() => {
        const loadHistory = async () => {
            if (candles.length === 0) setLoading(true);
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
            } catch (error) {
                console.error("Failed to load chart data", error);
            } finally {
                setLoading(false);
            }
        };

        loadHistory();
        const interval = setInterval(loadHistory, 5000);
        return () => clearInterval(interval);
    }, [chartSymbol]);

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

    // Coinglass-style Color Interpolator
    // Purple (low) → Blue → Cyan → Yellow (high)
    const getHeatmapColor = useCallback((t: number) => {
        // t is normalized volume 0..1
        // Coinglass gradient: Purple → Blue → Cyan/Teal → Yellow

        if (t < 0.15) {
            // Deep Purple (barely visible)
            return `rgba(61, 12, 116, ${0.3 + t * 2})`;
        }
        if (t < 0.35) {
            // Blue transition
            const localT = (t - 0.15) / 0.2;
            const r = Math.floor(61 - 61 * localT);
            const g = Math.floor(12 + 90 * localT);
            const b = Math.floor(116 + 88 * localT);
            return `rgba(${r}, ${g}, ${b}, ${0.6 + t * 0.3})`;
        }
        if (t < 0.6) {
            // Cyan/Teal
            const localT = (t - 0.35) / 0.25;
            const r = Math.floor(0 + 0 * localT);
            const g = Math.floor(102 + 104 * localT);
            const b = Math.floor(204 - 15 * localT);
            return `rgba(${r}, ${g}, ${b}, ${0.7 + t * 0.2})`;
        }
        // Yellow (brightest)
        const localT = (t - 0.6) / 0.4;
        const r = Math.floor(0 + 252 * localT);
        const g = Math.floor(206 + 49 * localT);
        const b = Math.floor(189 - 189 * localT);
        return `rgba(${r}, ${g}, ${b}, ${0.85 + t * 0.15})`;
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

            // Estimate candle width by checking coordinates of adjacent candles
            let candleWidth = 12; // Default
            if (candles.length >= 2) {
                const x1 = timeScale.timeToCoordinate(candles[0].time);
                const x2 = timeScale.timeToCoordinate(candles[1].time);
                if (x1 !== null && x2 !== null) {
                    candleWidth = Math.max(Math.abs(x2 - x1), 4);
                }
            }

            // Calculate cell height based on price bins
            const { binSize } = priceRange;

            // Draw each time+price cell
            timePriceBins.forEach(bin => {
                const x = timeScale.timeToCoordinate(bin.time);
                const y = candleSeriesRef.current!.priceToCoordinate(bin.price);

                if (x === null || y === null) return;
                if (x < 0 || y < -50 || y > height + 50) return;

                const intensity = bin.volume / maxVolume;

                // Skip very low intensity for cleaner look
                if (intensity < 0.03) return;

                const color = getHeatmapColor(intensity);

                // Calculate cell height in pixels (based on price bin size)
                const priceTop = bin.price + binSize / 2;
                const priceBottom = bin.price - binSize / 2;
                const yTop = candleSeriesRef.current!.priceToCoordinate(priceTop);
                const yBottom = candleSeriesRef.current!.priceToCoordinate(priceBottom);

                let cellHeight = 15; // Default
                if (yTop !== null && yBottom !== null) {
                    cellHeight = Math.max(Math.abs(yBottom - yTop), 8);
                }

                // Draw cell centered on candle time, behind the candle
                const cellX = x - candleWidth / 2;
                const cellY = y - cellHeight / 2;

                // Create soft glow effect
                ctx.save();
                ctx.shadowColor = color;
                ctx.shadowBlur = 8;
                ctx.fillStyle = color;
                ctx.fillRect(cellX, cellY, candleWidth, cellHeight);
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

            {/* 1. Heatmap Overlay (Background Layer) */}
            <div
                ref={overlayRef}
                className="absolute inset-0 z-0 pointer-events-none"
            >
                <canvas
                    className="w-full h-full"
                    style={{ filter: 'blur(3px)', opacity: 0.95 }}
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
