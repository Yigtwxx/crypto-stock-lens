"""
RAG 2.0 Router
Handles RAG initialization, statistics, and context queries.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/api/rag/initialize")
async def initialize_rag():
    """Initialize RAG 2.0 with historical data (run once)."""
    try:
        from services.rag_v2_service import initialize_rag_v2
        stats = await initialize_rag_v2(symbols=["BTC", "ETH", "SOL"])
        return {"success": True, "stats": stats}
    except Exception as e:
        print(f"Error initializing RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/rag/stats")
async def get_rag_statistics():
    """Get RAG 2.0 statistics."""
    try:
        from services.rag_v2_service import get_rag_stats
        return get_rag_stats()
    except Exception as e:
        return {"status": f"error: {str(e)}", "news_count": 0, "events_count": 0, "prices_count": 0}


@router.get("/api/rag/query")
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
