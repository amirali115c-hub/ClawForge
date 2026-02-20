"""
Leo 2.0 - OpenAI-Style Tool Calling Engine
==========================================
Enhanced tool detection and execution with function calling patterns.
Based on OpenAI's function calling API.
"""

import re
import json
import asyncio
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class ToolType(Enum):
    SEARCH = "search"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    CODE_RUN = "code_run"
    WEB_FETCH = "web_fetch"
    MEMORY = "memory"
    CALCULATE = "calculate"
    TRANSLATE = "translate"
    CUSTOM = "custom"
    NONE = "none"


@dataclass
class ToolParameter:
    """A parameter definition for a tool."""
    name: str
    type: str
    description: str
    required: bool = False
    default: Any = None
    enum: List[str] = None


@dataclass
class ToolDefinition:
    """Definition of a callable tool (OpenAI-style)."""
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    function: Callable = None
    category: str = "general"


@dataclass
class ToolCall:
    """A detected tool call."""
    tool_name: str
    arguments: Dict[str, Any]
    confidence: float
    reasoning: str
    result: Any = None
    error: str = None
    executed_at: str = field(default_factory=lambda: datetime.now().isoformat())


class OpenAIToolCallingEngine:
    """
    OpenAI-style function calling engine.
    
    Features:
    - Tool definitions with parameters
    - Structured argument parsing
    - Function execution
    - Result formatting
    """
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.call_history: List[ToolCall] = []
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """Register built-in tools."""
        
        # Web Search Tool
        self.register_tool(ToolDefinition(
            name="web_search",
            description="Search the web for information",
            parameters=[
                ToolParameter("query", "string", "The search query", required=True),
                ToolParameter("max_results", "integer", "Maximum results to return", required=False, default=5)
            ],
            category="search"
        ))
        
        # Web Fetch Tool
        self.register_tool(ToolDefinition(
            name="web_fetch",
            description="Fetch and extract content from a URL",
            parameters=[
                ToolParameter("url", "string", "The URL to fetch", required=True),
                ToolParameter("max_chars", "integer", "Maximum characters to extract", required=False, default=5000)
            ],
            category="web"
        ))
        
        # Calculator Tool
        self.register_tool(ToolDefinition(
            name="calculate",
            description="Perform mathematical calculations",
            parameters=[
                ToolParameter("expression", "string", "Mathematical expression to evaluate", required=True)
            ],
            category="utility"
        ))
        
        # Memory Search Tool
        self.register_tool(ToolDefinition(
            name="memory_search",
            description="Search the knowledge base for information",
            parameters=[
                ToolParameter("query", "string", "Search query", required=True),
                ToolParameter("max_results", "integer", "Maximum results", required=False, default=5)
            ],
            category="memory"
        ))
        
        # File Read Tool
        self.register_tool(ToolDefinition(
            name="file_read",
            description="Read content from a file",
            parameters=[
                ToolParameter("path", "string", "File path to read", required=True),
                ToolParameter("lines", "integer", "Number of lines to read", required=False)
            ],
            category="file"
        ))
        
        # Code Run Tool
        self.register_tool(ToolDefinition(
            name="run_code",
            description="Execute Python code",
            parameters=[
                ToolParameter("code", "string", "Python code to execute", required=True),
                ToolParameter("timeout", "integer", "Timeout in seconds", required=False, default=30)
            ],
            category="code"
        ))
    
    def register_tool(self, tool: ToolDefinition):
        """Register a new tool."""
        self.tools[tool.name] = tool
    
    def get_tool_schemas(self) -> List[Dict]:
        """Get OpenAI-style tool schemas."""
        schemas = []
        for tool in self.tools.values():
            params = {
                "type": "object",
                "properties": {},
                "required": []
            }
            for p in tool.parameters:
                params["properties"][p.name] = {
                    "type": p.type,
                    "description": p.description
                }
                if p.enum:
                    params["properties"][p.name]["enum"] = p.enum
                if p.required:
                    params["required"].append(p.name)
            
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": params
                }
            })
        return schemas
    
    def detect_tool_call(self, user_input: str) -> Optional[ToolCall]:
        """Detect if user wants to use a tool."""
        user_lower = user_input.lower()
        
        # Pattern-based detection
        patterns = {
            "web_search": [
                r'search (?:for |)(.+)',
                r'find (?:information about |)(.+)',
                r'look up (.+)',
                r'what is (.+)',
                r'who is (.+)',
                r'how to (.+)',
                r'googling? (.+)',
            ],
            "calculate": [
                r'calculate (.+)',
                r'compute (.+)',
                r'what is (\d+\s*[\+\-\*/]\s*\d+)',
                r'(\d+\s*[\+\-\*/]\s*\d+\s*[\+\-\*/]\s*\d+)',
            ],
            "web_fetch": [
                r'fetch (?:from |)(https?://.+)',
                r'open (?:the |)(https?://.+)',
                r'get (?:content from |)(https?://.+)',
            ]
        }
        
        for tool_name, regex_list in patterns.items():
            for pattern in regex_list:
                match = re.search(pattern, user_lower)
                if match:
                    args = {}
                    if tool_name == "web_search":
                        args["query"] = match.group(1).strip()
                    elif tool_name == "calculate":
                        args["expression"] = match.group(1).strip()
                    elif tool_name == "web_fetch":
                        args["url"] = match.group(1).strip()
                    
                    return ToolCall(
                        tool_name=tool_name,
                        arguments=args,
                        confidence=0.9,
                        reasoning=f"Detected {tool_name} intent from pattern match"
                    )
        
        # Check for explicit tool mentions
        for tool_name in self.tools:
            if tool_name in user_lower:
                return ToolCall(
                    tool_name=tool_name,
                    arguments={},
                    confidence=0.7,
                    reasoning=f"Explicit mention of {tool_name}"
                )
        
        return None
    
    def parse_function_call(self, response_text: str) -> Optional[ToolCall]:
        """Parse function call from LLM response."""
        # Look for JSON in response
        json_patterns = [
            r'```json\n({.*?})\n```',
            r'\{[^{}]*"name"\s*:\s*"([^"]+)"[^{}]*"arguments"\s*:\s*(\{.*?\})',
            r'"tool_calls"\s*:\s*\[(.*?)\]',
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                try:
                    if '"name"' in pattern:
                        name = match.group(1)
                        args = json.loads(match.group(2))
                        return ToolCall(tool_name=name, arguments=args, confidence=0.95)
                except:
                    pass
        
        return None
    
    async def execute_tool(self, tool_call: ToolCall) -> Dict:
        """Execute a tool call."""
        tool = self.tools.get(tool_call.tool_name)
        
        if not tool:
            return {"error": f"Tool '{tool_call.tool_name}' not found"}
        
        # Validate required parameters
        missing = []
        for p in tool.parameters:
            if p.required and p.name not in tool_call.arguments:
                missing.append(p.name)
        
        if missing:
            return {"error": f"Missing required parameters: {missing}"}
        
        # Apply defaults
        for p in tool.parameters:
            if p.name not in tool_call.arguments and p.default is not None:
                tool_call.arguments[p.name] = p.default
        
        # Execute function if provided
        try:
            if tool.function:
                result = tool.function(**tool_call.arguments)
                tool_call.result = result
            else:
                # Return mock result for registered tools
                tool_call.result = f"[Mock] Would execute {tool.name} with {tool_call.arguments}"
            
            self.call_history.append(tool_call)
            
            return {
                "status": "ok",
                "tool": tool_call.tool_name,
                "result": tool_call.result,
                "reasoning": tool_call.reasoning
            }
            
        except Exception as e:
            tool_call.error = str(e)
            return {"error": str(e)}
    
    def get_call_history(self) -> List[Dict]:
        """Get tool call history."""
        return [
            {
                "tool": call.tool_name,
                "arguments": call.arguments,
                "result": str(call.result)[:100] if call.result else None,
                "error": call.error,
                "executed_at": call.executed_at
            }
            for call in self.call_history
        ]
    
    def get_stats(self) -> Dict:
        """Get tool usage statistics."""
        tool_counts = {}
        for call in self.call_history:
            tool_counts[call.tool_name] = tool_counts.get(call.tool_name, 0) + 1
        
        return {
            "total_calls": len(self.call_history),
            "tool_counts": tool_counts,
            "available_tools": list(self.tools.keys())
        }


# Singleton
_tool_calling_engine = None

def get_tool_calling_engine() -> OpenAIToolCallingEngine:
    global _tool_calling_engine
    if _tool_calling_engine is None:
        _tool_calling_engine = OpenAIToolCallingEngine()
    return _tool_calling_engine
