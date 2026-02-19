# backend/__init__.py - ClawForge Backend Package

"""
ClawForge - Production-grade Autonomous AI Agent Framework

Backend modules for task management, tool execution, and API server.
"""

from .identity import (
    AGENT_NAME,
    AGENT_VERSION,
    AGENT_ROLE,
    CORE_MISSION,
    CAPABILITIES,
    WORKSPACE_PATHS,
    WORKSPACE_ROOT,
    MEMORY_FILE,
    SecurityMode,
    TaskStatus,
    NEVER_DO,
    ALWAYS_DO,
    OUTPUT_SECTIONS,
    REQUIRED_MODULES,
    format_response_template,
    initialize_workspace,
    display_agent_info,
    print_execution_loop,
    verify_modules
)

from .file_manager import (
    FileManager,
    read_file,
    write_file,
    create_folder,
    delete_file,
    list_folder,
    WorkspaceViolationError
)

from .planner import (
    PlannerEngine,
    TaskPlan,
    SubTask,
    TaskStatus as PlannerTaskStatus,
    interpret_task,
    build_plan,
    generate_task_id,
    plan_to_markdown
)

from .ollama_client import (
    OllamaClient,
    CLAWFORGE_SYSTEM_PROMPT,
    SUPPORTED_MODELS,
    MODEL_ROUTING,
    health_check,
    generate,
    route_and_generate
)

from .tools import (
    ToolRouter,
    SecurityMode as ToolSecurityMode,
    ALL_TOOLS,
    DISABLED_TOOLS_BY_MODE,
    create_router
)

from .memory import (
    MemoryVault,
    ShortTermMemory,
    LongTermMemory,
    create_vault
)

from .task_manager import (
    TaskManager,
    Task,
    TaskStatus as ManagerTaskStatus,
    create_task_manager
)

from .api import app

from .blog_writer import (
    BlogWriter,
    BlogOutput,
    BLOG_TYPES,
    create_blog
)

from .code_runner import (
    CodeRunner,
    DeveloperAssistant,
    run_code_project
)

from .office_modules import (
    ExcelSolver,
    DocumentWriter,
    PDFBuilder,
    UIController,
    create_excel,
    create_document,
    create_pdf
)

from .risk_analyzer import (
    CommandRiskAnalyzer,
    analyze_command,
    check_file,
    BLOCKED_PATTERNS,
    DANGEROUS_EXTENSIONS,
    RISK_WEIGHTS
)

from .permissions import (
    PermissionManager,
    ApprovalRecord,
    PERMISSION_CATEGORIES,
    request_permission,
    check_permission
)

from .security import (
    SecurityLayer,
    MalwareDefenseLayer,
    DataExfiltrationPrevention,
    PromptInjectionProtector,
    QuarantineSystem,
    RiskScoringEngine,
    check_command_security,
    check_path_security,
    check_input_security
)

from .api_client import (
    BaseAPIClient,
    OpenAICompatClient,
    SiliconFlowClient,
    OpenRouterClient,
    APIClient,
    get_api_client
)

from .nvidia_client import (
    NvidiaAPIClient,
    UnifiedAPIClient,
    get_unified_client,
    test_nvidia_api_key
)

# Consolidated Features (from features.py)
from .features import (
    get_memory_stats,
    search_memories,
    add_memory,
    get_memories,
    delete_memory,
    get_privacy_settings,
    update_privacy_settings,
    export_memory_data,
    import_memory_data,
    clear_memory_data,
    add_conversation,
    get_conversations,
    web_search,
    fetch_url,
    get_git_status,
    git_commit,
    text_to_speech,
    list_voices,
    read_file_content,
    edit_file_content,
    generate_plan,
    longterm_memory,
)

__version__ = "4.0"
__author__ = "ClawForge Team"

__all__ = [
    # Identity
    "AGENT_NAME",
    "AGENT_VERSION",
    "AGENT_ROLE",
    "CORE_MISSION",
    "CAPABILITIES",
    "WORKSPACE_PATHS",
    "WORKSPACE_ROOT",
    "MEMORY_FILE",
    "SecurityMode",
    "TaskStatus",
    "NEVER_DO",
    "ALWAYS_DO",
    "OUTPUT_SECTIONS",
    "REQUIRED_MODULES",
    "format_response_template",
    "initialize_workspace",
    "display_agent_info",
    "print_execution_loop",
    "verify_modules",
    
    # File Manager
    "FileManager",
    "read_file",
    "write_file",
    "create_folder",
    "delete_file",
    "list_folder",
    "WorkspaceViolationError",
    
    # Planner
    "PlannerEngine",
    "TaskPlan",
    "SubTask",
    "PlannerTaskStatus",
    "interpret_task",
    "build_plan",
    "generate_task_id",
    "plan_to_markdown",
    
    # Ollama
    "OllamaClient",
    "CLAWFORGE_SYSTEM_PROMPT",
    "SUPPORTED_MODELS",
    "MODEL_ROUTING",
    "health_check",
    "generate",
    "route_and_generate",
    
    # Tools
    "ToolRouter",
    "ToolSecurityMode",
    "ALL_TOOLS",
    "DISABLED_TOOLS_BY_MODE",
    "create_router",
    
    # Memory
    "MemoryVault",
    "ShortTermMemory",
    "LongTermMemory",
    "create_vault",
    
    # Task Manager
    "TaskManager",
    "Task",
    "ManagerTaskStatus",
    "create_task_manager",
    
    # API
    "app",
    
    # Blog Writer
    "BlogWriter",
    "BlogOutput",
    "BLOG_TYPES",
    "create_blog",
    
    # Code Runner
    "CodeRunner",
    "DeveloperAssistant",
    "run_code_project",
    
    # Office Modules
    "ExcelSolver",
    "DocumentWriter",
    "PDFBuilder",
    "UIController",
    "create_excel",
    "create_document",
    "create_pdf",
    
    # Risk Analyzer
    "CommandRiskAnalyzer",
    "analyze_command",
    "check_file",
    "BLOCKED_PATTERNS",
    "DANGEROUS_EXTENSIONS",
    "RISK_WEIGHTS",
    
    # Permission Manager
    "PermissionManager",
    "ApprovalRecord",
    "PERMISSION_CATEGORIES",
    "request_permission",
    "check_permission",
    
    # Security Layer
    "SecurityLayer",
    "MalwareDefenseLayer",
    "DataExfiltrationPrevention",
    "PromptInjectionProtector",
    "QuarantineSystem",
    "RiskScoringEngine",
    "check_command_security",
    "check_path_security",
    "check_input_security",
    
    # NVIDIA API
    "NvidiaAPIClient",
    "UnifiedAPIClient",
    "get_unified_client",
    "test_nvidia_api_key",
    
    # Features (Consolidated)
    "get_memory_stats",
    "search_memories",
    "add_memory",
    "get_memories",
    "delete_memory",
    "get_privacy_settings",
    "update_privacy_settings",
    "export_memory_data",
    "import_memory_data",
    "clear_memory_data",
    "add_conversation",
    "get_conversations",
    "web_search",
    "fetch_url",
    "get_git_status",
    "git_commit",
    "text_to_speech",
    "list_voices",
    "read_file_content",
    "edit_file_content",
    "generate_plan",
    "longterm_memory",
]