# Fix extended_personas.py to properly register personas

# Read the current file
with open('extended_personas.py', 'r') as f:
    content = f.read()

# Check if register function already exists
if 'def register_extended_personas' in content:
    print('Function already exists')
else:
    # Add the function at the end
    appendix = '''

# Add all extended personas to the main PromptEngine class
def register_extended_personas(engine):
    """Register all extended personas with a PromptEngine instance."""
    # Update the class attribute so all instances can access it
    from prompt_engine import PromptEngine
    for name, persona in EXTENDED_PERSONAS.items():
        PromptEngine.DEFAULT_PERSONAS[name] = persona
    return engine


def load_all_personas():
    """Load all personas including extended ones."""
    from prompt_engine import PromptEngine
    engine = PromptEngine()
    register_extended_personas(engine)
    return engine
'''
    with open('extended_personas.py', 'a') as f:
        f.write(appendix)
    print('Added register function')
