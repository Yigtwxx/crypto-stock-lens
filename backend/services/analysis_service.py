
import logging
import json
import os
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any
from services.ollama_service import generate_completion
from services.news_service import fetch_all_news
from services.market_overview_service import fetch_market_overview
from services.fear_greed_service import fetch_fear_greed_index

logger = logging.getLogger(__name__)

REPORTS_FILE = "data/analysis_reports.json"
NOTES_FILE = "data/user_notes.json"

# ═══════════════════════════════════════════════════════════════════════════════
# DATA PERSISTENCE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _load_json(filepath: str, default: Any) -> Any:
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default

def _save_json(filepath: str, data: Any) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

# ═══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

async def generate_market_report(timeframe: str) -> str:
    """
    Generate a comprehensive market report (Daily, Weekly, Monthly) using aggregated data and AI.
    Enhanced version with Chain of Thought prompting for higher quality analysis.
    """
    # 1. Aggregate Data
    try:
        news_items = await fetch_all_news()
        market_data = await fetch_market_overview()
        fear_greed = await fetch_fear_greed_index()
    except Exception as e:
        logger.error(f"Error fetching data for report: {e}")
        return "Failed to generate report due to data fetching error."

    # Filter news based on timeframe
    limit = 30 if timeframe == 'daily' else 60 if timeframe == 'weekly' else 100
    recent_news = news_items[:limit]
    
    # Separate crypto and stock news for better analysis
    crypto_news = [n for n in recent_news if n.asset_type == "crypto"][:15]
    stock_news = [n for n in recent_news if n.asset_type == "stock"][:15]
    
    crypto_headlines = "\n".join([f"• {n.title}" for n in crypto_news]) or "No recent crypto news"
    stock_headlines = "\n".join([f"• {n.title}" for n in stock_news]) or "No recent stock news"
    
    # Get top 10 coins with more detail
    coins = market_data.get('coins', [])[:10]
    top_coins_data = "\n".join([
        f"{i+1}. {c['symbol']}: ${c['price']:,.2f} ({'+' if c['change_24h'] >= 0 else ''}{c['change_24h']:.2f}%)"
        for i, c in enumerate(coins)
    ]) if coins else "Market data unavailable"
    
    # Find top gainers and losers
    sorted_by_change = sorted(market_data.get('coins', []), key=lambda x: x.get('change_24h', 0), reverse=True)
    top_gainers = sorted_by_change[:3]
    top_losers = sorted_by_change[-3:]
    
    gainers_str = ", ".join([f"{c['symbol']} (+{c['change_24h']:.1f}%)" for c in top_gainers]) if top_gainers else "N/A"
    losers_str = ", ".join([f"{c['symbol']} ({c['change_24h']:.1f}%)" for c in top_losers]) if top_losers else "N/A"
    
    # Calculate total market metrics
    total_market_cap = market_data.get('total_market_cap', 0)
    btc_dominance = market_data.get('btc_dominance', 0)
    eth_dominance = market_data.get('eth_dominance', 0)
    
    prompt = f"""
═══════════════════════════════════════════════════════════════
📊 MARKET ANALYSIS REQUEST - {timeframe.upper()} REPORT
📅 Date: {datetime.now().strftime('%B %d, %Y')}
═══════════════════════════════════════════════════════════════

▸ GLOBAL MARKET METRICS:
  • Total Market Cap: ${total_market_cap:,.0f}
  • BTC Dominance: {btc_dominance:.1f}%
  • ETH Dominance: {eth_dominance:.1f}%
  • Fear & Greed Index: {fear_greed.get('value', 'N/A')} ({fear_greed.get('classification', 'N/A')})

▸ TOP 10 CRYPTOCURRENCIES:
{top_coins_data}

▸ BIGGEST MOVERS:
  🟢 Top Gainers: {gainers_str}
  🔴 Top Losers: {losers_str}

▸ CRYPTO NEWS HEADLINES:
{crypto_headlines}

▸ STOCK/TRADITIONAL MARKET NEWS:
{stock_headlines}

═══════════════════════════════════════════════════════════════
📝 INSTRUCTIONS FOR ANALYSIS:
═══════════════════════════════════════════════════════════════

Write a comprehensive {timeframe} financial market intelligence report.

**CHAIN OF THOUGHT PROCESS:**
1. First, analyze the Fear & Greed Index - what does it indicate about market psychology?
2. Review the top gainers/losers - what themes emerge?
3. Identify the 2-3 MOST IMPORTANT news stories and explain WHY they matter
4. Connect the data points to form a coherent market narrative
5. Provide actionable outlook for the next {timeframe}

**FORMAT (Use Markdown):**

## 📈 Executive Summary
[3-4 sentences capturing the overall market tone and key takeaway]

## 🔥 Market Highlights
[Bullet points of the most significant moves with context]

## 📰 Key News Analysis
[Deep dive into 2-3 important news stories. Explain implications.]

## 🎯 Sector Breakdown
[Brief analysis of: Bitcoin, Major Altcoins, DeFi, Traditional Markets]

## 🔮 Outlook & Watchlist
[What to watch for. Key levels. Risk factors.]

**STYLE:**
- Professional, analytical tone
- Use data to support every claim
- Avoid generic phrases like "markets are volatile"
- Be specific with prices and percentages
- Write as a Senior Analyst at a top investment firm
- Do NOT mention you are an AI
"""
    
    system_prompt = """You are a Senior Market Analyst at a top-tier global investment research firm. 
You write institutional-grade market intelligence reports that hedge funds and asset managers rely on.
Your analysis is:
- Data-driven: Every claim is backed by specific numbers
- Insightful: You connect dots others miss
- Actionable: You provide clear takeaways
- Professional: Authoritative yet accessible tone

Write in a hybrid style mixing Turkish market terminology with English financial terms where appropriate."""
    
    # Use higher token limit for detailed reports (user said time is not an issue)
    report_content = await generate_completion(prompt, system_prompt, temperature=0.25, max_tokens=3000)
    
    if not report_content:
        return "AI generation failed. Please try again."
        
    # Save Report
    reports = _load_json(REPORTS_FILE, {})
    reports[timeframe] = {
        "content": report_content,
        "timestamp": datetime.now().isoformat()
    }
    _save_json(REPORTS_FILE, reports)
    
    return report_content

