"""
News Service - Fetches news from multiple sources
Supports: CryptoCompare, NewsAPI, RSS feeds
"""
import httpx
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import hashlib
import feedparser
from email.utils import parsedate_to_datetime

from models.schemas import NewsItem


def parse_feed_date(entry) -> datetime:
    """
    Parse date from feed entry with proper timezone handling.
    Returns datetime in local time for accurate display.
    """
    now = datetime.now()
    
    try:
        # First try raw published string with timezone info
        raw_pub = entry.get("published", "")
        if raw_pub:
            try:
                # email.utils handles RFC 2822 dates with timezone
                dt = parsedate_to_datetime(raw_pub)
                # Convert to local timezone (Turkey UTC+3)
                local_tz = timezone(timedelta(hours=3))
                dt_local = dt.astimezone(local_tz)
                # Return as naive datetime for compatibility
                result = dt_local.replace(tzinfo=None)
                # Sanity check: date shouldn't be in the future
                if result > now:
                    return now
                return result
            except:
                pass
        
        # Fallback to parsed tuple (feedparser parses to UTC struct_time)
        published = entry.get("published_parsed")
        if published:
            # published_parsed is struct_time in UTC, convert to local (UTC+3)
            dt = datetime(*published[:6], tzinfo=timezone.utc)
            local_tz = timezone(timedelta(hours=3))
            dt_local = dt.astimezone(local_tz)
            result = dt_local.replace(tzinfo=None)
            # Sanity check: date shouldn't be in the future
            if result > now:
                return now
            return result
    except:
        pass
    
    return now



