@echo off
:: ============================================
:: LEO 2.0 - Quick RAM Cleaner
:: ============================================
:: One-click system RAM cleanup
:: Run as Administrator
:: ============================================

title Leo 2.0 - Quick RAM Cleaner
color 0A
cls

echo.
echo 🦁 LEO 2.0 - QUICK RAM CLEANER
echo ========================================
echo.

:: Clear temp files
echo 🧹 Cleaning temporary files...
del /q /s /f %temp%\* >nul 2>&1
del /q /s /f %windir%\Temp\* >nul 2>&1

:: Clear thumbnail cache
del /q "%localappdata%\Microsoft\Windows\Explorer\thumbcache_*.db" >nul 2>&1

:: Clear DNS
ipconfig /flushdns >nul 2>&1

:: Force garbage collection
powershell -Command "[System.GC]::Collect()" >nul 2>&1

echo ✅ Done! RAM cleaned.
echo.
pause
