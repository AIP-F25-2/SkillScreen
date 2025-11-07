import os
import json
import tempfile
from datetime import datetime
from typing import List, Optional, Tuple

from flask import current_app
from azure.storage.blob import ContainerClient, ContentSettings

from sqlalchemy import create_engine, select, insert, update, delete, func, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from ..utils.filename import secure_part
from ..db.schema import media, metadata

MANIFEST = "chunks_manifest.json"

# ---------------------- Azure helpers ----------------------
def _container_client() -> ContainerClient:
    """
    Build a ContainerClient from a container SAS URL, e.g.:
    https://<acct>.blob.core.windows.net/<container>?sv=...&sp=rwlacd&...
    """
    url = current_app.config.get("AZURE_BLOB_CONTAINER_URL") or os.getenv("AZURE_BLOB_CONTAINER_URL")
    if not url:
        raise RuntimeError("AZURE_BLOB_CONTAINER_URL not configured")
    return ContainerClient.from_container_url(url)

def _prefix_for_user(user_id: str) -> str:
    return f"{secure_part(user_id)}/"

def _blob_name(user_id: str, filename: str) -> str:
    return _prefix_for_user(user_id) + secure_part(filename)

def _azure_delete_if_exists(cc: ContainerClient, name: str) -> bool:
    try:
        cc.delete_blob(name)
        return True
    except Exception as ex:
        msg = str(ex).lower()
        # Treat 404/missing as success for idempotency
        if "404" in msg or "not found" in msg or "does not exist" in msg:
            return False
        raise

def _azure_upload_bytes(cc: ContainerClient, name: str, data: bytes, content_type: str) -> Tuple[Optional[str], int]:
    bc = cc.get_blob_client(name)
    bc.upload_blob(data, overwrite=True, content_settings=ContentSettings(content_type=content_type))
    etag = None
    try:
        etag = bc.get_blob_properties().etag
    except Exception:
        pass
    return etag, len(data)

def _azure_upload_stream(cc: ContainerClient, name: str, stream, content_type: str) -> Tuple[Optional[str], Optional[int]]:
    bc = cc.get_blob_client(name)
    bc.upload_blob(stream, overwrite=True, content_settings=ContentSettings(content_type=content_type))
    etag, size = None, None
    try:
        props = bc.get_blob_properties()
        etag = getattr(props, "etag", None)
        size = getattr(props, "size", None)
    except Exception:
        pass
    return etag, size


# ---------------------- DB helpers (SQLAlchemy Core) ----------------------
def _get_engine() -> Engine:
    # Try Flask-SQLAlchemy engine first
    ext = current_app.extensions.get("sqlalchemy")
    if ext and hasattr(ext, "db") and hasattr(ext.db, "engine"):
        return ext.db.engine

    # Else build from URI
    uri = (
        current_app.config.get("SQLALCHEMY_DATABASE_URI")
        or os.getenv("SQLALCHEMY_DATABASE_URI")
        or os.getenv("DATABASE_URL")
    )
    if not uri:
        raise RuntimeError("No database URI found for SQLAlchemy Core engine.")
    if not hasattr(current_app, "_core_engine"):
        current_app._core_engine = create_engine(uri, future=True)
    return current_app._core_engine


def _now():
    return datetime.utcnow()


def _upsert_media_row(
    *,
    engine: Engine,
    user_id: str,
    media_type_val: str,
    blob_name_val: str,
    content_type_val: Optional[str] = None,
    session_id_val: Optional[str] = None,
    candidate_id_val: Optional[str] = None,
    interview_id_val: Optional[str] = None,
    assigned_user_val: Optional[str] = None,
    size_bytes_val: Optional[int] = None,
    duration_ms_val: Optional[int] = None,
    status_val: Optional[str] = None,
    expected_total_val: Optional[int] = None,
    received_indices_val: Optional[List[int]] = None,
    extra_val: Optional[dict] = None,
    file_path_val: Optional[str] = None,
):
    """Upsert by (user_id, blob_name). If no row, INSERT; else UPDATE."""
    with engine.begin() as conn:
        row = conn.execute(
            select(media.c.id).where(
                media.c.user_id == user_id,
                media.c.blob_name == blob_name_val,
            )
        ).fetchone()

        payload = {
            "user_id": user_id,
            "media_type": media_type_val,
            "file_path": file_path_val or blob_name_val,  # use provided file_path or fallback to blob_name
            "blob_name": blob_name_val,
            "content_type": content_type_val,
            "session_id": session_id_val,
            "candidate_id": candidate_id_val,
            "interview_id": interview_id_val,
            "assigned_user": assigned_user_val,
            "size_bytes": size_bytes_val,
            "duration_ms": duration_ms_val,
            "status": status_val,
            "expected_total": expected_total_val,
            "received_indices": received_indices_val,
            "extra": extra_val or {},
            "updated_at": func.now(),
        }

        if row is None:
            payload["created_at"] = func.now()
            conn.execute(insert(media).values(**payload))
        else:
            conn.execute(
                update(media)
                .where(media.c.id == row.id)
                .values(**payload)
            )


