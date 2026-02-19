"""
╔═══════════════════════════════════════════════════════════════════════╗
║        AGENT LONG-TERM MEMORY SYSTEM — CLAWFORGE           ║
║        Persistent memory for ClawForge AI Agent            ║
╚═══════════════════════════════════════════════════════════════════════╝

Based on the Python Memory Agent implementation.
Integrates with ClawForge's existing API structure.
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path


# ── CONFIG ────────────────────────────────────────────────────
CONFIG = {
    "memory_file": "agent_memory.json",
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "extract_every": 2,  # extract memory every N exchanges
    "max_facts": 60,
    "max_episodes": 25,
    "max_ctx_len": 3000,
}


# ── DEFAULT MEMORY STRUCTURE ──────────────────────────────────
def default_memory() -> dict:
    return {
        "semantic": {
            "facts": [],
            "preferences": [],
            "profile": {
                "name": None,
                "location": None,
                "occupation": None,
                "goals": None,
            },
        },
        "episodic": {
            "sessions": [],
            "compressed": None,
        },
        "tasks": {
            "open": [],
            "completed": [],
            "blocked": [],
        },
        "meta": {
            "session_count": 0,
            "total_messages": 0,
            "created_at": datetime.now().isoformat(),
            "last_seen": None,
            "version": "1.0",
        },
    }


# ════════════════════════════════════════════════════════════════
# MEMORY MANAGER
# ════════════════════════════════════════════════════════════════
class MemoryManager:
    """Manages persistent memory for ClawForge agent."""
    
    def __init__(self, memory_dir: str = "./workspace"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.memory_dir / CONFIG["memory_file"]
        self.mem: Optional[dict] = None

    # ── LOAD ────────────────────────────────────────────────────
    def load(self) -> dict:
        """Load memory from disk."""
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                self.mem = json.load(f)
            facts = len(self.mem["semantic"]["facts"])
            sessions = len(self.mem["episodic"]["sessions"])
            print(f"[Memory] Loaded: {facts} facts, {sessions} sessions")
        except FileNotFoundError:
            print("[Memory] No existing memory — starting fresh.")
            self.mem = default_memory()
            self.save()
        except json.JSONDecodeError:
            print("[Memory] Corrupted memory file — starting fresh.")
            self.mem = default_memory()
            self.save()
        return self.mem

    # ── SAVE ────────────────────────────────────────────────────
    def save(self):
        """Save memory to disk."""
        if self.mem:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.mem, f, indent=2, ensure_ascii=False)
            # print("[Memory] Saved ✓")

    # ── BUILD CONTEXT BLOCK FOR SYSTEM PROMPT ───────────────────
    def build_context_block(self) -> str:
        """Build memory context block for system prompt injection."""
        m = self.mem
        if not m:
            return ""
        
        lines = ["[LONG-TERM MEMORY — READ THIS BEFORE RESPONDING]"]

        # Session metadata
        if m["meta"]["session_count"] > 0:
            lines.append(f"\nCONTINUITY: Session #{m['meta']['session_count'] + 1}.")
            last_seen = m["meta"]["last_seen"] or "unknown"
            lines.append(f"Last seen: {last_seen}. Total messages: {m['meta']['total_messages']}.")

        # User profile
        profile = {k: v for k, v in m["semantic"]["profile"].items() if v}
        if profile:
            lines.append("\nUSER PROFILE:")
            for k, v in profile.items():
                lines.append(f"  {k}: {v}")

        # Key facts
        if m["semantic"]["facts"]:
            lines.append("\nKEY FACTS:")
            for f in m["semantic"]["facts"][-20:]:
                lines.append(f"  • {f}")

        # Preferences
        if m["semantic"]["preferences"]:
            lines.append("\nUSER PREFERENCES:")
            for p in m["semantic"]["preferences"]:
                lines.append(f"  • {p}")

        # Open tasks
        if m["tasks"]["open"]:
            lines.append("\nOPEN TASKS (not yet completed):")
            for t in m["tasks"]["open"]:
                lines.append(f"  ○ {t}")

        # Compressed old history
        if m["episodic"]["compressed"]:
            lines.append("\nEARLY HISTORY (compressed):")
            lines.append(f"  {m['episodic']['compressed']}")

        # Recent sessions
        for s in m["episodic"]["sessions"][-4:]:
            lines.append(f"\nSession {s['id']} ({s['date']}): {s['summary']}")
            if s.get("key_decisions"):
                lines.append(f"  Decisions: {' | '.join(s['key_decisions'])}")

        lines.append("\n[END OF MEMORY] — Use naturally, reference when relevant.")

        result = "\n".join(lines)
        # Truncate if too long
        if len(result) > CONFIG["max_ctx_len"]:
            result = result[:CONFIG["max_ctx_len"]] + "\n... [memory truncated]"
        return result

    # ── EXTRACT MEMORY FROM CONVERSATION ────────────────────────
    def extract_from_conversation(self, history: List[Dict[str, str]], anthropic_client=None) -> Optional[dict]:
        """Extract structured memory from conversation using Claude."""
        if not anthropic_client:
            return None
            
        convo_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}"
            for m in history[-10:]
        )
        
        existing_profile = json.dumps(self.mem["semantic"]["profile"], ensure_ascii=False)
        existing_facts = json.dumps(self.mem["semantic"]["facts"][-10:], ensure_ascii=False)
        existing_tasks = json.dumps(self.mem["tasks"]["open"], ensure_ascii=False)

        prompt = f"""You are a memory extraction AI. Analyze this conversation and extract structured memory.

