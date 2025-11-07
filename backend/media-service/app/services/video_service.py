from __future__ import annotations

import os
import re
import json
import shutil
import subprocess
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import logging

from ..utils.filename import secure_part
from .storage_service import StorageService

logger = logging.getLogger(__name__)

# Constants
WEBM_EXT = ".webm"
MANIFEST = "chunks_manifest.json"

_num_pat = re.compile(r"(\d+)(?=\.webm$)", re.IGNORECASE)


def _server_chunk_name(idx_zero_based: int) -> str:
    return f"chunk-{idx_zero_based + 1:05d}.webm"


def _seq_num(name: str) -> int:
    m = _num_pat.search(name)
    return int(m.group(1)) if m else 0


def _run(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# ---------------- Manifest / session lifecycle ----------------
def init_manifest(
    user_id: str,
    *,
    session_id: Optional[str],
    expected_total: int,
    candidate_id: Optional[str] = None,
    interview_id: Optional[str] = None,
    assigned_user: Optional[str] = None,
) -> Dict[str, Any]:
    # First load any existing manifest to preserve received chunks
    existing = StorageService.load_manifest(user_id) or {}
    existing_received = existing.get("received", [])
    existing_session = existing.get("session_id")
    existing_status = existing.get("status")

    sanitized_session = secure_part(session_id) if session_id else None

    # If caller starts a fresh session (different ID) or previous manifest was finalized,
    # clear out the stale chunk indices so we only track the active recording.
    if existing_received:
        reset_required = False
        if sanitized_session:
            if existing_session != sanitized_session:
                reset_required = True
        else:
            if existing_status == "done":
                reset_required = True
        if reset_required:
            existing_received = []
    
    data = {
        "expected_total": int(expected_total),
        "received": existing_received,  # Preserve any existing received chunks
        "status": "in_progress",
        "session_id": sanitized_session,
    }
    StorageService.save_manifest(
        user_id,
        data,
        session_id=session_id,
        candidate_id=candidate_id,
        interview_id=interview_id,
        assigned_user=assigned_user,
    )
    return data


def load_manifest(user_id: str) -> Dict[str, Any]:
    return StorageService.load_manifest(user_id)


def update_manifest_received(
    user_id: str,
    chunk_idx_zero_based: int,
    *,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    mf = StorageService.load_manifest(user_id) or {}
    received = set(mf.get("received") or [])
    received.add(chunk_idx_zero_based)
    mf["received"] = sorted(received)  # sort for stability
    prev_expected = mf.get("expected_total")
    try:
        prev_expected_int = int(prev_expected)
    except (TypeError, ValueError):
        prev_expected_int = 0
    mf["expected_total"] = max(prev_expected_int, chunk_idx_zero_based + 1)
    if session_id:
        mf["session_id"] = secure_part(session_id)
    StorageService.save_manifest(
        user_id,
        mf,
        session_id=session_id,
    )
    return mf


def get_missing_chunks(user_id: str) -> List[int]:
    mf = StorageService.load_manifest(user_id) or {}
    expected = int(mf.get("expected_total") or 0)
    received = set(mf.get("received") or [])
    return [i for i in range(expected) if i not in received]





# ---------------- Chunk uploads ----------------
def save_chunk(
    user_id: str,
    idx_zero_based: int,
    fileobj,
    *,
    session_id: Optional[str] = None,
    candidate_id: Optional[str] = None,
    interview_id: Optional[str] = None,
    assigned_user: Optional[str] = None,
) -> str:
    # First ensure manifest exists
    try:
        man = StorageService.load_manifest(user_id)
        sanitized_session = secure_part(session_id) if session_id else None
        man_session = man.get("session_id") if man else None
        session_mismatch = (
            sanitized_session
            and man
            and (
                (man_session and man_session != sanitized_session)
                or (man_session is None and bool(man.get("received")))
                or (man_session is None and (man.get("status") in {"done", "aborted"}))
            )
        )
        if not man or "expected_total" not in man or session_mismatch:
            # Create or update manifest with reasonable defaults
            # Will be updated by client with correct total
            init_manifest(user_id, session_id=session_id, expected_total=max(idx_zero_based + 1, 1))
    except Exception as e:
        logger.warning(f"Failed to handle manifest in save_chunk: {str(e)}")
        pass

    filename = _server_chunk_name(idx_zero_based)
    blob = StorageService.save_chunk_to_cloud(
        user_id,
        filename,
        fileobj,
        session_id=session_id,
        candidate_id=candidate_id,
        interview_id=interview_id,
        assigned_user=assigned_user,
        media_type="chunk",
    )
    # Track receipt in manifest
    update_manifest_received(user_id, idx_zero_based, session_id=session_id)
    return blob


# ---------------- Helpers for concat/encode ----------------
def _binary_concat_to_webm(folder: str, chunks_sorted: List[str]) -> str:
    merged_path = os.path.join(folder, "merged.webm")
    with open(merged_path, "wb") as out:
        for fn in chunks_sorted:
            with open(os.path.join(folder, fn), "rb") as inp:
                out.write(inp.read())
    return merged_path


def _encode_webm_to_mp4(in_webm: str, out_mp4: str) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-fflags",
        "+genpts",
        "-i",
        in_webm,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-r",
        "30",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-movflags",
        "+faststart",
        out_mp4,
    ]
    _run(cmd)


def _probe_duration_ms(path: str) -> Optional[int]:
    try:
        p = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        s = p.stdout.decode().strip()
        if not s:
            return None
        return int(float(s) * 1000)
    except Exception:
        return None


def _clean_local_files(folder: str, filenames: List[str]) -> None:
    for f in filenames:
        try:
            os.remove(os.path.join(folder, f))
        except Exception:
            pass


# ---------------- Finalize: concat -> encode -> upload ----------------
def finalize_concat_then_encode(
    user_folder: str,
    user_id: str,
    *,
    keep_merged: bool = False,
    keep_manifest: bool = False,
    session_id: Optional[str] = None,
    candidate_id: Optional[str] = None,
    interview_id: Optional[str] = None,
    assigned_user: Optional[str] = None,
) -> Tuple[str, Optional[str], List[str]]:
    # 1) gather and order chunks
    chunks = [f for f in os.listdir(user_folder) if f.lower().endswith(WEBM_EXT) and not f.startswith("merged")]
    if not chunks:
        raise FileNotFoundError("No .webm chunks found")
    chunks.sort(key=_seq_num)

    # 2) concat -> merged.webm
    merged_webm_path = _binary_concat_to_webm(user_folder, chunks)

    # 3) encode merged.webm -> final mp4
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name_mp4 = f"{secure_part(user_id)}_{ts}.mp4"
    out_path_mp4 = os.path.join(user_folder, out_name_mp4)

    try:
        _encode_webm_to_mp4(merged_webm_path, out_path_mp4)
    except subprocess.CalledProcessError as e:
        raise RuntimeError((e.stderr or b"").decode(errors="ignore"))

    # 4) probe duration
    duration_ms = _probe_duration_ms(out_path_mp4)

        # 5) upload final mp4 to Azure
    try:
        StorageService.upload_from_path(
            user_id=user_id,
            local_path=out_path_mp4,
            dest_filename=out_name_mp4,
            content_type="video/mp4",
            session_id=session_id,
            candidate_id=candidate_id,
            interview_id=interview_id,
            assigned_user=assigned_user,
            media_type="file",
            duration_ms=duration_ms,
        )
    except Exception as e:
        # bubble up as runtime error for controller to convert
        raise RuntimeError(str(e))

    merged_name: Optional[str] = None
    if keep_merged:
        try:
            StorageService.upload_from_path(
                user_id=user_id,
                local_path=merged_webm_path,
                dest_filename="merged.webm",
                content_type="video/webm",
                session_id=session_id,
                candidate_id=candidate_id,
                interview_id=interview_id,
                assigned_user=assigned_user,
                media_type="merged",
            )
            merged_name = os.path.basename(merged_webm_path)
        except Exception:
            # non-fatal
            merged_name = None

    # 6) cleanup local chunks
    _clean_local_files(user_folder, chunks)

    # 7) cleanup merged.webm (unless asked to keep)
    if not keep_merged:
        try:
            os.remove(merged_webm_path)
        except Exception:
            pass

    # 8) cleanup manifest(s) (unless asked to keep)
    if not keep_manifest:
        try:
            StorageService.delete_file(user_id, MANIFEST)
        except Exception:
            pass
            
    return out_name_mp4, merged_name, chunks


def reset_session(user_id: str, *, wipe_merged: bool = True, wipe_manifest: bool = True) -> None:
    # Remove all chunk blobs
    StorageService.delete_all(user_id, include_exts=[".webm"], exclude_exts=None)
    if wipe_merged:
        StorageService.delete_file(user_id, "merged.webm")
    if wipe_manifest:
        StorageService.delete_file(user_id, MANIFEST)
