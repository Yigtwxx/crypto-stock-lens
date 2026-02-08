"""Profile service for user management, subscriptions, and connected accounts."""
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from services.supabase_service import get_supabase


# ═══════════════════════════════════════════════════════════════════════════════
# PROFILE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user profile with subscription info.
    Creates a default profile if one doesn't exist.
    """
    try:
        supabase = get_supabase()
        
        # First try to get existing profile
        response = supabase.table("profiles").select("*").eq("id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            profile = response.data[0]
            
            # Reset AI queries if new day
            if profile.get("ai_queries_reset_at"):
                reset_date = profile["ai_queries_reset_at"]
                if isinstance(reset_date, str):
                    reset_date = date.fromisoformat(reset_date.split("T")[0])
                
                if reset_date < date.today():
                    # Reset queries for new day
                    await update_user_profile(user_id, {
                        "ai_queries_today": 0,
                        "ai_queries_reset_at": date.today().isoformat()
                    })
                    profile["ai_queries_today"] = 0
            
            # Add computed fields
            plan = profile.get("subscription_plan", "free")
            profile["ai_query_limit"] = 5 if plan == "free" else 999999
            profile["ai_queries_remaining"] = max(0, profile["ai_query_limit"] - profile.get("ai_queries_today", 0))
            
            return profile
        
        # Profile doesn't exist - create a default one
        print(f"Creating default profile for user: {user_id}")
        default_profile = {
            "id": user_id,
            "subscription_plan": "free",
            "ai_queries_today": 0,
            "ai_queries_reset_at": date.today().isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            supabase.table("profiles").insert(default_profile).execute()
        except Exception as insert_error:
            print(f"Could not create profile (may already exist): {insert_error}")
        
        # Return default profile with computed fields
        default_profile["ai_query_limit"] = 5
        default_profile["ai_queries_remaining"] = 5
        return default_profile
        
    except Exception as e:
        print(f"Error getting profile: {e}")
    
    # Return a minimal default profile even on error
    return {
        "id": user_id,
        "subscription_plan": "free",
        "ai_queries_today": 0,
        "ai_query_limit": 5,
        "ai_queries_remaining": 5
    }


async def update_user_profile(user_id: str, data: Dict[str, Any]) -> bool:
    """
    Update user profile fields.
    Allowed fields: full_name, avatar_url, subscription_plan, ai_queries_today, ai_queries_reset_at
    """
    allowed_fields = ["full_name", "avatar_url", "subscription_plan", "subscription_expires_at", 
                      "ai_queries_today", "ai_queries_reset_at"]
    
    filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
    filtered_data["updated_at"] = datetime.now().isoformat()
    
    try:
        supabase = get_supabase()
        
        response = supabase.table("profiles").update(filtered_data).eq("id", user_id).execute()
        
        return response.data is not None
    except Exception as e:
        print(f"Error updating profile: {e}")
    
    return False


async def increment_ai_queries(user_id: str) -> Dict[str, Any]:
    """
    Increment AI query count for user. Returns updated count and limit info.
    """
    profile = await get_user_profile(user_id)
    
    if not profile:
        return {"allowed": False, "reason": "Profile not found"}
    
    current_count = profile.get("ai_queries_today", 0)
    limit = profile.get("ai_query_limit", 5)
    
    if current_count >= limit:
        return {
            "allowed": False,
            "reason": "Daily AI query limit reached",
            "queries_today": current_count,
            "limit": limit,
            "plan": profile.get("subscription_plan", "free")
        }
    
    # Increment count
    await update_user_profile(user_id, {"ai_queries_today": current_count + 1})
    
    return {
        "allowed": True,
        "queries_today": current_count + 1,
        "limit": limit,
        "remaining": limit - current_count - 1,
        "plan": profile.get("subscription_plan", "free")
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CONNECTED ACCOUNTS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def get_connected_accounts(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all connected social accounts for a user.
    """
    try:
        supabase = get_supabase()
        
        response = supabase.table("connected_accounts").select(
            "provider, provider_username, connected_at"
        ).eq("user_id", user_id).execute()
        
        return response.data or []
    except Exception as e:
        print(f"Error getting connected accounts: {e}")
    
    return []


async def connect_account(
    user_id: str, 
    provider: str, 
    provider_user_id: str,
    provider_username: str,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None
) -> bool:
    """
    Connect a social account for a user.
    """
    if provider not in ["twitter", "discord", "telegram"]:
        return False
    
    try:
        supabase = get_supabase()
        
        # Upsert (insert or update)
        response = supabase.table("connected_accounts").upsert({
            "user_id": user_id,
            "provider": provider,
            "provider_user_id": provider_user_id,
            "provider_username": provider_username,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "connected_at": datetime.now().isoformat()
        }, on_conflict="user_id,provider").execute()
        
        return response.data is not None
    except Exception as e:
        print(f"Error connecting account: {e}")
    
    return False


