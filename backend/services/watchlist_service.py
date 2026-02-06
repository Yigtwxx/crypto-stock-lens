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

# In-memory cache for simple persistence
def _load_db():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
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
    
    async with httpx.AsyncClient() as client:
        # Stocks (Concurrent)
        tasks = [fetch_single_stock(client, sym) for sym in unique_stocks]
        stock_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res in stock_results:
            if isinstance(res, dict):
                stock_data[res["symbol"]] = res
        
        # Crypto (CoinGecko supports batch, but we need IDs. Resolving symbols to IDs is tricky efficiently without a map.
        # For MVP, we will assume standard symbols work with a "symbol map" or just fetch markets and filter.)
        # Reuse market overview logic: fetch top 250 and map.
        if unique_cryptos:
            try:
                # Fetching broad market to match symbols
                response = await client.get(
                    "https://api.coingecko.com/api/v3/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "ids": "", # Empty returns top 100
                        "per_page": 250, 
                        "sparkline": False
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    coins = response.json()
                    for coin in coins:
                        sym = coin["symbol"].upper()
                        if sym in unique_cryptos:
                            crypto_data[sym] = {
                                "price": coin["current_price"],
                                "change_24h": coin["price_change_percentage_24h"],
                                "market_cap": coin["market_cap"],
                                "logo": coin["image"],
                                "name": coin["name"]
                            }
            except Exception as e:
                print(f"Watchlist crypto fetch error: {e}")

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
            
            if item["type"] == "STOCK" and sym in stock_data:
                d = stock_data[sym]
                obj.update({
                    "price": d["price"],
                    "change_24h": d["change_24h"],
                    "logo": d["logo"],
                    "name": d["name"]
                })
            elif item["type"] == "CRYPTO":
                # Handle crypto format
                # Ensure symbol match (CoinGecko uses lowercase usually, we upper)
                c_sym = sym.upper()
                if c_sym in crypto_data:
                    d = crypto_data[c_sym]
                    obj.update({
                        "price": d["price"],
                        "change_24h": d["change_24h"],
                        "logo": d["logo"],
                        "name": d["name"]
                    })
                # If not found in top 250, maybe fetch single? (Skip for now for speed)
            
            hydrated_items.append(obj)
        
        hydrated_lists.append({
            "id": w["id"],
            "name": w["name"],
            "items": hydrated_items
        })
        
    return hydrated_lists
