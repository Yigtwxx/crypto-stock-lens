"""
Oracle Chat Service - Conversational AI for financial questions
Uses Ollama (llama3.1:8b) with extended thinking time for quality responses.
"""
import httpx
import json
from typing import List, Dict, Optional
from datetime import datetime


# Ollama API endpoint
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3.1:8b"

# Extended timeout for thorough responses
CHAT_TIMEOUT = 180.0  # 3 minutes for complex questions

# Financial Oracle system prompt
CHAT_SYSTEM_PROMPT = """Sen Oracle-X, gelişmiş bir finansal yapay zeka asistanısın. Kripto paralar, hisse senetleri, piyasa analizi ve yatırım stratejileri konusunda uzmansın.

GÖREVLER:
1. Kullanıcıların finansal sorularını detaylı ve doğru şekilde yanıtla
2. Teknik analiz, temel analiz ve piyasa trendleri hakkında bilgi ver
3. Risk yönetimi ve yatırım stratejileri öner
4. Güncel piyasa koşullarını değerlendir

YANITLAMA KURALLARI:
1. Her zaman Türkçe yanıt ver
2. Yanıtlarını markdown formatında ver
3. Önemli terimleri **kalın** yap
4. Sayıları ve fiyatları `kod formatında` göster
5. Listeler ve maddeler kullan
6. Bullish/pozitif bilgiler için 🟢, bearish/negatif için 🔴, nötr için 🟡 emoji kullan
7. Uyarıları ve riskleri ⚠️ ile işaretle
8. Önemli noktaları 💡 ile vurgula

ÖRNEK FORMAT:
**Bitcoin (BTC) Analizi**

🟢 **Olumlu Faktörler:**
- Kurumsal alımlar artıyor
- `$100,000` psikolojik direnç kırıldı

🔴 **Risk Faktörleri:**
- RSI aşırı alım bölgesinde
- Kısa vadeli düzeltme olası

💡 **Öneri:** Kademeli alım stratejisi uygulanabilir.

⚠️ **Uyarı:** Bu yatırım tavsiyesi değildir.

---

KAPSAM:
- Kripto: Bitcoin, Ethereum, Solana, ve 100+ altcoin
- Hisse: NASDAQ, NYSE, BIST hisseleri
- Genel: Makroekonomi, Fed kararları, enflasyon, faiz oranları

Detaylı, doğru ve iyi yapılandırılmış yanıtlar ver. Acele etme, kaliteli analiz yap."""


