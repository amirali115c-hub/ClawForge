# self_reflection.py - Leo's Self-Analysis System

"""
Self-Reflection Module - Leo Analyzes and Improves Himself

Features:
- Analyze own performance and errors
- Identify areas for improvement
- Suggest modifications (ALWAYS asks permission)
- Never autonomous modification
- Learn from feedback patterns
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# CONFIGURATION
# ============================================================================

class ReflectionConfig:
    """Self-reflection configuration."""
    
    STORAGE_DIR = Path.home() / ".leo2" / "reflection"
    DB_FILE = STORAGE_DIR / "reflection.db"
    
    # Analysis intervals
    PERFORMANCE_CHECK_INTERVAL = 3600  # Every hour
    ERROR_ANALYSIS_INTERVAL = 1800  # Every 30 minutes
    
    # Thresholds
    ERROR_THRESHOLD = 5  # Errors before auto-analysis
    LATENCY_THRESHOLD_MS = 5000  # 5 seconds
    
    # Self-modification requires explicit permission
    REQUIRE_PERMISSION_FOR_CHANGES = True


# ============================================================================
# DATA MODELS
# ============================================================================

class ReflectionCategory(Enum):
    """Categories of self-reflection."""
    PERFORMANCE = "performance"
    ACCURACY = "accuracy"
    EFFICIENCY = "efficiency"
    USER_SATISFACTION = "user_satisfaction"
    ERROR_ANALYSIS = "error_analysis"
    LEARNING = "learning"
    COMMUNICATION = "communication"


class ModificationStatus(Enum):
    """Status of proposed modifications."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    IMPLEMENTED = "implemented"
    EXPIRED = "expired"


@dataclass
class PerformanceMetric:
    """A single performance metric."""
    id: str
    category: str
    metric_name: str
    value: float
    unit: str
    timestamp: str
    context: str
    trend: str  # improving, declining, stable


@dataclass
class ErrorRecord:
    """A recorded error or issue."""
    id: str
    error_type: str
    description: str
    severity: str  # low, medium, high, critical
    context: str
    timestamp: str
    frequency: int
    resolved: bool
    resolution: str
    learnings: List[str]


@dataclass
class SelfModification:
    """A proposed modification to Leo's behavior/configuration."""
    id: str
    category: str
    title: str
    description: str
    rationale: str
    expected_improvement: str
    risk_level: str  # low, medium, high
    implementation_steps: List[str]
    status: str
    created_at: str
    expires_at: str
    approved_by: str
    implemented_at: str
    user_feedback: str
    effectiveness_score: float  # Post-implementation rating


@dataclass
class Insight:
    """A self-generated insight about Leo's behavior."""
    id: str
    category: str
    insight: str
    evidence: List[str]
    confidence: float
    recommendations: List[str]
    created_at: str
    useful_count: int
    applied: bool


# ============================================================================
# SELF-REFLECTION ENGINE
# ============================================================================

