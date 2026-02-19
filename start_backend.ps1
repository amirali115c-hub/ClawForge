# ClawForge v4.0 - Start Backend (Windows PowerShell)
# Usage: .\start_backend.ps1

Write-Host "🚀 Starting ClawForge Backend Server..." -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Gray

# Pull Ollama model
Write-Host "`n📦 Pulling Ollama model (llama3)..." -ForegroundColor Cyan
ollama pull llama3

# Start backend
Write-Host "`n🔧 Starting Backend (FastAPI on port 8000)..." -ForegroundColor Cyan
cd $PSScriptRoot
python backend/main.py

# Keep window open
Write-Host "`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
