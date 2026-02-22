"""
RAG v4 Service — Reasoning Agent
Faz 3: Gelişmiş Akıl Yürütme — Karşılaştırmalı analiz ve senaryo simülasyonu.

Bu ajan 2 temel görev yapar:
1. Karşılaştırmalı Analiz: İki varlığı teknik ve tarihsel olarak kıyaslar
2. Senaryo Simülasyonu: "Eğer X olursa ne olur?" sorusunu geçmiş verilerle simüle eder
"""
import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from services.rag_v2_service import (
    get_collection, generate_embedding,
    NEWS_COLLECTION, EVENTS_COLLECTION, PRICE_COLLECTION
)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. COMPARATIVE ANALYSIS — "SOL vs AVAX"
# ═══════════════════════════════════════════════════════════════════════════════

async def compare_assets(symbol_a: str, symbol_b: str) -> Dict:
    """
    Compare two crypto assets using historical RAG data and live prices.
    
    Returns comprehensive comparison including:
    - Current prices and 24h changes
    - Historical price patterns from RAG
    - Related events for each
    - News sentiment for each
    - Overall comparison verdict
    """
    result = {
        "symbol_a": symbol_a,
        "symbol_b": symbol_b,
        "comparison": {
            "price_data": {},
            "historical_events": {},
            "news_sentiment": {},
            "price_patterns": {}
        },
        "verdict": "",
        "summary": ""
    }
    
    try:
        # Step 1: Get live price data for both
        price_a = await _get_live_data(symbol_a)
        price_b = await _get_live_data(symbol_b)
        
        result["comparison"]["price_data"] = {
            symbol_a: price_a or {"price": 0, "change_24h": 0, "volume": 0},
            symbol_b: price_b or {"price": 0, "change_24h": 0, "volume": 0}
        }
        
        # Step 2: Get historical events related to each symbol
        for symbol in [symbol_a, symbol_b]:
            query = f"{symbol} major events milestones"
            embedding = generate_embedding(query)
            
            events_col = get_collection(EVENTS_COLLECTION)
            events = []
            if events_col.count() > 0:
                event_results = events_col.query(
                    query_embeddings=[embedding],
                    n_results=min(3, events_col.count()),
                    where={"symbol": symbol} if symbol in ["BTC", "ETH", "SOL"] else None,
                    include=["metadatas", "distances"]
                )
                if event_results and event_results['ids'][0]:
                    for i, doc_id in enumerate(event_results['ids'][0]):
                        meta = event_results['metadatas'][0][i]
                        distance = event_results['distances'][0][i]
                        similarity = 1 / (1 + distance)
                        if similarity > 0.3:
                            events.append({
                                "event": meta.get("event_name", ""),
                                "date": meta.get("date", ""),
                                "type": meta.get("event_type", "")
                            })
            
            result["comparison"]["historical_events"][symbol] = events[:3]
        
        # Step 3: Get news sentiment for each symbol
        for symbol in [symbol_a, symbol_b]:
            query = f"{symbol} recent news sentiment analysis"
            embedding = generate_embedding(query)
            
            news_col = get_collection(NEWS_COLLECTION)
            sentiments = {"bullish": 0, "bearish": 0, "neutral": 0}
            news_count = 0
            
            if news_col.count() > 0:
                news_results = news_col.query(
                    query_embeddings=[embedding],
                    n_results=min(10, news_col.count()),
                    include=["metadatas", "distances"]
                )
                if news_results and news_results['ids'][0]:
                    for i in range(len(news_results['ids'][0])):
                        meta = news_results['metadatas'][0][i]
                        distance = news_results['distances'][0][i]
                        similarity = 1 / (1 + distance)
                        
                        if similarity > 0.3:
                            sent = meta.get("sentiment", "neutral").lower()
                            if sent in sentiments:
                                sentiments[sent] += 1
                                news_count += 1
            
            total = sum(sentiments.values()) or 1
            result["comparison"]["news_sentiment"][symbol] = {
                "bullish_pct": round(sentiments["bullish"] / total * 100),
                "bearish_pct": round(sentiments["bearish"] / total * 100),
                "neutral_pct": round(sentiments["neutral"] / total * 100),
                "news_count": news_count,
                "dominant": max(sentiments, key=sentiments.get)
            }
        
        # Step 4: Get price pattern analysis from RAG
        for symbol in [symbol_a, symbol_b]:
            query = f"{symbol} price trend pattern weekly monthly"
            embedding = generate_embedding(query)
            
            price_col = get_collection(PRICE_COLLECTION)
            patterns = []
            if price_col.count() > 0:
                price_results = price_col.query(
                    query_embeddings=[embedding],
                    n_results=min(5, price_col.count()),
                    where={"symbol": symbol},
                    include=["metadatas", "distances"]
                )
                if price_results and price_results['ids'][0]:
                    for i in range(len(price_results['ids'][0])):
                        meta = price_results['metadatas'][0][i]
                        patterns.append({
                            "date": meta.get("date", ""),
                            "change_pct": meta.get("change_pct", 0),
                            "close": meta.get("close", 0)
                        })
            
            result["comparison"]["price_patterns"][symbol] = patterns[:5]
        
        # Step 5: Generate verdict
        result["verdict"] = _generate_comparison_verdict(result, symbol_a, symbol_b)
        result["summary"] = _generate_comparison_summary(result, symbol_a, symbol_b)
        
    except Exception as e:
        result["summary"] = f"Karşılaştırma hatası: {str(e)}"
        print(f"[RAG v4] Compare assets error: {e}")
    
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SCENARIO SIMULATION — "Eğer Bitcoin ETF reddedilirse ne olur?"
# ═══════════════════════════════════════════════════════════════════════════════

