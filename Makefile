# SkillScreen Backend Services Makefile
# Professional build and deployment automation

.PHONY: help build start stop restart logs test clean health status

# Default target
.DEFAULT_GOAL := help

# Configuration
COMPOSE_FILE := docker-compose.yml
PROJECT_NAME := skillscreen-backend
ENVIRONMENT := development

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)SkillScreen Backend Services$(NC)"
	@echo "=========================="
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Examples:$(NC)"
	@echo "  make start          # Start all services"
	@echo "  make test           # Run connectivity tests"
	@echo "  make logs           # View service logs"
	@echo "  make stop           # Stop all services"

build: ## Build all Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose -f $(COMPOSE_FILE) build

start: ## Start all services
	@echo "$(BLUE)Starting SkillScreen Backend Services...$(NC)"
	@echo "$(YELLOW)Environment: $(ENVIRONMENT)$(NC)"
	@echo "=========================="
	@$(MAKE) _check-docker
	@$(MAKE) _cleanup
	@echo "$(BLUE)Building and starting services...$(NC)"
	docker-compose -f $(COMPOSE_FILE) up --build -d
	@echo "$(GREEN)✅ Services started successfully$(NC)"
	@echo "$(BLUE)Waiting for services to be ready...$(NC)"
	@sleep 30
	@$(MAKE) health

stop: ## Stop all services
	@echo "$(BLUE)Stopping all services...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down
	@echo "$(GREEN)✅ Services stopped$(NC)"

restart: ## Restart all services
	@echo "$(BLUE)Restarting all services...$(NC)"
	@$(MAKE) stop
	@$(MAKE) start

logs: ## View logs for all services
	@echo "$(BLUE)Viewing service logs...$(NC)"
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-service: ## View logs for specific service (usage: make logs-service SERVICE=api-gateway)
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)Error: SERVICE parameter required$(NC)"; \
		echo "Usage: make logs-service SERVICE=api-gateway"; \
		exit 1; \
	fi
	@echo "$(BLUE)Viewing logs for $(SERVICE)...$(NC)"
	docker-compose -f $(COMPOSE_FILE) logs -f $(SERVICE)

test: ## Run connectivity tests
	@echo "$(BLUE)Running connectivity tests...$(NC)"
	@$(MAKE) _check-python
	python test-services.py

health: ## Check health of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo "=========================="
	@$(MAKE) _check-service api-gateway 5000
	@$(MAKE) _check-service user-service 5001
	@$(MAKE) _check-service auth-service 5002
	@$(MAKE) _check-service interview-service 5003
	@$(MAKE) _check-service media-service 5004
	@$(MAKE) _check-service video-ai-service 5005
	@$(MAKE) _check-service audio-ai-service 5006
	@$(MAKE) _check-service text-ai-service 5007
	@$(MAKE) _check-service assessment-service 5008
	@$(MAKE) _check-service coding-service 5009
	@$(MAKE) _check-service logger-service 5010
	@$(MAKE) _check-service notification-service 5011
	@echo "=========================="
	@echo "$(GREEN)Health check completed$(NC)"

status: ## Show status of all containers
	@echo "$(BLUE)Container Status:$(NC)"
	docker-compose -f $(COMPOSE_FILE) ps

clean: ## Clean up containers, networks, and volumes
	@echo "$(BLUE)Cleaning up...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker system prune -f
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

clean-images: ## Remove all Docker images
	@echo "$(BLUE)Removing Docker images...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down --rmi all
	@echo "$(GREEN)✅ Images removed$(NC)"

dev: ## Start services in development mode with live logs
	@echo "$(BLUE)Starting in development mode...$(NC)"
	docker-compose -f $(COMPOSE_FILE) up --build

prod: ## Start services in production mode
	@echo "$(BLUE)Starting in production mode...$(NC)"
	@$(MAKE) _check-env-file
	ENVIRONMENT=production docker-compose -f $(COMPOSE_FILE) up --build -d

# Internal targets
_check-docker:
	@if ! docker info > /dev/null 2>&1; then \
		echo "$(RED)❌ Docker is not running. Please start Docker first.$(NC)"; \
		exit 1; \
	fi
	@if ! docker-compose --version > /dev/null 2>&1; then \
		echo "$(RED)❌ Docker Compose is not available. Please install Docker Compose.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Docker checks passed$(NC)"

_check-python:
	@if ! python --version > /dev/null 2>&1; then \
		echo "$(RED)❌ Python is not available. Please install Python 3.7+.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Python check passed$(NC)"

_check-env-file:
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)⚠️  .env file not found. Creating from template...$(NC)"; \
		cp .env.example .env 2>/dev/null || echo "JWT_SECRET=your-secret-key-change-in-production" > .env; \
	fi

_cleanup:
	@echo "$(BLUE)Cleaning up existing containers...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down --remove-orphans > /dev/null 2>&1 || true

_check-service:
	@if curl -s -f http://localhost:$(2)/health > /dev/null 2>&1; then \
		echo "$(GREEN)✅ $(1) (port $(2)) - Healthy$(NC)"; \
	else \
		echo "$(RED)❌ $(1) (port $(2)) - Unhealthy$(NC)"; \
	fi

# Service-specific targets
restart-service: ## Restart specific service (usage: make restart-service SERVICE=api-gateway)
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)Error: SERVICE parameter required$(NC)"; \
		echo "Usage: make restart-service SERVICE=api-gateway"; \
		exit 1; \
	fi
	@echo "$(BLUE)Restarting $(SERVICE)...$(NC)"
	docker-compose -f $(COMPOSE_FILE) restart $(SERVICE)
	@echo "$(GREEN)✅ $(SERVICE) restarted$(NC)"

shell-service: ## Get shell access to specific service (usage: make shell-service SERVICE=api-gateway)
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)Error: SERVICE parameter required$(NC)"; \
		echo "Usage: make shell-service SERVICE=api-gateway"; \
		exit 1; \
	fi
	@echo "$(BLUE)Opening shell for $(SERVICE)...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec $(SERVICE) /bin/bash

# Database targets
db-shell: ## Access PostgreSQL database shell
	@echo "$(BLUE)Opening database shell...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec postgres psql -U postgres -d ai_interview_platform_dev

db-reset: ## Reset database (WARNING: This will delete all data)
	@echo "$(RED)⚠️  WARNING: This will delete all database data!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	@echo "$(BLUE)Resetting database...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down -v
	docker volume rm skillscreen-backend_postgres_dev_data 2>/dev/null || true
	@echo "$(GREEN)✅ Database reset completed$(NC)"

# Monitoring targets
monitor: ## Monitor resource usage
	@echo "$(BLUE)Monitoring resource usage...$(NC)"
	docker stats

# Backup targets
backup-db: ## Backup database
	@echo "$(BLUE)Creating database backup...$(NC)"
	@mkdir -p backups
	docker-compose -f $(COMPOSE_FILE) exec postgres pg_dump -U postgres ai_interview_platform_dev > backups/db_backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Database backup created$(NC)"

# Security targets
security-scan: ## Run security scan on images
	@echo "$(BLUE)Running security scan...$(NC)"
	@if command -v trivy > /dev/null 2>&1; then \
		trivy image --severity HIGH,CRITICAL skillscreen-backend-api-gateway; \
	else \
		echo "$(YELLOW)⚠️  Trivy not installed. Install it for security scanning.$(NC)"; \
	fi