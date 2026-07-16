import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://mcpt_user:change_me_in_production@localhost:5432/mcpt_db"
)

# Create async engine optimized with pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider yielding async SQLAlchemy session handles."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
