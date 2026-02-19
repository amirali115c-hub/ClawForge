# ClawForge v4.0 - Start Frontend (Windows PowerShell)
# Usage: .\start_frontend.ps1

Write-Host "🎨 Starting ClawForge Frontend Dashboard..." -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Gray

Write-Host "`n🌐 Starting React Dashboard (port 7860)..." -ForegroundColor Cyan
cd $PSScriptRoot\frontend
npm run dev

Write-Host "`nDashboard should open at: http://127.0.0.1:7860" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
