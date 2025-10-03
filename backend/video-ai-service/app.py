from flask import Flask, jsonify, request, send_from_directory, render_template
from services.video_processor import VideoProcessor
import os
from flask_cors import CORS
from dotenv import load_dotenv
import shutil

# Load env
load_dotenv()

app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "changeme")

# Initialize processor with .env configs
processor = VideoProcessor()

# ------------------ API Routes ------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process_video', methods=['POST'])
def process_video():
    data = request.get_json(force=True)
    video_url = data.get("video_url")

    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400

    try:
        annotated_video, report = processor.process_video(video_url)

        # relative URL for serving back
        rel_path = os.path.relpath(annotated_video, processor.processed_folder)
        return jsonify({
            "annotated_video_url": f"/api/videos/{rel_path}",
            "report": report
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Serve processed videos
@app.route('/api/videos/<path:filename>', methods=['GET'])
def get_processed_video(filename):
    return send_from_directory(processor.processed_folder, filename)


# List videos by user (existing)
@app.route('/api/list_videos_by_user', methods=['GET'])
def list_videos_by_user():
    users = {}
    for root, dirs, files in os.walk(processor.processed_folder):
        for f in files:
            if f.lower().endswith(".mp4"):
                rel_path = os.path.relpath(os.path.join(root, f), processor.processed_folder)
                parts = rel_path.split(os.sep)
                if len(parts) < 2:
                    continue
                user_id = parts[0]
                users.setdefault(user_id, []).append(f"/api/videos/{rel_path}")
    return jsonify(users)


# ------------------ Additional Endpoints ------------------

# 1. Get videos of a particular user
@app.route('/api/videos/<user_id>', methods=['GET'])
def get_videos_by_user(user_id):
    user_folder = os.path.join(processor.processed_folder, user_id)
    if not os.path.exists(user_folder):
        return jsonify({"error": f"No videos found for user {user_id}"}), 404

    videos = []
    for root, dirs, files in os.walk(user_folder):
        for f in files:
            if f.lower().endswith(".mp4"):
                rel_path = os.path.relpath(os.path.join(root, f), processor.processed_folder)
                videos.append(f"/api/videos/{rel_path}")
    return jsonify({"user_id": user_id, "videos": videos})


# 2. Get all videos grouped by user
@app.route('/api/all_videos_by_user', methods=['GET'])
def all_videos_by_user():
    users = {}
    for root, dirs, files in os.walk(processor.processed_folder):
        for f in files:
            if f.lower().endswith(".mp4"):
                rel_path = os.path.relpath(os.path.join(root, f), processor.processed_folder)
                parts = rel_path.split(os.sep)
                if len(parts) < 2:
                    continue
                user_id = parts[0]
                users.setdefault(user_id, []).append(f"/api/videos/{rel_path}")
    return jsonify(users)


# 3. Delete a single video
@app.route('/api/delete_video', methods=['POST'])
def delete_video():
    data = request.get_json(force=True)
    video_url = data.get("video_url")
    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400

    # Strip '/api/videos/' prefix if present
    if video_url.startswith("/api/videos/"):
        video_url = video_url[len("/api/videos/"):]

    file_path = os.path.join(processor.processed_folder, video_url.lstrip("/"))
    if not os.path.exists(file_path):
        return jsonify({"error": "File does not exist"}), 404

    try:
        os.remove(file_path)
        return jsonify({"status": "success", "deleted": video_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Delete all videos for a user
@app.route('/api/users/<user_id>/videos', methods=['DELETE'])
def delete_user_videos(user_id):
    user_dir = os.path.join(processor.processed_folder, user_id)
    if not os.path.exists(user_dir):
        return jsonify({"error": f"User {user_id} not found"}), 404

    deleted = []
    for root, dirs, files in os.walk(user_dir):
        for f in files:
            if f.lower().endswith(".mp4"):
                file_path = os.path.join(root, f)
                try:
                    os.remove(file_path)
                    deleted.append(f)
                except Exception as e:
                    return jsonify({"error": str(e)}), 500

    return jsonify({"message": f"Deleted {len(deleted)} videos for user {user_id}", "deleted_files": deleted})


# 5. Check if a video exists
@app.route('/api/video_exists', methods=['GET'])
def video_exists():
    video_url = request.args.get("video_url")
    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400

    file_path = os.path.join(processor.processed_folder, video_url.lstrip("/"))
    return jsonify({"exists": os.path.exists(file_path)})


# 6. List all users
@app.route('/api/list_users', methods=['GET'])
def list_users():
    users = [d for d in os.listdir(processor.processed_folder)
             if os.path.isdir(os.path.join(processor.processed_folder, d))]
    return jsonify(users)


# Get all videos for a specific user
@app.route('/api/users/<user_id>/videos', methods=['GET'])
def get_user_videos(user_id):
    user_dir = os.path.join(processor.processed_folder, user_id)
    if not os.path.exists(user_dir):
        return jsonify({"error": f"User {user_id} not found"}), 404

    videos = []
    for root, dirs, files in os.walk(user_dir):
        for f in files:
            if f.lower().endswith(".mp4"):
                rel_path = os.path.relpath(os.path.join(root, f), processor.processed_folder)
                videos.append(f"/api/videos/{rel_path}")
    return jsonify({"user": user_id, "videos": videos})


# Delete a single processed video
@app.route('/api/videos/<user_id>/<video_name>', methods=['DELETE'])
def delete_video_by_user_id_and_video_name(user_id, video_name):
    video_path = os.path.join(processor.processed_folder, user_id, video_name)
    if not os.path.exists(video_path):
        return jsonify({"error": "Video not found"}), 404
    try:
        os.remove(video_path)
        return jsonify({"message": f"Deleted video {video_name} for user {user_id}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500




# ------------------ Search videos by filename ------------------
@app.route('/api/search_videos', methods=['GET'])
def search_videos():
    query = request.args.get("q", "").lower()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    results = {}
    for root, dirs, files in os.walk(processor.processed_folder):
        for f in files:
            if f.lower().endswith(".mp4") and query in f.lower():
                rel_path = os.path.relpath(os.path.join(root, f), processor.processed_folder)
                parts = rel_path.split(os.sep)
                if len(parts) < 2:
                    continue  # skip videos not under user folder
                user_id = parts[0]
                results.setdefault(user_id, []).append(f"/api/videos/{rel_path}")

    return jsonify(results)


# ------------------ Main ------------------
if __name__ == '__main__':
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", 5010))
    debug = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")
    app.run(host=host, port=port, debug=debug)