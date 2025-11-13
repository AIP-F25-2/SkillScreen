"""
Database connection and session management for SkillScreen
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import os
from typing import Generator
from utils.config_loader import get_config

class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection"""
        try:
            # Get database URL from environment variables
            database_url = get_config('DATABASE_URL')
            
            if not database_url:
                # Fallback to individual components
                host = get_config('DATABASE_HOST', 'localhost')
                port = get_config('DATABASE_PORT', '5432')
                dbname = get_config('DATABASE_NAME', 'skillscreen_database')
                user = get_config('DATABASE_USER', 'postgres')
                password = get_config('DATABASE_PASSWORD', '')
                ssl_mode = get_config('DATABASE_SSL_MODE', 'prefer')
                
                database_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}?sslmode={ssl_mode}"
            
            # Create PostgreSQL engine with proper configuration
            self.engine = create_engine(
                database_url,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,
                pool_recycle=300,
                pool_size=10,
                max_overflow=20,
                connect_args={
                    "sslmode": "require",
                    "application_name": "SkillScreen-TextService"
                }
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Import models to ensure they're registered
            from .models import Base
            Base.metadata.create_all(bind=self.engine)
            
            print(f"Database initialized: {database_url.split('@')[1] if '@' in database_url else 'Azure PostgreSQL'}")
            
        except Exception as e:
            print(f"Database initialization failed: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """Get database session (caller responsible for cleanup)"""
        return self.SessionLocal()
    
    def close_all_sessions(self):
        """Close all database connections"""
        if self.engine:
            self.engine.dispose()

# Global database manager instance
db_manager = DatabaseManager()

# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions"""
    with db_manager.get_session() as session:
        yield session
