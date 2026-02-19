'use client';

import React, { useEffect, useRef, useState, useCallback, useLayoutEffect } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi, Time } from 'lightweight-charts';
import { API_BASE_URL } from '@/lib/api';
import { useStore } from '@/store/useStore';
import { RefreshCw, Settings } from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════════

interface LiquidationEvent {
    price: number;
    amount_usd: number;
    side: 'SELL' | 'BUY';
    timestamp: number;
}

interface LiquidationLevel {
    price: number;
    long_liq: number;
    short_liq: number;
    total: number;
}

interface LiquidationLevelsResponse {
    levels: LiquidationLevel[];
    max_value: number;
    bin_size: number;
    price_min: number;
    price_max: number;
}

interface Candle {
    time: Time;
    open: number;
    high: number;
    low: number;
    close: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
// LEGEND COMPONENT (Coinglass Style)
// ═══════════════════════════════════════════════════════════════════════════════

const HeatmapLegend = ({ maxValue }: { maxValue: number }) => {
    const formatValue = (val: number) => {
        if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(2)}M`;
        if (val >= 1_000) return `${(val / 1_000).toFixed(0)}K`;
        return val.toFixed(0);
    };

    return (
        <div className="absolute left-3 top-1/2 -translate-y-1/2 z-30 flex items-center gap-2">
            {/* Gradient Bar - Coinglass Style */}
            <div
                className="w-3 h-40 rounded-sm"
                style={{
                    background: 'linear-gradient(to bottom, #FCFF00 0%, #00CED1 40%, #3366CC 70%, #3D0C74 100%)',
                    boxShadow: '0 0 15px rgba(252, 255, 0, 0.4)'
                }}
            />
            {/* Labels */}
            <div className="flex flex-col justify-between h-40 text-[10px] font-mono">
                <span className="text-yellow-400 font-semibold">{formatValue(maxValue)}</span>
                <span className="text-cyan-400">{formatValue(maxValue * 0.5)}</span>
                <span className="text-purple-400">0</span>
            </div>
        </div>
    );
};

// ═══════════════════════════════════════════════════════════════════════════════
// COINGLASS-STYLE LIQUIDATION HEATMAP
// ═══════════════════════════════════════════════════════════════════════════════

export default function LiquidationChart() {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
    const heatmapCanvasRef = useRef<HTMLCanvasElement>(null);
    const { chartSymbol } = useStore();

    // State
    const [candles, setCandles] = useState<Candle[]>([]);
    const [liquidations, setLiquidations] = useState<LiquidationEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
    const [maxVolume, setMaxVolume] = useState(0);
    const [priceRange, setPriceRange] = useState({ min: 0, max: 0 });

    // ═══════════════════════════════════════════════════════════════════════════
    // Coinglass Color Gradient: Purple → Cyan → Yellow
    // ═══════════════════════════════════════════════════════════════════════════
    const getHeatmapColor = useCallback((intensity: number) => {
        // intensity: 0 to 1
        const t = Math.min(Math.max(intensity, 0), 1);

        // Coinglass gradient: Deep Purple (0) → Blue → Cyan → Yellow (1)
        if (t < 0.2) {
            // Deep Purple base
            const alpha = 0.3 + t * 2;
            return `rgba(61, 12, 116, ${alpha})`;
        }
        if (t < 0.4) {
            // Purple to Blue
            const localT = (t - 0.2) / 0.2;
            const r = Math.floor(61 - 10 * localT);
            const g = Math.floor(12 + 50 * localT);
            const b = Math.floor(116 + 88 * localT);
            return `rgba(${r}, ${g}, ${b}, ${0.7 + t * 0.2})`;
        }
        if (t < 0.65) {
            // Blue to Cyan
            const localT = (t - 0.4) / 0.25;
            const r = Math.floor(51 - 51 * localT);
            const g = Math.floor(62 + 144 * localT);
            const b = Math.floor(204 + 5 * localT);
            return `rgba(${r}, ${g}, ${b}, ${0.75 + t * 0.15})`;
        }
        // Cyan to Yellow (brightest)
        const localT = (t - 0.65) / 0.35;
        const r = Math.floor(0 + 252 * localT);
        const g = Math.floor(206 + 49 * localT);
        const b = Math.floor(209 - 209 * localT);
        return `rgba(${r}, ${g}, ${b}, ${0.85 + t * 0.15})`;
    }, []);

    // ═══════════════════════════════════════════════════════════════════════════
    // FETCH DATA
    // ═══════════════════════════════════════════════════════════════════════════
    const fetchData = useCallback(async (isInitial: boolean = false) => {
        if (isInitial) setLoading(true);
        else setRefreshing(true);

        try {
            const symbol = chartSymbol.split(':')[1] || chartSymbol;

            // Fetch candles (1h, 7 days)
            const candleRes = await fetch(`${API_BASE_URL}/api/market/candles/${symbol}?interval=1h&limit=168`);
            if (candleRes.ok) {
                const candleData = await candleRes.json();
                setCandles(candleData);

                // Calculate price range from candles
                if (candleData.length > 0) {
                    const prices = candleData.flatMap((c: Candle) => [c.high, c.low]);
                    const minPrice = Math.min(...prices);
                    const maxPrice = Math.max(...prices);
                    const padding = (maxPrice - minPrice) * 0.1;
                    setPriceRange({
                        min: minPrice - padding,
                        max: maxPrice + padding
                    });
                }
            }

            // Fetch liquidation history
            const liqRes = await fetch(`${API_BASE_URL}/api/liquidations/history/${symbol}`);
            if (liqRes.ok) {
                const liqData = await liqRes.json();
                setLiquidations(liqData);

                // Calculate max volume for normalization
                if (liqData.length > 0) {
                    const maxLiq = Math.max(...liqData.map((l: LiquidationEvent) => l.amount_usd));
                    setMaxVolume(maxLiq * 2); // Scale up for visibility
                }
            }

            setLastUpdated(new Date());
        } catch (error) {
            console.error("Failed to load chart data", error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, [chartSymbol]);

    // Initial load
    useEffect(() => {
        fetchData(true);
    }, [fetchData]);

    // ═══════════════════════════════════════════════════════════════════════════
    // BUILD PRICE-LEVEL BINS (Coinglass Style)
    // ═══════════════════════════════════════════════════════════════════════════
    const buildPriceLevelBins = useCallback(() => {
        if (liquidations.length === 0 || priceRange.max <= priceRange.min) {
            return { bins: new Map<number, number>(), maxValue: 0, binSize: 0, numBins: 0 };
        }

        const NUM_BINS = 150; // More bins for finer granularity
        const binSize = (priceRange.max - priceRange.min) / NUM_BINS;
        const bins = new Map<number, number>();

        // Initialize all bins
        for (let i = 0; i < NUM_BINS; i++) {
            const price = priceRange.min + (i + 0.5) * binSize;
            bins.set(i, 0);
        }

        // Aggregate liquidations into bins
        liquidations.forEach(liq => {
            if (liq.price >= priceRange.min && liq.price <= priceRange.max) {
                const binIndex = Math.floor((liq.price - priceRange.min) / binSize);
                if (binIndex >= 0 && binIndex < NUM_BINS) {
                    bins.set(binIndex, (bins.get(binIndex) || 0) + liq.amount_usd);
                }
            }
        });

        const maxValue = Math.max(...Array.from(bins.values()));
        return { bins, maxValue, binSize, numBins: NUM_BINS };
    }, [liquidations, priceRange]);

    // ═══════════════════════════════════════════════════════════════════════════
    // INITIALIZE LIGHTWEIGHT CHARTS
    // ═══════════════════════════════════════════════════════════════════════════
    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: 'transparent' },
                textColor: '#9CA3AF',
            },
            grid: {
                vertLines: { color: 'rgba(42, 46, 57, 0.3)', style: 0 },
                horzLines: { color: 'rgba(42, 46, 57, 0.3)', style: 0 },
            },
            crosshair: {
                mode: 0,
                vertLine: { color: 'rgba(186, 104, 200, 0.5)', width: 1 },
                horzLine: { color: 'rgba(186, 104, 200, 0.5)', width: 1 },
            },
            rightPriceScale: {
                borderColor: 'rgba(42, 46, 57, 0.5)',
                textColor: '#9CA3AF',
            },
            timeScale: {
                borderColor: 'rgba(42, 46, 57, 0.5)',
                timeVisible: true,
                secondsVisible: false,
            },
            handleScroll: true,
            handleScale: true,
        });

        const candleSeries = chart.addCandlestickSeries({
            upColor: '#22C55E',
            downColor: '#EF4444',
            borderUpColor: '#22C55E',
            borderDownColor: '#EF4444',
            wickUpColor: '#22C55E',
            wickDownColor: '#EF4444',
        });

        chartRef.current = chart;
        candleSeriesRef.current = candleSeries;

        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                    height: chartContainerRef.current.clientHeight,
                });
            }
        };

        window.addEventListener('resize', handleResize);
        handleResize();

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, []);

    // Update candle data
    useEffect(() => {
        if (candleSeriesRef.current && candles.length > 0) {
            candleSeriesRef.current.setData(candles);
            chartRef.current?.timeScale().fitContent();
        }
    }, [candles]);

    // ═══════════════════════════════════════════════════════════════════════════
    // RENDER HEATMAP BACKGROUND (Full-Width Horizontal Bars)
    // ═══════════════════════════════════════════════════════════════════════════
    useEffect(() => {
        let animationFrameId: number;
        const canvas = heatmapCanvasRef.current;
        const ctx = canvas?.getContext('2d');

        const renderHeatmap = () => {
            if (!chartRef.current || !candleSeriesRef.current || !canvas || !ctx) {
                animationFrameId = requestAnimationFrame(renderHeatmap);
                return;
            }

            const width = canvas.width;
            const height = canvas.height;
            ctx.clearRect(0, 0, width, height);

            // ═══════════════════════════════════════════════════════════════════
            // STEP 1: Fill ENTIRE background with base purple gradient (Coinglass style)
            // ═══════════════════════════════════════════════════════════════════
            const bgGradient = ctx.createLinearGradient(0, 0, 0, height);
            bgGradient.addColorStop(0, 'rgba(61, 12, 116, 0.85)');   // Deep purple top
            bgGradient.addColorStop(0.5, 'rgba(45, 15, 90, 0.75)');  // Darker mid
            bgGradient.addColorStop(1, 'rgba(61, 12, 116, 0.85)');   // Deep purple bottom
            ctx.fillStyle = bgGradient;
            ctx.fillRect(0, 0, width, height);

            if (liquidations.length === 0 || priceRange.max <= priceRange.min) {
                animationFrameId = requestAnimationFrame(renderHeatmap);
                return;
            }

            const { bins, maxValue, binSize, numBins } = buildPriceLevelBins();

            // Even if no liquidations, still draw bars at each price level
            const effectiveMaxValue = maxValue > 0 ? maxValue : 1;

            // ═══════════════════════════════════════════════════════════════════
            // STEP 2: Draw bars at EVERY price level (Coinglass style - dense coverage)
            // ═══════════════════════════════════════════════════════════════════

            // Draw ALL bins - each one gets a visible bar
            for (let i = 0; i < numBins; i++) {
                const volume = bins.get(i) || 0;
                const price = priceRange.min + (i + 0.5) * binSize;
                const y = candleSeriesRef.current!.priceToCoordinate(price);

                if (y === null || y < -50 || y > height + 50) continue;

                // Calculate bar height - make them slightly overlap for no gaps
                const priceTop = price + binSize / 2;
                const priceBottom = price - binSize / 2;
                const yTop = candleSeriesRef.current!.priceToCoordinate(priceTop);
                const yBottom = candleSeriesRef.current!.priceToCoordinate(priceBottom);

                let barHeight = 8;
                if (yTop !== null && yBottom !== null) {
                    barHeight = Math.max(Math.abs(yBottom - yTop) * 1.1, 6); // 10% overlap
                }

                // Calculate intensity - give every bar a minimum visibility
                let intensity = 0.08; // Base intensity for all bars (visible purple)
                if (volume > 0) {
                    const rawIntensity = volume / effectiveMaxValue;
                    intensity = 0.15 + Math.pow(rawIntensity, 0.35) * 0.85; // Range: 0.15 to 1.0
                }

                const color = getHeatmapColor(intensity);

                // Draw bar
                ctx.save();

                // Add glow for higher intensity bars
                if (intensity > 0.2) {
                    ctx.shadowColor = color;
                    ctx.shadowBlur = 8 + intensity * 35;
                }

                ctx.fillStyle = color;
                ctx.fillRect(0, y - barHeight / 2, width, barHeight);

                // Extra glow for high intensity
                if (intensity > 0.5) {
                    ctx.shadowBlur = 20 + intensity * 25;
                    ctx.fillRect(0, y - barHeight / 2, width, barHeight);
                }

                ctx.restore();
            }

            animationFrameId = requestAnimationFrame(renderHeatmap);
        };

        renderHeatmap();
        return () => cancelAnimationFrame(animationFrameId);
    }, [liquidations, priceRange, buildPriceLevelBins, getHeatmapColor]);

    // ═══════════════════════════════════════════════════════════════════════════
    // CANVAS RESIZE HANDLER
    // ═══════════════════════════════════════════════════════════════════════════
    useLayoutEffect(() => {
        const canvas = heatmapCanvasRef.current;
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

    // Calculate displayed max value
    const displayMaxValue = maxVolume || 1;

    return (
        <div className="flex flex-col w-full h-full bg-[#0a0a14]">
            {/* Header Bar - Refresh controls separated from chart */}
            <div className="shrink-0 flex items-center justify-between px-4 py-2 border-b border-purple-900/30 bg-[#0d0d1a]">
                <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-purple-400">Liquidation Heatmap</span>
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

            {/* Chart Area */}
            <div className="relative flex-1 min-h-0">
                {/* Legend */}
                <HeatmapLegend maxValue={displayMaxValue} />

                {/* 1. Heatmap Canvas (Background Layer) */}
                <canvas
                    ref={heatmapCanvasRef}
                    className="absolute inset-0 z-0 pointer-events-none"
                    style={{ filter: 'blur(1px)' }}
                />

                {/* 2. Chart Container (Foreground Layer) */}
                <div
                    ref={chartContainerRef}
                    className="absolute inset-0 z-10"
                />

                {/* Loading Overlay */}
                {loading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm z-20">
                        <div className="flex flex-col items-center gap-3">
                            <RefreshCw className="w-8 h-8 animate-spin text-purple-400" />
                            <span className="text-sm text-gray-400">Heatmap loading...</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
