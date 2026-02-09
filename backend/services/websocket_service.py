"""
WebSocket Price Streaming Service
Provides real-time price updates via CCXT WebSocket connections.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from collections import defaultdict
import ccxt.pro as ccxtpro  # CCXT Pro for WebSocket support

# Configure logging
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Default symbols to stream
DEFAULT_SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "ADA/USDT",
    "DOGE/USDT",
    "AVAX/USDT",
    "DOT/USDT",
    "MATIC/USDT",
    "LINK/USDT",
    "UNI/USDT",
    "LTC/USDT",
    "ATOM/USDT",
    "FIL/USDT",
]

# Primary exchange for streaming (most reliable)
PRIMARY_EXCHANGE = "binance"

# Broadcast throttle (ms) - don't flood clients
MIN_BROADCAST_INTERVAL_MS = 100


# ═══════════════════════════════════════════════════════════════════════════════
# CONNECTION MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class ConnectionManager:
    """Manages WebSocket connections to frontend clients."""
    
    def __init__(self):
        self.active_connections: Set[Any] = set()
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket):
        """Add a new client connection."""
        async with self._lock:
            self.active_connections.add(websocket)
            logger.info(f"Client connected. Total: {len(self.active_connections)}")
    
    async def disconnect(self, websocket):
        """Remove a client connection."""
        async with self._lock:
            self.active_connections.discard(websocket)
            logger.info(f"Client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return
        
        message_json = json.dumps(message)
        
        async with self._lock:
            dead_connections = set()
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_json)
                except Exception:
                    dead_connections.add(connection)
            
            # Remove dead connections
            for dead in dead_connections:
                self.active_connections.discard(dead)
    
    @property
    def client_count(self) -> int:
        return len(self.active_connections)


# Global connection manager
manager = ConnectionManager()


# ═══════════════════════════════════════════════════════════════════════════════
# PRICE STREAMING SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class PriceStreamingService:
    """
    Streams real-time prices from exchanges via CCXT Pro WebSocket.
    Broadcasts updates to connected frontend clients.
    """
    
    def __init__(self):
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.exchange = None
        self.last_prices: Dict[str, float] = {}
        self.last_broadcast: Dict[str, float] = defaultdict(float)
        self._lock = asyncio.Lock()
    
    async def start(self):
        """Start the price streaming service."""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._stream_prices())
        logger.info("Price streaming service started.")
    
    async def stop(self):
        """Stop the price streaming service."""
        self.running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        if self.exchange:
            try:
                await self.exchange.close()
            except Exception:
                pass
        
        logger.info("Price streaming service stopped.")
    
    async def _create_exchange(self):
        """Create CCXT Pro exchange instance."""
        try:
            exchange_class = getattr(ccxtpro, PRIMARY_EXCHANGE, None)
            if exchange_class is None:
                logger.error(f"Exchange {PRIMARY_EXCHANGE} not found in CCXT Pro")
                return None
            
            self.exchange = exchange_class({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                }
            })
            return self.exchange
        except Exception as e:
            logger.error(f"Failed to create exchange: {e}")
            return None
    
    async def _stream_prices(self):
        """Main streaming loop - watches tickers and broadcasts updates."""
        while self.running:
            try:
                if not self.exchange:
                    await self._create_exchange()
                    if not self.exchange:
                        await asyncio.sleep(5)
                        continue
                
                logger.info(f"Starting price stream for {len(DEFAULT_SYMBOLS)} symbols...")
                
                # Watch all symbols
                while self.running:
                    try:
                        # Watch tickers for all symbols (CCXT Pro efficiently batches)
                        tickers = await self.exchange.watch_tickers(DEFAULT_SYMBOLS)
                        
                        # Process each ticker update
                        for symbol, ticker in tickers.items():
                            await self._process_ticker(symbol, ticker)
                        
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"Error watching tickers: {e}")
                        await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Stream error: {e}")
                if self.running:
                    await asyncio.sleep(5)
                    # Reset exchange on error
                    if self.exchange:
                        try:
                            await self.exchange.close()
                        except Exception:
                            pass
                        self.exchange = None
    
    async def _process_ticker(self, symbol: str, ticker: dict):
        """Process a ticker update and broadcast if significant."""
        try:
            current_price = ticker.get('last') or ticker.get('close')
            if not current_price:
                return
            
            now = asyncio.get_event_loop().time() * 1000  # ms
            
            # Throttle broadcasts per symbol
            last_broadcast_time = self.last_broadcast.get(symbol, 0)
            if now - last_broadcast_time < MIN_BROADCAST_INTERVAL_MS:
                return
            
            # Get previous price for change calculation
            prev_price = self.last_prices.get(symbol)
            
            # Calculate instant change
            instant_change = 0
            if prev_price and prev_price > 0:
                instant_change = ((current_price - prev_price) / prev_price) * 100
            
            # Update stored price
            async with self._lock:
                self.last_prices[symbol] = current_price
                self.last_broadcast[symbol] = now
            
            # Build update message
            update = {
                "type": "price_update",
                "symbol": symbol.replace("/", ""),  # BTC/USDT -> BTCUSDT
                "symbol_formatted": symbol,  # Keep formatted version
                "price": current_price,
                "bid": ticker.get('bid'),
                "ask": ticker.get('ask'),
                "high_24h": ticker.get('high'),
                "low_24h": ticker.get('low'),
                "volume_24h": ticker.get('baseVolume'),
                "change_24h": ticker.get('percentage'),
                "instant_change": round(instant_change, 4),
                "direction": "up" if instant_change > 0 else "down" if instant_change < 0 else "none",
                "timestamp": datetime.now().isoformat(),
            }
            
            # Broadcast to connected clients
            await manager.broadcast(update)
            
        except Exception as e:
            logger.error(f"Error processing ticker {symbol}: {e}")
    
    def get_last_prices(self) -> Dict[str, float]:
        """Get the latest cached prices."""
        return dict(self.last_prices)
    
    @property
    def is_running(self) -> bool:
        return self.running


# Global service instance
price_streaming_service = PriceStreamingService()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager."""
    return manager


def get_streaming_service() -> PriceStreamingService:
    """Get the global streaming service."""
    return price_streaming_service


async def get_streaming_stats() -> dict:
    """Get streaming service statistics."""
    return {
        "is_running": price_streaming_service.is_running,
        "connected_clients": manager.client_count,
        "symbols_tracked": len(DEFAULT_SYMBOLS),
        "symbols": DEFAULT_SYMBOLS,
        "last_prices_count": len(price_streaming_service.last_prices),
        "exchange": PRIMARY_EXCHANGE,
    }
