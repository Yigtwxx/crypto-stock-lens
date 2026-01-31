import { create } from 'zustand';
import { persist } from 'zustand/middleware';

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

// Price Alert Types
export interface PriceAlert {
    id: string;
    symbol: string;
    displaySymbol: string;
    targetPrice: number;
    condition: 'above' | 'below';
    isActive: boolean;
    isTriggered: boolean;
    createdAt: string;
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

    // Price Alerts state
    priceAlerts: PriceAlert[];
    isAlertModalOpen: boolean;

    // Actions
    setNewsItems: (items: NewsItem[]) => void;
    selectNews: (news: NewsItem) => void;
    setChartSymbol: (symbol: string) => void;
    setAnalysis: (analysis: SentimentAnalysis | null) => void;
    setLoadingNews: (loading: boolean) => void;
    setLoadingAnalysis: (loading: boolean) => void;
    setCurrentPrice: (price: number) => void;
    clearSelection: () => void;

    // Price Alert Actions
    addAlert: (alert: Omit<PriceAlert, 'id' | 'isActive' | 'isTriggered' | 'createdAt'>) => void;
    removeAlert: (id: string) => void;
    triggerAlert: (id: string) => void;
    toggleAlertModal: (open: boolean) => void;
}

export const useStore = create<OracleStore>()(
    persist(
        (set, get) => ({
            // Initial state
            newsItems: [],
            selectedNews: null,
            isLoadingNews: false,
            chartSymbol: 'BINANCE:BTCUSDT',
            analysis: null,
            isLoadingAnalysis: false,
            currentPrice: null,
            priceAlerts: [],
            isAlertModalOpen: false,

            // Actions - setNewsItems with guaranteed sorted order
            setNewsItems: (items) => {
                const sortedItems = [...items].sort((a, b) => {
                    const dateCompare = b.published_at.localeCompare(a.published_at);
                    if (dateCompare !== 0) return dateCompare;
                    return a.id.localeCompare(b.id);
                });
                set({ newsItems: sortedItems });
            },

            selectNews: (news) => set({
                selectedNews: news,
                chartSymbol: news.symbol,
                analysis: null,
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

            // Price Alert Actions
            addAlert: (alertData) => {
                const newAlert: PriceAlert = {
                    ...alertData,
                    id: `alert_${Date.now()}`,
                    isActive: true,
                    isTriggered: false,
                    createdAt: new Date().toISOString(),
                };
                set((state) => ({
                    priceAlerts: [...state.priceAlerts, newAlert],
                }));
            },

            removeAlert: (id) => {
                set((state) => ({
                    priceAlerts: state.priceAlerts.filter((a) => a.id !== id),
                }));
            },

            triggerAlert: (id) => {
                set((state) => ({
                    priceAlerts: state.priceAlerts.map((a) =>
                        a.id === id ? { ...a, isTriggered: true, isActive: false } : a
                    ),
                }));
            },

            toggleAlertModal: (open) => set({ isAlertModalOpen: open }),
        }),
        {
            name: 'oracle-x-storage',
            partialize: (state) => ({ priceAlerts: state.priceAlerts }),
        }
    )
);
