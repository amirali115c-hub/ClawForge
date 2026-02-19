# task_manager.py - TaskManager for ClawForge

"""
Manages the full task lifecycle:
- Multi-task queue
- Pause / Resume / Cancel
- Status tracking (6 statuses)
- Background worker integration
- Task state persistence
- Emergency Kill Switch
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
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
# TASK DATA CLASS
# ============================================================================

@dataclass
class Task:
    """Represents a task in the system."""
    task_id: str
    goal: str
    category: str = "general"
    status: TaskStatus = TaskStatus.PLANNED
    progress: int = 0  # 0-100
    current_step: str = ""
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    risk_score: int = 0
    pending_approvals: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    logs: List[Dict] = field(default_factory=list)
    error: Optional[str] = None
    result: Optional[str] = None
    _paused: bool = False
    _cancelled: bool = False
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
    
    def add_log(self, message: str, level: str = "INFO"):
        """Adds a log entry with timestamp and level."""
        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "level": level
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Returns complete task state as dictionary."""
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "category": self.category,
            "status": self.status.value,
            "progress": self.progress,
            "current_step": self.current_step,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "risk_score": self.risk_score,
            "pending_approvals": self.pending_approvals,
            "files_created": self.files_created,
            "logs_count": len(self.logs),
            "error": self.error,
            "result": self.result,
            "paused": self._paused,
            "cancelled": self._cancelled
        }

# ============================================================================
# TASK MANAGER CLASS
# ============================================================================

