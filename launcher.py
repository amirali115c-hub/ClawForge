#!/usr/bin/env python3
"""
ClawForge v4.0 - Permanent Service Launcher

Run this script to start ClawForge and keep it running.
Supports auto-restart on crash.

Usage:
    python launcher.py           # Start both services
    python launcher.py --status  # Check status
    python launcher.py --stop    # Stop all services
    python launcher.py --restart # Restart services
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
BACKEND_PORT = 8000
FRONTEND_PORT = 7860

class ClawForgeLauncher:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = False
        
    def log(self, message):
        print(f"[{time.strftime('%H:%M:%S')}] {message}")
        
    def start_backend(self):
        """Start the backend server."""
        self.log("Starting Backend Server (port 8000)...")
        try:
            self.backend_process = subprocess.Popen(
                [sys.executable, "backend/main.py", "--server"],
                cwd=str(SCRIPT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.log(f"Backend started with PID: {self.backend_process.pid}")
            return True
        except Exception as e:
            self.log(f"Failed to start backend: {e}")
            return False
    
    def start_frontend(self):
        """Start the frontend dashboard."""
        self.log("Starting Frontend Dashboard (port 7860)...")
        try:
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=str(SCRIPT_DIR / "frontend"),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.log(f"Frontend started with PID: {self.frontend_process.pid}")
            return True
        except Exception as e:
            self.log(f"Failed to start frontend: {e}")
            return False
    
    def start(self):
        """Start all services."""
        self.log("=" * 47)
        self.log("  ClawForge v4.0 - Starting Services")
        self.log("=" * 47)
        self.log("")
        
        if not self.start_backend():
            return False
        time.sleep(5)  # Wait for backend
        
        if not self.start_frontend():
            return False
            
        self.running = True
        self.log("")
        self.log("=" * 47)
        self.log("  ClawForge is Running!")
        self.log("=" * 47)
        self.log("")
        self.log("  Backend:  http://127.0.0.1:8000")
        self.log("  Frontend: http://127.0.0.1:7860")
        self.log("  API Docs: http://127.0.0.1:8000/docs")
        self.log("")
        self.log("Press Ctrl+C to stop...")
        self.log("")
        
        return True
    
    def monitor(self):
        """Monitor and auto-restart crashed services."""
        while self.running:
            time.sleep(10)
            
            # Check backend
            if self.backend_process and self.backend_process.poll() is not None:
                self.log("Backend crashed! Restarting...")
                self.start_backend()
                
            # Check frontend
            if self.frontend_process and self.frontend_process.poll() is not None:
                self.log("Frontend crashed! Restarting...")
                self.start_frontend()
    
    def stop(self):
        """Stop all services."""
        self.log("Stopping ClawForge services...")
        
        if self.backend_process:
            self.backend_process.terminate()
            self.log("Backend stopped.")
            
        if self.frontend_process:
            self.frontend_process.terminate()
            self.log("Frontend stopped.")
            
        self.running = False
        self.log("All services stopped.")
    
    def check_status(self):
        """Check if services are running."""
        import socket
        
        # Check backend
        backend_ok = False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', BACKEND_PORT))
            backend_ok = (result == 0)
            sock.close()
        except:
            pass
        
        # Check frontend
        frontend_ok = False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', FRONTEND_PORT))
            frontend_ok = (result == 0)
            sock.close()
        except:
            pass
        
        print("")
        print("=" * 47)
        print("  ClawForge Status")
        print("=" * 47)
        print(f"  Backend (port {BACKEND_PORT}):    {'Running' if backend_ok else 'Stopped'}")
        print(f"  Frontend (port {FRONTEND_PORT}):  {'Running' if frontend_ok else 'Stopped'}")
        print("=" * 47)
        print("")
        
        return backend_ok and frontend_ok

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="ClawForge Launcher")
    parser.add_argument("--status", action="store_true", help="Check service status")
    parser.add_argument("--stop", action="store_true", help="Stop all services")
    parser.add_argument("--restart", action="store_true", help="Restart services")
    
    args = parser.parse_args()
    
    launcher = ClawForgeLauncher()
    
    if args.status:
        launcher.check_status()
        sys.exit(0)
        
    if args.stop:
        launcher.stop()
        sys.exit(0)
        
    if args.restart:
        launcher.stop()
        time.sleep(2)
        
    if launcher.start():
        try:
            launcher.monitor()
        except KeyboardInterrupt:
            launcher.stop()
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
