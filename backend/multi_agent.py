"""
Leo 2.0 - Multi-Agent System
===========================
Implements CrewAI-style multi-agent collaboration.
Based on patterns from the Udemy course.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class AgentRole(Enum):
    RESEARCHER = "researcher"
    CODER = "coder"
    ANALYZER = "analyzer"
    PLANNER = "planner"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    GENERAL = "general"


class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    DONE = "done"
    ERROR = "error"


@dataclass
class Agent:
    """An individual agent in the system."""
    id: str
    name: str
    role: AgentRole
    description: str
    instructions: str
    tools: List[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE
    current_task: str = ""
    result: Any = None
    metadata: Dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentMessage:
    """Message between agents."""
    id: str
    from_agent: str
    to_agent: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Task:
    """A task assigned to an agent."""
    id: str
    description: str
    assigned_agent: str = ""
    status: str = "pending"
    result: Any = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None


class MultiAgentSystem:
    """
    Multi-agent collaboration system.
    
    Features:
    - Multiple specialized agents
    - Task assignment and coordination
    - Inter-agent communication
    - Parallel execution
    """
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.messages: List[AgentMessage] = []
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self._register_builtin_agents()
    
    def _register_builtin_agents(self):
        """Register built-in agents."""
        
        # Researcher Agent
        self.register_agent(Agent(
            id="researcher",
            name="Researcher",
            role=AgentRole.RESEARCHER,
            description="Gathers and analyzes information",
            instructions="Search for relevant information and provide detailed findings.",
            tools=["web_search", "web_fetch", "memory_search"]
        ))
        
        # Coder Agent
        self.register_agent(Agent(
            id="coder",
            name="Coder",
            role=AgentRole.CODER,
            description="Writes and reviews code",
            instructions="Write clean, efficient code. Review code for issues.",
            tools=["run_code", "file_read"]
        ))
        
        # Analyzer Agent
        self.register_agent(Agent(
            id="analyzer",
            name="Analyzer",
            role=AgentRole.ANALYZER,
            description="Analyzes data and problems",
            instructions="Break down problems and analyze them thoroughly.",
            tools=["calculate", "memory_search"]
        ))
        
        # Planner Agent
        self.register_agent(Agent(
            id="planner",
            name="Planner",
            role=AgentRole.PLANNER,
            description="Creates plans and strategies",
            instructions="Create detailed plans for accomplishing tasks.",
            tools=["memory_search"]
        ))
        
        # Executor Agent
        self.register_agent(Agent(
            id="executor",
            name="Executor",
            role=AgentRole.EXECUTOR,
            description="Executes plans and tasks",
            instructions="Execute tasks efficiently and report results.",
            tools=["run_code", "file_read", "file_write"]
        ))
        
        # Reviewer Agent
        self.register_agent(Agent(
            id="reviewer",
            name="Reviewer",
            role=AgentRole.REVIEWER,
            description="Reviews and validates work",
            instructions="Review work and provide constructive feedback.",
            tools=["memory_search"]
        ))
    
    def register_agent(self, agent: Agent):
        """Register an agent."""
        self.agents[agent.id] = agent
    
    def create_agent(self, name: str, role: AgentRole, description: str, 
                    instructions: str, tools: List[str] = None) -> str:
        """Create a new agent."""
        agent_id = str(uuid.uuid4())[:8]
        agent = Agent(
            id=agent_id,
            name=name,
            role=role,
            description=description,
            instructions=instructions,
            tools=tools or []
        )
        self.agents[agent_id] = agent
        return agent_id
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict]:
        """List all agents."""
        return [
            {
                "id": a.id,
                "name": a.name,
                "role": a.role.value,
                "status": a.status.value,
                "tools": a.tools
            }
            for a in self.agents.values()
        ]
    
    def create_task(self, description: str, assigned_agent: str = "") -> str:
        """Create a new task."""
        task_id = str(uuid.uuid4())[:8]
        task = Task(
            id=task_id,
            description=description,
            assigned_agent=assigned_agent
        )
        self.tasks[task_id] = task
        return task_id
    
    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """Assign a task to an agent."""
        if task_id not in self.tasks or agent_id not in self.agents:
            return False
        
        task = self.tasks[task_id]
        task.assigned_agent = agent_id
        return True
    
    def send_message(self, from_agent: str, to_agent: str, content: str) -> str:
        """Send a message between agents."""
        msg_id = str(uuid.uuid4())[:8]
        message = AgentMessage(
            id=msg_id,
            from_agent=from_agent,
            to_agent=to_agent,
            content=content
        )
        self.messages.append(message)
        return msg_id
    
    def get_messages(self, agent_id: str = None) -> List[Dict]:
        """Get messages for an agent."""
        if agent_id:
            return [
                {
                    "id": m.id,
                    "from": m.from_agent,
                    "to": m.to_agent,
                    "content": m.content,
                    "timestamp": m.timestamp
                }
                for m in self.messages 
                if m.to_agent == agent_id or m.from_agent == agent_id
            ]
        return [
            {
                "id": m.id,
                "from": m.from_agent,
                "to": m.to_agent,
                "content": m.content,
                "timestamp": m.timestamp
            }
            for m in self.messages
        ]
    
    async def execute_task(self, task_id: str) -> Dict:
        """Execute a task with the assigned agent."""
        if task_id not in self.tasks:
            return {"error": "Task not found"}
        
        task = self.tasks[task_id]
        
        if not task.assigned_agent:
            return {"error": "No agent assigned"}
        
        agent = self.agents.get(task.assigned_agent)
        if not agent:
            return {"error": "Agent not found"}
        
        # Update status
        agent.status = AgentStatus.THINKING
        agent.current_task = task.description
        
        # Simulate execution (in real impl, this would call LLM)
        await asyncio.sleep(0.5)
        
        task.result = f"[{agent.name}] Processed: {task.description}"
        task.status = "completed"
        task.completed_at = datetime.now().isoformat()
        
        agent.status = AgentStatus.DONE
        agent.result = task.result
        
        return {
            "task_id": task_id,
            "agent": agent.name,
            "result": task.result
        }
    
    async def run_parallel(self, task_ids: List[str]) -> List[Dict]:
        """Run multiple tasks in parallel."""
        results = await asyncio.gather(
            *[self.execute_task(task_id) for task_id in task_ids]
        )
        return results
    
    def get_system_status(self) -> Dict:
        """Get overall system status."""
        return {
            "agents": len(self.agents),
            "tasks": len(self.tasks),
            "messages": len(self.messages),
            "agent_details": [
                {
                    "id": a.id,
                    "name": a.name,
                    "status": a.status.value,
                    "current_task": a.current_task
                }
                for a in self.agents.values()
            ]
        }


# Singleton
_multi_agent_system = None

def get_multi_agent_system() -> MultiAgentSystem:
    global _multi_agent_system
    if _multi_agent_system is None:
        _multi_agent_system = MultiAgentSystem()
    return _multi_agent_system
