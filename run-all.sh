#!/bin/bash

# SkillScreen Backend Services Startup Script
# This script starts all backend services using Docker Compose

echo "🚀 Starting SkillScreen Backend Services..."
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Remove any orphaned containers
echo "🧹 Cleaning up orphaned containers..."
docker-compose down --remove-orphans

# Build and start all services
echo "🔨 Building and starting all services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🏥 Checking service health..."
echo "=============================================="

# Function to check service health
check_service() {
    local service_name=$1
    local port=$2
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
            echo "✅ $service_name (port $port) - Healthy"
            return 0
        else
            echo "⏳ $service_name (port $port) - Waiting... (attempt $attempt/$max_attempts)"
            sleep 5
            ((attempt++))
        fi
    done
    
    echo "❌ $service_name (port $port) - Unhealthy"
    return 1
}

# Check all services
services=(
    "API Gateway:5000"
    "User Service:5001"
    "Auth Service:5002"
    "Interview Service:5003"
    "Media Service:5004"
    "Video AI Service:5005"
    "Audio AI Service:5006"
    "Text AI Service:5007"
    "Assessment Service:5008"
    "Coding Service:5009"
    "Logger Service:5010"
    "Notification Service:5011"
)

healthy_services=0
total_services=${#services[@]}

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if check_service "$name" "$port"; then
        ((healthy_services++))
    fi
done

echo "=============================================="
echo "📊 Health Check Summary:"
echo "   Healthy Services: $healthy_services/$total_services"

if [ $healthy_services -eq $total_services ]; then
    echo "🎉 All services are healthy and running!"
    echo ""
    echo "🌐 Service URLs:"
    echo "   API Gateway:      http://localhost:5000"
    echo "   User Service:     http://localhost:5001"
    echo "   Auth Service:     http://localhost:5002"
    echo "   Interview Service: http://localhost:5003"
    echo "   Media Service:    http://localhost:5004"
    echo "   Video AI Service: http://localhost:5005"
    echo "   Audio AI Service: http://localhost:5006"
    echo "   Text AI Service:  http://localhost:5007"
    echo "   Assessment Service: http://localhost:5008"
    echo "   Coding Service:   http://localhost:5009"
    echo "   Logger Service:   http://localhost:5010"
    echo "   Notification Service: http://localhost:5011"
    echo ""
    echo "🔧 Quick Test Commands:"
    echo "   Test API Gateway: curl http://localhost:5000/route-test"
    echo "   Test Health:      curl http://localhost:5000/health"
    echo "   View Logs:        docker-compose logs -f"
    echo "   Stop Services:    docker-compose down"
    echo ""
    echo "📚 For detailed testing, run: python test-services.py"
else
    echo "⚠️  Some services are not healthy. Check the logs:"
    echo "   docker-compose logs"
    echo ""
    echo "🔄 You can try restarting specific services:"
    echo "   docker-compose restart <service-name>"
fi

echo "=============================================="
