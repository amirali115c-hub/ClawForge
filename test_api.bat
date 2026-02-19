@echo off
REM ClawForge - Quick Test Script for NVIDIA API

echo ============================================
echo   ClawForge - NVIDIA API Test
echo ============================================
echo.

REM Check if API key is provided as argument
if "%1"=="" (
    echo No API key provided!
    echo.
    echo Usage:
    echo   test_api.bat YOUR_NVIDIA_API_KEY
    echo.
    echo Or set environment variable:
    echo   $env:NVIDIA_API_KEY = "your_key"
    echo.
    pause
    exit /b 1
)

echo Testing NVIDIA API with Qwen3.5-397B...
echo.

python -c "
import sys
sys.path.insert(0, 'backend')

from nvidia_client import test_nvidia_api_key

result = test_nvidia_api_key('%1')

if result['success']:
    print('SUCCESS! NVIDIA API is working.')
    print()
    print('Response from Qwen3.5-397B:')
    print('-' * 50)
    print(result['response'][:500])
    print('-' * 50)
    print()
    print('Available models:')
    for m in result['models']:
        print(f'  - {m}')
else:
    print('FAILED!')
    print(f'Error: {result[\"error\"]}')
"

echo.
pause
