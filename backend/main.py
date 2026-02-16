"""
Oracle-X Backend API
FastAPI server providing news feeds, AI analysis, and blockchain verification.

All endpoint logic has been moved to router modules in the `routers/` directory.
This file handles app creation, middleware, lifecycle events, and router registration.
"""
# Suppress warnings before other imports
import warnings
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")
warnings.filterwarnings("ignore", category=DeprecationWarning)

from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.liquidation_service import liquidation_service

# Import all routers
from routers import news, market, liquidation, watchlist, home, analysis, rag, chat, profile, exchanges, websocket


# ═══════════════════════════════════════════════════════════════════════════════
# APP CREATION
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Oracle-X API",
    description="Financial Intelligence Terminal Backend",
    version="1.0.0"
)


# ═══════════════════════════════════════════════════════════════════════════════
# LIFECYCLE EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════════

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Oracle-X API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTER ROUTERS
# ═══════════════════════════════════════════════════════════════════════════════

app.include_router(news.router)          # /api/news, /api/analyze, /api/symbols, /api/technical, /api/ollama, /api/rag/stats
app.include_router(market.router)        # /api/fear-greed, /api/market-overview, /api/nasdaq-overview, /api/market/indices, /api/heatmap
app.include_router(liquidation.router)   # /api/liquidations/*, /api/market/candles
app.include_router(watchlist.router)     # /api/home/watchlist
app.include_router(home.router)          # /api/home/funding-rates, /api/home/liquidations, /api/home/onchain, /api/home/macro-calendar, /api/onchain/whales
app.include_router(analysis.router)      # /api/analysis/report, /api/analysis/notes
app.include_router(rag.router)           # /api/rag/initialize, /api/rag/stats (v2), /api/rag/query
app.include_router(chat.router)          # /api/chat, /api/chat/status, /api/chat/history
app.include_router(profile.router)       # /api/profile/*
app.include_router(exchanges.router)     # /api/exchanges, /api/multi-exchange, /api/arbitrage
app.include_router(websocket.router)     # /ws/prices, /api/websocket/status


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
