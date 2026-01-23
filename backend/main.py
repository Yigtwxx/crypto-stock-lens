"""
Oracle-X Backend API
FastAPI server providing news feeds, AI analysis, and blockchain verification.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import random
import hashlib

from models.schemas import NewsItem, NewsResponse, AnalysisRequest, SentimentAnalysis

app = FastAPI(
    title="Oracle-X API",
    description="Financial Intelligence Terminal Backend",
    version="1.0.0"
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock news data for development
MOCK_NEWS: list[NewsItem] = [
    NewsItem(
        id="news_001",
        title="Bitcoin Surges Past $105K as Institutional Demand Grows",
        summary="Major financial institutions increase BTC holdings, driving unprecedented rally.",
        source="CryptoNews",
        published_at=datetime.now() - timedelta(hours=1),
        symbol="BINANCE:BTCUSDT",
        asset_type="crypto",
        url="https://example.com/btc-surge"
    ),
    NewsItem(
        id="news_002",
        title="Ethereum 2.0 Staking Rewards Hit All-Time High",
        summary="ETH staking yields reach 8.2% as network activity increases.",
        source="DeFi Daily",
        published_at=datetime.now() - timedelta(hours=2),
        symbol="BINANCE:ETHUSDT",
        asset_type="crypto",
        url="https://example.com/eth-staking"
    ),
    NewsItem(
        id="news_003",
        title="Apple Announces Revolutionary AI Chip for iPhone 17",
        summary="New A19 Bionic chip promises 3x faster on-device AI processing.",
        source="TechCrunch",
        published_at=datetime.now() - timedelta(hours=3),
        symbol="NASDAQ:AAPL",
        asset_type="stock",
        url="https://example.com/apple-ai"
    ),
    NewsItem(
        id="news_004",
        title="Tesla Cybertruck Deliveries Exceed 500K Units in Q4",
        summary="Record-breaking quarter as Cybertruck becomes best-selling electric truck.",
        source="Electrek",
        published_at=datetime.now() - timedelta(hours=4),
        symbol="NASDAQ:TSLA",
        asset_type="stock",
        url="https://example.com/tesla-cybertruck"
    ),
    NewsItem(
        id="news_005",
        title="Microsoft Azure AI Revenue Doubles Year-Over-Year",
        summary="Cloud AI services drive massive growth as enterprise adoption accelerates.",
        source="Bloomberg",
        published_at=datetime.now() - timedelta(hours=5),
        symbol="NASDAQ:MSFT",
        asset_type="stock",
        url="https://example.com/msft-azure"
    ),
    NewsItem(
        id="news_006",
        title="Solana Network Processes 100K TPS in Stress Test",
        summary="New optimization upgrades push Solana to unprecedented transaction speeds.",
        source="The Block",
        published_at=datetime.now() - timedelta(hours=6),
        symbol="BINANCE:SOLUSDT",
        asset_type="crypto",
        url="https://example.com/solana-tps"
    ),
    NewsItem(
        id="news_007",
        title="NVIDIA Unveils Next-Gen H200 AI Accelerator",
        summary="New GPU delivers 2x inference performance for large language models.",
        source="AnandTech",
        published_at=datetime.now() - timedelta(hours=7),
        symbol="NASDAQ:NVDA",
        asset_type="stock",
        url="https://example.com/nvidia-h200"
    ),
    NewsItem(
        id="news_008",
        title="XRP Sees Major Exchange Listings After SEC Victory",
        summary="Multiple major exchanges re-list XRP following regulatory clarity.",
        source="CoinDesk",
        published_at=datetime.now() - timedelta(hours=8),
        symbol="BINANCE:XRPUSDT",
        asset_type="crypto",
        url="https://example.com/xrp-listings"
    ),
]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Oracle-X API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/news", response_model=NewsResponse)
async def get_news(
    asset_type: str | None = None,
    limit: int = 10
):
    """
    Fetch latest news items.
    
    Args:
        asset_type: Filter by "stock" or "crypto" (optional)
        limit: Maximum number of items to return
    
    Returns:
        List of news items with metadata
    """
    items = MOCK_NEWS.copy()
    
    if asset_type:
        items = [n for n in items if n.asset_type == asset_type]
    
    items = items[:limit]
    
    return NewsResponse(items=items, total=len(items))


@app.get("/api/news/{news_id}", response_model=NewsItem)
async def get_news_item(news_id: str):
    """Fetch a specific news item by ID."""
    for item in MOCK_NEWS:
        if item.id == news_id:
            return item
    raise HTTPException(status_code=404, detail="News item not found")


@app.post("/api/analyze", response_model=SentimentAnalysis)
async def analyze_news(request: AnalysisRequest):
    """
    Analyze a news item using RAG + LLM.
    
    Currently returns mock data. Will integrate Ollama + ChromaDB in Phase 2.
    """
    # Find the news item
    news_item = None
    for item in MOCK_NEWS:
        if item.id == request.news_id:
            news_item = item
            break
    
    if not news_item:
        raise HTTPException(status_code=404, detail="News item not found")
    
    # Mock analysis (will be replaced with Ollama + RAG)
    sentiments = ["bullish", "bearish", "neutral"]
    sentiment = random.choice(sentiments[:2])  # Favor bullish/bearish for demo
    confidence = round(random.uniform(0.65, 0.95), 2)
    
    # Generate prediction hash
    prediction_data = f"{news_item.id}:{sentiment}:{confidence}:{datetime.now().isoformat()}"
    prediction_hash = hashlib.sha256(prediction_data.encode()).hexdigest()
    
    return SentimentAnalysis(
        sentiment=sentiment,
        confidence=confidence,
        reasoning=f"Based on analysis of '{news_item.title}', market indicators suggest "
                  f"a {sentiment} outlook. Key factors include institutional activity, "
                  f"technical patterns, and sector momentum.",
        historical_context=f"Similar news patterns in the past 12 months have resulted in "
                          f"average price movements of +/-8.5% within 7 days. The {news_item.symbol} "
                          f"has shown strong correlation with this type of catalyst.",
        prediction_hash=prediction_hash,
        tx_hash=None  # Will be populated after blockchain verification
    )


@app.get("/api/symbols")
async def get_tracked_symbols():
    """Get list of all tracked symbols."""
    symbols = list(set(item.symbol for item in MOCK_NEWS))
    return {"symbols": symbols}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
