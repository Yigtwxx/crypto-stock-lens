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


# Financial analysis system prompt
SYSTEM_PROMPT = """You are an expert financial analyst AI specializing in cryptocurrency and stock market analysis. 
Your task is to analyze news headlines and provide accurate sentiment analysis with trading insights.

You MUST respond in valid JSON format with the following structure:
{
    "sentiment": "bullish" | "bearish" | "neutral",
    "confidence": 0.0 to 1.0,
    "reasoning": "Brief explanation of your analysis",
    "key_factors": ["factor1", "factor2", "factor3"],
    "price_impact": "short explanation of expected price movement",
    "risk_level": "low" | "medium" | "high",
    "time_horizon": "short-term" | "medium-term" | "long-term"
}

Be objective and base your analysis on:
1. The actual content of the news
2. Historical market patterns for similar news
3. Technical and fundamental implications
4. Market sentiment indicators

Always provide a confidence score between 0.65 and 0.95 - avoid extremes unless absolutely certain."""


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
    asset_type: str
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
    # Construct the analysis prompt
    user_prompt = f"""Analyze the following {asset_type} news for {symbol}:

HEADLINE: {title}

SUMMARY: {summary}

Provide your sentiment analysis in the exact JSON format specified. Focus on accuracy and actionable insights."""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": MODEL_NAME,
                    "prompt": user_prompt,
                    "system": SYSTEM_PROMPT,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower = more consistent/accurate
                        "top_p": 0.9,
                        "num_predict": 500,
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
                "raw_response": raw_response[:500]  # Keep for debugging
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
