"""
Memory API Routes for ClawForge
Provides REST API endpoints for the memory system.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from memory_agent import MemoryManager, MemoryAgent, create_memory_agent, CONFIG

router = APIRouter(prefix="/api/longterm-memory", tags=["Long-Term Memory"])

# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None
_memory_agent: Optional[MemoryAgent] = None


def get_memory_manager() -> MemoryManager:
    """Get or create the global memory manager."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(memory_dir="./workspace")
        _memory_manager.load()
    return _memory_manager


def get_memory_agent() -> MemoryAgent:
    """Get or create the global memory agent."""
    global _memory_agent
    if _memory_agent is None:
        mem_mgr = get_memory_manager()
        _memory_agent = MemoryAgent(mem_mgr, "ClawForge")
        _memory_agent.boot()
    return _memory_agent


# ════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ════════════════════════════════════════════════════════════════

class MemoryStatsResponse(BaseModel):
    """Memory statistics response."""
    total: int
    facts: int
    preferences: int
    sessions: int
    open_tasks: int
    completed_tasks: int
    session_count: int
    total_messages: int
    last_seen: Optional[str] = None


class FactRequest(BaseModel):
    """Add a fact to memory."""
    fact: str


class TaskRequest(BaseModel):
    """Task request."""
    task: str


class ProfileUpdateRequest(BaseModel):
    """Update user profile."""
    name: Optional[str] = None
    location: Optional[str] = None
    occupation: Optional[str] = None
    goals: Optional[str] = None


class MemoryContextResponse(BaseModel):
    """Memory context for system prompt."""
    context: str


# ════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ════════════════════════════════════════════════════════════════

@router.get("/stats", response_model=MemoryStatsResponse)
async def get_memory_stats() -> MemoryStatsResponse:
    """Get memory statistics."""
    try:
        manager = get_memory_manager()
        stats = manager.get_stats()
        return MemoryStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context")
