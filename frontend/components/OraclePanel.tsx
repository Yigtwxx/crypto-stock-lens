'use client';

import { useState } from 'react';
import { useStore } from '@/store/useStore';
import { verifyOnChain } from '@/lib/api';
import {
    Brain,
    TrendingUp,
    TrendingDown,
    Minus,
    Shield,
    ExternalLink,
    Loader2,
    History,
    Target,
    Sparkles,
    CheckCircle2,
    LinkIcon,
    Activity
} from 'lucide-react';

export default function OraclePanel() {
    const { selectedNews, analysis, isLoadingAnalysis } = useStore();
    const [isVerifying, setIsVerifying] = useState(false);
    const [txHash, setTxHash] = useState<string | null>(null);

    const handleVerifyOnChain = async () => {
        if (!analysis?.prediction_hash) return;

        setIsVerifying(true);
        try {
            const result = await verifyOnChain(analysis.prediction_hash);
            setTxHash(result.txHash);
        } catch (error) {
            console.error('Verification failed:', error);
        } finally {
            setIsVerifying(false);
        }
    };

    const getSentimentIcon = (sentiment: string) => {
        switch (sentiment) {
            case 'bullish':
                return <TrendingUp className="w-5 h-5" />;
            case 'bearish':
                return <TrendingDown className="w-5 h-5" />;
            default:
                return <Minus className="w-5 h-5" />;
        }
    };

    const getSentimentColor = (sentiment: string) => {
        switch (sentiment) {
            case 'bullish':
                return 'text-oracle-bullish';
            case 'bearish':
                return 'text-oracle-bearish';
            default:
                return 'text-oracle-neutral';
        }
    };

    const getTheme = (sentiment: string) => {
        switch (sentiment) {
            case 'bullish':
                return {
                    text: 'text-oracle-bullish',
                    border: 'border-oracle-bullish/30',
                    bg: 'bg-oracle-bullish/10',
                    icon: 'text-oracle-bullish',
                    glow: 'glow-bullish'
                };
            case 'bearish':
                return {
                    text: 'text-oracle-bearish',
                    border: 'border-oracle-bearish/30',
                    bg: 'bg-oracle-bearish/10',
                    icon: 'text-oracle-bearish',
                    glow: 'glow-bearish'
                };
            default:
                return {
                    text: 'text-oracle-neutral',
                    border: 'border-oracle-neutral/30',
                    bg: 'bg-oracle-neutral/10',
                    icon: 'text-oracle-neutral',
                    glow: ''
                };
        }
    };

    const theme = analysis ? getTheme(analysis.sentiment) : getTheme('neutral');

    return (
        <div className="flex flex-col h-full">
            {/* Header - Fixed height to align with other panels */}
            <div className="h-14 px-4 border-b border-oracle-border flex items-center gap-2 bg-gradient-to-r from-oracle-dark via-oracle-dark to-pink/5">
                <Brain className="w-5 h-5 text-pink" />
                <h2 className="font-semibold bg-gradient-to-r from-white to-pink bg-clip-text text-transparent">The Oracle</h2>
                <Sparkles className="w-4 h-4 text-pink ml-1 animate-pulse" />
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                {!selectedNews ? (
                    // Empty State
                    <div className="h-full flex flex-col items-center justify-center text-center px-6">
                        <div className="w-16 h-16 rounded-2xl bg-oracle-card border border-oracle-border flex items-center justify-center mb-4">
                            <Brain className="w-8 h-8 text-gray-600" />
                        </div>
                        <h3 className="text-lg font-medium text-gray-400 mb-2">
                            Select a News Item
                        </h3>
                        <p className="text-sm text-gray-500 leading-relaxed">
                            Click on any news article in The Feed to receive AI-powered sentiment analysis with blockchain verification.
                        </p>
                    </div>
                ) : isLoadingAnalysis ? (
                    // Loading State
                    <div className="h-full flex flex-col items-center justify-center">
                        <div className="relative">
                            <div className="w-20 h-20 rounded-full border-4 border-oracle-card border-t-oracle-accent animate-spin"></div>
                            <Brain className="w-8 h-8 text-oracle-accent absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                        </div>
                        <p className="mt-6 text-gray-400 animate-pulse">Analyzing with RAG + LLM...</p>
                        <p className="text-sm text-gray-500 mt-2">Retrieving historical context...</p>
                    </div>
                ) : analysis ? (
                    // Analysis Results
                    <div className="space-y-4">
                        {/* Selected Article */}
                        <div className="p-3 rounded-lg bg-oracle-card/50 border border-oracle-border">
                            <p className="text-xs text-gray-500 mb-1">Analyzing:</p>
                            <p className="text-sm text-white font-medium line-clamp-2">
                                {selectedNews.title}
                            </p>
                        </div>

                        {/* Sentiment Card */}
                        <div className={`p-4 rounded-xl border ${theme.bg} ${theme.border} ${theme.glow}`}>
                            <div className="flex items-center justify-between mb-3">
                                <div className={`flex items-center gap-2 ${theme.text}`}>
                                    {getSentimentIcon(analysis.sentiment)}
                                    <span className="text-lg font-bold capitalize">{analysis.sentiment}</span>
                                </div>
                                <span className={`badge-${analysis.sentiment} px-3 py-1 rounded-full text-sm font-semibold`}>
                                    {Math.round(analysis.confidence * 100)}% Confidence
                                </span>
                            </div>
                        </div>

                        {/* Reasoning */}
                        <div className={`p-4 rounded-xl bg-oracle-card border border-oracle-border`}>
                            <div className="flex items-center gap-2 mb-3">
                                <Target className={`w-4 h-4 ${theme.icon}`} />
                                <h4 className={`font-medium ${theme.text}`}>Analysis</h4>
                            </div>
                            <p className="text-sm text-gray-300 leading-relaxed">
                                {analysis.reasoning}
                            </p>
                        </div>

                        {/* Historical Context */}
                        <div className={`p-4 rounded-xl bg-oracle-card border border-oracle-border`}>
                            <div className="flex items-center gap-2 mb-3">
                                <History className={`w-4 h-4 ${theme.icon}`} />
                                <h4 className={`font-medium ${theme.text}`}>Historical Context</h4>
                            </div>
                            <p className="text-sm text-gray-300 leading-relaxed">
                                {analysis.historical_context}
                            </p>
                        </div>

                        {/* Technical Analysis */}
                        {analysis.technical_signals && (
                            <div className={`p-4 rounded-xl bg-oracle-card border border-oracle-border`}>
                                <div className="flex items-center gap-2 mb-3">
                                    <Activity className={`w-4 h-4 ${theme.icon}`} />
                                    <h4 className={`font-medium ${theme.text}`}>Technical Analysis</h4>
                                </div>
                                <div className="space-y-3">
                                    {/* RSI */}
                                    <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                                        <span className="text-gray-400">RSI Signal</span>
                                        <span className="text-white font-medium">{analysis.technical_signals.rsi_signal}</span>
                                    </div>

                                    {/* Supports */}
                                    <div className="text-sm">
                                        <span className="text-gray-400 block mb-1">Support Levels</span>
                                        <div className="flex gap-2">
                                            {analysis.technical_signals.support_levels.map((level, i) => (
                                                <span key={i} className="px-2 py-0.5 bg-green-500/20 text-green-400 rounded text-xs font-mono">
                                                    {level}
                                                </span>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Resistances */}
                                    <div className="text-sm">
                                        <span className="text-gray-400 block mb-1">Resistance Levels</span>
                                        <div className="flex gap-2">
                                            {analysis.technical_signals.resistance_levels.map((level, i) => (
                                                <span key={i} className="px-2 py-0.5 bg-red-500/20 text-red-400 rounded text-xs font-mono">
                                                    {level}
                                                </span>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Target */}
                                    {analysis.technical_signals.target_price && (
                                        <div className="mt-2 pt-2 border-t border-white/5">
                                            <span className="text-xs text-gray-500 block mb-1">Target Price</span>
                                            <span className={`font-mono font-bold ${theme.text}`}>
                                                {analysis.technical_signals.target_price}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Trading Signals - Multi Timeframe */}
                        <div className={`p-4 rounded-xl bg-oracle-card border border-oracle-border`}>
                            <div className="flex items-center gap-2 mb-4">
                                <TrendingUp className={`w-4 h-4 ${theme.icon}`} />
                                <h4 className={`font-medium ${theme.text}`}>Trading Signals</h4>
                            </div>

                            <div className="space-y-3">
                                {/* Short Term */}
                                <div className="flex items-center justify-between p-3 rounded-lg bg-oracle-darker border border-oracle-border">
                                    <div className="flex flex-col">
                                        <span className="text-sm font-medium text-white">Kısa Vadeli</span>
                                        <span className="text-xs text-gray-500">1-7 Gün</span>
                                    </div>
                                    <span className={`px-3 py-1.5 rounded-full text-xs font-bold uppercase ${analysis.sentiment === 'bullish'
                                        ? 'bg-oracle-bullish/20 text-oracle-bullish border border-oracle-bullish/30'
                                        : analysis.sentiment === 'bearish'
                                            ? 'bg-oracle-bearish/20 text-oracle-bearish border border-oracle-bearish/30'
                                            : 'bg-oracle-neutral/20 text-oracle-neutral border border-oracle-neutral/30'
                                        }`}>
                                        {analysis.sentiment === 'bullish' ? '🟢 BUY' :
                                            analysis.sentiment === 'bearish' ? '🔴 SELL' : '🟡 HOLD'}
                                    </span>
                                </div>

                                {/* Medium Term */}
                                <div className="flex items-center justify-between p-3 rounded-lg bg-oracle-darker border border-oracle-border">
                                    <div className="flex flex-col">
                                        <span className="text-sm font-medium text-white">Orta Vadeli</span>
                                        <span className="text-xs text-gray-500">1-4 Hafta</span>
                                    </div>
                                    <span className={`px-3 py-1.5 rounded-full text-xs font-bold uppercase ${analysis.confidence >= 0.7 && analysis.sentiment === 'bullish'
                                        ? 'bg-oracle-bullish/20 text-oracle-bullish border border-oracle-bullish/30'
                                        : analysis.confidence >= 0.7 && analysis.sentiment === 'bearish'
                                            ? 'bg-oracle-bearish/20 text-oracle-bearish border border-oracle-bearish/30'
                                            : 'bg-oracle-neutral/20 text-oracle-neutral border border-oracle-neutral/30'
                                        }`}>
                                        {analysis.confidence >= 0.7 && analysis.sentiment === 'bullish' ? '🟢 BUY' :
                                            analysis.confidence >= 0.7 && analysis.sentiment === 'bearish' ? '🔴 SELL' : '🟡 HOLD'}
                                    </span>
                                </div>

                                {/* Long Term */}
                                <div className="flex items-center justify-between p-3 rounded-lg bg-oracle-darker border border-oracle-border">
                                    <div className="flex flex-col">
                                        <span className="text-sm font-medium text-white">Uzun Vadeli</span>
                                        <span className="text-xs text-gray-500">1-6 Ay</span>
                                    </div>
                                    <span className={`px-3 py-1.5 rounded-full text-xs font-bold uppercase ${analysis.confidence >= 0.8 && analysis.sentiment === 'bullish'
                                        ? 'bg-oracle-bullish/20 text-oracle-bullish border border-oracle-bullish/30'
                                        : analysis.confidence >= 0.8 && analysis.sentiment === 'bearish'
                                            ? 'bg-oracle-bearish/20 text-oracle-bearish border border-oracle-bearish/30'
                                            : 'bg-oracle-neutral/20 text-oracle-neutral border border-oracle-neutral/30'
                                        }`}>
                                        {analysis.confidence >= 0.8 && analysis.sentiment === 'bullish' ? '🟢 BUY' :
                                            analysis.confidence >= 0.8 && analysis.sentiment === 'bearish' ? '🔴 SELL' : '🟡 HOLD'}
                                    </span>
                                </div>
                            </div>

                            {/* Disclaimer */}
                            <p className="text-[10px] text-gray-600 mt-3 text-center italic">
                                Bu sinyaller yatırım tavsiyesi değildir.
                            </p>
                        </div>
                    </div>
                ) : null}
            </div>
        </div>
    );
}
