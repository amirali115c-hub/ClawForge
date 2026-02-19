"""
ClawForge Context Manager
=========================
Privacy-first conversation continuity system.
- Auto-loads context at session start
- Updates after each interaction
- Privacy protection layers for sensitive data
- Encryption option for PII
"""

import json
import os
import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import threading

# Configuration
MEMORY_DIR = Path(__file__).parent
CONVERSATION_STATE_FILE = MEMORY_DIR / "conversation_state.json"
DAILY_LOGS_DIR = MEMORY_DIR / "daily_logs"
ENCRYPTION_KEY_FILE = MEMORY_DIR / ".key"
RETENTION_DAYS = 30  # Auto-cleanup after 30 days


class PrivacyLevel:
    """Privacy levels for different data sensitivity"""
    PUBLIC = "public"           # No restrictions
    STANDARD = "standard"       # Basic protection
    CONFIDENTIAL = "confidential"  # Encrypted, access logged
    RESTRICTED = "restricted"   # Requires explicit consent


class DataClassifier:
    """Classifies data sensitivity and applies privacy rules"""
    
    # Patterns that indicate sensitive data
    SENSITIVE_PATTERNS = {
        "password": {"level": PrivacyLevel.RESTRICTED, "action": "reject"},
        "api_key": {"level": PrivacyLevel.RESTRICTED, "action": "reject"},
        "token": {"level": PrivacyLevel.RESTRICTED, "action": "reject"},
        "ssn": {"level": PrivacyLevel.RESTRICTED, "action": "reject"},
        "credit_card": {"level": PrivacyLevel.RESTRICTED, "action": "reject"},
        "email": {"level": PrivacyLevel.CONFIDENTIAL, "action": "encrypt"},
        "phone": {"level": PrivacyLevel.CONFIDENTIAL, "action": "encrypt"},
        "address": {"level": PrivacyLevel.CONFIDENTIAL, "action": "encrypt"},
        "name": {"level": PrivacyLevel.STANDARD, "action": "store"},
    }
    
    @classmethod
    def classify(cls, key: str, value: Any) -> Dict[str, Any]:
        """Classify data sensitivity"""
        key_lower = key.lower()
        
        for pattern, rules in cls.SENSITIVE_PATTERNS.items():
            if pattern in key_lower:
                return {
                    "level": rules["level"],
                    "action": rules["action"],
                    "pattern": pattern
                }
        
        return {"level": PrivacyLevel.PUBLIC, "action": "store", "pattern": None}
    
    @classmethod
    def should_store(cls, key: str, value: Any) -> bool:
        """Determine if data should be stored"""
        classification = cls.classify(key, value)
        return classification["action"] != "reject"


