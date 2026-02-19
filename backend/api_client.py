# api_client.py - Online API Client for ClawForge
# Supports: OpenAI, Anthropic, SiliconFlow, OpenRouter, Groq, etc.

import os
import json
import httpx
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

# ============================================================================
# BASE API CLIENT
# ============================================================================

class BaseAPIClient(ABC):
    """Base class for API clients."""
    
    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url
        self.model = None
    
    @abstractmethod
    def chat(self, messages: List[Dict], model: str = None) -> str:
        """Send chat request and return response text."""
        pass
    
    @abstractmethod
    def generate(self, prompt: str, model: str = None) -> str:
        """Send generation request."""
        pass
    
    @abstractmethod
    def get_models(self) -> List[str]:
        """Get available models."""
        pass

# ============================================================================
# OPENAI-COMPATIBLE CLIENT (SiliconFlow, OpenRouter, etc.)
# ============================================================================

class OpenAICompatClient(BaseAPIClient):
    """
    OpenAI-compatible API client.
    Works with: SiliconFlow, OpenRouter, Groq, Together AI, etc.
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        super().__init__(api_key, base_url)
        self.model = "qwen3.5-397b-a17b"  # Default model
    
    def chat(self, messages: List[Dict], model: str = None) -> str:
        """Send chat completion request."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096
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
    
    def get_models(self) -> List[str]:
        """Get available models."""
        # For OpenAI-compatible, we don't have a standard endpoint
        # Return common models
        return [
            "qwen3.5-397b-a17b",
            "qwen3-8b",
            "glm-5",
            "minimax-m2.5",
            "kimi-k2.5",
            "gpt-4",
            "gpt-3.5-turbo",
            "llama3-70b",
            "mixtral-8x7b",
        ]
    
    def set_model(self, model: str):
        """Set the active model."""
        self.model = model

# ============================================================================
# SILICONFLOW CLIENT
# ============================================================================

class SiliconFlowClient(OpenAICompatClient):
    """
    SiliconFlow API client.
    Supports: Qwen, GLM, Minimax, Kimi models.
    """
    
    def __init__(self, api_key: str = None):
        # Get from env or use provided
        key = api_key or os.environ.get("SILICON_API_KEY", "")
        base_url = os.environ.get("SILICON_BASE_URL", "https://api.siliconflow.cn/v1")
        super().__init__(key, base_url)
        self.model = "Qwen3.5-397B-A17B"  # SiliconFlow model name
    
    def get_models(self) -> List[str]:
        """Return SiliconFlow available models."""
        return [
            "Qwen3.5-397B-A17B",
            "Qwen3-8B",
            "GLM-5",
            "MiniMax-M2.5",
            "Kimi-k2.5",
            "Llama3-70B",
            "Mixtral-8x7B",
        ]

# ============================================================================
# OPENROUTER CLIENT
# ============================================================================

class OpenRouterClient(OpenAICompatClient):
    """
    OpenRouter API client.
    Access to multiple providers.
    """
    
    def __init__(self, api_key: str = None):
        key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        super().__init__(key, base_url)
        self.model = "qwen/qwen-3-40b"  # OpenRouter model path
    
    def get_models(self) -> List[str]:
        """Return OpenRouter available models."""
        return [
            "qwen/qwen-3-40b",
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4",
            "google/gemini-pro",
            "meta-llama/llama-3.1-70b",
        ]

# ============================================================================
# MAIN API CLIENT FACTORY
# ============================================================================

class APIClient:
    """
    Unified API client that supports Ollama + Online APIs.
    Auto-detects best available provider.
    """
    
    def __init__(self):
        self.ollama_client = None
        self.online_client = None
        self.active_provider = "none"
    
    def initialize(self) -> Dict[str, Any]:
        """
        Initialize the best available client.
        Returns status with provider info.
        """
        # Check for online API first
        api_key = os.environ.get("SILICON_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
        
        if api_key:
            provider = "SiliconFlow" if os.environ.get("SILICON_API_KEY") else "OpenRouter"
            self.online_client = SiliconFlowClient() if provider == "SiliconFlow" else OpenRouterClient()
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
                    "provider": "Ollama",
                    "model": health.get("active_model", "llama3"),
                    "available_models": health.get("available_models", []),
                    "message": "Using local Ollama"
                }
        except ImportError:
            pass
        
        return {
            "status": "unavailable",
            "provider": "none",
            "message": "No API available. Set SILICON_API_KEY or ensure Ollama is running."
        }
    
    def chat(self, messages: List[Dict], model: str = None) -> str:
        """Send chat request to active provider."""
        if self.online_client:
            return self.online_client.chat(messages, model)
        elif self.ollama_client:
            return self.ollama_client.chat(messages, model)
        else:
            raise RuntimeError("No API client available")
    
    def generate(self, prompt: str, model: str = None) -> str:
        """Send generation request."""
        if self.online_client:
            return self.online_client.generate(prompt, model)
        elif self.ollama_client:
            return self.ollama_client.generate(prompt, model)
        else:
            raise RuntimeError("No API client available")
    
    def set_model(self, model: str):
        """Change active model."""
        if self.online_client:
            self.online_client.set_model(model)
        elif self.ollama_client:
            self.ollama_client.set_model(model)
    
    def get_models(self) -> List[str]:
        """Get available models."""
        if self.online_client:
            return self.online_client.get_models()
        elif self.ollama_client:
            return self.ollama_client.get_models()
        return []
    
    def get_active_model(self) -> str:
        """Get currently active model."""
        if self.online_client:
            return self.online_client.model
        elif self.ollama_client:
            return self.ollama_client.get_active_model()
        return None

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_api_client() -> APIClient:
    """Get initialized API client."""
    client = APIClient()
    client.initialize()
    return client

def test_online_api(api_key: str, base_url: str = "https://api.siliconflow.cn/v1") -> Dict:
    """Test if API key is valid."""
    try:
        client = OpenAICompatClient(api_key, base_url)
        response = client.generate("Hello! Say hi and confirm you're working.")
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
    print("  ClawForge API Client - Test")
    print("="*60)
    
    # Check environment
    api_key = os.environ.get("SILICON_API_KEY")
    
    if not api_key:
        print("\nNo API key found!")
        print("Set your API key:")
        print("  $env:SILICON_API_KEY = 'your_key_here'")
        print("\nOr run with key:")
        print("  python api_client.py YOUR_API_KEY")
        sys.exit(1)
    
    # Test API
    print("\nTesting SiliconFlow API...")
    result = test_online_api(api_key)
    
    if result["success"]:
        print("\nAPI is working!")
        print(f"Response: {result['response']}")
        print(f"\nAvailable models:")
        for model in result["models"]:
            print(f"  - {model}")
    else:
        print(f"\nAPI test failed: {result['error']}")
