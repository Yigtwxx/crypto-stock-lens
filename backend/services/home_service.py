"""
Home Page Service
Fetches Funding Rates, Liquidations (Binance), and On-Chain Data (Mock).
"""

import httpx
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import xml.etree.ElementTree as ET

# ==========================================
# CONSTANTS & CACHE
# ==========================================

BINANCE_FUTURES_API = "https://fapi.binance.com"

# Cache structure
_home_cache: Dict[str, Any] = {
    "funding": {"data": None, "timestamp": None},
    "liquidations": {"data": None, "timestamp": None},
    "onchain": {"data": None, "timestamp": None},
    "macro": {"data": None, "timestamp": None},
}

CACHE_TTL = 60  # seconds


# ==========================================
# MACRO CALENDAR
# ==========================================

async def fetch_macro_calendar() -> List[Dict]:
    """
    Fetch US Economic Calendar from ForexFactory (XML).
    Filters for USD events with Medium/High impact.
    """
    global _home_cache
    
    if _is_cache_valid("macro"):
        return _home_cache["macro"]["data"]

    try:
        async with httpx.AsyncClient() as client:
            # ForexFactory Weekly XML Feed
            response = await client.get("https://nfs.faireconomy.media/ff_calendar_thisweek.xml", timeout=10)
            
            if response.status_code != 200:
                print(f"Failed to fetch ForexFactory calendar: {response.status_code}")
                return []
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            events = []
            for event in root.findall('event'):
                country = event.find('country').text
                
                # Filter for USD events only (as requested)
                if country != 'USD':
                    continue
                    
                impact = event.find('impact').text
                # Filter for Medium and High impact to reduce noise
                if impact not in ['Medium', 'High']:
                    continue
                
                title = event.find('title').text
                date_str = event.find('date').text  # MM-DD-YYYY
                time_str = event.find('time').text  # 1:30pm
                
                # Combine date/time parsing if needed, but for display raw strings might be fine
                # or formatting them nicely.
                
                forecast = event.find('forecast').text or ""
                previous = event.find('previous').text or ""
                
                events.append({
                    "title": title,
                    "country": country,
                    "date": date_str,
                    "time": time_str,
                    "impact": impact,
                    "forecast": forecast,
                    "previous": previous
                })
            
            # Since XML is this week's events, we might want to sort them or just return all
            # They usually come sorted by date.
            
            _update_cache("macro", events)
            return events

    except Exception as e:
        print(f"Error fetching macro calendar: {e}")
        return []

# ==========================================
# FUNDING RATES
# ==========================================

async def fetch_funding_rates() -> List[Dict]:
    """
    Fetch real-time funding rates for top coins from Binance Futures.
    Returns: List of {symbol, rate, time_until_funding}
    """
    global _home_cache
    
    # Check cache
    if _is_cache_valid("funding"):
        return _home_cache["funding"]["data"]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BINANCE_FUTURES_API}/fapi/v1/premiumIndex", timeout=10)
            data = response.json()
            
            # Filter for top USDT pairs
            top_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT"]
            results = []
            
            for item in data:
                symbol = item["symbol"]
                if symbol in top_symbols:
                    funding_rate = float(item["lastFundingRate"])
                    # Annualized rate = funding_rate * 3 * 365 (assuming 8h interval)
                    # But usually display as 8h rate percentage
                    
                    results.append({
                        "symbol": symbol.replace("USDT", ""),
                        "rate": funding_rate, 
                        "rate_formatted": f"{funding_rate * 100:.4f}%",
                        "index_price": float(item["indexPrice"]),
                        "mark_price": float(item["markPrice"]),
                        "next_funding_time": item["nextFundingTime"]
                    })
            
            # Sort by absolute funding rate (highest intensity first)
            results.sort(key=lambda x: abs(x["rate"]), reverse=True)
            
            _update_cache("funding", results)
            return results
            
    except Exception as e:
        print(f"Error fetching funding rates: {e}")
        return []


# ==========================================
# LIQUIDATIONS
# ==========================================

