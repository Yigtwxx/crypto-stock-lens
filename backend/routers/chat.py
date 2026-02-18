"""
Chat Router
Handles Oracle AI chat, chat status, and chat history persistence.
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.chat_service import chat_with_oracle, check_chat_available
from utils import Colors, log_header, log_step, log_success, log_info

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    response: str
    thinking_time: float

class SaveChatMessageRequest(BaseModel):
    user_id: str
    role: str
    content: str
    thinking_time: Optional[float] = None


# ═══════════════════════════════════════════════════════════════════════════════
# ORACLE CHAT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/chat", response_model=ChatResponse)
async def oracle_chat(request: ChatRequest):
    """
    Chat with Oracle AI assistant.
    
    Provides intelligent responses about crypto, stocks, and market analysis.
    Uses extended thinking time for quality responses.
    """
    log_header("ORACLE CHAT REQUEST")
    log_step("💬", f"Message: {request.message[:100]}..." if len(request.message) > 100 else f"Message: {request.message}")
    
    # Convert history to dict format
    history = None
    if request.history:
        history = [{"role": m.role, "content": m.content} for m in request.history]
        log_info(f"Conversation history: {len(history)} messages")
    
    log_step("🤔", "Oracle is thinking (this may take a while for complex questions)...", Colors.PURPLE)
    
    result = await chat_with_oracle(request.message, history)
    
    log_success(f"Response generated in {result['thinking_time']}s")
    log_info(f"Response length: {len(result['response'])} characters")
    print(f"{Colors.PURPLE}{'═'*60}{Colors.END}\n")
    
    return ChatResponse(
        response=result["response"],
        thinking_time=result["thinking_time"]
    )


@router.get("/api/chat/status")
async def chat_status():
    """Check if Oracle chat is available."""
    is_available = await check_chat_available()
    return {
        "available": is_available,
        "model": "llama3.1:8b" if is_available else None,
        "message": "Oracle hazır" if is_available else "Ollama servisi çalışmıyor"
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CHAT HISTORY ENDPOINTS (Database Persistence)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/chat/history/{user_id}")
async def get_chat_history_endpoint(user_id: str, limit: int = 50):
    """
    Get chat history for a user from database.
    Automatically cleans up messages older than 7 days.
    """
    try:
        from services.supabase_service import get_chat_history
        messages = await get_chat_history(user_id, limit)
        return {"messages": messages, "count": len(messages)}
    except Exception as e:
        print(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/chat/history")
async def save_chat_message_endpoint(request: SaveChatMessageRequest):
    """Save a chat message to database."""
    try:
        from services.supabase_service import save_chat_message
        result = await save_chat_message(
            user_id=request.user_id,
            role=request.role,
            content=request.content,
            thinking_time=request.thinking_time
        )
        return {"success": True, "message": result}
    except Exception as e:
        print(f"Error saving chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/chat/history/{user_id}")
async def clear_chat_history_endpoint(user_id: str):
    """Clear all chat history for a user."""
    try:
        from services.supabase_service import clear_chat_history
        success = await clear_chat_history(user_id)
        return {"success": success}
    except Exception as e:
        print(f"Error clearing chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
