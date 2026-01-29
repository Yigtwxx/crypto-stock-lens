"""
News Service - Fetches news from multiple sources
Supports: CryptoCompare, NewsAPI, RSS feeds
"""
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
import hashlib
import feedparser

from models.schemas import NewsItem


# Symbol mappings for different news sources
CRYPTO_SYMBOLS = {
    "BTC": "BINANCE:BTCUSDT",
    "ETH": "BINANCE:ETHUSDT",
    "SOL": "BINANCE:SOLUSDT",
    "XRP": "BINANCE:XRPUSDT",
    "ADA": "BINANCE:ADAUSDT",
    "DOGE": "BINANCE:DOGEUSDT",
    "DOT": "BINANCE:DOTUSDT",
    "AVAX": "BINANCE:AVAXUSDT",
}

STOCK_SYMBOLS = {
    "AAPL": "NASDAQ:AAPL",
    "TSLA": "NASDAQ:TSLA",
    "MSFT": "NASDAQ:MSFT",
    "NVDA": "NASDAQ:NVDA",
    "GOOGL": "NASDAQ:GOOGL",
    "AMZN": "NASDAQ:AMZN",
    "META": "NASDAQ:META",
}


def detect_symbol(text: str, asset_type: str) -> Optional[str]:
    """Detect trading symbol from news text."""
    text_upper = text.upper()
    
    if asset_type == "crypto":
        for symbol, tradingview in CRYPTO_SYMBOLS.items():
            if symbol in text_upper or symbol.lower() in text.lower():
                return tradingview
        return "BINANCE:BTCUSDT"  # Default
    else:
        for symbol, tradingview in STOCK_SYMBOLS.items():
            if symbol in text_upper:
                return tradingview
        return "NASDAQ:SPY"  # Default to S&P 500


def generate_news_id(title: str, source: str) -> str:
    """Generate unique news ID from title and source."""
    data = f"{title}:{source}"
    return hashlib.md5(data.encode()).hexdigest()[:12]


async def fetch_cryptocompare_news() -> List[NewsItem]:
    """
    Fetch crypto news from CryptoCompare API (free, no API key required).
    """
    items = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
            )
            if response.status_code == 200:
                data = response.json()
                news_list = data.get("Data", [])[:15]  # Get top 15 news
                
                for news in news_list:
                    title = news.get("title", "")
                    body = news.get("body", "")
                    
                    # Detect crypto symbol from title/body
                    symbol = detect_symbol(f"{title} {body}", "crypto")
                    
                    items.append(NewsItem(
                        id=generate_news_id(title, news.get("source", "")),
                        title=title,
                        summary=body[:200] + "..." if len(body) > 200 else body,
                        source=news.get("source", "CryptoCompare"),
                        published_at=datetime.fromtimestamp(news.get("published_on", datetime.now().timestamp())),
                        symbol=symbol,
                        asset_type="crypto",
                        url=news.get("url", "")
                    ))
    except Exception as e:
        print(f"CryptoCompare fetch error: {e}")
    
    return items


async def fetch_coindesk_rss() -> List[NewsItem]:
    """
    Fetch news from CoinDesk RSS feed (free).
    """
    items = []
    try:
        feed = feedparser.parse("https://www.coindesk.com/arc/outboundfeeds/rss/")
        
        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            
            # Clean HTML from summary
            import re
            summary = re.sub(r'<[^>]+>', '', summary)
            
            symbol = detect_symbol(f"{title} {summary}", "crypto")
            
            # Parse published date
            published = entry.get("published_parsed")
            if published:
                pub_date = datetime(*published[:6])
            else:
                pub_date = datetime.now()
            
            items.append(NewsItem(
                id=generate_news_id(title, "CoinDesk"),
                title=title,
                summary=summary[:200] + "..." if len(summary) > 200 else summary,
                source="CoinDesk",
                published_at=pub_date,
                symbol=symbol,
                asset_type="crypto",
                url=entry.get("link", "")
            ))
    except Exception as e:
        print(f"CoinDesk RSS fetch error: {e}")
    
    return items


