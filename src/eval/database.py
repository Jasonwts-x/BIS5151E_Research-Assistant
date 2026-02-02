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
    """
    Manages PostgreSQL connection and session lifecycle for evaluation data.

    This class handles the creation of the SQLAlchemy engine, connection pooling,
    and provides a context-managed session for safe database operations.

    Attributes:
        database_url (str): The full connection string used for the database.
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine instance.
        SessionLocal (sqlalchemy.orm.sessionmaker): Factory for producing Session objects.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the database connection and internal session factory.

        Args:
            database_url: PostgreSQL connection string. 
                Format: `postgresql://user:pass@host:port/dbname`.
                If None, defaults to the DATABASE_URL environment variable.

        Raises:
            Exception: If the initial connection attempt fails.
        """
        if database_url is None:
            # Fallback chain: Env Var -> Hardcoded Docker Default
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
        """
        Establish the engine with connection pooling and initialize schema.

        Configures:
            - pool_pre_ping: Ensures stale connections are refreshed (pessimistic testing).
            - pool_size/max_overflow: Manages concurrent connection limits.
        """
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,  # Verify connections before using to avoid 'Server closed' errors
            pool_size=5,         # Keep 5 connections ready
            max_overflow=10,     # Allow up to 10 extra connections during peaks
            echo=False,          # Toggle to True to see raw SQL in logs
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        # Idempotent table creation
        Base.metadata.create_all(bind=self.engine)
        logger.info("✓ Database tables initialized")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        This context manager ensures that the session is automatically closed,
        and provides a rollback mechanism if an exception occurs during the block.

        Yields:
            sqlalchemy.orm.Session: An active SQLAlchemy session.

        Example:
            >>> db = get_database()
            >>> with db.get_session() as session:
            ...     session.add(my_record)
            ...     session.commit()

        Raises:
            RuntimeError: If called before a connection is established.
            Exception: Re-raises any exception encountered within the 'with' block 
                after performing a rollback.
        """
        if self.SessionLocal is None:
            raise RuntimeError("Database not connected. Initialize EvaluationDatabase first.")
        
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
        Perform a simple query to verify database accessibility.

        Returns:
            bool: True if the database responds, False otherwise.
        """
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("Database health check failed: %s", e)
            return False

    def close(self):
        """
        Dispose of the engine and release all pooled connections.
        
        Should be called during application shutdown.
        """
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")


# Singleton instance to prevent multiple redundant connection pools
_db = None


def get_database() -> EvaluationDatabase:
    """
    Retrieve or initialize the singleton EvaluationDatabase instance.

    Returns:
        EvaluationDatabase: The shared database manager.
    """
    global _db
    if _db is None:
        _db = EvaluationDatabase()
    return _db