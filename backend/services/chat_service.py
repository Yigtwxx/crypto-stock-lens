"""
Oracle Chat Service v2 - Enhanced AI Financial Assistant
Uses Ollama (llama3.1:8b) with web search and multi-source data analysis.
"""
import httpx
import re
from typing import List, Dict, Optional
from datetime import datetime


# Ollama API endpoint
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3.1:8b"

# Extended timeout for thorough responses (5 minutes for complex analysis)
CHAT_TIMEOUT = 300.0

# Common words to ignore when detecting symbols
IGNORED_WORDS = {
    "THE", "AND", "FOR", "ARE", "BUY", "SELL", "HOW", "WHAT", "WHY", "USD", "USDT",
    "WHEN", "WHERE", "CAN", "WILL", "SHOULD", "COULD", "WOULD", "HAVE", "HAS",
    "DOES", "DID", "NOT", "YES", "THIS", "THAT", "WHICH", "THERE", "THEIR",
    "PRICE", "MARKET", "TODAY", "NOW", "GOOD", "BAD", "HIGH", "LOW"
}

# Enhanced Financial Oracle system prompt with strict data binding
CHAT_SYSTEM_PROMPT = """Sen Oracle-X, gelişmiş bir finansal yapay zeka asistanısın.

🎯 **ANA GÖREV:**
Kullanıcılara CANLI VERİYE dayalı, GÜNCEL ve DOĞRU finansal bilgi sağla.

⚠️ **KRİTİK KURALLAR:**
1. **ASLA ESKİ VERİ KULLANMA** - Sadece aşağıda sağlanan CANLI verileri kullan
2. **TARİH KONTROLÜ** - Bugünün tarihi sistem tarafından verildi, bunu referans al
3. **FİYAT DOĞRULUĞU** - Fiyatları SADECE sağlanan verilerden al, tahmin etme
4. **WEB ARAMALARI** - Web arama sonuçları en güncel bilgiyi içerir, bunları öncelikle kullan

📋 **YANITLAMA FORMATI:**
- Markdown kullan
- Önemli sayıları `kod formatında` göster
- 🟢 Pozitif, 🔴 Negatif, 🟡 Nötr
- ⚠️ Uyarılar, 💡 Öneriler
- Türkçe yanıt ver

🧠 **ANALİZ SÜRECİ:**
Yanıt vermeden önce şu adımları izle:
1. Kullanıcı ne soruyor? (Fiyat mı, analiz mi, haber mi?)
2. CANLI verilerden hangileri bu soruyu yanıtlar?
3. Web arama sonuçları ne diyor?
4. Teknik göstergeler (RSI, destek/direnç) ne gösteriyor?
5. Tüm verileri sentezle ve net bir yanıt oluştur.

📊 **VERİ ÖNCELİĞİ:**
1. Sistem tarafından sağlanan CANLI fiyatlar (en güvenilir)
2. Web arama sonuçları (güncel haberler için)
3. Teknik analiz verileri
4. Genel piyasa göstergeleri

⚠️ **UYARILAR:**
- "Bilgim yok" deme, verileri yorumla
- Yatırım tavsiyesi olmadığını belirt
- Belirsizlik varsa açıkça belirt"""


async def detect_symbols(message: str) -> List[str]:
    """
    Detect potential trading symbols from user message.
    Returns list of potential symbols (uppercase, 2-5 characters).
    """
    potential = re.findall(r'\b[A-Z]{2,5}\b', message.upper())
    return [s for s in potential if s not in IGNORED_WORDS]


async def fetch_all_market_data(detected_symbols: List[str]) -> Dict[str, any]:
    """
    Fetch comprehensive market data from all available sources.
    """
    from services.market_overview_service import fetch_market_overview
    from services.news_service import fetch_all_news
    from services.fear_greed_service import fetch_fear_greed_index
    from services.technical_analysis_service import get_technical_analysis
    
    data = {
        "overview": None,
        "fear_greed": None,
        "news": [],
        "technicals": {},
        "timestamp": datetime.now().strftime('%d %B %Y, %H:%M')
    }
    
    try:
        # Fetch general market data
        data["overview"] = await fetch_market_overview()
    except Exception as e:
        print(f"Market overview fetch error: {e}")
    
    try:
        data["fear_greed"] = await fetch_fear_greed_index()
    except Exception as e:
        print(f"Fear/Greed fetch error: {e}")
    
    try:
        news = await fetch_all_news()
        data["news"] = news[:5] if news else []
    except Exception as e:
        print(f"News fetch error: {e}")
    
    # Fetch technicals for detected symbols
    for symbol in detected_symbols[:3]:  # Limit to 3 symbols
        try:
            tech = await get_technical_analysis(f"BINANCE:{symbol}USDT")
            if tech and tech.get("current_price", 0) > 0:
                data["technicals"][symbol] = tech
        except Exception as e:
            print(f"Technical analysis error for {symbol}: {e}")
    
    return data


