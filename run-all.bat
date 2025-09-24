@echo off
REM SkillScreen Backend Services Startup Script for Windows
REM This script starts all backend services using Docker Compose

echo 🚀 Starting SkillScreen Backend Services...
echo ==============================================

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker first.
    pause
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Stop any existing containers
echo 🛑 Stopping existing containers...
docker-compose down

REM Remove any orphaned containers
echo 🧹 Cleaning up orphaned containers...
docker-compose down --remove-orphans

REM Build and start all services
echo 🔨 Building and starting all services...
docker-compose up --build -d

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 30 /nobreak >nul

REM Check service health
echo 🏥 Checking service health...
echo ==============================================

REM Check all services
set healthy_services=0
set total_services=12

echo Checking API Gateway (port 5000)...
curl -s -f http://localhost:5000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ API Gateway - Healthy
    set /a healthy_services+=1
) else (
    echo ❌ API Gateway - Unhealthy
)

echo Checking User Service (port 5001)...
curl -s -f http://localhost:5001/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ User Service - Healthy
    set /a healthy_services+=1
) else (
    echo ❌ User Service - Unhealthy
)

echo Checking Auth Service (port 5002)...
curl -s -f http://localhost:5002/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Auth Service - Healthy
    set /a healthy_services+=1
) else (
    echo ❌ Auth Service - Unhealthy
)

echo Checking Interview Service (port 5003)...
curl -s -f http://localhost:5003/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Interview Service - Healthy
    set /a healthy_services+=1
) else (
    echo ❌ Interview Service - Unhealthy
)

echo Checking Media Service (port 5004)...
curl -s -f http://localhost:5004/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Media Service - Healthy
    set /a healthy_services+=1
) else (
    echo ❌ Media Service - Unhealthy
)

echo Checking Video AI Service (port 5005)...
curl -s -f http://localhost:5005/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Video AI Service - Healthy
    set /a healthy_services+=1
) else (
    echo ❌ Video AI Service - Unhealthy
)

echo Checking Audio AI Service (port 5006)...
curl -s -f http://localhost:5006/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Audio AI Service - Healthy
    set /a healthy_services+=1
) else (
    echo ❌ Audio AI Service - Unhealthy
)

echo Checking Text AI Service (port 5007)...
curl -s -f http://localhost:5007/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Text AI Service - Healthy
    set /a healthy_services+=1
) else (
    echo ❌ Text AI Service - Unhealthy
)

echo Checking Assessment Service (port 5008)...
curl -s -f http://localhost:5008/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Assessment Service - Healthy
    set /a healthy_services+=1
) else (
    echo ❌ Assessment Service - Unhealthy
)

echo Checking Coding Service (port 5009)...
curl -s -f http://localhost:5009/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Coding Service - Healthy
    set /a healthy_services+=1
) else (
    echo ❌ Coding Service - Unhealthy
)

echo Checking Logger Service (port 5010)...
curl -s -f http://localhost:5010/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Logger Service - Healthy
    set /a healthy_services+=1
) else (
    echo ❌ Logger Service - Unhealthy
)

echo Checking Notification Service (port 5011)...
curl -s -f http://localhost:5011/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Notification Service - Healthy
    set /a healthy_services+=1
) else (
    echo ❌ Notification Service - Unhealthy
)

echo ==============================================
echo 📊 Health Check Summary:
echo    Healthy Services: %healthy_services%/%total_services%

if %healthy_services% equ %total_services% (
    echo 🎉 All services are healthy and running!
    echo.
    echo 🌐 Service URLs:
    echo    API Gateway:      http://localhost:5000
    echo    User Service:     http://localhost:5001
    echo    Auth Service:     http://localhost:5002
    echo    Interview Service: http://localhost:5003
    echo    Media Service:    http://localhost:5004
    echo    Video AI Service: http://localhost:5005
    echo    Audio AI Service: http://localhost:5006
    echo    Text AI Service:  http://localhost:5007
    echo    Assessment Service: http://localhost:5008
    echo    Coding Service:   http://localhost:5009
    echo    Logger Service:   http://localhost:5010
    echo    Notification Service: http://localhost:5011
    echo.
    echo 🔧 Quick Test Commands:
    echo    Test API Gateway: curl http://localhost:5000/route-test
    echo    Test Health:      curl http://localhost:5000/health
    echo    View Logs:        docker-compose logs -f
    echo    Stop Services:    docker-compose down
    echo.
    echo 📚 For detailed testing, run: python test-services.py
) else (
    echo ⚠️  Some services are not healthy. Check the logs:
    echo    docker-compose logs
    echo.
    echo 🔄 You can try restarting specific services:
    echo    docker-compose restart ^<service-name^>
)

echo ==============================================
pause
