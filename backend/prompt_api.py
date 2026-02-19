"""
Prompt Engine API Routes
Integrates the Advanced Prompt Understanding Engine with ClawForge API.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

from prompt_engine import (
    PromptEngine,
    PromptContext,
    Persona,
    Tone,
    Perspective,
    SpecificityLevel,
    OutputFormat,
)

router = APIRouter(prefix="/api/prompt", tags=["Prompt Engine"])

# Load prompt engine with all personas registered
try:
    from extended_personas import load_all_personas
    prompt_engine = load_all_personas()
    print(f"[PROMPT] Loaded {len(prompt_engine.DEFAULT_PERSONAS)} personas total")
except ImportError:
    prompt_engine = PromptEngine()
    print("[PROMPT] Extended personas not available")
except ImportError:
    print("[PROMPT] Extended personas not available")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PersonaRequest(BaseModel):
    """Request to set persona."""
    persona_name: str
    custom_name: Optional[str] = None
    custom_role: Optional[str] = None
    custom_expertise: Optional[str] = None
    custom_tone: Optional[str] = None


class FormattingRequest(BaseModel):
    """Request to set formatting options."""
    format: str = "prose"  # json, markdown, yaml, xml, prose, bullets, numbered, table, code
    length: Optional[str] = None  # short, medium, long, exhaustive
    structure: Optional[str] = None  # headers, prose, bullets, numbered, table
    max_words: Optional[int] = None


class ConstraintRequest(BaseModel):
    """Request to add constraint."""
    type: str = "positive"  # positive or negative
    description: str
    category: str = "style"  # style, content, format, behavior


class ExampleRequest(BaseModel):
    """Request to add example."""
    input_text: str
    output_text: str
    explanation: Optional[str] = None


class AudienceRequest(BaseModel):
    """Request to set audience."""
    name: str
    expertise_level: str  # child, teen, adult, expert, phd
    technical_level: str = "semi_technical"  # non_technical, semi_technical, highly_technical
    interests: List[str] = []


class ConditionalRequest(BaseModel):
    """Request to add conditional rule."""
    condition: str
    response: str


class CompileRequest(BaseModel):
    """Request to compile prompt."""
    user_message: str
    persona: Optional[PersonaRequest] = None
    formatting: Optional[FormattingRequest] = None
    constraints: List[ConstraintRequest] = []
    examples: List[ExampleRequest] = []
    audience: Optional[AudienceRequest] = None
    chain_of_thought: bool = False
    show_reasoning: bool = True
    task_decomposition: bool = False
    conditionals: List[ConditionalRequest] = []
    tone: Optional[str] = None
    perspective: Optional[str] = None
    language: str = "en"
    dialect: Optional[str] = None
    region: Optional[str] = None
    specificity: str = "medium"
    self_review: bool = False
    critique_before_final: bool = False
    knowledge_scope: str = "unlimited"
    uncertainty_handling: str = "acknowledge"
    output_prefix: Optional[str] = None
    output_suffix: Optional[str] = None
    style_sample: Optional[str] = None
    vocabulary_preferences: List[str] = []
    vocabulary_restrictions: List[str] = []


class CompileResponse(BaseModel):
    """Response with compiled prompt."""
    system_prompt: str
    features_used: List[str]
    token_estimate: int


# ============================================================================
# API ROUTES
# ============================================================================

@router.get("/personas")
async def list_personas() -> Dict[str, Any]:
    """List available personas."""
    return {
        "personas": list(prompt_engine.DEFAULT_PERSONAS.keys()),
        "tones": [t.value for t in Tone],
        "perspectives": [p.value for p in Perspective],
        "specificity_levels": [s.value for s in SpecificityLevel],
        "output_formats": [f.value for f in OutputFormat],
    }


@router.get("/features")
async def list_features() -> Dict[str, Any]:
    """List all 25 prompt understanding features."""
    return {
        "features": [
            {"id": 1, "name": "Role & Persona Assignment"},
            {"id": 2, "name": "System Prompt Layering"},
            {"id": 3, "name": "Explicit Output Formatting Control"},
            {"id": 4, "name": "XML / Structured Tag Instructions"},
            {"id": 5, "name": "Chain-of-Thought (CoT) Prompting"},
            {"id": 6, "name": "Few-Shot & Many-Shot Examples"},
            {"id": 7, "name": "Positive & Negative Constraints"},
            {"id": 8, "name": "Audience Targeting"},
            {"id": 9, "name": "Conditional / If-Then Logic"},
            {"id": 10, "name": "Task Decomposition Instructions"},
            {"id": 11, "name": "Meta-Prompting (Prompt Refinement)"},
            {"id": 12, "name": "Context Window Utilization"},
            {"id": 13, "name": "Instruction Priority & Conflict Resolution"},
            {"id": 14, "name": "Tone & Register Control"},
            {"id": 15, "name": "Output Anchoring with Prefills"},
            {"id": 16, "name": "Multi-Turn Conversation Control"},
            {"id": 17, "name": "Perspective & Stance Control"},
            {"id": 18, "name": "Language & Localization"},
            {"id": 19, "name": "Specificity Dial"},
            {"id": 20, "name": "Constraint Stacking"},
            {"id": 21, "name": "Iterative Refinement Instructions"},
            {"id": 22, "name": "Custom Vocabulary / Style Mirroring"},
            {"id": 23, "name": "Hypothetical & Counterfactual Framing"},
            {"id": 24, "name": "Knowledge Scope Limiting"},
            {"id": 25, "name": "Error & Uncertainty Handling"},
        ]
    }


@router.post("/compile", response_model=CompileResponse)
async def compile_prompt(request: CompileRequest) -> CompileResponse:
    """Compile a complete prompt with all features."""
    
    # Create prompt context
    context = PromptContext()
    
    # Apply persona
    if request.persona:
        if request.persona.persona_name in prompt_engine.DEFAULT_PERSONAS:
            context = prompt_engine.set_persona(context, request.persona.persona_name)
        else:
            # Custom persona
            tone_map = {
                'neutral': Tone.NEUTRAL, 'formal': Tone.FORMAL, 'casual': Tone.CASUAL,
                'empathetic': Tone.EMPATHETIC, 'authoritative': Tone.AUTHORITATIVE,
                'playful': Tone.PLAYFUL, 'clinical': Tone.CLINICAL, 'socratic': Tone.SOCRATIC,
                'blunt': Tone.BLUNT, 'diplomatic': Tone.DIPLOMATIC,
                'persuasive': Tone.PERSUASIVE, 'technical': Tone.TECHNICAL,
            }
            custom_tone = tone_map.get(request.persona.custom_tone or "neutral", Tone.NEUTRAL)
            persona = prompt_engine.create_custom_persona(
                name=request.persona.custom_name or request.persona.persona_name,
                role=request.persona.custom_role or request.persona.persona_name,
                expertise_level=request.persona.custom_expertise or "custom",
                tone=custom_tone,
            )
            context.persona = persona
    
    # Apply formatting
    if request.formatting:
        context = prompt_engine.set_formatting(
            context,
            format=request.formatting.format,
            length=request.formatting.length,
            structure=request.formatting.structure,
            max_words=request.formatting.max_words
        )
    
    # Add constraints
    for constraint in request.constraints:
        context = prompt_engine.add_constraint(
            context,
            constraint_type=constraint.type,
            description=constraint.description,
            category=constraint.category
        )
    
    # Add examples
    for example in request.examples:
        context = prompt_engine.add_example(
            context,
            input_text=example.input_text,
            output_text=example.output_text,
            explanation=example.explanation
        )
    
    # Set audience
    if request.audience:
        context = prompt_engine.set_audience(
            context,
            name=request.audience.name,
            expertise_level=request.audience.expertise_level,
            technical_level=request.audience.technical_level,
            interests=request.audience.interests
        )
    
    # Enable CoT
    if request.chain_of_thought:
        context = prompt_engine.enable_chain_of_thought(context, request.show_reasoning)
    
    # Enable task decomposition
    if request.task_decomposition:
        context = prompt_engine.enable_task_decomposition(context)
    
    # Add conditionals
    for conditional in request.conditionals:
        context = prompt_engine.add_conditional_rule(
            context,
            condition=conditional.condition,
            response=conditional.response
        )
    
    # Set tone
    if request.tone:
        context = prompt_engine.set_tone(context, request.tone)
    
    # Set perspective
    if request.perspective:
        context = prompt_engine.set_perspective(context, request.perspective)
    
    # Set language
    if request.language:
        context = prompt_engine.set_language(context, request.language, request.dialect, request.region)
    
    # Set specificity
    context = prompt_engine.set_specificity(context, request.specificity)
    
    # Enable self-review
    if request.self_review:
        context = prompt_engine.enable_self_review(context)
    
    # Enable critique
    if request.critique_before_final:
        context = prompt_engine.enable_critique_before_final(context)
    
    # Set knowledge scope
    context = prompt_engine.set_knowledge_scope(context, request.knowledge_scope)
    
    # Set uncertainty handling
    context = prompt_engine.set_uncertainty_handling(context, request.uncertainty_handling)
    
    # Set output anchoring
    if request.output_prefix:
        context = prompt_engine.set_output_prefix(context, request.output_prefix)
    if request.output_suffix:
        context = prompt_engine.set_output_suffix(context, request.output_suffix)
    
    # Set style sample
    if request.style_sample:
        context = prompt_engine.set_style_sample(context, request.style_sample)
    
    # Add vocabulary preferences/restrictions
    for word in request.vocabulary_preferences:
        context = prompt_engine.add_vocabulary_preference(context, word)
    for word in request.vocabulary_restrictions:
        context = prompt_engine.add_vocabulary_restriction(context, word)
    
    # Compile the prompt
    compiled = prompt_engine.compile_prompt(context, request.user_message)
    
    # Calculate features used
    features_used = []
    if request.persona or context.persona:
        features_used.append("Persona Assignment")
    if request.formatting:
        features_used.append("Output Formatting")
    if request.constraints:
        features_used.append("Constraints")
    if request.examples:
        features_used.append("Few-Shot Examples")
    if request.audience:
        features_used.append("Audience Targeting")
    if request.chain_of_thought:
        features_used.append("Chain-of-Thought")
    if request.task_decomposition:
        features_used.append("Task Decomposition")
    if request.conditionals:
        features_used.append("Conditional Logic")
    if request.tone:
        features_used.append("Tone Control")
    if request.perspective:
        features_used.append("Perspective Control")
    if request.language:
        features_used.append("Language & Localization")
    if request.specificity != "medium":
        features_used.append("Specificity Dial")
    if request.self_review or request.critique_before_final:
        features_used.append("Iterative Refinement")
    if request.knowledge_scope != "unlimited":
        features_used.append("Knowledge Scope Limiting")
    if request.uncertainty_handling != "acknowledge":
        features_used.append("Uncertainty Handling")
    if request.output_prefix or request.output_suffix:
        features_used.append("Output Anchoring")
    if request.style_sample:
        features_used.append("Style Mirroring")
    
    # Estimate tokens
    token_estimate = prompt_engine.estimate_context_usage(context)
    
    return CompileResponse(
        system_prompt=compiled,
        features_used=features_used,
        token_estimate=token_estimate
    )


@router.post("/critique")
async def critique_prompt(prompt: str) -> Dict[str, Any]:
    """Critique a prompt and suggest improvements."""
    critique = prompt_engine.generate_prompt_critique(prompt)
    improved = prompt_engine.improve_prompt(prompt)
    return {
        "original_prompt": prompt,
        "critique": critique,
        "improved_prompt": improved
    }


@router.post("/parse-xml")
async def parse_xml_tags(text: str) -> Dict[str, str]:
    """Parse XML-style tags from text."""
    parsed = prompt_engine.parse_xml_tags(text)
    return {"parsed_tags": parsed, "count": len(parsed)}


@router.post("/evaluate-conditions")
async def evaluate_conditions(
    user_input: str,
    rules: Dict[str, str]
) -> Dict[str, Any]:
    """Evaluate conditional rules against user input."""
    context = PromptContext()
    for condition, response in rules.items():
        context = prompt_engine.add_conditional_rule(context, condition, response)
    
    matched = prompt_engine.evaluate_conditions(context, user_input)
    return {
        "user_input": user_input,
        "matched_rules": matched,
        "rule_count": len(rules),
        "matched_count": len(matched)
    }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

EXAMPLE_USAGE = """
# Example 1: Set a persona with formatting
POST /api/prompt/compile
{
    "user_message": "Explain quantum computing to me",
    "persona": {"persona_name": "technical_writer"},
    "formatting": {"format": "markdown", "length": "medium"},
    "audience": {"name": "Curious Learner", "expertise_level": "teen", "technical_level": "non_technical"}
}

# Example 2: Chain-of-thought with constraints
POST /api/prompt/compile
{
    "user_message": "Should I invest in stocks or bonds?",
    "chain_of_thought": true,
    "show_reasoning": true,
    "constraints": [
        {"type": "positive", "description": "Consider risk tolerance", "category": "content"},
        {"type": "negative", "description": "Give specific financial advice", "category": "behavior"}
    ],
    "perspective": "neutral"
}

# Example 3: Few-shot examples with specific format
POST /api/prompt/compile
{
    "user_message": "Write a haiku about autumn",
    "formatting": {"format": "prose"},
    "examples": [
        {"input_text": "Write a haiku about spring", "output_text": "Cherry blossoms fall\nPetals dance in morning light\nWinter's grip releases"}
    ]
}

# Example 4: Persona with language and tone
POST /api/prompt/compile
{
    "user_message": "Tell me about machine learning",
    "persona": {"persona_name": "data_scientist"},
    "tone": "technical",
    "specificity": "detailed",
    "knowledge_scope": "unlimited"
}
"""

@router.get("/examples")
async def get_examples() -> Dict[str, Any]:
    """Get usage examples."""
    return {"examples": EXAMPLE_USAGE}
