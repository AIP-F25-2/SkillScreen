"""
Database connection and session management for SkillScreen
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import os
from typing import Generator
from config import config

class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection"""
        try:
            # Get database URL from config or environment
            database_url = os.getenv('DATABASE_URL', 'sqlite:///skillscreen.db')
            
            # For SQLite, use StaticPool to handle concurrent access
            if database_url.startswith('sqlite'):
                self.engine = create_engine(
                    database_url,
                    poolclass=StaticPool,
                    connect_args={"check_same_thread": False},
                    echo=config.debug
                )
            else:
                # For PostgreSQL, MySQL, etc.
                self.engine = create_engine(
                    database_url,
                    echo=config.debug,
                    pool_pre_ping=True,
                    pool_recycle=300
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
            
            print(f"✅ Database initialized: {database_url}")
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
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
            print(f"❌ Database session error: {e}")
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
