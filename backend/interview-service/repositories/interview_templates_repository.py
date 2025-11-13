import psycopg
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def _conn():
    if not DB_URL:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg.connect(DB_URL)


def get_template_by_id(template_id: str, org_id: str):
    """
    Fetch a template by ID and organization.
    """
    query = """
        SELECT id, name, questions
        FROM interview_templates
        WHERE id = %s AND organization_id = %s AND deleted_at IS NULL
        LIMIT 1
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(query, (template_id, org_id))
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "name": row[1],
            "questions": row[2]
        }


def get_template_questions(template_id: str):
    """
    Fetch the `questions` field from a given template.
    """
    query = """
        SELECT questions
        FROM interview_templates
        WHERE id = %s AND deleted_at IS NULL
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(query, (template_id,))
        row = cur.fetchone()
        if not row:
            return None
        return row[0]  # returns JSONB list of questions