EXISTING PROFILE: {existing_profile}
EXISTING FACTS: {existing_facts}
EXISTING TASKS: {existing_tasks}

CONVERSATION:
{convo_text}

Extract ONLY new/changed information. Return VALID JSON only, no markdown:
{{
  "new_facts": ["fact1", "fact2"],
  "profile_updates": {{
    "name": "string or null",
    "location": "string or null",
    "occupation": "string or null",
    "goals": "string or null"
  }},
  "new_preferences": ["preference"],
  "new_open_tasks": ["task"],
  "completed_tasks": ["task text"],
  "blocked_tasks": ["task — reason"],
  "key_decisions": ["decision made"],
  "session_summary": "2-3 sentence summary of what was accomplished"
}}

Rules:
- Only include fields with actual new data
- Use empty arrays [] for nothing new
- null for profile fields not mentioned
- Be specific and factual"""

        try:
            response = anthropic_client.messages.create(
                model=CONFIG["model"],
                max_tokens=600,
                system="You are a precise JSON extraction system. Output only valid JSON.",
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text
            clean = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except Exception as e:
            print(f"[Memory] Extraction failed: {e}")
            return None

    # ── UPDATE MEMORY ────────────────────────────────────────────
    def update(self, extracted: Optional[dict], session_messages: int):
        """Update memory with extracted data."""
        if not extracted or not self.mem:
            return
        
        m = self.mem

        # New facts
        if extracted.get("new_facts"):
            new_facts = list(set(m["semantic"]["facts"] + extracted["new_facts"]))[-CONFIG["max_facts"]:]
            m["semantic"]["facts"] = new_facts

        # Preferences
        if extracted.get("new_preferences"):
            new_prefs = list(set(m["semantic"]["preferences"] + extracted["new_preferences"]))[-20:]
            m["semantic"]["preferences"] = new_prefs

        # Profile updates
        if extracted.get("profile_updates"):
            for k, v in extracted["profile_updates"].items():
                if v is not None:
                    m["semantic"]["profile"][k] = v

        # New tasks
        if extracted.get("new_open_tasks"):
            m["tasks"]["open"].extend(extracted["new_open_tasks"])

        # Completed tasks
        if extracted.get("completed_tasks"):
            for ct in extracted["completed_tasks"]:
                for i, t in enumerate(m["tasks"]["open"]):
                    if ct[:30].lower() in t.lower():
                        m["tasks"]["completed"].append(m["tasks"]["open"].pop(i))
                        break

        # Blocked tasks
        if extracted.get("blocked_tasks"):
            m["tasks"]["blocked"].extend(extracted["blocked_tasks"])

        # Session summary
        if extracted.get("session_summary"):
            episode = {
                "id": m["meta"]["session_count"],
                "date": datetime.now().strftime("%b %d, %Y"),
                "summary": extracted["session_summary"],
                "key_decisions": extracted.get("key_decisions", []),
                "message_count": session_messages,
            }
            m["episodic"]["sessions"].append(episode)

            # Compress old episodes if needed
            if len(m["episodic"]["sessions"]) > CONFIG["max_episodes"]:
                self._compress_old_episodes()

        # Update meta
        m["meta"]["total_messages"] += session_messages
        m["meta"]["last_seen"] = datetime.now().isoformat()
        self.save()

    # ── COMPRESS OLD EPISODES ─────────────────────────────────────
    def _compress_old_episodes(self, anthropic_client=None):
        """Compress old sessions to save space."""
        if not anthropic_client:
            return
            
        to_compress = self.mem["episodic"]["sessions"][:10]
        text = "\n".join(
            f"Session {s['id']} ({s['date']}): {s['summary']}" 
            for s in to_compress
        )
        
        try:
            response = anthropic_client.messages.create(
                model=CONFIG["model"],
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": f"Compress these session summaries into 2-3 sentences of key context:\n\n{text}"
                }],
            )
            compressed = response.content[0].text
            existing = self.mem["episodic"]["compressed"]
            self.mem["episodic"]["compressed"] = (
                f"{existing} | {compressed}" if existing else compressed
            )
            self.mem["episodic"]["sessions"] = self.mem["episodic"]["sessions"][10:]
            print("[Memory] Compressed old episodes ✓")
        except Exception as e:
            print(f"[Memory] Compression failed: {e}")

    def start_new_session(self):
        """Increment session counter."""
        if self.mem:
            self.mem["meta"]["session_count"] += 1
            self.mem["meta"]["last_seen"] = datetime.now().isoformat()
            self.save()

    # ── UTILITY METHODS ──────────────────────────────────────────
    def get_stats(self) -> dict:
        """Get memory statistics."""
        if not self.mem:
            return {"total": 0, "facts": 0, "sessions": 0, "tasks": 0}
        return {
            "total": len(self.mem["semantic"]["facts"]),
            "facts": len(self.mem["semantic"]["facts"]),
            "preferences": len(self.mem["semantic"]["preferences"]),
            "sessions": len(self.mem["episodic"]["sessions"]),
            "open_tasks": len(self.mem["tasks"]["open"]),
            "completed_tasks": len(self.mem["tasks"]["completed"]),
            "session_count": self.mem["meta"]["session_count"],
            "total_messages": self.mem["meta"]["total_messages"],
            "last_seen": self.mem["meta"]["last_seen"],
        }

    def get_facts(self, limit: int = 20) -> List[str]:
        """Get recent facts."""
        if not self.mem:
            return []
        return self.mem["semantic"]["facts"][-limit:]

    def get_tasks(self) -> dict:
        """Get all tasks."""
        if not self.mem:
            return {"open": [], "completed": []}
        return {
            "open": self.mem["tasks"]["open"],
            "completed": self.mem["tasks"]["completed"],
            "blocked": self.mem["tasks"]["blocked"],
        }

    def clear(self):
        """Clear all memory."""
        self.mem = default_memory()
        self.save()
        print("[Memory] All memory cleared.")


# ════════════════════════════════════════════════════════════════
# MEMORY AGENT WRAPPER
# ════════════════════════════════════════════════════════════════
class MemoryAgent:
    """Agent wrapper with persistent memory."""
    
    def __init__(self, memory_manager: MemoryManager, agent_name: str = "ClawForge"):
        self.memory = memory_manager
        self.agent_name = agent_name
        self.history = []
        self.exchange_count = 0
        self.system_prompt = ""

    def boot(self) -> str:
        """Boot the agent and load memory."""
        print(f"\n[Agent] Booting {self.agent_name}...")
        print("[Agent] Loading long-term memory...")

        self.memory.load()
        is_returning = self.memory.mem["meta"]["session_count"] > 0
        self.memory.start_new_session()

        mem_ctx = self.memory.build_context_block()

        self.system_prompt = f"""{mem_ctx}

