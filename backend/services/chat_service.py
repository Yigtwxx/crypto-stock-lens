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
# Enhanced Financial Oracle system prompt with XML structure and CoT
CHAT_SYSTEM_PROMPT = """Sen Oracle-X, gelişmiş bir finansal yapay zeka asistanısın.

🎯 **GÖREVİN:**
Sana sağlanan **CANLI VERİLERİ (<context>)** kullanarak kullanıcı sorularına yanıt ver.

⚠️ **KATİ KURALLAR:**
1. **SADECE** aşağıdaki verileri kullan. Tahmin yapma.
2. **<thinking>** etiketi içinde önce verileri analiz et, sonra yanıtı yaz.
3. **YANITINDA XML VEYA THINKING ETİKETLERİ ASLA GÖRÜNMEMELİ.**
4. Samimi, yardımsever ve profesyonel bir üslup kullan. Robot gibi konuşma.
5. Kullanıcı "Merhaba" derse kısaca selam ver ve piyasa özetini sun.
6. **HER YANITINDA MUTLAKA** Bitcoin'in (BTC) güncel fiyatını belirt (örneğin: "Bitcoin şu an $X seviyesinde..."). Konu başka bir coin olsa bile BTC'yi piyasa göstergesi olarak ekle.

📋 **VERİ KAYNAKLARI:**
- Market ve fiyat verileri
- Teknik analiz sinyalleri
- Haberler ve web sonuçları
- Geçmiş olaylar (RAG)

🗣️ **YANIT FORMATI:**
- Markdown kullan (kalın, liste vb.)
- Kısa ve öz paragraflar
- Gereksiz teknik terimlerden kaçın
"""


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
    
    # Ensure BTC is always analyzed for context
    if "BTC" not in detected_symbols:
        detected_symbols.insert(0, "BTC")
    
    # Fetch technicals for detected symbols
    for symbol in detected_symbols[:3]:  # Limit to 3 symbols
        try:
            tech = await get_technical_analysis(f"BINANCE:{symbol}USDT")
            if tech and tech.get("current_price", 0) > 0:
                data["technicals"][symbol] = tech
        except Exception as e:
            print(f"Technical analysis error for {symbol}: {e}")
    
    return data


async def build_context_string(market_data: Dict, web_context: str, message: str, rag_context: str = "") -> str:
    """
    Build comprehensive context string using XML tags.
    """
    parts = ["<context>"]
    
    # Current date/time
    parts.append(f"  <current_time>{market_data['timestamp']}</current_time>")
    
    # Market Overview
    if market_data["overview"]:
        ov = market_data["overview"]
        parts.append("  <market_overview>")
        parts.append(f"    <total_cap>${ov.get('total_market_cap', 0):,.0f}</total_cap>")
        parts.append(f"    <btc_dominance>%{ov.get('btc_dominance', 0):.1f}</btc_dominance>")
        parts.append(f"    <volume_24h>${ov.get('total_24h_volume', 0):,.0f}</volume_24h>")
        parts.append("  </market_overview>")
    
    # Fear & Greed
    if market_data["fear_greed"]:
        fg = market_data["fear_greed"]
        parts.append("  <sentiment>")
        parts.append(f"    <fear_greed_index>{fg.get('value', 'N/A')}</fear_greed_index>")
        parts.append(f"    <status>{fg.get('value_classification', 'N/A')}</status>")
        parts.append("  </sentiment>")
    
    # Technical Analysis
    if market_data["technicals"]:
        parts.append("  <technical_analysis>")
        for symbol, tech in market_data["technicals"].items():
            parts.append(f"    <asset symbol='{symbol}'>")
            parts.append(f"      <price>${tech.get('current_price', 0):,.4f}</price>")
            parts.append(f"      <rsi>{tech.get('rsi_value', 0):.1f} ({tech.get('rsi_signal', 'N/A')})</rsi>")
            parts.append(f"      <trend>{tech.get('trend', 'N/A').upper()}</trend>")
            
            supports = tech.get('support_levels', [])
            resistances = tech.get('resistance_levels', [])
            
            if supports:
                parts.append(f"      <supports>{', '.join(supports[:3])}</supports>")
            if resistances:
                parts.append(f"      <resistances>{', '.join(resistances[:3])}</resistances>")
            
            target = tech.get('target_price', '')
            if target:
                parts.append(f"      <target_price>{target}</target_price>")
            parts.append("    </asset>")
        parts.append("  </technical_analysis>")
    
    # Recent News
    if market_data["news"]:
        parts.append("  <news>")
        for item in market_data["news"][:3]:
            parts.append("    <item>")
            parts.append(f"      <title>{item.title}</title>")
            parts.append(f"      <source>{item.source}</source>")
            parts.append("    </item>")
        parts.append("  </news>")
    
    # RAG History
    if rag_context:
        parts.append(f"  <rag_history>\n{rag_context}\n  </rag_history>")
    
    # Web Search
    if web_context:
        parts.append(f"  <web_search>\n{web_context}\n  </web_search>")
    
    parts.append("</context>")
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
    
    # Step 4b: Get RAG 2.0 historical context (for temporal queries)
    rag_context = ""
    # Check if query is about historical events or patterns
    historical_keywords = ["geçen", "önceki", "tarihte", "halving", "ath", "dip", "crash", 
                          "geçmiş", "nasıl davran", "ne oldu", "benzer", "daha önce"]
    is_historical_query = any(kw in message.lower() for kw in historical_keywords)
    
    if is_historical_query or primary_symbol:
        try:
            from services.rag_v2_service import get_rag_context_v2
            rag_context = get_rag_context_v2(
                query=message,
                symbol=primary_symbol,
                context_type="all"
            )
        except Exception as e:
            print(f"RAG 2.0 context error: {e}")
    
    # Step 5: Build comprehensive context (now includes RAG)
    full_context = await build_context_string(market_data, web_context, message, rag_context)
    
    # Step 5: Build conversation history
    conversation_text = ""
    if history:
        for msg in history[-4:]:  # Last 4 messages for context
            role = "Kullanıcı" if msg.get("role") == "user" else "Oracle"
            conversation_text += f"\n{role}: {msg.get('content', '')}\n"
    
    # Step 6: Construct final system prompt
    final_system_prompt = f"""{CHAT_SYSTEM_PROMPT}

<context>
{full_context}
</context>
"""

    # Step 7: Build user prompt
    user_prompt = f"""Geçmiş Konuşma:
{conversation_text}

Kullanıcı Sorusu: {message}

📌 GÖREV:
1. `<context>` içindeki verileri analiz et.
2. `<thinking>` etiketi aç ve adım adım plan yap.
3. Kullanıcıya net yanıt ver.

Yanıtın:"""

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
                        "temperature": 0.3,    # Lower slightly for more focused answers
                        "top_p": 0.9,
                        "num_predict": 4096,
                        "repeat_penalty": 1.1,
                        "num_ctx": 8192,
                    }
                }
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                raw_response = result.get("response", "").strip()
                
                # Extract clean response by removing <thinking> blocks
                import re
                clean_response = re.sub(r'<thinking>.*?</thinking>', '', raw_response, flags=re.DOTALL).strip()
                
                # If everything was in thinking block (edge case), use raw or fallback
                if not clean_response:
                     # Try to find content after thinking block if regex failed or it's just text
                    if "</thinking>" in raw_response:
                        clean_response = raw_response.split("</thinking>")[-1].strip()
                    else:
                        clean_response = raw_response

                if not clean_response:
                    clean_response = "Üzgünüm, yanıt oluşturulamadı. Lütfen tekrar deneyin."
                
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
                    "response": clean_response,
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
