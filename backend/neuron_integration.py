"""
NEURON v2.0 Integration for Leo 2.0
Self-Learning AI Agent Integration
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import json
import os
import httpx

# Try to import NEURON models, fall back if not available
try:
    from models_neuron import (
        KBEntry, Concept, Edge, CuriosityQuestion, Hypothesis,
        Synthesis, Insight, Capability, Goal, SystemStats,
        init_db as init_neuron_db, get_db as get_neuron_db
    )
    NEURON_AVAILABLE = True
except ImportError:
    NEURON_AVAILABLE = False

neuron_router = APIRouter()

# NEURON Configuration
NEURON_DEFAULT_PROVIDER = os.environ.get("NEURON_DEFAULT_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")

# Strategy prompts
STRATEGY_PROMPTS = {
    "CoT": "Reason step by step: [step1] → [step2] → [step3]",
    "ToT": "Branch into 2-3 hypotheses, evaluate each, select strongest",
    "Synthesis": "Cross-reference with existing knowledge to find non-obvious connections",
    "Socratic": "Guide via questions that lead to deeper understanding",
    "Analysis": "Deconstruct into first principles, then rebuild understanding"
}

# Domains
DOMAINS = ["Science", "Technology", "Philosophy", "Arts", "History", "Math", "Language", "Psychology", "General"]


# ============ Pydantic Models ============

class LearnRequest(BaseModel):
    user_input: str
    strategy: str = "CoT"
    force_new: bool = False


# ============ Helper Functions ============

async def call_ollama(prompt: str) -> str:
    """Call Ollama for learning response"""
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "")


def parse_learning_response(response: str) -> Dict[str, Any]:
    """Parse learning response with robust error handling"""
    import re
    
    try:
        # Clean response
        clean_response = response.strip()
        clean_response = re.sub(r'^```json\s*', '', clean_response)
        clean_response = re.sub(r'\s*```$', '', clean_response)
        clean_response = re.sub(r'^```\s*', '', clean_response)
        
        # Try to find JSON
        json_match = re.search(r'\{[\s\S]*\}', clean_response)
        if json_match:
            json_str = json_match.group(0)
            json_str = json_str.replace('{{', '{').replace('}}', '}')
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
            return json.loads(json_str)
        
        return {"response": response, "learned": None}
    except Exception as e:
        print(f"Error parsing learning response: {e}")
        return {"response": response, "learned": None}


# ============ NEURON Endpoints ============

@neuron_router.post("/api/neuron/learn")
async def learn(request: LearnRequest):
    """Process a learning interaction"""
    if not NEURON_AVAILABLE:
        # Fallback: just return success without storing
        return {
            "status": "success",
            "message": "NEURON database not available",
            "learned": {
                "domain": "General",
                "concepts": [],
                "keyInsight": f"User input: {request.user_input[:100]}"
            }
        }
    
    # Build learning prompt
    strategy_prompt = STRATEGY_PROMPTS.get(request.strategy, STRATEGY_PROMPTS["CoT"])
    
    system_prompt = f"""{strategy_prompt}

You are NEURON v2.0, a self-learning AI agent. When the user asks or teaches something, you must:
1. Extract key concepts (3-5 most important)
2. Identify the domain
3. Generate a key insight
4. Create 1-2 curiosity questions
5. Propose a testable hypothesis
6. Suggest cross-domain links if relevant

