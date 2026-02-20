"""
Background Scheduler Service
Manages automated tasks like news fetching and data aggregation.
"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

# Correct import path
from services.news_service import fetch_all_news
from utils import log_header, log_step, log_success, log_error, update_news_cache

# Global scheduler instance
scheduler = AsyncIOScheduler()

async def update_news_cache_job():
    """
    Background job to fetch news and update the global cache.
    """
    try:
        # Gray color for log_step message part isn't standard in utils, using standard log_step
        log_step("🔄", "Background Job: Fetching fresh news...") 
        
        # Fetch news from all sources
        items = await fetch_all_news()
        
        if items:
            # Update the cache
            update_news_cache(items)
            log_success(f"Background Job: Cache updated with {len(items)} news items")
        else:
            log_error("Background Job: No news items fetched")
            
    except Exception as e:
        log_error(f"Background Job Error: {e}")

def start_scheduler():
    """Start the background scheduler."""
    if not scheduler.running:
        # Add news update job - runs every 10 minutes
        # Also run immediately on startup is handled in main.py startup event
        scheduler.add_job(
            update_news_cache_job,
            trigger=IntervalTrigger(minutes=2),
            id="news_update_job",
            name="Update News Cache",
            replace_existing=True
        )
        
        scheduler.start()
        log_header("SCHEDULER STARTED")
        log_success("Background tasks initialized (News fetch: 10m)")

def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler shut down successfully.")
