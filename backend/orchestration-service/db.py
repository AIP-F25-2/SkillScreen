"""
Database connection and Unit of Work pattern
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import settings


class DBFactory:
    """Database factory for managing connections"""
    _engine = None
    _SessionFactory = None

    @classmethod
    def init(cls):
        """Initialize database engine and session factory"""
        if cls._engine is None:
            database_url = settings.DATABASE_URL
            cls._engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20
            )
            cls._SessionFactory = sessionmaker(bind=cls._engine)

    @classmethod
    def get_session(cls) -> Session:
        """Get database session"""
        if cls._SessionFactory is None:
            cls.init()
        return cls._SessionFactory()


class UnitOfWork:
    """Unit of Work pattern for database transactions"""
    
    def __init__(self):
        self.session = DBFactory.get_session()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        self.session.close()


# Initialize database on module import
DBFactory.init()

