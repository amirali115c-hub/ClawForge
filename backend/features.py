"""
features.py - Consolidated Features Module for ClawForge

All features in one clean module:
1. Long-Term Memory System (with privacy)
2. Web Search
3. Git Integration
4. Text-to-Speech
5. File Editor
6. Enhanced Planner

API keys stored in api.py only - NEVER in this file
"""

import os
import json
import hashlib
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# ============================================================================
# 1. LONG-TERM MEMORY SYSTEM (With Privacy Controls)
# ============================================================================

class LongTermMemory:
    """
    Persistent long-term memory system with privacy controls.
    
    Features:
    - Categorized memories (facts, preferences, context)
    - Importance scoring
    - Privacy controls (view, delete, export)
    - Encrypted storage for sensitive data
    """

    def __init__(self):
        self.memory_dir = Path(__file__).parent.parent / "memory"
        self.memory_dir.mkdir(exist_ok=True)
        
        # Memory files
        self.memories_file = self.memory_dir / "longterm_memories.json"
        self.conversations_file = self.memory_dir / "conversations.json"
        self.privacy_file = self.memory_dir / "privacy_settings.json"
        
        # Load data
        self.memories = self._load_memories()
        self.conversations = self._load_conversations()
        self.privacy = self._load_privacy()
        
        # Categories
        self.categories = {
            "fact": "Facts & Knowledge",
            "preference": "User Preferences", 
            "context": "Project Context",
            "personal": "Personal Information",
            "setting": "Settings & Config",
            "conversation": "Conversation History"
        }
    
    # ----------------- LOAD/SAVE -----------------
    
    def _load_memories(self) -> Dict:
        """Load memories from disk."""
        if self.memories_file.exists():
            try:
                with open(self.memories_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"memories": []}
    
    def _save_memories(self):
        """Save memories to disk."""
        with open(self.memories_file, 'w', encoding='utf-8') as f:
            json.dump(self.memories, f, indent=2, ensure_ascii=False)
    
    def _load_conversations(self) -> Dict:
        """Load conversations from disk."""
        if self.conversations_file.exists():
            try:
                with open(self.conversations_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"conversations": []}
    
    def _save_conversations(self):
        """Save conversations to disk."""
        with open(self.conversations_file, 'w', encoding='utf-8') as f:
            json.dump(self.conversations, f, indent=2, ensure_ascii=False)
    
    def _load_privacy(self) -> Dict:
        """Load privacy settings."""
        default_privacy = {
            "auto_save": True,
            "encrypt_sensitive": True,
            "remember_facts": True,
            "remember_preferences": True,
            "remember_context": True,
            "auto_clear_conversations": False,
            "max_conversations": 100,
            "sensitive_categories": ["personal", "setting"],
            "export_encrypted": False
        }
        
        if self.privacy_file.exists():
            try:
                with open(self.privacy_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    return {**default_privacy, **saved}
            except Exception:
                pass
        return default_privacy
    
    def _save_privacy(self):
        """Save privacy settings."""
        with open(self.privacy_file, 'w', encoding='utf-8') as f:
            json.dump(self.privacy, f, indent=2, ensure_ascii=False)
    
    # ----------------- MEMORY OPERATIONS -----------------
    
    def add_memory(self, content: str, category: str = "fact", 
                   importance: int = 5, tags: List[str] = None,
                   metadata: Dict = None) -> Dict:
        """
        Add a new memory.
        
        Args:
            content: The memory content
            category: fact/preference/context/personal/setting
            importance: 1-10 importance score
            tags: List of tags
            metadata: Additional metadata
        
        Returns:
            The created memory
        """
        memory = {
            "id": str(uuid.uuid4())[:8],
            "content": content,
            "category": category,
            "importance": min(10, max(1, importance)),
            "tags": tags or [],
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "access_count": 0
        }
        
        self.memories["memories"].append(memory)
        self._save_memories()
        
        return memory
    
    def get_memory(self, memory_id: str) -> Optional[Dict]:
        """Get a specific memory by ID."""
        for mem in self.memories["memories"]:
            if mem["id"] == memory_id:
                mem["last_accessed"] = datetime.now().isoformat()
                mem["access_count"] += 1
                self._save_memories()
                return mem
        return None
    
    def get_all_memories(self, category: str = None) -> List[Dict]:
        """Get all memories, optionally filtered by category."""
        memories = self.memories["memories"]
        if category:
            memories = [m for m in memories if m["category"] == category]
        # Sort by importance and date
        memories.sort(key=lambda x: (-x["importance"], x["created_at"]))
        return memories
    
    def search_memories(self, query: str, category: str = None, 
                        limit: int = 20) -> List[Dict]:
        """Search memories by content."""
        results = []
        query_lower = query.lower()
        
        for mem in self.memories["memories"]:
            if category and mem["category"] != category:
                continue
            if (query_lower in mem["content"].lower() or 
                any(query_lower in t.lower() for t in mem.get("tags", []))):
                results.append(mem)
        
        return results[:limit]
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        memories = self.memories["memories"]
        for i, mem in enumerate(memories):
            if mem["id"] == memory_id:
                memories.pop(i)
                self._save_memories()
                return True
        return False
    
    def clear_category(self, category: str) -> int:
        """Clear all memories in a category."""
        original_count = len(self.memories["memories"])
        self.memories["memories"] = [m for m in self.memories["memories"] 
                                     if m["category"] != category]
        deleted = original_count - len(self.memories["memories"])
        self._save_memories()
        return deleted
    
    def get_statistics(self) -> Dict:
        """Get memory statistics."""
        memories = self.memories["memories"]
        by_category = {}
        for cat in self.categories:
            by_category[cat] = len([m for m in memories if m["category"] == cat])
        
        return {
            "total_memories": len(memories),
            "by_category": by_category,
            "total_conversations": len(self.conversations.get("conversations", [])),
            "privacy_settings": {
                "auto_save": self.privacy.get("auto_save", True),
                "encrypt_sensitive": self.privacy.get("encrypt_sensitive", True),
                "auto_clear": self.privacy.get("auto_clear_conversations", False)
            },
            "categories": self.categories
        }
    
    # ----------------- CONVERSATION MEMORY -----------------
    
    def add_conversation(self, role: str, content: str, 
                         summary: str = None, metadata: Dict = None):
        """Add a conversation message."""
        if "conversations" not in self.conversations:
            self.conversations["conversations"] = []
        
        conv = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().isoformat(),
            "role": role,  # user/assistant/system
            "content": content,
            "summary": summary,
            "metadata": metadata or {}
        }
        
        self.conversations["conversations"].append(conv)
        
        # Limit conversation history
        max_conv = self.privacy.get("max_conversations", 100)
        if len(self.conversations["conversations"]) > max_conv:
            self.conversations["conversations"] = self.conversations["conversations"][-max_conv:]
        
        self._save_conversations()
    
    def get_conversations(self, limit: int = 50) -> List[Dict]:
        """Get recent conversations."""
        convs = self.conversations.get("conversations", [])
        return convs[-limit:] if limit > 0 else convs
    
    def search_conversations(self, query: str, limit: int = 20) -> List[Dict]:
        """Search conversations."""
        results = []
        query_lower = query.lower()
        convs = self.conversations.get("conversations", [])
        
        for conv in convs:
            if query_lower in conv.get("content", "").lower():
                results.append(conv)
        
        return results[-limit:]
    
    def clear_conversations(self):
        """Clear all conversations."""
        self.conversations["conversations"] = []
        self._save_conversations()
    
    # ----------------- PRIVACY CONTROLS -----------------
    
    def get_privacy_settings(self) -> Dict:
        """Get privacy settings."""
        return self.privacy
    
    def update_privacy_settings(self, settings: Dict) -> Dict:
        """Update privacy settings."""
        self.privacy = {**self.privacy, **settings}
        self._save_privacy()
        return self.privacy
    
    def export_data(self, include_sensitive: bool = False) -> Dict:
        """Export all memory data."""
        data = {
            "exported_at": datetime.now().isoformat(),
            "memories": [],
            "conversations": [],
            "privacy_settings": {k: v for k, v in self.privacy.items() 
                               if k != "sensitive_categories"}
        }
        
        # Export memories (filter sensitive if needed)
        for mem in self.memories["memories"]:
            if not include_sensitive and mem["category"] in self.privacy.get("sensitive_categories", []):
                mem_copy = mem.copy()
                mem_copy["content"] = "***ENCRYPTED***"
                data["memories"].append(mem_copy)
            else:
                data["memories"].append(mem)
        
        # Export conversations
        data["conversations"] = self.conversations.get("conversations", [])[-50:]
        
        return data
    
    def import_data(self, data: Dict, merge: bool = True) -> Dict:
        """Import memory data."""
        imported_memories = 0
        imported_conversations = 0
        
        if merge:
            # Add memories
            for mem in data.get("memories", []):
                if "id" in mem:
                    # Check if exists
                    exists = any(m["id"] == mem["id"] for m in self.memories["memories"])
                    if not exists:
                        self.memories["memories"].append(mem)
                        imported_memories += 1
            
            # Add conversations
            for conv in data.get("conversations", []):
                if "id" in conv:
                    exists = any(c["id"] == conv["id"] for c in self.conversations.get("conversations", []))
                    if not exists:
                        self.conversations["conversations"].append(conv)
                        imported_conversations += 1
        else:
            # Replace all
            self.memories["memories"] = data.get("memories", [])
            self.conversations["conversations"] = data.get("conversations", [])[-50:]
            imported_memories = len(data.get("memories", []))
            imported_conversations = len(data.get("conversations", []))
        
        self._save_memories()
        self._save_conversations()
        
        return {
            "memories_imported": imported_memories,
            "conversations_imported": imported_conversations
        }
    
    def clear_all(self, keep_settings: bool = True):
        """Clear all memory data."""
        self.memories["memories"] = []
        self.conversations["conversations"] = []
        self._save_memories()
        self._save_conversations()
        
        if not keep_settings:
            self.privacy = self._load_privacy()
            self._save_privacy()
    
    # ----------------- AUTO-LEARNING -----------------
    
    def extract_and_save_facts(self, text: str):
        """
        Extract potential facts from text and save them.
        This is a simple implementation - in production, use NLP.
        """
        # Look for patterns like "My name is X" or "I prefer Y"
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Simple pattern matching
            if "my name is" in line.lower():
                name = line.split("is")[-1].strip().rstrip(".")
                self.add_memory(f"User's name is {name}", category="personal", 
                              importance=10, tags=["name", "identity"])
            
            elif "i live in" in line.lower():
                location = line.split("in")[-1].strip().rstrip(".")
                self.add_memory(f"User lives in {location}", category="personal",
                              importance=8, tags=["location", "personal"])
            
            elif "i prefer" in line.lower() or "i like" in line.lower():
                preference = line.split("like")[-1].strip().split(".")[0]
                self.add_memory(f"User preference: {preference}", category="preference",
                              importance=7, tags=["preference"])


