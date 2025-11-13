import os
import subprocess
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

app = Flask(__name__)

# Configure CORS with specific origins for security
# In production, replace with actual frontend domain
CORS(app, origins=[
    "http://localhost:3000",  # Next.js dev server
    "http://localhost:5000",  # API Gateway
    "https://localhost:3000",  # HTTPS dev
    "https://localhost:5000",  # HTTPS API Gateway
], 
methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
supports_credentials=True)

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload_chunk", methods=["POST"])
def upload_chunk():
    file = request.files.get("file")
    user_id = request.form.get("user_id")

    if not file or not user_id:
        return jsonify({"error": "Missing file or user_id"}), 400

    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    os.makedirs(user_folder, exist_ok=True)

    # Get chunk filename and ensure it's a valid format (chunk_XXXX.webm)
    chunk_filename = file.filename
    if not chunk_filename.startswith('chunk_') or not chunk_filename.endswith('.webm'):
        return jsonify({"error": "Invalid chunk filename format"}), 400

    # Extract chunk index and validate
    try:
        chunk_index = int(chunk_filename.split('_')[1].split('.')[0])
    except (IndexError, ValueError):
        return jsonify({"error": "Invalid chunk index"}), 400

    # Save chunk
    chunk_path = os.path.join(user_folder, chunk_filename)
    if os.path.exists(chunk_path):
        # Skip if chunk already exists (avoid duplicates)
        return jsonify({"status": "chunk already exists", "chunk": chunk_filename}), 200

    file.save(chunk_path)
    print(f"Saved chunk {chunk_filename} for user {user_id}")

    return jsonify({"status": "chunk saved", "chunk": chunk_filename}), 200


@app.route("/reset_chunks", methods=["POST"])
def reset_chunks():
    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    if os.path.exists(user_folder):
        # First, list all chunks to delete
        chunks_to_delete = [f for f in os.listdir(user_folder) if f.endswith(".webm")]
        print(f"Found {len(chunks_to_delete)} chunks to delete for user {user_id}")
        
        # Delete each chunk
        deleted_chunks = []
        failed_chunks = []
        for chunk in chunks_to_delete:
            try:
                chunk_path = os.path.join(user_folder, chunk)
                os.remove(chunk_path)
                deleted_chunks.append(chunk)
            except Exception as e:
                print(f"Failed to delete {chunk}: {e}")
                failed_chunks.append(chunk)
        
        # Double check no chunks remain
        remaining_chunks = [f for f in os.listdir(user_folder) if f.endswith(".webm")]
        if remaining_chunks:
            print(f"Warning: {len(remaining_chunks)} chunks still remain after cleanup")
            # Try one more time with a delay
            import time
            time.sleep(0.1)
            for chunk in remaining_chunks:
                try:
                    os.remove(os.path.join(user_folder, chunk))
                except Exception:
                    pass

    return jsonify({
        "status": "chunks reset",
        "deleted": len(deleted_chunks),
        "failed": len(failed_chunks)
    }), 200


