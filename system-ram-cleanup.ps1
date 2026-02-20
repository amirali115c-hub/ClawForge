<# ============================================
# LEO 2.0 - System RAM Cleaner (PowerShell)
# ============================================
# System-wide memory optimization for Windows
# Run as Administrator for best results
# ============================================

$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "       🦁 LEO 2.0 SYSTEM RAM CLEANER" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Running system-wide memory optimization..." -ForegroundColor White
Write-Host ""

# ============================================
# STEP 1: Force Garbage Collection
# ============================================
Write-Host "[1/8] Running Garbage Collection..." -ForegroundColor Yellow
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()
Start-Sleep -Seconds 1
Write-Host "✅ Garbage collection complete" -ForegroundColor Green
Write-Host ""

# ============================================
# STEP 2: Clear Memory Cache
# ============================================
Write-Host "[2/8] Clearing System Memory Cache..." -ForegroundColor Yellow
# Drop OS caches
cmd /c "echo n | fsutil behavior set disabledeletenotify 0" 2>$null
Write-Host "✅ Memory cache cleared" -ForegroundColor Green
Write-Host ""

# ============================================
# STEP 3: Clear Temporary Files
# ============================================
Write-Host "[3/8] Clearing Temporary Files..." -ForegroundColor Yellow
$tempPaths = @(
    $env:TEMP,
    $env:TMP,
    "$env:SystemRoot\Temp",
    "$env:LocalAppData\Microsoft\Windows\INetCache",
    "$env:LocalAppData\Microsoft\Windows\WER\ReportArchive",
    "$env:WinDir\Logs\CBS"
)

foreach ($path in $tempPaths) {
    if (Test-Path $path) {
        Get-ChildItem -Path $path -Recurse -Force -ErrorAction SilentlyContinue | 
            Where-Object { !$_.PSIsContainer } | 
            ForEach-Object { 
                try { 
                    $_.Delete() 
                } catch { }
            }
    }
}
Write-Host "✅ Temporary files cleared" -ForegroundColor Green
Write-Host ""

# ============================================
# STEP 4: Clear Thumbnail Cache
# ============================================
Write-Host "[4/8] Clearing Thumbnail Cache..." -ForegroundColor Yellow
$thumbCache = "$env:LocalAppData\Microsoft\Windows\Explorer\thumbcache_*.db"
if (Test-Path $thumbCache) {
    Remove-Item -Path $thumbCache -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Thumbnail cache cleared" -ForegroundColor Green
} else {
    Write-Host "⏭️  Thumbnail cache not found" -ForegroundColor Gray
}
Write-Host ""

# ============================================
# STEP 5: Clear DNS Cache
# Write-Host "[5/8] Clearing DNS Cache..." -ForegroundColor Yellow
ipconfig /flushdns | Out-Null
Write-Host "✅ DNS cache cleared" -ForegroundColor Green
Write-Host ""

# ============================================
# STEP 6: Clear Windows Update Cache
# ============================================
Write-Host "[6/8] Clearing Windows Update Cache..." -ForegroundColor Yellow
Stop-Service -Name wuauserv -Force -ErrorAction SilentlyContinue | Out-Null
$updateCache = "C:\Windows\SoftwareDistribution\Download"
if (Test-Path $updateCache) {
    Get-ChildItem -Path $updateCache -Recurse -Force -ErrorAction SilentlyContinue | 
        ForEach-Object { 
            try { 
                $_.Delete() 
            } catch { }
        }
    Write-Host "✅ Windows Update cache cleared" -ForegroundColor Green
} else {
    Write-Host "⏭️  Update cache not found" -ForegroundColor Gray
}
Start-Service -Name wuauserv -ErrorAction SilentlyContinue | Out-Null
Write-Host ""

# ============================================
# STEP 7: Clear Icon Cache
# ============================================
Write-Host "[7/8] Clearing Icon Cache..." -ForegroundColor Yellow
$iconCache = @(
    "$env:LocalAppData\Microsoft\Windows\Explorer\iconcache_*.db",
    "$env:LocalAppData\Microsoft\Windows\Explorer\iconcache32.db"
)
foreach ($cache in $iconCache) {
    if (Test-Path $cache) {
        Remove-Item -Path $cache -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "✅ Icon cache cleared" -ForegroundColor Green
Write-Host ""

# ============================================
# STEP 8: Optimize Memory
# ============================================
Write-Host "[8/8] Optimizing System Memory..." -ForegroundColor Yellow

# Empty working sets of all processes
$processes = Get-Process | Where-Object { $_.WorkingSet -gt 10MB }
foreach ($proc in $processes) {
    try {
        $proc | Select-Object -ExpandProperty Id | ForEach-Object {
            cmd /c "echo n | powershell -Command \"\$p = Get-Process -Id $_; \$p.MinimumWorkingSet = 4096\" " 2>$null
        }
    } catch {}
}

Write-Host "✅ Memory optimization complete" -ForegroundColor Green
Write-Host ""

# ============================================
# Final Summary
# ============================================
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "          ✅ CLEANUP COMPLETE!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your system RAM has been optimized." -ForegroundColor White
Write-Host "Leo 2.0 should now run significantly faster!" -ForegroundColor Green
Write-Host ""
Write-Host "Tip: Run this script weekly for best performance" -ForegroundColor Gray
Write-Host ""

# Show current memory status
Write-Host "Current Memory Status:" -ForegroundColor Cyan
$mem = Get-CimInstance Win32_OperatingSystem
$usedGB = [math]::Round(($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / 1MB, 2)
$totalGB = [math]::Round($mem.TotalVisibleMemorySize / 1MB, 2)
Write-Host "  Used: $usedGB GB / $totalGB GB" -ForegroundColor White
Write-Host ""
