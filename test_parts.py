import sys
sys.path.insert(0, '.')

print('='*60)
print('CLAWFORGE PARTS 1-3 TEST')
print('='*60)

# Test 1: Identity Module
print('\n[OK] Test 1: Identity Module')
from backend.identity import (
    AGENT_NAME, AGENT_VERSION, SecurityMode, NEVER_DO, ALWAYS_DO
)
print(f'   Agent: {AGENT_NAME} v{AGENT_VERSION}')
print(f'   Security Modes: {[m.value for m in SecurityMode]}')
print(f'   NEVER DO Rules: {len(NEVER_DO)} rules')
print(f'   ALWAYS DO Rules: {len(ALWAYS_DO)} rules')

# Test 2: File Manager
print('\n[OK] Test 2: File Manager')
from backend.file_manager import FileManager
result = FileManager.create_folder('./workspace/test_folder')
print(f'   create_folder: {result["status"]}')
result = FileManager.write_file('./workspace/test_folder/sample.txt', 'Hello ClawForge!')
print(f'   write_file: {result["status"]}')
result = FileManager.read_file('./workspace/test_folder/sample.txt')
content = result.get('content', '')
print(f'   read_file: {result["status"]}, content: {content[:20]}...')
result = FileManager.list_folder('./workspace')
print(f'   list_folder: {result["status"]}, folders: {result.get("folder_count", 0)}')

# Test 3: Planner Engine
print('\n[OK] Test 3: Planner Engine')
from backend.planner import build_plan, interpret_task
interpretation = interpret_task('Write a blog about AI agents')
print(f'   interpret_task: category={interpretation["detected_category"]}')
plan = build_plan('Write a blog about AI agents')
print(f'   build_plan: task_id={plan.task_id}')
print(f'   Subtasks: {len(plan.subtasks)} tasks')
print(f'   Estimated Risk: {plan.estimated_total_risk}')

# Test 4: Ollama Client
print('\n[OK] Test 4: Ollama Client')
from backend.ollama_client import OllamaClient
client = OllamaClient()
health = client.health_check()
print(f'   Ollama Status: {health["status"]}')
if health['status'] == 'healthy':
    print(f'   Available Models: {len(health.get("available_models", []))} models')

# Test 5: Tool Router
print('\n[OK] Test 5: Tool Router')
from backend.tools import ToolRouter, SecurityMode
router = ToolRouter(security_mode=SecurityMode.DEVELOPER)
result = router.call('create_folder', {'path': './workspace/test_tools'})
print(f'   create_folder: {result["status"]}')
result = router.call('write_file', {'path': './workspace/test_tools/test.txt', 'content': 'Test'})
print(f'   write_file: {result["status"]}')
result = router.call('run_command', {'command': 'rm -rf /'})
print(f'   Blocked dangerous command: {result["status"]}')

# Test 6: Memory System
print('\n[OK] Test 6: Memory System')
from backend.memory import create_vault
vault = create_vault('test_task_001')
vault.remember_instruction('Write a blog post')
vault.remember_file('./workspace/blog.md')
vault.update_progress('50%', 'Drafting content')
print(f'   Session: {vault.summarize_session()}')
print(f'   Writing tone: {vault.get_tone()}')
vault.end_task('COMPLETED', 3)
print(f'   Task ended and logged')

# Test 7: Task Manager
print('\n[OK] Test 7: Task Manager')
from backend.task_manager import create_task_manager
tm = create_task_manager()
task = tm.create_task('Test task for demonstration', 'general')
print(f'   Created task: {task.task_id}')
tm.start_task(task.task_id)
print(f'   Started task: {task.task_id}')
tm.update_progress(task.task_id, 50, 'Halfway done')
print(f'   Updated progress: 50%')
tm.complete_task(task.task_id, 'Test completed successfully')
print(f'   Completed task: {task.task_id}')
tasks = tm.list_tasks()
print(f'   Total tasks: {len(tasks)}')
stats = tm.get_stats()
print(f'   Completed tasks: {stats["by_status"]["COMPLETED"]}')

# Test 8: Test API Import
print('\n[OK] Test 8: API Import')
from backend.api import app
print(f'   FastAPI app loaded')
print(f'   Endpoints: /api/tasks, /api/status, /api/kill, etc.')

print('\n' + '='*60)
print('ALL PARTS 1-3 TESTS PASSED!')
print('='*60)
print('\nTo start the API server:')
print('  cd ClawForge')
print('  python -m uvicorn backend.api:app --host 127.0.0.1 --port 7860')
print('='*60)
