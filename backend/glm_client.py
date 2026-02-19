# glm_client.py - GLM-5 API Client for ClawForge
# Supports: GLM-5, GLM-4, and other Zhipu AI models

import os
import json
import httpx
from typing import Optional, Dict, Any, List

# ============================================================================
# ZHIPU AI (GLM) API CLIENT
# ============================================================================

class GLMAPIClient:
    """
    Zhipu AI API client for GLM-5 and other models.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GLM_API_KEY", "")
        self.base_url = os.environ.get("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        self.model = "glm-5"  # Default model
    
    def chat(self, messages: List[Dict], model: str = None) -> str:
        """Send chat completion request to Zhipu AI."""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096,
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
        """Return available GLM models."""
        return [
            "glm-5",
            "glm-5-plus",
            "glm-4",
            "glm-4-plus",
            "glm-4v",
            "chatglm_turbo",
            "chatglm_pro",
        ]
    
    def set_model(self, model: str):
        """Set the active model."""
        self.model = model
    
    def get_active_model(self) -> str:
        """Get currently active model."""
        return self.model

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def test_glm_api_key(api_key: str) -> Dict:
    """Test if GLM API key is valid."""
    try:
        client = GLMAPIClient(api_key)
        response = client.generate("Say hello and confirm you're working!")
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

def get_glm_client(api_key: str = None) -> GLMAPIClient:
    """Get GLM API client."""
    return GLMAPIClient(api_key)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("  ClawForge - GLM API Client")
    print("="*60)
    
    api_key = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GLM_API_KEY")
    
    if not api_key:
        print("\nNo API key provided!")
        print("\nUsage:")
        print("  python glm_client.py YOUR_API_KEY")
        print("  or")
        print("  $env:GLM_API_KEY = 'your_key'")
        print("  python glm_client.py")
        sys.exit(1)
    
    print("\nTesting GLM API...")
    result = test_glm_api_key(api_key)
    
    if result["success"]:
        print("\nGLM API is working!")
        print(f"\nResponse: {result['response']}")
        print(f"\nAvailable models:")
        for model in result["models"]:
            print(f"  - {model}")
    else:
        print(f"\nAPI test failed: {result['error']}")
