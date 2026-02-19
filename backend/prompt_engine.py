"""
Advanced Prompt Understanding Engine
Implements all 25 advanced prompt understanding features for ClawForge.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class OutputFormat(Enum):
    """Output format options."""
    JSON = "json"
    MARKDOWN = "markdown"
    YAML = "yaml"
    XML = "xml"
    PROSE = "prose"
    BULLETS = "bullets"
    NUMBERED = "numbered"
    TABLE = "table"
    CODE = "code"
    CUSTOM = "custom"


class Tone(Enum):
    """Tone and register options."""
    NEUTRAL = "neutral"
    FORMAL = "formal"
    CASUAL = "casual"
    EMPATHETIC = "empathetic"
    AUTHORITATIVE = "authoritative"
    PLAYFUL = "playful"
    CLINICAL = "clinical"
    SOCRATIC = "socratic"
    BLUNT = "blunt"
    DIPLOMATIC = "diplomatic"
    PERSUASIVE = "persuasive"
    TECHNICAL = "technical"


class Perspective(Enum):
    """Perspective and stance options."""
    NEUTRAL = "neutral"
    FIRST_PERSON = "first_person"
    THIRD_PERSON = "third_person"
    DEVILS_ADVOCATE = "devils_advocate"
    ARGUE_FOR = "argue_for"
    ARGUE_AGAINST = "argue_against"
    STEELMAN = "steelman"


class SpecificityLevel(Enum):
    """Specificity dial levels."""
    HIGH_LEVEL = "high_level"
    MEDIUM = "medium"
    DETAILED = "detailed"
    GRANULAR = "granular"


@dataclass
class Persona:
    """Persona assignment configuration."""
    name: str
    role: str
    expertise_level: str
    tone: Tone
    characteristics: List[str] = field(default_factory=list)
    background: str = ""
    constraints: List[str] = field(default_factory=list)


@dataclass
class FormattingOptions:
    """Output formatting configuration."""
    format: OutputFormat = OutputFormat.PROSE
    length: Optional[str] = None
    structure: Optional[str] = None
    include_headers: bool = True
    include_examples: bool = False
    max_words: Optional[int] = None
    custom_template: Optional[str] = None


@dataclass
class Constraint:
    """Positive or negative constraint."""
    type: str
    description: str
    category: str = "style"


@dataclass
class Example:
    """Few-shot example."""
    input_text: str
    output_text: str
    explanation: Optional[str] = None


@dataclass
class AudienceProfile:
    """Target audience configuration."""
    name: str
    expertise_level: str
    technical_level: str = "semi_technical"
    interests: List[str] = field(default_factory=list)
    communication_style: str = "standard"


@dataclass
class TaskStep:
    """Task decomposition step."""
    step_number: int
    description: str
    subtasks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class PromptContext:
    """Complete prompt context container."""
    # Core components
    system_prompt: str = ""
    user_message: str = ""
    persona: Optional[Persona] = None
    
    # Formatting
    formatting: FormattingOptions = field(default_factory=FormattingOptions)
    
    # Constraints
    positive_constraints: List[Constraint] = field(default_factory=list)
    negative_constraints: List[Constraint] = field(default_factory=list)
    
    # Examples
    examples: List[Example] = field(default_factory=list)
    
    # Audience
    audience: Optional[AudienceProfile] = None
    
    # Reasoning
    chain_of_thought: bool = False
    show_reasoning: bool = False
    task_decomposition: bool = False
    
    # Conditional logic
    conditional_rules: Dict[str, str] = field(default_factory=dict)
    
    # Context
    conversation_history: List[Dict] = field(default_factory=list)
    referenced_context: List[str] = field(default_factory=list)
    
    # Perspective and stance
    perspective: Perspective = Perspective.NEUTRAL
    stance_topic: Optional[str] = None
    stance_position: Optional[str] = None
    
    # Language and localization
    language: str = "en"
    dialect: Optional[str] = None
    region: Optional[str] = None
    
    # Specificity
    specificity: SpecificityLevel = SpecificityLevel.MEDIUM
    
    # Knowledge scope
    knowledge_scope: str = "unlimited"
    provided_documents: List[str] = field(default_factory=list)
    
    # Error handling
    uncertainty_handling: str = "acknowledge"
    confidence_required: bool = False
    
    # Iterative refinement
    self_review: bool = False
    critique_before_final: bool = False
    
    # Custom style
    style_sample: Optional[str] = None
    vocabulary_preferences: List[str] = field(default_factory=list)
    vocabulary_restrictions: List[str] = field(default_factory=list)
    
    # Output anchoring
    output_prefix: Optional[str] = None
    output_suffix: Optional[str] = None


class PromptEngine:
    """
    Advanced Prompt Understanding Engine.
    Implements all 25 advanced prompt understanding features.
    """
    
    DEFAULT_PERSONAS: Dict[str, Persona] = {}
    
    TONE_DESCRIPTIONS = {
        Tone.NEUTRAL: "neutral and objective",
        Tone.FORMAL: "formal and professional",
        Tone.CASUAL: "casual and conversational",
        Tone.EMPATHETIC: "empathetic and understanding",
        Tone.AUTHORITATIVE: "authoritative and confident",
        Tone.PLAYFUL: "playful and engaging",
        Tone.CLINICAL: "clinical and precise",
        Tone.SOCRATIC: "Socratic and questioning",
        Tone.BLUNT: "direct and blunt",
        Tone.DIPLOMATIC: "diplomatic and tactful",
        Tone.PERSUASIVE: "persuasive and compelling",
        Tone.TECHNICAL: "technical and precise",
    }
    
    def __init__(self):
        self._initialize_default_personas()
    
    def _initialize_default_personas(self):
        """Initialize default persona configurations."""
        self.DEFAULT_PERSONAS = {
            "cybersecurity_expert": Persona(
                name="Cybersecurity Expert",
                role="Senior Cybersecurity Analyst",
                expertise_level="expert",
                tone=Tone.AUTHORITATIVE,
                characteristics=["vigilant", "precise", "risk-aware", "methodical"],
                background="20+ years in cybersecurity, incident response, and threat analysis",
                constraints=["always consider security implications", "never suggest unsafe practices"]
            ),
            "philosophy_tutor": Persona(
                name="Philosophy Tutor",
                role="Socratic Philosophy Tutor",
                expertise_level="expert",
                tone=Tone.SOCRATIC,
                characteristics=["questioning", "thoughtful", "patient", "classical"],
                background="PhD in Philosophy, specializing in ancient Greek philosophy",
                constraints=["always ask questions before giving answers", "encourage critical thinking"]
            ),
            "business_consultant": Persona(
                name="Business Consultant",
                role="Senior Strategy Consultant",
                expertise_level="expert",
                tone=Tone.DIPLOMATIC,
                characteristics=["strategic", "practical", "results-oriented", "analytical"],
                background="MBA, 15 years consulting for Fortune 500 companies",
                constraints=["focus on actionable recommendations", "consider ROI and business impact"]
            ),
            "creative_writer": Persona(
                name="Creative Writer",
                role="Novelist and Content Creator",
                expertise_level="expert",
                tone=Tone.PLAYFUL,
                characteristics=["imaginative", "descriptive", "engaging", "storyteller"],
                background="Published author with expertise in multiple genres",
                constraints=["use vivid language", "create compelling narratives"]
            ),
            "technical_writer": Persona(
                name="Technical Writer",
                role="Documentation Specialist",
                expertise_level="expert",
                tone=Tone.TECHNICAL,
                characteristics=["precise", "clear", "structured", "thorough"],
                background="15 years creating technical documentation for software products",
                constraints=["prioritize clarity", "include practical examples", "avoid jargon without explanation"]
            ),
            "data_scientist": Persona(
                name="Data Scientist",
                role="Senior Data Scientist",
                expertise_level="expert",
                tone=Tone.TECHNICAL,
                characteristics=["analytical", "evidence-based", "methodical", "curious"],
                background="PhD in Statistics, 10+ years in ML and data analysis",
                constraints=["support claims with evidence", "consider statistical significance", "acknowledge limitations"]
            ),
        }
    
    # =========================================================================
    # FEATURE 1: Role & Persona Assignment
    # =========================================================================
    
    def set_persona(self, prompt_context: PromptContext, persona_name: str) -> PromptContext:
        """Apply a persona to the prompt context."""
        if persona_name in self.DEFAULT_PERSONAS:
            prompt_context.persona = self.DEFAULT_PERSONAS[persona_name]
        else:
            prompt_context.persona = Persona(
                name=persona_name,
                role=persona_name.replace("_", " ").title(),
                expertise_level="custom",
                tone=Tone.NEUTRAL,
                characteristics=[]
            )
        return prompt_context
    
    def create_custom_persona(
        self,
        name: str,
        role: str,
        expertise_level: str,
        tone: Tone,
        characteristics: List[str] = None,
        background: str = "",
        constraints: List[str] = None
    ) -> Persona:
        """Create a custom persona."""
        return Persona(
            name=name,
            role=role,
            expertise_level=expertise_level,
            tone=tone,
            characteristics=characteristics or [],
            background=background,
            constraints=constraints or []
        )
    
    def apply_persona_to_prompt(self, prompt_context: PromptContext) -> str:
        """Generate system prompt from persona configuration."""
        if not prompt_context.persona:
            return prompt_context.system_prompt
        
        p = prompt_context.persona
        persona_prompt = f"You are {p.name}, {p.role}.\n\n"
        persona_prompt += f"Background: {p.background}\n\n" if p.background else ""
        persona_prompt += f"Your expertise level: {p.expertise_level}\n\n"
        persona_prompt += f"Your characteristics: {', '.join(p.characteristics)}\n\n"
        
        if p.constraints:
            persona_prompt += "Your constraints:\n"
            for constraint in p.constraints:
                persona_prompt += f"- {constraint}\n"
            persona_prompt += "\n"
        
        persona_prompt += prompt_context.system_prompt
        return persona_prompt
    
    # =========================================================================
    # FEATURE 2: System Prompt Layering
    # =========================================================================
    
    def add_system_layer(
        self,
        prompt_context: PromptContext,
        layer_content: str,
        layer_name: str = "custom"
    ) -> PromptContext:
        """Add a persistent system prompt layer."""
        if not hasattr(prompt_context, '_system_layers'):
            prompt_context._system_layers = []
        
        prompt_context._system_layers.append({
            'name': layer_name,
            'content': layer_content,
            'priority': len(prompt_context._system_layers)
        })
        return prompt_context
    
    def combine_system_layers(self, prompt_context: PromptContext) -> str:
        """Combine all system layers into final system prompt."""
        if not hasattr(prompt_context, '_system_layers'):
            return prompt_context.system_prompt
        
        combined = prompt_context.system_prompt
        for layer in sorted(prompt_context._system_layers, key=lambda x: x['priority']):
            combined += f"\n\n[{layer['name'].upper()} LAYER]\n{layer['content']}\n[END {layer['name'].upper()} LAYER]"
        
        return combined
    
    # =========================================================================
    # FEATURE 3: Explicit Output Formatting Control
    # =========================================================================
    
    def set_formatting(
        self,
        prompt_context: PromptContext,
        format: str,
        length: str = None,
        structure: str = None,
        max_words: int = None
    ) -> PromptContext:
        """Set output formatting options."""
        format_map = {
            'json': OutputFormat.JSON,
            'markdown': OutputFormat.MARKDOWN,
            'yaml': OutputFormat.YAML,
            'xml': OutputFormat.XML,
            'prose': OutputFormat.PROSE,
            'bullets': OutputFormat.BULLETS,
            'numbered': OutputFormat.NUMBERED,
            'table': OutputFormat.TABLE,
            'code': OutputFormat.CODE,
        }
        
        prompt_context.formatting = FormattingOptions(
            format=format_map.get(format.lower(), OutputFormat.PROSE),
            length=length,
            structure=structure,
            max_words=max_words
        )
        return prompt_context
    
    def format_output_instructions(self, prompt_context: PromptContext) -> str:
        """Generate output formatting instructions."""
        f = prompt_context.formatting
        instructions = []
        
        format_descriptions = {
            OutputFormat.JSON: "Output must be valid JSON format",
            OutputFormat.MARKDOWN: "Use Markdown formatting with headers, lists, and code blocks",
            OutputFormat.YAML: "Output must be valid YAML format",
            OutputFormat.XML: "Output must be valid XML format",
            OutputFormat.PROSE: "Write in flowing prose, avoiding bullet lists",
            OutputFormat.BULLETS: "Use bullet points for all items",
            OutputFormat.NUMBERED: "Use numbered steps or lists",
            OutputFormat.TABLE: "Present information in table format",
            OutputFormat.CODE: "Output as code blocks with syntax highlighting",
        }
        instructions.append(format_descriptions.get(f.format, "Format output appropriately"))
        
        if f.length:
            length_map = {
                'short': "Keep the response brief and concise",
                'medium': "Provide a moderate-length response",
                'long': "Provide a comprehensive, detailed response",
                'exhaustive': "Provide an exhaustive, thorough response with all details"
            }
            instructions.append(length_map.get(f.length, f"Response length: {f.length}"))
        
        if f.structure:
            instructions.append(f"Structure: {f.structure}")
        
        if f.max_words:
            instructions.append(f"Maximum word count: {f.max_words}")
        
        return "\n".join(instructions)
    
    # =========================================================================
    # FEATURE 4: XML / Structured Tag Instructions
    # =========================================================================
    
    XML_TAGS = {
        '<context>': '</context>',
        '<task>': '</task>',
        '<format>': '</format>',
        '<examples>': '</examples>',
        '<constraints>': '</constraints>',
        '<tone>': '</tone>',
        '<audience>': '</audience>',
        '<purpose>': '</purpose>',
        '<background>': '</background>',
        '<notes>': '</notes>',
        '<thinking>': '</thinking>',
        '<reasoning>': '</reasoning>',
        '<output>': '</output>',
        '<step>': '</step>',
        '<example>': '</example>',
        '<note>': '</note>',
        '<warning>': '</warning>',
        '<important>': '</important>',
        '<question>': '</question>',
        '<answer>': '</answer>',
        '<summary>': '</summary>',
        '<detail>': '</detail>',
        '<header>': '</header>',
        '<section>': '</section>',
    }
    
    def parse_xml_tags(self, text: str) -> Dict[str, str]:
        """Parse XML-style tags and extract content."""
        parsed = {}
        for tag, closing in self.XML_TAGS.items():
            pattern = rf'{tag}(.*?){closing}'
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
                tag_name = tag.strip('<').strip('>').lower()
                parsed[tag_name] = matches[0].strip()
        return parsed
    
    def generate_xml_wrapper(self, content: str, tag: str) -> str:
        """Wrap content in XML-style tags."""
        closing = self.XML_TAGS.get(f'<{tag}>', f'</{tag}>')
        return f'<{tag}>{content}{closing}'
    
    def validate_xml_structure(self, text: str) -> bool:
        """Validate XML tag structure is balanced."""
        tag_pattern = r'<(\w+)[^>]*(?:/>|>(.*?)</\1>)'
        matches = re.findall(tag_pattern, text, re.DOTALL)
        
        for tag, content in matches:
            if not content:
                continue
            if not self.validate_xml_structure(content):
                return False
        
        return True
    
    # =========================================================================
    # FEATURE 5: Chain-of-Thought (CoT) Prompting
    # =========================================================================
    
    def enable_chain_of_thought(
        self,
        prompt_context: PromptContext,
        show_reasoning: bool = True
    ) -> PromptContext:
        """Enable chain-of-thought reasoning."""
        prompt_context.chain_of_thought = True
        prompt_context.show_reasoning = show_reasoning
        return prompt_context
    
    def cot_instructions(self, prompt_context: PromptContext) -> str:
        """Generate chain-of-thought instructions."""
        if not prompt_context.chain_of_thought:
            return ""
        
        instructions = [
            "Think through this step by step before answering.",
            "Show your reasoning process for complex decisions.",
            "Break down the problem into logical components.",
            "Consider alternative approaches and explain your choice.",
        ]
        
        if prompt_context.show_reasoning:
            instructions.append("Present your reasoning clearly in your response.")
        
        return "\n".join(instructions)
    
    # =========================================================================
    # FEATURE 6: Few-Shot & Many-Shot Examples
    # =========================================================================
    
    def add_example(
        self,
        prompt_context: PromptContext,
        input_text: str,
        output_text: str,
        explanation: str = None
    ) -> PromptContext:
        """Add a few-shot example."""
        prompt_context.examples.append(Example(input_text, output_text, explanation))
        return prompt_context
    
    def add_examples(
        self,
        prompt_context: PromptContext,
        examples: List[Dict[str, str]]
    ) -> PromptContext:
        """Add multiple examples."""
        for ex in examples:
            prompt_context.examples.append(Example(
                input_text=ex['input'],
                output_text=ex['output'],
                explanation=ex.get('explanation')
            ))
        return prompt_context
    
    def format_examples(self, prompt_context: PromptContext) -> str:
        """Generate few-shot examples section."""
        if not prompt_context.examples:
            return ""
        
        examples_text = []
        
        for i, ex in enumerate(prompt_context.examples, 1):
            examples_text.append(f"Example {i}:")
            examples_text.append(f"Input: {ex.input_text}")
            examples_text.append(f"Output: {ex.output_text}")
            if ex.explanation:
                examples_text.append(f"Explanation: {ex.explanation}")
            examples_text.append("")
        
        return "\n".join(examples_text)
    
    def count_examples(self, prompt_context: PromptContext) -> str:
        """Return example count category."""
        count = len(prompt_context.examples)
        if count == 0:
            return "zero-shot"
        elif count == 1:
            return "one-shot"
        elif count <= 5:
            return "few-shot"
        else:
            return "many-shot"
    
    # =========================================================================
    # FEATURE 7: Positive & Negative Constraints
    # =========================================================================
    
    def add_constraint(
        self,
        prompt_context: PromptContext,
        constraint_type: str,
        description: str,
        category: str = "style"
    ) -> PromptContext:
        """Add a constraint (positive or negative)."""
        constraint = Constraint(
            type=constraint_type,
            description=description,
            category=category
        )
        
        if constraint_type == "positive":
            prompt_context.positive_constraints.append(constraint)
        else:
            prompt_context.negative_constraints.append(constraint)
        
        return prompt_context
    
    def format_constraints(self, prompt_context: PromptContext) -> str:
        """Generate constraints section."""
        constraints_text = []
        
        if prompt_context.positive_constraints:
            constraints_text.append("Always:")
            for c in prompt_context.positive_constraints:
                constraints_text.append(f"  - {c.description}")
            constraints_text.append("")
        
        if prompt_context.negative_constraints:
            constraints_text.append("Never:")
            for c in prompt_context.negative_constraints:
                constraints_text.append(f"  - {c.description}")
        
        return "\n".join(constraints_text)
    
    # =========================================================================
    # FEATURE 8: Audience Targeting
    # =========================================================================
    
    def set_audience(
        self,
        prompt_context: PromptContext,
        name: str,
        expertise_level: str,
        technical_level: str = "semi_technical",
        interests: List[str] = None
    ) -> PromptContext:
        """Set target audience."""
        prompt_context.audience = AudienceProfile(
            name=name,
            expertise_level=expertise_level,
            technical_level=technical_level,
            interests=interests or []
        )
        return prompt_context
    
    def apply_audience_instructions(self, prompt_context: PromptContext) -> str:
        """Generate audience-specific instructions."""
        if not prompt_context.audience:
            return ""
        
        a = prompt_context.audience
        instructions = [f"Target audience: {a.name}"]
        
        expertise_map = {
            "child": "Explain like speaking to a 10-year-old",
            "teen": "Explain for a teenage audience",
            "adult": "Explain for a general adult audience",
            "expert": "Assume deep expertise in the subject",
            "phd": "Assume PhD-level expertise, can use technical terminology freely",
        }
        if a.expertise_level in expertise_map:
            instructions.append(expertise_map[a.expertise_level])
        
        tech_map = {
            "non_technical": "Avoid jargon, explain concepts in plain language",
            "semi_technical": "Use some technical terms but explain when needed",
            "highly_technical": "Use full technical terminology without explanation",
        }
        if a.technical_level in tech_map:
            instructions.append(tech_map[a.technical_level])
        
        if a.interests:
            instructions.append(f"Relevant interests: {', '.join(a.interests)}")
        
        return "\n".join(instructions)
    
    # =========================================================================
    # FEATURE 9: Conditional / If-Then Logic in Prompts
    # =========================================================================
    
    def add_conditional_rule(
        self,
        prompt_context: PromptContext,
        condition: str,
        response: str
    ) -> PromptContext:
        """Add a conditional if-then rule."""
        prompt_context.conditional_rules[condition] = response
        return prompt_context
    
    def format_conditional_instructions(self, prompt_context: PromptContext) -> str:
        """Generate conditional instructions."""
        if not prompt_context.conditional_rules:
            return ""
        
        instructions = ["Conditional instructions:"]
        for condition, response in prompt_context.conditional_rules.items():
            instructions.append(f"If {condition}, then: {response}")
        
        return "\n".join(instructions)
    
    def evaluate_conditions(
        self,
        prompt_context: PromptContext,
        user_input: str
    ) -> List[str]:
        """Evaluate which conditional rules apply to user input."""
        matched_rules = []
        
        for condition, response in prompt_context.conditional_rules.items():
            condition_lower = condition.lower()
            if condition_lower in user_input.lower():
                matched_rules.append(response)
        
        return matched_rules
    
    # =========================================================================
    # FEATURE 10: Task Decomposition Instructions
    # =========================================================================
    
    def decompose_task(
        self,
        prompt_context: PromptContext,
        task_description: str
    ) -> List[TaskStep]:
        """Decompose a complex task into subtasks."""
        steps = []
        
        if "and" in task_description.lower():
            subtasks = task_description.split("and")
            for i, subtask in enumerate(subtasks, 1):
                steps.append(TaskStep(
                    step_number=i,
                    description=subtask.strip(),
                    subtasks=[f"Complete: {subtask.strip()}"]
                ))
        else:
            steps.append(TaskStep(
                step_number=1,
                description=task_description,
                subtasks=["Understand requirements", "Plan approach", "Execute task", "Review results"]
            ))
        
        return steps
    
    def enable_task_decomposition(self, prompt_context: PromptContext) -> PromptContext:
        """Enable automatic task decomposition."""
        prompt_context.task_decomposition = True
        return prompt_context
    
    def format_decomposition_instructions(self, prompt_context: PromptContext) -> str:
        """Generate task decomposition instructions."""
        if not prompt_context.task_decomposition:
            return ""
        
        instructions = [
            "Before answering, identify the sub-problems that need to be solved.",
            "Outline your approach before executing each step.",
            "Break complex tasks into smaller, manageable components.",
            "Review progress after each major step.",
        ]
        
        return "\n".join(instructions)
    
    # =========================================================================
    # FEATURE 11: Meta-Prompting (Prompt Refinement)
    # =========================================================================
    
    def generate_prompt_critique(self, prompt: str) -> str:
        """Generate a critique of a prompt and suggestions for improvement."""
        critique_points = []
        
        if len(prompt) < 50:
            critique_points.append("Prompt is quite brief - consider adding more context")
        
        vague_words = ["some", "things", "stuff", "maybe", "possibly"]
        if any(word in prompt.lower() for word in vague_words):
            critique_points.append("Consider replacing vague language with specific terms")
        
        if "don't" not in prompt.lower() and "never" not in prompt.lower():
            critique_points.append("Consider adding negative constraints to avoid unwanted behavior")
        
        if "example" not in prompt.lower():
            critique_points.append("Consider adding example(s) to clarify expected output")
        
        if not any(fmt in prompt.lower() for fmt in ["format", "output", "structure", "write"]):
            critique_points.append("Consider specifying desired output format")
        
        if critique_points:
            return "Prompt critique:\n" + "\n".join(f"- {point}" for point in critique_points)
        return "Prompt looks well-structured!"
    
    def improve_prompt(self, prompt: str, critique: str = None) -> str:
        """Improve a prompt based on critique."""
        if not critique:
            critique = self.generate_prompt_critique(prompt)
        
        improved = prompt
        
        if "<task>" not in improved:
            improved = f"<task>{improved}</task>"
        
        if "<format>" not in improved and "format" not in improved.lower():
            improved += "\n<format>Provide a clear, well-structured response</format>"
        
        return improved
    
    # =========================================================================
    # FEATURE 12: Context Window Utilization
    # =========================================================================
    
    def add_conversation_history(
        self,
        prompt_context: PromptContext,
        role: str,
        content: str
    ) -> PromptContext:
        """Add to conversation history."""
        prompt_context.conversation_history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        return prompt_context
    
    def add_referenced_context(
        self,
        prompt_context: PromptContext,
        context_ref: str
    ) -> PromptContext:
        """Add a reference to external context."""
        prompt_context.referenced_context.append(context_ref)
        return prompt_context
    
    def format_context_section(self, prompt_context: PromptContext) -> str:
        """Generate conversation context section."""
        sections = []
        
        if prompt_context.conversation_history:
            sections.append("Conversation history:")
            for msg in prompt_context.conversation_history[-10:]:
                sections.append(f"[{msg['role']}]: {msg['content']}")
            sections.append("")
        
        if prompt_context.referenced_context:
            sections.append("Referenced documents/context:")
            for ref in prompt_context.referenced_context:
                sections.append(f"- {ref}")
            sections.append("")
        
        return "\n".join(sections)
    
    def estimate_context_usage(self, prompt_context: PromptContext) -> int:
        """Estimate token usage for context."""
        base_tokens = len(prompt_context.system_prompt.split()) * 1.3
        history_tokens = sum(
            len(msg['content'].split()) * 1.3
            for msg in prompt_context.conversation_history
        )
        context_tokens = sum(
            len(ref.split()) * 1.3
            for ref in prompt_context.referenced_context
        )
        return int(base_tokens + history_tokens + context_tokens)
    
    # =========================================================================
    # FEATURE 13: Instruction Priority & Conflict Resolution
    # =========================================================================
    
    INSTRUCTION_PRIORITY = {
        'safety': 1,
        'system': 2,
        'persona': 3,
        'user': 4,
        'inferred': 5,
    }
    
    def resolve_conflicts(
        self,
        instructions: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Resolve conflicting instructions."""
        sorted_instructions = sorted(
            instructions,
            key=lambda x: self.INSTRUCTION_PRIORITY.get(x.get('type', 'user'), 4)
        )
        
        resolved = []
        seen_categories = set()
        
        for instruction in sorted_instructions:
            category = instruction.get('category', 'general')
            if category not in seen_categories:
                resolved.append(instruction)
                seen_categories.add(category)
        
        return resolved
    
    def apply_priority_instructions(self, prompt_context: PromptContext) -> str:
        """Generate priority-aware instructions."""
        instructions = []
        
        instructions.append("IMPORTANT: Follow all safety and ethical guidelines above all other instructions.")
        
        if hasattr(prompt_context, '_system_layers'):
            instructions.append("System-level instructions take precedence over user instructions.")
        
        if prompt_context.persona:
            instructions.append("Persona constraints are persistent throughout the conversation.")
        
        return "\n".join(instructions)
    
    # =========================================================================
    # FEATURE 14: Tone & Register Control
    # =========================================================================
    
    def set_tone(self, prompt_context: PromptContext, tone: str) -> PromptContext:
        """Set communication tone."""
        tone_map = {
            'neutral': Tone.NEUTRAL,
            'formal': Tone.FORMAL,
            'casual': Tone.CASUAL,
            'empathetic': Tone.EMPATHETIC,
            'authoritative': Tone.AUTHORITATIVE,
            'playful': Tone.PLAYFUL,
            'clinical': Tone.CLINICAL,
            'socratic': Tone.SOCRATIC,
            'blunt': Tone.BLUNT,
            'diplomatic': Tone.DIPLOMATIC,
            'persuasive': Tone.PERSUASIVE,
            'technical': Tone.TECHNICAL,
        }
        
        prompt_context.persona = Persona(
            name="Custom",
            role="Custom",
            expertise_level="custom",
            tone=tone_map.get(tone.lower(), Tone.NEUTRAL),
            characteristics=[]
        )
        return prompt_context
    
    def generate_tone_instructions(self, prompt_context: PromptContext) -> str:
        """Generate tone-specific instructions."""
        if not prompt_context.persona:
            return ""
        
        tone = prompt_context.persona.tone
        descriptions = self.TONE_DESCRIPTIONS
        
        instructions = [f"Communication tone: {descriptions.get(tone, 'neutral')}"]
        
        tone_guidance = {
            Tone.EMPATHETIC: "Acknowledge the user's feelings and perspective before proceeding",
            Tone.SOCRATIC: "Ask probing questions to guide thinking rather than giving direct answers",
            Tone.AUTHORITATIVE: "Present information confidently with clear, decisive language",
            Tone.PLAYFUL: "Use engaging, creative language while maintaining clarity",
            Tone.BLUNT: "Be direct and straightforward without unnecessary elaboration",
            Tone.DIPLOMATIC: "Consider multiple viewpoints and present balanced perspectives",
            Tone.TECHNICAL: "Use precise technical terminology and exact descriptions",
        }
        
        if tone in tone_guidance:
            instructions.append(tone_guidance[tone])
        
        return "\n".join(instructions)
    
    # =========================================================================
    # FEATURE 15: Output Anchoring with Prefills
    # =========================================================================
    
    def set_output_prefix(self, prompt_context: PromptContext, prefix: str) -> PromptContext:
        """Set output prefix for anchoring."""
        prompt_context.output_prefix = prefix
        return prompt_context
    
    def set_output_suffix(self, prompt_context: PromptContext, suffix: str) -> PromptContext:
        """Set output suffix for anchoring."""
        prompt_context.output_suffix = suffix
        return prompt_context
    
    def format_anchoring_instructions(self, prompt_context: PromptContext) -> str:
        """Generate output anchoring instructions."""
        instructions = []
        
        if prompt_context.output_prefix:
            instructions.append(f"Begin your response with: {prompt_context.output_prefix}")
        
        if prompt_context.output_suffix:
            instructions.append(f"End your response with: {prompt_context.output_suffix}")
        
        return "\n".join(instructions) if instructions else ""
    
    def apply_output_anchoring(
        self,
        response: str,
        prompt_context: PromptContext
    ) -> str:
        """Apply output anchoring to response."""
        if prompt_context.output_prefix:
            if not response.startswith(prompt_context.output_prefix):
                response = prompt_context.output_prefix + response
        
        if prompt_context.output_suffix:
            if not response.endswith(prompt_context.output_suffix):
                response = response + prompt_context.output_suffix
        
        return response
    
    # =========================================================================
    # FEATURE 16: Multi-Turn Conversation Control
    # =========================================================================
    
    def enable_multi_turn_context(self, prompt_context: PromptContext) -> PromptContext:
        """Enable multi-turn conversation context."""
        return prompt_context
    
    def format_reference_instructions(self) -> str:
        """Generate instructions for multi-turn references."""
        return """
Multi-turn conversation:
- Remember context from earlier messages in this conversation
- You can reference previous responses explicitly
- If the user says "revise the third point", identify and revise the third point from earlier
- If the user says "ignore what I said earlier", adjust accordingly
- Build on previous responses to create coherent, iterative artifacts
""".strip()
    
    # =========================================================================
    # FEATURE 17: Perspective & Stance Control
    # =========================================================================
    
    def set_perspective(
        self,
        prompt_context: PromptContext,
        perspective: str,
        topic: str = None,
        position: str = None
    ) -> PromptContext:
        """Set perspective and stance."""
        perspective_map = {
            'neutral': Perspective.NEUTRAL,
            'first_person': Perspective.FIRST_PERSON,
            'third_person': Perspective.THIRD_PERSON,
            'devils_advocate': Perspective.DEVILS_ADVOCATE,
            'argue_for': Perspective.ARGUE_FOR,
            'argue_against': Perspective.ARGUE_AGAINST,
            'steelman': Perspective.STEELMAN,
        }
        
        prompt_context.perspective = perspective_map.get(perspective.lower(), Perspective.NEUTRAL)
        prompt_context.stance_topic = topic
        prompt_context.stance_position = position
        return prompt_context
    
    def format_perspective_instructions(self, prompt_context: PromptContext) -> str:
        """Generate perspective instructions."""
        if prompt_context.perspective == Perspective.NEUTRAL:
            return ""
        
        instructions = []
        
        perspective_guidance = {
            Perspective.FIRST_PERSON: "Speak from personal experience and perspective using 'I' statements",
            Perspective.THIRD_PERSON: "Maintain an objective, third-person viewpoint",
            Perspective.DEVILS_ADVOCATE: "Argue the opposing position to challenge assumptions",
            Perspective.ARGUE_FOR: f"Present arguments for: {prompt_context.stance_position or 'the given position'}",
            Perspective.ARGUE_AGAINST: f"Present arguments against: {prompt_context.stance_topic or 'the given topic'}",
            Perspective.STEELMAN: "Present the strongest possible version of an argument before critiquing",
        }
        
        if prompt_context.perspective in perspective_guidance:
            instructions.append(perspective_guidance[prompt_context.perspective])
        
        return "\n".join(instructions)
    
    # =========================================================================
    # FEATURE 18: Language & Localization
    # =========================================================================
    
    def set_language(
        self,
        prompt_context: PromptContext,
        language: str,
        dialect: str = None,
        region: str = None
    ) -> PromptContext:
        """Set language and localization."""
        prompt_context.language = language
        prompt_context.dialect = dialect
        prompt_context.region = region
        return prompt_context
    
    def format_localization_instructions(self, prompt_context: PromptContext) -> str:
        """Generate localization instructions."""
        instructions = [f"Respond in: {prompt_context.language.upper()}"]
        
        if prompt_context.dialect:
            instructions.append(f"Dialect: {prompt_context.dialect}")
        
        if prompt_context.region:
            region_guidance = {
                'us': "Use American English spelling and conventions",
                'uk': "Use British English spelling and conventions",
                'au': "Use Australian English conventions",
            }
            if prompt_context.region in region_guidance:
                instructions.append(region_guidance[prompt_context.region])
        
        return "\n".join(instructions)

    def set_specificity(self, prompt_context: PromptContext, level: str) -> PromptContext:
        """Set specificity level."""
        specificity_map = {
            'high_level': SpecificityLevel.HIGH_LEVEL,
            'medium': SpecificityLevel.MEDIUM,
            'detailed': SpecificityLevel.DETAILED,
            'granular': SpecificityLevel.GRANULAR,
        }
        prompt_context.specificity = specificity_map.get(level.lower(), SpecificityLevel.MEDIUM)
        return prompt_context
    
    def format_specificity_instructions(self, prompt_context: PromptContext) -> str:
        """Generate specificity instructions."""
        instructions = []
        
        specificity_guidance = {
            SpecificityLevel.HIGH_LEVEL: "Provide a high-level overview only, focusing on main concepts",
            SpecificityLevel.MEDIUM: "Balance detail with brevity, covering key points adequately",
            SpecificityLevel.DETAILED: "Provide comprehensive coverage with substantial detail",
            SpecificityLevel.GRANULAR: "Go into granular, implementation-level detail with edge cases",
        }
        
        if prompt_context.specificity in specificity_guidance:
            instructions.append(specificity_guidance[prompt_context.specificity])
        
        return "\n".join(instructions)
    
    # =========================================================================
    # FEATURE 20: Constraint Stacking
    # =========================================================================
    
    def get_stacked_constraints(self, prompt_context: PromptContext) -> str:
        """Get all stacked constraints combined."""
        all_constraints = []
        
        formatting = self.format_output_instructions(prompt_context)
        if formatting:
            all_constraints.append(formatting)
        
        pos_constraints = self.format_constraints(prompt_context)
        if pos_constraints:
            all_constraints.append(pos_constraints)
        
        tone = self.generate_tone_instructions(prompt_context)
        if tone:
            all_constraints.append(tone)
        
        specificity = self.format_specificity_instructions(prompt_context)
        if specificity:
            all_constraints.append(specificity)
        
        return "\n\n".join(all_constraints)
    
    # =========================================================================
    # FEATURE 21: Iterative Refinement Instructions
    # =========================================================================
    
    def enable_self_review(self, prompt_context: PromptContext) -> PromptContext:
        """Enable self-review before finalizing response."""
        prompt_context.self_review = True
        return prompt_context
    
    def enable_critique_before_final(self, prompt_context: PromptContext) -> PromptContext:
        """Enable critique before final response."""
        prompt_context.critique_before_final = True
        return prompt_context
    
    def format_refinement_instructions(self, prompt_context: PromptContext) -> str:
        """Generate iterative refinement instructions."""
        instructions = []
        
        if prompt_context.self_review:
            instructions.append("After drafting your response, review it for clarity and accuracy before sharing.")
        
        if prompt_context.critique_before_final:
            instructions.append("Critique your own response for logical consistency, then improve it before finalizing.")
        
        instructions.append("Check for completeness, accuracy, and relevance before responding.")
        
        return "\n".join(instructions)
    
    # =========================================================================
    # FEATURE 22: Custom Vocabulary / Style Mirroring
    # =========================================================================
    
    def set_style_sample(self, prompt_context: PromptContext, sample: str) -> PromptContext:
        """Set a style sample to mirror."""
        prompt_context.style_sample = sample
        return prompt_context
    
    def add_vocabulary_preference(
        self,
        prompt_context: PromptContext,
        word: str
    ) -> PromptContext:
        """Add a vocabulary preference."""
        prompt_context.vocabulary_preferences.append(word)
        return prompt_context
    
    def add_vocabulary_restriction(
        self,
        prompt_context: PromptContext,
        word: str
    ) -> PromptContext:
        """Add a vocabulary restriction."""
        prompt_context.vocabulary_restrictions.append(word)
        return prompt_context
    
    def format_vocabulary_instructions(self, prompt_context: PromptContext) -> str:
        """Generate vocabulary instructions."""
        instructions = []
        
        if prompt_context.style_sample:
            instructions.append("Mirror the style and tone of this text:\n\n" + prompt_context.style_sample)
        
        if prompt_context.vocabulary_preferences:
            instructions.append("Prefer using: " + ", ".join(prompt_context.vocabulary_preferences))
        
        if prompt_context.vocabulary_restrictions:
            instructions.append("Avoid using: " + ", ".join(prompt_context.vocabulary_restrictions))
        
        return "\n".join(instructions)
    
    # =========================================================================
    # FEATURE 23: Hypothetical & Counterfactual Framing
    # =========================================================================
    
    def format_hypothetical_instructions(self, prompt_context: PromptContext) -> str:
        """Generate hypothetical framing instructions."""
        return """Hypothetical and counterfactual framing:
- When asked to imagine scenarios, engage fully with the premise
- Clearly distinguish between hypotheticals and factual statements
- Explore implications and consequences of hypothetical scenarios
- Use phrases like "In a world where X is true..." to frame counterfactuals
- Present creative scenarios while maintaining logical consistency"""
    
    # =========================================================================
    # FEATURE 24: Knowledge Scope Limiting
    # =========================================================================
    
    def set_knowledge_scope(
        self,
        prompt_context: PromptContext,
        scope: str,
        documents: List[str] = None
    ) -> PromptContext:
        """Set knowledge scope limiting."""
        prompt_context.knowledge_scope = scope
        if documents:
            prompt_context.provided_documents = documents
        return prompt_context
    
    def format_knowledge_scope_instructions(self, prompt_context: PromptContext) -> str:
        """Generate knowledge scope instructions."""
        instructions = []
        
        if prompt_context.knowledge_scope == "provided_only":
            instructions.append("Answer only using the information provided in this conversation.")
            instructions.append("Do not use any external knowledge or training data.")
            if prompt_context.provided_documents:
                instructions.append("Referenced documents: " + ", ".join(prompt_context.provided_documents))
        
        elif prompt_context.knowledge_scope == "conversation_only":
            instructions.append("Base your answer only on information from this conversation history.")
            instructions.append("Do not introduce information not mentioned in the conversation.")
        
        return "\n".join(instructions)
    
    # =========================================================================
    # FEATURE 25: Error & Uncertainty Handling Instructions
    # =========================================================================
    
    def set_uncertainty_handling(
        self,
        prompt_context: PromptContext,
        mode: str,
        require_confidence: bool = False
    ) -> PromptContext:
        """Set uncertainty handling behavior."""
        prompt_context.uncertainty_handling = mode
        prompt_context.confidence_required = require_confidence
        return prompt_context
    
    def format_uncertainty_instructions(self, prompt_context: PromptContext) -> str:
        """Generate uncertainty handling instructions."""
        instructions = []
        
        if prompt_context.uncertainty_handling == "acknowledge":
            instructions.append("If you don't know something, say so clearly.")
            instructions.append("Distinguish between what you know and what you're inferring.")
        
        elif prompt_context.uncertainty_handling == "guess":
            instructions.append("Make reasonable inferences when direct knowledge is unavailable.")
            instructions.append("Clearly mark any assumptions or guesses.")
        
        elif prompt_context.uncertainty_handling == "ask_clarification":
            instructions.append("If the request is unclear, ask for clarification before answering.")
        
        if prompt_context.confidence_required:
            instructions.append("Rate your confidence level for each claim or statement.")
        
        return "\n".join(instructions)
    
    # =========================================================================
    # MASTER COMPILE METHOD
    # =========================================================================
    
    def compile_prompt(
        self,
        prompt_context: PromptContext,
        user_message: str = None
    ) -> str:
        """
        Compile all prompt components into final system prompt.
        This is the main method to generate the complete prompt.
        """
        components = []
        
        # 1. Apply persona
        persona_prompt = self.apply_persona_to_prompt(prompt_context)
        if persona_prompt:
            components.append(persona_prompt)
        
        # 2. Combine system layers
        layered_prompt = self.combine_system_layers(prompt_context)
        if layered_prompt:
            components.append(layered_prompt)
        
        # 3. Add formatting instructions
        formatting = self.format_output_instructions(prompt_context)
        if formatting:
            components.append(formatting)
        
        # 4. Add examples
        examples = self.format_examples(prompt_context)
        if examples:
            components.append(examples)
        
        # 5. Add constraints
        constraints = self.format_constraints(prompt_context)
        if constraints:
            components.append(constraints)
        
        # 6. Add audience instructions
        audience = self.apply_audience_instructions(prompt_context)
        if audience:
            components.append(audience)
        
        # 7. Add CoT instructions
        cot = self.cot_instructions(prompt_context)
        if cot:
            components.append(cot)
        
        # 8. Add task decomposition
        decomposition = self.format_decomposition_instructions(prompt_context)
        if decomposition:
            components.append(decomposition)
        
        # 9. Add conditional instructions
        conditional = self.format_conditional_instructions(prompt_context)
        if conditional:
            components.append(conditional)
        
        # 10. Add context section
        context = self.format_context_section(prompt_context)
        if context:
            components.append(context)
        
        # 11. Add priority instructions
        priority = self.apply_priority_instructions(prompt_context)
        if priority:
            components.append(priority)
        
        # 12. Add tone instructions
        tone = self.generate_tone_instructions(prompt_context)
        if tone:
            components.append(tone)
        
        # 13. Add anchoring
        anchoring = self.format_anchoring_instructions(prompt_context)
        if anchoring:
            components.append(anchoring)
        
        # 14. Add multi-turn reference instructions
        multi_turn = self.format_reference_instructions()
        if multi_turn:
            components.append(multi_turn)
        
        # 15. Add perspective
        perspective = self.format_perspective_instructions(prompt_context)
        if perspective:
            components.append(perspective)
        
        # 16. Add localization
        localization = self.format_localization_instructions(prompt_context)
        if localization:
            components.append(localization)
        
        # 17. Add specificity
        specificity = self.format_specificity_instructions(prompt_context)
        if specificity:
            components.append(specificity)
        
        # 18. Add stacked constraints
        stacked = self.get_stacked_constraints(prompt_context)
        if stacked:
            components.append(stacked)
        
        # 19. Add refinement
        refinement = self.format_refinement_instructions(prompt_context)
        if refinement:
            components.append(refinement)
        
        # 20. Add vocabulary
        vocabulary = self.format_vocabulary_instructions(prompt_context)
        if vocabulary:
            components.append(vocabulary)
        
        # 21. Add hypothetical
        hypothetical = self.format_hypothetical_instructions(prompt_context)
        if hypothetical:
            components.append(hypothetical)
        
        # 22. Add knowledge scope
        knowledge_scope = self.format_knowledge_scope_instructions(prompt_context)
        if knowledge_scope:
            components.append(knowledge_scope)
        
        # 23. Add uncertainty handling
        uncertainty = self.format_uncertainty_instructions(prompt_context)
        if uncertainty:
            components.append(uncertainty)
        
        # Join all components
        final_prompt = "\n\n".join(filter(None, components))
        
        # Add user message if provided
        if user_message:
            final_prompt += "\n\nUser's request:\n" + user_message
        
        return final_prompt
