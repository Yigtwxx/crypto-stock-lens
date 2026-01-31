import { create } from 'zustand';

export interface NewsItem {
    id: string;
    title: string;
    summary: string;
    source: string;
    published_at: string;
    symbol: string;
    asset_type: 'stock' | 'crypto';
    url?: string;
}

export interface TechnicalSignals {
    rsi_signal: string;
    support_levels: string[];
    resistance_levels: string[];
    target_price: string;
}

export interface SentimentAnalysis {
    sentiment: 'bullish' | 'bearish' | 'neutral';
    confidence: number;
    reasoning: string;
    historical_context: string;
    technical_signals?: TechnicalSignals;
    prediction_hash?: string;
    tx_hash?: string;
}

interface OracleStore {
    // News state
    newsItems: NewsItem[];
    selectedNews: NewsItem | null;
    isLoadingNews: boolean;

    // Chart state
    chartSymbol: string;

    // Analysis state
    analysis: SentimentAnalysis | null;
    isLoadingAnalysis: boolean;

    // Current price from chart
    currentPrice: number | null;

    // Actions
    setNewsItems: (items: NewsItem[]) => void;
    selectNews: (news: NewsItem) => void;
    setChartSymbol: (symbol: string) => void;
    setAnalysis: (analysis: SentimentAnalysis | null) => void;
    setLoadingNews: (loading: boolean) => void;
    setLoadingAnalysis: (loading: boolean) => void;
    setCurrentPrice: (price: number) => void;
    clearSelection: () => void;
}

export const useStore = create<OracleStore>((set) => ({
    // Initial state
    newsItems: [],
    selectedNews: null,
    isLoadingNews: false,
    chartSymbol: 'BINANCE:BTCUSDT',
    analysis: null,
    isLoadingAnalysis: false,
    currentPrice: null,

    // Actions - setNewsItems with guaranteed sorted order
    setNewsItems: (items) => {
        // Sort by published_at (newest first) using ISO string comparison
        // This is more stable than Date parsing
        const sortedItems = [...items].sort((a, b) => {
            // ISO strings can be compared lexicographically
            const dateCompare = b.published_at.localeCompare(a.published_at);
            if (dateCompare !== 0) return dateCompare;
            // Secondary sort by ID for stability
            return a.id.localeCompare(b.id);
        });
        set({ newsItems: sortedItems });
    },

    selectNews: (news) => set({
        selectedNews: news,
        chartSymbol: news.symbol,
        analysis: null, // Clear previous analysis
        isLoadingAnalysis: true,
    }),

    setChartSymbol: (symbol) => set({ chartSymbol: symbol }),

    setAnalysis: (analysis) => set({
        analysis,
        isLoadingAnalysis: false,
    }),

    setLoadingNews: (loading) => set({ isLoadingNews: loading }),

    setLoadingAnalysis: (loading) => set({ isLoadingAnalysis: loading }),

    setCurrentPrice: (price) => set({ currentPrice: price }),

    clearSelection: () => set({
        selectedNews: null,
        analysis: null,
        isLoadingAnalysis: false,
    }),
}));
