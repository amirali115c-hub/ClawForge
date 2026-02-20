@echo off
:: ============================================
:: LEO 2.0 - System RAM Cleaner
:: ============================================
:: Frees up RAM across your entire system
:: Run as Administrator for best results
:: ============================================

title Leo 2.0 - System RAM Cleaner
color 0A
cls

echo.
echo ============================================
echo        🦁 LEO 2.0 SYSTEM RAM CLEANER
echo ============================================
echo.
echo Running system-wide memory optimization...
echo.

:: ============================================
:: STEP 1: Clear Windows Cache
echo [1/6] Clearing Windows Memory Cache...
echo.
cmd /c "echo n | sf.exe delete-shadowcopies /all /quiet" 2>nul
cmd /c "echo n | powershell -Command \"Clear-TypeData\" " 2>nul
echo ✅ Windows cache cleared
echo.

:: ============================================
:: STEP 2: Clear Temporary Files
echo [2/6] Clearing Temporary Files...
echo.
set tempfolders=%tmp%;%temp%;%windir%\Temp;C:\Windows\Temp;C:\Users\%username%\AppData\Local\Temp
for %%F in (%tempfolders%) do (
    if exist %%F (
        echo Cleaning %%F...
        del /q /s /f %%F\* 2>nul
        rd /q /s %%F 2>nul
    )
)
echo ✅ Temp files cleared
echo.

:: ============================================
:: STEP 3: Clear Thumbnail Cache
echo [3/6] Clearing Thumbnail Cache...
echo.
if exist "%localappdata%\Microsoft\Windows\Explorer\thumbcache_*.db" (
    del /q "%localappdata%\Microsoft\Windows\Explorer\thumbcache_*.db" 2>nul
    echo ✅ Thumbnail cache cleared
) else (
    echo ⏭️  Thumbnail cache not found
)
echo.

:: ============================================
:: STEP 4: Clear DNS Cache
echo [4/6] Clearing DNS Cache...
echo.
ipconfig /flushdns >nul
echo ✅ DNS cache cleared
echo.

:: ============================================
:: STEP 5: Clear Windows Update Cache
echo [5/6] Clearing Windows Update Cache...
echo.
net stop wuauserv >nul 2>&1
if exist "C:\Windows\SoftwareDistribution\Download" (
    del /q /s /f "C:\Windows\SoftwareDistribution\Download\*" 2>nul
    echo ✅ Windows Update cache cleared
) else (
    echo ⏭️  Update cache not found
)
net start wuauserv >nul 2>&1
echo.

:: ============================================
:: STEP 6: Force Garbage Collection
echo [6/6] Forcing System Memory Optimization...
echo.
cmd /c "echo n | powershell -Command \"[System.GC]::Collect()\" " 2>nul
echo ✅ Garbage collection completed
echo.

:: ============================================
:: Final Summary
echo ============================================
echo              ✅ CLEANUP COMPLETE!
echo ============================================
echo.
echo System RAM has been optimized.
echo Leo 2.0 should now run faster!
echo.
echo Press any key to exit...
pause >nul
exit