# Symbol mappings for different news sources
# IMPORTANT: Listed in priority order - more specific names first
# Using exchanges where these coins are actually listed on TradingView
CRYPTO_SYMBOLS = [
    # Pi Network - use OKX (Binance doesn't have PI)
    ("PI NETWORK", "OKX:PIUSDT"),
    ("PI TOKEN", "OKX:PIUSDT"),
    ("PI COIN", "OKX:PIUSDT"),
    (" PI ", "OKX:PIUSDT"),
    ("(PI)", "OKX:PIUSDT"),
    
    # Bitcoin - specific patterns
    ("BITCOIN", "BINANCE:BTCUSDT"),
    ("BTCUSDT", "BINANCE:BTCUSDT"),
    ("BTC/", "BINANCE:BTCUSDT"),
    (" BTC ", "BINANCE:BTCUSDT"),
    ("(BTC)", "BINANCE:BTCUSDT"),
    
    # Ethereum
    ("ETHEREUM", "BINANCE:ETHUSDT"),
    ("ETHUSDT", "BINANCE:ETHUSDT"),
    ("ETH/", "BINANCE:ETHUSDT"),
    (" ETH ", "BINANCE:ETHUSDT"),
    ("(ETH)", "BINANCE:ETHUSDT"),
    
    # Solana
    ("SOLANA", "BINANCE:SOLUSDT"),
    ("SOLUSDT", "BINANCE:SOLUSDT"),
    (" SOL ", "BINANCE:SOLUSDT"),
    ("(SOL)", "BINANCE:SOLUSDT"),
    
    # XRP / Ripple
    ("RIPPLE", "BINANCE:XRPUSDT"),
    ("XRPUSDT", "BINANCE:XRPUSDT"),
    (" XRP ", "BINANCE:XRPUSDT"),
    ("(XRP)", "BINANCE:XRPUSDT"),
    
    # Cardano
    ("CARDANO", "BINANCE:ADAUSDT"),
    ("ADAUSDT", "BINANCE:ADAUSDT"),
    (" ADA ", "BINANCE:ADAUSDT"),
    ("(ADA)", "BINANCE:ADAUSDT"),
    
    # Dogecoin
    ("DOGECOIN", "BINANCE:DOGEUSDT"),
    ("DOGEUSDT", "BINANCE:DOGEUSDT"),
    (" DOGE ", "BINANCE:DOGEUSDT"),
    ("(DOGE)", "BINANCE:DOGEUSDT"),
    
    # Shiba Inu
    ("SHIBA INU", "BINANCE:SHIBUSDT"),
    ("SHIBA", "BINANCE:SHIBUSDT"),
    ("SHIBUSDT", "BINANCE:SHIBUSDT"),
    (" SHIB ", "BINANCE:SHIBUSDT"),
    ("(SHIB)", "BINANCE:SHIBUSDT"),
    
    # Pepe
    ("PEPE COIN", "BINANCE:PEPEUSDT"),
    ("PEPEUSDT", "BINANCE:PEPEUSDT"),
    (" PEPE ", "BINANCE:PEPEUSDT"),
    ("(PEPE)", "BINANCE:PEPEUSDT"),
    
    # Polkadot
    ("POLKADOT", "BINANCE:DOTUSDT"),
    ("DOTUSDT", "BINANCE:DOTUSDT"),
    (" DOT ", "BINANCE:DOTUSDT"),
    ("(DOT)", "BINANCE:DOTUSDT"),
    
    # Avalanche
    ("AVALANCHE", "BINANCE:AVAXUSDT"),
    ("AVAXUSDT", "BINANCE:AVAXUSDT"),
    (" AVAX ", "BINANCE:AVAXUSDT"),
    ("(AVAX)", "BINANCE:AVAXUSDT"),
    
    # Polygon / MATIC
    ("POLYGON", "BINANCE:MATICUSDT"),
    ("MATICUSDT", "BINANCE:MATICUSDT"),
    (" MATIC ", "BINANCE:MATICUSDT"),
    ("(MATIC)", "BINANCE:MATICUSDT"),
    
    # Chainlink
    ("CHAINLINK", "BINANCE:LINKUSDT"),
    ("LINKUSDT", "BINANCE:LINKUSDT"),
    (" LINK ", "BINANCE:LINKUSDT"),
    ("(LINK)", "BINANCE:LINKUSDT"),
    
    # Uniswap
    ("UNISWAP", "BINANCE:UNIUSDT"),
    ("UNIUSDT", "BINANCE:UNIUSDT"),
    (" UNI ", "BINANCE:UNIUSDT"),
    ("(UNI)", "BINANCE:UNIUSDT"),
    
    # Litecoin
    ("LITECOIN", "BINANCE:LTCUSDT"),
    ("LTCUSDT", "BINANCE:LTCUSDT"),
    (" LTC ", "BINANCE:LTCUSDT"),
    ("(LTC)", "BINANCE:LTCUSDT"),
    
    # Tron
    ("TRON", "BINANCE:TRXUSDT"),
    ("TRXUSDT", "BINANCE:TRXUSDT"),
    (" TRX ", "BINANCE:TRXUSDT"),
    ("(TRX)", "BINANCE:TRXUSDT"),
    
    # BNB
    ("BINANCE COIN", "BINANCE:BNBUSDT"),
    ("BNBUSDT", "BINANCE:BNBUSDT"),
    (" BNB ", "BINANCE:BNBUSDT"),
    ("(BNB)", "BINANCE:BNBUSDT"),
    
    # Tether - use USDC pair
    ("TETHER", "BINANCE:USDCUSDT"),
    (" USDT ", "BINANCE:USDCUSDT"),
    
    # ATOM / Cosmos
    ("COSMOS", "BINANCE:ATOMUSDT"),
    ("ATOMUSDT", "BINANCE:ATOMUSDT"),
    (" ATOM ", "BINANCE:ATOMUSDT"),
    ("(ATOM)", "BINANCE:ATOMUSDT"),
    
    # Near Protocol
    ("NEAR PROTOCOL", "BINANCE:NEARUSDT"),
    ("NEARUSDT", "BINANCE:NEARUSDT"),
    (" NEAR ", "BINANCE:NEARUSDT"),
    ("(NEAR)", "BINANCE:NEARUSDT"),
    
    # Sui
    ("SUI NETWORK", "BINANCE:SUIUSDT"),
    ("SUIUSDT", "BINANCE:SUIUSDT"),
    (" SUI ", "BINANCE:SUIUSDT"),
    ("(SUI)", "BINANCE:SUIUSDT"),
    
    # Aptos
    ("APTOS", "BINANCE:APTUSDT"),
    ("APTUSDT", "BINANCE:APTUSDT"),
    (" APT ", "BINANCE:APTUSDT"),
    ("(APT)", "BINANCE:APTUSDT"),
    
    # Arbitrum
    ("ARBITRUM", "BINANCE:ARBUSDT"),
    ("ARBUSDT", "BINANCE:ARBUSDT"),
    (" ARB ", "BINANCE:ARBUSDT"),
    ("(ARB)", "BINANCE:ARBUSDT"),
    
    # Optimism
    ("OPTIMISM", "BINANCE:OPUSDT"),
    ("OPUSDT", "BINANCE:OPUSDT"),
    (" OP ", "BINANCE:OPUSDT"),
    ("(OP)", "BINANCE:OPUSDT"),
]

