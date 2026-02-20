# multimodal_synthesis.py - Leo's Multi-Modal Synthesis Engine

"""
Multi-Modal Synthesis - Seamless Tool Chaining & Workflow Automation

Features:
- Chain tools together in sequences
- Automated workflows (Watch → Extract → Test → Summarize)
- Seamless data + code + planning synthesis
- Sequential processing (not real-time, but automated)
- Custom workflow templates
"""

import os
import json
import sqlite3
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# CONFIGURATION
# ============================================================================

class MultiModalConfig:
    """Multi-Modal synthesis configuration."""
    
    STORAGE_DIR = Path.home() / ".leo2" / "multimodal"
    DB_FILE = STORAGE_DIR / "workflows.db"
    
    # Workflow settings
    MAX_WORKFLOW_STEPS = 20
    WORKFLOW_TIMEOUT_SECONDS = 300  # 5 minutes
    AUTO_APPROVE_SAFE = True
    
    # Available tool categories
    TOOL_CATEGORIES = [
        "web",        # Search, fetch, browse
        "file",       # Read, write, edit files
        "code",       # Run code, lint, execute
        "shell",      # Terminal commands
        "memory",     # Store, retrieve memories
        "planning",   # Generate plans, tasks
        "analysis",   # Analyze data, text
        "synthesis",  # Combine outputs
    ]


# ============================================================================
# DATA MODELS
# ============================================================================

class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepType(Enum):
    """Types of workflow steps."""
    WEB_SEARCH = "web_search"
    WEB_FETCH = "web_fetch"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_EDIT = "file_edit"
    CODE_EXECUTE = "code_execute"
    CODE_RUN = "code_run"
    SHELL_EXECUTE = "shell_execute"
    MEMORY_STORE = "memory_store"
    MEMORY_RETRIEVE = "memory_retrieve"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    PLANNING = "planning"
    CONDITION = "condition"
    LOOP = "loop"
    TRANSFORM = "transform"
    FORMAT = "format"
    VALIDATE = "validate"


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    id: str
    workflow_id: str
    step_order: int
    step_type: str
    name: str
    description: str
    parameters: Dict
    next_steps: List[str]  # Conditional next steps
    condition: str  # Condition for branching
    retry_count: int
    timeout_seconds: int
    on_failure: str  # continue, abort, retry


@dataclass
class Workflow:
    """A complete workflow."""
    id: str
    name: str
    description: str
    category: str
    steps: List[WorkflowStep]
    status: str
    created_at: str
    updated_at: str
    created_by: str
    tags: List[str]
    is_template: bool
    usage_count: int
    success_rate: float
    avg_duration_seconds: float


@dataclass
class WorkflowExecution:
    """A single execution of a workflow."""
    id: str
    workflow_id: str
    status: str
    started_at: str
    completed_at: str
    duration_seconds: float
    current_step: int
    step_results: List[Dict]
    error_message: str
    output: str


@dataclass
class WorkflowTemplate:
    """A reusable workflow template."""
    id: str
    name: str
    description: str
    steps: List[Dict]
    category: str
    use_cases: List[str]
    prerequisites: List[str]
    estimated_duration: int
    difficulty: str  # beginner, intermediate, advanced


# ============================================================================
# MULTI-MODAL SYNTHESIS ENGINE
# ============================================================================

