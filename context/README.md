# ClawForge Conversation Continuity System

A privacy-first memory system for ClawForge that works like my own memory does.

## Features

### Conversation Continuity
- **Auto-save/restore** - Remembers where you left off between sessions
- **Task tracking** - Knows what was being worked on
- **Next steps** - Remembers upcoming tasks
- **Session history** - Keeps context of what happened

### Privacy Protection Layers

| Layer | Description |
|-------|-------------|
| **Data Classification** | Auto-detects sensitive data (passwords, API keys, PII) |
| **Encryption** | Optional encryption for confidential data |
| **Access Logging** | Tracks when sensitive data is accessed |
| **Auto-cleanup** | Removes logs older than 30 days |
| **Retention Controls** | Session-only or persistent storage options |

### Privacy Levels

- **public** - No restrictions
- **standard** - Basic protection (default)
- **confidential** - Encrypted, access logged
- **restricted** - Requires explicit consent

## Quick Start

### Python Usage

```python
from context.context_manager import start_session, update_context, get_resume_context, end_session

# Start a new session
conversation_id = start_session(user_context={"name": "Amir"})

# Update context as work progresses
update_context(
    current_task="Fixing login bug",
    where_left_off="Found the issue in auth.py line 42",
    next_steps=["Fix the token validation", "Test the fix"],
    task_status="executing"
)

# Later - get context for resuming
resume_context = get_resume_context()
# Output:
# [TASK] Fixing login bug
# [EXECUTING] Status: executing
# [PAUSED] Found the issue in auth.py line 42
# [NEXT] Next steps:
#    - Fix the token validation
#    - Test the fix

# End session when done
end_session(summary="Fixed authentication issue")
```

### API Usage

```bash
# Start session
curl -X POST http://localhost:8000/context/session/start

# Update context
curl -X POST http://localhost:8000/context/session/update \
  -H "Content-Type: application/json" \
  -d '{"current_task": "Deploy app", "task_status": "planning"}'

# Get resume context
curl http://localhost:8000/context/session/resume

# End session
curl -X POST http://localhost:8000/context/session/end \
  -H "Content-Type: application/json" \
  -d '{"summary": "Deployed successfully"}'

# Check privacy status
curl http://localhost:8000/context/privacy/status
```

## File Structure

```
ClawForge/
├── context/                    # Conversation continuity system
│   ├── context_manager.py      # Core system
│   ├── context_api.py         # FastAPI endpoints
│   ├── context_integration.py # API integration
│   ├── conversation_state.json # Current state (active session)
│   ├── conversation_state.example.json # Template
│   ├── .key                   # Encryption key (auto-generated)
│   └── daily_logs/
│       ├── 2026-02-19.jsonl
│       ├── 2026-02-18.jsonl
│       └── ...
└── ...
```

## Privacy Rules

### What Gets Stored (Allowed)
- Task names and descriptions
- Non-sensitive preferences
- General context
- Session timestamps

### What Gets Rejected
- Passwords
- API keys/tokens
- Credit card numbers
- SSN or government IDs

### What Gets Encrypted
- Email addresses
- Phone numbers
- Physical addresses
- Names (optional)

## Integration

To integrate with ClawForge's main agent, add this to your agent's session handling:

```python
from context.context_manager import get_context_manager

class ClawForgeAgent:
    def __init__(self):
        self.context = get_context_manager()
    
    def start_interaction(self, user_input):
        # Check if there's previous context
        if not self.context.get_context().get("conversation_id"):
            self.context.start_session()
        
        # Get resume context if starting fresh
        resume = self.context.get_resume_context()
        
        # ... process with context ...
    
    def end_interaction(self):
        # Auto-save state
        self.context._save_state()
```

## Security Notes

1. **Encryption key** - Stored in `.key` file, auto-generated on first run
2. **No PII by default** - Sensitive data is rejected unless explicitly allowed
3. **Access logging** - Tracks when confidential data is accessed
4. **Auto-cleanup** - Logs older than 30 days are automatically deleted

---

*Built with privacy first.*
