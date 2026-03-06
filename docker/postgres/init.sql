-- =============================================================================
-- DebtSense — PostgreSQL Initialization Script
-- =============================================================================
-- Runs automatically on first container startup via docker-entrypoint-initdb.d.
-- The POSTGRES_DB database is already created by the Docker image; this script
-- installs required extensions and applies baseline configuration.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------

-- UUID generation (used for primary keys across all tables)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cryptographic functions (used for server-side hashing and encryption)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Trigram similarity (used for fuzzy-search on debt descriptions, etc.)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ---------------------------------------------------------------------------
-- Schema
-- ---------------------------------------------------------------------------

-- Application tables live in the public schema (managed by Alembic migrations).
-- This script does NOT create tables — Alembic is the single source of truth
-- for the schema. Run `alembic upgrade head` after the database is initialized.

-- ---------------------------------------------------------------------------
-- Performance tuning for the containerized environment
-- ---------------------------------------------------------------------------

-- Allow the planner to use parallel queries
ALTER SYSTEM SET max_parallel_workers_per_gather = 2;

-- Increase work_mem for sorting/hashing (container has dedicated memory)
ALTER SYSTEM SET work_mem = '64MB';

-- Increase maintenance_work_mem for VACUUM, CREATE INDEX, etc.
ALTER SYSTEM SET maintenance_work_mem = '128MB';

-- WAL configuration for durability without excessive I/O
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;

-- Logging — log slow queries for monitoring
ALTER SYSTEM SET log_min_duration_statement = 500;  -- log queries > 500ms
ALTER SYSTEM SET log_statement = 'ddl';             -- log schema changes

-- Reload configuration
SELECT pg_reload_conf();
