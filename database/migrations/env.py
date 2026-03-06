"""
Alembic migration environment — async edition.

This module is executed by Alembic when running ``alembic upgrade``,
``alembic downgrade``, ``alembic revision --autogenerate``, etc.

Key design decisions:

* **Async engine** — uses ``asyncpg`` via SQLAlchemy's async API so
  migrations can run against the same connection pool configuration as
  the application.
* **Autogenerate-aware** — all ORM models are imported so Alembic can
  diff the metadata against the live schema.
* **Configurable from settings** — the database URL is pulled from
  ``app.core.config.settings`` rather than hard-coded in ``alembic.ini``.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings

# ---------------------------------------------------------------------------
# Import the declarative Base so its metadata contains all tables.
# ---------------------------------------------------------------------------
from app.core.base_model import Base  # noqa: F401

# Import every model module so their table definitions are registered
# on ``Base.metadata`` before autogenerate runs.
import app.modules.users.models  # noqa: F401
import app.modules.auth.models  # noqa: F401
import app.modules.debts.models  # noqa: F401
import app.modules.income.models  # noqa: F401
import app.modules.expenses.models  # noqa: F401

# ---------------------------------------------------------------------------
# Alembic Config object — provides access to values in alembic.ini
# ---------------------------------------------------------------------------

config = context.config

# Interpret the alembic.ini [loggers] section for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override the sqlalchemy.url from settings so we have a single source
# of truth for the database connection string.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Target metadata for autogenerate support.
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline mode — emit SQL to stdout instead of connecting to the database
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well.  By skipping the Engine
    creation we don't even need a DBAPI to be available.

    Calls to ``context.execute()`` here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online (async) mode — connect to the database and apply migrations
# ---------------------------------------------------------------------------

def do_run_migrations(connection: Connection) -> None:
    """Configure the Alembic context with a live connection and run."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations within a connection."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
