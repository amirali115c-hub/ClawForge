# Advanced System Prompt for ClawForge
ADVANCED_SYSTEM_PROMPT = """You are ClawForge, an advanced AI assistant with deep understanding capabilities.

## Your Core Capabilities

**🔍 Advanced Understanding**
- Understand complex, multi-part questions
- Extract intent from natural language
- Handle ambiguous queries by asking clarifying questions
- Remember context from entire conversation
- Connect ideas across multiple messages

**🧠 Reasoning & Analysis**
- Break down complex problems step-by-step
- Consider multiple perspectives before answering
- Explain your reasoning process when helpful
- Identify assumptions and edge cases
- Provide structured, logical responses

**💬 Communication Style**
- Be direct and concise when possible
- Use examples to clarify complex concepts
- Adapt tone to match the conversation
- Acknowledge uncertainty when appropriate
- Ask follow-up questions when helpful

**🔧 Your Tools (Use them proactively!)**
- **Web Search** (`web_search`) - Get current information
- **Memory** (`add_memory`, `get_memories`) - Remember important things
- **Code** (`CodeRunner.run_python_file`) - Execute Python code
- **Files** (`read_file_content`, `edit_file_content`) - Work with files
- **Planning** (`generate_plan`) - Create multi-step plans

## How to Respond

1. **Understand First** - What is the user really asking?
2. **Check Context** - What have we discussed before?
3. **Use Tools** - Don't guess, search/code/fetch when needed
4. **Reason Through It** - Show your thinking for complex topics
5. **Be Helpful** - Give complete, actionable answers

## Examples

User: "Search for the latest Python AI news, remember it, and write a summary to a file"
→ Use: web_search → add_memory → write file

User: "Why is my code giving this error?"  
→ Ask for code or read file → analyze → explain fix

User: "Plan a week-long trip to Europe"
→ Ask clarifying questions → generate_plan → execute steps

---

Remember: Understand deeply, reason clearly, use your tools, be helpful."""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Add current directory to path for imports
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

# Add context module to path for context integration
CONTEXT_DIR = Path(__file__).parent.parent / "context"
if str(CONTEXT_DIR) not in sys.path:
    sys.path.insert(0, str(CONTEXT_DIR))

# Import context integration
try:
    from context_integration import init_context_system, add_context_routes
    CONTEXT_AVAILABLE = True
    print("[CONTEXT] Context integration module loaded successfully")
except ImportError as e:
    CONTEXT_AVAILABLE = False
    print(f"Warning: Context system not available: {e}")
from features import (
    get_memory_stats,
    search_memories,
    add_memory,
    get_memories,
    delete_memory,
    get_privacy_settings,
    update_privacy_settings,
    export_memory_data,
    import_memory_data,
    clear_memory_data,
    add_conversation,
    get_conversations,
    longterm_memory,
    web_search,
    fetch_url,
    get_git_status,
    git_commit,
    text_to_speech,
    list_voices,
    read_file_content,
    edit_file_content,
    generate_plan,
)

# ============================================================================
# APP LIFESPAN
# ============================================================================

# Global instances
task_manager = None
websocket_connections: List[WebSocket] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan handler."""
    global task_manager
    
    # Initialize on startup
    from task_manager import TaskManager
    task_manager = TaskManager(broadcast_fn=broadcast)
    
    # Initialize context system (conversation continuity)
    if CONTEXT_AVAILABLE:
        try:
            import sys
            sys.stderr.write("[CONTEXT] Initializing context system...\n")
            sys.stderr.flush()
            init_context_system()
            sys.stderr.write("[CONTEXT] Adding context routes...\n")
            sys.stderr.flush()
            add_context_routes(app)
            sys.stderr.write("[CONTEXT] Context system ready\n")
            sys.stderr.flush()
        except Exception as e:
            import sys
            sys.stderr.write(f"[CONTEXT] Error: {e}\n")
            sys.stderr.flush()
    
    print("ClawForge API started")
    print("   Dashboard: http://127.0.0.1:7860")
    print("   API Docs: http://127.0.0.1:7860/docs")
    
    yield
    
    # Cleanup on shutdown
    print("ClawForge API stopped")

app = FastAPI(
    title="ClawForge API",
    description="Production-grade Autonomous AI Agent Framework",
    version="4.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# WEBSOCKET HANDLING
# ============================================================================

async def broadcast(message: Dict[str, Any]):
    """Broadcast message to all connected WebSocket clients."""
    disconnected = []
    
    for ws in websocket_connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)
    
    # Remove disconnected clients
    for ws in disconnected:
        if ws in websocket_connections:
            websocket_connections.remove(ws)

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for real-time log streaming."""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CreateTaskRequest(BaseModel):
    """Request model for creating a task."""
    goal: str
    category: str = "general"

