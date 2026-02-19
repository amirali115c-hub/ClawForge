
# ============================================================================
# AGENT CONFIG (Added for CLI)
# ============================================================================

class AgentConfig:
    """Agent configuration container."""
    
    def __init__(self):
        self.name = AGENT_NAME
        self.version = AGENT_VERSION
        self.role = AGENT_ROLE
        self.mission = CORE_MISSION
        self.capabilities = CAPABILITIES
        self.never_do = NEVER_DO
        self.always_do = ALWAYS_DO
        self.output_sections = OUTPUT_SECTIONS
        self.security_mode = DEFAULT_SECURITY_MODE


def print_banner():
    """Print ClawForge banner."""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🦁  ClawForge v4.0                                                    ║
║                                                                          ║
║   Production-grade Autonomous AI Agent                                   ║
║   Full-stack AI operator: planner, executor, tool user                   ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
