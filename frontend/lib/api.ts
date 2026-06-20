import { NewsItem, SentimentAnalysis } from '@/store/useStore';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_BASE = API_BASE_URL;

/** Error thrown by {@link apiFetch} for non-2xx responses, carrying the status. */
export class ApiError extends Error {
    constructor(
        public status: number,
        message: string
    ) {
        super(message);
        this.name = 'ApiError';
    }
}

type ApiFetchOptions = RequestInit & {
    params?: Record<string, string | number | boolean | undefined | null>;
};

/**
 * Thin wrapper around fetch for the Oracle-X backend.
 * - Prepends the API base URL (unless an absolute URL is passed)
 * - Serialises `params` into the query string (skipping nullish values)
 * - Sets a JSON Content-Type only when a body is present
 * - Throws {@link ApiError} on non-2xx responses
 * - Returns parsed JSON (or `undefined` for empty 204 responses)
 */
export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
    const { params, headers, ...init } = options;

    let url = path.startsWith('http') ? path : `${API_BASE}${path}`;
    if (params) {
        const search = new URLSearchParams();
        for (const [key, value] of Object.entries(params)) {
            if (value !== undefined && value !== null && value !== '') {
                search.append(key, String(value));
            }
        }
        const qs = search.toString();
        if (qs) url += `?${qs}`;
    }

    const finalHeaders: Record<string, string> = { ...(headers as Record<string, string>) };
    if (init.body && !finalHeaders['Content-Type']) {
        finalHeaders['Content-Type'] = 'application/json';
    }

    const response = await fetch(url, { ...init, headers: finalHeaders });
    if (!response.ok) {
        throw new ApiError(response.status, `Request to ${path} failed: ${response.status}`);
    }
    if (response.status === 204) {
        return undefined as T;
    }
    return response.json() as Promise<T>;
}

export async function fetchNews(assetType?: string): Promise<NewsItem[]> {
    const data = await apiFetch<{ items: NewsItem[] }>('/api/news', {
        params: { asset_type: assetType },
    });
    return data.items;
}

export async function analyzeNews(newsId: string, currentPrice?: number): Promise<SentimentAnalysis> {
    const body: { news_id: string; current_price?: number } = { news_id: newsId };
    if (currentPrice !== undefined && currentPrice > 0) {
        body.current_price = currentPrice;
    }

    return apiFetch<SentimentAnalysis>('/api/analyze', {
        method: 'POST',
        body: JSON.stringify(body),
    });
}

export async function verifyOnChain(_predictionHash: string): Promise<{ txHash: string }> {
    // On-chain doğrulama henüz uygulanmadı — Faz 3'te smart contract entegrasyonu ile aktif edilecek.
    throw new Error('On-chain verification is not yet implemented. Coming in Phase 3.');
}

/**
 * Fetch current price from Binance API for crypto assets
 * @param symbol - TradingView format symbol (e.g., "BINANCE:BTCUSDT")
 * @returns Current price or null if not available
 */
export async function fetchCurrentPrice(symbol: string): Promise<number | null> {
    try {
        // Extract the trading pair from TradingView symbol format
        // e.g., "BINANCE:BTCUSDT" -> "BTCUSDT"
        const cleanSymbol = symbol.includes(':') ? symbol.split(':')[1] : symbol;

        // For crypto assets, use Binance API
        if (symbol.includes('BINANCE') || cleanSymbol.endsWith('USDT')) {
            const response = await fetch(`https://api.binance.com/api/v3/ticker/price?symbol=${cleanSymbol}`);
            if (response.ok) {
                const data = await response.json();
                return parseFloat(data.price);
            }
        }

        // For stocks, return null (TradingView widget handles stocks, no free API available)
        return null;
    } catch (error) {
        console.error('Failed to fetch current price:', error);
        return null;
    }
}

// Fear & Greed Index types
export interface FearGreedHistory {
    value: number;
    classification: string;
    date: string;
}

export interface FearGreedData {
    value: number;
    classification: string;
    timestamp: string;
    history: FearGreedHistory[];
}

