import sys
sys.path.append('/common-service')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import settings, logger
from typing import Optional


class DBFactory:
    """Database factory for creating and managing database sessions"""

    _engine = None
    _SessionLocal = None

    @classmethod
    def initialize(cls):
        """Initialize database connection"""
        if cls._engine is None:
            if not settings.DATABASE_URL:
                raise ValueError("DATABASE_URL is not set in environment variables")

            logger.info(f"Initializing database connection: {settings.DATABASE_URL}")

            cls._engine = create_engine(
                settings.DATABASE_URL,
                echo=settings.is_debug(),
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 10}
            )

            cls._SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=cls._engine
            )

            logger.info("✅ Database connection initialized successfully")

    @classmethod
    def get_session(cls) -> Session:
        """Get a database session"""
        if cls._SessionLocal is None:
            cls.initialize()
        return cls._SessionLocal()

    @classmethod
    def get_engine(cls):
        """Get the database engine"""
        if cls._engine is None:
            cls.initialize()
        return cls._engine

    @classmethod
    def close_all(cls):
        """Close all connections"""
        if cls._engine is not None:
            cls._engine.dispose()
            logger.info("Database connections closed")


class UnitOfWork:
    """Unit of Work pattern for managing database transactions"""

    def __init__(self, session: Optional[Session] = None):
        self.session = session or DBFactory.get_session()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
            logger.error(f"Transaction rolled back due to error: {exc_val}")
        self.session.close()

    def commit(self):
        """Commit transaction"""
        try:
            self.session.commit()
            logger.debug("Transaction committed")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to commit transaction: {str(e)}")
            raise

    def rollback(self):
        """Rollback transaction"""
        self.session.rollback()
        logger.debug("Transaction rolled back")


# Initialize database on import
try:
    DBFactory.initialize()
except Exception as e:
    logger.warning(f"Database initialization warning: {str(e)}")
