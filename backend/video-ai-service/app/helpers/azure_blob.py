from __future__ import annotations

import json
import mimetypes
import os
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

from app.utils.config import settings
from app.core.logging import get_logger

try:
    from azure.storage.blob import BlobServiceClient, ContentSettings
except Exception:
    BlobServiceClient = None
    ContentSettings = None

_LOG = get_logger("azure_blob")


# ---------------------------------------------------------
# Data Structures
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Azure Blob Service (Refactored + Fail-Fast)
# ---------------------------------------------------------

class AzureBlobService:
    """
    Azure Blob helper with fail-fast initialization.
    If configuration or credentials are missing, raise errors immediately.
    """

    def __init__(self) -> None:
        self._client = None
        self._base_url: Optional[str] = None
        self._account_host: Optional[str] = None
        self._sas_suffix: str = ""

        self._load_basic_settings()
        self._resolve_container_url()
        self._resolve_account_credentials()
        self._validate_azure_dependencies()
        self._resolve_container_names()
        self._resolve_sas_suffix()
        self._initialize_client()
        self._compute_base_url()

        _LOG.info(
            "Azure Blob configured: container=%s processed=%s prefix=%s",
            self.videos_container,
            self.processed_container,
            self.videos_prefix
        )

    # ---------------------------------------------------------
    # Initialization Helpers (Refactored)
    # ---------------------------------------------------------

    def _load_basic_settings(self) -> None:
        """Load explicit settings and validate required Azure config."""
        self._explicit_account_url = (settings.AZURE_BLOB_ACCOUNT_URL or "").strip()
        self._explicit_credential = (settings.AZURE_BLOB_SAS_TOKEN or "").strip()

        if not self._explicit_account_url:
            raise ValueError("AZURE_BLOB_ACCOUNT_URL is missing.")

        if not self._explicit_credential:
            raise ValueError("AZURE_BLOB_SAS_TOKEN is missing.")

    def _resolve_container_url(self) -> None:
        """Resolve full container URL or build one."""
        raw_url = (settings.AZURE_BLOB_CONTAINER_URL or "").strip()

        if not raw_url:
            container = (settings.AZURE_BLOB_CONTAINER or "").strip()
            if not container:
                raise ValueError(
                    "Azure container is missing. Provide AZURE_BLOB_CONTAINER or AZURE_BLOB_CONTAINER_URL."
                )
            raw_url = f"{self._explicit_account_url.rstrip('/')}/{container}"

        self._container_url = raw_url
        self._container_info = self._parse_container_url(raw_url)

        if not self._container_info:
            raise ValueError(f"Invalid Azure container URL: {raw_url}")

    def _resolve_account_credentials(self) -> None:
        """Resolve account URL & SAS from explicit config or URL info."""
        self._account_url = self._explicit_account_url or self._container_info.account_url
        self._credential = self._explicit_credential or (self._container_info.sas or "")

    def _validate_azure_dependencies(self) -> None:
        """Ensure Azure SDK is installed."""
        if BlobServiceClient is None:
            raise RuntimeError("azure-storage-blob package not installed.")

    def _resolve_container_names(self) -> None:
        """Resolve container names & prefixes."""
        main_container = self._container_info.container
        self.videos_container = (settings.AZURE_VIDEOS_CONTAINER or "").strip() or main_container
        self.processed_container = (
            (settings.AZURE_PROCESSED_CONTAINER or "").strip() or self.videos_container
        )

        self.videos_prefix = self._normalize_prefix(settings.AZURE_VIDEOS_PREFIX)
        self.processed_prefix = self._normalize_prefix(settings.AZURE_PROCESSED_PREFIX)

    def _resolve_sas_suffix(self) -> None:
        """Compute SAS suffix for generated URLs."""
        if self._credential.startswith("?"):
            self._sas_suffix = self._credential
        elif self._container_info.sas:
            self._sas_suffix = self._container_info.sas

    def _initialize_client(self) -> None:
        """Initialize Azure Blob client (fail-fast)."""
        try:
            self._client = BlobServiceClient(
                account_url=self._account_url,
                credential=self._credential or None,
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize Azure Blob client: {exc}") from exc

    def _compute_base_url(self) -> None:
        """Build base URL for generating public blob URLs."""
        base = (
            self._account_url
            or getattr(self._client, "primary_endpoint", None)
            or getattr(self._client, "url", None)
        )

        if not base:
            try:
                base = f"https://{self._client.account_name}.blob.core.windows.net"
            except Exception as exc:
                raise RuntimeError("Unable to compute Azure Blob base URL") from exc

        self._base_url = base.rstrip("/")

        parsed = urlparse(self._base_url)
        self._account_host = parsed.netloc.lower()

    # ---------------------------------------------------------
    # Static Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _normalize_prefix(prefix: Optional[str]) -> str:
        return (prefix or "").strip().strip("/")

    @staticmethod
    def _parse_container_url(url: str) -> Optional[ContainerURLInfo]:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc or not parsed.path:
            return None

        container = parsed.path.strip("/").split("/", 1)[0]
        if not container:
            return None

        sas = parsed.query or parsed.fragment
        if sas and not sas.startswith("?"):
            sas = f"?{sas}"

        return ContainerURLInfo(
            account_url=f"{parsed.scheme}://{parsed.netloc}",
            container=container,
            sas=sas or None
        )

    # ---------------------------------------------------------
    # Blob Methods
    # ---------------------------------------------------------

    @property
    def enabled(self) -> bool:
        return True  # fail-fast means service is always enabled if constructed

    @property
    def base_url(self) -> Optional[str]:
        return self._base_url

    def _container_client(self, container: str):
        return self._client.get_container_client(container)

    def _blob_client(self, container: str, blob: str):
        return self._client.get_blob_client(container=container, blob=blob)

    # ---------------------------------------------------------

    def list_blobs(self, container: str, prefix: str) -> Iterable:
        return self._container_client(container).list_blobs(name_starts_with=prefix)

    def blob_exists(self, container: str, blob: str) -> bool:
        try:
            return bool(self._blob_client(container, blob).exists())
        except Exception:
            return False

    def delete_blob(self, container: str, blob: str) -> None:
        self._container_client(container).delete_blob(blob, delete_snapshots="include")

    def download_blob_to_path(self, ref: BlobReference, dest_path: str) -> str:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as fh:
            self._blob_client(ref.container, ref.blob).download_blob().readinto(fh)
        return dest_path

    def download_blob_to_tempfile(self, ref: BlobReference, suffix: str = "") -> str:
        fd, tmp = tempfile.mkstemp(prefix="video-ai-", suffix=suffix)
        os.close(fd)
        return self.download_blob_to_path(ref, tmp)

    def _url_with_sas(self, ref: BlobReference) -> Optional[str]:
        base_url = ref.url(self._base_url)
        if not base_url:
            return None
        return f"{base_url}{self._sas_suffix}" if self._sas_suffix else base_url

    def public_url(self, ref: BlobReference) -> Optional[str]:
        return self._url_with_sas(ref)

    # ---------------------------------------------------------

    def upload_file(self, ref: BlobReference, path: str, content_type: Optional[str]) -> Optional[str]:
        with open(path, "rb") as fh:
            self._blob_client(ref.container, ref.blob).upload_blob(
                fh,
                overwrite=True,
                content_settings=(
                    ContentSettings(content_type=content_type) if content_type and ContentSettings else None
                ),
            )
        return self.public_url(ref)

    def upload_bytes(self, ref: BlobReference, payload: bytes, content_type: Optional[str]) -> Optional[str]:
        self._blob_client(ref.container, ref.blob).upload_blob(
            payload,
            overwrite=True,
            content_settings=(
                ContentSettings(content_type=content_type) if content_type and ContentSettings else None
            ),
        )
        return self.public_url(ref)

    def read_json(self, ref: BlobReference) -> Dict[str, Any]:
        data = self._blob_client(ref.container, ref.blob).download_blob().readall()
        return json.loads(data.decode())

    def write_json(self, ref: BlobReference, data: Dict[str, Any]) -> Optional[str]:
        return self.upload_bytes(ref, json.dumps(data).encode(), "application/json")

    # ---------------------------------------------------------
    # Blob Path Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _join(*parts: str) -> str:
        return "/".join(p.strip("/") for p in parts if p)

    def build_video_blob(self, interview_id: str, session_id: str, filename: str) -> BlobReference:
        blob = self._join(self.videos_prefix, interview_id, session_id, os.path.basename(filename))
        return BlobReference(self.videos_container, blob)

    def build_processed_blob(self, interview_id: str, session_id: str, filename: str, subdir: Optional[str] = None) -> BlobReference:
        blob = self._join(self.processed_prefix, interview_id, session_id, subdir or "", filename)
        return BlobReference(self.processed_container, blob)

    def resolve_blob_from_url(self, url: str) -> Optional[BlobReference]:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or not parsed.path:
            return None

        container, _, blob = parsed.path.lstrip("/").partition("/")
        if not container or not blob:
            return None

        # Ensure same storage account
        if self._account_host and parsed.netloc.lower() != self._account_host:
            return None

        return BlobReference(container, blob)

    # ------------------------------

    def resolve_video_blob(self, video_url: str, interview_id: str, session_id: str) -> Optional[BlobReference]:
        ref = self.resolve_blob_from_url(video_url)
        if ref:
            return ref

        if "://" in video_url:
            return None

        trimmed = video_url.lstrip("/")
        if not trimmed:
            return None

        blob = self._join(self.videos_prefix, interview_id, session_id, trimmed)
        return BlobReference(self.videos_container, blob)

    def fetch_video(self, interview_id: str, session_id: str, video_url: str) -> Optional[Tuple[str, BlobReference]]:
        ref = self.resolve_video_blob(video_url, interview_id, session_id)
        if not ref:
            _LOG.warning("Could not resolve blob: interview=%s session=%s url=%s", interview_id, session_id, video_url)
            return None

        suffix = os.path.splitext(ref.blob)[1]
        try:
            path = self.download_blob_to_tempfile(ref, suffix)
            _LOG.info("Fetched blob '%s/%s' to temp file %s", ref.container, ref.blob, path)
            return path, ref
        except Exception as exc:
            _LOG.error("Download failed: %s/%s: %s", ref.container, ref.blob, exc)
            raise

    # ------------------------------

    def upload_processed_artifacts(
        self,
        interview_id: str,
        session_id: str,
        report_bytes: Optional[bytes],
        video_path: Optional[str],
        thumbs_dir: Optional[str],
    ) -> Dict[str, Optional[str]]:

        uploaded: Dict[str, Optional[str]] = {}

        if report_bytes:
            ref = self.build_processed_blob(interview_id, session_id, f"{session_id}_report.json")
            uploaded["report_blob"] = ref.blob
            uploaded["report_url"] = self.upload_bytes(ref, report_bytes, "application/json")

        if video_path and os.path.isfile(video_path):
            mime = mimetypes.guess_type(video_path)[0] or "video/mp4"
            ref = self.build_processed_blob(interview_id, session_id, os.path.basename(video_path))
            uploaded["video_blob"] = ref.blob
            uploaded["video_url"] = self.upload_file(ref, video_path, mime)

        if thumbs_dir and os.path.isdir(thumbs_dir):
            thumbs: List[str] = []
            for fname in sorted(os.listdir(thumbs_dir)):
                path = os.path.join(thumbs_dir, fname)
                if os.path.isfile(path):
                    ref = self.build_processed_blob(interview_id, session_id, fname, subdir="thumbs")
                    self.upload_file(ref, path, "image/jpeg")
                    thumbs.append(ref.blob)
            uploaded["thumbnail_blobs"] = thumbs

        return uploaded


# ---------------------------------------------------------
# Singleton instance
# ---------------------------------------------------------

azure_blob = AzureBlobService()
