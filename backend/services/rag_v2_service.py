"""
RAG 2.0 Service - Advanced Retrieval Augmented Generation
Features:
- Historical news with price outcomes
- Historical price data indexing
- Event correlation analysis
- Temporal context retrieval
- Automatic learning from past predictions
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import os
import json
import asyncio
import httpx

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Data directory for persistent storage
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "rag_v2")

# Collections
NEWS_COLLECTION = "historical_news"
EVENTS_COLLECTION = "market_events"
PRICE_COLLECTION = "price_history"

# Embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Binance API
BINANCE_API = "https://api.binance.com/api/v3"

# Important crypto events to track
IMPORTANT_EVENTS = [
    {"date": "2024-04-20", "event": "Bitcoin Halving 2024", "symbol": "BTC", "type": "halving"},
    {"date": "2024-01-11", "event": "Bitcoin ETF Approved", "symbol": "BTC", "type": "regulatory"},
    {"date": "2023-03-10", "event": "SVB Bank Collapse", "symbol": "BTC", "type": "macro"},
    {"date": "2022-11-11", "event": "FTX Collapse", "symbol": "BTC", "type": "exchange"},
    {"date": "2021-11-10", "event": "Bitcoin ATH $69K", "symbol": "BTC", "type": "price_milestone"},
    {"date": "2021-04-14", "event": "Coinbase IPO", "symbol": "BTC", "type": "adoption"},
    {"date": "2020-05-11", "event": "Bitcoin Halving 2020", "symbol": "BTC", "type": "halving"},
    {"date": "2024-03-13", "event": "Ethereum Dencun Upgrade", "symbol": "ETH", "type": "upgrade"},
    {"date": "2023-04-12", "event": "Ethereum Shanghai Upgrade", "symbol": "ETH", "type": "upgrade"},
    {"date": "2022-09-15", "event": "Ethereum Merge (PoS)", "symbol": "ETH", "type": "upgrade"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBALS (Lazy Loading)
# ═══════════════════════════════════════════════════════════════════════════════

_embedding_model = None
_chroma_client = None
_collections = {}


def get_embedding_model() -> SentenceTransformer:
    """Get or initialize the embedding model."""
    global _embedding_model
    if _embedding_model is None:
        print("[RAG 2.0] Loading embedding model...")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        print("[RAG 2.0] Embedding model loaded!")
    return _embedding_model


def get_chroma_client():
    """Get or initialize ChromaDB client."""
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(DATA_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=DATA_DIR)
        print(f"[RAG 2.0] ChromaDB client initialized at {DATA_DIR}")
    return _chroma_client


def get_collection(name: str):
    """Get or create a collection."""
    global _collections
    if name not in _collections:
        client = get_chroma_client()
        _collections[name] = client.get_or_create_collection(
            name=name,
            metadata={"description": f"RAG 2.0 collection: {name}"}
        )
        print(f"[RAG 2.0] Collection '{name}' ready with {_collections[name].count()} items")
    return _collections[name]


def generate_embedding(text: str) -> List[float]:
    """Generate embedding vector for text."""
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


# ═══════════════════════════════════════════════════════════════════════════════
# HISTORICAL PRICE DATA
# ═══════════════════════════════════════════════════════════════════════════════

async def fetch_historical_prices(symbol: str, days: int = 365) -> List[Dict]:
    """
    Fetch historical daily prices from Binance.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Calculate time range
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            
            response = await client.get(
                f"{BINANCE_API}/klines",
                params={
                    "symbol": f"{symbol}USDT",
                    "interval": "1d",
                    "startTime": start_time,
                    "endTime": end_time,
                    "limit": 1000
                }
            )
            
            if response.status_code != 200:
                return []
            
            klines = response.json()
            prices = []
            
            for k in klines:
                prices.append({
                    "date": datetime.fromtimestamp(k[0] / 1000).strftime("%Y-%m-%d"),
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                    "change_pct": ((float(k[4]) - float(k[1])) / float(k[1])) * 100
                })
            
            return prices
    except Exception as e:
        print(f"[RAG 2.0] Error fetching historical prices: {e}")
        return []


