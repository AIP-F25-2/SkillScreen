Offline Live Streaming STT Service

This project provides an offline Speech-to-Text (STT) service 
using Vosk for real-time transcription with the following features:


1   Live streaming transcription from the client browser.
2   Candidate-based sessions with per-session data storage.
3   Text files updated incrementally during the session to prevent data loss.
4   Data saved in CSV, JSON, and plain TXT formats for later processing.
5   Sentence-based segmentation for clean transcription.


Features
1   Offline STT: Uses Vosk models for English.
2   Live streaming: Text appears live in the frontend as the user speaks.
3   Per-candidate session: Each candidate has a dedicated folder for all their sessions.
4   Incremental file saving: Saves text after each sentence to prevent data loss if the session is interrupted.
5   Multi-format storage: CSV, JSON, and TXT files.
6   Timestamped session files: Each session file includes the candidate ID and start timestamp.


Project Structure

Offline_STT_Code_With_Live_Streaming/
│
├── app.py                # Flask + SocketIO backend
├── requirements.txt      # Python dependencies
├── templates/
│   └── index.html        # Frontend
├── static/
│   └── script.js         # JS for capturing microphone audio
├── models/
│   └── vosk-model-small-en-us-0.15/   # Downloaded Vosk model
└── transcriptions/       # Saved transcription folders per candidate



Setup Instructions

1. Clone and create environment

git clone <repo-url>
cd Offline_STT_Code_With_Live_Streaming
python -m venv env
source env/bin/activate   # Linux/macOS
# env\Scripts\activate    # Windows

2. Install dependencies

pip install -r requirements.txt
requirements.txt should contain:
flask
flask-socketio
vosk
numpy

3. Download Vosk Model

Download a small English model:

mkdir -p models
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
Make sure the folder structure is:
models/vosk-model-small-en-us-0.15/

4. Run the server

python app.py
Server runs on:
http://127.0.0.1:8002

5. Frontend

Open templates/index.html in a browser.

Features:
    Input candidate ID.
    Start recording microphone.
    Live streaming transcription.
    Session ends automatically on disconnect or page close.

6. Transcriptions Storage

All files saved under:
transcriptions/<candidate_id>/

Each session generates:
<candidate_id>_<YYYYMMDD_HHMMSS>.csv
<candidate_id>_<YYYYMMDD_HHMMSS>.json
<candidate_id>_<YYYYMMDD_HHMMSS>.txt
CSV: timestamp + sentence text
JSON: array of objects with timestamp + text
TXT: concatenated plain text

7. Notes

Ensure microphone access is allowed in the browser.
Closing the browser or stopping the session will save the latest transcription incrementally.
You can reset the recognizer for a new session via the reset SocketIO event.