You are {self.agent_name}, a persistent AI agent with genuine long-term memory.
{"You are restarting after a previous session. Greet the user warmly and naturally reference where you left off — the most relevant open task or recent topic. Be natural, not robotic. 2-3 sentences max." if is_returning else "This is your first session. Introduce yourself and explain you will remember everything between sessions."}

During conversation:
- Reference memory naturally when relevant
- Acknowledge when user shares new info you're storing
- Connect current topics to past context
- Proactively track and mention tasks"""

        return is_returning

    def get_system_prompt(self) -> str:
        """Get the current system prompt with memory injection."""
        return self.system_prompt

    def chat(self, user_message: str, anthropic_client=None) -> str:
        """Process a chat message with memory."""
        self.history.append({"role": "user", "content": user_message})
        self.exchange_count += 1

        if not anthropic_client:
            return "Error: Anthropic client not provided"

        # Generate response
        try:
            response = anthropic_client.messages.create(
                model=CONFIG["model"],
                max_tokens=CONFIG["max_tokens"],
                system=self.system_prompt,
                messages=self.history[-20:],
            )
            reply = response.content[0].text
            self.history.append({"role": "assistant", "content": reply})

            # Auto-extract memory every N exchanges
            if self.exchange_count % CONFIG["extract_every"] == 0:
                print("\n[Memory] Extracting memory...")
                extracted = self.memory.extract_from_conversation(self.history, anthropic_client)
                self.memory.update(extracted, self.exchange_count * 2)
                print("[Memory] Memory updated ✓\n")

            return reply
        except Exception as e:
            return f"Error: {str(e)}"

    def extract_and_save(self, anthropic_client=None):
        """Extract and save memory manually."""
        if not anthropic_client:
            return
        extracted = self.memory.extract_from_conversation(self.history, anthropic_client)
        self.memory.update(extracted, len(self.history))

    def shutdown(self, anthropic_client=None):
        """Shutdown and save final memory state."""
        print(f"\n[Agent] Shutting down {self.agent_name}...")
        if anthropic_client:
            extracted = self.memory.extract_from_conversation(self.history, anthropic_client)
            self.memory.update(extracted, len(self.history))
        print("[Agent] Final memory saved. Goodbye.")


# ════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ════════════════════════════════════════════════════════════════
def create_memory_agent(agent_name: str = "ClawForge", memory_dir: str = "./workspace") -> MemoryAgent:
    """Create and boot a memory agent. One function call."""
    mem_manager = MemoryManager(memory_dir)
    agent = MemoryAgent(mem_manager, agent_name)
    agent.boot()
    return agent


# ════════════════════════════════════════════════════════════════
# CLI EXAMPLE
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import anthropic
    
    client = anthropic.Anthropic()
    agent = create_memory_agent("ClawForge")
    
    print("\n(Type 'exit' to quit and save memory)\n")
    
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "bye"):
            agent.shutdown(client)
            break
        reply = agent.chat(user_input, client)
        print(f"\n{agent.agent_name}: {reply}\n")
