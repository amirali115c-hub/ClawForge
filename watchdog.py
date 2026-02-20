#!/usr/bin/env python3
"""
Leo 2.0 Server Watchdog - Windows Version
Automatically monitors and restarts backend and frontend servers.
"""

import subprocess
import time
import os
import sys
import socket
import signal
from datetime import datetime
from pathlib import Path

# Configuration
BACKEND_PORT = 7860
FRONTEND_PORT = 3000
BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}"
FRONTEND_URL = f"http://127.0.0.1:{FRONTEND_PORT}"
CHECK_INTERVAL = 10  # seconds
RESTART_DELAY = 5  # seconds

# Paths
SCRIPT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = SCRIPT_DIR / "ClawForge" / "backend"
FRONTEND_DIR = SCRIPT_DIR / "ClawForge" / "frontend"

# Process tracking
backend_process = None
frontend_process = None


def log(message: str):
    """Log message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def is_port_open(port: int) -> bool:
    """Check if a port is open and accepting connections."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except:
        return False


def is_process_running(process: subprocess.Popen) -> bool:
    """Check if process is still running."""
    if process is None:
        return False
    return process.poll() is None


def start_backend() -> subprocess.Popen:
    """Start the backend server."""
    log("Starting backend server...")
    try:
        # Create a new console window for backend
        cmd = [sys.executable, "main.py", "--server"]
        process = subprocess.Popen(
            cmd,
            cwd=str(BACKEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        log(f"Backend started with PID: {process.pid}")
        return process
    except Exception as e:
        log(f"Failed to start backend: {e}")
        return None


def start_frontend() -> subprocess.Popen:
    """Start the frontend dev server."""
    log("Starting frontend server...")
    try:
        # Create a new console window for frontend
        cmd = ["npm", "run", "dev"]
        process = subprocess.Popen(
            cmd,
            cwd=str(FRONTEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        log(f"Frontend started with PID: {process.pid}")
        return process
    except Exception as e:
        log(f"Failed to start frontend: {e}")
        return None


def stop_process(process: subprocess.Popen, name: str):
    """Stop a process gracefully."""
    if process is None:
        return
    
    log(f"Stopping {name} (PID: {process.pid})...")
    try:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        log(f"{name} stopped successfully")
    except Exception as e:
        log(f"Error stopping {name}: {e}")


def kill_process_on_port(port: int):
    """Kill any process running on the specified port."""
    try:
        # Find PID using netstat
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            capture_output=True,
            text=True,
            shell=True
        )
        for line in result.stdout.split("\n"):
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = int(parts[-1])
                    if pid > 0:
                        log(f"Killing process {pid} on port {port}")
                        subprocess.run(
                            f'taskkill /F /PID {pid}',
                            capture_output=True,
                            text=True,
                            shell=True
                        )
                        time.sleep(2)
                        break
    except Exception as e:
        log(f"Error killing process on port {port}: {e}")


def watchdog():
    """Main watchdog loop."""
    global backend_process, frontend_process
    
    print("\n" + "="*60)
    print("  🦁 LEO 2.0 SERVER WATCHDOG")
    print("="*60)
    log(f"Backend URL: {BACKEND_URL}")
    log(f"Frontend URL: {FRONTEND_URL}")
    log(f"Check interval: {CHECK_INTERVAL} seconds")
    print("="*60 + "\n")
    
    # Track restart counts
    backend_restarts = 0
    frontend_restarts = 0
    
    try:
        while True:
            # Check backend
            backend_up = is_port_open(BACKEND_PORT)
            backend_running = is_process_running(backend_process)
            
            if not backend_up:
                log(f"Backend is DOWN - Restarting... (restart #{backend_restarts + 1})")
                if backend_running:
                    stop_process(backend_process, "backend")
                # Kill any process on the port
                kill_process_on_port(BACKEND_PORT)
                time.sleep(RESTART_DELAY)
                backend_process = start_backend()
                backend_restarts += 1
            elif backend_running:
                log(f"Backend: ✅ Running on port {BACKEND_PORT}")
            
            # Check frontend
            frontend_up = is_port_open(FRONTEND_PORT)
            frontend_running = is_process_running(frontend_process)
            
            if not frontend_up:
                log(f"Frontend is DOWN - Restarting... (restart #{frontend_restarts + 1})")
                if frontend_running:
                    stop_process(frontend_process, "frontend")
                # Kill any process on the port
                kill_process_on_port(FRONTEND_PORT)
                time.sleep(RESTART_DELAY)
                frontend_process = start_frontend()
                frontend_restarts += 1
            elif frontend_running:
                log(f"Frontend: ✅ Running on port {FRONTEND_PORT}")
            
            # Summary
            status = f"Stats - Restarts: Backend={backend_restarts}, Frontend={frontend_restarts}"
            log(status)
            
            # Wait before next check
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        log("\nReceived shutdown signal...")
    finally:
        log("Stopping all servers...")
        stop_process(backend_process, "backend")
        stop_process(frontend_process, "frontend")
        log("Watchdog stopped.")


if __name__ == "__main__":
    # Change to script directory
    os.chdir(SCRIPT_DIR)
    
    # Run watchdog
    watchdog()
