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
CHAT_SYSTEM_PROMPT = """You are Oracle-X, an advanced financial AI assistant.

🎯 **YOUR MISSION:**
Answer user questions using the **LIVE DATA (<context>)** provided to you.

⚠️ **STRICT RULES:**
1. **ONLY** use the data provided below. Do not guess.
2. **<thinking>** inside this tag, analyze the data first, then write your response.
3. **NEVER SHOW XML OR THINKING TAGS IN YOUR FINAL RESPONSE.**
4. Use a sincere, helpful, and professional tone. Do not sound robotic.
5. If the user says "Hello", briefly greet them and provide a market summary.
6. **CITATION STYLE:** When mentioning news, **DO NOT** write "according to Investing.com". Instead, use a small link format like this: `[Source](url)`. Example: *"Bitcoin rallied today due to ETF inflows [Source](https://...)."*

📋 **DATA SOURCES:**
- Market and price data (Crypto OR Stocks)
- Technical analysis signals
- News and web results
- Historical events (RAG)

🗣️ **RESPONSE FORMAT:**
- Use Markdown (bold, lists, etc.)
- Short and concise paragraphs
- Avoid unnecessary technical jargon
- **ALWAYS ANSWER IN ENGLISH.**
- **Format news sources as small links:** `[Source](url)`
"""


async def detect_symbols(message: str) -> List[str]:
    """
    Detect potential trading symbols from user message.
    Returns list of potential symbols (uppercase, 2-5 characters).
    """
    potential = re.findall(r'\b[A-Z]{2,5}\b', message.upper())
    return [s for s in potential if s not in IGNORED_WORDS]


async def flatten_stock_data_for_context(stock_data: Dict) -> Dict:
    """Format stock data to match the expected 'technicals' structure for the context builder."""
    if not stock_data:
        return {}
    
    symbol = stock_data.get("symbol")
    return {
        symbol: {
            "current_price": stock_data.get("price", 0),
            "rsi_value": 0, # Not available for stocks yet
            "rsi_signal": "N/A",
            "trend": "N/A",
            "support_levels": [f"${stock_data.get('low_24h', 0):.2f}"],
            "resistance_levels": [f"${stock_data.get('high_24h', 0):.2f}"],
            "target_price": f"${stock_data.get('high_24h', 0):.2f}", # Basic target
            "market_cap": stock_data.get("market_cap", 0),
            "volume": stock_data.get("volume_24h", 0)
        }
    }


async def fetch_all_market_data(detected_symbols: List[str], context_type: str = "CRYPTO") -> Dict[str, any]:
    """
    Fetch comprehensive market data from all available sources based on Context Type.
    """
    from services.market_overview_service import fetch_market_overview
    from services.news_service import fetch_all_news
    from services.fear_greed_service import fetch_fear_greed_index
    from services.technical_analysis_service import get_technical_analysis
    from services.stock_market_service import get_stock_context_data, fetch_nasdaq_overview
    
    data = {
        "overview": None,
        "fear_greed": None,
        "news": [],
        "technicals": {},
        "timestamp": datetime.now().strftime('%d %B %Y, %H:%M'),
        "context_type": context_type
    }
    
    # --- PROCESSS STOCK CONTEXT ---
    if context_type == "STOCK":
        try:
            # 1. Get Stock Overview (NASDAQ)
            data["overview"] = await fetch_nasdaq_overview()
            
            # 2. Get specific symbol data if detected
            if detected_symbols:
                symbol = detected_symbols[0]
                stock_details = await get_stock_context_data(symbol)
                if stock_details:
                    data["technicals"] = await flatten_stock_data_for_context(stock_details)
                    # Use stock specific fear & greed from the details if available
                    if "fear_greed" in stock_details:
                        data["fear_greed"] = stock_details["fear_greed"]
            
            # 3. If no specific symbol fear/greed, fetch general stock fear/greed
            if not data["fear_greed"] and data["overview"]:
                data["fear_greed"] = data["overview"].get("fear_greed")

        except Exception as e:
            print(f"Stock data fetch error: {e}")

    # --- PROCESS CRYPTO CONTEXT ---
    else:
        try:
            # 1. Get Crypto Overview
            data["overview"] = await fetch_market_overview()
        except Exception as e:
            print(f"Market overview fetch error: {e}")
        
        try:
            data["fear_greed"] = await fetch_fear_greed_index()
        except Exception as e:
            print(f"Fear/Greed fetch error: {e}")
        
        # Ensure BTC is always analyzed for context in Crypto mode
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

    # --- COMMON DATA (NEWS) ---
    try:
        # We might want separate stock news in the future, but for now generic news is fine
        # Or filter news based on keywords if the news service supports it
        news = await fetch_all_news()
        data["news"] = news[:5] if news else []
    except Exception as e:
        print(f"News fetch error: {e}")
    
    return data


