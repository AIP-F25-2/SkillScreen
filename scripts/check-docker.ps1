# Docker Health Check Script
# This script checks if Docker is running and provides helpful guidance

param(
    [switch]$AutoStart,
    [switch]$Verbose
)

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-DockerRunning {
    try {
        $null = docker info 2>$null
        return $true
    } catch {
        return $false
    }
}

function Start-DockerDesktop {
    Write-ColorOutput "🚀 Attempting to start Docker Desktop..." -Color "Yellow"
    
    # Try to start Docker Desktop
    $dockerPaths = @(
        "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
        "${env:LOCALAPPDATA}\Docker\Docker Desktop.exe"
    )
    
    foreach ($path in $dockerPaths) {
        if (Test-Path $path) {
            Write-ColorOutput "Found Docker Desktop at: $path" -Color "Green"
            try {
                Start-Process -FilePath $path -WindowStyle Hidden
                Write-ColorOutput "✅ Docker Desktop started successfully" -Color "Green"
                return $true
            } catch {
                Write-ColorOutput "❌ Failed to start Docker Desktop: $($_.Exception.Message)" -Color "Red"
            }
        }
    }
    
    Write-ColorOutput "❌ Docker Desktop not found in common locations" -Color "Red"
    return $false
}

function Wait-ForDocker {
    param([int]$TimeoutSeconds = 60)
    
    Write-ColorOutput "⏳ Waiting for Docker to be ready..." -Color "Yellow"
    
    $elapsed = 0
    while ($elapsed -lt $TimeoutSeconds) {
        if (Test-DockerRunning) {
            Write-ColorOutput "✅ Docker is ready!" -Color "Green"
            return $true
        }
        
        Start-Sleep -Seconds 2
        $elapsed += 2
        
        if ($Verbose) {
            Write-ColorOutput "Still waiting... ($elapsed/$TimeoutSeconds seconds)" -Color "Cyan"
        }
    }
    
    Write-ColorOutput "❌ Docker did not start within $TimeoutSeconds seconds" -Color "Red"
    return $false
}

function Show-DockerHelp {
    Write-ColorOutput "`n🔧 Docker Troubleshooting Guide:" -Color "Magenta"
    Write-ColorOutput "=================================" -Color "Magenta"
    Write-ColorOutput ""
    Write-ColorOutput "1. Manual Start:" -Color "Yellow"
    Write-ColorOutput "   - Open Docker Desktop from Start Menu" -Color "White"
    Write-ColorOutput "   - Wait for Docker to fully start (whale icon in system tray)" -Color "White"
    Write-ColorOutput ""
    Write-ColorOutput "2. Check Docker Status:" -Color "Yellow"
    Write-ColorOutput "   - Look for Docker whale icon in system tray" -Color "White"
    Write-ColorOutput "   - Icon should be steady (not animated)" -Color "White"
    Write-ColorOutput ""
    Write-ColorOutput "3. Restart Docker:" -Color "Yellow"
    Write-ColorOutput "   - Right-click Docker whale icon" -Color "White"
    Write-ColorOutput "   - Select 'Restart Docker Desktop'" -Color "White"
    Write-ColorOutput ""
    Write-ColorOutput "4. Check WSL2 (if using WSL2 backend):" -Color "Yellow"
    Write-ColorOutput "   - Ensure WSL2 is installed and updated" -Color "White"
    Write-ColorOutput "   - Run: wsl --update" -Color "White"
    Write-ColorOutput ""
    Write-ColorOutput "5. Check Hyper-V (if using Hyper-V backend):" -Color "Yellow"
    Write-ColorOutput "   - Ensure Hyper-V is enabled in Windows Features" -Color "White"
    Write-ColorOutput "   - Restart computer if needed" -Color "White"
    Write-ColorOutput ""
    Write-ColorOutput "6. Download Docker Desktop:" -Color "Yellow"
    Write-ColorOutput "   - Visit: https://www.docker.com/products/docker-desktop" -Color "White"
    Write-ColorOutput "   - Download and install Docker Desktop for Windows" -Color "White"
}

# Main execution
Write-ColorOutput "🔍 Checking Docker status..." -Color "Cyan"

if (Test-DockerRunning) {
    Write-ColorOutput "✅ Docker is running and ready!" -Color "Green"
    exit 0
}

Write-ColorOutput "❌ Docker is not running" -Color "Red"

if ($AutoStart) {
    if (Start-DockerDesktop) {
        if (Wait-ForDocker -TimeoutSeconds 60) {
            Write-ColorOutput "🎉 Docker is now ready!" -Color "Green"
            exit 0
        }
    }
}

Show-DockerHelp

Write-ColorOutput "`n💡 Quick Fix:" -Color "Yellow"
Write-ColorOutput "1. Start Docker Desktop manually" -Color "White"
Write-ColorOutput "2. Wait for it to fully load" -Color "White"
Write-ColorOutput "3. Run this script again: .\scripts\check-docker.ps1" -Color "White"
Write-ColorOutput "4. Or use auto-start: .\scripts\check-docker.ps1 -AutoStart" -Color "White"

exit 1
