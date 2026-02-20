@echo off
REM Leo 2.0 - Start Script (Uses Python)
REM Run this to start both servers with auto-restart

echo ============================================
echo   LEO 2.0 - Starting Servers
echo ============================================
echo.

cd /d "%~dp0"

echo Starting Leo 2.0 Server Manager...
echo.
echo Backend: http://127.0.0.1:9000
echo Frontend: http://127.0.0.1:3000
echo.
echo Press Ctrl+C to stop
echo.

python start-leo.py
