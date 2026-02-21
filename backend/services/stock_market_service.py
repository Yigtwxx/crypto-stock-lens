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

# Cache for real market cap data (refreshed every 30 min)
_market_cap_cache: dict = {
    "data": {},
    "timestamp": None
}
MARKET_CAP_CACHE_DURATION = 1800  # 30 minutes

# Yahoo Finance crumb session cache
_yf_crumb_cache: dict = {
    "crumb": None,
    "cookies": None,
    "timestamp": None
}


async def _get_yahoo_crumb(client: httpx.AsyncClient) -> tuple:
    """
    Get a valid Yahoo Finance crumb + cookies for authenticated API calls.
    Crumb is required for v7/v10 endpoints.
    """
    global _yf_crumb_cache
    
    # Check crumb cache (valid for 1 hour)
    if (_yf_crumb_cache["crumb"] and _yf_crumb_cache["timestamp"] and
            (datetime.now() - _yf_crumb_cache["timestamp"]).total_seconds() < 3600):
        return _yf_crumb_cache["crumb"], _yf_crumb_cache["cookies"]
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Step 1: Get cookies from Yahoo Finance
        resp = await client.get("https://finance.yahoo.com/quote/AAPL/", headers=headers, follow_redirects=True)
        cookies = dict(resp.cookies)
        
        # Step 2: Get crumb using cookies
        crumb_resp = await client.get(
            "https://query2.finance.yahoo.com/v1/test/getcrumb",
            headers=headers,
            cookies=cookies
        )
        
        if crumb_resp.status_code == 200:
            crumb = crumb_resp.text.strip()
            if crumb and len(crumb) < 50:
                _yf_crumb_cache["crumb"] = crumb
                _yf_crumb_cache["cookies"] = cookies
                _yf_crumb_cache["timestamp"] = datetime.now()
                return crumb, cookies
    except Exception as e:
        print(f"Error getting Yahoo crumb: {e}")
    
    return None, None


async def _fetch_batch_market_caps(client: httpx.AsyncClient, symbols: list) -> dict:
    """
    Batch-fetch market caps for all symbols using Yahoo Finance v7 quote API with crumb auth.
    Returns dict of {symbol: market_cap_usd}.
    """
    global _market_cap_cache
    
    # Check if entire cache is still fresh
    if (_market_cap_cache["timestamp"] and 
            (datetime.now() - _market_cap_cache["timestamp"]).total_seconds() < MARKET_CAP_CACHE_DURATION and
            len(_market_cap_cache["data"]) >= len(symbols) * 0.8):
        return _market_cap_cache["data"]
    
    result = {}
    
    # Strategy 1: Yahoo Finance v7 quote with crumb (batch — single request for all symbols)
    try:
        crumb, cookies = await _get_yahoo_crumb(client)
        if crumb and cookies:
            symbols_str = ",".join(symbols)
            resp = await client.get(
                "https://query2.finance.yahoo.com/v7/finance/quote",
                params={
                    "symbols": symbols_str,
                    "fields": "symbol,marketCap",
                    "crumb": crumb
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
                cookies=cookies
            )
            
            if resp.status_code == 200:
                data = resp.json()
                quotes = data.get("quoteResponse", {}).get("result", [])
                for quote in quotes:
                    sym = quote.get("symbol", "")
                    mcap = quote.get("marketCap", 0)
                    if sym and mcap and mcap > 0:
                        result[sym] = mcap
                
                if result:
                    _market_cap_cache["data"].update(result)
                    _market_cap_cache["timestamp"] = datetime.now()
                    print(f"✓ Fetched {len(result)} market caps via Yahoo v7 batch")
                    return _market_cap_cache["data"]
    except Exception as e:
        print(f"Yahoo v7 batch market cap failed: {e}")
    
    # Strategy 2: Yahoo Finance v8 chart API — get sharesOutstanding and calculate
    try:
        for symbol in symbols:
            if symbol in result:
                continue
            try:
                resp = await client.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                    params={"interval": "1d", "range": "1d"},
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                        "Accept": "application/json"
                    }
                )
                if resp.status_code == 200:
                    chart_data = resp.json()
                    meta = chart_data.get("chart", {}).get("result", [{}])[0].get("meta", {})
                    price = meta.get("regularMarketPrice", 0) or 0
                    # v8 chart often includes sharesOutstanding in meta
                    shares = meta.get("sharesOutstanding", 0) or 0
                    if price > 0 and shares > 0:
                        result[symbol] = price * shares
            except Exception:
                continue
        
        if result:
            _market_cap_cache["data"].update(result)
            _market_cap_cache["timestamp"] = datetime.now()
            print(f"✓ Calculated {len(result)} market caps from v8 sharesOutstanding")
    except Exception as e:
        print(f"v8 shares-based market cap failed: {e}")
    
    return _market_cap_cache["data"]


