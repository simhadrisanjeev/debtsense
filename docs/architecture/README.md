# DebtSense Architecture Overview

## System Diagram

```
                                    Internet
                                       |
                                  [CloudFlare]
                                       |
                              [AWS ALB / Nginx]
                              /                \
                     [Next.js Frontend]    [FastAPI Backend]
                        (Port 3000)          (Port 8000)
                                                |
                          +---------+-----------+-----------+
                          |         |                       |
                     [PostgreSQL] [Redis]            [Celery Workers]
                      (Port 5432) (Port 6379)              |
                          |         |                   [Redis]
                          |         |                  (Broker)
                          |         |
                    [Primary + Read Replicas]   [Cache + Rate Limits]
```

## Tech Stack

### Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | FastAPI (Python 3.11) | Async REST API with OpenAPI docs |
| ORM | SQLAlchemy 2.0 (async) | Database access with type-safe models |
| Migrations | Alembic | Schema versioning and migrations |
| Validation | Pydantic v2 | Request/response validation and serialization |
| Auth | python-jose + passlib | JWT tokens and password hashing (bcrypt) |
| Task Queue | Celery 5.x | Background job processing |
| Logging | structlog | Structured JSON logging |
| Error Tracking | Sentry | Production error monitoring |

### Frontend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | Next.js 14 | Server-side rendering and routing |
| Language | TypeScript 5.x | Type-safe JavaScript |
| State | Zustand | Lightweight client state management |
| Server State | TanStack Query v5 | API data fetching, caching, sync |
| Forms | React Hook Form + Zod | Form handling with schema validation |
| Styling | Tailwind CSS | Utility-first CSS framework |
| Charts | Recharts | Financial data visualization |

### Infrastructure
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Database | PostgreSQL 16 (Aurora) | Primary data store |
| Cache | Redis 7 (ElastiCache) | Caching, sessions, rate limiting, Celery broker |
| Containers | Docker + ECS Fargate | Serverless container orchestration |
| IaC | Terraform | Infrastructure provisioning |
| CI/CD | GitHub Actions | Automated testing and deployment |
| Reverse Proxy | Nginx | Load balancing, TLS termination, rate limiting |
| Monitoring | Prometheus + Grafana | Metrics collection and dashboards |
| DNS/CDN | CloudFlare | DNS, CDN, DDoS protection |

## Module Dependency Graph

```
app/
 |-- core/
 |    |-- config.py          # Settings (env vars) - depended on by everything
 |    |-- database.py        # SQLAlchemy engine and session
 |    |-- security.py        # JWT and password utilities
 |    |-- base_model.py      # Base SQLAlchemy model with common fields
 |    |-- dependencies.py    # FastAPI dependency injection
 |    |-- exceptions.py      # Custom exception hierarchy
 |    |-- logging.py         # Structured logging setup
 |    +-- router.py          # Central router mounting all modules
 |
 |-- middleware/
 |    |-- rate_limiter.py    # Redis-backed rate limiting
 |    +-- request_id.py     # X-Request-ID propagation
 |
 |-- modules/
 |    |-- auth/              # Registration, login, JWT management
 |    |    +-- depends on: core/security, users/
 |    |
 |    |-- users/             # User profiles and preferences
 |    |    +-- depends on: core/base_model
 |    |
 |    |-- debts/             # Debt CRUD (credit cards, loans, etc.)
 |    |    +-- depends on: core/base_model, auth/
 |    |
 |    |-- income/            # Income source management
 |    |    +-- depends on: core/base_model, auth/
 |    |
 |    |-- expenses/          # Expense tracking
 |    |    +-- depends on: core/base_model, auth/
 |    |
 |    |-- financial_engine/  # Payoff calculators (avalanche, snowball)
 |    |    +-- depends on: debts/, income/
 |    |
 |    |-- simulation_engine/ # What-if scenario modeling
 |    |    +-- depends on: financial_engine/, debts/
 |    |
 |    |-- ai_advisor/        # LLM-powered financial advice
 |    |    +-- depends on: debts/, income/, expenses/, financial_engine/
 |    |
 |    |-- analytics/         # Dashboards and trend analysis
 |    |    +-- depends on: debts/, income/, expenses/
 |    |
 |    +-- notifications/     # User notification system
 |         +-- depends on: users/
 |
 +-- services/ (top-level shared services)
      |-- cache/             # Redis client wrapper
      |-- queue/             # Celery app and task definitions
      |-- storage/           # Encryption utilities
      +-- llm_gateway/       # LLM provider abstraction (OpenAI, etc.)
```

