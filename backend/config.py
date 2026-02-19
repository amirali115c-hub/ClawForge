# config.py - Centralized Configuration for ClawForge
# Loads environment variables and provides defaults

import os
from pathlib import Path
from typing import Optional

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Load .env file if exists
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)


class Config:
    """Centralized configuration management"""
    
    # NVIDIA API
    @property
    def NVIDIA_API_KEY(self) -> str:
        return os.environ.get("NVIDIA_API_KEY", "")
    
    @property
    def NVIDIA_API_CONFIGURED(self) -> bool:
        """Check if NVIDIA API key is properly configured"""
        key = self.NVIDIA_API_KEY
        return bool(key and len(key) > 20 and not key.endswith("-your-nvidia-api-key-here"))
    
    # GLM API
    @property
    def GLM_API_KEY(self) -> str:
        return os.environ.get("GLM_API_KEY", "")
    
    @property
    def GLM_API_CONFIGURED(self) -> bool:
        return bool(self.GLM_API_KEY and len(self.GLM_API_KEY) > 10)
    
    # SiliconFlow API
    @property
    def SILICON_API_KEY(self) -> str:
        return os.environ.get("SILICON_API_KEY", "")
    
    @property
    def SILICON_API_CONFIGURED(self) -> bool:
        return bool(self.SILICON_API_KEY and len(self.SILICON_API_KEY) > 10)
    
    # OpenRouter API
    @property
    def OPENROUTER_API_KEY(self) -> str:
        return os.environ.get("OPENROUTER_API_KEY", "")
    
    @property
    def OPENROUTER_API_CONFIGURED(self) -> bool:
        return bool(self.OPENROUTER_API_KEY and len(self.OPENROUTER_API_KEY) > 10)
    
    # Ollama
    @property
    def OLLAMA_BASE_URL(self) -> str:
        return os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    
    @property
    def OLLAMA_CONFIGURED(self) -> bool:
        """Check if Ollama is available"""
        import requests
        try:
            response = requests.get(f"{self.OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    # Brave Search
    @property
    def BRAVE_API_KEY(self) -> str:
        return os.environ.get("BRAVE_API_KEY", "")
    
    @property
    def BRAVE_API_CONFIGURED(self) -> bool:
        return bool(self.BRAVE_API_KEY and len(self.BRAVE_API_KEY) > 10)
    
    # Server Settings
    @property
    def HOST(self) -> str:
        return os.environ.get("CLAWFORGE_HOST", "127.0.0.1")
    
    @property
    def PORT(self) -> int:
        return int(os.environ.get("CLAWFORGE_PORT", 8000))
    
    @property
    def FRONTEND_PORT(self) -> int:
        return int(os.environ.get("CLAWFORGE_FRONTEND_PORT", 7860))
    
    # API Status Summary
    def get_api_status(self) -> dict:
        """Get status of all API configurations"""
        return {
            "nvidia": {
                "configured": self.NVIDIA_API_CONFIGURED,
                "key_length": len(self.NVIDIA_API_KEY) if self.NVIDIA_API_KEY else 0
            },
            "glm": {
                "configured": self.GLM_API_CONFIGURED,
                "key_length": len(self.GLM_API_KEY) if self.GLM_API_KEY else 0
            },
            "silicon": {
                "configured": self.SILICON_API_CONFIGURED,
                "key_length": len(self.SILICON_API_KEY) if self.SILICON_API_KEY else 0
            },
            "openrouter": {
                "configured": self.OPENROUTER_API_CONFIGURED,
                "key_length": len(self.OPENROUTER_API_KEY) if self.OPENROUTER_API_KEY else 0
            },
            "ollama": {
                "configured": self.OLLAMA_CONFIGURED
            },
            "brave": {
                "configured": self.BRAVE_API_CONFIGURED
            }
        }
    
    def get_available_providers(self) -> list:
        """Get list of configured API providers"""
        providers = []
        if self.NVIDIA_API_CONFIGURED:
            providers.append("nvidia")
        if self.GLM_API_CONFIGURED:
            providers.append("glm")
        if self.SILICON_API_CONFIGURED:
            providers.append("siliconflow")
        if self.OPENROUTER_API_CONFIGURED:
            providers.append("openrouter")
        if self.OLLAMA_CONFIGURED:
            providers.append("ollama")
        return providers
    
    def get_primary_provider(self) -> str:
        """Get the best available provider"""
        providers = self.get_available_providers()
        if providers:
            # Priority order: nvidia > siliconflow > openrouter > ollama
            priority = ["nvidia", "siliconflow", "openrouter", "ollama", "glm"]
            for p in priority:
                if p in providers:
                    return p
        return "none"


# Global config instance
config = Config()
