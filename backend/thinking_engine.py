"""
Leo 2.0 - Structured Thinking Engine
===================================
Implements thinking patterns for better reasoning.
Based on chain-of-thought, tree-of-thought, and other patterns.
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class ThinkingPattern(Enum):
    CHAIN_OF_THOUGHT = "chain_of_thought"      # Sequential reasoning
    TREE_OF_THOUGHT = "tree_of_thought"        # Branching exploration
    REFLECTION = "reflection"                   # Self-review
    REACT = "react"                           # Reason + Act
    SCOT = "scot"                             # Self-Consistent Optimization


@dataclass
class Thought:
    """A single thought in the thinking process."""
    id: str
    content: str
    reasoning: str
    pattern: ThinkingPattern
    confidence: float = 0.5
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ThinkingSession:
    """A complete thinking session."""
    id: str
    pattern: ThinkingPattern
    thoughts: Dict[str, Thought] = field(default_factory=dict)
    root_thought_id: Optional[str] = None
    current_thought_id: Optional[str] = None
    final_answer: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class StructuredThinkingEngine:
    """
    Multi-pattern thinking engine.
    
    Patterns:
    - Chain of Thought: Step-by-step reasoning
    - Tree of Thought: Explore multiple branches
    - Reflection: Review and improve
    - ReAct: Reason + Action
    - SCOT: Self-consistent optimization
    """
    
    def __init__(self):
        self.sessions: Dict[str, ThinkingSession] = {}
        self.current_session: Optional[ThinkingSession] = None
    
    def create_session(self, pattern: ThinkingPattern = ThinkingPattern.CHAIN_OF_THOUGHT) -> str:
        """Create a new thinking session."""
        session_id = str(uuid.uuid4())[:8]
        session = ThinkingSession(
            id=session_id,
            pattern=pattern
        )
        self.sessions[session_id] = session
        self.current_session = session
        return session_id
    
    def add_thought(self, content: str, reasoning: str = "", confidence: float = 0.5, 
                   parent_id: Optional[str] = None) -> str:
        """Add a thought to the current session."""
        if not self.current_session:
            self.create_session()
        
        thought_id = str(uuid.uuid4())[:8]
        thought = Thought(
            id=thought_id,
            content=content,
            reasoning=reasoning,
            pattern=self.current_session.pattern,
            confidence=confidence,
            parent_id=parent_id
        )
        
        # Update parent if exists
        if parent_id and parent_id in self.current_session.thoughts:
            self.current_session.thoughts[parent_id].children_ids.append(thought_id)
        elif not self.current_session.root_thought_id:
            self.current_session.root_thought_id = thought_id
        
        self.current_session.thoughts[thought_id] = thought
        self.current_session.current_thought_id = thought_id
        
        return thought_id
    
    def select_best_branch(self) -> str:
        """Select the best branch (Tree of Thought)."""
        if not self.current_session:
            return None
        
        # Find thoughts with highest confidence
        best_id = None
        best_confidence = 0
        
        for thought_id, thought in self.current_session.thoughts.items():
            if thought.confidence > best_confidence:
                best_confidence = thought.confidence
                best_id = thought_id
        
        return best_id
    
    def reflect(self) -> str:
        """Reflect on the current thinking."""
        if not self.current_session:
            return "No session to reflect on"
        
        thoughts = list(self.current_session.thoughts.values())
        if not thoughts:
            return "No thoughts to reflect on"
        
        # Find weaknesses
        low_confidence = [t for t in thoughts if t.confidence < 0.6]
        
        if low_confidence:
            reflection = f"Found {len(low_confidence)} thoughts with low confidence. Consider exploring alternatives."
        else:
            reflection = "All thoughts have high confidence. Current reasoning is solid."
        
        # Add reflection thought
        self.add_thought(
            content=reflection,
            reasoning="Self-reflection on current thinking",
            confidence=0.9
        )
        
        return reflection
    
    def get_thought_chain(self) -> List[Dict]:
        """Get the chain of thoughts."""
        if not self.current_session:
            return []
        
        chain = []
        current_id = self.current_session.root_thought_id
        
        while current_id:
            thought = self.current_session.thoughts.get(current_id)
            if thought:
                chain.append({
                    "id": thought.id,
                    "content": thought.content[:100],
                    "reasoning": thought.reasoning[:100],
                    "confidence": thought.confidence
                })
                # Follow first child for chain
                current_id = thought.children_ids[0] if thought.children_ids else None
            else:
                break
        
        return chain
    
    def get_tree(self) -> List[Dict]:
        """Get full tree of thoughts."""
        if not self.current_session:
            return []
        
        return [
            {
                "id": t.id,
                "content": t.content[:100],
                "confidence": t.confidence,
                "children": len(t.children_ids)
            }
            for t in self.current_session.thoughts.values()
        ]
    
    def conclude(self, answer: str) -> Dict:
        """Conclude the thinking session."""
        if not self.current_session:
            return {"error": "No active session"}
        
        self.current_session.final_answer = answer
        
        return {
            "session_id": self.current_session.id,
            "pattern": self.current_session.pattern.value,
            "thought_count": len(self.current_session.thoughts),
            "final_answer": answer
        }
    
    def get_session_summary(self) -> Dict:
        """Get summary of current session."""
        if not self.current_session:
            return {"error": "No active session"}
        
        return {
            "id": self.current_session.id,
            "pattern": self.current_session.pattern.value,
            "thoughts": len(self.current_session.thoughts),
            "root": self.current_session.root_thought_id,
            "current": self.current_session.current_thought_id,
            "final": self.current_session.final_answer
        }


# Singleton
_thinking_engine = None

def get_thinking_engine() -> StructuredThinkingEngine:
    global _thinking_engine
    if _thinking_engine is None:
        _thinking_engine = StructuredThinkingEngine()
    return _thinking_engine
