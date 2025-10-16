# def create_interview(data: dict):
#     """
#     Insert interview row into DB.
#     TODO: Implement with SQLAlchemy + PostgreSQL.
#     """
#     return {"id": "uuid_placeholder", **data}

# def get_interview_by_id(interview_id: str):
#     """
#     Fetch interview row from DB.
#     TODO: Implement with SQLAlchemy.
#     """
#     return {"id": interview_id, "status": "scheduled (placeholder)"}


import psycopg
from datetime import timedelta
from os import getenv

DB_URL = getenv("DATABASE_URL")

def check_time_conflicts(candidate_id, interviewer_id, scheduled_at, duration):
    """Check if candidate or interviewer already has interview during this time window."""
    end_time = scheduled_at + timedelta(minutes=duration)

    sql = """
        SELECT 1
        FROM interviews
        WHERE (candidate_id = %s OR interviewer_id = %s)
          AND status IN ('scheduled', 'in_progress')
          AND scheduled_at < %s
          AND (scheduled_at + (settings->>'duration_minutes')::interval) > %s
        LIMIT 1;
    """
    try:
        with psycopg.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (candidate_id, interviewer_id, end_time, scheduled_at))
                return cur.fetchone() is not None
    except Exception as e:
        print("DB conflict check error:", e)
        return False


def insert_interview_record(data: dict):
    """Insert a new interview record into the database."""
    sql = """
        INSERT INTO interviews (
            organization_id, job_position_id, candidate_id, interviewer_id,
            template_id, status, mode, scheduled_at, settings, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        RETURNING id, status, scheduled_at, settings;
    """
    try:
        with psycopg.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    data["organization_id"],
                    data["job_position_id"],
                    data["candidate_id"],
                    data["interviewer_id"],
                    data["template_id"],
                    data["status"],
                    data["mode"],
                    data["scheduled_at"],
                    json_dumps(data["settings"])
                ))
                row = cur.fetchone()
                conn.commit()
                return {
                    "id": row[0],
                    "status": row[1],
                    "scheduled_at": row[2],
                    "settings": row[3]
                }
    except Exception as e:
        raise Exception(f"Database insert failed: {e}")
