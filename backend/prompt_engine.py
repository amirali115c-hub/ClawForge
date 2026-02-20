"""
Leo 2.0 Prompt Understanding Engine
Based on OpenClaw's mechanism - Parses, understands, and routes prompts intelligently.
"""

import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib


class IntentType(Enum):
    """Types of user intents."""
    QUESTION = "question"
    COMMAND = "command"
    REQUEST = "request"
    CHAT = "chat"
    CREATIVE = "creative"
    CODE = "code"
    ANALYSIS = "analysis"
    PLANNING = "planning"
    LEARNING = "learning"
    SEARCH = "search"
    UNKNOWN = "unknown"


class ComplexityLevel(Enum):
    """Complexity levels for model routing."""
    TRIVIAL = 1
    SIMPLE = 2
    MODERATE = 3
    COMPLEX = 4
    EXPERT = 5


@dataclass
class ParsedIntent:
    """Parsed intent from user message."""
    raw_message: str
    intent_type: IntentType
    entities: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    language: str = "en"
    sentiment: str = "neutral"
    urgency: str = "normal"
    complexity: ComplexityLevel = ComplexityLevel.MODERATE
    context_needed: List[str] = field(default_factory=list)
    action_required: bool = False
    requires_memory: bool = False
    requires_web: bool = False
    requires_code: bool = False
    requires_planning: bool = False


@dataclass
class ContextItem:
    """Context item from memory or session."""
    source: str  # memory, session, user_config
    type: str  # fact, preference, history, instruction
    content: str
    relevance: float  # 0-1 score
    timestamp: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)


