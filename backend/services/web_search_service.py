"""
Web Search Service - DuckDuckGo Search Integration
Provides real-time web search capability for Oracle AI chat.
"""
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Cache for search results (5 minute TTL)
_search_cache: Dict[str, tuple] = {}
CACHE_TTL = 300  # 5 minutes


async def search_web(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search the web using DuckDuckGo.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        List of search results with title, snippet, and url
    """
    # Check cache first
    cache_key = f"{query}:{max_results}"
    if cache_key in _search_cache:
        cached_time, cached_results = _search_cache[cache_key]
        if (datetime.now() - cached_time).seconds < CACHE_TTL:
            return cached_results
    
    try:
        # Run the sync DuckDuckGo search in a thread pool
        from ddgs import DDGS
        
        def do_search():
            try:
                ddgs = DDGS()
                results = ddgs.text(query, max_results=max_results)
                return [
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("href", "")
                    }
                    for r in results
                ]
            except Exception as e:
                logger.error(f"DDGS search failed: {e}")
                return []
        
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, do_search)
        
        # Cache results
        _search_cache[cache_key] = (datetime.now(), results)
        
        return results
        
    except Exception as e:
        logger.error(f"Web search error for '{query}': {e}")
        return []


async def search_crypto_news(symbol: str) -> List[Dict]:
    """
    Search for recent crypto news about a specific symbol.
    """
    query = f"{symbol} cryptocurrency news today {datetime.now().strftime('%B %Y')}"
    return await search_web(query, max_results=3)


async def search_market_analysis(symbol: str) -> List[Dict]:
    """
    Search for market analysis and price predictions.
    """
    query = f"{symbol} price analysis technical analysis {datetime.now().strftime('%B %Y')}"
    return await search_web(query, max_results=3)


async def search_general_finance(query: str) -> List[Dict]:
    """
    Search for general financial information.
    """
    finance_query = f"{query} finance market {datetime.now().strftime('%Y')}"
    return await search_web(finance_query, max_results=4)


async def get_enhanced_context(user_message: str, detected_symbol: Optional[str] = None) -> str:
    """
    Build enhanced context from web searches based on user message.
    
    Returns formatted string with web search results.
    """
    context_parts = []
    
    try:
        # If a specific symbol is detected, search for it
        if detected_symbol:
            # Search for news about the symbol
            news_results = await search_crypto_news(detected_symbol)
            if news_results:
                context_parts.append(f"\n🔍 **{detected_symbol} GÜNCEL HABERLER (Web Arama):**")
                for i, r in enumerate(news_results[:3], 1):
                    context_parts.append(f"{i}. {r['title']}")
                    if r['snippet']:
                        context_parts.append(f"   → {r['snippet'][:150]}...")
            
            # Search for analysis
            analysis_results = await search_market_analysis(detected_symbol)
            if analysis_results:
                context_parts.append(f"\n📈 **{detected_symbol} ANALİZ (Web Arama):**")
                for i, r in enumerate(analysis_results[:2], 1):
                    context_parts.append(f"{i}. {r['title']}")
                    if r['snippet']:
                        context_parts.append(f"   → {r['snippet'][:150]}...")
        else:
            # General financial search based on user message
            general_results = await search_general_finance(user_message)
            if general_results:
                context_parts.append("\n🌐 **WEB ARAMA SONUÇLARI:**")
                for i, r in enumerate(general_results[:3], 1):
                    context_parts.append(f"{i}. {r['title']}")
                    if r['snippet']:
                        context_parts.append(f"   → {r['snippet'][:150]}...")
        
        if context_parts:
            return "\n".join(context_parts)
        return ""
        
    except Exception as e:
        logger.error(f"Error building enhanced context: {e}")
        return ""