class MultiModalEngine:
    """
    Leo's Multi-Modal Synthesis Engine
    
    Features:
    - Chain tools in sequences
    - Automated workflows
    - Conditional branching
    - Parallel execution support
    - Template library
    - Seamless synthesis
    """
    
    def __init__(self, storage_dir: Path = MultiModalConfig.STORAGE_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_file = self.storage_dir / "workflows.db"
        self._init_database()
        
        # Tool registry
        self.tool_registry = {}
        
        # Statistics
        self.stats = {
            "total_workflows": 0,
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_templates": 0
        }
        
        # Active executions
        self.active_executions = {}
        
        # Built-in templates
        self._init_templates()
    
    # =========================================================================
    # DATABASE SETUP
    # =========================================================================
    
    def _init_database(self):
        """Initialize the workflow database."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        # Workflows table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT,
                created_by TEXT,
                tags TEXT,
                is_template INTEGER,
                usage_count INTEGER,
                success_rate REAL,
                avg_duration_seconds REAL,
                steps TEXT
            )
        ''')
        
        # Workflow steps table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_steps (
                id TEXT PRIMARY KEY,
                workflow_id TEXT,
                step_order INTEGER,
                step_type TEXT,
                name TEXT,
                description TEXT,
                parameters TEXT,
                next_steps TEXT,
                condition TEXT,
                retry_count INTEGER,
                timeout_seconds INTEGER,
                on_failure TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id)
            )
        ''')
        
        # Executions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS executions (
                id TEXT PRIMARY KEY,
                workflow_id TEXT,
                status TEXT,
                started_at TEXT,
                completed_at TEXT,
                duration_seconds REAL,
                current_step INTEGER,
                step_results TEXT,
                error_message TEXT,
                output TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id)
            )
        ''')
        
        # Templates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                steps TEXT,
                category TEXT,
                use_cases TEXT,
                prerequisites TEXT,
                estimated_duration INTEGER,
                difficulty TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_workflow_status ON workflows(status)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_execution_workflow ON executions(workflow_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_template_category ON templates(category)
        ''')
        
        conn.commit()
        conn.close()
    
    def _init_templates(self):
        """Initialize built-in workflow templates."""
        templates = [
            {
                "name": "Research & Summarize",
                "description": "Search web, extract info, summarize findings",
                "category": "research",
                "use_cases": ["Learn a topic", "Competitive analysis", "Market research"],
                "prerequisites": [],
                "estimated_duration": 60,
                "difficulty": "beginner",
                "steps": [
                    {"type": "web_search", "name": "Search", "parameters": {"query": "${input}"}},
                    {"type": "analysis", "name": "Extract", "parameters": {"key_points": 5}},
                    {"type": "synthesis", "name": "Summarize", "parameters": {"format": "brief"}}
                ]
            },
            {
                "name": "Code & Test",
                "description": "Write code, run tests, fix errors",
                "category": "coding",
                "use_cases": ["Implement feature", "Fix bug", "Write tests"],
                "prerequisites": ["Requirements defined"],
                "estimated_duration": 120,
                "difficulty": "intermediate",
                "steps": [
                    {"type": "code_write", "name": "Write Code", "parameters": {"language": "${language}"}},
                    {"type": "code_run", "name": "Run Tests", "parameters": {"test_command": "python ${file}"}},
                    {"type": "condition", "name": "Check Result", "parameters": {"if_failed": "fix_errors"}},
                    {"type": "code_edit", "name": "Fix Errors", "parameters": {}}
                ]
            },
            {
                "name": "Learn & Remember",
                "description": "Research topic, extract concepts, store in memory",
                "category": "learning",
                "use_cases": ["Learn new skill", "Study topic", "Build knowledge"],
                "prerequisites": [],
                "estimated_duration": 45,
                "difficulty": "beginner",
                "steps": [
                    {"type": "web_fetch", "name": "Get Info", "parameters": {"url": "${url}"}},
                    {"type": "analysis", "name": "Extract Concepts", "parameters": {"concepts": 5}},
                    {"type": "memory_store", "name": "Remember", "parameters": {"category": "knowledge"}}
                ]
            },
            {
                "name": "Plan & Execute",
                "description": "Generate plan, create tasks, execute step by step",
                "category": "planning",
                "use_cases": ["Project planning", "Task breakdown", "Goal setting"],
                "prerequisites": ["Goal defined"],
                "estimated_duration": 30,
                "difficulty": "beginner",
                "steps": [
                    {"type": "planning", "name": "Create Plan", "parameters": {"goal": "${goal}"}},
                    {"type": "loop", "name": "Execute Tasks", "parameters": {"task_list": "${tasks}"}}
                ]
            },
            {
                "name": "Analyze & Report",
                "description": "Analyze data, generate insights, create report",
                "category": "analysis",
                "use_cases": ["Data analysis", "Performance review", "Research report"],
                "prerequisites": ["Data available"],
                "estimated_duration": 90,
                "difficulty": "intermediate",
                "steps": [
                    {"type": "file_read", "name": "Load Data", "parameters": {"path": "${data_file}"}},
                    {"type": "analysis", "name": "Analyze", "parameters": {"metrics": "${metrics}"}},
                    {"type": "synthesis", "name": "Generate Insights", "parameters": {}},
                    {"type": "file_write", "name": "Create Report", "parameters": {"format": "${format}"}}
                ]
            }
        ]
        
        # Store templates
        for template in templates:
            self.create_template(**template)
    
    # =========================================================================
    # WORKFLOW MANAGEMENT
    # =========================================================================
    
    def create_workflow(
        self,
        name: str,
        description: str,
        category: str,
        steps: List[Dict],
        created_by: str = "system",
        tags: List[str] = None,
        is_template: bool = False
    ) -> str:
        """Create a new workflow."""
        import uuid
        import json
        
        workflow_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        # Create workflow
        cursor.execute('''
            INSERT INTO workflows (
                id, name, description, category, status,
                created_at, updated_at, created_by, tags,
                is_template, usage_count, success_rate,
                avg_duration_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            workflow_id, name, description, category, WorkflowStatus.PENDING.value,
            now, now, created_by, json.dumps(tags or []),
            1 if is_template else 0, 0, 0.0, 0.0
        ))
        
        # Create steps
        for i, step in enumerate(steps):
            step_id = str(uuid.uuid4())[:12]
            cursor.execute('''
                INSERT INTO workflow_steps (
                    id, workflow_id, step_order, step_type, name,
                    description, parameters, next_steps, condition,
                    retry_count, timeout_seconds, on_failure
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                step_id, workflow_id, i + 1,
                step.get("type", "generic"),
                step.get("name", f"Step {i+1}"),
                step.get("description", ""),
                json.dumps(step.get("parameters", {})),
                json.dumps(step.get("next_steps", [])),
                step.get("condition", ""),
                step.get("retry_count", 0),
                step.get("timeout_seconds", 60),
                step.get("on_failure", "abort")
            ))
        
        conn.commit()
        conn.close()
        
        self.stats["total_workflows"] += 1
        
        return workflow_id
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Get a workflow with its steps."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        # Get workflow
        cursor.execute('SELECT * FROM workflows WHERE id = ?', (workflow_id,))
        workflow_row = cursor.fetchone()
        
        if not workflow_row:
            conn.close()
            return None
        
        # Get steps
        cursor.execute('''
            SELECT * FROM workflow_steps
            WHERE workflow_id = ?
            ORDER BY step_order
        ''', (workflow_id,))
        
        step_rows = cursor.fetchall()
        conn.close()
        
        steps = []
        for row in step_rows:
            steps.append({
                "id": row[0],
                "step_order": row[2],
                "step_type": row[3],
                "name": row[4],
                "description": row[5],
                "parameters": json.loads(row[6]),
                "next_steps": json.loads(row[7]),
                "condition": row[8],
                "retry_count": row[9],
                "timeout_seconds": row[10],
                "on_failure": row[11]
            })
        
        return {
            "id": workflow_row[0],
            "name": workflow_row[1],
            "description": workflow_row[2],
            "category": workflow_row[3],
            "status": workflow_row[4],
            "created_at": workflow_row[5],
            "updated_at": workflow_row[6],
            "created_by": workflow_row[7],
            "tags": json.loads(workflow_row[8]),
            "is_template": bool(workflow_row[9]),
            "usage_count": workflow_row[10],
            "success_rate": workflow_row[11],
            "avg_duration_seconds": workflow_row[12],
            "steps": steps
        }
    
    def get_workflows(self, category: str = None, status: str = None) -> List[Dict]:
        """Get workflows by category and/or status."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        sql = "SELECT * FROM workflows WHERE 1=1"
        params = []
        
        if category:
            sql += " AND category = ?"
            params.append(category)
        
        if status:
            sql += " AND status = ?"
            params.append(status)
        
        sql += " ORDER BY created_at DESC"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "category": row[3],
                "status": row[4],
                "created_at": row[5],
                "updated_at": row[6],
                "created_by": row[7],
                "tags": json.loads(row[8]),
                "is_template": bool(row[9]),
                "usage_count": row[10],
                "success_rate": row[11],
                "avg_duration_seconds": row[12]
            })
        
        return results
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM workflow_steps WHERE workflow_id = ?', (workflow_id,))
        cursor.execute('DELETE FROM workflows WHERE id = ?', (workflow_id,))
        
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return changed
    
    # =========================================================================
    # WORKFLOW EXECUTION
    # =========================================================================
    
    def execute_workflow(
        self,
        workflow_id: str,
        inputs: Dict = None
    ) -> str:
        """
        Execute a workflow with given inputs.
        Returns execution_id.
        """
        import uuid
        import json
        
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        execution_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat()
        
        # Create execution record
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO executions (
                id, workflow_id, status, started_at,
                current_step, step_results
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            execution_id, workflow_id, WorkflowStatus.RUNNING.value, now,
            0, json.dumps([])
        ))
        
        conn.commit()
        conn.close()
        
        # Store in active executions
        self.active_executions[execution_id] = {
            "workflow": workflow,
            "inputs": inputs or {},
            "current_step": 0,
            "results": [],
            "started_at": now
        }
        
        # Execute in background
        asyncio.create_task(self._run_workflow(execution_id, workflow, inputs or {}))
        
        return execution_id
    
    async def _run_workflow(self, execution_id: str, workflow: Dict, inputs: Dict):
        """Run a workflow asynchronously."""
        try:
            step_results = []
            
            for i, step in enumerate(workflow["steps"]):
                # Update current step
                conn = sqlite3.connect(str(self.db_file))
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE executions SET current_step = ? WHERE id = ?
                ''', (i + 1, execution_id))
                conn.commit()
                conn.close()
                
                # Execute step (placeholder - would integrate with actual tools)
                result = {
                    "step_id": step["id"],
                    "step_name": step["name"],
                    "step_type": step["step_type"],
                    "status": "completed",
                    "output": f"Executed {step['name']}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                step_results.append(result)
                
                # Store result
                conn = sqlite3.connect(str(self.db_file))
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE executions SET step_results = ? WHERE id = ?
                ''', (json.dumps(step_results), execution_id))
                conn.commit()
                conn.close()
            
            # Mark complete
            completed_at = datetime.utcnow().isoformat()
            duration = (datetime.fromisoformat(completed_at) - 
                       datetime.fromisoformat(self.active_executions[execution_id]["started_at"])).total_seconds()
            
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE executions SET
                    status = ?, completed_at = ?, duration_seconds = ?
                WHERE id = ?
            ''', (WorkflowStatus.COMPLETED.value, completed_at, duration, execution_id))
            conn.commit()
            conn.close()
            
            # Update stats
            self.stats["total_executions"] += 1
            self.stats["successful_executions"] += 1
            
            # Remove from active
            del self.active_executions[execution_id]
            
        except Exception as e:
            # Mark failed
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE executions SET
                    status = ?, error_message = ?, completed_at = ?
                WHERE id = ?
            ''', (WorkflowStatus.FAILED.value, str(e), datetime.utcnow().isoformat(), execution_id))
            conn.commit()
            conn.close()
            
            self.stats["total_executions"] += 1
            self.stats["failed_executions"] += 1
            del self.active_executions[execution_id]
    
    def get_execution(self, execution_id: str) -> Optional[Dict]:
        """Get execution status and results."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM executions WHERE id = ?', (execution_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        conn.close()
        
        return {
            "id": row[0],
            "workflow_id": row[1],
            "status": row[2],
            "started_at": row[3],
            "completed_at": row[4],
            "duration_seconds": row[5],
            "current_step": row[6],
            "step_results": json.loads(row[7]),
            "error_message": row[8],
            "output": row[9]
        }
    
    def get_executions(self, workflow_id: str = None, limit: int = 20) -> List[Dict]:
        """Get recent executions."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        sql = "SELECT * FROM executions"
        params = []
        
        if workflow_id:
            sql += " WHERE workflow_id = ?"
            params.append(workflow_id)
        
        sql += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "workflow_id": row[1],
                "status": row[2],
                "started_at": row[3],
                "completed_at": row[4],
                "duration_seconds": row[5],
                "current_step": row[6],
                "error_message": row[8]
            })
        
        return results
    
    # =========================================================================
    # TEMPLATES
    # =========================================================================
    
    def create_template(
        self,
        name: str,
        description: str,
        steps: List[Dict],
        category: str,
        use_cases: List[str],
        prerequisites: List[str],
        estimated_duration: int,
        difficulty: str
    ) -> str:
        """Create a workflow template."""
        import uuid
        
        template_id = str(uuid.uuid4())[:12]
        
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO templates (
                id, name, description, steps, category,
                use_cases, prerequisites, estimated_duration, difficulty
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            template_id, name, description, json.dumps(steps),
            category, json.dumps(use_cases), json.dumps(prerequisites),
            estimated_duration, difficulty
        ))
        
        conn.commit()
        conn.close()
        
        self.stats["total_templates"] += 1
        
        return template_id
    
    def get_templates(self, category: str = None) -> List[Dict]:
        """Get available templates."""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        if category:
            cursor.execute('SELECT * FROM templates WHERE category = ?', (category,))
        else:
            cursor.execute('SELECT * FROM templates')
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "steps": json.loads(row[3]),
                "category": row[4],
                "use_cases": json.loads(row[5]),
                "prerequisites": json.loads(row[6]),
                "estimated_duration": row[7],
                "difficulty": row[8]
            })
        
        return results
    
    def create_workflow_from_template(self, template_id: str, inputs: Dict = None) -> str:
        """Create a workflow from a template."""
        templates = self.get_templates()
        template = next((t for t in templates if t["id"] == template_id), None)
        
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        return self.create_workflow(
            name=f"From: {template['name']}",
            description=template['description'],
            category=template['category'],
            steps=template['steps'],
            is_template=False
        )
    
    # =========================================================================
    # TOOL REGISTRY
    # =========================================================================
    
    def register_tool(self, tool_name: str, tool_function: Callable, category: str):
        """Register a tool for use in workflows."""
        self.tool_registry[tool_name] = {
            "function": tool_function,
            "category": category,
            "registered_at": datetime.utcnow().isoformat()
        }
    
    def get_available_tools(self) -> Dict:
        """Get all registered tools by category."""
        tools = {}
        for name, info in self.tool_registry.items():
            cat = info["category"]
            if cat not in tools:
                tools[cat] = []
            tools[cat].append(name)
        return tools
    
    # =========================================================================
    # STATISTICS AND REPORTING
    # =========================================================================
    
    def get_stats(self) -> Dict:
        """Get multi-modal engine statistics."""
        return {
            "workflows": {
                "total": self.stats["total_workflows"],
                "active": len(self.active_executions)
            },
            "executions": {
                "total": self.stats["total_executions"],
                "successful": self.stats["successful_executions"],
                "failed": self.stats["failed_executions"],
                "success_rate": (
                    self.stats["successful_executions"] / 
                    max(self.stats["total_executions"], 1)
                )
            },
            "templates": {
                "total": self.stats["total_templates"]
            },
            "tools_registered": len(self.tool_registry)
        }
    
    def get_status(self) -> Dict:
        """Get complete engine status."""
        return {
            "statistics": self.get_stats(),
            "active_executions": len(self.active_executions),
            "available_tools": self.get_available_tools(),
            "templates": self.get_templates(),
            "recent_executions": self.get_executions(limit=10)
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_multimodal_engine(storage_dir: Path = None) -> MultiModalEngine:
    """Create a new multi-modal engine instance."""
    if storage_dir is None:
        storage_dir = MultiModalConfig.STORAGE_DIR
    return MultiModalEngine(storage_dir)


if __name__ == "__main__":
    print("LEO 2.0 - Multi-Modal Synthesis Test")
    print("=" * 50)
    
    engine = create_multimodal_engine()
    
    # Show templates
    print("\n[1] Available Templates:")
    templates = engine.get_templates()
    for t in templates:
        print(f"   - {t['name']} ({t['category']})")
        print(f"     {t['description'][:60]}...")
        print(f"     Difficulty: {t['difficulty']}, Duration: {t['estimated_duration']}s")
    
    # Show stats
    print("\n[2] Statistics:")
    stats = engine.get_stats()
    print(f"   Total workflows: {stats['workflows']['total']}")
    print(f"   Total templates: {stats['templates']['total']}")
    print(f"   Tools registered: {stats['tools_registered']}")
    
    # Create workflow from template
    print("\n[3] Creating workflow from template...")
    if templates:
        workflow_id = engine.create_workflow_from_template(templates[0]['id'])
        print(f"   Created workflow: {workflow_id}")
        
        # Execute workflow
        print("\n[4] Executing workflow...")
        execution_id = engine.execute_workflow(workflow_id, {"input": "test query"})
        print(f"   Execution started: {execution_id}")
    
    print("\n" + "=" * 50)
    print("Test complete!")
