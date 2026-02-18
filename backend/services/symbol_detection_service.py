"""
Symbol Detection Service - Smart detection of trading symbols from text
Uses CoinGecko API for dynamic coin list and intelligent pattern matching
"""
import httpx
import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Cache for coin data
_coin_cache: Dict[str, dict] = {}
_coin_cache_time: Optional[datetime] = None
CACHE_TTL_MINUTES = 15


@dataclass
class SymbolMatch:
    """Represents a potential symbol match with confidence score"""
    symbol: str  # TradingView format: EXCHANGE:SYMBOL
    score: float
    match_type: str  # 'name', 'ticker', 'pattern', 'alias'


# Extended crypto aliases for Turkish and common variations
CRYPTO_ALIASES = {
    "bitcoin": "BTC",
    "btc": "BTC",
    "₿": "BTC",
    "ethereum": "ETH",
    "eth": "ETH",
    "ether": "ETH",
    "solana": "SOL",
    "sol": "SOL",
    "ripple": "XRP",
    "xrp": "XRP",
    "cardano": "ADA",
    "ADA": "ADA",
    "dogecoin": "DOGE",
    "doge": "DOGE",
    "polkadot": "DOT",
    "dot": "DOT",
    "avalanche": "AVAX",
    "avax": "AVAX",
    "chainlink": "LINK",
    "link": "LINK",
    "polygon": "MATIC",
    "matic": "MATIC",
    "shiba": "SHIB",
    "shiba inu": "SHIB",
    "litecoin": "LTC",
    "ltc": "LTC",
    "uniswap": "UNI",
    "uni": "UNI",
    "cosmos": "ATOM",
    "atom": "ATOM",
    "near": "NEAR",
    "near protocol": "NEAR",
    "arbitrum": "ARB",
    "arb": "ARB",
    "optimism": "OP",
    "op": "OP",
    "aptos": "APT",
    "apt": "APT",
    "sui": "SUI",
    "pepe": "PEPE",
    "bonk": "BONK",
    "wif": "WIF",
    "floki": "FLOKI",
    "tron": "TRX",
    "trx": "TRX",
    "stellar": "XLM",
    "xlm": "XLM",
    "monero": "XMR",
    "xmr": "XMR",
    "binance coin": "BNB",
    "BNB": "BNB",
    "bnb": "BNB",
    "tether": "USDT",
    "usdt": "USDT",
    "usdc": "USDC",
    "pi": "PI",
    "pi network": "PI",
    "pi coin": "PI",
}

