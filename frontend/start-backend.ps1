# SkillScreen Backend Startup Script
# Run this script after Docker Desktop is fully started

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SkillScreen Backend Services Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker status..." -ForegroundColor Yellow
try {
    $dockerStatus = docker ps 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker Desktop is not running!" -ForegroundColor Red
        Write-Host "Please start Docker Desktop and wait for it to fully initialize." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Then run this script again." -ForegroundColor White
        exit 1
    }
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Desktop is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and wait for it to fully initialize." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Starting all backend services..." -ForegroundColor Yellow
Write-Host ""

# Start services
docker-compose -f docker-compose.dev.yml up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Services started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Service Status:" -ForegroundColor Cyan
    docker-compose -f docker-compose.dev.yml ps
    Write-Host ""
    Write-Host "Access Points:" -ForegroundColor Cyan
    Write-Host "  Frontend:        http://localhost:3000" -ForegroundColor White
    Write-Host "  API Gateway:    http://localhost:5001" -ForegroundColor White
    Write-Host "  Text Service:   http://localhost:8001" -ForegroundColor White
    Write-Host "  Interview Svc:  http://localhost:8003" -ForegroundColor White
    Write-Host "  Assessment Svc: http://localhost:8005" -ForegroundColor White
    Write-Host "  Audio AI Svc:   http://localhost:8000" -ForegroundColor White
    Write-Host "  Seq Logging:    http://localhost:8081" -ForegroundColor White
    Write-Host ""
    Write-Host "View logs: docker-compose -f docker-compose.dev.yml logs -f" -ForegroundColor Yellow
    Write-Host "Stop services: docker-compose -f docker-compose.dev.yml down" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "❌ Failed to start services. Check the error messages above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - Docker Desktop not fully started" -ForegroundColor White
    Write-Host "  - Port conflicts (check if ports are already in use)" -ForegroundColor White
    Write-Host "  - Database connection issues" -ForegroundColor White
}

