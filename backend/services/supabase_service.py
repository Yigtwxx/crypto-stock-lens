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
        # Prefer Service Role key for backend operations to bypass RLS
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or SUPABASE_KEY
        
        if not SUPABASE_URL or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY (or SUPABASE_SERVICE_ROLE_KEY) must be set in environment")
        
        from supabase import create_client, Client
        _supabase_client = create_client(SUPABASE_URL, key)
    
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


# ═══════════════════════════════════════════════════════════════════════════════
# CHAT MESSAGE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

async def get_user_sessions(user_id: str) -> List[Dict]:
    """
    Get user's chat sessions.
    Automatically cleans up sessions older than 7 days.
    """
    try:
        supabase = get_supabase()
        
        # Cleanup old sessions (7+ days)
        from datetime import datetime, timedelta
        cutoff_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        supabase.table("chat_sessions").delete().eq("user_id", user_id).lt("updated_at", cutoff_date).execute()
        
        # Fetch active sessions
        response = supabase.table("chat_sessions")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("updated_at", desc=True)\
            .execute()
            
        sessions = response.data or []

        # Auto-migrate legacy messages (if no sessions exist or just as a check)
        # Check if there are messages without session_id
        orphans_check = supabase.table("chat_messages")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .is_("session_id", "null")\
            .limit(1)\
            .execute()
            
        if orphans_check.count > 0:
            print(f"Found {orphans_check.count} orphaned messages. Migrating to new session...")
            # Create a catch-all session for legacy chats
            # We use a specific title or just "Geçmiş Sohbetler"
            # First check if we already have a "Geçmiş Sohbetler" session from today? 
            # Simplified: Just create one if orphans exist.
            
            # Create session
            migration_session = supabase.table("chat_sessions").insert({
                "user_id": user_id,
                "title": "Geçmiş Sohbetler"
            }).execute()
            
            if migration_session.data:
                session_id = migration_session.data[0]['id']
                
                # Update orphans
                supabase.table("chat_messages").update({
                    "session_id": session_id
                }).eq("user_id", user_id).is_("session_id", "null").execute()
                
                # Add to sessions list
                sessions.insert(0, migration_session.data[0])

        return sessions
    except Exception as e:
        # Check for missing table error
        msg = str(e)
        if "PGRST205" in msg or "Could not find the table" in msg:
            print(f"Warning: 'chat_sessions' table missing. Chat history disabled. Run migration 003_chat_sessions.sql.")
        else:
            print(f"Error fetching sessions: {e}")
        return []


async def create_chat_session(user_id: str, title: str = "Yeni Sohbet") -> Optional[Dict]:
    """Create a new chat session."""
    try:
        supabase = get_supabase()
        response = supabase.table("chat_sessions").insert({
            "user_id": user_id,
            "title": title
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error creating session: {e}")
        return None


async def update_session_title(session_id: str, title: str, user_id: str) -> bool:
    """Update session title."""
    try:
        supabase = get_supabase()
        supabase.table("chat_sessions").update({"title": title}).eq("id", session_id).eq("user_id", user_id).execute()
        return True
    except Exception as e:
        print(f"Error updating session: {e}")
        return False


async def delete_chat_session(session_id: str, user_id: str) -> bool:
    """Delete a chat session."""
    try:
        supabase = get_supabase()
        supabase.table("chat_sessions").delete().eq("id", session_id).eq("user_id", user_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting session: {e}")
        return False


async def get_session_messages(session_id: str, limit: int = 50) -> List[Dict]:
    """
    Get messages for a specific session.
    """
    try:
        supabase = get_supabase()
        
        response = supabase.table("chat_messages")\
            .select("*")\
            .eq("session_id", session_id)\
            .order("created_at", desc=False)\
            .execute() # Removed limit to get full context of session
        
        return response.data or []
    except Exception as e:
        print(f"Error fetching session messages: {e}")
        return []


async def save_chat_message(
    user_id: str, 
    role: str, 
    content: str, 
    session_id: Optional[str] = None,
    thinking_time: float = None
) -> Optional[Dict]:
    """Save a chat message to database."""
    try:
        supabase = get_supabase()
        
        data = {
            "user_id": user_id,
            "role": role,
            "content": content
        }
        
        if session_id:
            data["session_id"] = session_id
            
            # Update session timestamp
            supabase.table("chat_sessions").update({
                "updated_at": "now()"
            }).eq("id", session_id).execute()
        
        if thinking_time is not None:
            data["thinking_time"] = thinking_time
        
        response = supabase.table("chat_messages").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error saving chat message: {e}")
        return None


async def get_chat_history(user_id: str, limit: int = 50) -> List[Dict]:
    """Get chat history for a user (legacy endpoint)."""
    try:
        supabase = get_supabase()
        response = supabase.table("chat_messages")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching chat history: {e}")
        return []


async def clear_chat_history(user_id: str) -> bool:
    """Clear all chat history for a user."""
    try:
        supabase = get_supabase()
        supabase.table("chat_messages").delete().eq("user_id", user_id).execute()
        return True
    except Exception as e:
        print(f"Error clearing chat history: {e}")
        return False

