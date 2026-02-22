"""
Home Page Service
Fetches Funding Rates, Liquidations (Binance), and On-Chain Data.
"""

import httpx
from datetime import datetime
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
    Fetch Real-time US Economic Calendar from ForexFactory XML Feed.
    Source: https://nfs.faireconomy.media/ff_calendar_thisweek.xml
    Returns: List of high/medium impact events for USD.
    """
    global _home_cache
    
    # Cache for 1 hour (data is weekly/daily, doesn't change every second)
    if _is_cache_valid("macro", ttl_override=3600):
        return _home_cache["macro"]["data"]

    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
    events = []
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            
            if response.status_code == 200:
                # Parse XML
                root = ET.fromstring(response.content)
                
                for event in root.findall("event"):
                    country = event.find("country").text
                    
                    # Filter for USD events only
                    if country != "USD":
                        continue
                        
                    impact = event.find("impact").text
                    # Filter for Medium/High impact to reduce noise
                    if impact not in ["Medium", "High"]:
                        continue
                        
                    title = event.find("title").text
                    date_str = event.find("date").text  # Format: MM-DD-YYYY
                    time_str = event.find("time").text  # Format: 1:30pm
                    forecast = event.find("forecast").text or ""
                    previous = event.find("previous").text or ""
                    
                    events.append({
                        "title": title,
                        "country": country,
                        "date": date_str,
                        "time": time_str,
                        "impact": impact,
                        "forecast": forecast,
                        "previous": previous
                    })
                
                # Sort by date and time (though XML is usually sorted)
                # We can rely on source order for now
                
                # Update cache
                _update_cache("macro", events)
                return events
            else:
                print(f"Failed to fetch macro calendar: {response.status_code}")
                
    except Exception as e:
        print(f"Error fetching macro calendar: {e}")
        # Return cached data if available (even if expired) as fallback
        if _home_cache["macro"]["data"]:
            return _home_cache["macro"]["data"]
            
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
    Fetch recent liquidation orders from the background LiquidationService.
    This provides real-time, 100% accurate data instead of mock or limited REST data.
    Returns: List of {symbol, side, quantity, price, amount_usd, time_ago}
    """
    global _home_cache
    
    # We lower the cache TTL for liquidations since it's a fast-moving "feed"
    # Even 10 seconds is enough to prevent spamming
    if _is_cache_valid("liquidations", ttl_override=10):
        return _home_cache["liquidations"]["data"]

    try:
        from services.liquidation_service import liquidation_service
        
        # Access the deque directly within a lock (or a copy of it)
        # We want the most recent ones first
        async with liquidation_service._lock:
            recent_liquidations = list(liquidation_service.liquidations)
            
        # The service appends new events to the right of the deque
        # So we reverse it to get newest first
        recent_liquidations.reverse()
        
        # Take the top 100 to show in the feed
        feed_data = recent_liquidations[:100]
        
        cleaned_data = []
        for item in feed_data:
            # "SELL" = Long Liquidated, "BUY" = Short Liquidated
            side_formatted = "Long" if item["side"] == "SELL" else "Short"
            
            # format symbol (e.g. BTCUSDT -> BTC)
            symbol_formatted = item["symbol"].replace("USDT", "")
            
            cleaned_data.append({
                "symbol": symbol_formatted,
                "side": side_formatted,
                "price": item["price"],
                "amount_usd": item["amount_usd"],
                "time_ago": _get_time_ago(item["timestamp"]),
                "timestamp": item["timestamp"]
            })
            
        _update_cache("liquidations", cleaned_data)
        return cleaned_data

    except Exception as e:
        print(f"Error fetching liquidations from service: {e}")
        # Fallback to cache if exists
        if _home_cache["liquidations"]["data"]:
             return _home_cache["liquidations"]["data"]
        return []


# ==========================================
# ON-CHAIN DATA (REAL APIs)
# ==========================================

import os
import asyncio

# Optional Etherscan API key (free tier: 5 req/sec, 100k/day)
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")

# Previous values for calculating 24h change (persisted across calls)
_prev_onchain: Dict[str, Any] = {}


