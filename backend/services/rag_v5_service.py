"""
RAG v5 Service — Proactive Agent
Faz 4: Proaktif Asistan — Kullanıcı sormadan bilgi sunar.

Bu ajan 2 temel görev yapar:
1. Sabah Briffingi: Gece olan olayları, önemli haberleri ve bugünkü takvimi derler
2. Anomali Tespiti: Fiyat hareketi ile haber akışı arasındaki uyumsuzlukları tespit eder
"""
import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from services.rag_v2_service import (
    get_collection, generate_embedding,
    NEWS_COLLECTION, EVENTS_COLLECTION, PRICE_COLLECTION
)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. DAILY BRIEF — Sabah Briffingi
# ═══════════════════════════════════════════════════════════════════════════════

async def generate_daily_brief(symbols: List[str] = None) -> Dict:
    """
    Generate a comprehensive daily briefing.
    
    Covers:
    - Overnight price movements for watchlist symbols
    - Most important recent news from RAG
    - Any upcoming/recent events from events DB
    - Market sentiment summary
    
    Returns:
        {
            "date": "2025-02-21",
            "greeting": "Günaydın! İşte bugünkü piyasa özeti...",
            "market_snapshot": {...},
            "overnight_movers": [...],
            "top_news": [...],
            "upcoming_events": [...],
            "sentiment_summary": {...},
            "brief_text": "Full formatted brief"
        }
    """
    if symbols is None:
        symbols = ["BTC", "ETH", "SOL", "XRP", "BNB"]
    
    today = datetime.now()
    result = {
        "date": today.strftime("%Y-%m-%d"),
        "greeting": "",
        "market_snapshot": {},
        "overnight_movers": [],
        "top_news": [],
        "upcoming_events": [],
        "sentiment_summary": {},
        "brief_text": ""
    }
    
    try:
        # Step 1: Market Snapshot — Get current prices for key assets
        async with httpx.AsyncClient(timeout=15.0) as client:
            for symbol in symbols[:8]:
                try:
                    resp = await client.get(
                        "https://api.binance.com/api/v3/ticker/24hr",
                        params={"symbol": f"{symbol}USDT"}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        change = float(data.get("priceChangePercent", 0))
                        result["market_snapshot"][symbol] = {
                            "price": float(data.get("lastPrice", 0)),
                            "change_24h": change,
                            "volume": float(data.get("quoteVolume", 0))
                        }
                        
                        # Track big movers (>3% change)
                        if abs(change) > 3:
                            direction = "📈" if change > 0 else "📉"
                            result["overnight_movers"].append({
                                "symbol": symbol,
                                "change_pct": change,
                                "direction": direction,
                                "price": float(data.get("lastPrice", 0))
                            })
                except Exception:
                    continue
        
        # Sort movers by absolute change
        result["overnight_movers"].sort(key=lambda x: abs(x["change_pct"]), reverse=True)
        
        # Step 2: Top Recent News from RAG
        news_col = get_collection(NEWS_COLLECTION)
        if news_col.count() > 0:
            # Query for today's most relevant news
            query = "important crypto market news today breaking"
            query_embedding = generate_embedding(query)
            
            news_results = news_col.query(
                query_embeddings=[query_embedding],
                n_results=min(5, news_col.count()),
                include=["metadatas", "distances"]
            )
            
            if news_results and news_results['ids'][0]:
                for i in range(len(news_results['ids'][0])):
                    meta = news_results['metadatas'][0][i]
                    distance = news_results['distances'][0][i]
                    similarity = 1 / (1 + distance)
                    
                    result["top_news"].append({
                        "title": meta.get("title", "")[:120],
                        "sentiment": meta.get("sentiment", "neutral"),
                        "date": meta.get("stored_at", "")[:10],
                        "relevance": round(similarity, 3)
                    })
        
        # Step 3: Upcoming/Recent Events
        events_col = get_collection(EVENTS_COLLECTION)
        if events_col.count() > 0:
            query = f"upcoming event {today.strftime('%Y-%m')}"
            query_embedding = generate_embedding(query)
            
            event_results = events_col.query(
                query_embeddings=[query_embedding],
                n_results=min(3, events_col.count()),
                include=["metadatas", "distances"]
            )
            
            if event_results and event_results['ids'][0]:
                for i in range(len(event_results['ids'][0])):
                    meta = event_results['metadatas'][0][i]
                    result["upcoming_events"].append({
                        "event": meta.get("event_name", ""),
                        "date": meta.get("date", ""),
                        "type": meta.get("event_type", "")
                    })
        
        # Step 4: Sentiment Summary
        bullish_count = sum(1 for n in result["top_news"] if n.get("sentiment") == "bullish")
        bearish_count = sum(1 for n in result["top_news"] if n.get("sentiment") == "bearish")
        total_news = len(result["top_news"]) or 1
        
        if bullish_count > bearish_count:
            mood = "İyimser"
            emoji = "🟢"
        elif bearish_count > bullish_count:
            mood = "Temkinli"
            emoji = "🔴"
        else:
            mood = "Nötr"
            emoji = "🟡"
        
        result["sentiment_summary"] = {
            "mood": mood,
            "emoji": emoji,
            "bullish_pct": round(bullish_count / total_news * 100),
            "bearish_pct": round(bearish_count / total_news * 100)
        }
        
        # Step 5: Generate formatted brief
        result["greeting"] = _generate_greeting(today)
        result["brief_text"] = _format_daily_brief(result)
        
    except Exception as e:
        result["brief_text"] = f"Brifing oluşturulurken hata: {str(e)}"
        print(f"[RAG v5] Daily brief error: {e}")
    
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ANOMALY DETECTION — Fiyat-Haber Uyumsuzluk Tespiti
# ═══════════════════════════════════════════════════════════════════════════════

async def detect_anomalies(symbols: List[str] = None) -> Dict:
    """
    Detect anomalies: price movements that don't align with news sentiment.
    
    Examples:
    - Price rallying but all news is bearish → potential manipulation
    - Price crashing but no negative news found → possible whale activity
    - Sudden volume spike with no corresponding news → suspicious activity
    
    Returns:
        {
            "anomalies": [
                {
                    "symbol": "BTC",
                    "type": "price_news_divergence",
                    "severity": "high",
                    "description": "Fiyat yükseliyor ama olumsuz haberler var",
                    "price_direction": "up",
                    "news_sentiment": "bearish",
                    "confidence": 0.78
                }
            ],
            "checked_symbols": ["BTC", "ETH", ...],
            "anomaly_count": 2,
            "summary": "..."
        }
    """
    if symbols is None:
        symbols = ["BTC", "ETH", "SOL", "XRP", "BNB", "ADA", "DOGE", "AVAX"]
    
    result = {
        "anomalies": [],
        "checked_symbols": symbols,
        "anomaly_count": 0,
        "summary": ""
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            for symbol in symbols:
                anomaly = await _check_symbol_anomaly(client, symbol)
                if anomaly:
                    result["anomalies"].append(anomaly)
        
        result["anomaly_count"] = len(result["anomalies"])
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        result["anomalies"].sort(key=lambda x: severity_order.get(x.get("severity", "low"), 3))
        
        # Generate summary
        if result["anomalies"]:
            alerts = []
            for a in result["anomalies"][:3]:
                alerts.append(f"⚠️ {a['symbol']}: {a['description']}")
            result["summary"] = "\n".join(alerts)
        else:
            result["summary"] = "✅ Anomali tespit edilmedi — tüm fiyat hareketleri haber akışıyla uyumlu."
        
    except Exception as e:
        result["summary"] = f"Anomali analizi hatası: {str(e)}"
        print(f"[RAG v5] Anomaly detection error: {e}")
    
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

async def _check_symbol_anomaly(client: httpx.AsyncClient, symbol: str) -> Optional[Dict]:
    """Check a single symbol for price-news divergence anomaly."""
    try:
        # Get 24h price change
        resp = await client.get(
            "https://api.binance.com/api/v3/ticker/24hr",
            params={"symbol": f"{symbol}USDT"}
        )
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        price_change = float(data.get("priceChangePercent", 0))
        volume = float(data.get("quoteVolume", 0))
        
        # Only flag significant moves (>3%)
        if abs(price_change) < 3:
            return None
        
        price_direction = "up" if price_change > 0 else "down"
        
        # Search RAG for recent news about this symbol
        query = f"{symbol} recent news"
        query_embedding = generate_embedding(query)
        
        news_col = get_collection(NEWS_COLLECTION)
        if news_col.count() == 0:
            # No news at all but big price move → anomaly
            if abs(price_change) > 5:
                return {
                    "symbol": symbol,
                    "type": "no_news_coverage",
                    "severity": "medium",
                    "description": f"Fiyat {price_change:+.1f}% hareket etti ama RAG'da ilgili haber yok",
                    "price_direction": price_direction,
                    "price_change": price_change,
                    "news_sentiment": "none",
                    "confidence": 0.6
                }
            return None
        
        news_results = news_col.query(
            query_embeddings=[query_embedding],
            n_results=min(5, news_col.count()),
            include=["metadatas", "distances"]
        )
        
        # Analyze news sentiment
        sentiments = {"bullish": 0, "bearish": 0, "neutral": 0}
        relevant_count = 0
        
        if news_results and news_results['ids'][0]:
            for i in range(len(news_results['ids'][0])):
                meta = news_results['metadatas'][0][i]
                distance = news_results['distances'][0][i]
                similarity = 1 / (1 + distance)
                
                if similarity > 0.35:
                    sent = meta.get("sentiment", "neutral").lower()
                    if sent in sentiments:
                        sentiments[sent] += 1
                        relevant_count += 1
        
        if relevant_count == 0:
            if abs(price_change) > 5:
                return {
                    "symbol": symbol,
                    "type": "no_news_coverage",
                    "severity": "medium",
                    "description": f"Fiyat {price_change:+.1f}% hareket etti ama ilgili haber bulunamadı",
                    "price_direction": price_direction,
                    "price_change": price_change,
                    "news_sentiment": "none",
                    "confidence": 0.5
                }
            return None
        
        # Determine dominant news sentiment
        dominant_sentiment = max(sentiments, key=sentiments.get)
        
        # Check for divergence
        is_divergent = False
        divergence_desc = ""
        
        if price_direction == "up" and dominant_sentiment == "bearish":
            is_divergent = True
            divergence_desc = f"Fiyat yükseliyor ({price_change:+.1f}%) ama haberler olumsuz — Manipülasyon riski?"
        elif price_direction == "down" and dominant_sentiment == "bullish":
            is_divergent = True
            divergence_desc = f"Fiyat düşüyor ({price_change:+.1f}%) ama haberler olumlu — Balina satışı olabilir?"
        
        if is_divergent:
            severity = "critical" if abs(price_change) > 10 else "high" if abs(price_change) > 5 else "medium"
            confidence = min(0.95, 0.5 + (sentiments[dominant_sentiment] / relevant_count) * 0.3 + (abs(price_change) / 20) * 0.2)
            
            return {
                "symbol": symbol,
                "type": "price_news_divergence",
                "severity": severity,
                "description": divergence_desc,
                "price_direction": price_direction,
                "price_change": price_change,
                "news_sentiment": dominant_sentiment,
                "news_count": relevant_count,
                "confidence": round(confidence, 2)
            }
    
    except Exception as e:
        print(f"[RAG v5] Anomaly check error for {symbol}: {e}")
    
    return None


def _generate_greeting(now: datetime) -> str:
    """Generate time-appropriate greeting."""
    hour = now.hour
    if hour < 12:
        return "☀️ Günaydın! İşte bugünkü piyasa briffinginiz:"
    elif hour < 18:
        return "🌤️ İyi günler! İşte güncel piyasa briffinginiz:"
    else:
        return "🌙 İyi akşamlar! İşte piyasa briffinginiz:"


def _format_daily_brief(result: Dict) -> str:
    """Format the daily brief into readable text."""
    lines = [result["greeting"], ""]
    
    # Market Snapshot
    if result["market_snapshot"]:
        lines.append("📊 **Piyasa Anlık Görünümü:**")
        for symbol, data in list(result["market_snapshot"].items())[:5]:
            emoji = "🟢" if data["change_24h"] > 0 else "🔴" if data["change_24h"] < 0 else "⚪"
            lines.append(f"  {emoji} {symbol}: ${data['price']:,.2f} ({data['change_24h']:+.1f}%)")
        lines.append("")
    
    # Big Movers
    if result["overnight_movers"]:
        lines.append("🚀 **Büyük Hareketler (>3%):**")
        for mover in result["overnight_movers"][:3]:
            lines.append(f"  {mover['direction']} {mover['symbol']}: {mover['change_pct']:+.1f}%")
        lines.append("")
    
    # Top News
    if result["top_news"]:
        lines.append("📰 **Öne Çıkan Haberler:**")
        for news in result["top_news"][:3]:
            sent_emoji = "🟢" if news["sentiment"] == "bullish" else "🔴" if news["sentiment"] == "bearish" else "⚪"
            lines.append(f"  {sent_emoji} {news['title']}")
        lines.append("")
    
    # Upcoming Events
    if result["upcoming_events"]:
        lines.append("📅 **Yakın Olaylar:**")
        for event in result["upcoming_events"][:3]:
            lines.append(f"  • {event['event']} ({event['date']})")
        lines.append("")
    
    # Sentiment
    sentiment = result.get("sentiment_summary", {})
    if sentiment:
        lines.append(f"🎯 **Genel Sentiment:** {sentiment.get('emoji', '🟡')} {sentiment.get('mood', 'Nötr')}")
    
    return "\n".join(lines)


print("[RAG v5] Proactive Agent loaded.")
