@echo off
REM SkillScreen Backend Services - Simple Startup Script
REM This script calls the PowerShell startup script with proper execution policy

echo Starting SkillScreen Backend Services...
echo ========================================

REM Check if PowerShell is available
powershell -Command "Get-Host" >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: PowerShell is not available
    pause
    exit /b 1
)

REM Run the PowerShell script with execution policy bypass
powershell -ExecutionPolicy Bypass -File "start-services-simple.ps1" %*

REM Check if the script ran successfully
if %errorlevel% equ 0 (
    echo.
    echo ✅ Services started successfully!
    echo.
    echo Quick commands:
    echo   View logs:    docker-compose logs -f
    echo   Stop services: docker-compose down
    echo   Run tests:    python test-services.py
) else (
    echo.
    echo ❌ There was an issue starting the services.
    echo Check the output above for details.
)

echo.
pause
