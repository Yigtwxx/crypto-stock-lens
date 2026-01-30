# Technical Analysis Service
"""
Technical Analysis Service - Real market data analysis
Fetches OHLCV data from Binance and calculates accurate support/resistance levels.
"""
import httpx
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class TechnicalLevels:
    """Container for technical analysis results."""
    current_price: float
    support_levels: List[str]
    resistance_levels: List[str]
    pivot_point: float
    rsi: float
    rsi_signal: str
    target_price: str


# Binance API endpoint
BINANCE_API_URL = "https://api.binance.com/api/v3"


async def fetch_klines(symbol: str, interval: str = "1h", limit: int = 100) -> List[List]:
    """
    Fetch OHLCV (candlestick) data from Binance.
    
    Args:
        symbol: Trading pair (e.g., BTCUSDT)
        interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
        limit: Number of candles to fetch
    
    Returns:
        List of OHLCV data
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BINANCE_API_URL}/klines",
                params={
                    "symbol": symbol,
                    "interval": interval,
                    "limit": limit
                }
            )
            if response.status_code == 200:
                return response.json()
            return []
    except Exception as e:
        print(f"Error fetching klines: {e}")
        return []


async def fetch_current_price(symbol: str) -> Optional[float]:
    """Fetch current price from Binance."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{BINANCE_API_URL}/ticker/price",
                params={"symbol": symbol}
            )
            if response.status_code == 200:
                data = response.json()
                return float(data["price"])
            return None
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None


def calculate_pivot_points(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Calculate classic pivot points.
    
    Pivot Point (P) = (High + Low + Close) / 3
    Support 1 (S1) = (2 × P) − High
    Support 2 (S2) = P − (High − Low)
    Resistance 1 (R1) = (2 × P) − Low
    Resistance 2 (R2) = P + (High − Low)
    """
    pivot = (high + low + close) / 3
    
    s1 = (2 * pivot) - high
    s2 = pivot - (high - low)
    s3 = low - 2 * (high - pivot)
    
    r1 = (2 * pivot) - low
    r2 = pivot + (high - low)
    r3 = high + 2 * (pivot - low)
    
    return {
        "pivot": pivot,
        "s1": s1,
        "s2": s2,
        "s3": s3,
        "r1": r1,
        "r2": r2,
        "r3": r3
    }


def find_swing_levels(klines: List[List], lookback: int = 20) -> Tuple[List[float], List[float]]:
    """
    Find swing high and swing low levels from recent price action.
    
    Args:
        klines: OHLCV data from Binance
        lookback: Number of candles to analyze
    
    Returns:
        Tuple of (swing_lows, swing_highs)
    """
    if len(klines) < lookback:
        return [], []
    
    recent_klines = klines[-lookback:]
    
    highs = [float(k[2]) for k in recent_klines]  # High prices
    lows = [float(k[3]) for k in recent_klines]   # Low prices
    
    swing_highs = []
    swing_lows = []
    
    # Find local maxima and minima (swing points)
    for i in range(2, len(highs) - 2):
        # Swing high: higher than neighbors
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
           highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            swing_highs.append(highs[i])
        
        # Swing low: lower than neighbors
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
           lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            swing_lows.append(lows[i])
    
    return swing_lows, swing_highs


def calculate_rsi(closes: List[float], period: int = 14) -> float:
    """
    Calculate RSI (Relative Strength Index).
    
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    """
    if len(closes) < period + 1:
        return 50.0  # Neutral if not enough data
    
    changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    
    gains = [c if c > 0 else 0 for c in changes]
    losses = [-c if c < 0 else 0 for c in changes]
    
    # Calculate initial averages
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    # Smooth the averages
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)


def get_rsi_signal(rsi: float) -> str:
    """Interpret RSI value as a signal."""
    if rsi >= 70:
        return "Overbought"
    elif rsi <= 30:
        return "Oversold"
    elif rsi >= 60:
        return "Bullish Momentum"
    elif rsi <= 40:
        return "Bearish Momentum"
    else:
        return "Neutral"


def format_price(price: float) -> str:
    """Format price with appropriate precision."""
    if price >= 1000:
        return f"${price:,.2f}"
    elif price >= 1:
        return f"${price:.4f}"
    else:
        return f"${price:.6f}"


async def get_technical_analysis(symbol: str) -> Optional[Dict]:
    """
    Get complete technical analysis for a symbol.
    
    Args:
        symbol: TradingView format symbol (e.g., BINANCE:BTCUSDT)
    
    Returns:
        Dictionary with technical analysis data
    """
    # Clean symbol
    clean_symbol = symbol.split(':')[-1] if ':' in symbol else symbol
    
    # Only works for crypto (Binance)
    if not clean_symbol.endswith('USDT'):
        return None
    
    try:
        # Fetch OHLCV data (1 hour candles, last 100)
        klines = await fetch_klines(clean_symbol, "1h", 100)
        
        if not klines or len(klines) < 20:
            return None
        
        # Get current price
        current_price = await fetch_current_price(clean_symbol)
        if not current_price:
            current_price = float(klines[-1][4])  # Use last close price
        
        # Calculate pivot points from last 24h (24 candles for 1h chart)
        recent_24h = klines[-24:] if len(klines) >= 24 else klines
        
        high_24h = max(float(k[2]) for k in recent_24h)
        low_24h = min(float(k[3]) for k in recent_24h)
        close = float(klines[-1][4])
        
        pivots = calculate_pivot_points(high_24h, low_24h, close)
        
        # Find swing levels
        swing_lows, swing_highs = find_swing_levels(klines, 50)
        
        # Calculate RSI
        closes = [float(k[4]) for k in klines]
        rsi = calculate_rsi(closes, 14)
        rsi_signal = get_rsi_signal(rsi)
        
        # Determine support levels (below current price)
        all_supports = [pivots['s1'], pivots['s2']] + swing_lows
        supports = sorted([s for s in all_supports if s < current_price], reverse=True)[:2]
        
        # Determine resistance levels (above current price)
        all_resistances = [pivots['r1'], pivots['r2']] + swing_highs
        resistances = sorted([r for r in all_resistances if r > current_price])[:2]
        
        # Fallback: if not enough levels, use percentage-based
        if len(supports) < 2:
            supports = [current_price * 0.98, current_price * 0.95]
        if len(resistances) < 2:
            resistances = [current_price * 1.02, current_price * 1.05]
        
        # Calculate target price based on trend
        if rsi > 50:
            target = resistances[0] if resistances else current_price * 1.03
            target_str = f"{format_price(target)} - {format_price(target * 1.02)}"
        else:
            target = supports[0] if supports else current_price * 0.97
            target_str = f"{format_price(target * 0.98)} - {format_price(target)}"
        
        return {
            "current_price": current_price,
            "support_levels": [format_price(s) for s in supports[:2]],
            "resistance_levels": [format_price(r) for r in resistances[:2]],
            "rsi_signal": rsi_signal,
            "rsi_value": rsi,
            "pivot_point": format_price(pivots['pivot']),
            "target_price": target_str
        }
        
    except Exception as e:
        print(f"Technical analysis error: {e}")
        return None
