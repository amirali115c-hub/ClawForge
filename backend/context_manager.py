"""
Leo 2.0 Context Manager
Based on OpenClaw's context mechanism - Manages session, memory, and long-term context.
"""

import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict
import re


@dataclass
class ContextEntry:
    """A single context entry."""
    key: str
    value: Any
    source: str  # session, memory, config, user
    category: str  # fact, preference, history, instruction
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    relevance_score: float = 1.0
    expires_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)


class ContextManager:
    """
    Manages all context for Leo 2.0.
    Mirrors OpenClaw's context management mechanism.
    """
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path(".")
        self.context_dir = self.workspace_dir / "context"
        self.context_dir.mkdir(exist_ok=True)
        
        # In-memory context
        self._session_context: Dict[str, Any] = {}
        self._context_cache: OrderedDict = OrderedDict()
        self._max_cache_size = 100
        
        # Context files
        self._session_file = self.context_dir / "session.json"
        self._longterm_file = self.context_dir / "longterm.json"
        self._preferences_file = self.context_dir / "preferences.json"
        
        # Load existing context
        self._load_all_context()
    
    def _load_all_context(self):
        """Load all context from files."""
        # Session context
        if self._session_file.exists():
            try:
                with open(self._session_file, 'r') as f:
                    self._session_context = json.load(f)
            except:
                self._session_context = {}
        
        # Long-term memory
        self._longterm_memory = self._load_context_file(self._longterm_file)
        
        # User preferences
        self._user_preferences = self._load_context_file(self._preferences_file)
    
    def _load_context_file(self, filepath: Path) -> Dict:
        """Load a context file."""
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_context_file(self, filepath: Path, data: Dict):
        """Save a context file."""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    # =========================================================================
    # SESSION CONTEXT
    # =========================================================================
    
    def set_session(self, key: str, value: Any, category: str = "session"):
        """Set a session context value."""
        self._session_context[key] = {
            'value': value,
            'category': category,
            'updated_at': datetime.now().isoformat(),
        }
        self._save_context_file(self._session_file, self._session_context)
    
    def get_session(self, key: str, default: Any = None) -> Any:
        """Get a session context value."""
        entry = self._session_context.get(key)
        if entry:
            return entry['value']
        return default
    
    def delete_session(self, key: str):
        """Delete a session context value."""
        if key in self._session_context:
            del self._session_context[key]
            self._save_context_file(self._session_file, self._session_context)
    
    def clear_session(self):
        """Clear all session context."""
        self._session_context = {}
        self._save_context_file(self._session_file, {})
    
    # =========================================================================
    # LONG-TERM MEMORY
    # =========================================================================
    
    def add_memory(self, key: str, value: Any, category: str = "fact", 
                   importance: int = 5, tags: List[str] = None):
        """Add a long-term memory."""
        memory = {
            'value': value,
            'category': category,
            'importance': importance,
            'tags': tags or [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'access_count': 0,
        }
        
        # Generate unique key if needed
        if key in self._longterm_memory:
            key = f"{key}_{datetime.now().strftime('%H%M%S')}"
        
        self._longterm_memory[key] = memory
        self._save_context_file(self._longterm_file, self._longterm_memory)
        
        return key
    
    def get_memory(self, key: str) -> Optional[Dict]:
        """Get a long-term memory."""
        if key in self._longterm_memory:
            memory = self._longterm_memory[key]
            memory['access_count'] += 1
            memory['last_accessed'] = datetime.now().isoformat()
            return memory
        return None
    
    def search_memories(self, query: str, category: str = None, 
                        limit: int = 10) -> List[Tuple[str, Dict]]:
        """Search long-term memories."""
        results = []
        query_lower = query.lower()
        
        for key, memory in self._longterm_memory.items():
            # Filter by category
            if category and memory.get('category') != category:
                continue
            
            # Search in value and tags
            value_str = str(memory.get('value', '')).lower()
            tags = ' '.join(memory.get('tags', [])).lower()
            
            if query_lower in value_str or query_lower in tags:
                # Calculate relevance score
                score = 1.0
                if query_lower in value_str:
                    score += value_str.count(query_lower) * 0.5
                if query_lower in tags:
                    score += 1.0
                score *= memory.get('importance', 5) / 5.0
                
                results.append((key, memory))
        
        # Sort by relevance and importance
        results.sort(key=lambda x: (x[1].get('importance', 0), len(x[0])), reverse=True)
        
        return results[:limit]
    
    def delete_memory(self, key: str) -> bool:
        """Delete a long-term memory."""
        if key in self._longterm_memory:
            del self._longterm_memory[key]
            self._save_context_file(self._longterm_file, self._longterm_memory)
            return True
        return False
    
    # =========================================================================
    # USER PREFERENCES
    # =========================================================================
    
    def set_preference(self, key: str, value: Any):
        """Set a user preference."""
        self._user_preferences[key] = {
            'value': value,
            'updated_at': datetime.now().isoformat(),
        }
        self._save_context_file(self._preferences_file, self._user_preferences)
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        entry = self._user_preferences.get(key)
        if entry:
            return entry['value']
        return default
    
    # =========================================================================
    # CONTEXT LOADING FOR PROMPTS
    # =========================================================================
    
    def get_prompt_context(self, required_types: List[str] = None) -> Dict[str, Any]:
        """
        Get all context needed for prompt building.
        Mirrors OpenClaw's context loading mechanism.
        """
        context = {
            'session': self._session_context,
            'preferences': self._user_preferences,
            'memories': [],
        }
        
        # Load relevant memories
        for mem_type in (required_types or ['fact', 'preference', 'instruction']):
            memories = [
                (key, mem) for key, mem in self._longterm_memory.items()
                if mem.get('category') == mem_type
            ]
            context['memories'].extend(memories)
        
        return context
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation history."""
        conversations = []
        
        # Get from session
        history = self.get_session('conversation_history', [])
        
        for entry in history[-limit:]:
            conversations.append(entry)
        
        return conversations
    
    def add_conversation_turn(self, role: str, content: str):
        """Add a conversation turn to history."""
        history = self.get_session('conversation_history', [])
        
        turn = {
            'role': role,  # user, assistant, system
            'content': content,
            'timestamp': datetime.now().isoformat(),
        }
        
        history.append(turn)
        
        # Keep only last 50 turns
        if len(history) > 50:
            history = history[-50:]
        
        self.set_session('conversation_history', history)
    
    def get_system_context(self) -> Dict[str, Any]:
        """Get system-level context."""
        return {
            'workspace': str(self.workspace_dir),
            'session_start': self.get_session('start_time'),
            'total_requests': self.get_session('request_count', 0),
            'user_preferences': self._user_preferences,
        }
    
    # =========================================================================
    # CONTEXT CACHING
    # =========================================================================
    
    def get_cached_context(self, cache_key: str) -> Optional[Dict]:
        """Get cached context."""
        if cache_key in self._context_cache:
            # Move to end (LRU)
            self._context_cache.move_to_end(cache_key)
            entry = self._context_cache[cache_key]
            entry['access_count'] += 1
            return entry
        return None
    
    def cache_context(self, cache_key: str, context: Dict):
        """Cache context for reuse."""
        self._context_cache[cache_key] = {
            'data': context,
            'cached_at': datetime.now().isoformat(),
            'access_count': 0,
        }
        
        # Evict oldest if cache is full
        if len(self._context_cache) > self._max_cache_size:
            self._context_cache.popitem(last=False)
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context manager statistics."""
        return {
            'session_entries': len(self._session_context),
            'memory_entries': len(self._longterm_memory),
            'preference_entries': len(self._user_preferences),
            'cache_size': len(self._context_cache),
            'context_dir': str(self.context_dir),
        }
    
    def clear_all(self):
        """Clear all context."""
        self.clear_session()
        self._longterm_memory = {}
        self._user_preferences = {}
        self._context_cache = OrderedDict()
        
        # Clear files
        for filepath in [self._longterm_file, self._preferences_file]:
            if filepath.exists():
                filepath.unlink()
    
    def export_all(self) -> Dict[str, Any]:
        """Export all context data."""
        return {
            'session': self._session_context,
            'memory': self._longterm_memory,
            'preferences': self._user_preferences,
            'exported_at': datetime.now().isoformat(),
        }
    
    def import_all(self, data: Dict[str, Any]):
        """Import context data."""
        if 'session' in data:
            self._session_context = data['session']
            self._save_context_file(self._session_file, self._session_context)
        
        if 'memory' in data:
            self._longterm_memory = data['memory']
            self._save_context_file(self._longterm_file, self._longterm_memory)
        
        if 'preferences' in data:
            self._user_preferences = data['preferences']
            self._save_context_file(self._preferences_file, self._user_preferences)
