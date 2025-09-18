"""Database connection and session management"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine
)
from sqlalchemy.pool import NullPool
from structlog import get_logger

from ..config import settings

logger = get_logger()


class DatabaseManager:
    """Manages database connections and sessions"""

    def __init__(self):
        """Initialize database manager"""
        self.engine: Optional[AsyncEngine] = None
        self.async_session: Optional[async_sessionmaker] = None
        self._initialized = False

    async def initialize(self):
        """Initialize database connection"""
        if self._initialized:
            return

        try:
            # Create async engine with connection pooling
            self.engine = create_async_engine(
                settings.database.url.replace("postgresql://", "postgresql+asyncpg://"),
                echo=settings.database.echo if hasattr(settings.database, 'echo') else False,
                pool_size=settings.database.pool_size if hasattr(settings.database, 'pool_size') else 20,
                max_overflow=settings.database.max_overflow if hasattr(settings.database, 'max_overflow') else 40,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,  # Recycle connections after 1 hour
            )

            # Create session factory
            self.async_session = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False
            )

            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")

            self._initialized = True
            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise

    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Database connections closed")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager"""
        if not self._initialized:
            await self.initialize()

        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        """FastAPI dependency for database session"""
        async with self.get_session() as session:
            yield session


# Global database manager instance
db_manager = DatabaseManager()


# FastAPI dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for FastAPI dependency injection"""
    async with db_manager.get_session() as session:
        yield session