@echo off
REM SkillScreen Backend Services - Direct Docker Compose Startup
REM This script bypasses PowerShell detection issues and uses Docker Compose directly

echo ========================================
echo SkillScreen Backend Services Startup
echo ========================================
echo.

REM Check if Docker is available
echo Checking Docker availability...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not available. Please install Docker Desktop.
    echo Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker Compose is available
echo Checking Docker Compose availability...
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker Compose is not available.
    pause
    exit /b 1
)

echo SUCCESS: Docker and Docker Compose are available
echo.

REM Stop any existing containers
echo Cleaning up existing containers...
docker-compose down --remove-orphans >nul 2>&1

REM Build and start services
echo Building and starting all services...
echo This may take a few minutes on first run...
echo.

docker-compose up --build -d

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start services.
    echo Check the output above for details.
    echo.
    echo Troubleshooting:
    echo 1. Make sure Docker Desktop is running
    echo 2. Check available disk space
    echo 3. Try: docker-compose logs
    pause
    exit /b 1
)

echo.
echo SUCCESS: Services are starting up...
echo.

REM Wait for services to be ready
echo Waiting for services to be ready (30 seconds)...
timeout /t 30 /nobreak >nul

REM Check service health
echo.
echo Checking service health...
echo ========================================

set healthy_count=0
set total_services=12

echo Checking API Gateway (port 5000)...
curl -s -f http://localhost:5000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] API Gateway - Healthy
    set /a healthy_count+=1
) else (
    echo [FAIL] API Gateway - Not responding
)

echo Checking User Service (port 5001)...
curl -s -f http://localhost:5001/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] User Service - Healthy
    set /a healthy_count+=1
) else (
    echo [FAIL] User Service - Not responding
)

echo Checking Auth Service (port 5002)...
curl -s -f http://localhost:5002/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Auth Service - Healthy
    set /a healthy_count+=1
) else (
    echo [FAIL] Auth Service - Not responding
)

echo Checking Interview Service (port 5003)...
curl -s -f http://localhost:5003/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Interview Service - Healthy
    set /a healthy_count+=1
) else (
    echo [FAIL] Interview Service - Not responding
)

echo Checking Media Service (port 5004)...
curl -s -f http://localhost:5004/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Media Service - Healthy
    set /a healthy_count+=1
) else (
    echo [FAIL] Media Service - Not responding
)

echo Checking Video AI Service (port 5005)...
curl -s -f http://localhost:5005/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Video AI Service - Healthy
    set /a healthy_count+=1
) else (
    echo [FAIL] Video AI Service - Not responding
)

echo Checking Audio AI Service (port 5006)...
curl -s -f http://localhost:5006/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Audio AI Service - Healthy
    set /a healthy_count+=1
) else (
    echo [FAIL] Audio AI Service - Not responding
)

echo Checking Text AI Service (port 5007)...
curl -s -f http://localhost:5007/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Text AI Service - Healthy
    set /a healthy_count+=1
) else (
    echo [FAIL] Text AI Service - Not responding
)

echo Checking Assessment Service (port 5008)...
curl -s -f http://localhost:5008/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Assessment Service - Healthy
    set /a healthy_count+=1
) else (
    echo [FAIL] Assessment Service - Not responding
)

echo Checking Coding Service (port 5009)...
curl -s -f http://localhost:5009/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Coding Service - Healthy
    set /a healthy_count+=1
) else (
    echo [FAIL] Coding Service - Not responding
)

echo Checking Logger Service (port 5010)...
curl -s -f http://localhost:5010/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Logger Service - Healthy
    set /a healthy_count+=1
) else (
    echo [FAIL] Logger Service - Not responding
)

echo Checking Notification Service (port 5011)...
curl -s -f http://localhost:5011/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Notification Service - Healthy
    set /a healthy_count+=1
) else (
    echo [FAIL] Notification Service - Not responding
)

echo ========================================
echo Health Check Summary: %healthy_count%/%total_services% services healthy

if %healthy_count% equ %total_services% (
    echo.
    echo SUCCESS: All services are healthy and running!
    echo.
    echo Service URLs:
    echo   API Gateway:      http://localhost:5000
    echo   User Service:     http://localhost:5001
    echo   Auth Service:     http://localhost:5002
    echo   Interview Service: http://localhost:5003
    echo   Media Service:    http://localhost:5004
    echo   Video AI Service: http://localhost:5005
    echo   Audio AI Service: http://localhost:5006
    echo   Text AI Service:  http://localhost:5007
    echo   Assessment Service: http://localhost:5008
    echo   Coding Service:   http://localhost:5009
    echo   Logger Service:   http://localhost:5010
    echo   Notification Service: http://localhost:5011
    echo.
    echo Quick Test Commands:
    echo   Test API Gateway: curl http://localhost:5000/route-test
    echo   Test Health:      curl http://localhost:5000/health
    echo   View Logs:        docker-compose logs -f
    echo   Stop Services:    docker-compose down
    echo   Run Tests:        python test-services.py
) else (
    echo.
    echo WARNING: Some services are not healthy.
    echo Check the logs: docker-compose logs
    echo.
    echo You can try restarting specific services:
    echo   docker-compose restart ^<service-name^>
)

echo.
echo ========================================
pause
