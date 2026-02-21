"""
News & Analysis Router
Handles news fetching, AI sentiment analysis, technical analysis, and Ollama status.
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException


from models.schemas import NewsItem, NewsResponse, AnalysisRequest, SentimentAnalysis
from services.news_service import fetch_all_news
from services.ollama_service import analyze_news_with_ollama, generate_prediction_hash, check_ollama_health
from services.technical_analysis_service import get_technical_analysis
from services.rag_service import get_rag_context, store_news_with_outcome
from utils import (
    Colors, log_header, log_step, log_success, log_warning, log_error, log_info, log_result,
    USE_REAL_API, USE_OLLAMA_AI,
    get_news_from_cache, update_news_cache, get_news_cache
)

router = APIRouter()


@router.get("/api/news", response_model=NewsResponse)
async def get_news(
    asset_type: Optional[str] = None,
    limit: int = 20
):
    """
    Fetch latest news items.
    
    Serves data from memory cache (updated by background scheduler).
    If cache is empty (server just started), triggers a fetch.
    """
    # 1. Try to get from cache
    cached_dict = get_news_cache()
    items = list(cached_dict.values())
    
    # 2. If cache is empty, fetch immediately (fallback)
    if not items and USE_REAL_API:
        log_warning("Cache miss in /api/news - fetching synchronously...")
        try:
            items = await fetch_all_news()
            update_news_cache(items)
        except Exception as e:
            print(f"Error fetching real news: {e}")
            items = []
    
    # 3. If still empty, return empty list
    if not items:
        items = []
    
    # 4. Filter by asset type
    if asset_type:
        items = [n for n in items if n.asset_type == asset_type]
    
    # 5. Sort by date (newest first) just in case
    items.sort(key=lambda x: x.published_at, reverse=True)
    
    # 6. Pagination
    items = items[:limit]
    
    return NewsResponse(items=items, total=len(items))


@router.get("/api/news/{news_id}", response_model=NewsItem)
async def get_news_item(news_id: str):
    """Fetch a specific news item by ID."""
    item = get_news_from_cache(news_id)
    if item:
        return item
    raise HTTPException(status_code=404, detail="News item not found")


@router.post("/api/analyze", response_model=SentimentAnalysis)
async def analyze_news(request: AnalysisRequest):
    """
    Analyze a news item using Ollama LLM (llama3.1:8b).
    
    Provides real AI-powered sentiment analysis with confidence scores.
    Technical analysis uses REAL market data from Binance API.
    """
    log_header("NEW ANALYSIS REQUEST")
    log_step("📰", f"News ID: {request.news_id}")
    
    # Find the news item from cache
    news_item = get_news_from_cache(request.news_id)
    
    # If not found in cache, try to fetch fresh news and search again
    if not news_item:
        log_warning("News not in cache, fetching fresh data...")
        try:
            fresh_items = await fetch_all_news()
            update_news_cache(fresh_items)
            news_item = get_news_cache().get(request.news_id)
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
        log_warning("Ollama AI disabled, cannot perform analysis.")
        raise HTTPException(
            status_code=503,
            detail="AI analysis is currently unavailable. Ollama AI service is not enabled."
        )
    
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


@router.get("/api/symbols")
async def get_tracked_symbols():
    """Get list of all tracked symbols."""
    # Return empty list or cached symbols if available
    cached = get_news_cache()
    if cached:
        symbols = list(set(item.symbol for item in cached.values()))
        return {"symbols": symbols}
    return {"symbols": []}


@router.get("/api/technical/{symbol}")
async def get_technical_levels(symbol: str):
    """
    Get real technical analysis for a crypto symbol.
    
    Example: /api/technical/BTCUSDT
    """
    result = await get_technical_analysis(f"BINANCE:{symbol}")
    if result:
        return result
    raise HTTPException(status_code=404, detail="Technical analysis not available for this symbol")


@router.get("/api/ollama/status")
async def get_ollama_status():
    """Check Ollama AI service status."""
    is_healthy = await check_ollama_health()
    return {
        "ollama_available": is_healthy,
        "model": "llama3.1:8b" if is_healthy else None,
        "ai_enabled": USE_OLLAMA_AI and is_healthy,
        "message": "Ollama AI is ready" if is_healthy else "Ollama is not available - using fallback analysis"
    }

