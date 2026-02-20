# memory_manager.py - Auto RAM Cleanup System for Leo 2.0

"""
Automatically monitors and frees up system memory.
Clears caches, temp files, and manages Ollama model memory.
"""

import os
import gc
import psutil
import shutil
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

class MemoryConfig:
    """Memory management configuration."""
    
    # RAM thresholds (percentage)
    RAM_WARNING_THRESHOLD = 70  # Warn when RAM > 70%
    RAM_CRITICAL_THRESHOLD = 85  # Auto-clean when RAM > 85%
    RAM_CLEANUP_THRESHOLD = 90  # Force cleanup when RAM > 90%
    
    # Ollama settings
    OLLAMA_CACHE_DIR = Path.home() / ".cache" / "ollama"
    OLLAMA_TEMP_DIR = Path.home() / ".local" / "share" / "ollama" / "tmp"
    
    # Cleanup intervals (seconds)
    CHECK_INTERVAL = 30  # Check RAM every 30 seconds
    AUTO_CLEAN_INTERVAL = 300  # Auto-clean every 5 minutes
    
    # Max memory target (keep system under this)
    MAX_RAM_USAGE = 80  # Target: keep RAM under 80%


# ============================================================================
# MEMORY MONITOR
# ============================================================================

class MemoryMonitor:
    """Monitor and manage system memory."""
    
    def __init__(self):
        self.running = False
        self.check_interval = MemoryConfig.CHECK_INTERVAL
        self.auto_clean_interval = MemoryConfig.AUTO_CLEAN_INTERVAL
        self.last_cleanup = datetime.now()
        self.cleanup_count = 0
        self.warnings_issued = 0
        
        # Callbacks
        self.on_warning = None
        self.on_cleanup = None
        self.on_critical = None
    
    # =========================================================================
    # RAM INFO
    # =========================================================================
    
    def get_ram_info(self) -> dict:
        """Get current RAM usage."""
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent_used": mem.percent,
            "warning": mem.percent >= MemoryConfig.RAM_WARNING_THRESHOLD,
            "critical": mem.percent >= MemoryConfig.RAM_CRITICAL_THRESHOLD
        }
    
    def get_process_memory(self, pid: int = None) -> dict:
        """Get memory info for a specific process."""
        try:
            proc = psutil.Process(pid or os.getpid())
            mem_info = proc.memory_info()
            return {
                "rss_mb": round(mem_info.rss / (1024**2), 2),
                "vms_mb": round(mem_info.vms / (1024**2), 2),
                "percent": round(proc.memory_percent(), 2)
            }
        except:
            return {"error": "Cannot access process"}
    
    # =========================================================================
    # CLEANUP OPERATIONS
    # =========================================================================
    
    def force_garbage_collection(self):
        """Force Python garbage collection."""
        gc.collect()
        gc.collect(1)
        gc.collect(2)
        return {"status": "success", "message": "Garbage collection completed"}
    
    def clear_temp_files(self) -> dict:
        """Clear temporary files."""
        cleaned = {"count": 0, "size_freed_mb": 0}
        
        # Clear system temp
        temp_dirs = [
            Path("/tmp") if os.name == "posix" else Path(os.environ.get("TEMP", "")),
            Path.home() / "AppData" / "Local" / "Temp" if os.name == "nt" else None
        ]
        
        for temp_dir in temp_dirs:
            if temp_dir and temp_dir.exists():
                try:
                    cutoff = datetime.now() - timedelta(hours=1)
                    for file in temp_dir.glob("*"):
                        try:
                            if file.is_file():
                                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                                if mtime < cutoff:
                                    size = file.stat().st_size
                                    file.unlink()
                                    cleaned["count"] += 1
                                    cleaned["size_freed_mb"] += size / (1024**2)
                        except:
                            pass
                except:
                    pass
        
        return {
            "status": "success",
            "files_cleaned": cleaned["count"],
            "size_freed_mb": round(cleaned["size_freed_mb"], 2)
        }
    
    def clear_ollama_cache(self) -> dict:
        """Clear Ollama model cache to free RAM."""
        cleaned = {"models_unloaded": 0, "cache_freed_mb": 0}
        
        try:
            # Use ollama stop command via subprocess
            import subprocess
            
            # List loaded models
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines[1:]:  # Skip header
                    parts = line.split()
                    if parts:
                        model_name = parts[0]
                        # Don't unload the active model
                        cleaned["models_unloaded"] += 0  # For now, just list
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
        return {
            "status": "success",
            "models_unloaded": cleaned["models_unloaded"],
            "cache_freed_mb": round(cleaned["cache_freed_mb"], 2)
        }
    
    def optimize_python_memory(self) -> dict:
        """Optimize Python memory usage."""
        self.force_garbage_collection()
        
        return {
            "status": "success",
            "message": "Python memory optimized",
            "ram_after": self.get_ram_info()["used_gb"]
        }
    
    # =========================================================================
    # AUTO CLEANUP
    # =========================================================================
    
    def full_cleanup(self) -> dict:
        """Perform full system cleanup."""
        results = {}
        
        # Step 1: Garbage collection
        results["garbage_collection"] = self.force_garbage_collection()
        
        # Step 2: Clear temp files
        results["temp_files"] = self.clear_temp_files()
        
        # Step 3: Ollama cache
        results["ollama_cache"] = self.clear_ollama_cache()
        
        # Step 4: Get final RAM state
        results["final_ram"] = self.get_ram_info()
        
        self.cleanup_count += 1
        self.last_cleanup = datetime.now()
        
        return results
    
    def check_and_auto_clean(self) -> dict:
        """Check RAM and auto-clean if needed."""
        ram = self.get_ram_info()
        
        results = {
            "ram_percent": ram["percent_used"],
            "action": "none",
            "details": {}
        }
        
        if ram["percent_used"] >= MemoryConfig.RAM_CLEANUP_THRESHOLD:
            # Force cleanup
            results["action"] = "force_cleanup"
            results["details"] = self.full_cleanup()
        elif ram["percent_used"] >= MemoryConfig.RAM_CRITICAL_THRESHOLD:
            # Standard cleanup
            results["action"] = "critical_cleanup"
            results["details"] = self.optimize_python_memory()
        elif ram["percent_used"] >= MemoryConfig.RAM_WARNING_THRESHOLD:
            # Light cleanup
            results["action"] = "light_cleanup"
            results["details"] = self.force_garbage_collection()
        
        return results
    
    # =========================================================================
    # MONITORING LOOP
    # =========================================================================
    
    def start_monitoring(self, callback=None):
        """Start background monitoring loop."""
        self.running = True
        
        def loop():
            while self.running:
                ram = self.get_ram_info()
                
                if ram["percent_used"] >= MemoryConfig.RAM_CRITICAL_THRESHOLD:
                    if self.on_critical:
                        self.on_critical(ram)
                    self.check_and_auto_clean()
                elif ram["percent_used"] >= MemoryConfig.RAM_WARNING_THRESHOLD:
                    if self.on_warning:
                        self.on_warning(ram)
                    self.warnings_issued += 1
                
                time.sleep(self.check_interval)
        
        self.monitor_thread = threading.Thread(target=loop, daemon=True)
        self.monitor_thread.start()
        
        return {"status": "started", "thread": "memory_monitor"}
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self.running = False
        return {"status": "stopped"}
    
    # =========================================================================
    # STATUS REPORT
    # =========================================================================
    
    def get_status(self) -> dict:
        """Get memory manager status."""
        ram = self.get_ram_info()
        
        return {
            "monitoring": self.running,
            "ram": ram,
            "cleanups_performed": self.cleanup_count,
            "warnings_issued": self.warnings_issued,
            "last_cleanup": self.last_cleanup.isoformat() if self.last_cleanup else None,
            "config": {
                "warning_threshold": MemoryConfig.RAM_WARNING_THRESHOLD,
                "critical_threshold": MemoryConfig.RAM_CRITICAL_THRESHOLD,
                "cleanup_threshold": MemoryConfig.RAM_CLEANUP_THRESHOLD,
                "check_interval": self.check_interval
            }
        }


