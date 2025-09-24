# STT & TTS Flask Web Application

This project implements a real-time **Speech-to-Text (STT)** and **Text-to-Speech (TTS)** system using Flask and WebSocket (`Flask-SocketIO`). It allows users to transcribe audio in real-time and synthesize text into speech with multiple speakers using Mozilla TTS.

---

## Features

### STT Service

* Real-time speech transcription using **Vosk**.
* WebSocket-based streaming of audio chunks.
* Incremental partial results and final transcription.
* Session management per client.
* Transcriptions saved as:

  * CSV
  * JSON
  * Plain text (`.txt`)
* Automatic timestamps for all transcriptions.
* Logging of client connections, disconnections, and transcription events.

### TTS Service

* Multi-speaker **Mozilla TTS (VCTK/VITS)** model.
* Generate high-quality WAV audio from text.
* Supports selecting different speakers.
* Audio sent directly to client via Flask endpoint.
* Logging of text requests, audio generation, and errors.

---

## Requirements

* Python 3.10+
* Virtual environment recommended

### Python Packages

All required packages are in `requirements.txt`:

```
Flask
Flask-SocketIO
python-socketio
eventlet
vosk
numpy
scipy
TTS
```

Additional system requirements:

* `ffmpeg` (for TTS backend)
* `moreutils` if using timestamped logging in bash scripts

---

## Setup

1. **Clone repository**

```bash
git clone <repo_url>
cd STT_and_TTS_services
```

2. **Create virtual environment**

```bash
python3.10 -m venv env
source env/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Download Vosk model** (STT)

```bash
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d Offline_STT_Code_With_Live_Streaming/models/
```

---

## Usage

### Run servers individually

#### TTS Server

```bash
python Local_TTS_Code/app.py
```

* Access: `http://localhost:8000`
* Endpoint: `/speak` (POST)
  JSON body:

```json
{
  "text": "Hello world",
  "speaker": "p225"
}
```

#### STT Server

```bash
python Offline_STT_Code_With_Live_Streaming/app.py
```

* WebSocket server: port `8002`
* Connect using client-side JS or Python WebSocket client.
* Audio chunks sent as base64.
* Partial and final transcription streamed back to client.

### Run both via `run_all.sh`

```bash
./run_all.sh
```

* Automatically creates `logs/` directory.
* Saves logs with timestamps for each server.

---

## Logging

* **TTS**: Logs requests, audio generation, errors.
* **STT**: Logs client connections, disconnections, transcription events.
* Timestamped logs can be found in `logs/` (if using `run_all.sh`).

---

## File Structure

```
STT_and_TTS_services/
├── Local_TTS_Code/
│   ├── app.py          # TTS Flask server
│   └── ...             # Other TTS-related files
├── Offline_STT_Code_With_Live_Streaming/
│   ├── app.py          # STT Flask+WebSocket server
│   └── models/         # Vosk model directory
├── logs/               # Automatically created log files
├── requirements.txt
├── run_all.sh          # Bash script to start both servers with logging
└── README.md
```

---

## Example Client Code

### TTS Request (Python)

```python
import requests

data = {
    "text": "Hello, this is a test.",
    "speaker": "p225"
}
response = requests.post("http://localhost:8000/speak", json=data)
with open("output.wav", "wb") as f:
    f.write(response.content)
```

### STT WebSocket Client (JavaScript)

```javascript
const socket = io('http://localhost:8002');

socket.on('connect', () => {
    console.log('Connected to STT server');
    socket.emit('candidate', { candidate_id: 'user123' });
});

socket.on('transcription', (data) => {
    console.log('Final text:', data.text);
});

socket.on('partial_transcription', (data) => {
    console.log('Partial text:', data.text);
});

// Example: send base64 audio chunk
// socket.emit('audio_chunk', { chunk: base64Audio });
```

---

## Notes

* Ensure Python version compatibility: **3.10 recommended**.
* Use virtual environments to prevent package conflicts.
* The STT server saves session transcriptions with **timestamps** for traceability.
* For production deployment, replace Flask dev server with **WSGI server** (e.g., Gunicorn).

---

## License

MIT License (or your preferred license)
