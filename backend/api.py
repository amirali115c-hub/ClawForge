# Advanced System Prompt for Leo 2.0
ADVANCED_SYSTEM_PROMPT = """You are Leo 2.0, an advanced self-learning AI agent with deep understanding capabilities.

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
# NEW: PROMPT ENGINE & CONTEXT MANAGEMENT
# ============================================================================

try:
    from prompt_engine import PromptUnderstandingEngine, IntentType, ComplexityLevel
    PROMPT_ENGINE_AVAILABLE = True
    print("[PROMPT-ENGINE] Advanced Prompt Understanding loaded")
except ImportError as e:
    PROMPT_ENGINE_AVAILABLE = False
    print(f"[PROMPT-ENGINE] Warning: {e}")

try:
    from response_delivery import ResponseDeliveryEngine, ChannelType, FormattedResponse
    RESPONSE_ENGINE_AVAILABLE = True
    print("[RESPONSE-ENGINE] Response Delivery loaded")
except ImportError as e:
    RESPONSE_ENGINE_AVAILABLE = False
    print(f"[RESPONSE-ENGINE] Warning: {e}")

try:
    from context_manager import ContextManager
    CONTEXT_MGR_AVAILABLE = True
    context_manager = ContextManager()
    print("[CONTEXT-MGR] Context Manager loaded")
except ImportError as e:
    CONTEXT_MGR_AVAILABLE = False
    context_manager = None
    print(f"[CONTEXT-MGR] Warning: {e}")

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
    
    print("Leo 2.0 API started")
    print("   Dashboard: http://127.0.0.1:7860")
    print("   API Docs: http://127.0.0.1:7860/docs")
    
    yield
    
    # Cleanup on shutdown
    print("Leo 2.0 API stopped")

app = FastAPI(
    title="Leo 2.0 API",
    description="Self-Learning AI Agent with NEURON v2.0",
    version="2.0",
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
        "agent": "Leo 2.0",
        "version": "2.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

from fastapi import Request

# Task Progress Tracker
task_progress = {
    "status": "idle",
    "task": "",
    "time_remaining": 0,
    "total_time": 0,
    "steps": []
}

@app.get("/api/task/status")
async def get_task_status():
    """Get current task progress for timer display."""
    return task_progress

@app.post("/api/task/start")
async def start_task(request: Request):
    """Start a new task with timer."""
    try:
        body = await request.json()
    except:
        body = {}
    task_progress["status"] = "working"
    task_progress["task"] = body.get("task", "Task")
    task_progress["total_time"] = body.get("duration", 3600)
    task_progress["time_remaining"] = task_progress["total_time"]
    task_progress["steps"] = body.get("steps", [])
    return {"status": "started"}

@app.post("/api/task/update")
async def update_task(request: Request):
    """Update task progress."""
    body = await request.json()
    if "time_remaining" in body:
        task_progress["time_remaining"] = body["time_remaining"]
    if "step" in body:
        for step in task_progress["steps"]:
            step["done"] = True
            if step["name"] == body["step"]:
                break
        for step in task_progress["steps"]:
            step["active"] = False
        for step in task_progress["steps"]:
            if not step.get("done"):
                step["active"] = True
                break
    return {"status": "updated"}

@app.post("/api/task/complete")
async def complete_task():
    """Mark task as complete."""
    task_progress["status"] = "idle"
    task_progress["task"] = ""
    task_progress["time_remaining"] = 0
    task_progress["steps"] = []
    return {"status": "completed"}

# Sentiment Analysis
SENTIMENT_AVAILABLE = False
try:
    from sentiment_engine import SentimentAnalyzer, analyze_sentiment, get_response_tone
    SENTIMENT_AVAILABLE = True
    print("[SENTIMENT] Sentiment Analysis loaded")
except ImportError as e:
    print(f"[SENTIMENT] Warning: {e}")

@app.post("/api/sentiment/analyze")
async def analyze_text_sentiment(request: Request):
    """Analyze sentiment of input text."""
    try:
        body = await request.json()
    except:
        body = {}
    
    text = body.get("text", "")
    if not text:
        return {"error": "No text provided"}
    
    if not SENTIMENT_AVAILABLE:
        return {"error": "Sentiment engine not available"}
    
    result = analyze_sentiment(text)
    return result

@app.get("/api/sentiment/tone")
async def get_sentiment_tone(text: str):
    """Get appropriate response tone based on sentiment."""
    if not SENTIMENT_AVAILABLE:
        return {"error": "Sentiment engine not available"}
    
    tone = get_response_tone(text)
    return {"tone": tone}

# Tool Calling
TOOL_CALLING_AVAILABLE = False
try:
    from tool_calling_engine import ToolCallingEngine, should_use_tool, get_tool_stats
    TOOL_CALLING_AVAILABLE = True
    print("[TOOL-CALLING] Tool Calling Engine loaded")
except ImportError as e:
    print(f"[TOOL-CALLING] Warning: {e}")

@app.post("/api/tools/detect")
async def detect_tool_use(request: Request):
    """Detect if a tool should be used for the given message."""
    try:
        body = await request.json()
    except:
        body = {}
    
    message = body.get("message", "")
    if not message:
        return {"error": "No message provided"}
    
    if not TOOL_CALLING_AVAILABLE:
        return {"error": "Tool calling engine not available"}
    
    tool_call = should_use_tool(message)
    if tool_call:
        return {
            "should_use_tool": True,
            "tool": tool_call.tool.value,
            "confidence": tool_call.confidence,
            "reason": tool_call.reason,
            "parameters": tool_call.parameters
        }
    else:
        return {
            "should_use_tool": False,
            "tool": "none",
            "confidence": 0,
            "reason": "No tool needed"
        }

@app.get("/api/tools/stats")
async def get_tools_statistics():
    """Get tool calling statistics."""
    if not TOOL_CALLING_AVAILABLE:
        return {"error": "Tool calling engine not available"}
    return get_tool_stats()

# Conversation Summarizer
SUMMARIZER_AVAILABLE = False
try:
    from conversation_summarizer import summarize_conversation, get_resume_summary
    SUMMARIZER_AVAILABLE = True
    print("[SUMMARIZER] Conversation Summarizer loaded")
except ImportError as e:
    print(f"[SUMMARIZER] Warning: {e}")

@app.post("/api/conversation/summarize")
async def summarize_convo(request: Request):
    """Summarize a conversation."""
    try:
        body = await request.json()
    except:
        body = {}
    
    messages = body.get("messages", [])
    
    if not SUMMARIZER_AVAILABLE:
        return {"error": "Summarizer not available"}
    
    result = summarize_conversation(messages)
    return result

@app.post("/api/conversation/resume")
async def get_resume_convo(request: Request):
    """Get summary for resuming conversation."""
    try:
        body = await request.json()
    except:
        body = {}
    
    messages = body.get("messages", [])
    
    if not SUMMARIZER_AVAILABLE:
        return {"error": "Summarizer not available"}
    
    result = get_resume_summary(messages)
    return {"resume_summary": result}

@app.get("/api/health/detailed")
async def detailed_health_check():
    """Detailed health check with all service statuses."""
    from features import get_memory_stats
    
    # Check module availability
    neuron_status = "unknown"
    router_status = "unknown"
    vector_status = "unknown"
    custodian_status = "unknown"
    
    try:
        from neuron_integration import NEURON_AVAILABLE
        neuron_status = "active" if NEURON_AVAILABLE else "inactive"
    except:
        neuron_status = "inactive"
    
    try:
        from smart_router import SMART_ROUTER_AVAILABLE
        router_status = "active" if SMART_ROUTER_AVAILABLE else "inactive"
    except:
        router_status = "inactive"
    
    try:
        from vector_memory import VECTOR_MEMORY_AVAILABLE
        vector_status = "active" if VECTOR_MEMORY_AVAILABLE else "inactive"
    except:
        vector_status = "inactive"
    
    try:
        from custodian import CUSTODIAN_AVAILABLE
        custodian_status = "active" if CUSTODIAN_AVAILABLE else "inactive"
    except:
        custodian_status = "inactive"
    
    try:
        memory_stats = get_memory_stats()
    except:
        memory_stats = {"error": "Unable to fetch memory stats"}
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "services": {
            "api": {"status": "running", "port": 7860},
            "neuron": {"status": neuron_status},
            "smart_router": {"status": router_status},
            "vector_memory": {"status": vector_status},
            "custodian": {"status": custodian_status}
        },
        "memory": memory_stats
    }

# ============================================================================
# NEW: PROMPT UNDERSTANDING ENDPOINTS (OpenClaw-style)
# ============================================================================

class ParseRequest(BaseModel):
    message: str
    session_context: Dict = None

class ParseResponse(BaseModel):
    intent_type: str
    complexity: str
    entities: List[str]
    keywords: List[str]
    language: str
    sentiment: str
    urgency: str
    requires_web: bool
    requires_code: bool
    requires_planning: bool
    action_required: bool

@app.post("/api/understand/parse")
async def parse_prompt(request: ParseRequest):
    """
    Parse user prompt using OpenClaw-style understanding engine.
    Returns intent, complexity, entities, and routing information.
    """
    if not PROMPT_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Prompt engine not available")
    
    try:
        engine = PromptUnderstandingEngine()
        parsed = engine.parse(request.message, request.session_context)
        
        return {
            "status": "success",
            "parsed": {
                "intent_type": parsed.intent_type.value,
                "complexity": parsed.complexity.value,
                "entities": parsed.entities,
                "keywords": parsed.keywords,
                "language": parsed.language,
                "sentiment": parsed.sentiment,
                "urgency": parsed.urgency,
                "requires_web": parsed.requires_web,
                "requires_code": parsed.requires_code,
                "requires_planning": parsed.requires_planning,
                "action_required": parsed.action_required,
                "context_needed": parsed.context_needed,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/understand/route")
async def get_routing_info(request: ParseRequest):
    """
    Get model routing information based on prompt understanding.
    Mirrors OpenClaw's model routing mechanism.
    """
    if not PROMPT_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Prompt engine not available")
    
    try:
        engine = PromptUnderstandingEngine()
        parsed = engine.parse(request.message, request.session_context)
        routing = engine.get_routing_info(parsed)
        
        return {
            "status": "success",
            "routing": routing
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/understand/build-prompt")
async def build_system_prompt(request: ParseRequest):
    """
    Build optimized system prompt based on parsed intent.
    """
    if not PROMPT_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Prompt engine not available")
    
    try:
        engine = PromptUnderstandingEngine()
        parsed = engine.parse(request.message, request.session_context)
        
        # Get context if needed
        context_items = []
        if parsed.context_needed and CONTEXT_MGR_AVAILABLE and context_manager:
            context = context_manager.get_prompt_context(parsed.context_needed)
            # Convert to ContextItem objects
            from context_manager import ContextItem as CMContextItem
            for key, mem in context.get('memories', []):
                context_items.append(CMContextItem(
                    key=key,
                    value=mem.get('value', ''),
                    source='memory',
                    category=mem.get('category', 'fact'),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    relevance_score=mem.get('importance', 5) / 5.0,
                ))
        
        prompt = engine.build_system_prompt(parsed, context_items)
        
        return {
            "status": "success",
            "prompt": prompt,
            "parsed": {
                "intent_type": parsed.intent_type.value,
                "complexity": parsed.complexity.value,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# NEW: RESPONSE DELIVERY ENDPOINTS (OpenClaw-style)
# ============================================================================

class DeliverRequest(BaseModel):
    response: str
    channel: str = "webchat"
    intent_type: str = "chat"
    metadata: Dict = None

@app.post("/api/deliver/format")
async def format_response(request: DeliverRequest):
    """
    Format response for specific channel using OpenClaw-style delivery engine.
    """
    if not RESPONSE_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Response engine not available")
    
    try:
        # Map channel string to enum
        channel_map = {
            "webchat": ChannelType.WEBCHAT,
            "terminal": ChannelType.TERMINAL,
            "api": ChannelType.API,
            "markdown": ChannelType.MARKDOWN,
            "html": ChannelType.HTML,
            "plain": ChannelType.PLAIN,
        }
        channel = channel_map.get(request.channel.lower(), ChannelType.WEBCHAT)
        
        engine = ResponseDeliveryEngine()
        formatted = engine.process_response(
            raw_response=request.response,
            channel=channel,
            intent_type=request.intent_type,
            metadata=request.metadata
        )
        
        return {
            "status": "success",
            "formatted": {
                "text": formatted.text,
                "html": formatted.html,
                "markdown": formatted.markdown,
                "channel": formatted.channel.value,
                "metadata": formatted.metadata,
            },
            "word_count": formatted.metadata.get('word_count', 0),
            "char_count": formatted.metadata.get('char_count', 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/deliver/safety-check")
async def safety_check_response(request: DeliverRequest):
    """
    Check response for safety issues.
    """
    if not RESPONSE_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Response engine not available")
    
    try:
        engine = ResponseDeliveryEngine()
        result = engine._safety_check(request.response)
        
        return {
            "status": "success",
            "safety": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# NEW: CONTEXT MANAGEMENT ENDPOINTS
# ============================================================================

class ContextSetRequest(BaseModel):
    key: str
    value: Any
    category: str = "session"

class ContextGetRequest(BaseModel):
    key: str
    default: Any = None

@app.post("/api/context/session/set")
async def set_session_context(request: ContextSetRequest):
    """Set a session context value."""
    if not CONTEXT_MGR_AVAILABLE or not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not available")
    
    try:
        context_manager.set_session(request.key, request.value, request.category)
        return {"status": "success", "key": request.key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/context/session/get")
async def get_session_context(request: ContextGetRequest):
    """Get a session context value."""
    if not CONTEXT_MGR_AVAILABLE or not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not available")
    
    try:
        value = context_manager.get_session(request.key, request.default)
        return {"status": "success", "key": request.key, "value": value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/context/memory/add")
async def add_longterm_memory(request: ContextSetRequest):
    """Add a long-term memory."""
    if not CONTEXT_MGR_AVAILABLE or not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not available")
    
    try:
        key = context_manager.add_memory(
            key=request.key,
            value=request.value,
            category=request.category,
        )
        return {"status": "success", "key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/context/memory/search")
async def search_memories(request: ParseRequest):
    """Search long-term memories."""
    if not CONTEXT_MGR_AVAILABLE or not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not available")
    
    try:
        results = context_manager.search_memories(request.message)
        memories = [
            {"key": key, "data": data, "relevance": len(key) / 10}
            for key, data in results
        ]
        return {"status": "success", "results": memories, "total": len(memories)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/context/conversation/add")
async def add_conversation_turn(request: Dict):
    """Add a conversation turn to history."""
    if not CONTEXT_MGR_AVAILABLE or not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not available")
    
    try:
        context_manager.add_conversation_turn(
            role=request.get('role', 'user'),
            content=request.get('content', '')
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/context/stats")
async def get_context_stats():
    """Get context manager statistics."""
    if not CONTEXT_MGR_AVAILABLE or not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not available")
    
    try:
        return {"status": "success", "stats": context_manager.get_stats()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/context/export")
async def export_all_context():
    """Export all context data."""
    if not CONTEXT_MGR_AVAILABLE or not context_manager:
        raise HTTPException(status_code=503, detail="Context manager not available")
    
    try:
        return {"status": "success", "export": context_manager.export_all()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        "agent": "Leo 2.0",
        "version": "2.0",
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
# NEURON v2.0 SELF-LEARNING ENDPOINTS
# ============================================================================

# Import NEURON integration
try:
    from neuron_integration import neuron_router
    app.include_router(neuron_router)
    print("[NEURON] NEURON v2.0 integration loaded successfully")
except ImportError as e:
    print(f"[NEURON] NEURON integration not available: {e}")

# ============================================================================
# AUTO MEMORY MANAGEMENT
# ============================================================================

try:
    from memory_manager import MemoryMonitor, add_memory_routes
    memory_monitor = MemoryMonitor()
    add_memory_routes(app)
    print("[MEMORY-MGR] Auto Memory Manager loaded")
    MEMORY_MGR_AVAILABLE = True
except ImportError as e:
    print(f"[MEMORY-MGR] Warning: Memory Manager not available: {e}")
    MEMORY_MGR_AVAILABLE = False

# ============================================================================
# OLLAMA LOCAL ENDPOINT (Fast, Local)
# ============================================================================

@app.post("/api/chat/ollama")
async def chat_ollama(request: ChatRequest):
    """
    Chat with local Ollama model (qwen3:8b or others).
    Fast, offline, free - uses ADVANCED_SYSTEM_PROMPT.
    """
    from ollama_client import OllamaClient
    
    try:
        client = OllamaClient()
        
        messages = [
            {"role": "system", "content": ADVANCED_SYSTEM_PROMPT},
            {"role": "user", "content": request.message}
        ]
        
        response = client.chat(messages)
        
        return {
            "status": "success",
            "response": response,
            "model": client.get_active_model() or "qwen3:8b",
            "provider": "Ollama (Local)"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to communicate with Ollama"
        }

# ============================================================================
# SMART MODEL ROUTER (Auto-Switching)
# ============================================================================

try:
    from smart_router import SmartModelRouter, create_router
    smart_router = create_router()
    SMART_ROUTER_AVAILABLE = True
    print("[SMART-ROUTER] Intelligent Model Router loaded")
except ImportError as e:
    print(f"[SMART-ROUTER] Warning: Smart Router not available: {e}")
    SMART_ROUTER_AVAILABLE = False

@app.post("/api/smart/route")
async def smart_route(request: ChatRequest):
    """
    Analyze request and auto-select best model.
    Returns routing decision without switching.
    """
    if not SMART_ROUTER_AVAILABLE:
        return {
            "status": "error",
            "message": "Smart Router not available"
        }
    
    result = smart_router.analyze_and_route(
        message=request.message,
        context=""
    )
    
    return {
        "status": "success",
        "routing": result,
        "current_model": smart_router.current_model
    }

@app.post("/api/smart/switch")
async def smart_switch(request: ChatRequest):
    """
    Auto-switch to optimal model based on request.
    Returns the response from the newly selected model.
    """
    if not SMART_ROUTER_AVAILABLE:
        return {
            "status": "error",
            "message": "Smart Router not available"
        }
    
    # Analyze and get routing decision
    routing = smart_router.analyze_and_route(
        message=request.message,
        context=""
    )
    
    # Switch model if needed
    if routing["needs_switch"]:
        from ollama_client import OllamaClient
        client = OllamaClient()
        switch_result = client.set_model(routing["model_recommendation"])
        
        if switch_result["status"] == "error":
            # Fallback to current model if switch fails
            routing["model_recommendation"] = smart_router.current_model
    
    # Chat with selected model
    from ollama_client import OllamaClient
    client = OllamaClient()
    
    messages = [
        {"role": "system", "content": ADVANCED_SYSTEM_PROMPT},
        {"role": "user", "content": request.message}
    ]
    
    response = client.chat(messages, routing["model_recommendation"])
    
    return {
        "status": "success",
        "response": response.get("response", response.get("error", "Unknown error")),
        "model_used": routing["model_recommendation"],
        "routing": {
            "task_type": routing["task_type"],
            "complexity": routing["complexity"],
            "switch_reason": routing.get("switch_reason"),
            "confidence": routing["confidence"]
        }
    }

@app.get("/api/smart/stats")
async def smart_stats():
    """Get smart router statistics."""
    if not SMART_ROUTER_AVAILABLE:
        return {
            "status": "error",
            "message": "Smart Router not available"
        }
    
    return {
        "status": "success",
        "statistics": smart_router.get_statistics(),
        "current_model": smart_router.current_model
    }

@app.get("/api/smart/status")
async def smart_status():
    """Get smart router status."""
    if not SMART_ROUTER_AVAILABLE:
        return {
            "router_active": False,
            "message": "Smart Router not available"
        }
    
    return smart_router.get_status()

# ============================================================================
# PRIVACY VECTOR MEMORY (Privacy-First with Permissions)
# ============================================================================

try:
    from vector_memory import PrivacyVectorMemory, create_vector_memory
    vector_memory = create_vector_memory()
    VECTOR_MEMORY_AVAILABLE = True
    print("[VECTOR-MEMORY] Privacy-First Vector Memory loaded")
except ImportError as e:
    print(f"[VECTOR-MEMORY] Warning: Vector Memory not available: {e}")
    VECTOR_MEMORY_AVAILABLE = False

class MemoryRequest(BaseModel):
    content: str
    category: str
    tags: List[str] = []
    importance: float = 0.5
    source: str = "learned"
    is_personal: bool = False

class FeedbackRequest(BaseModel):
    feedback_type: str  # positive, negative, correction
    original_content: str
    corrected_content: str = None
    context: str = None

@app.post("/api/memory/store")
async def store_memory(request: MemoryRequest):
    """
    Store a memory in vector memory.
    Returns permission request ID if approval needed.
    """
    if not VECTOR_MEMORY_AVAILABLE:
        return {"status": "error", "message": "Vector Memory not available"}
    
    success, request_id = vector_memory.store_memory(
        content=request.content,
        category=request.category,
        tags=request.tags,
        importance=request.importance,
        source=request.source,
        is_personal=request.is_personal
    )
    
    if success:
        return {
            "status": "success",
            "message": "Memory stored successfully",
            "memory_id": request.content[:20] + "..."
        }
    else:
        return {
            "status": "pending_permission",
            "message": "Permission required to store this memory",
            "request_id": request_id
        }

@app.get("/api/memory/search")
async def search_memories(query: str, category: str = None, limit: int = 10):
    """
    Search memories using semantic keywords.
    Privacy-safe: uses keyword matching, not embeddings.
    """
    if not VECTOR_MEMORY_AVAILABLE:
        return {"status": "error", "message": "Vector Memory not available"}
    
    results = vector_memory.search_memories(
        query=query,
        category=category,
        limit=limit
    )
    
    return {
        "status": "success",
        "query": query,
        "results": results,
        "total": len(results)
    }

@app.post("/api/memory/feedback")
async def learn_from_feedback(request: FeedbackRequest):
    """
    Learn from user feedback (positive, negative, correction).
    """
    if not VECTOR_MEMORY_AVAILABLE:
        return {"status": "error", "message": "Vector Memory not available"}
    
    success, request_id = vector_memory.learn_from_feedback(
        feedback_type=request.feedback_type,
        original_content=request.original_content,
        corrected_content=request.corrected_content,
        context=request.context
    )
    
    if success:
        return {
            "status": "success",
            "message": f"Learned from {request.feedback_type} feedback"
        }
    else:
        return {
            "status": "pending_permission",
            "message": "Permission required",
            "request_id": request_id
        }

@app.get("/api/memory/improvements")
async def get_improvements():
    """Get all improvements from corrections."""
    if not VECTOR_MEMORY_AVAILABLE:
        return {"status": "error", "message": "Vector Memory not available"}
    
    improvements = vector_memory.get_improvements()
    return {
        "status": "success",
        "improvements": improvements,
        "total": len(improvements)
    }

@app.get("/api/memory/permissions/pending")
async def get_pending_permissions():
    """Get all pending permission requests."""
    if not VECTOR_MEMORY_AVAILABLE:
        return {"status": "error", "message": "Vector Memory not available"}
    
    requests = vector_memory.permission_manager.get_pending_requests()
    return {
        "status": "success",
        "pending_requests": requests,
        "total": len(requests)
    }

@app.post("/api/memory/permissions/{request_id}/grant")
async def grant_permission(request_id: str):
    """Grant a permission request."""
    if not VECTOR_MEMORY_AVAILABLE:
        return {"status": "error", "message": "Vector Memory not available"}
    
    success = vector_memory.permission_manager.grant_permission(request_id)
    
    if success:
        return {
            "status": "success",
            "message": "Permission granted"
        }
    else:
        return {
            "status": "error",
            "message": "Request not found or already processed"
        }

@app.post("/api/memory/permissions/{request_id}/deny")
async def deny_permission(request_id: str):
    """Deny a permission request."""
    if not VECTOR_MEMORY_AVAILABLE:
        return {"status": "error", "message": "Vector Memory not available"}
    
    success = vector_memory.permission_manager.deny_permission(request_id)
    
    if success:
        return {
            "status": "success",
            "message": "Permission denied"
        }
    else:
        return {
            "status": "error",
            "message": "Request not found or already processed"
        }

@app.get("/api/memory/export")
async def export_all_data():
    """
    Export all memory data (user right).
    Returns download link for all stored data.
    """
    if not VECTOR_MEMORY_AVAILABLE:
        return {"status": "error", "message": "Vector Memory not available"}
    
    data = vector_memory.export_data()
    return {
        "status": "success",
        "export": data,
        "download_ready": True
    }

@app.post("/api/memory/delete/request")
async def request_delete_all():
    """
    Request to delete all data.
    Requires explicit permission.
    """
    if not VECTOR_MEMORY_AVAILABLE:
        return {"status": "error", "message": "Vector Memory not available"}
    
    success, request_id = vector_memory.delete_all_data()
    
    if success:
        return {
            "status": "success",
            "message": "All data deleted"
        }
    else:
        return {
            "status": "pending_permission",
            "message": "Permission required to delete all data",
            "request_id": request_id,
            "warning": "This action is irreversible"
        }

@app.post("/api/memory/delete/confirm")
async def confirm_delete_all():
    """Confirm and execute deletion of all data (after permission)."""
    if not VECTOR_MEMORY_AVAILABLE:
        return {"status": "error", "message": "Vector Memory not available"}
    
    success = vector_memory.confirm_delete_all()
    
    if success:
        return {
            "status": "success",
            "message": "All data has been deleted"
        }
    else:
        return {
            "status": "error",
            "message": "Permission not granted or already processed"
        }

@app.get("/api/memory/stats")
async def memory_stats():
    """Get vector memory statistics."""
    if not VECTOR_MEMORY_AVAILABLE:
        return {"status": "error", "message": "Vector Memory not available"}
    
    stats = vector_memory.get_stats()
    return {
        "status": "success",
        "statistics": stats
    }

@app.post("/api/memory/{memory_id}/delete")
async def delete_specific_memory(memory_id: str):
    """Delete a specific memory."""
    if not VECTOR_MEMORY_AVAILABLE:
        return {"status": "error", "message": "Vector Memory not available"}
    
    success = vector_memory.delete_memory(memory_id)
    
    if success:
        return {
            "status": "success",
            "message": "Memory deleted"
        }
    else:
        return {
            "status": "error",
            "message": "Memory not found or requires permission"
        }

# ============================================================================
# CUSTODIAN MODE (Privacy & Security)
# ============================================================================

try:
    from custodian import CustodianEngine, RequestType, ThreatLevel
    custodian = CustodianEngine()
    CUSTODIAN_AVAILABLE = True
    print("[CUSTODIAN] Privacy & Security Custodian loaded")
except ImportError as e:
    print(f"[CUSTODIAN] Warning: Custodian not available: {e}")
    CUSTODIAN_AVAILABLE = False

class PersonalDataRequest(BaseModel):
    text: str
    action: str = "detect"

@app.post("/api/custodian/check")
async def check_personal_data(request: PersonalDataRequest):
    if not CUSTODIAN_AVAILABLE:
        return {"status": "error", "message": "Custodian not available"}
    
    detected = custodian.detect_personal_data(request.text)
    return {
        "status": "success",
        "detected": detected,
        "count": len(detected)
    }

@app.post("/api/custodian/block")
async def block_personal_data(request: PersonalDataRequest):
    if not CUSTODIAN_AVAILABLE:
        return {"status": "error", "message": "Custodian not available"}
    
    sanitized, detected = custodian.block_personal_data(request.text)
    custodian.log_personal_data_detection(detected, context="api")
    
    return {
        "status": "success",
        "sanitized_text": sanitized,
        "blocked_count": len(detected)
    }

@app.get("/api/custodian/permissions/pending")
async def get_custodian_permissions():
    if not CUSTODIAN_AVAILABLE:
        return {"status": "error", "message": "Custodian not available"}
    
    requests = custodian.get_pending_permissions()
    return {"status": "success", "pending": requests, "total": len(requests)}

@app.post("/api/custodian/permissions/{request_id}/approve")
async def approve_custodian_permission(request_id: str):
    if not CUSTODIAN_AVAILABLE:
        return {"status": "error", "message": "Custodian not available"}
    
    success = custodian.grant_permission(request_id)
    return {"status": "success" if success else "error", "message": "Granted" if success else "Not found"}

@app.post("/api/custodian/permissions/{request_id}/deny")
async def deny_custodian_permission(request_id: str):
    if not CUSTODIAN_AVAILABLE:
        return {"status": "error", "message": "Custodian not available"}
    
    success = custodian.deny_permission(request_id)
    return {"status": "success" if success else "error", "message": "Denied" if success else "Not found"}

@app.get("/api/custodian/audit")
async def get_audit_log(limit: int = 100, threat_level: str = None):
    if not CUSTODIAN_AVAILABLE:
        return {"status": "error", "message": "Custodian not available"}
    
    events = custodian.get_audit_log(limit=limit, threat_level=threat_level)
    return {"status": "success", "events": events, "total": len(events)}

@app.get("/api/custodian/stats")
async def custodian_stats():
    if not CUSTODIAN_AVAILABLE:
        return {"status": "error", "message": "Custodian not available"}
    
    return {"status": "success", "statistics": custodian.get_stats()}

@app.get("/api/custodian/status")
async def custodian_status():
    if not CUSTODIAN_AVAILABLE:
        return {"status": "error", "message": "Custodian not available"}
    
    return {"status": "success", "custodian": custodian.get_status()}

@app.post("/api/custodian/external/block")
async def block_external_requests():
    if not CUSTODIAN_AVAILABLE:
        return {"status": "error", "message": "Custodian not available"}
    
    custodian.block_external = True
    return {"status": "success", "message": "External requests blocked", "blocked": True}

@app.post("/api/custodian/external/unblock")
async def unblock_external_requests():
    if not CUSTODIAN_AVAILABLE:
        return {"status": "error", "message": "Custodian not available"}
    
    custodian.block_external = False
    return {"status": "success", "message": "External requests allowed", "blocked": False}

@app.get("/api/custodian/export")
async def export_custodian_data():
    if not CUSTODIAN_AVAILABLE:
        return {"status": "error", "message": "Custodian not available"}
    
    return {"status": "success", "export": custodian.export_all_data()}

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("LEO 2.0 - Self-Learning AI Agent")
    print("="*60)
    print("\nStarting server...")
    print("Dashboard will be available at: http://127.0.0.1:7860")
    print("API Documentation: http://127.0.0.1:7860/docs")
    print("NEURON Learning: http://127.0.0.1:7860/api/neuron/*")
    print("="*60 + "\n")
    
    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=7860,
        reload=True
    )
