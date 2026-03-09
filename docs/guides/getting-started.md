# DebtSense - Getting Started Guide

This guide walks you through setting up the DebtSense development environment from scratch.

## Prerequisites

### Required

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.11+ | Backend runtime |
| **Node.js** | 20 LTS | Frontend runtime |
| **npm** | 10+ | Frontend package manager |
| **Git** | 2.40+ | Source control |

### Optional

| Tool | Version | Purpose |
|------|---------|---------|
| **Ollama** | latest | Local LLM for AI Advisor feature |
| **Docker** | 24+ | Container runtime (production deployment) |
| **Docker Compose** | 2.20+ | Multi-container orchestration (production) |
| **Make** | 4.0+ | Task runner |

Verify your installations:

```bash
git --version
python --version
node --version
npm --version
```

## 1. Clone the Repository

```bash
git clone https://github.com/your-org/debtsense.git
cd debtsense
```

## 2. Backend Setup

### Install dependencies

```bash
cd backend
pip install -e ".[dev]"
```

### Environment configuration

The `.env` file in `backend/` is pre-configured for local development with SQLite:

```env
# Application
APP_NAME=DebtSense
APP_ENV=development
APP_DEBUG=true

# Database (SQLite for local dev - no PostgreSQL required)
USE_SQLITE=true

# JWT (use any random string for local dev)
JWT_SECRET_KEY=change-this-to-a-random-secret-key-in-production

# LLM - AI Advisor (optional - uses local Ollama by default)
LLM_PROVIDER=local
LLM_MODEL=llama3.1:8b
LLM_MAX_TOKENS=1024

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

Key settings:
- **`USE_SQLITE=true`** — Uses a local `debtsense_dev.db` SQLite file. No PostgreSQL installation needed.
- **`APP_DEBUG=true`** — Enables Swagger/ReDoc API docs at `/api/docs` and `/api/redoc`.
- **`LLM_PROVIDER=local`** — Uses a local Ollama instance for the AI Advisor. Set to `openai` or `anthropic` for cloud providers (requires `LLM_API_KEY`).

### Start the backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On first start, the SQLite database is auto-created with all tables. No migrations needed for local dev.

Verify the backend is running:
- **Health check**: http://localhost:8000/health
- **Swagger docs**: http://localhost:8000/api/docs
- **ReDoc docs**: http://localhost:8000/api/redoc

## 3. Frontend Setup

### Install dependencies

```bash
cd frontend
npm install
```

### Environment configuration

The frontend needs a `.env.local` file in `frontend/` (should already exist):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Start the frontend

```bash
cd frontend
npm run dev
```

Access the application at http://localhost:3000.

## 4. AI Advisor Setup (Optional)

The AI Advisor feature requires an LLM. Two options:

### Option A: Local LLM with Ollama (default)

1. Install [Ollama](https://ollama.ai)
2. Pull the model:
   ```bash
   ollama pull llama3.1:8b
   ```
3. Ensure Ollama is running (default at `http://localhost:11434`)
4. The backend `.env` is already configured for this:
   ```env
   LLM_PROVIDER=local
   LLM_MODEL=llama3.1:8b
   ```

### Option B: Cloud LLM (OpenAI / Anthropic)

Update `backend/.env`:
```env
LLM_PROVIDER=openai          # or "anthropic"
LLM_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4              # or "claude-3-sonnet-20240229"
LLM_MAX_TOKENS=4096
```

Without a valid LLM configuration, the AI Advisor endpoints return instant fallback responses instead of hanging.

## 5. Using Make (Optional)

If you have `make` installed, the Makefile provides shortcuts:

```bash
make install          # Install all dependencies (backend + frontend)
make dev-backend      # Start backend with hot reload
make dev-frontend     # Start frontend dev server
make test-backend     # Run backend tests with coverage
make test-frontend    # Run frontend tests
make lint             # Run all linters (ruff, mypy, eslint, tsc)
make format           # Format all code (ruff, prettier)
make clean            # Remove build artifacts
```

Run `make help` to see all available commands.

## 6. Run with Docker (Production-like)

For a full production-like stack with PostgreSQL, Redis, Celery, and Nginx:

### Start all services

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d
```

### Run database migrations

```bash
cd backend && alembic upgrade head
```

### Services

| Service | Port | Purpose |
|---------|------|---------|
| `debtsense-backend` | 8000 | FastAPI application |
| `debtsense-frontend` | 3000 | Next.js application |
| `debtsense-postgres` | 5432 | PostgreSQL 16 database |
| `debtsense-redis` | 6379 | Redis cache / message broker |
| `debtsense-celery-worker` | — | Background task processing |
| `debtsense-nginx` | 80 | Reverse proxy (production only) |

### Stop all services

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml down
```

### Production environment variables

For production, set these required variables (no defaults):

```env
USE_SQLITE=false
POSTGRES_HOST=your-db-host
POSTGRES_PORT=5432
POSTGRES_DB=debtsense
POSTGRES_USER=debtsense_user
POSTGRES_PASSWORD=<strong-password>
JWT_SECRET_KEY=<random-secret>
ENCRYPTION_KEY=<32-byte-key>
```

## 7. Running Tests

### Backend

```bash
cd backend
pytest -v --cov=app --cov-report=term-missing
```

The test suite includes unit tests for core business logic (e.g., income allocation month calculations).

### Frontend

```bash
cd frontend
npm test
```

### Type checking