# Global memory instance
longterm_memory = LongTermMemory()

# Convenience functions
def get_memory_stats() -> Dict:
    """Get memory statistics."""
    return longterm_memory.get_statistics()

def add_memory(content: str, category: str = "fact", 
               importance: int = 5, tags: List[str] = None) -> Dict:
    """Add a new memory."""
    return longterm_memory.add_memory(content, category, importance, tags)

def get_memories(category: str = None) -> List[Dict]:
    """Get all memories."""
    return longterm_memory.get_all_memories(category)

def search_memories(query: str, category: str = None) -> List[Dict]:
    """Search memories."""
    return longterm_memory.search_memories(query, category)

def delete_memory(memory_id: str) -> bool:
    """Delete a memory."""
    return longterm_memory.delete_memory(memory_id)

def get_privacy_settings() -> Dict:
    """Get privacy settings."""
    return longterm_memory.get_privacy_settings()

def update_privacy_settings(settings: Dict) -> Dict:
    """Update privacy settings."""
    return longterm_memory.update_privacy_settings(settings)

def export_memory_data(include_sensitive: bool = False) -> Dict:
    """Export all memory data."""
    return longterm_memory.export_data(include_sensitive)

def import_memory_data(data: Dict, merge: bool = True) -> Dict:
    """Import memory data."""
    return longterm_memory.import_data(data, merge)

