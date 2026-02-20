from datetime import datetime
from typing import List, Optional, Dict, Any
from services.supabase_service import get_supabase

async def get_all_posts(
    limit: int = 20, 
    offset: int = 0, 
    filter_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch community posts with user details.
    """
    try:
        supabase = get_supabase()
        
        query = supabase.table("community_posts")\
            .select("*, profiles(full_name, avatar_url, subscription_plan)")\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)
            
        if filter_type and filter_type != "all":
            query = query.eq("type", filter_type)
            
        response = query.execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []

async def create_post(
    user_id: str, 
    content: str, 
    post_type: str, 
    title: Optional[str] = None,
    asset_symbol: Optional[str] = None,
    image_url: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new community post.
    """
    try:
        supabase = get_supabase()
        
        data = {
            "user_id": user_id,
            "content": content,
            "type": post_type,
            "title": title,
            "asset_symbol": asset_symbol,
            "image_url": image_url
        }
        
        response = supabase.table("community_posts").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error creating post: {e}")
        return None

async def get_post_comments(post_id: str) -> List[Dict[str, Any]]:
    """
    Fetch comments for a specific post.
    """
    try:
        supabase = get_supabase()
        
        response = supabase.table("community_comments")\
            .select("*, profiles(full_name, avatar_url)")\
            .eq("post_id", post_id)\
            .order("created_at", desc=False)\
            .execute()
            
        return response.data or []
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return []

async def create_comment(user_id: str, post_id: str, content: str) -> Optional[Dict[str, Any]]:
    """
    Add a comment to a post.
    """
    try:
        supabase = get_supabase()
        
        # 1. Insert comment
        response = supabase.table("community_comments").insert({
            "user_id": user_id,
            "post_id": post_id,
            "content": content
        }).execute()
        
        if response.data:
            # 2. Increment comment count on post (could be a trigger, but doing manually for now)
            # Fetch current count first (atomicity issue possible but acceptable for MVP)
            # Actually, let's just increment safely if possible, but Supabase doesn't have nice increment without RPC
            # We'll rely on the client or subsequent fetch to get accurate count, or use a trigger in future
            # For now, simplistic update:
            post = supabase.table("community_posts").select("comments_count").eq("id", post_id).single().execute()
            if post.data:
                new_count = (post.data.get("comments_count") or 0) + 1
                supabase.table("community_posts").update({"comments_count": new_count}).eq("id", post_id).execute()
                
            return response.data[0]
            
        return None
    except Exception as e:
        print(f"Error creating comment: {e}")
        return None

async def toggle_like(user_id: str, post_id: str) -> Dict[str, Any]:
    """
    Toggle like on a post. Returns new state and count.
    """
    try:
        supabase = get_supabase()
        
        # Check if already liked
        existing = supabase.table("community_likes").select("*")\
            .eq("user_id", user_id).eq("post_id", post_id).execute()
            
        is_liked = False
        if existing.data and len(existing.data) > 0:
            # Unlike
            supabase.table("community_likes").delete()\
                .eq("user_id", user_id).eq("post_id", post_id).execute()
            is_liked = False
        else:
            # Like
            supabase.table("community_likes").insert({
                "user_id": user_id,
                "post_id": post_id
            }).execute()
            is_liked = True
            
        # Update post like count
        # Get count from likes table for accuracy
        count_res = supabase.table("community_likes").select("user_id", count="exact")\
            .eq("post_id", post_id).execute()
            
        new_count = count_res.count or 0
        
        supabase.table("community_posts").update({"likes_count": new_count}).eq("id", post_id).execute()
        
        return {"liked": is_liked, "likes_count": new_count}
        
    except Exception as e:
        print(f"Error toggling like: {e}")
        return {"error": str(e)}

async def get_user_posts(user_id: str) -> List[Dict[str, Any]]:
    """
    Fetch posts created by a specific user.
    """
    try:
        supabase = get_supabase()
        response = supabase.table("community_posts")\
            .select("*, profiles(full_name, avatar_url, subscription_plan)")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching user posts: {e}")
        return []
