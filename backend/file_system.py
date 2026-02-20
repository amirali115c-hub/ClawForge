"""
Leo 2.0 - File System Agent
===========================
File operations and document management for Leo 2.0.
"""

import os
import json
import shutil
import uuid
import base64
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum


class FileCategory(Enum):
    DOCUMENT = "document"
    CODE = "code"
    IMAGE = "image"
    DATA = "data"
    ARCHIVE = "archive"
    OTHER = "other"


@dataclass
class FileInfo:
    """File information."""
    name: str
    path: str
    size: int
    category: str
    modified: str
    is_dir: bool


class FileSystemAgent:
    """
    File system operations agent.
    
    Features:
    - File listing
    - File reading/writing
    - Directory operations
    - File search
    - Document handling
    """
    
    def __init__(self, root_dir: str = None):
        if root_dir is None:
            # Default to workspace files directory
            base_dir = Path(__file__).parent.parent
            root_dir = base_dir / "files"
        
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_category(self, filename: str) -> str:
        """Determine file category."""
        ext = Path(filename).suffix.lower()
        
        docs = ['.txt', '.md', '.doc', '.docx', '.pdf', '.odt', '.rtf']
        code = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.go', '.rs', '.html', '.css', '.json', '.yaml', '.yml', '.xml']
        images = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']
        data = ['.csv', '.json', '.xml', '.sql', '.db']
        archives = ['.zip', '.tar', '.gz', '.rar', '.7z']
        
        if ext in docs:
            return FileCategory.DOCUMENT.value
        elif ext in code:
            return FileCategory.CODE.value
        elif ext in images:
            return FileCategory.IMAGE.value
        elif ext in data:
            return FileCategory.DATA.value
        elif ext in archives:
            return FileCategory.ARCHIVE.value
        else:
            return FileCategory.OTHER.value
    
    def list_files(self, path: str = "", show_hidden: bool = False) -> List[Dict]:
        """List files in directory."""
        try:
            target = self.root_dir / path if path else self.root_dir
            
            if not target.exists():
                return [{"error": "Path does not exist"}]
            
            if not target.is_dir():
                return [{"error": "Path is not a directory"}]
            
            files = []
            for item in target.iterdir():
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                stat = item.stat()
                files.append({
                    "name": item.name,
                    "path": str(item.relative_to(self.root_dir)),
                    "size": stat.st_size if item.is_file() else 0,
                    "category": self._get_category(item.name) if item.is_file() else "folder",
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "is_dir": item.is_dir()
                })
            
            # Sort: directories first, then by name
            files.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
            
            return files
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def read_file(self, path: str, encoding: str = "utf-8") -> Dict:
        """Read file content."""
        try:
            target = self.root_dir / path
            
            if not target.exists():
                return {"error": "File does not exist"}
            
            if not target.is_file():
                return {"error": "Path is not a file"}
            
            # Check file size (limit to 1MB)
            size = target.stat().st_size
            if size > 1024 * 1024:
                return {"error": "File too large (max 1MB)"}
            
            content = target.read_text(encoding=encoding)
            
            return {
                "status": "ok",
                "name": target.name,
                "path": str(target.relative_to(self.root_dir)),
                "size": size,
                "content": content,
                "encoding": encoding
            }
            
        except UnicodeDecodeError:
            # Try binary read and encode as base64
            try:
                content = target.read_bytes()
                b64 = base64.b64encode(content).decode()
                return {
                    "status": "ok",
                    "name": target.name,
                    "path": str(target.relative_to(self.root_dir)),
                    "size": len(content),
                    "content": b64,
                    "encoding": "base64"
                }
            except Exception as e:
                return {"error": f"Cannot read file: {e}"}
        except Exception as e:
            return {"error": str(e)}
    
    def write_file(self, path: str, content: str, encoding: str = "utf-8") -> Dict:
        """Write file content."""
        try:
            target = self.root_dir / path
            
            # Create parent directories if needed
            target.parent.mkdir(parents=True, exist_ok=True)
            
            target.write_text(content, encoding=encoding)
            
            return {
                "status": "ok",
                "path": str(target.relative_to(self.root_dir)),
                "size": len(content)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def delete_file(self, path: str) -> Dict:
        """Delete file or directory."""
        try:
            target = self.root_dir / path
            
            if not target.exists():
                return {"error": "Path does not exist"}
            
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            
            return {
                "status": "ok",
                "path": path,
                "deleted": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def create_directory(self, path: str) -> Dict:
        """Create directory."""
        try:
            target = self.root_dir / path
            target.mkdir(parents=True, exist_ok=True)
            
            return {
                "status": "ok",
                "path": str(target.relative_to(self.root_dir)),
                "created": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def search_files(self, query: str, path: str = "") -> List[Dict]:
        """Search for files."""
        try:
            target = self.root_dir / path if path else self.root_dir
            
            results = []
            query_lower = query.lower()
            
            for item in target.rglob("*"):
                if item.is_file() and query_lower in item.name.lower():
                    stat = item.stat()
                    results.append({
                        "name": item.name,
                        "path": str(item.relative_to(self.root_dir)),
                        "size": stat.st_size,
                        "category": self._get_category(item.name)
                    })
            
            return results[:50]  # Limit results
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_file_info(self, path: str) -> Dict:
        """Get file information."""
        try:
            target = self.root_dir / path
            
            if not target.exists():
                return {"error": "Path does not exist"}
            
            stat = target.stat()
            
            return {
                "status": "ok",
                "name": target.name,
                "path": str(target.relative_to(self.root_dir)),
                "size": stat.st_size,
                "category": self._get_category(target.name) if target.is_file() else "folder",
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "is_dir": target.is_dir()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def copy_file(self, source: str, destination: str) -> Dict:
        """Copy file or directory."""
        try:
            src = self.root_dir / source
            dst = self.root_dir / destination
            
            if not src.exists():
                return {"error": "Source does not exist"}
            
            # Create destination parent
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            
            return {
                "status": "ok",
                "source": source,
                "destination": destination,
                "copied": True
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def move_file(self, source: str, destination: str) -> Dict:
        """Move file or directory."""
        try:
            src = self.root_dir / source
            dst = self.root_dir / destination
            
            if not src.exists():
                return {"error": "Source does not exist"}
            
            # Create destination parent
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src), str(dst))
            
            return {
                "status": "ok",
                "source": source,
                "destination": destination,
                "moved": True
            }
            
        except Exception as e:
            return {"error": str(e)}


# Singleton
_file_system = None

def get_file_system() -> FileSystemAgent:
    global _file_system
    if _file_system is None:
        _file_system = FileSystemAgent()
    return _file_system