async def index_price_history(symbol: str = "BTC", days: int = 365) -> int:
    """
    Index historical price data into vector store.
    Creates embeddings for price patterns and events.
    """
    collection = get_collection(PRICE_COLLECTION)
    prices = await fetch_historical_prices(symbol, days)
    
    if not prices:
        return 0
    
    indexed = 0
    for i, price in enumerate(prices):
        # Create descriptive text for embedding
        trend = "up" if price["change_pct"] > 0 else "down"
        magnitude = "strong" if abs(price["change_pct"]) > 3 else "moderate" if abs(price["change_pct"]) > 1 else "slight"
        
        text = f"{symbol} on {price['date']}: Price moved {magnitude}ly {trend} ({price['change_pct']:.1f}%). "
        text += f"Opened at ${price['open']:,.0f}, closed at ${price['close']:,.0f}. "
        text += f"Volume: ${price['volume']/1e9:.2f}B. "
        
        # Add weekly context
        if i >= 7:
            weekly_change = ((price['close'] - prices[i-7]['close']) / prices[i-7]['close']) * 100
            text += f"Weekly change: {weekly_change:+.1f}%."
        
        try:
            embedding = generate_embedding(text)
            doc_id = f"{symbol}_{price['date']}"
            
            collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                metadatas=[{
                    "symbol": symbol,
                    "date": price["date"],
                    "close": price["close"],
                    "change_pct": price["change_pct"],
                    "volume": price["volume"],
                    "type": "daily_price"
                }],
                documents=[text]
            )
            indexed += 1
        except Exception as e:
            print(f"[RAG 2.0] Error indexing price: {e}")
    
    print(f"[RAG 2.0] Indexed {indexed} price records for {symbol}")
    return indexed


# ═══════════════════════════════════════════════════════════════════════════════
# MARKET EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

async def index_market_events() -> int:
    """
    Index important market events into vector store.
    """
    collection = get_collection(EVENTS_COLLECTION)
    indexed = 0
    
    for event in IMPORTANT_EVENTS:
        text = f"{event['event']} happened on {event['date']}. "
        text += f"This was a {event['type']} event affecting {event['symbol']}."
        
        # Fetch price data around event
        event_date = datetime.strptime(event['date'], "%Y-%m-%d")
        
        # Get price change context (simplified)
        price_context = await get_price_around_date(event['symbol'], event_date)
        if price_context:
            text += f" Price before: ${price_context['before']:,.0f}, after: ${price_context['after']:,.0f} ({price_context['change']:+.1f}%)."
        
        try:
            embedding = generate_embedding(text)
            doc_id = f"event_{event['date']}_{event['symbol']}"
            
            collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                metadatas=[{
                    "symbol": event["symbol"],
                    "date": event["date"],
                    "event_type": event["type"],
                    "event_name": event["event"]
                }],
                documents=[text]
            )
            indexed += 1
        except Exception as e:
            print(f"[RAG 2.0] Error indexing event: {e}")
    
    print(f"[RAG 2.0] Indexed {indexed} market events")
    return indexed


