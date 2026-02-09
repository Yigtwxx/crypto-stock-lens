"""
Oracle-X Backend API
FastAPI server providing news feeds, AI analysis, and blockchain verification.
"""
# Suppress warnings before other imports
import warnings
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")
warnings.filterwarnings("ignore", category=DeprecationWarning)

from typing import Optional, List
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import random
import hashlib

from models.schemas import NewsItem, NewsResponse, AnalysisRequest, SentimentAnalysis, FearGreedData, MarketOverview
from services.news_service import fetch_all_news
from services.ollama_service import analyze_news_with_ollama, generate_prediction_hash, check_ollama_health
from services.technical_analysis_service import get_technical_analysis
from services.rag_service import get_rag_context, store_news_with_outcome, get_collection_stats
from services.fear_greed_service import fetch_fear_greed_index
from services.market_overview_service import fetch_market_overview
from services.stock_market_service import fetch_nasdaq_overview
from services.chat_service import chat_with_oracle, check_chat_available
from services.home_service import fetch_funding_rates, fetch_liquidations, fetch_onchain_data, fetch_macro_calendar
from services.liquidation_service import liquidation_service
from services.onchain_service import fetch_whale_trades
from services import profile_service

# ═══════════════════════════════════════════════════════════════════════════════
# TERMINAL COLORS & LOGGING
# ═══════════════════════════════════════════════════════════════════════════════
class Colors:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log_header(message: str):
    print(f"\n{Colors.PURPLE}{'═'*60}{Colors.END}", flush=True)
    print(f"{Colors.PURPLE}{Colors.BOLD}  🔮 {message}{Colors.END}", flush=True)
    print(f"{Colors.PURPLE}{'═'*60}{Colors.END}", flush=True)

def log_step(emoji: str, message: str, color: str = Colors.CYAN):
    print(f"{color}  {emoji}  {message}{Colors.END}", flush=True)

def log_success(message: str):
    print(f"{Colors.GREEN}  ✓  {message}{Colors.END}", flush=True)

def log_warning(message: str):
    print(f"{Colors.YELLOW}  ⚠  {message}{Colors.END}", flush=True)

def log_error(message: str):
    print(f"{Colors.RED}  ✗  {message}{Colors.END}", flush=True)

def log_info(message: str):
    print(f"{Colors.GRAY}      {message}{Colors.END}", flush=True)

def log_result(label: str, value: str, color: str = Colors.WHITE):
    print(f"{Colors.GRAY}      {label}: {color}{value}{Colors.END}", flush=True)

# Set to True to use real API data, False for mock data
USE_REAL_API = True
# Set to True to use Ollama AI for analysis
USE_OLLAMA_AI = True