async def get_report(timeframe: str) -> Optional[Dict]:
    """Get stored report or generate a new one if old."""
    reports = _load_json(REPORTS_FILE, {})
    report = reports.get(timeframe)
    
    # Check freshness (simple check: same day for daily)
    if report:
        last_gen = datetime.fromisoformat(report["timestamp"])
        now = datetime.now()
        
        needs_refresh = False
        if timeframe == 'daily' and (now - last_gen).days >= 1:
            needs_refresh = True
        elif timeframe == 'weekly' and (now - last_gen).days >= 7:
            needs_refresh = True
        elif timeframe == 'monthly' and (now - last_gen).days >= 30:
            needs_refresh = True
            
        if not needs_refresh:
            return report
            
    # Generate new if missing or stale
    content = await generate_market_report(timeframe)
    return {
        "content": content,
        "timestamp": datetime.now().isoformat()
    }

# ═══════════════════════════════════════════════════════════════════════════════
# NOTES MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def get_user_notes() -> List[Dict]:
    return _load_json(NOTES_FILE, [])

def add_user_note(title: str, content: str) -> List[Dict]:
    notes = get_user_notes()
    new_note = {
        "id": str(int(datetime.now().timestamp())),
        "title": title,
        "content": content,
        "date": datetime.now().isoformat()
    }
    notes.insert(0, new_note) # Newest first
    _save_json(NOTES_FILE, notes)
    return notes

def delete_user_note(note_id: str) -> List[Dict]:
    notes = get_user_notes()
    notes = [n for n in notes if n["id"] != note_id]
    _save_json(NOTES_FILE, notes)
    return notes
