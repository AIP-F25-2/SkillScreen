# SkillScreen Backend Services Startup Script (PowerShell)
# Professional implementation with best practices

param(
    [switch]$SkipHealthCheck,
    [switch]$Verbose,
    [string]$Environment = "development"
)

# Set error handling
$ErrorActionPreference = "Stop"

# Configuration
$Script:ServicePorts = @{
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

# Colors for output
$Colors = @{
    Success = "Green"
    Error = "Red"
    Warning = "Yellow"
    Info = "Cyan"
    Header = "Magenta"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White",
        [switch]$NoNewline
    )
    
    if ($NoNewline) {
        Write-Host $Message -ForegroundColor $Color -NoNewline
    } else {
        Write-Host $Message -ForegroundColor $Color
    }
}

function Test-DockerRunning {
    try {
        $null = docker info 2>$null
        return $true
    } catch {
        return $false
    }
}

function Start-DockerIfNeeded {
    if (-not (Test-DockerRunning)) {
        Write-ColorOutput "❌ Docker is not running." -Color $Colors.Error
        Write-ColorOutput "`n🔧 Attempting to start Docker Desktop..." -Color $Colors.Warning
        
        # Try to start Docker Desktop
        $dockerPaths = @(
            "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe",
            "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
            "${env:LOCALAPPDATA}\Docker\Docker Desktop.exe"
        )
        
        $dockerStarted = $false
        foreach ($path in $dockerPaths) {
            if (Test-Path $path) {
                try {
                    Start-Process -FilePath $path -WindowStyle Hidden
                    Write-ColorOutput "✅ Docker Desktop started successfully" -Color $Colors.Success
                    $dockerStarted = $true
                    break
                } catch {
                    Write-ColorOutput "❌ Failed to start Docker Desktop: $($_.Exception.Message)" -Color $Colors.Error
                }
            }
        }
        
        if (-not $dockerStarted) {
            Write-ColorOutput "❌ Could not start Docker Desktop automatically." -Color $Colors.Error
            Write-ColorOutput "`n💡 Please start Docker Desktop manually:" -Color $Colors.Info
            Write-ColorOutput "   1. Open Docker Desktop from Start Menu" -Color $Colors.Info
            Write-ColorOutput "   2. Wait for Docker to fully start (whale icon in system tray)" -Color $Colors.Info
            Write-ColorOutput "   3. Run this script again" -Color $Colors.Info
            Write-ColorOutput "`n📥 Download Docker Desktop: https://www.docker.com/products/docker-desktop" -Color $Colors.Info
            exit 1
        }
        
        # Wait for Docker to be ready
        Write-ColorOutput "⏳ Waiting for Docker to be ready..." -Color $Colors.Info
        $timeout = 60
        $elapsed = 0
        
        while ($elapsed -lt $timeout) {
            if (Test-DockerRunning) {
                Write-ColorOutput "✅ Docker is ready!" -Color $Colors.Success
                return $true
            }
            
            Start-Sleep -Seconds 2
            $elapsed += 2
            
            if ($Verbose) {
                Write-ColorOutput "   Still waiting... ($elapsed/$timeout seconds)" -Color $Colors.Info
            }
        }
        
        Write-ColorOutput "❌ Docker did not start within $timeout seconds" -Color $Colors.Error
        Write-ColorOutput "Please start Docker Desktop manually and try again." -Color $Colors.Info
        exit 1
    }
    return $true
}

