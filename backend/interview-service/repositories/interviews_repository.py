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

import os
import json
from datetime import timedelta
import psycopg

from dotenv import load_dotenv

import json

from repositories.interview_templates_repository import get_template_by_id, get_template_questions
from repositories.interview_questions_repository import insert_interview_session
from fastapi import HTTPException

# ✅ Load environment variables from .env
load_dotenv()

# ---------- DB Connection ----------

def _conn():
    DB_URL = os.getenv("DATABASE_URL")
    if not DB_URL:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg.connect(DB_URL)


def insert_interview_session(interview_id: str, question: dict):
    """
    Insert a single interview session row into interview_sessions.
    Assumes 'question' dict contains: id, text, type, metadata (optional)
    """
    sql = """
    INSERT INTO interview_sessions (
        interview_id,
        question_id,
        question_text,
        question_type,
        metadata,
        created_at
    )
    VALUES (%s, %s, %s, %s, %s, NOW())
    RETURNING id;
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (
            interview_id,
            question.get("id"),
            question.get("text"),
            question.get("type"),
            json.dumps(question.get("metadata") or {})
        ))
        session_id = cur.fetchone()[0]
        conn.commit()
        return session_id

# ---------- Foreign Key Sanity Checks ----------

def verify_fk_belong_to_org(org_id, job_position_id, candidate_id, interviewer_id, template_id):
    """
    Validate that referenced records exist and belong to the same organization.
    """
    sql = """
    SELECT
      (SELECT COUNT(*) FROM organizations o WHERE o.id = %(org)s) as org_ok,
      (SELECT COUNT(*) FROM job_positions jp WHERE jp.id=%(job)s AND jp.organization_id=%(org)s) as job_ok,
      (SELECT COUNT(*) FROM candidates c WHERE c.id=%(cand)s AND c.organization_id=%(org)s) as cand_ok,
      (SELECT COUNT(*) FROM users u WHERE u.id=%(intr)s AND u.organization_id=%(org)s) as intr_ok,
      (SELECT COUNT(*) FROM interview_templates t WHERE t.id=%(tpl)s AND t.organization_id=%(org)s) as tpl_ok;
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {
            "org": org_id,
            "job": job_position_id,
            "cand": candidate_id,
            "intr": interviewer_id,
            "tpl": template_id
        })
        org_ok, job_ok, cand_ok, intr_ok, tpl_ok = cur.fetchone()
    if org_ok != 1:
        return False, "organization_id not found"
    if job_ok != 1:
        return False, "job_position_id not found or not in organization"
    if cand_ok != 1:
        return False, "candidate_id not found in organization"
    if intr_ok != 1:
        return False, "interviewer_id not found in organization"
    if tpl_ok != 1:
        return False, "template_id not found in organization"
    return True, "ok"

# ---------- Time Conflict Checker ----------

def check_time_conflicts(org_id, candidate_id, interviewer_id, scheduled_at, duration):
    """
    Detect overlap for candidate or interviewer within same org.
    """
    end_time = scheduled_at + timedelta(minutes=duration)

    sql = """
    SELECT 1
    FROM interviews i
    WHERE i.organization_id = %(org)s
      AND (i.candidate_id = %(cand)s OR i.interviewer_id = %(intr)s)
      AND i.status IN ('scheduled','in_progress')
      AND i.scheduled_at IS NOT NULL
      AND i.scheduled_at < %(new_end)s
      AND (
        i.scheduled_at
        + make_interval(mins => COALESCE((i.settings->>'duration_minutes')::int, %(dur)s))
      ) > %(new_start)s
    LIMIT 1;
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {
            "org": org_id,
            "cand": candidate_id,
            "intr": interviewer_id,
            "new_start": scheduled_at,
            "new_end": end_time,
            "dur": duration
        })
        return cur.fetchone() is not None

# ---------- Insert Interview ----------

def insert_interview_record(data: dict):
    """
    Insert new interview row and return a minimal view used by the controller.
    """
    sql = """
    INSERT INTO interviews (
        organization_id, job_position_id, candidate_id, interviewer_id,
        template_id, status, mode, scheduled_at, settings, created_at, updated_at
    )
    VALUES (%(org)s, %(job)s, %(cand)s, %(intr)s,
            %(tpl)s, %(status)s, %(mode)s, %(sched)s, %(settings)s, NOW(), NOW())
    RETURNING id, status, scheduled_at, settings;
    """
    params = {
        "org": data["organization_id"],
        "job": data["job_position_id"],
        "cand": data["candidate_id"],
        "intr": data["interviewer_id"],
        "tpl": data["template_id"],
        "status": data["status"],
        "mode": data["mode"],
        "sched": data["scheduled_at"],
        "settings": json.dumps(data.get("settings") or {})
    }
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        conn.commit()
        return {
            "id": str(row[0]),
            "status": row[1],
            "scheduled_at": row[2],
            "settings": row[3]
        }

# ---------- Get Interview ----------

def get_interview_by_id(interview_id: str):
    """
    Retrieve full interview row by ID.
    """
    sql = """
    SELECT id, organization_id, job_position_id, candidate_id, interviewer_id,
           template_id, status, mode, scheduled_at, settings, created_at, updated_at
    FROM interviews
    WHERE id = %s;
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (interview_id,))
        row = cur.fetchone()
        if not row:
            return None
        return dict(zip([desc.name for desc in cur.description], row))

# ---------- Update Interview Status ----------

def update_interview_status(interview_id: str, new_status: str):
    """
    Update interview status and set timestamps if needed.
    """
    time_fields = {
        "in_progress": "started_at",
        "completed": "completed_at"
    }
    extra_field = time_fields.get(new_status)

    sql = f"""
    UPDATE interviews
    SET status = %(status)s,
        updated_at = NOW()
        {f", {extra_field} = NOW()" if extra_field else ""}
    WHERE id = %(id)s
    RETURNING id, status, updated_at;
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(sql, {"status": new_status, "id": interview_id})
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": str(row[0]),
            "status": row[1],
            "updated_at": row[2]
        }

# ---------- Store Interview Questions ----------

def store_questions_service(interview_id: str, template_id: str):
    # 🔍 Step 1: Get interview to extract organization_id
    interview = get_interview_by_id(interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    org_id = interview["organization_id"]

    # 🔍 Step 2: Get template using both template_id and org_id
    template = get_template_by_id(template_id, org_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    questions = template["questions"]
    if not questions:
        raise HTTPException(status_code=400, detail="Template has no questions")

    # ✅ Step 3: Store each question into interview_sessions
    for q in questions:
        insert_interview_session(interview_id, q)