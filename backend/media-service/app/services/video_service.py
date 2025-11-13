from __future__ import annotations
import os, re, subprocess, shutil, tempfile, logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from app.services.storage_service import StorageService
from app.utils.filename import secure_part
import app.utils.constants as CONSTANTS

logger = logging.getLogger(__name__)

WEBM_EXT = ".webm"
_num_pat = re.compile(r"(\d+)(?=\.webm$)", re.IGNORECASE)


def _server_chunk_name(idx_zero_based: int) -> str:
    return f"chunk_{idx_zero_based:05d}.webm"


def _seq_num(name: str) -> int:
    m = _num_pat.search(name)
    return int(m.group(1)) if m else 0


def _run(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# -----------------------------------------------------------------
# 🔧 Chunk saving  (thin wrapper)
# -----------------------------------------------------------------
def save_chunk(interview_id: str, chunk_index: int, fileobj) -> str:
    """Store a single chunk under videos/<interview_id>/chunks/."""
    data = fileobj.read()
    blob = StorageService.save_chunk(interview_id, f"{interview_id}_recording.webm", chunk_index, data)
    return blob


# -----------------------------------------------------------------
# 🎬 Local merge + encode helper
# -----------------------------------------------------------------
def _binary_concat_to_webm(folder: str, chunks_sorted: List[str]) -> str:
    merged_path = os.path.join(folder, CONSTANTS.MERGED_WEBM_NAMING)
    with open(merged_path, "wb") as out:
        for fn in chunks_sorted:
            with open(os.path.join(folder, fn), "rb") as inp:
                out.write(inp.read())
    return merged_path


def _encode_webm_to_mp4(in_webm: str, out_mp4: str) -> None:
    cmd = [
        "ffmpeg", "-y", "-fflags", "+genpts", "-i", in_webm,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", out_mp4,
    ]
    _run(cmd)


def _probe_duration_ms(path: str) -> Optional[int]:
    try:
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        s = p.stdout.decode().strip()
        return int(float(s) * 1000) if s else None
    except Exception:
        return None


# -----------------------------------------------------------------
# 🚀 Finalize concat → encode → upload
# -----------------------------------------------------------------
def finalize_concat_then_encode(
    workdir: str,
    interview_id: str,
    *,
    keep_merged: bool = False,
) -> Tuple[str, Optional[str], List[str], Optional[int]]:
    """
    Merge .webm chunks in `workdir`, encode to mp4, upload final to Azure/local storage,
    and optionally keep merged.webm.
    """
    chunks = [f for f in os.listdir(workdir)
              if f.lower().endswith(WEBM_EXT) and not f.startswith("merged")]
    if not chunks:
        raise FileNotFoundError("No .webm chunks found")
    chunks.sort(key=_seq_num)

    merged_webm_path = _binary_concat_to_webm(workdir, chunks)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_name_mp4 = f"{secure_part(interview_id)}_{ts}.mp4"
    out_path_mp4 = os.path.join(workdir, out_name_mp4)

    try:
        _encode_webm_to_mp4(merged_webm_path, out_path_mp4)
    except subprocess.CalledProcessError as e:
        raise RuntimeError((e.stderr or b"").decode(errors="ignore"))

    duration_ms = _probe_duration_ms(out_path_mp4)

    # Upload final mp4 to backend (videos/<interview_id>/)
    try:
        StorageService.upload_from_path(
            interview_id, out_path_mp4, out_name_mp4, "video/mp4"
        )
    except Exception as e:
        raise RuntimeError(str(e))

    merged_name = None
    if keep_merged:
        try:
            StorageService.upload_from_path(
                interview_id, merged_webm_path, CONSTANTS.MERGED_WEBM_NAMING, CONSTANTS.VIDEO_WEBM_FORMAT
            )
            merged_name = CONSTANTS.MERGED_WEBM_NAMING
        except Exception:
            pass

    # local cleanup
    for fn in chunks:
        try:
            os.remove(os.path.join(workdir, fn))
        except Exception:
            pass
    if not keep_merged:
        try:
            os.remove(merged_webm_path)
        except Exception:
            pass

    return out_name_mp4, merged_name, chunks, duration_ms


# -----------------------------------------------------------------
# 🧹 Reset / abort session
# -----------------------------------------------------------------
def reset_session(interview_id: str) -> None:
    """Remove all chunk blobs and mark session aborted."""
    try:
        StorageService.delete_folder(f"videos/{interview_id}/chunks/")
    except Exception:
        logger.warning("reset_session: failed to delete chunk folder", exc_info=True)