function Test-DockerComposeAvailable {
    try {
        $null = docker-compose --version 2>$null
        return $true
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
    Write-ColorOutput "🚀 Starting SkillScreen Backend Services..." -Color $Colors.Header
    Write-ColorOutput "Environment: $Environment" -Color $Colors.Info
    Write-ColorOutput "==============================================" -Color $Colors.Header
    
    # Pre-flight checks
    Write-ColorOutput "`n🔍 Performing pre-flight checks..." -Color $Colors.Info
    
    Start-DockerIfNeeded
    
    if (-not (Test-DockerComposeAvailable)) {
        Write-ColorOutput "❌ Docker Compose is not available. Please install Docker Compose." -Color $Colors.Error
        exit 1
    }
    
    Write-ColorOutput "✅ Pre-flight checks passed" -Color $Colors.Success
    
    # Cleanup existing containers
    Write-ColorOutput "`n🧹 Cleaning up existing containers..." -Color $Colors.Info
    try {
        docker-compose down --remove-orphans 2>$null
        Write-ColorOutput "✅ Cleanup completed" -Color $Colors.Success
    } catch {
        Write-ColorOutput "⚠️  Cleanup had some issues (this is usually fine)" -Color $Colors.Warning
    }
    
    # Build and start services
    Write-ColorOutput "`n🔨 Building and starting services..." -Color $Colors.Info
    try {
        if ($Verbose) {
            docker-compose up --build -d
        } else {
            docker-compose up --build -d 2>$null
        }
        Write-ColorOutput "✅ Services started successfully" -Color $Colors.Success
    } catch {
        Write-ColorOutput "❌ Failed to start services. Check the logs:" -Color $Colors.Error
        Write-ColorOutput "   docker-compose logs" -Color $Colors.Info
        exit 1
    }
    
    # Wait for services to be ready
    if (-not $SkipHealthCheck) {
        Write-ColorOutput "`n⏳ Waiting for services to be ready..." -Color $Colors.Info
        Start-Sleep -Seconds 30
        
        # Health checks
        Write-ColorOutput "`n🏥 Performing health checks..." -Color $Colors.Info
        $healthyServices = 0
        $totalServices = $Script:ServicePorts.Count
        
        foreach ($service in $Script:ServicePorts.GetEnumerator()) {
            $serviceName = $service.Key
            $port = $service.Value
            
            Write-ColorOutput "   Checking $serviceName (port $port)..." -Color $Colors.Info -NoNewline
            
            if (Test-ServiceHealth -ServiceName $serviceName -Port $port) {
                Write-ColorOutput " ✅" -Color $Colors.Success
                $healthyServices++
            } else {
                Write-ColorOutput " ❌" -Color $Colors.Error
            }
        }
        
        # Summary
        Write-ColorOutput "`n📊 Health Check Summary:" -Color $Colors.Header
        Write-ColorOutput "   Healthy Services: $healthyServices/$totalServices" -Color $Colors.Info
        
        if ($healthyServices -eq $totalServices) {
            Write-ColorOutput "`n🎉 All services are healthy and running!" -Color $Colors.Success
            Show-ServiceUrls
            Show-QuickCommands
        } else {
            Write-ColorOutput "`n⚠️  Some services are not healthy. Check the logs:" -Color $Colors.Warning
            Write-ColorOutput "   docker-compose logs" -Color $Colors.Info
            Write-ColorOutput "`n🔄 You can try restarting specific services:" -Color $Colors.Info
            Write-ColorOutput "   docker-compose restart <service-name>" -Color $Colors.Info
        }
    } else {
        Write-ColorOutput "`n✅ Services started (health checks skipped)" -Color $Colors.Success
        Show-ServiceUrls
    }
}

function Show-ServiceUrls {
    Write-ColorOutput "`n🌐 Service URLs:" -Color $Colors.Header
    foreach ($service in $Script:ServicePorts.GetEnumerator()) {
        $serviceName = $service.Key
        $port = $service.Value
        Write-ColorOutput "   $($serviceName.PadRight(20)) http://localhost:$port" -Color $Colors.Info
    }
}

function Show-QuickCommands {
    Write-ColorOutput "`n🔧 Quick Commands:" -Color $Colors.Header
    Write-ColorOutput "   Test API Gateway:    Invoke-RestMethod http://localhost:5000/route-test" -Color $Colors.Info
    Write-ColorOutput "   Test Health:         Invoke-RestMethod http://localhost:5000/health" -Color $Colors.Info
    Write-ColorOutput "   View Logs:           docker-compose logs -f" -Color $Colors.Info
    Write-ColorOutput "   Stop Services:       docker-compose down" -Color $Colors.Info
    Write-ColorOutput "   Run Tests:           python test-services.py" -Color $Colors.Info
}

function Show-Help {
    Write-ColorOutput "SkillScreen Backend Services Startup Script" -Color $Colors.Header
    Write-ColorOutput "=============================================" -Color $Colors.Header
    Write-ColorOutput ""
    Write-ColorOutput "Usage:" -Color $Colors.Info
    Write-ColorOutput "  .\start-services.ps1 [OPTIONS]" -Color $Colors.Info
    Write-ColorOutput ""
    Write-ColorOutput "Options:" -Color $Colors.Info
    Write-ColorOutput "  -SkipHealthCheck    Skip health checks after startup" -Color $Colors.Info
    Write-ColorOutput "  -Verbose           Show detailed Docker output" -Color $Colors.Info
    Write-ColorOutput "  -Environment       Set environment (default: development)" -Color $Colors.Info
    Write-ColorOutput "  -Help              Show this help message" -Color $Colors.Info
    Write-ColorOutput ""
    Write-ColorOutput "Examples:" -Color $Colors.Info
    Write-ColorOutput "  .\start-services.ps1" -Color $Colors.Info
    Write-ColorOutput "  .\start-services.ps1 -Verbose" -Color $Colors.Info
    Write-ColorOutput "  .\start-services.ps1 -SkipHealthCheck" -Color $Colors.Info
}

# Main execution
if ($args -contains "-Help" -or $args -contains "--help" -or $args -contains "-h") {
    Show-Help
    exit 0
}

try {
    Start-SkillScreenServices
} catch {
    Write-ColorOutput "`n❌ An error occurred: $($_.Exception.Message)" -Color $Colors.Error
    Write-ColorOutput "`nFor help, run: .\start-services.ps1 -Help" -Color $Colors.Info
    exit 1
}
