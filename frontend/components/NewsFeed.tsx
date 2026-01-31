'use client';

import { useEffect, useState } from 'react';
import { useStore, NewsItem } from '@/store/useStore';
import { fetchNews, analyzeNews, fetchCurrentPrice } from '@/lib/api';
import {
    Newspaper,
    TrendingUp,
    Bitcoin,
    Clock,
    RefreshCw,
    Filter
} from 'lucide-react';

export default function NewsFeed() {
    const {
        newsItems,
        selectedNews,
        isLoadingNews,
        setNewsItems,
        selectNews,
        setLoadingNews,
        setAnalysis,
        setLoadingAnalysis
    } = useStore();

    const [activeFilter, setActiveFilter] = useState<'all' | 'stock' | 'crypto'>('all');

    useEffect(() => {
        loadNews(false); // Initial load with loading state

        // Auto-refresh every 15 seconds (silent, no loading spinner)
        const interval = setInterval(() => {
            loadNews(true); // Silent refresh
        }, 15000);

        return () => clearInterval(interval);
    }, []);

    const loadNews = async (silent: boolean = false) => {
        if (!silent) {
            setLoadingNews(true);
        }
        try {
            const items = await fetchNews();

            // Stable sort: by published_at (newest first), then by ID for consistency
            const sortedItems = [...items].sort((a, b) => {
                const dateA = new Date(a.published_at).getTime();
                const dateB = new Date(b.published_at).getTime();

                // Primary sort: by date (newest first)
                if (dateB !== dateA) {
                    return dateB - dateA;
                }

                // Secondary sort: by ID for stable ordering when dates are equal
                return a.id.localeCompare(b.id);
            });

            setNewsItems(sortedItems);
        } catch (error) {
            console.error('Failed to load news:', error);
        } finally {
            if (!silent) {
                setLoadingNews(false);
            }
        }
    };

    const handleNewsClick = async (news: NewsItem) => {
        selectNews(news);

        // Trigger analysis with current price
        try {
            // Fetch current price for more accurate technical analysis
            const currentPrice = await fetchCurrentPrice(news.symbol);

            // Analyze with current price context
            const analysis = await analyzeNews(news.id, currentPrice ?? undefined);
            setAnalysis(analysis);
        } catch (error) {
            console.error('Failed to analyze news:', error);
            // Set a fallback analysis so UI shows something
            setAnalysis({
                sentiment: 'neutral',
                confidence: 0.5,
                reasoning: 'Analiz şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin.',
                historical_context: 'Bağlantı hatası veya sunucu meşgul olabilir.',
            });
        }
    };

    const formatTime = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

        if (diffMinutes < 1) return 'Just now';
        if (diffMinutes < 60) return `${diffMinutes}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${Math.floor(diffHours / 24)}d ago`;
    };

    // Filter news items based on active filter, then ensure stable sort
    const filteredNews = newsItems
        .filter(news => {
            if (activeFilter === 'all') return true;
            return news.asset_type === activeFilter;
        })
        .sort((a, b) => {
            const dateA = new Date(a.published_at).getTime();
            const dateB = new Date(b.published_at).getTime();

            // Primary sort: by date (newest first)
            if (dateB !== dateA) {
                return dateB - dateA;
            }

            // Secondary sort: by ID for stable ordering
            return a.id.localeCompare(b.id);
        });

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="p-4 border-b border-oracle-border flex items-center justify-between bg-gradient-to-r from-oracle-dark via-oracle-dark to-indigo/5">
                <div className="flex items-center gap-2">
                    <Newspaper className="w-5 h-5 text-indigo" />
                    <h2 className="font-semibold bg-gradient-to-r from-white to-indigo bg-clip-text text-transparent">The Feed</h2>
                </div>
                <button
                    onClick={() => loadNews(false)}
                    className="p-2 rounded-lg hover:bg-indigo/10 transition-colors"
                    title="Refresh"
                >
                    <RefreshCw className={`w-4 h-4 text-gray-400 hover:text-indigo ${isLoadingNews ? 'animate-spin' : ''}`} />
                </button>
            </div>

            {/* Filter Tabs */}
            <div className="p-3 border-b border-oracle-border flex gap-2">
                <button
                    onClick={() => setActiveFilter('all')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${activeFilter === 'all'
                        ? 'bg-violet/20 text-violet border border-violet/30'
                        : 'text-gray-400 hover:bg-violet/10 hover:text-violet'
                        }`}
                >
                    <Filter className="w-3.5 h-3.5" />
                    All
                </button>
                <button
                    onClick={() => setActiveFilter('stock')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${activeFilter === 'stock'
                        ? 'bg-stock/20 text-stock border border-stock/30'
                        : 'text-gray-400 hover:bg-stock/10 hover:text-stock'
                        }`}
                >
                    <TrendingUp className="w-3.5 h-3.5" />
                    Stocks
                </button>
                <button
                    onClick={() => setActiveFilter('crypto')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${activeFilter === 'crypto'
                        ? 'bg-crypto/20 text-crypto border border-crypto/30'
                        : 'text-gray-400 hover:bg-crypto/10 hover:text-crypto'
                        }`}
                >
                    <Bitcoin className="w-3.5 h-3.5" />
                    Crypto
                </button>
            </div>

            {/* News List */}
            <div className="flex-1 overflow-y-auto">
                {isLoadingNews ? (
                    // Loading skeleton
                    <div className="p-4 space-y-3">
                        {[...Array(5)].map((_, i) => (
                            <div key={i} className="p-4 rounded-lg border border-oracle-border">
                                <div className="h-4 w-3/4 shimmer rounded mb-2"></div>
                                <div className="h-3 w-full shimmer rounded mb-2"></div>
                                <div className="h-3 w-1/2 shimmer rounded"></div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="p-3 space-y-2">
                        {filteredNews.map((news) => (
                            <article
                                key={news.id}
                                onClick={() => handleNewsClick(news)}
                                className={`news-item p-4 rounded-lg border cursor-pointer ${selectedNews?.id === news.id
                                    ? 'selected border-oracle-accent bg-oracle-accent/10'
                                    : 'border-oracle-border hover:border-oracle-accent/50'
                                    }`}
                            >
                                {/* Asset Badge */}
                                <div className="flex items-center gap-2 mb-2">
                                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${news.asset_type === 'crypto'
                                        ? 'bg-crypto/20 text-crypto'
                                        : 'bg-stock/20 text-stock'
                                        }`}>
                                        {news.symbol.split(':')[1]}
                                    </span>
                                    <span className="flex items-center gap-1 text-xs text-gray-500">
                                        <Clock className="w-3 h-3" />
                                        {formatTime(news.published_at)}
                                    </span>
                                </div>

                                {/* Title */}
                                <h3 className="text-sm font-medium text-white leading-snug mb-1.5">
                                    {news.title}
                                </h3>

                                {/* Summary */}
                                <p className="text-xs text-gray-400 line-clamp-2">
                                    {news.summary}
                                </p>

                                {/* Source */}
                                <div className="mt-2 text-xs text-gray-500">
                                    {news.source}
                                </div>
                            </article>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