```bash
# Backend
cd backend && mypy app/

# Frontend
cd frontend && npx tsc --noEmit
```

## 8. Project Structure

```
debtsense/
  backend/                    # FastAPI application
    app/
      core/                   # Config, database, security, middleware, router
      modules/
        auth/                 # Registration, login, JWT tokens
        users/                # User profile management
        debts/                # Debt CRUD, payment overrides
        income/               # Income entries with allocation month logic
        expenses/             # Expense tracking
        financial_engine/     # Payoff strategies (avalanche, snowball, hybrid)
        simulation_engine/    # What-if scenario simulations
        ai_advisor/           # LLM-powered financial advice
        analytics/            # Dashboard stats, income summaries
        notifications/        # User notifications
    tests/                    # Backend test suite
    pyproject.toml            # Python dependencies and tool config
    alembic.ini               # Database migration config
    .env                      # Environment variables (local dev)

  frontend/                   # Next.js 14 application (App Router)
    src/
      app/                    # Pages and layouts
        dashboard/            # Dashboard, debts, income, expenses,
                              # strategies, advisor, settings
        login/                # Login page
        register/             # Registration page
      components/             # Reusable UI components
        layout/               # Header, Sidebar
        ui/                   # Button, Card, Input, etc.
      hooks/                  # Custom React hooks (useDebts, useIncome, etc.)
      lib/                    # API client, utilities
      providers/              # React context providers
      types/                  # TypeScript type definitions
    package.json
    tailwind.config.ts
    tsconfig.json
    .env.local                # Frontend environment variables

  services/                   # Shared services
    cache/                    # Redis client
    queue/                    # Celery task queue
    storage/                  # Encryption utilities
    llm_gateway/              # LLM provider abstraction
    interest_calculator.py    # Interest calculation utilities

  database/                   # Database utilities
    migrations/               # Alembic migrations
    seeds/                    # Seed data scripts

  docker/                     # Docker configuration
  infrastructure/             # Terraform, Kubernetes, monitoring
  docs/                       # Documentation
  scripts/                    # Utility scripts
  Makefile                    # Task runner
```

## 9. API Endpoints

All API routes are prefixed with `/api/v1`. Key endpoint groups:

| Prefix | Description |
|--------|-------------|
| `/api/v1/auth` | Register, login, token refresh |
| `/api/v1/users` | User profile |
| `/api/v1/debts` | Debt CRUD, payment overrides |
| `/api/v1/income` | Income entries, allocation by month, monthly totals |
| `/api/v1/expenses` | Expense tracking |
| `/api/v1/financial-engine` | Payoff strategy calculations |
| `/api/v1/simulations` | What-if scenario analysis |
| `/api/v1/ai-advisor` | LLM-powered financial advice |
| `/api/v1/analytics` | Dashboard stats, income summaries |
| `/api/v1/notifications` | User notifications |

Interactive API docs are available at `/api/docs` (Swagger) and `/api/redoc` when `APP_DEBUG=true`.

## 10. Key Concepts

### Income Allocation Month

Income entries support an **allocation month** concept. When you receive a salary on March 31, you can allocate it to April's budget:

- **Same Month** (`same_month`): Income is allocated to the month it was received.
- **Next Month** (`next_month`): Income is allocated to the following month (e.g., salary on March 31 appears in April's budget).

The `allocation_month` field is computed server-side based on `date_received` and `income_allocation_type`.

### Debt Payoff Strategies

The financial engine supports multiple payoff strategies:
- **Avalanche**: Pay highest interest rate first (saves the most money)
- **Snowball**: Pay smallest balance first (psychological wins)
- **Hybrid**: Balanced approach

### Payment Overrides

Monthly payment amounts can be overridden for specific months on each debt, allowing flexible planning around irregular expenses.

## 11. Common Issues

### Port already in use

```bash
# Find the process using the port (Linux/macOS)
lsof -i :8000
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Backend not picking up `.env` changes

The settings are cached with `@lru_cache`. Restart the backend process after changing `.env`:

```bash
# Kill existing Python/uvicorn processes and restart
```

### SQLite database issues

If the SQLite database gets into a bad state, delete it and restart:

```bash
cd backend
rm debtsense_dev.db
# Restart uvicorn - tables are auto-created on startup
```

### TypeScript errors

Run the type checker to catch issues:

```bash
cd frontend
npx tsc --noEmit
```

### AI Advisor not responding

- If using local Ollama, ensure it's running: `curl http://localhost:11434/api/tags`
- If using a cloud provider, verify `LLM_API_KEY` is set to a valid key (not a placeholder like `your-llm-api-key`)
- Without a valid LLM, the advisor returns fallback responses instantly

### CORS errors in browser

Ensure `CORS_ORIGINS` in `backend/.env` includes your frontend URL:

```env
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

## 12. Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript 5, Tailwind CSS 3 |
| **Backend** | FastAPI, Python 3.11, Pydantic v2 |
| **Database** | SQLite (dev) / PostgreSQL 16 (prod), SQLAlchemy 2.0 (async) |
| **State** | Zustand, React Query |
| **Auth** | JWT (access + refresh tokens), bcrypt |
| **AI** | Ollama (local) / OpenAI / Anthropic |
| **Icons** | Lucide React |
| **Charts** | Recharts |
| **HTTP Client** | Axios (frontend), httpx (backend) |
| **Testing** | pytest (backend), Jest (frontend) |
