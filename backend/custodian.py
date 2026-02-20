# custodian.py - Leo 2.0 Privacy & Security Custodian

"""
Leo 2.0 Custodian Mode - Complete Privacy & Security System

Purpose: Act as laptop custodian, protect from external threats,
ensure zero personal data collection, require permission for all actions.

Features:
- External request monitoring
- Personal data detection & blocking
- Threat classification
- Permission gateway for all actions
- Complete audit logging
- User data rights (export/delete)
"""

import os
import json
import hashlib
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import re

# ============================================================================
# CONFIGURATION
# ============================================================================

class CustodianConfig:
    """Custodian mode configuration."""
    
    # Storage
    STORAGE_DIR = Path.home() / ".leo2" / "custodian"
    DB_FILE = STORAGE_DIR / "custodian.db"
    AUDIT_LOG = STORAGE_DIR / "audit.log"
    
    # Privacy settings
    BLOCK_PERSONAL_DATA = True
    BLOCK_EXTERNAL_REQUESTS = False  # User must enable
    REQUIRE_PERMISSION_FOR_EXTERNAL = True
    
    # Personal data patterns to detect and block
    PERSONAL_DATA_PATTERNS = [
        # Email patterns
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        # Phone patterns
        r'\+?[0-9]{10,15}',
        r'\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
        # Credit card patterns
        r'\b[0-9]{4}[-.\s]?[0-9]{4}[-.\s]?[0-9]{4}[-.\s]?[0-9]{4}\b',
        # SSN patterns
        r'\b[0-9]{3}[-.\s]?[0-9]{2}[-.\s]?[0-9]{4}\b',
        # Password patterns
        r'(password|passwd|pwd)\s*[:=]\s*\S+',
        r'\S*(?:password|passwd|pwd)\s*=\s*\S+',
        # API keys
        r'(api[_-]?key|apikey|secret|token)\s*[:=]\s*\S+',
        r'SK-[a-zA-Z0-9]{20,}',
        # IP addresses (internal)
        r'192\.168\.\d{1,3}\.\d{1,3}',
        r'10\.\d{1,3}\.\d{1,3}\.\d{1,3}',
        # File paths with sensitive names
        r'/etc/passwd',
        r'C:\\Users\\[^\\]+\\Documents\\.*',
        r'/home/[^/]+/.ssh/',
    ]
    
    # Threat levels
    THREAT_LEVELS = {
        "critical": 100,
        "high": 75,
        "medium": 50,
        "low": 25,
        "none": 0
    }
    
    # Allowed external domains (safe)
    SAFE_DOMAINS = [
        "github.com",
        "stackoverflow.com",
        "docs.python.org",
        "pypi.org",
        "npmjs.com",
        "developer.mozilla.org",
    ]
    
    # Blocked categories
    BLOCKED_CATEGORIES = [
        "adult",
        "malware",
        "phishing",
        "tracking",
    ]


# ============================================================================
# DATA MODELS
# ============================================================================

