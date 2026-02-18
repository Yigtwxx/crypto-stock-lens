"""
Watchlist Service
Handles CRUD operations for user watchlists and fetches real-time prices 
for both Crypto (CoinGecko) and Stocks (Yahoo Finance).
"""
import json
import os
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from services.stock_market_service import fetch_single_stock
from services.market_overview_service import _fetch_coin_metadata

DATA_FILE = "data/watchlist.json"

FALLBACK_LOGOS = {
    "BTC": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png",
    "ETH": "https://assets.coingecko.com/coins/images/279/large/ethereum.png",
    "SOL": "https://assets.coingecko.com/coins/images/4128/large/solana.png",
    "BNB": "https://assets.coingecko.com/coins/images/825/large/binance-coin-logo.png",
    "XRP": "https://assets.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png",
    "DOGE": "https://assets.coingecko.com/coins/images/5/large/dogecoin.png",
    "ADA": "https://assets.coingecko.com/coins/images/975/large/cardano.png",
    "AVAX": "https://assets.coingecko.com/coins/images/12559/large/avalance-1.png",
    "AAPL": "https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg",
    "MSFT": "https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg",
    "GOOGL": "https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg",
    "NVDA": "https://upload.wikimedia.org/wikipedia/commons/2/21/Nvidia_logo.svg",
    "TSLA": "https://upload.wikimedia.org/wikipedia/commons/e/e8/Tesla_logo.png",
    "AMZN": "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg",
    "META": "https://upload.wikimedia.org/wikipedia/commons/7/7b/Meta_Platforms_Inc._logo.svg"
}

