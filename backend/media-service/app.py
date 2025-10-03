import os
import subprocess
from flask import Flask, request, jsonify, send_from_directory, render_template
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

app = Flask(__name__)

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

    # Save chunk with filename sent by frontend (overwrite if exists)
    chunk_filename = file.filename
    chunk_path = os.path.join(user_folder, chunk_filename)
    file.save(chunk_path)

    return jsonify({"status": "chunk saved", "chunk": chunk_filename}), 200


@app.route("/reset_chunks", methods=["POST"])
def reset_chunks():
    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    if os.path.exists(user_folder):
        for f in os.listdir(user_folder):
            if f.endswith(".webm"):
                try:
                    os.remove(os.path.join(user_folder, f))
                except Exception as e:
                    print(f"Failed to delete {f}: {e}")

    return jsonify({"status": "chunks reset"}), 200


@app.route("/finalize_upload", methods=["POST"])
def finalize_upload():
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    if not os.path.exists(user_folder):
        return jsonify({"error": "No chunks found"}), 400

    # Sort chunks numerically
    chunks = sorted([f for f in os.listdir(user_folder) if f.endswith(".webm")])
    if not chunks:
        return jsonify({"error": "No .webm chunks found"}), 400

    merged_webm = os.path.join(user_folder, "merged.webm")
    with open(merged_webm, "wb") as outfile:
        for fname in chunks:
            chunk_path = os.path.join(user_folder, fname)
            with open(chunk_path, "rb") as infile:
                outfile.write(infile.read())

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_mp4 = os.path.join(user_folder, f"{user_id}_{timestamp}.mp4")

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", merged_webm,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
                "-movflags", "+faststart",
                "-fflags", "+genpts",
                final_mp4
            ],
            check=True
        )
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"ffmpeg failed: {e}"}), 500

    # Cleanup chunks and intermediate merged file
    for fname in chunks + ["merged.webm"]:
        path_to_delete = os.path.join(user_folder, fname)
        try:
            os.remove(path_to_delete)
        except Exception as e:
            print(f"Failed to delete {path_to_delete}: {e}")

    return jsonify({
        "status": "done",
        "file": f"/video/{user_id}/{os.path.basename(final_mp4)}"
    }), 200


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


if __name__ == "__main__":
    app.run(
        host=str(os.getenv("SERVER_HOST", "0.0.0.0")),
        port=int(os.getenv("SERVER_PORT", 5004)),
        # ssl_context=(os.getenv("SSL_CERT", "cert.pem"), os.getenv("SSL_KEY", "key.pem"))
    )



# # Use the below command to generate self-signed certs for testing
# # openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout key.pem -out cert.pem -subj "/CN=192.168.1.100"