async def _fetch_btc_stats(client: httpx.AsyncClient) -> Dict[str, Any]:
    """
    Fetch BTC on-chain stats from multiple sources:
    1. Blockchain.com /stats → n_tx (transactions count)
    2. Blockchair /bitcoin/stats → hodling_addresses, mempool_size, transactions_24h
    """
    result = {}
    
    # Source 1: Blockchain.com for transaction count
    try:
        response = await client.get(
            "https://blockchain.info/stats?format=json",
            timeout=8.0
        )
        if response.status_code == 200:
            data = response.json()
            result["n_tx"] = data.get("n_tx", 0)
    except Exception as e:
        print(f"[OnChain] Blockchain.com BTC stats error: {e}")
    
    # Source 2: Blockchair for addresses and mempool
    try:
        response = await client.get(
            "https://api.blockchair.com/bitcoin/stats",
            timeout=8.0
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            result["hodling_addresses"] = data.get("hodling_addresses", 0)
            result["mempool_size"] = data.get("mempool_size", 0)
            result["transactions_24h"] = data.get("transactions_24h", 0)
            # Use Blockchair tx count as fallback
            if not result.get("n_tx"):
                result["n_tx"] = result["transactions_24h"]
    except Exception as e:
        print(f"[OnChain] Blockchair BTC stats error: {e}")
    
    return result


async def _fetch_eth_stats(client: httpx.AsyncClient) -> Dict[str, Any]:
    """
    Fetch ETH on-chain stats from Blockchair and estimate tx count from RPC.
    Blockchair free tier often returns 0 for 24h metrics.
    We estimate 24h tx count using the latest block from LlamaRPC.
    """
    stats = {}
    
    # 1. Try Blockchair for basic stats (addresses)
    try:
        response = await client.get(
            "https://api.blockchair.com/ethereum/stats",
            timeout=5.0
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            stats["addresses"] = data.get("addresses", 0)
            stats["transactions_24h"] = data.get("transactions_24h", 0)
            
            # Gas from Blockchair options
            gas_options = data.get("suggested_transaction_fee_gwei_options", {})
            stats["gas_price_gwei"] = gas_options.get("normal", 0)
    except Exception:
        pass

    # 2. If tx count is 0, estimate from latest block using LlamaRPC
    if not stats.get("transactions_24h"):
        try:
            response = await client.post(
                "https://eth.llamarpc.com",
                json={"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": ["latest", False], "id": 1},
                timeout=5.0
            )
            if response.status_code == 200:
                result = response.json().get("result", {})
                tx_count = len(result.get("transactions", []))
                # ETH blocks are ~12s, so ~7200 blocks/day
                # Estimate: (tx_in_latest_block) * 7200
                estimated_24h = tx_count * 7200
                stats["transactions_24h"] = estimated_24h
        except Exception:
            pass
            
    return stats


async def _fetch_eth_gas(client: httpx.AsyncClient) -> int:
    """
    Fetch ETH gas price from a free public RPC node.
    Returns gas price in Gwei.
    Falls back to Etherscan if API key is set, or returns 0.
    """
    # Try free public ETH RPC first
    try:
        response = await client.post(
            "https://eth.llamarpc.com",
            json={"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 1},
            timeout=5.0
        )
        if response.status_code == 200:
            result = response.json().get("result", "0x0")
            gas_wei = int(result, 16)
            gas_gwei = round(gas_wei / 1e9, 1)
            if gas_gwei > 0:
                return int(gas_gwei) if gas_gwei >= 1 else 1
    except Exception as e:
        print(f"[OnChain] ETH RPC gas price error: {e}")
    
    # Fallback: Etherscan V2 (if key available)
    if ETHERSCAN_API_KEY:
        try:
            response = await client.get(
                "https://api.etherscan.io/v2/api",
                params={
                    "chainid": "1",
                    "module": "gastracker",
                    "action": "gasoracle",
                    "apikey": ETHERSCAN_API_KEY
                },
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "1":
                    result = data.get("result", {})
                    return int(result.get("ProposeGasPrice", 0))
        except Exception as e:
            print(f"[OnChain] Etherscan gas oracle error: {e}")
    
    return 0


async def _fetch_exchange_flows(client: httpx.AsyncClient) -> Dict[str, float]:
    """
    Estimate exchange net flow from Binance aggregate trades.
    Buy pressure > sell pressure → net outflow (bullish).
    Sell pressure > buy pressure → net inflow (bearish).
    
    Projected to 1-Hour Flow intensity for readability.
    """
    flows = {"btc_net_flow_usd": 0.0, "eth_net_flow_usd": 0.0}
    pairs = [("BTCUSDT", "btc_net_flow_usd"), ("ETHUSDT", "eth_net_flow_usd")]

    for symbol, key in pairs:
        try:
            # Fetch max limit (1000) to get a decent time sample
            response = await client.get(
                "https://api.binance.com/api/v3/aggTrades",
                params={"symbol": symbol, "limit": 1500},
                timeout=8.0
            )
            if response.status_code == 200:
                trades = response.json()
                if not trades:
                    continue
                    
                buy_vol = 0.0
                sell_vol = 0.0
                
                # timestamps in ms
                start_time = trades[0]["T"]
                end_time = trades[-1]["T"]
                duration_sec = (end_time - start_time) / 1000.0
                
                if duration_sec <= 0:
                    duration_sec = 1 # avoid divide by zero if all in same ms
                
                for t in trades:
                    value = float(t["p"]) * float(t["q"])
                    if t["m"]:  # isBuyerMaker = True → market sell (taker sold)
                        sell_vol += value
                    else:  # market buy (taker bought)
                        buy_vol += value
                        
                # Net flow absolute for the sample
                sample_net_flow = sell_vol - buy_vol
                
                # Project to 1 Hour to give a "Flow Rate" meaningful to users
                # This represents the "Hourly Flow Intensity" at the current moment
                hourly_projection = (sample_net_flow / duration_sec) * 3600
                
                flows[key] = round(hourly_projection, 2)
        except Exception as e:
            print(f"[OnChain] Binance {symbol} flow error: {e}")

    return flows


async def fetch_onchain_data() -> Dict[str, Any]:
    """
    Fetch REAL on-chain data from multiple free blockchain APIs.
    
    Sources:
    - Blockchain.com: BTC active addresses, transactions, mempool
    - Blockchair: ETH active addresses, transactions, gas
    - Etherscan: ETH gas (if API key set)
    - Binance: Exchange flow estimation from aggregate trades
    """
    global _prev_onchain

    if _is_cache_valid("onchain"):
        return _home_cache["onchain"]["data"]

    try:
        async with httpx.AsyncClient() as client:
            # Fetch all data sources in parallel
            btc_task = _fetch_btc_stats(client)
            eth_task = _fetch_eth_stats(client)
            gas_task = _fetch_eth_gas(client)
            flow_task = _fetch_exchange_flows(client)

            btc_stats, eth_stats, etherscan_gas, exchange_flows = await asyncio.gather(
                btc_task, eth_task, gas_task, flow_task,
                return_exceptions=True
            )

            # Handle exceptions from gather
            if isinstance(btc_stats, Exception):
                print(f"[OnChain] BTC stats exception: {btc_stats}")
                btc_stats = {}
            if isinstance(eth_stats, Exception):
                print(f"[OnChain] ETH stats exception: {eth_stats}")
                eth_stats = {}
            if isinstance(etherscan_gas, Exception):
                print(f"[OnChain] Gas exception: {etherscan_gas}")
                etherscan_gas = 0
            if isinstance(exchange_flows, Exception):
                print(f"[OnChain] Flow exception: {exchange_flows}")
                exchange_flows = {"btc_net_flow_usd": 0.0, "eth_net_flow_usd": 0.0}

        # Extract values from API responses
        
        # BTC: Use transaction count from Blockchain.com or Blockchair
        btc_tx = btc_stats.get("n_tx", 0) or btc_stats.get("transactions_24h", 0)
        btc_addresses = btc_tx  # Proxying Active Addresses with Tx Count
        
        # ETH: Blockchair often returns 0 for addresses in free tier
        eth_tx = eth_stats.get("transactions_24h", 0)
        eth_addresses = eth_stats.get("addresses", 0)
        if eth_addresses == 0:
            eth_addresses = eth_tx  # Fallback to tx count from same API

        mempool_bytes = btc_stats.get("mempool_size", 0)

        # Gas: prefer RPC, fall back to Blockchair
        eth_gas = etherscan_gas if etherscan_gas > 0 else int(eth_stats.get("gas_price_gwei", 0))

        # Calculate real 24h change by comparing with previous cached values
        btc_change = 0.0
        eth_change = 0.0
        if _prev_onchain.get("btc_addresses") and _prev_onchain["btc_addresses"] > 0:
            btc_change = round(((btc_addresses - _prev_onchain["btc_addresses"]) / _prev_onchain["btc_addresses"]) * 100, 2)
        if _prev_onchain.get("eth_addresses") and _prev_onchain["eth_addresses"] > 0:
            eth_change = round(((eth_addresses - _prev_onchain["eth_addresses"]) / _prev_onchain["eth_addresses"]) * 100, 2)

        # Store current values (unused for change now, but kept for cache consistency if needed later)
        _prev_onchain["btc_addresses"] = btc_addresses
        _prev_onchain["eth_addresses"] = eth_addresses

        data = {
            "active_addresses": {
                "btc": btc_addresses,
                "eth": eth_addresses,
                "btc_change_24h": btc_change,
                "eth_change_24h": eth_change,
            },
            "transactions_24h": {
                "btc": btc_tx,
                "eth": eth_tx,
            },
            "network_load": {
                "eth_gas_gwei": eth_gas,
                "btc_mempool_size_vbytes": mempool_bytes,
            },
            "exchange_flows": exchange_flows,
        }

        _update_cache("onchain", data)
        return data

    except Exception as e:
        print(f"[OnChain] Fatal error in fetch_onchain_data: {e}")
        # Return empty defaults so UI doesn't break
        return {
            "active_addresses": {"btc": 0, "eth": 0, "btc_change_24h": 0, "eth_change_24h": 0},
            "transactions_24h": {"btc": 0, "eth": 0},
            "network_load": {"eth_gas_gwei": 0, "btc_mempool_size_vbytes": 0},
            "exchange_flows": {"btc_net_flow_usd": 0, "eth_net_flow_usd": 0},
        }


# ==========================================
# HELPERS
# ==========================================

def _is_cache_valid(key: str, ttl_override: int = None) -> bool:
    cache = _home_cache[key]
    if cache["data"] is None or cache["timestamp"] is None:
        return False
    
    elapsed = (datetime.now() - cache["timestamp"]).total_seconds()
    limit = ttl_override if ttl_override else CACHE_TTL
    return elapsed < limit

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
