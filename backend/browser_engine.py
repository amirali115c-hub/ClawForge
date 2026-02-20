"""
Leo 2.0 - Browser Automation Engine
===================================
Playwright-based browser automation for Leo 2.0.
Allows web navigation, form filling, data extraction, and more.
"""

import asyncio
import json
import base64
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class BrowserAction(Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    SCREENSHOT = "screenshot"
    EXTRACT = "extract"
    WAIT = "wait"
    SCROLL = "scroll"
    EVALUATE = "evaluate"


@dataclass
class BrowserSession:
    """A browser session."""
    session_id: str
    page = None
    browser = None
    context = None
    status: str = "idle"
    current_url: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    history: List[Dict] = field(default_factory=list)


class BrowserAutomationEngine:
    """
    Browser automation engine using Playwright.
    
    Capabilities:
    - Navigate to URLs
    - Click elements
    - Fill forms
    - Extract data
    - Take screenshots
    - Execute JavaScript
    """
    
    def __init__(self):
        self.playwright = None
        self.sessions: Dict[str, BrowserSession] = {}
        self.current_session: Optional[BrowserSession] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Playwright."""
        if self._initialized:
            return
        
        try:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self._initialized = True
            print("[BROWSER] Playwright initialized")
        except ImportError:
            print("[BROWSER] Playwright not installed. Run: pip install playwright")
        except Exception as e:
            print(f"[BROWSER] Init error: {e}")
    
    async def create_session(self, headless: bool = True) -> str:
        """Create a new browser session."""
        await self.initialize()
        
        if not self.playwright:
            return None
        
        import uuid
        session_id = str(uuid.uuid4())[:8]
        
        session = BrowserSession(session_id=session_id)
        
        try:
            session.browser = await self.playwright.chromium.launch(headless=headless)
            session.context = await session.browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            session.page = await session.context.new_page()
            session.status = "ready"
        except Exception as e:
            session.status = f"error: {e}"
        
        self.sessions[session_id] = session
        self.current_session = session
        
        return session_id
    
    async def navigate(self, url: str, session_id: str = None) -> Dict:
        """Navigate to a URL."""
        session = self._get_session(session_id)
        if not session or not session.page:
            return {"error": "No active session"}
        
        try:
            await session.page.goto(url, wait_until="domcontentloaded")
            session.current_url = session.page.url
            session.history.append({
                "action": "navigate",
                "url": url,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "status": "ok",
                "url": session.page.url,
                "title": await session.page.title()
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def click(self, selector: str, session_id: str = None) -> Dict:
        """Click an element."""
        session = self._get_session(session_id)
        if not session or not session.page:
            return {"error": "No active session"}
        
        try:
            await session.page.click(selector)
            session.history.append({
                "action": "click",
                "selector": selector,
                "timestamp": datetime.now().isoformat()
            })
            
            return {"status": "ok", "action": "clicked", "selector": selector}
        except Exception as e:
            return {"error": str(e)}
    
    async def type(self, selector: str, text: str, session_id: str = None) -> Dict:
        """Type text into an element."""
        session = self._get_session(session_id)
        if not session or not session.page:
            return {"error": "No active session"}
        
        try:
            await session.page.fill(selector, text)
            session.history.append({
                "action": "type",
                "selector": selector,
                "text_length": len(text),
                "timestamp": datetime.now().isoformat()
            })
            
            return {"status": "ok", "action": "typed", "selector": selector}
        except Exception as e:
            return {"error": str(e)}
    
    async def screenshot(self, session_id: str = None) -> Dict:
        """Take a screenshot."""
        session = self._get_session(session_id)
        if not session or not session.page:
            return {"error": "No active session"}
        
        try:
            screenshot_bytes = await session.page.screenshot()
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
            
            session.history.append({
                "action": "screenshot",
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "status": "ok",
                "screenshot": screenshot_b64,
                "format": "base64"
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def extract(self, selector: str = None, session_id: str = None) -> Dict:
        """Extract data from page."""
        session = self._get_session(session_id)
        if not session or not session.page:
            return {"error": "No active session"}
        
        try:
            if selector:
                # Extract from specific element
                elements = await session.page.query_selector_all(selector)
                data = []
                for el in elements[:50]:  # Limit to 50
                    text = await el.inner_text()
                    tag = await el.evaluate("el => el.tagName")
                    data.append({"tag": tag, "text": text[:200]})
            else:
                # Extract all text content
                data = await session.page.content()
            
            session.history.append({
                "action": "extract",
                "selector": selector,
                "timestamp": datetime.now().isoformat()
            })
            
            return {"status": "ok", "data": data}
        except Exception as e:
            return {"error": str(e)}
    
    async def execute_script(self, script: str, session_id: str = None) -> Dict:
        """Execute JavaScript."""
        session = self._get_session(session_id)
        if not session or not session.page:
            return {"error": "No active session"}
        
        try:
            result = await session.page.evaluate(script)
            
            session.history.append({
                "action": "evaluate",
                "script": script[:100],
                "timestamp": datetime.now().isoformat()
            })
            
            return {"status": "ok", "result": str(result)[:500]}
        except Exception as e:
            return {"error": str(e)}
    
    async def wait_for(self, selector: str, timeout: int = 30000, session_id: str = None) -> Dict:
        """Wait for element."""
        session = self._get_session(session_id)
        if not session or not session.page:
            return {"error": "No active session"}
        
        try:
            await session.page.wait_for_selector(selector, timeout=timeout)
            return {"status": "ok", "selector": selector}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_page_info(self, session_id: str = None) -> Dict:
        """Get current page info."""
        session = self._get_session(session_id)
        if not session or not session.page:
            return {"error": "No active session"}
        
        try:
            return {
                "status": "ok",
                "url": session.page.url,
                "title": await session.page.title(),
                "session_id": session.session_id,
                "status": session.status,
                "history_count": len(session.history)
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def close_session(self, session_id: str = None) -> Dict:
        """Close a browser session."""
        session = self._get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        try:
            if session.page:
                await session.page.close()
            if session.context:
                await session.context.close()
            if session.browser:
                await session.browser.close()
            
            session.status = "closed"
            
            return {"status": "ok", "session_id": session.session_id}
        except Exception as e:
            return {"error": str(e)}
    
    def _get_session(self, session_id: str = None) -> Optional[BrowserSession]:
        """Get session by ID or return current."""
        if session_id:
            return self.sessions.get(session_id)
        return self.current_session
    
    def get_active_sessions(self) -> List[Dict]:
        """Get all active sessions."""
        return [
            {
                "session_id": s.session_id,
                "status": s.status,
                "url": s.current_url,
                "created": s.created_at
            }
            for s in self.sessions.values()
        ]


# Singleton
_browser_engine = None

def get_browser_engine() -> BrowserAutomationEngine:
    global _browser_engine
    if _browser_engine is None:
        _browser_engine = BrowserAutomationEngine()
    return _browser_engine
