#!/usr/bin/env python3
"""
ClawForge Setup Script
Configures API keys and tests connections
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_status(text, status="INFO"):
    icons = {
        "INFO": "ℹ️ ",
        "SUCCESS": "✅ ",
        "WARNING": "⚠️ ",
        "ERROR": "❌ ",
        "ACTION": "🔧 "
    }
    print(f"{icons.get(status, 'ℹ️ ')} {text}")

def check_python_version():
    """Check Python version."""
    print_header("Python Version Check")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - OK", "SUCCESS")
        return True
    else:
        print_status(f"Python {version.major}.{version.minor} - Needs 3.8+", "ERROR")
        return False

def check_dependencies():
    """Check if required packages are installed."""
    print_header("Checking Dependencies")
    
    required = ["fastapi", "uvicorn", "requests", "python-dotenv"]
    optional = ["pydantic", "sse-starlette"]
    
    all_ok = True
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
            print_status(f"{pkg} - Installed", "SUCCESS")
        except ImportError:
            print_status(f"{pkg} - NOT INSTALLED", "ERROR")
            all_ok = False
    
    for pkg in optional:
        try:
            __import__(pkg.replace("-", "_"))
            print_status(f"{pkg} - Installed", "SUCCESS")
        except ImportError:
            print_status(f"{pkg} - Optional (not installed)", "WARNING")
    
    return all_ok

def check_api_keys():
    """Check API key configuration."""
    print_header("API Key Configuration")
    
    backend_dir = Path(__file__).parent
    env_file = backend_dir / ".env"
    
    # Load .env if exists
    env_vars = {}
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    
    # Check each API key
    checks = [
        ("NVIDIA_API_KEY", "NVIDIA API (Qwen 3.5 397B)", "https://build.nvidia.com/"),
        ("GLM_API_KEY", "GLM-5 (Zhipu AI)", "https://bigmodel.cn/"),
        ("SILICON_API_KEY", "SiliconFlow", "https://siliconflow.cn/"),
        ("OPENROUTER_API_KEY", "OpenRouter", "https://openrouter.ai/"),
        ("BRAVE_API_KEY", "Brave Search", "https://brave.com/search/api/"),
    ]
    
    configured = []
    for key, name, url in checks:
        value = env_vars.get(key, os.environ.get(key, ""))
        
        if value and len(value) > 10 and not value.endswith("-your-api-key-here"):
            print_status(f"{name}: ✅ Configured", "SUCCESS")
            configured.append(key)
        elif key == "NVIDIA_API_KEY":
            print_status(f"{name}: ❌ NOT CONFIGURED - Get key from {url}", "ERROR")
        else:
            print_status(f"{name}: ⚠️ Not configured (optional) - Get key from {url}", "WARNING")
    
    return configured

def test_nvidia_api():
    """Test NVIDIA API connection."""
    print_header("Testing NVIDIA API")
    
    api_key = os.environ.get("NVIDIA_API_KEY", "")
    if not api_key:
        print_status("NVIDIA_API_KEY not set", "ERROR")
        return False
    
    try:
        import requests
        
        response = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen/qwen3.5-397b-a17b",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 50
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print_status("NVIDIA API: ✅ Connected successfully!", "SUCCESS")
            data = response.json()
            print(f"   Model: qwen/qwen3.5-397b-a17b")
            print(f"   Response: {data['choices'][0]['message']['content'][:100]}...")
            return True
        else:
            print_status(f"NVIDIA API: ❌ Error {response.status_code}", "ERROR")
            print(f"   {response.text[:200]}")
            return False
            
    except Exception as e:
        print_status(f"NVIDIA API: ❌ Connection failed: {e}", "ERROR")
        return False

def test_ollama():
    """Test Ollama connection."""
    print_header("Testing Ollama (Local)")
    
    try:
        import requests
        
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            print_status("Ollama: ✅ Connected successfully!", "SUCCESS")
            data = response.json()
            models = [m["name"] for m in data.get("models", [])[:5]]
            print(f"   Available models: {', '.join(models)}")
            return True
        else:
            print_status(f"Ollama: ❌ Error {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Ollama: ❌ Not available ({e})", "WARNING")
        print("   This is OK if you're using cloud APIs instead")
        return False

def generate_env_file():
    """Generate .env file from template."""
    print_header("Generating .env File")
    
    backend_dir = Path(__file__).parent
    env_example = backend_dir / ".env.example"
    env_file = backend_dir / ".env"
    
    if env_file.exists():
        print_status(".env file already exists", "WARNING")
        return
    
    if env_example.exists():
        with open(env_example) as f:
            content = f.read()
        
        with open(env_file, "w") as f:
            f.write(content)
        
        print_status("Created .env file from template", "SUCCESS")
        print_status("Please edit .env and add your API keys", "ACTION")
    else:
        print_status(".env.example not found", "ERROR")

def show_quick_start():
    """Show quick start instructions."""
    print_header("Quick Start Guide")
    
    print("""
1. Edit the .env file:
   nano backend/.env
   # or on Windows:
   notepad backend/.env

2. Add your NVIDIA API key:
   NVIDIA_API_KEY=nvapi-your-actual-key-here

3. Start the server:
   python backend/main.py --server

4. Open in browser:
   http://127.0.0.1:7860

For help:
- NVIDIA API: https://build.nvidia.com/
- Documentation: See README.md
""")

def main():
    """Main setup function."""
    print("\n" + "="*60)
    print("  CLAWFORGE SETUP & DIAGNOSTIC TOOL")
    print("="*60)
    
    # Run all checks
    check_python_version()
    check_dependencies()
    check_api_keys()
    test_ollama()
    generate_env_file()
    
    print("\n" + "="*60)
    print("  SETUP COMPLETE")
    print("="*60)
    
    print("""
Next steps:
1. Add your API keys to backend/.env
2. Run: python backend/main.py --server
3. Open: http://127.0.0.1:7860

For cloud API (NVIDIA), no Ollama needed.
For local AI, install Ollama from https://ollama.com/
""")

if __name__ == "__main__":
    main()
