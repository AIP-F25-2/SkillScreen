from flask import Flask, render_template, request, send_file
from TTS.api import TTS
import numpy as np
import scipy.io.wavfile as wav
import io
import warnings
import logging

# --- Warnings ---
warnings.filterwarnings("ignore", category=UserWarning, module="multiprocessing")

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# --- Flask app ---
app = Flask(__name__)

# --- Load Mozilla TTS multi-speaker model ---
logging.info("Loading TTS model...")
tts = TTS(model_name="tts_models/en/vctk/vits")
speakers = tts.speakers
logging.info(f"TTS model loaded with {len(speakers)} speakers")

@app.route("/")
def index():
    logging.info("Serving index page")
    return render_template("index.html", speakers=speakers)

@app.route("/speak", methods=["POST"])
def speak():
    data = request.get_json()
    text = data.get("text")
    speaker = data.get("speaker")

    if not text:
        logging.warning("No text provided in /speak request")
        return {"error": "No text provided"}, 400

    logging.info(f"Generating audio for speaker '{speaker}': {text[:50]}{'...' if len(text) > 50 else ''}")
    try:
        # Generate audio
        audio = tts.tts(text, speaker=speaker)
        sample_rate = tts.synthesizer.output_sample_rate

        # Convert list to NumPy array
        audio_np = np.array(audio)

        # Save to in-memory WAV
        wav_io = io.BytesIO()
        wav.write(wav_io, sample_rate, (audio_np * 32767).astype(np.int16))
        wav_io.seek(0)

        logging.info("Audio generation successful")
        return send_file(
            wav_io,
            mimetype="audio/wav",
            as_attachment=False
        )

    except Exception as e:
        logging.error(f"Error generating audio: {e}")
        return {"error": str(e)}, 500

if __name__ == "__main__":
    logging.info("Starting TTS server on port 8000...")
    app.run(host="0.0.0.0", port=8000, debug=True)
