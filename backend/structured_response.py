"""
Leo 2.0 - Structured Response Formatter
======================================
Formats responses as tables, cards, lists, and other structured formats.
"""

import json
import re
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass


class ResponseFormat(Enum):
    PLAIN = "plain"
    MARKDOWN = "markdown"
    TABLE = "table"
    CARD = "card"
    LIST = "list"
    CODE = "code"
    JSON = "json"
    HTML = "html"


@dataclass
class StructuredResponse:
    """A structured response."""
    format: ResponseFormat
    content: Any
    metadata: Dict


class StructuredResponseFormatter:
    """Formats responses into various structured formats."""
    
    def __init__(self):
        self.format_count = 0
    
    def format(self, data: Any, format_type: str = "markdown") -> str:
        """Format data into specified structure."""
        self.format_count += 1
        
        format_type = format_type.lower()
        
        if format_type in ["table", "tabular"]:
            return self._format_table(data)
        elif format_type in ["card", "cards"]:
            return self._format_card(data)
        elif format_type in ["list", "bullet"]:
            return self._format_list(data)
        elif format_type in ["code", "pre"]:
            return self._format_code(data)
        elif format_type in ["json"]:
            return self._format_json(data)
        elif format_type in ["html"]:
            return self._format_html(data)
        else:
            return self._format_markdown(data)
    
    def _format_table(self, data: Any) -> str:
        """Format as a table."""
        # Handle list of dictionaries
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            headers = list(data[0].keys())
            
            # Build table
            lines = []
            
            # Header row
            lines.append("| " + " | ".join(headers) + " |")
            
            # Separator
            lines.append("|" + "|".join([" --- " for _ in headers]) + "|")
            
            # Data rows
            for row in data:
                values = [str(row.get(h, "")) for h in headers]
                lines.append("| " + " | ".join(values) + " |")
            
            return "\n".join(lines)
        
        # Handle dictionary
        elif isinstance(data, dict):
            lines = ["| Key | Value |", "| --- | --- |"]
            for key, value in data.items():
                lines.append(f"| {key} | {value} |")
            return "\n".join(lines)
        
        return str(data)
    
    def _format_card(self, data: Any) -> str:
        """Format as a card."""
        if isinstance(data, dict):
            lines = ["```card"]
            for key, value in data.items():
                lines.append(f"{key}: {value}")
            lines.append("```")
            return "\n".join(lines)
        
        elif isinstance(data, list):
            lines = []
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    lines.append(f"```card [{i+1}]")
                    for key, value in item.items():
                        lines.append(f"{key}: {value}")
                    lines.append("```")
                    lines.append("")
            return "\n".join(lines)
        
        return f"```card\n{data}\n```"
    
    def _format_list(self, data: Any) -> str:
        """Format as a list."""
        if isinstance(data, list):
            lines = []
            for item in data:
                if isinstance(item, dict):
                    # Format dict as mini-card
                    for key, value in item.items():
                        lines.append(f"  • {key}: {value}")
                else:
                    lines.append(f"  • {item}")
            return "\n".join(lines)
        
        elif isinstance(data, dict):
            lines = []
            for key, value in data.items():
                lines.append(f"• **{key}**: {value}")
            return "\n".join(lines)
        
        return f"• {data}"
    
    def _format_code(self, data: Any) -> str:
        """Format as code block."""
        if isinstance(data, str):
            return f"```\n{data}\n```"
        
        return f"```json\n{json.dumps(data, indent=2)}\n```"
    
    def _format_json(self, data: Any) -> str:
        """Format as JSON."""
        return json.dumps(data, indent=2)
    
    def _format_html(self, data: Any) -> str:
        """Format as HTML."""
        if isinstance(data, dict):
            lines = ['<div class="response">']
            for key, value in data.items():
                lines.append(f'  <div class="field">')
                lines.append(f'    <span class="key">{key}:</span>')
                lines.append(f'    <span class="value">{value}</span>')
                lines.append(f'  </div>')
            lines.append('</div>')
            return "\n".join(lines)
        
        elif isinstance(data, list):
            lines = ['<div class="response">']
            for item in data:
                lines.append(f'  <div class="item">{item}</div>')
            lines.append('</div>')
            return "\n".join(lines)
        
        return f"<div>{data}</div>"
    
    def _format_markdown(self, data: Any) -> str:
        """Format as markdown."""
        if isinstance(data, str):
            return data
        
        elif isinstance(data, dict):
            lines = []
            for key, value in data.items():
                lines.append(f"**{key}**: {value}")
            return "\n".join(lines)
        
        elif isinstance(data, list):
            lines = []
            for item in data:
                lines.append(f"- {item}")
            return "\n".join(lines)
        
        return str(data)
    
    # ========== AUTO-DETECTION ==========
    
    def detect_format(self, text: str) -> Optional[str]:
        """Auto-detect what format the user wants."""
        text_lower = text.lower()
        
        # Table indicators
        if any(word in text_lower for word in ["table", "tabular", "spreadsheet", "rows and columns"]):
            return "table"
        
        # Card indicators
        if any(word in text_lower for word in ["card", "display", "show as", "format as card"]):
            return "card"
        
        # List indicators
        if any(word in text_lower for word in ["list", "bullet", "enumerate"]):
            return "list"
        
        # Code indicators
        if any(word in text_lower for word in ["code", "json", "export"]):
            return "code"
        
        # HTML indicators
        if any(word in text_lower for word in ["html", "web", "display"]):
            return "html"
        
        return None
    
    def get_stats(self) -> Dict:
        """Get formatter statistics."""
        return {
            "formats_applied": self.format_count
        }


# Singleton
_formatter = None

def get_formatter() -> StructuredResponseFormatter:
    global _formatter
    if _formatter is None:
        _formatter = StructuredResponseFormatter()
    return _formatter


# Convenience functions
def format_response(data: Any, format_type: str = "markdown") -> str:
    """Format a response."""
    return get_formatter().format(data, format_type)


def detect_format(text: str) -> Optional[str]:
    """Auto-detect desired format."""
    return get_formatter().detect_format(text)
