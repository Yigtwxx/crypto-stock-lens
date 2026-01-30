# Technical Analysis Service v2
"""
Technical Analysis Service - Real market data analysis
Fetches OHLCV data from Binance and calculates accurate support/resistance levels.

IMPROVED VERSION:
- ATR-based support/resistance
- Better target price calculation
- More robust error handling
- Works for all crypto pairs
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
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
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
            print(f"Binance API returned {response.status_code} for {symbol}")
            return []
    except Exception as e:
        print(f"Error fetching klines for {symbol}: {e}")
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


def calculate_atr(klines: List[List], period: int = 14) -> float:
    """
    Calculate Average True Range (ATR) for volatility measurement.
    
    ATR = Average of True Range over period
    True Range = max(High - Low, abs(High - Previous Close), abs(Low - Previous Close))
    """
    if len(klines) < period + 1:
        return 0.0
    
    true_ranges = []
    for i in range(1, len(klines)):
        high = float(klines[i][2])
        low = float(klines[i][3])
        prev_close = float(klines[i-1][4])
        
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        true_ranges.append(tr)
    
    if len(true_ranges) < period:
        return sum(true_ranges) / len(true_ranges) if true_ranges else 0.0
    
    # Calculate ATR using smoothed average
    atr = sum(true_ranges[:period]) / period
    for i in range(period, len(true_ranges)):
        atr = (atr * (period - 1) + true_ranges[i]) / period
    
    return atr


def calculate_pivot_points(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Calculate classic pivot points.
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


def find_significant_levels(klines: List[List], current_price: float, num_levels: int = 3) -> Tuple[List[float], List[float]]:
    """
    Find significant support and resistance levels from price action.
    Uses local highs/lows with volume weighting.
    """
    if len(klines) < 20:
        return [], []
    
    # Get all highs and lows
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    volumes = [float(k[5]) for k in klines]
    
    # Find local extremes (where price reversed)
    potential_resistances = []
    potential_supports = []
    
    for i in range(2, len(klines) - 2):
        # High volume increases significance
        volume_weight = volumes[i] / (sum(volumes) / len(volumes)) if sum(volumes) > 0 else 1.0
        
        # Look for swing highs (local maxima)
        if highs[i] >= max(highs[i-2:i]) and highs[i] >= max(highs[i+1:i+3]):
            if highs[i] > current_price:
                potential_resistances.append((highs[i], volume_weight))
        
        # Look for swing lows (local minima)
        if lows[i] <= min(lows[i-2:i]) and lows[i] <= min(lows[i+1:i+3]):
            if lows[i] < current_price:
                potential_supports.append((lows[i], volume_weight))
    
    # Sort by proximity to current price and volume weight
    potential_resistances.sort(key=lambda x: (x[0] - current_price) / x[1])
    potential_supports.sort(key=lambda x: (current_price - x[0]) / x[1])
    
    # Get unique levels (cluster similar prices)
    def cluster_levels(levels: List[Tuple[float, float]], threshold: float = 0.005) -> List[float]:
        if not levels:
            return []
        clustered = []
        for price, _ in levels:
            # Check if this price is close to an existing cluster
            is_new = True
            for existing in clustered:
                if abs(price - existing) / existing < threshold:
                    is_new = False
                    break
            if is_new:
                clustered.append(price)
            if len(clustered) >= num_levels:
                break
        return clustered
    
    resistances = cluster_levels(potential_resistances)
    supports = cluster_levels(potential_supports)
    
    return supports, resistances


def calculate_rsi(closes: List[float], period: int = 14) -> float:
    """
    Calculate RSI (Relative Strength Index).
    """
    if len(closes) < period + 1:
        return 50.0
    
    changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    
    gains = [c if c > 0 else 0 for c in changes]
    losses = [-c if c < 0 else 0 for c in changes]
    
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
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


def calculate_trend(closes: List[float], short_period: int = 10, long_period: int = 30) -> str:
    """
    Determine trend using EMA crossover.
    """
    if len(closes) < long_period:
        return "neutral"
    
    def ema(data: List[float], period: int) -> float:
        multiplier = 2 / (period + 1)
        ema_val = sum(data[:period]) / period
        for price in data[period:]:
            ema_val = (price - ema_val) * multiplier + ema_val
        return ema_val
    
    short_ema = ema(closes, short_period)
    long_ema = ema(closes, long_period)
    
    if short_ema > long_ema * 1.01:
        return "bullish"
    elif short_ema < long_ema * 0.99:
        return "bearish"
    else:
        return "neutral"


def format_price(price: float) -> str:
    """Format price with appropriate precision."""
    if price >= 10000:
        return f"${price:,.0f}"
    elif price >= 1000:
        return f"${price:,.2f}"
    elif price >= 1:
        return f"${price:.4f}"
    elif price >= 0.01:
        return f"${price:.5f}"
    else:
        return f"${price:.8f}"


def calculate_target_price(
    current_price: float,
    atr: float,
    trend: str,
    rsi: float,
    supports: List[float],
    resistances: List[float]
) -> str:
    """
    Calculate realistic target price based on ATR, trend, and key levels.
    
    Target = Current Price ± (ATR * Multiplier) adjusted by trend and RSI
    """
    if atr == 0:
        atr = current_price * 0.02  # Fallback: 2% of price
    
    # Base multiplier based on trend strength
    if trend == "bullish":
        multiplier = 1.5 if rsi < 60 else 1.0  # Less upside if already overbought
    elif trend == "bearish":
        multiplier = -1.5 if rsi > 40 else -1.0  # Less downside if already oversold
    else:
        multiplier = 0.5 if rsi > 50 else -0.5
    
    # Calculate targets
    if multiplier > 0:
        # Bullish target: aim for next resistance or ATR-based
        base_target = current_price + (atr * multiplier)
        if resistances:
            # Use resistance if it's within reasonable range
            nearest_resistance = resistances[0]
            if nearest_resistance < base_target * 1.5:
                target_low = current_price + (atr * 0.5)
                target_high = nearest_resistance
            else:
                target_low = current_price + (atr * 0.5)
                target_high = base_target
        else:
            target_low = current_price + (atr * 0.5)
            target_high = base_target
    else:
        # Bearish target: aim for next support or ATR-based
        base_target = current_price + (atr * multiplier)
        if supports:
            nearest_support = supports[0]
            if nearest_support > base_target * 0.5:
                target_low = nearest_support
                target_high = current_price - (atr * 0.5)
            else:
                target_low = base_target
                target_high = current_price - (atr * 0.5)
        else:
            target_low = base_target
            target_high = current_price - (atr * 0.5)
    
    # Ensure proper ordering
    if target_low > target_high:
        target_low, target_high = target_high, target_low
    
    return f"{format_price(target_low)} - {format_price(target_high)}"


async def get_technical_analysis(symbol: str) -> Optional[Dict]:
    """
    Get complete technical analysis for a symbol.
    
    Args:
        symbol: TradingView format symbol (e.g., BINANCE:BTCUSDT, NASDAQ:AAPL)
    
    Returns:
        Dictionary with technical analysis data
    """
    # Clean symbol
    parts = symbol.split(':')
    exchange = parts[0] if len(parts) > 1 else ""
    clean_symbol = parts[-1]
    
    # Determine data source
    is_crypto = exchange.upper() == "BINANCE" or clean_symbol.endswith('USDT')
    
    if is_crypto:
        return await get_crypto_analysis(clean_symbol)
    else:
        # For stocks, use fallback percentage-based analysis
        return get_stock_fallback_analysis(symbol)


async def get_crypto_analysis(symbol: str) -> Optional[Dict]:
    """
    Get technical analysis for crypto using Binance API.
    """
    # Ensure symbol is in correct format
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    try:
        # Fetch OHLCV data - use 4h for better signals
        klines_4h = await fetch_klines(symbol, "4h", 100)
        klines_1h = await fetch_klines(symbol, "1h", 100)
        
        # Use 4h for main analysis, 1h for confirmation
        klines = klines_4h if len(klines_4h) >= 50 else klines_1h
        
        if not klines or len(klines) < 20:
            print(f"Not enough data for {symbol}")
            return get_fallback_analysis_for_symbol(symbol)
        
        # Get current price
        current_price = await fetch_current_price(symbol)
        if not current_price:
            current_price = float(klines[-1][4])
        
        # Calculate ATR for volatility
        atr = calculate_atr(klines, 14)
        
        # Calculate pivot points from last 24 candles
        num_candles = min(24, len(klines))
        recent = klines[-num_candles:]
        
        high_period = max(float(k[2]) for k in recent)
        low_period = min(float(k[3]) for k in recent)
        close = float(klines[-1][4])
        
        pivots = calculate_pivot_points(high_period, low_period, close)
        
        # Find significant levels
        swing_supports, swing_resistances = find_significant_levels(klines, current_price, 3)
        
        # Combine pivot and swing levels
        all_supports = [pivots['s1'], pivots['s2']] + swing_supports
        all_resistances = [pivots['r1'], pivots['r2']] + swing_resistances
        
        # Filter valid levels (supports < current, resistances > current)
        supports = sorted([s for s in all_supports if s < current_price], reverse=True)[:2]
        resistances = sorted([r for r in all_resistances if r > current_price])[:2]
        
        # Ensure we have at least 2 levels each using ATR
        while len(supports) < 2:
            last_support = supports[-1] if supports else current_price
            supports.append(last_support - atr)
        while len(resistances) < 2:
            last_resistance = resistances[-1] if resistances else current_price
            resistances.append(last_resistance + atr)
        
        # Calculate RSI
        closes = [float(k[4]) for k in klines]
        rsi = calculate_rsi(closes, 14)
        rsi_signal = get_rsi_signal(rsi)
        
        # Determine trend
        trend = calculate_trend(closes, 10, 30)
        
        # Calculate target price
        target_price = calculate_target_price(
            current_price, atr, trend, rsi, supports, resistances
        )
        
        return {
            "current_price": current_price,
            "support_levels": [format_price(s) for s in supports[:2]],
            "resistance_levels": [format_price(r) for r in resistances[:2]],
            "rsi_signal": rsi_signal,
            "rsi_value": rsi,
            "pivot_point": format_price(pivots['pivot']),
            "target_price": target_price,
            "atr": atr,
            "trend": trend
        }
        
    except Exception as e:
        print(f"Crypto analysis error for {symbol}: {e}")
        return get_fallback_analysis_for_symbol(symbol)


def get_fallback_analysis_for_symbol(symbol: str) -> Dict:
    """
    Generate fallback analysis when API fails.
    Uses percentage-based estimates.
    """
    # We don't have current price, so return placeholders
    return {
        "current_price": 0,
        "support_levels": ["Calculating...", "Calculating..."],
        "resistance_levels": ["Calculating...", "Calculating..."],
        "rsi_signal": "Unavailable",
        "rsi_value": 50,
        "pivot_point": "N/A",
        "target_price": "Data unavailable",
        "error": f"Could not fetch data for {symbol}"
    }


def get_stock_fallback_analysis(symbol: str) -> Dict:
    """
    Generate fallback analysis for stocks.
    Since we don't have free stock OHLCV data, use the LLM's analysis.
    """
    return None  # Return None to let LLM handle stocks
