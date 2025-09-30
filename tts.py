# tts.py
import io
import numpy as np
import logging
from flask import send_file
from TTS.api import TTS
import scipy.io.wavfile as wav

logging.info("Loading TTS model...")
tts = TTS(model_name="tts_models/en/vctk/vits")
speakers = tts.speakers
logging.info(f"TTS model loaded with {len(speakers)} speakers")

def synthesize_speech(text: str, speaker: str):
    """
    Convert text to speech and return as WAV BytesIO object
    """
    if not text:
        raise ValueError("No text provided for TTS")
    
    audio = tts.tts(text, speaker=speaker)
    sample_rate = tts.synthesizer.output_sample_rate
    audio_np = np.array(audio)

    wav_io = io.BytesIO()
    wav.write(wav_io, sample_rate, (audio_np * 32767).astype(np.int16))
    wav_io.seek(0)
    return wav_io
