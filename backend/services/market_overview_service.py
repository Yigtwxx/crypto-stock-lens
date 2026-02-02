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
    Fetch market overview data from Binance API with coin metadata from CoinGecko.
    Returns coin prices, 24h changes, logos, names, and market stats.
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
            # Fetch coin metadata first (with logos and names)
            coin_metadata = await _fetch_coin_metadata(client)
            
            # Fetch 24h ticker data for all coins at once from Binance
            response = await client.get("https://api.binance.com/api/v3/ticker/24hr")
            response.raise_for_status()
            all_tickers = response.json()
            
            # Filter only USDT pairs and exclude unwanted tokens
            usdt_tickers = [
                t for t in all_tickers 
                if t["symbol"].endswith("USDT") 
                and not t["symbol"].endswith("DOWNUSDT")
                and not t["symbol"].endswith("UPUSDT")
                and not t["symbol"].startswith("TUSD")
                and not t["symbol"].startswith("BUSD")
                and not t["symbol"].startswith("USDC")
                and not t["symbol"].startswith("FDUSD")
                and not t["symbol"].startswith("BFUSD")
                and not t["symbol"].startswith("USD1")
                and float(t.get("quoteVolume", 0)) > 1000000  # Min $1M volume
            ]
            
            # Sort by quote volume (trading volume in USDT) descending
            usdt_tickers.sort(key=lambda x: float(x.get("quoteVolume", 0)), reverse=True)
            
            # Take top N coins
            for ticker in usdt_tickers[:TOP_COINS_COUNT]:
                symbol = ticker["symbol"]
                price = float(ticker["lastPrice"])
                change_24h = float(ticker["priceChangePercent"])
                volume_24h = float(ticker["quoteVolume"])
                high_24h = float(ticker["highPrice"])
                low_24h = float(ticker["lowPrice"])
                
                total_volume_24h += volume_24h
                
                # Clean symbol name (remove USDT)
                coin_symbol = symbol.replace("USDT", "")
                
                # Get metadata from CoinGecko
                meta = coin_metadata.get(coin_symbol, {})
                
                coins_data.append({
                    "symbol": coin_symbol,
                    "name": meta.get("name", coin_symbol),
                    "logo": meta.get("logo", ""),
                    "price": price,
                    "change_24h": change_24h,
                    "volume_24h": volume_24h,
                    "high_24h": high_24h,
                    "low_24h": low_24h,
                    "market_cap": meta.get("market_cap", 0),
                    "market_cap_rank": meta.get("market_cap_rank", 0)
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
