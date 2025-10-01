````markdown
# Video & Audio Recorder

This project provides a Python-based video and audio recording system using OpenCV and SoundDevice. It captures video from your webcam and audio from your microphone simultaneously, merges them into a single MP4 file, and saves it to a folder defined in a `.env` file.

---

## Features

- Records video from webcam in real-time.
- Records audio simultaneously.
- Merges video and audio into a single MP4 using `ffmpeg`.
- Temporary raw files are deleted after merging.
- Configurable via `.env` file.
- Supports adjustable frame rate, audio sample rate, and audio gain.
- Returns latest frame for real-time preview if needed.
- Fully threaded recording to avoid blocking main application.

---

## Requirements

- Python 3.8+
- OpenCV (`cv2`)
- NumPy
- SoundDevice
- `ffmpeg` installed and accessible via command line
- Wave (built-in)
- `python-dotenv`

Install Python dependencies:

```bash
pip install opencv-python numpy sounddevice python-dotenv
````

Install ffmpeg:

* **macOS**: `brew install ffmpeg`
* **Windows**: Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
* **Linux (Ubuntu/Debian)**: `sudo apt install ffmpeg`

---

## Project Structure

```
project/
│
├── app.py                            # Main recording script
├── .env                              # Environment variables
├── README.md
└── services/video_recorder.py        # Video And Audio Recording Script
└── services/video_processor.py       # Video And Audio Processing Script
└── recordings/                       # Folder where recordings are saved
└── processed_videos/                 # Folder where recordings are saved
└── requirements.txt                  # Requirements of the project
```

---

## Environment Variables (`.env`)

Create a `.env` file in the project root:

```dotenv
# Folder to save video recordings (raw + final MP4)
VIDEO_FOLDER=/absolute/path/to/recordings

# Audio recording sample rate
AUDIO_SAMPLE_RATE=44100

# Audio gain multiplier
AUDIO_GAIN=2.0

# Video FPS
VIDEO_FPS=20
```

> Make sure to use absolute paths to avoid path issues.

---

## Usage

### Start Recording

```python
from recorder import start_recording

# Starts recording video + audio
mp4_file = start_recording(filename_base="my_recording")
print(f"Recording started. Saving to {mp4_file}")
```

### Stop Recording

```python
from recorder import stop_recording

stop_recording()
print("Recording stopped.")
```

### Get Latest Frame (for preview)

```python
from recorder import get_latest_frame

frame = get_latest_frame()
if frame is not None:
    import cv2
    cv2.imshow("Live Preview", frame)
    cv2.waitKey(1)
```

---

## Notes

* Raw `.avi` video and `.wav` audio are saved temporarily in `VIDEO_FOLDER` and removed after merging.
* Final merged MP4 file is saved in `VIDEO_FOLDER` as well.
* Ensure `ffmpeg` is installed and added to your system PATH.
* Adjust `VIDEO_FPS`, `AUDIO_SAMPLE_RATE`, and `AUDIO_GAIN` via `.env` for your recording needs.

---

## License

MIT License

---

```