async def fetch_cointelegraph_rss() -> List[NewsItem]:
    """
    Fetch news from CoinTelegraph RSS feed (free).
    """
    items = []
    try:
        feed = feedparser.parse("https://cointelegraph.com/rss")
        
        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            
            # Clean HTML from summary
            import re
            summary = re.sub(r'<[^>]+>', '', summary)
            
            symbol = detect_symbol(f"{title} {summary}", "crypto")
            
            # Parse published date
            published = entry.get("published_parsed")
            if published:
                pub_date = datetime(*published[:6])
            else:
                pub_date = datetime.now()
            
            items.append(NewsItem(
                id=generate_news_id(title, "CoinTelegraph"),
                title=title,
                summary=summary[:200] + "..." if len(summary) > 200 else summary,
                source="CoinTelegraph",
                published_at=pub_date,
                symbol=symbol,
                asset_type="crypto",
                url=entry.get("link", "")
            ))
    except Exception as e:
        print(f"CoinTelegraph RSS fetch error: {e}")
    
    return items


async def fetch_marketwatch_rss() -> List[NewsItem]:
    """
    Fetch stock news from MarketWatch RSS (free).
    """
    items = []
    try:
        # Use the correct redirect URL
        feed = feedparser.parse("https://feeds.content.dowjones.io/public/rss/mw_topstories")
        
        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            
            # Clean HTML
            import re
            summary = re.sub(r'<[^>]+>', '', summary)
            
            symbol = detect_symbol(f"{title} {summary}", "stock")
            
            # Parse published date
            published = entry.get("published_parsed")
            if published:
                pub_date = datetime(*published[:6])
            else:
                pub_date = datetime.now()
            
            items.append(NewsItem(
                id=generate_news_id(title, "MarketWatch"),
                title=title,
                summary=summary[:200] + "..." if len(summary) > 200 else summary,
                source="MarketWatch",
                published_at=pub_date,
                symbol=symbol,
                asset_type="stock",
                url=entry.get("link", "")
            ))
    except Exception as e:
        print(f"MarketWatch RSS fetch error: {e}")
    
    return items


async def fetch_investing_rss() -> List[NewsItem]:
    """
    Fetch stock news from Investing.com RSS (free).
    """
    items = []
    try:
        feed = feedparser.parse("https://www.investing.com/rss/news.rss")
        
        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            
            # Clean HTML
            import re
            summary = re.sub(r'<[^>]+>', '', summary)
            
            symbol = detect_symbol(f"{title} {summary}", "stock")
            
            # Parse published date
            published = entry.get("published_parsed")
            if published:
                pub_date = datetime(*published[:6])
            else:
                pub_date = datetime.now()
            
            items.append(NewsItem(
                id=generate_news_id(title, "Investing.com"),
                title=title,
                summary=summary[:200] + "..." if len(summary) > 200 else summary,
                source="Investing.com",
                published_at=pub_date,
                symbol=symbol,
                asset_type="stock",
                url=entry.get("link", "")
            ))
    except Exception as e:
        print(f"Investing.com RSS fetch error: {e}")
    
    return items


async def fetch_seeking_alpha_rss() -> List[NewsItem]:
    """
    Fetch stock news from Seeking Alpha RSS (free).
    """
    items = []
    try:
        feed = feedparser.parse("https://seekingalpha.com/market_currents.xml")
        
        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            
            # Clean HTML
            import re
            summary = re.sub(r'<[^>]+>', '', summary)
            
            symbol = detect_symbol(f"{title} {summary}", "stock")
            
            # Parse published date
            published = entry.get("published_parsed")
            if published:
                pub_date = datetime(*published[:6])
            else:
                pub_date = datetime.now()
            
            items.append(NewsItem(
                id=generate_news_id(title, "Seeking Alpha"),
                title=title,
                summary=summary[:200] + "..." if len(summary) > 200 else summary,
                source="Seeking Alpha",
                published_at=pub_date,
                symbol=symbol,
                asset_type="stock",
                url=entry.get("link", "")
            ))
    except Exception as e:
        print(f"Seeking Alpha RSS fetch error: {e}")
    
    return items


