"""
Oracle-X Backend API
FastAPI server providing news feeds, AI analysis, and blockchain verification.
"""
# Suppress warnings before other imports
import warnings
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")
warnings.filterwarnings("ignore", category=DeprecationWarning)

from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import random
import hashlib

from models.schemas import NewsItem, NewsResponse, AnalysisRequest, SentimentAnalysis
from services.news_service import fetch_all_news
from services.ollama_service import analyze_news_with_ollama, generate_prediction_hash, check_ollama_health
from services.technical_analysis_service import get_technical_analysis
from services.rag_service import get_rag_context, store_news_with_outcome, get_collection_stats

# Set to True to use real API data, False for mock data
USE_REAL_API = True
# Set to True to use Ollama AI for analysis
USE_OLLAMA_AI = True

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
MOCK_NEWS: List[NewsItem] = [
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
    asset_type: Optional[str] = None,
    limit: int = 20
):
    """
    Fetch latest news items from multiple sources.
    
    Args:
        asset_type: Filter by "stock" or "crypto" (optional)
        limit: Maximum number of items to return
    
    Returns:
        List of news items with metadata
    """
    if USE_REAL_API:
        try:
            items = await fetch_all_news()
        except Exception as e:
            print(f"Error fetching real news: {e}")
            items = MOCK_NEWS.copy()
    else:
        items = MOCK_NEWS.copy()
    
    if asset_type:
        items = [n for n in items if n.asset_type == asset_type]
    
    items = items[:limit]
    
    # Cache news items for analyze endpoint
    global _news_cache
    _news_cache = {item.id: item for item in items}
    
    return NewsResponse(items=items, total=len(items))

# Global cache for fetched news items
_news_cache: dict = {}


def get_news_from_cache_or_mock(news_id: str) -> Optional[NewsItem]:
    """Get news item from cache or mock data."""
    if news_id in _news_cache:
        return _news_cache[news_id]
    for item in MOCK_NEWS:
        if item.id == news_id:
            return item
    return None


@app.get("/api/news/{news_id}", response_model=NewsItem)
async def get_news_item(news_id: str):
    """Fetch a specific news item by ID."""
    item = get_news_from_cache_or_mock(news_id)
    if item:
        return item
    raise HTTPException(status_code=404, detail="News item not found")


