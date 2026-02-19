# Advanced Prompt Understanding Engine

## Overview

The **Advanced Prompt Understanding Engine** implements all 25 advanced prompt understanding features for ClawForge. This engine provides comprehensive control over how Claude interprets and responds to prompts.

## Features (25 Total)

### 1. Role & Persona Assignment
Assign specific roles or personas to shape behavior, tone, and expertise.
- **Default Personas**: cybersecurity_expert, philosophy_tutor, business_consultant, creative_writer, technical_writer, data_scientist
- **Custom Personas**: Create your own with custom tone, characteristics, and constraints

### 2. System Prompt Layering
Add multiple persistent system prompt layers with priority ordering.

### 3. Explicit Output Formatting Control
Control exactly how output looks:
- **Format**: JSON, Markdown, YAML, XML, Prose, Bullets, Numbered, Table, Code
- **Length**: Short, Medium, Long, Exhaustive
- **Structure**: Headers, Prose, Bullets, Numbered, Table
- **Max Words**: Limit response length

### 4. XML / Structured Tag Instructions
Use XML-style tags to structure prompts:
- `<context>`, `<task>`, `<format>`, `<examples>`, `<constraints>`
- `<tone>`, `<audience>`, `<purpose>`, `<background>`
- `<thinking>`, `<reasoning>`, `<output>`, `<step>`
- Custom tags are parsed and respected

### 5. Chain-of-Thought (CoT) Prompting
Enable step-by-step reasoning for complex tasks.
- Show reasoning process in response
- Break problems into logical components
- Consider alternative approaches

### 6. Few-Shot & Many-Shot Examples
Teach patterns with input/output examples:
- **Zero-shot**: No examples
- **One-shot**: 1 example
- **Few-shot**: 2-5 examples
- **Many-shot**: 10+ examples

### 7. Positive & Negative Constraints
Specify what to do and what to avoid:
- **Positive**: "Always cite sources", "Use technical vocabulary"
- **Negative**: "Never use bullet points", "Avoid hedging language"

### 8. Audience Targeting
Tailor responses to specific audiences:
- **Expertise**: child, teen, adult, expert, phd
- **Technical**: non_technical, semi_technical, highly_technical
- **Interests**: List relevant interests

### 9. Conditional / If-Then Logic
Add branching logic to prompts:
```
If user asks about pricing → respond with X
If user asks about features → respond with Y
```

### 10. Task Decomposition Instructions
Break complex tasks into subtasks automatically.

### 11. Meta-Prompting (Prompt Refinement)
Critique and improve prompts:
- Generate improvement suggestions
- Auto-enhance prompts with structure

### 12. Context Window Utilization
Manage long conversations and documents:
- Track conversation history
- Reference external documents
- Estimate token usage

### 13. Instruction Priority & Conflict Resolution
Hierarchical instruction following:
1. Safety/ethics (non-negotiable)
2. System prompt layers
3. Persona constraints
4. User instructions
5. Inferred intent

### 14. Tone & Register Control
Fine-grained tone control:
- neutral, formal, casual, empathetic, authoritative
- playful, clinical, socratic, blunt, diplomatic
- persuasive, technical

### 15. Output Anchoring with Prefills
Anchor output format with prefixes/suffixes:
- Force specific beginning: "Here is the answer:"
- Force specific ending: "Let me know if you need more."

### 16. Multi-Turn Conversation Control
Maintain context across conversations:
- Reference previous messages
- Revise earlier points
- Build iteratively

### 17. Perspective & Stance Control
Control viewpoint and stance:
- neutral, first_person, third_person
- devils_advocate, argue_for, argue_against
- steelman (strongest argument first)

### 18. Language & Localization
Respond in any language:
- Set language code (en, es, fr, de, etc.)
- Dialect support (en-US, en-UK)
- Regional conventions (spelling, idioms)

### 19. Specificity Dial
Control detail level:
- **high_level**: Overview only
- **medium**: Balanced
- **detailed**: Comprehensive
- **granular**: Implementation-level with edge cases

### 20. Constraint Stacking
Layer multiple constraints simultaneously - all are tracked and respected.

### 21. Iterative Refinement Instructions
Self-review before responding:
- Draft → Review → Improve → Finalize
- Check logical consistency
- Validate completeness

### 22. Custom Vocabulary / Style Mirroring
Match specific writing styles:
- Provide style sample to mirror
- Add vocabulary preferences
- Add vocabulary restrictions

### 23. Hypothetical & Counterfactual Framing
Handle "what-if" scenarios:
- Engage fully with hypothetical premises
- Distinguish facts from hypotheticals
- Explore implications

### 24. Knowledge Scope Limiting
Restrict knowledge sources:
- **unlimited**: Use all training knowledge
- **provided_only**: Only provided documents
- **conversation_only**: Only conversation history

### 25. Error & Uncertainty Handling
Control how uncertainty is handled:
- **acknowledge**: Say "I don't know"
- **guess**: Make reasonable inferences
- **ask_clarification**: Ask for clarification
- Confidence ratings for claims

## Quick Start

### Basic Usage

