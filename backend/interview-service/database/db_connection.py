import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set in the environment.")
    return psycopg.connect(db_url)