class SimpleEncryption:
    """Lightweight encryption for sensitive data"""
    
    def __init__(self):
        self._key = self._load_or_generate_key()
    
    def _load_or_generate_key(self) -> bytes:
        """Load existing key or generate new one"""
        if ENCRYPTION_KEY_FILE.exists():
            with open(ENCRYPTION_KEY_FILE, 'rb') as f:
                return f.read()
        
        # Generate new key
        key = os.urandom(32)
        with open(ENCRYPTION_KEY_FILE, 'wb') as f:
            f.write(key)
        return key
    
    def _hash_for_storage(self, data: str) -> str:
        """Create hash for comparison without storing raw data"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def encrypt(self, data: str) -> str:
        """Simple XOR-based encryption (for non-critical data)"""
        key_bytes = self._key
        data_bytes = data.encode()
        encrypted = bytes(a ^ b for a, b in zip(data_bytes, (key_bytes * (len(data_bytes) // len(key_bytes) + 1))[:len(data_bytes)]))
        return encrypted.hex()
    
    def decrypt(self, encrypted: str) -> str:
        """Decrypt data"""
        key_bytes = self._key
        encrypted_bytes = bytes.fromhex(encrypted)
        decrypted = bytes(a ^ b for a, b in zip(encrypted_bytes, (key_bytes * (len(encrypted_bytes) // len(key_bytes) + 1))[:len(encrypted_bytes)]))
        return decrypted.decode()


class ContextManager:
    """
    Manages conversation continuity with privacy protection.
    
    Features:
    - Auto-save/restore conversation state
    - Sensitive data classification
    - Optional encryption for PII
    - Daily activity logging
    - Auto-cleanup old data
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.encryption = SimpleEncryption()
        self.state = self._load_state()
        self._daily_log = []
        
        # Ensure daily logs directory exists
        DAILY_LOGS_DIR.mkdir(exist_ok=True)
        
        # Auto-cleanup old files
        self._cleanup_old_logs()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load conversation state from file"""
        if CONVERSATION_STATE_FILE.exists():
            try:
                with open(CONVERSATION_STATE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return self._get_default_state()
    
    def _get_default_state(self) -> Dict[str, Any]:
        """Get default conversation state"""
        return {
            "conversation_id": None,
            "started_at": None,
            "last_updated": None,
            "current_task": None,
            "task_status": None,
            "where_we_left_off": None,
            "next_steps": [],
            "session_history": [],
            "user_context": {
                "name": None,
                "preferences": {},
                "sensitive_data_accessed": False
            },
            "privacy_level": PrivacyLevel.STANDARD,
            "data_retention": "session_only"
        }
    
    def _save_state(self):
        """Save conversation state to file"""
        # Don't save if conversation_id is None (no active session)
        if not self.state.get("conversation_id"):
            return
        
        self.state["last_updated"] = datetime.now().isoformat()
        
        try:
            with open(CONVERSATION_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Could not save state: {e}")
    
    def _classify_and_sanitize(self, key: str, value: Any) -> Any:
        """Classify data and sanitize if needed"""
        classification = DataClassifier.classify(key, value)
        
        if classification["action"] == "reject":
            return None  # Don't store sensitive data
        
        if classification["action"] == "encrypt" and classification["level"] == PrivacyLevel.CONFIDENTIAL:
            # Mark that sensitive data was accessed
            self.state["user_context"]["sensitive_data_accessed"] = True
            # Store encrypted (simplified - just mark as encrypted)
            return {"_encrypted": True, "data": self.encryption.encrypt(str(value))}
        
        return value
    
    # ==================== PUBLIC API ====================
    
    def start_session(self, user_context: Optional[Dict] = None) -> str:
        """
        Start a new conversation session.
        Returns conversation ID.
        """
        conversation_id = str(uuid.uuid4())[:8]
        
        self.state = self._get_default_state()
        self.state["conversation_id"] = conversation_id
        self.state["started_at"] = datetime.now().isoformat()
        
        # Sanitize user context before storing
        if user_context:
            sanitized = {}
            for key, value in user_context.items():
                if DataClassifier.should_store(key, value):
                    sanitized[key] = self._classify_and_sanitize(key, value)
            self.state["user_context"].update(sanitized)
        
        self._save_state()
        
        # Log session start
        self._log_activity("session_start", {"conversation_id": conversation_id})
        
        return conversation_id
    
    def update_context(
        self,
        current_task: Optional[str] = None,
        where_left_off: Optional[str] = None,
        next_steps: Optional[List[str]] = None,
        task_status: Optional[str] = None
    ):
        """
        Update conversation context.
        
        Args:
            current_task: What agent is currently working on
            where_left_off: Where conversation/stopped
            next_steps: List of upcoming tasks
            task_status: Current status (planning, executing, waiting, completed)
        """
        if current_task:
            self.state["current_task"] = self._classify_and_sanitize("current_task", current_task)
        
        if where_left_off:
            self.state["where_we_left_off"] = self._classify_and_sanitize("where_left_off", where_left_off)
        
        if next_steps:
            sanitized_steps = []
            for step in next_steps:
                if DataClassifier.should_store("next_step", step):
                    sanitized_steps.append(step)
            self.state["next_steps"] = sanitized_steps
        
        if task_status:
            self.state["task_status"] = task_status
        
        self._save_state()
    
    def add_to_history(self, entry: Dict[str, Any]):
        """Add entry to session history"""
        # Sanitize entry
        sanitized_entry = {}
        for key, value in entry.items():
            if DataClassifier.should_store(key, value):
                sanitized_entry[key] = self._classify_and_sanitize(key, value)
        
        if sanitized_entry:
            sanitized_entry["timestamp"] = datetime.now().isoformat()
            self.state["session_history"].append(sanitized_entry)
            
            # Keep only last 50 entries
            if len(self.state["session_history"]) > 50:
                self.state["session_history"] = self.state["session_history"][-50:]
            
            self._save_state()
    
    def get_context(self) -> Dict[str, Any]:
        """Get current conversation context (decrypted)"""
        context = self.state.copy()
        
        # Decrypt sensitive fields
        user_ctx = context.get("user_context", {})
        for key, value in user_ctx.items():
            if isinstance(value, dict) and value.get("_encrypted"):
                try:
                    user_ctx[key] = self.encryption.decrypt(value["data"])
                except:
                    user_ctx[key] = "[encrypted]"
        
        return context
    
    def get_resume_context(self) -> str:
        """Get formatted context for resuming conversation"""
        state = self.get_context()
        
        lines = []
        
        if state.get("current_task"):
            lines.append(f"[TASK] {state['current_task']}")
        
        if state.get("task_status"):
            status_emoji = {
                "planning": "[PLANNING]",
                "executing": "[EXECUTING]",
                "waiting": "[WAITING]",
                "completed": "[COMPLETED]"
            }
            emoji = status_emoji.get(state["task_status"], "[STATUS]")
            lines.append(f"{emoji} Status: {state['task_status']}")
        
        if state.get("where_we_left_off"):
            lines.append(f"[PAUSED] {state['where_we_left_off']}")
        
        if state.get("next_steps"):
            lines.append("[NEXT] Next steps:")
            for step in state["next_steps"][:3]:  # Show max 3
                lines.append(f"   - {step}")
        
        return "\n".join(lines) if lines else "No previous context found."
    
    def end_session(self, summary: Optional[str] = None):
        """End current session"""
        if summary:
            self._log_activity("session_end", {
                "conversation_id": self.state.get("conversation_id"),
                "summary": summary
            })
        
        # Reset state but keep conversation_id for reference
        last_id = self.state.get("conversation_id")
        self.state = self._get_default_state()
        self.state["conversation_id"] = last_id  # Keep for reference
        self._save_state()
    
    def _log_activity(self, activity_type: str, data: Dict):
        """Log daily activity"""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = DAILY_LOGS_DIR / f"{today}.jsonl"
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": activity_type,
            "data": data
        }
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except IOError:
            pass
    
    def _cleanup_old_logs(self):
        """Remove logs older than RETENTION_DAYS"""
        if not DAILY_LOGS_DIR.exists():
            return
        
        cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
        
        for log_file in DAILY_LOGS_DIR.glob("*.jsonl"):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff:
                    log_file.unlink()
            except (OSError, ValueError):
                pass
    
    def get_privacy_status(self) -> Dict[str, Any]:
        """Get current privacy status"""
        return {
            "privacy_level": self.state.get("privacy_level", PrivacyLevel.STANDARD),
            "sensitive_data_accessed": self.state.get("user_context", {}).get("sensitive_data_accessed", False),
            "retention": self.state.get("data_retention", "session_only"),
            "conversation_active": self.state.get("conversation_id") is not None
        }
    
    def set_privacy_level(self, level: str):
        """Set privacy level"""
        if level in [PrivacyLevel.PUBLIC, PrivacyLevel.STANDARD, PrivacyLevel.CONFIDENTIAL, PrivacyLevel.RESTRICTED]:
            self.state["privacy_level"] = level
            self._save_state()
    
    def clear_sensitive_data(self):
        """Clear all sensitive data from memory"""
        self.state["user_context"] = {
            "name": None,
            "preferences": {},
            "sensitive_data_accessed": False
        }
        self._save_state()


# Singleton instance
_context_manager = None

def get_context_manager() -> ContextManager:
    """Get singleton context manager instance"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


# Convenience functions
def start_session(user_context: Optional[Dict] = None) -> str:
    """Start a new session"""
    return get_context_manager().start_session(user_context)

def update_context(**kwargs):
    """Update conversation context"""
    get_context_manager().update_context(**kwargs)

def add_to_history(entry: Dict[str, Any]):
    """Add to session history"""
    get_context_manager().add_to_history(entry)

def get_resume_context() -> str:
    """Get context for resuming"""
    return get_context_manager().get_resume_context()

def end_session(summary: Optional[str] = None):
    """End current session"""
    get_context_manager().end_session(summary)

def get_privacy_status() -> Dict[str, Any]:
    """Get privacy status"""
    return get_context_manager().get_privacy_status()
