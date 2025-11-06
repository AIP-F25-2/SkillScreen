from __future__ import annotations
from typing import List, Optional, Dict, Any, Tuple
import os
import tempfile
import subprocess
import shlex
import re
from glob import glob
from datetime import datetime

from .azure_storage_service import AzureStorageService, MANIFEST

_CHUNK_RE = re.compile(r"chunk-(\d{5})\.webm$", re.IGNORECASE)

def _server_chunk_name(idx_zero_based: int) -> str:
    return f"chunk-{idx_zero_based + 1:05d}.webm"

# ---- Session / Manifest lifecycle -----------------------------------
def init_manifest(
    user_id: str,
    *,
    session_id: Optional[str],           # kept for DB use in callers; not used here
    expected_total: int,
    candidate_id: Optional[str] = None,
    interview_id: Optional[str] = None,
    assigned_user: Optional[str] = None,
) -> Dict[str, Any]:
    """Create/overwrite the manifest in Azure (user-scoped)."""
    data = {"expected_total": int(expected_total), "received": [], "status": "in_progress"}
    AzureStorageService.save_manifest(user_id, data)
    return data

def load_manifest(user_id: str) -> Dict[str, Any]:
    return AzureStorageService.load_manifest(user_id) or {}

def update_manifest_received(user_id: str, chunk_idx_zero_based: int) -> Dict[str, Any]:
    """Append a received chunk index into the manifest (idempotent, user-scoped)."""
    mf = AzureStorageService.load_manifest(user_id) or {}
    expected = int(mf.get("expected_total") or 0)
    received = list(mf.get("received") or [])
    if chunk_idx_zero_based not in received:
        received.append(chunk_idx_zero_based)
        received.sort()
    out = {"expected_total": expected, "received": received, "status": mf.get("status") or "in_progress"}
    AzureStorageService.save_manifest(user_id, out)
    return out

def get_missing_chunks(user_id: str) -> List[int]:
    mf = AzureStorageService.load_manifest(user_id) or {}
    expected = int(mf.get("expected_total") or 0)
    received = set(mf.get("received") or [])
    return [i for i in range(expected) if i not in received]

# ---- Chunk uploads ---------------------------------------------------
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
    """Upload a chunk to Azure and mirror in DB; also update manifest.received."""
    filename = _server_chunk_name(idx_zero_based)
    blob = AzureStorageService.save_chunk(
        user_id,
        filename,
        fileobj,
        session_id=session_id,
        candidate_id=candidate_id,
        interview_id=interview_id,
        assigned_user=assigned_user,
        media_type="chunk",
    )
    update_manifest_received(user_id, idx_zero_based)
    return blob

# ---- Finalization ----------------------------------------------------
def finalize_with_merged(
    user_id: str,
    merged_local_path: str,
    *,
    content_type: str = "video/webm",
    duration_ms: Optional[int] = None,
    session_id: Optional[str] = None,
    candidate_id: Optional[str] = None,
    interview_id: Optional[str] = None,
    assigned_user: Optional[str] = None,
    keep_manifest: bool = True,
    delete_chunks: bool = True,
) -> str:
    """
    Upload merged WEBM, mark manifest done, optionally delete chunks.
    NOTE: merged name fixed ('merged.webm') to avoid accidental deletion.
    """
    merged_blob = AzureStorageService.upload_from_path(
        user_id=user_id,
        local_path=merged_local_path,
        dest_filename="merged.webm",
        content_type=content_type,
        media_type="merged",
        session_id=session_id,
        candidate_id=candidate_id,
        interview_id=interview_id,
        assigned_user=assigned_user,
        duration_ms=duration_ms,
    )

    # Mark manifest done
    try:
        mf = AzureStorageService.load_manifest(user_id) or {}
    except Exception:
        mf = {}
    AzureStorageService.save_manifest(
        user_id,
        {"expected_total": mf.get("expected_total"),
         "received": mf.get("received") or [],
         "status": "done"}
    )

    if delete_chunks:
        delete_all_chunks(user_id)

    if not keep_manifest:
        AzureStorageService.delete_file(user_id, MANIFEST)

    return merged_blob

# ---- Cleanup helpers -------------------------------------------------
def delete_all_chunks(user_id: str) -> List[str]:
    """Delete every chunk-*.webm (keeps 'merged.webm' and manifest)."""
    # Do NOT call delete_prefix; rely on filtered delete_all
    return AzureStorageService.delete_all(
        user_id, include_exts=[".webm"], exclude_exts=["merged.webm"]
    )

