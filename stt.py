# stt.py
import os
import json
import csv
import base64
import re
import logging
from datetime import datetime
from vosk import Model, KaldiRecognizer

# --------------------------
# --- STT Setup ---
# --------------------------
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models/vosk-model-small-en-us-0.15")
if not os.path.exists(MODEL_PATH):
    raise Exception(f"Vosk model not found at {MODEL_PATH}. Please download and unzip it.")

logging.info("Loading Vosk STT model...")
stt_model = Model(MODEL_PATH)
logging.info("Vosk STT model loaded")

BASE_DIR = "transcriptions"
os.makedirs(BASE_DIR, exist_ok=True)

sessions = {}

# --------------------------
# --- Session Management ---
# --------------------------
def get_candidate_dir(candidate_id):
    path = os.path.join(BASE_DIR, candidate_id)
    os.makedirs(path, exist_ok=True)
    return path

def get_session_filenames(candidate_id):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = get_candidate_dir(candidate_id)
    return {
        "csv": os.path.join(folder, f"{candidate_id}_{ts}.csv"),
        "json": os.path.join(folder, f"{candidate_id}_{ts}.json"),
        "txt": os.path.join(folder, f"{candidate_id}_{ts}.txt")
    }

def init_session_files(session):
    filenames = get_session_filenames(session["candidate_id"])
    session["files"] = filenames
    with open(filenames["csv"], "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "text"])
        writer.writeheader()
    with open(filenames["json"], "w", encoding="utf-8") as f:
        json.dump([], f)
    with open(filenames["txt"], "w", encoding="utf-8") as f:
        f.write("")
    logging.info(f"Initialized session files for candidate {session['candidate_id']}")

def append_to_session_files(session, record):
    files = session.get("files")
    if not files:
        logging.warning(f"No files initialized for candidate {session.get('candidate_id')}")
        return
    with open(files["csv"], "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "text"])
        writer.writerow({"timestamp": record["timestamp"], "text": record["text"]})
    with open(files["json"], "r+", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
        data.append(record)
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()
    with open(files["txt"], "a", encoding="utf-8") as f:
        f.write(record["text"] + " ")

def append_sentence(session, text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    for s in sentences:
        if s:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            record = {"candidate_id": session["candidate_id"], "timestamp": timestamp, "text": s}
            session["records"].append(record)
            session["full_text"] += " " + s
            append_to_session_files(session, record)
    return session["full_text"]

def create_session(sid):
    sessions[sid] = {"recognizer": KaldiRecognizer(stt_model, 16000), "candidate_id": None, "full_text": "", "records": [], "files": {}}
    return sessions[sid]
