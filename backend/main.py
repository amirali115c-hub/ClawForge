#!/usr/bin/env python3
"""
ClawForge v4.0 - CLI Entry Point
Run tasks, generate projects, or start the API server.
"""

import sys
import argparse
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from identity import AgentConfig, print_banner
from task_manager import TaskManager
from ollama_client import OllamaClient
from security import SecurityLayer, SecurityMode
from memory import MemoryVault


def run_demo():
    """Run demonstration of ClawForge capabilities."""
    print("\n" + "="*60)
    print("  ClawForge v4.0 - Demo Mode")
    print("="*60 + "\n")
    
    print("Available capabilities:")
    print("  - Task Planning & Execution")
    print("  - File Operations (read/write/move/delete)")
    print("  - Terminal Command Execution")
    print("  - Screen/UI Control")
    print("  - Browser Automation")
    print("  - Code Generation (Python, Node, etc.)")
    print("  - Blog/Content Writing (8 types)")
    print("  - Office Documents (Excel, DOCX, PDF)")
    print("  - Security & Risk Analysis")
    print("\nStart the API server to access full dashboard:")
    print("  python backend/main.py --server")
    print("\nOr use CLI directly:")
    print("  python backend/main.py --task 'Your task here'")
    print("  python backend/main.py --generate 'Create a FastAPI project'")


def run_server():
    """Start the FastAPI server."""
    import uvicorn
    from api import app
    
    print("\nStarting ClawForge API Server...")
    print("   Dashboard: http://127.0.0.1:8000")
    print("   Press Ctrl+C to stop\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)


async def execute_task(task_description: str):
    """Execute a single task."""
    print(f"\nTask: {task_description}\n")
    
    # Initialize components
    config = AgentConfig()
    security = SecurityLayer(mode=SecurityMode.DEVELOPER)
    memory = MemoryVault()
    ollama = OllamaClient()
    task_manager = TaskManager(config, ollama, memory, security)
    
    # Create and run task
    task = task_manager.create_task(task_description)
    print(f"Created task: {task.id}")
    
    # Execute
    result = await task_manager.execute_task(task.id)
    
    print(f"\n{'='*60}")
    print(f"Task Status: {result.status}")
    if result.output:
        print(f"Output: {result.output[:500]}...")
    if result.error:
        print(f"Error: {result.error}")
    print(f"{'='*60}\n")


def generate_project(project_type: str):
    """Generate a project scaffold."""
    print(f"\nGenerating: {project_type}\n")
    
    templates = {
        "fastapi": {
            "description": "FastAPI with authentication",
            "files": ["main.py", "requirements.txt", ".env.example"],
        },
        "react": {
            "description": "React + Vite project",
            "files": ["package.json", "vite.config.js", "src/App.jsx"],
        },
        "node": {
            "description": "Node.js Express project",
            "files": ["index.js", "package.json", ".env.example"],
        },
        "python": {
            "description": "Python package",
            "files": ["__init__.py", "main.py", "requirements.txt"],
        },
    }
    
    template = templates.get(project_type.lower())
    if not template:
        print(f"Unknown project type: {project_type}")
        print(f"Available: {', '.join(templates.keys())}")
        return
    
    print(f"Template: {template['description']}")
    print(f"Files: {', '.join(template['files'])}")
    print("\nProject scaffold generated!")
    print("(Full generation requires task execution)")


def main():
    parser = argparse.ArgumentParser(
        description="ClawForge v4.0 - AI Agent System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backend/main.py --demo              Run demo
  python backend/main.py --server            Start API server
  python backend/main.py --task "Your task"  Execute a task
  python backend/main.py --generate "fastapi" Generate project
        """
    )
    
    parser.add_argument("--demo", action="store_true", help="Run demo")
    parser.add_argument("--server", action="store_true", help="Start API server")
    parser.add_argument("--task", type=str, help="Execute a task")
    parser.add_argument("--generate", type=str, help="Generate a project scaffold")
    
    args = parser.parse_args()
    
    # Show banner
    print_banner()
    
    # Route
    if args.demo:
        run_demo()
    elif args.server:
        run_server()
    elif args.task:
        asyncio.run(execute_task(args.task))
    elif args.generate:
        generate_project(args.generate)
    else:
        parser.print_help()
        print("\nQuick start: python backend/main.py --demo")


if __name__ == "__main__":
    main()