# Stock company names and tickers
STOCK_MAPPINGS = {
    # Tech Giants
    "apple": ("AAPL", "NASDAQ"),
    "aapl": ("AAPL", "NASDAQ"),
    "microsoft": ("MSFT", "NASDAQ"),
    "msft": ("MSFT", "NASDAQ"),
    "google": ("GOOGL", "NASDAQ"),
    "alphabet": ("GOOGL", "NASDAQ"),
    "googl": ("GOOGL", "NASDAQ"),
    "amazon": ("AMZN", "NASDAQ"),
    "amzn": ("AMZN", "NASDAQ"),
    "meta": ("META", "NASDAQ"),
    "facebook": ("META", "NASDAQ"),
    "tesla": ("TSLA", "NASDAQ"),
    "tsla": ("TSLA", "NASDAQ"),
    "nvidia": ("NVDA", "NASDAQ"),
    "nvda": ("NVDA", "NASDAQ"),
    "netflix": ("NFLX", "NASDAQ"),
    "nflx": ("NFLX", "NASDAQ"),
    "amd": ("AMD", "NASDAQ"),
    "intel": ("INTC", "NASDAQ"),
    "intc": ("INTC", "NASDAQ"),
    
    # Finance
    "jpmorgan": ("JPM", "NYSE"),
    "jp morgan": ("JPM", "NYSE"),
    "jpm": ("JPM", "NYSE"),
    "goldman sachs": ("GS", "NYSE"),
    "goldman": ("GS", "NYSE"),
    "gs": ("GS", "NYSE"),
    "bank of america": ("BAC", "NYSE"),
    "bac": ("BAC", "NYSE"),
    "visa": ("V", "NYSE"),
    "mastercard": ("MA", "NYSE"),
    "paypal": ("PYPL", "NASDAQ"),
    "pypl": ("PYPL", "NASDAQ"),
    
    # ETFs
    "spy": ("SPY", "AMEX"),
    "s&p 500": ("SPY", "AMEX"),
    "s&p500": ("SPY", "AMEX"),
    "qqq": ("QQQ", "NASDAQ"),
    "nasdaq 100": ("QQQ", "NASDAQ"),
    "dow jones": ("DIA", "AMEX"),
    "dia": ("DIA", "AMEX"),
    
    # Energy
    "exxon": ("XOM", "NYSE"),
    "exxonmobil": ("XOM", "NYSE"),
    "xom": ("XOM", "NYSE"),
    "chevron": ("CVX", "NYSE"),
    "cvx": ("CVX", "NYSE"),
    
    # Consumer
    "walmart": ("WMT", "NYSE"),
    "wmt": ("WMT", "NYSE"),
    "coca-cola": ("KO", "NYSE"),
    "coke": ("KO", "NYSE"),
    "ko": ("KO", "NYSE"),
    "mcdonald": ("MCD", "NYSE"),
    "mcdonalds": ("MCD", "NYSE"),
    "mcd": ("MCD", "NYSE"),
    "disney": ("DIS", "NYSE"),
    "dis": ("DIS", "NYSE"),
    "nike": ("NKE", "NYSE"),
    "nke": ("NKE", "NYSE"),
    
    # Pharma
    "pfizer": ("PFE", "NYSE"),
    "pfe": ("PFE", "NYSE"),
    "moderna": ("MRNA", "NASDAQ"),
    "mrna": ("MRNA", "NASDAQ"),
    "johnson & johnson": ("JNJ", "NYSE"),
    "jnj": ("JNJ", "NYSE"),
    
    # Airlines
    "boeing": ("BA", "NYSE"),
    "ba": ("BA", "NYSE"),
    "delta": ("DAL", "NYSE"),
    "delta airlines": ("DAL", "NYSE"),
    "dal": ("DAL", "NYSE"),
    "american airlines": ("AAL", "NASDAQ"),
    "aal": ("AAL", "NASDAQ"),
    
    # Semiconductors
    "tsmc": ("TSM", "NYSE"),
    "taiwan semiconductor": ("TSM", "NYSE"),
    "tsm": ("TSM", "NYSE"),
    "broadcom": ("AVGO", "NASDAQ"),
    "avgo": ("AVGO", "NASDAQ"),
    "qualcomm": ("QCOM", "NASDAQ"),
    "qcom": ("QCOM", "NASDAQ"),
    "asml": ("ASML", "NASDAQ"),
    "micron": ("MU", "NASDAQ"),
    "mu": ("MU", "NASDAQ"),
}


async def fetch_coingecko_coins() -> List[dict]:
    """
    Fetch top 250 coins from CoinGecko API for dynamic matching.
    Returns list of coin data with id, symbol, name.
    """
    global _coin_cache, _coin_cache_time
    
    # Check cache
    if _coin_cache_time and (datetime.now() - _coin_cache_time) < timedelta(minutes=CACHE_TTL_MINUTES):
        return list(_coin_cache.values())
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 250,
                    "page": 1,
                    "sparkline": False
                }
            )
            
            if response.status_code == 200:
                coins = response.json()
                # Build cache with symbol as key
                _coin_cache = {
                    coin["symbol"].upper(): {
                        "id": coin["id"],
                        "symbol": coin["symbol"].upper(),
                        "name": coin["name"].lower(),
                    }
                    for coin in coins
                }
                _coin_cache_time = datetime.now()
                return list(_coin_cache.values())
    except Exception as e:
        print(f"CoinGecko fetch error: {e}")
    
    # Return cached data if fetch fails
    return list(_coin_cache.values()) if _coin_cache else []


