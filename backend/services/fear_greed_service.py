"""Fear and Greed Index service using alternative.me API."""
import httpx
from datetime import datetime
from typing import Optional
import asyncio

# Cache for Fear & Greed data (5 minutes)
_fear_greed_cache: dict = {
    "data": None,
    "timestamp": None
}

CACHE_DURATION_SECONDS = 300  # 5 minutes


async def fetch_fear_greed_index() -> dict:
    """
    Fetch Fear & Greed Index from alternative.me API.
    Returns cached data if available and fresh.
    """
    global _fear_greed_cache
    
    # Check cache
    if _fear_greed_cache["data"] and _fear_greed_cache["timestamp"]:
        elapsed = (datetime.now() - _fear_greed_cache["timestamp"]).total_seconds()
        if elapsed < CACHE_DURATION_SECONDS:
            return _fear_greed_cache["data"]
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get current value and last 7 days for trend
            response = await client.get(
                "https://api.alternative.me/fng/",
                params={"limit": 7}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("data"):
                current = data["data"][0]
                history = data["data"][:7]
                
                result = {
                    "value": int(current["value"]),
                    "classification": current["value_classification"],
                    "timestamp": datetime.fromtimestamp(int(current["timestamp"])).isoformat(),
                    "history": [
                        {
                            "value": int(h["value"]),
                            "classification": h["value_classification"],
                            "date": datetime.fromtimestamp(int(h["timestamp"])).strftime("%Y-%m-%d")
                        }
                        for h in history
                    ]
                }
                
                # Update cache
                _fear_greed_cache["data"] = result
                _fear_greed_cache["timestamp"] = datetime.now()
                
                return result
    except Exception as e:
        print(f"Error fetching Fear & Greed Index: {e}")
    
    # Return fallback data if API fails
    return {
        "value": 50,
        "classification": "Neutral",
        "timestamp": datetime.now().isoformat(),
        "history": []
    }
