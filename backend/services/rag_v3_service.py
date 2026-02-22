"""
RAG v3 Service — Insights Agent
Faz 2: Context Everywhere — Bağlamsal finansal zeka sağlar.

Bu ajan 3 temel görev yapar:
1. Fiyat Hareket Nedeni: Neden yükseliyor/düşüyor? (haber + sosyal sinyal korelasyonu)
2. Tarihsel Haber Benzerliği: Bir habere benzer geçmişte neler oldu + fiyat etkisi
3. Tarih Bazlı Olay Arama: Belirli bir tarihteki en önemli olayı bul (grafik tooltip)
"""
import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from services.rag_v2_service import (
    get_collection, generate_embedding,
    NEWS_COLLECTION, EVENTS_COLLECTION, PRICE_COLLECTION
)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. PRICE MOVEMENT REASONING — "Neden Yükseliyor/Düşüyor?"
# ═══════════════════════════════════════════════════════════════════════════════

async def get_price_movement_reason(symbol: str) -> Dict:
    """
    Analyze why a symbol is moving up or down.
    Correlates recent price change with recent news in RAG.
    
    Returns:
        {
            "symbol": "BTC",
            "price_change_24h": -5.2,
            "direction": "down",
            "reasons": [
                {"title": "SEC sues ...", "sentiment": "bearish", "confidence": 0.85, "similarity": 0.78},
                ...
            ],
            "confidence_score": 0.82,
            "summary": "📉 %5 Düşüş: SEC davası ile ilgili... (Güven: %82)"
        }
    """
    result = {
        "symbol": symbol,
        "price_change_24h": 0,
        "direction": "neutral",
        "reasons": [],
        "confidence_score": 0,
        "summary": ""
    }
    
    try:
        # Step 1: Get current price change from Binance
        price_data = await _get_24h_price_change(symbol)
        if not price_data:
            result["summary"] = f"{symbol} için fiyat verisi alınamadı."
            return result
        
        result["price_change_24h"] = price_data["change_pct"]
        result["direction"] = "up" if price_data["change_pct"] > 0 else "down" if price_data["change_pct"] < 0 else "neutral"
        
        # Step 2: Search RAG for recent news related to this symbol
        query = f"{symbol} price {'increase rally' if result['direction'] == 'up' else 'decrease drop crash'} recent news"
        query_embedding = generate_embedding(query)
        
        news_col = get_collection(NEWS_COLLECTION)
        if news_col.count() == 0:
            result["summary"] = f"{symbol} {result['price_change_24h']:+.1f}% — RAG'da ilgili haber bulunamadı."
            return result
        
        news_results = news_col.query(
            query_embeddings=[query_embedding],
            n_results=min(5, news_col.count()),
            include=["documents", "metadatas", "distances"]
        )
        
        # Step 3: Filter and rank relevant news
        reasons = []
        if news_results and news_results['ids'][0]:
            for i, doc_id in enumerate(news_results['ids'][0]):
                meta = news_results['metadatas'][0][i]
                distance = news_results['distances'][0][i]
                similarity = 1 / (1 + distance)
                
                if similarity > 0.35:
                    reasons.append({
                        "title": meta.get("title", "")[:150],
                        "sentiment": meta.get("sentiment", "unknown"),
                        "confidence": meta.get("confidence", 0),
                        "similarity": round(similarity, 3),
                        "date": meta.get("stored_at", "")[:10]
                    })
        
        result["reasons"] = reasons[:5]
        
        # Step 4: Calculate overall confidence
        if reasons:
            avg_similarity = sum(r["similarity"] for r in reasons) / len(reasons)
            result["confidence_score"] = round(avg_similarity, 2)
        
        # Step 5: Generate human-readable summary
        direction_emoji = "📈" if result["direction"] == "up" else "📉" if result["direction"] == "down" else "➡️"
        change_text = f"{result['price_change_24h']:+.1f}%"
        
        if reasons:
            top_reason = reasons[0]["title"][:80]
            conf_pct = int(result["confidence_score"] * 100)
            result["summary"] = f"{direction_emoji} {change_text}: {top_reason}... (Güven Skoru: %{conf_pct})"
        else:
            result["summary"] = f"{direction_emoji} {change_text}: İlişkili haber bulunamadı."
        
    except Exception as e:
        result["summary"] = f"Analiz hatası: {str(e)}"
        print(f"[RAG v3] Price movement reason error: {e}")
    
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 2. HISTORICAL NEWS SIMILARITY — "Benzer Geçmiş Olaylar"
# ═══════════════════════════════════════════════════════════════════════════════

