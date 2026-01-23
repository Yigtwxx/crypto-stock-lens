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

export interface SentimentAnalysis {
    sentiment: 'bullish' | 'bearish' | 'neutral';
    confidence: number;
    reasoning: string;
    historical_context: string;
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

    // Actions
    setNewsItems: (items: NewsItem[]) => void;
    selectNews: (news: NewsItem) => void;
    setChartSymbol: (symbol: string) => void;
    setAnalysis: (analysis: SentimentAnalysis | null) => void;
    setLoadingNews: (loading: boolean) => void;
    setLoadingAnalysis: (loading: boolean) => void;
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

    // Actions
    setNewsItems: (items) => set({ newsItems: items }),

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

    clearSelection: () => set({
        selectedNews: null,
        analysis: null,
        isLoadingAnalysis: false,
    }),
}));
