import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.utils.config import settings


class DBFactory:
    _engine = None
    _session_factory: Optional[sessionmaker] = None

    @classmethod
    def init(cls) -> None:
        db_url = settings.DATABASE_URL or os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL is not configured")
        if cls._engine is not None:
            return
        cls._engine = create_engine(db_url, echo=bool(os.getenv("SQL_ECHO")))
        cls._session_factory = sessionmaker(bind=cls._engine)

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            cls.init()
        return cls._engine

    @classmethod
    def get_session(cls):
        if cls._session_factory is None:
            cls.init()
        return cls._session_factory()


class UnitOfWork:
    def __init__(self):
        self.session = DBFactory.get_session()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
        finally:
            self.session.close()
