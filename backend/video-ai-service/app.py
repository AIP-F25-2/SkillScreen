from flask import Flask, Response, jsonify, request
from flask_socketio import SocketIO
from services.video_recorder import start_recording, stop_recording, get_latest_frame
from services.video_processor import VideoProcessor
import os
import cv2
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Secret key from .env
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "changeme")

socketio = SocketIO(app, cors_allowed_origins="*")
processor = VideoProcessor()

last_recording_path = None

# Live video feed (MJPEG)
@app.route('/api/video_feed')
def video_feed():
    def generate():
        while True:
            frame = get_latest_frame()
            if frame is None:
                continue
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Start recording
@app.route('/api/start', methods=['POST'])
def start():
    global last_recording_path
    data = request.get_json(force=True)
    filename = data.get("filename", "recording")
    last_recording_path = start_recording(filename)
    return jsonify({"status": "started", "file_path": os.path.abspath(last_recording_path)})


# Stop recording
@app.route('/api/stop', methods=['POST'])
def stop():
    stop_recording()
    return jsonify({
        "status": "stopped",
        "file_path": os.path.abspath(last_recording_path) if last_recording_path else None
    })


# Process video
@app.route('/api/process_video', methods=['POST'])
def process_video():
    data = request.get_json(force=True)
    video_url = data.get("video_url")

    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400
    if not os.path.exists(video_url):
        return jsonify({"error": f"Video file does not exist: {video_url}"}), 400

    try:
        annotated_video, report = processor.process_video(video_url)
        return jsonify({
            "annotated_video_url": os.path.abspath(annotated_video),
            "report": report
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 8000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")
    socketio.run(app, host=host, port=port, debug=debug)
