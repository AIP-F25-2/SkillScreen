import cv2
import threading
import time
import os
from datetime import datetime
import sounddevice as sd
import numpy as np
import wave
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

VIDEO_FOLDER = os.getenv("VIDEO_FOLDER", "recordings")  # folder for raw + final video
AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", 44100))
AUDIO_GAIN = float(os.getenv("AUDIO_GAIN", 2.0))
VIDEO_FPS = float(os.getenv("VIDEO_FPS", 20.0))

os.makedirs(VIDEO_FOLDER, exist_ok=True)

camera = None
latest_frame = None
video_writer = None
recording = False

# Audio globals
audio_frames = []
audio_recording = False
audio_stream = None


def _audio_callback(indata, frames, time_info, status):
    if audio_recording:
        audio_frames.append(indata.copy())


def start_audio_recording():
    global audio_frames, audio_recording, audio_stream
    audio_frames = []
    audio_recording = True
    audio_stream = sd.InputStream(
        samplerate=AUDIO_SAMPLE_RATE, channels=1, callback=_audio_callback
    )
    audio_stream.start()


def stop_audio_recording():
    global audio_recording, audio_stream
    audio_recording = False
    if audio_stream:
        audio_stream.stop()
        audio_stream.close()
        audio_stream = None


def save_audio(filename, gain=AUDIO_GAIN):
    """Save recorded audio frames to WAV file with optional gain boost."""
    audio_file = filename.replace(".avi", "_audio.wav")

    if not audio_frames:
        print("No audio frames recorded")
        return audio_file

    audio_data = np.concatenate(audio_frames, axis=0)

    # Normalize
    max_val = np.max(np.abs(audio_data))
    if max_val > 0:
        audio_data = audio_data / max_val

    # Apply gain
    audio_data *= gain

    # Clip to [-1, 1]
    audio_data = np.clip(audio_data, -1.0, 1.0)

    # Convert to 16-bit PCM
    audio_data = np.int16(audio_data * 32767)

    with wave.open(audio_file, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(AUDIO_SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())

    return audio_file


def merge_audio_video(video_file, audio_file):
    """Merge audio and video into a single MP4 file using ffmpeg with loudness normalization."""
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = os.path.join(VIDEO_FOLDER, f"{base_name}.mp4")  # same folder as raw video
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_file,
        "-i", audio_file,
        "-c:v", "copy",
        "-af", "loudnorm",
        "-c:a", "aac",
        output_file,
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_file


def start_recording(filename_base="recording"):
    """Start video + audio recording."""
    global camera, latest_frame, video_writer, recording

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_filename = f"{filename_base}_{timestamp}.avi"
    video_path = os.path.join(VIDEO_FOLDER, video_filename)

    # Start video capture
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise RuntimeError("Cannot open camera")

    width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(video_path, fourcc, VIDEO_FPS, (width, height))

    # Start audio recording
    start_audio_recording()
    recording = True

    def record_loop():
        global latest_frame, recording, camera, video_writer
        while recording:
            ret, frame = camera.read()
            if not ret:
                continue
            latest_frame = frame.copy()
            # Ensure frame is 3-channel BGR
            if frame.ndim == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            elif frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            video_writer.write(frame)
            time.sleep(1 / VIDEO_FPS)

        # Stop everything
        camera.release()
        video_writer.release()
        stop_audio_recording()

        # Save audio and merge
        audio_file = save_audio(video_path)
        final_file = merge_audio_video(video_path, audio_file)

        # Cleanup intermediate files
        os.remove(video_path)
        os.remove(audio_file)

        print(f"Recording complete: {final_file}")

    t = threading.Thread(target=record_loop, daemon=True)
    t.start()
    return os.path.join(VIDEO_FOLDER, f"{filename_base}_{timestamp}.mp4")


def stop_recording():
    """Stop recording."""
    global recording
    recording = False
    return True


def get_latest_frame():
    global latest_frame
    return latest_frame
