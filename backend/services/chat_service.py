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
    
    Args:
        message: User's question
        history: Previous conversation history [{role: "user"|"assistant", content: "..."}]
    
    Returns:
        {response: string, thinking_time: float}
    """
    # Build conversation context
    messages = []
    
    # Add history if provided
    if history:
        for msg in history[-6:]:  # Keep last 6 messages for context
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
    
    # Add current message
    messages.append({
        "role": "user",
        "content": message
    })
    
    # Build the full prompt with conversation context
    conversation_text = ""
    for msg in messages:
        role_label = "Kullanıcı" if msg["role"] == "user" else "Oracle"
        conversation_text += f"\n{role_label}: {msg['content']}\n"
    
    user_prompt = f"""Önceki konuşma:
{conversation_text}

Şimdi kullanıcının son sorusuna detaylı ve doğru bir yanıt ver. Markdown formatı kullan, emojiler ekle, önemli noktaları vurgula."""

    try:
        start_time = datetime.now()
        
        async with httpx.AsyncClient(timeout=CHAT_TIMEOUT) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": MODEL_NAME,
                    "prompt": user_prompt,
                    "system": CHAT_SYSTEM_PROMPT,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 50,
                        "num_predict": 2000,  # Allow longer responses
                        "repeat_penalty": 1.1,
                    }
                }
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "").strip()
                
                # Clean up response if needed
                if not ai_response:
                    ai_response = "Üzgünüm, bu soruya şu anda yanıt veremiyorum. Lütfen tekrar deneyin."
                
                return {
                    "response": ai_response,
                    "thinking_time": round(elapsed, 1)
                }
            else:
                return {
                    "response": "⚠️ AI servisi şu anda yanıt veremiyor. Lütfen daha sonra tekrar deneyin.",
                    "thinking_time": 0
                }
                
    except httpx.ConnectError:
        return {
            "response": "🔴 **Bağlantı Hatası**\n\nOllama servisi çalışmıyor. Lütfen `ollama serve` komutu ile başlatın.",
            "thinking_time": 0
        }
    except httpx.TimeoutException:
        return {
            "response": "⚠️ Yanıt süresi aşıldı. Sorunuz çok karmaşık olabilir, lütfen daha basit bir soru sorun.",
            "thinking_time": CHAT_TIMEOUT
        }
    except Exception as e:
        return {
            "response": f"🔴 **Hata:** {str(e)}",
            "thinking_time": 0
        }


async def check_chat_available() -> bool:
    """Check if chat service is available."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
    except:
        return False
