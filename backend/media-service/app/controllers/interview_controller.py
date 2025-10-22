import os
import subprocess
from flask import Flask,Blueprint, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

interview_bp = Blueprint("interview", __name__)

# =========================================================
# 📄 RESUME & CANDIDATE MANAGEMENT ENDPOINTS
# =========================================================

# In-memory storage for candidates and interviews (replace with DB later)
candidates_db = {}
interviews_db = {}

@interview_bp.route("/api/resumes/upload", methods=["POST"])
def upload_resume():
    """Upload a PDF resume for a candidate."""
    file = request.files.get("file")
    candidate_name = request.form.get("candidate_name", "Unknown Candidate")
    
    if not file:
        return jsonify({"error": "Missing file"}), 400
    
    if not file.filename.endswith('.pdf'):
        return jsonify({"error": "Only PDF files are allowed"}), 400
    
    # Generate candidate ID
    candidate_id = f"cand_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Save file
    candidate_folder = os.path.join(UPLOAD_FOLDER, "resumes", candidate_id)
    os.makedirs(candidate_folder, exist_ok=True)
    
    file_path = os.path.join(candidate_folder, f"{candidate_id}_resume.pdf")
    file.save(file_path)
    
    # Store candidate info
    candidates_db[candidate_id] = {
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "resume_path": file_path,
        "status": "pending",
        "uploaded_at": datetime.now().isoformat(),
        "assigned_user": "ashish"
    }
    
    return jsonify({
        "success": True,
        "data": candidates_db[candidate_id],
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "request_id": candidate_id,
            "version": "1.0"
        }
    }), 200


@interview_bp.route("/api/candidates", methods=["GET"])
def get_all_candidates():
    """Get all candidates."""
    return jsonify({
        "success": True,
        "data": {
            "candidates": list(candidates_db.values()),
            "count": len(candidates_db)
        },
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "request_id": "req_" + datetime.now().strftime('%Y%m%d%H%M%S'),
            "version": "1.0"
        }
    }), 200


@interview_bp.route("/api/candidates/user/<user_id>", methods=["GET"])
def get_user_candidates(user_id):
    """Get all candidates assigned to a specific user."""
    user_candidates = [
        candidate for candidate in candidates_db.values()
        if candidate.get("assigned_user") == user_id
    ]
    
    return jsonify({
        "success": True,
        "data": {
            "candidates": user_candidates,
            "count": len(user_candidates)
        },
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "request_id": f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "version": "1.0"
        }
    }), 200


@interview_bp.route("/api/candidates/<candidate_id>", methods=["GET"])
def get_candidate(candidate_id):
    """Get a specific candidate."""
    if candidate_id not in candidates_db:
        return jsonify({"error": "Candidate not found"}), 404
    
    return jsonify({
        "success": True,
        "data": candidates_db[candidate_id],
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "request_id": candidate_id,
            "version": "1.0"
        }
    }), 200


@interview_bp.route("/api/candidates/<candidate_id>/schedule", methods=["POST"])
def schedule_candidate(candidate_id):
    """Schedule an interview for a candidate."""
    if candidate_id not in candidates_db:
        return jsonify({"error": "Candidate not found"}), 404
    
    # Create interview session
    interview_id = f"interview_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    interview_data = {
        "interview_id": interview_id,
        "session_id": interview_id,  # Keep for backwards compatibility
        "candidate_id": candidate_id,
        "candidate_name": candidates_db[candidate_id]["candidate_name"],
        "assigned_user": "ashish",
        "user_id": "ashish",  # Add this for backwards compatibility
        "status": "scheduled",
        "scheduled_at": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat()
    }
    
    interviews_db[interview_id] = interview_data
    candidates_db[candidate_id]["status"] = "scheduled"
    candidates_db[candidate_id]["interview_id"] = interview_id
    candidates_db[candidate_id]["session_id"] = interview_id  # Keep for backwards compatibility
    
    return jsonify({
        "success": True,
        "data": interview_data,
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "request_id": interview_id,
            "version": "1.0"
        }
    }), 200


@interview_bp.route("/api/interviews", methods=["GET"])
def get_all_interviews():
    """Get all interviews."""
    return jsonify({
        "success": True,
        "data": {
            "interviews": list(interviews_db.values()),
            "count": len(interviews_db)
        },
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "request_id": "req_" + datetime.now().strftime('%Y%m%d%H%M%S'),
            "version": "1.0"
        }
    }), 200


@interview_bp.route("/api/interviews/<interview_id>", methods=["GET"])
def get_interview_details(interview_id):
    """Get details for a specific interview."""
    if interview_id not in interviews_db:
        return jsonify({"error": "Interview not found"}), 404
    
    return jsonify({
        "success": True,
        "data": interviews_db[interview_id],
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "request_id": interview_id,
            "version": "1.0"
        }
    }), 200


@interview_bp.route("/api/interviews/<interview_id>/status", methods=["PATCH"])
def update_interview_status(interview_id):
    """Update interview status."""
    if interview_id not in interviews_db:
        return jsonify({"error": "Interview not found"}), 404
    
    data = request.get_json()
    status = data.get("status")
    
    if not status:
        return jsonify({"error": "Missing status"}), 400
    
    interviews_db[interview_id]["status"] = status
    interviews_db[interview_id]["updated_at"] = datetime.now().isoformat()
    
    return jsonify({
        "success": True,
        "data": interviews_db[interview_id],
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "request_id": interview_id,
            "version": "1.0"
        }
    }), 200


@interview_bp.route("/api/interviews/<interview_id>/transcript", methods=["POST"])
def update_interview_transcript(interview_id):
    """Update interview transcript."""
    if interview_id not in interviews_db:
        return jsonify({"error": "Interview not found"}), 404
    
    data = request.get_json()
    
    interviews_db[interview_id]["transcript"] = data
    interviews_db[interview_id]["updated_at"] = datetime.now().isoformat()
    
    return jsonify({
        "success": True,
        "data": interviews_db[interview_id],
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "request_id": interview_id,
            "version": "1.0"
        }
    }), 200


@interview_bp.route("/api/interviews/user/<user_id>", methods=["GET"])
def get_user_interviews(user_id):
    """Get interviews for a specific user."""
    print(f"Getting interviews for user: {user_id}")
    print(f"All interviews: {list(interviews_db.values())}")
    user_interviews = [i for i in interviews_db.values() if i.get("assigned_user") == user_id or i.get("user_id") == user_id]
    print(f"User interviews: {user_interviews}")
    return jsonify({
        "success": True,
        "data": {
            "interviews": user_interviews,
            "count": len(user_interviews)
        },
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "request_id": "req_" + datetime.now().strftime('%Y%m%d%H%M%S'),
            "version": "1.0"
        }
    }), 200
