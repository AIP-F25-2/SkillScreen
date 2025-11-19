"""
Lightweight database helpers bundled with media-service.

This avoids reaching into the shared common-service package when the
service is built/pushed independently (e.g., Docker Hub).
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


class DBFactory:
    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None

    @classmethod
    def init(cls) -> None:
        """Initialize the global SQLAlchemy engine/session factory."""
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable is required")

        cls._engine = create_engine(db_url, echo=os.getenv("SQL_ECHO", "false").lower() == "true")
        cls._session_factory = sessionmaker(bind=cls._engine)

    @classmethod
    def get_session(cls) -> Session:
        """Return a SQLAlchemy session, initializing the factory on first use."""
        if cls._session_factory is None:
            cls.init()
        assert cls._session_factory is not None  # mypy hint
        return cls._session_factory()


class UnitOfWork:
    """Simple context manager wrapping a SQLAlchemy session."""

    def __init__(self) -> None:
        self.session: Session = DBFactory.get_session()

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
        finally:
            self.session.close()


@contextmanager
def get_uow() -> Generator[UnitOfWork, None, None]:
    """Helper generator for ad-hoc usage."""
    with UnitOfWork() as uow:
        yield uow
