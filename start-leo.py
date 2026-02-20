#!/usr/bin/env python3
"""
Leo 2.0 - Single Command Server Manager
Starts and monitors both frontend and backend with auto-restart.
"""

import subprocess
import time
import os
import sys
import socket
import signal
from datetime import datetime

# Configuration
BACKEND_PORT = 9000
FRONTEND_PORT = 3000
BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}"
FRONTEND_URL = f"http://127.0.0.1:{FRONTEND_PORT}"
CHECK_INTERVAL = 15  # seconds

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "ClawForge", "backend")
FRONTEND_DIR = os.path.join(BASE_DIR, "ClawForge", "frontend")

# Process tracking
backend_process = None
frontend_process = None


def log(msg: str):
    """Log with timestamp."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def kill_port(port: int):
    """Kill any process using a port."""
    try:
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True, capture_output=True, text=True
        )
        for line in result.stdout.split("\n"):
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = int(parts[-1])
                    if pid > 0:
                        log(f"Killing PID {pid} on port {port}")
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                        time.sleep(2)
    except Exception:
        pass


def is_port_open(port: int) -> bool:
    """Check if port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except:
        return False


def is_alive(process: subprocess.Popen) -> bool:
    """Check if process is still running."""
    return process is not None and process.poll() is None


def start_backend() -> subprocess.Popen:
    """Start backend server."""
    log("Starting backend...")
    try:
        # Kill any existing on port
        kill_port(BACKEND_PORT)
        time.sleep(1)
        
        process = subprocess.Popen(
            [sys.executable, "main.py", "--server"],
            cwd=BACKEND_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        log(f"Backend started (PID: {process.pid})")
        return process
    except Exception as e:
        log(f"Backend failed: {e}")
        return None


def start_frontend() -> subprocess.Popen:
    """Start frontend dev server."""
    log("Starting frontend...")
    try:
        # Kill any existing on port
        kill_port(FRONTEND_PORT)
        time.sleep(1)
        
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=FRONTEND_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        log(f"Frontend started (PID: {process.pid})")
        return process
    except Exception as e:
        log(f"Frontend failed: {e}")
        return None


def stop_all():
    """Stop all servers."""
    global backend_process, frontend_process
    
    for name, proc in [("Backend", backend_process), ("Frontend", frontend_process)]:
        if proc and is_alive(proc):
            log(f"Stopping {name}...")
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                proc.kill()
                proc.wait()


def main():
    global backend_process, frontend_process
    
    print("\n" + "="*50)
    print("  LEO 2.0 - Server Manager")
    print("="*50)
    print(f"Backend: {BACKEND_URL}")
    print(f"Frontend: {FRONTEND_URL}")
    print("="*50 + "\n")
    
    # Kill stale processes
    log("Cleaning up stale processes...")
    kill_port(BACKEND_PORT)
    kill_port(FRONTEND_PORT)
    time.sleep(2)
    
    backend_restarts = 0
    frontend_restarts = 0
    
    try:
        while True:
            # Check backend
            backend_ready = is_port_open(BACKEND_PORT)
            if not backend_ready or not is_alive(backend_process):
                log(f"Backend down - restarting... (restart #{backend_restarts + 1})")
                backend_restarts += 1
                stop_all()
                time.sleep(3)
                backend_process = start_backend()
            else:
                log(f"Backend: OK (port {BACKEND_PORT})")
            
            # Check frontend
            frontend_ready = is_port_open(FRONTEND_PORT)
            if not frontend_ready or not is_alive(frontend_process):
                log(f"Frontend down - restarting... (restart #{frontend_restarts + 1})")
                frontend_restarts += 1
                stop_all()
                time.sleep(3)
                frontend_process = start_frontend()
            else:
                log(f"Frontend: OK (port {FRONTEND_PORT})")
            
            log(f"Stats - Backend: {backend_restarts}, Frontend: {frontend_restarts}")
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        log("\nShutdown requested...")
    finally:
        stop_all()
        log("Done.")


if __name__ == "__main__":
    main()
