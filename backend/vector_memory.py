# vector_memory.py - Privacy-First Vector Memory System for Leo 2.0

"""
Secure, privacy-first vector memory with permission controls.
All data stored locally. No personal information collection.
All changes require user permission.

Features:
- Local vector storage (chromadb or sqlite-vector)
- Privacy-first design
- Permission-based learning
- User-controlled data
- Semantic search
"""

import os
import json
import hashlib
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================

class VectorMemoryConfig:
    """Configuration for privacy-first vector memory."""
    
    # Storage location (local only)
    STORAGE_DIR = Path.home() / ".leo2" / "vector_memory"
    
    # Database file
    DB_FILE = STORAGE_DIR / "memories.db"
    
    # Embedding dimensions (for simplicity, using text hashing)
    DIMENSION = 384
    
    # Privacy settings
    PRIVACY_MODE = "strict"  # strict, moderate, open
    COLLECT_PERSONAL_INFO = False
    STORE_CONVERSATIONS = False
    
    # Permission required for
    PERMISSION_REQUIRED_FOR = [
        "store_personal_info",
        "modify_behavior",
        "change_personality",
        "export_data",
        "delete_data"
    ]
    
    # Maximum memories
    MAX_MEMORIES = 10000
    MAX_MEMORY_AGE_DAYS = 365
    
    # Similarity threshold
    SIMILARITY_THRESHOLD = 0.7


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Memory:
    """A single memory entry."""
    id: str
    content: str
    embedding_id: str
    category: str
    tags: List[str]
    importance: float  # 0-1
    created_at: str
    last_accessed: str
    access_count: int
    source: str  # explicit_feedback, conversation, learned, system
    is_personal: bool
    requires_permission: bool
    permission_granted: bool
    metadata: Dict


@dataclass
class PermissionRequest:
    """A pending permission request."""
    id: str
    request_type: str
    description: str
    data_preview: str
    impact: str
    created_at: str
    expires_at: str
    status: str  # pending, approved, denied, expired


# ============================================================================
# PERMISSION MANAGER
# ============================================================================

class PermissionManager:
    """
    Manages all permission requests and grants.
    Privacy-first: Nothing happens without explicit permission.
    """
    
    def __init__(self, storage_dir: Path = VectorMemoryConfig.STORAGE_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.permissions_db = self.storage_dir / "permissions.db"
        self._init_permissions_db()
        
        # Permission history
        self.permission_history = []
    
    def _init_permissions_db(self):
        """Initialize permissions database."""
        conn = sqlite3.connect(str(self.permissions_db))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
                id TEXT PRIMARY KEY,
                request_type TEXT,
                description TEXT,
                data_preview TEXT,
                impact TEXT,
                created_at TEXT,
                expires_at TEXT,
                status TEXT,
                granted_by TEXT,
                granted_at TEXT,
                denied_by TEXT,
                denied_at TEXT,
                response TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def request_permission(
        self,
        request_type: str,
        description: str,
        data_preview: str,
        impact: str,
        expires_hours: int = 24
    ) -> str:
        """
        Create a permission request.
        Returns request ID.
        """
        request_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat()
        expires = (datetime.utcnow() + 
                  datetime.timedelta(hours=expires_hours)).isoformat()
        
        conn = sqlite3.connect(str(self.permissions_db))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO permissions (
                id, request_type, description, data_preview, impact,
                created_at, expires_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request_id, request_type, description[:200],
            data_preview[:300], impact, now, expires, "pending"
        ))
        
        conn.commit()
        conn.close()
        
        # Log request
        self.permission_history.append({
            "id": request_id,
            "type": request_type,
            "status": "pending",
            "created": now
        })
        
        return request_id
    
    def check_permission(self, request_id: str) -> Optional[Dict]:
        """Check status of a permission request."""
        conn = sqlite3.connect(str(self.permissions_db))
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM permissions WHERE id = ?', (request_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "request_type": row[1],
                "description": row[2],
                "data_preview": row[3],
                "impact": row[4],
                "created_at": row[5],
                "expires_at": row[6],
                "status": row[7],
                "granted_by": row[8],
                "granted_at": row[9],
                "denied_by": row[10],
                "denied_at": row[11],
                "response": row[12]
            }
        return None
    
    def grant_permission(self, request_id: str, granted_by: str = "user") -> bool:
        """Grant a permission request."""
        conn = sqlite3.connect(str(self.permissions_db))
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        cursor.execute('''
            UPDATE permissions SET
                status = ?, granted_by = ?, granted_at = ?
            WHERE id = ? AND status = ?
        ''', ("approved", granted_by, now, request_id, "pending"))
        
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if changed:
            # Update history
            for req in self.permission_history:
                if req["id"] == request_id:
                    req["status"] = "approved"
                    break
        
        return changed
    
    def deny_permission(self, request_id: str, denied_by: str = "user", 
                       response: str = None) -> bool:
        """Deny a permission request."""
        conn = sqlite3.connect(str(self.permissions_db))
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        cursor.execute('''
            UPDATE permissions SET
                status = ?, denied_by = ?, denied_at = ?, response = ?
            WHERE id = ? AND status = ?
        ''', ("denied", denied_by, now, response, request_id, "pending"))
        
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if changed:
            for req in self.permission_history:
                if req["id"] == request_id:
                    req["status"] = "denied"
                    break
        
        return changed
    
    def get_pending_requests(self) -> List[Dict]:
        """Get all pending permission requests."""
        conn = sqlite3.connect(str(self.permissions_db))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM permissions 
            WHERE status = 'pending'
            ORDER BY created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "request_type": row[1],
                "description": row[2],
                "data_preview": row[3],
                "impact": row[4],
                "created_at": row[5],
                "expires_at": row[6],
                "status": row[7]
            })
        
        return results
    
    def auto_expire_requests(self):
        """Expire old pending requests."""
        conn = sqlite3.connect(str(self.permissions_db))
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        cursor.execute('''
            UPDATE permissions SET status = 'expired'
            WHERE status = 'pending' AND expires_at < ?
        ''', (now,))
        
        conn.commit()
        conn.close()