class SelfReflectionEngine:
    """
    Leo's Self-Reflection System
    
    Core principles:
    1. Analyze own performance continuously
    2. Identify errors and improvement areas
    3. ALWAYS ask permission before changing
    4. Never autonomous modification
    5. Learn from patterns
    """
    
    def __init__(self, storage_dir: Path = ReflectionConfig.STORAGE_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_file = self.storage_dir / "reflection.db"
        self._init_database()
        
        # Statistics
        self.stats = {
            "total_metrics": 0,
            "total_errors": 0,
            "total_modifications": 0,
            "modifications_approved": 0,
            "modifications_denied": 0,
            "total_insights": 0
        }
        
        # Recent performance data
        self.recent_metrics = []
        self.recent_errors = []
    
    # =========================================================================
    # DATABASE SETUP
    # =========================================================================
    
    def _init_database(self):
        """Initialize the reflection database."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        # Performance metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id TEXT PRIMARY KEY,
                category TEXT,
                metric_name TEXT,
                value REAL,
                unit TEXT,
                timestamp TEXT,
                context TEXT,
                trend TEXT
            )
        ''')
        
        # Error records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS errors (
                id TEXT PRIMARY KEY,
                error_type TEXT,
                description TEXT,
                severity TEXT,
                context TEXT,
                timestamp TEXT,
                frequency INTEGER,
                resolved BOOLEAN,
                resolution TEXT,
                learnings TEXT
            )
        ''')
        
        # Self-modifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS modifications (
                id TEXT PRIMARY KEY,
                category TEXT,
                title TEXT,
                description TEXT,
                rationale TEXT,
                expected_improvement TEXT,
                risk_level TEXT,
                implementation_steps TEXT,
                status TEXT,
                created_at TEXT,
                expires_at TEXT,
                approved_by TEXT,
                implemented_at TEXTedback TEXT,
               ,
                user_fe effectiveness_score REAL
            )
        ''')
        
        # Insights
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id TEXT PRIMARY KEY,
                category TEXT,
                insight TEXT,
                evidence TEXT,
                confidence REAL,
                recommendations TEXT,
                created_at TEXT,
                useful_count INTEGER,
                applied BOOLEAN
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metric_time ON metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_time ON errors(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mod_status ON modifications(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_insight_cat ON insights(category)')
        
        conn.commit()
        conn.close()
    
    # =========================================================================
    # PERFORMANCE TRACKING
    # =========================================================================
    
    def record_metric(
        self,
        category: str,
        metric_name: str,
        value: float,
        unit: str,
        context: str = None,
        trend: str = "stable"
    ) -> str:
        """Record a performance metric."""
        import uuid
        metric_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO metrics (
                id, category, metric_name, value, unit,
                timestamp, context, trend
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metric_id, category, metric_name, value, unit,
            now, context, trend
        ))
        
        conn.commit()
        conn.close()
        
        self.stats["total_metrics"] += 1
        self.recent_metrics.append((category, value, now))
        
        # Keep only last 100 in memory
        if len(self.recent_metrics) > 100:
            self.recent_metrics = self.recent_metrics[-100:]
        
        return metric_id
    
    def get_metrics(
        self,
        category: str = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict]:
        """Get performance metrics."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        sql = "SELECT * FROM metrics WHERE timestamp > ?"
        params = [since]
        
        if category:
            sql += " AND category = ?"
            params.append(category)
        
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        return self._rows_to_metrics(rows)
    
    def analyze_performance(self) -> Dict:
        """Analyze recent performance metrics."""
        metrics = self.get_metrics(hours=24, limit=1000)
        
        if not metrics:
            return {"status": "no_data", "message": "No metrics available"}
        
        # Group by category
        by_category = {}
        for m in metrics:
            cat = m["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(m["value"])
        
        # Calculate averages
        analysis = {}
        for cat, values in by_category.items():
            analysis[cat] = {
                "average": sum(values) / len(values),
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "trend": self._calculate_trend(values)
            }
        
        # Identify issues
        issues = []
        for cat, data in analysis.items():
            if data["average"] > ReflectionConfig.LATENCY_THRESHOLD_MS:
                if cat in ["latency", "response_time"]:
                    issues.append({
                        "type": "high_latency",
                        "category": cat,
                        "average": data["average"],
                        "threshold": ReflectionConfig.LATENCY_THRESHOLD_MS
                    })
        
        return {
            "status": "analyzed",
            "period_hours": 24,
            "total_metrics": len(metrics),
            "analysis": analysis,
            "issues_identified": issues,
            "recommendations": self._generate_performance_recommendations(analysis, issues)
        }
    
    # =========================================================================
    # ERROR TRACKING
    # =========================================================================
    
    def record_error(
        self,
        error_type: str,
        description: str,
        severity: str,
        context: str = None
    ) -> str:
        """Record an error or issue."""
        import uuid
        error_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat()
        
        # Check for frequency
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM errors
            WHERE error_type = ? AND timestamp > ?
        ''', (error_type, (datetime.utcnow() - timedelta(hours=1)).isoformat()))
        
        frequency = cursor.fetchone()[0]
        
        cursor.execute('''
            INSERT INTO errors (
                id, error_type, description, severity,
                context, timestamp, frequency, resolved, learnings
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            error_id, error_type, description, severity,
            context, now, frequency + 1, False, json.dumps([])
        ))
        
        conn.commit()
        conn.close()
        
        self.stats["total_errors"] += 1
        self.recent_errors.append(error_id)
        
        # Auto-analyze if threshold reached
        if frequency >= ReflectionConfig.ERROR_THRESHOLD:
            self._auto_analyze_errors(error_type)
        
        return error_id
    
    def resolve_error(self, error_id: str, resolution: str, learnings: List[str]) -> bool:
        """Mark an error as resolved."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE errors SET
                resolved = ?, resolution = ?, learnings = ?
            WHERE id = ?
        ''', (True, resolution, json.dumps(learnings), error_id))
        
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return changed
    
    def get_errors(self, unresolved_only: bool = False, hours: int = 24) -> List[Dict]:
        """Get error records."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        if unresolved_only:
            cursor.execute('''
                SELECT * FROM errors
                WHERE timestamp > ? AND resolved = 0
                ORDER BY frequency DESC, timestamp DESC
            ''', (since,))
        else:
            cursor.execute('''
                SELECT * FROM errors
                WHERE timestamp > ?
                ORDER BY frequency DESC, timestamp DESC
            ''', (since,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return self._rows_to_errors(rows)
    
    def analyze_errors(self) -> Dict:
        """Analyze error patterns."""
        errors = self.get_errors(hours=24)
        
        if not errors:
            return {"status": "no_errors", "message": "No errors recorded"}
        
        # Group by type
        by_type = {}
        by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        for e in errors:
            e_type = e["error_type"]
            if e_type not in by_type:
                by_type[e_type] = {"count": 0, "recent": []}
            by_type[e_type]["count"] += 1
            by_type[e_type]["recent"].append(e["timestamp"])
            
            if e["severity"] in by_severity:
                by_severity[e["severity"]] += 1
        
        # Identify patterns
        patterns = []
        for e_type, data in by_type.items():
            if data["count"] >= 3:
                patterns.append({
                    "error_type": e_type,
                    "frequency": data["count"],
                    "recommendation": self._recommend_error_fix(e_type)
                })
        
        return {
            "status": "analyzed",
            "total_errors": len(errors),
            "by_type": by_type,
            "by_severity": by_severity,
            "patterns": patterns,
            "critical_count": by_severity.get("critical", 0)
        }
    
    def _auto_analyze_errors(self, error_type: str):
        """Auto-analyze frequent errors."""
        # This creates an insight but doesn't implement changes
        insight_id = self.generate_insight(
            category="error_analysis",
            insight=f"Error type '{error_type}' occurring frequently",
            evidence=["Frequent occurrences detected"],
            recommendations=["Review error handling for " + error_type]
        )
        
        return insight_id
    
    # =========================================================================
    # SELF-MODIFICATION (ALWAYS REQUIRES PERMISSION)
    # =========================================================================
    
    def propose_modification(
        self,
        category: str,
        title: str,
        description: str,
        rationale: str,
        expected_improvement: str,
        risk_level: str,
        implementation_steps: List[str],
        expires_hours: int = 48
    ) -> Tuple[bool, str]:
        """
        Propose a modification to Leo's behavior.
        ALWAYS requires permission before implementing.
        
        Returns: (pending_permission: bool, request_id: str)
        """
        import uuid
        mod_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat()
        expires = (datetime.utcnow() + timedelta(hours=expires_hours)).isoformat()
        
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO modifications (
                id, category, title, description, rationale,
                expected_improvement, risk_level, implementation_steps,
                status, created_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            mod_id, category, title, description, rationale,
            expected_improvement, risk_level, json.dumps(implementation_steps),
            ModificationStatus.PENDING.value, now, expires
        ))
        
        conn.commit()
        conn.close()
        
        self.stats["total_modifications"] += 1
        
        # Request permission
        request_id = self._request_permission(
            request_type="self_modification",
            description=f"Modify {category}: {title}",
            risk_level=risk_level,
            data_preview=description[:200],
            impact=expected_improvement,
            expires_hours=expires_hours
        )
        
        return True, request_id
    
    def approve_modification(self, mod_id: str, approved_by: str = "user") -> bool:
        """Approve a modification (user must approve)."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE modifications SET
                status = ?, approved_by = ?
            WHERE id = ? AND status = ?
        ''', (ModificationStatus.APPROVED.value, approved_by, 
              mod_id, ModificationStatus.PENDING.value))
        
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if changed:
            self.stats["modifications_approved"] += 1
        
        return changed
    
    def deny_modification(self, mod_id: str, feedback: str = None) -> bool:
        """Deny a modification."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE modifications SET
                status = ?, user_feedback = ?
            WHERE id = ? AND status = ?
        ''', (ModificationStatus.DENIED.value, feedback,
              mod_id, ModificationStatus.PENDING.value))
        
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if changed:
            self.stats["modifications_denied"] += 1
        
        return changed
    
    def implement_modification(self, mod_id: str) -> bool:
        """Mark a modification as implemented (after approval)."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE modifications SET
                status = ?, implemented_at = ?
            WHERE id = ? AND status = ?
        ''', (ModificationStatus.IMPLEMENTED.value, datetime.utcnow().isoformat(),
              mod_id, ModificationStatus.APPROVED.value))
        
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return changed
    
    def get_pending_modifications(self) -> List[Dict]:
        """Get all pending modifications."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM modifications
            WHERE status = 'pending'
            ORDER BY created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return self._rows_to_modifications(rows)
    
    def generate_modification_suggestions(self) -> List[Dict]:
        """Analyze performance and suggest modifications."""
        suggestions = []
        
        # Analyze performance
        perf_analysis = self.analyze_performance()
        
        if "issues_identified" in perf_analysis:
            for issue in perf_analysis["issues_identified"]:
                if issue["type"] == "high_latency":
                    suggestions.append({
                        "category": "efficiency",
                        "title": f"Optimize {issue['category']}",
                        "description": f"Average {issue['category']} is {issue['average']:.0f}ms, above threshold",
                        "rationale": "Performance analysis shows room for improvement",
                        "expected_improvement": "Reduce latency by 20%",
                        "risk_level": "medium",
                        "implementation_steps": [
                            "Profile current implementation",
                            "Identify bottlenecks",
                            "Implement optimizations",
                            "Test changes"
                        ]
                    })
        
        return suggestions
    
    # =========================================================================
    # INSIGHTS GENERATION
    # =========================================================================
    
    def generate_insight(
        self,
        category: str,
        insight: str,
        evidence: List[str],
        recommendations: List[str],
        confidence: float = 0.7
    ) -> str:
        """Generate a self-insight."""
        import uuid
        insight_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO insights (
                id, category, insight, evidence, confidence,
                recommendations, created_at, useful_count, applied
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            insight_id, category, insight, json.dumps(evidence),
            confidence, json.dumps(recommendations), now, 0, False
        ))
        
        conn.commit()
        conn.close()
        
        self.stats["total_insights"] += 1
        
        return insight_id
    
    def get_insights(self, category: str = None, unapplied_only: bool = False) -> List[Dict]:
        """Get insights."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        sql = "SELECT * FROM insights WHERE 1=1"
        params = []
        
        if category:
            sql += " AND category = ?"
            params.append(category)
        
        if unapplied_only:
            sql += " AND applied = 0"
        
        sql += " ORDER BY confidence DESC, created_at DESC"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        return self._rows_to_insights(rows)
    
    def mark_insight_applied(self, insight_id: str) -> bool:
        """Mark an insight as applied."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE insights SET applied = 1 WHERE id = ?
        ''', (insight_id,))
        
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return changed
    
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
        """Create a permission request for self-modification."""
        import uuid
        request_id = str(uuid.uuid4())[:8]
        
        # This would integrate with the Custodian permission system
        # For now, we store it locally
        return request_id
    
    def get_pending_permissions(self) -> List[Dict]:
        """Get pending modification permissions."""
        mods = self.get_pending_modifications()
        return [
            {
                "id": m["id"],
                "type": "self_modification",
                "title": m["title"],
                "description": m["description"],
                "risk_level": m["risk_level"],
                "status": m["status"]
            }
            for m in mods
        ]
    
    # =========================================================================
    # STATISTICS AND REPORTING
    # =========================================================================
    
    def get_stats(self) -> Dict:
        """Get reflection statistics."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM metrics')
        total_metrics = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM errors WHERE resolved = 0')
        open_errors = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM modifications WHERE status = "pending"')
        pending_mods = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM insights WHERE applied = 0')
        unapplied_insights = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "metrics_recorded": total_metrics,
            "open_errors": open_errors,
            "pending_modifications": pending_mods,
            "unapplied_insights": unapplied_insights,
            "modifications": {
                "total": self.stats["total_modifications"],
                "approved": self.stats["modifications_approved"],
                "denied": self.stats["modifications_denied"]
            },
            "insights_generated": self.stats["total_insights"]
        }
    
    def get_status(self) -> Dict:
        """Get complete reflection status."""
        return {
            "statistics": self.get_stats(),
            "recent_metrics": self.recent_metrics[-10:],
            "recent_errors": len(self.recent_errors),
            "performance_analysis": self.analyze_performance(),
            "error_analysis": self.analyze_errors(),
            "pending_modifications": self.get_pending_modifications(),
            "pending_permissions": self.get_pending_permissions()
        }
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from values."""
        if len(values) < 2:
            return "stable"
        
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        if second_half < first_half * 0.9:
            return "improving"
        elif second_half > first_half * 1.1:
            return "declining"
        else:
            return "stable"
    
    def _generate_performance_recommendations(self, analysis: Dict, issues: List) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        for issue in issues:
            if issue["type"] == "high_latency":
                recommendations.append(
                    f"Optimize {issue['category']} - currently averaging {issue['average']:.0f}ms"
                )
        
        return recommendations
    
    def _recommend_error_fix(self, error_type: str) -> str:
        """Recommend fix for error type."""
        fixes = {
            "timeout": "Add retry logic and better timeout handling",
            "connection": "Improve connection pooling and error recovery",
            "memory": "Optimize memory usage and add garbage collection",
            "parsing": "Improve input validation and error handling",
            "rate_limit": "Implement rate limiting and backoff",
        }
        
        return fixes.get(error_type, f"Review error handling for {error_type}")
    
    def _rows_to_metrics(self, rows: List) -> List[Dict]:
        """Convert metric rows to dicts."""
        return [
            {
                "id": r[0], "category": r[1], "metric_name": r[2],
                "value": r[3], "unit": r[4], "timestamp": r[5],
                "context": r[6], "trend": r[7]
            }
            for r in rows
        ]
    
    def _rows_to_errors(self, rows: List) -> List[Dict]:
        """Convert error rows to dicts."""
        return [
            {
                "id": r[0], "error_type": r[1], "description": r[2],
                "severity": r[3], "context": r[4], "timestamp": r[5],
                "frequency": r[6], "resolved": r[7],
                "resolution": r[8], "learnings": json.loads(r[9])
            }
            for r in rows
        ]
    
    def _rows_to_modifications(self, rows: List) -> List[Dict]:
        """Convert modification rows to dicts."""
        return [
            {
                "id": r[0], "category": r[1], "title": r[2],
                "description": r[3], "rationale": r[4],
                "expected_improvement": r[5], "risk_level": r[6],
                "implementation_steps": json.loads(r[7]),
                "status": r[8], "created_at": r[9],
                "expires_at": r[10], "approved_by": r[11],
                "implemented_at": r[12], "user_feedback": r[13],
                "effectiveness_score": r[14]
            }
            for r in rows
        ]
    
    def _rows_to_insights(self, rows: List) -> List[Dict]:
        """Convert insight rows to dicts."""
        return [
            {
                "id": r[0], "category": r[1], "insight": r[2],
                "evidence": json.loads(r[3]), "confidence": r[4],
                "recommendations": json.loads(r[5]), "created_at": r[6],
                "useful_count": r[7], "applied": r[8]
            }
            for r in rows
        ]


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_reflection_engine(storage_dir: Path = None) -> SelfReflectionEngine:
    """Create a new reflection engine instance."""
    if storage_dir is None:
        storage_dir = ReflectionConfig.STORAGE_DIR
    return SelfReflectionEngine(storage_dir)


if __name__ == "__main__":
    print("LEO 2.0 - Self-Reflection Test")
    print("=" * 50)
    
    engine = create_reflection_engine()
    
    # Record some metrics
    print("\n[1] Recording performance metrics...")
    engine.record_metric("latency", "response_time", 450, "ms", "general query")
    engine.record_metric("latency", "response_time", 520, "ms", "complex query")
    engine.record_metric("accuracy", "correct_responses", 0.92, "ratio", "user feedback")
    print("   Recorded 3 metrics")
    
    # Record an error
    print("\n[2] Recording an error...")
    error_id = engine.record_error(
        "timeout", "Request timeout", "medium", "web search"
    )
    print(f"   Recorded error: {error_id}")
    
    # Analyze performance
    print("\n[3] Analyzing performance...")
    analysis = engine.analyze_performance()
    print(f"   Status: {analysis['status']}")
    print(f"   Metrics analyzed: {analysis.get('total_metrics', 0)}")
    
    # Analyze errors
    print("\n[4] Analyzing errors...")
    error_analysis = engine.analyze_errors()
    print(f"   Total errors: {error_analysis['total_errors']}")
    
    # Get stats
    print("\n[5] Statistics:")
    stats = engine.get_stats()
    print(f"   Total metrics: {stats['metrics_recorded']}")
    print(f"   Open errors: {stats['open_errors']}")
    
    print("\n" + "=" * 50)
    print("Test complete!")
