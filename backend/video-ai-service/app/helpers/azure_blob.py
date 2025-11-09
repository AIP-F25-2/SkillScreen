from __future__ import annotations

import json
import mimetypes
import os
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

from app.config import settings
from app.core.logging import get_logger

try:
    from azure.storage.blob import BlobServiceClient, ContentSettings  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    BlobServiceClient = None  # type: ignore
    ContentSettings = None  # type: ignore

_LOG = get_logger("azure_blob")


@dataclass
class BlobReference:
    container: str
    blob: str

    def url(self, base: Optional[str]) -> Optional[str]:
        if not base:
            return None
        return f"{base.rstrip('/')}/{self.container}/{self.blob}"


@dataclass
class ContainerURLInfo:
    account_url: str
    container: str
    sas: Optional[str]


class AzureBlobService:
    """
    Lightweight helper for interacting with Azure Blob Storage.
    Gracefully disables itself when credentials or dependency are missing.
    """

    def __init__(self) -> None:
        self._explicit_account_url = (getattr(settings, "AZURE_BLOB_ACCOUNT_URL", "") or "").strip()
        explicit_cred = getattr(settings, "AZURE_BLOB_SAS_TOKEN", "") or ""
        self._explicit_credential = explicit_cred.strip()
        raw_container_url = (getattr(settings, "AZURE_BLOB_CONTAINER_URL", "") or "").strip()
        if not raw_container_url:
            account = getattr(settings, "AZURE_BLOB_ACCOUNT_URL", "").rstrip("/")
            container = getattr(settings, "AZURE_BLOB_CONTAINER", "").lstrip("/")
            if account and container:
                raw_container_url = f"{account}/{container}"
        self._container_url = raw_container_url
        self._container_info = self._parse_container_url(self._container_url) if self._container_url else None

        self._account_url = self._explicit_account_url or (
            self._container_info.account_url if self._container_info else ""
        )
        self._credential = self._explicit_credential or (
            self._container_info.sas if self._container_info else ""
        )

        default_container = (getattr(settings, "AZURE_BLOB_CONTAINER", "") or "").strip()
        resolved_container = self._container_info.container if self._container_info else default_container
        self.videos_container = (
            (getattr(settings, "AZURE_VIDEOS_CONTAINER", "") or "").strip() or resolved_container
        )
        self.processed_container = (
            (getattr(settings, "AZURE_PROCESSED_CONTAINER", "") or "").strip() or self.videos_container
        )
        self.videos_prefix = self._normalize_prefix(settings.AZURE_VIDEOS_PREFIX)
        self.processed_prefix = self._normalize_prefix(settings.AZURE_PROCESSED_PREFIX)

        self._client: Optional[BlobServiceClient] = None
        self._base_url: Optional[str] = None
        self._account_host: Optional[str] = None
        self._sas_suffix: str = ""
        if self._credential and self._credential.startswith("?"):
            self._sas_suffix = self._credential
        elif self._container_info and self._container_info.sas:
            self._sas_suffix = self._container_info.sas

        self._enabled = bool(
            settings.AZURE_STORAGE_ENABLED
            and self._account_url
            and self.videos_container
            and self._explicit_credential
        )
        if not self._enabled:
            _LOG.warning("Azure Blob disabled (enabled=%s, account_url=%s, container=%s, credential=%s)",
                         settings.AZURE_STORAGE_ENABLED, bool(self._account_url), bool(self.videos_container), bool(self._explicit_credential))
            return
        if BlobServiceClient is None:
            _LOG.warning("azure-storage-blob not installed; Azure integration disabled")
            self._enabled = False
            return

        try:
            self._client = self._build_client()
        except Exception as exc:  # pragma: no cover - configuration issue
            _LOG.error("Failed to initialize Azure Blob client: %s", exc)
            self._enabled = False
            return

        base = (
            self._account_url
            or getattr(self._client, "primary_endpoint", None)
            or getattr(self._client, "url", None)
        )
        if not base:
            try:
                base = f"https://{self._client.account_name}.blob.core.windows.net"  # type: ignore[attr-defined]
            except Exception:
                base = ""
        self._base_url = base.rstrip("/") if base else None
        parsed = urlparse(self._base_url or "")
        self._account_host = parsed.netloc.lower() if parsed.netloc else None
        _LOG.info("Azure Blob configured: container=%s, processed_container=%s, prefix=%s", self.videos_container, self.processed_container, self.videos_prefix)

    @staticmethod
    def _normalize_prefix(prefix: Optional[str]) -> str:
        return (prefix or "").strip().strip("/")

    @staticmethod
    def _parse_container_url(url: str) -> Optional[ContainerURLInfo]:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc or not parsed.path:
            return None
        account_url = f"{parsed.scheme}://{parsed.netloc}"
        container = parsed.path.strip("/").split("/", 1)[0]
        if not container:
            return None
        sas_query = parsed.query or parsed.fragment or ""
        if sas_query:
            # normalize to '?...' format expected by Azure SDK
            sas_query = sas_query if sas_query.startswith("?") else f"?{sas_query}"
        return ContainerURLInfo(account_url=account_url, container=container, sas=sas_query or None)

    def _build_client(self) -> BlobServiceClient:
        if not self._account_url:
            raise RuntimeError("AZURE_BLOB_ACCOUNT_URL or AZURE_BLOB_CONTAINER_URL must be set")
        credential = self._explicit_credential or None
        return BlobServiceClient(account_url=self._account_url, credential=credential)

    # -------- public surface --------
    @property
    def enabled(self) -> bool:
        return bool(self._enabled and self._client)

    @property
    def base_url(self) -> Optional[str]:
        return self._base_url

    def _container_client(self, container: str):
        if not self.enabled:
            raise RuntimeError("Azure Blob client not configured")
        if not container:
            raise RuntimeError("Container name required for Azure operation")
        return self._client.get_container_client(container)  # type: ignore[union-attr]

    def _blob_client(self, container: str, blob: str):
        if not self.enabled:
            raise RuntimeError("Azure Blob client not configured")
        return self._client.get_blob_client(container=container, blob=blob)  # type: ignore[union-attr]

    def list_blobs(self, container: str, prefix: str) -> Iterable:
        client = self._container_client(container)
        return client.list_blobs(name_starts_with=prefix)

    def blob_exists(self, container: str, blob: str) -> bool:
        try:
            return bool(self._blob_client(container, blob).exists())
        except Exception:
            return False

    def delete_blob(self, container: str, blob: str) -> None:
        client = self._container_client(container)
        client.delete_blob(blob, delete_snapshots="include")

    def download_blob_to_path(self, ref: BlobReference, dest_path: str) -> str:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        blob_client = self._blob_client(ref.container, ref.blob)
        with open(dest_path, "wb") as fh:
            data = blob_client.download_blob()
            data.readinto(fh)
        return dest_path

    def download_blob_to_tempfile(self, ref: BlobReference, suffix: str = "") -> str:
        fd, tmp_path = tempfile.mkstemp(prefix="video-ai-", suffix=suffix or "")
        os.close(fd)
        return self.download_blob_to_path(ref, tmp_path)

    def _url_with_sas(self, ref: BlobReference) -> Optional[str]:
        if not self._base_url:
            return None
        if hasattr(ref, "url"):
            base = ref.url(self._base_url)
        else:
            container = getattr(ref, "container", None)
            blob = getattr(ref, "blob", None)
            if not container or not blob:
                return None
            base = f"{self._base_url.rstrip('/')}/{str(container).strip('/')}/{str(blob).lstrip('/')}"
        if not base:
            return None
        return f"{base}{self._sas_suffix}" if self._sas_suffix else base

    def public_url(self, ref: BlobReference) -> Optional[str]:
        return self._url_with_sas(ref)

    def upload_file(self, ref: BlobReference, local_path: str, content_type: Optional[str] = None) -> Optional[str]:
        blob_client = self._blob_client(ref.container, ref.blob)
        with open(local_path, "rb") as fh:
            blob_client.upload_blob(
                fh,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type) if (content_type and ContentSettings) else None,
            )
        return self.public_url(ref)

    def upload_bytes(self, ref: BlobReference, payload: bytes, content_type: Optional[str] = None) -> Optional[str]:
        blob_client = self._blob_client(ref.container, ref.blob)
        blob_client.upload_blob(
            payload,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type) if (content_type and ContentSettings) else None,
        )
        return self.public_url(ref)

    def read_json(self, ref: BlobReference) -> Dict[str, Any]:
        blob_client = self._blob_client(ref.container, ref.blob)
        data = blob_client.download_blob().readall()
        return json.loads(data.decode("utf-8"))

    def write_json(self, ref: BlobReference, data: Dict[str, Any]) -> Optional[str]:
        payload = json.dumps(data, indent=2).encode("utf-8")
        return self.upload_bytes(ref, payload, "application/json")

    # -------- path helpers --------
    def _join(self, *parts: str) -> str:
        filtered = [p.strip("/") for p in parts if p]
        return "/".join(filtered)

    def build_video_blob(self, interview_id: str, session_id: str, filename: str) -> BlobReference:
        blob = self._join(self.videos_prefix, interview_id, session_id, os.path.basename(filename))
        return BlobReference(self.videos_container, blob)

    def build_processed_blob(self, interview_id: str, session_id: str, filename: str, subdir: Optional[str] = None) -> BlobReference:
        blob = self._join(self.processed_prefix, interview_id, session_id, subdir or "", filename)
        return BlobReference(self.processed_container, blob)

    def resolve_blob_from_url(self, url: str) -> Optional[BlobReference]:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return None
        if not parsed.netloc or not parsed.path:
            return None
        container, _, blob = parsed.path.lstrip("/").partition("/")
        if not container or not blob:
            return None
        if self._account_host and parsed.netloc.lower() != self._account_host:
            return None
        return BlobReference(container=container, blob=blob)

    def resolve_video_blob(self, video_url: str, interview_id: str, session_id: str) -> Optional[BlobReference]:
        if not self.enabled:
            return None
        ref = self.resolve_blob_from_url(video_url)
        if ref:
            return ref
        if "://" in video_url:
            return None
        trimmed = video_url.lstrip("/")
        if not trimmed:
            return None
        segments: List[str] = []
        if self.videos_prefix:
            segments.append(self.videos_prefix)
        if interview_id:
            segments.append(interview_id)
        if session_id:
            segments.append(session_id)
        segments.append(trimmed)
        blob = "/".join(seg.strip("/") for seg in segments if seg)
        return BlobReference(self.videos_container, blob)

    def fetch_video(self, interview_id: str, session_id: str, video_url: str) -> Optional[Tuple[str, BlobReference]]:
        ref = self.resolve_video_blob(video_url, interview_id, session_id)
        if not ref:
            _LOG.warning("Could not resolve blob for interview=%s session=%s url=%s", interview_id, session_id, video_url)
            return None
        suffix = os.path.splitext(ref.blob)[1]
        try:
            local_path = self.download_blob_to_tempfile(ref, suffix=suffix)
            _LOG.info("Fetched blob '%s/%s' to temp file %s", ref.container, ref.blob, local_path)
            return local_path, ref
        except Exception as exc:
            _LOG.error("Failed to download blob '%s/%s': %s", ref.container, ref.blob, exc)
            raise

    def upload_processed_artifacts(
        self,
        interview_id: str,
        session_id: str,
        report_bytes: Optional[bytes],
        video_path: Optional[str],
        thumbs_dir: Optional[str],
    ) -> Dict[str, Optional[str]]:
        if not self.enabled:
            return {}

        uploaded: Dict[str, Optional[str]] = {}
        if report_bytes:
            report_ref = self.build_processed_blob(interview_id, session_id, f"{session_id}_report.json")
            uploaded["report_blob"] = report_ref.blob
            uploaded["report_url"] = self.upload_bytes(report_ref, report_bytes, "application/json")
            _LOG.info("Uploaded report to blob %s", report_ref.blob)
        if video_path and os.path.isfile(video_path):
            mime = mimetypes.guess_type(video_path)[0] or "video/mp4"
            video_ref = self.build_processed_blob(interview_id, session_id, os.path.basename(video_path))
            uploaded["video_blob"] = video_ref.blob
            uploaded["video_url"] = self.upload_file(video_ref, video_path, mime)
            _LOG.info("Uploaded annotated video to blob %s", video_ref.blob)
        if thumbs_dir and os.path.isdir(thumbs_dir):
            thumbs: List[str] = []
            for fname in sorted(os.listdir(thumbs_dir)):
                local = os.path.join(thumbs_dir, fname)
                if not os.path.isfile(local):
                    continue
                thumb_ref = self.build_processed_blob(interview_id, session_id, fname, subdir="thumbs")
                self.upload_file(thumb_ref, local, "image/jpeg")
                thumbs.append(thumb_ref.blob)
            uploaded["thumbnail_blobs"] = thumbs
            if thumbs:
                _LOG.info("Uploaded %d thumbnails for interview %s session %s", len(thumbs), interview_id, session_id)

        return uploaded


azure_blob = AzureBlobService()