def reset_session(user_id: str, *, wipe_merged: bool = True, wipe_manifest: bool = True) -> None:
    """Remove all chunks; optionally remove merged + manifest."""
    delete_all_chunks(user_id)
    if wipe_merged:
        AzureStorageService.delete_file(user_id, "merged.webm")
    if wipe_manifest:
        AzureStorageService.delete_file(user_id, MANIFEST)

# ---- Compatibility wrapper used by controller -----------------------
def finalize_concat_then_encode(
    folder: str,                   # local chunk staging dir
    user_id: str,
    *,
    keep_merged: bool = False,
    keep_manifest: bool = False,
    session_id: Optional[str] = None,
) -> Tuple[str, str, List[str]]:
    """
    Collect chunks (local-first, Azure fallback), concat+encode via ffmpeg,
    upload final-YYYYMMDD-HHMMSS.mp4 + merged.webm, update manifest, optionally delete chunks.
    """
    local_chunk_paths: List[str] = []
    used_chunk_names: List[str] = []

    if folder and os.path.isdir(folder):
        candidates = glob(os.path.join(folder, "chunk-*.webm"))
        def keyf(p: str) -> int:
            m = _CHUNK_RE.search(os.path.basename(p))
            return int(m.group(1)) if m else 10**9
        candidates = sorted(candidates, key=keyf)
        if candidates:
            local_chunk_paths = candidates
            used_chunk_names = [os.path.basename(p) for p in candidates]

    if not local_chunk_paths:
        mf = AzureStorageService.load_manifest(user_id) or {}
        received = sorted(set(mf.get("received") or []))
        if not received and (mf.get("expected_total") is None or int(mf.get("expected_total") or 0) == 0):
            probe_max = 1000
            i = 0
            temp_paths, names = [], []
            while i < probe_max:
                name = _server_chunk_name(i)
                try:
                    p = AzureStorageService.download_to_temp(user_id, name)
                    temp_paths.append(p)
                    names.append(name)
                    i += 1
                except Exception:
                    break
            if not temp_paths:
                raise FileNotFoundError("No .webm chunks found (azure fallback)")
            local_chunk_paths = temp_paths
            used_chunk_names = names
        else:
            if not received:
                raise FileNotFoundError("No .webm chunks found (manifest empty)")
            max_idx = max(received)
            names = [_server_chunk_name(i) for i in range(max_idx + 1)]
            temp_paths = [AzureStorageService.download_to_temp(user_id, nm) for nm in names]
            local_chunk_paths = temp_paths
            used_chunk_names = names

    if not local_chunk_paths:
        raise FileNotFoundError("No .webm chunks found")

    # Timestamp for final file name (UTC)
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    final_mp4_name = f"final-{ts}.mp4"
    merged_webm_name = "merged.webm"

    with tempfile.TemporaryDirectory(prefix="merge_") as td:
        list_path = os.path.join(td, "list.txt")
        with open(list_path, "w", encoding="utf-8") as f:
            for p in local_chunk_paths:
                esc = p.replace("'", r"'\''")
                f.write(f"file '{esc}'\n")

        merged_webm_local = os.path.join(td, merged_webm_name)
        final_mp4_local  = os.path.join(td, final_mp4_name)

        cmd_webm = (
            f"ffmpeg -y -f concat -safe 0 -i {shlex.quote(list_path)} "
            f"-c:v libvpx-vp9 -crf 32 -b:v 0 -c:a libopus {shlex.quote(merged_webm_local)}"
        )
        p1 = subprocess.run(cmd_webm, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p1.returncode != 0:
            raise RuntimeError(p1.stderr.decode("utf-8", errors="ignore"))

        cmd_mp4 = (
            f"ffmpeg -y -i {shlex.quote(merged_webm_local)} "
            f"-c:v libx264 -preset veryfast -crf 23 -c:a aac -movflags +faststart {shlex.quote(final_mp4_local)}"
        )
        p2 = subprocess.run(cmd_mp4, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p2.returncode != 0:
            raise RuntimeError(p2.stderr.decode("utf-8", errors="ignore"))

        # Upload final MP4 (timestamped) — pass session_id
        AzureStorageService.upload_from_path(
            user_id=user_id,
            local_path=final_mp4_local,
            dest_filename=final_mp4_name,
            content_type="video/mp4",
            media_type="video",
            session_id=session_id,
        )

        # Upload merged.webm and finalize
        finalize_with_merged(
            user_id=user_id,
            merged_local_path=merged_webm_local,
            content_type="video/webm",
            session_id=session_id,
            keep_manifest=keep_manifest,
            delete_chunks=not keep_merged,
        )

    return (final_mp4_name, merged_webm_name, used_chunk_names)