async def find_historical_news_similarity(news_title: str, news_summary: str = "") -> Dict:
    """
    Given a news item, find similar historical news and their price outcomes.
    
    Returns:
        {
            "query_news": "Bitcoin ETF rejected by SEC",
            "similar_events": [
                {
                    "title": "SEC rejects Winklevoss ETF 2017",
                    "date": "2017-03-10",
                    "outcome": "bearish",
                    "price_change": -8.5,
                    "similarity": 0.87
                },
                ...
            ],
            "avg_price_impact": -5.2,
            "dominant_outcome": "bearish",
            "summary": "Bu habere benzer 5 olay yaşandı. Fiyat ortalama %5.2 düştü."
        }
    """
    result = {
        "query_news": news_title[:200],
        "similar_events": [],
        "avg_price_impact": 0,
        "dominant_outcome": "neutral",
        "summary": ""
    }
    
    try:
        query_text = f"{news_title}. {news_summary}"
        query_embedding = generate_embedding(query_text)
        
        # Search across both news and events collections
        similar_events = []
        
        # Search news collection
        news_col = get_collection(NEWS_COLLECTION)
        if news_col.count() > 0:
            news_results = news_col.query(
                query_embeddings=[query_embedding],
                n_results=min(5, news_col.count()),
                include=["documents", "metadatas", "distances"]
            )
            
            if news_results and news_results['ids'][0]:
                for i, doc_id in enumerate(news_results['ids'][0]):
                    meta = news_results['metadatas'][0][i]
                    distance = news_results['distances'][0][i]
                    similarity = 1 / (1 + distance)
                    
                    if similarity > 0.4:
                        similar_events.append({
                            "title": meta.get("title", "")[:150],
                            "date": meta.get("stored_at", "")[:10],
                            "outcome": meta.get("actual_outcome", meta.get("sentiment", "unknown")),
                            "price_change": meta.get("price_change", None),
                            "similarity": round(similarity, 3),
                            "source": "news"
                        })
        
        # Search events collection
        events_col = get_collection(EVENTS_COLLECTION)
        if events_col.count() > 0:
            event_results = events_col.query(
                query_embeddings=[query_embedding],
                n_results=min(3, events_col.count()),
                include=["documents", "metadatas", "distances"]
            )
            
            if event_results and event_results['ids'][0]:
                for i, doc_id in enumerate(event_results['ids'][0]):
                    meta = event_results['metadatas'][0][i]
                    distance = event_results['distances'][0][i]
                    similarity = 1 / (1 + distance)
                    
                    if similarity > 0.35:
                        similar_events.append({
                            "title": meta.get("event_name", "")[:150],
                            "date": meta.get("date", ""),
                            "outcome": meta.get("event_type", "unknown"),
                            "price_change": None,
                            "similarity": round(similarity, 3),
                            "source": "event"
                        })
        
        # Sort by similarity
        similar_events.sort(key=lambda x: x["similarity"], reverse=True)
        result["similar_events"] = similar_events[:7]
        
        # Calculate average price impact
        price_changes = [e["price_change"] for e in similar_events if e.get("price_change") is not None]
        if price_changes:
            result["avg_price_impact"] = round(sum(price_changes) / len(price_changes), 2)
        
        # Determine dominant outcome
        sentiments = [e["outcome"] for e in similar_events if e.get("outcome")]
        if sentiments:
            from collections import Counter
            most_common = Counter(sentiments).most_common(1)[0][0]
            result["dominant_outcome"] = most_common
        
        # Generate summary
        count = len(similar_events)
        if count > 0:
            if price_changes:
                avg = result["avg_price_impact"]
                direction = "arttı" if avg > 0 else "düştü"
                result["summary"] = f"Bu habere benzer geçmişte {count} olay yaşandı. Fiyat ortalama %{abs(avg):.1f} {direction}."
            else:
                result["summary"] = f"Bu habere benzer geçmişte {count} olay bulundu."
        else:
            result["summary"] = "Benzer geçmiş olay bulunamadı."
    
    except Exception as e:
        result["summary"] = f"Benzerlik analizi hatası: {str(e)}"
        print(f"[RAG v3] News similarity error: {e}")
    
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 3. EVENT AT DATE — Grafik Tooltip İçin
# ═══════════════════════════════════════════════════════════════════════════════

