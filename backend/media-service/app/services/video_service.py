# app/services/video_service.py
import os, re, json, subprocess
from datetime import datetime
from ..utils.filename import secure_part
from .storage_service import StorageService  # use single source of truth for manifest path

WEBM_EXT = ".webm"
MANIFEST = "chunks_manifest.json"

_num_pat = re.compile(r"(\d+)(?=\.webm$)", re.IGNORECASE)

def init_manifest(user_folder: str, total_chunks: int) -> None:
    total = int(total_chunks)
    if total <= 0:
        raise ValueError("total_chunks must be > 0")
    data = {
        "total": total,
        "received": [False] * total,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    with open(_manifest_path(user_folder), "w", encoding="utf-8") as f:
        json.dump(data, f)

def _manifest_path(user_folder: str) -> str:
    return os.path.join(user_folder, MANIFEST)


def _seq_num(name: str) -> int:
    m = _num_pat.search(name)
    return int(m.group(1)) if m else 0

def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# ---------- Manifest helpers ----------
def _legacy_manifest_path(user_folder: str) -> str:
    # Some older deployments used manifest.json
    return os.path.join(user_folder, "manifest.json")

def get_missing_chunks(user_folder: str) -> list[int]:
    # Try new manifest first (chunks_manifest.json), else legacy
    new_path = StorageService.manifest_path(os.path.basename(user_folder)) if os.path.basename(user_folder) else None
    # If we’re called with absolute user_folder, derive manifest by folder (not by id)
    if new_path is None or not os.path.isfile(new_path):
        # derive chunks_manifest.json path directly by folder
        new_path = os.path.join(user_folder, "chunks_manifest.json")
    path = new_path if os.path.isfile(new_path) else _legacy_manifest_path(user_folder)
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            m = json.load(f)
        return [i for i, ok in enumerate(m.get("received", [])) if not ok]
    except Exception:
        return []

def reset_chunks(user_folder: str) -> list[str]:
    deleted = []
    for f in os.listdir(user_folder):
        if f.endswith(WEBM_EXT) or f in ("chunks_manifest.json", "manifest.json", "merged.webm"):
            try:
                os.remove(os.path.join(user_folder, f))
                deleted.append(f)
            except Exception:
                pass
    return deleted

# ---------- Save chunk ----------
def save_chunk(user_folder: str, filename: str, fileobj) -> str:
    fname = secure_part(filename)
    if not fname.lower().endswith(WEBM_EXT):
        raise ValueError("Only .webm chunks allowed")
    os.makedirs(user_folder, exist_ok=True)
    path = os.path.join(user_folder, fname)
    fileobj.save(path)  # overwrite-safe on retry
    return path

# ---------- Reference-style finalize: write merged.webm then single ffmpeg pass ----------
def _binary_concat_to_webm(user_folder: str, chunks_sorted: list[str]) -> str:
    merged_path = os.path.join(user_folder, "merged.webm")
    with open(merged_path, "wb") as out:
        for fn in chunks_sorted:
            with open(os.path.join(user_folder, fn), "rb") as inp:
                out.write(inp.read())
    return merged_path

def _encode_webm_to_mp4(in_webm: str, out_mp4: str) -> None:
    cmd = [
        "ffmpeg", "-y",
        "-fflags", "+genpts",
        "-i", in_webm,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart",
        out_mp4
    ]
    _run(cmd)

def finalize_concat_then_encode(
    user_folder: str,
    user_id: str,
    *,
    keep_merged: bool = False,
    keep_manifest: bool = False
) -> tuple[str, str | None, list[str]]:
    # 1) gather and order chunks
    chunks = [f for f in os.listdir(user_folder)
              if f.lower().endswith(WEBM_EXT) and not f.startswith("merged")]
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

    # 4) cleanup original chunks
    for f in chunks:
        try:
            os.remove(os.path.join(user_folder, f))
        except Exception:
            pass

    # 5) cleanup merged.webm (unless asked to keep)
    merged_name = os.path.basename(merged_webm_path)
    if not keep_merged:
        try:
            os.remove(merged_webm_path)
            merged_name = None
        except Exception:
            pass

    # 6) cleanup manifest(s) (unless asked to keep)
    if not keep_manifest:
        for mf in ("chunks_manifest.json", "manifest.json"):
            mp = os.path.join(user_folder, mf)
            if os.path.isfile(mp):
                try:
                    os.remove(mp)
                except Exception:
                    pass

    return out_name_mp4, merged_name, chunks
