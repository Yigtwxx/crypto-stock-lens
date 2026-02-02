"""Stock Market Overview service using httpx for NASDAQ stocks."""
import httpx
from datetime import datetime
from typing import Dict, List, Optional
import asyncio

# Cache for stock data (2 minutes)
_stock_cache: dict = {
    "data": None,
    "timestamp": None
}

# Cache for CNN Fear & Greed (10 minutes for stocks)
_fear_greed_stock_cache: dict = {
    "data": None,
    "timestamp": None
}

CACHE_DURATION_SECONDS = 120  # 2 minutes
FEAR_GREED_CACHE_DURATION = 600  # 10 minutes

# Top 30 NASDAQ stocks by market cap  
NASDAQ_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX",
    "AMD", "ADBE", "PEP", "CSCO", "INTC", "CMCSA", "TMUS", "TXN", "QCOM", "INTU",
    "AMGN", "ISRG", "HON", "AMAT", "BKNG", "SBUX", "GILD", "ADP", "VRTX", "PYPL"
]

# Stock metadata (name and sector)
STOCK_METADATA = {
    "AAPL": {"name": "Apple Inc.", "sector": "Technology"},
    "MSFT": {"name": "Microsoft Corporation", "sector": "Technology"},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology"},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Consumer"},
    "NVDA": {"name": "NVIDIA Corporation", "sector": "Technology"},
    "META": {"name": "Meta Platforms Inc.", "sector": "Technology"},
    "TSLA": {"name": "Tesla Inc.", "sector": "Automotive"},
    "AVGO": {"name": "Broadcom Inc.", "sector": "Technology"},
    "COST": {"name": "Costco Wholesale", "sector": "Retail"},
    "NFLX": {"name": "Netflix Inc.", "sector": "Entertainment"},
    "AMD": {"name": "Advanced Micro Devices", "sector": "Technology"},
    "ADBE": {"name": "Adobe Inc.", "sector": "Technology"},
    "PEP": {"name": "PepsiCo Inc.", "sector": "Consumer"},
    "CSCO": {"name": "Cisco Systems", "sector": "Technology"},
    "INTC": {"name": "Intel Corporation", "sector": "Technology"},
    "CMCSA": {"name": "Comcast Corporation", "sector": "Media"},
    "TMUS": {"name": "T-Mobile US", "sector": "Telecom"},
    "TXN": {"name": "Texas Instruments", "sector": "Technology"},
    "QCOM": {"name": "Qualcomm Inc.", "sector": "Technology"},
    "INTU": {"name": "Intuit Inc.", "sector": "Technology"},
    "AMGN": {"name": "Amgen Inc.", "sector": "Healthcare"},
    "ISRG": {"name": "Intuitive Surgical", "sector": "Healthcare"},
    "HON": {"name": "Honeywell International", "sector": "Industrial"},
    "AMAT": {"name": "Applied Materials", "sector": "Technology"},
    "BKNG": {"name": "Booking Holdings", "sector": "Travel"},
    "SBUX": {"name": "Starbucks Corporation", "sector": "Consumer"},
    "GILD": {"name": "Gilead Sciences", "sector": "Healthcare"},
    "ADP": {"name": "Automatic Data Processing", "sector": "Technology"},
    "VRTX": {"name": "Vertex Pharmaceuticals", "sector": "Healthcare"},
    "PYPL": {"name": "PayPal Holdings", "sector": "Fintech"},
}

# Stock logos (company logos from Clearbit)
STOCK_LOGOS = {
    "AAPL": "https://logo.clearbit.com/apple.com",
    "MSFT": "https://logo.clearbit.com/microsoft.com",
    "GOOGL": "https://logo.clearbit.com/google.com",
    "AMZN": "https://logo.clearbit.com/amazon.com",
    "NVDA": "https://logo.clearbit.com/nvidia.com",
    "META": "https://logo.clearbit.com/meta.com",
    "TSLA": "https://logo.clearbit.com/tesla.com",
    "AVGO": "https://logo.clearbit.com/broadcom.com",
    "COST": "https://logo.clearbit.com/costco.com",
    "NFLX": "https://logo.clearbit.com/netflix.com",
    "AMD": "https://logo.clearbit.com/amd.com",
    "ADBE": "https://logo.clearbit.com/adobe.com",
    "PEP": "https://logo.clearbit.com/pepsico.com",
    "CSCO": "https://logo.clearbit.com/cisco.com",
    "INTC": "https://logo.clearbit.com/intel.com",
    "CMCSA": "https://logo.clearbit.com/comcast.com",
    "TMUS": "https://logo.clearbit.com/t-mobile.com",
    "TXN": "https://logo.clearbit.com/ti.com",
    "QCOM": "https://logo.clearbit.com/qualcomm.com",
    "INTU": "https://logo.clearbit.com/intuit.com",
    "AMGN": "https://logo.clearbit.com/amgen.com",
    "ISRG": "https://logo.clearbit.com/intuitive.com",
    "HON": "https://logo.clearbit.com/honeywell.com",
    "AMAT": "https://logo.clearbit.com/appliedmaterials.com",
    "BKNG": "https://logo.clearbit.com/booking.com",
    "SBUX": "https://logo.clearbit.com/starbucks.com",
    "GILD": "https://logo.clearbit.com/gilead.com",
    "ADP": "https://logo.clearbit.com/adp.com",
    "VRTX": "https://logo.clearbit.com/vrtx.com",
    "PYPL": "https://logo.clearbit.com/paypal.com",
}

