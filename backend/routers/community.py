from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from services import community_service

router = APIRouter()

# Models
class CreatePostRequest(BaseModel):
    user_id: str
    content: str
    type: str # 'question', 'thought', 'analysis'
    title: Optional[str] = None
    asset_symbol: Optional[str] = None
    image_url: Optional[str] = None

class CreateCommentRequest(BaseModel):
    user_id: str
    content: str

class LikeRequest(BaseModel):
    user_id: str

# Endpoints

@router.get("/api/community/posts")
async def get_posts(
    limit: int = 20, 
    offset: int = 0, 
    type: Optional[str] = None
):
    """Get all community posts."""
    try:
        posts = await community_service.get_all_posts(limit, offset, type)
        return {"posts": posts}
    except Exception as e:
        print(f"Error getting posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/community/posts")
async def create_post(request: CreatePostRequest):
    """Create a new post."""
    try:
        post = await community_service.create_post(
            user_id=request.user_id,
            content=request.content,
            post_type=request.type,
            title=request.title,
            asset_symbol=request.asset_symbol,
            image_url=request.image_url
        )
        if post:
            return post
        raise HTTPException(status_code=400, detail="Failed to create post")
    except Exception as e:
        print(f"Error creating post: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/community/posts/user/{user_id}")
async def get_user_posts(user_id: str):
    """Get posts by a specific user."""
    try:
        posts = await community_service.get_user_posts(user_id)
        return {"posts": posts}
    except Exception as e:
        print(f"Error getting user posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/community/posts/{post_id}/comments")
async def get_post_comments(post_id: str):
    """Get comments for a post."""
    try:
        comments = await community_service.get_post_comments(post_id)
        return {"comments": comments}
    except Exception as e:
        print(f"Error getting comments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/community/posts/{post_id}/comments")
async def create_comment(post_id: str, request: CreateCommentRequest):
    """Add a comment to a post."""
    try:
        comment = await community_service.create_comment(
            user_id=request.user_id,
            post_id=post_id,
            content=request.content
        )
        if comment:
            return comment
        raise HTTPException(status_code=400, detail="Failed to create comment")
    except Exception as e:
        print(f"Error creating comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/community/posts/{post_id}/like")
async def toggle_like(post_id: str, request: LikeRequest):
    """Toggle like on a post."""
    try:
        result = await community_service.toggle_like(request.user_id, post_id)
        return result
    except Exception as e:
        print(f"Error toggling like: {e}")
        raise HTTPException(status_code=500, detail=str(e))
