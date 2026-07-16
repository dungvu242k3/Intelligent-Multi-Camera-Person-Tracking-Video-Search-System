"""
DB Startup Utility
==================
Shared async helper that waits for PostgreSQL to be responsive before
proceeding with service startup. Prevents crash-loops caused by race
conditions between application containers and the database container.

Usage (in FastAPI lifespan):

    from packages.shared.db_startup import wait_for_db

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await wait_for_db(settings.DATABASE_URL)
        # ... rest of startup
        yield
        # ... shutdown
"""

import asyncio
import logging
import os

logger = logging.getLogger(__name__)

MAX_RETRIES = int(os.getenv("DB_STARTUP_MAX_RETRIES", "20"))
RETRY_DELAY = float(os.getenv("DB_STARTUP_RETRY_DELAY_SECONDS", "3.0"))


async def wait_for_db(database_url: str, *, max_retries: int = MAX_RETRIES, retry_delay: float = RETRY_DELAY) -> None:
    """
    Polls the database until a connection succeeds or max_retries is exhausted.

    Args:
        database_url: SQLAlchemy async URL (postgresql+asyncpg://...).
        max_retries: Number of connection attempts before raising.
        retry_delay: Seconds to wait between retries.

    Raises:
        RuntimeError: If the database is still unreachable after max_retries.
    """
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
    except ImportError:
        logger.warning("SQLAlchemy not available; skipping DB readiness check.")
        return

    logger.info("Waiting for database to become available...")

    for attempt in range(1, max_retries + 1):
        engine = create_async_engine(database_url, pool_pre_ping=True, pool_size=1, max_overflow=0)
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database is ready after %d attempt(s).", attempt)
            return
        except Exception as exc:
            logger.warning(
                "Database not ready (attempt %d/%d): %s. Retrying in %.1fs...",
                attempt, max_retries, exc, retry_delay,
            )
            await asyncio.sleep(retry_delay)
        finally:
            await engine.dispose()

    raise RuntimeError(
        f"Database at {database_url!r} did not become ready after {max_retries} attempts. "
        "Verify DATABASE_URL and that the postgres container is running."
    )