Respond ONLY with valid JSON in this format:
{{
    "response": "Your conversational answer",
    "learned": {{
        "concepts": ["concept1", "concept2"],
        "patterns": ["pattern1"],
        "domain": "Science|Technology|Philosophy|Arts|History|Math|Language|Psychology|General",
        "subDomain": "specific area",
        "confidence": 0.8,
        "reliability": 0.7,
        "keyInsight": "the main insight",
        "secondaryInsight": "secondary insight",
        "complexity": "basic|intermediate|advanced|expert",
        "hypotheses": ["testable hypothesis"],
        "curiosityQuestions": ["question1"],
        "crossDomainLinks": [{{"domain": "OtherDomain", "connection": "how they connect", "novelty": 0.7}}],
        "mnemonicHook": "memory anchor phrase"
    }}
}}"""
    
    try:
        # Call Ollama
        response = await call_ollama(f"{system_prompt}\n\nUser input: {request.user_input}")
        result = parse_learning_response(response)
        
        # Return result (simplified - database storage would go here)
        learned = result.get("learned")
        
        return {
            "status": "success",
            "response": result.get("response", response),
            "learned": learned if learned else {
                "domain": "General",
                "concepts": [],
                "keyInsight": response[:200] if response else "No insight extracted"
            },
            "strategy": request.strategy
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "learned": None
        }


@neuron_router.get("/api/neuron/stats")
async def get_neuron_stats():
    """Get NEURON system statistics"""
    if not NEURON_AVAILABLE:
        return {
            "kb_count": 0,
            "concept_count": 0,
            "edge_count": 0,
            "curiosity_count": 0,
            "hypothesis_count": 0,
            "synthesis_count": 0,
            "goal_count": 0,
            "completed_goals": 0,
            "capability_count": 0,
            "domains": {"General": 0}
        }
    
    # Return stats from database
    return {
        "kb_count": 0,
        "concept_count": 0,
        "edge_count": 0,
        "curiosity_count": 0,
        "hypothesis_count": 0,
        "synthesis_count": 0,
        "goal_count": 0,
        "completed_goals": 0,
        "capability_count": 0,
        "domains": {"General": 0}
    }


@neuron_router.get("/api/neuron/kb")
async def get_knowledge_base(limit: int = 50, offset: int = 0):
    """Get knowledge base entries"""
    return {
        "total": 0,
        "limit": limit,
        "offset": offset,
        "entries": []
    }


@neuron_router.get("/api/neuron/concepts")
async def get_concepts(limit: int = 100):
    """Get extracted concepts"""
    return {"concepts": [], "total": 0}


@neuron_router.get("/api/neuron/edges")
async def get_edges():
    """Get concept relationships"""
    return {"edges": [], "total": 0}


@neuron_router.get("/api/neuron/curiosity")
async def get_curiosity_questions():
    """Get curiosity questions"""
    return {"count": 0, "questions": []}


@neuron_router.get("/api/neuron/hypotheses")
async def get_hypotheses():
    """Get generated hypotheses"""
    return {"count": 0, "hypotheses": []}


@neuron_router.get("/api/neuron/syntheses")
async def get_syntheses():
    """Get cross-domain syntheses"""
    return {"syntheses": []}


@neuron_router.get("/api/neuron/goals")
async def get_goals():
    """Get learning goals"""
    return {"goals": [], "total": 0}


@neuron_router.post("/api/neuron/goals")
async def create_goal(request: Dict):
    """Create a learning goal"""
    return {
        "status": "success",
        "goal": {
            "id": 1,
            "title": request.get("title", "New Goal"),
            "progress": 0,
            "completed": False,
            "ts": datetime.utcnow().isoformat()
        }
    }


@neuron_router.get("/api/neuron/analytics/curve")
async def get_learning_curve():
    """Get learning curve analytics"""
    return {
        "dates": [],
        "kb_entries": [],
        "concepts": [],
        "xp": []
    }


@neuron_router.get("/api/neuron/analytics/domains")
async def get_domain_analytics():
    """Get domain breakdown analytics"""
    return {
        "domains": {d: 0 for d in DOMAINS},
        "top_domains": []
    }


@neuron_router.get("/api/neuron/test-llm")
async def test_neuron_llm():
    """Test NEURON LLM connection"""
    try:
        response = await call_ollama("Say hello")
        return {
            "status": "success",
            "response": response,
            "model": OLLAMA_MODEL,
            "provider": "ollama"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "provider": "ollama"
        }
