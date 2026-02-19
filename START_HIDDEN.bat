@echo off
REM ClawForge v4.0 - Background Start (No terminal window)
REM Creates a hidden window that runs ClawForge

cd /d "%~dp0"

REM Run launcher hidden
if exist "logs" (
    python launcher.py > logs\launcher.log 2>&1
) else (
    mkdir logs
    python launcher.py > logs\launcher.log 2>&1
)

echo ClawForge started (check logs/launcher.log for details)
