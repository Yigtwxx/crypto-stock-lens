"""
Supabase Service - Database and Auth integration
Provides centralized Supabase client and helper functions.
"""
import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Lazy-loaded client
_supabase_client = None


def get_supabase():
    """Get or create Supabase client instance."""
    global _supabase_client
    
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
        
        from supabase import create_client, Client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    return _supabase_client


# ═══════════════════════════════════════════════════════════════════════════════
# USER PROFILE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

async def get_user_profile(user_id: str) -> Optional[Dict]:
    """Get user profile from database."""
    try:
        supabase = get_supabase()
        response = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        return response.data
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        return None


async def update_user_profile(user_id: str, data: Dict) -> bool:
    """Update user profile in database."""
    try:
        supabase = get_supabase()
        supabase.table("profiles").upsert({
            "id": user_id,
            **data
        }).execute()
        return True
    except Exception as e:
        print(f"Error updating user profile: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# WATCHLIST HELPERS (Future migration from JSON)
# ═══════════════════════════════════════════════════════════════════════════════

async def get_user_watchlists(user_id: str) -> List[Dict]:
    """Get user's watchlists from database."""
    try:
        supabase = get_supabase()
        response = supabase.table("watchlists").select("*").eq("user_id", user_id).execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching watchlists: {e}")
        return []


async def create_watchlist(user_id: str, name: str, items: List[Dict]) -> Optional[Dict]:
    """Create a new watchlist for user."""
    try:
        supabase = get_supabase()
        response = supabase.table("watchlists").insert({
            "user_id": user_id,
            "name": name,
            "items": items
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error creating watchlist: {e}")
        return None


async def delete_watchlist(watchlist_id: str, user_id: str) -> bool:
    """Delete a watchlist (with user ownership check)."""
    try:
        supabase = get_supabase()
        supabase.table("watchlists").delete().eq("id", watchlist_id).eq("user_id", user_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting watchlist: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# NOTES HELPERS (Future migration from JSON)
# ═══════════════════════════════════════════════════════════════════════════════

async def get_user_notes(user_id: str) -> List[Dict]:
    """Get user's notes from database."""
    try:
        supabase = get_supabase()
        response = supabase.table("notes").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching notes: {e}")
        return []


async def create_note(user_id: str, title: str, content: str) -> Optional[Dict]:
    """Create a new note for user."""
    try:
        supabase = get_supabase()
        response = supabase.table("notes").insert({
            "user_id": user_id,
            "title": title,
            "content": content
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error creating note: {e}")
        return None


async def delete_note(note_id: str, user_id: str) -> bool:
    """Delete a note (with user ownership check)."""
    try:
        supabase = get_supabase()
        supabase.table("notes").delete().eq("id", note_id).eq("user_id", user_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting note: {e}")
        return False
