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

export async function analyzeNews(newsId: string): Promise<SentimentAnalysis> {
    const response = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ news_id: newsId }),
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