class PromptUnderstandingEngine:
    """
    Core engine for understanding user prompts.
    Mirrors OpenClaw's prompt understanding mechanism.
    """
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path(".")
        
        # Intent patterns (from OpenClaw)
        self.intent_patterns = {
            IntentType.QUESTION: [
                r'\b(what|who|where|when|why|how|which)\b',
                r'\?$',
                r'\bcan you explain\b',
                r'\bdo you know\b',
                r'\btell me about\b',
                r'\bi want to know\b',
            ],
            IntentType.COMMAND: [
                r'\b(do|make|create|write|build|run|execute)\b',
                r'\bplease\b',
                r'\bcan you\b',
                r'\bi need you to\b',
                r'\bstart\b',
                r'\bstop\b',
            ],
            IntentType.REQUEST: [
                r'\bi want\b',
                r'\bi would like\b',
                r'\bcould you\b',
                r'\bwould you\b',
                r'\bplease provide\b',
                r'\bgive me\b',
            ],
            IntentType.CODE: [
                r'\bcode\b',
                r'\bpython\b',
                r'\bjavascript\b',
                r'\bfunction\b',
                r'\bdebug\b',
                r'\berror\b',
                r'\bcompile\b',
                r'\bapi\b',
                r'\bclass\b',
                r'\bimport\b',
                r'\bdef\b',
                r'\bfunction\b',
            ],
            IntentType.CREATIVE: [
                r'\bstory\b',
                r'\bpoem\b',
                r'\bsong\b',
                r'\bwrite\b',
                r'\bcreative\b',
                r'\bimagine\b',
                r'\bdesign\b',
                r'\bart\b',
            ],
            IntentType.ANALYSIS: [
                r'\banalyze\b',
                r'\bcompare\b',
                r'\bevaluate\b',
                r'\bassess\b',
                r'\breview\b',
                r'\bopinion\b',
                r'\bthink about\b',
            ],
            IntentType.PLANNING: [
                r'\bplan\b',
                r'\bschedule\b',
                r'\borga[nz]e\b',
                r'\bstep by step\b',
                r'\b roadmap\b',
                r'\btimeline\b',
            ],
            IntentType.SEARCH: [
                r'\bsearch\b',
                r'\bfind\b',
                r'\blook up\b',
                r'\binternet\b',
                r'\bweb\b',
                r'\blatest\b',
                r'\brecent\b',
            ],
            IntentType.LEARNING: [
                r'\blearn\b',
                r'\bexplain\b',
                r'\bteach me\b',
                r'\bhow does\b',
                r'\bunderstand\b',
                r'\bhelp me understand\b',
            ],
        }
        
        # Keyword extractors
        self.keywords_pattern = re.compile(
            r'\b[a-zA-Z]{3,}\b',
            re.IGNORECASE
        )
        
        # Entity patterns
        self.entity_patterns = {
            'email': r'\b[\w.-]+@[\w.-]+\.\w+\b',
            'url': r'https?://[^\s]+',
            'file_path': r'(?:\./|/|\\)[^\s]+',
            'code': r'`[^`]+`',
            'number': r'\b\d+\.?\d*\b',
        }
        
        # Complexity indicators
        self.complexity_indicators = {
            ComplexityLevel.TRIVIAL: [
                r'\b(yes|no|ok|okay|yeah|nope)\b',
                r'^[a-zA-Z\s]{1,10}$',
            ],
            ComplexityLevel.SIMPLE: [
                r'\bhello|hi|hey\b',
                r'\bhow are you\b',
                r'\bthanks?\b',
            ],
            ComplexityLevel.MODERATE: [
                r'\?$',
                r'\b(because|however|although)\b',
            ],
            ComplexityLevel.COMPLEX: [
                r'\bhowever\b.*\b(because|therefore)\b',
                r'\band\b.*\b(because|therefore)\b',
                r'\b(what if|suppose|imagine)\b',
                r'\bmultiple\b.*\b(different|various)\b',
            ],
            ComplexityLevel.EXPERT: [
                r'\b(architect|design|implement|optimize)\b.*\b(scalable|distributed|concurrent)\b',
                r'\b(machine learning|neural network|deep learning)\b',
                r'\b(multi-thread|async|parallel)\b',
                r'\b(optimize|benchmark|profil)\b',
            ],
        }
        
        # Language detection patterns
        self.language_patterns = {
            'en': r'\b(the|is|are|was|were|have|has|been)\b',
            'ur': r'\b(کا|ہے|ہیں|کرتا|کرتی)\b',
            'es': r'\b(el|la|los|las|es|son|tiene)\b',
            'fr': r'\b(le|la|les|est|sont|a|ont)\b',
            'de': r'\b(der|die|das|ist|sind|hat|haben)\b',
        }
        
        # Urgency patterns
        self.urgency_patterns = {
            'urgent': [r'\burgent\b', r'\basap\b', r'\bimmediately\b', r'\bnow\b', r'\bquick\b'],
            'high': [r'\bsoon\b', r'\btoday\b', r'\bimportant\b'],
            'normal': [],
            'low': [r'\bwhenever\b', r'\blater\b', r'\bno rush\b'],
        }
        
        # Context requirements
        self.context_requirements = {
            IntentType.QUESTION: ['memory', 'knowledge'],
            IntentType.COMMAND: ['history', 'preferences'],
            IntentType.REQUEST: ['preferences', 'history'],
            IntentType.CODE: ['code_history', 'preferences'],
            IntentType.CREATIVE: ['style_preferences'],
            IntentType.ANALYSIS: ['data', 'history'],
            IntentType.PLANNING: ['goals', 'schedule'],
            IntentType.SEARCH: [],
            IntentType.LEARNING: ['knowledge_base'],
        }
        
    def parse(self, message: str, session_context: Dict = None) -> ParsedIntent:
        """
        Main entry point for parsing user messages.
        Mirrors OpenClaw's parse mechanism.
        
        Args:
            message: Raw user message
            session_context: Current session context
            
        Returns:
            ParsedIntent with full analysis
        """
        message = message.strip()
        
        # Stage 1: Basic parsing
        entities = self._extract_entities(message)
        keywords = self._extract_keywords(message)
        language = self._detect_language(message)
        
        # Stage 2: Intent detection
        intent_type = self._detect_intent(message, entities, keywords)
        
        # Stage 3: Complexity analysis
        complexity = self._analyze_complexity(message, intent_type)
        
        # Stage 4: Urgency detection
        urgency = self._detect_urgency(message)
        
        # Stage 5: Feature detection
        requires_web = self._detect_web_search(message)
        requires_code = self._detect_code_execution(message)
        requires_planning = self._detect_planning(message)
        requires_memory = self._detect_memory_need(message, intent_type)
        
        # Stage 6: Context requirements
        context_needed = self._get_context_requirements(intent_type, message)
        
        return ParsedIntent(
            raw_message=message,
            intent_type=intent_type,
            entities=entities,
            keywords=keywords,
            language=language,
            sentiment=self._analyze_sentiment(message),
            urgency=urgency,
            complexity=complexity,
            context_needed=context_needed,
            action_required=intent_type in [IntentType.COMMAND, IntentType.REQUEST],
            requires_memory=requires_memory,
            requires_web=requires_web,
            requires_code=requires_code,
            requires_planning=requires_planning,
        )
    
    def _extract_entities(self, message: str) -> List[str]:
        """Extract named entities from message."""
        entities = []
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, message)
            entities.extend(matches)
        return list(set(entities))
    
    def _extract_keywords(self, message: str) -> List[str]:
        """Extract significant keywords from message."""
        # Remove common stopwords
        stopwords = {
            'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'need', 'dare', 'ought', 'used',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
            'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between',
            'and', 'but', 'or', 'nor', 'so', 'yet', 'both',
            'either', 'neither', 'not', 'only', 'just',
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours',
            'you', 'your', 'yours', 'he', 'him', 'his',
            'she', 'her', 'hers', 'it', 'its', 'they', 'them',
            'what', 'which', 'who', 'whom', 'this', 'that',
            'these', 'those', 'am', 'a', 'an',
        }
        
        words = self.keywords_pattern.findall(message.lower())
        keywords = [w for w in words if w.lower() not in stopwords and len(w) > 2]
        return list(set(keywords))
    
    def _detect_language(self, message: str) -> str:
        """Detect the language of the message."""
        message_lower = message.lower()
        scores = {}
        
        for lang, pattern in self.language_patterns.items():
            matches = re.findall(pattern, message_lower)
            scores[lang] = len(matches)
        
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return 'en'
    
    def _detect_intent(self, message: str, entities: List[str], keywords: List[str]) -> IntentType:
        """Detect the user's intent from the message."""
        message_lower = message.lower()
        
        # Check each intent type
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent_type
        
        # Check for mixed intents
        code_indicators = any(k in message_lower for k in ['code', 'python', 'function', 'debug'])
        analysis_indicators = any(k in message_lower for k in ['analyze', 'compare', 'evaluate'])
        planning_indicators = any(k in message_lower for k in ['plan', 'schedule', 'steps'])
        
        if code_indicators and entities:
            return IntentType.CODE
        elif analysis_indicators:
            return IntentType.ANALYSIS
        elif planning_indicators:
            return IntentType.PLANNING
        elif len(message.split()) < 5:
            return IntentType.CHAT
        
        return IntentType.REQUEST
    
    def _analyze_complexity(self, message: str, intent_type: IntentType) -> ComplexityLevel:
        """Analyze the complexity of the request."""
        message_lower = message.lower()
        
        # Check expert level
        for pattern in self.complexity_indicators[ComplexityLevel.EXPERT]:
            if re.search(pattern, message_lower):
                return ComplexityLevel.EXPERT
        
        # Check complex level
        for pattern in self.complexity_indicators[ComplexityLevel.COMPLEX]:
            if re.search(pattern, message_lower):
                return ComplexityLevel.COMPLEX
        
        # Check moderate level
        for pattern in self.complexity_indicators[ComplexityLevel.MODERATE]:
            if re.search(pattern, message_lower):
                return ComplexityLevel.MODERATE
        
        # Check simple level
        for pattern in self.complexity_indicators[ComplexityLevel.SIMPLE]:
            if re.search(pattern, message_lower):
                return ComplexityLevel.SIMPLE
        
        # Check trivial level
        for pattern in self.complexity_indicators[ComplexityLevel.TRIVIAL]:
            if re.search(pattern, message_lower):
                return ComplexityLevel.TRIVIAL
        
        # Default based on intent type
        if intent_type in [IntentType.CODE, IntentType.ANALYSIS, IntentType.PLANNING]:
            return ComplexityLevel.MODERATE
        elif intent_type == IntentType.CHAT:
            return ComplexityLevel.SIMPLE
        else:
            return ComplexityLevel.MODERATE
    
    def _detect_urgency(self, message: str) -> str:
        """Detect urgency level of the request."""
        message_lower = message.lower()
        
        for urgency, patterns in self.urgency_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return urgency
        
        return 'normal'
    
    def _detect_web_search(self, message: str) -> bool:
        """Check if request requires web search."""
        web_keywords = ['search', 'find', 'latest', 'recent', 'web', 'internet', 
                       'news', 'current', 'today', 'weather', 'stock', 'price']
        return any(kw in message.lower() for kw in web_keywords)
    
    def _detect_code_execution(self, message: str) -> bool:
        """Check if request requires code execution."""
        code_keywords = ['code', 'python', 'run', 'execute', 'debug', 'test', 
                       'function', 'class', 'api', 'script', 'program']
        return any(kw in message.lower() for kw in code_keywords)
    
    def _detect_planning(self, message: str) -> bool:
        """Check if request requires planning."""
        planning_keywords = ['plan', 'schedule', 'steps', 'roadmap', 'timeline',
                          'organize', '安排', 'پلان', 'ترتیب']
        return any(kw in message.lower() for kw in planning_keywords)
    
    def _detect_memory_need(self, message: str, intent_type: IntentType) -> bool:
        """Check if request needs memory context."""
        memory_keywords = ['remember', 'previous', 'before', 'last time', 'earlier']
        needs_memory = any(kw in message.lower() for kw in memory_keywords)
        return needs_memory or intent_type in [IntentType.COMMAND, IntentType.REQUEST]
    
    def _analyze_sentiment(self, message: str) -> str:
        """Basic sentiment analysis."""
        positive = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'thanks', 'please']
        negative = ['bad', 'terrible', 'awful', 'hate', 'wrong', 'error', 'problem', 'issue']
        
        message_lower = message.lower()
        
        pos_count = sum(1 for w in positive if w in message_lower)
        neg_count = sum(1 for w in negative if w in message_lower)
        
        if neg_count > pos_count:
            return 'negative'
        elif pos_count > neg_count:
            return 'positive'
        return 'neutral'
    
    def _get_context_requirements(self, intent_type: IntentType, message: str) -> List[str]:
        """Get required context for this intent type."""
        requirements = self.context_requirements.get(intent_type, []).copy()
        
        # Add context based on keywords
        if 'code' in message.lower():
            requirements.append('code_history')
        if 'project' in message.lower():
            requirements.append('project_context')
        if any(w in message.lower() for w in ['file', 'document', 'write']):
            requirements.append('file_context')
            
        return list(set(requirements))
    
    def build_system_prompt(self, intent: ParsedIntent, context_items: List[ContextItem] = None) -> str:
        """
        Build system prompt based on parsed intent and context.
        Mirrors OpenClaw's prompt building mechanism.
        """
        prompt_parts = []
        
        # Base persona
        prompt_parts.append("You are Leo 2.0, a self-learning AI assistant.")
        
        # Add intent-specific instructions
        prompt_parts.append(self._get_intent_instruction(intent))
        
        # Add complexity-based instructions
        prompt_parts.append(self._get_complexity_instruction(intent.complexity))
        
        # Add context if available
        if context_items:
            prompt_parts.append(self._format_context(context_items))
        
        # Add language instruction
        if intent.language != 'en':
            prompt_parts.append(f"Respond in the user's language ({intent.language}).")
        
        # Add format instructions based on intent
        prompt_parts.append(self._get_format_instruction(intent))
        
        return "\n\n".join(prompt_parts)
    
    def _get_intent_instruction(self, intent: ParsedIntent) -> str:
        """Get instruction based on intent type."""
        instructions = {
            IntentType.QUESTION: "Provide clear, accurate answers. If unsure, acknowledge it.",
            IntentType.COMMAND: "Execute the requested action. Ask for clarification if needed.",
            IntentType.REQUEST: "Help fulfill the request efficiently. Offer alternatives if helpful.",
            IntentType.CHAT: "Respond in a friendly, conversational manner.",
            IntentType.CREATIVE: "Be creative and imaginative. Use vivid language.",
            IntentType.CODE: "Write clean, well-documented code. Explain your approach.",
            IntentType.ANALYSIS: "Provide thorough analysis. Consider multiple perspectives.",
            IntentType.PLANNING: "Create structured plans with clear steps and timelines.",
            IntentType.SEARCH: "Provide comprehensive information from your knowledge.",
            IntentType.LEARNING: "Explain concepts clearly. Use examples and analogies.",
            IntentType.UNKNOWN: "Try to understand the user's needs and respond helpfully.",
        }
        return instructions.get(intent.intent_type, instructions[IntentType.UNKNOWN])
    
    def _get_complexity_instruction(self, complexity: ComplexityLevel) -> str:
        """Get instruction based on complexity level."""
        instructions = {
            ComplexityLevel.TRIVIAL: "Keep responses extremely brief.",
            ComplexityLevel.SIMPLE: "Keep responses concise and direct.",
            ComplexityLevel.MODERATE: "Provide balanced responses with appropriate detail.",
            ComplexityLevel.COMPLEX: "Provide comprehensive responses with thorough explanations.",
            ComplexityLevel.EXPERT: "Provide detailed, technical responses. Assume high expertise.",
        }
        return instructions.get(complexity, instructions[ComplexityLevel.MODERATE])
    
    def _format_context(self, context_items: List[ContextItem]) -> str:
        """Format context items for the prompt."""
        if not context_items:
            return ""
        
        formatted = ["Relevant context:"]
        for item in sorted(context_items, key=lambda x: x.relevance, reverse=True):
            formatted.append(f"- [{item.source}] {item.content}")
        
        return "\n".join(formatted)
    
    def _get_format_instruction(self, intent: ParsedIntent) -> str:
        """Get format instruction based on intent."""
        if intent.intent_type == IntentType.CODE:
            return "Format code blocks properly with language specifiers."
        elif intent.intent_type == IntentType.CREATIVE:
            return "Use engaging language. Structure creative content appropriately."
        elif intent.intent_type == IntentType.PLANNING:
            return "Use clear structure: goals, steps, timeline, resources."
        return "Be clear and concise. Use formatting where helpful."
    
    def get_routing_info(self, intent: ParsedIntent) -> Dict[str, Any]:
        """
        Get routing information for model selection.
        Mirrors OpenClaw's model routing mechanism.
        """
        # Map complexity to model tiers
        model_tiers = {
            ComplexityLevel.TRIVIAL: ['phi3:mini', 'qwen2.5:3b'],
            ComplexityLevel.SIMPLE: ['qwen2.5:3b', 'llama3.2:3b'],
            ComplexityLevel.MODERATE: ['qwen3:8b', 'llama3.2:3b'],
            ComplexityLevel.COMPLEX: ['qwen3:8b', 'deepseek-v3'],
            ComplexityLevel.EXPERT: ['qwen3:8b', 'deepseek-v3', 'qwen3.5-397b'],
        }
        
        # Select model tier based on complexity and intent
        tier_models = model_tiers.get(intent.complexity, model_tiers[ComplexityLevel.MODERATE])
        
        # Adjust based on specific requirements
        if intent.requires_code and 'qwen3:8b' in tier_models:
            tier_models = ['qwen3:8b'] + tier_models
        if intent.requires_web:
            tier_models = tier_models + [tier_models[0]]  # Prefer current model
        
        return {
            'suggested_models': tier_models,
            'primary_model': tier_models[0] if tier_models else 'qwen2.5:3b',
            'complexity_score': intent.complexity.value,
            'requires_reasoning': intent.complexity.value >= 4,
            'requires_fast_response': intent.urgency in ['urgent', 'high'],
            'intent_type': intent.intent_type.value,
            'requires_memory': intent.requires_memory,
            'requires_tools': any([intent.requires_web, intent.requires_code, 
                                   intent.requires_planning]),
        }