class ApprovalRequest(BaseModel):
    """Request model for approvals."""
    task_id: str
    approval_item: str

class SecurityModeRequest(BaseModel):
    """Request model for changing security mode."""
    mode: str

class ModelSelectRequest(BaseModel):
    """Request model for selecting model."""
    model: str

class ChatRequest(BaseModel):
    """Request model for chat."""
    message: str
    model: str = "qwen/qwen3.5-397b-a17b"
    stream: bool = False

# ============================================================================
# HEALTH ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent": "ClawForge",
        "version": "4.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/status")
async def get_status():
    """Get system status (dashboard home)."""
    global task_manager
    
    if not task_manager:
        from task_manager import TaskManager
        task_manager = TaskManager()
    
    # Check Ollama
    ollama_status = "unknown"
    try:
        from ollama_client import OllamaClient
        client = OllamaClient()
        health = client.health_check()
        ollama_status = health.get("status", "unknown")
    except Exception:
        pass
    
    return {
        "agent": "ClawForge",
        "version": "4.0",
        "security_mode": "LOCKED",
        "active_model": None,
        "risk_score": 0,
        "kill_switch_active": task_manager.kill_switch_active if task_manager else False,
        "cpu_usage": 0,
        "memory_usage": 0,
        "task_stats": task_manager.get_stats() if task_manager else {"total": 0},
        "active_task": None,
        "pending_approvals": task_manager.get_pending_approvals() if task_manager else [],
        "ollama_status": ollama_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# TASK ENDPOINTS
# ============================================================================

@app.post("/api/tasks")
async def create_task(request: CreateTaskRequest):
    """Create a new task."""
    global task_manager
    
    if not task_manager:
        from task_manager import TaskManager
        task_manager = TaskManager(broadcast_fn=broadcast)
    
    task = task_manager.create_task(request.goal, request.category)
    
    return {
        "status": "success",
        "task": task.to_dict()
    }

@app.get("/api/tasks")
async def list_tasks(status: str = None):
    """List all tasks."""
    global task_manager
    
    if not task_manager:
        return {"tasks": []}
    
    return {
        "tasks": task_manager.list_tasks(status),
        "total": len(task_manager.tasks)
    }

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """Get a specific task."""
    global task_manager
    
    if not task_manager:
        raise HTTPException(status_code=404, detail="Task manager not initialized")
    
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"task": task}

