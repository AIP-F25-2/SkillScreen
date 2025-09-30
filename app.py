# app.py
import logging
from flask import Flask, render_template, request, send_file, redirect
from flask_socketio import SocketIO, emit

from tts import synthesize_speech, speakers
from stt import sessions, create_session, init_session_files, append_sentence, stt_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# --------------------------
# --- Routes ---
# --------------------------
@app.route("/")
def home():
    return redirect("/tts")

@app.route("/tts")
def tts_index():
    return render_template("tts_index.html", speakers=speakers)

@app.route("/tts/speak", methods=["POST"])
def tts_speak_route():
    data = request.get_json()
    text = data.get("text")
    speaker = data.get("speaker")
    try:
        wav_io = synthesize_speech(text, speaker)
        return send_file(wav_io, mimetype="audio/wav", as_attachment=False)
    except Exception as e:
        logging.error(f"TTS Error: {e}")
        return {"error": str(e)}, 500

@app.route("/stt")
def stt_index():
    return render_template("stt_index.html")

# --------------------------
# --- SocketIO Handlers ---
# --------------------------
@socketio.on('connect')
def handle_connect(auth):
    sid = request.sid
    logging.info(f"Client connected: {sid}")
    create_session(sid)
    emit('connected', {'data': 'Connected'})

@socketio.on('candidate')
def handle_candidate(data):
    sid = request.sid
    candidate_id = data.get("candidate_id")
    session = sessions.get(sid)
    if not candidate_id:
        emit('candidate_received', {'status': 'error', 'message': 'Candidate ID missing'})
        return
    if session:
        session["candidate_id"] = candidate_id
        init_session_files(session)
        logging.info(f"Candidate ID received: {candidate_id} (SID: {sid})")
    emit('candidate_received', {'status': 'ok'})

@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    sid = request.sid
    session = sessions.get(sid)
    if not session or not session.get("candidate_id"):
        logging.warning(f"Audio chunk received before candidate ID for SID: {sid}")
        return

    rec = session["recognizer"]
    import base64, json
    audio_bytes = base64.b64decode(data['chunk'])
    try:
        if rec.AcceptWaveform(audio_bytes):
            res = json.loads(rec.Result())
            text = res.get("text", "")
            if text:
                full_text = append_sentence(session, text)
                emit('transcription', {'text': full_text})
        else:
            res = json.loads(rec.PartialResult())
            partial = res.get("partial", "")
            if partial:
                emit('partial_transcription', {'text': session["full_text"] + " " + partial})
    except Exception as e:
        logging.error(f"STT Error for {session.get('candidate_id')} ({sid}): {e}")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    session = sessions.pop(sid, None)
    if session:
        logging.info(f"Client disconnected: {session['candidate_id']} ({sid})")
    else:
        logging.info(f"Unknown client disconnected: {sid}")

@socketio.on('reset')
def reset_recognizer():
    sid = request.sid
    session = sessions.get(sid)
    if session:
        from vosk import KaldiRecognizer
        session["recognizer"] = KaldiRecognizer(stt_model, 16000)
        session["full_text"] = ""
        session["records"] = []
        emit('reset_done', {'status': 'Recognizer reset'})
        logging.info(f"Recognizer reset for candidate {session['candidate_id']} ({sid})")

# --------------------------
# --- Run Server ---
# --------------------------
if __name__ == "__main__":
    logging.info("Starting combined TTS/STT server on port 8000...")
    socketio.run(app, host="0.0.0.0", port=8000, debug=True, use_reloader=False)