class TaskManager:
    """
    Manages the full task lifecycle.
    """
    
    def __init__(self, broadcast_fn: Optional[Callable] = None):
        """
        Initialize task manager.
        
        Args:
            broadcast_fn: Optional WebSocket broadcast hook for real-time updates
        """
        self.tasks: Dict[str, Task] = {}
        self.queue: List[str] = []
        self.broadcast_fn = broadcast_fn
        self._kill_switch_active = False
        
        # Load existing tasks from workspace
        self._load_tasks()
    
    def _broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast event to connected clients."""
        if self.broadcast_fn:
            try:
                self.broadcast_fn({
                    "event": event_type,
                    "data": data
                })
            except Exception:
                pass
    
    def _save_task_state(self, task_id: str):
        """Save task state to disk."""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task_folder = f"./workspace/tasks/{task_id}"
        os.makedirs(task_folder, exist_ok=True)
        
        state_path = os.path.join(task_folder, "state.json")
        with open(state_path, 'w') as f:
            json.dump(task.to_dict(), f, indent=2)
    
    def _load_tasks(self):
        """Load existing tasks from workspace."""
        tasks_folder = "./workspace/tasks"
        if not os.path.exists(tasks_folder):
            return
        
        for task_id in os.listdir(tasks_folder):
            state_path = os.path.join(tasks_folder, task_id, "state.json")
            if os.path.exists(state_path):
                try:
                    with open(state_path, 'r') as f:
                        state = json.load(f)
                    
                    task = Task(
                        task_id=state["task_id"],
                        goal=state["goal"],
                        category=state.get("category", "general"),
                        status=TaskStatus(state["status"]),
                        progress=state.get("progress", 0),
                        current_step=state.get("current_step", ""),
                        created_at=state.get("created_at", ""),
                        started_at=state.get("started_at"),
                        completed_at=state.get("completed_at"),
                        risk_score=state.get("risk_score", 0),
                        pending_approvals=state.get("pending_approvals", []),
                        files_created=state.get("files_created", []),
                        error=state.get("error"),
                        result=state.get("result"),
                        _paused=state.get("paused", False),
                        _cancelled=state.get("cancelled", False)
                    )
                    
                    self.tasks[task_id] = task
                    if task_id not in self.queue:
                        self.queue.append(task_id)
                
                except (json.JSONDecodeError, KeyError, FileNotFoundError):
                    continue
    
    # ============================================================================
    # CREATE TASK
    # ============================================================================
    
    def create_task(self, goal: str, category: str = "general") -> Task:
        """
        Creates a new task and adds it to the queue.
        Creates workspace folder: ./workspace/tasks/{task_id}/
        
        Args:
            goal: Task goal description
            category: Task category
        
        Returns:
            Task object
        """
        # Generate task ID
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        import random
        task_id = f"task_{timestamp}_{random.randint(100000, 999999)}"
        
        # Create task
        task = Task(
            task_id=task_id,
            goal=goal,
            category=category,
            status=TaskStatus.PLANNED,
            progress=0,
            created_at=datetime.utcnow().isoformat()
        )
        
        task.add_log(f"Task created: {goal}", "INFO")
        
        # Store task
        self.tasks[task_id] = task
        self.queue.append(task_id)
        
        # Create workspace folder
        self._create_task_workspace(task_id)
        
        # Save state
        self._save_task_state(task_id)
        
        # Broadcast
        self._broadcast("task_created", task.to_dict())
        
        print(f"[OK] Task created: {task_id}")
        
        return task
    
    def _create_task_workspace(self, task_id: str):
        """Create task workspace folder structure."""
        base_path = f"./workspace/tasks/{task_id}"
        output_path = os.path.join(base_path, "output")
        
        os.makedirs(base_path, exist_ok=True)
        os.makedirs(output_path, exist_ok=True)
        
        # Create initial files
        plan_path = os.path.join(base_path, "plan.md")
        with open(plan_path, 'w') as f:
            f.write(f"# Task: {task_id}\n\n## Goal\n{self.tasks[task_id].goal}\n")
        
        logs_path = os.path.join(base_path, "logs.jsonl")
        with open(logs_path, 'w') as f:
            f.write("")
        
        security_path = os.path.join(base_path, "security_report.json")
        with open(security_path, 'w') as f:
            json.dump({
                "task_id": task_id,
                "start_time": datetime.utcnow().isoformat(),
                "tools_used": [],
                "blocked_commands": [],
                "quarantined_files": [],
                "risk_score_final": 0
            }, f, indent=2)
    
    # ============================================================================
    # STATUS TRANSITIONS
    # ============================================================================
    
    def start_task(self, task_id: str) -> Dict[str, Any]:
        """
        Starts a task (PLANNED -> RUNNING).
        
        Args:
            task_id: Task identifier
        
        Returns:
            Dict with status and task info
        """
        if task_id not in self.tasks:
            return {"status": "error", "error": "Task not found"}
        
        task = self.tasks[task_id]
        
        if task.status == TaskStatus.RUNNING:
            return {"status": "warning", "message": "Task already running", "task": task.to_dict()}
        
        if task.status not in [TaskStatus.PLANNED, TaskStatus.WAITING_APPROVAL]:
            return {"status": "error", "error": f"Cannot start task in {task.status.value} status"}
        
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow().isoformat()
        task.add_log("Task started", "INFO")
        
        # Save and broadcast
        self._save_task_state(task_id)
        self._broadcast("task_started", task.to_dict())
        
        return {"status": "success", "task": task.to_dict()}
    
    def pause_task(self, task_id: str) -> Dict[str, Any]:
        """
        Pauses a RUNNING task.
        
        Args:
            task_id: Task identifier
        
        Returns:
            Dict with status and task info
        """
        if task_id not in self.tasks:
            return {"status": "error", "error": "Task not found"}
        
        task = self.tasks[task_id]
        
        if task.status != TaskStatus.RUNNING:
            return {"status": "error", "error": f"Task is not running (status: {task.status.value})"}
        
        task._paused = True
        task.status = TaskStatus.PLANNED
        task.add_log("Task paused", "INFO")
        
        self._save_task_state(task_id)
        self._broadcast("task_paused", task.to_dict())
        
        return {"status": "success", "task": task.to_dict()}
    
    def resume_task(self, task_id: str) -> Dict[str, Any]:
        """
        Resumes a paused task.
        
        Args:
            task_id: Task identifier
        
        Returns:
            Dict with status and task info
        """
        if task_id not in self.tasks:
            return {"status": "error", "error": "Task not found"}
        
        task = self.tasks[task_id]
        
        if not task._paused and task.status != TaskStatus.PLANNED:
            return {"status": "error", "error": "Task is not paused"}
        
        task._paused = False
        task.status = TaskStatus.RUNNING
        task.add_log("Task resumed", "INFO")
        
        self._save_task_state(task_id)
        self._broadcast("task_resumed", task.to_dict())
        
        return {"status": "success", "task": task.to_dict()}
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Cancels a task (sets status to FAILED).
        
        Args:
            task_id: Task identifier
        
        Returns:
            Dict with status and task info
        """
        if task_id not in self.tasks:
            return {"status": "error", "error": "Task not found"}
        
        task = self.tasks[task_id]
        task._cancelled = True
        task.status = TaskStatus.FAILED
        task.error = "Task cancelled by user"
        task.completed_at = datetime.utcnow().isoformat()
        task.add_log("Task cancelled", "WARNING")
        
        self._save_task_state(task_id)
        self._broadcast("task_cancelled", task.to_dict())
        
        return {"status": "success", "task": task.to_dict()}
    
    def complete_task(self, task_id: str, result: str = "") -> Dict[str, Any]:
        """
        Marks task as COMPLETED.
        
        Args:
            task_id: Task identifier
            result: Final result message
        
        Returns:
            Dict with status and task info
        """
        if task_id not in self.tasks:
            return {"status": "error", "error": "Task not found"}
        
        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.progress = 100
        task.completed_at = datetime.utcnow().isoformat()
        task.result = result
        task.add_log(f"Task completed: {result}", "INFO")
        
        self._save_task_state(task_id)
        self._broadcast("task_completed", task.to_dict())
        
        return {"status": "success", "task": task.to_dict()}
    
    def fail_task(self, task_id: str, error: str = "") -> Dict[str, Any]:
        """
        Marks task as FAILED with error message.
        
        Args:
            task_id: Task identifier
            error: Error message
        
        Returns:
            Dict with status and task info
        """
        if task_id not in self.tasks:
            return {"status": "error", "error": "Task not found"}
        
        task = self.tasks[task_id]
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.utcnow().isoformat()
        task.error = error
        task.add_log(f"Task failed: {error}", "ERROR")
        
        self._save_task_state(task_id)
        self._broadcast("task_failed", task.to_dict())
        
        return {"status": "success", "task": task.to_dict()}
    
    def security_block_task(self, task_id: str, reason: str = "") -> Dict[str, Any]:
        """
        Marks task as SECURITY_BLOCKED.
        
        Args:
            task_id: Task identifier
            reason: Security block reason
        
        Returns:
            Dict with status and task info
        """
        if task_id not in self.tasks:
            return {"status": "error", "error": "Task not found"}
        
        task = self.tasks[task_id]
        task.status = TaskStatus.SECURITY_BLOCKED
        task.completed_at = datetime.utcnow().isoformat()
        task.error = f"Security block: {reason}"
        task.add_log(f"Task security blocked: {reason}", "SECURITY")
        
        self._save_task_state(task_id)
        self._broadcast("security_blocked", task.to_dict())
        
        return {"status": "success", "task": task.to_dict()}
    
    # ============================================================================
    # PROGRESS & FILES
    # ============================================================================
    
    def update_progress(self, task_id: str, progress: int, step: str = ""):
        """
        Updates task progress (0-100) and current step.
        
        Args:
            task_id: Task identifier
            progress: Progress percentage (0-100)
            step: Current step description
        """
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.progress = max(0, min(100, progress))
        if step:
            task.current_step = step
        
        self._save_task_state(task_id)
    
    def add_file(self, task_id: str, file_path: str):
        """
        Adds a created file to task's files list.
        
        Args:
            task_id: Task identifier
            file_path: Path to created file
        """
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        if file_path not in task.files_created:
            task.files_created.append(file_path)
            task.add_log(f"File created: {file_path}", "INFO")
            self._save_task_state(task_id)
    
    def add_risk(self, task_id: str, points: int, reason: str = ""):
        """
        Adds risk points to task's risk score.
        
        Args:
            task_id: Task identifier
            points: Risk points to add
            reason: Reason for risk
        """
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.risk_score += points
        task.add_log(f"Risk added: {points} points - {reason}", "WARNING")
        self._save_task_state(task_id)
    
    # ============================================================================
    # APPROVAL FLOW
    # ============================================================================
    
    def request_approval(self, task_id: str, approval_item: str) -> Dict[str, Any]:
        """
        Requests approval for a tool/action. Sets status to WAITING_APPROVAL.
        
        Args:
            task_id: Task identifier
            approval_item: Item requiring approval
        
        Returns:
            Dict with status
        """
        if task_id not in self.tasks:
            return {"status": "error", "error": "Task not found"}
        
        task = self.tasks[task_id]
        
        if approval_item not in task.pending_approvals:
            task.pending_approvals.append(approval_item)
        
        task.status = TaskStatus.WAITING_APPROVAL
        task.add_log(f"Approval requested: {approval_item}", "WARNING")
        
        self._save_task_state(task_id)
        self._broadcast("approval_requested", {
            "task_id": task_id,
            "approval_item": approval_item,
            "task": task.to_dict()
        })
        
        return {"status": "success", "task": task.to_dict()}
    
    def grant_approval(self, task_id: str, approval_item: str) -> Dict[str, Any]:
        """
        Grants an approval. Resumes task if no pending approvals.
        
        Args:
            task_id: Task identifier
            approval_item: Item to approve
        
        Returns:
            Dict with status
        """
        if task_id not in self.tasks:
            return {"status": "error", "error": "Task not found"}
        
        task = self.tasks[task_id]
        
        if approval_item in task.pending_approvals:
            task.pending_approvals.remove(approval_item)
        
        task.add_log(f"Approval granted: {approval_item}", "INFO")
        
        # Resume if no more approvals needed
        if not task.pending_approvals and task._paused:
            task.status = TaskStatus.RUNNING
            task._paused = False
            task.add_log("Resumed (all approvals granted)", "INFO")
        
        self._save_task_state(task_id)
        self._broadcast("approval_granted", {
            "task_id": task_id,
            "approval_item": approval_item,
            "task": task.to_dict()
        })
        
        return {"status": "success", "task": task.to_dict()}
    
    def deny_approval(self, task_id: str, approval_item: str) -> Dict[str, Any]:
        """
        Denies an approval request.
        
        Args:
            task_id: Task identifier
            approval_item: Item to deny
        
        Returns:
            Dict with status
        """
        if task_id not in self.tasks:
            return {"status": "error", "error": "Task not found"}
        
        task = self.tasks[task_id]
        
        if approval_item in task.pending_approvals:
            task.pending_approvals.remove(approval_item)
        
        task.status = TaskStatus.FAILED
        task.error = f"Approval denied: {approval_item}"
        task.add_log(f"Approval denied: {approval_item}", "ERROR")
        
        self._save_task_state(task_id)
        self._broadcast("approval_denied", {
            "task_id": task_id,
            "approval_item": approval_item,
            "task": task.to_dict()
        })
        
        return {"status": "success", "task": task.to_dict()}
    
    # ============================================================================
    # KILL SWITCH
    # ============================================================================
    
    def activate_kill_switch(self) -> Dict[str, Any]:
        """
        EMERGENCY KILL SWITCH:
        - Stops all running tasks
        - Disables all tools
        - Logs shutdown to ./workspace/logs/kill_switch.log
        """
        self._kill_switch_active = True
        
        # Stop all running tasks
        stopped_tasks = []
        for task_id, task in self.tasks.items():
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.SECURITY_BLOCKED
                task.error = "Kill switch activated"
                task.completed_at = datetime.utcnow().isoformat()
                task.add_log("Task stopped by kill switch", "CRITICAL")
                self._save_task_state(task_id)
                stopped_tasks.append(task_id)
        
        # Log kill switch event
        kill_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "KILL_SWITCH_ACTIVATED",
            "tasks_stopped": stopped_tasks,
            "active_tasks_count": len(stopped_tasks)
        }
        
        os.makedirs("./workspace/logs", exist_ok=True)
        with open("./workspace/logs/kill_switch.log", 'a') as f:
            f.write(json.dumps(kill_log) + "\n")
        
        self._broadcast("kill_switch_activated", kill_log)
        
        return {
            "status": "kill_switch_activated",
            "message": "All tasks stopped",
            "tasks_affected": stopped_tasks
        }
    
    def reset_kill_switch(self) -> Dict[str, Any]:
        """Resets kill switch to allow new tasks."""
        self._kill_switch_active = False
        
        # Log reset
        reset_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "KILL_SWITCH_RESET"
        }
        
        with open("./workspace/logs/kill_switch.log", 'a') as f:
            f.write(json.dumps(reset_log) + "\n")
        
        self._broadcast("kill_switch_reset", reset_log)
        
        return {"status": "kill_switch_reset", "message": "Kill switch reset"}
    
    @property
    def kill_switch_active(self) -> bool:
        """Returns True if kill switch is active."""
        return self._kill_switch_active
    
    # ============================================================================
    # QUERIES
    # ============================================================================
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns task as dictionary or None.
        
        Args:
            task_id: Task identifier
        
        Returns:
            Task dict or None
        """
        if task_id not in self.tasks:
            return None
        return self.tasks[task_id].to_dict()
    
    def list_tasks(self, status: str = None) -> List[Dict[str, Any]]:
        """
        Returns all tasks as list of dictionaries.
        
        Args:
            status: Optional status filter
        
        Returns:
            List of task dictionaries
        """
        tasks = []
        for task_id in self.queue:
            if task_id in self.tasks:
                task_dict = self.tasks[task_id].to_dict()
                if status is None or task_dict["status"] == status:
                    tasks.append(task_dict)
        return tasks
    
    def get_queue(self) -> List[str]:
        """Returns ordered list of task_ids in queue."""
        return self.queue.copy()
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Returns all pending approvals across all tasks."""
        approvals = []
        for task_id, task in self.tasks.items():
            for approval in task.pending_approvals:
                approvals.append({
                    "task_id": task_id,
                    "goal": task.goal,
                    "approval_item": approval,
                    "status": task.status.value
                })
        return approvals
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Returns task statistics.
        
        Returns:
            Dict with statistics
        """
        stats = {
            "total": len(self.tasks),
            "by_status": {},
            "kill_switch_active": self._kill_switch_active
        }
        
        for status in TaskStatus:
            stats["by_status"][status.value] = sum(
                1 for t in self.tasks.values() if t.status == status
            )
        
        return stats

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_task_manager(broadcast_fn: Callable = None) -> TaskManager:
    """Create a new task manager."""
    return TaskManager(broadcast_fn)

if __name__ == "__main__":
    print("🐾 ClawForge TaskManager - Test")
    print("=" * 50)
    
    tm = TaskManager()
    
    # Test task creation
    print("\n📋 Task Creation Test:")
    task1 = tm.create_task("Write a blog about AI agents", "content_writing")
    print(f"   Created: {task1.task_id}")
    
    task2 = tm.create_task("Generate Python script", "code_generation")
    print(f"   Created: {task2.task_id}")
    
    # Test status transitions
    print("\n🔄 Status Transitions Test:")
    result = tm.start_task(task1.task_id)
    print(f"   Start task: {result['status']}")
    
    result = tm.update_progress(task1.task_id, 50, "Writing content")
    print(f"   Update progress: {result}")
    
    result = tm.complete_task(task1.task_id, "Blog written successfully")
    print(f"   Complete: {result['status']}")
    
    # Test task listing
    print("\n📊 Task Listing:")
    tasks = tm.list_tasks()
    print(f"   Total tasks: {len(tasks)}")
    for t in tasks:
        print(f"   - {t['task_id']}: {t['status']} ({t['progress']}%)")
    
    # Test statistics
    print("\n📈 Statistics:")
    stats = tm.get_stats()
    print(f"   Total: {stats['total']}")
    print(f"   By status: {stats['by_status']}")
