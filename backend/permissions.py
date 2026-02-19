# permissions.py - PermissionManager for ClawForge

"""
ClawForge - PermissionManager
==============================
Explicit YES/NO approval gating for all risky operations.
Enforces the master prompt permission requirements:
  - terminal command execution
  - download file
  - install package
  - run script
  - screen control
  - browser automation
  - editing important documents
  - VBA macros
  - network access

All approvals are logged with timestamp, task ID, and outcome.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# ============================================================================
# PERMISSION CATEGORIES
# ============================================================================

PERMISSION_CATEGORIES = {
    "terminal_command": {
        "label": "Terminal Command Execution",
        "description": "Execute a command in the system terminal",
        "risk_level": "HIGH",
        "risk_points": 4,
        "icon": "💻",
    },
    "download_file": {
        "label": "File Download",
        "description": "Download a file from the internet to workspace/downloads/",
        "risk_level": "HIGH",
        "risk_points": 5,
        "icon": "⬇️",
    },
    "install_package": {
        "label": "Package Installation",
        "description": "Install a software package (pip/npm)",
        "risk_level": "HIGH",
        "risk_points": 5,
        "icon": "📦",
    },
    "run_script": {
        "label": "Script Execution",
        "description": "Run a Python or Node.js script",
        "risk_level": "HIGH",
        "risk_points": 4,
        "icon": "▶️",
    },
    "screen_control": {
        "label": "Screen / UI Control",
        "description": "Control mouse, keyboard, or screen",
        "risk_level": "CRITICAL",
        "risk_points": 7,
        "icon": "🖥️",
    },
    "browser_automation": {
        "label": "Browser Automation",
        "description": "Open URLs, extract content, or navigate the browser",
        "risk_level": "HIGH",
        "risk_points": 6,
        "icon": "🌐",
    },
    "edit_document": {
        "label": "Edit Important Document",
        "description": "Modify an existing important file or document",
        "risk_level": "MEDIUM",
        "risk_points": 3,
        "icon": "📝",
    },
    "vba_macro": {
        "label": "VBA Macro Execution",
        "description": "Run a VBA macro inside Excel or Office",
        "risk_level": "HIGH",
        "risk_points": 6,
        "icon": "⚙️",
    },
    "network_access": {
        "label": "Network Access",
        "description": "Enable network tools for external connections",
        "risk_level": "HIGH",
        "risk_points": 5,
        "icon": "🔌",
    },
    "delete_file": {
        "label": "File Deletion",
        "description": "Permanently delete a file inside workspace",
        "risk_level": "MEDIUM",
        "risk_points": 3,
        "icon": "🗑️",
    },
}

# ============================================================================
# APPROVAL RECORD
# ============================================================================

class ApprovalRecord:
    def __init__(
        self,
        task_id: str,
        category: str,
        action_detail: str,
        outcome: str,  # "granted" / "denied" / "pending"
        user_response: Optional[str] = None,
    ):
        self.task_id = task_id
        self.category = category
        self.action_detail = action_detail
        self.outcome = outcome
        self.user_response = user_response
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "task_id": self.task_id,
            "category": self.category,
            "action_detail": self.action_detail[:200],
            "outcome": self.outcome,
            "user_response": self.user_response,
            "risk_points": PERMISSION_CATEGORIES.get(self.category, {}).get("risk_points", 0),
        }

# ============================================================================
# PERMISSION MANAGER
# ============================================================================

class PermissionManager:
    """
    Manages all permission requests and approvals for ClawForge.
    Every risky operation requires explicit YES/NO before execution.
    All decisions are logged.
    """
    
    def __init__(self, task_id: str = "global"):
        self.task_id = task_id
        self._approval_log: List[ApprovalRecord] = []
        self._granted_cache: Dict[str, bool] = {}  # category -> bool
        
        # Set log path
        try:
            from backend.identity import WORKSPACE_PATHS
            self._log_path = Path(WORKSPACE_PATHS.get("logs", "./workspace/logs")) / "approvals.jsonl"
        except ImportError:
            self._log_path = Path("./workspace/logs") / "approvals.jsonl"
        
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # ============================================================================
    # BUILD REQUEST PROMPT
    # ============================================================================
    
    def build_request_prompt(
        self,
        category: str,
        action_detail: str,
        command_preview: Optional[str] = None,
        file_info: Optional[dict] = None,
    ) -> str:
        """
        Builds the formatted permission request string shown to the user.
        """
        meta = PERMISSION_CATEGORIES.get(category, {
            "label": category,
            "risk_level": "UNKNOWN",
            "risk_points": 5,
            "icon": "⚠️",
            "description": "Unknown action type"
        })
        
        risk_color_map = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
        }
        risk_icon = risk_color_map.get(meta["risk_level"], "⚪")
        
        lines = [
            f"╔════════════════════════════════════════════════════════════════╗",
            f"║           PERMISSION REQUEST                              ║",
            f"╚════════════════════════════════════════════════════════════════╝",
            f"",
            f"  {meta['icon']}  {meta['label']}",
            f"  {risk_icon} Risk Level : {meta['risk_level']}  (+{meta['risk_points']} risk points)",
            f"  📋 Task ID  : {self.task_id}",
            f"",
            f"  Action: {action_detail}",
        ]
        
        if command_preview:
            lines.extend([
                f"",
                f"  Command Preview:",
                f"  {'─' * 50}",
                f"  {command_preview[:50]}",
                f"  {'─' * 50}",
            ])
        
        if file_info:
            lines.extend([
                f"",
                f"  File Info:",
                f"    Name  : {file_info.get('filename', 'unknown')}",
                f"    Type  : {file_info.get('type', 'unknown')}",
                f"    Size  : {file_info.get('size', 'unknown')}",
                f"    Source: {file_info.get('url', 'local')}",
            ])
        
        lines.extend([
            f"",
            f"  ┌──────────────────────────────────────────────────────┐",
            f"  │  Do you approve this action?                         │",
            f"  │                                                      │",
            f"  │    Type  YES  to allow    │    Type  NO  to cancel   │",
            f"  └──────────────────────────────────────────────────────┘",
            f"",
        ])
        
        return "\n".join(lines)
    
    # ============================================================================
    # REQUEST + EVALUATE
    # ============================================================================
    
    def request(
        self,
        category: str,
        action_detail: str,
        user_response: Optional[str] = None,
        command_preview: Optional[str] = None,
        file_info: Optional[dict] = None,
    ) -> dict:
        """
        Processes a permission request.
        If user_response is provided, evaluates it immediately.
        If not, returns the prompt for the caller to show the user.
        """
        prompt = self.build_request_prompt(category, action_detail, command_preview, file_info)
        
        if user_response is None:
            # No response yet — return the prompt
            record = ApprovalRecord(self.task_id, category, action_detail, "pending")
            self._log(record)
            return {
                "status": "awaiting_response",
                "prompt": prompt,
                "category": category,
                "risk_points": PERMISSION_CATEGORIES.get(category, {}).get("risk_points", 5),
            }
        
        # Evaluate response
        return self.evaluate(category, action_detail, user_response)
    
    def evaluate(self, category: str, action_detail: str, user_response: str) -> dict:
        """
        Evaluates user response (YES/NO) and records the decision.
        """
        response_clean = user_response.strip().upper()
        
        # Accept variants of YES
        approved = response_clean in ("YES", "Y", "APPROVE", "OK", "ALLOW", "1", "TRUE")
        
        outcome = "granted" if approved else "denied"
        record = ApprovalRecord(self.task_id, category, action_detail, outcome, user_response)
        self._approval_log.append(record)
        self._log(record)
        
        if approved:
            self._granted_cache[category] = True
        
        meta = PERMISSION_CATEGORIES.get(category, {})
        
        return {
            "status": outcome,
            "approved": approved,
            "category": category,
            "action_detail": action_detail,
            "risk_points": meta.get("risk_points", 5) if approved else 0,
            "message": (
                f"Permission GRANTED: {meta.get('label', category)}"
                if approved else
                f"Permission DENIED: {meta.get('label', category)} — action cancelled."
            ),
        }
    
    # ============================================================================
    # DOWNLOAD PRE-CHECK
    # ============================================================================
    
    def build_download_prompt(self, filename: str, filetype: str, size: str, url: str) -> dict:
        """
        Builds a pre-download approval request showing all file details.
        """
        file_info = {
            "filename": filename,
            "type": filetype,
            "size": size,
            "url": url,
        }
        return self.request(
            category="download_file",
            action_detail=f"Download '{filename}' from {url[:60]}",
            file_info=file_info,
        )
    
    # ============================================================================
    # SCREEN CONTROL GATE
    # ============================================================================
    
    def screen_control_gate(self, action_description: str, user_response: Optional[str] = None) -> dict:
        """
        Specialized gate for screen/UI control.
        Always ask "Do you approve screen control? YES/NO"
        """
        return self.request(
            category="screen_control",
            action_detail=action_description,
            user_response=user_response,
        )
    
    # ============================================================================
    # REPORTING
    # ============================================================================
    
    def get_log(self) -> List[dict]:
        return [r.to_dict() for r in self._approval_log]
    
    def get_summary(self) -> dict:
        log = self.get_log()
        return {
            "total_requests": len(log),
            "granted": sum(1 for r in log if r["outcome"] == "granted"),
            "denied": sum(1 for r in log if r["outcome"] == "denied"),
            "pending": sum(1 for r in log if r["outcome"] == "pending"),
            "total_risk_points_granted": sum(
                r["risk_points"] for r in log if r["outcome"] == "granted"
            ),
            "approvals": log,
        }
    
    def _log(self, record: ApprovalRecord):
        """Appends approval record to persistent log."""
        try:
            with open(self._log_path, "a") as f:
                f.write(json.dumps(record.to_dict()) + "\n")
        except Exception:
            pass
    
    def is_allowed(self, category: str) -> bool:
        """Check if a category was approved in this session."""
        return self._granted_cache.get(category, False)

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def request_permission(
    category: str,
    action_detail: str,
    user_response: Optional[str] = None,
    task_id: str = "global",
) -> dict:
    """Request permission for an action."""
    pm = PermissionManager(task_id=task_id)
    return pm.request(category, action_detail, user_response)

def check_permission(category: str, task_id: str = "global") -> dict:
    """Check permission status for a category."""
    pm = PermissionManager(task_id=task_id)
    return {"allowed": pm.is_allowed(category), "category": category}

# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("PermissionManager Test\n")

    pm = PermissionManager(task_id="task_test_permissions")

    tests = [
        ("terminal_command", "ls -la ./workspace", "YES"),
        ("download_file", "Download report.pdf from https://example.com", "NO"),
        ("screen_control", "Take a screenshot of the current screen", "YES"),
        ("run_script", "Run ./workspace/tasks/task_001/output/main.py", "YES"),
        ("install_package", "pip install requests", "NO"),
        ("browser_automation", "Open Chrome and navigate to https://example.com", "YES"),
        ("vba_macro", "Run Excel macro: GenerateReport()", "NO"),
    ]

    for category, detail, response in tests:
        result = pm.evaluate(category, detail, response)
        icon = "✅" if result["approved"] else "❌"
        print(f"{icon} [{category}] → {result['status']} | Risk: +{result['risk_points']}")
        print(f"   {result['message']}\n")

    # Download pre-check demo
    print("📥 Download Pre-Check:")
    dl = pm.build_download_prompt(
        filename="report.pdf",
        filetype="PDF",
        size="2.3 MB",
        url="https://example.com/reports/Q3.pdf"
    )
    print(dl["prompt"][:300] + "...\n")

    summary = pm.get_summary()
    print(f"📊 Summary: {summary['granted']} granted, {summary['denied']} denied")
    print(f"   Total risk from approved actions: +{summary['total_risk_points_granted']}")
    print("\n✅ PermissionManager test complete.")
