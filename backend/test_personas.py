# Direct test of prompt engine without HTTP
from prompt_engine import PromptEngine, PromptContext
from extended_personas import load_all_personas

# Load all personas
engine = load_all_personas()
print(f'Total personas: {len(engine.DEFAULT_PERSONAS)}')
print(f'\\nAvailable personas:')
for name in sorted(engine.DEFAULT_PERSONAS.keys()):
    print(f'  - {name}')

# Test SEO Specialist persona
print('\\n=== Testing SEO Specialist Persona ===')
context = PromptContext()
context = engine.set_persona(context, 'seo_specialist')
persona_prompt = engine.apply_persona_to_prompt(context)
print(persona_prompt[:800])
