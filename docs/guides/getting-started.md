# DebtSense - Getting Started Guide

This guide walks you through setting up the DebtSense development environment from scratch.

## Prerequisites

Ensure the following tools are installed on your machine:

| Tool | Version | Purpose |
|------|---------|---------|
| **Git** | 2.40+ | Source control |
| **Python** | 3.11+ | Backend runtime |
| **Node.js** | 20 LTS | Frontend runtime |
| **npm** | 10+ | Frontend package manager |
| **Docker** | 24+ | Container runtime |
| **Docker Compose** | 2.20+ | Multi-container orchestration |
| **Make** | 4.0+ | Task runner (optional, but recommended) |

Verify your installations:

```bash
git --version
python --version
node --version
npm --version
docker --version
docker compose version
```

## 1. Clone the Repository

```bash
git clone https://github.com/your-org/debtsense.git
cd debtsense
```

## 2. Environment Configuration

Copy the example environment file and fill in your local values:

```bash
cp .env.example .env
```

The minimal `.env` for local development:

```env
# Application
APP_ENV=development
APP_DEBUG=true

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=debtsense_dev
POSTGRES_USER=debtsense_user
POSTGRES_PASSWORD=devpassword

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT (use any random string for local dev)
JWT_SECRET_KEY=dev-secret-key-not-for-production

# Encryption (must be exactly 32 bytes for Fernet)
ENCRYPTION_KEY=dev-32-byte-encryption-key-!!!!

# LLM (optional - AI advisor features will be disabled without this)
LLM_API_KEY=
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
```

## 3. Run with Docker (Recommended)

The fastest way to get the full stack running.

### Start all services

```bash
# Start infrastructure (Postgres + Redis) and application services
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d
```

Or using Make:

```bash
make docker-up
```

### Verify services are running

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml ps
```

You should see the following services running:
- `debtsense-backend` on port **8000**
- `debtsense-frontend` on port **3000**
- `debtsense-postgres` on port **5432**
- `debtsense-redis` on port **6379**
- `debtsense-celery-worker`

### Run database migrations

```bash
cd backend && alembic upgrade head
```

Or using Make:

```bash
make migrate
```

### Seed the database (optional)

```bash
make db-seed
```

### Access the application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/v1
- **API Documentation (Swagger)**: http://localhost:8000/api/docs
- **API Documentation (ReDoc)**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

### View logs

```bash
make docker-logs
```

### Stop all services

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml down
```

Or:

```bash
make docker-down
```

## 4. Run Locally (Without Docker for Application Code)

If you prefer running the application code natively (while using Docker for Postgres and Redis):

### Start infrastructure services only

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d postgres redis
```

### Install backend dependencies

```bash
cd backend
pip install -e ".[dev]"
```

Or:

```bash
make install-backend
```

### Install frontend dependencies

```bash
cd frontend
npm install
```

Or:

```bash
make install-frontend
```

### Run database migrations

```bash
cd backend
alembic upgrade head
```

### Start the backend (with hot reload)

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or:

```bash
make dev-backend
```

### Start the frontend (in a separate terminal)

```bash
cd frontend
npm run dev
```

Or:

```bash
make dev-frontend
```

### Start a Celery worker (in a separate terminal, for background tasks)

```bash
cd backend
celery -A services.queue.celery_app worker --loglevel=debug --concurrency=2
```

## 5. Run Tests

### Backend tests

```bash
cd backend
pytest -v --cov=app --cov-report=term-missing
```

Or:

```bash
make test-backend
```

### Frontend tests

```bash
cd frontend
npm test
```

Or:

```bash
make test-frontend
```

### Run all tests

```bash
make test
```

## 6. Linting and Formatting

### Backend

```bash
# Lint
cd backend && ruff check app/ tests/

# Format
cd backend && ruff format app/ tests/

# Type check
cd backend && mypy app/
```

Or:

```bash
make lint-backend
make format
```

### Frontend

```bash
cd frontend && npm run lint
cd frontend && npm run format
```

Or:

```bash
make lint-frontend
```

## 7. Project Structure

```
debtsense/
  backend/             # FastAPI application
    app/
      core/            # Config, database, security, middleware
      modules/         # Feature modules (auth, debts, income, etc.)
    tests/             # Backend test suite
    pyproject.toml     # Python dependencies and tool config
    alembic.ini        # Database migration config

  frontend/            # Next.js application
    package.json       # Node.js dependencies

  services/            # Shared services
    cache/             # Redis client
    queue/             # Celery task queue
    storage/           # Encryption utilities
    llm_gateway/       # LLM provider abstraction

  database/            # Database utilities
    migrations/        # Alembic migrations
    seeds/             # Seed data scripts

  docker/              # Docker configuration
    Dockerfile.backend
    Dockerfile.frontend
    docker-compose.yml
    docker-compose.dev.yml
    nginx/             # Reverse proxy config
    postgres/          # DB initialization
    redis/             # Redis config

  infrastructure/      # Infrastructure as Code
    terraform/         # AWS provisioning
    k8s/               # Kubernetes manifests
    monitoring/        # Prometheus + Grafana

  docs/                # Documentation
  scripts/             # Utility scripts
  Makefile             # Task runner
```

## 8. Common Issues

### Port already in use

If port 8000 or 3000 is occupied:

```bash
# Find the process using the port
lsof -i :8000
# Kill it
kill -9 <PID>
```

Or change the port in `.env`:

```env
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

### Database connection refused

Ensure PostgreSQL is running:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml ps postgres
```

Check logs if it failed to start:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml logs postgres
```

### Redis connection error

Ensure Redis is running and accessible:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml ps redis
redis-cli -h localhost -p 6379 ping
```

### Migration errors

If migrations fail, check whether the database schema is out of sync:

```bash
cd backend
alembic current    # Show current revision
alembic history    # Show migration history
alembic heads      # Show latest revision
```

To reset the database in development:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml down -v
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d postgres redis
cd backend && alembic upgrade head
```

## 9. Useful Make Commands

Run `make help` to see all available commands:

```
build                Build all
build-backend        Build backend Docker image
build-frontend       Build frontend
clean                Clean build artifacts
dev                  Start all services for development
dev-backend          Start backend only
dev-frontend         Start frontend only
docker-down          Stop all Docker services
docker-logs          Tail Docker logs
docker-rebuild       Rebuild and restart Docker services
docker-up            Start all services via Docker
format               Format all code
install              Install all dependencies
install-backend      Install backend dependencies
install-frontend     Install frontend dependencies
lint                 Run all linters
lint-backend         Lint backend
lint-frontend        Lint frontend
migrate              Run database migrations
migrate-create       Create a new migration
migrate-rollback     Rollback last migration
test                 Run all tests
test-backend         Run backend tests
test-frontend        Run frontend tests
```
