# SkillScreen Backend Services Startup Script (Simplified)
# Professional implementation with best practices

param(
    [switch]$SkipHealthCheck,
    [switch]$Verbose
)

# Set error handling
$ErrorActionPreference = "Stop"

# Configuration
$ServicePorts = @{
    "api-gateway" = 5000
    "user-service" = 5001
    "auth-service" = 5002
    "interview-service" = 5003
    "media-service" = 5004
    "video-ai-service" = 5005
    "audio-ai-service" = 5006
    "text-ai-service" = 5007
    "assessment-service" = 5008
    "coding-service" = 5009
    "logger-service" = 5010
    "notification-service" = 5011
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-DockerRunning {
    try {
        $result = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            return $true
        } else {
            return $false
        }
    } catch {
        return $false
    }
}

function Test-DockerComposeAvailable {
    try {
        $result = docker-compose --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            return $true
        } else {
            return $false
        }
    } catch {
        return $false
    }
}

function Test-ServiceHealth {
    param(
        [string]$ServiceName,
        [int]$Port,
        [int]$MaxRetries = 10
    )
    
    $retryCount = 0
    do {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:$Port/health" -TimeoutSec 5 -ErrorAction Stop
            if ($response.status -eq "healthy") {
                return $true
            }
        } catch {
            # Service not ready yet
        }
        
        $retryCount++
        if ($retryCount -lt $MaxRetries) {
            Start-Sleep -Seconds 3
        }
    } while ($retryCount -lt $MaxRetries)
    
    return $false
}

function Start-SkillScreenServices {
    Write-ColorOutput "Starting SkillScreen Backend Services..." -Color "Magenta"
    Write-ColorOutput "==============================================" -Color "Magenta"
    
    # Pre-flight checks
    Write-ColorOutput "`nPerforming pre-flight checks..." -Color "Cyan"
    
    if (-not (Test-DockerRunning)) {
        Write-ColorOutput "ERROR: Docker is not running." -Color "Red"
        Write-ColorOutput "Please start Docker Desktop first:" -Color "Yellow"
        Write-ColorOutput "1. Open Docker Desktop from Start Menu" -Color "White"
        Write-ColorOutput "2. Wait for Docker to fully start" -Color "White"
        Write-ColorOutput "3. Run this script again" -Color "White"
        Write-ColorOutput "Download from: https://www.docker.com/products/docker-desktop" -Color "Cyan"
        exit 1
    }
    
    if (-not (Test-DockerComposeAvailable)) {
        Write-ColorOutput "ERROR: Docker Compose is not available." -Color "Red"
        Write-ColorOutput "Please install Docker Compose." -Color "Yellow"
        exit 1
    }
    
    Write-ColorOutput "SUCCESS: Pre-flight checks passed" -Color "Green"
    
    # Cleanup existing containers
    Write-ColorOutput "`nCleaning up existing containers..." -Color "Cyan"
    try {
        docker-compose down --remove-orphans 2>$null
        Write-ColorOutput "SUCCESS: Cleanup completed" -Color "Green"
    } catch {
        Write-ColorOutput "WARNING: Cleanup had some issues (this is usually fine)" -Color "Yellow"
    }
    
    # Build and start services
    Write-ColorOutput "`nBuilding and starting services..." -Color "Cyan"
    try {
        if ($Verbose) {
            docker-compose up --build -d
        } else {
            docker-compose up --build -d 2>$null
        }
        Write-ColorOutput "SUCCESS: Services started successfully" -Color "Green"
    } catch {
        Write-ColorOutput "ERROR: Failed to start services. Check the logs:" -Color "Red"
        Write-ColorOutput "   docker-compose logs" -Color "Cyan"
        exit 1
    }
    
    # Wait for services to be ready
    if (-not $SkipHealthCheck) {
        Write-ColorOutput "`nWaiting for services to be ready..." -Color "Cyan"
        Start-Sleep -Seconds 30
        
        # Health checks
        Write-ColorOutput "`nPerforming health checks..." -Color "Cyan"
        $healthyServices = 0
        $totalServices = $ServicePorts.Count
        
        foreach ($service in $ServicePorts.GetEnumerator()) {
            $serviceName = $service.Key
            $port = $service.Value
            
            Write-ColorOutput "   Checking $serviceName (port $port)..." -Color "Cyan" -NoNewline
            
            if (Test-ServiceHealth -ServiceName $serviceName -Port $port) {
                Write-ColorOutput " SUCCESS" -Color "Green"
                $healthyServices++
            } else {
                Write-ColorOutput " FAILED" -Color "Red"
            }
        }
        
        # Summary
        Write-ColorOutput "`nHealth Check Summary:" -Color "Magenta"
        Write-ColorOutput "   Healthy Services: $healthyServices/$totalServices" -Color "Cyan"
        
        if ($healthyServices -eq $totalServices) {
            Write-ColorOutput "`nSUCCESS: All services are healthy and running!" -Color "Green"
            Show-ServiceUrls
            Show-QuickCommands
        } else {
            Write-ColorOutput "`nWARNING: Some services are not healthy. Check the logs:" -Color "Yellow"
            Write-ColorOutput "   docker-compose logs" -Color "Cyan"
            Write-ColorOutput "`nYou can try restarting specific services:" -Color "Cyan"
            Write-ColorOutput "   docker-compose restart <service-name>" -Color "Cyan"
        }
    } else {
        Write-ColorOutput "`nSUCCESS: Services started (health checks skipped)" -Color "Green"
        Show-ServiceUrls
    }
}

