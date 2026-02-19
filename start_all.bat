@echo off
REM ClawForge v4.0 - Startup Script
REM Starts both backend and frontend automatically

echo.
echo ============================================
echo   ClawForge v4.0 - Starting Services
echo ============================================
echo.

REM Navigate to ClawForge directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.9+
    pause
    exit /b 1
)

REM Start Backend (port 8000) in background
echo [1/2] Starting Backend Server...
start "ClawForge Backend" /B python backend/main.py --server > logs\backend.log 2>&1

REM Wait for backend to start
timeout /t 5 /nobreak >nul

REM Start Frontend (port 7860)
echo [2/2] Starting Frontend Dashboard...
cd frontend
start "ClawForge Frontend" /B npm run dev > ..\logs\frontend.log 2>&1

echo.
echo ============================================
echo   ClawForge Started Successfully!
echo ============================================
echo.
echo   Backend:  http://127.0.0.1:8000
echo   Frontend: http://127.0.0.1:7860
echo   API Docs: http://127.0.0.1:8000/docs
echo.
echo   Press any key to stop all services...
pause >nul

REM Stop all services on key press
taskkill /FI "WINDOWTITLE eq ClawForge*" >nul 2>&1

echo.
echo All services stopped.
exit /b 0
