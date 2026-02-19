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
    session_id: Optional[str] = None
    style: Optional[str] = "detailed"  # 'detailed' or 'concise'

class ChatResponse(BaseModel):
    response: str
    thinking_time: float

class SaveChatMessageRequest(BaseModel):
    user_id: str
    role: str
    user_id: str
    role: str
    content: str
    session_id: Optional[str] = None
    thinking_time: Optional[float] = None


class CreateSessionRequest(BaseModel):
    user_id: str
    title: Optional[str] = "New Chat"


class UpdateSessionRequest(BaseModel):
    user_id: str
    title: str


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
    
    result = await chat_with_oracle(request.message, history, style=request.style)
    
    # Update session title if it's the first message and creating a new session
    # This logic handles auto-titling (simplified for now)
    if request.session_id and len(history or []) == 0:
        # TODO: Generate title from message
        pass
        
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
# CHAT SESSION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/chat/sessions/{user_id}")
async def get_user_sessions_endpoint(user_id: str):
    """Get all chat sessions for user."""
    try:
        from services.supabase_service import get_user_sessions
        sessions = await get_user_sessions(user_id)
        return {"sessions": sessions}
    except Exception as e:
        print(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/chat/sessions")
async def create_session_endpoint(request: CreateSessionRequest):
    """Create a new chat session."""
    try:
        from services.supabase_service import create_chat_session
        session = await create_chat_session(request.user_id, request.title)
        return session
    except Exception as e:
        print(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/chat/sessions/{session_id}")
async def update_session_endpoint(session_id: str, request: UpdateSessionRequest):
    """Update chat session title."""
    try:
        from services.supabase_service import update_session_title
        success = await update_session_title(session_id, request.title, request.user_id)
        return {"success": success}
    except Exception as e:
        print(f"Error updating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/chat/sessions/{session_id}")
async def delete_session_endpoint(session_id: str, user_id: str):
    """Delete a chat session."""
    try:
        from services.supabase_service import delete_chat_session
        success = await delete_chat_session(session_id, user_id)
        return {"success": success}
    except Exception as e:
        print(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/chat/sessions/{session_id}/messages")
async def get_session_messages_endpoint(session_id: str):
    """Get messages for a specific session."""
    try:
        from services.supabase_service import get_session_messages
        messages = await get_session_messages(session_id)
        return {"messages": messages}
    except Exception as e:
        print(f"Error getting session messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# CHAT HISTORY ENDPOINTS (Legacy / Direct Message)
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
            session_id=request.session_id,
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
