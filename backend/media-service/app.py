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

    chunk_path = os.path.join(user_folder, file.filename)
    file.save(chunk_path)

    return jsonify({"status": "chunk saved"}), 200


@app.route("/finalize_upload", methods=["POST"])
def finalize_upload():
    import time
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    if not os.path.exists(user_folder):
        return jsonify({"error": "No chunks found"}), 400

    time.sleep(0.2)

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

if __name__ == "__main__":
    app.run(
        host=str(os.getenv("SERVER_HOST", "0.0.0.0")),
        port=int(os.getenv("SERVER_PORT", 5004)),
        # ssl_context=(os.getenv("SSL_CERT", "cert.pem"), os.getenv("SSL_KEY", "key.pem"))
    )    
# # Use the below command to generate self-signed certs for testing
# # openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout key.pem -out cert.pem -subj "/CN=192.168.1.100"
