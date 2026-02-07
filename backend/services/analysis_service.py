
import json
import os
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from services.ollama_service import generate_completion
from services.news_service import fetch_all_news
from services.market_overview_service import fetch_market_overview
from services.fear_greed_service import fetch_fear_greed_index

REPORTS_FILE = "data/analysis_reports.json"
NOTES_FILE = "data/user_notes.json"

# ═══════════════════════════════════════════════════════════════════════════════
# DATA PERSISTENCE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _load_json(filepath: str, default: any):
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except:
        return default

def _save_json(filepath: str, data: any):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

# ═══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

async def generate_market_report(timeframe: str) -> str:
    """
    Generate a market report (Daily, Weekly, Monthly) using aggregated data and AI.
    """
    # 1. Aggregate Data
    try:
        news_items = await fetch_all_news()
        market_data = await fetch_market_overview()
        fear_greed = await fetch_fear_greed_index()
    except Exception as e:
        print(f"Error fetching data for report: {e}")
        return "Failed to generate report due to data fetching error."

    # Filter news based on timeframe (approximate)
    # real filtering would strictly check dates, but for MVP we use latest X items
    limit = 20 if timeframe == 'daily' else 50
    recent_news = news_items[:limit]
    
    news_summary = "\n".join([f"- {n.title} ({n.asset_type.upper()})" for n in recent_news])
    
    top_coins = "\n".join([f"{c['symbol']}: ${c['price']} ({c['change_24h']}%)" for c in market_data.get('coins', [])[:5]])
    
    prompt = f"""
    TIME_FRAME: {timeframe.upper()}
    DATE: {datetime.now().strftime('%Y-%m-%d')}
    
    MARKET DATA:
    Global Market Cap: ${market_data.get('total_market_cap', 0):,}
    BTC Dominance: {market_data.get('btc_dominance', 0)}%
    Fear & Greed Index: {fear_greed.get('value')} ({fear_greed.get('classification')})
    
    TOP ASSETS:
    {top_coins}
    
    RECENT NEWS HEADLINES:
    {news_summary}
    
    TASK:
    Write a comprehensive {timeframe} financial market analysis report.
    - Use Markdown formatting (## Headers, **Bold**, Lists).
    - Tone: Professional, analytical, institutional.
    - Structure:
      1. **Executive Summary**: High-level market sentiment.
      2. **Key Drivers**: What is moving the market? (Cite specific news).
      3. **Sector Analysis**: Crypto vs Stocks performance.
      4. **Outlook**: What to watch for in the next {timeframe}.
    
    Do not mention you are an AI. Write as a Senior Financial Analyst.
    """
    
    system_prompt = "You are a Senior Financial Analyst at a top-tier investment firm. You provide deep, insightful market commentary based on data."
    
    report_content = await generate_completion(prompt, system_prompt, temperature=0.3, max_tokens=1500)
    
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
