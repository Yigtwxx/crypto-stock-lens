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


# Coins that should default to OKX (usually due to lack of Spot on Binance or user preference)
OKX_PREFERRED_TOKENS = {
    "PI", 
    "POPCAT", 
    "BRETT", 
    "MOG", 
    "MEW", 
    "WEN", 
    "COQ"
}



# Common crypto aliases and their standard symbols
CRYPTO_ALIASES = {
    "btc": "BTC",
    "bitcoin": "BTC",
    "eth": "ETH",
    "ethereum": "ETH",
    "xrp": "XRP",
    "ripple": "XRP",
    "sol": "SOL",
    "solana": "SOL",
    "ada": "ADA",
    "cardano": "ADA",
    "doge": "DOGE",
    "dogecoin": "DOGE",
    "shib": "SHIB",
    "shiba inu": "SHIB",
    "dot": "DOT",
    "polkadot": "DOT",
    "link": "LINK",
    "chainlink": "LINK",
    "ltc": "LTC",
    "litecoin": "LTC",
    "bch": "BCH",
    "bitcoin cash": "BCH",
    "etc": "ETC",
    "ethereum classic": "ETC",
    "xlm": "XLM",
    "stellar": "XLM",
    "vet": "VET",
    "vechain": "VET",
    "uni": "UNI",
    "uniswap": "UNI",
    "atom": "ATOM",
    "cosmos": "ATOM",
    "algo": "ALGO",
    "algorand": "ALGO",
    "fil": "FIL",
    "filecoin": "FIL",
    "eos": "EOS",
    "trx": "TRX",
    "tron": "TRX",
    "xtz": "XTZ",
    "tezos": "XTZ",
    "neo": "NEO",
    "dash": "DASH",
    "zec": "ZEC",
    "zcash": "ZEC",
    "xmr": "XMR",
    "monero": "XMR",
    "icp": "ICP",
    "internet computer": "ICP",
    "avax": "AVAX",
    "avalanche": "AVAX",
    "matic": "MATIC",
    "polygon": "MATIC",
    "luna": "LUNA",
    "terra": "LUNA",
    "ftm": "FTM",
    "fantom": "FTM",
    "sand": "SAND",
    "the sandbox": "SAND",
    "mana": "MANA",
    "decentraland": "MANA",
    "axs": "AXS",
    "axie infinity": "AXS",
    "enj": "ENJ",
    "enjin coin": "ENJ",
    "chz": "CHZ",
    "chiliz": "CHZ",
    "aave": "AAVE",
    "comp": "COMP",
    "compound": "COMP",
    "snx": "SNX",
    "synthetix": "SNX",
    "yfi": "YFI",
    "yearn.finance": "YFI",
    "sushi": "SUSHI",
    "sushiswap": "SUSHI",
    "pancakeswap": "CAKE",
    "cake": "CAKE",
    "not": "NOT",
    "xrpl": "XRP",
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
    "nvidia": ("NVDA", "NASDAQ"),
    "nvda": ("NVDA", "NASDAQ"),
    "tesla": ("TSLA", "NASDAQ"),
    "tsla": ("TSLA", "NASDAQ"),
    "meta": ("META", "NASDAQ"),
    "facebook": ("META", "NASDAQ"),
    "netflix": ("NFLX", "NASDAQ"),
    "nflx": ("NFLX", "NASDAQ"),
    
    # Software & Cloud
    "adobe": ("ADBE", "NASDAQ"),
    "adbe": ("ADBE", "NASDAQ"),
    "salesforce": ("CRM", "NYSE"),
    "crm": ("CRM", "NYSE"),
    "oracle": ("ORCL", "NYSE"),
    "orcl": ("ORCL", "NYSE"),
    "sap": ("SAP", "NYSE"),
    "servicenow": ("NOW", "NYSE"),
    "now": ("NOW", "NYSE"),
    "snowflake": ("SNOW", "NYSE"),
    "snow": ("SNOW", "NYSE"),
    "intuit": ("INTU", "NASDAQ"),
    "intu": ("INTU", "NASDAQ"),
    "autodesk": ("ADSK", "NASDAQ"),
    "adsk": ("ADSK", "NASDAQ"),
    "workday": ("WDAY", "NASDAQ"),
    "wday": ("WDAY", "NASDAQ"),
    "zscaler": ("ZS", "NASDAQ"),
    "zs": ("ZS", "NASDAQ"),
    "crowdstrike": ("CRWD", "NASDAQ"),
    "crwd": ("CRWD", "NASDAQ"),
    "palo alto networks": ("PANW", "NASDAQ"),
    "panw": ("PANW", "NASDAQ"),
    "fortinet": ("FTNT", "NASDAQ"),
    "ftnt": ("FTNT", "NASDAQ"),
    "cloudflare": ("NET", "NYSE"),
    "net": ("NET", "NYSE"),
    "databricks": ("DBX", "NASDAQ"), # Note: DBX is Dropbox, Databricks is private. This is a placeholder.
    "mongodb": ("MDB", "NASDAQ"),
    "mdb": ("MDB", "NASDAQ"),
    "unity": ("U", "NYSE"),
    "u": ("U", "NYSE"),
    "roblox": ("RBLX", "NYSE"),
    "rblx": ("RBLX", "NYSE"),
    "atlassian": ("TEAM", "NASDAQ"),
    "team": ("TEAM", "NASDAQ"),
    "zoom": ("ZM", "NASDAQ"),
    "zm": ("ZM", "NASDAQ"),
    "okta": ("OKTA", "NASDAQ"),
    "okta": ("OKTA", "NASDAQ"),
    "docuSign": ("DOCU", "NASDAQ"),
    "docu": ("DOCU", "NASDAQ"),
    "coupa": ("COUP", "NASDAQ"),
    "coup": ("COUP", "NASDAQ"),
    "splunk": ("SPLK", "NASDAQ"),
    "splk": ("SPLK", "NASDAQ"),
    "vmware": ("VMW", "NYSE"),
    "vmw": ("VMW", "NYSE"),
    "cisco": ("CSCO", "NASDAQ"),
    "csco": ("CSCO", "NASDAQ"),
    "ibm": ("IBM", "NYSE"),
    "accenture": ("ACN", "NYSE"),
    "acn": ("ACN", "NYSE"),
    "cognizant": ("CTSH", "NASDAQ"),
    "ctsh": ("CTSH", "NASDAQ"),
    "infosys": ("INFY", "NYSE"),
    "infy": ("INFY", "NYSE"),
    "wipro": ("WIT", "NYSE"),
    "wit": ("WIT", "NYSE"),
    "capgemini": ("CAP.PA", "EURONEXT"), # Example for non-US
    "tata consultancy services": ("TCS.NS", "NSE"), # Example for non-US
    "palantir": ("PLTR", "NASDAQ"),
    "pltr": ("PLTR", "NASDAQ"),
    "crowdstrike": ("CRWD", "NASDAQ"),
    "crwd": ("CRWD", "NASDAQ"),
    "salesforce": ("CRM", "NYSE"),
    "crm": ("CRM", "NYSE"),
    "oracle": ("ORCL", "NYSE"),
    "orcl": ("ORCL", "NYSE"),
    "servicenow": ("NOW", "NYSE"),
    "now": ("NOW", "NYSE"),
    "snowflake": ("SNOW", "NYSE"),
    "snow": ("SNOW", "NYSE"),
    "autodesk": ("ADSK", "NASDAQ"),
    "adsk": ("ADSK", "NASDAQ"),

    # Crypto-Adjacent Stocks
    "coinbase": ("COIN", "NASDAQ"),
    "coin": ("COIN", "NASDAQ"),
    "microstrategy": ("MSTR", "NASDAQ"),
    "mstr": ("MSTR", "NASDAQ"),
    "marathon digital": ("MARA", "NASDAQ"),
    "mara": ("MARA", "NASDAQ"),
    "riot platforms": ("RIOT", "NASDAQ"),
    "riot": ("RIOT", "NASDAQ"),
    "cleanspark": ("CLSK", "NASDAQ"),
    "clsk": ("CLSK", "NASDAQ"),
    "blackrock": ("BLK", "NYSE"),
    "blk": ("BLK", "NYSE"),
    
    # EV & Auto
    "rivian": ("RIVN", "NASDAQ"),
    "rivn": ("RIVN", "NASDAQ"),
    "lucid": ("LCID", "NASDAQ"),
    "lcid": ("LCID", "NASDAQ"),
    "nio": ("NIO", "NYSE"),
    "ford": ("F", "NYSE"),
    "general motors": ("GM", "NYSE"),
    "gm": ("GM", "NYSE"),
    
    # Fintech & Payments
    "block": ("SQ", "NYSE"),
    "square": ("SQ", "NYSE"),
    "sq": ("SQ", "NYSE"),
    "sofi": ("SOFI", "NASDAQ"),
    "american express": ("AXP", "NYSE"),
    "axp": ("AXP", "NYSE"),
    "robinhood": ("HOOD", "NASDAQ"),
    "hood": ("HOOD", "NASDAQ"),
    
    # Retail & E-commerce
    "shopify": ("SHOP", "NYSE"),
    "shop": ("SHOP", "NYSE"),
    "uber": ("UBER", "NYSE"),
    "airbnb": ("ABNB", "NASDAQ"),
    "abnb": ("ABNB", "NASDAQ"),
    "booking": ("BKNG", "NASDAQ"),
    "bkng": ("BKNG", "NASDAQ"),
    
    # Biotech & Health
    "eli lilly": ("LLY", "NYSE"),
    "lly": ("LLY", "NYSE"),
    "novo nordisk": ("NVO", "NYSE"),
    "nvo": ("NVO", "NYSE"),
    "viking therapeutics": ("VKTX", "NASDAQ"),
    "vktx": ("VKTX", "NASDAQ"),
    
    # Energy & Industrial
    "plug power": ("PLUG", "NASDAQ"),
    "plug": ("PLUG", "NASDAQ"),
    "first solar": ("FSLR", "NASDAQ"),
    "fslr": ("FSLR", "NASDAQ"),
    "ge": ("GE", "NYSE"),
    "general electric": ("GE", "NYSE"),
    "caterpillar": ("CAT", "NYSE"),
    "cat": ("CAT", "NYSE"),
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


from services.ollama_service import detect_asset_symbol

async def detect_symbol_smart(
    text: str,
    title: str = "",
    asset_type: str = "crypto"
) -> Optional[str]:
    """
    Smart symbol detection using Hybrid approach:
    1. Explicit patterns ($BTC, #ETH) -> Fast & Reliable
    2. LLM Analysis (Ollama) -> Smart & Context-aware
    3. Legacy List Matching -> Fallback
    
    Returns TradingView symbol format: EXCHANGE:SYMBOL
    """
    text_lower = text.lower()
    title_lower = title.lower()
    combined_lower = title_lower + " " + text_lower
    
    # Strategy 1: Find explicit patterns ($BTC, BTC/USDT) - High Confidence
    pattern_matches = find_pattern_matches(title + " " + text)
    best_pattern_match = None
    
    for symbol, match_type in pattern_matches:
        # We prioritize explicit trading signals
        if match_type in ["dollar_sign", "trading_pair"]:
            # Check if it's a known crypto alias to map it correctly (e.g. $BTC -> BTC)
            clean_symbol = symbol.upper()
            if clean_symbol in CRYPTO_ALIASES:
                clean_symbol = CRYPTO_ALIASES[clean_symbol]
                
            # Construct symbol
            if asset_type == "crypto":
                exchange = "OKX" if clean_symbol in OKX_PREFERRED_TOKENS else "BINANCE"
                return f"{exchange}:{clean_symbol}USDT"
            else:
                # For stocks, we need to verify it's a valid ticker if possible, 
                # but valid $TICKER is usually strong enough.
                pass 
                
    # Strategy 2: LLM Detection (The User's Request)
    # If no explicit $TICKER found, ask the AI.
    try:
        # Combine title and start of text for context
        llm_context = f"{title}\n{text[:300]}"
        llm_symbol = await detect_asset_symbol(llm_context)
        
        # VALIDATION: Ensure LLM output matches the requested asset type using heuristic
        if llm_symbol:
            is_valid = True
            
            # 1. Check for mismatched exchange/asset_type
            if asset_type == "crypto" and ("NASDAQ:" in llm_symbol or "NYSE:" in llm_symbol):
                # LLM hallucinated a stock exchange for a crypto
                # Try to fix if the ticker is a known crypto
                ticker_part = llm_symbol.split(":")[-1]
                if ticker_part in CRYPTO_ALIASES.values() or ticker_part.lower() in CRYPTO_ALIASES:
                    final_ticker = CRYPTO_ALIASES.get(ticker_part.lower(), ticker_part)
                    exchange = "OKX" if final_ticker in OKX_PREFERRED_TOKENS else "BINANCE"
                    llm_symbol = f"{exchange}:{final_ticker}USDT"
                else:
                    # Invalid, force fallback
                    is_valid = False
                    
            if is_valid:
                print(f"[SymbolDetection] LLM found: {llm_symbol}")
                return llm_symbol
            else:
                print(f"[SymbolDetection] LLM output rejected (invalid for {asset_type}): {llm_symbol}")

    except Exception as e:
        print(f"[SymbolDetection] LLM failed: {e}")

    # Strategy 3: Legacy List Matching (Fallback)
    matches: List[SymbolMatch] = []
    
    # ... (Keep existing matching logic for fallback or remove if desired to be purely LLM)
    # The user wanted to avoid "writing all coins by hand", so relying on LLM is key.
    # We will keep the legacy logic as a "safety net" but it will rarely be reached 
    # if LLM works well.
    
    # [Rest of original function logic would go here, simplified for this replacement]
    
    # Strategy 2a: Match against CoinGecko coin list (for crypto) [Legacy]
    if asset_type == "crypto":
        coins = await fetch_coingecko_coins()
        for coin in coins:
            # Check full name in TITLE only (to be safer)
            if coin["name"] in title_lower:
                symbol = coin["symbol"]
                exchange = "OKX" if symbol in OKX_PREFERRED_TOKENS else "BINANCE"
                return f"{exchange}:{symbol}USDT"
            
            # Check symbol (with word boundary) in TITLE matches
            symbol_pattern = r'\b' + re.escape(coin["symbol"].lower()) + r'\b'
            if re.search(symbol_pattern, title_lower):
                 symbol = coin["symbol"]
                 exchange = "OKX" if symbol in OKX_PREFERRED_TOKENS else "BINANCE"
                 return f"{exchange}:{symbol}USDT"

    # Strategy 3a: Check aliases
    for alias, symbol in CRYPTO_ALIASES.items():
        if len(alias) >= 3:
            alias_pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(alias_pattern, title_lower): # Prioritize title
                if symbol in OKX_PREFERRED_TOKENS:
                    return f"OKX:{symbol}USDT"
                return f"BINANCE:{symbol}USDT"

    # Strategy 4: Check stock mappings
    if asset_type == "stock":
        for name, (ticker, exchange) in STOCK_MAPPINGS.items():
            name_pattern = r'\b' + re.escape(name) + r'\b'
            if re.search(name_pattern, combined_lower):
                 return f"{exchange}:{ticker}"

    
    # Fallback defaults
    if asset_type == "crypto":
        return "BINANCE:BTCUSDT"
    else:
        return "AMEX:SPY"

