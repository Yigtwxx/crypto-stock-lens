"""
Profile Router
Handles user profiles, subscriptions, connected accounts, settings, and AI query tracking.
"""
from fastapi import APIRouter, HTTPException
from services import profile_service

router = APIRouter()


@router.get("/api/profile/{user_id}")
async def get_user_profile(user_id: str):
    """Get user profile with subscription info."""
    try:
        profile = await profile_service.get_user_profile(user_id)
        if profile:
            return profile
        raise HTTPException(status_code=404, detail="Profile not found")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/profile/{user_id}")
async def update_user_profile(user_id: str, data: dict):
    """Update user profile."""
    try:
        success = await profile_service.update_user_profile(user_id, data)
        if success:
            return {"success": True}
        raise HTTPException(status_code=400, detail="Failed to update profile")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/profile/{user_id}/subscription")
async def get_subscription(user_id: str):
    """Get user's current subscription info."""
    try:
        subscription = await profile_service.get_subscription(user_id)
        return subscription
    except Exception as e:
        print(f"Error getting subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/profile/{user_id}/subscription")
async def update_subscription(user_id: str, data: dict):
    """Update user's subscription plan."""
    try:
        plan = data.get("plan", "free")
        duration_days = data.get("duration_days", 30)
        success = await profile_service.update_subscription(user_id, plan, duration_days)
        if success:
            return {"success": True, "plan": plan}
        raise HTTPException(status_code=400, detail="Failed to update subscription")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/profile/{user_id}/accounts")
async def get_connected_accounts(user_id: str):
    """Get user's connected social accounts."""
    try:
        accounts = await profile_service.get_connected_accounts(user_id)
        return {"accounts": accounts}
    except Exception as e:
        print(f"Error getting connected accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/profile/{user_id}/accounts/{provider}")
async def connect_account(user_id: str, provider: str, data: dict):
    """Connect a social account."""
    try:
        success = await profile_service.connect_account(
            user_id=user_id,
            provider=provider,
            provider_user_id=data.get("provider_user_id", ""),
            provider_username=data.get("provider_username", ""),
            access_token=data.get("access_token"),
            refresh_token=data.get("refresh_token")
        )
        if success:
            return {"success": True, "provider": provider}
        raise HTTPException(status_code=400, detail="Failed to connect account")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error connecting account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/profile/{user_id}/accounts/{provider}")
async def disconnect_account(user_id: str, provider: str):
    """Disconnect a social account."""
    try:
        success = await profile_service.disconnect_account(user_id, provider)
        if success:
            return {"success": True}
        raise HTTPException(status_code=400, detail="Failed to disconnect account")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error disconnecting account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/profile/{user_id}/settings")
async def get_user_settings(user_id: str):
    """Get user settings."""
    try:
        settings = await profile_service.get_user_settings(user_id)
        return settings
    except Exception as e:
        print(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/profile/{user_id}/settings")
async def update_user_settings(user_id: str, data: dict):
    """Update user settings."""
    try:
        success = await profile_service.update_user_settings(user_id, data)
        if success:
            return {"success": True}
        raise HTTPException(status_code=400, detail="Failed to update settings")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/profile/{user_id}/ai-query")
async def increment_ai_query(user_id: str):
    """Increment AI query count and check limits."""
    try:
        result = await profile_service.increment_ai_queries(user_id)
        return result
    except Exception as e:
        print(f"Error incrementing AI query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