async def get_price_around_date(symbol: str, event_date: datetime) -> Optional[Dict]:
    """Get price before and after a specific date."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Get data 7 days before and after
            start_time = int((event_date - timedelta(days=7)).timestamp() * 1000)
            end_time = int((event_date + timedelta(days=7)).timestamp() * 1000)
            
            response = await client.get(
                f"{BINANCE_API}/klines",
                params={
                    "symbol": f"{symbol}USDT",
                    "interval": "1d",
                    "startTime": start_time,
                    "endTime": end_time,
                    "limit": 15
                }
            )
            
            if response.status_code != 200:
                return None
            
            klines = response.json()
            if len(klines) < 10:
                return None
            
            before_price = float(klines[0][4])  # Close before
            after_price = float(klines[-1][4])   # Close after
            
            return {
                "before": before_price,
                "after": after_price,
                "change": ((after_price - before_price) / before_price) * 100
            }
    except:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# NEWS INDEXING
# ═══════════════════════════════════════════════════════════════════════════════

def store_news_with_outcome(
    title: str,
    summary: str,
    symbol: str,
    sentiment: str,
    confidence: float,
    price_before: Optional[float] = None,
    price_after: Optional[float] = None,
    actual_outcome: Optional[str] = None
) -> bool:
    """
    Store news with its outcome for future learning.
    """
    try:
        collection = get_collection(NEWS_COLLECTION)
        
        # Create rich text for embedding
        text = f"{title}. {summary}"
        if actual_outcome:
            text += f" Outcome: {actual_outcome}."
        
        embedding = generate_embedding(text)
        
        # Calculate price change if available
        price_change = None
        if price_before and price_after:
            price_change = ((price_after - price_before) / price_before) * 100
        
        # Determine if prediction was correct
        prediction_correct = None
        if actual_outcome and sentiment:
            if sentiment == "bullish" and actual_outcome in ["price_up", "bullish"]:
                prediction_correct = True
            elif sentiment == "bearish" and actual_outcome in ["price_down", "bearish"]:
                prediction_correct = True
            elif actual_outcome == "neutral":
                prediction_correct = sentiment == "neutral"
            else:
                prediction_correct = False
        
        doc_id = hashlib.md5(f"{title}:{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        metadata = {
            "title": title[:500],
            "symbol": symbol,
            "sentiment": sentiment,
            "confidence": confidence,
            "stored_at": datetime.now().isoformat(),
        }
        
        if price_change is not None:
            metadata["price_change"] = price_change
        if actual_outcome:
            metadata["actual_outcome"] = actual_outcome
        if prediction_correct is not None:
            metadata["prediction_correct"] = prediction_correct
        
        collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[text[:2000]]
        )
        
        return True
    except Exception as e:
        print(f"[RAG 2.0] Error storing news: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED RETRIEVAL
# ═══════════════════════════════════════════════════════════════════════════════

def query_historical_context(
    query: str,
    symbol: Optional[str] = None,
    include_events: bool = True,
    include_prices: bool = True,
    include_news: bool = True,
    k: int = 5
) -> Dict[str, List[Dict]]:
    """
    Query historical context from all collections.
    Returns events, price patterns, and news that are similar to the query.
    """
    results = {
        "events": [],
        "prices": [],
        "news": [],
        "summary": ""
    }
    
    query_embedding = generate_embedding(query)
    
    # Query market events
    if include_events:
        try:
            events_col = get_collection(EVENTS_COLLECTION)
            if events_col.count() > 0:
                event_results = events_col.query(
                    query_embeddings=[query_embedding],
                    n_results=min(k, events_col.count()),
                    include=["documents", "metadatas", "distances"]
                )
                
                if event_results and event_results['ids'][0]:
                    for i, doc_id in enumerate(event_results['ids'][0]):
                        meta = event_results['metadatas'][0][i]
                        distance = event_results['distances'][0][i]
                        similarity = 1 / (1 + distance)
                        
                        if similarity > 0.3:
                            results["events"].append({
                                "event": meta.get("event_name", ""),
                                "date": meta.get("date", ""),
                                "type": meta.get("event_type", ""),
                                "symbol": meta.get("symbol", ""),
                                "similarity": round(similarity, 3)
                            })
        except Exception as e:
            print(f"[RAG 2.0] Error querying events: {e}")
    
    # Query price history
    if include_prices:
        try:
            prices_col = get_collection(PRICE_COLLECTION)
            if prices_col.count() > 0:
                where_filter = {"symbol": symbol} if symbol else None
                
                price_results = prices_col.query(
                    query_embeddings=[query_embedding],
                    n_results=min(k, prices_col.count()),
                    where=where_filter,
                    include=["documents", "metadatas", "distances"]
                )
                
                if price_results and price_results['ids'][0]:
                    for i, doc_id in enumerate(price_results['ids'][0]):
                        meta = price_results['metadatas'][0][i]
                        distance = price_results['distances'][0][i]
                        similarity = 1 / (1 + distance)
                        
                        if similarity > 0.3:
                            results["prices"].append({
                                "date": meta.get("date", ""),
                                "close": meta.get("close", 0),
                                "change_pct": meta.get("change_pct", 0),
                                "symbol": meta.get("symbol", ""),
                                "similarity": round(similarity, 3)
                            })
        except Exception as e:
            print(f"[RAG 2.0] Error querying prices: {e}")
    
    # Query historical news
    if include_news:
        try:
            news_col = get_collection(NEWS_COLLECTION)
            if news_col.count() > 0:
                news_results = news_col.query(
                    query_embeddings=[query_embedding],
                    n_results=min(k, news_col.count()),
                    include=["documents", "metadatas", "distances"]
                )
                
                if news_results and news_results['ids'][0]:
                    for i, doc_id in enumerate(news_results['ids'][0]):
                        meta = news_results['metadatas'][0][i]
                        distance = news_results['distances'][0][i]
                        similarity = 1 / (1 + distance)
                        
                        if similarity > 0.4:
                            results["news"].append({
                                "title": meta.get("title", ""),
                                "sentiment": meta.get("sentiment", ""),
                                "outcome": meta.get("actual_outcome", ""),
                                "price_change": meta.get("price_change"),
                                "prediction_correct": meta.get("prediction_correct"),
                                "similarity": round(similarity, 3)
                            })
        except Exception as e:
            print(f"[RAG 2.0] Error querying news: {e}")
    
    # Generate summary
    results["summary"] = _generate_context_summary(results)
    
    return results


def _generate_context_summary(results: Dict) -> str:
    """Generate a human-readable summary of retrieved context."""
    parts = []
    
    if results["events"]:
        parts.append("📅 İlgili Tarihsel Olaylar:")
        for event in results["events"][:3]:
            parts.append(f"  • {event['event']} ({event['date']}) - {event['type']}")
    
    if results["prices"]:
        parts.append("\n📊 Benzer Fiyat Hareketleri:")
        for price in results["prices"][:3]:
            direction = "📈" if price["change_pct"] > 0 else "📉"
            parts.append(f"  • {price['date']}: {direction} {price['change_pct']:+.1f}% (${price['close']:,.0f})")
    
    if results["news"]:
        parts.append("\n📰 Benzer Geçmiş Haberler:")
        for news in results["news"][:3]:
            outcome = f" → {news['outcome']}" if news.get('outcome') else ""
            parts.append(f"  • {news['title'][:60]}... ({news['sentiment']}{outcome})")
    
    return "\n".join(parts) if parts else "Tarihsel veri bulunamadı."


def get_rag_context_v2(
    query: str,
    symbol: Optional[str] = None,
    context_type: str = "all"
) -> str:
    """
    Get enhanced RAG context for LLM prompts.
    
    Args:
        query: User's question or news title
        symbol: Filter by symbol (BTC, ETH, etc.)
        context_type: 'all', 'events', 'prices', 'news'
    
    Returns:
        Formatted context string for LLM
    """
    include_events = context_type in ["all", "events"]
    include_prices = context_type in ["all", "prices"]
    include_news = context_type in ["all", "news"]
    
    results = query_historical_context(
        query=query,
        symbol=symbol,
        include_events=include_events,
        include_prices=include_prices,
        include_news=include_news,
        k=5
    )
    
    # Format for LLM
    context_parts = ["=== TARİHSEL BAĞLAM (RAG 2.0) ===\n"]
    
    if results["events"]:
        context_parts.append("## İlgili Piyasa Olayları:")
        for event in results["events"][:3]:
            context_parts.append(f"- {event['date']}: {event['event']} ({event['type']})")
        context_parts.append("")
    
    if results["prices"]:
        context_parts.append("## Benzer Fiyat Hareketleri:")
        for price in results["prices"][:5]:
            context_parts.append(
                f"- {price['date']}: {price['symbol']} ${price['close']:,.0f} "
                f"({price['change_pct']:+.1f}%)"
            )
        context_parts.append("")
    
    if results["news"]:
        context_parts.append("## Benzer Geçmiş Haberler ve Sonuçları:")
        for news in results["news"][:3]:
            outcome = news.get('outcome', 'bilinmiyor')
            price_change = news.get('price_change')
            correct = news.get('prediction_correct')
            
            line = f"- \"{news['title'][:80]}...\""
            line += f"\n  Tahmin: {news['sentiment'].upper()}"
            if price_change is not None:
                line += f" | Sonuç: {price_change:+.1f}%"
            if correct is not None:
                line += f" | {'✓ Doğru' if correct else '✗ Yanlış'}"
            context_parts.append(line)
    
    return "\n".join(context_parts)


# ═══════════════════════════════════════════════════════════════════════════════
# INITIALIZATION & MAINTENANCE
# ═══════════════════════════════════════════════════════════════════════════════

async def initialize_rag_v2(symbols: List[str] = ["BTC", "ETH", "SOL"]) -> Dict:
    """
    Initialize RAG 2.0 with historical data.
    Should be called once to populate the vector store.
    """
    print("[RAG 2.0] Initializing with historical data...")
    
    stats = {
        "events_indexed": 0,
        "prices_indexed": 0,
        "status": "success"
    }
    
    try:
        # Index market events
        stats["events_indexed"] = await index_market_events()
        
        # Index price history for each symbol
        for symbol in symbols:
            indexed = await index_price_history(symbol, days=365)
            stats["prices_indexed"] += indexed
            await asyncio.sleep(0.5)  # Rate limiting
        
        print(f"[RAG 2.0] Initialization complete: {stats}")
        
    except Exception as e:
        stats["status"] = f"error: {str(e)}"
        print(f"[RAG 2.0] Initialization error: {e}")
    
    return stats


def get_rag_stats() -> Dict:
    """Get statistics about RAG 2.0 collections."""
    try:
        return {
            "news_count": get_collection(NEWS_COLLECTION).count(),
            "events_count": get_collection(EVENTS_COLLECTION).count(),
            "prices_count": get_collection(PRICE_COLLECTION).count(),
            "status": "healthy"
        }
    except Exception as e:
        return {
            "news_count": 0,
            "events_count": 0,
            "prices_count": 0,
            "status": f"error: {str(e)}"
        }


print("[RAG 2.0] Service module loaded. Use initialize_rag_v2() to populate data.")
