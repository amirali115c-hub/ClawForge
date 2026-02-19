# tools.py - ToolRouter + All Tool Categories for ClawForge

"""
Implements all 6 tool categories with firewall and permission gating.
Every tool call passes through ToolRouter for validation.
"""

import os
import re
import time
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

# ============================================================================
# TOOL REGISTRY
# ============================================================================

ALL_TOOLS = {
    # File Tools
    "read_file": {"category": "file", "requires_permission": False, "risk": 1},
    "write_file": {"category": "file", "requires_permission": False, "risk": 1},
    "create_folder": {"category": "file", "requires_permission": False, "risk": 0},
    "move_file": {"category": "file", "requires_permission": False, "risk": 1},
    "delete_file": {"category": "file", "requires_permission": True, "risk": 3},
    
    # Terminal Tools
    "run_command": {"category": "terminal", "requires_permission": True, "risk": 4},
    "list_processes": {"category": "terminal", "requires_permission": False, "risk": 1},
    "check_disk_usage": {"category": "terminal", "requires_permission": False, "risk": 1},
    
    # UI Tools
    "take_screenshot": {"category": "ui", "requires_permission": True, "risk": 2},
    "click": {"category": "ui", "requires_permission": True, "risk": 7},
    "type_text": {"category": "ui", "requires_permission": True, "risk": 7},
    "scroll": {"category": "ui", "requires_permission": True, "risk": 7},
    "open_app": {"category": "ui", "requires_permission": True, "risk": 5},
    "switch_window": {"category": "ui", "requires_permission": True, "risk": 3},
    "copy_paste": {"category": "ui", "requires_permission": True, "risk": 3},
    
    # Browser Tools
    "open_url": {"category": "browser", "requires_permission": True, "risk": 3},
    "extract_text": {"category": "browser", "requires_permission": True, "risk": 2},
    "download_file": {"category": "browser", "requires_permission": True, "risk": 5},
    
    # Code Tools
    "run_python": {"category": "code", "requires_permission": True, "risk": 4},
    "run_node": {"category": "code", "requires_permission": True, "risk": 4},
    "lint_code": {"category": "code", "requires_permission": False, "risk": 1},
    
    # Office Tools
    "create_docx": {"category": "office", "requires_permission": False, "risk": 1},
    "create_pdf": {"category": "office", "requires_permission": False, "risk": 1},
    "create_excel": {"category": "office", "requires_permission": False, "risk": 1},
    "update_excel": {"category": "office", "requires_permission": False, "risk": 1},
    "analyze_excel": {"category": "office", "requires_permission": False, "risk": 1}
}

# ============================================================================
# SECURITY MODE CONFIGURATION
# ============================================================================

class SecurityMode:
    LOCKED = "LOCKED"
    SAFE = "SAFE"
    DEVELOPER = "DEVELOPER"

DISABLED_TOOLS_BY_MODE = {
    SecurityMode.LOCKED: [
        "run_command", "run_python", "run_node", "download_file", "open_url",
        "extract_text", "click", "type_text", "scroll", "open_app", "switch_window",
        "copy_paste", "take_screenshot"
    ],
    SecurityMode.SAFE: ["click", "type_text", "scroll", "open_app", "switch_window"],
    SecurityMode.DEVELOPER: []
}

# ============================================================================
# RATE LIMITING
# ============================================================================

RATE_LIMIT_MAX_CALLS = 30
RATE_LIMIT_WINDOW = 60

# ============================================================================
# BLOCKED PATTERNS
# ============================================================================

BLOCKED_PATTERNS = [
    r"rm\s+-rf", r"del\s+/s", r"format\s", r"diskpart", r"\bshutdown\b", r"\breboot\b",
    r"reg\s+add", r"reg\s+delete", r"taskkill", r"Invoke-Expression", r"powershell\s+-enc",
    r"invoke-expression", r"\bcertutil\b", r"\bbitsadmin\b", r"curl\s+\|", r"wget\s+\|",
    r"mshta", r"rundll32", r"sc\s+stop", r"net\s+user", r"net\s+localgroup",
    r"attrib\s+\+h", r"vssadmin\s+delete"
]

# ============================================================================
# TOOL ROUTER CLASS
# ============================================================================

