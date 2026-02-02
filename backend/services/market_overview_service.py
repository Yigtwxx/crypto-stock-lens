"""Market Overview service using CoinGecko and Binance APIs."""
import httpx
from datetime import datetime
from typing import List, Optional, Dict

# Cache for market data (2 minutes)
_market_cache: dict = {
    "data": None,
    "timestamp": None
}

# Cache for coin metadata (logos, names) - longer cache (1 hour)
_coin_metadata_cache: dict = {
    "data": None,
    "timestamp": None
}

CACHE_DURATION_SECONDS = 120  # 2 minutes
METADATA_CACHE_DURATION = 3600  # 1 hour

# Number of top coins to display
TOP_COINS_COUNT = 50


async def _fetch_coin_metadata(client: httpx.AsyncClient) -> Dict[str, dict]:
    """
    Fetch coin metadata (name, logo) from CoinGecko API.
    Returns a dict mapping symbol to metadata.
    """
    global _coin_metadata_cache
    
    # Check cache
    if _coin_metadata_cache["data"] and _coin_metadata_cache["timestamp"]:
        elapsed = (datetime.now() - _coin_metadata_cache["timestamp"]).total_seconds()
        if elapsed < METADATA_CACHE_DURATION:
            return _coin_metadata_cache["data"]
    
    try:
        # Fetch top 100 coins by market cap from CoinGecko
        response = await client.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 250,
                "page": 1,
                "sparkline": False
            },
            timeout=15.0
        )
        
        if response.status_code == 200:
            coins = response.json()
            metadata = {}
            for coin in coins:
                symbol = coin.get("symbol", "").upper()
                metadata[symbol] = {
                    "name": coin.get("name", symbol),
                    "logo": coin.get("image", ""),
                    "market_cap": coin.get("market_cap", 0),
                    "market_cap_rank": coin.get("market_cap_rank", 0)
                }
            
            # Update cache
            _coin_metadata_cache["data"] = metadata
            _coin_metadata_cache["timestamp"] = datetime.now()
            return metadata
            
    except Exception as e:
        print(f"Failed to fetch coin metadata from CoinGecko: {e}")
    
    # Return cached data if available
    if _coin_metadata_cache["data"]:
        return _coin_metadata_cache["data"]
    
    return {}


async def fetch_market_overview() -> dict:
    """
    Fetch market overview data from CoinGecko API (primary) with optional Binance volume data.
    Returns coin prices, 24h changes, logos, names, market caps, and market stats.
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
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Fetch top coins directly from CoinGecko (includes market cap, price, etc.)
            response = await client.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": TOP_COINS_COUNT,
                    "page": 1,
                    "sparkline": False,
                    "price_change_percentage": "24h"
                },
                timeout=15.0
            )
            
            if response.status_code == 200:
                coins = response.json()
                
                for coin in coins:
                    symbol = coin.get("symbol", "").upper()
                    market_cap = coin.get("market_cap", 0) or 0
                    volume_24h = coin.get("total_volume", 0) or 0
                    
                    total_volume_24h += volume_24h
                    
                    coins_data.append({
                        "symbol": symbol,
                        "name": coin.get("name", symbol),
                        "logo": coin.get("image", ""),
                        "price": coin.get("current_price", 0) or 0,
                        "change_24h": coin.get("price_change_percentage_24h", 0) or 0,
                        "volume_24h": volume_24h,
                        "high_24h": coin.get("high_24h", 0) or 0,
                        "low_24h": coin.get("low_24h", 0) or 0,
                        "market_cap": market_cap,
                        "market_cap_rank": coin.get("market_cap_rank", 0) or 0
                    })
            
            # Get global market data from CoinGecko
            global_data = await _fetch_global_market_data(client)
            
            result = {
                "coins": coins_data,
                "total_volume_24h": total_volume_24h,
                "total_market_cap": global_data.get("total_market_cap", 0),
                "btc_dominance": global_data.get("btc_dominance", 0),
                "eth_dominance": global_data.get("eth_dominance", 0),
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
        "eth_dominance": 0,
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
                "eth_dominance": data.get("market_cap_percentage", {}).get("eth", 0),
                "active_cryptocurrencies": data.get("active_cryptocurrencies", 0)
            }
    except Exception as e:
        print(f"CoinGecko API failed (non-critical): {e}")
    
    return {}
