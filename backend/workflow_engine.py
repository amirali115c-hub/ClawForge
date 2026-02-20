"""
Leo 2.0 - LangGraph-Style Workflow Engine
=========================================
Implements graph-based agent workflows for structured thinking.
Based on LangGraph patterns from the Udemy course.
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import threading


class NodeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"


class EdgeType(Enum):
    NORMAL = "normal"          # Standard flow
    CONDITIONAL = "conditional"  # Based on condition
    LOOP = "loop"              # Loop back
    PARALLEL = "parallel"      # Run in parallel


@dataclass
class Node:
    """A node in the workflow graph."""
    id: str
    name: str
    description: str
    action: Callable = None
    status: NodeStatus = NodeStatus.PENDING
    result: Any = None
    error: str = None
    metadata: Dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    

@dataclass
class Edge:
    """An edge connecting nodes."""
    source_id: str
    target_id: str
    edge_type: EdgeType = EdgeType.NORMAL
    condition: Callable = None  # For conditional edges


@dataclass
class WorkflowState:
    """The current state of the workflow."""
    workflow_id: str
    current_node_id: str
    state: Dict = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())


class LangGraphWorkflow:
    """
    LangGraph-style workflow engine.
    
    Based on LangGraph patterns:
    - Nodes: Individual processing steps
    - Edges: Connections between nodes
    - State: Shared data across nodes
    - Conditional: Dynamic routing based on results
    """
    
    def __init__(self, name: str, description: str = ""):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.description = description
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.start_node_id: Optional[str] = None
        self.end_node_ids: List[str] = []
        self.state: Dict = {}
        self.workflow_history: List[WorkflowState] = []
        
        # Callbacks
        self.on_node_start: Optional[Callable] = None
        self.on_node_complete: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        self.lock = threading.Lock()
    
    def add_node(self, node_id: str, name: str, description: str = "", action: Callable = None) -> 'LangGraphWorkflow':
        """Add a node to the workflow."""
        with self.lock:
            node = Node(
                id=node_id,
                name=name,
                description=description,
                action=action
            )
            self.nodes[node_id] = node
        return self
    
    def set_start(self, node_id: str) -> 'LangGraphWorkflow':
        """Set the starting node."""
        self.start_node_id = node_id
        return self
    
    def add_end(self, node_id: str) -> 'LangGraphWorkflow':
        """Mark a node as an end node."""
        if node_id not in self.end_node_ids:
            self.end_node_ids.append(node_id)
        return self
    
    def add_edge(self, source_id: str, target_id: str, edge_type: EdgeType = EdgeType.NORMAL) -> 'LangGraphWorkflow':
        """Add an edge between nodes."""
        # Verify nodes exist
        if source_id not in self.nodes:
            raise ValueError(f"Source node '{source_id}' not found")
        if target_id not in self.nodes:
            raise ValueError(f"Target node '{target_id}' not found")
        
        edge = Edge(source_id=source_id, target_id=target_id, edge_type=edge_type)
        self.edges.append(edge)
        return self
    
    def add_conditional_edge(self, source_id: str, target_id: str, condition: Callable) -> 'LangGraphWorkflow':
        """Add a conditional edge."""
        edge = Edge(source_id=source_id, target_id=target_id, edge_type=EdgeType.CONDITIONAL, condition=condition)
        self.edges.append(edge)
        return self
    
    def _get_next_node_id(self, current_node_id: str) -> Optional[str]:
        """Determine the next node to execute."""
        # Find outgoing edges from current node
        outgoing = [e for e in self.edges if e.source_id == current_node_id]
        
        if not outgoing:
            return None
        
        # Check for conditional edges first
        for edge in outgoing:
            if edge.edge_type == EdgeType.CONDITIONAL and edge.condition:
                try:
                    if edge.condition(self.state, self.nodes[current_node_id].result):
                        return edge.target_id
                except:
                    pass
        
        # Return first normal edge
        for edge in outgoing:
            if edge.edge_type == EdgeType.NORMAL:
                return edge.target_id
        
        return None
    
    async def run(self, initial_state: Dict = None) -> Dict:
        """Execute the workflow."""
        if not self.start_node_id:
            raise ValueError("No start node defined")
        
        self.state = initial_state or {}
        current_node_id = self.start_node_id
        steps_executed = 0
        max_steps = 100  # Prevent infinite loops
        
        while current_node_id and steps_executed < max_steps:
            node = self.nodes[current_node_id]
            
            # Update status
            node.status = NodeStatus.RUNNING
            
            # Callback
            if self.on_node_start:
                self.on_node_start(node)
            
            # Execute node action
            try:
                if node.action:
                    result = await node.action(self.state, node.result)
                    node.result = result
                node.status = NodeStatus.COMPLETED
                
                # Callback
                if self.on_node_complete:
                    self.on_node_complete(node)
                    
            except Exception as e:
                node.status = NodeStatus.FAILED
                node.error = str(e)
                
                if self.on_error:
                    self.on_error(node, e)
                
                break
            
            # Record history
            self.workflow_history.append(WorkflowState(
                workflow_id=self.id,
                current_node_id=current_node_id,
                state=self.state.copy(),
                history=[]
            ))
            
            # Check if end node
            if current_node_id in self.end_node_ids:
                break
            
            # Get next node
            current_node_id = self._get_next_node_id(current_node_id)
            steps_executed += 1
        
        return {
            "workflow_id": self.id,
            "state": self.state,
            "completed": steps_executed < max_steps,
            "steps": steps_executed
        }
    
    def get_status(self) -> Dict:
        """Get current workflow status."""
        return {
            "id": self.id,
            "name": self.name,
            "nodes": {
                node_id: {
                    "name": node.name,
                    "status": node.status.value,
                    "result": str(node.result)[:100] if node.result else None,
                    "error": node.error
                }
                for node_id, node in self.nodes.items()
            },
            "state": self.state
        }


# Pre-built workflow templates
class WorkflowTemplates:
    """Pre-built workflow templates."""
    
    @staticmethod
    def research_workflow() -> LangGraphWorkflow:
        """Multi-step research workflow."""
        workflow = LangGraphWorkflow(
            name="Research Workflow",
            description="Research a topic with multiple sources"
        )
        
        # Add nodes
        workflow.add_node(
            "understand", 
            "Understand Query", 
            "Analyze the research question",
            action=lambda state, _: {"query": state.get("query", "")}
        ).add_node(
            "search", 
            "Search Sources", 
            "Search for relevant information",
            lambda state, _: {"sources_found": 5}
        ).add_node(
            "analyze", 
            "Analyze Results", 
            "Process and analyze findings",
            lambda state, _: {"analysis": "completed"}
        ).add_node(
            "synthesize", 
            "Synthesize", 
            "Create final summary",
            lambda state, _: {"summary": "Final research summary"}
        ).add_node(
            "cite", 
            "Add Citations", 
            "Add sources and references",
            lambda state, _: {"citations_added": True}
        )
        
        # Set flow
        workflow.set_start("understand")
        workflow.add_edge("understand", "search")
        workflow.add_edge("search", "analyze")
        workflow.add_edge("analyze", "synthesize")
        workflow.add_edge("synthesize", "cite")
        workflow.add_end("cite")
        
        return workflow
    
    @staticmethod
    def coding_workflow() -> LangGraphWorkflow:
        """Code generation workflow."""
        workflow = LangGraphWorkflow(
            name="Coding Workflow",
            description="Generate and review code"
        )
        
        workflow.add_node("analyze", "Analyze Request", "Understand what to build")
        workflow.add_node("design", "Design Solution", "Plan the architecture")
        workflow.add_node("generate", "Generate Code", "Write the code")
        workflow.add_node("review", "Review Code", "Check for issues")
        workflow.add_node("test", "Test Code", "Run tests")
        
        workflow.set_start("analyze")
        workflow.add_edge("analyze", "design")
        workflow.add_edge("design", "generate")
        workflow.add_edge("generate", "review")
        
        # Conditional: retry if issues
        def needs_revision(state, result):
            return result.get("issues_found", 0) > 0
        
        workflow.add_conditional_edge("review", "generate", needs_revision)
        workflow.add_edge("review", "test")
        workflow.add_end("test")
        
        return workflow


# Singleton
_workflow_engine = None

def get_workflow_engine() -> Dict:
    """Get workflow engine with templates."""
    return {
        "create": lambda name, desc: LangGraphWorkflow(name, desc),
        "templates": WorkflowTemplates(),
        "run": lambda wf, state: wf.run(state)
    }