app = FastAPI(
    title="Oracle-X API",
    description="Financial Intelligence Terminal Backend",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Start background services."""
    await liquidation_service.start()
    # Start price streaming service (lazy - starts when first client connects)
    # Uncomment below to start immediately on server start:
    # from services.websocket_service import price_streaming_service
    # await price_streaming_service.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop background services."""
    await liquidation_service.stop()
    # Stop price streaming if running
    try:
        from services.websocket_service import price_streaming_service
        await price_streaming_service.stop()
    except Exception:
        pass

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
    global _news_cache
    
    log_header("NEW ANALYSIS REQUEST")
    log_step("📰", f"News ID: {request.news_id}")
    
    # Find the news item from cache or mock data
    news_item = get_news_from_cache_or_mock(request.news_id)
    
    # If not found in cache, try to fetch fresh news and search again
    if not news_item:
        log_warning("News not in cache, fetching fresh data...")
        try:
            fresh_items = await fetch_all_news()
            _news_cache = {item.id: item for item in fresh_items}
            news_item = _news_cache.get(request.news_id)
            if news_item:
                log_success("Found news in fresh data!")
        except Exception as e:
            log_error(f"Failed to fetch fresh news: {e}")
    
    if not news_item:
        log_error(f"News item not found: {request.news_id}")
        raise HTTPException(status_code=404, detail=f"News item not found: {request.news_id}")
    
    # Log news details
    log_step("📋", f"Title: {news_item.title[:60]}...", Colors.WHITE)
    log_result("Symbol", news_item.symbol)
    log_result("Asset Type", news_item.asset_type.upper())
    if request.current_price:
        log_result("Current Price", f"${request.current_price:,.2f}", Colors.GREEN)
    
    # Fetch REAL technical analysis data for crypto assets
    real_technical = None
    if news_item.asset_type == "crypto":
        log_step("📊", "Fetching real-time technical analysis...", Colors.BLUE)
        real_technical = await get_technical_analysis(news_item.symbol)
        if real_technical:
            log_success(f"Technical data: RSI {real_technical.get('rsi_signal', 'N/A')}")
    
    if USE_OLLAMA_AI:
        # Get RAG context from similar historical news
        log_step("🧠", "Searching historical context (RAG)...", Colors.CYAN)
        rag_context = get_rag_context(
            title=news_item.title,
            summary=news_item.summary,
            asset_type=news_item.asset_type
        )
        if rag_context:
            log_success("Historical context found!")
        
        # Use Ollama AI analysis with RAG-enhanced context
        log_step("🤖", "AI is analyzing the news...", Colors.PURPLE)
        log_info("Connecting to Ollama (llama3.1:8b)...")
        log_info("Processing sentiment, confidence, and reasoning...")
        
        analysis = await analyze_news_with_ollama(
            title=news_item.title,
            summary=news_item.summary,
            symbol=news_item.symbol,
            asset_type=news_item.asset_type,
            current_price=request.current_price,
            rag_context=rag_context
        )
        
        sentiment = analysis.get("sentiment", "neutral")
        confidence = analysis.get("confidence", 0.7)
        reasoning = analysis.get("reasoning", "Analysis completed.")
        
        # Log AI result
        sentiment_colors = {
            "bullish": Colors.GREEN,
            "bearish": Colors.RED,
            "neutral": Colors.YELLOW
        }
        log_success("AI analysis complete!")
        log_result("Sentiment", sentiment.upper(), sentiment_colors.get(sentiment, Colors.WHITE))
        log_result("Confidence", f"{confidence*100:.0f}%", Colors.CYAN)
        
        # Build professional historical context
        key_factors = analysis.get("key_factors", [])
        price_impact = analysis.get("price_impact", "")
        risk_level = analysis.get("risk_level", "medium")
        time_horizon = analysis.get("time_horizon", "short-term")
        
        # Format risk level display
        risk_labels = {"low": "LOW", "medium": "MEDIUM", "high": "HIGH"}
        risk_display = risk_labels.get(risk_level.lower(), "MEDIUM")
        
        # Format time horizon display
        horizon_labels = {
            "immediate": "Immediate (minutes to hours)",
            "short-term": "Short-term (1-7 days)",
            "medium-term": "Medium-term (1-4 weeks)",
            "long-term": "Long-term (1+ months)"
        }
        horizon_display = horizon_labels.get(time_horizon.lower(), "Short-term (1-7 days)")
        
        log_result("Risk Level", risk_display)
        log_result("Time Horizon", horizon_display)
        
        # Build professional context string
        context_parts = []
        context_parts.append(f"Risk Level: {risk_display} | Time Horizon: {horizon_display}")
        
        if key_factors:
            factors_text = ", ".join(key_factors[:3])
            context_parts.append(f"Key factors: {factors_text}")
            log_result("Key Factors", factors_text)
        
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
        log_warning("Ollama AI disabled, using fallback analysis...")
        # Fallback to mock analysis
        sentiments = ["bullish", "bearish", "neutral"]
        sentiment = random.choice(sentiments[:2])
        confidence = round(random.uniform(0.65, 0.95), 2)
        reasoning = f"Based on analysis of '{news_item.title}', market indicators suggest a {sentiment} outlook."
        historical_context = f"Similar news patterns have resulted in average price movements of +/-8.5% within 7 days."
        technical_signals = None
    
    # Generate prediction hash
    log_step("🔐", "Generating prediction hash...", Colors.GRAY)
    prediction_hash = generate_prediction_hash(news_item.id, sentiment, confidence)
    
    # Store news and analysis in RAG for future learning
    log_step("💾", "Storing analysis in RAG database...", Colors.GRAY)
    store_news_with_outcome(
        news_id=news_item.id,
        title=news_item.title,
        summary=news_item.summary,
        symbol=news_item.symbol,
        asset_type=news_item.asset_type,
        sentiment=sentiment,
        confidence=confidence
    )
    
    log_success("Analysis complete and stored!")
    print(f"{Colors.PURPLE}{'═'*60}{Colors.END}\n")
    
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


@app.get("/api/fear-greed", response_model=FearGreedData)
async def get_fear_greed():
    """
    Get Crypto Fear & Greed Index from alternative.me API.
    
    Values: 0-25 Extreme Fear, 26-46 Fear, 47-54 Neutral, 55-75 Greed, 76-100 Extreme Greed
    """
    data = await fetch_fear_greed_index()
    return FearGreedData(**data)


@app.get("/api/market-overview", response_model=MarketOverview)
async def get_market_overview():
    """
    Get market overview with top coin prices and global stats.
    
    Includes: BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX
    """
    data = await fetch_market_overview()
    return MarketOverview(**data)


@app.get("/api/nasdaq-overview")
async def get_nasdaq_overview():
    """
    Get NASDAQ stock market overview with top stocks and Fear & Greed index.
    
    Includes: Top 50 NASDAQ stocks by market cap (AAPL, MSFT, GOOGL, etc.)
    """
    data = await fetch_nasdaq_overview()
    return data


@app.get("/api/market/indices")
async def get_market_indices():
    """
    Get global market indices (S&P 500, NASDAQ, Nikkei, FTSE, DAX, etc.)
    
    Returns real-time data from Yahoo Finance.
    """
    import httpx
    import asyncio
    
    # Major global indices with their Yahoo Finance symbols
    indices_config = [
        {"symbol": "^GSPC", "name": "S&P 500", "region": "US"},
        {"symbol": "^IXIC", "name": "NASDAQ", "region": "US"},
        {"symbol": "^DJI", "name": "Dow Jones", "region": "US"},
        {"symbol": "^FTSE", "name": "FTSE 100", "region": "UK"},
        {"symbol": "^GDAXI", "name": "DAX", "region": "DE"},
        {"symbol": "^N225", "name": "Nikkei 225", "region": "JP"},
        {"symbol": "^HSI", "name": "Hang Seng", "region": "HK"},
        {"symbol": "^STOXX50E", "name": "Euro Stoxx 50", "region": "EU"},
        {"symbol": "^FCHI", "name": "CAC 40", "region": "FR"},
        {"symbol": "^AXJO", "name": "ASX 200", "region": "AU"},
    ]
    
    async def fetch_index(client: httpx.AsyncClient, idx: dict) -> Optional[dict]:
        try:
            # Use Yahoo Finance quote endpoint for more accurate real-time data
            symbol = idx["symbol"]
            url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json"
            }
            
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                quote_response = data.get("quoteResponse", {})
                results = quote_response.get("result", [])
                
                if results:
                    quote = results[0]
                    current_price = quote.get("regularMarketPrice", 0)
                    change_percent = quote.get("regularMarketChangePercent", 0)
                    
                    return {
                        "symbol": idx["symbol"],
                        "name": idx["name"],
                        "price": round(current_price, 2),
                        "change_24h": round(change_percent, 2),
                        "region": idx["region"]
                    }
        except Exception as e:
            print(f"Failed to fetch {idx['name']}: {e}")
        return None
    
    results = []
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Fetch all indices in parallel
            tasks = [fetch_index(client, idx) for idx in indices_config]
            fetched = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in fetched:
                if result and not isinstance(result, Exception):
                    results.append(result)
    except Exception as e:
        print(f"Error fetching indices: {e}")
    
    # If no results or too few, return mock data with realistic values
    if len(results) < 3:
        results = [
            {"symbol": "^GSPC", "name": "S&P 500", "price": 6025.99, "change_24h": 0.36, "region": "US"},
            {"symbol": "^IXIC", "name": "NASDAQ", "price": 19654.02, "change_24h": 0.51, "region": "US"},
            {"symbol": "^DJI", "name": "Dow Jones", "price": 44747.63, "change_24h": 0.30, "region": "US"},
            {"symbol": "^FTSE", "name": "FTSE 100", "price": 8727.28, "change_24h": 0.57, "region": "UK"},
            {"symbol": "^GDAXI", "name": "DAX", "price": 21902.43, "change_24h": 0.74, "region": "DE"},
            {"symbol": "^N225", "name": "Nikkei 225", "price": 38787.02, "change_24h": -0.28, "region": "JP"},
            {"symbol": "^HSI", "name": "Hang Seng", "price": 21133.54, "change_24h": 1.15, "region": "HK"},
            {"symbol": "^STOXX50E", "name": "Euro Stoxx 50", "price": 5359.81, "change_24h": 0.42, "region": "EU"},
        ]
    
    return results



