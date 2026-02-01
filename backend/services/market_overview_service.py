"""Market Overview service using CoinGecko and Binance APIs."""
import httpx
from datetime import datetime
from typing import List, Optional

# Cache for market data (2 minutes)
_market_cache: dict = {
    "data": None,
    "timestamp": None
}

CACHE_DURATION_SECONDS = 120  # 2 minutes

# Top coins to track
TOP_COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT"]


async def fetch_market_overview() -> dict:
    """
    Fetch market overview data from Binance API.
    Returns coin prices, 24h changes, and market stats.
    """
    global _market_cache
    
    # Check cache
    if _market_cache["data"] and _market_cache["timestamp"]:
        elapsed = (datetime.now() - _market_cache["timestamp"]).total_seconds()
        if elapsed < CACHE_DURATION_SECONDS:
            return _market_cache["data"]
    
    coins_data = []
    total_volume_24h = 0
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Fetch 24h ticker data for all coins at once
            response = await client.get("https://api.binance.com/api/v3/ticker/24hr")
            response.raise_for_status()
            all_tickers = response.json()
            
            # Filter to our top coins
            ticker_map = {t["symbol"]: t for t in all_tickers}
            
            for symbol in TOP_COINS:
                if symbol in ticker_map:
                    ticker = ticker_map[symbol]
                    price = float(ticker["lastPrice"])
                    change_24h = float(ticker["priceChangePercent"])
                    volume_24h = float(ticker["quoteVolume"])
                    high_24h = float(ticker["highPrice"])
                    low_24h = float(ticker["lowPrice"])
                    
                    total_volume_24h += volume_24h
                    
                    # Clean symbol name (remove USDT)
                    coin_name = symbol.replace("USDT", "")
                    
                    coins_data.append({
                        "symbol": coin_name,
                        "price": price,
                        "change_24h": change_24h,
                        "volume_24h": volume_24h,
                        "high_24h": high_24h,
                        "low_24h": low_24h
                    })
            
            # Get global market data from CoinGecko (optional, may fail)
            global_data = await _fetch_global_market_data(client)
            
            result = {
                "coins": coins_data,
                "total_volume_24h": total_volume_24h,
                "total_market_cap": global_data.get("total_market_cap", 0),
                "btc_dominance": global_data.get("btc_dominance", 0),
                "active_cryptocurrencies": global_data.get("active_cryptocurrencies", 0),
                "timestamp": datetime.now().isoformat()
            }
            
            # Update cache
            _market_cache["data"] = result
            _market_cache["timestamp"] = datetime.now()
            
            return result
            
    except Exception as e:
        print(f"Error fetching market overview: {e}")
        
    # Return cached data if available, otherwise empty
    if _market_cache["data"]:
        return _market_cache["data"]
    
    return {
        "coins": [],
        "total_volume_24h": 0,
        "total_market_cap": 0,
        "btc_dominance": 0,
        "active_cryptocurrencies": 0,
        "timestamp": datetime.now().isoformat()
    }


async def _fetch_global_market_data(client: httpx.AsyncClient) -> dict:
    """Fetch global market data from CoinGecko."""
    try:
        response = await client.get(
            "https://api.coingecko.com/api/v3/global",
            timeout=5.0
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            return {
                "total_market_cap": data.get("total_market_cap", {}).get("usd", 0),
                "btc_dominance": data.get("market_cap_percentage", {}).get("btc", 0),
                "active_cryptocurrencies": data.get("active_cryptocurrencies", 0)
            }
    except Exception as e:
        print(f"CoinGecko API failed (non-critical): {e}")
    
    return {}
