"""
Oracle-X Shared Utilities
Logging, shared state, and helper functions used across routers.
"""
from typing import Optional, List
from datetime import datetime, timedelta
from models.schemas import NewsItem


# ═══════════════════════════════════════════════════════════════════════════════
# TERMINAL COLORS & LOGGING
# ═══════════════════════════════════════════════════════════════════════════════
class Colors:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log_header(message: str):
    print(f"\n{Colors.PURPLE}{'═'*60}{Colors.END}", flush=True)
    print(f"{Colors.PURPLE}{Colors.BOLD}  🔮 {message}{Colors.END}", flush=True)
    print(f"{Colors.PURPLE}{'═'*60}{Colors.END}", flush=True)

def log_step(emoji: str, message: str, color: str = Colors.CYAN):
    print(f"{color}  {emoji}  {message}{Colors.END}", flush=True)

def log_success(message: str):
    print(f"{Colors.GREEN}  ✓  {message}{Colors.END}", flush=True)

def log_warning(message: str):
    print(f"{Colors.YELLOW}  ⚠  {message}{Colors.END}", flush=True)

def log_error(message: str):
    print(f"{Colors.RED}  ✗  {message}{Colors.END}", flush=True)

def log_info(message: str):
    print(f"{Colors.GRAY}      {message}{Colors.END}", flush=True)

def log_result(label: str, value: str, color: str = Colors.WHITE):
    print(f"{Colors.GRAY}      {label}: {color}{value}{Colors.END}", flush=True)


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION FLAGS
# ═══════════════════════════════════════════════════════════════════════════════
# Set to True to use real API data, False for mock data
USE_REAL_API = True
# Set to True to use Ollama AI for analysis
USE_OLLAMA_AI = True


# ═══════════════════════════════════════════════════════════════════════════════
# MOCK NEWS DATA (for development fallback)
# ═══════════════════════════════════════════════════════════════════════════════
MOCK_NEWS: List[NewsItem] = [
    NewsItem(
        id="news_001",
        title="Bitcoin Surges Past $105K as Institutional Demand Grows",
        summary="Major financial institutions increase BTC holdings, driving unprecedented rally.",
        source="CryptoNews",
        published_at=datetime.now() - timedelta(hours=1),
        symbol="BINANCE:BTCUSDT",
        asset_type="crypto",
        url="https://example.com/btc-surge"
    ),
    NewsItem(
        id="news_002",
        title="Ethereum 2.0 Staking Rewards Hit All-Time High",
        summary="ETH staking yields reach 8.2% as network activity increases.",
        source="DeFi Daily",
        published_at=datetime.now() - timedelta(hours=2),
        symbol="BINANCE:ETHUSDT",
        asset_type="crypto",
        url="https://example.com/eth-staking"
    ),
    NewsItem(
        id="news_003",
        title="Apple Announces Revolutionary AI Chip for iPhone 17",
        summary="New A19 Bionic chip promises 3x faster on-device AI processing.",
        source="TechCrunch",
        published_at=datetime.now() - timedelta(hours=3),
        symbol="NASDAQ:AAPL",
        asset_type="stock",
        url="https://example.com/apple-ai"
    ),
    NewsItem(
        id="news_004",
        title="Tesla Cybertruck Deliveries Exceed 500K Units in Q4",
        summary="Record-breaking quarter as Cybertruck becomes best-selling electric truck.",
        source="Electrek",
        published_at=datetime.now() - timedelta(hours=4),
        symbol="NASDAQ:TSLA",
        asset_type="stock",
        url="https://example.com/tesla-cybertruck"
    ),
    NewsItem(
        id="news_005",
        title="Microsoft Azure AI Revenue Doubles Year-Over-Year",
        summary="Cloud AI services drive massive growth as enterprise adoption accelerates.",
        source="Bloomberg",
        published_at=datetime.now() - timedelta(hours=5),
        symbol="NASDAQ:MSFT",
        asset_type="stock",
        url="https://example.com/msft-azure"
    ),
    NewsItem(
        id="news_006",
        title="Solana Network Processes 100K TPS in Stress Test",
        summary="New optimization upgrades push Solana to unprecedented transaction speeds.",
        source="The Block",
        published_at=datetime.now() - timedelta(hours=6),
        symbol="BINANCE:SOLUSDT",
        asset_type="crypto",
        url="https://example.com/solana-tps"
    ),
    NewsItem(
        id="news_007",
        title="NVIDIA Unveils Next-Gen H200 AI Accelerator",
        summary="New GPU delivers 2x inference performance for large language models.",
        source="AnandTech",
        published_at=datetime.now() - timedelta(hours=7),
        symbol="NASDAQ:NVDA",
        asset_type="stock",
        url="https://example.com/nvidia-h200"
    ),
    NewsItem(
        id="news_008",
        title="XRP Sees Major Exchange Listings After SEC Victory",
        summary="Multiple major exchanges re-list XRP following regulatory clarity.",
        source="CoinDesk",
        published_at=datetime.now() - timedelta(hours=8),
        symbol="BINANCE:XRPUSDT",
        asset_type="crypto",
        url="https://example.com/xrp-listings"
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# NEWS CACHE (shared between news and analysis endpoints)
# ═══════════════════════════════════════════════════════════════════════════════
_news_cache: dict = {}


def get_news_cache() -> dict:
    """Get the news cache dict."""
    return _news_cache


def update_news_cache(items):
    """Update the news cache with fetched items."""
    global _news_cache
    _news_cache = {item.id: item for item in items}


def get_news_from_cache_or_mock(news_id: str) -> Optional[NewsItem]:
    """Get news item from cache or mock data."""
    if news_id in _news_cache:
        return _news_cache[news_id]
    for item in MOCK_NEWS:
        if item.id == news_id:
            return item
    return None
