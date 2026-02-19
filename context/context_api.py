"""
ClawForge Context API
=====================
FastAPI endpoints for context management.
Integrates with the main ClawForge API.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from context_manager import (
    get_context_manager,
    start_session,
    update_context,
    add_to_history,
    get_resume_context,
    end_session,
    get_privacy_status,
    PrivacyLevel
)

router = APIRouter(prefix="/context", tags=["context"])


# ==================== MODELS ====================

class SessionStartRequest(BaseModel):
    user_context: Optional[Dict[str, Any]] = None


class ContextUpdateRequest(BaseModel):
    current_task: Optional[str] = None
    where_left_off: Optional[str] = None
    next_steps: Optional[List[str]] = None
    task_status: Optional[str] = None


class HistoryEntryRequest(BaseModel):
    action: str
    details: Dict[str, Any]


class SessionEndRequest(BaseModel):
    summary: Optional[str] = None


class PrivacyLevelRequest(BaseModel):
    level: str


# ==================== ENDPOINTS ====================

@router.post("/session/start")
async def api_start_session(request: SessionStartRequest = None):
    """Start a new conversation session"""
    try:
        user_ctx = request.user_context if request else None
        conversation_id = start_session(user_ctx)
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "message": "Session started successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/status")
async def api_get_status():
    """Get current session status"""
    try:
        manager = get_context_manager()
        context = manager.get_context()
        privacy = manager.get_privacy_status()
        
        return {
            "active": privacy["conversation_active"],
            "conversation_id": context.get("conversation_id"),
            "started_at": context.get("started_at"),
            "privacy": privacy
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/update")
async def api_update_context(request: ContextUpdateRequest):
    """Update conversation context"""
    try:
        update_context(
            current_task=request.current_task,
            where_left_off=request.where_left_off,
            next_steps=request.next_steps,
            task_status=request.task_status
        )
        
        return {"success": True, "message": "Context updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/history")
async def api_add_history(request: HistoryEntryRequest):
    """Add entry to session history"""
    try:
        add_to_history({
            "action": request.action,
            **request.details
        })
        
        return {"success": True, "message": "History entry added"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/resume")
async def api_get_resume_context():
    """Get context for resuming conversation"""
    try:
        context = get_resume_context()
        
        return {
            "success": True,
            "context": context
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/end")
async def api_end_session(request: SessionEndRequest = None):
    """End current session"""
    try:
        summary = request.summary if request else None
        end_session(summary)
        
        return {"success": True, "message": "Session ended"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PRIVACY ENDPOINTS ====================

@router.get("/privacy/status")
async def api_get_privacy_status():
    """Get privacy status"""
    try:
        return get_privacy_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/privacy/level")
async def api_set_privacy_level(request: PrivacyLevelRequest):
    """Set privacy level"""
    try:
        manager = get_context_manager()
        manager.set_privacy_level(request.level)
        
        return {"success": True, "privacy_level": request.level}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/privacy/clear")
async def api_clear_sensitive_data():
    """Clear all sensitive data"""
    try:
        manager = get_context_manager()
        manager.clear_sensitive_data()
        
        return {"success": True, "message": "Sensitive data cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== DAILY LOGS ====================

@router.get("/logs/today")
async def api_get_today_logs():
    """Get today's activity logs"""
    try:
        from pathlib import Path
        import json
        
        log_file = Path(__file__).parent / "daily_logs" / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        
        if not log_file.exists():
            return {"logs": []}
        
        logs = []
        with open(log_file, 'r') as f:
            for line in f:
                logs.append(json.loads(line))
        
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