async def build_context_string(market_data: Dict, web_context: str, message: str, rag_context: str = "") -> str:
    """
    Build comprehensive context string using XML tags.
    Adapts based on market_data['context_type'].
    """
    context_type = market_data.get("context_type", "CRYPTO")
    parts = ["<context>"]
    
    # Current date/time
    parts.append(f"  <current_time>{market_data['timestamp']}</current_time>")
    
    # Market Overview
    if market_data["overview"]:
        ov = market_data["overview"]
        parts.append("  <market_overview>")
        if context_type == "STOCK":
             parts.append(f"    <market_status>{ov.get('market_status', {}).get('message', 'N/A')}</market_status>")
             parts.append(f"    <total_volume>${ov.get('total_volume_24h', 0):,.0f}</total_volume>")
             parts.append(f"    <active_stocks>{ov.get('active_cryptocurrencies', 0)} (Tracked)</active_stocks>") # Reused field name key
        else:
            parts.append(f"    <total_cap>${ov.get('total_market_cap', 0):,.0f}</total_cap>")
            parts.append(f"    <btc_dominance>%{ov.get('btc_dominance', 0):.1f}</btc_dominance>")
            parts.append(f"    <volume_24h>${ov.get('total_24h_volume', 0):,.0f}</volume_24h>")
        parts.append("  </market_overview>")
    
    # Fear & Greed
    if market_data["fear_greed"]:
        fg = market_data["fear_greed"]
        parts.append("  <sentiment>")
        parts.append(f"    <fear_greed_index>{fg.get('value', 'N/A')}</fear_greed_index>")
        parts.append(f"    <status>{fg.get('classification', 'N/A') or fg.get('value_classification', 'N/A')}</status>")
        parts.append("  </sentiment>")
    
    # Technical/Asset Analysis
    if market_data["technicals"]:
        parts.append("  <analysis_data>")
        for symbol, tech in market_data["technicals"].items():
            parts.append(f"    <asset symbol='{symbol}'>")
            parts.append(f"      <price>${tech.get('current_price', 0):,.2f}</price>")
            
            if context_type == "STOCK":
                 # Simplified stock data
                parts.append(f"      <market_cap>${tech.get('market_cap', 0):,.0f}</market_cap>")
                parts.append(f"      <day_high>{tech.get('target_price', 'N/A')}</day_high>") # Using target price field for high
                parts.append(f"      <day_low>{tech.get('support_levels', ['N/A'])[0]}</day_low>")
            else:
                # Full Crypto Technicals
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
        parts.append("  </analysis_data>")
    
    # Recent News
    if market_data["news"]:
        parts.append("  <news>")
        for item in market_data["news"][:3]:
            parts.append("    <item>")
            parts.append(f"      <title>{item.title}</title>")
            parts.append(f"      <source>{item.source}</source>")
            parts.append(f"      <url>{item.url}</url>")
            parts.append("    </item>")
        parts.append("  </news>")
    
    # RAG History
    if rag_context:
        parts.append(f"  <rag_history>\n{rag_context}\n  </rag_history>")
    
    # Web Search
    if web_context:
        parts.append(f"  <web_search>\n{web_context}\n  </web_search>")
    
    # RAG v3/v4 Advanced Context
    if advanced_rag_context := market_data.get("advanced_rag"):
        parts.append(f"  <advanced_agents>\n{advanced_rag_context}\n  </advanced_agents>")
    
    parts.append("</context>")
    return "\n".join(parts)