async def fetch_bloomberght_rss() -> List[NewsItem]:
    """
    Fetch Turkish finance news from BloombergHT RSS (free).
    """
    items = []
    try:
        feed = feedparser.parse("https://www.bloomberght.com/rss")
        
        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            summary = entry.get("description", "")
            
            # Clean HTML and CDATA
            import re
            summary = re.sub(r'<!\[CDATA\[|\]\]>', '', summary)
            summary = re.sub(r'<[^>]+>', '', summary)
            
            # Detect if it's crypto or stock related
            crypto_keywords = ["bitcoin", "btc", "ethereum", "eth", "kripto", "coin", "altcoin"]
            is_crypto = any(kw in title.lower() or kw in summary.lower() for kw in crypto_keywords)
            asset_type = "crypto" if is_crypto else "stock"
            symbol = detect_symbol(f"{title} {summary}", asset_type)
            
            # Parse published date
            published = entry.get("published_parsed")
            if published:
                pub_date = datetime(*published[:6])
            else:
                pub_date = datetime.now()
            
            items.append(NewsItem(
                id=generate_news_id(title, "BloombergHT"),
                title=title,
                summary=summary[:200] + "..." if len(summary) > 200 else summary,
                source="BloombergHT",
                published_at=pub_date,
                symbol=symbol,
                asset_type=asset_type,
                url=entry.get("link", "")
            ))
    except Exception as e:
        print(f"BloombergHT RSS fetch error: {e}")
    
    return items


async def fetch_paraanaliz_rss() -> List[NewsItem]:
    """
    Fetch Turkish economy news from Paraanaliz RSS (free).
    """
    items = []
    try:
        feed = feedparser.parse("https://www.paraanaliz.com/feed/")
        
        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            summary = entry.get("description", "")
            
            # Clean HTML
            import re
            summary = re.sub(r'<[^>]+>', '', summary)
            
            # Detect if it's crypto or stock related
            crypto_keywords = ["bitcoin", "btc", "ethereum", "eth", "kripto", "coin"]
            is_crypto = any(kw in title.lower() or kw in summary.lower() for kw in crypto_keywords)
            asset_type = "crypto" if is_crypto else "stock"
            symbol = detect_symbol(f"{title} {summary}", asset_type)
            
            # Parse published date
            published = entry.get("published_parsed")
            if published:
                pub_date = datetime(*published[:6])
            else:
                pub_date = datetime.now()
            
            items.append(NewsItem(
                id=generate_news_id(title, "Paraanaliz"),
                title=title,
                summary=summary[:200] + "..." if len(summary) > 200 else summary,
                source="Paraanaliz",
                published_at=pub_date,
                symbol=symbol,
                asset_type=asset_type,
                url=entry.get("link", "")
            ))
    except Exception as e:
        print(f"Paraanaliz RSS fetch error: {e}")
    
    return items


async def fetch_koinbulteni_rss() -> List[NewsItem]:
    """
    Fetch Turkish crypto news from Koin Bülteni RSS (free).
    """
    items = []
    try:
        feed = feedparser.parse("https://koinbulteni.com/feed")
        
        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            summary = entry.get("description", "")
            
            # Clean HTML
            import re
            summary = re.sub(r'<[^>]+>', '', summary)
            
            symbol = detect_symbol(f"{title} {summary}", "crypto")
            
            # Parse published date
            published = entry.get("published_parsed")
            if published:
                pub_date = datetime(*published[:6])
            else:
                pub_date = datetime.now()
            
            items.append(NewsItem(
                id=generate_news_id(title, "Koin Bülteni"),
                title=title,
                summary=summary[:200] + "..." if len(summary) > 200 else summary,
                source="Koin Bülteni",
                published_at=pub_date,
                symbol=symbol,
                asset_type="crypto",
                url=entry.get("link", "")
            ))
    except Exception as e:
        print(f"Koin Bülteni RSS fetch error: {e}")
    
    return items

async def fetch_all_news() -> List[NewsItem]:
    """
    Fetch news from all sources concurrently and combine results.
    """
    # Fetch from all sources concurrently
    results = await asyncio.gather(
        # Global crypto sources
        fetch_cryptocompare_news(),
        fetch_coindesk_rss(),
        fetch_cointelegraph_rss(),
        # Global stock sources
        fetch_marketwatch_rss(),
        fetch_investing_rss(),
        fetch_seeking_alpha_rss(),
        # Turkish sources
        fetch_bloomberght_rss(),
        fetch_paraanaliz_rss(),
        fetch_koinbulteni_rss(),
        return_exceptions=True
    )
    
    all_items = []
    for result in results:
        if isinstance(result, list):
            all_items.extend(result)
        else:
            print(f"News fetch error: {result}")
    
    # Remove duplicates by title similarity
    seen_titles = set()
    unique_items = []
    for item in all_items:
        title_key = item.title.lower()[:50]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_items.append(item)
    
    # Sort by published date (newest first)
    unique_items.sort(key=lambda x: x.published_at, reverse=True)
    
    return unique_items