# Market cap estimates (in billions) for ranking
# These are approximate values for sorting purposes
MARKET_CAP_ESTIMATES = {
    "AAPL": 3000, "MSFT": 2800, "GOOGL": 1800, "AMZN": 1700, "NVDA": 3000,
    "META": 1300, "TSLA": 800, "AVGO": 700, "COST": 400, "NFLX": 300,
    "AMD": 200, "ADBE": 250, "PEP": 230, "CSCO": 200, "INTC": 100,
    "CMCSA": 150, "TMUS": 200, "TXN": 180, "QCOM": 200, "INTU": 180,
    "AMGN": 150, "ISRG": 170, "HON": 140, "AMAT": 150, "BKNG": 150,
    "SBUX": 100, "GILD": 110, "ADP": 120, "VRTX": 100, "PYPL": 80,
}


async def fetch_single_stock(client: httpx.AsyncClient, symbol: str) -> Optional[dict]:
    """
    Fetch single stock data from Yahoo Finance chart API.
    """
    try:
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
        response = await client.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data.get("chart", {}).get("result", [])
            if result:
                meta = result[0].get("meta", {})
                
                price = meta.get("regularMarketPrice", 0) or 0
                prev_close = meta.get("previousClose", meta.get("chartPreviousClose", price)) or price
                change = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                volume = meta.get("regularMarketVolume", 0) or 0
                high = meta.get("regularMarketDayHigh", 0) or 0
                low = meta.get("regularMarketDayLow", 0) or 0
                
                stock_meta = STOCK_METADATA.get(symbol, {"name": symbol, "sector": "Other"})
                
                # Use estimated market cap for sorting
                est_market_cap = MARKET_CAP_ESTIMATES.get(symbol, 50) * 1e9
                
                return {
                    "symbol": symbol,
                    "name": stock_meta["name"],
                    "sector": stock_meta.get("sector", "Other"),
                    "logo": STOCK_LOGOS.get(symbol, ""),
                    "price": float(price),
                    "change_24h": float(change),
                    "volume_24h": float(volume * price) if price else 0,
                    "high_24h": float(high),
                    "low_24h": float(low),
                    "market_cap": float(est_market_cap),
                    "market_cap_rank": 0
                }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
    
    return None


async def fetch_nasdaq_overview() -> dict:
    """
    Fetch NASDAQ stock overview data.
    Returns stock prices, changes, and market stats.
    """
    global _stock_cache
    
    # Check cache
    if _stock_cache["data"] and _stock_cache["timestamp"]:
        elapsed = (datetime.now() - _stock_cache["timestamp"]).total_seconds()
        if elapsed < CACHE_DURATION_SECONDS:
            return _stock_cache["data"]
    
    stocks_data = []
    total_volume = 0
    total_market_cap = 0
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch all stocks concurrently
            tasks = [fetch_single_stock(client, symbol) for symbol in NASDAQ_STOCKS]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict):
                    stocks_data.append(result)
            
            if not stocks_data:
                print("No stock data received from Yahoo Finance")
            
            # Sort by market cap descending
            stocks_data.sort(key=lambda x: x.get("market_cap", 0), reverse=True)
            
            # Assign ranks
            for i, stock in enumerate(stocks_data):
                stock["market_cap_rank"] = i + 1
            
            # Calculate totals
            for stock in stocks_data:
                total_volume += stock.get("volume_24h", 0)
                total_market_cap += stock.get("market_cap", 0)
            
            # Get Fear & Greed for stocks
            fear_greed = await fetch_stock_fear_greed(client)
        
        result = {
            "coins": stocks_data,  # Using "coins" key for frontend compatibility
            "total_volume_24h": total_volume,
            "total_market_cap": total_market_cap,
            "btc_dominance": 0,  # N/A for stocks
            "active_cryptocurrencies": len(stocks_data),
            "fear_greed": fear_greed,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update cache only if we got data
        if stocks_data:
            _stock_cache["data"] = result
            _stock_cache["timestamp"] = datetime.now()
        
        return result
        
    except Exception as e:
        print(f"Error fetching NASDAQ overview: {e}")
    
    # Return cached data if available or empty response
    if _stock_cache["data"]:
        return _stock_cache["data"]
    
    return {
        "coins": [],
        "total_volume_24h": 0,
        "total_market_cap": 0,
        "btc_dominance": 0,
        "active_cryptocurrencies": 0,
        "fear_greed": None,
        "timestamp": datetime.now().isoformat()
    }


async def fetch_stock_fear_greed(client: Optional[httpx.AsyncClient] = None) -> dict:
    """
    Fetch CNN Fear & Greed Index for stock market.
    """
    global _fear_greed_stock_cache
    
    # Check cache
    if _fear_greed_stock_cache["data"] and _fear_greed_stock_cache["timestamp"]:
        elapsed = (datetime.now() - _fear_greed_stock_cache["timestamp"]).total_seconds()
        if elapsed < FEAR_GREED_CACHE_DURATION:
            return _fear_greed_stock_cache["data"]
    
    try:
        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=10.0)
            should_close = True
        
        # CNN Fear & Greed API
        response = await client.get(
            "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        
        if should_close:
            await client.aclose()
        
        if response.status_code == 200:
            data = response.json()
            
            # Get current score
            fear_greed_data = data.get("fear_and_greed", {})
            score = fear_greed_data.get("score", 50)
            rating = fear_greed_data.get("rating", "Neutral")
            
            result = {
                "value": int(score),
                "classification": rating,
                "timestamp": datetime.now().isoformat()
            }
            
            # Update cache
            _fear_greed_stock_cache["data"] = result
            _fear_greed_stock_cache["timestamp"] = datetime.now()
            
            return result
            
    except Exception as e:
        print(f"Error fetching CNN Fear & Greed: {e}")
    
    # Return cached or default
    if _fear_greed_stock_cache["data"]:
        return _fear_greed_stock_cache["data"]
    
    return {
        "value": 50,
        "classification": "Neutral",
        "timestamp": datetime.now().isoformat()
    }
