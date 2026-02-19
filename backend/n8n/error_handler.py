#!/usr/bin/env python3
"""
N8N Error Handling System
Catches, logs, and routes errors from N8N workflows
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Setup logging
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "n8n-errors.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("n8n-error-handler")


class ErrorHandler:
    """Centralized error handling for N8N workflows"""
    
    def __init__(self, notify_slack: bool = False, slack_webhook: Optional[str] = None):
        self.notify_slack = notify_slack
        self.slack_webhook = slack_webhook
        self.error_counts: Dict[str, int] = {}
        
    def log_error(
        self,
        error: Exception,
        workflow_name: str,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "ERROR"
    ) -> str:
        """Log an error and return error ID"""
        error_id = f"{workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        error_info = {
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "workflow": workflow_name,
            "severity": severity,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        # Update error counts
        self.error_counts[workflow_name] = self.error_counts.get(workflow_name, 0) + 1
        
        # Log to file
        logger.error(json.dumps(error_info, indent=2))
        
        # Send Slack notification if enabled
        if self.notify_slack and self.slack_webhook:
            self._send_slack_alert(error_info)
            
        return error_id
    
    def _send_slack_alert(self, error_info: Dict[str, Any]) -> None:
        """Send error alert to Slack"""
        try:
            import requests
            
            severity_emoji = {
                "CRITICAL": "🔴",
                "ERROR": "🟠", 
                "WARNING": "🟡",
                "INFO": "🟢"
            }.get(error_info["severity"], "⚪")
            
            message = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "text": f"{severity_emoji} N8N Workflow Error",
                            "type": "plain_text"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Workflow:*\n{error_info['workflow']}"},
                            {"type": "mrkdwn", "text": f"*Error ID:*\n{error_info['error_id']}"},
                            {"type": "mrkdwn", "text": f"*Type:*\n{error_info['error_type']}"},
                            {"type": "mrkdwn", "text": f"*Time:*\n{error_info['timestamp']}"}
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "text": f"*Message:*\n{error_info['error_message']}",
                            "type": "mrkdwn"
                        }
                    }
                ]
            }
            
            requests.post(self.slack_webhook, json=message, timeout=10)
            logger.info(f"Slack alert sent for error: {error_info['error_id']}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "total_errors": sum(self.error_counts.values()),
            "by_workflow": self.error_counts,
            "timestamp": datetime.now().isoformat()
        }
    
    def retry_workflow(self, workflow_id: str) -> bool:
        """Trigger retry for a failed workflow"""
        # This would integrate with N8N API
        logger.info(f"Retry triggered for workflow: {workflow_id}")
        return True


# Workflow error templates
ERROR_TEMPLATES = {
    "api_rate_limit": {
        "message": "API rate limit exceeded",
        "action": "wait_and_retry",
        "wait_seconds": 60
    },
    "api_auth_failed": {
        "message": "API authentication failed",
        "action": "notify_admin",
        "severity": "CRITICAL"
    },
    "webhook_timeout": {
        "message": "Webhook response timeout",
        "action": "retry",
        "max_retries": 3
    },
    "invalid_input": {
        "message": "Invalid input data",
        "action": "skip_and_log"
    }
}


def create_error_response(error_type: str, workflow_name: str) -> Dict[str, Any]:
    """Create standardized error response"""
    template = ERROR_TEMPLATES.get(error_type, {
        "message": "Unknown error",
        "action": "log_and_continue"
    })
    
    return {
        "status": "error",
        "error_type": error_type,
        "workflow": workflow_name,
        "action": template.get("action", "log_and_continue"),
        "message": template.get("message", "An error occurred"),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Test error handler
    handler = ErrorHandler()
    
    try:
        raise ConnectionError("Test connection error")
    except Exception as e:
        error_id = handler.log_error(
            e,
            "test_workflow",
            {"test": True},
            "ERROR"
        )
        print(f"Test error logged with ID: {error_id}")
        print(f"Stats: {handler.get_error_stats()}")
