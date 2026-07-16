# =====================================================
# Intelligent Multi-Camera Person Tracking System
# Makefile — Common Development Commands (Monorepo)
# =====================================================

.PHONY: help dev-up dev-down dev-logs dev-restart \
        build test lint format db-migrate db-migration db-rollback \
        clean gpu-status

# Default target
help: ## Show this help message
	@echo "======================================================"
	@echo " Multi-Camera Person Tracking System — Makefile"
	@echo "======================================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---- Development Environment ----

dev-up: ## Start all services in docker compose dev mode
	docker compose up -d
	@echo "\n✅ Services started. Access:"
	@echo "   Frontend Web:      http://localhost:5173"
	@echo "   API Gateway:       http://localhost:8000"
	@echo "   Analytics API:     http://localhost:8001/docs"
	@echo "   Camera Service:    http://localhost:8002/docs"
	@echo "   Search Service:    http://localhost:8003/docs"
	@echo "   MinIO Console:     http://localhost:9001"
	@echo "   Grafana Metrics:   http://localhost:3001"
	@echo "   Qdrant Dashboard:  http://localhost:6333/dashboard"

dev-down: ## Stop all docker compose services
	docker compose down

dev-restart: ## Restart all services
	docker compose down && docker compose up -d

dev-logs: ## Follow logs for all services
	docker compose logs -f

dev-logs-ai: ## Follow logs for the AI pipeline service
	docker compose logs -f ai-service

dev-logs-analytics: ## Follow logs for the Analytics service
	docker compose logs -f analytics-service

dev-logs-camera: ## Follow logs for the Camera service
	docker compose logs -f camera-service

# ---- Build ----

build: ## Build all monorepo Docker images
	docker compose build

# ---- Testing ----

test: ## Run unit tests across all microservices
	@echo "Running tests in Python backend services..."
	python -m pytest -o pythonpath=src apps/analytics-service/tests/
	python -m pytest -o pythonpath=src apps/camera-service/tests/

test-ai: ## Run AI pipeline GStreamer tests
	python -m pytest -o pythonpath=apps/ai-service/src apps/ai-service/tests/

test-web: ## Run frontend React unit tests
	cd apps/web && npm run test

# ---- Code Quality ----

lint: ## Lint check python backend and react codebases
	flake8 apps/ packages/
	cd apps/web && npm run lint

format: ## Auto-format python and React frontend codebases
	black apps/ packages/
	cd apps/web && npm run format

# ---- Database Migrations ----

db-migrate: ## Run alembic database migrations to upgrade to head
	cd database/postgres/migrations && alembic upgrade head

db-migration: ## Create a new migration revision (usage: make db-migration MSG="create cameras table")
	cd database/postgres/migrations && alembic revision --autogenerate -m "$(MSG)"

db-rollback: ## Rollback the last database migration revision
	cd database/postgres/migrations && alembic downgrade -1

# ---- Utilities ----

clean: ## Clean Python caches and Node build assets
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true

gpu-status: ## Show NVIDIA GPU status metrics
	nvidia-smi