@app.get("/api/liquidations/heatmap")
async def get_liquidation_heatmap():
    """
    Get live liquidation heatmap data.
    Aggregated from real-time Binance WebSocket stream.
    """
    return await liquidation_service.get_heatmap_data()


@app.get("/api/liquidations/history/{symbol}")
async def get_liquidation_history(symbol: str):
    """
    Get all stored liquidation history for a specific symbol.
    Start building your heat profile from this data.
    """
    return await liquidation_service.get_liquidation_history(symbol)


@app.get("/api/market/candles/{symbol}")
async def get_market_candles(symbol: str, interval: str = "1h"):
    """
    Get OHLCV candles for chart backfilling.
    Default: 1h interval, 1 week limit.
    """
    return await liquidation_service.fetch_candles(symbol, interval)


# ═══════════════════════════════════════════════════════════════════════════════
# WATCHLIST ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

from pydantic import BaseModel

class WatchlistItem(BaseModel):
    symbol: str
    type: str # "STOCK" or "CRYPTO"

class CreateWatchlistRequest(BaseModel):
    name: str
    items: List[WatchlistItem]

@app.get("/api/home/watchlist")
async def get_watchlists_endpoint():
    try:
        from services.watchlist_service import get_watchlists
        return await get_watchlists()
    except Exception as e:
        print(f"Error getting watchlists: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/home/watchlist")
