# Offline TTS + STT Flask Application

This project is a **combined offline Text-to-Speech (TTS) and Speech-to-Text (STT) web application** using Flask.  

It provides:  

- **TTS:** Convert text to speech with multiple voices using Mozilla TTS.  
- **STT:** Real-time speech-to-text transcription using Vosk.  
- **Logging:** All TTS inputs and STT transcriptions are saved to files.  
- **Web Interface:** Separate web pages for TTS and STT.  
- **WebSocket Support:** Real-time streaming STT updates.

---

## Project Structure

```

project_root/
│
├─ app.py                     # Main Flask + SocketIO app
├─ tts.py                     # TTS module
├─ stt.py                     # STT module
├─ env/                       # Python virtual environment
├─ logs/                      # Server logs (timestamped)
├─ tts_text_logs/             # Saved TTS input text files
├─ transcriptions/            # Saved STT transcripts
├─ models/                    # Vosk STT model folder
│   └─ vosk-model-small-en-us-0.15/
├─ templates/
│   ├─ tts_index.html         # TTS web page
│   └─ stt_index.html         # STT web page
├─ static/                    # Optional static files (CSS, JS)
└─ run_app.sh                 # Script to run the app with logging

````

---

## Requirements

- Python 3.10+  
- pip packages (install in virtual environment):

```bash
pip install flask flask-socketio numpy scipy TTS vosk
````

* **Vosk model:**
  Download from [Vosk models](https://alphacephei.com/vosk/models) and extract to `models/vosk-model-small-en-us-0.15`.

---

## Usage

### 1. Activate virtual environment and install dependencies

```bash
python -m venv env
source env/bin/activate          # Mac/Linux
# env\Scripts\activate         # Windows
pip install -r requirements.txt
```

### 2. Run the app

```bash
chmod +x run_app.sh
./run_app.sh
```

* Server runs on: `http://localhost:8000`
* Logs are saved in `logs/server_YYYYMMDD_HHMMSS.log`

---

## Endpoints

### TTS

* `/tts` → Web page for text-to-speech
* `/tts/speak` → API endpoint (POST)

**POST JSON Example:**

```json
{
    "text": "Hello world!",
    "speaker": "p225"
}
```

* Audio returned as WAV
* Input text is saved in `tts_text_logs/`

---

### STT

* `/stt` → Web page for live STT

* Uses **WebSocket** for real-time transcription

* Candidate ID is required before sending audio chunks

* Transcriptions saved in `transcriptions/<candidate_id>/` as CSV, JSON, and TXT

---

## Logging

* **Server logs:** `logs/server_YYYYMMDD_HHMMSS.log`
* **TTS input text:** `tts_text_logs/tts_YYYYMMDD_HHMMSS.txt`
* **STT transcripts:** `transcriptions/<candidate_id>/`

---

## Scripts

* `run_app.sh` → Starts the Flask + SocketIO server and saves console logs to the `logs/` folder
* Optional: You can create scripts to automatically archive TTS input logs or STT transcripts

---

## Notes

* Ensure the **Vosk model path** is correct: `models/vosk-model-small-en-us-0.15`
* Always submit **candidate ID** on the STT page before recording
* TTS supports multiple speakers from Mozilla TTS
* Web pages are in the `templates/` folder; static files like JS/CSS should go into `static/`

---

## License

This project is free to use and modify.
