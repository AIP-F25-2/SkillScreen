import pytest
from fastapi.testclient import TestClient

from coding import app


client = TestClient(app)


def test_root_and_health():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json().get("data")

    r2 = client.get("/health")
    assert r2.status_code == 200


def test_assess_difficulty_rule_based():
    payload = {
        "resume_data": {"experience_years": 0, "skills": []},
        "job_description": {"level": "entry", "required_skills": []}
    }

    r = client.post("/difficulty", json=payload)
    assert r.status_code == 200
    data = r.json().get("data")
    assert data is not None
    assert data.get("difficulty") in ["easy", "medium", "hard"]


def test_generate_question_fallback():
    payload = {
        "resume_data": {"skills": ["python"], "experience_years": 1},
        "job_description": {"job_title": "Software Engineer", "required_skills": ["python"]},
        "difficulty": "easy",
        "question_number": 1
    }

    r = client.post("/generate", json=payload)
    assert r.status_code == 200
    data = r.json().get("data")
    assert data is not None
    assert "title" in data or "description" in data or "test_cases" in data
