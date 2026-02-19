@echo off
REM ClawForge v4.0 - Quick Start Script
REM ====================================

echo.
echo ========================================
echo   ClawForge v4.0 - Starting...
echo ========================================
echo.

REM Check if backend is already running
netstat -ano | findstr :8000 >nul
if %errorlevel% equ 0 (
    echo [OK] Backend already running on port 8000
) else (
    echo [INFO] Starting backend...
    start "ClawForge Backend" cmd /c "cd /d \"%~dp0backend\" && python main.py --server"
    echo [OK] Backend starting...
)

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
echo [INFO] Starting frontend...
start "ClawForge Frontend" cmd /c "cd /d \"%~dp0frontend\" && npm run dev"

echo.
echo ========================================
echo   ClawForge is starting...
echo ========================================
echo.
echo   Backend API:  http://127.0.0.1:8000
echo   Frontend:     http://127.0.0.1:7860
echo.
echo   IMPORTANT: Add your API key to backend\.env
echo   Get key from: https://build.nvidia.com/
echo.
echo   Keep both windows open!
echo ========================================

pause