def find_pattern_matches(text: str) -> List[Tuple[str, str]]:
    """
    Find symbol patterns in text like $BTC, #ETH, @TSLA
    Returns list of (symbol, match_type) tuples
    """
    matches = []
    
    # Pattern: $BTC, $ETH, $TSLA (crypto or stock)
    dollar_pattern = re.findall(r'\$([A-Za-z]{2,10})', text)
    for match in dollar_pattern:
        matches.append((match.upper(), "dollar_sign"))
    
    # Pattern: #BTC, #ETH (social media style)
    hashtag_pattern = re.findall(r'#([A-Za-z]{2,10})', text)
    for match in hashtag_pattern:
        matches.append((match.upper(), "hashtag"))
    
    # Pattern: (BTC), (ETH) - ticker in parentheses
    paren_pattern = re.findall(r'\(([A-Z]{2,5})\)', text)
    for match in paren_pattern:
        matches.append((match, "parentheses"))
    
    # Pattern: BTC/USD, ETH/USDT - trading pairs
    pair_pattern = re.findall(r'([A-Z]{2,5})/(USD[TC]?|BTC|ETH)', text.upper())
    for match in pair_pattern:
        matches.append((match[0], "trading_pair"))
    
    # Pattern: Turkish price mentions "95.000$", "95,000$" followed/preceded by coin name
    # This helps identify the main subject of price news
    
    return matches


def calculate_match_score(
    text_lower: str,
    title_lower: str,
    match_term: str,
    match_type: str,
    is_title: bool = False
) -> float:
    """
    Calculate confidence score for a symbol match.
    Higher score = more likely to be the correct symbol.
    """
    base_score = 0.0
    match_term_lower = match_term.lower()
    
    # Match type weights
    type_weights = {
        "dollar_sign": 3.0,    # $BTC is very explicit
        "hashtag": 2.5,        # #ETH is quite explicit
        "parentheses": 2.5,    # (BTC) is explicit
        "trading_pair": 3.0,   # BTC/USD is very explicit
        "name": 2.0,           # Full name match
        "ticker": 1.5,         # Short ticker match
        "alias": 1.5,          # Alias match
    }
    
    base_score = type_weights.get(match_type, 1.0)
    
    # Title match bonus (3x weight)
    if is_title:
        base_score *= 3.0
    
    # Position bonus - earlier in text = more relevant
    pos = text_lower.find(match_term_lower)
    if pos != -1 and pos < 50:
        base_score *= 1.5
    
    # Context bonuses
    context_keywords = [
        "price", "fiyat", "usd", "dollar", "dolar", "$",
        "rally", "surge", "crash", "drop", "yüksel", "düş",
        "market", "piyasa", "trading", "trade", "işlem",
        "buy", "sell", "al", "sat", "bullish", "bearish"
    ]
    
    for keyword in context_keywords:
        if keyword in text_lower:
            base_score *= 1.1
            break
    
    return base_score


