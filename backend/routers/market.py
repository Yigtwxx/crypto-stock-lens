"""
Market Router
Handles Fear & Greed Index, market overview (crypto + NASDAQ), global indices, and heatmap data.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
import httpx
import asyncio

from models.schemas import FearGreedData, MarketOverview
from services.fear_greed_service import fetch_fear_greed_index
from services.market_overview_service import fetch_market_overview
from services.stock_market_service import fetch_nasdaq_overview

router = APIRouter()


@router.get("/api/fear-greed", response_model=FearGreedData)
async def get_fear_greed():
    """
    Get Crypto Fear & Greed Index from alternative.me API.
    
    Values: 0-25 Extreme Fear, 26-46 Fear, 47-54 Neutral, 55-75 Greed, 76-100 Extreme Greed
    """
    data = await fetch_fear_greed_index()
    return FearGreedData(**data)


@router.get("/api/market-overview", response_model=MarketOverview)
async def get_market_overview():
    """
    Get market overview with top coin prices and global stats.
    
    Includes: BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX
    """
    data = await fetch_market_overview()
    return MarketOverview(**data)


@router.get("/api/nasdaq-overview")
async def get_nasdaq_overview():
    """
    Get NASDAQ stock market overview with top stocks and Fear & Greed index.
    
    Includes: Top 50 NASDAQ stocks by market cap (AAPL, MSFT, GOOGL, etc.)
    """
    data = await fetch_nasdaq_overview()
    return data


@router.get("/api/market/indices")
async def get_market_indices():
    """
    Get global market indices (S&P 500, NASDAQ, Nikkei, FTSE, DAX, etc.)
    
    Returns real-time data from Yahoo Finance.
    """
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
            # Use v8 chart API (v7 quote API is deprecated/unauthorized)
            symbol = idx["symbol"]
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json"
            }
            
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                chart = data.get("chart", {})
                results = chart.get("result", [])
                
                if results:
                    meta = results[0].get("meta", {})
                    current_price = meta.get("regularMarketPrice", 0)
                    prev_close = meta.get("chartPreviousClose", 0) or meta.get("previousClose", 0) or current_price
                    change_percent = ((current_price - prev_close) / prev_close * 100) if prev_close and current_price else 0
                    
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
    
    # Return whatever real data we managed to fetch (may be partial)
    return results


@router.get("/api/heatmap/data")
async def get_heatmap_data():
    """Get multi-metric heatmap data (price, volume, social, developer)."""
    try:
        from services.heatmap_service import fetch_heatmap_data
        return await fetch_heatmap_data()
    except Exception as e:
        print(f"Error fetching heatmap data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
