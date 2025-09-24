# AI Interview Platform - Makefile
# ⚠️ SAMPLE MAKEFILE - CUSTOMIZE COMMANDS FOR YOUR PROJECT

.PHONY: help build up down test clean

# Default target
help:
	@echo "Available commands:"
	@echo "  build     - Build all Docker images"
	@echo "  up        - Start all services"
	@echo "  down      - Stop all services"
	@echo "  test      - Run tests for all services"
	@echo "  clean     - Clean up Docker containers and volumes"

# Build all Docker images
build:
	docker-compose build

# Start all services
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# Run tests for all services
test:
	@echo "Running tests for all services..."
	@for service in backend/*; do \
		if [ -f "$$service/requirements.txt" ]; then \
			echo "Testing $$service..."; \
			docker-compose exec $$(basename $$service) python -m pytest tests/ || true; \
		fi; \
	done

# Clean up Docker containers and volumes
clean:
	docker-compose down -v
	docker system prune -f

# Install dependencies for development
install-dev:
	@echo "Installing development dependencies..."
	pip install -r requirements-dev.txt || echo "No dev requirements found"

# Database migrations
migrate:
	@echo "Running database migrations..."
	docker-compose exec user-service flask db upgrade
	docker-compose exec auth-service flask db upgrade
	docker-compose exec interview-service flask db upgrade
