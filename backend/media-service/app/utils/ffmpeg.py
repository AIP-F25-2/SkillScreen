import subprocess
def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except Exception as exc:
        raise RuntimeError("ffmpeg not found on PATH") from exc
