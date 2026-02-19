# file_manager.py - Workspace File Manager for ClawForge

"""
Handles all file operations with strict workspace boundary enforcement.
No file reads or writes allowed outside ./workspace/
"""

import os
import json
import shutil
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class WorkspaceViolationError(Exception):
    """Raised when a file operation attempts to escape the workspace."""
    pass

class FileOperationError(Exception):
    """Raised when a file operation fails."""
    pass

# ============================================================================
# WORKSPACE BOUNDARY
# ============================================================================

WORKSPACE_ROOT = "./workspace"

def get_workspace_root() -> str:
    """Returns the workspace root directory."""
    return WORKSPACE_ROOT

# ============================================================================
# FILE MANAGER CLASS
# ============================================================================

class FileManager:
    """
    Handles all file operations with strict workspace boundary enforcement.
    """
    
    # Track created folders to avoid redundant creation
    _created_folders = set()
    
    # ============================================================================
    # PATH SAFETY
    # ============================================================================
    
    @classmethod
    def _safe_path(cls, path: str) -> Path:
        """
        Resolves and validates that a given path is inside the workspace.
        Raises WorkspaceViolationError if outside.
        
        Args:
            path: The file path to validate
        
        Returns:
            Resolved Path object
        
        Raises:
            WorkspaceViolationError: If path is outside workspace
        """
        # Normalize the path
        resolved_path = Path(path).resolve()
        workspace_path = Path(WORKSPACE_ROOT).resolve()
        
        # Check if path is inside workspace
        try:
            resolved_path.relative_to(workspace_path)
        except ValueError:
            raise WorkspaceViolationError(
                f"❌ SECURITY VIOLATION: Attempted to access path outside workspace:\n"
                f"   Requested: {path}\n"
                f"   Workspace: {workspace_path}\n"
                f"   All file operations must stay within {WORKSPACE_ROOT}/"
            )
        
        return resolved_path
    
    # ============================================================================
    # FILE TOOLS
    # ============================================================================
    
    @classmethod
    def read_file(cls, path: str) -> Dict[str, Any]:
        """
        Reads a file. Must be inside workspace.
        
        Args:
            path: Path to file (relative or absolute)
        
        Returns:
            Dict with status, content, and path
        """
        try:
            safe_path = cls._safe_path(path)
            
            if not safe_path.exists():
                return {
                    "status": "error",
                    "error": "File not found",
                    "path": str(safe_path)
                }
            
            if safe_path.is_dir():
                return {
                    "status": "error",
                    "error": "Path is a directory, not a file",
                    "path": str(safe_path)
                }
            
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "status": "success",
                "path": str(safe_path),
                "content": content,
                "size": len(content),
                "read_at": datetime.utcnow().isoformat()
            }
            
        except WorkspaceViolationError as e:
            return {"status": "blocked", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @classmethod
    def write_file(cls, path: str, content: str) -> Dict[str, Any]:
        """
        Writes content to a file. Must be inside workspace.
        
        Args:
            path: Path to file (relative or absolute)
            content: Content to write
        
        Returns:
            Dict with status and path
        """
        try:
            safe_path = cls._safe_path(path)
            
            # Create parent directories if they don't exist
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "status": "success",
                "path": str(safe_path),
                "size": len(content),
                "written_at": datetime.utcnow().isoformat()
            }
            
        except WorkspaceViolationError as e:
            return {"status": "blocked", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @classmethod
    def create_folder(cls, path: str) -> Dict[str, Any]:
        """
        Creates a folder. Must be inside workspace.
        
        Args:
            path: Path to folder (relative or absolute)
        
        Returns:
            Dict with status and path
        """
        try:
            safe_path = cls._safe_path(path)
            
            # Check if it already exists
            if safe_path.exists():
                return {
                    "status": "exists",
                    "path": str(safe_path),
                    "message": "Folder already exists"
                }
            
            safe_path.mkdir(parents=True, exist_ok=True)
            
            return {
                "status": "success",
                "path": str(safe_path),
                "created_at": datetime.utcnow().isoformat()
            }
            
        except WorkspaceViolationError as e:
            return {"status": "blocked", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @classmethod
    def move_file(cls, source: str, destination: str) -> Dict[str, Any]:
        """
        Moves a file within the workspace.
        
        Args:
            source: Source path
            destination: Destination path
        
        Returns:
            Dict with status and paths
        """
        try:
            safe_source = cls._safe_path(source)
            safe_destination = cls._safe_path(destination)
            
            if not safe_source.exists():
                return {"status": "error", "error": "Source file not found", "source": str(safe_source)}
            
            # Create parent directories for destination
            safe_destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(safe_source), str(safe_destination))
            
            return {
                "status": "success",
                "source": str(safe_source),
                "destination": str(safe_destination),
                "moved_at": datetime.utcnow().isoformat()
            }
            
        except WorkspaceViolationError as e:
            return {"status": "blocked", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @classmethod
    def delete_file(cls, path: str) -> Dict[str, Any]:
        """
        Deletes a file. ONLY allowed inside workspace.
        
        Args:
            path: Path to file (relative or absolute)
        
        Returns:
            Dict with status and path
        """
        try:
            safe_path = cls._safe_path(path)
            
            if not safe_path.exists():
                return {"status": "error", "error": "File not found", "path": str(safe_path)}
            
            if safe_path.is_dir():
                return {"status": "error", "error": "Path is a directory, use delete_folder instead", "path": str(safe_path)}
            
            # Double-check we're in quarantine or tasks folder for safety
            if "quarantine" not in str(safe_path) and "tasks" not in str(safe_path):
                return {
                    "status": "blocked",
                    "error": "File deletion restricted to quarantine and tasks folders only",
                    "path": str(safe_path)
                }
            
            safe_path.unlink()
            
            return {
                "status": "success",
                "path": str(safe_path),
                "deleted_at": datetime.utcnow().isoformat()
            }
            
        except WorkspaceViolationError as e:
            return {"status": "blocked", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @classmethod
    def list_folder(cls, path: str) -> Dict[str, Any]:
        """
        Lists contents of a folder inside workspace.
        
        Args:
            path: Path to folder (relative or absolute)
        
        Returns:
            Dict with status, files, and folders lists
        """
        try:
            safe_path = cls._safe_path(path)
            
            if not safe_path.exists():
                return {"status": "error", "error": "Folder not found", "path": str(safe_path)}
            
            if not safe_path.is_dir():
                return {"status": "error", "error": "Path is not a directory", "path": str(safe_path)}
            
            files = []
            folders = []
            
            for item in safe_path.iterdir():
                item_info = {
                    "name": item.name,
                    "path": str(item),
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                }
                
                if item.is_dir():
                    folders.append(item_info)
                else:
                    files.append(item_info)
            
            return {
                "status": "success",
                "path": str(safe_path),
                "files": files,
                "folders": folders,
                "file_count": len(files),
                "folder_count": len(folders)
            }
            
        except WorkspaceViolationError as e:
            return {"status": "blocked", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    # ============================================================================
    # TASK FOLDER MANAGEMENT
    # ============================================================================
    
    @classmethod
    def create_task_folder(cls, task_id: str) -> Dict[str, Any]:
        """
        Creates the standard folder structure for a task.
        
        Structure:
        ./workspace/tasks/{task_id}/
            ├── plan.md
            ├── notes.md
            ├── logs.jsonl
            ├── security_report.json
            └── output/
        
        Args:
            task_id: The task identifier
        
        Returns:
            Dict with status and created paths
        """
        task_root = f"{WORKSPACE_ROOT}/tasks/{task_id}"
        output_folder = f"{task_root}/output"
        
        # Create main task folder
        result = cls.create_folder(task_root)
        if result["status"] not in ["success", "exists"]:
            return result
        
        # Create output subfolder
        output_result = cls.create_folder(output_folder)
        
        # Initialize plan.md
        plan_path = f"{task_root}/plan.md"
        plan_result = cls.write_file(plan_path, f"# Task Plan: {task_id}\n\n## Goal\n\n## Subtasks\n\n## Permissions Required\n")
        
        # Initialize notes.md
        notes_path = f"{task_root}/notes.md"
        notes_result = cls.write_file(notes_path, f"# Task Notes: {task_id}\n\n## Reasoning\n\n## Execution Trace\n\n")
        
        # Initialize logs.jsonl
        logs_path = f"{task_root}/logs.jsonl"
        cls.write_file(logs_path, "")
        
        # Initialize security_report.json
        security_path = f"{task_root}/security_report.json"
        security_content = {
            "task_id": task_id,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "tools_used": [],
            "blocked_commands": [],
            "quarantined_files": [],
            "risk_score_final": 0,
            "status": "in_progress"
        }
        cls.write_file(security_path, json.dumps(security_content, indent=2))
        
        return {
            "status": "success",
            "task_id": task_id,
            "task_root": task_root,
            "output_folder": output_folder,
            "created_at": datetime.utcnow().isoformat(),
            "files_created": [
                plan_path,
                notes_path,
                logs_path,
                security_path,
                output_folder
            ]
        }
    
    # ============================================================================
    # QUARANTINE SYSTEM
    # ============================================================================
    
    @classmethod
    def quarantine_file(cls, path: str, reason: str = "Suspicious file") -> Dict[str, Any]:
        """
        Moves a suspicious file to the quarantine folder.
        Creates manifest file with timestamp.
        
        Args:
            path: Path to suspicious file
            reason: Reason for quarantine
        
        Returns:
            Dict with status and quarantine details
        """
        try:
            safe_path = cls._safe_path(path)
            quarantine_dir = cls._safe_path(f"{WORKSPACE_ROOT}/quarantine")
            
            if not safe_path.exists():
                return {"status": "error", "error": "File not found", "path": str(safe_path)}
            
            # Create quarantine folder if needed
            quarantine_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamped filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = safe_path.name
            quarantine_filename = f"{timestamp}_{filename}"
            quarantine_path = quarantine_dir / quarantine_filename
            
            # Move file to quarantine
            shutil.move(str(safe_path), str(quarantine_path))
            
            # Create manifest file
            manifest = {
                "original_path": str(safe_path),
                "quarantine_path": str(quarantine_path),
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
                "filename": filename,
                "size": quarantine_path.stat().st_size if quarantine_path.exists() else 0
            }
            
            manifest_path = quarantine_path.with_suffix(f"{quarantine_path.suffix}.manifest.json")
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            return {
                "status": "quarantined",
                "original_path": str(safe_path),
                "quarantine_path": str(quarantine_path),
                "manifest_path": str(manifest_path),
                "reason": reason,
                "quarantined_at": datetime.utcnow().isoformat()
            }
            
        except WorkspaceViolationError as e:
            return {"status": "blocked", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    # ============================================================================
    # FILE UTILITIES
    # ============================================================================
    
    @classmethod
    def get_file_hash(cls, path: str) -> Dict[str, Any]:
        """
        Returns SHA-256 hash of a file for integrity check.
        
        Args:
            path: Path to file
        
        Returns:
            Dict with status and hash
        """
        try:
            safe_path = cls._safe_path(path)
            
            if not safe_path.exists():
                return {"status": "error", "error": "File not found", "path": str(safe_path)}
            
            sha256_hash = hashlib.sha256()
            
            with open(safe_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            return {
                "status": "success",
                "path": str(safe_path),
                "hash": sha256_hash.hexdigest(),
                "algorithm": "SHA-256"
            }
            
        except WorkspaceViolationError as e:
            return {"status": "blocked", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @classmethod
    def save_deliverable(cls, task_id: str, filename: str, content: str) -> Dict[str, Any]:
        """
        Saves a task deliverable to ./workspace/tasks/{task_id}/output/
        
        Args:
            task_id: The task identifier
            filename: Name of the deliverable file
            content: Content to write
        
        Returns:
            Dict with status and path
        """
        output_path = f"{WORKSPACE_ROOT}/tasks/{task_id}/output/{filename}"
        return cls.write_file(output_path, content)
    
    @classmethod
    def append_to_log(cls, task_id: str, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Appends an entry to the task's logs.jsonl file.
        
        Args:
            task_id: The task identifier
            entry: Log entry dictionary
        
        Returns:
            Dict with status
        """
        log_path = f"{WORKSPACE_ROOT}/tasks/{task_id}/logs.jsonl"
        
        try:
            safe_path = cls._safe_path(log_path)
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(safe_path, 'a', encoding='utf-8') as f:
                entry["timestamp"] = datetime.utcnow().isoformat()
                f.write(json.dumps(entry) + "\n")
            
            return {"status": "success", "log_path": str(safe_path)}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @classmethod
    def update_security_report(cls, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates the security report for a task.
        
        Args:
            task_id: The task identifier
            updates: Dictionary of updates to apply
        
        Returns:
            Dict with status
        """
        report_path = f"{WORKSPACE_ROOT}/tasks/{task_id}/security_report.json"
        
        try:
            safe_path = cls._safe_path(report_path)
            
            # Read existing report
            if safe_path.exists():
                with open(safe_path, 'r') as f:
                    report = json.load(f)
            else:
                report = {
                    "task_id": task_id,
                    "start_time": datetime.utcnow().isoformat(),
                    "end_time": None,
                    "tools_used": [],
                    "blocked_commands": [],
                    "quarantined_files": [],
                    "risk_score_final": 0,
                    "status": "in_progress"
                }
            
            # Apply updates
            for key, value in updates.items():
                if key == "tools_used":
                    if isinstance(value, list):
                        report[key].extend(value)
                    else:
                        report[key].append(value)
                elif key == "blocked_commands":
                    if isinstance(value, list):
                        report[key].extend(value)
                    else:
                        report[key].append(value)
                elif key == "quarantined_files":
                    if isinstance(value, list):
                        report[key].extend(value)
                    else:
                        report[key].append(value)
                else:
                    report[key] = value
            
            # Write updated report
            with open(safe_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            return {"status": "success", "report_path": str(safe_path)}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def read_file(path: str) -> Dict[str, Any]:
    """Convenience function for FileManager.read_file()"""
    return FileManager.read_file(path)

def write_file(path: str, content: str) -> Dict[str, Any]:
    """Convenience function for FileManager.write_file()"""
    return FileManager.write_file(path, content)

def create_folder(path: str) -> Dict[str, Any]:
    """Convenience function for FileManager.create_folder()"""
    return FileManager.create_folder(path)

def delete_file(path: str) -> Dict[str, Any]:
    """Convenience function for FileManager.delete_file()"""
    return FileManager.delete_file(path)

def list_folder(path: str) -> Dict[str, Any]:
    """Convenience function for FileManager.list_folder()"""
    return FileManager.list_folder(path)

if __name__ == "__main__":
    # Test file manager
    print("🐾 ClawForge File Manager - Test")
    print("=" * 50)
    
    # Test workspace boundary
    try:
        result = FileManager.read_file("/etc/passwd")
        print(f"❌ Security test failed: {result}")
    except WorkspaceViolationError as e:
        print(f"✅ Security test passed: Blocked external file access")
    
    # Test creating folder
    result = FileManager.create_folder("./workspace/test_folder")
    print(f"Create folder: {result['status']}")
    
    # Test writing file
    result = FileManager.write_file("./workspace/test_folder/sample.txt", "Hello, ClawForge!")
    print(f"Write file: {result['status']}")
    
    # Test listing folder
    result = FileManager.list_folder("./workspace")
    print(f"List workspace: {result['status']}, items: {result.get('folder_count', 0)} folders")