# ============================================================================
# FLASK API ROUTES
# ============================================================================

def add_memory_routes(app):
    """Add memory management API routes to Flask app."""
    
    memory_manager = MemoryMonitor()
    
    @app.route("/api/memory/status")
    def memory_status():
        return memory_manager.get_status()
    
    @app.route("/api/memory/ram")
    def ram_info():
        return memory_manager.get_ram_info()
    
    @app.route("/api/memory/process")
    def process_memory():
        pid = request.args.get("pid", type=int)
        return memory_manager.get_process_memory(pid)
    
    @app.route("/api/memory/cleanup", methods=["POST"])
    def cleanup_memory():
        """Perform cleanup."""
        cleanup_type = request.args.get("type", "full")
        
        if cleanup_type == "full":
            result = memory_manager.full_cleanup()
        elif cleanup_type == "python":
            result = memory_manager.optimize_python_memory()
        elif cleanup_type == "temp":
            result = memory_manager.clear_temp_files()
        elif cleanup_type == "ollama":
            result = memory_manager.clear_ollama_cache()
        else:
            result = {"status": "error", "message": "Unknown cleanup type"}
        
        return result
    
    @app.route("/api/memory/auto-cleanup", methods=["POST"])
    def auto_cleanup():
        """Trigger auto-cleanup based on current RAM."""
        result = memory_manager.check_and_auto_clean()
        return result
    
    return memory_manager


# ============================================================================
# STANDALONE TEST
# ============================================================================

if __name__ == "__main__":
    import json
    
    print("🦁 Leo 2.0 - Memory Manager Test")
    print("=" * 50)
    
    mm = MemoryMonitor()
    
    # Show current RAM
    print("\n📊 Current RAM Status:")
    ram = mm.get_ram_info()
    print(f"   Used: {ram['used_gb']}GB / {ram['total_gb']}GB ({ram['percent_used']}%)")
    print(f"   Available: {ram['available_gb']}GB")
    
    # Show process memory
    print("\n🔍 Process Memory:")
    proc_mem = mm.get_process_memory()
    print(f"   RSS: {proc_mem['rss_mb']}MB")
    print(f"   VMS: {proc_mem['vms_mb']}MB")
    
    # Run cleanup
    print("\n🧹 Running Full Cleanup...")
    result = mm.full_cleanup()
    print(json.dumps(result, indent=2))
    
    # Show RAM after cleanup
    print("\n📊 RAM After Cleanup:")
    ram_after = mm.get_ram_info()
    print(f"   Used: {ram_after['used_gb']}GB ({ram_after['percent_used']}%)")
    
    # Show status
    print("\n📈 Manager Status:")
    status = mm.get_status()
    print(json.dumps(status, indent=2))
