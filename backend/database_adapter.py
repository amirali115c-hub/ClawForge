"""
Leo 2.0 - Database Adapter
=========================
Unified database interface supporting SQLite and PostgreSQL.
Currently using SQLite, can switch to PostgreSQL later.
"""

import sqlite3
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class DatabaseAdapter:
    """Unified database adapter for Leo 2.0."""
    
    def __init__(self, db_path: str = None, db_type: str = "sqlite"):
        self.db_type = db_type
        if db_path is None:
            # Default to SQLite in ClawForge folder
            base_dir = Path(__file__).parent.parent
            db_path = base_dir / "data" / "leo2.db"
        
        self.db_path = str(db_path)
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize tables
        self._init_tables()
    
    def _init_tables(self):
        """Initialize database tables."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        """)
        
        # Memory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                key TEXT NOT NULL,
                value TEXT,
                category TEXT,
                importance INTEGER DEFAULT 5,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                key TEXT NOT NULL,
                value TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _get_connection(self):
        """Get database connection."""
        if self.db_type == "sqlite":
            return sqlite3.connect(self.db_path)
        # PostgreSQL connection string can be added later
        # return psycopg2.connect(connection_string)
    
    # ========== USER METHODS ==========
    
    def create_user(self, username: str, email: str = None, metadata: Dict = None) -> int:
        """Create a new user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO users (username, email, metadata) VALUES (?, ?, ?)",
            (username, email, json.dumps(metadata) if metadata else None)
        )
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    
    def get_user(self, user_id: int = None, username: str = None) -> Optional[Dict]:
        """Get user by ID or username."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        elif username:
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        else:
            return None
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "created_at": row[3],
                "last_active": row[4],
                "metadata": json.loads(row[5]) if row[5] else {}
            }
        return None
    
    def update_user_activity(self, user_id: int):
        """Update user's last active timestamp."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_active = ? WHERE id = ?",
            (datetime.now().isoformat(), user_id)
        )
        conn.commit()
        conn.close()
    
    # ========== CONVERSATION METHODS ==========
    
    def create_conversation(self, user_id: int, title: str = "New Chat") -> int:
        """Create a new conversation."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO conversations (user_id, title, updated_at) VALUES (?, ?, ?)",
            (user_id, title, datetime.now().isoformat())
        )
        
        conv_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return conv_id
    
    def get_conversation(self, conversation_id: int) -> Optional[Dict]:
        """Get conversation by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "user_id": row[1],
                "title": row[2],
                "summary": row[3],
                "created_at": row[4],
                "updated_at": row[5]
            }
        return None
    
    def get_user_conversations(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get all conversations for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
            (user_id, limit)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "user_id": row[1],
                "title": row[2],
                "summary": row[3],
                "created_at": row[4],
                "updated_at": row[5]
            }
            for row in rows
        ]
    
    def update_conversation_summary(self, conversation_id: int, summary: str):
        """Update conversation summary."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE conversations SET summary = ?, updated_at = ? WHERE id = ?",
            (summary, datetime.now().isoformat(), conversation_id)
        )
        conn.commit()
        conn.close()
    
    # ========== MESSAGE METHODS ==========
    
    def add_message(self, conversation_id: int, role: str, content: str, metadata: Dict = None) -> int:
        """Add a message to conversation."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO messages (conversation_id, role, content, metadata) VALUES (?, ?, ?, ?)",
            (conversation_id, role, content, json.dumps(metadata) if metadata else None)
        )
        
        msg_id = cursor.lastrowid
        
        # Update conversation timestamp
        cursor.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), conversation_id)
        )
        
        conn.commit()
        conn.close()
        return msg_id
    
    def get_conversation_messages(self, conversation_id: int, limit: int = 100) -> List[Dict]:
        """Get messages from conversation."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC LIMIT ?",
            (conversation_id, limit)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "conversation_id": row[1],
                "role": row[2],
                "content": row[3],
                "timestamp": row[4],
                "metadata": json.loads(row[5]) if row[5] else {}
            }
            for row in rows
        ]
    
    # ========== MEMORY METHODS ==========
    
    def save_memory(self, user_id: int, key: str, value: Any, category: str = "general", importance: int = 5, tags: List[str] = None) -> int:
        """Save a memory."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO memories (user_id, key, value, category, importance, tags) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, key, json.dumps(value), category, importance, json.dumps(tags) if tags else None)
        )
        
        memory_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return memory_id
    
    def get_memory(self, user_id: int, key: str) -> Optional[Any]:
        """Get a memory by key."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT value FROM memories WHERE user_id = ? AND key = ?",
            (user_id, key)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            return json.loads(row[0])
        return None
    
    def search_memories(self, user_id: int, query: str, category: str = None, limit: int = 10) -> List[Dict]:
        """Search memories."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute(
                "SELECT * FROM memories WHERE user_id = ? AND category = ? AND (key LIKE ? OR value LIKE ?) ORDER BY importance DESC LIMIT ?",
                (user_id, category, f"%{query}%", f"%{query}%", limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM memories WHERE user_id = ? AND (key LIKE ? OR value LIKE ?) ORDER BY importance DESC LIMIT ?",
                (user_id, f"%{query}%", f"%{query}%", limit)
            )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "user_id": row[1],
                "key": row[2],
                "value": json.loads(row[3]) if row[3] else None,
                "category": row[4],
                "importance": row[5],
                "tags": json.loads(row[6]) if row[6] else [],
                "created_at": row[7]
            }
            for row in rows
        ]
    
    # ========== SETTINGS METHODS ==========
    
    def set_setting(self, user_id: int, key: str, value: Any):
        """Set a user setting."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Upsert
        cursor.execute(
            "INSERT OR REPLACE INTO settings (user_id, key, value) VALUES (?, ?, ?)",
            (user_id, key, json.dumps(value))
        )
        
        conn.commit()
        conn.close()
    
    def get_setting(self, user_id: int, key: str, default: Any = None) -> Any:
        """Get a user setting."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT value FROM settings WHERE user_id = ? AND key = ?",
            (user_id, key)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            return json.loads(row[0])
        return default
    
    # ========== STATISTICS ==========
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['users'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        stats['conversations'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        stats['messages'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM memories")
        stats['memories'] = cursor.fetchone()[0]
        
        conn.close()
        
        return stats


# Singleton instance
_db_adapter = None

def get_db_adapter() -> DatabaseAdapter:
    global _db_adapter
    if _db_adapter is None:
        _db_adapter = DatabaseAdapter()
    return _db_adapter