STOCK_SYMBOLS = {
    # ETFs & Indices (Most common defaults)
    "SPY": "AMEX:SPY", "S&P 500": "AMEX:SPY", "S&P500": "AMEX:SPY",
    "QQQ": "NASDAQ:QQQ", "NASDAQ 100": "NASDAQ:QQQ",
    "DIA": "AMEX:DIA", "DOW JONES": "AMEX:DIA",
    "IWM": "AMEX:IWM", "RUSSELL": "AMEX:IWM",
    "VTI": "AMEX:VTI",
    "VOO": "AMEX:VOO",
    
    # Tech Giants
    "AAPL": "NASDAQ:AAPL", "APPLE": "NASDAQ:AAPL",
    "TSLA": "NASDAQ:TSLA", "TESLA": "NASDAQ:TSLA",
    "MSFT": "NASDAQ:MSFT", "MICROSOFT": "NASDAQ:MSFT",
    "NVDA": "NASDAQ:NVDA", "NVIDIA": "NASDAQ:NVDA",
    "GOOGL": "NASDAQ:GOOGL", "GOOGLE": "NASDAQ:GOOGL", "ALPHABET": "NASDAQ:GOOGL",
    "AMZN": "NASDAQ:AMZN", "AMAZON": "NASDAQ:AMZN",
    "META": "NASDAQ:META", "FACEBOOK": "NASDAQ:META",
    "NFLX": "NASDAQ:NFLX", "NETFLIX": "NASDAQ:NFLX",
    "AMD": "NASDAQ:AMD",
    "INTC": "NASDAQ:INTC", "INTEL": "NASDAQ:INTC",
    "CRM": "NYSE:CRM", "SALESFORCE": "NYSE:CRM",
    "ORCL": "NYSE:ORCL", "ORACLE": "NYSE:ORCL",
    "CSCO": "NASDAQ:CSCO", "CISCO": "NASDAQ:CSCO",
    "ADBE": "NASDAQ:ADBE", "ADOBE": "NASDAQ:ADBE",
    
    # Finance
    "JPM": "NYSE:JPM", "JPMORGAN": "NYSE:JPM", "JP MORGAN": "NYSE:JPM",
    "BAC": "NYSE:BAC", "BANK OF AMERICA": "NYSE:BAC",
    "GS": "NYSE:GS", "GOLDMAN": "NYSE:GS", "GOLDMAN SACHS": "NYSE:GS",
    "MS": "NYSE:MS", "MORGAN STANLEY": "NYSE:MS",
    "WFC": "NYSE:WFC", "WELLS FARGO": "NYSE:WFC",
    "C": "NYSE:C", "CITIGROUP": "NYSE:C", "CITI": "NYSE:C",
    "V": "NYSE:V", "VISA": "NYSE:V",
    "MA": "NYSE:MA", "MASTERCARD": "NYSE:MA",
    "AXP": "NYSE:AXP", "AMERICAN EXPRESS": "NYSE:AXP",
    "BLK": "NYSE:BLK", "BLACKROCK": "NYSE:BLK",
    
    # Industrial
    "CAT": "NYSE:CAT", "CATERPILLAR": "NYSE:CAT",
    "BA": "NYSE:BA", "BOEING": "NYSE:BA",
    "GE": "NYSE:GE", "GENERAL ELECTRIC": "NYSE:GE",
    "HON": "NASDAQ:HON", "HONEYWELL": "NASDAQ:HON",
    "UPS": "NYSE:UPS",
    "FDX": "NYSE:FDX", "FEDEX": "NYSE:FDX",
    "DE": "NYSE:DE", "DEERE": "NYSE:DE", "JOHN DEERE": "NYSE:DE",
    
    # Airlines & Transport
    "LUV": "NYSE:LUV", "SOUTHWEST": "NYSE:LUV",
    "DAL": "NYSE:DAL", "DELTA": "NYSE:DAL",
    "UAL": "NASDAQ:UAL", "UNITED AIRLINES": "NASDAQ:UAL",
    "AAL": "NASDAQ:AAL", "AMERICAN AIRLINES": "NASDAQ:AAL",
    
    # Telecom
    "VZ": "NYSE:VZ", "VERIZON": "NYSE:VZ",
    "T": "NYSE:T", "AT&T": "NYSE:T",
    "TMUS": "NASDAQ:TMUS", "T-MOBILE": "NASDAQ:TMUS",
    
    # Energy
    "XOM": "NYSE:XOM", "EXXON": "NYSE:XOM", "EXXONMOBIL": "NYSE:XOM",
    "CVX": "NYSE:CVX", "CHEVRON": "NYSE:CVX",
    "COP": "NYSE:COP", "CONOCOPHILLIPS": "NYSE:COP",
    "OXY": "NYSE:OXY", "OCCIDENTAL": "NYSE:OXY",
    "SLB": "NYSE:SLB", "SCHLUMBERGER": "NYSE:SLB",
    
    # Consumer
    "WMT": "NYSE:WMT", "WALMART": "NYSE:WMT",
    "COST": "NASDAQ:COST", "COSTCO": "NASDAQ:COST",
    "TGT": "NYSE:TGT", "TARGET": "NYSE:TGT",
    "HD": "NYSE:HD", "HOME DEPOT": "NYSE:HD",
    "LOW": "NYSE:LOW", "LOWES": "NYSE:LOW",
    "KO": "NYSE:KO", "COCA-COLA": "NYSE:KO", "COKE": "NYSE:KO",
    "PEP": "NASDAQ:PEP", "PEPSI": "NASDAQ:PEP", "PEPSICO": "NASDAQ:PEP",
    "MCD": "NYSE:MCD", "MCDONALD": "NYSE:MCD", "MCDONALDS": "NYSE:MCD",
    "SBUX": "NASDAQ:SBUX", "STARBUCKS": "NASDAQ:SBUX",
    "NKE": "NYSE:NKE", "NIKE": "NYSE:NKE",
    "DIS": "NYSE:DIS", "DISNEY": "NYSE:DIS", "WALT DISNEY": "NYSE:DIS",
    
    # Pharma & Healthcare
    "JNJ": "NYSE:JNJ", "JOHNSON": "NYSE:JNJ", "JOHNSON & JOHNSON": "NYSE:JNJ",
    "PFE": "NYSE:PFE", "PFIZER": "NYSE:PFE",
    "MRNA": "NASDAQ:MRNA", "MODERNA": "NASDAQ:MRNA",
    "UNH": "NYSE:UNH", "UNITEDHEALTH": "NYSE:UNH",
    "CVS": "NYSE:CVS",
    "ABBV": "NYSE:ABBV", "ABBVIE": "NYSE:ABBV",
    "LLY": "NYSE:LLY", "ELI LILLY": "NYSE:LLY", "LILLY": "NYSE:LLY",
    "MRK": "NYSE:MRK", "MERCK": "NYSE:MRK",
    
    # Semiconductors
    "AVGO": "NASDAQ:AVGO", "BROADCOM": "NASDAQ:AVGO",
    "QCOM": "NASDAQ:QCOM", "QUALCOMM": "NASDAQ:QCOM",
    "TXN": "NASDAQ:TXN", "TEXAS INSTRUMENTS": "NASDAQ:TXN",
    "MU": "NASDAQ:MU", "MICRON": "NASDAQ:MU",
    "AMAT": "NASDAQ:AMAT", "APPLIED MATERIALS": "NASDAQ:AMAT",
    "LRCX": "NASDAQ:LRCX", "LAM RESEARCH": "NASDAQ:LRCX",
    "KLAC": "NASDAQ:KLAC",
    "ASML": "NASDAQ:ASML",
    "TSM": "NYSE:TSM", "TAIWAN SEMICONDUCTOR": "NYSE:TSM", "TSMC": "NYSE:TSM",
}


