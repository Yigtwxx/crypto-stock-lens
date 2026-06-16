"""Stock Market Overview service using httpx for NASDAQ stocks."""
import logging
import httpx
from datetime import datetime
from typing import Dict, List, Optional
import asyncio

from services.cache import market_cache

logger = logging.getLogger(__name__)

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

STOCK_LOGOS = {symbol: get_stock_logo(symbol) for symbol in NASDAQ_STOCKS}

# Cache for real market cap data (refreshed every 30 min)
_market_cap_cache: dict = {
    "data": {},
    "timestamp": None
}
MARKET_CAP_CACHE_DURATION = 1800  # 30 minutes


def _parse_market_cap_string(value_str: str) -> float:
    """
    Parse abbreviated market cap strings like '3.88T', '458.23B', '12.3M'.
    Returns value in USD.
    """
    if not value_str or not isinstance(value_str, str):
        return 0
    
    value_str = value_str.strip().replace(",", "")
    
    multipliers = {
        'T': 1e12,
        'B': 1e9,
        'M': 1e6,
        'K': 1e3,
    }
    
    for suffix, multiplier in multipliers.items():
        if value_str.upper().endswith(suffix):
            try:
                num = float(value_str[:-1])
                return num * multiplier
            except ValueError:
                return 0
    
    # No suffix — try parsing as plain number
    try:
        return float(value_str)
    except ValueError:
        return 0


async def _fetch_batch_market_caps(client: httpx.AsyncClient, symbols: list) -> dict:
    """
    Fetch market caps for all symbols from stockanalysis.com free API in parallel.
    Returns dict of {symbol: market_cap_usd}.
    """
    global _market_cap_cache

    # Check if cache is still fresh
    if (_market_cap_cache["timestamp"] and
            (datetime.now() - _market_cap_cache["timestamp"]).total_seconds() < MARKET_CAP_CACHE_DURATION and
            len(_market_cap_cache["data"]) >= len(symbols) * 0.5):
        return _market_cap_cache["data"]

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    async def _fetch_one(symbol: str) -> tuple[str, float]:
        try:
            resp = await client.get(
                f"https://api.stockanalysis.com/api/symbol/s/{symbol}/overview",
                headers=headers
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                mcap_str = data.get("marketCap", "")
                if mcap_str:
                    mcap = _parse_market_cap_string(str(mcap_str))
                    if mcap > 0:
                        return symbol, mcap
        except Exception:
            pass
        return symbol, 0.0

    responses = await asyncio.gather(*[_fetch_one(s) for s in symbols])
    result = {sym: cap for sym, cap in responses if cap > 0}

    if result:
        _market_cap_cache["data"].update(result)
        _market_cap_cache["timestamp"] = datetime.now()
        logger.info("Fetched %d market caps from stockanalysis.com", len(result))

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
        logger.warning("Error fetching %s: %s", symbol, e)

    return None


def get_market_status() -> dict:
    """
    Get current NASDAQ market status (US Eastern Time).
    """
    import pytz  # type: ignore

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
        logger.error("Error determining market status: %s", e)
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
    # Check cache first — always refresh market_status since it's time-dependent
    cached = market_cache.get("stock_overview")
    if cached is not None:
        cached_data = cached.copy()
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
                    except Exception:
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
        logger.warning("yfinance failed: %s", e)
    
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
            logger.error("Yahoo Finance v8 fallback also failed: %s", e)
    
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
    except Exception as e:
        logger.warning("Error fetching stock fear/greed: %s", e)
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
    
    market_cache.set("stock_overview", result, CACHE_DURATION_SECONDS)
    return result





async def fetch_stock_fear_greed(client: Optional[httpx.AsyncClient] = None) -> Optional[dict]:
    """
    Fetch CNN Fear & Greed Index for stock market.
    """
    cached = market_cache.get("fear_greed_stock")
    if cached is not None:
        return cached

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

            fear_greed_data = data.get("fear_and_greed", {})
            score = fear_greed_data.get("score", 50)
            rating = fear_greed_data.get("rating", "Neutral")

            result = {
                "value": int(score),
                "classification": rating,
                "timestamp": datetime.now().isoformat()
            }

            market_cache.set("fear_greed_stock", result, FEAR_GREED_CACHE_DURATION)
            return result

    except Exception as e:
        logger.error("Error fetching CNN Fear & Greed: %s", e)

    return market_cache.get_with_fallback("fear_greed_stock")


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
        logger.error("Error fetching global indices: %s", e)
        
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
        logger.error("Error fetching stock context for %s: %s", symbol, e)
    return None
