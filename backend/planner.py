# planner.py - PlannerEngine for ClawForge

"""
Transforms user requests into a structured execution plan.
Follows the mandatory 7-step Primary Execution Loop.
"""

import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Generator
from enum import Enum

# ============================================================================
# TASK STATUS
# ============================================================================

class TaskStatus(Enum):
    """Task status enumeration."""
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SECURITY_BLOCKED = "SECURITY_BLOCKED"

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class SubTask:
    """Represents a single subtask in a task plan."""
    id: str
    description: str
    tool_required: Optional[str] = None
    requires_permission: bool = False
    estimated_risk: int = 0
    status: str = "PENDING"
    result: Optional[str] = None

@dataclass
class TaskPlan:
    """Represents a complete task plan."""
    task_id: str
    goal: str
    user_request: str
    subtasks: List[SubTask]
    permissions_needed: List[str]
    estimated_total_risk: int
    created_at: str
    status: TaskStatus
    progress: str
    files_created: List[str]
    pending_approvals: List[str]

# ============================================================================
# TOOL RISK MAP
# ============================================================================

TOOL_RISK_MAP = {
    "read_file": 1,
    "write_file": 1,
    "create_folder": 0,
    "move_file": 1,
    "delete_file": 3,
    "run_command": 4,
    "list_processes": 1,
    "check_disk_usage": 1,
    "take_screenshot": 2,
    "click": 7,
    "type_text": 7,
    "scroll": 7,
    "open_app": 5,
    "switch_window": 3,
    "copy_paste": 3,
    "open_url": 3,
    "extract_text": 2,
    "download_file": 5,
    "run_python": 4,
    "run_node": 4,
    "lint_code": 1,
    "create_docx": 1,
    "create_pdf": 1,
    "create_excel": 1,
    "update_excel": 1,
    "analyze_excel": 1,
}

# Tools that require permission
PERMISSION_REQUIRED_TOOLS = [
    "run_command",
    "download_file",
    "run_python",
    "run_node",
    "take_screenshot",
    "click",
    "type_text",
    "scroll",
    "open_app",
    "switch_window",
    "open_url",
    "delete_file",
]

# ============================================================================
# TASK CATEGORIES
# ============================================================================

TASK_CATEGORIES = {
    "content_writing": {
        "keywords": ["blog", "seo", "article", "linkedin", "newsletter", "write", "content"],
        "default_tools": ["read_file", "write_file"],
        "risk_level": 1
    },
    "code_generation": {
        "keywords": ["code", "script", "python", "javascript", "app", "website", "api", "program"],
        "default_tools": ["read_file", "write_file", "run_python", "lint_code"],
        "risk_level": 3
    },
    "excel": {
        "keywords": ["excel", "spreadsheet", "formula", "csv", "pivot", "sheet"],
        "default_tools": ["read_file", "write_file", "analyze_excel", "update_excel"],
        "risk_level": 1
    },
    "document": {
        "keywords": ["pdf", "docx", "document", "report", "resume", "proposal"],
        "default_tools": ["read_file", "write_file", "create_docx", "create_pdf"],
        "risk_level": 1
    },
    "terminal": {
        "keywords": ["terminal", "command", "run", "execute", "install", "bash", "shell"],
        "default_tools": ["run_command"],
        "risk_level": 4
    },
    "ui_automation": {
        "keywords": ["click", "open", "browser", "screenshot", "control", "mouse", "keyboard"],
        "default_tools": ["take_screenshot", "click", "type_text", "open_app"],
        "risk_level": 7
    },
    "debugging": {
        "keywords": ["debug", "fix", "error", "bug", "issue", "problem", "troubleshoot"],
        "default_tools": ["read_file", "write_file", "run_python", "lint_code"],
        "risk_level": 3
    },
    "project_generation": {
        "keywords": ["build", "create", "generate", "make", "setup", "initialize"],
        "default_tools": ["create_folder", "write_file"],
        "risk_level": 2
    }
}

# ============================================================================
# PLANNER ENGINE CLASS
# ============================================================================

