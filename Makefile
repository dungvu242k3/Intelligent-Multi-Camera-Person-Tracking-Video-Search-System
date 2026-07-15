# =====================================================
# Intelligent Multi-Camera Person Tracking System
# Makefile — Common Development Commands
# =====================================================

.PHONY: help dev-up dev-down dev-logs dev-restart \
        build test lint format migrate \
        proto clean

# Default target
help: ## Show this help message
	@echo "======================================================"
	@echo " Multi-Camera Person Tracking System — Makefile"
	@echo "======================================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---- Development Environment ----

dev-up: ## Start all services in dev mode
	docker compose up -d
	@echo "\n✅ Services started. Access:"
	@echo "   Frontend:    http://localhost:5173"
	@echo "   Backend API: http://localhost:8000/docs"
	@echo "   Grafana:     http://localhost:3001"
	@echo "   MinIO:       http://localhost:9001"
	@echo "   Qdrant:      http://localhost:6333/dashboard"

dev-down: ## Stop all services
	docker compose down

dev-restart: ## Restart all services
	docker compose down && docker compose up -d

dev-logs: ## Follow logs for all services
	docker compose logs -f

dev-logs-backend: ## Follow backend logs
	docker compose logs -f backend

dev-logs-ai: ## Follow AI pipeline logs
	docker compose logs -f ai-pipeline

# ---- Build ----

build: ## Build all production Docker images
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build

build-backend: ## Build backend image only
	docker build -t mcpt-backend:latest ./backend

build-frontend: ## Build frontend image only
	docker build -t mcpt-frontend:latest ./frontend

build-ai: ## Build AI pipeline image only
	docker build -t mcpt-ai-pipeline:latest -f ./ai-pipeline/Dockerfile.deepstream ./ai-pipeline

# ---- Testing ----

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing

test-frontend: ## Run frontend tests
	cd frontend && npm run test

test-ai: ## Run AI pipeline tests
	cd ai-pipeline && python -m pytest tests/ -v

# ---- Code Quality ----

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend code
	cd backend && python -m ruff check app/ tests/
	cd backend && python -m mypy app/ --ignore-missing-imports

lint-frontend: ## Lint frontend code
	cd frontend && npm run lint

format: format-backend format-frontend ## Format all code

format-backend: ## Format backend code
	cd backend && python -m ruff format app/ tests/

format-frontend: ## Format frontend code
	cd frontend && npm run format

# ---- Database ----

migrate: ## Run database migrations
	cd backend && python -m alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="add cameras table")
	cd backend && python -m alembic revision --autogenerate -m "$(MSG)"

migrate-rollback: ## Rollback last migration
	cd backend && python -m alembic downgrade -1

seed: ## Seed database with test data
	cd backend && python -m app.scripts.seed_db

# ---- Protobuf ----

proto: ## Generate protobuf code from .proto files
	python -m grpc_tools.protoc \
		-I shared/proto \
		--python_out=backend/app/generated \
		--grpc_python_out=backend/app/generated \
		--pyi_out=backend/app/generated \
		shared/proto/*.proto

# ---- Utilities ----

clean: ## Clean build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/dist backend/htmlcov backend/.coverage

gpu-status: ## Show NVIDIA GPU status
	nvidia-smi

docker-prune: ## Prune unused Docker resources
	docker system prune -af --volumes
