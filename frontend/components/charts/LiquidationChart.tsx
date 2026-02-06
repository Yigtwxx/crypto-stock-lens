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

interface PriceBin {
    price: number;
    volume: number;
}

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
    const [profileBins, setProfileBins] = useState<PriceBin[]>([]);

    // Fetch initial data
    useEffect(() => {
        const loadHistory = async () => {
            // Only set loading on initial fetch if empty
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
    }, [chartSymbol]); // We only hard-reset on symbol change

    // Build Liquidation Profile Bins (Coinglass Style: Price Levels)
    const buildProfile = useCallback((events: LiquidationEvent[]) => {
        if (events.length === 0) {
            setProfileBins([]);
            return;
        }

        // Find min/max price for the whole dataset
        const prices = events.map(e => e.price);
        const minPrice = Math.min(...prices) * 0.99;
        const maxPrice = Math.max(...prices) * 1.01;

        // Use higher resolution bins for heatmap feel (e.g. 100 bins)
        const binCount = 100;
        const range = maxPrice - minPrice;
        const binSize = range / binCount;

        const bins: PriceBin[] = [];
        for (let i = 0; i < binCount; i++) {
            bins.push({
                price: minPrice + (i * binSize),
                volume: 0,
            });
        }

        // Fill bins
        events.forEach(e => {
            const binIndex = Math.floor((e.price - minPrice) / binSize);
            if (binIndex >= 0 && binIndex < binCount) {
                bins[binIndex].volume += e.amount_usd;
            }
        });

        setProfileBins(bins);
    }, []);

    // Trigger buildProfile when liquidations change
    useEffect(() => {
        buildProfile(liquidations);
    }, [liquidations, buildProfile]);

    // Initialize Chart (Run ONCE)
    useEffect(() => {
        if (!chartContainerRef.current) return;

        // Cleanup
        if (chartRef.current) {
            chartRef.current.remove();
        }

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: 'transparent' }, // Transparent to show heatmap behind
                textColor: '#9ca3af',
            },
            grid: {
                vertLines: { color: 'rgba(30, 30, 46, 0.5)' },
                horzLines: { color: 'rgba(30, 30, 46, 0.5)' },
            },
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
                borderColor: '#1e1e2e',
            },
            rightPriceScale: {
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.1,
                },
                borderColor: '#1e1e2e',
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

        // Resize Handler
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

    // Update Data
    useEffect(() => {
        if (candleSeriesRef.current && candles.length > 0) {
            candleSeriesRef.current.setData(candles);
        }
    }, [candles]);

    // Coinglass-like Color Interpolator
    // Dark Purple Background -> Heatmap adds light
    const getHeatmapColor = useCallback((t: number) => {
        // t is normalized volume 0..1
        // We want a glowing effect.

        // Low: Deep Purple/Blue (barely visible)
        // Mid: Cyan/Green
        // High: Yellow/White

        if (t < 0.2) return `rgba(76, 29, 149, ${t * 0.5})`; // Deep Purple
        if (t < 0.4) return `rgba(59, 130, 246, ${0.3 + t * 0.5})`; // Blue
        if (t < 0.7) return `rgba(34, 197, 94, ${0.4 + t * 0.5})`; // Green
        return `rgba(253, 224, 71, ${0.5 + t * 0.5})`; // Yellow (Bright)
    }, []);

    // Sync Overlay (Animation Loop)
    useEffect(() => {
        let animationFrameId: number;
        const canvas = overlayRef.current?.querySelector('canvas');
        const ctx = canvas?.getContext('2d');

        const renderLoop = () => {
            if (!chartRef.current || !candleSeriesRef.current || !canvas || !ctx || profileBins.length === 0) {
                animationFrameId = requestAnimationFrame(renderLoop);
                return;
            }

            const width = canvas.width;
            const height = canvas.height;

            // Clear entire canvas
            ctx.clearRect(0, 0, width, height);

            // Find max volume to normalize intensity
            let maxVol = 0;
            for (let i = 0; i < profileBins.length; i++) {
                if (profileBins[i].volume > maxVol) maxVol = profileBins[i].volume;
            }

            if (maxVol === 0) {
                animationFrameId = requestAnimationFrame(renderLoop);
                return;
            }

            // Draw full-width bands
            // We iterate all bins and draw them at their Y-coordinate

            // Optimization: Batch drawing calls or use a path? 
            // Simple rects are fine for <100 bins.

            profileBins.forEach(bin => {
                const y = candleSeriesRef.current!.priceToCoordinate(bin.price);

                // Check visibility
                if (y === null || y < -10 || y > height + 10) return;

                const intensity = bin.volume / maxVol;

                // Enhance "Heat" feel: Draw a band with soft edges?
                // Visual Trick: Draw full width rect.
                // The styling "filter: blur(8px)" on the canvas CSS handles the softness.

                ctx.fillStyle = getHeatmapColor(intensity);

                // Draw band
                // Height: Try to match bin size or fixed visual height.
                // Dynamic height based on Zoom? 
                // Getting price range is expensive every frame.
                // Let's use a fixed height that looks good visually (e.g. 1% of height or fixed px).
                // 10px with blur looks like a cloud.
                const barHeight = 12;
                ctx.fillRect(0, y - (barHeight / 2), width, barHeight);
            });

            animationFrameId = requestAnimationFrame(renderLoop);
        };

        renderLoop();
        return () => cancelAnimationFrame(animationFrameId);
    }, [profileBins, getHeatmapColor]);

    // Update Canvas Size
    useLayoutEffect(() => {
        const canvas = overlayRef.current?.querySelector('canvas');
        const container = chartContainerRef.current;

        if (canvas && container) {
            const resizeCanvas = () => {
                // Set canvas to full resolution of container
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
        <div className="relative w-full h-full bg-[#0b0b15]"> {/* Main Background */}

            {/* 1. Heatmap Overlay (Background Layer) */}
            <div
                ref={overlayRef}
                className="absolute inset-0 z-0 pointer-events-none"
            >
                <canvas
                    className="w-full h-full"
                    style={{ filter: 'blur(8px)', opacity: 0.8 }} // Strong blur for "Heat Clouds"
                />
            </div>

            {/* 2. Chart (Foreground Layer) */}
            <div
                ref={chartContainerRef}
                className="absolute inset-0 z-10" // z-10 ensures interactivity
            />

            {loading && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm z-20">
                    <RefreshCw className="w-6 h-6 animate-spin text-white" />
                </div>
            )}
        </div>
    );
}
