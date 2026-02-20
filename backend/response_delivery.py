"""
Leo 2.0 Response Delivery Engine
Based on OpenClaw's mechanism - Formats, validates, and delivers responses across channels.
"""

import re
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import html


class ChannelType(Enum):
    """Output channel types."""
    WEBCHAT = "webchat"
    TERMINAL = "terminal"
    API = "api"
    MARKDOWN = "markdown"
    HTML = "html"
    PLAIN = "plain"


@dataclass
class ResponseElement:
    """A single element in a response."""
    type: str  # text, code, link, image, list, table, quote
    content: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class FormattedResponse:
    """A fully formatted response ready for delivery."""
    text: str
    html: str = ""
    markdown: str = ""
    channel: ChannelType = ChannelType.WEBCHAT
    elements: List[ResponseElement] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    requires_action: bool = False
    action_label: str = ""
    errors: List[str] = field(default_factory=list)


class ResponseDeliveryEngine:
    """
    Core engine for formatting and delivering responses.
    Mirrors OpenClaw's response delivery mechanism.
    """
    
    def __init__(self):
        # Code language mappings
        self.code_languages = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'jsx': 'jsx',
            'tsx': 'tsx',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'sql': 'sql',
            'bash': 'bash',
            'sh': 'bash',
            'ps': 'powershell',
            'cmd': 'batch',
            'yaml': 'yaml',
            'yml': 'yaml',
            'md': 'markdown',
            'rst': 'rst',
            'txt': 'text',
            'xml': 'xml',
            'csv': 'csv',
        }
        
        # Formatting rules
        self.safety_patterns = {
            'email': r'\b[\w.-]+@[\w.-]+\.\w+\b',
            'phone': r'\b\+?[\d\s-]{10,}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            'api_key': r'\b[A-Za-z0-9]{20,}\b',
        }
        
        # Response templates
        self.response_templates = {
            'error': "I encountered an error: {error}\n\nPlease try again or rephrase your request.",
            'clarification': "I'd like to clarify: {question}\n\nCould you provide more details?",
            'success': "✓ {message}",
            'warning': "⚠️ {message}",
            'info': "ℹ️ {message}",
        }
    
    def process_response(self, raw_response: str, channel: ChannelType = ChannelType.WEBCHAT, 
                       intent_type: str = "chat", metadata: Dict = None) -> FormattedResponse:
        """
        Process raw LLM response for delivery.
        
        Args:
            raw_response: Raw response from LLM
            channel: Target delivery channel
            intent_type: Type of user intent
            metadata: Additional metadata
            
        Returns:
            FormattedResponse ready for delivery
        """
        # Stage 1: Basic cleaning
        cleaned = self._clean_response(raw_response)
        
        # Stage 2: Safety check
        safety_result = self._safety_check(cleaned)
        if safety_result['blocked']:
            return FormattedResponse(
                text="I cannot provide that response due to safety guidelines.",
                channel=channel,
                errors=safety_result['issues'],
            )
        
        # Stage 3: Extract elements
        elements = self._extract_elements(cleaned)
        
        # Stage 4: Format for channel
        formatted = self._format_for_channel(cleaned, elements, channel, intent_type)
        
        # Stage 5: Add metadata
        metadata = metadata or {}
        metadata['processed_at'] = datetime.now().isoformat()
        metadata['channel'] = channel.value
        metadata['intent_type'] = intent_type
        metadata['safety_passed'] = True
        metadata['word_count'] = len(cleaned.split())
        metadata['char_count'] = len(cleaned)
        
        return FormattedResponse(
            text=formatted['text'],
            html=formatted.get('html', ''),
            markdown=formatted.get('markdown', ''),
            channel=channel,
            elements=elements,
            metadata=metadata,
        )
    
    def _clean_response(self, response: str) -> str:
        """Clean raw response."""
        # Remove excessive whitespace
        lines = response.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            stripped = line.strip()
            if stripped:
                cleaned_lines.append(stripped)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append('')
                prev_empty = True
        
        # Join and remove trailing whitespace
        response = '\n'.join(cleaned_lines).strip()
        
        # Fix common issues
        # Remove assistant: prefix if present
        response = re.sub(r'^assistant:\s*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'^leo:\s*', '', response, flags=re.IGNORECASE)
        
        return response
    
    def _safety_check(self, response: str) -> Dict[str, Any]:
        """Check response for safety issues."""
        issues = []
        
        for issue_type, pattern in self.safety_patterns.items():
            matches = re.findall(pattern, response)
            if matches:
                issues.append(f"Potential {issue_type} detected: {len(matches)} instance(s)")
        
        # Check for harmful content patterns
        harmful_patterns = [
            (r'self[- ]?harm', 'Self-harm content'),
            (r'violence', 'Violence content'),
            (r'illegal', 'Illegal activity'),
        ]
        
        for pattern, description in harmful_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                issues.append(description)
        
        return {
            'blocked': len(issues) > 2,  # Block if multiple issues
            'issues': issues,
            'safe': len(issues) == 0,
        }
    
    def _extract_elements(self, response: str) -> List[ResponseElement]:
        """Extract structured elements from response."""
        elements = []
        
        # Extract code blocks
        code_blocks = re.findall(r'```(\w*)\n([\s\S]*?)```', response)
        for lang, code in code_blocks:
            elements.append(ResponseElement(
                type='code',
                content=code.strip(),
                metadata={'language': self.code_languages.get(lang, lang)}
            ))
        
        # Extract links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', response)
        for text, url in links:
            elements.append(ResponseElement(
                type='link',
                content=text,
                metadata={'url': url}
            ))
        
        # Extract lists
        list_items = re.findall(r'^\s*[-*•]\s+(.+)$', response, re.MULTILINE)
        if list_items:
            elements.append(ResponseElement(
                type='list',
                content='\n'.join(list_items),
            ))
        
        # Extract numbered lists
        num_items = re.findall(r'^\s*\d+\.\s+(.+)$', response, re.MULTILINE)
        if num_items:
            elements.append(ResponseElement(
                type='numbered_list',
                content='\n'.join(num_items),
            ))
        
        # Extract quotes
        quotes = re.findall(r'> (.+)$', response, re.MULTILINE)
        if quotes:
            elements.append(ResponseElement(
                type='quote',
                content='\n'.join(quotes),
            ))
        
        return elements
    
    def _format_for_channel(self, response: str, elements: List[ResponseElement], 
                           channel: ChannelType, intent_type: str) -> Dict[str, str]:
        """Format response for specific channel."""
        
        if channel == ChannelType.WEBCHAT:
            return self._format_for_webchat(response, elements)
        elif channel == ChannelType.TERMINAL:
            return self._format_for_terminal(response, elements)
        elif channel == ChannelType.MARKDOWN:
            return self._format_for_markdown(response, elements)
        elif channel == ChannelType.API:
            return self._format_for_api(response, elements)
        elif channel == ChannelType.HTML:
            return self._format_for_html(response, elements)
        else:
            return self._format_for_plain(response, elements)
    
    def _markdown_to_html(self, text: str) -> str:
        """Convert markdown to HTML."""
        if not text:
            return ""
        
        html = text
        
        # Code blocks (first, to avoid double-processing)
        html = re.sub(
            r'```(\w*)\n([\s\S]*?)```',
            r'<pre><code class="language-\1">\2</code></pre>',
            html
        )
        
        # Inline code
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
        
        # Bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        
        # Italic
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Headers
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Links
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', html)
        
        # Line breaks
        html = html.replace('\n', '<br>')
        
        return html
    
    def _format_for_webchat(self, response: str, elements: List[ResponseElement]) -> Dict[str, str]:
        """Format for web chat interface."""
        html_content = self._markdown_to_html(response)
        
        # Add interactive elements
        for elem in elements:
            if elem.type == 'code':
                html_content += f'''
                <div class="code-block" data-lang="{elem.metadata.get('language', 'text')}">
                    <pre><code>{html.escape(elem.content)}</code></pre>
                </div>
                '''
        
        return {
            'text': response,
            'html': html_content,
            'markdown': response,
        }
    
    def _format_for_terminal(self, response: str, elements: List[ResponseElement]) -> Dict[str, str]:
        """Format for terminal output."""
        # Strip formatting for terminal
        text = response
        
        # Convert markdown to terminal-friendly format
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)  # Italic
        text = re.sub(r'`(.+?)`', r'\1', text)  # Inline code
        text = re.sub(r'```(\w*)\n([\s\S]*?)```', r'\2', text)  # Code blocks
        
        return {
            'text': text,
            'html': '',
            'markdown': response,
        }
    
    def _format_for_markdown(self, response: str, elements: List[ResponseElement]) -> Dict[str, str]:
        """Format as markdown."""
        return {
            'text': response,
            'html': '',
            'markdown': response,
        }
    
    def _format_for_api(self, response: str, elements: List[ResponseElement]) -> Dict[str, str]:
        """Format for API response."""
        return {
            'text': response,
            'html': '',
            'markdown': '',
        }
    
    def _format_for_html(self, response: str, elements: List[ResponseElement]) -> Dict[str, str]:
        """Format as HTML."""
        html_content = self._markdown_to_html(response)
        return {
            'text': html_content,
            'html': html_content,
            'markdown': response,
        }
    
    def _format_for_plain(self, response: str, elements: List[ResponseElement]) -> Dict[str, str]:
        """Format as plain text."""
        # Strip all formatting
        text = response
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'`(.+?)`', r'\1', text)
        text = re.sub(r'```(\w*)\n([\s\S]*?)```', r'\2', text)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', text)
        
        return {
            'text': text,
            'html': '',
            'markdown': '',
        }
    

# Utility functions
def format_timestamp(dt: datetime = None) -> str:
    """Format current timestamp."""
    return (dt or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")


def generate_response_id() -> str:
    """Generate unique response ID."""
    return hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()[:12]


def calculate_reading_time(text: str) -> str:
    """Calculate approximate reading time."""
    words = len(text.split())
    minutes = words // 200  # 200 words per minute
    seconds = (words % 200) * 60 // 200
    
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"