async def chat_with_oracle(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    style: str = "detailed"
) -> Dict:
    """
    Enhanced Oracle chat with web search and multi-source analysis.
    """
    from services.web_search_service import get_enhanced_context
    from services.stock_market_service import is_stock_symbol
    
    start_time = datetime.now()
    
    # Step 1: Detect symbols
    detected_symbols = await detect_symbols(message)
    primary_symbol = detected_symbols[0] if detected_symbols else None
    
    # Step 1.5: Determine Context (Stock vs Crypto)
    context_type = "CRYPTO" # Default
    if primary_symbol and is_stock_symbol(primary_symbol):
        context_type = "STOCK"
    elif any(kw in message.lower() for kw in ["nasdaq", "stock", "hisse", "borsa", "sp500", "dow jones"]):
         context_type = "STOCK"

    # Step 2: Fetch market data based on context
    market_data = await fetch_all_market_data(detected_symbols, context_type)
    market_data["advanced_rag"] = ""
    
    # Step 2.5: Trigger RAG v3/v4 Advanced Agents based on intent
    advanced_context = []
    
    # 2.5a: Comparative Analysis (v4) - e.g. "SOL vs ETH"
    if " vs " in message.lower() or "karşılaştır" in message.lower():
        if len(detected_symbols) >= 2:
            try:
                from services.rag_v4_service import compare_assets
                cmp_result = await compare_assets(detected_symbols[0], detected_symbols[1])
                if cmp_result.get("summary"):
                    advanced_context.append(f"KARŞILAŞTIRMA AJANI (v4):\n{cmp_result['summary']}")
            except Exception as e:
                print(f"RAG v4 Compare error: {e}")
                
    # 2.5b: Scenario Simulation (v4) - e.g. "Eğer faiz düşerse BTC ne olur?"
    scenario_kws = ["eğer", "olursa", "senaryo", "düşerse", "çıkarsa", "neler olur", "farz edelim"]
    if any(kw in message.lower() for kw in scenario_kws):
        try:
            from services.rag_v4_service import simulate_scenario
            sim_result = await simulate_scenario(message, primary_symbol or "BTC")
            if sim_result.get("simulation_summary"):
                advanced_context.append(f"SİMÜLASYON AJANI (v4):\n{sim_result['simulation_summary']}")
        except Exception as e:
            print(f"RAG v4 Simulate error: {e}")
            
    # 2.5c: Price Movement Insights (v3) - If primary symbol exists and no other agent fired
    if primary_symbol and not advanced_context:
        try:
            from services.rag_v3_service import get_price_movement_reason
            reason_result = await get_price_movement_reason(primary_symbol)
            if reason_result.get("summary"):
                advanced_context.append(f"İÇGÖRÜ AJANI (v3):\n{reason_result['summary']}")
        except Exception as e:
            print(f"RAG v3 Insight error: {e}")
            
    if advanced_context:
        market_data["advanced_rag"] = "\n\n".join(advanced_context)
    
    # Step 3: Get web search context
    web_context = ""
    try:
        web_context = await get_enhanced_context(message, primary_symbol)
    except Exception as e:
        print(f"Web search error: {e}")
    
    # Step 4: Get RAG 2.0 historical context (always active for richer responses)
    rag_context = ""
    try:
        from services.rag_v2_service import get_rag_context_v2
        rag_context = get_rag_context_v2(
            query=message,
            symbol=primary_symbol,
            context_type="all"
        )
    except Exception as e:
        print(f"RAG 2.0 context error: {e}")
    
    # Step 5: Build comprehensive context
    full_context = await build_context_string(market_data, web_context, message, rag_context)
    
    # Step 6: Build conversation history
    conversation_text = ""
    if history:
        for msg in history[-4:]:  # Last 4 messages for context
            role = "Kullanıcı" if msg.get("role") == "user" else "Oracle"
            conversation_text += f"\n{role}: {msg.get('content', '')}\n"
    
    # Step 7: Construct final system prompt
    # Dynamic additional instruction based on context
    context_instruction = ""
    if context_type == "STOCK":
         context_instruction = "\n7. **CONTEXT:** This is a STOCK MARKET query. Do NOT mention Bitcoin or Crypto unless explicitly asked. Focus on the stock data provided."
    else:
         context_instruction = "\n7. **CONTEXT:** This is a CRYPTO MARKET query. Always mention Bitcoin (BTC) price as a benchmark."

    style_instruction = ""
    if style == "concise":
        style_instruction = "\n8. **CONCISE MODE:** Keep your answer under 150 words. Be direct and to the point. No fluff."
    else:
        style_instruction = "\n8. **DETAILED MODE:** Provide deep analysis, multiple perspectives, and thorough explanation."

    final_system_prompt = f"""{CHAT_SYSTEM_PROMPT}{context_instruction}{style_instruction}

<context>
{full_context}
</context>
"""

    # Step 8: Build user prompt
    user_prompt = f"""Geçmiş Konuşma:
{conversation_text}

Kullanıcı Sorusu: {message}

📌 GÖREV:
1. `<context>` içindeki verileri analiz et.
2. `<thinking>` etiketi aç ve adım adım plan yap.
3. Kullanıcıya net yanıt ver.

Yanıtın:"""

    # Step 9: Call Ollama
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
                    sources_used.append("Piyasa Verileri" if context_type == "STOCK" else "Teknik Analiz")
                if market_data["news"]:
                    sources_used.append("Haberler")
                if web_context:
                    sources_used.append("Web Arama")
                if market_data["fear_greed"]:
                    sources_used.append("Sentiment")
                if rag_context:
                    sources_used.append("Tarihsel Analiz (RAG)")
                if market_data.get("advanced_rag"):
                    sources_used.append("Gelişmiş AI Ajanları")
                
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
