# test_nvidia_api.py - Test NVIDIA API for Qwen3.5-397B

import requests
import base64
import os
import sys

def read_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def test_nvidia_api(api_key=None):
    """Test NVIDIA API with Qwen3.5-397B."""
    
    # Get API key from env or parameter
    key = api_key or os.environ.get("NVIDIA_API_KEY")
    
    if not key:
        print("No API key provided!")
        print("Usage:")
        print("  python test_nvidia_api.py YOUR_API_KEY")
        print("  or")
        print("  $env:NVIDIA_API_KEY = 'your_key'")
        print("  python test_nvidia_api.py")
        return None
    
    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "text/event-stream"
    }
    
    payload = {
        "model": "qwen/qwen3.5-397b-a17b",
        "messages": [{"role": "user", "content": "Say hello and confirm you're working!"}],
        "max_tokens": 1024,
        "temperature": 0.60,
        "top_p": 0.95,
        "stream": False,  # Simple test without streaming
    }
    
    print("Testing NVIDIA API with Qwen3.5-397B...")
    print("-" * 50)
    
    try:
        response = requests.post(invoke_url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            print("SUCCESS!")
            print(f"\nResponse:\n{content}")
            return {"success": True, "response": content}
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return {"success": False, "error": response.text}
            
    except Exception as e:
        print(f"Exception: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Try to get key from command line
    api_key = sys.argv[1] if len(sys.argv) > 1 else None
    result = test_nvidia_api(api_key)
    
    if result and result["success"]:
        print("\n" + "="*50)
        print("NVIDIA API is working! Qwen3.5-397B is ready.")
        print("="*50)