// Market Overview types
export interface CoinData {
    symbol: string;
    name: string;
    logo: string;
    price: number;
    change_24h: number;
    volume_24h: number;
    high_24h: number;
    low_24h: number;
    market_cap: number;
    market_cap_rank: number;
}

export interface MarketStatus {
    status: string;
    message: string;
    color: string;
    next_event: string;
}

export interface MarketOverview {
    coins: CoinData[];
    total_volume_24h: number;
    total_market_cap: number;
    btc_dominance: number;
    eth_dominance?: number;
    active_cryptocurrencies: number;
    fear_greed: FearGreedData;
    timestamp: string;
    market_status?: MarketStatus;
}

export async function fetchFearGreedIndex(): Promise<FearGreedData> {
    return apiFetch<FearGreedData>('/api/fear-greed');
}

export async function fetchMarketOverview(): Promise<MarketOverview> {
    return apiFetch<MarketOverview>('/api/market-overview');
}

export interface NasdaqOverview {
    coins: CoinData[];  // Reusing CoinData for compatibility
    total_volume_24h: number;
    total_market_cap: number;
    btc_dominance: number;  // N/A for stocks
    active_cryptocurrencies: number;
    fear_greed?: {
        value: number;
        classification: string;
        timestamp: string;
    };
    timestamp: string;
}

export async function fetchNasdaqOverview(): Promise<NasdaqOverview> {
    return apiFetch<NasdaqOverview>('/api/nasdaq-overview');
}

// ==========================================
// HOME PAGE TYPES & API
// ==========================================

export interface FundingRate {
    symbol: string;
    rate: number;
    rate_formatted: string;
    index_price: number;
    mark_price: number;
    next_funding_time: number;
}

export interface Liquidation {
    symbol: string;
    side: 'Long' | 'Short';
    price: number;
    amount_usd: number;
    time_ago: string;
    timestamp: number;
}

export interface MacroEvent {
    title: string;
    country: string;
    date: string;
    time: string;
    impact: 'Low' | 'Medium' | 'High';
    forecast: string;
    previous: string;
}

export interface OnChainData {
    active_addresses: {
        btc: number;
        eth: number;
        btc_change_24h: number;
        eth_change_24h: number;
    };
    transactions_24h: {
        btc: number;
        eth: number;
    };
    network_load: {
        eth_gas_gwei: number;
        btc_mempool_size_vbytes: number;
    };
    exchange_flows: {
        btc_net_flow_usd: number;
        eth_net_flow_usd: number;
    };
}

export async function fetchFundingRates(): Promise<FundingRate[]> {
    return apiFetch<FundingRate[]>('/api/home/funding-rates');
}

export async function fetchMacroCalendar(): Promise<MacroEvent[]> {
    try {
        return await apiFetch<MacroEvent[]>('/api/home/macro-calendar');
    } catch (error) {
        console.error('Error fetching macro calendar:', error);
        return [];
    }
}

export async function fetchLiquidations(): Promise<Liquidation[]> {
    return apiFetch<Liquidation[]>('/api/home/liquidations');
}

export async function fetchOnChainData(): Promise<OnChainData> {
    return apiFetch<OnChainData>('/api/home/onchain');
}


// ==========================================
// WATCHLIST
// ==========================================

export interface WatchlistItem {
    symbol: string;
    type: 'STOCK' | 'CRYPTO';
    price?: number;
    change_24h?: number;
    logo?: string;
    name?: string;
}

export interface Watchlist {
    id: string;
    name: string;
    items: WatchlistItem[];
}

export async function fetchWatchlists(): Promise<Watchlist[]> {
    try {
        return await apiFetch<Watchlist[]>('/api/home/watchlist');
    } catch (error) {
        console.error('Error fetching watchlists:', error);
        return [];
    }
}

export async function createWatchlist(
    name: string,
    items: { symbol: string; type: 'STOCK' | 'CRYPTO' }[]
): Promise<Watchlist[]> {
    try {
        return await apiFetch<Watchlist[]>('/api/home/watchlist', {
            method: 'POST',
            body: JSON.stringify({ name, items }),
        });
    } catch (error) {
        console.error('Error creating watchlist:', error);
        throw error;
    }
}

