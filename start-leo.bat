@echo off
REM Leo 2.0 - Quick Start Script
REM Starts both backend and frontend servers

echo ============================================
echo   LEO 2.0 - Starting All Servers
echo ============================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if watchdog is needed
if "%1"=="--watchdog" (
    echo Starting with Watchdog monitoring...
    python watchdog.py
) else (
    echo Starting servers without watchdog...
    echo.
    echo Backend will run on: http://127.0.0.1:7860
    echo Frontend will run on: http://127.0.0.1:3000
    echo.
    echo To start with automatic restart monitoring, run:
    echo   python watchdog.py
    echo.
    echo ============================================
    
    REM Start backend
    echo Starting Backend Server...
    cd ClawForge\backend
    start "Leo 2.0 Backend" cmd /k "python main.py --server"
    cd ..\..
    
    REM Wait a moment
    timeout /t 5 /nobreak >nul
    
    REM Start frontend
    echo Starting Frontend Server...
    cd ClawForge\frontend
    start "Leo 2.0 Frontend" cmd /k "npm run dev"
    cd ..\..
    
    echo.
    echo ============================================
    echo   SERVERS STARTED!
    echo ============================================
    echo.
    echo Open your browser:
    echo   http://127.0.0.1:3000
    echo.
    echo Press any key to close this window...
    pause >nul
)
