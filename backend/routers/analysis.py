"""
Analysis & Notes Router
Handles AI market reports and user notes.
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class NoteRequest(BaseModel):
    title: str
    content: str


@router.get("/api/analysis/report/{timeframe}")
async def get_analysis_report(timeframe: str):
    """Get AI generated market report (daily, weekly, monthly)."""
    try:
        from services.analysis_service import get_report
        if timeframe not in ['daily', 'weekly', 'monthly']:
            raise HTTPException(status_code=400, detail="Invalid timeframe")
        return await get_report(timeframe)
    except Exception as e:
        print(f"Error getting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/analysis/generate/{timeframe}")
async def generate_analysis_report(timeframe: str):
    """Force regenerate a market report."""
    try:
        from services.analysis_service import generate_market_report
        content = await generate_market_report(timeframe)
        return {"content": content, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        print(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/analysis/notes")
async def get_notes():
    """Get all user notes."""
    try:
        from services.analysis_service import get_user_notes
        return get_user_notes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/analysis/notes")
async def create_note(request: NoteRequest):
    """Create a new user note."""
    try:
        from services.analysis_service import add_user_note
        return add_user_note(request.title, request.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/analysis/notes/{note_id}")
async def delete_note(note_id: str):
    """Delete a user note."""
    try:
        from services.analysis_service import delete_user_note
        return delete_user_note(note_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
