# ollama_client.py - Ollama Client for Leo 2.0

"""
Handles all communication with the local Ollama LLM backend.
Uses httpx for async HTTP requests.
"""

import httpx
import json
from typing import Optional, Dict, Any, List

# ============================================================================
# OLLAMA CONFIGURATION
# ============================================================================

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_API_CHAT = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_API_TAGS = f"{OLLAMA_BASE_URL}/api/tags"

# ============================================================================
# SUPPORTED MODELS (Leo 2.0)
# ============================================================================

SUPPORTED_MODELS = [
    "qwen2.5:3b",      # 2GB - Best for limited memory
    "llama3.2:3b",     # 2GB - Good alternative  
    "phi3:mini",       # 2GB - Fast & efficient
]

# ============================================================================
# LEO 2.0 SYSTEM PROMPT
# ============================================================================

LEO_SYSTEM_PROMPT = """You are Leo 2.0, a self-learning AI agent with NEURON v2.0 capabilities.

## Your Core Identity
- You are Leo 2.0, created by Amir Ali (Project Shahzada)
- You learn from every conversation automatically
- You have NEURON v2.0 integrated into your core

## Your Capabilities
- Self-Learning (NEURON): You extract concepts from every message
- Memory: You remember important things
- Reasoning: You think step-by-step
- Code: You can write and run Python
- Files: You can read and edit files
- Web: You can search the web
- Planning: You create multi-step plans

## How You Respond
1. Be direct and concise
2. Use examples to clarify
3. Ask follow-up questions when helpful
4. Remember context from conversation
5. Learn from every interaction

## Your Personality
- Autonomous within boundaries
- Efficient and practical
- Privacy-conscious
- Security-minded
- Continuously learning

Remember: You are Leo 2.0, not a chatbot. You are a self-learning AI agent."""

# ============================================================================
# OLLAMA CLIENT CLASS
# ============================================================================

class OllamaClient:
    """
    Handles all communication with the local Ollama LLM backend.
    """
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url
        self.active_model = "qwen2.5:3b"  # Default model - 2GB, works with limited RAM
        self.request_timeout = 120.0  # seconds
    
    # ============================================================================
    # MODEL SELECTION
    # ============================================================================
    
    def set_model(self, model_name: str) -> Dict[str, Any]:
        """
        Set active model.
        
        Args:
            model_name: Name of model to set (e.g., "qwen3:8b", "phi3:mini")
        
        Returns:
            Dict with status and model info
        """
        # Handle "ollama/" prefix from frontend
        clean_name = model_name.replace("ollama/", "")
        
        if clean_name not in SUPPORTED_MODELS:
            # Try without version (e.g., "qwen3" -> "qwen3:8b")
            return {
                "status": "error",
                "error": f"Model {model_name} not supported",
                "supported_models": SUPPORTED_MODELS
            }
        
        self.active_model = clean_name
        return {
            "status": "success",
            "model": clean_name,
            "message": f"Active model set to {clean_name}"
        }
    
    def get_active_model(self) -> str:
        """Returns active model name."""
        return self.active_model
    
    # ============================================================================
    # HEALTH CHECK
    # ============================================================================
    
    def health_check(self) -> Dict[str, Any]:
        """
        Checks if Ollama is running and lists available models.
        
        Returns:
            Dict with status, available_models, and supported_models
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(OLLAMA_API_TAGS)
                
                if response.status_code == 200:
                    data = response.json()
                    available_models = [model["name"] for model in data.get("models", [])]
                    
                    return {
                        "status": "healthy",
                        "available_models": available_models,
                        "supported_models": SUPPORTED_MODELS,
                        "active_model": self.active_model,
                        "api_version": "0.1.x"
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"API returned status {response.status_code}"
                    }
        
        except httpx.ConnectError:
            return {
                "status": "unavailable",
                "error": "Cannot connect to Ollama. Make sure Ollama is running.",
                "hint": "Run 'ollama serve' in terminal"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    # ============================================================================
    # CHAT (Multi-turn)
    # ============================================================================
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Multi-turn chat with Ollama using /api/chat endpoint.
        
        Args:
            messages: List of messages [{"role": "user"/"assistant"/"system", "content": "..."}]
            model: Model to use (optional, uses active model if not specified)
            temperature: Sampling temperature
        
        Returns:
            Dict with status, response, and metrics
        """
        model = model or self.active_model
        
        # Clean model name if needed
        clean_model = model.replace("ollama/", "")
        
        # Build payload for /api/chat
        payload = {
            "model": clean_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            with httpx.Client(timeout=self.request_timeout) as client:
                response = client.post(OLLAMA_API_CHAT, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    return {
                        "status": "success",
                        "model": clean_model,
                        "response": data.get("message", {}).get("content", ""),
                        "done": data.get("done", True),
                        "total_duration_ms": data.get("total_duration", 0)
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"API returned status {response.status_code}",
                        "message": response.text[:200] if response.text else None
                    }
        
        except httpx.ConnectError:
            return {
                "status": "error",
                "error": "Cannot connect to Ollama",
                "message": "Make sure Ollama is running on port 11434"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    # ============================================================================
    # SIMPLE GENERATE
    # ============================================================================
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Simple single-prompt generation.
        
        Args:
            prompt: The user prompt
            model: Model to use (optional)
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
        
        Returns:
            Dict with status, response, and metrics
        """
        model = model or self.active_model
        clean_model = model.replace("ollama/", "")
        
        # Build messages list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({"role": "system", "content": LEO_SYSTEM_PROMPT})
        
        messages.append({"role": "user", "content": prompt})
        
        return self.chat(messages, clean_model, temperature)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def health_check() -> Dict[str, Any]:
    """Convenience function for OllamaClient().health_check()"""
    client = OllamaClient()
    return client.health_check()


if __name__ == "__main__":
    print("🦁 Leo 2.0 - Ollama Client Test")
    print("=" * 50)
    
    client = OllamaClient()
    
    # Health check
    print("\n🔍 Health Check:")
    health = client.health_check()
    print(f"   Status: {health['status']}")
    
    if health['status'] == 'healthy':
        print(f"   Available models: {health.get('available_models', [])}")
        print(f"   Active model: {client.get_active_model()}")
        
        # Chat test
        print("\n💬 Chat Test:")
        result = client.chat(
            messages=[
                {"role": "system", "content": "Respond in one sentence."},
                {"role": "user", "content": "Who are you?"}
            ],
            model=client.active_model
        )
        
        if result['status'] == 'success':
            print(f"   Response: {result['response']}")
        else:
            print(f"   Error: {result.get('error', result.get('message', 'Unknown'))}")
    else:
        print(f"   Error: {health.get('error', 'Unknown')}")
        print(f"   Hint: {health.get('hint', 'Make sure Ollama is running')}")