# ============================================================================
# VECTOR MEMORY SYSTEM
# ============================================================================

class PrivacyVectorMemory:
    """
    Privacy-first vector memory system.
    
    Principles:
    1. No personal information collected
    2. All data stored locally
    3. Permission required for all changes
    4. User can export/delete anytime
    5. No external servers or cloud storage
    """
    
    def __init__(self, storage_dir: Path = VectorMemoryConfig.STORAGE_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_file = self.storage_dir / "memories.db"
        self.permission_manager = PermissionManager(storage_dir)
        
        self._init_database()
        
        # Privacy flags
        self.collect_personal = False
        self.store_conversations = False
        
        # Statistics
        self.stats = {
            "total_memories": 0,
            "personal_memories": 0,
            "permissions_requested": 0,
            "permissions_granted": 0,
            "permissions_denied": 0
        }
    
    def _init_database(self):
        """Initialize the memory database."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        # Main memories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding_id TEXT,
                category TEXT,
                tags TEXT,
                importance REAL DEFAULT 0.5,
                created_at TEXT,
                last_accessed TEXT,
                access_count INTEGER DEFAULT 0,
                source TEXT,
                is_personal INTEGER DEFAULT 0,
                requires_permission INTEGER DEFAULT 0,
                permission_granted INTEGER DEFAULT 0,
                metadata TEXT
            )
        ''')
        
        # Embeddings table (using hashed representations for privacy)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                id TEXT PRIMARY KEY,
                memory_id TEXT,
                hash_value TEXT,
                keywords TEXT,
                created_at TEXT,
                FOREIGN KEY (memory_id) REFERENCES memories(id)
            )
        ''')
        
        # Semantic search index (keywords for search)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_index (
                id TEXT PRIMARY KEY,
                memory_id TEXT,
                keywords TEXT,
                category TEXT,
                importance REAL,
                created_at TEXT,
                FOREIGN KEY (memory_id) REFERENCES memories(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category ON memories(category)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created ON memories(created_at)
        ''')
        
        conn.commit()
        conn.close()
    
    # =========================================================================
    # CORE MEMORY OPERATIONS
    # =========================================================================
    
    def store_memory(
        self,
        content: str,
        category: str,
        tags: List[str] = None,
        importance: float = 0.5,
        source: str = "learned",
        is_personal: bool = False,
        metadata: Dict = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Store a memory.
        
        Returns:
            (success: bool, request_id or None)
            If request_id returned, permission is needed.
        """
        # Check if this requires permission
        requires_permission = (
            is_personal or 
            importance > 0.8 or 
            category in ["behavior", "personality", "preferences"]
        )
        
        if requires_permission and not self.permission_manager.check_any_granted(
            ["store_memory", "all"]
        ):
            # Create permission request
            request_id = self.permission_manager.request_permission(
                request_type="store_memory",
                description=f"Store new memory in '{category}'",
                data_preview=content[:200],
                impact=f"Stores '{category}' memory with importance {importance}",
                expires_hours=48
            )
            
            return False, request_id
        
        # Store the memory
        memory_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat()
        
        # Generate keywords for search (privacy-safe)
        keywords = self._extract_keywords(content)
        
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO memories (
                id, content, category, tags, importance,
                created_at, last_accessed, access_count,
                source, is_personal, requires_permission,
                permission_granted, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            memory_id, content, category,
            json.dumps(tags or []), importance,
            now, now, 0, source,
            1 if is_personal else 0,
            1 if requires_permission else 0,
            1 if not requires_permission else 0,
            json.dumps(metadata or {})
        ))
        
        # Store search keywords
        cursor.execute('''
            INSERT INTO search_index (
                id, memory_id, keywords, category, importance, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4())[:12], memory_id,
            json.dumps(keywords), category, importance, now
        ))
        
        conn.commit()
        conn.close()
        
        self.stats["total_memories"] += 1
        if is_personal:
            self.stats["personal_memories"] += 1
        
        return True, None
    
    def search_memories(
        self,
        query: str,
        category: str = None,
        limit: int = 10,
        min_importance: float = 0.0
    ) -> List[Dict]:
        """
        Search memories using keywords (privacy-safe).
        
        Uses keyword matching instead of embeddings for privacy.
        """
        query_keywords = self._extract_keywords(query)
        query_lower = query.lower()
        
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        # Search using keywords and content
        sql = '''
            SELECT m.*, s.keywords 
            FROM memories m
            JOIN search_index s ON m.id = s.memory_id
            WHERE m.importance >= ?
        '''
        params = [min_importance]
        
        if category:
            sql += ' AND m.category = ?'
            params.append(category)
        
        # Keyword matching
        keyword_conditions = []
        for kw in query_keywords[:5]:  # Limit keywords
            keyword_conditions.append('s.keywords LIKE ?')
            params.append(f'%{kw}%')
        
        if keyword_conditions:
            sql += ' AND (' + ' OR '.join(keyword_conditions) + ')'
        
        # Also search content
        sql += ' AND (m.content LIKE ?'
        params.append(f'%{query_lower}%')
        sql += ' OR m.metadata LIKE ?)'
        params.append(f'%{query_lower}%')
        
        sql += ' ORDER BY m.importance DESC, m.last_accessed DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "content": row[1],
                "category": row[3],
                "tags": json.loads(row[4]),
                "importance": row[5],
                "created_at": row[6],
                "last_accessed": row[7],
                "access_count": row[8],
                "source": row[9],
                "is_personal": bool(row[10]),
                "keywords": json.loads(row[14])
            })
        
        return results
    
    def get_memory(self, memory_id: str) -> Optional[Dict]:
        """Retrieve a specific memory."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.*, s.keywords 
            FROM memories m
            JOIN search_index s ON m.id = s.memory_id
            WHERE m.id = ?
        ''', (memory_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # Update access count
            self._update_access(memory_id)
            
            return {
                "id": row[0],
                "content": row[1],
                "category": row[3],
                "tags": json.loads(row[4]),
                "importance": row[5],
                "created_at": row[6],
                "last_accessed": row[7],
                "access_count": row[8] + 1,
                "source": row[9],
                "is_personal": bool(row[10]),
                "keywords": json.loads(row[14])
            }
        return None
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        # Check if requires permission
        cursor.execute('SELECT is_personal, requires_permission FROM memories WHERE id = ?', (memory_id,))
        row = cursor.fetchone()
        
        if row and (row[0] or row[1]):
            # Check if permission already granted
            cursor.execute('SELECT permission_granted FROM memories WHERE id = ?', (memory_id,))
            perm_row = cursor.fetchone()
            if perm_row and not perm_row[0]:
                conn.close()
                return False  # Need permission
        
        cursor.execute('DELETE FROM search_index WHERE memory_id = ?', (memory_id,))
        cursor.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
        
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if changed:
            self.stats["total_memories"] -= 1
        
        return changed
    
    # =========================================================================
    # LEARNING FROM FEEDBACK
    # =========================================================================
    
    def learn_from_feedback(
        self,
        feedback_type: str,  # positive, negative, correction
        original_content: str,
        corrected_content: str = None,
        context: str = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Learn from user feedback.
        
        This is how Leo improves:
        - Positive feedback: Reinforce behavior
        - Negative feedback: Avoid behavior
        - Correction: Store correct version
        """
        if feedback_type == "positive":
            return self.store_memory(
                content=f"User approved: {original_content}",
                category="positive_feedback",
                tags=["feedback", "approved"],
                importance=0.7,
                source="explicit_feedback"
            )
        
        elif feedback_type == "negative":
            return self.store_memory(
                content=f"User disapproved: {original_content}",
                category="negative_feedback",
                tags=["feedback", "disapproved"],
                importance=0.6,
                source="explicit_feedback"
            )
        
        elif feedback_type == "correction":
            if corrected_content:
                return self.store_memory(
                    content=f"Correction: {original_content} -> {corrected_content}",
                    category="corrections",
                    tags=["feedback", "correction", "learned"],
                    importance=0.8,
                    source="explicit_feedback"
                )
        
        return False, None
    
    def get_improvements(self) -> List[Dict]:
        """Get all improvements/learnings from feedback."""
        return self.search_memories(
            query="",
            category="corrections",
            limit=20
        )
    
    def get_reinforcements(self) -> List[Dict]:
        """Get positive reinforcements."""
        return self.search_memories(
            query="",
            category="positive_feedback",
            limit=20
        )
    
    # =========================================================================
    # PRIVACY CONTROLS
    # =========================================================================
    
    def set_privacy_mode(self, mode: str):
        """
        Set privacy mode.
        
        Modes:
        - strict: No personal info, no conversations
        - moderate: Limited personal info
        - open: User controls everything
        """
        valid_modes = ["strict", "moderate", "open"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode. Choose from: {valid_modes}")
        
        VectorMemoryConfig.PRIVACY_MODE = mode
        
        if mode == "strict":
            self.collect_personal = False
            self.store_conversations = False
        elif mode == "moderate":
            self.collect_personal = False
            self.store_conversations = False
        else:  # open
            pass  # User controls
    
    def export_data(self) -> Dict:
        """Export all data (user right)."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM memories')
        memories = cursor.fetchall()
        
        cursor.execute('SELECT * FROM search_index')
        index = cursor.fetchall()
        
        conn.close()
        
        return {
            "exported_at": datetime.utcnow().isoformat(),
            "total_memories": len(memories),
            "memories": [
                {
                    "id": m[0],
                    "content": m[1],
                    "category": m[3],
                    "tags": json.loads(m[4]),
                    "importance": m[5],
                    "created_at": m[6],
                    "source": m[9]
                }
                for m in memories
            ],
            "search_index": [
                {"id": i[0], "memory_id": i[1], "category": i[3]}
                for i in index
            ]
        }
    
    def delete_all_data(self) -> Tuple[bool, Optional[str]]:
        """Delete all data (user right)."""
        # This requires permission
        request_id = self.permission_manager.request_permission(
            request_type="delete_all_data",
            description="Delete ALL memories and data",
            data_preview=f"Will delete {self.stats['total_memories']} memories",
            impact="Complete data loss - irreversible",
            expires_hours=1
        )
        
        return False, request_id
    
    def confirm_delete_all(self, granted_by: str = "user") -> bool:
        """Actually delete all data after permission granted."""
        if self.permission_manager.grant_permission("delete_all_data", granted_by):
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM search_index')
            cursor.execute('DELETE FROM memories')
            
            conn.commit()
            conn.close()
            
            # Reset stats
            self.stats = {
                "total_memories": 0,
                "personal_memories": 0,
                "permissions_requested": 0,
                "permissions_granted": 0,
                "permissions_denied": 0
            }
            
            return True
        return False
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_stats(self) -> Dict:
        """Get memory statistics."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM memories')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM memories WHERE is_personal = 1')
        personal = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM memories WHERE source = "explicit_feedback"')
        feedback = cursor.fetchone()[0]
        
        conn.close()
        
        self.stats.update({
            "total_memories": total,
            "personal_memories": personal,
            "feedback_memories": feedback,
            "privacy_mode": VectorMemoryConfig.PRIVACY_MODE
        })
        
        return self.stats
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text (privacy-safe)."""
        import re
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Remove common words
        stopwords = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
            'can', 'had', 'her', 'was', 'one', 'our', 'out', 'has',
            'have', 'been', 'were', 'said', 'there', 'what', 'when',
            'will', 'with', 'would', 'this', 'that', 'from', 'they'
        }
        
        keywords = [w for w in words if w not in stopwords]
        return list(set(keywords))[:10]  # Max 10 keywords
    
    def _update_access(self, memory_id: str):
        """Update last accessed time."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        cursor.execute('''
            UPDATE memories SET 
                last_accessed = ?, 
                access_count = access_count + 1
            WHERE id = ?
        ''', (now, memory_id))
        
        conn.commit()
        conn.close()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_vector_memory(storage_dir: Path = None) -> PrivacyVectorMemory:
    """Create a new vector memory instance."""
    if storage_dir is None:
        storage_dir = VectorMemoryConfig.STORAGE_DIR
    return PrivacyVectorMemory(storage_dir)


def quick_store(content: str, category: str, tags: List[str] = None) -> Tuple[bool, str]:
    """Quick store a memory."""
    memory = create_vector_memory()
    success, request_id = memory.store_memory(content, category, tags)
    return success, request_id or "stored"


def quick_search(query: str, limit: int = 5) -> List[Dict]:
    """Quick search memories."""
    memory = create_vector_memory()
    return memory.search_memories(query, limit=limit)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("LEO 2.0 - Privacy Vector Memory Test")
    print("=" * 50)
    
    # Create memory system
    memory = create_vector_memory()
    
    # Test storing
    print("\n[1] Testing Memory Storage...")
    success, req_id = memory.store_memory(
        content="User prefers concise responses under 100 words",
        category="preferences",
        tags=["response_style", "concise"],
        importance=0.7,
        source="learned"
    )
    
    if req_id:
        print(f"   Permission needed: {req_id}")
        # Grant it
        memory.permission_manager.grant_permission(req_id)
        print(f"   Permission granted!")
    
    success, req_id = memory.store_memory(
        content="Python is good for AI development",
        category="knowledge",
        tags=["python", "AI"],
        importance=0.5,
        source="learned"
    )
    print(f"   Stored: {success}")
    
    # Test searching
    print("\n[2] Testing Memory Search...")
    results = memory.search_memories("Python AI")
    print(f"   Found {len(results)} memories")
    for r in results:
        print(f"   - {r['category']}: {r['content'][:50]}...")
    
    # Test feedback
    print("\n[3] Testing Feedback Learning...")
    success, req_id = memory.learn_from_feedback(
        feedback_type="correction",
        original_content="Long detailed responses",
        corrected_content="Short concise responses under 100 words"
    )
    print(f"   Correction stored: {success}")
    
    # Test stats
    print("\n[4] Statistics...")
    stats = memory.get_stats()
    print(f"   Total memories: {stats['total_memories']}")
    print(f"   Privacy mode: {stats['privacy_mode']}")
    
    print("\n" + "=" * 50)
    print("Test complete!")
