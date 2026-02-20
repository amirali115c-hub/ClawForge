# smart_router.py - Intelligent Model Router for Leo 2.0

"""
Automatically selects the best model based on task complexity and requirements.
Routes requests to optimal Ollama models without manual intervention.
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# ============================================================================
# TASK COMPLEXITY LEVELS
# ============================================================================

class ComplexityLevel(Enum):
    """Classification of task complexity."""
    SIMPLE = 1      # Quick questions, basic chat
    MODERATE = 2    # Multi-step reasoning, coding
    COMPLEX = 3     # Deep analysis, large codebases, research
    EXPERT = 4      # Advanced reasoning, system design


# ============================================================================
# TASK TYPE CLASSIFICATION
# ============================================================================

class TaskType(Enum):
    """Types of tasks Leo can perform."""
    GENERAL_CHAT = "general_chat"
    CODING = "coding"
    DEBUGGING = "debugging"
    ANALYSIS = "analysis"
    RESEARCH = "research"
    PLANNING = "planning"
    WRITING = "writing"
    FILE_OPERATIONS = "file_operations"
    WEB_SEARCH = "web_search"
    EXECUTION = "execution"


# ============================================================================
# KEYWORD PATTERNS FOR TASK DETECTION
# ============================================================================

TASK_KEYWORDS = {
    TaskType.CODING: [
        r'\b(code|program|function|class|method|api|debug|bug|error|fix|syntax|compile|build|deploy|devops|repository|git|javascript|python|react|node|sql|database|frontend|backend|fullstack|framework|library|package|module|import|export|variable|constant|loop|condition|algorithm|data structure)\b',
        r'\b(write|create|build|develop|implement|refactor|optimize)\b(?:\s+\w+){0,3}\s*(?:code|program|function|app|application|software|tool)',
    ],
    
    TaskType.DEBUGGING: [
        r'\b(debug|fix|error|bug|issue|problem|exception|traceback|crash|not working|doesn\'t work|failing|broken|wrong|unexpected)\b',
        r'\b(why|how to fix|what\'s wrong|what caused|debugging|troubleshoot)\b',
    ],
    
    TaskType.ANALYSIS: [
        r'\b(analyze|compare|evaluate|assess|review|examine|investigate|understand|explain|difference|pros cons|benefits drawbacks|tradeoff|performance|scalability|security|architecture|design pattern)\b',
        r'\b(why is|how does|what is the|explain the|describe the)\b',
    ],
    
    TaskType.RESEARCH: [
        r'\b(search|find|lookup|look up|research|information|data|statistics|facts|latest|recent|news|trends|best practices|alternatives|options|comparisons)\b',
        r'\b(what are|list|all the|every|complete|comprehensive)\b',
    ],
    
    TaskType.PLANNING: [
        r'\b(plan|plan out|design|strategy|roadmap|steps|workflow|task list|todo|schedule|prioritize|organize|coordinate)\b',
        r'\b(how to approach|what steps|first|then|after|before)\b',
    ],
    
    TaskType.WRITING: [
        r'\b(write|compose|draft|create|generate|produce|content|article|blog|post|documentation|readme|comments|summary|outline)\b',
        r'\b(essay|report|letter|email|message|text|description)\b',
    ],
    
    TaskType.FILE_OPERATIONS: [
        r'\b(read|write|edit|modify|update|delete|remove|create|file|folder|directory|path|save|open|close|copy|move|rename)\b',
        r'\b(\.(txt|csv|json|xml|html|css|js|py|md|yaml|yml|ini|conf|config))\b',
    ],
    
    TaskType.WEB_SEARCH: [
        r'\b(search|find on web|lookup online|google|browse|visit|url|link|website|page|article|blog post)\b',
        r'\b(what\'s new|latest|recent updates|news|trends)\b',
    ],
    
    TaskType.EXECUTION: [
        r'\b(run|execute|start|stop|restart|kill|process|task|job|batch|automation|script|command|terminal|shell|powershell|cmd)\b',
    ],
}


# ============================================================================
# COMPLEXITY INDICATORS
# ============================================================================

COMPLEXITY_INDICATORS = {
    ComplexityLevel.SIMPLE: [
        r'^(hi|hello|hey|how are you|what\'s up|good morning|good afternoon|good evening)\b',
        r'^(yes|no|sure|okay|ok|thanks|thank you)\b',
        r'\b(who are you|what can you do|tell me about yourself)\b',
        r'^.{1,50}$',  # Very short messages
    ],
    
    ComplexityLevel.MODERATE: [
        r'.{100,300}',  # Medium length
        r'\band|or|but|then|so|because|therefore|however\b',  # Logical connectors
        r'\bexplain|describe|tell me|help me|can you\b',
    ],
    
    ComplexityLevel.COMPLEX: [
        r'.{300,1000}',  # Long messages
        r'\b(detailed|comprehensive|complete|thorough|in-depth|step by step)\b',
        r'\b(architecture|system design|microservices|distributed|performance optimization|scalability|security analysis)\b',
        r'(?s).{20,}',  # Multi-sentence with complexity
    ],
    
    ComplexityLevel.EXPERT: [
        r'.{1000,}',  # Very long/complex
        r'\b(research paper|technical specification|design document|production system|critical path|enterprise)\b',
        r'\b(advanced|expert|professional|enterprise-grade|mission-critical)\b',
    ],
}


# ============================================================================
# MODEL CAPABILITIES
# ============================================================================

MODEL_CAPABILITIES = {
    "ollama/qwen2.5:3b": {
        "context_window": 131072,
        "max_tokens": 8192,
        "strengths": ["fast", "efficient", "general_chat", "simple_coding", "quick_tasks"],
        "weaknesses": ["deep_reasoning", "complex_analysis"],
        "ram_usage_gb": 2,
        "speed_rating": 5,  # 1-5, 5 is fastest
        "complexity_limit": ComplexityLevel.MODERATE,
    },
    
    "ollama/phi3:mini": {
        "context_window": 4096,
        "max_tokens": 2048,
        "strengths": ["ultra_fast", "lightweight", "simple_chat", "quick_responses"],
        "weaknesses": ["limited_context", "basic_reasoning"],
        "ram_usage_gb": 2,
        "speed_rating": 5,
        "complexity_limit": ComplexityLevel.SIMPLE,
    },
    
    "ollama/qwen3:8b": {
        "context_window": 131072,
        "max_tokens": 8192,
        "strengths": ["deep_reasoning", "coding", "analysis", "planning", "complex_tasks"],
        "weaknesses": [],
        "ram_usage_gb": 5,
        "speed_rating": 4,
        "complexity_limit": ComplexityLevel.EXPERT,
    },
    
    "ollama/llama3.2:3b": {
        "context_window": 131072,
        "max_tokens": 8192,
        "strengths": ["balanced", "coding", "chat", "reasoning"],
        "weaknesses": ["very_complex"],
        "ram_usage_gb": 3,
        "speed_rating": 4,
        "complexity_limit": ComplexityLevel.COMPLEX,
    },
}


# ============================================================================
# SMART ROUTER CLASS
# ============================================================================

class SmartModelRouter:
    """
    Intelligently routes requests to optimal models based on task analysis.
    """
    
    def __init__(self):
        self.model_order = [
            "ollama/qwen2.5:3b",      # Fastest, default
            "ollama/llama3.2:3b",     # Balanced
            "ollama/qwen3:8b",        # Most capable
        ]
        
        self.current_model = "ollama/qwen2.5:3b"
        self.last_switch = datetime.now()
        self.switch_count = 0
        self.analysis_count = 0
        
        # Statistics
        self.route_history = []
        self.task_distribution = {task.value: 0 for task in TaskType}
        self.complexity_distribution = {level.value: 0 for level in ComplexityLevel}
    
    # =========================================================================
    # MAIN ROUTING METHOD
    # =========================================================================
    
    def analyze_and_route(self, message: str, context: str = "") -> Dict:
        """
        Analyze the request and select the optimal model.
        
        Args:
            message: The user's message/request
            context: Previous conversation context (optional)
        
        Returns:
            Dict with routing decision and reasoning
        """
        self.analysis_count += 1
        
        # Step 1: Detect task type
        task_type = self._detect_task_type(message)
        self.task_distribution[task_type.value] += 1
        
        # Step 2: Analyze complexity
        complexity = self._analyze_complexity(message, context)
        self.complexity_distribution[complexity.value] += 1
        
        # Step 3: Select optimal model
        optimal_model = self._select_model(task_type, complexity)
        
        # Step 4: Check if switch is needed
        needs_switch = optimal_model != self.current_model
        
        if needs_switch:
            self.switch_count += 1
            self.last_switch = datetime.now()
            old_model = self.current_model
            self.current_model = optimal_model
        else:
            old_model = None
        
        # Build route info
        route_info = {
            "current_model": self.current_model,
            "task_type": task_type.value,
            "complexity": complexity.value,
            "complexity_label": complexity.name,
            "model_recommendation": optimal_model,
            "needs_switch": needs_switch,
            "switch_reason": self._get_switch_reason(task_type, complexity) if needs_switch else None,
            "confidence": self._calculate_confidence(task_type, complexity),
            "alternative_models": self._get_alternatives(task_type, complexity),
        }
        
        # Log route
        self.route_history.append({
            "timestamp": datetime.now().isoformat(),
            "message_length": len(message),
            "task_type": task_type.value,
            "complexity": complexity.value,
            "model_selected": optimal_model,
            "was_switch": needs_switch,
        })
        
        # Keep only last 100 entries
        if len(self.route_history) > 100:
            self.route_history = self.route_history[-100:]
        
        return route_info
    
    # =========================================================================
    # TASK TYPE DETECTION
    # =========================================================================
    
    def _detect_task_type(self, message: str) -> TaskType:
        """Detect the type of task from the message."""
        message_lower = message.lower()
        
        # Score each task type
        task_scores = {task: 0 for task in TaskType}
        
        for task_type, keywords in TASK_KEYWORDS.items():
            for pattern in keywords:
                matches = len(re.findall(pattern, message_lower, re.IGNORECASE))
                task_scores[task_type] += matches
        
        # Return task with highest score, default to GENERAL_CHAT
        max_score = max(task_scores.values())
        if max_score > 0:
            for task, score in task_scores.items():
                if score == max_score:
                    return task
        
        return TaskType.GENERAL_CHAT
    
    # =========================================================================
    # COMPLEXITY ANALYSIS
    # =========================================================================
    
    def _analyze_complexity(self, message: str, context: str = "") -> ComplexityLevel:
        """Analyze the complexity of the request."""
        combined_text = f"{context} {message}".strip()
        
        # Score each complexity level
        complexity_scores = {level: 0 for level in ComplexityLevel}
        
        for level, indicators in COMPLEXITY_INDICATORS.items():
            for pattern in indicators:
                matches = len(re.findall(pattern, combined_text, re.IGNORECASE | re.DOTALL))
                complexity_scores[level] += matches
        
        # Return highest matching complexity
        max_score = max(complexity_scores.values())
        if max_score > 0:
            for level, score in complexity_scores.items():
                if score == max_score:
                    return level
        
        return ComplexityLevel.SIMPLE
    
    # =========================================================================
    # MODEL SELECTION
    # =========================================================================
    
    def _select_model(self, task_type: TaskType, complexity: ComplexityLevel) -> str:
        """
        Select the optimal model based on task and complexity.
        """
        # Rule 1: Simple tasks always use fastest model
        if complexity == ComplexityLevel.SIMPLE:
            return "ollama/qwen2.5:3b"
        
        # Rule 2: Coding tasks need qwen3:8b for complex coding
        if task_type in [TaskType.CODING, TaskType.DEBUGGING]:
            if complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.EXPERT]:
                return "ollama/qwen3:8b"
            else:
                return "ollama/llama3.2:3b"
        
        # Rule 3: Analysis needs qwen3:8b
        if task_type in [TaskType.ANALYSIS, TaskType.RESEARCH]:
            if complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.EXPERT]:
                return "ollama/qwen3:8b"
            else:
                return "ollama/llama3.2:3b"
        
        # Rule 4: Planning benefits from qwen3:8b
        if task_type == TaskType.PLANNING:
            if complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.EXPERT]:
                return "ollama/qwen3:8b"
            else:
                return "ollama/llama3.2:3b"
        
        # Rule 5: Default to qwen2.5:3b for simple tasks
        if complexity == ComplexityLevel.SIMPLE:
            return "ollama/qwen2.5:3b"
        
        # Rule 6: Moderate tasks use balanced model
        if complexity == ComplexityLevel.MODERATE:
            return "ollama/llama3.2:3b"
        
        # Default fallback
        return "ollama/llama3.2:3b"
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _get_switch_reason(self, task_type: TaskType, complexity: ComplexityLevel) -> str:
        """Get human-readable reason for model switch."""
        reasons = []
        
        if task_type != TaskType.GENERAL_CHAT:
            reasons.append(f"{task_type.value.replace('_', ' ').title()}")
        
        if complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.EXPERT]:
            reasons.append("complex task")
        elif complexity in [ComplexityLevel.MODERATE]:
            reasons.append("moderate complexity")
        
        if not reasons:
            return "Performance optimization"
        
        return " and ".join(reasons)
    
    def _calculate_confidence(self, task_type: TaskType, complexity: ComplexityLevel) -> float:
        """Calculate confidence score for routing decision (0-1)."""
        base_confidence = 0.7
        
        # Higher confidence for clear task types
        if task_type != TaskType.GENERAL_CHAT:
            base_confidence += 0.1
        
        # Higher confidence for clear complexity
        if complexity in [ComplexityLevel.SIMPLE, ComplexityLevel.EXPERT]:
            base_confidence += 0.1
        else:
            base_confidence += 0.05
        
        return min(base_confidence, 0.95)
    
    def _get_alternatives(self, task_type: TaskType, complexity: ComplexityLevel) -> List[str]:
        """Get alternative model recommendations."""
        alternatives = []
        
        primary = self._select_model(task_type, complexity)
        
        for model in self.model_order:
            if model != primary:
                capabilities = MODEL_CAPABILITIES.get(model, {})
                model_limit = capabilities.get("complexity_limit", ComplexityLevel.EXPERT)
                if model_limit.value >= complexity.value:
                    alternatives.append(model)
        
        return alternatives[:2]  # Return max 2 alternatives
    
    def get_model_info(self, model_name: str) -> Dict:
        """Get information about a specific model."""
        return MODEL_CAPABILITIES.get(model_name, {"error": "Model not found"})
    
    # =========================================================================
    # STATISTICS AND REPORTING
    # =========================================================================
    
    def get_statistics(self) -> Dict:
        """Get routing statistics."""
        total_routes = len(self.route_history)
        
        return {
            "current_model": self.current_model,
            "total_analyses": self.analysis_count,
            "total_switches": self.switch_count,
            "last_switch": self.last_switch.isoformat() if self.last_switch else None,
            "task_distribution": self.task_distribution,
            "complexity_distribution": self.complexity_distribution,
            "model_usage": self._get_model_usage(),
            "switch_rate": round(self.switch_count / max(total_routes, 1) * 100, 1),
        }
    
    def _get_model_usage(self) -> Dict[str, int]:
        """Get model usage statistics from route history."""
        usage = {model: 0 for model in self.model_order}
        
        for route in self.route_history:
            model = route.get("model_selected")
            if model in usage:
                usage[model] += 1
        
        return usage
    
    def get_status(self) -> Dict:
        """Get router status for API."""
        stats = self.get_statistics()
        
        return {
            "router_active": True,
            "current_model": self.current_model,
            "available_models": list(MODEL_CAPABILITIES.keys()),
            "statistics": stats,
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_router() -> SmartModelRouter:
    """Create and return a new SmartModelRouter instance."""
    return SmartModelRouter()


def quick_route(message: str, context: str = "") -> str:
    """
    Quick one-line routing function.
    
    Usage:
        model = quick_route("Write me a Python function", "")
        # Returns: "ollama/qwen3:8b"
    """
    router = SmartModelRouter()
    result = router.analyze_and_route(message, context)
    return result["model_recommendation"]


if __name__ == "__main__":
    # Test the router
    router = SmartModelRouter()
    
    test_messages = [
        "Hello! How are you today?",
        "Write a Python function to calculate factorial",
        "Debug this code: for i in range(10) print(i)",
        "Design a microservices architecture for an e-commerce system",
        "What are the best practices for React performance optimization?",
        "Quick question: what's 2+2?",
        "Analyze the security vulnerabilities in this authentication system",
        "Create a comprehensive roadmap for building a SaaS product",
    ]
    
    print(" Smart Model Router - Test")
    print("=" * 60)
    
    for msg in test_messages:
        result = router.analyze_and_route(msg)
        print(f"\n Message: {msg[:50]}...")
        print(f"   Task: {result['task_type']}")
        print(f"   Complexity: {result['complexity_label']}")
        print(f"   Model: {result['model_recommendation']}")
        print(f"   Switch: {'' if result['needs_switch'] else ''}")
        print(f"   Confidence: {result['confidence']:.0%}")
    
    print("\n" + "=" * 60)
    print("\n Statistics:")
    stats = router.get_statistics()
    for key, value in stats.items():
        if key != "task_distribution" and key != "complexity_distribution":
            print(f"   {key}: {value}")
