
import httpx
import asyncio
from datetime import datetime
from typing import List, Dict

# Cache configuration
_whale_cache = {
    "data": [],
    "timestamp": None
}
CACHE_DURATION = 10  # 10 seconds (near real-time)

# Tracked Pairs for Whale Activity
TRACKED_PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
MIN_WHALE_VALUE_USD = 500000  # $500k minimum trade size

async def fetch_whale_trades() -> Dict:
    """
    Fetch recent large trades from Binance AggTrades.
    """
    global _whale_cache
    
    # Check cache
    if _whale_cache["timestamp"]:
        elapsed = (datetime.now() - _whale_cache["timestamp"]).total_seconds()
        if elapsed < CACHE_DURATION and _whale_cache["data"]:
            return _whale_cache["data"]

    whale_trades = []
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Fetch trades for all pairs concurrently
            tasks = [_fetch_pair_trades(client, symbol) for symbol in TRACKED_PAIRS]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for res in results:
                if isinstance(res, list):
                    whale_trades.extend(res)
            
            # Sort by time descending (newest first)
            whale_trades.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Calculate Flow Stats
            buy_vol = sum(t['value'] for t in whale_trades if t['side'] == 'buy')
            sell_vol = sum(t['value'] for t in whale_trades if t['side'] == 'sell')
            net_flow = buy_vol - sell_vol
            
            result = {
                "trades": whale_trades[:50],  # Keep top 50 recent
                "stats": {
                    "total_24h_volume": buy_vol + sell_vol,  # Actually just recent window volume for this MVP
                    "net_flow": net_flow,
                    "buy_pressure_percent": (buy_vol / (buy_vol + sell_vol) * 100) if (buy_vol+sell_vol) > 0 else 50
                }
            }
            
            _whale_cache["data"] = result
            _whale_cache["timestamp"] = datetime.now()
            
            return result
            
    except Exception as e:
        print(f"Error fetching whale trades: {e}")
        return {"trades": [], "stats": {}}

async def _fetch_pair_trades(client: httpx.AsyncClient, symbol: str) -> List[Dict]:
    """Fetch aggregated trades for a single pair and filter for whales."""
    try:
        # Get recent trades
        url = "https://api.binance.com/api/v3/aggTrades"
        params = {"symbol": symbol, "limit": 80} # Fetch last 80 trades
        
        response = await client.get(url, params=params)
        if response.status_code == 200:
            trades = response.json()
            whales = []
            
            for t in trades:
                price = float(t['p'])
                quantity = float(t['q'])
                value = price * quantity
                
                if value >= MIN_WHALE_VALUE_USD:
                    # isBuyerMaker = True means SELL (Maker was buyer)
                    # isBuyerMaker = False means BUY (Taker was buyer)
                    side = "sell" if t['m'] else "buy"
                    
                    whales.append({
                        "symbol": symbol.replace("USDT", ""),
                        "price": price,
                        "quantity": quantity,
                        "value": value,
                        "side": side,
                        "timestamp": t['T'] # ms timestamp
                    })
            return whales
    except Exception as e:
        print(f"Error fetching trades for {symbol}: {e}")
    return []