function Show-ServiceUrls {
    Write-ColorOutput "`nService URLs:" -Color "Magenta"
    foreach ($service in $ServicePorts.GetEnumerator()) {
        $serviceName = $service.Key
        $port = $service.Value
        Write-ColorOutput "   $($serviceName.PadRight(20)) http://localhost:$port" -Color "Cyan"
    }
}

function Show-QuickCommands {
    Write-ColorOutput "`nQuick Commands:" -Color "Magenta"
    Write-ColorOutput "   Test API Gateway:    Invoke-RestMethod http://localhost:5000/route-test" -Color "Cyan"
    Write-ColorOutput "   Test Health:         Invoke-RestMethod http://localhost:5000/health" -Color "Cyan"
    Write-ColorOutput "   View Logs:           docker-compose logs -f" -Color "Cyan"
    Write-ColorOutput "   Stop Services:       docker-compose down" -Color "Cyan"
    Write-ColorOutput "   Run Tests:           python test-services.py" -Color "Cyan"
}

function Show-Help {
    Write-ColorOutput "SkillScreen Backend Services Startup Script" -Color "Magenta"
    Write-ColorOutput "=============================================" -Color "Magenta"
    Write-ColorOutput ""
    Write-ColorOutput "Usage:" -Color "Cyan"
    Write-ColorOutput "  .\start-services-simple.ps1 [OPTIONS]" -Color "Cyan"
    Write-ColorOutput ""
    Write-ColorOutput "Options:" -Color "Cyan"
    Write-ColorOutput "  -SkipHealthCheck    Skip health checks after startup" -Color "Cyan"
    Write-ColorOutput "  -Verbose           Show detailed Docker output" -Color "Cyan"
    Write-ColorOutput "  -Help              Show this help message" -Color "Cyan"
    Write-ColorOutput ""
    Write-ColorOutput "Examples:" -Color "Cyan"
    Write-ColorOutput "  .\start-services-simple.ps1" -Color "Cyan"
    Write-ColorOutput "  .\start-services-simple.ps1 -Verbose" -Color "Cyan"
    Write-ColorOutput "  .\start-services-simple.ps1 -SkipHealthCheck" -Color "Cyan"
}

# Main execution
if ($args -contains "-Help" -or $args -contains "--help" -or $args -contains "-h") {
    Show-Help
    exit 0
}

try {
    Start-SkillScreenServices
} catch {
    Write-ColorOutput "`nERROR: An error occurred: $($_.Exception.Message)" -Color "Red"
    Write-ColorOutput "`nFor help, run: .\start-services-simple.ps1 -Help" -Color "Cyan"
    exit 1
}