class PlannerEngine:
    """
    Transforms user requests into structured execution plans.
    Follows the mandatory 7-step Primary Execution Loop.
    """
    
    # Counter for subtask IDs
    _subtask_counter = 0
    
    # ============================================================================
    # TASK ID GENERATION
    # ============================================================================
    
    @classmethod
    def generate_task_id(cls) -> str:
        """
        Generates a unique task ID.
        Format: task_YYYYMMDD_HHMMSS_xxxxxx
        
        Returns:
            Unique task identifier string
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        random_suffix = str(cls._subtask_counter).zfill(6)
        cls._subtask_counter += 1
        return f"task_{timestamp}_{random_suffix}"
    
    # ============================================================================
    # TASK INTERPRETATION
    # ============================================================================
    
    @classmethod
    def interpret_task(cls, user_request: str) -> Dict[str, Any]:
        """
        STEP 1: Interpret the task.
        Analyzes intent, detects requirements, identifies hidden sub-needs.
        
        Args:
            user_request: The raw user request
        
        Returns:
            Dictionary with interpretation results
        """
        request_lower = user_request.lower()
        
        # Detect category
        detected_category = "general"
        category_score = 0
        
        for category, config in TASK_CATEGORIES.items():
            score = sum(1 for keyword in config["keywords"] if keyword in request_lower)
            if score > category_score:
                category_score = score
                detected_category = category
        
        # Detect requirements
        requires_network = any(word in request_lower for word in [
            "fetch", "download", "browse", "search", "url", "http", "website"
        ])
        
        requires_ui = any(word in request_lower for word in [
            "click", "open", "screenshot", "browser", "window"
        ])
        
        requires_terminal = any(word in request_lower for word in [
            "run", "execute", "command", "terminal", "bash", "shell"
        ])
        
        requires_file_creation = any(word in request_lower for word in [
            "create", "write", "generate", "make", "build"
        ])
        
        # Detect hidden sub-needs
        hidden_needs = []
        
        if detected_category == "content_writing":
            if "seo" in request_lower:
                hidden_needs.append("SEO optimization required")
            if "linkedin" in request_lower or "blog" in request_lower:
                hidden_needs.append("Format for social media/platform")
        
        if detected_category == "code_generation":
            if "test" in request_lower:
                hidden_needs.append("Include unit tests")
            if "api" in request_lower:
                hidden_needs.append("Include API documentation")
        
        return {
            "original_request": user_request,
            "detected_category": detected_category,
            "requires_network": requires_network,
            "requires_ui": requires_ui,
            "requires_terminal": requires_terminal,
            "requires_file_creation": requires_file_creation,
            "hidden_needs": hidden_needs,
            "interpreted_at": datetime.utcnow().isoformat()
        }
    
    # ============================================================================
    # PLAN BUILDING
    # ============================================================================
    
    @classmethod
    def build_plan(
        cls,
        user_request: str,
        manual_subtasks: Optional[List[Dict]] = None
    ) -> TaskPlan:
        """
        STEP 2: Generate a structured execution plan.
        
        Args:
            user_request: The user's task request
            manual_subtasks: Optional list of manually specified subtasks
        
        Returns:
            TaskPlan object with subtasks, risk estimates, and permissions
        """
        # Interpret task
        interpretation = cls.interpret_task(user_request)
        category = interpretation["detected_category"]
        
        # Generate subtasks
        if manual_subtasks:
            subtasks = cls._manual_subtasks(manual_subtasks, category)
        else:
            subtasks = cls._auto_subtasks(category, user_request)
        
        # Calculate permissions needed
        permissions_needed = []
        for subtask in subtasks:
            if subtask.requires_permission:
                if subtask.tool_required and subtask.tool_required not in permissions_needed:
                    permissions_needed.append(subtask.tool_required)
        
        # Calculate total risk
        total_risk = sum(subtask.estimated_risk for subtask in subtasks)
        
        # Generate task ID
        task_id = cls.generate_task_id()
        
        # Create task plan
        plan = TaskPlan(
            task_id=task_id,
            goal=user_request,
            user_request=user_request,
            subtasks=subtasks,
            permissions_needed=permissions_needed,
            estimated_total_risk=total_risk,
            created_at=datetime.utcnow().isoformat(),
            status=TaskStatus.PLANNED,
            progress="0%",
            files_created=[],
            pending_approvals=permissions_needed.copy()
        )
        
        return plan
    
    @classmethod
    def _auto_subtasks(cls, category: str, request: str) -> List[SubTask]:
        """
        Generates default subtasks based on detected task category.
        
        Args:
            category: Detected task category
            request: Original user request
        
        Returns:
            List of SubTask objects
        """
        subtasks = []
        subtask_counter = 1
        
        # Category-specific subtask templates
        category_templates = {
            "content_writing": [
                ("Analyze topic and requirements", None, False, 1),
                ("Research and gather information", "read_file", False, 2),
                ("Create outline and structure", None, False, 1),
                ("Write first draft", "write_file", False, 2),
                ("Review and edit content", None, False, 1),
                ("Finalize and save output", "write_file", False, 1),
            ],
            "code_generation": [
                ("Analyze requirements and specifications", None, False, 1),
                ("Design solution architecture", None, False, 2),
                ("Write code implementation", "write_file", False, 3),
                ("Add error handling and validation", None, False, 2),
                ("Test with sample inputs", "run_python", True, 2),
                ("Review and optimize code", "lint_code", False, 1),
            ],
            "excel": [
                ("Analyze data requirements", None, False, 1),
                ("Create spreadsheet structure", "create_excel", False, 1),
                ("Add formulas and calculations", "update_excel", False, 2),
                ("Format for readability", None, False, 1),
                ("Validate results", "analyze_excel", False, 1),
            ],
            "document": [
                ("Analyze document requirements", None, False, 1),
                ("Create document structure", "create_docx", False, 1),
                ("Add content and formatting", "write_file", False, 2),
                ("Review and edit", None, False, 1),
                ("Export to final format", "create_pdf", False, 1),
            ],
            "terminal": [
                ("Analyze command requirements", None, False, 1),
                ("Build command sequence", None, False, 2),
                ("Execute commands safely", "run_command", True, 4),
                ("Verify execution results", None, False, 1),
            ],
            "ui_automation": [
                ("Analyze automation requirements", None, False, 1),
                ("Identify target applications", None, False, 1),
                ("Take current state screenshot", "take_screenshot", True, 2),
                ("Perform UI actions", "click", True, 7),
                ("Verify results", None, False, 1),
            ],
            "debugging": [
                ("Analyze error or issue", None, False, 1),
                ("Review relevant code files", "read_file", False, 2),
                ("Identify root cause", None, False, 2),
                ("Implement fix", "write_file", False, 3),
                ("Test fix", "run_python", True, 2),
                ("Verify all tests pass", None, False, 1),
            ],
            "project_generation": [
                ("Analyze project requirements", None, False, 1),
                ("Create project structure", "create_folder", False, 1),
                ("Generate core files", "write_file", False, 2),
                ("Add configuration files", "write_file", False, 1),
                ("Initialize documentation", None, False, 1),
            ],
            "general": [
                ("Analyze task requirements", None, False, 1),
                ("Plan execution steps", None, False, 1),
                ("Execute planned steps", None, False, 2),
                ("Review and validate results", None, False, 1),
                ("Finalize output", None, False, 1),
            ]
        }
        
        # Get template for category or use general
        template = category_templates.get(category, category_templates["general"])
        
        # Generate subtasks from template
        for description, tool, permission, risk in template:
            subtask = SubTask(
                id=f"subtask_{subtask_counter:03d}",
                description=description,
                tool_required=tool,
                requires_permission=permission,
                estimated_risk=risk,
                status="PENDING",
                result=None
            )
            subtasks.append(subtask)
            subtask_counter += 1
        
        return subtasks
    
    @classmethod
    def _manual_subtasks(
        cls,
        manual_subtasks: List[Dict],
        category: str
    ) -> List[SubTask]:
        """
        Converts manual subtask definitions to SubTask objects.
        
        Args:
            manual_subtasks: List of subtask dictionaries
            category: Task category
        
        Returns:
            List of SubTask objects
        """
        subtasks = []
        subtask_counter = 1
        
        for subtask_def in manual_subtasks:
            tool = subtask_def.get("tool")
            tool_risk = TOOL_RISK_MAP.get(tool, 1) if tool else 1
            requires_permission = tool in PERMISSION_REQUIRED_TOOLS if tool else False
            
            subtask = SubTask(
                id=f"subtask_{subtask_counter:03d}",
                description=subtask_def.get("description", "No description"),
                tool_required=tool,
                requires_permission=requires_permission,
                estimated_risk=subtask_def.get("risk", tool_risk),
                status="PENDING",
                result=None
            )
            subtasks.append(subtask)
            subtask_counter += 1
        
        return subtasks
    
    # ============================================================================
    # PLAN CONVERSION
    # ============================================================================
    
    @classmethod
    def plan_to_markdown(cls, plan: TaskPlan) -> str:
        """
        Converts a TaskPlan to a human-readable Markdown plan file.
        
        Args:
            plan: TaskPlan object
        
        Returns:
            Markdown formatted string
        """
        md_lines = [
            f"# Task Plan: {plan.task_id}",
            "",
            f"**Goal:** {plan.goal}",
            "",
            f"**Category:** {cls.interpret_task(plan.user_request)['detected_category']}",
            f"**Status:** {plan.status.value}",
            f"**Created:** {plan.created_at}",
            f"**Estimated Risk:** {plan.estimated_total_risk}",
            "",
            "---",
            "",
            "## Subtasks",
            "",
        ]
        
        for subtask in plan.subtasks:
            status_icon = "⏳" if subtask.status == "PENDING" else "🔄" if subtask.status == "RUNNING" else "✅"
            permission_icon = "🔐" if subtask.requires_permission else "🔓"
            risk_bar = "⚠️" * min(subtask.estimated_risk, 5)
            
            md_lines.append(f"### {status_icon} {permission_icon} {subtask.id}: {subtask.description}")
            md_lines.append(f"- **Tool:** {subtask.tool_required or 'None'}")
            md_lines.append(f"- **Risk:** {risk_bar} ({subtask.estimated_risk})")
            md_lines.append(f"- **Status:** {subtask.status}")
            if subtask.result:
                md_lines.append(f"- **Result:** {subtask.result}")
            md_lines.append("")
        
        # Permissions section
        if plan.permissions_needed:
            md_lines.extend([
                "## Permissions Required",
                "",
            ])
            for permission in plan.permissions_needed:
                md_lines.append(f"- [ ] {permission}")
            md_lines.append("")
        
        # Files section
        if plan.files_created:
            md_lines.extend([
                "## Files Created",
                "",
            ])
            for file_path in plan.files_created:
                md_lines.append(f"- {file_path}")
            md_lines.append("")
        
        md_lines.extend([
            "---",
            "",
            f"*Plan generated at {plan.created_at}*",
        ])
        
        return "\n".join(md_lines)
    
    @classmethod
    def plan_to_dict(cls, plan: TaskPlan) -> Dict[str, Any]:
        """
        Converts a TaskPlan to a dictionary.
        
        Args:
            plan: TaskPlan object
        
        Returns:
            Dictionary representation
        """
        return {
            "task_id": plan.task_id,
            "goal": plan.goal,
            "user_request": plan.user_request,
            "category": cls.interpret_task(plan.user_request)['detected_category'],
            "status": plan.status.value,
            "progress": plan.progress,
            "created_at": plan.created_at,
            "estimated_total_risk": plan.estimated_total_risk,
            "permissions_needed": plan.permissions_needed,
            "pending_approvals": plan.pending_approvals,
            "files_created": plan.files_created,
            "subtasks": [
                {
                    "id": subtask.id,
                    "description": subtask.description,
                    "tool_required": subtask.tool_required,
                    "requires_permission": subtask.requires_permission,
                    "estimated_risk": subtask.estimated_risk,
                    "status": subtask.status,
                    "result": subtask.result
                }
                for subtask in plan.subtasks
            ]
        }
    
    # ============================================================================
    # PLAN EXECUTION HELPERS
    # ============================================================================
    
    @classmethod
    def get_next_subtask(cls, plan: TaskPlan) -> Optional[SubTask]:
        """
        Gets the next pending subtask from a plan.
        
        Args:
            plan: TaskPlan object
        
        Returns:
            Next SubTask or None if all complete
        """
        for subtask in plan.subtasks:
            if subtask.status == "PENDING":
                return subtask
        return None
    
    @classmethod
    def update_subtask_status(
        cls,
        plan: TaskPlan,
        subtask_id: str,
        status: str,
        result: Optional[str] = None
    ) -> bool:
        """
        Updates the status of a subtask.
        
        Args:
            plan: TaskPlan object
            subtask_id: ID of subtask to update
            status: New status
            result: Optional result string
        
        Returns:
            True if updated, False if not found
        """
        for subtask in plan.subtasks:
            if subtask.id == subtask_id:
                subtask.status = status
                if result:
                    subtask.result = result
                return True
        return False
    
    @classmethod
    def calculate_progress(cls, plan: TaskPlan) -> str:
        """
        Calculates and returns progress percentage.
        
        Args:
            plan: TaskPlan object
        
        Returns:
            Progress percentage string (e.g., "33%")
        """
        if not plan.subtasks:
            return "0%"
        
        completed = sum(1 for subtask in plan.subtasks if subtask.status == "COMPLETED")
        total = len(plan.subtasks)
        percentage = (completed / total) * 100
        
        return f"{percentage:.0f}%"
    
    @classmethod
    def are_all_subtasks_complete(cls, plan: TaskPlan) -> bool:
        """
        Checks if all subtasks are complete.
        
        Args:
            plan: TaskPlan object
        
        Returns:
            True if all complete, False otherwise
        """
        return all(
            subtask.status == "COMPLETED" or subtask.status == "SKIPPED"
            for subtask in plan.subtasks
        )

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def interpret_task(user_request: str) -> Dict[str, Any]:
    """Convenience function for PlannerEngine.interpret_task()"""
    return PlannerEngine.interpret_task(user_request)

def build_plan(user_request: str, manual_subtasks: Optional[List[Dict]] = None) -> TaskPlan:
    """Convenience function for PlannerEngine.build_plan()"""
    return PlannerEngine.build_plan(user_request, manual_subtasks)

def generate_task_id() -> str:
    """Convenience function for PlannerEngine.generate_task_id()"""
    return PlannerEngine.generate_task_id()

def plan_to_markdown(plan: TaskPlan) -> str:
    """Convenience function for PlannerEngine.plan_to_markdown()"""
    return PlannerEngine.plan_to_markdown(plan)

if __name__ == "__main__":
    # Test planner
    print("🐾 ClawForge PlannerEngine - Test")
    print("=" * 50)
    
    # Test task interpretation
    test_request = "Write a blog about AI agents for beginners"
    interpretation = PlannerEngine.interpret_task(test_request)
    print(f"\n📝 Task: {test_request}")
    print(f"   Category: {interpretation['detected_category']}")
    print(f"   Hidden needs: {interpretation['hidden_needs']}")
    
    # Test plan building
    plan = PlannerEngine.build_plan(test_request)
    print(f"\n📋 Plan created: {plan.task_id}")
    print(f"   Subtasks: {len(plan.subtasks)}")
    print(f"   Estimated risk: {plan.estimated_total_risk}")
    print(f"   Permissions needed: {plan.permissions_needed}")
    
    # Test markdown conversion
    md = PlannerEngine.plan_to_markdown(plan)
    print(f"\n📄 Markdown preview:")
    print(md[:500] + "..." if len(md) > 500 else md)
