from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

class DBFactory:
    _engine = None
    _SessionFactory = None

    @classmethod
    def init(cls):
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            # Default to local SQLite if not configured to avoid startup failure
            db_url = "sqlite:///./user_service.db"
        try:
            is_sqlite = db_url.startswith("sqlite")
            engine_kwargs = {"echo": True}
            if is_sqlite:
                # SQLite needs this for multithreaded FastAPI
                engine_kwargs["connect_args"] = {"check_same_thread": False}
            cls._engine = create_engine(db_url, **engine_kwargs)
            cls._SessionFactory = sessionmaker(bind=cls._engine)
            print(f"Connected to database: {db_url}")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to database at {db_url}: {e}")

    @classmethod
    def get_session(cls):
        if cls._SessionFactory is None:
            cls.init()
        return cls._SessionFactory()

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            cls.init()
        return cls._engine

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