def detect_symbol(text: str, asset_type: str, title: str = "") -> Optional[str]:
    """
    Detect trading symbol from news text with intelligent priority-based matching.
    
    Priority:
    1. Exact match in title (most important)
    2. Exact match in body
    3. Longer/more specific matches > shorter matches
    """
    # Normalize text for matching
    title_upper = " " + title.upper() + " " if title else ""
    text_upper = " " + text.upper() + " "  # Add spaces for boundary matching
    
    if asset_type == "crypto":
        # First, try to find matches in title (highest priority)
        for keyword, tradingview in CRYPTO_SYMBOLS:
            if keyword in title_upper:
                return tradingview
        
        # Then try body text
        for keyword, tradingview in CRYPTO_SYMBOLS:
            if keyword in text_upper:
                return tradingview
        
        return "BINANCE:BTCUSDT"  # Default
    else:
        # For stocks, also prioritize title matches
        # First check title
        for keyword, tradingview in STOCK_SYMBOLS.items():
            if keyword in title_upper:
                return tradingview
        
        # Then check body
        for keyword, tradingview in STOCK_SYMBOLS.items():
            if keyword in text_upper:
                return tradingview
        
        return "AMEX:SPY"  # Default to S&P 500 ETF


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
                    symbol = detect_symbol(body, "crypto", title)
                    
                    # CryptoCompare returns UTC timestamp, convert to local time (UTC+3)
                    pub_timestamp = news.get("published_on", datetime.now().timestamp())
                    pub_dt_utc = datetime.fromtimestamp(pub_timestamp, tz=timezone.utc)
                    local_tz = timezone(timedelta(hours=3))
                    pub_dt_local = pub_dt_utc.astimezone(local_tz).replace(tzinfo=None)
                    
                    # Sanity check: date shouldn't be in the future
                    now = datetime.now()
                    if pub_dt_local > now:
                        pub_dt_local = now
                    
                    items.append(NewsItem(
                        id=generate_news_id(title, news.get("source", "")),
                        title=title,
                        summary=body[:200] + "..." if len(body) > 200 else body,
                        source=news.get("source", "CryptoCompare"),
                        published_at=pub_dt_local,
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
            
            symbol = detect_symbol(summary, "crypto", title)
            
            pub_date = parse_feed_date(entry)
            
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
            
            symbol = detect_symbol(summary, "crypto", title)
            
            pub_date = parse_feed_date(entry)
            
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
            
            symbol = detect_symbol(summary, "stock", title)
            pub_date = parse_feed_date(entry)
            
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
            
            symbol = detect_symbol(summary, "stock", title)
            pub_date = parse_feed_date(entry)
            
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
            
            symbol = detect_symbol(summary, "stock", title)
            pub_date = parse_feed_date(entry)
            
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
            title = re.sub(r'<!\[CDATA\[|\]\]>', '', title).strip()
            summary = re.sub(r'<!\[CDATA\[|\]\]>', '', summary)
            summary = re.sub(r'<[^>]+>', '', summary).strip()
            
            # Detect if it's crypto or stock related
            crypto_keywords = ["bitcoin", "btc", "ethereum", "eth", "kripto", "coin", "altcoin"]
            is_crypto = any(kw in title.lower() or kw in summary.lower() for kw in crypto_keywords)
            asset_type = "crypto" if is_crypto else "stock"
            symbol = detect_symbol(summary, asset_type, title)
            
            pub_date = parse_feed_date(entry)
            
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
            symbol = detect_symbol(summary, asset_type, title)
            
            pub_date = parse_feed_date(entry)
            
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
            
            symbol = detect_symbol(summary, "crypto", title)
            
            pub_date = parse_feed_date(entry)
            
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