async def create_watchlist_endpoint(request: CreateWatchlistRequest):
    try:
        from services.watchlist_service import create_watchlist
        # Convert Pydantic models to dicts
        items_dict = [{"symbol": item.symbol, "type": item.type} for item in request.items]
        return await create_watchlist(request.name, items_dict)
    except Exception as e:
        print(f"Error creating watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/home/watchlist/{list_id}")
async def delete_watchlist_endpoint(list_id: str):
    try:
        from services.watchlist_service import delete_watchlist
        return await delete_watchlist(list_id)
    except Exception as e:
        print(f"Error deleting watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# HOME PAGE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/home/funding-rates")
async def get_funding_rates():
    """Get real-time funding rates from Binance Futures."""
    return await fetch_funding_rates()

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS & NOTES ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

class NoteRequest(BaseModel):
    title: str
    content: str

@app.get("/api/analysis/report/{timeframe}")
async def get_analysis_report(timeframe: str):
    """Get AI generated market report (daily, weekly, monthly)."""
    try:
        from services.analysis_service import get_report
        if timeframe not in ['daily', 'weekly', 'monthly']:
            raise HTTPException(status_code=400, detail="Invalid timeframe")
        return await get_report(timeframe)
    except Exception as e:
        print(f"Error getting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/generate/{timeframe}")
