import psycopg
import os
import json

from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

def _conn():
    if not DB_URL:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg.connect(DB_URL)

def get_template_questions(template_id: str):
    """
    Retrieve the questions field from the interview_templates table for a given template_id.
    """
    sql = """
    SELECT questions
    FROM interview_templates
    WHERE id = %s AND deleted_at IS NULL
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (template_id,))
        row = cur.fetchone()
        if not row:
            return None
        return row[0]  # questions column (jsonb)