async def get_event_at_date(symbol: str, date_str: str) -> Dict:
    """
    Find the most significant event near a specific date.
    Used for chart tooltip overlays.
    
    Args:
        symbol: Trading symbol (BTC, ETH, etc.)
        date_str: Date string (YYYY-MM-DD)
    
    Returns:
        {
            "date": "2024-03-12",
            "event": "ABD Enflasyon Verisi Açıklandı (%3.2)",
            "type": "macro",
            "price_impact": -2.1,
            "found": true
        }
    """
    result = {
        "date": date_str,
        "event": None,
        "type": None,
        "price_impact": None,
        "found": False
    }
    
    try:
        # Create query for this date range
        query = f"{symbol} price event on {date_str}"
        query_embedding = generate_embedding(query)
        
        # Search events collection first (most relevant for tooltips)
        events_col = get_collection(EVENTS_COLLECTION)
        best_match = None
        best_similarity = 0
        
        if events_col.count() > 0:
            event_results = events_col.query(
                query_embeddings=[query_embedding],
                n_results=min(5, events_col.count()),
                include=["documents", "metadatas", "distances"]
            )
            
            if event_results and event_results['ids'][0]:
                for i, doc_id in enumerate(event_results['ids'][0]):
                    meta = event_results['metadatas'][0][i]
                    distance = event_results['distances'][0][i]
                    similarity = 1 / (1 + distance)
                    
                    # Check if event date is within 3 days of target date
                    event_date = meta.get("date", "")
                    if event_date and _is_date_nearby(date_str, event_date, days=3):
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = {
                                "event": meta.get("event_name", ""),
                                "type": meta.get("event_type", ""),
                                "date": event_date
                            }
        
        # Also search in news collection
        news_col = get_collection(NEWS_COLLECTION)
        if news_col.count() > 0 and not best_match:
            news_results = news_col.query(
                query_embeddings=[query_embedding],
                n_results=min(5, news_col.count()),
                include=["documents", "metadatas", "distances"]
            )
            
            if news_results and news_results['ids'][0]:
                for i, doc_id in enumerate(news_results['ids'][0]):
                    meta = news_results['metadatas'][0][i]
                    distance = news_results['distances'][0][i]
                    similarity = 1 / (1 + distance)
                    
                    stored_at = meta.get("stored_at", "")[:10]
                    if stored_at and _is_date_nearby(date_str, stored_at, days=2):
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = {
                                "event": meta.get("title", "")[:100],
                                "type": meta.get("sentiment", "neutral"),
                                "date": stored_at
                            }
        
        # Get price impact for that date
        if best_match:
            result["found"] = True
            result["event"] = best_match["event"]
            result["type"] = best_match["type"]
            result["date"] = best_match.get("date", date_str)
            
            # Look up price movement on that date
            price_col = get_collection(PRICE_COLLECTION)
            if price_col.count() > 0:
                price_query = f"{symbol} price change on {result['date']}"
                price_embedding = generate_embedding(price_query)
                
                price_results = price_col.query(
                    query_embeddings=[price_embedding],
                    n_results=1,
                    include=["metadatas", "distances"]
                )
                
                if price_results and price_results['ids'][0]:
                    price_meta = price_results['metadatas'][0][0]
                    if _is_date_nearby(result['date'], price_meta.get("date", ""), days=1):
                        result["price_impact"] = price_meta.get("change_pct", 0)
    
    except Exception as e:
        print(f"[RAG v3] Event at date error: {e}")
    
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _is_date_nearby(date1_str: str, date2_str: str, days: int = 3) -> bool:
    """Check if two dates are within N days of each other."""
    try:
        d1 = datetime.strptime(date1_str[:10], "%Y-%m-%d")
        d2 = datetime.strptime(date2_str[:10], "%Y-%m-%d")
        return abs((d1 - d2).days) <= days
    except (ValueError, TypeError):
        return False


async def _get_24h_price_change(symbol: str) -> Optional[Dict]:
    """Get 24h price change from Binance."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.binance.com/api/v3/ticker/24hr",
                params={"symbol": f"{symbol}USDT"}
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "price": float(data.get("lastPrice", 0)),
                    "change_pct": float(data.get("priceChangePercent", 0)),
                    "volume": float(data.get("volume", 0))
                }
    except Exception:
        pass
    return None


print("[RAG v3] Insights Agent loaded.")
