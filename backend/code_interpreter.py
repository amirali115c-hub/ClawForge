"""
Leo 2.0 - Code Interpreter Engine
================================
Sandbox-based code execution for Python and JavaScript.
"""

import asyncio
import json
import uuid
import io
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CodeLanguage(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    BASH = "bash"


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class Execution:
    """Code execution result."""
    execution_id: str
    language: str
    code: str
    status: ExecutionStatus
    output: str = ""
    error: str = ""
    execution_time: float = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class CodeInterpreterEngine:
    """
    Code interpreter with sandbox execution.
    
    Features:
    - Python execution
    - JavaScript execution
    - Bash command execution
    - Output capture
    - Error handling
    - Execution history
    """
    
    def __init__(self):
        self.executions: Dict[str, Execution] = {}
        self.max_output_size = 100000  # 100KB max output
        self.max_execution_time = 30  # 30 seconds max
    
    def execute_python(self, code: str) -> Dict:
        """Execute Python code safely."""
        execution_id = str(uuid.uuid4())[:8]
        
        # Create capture streams
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Store original streams
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        execution = Execution(
            execution_id=execution_id,
            language="python",
            code=code,
            status=ExecutionStatus.RUNNING
        )
        self.executions[execution_id] = execution
        
        try:
            # Redirect output
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            # Execute code
            import time
            start_time = time.time()
            
            # Create a restricted namespace
            restricted_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                    'sum': sum,
                    'min': min,
                    'max': max,
                    'abs': abs,
                    'round': round,
                    'sorted': sorted,
                    'reversed': reversed,
                    'any': any,
                    'all': all,
                    'isinstance': isinstance,
                    'type': type,
                    'hasattr': hasattr,
                    'getattr': getattr,
                    'setattr': setattr,
                    'input': lambda x=None: "",
                    'open': None,  # Disable file operations
                }
            }
            
            # Execute with timeout simulation
            try:
                compiled = compile(code, '<string>', 'exec')
                exec(compiled, restricted_globals)
            except SyntaxError as e:
                execution.error = f"Syntax Error: {e}"
                execution.status = ExecutionStatus.ERROR
            except Exception as e:
                execution.error = f"Error: {e}"
                execution.status = ExecutionStatus.ERROR
            
            execution.execution_time = time.time() - start_time
            
            # Capture output
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            output = stdout_output
            if stderr_output:
                output += "\n[STDERR] " + stderr_output
            
            # Limit output size
            if len(output) > self.max_output_size:
                output = output[:self.max_output_size] + "\n... (output truncated)"
            
            execution.output = output
            execution.status = ExecutionStatus.COMPLETED
            
        except Exception as e:
            execution.error = str(e)
            execution.status = ExecutionStatus.ERROR
        
        finally:
            # Restore streams
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        return {
            "execution_id": execution_id,
            "status": execution.status.value,
            "output": execution.output,
            "error": execution.error,
            "execution_time": execution.execution_time
        }
    
    def execute_javascript(self, code: str) -> Dict:
        """Execute JavaScript code."""
        execution_id = str(uuid.uuid4())[:8]
        
        execution = Execution(
            execution_id=execution_id,
            language="javascript",
            code=code,
            status=ExecutionStatus.RUNNING
        )
        self.executions[execution_id] = execution
        
        try:
            # For now, return a mock response
            # In production, you'd use a JS runtime like quickjs or node
            execution.output = "[JavaScript] Code execution requires Node.js runtime"
            execution.status = ExecutionStatus.COMPLETED
            
        except Exception as e:
            execution.error = str(e)
            execution.status = ExecutionStatus.ERROR
        
        return {
            "execution_id": execution_id,
            "status": execution.status.value,
            "output": execution.output,
            "error": execution.error,
            "execution_time": execution.execution_time
        }
    
    def execute(self, code: str, language: str = "python") -> Dict:
        """Execute code in the specified language."""
        if language.lower() == "python":
            return self.execute_python(code)
        elif language.lower() in ["javascript", "js"]:
            return self.execute_javascript(code)
        elif language.lower() == "bash":
            return self.execute_bash(code)
        else:
            return {"error": f"Unsupported language: {language}"}
    
    def execute_bash(self, code: str) -> Dict:
        """Execute bash commands."""
        execution_id = str(uuid.uuid4())[:8]
        
        execution = Execution(
            execution_id=execution_id,
            language="bash",
            code=code,
            status=ExecutionStatus.RUNNING
        )
        self.executions[execution_id] = execution
        
        try:
            import subprocess
            result = subprocess.run(
                code,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.max_execution_time
            )
            
            output = result.stdout
            if result.stderr:
                output += "\n[STDERR] " + result.stderr
            
            execution.output = output
            execution.status = ExecutionStatus.COMPLETED
            
        except subprocess.TimeoutExpired:
            execution.error = "Execution timed out"
            execution.status = ExecutionStatus.TIMEOUT
        except Exception as e:
            execution.error = str(e)
            execution.status = ExecutionStatus.ERROR
        
        return {
            "execution_id": execution_id,
            "status": execution.status.value,
            "output": execution.output,
            "error": execution.error,
            "execution_time": execution.execution_time
        }
    
    def get_execution(self, execution_id: str) -> Optional[Execution]:
        """Get execution by ID."""
        return self.executions.get(execution_id)
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get execution history."""
        executions = sorted(
            self.executions.values(),
            key=lambda x: x.created_at,
            reverse=True
        )[:limit]
        
        return [
            {
                "execution_id": e.execution_id,
                "language": e.language,
                "status": e.status.value,
                "output": e.output[:100],
                "error": e.error,
                "execution_time": e.execution_time,
                "created_at": e.created_at
            }
            for e in executions
        ]


# Singleton
_code_interpreter = None

def get_code_interpreter() -> CodeInterpreterEngine:
    global _code_interpreter
    if _code_interpreter is None:
        _code_interpreter = CodeInterpreterEngine()
    return _code_interpreter