class ThreatLevel(Enum):
    """Threat classification levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequestType(Enum):
    """Types of external requests."""
    WEB_SEARCH = "web_search"
    WEB_FETCH = "web_fetch"
    API_CALL = "api_call"
    FILE_DOWNLOAD = "file_download"
    CODE_EXECUTION = "code_execution"
    COMMAND_EXECUTION = "command_execution"


@dataclass
class SecurityEvent:
    """A security event for audit logging."""
    id: str
    timestamp: str
    event_type: str
    request_type: str
    details: str
    threat_level: str
    action_taken: str
    permission_granted: bool
    user_approved: bool
    metadata: Dict = field(default_factory=dict)


@dataclass
class PermissionRequest:
    """A pending permission request."""
    id: str
    timestamp: str
    request_type: str
    description: str
    risk_level: str
    data_preview: str
    impact: str
    expires_minutes: int
    status: str  # pending, approved, denied, expired


# ============================================================================
# CUSTODIAN ENGINE
# ============================================================================

class CustodianEngine:
    """
    Leo 2.0 Custodian - Privacy & Security Engine
    
    Core responsibilities:
    1. Monitor all external requests
    2. Detect and block personal data
    3. Classify threats
    4. Require permissions for sensitive actions
    5. Log all security events
    6. Protect user data
    """
    
    def __init__(self, storage_dir: Path = CustodianConfig.STORAGE_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_file = self.storage_dir / "custodian.db"
        self._init_database()
        
        # State
        self.block_external = CustodianConfig.BLOCK_EXTERNAL_REQUESTS
        self.protection_active = True
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "personal_data_detected": 0,
            "threats_blocked": 0,
            "permissions_requested": 0,
            "permissions_granted": 0,
            "permissions_denied": 0
        }
        
        # Permission cache (for approved requests)
        self.permission_cache = {}
        
        # Event history
        self.event_history = []
    
    # =========================================================================
    # DATABASE SETUP
    # =========================================================================
    
    def _init_database(self):
        """Initialize the custodian database."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        # Security events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                event_type TEXT,
                request_type TEXT,
                details TEXT,
                threat_level TEXT,
                action_taken TEXT,
                permission_granted INTEGER,
                user_approved INTEGER,
                metadata TEXT
            )
        ''')
        
        # Permission requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permission_requests (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                request_type TEXT,
                description TEXT,
                risk_level TEXT,
                data_preview TEXT,
                impact TEXT,
                expires_minutes INTEGER,
                status TEXT,
                response TEXT,
                responded_at TEXT
            )
        ''')
        
        # Permission cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permission_cache (
                id TEXT PRIMARY KEY,
                request_type TEXT,
                description TEXT,
                created_at TEXT,
                expires_at TEXT,
                usage_count INTEGER DEFAULT 0,
                max_uses INTEGER DEFAULT 1
            )
        ''')
        
        # Personal data patterns detected
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personal_data_log (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                pattern_type TEXT,
                matched_text TEXT,
                action_taken TEXT,
                request_context TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON security_events(timestamp)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_threat ON security_events(threat_level)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status ON permission_requests(status)
        ''')
        
        conn.commit()
        conn.close()
    
    # =========================================================================
    # PERSONAL DATA DETECTION
    # =========================================================================
    
    def detect_personal_data(self, text: str) -> List[Dict]:
        """
        Scan text for personal data patterns.
        Returns list of detected items.
        """
        detected = []
        
        for pattern in CustodianConfig.PERSONAL_DATA_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                matched_text = match.group()
                
                # Determine pattern type
                if '@' in matched_text:
                    pattern_type = "email"
                elif 'password' in matched_text.lower() or 'passwd' in matched_text.lower():
                    pattern_type = "password"
                elif 'api' in matched_text.lower() or 'secret' in matched_text.lower():
                    pattern_type = "api_key"
                elif re.match(r'\d{3}[-.\s]?\d{2}[-.\s]?\d{4}', matched_text):
                    pattern_type = "ssn"
                elif re.match(r'\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}', matched_text):
                    pattern_type = "credit_card"
                elif '192.168.' in matched_text or '10.' in matched_text:
                    pattern_type = "internal_ip"
                else:
                    pattern_type = "other"
                
                # Hash the matched text for logging (privacy-safe)
                hashed = hashlib.sha256(matched_text.encode()).hexdigest()[:16]
                
                detected.append({
                    "pattern_type": pattern_type,
                    "matched_text_hashed": hashed,
                    "position": match.span(),
                    "action": "block" if CustodianConfig.BLOCK_PERSONAL_DATA else "warn"
                })
        
        return detected
    
    def block_personal_data(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Block personal data from text.
        Returns sanitized text and detection report.
        """
        detected = self.detect_personal_data(text)
        
        sanitized = text
        for item in detected:
            # Replace with placeholder
            placeholder = f"[{item['pattern_type'].upper()}_BLOCKED]"
            start, end = item['position']
            sanitized = sanitized[:start] + placeholder + sanitized[end:]
        
        return sanitized, detected
    
    def log_personal_data_detection(self, detected: List[Dict], context: str = None):
        """Log personal data detection for audit."""
        if not detected:
            return
        
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        for item in detected:
            cursor.execute('''
                INSERT INTO personal_data_log (
                    id, timestamp, pattern_type, matched_text_hashed,
                    action_taken, request_context
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self._generate_id(),
                datetime.utcnow().isoformat(),
                item['pattern_type'],
                item.get('matched_text_hashed', 'unknown'),
                item['action'],
                context[:200] if context else None
            ))
            
            self.stats["personal_data_detected"] += 1
        
        conn.commit()
        conn.close()
    
    # =========================================================================
    # THREAT DETECTION
    # =========================================================================
    
    def classify_threat(self, request_type: str, url: str = None, 
                       content: str = None) -> Tuple[ThreatLevel, str, str]:
        """
        Classify the threat level of a request.
        
        Returns:
            (threat_level, risk_category, reason)
        """
        threat_level = ThreatLevel.NONE
        risk_category = "safe"
        reason = "No threats detected"
        
        # Check URL against blocked categories
        if url:
            url_lower = url.lower()
            
            # Check for malicious patterns
            malicious_patterns = [
                (r'malware', 'malware', 'High'),
                (r'phish', 'phishing', 'Critical'),
                (r'tracker', 'tracking', 'Medium'),
                (r'download.*\.exe', 'executable_download', 'High'),
                (r'download.*\.zip', 'archive_download', 'Low'),
            ]
            
            for pattern, category, level in malicious_patterns:
                if re.search(pattern, url_lower):
                    threat_level = ThreatLevel[level.upper()]
                    risk_category = category
                    reason = f"Detected {category} URL pattern"
                    break
        
        # Check content for malicious patterns
        if content:
            malicious_content = [
                (r'<script.*?>.*?execute.*?</script>', 'xss', 'High'),
                (r'union.*select', 'sql_injection', 'Critical'),
                (r'\.\./', 'path_traversal', 'Medium'),
                (r'\$ \{.*\}', 'command_injection', 'High'),
            ]
            
            for pattern, category, level in malicious_content:
                if re.search(pattern, content, re.IGNORECASE):
                    threat_level = ThreatLevel[level.upper()]
                    risk_category = category
                    reason = f"Detected {category} in content"
                    break
        
        # External requests always have some risk
        if request_type in [RequestType.WEB_FETCH.value, RequestType.FILE_DOWNLOAD.value]:
            if threat_level == ThreatLevel.NONE:
                threat_level = ThreatLevel.LOW
                risk_category = "external_request"
                reason = "External content fetch"
        
        return threat_level, risk_category, reason
    
    def check_url_safety(self, url: str) -> Tuple[bool, str]:
        """Check if URL is in safe list."""
        if not url:
            return True, "No URL provided"
        
        url_lower = url.lower()
        
        # Check safe domains
        for safe_domain in CustodianConfig.SAFE_DOMAINS:
            if safe_domain in url_lower:
                return True, f"Safe domain: {safe_domain}"
        
        # Check for suspicious patterns
        suspicious = [
            (r'bit\.ly', "Shortened URL - potential tracking"),
            (r'tinyurl', "Shortened URL - potential tracking"),
            (r'raw\.githubusercontent', "Raw GitHub - verify source"),
        ]
        
        for pattern, warning in suspicious:
            if re.search(pattern, url_lower):
                return False, warning
        
        return True, "URL passed basic checks"
    
    # =========================================================================
    # PERMISSION SYSTEM
    # =========================================================================
    
    def request_permission(
        self,
        request_type: str,
        description: str,
        risk_level: str,
        data_preview: str = None,
        impact: str = None,
        expires_minutes: int = 30
    ) -> Tuple[bool, str]:
        """
        Request permission for an action.
        
        Returns:
            (permission_granted: bool, request_id: str or reason)
        """
        # Check cache first
        cache_key = f"{request_type}:{description[:50]}"
        if cache_key in self.permission_cache:
            cached = self.permission_cache[cache_key]
            if cached['expires_at'] > datetime.utcnow().isoformat():
                if cached['uses'] < cached['max_uses']:
                    cached['uses'] += 1
                    return True, f"Cached permission: {cached['id']}"
        
        # Create new request
        request_id = self._generate_id()
        now = datetime.utcnow().isoformat()
        expires = (datetime.utcnow() + 
                  datetime.timedelta(minutes=expires_minutes)).isoformat()
        
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO permission_requests (
                id, timestamp, request_type, description,
                risk_level, data_preview, impact,
                expires_minutes, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request_id, now, request_type, description,
            risk_level, data_preview[:300] if data_preview else None,
            impact, expires_minutes, "pending"
        ))
        
        conn.commit()
        conn.close()
        
        self.stats["permissions_requested"] += 1
        
        return False, request_id
    
    def grant_permission(self, request_id: str, response: str = None) -> bool:
        """Grant a permission request."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        cursor.execute('''
            UPDATE permission_requests SET
                status = ?, response = ?, responded_at = ?
            WHERE id = ? AND status = ?
        ''', ("approved", response, now, request_id, "pending"))
        
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if changed:
            self.stats["permissions_granted"] += 1
        
        return changed
    
    def deny_permission(self, request_id: str, response: str = None) -> bool:
        """Deny a permission request."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        cursor.execute('''
            UPDATE permission_requests SET
                status = ?, response = ?, responded_at = ?
            WHERE id = ? AND status = ?
        ''', ("denied", response, now, request_id, "pending"))
        
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if changed:
            self.stats["permissions_denied"] += 1
        
        return changed
    
    def get_pending_permissions(self) -> List[Dict]:
        """Get all pending permission requests."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM permission_requests
            WHERE status = 'pending'
            ORDER BY timestamp DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "timestamp": row[1],
                "request_type": row[2],
                "description": row[3],
                "risk_level": row[4],
                "data_preview": row[5],
                "impact": row[6],
                "expires_minutes": row[7],
                "status": row[8]
            })
        
        return results
    
    def check_permission(self, request_id: str) -> Optional[Dict]:
        """Check permission status."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM permission_requests WHERE id = ?', (request_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "status": row[8],
                "response": row[10]
            }
        return None
    
    # =========================================================================
    # SECURITY AUDIT LOGGING
    # =========================================================================
    
    def log_event(
        self,
        event_type: str,
        request_type: str,
        details: str,
        threat_level: ThreatLevel,
        action_taken: str,
        permission_granted: bool = False,
        user_approved: bool = False,
        metadata: Dict = None
    ):
        """Log a security event."""
        event_id = self._generate_id()
        now = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_events (
                id, timestamp, event_type, request_type, details,
                threat_level, action_taken, permission_granted,
                user_approved, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_id, now, event_type, request_type, details,
            threat_level.value, action_taken,
            1 if permission_granted else 0,
            1 if user_approved else 0,
            json.dumps(metadata or {})
        ))
        
        conn.commit()
        conn.close()
        
        # Update stats
        self.stats["total_requests"] += 1
        if threat_level.value in ["high", "critical"]:
            self.stats["threats_blocked"] += 1
            self.stats["blocked_requests"] += 1
        
        # Add to event history
        self.event_history.append({
            "id": event_id,
            "timestamp": now,
            "type": event_type,
            "threat": threat_level.value,
            "action": action_taken
        })
        
        # Keep only last 100 events in memory
        if len(self.event_history) > 100:
            self.event_history = self.event_history[-100:]
    
    def get_audit_log(self, limit: int = 100, threat_level: str = None) -> List[Dict]:
        """Get audit log entries."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        if threat_level:
            cursor.execute('''
                SELECT * FROM security_events
                WHERE threat_level = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (threat_level, limit))
        else:
            cursor.execute('''
                SELECT * FROM security_events
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "timestamp": row[1],
                "event_type": row[2],
                "request_type": row[3],
                "details": row[4],
                "threat_level": row[5],
                "action_taken": row[6],
                "permission_granted": bool(row[7]),
                "user_approved": bool(row[8]),
                "metadata": json.loads(row[9] or "{}")
            })
        
        return results
    
    # =========================================================================
    # EXTERNAL REQUEST HANDLING
    # =========================================================================
    
    def validate_external_request(
        self,
        request_type: RequestType,
        url: str = None,
        content: str = None,
        purpose: str = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Validate an external request.
        
        Returns:
            (allowed: bool, message: str, request_id: str or None)
        """
        # Check if external requests are blocked
        if self.block_external:
            self.log_event(
                event_type="external_request_blocked",
                request_type=request_type.value,
                details=f"External requests blocked by user setting",
                threat_level=ThreatLevel.MEDIUM,
                action_taken="blocked",
                permission_granted=False
            )
            return False, "External requests are blocked", None
        
        # Check URL safety
        if url:
            safe, message = self.check_url_safety(url)
            if not safe:
                self.log_event(
                    event_type="url_blocked",
                    request_type=request_type.value,
                    details=f"URL safety check failed: {message}",
                    threat_level=ThreatLevel.MEDIUM,
                    action_taken="blocked",
                    permission_granted=False
                )
                return False, f"URL blocked: {message}", None
        
        # Classify threat
        threat_level, category, reason = self.classify_threat(
            request_type.value, url, content
        )
        
        # Check personal data
        if content:
            sanitized, detected = self.block_personal_data(content)
            if detected:
                self.log_personal_data_detection(detected, context=purpose)
        
        # High/critical threats always blocked
        if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            self.log_event(
                event_type="threat_blocked",
                request_type=request_type.value,
                details=f"{category}: {reason}",
                threat_level=threat_level,
                action_taken="blocked",
                permission_granted=False
            )
            return False, f"Threat detected: {reason}", None
        
        # Medium threats require permission
        if threat_level == ThreatLevel.MEDIUM:
            success, request_id = self.request_permission(
                request_type=f"external_{request_type.value}",
                description=f"External {request_type.value}: {purpose or 'No purpose provided'}",
                risk_level="medium",
                data_preview=url or content[:200] if content else None,
                impact="May access external content",
                expires_minutes=15
            )
            
            if not success:
                self.log_event(
                    event_type="permission_requested",
                    request_type=request_type.value,
                    details=f"Permission requested for: {purpose}",
                    threat_level=threat_level,
                    action_taken="pending_permission",
                    permission_granted=False
                )
                return False, "Permission required", request_id
        
        # Low threats allowed with logging
        self.log_event(
            event_type="external_request_allowed",
            request_type=request_type.value,
            details=purpose or "External request",
            threat_level=threat_level,
            action_taken="allowed",
            permission_granted=True,
            user_approved=threat_level in [ThreatLevel.NONE, ThreatLevel.LOW]
        )
        
        return True, "Request allowed", None
    
    # =========================================================================
    # USER DATA RIGHTS
    # =========================================================================
    
    def export_all_data(self) -> Dict:
        """Export all custodian data (user right)."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        # Export events
        cursor.execute('SELECT * FROM security_events ORDER BY timestamp DESC')
        events = cursor.fetchall()
        
        # Export permissions
        cursor.execute('SELECT * FROM permission_requests ORDER BY timestamp DESC')
        permissions = cursor.fetchall()
        
        # Export personal data log
        cursor.execute('SELECT * FROM personal_data_log ORDER BY timestamp DESC')
        personal_data = cursor.fetchall()
        
        conn.close()
        
        return {
            "exported_at": datetime.utcnow().isoformat(),
            "statistics": self.get_stats(),
            "security_events": len(events),
            "permission_requests": len(permissions),
            "personal_data_detections": len(personal_data),
            "data": {
                "events": [
                    {
                        "id": e[0],
                        "timestamp": e[1],
                        "type": e[2],
                        "threat": e[5],
                        "action": e[6]
                    }
                    for e in events
                ],
                "permissions": [
                    {
                        "id": p[0],
                        "type": p[2],
                        "status": p[8]
                    }
                    for p in permissions
                ]
            }
        }
    
    def delete_all_data(self) -> Tuple[bool, str]:
        """
        Delete all custodian data.
        Requires explicit permission.
        """
        request_id = self._generate_id()
        
        # This requires permission - create request
        self.request_permission(
            request_type="delete_all_custodian_data",
            description="DELETE ALL custodian data including audit logs",
            risk_level="critical",
            data_preview=f"Will delete {self.stats['total_requests']} events",
            impact="Complete data loss - irreversible",
            expires_minutes=5
        )
        
        return False, request_id
    
    def confirm_delete_all(self, granted_by: str = "user") -> bool:
        """Actually delete all data after permission."""
        granted = self.grant_permission("delete_all_custodian_data", 
                                      f"Approved by {granted_by}")
        
        if granted:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM security_events')
            cursor.execute('DELETE FROM permission_requests')
            cursor.execute('DELETE FROM personal_data_log')
            cursor.execute('DELETE FROM permission_cache')
            
            conn.commit()
            conn.close()
            
            # Reset stats
            self.stats = {
                "total_requests": 0,
                "blocked_requests": 0,
                "personal_data_detected": 0,
                "threats_blocked": 0,
                "permissions_requested": 0,
                "permissions_granted": 0,
                "permissions_denied": 0
            }
            
            return True
        
        return False
    
    # =========================================================================
    # STATISTICS AND REPORTING
    # =========================================================================
    
    def get_stats(self) -> Dict:
        """Get custodian statistics."""
        return {
            "protection_active": self.protection_active,
            "external_blocked": self.block_external,
            **self.stats,
            "threats_by_level": self._get_threat_distribution()
        }
    
    def _get_threat_distribution(self) -> Dict:
        """Get distribution of threats by level."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT threat_level, COUNT(*) as count
            FROM security_events
            GROUP BY threat_level
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return {row[0]: row[1] for row in rows}
    
    def get_status(self) -> Dict:
        """Get complete custodian status."""
        return {
            "active": self.protection_active,
            "external_blocked": self.block_external,
            "statistics": self.get_stats(),
            "pending_permissions": len(self.get_pending_permissions()),
            "recent_events": self.event_history[-10:],
            "data_rights": {
                "can_export": True,
                "can_delete": True,
                "can_manage_permissions": True
            }
        }
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _generate_id(self) -> str:
        """Generate a unique ID."""
        return hashlib.md5(
            f"{datetime.utcnow().isoformat()}{os.urandom(8)}".encode()
        ).hexdigest()[:12]