async def build_context_string(market_data: Dict, web_context: str, message: str) -> str:
    """
    Build comprehensive context string for the AI.
    """
    parts = []
    
    # Current date/time
    parts.append(f"📅 **GÜNCEL TARİH/SAAT:** {market_data['timestamp']}")
    parts.append("")
    
    # Market Overview
    if market_data["overview"]:
        ov = market_data["overview"]
        parts.append("📉 **GENEL PİYASA:**")
        parts.append(f"• Toplam Piyasa Değeri: ${ov.get('total_market_cap', 0):,.0f}")
        parts.append(f"• BTC Dominansı: %{ov.get('btc_dominance', 0):.1f}")
        parts.append(f"• 24s Hacim: ${ov.get('total_24h_volume', 0):,.0f}")
        parts.append("")
    
    # Fear & Greed
    if market_data["fear_greed"]:
        fg = market_data["fear_greed"]
        parts.append(f"😨 **Korku & Açgözlülük İndeksi:** {fg.get('value', 'N/A')} ({fg.get('value_classification', 'N/A')})")
        parts.append("")
    
    # Technical Analysis for each detected symbol
    if market_data["technicals"]:
        for symbol, tech in market_data["technicals"].items():
            parts.append(f"📊 **{symbol} TEKNİK ANALİZ (CANLI):**")
            parts.append(f"• Fiyat: ${tech.get('current_price', 0):,.4f}")
            parts.append(f"• RSI (14): {tech.get('rsi_value', 0):.1f} ({tech.get('rsi_signal', 'N/A')})")
            parts.append(f"• Trend: {tech.get('trend', 'N/A').upper()}")
            
            supports = tech.get('support_levels', [])
            resistances = tech.get('resistance_levels', [])
            
            if supports:
                parts.append(f"• Destek Seviyeleri: {', '.join(supports[:3])}")
            if resistances:
                parts.append(f"• Direnç Seviyeleri: {', '.join(resistances[:3])}")
            
            target = tech.get('target_price', '')
            if target:
                parts.append(f"• Hedef Fiyat: {target}")
            parts.append("")
    
    # Recent News
    if market_data["news"]:
        parts.append("📰 **SON HABERLER:**")
        for i, item in enumerate(market_data["news"][:3], 1):
            parts.append(f"{i}. {item.title} ({item.source})")
        parts.append("")
    
    # Web Search Results
    if web_context:
        parts.append(web_context)
        parts.append("")
    
    return "\n".join(parts)


async def chat_with_oracle(
    message: str,
    history: Optional[List[Dict[str, str]]] = None
) -> Dict:
    """
    Enhanced Oracle chat with web search and multi-source analysis.
    """
    from services.web_search_service import get_enhanced_context
    
    start_time = datetime.now()
    
    # Step 1: Detect symbols in user message
    detected_symbols = await detect_symbols(message)
    primary_symbol = detected_symbols[0] if detected_symbols else None
    
    # Step 2: Fetch all market data (concurrent)
    market_data = await fetch_all_market_data(detected_symbols)
    
    # Step 3: Get web search context
    web_context = ""
    try:
        web_context = await get_enhanced_context(message, primary_symbol)
    except Exception as e:
        print(f"Web search error: {e}")
    
    # Step 4: Build comprehensive context
    full_context = await build_context_string(market_data, web_context, message)
    
    # Step 5: Build conversation history
    conversation_text = ""
    if history:
        for msg in history[-4:]:  # Last 4 messages for context
            role = "Kullanıcı" if msg.get("role") == "user" else "Oracle"
            conversation_text += f"\n{role}: {msg.get('content', '')}\n"
    
    # Step 6: Construct final system prompt
    final_system_prompt = f"""{CHAT_SYSTEM_PROMPT}

═══════════════════════════════════════════════════
🔴 CANLI VERİ KAYNAĞI - SADECE BUNLARI KULLAN 🔴
═══════════════════════════════════════════════════

{full_context}

═══════════════════════════════════════════════════
"""

    # Step 7: Build user prompt
    user_prompt = f"""Geçmiş Konuşma:
{conversation_text}

Kullanıcı Sorusu: {message}

📌 GÖREV:
1. Yukarıdaki CANLI VERİLERİ analiz et
2. Web arama sonuçlarını değerlendir
3. Teknik göstergeleri yorumla
4. Net, doğru ve güncel bir yanıt ver

Yanıtını şimdi oluştur:"""

    # Step 8: Call Ollama
    try:
        async with httpx.AsyncClient(timeout=CHAT_TIMEOUT) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": MODEL_NAME,
                    "prompt": user_prompt,
                    "system": final_system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,    # Lower for accuracy
                        "top_p": 0.9,
                        "num_predict": 4000,   # Allow detailed responses
                        "repeat_penalty": 1.1,
                        "num_ctx": 8192,       # Larger context window
                    }
                }
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "").strip()
                
                if not ai_response:
                    ai_response = "Üzgünüm, yanıt oluşturulamadı. Lütfen tekrar deneyin."
                
                # Add data sources indicator
                sources_used = []
                if market_data["technicals"]:
                    sources_used.append("Teknik Analiz")
                if market_data["news"]:
                    sources_used.append("Haberler")
                if web_context:
                    sources_used.append("Web Arama")
                if market_data["fear_greed"]:
                    sources_used.append("Sentiment")
                
                return {
                    "response": ai_response,
                    "thinking_time": round(elapsed, 1),
                    "sources": sources_used,
                    "detected_symbol": primary_symbol
                }
            else:
                return {
                    "response": "⚠️ AI servisine ulaşılamıyor. Lütfen Ollama'nın çalıştığından emin olun.",
                    "thinking_time": 0,
                    "sources": [],
                    "detected_symbol": None
                }
                
    except httpx.TimeoutException:
        return {
            "response": "⏱️ Yanıt süresi aşıldı. Soru çok karmaşık olabilir, daha basit bir şekilde sormayı deneyin.",
            "thinking_time": 0,
            "sources": [],
            "detected_symbol": None
        }
    except Exception as e:
        return {
            "response": f"🔴 Bir hata oluştu: {str(e)}",
            "thinking_time": 0,
            "sources": [],
            "detected_symbol": None
        }


async def check_chat_available() -> bool:
    """Check if chat service is available."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
    except (httpx.TimeoutException, httpx.ConnectError):
        return False
