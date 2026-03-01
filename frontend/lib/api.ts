import { NewsItem, SentimentAnalysis } from '@/store/useStore';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_BASE = API_BASE_URL;

export async function fetchNews(assetType?: string): Promise<NewsItem[]> {
    const params = new URLSearchParams();
    if (assetType) params.append('asset_type', assetType);

    const response = await fetch(`${API_BASE}/api/news?${params}`);
    if (!response.ok) {
        throw new Error('Failed to fetch news');
    }

    const data = await response.json();
    return data.items;
}

export async function analyzeNews(newsId: string, currentPrice?: number): Promise<SentimentAnalysis> {
    const body: { news_id: string; current_price?: number } = { news_id: newsId };
    if (currentPrice !== undefined && currentPrice > 0) {
        body.current_price = currentPrice;
    }

    const response = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        throw new Error('Failed to analyze news');
    }

    return response.json();
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
    const response = await fetch(`${API_BASE}/api/fear-greed`);
    if (!response.ok) {
        throw new Error('Failed to fetch Fear & Greed Index');
    }
    return response.json();
}

export async function fetchMarketOverview(): Promise<MarketOverview> {
    const response = await fetch(`${API_BASE}/api/market-overview`);
    if (!response.ok) {
        throw new Error('Failed to fetch market overview');
    }
    return response.json();
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
    const response = await fetch(`${API_BASE}/api/nasdaq-overview`);
    if (!response.ok) {
        throw new Error('Failed to fetch NASDAQ overview');
    }
    return response.json();
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
    const response = await fetch(`${API_BASE}/api/home/funding-rates`);
    if (!response.ok) throw new Error('Failed to fetch funding rates');
    return response.json();
}

export async function fetchMacroCalendar(): Promise<MacroEvent[]> {
    try {
        const response = await fetch(`${API_BASE}/api/home/macro-calendar`);
        if (!response.ok) return [];
        return await response.json();
    } catch (error) {
        console.error("Error fetching macro calendar:", error);
        return [];
    }
}

export async function fetchLiquidations(): Promise<Liquidation[]> {
    const response = await fetch(`${API_BASE}/api/home/liquidations`);
    if (!response.ok) throw new Error('Failed to fetch liquidations');
    return response.json();
}

export async function fetchOnChainData(): Promise<OnChainData> {
    const response = await fetch(`${API_BASE}/api/home/onchain`);
    if (!response.ok) throw new Error('Failed to fetch on-chain data');
    return response.json();
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
        const res = await fetch(`${API_BASE}/api/home/watchlist`);
        if (!res.ok) return [];
        return await res.json();
    } catch (error) {
        console.error("Error fetching watchlists:", error);
        return [];
    }
}

export async function createWatchlist(name: string, items: { symbol: string, type: 'STOCK' | 'CRYPTO' }[]): Promise<Watchlist[]> {
    try {
        const res = await fetch(`${API_BASE}/api/home/watchlist`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, items })
        });
        if (!res.ok) throw new Error("Failed to create watchlist");
        return await res.json();
    } catch (error) {
        console.error("Error creating watchlist:", error);
        throw error;
    }
}

export async function deleteWatchlist(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/home/watchlist/${id}`, {
        method: "DELETE"
    });
    if (!res.ok) throw new Error("Failed to delete watchlist");
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

export async function fetchAssetDetail(symbol: string, type: 'crypto' | 'stock' = 'crypto'): Promise<AssetDetail> {
    const response = await fetch(`${API_BASE}/api/asset-detail/${symbol}?type=${type}`);
    if (!response.ok) throw new Error(`Failed to fetch asset detail for ${symbol}`);
    return response.json();
}
