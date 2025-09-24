# Fix Dockerfiles with correct paths
$services = @(
    "api-gateway",
    "user-service", 
    "auth-service",
    "interview-service",
    "media-service",
    "video-ai-service",
    "audio-ai-service", 
    "text-ai-service",
    "assessment-service",
    "coding-service",
    "logger-service",
    "notification-service"
)

foreach ($service in $services) {
    $dockerfilePath = "backend/$service/Dockerfile"
    $serviceName = $service
    
    Write-Host "Fixing $dockerfilePath..."
    
    $content = @"
FROM python:3.11-slim

WORKDIR /app

# Copy shared utilities
COPY shared /app/shared

# Copy service files
COPY backend/$serviceName/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/$serviceName .

EXPOSE $((5000 + $services.IndexOf($service)))

CMD ["python", "app.py"]
"@
    
    Set-Content -Path $dockerfilePath -Value $content
    Write-Host "Fixed $dockerfilePath"
}

Write-Host "All Dockerfiles fixed!"