class ToolRouter:
    def __init__(self, security_mode: str = SecurityMode.LOCKED):
        self.security_mode = security_mode
        self._call_history: Dict[str, List[float]] = {}
        self._tool_calls: List[Dict] = []
        self.broadcast_fn: Optional[Callable] = None
    
    def _firewall_check(self, tool_name: str, args: Dict) -> Dict:
        if tool_name not in ALL_TOOLS:
            return {"allowed": False, "reason": f"Tool '{tool_name}' does not exist"}
        
        disabled_tools = DISABLED_TOOLS_BY_MODE.get(self.security_mode, [])
        if tool_name in disabled_tools:
            return {"allowed": False, "reason": f"Tool disabled in {self.security_mode} mode"}
        
        if not isinstance(args, dict):
            return {"allowed": False, "reason": "Arguments must be a dictionary"}
        
        path_args = ["path", "source", "destination", "file_path"]
        for arg_name in path_args:
            if arg_name in args:
                if not self._check_workspace_boundary(args[arg_name]):
                    return {"allowed": False, "reason": f"Path outside workspace"}
        
        if not self._check_rate_limit(tool_name):
            return {"allowed": False, "reason": f"Rate limit exceeded"}
        
        return {"allowed": True, "reason": "All checks passed"}
    
    def _check_workspace_boundary(self, path: str) -> bool:
        workspace_root = Path("./workspace").resolve()
        try:
            resolved_path = Path(path).resolve()
            resolved_path.relative_to(workspace_root)
            return True
        except (ValueError, OSError):
            return False
    
    def _check_rate_limit(self, tool_name: str) -> bool:
        now = time.time()
        if tool_name not in self._call_history:
            self._call_history[tool_name] = []
        self._call_history[tool_name] = [t for t in self._call_history[tool_name] if now - t < RATE_LIMIT_WINDOW]
        return len(self._call_history[tool_name]) < RATE_LIMIT_MAX_CALLS
    
    def call(self, tool_name: str, args: Dict, approved: bool = False) -> Dict[str, Any]:
        start_time = time.time()
        
        firewall_result = self._firewall_check(tool_name, args)
        if not firewall_result["allowed"]:
            return {"status": "blocked", "tool": tool_name, "error": firewall_result["reason"]}
        
        if not approved:
            tool_info = ALL_TOOLS.get(tool_name, {})
            if tool_info.get("requires_permission", False):
                return {"status": "approval_required", "tool": tool_name, "risk_level": tool_info.get("risk", 0)}
        
        result = self._dispatch(tool_name, args)
        duration_ms = int((time.time() - start_time) * 1000)
        
        self._tool_calls.append({
            "timestamp": datetime.utcnow().isoformat(),
            "tool": tool_name,
            "args": args,
            "result": result,
            "approved": approved,
            "duration_ms": duration_ms
        })
        
        return result
    
    def _dispatch(self, tool_name: str, args: Dict) -> Dict:
        tool_info = ALL_TOOLS.get(tool_name, {})
        category = tool_info.get("category", "unknown")
        
        handlers = {
            "file": FileTools.handle,
            "terminal": TerminalTools.handle,
            "ui": UITools.handle,
            "browser": BrowserTools.handle,
            "code": CodeTools.handle,
            "office": OfficeTools.handle
        }
        
        handler = handlers.get(category)
        if handler:
            return handler(tool_name, args)
        return {"status": "error", "error": f"No handler for category: {category}"}

# ============================================================================
# TOOL HANDLERS
# ============================================================================

class FileTools:
    @staticmethod
    def handle(tool_name: str, args: Dict) -> Dict:
        from backend.file_manager import FileManager
        
        if tool_name == "read_file":
            return FileManager.read_file(args.get("path", ""))
        elif tool_name == "write_file":
            return FileManager.write_file(args.get("path", ""), args.get("content", ""))
        elif tool_name == "create_folder":
            return FileManager.create_folder(args.get("path", ""))
        elif tool_name == "move_file":
            return FileManager.move_file(args.get("source", ""), args.get("destination", ""))
        elif tool_name == "delete_file":
            return FileManager.delete_file(args.get("path", ""))
        return {"status": "error", "error": f"Unknown file tool: {tool_name}"}

