# nvidia_client.py - NVIDIA API Client for ClawForge
# Supports: Qwen3.5-397B, Llama models, and more

import os
import json
import httpx
from typing import Optional, Dict, Any, List

# ============================================================================
# NVIDIA API CLIENT
# ============================================================================

class NvidiaAPIClient:
    """
    NVIDIA API client for Qwen3.5-397B and other models.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY", "")
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.model = "qwen/qwen3.5-397b-a17b"  # Default model
        self.streaming = False
    
    def chat(self, messages: List[Dict], model: str = None) -> str:
        """Send chat completion request to NVIDIA API."""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "model": model or self.model,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.95,
            "stream": False
        }
        
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def generate(self, prompt: str, model: str = None) -> str:
        """Send generation request."""
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, model)
    
    def chat_stream(self, messages: List[Dict], model: str = None):
        """Send streaming chat request - yields chunks."""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        payload = {
            "model": model or self.model,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.95,
            "stream": True
        }
        
        with httpx.Client(timeout=300.0) as client:
            with client.post(url, headers=headers, json=payload) as response:
                for line in response.iter_lines():
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            data = line[6:]
                            if data != "[DONE]":
                                try:
                                    chunk = json.loads(data)
                                    if "choices" in chunk:
                                        delta = chunk["choices"][0].get("delta", {})
                                        content = delta.get("content", "")
                                        if content:
                                            yield content
                                except json.JSONDecodeError:
                                    pass
    
    def get_models(self) -> List[str]:
        """Return available NVIDIA models."""
        return [
            "z-ai/glm5",
            "qwen/qwen3.5-397b-a17b",
            "qwen/qwen3-8b-instruct",
            "meta/llama-3.1-70b-instruct",
            "meta/llama-3.1-405b-instruct",
            "meta/llama-3.3-70b-instruct",
            "nvidia/llama-3.1-nemotron-70b-Instruct",
            "deepseek/deepseek-r1",
        ]
    
    def set_model(self, model: str):
        """Set the active model."""
        self.model = model
    
    def get_active_model(self) -> str:
        """Get currently active model."""
        return self.model

# ============================================================================
# UNIFIED API CLIENT
# ============================================================================

class UnifiedAPIClient:
    """
    Unified client that supports:
    - NVIDIA API (Qwen3.5-397B)
    - Ollama (local)
    - OpenAI-compatible APIs (SiliconFlow, OpenRouter)
    """
    
    def __init__(self):
        self.nvidia_client = None
        self.ollama_client = None
        self.online_client = None
        self.active_provider = "none"
    
    def initialize(self) -> Dict[str, Any]:
        """Initialize the best available client."""
        # Check for NVIDIA API
        nvidia_key = os.environ.get("NVIDIA_API_KEY")
        if nvidia_key:
            self.nvidia_client = NvidiaAPIClient(nvidia_key)
            self.active_provider = "nvidia"
            return {
                "status": "healthy",
                "provider": "NVIDIA API",
                "model": self.nvidia_client.model,
                "message": "Using NVIDIA API with Qwen3.5-397B"
            }
        
        # Check for OpenAI-compatible API (SiliconFlow, etc.)
        api_key = os.environ.get("SILICON_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
        if api_key:
            provider = "SiliconFlow" if os.environ.get("SILICON_API_KEY") else "OpenRouter"
            
            base_url = os.environ.get("SILICON_BASE_URL", "https://api.siliconflow.cn/v1")
            if provider == "OpenRouter":
                base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            
            from api_client import OpenAICompatClient
            self.online_client = OpenAICompatClient(api_key, base_url)
            self.active_provider = provider.lower()
            
            return {
                "status": "healthy",
                "provider": provider,
                "model": self.online_client.model,
                "message": f"Using {provider} API"
            }
        
        # Fallback to Ollama
        try:
            from ollama_client import OllamaClient
            self.ollama_client = OllamaClient()
            health = self.ollama_client.health_check()
            
            if health["status"] == "healthy":
                self.active_provider = "ollama"
                return {
                    "status": "healthy",
                    "provider": "Ollama (Local)",
                    "model": health.get("active_model", "llama3"),
                    "available_models": health.get("available_models", []),
                    "message": "Using local Ollama"
                }
        except ImportError:
            pass
        
        return {
            "status": "unavailable",
            "provider": "none",
            "message": "No API available. Set NVIDIA_API_KEY or ensure Ollama is running."
        }
    
    def chat(self, messages: List[Dict], model: str = None) -> str:
        """Send chat request to active provider."""
        if self.nvidia_client:
            return self.nvidia_client.chat(messages, model)
        elif self.online_client:
            return self.online_client.chat(messages, model)
        elif self.ollama_client:
            return self.ollama_client.chat(messages, model)
        else:
            raise RuntimeError("No API client available")
    
    def generate(self, prompt: str, model: str = None) -> str:
        """Send generation request."""
        if self.nvidia_client:
            return self.nvidia_client.generate(prompt, model)
        elif self.online_client:
            return self.online_client.generate(prompt, model)
        elif self.ollama_client:
            return self.ollama_client.generate(prompt, model)
        else:
            raise RuntimeError("No API client available")
    
    def set_model(self, model: str):
        """Change active model."""
        if self.nvidia_client and "/" in model:
            self.nvidia_client.set_model(model)
        elif self.online_client:
            self.online_client.set_model(model)
        elif self.ollama_client:
            self.ollama_client.set_model(model)
    
    def get_models(self) -> List[str]:
        """Get available models."""
        models = []
        
        # NVIDIA models
        if self.nvidia_client:
            models.extend(self.nvidia_client.get_models())
        
        # Online API models
        if self.online_client:
            models.extend(self.online_client.get_models())
        
        # Ollama models
        if self.ollama_client:
            models.extend(self.ollama_client.get_models())
        
        return list(set(models))
    
    def get_active_model(self) -> str:
        """Get currently active model."""
        if self.nvidia_client:
            return self.nvidia_client.get_active_model()
        elif self.online_client:
            return self.online_client.get_active_model()
        elif self.ollama_client:
            return self.ollama_client.get_active_model()
        return None

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_unified_client() -> UnifiedAPIClient:
    """Get initialized unified client."""
    client = UnifiedAPIClient()
    client.initialize()
    return client

def test_nvidia_api_key(api_key: str) -> Dict:
    """Test if NVIDIA API key is valid."""
    try:
        client = NvidiaAPIClient(api_key)
        response = client.generate("Say hi and confirm you're working!")
        return {
            "success": True,
            "response": response[:200],
            "models": client.get_models()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("  ClawForge - NVIDIA API Client")
    print("="*60)
    
    # Get API key
    api_key = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("NVIDIA_API_KEY")
    
    if not api_key:
        print("\nNo API key provided!")
        print("\nUsage:")
        print("  1. Set environment variable:")
        print("     $env:NVIDIA_API_KEY = 'your_key'")
        print("  2. Or pass as argument:")
        print("     python nvidia_client.py YOUR_API_KEY")
        sys.exit(1)
    
    # Test API
    print("\nTesting NVIDIA API...")
    result = test_nvidia_api_key(api_key)
    
    if result["success"]:
        print("\nNVIDIA API is working!")
        print(f"\nResponse: {result['response']}")
        print(f"\nAvailable models:")
        for model in result["models"]:
            print(f"  - {model}")
    else:
        print(f"\nAPI test failed: {result['error']}")
