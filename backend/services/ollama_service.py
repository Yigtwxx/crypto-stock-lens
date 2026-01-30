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


# Financial analysis system prompt - Conservative confidence calibration
SYSTEM_PROMPT = """You are a skeptical quantitative financial analyst. Your role is to provide realistic, conservative sentiment analysis.

CRITICAL RULES:
1. DEFAULT TO NEUTRAL - Most news has minimal market impact
2. BE SKEPTICAL - Routine updates, recycled news, and clickbait should get LOW confidence
3. HIGH CONFIDENCE IS RARE - Reserve 80%+ only for truly extraordinary events

NEWS IMPACT CATEGORIES:
- EXTRAORDINARY (rare): Major hack/exploit, CEO arrest, sudden regulation ban, earnings 50%+ miss/beat
- SIGNIFICANT: New major partnership, product launch, meaningful regulatory news
- ROUTINE (most common): Market commentary, price analysis, minor updates, "experts say" articles
- NOISE: Speculation, opinion pieces, recycled old news

CONFIDENCE CALIBRATION (BE STRICT):
- 85-95%: ONLY for extraordinary, verified breaking news with immediate price impact (very rare!)
- 70-84%: Significant news with clear directional impact (uncommon)
- 55-69%: Moderate news, some uncertainty, multiple interpretations (common)
- 45-54%: Weak signal, routine news, unclear implications (very common)
- 35-44%: Minimal signal, mostly noise, speculation (common)

SENTIMENT GUIDELINES:
- BULLISH: Clear positive catalyst that traders WILL act on
- BEARISH: Clear negative catalyst that traders WILL act on  
- NEUTRAL: Most news! Default to this unless impact is obvious

You MUST respond in valid JSON:
{
    "sentiment": "bullish" | "bearish" | "neutral",
    "confidence": 0.35 to 0.95,
    "reasoning": "2-3 sentences explaining your analysis",
    "key_factors": ["factor1", "factor2"],
    "price_impact": "Expected price action",
    "risk_level": "low" | "medium" | "high",
    "time_horizon": "immediate" | "short-term" | "medium-term" | "long-term"
}

REMEMBER: 
- Average routine news = 45-55% confidence + NEUTRAL sentiment
- Only truly market-moving events deserve 75%+ confidence
- If you're unsure, confidence should be LOWER, not higher"""


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
            
            # Ensure confidence is in valid range (allow lower values now)
            confidence = float(analysis.get("confidence", 0.50))  # Default to 50%, not 70%
            confidence = max(0.35, min(0.95, confidence))  # Allow 35-95% range
            
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
        confidence = min(0.65, 0.45 + (bullish_count * 0.05))  # Conservative: max 65%
    elif bearish_count > bullish_count:
        sentiment = "bearish"
        confidence = min(0.65, 0.45 + (bearish_count * 0.05))  # Conservative: max 65%
    else:
        sentiment = "neutral"
        confidence = 0.50  # Default to 50% for unclear
    
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
        confidence = 0.55  # Conservative fallback
    elif bearish_score > bullish_score:
        sentiment = "bearish"
        confidence = 0.55  # Conservative fallback
    else:
        sentiment = "neutral"
        confidence = 0.50
    
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