async def simulate_scenario(scenario_query: str, symbol: str = "BTC") -> Dict:
    """
    Simulate a scenario by finding similar historical events and their price impacts.
    
    Args:
        scenario_query: "What if Bitcoin ETF is rejected?" or "Fed faiz artırırsa?"
        symbol: Primary symbol to analyze
    
    Returns:
        {
            "scenario": "Bitcoin ETF reddedilirse",
            "symbol": "BTC",
            "similar_past_events": [...],
            "price_impact_range": {"min": -15, "max": -5, "avg": -8.5},
            "recovery_time_days": 14,
            "confidence": 0.72,
            "simulation_summary": "..."
        }
    """
    result = {
        "scenario": scenario_query,
        "symbol": symbol,
        "similar_past_events": [],
        "price_impact_range": {"min": 0, "max": 0, "avg": 0},
        "recovery_time_days": None,
        "confidence": 0,
        "simulation_summary": ""
    }
    
    try:
        # Step 1: Search for similar historical events
        query_embedding = generate_embedding(scenario_query)
        
        similar_events = []
        
        # Search events collection
        events_col = get_collection(EVENTS_COLLECTION)
        if events_col.count() > 0:
            event_results = events_col.query(
                query_embeddings=[query_embedding],
                n_results=min(5, events_col.count()),
                include=["documents", "metadatas", "distances"]
            )
            
            if event_results and event_results['ids'][0]:
                for i in range(len(event_results['ids'][0])):
                    meta = event_results['metadatas'][0][i]
                    distance = event_results['distances'][0][i]
                    similarity = 1 / (1 + distance)
                    
                    if similarity > 0.3:
                        similar_events.append({
                            "event": meta.get("event_name", ""),
                            "date": meta.get("date", ""),
                            "type": meta.get("event_type", ""),
                            "similarity": round(similarity, 3),
                            "source": "events"
                        })
        
        # Search news collection for similar past scenarios
        news_col = get_collection(NEWS_COLLECTION)
        if news_col.count() > 0:
            news_results = news_col.query(
                query_embeddings=[query_embedding],
                n_results=min(5, news_col.count()),
                include=["documents", "metadatas", "distances"]
            )
            
            if news_results and news_results['ids'][0]:
                for i in range(len(news_results['ids'][0])):
                    meta = news_results['metadatas'][0][i]
                    distance = news_results['distances'][0][i]
                    similarity = 1 / (1 + distance)
                    
                    if similarity > 0.4:
                        similar_events.append({
                            "event": meta.get("title", "")[:100],
                            "date": meta.get("stored_at", "")[:10],
                            "type": meta.get("sentiment", "neutral"),
                            "price_change": meta.get("price_change", None),
                            "similarity": round(similarity, 3),
                            "source": "news"
                        })
        
        similar_events.sort(key=lambda x: x["similarity"], reverse=True)
        result["similar_past_events"] = similar_events[:7]
        
        # Step 2: Analyze price patterns around similar events
        price_impacts = []
        price_col = get_collection(PRICE_COLLECTION)
        
        for event in similar_events[:5]:
            # If news has direct price_change, use it
            if event.get("price_change") is not None:
                price_impacts.append(event["price_change"])
                continue
            
            # Otherwise search for price data near event date
            if event.get("date") and price_col.count() > 0:
                price_query = f"{symbol} price on {event['date']}"
                price_embedding = generate_embedding(price_query)
                
                price_results = price_col.query(
                    query_embeddings=[price_embedding],
                    n_results=3,
                    include=["metadatas", "distances"]
                )
                
                if price_results and price_results['ids'][0]:
                    for j in range(len(price_results['ids'][0])):
                        p_meta = price_results['metadatas'][0][j]
                        p_date = p_meta.get("date", "")
                        change = p_meta.get("change_pct", 0)
                        
                        if p_date and event.get("date"):
                            try:
                                d1 = datetime.strptime(p_date[:10], "%Y-%m-%d")
                                d2 = datetime.strptime(event["date"][:10], "%Y-%m-%d")
                                if abs((d1 - d2).days) <= 5:
                                    price_impacts.append(change)
                                    break
                            except (ValueError, TypeError):
                                continue
        
        # Step 3: Calculate simulation results
        if price_impacts:
            result["price_impact_range"] = {
                "min": round(min(price_impacts), 2),
                "max": round(max(price_impacts), 2),
                "avg": round(sum(price_impacts) / len(price_impacts), 2)
            }
            
            # Estimate recovery: larger drops take longer
            avg_impact = abs(result["price_impact_range"]["avg"])
            if avg_impact > 10:
                result["recovery_time_days"] = 30
            elif avg_impact > 5:
                result["recovery_time_days"] = 14
            elif avg_impact > 2:
                result["recovery_time_days"] = 7
            else:
                result["recovery_time_days"] = 3
        
        # Step 4: Calculate confidence
        if similar_events:
            avg_similarity = sum(e["similarity"] for e in similar_events[:5]) / min(5, len(similar_events))
            data_richness = min(1.0, len(price_impacts) / 3)
            result["confidence"] = round(avg_similarity * 0.6 + data_richness * 0.4, 2)
        
        # Step 5: Generate simulation summary
        result["simulation_summary"] = _generate_scenario_summary(result)
        
    except Exception as e:
        result["simulation_summary"] = f"Simülasyon hatası: {str(e)}"
        print(f"[RAG v4] Scenario simulation error: {e}")
    
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