## Scaling Strategy

### Horizontal Backend Scaling
- **ECS Fargate auto-scaling**: Backend services scale from 3 to 10 instances based on CPU utilization (target: 70%).
- **Stateless design**: No server-side session state. All state is in PostgreSQL or Redis, allowing any instance to handle any request.
- **Connection pooling**: SQLAlchemy async connection pool per instance. PgBouncer can be introduced as an intermediate pooler if connection limits become a concern.

### Database Scaling
- **Aurora PostgreSQL** with read replicas: Write operations go to the primary instance; read-heavy queries (analytics, dashboards) are routed to read replicas.
- **Connection limits**: Each backend instance maintains a pool of 10-20 connections. With 10 instances, this stays well within Aurora's connection limits.
- **Indexing strategy**: B-tree indexes on foreign keys and query filters. GIN indexes with pg_trgm for text search on debt descriptions.
- **Partitioning**: The analytics and notifications tables can be time-partitioned when data volume grows.

### Redis Scaling
- **ElastiCache cluster mode**: Start with a single-node setup; scale to a Redis cluster with sharding when cache hit ratios or throughput demands increase.
- **Usage separation**: Cache entries use TTLs and `allkeys-lru` eviction. Celery task results have explicit expiry (24 hours). Rate limit counters use Redis INCR with TTL.
- **Failover**: Multi-AZ with automatic failover enabled in production.

### Celery Worker Scaling
- **Queue-based scaling**: Separate queues for `default`, `ai_tasks`, and `financial_tasks`. Workers can be scaled independently per queue based on backlog depth.
- **Concurrency**: Each worker process handles 4 concurrent tasks. Scale horizontally by adding more ECS tasks running the Celery worker command.
- **Task timeouts**: 5-minute soft limit and 6-minute hard kill to prevent runaway tasks.

### Frontend Scaling
- **Static generation**: Next.js static pages served from CDN (CloudFlare). Only dynamic pages hit the Next.js server.
- **Standalone output**: Minimal Node.js server footprint. 2-4 instances behind the ALB handle SSR requests.

## Security Measures

### Authentication and Authorization
- **JWT tokens**: Short-lived access tokens (30 minutes) with long-lived refresh tokens (7 days). Tokens are signed with HS256.
- **Password hashing**: bcrypt with automatic salt generation via passlib.
- **Role-based access**: Users can only access their own data. All endpoints verify resource ownership.

### Encryption
- **At rest**: Aurora PostgreSQL storage encrypted with AWS KMS. Redis ElastiCache at-rest encryption enabled. S3 buckets (if used) encrypted with SSE-S3.
- **In transit**: TLS 1.3 enforced at the ALB. Internal services communicate over the VPC private network. Redis transit encryption enabled.
- **Application-level**: Sensitive financial data (account numbers, SSNs if collected) encrypted at the application layer using the `cryptography` library with Fernet symmetric encryption before storage.

### Rate Limiting
- **Nginx layer**: Global rate limits (30 req/s general, 5 req/s for auth endpoints) at the reverse proxy level.
- **Application layer**: Per-user rate limiting via Redis-backed middleware (60 req/min general, 10 req/min for AI advisor).
- **Celery tasks**: Default rate limit of 60 tasks/minute per task type, configurable per task.

### Network Security
- **VPC isolation**: All backend services (ECS, RDS, Redis) run in private subnets with no public IPs. Internet access is via NAT Gateway.
- **Security groups**: Least-privilege access. RDS only accepts connections from ECS tasks. Redis only accepts connections from ECS tasks. ALB accepts public HTTP/HTTPS traffic.
- **WAF**: AWS WAF (or CloudFlare) rules block common attack patterns (SQL injection, XSS, etc.).

### Secrets Management
- **AWS SSM Parameter Store**: Database credentials, JWT secrets, and encryption keys stored as SecureString parameters. Injected into ECS tasks at runtime.
- **No secrets in code**: All secrets are loaded from environment variables via pydantic-settings. Default values in config.py are clearly marked as development-only placeholders.

### Logging and Monitoring
- **Structured logging**: All logs are JSON-formatted with request IDs for traceability.
- **Audit trail**: Authentication events (login, logout, password changes) are logged with timestamps and IP addresses.
- **Alerting**: Prometheus alerting rules for error rate spikes, latency degradation, and resource exhaustion.