def _delete_media_row(engine: Engine, user_id: str, blob_name_val: str):
    with engine.begin() as conn:
        conn.execute(
            delete(media).where(
                media.c.user_id == user_id,
                media.c.blob_name == blob_name_val,
            )
        )

def _delete_media_rows_by_user(engine: Engine, user_id: str):
    with engine.begin() as conn:
        conn.execute(delete(media).where(media.c.user_id == user_id))


def _list_files_db(engine: Engine, user_id: str) -> List[str]:
    # FIX: select file_path (real column) instead of non-existent file_name
    with engine.begin() as conn:
        rows = conn.execute(
            select(media.c.file_path, media.c.blob_name).where(media.c.user_id == user_id)
        ).fetchall()
    out: List[str] = []
    for fp, bn in rows:
        path = fp or bn
        if path:
            # convert "userid/filename" -> "filename" (API expects bare filenames)
            fname = path.split("/", 1)[1] if "/" in path else path
            out.append(fname)
    return sorted(set([f for f in out if f]))


def _list_users_db(engine: Engine) -> List[str]:
    with engine.begin() as conn:
        rows = conn.execute(select(media.c.user_id).distinct()).fetchall()
    return sorted([r[0] for r in rows if r[0]])


# ---------------------- Public Service ----------------------
class AzureStorageService:
    """
    Dual-write service (Azure for bytes, Postgres 'media' for metadata)
    using SQLAlchemy Core per app/db/schema.py.
    """

    # -------- Listing --------
    @staticmethod
    def user_folder(user_id: str) -> str:
        return _prefix_for_user(user_id)

    @staticmethod
    def list_users() -> List[str]:
        engine = _get_engine()
        users = _list_users_db(engine)
        if users:
            return users

        # Fallback to Azure if DB has none (first run)
        cc = _container_client()
        found = set()
        for b in cc.list_blobs(name_starts_with=""):
            if "/" in b.name:
                found.add(b.name.split("/", 1)[0])
        return sorted(found)

    @staticmethod
    def list_files(
        user_id: str,
        include_exts: Optional[List[str]] = None,
        exclude_exts: Optional[List[str]] = None,
        reconcile_if_missing: bool = False,
    ) -> List[str]:
        engine = _get_engine()
        files = _list_files_db(engine, user_id)

        # Optional reconcile: index Azure into DB if DB is empty
        if not files and reconcile_if_missing:
            cc = _container_client()
            prefix = _prefix_for_user(user_id)
            seen: List[str] = []
            for b in cc.list_blobs(name_starts_with=prefix):
                fname = b.name[len(prefix):]
                seen.append(fname)
                # minimal upsert
                _upsert_media_row(
                    engine=engine,
                    user_id=user_id,
                    media_type_val="file",
                    blob_name_val=b.name,
                    file_path_val=b.name,
                    status_val="indexed",
                    extra_val={"reconciled": True},
                )
            files = sorted(seen)

        # Apply filters
        out: List[str] = []
        for f in files:
            low = f.lower()
            if include_exts and not any(low.endswith(e) for e in include_exts):
                continue
            if exclude_exts and any(low.endswith(e) for e in exclude_exts):
                continue
            out.append(f)
        return sorted(out)

    # -------- Manifest (JSON) --------
    @staticmethod
    def manifest_blob_name(user_id: str) -> str:
        return _blob_name(user_id, MANIFEST)

    @staticmethod
    def load_manifest(user_id: str) -> dict:
        engine = _get_engine()
        blob = AzureStorageService.manifest_blob_name(user_id)

        # Try DB first
        with engine.begin() as conn:
            row = conn.execute(
                select(media.c.expected_total, media.c.received_indices, media.c.status)
                .where(media.c.user_id == user_id, media.c.blob_name == blob, media.c.media_type == "manifest")
            ).fetchone()

        if row and (row.expected_total is not None or row.received_indices is not None or row.status):
            return {
                "expected_total": row.expected_total,
                "received": row.received_indices or [],
                "status": row.status or "unknown",
            }

        # Fallback to Azure JSON
        cc = _container_client()
        try:
            data = cc.get_blob_client(blob).download_blob().readall()
            obj = json.loads(data.decode("utf-8"))
            # Backfill DB
            _upsert_media_row(
                engine=engine,
                user_id=user_id,
                media_type_val="manifest",
                blob_name_val=blob,
                content_type_val="application/json",
                expected_total_val=obj.get("expected_total"),
                received_indices_val=obj.get("received") or [],
                status_val=obj.get("status") or "in_progress",
                extra_val={"source": "backfill"},
            )
            return obj
        except Exception:
            return {"received": [], "expected_total": None}

    @staticmethod
    def save_manifest(
        user_id: str,
        data: dict,
        *,
        session_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        interview_id: Optional[str] = None,
        assigned_user: Optional[str] = None,
    ) -> None:
        engine = _get_engine()
        cc = _container_client()
        blob = AzureStorageService.manifest_blob_name(user_id)
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")

        # 1) Azure write
        _azure_upload_bytes(cc, blob, payload, "application/json")

        # 2) DB upsert (compensate: remove blob if DB fails)
        try:
            _upsert_media_row(
                engine=engine,
                user_id=user_id,
                media_type_val="manifest",
                blob_name_val=blob,
                content_type_val="application/json",
                session_id_val=session_id,
                candidate_id_val=candidate_id,
                interview_id_val=interview_id,
                assigned_user_val=assigned_user,
                expected_total_val=data.get("expected_total"),
                received_indices_val=data.get("received") or [],
                status_val=data.get("status") or "in_progress",
                extra_val={"kind": "manifest"},
            )
        except SQLAlchemyError:
            _azure_delete_if_exists(cc, blob)
            raise

    # -------- Uploads (chunks/files) --------
    @staticmethod
    def save_chunk(
        user_id: str,
        filename: str,
        fileobj,
        *,
        session_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        interview_id: Optional[str] = None,
        assigned_user: Optional[str] = None,
        media_type: str = "chunk",
    ) -> str:
        engine = _get_engine()
        cc = _container_client()
        blob = _blob_name(user_id, filename)
        stream = getattr(fileobj, "stream", fileobj)

        # 1) Azure upload
        etag, size = _azure_upload_stream(cc, blob, stream, "video/webm")

        # 2) DB upsert
        try:
            _upsert_media_row(
                engine=engine,
                user_id=user_id,
                media_type_val=media_type,
                blob_name_val=blob,
                content_type_val="video/webm",
                session_id_val=session_id,
                candidate_id_val=candidate_id,
                interview_id_val=interview_id,
                assigned_user_val=assigned_user,
                size_bytes_val=size,
                status_val="uploaded",
                extra_val={"etag": etag},
            )
        except SQLAlchemyError:
            _azure_delete_if_exists(cc, blob)
            raise
        return blob

    @staticmethod
    def upload_from_path(
        user_id: str,
        local_path: str,
        dest_filename: str,
        content_type: str,
        *,
        session_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        interview_id: Optional[str] = None,
        assigned_user: Optional[str] = None,
        media_type: str = "file",
        duration_ms: Optional[int] = None,
    ) -> str:
        engine = _get_engine()
        cc = _container_client()
        blob = _blob_name(user_id, dest_filename)
        with open(local_path, "rb") as f:
            data = f.read()

        # 1) Azure upload
        etag, size = _azure_upload_bytes(cc, blob, data, content_type)

        # 2) DB upsert
        try:
            _upsert_media_row(
                engine=engine,
                user_id=user_id,
                media_type_val=media_type,
                blob_name_val=blob,
                content_type_val=content_type,
                session_id_val=session_id,
                candidate_id_val=candidate_id,
                interview_id_val=interview_id,
                assigned_user_val=assigned_user,
                size_bytes_val=size,
                duration_ms_val=duration_ms,
                status_val="uploaded",
                extra_val={"etag": etag},
            )
        except SQLAlchemyError:
            _azure_delete_if_exists(cc, blob)
            raise
        return blob

    # -------- Download --------
    @staticmethod
    def download_to_temp(user_id: str, filename: str) -> str:
        cc = _container_client()
        name = _blob_name(user_id, filename)
        suffix = os.path.splitext(filename)[1]
        with tempfile.NamedTemporaryFile(prefix="media_", suffix=suffix, delete=False) as tmp:
            cc.get_blob_client(name).download_blob().readinto(tmp)
            return tmp.name

    # -------- Deletes (hard) --------
    @staticmethod
    def delete_file(user_id: str, filename: str) -> bool:
        engine = _get_engine()
        cc = _container_client()
        blob = _blob_name(user_id, filename)

        # 1) Azure (idempotent)
        try:
            _azure_delete_if_exists(cc, blob)
        finally:
            # 2) DB hard-delete regardless
            try:
                _delete_media_row(engine, user_id, blob)
            except SQLAlchemyError:
                return False
        return True

    @staticmethod
    def delete_all(
        user_id: str,
        include_exts: Optional[List[str]] = None,
        exclude_exts: Optional[List[str]] = None
    ) -> List[str]:
        engine = _get_engine()
        cc = _container_client()
        prefix = _prefix_for_user(user_id)

        filenames = AzureStorageService.list_files(user_id, include_exts, exclude_exts)

        # Azure pass
        for fname in filenames:
            try:
                _azure_delete_if_exists(cc, prefix + secure_part(fname))
            except Exception:
                # continue; still attempt DB delete for remaining
                pass

        # DB pass
        for fname in filenames:
            try:
                _delete_media_row(engine, user_id, prefix + secure_part(fname))
            except SQLAlchemyError:
                pass

        # Special cleanup when wiping chunks (keep manifest by default)
        if include_exts and ".webm" in include_exts:
            # DO NOT touch merged.webm or manifest here; guarded by caller.
            pass

        return filenames

    @staticmethod
    def delete_user(user_id: str) -> bool:
        engine = _get_engine()
        cc = _container_client()
        prefix = _prefix_for_user(user_id)
        ok = True

        # Azure wipe
        try:
            for b in cc.list_blobs(name_starts_with=prefix):
                try:
                    _azure_delete_if_exists(cc, b.name)
                except Exception:
                    ok = False
        except Exception:
            ok = False

        # DB wipe
        try:
            _delete_media_rows_by_user(engine, user_id)
        except SQLAlchemyError:
            ok = False

        return ok

    # -------- Optional reconcile utility --------
    @staticmethod
    def reconcile_user_index(user_id: str) -> int:
        """
        Scan Azure for a user prefix and upsert missing DB rows.
        Returns number of upserts.
        """
        engine = _get_engine()
        cc = _container_client()
        prefix = _prefix_for_user(user_id)
        count = 0
        for b in cc.list_blobs(name_starts_with=prefix):
            fname = b.name[len(prefix):]
            try:
                _upsert_media_row(
                    engine=engine,
                    user_id=user_id,
                    media_type_val="file",
                    blob_name_val=b.name,
                    file_path_val=b.name,
                    status_val="indexed",
                    extra_val={"reconciled": True},
                )
                count += 1
            except SQLAlchemyError:
                pass
        return count

    @staticmethod
    def delete_all_users() -> list[str]:
        """Delete ALL users' blobs + return the list of user IDs that were fully deleted."""
        users = AzureStorageService.list_users()
        deleted: list[str] = []
        for u in users:
            if AzureStorageService.delete_user(u):
                deleted.append(u)
        return deleted

    @staticmethod
    def list_chunk_filenames(user_id: str, ext: str = ".webm") -> list[str]:
        """Return only the chunk filenames inside the user's 'virtual folder' (excludes 'merged')."""
        cc = _container_client()
        prefix = _prefix_for_user(user_id)
        chunks: list[str] = []
        for b in cc.list_blobs(name_starts_with=prefix):
            fname = b.name[len(prefix):]
            low = fname.lower()
            if low.endswith(ext) and not fname.startswith("merged"):
                chunks.append(fname)
        return chunks
