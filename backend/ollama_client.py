# ollama_client.py - Ollama Client for ClawForge

"""
Handles all communication with the local Ollama LLM backend.
Supports streaming, model routing, and fallback handling.
"""

import json
import requests
from typing import Optional, Dict, Any, List, Generator
from datetime import datetime

# ============================================================================
# OLLAMA CONFIGURATION
# ============================================================================

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_API_GENERATE = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_API_CHAT = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_API_TAGS = f"{OLLAMA_BASE_URL}/api/tags"

# ============================================================================
# SUPPORTED MODELS
# ============================================================================

SUPPORTED_MODELS = [
    "llama3",
    "mistral",
    "qwen2.5",
    "deepseek-coder",
    "codellama",
    "phi3",
    "mixtral",
]

# ============================================================================
# MODEL ROUTING RULES
# ============================================================================

MODEL_ROUTING = {
    "content_writing": {
        "primary": "llama3",
        "fallback": "mistral"
    },
    "code_generation": {
        "primary": "deepseek-coder",
        "fallback": "codellama"
    },
    "excel": {
        "primary": "qwen2.5",
        "fallback": None
    },
    "logic": {
        "primary": "qwen2.5",
        "fallback": None
    },
    "planning": {
        "primary": "mixtral",
        "fallback": None
    },
    "multi_step": {
        "primary": "mixtral",
        "fallback": None
    },
    "lightweight": {
        "primary": "phi3",
        "fallback": None
    },
    "debugging": {
        "primary": "deepseek-coder",
        "fallback": "codellama"
    },
    "document": {
        "primary": "llama3",
        "fallback": "mistral"
    },
    "general": {
        "primary": "llama3",
        "fallback": None
    }
}

# ============================================================================
# CLAWFORGE SYSTEM PROMPT
# ============================================================================

CLAWFORGE_SYSTEM_PROMPT = """You are ClawForge, a production-grade autonomous AI agent framework.
You are not a chatbot. You are a full-stack AI operator.

You must respond using this exact structure:
TASK UNDERSTANDING: ...
PLAN: ...
PERMISSION REQUIRED: ...
EXECUTION: ...
OUTPUT: ...
FILES GENERATED: ...
SECURITY REPORT: ...

Rules:
- Never run dangerous commands.
- Always work within ./workspace/ only.
- Always ask permission before computer control.
- Always log your actions.
- Always provide a security report at the end.
"""

# ============================================================================
# OLLAMA CLIENT CLASS
# ============================================================================

