# ClawForge v4.0 - Permanent Startup Script
# Run this to start ClawForge and keep it running

param(
    [switch]$Background
)

$ErrorActionPreference = "Stop"

# Colors for output
$Green = "Green"
$Yellow = "Yellow"
$Cyan = "Cyan"

function Write-Status {
    param([string]$Message, [string]$Color = $Green)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] " -NoNewline
    Write-Host $Message -ForegroundColor $Color
}

function Start-ClawForge {
    $baseDir = Split-Path -Parent (Get-PSScriptRoot)
    Set-Location $baseDir
    
    Write-Status "============================================" $Cyan
    Write-Status "  ClawForge v4.0 - Starting Services" $Cyan
    Write-Status "============================================" $Cyan
    Write-Status ""
    
    # Create logs directory
    $logsDir = Join-Path $baseDir "logs"
    if (-not (Test-Path $logsDir)) {
        New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    }
    
    # Start Backend
    Write-Status "[1/2] Starting Backend Server (port 8000)..." $Yellow
    $backendLog = Join-Path $logsDir "backend.log"
    $backendProcess = Start-Process -FilePath "python" `
        -ArgumentList "backend/main.py --server" `
        -WorkingDirectory $baseDir `
        -PassThru `
        -NoNewWindow
    
    Write-Status "      Backend PID: $($backendProcess.Id)" $Green
    
    # Wait for backend
    Start-Sleep -Seconds 5
    
    # Start Frontend
    Write-Status "[2/2] Starting Frontend Dashboard (port 7860)..." $Yellow
    $frontendDir = Join-Path $baseDir "frontend"
    $frontendLog = Join-Path $logsDir "frontend.log"
    $frontendProcess = Start-Process -FilePath "npm" `
        -ArgumentList "run dev" `
        -WorkingDirectory $frontendDir `
        -PassThru `
        -NoNewWindow
    
    Write-Status "      Frontend PID: $($frontendProcess.Id)" $Green
    
    Write-Status ""
    Write-Status "============================================" $Cyan
    Write-Status "  ClawForge is Running!" $Cyan
    Write-Status "============================================" $Cyan
    Write-Status ""
    Write-Status "  Backend:  http://127.0.0.1:8000" $Green
    Write-Status "  Frontend: http://127.0.0.1:7860" $Green
    Write-Status "  API Docs: http://127.0.0.1:8000/docs" $Green
    Write-Status ""
    Write-Status "Press Ctrl+C to stop all services..." $Yellow
    Write-Status ""
    
    # Wait for processes
    try {
        Wait-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
        Wait-Process -Id $frontendProcess.Id -ErrorAction SilentlyContinue
    }
    catch {
        Write-Status "Services stopped." $Green
    }
}

function Stop-ClawForge {
    Write-Status "Stopping ClawForge services..." $Yellow
    
    # Stop backend
    Get-Process | Where-Object { $_.ProcessName -like "python" -and $_.MainModule.FileName -like "*ClawForge*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # Stop frontend
    Get-Process | Where-Object { $_.ProcessName -like "node" -and $_.MainModule.FileName -like "*ClawForge*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Status "All services stopped." $Green
}

# Main
if ($Background) {
    Start-ClawForge
} else {
    Start-ClawForge
}