async def detect_symbol_smart(
    text: str,
    title: str = "",
    asset_type: str = "crypto"
) -> Optional[str]:
    """
    Smart symbol detection using multiple strategies:
    1. Explicit patterns ($BTC, #ETH)
    2. CoinGecko coin list matching
    3. Alias/name matching
    4. Score-based selection of best match
    
    Returns TradingView symbol format: EXCHANGE:SYMBOL
    """
    text_lower = text.lower()
    title_lower = title.lower()
    combined_lower = title_lower + " " + text_lower
    
    matches: List[SymbolMatch] = []
    
    # Strategy 1: Find explicit patterns
    pattern_matches = find_pattern_matches(title + " " + text)
    for symbol, match_type in pattern_matches:
        # Check if it's a known crypto
        if symbol in CRYPTO_ALIASES.values() or symbol.lower() in CRYPTO_ALIASES:
            final_symbol = CRYPTO_ALIASES.get(symbol.lower(), symbol)
            score = calculate_match_score(combined_lower, title_lower, symbol, match_type, symbol.lower() in title_lower)
            
            # Determine exchange
            if final_symbol == "PI":
                exchange = "OKX"
                pair = "PIUSDT"
            else:
                exchange = "BINANCE"
                pair = f"{final_symbol}USDT"
            
            matches.append(SymbolMatch(
                symbol=f"{exchange}:{pair}",
                score=score,
                match_type=match_type
            ))
        
        # Check if it's a known stock
        stock_key = symbol.lower()
        if stock_key in STOCK_MAPPINGS:
            ticker, exchange = STOCK_MAPPINGS[stock_key]
            score = calculate_match_score(combined_lower, title_lower, symbol, match_type, symbol.lower() in title_lower)
            matches.append(SymbolMatch(
                symbol=f"{exchange}:{ticker}",
                score=score,
                match_type=match_type
            ))
    
    # Strategy 2: Match against CoinGecko coin list (for crypto)
    if asset_type == "crypto":
        coins = await fetch_coingecko_coins()
        for coin in coins:
            # Check full name
            if coin["name"] in combined_lower:
                score = calculate_match_score(combined_lower, title_lower, coin["name"], "name", coin["name"] in title_lower)
                
                symbol = coin["symbol"]
                if symbol == "PI":
                    exchange = "OKX"
                    pair = "PIUSDT"
                else:
                    exchange = "BINANCE"
                    pair = f"{symbol}USDT"
                
                matches.append(SymbolMatch(
                    symbol=f"{exchange}:{pair}",
                    score=score,
                    match_type="name"
                ))
            
            # Check symbol (with word boundary)
            symbol_pattern = r'\b' + re.escape(coin["symbol"].lower()) + r'\b'
            if re.search(symbol_pattern, combined_lower):
                score = calculate_match_score(combined_lower, title_lower, coin["symbol"], "ticker", coin["symbol"].lower() in title_lower)
                
                symbol = coin["symbol"]
                if symbol == "PI":
                    exchange = "OKX"
                    pair = "PIUSDT"
                else:
                    exchange = "BINANCE"
                    pair = f"{symbol}USDT"
                
                matches.append(SymbolMatch(
                    symbol=f"{exchange}:{pair}",
                    score=score * 0.8,  # Slightly lower for ticker-only match
                    match_type="ticker"
                ))
    
    # Strategy 3: Check aliases
    for alias, symbol in CRYPTO_ALIASES.items():
        if len(alias) >= 3:  # Skip very short aliases
            if alias in combined_lower:
                score = calculate_match_score(combined_lower, title_lower, alias, "alias", alias in title_lower)
                
                if symbol == "PI":
                    exchange = "OKX"
                    pair = "PIUSDT"
                else:
                    exchange = "BINANCE"
                    pair = f"{symbol}USDT"
                
                matches.append(SymbolMatch(
                    symbol=f"{exchange}:{pair}",
                    score=score,
                    match_type="alias"
                ))
    
    # Strategy 4: Check stock mappings
    if asset_type == "stock":
        for name, (ticker, exchange) in STOCK_MAPPINGS.items():
            if len(name) >= 3 and name in combined_lower:
                score = calculate_match_score(combined_lower, title_lower, name, "name", name in title_lower)
                matches.append(SymbolMatch(
                    symbol=f"{exchange}:{ticker}",
                    score=score,
                    match_type="name"
                ))
    
    # Select best match by score
    if matches:
        # Sort by score descending
        matches.sort(key=lambda m: m.score, reverse=True)
        best_match = matches[0]
        
        # Debug logging (can be removed in production)
        if best_match.score >= 2.0:
            print(f"[SymbolDetection] Best match: {best_match.symbol} (score: {best_match.score:.2f}, type: {best_match.match_type})")
        
        return best_match.symbol
    
    # Fallback defaults
    if asset_type == "crypto":
        return "BINANCE:BTCUSDT"
    else:
        return "AMEX:SPY"
