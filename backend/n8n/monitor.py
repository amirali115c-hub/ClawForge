#!/usr/bin/env python3
"""
N8N Monitoring & Health Check System
Monitors workflow execution, system health, and sends alerts
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import requests

# Setup logging
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "n8n-monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("n8n-monitor")


class N8NMonitor:
    """Monitor N8N instance health and workflow execution"""
    
    def __init__(self, n8n_url: str = "http://localhost:5678", api_key: Optional[str] = None):
        self.n8n_url = n8n_url.rstrip('/')
        self.api_key = api_key
        self.headers = {"X-N8N-API-KEY": api_key} if api_key else {}
        self.workflow_cache: Dict[str, Dict] = {}
        
    def health_check(self) -> Dict[str, Any]:
        """Check N8N instance health"""
        try:
            response = requests.get(
                f"{self.n8n_url}/healthz",
                timeout=10
            )
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_code": response.status_code,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows"""
        try:
            response = requests.get(
                f"{self.n8n_url}/api/v1/workflows",
                headers=self.headers,
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("data", [])
            return []
        except Exception as e:
            logger.error(f"Failed to fetch workflows: {e}")
            return []
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get specific workflow status"""
        workflows = self.get_workflows()
        for wf in workflows:
            if wf.get("id") == workflow_id:
                return wf
        return {}
    
    def get_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent executions"""
        try:
            response = requests.get(
                f"{self.n8n_url}/api/v1/executions",
                params={"limit": limit},
                headers=self.headers,
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("data", [])
            return []
        except Exception as e:
            logger.error(f"Failed to fetch executions: {e}")
            return []
    
    def get_failed_executions(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get failed executions in the last N hours"""
        executions = self.get_executions(limit=100)
        failed = []
        cutoff = datetime.now() - timedelta(hours=hours)
        
        for exec_data in executions:
            started = exec_data.get("startedAt", "")
            if started:
                exec_time = datetime.fromisoformat(started.replace("Z", "+00:00"))
                if exec_time > cutoff and exec_data.get("status") == "failed":
                    failed.append(exec_data)
                    
        return failed
    
    def trigger_workflow(self, workflow_id: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Trigger a workflow manually"""
        try:
            response = requests.post(
                f"{self.n8n_url}/api/v1/workflows/{workflow_id}/activate",
                headers=self.headers,
                json=data or {},
                timeout=30
            )
            return {
                "success": response.status_code in [200, 201],
                "status_code": response.status_code,
                "response": response.json() if response.status_code in [200, 201] else response.text
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        workflows = self.get_workflows()
        executions = self.get_executions(limit=100)
        failed = [e for e in executions if e.get("status") == "failed"]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "workflows": {
                "total": len(workflows),
                "active": len([w for w in workflows if w.get("active", False)]),
                "inactive": len([w for w in workflows if not w.get("active", False)])
            },
            "executions": {
                "total": len(executions),
                "failed": len(failed),
                "success_rate": round((len(executions) - len(failed)) / max(len(executions), 1) * 100, 2)
            },
            "health": self.health_check()
        }
    
    def monitor_loop(self, interval: int = 60) -> None:
        """Continuous monitoring loop"""
        logger.info(f"Starting N8N monitoring (interval: {interval}s)")
        
        while True:
            try:
                stats = self.get_system_stats()
                logger.info(f"Stats: {json.dumps(stats, indent=2)}")
                
                # Check for failed executions
                failed = self.get_failed_executions(hours=1)
                if failed:
                    logger.warning(f"Found {len(failed)} failed executions in last hour")
                    for f in failed[:5]:  # Log first 5
                        logger.warning(f"  - {f.get('id')}: {f.get('errorMessage', 'Unknown error')}")
                
                # Health check
                health = stats["health"]
                if health["status"] != "healthy":
                    logger.error(f"N8N unhealthy: {health}")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(interval)


class MetricsCollector:
    """Collect and store metrics for historical analysis"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        self.metrics_file = data_dir / "n8n_metrics.json"
        self.metrics: List[Dict] = self._load_metrics()
        
    def _load_metrics(self) -> List[Dict]:
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_metrics(self):
        """Save metrics to file"""
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def add_metric(self, metric_type: str, value: Any, tags: Optional[Dict] = None):
        """Add a new metric"""
        self.metrics.append({
            "timestamp": datetime.now().isoformat(),
            "type": metric_type,
            "value": value,
            "tags": tags or {}
        })
        
        # Keep only last 1000 entries
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]
        
        self.save_metrics()
    
    def get_metric_summary(self, metric_type: str, hours: int = 24) -> Dict[str, Any]:
        """Get summary for a specific metric"""
        cutoff = datetime.now() - timedelta(hours=hours)
        relevant = [
            m for m in self.metrics
            if m.get("type") == metric_type
            and datetime.fromisoformat(m["timestamp"]) > cutoff
        ]
        
        if not relevant:
            return {"count": 0, "avg": 0, "min": 0, "max": 0}
        
        values = [m["value"] for m in relevant]
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values)
        }


def main():
    """Main entry point for monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description="N8N Monitor")
    parser.add_argument("--url", default="http://localhost:5678", help="N8N URL")
    parser.add_argument("--api-key", help="N8N API key")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    args = parser.parse_args()
    
    monitor = N8NMonitor(args.url, args.api_key)
    
    if args.continuous:
        monitor.monitor_loop(interval=60)
    else:
        # Single check
        stats = monitor.get_system_stats()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