export async function deleteWatchlist(id: string): Promise<void> {
    await apiFetch<void>(`/api/home/watchlist/${id}`, { method: 'DELETE' });
}


// ==========================================
// ASSET DETAIL
// ==========================================

export interface AssetDetail {
    type: 'crypto' | 'stock';
    symbol: string;
    name: string;
    logo: string;
    description: string;

    // Crypto-specific
    categories?: string[];
    genesis_date?: string;
    hashing_algorithm?: string;
    circulating_supply?: number;
    total_supply?: number;
    max_supply?: number | null;
    ath?: number;
    ath_change_percentage?: number;
    ath_date?: string;
    atl?: number;
    atl_change_percentage?: number;
    atl_date?: string;
    fully_diluted_valuation?: number;
    // Crypto community
    twitter_followers?: number;
    reddit_subscribers?: number;
    telegram_channel_user_count?: number;
    // Crypto developer
    github_stars?: number;
    github_forks?: number;
    github_subscribers?: number;
    github_total_issues?: number;
    github_closed_issues?: number;
    github_pull_requests_merged?: number;
    commit_count_4_weeks?: number;
    // Crypto sentiment
    sentiment_votes_up_percentage?: number;
    sentiment_votes_down_percentage?: number;
    watchlist_portfolio_users?: number;

    // Stock-specific
    sector?: string;
    industry?: string;
    country?: string;
    employees?: number;
    website?: string;
    pe_ratio?: number | null;
    dividend_yield?: number | null;
    fifty_two_week_high?: number;
    fifty_two_week_low?: number;
    // Stock financials
    revenue?: number | null;
    net_income?: number | null;
    earnings_per_share?: number | null;
    forward_eps?: number | null;
    forward_pe?: number | null;
    profit_margin?: number | null;
    operating_margin?: number | null;
    beta?: number | null;
    book_value?: number | null;
    price_to_book?: number | null;
    free_cash_flow?: number | null;
    debt_to_equity?: number | null;
    return_on_equity?: number | null;
    // Analyst
    target_high_price?: number | null;
    target_low_price?: number | null;
    target_mean_price?: number | null;
    recommendation?: string;
    // Moving averages
    fifty_day_average?: number | null;
    two_hundred_day_average?: number | null;

    // Common market data
    market_cap_rank?: number;
    price: number;
    market_cap: number;
    total_volume: number;
    change_24h: number;
    change_7d?: number;
    change_30d?: number;
    change_1y?: number;
    high_24h: number;
    low_24h: number;

    links: Record<string, string>;
    timestamp: string;
}

export async function fetchAssetDetail(
    symbol: string,
    type: 'crypto' | 'stock' = 'crypto'
): Promise<AssetDetail> {
    return apiFetch<AssetDetail>(`/api/asset-detail/${symbol}`, { params: { type } });
}


// ==========================================
// ANALYSIS REPORTS & NOTES
// ==========================================

export type TimeFrame = 'daily' | 'weekly' | 'monthly';

export interface AnalysisReport {
    content: string;
    timestamp: string;
}

export interface Note {
    id: string;
    title: string;
    content: string;
    date: string;
}

export async function fetchAnalysisReport(timeframe: TimeFrame): Promise<AnalysisReport> {
    return apiFetch<AnalysisReport>(`/api/analysis/report/${timeframe}`);
}

export async function generateAnalysisReport(timeframe: TimeFrame): Promise<AnalysisReport> {
    return apiFetch<AnalysisReport>(`/api/analysis/generate/${timeframe}`, { method: 'POST' });
}

export async function fetchNotes(): Promise<Note[]> {
    return apiFetch<Note[]>('/api/analysis/notes');
}

export async function createNote(title: string, content: string): Promise<Note[]> {
    return apiFetch<Note[]>('/api/analysis/notes', {
        method: 'POST',
        body: JSON.stringify({ title, content }),
    });
}

export async function deleteNote(id: string): Promise<Note[]> {
    return apiFetch<Note[]>(`/api/analysis/notes/${id}`, { method: 'DELETE' });
}
