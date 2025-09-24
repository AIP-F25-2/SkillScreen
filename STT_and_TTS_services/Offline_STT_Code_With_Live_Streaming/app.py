from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from vosk import Model, KaldiRecognizer
import base64
import json
from datetime import datetime
import os
import re
import csv
import logging
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="multiprocessing")

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# --- Flask setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Vosk model ---
model = Model("Offline_STT_Code_With_Live_Streaming/models/vosk-model-small-en-us-0.15")

# --- Save directory ---
BASE_DIR = "transcriptions"
os.makedirs(BASE_DIR, exist_ok=True)

# --- Session storage ---
sessions = {}

# --- Helper: get candidate folder ---
def get_candidate_dir(candidate_id):
    path = os.path.join(BASE_DIR, candidate_id)
    os.makedirs(path, exist_ok=True)
    return path

# --- Helper: generate timestamped session filename ---
def get_session_filenames(candidate_id):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = get_candidate_dir(candidate_id)
    return {
        "csv": os.path.join(folder, f"{candidate_id}_{ts}.csv"),
        "json": os.path.join(folder, f"{candidate_id}_{ts}.json"),
        "txt": os.path.join(folder, f"{candidate_id}_{ts}.txt")
    }

# --- Initialize session files ---
def init_session_files(session):
    filenames = get_session_filenames(session["candidate_id"])
    session["files"] = filenames
    # CSV header
    with open(filenames["csv"], "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "text"])
        writer.writeheader()
    # Empty JSON
    with open(filenames["json"], "w", encoding="utf-8") as f:
        json.dump([], f)
    # Empty TXT
    with open(filenames["txt"], "w", encoding="utf-8") as f:
        f.write("")
    logging.info(f"Initialized session files for candidate {session['candidate_id']}")

# --- Helper: append to session files ---
def append_to_session_files(session, record):
    # CSV
    with open(session["files"]["csv"], "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "text"])
        writer.writerow({"timestamp": record["timestamp"], "text": record["text"]})
    # JSON
    with open(session["files"]["json"], "r+", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
        data.append(record)
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()
    # TXT
    with open(session["files"]["txt"], "a", encoding="utf-8") as f:
        f.write(record["text"] + " ")

# --- Helper: sentence segmentation and append ---
def append_sentence(session, text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    for s in sentences:
        if s:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            record = {
                "candidate_id": session["candidate_id"],
                "timestamp": timestamp,
                "text": s
            }
            session["records"].append(record)
            session["full_text"] += " " + s
            append_to_session_files(session, record)
            logging.info(f"Appended sentence for candidate {session['candidate_id']}: {s}")
    return session["full_text"]

# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html")

# --- Client connected ---
@socketio.on('connect')
def handle_connect(auth):
    sid = request.sid
    logging.info(f"Client connected: {sid}")
    sessions[sid] = {
        "recognizer": KaldiRecognizer(model, 16000),
        "candidate_id": None,
        "full_text": "",
        "records": [],
        "files": {}
    }
    emit('connected', {'data': 'Connected'})

# --- Receive candidate ID ---
@socketio.on('candidate')
def handle_candidate(data):
    sid = request.sid
    candidate_id = data.get("candidate_id")
    if sid in sessions:
        sessions[sid]["candidate_id"] = candidate_id
        init_session_files(sessions[sid])
        logging.info(f"Candidate ID received: {candidate_id} (SID: {sid})")
    emit('candidate_received', {'status': 'ok'})

# --- Audio chunks ---
@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    sid = request.sid
    session = sessions.get(sid)
    if not session:
        logging.warning(f"Received audio chunk for unknown session: {sid}")
        return

    rec = session["recognizer"]
    audio_bytes = base64.b64decode(data['chunk'])

    try:
        if rec.AcceptWaveform(audio_bytes):
            res = json.loads(rec.Result())
            text = res.get("text", "")
            if text:
                full_text = append_sentence(session, text)
                emit('transcription', {'text': full_text})
                logging.info(f"Final transcription for {session['candidate_id']}: {text}")
        else:
            res = json.loads(rec.PartialResult())
            partial = res.get("partial", "")
            if partial:
                emit('partial_transcription', {'text': session["full_text"] + " " + partial})
                logging.debug(f"Partial transcription for {session['candidate_id']}: {partial}")
    except Exception as e:
        logging.error(f"Error processing audio chunk for {session['candidate_id']} ({sid}): {e}")

# --- Disconnect ---
@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    session = sessions.pop(sid, None)
    if session:
        logging.info(f"Client disconnected: {session['candidate_id']} ({sid})")
    else:
        logging.info(f"Unknown client disconnected: {sid}")

# --- Reset recognizer ---
@socketio.on('reset')
def reset_recognizer():
    sid = request.sid
    session = sessions.get(sid)
    if session:
        session["recognizer"] = KaldiRecognizer(model, 16000)
        session["full_text"] = ""
        session["records"] = []
        emit('reset_done', {'status': 'Recognizer reset'})
        logging.info(f"Recognizer reset for candidate {session['candidate_id']} ({sid})")

# --- Run server ---
if __name__ == "__main__":
    logging.info("Starting STT WebSocket server on port 8002...")
    socketio.run(app, host="0.0.0.0", port=8002)