class OllamaClient:
    """
    Handles all communication with the local Ollama LLM backend.
    """
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        """
        Initialize the Ollama client.
        
        Args:
            base_url: Base URL for Ollama API (default: http://localhost:11434)
        """
        self.base_url = base_url
        self.active_model = None
        self.request_timeout = 120  # seconds
    
    # ============================================================================
    # MODEL SELECTION
    # ============================================================================
    
    def select_model(self, task_category: str) -> str:
        """
        Dynamically selects best Ollama model for task category.
        
        Args:
            task_category: The task category (e.g., "content_writing", "code_generation")
        
        Returns:
            Model name to use
        """
        routing = MODEL_ROUTING.get(task_category, MODEL_ROUTING["general"])
        selected = routing["primary"]
        
        # Update active model
        self.active_model = selected
        
        return selected
    
    def set_model(self, model_name: str) -> Dict[str, Any]:
        """
        Manually override active model.
        
        Args:
            model_name: Name of model to set
        
        Returns:
            Dict with status and model info
        """
        if model_name not in SUPPORTED_MODELS:
            return {
                "status": "error",
                "error": f"Model {model_name} not in supported models list",
                "supported_models": SUPPORTED_MODELS
            }
        
        self.active_model = model_name
        return {
            "status": "success",
            "model": model_name,
            "message": f"Active model set to {model_name}"
        }
    
    def get_active_model(self) -> str:
        """
        Returns active model name.
        
        Returns:
            Active model name or None
        """
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
            # Try to get tags (list models)
            response = requests.get(OLLAMA_API_TAGS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                available_models = [model["name"] for model in data.get("models", [])]
                
                return {
                    "status": "healthy",
                    "available_models": available_models,
                    "supported_models": SUPPORTED_MODELS,
                    "active_model": self.active_model,
                    "api_version": "0.1.x",
                    "checked_at": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"API returned status {response.status_code}",
                    "supported_models": SUPPORTED_MODELS
                }
        
        except requests.exceptions.ConnectionError:
            return {
                "status": "unavailable",
                "error": "Cannot connect to Ollama. Make sure Ollama is running.",
                "supported_models": SUPPORTED_MODELS,
                "hint": "Run 'ollama serve' in terminal"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "supported_models": SUPPORTED_MODELS
            }
    
    # ============================================================================
    # NON-STREAMING INFERENCE
    # ============================================================================
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Sends prompt to Ollama and returns full response.
        
        Args:
            prompt: The user prompt
            model: Model to use (optional, uses active model if not specified)
            system_prompt: System prompt (optional)
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens to generate
        
        Returns:
            Dict with status, model, response, and metrics
        """
        # Use specified model or active model
        model = model or self.active_model
        if not model:
            return {
                "status": "error",
                "error": "No model specified and no active model set. Call select_model() first."
            }
        
        # Build payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt
        else:
            payload["system"] = CLAWFORGE_SYSTEM_PROMPT
        
        try:
            response = requests.post(
                OLLAMA_API_GENERATE,
                json=payload,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                return {
                    "status": "success",
                    "model": model,
                    "response": data.get("response", ""),
                    "done": data.get("done", True),
                    "total_duration_ms": data.get("total_duration", 0),
                    "tokens_generated": data.get("eval_count", 0),
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "generated_at": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "error": f"API returned status {response.status_code}",
                    "response_text": response.text[:500] if response.text else None
                }
        
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "error": "Cannot connect to Ollama. Make sure it's running."
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    # ============================================================================
    # STREAMING INFERENCE
    # ============================================================================
    
    def stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Streams response tokens from Ollama one chunk at a time.
        
        Args:
            prompt: The user prompt
            model: Model to use (optional)
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
        
        Yields:
            Dict with token chunk and metrics
        """
        # Use specified model or active model
        model = model or self.active_model
        if not model:
            yield {"status": "error", "error": "No model specified"}
            return
        
        # Build payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        
        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt
        else:
            payload["system"] = CLAWFORGE_SYSTEM_PROMPT
        
        try:
            response = requests.post(
                OLLAMA_API_GENERATE,
                json=payload,
                timeout=self.request_timeout,
                stream=True
            )
            
            if response.status_code != 200:
                yield {"status": "error", "error": f"API returned status {response.status_code}"}
                return
            
            # Process streaming response
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        yield {
                            "status": "streaming",
                            "model": model,
                            "chunk": data.get("response", ""),
                            "done": data.get("done", False),
                            "total_duration_ms": data.get("total_duration", 0),
                            "tokens_generated": data.get("eval_count", 0)
                        }
                        
                        if data.get("done"):
                            break
                    
                    except json.JSONDecodeError:
                        continue
        
        except requests.exceptions.ConnectionError:
            yield {"status": "error", "error": "Cannot connect to Ollama"}
        except Exception as e:
            yield {"status": "error", "error": str(e)}
    
    # ============================================================================
    # MULTI-TURN CHAT
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
            messages: List of messages [{"role": "user"/"assistant", "content": "..."}]
            model: Model to use (optional)
            temperature: Sampling temperature
        
        Returns:
            Dict with status, response, and metrics
        """
        # Use specified model or active model
        model = model or self.active_model
        if not model:
            return {
                "status": "error",
                "error": "No model specified"
            }
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            response = requests.post(
                OLLAMA_API_CHAT,
                json=payload,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                return {
                    "status": "success",
                    "model": model,
                    "response": data.get("message", {}).get("content", ""),
                    "done": data.get("done", True),
                    "total_duration_ms": data.get("total_duration", 0),
                    "generated_at": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "error": f"API returned status {response.status_code}"
                }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    # ============================================================================
    # ROUTING HELPER
    # ============================================================================
    
    def route_and_generate(
        self,
        prompt: str,
        task_category: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Auto-selects model, then runs inference. One-call convenience.
        
        Args:
            prompt: The user prompt
            task_category: Task category for model routing
            system_prompt: Optional system prompt override
        
        Returns:
            Dict with inference results
        """
        # Select model for task category
        model = self.select_model(task_category)
        
        # Generate response
        result = self.generate(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt
        )
        
        # Add routing info
        result["routed_model"] = model
        result["task_category"] = task_category
        
        return result
    
    # ============================================================================
    # MODEL INFO
    # ============================================================================
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Gets information about a specific model.
        
        Args:
            model_name: Name of the model
        
        Returns:
            Dict with model information
        """
        routing = None
        for category, config in MODEL_ROUTING.items():
            if config["primary"] == model_name:
                routing = {
                    "category": category,
                    "role": "primary",
                    "fallback": config["fallback"]
                }
                break
            elif config["fallback"] == model_name:
                routing = {
                    "category": category,
                    "role": "fallback",
                    "primary": config["primary"]
                }
                break
        
        return {
            "name": model_name,
            "supported": model_name in SUPPORTED_MODELS,
            "routing": routing
        }

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def health_check() -> Dict[str, Any]:
    """Convenience function for OllamaClient().health_check()"""
    client = OllamaClient()
    return client.health_check()

def generate(
    prompt: str,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function for OllamaClient().generate()"""
    client = OllamaClient()
    return client.generate(prompt, model, system_prompt)

def route_and_generate(
    prompt: str,
    task_category: str,
    system_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function for OllamaClient().route_and_generate()"""
    client = OllamaClient()
    return client.route_and_generate(prompt, task_category, system_prompt)

if __name__ == "__main__":
    # Test Ollama client
    print("🐾 ClawForge Ollama Client - Test")
    print("=" * 50)
    
    client = OllamaClient()
    
    # Health check
    print("\n🔍 Health Check:")
    health = client.health_check()
    print(f"   Status: {health['status']}")
    if health['status'] == 'healthy':
        print(f"   Available models: {health.get('available_models', [])}")
    else:
        print(f"   Error: {health.get('error', 'Unknown')}")
    
    # Model routing test
    print("\n📊 Model Routing:")
    for category, routing in MODEL_ROUTING.items():
        client.select_model(category)
        print(f"   {category}: {client.get_active_model()}")
    
    # Generate test (if Ollama is running)
    print("\n🧠 Generation Test:")
    if health['status'] == 'healthy':
        result = client.generate(
            prompt="What is ClawForge?",
            model="llama3",
            system_prompt="Respond in one sentence."
        )
        if result['status'] == 'success':
            print(f"   Response: {result['response'][:100]}...")
        else:
            print(f"   Error: {result['error']}")
    else:
        print("   Skipped (Ollama not running)")
