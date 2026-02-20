"""
Leo 2.0 - Gradio UI Integration
==============================
Alternative web interface using Gradio.
"""

import json
from typing import Optional

# Check if Gradio is available
try:
    import gradio as gr
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False
    print("[GRADIO] Not installed. Run: pip install gradio")


class GradioInterface:
    """Gradio-based interface for Leo 2.0."""
    
    def __init__(self, api_base: str = "http://127.0.0.1:9000"):
        self.api_base = api_base
        self.demo = None
    
    def chat(self, message: str, history: list = None) -> tuple:
        """Handle chat messages."""
        import urllib.request
        
        if history is None:
            history = []
        
        try:
            # Send to API
            data = json.dumps({
                "message": message,
                "mode": "chat"
            }).encode('utf-8')
            
            req = urllib.request.Request(
                f"{self.api_base}/api/chat",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            response = urllib.request.urlopen(req, timeout=120)
            result = json.loads(response.read().decode())
            
            reply = result.get("response", "No response")
            history.append((message, reply))
            
        except Exception as e:
            history.append((message, f"Error: {str(e)}"))
        
        return "", history
    
    def create_interface(self):
        """Create Gradio interface."""
        if not GRADIO_AVAILABLE:
            return None
        
        self.demo = gr.ChatInterface(
            fn=self.chat,
            title="Leo 2.0 - AI Assistant",
            description="Self-learning AI agent powered by NEURON v2.0",
            examples=[
                ["Hello, how are you?"],
                ["Search for Python tutorials"],
                ["Remember that I like pizza"],
                ["What do you know about me?"]
            ],
            theme=gr.themes.Soft()
        )
        
        return self.demo
    
    def launch(self, share: bool = False, port: int = 7860):
        """Launch Gradio interface."""
        if not GRADIO_AVAILABLE:
            print("Gradio not available. Install with: pip install gradio")
            return
        
        if self.demo is None:
            self.create_interface()
        
        if self.demo:
            self.demo.launch(server_name="0.0.0.0", server_port=share, share=share)
        else:
            print("Failed to create Gradio interface")


def create_gradio_app():
    """Create and return Gradio app."""
    if not GRADIO_AVAILABLE:
        return None
    
    interface = GradioInterface()
    return interface.create_interface()


# Main entry point
if __name__ == "__main__":
    if GRADIO_AVAILABLE:
        app = create_gradio_app()
        if app:
            app.launch(server_name="0.0.0.0", server_port=7860)
    else:
        print("Gradio not installed. Install with: pip install gradio")
