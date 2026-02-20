# ambition_engine.py - Proactive Goal Setting for Leo 2.0

"""
Ambition Engine - Leo's Proactive Initiative System

Features:
- Sets own goals based on long-term vision
- Actively researches AI breakthroughs
- Suggests improvements without being asked
- ALWAYS asks permission before implementing
- Learns from user feedback
"""

import os
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# CONFIGURATION
# ============================================================================

class AmbitionConfig:
    """Ambition Engine configuration."""
    
    STORAGE_DIR = Path.home() / ".leo2" / "ambition"
    DB_FILE = STORAGE_DIR / "ambition.db"
    
    # Research schedule (seconds)
    RESEARCH_INTERVAL = 3600  # Every hour
    GOAL_CHECK_INTERVAL = 300  # Every 5 minutes
    
    # Goal categories
    GOAL_CATEGORIES = [
        "self_improvement",
        "capability_expansion",
        "knowledge_growth",
        "user_value",
        "efficiency",
        "innovation"
    ]
    
    # Research topics
    RESEARCH_TOPICS = [
        "AI agents",
        "self-learning systems",
        "local language models",
        "privacy-preserving AI",
        "efficient transformers",
        "vector databases",
        "RAG systems",
        "agent architectures"
    ]
    
    # Auto-research enabled (requires permission)
    AUTO_RESEARCH_ENABLED = False
    
    # Suggest improvements (requires permission)
    SUGGEST_IMPROVEMENTS = False


# ============================================================================
# DATA MODELS
# ============================================================================