async def fetch_liquidations() -> List[Dict]:
    """
    Fetch recent liquidation orders from Binance Futures.
    Iterates through top symbols to ensure we get data.
    Returns: List of {symbol, side, quantity, price, value_usd, time}
    """
    global _home_cache
    
    if _is_cache_valid("liquidations"):
        return _home_cache["liquidations"]["data"]

    try:
        async with httpx.AsyncClient() as client:
            all_orders = []
            # Fetch for top volatile assets to find liquidations
            target_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
            
            for symbol in target_symbols:
                try:
                    response = await client.get(
                        f"{BINANCE_FUTURES_API}/fapi/v1/allForceOrders", 
                        params={"symbol": symbol, "limit": 10},
                        timeout=5
                    )
                    if response.status_code == 200:
                        data = response.json()
                        all_orders.extend(data)
                except Exception:
                    continue
            
            cleaned_data = []
            for item in all_orders:
                qty = float(item["origQty"])
                price = float(item["price"])
                value_usd = qty * price
                
                # "SELL" = Long Liquidated, "BUY" = Short Liquidated
                cleaned_data.append({
                    "symbol": item["symbol"].replace("USDT", ""),
                    "side": "Long" if item["side"] == "SELL" else "Short",
                    "price": price,
                    "amount_usd": value_usd,
                    "time_ago": _get_time_ago(item["time"]),
                    "timestamp": item["time"]
                })
            
            # Sort by timestamp descending (newest first)
            cleaned_data.sort(key=lambda x: x["timestamp"], reverse=True)
            
            # If still empty (market is calm), add a fake one for UI test if needed, 
            # but better to show empty than fake.
            
            result = cleaned_data[:50]
            _update_cache("liquidations", result)
            return result

    except Exception as e:
        print(f"Error fetching liquidations: {e}")
        return []


# ==========================================
# ON-CHAIN DATA (MOCK)
# ==========================================

async def fetch_onchain_data() -> Dict[str, Any]:
    """
    Generates realistic Mock On-Chain Data.
    Since real on-chain APIs are expensive (Glassnode, Nansen), we mock this
    to demonstrate the UI capability.
    """
    if _is_cache_valid("onchain"):
        return _home_cache["onchain"]["data"]

    # Generate realistic flux
    btc_active_addresses = int(random.gauss(950000, 20000))
    eth_active_addresses = int(random.gauss(450000, 15000))
    
    # Gas (Gwei)
    eth_gas = int(random.gauss(15, 5))
    if eth_gas < 5: eth_gas = 5
    
    data = {
        "active_addresses": {
            "btc": btc_active_addresses,
            "eth": eth_active_addresses,
            "btc_change_24h": round(random.uniform(-5, 5), 2),
            "eth_change_24h": round(random.uniform(-5, 5), 2),
        },
        "transactions_24h": {
            "btc": int(random.gauss(350000, 10000)),
            "eth": int(random.gauss(1100000, 50000)),
        },
        "network_load": {
            "eth_gas_gwei": eth_gas,
            "btc_mempool_size_vbytes": int(random.gauss(15000000, 5000000)),
        },
        "exchange_flows": {
            # Negative = Outflow (Bullish), Positive = Inflow (Bearish)
            "btc_net_flow_usd": round(random.uniform(-100000000, 50000000), 2),
            "eth_net_flow_usd": round(random.uniform(-50000000, 30000000), 2),
        }
    }
    
    _update_cache("onchain", data)
    return data


# ==========================================
# HELPERS
# ==========================================

def _is_cache_valid(key: str) -> bool:
    cache = _home_cache[key]
    if cache["data"] is None or cache["timestamp"] is None:
        return False
    
    elapsed = (datetime.now() - cache["timestamp"]).total_seconds()
    return elapsed < CACHE_TTL

def _update_cache(key: str, data: Any):
    _home_cache[key] = {
        "data": data,
        "timestamp": datetime.now()
    }

def _get_time_ago(timestamp_ms: int) -> str:
    # Convert binance timestamp (ms) to readable string
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    if seconds < 60:
        return f"{int(seconds)}s ago"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    else:
        return f"{int(seconds // 3600)}h ago"