async def _get_live_data(symbol: str) -> Optional[Dict]:
    """Get live price data from Binance."""
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
                    "change_24h": float(data.get("priceChangePercent", 0)),
                    "volume": float(data.get("quoteVolume", 0)),
                    "high_24h": float(data.get("highPrice", 0)),
                    "low_24h": float(data.get("lowPrice", 0))
                }
    except Exception:
        pass
    return None


def _generate_comparison_verdict(result: Dict, sym_a: str, sym_b: str) -> str:
    """Generate a comparative verdict between two assets."""
    price_data = result["comparison"]["price_data"]
    sentiment = result["comparison"]["news_sentiment"]
    
    a_change = price_data.get(sym_a, {}).get("change_24h", 0)
    b_change = price_data.get(sym_b, {}).get("change_24h", 0)
    
    a_sentiment = sentiment.get(sym_a, {}).get("dominant", "neutral")
    b_sentiment = sentiment.get(sym_b, {}).get("dominant", "neutral")
    
    # Simple scoring
    a_score = 0
    b_score = 0
    
    if a_change > b_change:
        a_score += 1
    else:
        b_score += 1
    
    sentiment_order = {"bullish": 2, "neutral": 1, "bearish": 0}
    a_score += sentiment_order.get(a_sentiment, 1)
    b_score += sentiment_order.get(b_sentiment, 1)
    
    if a_score > b_score:
        return f"{sym_a} şu an daha güçlü görünüyor (Momentum: {a_change:+.1f}%, Sentiment: {a_sentiment})"
    elif b_score > a_score:
        return f"{sym_b} şu an daha güçlü görünüyor (Momentum: {b_change:+.1f}%, Sentiment: {b_sentiment})"
    else:
        return f"{sym_a} ve {sym_b} birbirine yakın performans gösteriyor."


def _generate_comparison_summary(result: Dict, sym_a: str, sym_b: str) -> str:
    """Generate human-readable comparison summary."""
    price_data = result["comparison"]["price_data"]
    
    a_price = price_data.get(sym_a, {}).get("price", 0)
    b_price = price_data.get(sym_b, {}).get("price", 0)
    a_change = price_data.get(sym_a, {}).get("change_24h", 0)
    b_change = price_data.get(sym_b, {}).get("change_24h", 0)
    
    lines = [
        f"📊 {sym_a} vs {sym_b} Karşılaştırması",
        f"",
        f"💰 Fiyat: {sym_a}=${a_price:,.2f} ({a_change:+.1f}%) | {sym_b}=${b_price:,.2f} ({b_change:+.1f}%)",
        f"",
        result["verdict"]
    ]
    
    return "\n".join(lines)


def _generate_scenario_summary(result: Dict) -> str:
    """Generate simulation summary text."""
    symbol = result["symbol"]
    impact = result["price_impact_range"]
    events_count = len(result["similar_past_events"])
    confidence = int(result["confidence"] * 100)
    
    if events_count == 0:
        return f"'{result['scenario']}' senaryosu için geçmişte benzer olay bulunamadı."
    
    avg_impact = impact["avg"]
    direction = "yükseliş" if avg_impact > 0 else "düşüş"
    
    lines = [
        f"🔮 Senaryo Simülasyonu: {result['scenario']}",
        f"",
        f"📊 Geçmişte benzer {events_count} olay bulundu:",
        f"   • Tahmini etki: {impact['min']:+.1f}% ile {impact['max']:+.1f}% arası",
        f"   • Ortalama etki: {avg_impact:+.1f}% ({direction})",
    ]
    
    if result["recovery_time_days"]:
        lines.append(f"   • Tahmini toparlanma: ~{result['recovery_time_days']} gün")
    
    lines.append(f"   • Güven skoru: %{confidence}")
    
    return "\n".join(lines)


print("[RAG v4] Reasoning Agent loaded.")