class TerminalTools:
    @staticmethod
    def handle(tool_name: str, args: Dict) -> Dict:
        import subprocess
        import psutil
        
        if tool_name == "run_command":
            command = args.get("command", "")
            for pattern in BLOCKED_PATTERNS:
                if re.search(pattern, command, re.IGNORECASE):
                    return {"status": "blocked", "error": f"Command blocked: {pattern}"}
            
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30, cwd="./workspace")
                return {"status": "success", "stdout": result.stdout, "stderr": result.stderr, "return_code": result.returncode}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        elif tool_name == "list_processes":
            try:
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        processes.append(proc.info)
                    except: pass
                return {"status": "success", "processes": processes, "count": len(processes)}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        elif tool_name == "check_disk_usage":
            try:
                usage = psutil.disk_usage("./workspace")
                return {"status": "success", "total": usage.total, "used": usage.used, "free": usage.free, "percent": usage.percent}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        return {"status": "error", "error": f"Unknown terminal tool: {tool_name}"}

class UITools:
    @staticmethod
    def handle(tool_name: str, args: Dict) -> Dict:
        try:
            import pyautogui
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.1
            
            if tool_name == "take_screenshot":
                path = args.get("path", "./workspace/screenshot.png")
                pyautogui.screenshot().save(path)
                return {"status": "success", "path": path}
            
            elif tool_name == "click":
                pyautogui.click(x=args.get("x", 0), y=args.get("y", 0))
                return {"status": "success"}
            
            elif tool_name == "type_text":
                pyautogui.write(args.get("text", ""))
                return {"status": "success"}
            
            elif tool_name == "scroll":
                pyautogui.scroll(args.get("amount", 0))
                return {"status": "success"}
            
            return {"status": "error", "error": f"Unknown UI tool: {tool_name}"}
        except ImportError:
            return {"status": "unavailable", "error": "PyAutoGUI not installed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

class BrowserTools:
    ENABLE_NETWORK_TOOLS = False
    ALLOWED_DOMAINS: List[str] = []
    
    @staticmethod
    def handle(tool_name: str, args: Dict) -> Dict:
        if not BrowserTools.ENABLE_NETWORK_TOOLS:
            return {"status": "blocked", "error": "Network tools disabled"}
        
        if tool_name == "open_url":
            try:
                import webbrowser
                webbrowser.open(args.get("url", ""))
                return {"status": "success"}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        return {"status": "error", "error": f"Unknown browser tool: {tool_name}"}

class CodeTools:
    @staticmethod
    def handle(tool_name: str, args: Dict) -> Dict:
        import tempfile
        import subprocess
        import os
        
        if tool_name == "run_python":
            code = args.get("code", "")
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(code)
                    temp_path = f.name
                try:
                    result = subprocess.run(["python", temp_path], capture_output=True, text=True, timeout=30)
                    return {"status": "success", "stdout": result.stdout, "stderr": result.stderr}
                finally:
                    if os.path.exists(temp_path): os.unlink(temp_path)
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        elif tool_name == "lint_code":
            code = args.get("code", "")
            try:
                compile(code, '<string>', 'exec')
                return {"status": "success", "issues": []}
            except SyntaxError as e:
                return {"status": "warning", "issues": [{"type": "error", "message": str(e)}]}
        
        return {"status": "error", "error": f"Unknown code tool: {tool_name}"}

class OfficeTools:
    @staticmethod
    def handle(tool_name: str, args: Dict) -> Dict:
        path = args.get("path", "")
        content = args.get("content", "")
        
        if tool_name == "create_docx":
            try:
                from docx import Document
                doc = Document()
                for paragraph in content.split('\n\n'):
                    if paragraph.strip():
                        doc.add_paragraph(paragraph.strip())
                doc.save(path)
                return {"status": "success", "path": path}
            except ImportError:
                return {"status": "error", "error": "python-docx not installed"}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        elif tool_name == "create_pdf":
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                c = canvas.Canvas(path, pagesize=letter)
                c.drawString(72, 750, args.get("title", "Document"))
                c.save()
                return {"status": "success", "path": path}
            except ImportError:
                return {"status": "error", "error": "reportlab not installed"}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        return {"status": "error", "error": f"Unknown office tool: {tool_name}"}

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_router(security_mode: str = SecurityMode.LOCKED) -> ToolRouter:
    return ToolRouter(security_mode)

if __name__ == "__main__":
    print("ClawForge ToolRouter - Test")
    router = ToolRouter(SecurityMode.DEVELOPER)
    
    result = router.call("create_folder", {"path": "./workspace/test"})
    print(f"create_folder: {result['status']}")
    
    result = router.call("write_file", {"path": "./workspace/test/sample.txt", "content": "Hello!"})
    print(f"write_file: {result['status']}")
    
    result = router.call("read_file", {"path": "./workspace/test/sample.txt"})
    print(f"read_file: {result.get('status')}, content: {result.get('content', '')}")