async def generate_analysis_report(timeframe: str):
    """Force regenerate a market report."""
    try:
        from services.analysis_service import generate_market_report
        content = await generate_market_report(timeframe)
        return {"content": content, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        print(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/notes")
async def get_notes():
    """Get all user notes."""
    try:
        from services.analysis_service import get_user_notes
        return get_user_notes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis/notes")
async def create_note(request: NoteRequest):
    """Create a new user note."""
    try:
        from services.analysis_service import add_user_note
        return add_user_note(request.title, request.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/analysis/notes/{note_id}")
async def delete_note(note_id: str):
    """Delete a user note."""
    try:
        from services.analysis_service import delete_user_note
        return delete_user_note(note_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/home/liquidations")
async def get_liquidations():
    """Get recent large liquidations from Binance Futures."""
    return await fetch_liquidations()

@app.get("/api/home/onchain")
async def get_onchain_data():
    """Get on-chain stats (Mocked for demo)."""
    return await fetch_onchain_data()

@app.get("/api/onchain/whales")
async def get_whale_trades():
    """Get on-chain whale trade activity from Binance."""
    return await fetch_whale_trades()


@app.get("/api/heatmap/data")
async def get_heatmap_data():
    """Get multi-metric heatmap data (price, volume, social, developer)."""
    try:
        from services.heatmap_service import fetch_heatmap_data
        return await fetch_heatmap_data()
    except Exception as e:
        print(f"Error fetching heatmap data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# RAG 2.0 ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/rag/initialize")
async def initialize_rag():
    """Initialize RAG 2.0 with historical data (run once)."""
    try:
        from services.rag_v2_service import initialize_rag_v2
        stats = await initialize_rag_v2(symbols=["BTC", "ETH", "SOL"])
        return {"success": True, "stats": stats}
    except Exception as e:
        print(f"Error initializing RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rag/stats")
async def get_rag_statistics():
    """Get RAG 2.0 statistics."""
    try:
        from services.rag_v2_service import get_rag_stats
        return get_rag_stats()
    except Exception as e:
        return {"status": f"error: {str(e)}", "news_count": 0, "events_count": 0, "prices_count": 0}


@app.get("/api/rag/query")
async def query_rag_context(
    q: str,
    symbol: Optional[str] = None,
    context_type: str = "all"
):
    """
    Query RAG 2.0 for historical context.
    
    - q: Query text (e.g., "Bitcoin halving price behavior")
    - symbol: Filter by symbol (BTC, ETH, etc.)
    - context_type: 'all', 'events', 'prices', 'news'
    """
    try:
        from services.rag_v2_service import query_historical_context, get_rag_context_v2
        
        results = query_historical_context(
            query=q,
            symbol=symbol,
            include_events=context_type in ["all", "events"],
            include_prices=context_type in ["all", "prices"],
            include_news=context_type in ["all", "news"],
            k=5
        )
        
        return {
            "query": q,
            "symbol": symbol,
            "results": results
        }
    except Exception as e:
        print(f"Error querying RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/home/macro-calendar")
async def get_macro_calendar():
    """Get US Economic Calendar (ForexFactory)."""
    # Local import to avoid circular dependency if needed, but usually fine at top
    # We need to ensure it's imported at top, so let's check `home_service` import
    return await fetch_macro_calendar()


# ═══════════════════════════════════════════════════════════════════════════════
# ORACLE CHAT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    response: str
    thinking_time: float


@app.post("/api/chat", response_model=ChatResponse)
async def oracle_chat(request: ChatRequest):
    """
    Chat with Oracle AI assistant.
    
    Provides intelligent responses about crypto, stocks, and market analysis.
    Uses extended thinking time for quality responses.
    """
    log_header("ORACLE CHAT REQUEST")
    log_step("💬", f"Message: {request.message[:100]}..." if len(request.message) > 100 else f"Message: {request.message}")
    
    # Convert history to dict format
    history = None
    if request.history:
        history = [{"role": m.role, "content": m.content} for m in request.history]
        log_info(f"Conversation history: {len(history)} messages")
    
    log_step("🤔", "Oracle is thinking (this may take a while for complex questions)...", Colors.PURPLE)
    
    result = await chat_with_oracle(request.message, history)
    
    log_success(f"Response generated in {result['thinking_time']}s")
    log_info(f"Response length: {len(result['response'])} characters")
    print(f"{Colors.PURPLE}{'═'*60}{Colors.END}\n")
    
    return ChatResponse(
        response=result["response"],
        thinking_time=result["thinking_time"]
    )


@app.get("/api/chat/status")
async def chat_status():
    """Check if Oracle chat is available."""
    is_available = await check_chat_available()
    return {
        "available": is_available,
        "model": "llama3.1:8b" if is_available else None,
        "message": "Oracle hazır" if is_available else "Ollama servisi çalışmıyor"
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CHAT HISTORY ENDPOINTS (Database Persistence)
# ═══════════════════════════════════════════════════════════════════════════════

class SaveChatMessageRequest(BaseModel):
    user_id: str
    role: str
    content: str
    thinking_time: Optional[float] = None


@app.get("/api/chat/history/{user_id}")
async def get_chat_history_endpoint(user_id: str, limit: int = 50):
    """
    Get chat history for a user from database.
    Automatically cleans up messages older than 7 days.
    """
    try:
        from services.supabase_service import get_chat_history
        messages = await get_chat_history(user_id, limit)
        return {"messages": messages, "count": len(messages)}
    except Exception as e:
        print(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/history")
async def save_chat_message_endpoint(request: SaveChatMessageRequest):
    """Save a chat message to database."""
    try:
        from services.supabase_service import save_chat_message
        result = await save_chat_message(
            user_id=request.user_id,
            role=request.role,
            content=request.content,
            thinking_time=request.thinking_time
        )
        return {"success": True, "message": result}
    except Exception as e:
        print(f"Error saving chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chat/history/{user_id}")
async def clear_chat_history_endpoint(user_id: str):
    """Clear all chat history for a user."""
    try:
        from services.supabase_service import clear_chat_history
        success = await clear_chat_history(user_id)
        return {"success": success}
    except Exception as e:
        print(f"Error clearing chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# PROFILE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/profile/{user_id}")
async def get_user_profile(user_id: str):
    """Get user profile with subscription info."""
    try:
        profile = await profile_service.get_user_profile(user_id)
        if profile:
            return profile
        raise HTTPException(status_code=404, detail="Profile not found")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/profile/{user_id}")
async def update_user_profile(user_id: str, data: dict):
    """Update user profile."""
    try:
        success = await profile_service.update_user_profile(user_id, data)
        if success:
            return {"success": True}
        raise HTTPException(status_code=400, detail="Failed to update profile")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profile/{user_id}/subscription")
async def get_subscription(user_id: str):
    """Get user's current subscription info."""
    try:
        subscription = await profile_service.get_subscription(user_id)
        return subscription
    except Exception as e:
        print(f"Error getting subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profile/{user_id}/subscription")
async def update_subscription(user_id: str, data: dict):
    """Update user's subscription plan."""
    try:
        plan = data.get("plan", "free")
        duration_days = data.get("duration_days", 30)
        success = await profile_service.update_subscription(user_id, plan, duration_days)
        if success:
            return {"success": True, "plan": plan}
        raise HTTPException(status_code=400, detail="Failed to update subscription")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profile/{user_id}/accounts")
async def get_connected_accounts(user_id: str):
    """Get user's connected social accounts."""
    try:
        accounts = await profile_service.get_connected_accounts(user_id)
        return {"accounts": accounts}
    except Exception as e:
        print(f"Error getting connected accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profile/{user_id}/accounts/{provider}")
async def connect_account(user_id: str, provider: str, data: dict):
    """Connect a social account."""
    try:
        success = await profile_service.connect_account(
            user_id=user_id,
            provider=provider,
            provider_user_id=data.get("provider_user_id", ""),
            provider_username=data.get("provider_username", ""),
            access_token=data.get("access_token"),
            refresh_token=data.get("refresh_token")
        )
        if success:
            return {"success": True, "provider": provider}
        raise HTTPException(status_code=400, detail="Failed to connect account")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error connecting account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/profile/{user_id}/accounts/{provider}")
async def disconnect_account(user_id: str, provider: str):
    """Disconnect a social account."""
    try:
        success = await profile_service.disconnect_account(user_id, provider)
        if success:
            return {"success": True}
        raise HTTPException(status_code=400, detail="Failed to disconnect account")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error disconnecting account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profile/{user_id}/settings")
async def get_user_settings(user_id: str):
    """Get user settings."""
    try:
        settings = await profile_service.get_user_settings(user_id)
        return settings
    except Exception as e:
        print(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/profile/{user_id}/settings")
async def update_user_settings(user_id: str, data: dict):
    """Update user settings."""
    try:
        success = await profile_service.update_user_settings(user_id, data)
        if success:
            return {"success": True}
        raise HTTPException(status_code=400, detail="Failed to update settings")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profile/{user_id}/ai-query")
async def increment_ai_query(user_id: str):
    """Increment AI query count and check limits."""
    try:
        result = await profile_service.increment_ai_queries(user_id)
        return result
    except Exception as e:
        print(f"Error incrementing AI query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# CCXT MULTI-EXCHANGE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/exchanges")
async def get_exchanges():
    """
    Get list of supported exchanges for multi-exchange price comparison.
    
    Returns list of exchange IDs that can be used with other endpoints.
    Supports 100+ exchanges via CCXT library.
    """
    try:
        from services.ccxt_service import get_supported_exchanges, get_exchange_info
        exchanges = get_supported_exchanges()
        return {
            "exchanges": [
                {
                    "id": ex,
                    **(get_exchange_info(ex) or {"name": ex.capitalize()})
                }
                for ex in exchanges
            ],
            "total": len(exchanges)
        }
    except Exception as e:
        print(f"Error getting exchanges: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/exchanges/all")
async def get_all_exchanges():
    """
    Get list of ALL 100+ exchanges supported by CCXT.
    Use with caution - not all may be reliable or available.
    """
    try:
        from services.ccxt_service import get_all_ccxt_exchanges
        exchanges = get_all_ccxt_exchanges()
        return {"exchanges": exchanges, "total": len(exchanges)}
    except Exception as e:
        print(f"Error getting all exchanges: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/exchanges/{exchange_id}/ticker/{base}/{quote}")
async def get_exchange_ticker(exchange_id: str, base: str, quote: str):
    """
    Get ticker data from a specific exchange.
    
    Args:
        exchange_id: Exchange ID (e.g., 'binance', 'kraken', 'coinbasepro')
        base: Base currency (e.g., 'BTC')
        quote: Quote currency (e.g., 'USDT')
    
    Example: /api/exchanges/binance/ticker/BTC/USDT
    """
    try:
        from services.ccxt_service import fetch_ticker, get_supported_exchanges
        
        symbol = f"{base.upper()}/{quote.upper()}"
        
        if exchange_id not in get_supported_exchanges():
            raise HTTPException(
                status_code=400, 
                detail=f"Exchange '{exchange_id}' not supported. Use /api/exchanges to see available exchanges."
            )
        
        result = await fetch_ticker(exchange_id, symbol)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Could not fetch {symbol} from {exchange_id}. Symbol may not be available."
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching ticker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/multi-exchange/prices/{base}/{quote}")
async def get_multi_exchange_prices(base: str, quote: str, exchanges: Optional[str] = None):
    """
    Get prices for a trading pair from multiple exchanges simultaneously.
    
    Args:
        base: Base currency (e.g., 'BTC')
        quote: Quote currency (e.g., 'USDT')
        exchanges: Comma-separated list of exchange IDs (optional, defaults to all supported)
    
    Example: /api/multi-exchange/prices/BTC/USDT?exchanges=binance,kraken,coinbasepro
    
    Returns prices sorted from lowest to highest.
    """
    try:
        from services.ccxt_service import fetch_multi_exchange_prices
        
        symbol = f"{base.upper()}/{quote.upper()}"
        exchange_list = exchanges.split(",") if exchanges else None
        
        results = await fetch_multi_exchange_prices(symbol, exchange_list)
        
        return {
            "symbol": symbol,
            "prices": results,
            "exchanges_queried": len(exchange_list) if exchange_list else 8,
            "exchanges_responded": len(results),
            "lowest_price": results[0] if results else None,
            "highest_price": results[-1] if results else None,
        }
    except Exception as e:
        print(f"Error fetching multi-exchange prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/arbitrage/{base}/{quote}")
async def get_arbitrage_opportunity(
    base: str, 
    quote: str, 
    min_spread: float = 0.5,
    exchanges: Optional[str] = None
):
    """
    Detect arbitrage opportunities for a trading pair across exchanges.
    
    Args:
        base: Base currency (e.g., 'BTC')
        quote: Quote currency (e.g., 'USDT')
        min_spread: Minimum spread percentage to flag as opportunity (default: 0.5%)
        exchanges: Comma-separated list of exchange IDs (optional)
    
    Example: /api/arbitrage/BTC/USDT?min_spread=0.3
    
    Returns:
        - has_opportunity: Whether an arbitrage opportunity exists
        - spread_percent: Price difference as percentage
        - buy_exchange: Where to buy (lowest price)
        - sell_exchange: Where to sell (highest price)
        - potential_profit_per_unit: Profit potential per unit traded
    """
    try:
        from services.ccxt_service import detect_arbitrage_opportunities
        
        symbol = f"{base.upper()}/{quote.upper()}"
        exchange_list = exchanges.split(",") if exchanges else None
        
        result = await detect_arbitrage_opportunities(symbol, min_spread, exchange_list)
        return result
    except Exception as e:
        print(f"Error detecting arbitrage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/arbitrage/scan")
async def scan_arbitrage_opportunities(
    min_spread: float = 0.5,
    symbols: Optional[str] = None,
    exchanges: Optional[str] = None
):
    """
    Scan multiple trading pairs for arbitrage opportunities.
    
    Args:
        min_spread: Minimum spread percentage to flag (default: 0.5%)
        symbols: Comma-separated trading pairs (e.g., 'BTC/USDT,ETH/USDT')
        exchanges: Comma-separated exchange IDs
    
    Example: /api/arbitrage/scan?min_spread=0.3&symbols=BTC/USDT,ETH/USDT,SOL/USDT
    
    Returns all pairs sorted by spread percentage (highest first).
    """
    try:
        from services.ccxt_service import scan_all_arbitrage_opportunities
        
        symbol_list = symbols.split(",") if symbols else None
        exchange_list = exchanges.split(",") if exchanges else None
        
        results = await scan_all_arbitrage_opportunities(
            symbols=symbol_list,
            min_spread_percent=min_spread,
            exchanges=exchange_list
        )
        
        opportunities = [r for r in results if r.get("has_opportunity")]
        
        return {
            "total_scanned": len(results),
            "opportunities_found": len(opportunities),
            "min_spread_threshold": min_spread,
            "opportunities": opportunities,
            "all_results": results
        }
    except Exception as e:
        print(f"Error scanning arbitrage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET REAL-TIME PRICE STREAMING
# ═══════════════════════════════════════════════════════════════════════════════

@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """
    Real-time price streaming via WebSocket.
    
    Connect to receive live price updates for top cryptocurrencies.
    Updates are pushed as prices change (millisecond latency).
    
    Message format:
    {
        "type": "price_update",
        "symbol": "BTCUSDT",
        "price": 97000.50,
        "change_24h": 1.25,
        "direction": "up" | "down" | "none",
        "timestamp": "2026-02-09T19:20:00.000000"
    }
    """
    from services.websocket_service import (
        get_connection_manager, 
        get_streaming_service
    )
    
    manager = get_connection_manager()
    streaming_service = get_streaming_service()
    
    await websocket.accept()
    await manager.connect(websocket)
    
    # Start streaming service if not already running
    if not streaming_service.is_running:
        await streaming_service.start()
    
    try:
        # Send initial snapshot of last known prices
        last_prices = streaming_service.get_last_prices()
        if last_prices:
            await websocket.send_json({
                "type": "snapshot",
                "prices": last_prices,
                "timestamp": datetime.now().isoformat()
            })
        
        # Keep connection alive, receive any client messages (ping/pong)
        while True:
            try:
                # Wait for client messages (ping, subscribe, etc.)
                data = await websocket.receive_text()
                
                # Handle ping/pong for keepalive
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)


@app.get("/api/websocket/status")
async def get_websocket_status():
    """Get WebSocket streaming service status."""
    try:
        from services.websocket_service import get_streaming_stats
        stats = await get_streaming_stats()
        return stats
    except Exception as e:
        return {
            "is_running": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


