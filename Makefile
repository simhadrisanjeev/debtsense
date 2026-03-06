# =============================================================================
# DebtSense Monorepo Makefile
# =============================================================================

.PHONY: help install dev build test lint clean docker-up docker-down migrate

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------

install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install backend dependencies
	cd backend && pip install -e ".[dev]"

install-frontend: ## Install frontend dependencies
	cd frontend && npm install

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

dev: ## Start all services for development
	docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d postgres redis
	@echo "Starting backend..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "Starting frontend..."
	cd frontend && npm run dev

dev-backend: ## Start backend only
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend only
	cd frontend && npm run dev

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

build: build-backend build-frontend ## Build all

build-backend: ## Build backend Docker image
	docker build -f docker/Dockerfile.backend -t debtsense-backend .

build-frontend: ## Build frontend
	cd frontend && npm run build

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	cd backend && pytest -v --cov=app --cov-report=term-missing

test-frontend: ## Run frontend tests
	cd frontend && npm test

test-integration: ## Run integration tests
	cd backend && pytest tests/integration -v

test-e2e: ## Run end-to-end tests
	cd backend && pytest tests/e2e -v

# ---------------------------------------------------------------------------
# Linting
# ---------------------------------------------------------------------------

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend
	cd backend && ruff check app/ tests/
	cd backend && mypy app/

lint-frontend: ## Lint frontend
	cd frontend && npm run lint

format: ## Format all code
	cd backend && ruff format app/ tests/
	cd frontend && npm run format

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	cd backend && alembic revision --autogenerate -m "$(MSG)"

migrate-rollback: ## Rollback last migration
	cd backend && alembic downgrade -1

db-seed: ## Seed the database
	cd backend && python -m database.seeds.run

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

docker-up: ## Start all services via Docker
	docker compose -f docker/docker-compose.yml up -d

docker-down: ## Stop all Docker services
	docker compose -f docker/docker-compose.yml down

docker-logs: ## Tail Docker logs
	docker compose -f docker/docker-compose.yml logs -f

docker-rebuild: ## Rebuild and restart Docker services
	docker compose -f docker/docker-compose.yml up -d --build

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