@app.route("/finalize_upload", methods=["POST"])
def finalize_upload():
    print("=== FINALIZE_UPLOAD STARTED ===")
    data = request.get_json()
    print(f"Request data: {data}")
    
    user_id = data.get("user_id")
    session_id = data.get("session_id")
    candidate_id = data.get("candidate_id")

    print(f"Extracted values: user_id={user_id}, session_id={session_id}, candidate_id={candidate_id}")

    if not user_id:
        print("ERROR: Missing user_id")
        return jsonify({"error": "Missing user_id"}), 400

    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    if not os.path.exists(user_folder):
        print(f"ERROR: No chunks found for user {user_id}")
        return jsonify({"error": "No chunks found"}), 400

    # Get all WebM chunks and sort by chunk index
    chunks = [f for f in os.listdir(user_folder) if f.endswith(".webm")]
    if not chunks:
        print(f"ERROR: No .webm chunks found in {user_folder}")
        return jsonify({"error": "No .webm chunks found"}), 400
    
    print(f"Found {len(chunks)} chunks: {chunks}")
    
    # Sort chunks by their numeric index (chunk_0000.webm, chunk_0001.webm, etc.)
    chunks.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_mp4 = os.path.join(user_folder, f"{user_id}_{timestamp}.mp4")
    
    print(f"Creating final video: {final_mp4}")
    
    # Create concat file list for FFmpeg
    concat_file = os.path.join(user_folder, "concat_list.txt")
    with open(concat_file, "w") as f:
        for fname in chunks:
            chunk_path = os.path.join(user_folder, fname)
            # Use absolute path and escape special characters
            f.write(f"file '{os.path.abspath(chunk_path)}'\n")

    try:
        print("Starting FFmpeg processing...")
        # Use FFmpeg concat demuxer for proper WebM merging
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
                "-movflags", "+faststart",
                final_mp4
            ],
            check=True,
            capture_output=True,
            text=True
        )
        print("FFmpeg processing completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr}")
        return jsonify({"error": f"ffmpeg failed: {e.stderr}"}), 500

    # Cleanup chunks and concat file
    for fname in chunks + ["concat_list.txt"]:
        path_to_delete = os.path.join(user_folder, fname)
        try:
            os.remove(path_to_delete)
        except Exception as e:
            print(f"Failed to delete {path_to_delete}: {e}")
    
    print("=== CREATING INTERVIEW RECORD ===")
    
    # Create interview record
    interview_id = session_id if session_id else f"interview_{timestamp}"
    video_path = f"/{user_id}/{os.path.basename(final_mp4)}"
    
    print(f"Creating interview record: interview_id={interview_id}, video_path={video_path}")
    
    interview_data = {
        "interview_id": interview_id,
        "session_id": session_id or interview_id,
        "candidate_id": candidate_id or user_id,
        "candidate_name": candidate_id or user_id,
        "user_id": user_id,
        "assigned_user": user_id,
        "video_path": video_path,
        "status": "completed",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    interviews_db[interview_id] = interview_data
    print(f"Interview record created and stored: {interview_id}")
    print(f"Total interviews in DB: {len(interviews_db)}")

    response_data = {
        "status": "done",
        "interview_id": interview_id,
        "file": video_path
    }
    print(f"Returning response: {response_data}")
    
    return jsonify(response_data), 200


@app.route("/video/<user_id>/<filename>")
def serve_video(user_id, filename):
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    return send_from_directory(user_folder, filename)


# ----------------------------
# VIDEO MANAGEMENT ENDPOINTS
# ----------------------------

# 1️⃣ Get all videos of all users
@app.route("/admin/videos", methods=["GET"])
def get_all_videos():
    all_videos = {}
    for user in os.listdir(UPLOAD_FOLDER):
        user_folder = os.path.join(UPLOAD_FOLDER, user)
        if os.path.isdir(user_folder):
            videos = [f for f in os.listdir(user_folder) if f.endswith(".mp4")]
            all_videos[user] = videos
    return jsonify(all_videos), 200

# 2️⃣ Get all videos of a specific user
@app.route("/admin/videos/<user_id>", methods=["GET"])
def get_user_videos(user_id):
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    if not os.path.exists(user_folder):
        return jsonify({"videos": []}), 200
    videos = [f for f in os.listdir(user_folder) if f.endswith(".mp4")]
    return jsonify({"user": user_id, "videos": videos}), 200

# 3️⃣ Delete a specific video of a user
@app.route("/admin/video/<user_id>/<filename>", methods=["DELETE"])
def delete_video(user_id, filename):
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    video_path = os.path.join(user_folder, filename)
    if os.path.exists(video_path):
        os.remove(video_path)
        return jsonify({"status": "deleted", "file": filename}), 200
    return jsonify({"error": "file not found"}), 404

# 4️⃣ Delete all videos of a user
@app.route("/admin/videos/<user_id>", methods=["DELETE"])
def delete_user_videos(user_id):
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    if not os.path.exists(user_folder):
        return jsonify({"status": "no videos found"}), 200

    deleted = []
    for f in os.listdir(user_folder):
        if f.endswith(".mp4"):
            try:
                os.remove(os.path.join(user_folder, f))
                deleted.append(f)
            except Exception as e:
                print(f"Failed to delete {f}: {e}")

    return jsonify({"status": "deleted", "deleted_files": deleted}), 200

# 5️⃣ Delete all videos of all users
@app.route("/admin/videos", methods=["DELETE"])
def delete_all_videos():
    deleted = {}
    for user in os.listdir(UPLOAD_FOLDER):
        user_folder = os.path.join(UPLOAD_FOLDER, user)
        if os.path.isdir(user_folder):
            deleted[user] = []
            for f in os.listdir(user_folder):
                if f.endswith(".mp4"):
                    try:
                        os.remove(os.path.join(user_folder, f))
                        deleted[user].append(f)
                    except Exception as e:
                        print(f"Failed to delete {f}: {e}")
    return jsonify({"status": "deleted all videos", "deleted_files": deleted}), 200

@app.route("/admin/video/<user_id>/preview/<filename>", methods=["GET"])
def admin_preview_video(user_id, filename):
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    video_path = os.path.join(user_folder, filename)
    if os.path.exists(video_path):
        return send_from_directory(user_folder, filename)
    return jsonify({"error": "file not found"}), 404


@app.route("/admin/search/users", methods=["GET"])
def search_users():
    query = request.args.get("q", "").lower()
    matched_users = [u for u in os.listdir(UPLOAD_FOLDER) if query in u.lower()]
    return jsonify({"query": query, "matched_users": matched_users}), 200


@app.route("/admin/search/videos", methods=["GET"])
def search_videos():
    query = request.args.get("q", "").lower()
    matched_videos = {}
    for user in os.listdir(UPLOAD_FOLDER):
        user_folder = os.path.join(UPLOAD_FOLDER, user)
        if os.path.isdir(user_folder):
            videos = [f for f in os.listdir(user_folder) if query in f.lower() and f.endswith(".mp4")]
            if videos:
                matched_videos[user] = videos
    return jsonify({"query": query, "matched_videos": matched_videos}), 200

@app.route("/admin/user", methods=["POST"])
def create_user():
    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    if os.path.exists(user_folder):
        return jsonify({"status": "user already exists"}), 200

    os.makedirs(user_folder, exist_ok=True)
    return jsonify({"status": "user created", "user_id": user_id}), 201


@app.route("/admin/users", methods=["GET"])
def get_all_users():
    users = [u for u in os.listdir(UPLOAD_FOLDER) if os.path.isdir(os.path.join(UPLOAD_FOLDER, u))]
    return jsonify({"users": users}), 200


@app.route("/admin/user/<user_id>", methods=["GET"])
def get_user(user_id):
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    if os.path.exists(user_folder):
        videos = [f for f in os.listdir(user_folder) if f.endswith(".mp4")]
        return jsonify({"user_id": user_id, "videos": videos}), 200
    return jsonify({"error": "user not found"}), 404

@app.route("/admin/user/<user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()
    new_user_id = data.get("new_user_id")
    if not new_user_id:
        return jsonify({"error": "Missing new_user_id"}), 400

    old_folder = os.path.join(UPLOAD_FOLDER, user_id)
    new_folder = os.path.join(UPLOAD_FOLDER, new_user_id)

    if not os.path.exists(old_folder):
        return jsonify({"error": "user not found"}), 404
    if os.path.exists(new_folder):
        return jsonify({"error": "new user_id already exists"}), 400

    os.rename(old_folder, new_folder)
    return jsonify({"status": "user renamed", "old_user_id": user_id, "new_user_id": new_user_id}), 200

@app.route("/admin/user/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    if os.path.exists(user_folder):
        import shutil
        shutil.rmtree(user_folder)
        return jsonify({"status": "user deleted", "user_id": user_id}), 200
    return jsonify({"error": "user not found"}), 404

# Delete all users and all their data
@app.route("/admin/users", methods=["DELETE"])
def delete_all_users():
    deleted = []
    for user in os.listdir(UPLOAD_FOLDER):
        user_folder = os.path.join(UPLOAD_FOLDER, user)
        if os.path.isdir(user_folder):
            try:
                for f in os.listdir(user_folder):
                    os.remove(os.path.join(user_folder, f))
                os.rmdir(user_folder)
                deleted.append(user)
            except Exception as e:
                print(f"Failed to delete user {user}: {e}")
    return jsonify({"status":"deleted all users", "deleted_users": deleted}), 200


# =========================================================
# 📁 GENERAL FILE UPLOAD + ADMIN CRUD ENDPOINTS
# =========================================================

@app.route("/upload", methods=["POST"])
def upload_general_file():
    """
    Upload any general file (e.g., PDF, DOCX, ZIP, PNG, etc.) into the same user folder.
    FormData:
        user_id: "123"
        file: (any file)
    """
    file = request.files.get("file")
    user_id = request.form.get("user_id")

    if not file or not user_id:
        return jsonify({"error": "Missing file or user_id"}), 400

    # Create user folder if it doesn't exist
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    os.makedirs(user_folder, exist_ok=True)

    # Generate safe filename with timestamp to prevent overwrites
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_name, ext = os.path.splitext(file.filename)
    safe_filename = f"{original_name}_{timestamp}{ext}"

    file_path = os.path.join(user_folder, safe_filename)
    file.save(file_path)

    return jsonify({
        "status": "file uploaded",
        "file_name": safe_filename,
        "file_path": f"/{user_id}/{safe_filename}"
    }), 200


@app.route("/file/<user_id>/<filename>", methods=["GET"])
def serve_general_file(user_id, filename):
    """Serve any uploaded file from the user's folder."""
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    if not os.path.exists(os.path.join(user_folder, filename)):
        return jsonify({"error": "file not found"}), 404
    return send_from_directory(user_folder, filename)


# =========================================================
# 🧑‍💼 ADMIN CRUD ROUTES FOR GENERAL FILES
# =========================================================

# 1️⃣ Get all files for all users
@app.route("/admin/files", methods=["GET"])
def get_all_files():
    all_files = {}
    for user in os.listdir(UPLOAD_FOLDER):
        user_folder = os.path.join(UPLOAD_FOLDER, user)
        if os.path.isdir(user_folder):
            files = [f for f in os.listdir(user_folder)
                     if not f.endswith(".mp4") and not f.endswith(".webm")]
            if files:
                all_files[user] = files
    return jsonify(all_files), 200


# 2️⃣ Get all general files for a specific user
@app.route("/admin/files/<user_id>", methods=["GET"])
def get_user_files(user_id):
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    if not os.path.exists(user_folder):
        return jsonify({"files": []}), 200
    files = [f for f in os.listdir(user_folder)
             if not f.endswith(".mp4") and not f.endswith(".webm")]
    return jsonify({"user": user_id, "files": files}), 200


# 3️⃣ Delete a specific general file of a user
@app.route("/admin/file/<user_id>/<filename>", methods=["DELETE"])
def delete_user_file(user_id, filename):
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    file_path = os.path.join(user_folder, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({"status": "deleted", "file": filename}), 200
    return jsonify({"error": "file not found"}), 404


# 4️⃣ Delete all general files for a specific user
@app.route("/admin/files/<user_id>", methods=["DELETE"])
def delete_all_user_files(user_id):
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    if not os.path.exists(user_folder):
        return jsonify({"status": "no files found"}), 200

    deleted = []
    for f in os.listdir(user_folder):
        if not f.endswith(".mp4") and not f.endswith(".webm"):
            try:
                os.remove(os.path.join(user_folder, f))
                deleted.append(f)
            except Exception as e:
                print(f"Failed to delete {f}: {e}")

    return jsonify({"status": "deleted", "deleted_files": deleted}), 200


# 5️⃣ Delete all general files of all users
@app.route("/admin/files", methods=["DELETE"])
def delete_all_general_files():
    deleted = {}
    for user in os.listdir(UPLOAD_FOLDER):
        user_folder = os.path.join(UPLOAD_FOLDER, user)
        if os.path.isdir(user_folder):
            deleted[user] = []
            for f in os.listdir(user_folder):
                if not f.endswith(".mp4") and not f.endswith(".webm"):
                    try:
                        os.remove(os.path.join(user_folder, f))
                        deleted[user].append(f)
                    except Exception as e:
                        print(f"Failed to delete {f}: {e}")
    return jsonify({"status": "deleted all general files", "deleted_files": deleted}), 200


# 6️⃣ Search general files (by partial name match)
@app.route("/admin/search/files", methods=["GET"])
def search_general_files():
    query = request.args.get("q", "").lower()
    matched_files = {}
    for user in os.listdir(UPLOAD_FOLDER):
        user_folder = os.path.join(UPLOAD_FOLDER, user)
        if os.path.isdir(user_folder):
            files = [f for f in os.listdir(user_folder)
                     if query in f.lower() and not f.endswith(".mp4") and not f.endswith(".webm")]
            if files:
                matched_files[user] = files
    return jsonify({"query": query, "matched_files": matched_files}), 200


# =========================================================
# 📄 RESUME & CANDIDATE MANAGEMENT ENDPOINTS
# =========================================================

# In-memory storage for candidates and interviews (replace with DB later)
candidates_db = {}
interviews_db = {}

@app.route("/api/resumes/upload", methods=["POST"])
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


@app.route("/api/candidates", methods=["GET"])
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


@app.route("/api/candidates/user/<user_id>", methods=["GET"])
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


@app.route("/api/candidates/<candidate_id>", methods=["GET"])
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


@app.route("/api/candidates/<candidate_id>/schedule", methods=["POST"])
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


@app.route("/api/interviews/<interview_id>", methods=["GET"])
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


@app.route("/api/interviews/<interview_id>/status", methods=["PATCH"])
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


@app.route("/api/interviews/<interview_id>/transcript", methods=["POST"])
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


@app.route("/api/interviews/user/<user_id>", methods=["GET"])
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


@app.route("/api/interviews", methods=["GET"])
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


if __name__ == "__main__":
    app.run(
        host=str(os.getenv("HOST", "0.0.0.0")),
        port=int(os.getenv("PORT", 8080)),
        # ssl_context=(os.getenv("SSL_CERT", "cert.pem"), os.getenv("SSL_KEY", "key.pem"))
    )



# # Use the below command to generate self-signed certs for testing
# # openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout key.pem -out cert.pem -subj "/CN=192.168.1.100"