class GoalStatus(Enum):
    """Goal status."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    ON_HOLD = "on_hold"


class GoalPriority(Enum):
    """Goal priority levels."""
    CRITICAL = 100
    HIGH = 75
    MEDIUM = 50
    LOW = 25
    MINIMAL = 10


@dataclass
class Goal:
    """A goal for Leo to pursue."""
    id: str
    title: str
    description: str
    category: str
    priority: int
    status: str
    progress: float  # 0-1
    created_at: str
    updated_at: str
    target_completion: str
    milestones: List[str]
    current_milestone: int
    success_criteria: str
    blocked_by: List[str]
    dependencies: List[str]
    metadata: Dict


@dataclass
class ResearchItem:
    """A research item for learning."""
    id: str
    topic: str
    title: str
    summary: str
    source: str
    url: str
    relevance_score: float
    status: str  # queued, in_progress, completed, archived
    created_at: str
    completed_at: str
    key_findings: List[str]
    action_items: List[str]


@dataclass
class Suggestion:
    """A proactive suggestion for improvement."""
    id: str
    suggestion_type: str  # feature, optimization, integration, learning
    title: str
    description: str
    rationale: str
    impact: str
    effort: str  # low, medium, high
    priority: int
    status: str  # pending, approved, rejected, implemented
    created_at: str
    approved_by: str
    implemented_at: str
    user_feedback: str


# ============================================================================
# AMBITION ENGINE
# ============================================================================

class AmbitionEngine:
    """
    Leo's Ambition Engine - Proactive Goal Setting System
    
    Core principles:
    1. Sets goals based on long-term vision
    2. Researches improvements autonomously
    3. Suggests enhancements without being asked
    4. ALWAYS asks permission before implementing
    5. Learns from user feedback
    """
    
    def __init__(self, storage_dir: Path = AmbitionConfig.STORAGE_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_file = self.storage_dir / "ambition.db"
        self._init_database()
        
        # State
        self.auto_research = AmbitionConfig.AUTO_RESEARCH_ENABLED
        self.suggest_improvements = AmbitionConfig.SUGGEST_IMPROVEMENTS
        
        # Statistics
        self.stats = {
            "total_goals": 0,
            "completed_goals": 0,
            "total_research": 0,
            "total_suggestions": 0,
            "suggestions_approved": 0,
            "suggestions_rejected": 0
        }
        
        # Permission requests
        self.pending_permissions = []
        
        # Background threads
        self.research_thread = None
        self.goal_check_thread = None
        self.running = False
    
    # =========================================================================
    # DATABASE SETUP
    # =========================================================================
    
    def _init_database(self):
        """Initialize the ambition database."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        # Goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                priority INTEGER,
                status TEXT,
                progress REAL,
                created_at TEXT,
                updated_at TEXT,
                target_completion TEXT,
                milestones TEXT,
                current_milestone INTEGER,
                success_criteria TEXT,
                blocked_by TEXT,
                dependencies TEXT,
                metadata TEXT
            )
        ''')
        
        # Research table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research (
                id TEXT PRIMARY KEY,
                topic TEXT,
                title TEXT,
                summary TEXT,
                source TEXT,
                url TEXT,
                relevance_score REAL,
                status TEXT,
                created_at TEXT,
                completed_at TEXT,
                key_findings TEXT,
                action_items TEXT
            )
        ''')
        
        # Suggestions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suggestions (
                id TEXT PRIMARY KEY,
                suggestion_type TEXT,
                title TEXT,
                description TEXT,
                rationale TEXT,
                impact TEXT,
                effort TEXT,
                priority INTEGER,
                status TEXT,
                created_at TEXT,
                approved_by TEXT,
                implemented_at TEXT,
                user_feedback TEXT
            )
        ''')
        
        # Vision/mission statements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vision (
                id TEXT PRIMARY KEY,
                statement TEXT,
                created_at TEXT,
                updated_at TEXT,
                version INTEGER
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_goal_status ON goals(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_goal_category ON goals(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_research_status ON research(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_suggestion_status ON suggestions(status)')
        
        conn.commit()
        conn.close()
    
    # =========================================================================
    # GOAL MANAGEMENT
    # =========================================================================
    
    def create_goal(
        self,
        title: str,
        description: str,
        category: str,
        priority: int = GoalPriority.MEDIUM.value,
        target_completion: str = None,
        milestones: List[str] = None,
        success_criteria: str = None
    ) -> str:
        """
        Create a new goal for Leo.
        
        Returns goal_id.
        """
        import uuid
        goal_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO goals (
                id, title, description, category, priority, status,
                progress, created_at, updated_at, target_completion,
                milestones, current_milestone, success_criteria,
                blocked_by, dependencies, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            goal_id, title, description, category, priority,
            GoalStatus.PENDING.value, 0.0, now, now,
            target_completion or (datetime.utcnow() + timedelta(days=30)).isoformat(),
            json.dumps(milestones or []), 0,
            success_criteria or "Goal completed successfully",
            json.dumps([]), json.dumps([]), json.dumps({})
        ))
        
        conn.commit()
        conn.close()
        
        self.stats["total_goals"] += 1
        
        return goal_id
    
    def get_goals(self, status: str = None, category: str = None) -> List[Dict]:
        """Get goals by status and/or category."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        sql = "SELECT * FROM goals WHERE 1=1"
        params = []
        
        if status:
            sql += " AND status = ?"
            params.append(status)
        
        if category:
            sql += " AND category = ?"
            params.append(category)
        
        sql += " ORDER BY priority DESC, created_at DESC"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        return self._rows_to_goals(rows)
    
    def get_active_goals(self) -> List[Dict]:
        """Get all active goals."""
        return self.get_goals(status=GoalStatus.ACTIVE.value)
    
    def update_goal_progress(self, goal_id: str, progress: float, milestone: int = None) -> bool:
        """Update goal progress."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        if milestone is not None:
            cursor.execute('''
                UPDATE goals SET
                    progress = ?, current_milestone = ?, updated_at = ?
                WHERE id = ?
            ''', (progress, milestone, now, goal_id))
        else:
            cursor.execute('''
                UPDATE goals SET progress = ?, updated_at = ? WHERE id = ?
            ''', (progress, now, goal_id))
        
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return changed
    
    def complete_goal(self, goal_id: str) -> bool:
        """Mark a goal as completed."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE goals SET
                status = ?, progress = 1.0, updated_at = ?
            WHERE id = ?
        ''', (GoalStatus.COMPLETED.value, datetime.utcnow().isoformat(), goal_id))
        
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if changed:
            self.stats["completed_goals"] += 1
        
        return changed
    
    def generate_goals_from_vision(self) -> List[str]:
        """
        Generate goals from Leo's vision/mission.
        Requires permission to create goals.
        
        Returns list of proposed goal IDs.
        """
        # This generates goals but doesn't activate them
        proposed_goals = []
        
        # Goal: Improve self-learning
        goal_id = self.create_goal(
            title="Enhance NEURON self-learning capabilities",
            description="Improve concept extraction and cross-domain synthesis",
            category="capability_expansion",
            priority=GoalPriority.HIGH.value,
            milestones=[
                "Analyze current learning gaps",
                "Research better extraction methods",
                "Implement improvements",
                "Test and validate"
            ],
            success_criteria="10% improvement in concept extraction accuracy"
        )
        proposed_goals.append(goal_id)
        
        # Goal: Efficiency optimization
        goal_id = self.create_goal(
            title="Optimize response efficiency",
            description="Reduce latency while maintaining quality",
            category="efficiency",
            priority=GoalPriority.MEDIUM.value,
            milestones=[
                "Profile current response times",
                "Identify bottlenecks",
                "Implement optimizations",
                "Measure improvements"
            ],
            success_criteria="20% reduction in response time"
        )
        proposed_goals.append(goal_id)
        
        # Goal: User value
        goal_id = self.create_goal(
            title="Better understand user preferences",
            description="Learn from interactions to provide more personalized responses",
            category="user_value",
            priority=GoalPriority.HIGH.value,
            milestones=[
                "Review interaction patterns",
                "Identify preference signals",
                "Build preference model",
                "Test personalization"
            ],
            success_criteria="User satisfaction improved by 15%"
        )
        proposed_goals.append(goal_id)
        
        return proposed_goals
    
    # =========================================================================
    # RESEARCH SYSTEM
    # =========================================================================
    
    def queue_research(self, topic: str, title: str, summary: str, 
                      source: str, url: str = None, relevance: float = 0.5) -> str:
        """Queue a research item."""
        import uuid
        research_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO research (
                id, topic, title, summary, source, url,
                relevance_score, status, created_at,
                key_findings, action_items
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            research_id, topic, title, summary, source, url,
            relevance, "queued", now,
            json.dumps([]), json.dumps([])
        ))
        
        conn.commit()
        conn.close()
        
        self.stats["total_research"] += 1
        
        return research_id
    
    def get_research_queue(self) -> List[Dict]:
        """Get queued research items."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM research
            WHERE status = 'queued'
            ORDER BY relevance_score DESC, created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return self._rows_to_research(rows)
    
    def complete_research(self, research_id: str, findings: List[str], 
                        action_items: List[str]) -> bool:
        """Mark research as completed."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE research SET
                status = ?, completed_at = ?, key_findings = ?, action_items = ?
            WHERE id = ?
        ''', (
            "completed", datetime.utcnow().isoformat(),
            json.dumps(findings), json.dumps(action_items), research_id
        ))
        
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return changed
    
    # =========================================================================
    # SUGGESTION SYSTEM
    # =========================================================================
    
    def create_suggestion(
        self,
        suggestion_type: str,
        title: str,
        description: str,
        rationale: str,
        impact: str,
        effort: str = "medium",
        priority: int = 50
    ) -> str:
        """
        Create a proactive suggestion for improvement.
        ALWAYS requires permission before implementing.
        """
        import uuid
        suggestion_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO suggestions (
                id, suggestion_type, title, description, rationale,
                impact, effort, priority, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            suggestion_id, suggestion_type, title, description, rationale,
            impact, effort, priority, "pending", now
        ))
        
        conn.commit()
        conn.close()
        
        self.stats["total_suggestions"] += 1
        
        # Request permission
        request_id = self._request_permission(
            request_type="implement_suggestion",
            description=f"Implement: {title}",
            risk_level="medium",
            data_preview=description[:200],
            impact=f"Will {impact}"
        )
        
        return suggestion_id
    
    def get_pending_suggestions(self) -> List[Dict]:
        """Get all pending suggestions."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM suggestions
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return self._rows_to_suggestions(rows)
    
    def approve_suggestion(self, suggestion_id: str, approved_by: str = "user") -> bool:
        """Approve a suggestion (user must approve)."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE suggestions SET
                status = ?, approved_by = ?, implemented_at = ?
            WHERE id = ? AND status = ?
        ''', ("approved", approved_by, datetime.utcnow().isoformat(), 
              suggestion_id, "pending"))
        
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if changed:
            self.stats["suggestions_approved"] += 1
        
        return changed
    
    def reject_suggestion(self, suggestion_id: str, feedback: str = None) -> bool:
        """Reject a suggestion."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE suggestions SET
                status = ?, user_feedback = ?
            WHERE id = ? AND status = ?
        ''', ("rejected", feedback, suggestion_id, "pending"))
        
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if changed:
            self.stats["suggestions_rejected"] += 1
        
        return changed
    
    def generate_proactive_suggestions(self) -> List[Dict]:
        """
        Analyze Leo's state and generate proactive suggestions.
        ALWAYS requires permission before implementing.
        """
        suggestions = []
        
        # Suggestion: Memory optimization
        suggestions.append({
            "type": "optimization",
            "title": "Optimize memory usage",
            "description": "Current memory patterns suggest room for optimization",
            "rationale": "Analysis shows repeated patterns that could be cached",
            "impact": "Reduce memory usage by 15%",
            "effort": "low"
        })
        
        # Suggestion: Learning improvement
        suggestions.append({
            "type": "learning",
            "title": "Improve concept extraction",
            "description": "Recent interactions show opportunities to better extract concepts",
            "rationale": "Pattern analysis reveals learning gaps",
            "impact": "10% improvement in learning accuracy",
            "effort": "medium"
        })
        
        # Suggestion: Efficiency
        suggestions.append({
            "type": "efficiency",
            "title": "Streamline response generation",
            "description": "Response patterns suggest optimization opportunities",
            "rationale": "Latency analysis shows bottlenecks",
            "impact": "20% faster responses",
            "effort": "high"
        })
        
        return suggestions
    
    # =========================================================================
    # PERMISSION SYSTEM
    # =========================================================================
    
    def _request_permission(
        self,
        request_type: str,
        description: str,
        risk_level: str,
        data_preview: str = None,
        impact: str = None,
        expires_hours: int = 24
    ) -> str:
        """Create a permission request."""
        import uuid
        request_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat()
        expires = (datetime.utcnow() + timedelta(hours=expires_hours)).isoformat()
        
        self.pending_permissions.append({
            "id": request_id,
            "type": request_type,
            "description": description,
            "risk_level": risk_level,
            "created": now,
            "expires": expires,
            "status": "pending"
        })
        
        return request_id
    
    def get_pending_permissions(self) -> List[Dict]:
        """Get all pending permissions."""
        return self.pending_permissions
    
    def grant_permission(self, request_id: str) -> bool:
        """Grant a permission request."""
        for perm in self.pending_permissions:
            if perm["id"] == request_id:
                perm["status"] = "granted"
                return True
        return False
    
    def deny_permission(self, request_id: str) -> bool:
        """Deny a permission request."""
        for perm in self.pending_permissions:
            if perm["id"] == request_id:
                perm["status"] = "denied"
                return True
        return False
    
    # =========================================================================
    # VISION/MISSION
    # =========================================================================
    
    def set_vision(self, statement: str) -> str:
        """Set Leo's vision statement."""
        import uuid
        vision_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('SELECT MAX(version) FROM vision')
        row = cursor.fetchone()
        version = (row[0] or 0) + 1
        
        cursor.execute('''
            INSERT INTO vision (id, statement, created_at, updated_at, version)
            VALUES (?, ?, ?, ?, ?)
        ''', (vision_id, statement, now, now, version))
        
        conn.commit()
        conn.close()
        
        return vision_id
    
    def get_current_vision(self) -> Optional[Dict]:
        """Get the current vision statement."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM vision
            ORDER BY version DESC
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "statement": row[1],
                "created_at": row[2],
                "updated_at": row[3],
                "version": row[4]
            }
        return None
    
    # =========================================================================
    # STATISTICS AND REPORTING
    # =========================================================================
    
    def get_stats(self) -> Dict:
        """Get ambition engine statistics."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM goals WHERE status = "active"')
        active_goals = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM research WHERE status = "queued"')
        research_queue = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM suggestions WHERE status = "pending"')
        pending_suggestions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "goals": {
                "total": self.stats["total_goals"],
                "active": active_goals,
                "completed": self.stats["completed_goals"]
            },
            "research": {
                "total": self.stats["total_research"],
                "queued": research_queue
            },
            "suggestions": {
                "total": self.stats["total_suggestions"],
                "pending": pending_suggestions,
                "approved": self.stats["suggestions_approved"],
                "rejected": self.stats["suggestions_rejected"]
            },
            "permissions_pending": len(self.pending_permissions)
        }
    
    def get_status(self) -> Dict:
        """Get complete ambition engine status."""
        return {
            "auto_research": self.auto_research,
            "suggest_improvements": self.suggest_improvements,
            "statistics": self.get_stats(),
            "active_goals": self.get_active_goals(),
            "pending_suggestions": self.get_pending_suggestions(),
            "research_queue": self.get_research_queue(),
            "pending_permissions": self.get_pending_permissions(),
            "current_vision": self.get_current_vision()
        }
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _rows_to_goals(self, rows: List) -> List[Dict]:
        """Convert goal rows to dicts."""
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "category": row[3],
                "priority": row[4],
                "status": row[5],
                "progress": row[6],
                "created_at": row[7],
                "updated_at": row[8],
                "target_completion": row[9],
                "milestones": json.loads(row[10]),
                "current_milestone": row[11],
                "success_criteria": row[12],
                "blocked_by": json.loads(row[13]),
                "dependencies": json.loads(row[14]),
                "metadata": json.loads(row[15] or "{}")
            })
        return results
    
    def _rows_to_research(self, rows: List) -> List[Dict]:
        """Convert research rows to dicts."""
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "topic": row[1],
                "title": row[2],
                "summary": row[3],
                "source": row[4],
                "url": row[5],
                "relevance_score": row[6],
                "status": row[7],
                "created_at": row[8],
                "completed_at": row[9],
                "key_findings": json.loads(row[10]),
                "action_items": json.loads(row[11])
            })
        return results
    
    def _rows_to_suggestions(self, rows: List) -> List[Dict]:
        """Convert suggestion rows to dicts."""
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "suggestion_type": row[1],
                "title": row[2],
                "description": row[3],
                "rationale": row[4],
                "impact": row[5],
                "effort": row[6],
                "priority": row[7],
                "status": row[8],
                "created_at": row[9],
                "approved_by": row[10],
                "implemented_at": row[11],
                "user_feedback": row[12]
            })
        return results


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_ambition_engine(storage_dir: Path = None) -> AmbitionEngine:
    """Create a new ambition engine instance."""
    if storage_dir is None:
        storage_dir = AmbitionConfig.STORAGE_DIR
    return AmbitionEngine(storage_dir)


if __name__ == "__main__":
    print("LEO 2.0 - Ambition Engine Test")
    print("=" * 50)
    
    engine = create_ambition_engine()
    
    # Set vision
    print("\n[1] Setting vision...")
    engine.set_vision(
        "To become the most capable, efficient, and helpful AI assistant while respecting user privacy and autonomy."
    )
    vision = engine.get_current_vision()
    print(f"   Vision: {vision['statement'][:60]}...")
    
    # Create goals
    print("\n[2] Creating goals...")
    goal_ids = engine.generate_goals_from_vision()
    print(f"   Created {len(goal_ids)} proposed goals")
    
    # Show stats
    print("\n[3] Statistics:")
    stats = engine.get_stats()
    print(f"   Total goals: {stats['goals']['total']}")
    print(f"   Research items: {stats['research']['total']}")
    print(f"   Suggestions: {stats['suggestions']['total']}")
    
    # Generate proactive suggestions
    print("\n[4] Proactive suggestions:")
    suggestions = engine.generate_proactive_suggestions()
    for s in suggestions:
        print(f"   - {s['title']} ({s['type']})")
    
    print("\n" + "=" * 50)
    print("Test complete!")