async def get_memory_context() -> MemoryContextResponse:
    """Get memory context block for system prompt injection."""
    try:
        manager = get_memory_manager()
        context = manager.build_context_block()
        return MemoryContextResponse(context=context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/facts")
async def get_facts(limit: int = 20) -> Dict[str, Any]:
    """Get stored facts."""
    try:
        manager = get_memory_manager()
        facts = manager.get_facts(limit)
        return {"facts": facts, "count": len(facts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/facts")
async def add_fact(request: FactRequest) -> Dict[str, str]:
    """Add a fact to memory."""
    try:
        manager = get_memory_manager()
        if manager.mem:
            manager.mem["semantic"]["facts"].append(request.fact)
            manager.mem["semantic"]["facts"] = manager.mem["semantic"]["facts"][-CONFIG["max_facts"]:]
            manager.save()
            return {"status": "added", "fact": request.fact}
        raise HTTPException(status_code=500, detail="Memory not initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def get_tasks() -> Dict[str, Any]:
    """Get all tasks."""
    try:
        manager = get_memory_manager()
        tasks = manager.get_tasks()
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/open")
async def add_open_task(request: TaskRequest) -> Dict[str, str]:
    """Add an open task."""
    try:
        manager = get_memory_manager()
        if manager.mem:
            manager.mem["tasks"]["open"].append(request.task)
            manager.save()
            return {"status": "added", "task": request.task}
        raise HTTPException(status_code=500, detail="Memory not initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/complete")
async def complete_task(request: TaskRequest) -> Dict[str, Any]:
    """Mark a task as completed."""
    try:
        manager = get_memory_manager()
        if manager.mem:
            task_text = request.task.lower()
            for i, task in enumerate(manager.mem["tasks"]["open"]):
                if task_text in task.lower():
                    completed = manager.mem["tasks"]["open"].pop(i)
                    manager.mem["tasks"]["completed"].append(completed)
                    manager.save()
                    return {"status": "completed", "task": completed}
            raise HTTPException(status_code=404, detail="Task not found")
        raise HTTPException(status_code=500, detail="Memory not initialized")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile")
async def update_profile(request: ProfileUpdateRequest) -> Dict[str, Any]:
    """Update user profile."""
    try:
        manager = get_memory_manager()
        if manager.mem:
            updates = {}
            if request.name is not None:
                manager.mem["semantic"]["profile"]["name"] = request.name
                updates["name"] = request.name
            if request.location is not None:
                manager.mem["semantic"]["profile"]["location"] = request.location
                updates["location"] = request.location
            if request.occupation is not None:
                manager.mem["semantic"]["profile"]["occupation"] = request.occupation
                updates["occupation"] = request.occupation
            if request.goals is not None:
                manager.mem["semantic"]["profile"]["goals"] = request.goals
                updates["goals"] = request.goals
            manager.save()
            return {"status": "updated", **updates}
        raise HTTPException(status_code=500, detail="Memory not initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile")
async def get_profile() -> Dict[str, Any]:
    """Get user profile."""
    try:
        manager = get_memory_manager()
        if manager.mem:
            return manager.mem["semantic"]["profile"]
        raise HTTPException(status_code=500, detail="Memory not initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions")
async def get_sessions(limit: int = 10) -> Dict[str, Any]:
    """Get recent sessions."""
    try:
        manager = get_memory_manager()
        if manager.mem:
            sessions = manager.mem["episodic"]["sessions"][-limit:]
            return {"sessions": sessions, "count": len(sessions)}
        raise HTTPException(status_code=500, detail="Memory not initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract")
async def extract_memory_from_history(history: List[Dict[str, str]]) -> Dict[str, Any]:
    """Extract memory from conversation history."""
    try:
        manager = get_memory_manager()
        # Try to import anthropic for extraction
        try:
            import anthropic
            client = anthropic.Anthropic()
        except ImportError:
            return {"error": "Anthropic client not available"}
        
        extracted = manager.extract_from_conversation(history, client)
        if extracted:
            return {"status": "extracted", "data": extracted}
        return {"status": "no_new_data"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update")
async def update_memory(extracted: Dict[str, Any], message_count: int = 0) -> Dict[str, str]:
    """Update memory with extracted data."""
    try:
        manager = get_memory_manager()
        await manager.update(extracted, message_count)
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/boot")
async def boot_memory_agent(agent_name: str = "ClawForge") -> Dict[str, Any]:
    """Boot the memory agent."""
    try:
        agent = get_memory_agent()
        is_returning = agent.memory.mem["meta"]["session_count"] > 0
        return {
            "status": "booted",
            "agent_name": agent.agent_name,
            "is_returning": is_returning,
            "session_count": agent.memory.mem["meta"]["session_count"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-prompt")
async def get_system_prompt() -> Dict[str, str]:
    """Get the system prompt with memory injection."""
    try:
        agent = get_memory_agent()
        return {"system_prompt": agent.get_system_prompt()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_all_memory() -> Dict[str, str]:
    """Clear all memory."""
    try:
        manager = get_memory_manager()
        manager.clear()
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save")
async def force_save_memory() -> Dict[str, str]:
    """Force save memory to disk."""
    try:
        manager = get_memory_manager()
        manager.save()
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════
# EXAMPLE CURL COMMANDS
# ════════════════════════════════════════════════════════════════
EXAMPLE_COMMANDS = """
# Get memory stats
curl http://127.0.0.1:8000/api/memory/stats

# Get memory context for system prompt
curl http://127.0.0.1:8000/api/memory/context

# Add a fact
curl -X POST http://127.0.0.1:8000/api/memory/facts -H "Content-Type: application/json" -d '{"fact": "User prefers concise answers"}'

# Get all tasks
curl http://127.0.0.1:8000/api/memory/tasks

# Add open task
curl -X POST http://127.0.0.1:8000/api/memory/tasks/open -H "Content-Type: application/json" -d '{"task": "Build memory system"}'

# Update profile
curl -X POST http://127.0.0.1:8000/api/memory/profile -H "Content-Type: application/json" -d '{"name": "Amir", "occupation": "Developer"}'

# Clear all memory
curl -X DELETE http://127.0.0.1:8000/api/memory/clear
"""


@router.get("/examples")
async def get_examples() -> Dict[str, str]:
    """Get example curl commands."""
    return {"examples": EXAMPLE_COMMANDS.strip()}
