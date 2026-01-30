"""
Ollama AI Service - Real sentiment analysis using local LLM
Uses llama3.1:8b for maximum accuracy in financial news analysis.
"""
import httpx
import json
from typing import Optional
from datetime import datetime
import hashlib


# Ollama API endpoint (default local)
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3.1:8b"


# Financial analysis system prompt - Enhanced for accuracy
SYSTEM_PROMPT = """You are a senior quantitative financial analyst with 15+ years experience in cryptocurrency and equity markets.
Your role is to provide institutional-grade sentiment analysis based on news content.

CRITICAL ANALYSIS RULES:
1. NEVER guess - base analysis ONLY on the actual news content provided
2. Consider market psychology: how will traders react to this news?
3. Evaluate the SOURCE credibility (major outlets vs unknown sources)
4. Assess the NEWS IMPACT MAGNITUDE (breaking news vs routine update)
5. Consider TIMING: earnings season, market hours, macro events

SENTIMENT CRITERIA:
- BULLISH: News clearly indicates positive price catalyst (partnerships, adoption, earnings beat, regulatory approval)
- BEARISH: News indicates negative catalyst (hacks, regulatory crackdown, earnings miss, executive departure)
- NEUTRAL: Mixed signals, routine updates, or unclear market implications

CONFIDENCE GUIDELINES:
- 0.90-0.95: Breaking news with clear, immediate market impact
- 0.80-0.89: Strong directional signal with some uncertainty
- 0.70-0.79: Moderate signal, multiple interpretations possible
- 0.60-0.69: Weak signal, high uncertainty, conflicting factors

You MUST respond in valid JSON format:
{
    "sentiment": "bullish" | "bearish" | "neutral",
    "confidence": 0.60 to 0.95,
    "reasoning": "2-3 sentence analysis explaining WHY this news affects the asset price",
    "key_factors": ["factor1", "factor2", "factor3"],
    "price_impact": "Expected short-term price action description",
    "risk_level": "low" | "medium" | "high",
    "time_horizon": "immediate" | "short-term" | "medium-term" | "long-term",
    "trading_signal": "strong_buy" | "buy" | "hold" | "sell" | "strong_sell",
    "technical_signals": {
        "rsi_signal": "Overbought" | "Oversold" | "Neutral" | "Bullish Divergence" | "Bearish Divergence",
        "support_levels": ["level1", "level2"],
        "resistance_levels": ["level1", "level2"],
        "target_price": "Expected price target range based on current price"
    }
}

TECHNICAL ANALYSIS RULES:
- Support levels MUST be BELOW the current price (typically 2-10% below)
- Resistance levels MUST be ABOVE the current price (typically 2-10% above)
- Target price should be a realistic short-term range based on sentiment and volatility
- Always use the CURRENT PRICE provided as the reference point
- Format price levels with appropriate precision (e.g., $1.75, $1.82 for low-priced assets)

IMPORTANT: Your analysis will be used for real trading decisions. Be precise, objective, and accountable."""


async def check_ollama_health() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


async def analyze_news_with_ollama(
    title: str,
    summary: str,
    symbol: str,
    asset_type: str,
    current_price: float = None
) -> dict:
    """
    Analyze a news item using Ollama LLM.
    
    Args:
        title: News headline
        summary: News summary/body
        symbol: Trading symbol (e.g., BINANCE:BTCUSDT)
        asset_type: "crypto" or "stock"
    
    Returns:
        Analysis result dictionary
    """
    # Extract clean symbol name
    clean_symbol = symbol.split(':')[-1] if ':' in symbol else symbol
    asset_name = "cryptocurrency" if asset_type == "crypto" else "stock"
    
    # Construct detailed analysis prompt with current price context
    price_context = ""
    if current_price and current_price > 0:
        price_context = f"\nCURRENT PRICE: ${current_price:.4f}\n\nIMPORTANT: When calculating technical levels, use ${current_price:.4f} as the reference:\n- Support levels should be 2-8% BELOW current price (e.g., ${current_price * 0.95:.4f}, ${current_price * 0.92:.4f})\n- Resistance levels should be 2-8% ABOVE current price (e.g., ${current_price * 1.05:.4f}, ${current_price * 1.08:.4f})\n- Target price should be a realistic range near current price"
    
    user_prompt = f"""ASSET: {clean_symbol} ({asset_name})
SYMBOL: {symbol}
{price_context}

NEWS HEADLINE:
"{title}"

NEWS CONTENT:
{summary}

---
TASK: Analyze this news and determine its impact on {clean_symbol} price.

Consider:
1. Is this news MATERIAL to the price? Will traders care?
2. What is the DIRECTION of impact (bullish/bearish/neutral)?
3. How CONFIDENT are you based on the clarity of the news?
4. What is the expected TIME HORIZON for price impact?
5. For technical_signals, calculate support/resistance relative to the CURRENT PRICE provided above.

Respond with ONLY the JSON object, no additional text."""

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": MODEL_NAME,
                    "prompt": user_prompt,
                    "system": SYSTEM_PROMPT,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Very low for consistency
                        "top_p": 0.85,
                        "top_k": 40,
                        "num_predict": 600,
                        "repeat_penalty": 1.1,
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                raw_response = result.get("response", "")
                
                # Parse JSON from response
                analysis = parse_llm_response(raw_response)
                return analysis
            else:
                print(f"Ollama API error: {response.status_code}")
                return get_fallback_analysis(title, symbol)
                
    except Exception as e:
        print(f"Ollama analysis error: {e}")
        return get_fallback_analysis(title, symbol)