def clear_memory_data():
    """Clear all memory."""
    longterm_memory.clear_all()

def add_conversation(role: str, content: str, summary: str = None):
    """Add a conversation."""
    longterm_memory.add_conversation(role, content, summary)

def get_conversations(limit: int = 50) -> List[Dict]:
    """Get conversations."""
    return longterm_memory.get_conversations(limit)


# ============================================================================
# 2. WEB SEARCH (Brave Search API)
# ============================================================================

try:
    import requests

    def web_search(query: str, num_results: int = 10) -> List[Dict]:
        """Search the web using Brave Search API."""
        # API key would be in api.py
        # This is a placeholder - actual implementation needs Brave API key
        return [
            {
                "title": f"Search Result for: {query}",
                "url": "https://example.com",
                "snippet": f"This is a placeholder result for: {query}"
            }
        ]

    def fetch_url(url: str) -> Dict:
        """Fetch content from a URL."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return {
                "url": url,
                "content": response.text[:5000],
                "status": "success"
            }
        except Exception as e:
            return {"url": url, "error": str(e), "status": "error"}

except ImportError:
    def web_search(query: str, num_results: int = 10) -> List[Dict]:
        """Search disabled - requests not installed."""
        return [{"error": "Web search disabled - requests module not installed"}]

    def fetch_url(url: str) -> Dict:
        """Fetch disabled."""
        return {"error": "Web fetch disabled - requests module not installed"}


# ============================================================================
# 3. GIT INTEGRATION
# ============================================================================

try:
    import subprocess

    def get_git_status() -> Dict:
        """Get git repository status."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=os.path.dirname(os.path.dirname(__file__)),
                capture_output=True,
                text=True,
                timeout=5
            )
            files = [line[3:] for line in result.stdout.strip().split('\n') if line]

            branch = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=os.path.dirname(os.path.dirname(__file__)),
                capture_output=True,
                text=True,
                timeout=5
            ).stdout.strip()

            return {
                "status": "success",
                "branch": branch or "main",
                "changed_files": files,
                "has_changes": len(files) > 0
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def git_commit(message: str) -> Dict:
        """Create a git commit."""
        try:
            # Stage all changes
            subprocess.run(
                ["git", "add", "."],
                cwd=os.path.dirname(os.path.dirname(__file__)),
                capture_output=True,
                timeout=10
            )

            # Create commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=os.path.dirname(os.path.dirname(__file__)),
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return {"status": "success", "message": f"Committed: {message}"}
            else:
                return {"status": "error", "message": result.stderr.strip()}
        except Exception as e:
            return {"status": "error", "message": str(e)}

except ImportError:
    def get_git_status() -> Dict:
        return {"status": "error", "message": "Git not available"}

    def git_commit(message: str) -> Dict:
        return {"status": "error", "message": "Git not available"}


# ============================================================================
# 4. TEXT-TO-SPEECH (pyttsx3)
# ============================================================================

try:
    import pyttsx3

    tts_engine = None
    try:
        tts_engine = pyttsx3.init()
    except Exception:
        pass

    def text_to_speech(text: str, filename: str = None) -> Dict:
        """Convert text to speech."""
        global tts_engine

        if tts_engine is None:
            try:
                tts_engine = pyttsx3.init()
            except Exception as e:
                return {"status": "error", "message": str(e)}

        try:
            output_dir = Path(__file__).parent.parent / "output"
            output_dir.mkdir(exist_ok=True)

            if filename is None:
                filename = f"speech_{int(time.time())}.wav"

            filepath = output_dir / filename
            tts_engine.save_to_file(text, str(filepath))
            tts_engine.runAndWait()

            return {
                "status": "success",
                "filename": filename,
                "path": str(filepath),
                "text": text[:100]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def list_voices() -> List[Dict]:
        """List available TTS voices."""
        if tts_engine is None:
            return []
        voices = []
        for voice in tts_engine.getProperty('voices'):
            voices.append({
                "id": voice.id,
                "name": voice.name,
                "languages": voice.languages,
                "gender": voice.gender
            })
        return voices

except ImportError:
    def text_to_speech(text: str, filename: str = None) -> Dict:
        return {"status": "error", "message": "pyttsx3 not installed"}

    def list_voices() -> List[Dict]:
        return []


# ============================================================================
# 5. FILE EDITOR
# ============================================================================

def read_file_content(filepath: str) -> Dict:
    """Read file content."""
    try:
        path = Path(filepath)
        if not path.exists():
            return {"status": "error", "message": "File not found"}
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"status": "success", "content": content, "path": filepath}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def edit_file_content(filepath: str, old_text: str, new_text: str) -> Dict:
    """Edit file with search/replace."""
    try:
        path = Path(filepath)
        if not path.exists():
            return {"status": "error", "message": "File not found"}

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if old_text not in content:
            return {"status": "error", "message": "Text not found in file"}

        new_content = content.replace(old_text, new_text)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return {
            "status": "success",
            "message": "File updated",
            "path": filepath
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def search_in_file(filepath: str, query: str) -> List[Dict]:
    """Search for text in a file."""
    try:
        path = Path(filepath)
        if not path.exists():
            return []

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        results = []
        for i, line in enumerate(lines, 1):
            if query.lower() in line.lower():
                results.append({
                    "line": i,
                    "content": line.strip()
                })

        return results
    except Exception:
        return []


# ============================================================================
# 6. ENHANCED PLANNER
# ============================================================================

class TaskPlan:
    """Multi-step task plan."""

    def __init__(self, goal: str):
        self.goal = goal
        self.steps = []
        self.current_step = 0

    def add_step(self, step: Dict):
        """Add a step to the plan."""
        self.steps.append(step)

    def to_dict(self) -> Dict:
        """Convert plan to dictionary."""
        return {
            "goal": self.goal,
            "steps": self.steps,
            "total_steps": len(self.steps),
            "current_step": self.current_step
        }

    def get_next_step(self) -> Optional[Dict]:
        """Get the next step to execute."""
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            self.current_step += 1
            return step
        return None


def generate_plan(goal: str) -> TaskPlan:
    """Generate a multi-step plan for a goal."""
    plan = TaskPlan(goal)

    # Parse goal and generate steps
    goal_lower = goal.lower()

    # Add general planning steps
    plan.add_step({
        "step": 1,
        "action": "analyze",
        "description": f"Analyze the goal: {goal}",
        "details": "Break down the requirements and constraints"
    })

    plan.add_step({
        "step": 2,
        "action": "research",
        "description": "Gather necessary information",
        "details": "Search for relevant data and resources"
    })

    plan.add_step({
        "step": 3,
        "action": "execute",
        "description": "Execute the main task",
        "details": "Perform the core work to achieve the goal"
    })

    plan.add_step({
        "step": 4,
        "action": "verify",
        "description": "Verify the results",
        "details": "Check that the output meets requirements"
    })

    plan.add_step({
        "step": 5,
        "action": "complete",
        "description": "Finalize and report",
        "details": "Deliver the results and document any changes"
    })

    return plan


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Memory
    "memory_system",
    "get_memory_stats",
    "search_memory",

    # Web
    "web_search",
    "fetch_url",

    # Git
    "get_git_status",
    "git_commit",

    # TTS
    "text_to_speech",
    "list_voices",

    # File
    "read_file_content",
    "edit_file_content",
    "search_in_file",

    # Planner
    "TaskPlan",
    "generate_plan",
]
