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
                raise ValueError("DATABASE_URL is not set")
        try:
                cls._engine = create_engine(db_url, echo=True)
                cls._SessionFactory = sessionmaker(bind=cls._engine)
                print(f"Connected to database: {db_url}")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to database at {db_url}: {e}")

    @classmethod
    def get_session(cls):
        if cls._SessionFactory is None:
            cls.init()
        return cls._SessionFactory()

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