# In-memory cache for simple persistence
def _load_db():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def _save_db(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

async def get_watchlists():
    """
    Get all watchlists with current market data.
    """
    watchlists = _load_db()
    if not watchlists:
        return []

    # Collect all symbols to fetch
    stock_symbols = set()
    crypto_ids = set() # We might store crypto as ID or Symbol. Let's assume Symbol for simplicity, but ID is better.
                       # For this MVP, we will try to detect type or store type in the watchlist item.
    
    # We'll assume the structure is:
    # { "id": "uuid", "name": "Tech", "items": [ {"symbol": "AAPL", "type": "STOCK"}, {"symbol": "BTC", "type": "CRYPTO"} ] }
    
    return await _hydrate_prices(watchlists)

async def create_watchlist(name: str, items: List[Dict[str, str]]):
    """
    Create a new watchlist.
    items: List of {"symbol": "BTC", "type": "CRYPTO"}
    """
    db = _load_db()
    new_list = {
        "id": str(len(db) + 1), # Simple ID generation
        "name": name,
        "items": items
    }
    db.append(new_list)
    _save_db(db)
    return await _hydrate_prices([new_list])

async def delete_watchlist(list_id: str):
    db = _load_db()
    new_db = [w for w in db if w["id"] != list_id]
    _save_db(new_db)
    return {"status": "success"}

# -----------------------------------------------------------------------------
# Smart Crypto Resolver
# -----------------------------------------------------------------------------

SYMBOL_MAP_FILE = "data/crypto_symbol_map.json"

class CryptoSymbolResolver:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CryptoSymbolResolver, cls).__new__(cls)
            cls._instance.cache = cls._instance._load_cache()
            # Hardcoded common overrides to ensure top coins are always correct immediately
            cls._instance.overrides = {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana",
                "BNB": "binancecoin",
                "XRP": "ripple",
                "DOGE": "dogecoin",
                "ADA": "cardano",
                "AVAX": "avalanche-2",
                "TRX": "tron",
                "DOT": "polkadot",
                "LINK": "chainlink",
                "MATIC": "matic-network",
                "SHIB": "shiba-inu",
                "LTC": "litecoin",
                "BCH": "bitcoin-cash",
                "ATOM": "cosmos",
                "UNI": "uniswap",
                "XLM": "stellar",
                "OKB": "okb",
                "ETC": "ethereum-classic",
                "FIL": "filecoin",
                "HBAR": "hedera-hashgraph",
                "LDO": "lido-dao",
                "APT": "aptos",
                "ARB": "arbitrum",
                "NEAR": "near",
                "VET": "vechain",
                "QNT": "quant-network",
                "MKR": "maker",
                "GRT": "the-graph",
                "AAVE": "aave",
                "ALGO": "algorand",
                "AXS": "axie-infinity",
                "SAND": "the-sandbox",
                "EOS": "eos",
                "MANA": "decentraland",
                "THETA": "theta-token",
                "EGLD": "elrond-erd-2",
                "FLOW": "flow",
                "XTZ": "tezos",
                "PEPE": "pepe" # Specifically ensure real PEPE
            }
        return cls._instance

    def _load_cache(self):
        if not os.path.exists(SYMBOL_MAP_FILE):
            return {}
        try:
            with open(SYMBOL_MAP_FILE, "r") as f:
                return json.load(f)
        except:
            return {}

    def _save_cache(self):
        os.makedirs(os.path.dirname(SYMBOL_MAP_FILE), exist_ok=True)
        with open(SYMBOL_MAP_FILE, "w") as f:
            json.dump(self.cache, f, indent=2)

    async def resolve(self, symbol: str, client: httpx.AsyncClient) -> Optional[str]:
        symbol = symbol.upper()
        
        # 1. Check Overrides
        if symbol in self.overrides:
            return self.overrides[symbol]
            
        # 2. Check Cache
        if symbol in self.cache:
            return self.cache[symbol]
            
        # 3. Fetch from API (Search)
        try:
            # print(f"Resolving symbol from API: {symbol}")
            response = await client.get(
                "https://api.coingecko.com/api/v3/search",
                params={"query": symbol},
                headers={"User-Agent": "Oracle-X/1.0"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                coins = data.get("coins", [])
                
                if coins:
                    # Find best match. 
                    # The API returns them sorted by market cap rank usually, but let's be safe.
                    # We look for exact symbol match first among the results.
                    
                    best_match = None
                    
                    # First pass: Exact symbol match
                    for coin in coins:
                        if coin["symbol"].upper() == symbol:
                            best_match = coin
                            break
                    
                    # Second pass: If no exact symbol match, take the first result (highest rank)
                    if not best_match and coins:
                        best_match = coins[0]
                        
                    if best_match:
                        coin_id = best_match["id"]
                        self.cache[symbol] = coin_id
                        self._save_cache()
                        return coin_id
                        
        except Exception as e:
            print(f"Error resolving symbol {symbol}: {e}")
            
        return None


# Simple robust cache for crypto prices to prevent 429s
_crypto_price_cache = {
    "data": {},
    "timestamp": 0
}
CACHE_DURATION = 60  # seconds

async def _hydrate_prices(watchlists):
    """
    Fetch current prices for all items in the watchlists.
    """
    # 1. Identify all unique assets
    unique_stocks = set()
    unique_cryptos = set()
    
    for w in watchlists:
        for item in w.get("items", []):
            if item["type"] == "STOCK":
                unique_stocks.add(item["symbol"])
            elif item["type"] == "CRYPTO":
                unique_cryptos.add(item["symbol"].upper())

    # 2. Fetch Data
    stock_data = {}
    crypto_data = {}
    
    resolver = CryptoSymbolResolver()
    
    async with httpx.AsyncClient() as client:
        # Stocks (Concurrent)
        tasks = [fetch_single_stock(client, sym) for sym in unique_stocks]
        stock_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res in stock_results:
            if isinstance(res, dict):
                stock_data[res["symbol"]] = res
        
        # Crypto with Caching
        if unique_cryptos:
            import time
            current_time = time.time()
            
            # Check cache validity
            # We use a simple global cache. If valid, use it.
            # If we need symbols not in cache, we might need to fetch, but for now
            # let's just refresh the whole cache if it's old.
            
            use_cache = False
            if _crypto_price_cache["timestamp"] > current_time - CACHE_DURATION:
                use_cache = True
                # Check if we have data for all requested symbols involved (roughly)
                # Actually, we cache by Symbol -> Data.
                # If we have data for all unique_cryptos, return.
                # If missing some, maybe fetch? 
                # For simplicity and to avoid 429s, we serve what we have if cache is fresh-ish.
                pass
            
            if use_cache:
                crypto_data = _crypto_price_cache["data"]
            else:
                try:
                    # Resolve IDs first
                    ids_to_fetch = set()
                    symbol_id_map = {} # SYMBOL -> ID
                    
                    for sym in unique_cryptos:
                        c_id = await resolver.resolve(sym, client)
                        if c_id:
                            ids_to_fetch.add(c_id)
                            symbol_id_map[sym] = c_id

                    if ids_to_fetch:
                        response = await client.get(
                            "https://api.coingecko.com/api/v3/coins/markets",
                            params={
                                "vs_currency": "usd",
                                "ids": ",".join(ids_to_fetch), 
                                "per_page": 250,
                                "sparkline": "false",
                                "order": "market_cap_desc"
                            },
                            headers={
                                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                                "Accept": "application/json"
                            },
                            # Slightly longer timeout
                            timeout=20
                        )
                        
                        if response.status_code == 200:
                            coins = response.json()
                            id_coin_map = {c["id"]: c for c in coins}
                            
                            new_crypto_data = {}
                            for sym, c_id in symbol_id_map.items():
                                if c_id in id_coin_map:
                                    coin = id_coin_map[c_id]
                                    new_crypto_data[sym] = {
                                        "price": coin.get("current_price", 0) or 0,
                                        "change_24h": coin.get("price_change_percentage_24h", 0) or 0,
                                        "market_cap": coin.get("market_cap", 0) or 0,
                                        "logo": coin.get("image", ""),
                                        "name": coin.get("name", sym)
                                    }
                            
                            # Update Cache
                            _crypto_price_cache["data"] = new_crypto_data
                            _crypto_price_cache["timestamp"] = current_time
                            crypto_data = new_crypto_data
                        elif response.status_code == 429:
                            print(f"Watchlist crypto fetch rate limited (429). Using cache/fallback.")
                            # Use old cache if exists
                            crypto_data = _crypto_price_cache["data"]
                        else:
                            print(f"Watchlist crypto fetch failed with status: {response.status_code}")
                            crypto_data = _crypto_price_cache["data"]
                            
                except Exception as e:
                    print(f"Watchlist crypto fetch error: {e}")
                    # Fallback to cache on error
                    crypto_data = _crypto_price_cache["data"]

    # 3. Merge Data back
    hydrated_lists = []
    for w in watchlists:
        hydrated_items = []
        for item in w.get("items", []):
            sym = item["symbol"]
            obj = {
                "symbol": sym,
                "type": item["type"],
                "price": 0,
                "change_24h": 0,
                "logo": "",
                "name": sym
            }
            
            if item["type"] == "STOCK":
                if sym in stock_data:
                    d = stock_data[sym]
                    obj.update({
                        "price": d["price"],
                        "change_24h": d["change_24h"],
                        "logo": d.get("logo", ""),
                        "name": d.get("name", sym)
                    })
                if not obj["logo"] and sym in FALLBACK_LOGOS:
                    obj["logo"] = FALLBACK_LOGOS[sym]
            
            elif item["type"] == "CRYPTO":
                c_sym = sym.upper()
                # Check current fetch OR cache
                if c_sym in crypto_data:
                    d = crypto_data[c_sym]
                    obj.update({
                        "price": d["price"],
                        "change_24h": d["change_24h"],
                        "logo": d["logo"],
                        "name": d["name"]
                    })
                elif c_sym in _crypto_price_cache["data"]:
                     # Fallback to cache if current fetch missed it
                    d = _crypto_price_cache["data"][c_sym]
                    obj.update({
                        "price": d["price"],
                        "change_24h": d["change_24h"],
                        "logo": d["logo"],
                        "name": d["name"]
                    })
                
                if not obj["logo"] and c_sym in FALLBACK_LOGOS:
                    obj["logo"] = FALLBACK_LOGOS[c_sym]
            
            hydrated_items.append(obj)
        
        hydrated_lists.append({
            "id": w["id"],
            "name": w["name"],
            "items": hydrated_items
        })
        
    return hydrated_lists
