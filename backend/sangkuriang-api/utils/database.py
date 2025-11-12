"""
Database utilities for SANGKURIANG API
"""

import os
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import logging

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://sangkuriang:sangkuriang@localhost/sangkuriang_db")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,  # For development, use connection pooling in production
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
    future=True
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database."""
    try:
        # Test connection
        async with engine.begin() as conn:
            # Check if connection is working
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()
            
            logger.info("Database connection successful")
            
            # Create tables if they don't exist
            # This is a simplified version - in production, use proper migrations
            # await conn.run_sync(Base.metadata.create_all)
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

async def close_db():
    """Close database connections."""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

# Database utilities
async def execute_query(query: str, params: dict = None) -> list:
    """Execute raw SQL query."""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(text(query), params or {})
            return result.fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

async def execute_command(command: str, params: dict = None) -> int:
    """Execute raw SQL command (INSERT, UPDATE, DELETE)."""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(text(command), params or {})
            await session.commit()
            return result.rowcount
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# Database health check
async def check_db_health():
    """Check database health."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            await result.fetchone()
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False