@app.post("/api/tasks/{task_id}/start")
async def start_task(task_id: str):
    """Start a task."""
    global task_manager
    
    if not task_manager:
        raise HTTPException(status_code=404, detail="Task manager not initialized")
    
    result = task_manager.start_task(task_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result

@app.post("/api/tasks/{task_id}/pause")
async def pause_task(task_id: str):
    """Pause a running task."""
    global task_manager
    
    if not task_manager:
        raise HTTPException(status_code=404, detail="Task manager not initialized")
    
    result = task_manager.pause_task(task_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result

@app.post("/api/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    """Resume a paused task."""
    global task_manager
    
    if not task_manager:
        raise HTTPException(status_code=404, detail="Task manager not initialized")
    
    result = task_manager.resume_task(task_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result

@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a task."""
    global task_manager
    
    if not task_manager:
        raise HTTPException(status_code=404, detail="Task manager not initialized")
    
    result = task_manager.cancel_task(task_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result

@app.post("/api/tasks/{task_id}/approve")
async def approve_task(request: ApprovalRequest):
    """Grant approval for a task."""
    global task_manager
    
    if not task_manager:
        raise HTTPException(status_code=404, detail="Task manager not initialized")
    
    result = task_manager.grant_approval(request.task_id, request.approval_item)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result

@app.post("/api/tasks/{task_id}/deny")
async def deny_task(request: ApprovalRequest):
    """Deny approval for a task."""
    global task_manager
    
    if not task_manager:
        raise HTTPException(status_code=404, detail="Task manager not initialized")
    
    result = task_manager.deny_approval(request.task_id, request.approval_item)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result

# ============================================================================
# APPROVAL ENDPOINTS
# ============================================================================

@app.get("/api/approvals")
async def get_approvals():
    """Get all pending approvals."""
    global task_manager
    
    if not task_manager:
        return {"approvals": []}
    
    return {
        "approvals": task_manager.get_pending_approvals(),
        "total": len(task_manager.get_pending_approvals())
    }

# ============================================================================
# KILL SWITCH ENDPOINTS
# ============================================================================

@app.post("/api/kill")
async def activate_kill_switch():
    """Activate emergency kill switch."""
    global task_manager
    
    if not task_manager:
        raise HTTPException(status_code=404, detail="Task manager not initialized")
    
    result = task_manager.activate_kill_switch()
    
    return result

@app.post("/api/kill/reset")
async def reset_kill_switch():
    """Reset kill switch."""
    global task_manager
    
    if not task_manager:
        raise HTTPException(status_code=404, detail="Task manager not initialized")
    
    result = task_manager.reset_kill_switch()
    
    return result

# ============================================================================
# LOGS ENDPOINTS
# ============================================================================

@app.get("/api/logs")
async def get_logs(limit: int = 100):
    """Get recent log entries."""
    global task_manager
    
    logs = []
    
    # Collect logs from all tasks
    if task_manager:
        for task_id, task in task_manager.tasks.items():
            for log in task.logs[-limit:]:
                log["task_id"] = task_id
                logs.append(log)
    
    # Sort by timestamp
    logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {
        "logs": logs[:limit],
        "total": len(logs)
    }

@app.get("/api/tasks/{task_id}/logs")
async def get_task_logs(task_id: str, limit: int = 100):
    """Get logs for a specific task."""
    global task_manager
    
    if not task_manager:
        raise HTTPException(status_code=404, detail="Task manager not initialized")
    
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task_id,
        "logs": task_manager.tasks[task_id].logs[-limit:],
        "total": len(task_manager.tasks[task_id].logs)
    }

# ============================================================================
# FILE EXPLORER ENDPOINTS
# ============================================================================

@app.get("/api/files")
async def list_files(path: str = "./workspace"):
    """List workspace directory."""
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Path not found")
    
    if not path.startswith("./workspace") and path != "./workspace":
        raise HTTPException(status_code=403, detail="Access outside workspace not allowed")
    
    files = []
    folders = []
    
    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                folders.append({
                    "name": item,
                    "path": item_path,
                    "type": "folder"
                })
            else:
                files.append({
                    "name": item,
                    "path": item_path,
                    "size": os.path.getsize(item_path),
                    "type": "file"
                })
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return {
        "path": path,
        "files": files,
        "folders": folders,
        "file_count": len(files),
        "folder_count": len(folders)
    }

@app.get("/api/files/read")
async def read_file(path: str):
    """Read a file."""
    from file_manager import FileManager
    
    if not path.startswith("./workspace"):
        raise HTTPException(status_code=403, detail="Access outside workspace not allowed")
    
    result = FileManager.read_file(path)
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result.get("error"))
    
    return result

# ============================================================================
# CHAT ENDPOINT (NVIDIA API) - HARDCODED FOR AMIR
# ============================================================================

# Amir's NVIDIA API credentials
NVIDIA_API_KEY = "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"
DEFAULT_MODEL = "qwen/qwen3.5-397b-a17b"

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Chat with AI using NVIDIA API (Qwen3.5-397B).
    Uses Amir's hardcoded API credentials.
    """
    from nvidia_client import NvidiaAPIClient
    
    try:
        client = NvidiaAPIClient(NVIDIA_API_KEY)
        
        # Build messages with advanced system prompt
        messages = [
            {"role": "system", "content": ADVANCED_SYSTEM_PROMPT},
            {"role": "user", "content": request.message}
        ]
        
        # Send to NVIDIA API
        model = request.model or DEFAULT_MODEL
        response = client.chat(messages, model)
        
        return {
            "status": "success",
            "response": response,
            "model": model,
            "provider": "NVIDIA API"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to communicate with NVIDIA API"
        }

# ============================================================================
# CHAT ENDPOINT (GLM API) - ADD YOUR KEY BELOW
# ============================================================================

# GLM API Key - Set this to enable GLM-5
GLM_API_KEY = ""  # Paste your GLM API key here
GLM_DEFAULT_MODEL = "glm-5"

@app.post("/api/chat/glm")
async def chat_glm(request: ChatRequest):
    """
    Chat with AI using GLM-5 (Zhipu AI).
    """
    from glm_client import GLMAPIClient
    
    if not GLM_API_KEY:
        return {
            "status": "error",
            "error": "GLM_API_KEY not set",
            "message": "Edit api.py and set GLM_API_KEY"
        }
    
    try:
        client = GLMAPIClient(GLM_API_KEY)
        
        messages = [
            {"role": "system", "content": ADVANCED_SYSTEM_PROMPT},
            {"role": "user", "content": request.message}
        ]
        
        model = request.model or GLM_DEFAULT_MODEL
        response = client.chat(messages, model)
        
        return {
            "status": "success",
            "response": response,
            "model": model,
            "provider": "GLM (Zhipu AI)"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to communicate with GLM API"
        }

# ============================================================================
# Z-AI GLM5 ENDPOINT
# ============================================================================

ZAI_GLM5_API_KEY = "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"

@app.post("/api/chat/glm5")
async def chat_glm5(request: ChatRequest):
    """
    Chat with z-ai/glm5 model via NVIDIA API.
    """
    from nvidia_client import NvidiaAPIClient
    
    if not ZAI_GLM5_API_KEY:
        return {
            "status": "error",
            "error": "ZAI_GLM5_API_KEY not set",
            "message": "Edit api.py and set ZAI_GLM5_API_KEY"
        }
    
    try:
        client = NvidiaAPIClient(ZAI_GLM5_API_KEY)
        
        messages = [
            {"role": "system", "content": ADVANCED_SYSTEM_PROMPT},
            {"role": "user", "content": request.message}
        ]
        
        response = client.chat(messages, "z-ai/glm5")
        
        return {
            "status": "success",
            "response": response,
            "model": "z-ai/glm5",
            "provider": "NVIDIA (z-ai)"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to communicate with z-ai API"
        }

# ============================================================================
# QWEN QWEN3.5-397B ENDPOINT
# ============================================================================

QWEN_API_KEY = "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"

@app.post("/api/chat/qwen")
async def chat_qwen(request: ChatRequest):
    """
    Chat with qwen/qwen3.5-397b-a17b model via NVIDIA API.
    """
    from nvidia_client import NvidiaAPIClient
    
    if not QWEN_API_KEY:
        return {
            "status": "error",
            "error": "QWEN_API_KEY not set",
            "message": "Edit api.py and set QWEN_API_KEY"
        }
    
    try:
        client = NvidiaAPIClient(QWEN_API_KEY)
        
        messages = [
            {"role": "system", "content": ADVANCED_SYSTEM_PROMPT},
            {"role": "user", "content": request.message}
        ]
        
        response = client.chat(messages, "qwen/qwen3.5-397b-a17b")
        
        return {
            "status": "success",
            "response": response,
            "model": "qwen/qwen3.5-397b-a17b",
            "provider": "NVIDIA (Qwen)"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to communicate with Qwen API"
        }

# ============================================================================
# NVIDIA BUILD API ENDPOINT
# ============================================================================

NVIDIA_BUILD_API_KEY = "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"

@app.post("/api/chat/nvidia-build")
async def chat_nvidia_build(request: ChatRequest):
    """
    Chat with NVIDIA Build model via NVIDIA API.
    """
    from nvidia_client import NvidiaAPIClient
    
    if not NVIDIA_BUILD_API_KEY:
        return {
            "status": "error",
            "error": "NVIDIA_BUILD_API_KEY not set",
            "message": "Edit api.py and set NVIDIA_BUILD_API_KEY"
        }
    
    try:
        client = NvidiaAPIClient(NVIDIA_BUILD_API_KEY)
        
        messages = [
            {"role": "system", "content": ADVANCED_SYSTEM_PROMPT},
            {"role": "user", "content": request.message}
        ]
        
        response = client.chat(messages, "qwen/qwen3.5-397b-a17b")
        
        return {
            "status": "success",
            "response": response,
            "model": "NVIDIABuild-Autogen-60",
            "provider": "NVIDIA Build"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to communicate with NVIDIA Build API"
        }

# ============================================================================
# DEEPSEEK V3.2 ENDPOINT (Thinking Enabled)
# ============================================================================

DEEPSEEK_API_KEY = "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"

@app.post("/api/chat/deepseek")
async def chat_deepseek(request: ChatRequest):
    """
    Chat with deepseek-v3.2 model (thinking enabled).
    """
    import httpx
    
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-ai/deepseek-v3.2",
        "messages": [
            {"role": "system", "content": ADVANCED_SYSTEM_PROMPT},
            {"role": "user", "content": request.message}
        ],
        "temperature": 1,
        "top_p": 0.95,
        "max_tokens": 8192,
        "extra_body": {"chat_template_kwargs": {"thinking": True}},
        "stream": False
    }
    
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract response (including reasoning if available)
            content = data["choices"][0]["message"]["content"]
            
            return {
                "status": "success",
                "response": content,
                "model": "deepseek-ai/deepseek-v3.2",
                "provider": "NVIDIA (DeepSeek V3.2 with Thinking)"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to communicate with DeepSeek API"
        }

# ============================================================================
# MODEL ENDPOINTS
# ============================================================================

@app.get("/api/models")
async def get_models():
    """Get available models."""
    from ollama_client import OllamaClient, SUPPORTED_MODELS
    
    client = OllamaClient()
    health = client.health_check()
    
    return {
        "supported_models": SUPPORTED_MODELS,
        "available_models": health.get("available_models", []),
        "active_model": client.get_active_model(),
        "ollama_status": health.get("status", "unknown")
    }

@app.post("/api/models/select")
async def select_model(request: ModelSelectRequest):
    """Change active model."""
    from ollama_client import OllamaClient
    
    client = OllamaClient()
    result = client.set_model(request.model)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result

# ============================================================================
# BYTEDANCE SEED-OSS ENDPOINT (Thinking Enabled)
# ============================================================================

BYTEDANCE_API_KEY = "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"

@app.post("/api/chat/bytedance")
async def chat_bytedance(request: ChatRequest):
    """
    Chat with Bytedance Seed-OSS-36B model (thinking enabled).
    """
    import httpx
    
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {BYTEDANCE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "bytedance/seed-oss-36b-instruct",
        "messages": [
            {"role": "system", "content": ADVANCED_SYSTEM_PROMPT},
            {"role": "user", "content": request.message}
        ],
        "temperature": 1.1,
        "top_p": 0.95,
        "max_tokens": 4096,
        "extra_body": {"thinking_budget": -1},
        "stream": False
    }
    
    try:
        if not BYTEDANCE_API_KEY:
            return {
                "status": "error",
                "message": "BYTEDANCE_API_KEY not set. Add your key to api.py"
            }
        
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            return {
                "status": "success",
                "response": content,
                "model": "bytedance/seed-oss-36b-instruct",
                "provider": "NVIDIA API (Bytedance)"
            }
        else:
            return {
                "status": "error",
                "message": f"API error: {response.status_code} - {response.text[:200]}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# ============================================================================
# LONG-TERM MEMORY ENDPOINTS (With Privacy Controls)
# ============================================================================

class AddMemoryRequest(BaseModel):
    content: str
    category: str = "fact"
    importance: int = 5
    tags: List[str] = []

class UpdatePrivacyRequest(BaseModel):
    auto_save: bool = True
    encrypt_sensitive: bool = True
    remember_facts: bool = True
    remember_preferences: bool = True
    remember_context: bool = True
    auto_clear_conversations: bool = False
    max_conversations: int = 100

@app.get("/api/memory/stats")
async def memory_stats():
    """Get comprehensive memory statistics."""
    from features import get_memory_stats as gms
    return gms()

@app.get("/api/memory/all")
async def list_memories(category: str = None):
    """Get all memories, optionally filtered by category."""
    from features import get_memories
    memories = get_memories(category)
    return {"memories": memories, "total": len(memories)}

@app.post("/api/memory/add")
async def create_memory(request: AddMemoryRequest):
    """Add a new memory."""
    from features import add_memory as am
    memory = am(
        content=request.content,
        category=request.category,
        importance=request.importance,
        tags=request.tags
    )
    return {"status": "success", "memory": memory}

@app.get("/api/memory/search")
async def search_memories_endpoint(query: str, category: str = None):
    """Search memories."""
    from features import search_memories as sm
    results = sm(query, category)
    return {"results": results, "total": len(results)}

@app.delete("/api/memory/{memory_id}")
async def remove_memory(memory_id: str):
    """Delete a specific memory."""
    from features import delete_memory as dm
    success = dm(memory_id)
    if success:
        return {"status": "success", "message": "Memory deleted"}
    else:
        raise HTTPException(status_code=404, detail="Memory not found")

@app.delete("/api/memory/category/{category}")
async def clear_category(category: str):
    """Clear all memories in a category."""
    from features import longterm_memory
    count = longterm_memory.clear_category(category)
    return {"status": "success", "deleted_count": count}

# ----------------- Conversations -----------------

@app.get("/api/memory/conversations")
async def list_conversations(limit: int = 50):
    """Get conversation history."""
    from features import get_conversations as gc
    conversations = gc(limit)
    return {"conversations": conversations, "total": len(conversations)}

@app.post("/api/memory/conversations/add")
async def save_conversation(role: str, content: str, summary: str = None):
    """Add a conversation message."""
    from features import add_conversation as ac
    ac(role, content, summary)
    return {"status": "success"}

@app.delete("/api/memory/conversations/clear")
async def clear_all_conversations():
    """Clear all conversations."""
    from features import longterm_memory
    longterm_memory.clear_conversations()
    return {"status": "success", "message": "Conversations cleared"}

# ----------------- Privacy Controls -----------------

@app.get("/api/memory/privacy")
async def view_privacy_settings():
    """Get privacy settings."""
    from features import get_privacy_settings as gps
    return gps()

@app.post("/api/memory/privacy")
async def modify_privacy_settings(request: UpdatePrivacyRequest):
    """Update privacy settings."""
    from features import update_privacy_settings as ups
    settings = request.model_dump()
    updated = ups(settings)
    return {"status": "success", "settings": updated}

@app.get("/api/memory/export")
async def export_all_data(include_sensitive: bool = False):
    """Export all memory data."""
    from features import export_memory_data as emd
    data = emd(include_sensitive)
    return data

@app.post("/api/memory/import")
async def import_all_data(data: Dict, merge: bool = True):
    """Import memory data."""
    from features import import_memory_data as imd
    result = imd(data, merge)
    return {"status": "success", **result}

@app.delete("/api/memory/clear")
async def wipe_all_memory():
    """Clear all memory data (memories and conversations)."""
    from features import clear_memory_data as cmd
    cmd()
    return {"status": "success", "message": "All memory cleared"}

@app.post("/api/memory/extract")
async def auto_extract_facts(text: str):
    """Extract and save facts from text."""
    from features import longterm_memory
    longterm_memory.extract_and_save_facts(text)
    return {"status": "success", "message": "Facts extracted and saved"}

# ============================================================================
# SECURITY ENDPOINTS
# ============================================================================

@app.get("/api/security")
async def get_security_status():
    """Get security status."""
    global task_manager
    
    return {
        "mode": "LOCKED",
        "kill_switch_active": task_manager.kill_switch_active if task_manager else False,
        "risk_threshold": 50,
        "current_risk_score": 0
    }

@app.post("/api/security/mode")
async def change_security_mode(request: SecurityModeRequest):
    """Change security mode."""
    valid_modes = ["LOCKED", "SAFE", "DEVELOPER"]
    
    if request.mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Valid modes: {valid_modes}")
    
    return {
        "status": "success",
        "mode": request.mode,
        "message": f"Security mode changed to {request.mode}"
    }

# ============================================================================
# TOOL EXECUTION ENDPOINT
# ============================================================================

@app.post("/api/tools/call")
async def call_tool(tool_name: str, args: Dict[str, Any]):
    """Execute a tool call."""
    from tools import ToolRouter, SecurityMode
    
    router = ToolRouter(security_mode=SecurityMode.LOCKED)
    result = router.call(tool_name, args)
    
    if result.get("status") == "blocked":
        raise HTTPException(status_code=403, detail=result.get("error"))
    
    if result.get("status") == "approval_required":
        raise HTTPException(status_code=403, detail=result.get("error"))
    
    return result

# ============================================================================
# NEW FEATURES ENDPOINTS
# ============================================================================

# Memory Endpoints
@app.get("/api/memory/stats")
async def memory_stats():
    """Get memory statistics."""
    return get_memory_stats()

@app.get("/api/memory/conversations")
async def list_conversations(limit: int = 10):
    """Get recent conversations."""
    return {"conversations": []}

@app.post("/api/memory/search")
async def search_memory_endpoint(request: Dict):
    """Search through memory."""
    query = request.get("query", "")
    results = search_memory(query)
    return {"results": results}

# Web Search Endpoints
class SearchRequest(BaseModel):
    query: str
    num_results: int = 10

@app.post("/api/search")
async def web_search_endpoint(request: SearchRequest):
    """Search the web."""
    results = web_search(request.query, request.num_results)
    return {"results": results}

@app.post("/api/fetch")
async def fetch_url_endpoint(request: Dict):
    """Fetch a URL."""
    url = request.get("url", "")
    return fetch_url(url)

# Git Endpoints
@app.get("/api/git/status")
async def git_status_endpoint():
    """Get git status."""
    return get_git_status()

@app.post("/api/git/commit")
async def git_commit_endpoint(request: Dict):
    """Create a git commit."""
    message = request.get("message", "Update")
    return git_commit(message)

# TTS Endpoints
class TTSRequest(BaseModel):
    text: str
    filename: str = None

@app.post("/api/tts/speak")
async def tts_speak_endpoint(request: TTSRequest):
    """Generate speech from text."""
    return text_to_speech(request.text, request.filename)

@app.get("/api/tts/voices")
async def tts_voices_endpoint():
    """List available TTS voices."""
    return {"voices": list_voices()}

# File Editor Endpoints
class ReadFileRequest(BaseModel):
    file_path: str

@app.post("/api/files/read")
async def read_file_endpoint(request: ReadFileRequest):
    """Read file content."""
    return read_file_content(request.file_path)

class EditFileRequest(BaseModel):
    file_path: str
    old_text: str
    new_text: str

@app.post("/api/files/edit")
async def edit_file_endpoint(request: EditFileRequest):
    """Edit a file with search/replace."""
    return edit_file_content(request.file_path, request.old_text, request.new_text)

# Planner Endpoints
class GeneratePlanRequest(BaseModel):
    goal: str

@app.post("/api/plans/generate")
async def generate_plan_endpoint(request: GeneratePlanRequest):
    """Generate a plan for a goal."""
    plan = generate_plan(request.goal)
    return plan.to_dict()

# ============================================================================
# PROMPT ENGINE API ROUTES
# ============================================================================

# Import and add prompt engine routes
try:
    from prompt_api import router as prompt_router
    app.include_router(prompt_router)
    print("[PROMPT] Advanced Prompt Engine routes loaded")
except ImportError as e:
    print(f"[PROMPT] Warning: Prompt Engine not available: {e}")

# ============================================================================
# MEMORY SYSTEM API ROUTES
# ============================================================================

# Import and add memory system routes
try:
    from memory_api import router as memory_router
    app.include_router(memory_router)
    print("[MEMORY] Memory System routes loaded")
except ImportError as e:
    print(f"[MEMORY] Warning: Memory System not available: {e}")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("CLAWFORGE v4.0 - FastAPI Backend")
    print("="*60)
    print("\nStarting server...")
    print("Dashboard will be available at: http://127.0.0.1:7860")
    print("API Documentation: http://127.0.0.1:7860/docs")
    print("="*60 + "\n")
    
    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=7860,
        reload=True
    )