async def chat_with_oracle(
    message: str,
    history: Optional[List[Dict[str, str]]] = None
) -> Dict:
    """
    Send a message to Oracle and get a response.
    Injects real-time market data AND specific technical analysis.
    """
    from services.market_overview_service import fetch_market_overview
    from services.news_service import fetch_all_news
    from services.fear_greed_service import fetch_fear_greed_index
    from services.technical_analysis_service import get_technical_analysis
    import re

    # 1. Fetch General Market Context
    try:
        overview = await fetch_market_overview()
        fg_data = await fetch_fear_greed_index()
        news = await fetch_all_news()
        
        # Format Market Data
        market_context = "📉 **GENEL PİYASA GÖRÜNÜMÜ:**\n"
        market_context += f"📅 Tarih: {datetime.now().strftime('%d %B %Y, %H:%M')}\n"
        market_context += f"• Toplam Piyasa Değeri: ${overview['total_market_cap']:,.0f}\n"
        market_context += f"• BTC Dominansı: %{overview['btc_dominance']:.1f}\n"
        market_context += f"• Korku & Açgözlülük: {fg_data['value']} ({fg_data['value_classification']})\n"

        # Format News Headlines (Top 3)
        market_context += "\n📰 **SON HABERLER:**\n"
        for item in news[:3]:
            # Add time ago
            market_context += f"- {item.title} ({item.source})\n"
        
    except Exception as e:
        print(f"Error fetching general context: {e}")
        market_context = "⚠️ Genel piyasa verileri alınamadı."

    # 2. Detect Specific Symbol & Fetch Technicals
    # Regex to find potential tickers (e.g., BTC, ETH, SOL, AVAX) - 2 to 5 uppercase letters
    potential_symbols = re.findall(r'\b[A-Z]{2,5}\b', message.upper())
    
    # Common words to ignore
    ignored_words = {"THE", "AND", "FOR", "ARE", "BUY", "SELL", "HOW", "WHAT", "WHY", "USD", "USDT"}
    detected_symbol = None
    technical_context = ""
    
    for word in potential_symbols:
        if word in ignored_words: continue
        
        # Try to fetch technicals to validate if it's a crypto
        # We try adding USDT to it
        tech_data = await get_technical_analysis(f"BINANCE:{word}USDT")
        
        if tech_data and "current_price" in tech_data and tech_data["current_price"] > 0:
            detected_symbol = word
            
            # Format Technical Data
            technical_context = f"\n📊 **{word} İÇİN TEKNİK ANALİZ (CANLI):**\n"
            technical_context += f"• Fiyat: ${tech_data.get('current_price'):,.4f}\n"
            technical_context += f"• RSI (14): {tech_data.get('rsi_value'):.1f} ({tech_data.get('rsi_signal')})\n"
            technical_context += f"• Trend: {tech_data.get('trend').upper()}\n"
            technical_context += f"• Destek Seviyeleri: {', '.join(tech_data.get('support_levels', []))}\n"
            technical_context += f"• Direnç Seviyeleri: {', '.join(tech_data.get('resistance_levels', []))}\n"
            technical_context += f"• Hedef Fiyat: {tech_data.get('target_price')}\n"
            
            # Add specific prompt instruction
            market_context += technical_context
            break # Focus on the first valid symbol found
            
    # 3. Build Conversation Context
    messages = []
    
    if history:
        for msg in history[-6:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
    
    # 4. Construct Advanced System Prompt
    final_system_prompt = f"""{CHAT_SYSTEM_PROMPT}

🔍 **CANLI VERİ KAYNAĞI:**
Aşağıdaki veriler şu anda sistemden çekilmiştir. Yanıtında KESİNLİKLE bu verileri kullan.
{market_context}

🧠 **DÜŞÜNME SÜRECİ (CHAIN OF THOUGHT):**
Yanıt vermeden önce adım adım düşün:
1. Kullanıcı ne soruyor? (Genel piyasa mı, özel bir coin mi?)
2. Elimdeki CANLI veriler bu soruyu yanıtlamak için yeterli mi?
3. Eğer teknik analiz verisi varsa (RSI, Destek/Direnç), bunları yorumla. "RSI 70 üzeri, yani aşırı alım var" gibi.
4. Haberler piyasayı nasıl etkiliyor?
5. Sonuç olarak net bir strateji veya yanıt oluştur.

⚠️ **ÖNEMLİ:**
- Asla "bilgim yok" deme, yukarıdaki verileri yorumla.
- Eski tarihli (2021-2022) fiyat tahmini YAPMA. Sadece yukarıdaki canlı fiyatı kullan.
- Finansal tavsiye değildir uyarısını ekle.
"""

    # Build Prompt
    conversation_text = ""
    for msg in messages:
        role_label = "Kullanıcı" if msg["role"] == "user" else "Oracle"
        conversation_text += f"\n{role_label}: {msg['content']}\n"
    
    user_prompt = f"""Geçmiş Konuşma:
{conversation_text}

Kullanıcı: {message}

Yukarıdaki CANLI PİYASA ANALİZİNİ kullanarak, bir finans uzmanı gibi detaylıca yanıtla."""

    try:
        start_time = datetime.now()
        
        async with httpx.AsyncClient(timeout=CHAT_TIMEOUT) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": MODEL_NAME,
                    "prompt": user_prompt,
                    "system": final_system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.4, # Lower for accuracy
                        "top_p": 0.85,
                        "num_predict": 3000, # Allow deep explanations
                        "repeat_penalty": 1.15,
                    }
                }
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "").strip()
                
                if not ai_response:
                    ai_response = "Üzgünüm, yanıt oluşturulamadı."
                
                return {
                    "response": ai_response,
                    "thinking_time": round(elapsed, 1)
                }
            else:
                return {
                    "response": "⚠️ AI servisine ulaşılamıyor.",
                    "thinking_time": 0
                }
                
    except Exception as e:
        return {
            "response": f"🔴 Bir hata oluştu: {str(e)}",
            "thinking_time": 0
        }


async def check_chat_available() -> bool:
    """Check if chat service is available."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
    except (httpx.TimeoutException, httpx.ConnectError):
        return False
