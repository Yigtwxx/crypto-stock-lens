import { NewsItem, SentimentAnalysis } from '@/store/useStore';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

export async function verifyOnChain(predictionHash: string): Promise<{ txHash: string }> {
    // Placeholder for blockchain verification
    // Will be implemented in Phase 3
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({ txHash: `0x${predictionHash.slice(0, 64)}` });
        }, 2000);
    });
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