def _get_cached_market_cap(symbol: str) -> float:
    """Get market cap from cache for a single symbol."""
    return _market_cap_cache["data"].get(symbol, 0)



async def fetch_single_stock(client: httpx.AsyncClient, symbol: str) -> Optional[dict]:
    """
    Fetch single stock data from Yahoo Finance v8 chart API.
    Returns real-time price, change, volume and market cap.
    """
    try:
        # Use v8 chart API (v7 quote API is now deprecated/unauthorized)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
        response = await client.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            chart = data.get("chart", {})
            results = chart.get("result", [])
            
            if results:
                meta = results[0].get("meta", {})
                
                price = meta.get("regularMarketPrice", 0) or 0
                prev_close = meta.get("chartPreviousClose", 0) or meta.get("previousClose", 0) or price
                change = ((price - prev_close) / prev_close * 100) if prev_close and price else 0
                volume = meta.get("regularMarketVolume", 0) or 0
                high = meta.get("regularMarketDayHigh", 0) or 0
                low = meta.get("regularMarketDayLow", 0) or 0
                fifty_two_week_high = meta.get("fiftyTwoWeekHigh", high) or high
                fifty_two_week_low = meta.get("fiftyTwoWeekLow", low) or low
                
                # Get market cap: try from cache first, then calculate from v8 sharesOutstanding
                market_cap = _get_cached_market_cap(symbol)
                if market_cap == 0:
                    shares = meta.get("sharesOutstanding", 0) or 0
                    if shares > 0 and price > 0:
                        market_cap = price * shares
                
                stock_meta = STOCK_METADATA.get(symbol, {
                    "name": meta.get("longName") or meta.get("shortName") or symbol, 
                    "sector": "Other"
                })
                
                return {
                    "symbol": symbol,
                    "name": stock_meta["name"],
                    "sector": stock_meta.get("sector", "Other"),
                    "logo": STOCK_LOGOS.get(symbol, get_stock_logo(symbol)),
                    "price": float(price),
                    "change_24h": round(float(change), 2),
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

def get_market_status() -> dict:
    """
    Get current NASDAQ market status (US Eastern Time).
    """
    from datetime import datetime
    import pytz # type: ignore

    try:
        # Define timezones
        tz_ny = pytz.timezone('America/New_York')
        now_ny = datetime.now(tz_ny)
        
        # Check weekend
        if now_ny.weekday() >= 5: # 5=Saturday, 6=Sunday
            return {
                "status": "Closed",
                "message": "🔴 Closed (Weekend)",
                "color": "red",
                "next_event": "Opens Mon 09:30 ET"
            }
            
        # Convert to Minutes from Midnight for easy comparison
        current_minutes = now_ny.hour * 60 + now_ny.minute
        
        # Market Hours (in minutes)
        # Pre-market: 04:00 (240) - 09:30 (570)
        # Open: 09:30 (570) - 16:00 (960)
        # After-hours: 16:00 (960) - 20:00 (1200)
        
        pre_market_start = 4 * 60
        open_start = 9 * 60 + 30
        close_start = 16 * 60
        after_hours_end = 20 * 60
        
        if pre_market_start <= current_minutes < open_start:
            # Pre-market
            minutes_to_open = open_start - current_minutes
            hrs = minutes_to_open // 60
            mins = minutes_to_open % 60
            return {
                "status": "Pre-market",
                "message": f"🟠 Pre-market • Opens in {hrs}h {mins}m",
                "color": "orange",
                "next_event": "Market Opens 09:30 ET"
            }
            
        elif open_start <= current_minutes < close_start:
            # Market Open
            minutes_to_close = close_start - current_minutes
            hrs = minutes_to_close // 60
            mins = minutes_to_close % 60
            return {
                "status": "Open",
                "message": f"🟢 Market Open • Closes in {hrs}h {mins}m",
                "color": "green",
                "next_event": "Closes 16:00 ET"
            }
            
        elif close_start <= current_minutes < after_hours_end:
            # After-hours
            return {
                "status": "After-hours",
                "message": "🌙 After-hours",
                "color": "blue",
                "next_event": "Pre-market 04:00 ET"
            }
            
        else:
            # Closed (Night)
            return {
                "status": "Closed",
                "message": "🔴 Closed",
                "color": "red",
                "next_event": "Pre-market 04:00 ET"
            }
            
    except Exception as e:
        print(f"Error determining market status: {e}")
        return {
            "status": "Unknown",
            "message": "--",
            "color": "gray",
            "next_event": ""
        }

async def fetch_nasdaq_overview() -> dict:
    """
    Fetch NASDAQ stock overview data.
    Uses yfinance first, falls back to Yahoo Finance v8 chart API.
    """
    global _stock_cache
    
    # Check cache first
    if _stock_cache["data"] and _stock_cache["timestamp"]:
        elapsed = (datetime.now() - _stock_cache["timestamp"]).total_seconds()
        if elapsed < CACHE_DURATION_SECONDS:
            # Ensure we update the status even if cached, as time flows
            # But deep copy to not mutate cache in place improperly if threading issues (simple dict ok)
            cached_data = _stock_cache["data"].copy()
            cached_data["market_status"] = get_market_status()
            return cached_data
    
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
                
                # Use fast_info for critical data (faster and more reliable)
                price = ticker.fast_info.last_price
                market_cap = ticker.fast_info.market_cap
                
                # Fallback to info for metadata if needed, but prioritize fast_info 
                # fast_info doesn't have name/sector, so we rely on our metadata map or try info as backup
                
                if price and price > 0:
                    # Try to get extra info if available without blocking
                    # We can use our static metadata to be safe and fast
                    stock_meta = STOCK_METADATA.get(symbol, {"name": symbol, "sector": "Other"})
                    
                    # Try getting volume from fast_info (not always available directly in same way, need verification)
                    # fast_info doesn't have 24h volume directly behaving like 'regularMarketVolume'
                    # We can try accessing it, otherwise use fallback
                    # Actually fast_info has 'last_volume' but it might be 0 until close.
                    # safer to try info for volume/change if we want, or calculate change manually if we had prev close.
                    
                    # For change, fast_info has 'previous_close'
                    prev_close = ticker.fast_info.previous_close
                    change = ((price - prev_close) / prev_close * 100) if prev_close else 0
                    
                    # Volume from info (might trigger fetch) or estimate
                    # To allow 'lazy' loading, access info properties only if necessary
                    # But for now, let's trust fast_info for the heavy lifting (price/cap)
                    
                    # We will try to fetch full info for other fields, but if it fails, we keep price/cap
                    try:
                        info = ticker.info
                        volume = info.get('volume', 0)
                        high = info.get('dayHigh', price)
                        low = info.get('dayLow', price)
                        year_high = info.get('fiftyTwoWeekHigh', price)
                        year_low = info.get('fiftyTwoWeekLow', price)
                    except:
                        # minimal fallback if full info fetch fails
                        volume = 0
                        high = price
                        low = price
                        year_high = price
                        year_low = price
                    
                    stocks_data.append({
                        "symbol": symbol,
                        "name": stock_meta["name"],
                        "sector": stock_meta.get("sector", "Other"),
                        "logo": STOCK_LOGOS.get(symbol, get_stock_logo(symbol)),
                        "price": float(price),
                        "change_24h": float(change),
                        "volume_24h": float(volume * price),
                        "high_24h": float(high),
                        "low_24h": float(low),
                        "market_cap": float(market_cap),
                        "market_cap_rank": 0,
                        "fifty_two_week_high": float(year_high),
                        "fifty_two_week_low": float(year_low)
                    })
            except Exception as e:
                # If individual ticker fails, skip
                continue
    except Exception as e:
        print(f"yfinance failed: {e}")
    
    # If yfinance failed or returned too few, try Yahoo Finance v8 chart API directly
    if len(stocks_data) < 5:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                # First, batch-fetch market caps for all symbols
                await _fetch_batch_market_caps(client, NASDAQ_STOCKS)
                
                # Then fetch individual stock data (will use cached market caps)
                tasks = [fetch_single_stock(client, symbol) for symbol in NASDAQ_STOCKS]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, dict) and result.get("price", 0) > 0:
                        stocks_data.append(result)
        except Exception as e:
            print(f"Yahoo Finance v8 fallback also failed: {e}")
    
    # Sort and rank all data regardless of source
    if stocks_data:
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
        fear_greed = None
    
    result = {
        "coins": stocks_data,
        "total_volume_24h": total_volume,
        "total_market_cap": total_market_cap,
        "btc_dominance": 0,
        "active_cryptocurrencies": len(stocks_data),
        "fear_greed": fear_greed,
        "timestamp": datetime.now().isoformat(),
        "market_status": get_market_status()
    }
    
    # Update cache
    _stock_cache["data"] = result
    _stock_cache["timestamp"] = datetime.now()
    
    return result





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
    
    # Return cached data if available, otherwise None
    if _fear_greed_stock_cache["data"]:
        return _fear_greed_stock_cache["data"]
    
    return None


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

def is_stock_symbol(symbol: str) -> bool:
    """Check if the symbol is a known stock symbol."""
    return symbol in NASDAQ_STOCKS or symbol in STOCK_METADATA or symbol in GLOBAL_INDICES

async def get_stock_context_data(symbol: str) -> Optional[Dict]:
    """
    Get formatted stock data for AI context.
    Usage: Chat Service
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            data = await fetch_single_stock(client, symbol)
            if data:
                # Add Fear & Greed for context
                fg = await fetch_stock_fear_greed(client)
                data["fear_greed"] = fg
                return data
    except Exception as e:
        print(f"Error fetching stock context for {symbol}: {e}")
    return None