def parse_llm_response(raw_response: str) -> dict:
    """Parse the LLM response and extract JSON."""
    try:
        # Try to find JSON in the response
        start_idx = raw_response.find('{')
        end_idx = raw_response.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = raw_response[start_idx:end_idx]
            analysis = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["sentiment", "confidence", "reasoning"]
            for field in required_fields:
                if field not in analysis:
                    raise ValueError(f"Missing required field: {field}")
            
            # Normalize sentiment
            sentiment = analysis["sentiment"].lower()
            if sentiment not in ["bullish", "bearish", "neutral"]:
                sentiment = "neutral"
            
            # Ensure confidence is in valid range
            confidence = float(analysis.get("confidence", 0.7))
            confidence = max(0.5, min(0.95, confidence))
            
            return {
                "sentiment": sentiment,
                "confidence": round(confidence, 2),
                "reasoning": analysis.get("reasoning", "Analysis completed."),
                "key_factors": analysis.get("key_factors", []),
                "price_impact": analysis.get("price_impact", ""),
                "risk_level": analysis.get("risk_level", "medium"),
                "time_horizon": analysis.get("time_horizon", "short-term"),
                "trading_signal": analysis.get("trading_signal", "hold"),
                "technical_signals": analysis.get("technical_signals", None),
            }
    except (json.JSONDecodeError, ValueError) as e:
        print(f"JSON parse error: {e}")
    
    # If parsing fails, extract what we can
    return extract_analysis_from_text(raw_response)


def extract_analysis_from_text(text: str) -> dict:
    """Extract analysis from non-JSON text response."""
    text_lower = text.lower()
    
    # Determine sentiment from text
    bullish_keywords = ["bullish", "positive", "growth", "surge", "rally", "upward", "gain", "rise"]
    bearish_keywords = ["bearish", "negative", "decline", "crash", "fall", "drop", "loss", "down"]
    
    bullish_count = sum(1 for kw in bullish_keywords if kw in text_lower)
    bearish_count = sum(1 for kw in bearish_keywords if kw in text_lower)
    
    if bullish_count > bearish_count:
        sentiment = "bullish"
        confidence = min(0.85, 0.6 + (bullish_count * 0.05))
    elif bearish_count > bullish_count:
        sentiment = "bearish"
        confidence = min(0.85, 0.6 + (bearish_count * 0.05))
    else:
        sentiment = "neutral"
        confidence = 0.65
    
    return {
        "sentiment": sentiment,
        "confidence": round(confidence, 2),
        "reasoning": text[:300] if len(text) > 300 else text,
        "key_factors": [],
        "price_impact": "",
        "risk_level": "medium",
        "time_horizon": "short-term"
    }


def get_fallback_analysis(title: str, symbol: str) -> dict:
    """Return a fallback analysis when Ollama is unavailable."""
    # Simple keyword-based fallback
    title_lower = title.lower()
    
    bullish_words = ["surge", "rally", "grow", "gain", "rise", "high", "record", "breakthrough", "success"]
    bearish_words = ["crash", "fall", "drop", "decline", "loss", "low", "fail", "concern", "risk"]
    
    bullish_score = sum(1 for w in bullish_words if w in title_lower)
    bearish_score = sum(1 for w in bearish_words if w in title_lower)
    
    if bullish_score > bearish_score:
        sentiment = "bullish"
        confidence = 0.70
    elif bearish_score > bullish_score:
        sentiment = "bearish"
        confidence = 0.70
    else:
        sentiment = "neutral"
        confidence = 0.65
    
    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "reasoning": f"Fallback analysis for '{title}'. Ollama was unavailable.",
        "key_factors": ["Keyword-based analysis"],
        "price_impact": "Unable to determine - using fallback",
        "risk_level": "medium",
        "time_horizon": "short-term"
    }


def generate_prediction_hash(news_id: str, sentiment: str, confidence: float) -> str:
    """Generate a unique hash for the prediction."""
    data = f"{news_id}:{sentiment}:{confidence}:{datetime.now().isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()