@app.post("/api/analyze", response_model=SentimentAnalysis)
async def analyze_news(request: AnalysisRequest):
    """
    Analyze a news item using Ollama LLM (llama3.1:8b).
    
    Provides real AI-powered sentiment analysis with confidence scores.
    Technical analysis uses REAL market data from Binance API.
    """
    # Find the news item from cache or mock data
    news_item = get_news_from_cache_or_mock(request.news_id)
    
    if not news_item:
        raise HTTPException(status_code=404, detail="News item not found")
    
    # Fetch REAL technical analysis data for crypto assets
    real_technical = None
    if news_item.asset_type == "crypto":
        real_technical = await get_technical_analysis(news_item.symbol)
    
    if USE_OLLAMA_AI:
        # Get RAG context from similar historical news
        rag_context = get_rag_context(
            title=news_item.title,
            summary=news_item.summary,
            asset_type=news_item.asset_type
        )
        
        # Use Ollama AI analysis with RAG-enhanced context
        analysis = await analyze_news_with_ollama(
            title=news_item.title,
            summary=news_item.summary,
            symbol=news_item.symbol,
            asset_type=news_item.asset_type,
            current_price=request.current_price,
            rag_context=rag_context  # Include historical context
        )
        
        sentiment = analysis.get("sentiment", "neutral")
        confidence = analysis.get("confidence", 0.7)
        reasoning = analysis.get("reasoning", "Analysis completed.")
        
        # Build professional historical context
        key_factors = analysis.get("key_factors", [])
        price_impact = analysis.get("price_impact", "")
        risk_level = analysis.get("risk_level", "medium")
        time_horizon = analysis.get("time_horizon", "short-term")
        
        # Format risk level display
        risk_labels = {
            "low": "LOW",
            "medium": "MEDIUM", 
            "high": "HIGH"
        }
        risk_display = risk_labels.get(risk_level.lower(), "MEDIUM")
        
        # Format time horizon display
        horizon_labels = {
            "immediate": "Immediate (minutes to hours)",
            "short-term": "Short-term (1-7 days)",
            "medium-term": "Medium-term (1-4 weeks)",
            "long-term": "Long-term (1+ months)"
        }
        horizon_display = horizon_labels.get(time_horizon.lower(), "Short-term (1-7 days)")
        
        # Build professional context string
        context_parts = []
        context_parts.append(f"Risk Level: {risk_display} | Time Horizon: {horizon_display}")
        
        if key_factors:
            factors_text = ", ".join(key_factors[:3])
            context_parts.append(f"Key factors: {factors_text}")
        
        if price_impact:
            context_parts.append(f"Expected impact: {price_impact}")
        
        historical_context = ". ".join(context_parts)
        
        # Use REAL technical data if available, otherwise fallback to LLM
        if real_technical:
            technical_signals = {
                "rsi_signal": real_technical["rsi_signal"],
                "support_levels": real_technical["support_levels"],
                "resistance_levels": real_technical["resistance_levels"],
                "target_price": real_technical["target_price"]
            }
        else:
            technical_signals = analysis.get("technical_signals")
    else:
        # Fallback to mock analysis
        sentiments = ["bullish", "bearish", "neutral"]
        sentiment = random.choice(sentiments[:2])
        confidence = round(random.uniform(0.65, 0.95), 2)
        reasoning = f"Based on analysis of '{news_item.title}', market indicators suggest a {sentiment} outlook."
        historical_context = f"Similar news patterns have resulted in average price movements of +/-8.5% within 7 days."
        technical_signals = None
    
    # Generate prediction hash
    prediction_hash = generate_prediction_hash(news_item.id, sentiment, confidence)
    
    # Store news and analysis in RAG for future learning
    store_news_with_outcome(
        news_id=news_item.id,
        title=news_item.title,
        summary=news_item.summary,
        symbol=news_item.symbol,
        asset_type=news_item.asset_type,
        sentiment=sentiment,
        confidence=confidence
    )
    
    return SentimentAnalysis(
        sentiment=sentiment,
        confidence=confidence,
        reasoning=reasoning,
        historical_context=historical_context,
        technical_signals=technical_signals,
        prediction_hash=prediction_hash,
        tx_hash=None
    )


@app.get("/api/symbols")
async def get_tracked_symbols():
    """Get list of all tracked symbols."""
    symbols = list(set(item.symbol for item in MOCK_NEWS))
    return {"symbols": symbols}


@app.get("/api/technical/{symbol}")
async def get_technical_levels(symbol: str):
    """
    Get real technical analysis for a crypto symbol.
    
    Example: /api/technical/BTCUSDT
    """
    result = await get_technical_analysis(f"BINANCE:{symbol}")
    if result:
        return result
    raise HTTPException(status_code=404, detail="Technical analysis not available for this symbol")


@app.get("/api/ollama/status")
async def get_ollama_status():
    """Check Ollama AI service status."""
    is_healthy = await check_ollama_health()
    return {
        "ollama_available": is_healthy,
        "model": "llama3.1:8b" if is_healthy else None,
        "ai_enabled": USE_OLLAMA_AI and is_healthy,
        "message": "Ollama AI is ready" if is_healthy else "Ollama is not available - using fallback analysis"
    }


@app.get("/api/rag/stats")
async def get_rag_stats():
    """Get RAG system statistics."""
    stats = get_collection_stats()
    return {
        "rag_enabled": True,
        "total_stored_news": stats.get("total_items", 0),
        "status": stats.get("status", "unknown"),
        "message": f"RAG system has {stats.get('total_items', 0)} historical news items for learning"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
