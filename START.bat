@echo off
echo ============================================
echo    CLAWFORGE - Starting All Services
echo ============================================

REM Check if backend is already running
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | findstr /I "python.exe" >nul
if %ERRORLEVEL% equ 0 (
    echo [BACKEND] Already running or Python processes exist
) else (
    echo [BACKEND] Starting backend server...
    start "ClawForge Backend" cmd /c "cd /d %~dp0backend && python api.py"
)

REM Wait for backend to start
echo [WAITING] For backend to initialize (5s)...
timeout /t 5 /nobreak >nul

REM Start frontend in current window
echo [FRONTEND] Starting frontend...
cd /d %~dp0frontend
npm run dev

echo ============================================
echo    CLAWFORGE Started Successfully!
echo ============================================
echo    Frontend: http://localhost:7860
echo    Backend:  http://127.0.0.1:8000
echo ============================================
