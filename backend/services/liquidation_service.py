import asyncio
import json
import logging
import websockets
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque

# Configure logging
logger = logging.getLogger(__name__)

# Constants
BINANCE_WS_URL = "wss://fstream.binance.com/ws/!forceOrder@arr"
MAX_HISTORY_LEN = 1000  # Keep last 1000 liquidation events in memory
CLEANUP_INTERVAL = 60   # Cleanup old data every 60 seconds
DATA_TTL = 3600         # Keep data for 1 hour

class LiquidationService:
    def __init__(self):
        self.liquidations = deque(maxlen=MAX_HISTORY_LEN)
        self.running = False
        self.task = None
        self._lock = asyncio.Lock()

    async def start(self):
        """Start the WebSocket listener in the background."""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._connect_and_listen())
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
        logger.info("Liquidation service stopped.")

    async def _connect_and_listen(self):
        """Connect to Binance WebSocket and listen for liquidation events."""
        while self.running:
            try:
                async with websockets.connect(BINANCE_WS_URL) as ws:
                    logger.info(f"Connected to Binance Liquidation Stream: {BINANCE_WS_URL}")
                    
                    while self.running:
                        message = await ws.recv()
                        data = json.loads(message)
                        await self._process_message(data)
                        
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed. Reconnecting in 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error in liquidation listener: {e}")
                await asyncio.sleep(5)

    async def _process_message(self, data: dict):
        """
        Process incoming liquidation data.
        Format example from Binance:
        {
          "e": "forceOrder",
          "E": 1568014460893,
          "o": {
            "s": "BTCUSDT",
            "S": "SELL",  # Side: SELL means Long Liquidated, BUY means Short Liquidated
            "o": "LIMIT",
            "f": "IOC",
            "q": "0.014", # Quantity
            "p": "9910",  # Price
            "ap": "9905.04",
            "X": "FILLED",
            "l": "0.014",
            "z": "0.014",
            "T": 1568014460891
          }
        }
        """
        try:
            # Handle both single object and list of objects (though !forceOrder@arr sends partial stream info, usually a dict wrapper)
            # The documentation says !forceOrder@arr string, but usually it comes as a payload.
            # actually !forceOrder@arr payload is: {"e":"forceOrder", ...}
            
            # If data is a list (some streams do this), iterate
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
                    # average_price = float(order.get('ap', 0)) # Average filled price is better if available
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
        """
        Get aggregated liquidation data for the heatmap.
        Aggregates by symbol over the last `time_window_seconds`.
        """
        async with self._lock:
            now = datetime.now()
            cutoff = now - timedelta(seconds=time_window_seconds)
            
            # Aggregation dictionary: symbol -> {total_usd, long_usd, short_usd}
            agg: Dict[str, Dict] = {}
            
            current_data = list(self.liquidations)
            
            for event in current_data:
                if event['received_at'] < cutoff:
                    continue
                
                symbol = event['symbol']
                amount = event['amount_usd']
                side = event['side']
                
                if symbol not in agg:
                    agg[symbol] = {
                        "symbol": symbol,
                        "total_usd": 0.0,
                        "long_usd": 0.0,   # SELL side = Longs getting rekt
                        "short_usd": 0.0,  # BUY side = Shorts getting rekt
                        "count": 0
                    }
                
                agg[symbol]["total_usd"] += amount
                agg[symbol]["count"] += 1
                
                if side == "SELL":
                    agg[symbol]["long_usd"] += amount
                else:
                    agg[symbol]["short_usd"] += amount

            # Convert to list and calculate dominance
            result = []
            for symbol, data in agg.items():
                if data["total_usd"] < 1000: # Filter excessive noise
                    continue
                    
                # Determine dominant side and color intensity
                is_long_heavy = data["long_usd"] > data["short_usd"]
                dominant_side = "Long" if is_long_heavy else "Short"
                
                # Net Difference: Net > 0 means Longs Liquidated (Red), Net < 0 means Shorts Liquidated (Green)
                # Actually lets map it simply:
                # Long Liquidation (SELL) -> Price goes DOWN -> Bearish for price, but denotes "Longs Rekt" (Red)
                # Short Liquidation (BUY) -> Price goes UP -> Bullish for price, but denotes "Shorts Rekt" (Green)
                
                # We want to enable the frontend to color it.
                # Let's return raw values.
                
                result.append({
                    "symbol": symbol,
                    "value": round(data["total_usd"], 2), # Size of the box
                    "long_liq": round(data["long_usd"], 2),
                    "short_liq": round(data["short_usd"], 2),
                    "count": data["count"]
                })
            
            # Sort by total value descending
            result.sort(key=lambda x: x["value"], reverse=True)
            
            return result[:50] # Top 50 symbols

# Global instance
liquidation_service = LiquidationService()
