import uuid
from datetime import datetime
from psycopg import connect
import os

DB_URL = os.getenv("DATABASE_URL")

def _conn():
    return connect(DB_URL)

def store_template_questions_into_sessions(interview_id: str, template: dict):
    """
    Stores all questions from the template into interview_sessions.
    """
    questions = template["questions"] or []
    now = datetime.utcnow()
    rows = []

    for q in questions:
        rows.append((
            str(uuid.uuid4()),  # session row id
            interview_id,
            q.get("id", None),
            q["text"],
            q["type"],
            now
        ))

    sql = """
    INSERT INTO interview_sessions (
        id, interview_id, question_id, question_text, question_type, created_at
    ) VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id;
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.executemany(sql, rows)
        conn.commit()

def get_questions_by_interview_id(interview_id: str):
    sql = """
    SELECT id, interview_id, question_id, question_text, question_type, created_at
    FROM interview_sessions
    WHERE interview_id = %s
    ORDER BY created_at ASC;
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (interview_id,))
        rows = cur.fetchall()
        if not rows:
            return []
        return [
            {
                "id": str(row[0]),
                "interview_id": row[1],
                "question_id": row[2],
                "question_text": row[3],
                "question_type": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]
