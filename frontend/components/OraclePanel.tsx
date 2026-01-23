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
    LinkIcon
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

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="p-4 border-b border-oracle-border flex items-center gap-2">
                <Brain className="w-5 h-5 text-oracle-accent" />
                <h2 className="font-semibold text-white">The Oracle</h2>
                <Sparkles className="w-4 h-4 text-purple-400 ml-1" />
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
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
                        <div className={`p-4 rounded-xl border ${analysis.sentiment === 'bullish'
                                ? 'bg-oracle-bullish/10 border-oracle-bullish/30 glow-bullish'
                                : analysis.sentiment === 'bearish'
                                    ? 'bg-oracle-bearish/10 border-oracle-bearish/30 glow-bearish'
                                    : 'bg-oracle-neutral/10 border-oracle-neutral/30'
                            }`}>
                            <div className="flex items-center justify-between mb-3">
                                <div className={`flex items-center gap-2 ${getSentimentColor(analysis.sentiment)}`}>
                                    {getSentimentIcon(analysis.sentiment)}
                                    <span className="text-lg font-bold capitalize">{analysis.sentiment}</span>
                                </div>
                                <span className={`badge-${analysis.sentiment} px-3 py-1 rounded-full text-sm font-semibold`}>
                                    {Math.round(analysis.confidence * 100)}% Confidence
                                </span>
                            </div>
                        </div>

                        {/* Reasoning */}
                        <div className="p-4 rounded-xl bg-oracle-card border border-oracle-border">
                            <div className="flex items-center gap-2 mb-3">
                                <Target className="w-4 h-4 text-oracle-accent" />
                                <h4 className="font-medium text-white">Analysis</h4>
                            </div>
                            <p className="text-sm text-gray-300 leading-relaxed">
                                {analysis.reasoning}
                            </p>
                        </div>

                        {/* Historical Context */}
                        <div className="p-4 rounded-xl bg-oracle-card border border-oracle-border">
                            <div className="flex items-center gap-2 mb-3">
                                <History className="w-4 h-4 text-purple-400" />
                                <h4 className="font-medium text-white">Historical Context</h4>
                            </div>
                            <p className="text-sm text-gray-300 leading-relaxed">
                                {analysis.historical_context}
                            </p>
                        </div>

                        {/* Prediction Hash */}
                        {analysis.prediction_hash && (
                            <div className="p-3 rounded-lg bg-oracle-darker border border-oracle-border">
                                <p className="text-xs text-gray-500 mb-1">Prediction Hash (SHA-256)</p>
                                <p className="text-xs font-mono text-gray-400 break-all">
                                    {analysis.prediction_hash}
                                </p>
                            </div>
                        )}
                    </div>
                ) : null}
            </div>

            {/* Blockchain Verification Footer */}
            {analysis && (
                <div className="p-4 border-t border-oracle-border bg-oracle-dark/50">
                    {txHash ? (
                        <div className="flex items-center gap-2 p-3 rounded-lg bg-oracle-bullish/10 border border-oracle-bullish/30">
                            <CheckCircle2 className="w-5 h-5 text-oracle-bullish" />
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-oracle-bullish">Verified on Chain</p>
                                <p className="text-xs text-gray-400 truncate font-mono">{txHash}</p>
                            </div>
                            <a
                                href={`https://sepolia.etherscan.io/tx/${txHash}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-2 rounded-lg hover:bg-oracle-card transition-colors"
                            >
                                <ExternalLink className="w-4 h-4 text-gray-400" />
                            </a>
                        </div>
                    ) : (
                        <button
                            onClick={handleVerifyOnChain}
                            disabled={isVerifying}
                            className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-oracle-accent to-purple-600 text-white font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                        >
                            {isVerifying ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Verifying...
                                </>
                            ) : (
                                <>
                                    <Shield className="w-5 h-5" />
                                    Verify on Blockchain
                                    <LinkIcon className="w-4 h-4 ml-1" />
                                </>
                            )}
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}
