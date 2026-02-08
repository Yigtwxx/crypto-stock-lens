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

# Stock logos - using financial icons API which has better coverage for stock symbols
# Falls back to ui-avatars for stocks without specific logos
def get_stock_logo(symbol: str) -> str:
    """Get logo URL for stock symbol - uses financial icons service or generates fallback."""
    # Financial icons from financialmodelingprep.com and other reliable sources
    logos = {
        "AAPL": "https://financialmodelingprep.com/image-stock/AAPL.png",
        "MSFT": "https://financialmodelingprep.com/image-stock/MSFT.png",
        "GOOGL": "https://financialmodelingprep.com/image-stock/GOOGL.png",
        "AMZN": "https://financialmodelingprep.com/image-stock/AMZN.png",
        "NVDA": "https://financialmodelingprep.com/image-stock/NVDA.png",
        "META": "https://financialmodelingprep.com/image-stock/META.png",
        "TSLA": "https://financialmodelingprep.com/image-stock/TSLA.png",
        "AVGO": "https://financialmodelingprep.com/image-stock/AVGO.png",
        "COST": "https://financialmodelingprep.com/image-stock/COST.png",
        "NFLX": "https://financialmodelingprep.com/image-stock/NFLX.png",
        "AMD": "https://financialmodelingprep.com/image-stock/AMD.png",
        "ADBE": "https://financialmodelingprep.com/image-stock/ADBE.png",
        "PEP": "https://financialmodelingprep.com/image-stock/PEP.png",
        "CSCO": "https://financialmodelingprep.com/image-stock/CSCO.png",
        "INTC": "https://financialmodelingprep.com/image-stock/INTC.png",
        "CMCSA": "https://financialmodelingprep.com/image-stock/CMCSA.png",
        "TMUS": "https://financialmodelingprep.com/image-stock/TMUS.png",
        "TXN": "https://financialmodelingprep.com/image-stock/TXN.png",
        "QCOM": "https://financialmodelingprep.com/image-stock/QCOM.png",
        "INTU": "https://financialmodelingprep.com/image-stock/INTU.png",
        "AMGN": "https://financialmodelingprep.com/image-stock/AMGN.png",
        "ISRG": "https://financialmodelingprep.com/image-stock/ISRG.png",
        "HON": "https://financialmodelingprep.com/image-stock/HON.png",
        "AMAT": "https://financialmodelingprep.com/image-stock/AMAT.png",
        "BKNG": "https://financialmodelingprep.com/image-stock/BKNG.png",
        "SBUX": "https://financialmodelingprep.com/image-stock/SBUX.png",
        "GILD": "https://financialmodelingprep.com/image-stock/GILD.png",
        "ADP": "https://financialmodelingprep.com/image-stock/ADP.png",
        "VRTX": "https://financialmodelingprep.com/image-stock/VRTX.png",
        "PYPL": "https://financialmodelingprep.com/image-stock/PYPL.png",
    }
    if symbol in logos:
        return logos[symbol]
    # Generate fallback with ui-avatars
    return f"https://ui-avatars.com/api/?name={symbol}&background=4f46e5&color=fff&size=64&bold=true"

