'use client';

import { useEffect } from 'react';
import { useStore, NewsItem } from '@/store/useStore';
import { fetchNews, analyzeNews } from '@/lib/api';
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

    useEffect(() => {
        loadNews(false); // Initial load with loading state

        // Auto-refresh every 5 seconds (silent, no loading spinner)
        const interval = setInterval(() => {
            loadNews(true); // Silent refresh
        }, 5000);

        return () => clearInterval(interval);
    }, []);

    const loadNews = async (silent: boolean = false) => {
        if (!silent) {
            setLoadingNews(true);
        }
        try {
            const items = await fetchNews();
            setNewsItems(items);
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

        // Trigger analysis
        try {
            const analysis = await analyzeNews(news.id);
            setAnalysis(analysis);
        } catch (error) {
            console.error('Failed to analyze news:', error);
            setLoadingAnalysis(false);
        }
    };

    const formatTime = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

        if (diffHours < 1) return 'Just now';
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${Math.floor(diffHours / 24)}d ago`;
    };

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="p-4 border-b border-oracle-border flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Newspaper className="w-5 h-5 text-oracle-accent" />
                    <h2 className="font-semibold text-white">The Feed</h2>
                </div>
                <button
                    onClick={() => loadNews(false)}
                    className="p-2 rounded-lg hover:bg-oracle-card transition-colors"
                    title="Refresh"
                >
                    <RefreshCw className={`w-4 h-4 text-gray-400 ${isLoadingNews ? 'animate-spin' : ''}`} />
                </button>
            </div>

            {/* Filter Tabs */}
            <div className="p-3 border-b border-oracle-border flex gap-2">
                <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-oracle-accent/20 text-oracle-accent text-sm font-medium">
                    <Filter className="w-3.5 h-3.5" />
                    All
                </button>
                <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-oracle-card text-gray-400 text-sm transition-colors">
                    <TrendingUp className="w-3.5 h-3.5" />
                    Stocks
                </button>
                <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-oracle-card text-gray-400 text-sm transition-colors">
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
                        {newsItems.map((news) => (
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
                                        ? 'bg-purple-500/20 text-purple-400'
                                        : 'bg-blue-500/20 text-blue-400'
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