async def disconnect_account(user_id: str, provider: str) -> bool:
    """
    Disconnect a social account.
    """
    try:
        supabase = get_supabase()
        
        response = supabase.table("connected_accounts").delete().eq(
            "user_id", user_id
        ).eq("provider", provider).execute()
        
        return True
    except Exception as e:
        print(f"Error disconnecting account: {e}")
    
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# SUBSCRIPTION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def get_subscription(user_id: str) -> Dict[str, Any]:
    """
    Get user's current subscription info.
    """
    profile = await get_user_profile(user_id)
    
    if not profile:
        return {
            "plan": "free",
            "expires_at": None,
            "features": get_plan_features("free")
        }
    
    plan = profile.get("subscription_plan", "free")
    expires_at = profile.get("subscription_expires_at")
    
    # Check if subscription expired
    if expires_at and plan != "free":
        exp_date = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if exp_date < datetime.now(exp_date.tzinfo):
            # Subscription expired, downgrade to free
            await update_user_profile(user_id, {"subscription_plan": "free"})
            plan = "free"
    
    return {
        "plan": plan,
        "expires_at": expires_at,
        "features": get_plan_features(plan),
        "ai_queries_today": profile.get("ai_queries_today", 0),
        "ai_query_limit": profile.get("ai_query_limit", 5)
    }


async def update_subscription(user_id: str, plan: str, duration_days: int = 30) -> bool:
    """
    Update user's subscription plan.
    For production, this would integrate with Stripe/payment processor.
    """
    if plan not in ["free", "pro", "whale"]:
        return False
    
    expires_at = None
    if plan != "free":
        from datetime import timedelta
        expires_at = (datetime.now() + timedelta(days=duration_days)).isoformat()
    
    return await update_user_profile(user_id, {
        "subscription_plan": plan,
        "subscription_expires_at": expires_at
    })


def get_plan_features(plan: str) -> Dict[str, Any]:
    """
    Get features available for a subscription plan.
    """
    plans = {
        "free": {
            "name": "Free",
            "price": 0,
            "news_delay_minutes": 15,
            "ai_queries_per_day": 5,
            "live_liquidation": False,
            "advanced_alerts": False,
            "api_access": False,
            "priority_support": False
        },
        "pro": {
            "name": "Pro",
            "price": 29,
            "news_delay_minutes": 0,
            "ai_queries_per_day": 999999,
            "live_liquidation": True,
            "advanced_alerts": True,
            "api_access": False,
            "priority_support": False
        },
        "whale": {
            "name": "Whale",
            "price": 99,
            "news_delay_minutes": 0,
            "ai_queries_per_day": 999999,
            "live_liquidation": True,
            "advanced_alerts": True,
            "api_access": True,
            "priority_support": True
        }
    }
    
    return plans.get(plan, plans["free"])


# ═══════════════════════════════════════════════════════════════════════════════
# USER SETTINGS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def get_user_settings(user_id: str) -> Dict[str, Any]:
    """
    Get user settings, create defaults if not exists.
    """
    try:
        supabase = get_supabase()
        
        response = supabase.table("user_settings").select("*").eq("user_id", user_id).single().execute()
        
        if response.data:
            return response.data
        
        # Create default settings
        default_settings = {
            "user_id": user_id,
            "theme": "dark",
            "notifications_enabled": True,
            "email_alerts": False,
            "telegram_alerts": False,
            "default_market": "crypto"
        }
        
        supabase.table("user_settings").insert(default_settings).execute()
        return default_settings
        
    except Exception as e:
        print(f"Error getting settings: {e}")
    
    return {
        "theme": "dark",
        "notifications_enabled": True,
        "email_alerts": False,
        "telegram_alerts": False,
        "default_market": "crypto"
    }


async def update_user_settings(user_id: str, settings: Dict[str, Any]) -> bool:
    """
    Update user settings.
    """
    allowed_fields = ["theme", "notifications_enabled", "email_alerts", 
                      "telegram_alerts", "default_market"]
    
    filtered_settings = {k: v for k, v in settings.items() if k in allowed_fields}
    filtered_settings["updated_at"] = datetime.now().isoformat()
    
    try:
        supabase = get_supabase()
        
        # Check if settings exist
        existing = supabase.table("user_settings").select("id").eq("user_id", user_id).execute()
        
        if existing.data:
            supabase.table("user_settings").update(filtered_settings).eq("user_id", user_id).execute()
        else:
            filtered_settings["user_id"] = user_id
            supabase.table("user_settings").insert(filtered_settings).execute()
        
        return True
    except Exception as e:
        print(f"Error updating settings: {e}")
    
    return False
