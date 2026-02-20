"""
Leo 2.0 - Tool Calling Engine
=============================
Automatically detects when to use tools and executes them.
"""

import re
import json
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass


class ToolType(Enum):
    SEARCH = "search"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    CODE_RUN = "code_run"
    WEB_FETCH = "web_fetch"
    MEMORY = "memory"
    CALCULATE = "calculate"
    TRANSLATE = "translate"
    NONE = "none"


@dataclass
class ToolCall:
    tool: ToolType
    confidence: float
    reason: str
    parameters: Dict[str, Any]


class ToolCallingEngine:
    """Detects when to call tools based on user input."""
    
    # Intent patterns for tool detection
    TOOL_PATTERNS = {
        ToolType.SEARCH: [
            r'search (?:for |)(.+)',
            r'find (?:information about |)(.+)',
            r'look up (.+)',
            r'what is (.+)',
            r'who is (.+)',
            r'how to (.+)',
            r'lookup (.+)',
            r'googling (.+)',
        ],
        ToolType.FILE_READ: [
            r'read (?:the |)(?:file |)(.+\.(?:txt|py|js|md|json|html|css))',
            r'show (?:me |)(?:the |)(?:content of |)(.+\.(?:txt|py|js|md|json|html|css))',
            r'open (?:file |)(.+\.(?:txt|py|js|md|json|html|css))',
            r'what.?s in (.+)',
            r'list (?:files |)(?:in |)(.+)',
        ],
        ToolType.FILE_WRITE: [
            r'write (?:to |)(?:file |)(.+)',
            r'save (?:to |)(?:file |)(.+)',
            r'create (?:file |)(.+)',
            r'make (?:a |)(?:file |)(.+)',
        ],
        ToolType.CODE_RUN: [
            r'run (?:the |)(?:code |)(.+)',
            r'execute (?:code |)(.+)',
            r'run python (.+)',
            r'calculate (.+)',
            r'compute (.+)',
            r'eval(?:uate|)? (.+)',
        ],
        ToolType.WEB_FETCH: [
            r'fetch (?:from |)(https?://.+)',
            r'scrape (.+)',
            r'get (?:content from |)(https?://.+)',
            r'open (?:website |)(https?://.+)',
        ],
        ToolType.MEMORY: [
            r'remember (?:that |)(.+)',
            r'memorize (.+)',
            r'don.?t forget (.+)',
            r'save this (.+)',
            r'recall (.+)',
        ],
        ToolType.CALCULATE: [
            r'what.?s (\d+\s*[\+\-\*/]\s*\d+)',
            r'calculate (\d+\s*[\+\-\*/]\s*\d+)',
            r'compute (\d+\s*[\+\-\*/]\s*\d+)',
            r'(\d+\s*[\+\-\*/]\s*\d+)',
        ],
    }
    
    # Keywords that indicate tool use
    TOOL_KEYWORDS = {
        ToolType.SEARCH: {'search', 'find', 'lookup', 'google', 'what is', 'who is', 'how to', 'information'},
        ToolType.FILE_READ: {'read', 'show', 'open', 'display', 'view', 'list', 'contents'},
        ToolType.FILE_WRITE: {'write', 'save', 'create', 'make', 'edit', 'modify'},
        ToolType.CODE_RUN: {'run', 'execute', 'code', 'python', 'calculate', 'compute'},
        ToolType.WEB_FETCH: {'fetch', 'scrape', 'get content', 'open website'},
        ToolType.MEMORY: {'remember', 'memorize', 'save', 'recall', 'keep in mind'},
        ToolType.CALCULATE: {'calculate', 'compute', 'sum', 'plus', 'minus', 'times', 'divided'},
    }
    
    def __init__(self):
        self.call_count = 0
        self.tool_history: List[ToolCall] = []
    
    def should_use_tool(self, user_message: str) -> Optional[ToolCall]:
        """Analyze if a tool should be used."""
        self.call_count += 1
        message_lower = user_message.lower()
        
        # Check regex patterns first (highest confidence)
        for tool_type, patterns in self.TOOL_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, message_lower, re.IGNORECASE)
                if match:
                    try:
                        param = match.group(1).strip() if match.groups() else user_message
                    except:
                        param = user_message
                    
                    tool_call = ToolCall(
                        tool=tool_type,
                        confidence=0.9,
                        reason=f"Pattern match: {pattern}",
                        parameters={'query': param, 'original': user_message}
                    )
                    self.tool_history.append(tool_call)
                    return tool_call
        
        # Check keywords
        for tool_type, keywords in self.TOOL_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in message_lower)
            if matches >= 1:
                # Extract potential parameter
                param = self._extract_parameter(user_message, tool_type)
                
                tool_call = ToolCall(
                    tool=tool_type,
                    confidence=0.6 + (matches * 0.1),
                    reason=f"Keyword match: {matches} keywords",
                    parameters={'query': param, 'keywords': list(keywords & set(message_lower.split()))}
                )
                self.tool_history.append(tool_call)
                return tool_call
        
        return None
    
    def _extract_parameter(self, message: str, tool_type: ToolType) -> str:
        """Extract relevant parameter from message."""
        # Remove common prefixes
        prefixes = ['search for', 'find', 'look up', 'read', 'write to', 'calculate', 'compute']
        msg_lower = message.lower()
        
        for prefix in prefixes:
            if msg_lower.startswith(prefix):
                return message[len(prefix):].strip()
        
        return message
    
    def get_stats(self) -> Dict:
        """Get tool calling statistics."""
        tool_counts = {}
        for tc in self.tool_history:
            tool_name = tc.tool.value
            tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
        
        return {
            'total_calls': self.call_count,
            'tool_history_count': len(self.tool_history),
            'tool_usage': tool_counts,
            'recent_tools': [tc.tool.value for tc in self.tool_history[-5:]]
        }


# Singleton
_tool_calling_engine = None

def get_tool_calling_engine() -> ToolCallingEngine:
    global _tool_calling_engine
    if _tool_calling_engine is None:
        _tool_calling_engine = ToolCallingEngine()
    return _tool_calling_engine


# Convenience functions
def should_use_tool(message: str) -> Optional[ToolCall]:
    """Check if tool should be used."""
    return get_tool_calling_engine().should_use_tool(message)


def get_tool_stats() -> Dict:
    """Get tool calling stats."""
    return get_tool_calling_engine().get_stats()