STOCK_LOGOS = {
    "AAPL": get_stock_logo("AAPL"),
    "MSFT": get_stock_logo("MSFT"),
    "GOOGL": get_stock_logo("GOOGL"),
    "AMZN": get_stock_logo("AMZN"),
    "NVDA": get_stock_logo("NVDA"),
    "META": get_stock_logo("META"),
    "TSLA": get_stock_logo("TSLA"),
    "AVGO": get_stock_logo("AVGO"),
    "COST": get_stock_logo("COST"),
    "NFLX": get_stock_logo("NFLX"),
    "AMD": get_stock_logo("AMD"),
    "ADBE": get_stock_logo("ADBE"),
    "PEP": get_stock_logo("PEP"),
    "CSCO": get_stock_logo("CSCO"),
    "INTC": get_stock_logo("INTC"),
    "CMCSA": get_stock_logo("CMCSA"),
    "TMUS": get_stock_logo("TMUS"),
    "TXN": get_stock_logo("TXN"),
    "QCOM": get_stock_logo("QCOM"),
    "INTU": get_stock_logo("INTU"),
    "AMGN": get_stock_logo("AMGN"),
    "ISRG": get_stock_logo("ISRG"),
    "HON": get_stock_logo("HON"),
    "AMAT": get_stock_logo("AMAT"),
    "BKNG": get_stock_logo("BKNG"),
    "SBUX": get_stock_logo("SBUX"),
    "GILD": get_stock_logo("GILD"),
    "ADP": get_stock_logo("ADP"),
    "VRTX": get_stock_logo("VRTX"),
    "PYPL": get_stock_logo("PYPL"),
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
    Fetch single stock data from Yahoo Finance quote API.
    Returns real-time price, change, volume and market cap.
    """
    try:
        # Use v7 quote API which provides marketCap directly
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        response = await client.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            quote_response = data.get("quoteResponse", {})
            results = quote_response.get("result", [])
            
            if results:
                quote = results[0]
                
                price = quote.get("regularMarketPrice", 0) or 0
                change = quote.get("regularMarketChangePercent", 0) or 0
                volume = quote.get("regularMarketVolume", 0) or 0
                high = quote.get("regularMarketDayHigh", 0) or 0
                low = quote.get("regularMarketDayLow", 0) or 0
                market_cap = quote.get("marketCap", 0) or 0
                
                # 7-day price history (simplified - just current and previous close for calculation)
                prev_close = quote.get("regularMarketPreviousClose", price)
                fifty_two_week_high = quote.get("fiftyTwoWeekHigh", high)
                fifty_two_week_low = quote.get("fiftyTwoWeekLow", low)
                
                stock_meta = STOCK_METADATA.get(symbol, {"name": quote.get("shortName", symbol), "sector": "Other"})
                
                return {
                    "symbol": symbol,
                    "name": stock_meta["name"],
                    "sector": stock_meta.get("sector", "Other"),
                    "logo": STOCK_LOGOS.get(symbol, get_stock_logo(symbol)),
                    "price": float(price),
                    "change_24h": float(change),
                    "volume_24h": float(volume * price) if price else 0,
                    "high_24h": float(high),
                    "low_24h": float(low),
                    "market_cap": float(market_cap),
                    "market_cap_rank": 0,
                    "fifty_two_week_high": float(fifty_two_week_high),
                    "fifty_two_week_low": float(fifty_two_week_low)
                }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
    
    return None


async def fetch_nasdaq_overview() -> dict:
    """
    Fetch NASDAQ stock overview data.
    Uses fallback data when markets are closed or API is unavailable.
    """
    global _stock_cache
    
    # Check cache first
    if _stock_cache["data"] and _stock_cache["timestamp"]:
        elapsed = (datetime.now() - _stock_cache["timestamp"]).total_seconds()
        if elapsed < CACHE_DURATION_SECONDS:
            return _stock_cache["data"]
    
    stocks_data = []
    total_volume = 0
    total_market_cap = 0
    
    # Try yfinance first (works when markets are open)
    try:
        import yfinance as yf
        
        symbols_str = " ".join(NASDAQ_STOCKS)
        tickers = yf.Tickers(symbols_str)
        
        for symbol in NASDAQ_STOCKS:
            try:
                ticker = tickers.tickers.get(symbol)
                if ticker is None:
                    continue
                
                # Try to get basic info
                info = ticker.info
                
                price = info.get('regularMarketPrice') or info.get('currentPrice') or 0
                prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose') or price
                change = ((price - prev_close) / prev_close * 100) if prev_close and price else 0
                market_cap = info.get('marketCap') or 0
                
                if price > 0 and market_cap > 0:
                    stock_meta = STOCK_METADATA.get(symbol, {"name": info.get('shortName', symbol), "sector": "Other"})
                    
                    stocks_data.append({
                        "symbol": symbol,
                        "name": stock_meta["name"],
                        "sector": stock_meta.get("sector", "Other"),
                        "logo": STOCK_LOGOS.get(symbol, get_stock_logo(symbol)),
                        "price": float(price),
                        "change_24h": float(change),
                        "volume_24h": float(info.get('volume', 5_000_000) * price),
                        "high_24h": float(info.get('dayHigh', price * 1.01)),
                        "low_24h": float(info.get('dayLow', price * 0.99)),
                        "market_cap": float(market_cap),
                        "market_cap_rank": 0,
                        "fifty_two_week_high": float(info.get('fiftyTwoWeekHigh', price * 1.15)),
                        "fifty_two_week_low": float(info.get('fiftyTwoWeekLow', price * 0.75))
                    })
            except:
                continue
    except:
        pass  # Silently fall through to fallback
    
    # Use fallback if we didn't get enough data
    if len(stocks_data) < 5:
        stocks_data = _get_fallback_nasdaq_data()
    else:
        # Sort and rank the data we got
        stocks_data.sort(key=lambda x: x.get("market_cap", 0), reverse=True)
        for i, stock in enumerate(stocks_data):
            stock["market_cap_rank"] = i + 1
    
    # Calculate totals
    for stock in stocks_data:
        total_volume += stock.get("volume_24h", 0)
        total_market_cap += stock.get("market_cap", 0)
    
    # Get Fear & Greed for stocks
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            fear_greed = await fetch_stock_fear_greed(client)
    except:
        fear_greed = {"value": 50, "classification": "Neutral", "timestamp": datetime.now().isoformat()}
    
    result = {
        "coins": stocks_data,
        "total_volume_24h": total_volume,
        "total_market_cap": total_market_cap,
        "btc_dominance": 0,
        "active_cryptocurrencies": len(stocks_data),
        "fear_greed": fear_greed,
        "timestamp": datetime.now().isoformat()
    }
    
    # Update cache
    _stock_cache["data"] = result
    _stock_cache["timestamp"] = datetime.now()
    
    return result


def _get_fallback_nasdaq_data() -> list:
    """Return fallback stock data when API is unavailable."""
    # Accurate market caps as of Feb 2025 (in USD)
    fallback_prices = {
        "AAPL": {"price": 227.63, "change": 0.75, "market_cap": 3440e9},   # #1-2
        "MSFT": {"price": 412.38, "change": 0.45, "market_cap": 3060e9},   # #2-3
        "NVDA": {"price": 129.84, "change": 2.15, "market_cap": 3180e9},   # #1-3
        "GOOGL": {"price": 185.34, "change": -0.32, "market_cap": 2280e9}, # #4
        "AMZN": {"price": 228.68, "change": 1.25, "market_cap": 2420e9},   # #5
        "META": {"price": 676.12, "change": 1.85, "market_cap": 1720e9},   # #6
        "AVGO": {"price": 224.76, "change": 0.95, "market_cap": 1050e9},   # #7
        "TSLA": {"price": 352.36, "change": -1.45, "market_cap": 1130e9},  # #8
        "COST": {"price": 1032.89, "change": 0.55, "market_cap": 458e9},   # #9
        "NFLX": {"price": 982.54, "change": 1.35, "market_cap": 422e9},    # #10
        "TMUS": {"price": 246.50, "change": 0.85, "market_cap": 289e9},
        "CSCO": {"price": 63.21, "change": 0.15, "market_cap": 252e9},
        "ADBE": {"price": 438.96, "change": 0.65, "market_cap": 192e9},
        "AMD": {"price": 112.45, "change": -0.85, "market_cap": 182e9},
        "QCOM": {"price": 167.82, "change": 1.05, "market_cap": 186e9},
        "INTU": {"price": 604.23, "change": 0.75, "market_cap": 169e9},
        "TXN": {"price": 192.75, "change": 0.45, "market_cap": 175e9},
        "ISRG": {"price": 578.34, "change": 0.95, "market_cap": 205e9},
        "PEP": {"price": 143.28, "change": 0.25, "market_cap": 196e9},
        "AMGN": {"price": 282.91, "change": 0.35, "market_cap": 151e9},
        "AMAT": {"price": 172.65, "change": 1.25, "market_cap": 142e9},
        "BKNG": {"price": 5012.78, "change": 0.65, "market_cap": 158e9},
        "HON": {"price": 223.45, "change": 0.45, "market_cap": 145e9},
        "VRTX": {"price": 432.18, "change": 1.15, "market_cap": 111e9},
        "ADP": {"price": 302.56, "change": 0.45, "market_cap": 124e9},
        "GILD": {"price": 101.23, "change": 0.25, "market_cap": 126e9},
        "CMCSA": {"price": 36.78, "change": 0.35, "market_cap": 142e9},
        "SBUX": {"price": 112.34, "change": -0.55, "market_cap": 128e9},
        "INTC": {"price": 20.12, "change": -1.25, "market_cap": 87e9},
        "PYPL": {"price": 78.92, "change": -0.75, "market_cap": 82e9},
    }
    
    stocks_data = []
    for symbol in NASDAQ_STOCKS:
        data = fallback_prices.get(symbol, {"price": 100, "change": 0, "market_cap": 50e9})
        stock_meta = STOCK_METADATA.get(symbol, {"name": symbol, "sector": "Other"})
        
        stocks_data.append({
            "symbol": symbol,
            "name": stock_meta["name"],
            "sector": stock_meta.get("sector", "Other"),
            "logo": STOCK_LOGOS.get(symbol, get_stock_logo(symbol)),
            "price": data["price"],
            "change_24h": data["change"],
            "volume_24h": data["price"] * 5_000_000,  # Estimated volume
            "high_24h": data["price"] * 1.02,
            "low_24h": data["price"] * 0.98,
            "market_cap": data["market_cap"],
            "market_cap_rank": 0,
            "fifty_two_week_high": data["price"] * 1.15,
            "fifty_two_week_low": data["price"] * 0.75
        })
    
    # Sort by market cap
    stocks_data.sort(key=lambda x: x["market_cap"], reverse=True)
    for i, stock in enumerate(stocks_data):
        stock["market_cap_rank"] = i + 1
    
    return stocks_data


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


# Global Indices Configuration
GLOBAL_INDICES = {
    "^GSPC": {"name": "S&P 500", "region": "US"},
    "^IXIC": {"name": "NASDAQ", "region": "US"},
    "^DJI": {"name": "Dow Jones", "region": "US"},
    "^FTSE": {"name": "FTSE 100", "region": "UK"},
    "^GDAXI": {"name": "DAX", "region": "DE"},
    "^N225": {"name": "Nikkei 225", "region": "JP"},
    "^HSI": {"name": "Hang Seng", "region": "HK"},
    "^FCHI": {"name": "CAC 40", "region": "FR"},
}

async def fetch_global_indices() -> list:
    """
    Fetch global market indices data.
    """
    indices_data = []
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            tasks = [fetch_single_stock(client, symbol) for symbol in GLOBAL_INDICES.keys()]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict):
                    symbol = result["symbol"]
                    meta = GLOBAL_INDICES.get(symbol, {})
                    result["name"] = meta.get("name", result["name"])
                    result["region"] = meta.get("region", "Global")
                    indices_data.append(result)
                    
    except Exception as e:
        print(f"Error fetching global indices: {e}")
        
    # Sort by region/importance (custom order based on dict keys)
    ordered_data = []
    for symbol in GLOBAL_INDICES.keys():
        item = next((i for i in indices_data if i["symbol"] == symbol), None)
        if item:
            ordered_data.append(item)
            
    return ordered_data