```python
from prompt_engine import PromptEngine, PromptContext

engine = PromptEngine()

# Create context
context = PromptContext()

# Set a persona
context = engine.set_persona(context, "technical_writer")

# Enable chain-of-thought
context = engine.enable_chain_of_thought(context, show_reasoning=True)

# Set output format
context = engine.set_formatting(context, format="markdown", length="medium")

# Compile the prompt
system_prompt = engine.compile_prompt(context, user_message="Explain Python decorators")
```

### Using the API

```bash
# List available personas
GET /api/prompt/personas

# List all features
GET /api/prompt/features

# Compile a prompt
POST /api/prompt/compile
{
    "user_message": "Explain quantum computing",
    "persona": {"persona_name": "technical_writer"},
    "formatting": {"format": "markdown", "length": "medium"},
    "audience": {"name": "Curious Learner", "expertise_level": "teen"}
}

# Critique a prompt
POST /api/prompt/critique
{"prompt": "Your prompt here"}
```

### Complete Example

```python
from prompt_engine import PromptEngine, PromptContext, Tone

engine = PromptEngine()
context = PromptContext()

# Set a custom persona
context = engine.set_persona(context, "data_scientist")

# Add constraints
context = engine.add_constraint(context, "positive", "Support claims with evidence", "content")
context = engine.add_constraint(context, "negative", "Make up statistics", "behavior")

# Add examples
context = engine.add_example(
    context,
    input_text="What is linear regression?",
    output_text="Linear regression is a supervised learning algorithm..."
)

# Set audience
context = engine.set_audience(
    context,
    name="Data Science Student",
    expertise_level="adult",
    technical_level="semi_technical"
)

# Enable reasoning
context = engine.enable_chain_of_thought(context, show_reasoning=True)

# Set specificity
context = engine.set_specificity(context, "detailed")

# Compile
prompt = engine.compile_prompt(
    context,
    user_message="Explain how random forests work"
)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/prompt/personas` | List available personas and options |
| GET | `/api/prompt/features` | List all 25 features |
| POST | `/api/prompt/compile` | Compile a complete prompt |
| POST | `/api/prompt/critique` | Critique and improve a prompt |
| POST | `/api/prompt/parse-xml` | Parse XML tags from text |
| POST | `/api/prompt/evaluate-conditions` | Test conditional rules |
| GET | `/api/prompt/examples` | Get usage examples |

## File Structure

```
backend/
├── api.py                 # Main API with all routes
├── prompt_engine.py        # Core prompt engine (1450+ lines)
└── prompt_api.py          # API routes for prompt engine
```

## Default Personas

| Persona | Role | Tone |
|---------|------|------|
| cybersecurity_expert | Senior Cybersecurity Analyst | authoritative |
| philosophy_tutor | Socratic Philosophy Tutor | socratic |
| business_consultant | Senior Strategy Consultant | diplomatic |
| creative_writer | Novelist and Content Creator | playful |
| technical_writer | Documentation Specialist | technical |
| data_scientist | Senior Data Scientist | technical |

## Tone Options

1. **neutral** - Objective and balanced
2. **formal** - Professional and structured
3. **casual** - Conversational and relaxed
4. **empathetic** - Understanding and supportive
5. **authoritative** - Confident and decisive
6. **playful** - Creative and engaging
7. **clinical** - Precise and detached
8. **socratic** - Questioning and guiding
9. **blunt** - Direct and straightforward
10. **diplomatic** - Tactful and balanced
11. **persuasive** - Compelling and convincing
12. **technical** - Exact and specialized

## Output Format Options

1. **json** - Valid JSON output
2. **markdown** - Markdown with headers and code blocks
3. **yaml** - Valid YAML output
4. **xml** - Valid XML output
5. **prose** - Flowing paragraphs, no lists
6. **bullets** - Bullet point lists
7. **numbered** - Numbered steps/lists
8. **table** - Tabular format
9. **code** - Syntax-highlighted code blocks

## Best Practices

1. **Start with persona** - Set the voice first
2. **Be specific** - Use the specificity dial
3. **Add examples** - Few-shot is powerful
4. **Use constraints** - Both positive and negative
5. **Enable CoT** - For complex reasoning
6. **Match audience** - Tailor to readers
7. **Control format** - Specify exact output style
8. **Handle uncertainty** - Set expectations

## Example Prompts

### Technical Documentation
```json
{
    "user_message": "Write API documentation for user login",
    "persona": {"persona_name": "technical_writer"},
    "formatting": {"format": "markdown"},
    "specificity": "detailed"
}
```

### Business Proposal
```json
{
    "user_message": "Create a project proposal",
    "persona": {"persona_name": "business_consultant"},
    "formatting": {"format": "prose", "length": "long"},
    "audience": {"name": "Executive Team", "expertise_level": "adult"}
}
```

### Educational Content
```json
{
    "user_message": "Explain photosynthesis",
    "chain_of_thought": true,
    "audience": {"name": "Middle School Students", "expertise_level": "child", "technical_level": "non_technical"},
    "tone": "playful"
}
```

## License

Part of ClawForge - see main LICENSE file.
