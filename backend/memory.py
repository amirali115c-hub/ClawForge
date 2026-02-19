# memory.py - MemoryVault for ClawForge

"""
Two-level memory system for ClawForge:
- SHORT-TERM: Per task session only
- LONG-TERM: Persists across tasks in user_profile.json
- Context state management to prevent context overload
"""

import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

# ============================================================================
# WORKSPACE ROOT
# ============================================================================

WORKSPACE_ROOT = "./workspace"
MEMORY_FILE = f"{WORKSPACE_ROOT}/memory/user_profile.json"

# ============================================================================
# SHORT-TERM MEMORY CLASS
# ============================================================================

class ShortTermMemory:
    """
    Stores task-scoped data only. Cleared when task ends.
    """
    
    def __init__(self, task_id: str):
        """
        Initialize short-term memory for a task.
        
        Args:
            task_id: The task identifier
        """
        self.task_id = task_id
        self._data = {
            "task_id": task_id,
            "user_instructions": [],
            "file_paths": [],
            "progress": "",
            "current_step": "",
            "last_tool_result": None,
            "notes": [],
            "created_at": datetime.utcnow().isoformat()
        }
    
    def set(self, key: str, value: Any):
        """Sets a value in short-term memory."""
        self._data[key] = value
    
    def get(self, key: str, default=None) -> Any:
        """Gets a value from short-term memory."""
        return self._data.get(key, default)
    
    def add_instruction(self, instruction: str):
        """Adds a user instruction with timestamp."""
        self._data["user_instructions"].append({
            "instruction": instruction,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def add_file_path(self, path: str):
        """Adds a file path (prevents duplicates)."""
        if path not in self._data["file_paths"]:
            self._data["file_paths"].append(path)
    
    def update_progress(self, progress: str, step: str = None):
        """Updates current progress and step."""
        self._data["progress"] = progress
        if step:
            self._data["current_step"] = step
    
    def add_note(self, note: str):
        """Adds a note with timestamp."""
        self._data["notes"].append({
            "note": note,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Returns copy of short-term memory."""
        return self._data.copy()
    
    def to_state_object(
        self,
        goal: str = "",
        pending_approvals: List[str] = None,
        risk_score: int = 0
    ) -> Dict[str, Any]:
        """
        Compact context state object to prevent context overload.
        
        Args:
            goal: Task goal
            pending_approvals: List of pending approvals
            risk_score: Current risk score
        
        Returns:
            Compact state dictionary
        """
        return {
            "task_id": self.task_id,
            "goal": goal,
            "progress": self._data.get("progress", ""),
            "current_step": self._data.get("current_step", ""),
            "files_created": len(self._data.get("file_paths", [])),
            "pending_approvals": pending_approvals or [],
            "risk_score": risk_score,
            "instruction_count": len(self._data.get("user_instructions", [])),
            "note_count": len(self._data.get("notes", []))
        }
    
    def summarize(self) -> str:
        """Returns compact string summary of session state."""
        files = len(self._data.get("file_paths", []))
        instructions = len(self._data.get("user_instructions", []))
        notes = len(self._data.get("notes", []))
        progress = self._data.get("progress", "Not started")
        
        return f"Task: {self.task_id} | Progress: {progress} | Files: {files} | Instructions: {instructions} | Notes: {notes}"
    
    def clear(self):
        """Clears short-term memory (keeps task_id)."""
        self._data = {
            "task_id": self.task_id,
            "user_instructions": [],
            "file_paths": [],
            "progress": "",
            "current_step": "",
            "last_tool_result": None,
            "notes": [],
            "created_at": datetime.utcnow().isoformat()
        }

# ============================================================================
# LONG-TERM MEMORY CLASS
# ============================================================================

class LongTermMemory:
    """
    Persists user preferences, templates, and workflows across all sessions.
    """
    
    def __init__(self, memory_file: str = MEMORY_FILE):
        """
        Initialize long-term memory.
        
        Args:
            memory_file: Path to the memory JSON file
        """
        self.memory_file = memory_file
        self._profile = self._load_profile()
    
    def _load_profile(self) -> Dict[str, Any]:
        """Loads the user profile from disk."""
        default_profile = {
            "version": "1.0",
            "created_at": None,
            "last_updated": None,
            "user_preferences": {
                "language": "English",
                "output_verbosity": "standard",
                "auto_save": True,
            },
            "writing_tone": "professional",
            "frequently_used_templates": [],
            "common_workflows": [],
            "task_history": [],
            "saved_snippets": {},
            "blocked_domains": [],
            "allowed_domains": [],
            "security_mode": "LOCKED",
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        
        # Load or create profile
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    profile = json.load(f)
                    # Merge with defaults for missing keys
                    for key, value in default_profile.items():
                        if key not in profile:
                            profile[key] = value
                    return profile
            except (json.JSONDecodeError, IOError):
                return default_profile.copy()
        else:
            return default_profile.copy()
    
    def _save_profile(self):
        """Saves the user profile to disk."""
        self._profile["last_updated"] = datetime.utcnow().isoformat()
        with open(self.memory_file, 'w') as f:
            json.dump(self._profile, f, indent=2)
    
    # ============================================================================
    # READ METHODS
    # ============================================================================
    
    def get(self, key: str, default=None) -> Any:
        """Gets any value from profile."""
        return self._profile.get(key, default)
    
    def get_preference(self, key: str, default=None) -> Any:
        """Gets a user preference value."""
        return self._profile.get("user_preferences", {}).get(key, default)
    
    def get_writing_tone(self) -> str:
        """Returns current writing tone (default: professional)."""
        return self._profile.get("writing_tone", "professional")
    
    def get_templates(self) -> List[Dict[str, str]]:
        """Returns list of frequently used templates."""
        return self._profile.get("frequently_used_templates", [])
    
    def get_workflows(self) -> List[Dict[str, Any]]:
        """Returns list of common workflows."""
        return self._profile.get("common_workflows", [])
    
    def get_snippet(self, name: str) -> Optional[str]:
        """Returns a saved code/text snippet by name."""
        return self._profile.get("saved_snippets", {}).get(name)
    
    def get_security_mode(self) -> str:
        """Returns current security mode."""
        return self._profile.get("security_mode", "LOCKED")
    
    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns task history."""
        history = self._profile.get("task_history", [])
        return history[-limit:]
    
    def full_profile(self) -> Dict[str, Any]:
        """Returns complete profile copy."""
        return self._profile.copy()
    
    # ============================================================================
    # WRITE METHODS
    # ============================================================================
    
    def set(self, key: str, value: Any):
        """Sets any value in profile."""
        self._profile[key] = value
        self._save_profile()
    
    def set_preference(self, key: str, value: Any):
        """Sets a user preference."""
        if "user_preferences" not in self._profile:
            self._profile["user_preferences"] = {}
        self._profile["user_preferences"][key] = value
        self._save_profile()
    
    def set_writing_tone(self, tone: str):
        """
        Sets writing tone. Valid options:
        - professional
        - casual
        - technical
        - friendly
        - academic
        """
        valid_tones = ["professional", "casual", "technical", "friendly", "academic"]
        if tone not in valid_tones:
            tone = "professional"
        
        self._profile["writing_tone"] = tone
        self._save_profile()
    
    def add_template(self, name: str, content: str, category: str = "general"):
        """Adds or updates a template. Keeps last 20."""
        if "frequently_used_templates" not in self._profile:
            self._profile["frequently_used_templates"] = []
        
        # Remove existing template with same name
        self._profile["frequently_used_templates"] = [
            t for t in self._profile["frequently_used_templates"]
            if t.get("name") != name
        ]
        
        # Add new template
        self._profile["frequently_used_templates"].append({
            "name": name,
            "content": content,
            "category": category,
            "created_at": datetime.utcnow().isoformat()
        })
        
        # Keep only last 20
        self._profile["frequently_used_templates"] = self._profile["frequently_used_templates"][-20:]
        
        self._save_profile()
    
    def add_workflow(self, name: str, steps: List[str], category: str = "general"):
        """Adds or updates a workflow. Keeps last 20."""
        if "common_workflows" not in self._profile:
            self._profile["common_workflows"] = []
        
        # Remove existing workflow with same name
        self._profile["common_workflows"] = [
            w for w in self._profile["common_workflows"]
            if w.get("name") != name
        ]
        
        # Add new workflow
        self._profile["common_workflows"].append({
            "name": name,
            "steps": steps,
            "category": category,
            "created_at": datetime.utcnow().isoformat()
        })
        
        # Keep only last 20
        self._profile["common_workflows"] = self._profile["common_workflows"][-20:]
        
        self._save_profile()
    
    def save_snippet(self, name: str, content: str):
        """Saves a code or text snippet by name."""
        if "saved_snippets" not in self._profile:
            self._profile["saved_snippets"] = {}
        
        self._profile["saved_snippets"][name] = content
        self._save_profile()
    
    def log_task(self, task_id: str, goal: str, status: str, risk_score: int):
        """
        Records a completed task in history.
        Keeps last 50 task summaries.
        """
        if "task_history" not in self._profile:
            self._profile["task_history"] = []
        
        self._profile["task_history"].append({
            "task_id": task_id,
            "goal": goal,
            "status": status,
            "risk_score": risk_score,
            "completed_at": datetime.utcnow().isoformat()
        })
        
        # Keep only last 50
        self._profile["task_history"] = self._profile["task_history"][-50:]
        
        self._save_profile()
    
    def set_security_mode(self, mode: str):
        """Sets the security mode (LOCKED/SAFE/DEVELOPER)."""
        valid_modes = ["LOCKED", "SAFE", "DEVELOPER"]
        if mode not in valid_modes:
            mode = "LOCKED"
        
        self._profile["security_mode"] = mode
        self._save_profile()

# ============================================================================
# MEMORY VAULT CLASS
# ============================================================================

class MemoryVault:
    """
    Unified interface to both short-term and long-term memory.
    """
    
    def __init__(self, task_id: str = None):
        """
        Initialize both short-term and long-term memory.
        
        Args:
            task_id: Optional task ID for short-term memory
        """
        self.short_term = ShortTermMemory(task_id or "default") if task_id else None
        self.long_term = LongTermMemory()
    
    def new_task(self, task_id: str):
        """Start a new short-term memory context."""
        self.short_term = ShortTermMemory(task_id)
    
    def save_context(
        self,
        goal: str = "",
        pending_approvals: List[str] = None,
        risk_score: int = 0
    ) -> Dict[str, Any]:
        """
        Returns compact state object (prevents context window overload).
        """
        if self.short_term:
            return self.short_term.to_state_object(goal, pending_approvals, risk_score)
        return {"error": "No short-term memory context"}
    
    def summarize_session(self) -> str:
        """Returns compact string summary of current session."""
        if self.short_term:
            return self.short_term.summarize()
        return "No active session"
    
    def remember_instruction(self, instruction: str):
        """Stores instruction in short-term memory."""
        if self.short_term:
            self.short_term.add_instruction(instruction)
    
    def remember_file(self, path: str):
        """Stores file path in short-term memory."""
        if self.short_term:
            self.short_term.add_file_path(path)
    
    def update_progress(self, progress: str, step: str = None):
        """Updates progress in short-term memory."""
        if self.short_term:
            self.short_term.update_progress(progress, step)
    
    def get_tone(self) -> str:
        """Gets writing tone from long-term memory."""
        return self.long_term.get_writing_tone()
    
    def get_template(self, name: str) -> Optional[Dict[str, str]]:
        """Gets a template by name from long-term memory."""
        for template in self.long_term.get_templates():
            if template.get("name") == name:
                return template
        return None
    
    def get_all_templates(self) -> List[Dict[str, str]]:
        """Gets all templates from long-term memory."""
        return self.long_term.get_templates()
    
    def end_task(self, status: str, risk_score: int):
        """
        Finalizes a task:
        1. Logs task to long-term history
        2. Clears short-term memory
        """
        if self.short_term:
            # Log to history
            self.long_term.log_task(
                task_id=self.short_term.task_id,
                goal=self.short_term.get("goal", ""),
                status=status,
                risk_score=risk_score
            )
            
            # Clear short-term
            self.short_term.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Returns summary of both memory layers."""
        return {
            "short_term": self.short_term.to_dict() if self.short_term else None,
            "long_term": {
                "writing_tone": self.long_term.get_writing_tone(),
                "security_mode": self.long_term.get_security_mode(),
                "template_count": len(self.long_term.get_templates()),
                "workflow_count": len(self.long_term.get_workflows()),
                "snippet_count": len(self.long_term.get("saved_snippets", {})),
                "task_history_count": len(self.long_term.get_task_history())
            }
        }

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_vault(task_id: str = None) -> MemoryVault:
    """Create a new memory vault."""
    return MemoryVault(task_id)

if __name__ == "__main__":
    print("🐾 ClawForge MemoryVault - Test")
    print("=" * 50)
    
    # Test long-term memory
    print("\n📚 Long-Term Memory Test:")
    ltm = LongTermMemory()
    
    ltm.set_writing_tone("professional")
    print(f"   Writing tone: {ltm.get_writing_tone()}")
    
    ltm.set_security_mode("DEVELOPER")
    print(f"   Security mode: {ltm.get_security_mode()}")
    
    ltm.add_template("blog_post", "# Blog Post\n\n## Introduction", "writing")
    templates = ltm.get_templates()
    print(f"   Templates: {len(templates)}")
    
    ltm.save_snippet("header", "# My Header")
    print(f"   Snippets: {ltm.get_snippet('header')}")
    
    # Test short-term memory
    print("\n📝 Short-Term Memory Test:")
    stm = ShortTermMemory("task_001")
    
    stm.add_instruction("Write a blog post")
    stm.add_file_path("./workspace/blog.md")
    stm.update_progress("50%", "Writing conclusion")
    
    print(f"   Summary: {stm.summarize()}")
    print(f"   State: {stm.to_state_object('Write a blog')}")
    
    # Test MemoryVault
    print("\n🔐 MemoryVault Test:")
    vault = MemoryVault("task_002")
    
    vault.remember_instruction("Create a document")
    vault.remember_file("./workspace/doc.docx")
    vault.update_progress("75%")
    
    print(f"   Session: {vault.summarize_session()}")
    print(f"   Writing tone: {vault.get_tone()}")
    
    # End task
    vault.end_task("COMPLETED", 5)
    print(f"   Task ended and logged to history")
    
    # Check history
    history = ltm.get_task_history()
    print(f"   Task history: {len(history)} tasks")
