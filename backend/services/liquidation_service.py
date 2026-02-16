import asyncio
import json
import logging
import os
import httpx
import websockets
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque

# Configure logging
logger = logging.getLogger(__name__)

# Constants
BINANCE_WS_URL = "wss://fstream.binance.com/ws/!forceOrder@arr"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "liquidations.json")
MAX_HISTORY_LEN = 10000  # Increased for persistence
SAVE_INTERVAL = 60       # Save to disk every 60 seconds

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

class LiquidationService:
    def __init__(self):
        self.liquidations = deque(maxlen=MAX_HISTORY_LEN)
        self.running = False
        self.task = None
        self.save_task = None
        self._lock = asyncio.Lock()
        self.load_data()

    def load_data(self):
        """Load persisted liquidation data from disk."""
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    # Convert timestamps back to logic if needed, but JSON is simple
                    # We might need to parse 'received_at' back to datetime if we use it for logic
                    # For simplicty, we store timestamps as simple floats/iso strings in JSON
                    # and re-parse them when loading.
                    
                    loaded_count = 0
                    for item in data:
                        # Parse received_at string back to datetime
                        if isinstance(item.get('received_at'), str):
                            item['received_at'] = datetime.fromisoformat(item['received_at'])
                        self.liquidations.append(item)
                        loaded_count += 1
                    
                    logger.info(f"Loaded {loaded_count} liquidation events from disk.")
        except Exception as e:
            logger.error(f"Failed to load liquidation data: {e}")

    async def save_data_loop(self):
        """Periodically save data to disk."""
        while self.running:
            await asyncio.sleep(SAVE_INTERVAL)
            await self.save_data()

    async def save_data(self):
        """Save current liquidations to disk."""
        try:
            async with self._lock:
                data_to_save = list(self.liquidations)
                
            # Convert datetime objects to string for JSON serialization
            serializable_data = []
            for item in data_to_save:
                item_copy = item.copy()
                if isinstance(item_copy.get('received_at'), datetime):
                    item_copy['received_at'] = item_copy['received_at'].isoformat()
                serializable_data.append(item_copy)

            # Sort by timestamp to ensure order
            serializable_data.sort(key=lambda x: x['timestamp'])

            # Write to temp file then rename for atomic write
            temp_file = f"{DATA_FILE}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(serializable_data, f)
            os.replace(temp_file, DATA_FILE)
            logger.info(f"Saved {len(serializable_data)} events to disk.")
            
        except Exception as e:
            logger.error(f"Failed to save liquidation data: {e}")

    async def start(self):
        """Start the WebSocket listener in the background."""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._connect_and_listen())
        self.save_task = asyncio.create_task(self.save_data_loop())
        logger.info("Liquidation service started.")

    async def stop(self):
        """Stop the WebSocket listener."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        if self.save_task:
            self.save_task.cancel()
            try:
                await self.save_task
            except asyncio.CancelledError:
                pass
                
        # Final save
        await self.save_data()
        logger.info("Liquidation service stopped.")

    async def _connect_and_listen(self):
        """Connect to Binance WebSocket and listen for liquidation events."""
        while self.running:
            ws = None
            try:
                # Use ping_interval=None to disable automatic keepalive pings
                # This prevents keepalive timeout errors on shutdown
                ws = await websockets.connect(
                    BINANCE_WS_URL,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=5
                )
                logger.info(f"Connected to Binance Liquidation Stream: {BINANCE_WS_URL}")
                
                while self.running:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=30)
                        data = json.loads(message)
                        await self._process_message(data)
                    except asyncio.TimeoutError:
                        # No message received in 30s, just continue
                        continue
                    except asyncio.CancelledError:
                        break
                        
            except asyncio.CancelledError:
                logger.info("WebSocket listener cancelled.")
                break
            except websockets.exceptions.ConnectionClosed:
                if self.running:
                    logger.warning("WebSocket connection closed. Reconnecting in 5s...")
                    await asyncio.sleep(5)
            except Exception as e:
                if self.running:
                    logger.error(f"Error in liquidation listener: {e}")
                    await asyncio.sleep(5)
            finally:
                if ws:
                    try:
                        await ws.close()
                    except Exception:
                        pass

    async def _process_message(self, data: dict):
        """Process incoming liquidation data."""
        try:
            items = data if isinstance(data, list) else [data]
            
            async with self._lock:
                now = datetime.now()
                for item in items:
                    if item.get('e') != 'forceOrder':
                        continue
                        
                    order = item.get('o', {})
                    symbol = order.get('s')
                    side = order.get('S') # SELL = Long Liquidation, BUY = Short Liquidation
                    quantity = float(order.get('q', 0))
                    price = float(order.get('p', 0))
                    amount_usd = quantity * price
                    timestamp = order.get('T')
                    
                    liquidation_event = {
                        "symbol": symbol,
                        "side": side,
                        "amount_usd": amount_usd,
                        "price": price,
                        "timestamp": timestamp, # ms timestamp
                        "received_at": now
                    }
                    
                    self.liquidations.append(liquidation_event)
                    
        except Exception as e:
            logger.error(f"Error processing liquidation message: {e}")

    async def get_heatmap_data(self, time_window_seconds: int = 3600) -> List[Dict]:
        """Get aggregated liquidation data for the heatmap widget."""
        async with self._lock:
            now = datetime.now()
            cutoff = now - timedelta(seconds=time_window_seconds)
            
            agg: Dict[str, Dict] = {}
            current_data = list(self.liquidations)
            
            for event in current_data:
                # Ensure received_at is datetime (it should be if loaded correctly, but safety check)
                received_at = event['received_at']
                if isinstance(received_at, str):
                    received_at = datetime.fromisoformat(received_at)

                if received_at < cutoff:
                    continue
                
                symbol = event['symbol']
                amount = event['amount_usd']
                side = event['side']
                
                if symbol not in agg:
                    agg[symbol] = {
                        "symbol": symbol,
                        "total_usd": 0.0,
                        "long_usd": 0.0,
                        "short_usd": 0.0,
                        "count": 0
                    }
                
                agg[symbol]["total_usd"] += amount
                agg[symbol]["count"] += 1
                
                if side == "SELL":
                    agg[symbol]["long_usd"] += amount
                else:
                    agg[symbol]["short_usd"] += amount

            result = []
            for symbol, data in agg.items():
                if data["total_usd"] < 1000: 
                    continue
                    
                result.append({
                    "symbol": symbol,
                    "value": round(data["total_usd"], 2),
                    "long_liq": round(data["long_usd"], 2),
                    "short_liq": round(data["short_usd"], 2),
                    "count": data["count"]
                })
            
            result.sort(key=lambda x: x["value"], reverse=True)
            return result[:50]

    async def get_liquidation_history(self, symbol: str) -> List[Dict]:
        """Get all stored liquidation history for a specific symbol."""
        # Clean symbol format if needed (TradingView "BINANCE:BTCUSDT" -> "BTCUSDT")
        clean_symbol = symbol.split(':')[-1]
        
        async with self._lock:
            # Filter liquidations for this symbol
            history = [
                {
                    "price": event["price"],
                    "amount_usd": event["amount_usd"],
                    "side": event["side"],
                    "timestamp": event["timestamp"]
                }
                for event in self.liquidations
                if event["symbol"] == clean_symbol
            ]
            
            # Sort by timestamp
            history.sort(key=lambda x: x["timestamp"])
            return history

    async def get_liquidation_levels(
        self, 
        symbol: str, 
        price_min: float,
        price_max: float,
        num_bins: int = 100,
        leverage: int = 50
    ) -> Dict:
        """
        Get cumulative liquidation levels grouped by price bins.
        Returns data for Coinglass-style heatmap visualization.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            price_min: Minimum price for binning
            price_max: Maximum price for binning  
            num_bins: Number of price bins (default 100)
            leverage: Leverage assumption for liquidation levels (default 50x)
            
        Returns:
            Dictionary with:
            - levels: Array of {price, long_liq, short_liq, total}
            - max_value: Maximum liquidation value (for normalization)
            - bin_size: Size of each price bin
        """
        clean_symbol = symbol.split(':')[-1]
        
        # Calculate bin size
        price_range = price_max - price_min
        bin_size = price_range / num_bins
        
        if bin_size <= 0:
            return {"levels": [], "max_value": 0, "bin_size": 0}
        
        # Initialize bins
        bins = {}
        for i in range(num_bins):
            bin_price = price_min + (i + 0.5) * bin_size  # Use mid-point of bin
            bins[i] = {
                "price": round(bin_price, 2),
                "long_liq": 0.0,
                "short_liq": 0.0,
                "total": 0.0
            }
        
        async with self._lock:
            # Process all liquidations for this symbol
            for event in self.liquidations:
                if event["symbol"] != clean_symbol:
                    continue
                    
                liq_price = event["price"]
                amount = event["amount_usd"]
                side = event["side"]
                
                # For each liquidation, calculate where positions would be liquidated
                # at different leverage levels
                
                # Original position entry price is estimated from liquidation price
                # Long liquidation: entry = liq_price * (1 + 1/leverage)
                # Short liquidation: entry = liq_price * (1 - 1/leverage)
                
                if side == "SELL":  # Long position liquidated
                    # This was a long position, liquidated at liq_price
                    # Entry was above: entry = liq_price * (1 + 1/leverage)
                    entry_price = liq_price * (1 + 1/leverage)
                    
                    # The liquidation affects price levels around and below entry
                    # Show liquidation accumulation at the actual liq_price level
                    bin_index = int((liq_price - price_min) / bin_size)
                    if 0 <= bin_index < num_bins:
                        bins[bin_index]["long_liq"] += amount
                        bins[bin_index]["total"] += amount
                        
                else:  # Short position liquidated (BUY)
                    # This was a short position, liquidated at liq_price
                    # Entry was below: entry = liq_price * (1 - 1/leverage)
                    entry_price = liq_price * (1 - 1/leverage)
                    
                    bin_index = int((liq_price - price_min) / bin_size)
                    if 0 <= bin_index < num_bins:
                        bins[bin_index]["short_liq"] += amount
                        bins[bin_index]["total"] += amount
        
        # Convert to list and find max value
        levels = list(bins.values())
        max_value = max((b["total"] for b in levels), default=0)
        
        # Filter out empty bins for efficiency
        levels = [b for b in levels if b["total"] > 0]
        
        # Sort by price
        levels.sort(key=lambda x: x["price"])
        
        return {
            "levels": levels,
            "max_value": round(max_value, 2),
            "bin_size": round(bin_size, 2),
            "price_min": round(price_min, 2),
            "price_max": round(price_max, 2)
        }

    async def fetch_candles(self, symbol: str, interval: str = '1h', limit: int = 168) -> List[Dict]:
        """
        Fetch OHLCV candles from Binance Public API.
        Default: 1h interval, 168 candles (1 week).
        """
        clean_symbol = symbol.split(':')[-1]
        url = "https://fapi.binance.com/fapi/v1/klines"
        params = {
            "symbol": clean_symbol,
            "interval": interval,
            "limit": limit
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    # Parse Binance format: [Open Time, Open, High, Low, Close, Volume, ...]
                    candles = []
                    for k in data:
                        candles.append({
                            "time": int(k[0] / 1000), # Unix timestamp in seconds for lightweight-charts
                            "open": float(k[1]),
                            "high": float(k[2]),
                            "low": float(k[3]),
                            "close": float(k[4]),
                            "volume": float(k[5])
                        })
                    return candles
                else:
                    logger.error(f"Binance candle fetch failed: {response.text}")
                    return []
            except Exception as e:
                logger.error(f"Error fetching candles: {e}")
                return []

# Global instance
liquidation_service = LiquidationService()
