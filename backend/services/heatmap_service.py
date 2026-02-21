"""
Heatmap Data Service - Provides multi-metric data for advanced heatmaps
Metrics: Price Change, Volume, Social Hype, Developer Activity
"""
import httpx
from typing import Dict, List, Any
from datetime import datetime
import asyncio

# CoinGecko API (Free tier)
COINGECKO_API = "https://api.coingecko.com/api/v3"

# Top cryptocurrencies to track
TOP_CRYPTOS = [
    "bitcoin", "ethereum", "binancecoin", "solana", "xrp", 
    "cardano", "dogecoin", "avalanche-2", "polkadot", "chainlink",
    "polygon", "litecoin", "uniswap", "near", "stellar",
    "cosmos", "aptos", "arbitrum", "optimism", "filecoin",
    "injective", "sui", "render-token", "the-graph", "aave"
]

# Sector mappings
SECTOR_MAP = {
    "bitcoin": "Store of Value",
    "ethereum": "Smart Contracts",
    "binancecoin": "Exchange",
    "solana": "Smart Contracts",
    "xrp": "Payments",
    "cardano": "Smart Contracts",
    "dogecoin": "Meme",
    "avalanche-2": "Smart Contracts",
    "polkadot": "Interoperability",
    "chainlink": "Oracle",
    "polygon": "Layer 2",
    "litecoin": "Payments",
    "uniswap": "DeFi",
    "near": "Smart Contracts",
    "stellar": "Payments",
    "cosmos": "Interoperability",
    "aptos": "Smart Contracts",
    "arbitrum": "Layer 2",
    "optimism": "Layer 2",
    "filecoin": "Storage",
    "injective": "DeFi",
    "sui": "Smart Contracts",
    "render-token": "AI/Compute",
    "the-graph": "Infrastructure",
    "aave": "DeFi"
}

# Cache
_heatmap_cache: Dict[str, Any] = {
    "data": None,
    "timestamp": None
}
CACHE_DURATION = 300  # 5 minutes


async def fetch_heatmap_data() -> Dict[str, Any]:
    """
    Fetch comprehensive heatmap data with multiple metrics.
    Returns data for: Price, Volume, Social Score, Developer Score
    """
    global _heatmap_cache
    
    # Check cache
    if _heatmap_cache["data"] and _heatmap_cache["timestamp"]:
        elapsed = (datetime.now() - _heatmap_cache["timestamp"]).total_seconds()
        if elapsed < CACHE_DURATION:
            return _heatmap_cache["data"]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch market data with social and developer info
            coins_str = ",".join(TOP_CRYPTOS)
            response = await client.get(
                f"{COINGECKO_API}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids": coins_str,
                    "order": "market_cap_desc",
                    "per_page": 50,
                    "page": 1,
                    "sparkline": False,
                    "price_change_percentage": "24h,7d"
                }
            )
            
            if response.status_code != 200:
                return _get_fallback_heatmap_data()
            
            market_data = response.json()
            
            # Fetch detailed data for each coin (social + developer)
            detailed_data = await _fetch_detailed_metrics(client, TOP_CRYPTOS[:15])
            
            # Build heatmap data
            coins = []
            for coin in market_data:
                coin_id = coin.get("id", "")
                symbol = coin.get("symbol", "").upper()
                
                # Get detailed metrics if available
                details = detailed_data.get(coin_id, {})
                
                # Calculate normalized scores (0-100)
                price_change = coin.get("price_change_percentage_24h", 0) or 0
                volume = coin.get("total_volume", 0) or 0
                market_cap = coin.get("market_cap", 0) or 0
                
                # Social score from community data
                social_score = details.get("social_score", 50)
                
                # Developer score from developer data
                dev_score = details.get("developer_score", 50)
                
                coins.append({
                    "id": coin_id,
                    "symbol": symbol,
                    "name": coin.get("name", symbol),
                    "sector": SECTOR_MAP.get(coin_id, "Other"),
                    "image": coin.get("image", ""),
                    "price": coin.get("current_price", 0),
                    "market_cap": market_cap,
                    "volume_24h": volume,
                    "price_change_24h": price_change,
                    "price_change_7d": coin.get("price_change_percentage_7d_in_currency", 0) or 0,
                    "social_score": social_score,
                    "developer_score": dev_score,
                    # Normalized values for heatmap coloring (0-100 scale)
                    "volume_score": min(100, (volume / 1e9) * 10) if volume else 0,
                })
            
            # Sort by market cap
            coins.sort(key=lambda x: x.get("market_cap", 0), reverse=True)
            
            # Group by sector
            sectors = {}
            for coin in coins:
                sector = coin["sector"]
                if sector not in sectors:
                    sectors[sector] = []
                sectors[sector].append(coin)
            
            result = {
                "coins": coins,
                "sectors": sectors,
                "timestamp": datetime.now().isoformat(),
                "metrics": ["price_change_24h", "volume_score", "social_score", "developer_score"]
            }
            
            # Update cache
            _heatmap_cache["data"] = result
            _heatmap_cache["timestamp"] = datetime.now()
            
            return result
            
    except Exception as e:
        print(f"Error fetching heatmap data: {e}")
        return _get_fallback_heatmap_data()


async def _fetch_detailed_metrics(client: httpx.AsyncClient, coin_ids: List[str]) -> Dict[str, Dict]:
    """
    Fetch detailed social and developer metrics for coins.
    """
    detailed = {}
    
    # Limit concurrent requests
    for coin_id in coin_ids[:10]:
        try:
            response = await client.get(
                f"{COINGECKO_API}/coins/{coin_id}",
                params={
                    "localization": False,
                    "tickers": False,
                    "market_data": False,
                    "community_data": True,
                    "developer_data": True,
                    "sparkline": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Calculate social score from community data
                community = data.get("community_data", {})
                twitter_followers = community.get("twitter_followers", 0) or 0
                reddit_subscribers = community.get("reddit_subscribers", 0) or 0
                telegram_users = community.get("telegram_channel_user_count", 0) or 0
                
                # Normalize social score (based on typical ranges)
                social_score = min(100, (
                    (twitter_followers / 10_000_000) * 40 +
                    (reddit_subscribers / 5_000_000) * 30 +
                    (telegram_users / 1_000_000) * 30
                ) * 100)
                
                # Calculate developer score
                developer = data.get("developer_data", {})
                commits_4w = developer.get("commit_count_4_weeks", 0) or 0
                stars = developer.get("stars", 0) or 0
                forks = developer.get("forks", 0) or 0
                
                dev_score = min(100, (
                    (commits_4w / 500) * 50 +
                    (stars / 50_000) * 30 +
                    (forks / 10_000) * 20
                ) * 100)
                
                detailed[coin_id] = {
                    "social_score": round(social_score, 1),
                    "developer_score": round(dev_score, 1),
                    "twitter_followers": twitter_followers,
                    "reddit_subscribers": reddit_subscribers,
                    "github_commits": commits_4w,
                    "github_stars": stars
                }
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
            
        except Exception as e:
            print(f"Error fetching details for {coin_id}: {e}")
            detailed[coin_id] = {"social_score": 50, "developer_score": 50}
    
    return detailed


def _get_fallback_heatmap_data() -> Dict[str, Any]:
    """
    Return empty data when API fails and no cache is available.
    """
    return {
        "coins": [],
        "sectors": {},
        "timestamp": datetime.now().isoformat(),
        "metrics": ["price_change_24h", "volume_score", "social_score", "developer_score"]
    }

