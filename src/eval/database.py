"""
Database Connection
PostgreSQL connection management for evaluation storage.
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

logger = logging.getLogger(__name__)


class EvaluationDatabase:
    """Manages PostgreSQL connection for evaluation data."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            database_url: PostgreSQL connection string
                          Format: postgresql://user:pass@host:port/dbname
        """
        if database_url is None:
            # Get from environment or use default
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://research_assistant:research_password@postgres:5432/research_assistant"
            )

        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None

        try:
            self._connect()
            logger.info("✓ Database connection established")
        except Exception as e:
            logger.error("Database connection failed: %s", e)
            raise

    def _connect(self):
        """Establish database connection and create tables."""
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=5,
            max_overflow=10,
            echo=False,  # Set to True for SQL query debugging
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
        logger.info("✓ Database tables initialized")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session as context manager.
        
        Automatically handles commit/rollback and cleanup.
        
        Usage:
            with db.get_session() as session:
                session.add(record)
                session.commit()
        
        Yields:
            SQLAlchemy session
        """
        if self.SessionLocal is None:
            raise RuntimeError("Database not connected")
        
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error("Database session error, rolled back: %s", e)
            raise
        finally:
            session.close()

    def health_check(self) -> bool:
        """
        Check if database is accessible.
        
        Returns:
            True if database is healthy, False otherwise
        """
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("Database health check failed: %s", e)
            return False

    def close(self):
        """Close database connection and cleanup resources."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")


# Singleton instance
_db = None


def get_database() -> EvaluationDatabase:
    """
    Get singleton database instance.
    
    Returns:
        EvaluationDatabase singleton
    """
    global _db
    if _db is None:
        _db = EvaluationDatabase()
    return _db